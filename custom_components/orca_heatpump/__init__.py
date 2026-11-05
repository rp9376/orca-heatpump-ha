"""The Orca Heat Pump integration."""

import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    IntegrationError,
)
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import catalog
from .client.client import OrcaClient
from .client.errors import OrcaAuthError, OrcaError, OrcaTooManyUsersError
from .client.models import DeviceIdentity, PumpTopology, Snapshot
from .const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_TOPOLOGY,
    DOMAIN,
    OLD_CONF_HOST,
    OLD_DOMAIN,
)
from .coordinator import (
    OrcaConfigEntry,
    OrcaCoordinator,
    OrcaRuntimeData,
    OrcaTimerCoordinator,
)
from .helpers import apply_overrides, split_host, topology_from_data, topology_to_data

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.EVENT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER,
]
POWER_LIMITS = (
    catalog.HP_POWER_LIMIT_HEATING,
    catalog.HP_POWER_LIMIT_DHW,
    catalog.HP_POWER_LIMIT_COOLING,
    catalog.QUIET_POWER_LIMIT,
)


async def async_setup_entry(hass: HomeAssistant, entry: OrcaConfigEntry) -> None:
    """Set up Orca Heat Pump from a config entry."""
    host, port = split_host(entry.data[CONF_HOST])
    client = OrcaClient(
        async_get_clientsession(hass),
        host,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        port=port,
    )
    try:
        identity = await client.async_read_identity()
        detected = await client.async_detect_topology()
    except OrcaError as err:
        await client.async_logout()
        raise _setup_error(err) from err

    topology = apply_overrides(_stored_topology(hass, entry, detected), entry.options)
    coordinator = OrcaCoordinator(hass, entry, client, topology)
    try:
        await coordinator.async_config_entry_first_refresh()
    except IntegrationError:
        await client.async_logout()
        raise
    timers = OrcaTimerCoordinator(hass, entry, client)
    await timers.async_refresh()
    entry.runtime_data = OrcaRuntimeData(
        client, coordinator, timers, topology, identity
    )
    _register_devices(hass, entry, topology, identity, coordinator.data)
    _remove_unused_power_limits(hass, entry)
    _check_old_integration(hass, entry, host)

    async def _logout(event: Event) -> None:
        await client.async_logout()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _logout))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: OrcaConfigEntry) -> None:
    """Unload a config entry and free the display's session."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
    await entry.runtime_data.client.async_logout()


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the entry's repair issues."""
    for issue in ("topology_changed", "old_integration", "sessions_exhausted"):
        ir.async_delete_issue(hass, DOMAIN, f"{issue}_{entry.entry_id}")


@callback
def _remove_unused_power_limits(hass: HomeAssistant, entry: OrcaConfigEntry) -> None:
    """Remove the power limits' sensors or numbers, whichever the option hides.

    Changing the option swaps one form for the other (ADR 0012).
    """
    unused = (
        Platform.SENSOR
        if entry.options.get(CONF_ALLOW_POWER_LIMITS)
        else Platform.NUMBER
    )
    registry = er.async_get(hass)
    for definition in POWER_LIMITS:
        unique_id = f"{entry.entry_id}_{definition.key}"
        if entity_id := registry.async_get_entity_id(unused, DOMAIN, unique_id):
            registry.async_remove(entity_id)


def _setup_error(err: OrcaError) -> IntegrationError:
    if isinstance(err, OrcaAuthError):
        return ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="invalid_auth"
        )
    if isinstance(err, OrcaTooManyUsersError):
        return ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="too_many_users"
        )
    return ConfigEntryNotReady(
        translation_domain=DOMAIN,
        translation_key="cannot_connect",
        translation_placeholders={"error": str(err)},
    )


@callback
def _stored_topology(
    hass: HomeAssistant, entry: OrcaConfigEntry, detected: PumpTopology
) -> PumpTopology:
    """Return the stored topology; a different detected one raises an issue.

    The entities keep following the stored topology until the user accepts
    the change, so a misread signal can't make devices disappear.
    """
    issue_id = f"topology_changed_{entry.entry_id}"
    stored = entry.data[CONF_TOPOLOGY]
    if (new := topology_to_data(detected)) == stored:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
    else:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="topology_changed",
            data={"entry_id": entry.entry_id, "topology": json.dumps(new)},
        )
    return topology_from_data(stored)


@callback
def _register_devices(
    hass: HomeAssistant,
    entry: OrcaConfigEntry,
    topology: PumpTopology,
    identity: DeviceIdentity,
    snapshot: Snapshot,
) -> None:
    """Create the heat pump device and one sub-device per element; drop the rest."""
    registry = dr.async_get(hass)
    model = (
        "Heat pump"
        if identity.outdoor_unit is None
        else f"Heat pump ({identity.outdoor_unit.capitalize()})"
    )
    main = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Orca Energija",
        model=model,
        sw_version=identity.firmware,
        translation_key="heat_pump",
    )
    keep = {main.id}
    for circuit in topology.circuits:
        name = snapshot.value(catalog.CIRCUIT_NAME, circuit.slot)
        keep.add(
            registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, f"{entry.entry_id}_circuit{circuit.slot}")},
                manufacturer="Orca Energija",
                model="Heating circuit",
                translation_key=f"circuit_{name}"
                if isinstance(name, str)
                else "circuit",
                translation_placeholders={"slot": str(circuit.slot)},
                via_device_id=main.id,
            ).id
        )
    for element, present in (
        ("dhw", topology.dhw),
        ("solar", topology.solar),
        ("buffer", topology.buffer),
    ):
        if present:
            keep.add(
                registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers={(DOMAIN, f"{entry.entry_id}_{element}")},
                    manufacturer="Orca Energija",
                    translation_key=element,
                    via_device_id=main.id,
                ).id
            )
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if device.id not in keep:
            registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )


@callback
def _check_old_integration(
    hass: HomeAssistant, entry: OrcaConfigEntry, host: str
) -> None:
    """Raise an issue while orca-energy-ha polls the same pump (ADR 0001)."""
    issue_id = f"old_integration_{entry.entry_id}"
    if any(
        old.disabled_by is None and host in (old.unique_id, old.data.get(OLD_CONF_HOST))
        for old in hass.config_entries.async_entries(OLD_DOMAIN)
    ):
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="old_integration",
            translation_placeholders={"host": host},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
