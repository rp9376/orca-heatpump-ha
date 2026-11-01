"""Home Assistant finds the integration in this repository."""

import json
from pathlib import Path
from typing import Any

from custom_components.orca_heatpump.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

COMPONENT = Path(__file__).parents[3] / "custom_components" / DOMAIN


async def test_integration_is_discovered(hass: HomeAssistant) -> None:
    """The integration loads as a custom integration without requirements."""
    integration = await async_get_integration(hass, DOMAIN)

    assert not integration.is_built_in
    assert integration.manifest["codeowners"] == ["@rp9376"]
    # No runtime dependencies beyond Home Assistant (ADR 0005).
    assert integration.manifest["requirements"] == []


def _keys(tree: dict[str, Any], prefix: str = "") -> set[str]:
    return {
        key
        for name, value in tree.items()
        for key in (
            _keys(value, f"{prefix}{name}.")
            if isinstance(value, dict)
            else {f"{prefix}{name}"}
        )
    }


def test_translations_complete() -> None:
    """English matches strings.json; Slovenian translates every key."""
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations/en.json").read_text("utf-8"))
    slovenian = json.loads((COMPONENT / "translations/sl.json").read_text("utf-8"))

    assert english == strings
    assert _keys(slovenian) == _keys(english)
