# 0010. Entity model

Status: Proposed (structure from `PLAN.md` §8; finalised at CP1)

## Context
The old integration's entity set grew around one setup and crashed on
others. The new one must fit all 45 circuit schemas, and the research in
Phase 1 decides which tags mean what.

## Decision
The proposal in `PLAN.md` §8, in outline:

- One main device for the heat pump and one sub-device per present element
  (each heating circuit, hot water, solar, buffer).
- Entities only for elements the topology says exist; availability then
  follows each value.
- Unique IDs `{base}_{catalog_key}`, with the circuit number (never its
  name) in circuit-scoped keys; `base` is the hardware ID from R3, else the
  config entry ID.
- Alarms are first-class: an overall problem sensor, per-alarm sensors,
  the active alarm text and an event entity.
- Installer settings are never writable (`PLAN.md` §10).

Final keys, names and the enabled-by-default set come out of R7–R9 and are
written here at CP1.

## Consequences
- Unique IDs are permanent from 1.0 (`PLAN.md` §7.3a), so the keys must be
  right before the first release.
- Every entity of the old integration gets a counterpart or a documented
  reason for removal (parity list from research D).
