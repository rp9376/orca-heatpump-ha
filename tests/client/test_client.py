"""Tests for OrcaClient against the display emulator."""

import asyncio
from collections.abc import AsyncIterator
import logging

import aiohttp
from aiohttp import web
import pytest

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.catalog import CATALOG
from custom_components.orca_heatpump.client.client import OrcaClient
from custom_components.orca_heatpump.client.errors import (
    OrcaAuthError,
    OrcaConnectionError,
    OrcaProtocolError,
    OrcaTagError,
    OrcaTimeoutError,
    OrcaTooManyUsersError,
    OrcaValueError,
    OrcaWriteError,
)
from custom_components.orca_heatpump.client.models import (
    CircuitKind,
    Element,
    Kind,
    Reason,
    TagDef,
)
from tools.emulator import Emulator, Faults

from .helpers import DUMPS, OURS_HEATING

FLOW = catalog.MAX_FLOW_HEATING


@pytest.fixture
def emulator() -> Emulator:
    """Return an emulator serving our pump while it heats."""
    return Emulator.from_dump(
        DUMPS / OURS_HEATING, writable={"2_Max_VF_MK1", "2_Rezim_MK1"}
    )


@pytest.fixture
async def port(socket_enabled: None, emulator: Emulator) -> AsyncIterator[int]:
    """Serve the emulator on a free local port."""
    del socket_enabled
    runner = web.AppRunner(emulator.app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    yield runner.addresses[0][1]
    await runner.cleanup()


@pytest.fixture
async def client(port: int) -> AsyncIterator[OrcaClient]:
    """Return a client of the emulator."""
    async with aiohttp.ClientSession() as session:
        yield OrcaClient(session, "127.0.0.1", "admin", "admin", port=port, timeout=1)


def logins(emulator: Emulator) -> int:
    """Return how many times the client logged in."""
    return sum(path.startswith("/cgi/login") for path in emulator.requests)


async def test_read_everything(client: OrcaClient, emulator: Emulator) -> None:
    """One login, a few requests, a reading for every catalog tag."""
    snapshot = await client.async_read_definitions(CATALOG)

    assert snapshot.value(catalog.HP_TARGET_TEMPERATURE) == 28.0
    assert snapshot.value(catalog.CIRCUIT_MODE, 1) == "heating"
    assert snapshot.value(catalog.CIRCUIT_PUMP, 1) is True
    assert snapshot.reading(catalog.ROOM_TEMPERATURE, 1).reason is Reason.NOT_CONNECTED
    assert snapshot.reading(catalog.ALARM_ERROR).reason is Reason.UNKNOWN_TAG
    assert logins(emulator) == 1
    assert len(emulator.requests) == 3
    assert client.logged_in


async def test_identity_and_topology(client: OrcaClient) -> None:
    """Firmware, outdoor unit and topology of our pump."""
    identity = await client.async_read_identity()
    topology = await client.async_detect_topology()

    assert identity.firmware == "61 (2016-12-12)"
    assert identity.outdoor_unit == "mitsubishi"
    assert topology.schema == 23
    assert [(c.slot, c.kind, c.room_sensor) for c in topology.circuits] == [
        (1, CircuitKind.DIRECT, False),
        (2, CircuitKind.MIXING, False),
    ]


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"2_Verzija_programa_MESEC": "13"}, id="month_13"),
        pytest.param({"2_Verzija_programa_LETO": ""}, id="year_empty"),
    ],
)
async def test_identity_partial(
    client: OrcaClient, emulator: Emulator, overrides: dict[str, str]
) -> None:
    """Odd or missing firmware parts give a partial identity, not an error."""
    emulator.values |= overrides | {"2_Izbira_Mitsubishi_Fujitsu": ""}

    identity = await client.async_read_identity()

    assert (identity.firmware_build, identity.firmware_date, identity.outdoor_unit) == (
        61,
        None,
        None,
    )


