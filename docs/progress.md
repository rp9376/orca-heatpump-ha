# Progress

**Phase 7 done on 2026-11-07: stopped at CP3. Nothing is pushed or published.** The
user decides the points below and publishes.

## CP3 report (2026-11-07)

### Where things stand

- **Public since 2026-11-07:** the user pushed the full history to
  `rp9376/orca-heatpump-ha`. No release yet.
- **Version `1.0.0b1`.** Changelog, README, supported setups, backlog, contributing
  guide, CI and release workflows, issue templates and HACS settings are in place.
- **Checks on this commit's code:** lint, ruff, mypy strict and zizmor pass, hassfest
  reports the integration valid, 1,115 tests and 739 snapshots pass, coverage is 100 %
  (1,525 statements, 292 branches). The one test warning comes from the `backoff`
  package, not from this code.
- **"Moving from orca-energy-ha", end to end in the dev HA, emulator only.** The old
  integration set up, then this one: the warning appears before any login, continuing
  works, and a repair issue opens. Removing the old entry closes the issue. Adding the
  same display as `127.0.0.1:80` aborts as already configured. Removing the test entry
  leaves no entities behind. The first run of this test found a real bug: the warning
  came after the login, which the old integration's open sessions could refuse. Fixed
  in `809d5fd`.
- **The real pump:** dev HA restarted on the release code and polls normally. Every
  writable setting equals the baseline of 7 Nov apart from the system switch, on as
  agreed. No alarm. Power limit option off. No warning from `orca_heatpump` in the log.
  The log's warnings about deprecated properties all come from the old `orca` component
  in the dev HA, which the move test loaded.
- **The tests need nothing outside git:** all 1,115 pass from a throwaway clone. The
  `research/` folder has to stay public, because the tests load two files from it.

### History audit before publishing (user's request, 2026-11-07)

The user will push the full history if nothing critical is in it. **Nothing is.**

- **Scope:** every file version in all 62 commits at that point (383 blobs), plus commit
  messages and author fields.
- **Real values:** the dev HA password, every session token and cookie in the raw
  captures, and the dev HA's home location. None found. The pump's serial number isn't
  labelled in any capture, so it was never there to copy.
- **Patterns:** login tokens, API keys, private keys, logins in URLs. None found.
- **gitleaks 8.24.0, offline, as a second opinion:** 12 hits, all false positives (the
  entity key `heater_stageN_outdoor_temp` and one tag name).
- **Code and password tags in the fixtures:** every value is redacted or absent.
- **Never committed:** captures, HAR files, databases, `.storage` files.
- **Images:** logos and dashboard screenshots, no metadata, nothing personal.

Public but not secret: the display's private LAN address (`PLAN.md`, older versions of
`research/protocol.md`), the manufacturer's default login, the author address (already
on the public fork `rp9376/orca-energy-ha`) and this log. This can't prove the absence
of a value nobody knew to look for, such as a cloud password that was never given to the
agents.

### Login limits on the real display (user's request, 2026-11-07)

With the dev HA running, using only `login` and `logout`, one request at a time. Raw
answers are in `research/captures/2026-11-07_login_limits/`. The user accepted a power
cycle as the worst case for the full-display test; it wasn't needed.

- **Wrong password:** `E_PASS_DONT_MATCH`, and the real form says the login was rejected.
- **Wrong username:** `E_USER_DONT_EXIST`, which the code read as "not an Orca display".
  **A real bug, fixed.** Neither wrong login locks the display.
- **Full display:** three sessions fit, the next login gets `E_TOO_MANY_USERS`, and the
  form says so. An open session keeps polling (15:06:06 and 15:06:36 succeeded). Logout
  frees a slot at once.
- **Setup while full:** `setup_retry` with a clear reason, then loaded by itself 21 s
  after the slots were freed. No entity changed.
