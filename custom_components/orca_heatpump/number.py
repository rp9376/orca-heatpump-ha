"""Number entities of the Orca heat pump: setpoints and settings.

Every range is the manufacturer's, from the catalog; the client refuses
anything outside it before a request is sent.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .client.models import TagDef
from .const import CONF_ALLOW_POWER_LIMITS
from .coordinator import OrcaConfigEntry
from .entity import (
    EntityContext,
    OrcaEntity,
    OrcaEntityDescription,
    entity_targets,
    heater_stage,
    mixing_circuit,
    room_sensor,
)

# The pump takes one write at a time.
PARALLEL_UPDATES = 1

OUTDOOR_REGULATION = ("outdoor", "room_and_outdoor")


@dataclass(frozen=True, kw_only=True)
class OrcaNumberEntityDescription(NumberEntityDescription, OrcaEntityDescription):
    """Describes an Orca number."""


def _number(
    definition: TagDef,
    *,
    enabled: bool = True,
    category: EntityCategory | None = EntityCategory.CONFIG,
    step: float | None = None,
    **kwargs: Any,
) -> OrcaNumberEntityDescription:
    return OrcaNumberEntityDescription(
        key=definition.key,
        definition=definition,
        native_min_value=definition.minimum,
        native_max_value=definition.maximum,
        native_step=step or definition.step,
        mode=NumberMode.BOX,
        entity_registry_enabled_default=enabled,
        entity_category=category,
        **kwargs,
    )


def _temperature(definition: TagDef, **kwargs: Any) -> OrcaNumberEntityDescription:
    return _number(
        definition,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        **kwargs,
    )


def _difference(definition: TagDef, **kwargs: Any) -> OrcaNumberEntityDescription:
    return _number(
        definition,
        device_class=NumberDeviceClass.TEMPERATURE_DELTA,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        **kwargs,
    )


def _duration(
    definition: TagDef, unit: UnitOfTime, **kwargs: Any
) -> OrcaNumberEntityDescription:
    return _number(
        definition,
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=unit,
        **kwargs,
    )


def _power_limit(definition: TagDef) -> OrcaNumberEntityDescription:
    # Opt-in and whole percent only (ADR 0012); otherwise a sensor shows it.
    return _number(
        definition,
        native_unit_of_measurement=PERCENTAGE,
        step=1,
        exists_fn=lambda context, _: bool(context.options.get(CONF_ALLOW_POWER_LIMITS)),
    )


def _heating_regulation(
    *regulations: str, expected: bool = True
) -> Callable[[EntityContext, int | None], bool]:
    """Return whether the circuit's heating regulation is (not) one of these.

    Decided at setup, like the names and defaults that depend on it.
    """

    def exists(context: EntityContext, slot: int | None) -> bool:
        value = context.snapshot.value(catalog.HEATING_REGULATION, slot)
        return (value in regulations) is expected

    return exists


DESCRIPTIONS: tuple[OrcaNumberEntityDescription, ...] = (
    _power_limit(catalog.HP_POWER_LIMIT_HEATING),
    _power_limit(catalog.HP_POWER_LIMIT_DHW),
    _power_limit(catalog.HP_POWER_LIMIT_COOLING),
    _power_limit(catalog.QUIET_POWER_LIMIT),
    _temperature(catalog.QUIET_OUTDOOR_TEMP, enabled=False),
    *(
        _duration(definition, UnitOfTime.MINUTES, enabled=False, exists_fn=exists)
        for definition, exists in (
            (catalog.HEATER_STAGE1_DELAY, heater_stage(1)),
            (catalog.HEATER_STAGE2_DELAY, heater_stage(2)),
            (catalog.HEATER_STAGE3_DELAY, heater_stage(3)),
        )
    ),
    *(
        _temperature(definition, enabled=False, exists_fn=exists)
        for definition, exists in (
            (catalog.HEATER_STAGE1_OUTDOOR_TEMP, heater_stage(1)),
            (catalog.HEATER_STAGE2_OUTDOOR_TEMP, heater_stage(2)),
            (catalog.HEATER_STAGE3_OUTDOOR_TEMP, heater_stage(3)),
        )
    ),
    _duration(catalog.ADDITIONAL_SOURCE_DELAY, UnitOfTime.MINUTES, enabled=False),
    _temperature(catalog.ADDITIONAL_SOURCE_OUTDOOR_TEMP, enabled=False),
    _temperature(catalog.SCREED_DRYING_MIN_FLOW, enabled=False),
    _temperature(catalog.SCREED_DRYING_MAX_FLOW, enabled=False),
    # On a constant-temperature circuit the maximum is the flow setpoint (R8).
    _temperature(
        catalog.MAX_FLOW_HEATING,
        category=None,
        translation_key="flow_setpoint",
        exists_fn=_heating_regulation("constant"),
    ),
    _temperature(
        catalog.MAX_FLOW_HEATING,
        category=None,
        exists_fn=_heating_regulation("constant", expected=False),
    ),
    _temperature(catalog.MIN_FLOW_HEATING, enabled=False),
    _difference(catalog.HP_BOOST_FOR_CIRCUIT, enabled=False, exists_fn=mixing_circuit),
    # The heating curve only matters with outdoor-based regulation.
    *(
        _difference(
            catalog.CURVE_PARALLEL_SHIFT,
            category=None,
            enabled=outdoor,
            exists_fn=_heating_regulation(*OUTDOOR_REGULATION, expected=outdoor),
        )
        for outdoor in (True, False)
    ),
    *(
        _number(
            catalog.CURVE_SLOPE,
            category=None,
            enabled=outdoor,
            exists_fn=_heating_regulation(*OUTDOOR_REGULATION, expected=outdoor),
        )
        for outdoor in (True, False)
    ),
    # The climate entity sets the comfort temperature.
    _temperature(
        catalog.ROOM_SETPOINT_HIGH,
        category=None,
        enabled=False,
        exists_fn=room_sensor,
    ),
    _temperature(catalog.ROOM_SETPOINT_LOW, category=None, exists_fn=room_sensor),
    _temperature(catalog.MIN_FLOW_COOLING, enabled=False),
    _temperature(catalog.COOLING_FLOW_AT_20, enabled=False),
    _temperature(catalog.COOLING_FLOW_AT_30, enabled=False),
    _temperature(catalog.AUTO_HEATING_SWITCH_TEMP, enabled=False),
    _duration(catalog.AUTO_HEATING_SWITCH_DELAY, UnitOfTime.HOURS, enabled=False),
    _temperature(catalog.AUTO_COOLING_SWITCH_TEMP, enabled=False),
    _duration(catalog.AUTO_COOLING_SWITCH_DELAY, UnitOfTime.HOURS, enabled=False),
    _temperature(catalog.DHW_SETPOINT_LOW),
    _difference(catalog.DHW_ON_DIFFERENCE, enabled=False),
    _difference(catalog.DHW_HP_BOOST, enabled=False),
    _temperature(catalog.LEGIONELLA_TEMPERATURE, enabled=False),
    # An hour of the day, not a duration.
    _number(catalog.LEGIONELLA_HOUR, enabled=False),
    _temperature(catalog.SOLAR_MIN_COLLECTOR_TEMP, enabled=False),
    _difference(catalog.SOLAR_ON_DIFFERENCE, enabled=False),
    _difference(catalog.SOLAR_OFF_DIFFERENCE, enabled=False),
    _temperature(catalog.BUFFER_HIGH_HEATING),
    _temperature(catalog.BUFFER_LOW_HEATING),
    _temperature(catalog.BUFFER_HIGH_COOLING),
    _temperature(catalog.BUFFER_LOW_COOLING),
    _difference(catalog.BUFFER_ON_DIFFERENCE),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the numbers of the pump's elements."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaNumber(coordinator, description, slot)
        for description, slot in entity_targets(entry, DESCRIPTIONS)
    )


class OrcaNumber(OrcaEntity, NumberEntity):
    """A number backed by one writable tag."""

    entity_description: OrcaNumberEntityDescription

    @property
    @override
    def native_value(self) -> float | None:
        """Return the tag's value."""
        value = self.reading.value
        return value if isinstance(value, int | float) else None

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Write the value; the client checks the range and step first."""
        await self.async_write(value)
