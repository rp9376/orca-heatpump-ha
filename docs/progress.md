# Progress

**Phase 5 (hardening and review) in progress.** Paused 2026-11-01 ~20:05
UTC at the user's request, resumed 2026-11-02 ~20:00 UTC. Phase 4 done on
2026-11-01; Phases 2 and 3 and CP1 the same day. Next: see "Resume here"
below.

## Phase 5 (hardening and review): in progress

### Resume here
1. **Independent reviews (PLAN §9 P5).** Three read-only review subagents
   were started at ~19:58 and stopped for the pause before they reported;
   nothing of theirs is on disk. Restart them in the background:
   - HA code review of the whole integration, following
     `../HAcore/.claude/skills/ha-review/SKILL.md` (no upstream base: review
     everything as new code).
   - Quality scale: verify every rule in `quality_scale.yaml` from scratch
     with `../HAcore/.claude/skills/ha-quality-scale-verify/SKILL.md`
     (docs = README; brands = `brand/`; strict typing = mypy strict in
     `pyproject.toml`).
   - Security and write safety: every service → `writeTags` path, catalog
     writability vs PLAN §10 and the register areas, ranges vs
     `research/moja_orca_catalog.json`, no password/code tags, endpoint
     allowlist in `protocol.py` and the probe tools, sessions, redaction.
   Each prompt: read-only (no file changes, no commits), never contact the
   pump or the dev HA, only `ha-dev.sh test` / `hassfest` (never `lint`,
   which auto-fixes), no nested subagents. Then fix the findings.
2. **24 h live run.** Restarted 2026-11-02 20:00 UTC (`ha-dev.sh up`); due
   2026-11-03 20:00 UTC, **only valid if the host stays awake**. Check
   `../HAcore/config/home-assistant.log` from then on: no warnings or errors
   from `orca_heatpump`, no `too_many_users`, no availability gaps, and a
   poll every 30 s without gaps (gaps with no log lines at all mean the
   host slept). Then ask the user to spot-check values against the touch
   display.
   - First attempt (2026-11-01 19:44 → 2026-11-02 17:29 UTC) doesn't count:
     the host suspended at 22:21 UTC and stayed mostly asleep, then
     rebooted, which stopped the container. Polling covered about 3.5 h:
     387 polls and 9 timer reads, none failed, no warning or error from
     the integration. After each wake the display had dropped the session
     and the client logged in again within the poll (05:18 and 16:58 UTC),
     with nothing going unavailable.
3. Update this file, the PLAN Status line and the Work log, and **stop at
   CP2** (before any write to the pump, PLAN §2.3) with the report and the
   questions collected below.

### State while paused
- The dev HA keeps running and its `orca_heatpump` entry keeps polling the
  real pump every 30 s (one login; timers hourly). That is the 24 h run.
  To free the display, disable the entry in the dev HA (Settings → Devices
  & services) or stop the container (`../ha-dev/ha-dev.sh down`); a
  disabled or stopped entry ends the 24 h run, which then has to start
  again.
- Nothing has been written to the pump. All work is committed; the
  repository is clean.

### Done (committed)
- **Fault suite** (`tests/components/orca_heatpump/test_faults.py`), all
  platforms on the emulator: failed polls (HTTP 503, malformed body,
  disconnect, whole-response error) and recovery; token expiry renewed
  within the poll; display reboot; exhausted sessions and recovery;
  dropped records never make an entity flap (10 polls at 10 % drops);
  five reloads and an HA stop with only one session allowed leave none
  behind.
- **All 45 schemas** set up against the emulator, are detected as stored,
  raise no issue and get one device per element (`test_schemas.py`,
  snapshot of devices and entity counts). Pumps without a heating circuit
  no longer get quick room mode or screed drying.
- **Odd values everywhere** (empty, text, -9999, huge, negative in every
  non-topology tag): the integration stays loaded with no error logged.
  This found a real bug: a huge firmware year raised `OverflowError` in
  `async_read_identity` and stopped setup; fixed and tested.
- Values nobody has seen yet keep any entity available with an unknown
  state (rule moved into the base entity).
- `quality_scale.yaml`: every rule done or exempt with a reason
  (exempt: action-setup, docs-actions/conditions/triggers,
  dependency-transparency, discovery, discovery-update-info,
  dynamic-devices). **Not yet independently verified** (see above).
