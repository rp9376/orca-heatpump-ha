# 0005. No runtime dependencies

Status: Accepted (user, 2026-10-31)

## Context
Every requirement in `manifest.json` is something HA must install and keep
compatible across releases. The old integration's requirements (aiohttp,
PyYAML, aiofiles, pydantic) also fail hassfest.

## Decision
`requirements` stays empty. The integration uses only HA itself, the
aiohttp that HA ships, and the standard library.

## Consequences
- Simplest install, nothing to break on HA upgrades.
- Test-only tools (hypothesis, pytest-cov, mypy) are dev dependency groups
  in `pyproject.toml`, never runtime requirements.
- `tests/components/orca_heatpump/test_manifest.py` checks that
  `requirements` is empty.