async def test_relogin_when_session_expires(
    client: OrcaClient, emulator: Emulator
) -> None:
    """An expired session is renewed once, transparently."""
    await client.async_read(catalog.HP_TEMPERATURE.refs())
    emulator.expire_sessions()

    snapshot = await client.async_read(catalog.HP_TEMPERATURE.refs())

    assert snapshot.value(catalog.HP_TEMPERATURE) == 30.0
    assert logins(emulator) == 2


async def test_login_is_single_flight(client: OrcaClient, emulator: Emulator) -> None:
    """Concurrent reads share one login, one request at a time."""
    await asyncio.gather(
        *(client.async_read(catalog.HP_TEMPERATURE.refs()) for _ in range(5))
    )

    assert logins(emulator) == 1


@pytest.mark.parametrize(
    ("change", "error"),
    [
        pytest.param({"max_sessions": 0}, OrcaTooManyUsersError, id="too_many_users"),
        pytest.param({"password": "other"}, OrcaAuthError, id="wrong_password"),
    ],
)
async def test_login_errors(
    client: OrcaClient,
    emulator: Emulator,
    change: dict[str, object],
    error: type[Exception],
) -> None:
    """Login failures are typed; the client never sleeps or retries."""
    for name, value in change.items():
        setattr(emulator, name, value)

    with pytest.raises(error):
        await client.async_login()
    assert logins(emulator) == 1


async def test_logout(client: OrcaClient, emulator: Emulator) -> None:
    """Logout frees the session; calling it again is harmless."""
    await client.async_login()
    await client.async_login()
    assert len(emulator.sessions) == 1

    await client.async_logout()
    await client.async_logout()

    assert not emulator.sessions
    assert not client.logged_in
    assert sum(p.startswith("/cgi/logout") for p in emulator.requests) == 1


async def test_logout_never_raises(client: OrcaClient, emulator: Emulator) -> None:
    """A failing logout still forgets the token."""
    await client.async_login()
    emulator.faults = Faults(http_status=503)

    await client.async_logout()

    assert not client.logged_in


async def test_missing_records_are_requested_again(
    client: OrcaClient, emulator: Emulator
) -> None:
    """Records missing from a response are re-read in the same poll."""
    emulator.faults.drop_tags_once = {"2_Poti1", "2_Temp_Zunanja"}

    snapshot = await client.async_read_definitions(
        [catalog.HP_TEMPERATURE, catalog.OUTDOOR_TEMPERATURE, catalog.PUMP_P0]
    )

    assert snapshot.value(catalog.HP_TEMPERATURE) == 30.0
    assert snapshot.value(catalog.OUTDOOR_TEMPERATURE) == 7.8
    assert sum(p.startswith("/cgi/readTags") for p in emulator.requests) == 2


async def test_stale_values(client: OrcaClient, emulator: Emulator) -> None:
    """A lost record keeps its value for two polls, marked stale, then goes."""
    refs = catalog.HP_TEMPERATURE.refs() + catalog.ROOM_TEMPERATURE.refs()
    await client.async_read(refs)
    emulator.faults.drop_record_rate = 1.0

    readings = [
        (await client.async_read(refs)).reading(catalog.HP_TEMPERATURE)
        for _ in range(3)
    ]

    assert [(r.value, r.stale) for r in readings] == [
        (30.0, True),
        (30.0, True),
        (None, False),
    ]
    assert readings[2].reason is Reason.NO_RESPONSE


async def test_unknown_option_logged_once(
    client: OrcaClient, emulator: Emulator, caplog: pytest.LogCaptureFixture
) -> None:
    """An unknown enum value reads as None and is logged only once."""
    emulator.values["2_Rezim_MK1"] = "9"

    with caplog.at_level(logging.WARNING):
        for _ in range(2):
            snapshot = await client.async_read(catalog.CIRCUIT_MODE.refs())

    assert snapshot.reading(catalog.CIRCUIT_MODE, 1).reason is Reason.UNKNOWN_OPTION
    assert caplog.text.count("Unknown value 9 of 2_Rezim_MK1") == 1


