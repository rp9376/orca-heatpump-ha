"""Data model of the Orca client: tag definitions, readings and topology."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from types import MappingProxyType
from typing import Final

SLOTS: Final = (1, 2, 3)

type Value = bool | int | float | str


class Element(StrEnum):
    """Part of the heat pump a tag belongs to."""

    SYSTEM = "system"
    CIRCUIT = "circuit"
    DHW = "dhw"
    SOLAR = "solar"
    BUFFER = "buffer"


class Kind(StrEnum):
    """How a tag's raw integer is interpreted."""

    BOOL = "bool"
    NUMBER = "number"
    ENUM = "enum"


class Reason(StrEnum):
    """Why a reading has no value."""

    NOT_CONNECTED = "not_connected"
    UNKNOWN_TAG = "unknown_tag"
    TAG_ERROR = "tag_error"
    EMPTY = "empty"
    CONVERSION_FAILED = "conversion_failed"
    UNKNOWN_OPTION = "unknown_option"
    NO_RESPONSE = "no_response"
    NOT_IN_SLOT = "not_in_slot"


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class TagDef:
    """One catalog entry: what a tag means and how to read and write it.

    Circuit entries name one tag per slot in ``slot_tags``, because the
    display's names are irregular; ``None`` marks a slot without that tag.
    Other entries name their tag in ``tag``. ``minimum`` and ``maximum`` are
    in engineering units (after scaling).
    """

    key: str
    element: Element
    kind: Kind
    tag: str | None = None
    slot_tags: tuple[str | None, str | None, str | None] | None = None
    scale: int = 1
    unit: str | None = None
    writable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    options: Mapping[int, str] = field(default_factory=lambda: MappingProxyType({}))
    slot_options: Mapping[int, Mapping[int, str]] = field(
        default_factory=lambda: MappingProxyType({})
    )
    mixing_only: bool = False

    def tag_name(self, slot: int | None = None) -> str | None:
        """Return the tag of this entry, for a slot if it is a circuit entry."""
        if self.slot_tags is None:
            return self.tag
        if slot not in SLOTS:
            raise ValueError(f"{self.key} is a circuit entry; slot 1-3 required")
        return self.slot_tags[slot - 1]

    def tag_names(self) -> tuple[str, ...]:
        """Return every tag this entry may read."""
        if self.slot_tags is None:
            return () if self.tag is None else (self.tag,)
        return tuple(tag for tag in self.slot_tags if tag is not None)

    def refs(self) -> tuple[TagRef, ...]:
        """Return (definition, slot) for every tag of this entry."""
        if self.slot_tags is None:
            return () if self.tag is None else ((self, None),)
        return tuple((self, slot) for slot in SLOTS if self.slot_tags[slot - 1])

    def options_for(self, slot: int | None = None) -> Mapping[int, str]:
        """Return the enum options, which may differ for one slot."""
        if slot is not None and slot in self.slot_options:
            return self.slot_options[slot]
        return self.options


type TagRef = tuple[TagDef, int | None]


@dataclass(frozen=True, slots=True)
class Reading:
    """A decoded tag value; ``value`` is None with a ``reason`` when unavailable."""

    value: Value | None
    raw: str | None = None
    reason: Reason | None = None
    stale: bool = False


NO_RESPONSE: Final = Reading(None, reason=Reason.NO_RESPONSE)
NOT_IN_SLOT: Final = Reading(None, reason=Reason.NOT_IN_SLOT)


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Readings of one poll, by tag name. Looking up any tag never fails."""

    readings: Mapping[str, Reading]

    def get(self, tag: str) -> Reading:
        """Return the reading of a tag; unread tags have no response."""
        return self.readings.get(tag, NO_RESPONSE)

    def reading(self, definition: TagDef, slot: int | None = None) -> Reading:
        """Return the reading of a catalog entry (for a slot)."""
        if (tag := definition.tag_name(slot)) is None:
            return NOT_IN_SLOT
        return self.get(tag)

    def value(self, definition: TagDef, slot: int | None = None) -> Value | None:
        """Return the value of a catalog entry, or None."""
        return self.reading(definition, slot).value


class CircuitKind(StrEnum):
    """Type of heating circuit."""

    MIXING = "mixing"
    DIRECT = "direct"


@dataclass(frozen=True, slots=True)
class CircuitTopology:
    """One heating circuit present on the pump."""

    slot: int
    kind: CircuitKind
    room_sensor: bool


@dataclass(frozen=True, slots=True)
class PumpTopology:
    """Which elements the pump has, from its schema and configuration."""

    schema: int
    circuits: tuple[CircuitTopology, ...]
    dhw: bool
    solar: bool
    buffer: bool

    def circuit(self, slot: int) -> CircuitTopology | None:
        """Return the circuit in a slot, or None if the slot is empty."""
        return next((c for c in self.circuits if c.slot == slot), None)


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    """What the pump tells about itself."""

    firmware_build: int | None
    firmware_date: date | None
    outdoor_unit: str | None

    @property
    def firmware(self) -> str | None:
        """Return the firmware as shown to users, e.g. ``61 (2016-12-12)``."""
        if self.firmware_build is None:
            return None
        if self.firmware_date is None:
            return str(self.firmware_build)
        return f"{self.firmware_build} ({self.firmware_date.isoformat()})"
