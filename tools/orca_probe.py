"""Research CLI for the Orca heat pump display. Only the lead agent runs it.

Every request goes through one method that enforces the endpoint allowlist of
PLAN.md §2.2. A lock file keeps two sessions from overlapping, and every
session logs out in a ``finally``. Raw responses and a per-request log land in
research/captures/ (gitignored).

Usage (from the repository root):
  python -m tools.orca_probe --host HOST console   save the static console files
  python -m tools.orca_probe --host HOST dump      read all known tags, then log out
"""

import argparse
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import fcntl
import http.client
from itertools import batched
import json
from pathlib import Path
import posixpath
import re
import signal
import sys
import time
from urllib.parse import quote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / "research" / "captures"
LOCK_PATH = ROOT / ".scratch" / "orca_probe.lock"
REQUEST_LOG = CAPTURES / "requests.jsonl"
ALL_FIELDS = ROOT.parent / "orca-energy-ha" / "development_resources" / "all_fields.txt"

# Read-only endpoints allowed without asking (PLAN.md §2.2). readFile (R14)
# and writeTags (Phase 6, user present) are deliberately not here.
ALLOWED_CGI = frozenset(
    {
        "login",
        "logout",
        "readTags",
        "browse",
        "getProperties",
        "readAlarms",
        "readGroups",
        "readIDALStatusParameters",
        "getTCPIPSettings",
        "getPLCStatus",
        "getTime",
        "getLocalTime",
        "getDLSSettings",
        "readTrend",
        "readEvent",
        "getPropertyGroup",
        "browsePropertyGroup",
    }
)
# cgi/readFile is approved for R14 only (user, 2026-10-30): reachable solely
# through Display.read_file, for paths listed explicitly per run.
READ_FILE = "/cgi/readFile"
# Password and code tags are never read (CLAUDE.md, data hygiene).
SECRET_TAG_RE = re.compile(r"geslo|kod[ae]", re.IGNORECASE)
# PLAN.md §2.2 rule 3: 15 minutes in total, never faster, then ask the user.
BACKOFF_MINUTES = (1, 2, 4, 8)
REQUEST_PAUSE = 1.0
TIMEOUT = 30.0
BATCH_SIZE = 150
RETRY_BATCH_SIZE = 50
MAX_PASSES = 4
CLIENT_ID = "orca_probe"
TAG_RE = re.compile(r"[A-Za-z0-9_()]+")
STATIC_SUFFIXES = (".html", ".htm", ".js", ".css", ".jar")
MAX_STATIC_FILES = 300
LINK_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"'#?\s]+)""", re.IGNORECASE)
STRING_REF_RE = re.compile(
    r"""["']([\w./-]+\.(?:html?|js|css|jar))["']""", re.IGNORECASE
)


class ProbeError(Exception):
    """A request was refused locally or the display answered unexpectedly."""


class TooManyUsersError(ProbeError):
    """The display still reported E_TOO_MANY_USERS after the full backoff."""


class NeedLoginError(ProbeError):
    """The display reported E_NEED_LOGIN: the session is gone."""


@dataclass(frozen=True)
class Record:
    """One tag record of a readTags response."""

    status: str
    quality: str | None
    value: str | None


@dataclass(frozen=True)
class Response:
    """A raw HTTP response, plus the size of the header block we sent."""

    status: int
    headers: dict[str, str]
    body: bytes
    header_bytes: int
    seconds: float

    @property
    def text(self) -> str:
        """The body as text."""
        return self.body.decode("utf-8", "replace")


