"""Print the Home Assistant version a CI channel tests against.

Usage: ci_ha_version.py minimum|stable|beta|dev

Prints ``version=<version>`` for ``$GITHUB_OUTPUT``. Home Assistant core tags
every release with its exact version, and ``dev`` is its development branch,
so the value is also the git ref to take pytest-home-assistant from.
"""

import json
from pathlib import Path
import re
import sys
import urllib.request

PYPI_URL = "https://pypi.org/pypi/homeassistant/json"
HACS_JSON = Path(__file__).parents[1] / "hacs.json"
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:b(\d+))?")


def sort_key(version: str) -> tuple[int, int, int, int, int]:
    """Order release versions, with a final release after all its betas."""
    if (match := VERSION_RE.fullmatch(version)) is None:
        raise ValueError(f"not a Home Assistant release version: {version}")
    year, month, patch, beta = match.groups()
    if beta is None:
        return (int(year), int(month), int(patch), 1, 0)
    return (int(year), int(month), int(patch), 0, int(beta))


def pypi_versions() -> list[str]:
    """Return the released, not yanked Home Assistant versions on PyPI."""
    with urllib.request.urlopen(PYPI_URL, timeout=30) as response:
        releases: dict[str, list[dict[str, object]]] = json.load(response)["releases"]
    return [
        version
        for version, files in releases.items()
        if VERSION_RE.fullmatch(version) and any(not file["yanked"] for file in files)
    ]


def resolve(channel: str) -> str:
    """Return the Home Assistant version for a CI channel."""
    match channel:
        case "minimum":
            minimum: str = json.loads(HACS_JSON.read_text(encoding="utf-8"))[
                "homeassistant"
            ]
            return minimum
        case "dev":
            return "dev"
        case "stable":
            return max(
                (version for version in pypi_versions() if "b" not in version),
                key=sort_key,
            )
        case "beta":
            return max(pypi_versions(), key=sort_key)
    raise ValueError(f"unknown channel: {channel}")


if __name__ == "__main__":
    print(f"version={resolve(sys.argv[1])}")
