"""Climate entities of the Orca heat pump: one per heating circuit.

A circuit regulated by its room sensor gets a thermostat. Any other circuit
gets a mode-only climate (on/off, heating or cooling), because a climate
target means a room temperature; its flow setpoint is a number entity.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
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

HVAC_MODES = {
    "heating": HVACMode.HEAT,
    "cooling": HVACMode.COOL,
    "auto_heat_cool": HVACMode.HEAT_COOL,
    # Switched by input ID2 or by hand: shown, but only the raw select sets it.
    "input_id2": HVACMode.AUTO,
    "manual": HVACMode.AUTO,
}
CIRCUIT_MODES = {
    HVACMode.HEAT: "heating",
    HVACMode.COOL: "cooling",
    HVACMode.HEAT_COOL: "auto_heat_cool",
}
ROOM_REGULATION = {"room", "room_and_outdoor"}


@dataclass(frozen=True, kw_only=True)
class OrcaClimateEntityDescription(ClimateEntityDescription, OrcaEntityDescription):
    """Describes an Orca climate entity."""


DESCRIPTION = OrcaClimateEntityDescription(
    key="climate", definition=catalog.CIRCUIT_ENABLE, name=None
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a climate entity per heating circuit."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaClimate(coordinator, description, slot)
        for description, slot in entity_targets(entry, (DESCRIPTION,))
    )


class OrcaClimate(OrcaEntity, ClimateEntity):
    """A heating circuit: on/off and mode, plus the room target if regulated."""

    entity_description: OrcaClimateEntityDescription
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        description: OrcaClimateEntityDescription,
        slot: int | None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description, slot)
        circuit = coordinator.topology.circuit(slot) if slot is not None else None
        self._room_sensor = bool(circuit and circuit.room_sensor)
        setpoint = catalog.ROOM_SETPOINT_HIGH
        if TYPE_CHECKING:
            assert setpoint.minimum is not None and setpoint.maximum is not None
        self._attr_min_temp = setpoint.minimum
        self._attr_max_temp = setpoint.maximum
        self._attr_target_temperature_step = setpoint.step

    @property
    def _room_regulated(self) -> bool:
        return self._room_sensor and any(
            self.value_of(regulation) in ROOM_REGULATION
            for regulation in (catalog.HEATING_REGULATION, catalog.COOLING_REGULATION)
        )

    @property
    @override
    def supported_features(self) -> ClimateEntityFeature:
        """Return on/off, plus the target while the room sensor regulates."""
        features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self._room_regulated:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        return features

    @property
    @override
    def hvac_mode(self) -> HVACMode | None:
        """Return off when the circuit is disabled, else its mode."""
        if self.reading.value is False:
            return HVACMode.OFF
        mode = self.value_of(catalog.CIRCUIT_MODE)
        return HVAC_MODES.get(mode) if isinstance(mode, str) else None

    @property
    @override
    def hvac_modes(self) -> list[HVACMode]:
        """Return the settable modes, plus auto while the circuit is in it."""
        modes = [HVACMode.OFF, *CIRCUIT_MODES]
        mode = self.value_of(catalog.CIRCUIT_MODE)
        if isinstance(mode, str) and HVAC_MODES.get(mode) is HVACMode.AUTO:
            modes.append(HVACMode.AUTO)
        return modes

    @property
    @override
    def hvac_action(self) -> HVACAction | None:
        """Return what the circuit is doing, from its pump and the heat pump."""
        if (
            self.hvac_mode is HVACMode.OFF
            or self.value_of(catalog.SYSTEM_ENABLE) is False
        ):
            return HVACAction.OFF
        if self.value_of(catalog.DEFROST_ACTIVE):
            return HVACAction.DEFROSTING
        if self.value_of(catalog.CIRCUIT_PUMP):
            match self.value_of(catalog.OUTDOOR_UNIT_STATE):
                case "heating":
                    return HVACAction.HEATING
                case "cooling":
                    return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    @override
    def native_current_temperature(self) -> float | None:
        """Return the room temperature, if the circuit has a room sensor."""
        value = self.value_of(catalog.ROOM_TEMPERATURE) if self._room_sensor else None
        return value if isinstance(value, float) else None

    @property
    @override
    def native_target_temperature(self) -> float | None:
        """Return the comfort room temperature while the room sensor regulates."""
        value = (
            self.value_of(catalog.ROOM_SETPOINT_HIGH) if self._room_regulated else None
        )
        return value if isinstance(value, float) else None

    def _mode_writes(self, hvac_mode: HVACMode) -> list[TagWrite]:
        enable = self.entity_description.definition
        if hvac_mode is HVACMode.OFF:
            # The mode stays, so turning on resumes it.
            return [(enable, self.slot, False)]
        writes: list[TagWrite] = []
        if (mode := CIRCUIT_MODES.get(hvac_mode)) is not None:
            writes.append((catalog.CIRCUIT_MODE, self.slot, mode))
        # Mode before enable, so the circuit never starts in the old mode.
        writes.append((enable, self.slot, True))
        return writes

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the circuit's mode, or switch it off."""
        await async_write_values(self.coordinator, self._mode_writes(hvac_mode))

    @override
    async def async_turn_on(self) -> None:
        """Switch the circuit on in its current mode."""
        await self.async_write(True)

    @override
    async def async_turn_off(self) -> None:
        """Switch the circuit off."""
        await self.async_write(False)

    @override
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the comfort room temperature, and the mode if given."""
        writes: list[TagWrite] = []
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            self._valid_mode_or_raise("hvac", hvac_mode, self.hvac_modes)
            writes = self._mode_writes(hvac_mode)
        writes.append((catalog.ROOM_SETPOINT_HIGH, self.slot, kwargs[ATTR_TEMPERATURE]))
        await async_write_values(self.coordinator, writes)
