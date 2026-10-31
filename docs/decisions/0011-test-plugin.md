# 0011. Test with HA's pytest-home-assistant, taken from the core tag

Status: Proposed (deviates from `PLAN.md` §4.3; confirm at CP0)

## Context
Tests must run in the ha-dev container and in CI. `PLAN.md` §4.3 says CI
uses a pinned `homeassistant` + `pytest-home-assistant` pair from PyPI, and
falls back to `pytest-homeassistant-custom-component` if the plugin isn't
on PyPI for our HA version.

Findings on 2026-10-31:
- `pytest-home-assistant` is **not on PyPI** (404). HA split it out of
  core's `tests/` on 2026-10-17 into `packages/pytest-home-assistant`, so it
  first ships with 2026.11. Core has no workflow that publishes it.
- It **is** in the 2026.11.0b0 and b1 tags (not in 2026.10.4).
- `pytest-homeassistant-custom-component` (the plan's fallback) is at
  0.13.375, which pins `homeassistant==2026.10.4`. It has no 2026.11
  build, so it can't test an integration whose minimum is 2026.11
  (ADR 0006).
- The two plugins import from different modules (`pytest_homeassistant`
  vs `pytest_homeassistant_custom_component`). The HA plugin's README says
  not to install them together.
- The container already has `pytest-home-assistant`, installed editable from
  `HAcore/packages/`.

## Decision
Use HA's `pytest-home-assistant` everywhere. CI installs `homeassistant`
from PyPI at the version under test, plus `pytest-home-assistant` from a
shallow clone of the core repository at the matching tag (core tags every
release with its exact version). The `dev` channel installs both from the
`dev` branch. The plan's fallback is not used.

## Consequences
- One plugin and one import path in the container and in CI; no shim.
- The pair always matches exactly, because both come from the same release.
- CI clones core (depth 1) per test job, which costs some time.
- Verified locally on 2026-10-31: a fresh Python 3.14 venv with
  `homeassistant==2026.11.0b1` and the plugin from the `2026.11.0b1` tag
  passes mypy and pytest (see `docs/progress.md`).
- When HA publishes `pytest-home-assistant` on PyPI, switch CI to the
  PyPI pin and drop the clone.
- If the user prefers the plan's fallback instead: phcc needs a 2026.11
  build first, and tests would need an import shim between the two
  plugins.
