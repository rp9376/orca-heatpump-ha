"""Tests for setting up and unloading the integration."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

import aiohttp
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.config_flow import validate
from custom_components.orca_heatpump.const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_BUFFER,
    CONF_SOLAR,
    CONF_TOPOLOGY,
    DOMAIN,
    OLD_DOMAIN,
    OVERRIDE_ABSENT,
)
from custom_components.orca_heatpump.helpers import (
    async_create_session,
    topology_to_data,
)
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from tools.emulator import Emulator, Faults

from .conftest import OUR_TOPOLOGY


async def test_setup_and_unload(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Setup creates the devices; unload frees the display's session."""
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.topology == OUR_TOPOLOGY
    assert entry.runtime_data.identity.firmware == "61 (2016-12-12)"
    devices = {
        next(iter(d.identifiers))[1].removeprefix(entry.entry_id): d
        for d in dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    }
    assert {key: d.name for key, d in devices.items()} == {
        "": "Heat pump",
        "_circuit1": "Underfloor heating",
        "_circuit2": "Radiators",
        "_dhw": "Hot water",
        "_solar": "Solar collectors",
    }
    assert devices[""].sw_version == "61 (2016-12-12)"
    assert devices[""].model == "Heat pump (Mitsubishi)"
    assert devices["_circuit1"].via_device_id == devices[""].id
    assert len(emulator.sessions) == 1

    await hass.config_entries.async_unload(entry.entry_id)

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert emulator.sessions == {}


@pytest.mark.parametrize(
    ("broken", "state", "sessions_left"),
    [
        pytest.param({"password": "other"}, ConfigEntryState.SETUP_ERROR, 0, id="auth"),
        pytest.param(
            {"max_sessions": 0}, ConfigEntryState.SETUP_RETRY, 0, id="too_many_users"
        ),
        pytest.param(
            {"faults": Faults(http_status=503)},
            ConfigEntryState.SETUP_RETRY,
            0,
            id="error",
        ),
        # The logout fails too; the display drops the session when it idles out.
        pytest.param(
            {"faults": Faults(fail_after_requests=3)},
            ConfigEntryState.SETUP_RETRY,
            1,
            id="first_refresh",
        ),
    ],
)
async def test_setup_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    emulator: Emulator,
    broken: dict[str, object],
    state: ConfigEntryState,
    sessions_left: int,
) -> None:
    """Setup failures map to retry or error and leave no session behind."""
    emulator.__dict__.update(broken)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert mock_config_entry.state is state
    assert len(emulator.sessions) == sessions_left


async def test_auth_error_starts_reauth(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, emulator: Emulator
) -> None:
    """A refused login starts reauthentication."""
    emulator.password = "other"
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == ["reauth"]


async def test_logout_on_stop(
    hass: HomeAssistant, init_integration: MockConfigEntry, emulator: Emulator
) -> None:
    """Stopping Home Assistant frees the display's session."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    assert emulator.sessions == {}


async def test_topology_change_raises_issue(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """A different detected topology raises an issue; the stored one stays."""
    stored = topology_to_data(OUR_TOPOLOGY) | {"buffer": True}
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, data={**mock_config_entry.data, CONF_TOPOLOGY: stored}
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    issue = issue_registry.async_get_issue(
        DOMAIN, f"topology_changed_{mock_config_entry.entry_id}"
    )
    assert issue is not None
    assert issue.is_fixable
    assert issue.translation_placeholders == {
        "old": "23 (DK1, MK2, SV, SOLAR, ZALOG)",
        "new": "23 (DK1, MK2, SV, SOLAR)",
    }
    assert mock_config_entry.runtime_data.topology.buffer is True


@pytest.mark.parametrize(
    ("disabled_by", "has_issue"),
    [
        pytest.param(None, True, id="active"),
        pytest.param(ConfigEntryDisabler.USER, False, id="disabled"),
    ],
)
async def test_old_integration_issue(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
    disabled_by: ConfigEntryDisabler | None,
    has_issue: bool,
) -> None:
    """orca-energy-ha on the same pump raises an issue unless disabled."""
    MockConfigEntry(
        domain=OLD_DOMAIN,
        unique_id="127.0.0.1",
        data={"hostname": "127.0.0.1"},
        disabled_by=disabled_by,
    ).add_to_hass(hass)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    issue_id = f"old_integration_{mock_config_entry.entry_id}"
    assert (issue_registry.async_get_issue(DOMAIN, issue_id) is not None) is has_issue


async def test_overrides_and_stale_devices(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Options override detection; devices of absent elements are removed."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"room_sensor_1": "present", CONF_SOLAR: "absent", CONF_BUFFER: "auto"},
    )
    stale = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, f"{mock_config_entry.entry_id}_solar")},
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    topology = mock_config_entry.runtime_data.topology
    assert topology.circuits[0].room_sensor is True
    assert topology.solar is False
    assert device_registry.async_get(stale.id) is None


async def test_remove_entry_removes_issues(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Removing the entry removes its repair issues."""
    issue_id = f"sessions_exhausted_{init_integration.entry_id}"
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="sessions_exhausted",
    )

    await hass.config_entries.async_remove(init_integration.entry_id)

    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.parametrize("platforms", [[Platform.NUMBER, Platform.SENSOR]])
