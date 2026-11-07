# Phase 6: live write test plan

The plan agreed at CP2. Anything further needs the user's agreement in the conversation
and them present (`PLAN.md` §2.2, §2.3). Values are from 2026-11-05 and only show the
size of each change: the "now" value is read again right before each write, and
that is what gets restored.

## Result (2026-11-07)

Run with the user's agreement, with the system switched off and no alarm, after they
had turned off the old integration and power cycled the pump. **Passed.**

- **65 settings** (Tier A and B), 141 writes through Home Assistant's own actions.
  Each changed by one step, read back and restored. Every answer `S_OK`, no failed
  poll, no warning, no alarm, and no other setting moved at any point (checked after
  every write). At the end every writable setting equalled the baseline.
- **The display answers a write like a read record:** `#tag`, `S_OK`, then quality
  and value. A new value is readable at once, so the read-back needs no wait. One
  value held across several polls for 80 seconds.
- **Combined actions:** the climate writes the mode, then the enable, 0.5 s apart.
  Turning on and off, and a hot water temperature set with an operation, work too.
- **One setting didn't hold: the operating programme.** The pump accepted Eco and read
  it back, then went back to Normal by itself within 5 seconds. Every other setting
  kept its test value until restored. Not explained yet: either a programme can't start
  with the system off, or `2_Delovanje_MENI` only shows the programme and another tag
  starts it (`2_ECO`, `2_PARTY`, `2_POCITNISKI`: coils, all 0, purpose unknown). The
  recorded ECO duration on this pump is 8 hours, so a zero duration isn't the cause.
- **Not run:** Tier C (not chosen), and the six settings below that are not tested
  live. With the system off, nothing here shows how the pump *acts* on a new value.
- The hidden test entities were disabled again, by the user rather than by the
  integration, because the API doesn't allow setting that back. It makes no practical
  difference.

The full log is in `research/captures/write_tests.md` (not in the repository).

## What it proves

Every setting the integration can change really changes on the real pump, is
read back correctly, and returns to its original value. Until now writes have
only run against the emulator.

## How it runs

- The dev HA is restarted first if the code changed since it last started, so it
  runs the committed code, including the debug line for the write response.
- Through Home Assistant's own actions on the dev HA, one at a time, so the whole
  path is exercised on the integration's one session.
- Settings hidden by default are enabled for the test and disabled again
  afterwards.
- The old integration in the other Home Assistant is turned off for the test: it
  uses a login, and its number entities can write too.
- Before and after: a full copy of all values from diagnostics. Afterwards every
  setting must equal the copy from before.
- Every write goes into `research/captures/write_tests.md`: time, tag, old value,
  new value, read-back.
- At least 5 seconds between writes; nothing repeats automatically.

## Order

1. **One first write, then stop and look:** Radiators, cooling flow temperature at
   20 °C outside, 25.0 → 24.9 °C and back. The radiators circuit is off and this
   only matters in cooling. Two things are unknown until now and the client's
   behaviour depends on them: what the display answers to a write (the debug log
   records it), and how soon a read shows the new value. If it takes longer than
   the immediate read-back, the client must wait before reading back, and that gets
   fixed before going on.
2. **Tier A.** About 10 minutes.
3. **Tier B,** only while the pump is idle, not during a hot water cycle. Each
   change is restored right away. About 5 minutes. The climate and water heater
   paths are tested here: underfloor off and back to heat, hot water off and back.
4. **Tier C,** only the ones the user picks.

## When to stop

Stop at once, restore what was written and tell the user if:

- an alarm appears, or the alarm state changes;
- the display stops answering, or the login is refused;
- a read-back still differs after the first-write check has settled the timing;
- anything happens on the pump that the user doesn't expect.

The first write is the moment to catch surprises: orca-energy-ha #20 restarted a
controller with an out-of-range value, which is why every test value here is
inside the manufacturer's range, one step from the current value.

## Afterwards

Done: the dashboard has mode buttons on the climates and on the water heater.

## Settings

### Tier A: no effect on what the pump is doing right now (48)