- Docs (PLAN §11): README rewritten (what it does, supported pumps,
  install, setup, options, entities, data updates, alarms with an
  automation example, moving from orca-energy-ha, troubleshooting, write
  wear advice from §10/R10, known limitations, removal),
  `docs/supported-setups.md`, `CONTRIBUTING.md`.
- `tools/dump_to_fixture.py` turns a diagnostics download into a fixture;
  a test replays each real pump's diagnostics through the emulator and gets
  identical readings.
- A test keeps `translations/en.json` equal to `strings.json` and
  `sl.json` complete.
- Tests: 1,038 passing; coverage 100 % for every module; ruff, ruff
  format, mypy (strict), hassfest clean.

### Live checks so far
- Startup with all platforms (19:44 UTC): 123 entities, polls 50–90 ms,
  timers read in 0.19 s, no warnings or errors from the integration.
- Six reloads of the live entry in a row, 20 s apart (19:58–20:01 UTC):
  each loaded, no refused login, no failed read, no warning or error, so
  no session leaks on the real display.

### Questions collected for CP2
- Mono fixture's heating power limit 39.0 % is below the manufacturer's
  minimum 40.0 %: can installers set lower values (then the catalog minimum
  is wrong), or is it a leftover from older firmware?
- Alarm reset button: does the controller clear the flag itself? (The
  client's read-back would then report a failed write.) Phase 6 test.
- Climate on the real pump: mode written before the circuit's enable.

## Phase 4 (platforms): done 2026-11-01

One commit per platform, each with en + sl names, icons, snapshot tests for
the three real pumps (ours, Duo, Mono) and 100 % coverage. Written by the
lead in sequence rather than by parallel subagents in worktrees (PLAN §9
P4): with the contracts in `entity.py` frozen, each platform was small, and
one author kept names and translations consistent.

- **Platforms:** binary_sensor, sensor, event (alarm raised/cleared),
  climate (a thermostat when a room sensor regulates the circuit, else
  mode-only; CP1), water_heater, number (manufacturer ranges, box mode),
  select, switch, button (alarm reset, disabled until the Phase 6 write
  test). Our pump gets 123 entities, 44 enabled by default (19 sensors,
  8 binary sensors, 8 selects, 3 numbers, 2 climates, 2 switches, the event
  and the water heater); the snapshots hold the exact sets per pump.
- **Power limits (ADR 0012):** sensors by default; numbers (whole percent,
  manufacturer range) with the option; changing the option removes the other
  form from the entity registry. The hot water limit exists only with hot
  water.
- **Writes** go through `async_write_values`: several values in order, one
  refresh. A climate mode is written before the circuit's enable; off keeps
  the mode, so turning on resumes it.
- **Regulation-dependent names and defaults** (flow setpoint vs maximum flow
  temperature, curve settings enabled) are decided at setup; a regulation
  change shows after a reload. The climate's target follows regulation on
  every poll.
- **Timer programmes:** a second coordinator reads the 165 timer tags once
  an hour through the same client and lock; the timer selects show the
  selected programme as a `schedule` attribute (unrecorded), diagnostics
  show all five. Incomplete reads keep the last good programme.
- **Synthetic schemas:** besides the three real pumps, schema 43 (two mixing
  circuits, direct circuit 3, buffer, a room-regulated circuit) and schema
  11 (one mixing circuit, nothing else), built from our dump; each is
  detected as built and its whole entity set is a snapshot.
- Tests: 973. Coverage 100 % for the whole integration. ruff, mypy
  (strict), hassfest clean. A test keeps `en.json` equal to `strings.json`
  and `sl.json` complete.
- **Live (read-only), 2026-11-01 19:44:** the dev HA restarted with all
  platforms against the real pump: 123 entities registered, timers read in
  0.19 s, polls 50–90 ms, no warnings or errors from the integration, no
  unknown values. Entity values not yet compared with the touch display
  (user spot check in P5). Nothing was written.
- **Real data below the manufacturer's minimum:** the Mono fixture holds a
  heating power limit of 39.0 % (minimum 40.0 %). Home Assistant shows it;
  writing it back would be refused. Ask the user at CP2 whether installers
  can set lower values (then the catalog minimum is wrong) or this is a
  leftover from older firmware.
- **For CP2 / Phase 6:** the alarm reset button's behaviour (does the
  controller clear the flag itself? The client's read-back would then report
  a failed write); the climate's mode-then-enable order on the real pump.

