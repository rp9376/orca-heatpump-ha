"""Tests for the client's data model."""

from datetime import date

import pytest

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.models import (
    NO_RESPONSE,
    NOT_IN_SLOT,
    CircuitKind,
    CircuitTopology,
    DeviceIdentity,
    PumpTopology,
    Reading,
    Snapshot,
)


def test_tag_names() -> None:
    """Entries name their tags per slot or once."""
    assert catalog.HP_BOOST_FOR_CIRCUIT.tag_name(1) == "2_Povec_temp_TC_pri_MK1"
    assert catalog.HP_BOOST_FOR_CIRCUIT.tag_name(3) is None
    assert catalog.HP_BOOST_FOR_CIRCUIT.tag_names() == (
        "2_Povec_temp_TC_pri_MK1",
        "2_Povec_temp_TC_pri_MK2",
    )
    assert catalog.HP_TEMPERATURE.tag_name() == "2_Poti1"
    assert catalog.HP_TEMPERATURE.tag_names() == ("2_Poti1",)


@pytest.mark.parametrize("slot", [None, 0, 4])
def test_tag_name_needs_slot(slot: int | None) -> None:
    """A circuit entry without a valid slot is a programming error."""
    with pytest.raises(ValueError, match="slot 1-3"):
        catalog.CIRCUIT_MODE.tag_name(slot)


def test_options_per_slot() -> None:
    """Slot 3 has no manual mode."""
    assert "manual" in catalog.CIRCUIT_MODE.options_for(1).values()
    assert "manual" not in catalog.CIRCUIT_MODE.options_for(3).values()
    assert catalog.CIRCUIT_MODE.options_for() == catalog.CIRCUIT_MODE.options_for(1)


def test_snapshot_never_fails() -> None:
    """Lookups of unread tags and empty slots return readings without values."""
    snapshot = Snapshot({"2_Poti1": Reading(41.5, raw="415")})

    assert snapshot.value(catalog.HP_TEMPERATURE) == 41.5
    assert snapshot.reading(catalog.OUTDOOR_TEMPERATURE) is NO_RESPONSE
    assert snapshot.reading(catalog.HP_BOOST_FOR_CIRCUIT, 3) is NOT_IN_SLOT
    assert snapshot.get("anything") is NO_RESPONSE


def test_topology_circuit() -> None:
    """Circuits are looked up by slot."""
    circuit = CircuitTopology(1, CircuitKind.DIRECT, room_sensor=False)
    topology = PumpTopology(23, (circuit,), dhw=True, solar=True, buffer=False)

    assert topology.circuit(1) is circuit
    assert topology.circuit(2) is None


@pytest.mark.parametrize(
    ("identity", "firmware"),
    [
        pytest.param(
            DeviceIdentity(61, date(2016, 12, 12), "mitsubishi"),
            "61 (2016-12-12)",
            id="full",
        ),
        pytest.param(DeviceIdentity(61, None, None), "61", id="no_date"),
        pytest.param(DeviceIdentity(None, None, None), None, id="unknown"),
    ],
)
def test_firmware(identity: DeviceIdentity, firmware: str | None) -> None:
    """The firmware string shows the build and, when known, its date."""
    assert identity.firmware == firmware
