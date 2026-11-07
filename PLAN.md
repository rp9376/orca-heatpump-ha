# Orca heat pump integration — rewrite master plan

Status: **P0–P6 done (2026-11-07), one open point on the operating programme; P7 next; see `docs/progress.md`** · Written 2026-10-30 ·
Owner: @rp9376 (GitHub) · Domain: `orca_heatpump`

This is the brief for the lead agent (Claude Fable) that builds a new Home
Assistant integration for Orca Energy heat pumps from scratch. Read it fully
before doing anything. It tells you what to build, in which order, what you
may and may not do, and when to stop and ask the human.

**Start here:**
1. Read §2 (ground rules) twice.
2. Check `docs/progress.md` (if it exists) for where the previous session
   stopped.
3. Otherwise begin with P0 (§9).

---

## 1. Mission

Build **the last Orca integration anyone needs**: one integration that works
for every Orca heat pump with a networked touch display, for any circuit
configuration, in any language, and keeps working across Home Assistant
releases.

- **Flexible:** supports every circuit combination the pump supports: all 45
  schemas in `../Citcuit_schemas.md` (checked against the pump's own list in
  `research/moja_orca_catalog.json`), i.e. circuits 1–3 as MK or DK, hot
  water (SV), solar, buffer tank and cooling. It also supports every mode of
  operation, without hard-coded assumptions about one person's setup.
- **Bulletproof:**
  - a missing or odd value never crashes a platform
  - the pump's tiny session limit is never exhausted
  - temporary outages recover on their own
  - writes are validated and verified
- **Future-proof:**
  - follows current HA conventions and meets the integration quality scale
    (Gold, plus the applicable Platinum rules)
  - the pump protocol lives in an HA-independent client package that could
    be published to PyPI later
  - strictly typed and fully tested
  - CI runs against HA beta