## Phase 3 (integration core): done 2026-11-01

- `__init__.py` (setup/unload, logout on every failure, on unload and on HA
  stop), `coordinator.py` (polls only present elements; "sessions
  exhausted" issue after 3 refused polls), `entity.py` (base entity, device
  per element), `config_flow.py` (user, orca-energy-ha warning, reauth,
  reconfigure, options with opt-in power limits and topology overrides),
  `diagnostics.py`, `repairs.py` (accept a changed topology), `helpers.py`,
  translations en + sl (device names from each circuit's own name).
- Repair issues: topology changed (fixable; the stored topology wins until
  confirmed), orca-energy-ha on the same pump, sessions exhausted.
- Tests: 881 in total; the integration tests run Home Assistant against the
  emulator over real HTTP. Coverage 100 % for every module except
  `entity.py` (used from P4 on). Config flow 100 %, each error with a
  successful retry.
- **Live test bed:** an `orca_heatpump` entry for the real pump is now in
  the dev HA (added through the config flow, 2026-11-01 ~10:45). Devices:
  Heat pump (Mitsubishi, firmware 61 (2016-12-12)), Underfloor heating,
  Radiators, Hot water, Solar collectors. No warnings or errors in the log.
  Without entity platforms the coordinator does not poll yet; from P4 on
  it polls every 30 s with one session. Before any research session, this
  entry must be disabled (PLAN.md §2.2).
- Learned on the way (HA 2026.11): `async_setup_entry` returns None,
  unload uses `async_unload_platforms_or_raise`, config flows use
  `probatio`, repair flows return `RepairsFlowResult`, issue data holds
  only scalars, and a coordinator without listeners does not poll.



## CP1 outcome (user, 2026-11-01)

Research, catalog and entity model approved, with these decisions
(`docs/entity-model.md`, ADRs 0010, 0012, 0013):
1. Constant-temperature circuits: mode-only climate plus a "Flow temperature"
   number. **Without a room sensor** the climate is stripped down to the
   controls (on/off, heat/cool); **with one** it is a normal climate entity.
2. Power limits (heating, hot water, cooling, quiet mode): an **opt-in
   "Allow changing power limits" checkbox** at setup (and in the options),
   described as risky; ranges enforced in code (ADR 0012). orca-energy-ha
   exposes them always, with 10–100 %.
3. Cooling: Orca pumps can cool their heating circuits. Every circuit offers
   off / heat / cool / heat-cool, as orca-energy-ha does via "Režim
   delovanja" (`2_Rezim_MKn`).
4. Passwords are not this integration's business: no password or code tag in
   the catalog, nothing more.
5. No presets on the climate. (Read as "skip presets"; modes 4 and 5 still
   show as `auto` and are set through the raw mode select.)
6. Session slot count: not measured (no concurrent sessions).
7. No network discovery; the display keeps a fixed IP (ADR 0013).
FYI items (MK2 flow sensor, firmware 2016) were noted without action.

## Phase 2 (client package and emulator): plan and state

Package `custom_components/orca_heatpump/client/`, no HA imports, 100 %
coverage, tests in `tests/client/`. Steps (tick when committed):
- [x] `errors.py`, `models.py` (TagDef, Reading, Snapshot, topology, identity)
- [x] `protocol.py`: request targets (budget 3,500 bytes per target, R11),
      record and login parsing, error-code mapping
- [x] `codec.py`: raw ↔ value per tag kind; -9999, empty, unknown option
- [x] `topology.py`: the 45 schemas (checked against the manufacturer's
      list) and detection; tests for all schemas and the real dumps
- [x] `catalog.py`: the keys of `docs/entity-model.md`; tests against
      `moja_orca_catalog.json` (types, ranges, enums) and
      `tag_registers.json` (×10 ⇔ 5xxxxx, never writable on IREG/INP)
- [x] `client.py`: OrcaClient (lock, login single-flight, re-login on
      E_NEED_LOGIN, batching, stale carry, guarded write with read-back,
      idempotent logout, identity, topology)
- [x] `tools/emulator/`: fake IDAL server with fault injection; client
      tests against it
- [x] `tools/orca_probe.py` on top of the client
- [x] exit: 100 % `client/` coverage, mypy strict, one live read-only read
      of our pump through the client

Done so far: 125 catalog entries (generated once from `catalog_draft.md` and
the manufacturer's metadata, then reviewed; generator kept out of the repo),
fixtures for the duo (#3) and mono (#7) pumps, 814 tests, 100 % coverage.
Found while testing: `2_Shema` is used as a number (the app models it as a
list), and the mixing valve position sits in an integer register but is
shown ×10 by the app; both are named exceptions in `test_catalog.py`.

**Phase 2 exit (2026-11-01):** 841 tests, `client/` coverage 100 %, mypy
strict clean. Live read of our pump through `OrcaClient` (one read-only
session, logged out): identity "61 (2016-12-12)", Mitsubishi, topology #23
as built, all 189 catalog tags; the only readings without a value are the 4
newer-firmware alarm tags and 5 unplugged sensors. No conversion failures,
no unknown enum values, nothing stale.

Design notes: the token is sent as an explicit `Cookie` header (HA's shared
session has a cookie jar); errors arrive with HTTP 500 and a `#E_…` body;
HTTP 408 means our request was too big (a bug, never "tag missing").

## Phase 1 (research)

### Done
- Lead's live work, all read-only, one session at a time, 9 logins, never
  `E_TOO_MANY_USERS` (session table in `research/findings.md`):
  - static console files, a two-pass dump of all 1,767 known tags
  - C's Session 1 (discovery, exact request limit, timing, 10 reliability
    passes), Session 2 (R14 `readFile`: the alarm page with the alarm texts),
    Session 3 (session lifetime), a full tag-definition browse and a
    heating snapshot
  - not run: C's optional S1-38/39 (oversized POST, duplicate tags; risk
    without value) and the gated Session 4 (decision 6)
- Research subagents A (catalog), B (manuals), C (protocol), D (history,
  parity, credits); all four outputs verified by the lead before use.
- Tools: `tools/orca_probe.py` (allowlisted transport: lock, backoff, logout
  in a `finally`, exact header-size measurement, refusal of password tags and
  unlisted `readFile` paths) and `tools/orca_research.py` (the sessions).
  Session 1 and 2 runners were dry-run against a local fake server first,
  which caught two bugs before they reached the pump.
- Committed derivatives: two fixtures of our pump (timer off; heating),
  `research/tag_registers.json` (1,189 tag definitions),
  `research/alarm_texts.json` (alarm codes, 7 languages).
- `CREDITS.md` handles verified by research D (all 8; "420Cupcake" is
  @rp9376, "Robert" is @thranduil).
- `docs/entity-model.md`; ADR 0010 points to it.

### Key results
- No random record loss: a deterministic HTTP 408 above 4,095 header bytes.
- Session idle timeout 2–3 min; reads keep it alive; errors on HTTP 500.
- No hardware ID; MAC vendor prefix is Carel's.
- Alarm codes 1–6 with texts in 7 languages; no alarm history.
- Constant mode confirmed: the HP target is `2_Max_VF_MKn` while the timer
  is on.
- Register address shows the ×10 scale; IREG/INP tags are read-only.

### Judgement calls to review
- R14 "stop at the first unexpected error": two stops (`#E_FILEOPENFAIL` on a
  directory path, `#E_FILENOTEXIST` on `propertymap.xml`). Both meant "not a
  file"; the display stayed healthy, so I resumed in new sessions with the
  remaining **named** files only. One follow-up file
  (`Page109 - Kopija.jmx`) came from the old menu map, not from C's list (C
  had dropped the " - Kopija" suffix).
