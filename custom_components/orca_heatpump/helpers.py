"""Helpers of the integration."""

from collections.abc import Mapping
import re
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .client.catalog import CATALOG
from .client.models import CircuitKind, CircuitTopology, Element, PumpTopology, TagRef
from .const import OLD_CONF_HOST, OLD_DOMAIN

_HOST_RE = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]{1,5})?")


@callback
def async_create_session(
    hass: HomeAssistant, *, auto_cleanup: bool = True
) -> aiohttp.ClientSession:
    """Return a web session that keeps no cookies.

    The display also sets its login token as a cookie. With a host name, a
    shared session's jar would store it and send it in place of the token of
    every other client of that display, losing track of their sessions.
    Created during setup, Home Assistant detaches it when the entry unloads.
    """
    return async_create_clientsession(
        hass, auto_cleanup=auto_cleanup, cookie_jar=aiohttp.DummyCookieJar()
    )


def normalize_host(value: str) -> str:
    """Return a host or ``host:port`` in one spelling, without the default port.

    Raises ValueError for anything else: the text becomes part of the URLs the
    client requests, so a path in it could reach other endpoints of the display.
    """
    host = value.strip().lower()
    if _HOST_RE.fullmatch(host) is None:
        raise ValueError(f"not a host: {value!r}")
    name, port = split_host(host)
    if not 0 < port < 65536:
        raise ValueError(f"not a port: {port}")
    return name if port == 80 else f"{name}:{port}"


@callback
def old_integration_has(hass: HomeAssistant, host: str) -> bool:
    """Return whether an enabled orca-energy-ha entry polls this display."""
    name = split_host(host)[0]
    return any(
        old.disabled_by is None and name in (old.unique_id, old.data.get(OLD_CONF_HOST))
        for old in hass.config_entries.async_entries(OLD_DOMAIN)
    )


def topology_label(topology: PumpTopology) -> str:
    """Return a topology in the manufacturer's notation, for repair issues."""
    parts = [
        ("MK" if circuit.kind is CircuitKind.MIXING else "DK")
        + str(circuit.slot)
        + ("+RF" if circuit.room_sensor else "")
        for circuit in topology.circuits
    ]
    parts += [
        name
        for name, present in (
            ("SV", topology.dhw),
            ("SOLAR", topology.solar),
            ("ZALOG", topology.buffer),
        )
        if present
    ]
    return f"{topology.schema} ({', '.join(parts)})"


def split_host(value: str) -> tuple[str, int]:
    """Split ``host`` or ``host:port``; the display itself always uses port 80."""
    host, sep, port = value.strip().rpartition(":")
    if sep and port.isdigit() and host and not host.endswith(":"):
        return host, int(port)
    return value.strip(), 80


def topology_to_data(topology: PumpTopology) -> dict[str, Any]:
    """Return a topology as JSON-safe data for the config entry."""
    return {
        "schema": topology.schema,
        "circuits": [
            {"slot": c.slot, "kind": c.kind.value, "room_sensor": c.room_sensor}
            for c in topology.circuits
        ],
        "dhw": topology.dhw,
        "solar": topology.solar,
        "buffer": topology.buffer,
    }


def topology_from_data(data: Mapping[str, Any]) -> PumpTopology:
    """Return the topology stored by topology_to_data."""
    return PumpTopology(
        data["schema"],
        tuple(
            CircuitTopology(c["slot"], CircuitKind(c["kind"]), c["room_sensor"])
            for c in data["circuits"]
        ),
        dhw=data["dhw"],
        solar=data["solar"],
        buffer=data["buffer"],
    )


def element_present(topology: PumpTopology, element: Element, slot: int | None) -> bool:
    """Return whether the pump has an element (or, for circuits, the slot)."""
    if element is Element.CIRCUIT:
        return topology.circuit(slot) is not None if slot is not None else False
    return {
        Element.SYSTEM: True,
        Element.DHW: topology.dhw,
        Element.SOLAR: topology.solar,
        Element.BUFFER: topology.buffer,
    }[element]


def refs_for(topology: PumpTopology) -> tuple[TagRef, ...]:
    """Return the catalog tags to poll for the elements the pump has."""
    return tuple(
        (definition, slot)
        for definition in CATALOG
        for _, slot in definition.refs()
        if element_present(topology, definition.element, slot)
    )
