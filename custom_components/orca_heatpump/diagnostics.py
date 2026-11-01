"""Diagnostics for the Orca Heat Pump integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import OrcaConfigEntry
from .helpers import topology_to_data

TO_REDACT = {CONF_HOST, CONF_USERNAME, CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OrcaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics; the tag section can become a test fixture."""
    data = entry.runtime_data
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "identity": {
            "firmware": data.identity.firmware,
            "outdoor_unit": data.identity.outdoor_unit,
        },
        "topology": topology_to_data(data.topology),
        "tags": {
            tag: {
                "raw": reading.raw,
                "value": reading.value,
                "reason": reading.reason,
                "stale": reading.stale,
            }
            for tag, reading in sorted(data.coordinator.data.readings.items())
        },
    }