| Setting | Tag | Now | Test | Note |
|---|---|---|---|---|
| Heat pump: Additional heat source delay | `2_Dodatni_Vir_Zakasnitev` | 1 min | 0 min |  |
| Heat pump: Additional heat source outdoor temperature | `2_Temp_Vklop_Dod_Vir` | 20.0 °C | 19.9 °C |  |
| Heat pump: Additional source alongside heat pump | `2_Vzporedno_Dod_vir_izklop` | off | on |  |
| Heat pump: Anti-blocking programme | `2_Vklop_ANTI_BLOK_prog` | on | off |  |
| Heat pump: Electric heater stage 1 delay | `2_Elektro_Grelec_Zakasnitev_1_ST` | 1 min | 2 min |  |
| Heat pump: Electric heater stage 1 outdoor temperature | `2_Zun_temp_za_vklop_Grelec_1` | 22.0 °C | 21.9 °C |  |
| Heat pump: Electric heater stage 2 delay | `2_Elektro_Grelec_Zakasnitev_2_ST` | 3 min | 2 min |  |
| Heat pump: Electric heater stage 2 outdoor temperature | `2_Zun_temp_za_vklop_Grelec_2` | 22.9 °C | 22.8 °C |  |
| Heat pump: PV function | `2_PV_Vklop` | off | on |  |
| Heat pump: Quiet operation timer programme | `2_Izbira_TIMERJA_TISJE` | all_day | programme_1 |  |
| Heat pump: Screed drying maximum flow temperature | `2_Max_VF_susenje_estrihov` | 55.0 °C | 54.9 °C |  |
| Heat pump: Screed drying minimum flow temperature | `2_Min_VF_susenje_estrihov` | 25.0 °C | 24.9 °C |  |
| Hot water: Legionella protection cycle | `2_Legionela_Cikel` | weekly | every_two_weeks |  |
| Hot water: Legionella protection day | `2_On_Dan_Legionella` | sunday | saturday |  |
| Hot water: Legionella protection start hour | `2_On_Ura_Legionella` | 14 h | 13 h |  |
| Hot water: Legionella protection temperature | `2_Temperatura_legionela` | 70.0 °C | 69.9 °C |  |
| Radiators: Automatic cooling switch | `2_Aktiv_avtom_preklop_poletje_MK2` | off | on |  |
| Radiators: Automatic cooling switch delay | `2_Cas_ur_preklop_poletje_MK2_HL` | 24 h | 23 h |  |
| Radiators: Automatic cooling switch outdoor temperature | `2_Temp_preklop_poletje_MK2_HL` | 21.0 °C | 20.9 °C |  |
| Radiators: Automatic heating switch | `2_Aktiv_avtom_preklop_zima_MK2` | off | on |  |
| Radiators: Automatic heating switch delay | `2_Cas_ur_preklop_zima_MK2` | 10 h | 9 h |  |
| Radiators: Automatic heating switch outdoor temperature | `2_Temp_za_preklop_zima_MK2` | 22.0 °C | 21.9 °C |  |
| Radiators: Cooling flow temperature at 20 °C outside | `2_Tocka_1_20st_HL_MK2` | 25.0 °C | 24.9 °C |  |
| Radiators: Cooling flow temperature at 30 °C outside | `2_Tocka_2_30st_HL_MK2` | 15.0 °C | 14.9 °C |  |
| Radiators: Cooling regulation | `2_Reg_po_RF_AF_KONST_MK2_HL` | room_and_outdoor | outdoor |  |
| Radiators: Flow temperature setpoint | `2_Max_VF_MK2` | 37.0 °C | 36.9 °C |  |
| Radiators: Heat pump temperature boost | `2_Povec_temp_TC_pri_MK2` | 5.0 °C | 4.9 °C |  |
| Radiators: Heating curve shift | `2_Zamik_krivulje_MK2` | 5.0 °C | 4.9 °C |  |
| Radiators: Heating curve slope correction | `2_Nagib_krivulje_MK2` | 0.0 °C | -0.1 °C |  |
| Radiators: Heating regulation | `2_Reg_po_RF_AF_KONST_MK2` | constant | outdoor |  |
| Radiators: Minimum cooling flow temperature | `2_Min_VF_MK2_HL` | 17.5 °C | 17.4 °C |  |
| Radiators: Minimum heating flow temperature | `2_Min_VF_MK2` | 30.0 °C | 29.9 °C |  |
| Radiators: Night setback | `2_Ponoci_min_temp_IZKLOP_MK2` | off | lower_temperature |  |
| Radiators: Operating mode | `2_Rezim_MK2` | heating | auto_heat_cool |  |
| Radiators: Timer programme | `2_Izbira_TIMERJA_MK2` | programme_5 | programme_1 |  |
| Solar: Minimum collector temperature | `2_Min_Temp_SOLAR` | 50.0 °C | 49.9 °C |  |
| Solar: Switch-off difference | `2_Dif_izklopa_SOLAR` | 5.0 °C | 4.9 °C |  |
| Solar: Switch-on difference | `2_Dif_vklopa_SOLAR` | 10.0 °C | 9.9 °C |  |
| Underfloor: Automatic cooling switch | `2_Aktiv_avtom_preklop_poletje_MK1` | off | on | only used in cooling |
| Underfloor: Automatic cooling switch delay | `2_Cas_ur_preklop_poletje_MK1_HL` | 24 h | 23 h | only used in cooling |
| Underfloor: Automatic cooling switch outdoor temperature | `2_Temp_preklop_poletje_MK1_HL` | 21.0 °C | 20.9 °C | only used in cooling |
| Underfloor: Automatic heating switch delay | `2_Cas_ur_preklop_zima_MK1` | 24 h | 23 h | the outdoor temperature must be well below the threshold |
| Underfloor: Automatic heating switch outdoor temperature | `2_Temp_za_preklop_zima_MK1` | 18.0 °C | 17.9 °C | the outdoor temperature must be well below the threshold |
| Underfloor: Cooling flow temperature at 20 °C outside | `2_Tocka_1_20st_HL_MK1` | 18.5 °C | 18.4 °C | only used in cooling |
| Underfloor: Cooling flow temperature at 30 °C outside | `2_Tocka_2_30st_HL_MK1` | 18.5 °C | 18.4 °C | only used in cooling |
| Underfloor: Heating curve shift | `2_Zamik_krivulje_MK1` | -0.1 °C | -0.2 °C | only used with outdoor-based regulation |
| Underfloor: Heating curve slope correction | `2_Nagib_krivulje_MK1` | 0.0 °C | -0.1 °C | only used with outdoor-based regulation |
| Underfloor: Minimum cooling flow temperature | `2_Min_VF_MK1_HL` | 18.0 °C | 17.9 °C | only used in cooling |

