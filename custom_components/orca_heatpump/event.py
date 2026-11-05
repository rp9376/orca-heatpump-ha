"""Alarm events of the Orca heat pump, for notifications from automations."""

from dataclasses import dataclass
from typing import override

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import catalog
from .client.models import Reason
from .coordinator import OrcaConfigEntry, OrcaCoordinator
from .entity import OrcaEntity, OrcaEntityDescription, entity_targets
from .sensor import UNKNOWN_ALARM

PARALLEL_UPDATES = 0

NO_ALARM = "none"
ALARM_RAISED = "alarm_raised"
ALARM_CLEARED = "alarm_cleared"


@dataclass(frozen=True, kw_only=True)
class OrcaEventEntityDescription(EventEntityDescription, OrcaEntityDescription):
    """Describes an Orca event entity."""


DESCRIPTION = OrcaEventEntityDescription(
    key="alarm_event",
    definition=catalog.ALARM_CODE,
    event_types=[ALARM_RAISED, ALARM_CLEARED],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the alarm event entity."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        OrcaAlarmEvent(coordinator, description, slot)
        for description, slot in entity_targets(entry, (DESCRIPTION,))
    )


class OrcaAlarmEvent(OrcaEntity, EventEntity):
    """Fires when an alarm appears or goes away.

    Only changes the coordinator observes fire; an alarm already active at
    startup does not, since the alarm sensors show it.
    """

    entity_description: OrcaEventEntityDescription

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        description: OrcaEventEntityDescription,
        slot: int | None,
    ) -> None:
        """Initialize the entity with the current alarm."""
        super().__init__(coordinator, description, slot)
        self._alarm = self._current()

    def _current(self) -> tuple[str, str | None] | None:
        reading = self.reading
        if reading.reason is Reason.UNKNOWN_OPTION:
            return UNKNOWN_ALARM, reading.raw
        if reading.value is None:
            return None
        return str(reading.value), reading.raw

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        current = self._current()
        previous, self._alarm = self._alarm, (current or self._alarm)
        if current is not None and previous is not None and current != previous:
            # One update carries one event: a switch to another alarm is a raise.
            if current[0] == NO_ALARM:
                self._trigger_event(ALARM_CLEARED, _attributes(previous))
            else:
                self._trigger_event(ALARM_RAISED, _attributes(current))
        super()._handle_coordinator_update()


def _attributes(alarm: tuple[str, str | None]) -> dict[str, str | int]:
    return {"alarm": alarm[0], "code": int(alarm[1] or 0)}
