"""Async client for the Orca display."""

import asyncio
from collections.abc import Callable, Iterable, Sequence
import contextlib
from dataclasses import replace
from datetime import date
import logging
from typing import TYPE_CHECKING, Final

import aiohttp
from yarl import URL

from . import catalog
from .codec import decode, decode_timers, encode
from .errors import (
    OrcaConnectionError,
    OrcaError,
    OrcaProtocolError,
    OrcaSessionExpiredError,
    OrcaTagError,
    OrcaTimeoutError,
    OrcaWriteError,
)
from .models import (
    DeviceIdentity,
    PumpTopology,
    Reading,
    Reason,
    Snapshot,
    TagDef,
    TagRef,
    TimerProgramme,
    Value,
)
from .protocol import (
    LOGOUT,
    STATUS_OK,
    Record,
    login_target,
    parse_login,
    parse_records,
    parse_write_status,
    read_batches,
    read_target,
    write_target,
)
from .topology import detect_topology

_LOGGER = logging.getLogger(__name__)

# A record missing from a response keeps its last value for this many polls,
# marked stale, so entities don't flap on one bad response.
MAX_STALE_POLLS: Final = 2
DEFAULT_TIMEOUT: Final = 15.0

IDENTITY: Final = (
    catalog.FIRMWARE_BUILD,
    catalog.FIRMWARE_YEAR,
    catalog.FIRMWARE_MONTH,
    catalog.FIRMWARE_DAY,
    catalog.OUTDOOR_UNIT_BRAND,
)
TOPOLOGY: Final = (
    catalog.SCHEMA,
    catalog.BUFFER_PRESENT,
    catalog.ROOM_SENSOR_CONFIGURED,
    catalog.ROOM_TEMPERATURE,
)


