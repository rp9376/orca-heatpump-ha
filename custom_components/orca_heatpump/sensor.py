"""Sensors of the Orca heat pump: temperatures, states and the active alarm."""

from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
from .client.models import Reason, TagDef, Value
from .const import UNKNOWN_ALARM
from .coordinator import OrcaConfigEntry
from .entity import (
    OrcaEntity,
    OrcaEntityDescription,
    any_circuit,
    entity_targets,
    mixing_circuit,
    power_limit,
    repurposed_solar_input,
    room_sensor,
)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class OrcaSensorEntityDescription(SensorEntityDescription, OrcaEntityDescription):
    """Describes an Orca sensor."""


def _temperature(
    definition: TagDef, *, enabled: bool = True, diagnostic: bool = False, **kwargs: Any
) -> OrcaSensorEntityDescription:
    return OrcaSensorEntityDescription(
        key=definition.key,
        definition=definition,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=None if diagnostic else SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_registry_enabled_default=enabled,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
        **kwargs,
    )


def _enum(
    definition: TagDef, *, enabled: bool = True, diagnostic: bool = False
) -> OrcaSensorEntityDescription:
    return OrcaSensorEntityDescription(
        key=definition.key,
        definition=definition,
        device_class=SensorDeviceClass.ENUM,
        options=sorted(
            {
                o
                for slot in (None, 1, 2, 3)
                for o in definition.options_for(slot).values()
            }
        ),
        entity_registry_enabled_default=enabled,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
    )


def _power_limit(definition: TagDef) -> OrcaSensorEntityDescription:
    return OrcaSensorEntityDescription(
        key=definition.key,
        definition=definition,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=power_limit(definition, writable=False),
    )


DESCRIPTIONS: tuple[OrcaSensorEntityDescription, ...] = (
    _temperature(catalog.OUTDOOR_TEMPERATURE),
    _temperature(catalog.HP_TEMPERATURE),
    _temperature(catalog.HP_TARGET_TEMPERATURE),
    OrcaSensorEntityDescription(
        key="outdoor_unit_power",
        definition=catalog.OUTDOOR_UNIT_POWER,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _enum(catalog.OUTDOOR_UNIT_STATE),
    _enum(catalog.VALVE_3WAY),
    OrcaSensorEntityDescription(
        key="alarm_code",
        definition=catalog.ALARM_CODE,
        device_class=SensorDeviceClass.ENUM,
        options=[*catalog.ALARM_CODE.options.values(), UNKNOWN_ALARM],
    ),
    _power_limit(catalog.HP_POWER_LIMIT_HEATING),
    _power_limit(catalog.HP_POWER_LIMIT_DHW),
    _power_limit(catalog.HP_POWER_LIMIT_COOLING),
    _power_limit(catalog.QUIET_POWER_LIMIT),
    OrcaSensorEntityDescription(
        key="screed_drying_days",
        definition=catalog.SCREED_DRYING_DAYS,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        exists_fn=any_circuit,
    ),
    # A position in the programme, not a duration.
    OrcaSensorEntityDescription(
        key="screed_drying_current_day",
        definition=catalog.SCREED_DRYING_CURRENT_DAY,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        exists_fn=any_circuit,
    ),
    _enum(catalog.ADDITIONAL_SOURCE, enabled=False, diagnostic=True),
    _enum(catalog.HEATER_STAGES, enabled=False, diagnostic=True),
    OrcaSensorEntityDescription(
        key="schema",
        definition=catalog.SCHEMA,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _temperature(catalog.FLOW_TEMPERATURE),
    # A direct circuit's flow follows the heat pump's own target.
    _temperature(catalog.FLOW_TARGET, exists_fn=mixing_circuit),
    _temperature(catalog.ROOM_TEMPERATURE, exists_fn=room_sensor),
    _temperature(catalog.ROOM_SETPOINT_ACTIVE, enabled=False, diagnostic=True),
    _enum(catalog.MIXING_VALVE_STATE),
    OrcaSensorEntityDescription(
        key="mixing_valve_position",
        definition=catalog.MIXING_VALVE_POSITION,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    _enum(catalog.INSTALLATION_TYPE, enabled=False, diagnostic=True),
    _enum(catalog.ROOM_SENSOR_TYPE, enabled=False, diagnostic=True),
    _temperature(catalog.DHW_TEMP_TOP),
    _temperature(catalog.DHW_TEMP_BOTTOM),
    _temperature(catalog.SOLAR_COLLECTOR_TEMPERATURE),
    _temperature(catalog.SOLAR_INPUT_TEMPERATURE, exists_fn=repurposed_solar_input),
    _enum(catalog.SOLAR_TARGET, enabled=False, diagnostic=True),
    _temperature(catalog.SOLAR_MAX_DHW_TEMP, enabled=False, diagnostic=True),
    _temperature(catalog.SOLAR_MAX_COLLECTOR_TEMP, enabled=False, diagnostic=True),
    _temperature(catalog.BUFFER_TEMPERATURE),
    _temperature(catalog.BUFFER_TARGET),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors of the pump's elements."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        (OrcaAlarmSensor if description.key == "alarm_code" else OrcaSensor)(
            coordinator, description, slot
        )
        for description, slot in entity_targets(entry, DESCRIPTIONS)
    )


class OrcaSensor(OrcaEntity, SensorEntity):
    """A sensor backed by one tag."""

    entity_description: OrcaSensorEntityDescription

    @property
    @override
    def native_value(self) -> Value | None:
        """Return the tag's value."""
        return self.reading.value


class OrcaAlarmSensor(OrcaSensor):
    """The active alarm; codes the catalog doesn't know still show."""

    @property
    @override
    def native_value(self) -> Value | None:
        """Return the alarm, or 'unknown_code' for codes nobody has seen yet."""
        if self.reading.reason is Reason.UNKNOWN_OPTION:
            return UNKNOWN_ALARM
        return self.reading.value

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the raw alarm code."""
        raw = self.reading.raw
        return {"code": int(raw) if raw and raw.lstrip("-").isdigit() else None}
