"""Tests for the climate entities."""

from collections.abc import Callable
from typing import Any

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant.common import (
    MockConfigEntry,
    async_fire_time_changed,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.models import TagDef
from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import REQUEST_REFRESH_DEFAULT_COOLDOWN
from tools.emulator import Emulator

UNDERFLOOR = "climate.underfloor_heating"
RADIATORS = "climate.radiators"


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the climate entities."""
    return [Platform.CLIMATE]


@pytest.fixture(autouse=True)
def writable(emulator: Emulator) -> None:
    """Accept writes to the climate tags."""
    for definition in (
        catalog.CIRCUIT_ENABLE,
        catalog.CIRCUIT_MODE,
        catalog.ROOM_SETPOINT_HIGH,
    ):
        emulator.writable.update(definition.tag_names())


def tag(definition: TagDef, slot: int | None = 1) -> str:
    """Return the tag of a catalog entry in a circuit slot."""
    name = definition.tag_name(slot)
    assert name is not None
    return name


def climate(hass: HomeAssistant, entity_id: str = UNDERFLOOR) -> State:
    """Return a climate entity's state."""
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def call(
    hass: HomeAssistant, service: str, entity_id: str = UNDERFLOOR, **data: Any
) -> None:
    """Call a climate action and wait for the refresh."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        service,
        {ATTR_ENTITY_ID: entity_id, **data},
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
    """Each circuit gets a climate; room-regulated ones get a thermostat."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("entity_id", "hvac_mode", "writes"),
    [
        pytest.param(
            RADIATORS,
            HVACMode.COOL,
            [(tag(catalog.CIRCUIT_MODE, 2), 2), (tag(catalog.CIRCUIT_ENABLE, 2), 1)],
            id="mode_before_enable",
        ),
        pytest.param(
            RADIATORS,
            HVACMode.HEAT,
            [(tag(catalog.CIRCUIT_ENABLE, 2), 1)],
            id="same_mode_only_enables",
        ),
        pytest.param(
            UNDERFLOOR,
            HVACMode.HEAT_COOL,
            [(tag(catalog.CIRCUIT_MODE), 3)],
            id="enabled_circuit_mode_only",
        ),
        pytest.param(
            UNDERFLOOR,
            HVACMode.OFF,
            [(tag(catalog.CIRCUIT_ENABLE), 0)],
            id="off_keeps_mode",
        ),
    ],
)
async def test_set_hvac_mode(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    entity_id: str,
    hvac_mode: HVACMode,
    writes: list[tuple[str, int]],
) -> None:
    """Setting a mode writes only what changes: the mode first, then enable."""
    await call(hass, SERVICE_SET_HVAC_MODE, entity_id, hvac_mode=hvac_mode)

    assert emulator.writes == writes
    assert climate(hass, entity_id).state == hvac_mode


