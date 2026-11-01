"""Live research sessions from research/protocol.md §7. Only the lead runs them.

Every request goes through orca_probe's allowlisted transport. A session is one
login: its steps run serially, every raw response is saved under
research/captures/, and the logout runs in a ``finally``. Any unexpected answer
stops the session. protocol.md §7.5 (several sessions at once) is deliberately
missing: it breaks the one-session rule of PLAN.md §2.2.

Usage (from the repository root):
  python -m tools.orca_research --host HOST session1
"""

import argparse
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
import http.client
import json
from pathlib import Path
import re
import signal
import sys
import time
from typing import Any
from urllib.parse import quote

from tools import orca_probe as probe
from tools.orca_probe import Display, ProbeError, Record, Response

FIXTURE = (
    probe.ROOT / "tests" / "fixtures" / "dumps" / "schema23_duo300solar_2026-10-31.json"
)
BASELINE = [
    "2_Temp_vode_sanitarna",
    "2_Rezim_MK1",
    "2_Temp_Zunanja",
    "2_SV_vklop",
    "2_Temp_RF2",
    "2_NAPAKA",
    "MK1_IME(2)",
    "2_CURRENT_SECOND",
]
METADATA_TAGS = ["2_Temp_vode_sanitarna", "2_Rezim_MK1", "2_Temp_Zunanja", "2_SV_vklop"]
# Header-block sizes seen on 2026-10-31 (request line + headers, as sent).
LAST_OK_HEADER = 4051
FIRST_408_HEADER = 4479
# protocol.md §5: the server's 4,096-byte buffer holds at most 4,095 bytes.
PREDICTED_MAX_HEADER = 4095
SAFE_HEADER_BUDGET = 3900
# A 408 slower than this is a real timeout, not the buffer limit.
INSTANT_SECONDS = 2.0
RELIABILITY_PASSES = 10
TIMING_SIZES = (25, 50, 100)
TIMING_REPEATS = 3
# R14 (protocol.md §7.3): the project folder found over FTP by orca-energy-ha's
# author, in the three path forms the server might expect.
CONFIG_DIRS = (
    "workspace/Project/config/",
    "/workspace/Project/config/",
    "\\workspace\\Project\\config\\",
)
# E_FILEOPENFAIL: seen 2026-11-01 for a directory path; the path is not a file.
EXPECTED_FILE_ERRORS = (
    "#E_FAIL",
    "#E_INVALIDARG",
    "#E_READFORBIDDEN",
    "#E_FILEOPENFAIL",
)
READFILE_OUT = probe.CAPTURES / "readfile"
# R1 (protocol.md §7.4): probe every 2 min for 20 min, then wait longer and longer.
KEEPALIVE_PROBES = 10
KEEPALIVE_INTERVAL = 120
IDLE_GAPS_MINUTES = (3, 5, 8, 12, 17, 23, 30)


class StepError(ProbeError):
    """The display answered a step unexpectedly; the session stops."""


