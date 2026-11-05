"""Polling of the heat pump."""

from dataclasses import dataclass, field
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client.client import OrcaClient
from .client.errors import OrcaAuthError, OrcaError, OrcaTooManyUsersError
from .client.models import DeviceIdentity, PumpTopology, Snapshot, TimerProgramme
from .const import (
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL,
    SESSIONS_EXHAUSTED_AFTER,
    TIMER_SCAN_INTERVAL,
)
from .helpers import refs_for

type OrcaConfigEntry = ConfigEntry[OrcaRuntimeData]


@dataclass
class OrcaRuntimeData:
    """Objects of a loaded config entry."""

    client: OrcaClient
    coordinator: OrcaCoordinator
    timers: OrcaTimerCoordinator
    topology: PumpTopology
    identity: DeviceIdentity
    unique_ids: set[str] = field(default_factory=set)


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
        self._refused = 0
        # Also after a reload, which starts counting anew.
        ir.async_delete_issue(self.hass, DOMAIN, self.sessions_issue_id)
        return snapshot


class OrcaTimerCoordinator(DataUpdateCoordinator[dict[int, TimerProgramme]]):
    """Reads the weekly timer programmes, through the same client."""

    config_entry: OrcaConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: OrcaConfigEntry, client: OrcaClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} timers",
            update_interval=TIMER_SCAN_INTERVAL,
            always_update=False,
        )
        self.client = client

    @override
    async def _async_update_data(self) -> dict[int, TimerProgramme]:
        try:
            programmes = await self.client.async_read_timers()
        except OrcaError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
        # Keep a programme that didn't come back complete this time.
        return {**(self.data or {}), **programmes}
