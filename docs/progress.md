# Progress

**Phase 1 (research) in progress.** CP0 passed on 2026-10-31.

## CP0 outcome (user, 2026-10-31)

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

## Phase 1 (research), §6.2

1. **Done, 2026-10-31 20:23–20:25.** Lead's first live work with
   `tools/orca_probe.py` (allowlist in code, lock, backoff, logout in a
   `finally`). Before it, no HA instance polled the pump.
   - Static console files, no login: 20 files in `research/captures/console/`.
   - Full dump, one session: login at the first attempt, 2 passes agreed,
     logout `#S_OK`. 708 tags `S_OK`, 1,059 `E_UNKNOWNTAG`. One batch of
     150 tags got HTTP 408 in both passes (request line 4,374 chars; the
     longest that worked was 3,946); re-read in batches of 50, it worked.
     Raw passes and the merged dump: `research/captures/2026-10-31_full_dump/`.
   - First findings: `research/findings.md`.
2. **Running:** research subagents A (catalog), B (manuals), C (protocol and
   live-test script), D (history and parity list), offline, writing
   `research/catalog_draft.md`, `manual_facts.md`, `protocol.md`,
   `requirements.md`.
3. Next: review C's live-test script against the allowlist, run it (R1–R4,
   R11, R13, R14), write `research/findings.md` (R1–R15), finalise the
   catalog, propose the entity and topology model, then CP1.

The sanitised JSON test fixture of our dump is still to do: the raw dump
stays in `captures/` until its values are checked for MAC/IP/serial data.
