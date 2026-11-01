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
- The config entry's unique ID is the host (`PLAN.md` §7.3 fallback);
  reconfigure updates it together with the host.
- The README tells users to give the display a fixed IP.
