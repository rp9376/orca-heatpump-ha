"""The example dashboards are current and use entities every setup has."""

from collections.abc import Iterator
from typing import Any

import pytest
from pytest_homeassistant.common import MockConfigEntry
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tools import build_dashboard
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


IDLE = {
    build_dashboard.PUMP: "off",
    build_dashboard.VALVE: "hot_water",
    build_dashboard.OUTDOOR_STATE: "off",
    build_dashboard.OUTDOOR_POWER: "0.0",
    build_dashboard.FLOOR_PUMP: "off",
    build_dashboard.RADIATOR_PUMP: "off",
    build_dashboard.SOLAR_PUMP: "off",
}
RUNNING = {build_dashboard.PUMP: "on", build_dashboard.OUTDOOR_POWER: "50.0"}
HOT, COLD, SOLAR = build_dashboard.HOT, build_dashboard.COLD, build_dashboard.SOLAR
SUPPLY, MAIN = build_dashboard.SUPPLY, build_dashboard.HEATING_MAIN
FLOOR, TANK = build_dashboard.FLOOR, build_dashboard.TANK


def _holds(condition: dict[str, Any], states: dict[str, str]) -> bool:
    value = states[condition["entity"]]
    if condition.get("condition") == "numeric_state":
        return bool(float(value) > condition["above"])
    if "state_not" in condition:
        return bool(value != condition["state_not"])
    return bool(value == condition["state"])


@pytest.mark.parametrize(
    ("changes", "flows"),
    [
        pytest.param({}, set(), id="idle"),
        pytest.param(
            {build_dashboard.PUMP: "on", build_dashboard.FLOOR_PUMP: "on"},
            set(),
            id="valve_resting_on_hot_water_at_0_percent",
        ),
        pytest.param(
            {
                build_dashboard.PUMP: "on",
                build_dashboard.FLOOR_PUMP: "on",
                build_dashboard.VALVE: "space_heating",
            },
            set(),
            id="pause_between_compressor_runs",
        ),
        pytest.param(
            {**RUNNING, build_dashboard.VALVE: "space_heating"},
            set(),
            id="starting_power_set_but_unit_not_heating",
        ),
        pytest.param(
            {
                **RUNNING,
                build_dashboard.OUTDOOR_STATE: "heating",
                build_dashboard.OUTDOOR_POWER: "0.0",
            },
            set(),
            id="unit_heating_at_0_percent",
        ),
        pytest.param(
            {
                **RUNNING,
                build_dashboard.OUTDOOR_STATE: "heating",
                build_dashboard.VALVE: "space_heating",
                build_dashboard.FLOOR_PUMP: "on",
            },
            {(SUPPLY, HOT), (MAIN, HOT), (FLOOR, HOT)},
            id="heating_the_floor",
        ),
        pytest.param(
            {
                **RUNNING,
                build_dashboard.OUTDOOR_STATE: "heating",
                build_dashboard.FLOOR_PUMP: "on",
            },
            {(SUPPLY, HOT), (TANK, HOT)},
            id="heating_hot_water_with_the_floor_pump_on",
        ),
        pytest.param(
            {
                **RUNNING,
                build_dashboard.OUTDOOR_STATE: "cooling",
                build_dashboard.VALVE: "space_heating",
                build_dashboard.FLOOR_PUMP: "on",
            },
            {(SUPPLY, COLD), (MAIN, COLD), (FLOOR, COLD)},
            id="cooling_the_floor",
        ),
        pytest.param(
            {build_dashboard.SOLAR_PUMP: "on"},
            {(build_dashboard.SOLAR_PIPE, SOLAR)},
            id="solar_runs_by_itself",
        ),
    ],
)
def test_pipes_flow_only_while_heat_is_produced(
    changes: dict[str, str], flows: set[tuple[str, str]]
) -> None:
    """The diagram animates a pipe only when heat or cold really moves through it."""
    states = IDLE | changes
    every_flow = {
        build_dashboard._flow(path, color): (path, color)
        for path in (
            SUPPLY,
            MAIN,
            FLOOR,
            TANK,
            build_dashboard.RADIATORS,
            build_dashboard.SOLAR_PIPE,
        )
        for color in (HOT, COLD, SOLAR)
    }
    shown = {
        every_flow[element["elements"][0]["image"]]
        for element in build_dashboard._diagram()["elements"]
        if element.get("type") == "conditional"
        and element["elements"][0].get("image") in every_flow
        and all(_holds(c, states) for c in element["conditions"])
    }

    assert shown == flows


@pytest.mark.parametrize(
    ("flow", "shown"),
    [("35.0", True), ("unavailable", False), ("unknown", False)],
)
def test_radiator_flow_is_empty_without_a_value(flow: str, *, shown: bool) -> None:
    """The radiators' flow line stays empty on a circuit without a flow sensor."""
    states = {build_dashboard.RADIATOR_FLOW: flow}
    group = next(
        element
        for element in build_dashboard._diagram()["elements"]
        if element.get("type") == "conditional"
        and element["elements"][0].get("entity") == build_dashboard.RADIATOR_FLOW
    )
    assert all(_holds(c, states) for c in group["conditions"]) is shown
