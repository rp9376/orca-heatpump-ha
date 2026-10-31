# 0008. No migration from orca-energy-ha

Status: Accepted (user, 2026-10-30)

## Context
Users of orca-energy-ha (domain `orca`) could have their config entries and
entity IDs carried over. The new entity model, unique IDs and domain differ
too much for that to be clean (ADR 0001).

## Decision
No migration. Users remove orca-energy-ha and set this integration up fresh.
Config entries start at `VERSION 1`; migrations exist only for our own
future versions (`PLAN.md` §7.3a).

## Consequences
- Simpler code and no legacy unique IDs.
- Users lose entity history and must update dashboards and automations.
  The README explains the move step by step, and P7 tests it end to end.
- The config flow warns when an `orca` entry for the same host exists
  (ADR 0001).
