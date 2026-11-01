"""Tests for decoding and encoding tag values."""

from hypothesis import given, strategies as st
import pytest

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.codec import (
    DAYS,
    decode,
    decode_timers,
    encode,
)
from custom_components.orca_heatpump.client.errors import OrcaValueError
from custom_components.orca_heatpump.client.models import (
    Element,
    Kind,
    Reading,
    Reason,
    TagDef,
    TimerProgramme,
    TimerRange,
    Value,
)
from custom_components.orca_heatpump.client.protocol import Record

from .helpers import OURS_HEATING, dump_record, load_dump

UNRANGED = TagDef(
    key="unranged", element=Element.SYSTEM, kind=Kind.NUMBER, tag="x", writable=True
)


def ok(value: str) -> Record:
    """Return a successful record with a raw value."""
    return Record("tag", "S_OK", 192, value)


@pytest.mark.parametrize(
    ("definition", "slot", "record", "expected"),
    [
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            None,
            Reading(None, reason=Reason.NO_RESPONSE),
            id="no_response",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            Record("t", "E_UNKNOWNTAG"),
            Reading(None, reason=Reason.UNKNOWN_TAG),
            id="unknown_tag",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            Record("t", "E_READFORBIDDEN"),
            Reading(None, raw="E_READFORBIDDEN", reason=Reason.TAG_ERROR),
            id="tag_error",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            ok(""),
            Reading(None, raw="", reason=Reason.EMPTY),
            id="empty",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            ok("-9999"),
            Reading(None, raw="-9999", reason=Reason.NOT_CONNECTED),
            id="not_connected",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            ok("4.2"),
            Reading(None, raw="4.2", reason=Reason.CONVERSION_FAILED),
            id="not_an_integer",
        ),
        pytest.param(
            catalog.HP_TEMPERATURE,
            None,
            ok("415"),
            Reading(41.5, raw="415"),
            id="scaled",
        ),
        pytest.param(
            catalog.OUTDOOR_TEMPERATURE,
            None,
            ok("-35"),
            Reading(-3.5, raw="-35"),
            id="negative",
        ),
        pytest.param(
            catalog.FIRMWARE_BUILD,
            None,
            ok(" 61 "),
            Reading(61, raw="61"),
            id="integer",
        ),
        pytest.param(
            catalog.PUMP_P0, None, ok("1"), Reading(True, raw="1"), id="bool_true"
        ),
        pytest.param(
            catalog.PUMP_P0, None, ok("0"), Reading(False, raw="0"), id="bool_false"
        ),
        pytest.param(
            catalog.PUMP_P0,
            None,
            ok("2"),
            Reading(None, raw="2", reason=Reason.CONVERSION_FAILED),
            id="bool_out_of_range",
        ),
        pytest.param(
            catalog.CIRCUIT_MODE, 1, ok("5"), Reading("manual", raw="5"), id="enum"
        ),
        pytest.param(
            catalog.CIRCUIT_MODE,
            3,
            ok("5"),
            Reading(None, raw="5", reason=Reason.UNKNOWN_OPTION),
            id="enum_slot_options",
        ),
        pytest.param(
            catalog.CIRCUIT_NAME,
            2,
            ok("42"),
            Reading(None, raw="42", reason=Reason.UNKNOWN_OPTION),
            id="enum_unknown",
        ),
    ],
)
def test_decode(
    definition: TagDef, slot: int | None, record: Record | None, expected: Reading
) -> None:
    """Every raw value decodes to a value or to a reason, never an exception."""
    assert decode(definition, slot, record) == expected


@pytest.mark.parametrize(
    ("definition", "slot", "value", "raw"),
    [
        pytest.param(catalog.SYSTEM_ENABLE, None, True, 1, id="bool"),
        pytest.param(catalog.CIRCUIT_MODE, 1, "cooling", 2, id="enum"),
        pytest.param(catalog.MAX_FLOW_HEATING, 1, 28.0, 280, id="scaled"),
        pytest.param(catalog.MAX_FLOW_HEATING, 3, 60, 600, id="maximum_int"),
        pytest.param(catalog.CURVE_SLOPE, 2, -15.0, -150, id="negative_minimum"),
        pytest.param(catalog.LEGIONELLA_HOUR, None, 23, 23, id="unscaled"),
        pytest.param(
            catalog.HP_POWER_LIMIT_COOLING, None, 16.0, 160, id="power_limit_minimum"
        ),
    ],
)
def test_encode(definition: TagDef, slot: int | None, value: Value, raw: int) -> None:
    """Valid values encode to the raw integer the display stores."""
    assert encode(definition, slot, value) == raw


