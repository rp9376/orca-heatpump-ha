"""Tests for the alarm event entity."""

import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.const import STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant, State
from tools.emulator import Emulator

EVENT = "event.heat_pump_alarm"


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up only the event entity."""
    return [Platform.EVENT]


def event(hass: HomeAssistant) -> State:
    """Return the alarm event entity's state."""
    state = hass.states.get(EVENT)
    assert state is not None
    return state


async def set_alarm(
    hass: HomeAssistant, entry: MockConfigEntry, emulator: Emulator, code: str
) -> None:
    """Change the pump's alarm code and poll."""
    emulator.values["2_Vrsta_alarma"] = code
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


async def test_alarm_sequence(
    hass: HomeAssistant, init_integration: MockConfigEntry, emulator: Emulator
) -> None:
    """Raising, switching and clearing alarms fire one event each."""
    assert event(hass).state == STATE_UNKNOWN

    seen = []
    for code in ("4", "4", "5", "0", "42"):
        await set_alarm(hass, init_integration, emulator, code)
        state = event(hass)
        seen.append(
            (
                state.attributes.get("event_type"),
                state.attributes.get("alarm"),
                state.attributes.get("code"),
            )
        )

    assert seen == [
        ("alarm_raised", "no_flow", 4),
        ("alarm_raised", "no_flow", 4),
        ("alarm_raised", "flow_switch", 5),
        ("alarm_cleared", "flow_switch", 5),
        ("alarm_raised", "unknown_code", 42),
    ]


async def test_unreadable_alarm(
    hass: HomeAssistant, init_integration: MockConfigEntry, emulator: Emulator
) -> None:
    """An unreadable alarm code makes the entity unavailable, firing nothing."""
    await set_alarm(hass, init_integration, emulator, "")

    assert event(hass).state == "unavailable"

    await set_alarm(hass, init_integration, emulator, "0")
    assert event(hass).state == STATE_UNKNOWN