async def test_power_limit_option_swaps_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Allowing power limit changes swaps their sensors for numbers, and back."""
    entry = init_integration

    def power_limits() -> set[str]:
        return {
            e.entity_id
            for e in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
            if e.unique_id.endswith("_hp_power_limit_heating")
        }

    assert power_limits() == {"sensor.heat_pump_power_limit_heating"}

    for allow, entity_id in (
        (True, "number.heat_pump_power_limit_heating"),
        (False, "sensor.heat_pump_power_limit_heating"),
    ):
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_ALLOW_POWER_LIMITS: allow}
        )
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        assert power_limits() == {entity_id}


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(
            lambda hass, old: hass.config_entries.async_remove(old.entry_id),
            id="removed",
        ),
        pytest.param(
            lambda hass, old: hass.config_entries.async_set_disabled_by(
                old.entry_id, ConfigEntryDisabler.USER
            ),
            id="disabled",
        ),
    ],
)
async def test_old_integration_issue_clears(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
    change: Callable[[HomeAssistant, MockConfigEntry], Awaitable[Any]],
) -> None:
    """The issue goes away as soon as orca-energy-ha stops polling, no reload."""
    old = MockConfigEntry(
        domain=OLD_DOMAIN, unique_id="127.0.0.1", data={"hostname": "127.0.0.1"}
    )
    old.add_to_hass(hass)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    issue_id = f"old_integration_{mock_config_entry.entry_id}"
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is not None

    await change(hass, old)
    await hass.async_block_till_done()

    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["duo"], indirect=True)
@pytest.mark.parametrize("platforms", [[Platform.NUMBER, Platform.SENSOR]])
async def test_option_removes_orphaned_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Saying a room sensor is absent removes its entities, and only those."""
    entry = init_integration
    room = "sensor.underfloor_heating_room_temperature"
    assert entity_registry.async_get(room) is not None
    before = len(er.async_entries_for_config_entry(entity_registry, entry.entry_id))

    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, "room_sensor_1": OVERRIDE_ABSENT},
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get(room) is None
    # The room temperature and the two room setpoints.
    after = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert before - len(after) == 3


async def test_sessions_keep_no_cookies(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The entry's client uses a session without a cookie jar."""
    session = init_integration.runtime_data.client._session
    assert isinstance(session.cookie_jar, aiohttp.DummyCookieJar)


async def test_flow_check_cleans_up_its_session(
    hass: HomeAssistant, host: str, emulator: Emulator
) -> None:
    """The flow's check logs out and detaches its own cookie-free session."""
    session = async_create_session(hass, auto_cleanup=False)
    with patch(
        "custom_components.orca_heatpump.config_flow.async_create_session",
        return_value=session,
    ):
        errors, topology = await validate(
            hass, {CONF_HOST: host, CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}
        )

    assert (errors, topology) == ({}, OUR_TOPOLOGY)
    assert session.closed
    assert emulator.sessions == {}
