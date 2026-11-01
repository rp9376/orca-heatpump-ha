"""Helpers shared by the client tests."""

import json
from pathlib import Path
from typing import Any

from custom_components.orca_heatpump.client.catalog import CATALOG
from custom_components.orca_heatpump.client.codec import decode
from custom_components.orca_heatpump.client.models import SLOTS, Reading, Snapshot
from custom_components.orca_heatpump.client.protocol import Record

ROOT = Path(__file__).parents[2]
DUMPS = ROOT / "tests" / "fixtures" / "dumps"
OURS = "schema23_duo300solar_2026-10-31.json"
OURS_HEATING = "schema23_duo300solar_2026-11-01_heating.json"
DUO = "schema3_duo_2025-12-08.json"
MONO = "schema7_mono_2025-12-10.json"


def load_json(path: Path) -> Any:
    """Load a JSON file of the repository."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_dump(name: str) -> dict[str, dict[str, str]]:
    """Return the tag records of a dump fixture."""
    tags: dict[str, dict[str, str]] = load_json(DUMPS / name)["tags"]
    return tags


def dump_record(tags: dict[str, dict[str, str]], tag: str) -> Record:
    """Return a dump's record of a tag; tags a dump lacks are unknown there."""
    entry = tags.get(tag, {"status": "E_UNKNOWNTAG"})
    if entry["status"] != "S_OK":
        return Record(tag, entry["status"])
    return Record(tag, "S_OK", 192, entry["value"])


def snapshot_from_dump(name: str) -> Snapshot:
    """Decode every catalog tag of a dump fixture."""
    tags = load_dump(name)
    readings: dict[str, Reading] = {}
    for definition in CATALOG:
        for slot in SLOTS if definition.slot_tags else (None,):
            if (tag := definition.tag_name(slot)) is not None:
                readings[tag] = decode(definition, slot, dump_record(tags, tag))
    return Snapshot(readings)