@pytest.mark.parametrize(
    ("faults", "error", "match"),
    [
        pytest.param(Faults(delay=2), OrcaTimeoutError, "no answer", id="timeout"),
        pytest.param(
            Faults(disconnect=True),
            OrcaConnectionError,
            "cannot reach",
            id="disconnect",
        ),
        pytest.param(
            Faults(http_status=408), OrcaProtocolError, "too large", id="http_408"
        ),
        pytest.param(
            Faults(http_status=503), OrcaProtocolError, "HTTP status 503", id="http_503"
        ),
        pytest.param(
            Faults(malformed_body=True), OrcaProtocolError, "malformed", id="malformed"
        ),
        pytest.param(
            Faults(whole_error="E_FAIL"), OrcaProtocolError, "E_FAIL", id="whole_error"
        ),
    ],
)
async def test_read_errors(
    client: OrcaClient,
    emulator: Emulator,
    faults: Faults,
    error: type[Exception],
    match: str,
) -> None:
    """Transport and protocol failures surface as typed errors."""
    await client.async_login()
    emulator.faults = faults

    with pytest.raises(error, match=match):
        await client.async_read(catalog.HP_TEMPERATURE.refs())


async def test_unreachable(socket_enabled: None) -> None:
    """A closed port is a connection error."""
    del socket_enabled
    async with aiohttp.ClientSession() as session:
        client = OrcaClient(session, "127.0.0.1", "admin", "admin", port=1, timeout=1)

        with pytest.raises(OrcaConnectionError):
            await client.async_login()


async def test_write(client: OrcaClient, emulator: Emulator) -> None:
    """A write is sent once and read back."""
    await client.async_write(FLOW, 1, 30.5)

    assert emulator.writes == [("2_Max_VF_MK1", 305)]
    assert (await client.async_read(FLOW.refs())).value(FLOW, 1) == 30.5


async def test_write_unchanged_is_skipped(
    client: OrcaClient, emulator: Emulator
) -> None:
    """Writing the current value sends nothing (flash wear, R10)."""
    await client.async_write(FLOW, 1, 28.0)

    assert emulator.writes == []
    assert not any(p.startswith("/cgi/writeTags") for p in emulator.requests)


async def test_invalid_write_sends_nothing(
    client: OrcaClient, emulator: Emulator
) -> None:
    """Validation happens before any request."""
    with pytest.raises(OrcaValueError):
        await client.async_write(FLOW, 1, 99.0)

    assert emulator.requests == []


@pytest.mark.parametrize(
    ("definition", "slot", "value", "error", "match"),
    [
        pytest.param(FLOW, 2, 30.0, OrcaWriteError, "E_WRITEFORBIDDEN", id="forbidden"),
        pytest.param(
            TagDef(
                key="gone",
                element=Element.SYSTEM,
                kind=Kind.BOOL,
                tag="2_Gone",
                writable=True,
            ),
            None,
            True,
            OrcaTagError,
            "not readable",
            id="unknown_tag",
        ),
    ],
)
async def test_write_rejected(
    client: OrcaClient,
    definition: TagDef,
    slot: int | None,
    value: float | bool,
    error: type[Exception],
    match: str,
) -> None:
    """Writes the display refuses raise and change nothing."""
    with pytest.raises(error, match=match):
        await client.async_write(definition, slot, value)


async def test_write_not_taking_effect(client: OrcaClient, emulator: Emulator) -> None:
    """A write the controller ignores is caught by the read-back."""
    emulator.faults.ignore_writes = True

    with pytest.raises(OrcaWriteError, match="reads '280' after writing 300"):
        await client.async_write(FLOW, 1, 30.0)
