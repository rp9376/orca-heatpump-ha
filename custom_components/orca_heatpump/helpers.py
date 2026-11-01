"""Helpers of the integration that need no Home Assistant objects."""

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .client.catalog import CATALOG
from .client.models import CircuitKind, CircuitTopology, Element, PumpTopology, TagRef
from .const import (
    CONF_BUFFER,
    CONF_ROOM_SENSORS,
    CONF_SOLAR,
    OVERRIDE_ABSENT,
    OVERRIDE_PRESENT,
)


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


def _override(detected: bool, choice: object) -> bool:
    if choice == OVERRIDE_PRESENT:
        return True
    if choice == OVERRIDE_ABSENT:
        return False
    return detected


def apply_overrides(topology: PumpTopology, options: Mapping[str, Any]) -> PumpTopology:
    """Apply the user's corrections for setups detection gets wrong (#30)."""
    return replace(
        topology,
        circuits=tuple(
            replace(
                c,
                room_sensor=_override(
                    c.room_sensor, options.get(CONF_ROOM_SENSORS[c.slot - 1])
                ),
            )
            for c in topology.circuits
        ),
        solar=_override(topology.solar, options.get(CONF_SOLAR)),
        buffer=_override(topology.buffer, options.get(CONF_BUFFER)),
    )


def refs_for(topology: PumpTopology) -> tuple[TagRef, ...]:
    """Return the catalog tags to poll for the elements the pump has."""
    present = {
        Element.SYSTEM: True,
        Element.DHW: topology.dhw,
        Element.SOLAR: topology.solar,
        Element.BUFFER: topology.buffer,
    }
    slots = {c.slot for c in topology.circuits}
    return tuple(
        (definition, slot)
        for definition in CATALOG
        for _, slot in definition.refs()
        if (
            slot in slots
            if definition.element is Element.CIRCUIT
            else present[definition.element]
        )
    )
