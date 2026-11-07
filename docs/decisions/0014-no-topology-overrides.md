# 0014. No topology overrides

Status: Accepted (user, CP3, 2026-11-07)

## Context
The options menu had dropdowns to force each room sensor, solar and the buffer tank
present or absent, for pumps where detection is wrong. Nobody has needed them: detection
matched on all three pumps we have data for, and a real rewiring already raises a repair
issue.

Forcing an element on the emulator only adds what the pump doesn't have: a Solar
collectors device on a pump with circuit 3, a Buffer tank device with 7 entities on a
pump with none, and a room sensor that gives no setpoint.

One real user depended on the idea. On a three-circuit pump,
[@sinjorgo wired an external sensor to the unused solar input](https://github.com/Tomasinjo/orca-energy-ha/issues/30)
and lost its reading when solar stopped being detected. The manual override in
orca-energy-ha 2.4.0 brought it back, along with solar pump and solar heating entities
that mean nothing on that pump.

## Decision
No overrides; the options menu holds only the power limit permission.

The real case is detected instead. The solar input reads -9999 on both recorded pumps
without solar and 37.9 °C on the pump with the wired sensor, so a pump without solar
that reads anything but "not connected" on `2_Poti5` gets one sensor on the Heat pump
device: Solar input temperature.

## Consequences
- If detection is wrong on someone's pump, they report it with diagnostics and it gets
  fixed for everyone. Until then they can't correct it themselves. For a room sensor
  that costs the room setpoint in Home Assistant; the pump itself keeps working.
- A sensor wired to the solar input later appears after the next reload.
- The new sensor has not run on a real pump with a wired input. It rests on the reading
  reported in that issue.