async def test_turn_off_and_on(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    init_integration: MockConfigEntry,
    emulator: Emulator,
) -> None:
    """Turning on resumes the circuit's mode instead of choosing one."""
    emulator.values[tag(catalog.CIRCUIT_MODE)] = "2"
    await call(hass, SERVICE_TURN_OFF)
    assert climate(hass).state == HVACMode.OFF

    await call(hass, SERVICE_TURN_ON)
    # The refresh after a second write waits out the debouncer's cooldown.
    freezer.tick(REQUEST_REFRESH_DEFAULT_COOLDOWN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert emulator.writes == [
        (tag(catalog.CIRCUIT_ENABLE), 0),
        (tag(catalog.CIRCUIT_ENABLE), 1),
    ]
    assert climate(hass).state == HVACMode.COOL


@pytest.mark.parametrize(
    "values",
    [
        pytest.param(
            {tag(catalog.CIRCUIT_MODE): mode, tag(catalog.CIRCUIT_ENABLE): "0"},
            id=f"mode_{mode}",
        )
        for mode in ("4", "5")
    ],
)
async def test_auto_mode(
    hass: HomeAssistant, init_integration: MockConfigEntry, emulator: Emulator
) -> None:
    """Modes switched outside Home Assistant show as auto; auto only enables."""
    assert HVACMode.AUTO in climate(hass).attributes[ATTR_HVAC_MODES]
    assert HVACMode.AUTO not in climate(hass, RADIATORS).attributes[ATTR_HVAC_MODES]

    await call(hass, SERVICE_SET_HVAC_MODE, hvac_mode=HVACMode.AUTO)

    assert emulator.writes == [(tag(catalog.CIRCUIT_ENABLE), 1)]
    assert climate(hass).state == HVACMode.AUTO


@pytest.mark.parametrize("values", [{tag(catalog.CIRCUIT_MODE): "9"}])
@pytest.mark.usefixtures("init_integration")
async def test_unknown_mode(hass: HomeAssistant) -> None:
    """An enabled circuit in a mode nobody has seen yet has no known state."""
    assert climate(hass).state == STATE_UNKNOWN


@pytest.mark.parametrize(
    ("values", "action"),
    [
        pytest.param({}, HVACAction.HEATING, id="heating"),
        pytest.param(
            {tag(catalog.OUTDOOR_UNIT_STATE, None): "2"},
            HVACAction.COOLING,
            id="cooling",
        ),
        pytest.param(
            {tag(catalog.DEFROST_ACTIVE, None): "1"},
            HVACAction.DEFROSTING,
            id="defrosting",
        ),
        pytest.param(
            {tag(catalog.OUTDOOR_UNIT_STATE, None): "0"},
            HVACAction.IDLE,
            id="heat_pump_off",
        ),
        pytest.param({tag(catalog.CIRCUIT_PUMP): "0"}, HVACAction.IDLE, id="pump_off"),
        pytest.param(
            {tag(catalog.SYSTEM_ENABLE, None): "0"}, HVACAction.OFF, id="system_off"
        ),
        pytest.param(
            {tag(catalog.CIRCUIT_ENABLE): "0", tag(catalog.DEFROST_ACTIVE, None): "1"},
            HVACAction.OFF,
            id="circuit_off",
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_hvac_action(hass: HomeAssistant, action: HVACAction) -> None:
    """The action follows the circuit pump, defrost and the heat pump's state."""
    assert climate(hass).attributes[ATTR_HVAC_ACTION] == action


@pytest.mark.parametrize("pump", ["duo"], indirect=True)
@pytest.mark.parametrize(
    ("data", "writes"),
    [
        pytest.param(
            {ATTR_TEMPERATURE: 21.5},
            [(tag(catalog.ROOM_SETPOINT_HIGH), 215)],
            id="temperature",
        ),
        pytest.param(
            {ATTR_TEMPERATURE: 21, ATTR_HVAC_MODE: HVACMode.COOL},
            [(tag(catalog.CIRCUIT_MODE), 2), (tag(catalog.ROOM_SETPOINT_HIGH), 210)],
            id="with_mode",
        ),
    ],
)
async def test_set_temperature(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    data: dict[str, Any],
    writes: list[tuple[str, int]],
) -> None:
    """A room-regulated circuit's target is its comfort room temperature."""
    await call(hass, SERVICE_SET_TEMPERATURE, **data)

    assert emulator.writes == writes
    assert climate(hass).attributes[ATTR_TEMPERATURE] == data[ATTR_TEMPERATURE]


@pytest.mark.parametrize("pump", ["duo"], indirect=True)
@pytest.mark.parametrize(
    ("data", "translation_key"),
    [
        pytest.param(
            {ATTR_TEMPERATURE: 21, ATTR_HVAC_MODE: HVACMode.AUTO},
            "not_valid_hvac_mode",
            id="mode_not_offered",
        ),
        pytest.param({ATTR_TEMPERATURE: 21.55}, "invalid_value", id="step"),
    ],
)
async def test_set_temperature_invalid(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    data: dict[str, Any],
    translation_key: str,
) -> None:
    """Invalid values are refused before anything is written."""
    with pytest.raises(ServiceValidationError) as err:
        await call(hass, SERVICE_SET_TEMPERATURE, **data)

    assert err.value.translation_key == translation_key
    assert emulator.writes == []


async def test_mode_only_has_no_target(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Without a room sensor the climate has no temperatures to set."""
    with pytest.raises(ServiceValidationError):
        await call(hass, SERVICE_SET_TEMPERATURE, temperature=21)

    attributes = climate(hass).attributes
    assert attributes[ATTR_CURRENT_TEMPERATURE] is None
    assert ATTR_TEMPERATURE not in attributes


@pytest.mark.parametrize("pump", ["duo"], indirect=True)
async def test_regulation_change(
    hass: HomeAssistant, init_integration: MockConfigEntry, emulator: Emulator
) -> None:
    """Outdoor-only regulation drops the target but keeps the room temperature."""
    assert climate(hass).attributes[ATTR_TEMPERATURE] == 20.1

    for definition in (catalog.HEATING_REGULATION, catalog.COOLING_REGULATION):
        emulator.values[tag(definition)] = "2"
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    attributes = climate(hass).attributes
    assert ATTR_TEMPERATURE not in attributes
    assert attributes[ATTR_CURRENT_TEMPERATURE] == 20.7
    assert attributes[ATTR_SUPPORTED_FEATURES] == (
        ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(
            lambda emulator: setattr(emulator.faults, "ignore_writes", True),
            id="not_applied",
        ),
        pytest.param(lambda emulator: emulator.writable.clear(), id="forbidden"),
    ],
)
async def test_write_failed(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    fault: Callable[[Emulator], None],
) -> None:
    """A write the pump doesn't take raises and leaves the state."""
    fault(emulator)

    with pytest.raises(HomeAssistantError) as err:
        await call(hass, SERVICE_TURN_OFF)

    assert err.value.translation_key == "write_failed"
    assert climate(hass).state == HVACMode.HEAT
