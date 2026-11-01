"""Tests for the integration's helpers and translations."""

import json
from pathlib import Path

import pytest

from custom_components.orca_heatpump.client.catalog import CATALOG
from custom_components.orca_heatpump.helpers import (
    refs_for,
    split_host,
    topology_from_data,
    topology_to_data,
)

from .conftest import OUR_TOPOLOGY

INTEGRATION = Path(__file__).parents[3] / "custom_components" / "orca_heatpump"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("192.168.1.5", ("192.168.1.5", 80), id="ip"),
        pytest.param(" orca.local ", ("orca.local", 80), id="name"),
        pytest.param("127.0.0.1:8780", ("127.0.0.1", 8780), id="port"),
        pytest.param(
            "host.docker.internal:8780", ("host.docker.internal", 8780), id="name_port"
        ),
        pytest.param("fe80::1", ("fe80::1", 80), id="ipv6"),
    ],
)
def test_split_host(value: str, expected: tuple[str, int]) -> None:
    """A host may carry a port, for the emulator."""
    assert split_host(value) == expected


def test_topology_roundtrip() -> None:
    """Stored topologies come back unchanged."""
    assert topology_from_data(topology_to_data(OUR_TOPOLOGY)) == OUR_TOPOLOGY


def test_refs_follow_topology() -> None:
    """Only present elements and circuit slots are polled."""
    tags = {d.tag_name(slot) for d, slot in refs_for(OUR_TOPOLOGY)}

    assert "2_Max_VF_MK1" in tags
    assert "2_Max_VF_MK2" in tags
    assert "2_Max_VF_DK3" not in tags
    assert "2_Temp_Zalog" not in tags
    assert "2_Poti5" in tags
    assert len(tags) < sum(len(d.tag_names()) for d in CATALOG)


def test_translations_complete() -> None:
    """en.json equals strings.json, and sl.json has the same keys."""

    def keys(data: dict[str, object], prefix: str = "") -> set[str]:
        return {
            k
            for name, value in data.items()
            for k in (
                keys(value, f"{prefix}{name}.")
                if isinstance(value, dict)
                else {f"{prefix}{name}"}
            )
        }

    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (INTEGRATION / "translations/en.json").read_text(encoding="utf-8")
    )
    slovenian = json.loads(
        (INTEGRATION / "translations/sl.json").read_text(encoding="utf-8")
    )

    assert english == strings
    assert keys(slovenian) == keys(strings)
