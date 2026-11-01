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
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from tools.emulator import Emulator

from tests.client.helpers import DUMPS, DUO, MONO, OURS_HEATING

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
DUO_TOPOLOGY = PumpTopology(
    3,
    (CircuitTopology(1, CircuitKind.DIRECT, room_sensor=True),),
    dhw=True,
    solar=False,
    buffer=False,
)
MONO_TOPOLOGY = PumpTopology(
    7,
    (
        CircuitTopology(1, CircuitKind.DIRECT, room_sensor=True),
        CircuitTopology(2, CircuitKind.DIRECT, room_sensor=True),
    ),
    dhw=True,
    solar=False,
    buffer=True,
)
# The three real pumps: our Duo 300 Solar (heating), a Duo and a Mono.
PUMPS = {
    "ours": (OURS_HEATING, OUR_TOPOLOGY),
    "duo": (DUO, DUO_TOPOLOGY),
    "mono": (MONO, MONO_TOPOLOGY),
}


async def serve(emulator: Emulator) -> tuple[web.AppRunner, str]:
    """Serve an emulator on a free local port; return the runner and host."""
    runner = web.AppRunner(emulator.app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", 0).start()
    return runner, f"127.0.0.1:{runner.addresses[0][1]}"


@pytest.fixture
def pump(request: pytest.FixtureRequest) -> str:
    """Return which real pump to emulate; parametrize indirectly for others."""
    return getattr(request, "param", "ours")


@pytest.fixture
def platforms() -> list[Platform]:
    """Return the platforms to set up; platform tests override this."""
    return []


@pytest.fixture
def emulator(pump: str) -> Emulator:
    """Return an emulator serving the pump's dump."""
    return Emulator.from_dump(DUMPS / PUMPS[pump][0])


@pytest.fixture
async def host(socket_enabled: None, emulator: Emulator) -> AsyncIterator[str]:
    """Serve the emulator; return its host:port."""
    del socket_enabled
    runner, host = await serve(emulator)
    yield host
    await runner.cleanup()


@pytest.fixture
def mock_config_entry(host: str, pump: str) -> MockConfigEntry:
    """Return a config entry of the pump on the emulator."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_TITLE,
        entry_id="01ORCAHEATPUMPTESTENTRY000",
        unique_id=host,
        data={
            CONF_HOST: host,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin",
            CONF_TOPOLOGY: topology_to_data(PUMPS[pump][1]),
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
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, platforms: list[Platform]
) -> AsyncIterator[MockConfigEntry]:
    """Set up the integration with only the given platforms."""
    with patch("custom_components.orca_heatpump.PLATFORMS", platforms):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        yield mock_config_entry
