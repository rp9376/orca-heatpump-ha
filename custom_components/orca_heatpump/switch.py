"""Switches of the Orca heat pump: the system and on/off settings.

Circuits and hot water switch through their climate and water heater.
"""

from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .client.models import TagDef
from .coordinator import OrcaConfigEntry
from .entity import OrcaEntity, OrcaEntityDescription, entity_targets

# The pump takes one write at a time.
PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class OrcaSwitchEntityDescription(SwitchEntityDescription, OrcaEntityDescription):
    """Describes an Orca switch."""


def _switch(
    definition: TagDef,
    *,
    enabled: bool = False,
    category: EntityCategory | None = EntityCategory.CONFIG,
) -> OrcaSwitchEntityDescription:
    return OrcaSwitchEntityDescription(
        key=definition.key,
        definition=definition,
        device_class=SwitchDeviceClass.SWITCH,
        entity_registry_enabled_default=enabled,
        entity_category=category,
    )


DESCRIPTIONS: tuple[OrcaSwitchEntityDescription, ...] = (
    _switch(catalog.SYSTEM_ENABLE, enabled=True, category=None),
    _switch(catalog.PV_FUNCTION),
    _switch(catalog.SCREED_DRYING),
    _switch(catalog.ANTI_BLOCK_PROGRAMME),
    _switch(catalog.ADDITIONAL_SOURCE_PARALLEL),
    _switch(catalog.AUTO_HEATING_SWITCH),
    _switch(catalog.AUTO_COOLING_SWITCH),
    _switch(catalog.LEGIONELLA_ENABLE, enabled=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switches of the pump's elements."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaSwitch(coordinator, description, slot)
        for description, slot in entity_targets(entry, DESCRIPTIONS)
    )


class OrcaSwitch(OrcaEntity, SwitchEntity):
    """A switch backed by one boolean tag."""

    entity_description: OrcaSwitchEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the setting is on."""
        value = self.reading.value
        return value if isinstance(value, bool) else None

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the setting on."""
        await self.async_write(True)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the setting off."""
        await self.async_write(False)
