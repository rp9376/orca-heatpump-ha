"""Repairs for the Orca Heat Pump integration."""

import json
from typing import Any

from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.core import HomeAssistant

from .const import CONF_TOPOLOGY


class TopologyChangedFlow(RepairsFlow):
    """Accept a changed topology: store it and reload the entry."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the flow with the issue's data."""
        self._entry_id: str = data["entry_id"]
        self._topology: dict[str, Any] = json.loads(data["topology"])

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> RepairsFlowResult:
        """Ask the user to confirm."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> RepairsFlowResult:
        """Store the new topology and reload."""
        if user_input is None:
            return self.async_show_form(step_id="confirm")
        if (
            entry := self.hass.config_entries.async_get_entry(self._entry_id)
        ) is not None:
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_TOPOLOGY: self._topology}
            )
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
        return self.async_create_entry(data={})


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """Return the fix flow of an issue; only a changed topology is fixable."""
    if data is None:
        raise ValueError(f"issue {issue_id} has no data")
    return TopologyChangedFlow(data)
