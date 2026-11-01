"""Tests for the sensors."""

import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from custom_components.orca_heatpump.const import CONF_ALLOW_POWER_LIMITS
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools.emulator import Emulator

ALARM = "sensor.heat_pump_active_alarm"


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the sensors."""
    return [Platform.SENSOR]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Each real pump gets the sensors of its own elements."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.parametrize(
    ("raw", "state", "code"),
    [
        pytest.param("4", "no_flow", 4, id="known"),
        pytest.param("42", "unknown_code", 42, id="unknown"),
        pytest.param("", STATE_UNAVAILABLE, None, id="empty"),
    ],
)
async def test_active_alarm(
    hass: HomeAssistant,
    emulator: Emulator,
    mock_config_entry: MockConfigEntry,
    raw: str,
    state: str,
    code: int | None,
) -> None:
    """Alarm codes show their text; unknown codes still show, never crash."""
    emulator.values["2_Vrsta_alarma"] = raw
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    alarm = hass.states.get(ALARM)
    assert alarm is not None
    assert alarm.state == state
    assert alarm.attributes.get("code") == code


async def test_power_limits_hidden_when_writable(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """With power limits writable, the number platform owns them."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_ALLOW_POWER_LIMITS: True}
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert hass.states.get("sensor.heat_pump_power_limit_heating") is None
