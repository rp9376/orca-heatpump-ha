"""Every one of the 45 wiring schemas sets up with the right devices."""

from collections import Counter

import pytest
from pytest_homeassistant.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client.models import CircuitTopology, PumpTopology
from custom_components.orca_heatpump.client.topology import SCHEMAS
from custom_components.orca_heatpump.const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_TOPOLOGY,
    DEFAULT_TITLE,
    DOMAIN,
)
from custom_components.orca_heatpump.helpers import topology_to_data
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from tools.emulator import Emulator


def expected_topology(schema: int) -> PumpTopology:
    """Return the topology our pump's values give with another schema."""
    return PumpTopology(
        schema,
        tuple(
            CircuitTopology(slot, kind, room_sensor=False)
            for slot, kind in enumerate(SCHEMAS[schema].circuits, 1)
            if kind is not None
        ),
        dhw=SCHEMAS[schema].dhw,
        solar=SCHEMAS[schema].solar,
        buffer=False,
    )


@pytest.mark.parametrize("schema", sorted(SCHEMAS))
async def test_schema(
    hass: HomeAssistant,
    host: str,
    emulator: Emulator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    schema: int,
    snapshot: SnapshotAssertion,
) -> None:
    """The schema is detected as stored and each element gets its device."""
    emulator.values["2_Shema"] = str(schema)
    topology = expected_topology(schema)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_TITLE,
        entry_id="01ORCAHEATPUMPTESTENTRY000",
        data={
            CONF_HOST: host,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin",
            CONF_TOPOLOGY: topology_to_data(topology),
        },
        options={CONF_ALLOW_POWER_LIMITS: False},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.topology == topology
    assert not issue_registry.issues
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert all(
        hass.states.get(e.entity_id) is not None for e in entities if not e.disabled
    )
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert {
        "devices": sorted(
            next(iter(d.identifiers))[1].removeprefix(entry.entry_id) or "heat_pump"
            for d in devices
        ),
        "entities": dict(sorted(Counter(e.domain for e in entities).items())),
    } == snapshot


@pytest.mark.parametrize(
    ("schema", "raw", "expected"),
    [
        pytest.param(39, "379", "37.9", id="sensor_wired"),
        pytest.param(39, "-9999", None, id="nothing_wired"),
        pytest.param(23, "379", None, id="real_solar"),
    ],
)
async def test_solar_input(
    hass: HomeAssistant,
    host: str,
    emulator: Emulator,
    schema: int,
    raw: str,
    expected: str | None,
) -> None:
    """A sensor on the solar input of a pump without solar shows up by itself (#30)."""
    emulator.values["2_Shema"] = str(schema)
    emulator.values["2_Poti5"] = raw
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_TITLE,
        data={
            CONF_HOST: host,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin",
            CONF_TOPOLOGY: topology_to_data(expected_topology(schema)),
        },
        options={CONF_ALLOW_POWER_LIMITS: False},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.heat_pump_solar_input_temperature")
    assert (state.state if state else None) == expected
