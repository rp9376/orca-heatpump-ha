"""Tests for the Orca Heat Pump config flow."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_BUFFER,
    CONF_SOLAR,
    CONF_TOPOLOGY,
    DEFAULT_TITLE,
    DOMAIN,
    OLD_DOMAIN,
)
from custom_components.orca_heatpump.helpers import topology_to_data
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from tools.emulator import Emulator, Faults

from .conftest import OUR_TOPOLOGY, serve

pytestmark = pytest.mark.usefixtures("mock_setup_entry")

CLOSED = "127.0.0.1:1"


def login(host: str, password: str = "admin") -> dict[str, Any]:
    """Return connection form input."""
    return {CONF_HOST: host, CONF_USERNAME: "admin", CONF_PASSWORD: password}


@pytest.fixture
async def second_host(emulator: Emulator, host: str) -> AsyncIterator[str]:
    """Serve the same emulator on a second address."""
    del host
    runner, second = await serve(emulator)
    yield second
    await runner.cleanup()


async def test_user_flow(hass: HomeAssistant, host: str, emulator: Emulator) -> None:
    """The user flow creates an entry with the topology and logs out."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: True}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_TITLE
    assert result["data"] == login(host) | {
        CONF_TOPOLOGY: topology_to_data(OUR_TOPOLOGY)
    }
    assert result["options"] == {CONF_ALLOW_POWER_LIMITS: True}
    assert result["result"].unique_id == host
    assert emulator.sessions == {}


@pytest.mark.parametrize(
    ("broken", "error"),
    [
        pytest.param({"password": "other"}, "invalid_auth", id="invalid_auth"),
        pytest.param({"max_sessions": 0}, "too_many_users", id="too_many_users"),
        pytest.param(
            {"faults": Faults(malformed_body=True)}, "not_orca", id="not_orca"
        ),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    host: str,
    emulator: Emulator,
    broken: dict[str, Any],
    error: str,
) -> None:
    """Errors are shown and the user can try again."""
    working = {name: getattr(emulator, name) for name in broken}
    emulator.__dict__.update(broken)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["errors"] == {"base": error}

    emulator.__dict__.update(working)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_cannot_connect(hass: HomeAssistant, host: str) -> None:
    """An unreachable display is reported; a correct address then works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(CLOSED) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_unknown_error(hass: HomeAssistant, host: str) -> None:
    """Unexpected errors are logged and reported as unknown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with patch(
        "custom_components.orca_heatpump.config_flow.OrcaClient.async_detect_topology",
        side_effect=RuntimeError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
        )
    assert result["errors"] == {"base": "unknown"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_already_configured(
    hass: HomeAssistant, host: str, mock_config_entry: MockConfigEntry
) -> None:
    """The same display can't be added twice."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_old_integration_warning(hass: HomeAssistant, host: str) -> None:
    """With orca-energy-ha on the same pump, the flow warns first."""
    MockConfigEntry(
        domain=OLD_DOMAIN, unique_id="127.0.0.1", data={"hostname": "127.0.0.1"}
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "old_integration"
    assert result["description_placeholders"] == {"host": host}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reauth(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, emulator: Emulator
) -> None:
    """Reauthentication stores the new login."""
    mock_config_entry.add_to_hass(hass)
    emulator.password = "new"
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "old"}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == "new"


async def test_reconfigure(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, second_host: str
) -> None:
    """Reconfigure moves the entry to a new address and unique ID."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(CLOSED)
    )
    assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(second_host)
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == second_host
    assert mock_config_entry.unique_id == second_host


async def test_reconfigure_same_host(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, host: str
) -> None:
    """Reconfigure with the same address only updates the login."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host)
    )

    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.unique_id == host


async def test_reconfigure_to_other_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Reconfigure can't take another entry's address."""
    mock_config_entry.add_to_hass(hass)
    MockConfigEntry(domain=DOMAIN, unique_id="10.0.0.9").add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login("10.0.0.9")
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Options offer power limits and one override per present element."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    schema = result["data_schema"]
    assert schema is not None
    assert [str(key) for key in schema.schema] == [
        CONF_ALLOW_POWER_LIMITS,
        "room_sensor_1",
        "room_sensor_2",
        CONF_SOLAR,
        CONF_BUFFER,
    ]
    options = {
        CONF_ALLOW_POWER_LIMITS: True,
        "room_sensor_1": "present",
        "room_sensor_2": "auto",
        CONF_SOLAR: "absent",
        CONF_BUFFER: "auto",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], options
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == options
