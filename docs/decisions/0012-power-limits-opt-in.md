# 0012. Power limits are an opt-in, guarded setting

Status: Accepted (user, CP1, 2026-11-01)

## Context
The heat pump's power limits are service-level settings:
`2_Max_moc_TC_pri_OGR` (space heating), `2_Max_moc_TC_pri_SV` (hot water),
`2_Max_moc_TC_pri_HLAJ` (space cooling) and `2_Max_moc_TC_TISJA` (quiet
mode). orca-energy-ha exposes the first three as writable numbers for
everyone, with a range of 10–100 %. The manufacturer's minimums are higher,
and in orca-energy-ha #20 an out-of-range value written by an automation
**restarted the controller**.

Manufacturer ranges (`research/moja_orca_catalog.json`, raw ×10):

| Limit | Range |
|---|---|
| space heating | 40.0–100.0 % |
| hot water | 40.0–100.0 % |
| space cooling | 16.0–100.0 % |
| quiet mode | 31.0–100.0 % |

## Decision
- A checkbox in the setup flow, **"Allow changing power limits"**, off by
  default and described as risky (wrong values can stop the heat pump). It
  is stored in the entry's options and can be changed in the options flow.
- Off: the four limits are read-only sensors.
- On: they are number entities (box mode, step 1 %), enabled by default,
  entity category config.
- Protection in code, independent of the UI:
  - the client rejects any write outside the manufacturer's range before
    anything is sent (`OrcaValueError`), for these and all other writes
  - the number entities carry the same min/max, so HA's action validation
    rejects out-of-range values too
  - unchanged values are never written; every write is read back
  - a test checks that each limit's catalog range equals the manufacturer's

## Consequences
- Users who never tick the box can't change service settings by accident,
  and automations can't push values the controller rejects.
- Turning the option on or off reloads the entry and swaps the sensors for
  numbers or back; the entities of the other form are removed from the
  entity registry, so nothing stale is left (`PLAN.md` §7.3a).
- The README documents the risk and the ranges.
- The minimums stay even though a pump can hold less (user, CP2): the recorded Mono
  holds a heating limit of 39 %. Such a value is shown, and can't be written back.
