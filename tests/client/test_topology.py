"""Tests for topology detection."""

import pytest

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.errors import OrcaProtocolError
from custom_components.orca_heatpump.client.models import (
    CircuitKind,
    CircuitTopology,
    PumpTopology,
    Reading,
    Reason,
    Snapshot,
)
from custom_components.orca_heatpump.client.topology import (
    SCHEMAS,
    TOPOLOGY_TAGS,
    detect_topology,
)

from .helpers import DUO, MONO, OURS, ROOT, load_json, snapshot_from_dump

M, D = CircuitKind.MIXING, CircuitKind.DIRECT
NOT_FOUND = Reading(None, reason=Reason.UNKNOWN_TAG)


def synthetic(schema: int, **overrides: Reading) -> Snapshot:
    """Return a topology snapshot: no buffer, no room sensors."""
    readings = dict.fromkeys(TOPOLOGY_TAGS, Reading(False, raw="0"))
    readings |= {
        "2_Shema": Reading(schema, raw=str(schema)),
        "2_Temp_Prostora": Reading(None, raw="-9999", reason=Reason.NOT_CONNECTED),
        "2_Temp_RF2": Reading(None, raw="-9999", reason=Reason.NOT_CONNECTED),
        "2_Temp_RF3": Reading(None, raw="-9999", reason=Reason.NOT_CONNECTED),
    }
    return Snapshot(readings | overrides)


def test_schema_table_matches_manufacturer() -> None:
    """SCHEMAS equals the manufacturer's 45 wiring diagram names."""
    names = load_json(ROOT / "research" / "moja_orca_catalog.json")["lists"][
        "wiring_diagrams"
    ]
    expected = {}
    for number, name in names.items():
        parts = {"SV" if p == "SAN.VODA" else p for p in name.upper().split("+")}
        expected[int(number)] = (
            tuple(
                M if f"MK{slot}" in parts else D if f"DK{slot}" in parts else None
                for slot in (1, 2, 3)
            ),
            "SV" in parts,
            "SOLAR" in parts,
        )

    assert {
        number: (schema.circuits, schema.dhw, schema.solar)
        for number, schema in SCHEMAS.items()
    } == expected


@pytest.mark.parametrize(
    ("dump", "expected"),
    [
        pytest.param(
            OURS,
            PumpTopology(
                23,
                (CircuitTopology(1, D, False), CircuitTopology(2, M, False)),
                dhw=True,
                solar=True,
                buffer=False,
            ),
            id="ours_23",
        ),
        pytest.param(
            DUO,
            PumpTopology(
                3, (CircuitTopology(1, D, True),), dhw=True, solar=False, buffer=False
            ),
            id="duo_3",
        ),
        pytest.param(
            MONO,
            PumpTopology(
                7,
                (CircuitTopology(1, D, True), CircuitTopology(2, D, True)),
                dhw=True,
                solar=False,
                buffer=True,
            ),
            id="mono_7",
        ),
    ],
)
def test_real_pumps(dump: str, expected: PumpTopology) -> None:
    """The three known pumps are detected as they are built."""
    assert detect_topology(snapshot_from_dump(dump)) == expected


@pytest.mark.parametrize("schema", sorted(SCHEMAS))
def test_every_schema(schema: int) -> None:
    """Every schema yields its circuits, hot water and solar."""
    topology = detect_topology(synthetic(schema))

    assert [(c.slot, c.kind) for c in topology.circuits] == [
        (slot, kind)
        for slot, kind in enumerate(SCHEMAS[schema].circuits, 1)
        if kind is not None
    ]
    assert (topology.dhw, topology.solar, topology.buffer) == (
        SCHEMAS[schema].dhw,
        SCHEMAS[schema].solar,
        False,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"2_Shema_ZALOG": NOT_FOUND}, id="buffer_flag_unknown"),
        pytest.param({"2_Shema_ZALOG": Reading(False, raw="0")}, id="buffer_flag_off"),
    ],
)
def test_no_buffer(overrides: dict[str, Reading]) -> None:
    """A buffer flag that is unknown or off means no buffer."""
    assert detect_topology(synthetic(23, **overrides)).buffer is False


@pytest.mark.parametrize(
    ("overrides", "room_sensor"),
    [
        pytest.param(
            {"2_PogojPGDT_Shema_in_tipalo_OK1": Reading(True, raw="1")},
            True,
            id="flag_on",
        ),
        pytest.param(
            {
                "2_PogojPGDT_Shema_in_tipalo_OK1": NOT_FOUND,
                "2_Temp_Prostora": Reading(21.5, raw="215"),
            },
            True,
            id="no_flag_sensor_reads",
        ),
        pytest.param(
            {"2_PogojPGDT_Shema_in_tipalo_OK1": NOT_FOUND},
            False,
            id="no_flag_no_sensor",
        ),
    ],
)
def test_room_sensor(overrides: dict[str, Reading], room_sensor: bool) -> None:
    """The flag decides; without it, a room temperature reading does."""
    topology = detect_topology(synthetic(23, **overrides))

    assert topology.circuits[0].room_sensor is room_sensor


@pytest.mark.parametrize(
    ("schema", "missing"),
    [
        pytest.param(23, "2_Shema", id="schema"),
        pytest.param(23, "2_Shema_ZALOG", id="buffer"),
        pytest.param(23, "2_PogojPGDT_Shema_in_tipalo_OK2", id="room_sensor_flag"),
    ],
)
def test_not_received(schema: int, missing: str) -> None:
    """A topology signal that was not received is an error, not 'absent'."""
    readings = dict(synthetic(schema).readings)
    del readings[missing]

    with pytest.raises(OrcaProtocolError, match="not received"):
        detect_topology(Snapshot(readings))


def test_room_temperature_not_received() -> None:
    """Without the flag, the fallback reading must have been received."""
    readings = dict(
        synthetic(23, **{"2_PogojPGDT_Shema_in_tipalo_OK1": NOT_FOUND}).readings
    )
    del readings["2_Temp_Prostora"]

    with pytest.raises(OrcaProtocolError, match="room_temperature"):
        detect_topology(Snapshot(readings))


@pytest.mark.parametrize(
    "reading",
    [
        pytest.param(Reading(0, raw="0"), id="zero"),
        pytest.param(Reading(46, raw="46"), id="too_high"),
        pytest.param(
            Reading(None, raw="-9999", reason=Reason.NOT_CONNECTED), id="no_value"
        ),
    ],
)
def test_unknown_schema(reading: Reading) -> None:
    """Schemas outside the manufacturer's list are refused."""
    with pytest.raises(OrcaProtocolError, match="unknown schema"):
        detect_topology(synthetic(23, **{"2_Shema": reading}))


def test_topology_tags() -> None:
    """Detection reads only a handful of tags."""
    assert catalog.SCHEMA.tag in TOPOLOGY_TAGS
    assert len(TOPOLOGY_TAGS) == 8
