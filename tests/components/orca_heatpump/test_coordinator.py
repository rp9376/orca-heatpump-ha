"""Tests for polling the heat pump."""

from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from tools.emulator import Emulator, Faults


async def poll(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Poll once, as the coordinator does on its interval."""
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


async def test_failure_and_recovery(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
) -> None:
    """A failed poll makes the data unavailable until the next good one."""
    coordinator = init_integration.runtime_data.coordinator
    emulator.faults = Faults(http_status=503)
    await poll(hass, init_integration)
    assert not coordinator.last_update_success

    emulator.faults = Faults()
    await poll(hass, init_integration)
    assert coordinator.last_update_success


async def test_sessions_exhausted_issue(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Three refused polls raise an issue; the next good poll clears it."""
    issue_id = f"sessions_exhausted_{init_integration.entry_id}"
    emulator.expire_sessions()
    emulator.max_sessions = 0
    for _ in range(2):
        await poll(hass, init_integration)
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None

    await poll(hass, init_integration)
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is not None

    emulator.max_sessions = 2
    await poll(hass, init_integration)
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None


async def test_auth_failure_starts_reauth(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
) -> None:
    """A login refused while polling starts reauthentication."""
    emulator.expire_sessions()
    emulator.password = "other"

    await poll(hass, init_integration)

    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == ["reauth"]


async def test_timers_keep_last_good(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    emulator: Emulator,
) -> None:
    """A failed or incomplete timer read keeps the programmes read before."""
    timers = init_integration.runtime_data.timers
    before = timers.data
    assert set(before) == {1, 2, 3, 4, 5}

    emulator.faults = Faults(http_status=503)
    await timers.async_refresh()
    assert not timers.last_update_success
    assert timers.data == before

    emulator.faults = Faults()
    emulator.values["2_TIMER_2_Ura_ON_1"] = "x"
    for time_range in (1, 2, 3):
        emulator.values[f"2_TIMER_3_Ura_ON_{time_range}"] = "19"
    await timers.async_refresh()

    assert timers.last_update_success
    assert timers.data[2] == before[2]
    assert timers.data[3] != before[3]
