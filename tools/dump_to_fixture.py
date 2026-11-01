"""Turn a diagnostics download into a test fixture for tests/fixtures/dumps/.

Diagnostics hold the raw value and the reason of every tag the integration
reads, which is enough to give the emulator the records the display sent.

Usage (from the repository root):
  python -m tools.dump_to_fixture DIAGNOSTICS.json OUTPUT.json
      --description "Orca Mono, schema 7, room sensors on both circuits"
      [--captured 2026-11-01T10:00]
"""

import argparse
import json
from pathlib import Path
from typing import Any

NOTE = (
    "Made from a diagnostics download with tools/dump_to_fixture.py. It holds"
    " only the tags the integration reads; timer programmes are not included."
)


def to_record(reading: dict[str, Any]) -> dict[str, str] | None:
    """Return the record the display sent for a reading, or None if none came."""
    reason, raw = reading["reason"], reading["raw"]
    if reason in ("no_response", "not_in_slot"):
        return None
    if reason == "unknown_tag":
        return {"status": "E_UNKNOWNTAG"}
    if reason == "tag_error":
        return {"status": raw}
    return {"status": "S_OK", "value": "" if raw is None else raw}


def convert(
    diagnostics: dict[str, Any], description: str, captured: str | None
) -> dict[str, Any]:
    """Return the fixture for a diagnostics download (or its ``data`` part)."""
    data = diagnostics.get("data", diagnostics)
    return {
        "description": description,
        "schema": data["topology"]["schema"],
        "captured": captured,
        "note": NOTE,
        "redacted": [],
        "tags": {
            tag: record
            for tag, reading in sorted(data["tags"].items())
            if (record := to_record(reading)) is not None
        },
    }


def main() -> None:
    """Convert the file given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("diagnostics", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--description", required=True)
    parser.add_argument("--captured", help="when the data was read, ISO 8601")
    args = parser.parse_args()
    diagnostics = json.loads(args.diagnostics.read_text(encoding="utf-8"))
    fixture = convert(diagnostics, args.description, args.captured)
    args.output.write_text(
        json.dumps(fixture, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{args.output}: schema {fixture['schema']}, {len(fixture['tags'])} tags")


if __name__ == "__main__":
    main()
