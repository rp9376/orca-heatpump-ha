# Orca Heat Pump for Home Assistant

A Home Assistant integration for [Orca Energija](https://www.orcaenergy.eu/)
heat pumps with a networked touch display. It talks to the display over your
local network; no cloud account is needed.

> **Status: in development, not usable yet.** There is no release. If you
> need an Orca integration today, use
> [orca-energy-ha](https://github.com/Tomasinjo/orca-energy-ha).

## Goals

- Every circuit configuration the pump supports: heating circuits 1–3
  (mixed or direct), hot water, solar, buffer tank and cooling.
- Safe with the pump's small login limit: one session, always logged out.
- Alarms as first-class entities and events.
- English and Slovenian.

## Requirements

- Home Assistant 2026.11 or newer.
- An Orca heat pump whose touch display is reachable on your network.

## Credits

This integration is a rewrite inspired by, and partly derived from,
[orca-energy-ha](https://github.com/Tomasinjo/orca-energy-ha) by Tom Kern
(@Tomasinjo) and its contributors. See [CREDITS.md](CREDITS.md).

Not affiliated with Orca Energija d.o.o., Carel or EXOR. "Orca" is a
trademark of Orca Energija d.o.o.

## License

[MIT](LICENSE)