@pytest.mark.parametrize(
    ("definition", "slot", "value", "match"),
    [
        pytest.param(
            catalog.HP_TEMPERATURE, None, 40.0, "not writable", id="read_only"
        ),
        pytest.param(catalog.HP_BOOST_FOR_CIRCUIT, 3, 5.0, "slot 3", id="missing_slot"),
        pytest.param(catalog.SYSTEM_ENABLE, None, 1, "boolean", id="bool_type"),
        pytest.param(
            catalog.CIRCUIT_MODE, 3, "manual", "no option", id="enum_slot_option"
        ),
        pytest.param(
            catalog.MAX_FLOW_HEATING, 1, True, "needs a number", id="bool_as_number"
        ),
        pytest.param(
            catalog.MAX_FLOW_HEATING, 1, "28", "needs a number", id="string_as_number"
        ),
        pytest.param(catalog.MAX_FLOW_HEATING, 1, float("nan"), "finite", id="nan"),
        pytest.param(catalog.MAX_FLOW_HEATING, 1, 60.1, "between", id="above_range"),
        pytest.param(
            catalog.HP_POWER_LIMIT_HEATING,
            None,
            10.0,
            "between",
            id="power_limit_below",
        ),
        pytest.param(catalog.MAX_FLOW_HEATING, 1, 28.05, "steps", id="resolution"),
        pytest.param(UNRANGED, None, 1, "no known range", id="no_range"),
    ],
)
def test_encode_rejects(
    definition: TagDef, slot: int | None, value: Value, match: str
) -> None:
    """Invalid writes are refused before anything reaches the pump."""
    with pytest.raises(OrcaValueError, match=match):
        encode(definition, slot, value)


@given(st.integers(min_value=80, max_value=600))
def test_number_roundtrip(raw: int) -> None:
    """Every raw value in range decodes and encodes back to itself."""
    reading = decode(catalog.MAX_FLOW_HEATING, 1, Record("t", "S_OK", 192, str(raw)))

    assert reading.value is not None
    assert encode(catalog.MAX_FLOW_HEATING, 1, reading.value) == raw


def timer_records(**changes: str | None) -> dict[str, Record]:
    """Return our pump's timer records, with values changed or removed."""
    tags = load_dump(OURS_HEATING)
    records = {
        tag: dump_record(tags, tag)
        for programme in catalog.TIMER_PROGRAMMES
        for time_range in catalog.TIMER_RANGES
        for tag in catalog.timer_tags(programme, time_range)
    }
    for tag, value in changes.items():
        if value is None:
            del records[tag]
        else:
            records[tag] = ok(value)
    return records


def test_decode_timers() -> None:
    """Every programme of our pump decodes; ranges without a day are dropped."""
    programmes = decode_timers(timer_records())

    assert set(programmes) == set(catalog.TIMER_PROGRAMMES)
    assert programmes[2] == (TimerRange("08:00", "18:00", DAYS),)


@pytest.mark.parametrize(
    ("changes", "programme_2"),
    [
        pytest.param(
            {"2_TIMER_2_Ura_OFF_2": "24", "2_TIMER_2_Sobota_2": "0"},
            (TimerRange("08:00", "24:00", DAYS[:5] + DAYS[6:]),),
            id="ends_at_midnight",
        ),
        pytest.param(
            {"2_TIMER_2_Ponedeljek_1": "1"},
            (
                TimerRange("23:00", "06:00", ("monday",)),
                TimerRange("08:00", "18:00", DAYS),
            ),
            id="crosses_midnight",
        ),
        pytest.param({"2_TIMER_2_Ura_ON_3": None}, None, id="missing"),
        pytest.param({"2_TIMER_2_Ura_ON_1": "25"}, None, id="bad_hour"),
        pytest.param({"2_TIMER_2_Minute_OFF_2": "60"}, None, id="bad_minute"),
        pytest.param(
            {"2_TIMER_2_Ura_OFF_2": "24", "2_TIMER_2_Minute_OFF_2": "30"},
            None,
            id="after_midnight",
        ),
        pytest.param({"2_TIMER_2_Petek_3": "2"}, None, id="bad_flag"),
        pytest.param({"2_TIMER_2_Petek_3": "x"}, None, id="not_a_number"),
    ],
)
def test_decode_timers_odd(
    changes: dict[str, str | None], programme_2: TimerProgramme | None
) -> None:
    """A programme with a missing or odd record is left out, the others stay."""
    programmes = decode_timers(timer_records(**changes))

    assert programmes.get(2) == programme_2
    assert set(programmes) - {2} == {1, 3, 4, 5}
