"""Conversion between raw tag values and typed values."""

from collections.abc import Mapping
import math

from .catalog import TIMER_PROGRAMMES, TIMER_RANGES, timer_tags
from .errors import OrcaValueError
from .models import (
    NO_RESPONSE,
    Kind,
    Reading,
    Reason,
    TagDef,
    TimerProgramme,
    TimerRange,
    Value,
)
from .protocol import NOT_CONNECTED, STATUS_OK, STATUS_UNKNOWN_TAG, Record

# The tag isn't there on this firmware or isn't bound in the display's project.
_ABSENT_STATUSES = frozenset(
    {
        STATUS_UNKNOWN_TAG,
        "E_TAG_NOT_BOUNDED_TO_A_TAG",
        "E_BOUNDED_TAG_NOT_CONNECTED_TO_PROTOCOL",
    }
)
_TEMPORARY_STATUSES = frozenset({"E_UNACTIVETAG", "E_INACTIVETAG", "E_FAIL"})
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def decode(definition: TagDef, slot: int | None, record: Record | None) -> Reading:
    """Decode a record; anything odd becomes a reading without a value."""
    if record is None:
        return NO_RESPONSE
    if record.status in _ABSENT_STATUSES:
        return Reading(None, reason=Reason.UNKNOWN_TAG)
    if record.status in _TEMPORARY_STATUSES:
        return NO_RESPONSE
    if record.status != STATUS_OK:
        return Reading(None, raw=record.status, reason=Reason.TAG_ERROR)
    raw = (record.value or "").strip()
    if not raw:
        return Reading(None, raw=record.value, reason=Reason.EMPTY)
    if raw == NOT_CONNECTED:
        return Reading(None, raw=raw, reason=Reason.NOT_CONNECTED)
    try:
        number = int(raw)
    except ValueError:
        return Reading(None, raw=raw, reason=Reason.CONVERSION_FAILED)
    if definition.kind is Kind.BOOL:
        if number not in (0, 1):
            return Reading(None, raw=raw, reason=Reason.CONVERSION_FAILED)
        return Reading(number == 1, raw=raw)
    if definition.kind is Kind.NUMBER:
        if definition.scale == 1:
            return Reading(number, raw=raw)
        return Reading(number / definition.scale, raw=raw)
    if (option := definition.options_for(slot).get(number)) is None:
        return Reading(None, raw=raw, reason=Reason.UNKNOWN_OPTION)
    return Reading(option, raw=raw)


def encode(definition: TagDef, slot: int | None, value: Value) -> int:
    """Return the raw integer to write, or raise OrcaValueError.

    Only catalog entries marked writable can be encoded, and numbers only
    within their catalog range: the controller may restart on values it
    rejects (orca-energy-ha #20).
    """
    key = definition.key
    if not definition.writable:
        raise OrcaValueError(f"{key} is not writable")
    if definition.tag_name(slot) is None:
        raise OrcaValueError(f"{key} does not exist in slot {slot}")
    if definition.kind is Kind.BOOL:
        if not isinstance(value, bool):
            raise OrcaValueError(f"{key} needs a boolean, got {value!r}")
        return int(value)
    if definition.kind is Kind.ENUM:
        for raw, option in definition.options_for(slot).items():
            if option == value:
                return raw
        raise OrcaValueError(f"{key} has no option {value!r}")
    return _encode_number(definition, value)


def _encode_number(definition: TagDef, value: Value) -> int:
    key = definition.key
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise OrcaValueError(f"{key} needs a number, got {value!r}")
    if not math.isfinite(value):
        raise OrcaValueError(f"{key} needs a finite number, got {value!r}")
    if definition.minimum is None or definition.maximum is None:
        raise OrcaValueError(f"{key} has no known range; refusing to write")
    if not definition.minimum <= value <= definition.maximum:
        raise OrcaValueError(
            f"{key} must be between {definition.minimum} and"
            f" {definition.maximum}, got {value}"
        )
    raw = round(value * definition.scale)
    if not math.isclose(raw, value * definition.scale, abs_tol=1e-6):
        raise OrcaValueError(
            f"{key} accepts steps of {1 / definition.scale}, got {value}"
        )
    return raw


def decode_timers(records: Mapping[str, Record]) -> dict[int, TimerProgramme]:
    """Decode the weekly timer programmes.

    A programme with a missing or odd record is left out rather than shown
    wrong; ranges without a day are unused and dropped.
    """
    programmes: dict[int, TimerProgramme] = {}
    for programme in TIMER_PROGRAMMES:
        ranges: list[TimerRange] = []
        for time_range in TIMER_RANGES:
            values = [
                _timer_value(records.get(tag))
                for tag in timer_tags(programme, time_range)
            ]
            if None in values:
                break
            start_h, start_m, end_h, end_m, *flags = (
                v for v in values if v is not None
            )
            if not (_valid_time(start_h, start_m) and _valid_time(end_h, end_m)):
                break
            if any(flag not in (0, 1) for flag in flags):
                break
            if days := tuple(
                day for day, flag in zip(DAYS, flags, strict=True) if flag
            ):
                ranges.append(
                    TimerRange(
                        f"{start_h:02}:{start_m:02}", f"{end_h:02}:{end_m:02}", days
                    )
                )
        else:
            programmes[programme] = tuple(ranges)
    return programmes


def _timer_value(record: Record | None) -> int | None:
    if record is None or record.status != STATUS_OK:
        return None
    try:
        return int((record.value or "").strip())
    except ValueError:
        return None


def _valid_time(hour: int, minute: int) -> bool:
    # 24:00 ends a range at midnight.
    return 0 <= minute < 60 and (0 <= hour < 24 or (hour == 24 and minute == 0))
