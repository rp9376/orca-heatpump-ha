# Progress

**Phase 0 done. Stopped at checkpoint CP0 (2026-10-31).**
Next: Phase 1 (research), once you've confirmed the decisions below.

## CP0: what I need from you

1. **Confirm the default decisions** D2, D3, D4, D5, D7 and D9 as written
   in `docs/decisions/` (D1 and D8 are yours already; D10 is settled at
   CP1).
2. **D6, the minimum HA version: 2026.11.0** (ADR 0006). The `native_*`
   temperature API for climate and water heater is new in 2026.11; it is
   missing from 2026.10.4. That conflicts with the plan's "at most the
   current stable release" until 2026.11.0 ships (due Wednesday 2026-11-04,
   well before our first beta). The alternative is 2026.10 with the
   temperature API that 2026.11 deprecates. I recommend 2026.11.0.
3. **Test plugin: a deviation from §4.3** (ADR 0011). `pytest-home-assistant`
   is not on PyPI, and the plan's fallback,
   `pytest-homeassistant-custom-component`, has no 2026.11 build (its
   newest pins HA 2026.10.4). So CI installs HA from PyPI and the plugin
   from the matching core release tag on GitHub. The container uses the
   same plugin, so tests are identical in both places. I recommend keeping
   this.
4. **Git author.** No global git identity is set, so the repo has a local
   one: `rp9376 <rp9376@student.uni-lj.si>`, as in your orca-energy-ha
   commits. It becomes public at CP3. Keep it, or use another, e.g. your
   GitHub noreply address? History can still be rewritten, since nothing is
   pushed.

FYI, no action needed:
- In `research/moja_orca_catalog.json` I replaced the observed value of
  `2_NOVO_GESLO_PGDT` ("Change password", the 4-digit service password
  input) with `REDACTED` before the first commit; it might be the service
  code. The raw HARs still have everything.
- The old `orca` config entry is **deleted** from the dev HA (§2.2), so
  nothing polls the pump. To test the stop-gap branch again, add the old
  integration again in the UI, and never alongside an `orca_heatpump` entry
  for the pump.

## Done in Phase 0

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

## Verified

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

## Not verified, caveats

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
- `CREDITS.md` lists the contributors named in the plan. They are not yet
  verified against the old repository's PR authors (research D in P1).

## Before CP3 (collected as I go)

- `PLAN.md` will be public. It contains the pump's LAN address, its default
  login and details of your house's setup. Decide whether to publish it
  as is.
- Verify the GitHub handles in `CREDITS.md`.
- Git author (question 4 above).

## Next: Phase 1 (§6.2)

1. Pre-flight: no HA instance polls the pump (no `orca` or `orca_heatpump`
   entry exists now).
2. Lead's first live session: read all 1,767 known tags in passes until two
   agree (at most 4), log out in a `finally`, save the raw passes and a
   merged dump. Then save the display's static console files.
3. Research subagents A–D in parallel (offline).
4. Lead's live experiments from C's script, then CP1.
