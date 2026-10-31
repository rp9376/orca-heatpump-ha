# Research findings (Phase 1)

Answers to R1–R15 (`PLAN.md` §6.1), with evidence and confidence. Raw
evidence is in `research/captures/` (gitignored); `requests.jsonl` there logs
every request the probe made (time, endpoint, tag count, HTTP status, bytes,
duration).

Status: **in progress.** Sections fill in as the research proceeds.

## Live sessions so far

| When (CET) | What | Logins | Result |
|---|---|---|---|
| 2026-10-31 20:23–20:24 | Static console files (`tools/orca_probe.py console`), no login | 0 | 20 files to `captures/console/`; 2 links 404 (`style1.css`, `scripts/soapclient.js`) |
| 2026-10-31 20:24:30–20:25:02 | Full tag dump (`tools/orca_probe.py dump`), 2 passes | 1 | Login on the first attempt, logout `#S_OK`. `captures/2026-10-31_full_dump/` |

Before both, the dev HA had no `orca` or `orca_heatpump` config entry.

## First observations (2026-10-31 dump)

### Session (R1, partial)
- `GET /cgi/login?username=…&password=…` answered HTTP 200 with body
  `1\n#S_OK\nIDALToken=<32 hex>` (50 bytes) in 12 ms. No
  `E_TOO_MANY_USERS`, although the old integration's last session (entry
  disabled earlier on 2026-10-31, deleted at ~19:50) was never logged out.
- `GET /cgi/logout` with the `IDALToken` cookie answered `1\n#S_OK`. The
  console's own pages call it the same way (`logout('cgi/logout')`, success
  = body contains `#s_ok`).
- The console's login page treats `#S_OK` and `#E_RE-LOGIN_ATTEMPT` as
  success, and accepts HTTP 200 or 500 (`captures/console/root.html`).
- Open: slot count, idle timeout, whether logout frees the slot at once.

### Request limits and "missing records" (R11, partial)
- 12 batches of 150 tags per pass. **One batch failed with HTTP 408 in
  12 ms, deterministically in both passes** (an HTML "Error 408" page, no
  records). Its request line was 4,374 characters; the longest successful
  one was 3,946. The same 150 tags succeeded as 3 batches of 50 (request
  lines 1,328–1,606).
- Hypothesis (medium confidence): the server rejects request lines over
  about 4 KiB with HTTP 408. The "API drops tags" observation in
  `PLAN.md` §5.1 may be exactly this: a whole request rejected, not
  records lost at random. The client must batch by request length, not
  tag count, and treat HTTP 408 as a protocol error, not as "tags absent".
- Apart from that batch, the two passes returned identical tag sets: no
  random record loss in 2 × 1,767 tags (low confidence; one session).
- Latency: 12–94 ms per `readTags` of 150 tags (~5 KB responses).

### Tags (R2/R12 input)
- Of the 1,767 names in orca-energy-ha's `all_fields.txt`, **708 are
  `S_OK` and 1,059 are `E_UNKNOWNTAG`** on our pump, identically in both
  passes. Unknown tags come back as `#<tag>\tE_UNKNOWNTAG` with no value
  line.
- Every `S_OK` record has quality `192`.
- 5 tags read `-9999` (sensor not connected); no empty values.

### Sensitive tags (input for §10)
- No tag value on our pump holds a MAC, IP address or serial number; the
  device identity must come from elsewhere (R3).
- 12 tags contain `GESLO` (password): besides the service password and its
  timeout from `PLAN.md` §10, also `2_GESLO_PGDT`, `2_Geslo_ZAGON_AAXX`,
  `…_CCXX`, `…_XXBB`, `…_XXDD` (apparently a commissioning password in four
  parts), `2_Novo_Geslo`, `2_Potrdi_GESLO_Vklop`, `GESLO`, `Cas_GESLO` and
  the service-mode flag `2_GESLO_PGDT_Vklop`. Proposal for CP1: none of them
  is ever exposed; they are redacted in fixtures
  (`tests/fixtures/dumps/schema23_duo300solar_2026-10-31.json`).
