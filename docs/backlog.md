# Backlog

Ideas for after v1, added when someone asks for them.

- **Alarm reset button** (`2_Reset_ALARMA_iz_PGDT`), on a feature request. Left out
  of v1 by the user's choice: an alarm usually means someone should look at the heat
  pump itself. It also can't be tested on demand, since an alarm is never provoked
  on purpose. If added: test it on a real alarm, make it available only while an
  alarm is active, keep a minimum interval between resets, and check how the
  controller clears the flag, because the client's read-back assumes a value stays.
- **Operating programme that holds.** Eco goes back to Normal by itself on the tested
  pump (firmware from 2016), even though the Moja Orca app writes the same tag. Left as
  it is (user, 2026-11-07). If someone asks: `2_ECO`, `2_PARTY` and `2_POCITNISKI` are
  coils of unknown purpose, and the first place to look.
- **Editing the weekly timer programmes.** v1 shows them read-only.
- **Noticing a rewired pump while running.** v1 notices at the next setup or reload.
- **Discovery.** v1 has none (ADR 0013). A DHCP match would need the display's DHCP
  host name to be distinctive, which hasn't been checked.
