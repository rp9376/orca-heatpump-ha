"""Tests for request building and response parsing."""

import contextlib
import json
from pathlib import Path
import string

from hypothesis import given, strategies as st
import pytest

from custom_components.orca_heatpump.client.errors import (
    OrcaAuthError,
    OrcaError,
    OrcaProtocolError,
    OrcaSessionExpiredError,
    OrcaTooManyUsersError,
)
from custom_components.orca_heatpump.client.protocol import (
    MAX_TARGET_BYTES,
    Record,
    login_target,
    parse_login,
    parse_records,
    parse_write_status,
    raise_for_error,
    read_batches,
    read_target,
    write_target,
)

FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "dumps"
    / "schema23_duo300solar_2026-11-01_heating.json"
)
TAG_NAME = st.text(
    alphabet=string.ascii_letters + string.digits + "_()", min_size=1, max_size=36
)


def test_targets() -> None:
    """Targets carry the parameters the display expects, tag names intact."""
    assert login_target("admin", "p&ss w") == (
        "/cgi/login?username=admin&password=p%26ss%20w"
    )
    assert read_target(["2_Poti1", "MK1_IME(2)"]) == (
        "/cgi/readTags?n=2&t1=2_Poti1&t2=MK1_IME(2)"
    )
    assert write_target("2_Max_VF_MK1", 280) == (
        "/cgi/writeTags?n=1&t1=2_Max_VF_MK1&v1=280"
    )


def test_read_batches_real_tags() -> None:
    """All 694 readable tags of our pump fit in a few requests under the limit."""
    tags = list(json.loads(FIXTURE.read_text(encoding="utf-8"))["tags"])

    batches = list(read_batches(tags))

    assert [tag for batch in batches for tag in batch] == tags
    assert all(len(read_target(batch)) <= MAX_TARGET_BYTES for batch in batches)
    assert len(batches) == 5


@given(tags=st.lists(TAG_NAME, max_size=300), max_bytes=st.integers(80, 4000))
def test_read_batches_property(tags: list[str], max_bytes: int) -> None:
    """Batches keep every tag in order and never exceed the byte budget."""
    batches = list(read_batches(tags, max_bytes))

    assert [tag for batch in batches for tag in batch] == tags
    assert all(len(read_target(batch)) <= max_bytes for batch in batches)
    assert all(batches)


def test_read_batches_rejects_huge_tag() -> None:
    """A tag that can never fit is a programming error."""
    with pytest.raises(ValueError, match="too long"):
        list(read_batches(["x" * 100], max_bytes=50))


@pytest.mark.parametrize(
    ("text", "error"),
    [
        pytest.param("#E_NEED_LOGIN\n", OrcaSessionExpiredError, id="need_login"),
        pytest.param("-37\n#E_TOO_MANY_USERS", OrcaTooManyUsersError, id="too_many"),
        pytest.param("-45\n#E_PASS_DONT_MATCH", OrcaAuthError, id="password"),
        pytest.param("-49\n#E_USER_DONT_EXIST", OrcaAuthError, id="username"),
        pytest.param("#E_RE-LOGIN_ATTEMPT\n", OrcaProtocolError, id="relogin"),
        pytest.param("#E_FAIL\n", OrcaProtocolError, id="fail"),
    ],
)
def test_whole_response_errors(text: str, error: type[OrcaError]) -> None:
    """Whole-response error codes map to typed exceptions."""
    with pytest.raises(error):
        parse_records(text)


def test_parse_login() -> None:
    """The token comes from the body; errors are typed."""
    assert parse_login("1\n#S_OK\nIDALToken=" + "ab12" * 8) == "ab12" * 8
    with pytest.raises(OrcaTooManyUsersError):
        parse_login("#E_TOO_MANY_USERS\n")
    with pytest.raises(OrcaProtocolError, match="unexpected login"):
        parse_login("<html>hello</html>")


def test_parse_records() -> None:
    """Records come back in order, with and without value lines."""
    text = (
        "#2_Temp_Zunanja\tS_OK\r\n192\t-35\r\n"
        "#2_NAPAKA\tE_UNKNOWNTAG\n"
        "#2_Empty\tS_OK\n192\t\n"
        "#MK1_IME(2)\tS_OK\n192\t15\n"
    )

    assert parse_records(text) == [
        Record("2_Temp_Zunanja", "S_OK", 192, "-35"),
        Record("2_NAPAKA", "E_UNKNOWNTAG"),
        Record("2_Empty", "S_OK", 192, ""),
        Record("MK1_IME(2)", "S_OK", 192, "15"),
    ]


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("#2_Poti1\n192\t1\n", id="no_tab"),
        pytest.param("#\tS_OK\n192\t1\n", id="no_tag"),
        pytest.param("#2_Poti1\tS_OK\n", id="no_value_line"),
        pytest.param("#2_Poti1\tS_OK\nxx\t1\n", id="bad_quality"),
        pytest.param("#2_Poti1\tS_OK\n#2_Poti2\tS_OK\n192\t1\n", id="next_record"),
    ],
)
def test_parse_records_malformed(text: str) -> None:
    """Malformed records raise a protocol error instead of guessing."""
    with pytest.raises(OrcaProtocolError):
        parse_records(text)


@given(
    st.lists(
        st.tuples(
            TAG_NAME,
            st.sampled_from(["S_OK", "E_UNKNOWNTAG", "E_READFORBIDDEN"]),
            st.integers(0, 255),
            st.from_regex(r"-?[0-9]{0,6}", fullmatch=True),
        ),
        max_size=50,
    )
)
def test_parse_records_roundtrip(
    items: list[tuple[str, str, int, str]],
) -> None:
    """Whatever the display sends in its format parses back exactly."""
    text = "".join(
        f"#{tag}\t{status}\n" + (f"{quality}\t{value}\n" if status == "S_OK" else "")
        for tag, status, quality, value in items
    )

    assert parse_records(text) == [
        Record(tag, status, quality, value) if status == "S_OK" else Record(tag, status)
        for tag, status, quality, value in items
    ]


@given(st.text())
def test_parse_records_never_crashes(text: str) -> None:
    """Arbitrary bodies either parse or raise an Orca error, nothing else."""
    with contextlib.suppress(OrcaError):
        parse_records(text)


@pytest.mark.parametrize(
    ("text", "status"),
    [
        pytest.param("#tag\tS_OK\n192\t1\n", "S_OK", id="full_record"),
        pytest.param("#tag\tS_OK\n", "S_OK", id="status_only"),
        pytest.param("#tag\tE_WRITEFORBIDDEN\r\n", "E_WRITEFORBIDDEN", id="refused"),
        pytest.param("#other\tE_FAIL\n", None, id="other_tag"),
        pytest.param("1\n#S_OK\n", None, id="no_tag"),
        pytest.param("", None, id="empty"),
    ],
)
def test_parse_write_status(text: str, status: str | None) -> None:
    """Only a status for this tag counts; any other form says nothing."""
    assert parse_write_status(text, "tag") == status


def test_whole_error_with_crlf() -> None:
    """A whole-response error is recognised with any line ending."""
    with pytest.raises(OrcaTooManyUsersError):
        raise_for_error("#E_TOO_MANY_USERS\r\n")


def test_quality_digits_only_ascii() -> None:
    """A quality that isn't a plain number is a protocol error, not a crash."""
    with pytest.raises(OrcaProtocolError, match="no value line"):
        parse_records("#tag\tS_OK\n²\t1\n")