### Tier B: live controls, smallest possible change, restored straight away (17)

| Setting | Tag | Now | Test | Note |
|---|---|---|---|---|
| Heat pump: Operating programme | `2_Delovanje_MENI` | normal | eco | changes setpoints while it lasts |
| Heat pump: Quiet operation | `2_Tisje_delov` | outdoor_temperature | off | changes quiet operation while it lasts |
| Heat pump: Quiet operation outdoor temperature | `2_Temp_AF_za_TISJE_DEL` | 15.0 °C | 14.9 °C |  |
| Hot water: Heat pump temperature boost | `2_Povec_temp_TC_pri_SV` | 8.5 °C | 8.4 °C |  |
| Hot water: Higher temperature (water heater target) | `2_Temp_vode_sanitarna` | 42.0 °C | 41.9 °C |  |
| Hot water: Legionella protection | `2_Legionela_vklop` | off | on | not near its start hour |
| Hot water: Lower temperature | `2_Temp_vode_sanitarna_NIZJA` | 36.0 °C | 35.9 °C |  |
| Hot water: On/off (water heater) | `2_SV_vklop` | on | off | hot water off for a moment |
| Hot water: Switch-on difference | `2_Diferenca_vklopa_SV` | 7.0 °C | 6.9 °C |  |
| Hot water: Timer programme | `2_Izbira_TIMERJA_SV` | programme_4 | programme_1 | schedule changes while it lasts |
| Underfloor: Automatic heating switch | `2_Aktiv_avtom_preklop_zima_MK1` | on | off |  |
| Underfloor: Circuit on/off (climate) | `2_MK1_vklop` | on | off | underfloor off for a moment |
| Underfloor: Flow temperature setpoint | `2_Max_VF_MK1` | 30.0 °C | 29.9 °C | the running setpoint, smallest step |
| Underfloor: Minimum heating flow temperature | `2_Min_VF_MK1` | 25.0 °C | 24.9 °C |  |
| Underfloor: Night setback | `2_Ponoci_min_temp_IZKLOP_MK1` | off | lower_temperature |  |
| Underfloor: Operating mode | `2_Rezim_MK1` | heating | auto_heat_cool | stays on heating or automatic, never cooling |
| Underfloor: Timer programme | `2_Izbira_TIMERJA_MK1` | programme_2 | programme_1 | schedule changes while it lasts |

### Tier C: only if you explicitly want these tested (6)

| Setting | Tag | Now | Test | Note |
|---|---|---|---|---|
| Heat pump: Power limit cooling | `2_Max_moc_TC_pri_HLAJ` | 30.0 % | 29.0 % | needs the power limit option on |
| Heat pump: Power limit heating | `2_Max_moc_TC_pri_OGR` | 70.0 % | 69.0 % | needs the power limit option on |
| Heat pump: Power limit hot water | `2_Max_moc_TC_pri_SV` | 75.0 % | 74.0 % | needs the power limit option on |
| Heat pump: Power limit quiet operation | `2_Max_moc_TC_TISJA` | 65.0 % | 64.0 % | needs the power limit option on |
| Heat pump: Quick room mode | `2_HITRI_Rezim` | inactive | heating | overrides every circuit, including the radiators that are off |
| Heat pump: System | `2_Vklop_Izklop` | on | off | disabled by default, so enable it first; stops heating and hot water while off; only with the pump idle |

### Not tested live (6)

| Setting | Tag | Why |
|---|---|---|
| Heat pump: Electric heater | `2_Vklop_Elektro_Grelci` | auto could start the electric heater: its outdoor thresholds (22 °C) are above today's temperature |
| Heat pump: Electric heater alongside heat pump | `2_Vzporedno_Elektro_Grelci` | could run the electric heater alongside the heat pump |
| Heat pump: Screed drying | `2_Susenje_estrihov_vklop` | starts a multi-day floor drying programme |
| Radiators: Circuit on/off (climate) | `2_MK2_vklop` | would start the radiators circuit; tested on the underfloor circuit, same code |
| Underfloor: Cooling regulation | `2_Reg_po_RF_AF_KONST_MK1_HL` | changes how the running circuit regulates; tested on the radiators, same code |
| Underfloor: Heating regulation | `2_Reg_po_RF_AF_KONST_MK1` | changes how the running circuit regulates; tested on the radiators, same code |

Buffer tank settings and circuit 3 have no entities on this pump, and room
setpoints need a room sensor, so these are covered by the emulator only.
