"""Tests for the alarm reset button."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

RESET = "button.heat_pump_reset_alarms"
(RESET_TAG,) = catalog.ALARM_RESET.tag_names()


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the button."""
    return [Platform.BUTTON]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """The heat pump gets an alarm reset button."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


async def test_disabled_by_default(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """The button stays disabled until the live write test confirms it."""
    entry = entity_registry.async_get(RESET)
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_press(hass: HomeAssistant, emulator: Emulator) -> None:
    """Pressing sets the reset tag."""
    emulator.writable.add(RESET_TAG)

    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: RESET}, blocking=True
    )

    assert emulator.writes == [(RESET_TAG, 1)]
