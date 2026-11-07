# Changelog

## 1.0.0b1

First release: a rewrite of [orca-energy-ha](https://github.com/Tomasinjo/orca-energy-ha),
not an update of it. There is no automatic migration; see "Moving from
orca-energy-ha" in the README.

### Added

- All 45 wiring schemas of the manufacturer: up to three heating circuits (mixing or
  direct), hot water, solar collectors and a buffer tank, each read from the pump.
- A climate entity per circuit, also without a room sensor, with cooling modes; a water
  heater; sensors, numbers, selects and switches for what the display offers users,
  with the manufacturer's ranges. Installer settings are read-only.
- Alarms as a sensor, problem binary sensors and an event entity.
- A sensor wired to the unused solar input of a pump without solar is detected and shown.
- Weekly timer programmes shown on the timer selects.
- A ready-made dashboard with a live system diagram, built-in cards only, in English
  and Slovenian.
- One login on the display, always logged out. Recovery from refused logins, expired
  sessions and display restarts without a reload.
- Setup, reauthentication, reconfiguration and options flows; diagnostics; repair
  issues; English and Slovenian.

### Safety

- Every write is checked against the catalog before anything is sent, skipped when
  unchanged, and read back.
- Power limits are read-only unless you allow changing them, and always stay within
  the manufacturer's range.

### Known limitations

- Eco goes back to Normal by itself on the tested pump; see the README.
- The system on/off switch is disabled by default.
- No alarm reset, and weekly timer programmes can't be edited; see `docs/backlog.md`.
