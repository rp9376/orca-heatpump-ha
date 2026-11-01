"""Tests for the water heater."""

from typing import Any

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from homeassistant.components.water_heater import (
    ATTR_OPERATION_MODE,
    DOMAIN as WATER_HEATER_DOMAIN,
    SERVICE_SET_OPERATION_MODE,
    SERVICE_SET_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_HEAT_PUMP,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, STATE_OFF, Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

WATER_HEATER = "water_heater.hot_water"
(ENABLE,) = catalog.DHW_ENABLE.tag_names()
(SETPOINT,) = catalog.DHW_SETPOINT_HIGH.tag_names()


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the water heater."""
    return [Platform.WATER_HEATER]


@pytest.fixture(autouse=True)
def writable(emulator: Emulator) -> None:
    """Accept writes to the water heater's tags."""
    emulator.writable.update((ENABLE, SETPOINT))


def water_heater(hass: HomeAssistant) -> State:
    """Return the water heater's state."""
    state = hass.states.get(WATER_HEATER)
    assert state is not None
    return state


async def call(hass: HomeAssistant, service: str, **data: Any) -> None:
    """Call a water heater action and wait for the refresh."""
    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: WATER_HEATER, **data},
        blocking=True,
    )
    await hass.async_block_till_done()


@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Every pump with hot water gets the water heater."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("values", "service", "data", "written", "state"),
    [
        pytest.param({}, SERVICE_TURN_OFF, {}, 0, STATE_OFF, id="turn_off"),
        pytest.param(
            {ENABLE: "0"}, SERVICE_TURN_ON, {}, 1, STATE_HEAT_PUMP, id="turn_on"
        ),
        pytest.param(
            {},
            SERVICE_SET_OPERATION_MODE,
            {ATTR_OPERATION_MODE: STATE_OFF},
            0,
            STATE_OFF,
            id="operation_off",
        ),
        pytest.param(
            {ENABLE: "0"},
            SERVICE_SET_OPERATION_MODE,
            {ATTR_OPERATION_MODE: STATE_HEAT_PUMP},
            1,
            STATE_HEAT_PUMP,
            id="operation_heat_pump",
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_on_off(
    hass: HomeAssistant,
    emulator: Emulator,
    service: str,
    data: dict[str, Any],
    written: int,
    state: str,
) -> None:
    """Hot water switches on and off through its enable."""
    await call(hass, service, **data)

    assert emulator.writes == [(ENABLE, written)]
    assert water_heater(hass).state == state


@pytest.mark.parametrize(
    ("data", "writes", "state"),
    [
        pytest.param(
            {ATTR_TEMPERATURE: 45},
            [(SETPOINT, 450)],
            STATE_HEAT_PUMP,
            id="temperature",
        ),
        pytest.param(
            {ATTR_TEMPERATURE: 45, ATTR_OPERATION_MODE: STATE_OFF},
            [(ENABLE, 0), (SETPOINT, 450)],
            STATE_OFF,
            id="with_operation",
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_set_temperature(
    hass: HomeAssistant,
    emulator: Emulator,
    data: dict[str, Any],
    writes: list[tuple[str, int]],
    state: str,
) -> None:
    """The target is the higher hot water setpoint."""
    await call(hass, SERVICE_SET_TEMPERATURE, **data)

    assert emulator.writes == writes
    assert water_heater(hass).state == state
    assert water_heater(hass).attributes[ATTR_TEMPERATURE] == 45


@pytest.mark.parametrize(
    ("data", "translation_key"),
    [
        pytest.param(
            {ATTR_TEMPERATURE: 45, ATTR_OPERATION_MODE: "eco"},
            "not_valid_operation_mode",
            id="operation",
        ),
        pytest.param({ATTR_TEMPERATURE: 60}, "invalid_value", id="above_range"),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_set_temperature_invalid(
    hass: HomeAssistant,
    emulator: Emulator,
    data: dict[str, Any],
    translation_key: str,
) -> None:
    """Invalid values are refused before anything is written."""
    with pytest.raises(ServiceValidationError) as err:
        await call(hass, SERVICE_SET_TEMPERATURE, **data)

    assert err.value.translation_key == translation_key
    assert emulator.writes == []


@pytest.mark.parametrize("values", [{ENABLE: ""}])
@pytest.mark.usefixtures("init_integration")
async def test_unreadable(hass: HomeAssistant) -> None:
    """Without a readable enable the water heater is unavailable."""
    assert water_heater(hass).state == "unavailable"
