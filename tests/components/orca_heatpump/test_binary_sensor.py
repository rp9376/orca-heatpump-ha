"""Tests for the binary sensors."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the binary sensors."""
    return [Platform.BINARY_SENSOR]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Each real pump gets the binary sensors of its own elements."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_heater_stages_unknown(
    hass: HomeAssistant,
    emulator: Emulator,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Without a stage count, every heater stage gets a sensor."""
    emulator.values["2_Izbira_st_grelcev"] = ""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.heat_pump_electric_heater_stage_3")


@pytest.mark.parametrize("values", [{"2_Izbira_DOD_VIRA": "2"}])
@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_no_heater_stages_without_a_heater(hass: HomeAssistant) -> None:
    """A pump whose only additional source isn't a heater has no stage sensors."""
    assert hass.states.get("binary_sensor.heat_pump_electric_heater_stage_1") is None
