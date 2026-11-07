"""Requests and responses of the display's IDAL CGI API, as pure functions."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
import re
from typing import Final
from urllib.parse import quote

from .errors import (
    OrcaAuthError,
    OrcaProtocolError,
    OrcaSessionExpiredError,
    OrcaTooManyUsersError,
)

LOGIN: Final = "/cgi/login"
LOGOUT: Final = "/cgi/logout"
READ_TAGS: Final = "/cgi/readTags"
WRITE_TAGS: Final = "/cgi/writeTags"

# The display answers HTTP 408 when the request line and headers exceed 4,095
# bytes (research R11). HTTP clients add a few hundred bytes of headers, so
# request targets stay well below that.
MAX_TARGET_BYTES: Final = 3500

STATUS_OK: Final = "S_OK"
STATUS_UNKNOWN_TAG: Final = "E_UNKNOWNTAG"
NOT_CONNECTED: Final = "-9999"

_TOKEN_RE: Final = re.compile(r"IDALToken=(\w+)")
# A whole-response error is a line holding only the code; records carry a tab.
_WHOLE_ERROR_RE: Final = re.compile(r"^#(E_[A-Z0-9_-]+)[ \t\r]*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Record:
    """One tag record of a readTags or writeTags response."""

    tag: str
    status: str
    quality: int | None = None
    value: str | None = None


def _encode(text: str) -> str:
    return quote(text, safe="()")


def login_target(username: str, password: str) -> str:
    """Return the request target that logs in."""
    return f"{LOGIN}?username={_encode(username)}&password={_encode(password)}"


def read_target(tags: Sequence[str]) -> str:
    """Return the request target that reads tags."""
    return f"{READ_TAGS}?n={len(tags)}" + "".join(
        f"&t{index}={_encode(tag)}" for index, tag in enumerate(tags, 1)
    )


def write_target(tag: str, raw: int) -> str:
    """Return the request target that writes one raw value."""
    return f"{WRITE_TAGS}?n=1&t1={_encode(tag)}&v1={raw}"


def read_batches(
    tags: Sequence[str], max_bytes: int = MAX_TARGET_BYTES
) -> Iterator[list[str]]:
    """Split tags into readTags batches whose target fits in ``max_bytes``."""
    fixed = len(f"{READ_TAGS}?n=")
    batch: list[str] = []
    size = 0
    for tag in tags:
        part = len(f"&t{len(batch) + 1}={_encode(tag)}")
        if batch and fixed + len(str(len(batch) + 1)) + size + part > max_bytes:
            yield batch
            batch, size = [], 0
            part = len(f"&t1={_encode(tag)}")
        if not batch and fixed + 1 + part > max_bytes:
            raise ValueError(f"tag name too long for one request: {tag}")
        batch.append(tag)
        size += part
    if batch:
        yield batch


def raise_for_error(text: str) -> None:
    """Raise if the response is a whole-response error such as E_NEED_LOGIN."""
    if (match := _WHOLE_ERROR_RE.search(text)) is None:
        return
    code = match.group(1)
    if code == "E_NEED_LOGIN":
        raise OrcaSessionExpiredError(code)
    if code == "E_TOO_MANY_USERS":
        raise OrcaTooManyUsersError(code)
    if code in ("E_PASS_DONT_MATCH", "E_USER_DONT_EXIST"):
        raise OrcaAuthError(code)
    raise OrcaProtocolError(code)


def parse_login(text: str) -> str:
    """Return the session token of a login response."""
    if match := _TOKEN_RE.search(text):
        return match.group(1)
    raise_for_error(text)
    raise OrcaProtocolError(f"unexpected login response: {text.strip()[:80]!r}")


def parse_write_status(text: str, tag: str) -> str | None:
    """Return the status a writeTags response gives for a tag, if it gives one.

    Reads nothing else: a surprise here must not fail a write that landed, and
    the read back decides. The real display answers like a read record.
    """
    raise_for_error(text)
    for line in text.replace("\r", "").split("\n"):
        name, sep, status = line.removeprefix("#").partition("\t")
        if line.startswith("#") and sep and name == tag:
            return status.strip()
    return None


def parse_records(text: str) -> list[Record]:
    r"""Parse ``#<tag>\t<status>\n<quality>\t<value>`` records, in order.

    Records with a status other than S_OK have no value line.
    """
    raise_for_error(text)
    lines = text.replace("\r", "").split("\n")
    records: list[Record] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.startswith("#"):
            continue
        tag, sep, status = line[1:].partition("\t")
        status = status.strip()
        if not sep or not tag or not status:
            raise OrcaProtocolError(f"malformed record: {line[:80]!r}")
        if status != STATUS_OK:
            records.append(Record(tag, status))
            continue
        payload = lines[index] if index < len(lines) else ""
        quality, sep, value = payload.partition("\t")
        if not sep or not quality.strip().isdecimal():
            raise OrcaProtocolError(f"record {tag} has no value line")
        index += 1
        records.append(Record(tag, status, int(quality), value))
    return records
