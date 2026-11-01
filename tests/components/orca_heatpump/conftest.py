"""Fixtures for the Orca Heat Pump integration tests."""

from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, patch

from aiohttp import web
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.orca_heatpump.client.models import (
    CircuitKind,
    CircuitTopology,
    PumpTopology,
)
from custom_components.orca_heatpump.const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_TOPOLOGY,
    DEFAULT_TITLE,
    DOMAIN,
)
from custom_components.orca_heatpump.helpers import topology_to_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from tools.emulator import Emulator

from tests.client.helpers import DUMPS, OURS_HEATING

OUR_TOPOLOGY = PumpTopology(
    23,
    (
        CircuitTopology(1, CircuitKind.DIRECT, room_sensor=False),
        CircuitTopology(2, CircuitKind.MIXING, room_sensor=False),
    ),
    dhw=True,
    solar=True,
    buffer=False,
)


async def serve(emulator: Emulator) -> tuple[web.AppRunner, str]:
    """Serve an emulator on a free local port; return the runner and host."""
    runner = web.AppRunner(emulator.app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", 0).start()
    return runner, f"127.0.0.1:{runner.addresses[0][1]}"


@pytest.fixture
def emulator() -> Emulator:
    """Return an emulator serving our pump while it heats."""
    return Emulator.from_dump(DUMPS / OURS_HEATING)


@pytest.fixture
async def host(socket_enabled: None, emulator: Emulator) -> AsyncIterator[str]:
    """Serve the emulator; return its host:port."""
    del socket_enabled
    runner, host = await serve(emulator)
    yield host
    await runner.cleanup()


@pytest.fixture
def mock_config_entry(host: str) -> MockConfigEntry:
    """Return a config entry of our pump on the emulator."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_TITLE,
        unique_id=host,
        data={
            CONF_HOST: host,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin",
            CONF_TOPOLOGY: topology_to_data(OUR_TOPOLOGY),
        },
        options={CONF_ALLOW_POWER_LIMITS: False},
    )


@pytest.fixture
def mock_setup_entry() -> Iterator[AsyncMock]:
    """Keep config flow tests from setting the entry up."""
    with patch(
        "custom_components.orca_heatpump.async_setup_entry", return_value=None
    ) as mock:
        yield mock


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the integration against the emulator."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
