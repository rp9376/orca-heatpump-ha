"""Every entity of pumps built from schemas nobody recorded yet."""

import pytest
from pytest_homeassistant.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir

from .conftest import PUMPS


@pytest.mark.parametrize("pump", ["three_circuits", "heating_only"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    mock_config_entry: MockConfigEntry,
    pump: str,
    snapshot: SnapshotAssertion,
) -> None:
    """The pump is detected as built and gets the entities of its elements."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.runtime_data.topology == PUMPS[pump][1]
    assert not issue_registry.issues
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    lines = []
    for entry in sorted(entries, key=lambda e: e.entity_id):
        state = hass.states.get(entry.entity_id)
        lines.append(
            f"{entry.entity_id} | {entry.unique_id.split('_', 1)[1]}"
            f" | {'disabled' if entry.disabled else state.state if state else '-'}"
        )
    assert lines == snapshot
