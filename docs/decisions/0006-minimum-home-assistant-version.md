# 0006. Minimum Home Assistant version: 2026.11.0

Status: Accepted (user, 2026-10-31), with a latest-only policy

## Context
`PLAN.md` §3 asks for the oldest HA release that has every API we use, and
at most the current stable release. Users lag behind on updates, but we
won't carry deprecated code.

Checked on 2026-10-31 against the release tags on GitHub (2026.10.4,
2026.11.0b0, 2026.11.0b1) and HAcore at `9ba6491` (dev, 2026.11.0.dev0):

| API | First release |
|---|---|
| Climate and water heater `native_*` temperatures (`native_temperature_unit`, `native_current_temperature`, `native_target_temperature[_high/_low]`); the old names are deprecated until 2027.11 | **2026.11** (absent in 2026.10.4, present in 2026.11.0b0) |
| `pytest-home-assistant` (test-only; ADR 0011) | 2026.11 |
| Python 3.14.2 | 2026.10.x already requires it |
| Local brand images in `custom_components/<domain>/brand/` | ≤ 2026.10 |
| `probatio` (replaces voluptuous) | ≤ 2026.10 |
| `ConfigEntry.runtime_data`, device and exception translations, icon translations, reconfigure flow, event entities, coordinator `config_entry` | 2024–2025 |

The `native_*` API is the only one newer than 2026.10. Climate and water
heater are core platforms of this integration.

## Decision
The minimum is **2026.11.0**, set in `hacs.json`.

The user added a policy (2026-10-31): **no backward compatibility.** The
integration is built, tested and used only with the latest Home Assistant
and should be as future-proof as possible:
- Use the newest HA APIs and conventions, including 2026.11 features. Never
  write compatibility code for older releases.
- Raise the minimum whenever a newer release brings something we use.
- The ha-dev container may move to any HA version we need (a newer
  HAcore commit, tag or the release branch).

## Consequences
- Until 2026.11.0 ships (due Wednesday 2026-11-04), the minimum is newer
  than the current stable release (2026.10.4). The user accepted that.
- Users on older releases must update HA first; HACS enforces this.
- CI's `minimum` channel reads the version from `hacs.json`
  (`tools/ci_ha_version.py`). It fails until 2026.11.0 is on PyPI; nothing
  runs in CI before CP3 anyway.
- Raising the minimum is a deliberate change to `hacs.json` (the
  `minimum` CI job catches accidental use of newer APIs) with a CHANGELOG
  note.