- The register map and snapshot sessions were additions to C's script: the
  same read-only `browse` and `readTags` calls.

### Not verified, caveats
- Session slot count and whether logout frees a slot at once (decision 6).
- `2_Min_VF_MKn` as the setpoint with the "lower temperature" low-regime
  action: needs a write (Phase 6).
- Outdoor unit states 2 (cooling) and 3 (defrost); room setpoint ranges
  (no pump with a room sensor recorded).
- The code → per-alarm-tag mapping is by name; a real alarm is never
  provoked.

## Phase 0 (bootstrap)

### CP0 outcome (user, 2026-10-31)

- All decisions confirmed (ADRs 0002–0005, 0007, 0011, and the git author
  `rp9376 <rp9376@student.uni-lj.si>`), with two changes:
  - **D6:** minimum 2026.11.0 and **latest HA only, no backward
    compatibility**. Use 2026.11 features; the container may move to any
    HA version (ADR 0006).
  - **D9:** the **official Orca logo**, like the old integration (ADR 0009).
    Done: the four images from home-assistant/brands
    `custom_integrations/orca` are in `custom_components/orca_heatpump/brand/`,
    and ha-dev serves them for `orca_heatpump`.
- **Local only:** no remote repositories for now.
- The redaction of `2_NOVO_GESLO_PGDT` in the catalog and the deletion of
  the old `orca` config entry stand.

