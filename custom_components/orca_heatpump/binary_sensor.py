"""Binary sensors of the Orca heat pump: pumps, defrost and alarms."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .client.models import TagDef, Value
from .coordinator import OrcaConfigEntry
from .entity import OrcaEntity, OrcaEntityDescription, entity_targets, heater_stage

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class OrcaBinarySensorEntityDescription(
    BinarySensorEntityDescription, OrcaEntityDescription
):
    """Describes an Orca binary sensor."""

    is_on_fn: Callable[[Value], bool] = lambda value: value is True


def _problem(
    key: str, definition: TagDef, *, enabled: bool = False
) -> OrcaBinarySensorEntityDescription:
    return OrcaBinarySensorEntityDescription(
        key=key,
        definition=definition,
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=enabled,
    )


DESCRIPTIONS: tuple[OrcaBinarySensorEntityDescription, ...] = (
    OrcaBinarySensorEntityDescription(
        key="pump_p0",
        definition=catalog.PUMP_P0,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    OrcaBinarySensorEntityDescription(
        key="flow_switch",
        definition=catalog.FLOW_SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    OrcaBinarySensorEntityDescription(
        key="defrost_active", definition=catalog.DEFROST_ACTIVE
    ),
    OrcaBinarySensorEntityDescription(
        key="quiet_active",
        definition=catalog.QUIET_ACTIVE,
        entity_registry_enabled_default=False,
    ),
    *(
        OrcaBinarySensorEntityDescription(
            key=definition.key,
            definition=definition,
            device_class=BinarySensorDeviceClass.RUNNING,
            exists_fn=heater_stage(stage),
        )
        for stage, definition in enumerate(
            (
                catalog.HEATER_STAGE1_ON,
                catalog.HEATER_STAGE2_ON,
                catalog.HEATER_STAGE3_ON,
            ),
            1,
        )
    ),
    OrcaBinarySensorEntityDescription(
        key="circuit_pump",
        definition=catalog.CIRCUIT_PUMP,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    OrcaBinarySensorEntityDescription(
        key="solar_pump",
        definition=catalog.SOLAR_PUMP,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _problem("alarm_active", catalog.ALARM_ACTIVE, enabled=True),
    _problem("alarm_outdoor_unit", catalog.ALARM_OUTDOOR_UNIT),
    _problem("alarm_flow_switch", catalog.ALARM_FLOW_SWITCH),
    _problem("alarm_no_flow", catalog.ALARM_NO_FLOW),
    _problem("alarm_hp_temperature_low", catalog.ALARM_HP_TEMPERATURE_LOW),
    _problem("alarm_flow_temperature", catalog.ALARM_FLOW_TEMPERATURE),
    _problem("alarm_room_sensor", catalog.ALARM_ROOM_SENSOR),
    OrcaBinarySensorEntityDescription(
        key="alarm_error",
        definition=catalog.ALARM_ERROR,
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=False,
        is_on_fn=lambda value: value != 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors of the pump's elements."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaBinarySensor(coordinator, description, slot)
        for description, slot in entity_targets(entry, DESCRIPTIONS)
    )


class OrcaBinarySensor(OrcaEntity, BinarySensorEntity):
    """A binary sensor backed by one tag."""

    entity_description: OrcaBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the sensor is on."""
        value = self.reading.value
        return None if value is None else self.entity_description.is_on_fn(value)
