# 0001. Integration domain `orca_heatpump`

Status: Accepted (user, 2026-10-30)

## Context
The old integration, orca-energy-ha, uses the domain `orca`. Reusing it would
make the rewrite a drop-in replacement, but it would also mix up the two
projects, collide in `custom_components/`, and commit us to its entity
model.

## Decision
The domain is `orca_heatpump`, following HA core's `nibe_heatpump`.

## Consequences
- Both integrations can be installed at once. Two integrations polling one
  pump exhaust its few sessions, so the config flow warns when an `orca`
  entry for the same host exists, and a repair issue stays open while both
  are loaded (`PLAN.md` §7.3).
- No shared files or entity IDs with the old integration (see ADR 0008).
