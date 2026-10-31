# 0009. Neutral heat pump brand icon

Status: Proposed (default from `PLAN.md` §3; confirm at CP0)

## Context
HA shows an integration's icon and logo in the UI. Custom integrations can
ship them in `custom_components/<domain>/brand/` (supported in 2026.10 and
later). The "Orca" logo is Orca Energija's trademark.

## Decision
Ship a neutral heat pump icon of our own in
`custom_components/orca_heatpump/brand/`, no Orca logo without permission.
The file names are the ones HA accepts (`homeassistant/components/brands/const.py`):
`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png` and their `dark_`
variants; missing variants fall back to `icon.png`.

## Consequences
- No trademark issues.
- The HACS action's `brands` check expects an entry in the
  home-assistant/brands repository; CI skips that check for now. Revisit
  at P7, when the icon exists and we see what the current HACS action
  accepts.
