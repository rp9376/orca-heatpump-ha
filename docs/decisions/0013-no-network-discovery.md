# 0013. No network discovery

Status: Accepted (user, CP1, 2026-11-01)

## Context
The display has no mDNS service, and the API exposes no MAC or hostname
(R3, R13). Its MAC vendor prefix (00:0A:5C) is Carel's, so a DHCP matcher
could find it, but it would also match other Carel equipment.

## Decision
No discovery. The user enters the host in the setup flow. The display is
expected to keep a fixed local IP (a static address or a DHCP
reservation); if it changes, the reconfigure flow updates the host.

## Consequences
- The quality scale rules `discovery` and `discovery-update-info` are
  `exempt`, with this ADR as the reason.
- Config entries have no unique ID. `PLAN.md` §7.3 had the host as a fallback,
  but Home Assistant's rules exclude an IP address or a changeable host name
  as a unique ID (quality scale review, 2026-11-05). Entries are told apart by
  their normalised host instead (lower case, no default port), checked in the
  user and reconfigure flows. An IP and a host name of one display can't be
  recognised as the same; the README says so.
- The README tells users to give the display a fixed IP.
