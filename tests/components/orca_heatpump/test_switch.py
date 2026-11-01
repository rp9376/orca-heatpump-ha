"""Tests for the switches."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

SYSTEM = "switch.heat_pump_system"
(SYSTEM_TAG,) = catalog.SYSTEM_ENABLE.tag_names()


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the switches."""
    return [Platform.SWITCH]


@pytest.fixture(autouse=True)
def writable(emulator: Emulator) -> None:
    """Accept writes to the system switch."""
    emulator.writable.add(SYSTEM_TAG)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Each pump gets the on/off settings of its elements."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("values", "service", "written", "state"),
    [
        pytest.param({}, SERVICE_TURN_OFF, 0, STATE_OFF, id="off"),
        pytest.param({SYSTEM_TAG: "0"}, SERVICE_TURN_ON, 1, STATE_ON, id="on"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_turn_on_off(
    hass: HomeAssistant, emulator: Emulator, service: str, written: int, state: str
) -> None:
    """Switching writes the tag and shows the value read back."""
    await hass.services.async_call(
        SWITCH_DOMAIN, service, {ATTR_ENTITY_ID: SYSTEM}, blocking=True
    )
    await hass.async_block_till_done()

    assert emulator.writes == [(SYSTEM_TAG, written)]
    assert (current := hass.states.get(SYSTEM)) is not None
    assert current.state == state
