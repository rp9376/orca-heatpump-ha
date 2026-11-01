"""Base entity of the Orca Heat Pump integration."""

from typing import override

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client.models import Element, Reading, TagDef, Value
from .const import DOMAIN
from .coordinator import OrcaCoordinator


def device_identifier(entry_id: str, element: Element, slot: int | None) -> str:
    """Return the identifier of the device an element's entities belong to."""
    if element is Element.CIRCUIT:
        return f"{entry_id}_circuit{slot}"
    if element is Element.SYSTEM:
        return entry_id
    return f"{entry_id}_{element.value}"


class OrcaEntity(CoordinatorEntity[OrcaCoordinator]):
    """An entity backed by one catalog entry (in one circuit slot)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        definition: TagDef,
        slot: int | None = None,
        key: str | None = None,
    ) -> None:
        """Initialize the entity; ``key`` overrides the catalog key."""
        super().__init__(coordinator)
        self.definition = definition
        self.slot = slot
        key = key or definition.key
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = (
            f"{entry_id}_circuit{slot}_{key}"
            if slot is not None
            else f"{entry_id}_{key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, device_identifier(entry_id, definition.element, slot))
            }
        )

    @property
    def reading(self) -> Reading:
        """Return the entity's current reading."""
        return self.coordinator.data.reading(self.definition, self.slot)

    @property
    def value(self) -> Value | None:
        """Return the entity's current value, or None."""
        return self.reading.value

    @property
    @override
    def available(self) -> bool:
        """Return whether the tag has a value; a stale value still counts."""
        return super().available and self.reading.value is not None