@dataclass
class Recorder:
    """Saves raw responses and a step log for one session."""

    out: Path
    results: dict[str, Any] = field(default_factory=dict)

    def save(self, step: str, response: Response, note: str = "") -> Response:
        """Save a raw response and log the step."""
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / f"{step}.txt").write_bytes(response.body)
        entry = {
            "step": step,
            "time": _now(),
            "status": response.status,
            "header_bytes": response.header_bytes,
            "bytes": len(response.body),
            "seconds": response.seconds,
            "headers": response.headers,
            "head": response.text[:160],
            "note": note,
        }
        with (self.out / "steps.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(
            f"{step}: HTTP {response.status}, {len(response.body)} B,"
            f" {response.seconds} s, header {response.header_bytes} B {note}"
        )
        return response

    def write_results(self) -> None:
        """Write the session's structured results."""
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "results.json").write_text(
            json.dumps(self.results, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def answered(step: str, response: Response) -> Response:
    """Accept HTTP 200 or a CGI error on HTTP 500; anything else stops."""
    if response.status not in (200, 500):
        raise StepError(f"{step}: unexpected HTTP {response.status}")
    return response


def readable_tags() -> list[str]:
    """Tags that read S_OK on our pump, minus password and code tags."""
    tags: dict[str, dict[str, str]] = json.loads(FIXTURE.read_text(encoding="utf-8"))[
        "tags"
    ]
    return [
        tag
        for tag, record in tags.items()
        if record["status"] == "S_OK" and not probe.SECRET_TAG_RE.search(tag)
    ]


def budget_batches(
    display: Display, tags: list[str], budget: int
) -> Iterator[list[str]]:
    """Split tags into readTags batches whose header block fits the budget."""
    batch: list[str] = []
    for tag in tags:
        query = probe.read_tags_query([*batch, tag])
        if batch and display.header_size("GET", "/cgi/readTags", query) > budget:
            yield batch
            batch = []
        batch.append(tag)
    if batch:
        yield batch


def exact_fill(
    display: Display, tags: list[str], target: int, extra: int = 0
) -> list[str]:
    """Choose tags so that a readTags header block is exactly ``target`` bytes.

    ``extra`` reserves bytes for additional headers sent with the request.
    """

    def size(chosen: list[str]) -> int:
        query = probe.read_tags_query(chosen)
        return display.header_size("GET", "/cgi/readTags", query) + extra

    chosen: list[str] = []
    for tag in tags:
        if size([*chosen, tag]) > target - 45:
            break
        chosen.append(tag)
    rest = [tag for tag in tags if tag not in chosen]
    by_length: dict[int, list[str]] = {}
    for tag in rest:
        by_length.setdefault(len(tag), []).append(tag)
    gap = target - size(chosen)
    for count in (1, 2, 3):
        for combo in _fillers(rest, by_length, count, len(chosen) + 1, gap):
            if size([*chosen, *combo]) == target:
                return [*chosen, *combo]
    raise ProbeError(f"no tag combination reaches exactly {target} bytes")


def _fillers(
    rest: list[str],
    by_length: dict[int, list[str]],
    count: int,
    position: int,
    gap: int,
    used: frozenset[str] = frozenset(),
) -> Iterator[tuple[str, ...]]:
    """Yield ``count`` distinct tags whose ``&t<n>=<tag>`` parts add up to gap."""
    prefix = len(f"&t{position}=")
    if count == 1:
        for tag in by_length.get(gap - prefix, []):
            if tag not in used:
                yield (tag,)
        return
    for tag in rest:
        if tag in used:
            continue
        for more in _fillers(
            rest,
            by_length,
            count - 1,
            position + 1,
            gap - prefix - len(tag),
            used | {tag},
        ):
            yield (tag, *more)


def _statuses(records: dict[str, Record]) -> dict[str, str]:
    return {tag: record.status for tag, record in records.items()}


def browse(
    display: Display,
    rec: Recorder,
    step: str,
    where: str,
    has_value: str,
    return_object: bool,
    max_result: int = 1000,
    max_pages: int = 3,
    max_page_seconds: float | None = None,
    method: str = "GET",
) -> tuple[str, list[str]]:
    """Run a browse query with paging; return the status line and the items."""
    items: list[str] = []
    status_line = ""
    cont = ""
    for page in range(1, max_pages + 1):
        form = (
            f"maxWait=10000&maxResult={max_result}&where={where}"
            f"&hasValue={quote(has_value, safe='*.')}&contPt={quote(cont, safe='')}"
            f"&returnObject={'true' if return_object else 'false'}"
        )
        response = answered(
            step,
            display.post("/cgi/browse", form)
            if method == "POST"
            else display.get("/cgi/browse", form),
        )
        lines = response.text.replace("\r", "").split("\n")
        status_line = lines[0].strip()
        rec.save(f"{step}_p{page}", response, status_line)
        if status_line != "#S_OK":
            break
        header = lines[1].split("\t") if len(lines) > 1 else []
        items += [line for line in lines[2:] if line]
        cont = header[1] if len(header) > 1 else ""
        if not cont or (max_page_seconds and response.seconds > max_page_seconds):
            break
    return status_line, items


def query_list(prefix: str, names: list[str]) -> str:
    """Build ``n=<k>&<prefix>1=<name>…`` with names percent-encoded."""
    return f"n={len(names)}" + "".join(
        f"&{prefix}{index}={quote(name, safe='()_-.')}"
        for index, name in enumerate(names, 1)
    )


def named_batches(
    display: Display, path: str, prefix: str, names: list[str], budget: int
) -> Iterator[str]:
    """Split names into queries for ``path`` whose header block fits the budget."""
    batch: list[str] = []
    for name in names:
        query = query_list(prefix, [*batch, name])
        if batch and display.header_size("GET", path, query) > budget:
            yield query_list(prefix, batch)
            batch = []
        batch.append(name)
    if batch:
        yield query_list(prefix, batch)


def limit_probe(
    display: Display,
    rec: Recorder,
    step: str,
    tags: list[str],
    target: int,
    pad: int = 0,
) -> bool:
    """Send a readTags header block of exactly ``target`` bytes.

    Return True for a complete answer and False for an instant 408; anything
    else stops the session. ``pad`` moves that many bytes from the request line
    into an extra header.
    """
    extra = {"X-Pad": "a" * (pad - len("X-Pad: ") - 2)} if pad else {}
    chosen = exact_fill(display, tags, target, extra=pad)
    query = probe.read_tags_query(chosen)
    response = display.get("/cgi/readTags", query, extra_headers=extra)
    if response.header_bytes != target:
        raise StepError(f"{step}: sent {response.header_bytes} B, meant {target}")
    records = probe.parse_records(response.text)
    complete = response.status == 200 and list(records) == chosen
    instant_408 = response.status == 408 and response.seconds < INSTANT_SECONDS
    rec.save(
        step,
        response,
        f"target={target} pad={pad} tags={len(chosen)}"
        f" {'complete' if complete else '408' if instant_408 else 'UNEXPECTED'}",
    )
    if not complete and not instant_408:
        raise StepError(f"{step}: neither complete nor an instant 408")
    return complete


def run_limits(display: Display, rec: Recorder, tags: list[str]) -> None:
    """S1-25…27: where exactly does the display answer 408 (R11)?"""
    ok = {LAST_OK_HEADER}
    failed = {FIRST_408_HEADER}
    for step, target in (
        ("S1-25", PREDICTED_MAX_HEADER),
        ("S1-26", PREDICTED_MAX_HEADER + 1),
    ):
        (
            ok if limit_probe(display, rec, f"{step}_limit", tags, target) else failed
        ).add(target)
    probes = 0
    while min(failed) - max(ok) > 1 and probes < 5:
        target = (max(ok) + min(failed)) // 2
        probes += 1
        (
            ok
            if limit_probe(display, rec, f"S1-26b{probes}_limit", tags, target)
            else failed
        ).add(target)
    rec.results["limit_max_ok_header_bytes"] = max(ok)
    rec.results["limit_min_408_header_bytes"] = min(failed)
    # Over the limit in total, but with 109 bytes moved into a header so the
    # request line is short: a 408 means the limit is on the whole header block.
    rec.results["limit_counts_headers"] = not limit_probe(
        display, rec, "S1-27_header_pad", tags, min(failed) + 18, pad=109
    )


def run_timing(display: Display, rec: Recorder, tags: list[str]) -> None:
    """S1-28…39: latency per batch size (R11)."""
    timing: dict[str, list[float]] = {}
    for repeat in range(TIMING_REPEATS):
        pool = tags[repeat * 30 :] + tags[: repeat * 30]
        largest = next(budget_batches(display, pool, SAFE_HEADER_BUDGET))
        for batch in (*(pool[:size] for size in TIMING_SIZES), largest):
            key = "max" if batch is largest else str(len(batch))
            response, records = probe.read_tags(display, batch)
            rec.save(
                f"S1-timing_{key}_{repeat + 1}", response, f"{len(records)} records"
            )
            if response.status != 200 or list(records) != batch:
                raise StepError(f"timing {key}: incomplete answer")
            timing.setdefault(key, []).append(response.seconds)
            if key == "max":
                timing.setdefault("max_tags", []).append(len(batch))
    rec.results["timing_seconds"] = timing


def run_reliability(display: Display, rec: Recorder, tags: list[str]) -> None:
    """S1-50…89: repeated full reads; do records ever go missing (R11)?"""
    batches = list(budget_batches(display, tags, SAFE_HEADER_BUDGET))
    first: dict[str, str | None] = {}
    passes: list[dict[str, Any]] = []
    for number in range(1, RELIABILITY_PASSES + 1):
        summary: dict[str, Any] = {
            "missing": [],
            "extra": [],
            "out_of_order_batches": 0,
            "not_ok": {},
            "http": [],
            "seconds": [],
        }
        values: dict[str, str | None] = {}
        for index, batch in enumerate(batches, 1):
            response, records = probe.read_tags(display, batch)
            rec.save(f"S1-rel_{number:02}_{index}", response)
            summary["http"].append(response.status)
            summary["seconds"].append(response.seconds)
            if response.status != 200:
                raise StepError(f"reliability pass {number}: HTTP {response.status}")
            summary["missing"] += [tag for tag in batch if tag not in records]
            summary["extra"] += [tag for tag in records if tag not in batch]
            if [tag for tag in records if tag in batch] != [
                tag for tag in batch if tag in records
            ]:
                summary["out_of_order_batches"] += 1
            summary["not_ok"] |= {
                tag: record.status
                for tag, record in records.items()
                if record.status != "S_OK"
            }
            values |= {tag: record.value for tag, record in records.items()}
        if number == 1:
            first = values
        summary["changed_vs_pass1"] = sorted(
            tag for tag, value in values.items() if first.get(tag) != value
        )
        passes.append(summary)
        print(
            f"pass {number}: {len(summary['missing'])} missing,"
            f" {len(summary['changed_vs_pass1'])} changed"
        )
    rec.results["reliability"] = {
        "batches_per_pass": len(batches),
        "tags": len(tags),
        "passes": passes,
    }


def session1(display: Display, rec: Recorder) -> None:
    """Discovery, R2/R3/R4/R11 (protocol.md §7.2, without S1-38/39)."""
    tags = readable_tags()

    response, records = probe.read_tags(display, BASELINE)
    rec.save("S1-02_baseline", response, f"order={list(records) == BASELINE}")
    if response.status != 200 or set(records) != set(BASELINE):
        raise StepError("S1-02: baseline not as expected")
    rec.results["readtags_in_request_order"] = list(records) == BASELINE

    response, other = probe.read_tags(display, BASELINE, client=None)
    rec.results["client_param_ignored"] = _statuses(other) == _statuses(records)
    rec.save("S1-03_no_client", response, f"same={rec.results['client_param_ignored']}")

    response = display.post("/cgi/readTags", probe.read_tags_query(BASELINE, None))
    other = probe.parse_records(response.text)
    rec.results["post_equivalent"] = _statuses(other) == _statuses(records)
    rec.save("S1-04_post", response, f"same={rec.results['post_equivalent']}")

    for step, endpoint in (
        ("S1-05", "getTCPIPSettings"),
        ("S1-06", "getPLCStatus"),
        ("S1-07", "getTime"),
        ("S1-08", "getLocalTime"),
        ("S1-09", "getDLSSettings"),
    ):
        rec.save(f"{step}_{endpoint}", answered(step, display.get(f"/cgi/{endpoint}")))

    status, alarms = browse(display, rec, "S1-10_alarms", "alarmName", "*", False)
    if status == "#E_INVALIDARG":
        status, alarms = browse(
            display, rec, "S1-10b_alarms_post", "alarmName", "*", False, method="POST"
        )
    elif status == "#E_NO_OBJECTS_FOUND":
        status, alarms = browse(display, rec, "S1-10c_alarms", "alarmName", ".*", False)
    rec.results["alarm_names"] = alarms
    if alarms:
        _, objects = browse(display, rec, "S1-11_alarm_objects", "alarmName", "*", True)
        rec.results["alarm_objects_lines"] = len(objects)
        states: list[str] = []
        for index, query in enumerate(
            named_batches(display, "/cgi/readAlarms", "al", alarms, 3600), 1
        ):
            response = answered("S1-12", display.get("/cgi/readAlarms", query))
            rec.save(f"S1-12_readAlarms_{index}", response)
            states += [
                line for line in response.text.split("\n") if line.startswith("#")
            ]
        rec.results["alarm_states_lines"] = len(states)

    for index, tag in enumerate(METADATA_TAGS, 13):
        browse(
            display, rec, f"S1-{index}_meta_{tag}", "tagName", tag, True, max_result=10
        )

    _, groups = browse(display, rec, "S1-17_groups", "groupName", "*", False)
    _, trends = browse(display, rec, "S1-18_trends", "trendName", "*", False)
    browse(display, rec, "S1-19_protocols", "protocolName", "*", True)
    rec.results["groups"] = groups
    rec.results["trends"] = trends

    _, page1 = browse(display, rec, "S1-20_paging", "tagName", "*", False, 100, 1)
    _, both = browse(display, rec, "S1-21_paging", "tagName", "*", False, 100, 2)
    rec.results["paging_works"] = len(both) > len(page1) and not (
        set(both[len(page1) :]) & set(page1)
    )
    _, all_tags = browse(
        display, rec, "S1-22_all_tags", "tagName", "*", False, 1000, 5, 10.0
    )
    rec.results["browse_tag_count"] = len(all_tags)
    (rec.out / "browse_tag_names.txt").write_text(
        "\n".join(all_tags) + "\n", encoding="utf-8"
    )

    if groups:
        query = query_list("gr", groups[:3])
        rec.save(
            "S1-23_readGroups", answered("S1-23", display.get("/cgi/readGroups", query))
        )
    if trends:
        now = int(time.time())
        query = (
            f"tr={quote(trends[0], safe='')}&returnTS=true&returnRT=false"
            f"&iso8601TS=false&startTime={now - 86400}&endTime={now}"
            "&deltaTime=0.0&nSamples=20&bounds=false"
        )
        rec.save(
            "S1-24_readTrend", answered("S1-24", display.get("/cgi/readTrend", query))
        )

    run_limits(display, rec, tags)
    run_timing(display, rec, tags)
    run_reliability(display, rec, tags)

    token = display.token
    logged_out = probe.logout(display)
    if logged_out is not None:
        rec.save("S1-90_logout", logged_out)
    # R1: what a dead token, a second logout and no token at all return.
    display.token = token
    rec.save(
        "S1-91_stale_token_read",
        display.get("/cgi/readTags", "n=1&t1=2_CURRENT_SECOND"),
    )
    rec.save("S1-92_stale_token_logout", display.get("/cgi/logout"))
    display.token = None
    rec.save(
        "S1-93_no_token_read", display.get("/cgi/readTags", "n=1&t1=2_CURRENT_SECOND")
    )


def config_files(config_dir: str) -> list[str]:
    """R14 files for one path form: the folder itself, then named files."""
    sep = "\\" if config_dir.startswith("\\") else "/"
    project = config_dir.removesuffix(f"config{sep}")
    return [
        f"{config_dir}alarms.xml",
        config_dir,
        f"{project}Page109.jmx",
        f"{config_dir}eventconfig.xml",
        f"{config_dir}propertymap.xml",
        # trends.xml is skipped: session 1 found no trends on the display.
        f"{config_dir}groups.xml",
    ]


def read_one_file(display: Display, rec: Recorder, step: str, path: str) -> bool:
    """Read one R14 file; return True if it came back, False on an expected error.

    Anything unexpected stops the session (PLAN.md §2.2: stop at the first
    unexpected error).
    """
    response = display.read_file(path)
    if response.text.startswith("#E_INVALIDARG"):
        rec.save(f"{step}_get", response, path)
        response = display.read_file(path, method="POST")
    lines = response.text.replace("\r", "").split("\n")
    first = lines[0].strip()
    note = path
    sized = len(lines) > 1 and lines[1].strip().isdigit()
    if response.status in (200, 500) and first == "#S_OK" and sized:
        content = "\n".join(lines[2:])
        note += f" size={lines[1]} received={len(content.encode())}"
        target = READFILE_OUT / path.replace("\\", "/").lstrip("/")
        if path.endswith(("/", "\\")):
            target = target / "_directory.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.body)
        rec.save(step, response, note)
        return True
    rec.save(step, response, note)
    if (
        response.status in (200, 500)
        and first in EXPECTED_FILE_ERRORS
        and len([line for line in lines if line.strip()]) == 1
    ):
        return False
    raise StepError(f"{step}: unexpected readFile answer {first[:60]!r}")


def last_token() -> str | None:
    """The token of the previous session's login, from the request log."""
    token = None
    with probe.REQUEST_LOG.open(encoding="utf-8") as log:
        for line in log:
            entry = json.loads(line)
            if entry["path"] == "/cgi/login" and (
                found := re.search(r"IDALToken=(\w+)", entry["head"])
            ):
                token = found.group(1)
    return token


def session2a(display: Display, rec: Recorder, username: str, password: str) -> None:
    """R1 re-login with a stale cookie, then the fixed R14 readFile list."""
    display.token = last_token()
    response = display.get("/cgi/login", f"username={username}&password={password}")
    rec.save("S2-01_login_stale_cookie", response)
    if found := re.search(r"IDALToken=(\w+)", response.text):
        display.token = found.group(1)
    else:
        check = display.get("/cgi/readTags", "n=1&t1=2_CURRENT_SECOND")
        rec.save("S2-01b_stale_cookie_read", check)
        display.token = None
        probe.login(display, username, password)
    response, records = probe.read_tags(display, ["2_CURRENT_SECOND"])
    rec.save("S2-02_sanity", response)
    if records.get("2_CURRENT_SECOND", Record("", None, None)).status != "S_OK":
        raise StepError("S2-02: session not usable")

    found_dir = None
    for index, config_dir in enumerate(CONFIG_DIRS, 3):
        if read_one_file(
            display, rec, f"S2-{index:02}_alarms", f"{config_dir}alarms.xml"
        ):
            found_dir = config_dir
            break
    rec.results["config_dir"] = found_dir
    if found_dir is None:
        rec.results["r14"] = "alarms.xml not found in any path form; ask the user"
        return
    results: dict[str, bool] = {}
    for index, path in enumerate(config_files(found_dir)[1:], 6):
        results[path] = read_one_file(display, rec, f"S2-{index:02}_file", path)
    rec.results["files"] = results


def session2b(display: Display, rec: Recorder, files: list[str]) -> None:
    """R14 follow-up: read files named on the command line, one by one."""
    results: dict[str, bool] = {}
    rec.results["files"] = results
    for index, path in enumerate(files, 1):
        results[path] = read_one_file(display, rec, f"S2b-{index:02}_file", path)


def session_meta(display: Display, rec: Recorder) -> None:
    """R2: every tag definition (register kind and data type) via browse."""
    status, items = browse(
        display, rec, "S4-01_tag_objects", "tagName", "*", True, 500, 4, 10.0
    )
    rec.results["status"] = status
    rec.results["object_lines"] = len(items)


def session_snapshot(display: Display, rec: Recorder) -> None:
    """One read of every readable tag, e.g. to compare timer-on and timer-off (R8)."""
    values: dict[str, str | None] = {}
    for index, batch in enumerate(
        budget_batches(display, readable_tags(), SAFE_HEADER_BUDGET), 1
    ):
        response, records = probe.read_tags(display, batch)
        rec.save(f"S5-{index:02}_snapshot", response)
        if response.status != 200 or list(records) != batch:
            raise StepError(f"snapshot batch {index}: incomplete answer")
        values |= {tag: record.value for tag, record in records.items()}
    rec.results["time"] = _now()
    rec.results["values"] = values


def session3(display: Display, rec: Recorder) -> None:
    """R1: do reads keep a session alive, and when does an idle one expire?"""
    start = time.monotonic()
    timeline: list[dict[str, Any]] = []
    rec.results["timeline"] = timeline

    def alive(step: str) -> bool:
        response = display.get("/cgi/readTags", "n=1&t1=2_CURRENT_SECOND")
        ok = "S_OK" in response.text and "E_NEED_LOGIN" not in response.text
        rec.save(step, response, f"t={round((time.monotonic() - start) / 60, 1)} min")
        timeline.append({"step": step, "time": _now(), "alive": ok})
        return ok

    if not alive("S3-02_t0"):
        raise StepError("S3: session dead right after login")
    for index in range(1, KEEPALIVE_PROBES + 1):
        time.sleep(KEEPALIVE_INTERVAL)
        if not alive(f"S3-keepalive_{index:02}"):
            rec.results["keepalive"] = f"expired after {index * 2} min of 2-min reads"
            return
    rec.results["keepalive"] = "alive after 20 min of reads every 2 min"
    previous = None
    for gap in IDLE_GAPS_MINUTES:
        time.sleep(gap * 60)
        if not alive(f"S3-idle_{gap:02}min"):
            rec.results["idle_timeout"] = f"between {previous} and {gap} min"
            return
        previous = gap
    rec.results["idle_timeout"] = f"over {previous} min"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    """Run one research session."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--out", type=Path, help="output folder (dry runs)")
    parser.add_argument("--health-wait", type=int, default=300)
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="session2b: a file to read (repeat; each must be justified)",
    )
    parser.add_argument(
        "session",
        choices=("session1", "session2a", "session2b", "session3", "meta", "snapshot"),
    )
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    display = Display(
        args.host,
        port=args.port,
        readfile_paths=frozenset(
            args.file
            if args.session == "session2b"
            else [
                path for config_dir in CONFIG_DIRS for path in config_files(config_dir)
            ]
        ),
    )
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d")
    out = args.out or probe.CAPTURES / f"{stamp}_research"
    if args.out:
        probe.REQUEST_LOG = args.out / "requests.jsonl"
    rec = Recorder(out / args.session)
    failed = False
    with probe.exclusive():
        try:
            if args.session == "session2a":
                try:
                    session2a(display, rec, args.username, args.password)
                finally:
                    probe.logout(display)
            else:
                with probe.session(display, args.username, args.password):
                    if args.session == "session1":
                        session1(display, rec)
                    elif args.session == "session2b":
                        session2b(display, rec, args.file)
                    elif args.session == "meta":
                        session_meta(display, rec)
                    elif args.session == "snapshot":
                        session_snapshot(display, rec)
                    else:
                        session3(display, rec)
        except (ProbeError, OSError, http.client.HTTPException) as err:
            failed = True
            rec.results["stopped"] = repr(err)
            print(f"{_now()} STOPPED: {err!r}")
        finally:
            rec.write_results()
        if failed:
            # protocol.md §7.1: wait, then one health check without logging in.
            time.sleep(args.health_wait)
            health = display.get("/")
            print(f"{_now()} health check: HTTP {health.status}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
