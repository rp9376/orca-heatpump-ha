"""The hot water tank of the Orca heat pump."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.water_heater import (
    ATTR_OPERATION_MODE,
    DOMAIN as WATER_HEATER_DOMAIN,
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .coordinator import OrcaConfigEntry, OrcaCoordinator
from .entity import (
    OrcaEntity,
    OrcaEntityDescription,
    TagWrite,
    async_write_values,
    entity_targets,
)

# The pump takes one write at a time.
PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class OrcaWaterHeaterEntityDescription(
    WaterHeaterEntityDescription, OrcaEntityDescription
):
    """Describes the Orca water heater."""


DESCRIPTION = OrcaWaterHeaterEntityDescription(
    key="water_heater", definition=catalog.DHW_ENABLE, name=None
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the water heater if the pump heats hot water."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaWaterHeater(coordinator, description, slot)
        for description, slot in entity_targets(entry, (DESCRIPTION,))
    )


class OrcaWaterHeater(OrcaEntity, WaterHeaterEntity):
    """Hot water: on or off, and the higher of its two setpoints.

    The weekly timer switches between the higher and the lower setpoint;
    the lower one is a number entity.
    """

    entity_description: OrcaWaterHeaterEntityDescription
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = [STATE_OFF, STATE_HEAT_PUMP]
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        description: OrcaWaterHeaterEntityDescription,
        slot: int | None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description, slot)
        setpoint = catalog.DHW_SETPOINT_HIGH
        if TYPE_CHECKING:
            assert setpoint.minimum is not None and setpoint.maximum is not None
        self._attr_min_temp = setpoint.minimum
        self._attr_max_temp = setpoint.maximum
        self._attr_target_temperature_step = setpoint.step

    @property
    @override
    def current_operation(self) -> str | None:
        """Return heat_pump while hot water is on."""
        return STATE_HEAT_PUMP if self.reading.value else STATE_OFF

    @property
    @override
    def native_current_temperature(self) -> float | None:
        """Return the temperature at the top of the tank."""
        value = self.value_of(catalog.DHW_TEMP_TOP)
        return value if isinstance(value, float) else None

    @property
    @override
    def native_target_temperature(self) -> float | None:
        """Return the higher hot water setpoint."""
        value = self.value_of(catalog.DHW_SETPOINT_HIGH)
        return value if isinstance(value, float) else None

    def _operation_write(self, operation_mode: str) -> TagWrite:
        return (
            self.entity_description.definition,
            None,
            operation_mode == STATE_HEAT_PUMP,
        )

    @override
    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Switch hot water on or off."""
        await async_write_values(
            self.coordinator, (self._operation_write(operation_mode),)
        )

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch hot water on."""
        await self.async_write(True)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch hot water off."""
        await self.async_write(False)

    @override
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the higher hot water setpoint, and the operation if given."""
        writes: list[TagWrite] = []
        if (operation_mode := kwargs.get(ATTR_OPERATION_MODE)) is not None:
            if operation_mode not in self._attr_operation_list:
                raise ServiceValidationError(
                    translation_domain=WATER_HEATER_DOMAIN,
                    translation_key="not_valid_operation_mode",
                    translation_placeholders={
                        "entity_id": self.entity_id,
                        "operation_mode": operation_mode,
                        "operation_list": ", ".join(self._attr_operation_list),
                    },
                )
            writes.append(self._operation_write(operation_mode))
        writes.append((catalog.DHW_SETPOINT_HIGH, None, kwargs[ATTR_TEMPERATURE]))
        await async_write_values(self.coordinator, writes)
