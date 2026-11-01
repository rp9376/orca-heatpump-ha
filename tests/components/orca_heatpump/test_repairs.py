"""Tests for the repair flows."""

import pytest
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.repairs import (
    process_repair_fix_flow,
    start_repair_fix_flow,
)
from pytest_homeassistant.typing import ClientSessionGenerator

from custom_components.orca_heatpump.const import CONF_TOPOLOGY, DOMAIN
from custom_components.orca_heatpump.helpers import topology_to_data
from custom_components.orca_heatpump.repairs import async_create_fix_flow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from .conftest import OUR_TOPOLOGY


async def test_accept_topology_change(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Confirming the issue stores the detected topology and reloads."""
    assert await async_setup_component(hass, "repairs", {})
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={
            **mock_config_entry.data,
            CONF_TOPOLOGY: topology_to_data(OUR_TOPOLOGY) | {"buffer": True},
        },
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    issue_id = f"topology_changed_{mock_config_entry.entry_id}"
    client = await hass_client()

    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["step_id"] == "confirm"
    result = await process_repair_fix_flow(client, result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert mock_config_entry.data[CONF_TOPOLOGY] == topology_to_data(OUR_TOPOLOGY)
    assert mock_config_entry.runtime_data.topology.buffer is False
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None


async def test_fix_after_entry_removed(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """Confirming an issue whose entry is gone just closes the flow."""
    assert await async_setup_component(hass, "repairs", {})
    issue_id = f"topology_changed_{init_integration.entry_id}"
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="topology_changed",
        data={"entry_id": "gone", "topology": "{}"},
    )
    client = await hass_client()

    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["step_id"] == "confirm"
    result = await process_repair_fix_flow(client, result["flow_id"])

    assert result["type"] == "create_entry"
    assert init_integration.data[CONF_TOPOLOGY] == topology_to_data(OUR_TOPOLOGY)


async def test_fix_flow_needs_data(hass: HomeAssistant) -> None:
    """Only issues with data have a fix flow."""
    with pytest.raises(ValueError, match="has no data"):
        await async_create_fix_flow(hass, "old_integration_x", None)
