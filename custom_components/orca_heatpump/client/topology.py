"""Topology detection: which circuits and elements a pump has."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from . import catalog
from .errors import OrcaProtocolError
from .models import (
    SLOTS,
    CircuitKind,
    CircuitTopology,
    PumpTopology,
    Reading,
    Reason,
    Snapshot,
    TagDef,
)


@dataclass(frozen=True, slots=True)
class Schema:
    """One of the controller's wiring schemas."""

    circuits: tuple[CircuitKind | None, CircuitKind | None, CircuitKind | None]
    dhw: bool
    solar: bool


M, D = CircuitKind.MIXING, CircuitKind.DIRECT

# The manufacturer's wiring diagrams (`2_Shema` values); the comments are its
# names. tests/client/test_topology.py checks this table against them.
SCHEMAS: Final[Mapping[int, Schema]] = MappingProxyType(
    {
        1: Schema((M, None, None), dhw=True, solar=False),  # MK1+SV
        2: Schema((M, None, None), dhw=True, solar=True),  # MK1+SV+SOLAR
        3: Schema((D, None, None), dhw=True, solar=False),  # DK1+SV
        4: Schema((D, None, None), dhw=True, solar=True),  # DK1+SV+SOLAR
        5: Schema((M, D, None), dhw=True, solar=False),  # MK1+DK2+SV
        6: Schema((M, D, None), dhw=True, solar=True),  # MK1+DK2+SV+SOLAR
        7: Schema((D, D, None), dhw=True, solar=False),  # DK1+DK2+SV
        8: Schema((D, D, None), dhw=True, solar=True),  # DK1+DK2+SV+SOLAR
        9: Schema((M, D, None), dhw=False, solar=False),  # MK1+DK2
        10: Schema((D, D, None), dhw=False, solar=False),  # DK1+DK2
        11: Schema((M, None, None), dhw=False, solar=False),  # MK1
        12: Schema((D, None, None), dhw=False, solar=False),  # DK1
        13: Schema((None, D, None), dhw=False, solar=False),  # DK2
        14: Schema((None, None, None), dhw=True, solar=False),  # San.voda
        15: Schema((None, None, None), dhw=True, solar=True),  # SV+SOLAR
        16: Schema((None, D, None), dhw=True, solar=False),  # DK2+SV
        17: Schema((None, D, None), dhw=True, solar=True),  # DK2+SV+SOLAR
        18: Schema((None, M, None), dhw=False, solar=False),  # MK2
        19: Schema((None, M, None), dhw=True, solar=False),  # MK2+SV
        20: Schema((None, M, None), dhw=True, solar=True),  # MK2+SV+SOLAR
        21: Schema((D, M, None), dhw=False, solar=False),  # DK1+MK2
        22: Schema((D, M, None), dhw=True, solar=False),  # DK1+MK2+SV
        23: Schema((D, M, None), dhw=True, solar=True),  # DK1+MK2+SV+SOLAR
        24: Schema((M, M, None), dhw=False, solar=False),  # MK1+MK2
        25: Schema((M, M, None), dhw=True, solar=False),  # MK1+MK2+SV
        26: Schema((M, M, None), dhw=True, solar=True),  # MK1+MK2+SV+SOLAR
        27: Schema((None, None, None), dhw=False, solar=True),  # SOLAR
        28: Schema((None, None, D), dhw=False, solar=False),  # DK3
        29: Schema((None, None, D), dhw=True, solar=False),  # DK3+SV
        30: Schema((D, None, D), dhw=False, solar=False),  # DK1+DK3
        31: Schema((D, None, D), dhw=True, solar=False),  # DK1+DK3+SV
        32: Schema((M, None, D), dhw=False, solar=False),  # MK1+DK3
        33: Schema((M, None, D), dhw=True, solar=False),  # MK1+DK3+SV
        34: Schema((None, D, D), dhw=False, solar=False),  # DK2+DK3
        35: Schema((None, D, D), dhw=True, solar=False),  # DK2+DK3+SV
        36: Schema((None, M, D), dhw=False, solar=False),  # MK2+DK3
        37: Schema((None, M, D), dhw=True, solar=False),  # MK2+DK3+SV
        38: Schema((D, D, D), dhw=False, solar=False),  # DK1+DK2+DK3
        39: Schema((D, D, D), dhw=True, solar=False),  # DK1+DK2+DK3+SV
        40: Schema((M, D, D), dhw=False, solar=False),  # MK1+DK2+DK3
        41: Schema((M, D, D), dhw=True, solar=False),  # MK1+DK2+DK3+SV
        42: Schema((M, M, D), dhw=False, solar=False),  # MK1+MK2+DK3
        43: Schema((M, M, D), dhw=True, solar=False),  # MK1+MK2+DK3+SV
        44: Schema((D, M, D), dhw=False, solar=False),  # DK1+MK2+DK3
        45: Schema((D, M, D), dhw=True, solar=False),  # DK1+MK2+DK3+SV
    }
)

TOPOLOGY_TAGS: Final = tuple(
    tag
    for definition in (
        catalog.SCHEMA,
        catalog.BUFFER_PRESENT,
        catalog.ROOM_SENSOR_CONFIGURED,
        catalog.ROOM_TEMPERATURE,
    )
    for tag in definition.tag_names()
)


def detect_topology(snapshot: Snapshot) -> PumpTopology:
    """Return the pump's topology from a snapshot of TOPOLOGY_TAGS.

    An element is only taken as absent when its signals were actually read;
    a signal that was not received raises OrcaProtocolError instead.
    """
    reading = _received(snapshot, catalog.SCHEMA)
    if not isinstance(reading.value, int) or reading.value not in SCHEMAS:
        raise OrcaProtocolError(f"unknown schema {reading.raw!r}")
    schema = SCHEMAS[reading.value]
    circuits = tuple(
        CircuitTopology(slot, kind, _room_sensor(snapshot, slot))
        for slot, kind in zip(SLOTS, schema.circuits, strict=True)
        if kind is not None
    )
    return PumpTopology(
        reading.value,
        circuits,
        dhw=schema.dhw,
        solar=schema.solar,
        buffer=_received(snapshot, catalog.BUFFER_PRESENT).value is True,
    )


def _room_sensor(snapshot: Snapshot, slot: int) -> bool:
    flag = _received(snapshot, catalog.ROOM_SENSOR_CONFIGURED, slot)
    if isinstance(flag.value, bool):
        return flag.value
    # Firmware without the flag: a connected sensor still reads a temperature.
    return _received(snapshot, catalog.ROOM_TEMPERATURE, slot).value is not None


def _received(
    snapshot: Snapshot, definition: TagDef, slot: int | None = None
) -> Reading:
    reading = snapshot.reading(definition, slot)
    if reading.reason is Reason.NO_RESPONSE:
        raise OrcaProtocolError(f"{definition.key} was not received")
    return reading
