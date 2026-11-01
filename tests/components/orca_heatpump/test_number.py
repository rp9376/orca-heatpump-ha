"""Tests for the number entities."""

from typing import Any

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.const import CONF_ALLOW_POWER_LIMITS
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

DHW_LOW = "number.hot_water_lower_temperature"
POWER_LIMIT = "number.heat_pump_power_limit_heating"
(DHW_LOW_TAG,) = catalog.DHW_SETPOINT_LOW.tag_names()
(POWER_LIMIT_TAG,) = catalog.HP_POWER_LIMIT_HEATING.tag_names()


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the numbers."""
    return [Platform.NUMBER]


@pytest.fixture(autouse=True)
def writable(emulator: Emulator) -> None:
    """Accept writes to the tags the tests set."""
    emulator.writable.update((DHW_LOW_TAG, POWER_LIMIT_TAG))


@pytest.fixture
def options() -> dict[str, Any]:
    """Allow changing the power limits."""
    return {CONF_ALLOW_POWER_LIMITS: True}


async def set_value(hass: HomeAssistant, entity_id: str, value: float) -> None:
    """Set a number and wait for the refresh."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await hass.async_block_till_done()


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Each pump gets the settings of its elements, named for its regulation."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("entity_id", "value", "write"),
    [
        pytest.param(DHW_LOW, 40.5, (DHW_LOW_TAG, 405), id="temperature"),
        pytest.param(POWER_LIMIT, 75, (POWER_LIMIT_TAG, 750), id="power_limit"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_set_value(
    hass: HomeAssistant,
    emulator: Emulator,
    entity_id: str,
    value: float,
    write: tuple[str, int],
) -> None:
    """A value is written in the pump's scale and read back."""
    await set_value(hass, entity_id, value)

    assert emulator.writes == [write]
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == value


@pytest.mark.parametrize(
    ("entity_id", "value", "translation_key"),
    [
        pytest.param(POWER_LIMIT, 39, "out_of_range", id="below_range"),
        pytest.param(DHW_LOW, 40.55, "invalid_value", id="step"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_set_value_invalid(
    hass: HomeAssistant,
    emulator: Emulator,
    entity_id: str,
    value: float,
    translation_key: str,
) -> None:
    """Values outside the range or step are refused before anything is sent."""
    with pytest.raises(ServiceValidationError) as err:
        await set_value(hass, entity_id, value)

    assert err.value.translation_key == translation_key
    assert emulator.writes == []


@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_enabled_by_default(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Only everyday settings start enabled; curves only with outdoor regulation."""
    entries = er.async_entries_for_config_entry(
        entity_registry, init_integration.entry_id
    )
    assert sorted(e.entity_id for e in entries if not e.disabled) == snapshot
