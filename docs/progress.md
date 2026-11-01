# Progress

**Phase 4 (platforms) in progress.** Phases 2 and 3 done on 2026-11-01;
CP1 passed the same day.

## Phase 4 (platforms): in progress

One commit per platform, each with en + sl names, snapshot tests for the
three real pumps (ours, Duo, Mono) and 100 % coverage.

- Done: binary_sensor, sensor, event (alarm raised/cleared), climate
  (thermostat with a room sensor and room-based regulation, else
  mode-only; CP1), water_heater, number (manufacturer ranges, box mode;
  power limits opt-in with the other form removed from the registry,
  ADR 0012).
- Next: select, switch, button (alarm reset, disabled until the Phase 6
  write test).
- Writes go through `async_write_values`: several values in order, one
  refresh. A climate mode is written before the circuit's enable.
- Names and defaults that depend on regulation (flow setpoint vs maximum
  flow temperature, curve settings enabled) are decided at setup; a
  regulation change shows after a reload. The climate's target follows
  regulation on every poll.
- **Real data below the manufacturer's minimum:** the Mono fixture holds a
  heating power limit of 39.0 % (minimum 40.0 %). Home Assistant shows it;
  writing it back would be refused. Ask the user at CP2 whether installers
  can set lower values (then the catalog minimum is wrong) or this is a
  leftover from older firmware.

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
