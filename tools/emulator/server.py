"""A fake Orca display: the IDAL CGI API as research found it, plus faults.

It serves tag values from a dump fixture and behaves like the real display
(research/findings.md): a token per login, a few session slots, an idle
timeout, errors as HTTP 500 with a ``#E_…`` body, and HTTP 408 for header
blocks over 4,095 bytes. Fault switches let tests break it on purpose.
"""

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
import secrets
import time
from typing import Any

from aiohttp import web

HEADER_LIMIT = 4095
NEED_LOGIN = "#E_NEED_LOGIN\n"
TOO_LARGE = (
    "<HTML><HEAD><TITLE>Error 408</TITLE></HEAD><BODY><H1>Error 408</H1>"
    "<P>Request Timeout</P></BODY></HTML>"
)


@dataclass
class Faults:
    """Ways to make the emulator misbehave."""

    drop_record_rate: float = 0.0
    drop_tags_once: set[str] = field(default_factory=set)
    ignore_writes: bool = False
    delay: float = 0.0
    malformed_body: bool = False
    http_status: int | None = None
    whole_error: str | None = None
    disconnect: bool = False
    fail_after_requests: int | None = None


@dataclass
class Emulator:
    """State of a fake display; ``app`` serves it."""

    values: dict[str, str]
    writable: set[str] = field(default_factory=set)
    username: str = "admin"
    password: str = "admin"
    max_sessions: int = 2
    idle_timeout: float = 150.0
    faults: Faults = field(default_factory=Faults)
    clock: Callable[[], float] = time.monotonic
    sessions: dict[str, float] = field(default_factory=dict)
    writes: list[tuple[str, int]] = field(default_factory=list)
    requests: list[str] = field(default_factory=list)
    rng: random.Random = field(default_factory=lambda: random.Random(0))

    @classmethod
    def from_dump(cls, path: Path, **kwargs: Any) -> Emulator:
        """Create an emulator from a dump fixture; only S_OK tags exist."""
        tags: Mapping[str, Mapping[str, str]] = json.loads(
            path.read_text(encoding="utf-8")
        )["tags"]
        values = {
            tag: record["value"]
            for tag, record in tags.items()
            if record["status"] == "S_OK"
        }
        return cls(values, **kwargs)

    @property
    def app(self) -> web.Application:
        """Return the aiohttp application serving this emulator."""
        app = web.Application(middlewares=[self._middleware])
        app.router.add_get("/cgi/login", self._login)
        app.router.add_get("/cgi/logout", self._logout)
        app.router.add_get("/cgi/readTags", self._read_tags)
        app.router.add_get("/cgi/writeTags", self._write_tags)
        return app

    def expire_sessions(self) -> None:
        """Forget every session, as after a display restart."""
        self.sessions.clear()

    @web.middleware
    async def _middleware(
        self,
        request: web.Request,
        handler: Callable[[web.Request], Any],
    ) -> web.StreamResponse:
        self.requests.append(request.path_qs)
        header_bytes = (
            len(f"{request.method} {request.raw_path} HTTP/1.1\r\n")
            + sum(len(name) + len(value) + 4 for name, value in request.raw_headers)
            + 2
        )
        if header_bytes > HEADER_LIMIT:
            return web.Response(status=408, text=TOO_LARGE, content_type="text/html")
        if self.faults.delay:
            await asyncio.sleep(self.faults.delay)
        if self.faults.disconnect and request.transport is not None:
            request.transport.close()
            return web.Response()
        failing = self.faults.fail_after_requests
        if self.faults.http_status is not None or (
            failing is not None and len(self.requests) > failing
        ):
            return web.Response(status=self.faults.http_status or 503, text="error")
        if self.faults.malformed_body:
            return web.Response(text="#broken\n\x00garbage")
        response: web.StreamResponse = await handler(request)
        return response

    def _token(self, request: web.Request) -> str | None:
        token = request.cookies.get("IDALToken")
        if token is None or token not in self.sessions:
            return None
        if self.clock() - self.sessions[token] > self.idle_timeout:
            del self.sessions[token]
            return None
        self.sessions[token] = self.clock()
        return token

    async def _login(self, request: web.Request) -> web.Response:
        query = request.query
        if (
            query.get("username") != self.username
            or query.get("password") != self.password
        ):
            return _text("#E_PASS_DONT_MATCH\n")
        now = self.clock()
        for token, used in list(self.sessions.items()):
            if now - used > self.idle_timeout:
                del self.sessions[token]
        if len(self.sessions) >= self.max_sessions:
            return _text("#E_TOO_MANY_USERS\n")
        token = secrets.token_hex(16)
        self.sessions[token] = now
        return _text(f"1\n#S_OK\nIDALToken={token}")

    async def _logout(self, request: web.Request) -> web.Response:
        if (token := self._token(request)) is None:
            return _text(NEED_LOGIN, status=500)
        del self.sessions[token]
        return _text("1\n#S_OK")

    async def _read_tags(self, request: web.Request) -> web.Response:
        if self._token(request) is None:
            return _text(NEED_LOGIN, status=500)
        if self.faults.whole_error:
            return _text(f"#{self.faults.whole_error}\n")
        tags = [
            request.query[f"t{index}"]
            for index in range(1, int(request.query.get("n", "0")) + 1)
        ]
        body = "".join(self._record(tag) for tag in tags if not self._drop(tag))
        return _text(body)

    async def _write_tags(self, request: web.Request) -> web.Response:
        if self._token(request) is None:
            return _text(NEED_LOGIN, status=500)
        tag, raw = request.query["t1"], int(request.query["v1"])
        if tag not in self.values:
            return _text(f"#{tag}\tE_UNKNOWNTAG\n")
        if tag not in self.writable:
            return _text(f"#{tag}\tE_WRITEFORBIDDEN\n")
        self.writes.append((tag, raw))
        if not self.faults.ignore_writes:
            self.values[tag] = str(raw)
        return _text(self._record(tag))

    def _drop(self, tag: str) -> bool:
        if tag in self.faults.drop_tags_once:
            self.faults.drop_tags_once.discard(tag)
            return True
        return self.rng.random() < self.faults.drop_record_rate

    def _record(self, tag: str) -> str:
        if tag not in self.values:
            return f"#{tag}\tE_UNKNOWNTAG\n"
        return f"#{tag}\tS_OK\n192\t{self.values[tag]}\n"


def _text(body: str, status: int = 200) -> web.Response:
    return web.Response(status=status, text=body)
