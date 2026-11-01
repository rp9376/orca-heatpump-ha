"""Faults of the display, with every platform running on top (PLAN.md P5)."""

from collections.abc import Callable

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.models import Kind
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator, Faults


@pytest.fixture
async def entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set the integration up with all platforms."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


def unavailable(hass: HomeAssistant, entry: MockConfigEntry) -> set[str]:
    """Return the entry's unavailable entities."""
    return {
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
        if (state := hass.states.get(e.entity_id)) and state.state == STATE_UNAVAILABLE
    }


async def poll(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Poll once, as the coordinator does on its interval."""
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(
            lambda e: setattr(e, "faults", Faults(http_status=503)), id="http_503"
        ),
        pytest.param(
            lambda e: setattr(e, "faults", Faults(malformed_body=True)), id="malformed"
        ),
        pytest.param(
            lambda e: setattr(e, "faults", Faults(disconnect=True)), id="disconnect"
        ),
        pytest.param(
            lambda e: setattr(e, "faults", Faults(whole_error="E_FAIL")),
            id="whole_error",
        ),
    ],
)
async def test_failed_poll_and_recovery(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    emulator: Emulator,
    fault: Callable[[Emulator], None],
) -> None:
    """A failed poll makes everything unavailable; the next good one restores it."""
    baseline = unavailable(hass, entry)
    everything = {
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
        if hass.states.get(e.entity_id)
    }

    fault(emulator)
    await poll(hass, entry)
    assert unavailable(hass, entry) == everything

    emulator.faults = Faults()
    await poll(hass, entry)
    assert unavailable(hass, entry) == baseline
    assert len(emulator.sessions) == 1


async def test_session_expiry_is_invisible(
    hass: HomeAssistant, entry: MockConfigEntry, emulator: Emulator
) -> None:
    """An expired token is renewed within the poll; nothing goes unavailable."""
    baseline = unavailable(hass, entry)

    emulator.expire_sessions()
    await poll(hass, entry)

    assert entry.runtime_data.coordinator.last_update_success
    assert unavailable(hass, entry) == baseline
    assert len(emulator.sessions) == 1


async def test_display_reboot(
    hass: HomeAssistant, entry: MockConfigEntry, emulator: Emulator
) -> None:
    """While the display restarts the pump is unavailable; then it logs in again."""
    baseline = unavailable(hass, entry)

    emulator.expire_sessions()
    emulator.faults = Faults(disconnect=True)
    await poll(hass, entry)
    assert not entry.runtime_data.coordinator.last_update_success

    emulator.faults = Faults()
    await poll(hass, entry)
    assert unavailable(hass, entry) == baseline
    assert len(emulator.sessions) == 1


async def test_sessions_exhausted_and_recovery(
    hass: HomeAssistant, entry: MockConfigEntry, emulator: Emulator
) -> None:
    """With every session taken by others the pump is unavailable, then recovers."""
    baseline = unavailable(hass, entry)
    emulator.expire_sessions()
    emulator.max_sessions = 0

    await poll(hass, entry)
    assert not entry.runtime_data.coordinator.last_update_success
    assert emulator.sessions == {}

    emulator.max_sessions = 2
    await poll(hass, entry)
    assert unavailable(hass, entry) == baseline
    assert len(emulator.sessions) == 1


async def test_dropped_records_do_not_flap(
    hass: HomeAssistant, entry: MockConfigEntry, emulator: Emulator
) -> None:
    """Records the display drops now and then never make an entity unavailable."""
    baseline = unavailable(hass, entry)
    emulator.faults = Faults(drop_record_rate=0.1)

    for _ in range(10):
        await poll(hass, entry)
        assert unavailable(hass, entry) == baseline


@pytest.mark.parametrize(
    "values",
    [
        {
            tag: "99"
            for definition in catalog.CATALOG
            if definition.kind is Kind.ENUM
            for tag in definition.tag_names()
        }
    ],
)
async def test_unknown_values_everywhere(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Values nobody has seen yet leave entities available with unknown states."""
    assert entry.state is ConfigEntryState.LOADED
    states = {
        entity_id: state.state
        for entity_id in (
            "sensor.heat_pump_active_alarm",
            "sensor.heat_pump_outdoor_unit_state",
            "select.heat_pump_operating_programme",
            # An unknown circuit name falls back to the circuit's number.
            "climate.circuit_1",
        )
        if (state := hass.states.get(entity_id))
    }
    assert states == {
        "sensor.heat_pump_active_alarm": "unknown_code",
        "sensor.heat_pump_outdoor_unit_state": "unknown",
        "select.heat_pump_operating_programme": "unknown",
        "climate.circuit_1": "unknown",
    }


async def test_restart_loops_release_sessions(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, emulator: Emulator
) -> None:
    """Reloads and stops never leave a session behind, even with only one allowed."""
    emulator.max_sessions = 1
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    for _ in range(5):
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert len(emulator.sessions) == 1

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert emulator.sessions == {}
