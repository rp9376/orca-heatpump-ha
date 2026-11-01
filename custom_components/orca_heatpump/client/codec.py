"""Conversion between raw tag values and typed values."""

import math

from .errors import OrcaValueError
from .models import NO_RESPONSE, Kind, Reading, Reason, TagDef, Value
from .protocol import NOT_CONNECTED, STATUS_OK, STATUS_UNKNOWN_TAG, Record


def decode(definition: TagDef, slot: int | None, record: Record | None) -> Reading:
    """Decode a record; anything odd becomes a reading without a value."""
    if record is None:
        return NO_RESPONSE
    if record.status == STATUS_UNKNOWN_TAG:
        return Reading(None, reason=Reason.UNKNOWN_TAG)
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
