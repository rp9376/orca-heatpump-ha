"""Tests for the Orca Heat Pump config flow."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_TOPOLOGY,
    DEFAULT_TITLE,
    DOMAIN,
    OLD_DOMAIN,
)
from custom_components.orca_heatpump.helpers import topology_to_data
from homeassistant.config_entries import SOURCE_USER, ConfigEntryDisabler
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
    assert result["result"].unique_id is None
    assert emulator.sessions == {}


@pytest.mark.parametrize(
    ("broken", "error"),
    [
        pytest.param({"password": "other"}, "invalid_auth", id="invalid_auth"),
        pytest.param({"username": "other"}, "invalid_auth", id="wrong_username"),
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
    """Reconfigure moves the entry to a new address."""
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
    assert mock_config_entry.data[CONF_HOST] == host


async def test_reconfigure_to_other_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Reconfigure can't take another entry's address."""
    mock_config_entry.add_to_hass(hass)
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "10.0.0.9"}).add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login("10.0.0.9")
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """The only option is the permission to change the power limits."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    schema = result["data_schema"]
    assert schema is not None
    assert [str(key) for key in schema.schema] == [CONF_ALLOW_POWER_LIMITS]
    options = {CONF_ALLOW_POWER_LIMITS: True}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], options
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == options


ERRORS = [
    pytest.param({"password": "other"}, "invalid_auth", id="invalid_auth"),
    pytest.param({"username": "other"}, "invalid_auth", id="wrong_username"),
    pytest.param({"max_sessions": 0}, "too_many_users", id="too_many_users"),
    pytest.param({"faults": Faults(malformed_body=True)}, "not_orca", id="not_orca"),
    pytest.param({"faults": Faults(disconnect=True)}, "cannot_connect", id="connect"),
]
UNEXPECTED = (
    "custom_components.orca_heatpump.config_flow.OrcaClient.async_detect_topology"
)


@pytest.mark.parametrize(("broken", "error"), ERRORS)
async def test_reauth_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    emulator: Emulator,
    broken: dict[str, Any],
    error: str,
) -> None:
    """Every error of the reauth flow is shown and a retry can succeed."""
    mock_config_entry.add_to_hass(hass)
    working = {name: getattr(emulator, name) for name in broken}
    emulator.__dict__.update(broken)
    result = await mock_config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}
    )
    assert result["errors"] == {"base": error}

    emulator.__dict__.update(working)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}
    )
    assert result["reason"] == "reauth_successful"


async def test_reauth_unknown_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """An unexpected error in the reauth flow is shown and a retry can succeed."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    with patch(UNEXPECTED, side_effect=RuntimeError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}
        )
    assert result["errors"] == {"base": "unknown"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}
    )
    assert result["reason"] == "reauth_successful"


@pytest.mark.parametrize(("broken", "error"), ERRORS)
async def test_reconfigure_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    emulator: Emulator,
    host: str,
    broken: dict[str, Any],
    error: str,
) -> None:
    """Every error of the reconfigure flow is shown and a retry can succeed."""
    mock_config_entry.add_to_hass(hass)
    working = {name: getattr(emulator, name) for name in broken}
    emulator.__dict__.update(broken)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host)
    )
    assert result["errors"] == {"base": error}

    emulator.__dict__.update(working)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host)
    )
    assert result["reason"] == "reconfigure_successful"


async def test_reconfigure_unknown_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, host: str
) -> None:
    """An unexpected error in reconfigure is shown and a retry can succeed."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    with patch(UNEXPECTED, side_effect=RuntimeError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], login(host)
        )
    assert result["errors"] == {"base": "unknown"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host)
    )
    assert result["reason"] == "reconfigure_successful"


async def test_dropped_topology_is_not_called_not_orca(
    hass: HomeAssistant, emulator: Emulator, host: str
) -> None:
    """A display that drops every record is reachable, but not "not an Orca"."""
    emulator.faults = Faults(drop_record_rate=1.0)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )

    assert result["errors"] == {"base": "cannot_connect"}


INVALID_HOSTS = [
    pytest.param("192.168.1.5/cgi/restart?x=", id="endpoint"),
    pytest.param("http://192.168.1.5", id="scheme"),
    pytest.param("192.168.1.5:99999", id="port"),
    pytest.param("orca display", id="space"),
    pytest.param("-", id="dash"),
]


@pytest.mark.parametrize("value", INVALID_HOSTS)
async def test_user_flow_invalid_host(
    hass: HomeAssistant, emulator: Emulator, host: str, value: str
) -> None:
    """Anything but a host is refused before a request can go anywhere."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(value) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["errors"] == {CONF_HOST: "invalid_host"}
    assert emulator.requests == []

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize("value", INVALID_HOSTS)
async def test_reconfigure_invalid_host(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    emulator: Emulator,
    value: str,
) -> None:
    """Reconfigure refuses anything but a host too."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(value)
    )

    assert result["errors"] == {CONF_HOST: "invalid_host"}
    assert emulator.requests == []


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("orca.local", id="same"),
        pytest.param(" ORCA.local ", id="spelling"),
        pytest.param("orca.local:80", id="default_port"),
    ],
)
async def test_already_configured_spellings(hass: HomeAssistant, value: str) -> None:
    """The same display can't be added twice under another spelling."""
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "orca.local"}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(value) | {CONF_ALLOW_POWER_LIMITS: False}
    )

    assert result["reason"] == "already_configured"


async def test_disabled_old_integration_needs_no_warning(
    hass: HomeAssistant, host: str
) -> None:
    """A disabled orca-energy-ha entry doesn't poll, so the flow doesn't warn."""
    MockConfigEntry(
        domain=OLD_DOMAIN,
        unique_id="127.0.0.1",
        data={"hostname": "127.0.0.1"},
        disabled_by=ConfigEntryDisabler.USER,
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_old_integration_warning_comes_before_login(
    hass: HomeAssistant, host: str, emulator: Emulator
) -> None:
    """The old integration never logs out, so the warning can't depend on a login."""
    MockConfigEntry(
        domain=OLD_DOMAIN, unique_id="127.0.0.1", data={"hostname": "127.0.0.1"}
    ).add_to_hass(hass)
    emulator.max_sessions = 0
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["step_id"] == "old_integration"
    assert emulator.requests == []

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "too_many_users"}

    emulator.max_sessions = 2
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], login(host) | {CONF_ALLOW_POWER_LIMITS: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