- **My mistakes on the way:** the first attempt got HTTP 400 from a script bug
  (`//cgi/login`), not a lockout. The script's "last poll" check didn't move either; the
  log proved the polls succeeded. The emulator now gives these answers and allows three
  sessions.

### Options menu (user's decision, 2026-11-07)

The room sensor, solar and buffer dropdowns are gone (ADR 0014). I first told the user
they had no real use. That was wrong: @sinjorgo depended on the solar one for a sensor
wired to the solar input (orca-energy-ha #30). That case is now detected from the
input's value.

Looked at in a browser for the first time, against the dev HA: the options dialog in
English, and the setup form in English and Slovenian (opened, not submitted). All three
render correctly.

### Diagram rule (user's report, 2026-11-07)

The user toggled the underfloor circuit and saw the diagram change live, which also
settles the open check on redrawing without a reload. It showed flow to the hot water
tank at 0 % power. The diagram drew what the pump reported, but from the wrong rule:

- The valve rests on hot water when nothing demands heat. It did for one poll after the
  toggle (15:27:00–15:27:30), with the unit off, and for hours overnight.
- The circulation pump keeps running between compressor runs (6.1 of 39 logged hours).
- At a start the power reads 70 % up to 3.5 minutes before the unit reports heating.

Pipes now animate only with the circulation pump on, the unit not off and power above
0. Circuit pipes also need the valve on space heating, which removes the underfloor pipe
staying orange during hot water runs (2.5 logged hours), and the supply pipe turns blue
when cooling. The stub at the valve is neutral grey. So at a start the label can read
70 % with no flow yet, for up to 3.5 minutes.

I had told the user the pipes would stop when the unit stops. That was wrong for the old
rule: the data above was already there to check.

Seen on the real pump with a page left open and no reload: the unit stopped at 15:44:30
and only the grey stub stayed; it started at 15:49:30 and the pipes came back. A cooling
run and a real hot water run with this rule are covered by tests only so far.

The radiator box now matches the underfloor one at the user's request: flow temperature
and set point, with the flow line empty when there is no value, as on this pump, which
has no radiator flow sensor. The mixing valve sits on the split with its opening beside
it. Seen on the real page in light and at phone width in dark, in English; the Slovenian
files come from the same generator, with no diagram text of their own.

### Heat pump temperature renamed (user, 2026-11-07)

"Water temperature" could be read as hot water, so `2_Poti1` follows the app's "HP
temperature" / "Temperatura toplotne črpalke". It is named "Temperature" on the Heat
pump device, as the buffer tank's already is, to avoid "Heat pump Heat pump
temperature". The target and the "too low" alarm changed with it. Unique IDs are
unchanged. Its logged behaviour (142 hours) fits water leaving the heat pump: it follows
its target to either circuits or tank, and drifts to about 24 °C when stopped.

### Decisions for the user

1. **Pushing.** Done by the user: this machine holds no GitHub login, and I never handle
   tokens. The remaining steps are in `docs/repo-setup.md`.
2. **Release.** `v1.0.0b1` as a pre-release, installed through HACS as a custom
   repository. The HACS default store can wait until the beta has been used.
3. **Tom Kern.** Draft in `.scratch/note-to-tom-kern.md`, not sent. Send it, change it
   or skip it; it links to the repository, so it goes after the push. `<your name>` is
   a placeholder.
4. **PyPI:** nothing to do. The client is inside the integration (ADR 0005).

### Not verified

- **CI is green on GitHub since `485a427` (2026-11-07):** Lint, hassfest, HACS
  validation and the tests on minimum, stable and beta all pass. HACS warns only that the
  manifest has no categories. On the first push HACS validation failed only on the
  missing repository topics. All three test jobs failed at
  install: the plugin's folder is `pytest-homeassistant` in the 2026.11.0 tag and
  `pytest-home-assistant` on dev, and CI used the dev name. With that fixed, a fresh
  Python 3.14 venv with `homeassistant==2026.11.0` showed `mypy` lacked the PyYAML stubs
  it gets from the container; with those added, mypy and all 1,137 tests pass there, at
  100 % coverage. That was the first run against the release rather than dev.
- **The release workflow has never run.**
- **Only one real pump:** schema 23. The other 44 schemas run on synthetic data. Not
  tested live: a room sensor, cooling in operation, a third circuit, a buffer tank.
- **Out-of-range refusal:** tested on the emulator only, deliberately (#20).
- **Eco:** the pump goes back to Normal by itself, a known limitation by the user's
  decision.
- **Moving:** tested on the emulator, by removing the old entry. Disabling it instead
  is covered by tests but wasn't run end to end.
- **Refused logins while running:** the repair issue raised when a running integration
  keeps being refused needs its session to die while the display is full. Emulator only,
  though it reads the same recorded answer.
- **Solar input temperature:** never run on a real pump with a wired input; it rests on
  the reading reported in orca-energy-ha #30.

## Dashboard (user's request, 2026-11-05)

`docs/dashboard/` (English and Slovenian), generated by `tools/build_dashboard.py`,
deployed to the dev HA as "Heat pump" in the sidebar.

- Built-in cards only: Home Assistant 2026.11 has everything needed, so nothing to
  install and no third-party code. Custom cards were considered (mushroom,
  mini-graph-card, button-card, apexcharts-card) and not needed.
- A live system diagram (picture-elements over inlined SVG), sections with tiles,
  gauges and trend graphs, a Trends view with history and the alarm log.
- Mode buttons on the circuits and hot water, added once the write test had passed.
- Tests: the files are current, no custom cards, and every entity exists and is
  enabled by default on our pump.
- Checked with headless Chrome: dark, light, phone width, no card errors; the pipes
  animate (4 of 4 frames differ), on a temporary preview with the conditions removed,
  because the pump was idle. In this version conditions are evaluated through the
  backend, so a simulated state in the browser doesn't reach them. Since then, a page
  loaded while the pump was really heating showed the right pipes, and the user saw it
  change live (see the CP3 report).
- The Marketplace's first-run warning was left for the user; nothing was installed.
- Seen in the data, not a defect: about 40 outdoor unit starts a day, 3–4 an hour
  during the 12 heating hours (median run 12.5 min, pause 5 min, 3–5 Nov). Mentioned
  to the user.

## CP2 outcome (user, 2026-11-05)

1. The four setting changes were the user's own, made by hand. Resolved.
2. Spot check against the touch display: values check out.
3. Write test plan: **the user says when.** Do not start before that. Tier C not
   chosen yet.
4. System switch: stays, disabled by default (done). An existing registry entry keeps
   its state, so it is still enabled in the dev HA.
5. Alarm reset: left out of v1, in `docs/backlog.md`, and the README says to ask for
   it (done). The user prefers it that way: alarms usually mean someone must look at
   the heat pump.
6. Service-level settings: they stay writable and hidden as accepted at CP1, and
   underfloor circuits get no lower cap than the manufacturer's 60 °C (user agreed).
7. Limits below the manufacturer's minimum: no, the limits stay (ADR 0012).
8. Room setpoint range: the user has no sensor, and asked to use the old integration's
   limits or normal values. The old integration has 10.0–35.0 °C, step 0.1, and all
   recorded values fit, so the catalog keeps that. Not the manufacturer's data.

## CP2 report (2026-11-05)

### Where things stand
- The integration is complete: every platform, 45 schemas, fault and odd-value
  suites, docs. 1,107 tests, 100 % coverage of every module, ruff, mypy strict
  and hassfest clean.
- 69.7 hours of read-only polling on the real pump without a single failure
  (details under "Live checks so far").
- Three independent reviews ran. No critical or high findings; the write path
  held up. Their findings are fixed, except those listed below.
- The Phase 6 plan is ready: `docs/phase6-write-test-plan.md`.

### Decisions asked of the user (answered above)
1. **The four setting changes** (hot water power limit 65 → 75 %, underfloor flow
   setpoint 28 → 30 °C, minimum flow 24 → 25 °C, hot water switch-on difference
   6 → 7 °C): did the user make them? The old integration's history of "max power
   hot water" dates the first exactly. If not, find out who can write before any
   write test.
2. **Spot check** of values in Home Assistant against the touch display.
3. **Write test plan:** agree to it, pick from Tier C, and choose a time when the
   user is present.
4. **System switch category** (safety review L4). As an ordinary control,
   `switch.turn_off` on an area or device and voice assistants include it, so "turn
   everything off" would stop heating and hot water. Recommendation: entity category
   config, which excludes it from both and keeps it on the device page. Differs
   from the entity model accepted at CP1, so it's the user's call.
5. **Alarm reset left out of v1.** The plan allows the button only after a Phase 6
   test, and alarms are never provoked on purpose, so it can't be tested on demand.
6. **Service-level settings** (minimum/maximum flow, regulation, screed drying) are
   writable but hidden by default, as accepted at CP1; only power limits have an
   opt-in. Keep that? The regulation select also offers "room" on circuits without
   a room sensor, which is what the pump's own menu holds today for the radiators'
   cooling regulation, so it isn't filtered.
7. **Below the manufacturer's minimum:** the recorded Mono holds a heating limit of
   39 % (minimum 40 %). Can installers go lower, so the catalog minimum is wrong?
8. **Room setpoint range:** 10–35 °C comes from the older integration, not the
   manufacturer. If the display shows the allowed range, it would confirm it.

### Next steps after CP2
Phase 6 per the plan: first write, look at the raw answer and read-back timing, then
the tiers. Then Phase 7. The first live write settles how the client should treat
the write response and whether the read-back needs to wait.

### From the reviews: fixed
- **Password in errors** (M1): aiohttp's text holds the login URL; connection
  errors now name only the error type and status.
- **Partial writes** (M2): every value is checked before the first is sent; state
  refreshes after a failed write too.
- **Write response format** (M3): only an explicit per-tag error counts as failure;
  the read-back decides. The raw answer is logged at debug level.
- **Alarm reset** (M4): removed (decision 5).
- **Host validation** (L1): closes the one route to a never-call endpoint. Entries
  have no unique ID any more; `host` and `host:80` are one display (ADR 0013).
- **Cookie collision** (L2): cookie-free sessions, proven with a test that fails on
  a normal jar.
- **Closed client** (L3): no login after the final logout.
- **Fahrenheit** (L7): numbers are rounded to the pump's resolution.
- **§10 test** (L6): the never-writable list is enforced against the catalog.
- Repair issues clear themselves and say what changed; orphaned entities are
  removed (checked on the real registry: only the old button went, 123 → 122);
  stale values don't outlast an outage; temporary tag statuses count as no
  response; missing values are unknown rather than unavailable; heater stages need
  a heater; reauth and reconfigure test all five errors; README corrections.

### From the reviews: deliberately not changed
- A rewired pump is noticed at the next setup or reload, not while running; the
  dynamic-devices exemption now says so.
- No DHCP discovery (CP1). The display's DHCP host name was never checked; that
  would be the way in if this is ever revisited.
- No `configuration_url`: whether the display serves a useful page isn't verified.
- Device models are English: Home Assistant can't translate them.
- `**kwargs: Any` in the description helpers, and in the probe tool percent-encoded
  `..` and unencoded credentials: developer-only, left alone.
- `quality_scale.yaml` was reviewed before these fixes and not re-reviewed since.
  hassfest checks none of it for a custom integration.

### Not verified yet
- **Any write on the real pump.** All write behaviour so far is emulator-only.
- The reviewed code has run on the real pump only since 2026-11-05 19:44 UTC; the
  69.7 h run was on the code before the fixes. It keeps polling.
- The window 2026-11-01 20:44 → 2026-11-02 17:29 UTC can't be re-checked for
  off-beat refreshes (log rotated). Nothing wrote in it as far as is known.
- HACS validation and CI wait for a remote repository (CP3).

### Running now
The dev HA keeps polling the real pump every 30 s (one login, timers hourly). To
free the display: disable the entry in the dev HA, or `../ha-dev/ha-dev.sh down`.

## Phase 5 (hardening and review): record

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
- `quality_scale.yaml`: every rule done or exempt with a reason (exempt:
  action-setup, docs-actions/conditions/triggers, dependency-transparency,
  discovery, discovery-update-info, dynamic-devices). The independent review found
  three over-claims, since fixed.
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
- Tests at that point: 1,038. After the review fixes: 1,107, see the CP2 report.

### Live checks so far
- Startup with all platforms (19:44 UTC): 123 entities, polls 50–90 ms,
  timers read in 0.19 s, no warnings or errors from the integration.
- Six reloads of the live entry in a row, 20 s apart (19:58–20:01 UTC):
  each loaded, no refused login, no failed read, no warning or error, so
  no session leaks on the real display.
- **Long read-only run: 2026-11-02 21:32 → 2026-11-05 19:15 UTC, 69.7 h**
  (plan: at least 24 h), on the code as of commit `75de131`:
  - 8,369 polls, all successful; all 8,368 intervals exactly 30 s, so no
    gap and no off-beat refresh, which also proves nothing was written
    through Home Assistant. 70 hourly timer reads, all successful.
  - No warning or error from the integration, no refused login, no session
    renewal, no re-read records, no unknown values, no repair issue. Read
    time 61 ms median, 273 ms at most.
  - From the recorder: no enabled entity went unavailable or unknown.
    Outdoor 5.8–11.8 °C; hot water top 33.5–43.2 °C (setpoint 42); bottom
    22.2–41.1 °C; underfloor flow 21.8–27.9 °C (setpoint 28); collector
    5.2–36 °C; water 22.5–51.7 °C. All plausible.
  - Outdoor unit power reaches 75 % in hot water cycles (target 50.5 or
    44.5 °C) and at most 70 % in heating (target 30 °C): exactly the limits
    the pump holds now, 75 % and 70 %. An earlier note here said it exceeded
    them; that compared against the old 65 % from a fixture.
  - **Settings changed outside the integration since 2026-11-01 09:36**
    (user asked to confirm; investigated after they saw 75 % from 11:50 on
    1 Nov in the old integration's data):
    `2_Max_moc_TC_pri_SV` 65 → 75 % (between the 10:28 read and 20:44 on
    1 Nov), `2_Max_VF_MK1` 28 → 30 °C (2 Nov 21:08 local), `2_Min_VF_MK1`
    24 → 25 °C and `2_Diferenca_vklopa_SV` 6 → 7 °C (time unknown, entities
    disabled by default). Not this integration: the code running 10:42–20:44
    on 1 Nov (`fbbbc89`) has `PLATFORMS = []`, no services and no write call
    outside the client; the tools have no write endpoint and last touched
    the pump at 10:28; the 2 Nov change fell on the regular poll beat with
    no off-beat refresh. The log of 1 Nov 20:44 → 2 Nov 17:29 has rotated
    away, so that window's rhythm can't be re-checked.
  - The heat pump's target temperature reads 9.0 °C while the timer has heating
    off (evening to 07:00 UTC). That is the pump's own value.
  - The underfloor timer programme changed at 18:36 and 19:43 UTC on 3 Nov
    (all day → programme 4 → programme 2). The user did that in the app
    (confirmed); the integration followed it.
  - Earlier attempt (2026-11-01 19:44 → 2026-11-02 17:29 UTC) was cut short
    by the host suspending: 387 polls over about 3.5 h, none failed. After
    each wake the display had dropped the session and the client logged in
    again within the poll, with nothing going unavailable.

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
- Questions from this phase moved into the CP2 report.

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

