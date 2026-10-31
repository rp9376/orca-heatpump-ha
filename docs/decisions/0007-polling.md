# 0007. Polling: one coordinator, 30 seconds

Status: Proposed (default from `PLAN.md` §3; confirm at CP0)

## Context
The pump only answers polls; there is no push. The old integration polls
every 30 s without complaints about load. HA doesn't allow user-configurable
polling intervals.

## Decision
One `DataUpdateCoordinator` per config entry, polling every 30 s. Each poll
reads all tags in as few requests as the pump allows (batch size from R11).
The interval is a constant, not an option.

## Consequences
- One session, one lock, one poll: no concurrent requests to the pump.
- Values are up to 30 s old. Users who want faster updates can call
  `homeassistant.update_entity`.
- Revisit only if research (R11) shows load problems.