class OrcaClient:
    """Talks to one display; every request goes through one lock.

    The display allows only a few sessions, so the client logs in once,
    re-logs in once when the session expires and logs out on request.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        port: int = 80,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the client; ``session`` is owned by the caller."""
        self._session = session
        self._base = f"http://{host}" if port == 80 else f"http://{host}:{port}"
        self._username = username
        self._password = password
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._token: str | None = None
        self._closed = False
        self._last: dict[str, tuple[Reading, int]] = {}
        self._logged_options: set[tuple[str, str | None]] = set()

    @property
    def logged_in(self) -> bool:
        """Return whether the client holds a session token."""
        return self._token is not None

    async def async_login(self) -> None:
        """Log in now; usually the first request does it."""
        async with self._lock:
            if self._token is None:
                await self._login()

    async def async_logout(self) -> None:
        """Log out; safe to call at any time, never raises."""
        async with self._lock:
            if self._token is None:
                return
            try:
                await self._get(LOGOUT)
            except OrcaError as err:
                _LOGGER.debug("Logout failed: %s", err)
            finally:
                self._token = None

    async def async_close(self) -> None:
        """Log out for good: later requests fail instead of logging in again.

        A refresh that follows a write could otherwise open a session nobody
        logs out, on a display with very few of them.
        """
        self._closed = True
        await self.async_logout()

    async def async_read(self, refs: Iterable[TagRef]) -> Snapshot:
        """Read and decode tags; the snapshot has a reading for every one."""
        wanted = [(d, s, tag) for d, s in refs if (tag := d.tag_name(s)) is not None]
        async with self._lock:
            try:
                records = await self._read_records(
                    list(dict.fromkeys(tag for _, _, tag in wanted))
                )
            except OrcaError:
                # Stale values may bridge dropped records, not an outage.
                self._last.clear()
                raise
        readings: dict[str, Reading] = {}
        for definition, slot, tag in wanted:
            readings[tag] = self._reading(definition, slot, tag, records.get(tag))
        return Snapshot(readings)

    async def async_read_definitions(self, definitions: Iterable[TagDef]) -> Snapshot:
        """Read every tag of the given catalog entries."""
        return await self.async_read(ref for d in definitions for ref in d.refs())

    async def async_write(
        self, definition: TagDef, slot: int | None, value: Value
    ) -> None:
        """Write a value: validated, skipped when unchanged, and read back.

        Raises OrcaValueError before any request if the value is invalid.
        """
        raw = encode(definition, slot, value)
        tag = definition.tag_name(slot)
        if TYPE_CHECKING:
            assert tag is not None
        async with self._lock:
            current = (await self._read_records([tag])).get(tag)
            if current is None or current.status != STATUS_OK:
                raise OrcaTagError(f"{tag} is not readable before writing")
            if (current.value or "").strip() == str(raw):
                return
            status = await self._authenticated(
                write_target(tag, raw), lambda text: parse_write_status(text, tag)
            )
            if status not in (None, STATUS_OK):
                raise OrcaWriteError(f"writing {tag} = {raw} failed: {status}")
            check = (await self._read_records([tag])).get(tag)
        if check is None or (check.value or "").strip() != str(raw):
            got = check.value if check else None
            raise OrcaWriteError(f"{tag} reads {got!r} after writing {raw}")

    async def async_read_identity(self) -> DeviceIdentity:
        """Return firmware and outdoor unit as far as the pump tells them."""
        snapshot = await self.async_read_definitions(IDENTITY)
        build = snapshot.value(catalog.FIRMWARE_BUILD)
        year, month, day = (
            snapshot.value(d)
            for d in (
                catalog.FIRMWARE_YEAR,
                catalog.FIRMWARE_MONTH,
                catalog.FIRMWARE_DAY,
            )
        )
        firmware_date: date | None = None
        if isinstance(year, int) and isinstance(month, int) and isinstance(day, int):
            with contextlib.suppress(ValueError, OverflowError):
                firmware_date = date(2000 + year, month, day)
        brand = snapshot.value(catalog.OUTDOOR_UNIT_BRAND)
        return DeviceIdentity(
            build if isinstance(build, int) else None,
            firmware_date,
            brand if isinstance(brand, str) else None,
        )

    async def async_read_timers(self) -> dict[int, TimerProgramme]:
        """Read the weekly timer programmes that came back complete."""
        tags = [
            tag
            for programme in catalog.TIMER_PROGRAMMES
            for time_range in catalog.TIMER_RANGES
            for tag in catalog.timer_tags(programme, time_range)
        ]
        async with self._lock:
            records = await self._read_records(tags)
        return decode_timers(records)

    async def async_detect_topology(self) -> PumpTopology:
        """Return the pump's topology (raises if a signal is not received)."""
        return detect_topology(await self.async_read_definitions(TOPOLOGY))

    def _reading(
        self, definition: TagDef, slot: int | None, tag: str, record: Record | None
    ) -> Reading:
        reading = decode(definition, slot, record)
        if reading.reason is Reason.NO_RESPONSE:
            previous = self._last.get(tag)
            if previous is not None and previous[1] < MAX_STALE_POLLS:
                self._last[tag] = (previous[0], previous[1] + 1)
                return replace(previous[0], stale=True)
            self._last.pop(tag, None)
            return reading
        if reading.value is not None:
            self._last[tag] = (reading, 0)
        else:
            self._last.pop(tag, None)
        if reading.reason is Reason.UNKNOWN_OPTION and (
            (tag, reading.raw) not in self._logged_options
        ):
            self._logged_options.add((tag, reading.raw))
            _LOGGER.warning("Unknown value %s of %s", reading.raw, tag)
        return reading

    async def _read_records(self, tags: Sequence[str]) -> dict[str, Record]:
        records: dict[str, Record] = {}
        for batch in read_batches(tags):
            for record in await self._authenticated(read_target(batch), parse_records):
                records[record.tag] = record
        # Re-request missing records once, so one bad answer can't hide them.
        if missing := [tag for tag in tags if tag not in records]:
            _LOGGER.debug("Re-reading %d missing records", len(missing))
            for batch in read_batches(missing):
                for record in await self._authenticated(
                    read_target(batch), parse_records
                ):
                    records[record.tag] = record
        return records

    async def _authenticated[T](self, target: str, parse: Callable[[str], T]) -> T:
        if self._token is None:
            await self._login()
        try:
            return parse(await self._get(target))
        except OrcaSessionExpiredError:
            _LOGGER.debug("Session expired, logging in again")
            self._token = None
            await self._login()
            return parse(await self._get(target))

    async def _login(self) -> None:
        if self._closed:
            raise OrcaConnectionError("the client is closed")
        self._token = parse_login(
            await self._get(login_target(self._username, self._password))
        )

    async def _get(self, target: str) -> str:
        headers = {"Cookie": f"IDALToken={self._token}"} if self._token else {}
        url = URL(self._base + target, encoded=True)
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(
                    url, headers=headers, allow_redirects=False
                ) as response:
                    body = await response.read()
                    status = response.status
        except TimeoutError as err:
            raise OrcaTimeoutError(f"no answer from {self._base}") from err
        except aiohttp.ClientError as err:
            # aiohttp's message can hold the URL, and the login URL the password.
            raise OrcaConnectionError(
                f"cannot reach {self._base}: {_describe(err)}"
            ) from None
        if status == 408:
            raise OrcaProtocolError("request too large for the display (HTTP 408)")
        if status not in (200, 500):
            raise OrcaProtocolError(f"unexpected HTTP status {status}")
        return body.decode("utf-8", "replace")


def _describe(err: aiohttp.ClientError) -> str:
    if isinstance(err, aiohttp.ClientResponseError):
        return f"{type(err).__name__}: {err.status}, {err.message}"
    return type(err).__name__
