"""The alarm reset button of the Orca heat pump."""

from dataclasses import dataclass
from typing import override

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .coordinator import OrcaConfigEntry
from .entity import OrcaEntity, OrcaEntityDescription, entity_targets

# The pump takes one write at a time.
PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class OrcaButtonEntityDescription(ButtonEntityDescription, OrcaEntityDescription):
    """Describes an Orca button."""


# Disabled until the live write test confirms how the controller clears it.
DESCRIPTION = OrcaButtonEntityDescription(
    key="alarm_reset",
    definition=catalog.ALARM_RESET,
    entity_category=EntityCategory.CONFIG,
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the alarm reset button."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaButton(coordinator, description, slot)
        for description, slot in entity_targets(entry, (DESCRIPTION,))
    )


class OrcaButton(OrcaEntity, ButtonEntity):
    """A button that sets one boolean tag."""

    entity_description: OrcaButtonEntityDescription

    @override
    async def async_press(self) -> None:
        """Set the tag."""
        await self.async_write(True)