@dataclass
class Display:
    """Serial, allowlisted HTTP access to the display."""

    host: str
    port: int = 80
    token: str | None = None
    readfile_paths: frozenset[str] = frozenset()
    _last_request: float = field(default=0.0, repr=False)

    def get(
        self, path: str, query: str = "", extra_headers: dict[str, str] | None = None
    ) -> Response:
        """GET an allowlisted path."""
        self._check_allowed(path)
        return self._send("GET", path, query, None, extra_headers or {})

    def post(self, path: str, form: str) -> Response:
        """POST a form body to an allowlisted path, as the vendor client does."""
        self._check_allowed(path)
        return self._send("POST", path, "", form.encode(), {})

    def read_file(
        self, file_path: str, mode: str = "ASCII", method: str = "GET"
    ) -> Response:
        """Read one file for R14, if it is on this run's explicit list."""
        if file_path not in self.readfile_paths:
            raise ProbeError(f"refused readFile path {file_path!r}: not listed")
        form = f"MODE={mode}&PATH={quote(file_path, safe='/')}"
        if method == "POST":
            return self._send("POST", READ_FILE, "", form.encode(), {})
        return self._send("GET", READ_FILE, form, None, {})

    def header_size(
        self,
        method: str,
        path: str,
        query: str = "",
        body: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> int:
        """Return the bytes of request line and headers that a request sends."""
        target = f"{path}?{query}" if query else path
        # putrequest adds exactly Host and Accept-Encoding; the display rejects
        # header blocks over about 4 KiB, so the research needs the exact size.
        lines = [
            f"{method} {target} HTTP/1.1",
            f"Host: {self.host}" + (f":{self.port}" if self.port != 80 else ""),
            "Accept-Encoding: identity",
            *(
                f"{name}: {value}"
                for name, value in self._headers(body, extra_headers or {}).items()
            ),
        ]
        return sum(len(line) + 2 for line in lines) + 2

    def _headers(
        self, body: bytes | None, extra_headers: dict[str, str]
    ) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.token:
            headers["Cookie"] = f"IDALToken={self.token}"
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["Content-Length"] = str(len(body))
        return headers | extra_headers

    def _send(
        self,
        method: str,
        path: str,
        query: str,
        body: bytes | None,
        extra_headers: dict[str, str],
    ) -> Response:
        if (wait := self._last_request + REQUEST_PAUSE - time.monotonic()) > 0:
            time.sleep(wait)
        target = f"{path}?{query}" if query else path
        headers = self._headers(body, extra_headers)
        header_bytes = self.header_size(method, path, query, body, extra_headers)
        started = datetime.now().astimezone()
        start = time.monotonic()
        conn = http.client.HTTPConnection(self.host, self.port, timeout=TIMEOUT)
        try:
            conn.putrequest(method, target)
            for name, value in headers.items():
                conn.putheader(name, value)
            conn.endheaders(body)
            raw = conn.getresponse()
            data = raw.read()
        except (OSError, http.client.HTTPException) as err:
            self._last_request = time.monotonic()
            self._log(started, method, path, query, header_bytes, None, repr(err))
            raise
        finally:
            conn.close()
        self._last_request = time.monotonic()
        response = Response(
            raw.status,
            dict(raw.getheaders()),
            data,
            header_bytes,
            round(self._last_request - start, 3),
        )
        self._log(started, method, path, query, header_bytes, response, None)
        return response

    @staticmethod
    def _log(
        started: datetime,
        method: str,
        path: str,
        query: str,
        header_bytes: int,
        response: Response | None,
        error: str | None,
    ) -> None:
        _log_request(
            {
                "time": started.isoformat(timespec="milliseconds"),
                "method": method,
                "path": path,
                "query": _mask_password(query)[:300],
                "tags": query.count("&t"),
                "header_bytes": header_bytes,
                "status": response.status if response else None,
                "bytes": len(response.body) if response else 0,
                "seconds": response.seconds if response else None,
                "head": response.body[:80].decode("utf-8", "replace")
                if response
                else "",
                "response_headers": response.headers if response else None,
                "error": error,
            }
        )

    @staticmethod
    def _check_allowed(path: str) -> None:
        if ".." in path or not path.startswith("/"):
            raise ProbeError(f"refused path {path!r}")
        if path.startswith("/cgi/"):
            if path.removeprefix("/cgi/") not in ALLOWED_CGI:
                raise ProbeError(f"refused endpoint {path!r}: not on the allowlist")
        elif path != "/" and not path.startswith("/console-carel/"):
            raise ProbeError(f"refused static path {path!r}")


def _mask_password(query: str) -> str:
    return re.sub(r"(password=)[^&]*", r"\1***", query)


def _log_request(entry: dict[str, object]) -> None:
    REQUEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REQUEST_LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")


@contextmanager
def exclusive() -> Iterator[None]:
    """Hold the probe lock: never two pump sessions at once."""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ProbeError("another orca_probe holds the lock") from None
        yield


@contextmanager
def session(display: Display, username: str, password: str) -> Iterator[None]:
    """Log in, and always log out afterwards."""
    login(display, username, password)
    try:
        yield
    finally:
        logout(display)


def login(display: Display, username: str, password: str) -> None:
    """Log in, backing off on E_TOO_MANY_USERS per PLAN.md §2.2."""
    for wait in (*BACKOFF_MINUTES, None):
        text = display.get(
            "/cgi/login", f"username={username}&password={password}"
        ).text
        if match := re.search(r"IDALToken=(\w+)", text):
            display.token = match.group(1)
            print(f"{_now()} logged in")
            return
        if "E_TOO_MANY_USERS" not in text:
            raise ProbeError(f"login failed: {text.strip()[:200]!r}")
        if wait is None:
            raise TooManyUsersError("E_TOO_MANY_USERS after 15 minutes; ask the user")
        print(f"{_now()} E_TOO_MANY_USERS, waiting {wait} min")
        time.sleep(wait * 60)


def logout(display: Display) -> Response | None:
    """Log out; never raises, so it is safe in a finally."""
    if display.token is None:
        return None
    response: Response | None = None
    try:
        response = display.get("/cgi/logout")
    except (OSError, http.client.HTTPException, ProbeError) as err:
        print(f"{_now()} logout failed: {err!r}")
    else:
        print(f"{_now()} logged out: HTTP {response.status} {response.text[:120]!r}")
    display.token = None
    return response


def parse_records(text: str) -> dict[str, Record]:
    r"""Parse ``#<tag>\t<status>\n<quality>\t<value>`` records."""
    records: dict[str, Record] = {}
    for chunk in text.replace("\r", "").split("#")[1:]:
        head, _, rest = chunk.partition("\n")
        tag, _, status = head.partition("\t")
        quality: str | None = None
        value: str | None = None
        if line := rest.rstrip("\n"):
            quality, _, value = line.partition("\t")
        records[tag.strip()] = Record(status.strip(), quality, value)
    return records


def read_tags_query(tags: list[str], client: str | None = CLIENT_ID) -> str:
    """Build a readTags query; refuse malformed, password and code tags."""
    if bad := [tag for tag in tags if not TAG_RE.fullmatch(tag)]:
        raise ProbeError(f"refused tag names {bad}")
    if secret := [tag for tag in tags if SECRET_TAG_RE.search(tag)]:
        raise ProbeError(f"refused password/code tags {secret}")
    prefix = f"client={client}&" if client is not None else ""
    return f"{prefix}n={len(tags)}" + "".join(
        f"&t{index}={tag}" for index, tag in enumerate(tags, 1)
    )


def read_tags(
    display: Display, tags: list[str], client: str | None = CLIENT_ID
) -> tuple[Response, dict[str, Record]]:
    """Read one batch of tags."""
    response = display.get("/cgi/readTags", read_tags_query(tags, client))
    if "E_NEED_LOGIN" in response.text:
        raise NeedLoginError(response.text.strip()[:200])
    return response, parse_records(response.text)


def run_dump(display: Display, out_dir: Path) -> None:
    """Read all known tags in passes until two passes agree (at most 4)."""
    tags = [
        tag
        for tag in ALL_FIELDS.read_text(encoding="utf-8").split()
        if not SECRET_TAG_RE.search(tag)
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    passes: list[dict[str, object]] = []
    merged: dict[str, Record] = {}
    previous_ok: set[str] | None = None
    for number in range(1, MAX_PASSES + 1):
        records: dict[str, Record] = {}
        for index, batch in enumerate(batched(tags, BATCH_SIZE, strict=False), 1):
            response, parsed = read_tags(display, list(batch))
            (out_dir / f"pass{number}_batch{index:02}.txt").write_bytes(response.body)
            records |= {tag: parsed[tag] for tag in batch if tag in parsed}
        missing = [tag for tag in tags if tag not in records]
        for index, batch in enumerate(
            batched(missing, RETRY_BATCH_SIZE, strict=False), 1
        ):
            response, parsed = read_tags(display, list(batch))
            (out_dir / f"pass{number}_retry{index:02}.txt").write_bytes(response.body)
            records |= {tag: parsed[tag] for tag in batch if tag in parsed}
        still_missing = [tag for tag in tags if tag not in records]
        ok = {tag for tag, record in records.items() if record.status == "S_OK"}
        for tag, record in records.items():
            if record.status == "S_OK" or tag not in merged:
                merged[tag] = record
        passes.append(
            {
                "pass": number,
                "finished": _now(),
                "missing": missing,
                "missing_after_retry": still_missing,
                "ok": len(ok),
                "statuses": Counter(record.status for record in records.values()),
            }
        )
        print(
            f"{_now()} pass {number}: {len(ok)} S_OK, {len(missing)} missing,"
            f" {len(still_missing)} still missing after retry"
        )
        if ok == previous_ok:
            break
        previous_ok = ok
    _write_dump(out_dir, tags, merged, passes)


def _write_dump(
    out_dir: Path,
    tags: list[str],
    merged: dict[str, Record],
    passes: list[dict[str, object]],
) -> None:
    lines = []
    for tag in tags:
        record = merged.get(tag)
        if record is None:
            lines.append(f"{tag}: <no_response>")
        elif record.status == "S_OK":
            lines.append(f"{tag}: {record.value}")
        else:
            lines.append(f"{tag}: <{record.status}>")
    (out_dir / "full_dump.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "full_dump.json").write_text(
        json.dumps(
            {
                "captured": _now(),
                "tag_source": "orca-energy-ha development_resources/all_fields.txt",
                "batch_size": BATCH_SIZE,
                "passes": passes,
                "tags": {
                    tag: (
                        None
                        if (record := merged.get(tag)) is None
                        else {
                            "status": record.status,
                            "quality": record.quality,
                            "value": record.value,
                        }
                    )
                    for tag in tags
                },
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


def run_console(display: Display, out_dir: Path) -> None:
    """Save the login page and the static console files it references."""
    queue = ["/", "/console-carel/INDEX.HTML", "/console-carel/ICUGateway.jar"]
    seen: set[str] = set()
    saved = 0
    while queue and saved < MAX_STATIC_FILES:
        path = queue.pop(0)
        if path.lower() in seen:
            continue
        seen.add(path.lower())
        try:
            response = display.get(path)
        except ProbeError as err:
            print(f"skipped {path}: {err}")
            continue
        target = out_dir / ("root.html" if path == "/" else path.lstrip("/"))
        print(f"{response.status} {len(response.body):>8} {path}")
        if response.status != 200:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.body)
        saved += 1
        if path.lower().endswith(".jar"):
            continue
        text = response.text
        for ref in (*LINK_RE.findall(text), *STRING_REF_RE.findall(text)):
            resolved = urlsplit(urljoin(path, ref)).path
            normalized = posixpath.normpath(resolved)
            if (
                normalized.lower().endswith(STATIC_SUFFIXES)
                and normalized.startswith("/console-carel/")
                and normalized.lower() not in seen
            ):
                queue.append(normalized)
    print(f"saved {saved} files to {out_dir}")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    """Run one probe command."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("command", choices=("console", "dump"))
    args = parser.parse_args()
    # Turn SIGTERM (e.g. from `timeout`) into SystemExit so the logout still runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    display = Display(args.host)
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d")
    with exclusive():
        if args.command == "console":
            run_console(display, CAPTURES / "console")
            return 0
        with session(display, args.username, args.password):
            run_dump(display, CAPTURES / f"{stamp}_full_dump")
    return 0


if __name__ == "__main__":
    sys.exit(main())
