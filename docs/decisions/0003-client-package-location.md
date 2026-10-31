# 0003. Protocol client inside the integration, independent of HA

Status: Proposed (default from `PLAN.md` §3; confirm at CP0)

## Context
HA wants integrations to be thin: protocol parsing and device logic belong
in a separate library, normally on PyPI. Publishing a library needs the
user and adds a release process; v1 doesn't need it.

## Decision
The protocol code lives in `custom_components/orca_heatpump/client/`, a
package with no `homeassistant` imports, its own tests and `py.typed`.

## Consequences
- It can move to PyPI (e.g. `pyorca-heatpump`) later with only import
  changes. Publishing is out of scope for v1.
- `tests/client/test_isolation.py` fails if a client module imports
  Home Assistant or reaches outside the package.
- HACS ships the client with the integration; there is nothing extra to
  install.