### Done

- Read `PLAN.md` and the workspace README. No pump access in this phase.
- `git init` (branch `main`, local only). First commit: `.gitignore`,
  `PLAN.md`, `research/moja_orca_catalog.json`.
- Repository files: `LICENSE` (MIT, both copyright lines), `README.md`
  stub, `CREDITS.md`, `CLAUDE.md` (agent rules from §2 and §10), `hacs.json`
  (minimum 2026.11.0).
- Tooling:
  - `pyproject.toml`: ruff (HA core's rules), mypy strict (plus HA's extra
    checks, including `explicit-override`), pytest, coverage, and the
    `dev` and `ci` dependency groups
  - `.pre-commit-config.yaml`: ruff, ruff-format, codespell, check-json,
    check-yaml, zizmor, mypy
  - `.github/workflows/ci.yaml`: lint, hassfest, HACS, and tests on HA
    minimum, stable and beta; weekly on beta and dev. 100% coverage
    required for `client/`. Actions are pinned to commit SHAs.
  - `.github/dependabot.yml` keeps the actions current.
  - `tools/ci_ha_version.py` maps a CI channel to an HA version.
- Package skeleton: `custom_components/orca_heatpump/` (`manifest.json`
  with `config_flow: false` until P3, `const.py`, `quality_scale.yaml` all
  `todo`) and `client/` with `py.typed`.
- Tests: `tests/client/test_isolation.py` (the client never imports HA,
  ADR 0003) and `tests/components/orca_heatpump/test_manifest.py` (HA finds
  the integration; no requirements, ADR 0005).
- ADRs 0001–0011 in `docs/decisions/`.
- D6 determined (ADR 0006).
- Dev HA: deleted the old `orca` entry through the REST API; added debug
  logging for `custom_components.orca_heatpump`.
- ha-dev (§4.3): mounts this repo and the integration, adds
  `host.docker.internal`, new `test` and `lint` commands, `hassfest`
  defaults to `orca_heatpump`, and the entrypoint installs the `dev` group
  from this repo's `pyproject.toml`. Container recreated (`rm` + `up`).
  `../ha-dev/README.md` and `../README.md` updated.

### Verified

| Check | Where | Result |
|---|---|---|
| `ha-dev.sh test` | container (HA 2026.11.0.dev0) | 2 passed, coverage 100% |
| `mypy` (strict) | container | no issues, 11 files |
| `ha-dev.sh lint` (all hooks) | container | all passed |
| `ha-dev.sh hassfest` | container | 1 integration, 0 invalid |
| CI test recipe | throwaway container: fresh venv, `homeassistant==2026.11.0b1` from PyPI, plugin from the `2026.11.0b1` tag | mypy clean, 2 passed, client coverage 100%, ~40 s |
| `ci_ha_version.py` | host, live PyPI | minimum 2026.11.0, stable 2026.10.4, beta 2026.11.0b1, dev |
| Entrypoint `dev` group | container log | `hypothesis==6.170.1` installed |
| HA discovers `orca_heatpump` | container log | yes |

### Not verified, caveats

- The GitHub workflow has never run on GitHub; nothing is pushed until CP3.
  The hassfest and HACS actions were not run; hassfest was checked with the
  container's copy instead.
- Until 2026.11.0 is on PyPI, CI's `minimum` job can't install it and the
  `stable` job tests 2026.10.4, below our minimum. Both resolve themselves
  on 2026-11-04.
- The pytest run shows 5 deprecation warnings from HA's dependency
  `backoff`, not from our code.
- An aborted `git log -S` over HAcore (a `blob:none` partial clone) may
  have fetched some git objects into `HAcore/.git`. The working tree is
  unchanged (`git status` clean). I then used the release tags on GitHub
  instead.

## Before CP3 (collected as I go)

- `PLAN.md` will be public. It contains the pump's LAN address, its default
  login and details of your house's setup. Decide whether to publish it
  as is.