- **Honest about its origins:** it is a rewrite inspired by, and partly derived
  from, [orca-energy-ha](https://github.com/Tomasinjo/orca-energy-ha) by Tom
  Kern (@Tomasinjo). Credit Tom Kern and the contributors visibly (§12).

The old integration works. Use it as a reference for tag names, value
encodings and behaviour, and fix its flaws. Do not copy its structure.

---

## 2. Ground rules (read twice)

### 2.1 Workspace
- All work stays inside `~/WorkDir/Home_Assistant_ORCA_HA/`. Never create
  files outside it. Temporary files go in your session scratchpad or in
  `orca-heatpump-ha/.scratch/` (gitignored), never in other projects.
- The new integration lives in `~/WorkDir/Home_Assistant_ORCA_HA/orca-heatpump-ha/`
  (this folder). It becomes its own git repository in Phase 0.
- Read-only references: `../orca-energy-ha/` (old integration, MIT; it has
  the user's uncommitted stop-gap work, so don't touch it), `../HAcore/` (HA
  core source, dev 2026.11), `../Citcuit_schemas.md`, `../ORCA_FIX_NOTES.md`.
  Never modify the old repo or HAcore.
- **ha-dev is yours.** The dev container and its HA instance exist only for
  this task. You may start, stop, rebuild or remove it, wipe or edit its HA
  config in `../HAcore/config/`, and delete the old Orca config entry there,
  without asking.
- Files outside this folder that you may change:
  - `../ha-dev/` scripts and their README (§4.3)
  - `../HAcore/config/` (dev HA state only, never HAcore source)
  - the workspace `../README.md`: append to its Work log, and keep its
    container docs in sync with ha-dev changes
- The user doesn't want stale leftovers. Don't keep backups or copies of old
  state unless this plan asks for them (e.g. test fixtures).

### 2.2 The heat pump is a shared, fragile, real device
- Address `192.168.178.62`, login `admin` / `admin`, plain HTTP. This is the
  user's own heating system, running a real house.
- **Only the lead agent talks to the pump. Subagents never do.** They work
  against recorded fixtures and the emulator (§7.4).
- **Session limit:** the pump allows only a few concurrent logins and answers
  `#E_TOO_MANY_USERS` when full. The old integration never logs out, so dead
  sessions linger until they time out (its log shows "Too many users.
  Retrying in 5s"). The user's Moja Orca app/web and the ha-dev Home
  Assistant also hold sessions. Rules:
  1. In P0, delete the old Orca config entry from the dev HA, so the old
     integration stops polling. Its last session is never logged out, so
     expect that slot to stay taken until it times out. Measuring that
     timeout is part of R1. Before each research session, make sure no HA
     instance you control is polling the pump.
  2. Log in once, do all planned reads, and **always call `cgi/logout`** in a
     `finally`.
  3. On `E_TOO_MANY_USERS`, back off: wait 1, 2, 4 and 8 minutes. That's 15
     minutes in total; never retry faster. If still blocked, stop and ask
     the user (they may need to close the app). Never loop indefinitely.
  4. Never run two pump sessions at once (no parallel scripts).
- **Endpoint allowlist.** The display is an EXOR HMI running the IDAL CGI
  server (Carel-branded console). Endpoints were found in
  `console-carel/ICUGateway.jar`.
  - Allowed without asking (read-only): `cgi/login`, `cgi/logout`,
    `cgi/readTags`, `cgi/browse`, `cgi/getProperties`, `cgi/readAlarms`,
    `cgi/readGroups`, `cgi/readIDALStatusParameters`, `cgi/getTCPIPSettings`,
    `cgi/getPLCStatus`, `cgi/getTime`, `cgi/getLocalTime`,
    `cgi/getDLSSettings`, `cgi/readTrend`, `cgi/readEvent`,
    `cgi/getPropertyGroup`, `cgi/browsePropertyGroup`, plus static files
    under `/console-carel/`.
  - `cgi/readFile`: **approved by the user on 2026-10-30** ("just don't
    break anything"), for R14 only. It's read-only, but go carefully: only
    paths that C's analysis (§6.3) or a directory listing points to, one
    file per request, serially, inside the normal session rules. Save every
    file to `research/captures/readfile/`. Stop at the first unexpected
    error.
  - Allowed only with the user's explicit approval in the current
    conversation: `cgi/writeTags` (Phase 6 only, §10).
  - **Never call**, not even "to see what it returns": `restart`, `reset`,
    `setTCPIPSettings`, `setPLCStatus`, `enterConfigMode`,
    `enterOperatingMode`, `writeFile`, `setTime`, `setLocalTime`,
    `setDLSSettings`, `setProperties`, `setPropertyGroup`, `addPropertyGroup`,
    `deletePropertyGroup`, `activateGroups`, `deactivate`, `resetAlarms`,
    `acknowledgeAlarms`, `deleteTrendFile`, `deleteEventArchive`,
    `dumpTrendFile`, `dumpAllTrendFiles`, `dumpArchiveFile`,
    `dumpAllArchiveFiles`, `rgprs`, or any endpoint not listed here.
- Record every live response you rely on (raw text) in `research/captures/`,
  so nobody needs to ask the pump twice.
- Raw captures can contain network details (MAC, IP, network settings),
  serial numbers and personal data. Keep `research/captures/`
  **gitignored** (the `.gitignore` already exists; keep it when you
  `git init`). Commit only sanitised derivatives: fixtures and findings
  with MAC/IP/serial replaced by placeholders. The repo will be public
  after CP3.

### 2.3 Human checkpoints: stop and report
Work autonomously between checkpoints. At each checkpoint, write a short
report in `docs/progress.md` and stop for the user.

| ID | When | What the user decides |
|---|---|---|
| CP0 | End of Phase 0 | Confirms the decisions in §3 |
| CP1 | End of Phase 1 | Approves the research findings, catalog scope, and entity model (§8) |
| CP2 | Before Phase 6 | Approves the write-test plan; the user is present |
| CP3 | When v1.0 beta is done (P7) | The go to push to the user's GitHub (`github.com/rp9376/…`) and set up the repo. The user already agreed to publish there once it's done; CP3 is the timing and final look. Also: HACS release, contacting the old maintainer, anything PyPI |

Also stop when something contradicts this plan, or when you would need to
break a ground rule.

### 2.4 Git and publishing
- Develop in a local git repository. Local commits are allowed and
  expected: one per finished task, with clear messages. Don't rewrite history
  once something is pushed. Local only for now: no remote repositories
  (user, 2026-10-31).
- Nothing is pushed or published, and no issues, PRs or comments are made,
  until CP3.
- The target is a new public repository under the user's GitHub account
  **rp9376**. The `gh` CLI is **not installed** on this machine. At CP3, ask
  how to authenticate: the user installs `gh` and runs `gh auth login`, or
  provides an SSH/HTTPS remote. Never handle their tokens yourself.
- Prepare the repo setup in P7 so it's a few commands at CP3:
  - description, topics (`home-assistant`, `hacs`, `heat-pump`, `orca`)
  - issue templates: bug report asking for diagnostics; new-setup/fixture
    submission
  - a release workflow that zips `custom_components/orca_heatpump` for HACS
  - a suggested branch protection setup

### 2.5 Language and style
- Code, comments and docs: English. Translations: `en` and `sl`. The HA
  language code for Slovenian is `sl`; the old integration's "si" is wrong.
  Start from the manufacturer's own wording in
  `research/moja_orca_catalog.json` (`*_sl`, `*_en`), cleaned up to HA
  style (§5.4, "Languages").
- Follow `../HAcore/CLAUDE.md` style rules and the HA integration guidelines
  in `../HAcore/.claude/skills/ha-integration-knowledge/`. Comments explain
  *why*, not *what*.
- Python 3.14, matching the HA dev version. `mypy --strict` clean.
  `ruff` uses the HA core config.

---

## 3. Decisions

D1, D8 and the owner (@rp9376) were decided by the user on 2026-10-30; the
rest were confirmed at CP0 on 2026-10-31, with the changes to D6 and D9
below. All of them are ADRs in `docs/decisions/` (context, decision,
consequences); the ADRs are authoritative.

| # | Decision | Default | Why |
|---|---|---|---|
| D1 | Integration domain | **`orca_heatpump`** (decided). Not `orca`. | A clean start with no mix-ups with orca-energy-ha (domain `orca`), and no file collision in `custom_components/`. Naming follows HA core's `nibe_heatpump`. Because both could now be installed at once, and two integrations polling one pump exhaust its sessions, the config flow warns when an `orca` entry for the same host exists (§7.3). |
| D2 | Repo / folder name | `orca-heatpump-ha` | Descriptive. The domain is independent of the name. |
| D3 | Protocol code location | HA-independent package inside the integration: `custom_components/orca_heatpump/client/` (no `homeassistant` imports, own tests, `py.typed`) | Satisfies "integration stays thin" in spirit, and can be extracted to PyPI (`pyorca-heatpump` or similar) later without code changes beyond imports. Publishing to PyPI needs the user and is out of scope for v1. |
| D4 | Tag catalog format | Typed Python (frozen dataclasses), not YAML | Type-checked, no runtime YAML/pydantic/aiofiles dependencies, fast import, and still easy to contribute to. |
| D5 | Runtime dependencies | **None** beyond HA itself (aiohttp from HA, stdlib) | Simplest install; nothing to break on HA upgrades. |
| D6 | Minimum HA version | **2026.11.0** (decided 2026-10-31; `native_*` climate/water-heater temperatures are new in 2026.11). **Latest HA only, no backward compatibility:** use the newest APIs, raise the minimum when needed; the container may move to any HA version. | As future-proof as possible; tested and used only with the latest HA. |
| D7 | Polling | One coordinator, 30 s, all tags batched in as few requests as the pump allows; not user-configurable (HA rule) | The old integration proves 30 s is fine. Revisit only if research shows load issues. |
| D8 | Users of the old integration | **No migration** (decided). They remove orca-energy-ha and set this one up fresh. Config entries start at `VERSION 1`; migrations exist only for our own future versions (§7.3a). | Simpler and cleaner. The README explains the move step by step. |
| D9 | Brand icon | **The official Orca logo, like the old integration** (decided 2026-10-31): the images from home-assistant/brands `custom_integrations/orca` in `custom_components/orca_heatpump/brand/` | Users recognise it; same as orca-energy-ha. |
| D10 | Entity model | As proposed in §8, finalised at CP1 | Driven by research. |

---

## 4. Environment

### 4.1 What exists
- `../ha-dev/ha-dev.sh`: Docker dev environment running HA core from
  `../HAcore` (image `ha-core-dev:latest`, container `ha-dev`, UI
  http://localhost:8123). It currently mounts the **old** integration:
  `../orca-energy-ha/custom_components/orca` →
  `/workspaces/HAcore/config/custom_components/orca`. Commands are in
  `../README.md`.
- The container has HA's dev venv, with `hassfest` and
  `pytest-home-assistant` (HA's new official test plugin for custom
  integrations) installed from `HAcore/packages/`.
- `../HAcore/config/` holds the dev HA config. It has an Orca config entry
  for the **old** integration (entry title `192.168.178.62`). It was
  **disabled** on 2026-10-31, so it doesn't poll the pump. Delete it in P0
  (§2.2).
- The HA login for the dev instance is in `../README.md` (dev-only; never
  copy it into this repo). Use it for the REST and websocket APIs: config
  entries, entity states, and checking your integration live. Change HA
  state through the API, not by editing `.storage/` files: an edit there
  was ignored on startup.
- Gotcha: never use Restart in the HA UI (the container exits with code 100);
  use `ha-dev.sh restart`.

### 4.2 Our test pump
- Model: Orca **Duo 300 Solar**. Schema **#23**: DK1 + MK2 + SV + Solar
  (confirmed by the user).
  - circuit 1 = DK1, named "Floor" (TALNO)
  - circuit 2 = MK2, named "Radiator" (RADIATORJI); currently switched off
    (`2_MK2_vklop` = 0)
  - hot water and solar are present; no buffer tank
  - outdoor unit: Mitsubishi; commissioned October 2026
- **No room sensors**: `2_Temp_Prostora` and `2_Temp_RF2` return `-9999`;
  `2_PogojPGDT_Shema_in_tipalo_OK1/OK2` are `0`. Both circuits regulate on
  **constant temperature** (`2_Reg_po_RF_AF_KONST_MKn` = 4, §5.4). The
  user wants HVAC-mode control only, and sets the flow temperature by hand.
- Alarms seen on this pump in the past (from the user): **"Ni pretoka"**
  (no flow) and **"Napaka senzorja pretoka"** (flow sensor fault).
- The circuit is detected but climate still crashed in the old integration.
  The analysis is in `../ORCA_FIX_NOTES.md`; a stop-gap fix sits on branch
  `climate-without-room-sensor` in the old repo, unrelated to this rewrite.

### 4.3 Changes to make in Phase 0
- Extend `../ha-dev/ha-dev.sh`:
  - Mount this repo at `/workspaces/orca-heatpump-ha`, so tests can run
    inside the container (`ha-dev.sh exec ...`).
  - Mount `custom_components/orca_heatpump` at
    `/workspaces/HAcore/config/custom_components/orca_heatpump`.
  - Because the domains differ, the old `orca` mount can stay for reference,
    but never give both integrations a config entry for the real pump at the
    same time.
  - New mounts need `rm` + `up`.
  - Update `../ha-dev/README.md` and `../README.md`.
- Test runner: tests must run both inside the ha-dev container (fast inner
  loop) and in CI. CI uses a pinned `homeassistant` +
  `pytest-home-assistant` pair; verify these exist. Decided at CP0
  (ADR 0011): `pytest-home-assistant` isn't on PyPI, so CI takes it from
  the core tag that matches the `homeassistant` version under test. Dev-only
  extras (`hypothesis`, …) are installed into the container venv
  (`ha-dev.sh exec uv pip install …`). The entrypoint doesn't reinstall
  them after `rm`, so make the entrypoint install them from this repo's
  `pyproject.toml`, if present.
- Add `--add-host=host.docker.internal:host-gateway` to the container, so HA
  inside it can reach the emulator (§7.4) running on the host.

---

## 5. What we already know (don't rediscover)

### 5.1 Protocol basics (from the old integration)
- `GET /cgi/login?username=…&password=…` returns a body containing
  `IDALToken=<hex>`, used as a cookie. Error bodies: `#E_TOO_MANY_USERS`,
  `#E_PASS_DONT_MATCH`; the web UI also treats `#E_RE-LOGIN_ATTEMPT` as
  success.
- `GET /cgi/readTags?client=<any>&n=<N>&t1=<tag>&…` returns one record per
  tag: `#<tag>\t<status>\n<quality>\t<value>`. Status is `S_OK` or an error
  such as `E_UNKNOWNTAG`; quality `192` = OPC "good". The old integration
  batches 150 tags per request.
- `GET /cgi/writeTags?n=1&t1=<tag>&v1=<int>` returns the same record format.
- `E_NEED_LOGIN` in a response means the token expired.
- **The API is flaky.** The user saw a full tag scrape miss tags on the first
  run; a rerun returned them. Expect responses with records missing, and
  design for it (§6.2, §7.2, R11). Never conclude "this pump doesn't have
  tag X" from a single read.
- Values are always integers:
  - boolean: `0` / `1`
  - one-decimal float: ×10, so 41.5 °C is `415`
  - enum: an integer mapped to a string
  - `-9999` = sensor not connected; an empty string has also been seen
- The jar also lists error codes: `E_UNKNOWNTAG`, `E_READFORBIDDEN`,
  `E_WRITEFORBIDDEN`, `E_UNACTIVETAG`, `E_INVALIDARG`, `E_FAIL`, and others.
  `readTags` can also return `LIMITS`, `SUBSTATUS` and `TIME_STAMP`, which
  may give min/max for writable tags (R2).

### 5.2 Topology signals (verified on 3 pumps: duo #3, mono #7, ours #23)
- `2_Shema`: the schema number, matching the numbering in
  `../Citcuit_schemas.md`. The duo dump says 3 = DK1+SV; the mono dump says
  7 = DK1+DK2+SV.
- `2_Shema_MK1/DK1/MK2/DK2/DK3/SOLAR/SV/ZALOG`: per-element flags. There is
  no MK3 (circuit 3 is DK only).
- `2_PogojPGDT_Shema_OK1/OK2`: circuit present (newer firmware).
- `2_PogojPGDT_Shema_in_tipalo_OK1/OK2/OK3/SV/ZALOG`: **sensor configured**
  for that element. For OKn this matches the room sensor exactly on all
  3 pumps.
- `2_Tipalo_*` (`RF`, `RF2`, `RF3`, `VF1`, `VF2`, `AF`, `BF1`, `BF2`, `KF`,
  `Zalog`, `B11`, `B12`): per-input sensor-present flags, probably more
  granular. Meaning to be confirmed (R6).
- `2_PogojPGDT_Shema_in_Upor_*` and `…_in_Servisni_*`: unknown (R6).
- Circuit names: `MK1_IME`, `MK1_IME(2)`, … are enums ("Floor", "Radiator",
  "Attic", …); the full map is in the old `config.yml`.
- Firmware: `2_Verzija_programa_LETO/MESEC/DAN/ZAPOREDJE` (year, month, day,
  build).
- Alarms: `2_JE_ALARM`, `2_Vrsta_alarma`, `2_Alarm_*`, `2_NI_ALARMA`.
- Regulation mode per circuit and the circuits' tag naming: see §5.4.

### 5.3 Sources to mine
In `../orca-energy-ha/` unless noted:

| Source | Content |
|---|---|
| `custom_components/orca/config.yml` | 74 curated tags with names (EN/SI), types, units, ranges, enum maps. The best starting point. |
| `development_resources/all_fields.txt` | 1,767 tag names (all known tags) |
| `development_resources/field_dump_duo_floor+sv.txt`, `field_dump_mono_floor+radiators+sv.txt` | Raw value dumps from two other pumps (schemas 3 and 7) |
| `development_resources/menu_to_field.yaml` | Touch-UI label → tag (Slovenian; "may contain errors") |
| `development_resources/readme.md` | How tags were discovered (Wireshark, FTP to the display's `workspace/Project/config/` XML) |
| `development_resources/*.pdf` | Slovenian manuals: installation/use Duo (66 pp.) and touch-screen quick guide Mono & Duo (35 pp.). © Orca Energija: **extract facts only, never copy them into this repo.** |
| `development_resources/dump_all/` | Old sync dump tooling |
| `dashboards/`, `measuring_power_consumption/` | Example dashboard and external power metering (ESPHome) docs |
| GitHub issues and PRs at Tomasinjo/orca-energy-ha | Requirements and bugs: #39 circuit 3 (DK3) vs solar and buffer setpoints, #40 DHW setpoint, #30 repurposed sensor input, #33/#34 power and cooling limits, #38 unmapped enum crash, #41 old LCD units (unsupported), #27 schema-based detection, PR #35 |
| `research/moja_orca_catalog.json` (**committable**) | Derived from the two Moja Orca recordings (§5.4): 193 tags with Slovenian **and English** labels (`label_sl`/`label_en`), type, ×10 flag, raw min/max, unit suffix, enum texts (`values_sl`/`values_en`) and our pump's values; all 45 schema names; circuit-name lists; the 5 time programmes; a labelled snapshot of the app's info page. **The primary source for catalog types, ranges and `sl` texts.** |
| `research/captures/moja_orca_si.har`, `moja_orca_en.har` (gitignored) | The raw recordings (Slovenian and English UI, service mode, 2026-10-30, same click path), already sanitised: password, service code, serial and installer name removed. Re-derive the JSON with a script if needed; never commit the HARs. |
| `../ORCA_FIX_NOTES.md` | Code review of the old integration (flaws R1–R4, A1–A7, B1–B7). **Every one of these must be designed out.** |

### 5.4 Facts from the Moja Orca recording (2026-10-30)
The user recorded the manufacturer's web app (`mojaorca.orcaenergy.eu`)
while clicking through every settings page, once in Slovenian and about
3 hours later in English. Both recordings returned the same 193 tags,
ranges and time programmes. The data is in
`research/moja_orca_catalog.json` (§5.3).

- **What the app is:** a PHP site that proxies to the pump through the Orca
  cloud. Login is the device serial number and a password, plus an optional
  service code. It uses `orca.php?f=getpage|readpagetags` and occupies one
  pump session while open. It's not a v1 transport (§8).
- **The manufacturer's own tag metadata.** Each settings page embeds an
  `ORCA.tags_info` JSON with, per tag:
  - Slovenian label
  - type: `boolean`, `integer`, `float`, enum or `input`
  - `cdegrees` (°C, ×10), raw `min`/`max`, and a unit `suffix` (` min`,
    ` s`, ` h`, `%`, `:00`)
  - enum texts
  The recording covers 193 tags, all present in `all_fields.txt`. 152 of
  them are unused by the old integration. Ranges are raw: `float` and
  `cdegrees` values are ×10, and the `%` power limits are ×10 too
  (700 = 70.0 %).
- **Schema names:** `2_Shema` indexes the `wiring_diagrams` list (45
  entries). It matches `../Citcuit_schemas.md`, whose row 5 was wrong
  (fixed: it is MK1+DK2+SV).
- **Circuit tags are named by slot, not by MK/DK.**
  - Slot 1 uses `*_MK1` even on a DK1 pump (ours).
  - Slot 2 uses `*_MK2`.
  - Slot 3 uses `*_DK3`, but also `2_IME_MK3` and `2_Izbira_TIMERJA_MK3`.
  - Some names are irregular: `2_Sobni_DPWT_PGD1` /
    `2_Sobni_2_DPWT_PGD1` / `2_Sobni_3_DPWT_PGD1`; `2_Kalibracija_VF` /
    `_VF2`; `2_Cas_zakasn_izkl_C1..C3`.
  - So the catalog lists **explicit tag names per slot**; no string
    templates.
- **Slots differ:** slot 3 has no mixing-valve tags and no "heat pump
  boost for this circuit". Its mode enum lacks "Ročni preklop" (manual).
  Enum sets and entity sets are therefore per slot.
- **The app doesn't filter by topology.** It shows all three circuit pages
  even on a 2-circuit pump. Never use "the app shows it" as a presence
  signal.
- **Regulation mode per circuit:** `2_Reg_po_RF_AF_KONST_MKn` (heating)
  and `…_HL` (cooling). Values: 1 room temp, 2 outdoor temp, 3 room +
  outdoor, 4 constant. Our pump is on 4 for both circuits. The room-sensor
  type is `2_Sobni_*DPWT_PGD1` (DPWT Carel, NTC, ON/OFF thermostat,
  wireless ORCA, ThTune). Together with sensor presence, this decides what
  the climate entity offers (§7.3, R8).
- **Flow temperature in constant mode (hypothesis for R8):**
  - At 17:16 local, inside circuit 1's timer range (programme 2,
    08:00–18:00), the info page showed "Desired HP temperature" 28.0 °C.
    `2_Max_VF_MK1` was 280 at the same time.
  - At 20:09 local, outside the range, it showed 9.0 °C with pump P1 off.
    The low-regime action, `2_Ponoci_min_temp_IZKLOP_MK1`, is "OFF".
  - So on a constant-temperature circuit, the max-flow setting is probably
    the flow setpoint while the timer is on. `2_Min_VF_*` is probably the
    setpoint for the lower regime when that action is "LOWER
    TEMPERATURE".
  - Verify before exposing it as such. The user controls exactly this
    value by hand today.
- **Global controls the old integration lacks:**
  - `2_Delovanje_MENI`: operating programme (Normal, Holiday, Party, ECO)
  - `2_HITRI_Rezim`: quick room mode (Inactive, Off, Heating, Cooling)
  - `2_Vklop_Izklop`: system on/off
  - `2_SV_vklop`: hot-water enable
  - quiet mode: `2_Tisje_delov` with its outdoor temperature, timer
    programme and power limit
  - power limits per use (heating, cooling, DHW)
  - PV function (`2_PV_Vklop`) and the EVU (utility block) and PV signals
  - screed-drying programme and anti-blocking programme
- **Hot water:**
  - higher and lower temperature (`2_Temp_vode_sanitarna` /
    `_NIZJA`, 8–55 °C) and the on-difference
  - heat pump boost for DHW
  - legionella programme: enable, 65–70 °C, weekday, hour, cycle
  - timer programme selection
- **Additional source / electric heater:**
  - source choice; heater mode Off / Auto / Manual
  - active stages: 1–3 (3 / 6 / 9 kW)
  - per-stage delay and outdoor-temperature threshold
  - parallel operation with the heat pump
- **Buffer and solar:** buffer higher/lower temperatures for heating and
  cooling, on-difference, timer; solar target (DHW or rooms), collector
  min/max temperatures, on/off differences, DHW maximum.
- **Time programmes:** 5 programmes × 3 ranges, each a start–end time and a
  set of weekdays. A range with no days is unused. All 15 of our pump's
  ranges are in the JSON: **ground truth for decoding the `2_TIMER_*`
  tags** (R7). Circuit 1 uses programme 2, circuit 2 programme 5, DHW
  programme 4; the quiet-mode timer is unused ("24-urni režim").
- **Info page:** a labelled value snapshot (outdoor, DHW top/bottom, HP
  temperature and target, pump C0, flow switch, outdoor unit state and
  power %, valve direction, and per circuit room/target/flow/target-flow,
  mixing valve state and opening, pump state). It has labels but no tag
  names. Match it against the P1 full dump to name tags, then confirm
  live, because the values change between the two moments.
- **Alarms:** the app only shows a bare "ALARM" badge from `2_JE_ALARM`,
  with no text, so it offers no alarm texts. Known texts so far: the two
  in §4.2. Hypothesis: "Ni pretoka" ↔ `2_Alarm_ni_pretoka`, "Napaka
  senzorja pretoka" ↔ `2_Alarm_pretocno_stikalo` (R4 confirms).
- **Consistently empty in the app:** `2_Signal_PV`, `2_Signal_EVU`,
  `2_Pogoj_ikona_ele_grelca_1..3` and `2_PogojPGDT_N_OSN_*` came back
  `null` on all 3 reads. That's probably an unreadable or inactive tag on
  this pump, not a random drop. Check their status codes in the P1 dump
  (R6, R11).
- **Service-level settings:** the session was in service mode
  (`2_GESLO_PGDT_Vklop` = 1), which is why installer settings were
  visible. The service password tags (`2_NOVO_GESLO_PGDT`,
  `2_CAS_GESLO_PGDT`) are never exposed by the integration.
- **Languages:** the app offers SI, EN, DE, FR and CZ; SI and EN are
  recorded. Use the English texts as a **reference, not verbatim**:
  - they contain mistranslations, e.g. "HEATING CIRCLE" for circuit, and
    "outlet temperature" for the flow temperature
  - they're ambiguous: "FLOOR" is both storey (ETAŽA) and floor heating
    (TALNO)
  - they're in mixed upper case
  Write `en` in HA style (sentence case, HA's standard terms).
  - 10 labels are English even in the SI UI (summer/winter switch,
    additional-source choice), so the app has no Slovenian text for them.
  - Write `sl` from the SI texts, and translate those 10 yourself.

---

## 6. Research phase details (Phase 1)

### 6.1 Questions to answer
Answer each in `research/findings.md`, with evidence (capture file, manual
page, dump line) and a confidence level.

| ID | Question | How |
|---|---|---|
| R1 | Session model: how many concurrent sessions? Idle timeout? Does polling keep a session alive? Does `logout` free the slot immediately? What does `E_RE-LOGIN_ATTEMPT` mean? | Few, carefully timed live experiments; jar analysis; EXOR/IDAL docs online |
| R2 | Can `browse` enumerate all tags, and does `getProperties` or `readTags` `LIMITS` give type, unit, min, max, writability? | Jar strings and decompiled call formats (static analysis only, never run it); then one live call each |
| R3 | Stable unique device ID (MAC via `getTCPIPSettings`, serial number, PLC ID)? | Live read |
| R4 | **Alarms (a v1 feature, see §8).** What `readAlarms` returns (alarm names, states, events, timestamps, source values). Whether `readEvent` gives an alarm history. What each of the 21 alarm tags means (`2_JE_ALARM`, `2_NI_ALARMA`, `2_NAPAKA`, `2_Vrsta_alarma` (enum: code → text), `2_Alarm_skupna_napaka`, `_pretocno_stikalo`, `_prenizka_temp_TC`, `_ni_pretoka`, `_Talno`, `_Talno_VF2`, `_RF1..3`, `2_Cas_zakasn_ALARM_RF1`, and the `2_Reset*`/`2_Resetiranje_alarmov_*` tags). Which alarms reset themselves (the manual says "NI PRETOKA" does after 30 s of flow) and which need a reset. The manuals have **no alarm code table**, and the Moja Orca app shows no alarm texts (§5.4), so the texts must come from `readAlarms` or R14. Known texts from this pump: "Ni pretoka" and "Napaka senzorja pretoka" (§4.2); match them to tags and codes. | Live reads, R14, manuals, dumps |
| R5 | Firmware/model identification for device info, and model differences (Mono vs Duo, old vs new firmware) | Dumps, live, manuals |
| R6 | Exact meaning of `2_Tipalo_*`, `in_tipalo_*`, `in_Upor_*`, `in_Servisni_*`; how to detect cooling capability, buffer, electric heater stages | Cross-tabulate 3 dumps vs known hardware; manuals |
| R7 | Full tag semantics per element: circuits 1–3, **including circuit 3 (DK3), which the old integration conflated with solar (#39)** (flow temps, mixing valve, pump, curve, day/night, timer programmes and their weekly schedules (`2_TIMER_<n>_<day>_<k>`, on/off hour/minute tags; decode them against the 15 known ranges in §5.4), modes), DHW (setpoint, boost, legionella?), solar, buffer (#39 setpoint logic), outdoor unit, power limits, electric heater | Old config.yml + menu map + manuals |
| R8 | Per regulation mode (`2_Reg_po_RF_AF_KONST_MKn`: room / outdoor / room+outdoor / constant, §5.4), which setpoints actually act? Without a room sensor, do day/night/desired room temperatures still shift the curve? In constant mode, is `2_Max_VF_MKn` (and `2_Min_VF_MKn` in the lower regime) the flow setpoint, as the info page suggests? (Decides what climate and number entities offer per circuit.) | Manuals; observe `2_Izrac_temp_TC` / desired-flow behaviour in captures; compare the info-page snapshot with the P1 dump |
| R9 | Mode semantics: heat / cool / auto / external input / manual per circuit; any global season mode or system on/off? | Manuals, menu map |
| R10 | Are written parameters stored in non-volatile memory with write-cycle limits (EEPROM/flash wear)? | Carel/EXOR docs, manuals. If unknown, assume yes and design for it (§7.2). |
| R11 | Request limits and **reliability**: max tags per request / URL length, latency, whether concurrent requests are safe, and why records go missing (batch size? response truncation? timing? lost while the controller is busy?). Measure the missing-record rate per batch size. | Live, conservative, repeated |
| R12 | Enumerate every enum used (values outside the old maps, e.g. #38) | `research/moja_orca_catalog.json` (enum texts for 42 settings), dumps, menu map, `browse`/`getProperties` |
| R13 | Network discovery possible (DHCP hostname, MAC OUI)? | Live `getTCPIPSettings`, HA DHCP matcher docs |
| R14 (**approved** 2026-10-30) | Does `cgi/readFile` expose the touch-UI project XML (labels ↔ tags, enum texts incl. **alarm texts**, ranges)? The old readme found the project under `workspace/Project/config/` via FTP. This is now the main hope for alarm texts. | Live, read-only, under the §2.2 readFile rules, after C's analysis |
| R15 | Map the Moja Orca browser app. **Done** (SI and EN, §5.4). It has no alarm texts. Nothing left except linking app labels to entities in the catalog. | User recordings only. Never log into the app yourself. |

### 6.2 Order of work
1. **Lead, first:**
   - One live session that reads all 1,767 known tags (batched, read-only,
     then logout) → `research/captures/<date>_full_dump.txt`, plus a JSON
     fixture. This needs only what §5.1 already knows, and gives subagent A
     a third real dump.
   - The API drops records (§5.1). In the same session, re-read every tag
     that came back missing, and repeat full passes until two consecutive
     passes agree on the set of tags present, up to 4 passes. Merge the
     passes into one dump. Keep each raw pass and note which tags were
     missing in which pass: that's the first data point for R11.
   - Save the display's static console files for subagent C, who has no
     pump access: `/` (login page), `/console-carel/INDEX.HTML`, the
     `*.html` pages it links, `scripts/**/*.js` and `ICUGateway.jar` →
     `research/captures/console/`. No login is needed.
2. **Subagents A–D in parallel** (below).
3. **Lead:** the live experiments from C's script (§6.4).

### 6.3 Parallel research subagents (offline only, no pump access)
Launch these at the same time. Each gets a self-contained prompt (they don't
see this conversation) and writes a single file under `research/`.

- **A — tag catalog miner:** cross-references `research/moja_orca_catalog.json`
  (types, ranges, units, enum texts, labels: the most authoritative source),
  config.yml, all_fields.txt, the three dumps (two old ones and ours from
  step 1) and the menu map.
  Output `research/catalog_draft.md`: one row per relevant tag with element,
  semantics, type, scale, unit, writable, range, enum map, confidence and
  source.
- **B — manual reader:** reads both PDFs (Slovenian; `pdftotext` is
  installed, and the Read tool also takes PDF page ranges) and extracts operating
  concepts, parameters, ranges, modes, alarms, timer programmes, heating
  curve, buffer/DHW/solar behaviour and cooling. Output
  `research/manual_facts.md`, citing pages. Facts only, no copied passages.
- **C — protocol analyst:** reads the saved console files and the jar
  (`research/captures/console/`) statically (`unzip`, `javap -c` if
  available, string extraction; never execute it) and EXOR IDAL / JMobile HTTP
  CGI documentation online. Documents the request/response format of every
  allowlisted endpoint (including `readFile`: parameters, path format, how
  to list a directory, which project files hold labels and alarm texts),
  session/lease semantics and error codes. Output
  `research/protocol.md` with a concrete live-test script for the lead.
- **D — history miner:** reads the old integration code, git log, GitHub
  issues/PRs (public API, read-only) and `../ORCA_FIX_NOTES.md`. Outputs
  `research/requirements.md`, containing:
  - the user requirements and every known bug
  - a feature parity list, listing every entity the old integration creates

### 6.4 Lead: live experiments (serial, after C's script)
1. Review C's script against the allowlist before running anything.
2. The R1–R3, R11 and R13 experiments. Keep logins to a minimum and always
   log out.
3. R4 and R14: `readAlarms`, `readEvent`, then `readFile` under the §2.2
   rules. Look for the alarm list and its texts first, then the UI labels.
4. Record session-limit observations precisely (timestamps, responses).

Output of the phase:
- `research/findings.md` (answers R1–R15)
- the finalised `research/catalog_draft.md`
- a proposed entity model and topology model (§8)

Then **CP1**.

---

## 7. Architecture

### 7.1 Repository layout (target)
```
orca-heatpump-ha/
├── PLAN.md                     this file (keep its Status line current)
├── README.md                   user docs (install, setup, entities, supported setups,
│                               moving from orca-energy-ha, alarms, troubleshooting,
│                               limitations, removal, credits)
├── CREDITS.md  LICENSE  CHANGELOG.md  CONTRIBUTING.md  hacs.json
├── CLAUDE.md                   agent rules distilled from §2 (pump safety, workspace)
├── pyproject.toml              ruff, mypy (strict), pytest, coverage config; dev deps
├── .pre-commit-config.yaml     ruff, ruff-format, mypy, codespell, check-json/yaml
├── .github/workflows/          hassfest, HACS validation, lint+type+test (HA stable &
│                               beta), weekly scheduled run against HA beta/dev
├── custom_components/orca_heatpump/
│   ├── __init__.py             setup/unload/migrate; runtime_data
│   ├── manifest.json           config_flow, local_polling, integration_type: device,
│   │                           version, no requirements (add `quality_scale` only
│   │                           if hassfest accepts it for custom integrations)
│   ├── const.py  coordinator.py  entity.py  config_flow.py  diagnostics.py
│   ├── repairs.py  migration.py  helpers.py (if needed)
│   ├── climate.py water_heater.py sensor.py binary_sensor.py number.py
│   ├── select.py switch.py button.py event.py
│   ├── descriptions/           EntityDescription tables per platform (data, no logic)
│   ├── strings.json  icons.json  translations/en.json  translations/sl.json
│   ├── quality_scale.yaml
│   ├── brand/                  brand images (D9); file names per the current HA docs
│   └── client/                 HA-independent protocol package (D3)
│       ├── __init__.py  py.typed
│       ├── client.py           OrcaClient: session, login/logout, read/write, batching
│       ├── protocol.py         URL building, response parsing (pure functions)
│       ├── codec.py            raw int ↔ typed value per tag kind
│       ├── catalog.py          tag definitions (D4)
│       ├── topology.py         schema/flags → PumpTopology
│       ├── models.py           TagDef, TagValue, Snapshot, PumpTopology, DeviceIdentity
│       └── errors.py           exception hierarchy
├── tests/
│   ├── client/                 pure unit tests (parser fuzzing, codec, topology, client)
│   ├── components/orca_heatpump/      HA tests per platform + flows + alarms + diagnostics
│   ├── fixtures/               real dumps (ours #23, duo #3, mono #7), synthetic schemas,
│   │                           alarm scenarios, responses with missing records
│   └── snapshots/
├── tools/
│   ├── orca_probe.py           research CLI: allowlist enforced in code, always logs out
│   ├── dump_to_fixture.py      raw dump / diagnostics JSON → test fixture
│   └── emulator/               fake IDAL server (§7.4)
├── research/                   findings, protocol notes, captures (raw)
└── docs/                       decisions/ (ADRs), progress.md, entities.md,
                                supported-setups.md, protocol.md (summary)
```

### 7.2 Client package (`client/`)
- `OrcaClient(session: aiohttp.ClientSession, host, username, password)`.
  - The session is **injected** (HA passes `async_get_clientsession`).
  - Never create sessions per request.
- One `asyncio.Lock` serialises **all** requests to the pump. The pump is
  slow and single-minded; no concurrency.
- **Login:**
  - single-flight, with the token cached
  - re-login once on `E_NEED_LOGIN`
  - `E_TOO_MANY_USERS` raises `OrcaTooManyUsersError` immediately, with no
    sleeping inside the client; HA's retry machinery handles the backoff
  - `async_logout()` is idempotent and safe on a dead connection
- **Typed exceptions:** `OrcaError` → `OrcaConnectionError`,
  `OrcaTimeoutError`, `OrcaAuthError`, `OrcaTooManyUsersError`,
  `OrcaProtocolError`, `OrcaTagError` (unknown/forbidden tag),
  `OrcaWriteError`, `OrcaValueError` (out of range / bad type).
- **Reading:**
  - `async_read(tags) -> Snapshot`, batched per R11
  - a snapshot contains **every requested tag**, with value `None` and a
    reason (`not_connected`, `unknown_tag`, `empty`, `conversion_failed`)
    when unavailable
  - consumers never `KeyError`: this designs out the old integration's
    bug class
  - **records missing from a response** (the API is flaky, §5.1) are
    re-requested once in the same poll, as one small batch. Still missing →
    reason `no_response`. The snapshot carries the previous value for at
    most 2 consecutive polls, marked stale, before it becomes `None`. This
    stops entities flapping to unavailable on one bad response. The stale
    limit is a constant, tuned by R11.
- **Writing:**
  - `async_write(tag, value)` validates kind and range, encodes, writes,
    then **reads back** and raises `OrcaWriteError` on a mismatch
  - a value equal to the pump's current value (read inside the same lock) is
    not written (flash wear, R10)
- `async_read_identity()` returns the device ID, firmware and model (R3/R5).
- `async_detect_topology()` returns a `PumpTopology`:
  - circuits 1–3, each with kind (MK/DK), name enum, room sensor yes/no,
    flow sensor yes/no
  - DHW, solar, buffer, cooling capability, electric heater stages
  - schema number and firmware
  - derived from §5.2 signals, with deterministic precedence rules and
    fallbacks for older firmware, documented in `docs/protocol.md`
  - robust to dropped records: topology tags missing from a response are
    re-read, and an element is only treated as absent when its signals were
    actually read and say so. "Not received" never counts as "not
    present".
- **Catalog:**
  - one `TagDef` per tag: key, tag name (circuit tags: an explicit name
    per slot 1–3, because the naming is irregular, §5.4), kind
    (float/bool/enum/int), scale, unit, writable, range/step, enum map
    (per slot where the slots differ), element
    (system/circuit/dhw/solar/buffer), required topology predicate, and an
    "advanced" flag
  - types, ranges and enum orders come from `research/moja_orca_catalog.json`
    where it has the tag; a unit test checks the catalog against that JSON
  - Unknown enum values never fail: they decode to `None`, are logged once,
    and appear in diagnostics.
- No HA imports, no logging configuration, no global state. 100% unit test
  coverage. Parser fuzzed with `hypothesis`.

### 7.3 Integration layer
- `entry.runtime_data` holds a typed dataclass (client, coordinator,
  topology, identity).
- **Setup:**
  - connection errors → `ConfigEntryNotReady`
  - auth errors → `ConfigEntryAuthFailed`, which starts reauth
  - too many users → `ConfigEntryNotReady`, with a translated message
    telling the user to close other sessions
- Logout on unload and on HA stop.
- **Coordinator:**
  - `DataUpdateCoordinator[Snapshot]`, passing `config_entry`, 30 s interval
  - converts client errors to `UpdateFailed` with translation keys; the
    coordinator's built-in once-only logging covers "unavailable" and
    "back online"
  - `PARALLEL_UPDATES = 1` on platforms that write, `0` on read-only ones
- **Devices:**
  - one main device for the heat pump (identifier from R3, firmware as
    `sw_version`)
  - one sub-device per present element (each heating circuit, DHW, solar,
    buffer) via `via_device`
  - device names translated (`translation_key` + placeholders for the
    circuit's own name)
- **Entities:**
  - `has_entity_name = True` with a `translation_key` on every entity
  - unique ID = `{base}_{catalog_key}`. `base` is the hardware ID from R3
    if one exists, otherwise the config entry ID (never the host/IP).
    Circuit-scoped keys include the circuit number, never its name.
  - entity category, device class, state class and display precision set
    correctly
  - obscure and service values disabled by default
  - entities are created only when the topology says the element exists;
    availability then follows the tag's actual value
- **Climate (per heating circuit):**
  - HVAC modes derived from capability (off/heat/cool/heat_cool)
  - target temperature features only when the circuit has a room sensor
    **and** its regulation mode uses room temperature (room or room +
    outdoor); otherwise mode-only, like the user's pump (§4.2). Final rule
    from R8
  - preset modes from `2_Delovanje_MENI` (normal / away = holiday / party /
    eco) only if CP1 agrees; it's a global setting, so the main device's
    select is the primary control
  - `native_*` temperature API
  - hvac_action from valve, pump and compressor state
  - turn on/off
  - the raw Orca mode exposed losslessly via the mode `select` entity
  - the mapping is a tested table
- **Water heater:**
  - current temperature (top sensor) and target temperature (#40)
  - operation modes from R7 (e.g. off/on/boost), away mode if meaningful
  - `native_*` temperature API
- **Select:** every writable enum (circuit mode, timer programme, …).
- **Number:**
  - writable numeric settings, with ranges from the catalog/LIMITS
  - `mode: box` for setpoints, so a slider can't spam writes
- **Switch:** writable booleans.
- **Alarms (first-class v1 feature; details depend on R4):**
  - binary sensor "Alarm" (`problem`), on when any alarm is active
  - one binary sensor per specific alarm (flow switch, no flow, low heat
    pump temperature, floor overheat per circuit, room sensor faults, …),
    created per topology and disabled by default where noisy
  - sensor "Active alarm" (enum, translated text from `2_Vrsta_alarma` /
    `readAlarms`); an unknown code shows as "Unknown alarm (code N)",
    never a crash
  - **event entity** "Alarm" firing `alarm_raised` / `alarm_cleared` with
    code and text, so users can notify themselves from an automation without
    templates
  - alarm history from `readEvent`, if R4 shows it works: last N alarms in
    diagnostics and as attributes of the "Active alarm" sensor
  - a "Reset alarms" button **only if** R4 finds a safe reset tag; disabled
    by default, tested in P6, and only for alarms that need a manual reset
- **Sensor / binary sensor:** the other read-only values.
- **Flows:**
  - User flow (host, username, password) with standard error keys:
    `cannot_connect`, `invalid_auth`, `too_many_users`, `unknown`
    (`unknown` is logged with `_LOGGER.exception`)
  - No hardware ID exists (R3) and a host isn't a valid unique ID, so entries
    have none and are told apart by their normalised host (ADR 0013)
  - Reauth flow and reconfigure flow (change host or credentials)
  - Options flow (stored in `entry.options`): topology overrides (force an
    element present/absent, or a room sensor present/absent) for the rare
    pumps where detection is wrong, or where a sensor input is repurposed
    (#30). There's no "show advanced entities" toggle: advanced entities
    always exist and are disabled by default, which is the HA convention.
  - The config flow logs out after validating.
- **Diagnostics:** topology, identity, full snapshot and raw values (with
  host, credentials, MAC and serial redacted). Designed so a user's diagnostics file can
  be turned into a test fixture with `tools/dump_to_fixture.py`. This is how
  the integration grows to "everyone's" setups.
- **Repairs:**
  - an issue when detected topology differs from the stored one (pump
    reconfigured), offering a reload
  - an issue when sessions are persistently exhausted
- **Coexistence with orca-energy-ha (D1, D8):** no migration. If a config
  entry of domain `orca` exists for the same host:
  - the user flow shows a warning step explaining that two integrations
    polling one pump exhaust its sessions, and asks the user to remove or
    disable the old one first (they may continue anyway)
  - a repair issue stays open while both are loaded
- **Translations:** `en` and `sl` complete, with exception and icon
  translations.

### 7.3a Compatibility rules (forever, from 1.0 on)
- Entity unique IDs never change. Renaming a catalog key requires an
  entity-registry migration in `migration.py` and a test.
- Any change to stored entry data or options bumps the config entry
  version (or minor version), with a migration and a test.
- Never silently remove an entity. Removals are listed in the CHANGELOG;
  stale devices and entities are cleaned up deliberately.
- Releases use semantic versioning. Breaking user-visible changes need a
  major version and a CHANGELOG "Breaking changes" section.

### 7.4 Emulator (`tools/emulator/`)
An aiohttp server that mimics the IDAL CGI API, driven by a fixture:
- login/logout/readTags/writeTags plus the other allowlisted reads
- configurable session limit and idle timeout
- token expiry, `-9999` and empty values, unknown tags, slow responses,
  dropped connections, malformed bodies, randomly dropped records, and
  scripted alarm raise/clear sequences (fault-injection flags)

Uses:
1. the client test suite
2. HA integration tests at the HTTP level
3. pointing the ha-dev HA at the emulator to click through **any topology**
   (all 45 schemas and the real dumps) without touching the pump

Run it on the host and reach it from the container via the Docker host
gateway.

---

## 8. Entity model (proposal — finalise at CP1 with research)

Per element, present only when the topology says so. Final keys, names and
the enabled-by-default set come out of R7–R9.

- **Heat pump (main device):**
  - outdoor temperature
  - heat pump flow temperature and its target
  - compressor power % (`2_PRIKAZ_Reg_temp_vode`; #33 doubts what it really
    is, so confirm it in R7 before naming it)
  - operating state (enum)
  - 3-way valve position
  - circulation pump C0 and flow switch
  - electric heater: status, mode (off/auto/manual), active stages, stage
    delays and outdoor thresholds; additional source choice
  - max power heating/cooling/DHW (numbers)
  - system on/off (`2_Vklop_Izklop`)
  - operating programme select (`2_Delovanje_MENI`: normal / holiday /
    party / eco) and quick room mode select (`2_HITRI_Rezim`), §5.4
  - quiet mode (mode, outdoor temperature, timer, power limit)
  - PV function and the EVU/PV input signals
  - screed drying and anti-blocking programmes (advanced, disabled by
    default)
  - alarms: overall, per-alarm binary sensors, active alarm text, alarm
    event entity, optional reset button (§7.3)
  - firmware
- **Heating circuit n (1–3, MK or DK):**
  - climate entity
  - room temperature (only with a sensor)
  - flow temperature and its target
  - mixing valve status/position (MK only)
  - pump status
  - day/night/desired room temperatures (R8)
  - heating curve parallel shift and slope
  - min/max flow temperature for heating and cooling. On a
    constant-temperature circuit, this may be the flow setpoint the user
    wants to control (R8); if so, name and place it as such.
  - mode select, regulation mode select (heating and cooling) and timer
    programme select
  - summer/winter automatic switch (enable, outdoor temperature, delay)
  - room sensor type (diagnostic)
  - circuit on/off (handled by climate; no duplicate switch)
  - weekly timer schedules: read-only in v1 (programme in use, plus diagnostics
    and attributes); editing them goes to the backlog unless R7 shows it's
    simple and safe
- **Hot water:**
  - water heater entity
  - top and bottom temperatures
  - higher and lower setpoints, and on-difference
  - boost / extra temperature (`2_Povec_temp_TC_pri_SV`)
  - enable
  - legionella programme (enable, temperature, day, hour, cycle)
- **Solar:** collector temperature, pump, enable (repurposed input, #30:
  options override).
- **Buffer:** temperature, setpoints, explaining the actual logic from #39 in
  the docs.
- **Not in v1:**
  - trends/history (HA records history itself)
  - cloud/remote access via Moja Orca
  - Modbus
  - old LCD-display units without a network port (#41)
  - power metering (link the old ESPHome guide, with credit)
- **Later, optional, the user decides:**
  - extract `client/` to PyPI
  - submit to HA core (needs the PyPI library, brand assets in the
    home-assistant/brands repo, and HA's review/AI policy, which requires
    the human to drive)

Parity rule: every entity the old integration created has a counterpart, or
a documented reason for removal (research D's parity list).

---

## 9. Phases

Each phase ends with:
- tests green
- `docs/progress.md` updated
- a local commit
- a line in `../README.md` → Work log

### P0 — Bootstrap → CP0
- `git init`. The `.gitignore` already exists (`.scratch/`,
  `research/captures/`, `*.har`, `__pycache__/`, `*.py[cod]`); keep it in the
  very first commit, together with `research/moja_orca_catalog.json`. Add LICENSE (§12), README stub, CREDITS.md, CLAUDE.md,
  pyproject, pre-commit, CI workflows, empty package skeletons, quality_scale.yaml
  (all `todo`), docs/ and research/ folders.
- Determine D6, the minimum HA version (check when each API we need was
  introduced).
- Delete the old Orca config entry from the dev HA (§2.2), so it stops
  polling the pump.
- ha-dev changes (§4.3); prove that `pytest` runs in the container with a
  trivial test.
- Write the ADR stubs for D1–D10. **Stop at CP0.**

### P1 — Research → CP1
§6, in the order of §6.2. Deliverables are listed in §6.4. **Stop at CP1.**

### P2 — Client package + emulator
- Tests first: parser, codec, catalog validation (no duplicate keys, ranges
  sane, every enum complete per R12), topology for all 45 schemas
  (parametrized synthetic fixtures) and the 3 real dumps.
- Client against the emulator: session handling, batching, errors, logout,
  write read-back.
- `tools/orca_probe.py` re-implemented on top of the client, with the
  allowlist enforced in code.
- Exit criteria:
  - 100% coverage of `client/`
  - mypy strict clean
  - a one-shot live read of our pump through the new client (lead only,
    read-only, logs out) produces a snapshot with no unexplained conversion
    failures; any new enum values found are added to the catalog

### P3 — Integration core
- `__init__` (setup/unload/migrate), runtime_data, coordinator, base entity,
  device registry layout, config/reauth/reconfigure/options flows,
  diagnostics, repairs, translations skeleton.
- Tests:
  - 100% config-flow coverage
  - setup failure modes (not ready / auth failed / too many users)
  - unload logs out
  - the coexistence warning with an `orca` entry present
- When P3 is green, add an `orca_heatpump` config entry for the real pump in
  the dev HA. It stays there from now on and is the live test bed.

### P4 — Platforms (parallel)
The lead first freezes the contracts: base entity, description dataclasses,
snapshot API, catalog keys. Then subagents run in **separate git worktrees**,
each owning only its files:

| Agent | Files |
|---|---|
| A | climate |
| B | water_heater |
| C | sensor + binary_sensor + event (alarms, §7.3) |
| D | number + select + switch + button |

- Each delivers: a descriptions table, translations (en + sl) for its keys,
  and snapshot tests for all 3 real fixtures plus representative synthetic
  schemas.
- The lead merges, resolves translation-file conflicts and runs the full
  suite.

### P5 — Hardening and review
- **Fault-injection suite** against the emulator:
  - session exhaustion and recovery
  - token expiry mid-poll
  - pump reboot
  - malformed responses
  - unknown enum
  - HA restart loops: verify sessions are released
- **Live, read-only:**
  - with ha-dev on the new integration since P3, run at least **24 hours**
    against the real pump
  - check: no errors or warnings in the log, no `E_TOO_MANY_USERS`, the
    session count stays stable across 5+ reloads, and entity values are
    plausible against the touch display (the user spot-checks)
- **Reviews:** independent review subagents using
  `../HAcore/.claude/skills/ha-review/` and `ha-quality-scale-verify/`,
  plus a separate security/safety review of the write paths. Fix the
  findings.
- `quality_scale.yaml`: every Bronze, Silver and Gold rule `done` or `exempt`
  with a reason; Platinum `inject-websession`, `strict-typing` and
  `async-dependency` done.
- Docs complete (§11).

### P6 — Live write testing → CP2 first
- Write a test plan: each writable entity, a safe test value, the original
  value, and the restore step.
- **Stop at CP2.** Run it only with the user present and agreeing in the
  conversation.
- Log every write (time, tag, old, new, read-back) in
  `research/captures/write_tests.md`. Restore everything.

### P7 — Release preparation → CP3
- Version `1.0.0b1`, CHANGELOG, HACS validation green, README "Moving from
  orca-energy-ha" section tested end to end in ha-dev: remove the old
  integration, then add this one.
- GitHub repo setup prepared (§2.4).
- Draft (do not send) a friendly note to Tom Kern explaining the rewrite and
  offering it upstream.
- **Stop at CP3.** The user publishes.

---

## 10. Write safety (all phases)
- The product code writes only through `OrcaClient.async_write`. That means
  catalog-declared writable tags only, range-checked, read back, and skipped
  when unchanged.
- Numbers use box mode; no auto-repeat writes. The coordinator refreshes
  right after a write.
- Never write in tests against the real pump outside P6. Test writes run
  against the emulator.
- **Installer settings are never writable**, in any version, because a
  wrong value can stop the heating or damage hardware. They may be
  read-only diagnostic entities, disabled by default:
  - the schema (`2_Shema`, `2_Shema_*`)
  - contact types (`2_Kontakt_*`, NO/NC)
  - sensor calibrations (`2_Kalibracija_*`)
  - the service password and its timeout (`2_NOVO_GESLO_PGDT`,
    `2_CAS_GESLO_PGDT`; not even read-only)
  - the clock (`2_CURRENT_*`)
  - mixing-valve run times (`2_Cas_MP*`)
  - pump and compressor delays and minimum times
  - the heat pump's differential and limit curve (`2_Krivulja_TC`,
    `2_Limita_moci_*`)
  - room-sensor type and circuit hardware type
    (`2_Sobni_*`, `2_Talno_Radiatorsko_*`)
  CP1 may move an item onto this list, never off it.
- Document in the README that automations writing setpoints frequently may
  wear the controller's memory (R10), and recommend change thresholds.

---

## 11. Definition of done (v1.0)
- Works for all 45 schemas: tested with synthetic fixtures. Works on 3 real
  pumps: tested with their dumps, and live on ours.
- No platform can crash from missing, odd or unknown values: tested.
- Session-safe:
  - logs out on unload and stop
  - recovers from too-many-users without a manual reload
  - verified live
- Quality: ruff, mypy strict, hassfest, HACS validation and pytest all green
  in CI (HA stable and beta); coverage at least 95% overall, 100% for
  `client/` and config flows.
- Quality scale: Gold done (or exempt with a reason); the Platinum items
  above done.
- Alarms work end to end: tested with emulator scenarios (raise, clear,
  unknown code, flapping). On the real pump, verify at least the "no alarm"
  state; a real alarm is never provoked on purpose.
- Coexistence warning with orca-energy-ha tested; README explains the move.
- The API's dropped records never make an entity flap or a topology element
  disappear (tested with the emulator's drop-record fault).
- Docs:
  - README: what it is, supported hardware, install (HACS and manual),
    setup, entities per element, moving from the old integration, alarms, options,
    troubleshooting (incl. session limit), known limitations, removal,
    credits
  - `docs/supported-setups.md`: schemas tested, how to contribute a
    diagnostics dump
  - CONTRIBUTING.md: adding a tag, a translation, a fixture
- English and Slovenian translations complete.

---

## 12. Credits and license
- **LICENSE:** MIT. Because the catalog, encodings and tag research derive
  from orca-energy-ha (MIT), keep its notice. Its LICENSE file has no
  copyright line, so state it explicitly:
  `Copyright (c) 2022-2026 Tom Kern (@Tomasinjo) and orca-energy-ha contributors`,
  then the new work's line:
  `Copyright (c) 2026 rp9376 and orca-heatpump-ha contributors`.
- **CREDITS.md and a README section "Credits":**
  - Original integration: **orca-energy-ha** by **Tom Kern
    (@Tomasinjo)**, 2022–2026, https://github.com/Tomasinjo/orca-energy-ha.
    It did the protocol and tag research (Wireshark/FTP methods, tag dumps,
    menu mapping) this rewrite builds on.
  - Contributors to the original: list them by **GitHub handle**, built
    from the merged PR authors and the git log, and verified before
    publishing (never use email addresses). Known so far: @thranduil,
    @romanorac, @FloGerl, @rp9376 and @sinjorgo. Also thank the issue
    reporters and testers, e.g. @truzzman and @Speijtuut.
  - External power-metering guide (ESPHome) from the original repo: link and
    credit, don't copy.
  - Orca Energija d.o.o. manuals: used as reference only, not redistributed.
    "Orca" is their trademark; this project is not affiliated with Orca
    Energija, Carel or EXOR.
- `manifest.json` `codeowners`: `["@rp9376"]`.

---

## 13. Working method for the lead agent
- **Keep state on disk, not in your head.** Long tasks get summarised.
  - `docs/progress.md`: current phase, done, next, blockers
  - `research/`: facts
  - `docs/decisions/`: ADRs
  - the Status line at the top of this file
  - Update them as you go, so a fresh session can resume from them alone.
- **Subagents:**
  - Use them where work is independent: research A–D in P1, platforms in
    P4, reviews in P5.
  - Give each a complete, self-contained brief: goal, inputs (absolute
    paths), output file, constraints including "no pump access, stay in the
    workspace", and acceptance criteria.
  - Code-writing subagents use `isolation: worktree` and own disjoint files.
  - Read-only searches use Explore agents.
  - Verify subagent output yourself before building on it.
- **Contracts before parallelism:** freeze the shared interfaces (models,
  catalog keys, base entity, description types) before fanning out.
- **Tests first** for the client and topology. Snapshot tests for platforms.
- **Small steps:** commit per task; keep `main` green.
- **When unsure,** prefer what HA core's Gold/Platinum integrations do; look
  them up in `../HAcore/homeassistant/components/`.
- **Report faithfully:** if something fails, is skipped, or couldn't be
  verified on the real pump, say so in `docs/progress.md` and at
  checkpoints.

---

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Session lockout during development | One pump owner, logout always, backoff schedule, the emulator for everything else |
| API drops records | Retry missing tags within the poll, short stale tolerance, multi-pass research scrapes, the emulator's drop-record fault in tests |
| Users run old and new integration together | Different domains prevent file clashes; config-flow warning and repair issue against session exhaustion |
| Writes harm the heating system | Allowlist, P6 only with the user, read-back, restore log |
| Flash wear from frequent writes | Skip unchanged values, box-mode numbers, documentation (R10) |
| Topology detection wrong on unseen pumps | Multiple signals with precedence, options overrides, diagnostics → fixture pipeline, repairs on change |
| Unknown firmware differences (older pumps) | Tolerant snapshot (unknown tag → None), feature detection over version checks, community fixtures |
| HA API deprecations | CI against HA beta weekly, min version policy (D6) |
| Upstream relationship | Credit prominently, draft a note to Tom Kern, offer collaboration; the user decides at CP3 |
| Scope creep | §8 "Not in v1" list; new ideas go to `docs/backlog.md` |
