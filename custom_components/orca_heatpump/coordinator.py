"""Polling of the heat pump."""

from dataclasses import dataclass
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client.client import OrcaClient
from .client.errors import OrcaAuthError, OrcaError, OrcaTooManyUsersError
from .client.models import DeviceIdentity, PumpTopology, Snapshot
from .const import DOMAIN, LOGGER, SCAN_INTERVAL, SESSIONS_EXHAUSTED_AFTER
from .helpers import refs_for

type OrcaConfigEntry = ConfigEntry[OrcaRuntimeData]


@dataclass
class OrcaRuntimeData:
    """Objects of a loaded config entry."""

    client: OrcaClient
    coordinator: OrcaCoordinator
    topology: PumpTopology
    identity: DeviceIdentity


class OrcaCoordinator(DataUpdateCoordinator[Snapshot]):
    """Reads every tag the pump's elements need, once per interval."""

    config_entry: OrcaConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: OrcaConfigEntry,
        client: OrcaClient,
        topology: PumpTopology,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )
        self.client = client
        self.topology = topology
        self._refs = refs_for(topology)
        self._refused = 0

    @property
    def sessions_issue_id(self) -> str:
        """Return the ID of this entry's 'sessions exhausted' repair issue."""
        return f"sessions_exhausted_{self.config_entry.entry_id}"

    @override
    async def _async_update_data(self) -> Snapshot:
        try:
            snapshot = await self.client.async_read(self._refs)
        except OrcaAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except OrcaTooManyUsersError as err:
            self._refused += 1
            if self._refused == SESSIONS_EXHAUSTED_AFTER:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    self.sessions_issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="sessions_exhausted",
                )
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="too_many_users"
            ) from err
        except OrcaError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
        if self._refused:
            self._refused = 0
            ir.async_delete_issue(self.hass, DOMAIN, self.sessions_issue_id)
        return snapshot
