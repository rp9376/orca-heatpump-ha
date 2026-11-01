"""Tests for the select entities."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

PROGRAMME = "select.heat_pump_operating_programme"
(PROGRAMME_TAG,) = catalog.OPERATING_PROGRAMME.tag_names()
(SOURCE_TAG,) = catalog.ADDITIONAL_SOURCE.tag_names()


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the selects."""
    return [Platform.SELECT]


@pytest.fixture(autouse=True)
def writable(emulator: Emulator) -> None:
    """Accept writes to the operating programme."""
    emulator.writable.add(PROGRAMME_TAG)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Each pump gets the programmes and modes of its elements."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("values", "before"),
    [
        pytest.param({}, "normal", id="known"),
        pytest.param({PROGRAMME_TAG: "9"}, STATE_UNKNOWN, id="unseen_value"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_select_option(
    hass: HomeAssistant, emulator: Emulator, before: str
) -> None:
    """An option is written as its raw value, even from a value nobody knows."""
    assert (state := hass.states.get(PROGRAMME)) is not None
    assert state.state == before

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: PROGRAMME, ATTR_OPTION: "holiday"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert emulator.writes == [(PROGRAMME_TAG, 1)]
    assert (state := hass.states.get(PROGRAMME)) is not None
    assert state.state == "holiday"


@pytest.mark.parametrize(
    ("values", "present"),
    [
        pytest.param({SOURCE_TAG: "1"}, True, id="electric_heater"),
        pytest.param({SOURCE_TAG: "2"}, False, id="other_source_only"),
        pytest.param({SOURCE_TAG: ""}, True, id="unknown"),
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_heater_selects(hass: HomeAssistant, present: bool) -> None:
    """The electric heater's selects exist unless the pump surely has none."""
    assert (hass.states.get("select.heat_pump_electric_heater") is not None) is present
