"""Select entities of the Orca heat pump: programmes, modes and timers."""

from dataclasses import asdict, dataclass
from typing import Any, override

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .client.models import TagDef
from .coordinator import OrcaConfigEntry, OrcaCoordinator
from .entity import (
    EntityContext,
    OrcaEntity,
    OrcaEntityDescription,
    any_circuit,
    entity_targets,
)

# The pump takes one write at a time.
PARALLEL_UPDATES = 1

HEATER_SOURCES = ("electric_heater", "electric_heater_and_additional_source")
ATTR_SCHEDULE = "schedule"


@dataclass(frozen=True, kw_only=True)
class OrcaSelectEntityDescription(SelectEntityDescription, OrcaEntityDescription):
    """Describes an Orca select; a timer select shows its programme."""

    timer: bool = False


def _select(
    definition: TagDef,
    *,
    enabled: bool = True,
    category: EntityCategory | None = EntityCategory.CONFIG,
    **kwargs: Any,
) -> OrcaSelectEntityDescription:
    return OrcaSelectEntityDescription(
        key=definition.key,
        definition=definition,
        entity_registry_enabled_default=enabled,
        entity_category=category,
        **kwargs,
    )


def _electric_heater(context: EntityContext, slot: int | None) -> bool:
    source = context.snapshot.value(catalog.ADDITIONAL_SOURCE)
    return not isinstance(source, str) or source in HEATER_SOURCES


DESCRIPTIONS: tuple[OrcaSelectEntityDescription, ...] = (
    _select(catalog.OPERATING_PROGRAMME, category=None),
    _select(catalog.QUICK_ROOM_MODE, category=None, exists_fn=any_circuit),
    _select(catalog.QUIET_MODE, enabled=False),
    _select(catalog.QUIET_TIMER_PROGRAMME, enabled=False, timer=True),
    _select(catalog.HEATER_MODE, exists_fn=_electric_heater),
    _select(catalog.HEATER_PARALLEL, enabled=False, exists_fn=_electric_heater),
    _select(catalog.CIRCUIT_MODE),
    _select(catalog.HEATING_REGULATION, enabled=False),
    _select(catalog.COOLING_REGULATION, enabled=False),
    _select(catalog.TIMER_PROGRAMME, timer=True),
    _select(catalog.LOW_REGIME_ACTION, enabled=False),
    _select(catalog.DHW_TIMER_PROGRAMME, timer=True),
    _select(catalog.LEGIONELLA_DAY, enabled=False),
    _select(catalog.LEGIONELLA_CYCLE, enabled=False),
    _select(catalog.BUFFER_TIMER_PROGRAMME, enabled=False, timer=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the selects of the pump's elements."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        (OrcaTimerSelect if description.timer else OrcaSelect)(
            coordinator, description, slot
        )
        for description, slot in entity_targets(entry, DESCRIPTIONS)
    )


class OrcaSelect(OrcaEntity, SelectEntity):
    """A select backed by one enum tag."""

    entity_description: OrcaSelectEntityDescription

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        description: OrcaSelectEntityDescription,
        slot: int | None,
    ) -> None:
        """Initialize the entity with the slot's options."""
        super().__init__(coordinator, description, slot)
        self._attr_options = list(description.definition.options_for(slot).values())

    @property
    @override
    def current_option(self) -> str | None:
        """Return the selected option; None for a value nobody has seen yet."""
        value = self.reading.value
        return value if isinstance(value, str) else None

    @override
    async def async_select_option(self, option: str) -> None:
        """Write the option."""
        await self.async_write(option)


class OrcaTimerSelect(OrcaSelect):
    """A timer programme select; an attribute shows the selected programme."""

    _unrecorded_attributes = frozenset({ATTR_SCHEDULE})

    @override
    async def async_added_to_hass(self) -> None:
        """Also follow the timer programmes."""
        await super().async_added_to_hass()
        timers = self.coordinator.config_entry.runtime_data.timers
        self.async_on_remove(timers.async_add_listener(self._handle_coordinator_update))

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the selected programme's ranges; none all day or unread."""
        # The raw value is the programme's number; 0 is all day.
        raw = self.reading.raw
        programmes = self.coordinator.config_entry.runtime_data.timers.data or {}
        ranges = programmes.get(int(raw)) if raw and raw.isdigit() else None
        return {
            ATTR_SCHEDULE: None
            if ranges is None
            else [asdict(time_range) for time_range in ranges]
        }
