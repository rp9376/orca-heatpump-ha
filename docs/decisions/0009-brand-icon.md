# 0009. Official Orca logo as the brand icon

Status: Accepted (user, 2026-10-31); replaces the plan's default of a
neutral icon

## Context
HA shows an integration's icon and logo in the UI. Custom integrations can
ship them in `custom_components/<domain>/brand/`, and HA serves those before
looking at the home-assistant/brands repository. orca-energy-ha shows the
official Orca logo: Tom Kern added it to home-assistant/brands under
`custom_integrations/orca` (commit `b8100c975d`, PR #5647, 2024-07-09). Our
domain `orca_heatpump` has no entry there.

## Decision
Use the official Orca logo, like the old integration. The four images from
`custom_integrations/orca` at `b8100c975d` ship unchanged in
`custom_components/orca_heatpump/brand/`:

| File | Size |
|---|---|
| `icon.png` | 256 × 256 |
| `icon@2x.png` | 512 × 512 |
| `logo.png` | 494 × 128 |
| `logo@2x.png` | 987 × 256 |

HA accepts these names plus `dark_` variants
(`homeassistant/components/brands/const.py`); without dark variants it falls
back to the light ones.

## Consequences
- Verified on 2026-10-31 in ha-dev: `/api/brands/integration/orca_heatpump/`
  serves `icon.png` and `logo@2x.png` byte-identical to the repo, and
  `dark_icon.png` falls back to `icon.png`.
- The logo is a trademark of Orca Energija d.o.o. It is used the way
  orca-energy-ha uses it; `CREDITS.md` and the README say so, and that the
  project is not affiliated with Orca Energija.
- The HACS action's `brands` check looks at home-assistant/brands; CI skips
  it because the images ship locally.
