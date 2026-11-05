"""The example dashboards are current and use entities every setup has."""

from collections.abc import Iterator
from typing import Any

import pytest
from pytest_homeassistant.common import MockConfigEntry
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.build_dashboard import DIRECTORY, FILES, build


def entity_ids(node: Any) -> Iterator[str]:
    """Yield every entity ID a dashboard refers to."""
    if isinstance(node, list):
        for item in node:
            yield from entity_ids(item)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in ("entity", "entities", "entity_id"):
                yield from [value] if isinstance(value, str) else value
            else:
                yield from entity_ids(value)


@pytest.mark.parametrize("language", FILES)
def test_files_are_current(language: str) -> None:
    """The committed files are what the generator makes."""
    assert (DIRECTORY / FILES[language]).read_text("utf-8") == build(language)


@pytest.mark.parametrize("language", FILES)
def test_only_built_in_cards(language: str) -> None:
    """Nobody has to install anything for the dashboard."""
    assert "custom:" not in build(language)


@pytest.mark.parametrize("language", FILES)
async def test_entities_exist_and_are_enabled(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    language: str,
) -> None:
    """Every entity is there and enabled by default, without further setup."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    enabled = {
        entry.entity_id
        for entry in er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
        if not entry.disabled
    }
    used = set(entity_ids(yaml.safe_load(build(language))))
    assert used
    assert used - enabled == set()
