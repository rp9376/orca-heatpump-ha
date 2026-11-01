# Progress

**Phase 1 (research) done. Stopped at checkpoint CP1 (2026-11-01).**
Next: Phase 2 (client package and emulator) once you've approved.

## CP1: what I need from you

The research, catalog scope and entity model to approve:
- `research/findings.md`: R1–R15 answered, with evidence; start with its
  "Summary for the design" and "Corrections to PLAN.md assumptions".
- `research/catalog_draft.md`: the tag catalog, with the lead's corrections
  in its §10.
- `docs/entity-model.md`: topology rules, devices, every entity, the climate
  and water heater mappings, alarms. Items marked [CP1] are below.

Decisions (my recommendation first):
1. **Constant-temperature circuits:** climate with HVAC modes only, plus a
   number "Flow temperature" (= `2_Max_VF_MKn`) on the circuit, as you use
   it today. Recommended over putting the flow setpoint into the climate's
   target temperature, which HA treats as a room temperature.
2. **Power limits** (`2_Max_moc_TC_pri_OGR/SV/HLAJ`, quiet-mode limit):
   writable numbers with the manufacturer's ranges (40–100 %, cooling
   16–100 %), disabled by default. They are service-level settings, and an
   out-of-range write once restarted a user's controller (#20), so the
   alternative is read-only.
3. **Cooling:** no tag says whether a pump can cool. Offer cool and
   heat/cool by default, with an options switch to hide them on heating-only
   installations? Or hide them by default?
4. **Password and code tags:** never read or expose any tag whose name
   contains `GESLO`, `KODA` or `KODE` (14 on our pump). This extends
   `PLAN.md` §10.
5. **Circuit modes 4 (by input) and 5 (manual)** show as HVAC `auto` and can
   only be set through the raw mode select. No presets on the climate: the
   operating programme (normal / holiday / party / ECO) is global, so it is a
   select on the heat pump device.
6. **Session slot count (C's Session 4):** measuring it needs several
   sessions open at once, which breaks the one-session rule. I recommend
   skipping it: the design never needs a second session, and a leaked
   session frees itself within 3 minutes.
7. **DHCP discovery** on the Carel MAC prefix 00:0A:5C, confirmed by login:
   build it in P3 (Gold "discovery" rule)?

For your information:
- Your MK2 (radiator) circuit reports no flow sensor (`2_Temp_VF2` = -9999,
  `2_Tipalo_VF2` = 0). Expected because it's switched off, or worth checking?
- Your controller runs program build 61 from 2016-12-12, the oldest of the
  three known pumps, although the pump was commissioned in October 2026.
- The two alarms you've seen are codes 4 "Ni pretoka" and 5 "Okvara
  pretočnega stikala" (flow switch failure).

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
