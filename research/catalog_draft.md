# Tag catalog draft (research subagent A)

Status: draft for CP1, offline work only (no pump access). Generated on 2026-10-31 from the files below; nothing here
was read live. Sensitive values are left out: no MAC, IP or serial numbers appear, and every tag whose name contains
`GESLO` is shown as `<redacted>` (`<r>` in dump columns).

**Sources** (codes used in the `src` column):

| code | source |
|---|---|
| J | `research/moja_orca_catalog.json` (Moja Orca app metadata, recorded 2026-10-30; `J:<page>` = app page). Most authoritative for types, ranges, units, enum order. |
| C | `orca-energy-ha/custom_components/orca/config.yml` (old integration; working tree, 74 tags; committed `main` has 72) |
| M | `orca-energy-ha/development_resources/menu_to_field.yaml` (touch-UI label → tag; "may contain errors") |
| D | value dumps: ours (`research/captures/2026-10-31_full_dump/`, schema 23), duo (schema 3), mono (schema 7) |
| R | the INFO-page `readTags` request quoted in `orca-energy-ha/development_resources/readme.md` (25 tags in page order) |
| H | page HTML/JS inside the Moja Orca HAR recordings (home widgets, clock-setting code, info page extra lines) |
| I | info-page matching (§4) |
| T | timer ground truth: the 15 programme ranges in J, decoded in §5 |
| B | `research/manual_facts.md` (subagent B, facts from the manuals) |
| X | cross-pump inference from the three dumps |
| N | inference from the tag name only |

**Conventions.** Raw values are integers. `×10` = one-decimal value (415 = 41.5). `-9999` = sensor not connected
(`n/c`). Writable: `yes` = proposed user setting with a known range; `no` = read-only state/value (or setting we don't
propose to write); `installer` = never writable (PLAN §10, plus items proposed for that list, marked "proposed");
`never` = commands, test outputs, passwords: never write, mostly never expose. Duo/mono columns show raw values;
`–` = not in that dump. The duo/mono dump files list only tags that returned a value, so "not in the dump" most
likely means unknown on that firmware (whole families are missing consistently), but it is not proven. The dumps are
from different dates: ours 2026-10-31 20:24 (Sat), duo 2025-12-08 18:45 (Mon),
mono 2025-12-10 20:45 (Wed) (their `2_CURRENT_*` tags).

## 1. Summary

### 1.1 Counts

| item | count |
|---|---|
| Tags in J | 193: 180 S_OK on ours, 13 E_UNKNOWNTAG (all on the home page, §7); all 193 in duo, 192 in mono |
| Tags in C | 74 (working tree; `main` has 72: the working tree adds `2_PogojPGDT_Shema_in_tipalo_OK1/OK2` and makes `2_Rezim_MK1/MK2` writable); 74 S_OK on ours |
| J ∩ C | 40; J ∪ C = 227; C-only tags: 34 |
| `all_fields.txt` | 1,767 names: 708 S_OK / 1,059 E_UNKNOWNTAG on ours (identical in both passes) |
| duo dump | 1,240 tags, a strict superset of our 708 (532 more) |
| mono dump | 744 tags: 541 of our 708, plus 203 that ours lacks; it lacks 167 of ours (e.g. `2_Shema_DK1/DK2`, all `*_DK1/*_DK2`, alarms `2_Alarm_*`) |
| menu map | 1,891 label → name bindings (`::` and `:` lines), 554 distinct names, 360 of them real tag names, 284 S_OK on ours (the rest are display-local aliases with spaces) |
| this catalog | 253 rows in §2 covering 682 tag names (645 of our 708 S_OK); the other 63 S_OK tags are display-local variables (§9.1) |
| firmware (`2_Verzija_programa_DAN/MESEC/LETO/ZAPOREDJE`) | ours 12.12.2016 build 61; duo 20.01.2020 build 89; mono 03.11.2022 build 103 |

### 1.2 Key findings and surprises

1. **Our controller runs the oldest firmware of the three** (build 61 from 2016 vs 89 and 103). That alone explains
   most of the 1,059 unknown tags: operating hours and start counters (`2_URE_*`, `2_VKLOPI_*`), the defrost log,
   `2_NAPAKA`, room-sensor alarms, PV-function parameters, `2_Signal_PV/EVU`, the home-page demand flags
   `2_PogojPGDT_N_OSN_*` and heater icons all exist on duo/mono but not on ours. The 13 tags the app showed as `null`
   are exactly the J tags that are E_UNKNOWNTAG on ours. Feature detection must be per tag (status code), never per
   model or "the app shows it".
2. **Topology flags differ by firmware.** The newest firmware (mono dump) has no `2_Shema_DK1`/`2_Shema_DK2` and no
   `*_DK1`/`*_DK2` settings at all (absent from the dump, most likely unknown there), so the old integration's DK
   flags fail there. `2_Shema` (schema number) and
   `2_PogojPGDT_Shema_OK1/OK2` exist on all three and agree with the hardware. Old firmware still carries legacy
   `*_DK1`/`*_DK2` settings with identical factory-like values on ours and duo; the app never uses them (§2.19).
3. **Timers fully decoded** (§5): `2_TIMER_<p>_{Ura|Minute}_{ON|OFF}_<r>` plus seven weekday flags per range,
   plain integers. All 15 ranges match the JSON exactly. Behaviour check: the active room setpoint
   (`2_Zahtevana_RF_*`) switched between the high and low setpoint exactly as the selected programmes predict at three
   moments, which also proves that **a range without weekdays is inactive**.
4. **All 31 info-page lines are named** (§4): the old readme's INFO request lists the first 25 tags in page order,
   and the rest follow from the menu map and exact value matches. Highlights: `2_Preklop_PV1` is the 3-way valve
   ("PV" = preklopni ventil, not photovoltaics; 1 = DHW); `2_Pogoj_maska_pret_stik` 1 = flow OK; HP target
   `2_Izrac_temp_TC` reads 9.0 °C when there is no demand; `2_Vklop_C3` is both "solar pump" and "circuit 3 pump"
   because DK3 and solar share output P3 (no schema has both; B).
5. **Enums (R12):** no value in any of the three dumps falls outside the J maps. Issue #38 came from the old config's
   circuit-name map, which is shifted by one from value 4, has phantom values 21/23/24 and lacks 3 and 22 (our
   `MK1_IME(3)` = 3). The app decodes slot 3's home name with a different list (`widget_titles2`, no "mixing circuit"
   entries, so values ≥ 7 shift by 2) and its settings list has a typo key (28 instead of 18).
6. **The old config has wrong ranges** for curve shift/slope (±9.9 vs J ±15.0), power limits (10–100 % vs J 40–100 %
   and 16–100 %), heater outdoor thresholds (−30…10 vs J −30…30; our stage-2 value 22.9 °C is outside the old
   range), DHW setpoint (25–60 vs J 8–55) and buffer setpoints (15–55 vs J 12–55). Also two wrong semantics:
   `2_Poti1` is the HP water temperature, not a "gas" temperature; `2_Vklop_ele_grelca_1` is heater stage 1 /
   additional source, not "for defrosting" (§8).
7. **Constant-mode hypothesis (R8) supported:** at 17:16 (circuit 1 timer on) HP target 28.0 = `2_Max_VF_MK1`, P1 on;
   at ~20:09 and in our dump (timer off, low-regime action "off") target 9.0, P1 off.
8. **`2_Tipalo_*` are per-input "sensor enabled" flags, not topology**: `2_Tipalo_VF2` = 1 on duo without a
   circuit 2 (but the input reads 21.0 °C) and 0 on ours with MK2 present; `2_Tipalo_KF` = 1 on duo without solar.
   `2_PogojPGDT_Shema_in_tipalo_OKn` matches room-sensor presence on all three pumps and is what the app uses to make a
   circuit widget active.

### 1.3 Open questions for the lead

1. `2_PRIKAZ_Reg_temp_vode` ("Delovna moč zunanje enote"): % demand (0–10 V Y3 signal) or a regulated water
   temperature? The old readme example had it equal to `2_Izrac_temp_TC` (475). Read both while the outdoor unit runs
   (#33).
2. `2_Rezim_delov_TC` values other than 0 (old config: 1 heating, 2 cooling, 3 defrost): observe during space
   heating, DHW and defrost.
3. Room setpoint ranges (`2_Temp_prostor_dnevna/_nocna[_OK2|_OK3]`): not in J (the app showed no circuit popup
   because no room sensor). Needs `LIMITS` (R2) or a recording on a pump with a room sensor.
4. Slot-3 circuit name: `2_IME_MK3` (decoded with `settings_titles`) and `MK1_IME(3)` (`widget_titles2`) hold the
   same raw value on all pumps; for values ≥ 7 the two lists disagree. Which is right? Needs a slot-3 name ≥ 7.
5. Midnight-crossing ranges (23:00–06:00 etc.): which weekday flag governs the part after midnight? All such ranges on
   our pump have no days, so untestable from the captures.
6. Party/ECO duration and holiday end-date tags (`2_PARTY_cas`, `2_ECO_cas`, `2_*_pocitniski`): ranges and whether
   writing `2_Delovanje_MENI` alone is enough. `2_NORMALNO_DELOVANJE`/`2_PARTY`/`2_ECO`/`2_POCITNISKI` are all 0
   while the programme is normal: commands or stale?
7. `2_SV_24ur_timer` = 1 contradicts `2_Izbira_TIMERJA_SV` = 4 on ours. Ignore it?
8. Our MK2 (mixing circuit) has no flow sensor (`2_Temp_VF2` = -9999, `2_Tipalo_VF2` = 0). Expected because it is
   switched off, or a wiring issue the user should know about?
9. Writability of borderline settings (proposed here as installer): solar enable/target/limits, additional-source
   choice, number of heater stages, `2_Cas_zakasn_po_solarju`. Circuit names proposed read-only.
10. Is the current DHW setpoint readable on our firmware? `2_Temp_zelena_SV` (duo: equals the high setpoint) is
    E_UNKNOWNTAG on ours, so the integration must compute it from the DHW timer.

## 2. Catalog

Sections follow the elements. Circuit rows give one tag per slot. `ours` shows raw (decoded); enum texts are EN / SI from J where J has them.

### 2.1 System and heat pump (global)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `outdoor_temperature` | `2_Temp_Zunanja` | heat pump | Outdoor temperature (sensor OT on B1). Home widget ZUNAJ; info line 1. | float | ×10 | °C | no | — | — | 74 (7.4) | duo 60 · mono 24 | high | J:home, R, I, H, B, C, M, D |
| `hp_temperature` | `2_Poti1` | heat pump | Heat pump water temperature (sensor HTT on B3; app: 'Temperatura toplotne črpalke', home widget TOPLOTNA ČRPALKA). The old config called it 'internal/gas temperature'; that is wrong. | float | ×10 | °C | no | — | — | 235 (23.5) | duo 255 · mono 363 | high | J:home, R, I, H, B, C, M, D |
| `hp_target_temperature` | `2_Izrac_temp_TC` | heat pump | Computed target temperature of the heat pump ('Želena temp. toplotne črpalke'). 28.0 °C at 17:16 on 10-30 (= `2_Max_VF_MK1` while circuit 1's timer was on), 9.0 °C at ~20:16 and in our dump (no demand). 9.0 °C looks like the 'no demand' value (also on duo). | float | ×10 | °C | no | — | — | 90 (9.0) | duo 90 · mono 470 | high | R, I, X, C, M, D |
| `outdoor_unit_state` | `2_Rezim_delov_TC` | heat pump | Outdoor unit state ('Stanje zunanje enote'). Only 0 = off seen on ours/duo; mono = 1 while heating DHW. | enum | ×1 | — | no | 0..3? | 0 = off (Izklop, app); 1 = heating?; 2 = cooling?; 3 = defrost? (1–3 from old config, unverified) | 0 | duo 0 · mono 1 | medium | R, I, X, C, M, D |
| `outdoor_unit_demand` | `2_PRIKAZ_Reg_temp_vode` | heat pump | Info line 'Delovna moč zunanje enote' (outdoor unit power, %). Probably the 0–10 V demand signal Y3 to the Mitsubishi PAC-IF (B, Duo p. 53) as 0..1000 = 0–100 %. Values: 0 ours/duo (idle), 500 mono (DHW run), 475 in the old readme example where `2_Izrac_temp_TC` was also 475; the name says 'regulated water temperature display'. Unit and meaning need live confirmation (#33). | float | ×10 | % (?) | no | 0..1000? | — | 0 (0.0) | duo 0 · mono 500 | medium (tag) / low (unit) | R, I, M, B, X, C, D |
| `pump_p0` | `2_Vklop_C0` | heat pump | Heat pump circulation pump P0 (Č0) running. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 1 | high | R, I, M, C, D |
| `flow_switch` | `2_Pogoj_maska_pret_stik` | heat pump | Flow switch FS (input ID1) state as shown on the info page. SI snapshot 'Pretok O.K.' with P0 on; EN snapshot 'No flow' with P0 off; our dump 0 with P0 off; mono 1 with P0 on. | enum | ×1 | — | no | 0..1 | 0 = no flow (EN 'No flow'); 1 = flow OK (Pretok O.K.) | 0 | duo 0 · mono 1 | medium-high | R, I, M, X, B, D |
| `valve_3way` | `2_Preklop_PV1` | heat pump | 3-way changeover valve position ('Smer prekl. ventila'). 'PV' = preklopni ventil, not photovoltaics. Mono shows 1 while heating DHW (its HP target = DHW setpoint + DHW boost). | enum | ×1 | — | no | 0..1 | 0 = rooms (Prostori); 1 = DHW (EN 'DHW heating') | 1 | duo 1 · mono 1 | high (tag) / medium-high (enum) | R, I, M, X, C, D |
| `defrost_active` | `2_Odtaljevanje_izhod` | heat pump | Defrost output/indicator ('odtaljevanje' = defrosting); home page. 0 on all pumps. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | medium | J:home, N, D |
| `heating_active` | `2_Pogoj_maska_napis_ogrevanje` | heat pump | Home-page 'heating' caption/icon condition. 0 ours/duo (idle), 1 mono (HP running for DHW), so probably 'HP currently producing heat'. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 1 | medium-low | J:home, X, D |
| `system_enable` | `2_Vklop_Izklop` | heat pump | System on/off ('Aktiviranje sistema'). SI: 'Aktiviranje sistema'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1 | duo 1 · mono 1 | high | J:settings_basic, D |
| `system_mode` | `2_REZIM_SISTEMA` | heat pump | Unknown system-mode enum; 1 on ours and duo, absent on mono. HMI derives `_1`/`_3` flags from it, so values 1 and 3 are meaningful. Not in the app. | enum | ×1 | — | no | ? | 1 = ? (observed); 3 = ? | 1 | duo 1 · mono – | low | N, X, D |
| `anti_block_programme` | `2_Vklop_ANTI_BLOK_prog` | heat pump | Anti-blocking programme for pumps/valves (periodic exercise). SI: 'Protiblokirni program'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1 | duo 1 · mono 1 | high | J:settings_basic, D |
| `screed_drying` | `2_Susenje_estrihov_vklop` | heat pump | Screed drying programme on/off. Advanced; disabled by default in HA. SI: 'Program sušenja estrihov'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:settings_basic, D |
| `screed_drying_min_flow` | `2_Min_VF_susenje_estrihov` | heat pump | Minimum flow temperature during screed drying. SI: 'Min. temp. vtoka pri sušenju estrihov'. | float | ×10 | °C | yes | 90..500 (9.0 to 50.0 °C) | — | 250 (25.0) | duo 350 · mono 250 | high | J:settings_basic, D |
| `screed_drying_max_flow` | `2_Max_VF_susenje_estrihov` | heat pump | Maximum flow temperature during screed drying. SI: 'Max. temp. vtoka pri sušenju estrihov'. | float | ×10 | °C | yes | 90..550 (9.0 to 55.0 °C) | — | 550 (55.0) | duo 420 · mono 550 | high | J:settings_basic, D |
| `screed_drying_days` | `2_Stevilo_dni_susenje_estrihov` | heat pump | Length of the screed drying programme in days (21 on all pumps). Range unknown. | int | ×1 | d | no | ? | — | 21 | duo 21 · mono 21 | medium | N, X, D |
| `screed_drying_current_day` | `2_Tekoci_dan_susenje_estrihov` | heat pump | Current day of the screed drying programme (1 ours, 2 duo, 1 mono). | int | ×1 | d | no | ? | — | 1 | duo 2 · mono 1 | medium | N, X, M, D |
| `remote_link` | `2_POVEZAVA` | heat pump | 'Connection'; 0 ours/duo, 1 mono. Possibly the cloud/Moja Orca link state. Unknown. | bool? | ×1 | — | no | 0..1? | — | 0 | duo 0 · mono 1 | low | N, X, D |

### 2.2 Operating programme and quick room mode

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `operating_programme` | `2_Delovanje_MENI` | system | Operating programme (home-page drop-down): normal (follow timers), holiday and ECO force the lower regime, party forces the higher regime (B, Touch p. 6–7). | enum | ×1 | — | yes | 0..3 | 0 = Normal operation / Normalno delovanje; 1 = HOLIDAY / POČITNIŠKI REŽIM; 2 = PARTY; 3 = ECO | 0 (Normal operation) | duo 0 · mono 0 | high | J:home, H, B, M, D |
| `quick_room_mode` | `2_HITRI_Rezim` | system | Quick room mode ('Hitra izbira prostorskega režima'): inactive = circuits follow their own mode; off = all space heating/cooling off (DHW stays on); heating/cooling = only heating/cooling circuits on (B, Touch p. 6). Duo had 2 (heating). SI: 'Režim delovanja'. | enum | ×1 | — | yes | 0..3 | 0 = Inactive / Neaktivna funkcija; 1 = OFF / Izklop; 2 = Heating / Ogrevanje; 3 = Cooling / Hlajenje | 0 (Inactive) | duo 2 · mono 0 | high | J:operation_mode, B, X, D |
| `party_duration` | `2_PARTY_cas` | system | Party programme duration in hours (manual: 'TRAJANJE PARTY REŽIMA', hours). 4 ours, 2 duo/mono. Range unknown. | int | ×1 | h | no | ? | — | 4 | duo 2 · mono 2 | medium | N, B, X, D |
| `eco_duration` | `2_ECO_cas` | system | ECO programme duration in hours ('TRAJANJE ECO REŽIMA'). 8 ours, 2 duo/mono. Range unknown. | int | ×1 | h | no | ? | — | 8 | duo 2 · mono 2 | medium | N, B, X, D |
| `holiday_end_day` | `2_Dan_pocitniski` | system | Holiday programme end date, day part ('KONEC POČITNIŠKEGA REŽIMA'). Ours 0 (unset), duo 9, mono 11. | int | ×1 | — | no | ? | — | 0 | duo 9 · mono 11 | medium-low | N, B, X, D |
| `holiday_end_month` | `2_Mesec_pocitniski` | system | Holiday end date, month (ours 1, duo/mono 12). | int | ×1 | — | no | ? | — | 1 | duo 12 · mono 12 | medium-low | N, B, X, D |
| `holiday_end_year` | `2_Leto_pocitniski` | system | Holiday end date, 2-digit year (ours 15, duo/mono 25). | int | ×1 | — | no | ? | — | 15 | duo 25 · mono 25 | medium-low | N, B, X, D |
| `programme_flags` | `2_NORMALNO_DELOVANJE`, `2_PARTY`, `2_ECO`, `2_POCITNISKI` | system | All 0 on all pumps even though `2_Delovanje_MENI` = 0 (normal), so not state mirrors. Probably HMI button/command flags. Do not use. | bool | ×1 | — | never | 0..1 | — | 2_NORMALNO_DELOVANJE: 0<br>2_PARTY: 0<br>2_ECO: 0<br>2_POCITNISKI: 0 | duo 0 · 0 · 0 · 0<br>mono 0 · 0 · 0 · 0 | low | N, X, D |

### 2.3 Heating circuits: settings (slot 1 / 2 / 3)

Tag names are per slot (slot 1 `*_MK1` even on DK1). `—` = the slot has no such tag. Values: ours S1 = DK1 floor (on), S2 = MK2 radiator (off), S3 = absent.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `circuit_name` | 1: `2_IME_MK1`<br>2: `2_IME_MK2`<br>3: `2_IME_MK3` | circuit | Circuit name chosen by the installer (settings page). App decodes all three with `settings_titles`; see §6 for the list and the slot-3 conflict. SI: 'Ime ogrevalne veje 1'. | enum (list) | ×1 | — | no | 1..20 | list `settings_titles` (20 entries, §6) | 1: 16 (FLOOR)<br>2: 15 (RADIATOR)<br>3: 3 (HEATING CIRCLE 3) | duo 16 · 2 · 3<br>mono 15 · 16 · 3 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `circuit_name_widget` | 1: `MK1_IME`<br>2: `MK1_IME(2)`<br>3: `MK1_IME(3)` | circuit | Circuit name as used on the home page/info page. Equal to `2_IME_MKn` on all 3 pumps (likely an HMI mirror). Slots 1–2 decode with `widget_titles`, slot 3 with `widget_titles2` (different numbering from 7 up). The old map lacked value 3 (crash #38). | enum (list) | ×1 | — | no | slot 1/2: 1..20 <br>slot 3: 1..18 | slot 1/2: list `widget_titles` (20 entries, §6) <br>slot 3: list `widget_titles2` (18 entries, §6) | 1: 16 (FLOOR)<br>2: 15 (RADIATOR)<br>3: 3 (HEATING CIRCLE 3) | duo 16 · 2 · 3<br>mono 15 · 16 · 3 | high (tag) / medium (slot-3 list) | J:home/settings_dyn_1/settings_dyn_2/settings_dyn_3, C, H, X, M, D |
| `circuit_enable` | 1: `2_MK1_vklop`<br>2: `2_MK2_vklop`<br>3: `2_DK3_vklop` | circuit | Circuit on/off ('Aktiviranje'). SI: 'Aktiviranje'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1: 1<br>2: 0<br>3: 0 | duo 1 · 0 · 0<br>mono 1 · 1 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, D |
| `installation_type` | 1: `2_Talno_Radiatorsko_MK1`<br>2: `2_Talno_Radiatorsko_MK2`<br>3: `2_Talno_Radiatorsko_DK3` | circuit | Hydronic type (selects the base heating curve: floor or radiator, B Duo p. 44). SI: 'Vrsta strojne inštalacije'. | enum | ×1 | — | installer | 0..1 | 0 = RADIATOR / RADIATORJI; 1 = FLOOR / TALNO | 1: 1 (FLOOR)<br>2: 0 (RADIATOR)<br>3: 1 (FLOOR) | duo 1 · 1 · 1<br>mono 0 · 0 · 1 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, B, D |
| `circuit_mode` | 1: `2_Rezim_MK1`<br>2: `2_Rezim_MK2`<br>3: `2_Rezim_DK3` | circuit | Operating mode of the circuit. **Slot 3 lacks 5 (manual).** Value 0 is an empty, non-selectable entry. Old working-tree config makes it writable. SI: 'Režim delovanja'. | enum | ×1 | — | yes | slot 1/2: 1..5 <br>slot 3: 1..4 | slot 1/2: 0 = (empty); 1 = Heating / Ogrevanje; 2 = Cooling / Hlajenje; 3 = Automatic sw.HEAT-COOL / Avtomatski preklop ogr.-hl.; 4 = Switch with ID2 input / Preklop preko vhoda ID2; 5 = Manual switching / Ročni preklop <br>slot 3: 0 = (empty); 1 = Heating / Ogrevanje; 2 = Cooling / Hlajenje; 3 = Automatic sw.HEAT-COOL / Avtomatski preklop ogr.-hl.; 4 = Switch with ID2 input / Preklop preko vhoda ID2 | 1: 1 (Heating)<br>2: 1 (Heating)<br>3: 1 (Heating) | duo 1 · 1 · 1<br>mono 1 · 1 · 1 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, D |
| `heating_regulation` | 1: `2_Reg_po_RF_AF_KONST_MK1`<br>2: `2_Reg_po_RF_AF_KONST_MK2`<br>3: `2_Reg_po_RF_AF_KONST_DK3` | circuit | What heating regulates on. Ours: 4/4/3. SI: 'Reguliranje ogrevanja po'. | enum | ×1 | — | yes | 1..4 | 0 = (empty); 1 = Indoor temperature / Prostorski temperaturi; 2 = Outdoor temperature / Zunanja temperatura; 3 = Indoor+outdoor temp. / Prostorski in zunanji temp.; 4 = Constant temperature / Konstantni temperaturi | 1: 4 (Constant temperature)<br>2: 4 (Constant temperature)<br>3: 3 (Indoor+outdoor temp.) | duo 3 · 3 · 3<br>mono 1 · 1 · 4 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `cooling_regulation` | 1: `2_Reg_po_RF_AF_KONST_MK1_HL`<br>2: `2_Reg_po_RF_AF_KONST_MK2_HL`<br>3: `2_Reg_po_RF_AF_KONST_DK3_HL` | circuit | What cooling regulates on (same enum). SI: 'Reguliranje hlajenja po'. | enum | ×1 | — | yes | 1..4 | 0 = (empty); 1 = Indoor temperature / Prostorski temperaturi; 2 = Outdoor temperature / Zunanja temperatura; 3 = Indoor+outdoor temp. / Prostorski in zunanji temp.; 4 = Constant temperature / Konstantni temperaturi | 1: 4 (Constant temperature)<br>2: 3 (Indoor+outdoor temp.)<br>3: 3 (Indoor+outdoor temp.) | duo 3 · 3 · 3<br>mono 1 · 1 · 4 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `max_flow_heating` | 1: `2_Max_VF_MK1`<br>2: `2_Max_VF_MK2`<br>3: `2_Max_VF_DK3` | circuit | Maximum flow temperature in heating ('outlet' in the EN app = flow). In constant mode probably the flow setpoint while the timer is on (PLAN §5.4, R8). SI: 'Max. temperatura vtoka pri ogrevanju'. | float | ×10 | °C | yes | 80..600 (8.0 to 60.0 °C) | — | 1: 280 (28.0)<br>2: 370 (37.0)<br>3: 400 (40.0) | duo 400 · 400 · 400<br>mono 380 · 360 · 400 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, D |
| `min_flow_heating` | 1: `2_Min_VF_MK1`<br>2: `2_Min_VF_MK2`<br>3: `2_Min_VF_DK3` | circuit | Minimum flow temperature in heating. Note max range 8–60 °C vs min 8–50 °C. SI: 'Min. temperatura vtoka pri ogrevanju'. | float | ×10 | °C | yes | 80..500 (8.0 to 50.0 °C) | — | 1: 240 (24.0)<br>2: 300 (30.0)<br>3: 120 (12.0) | duo 270 · 270 · 270<br>mono 300 · 300 · 270 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, D |
| `hp_boost_for_circuit` | 1: `2_Povec_temp_TC_pri_MK1`<br>2: `2_Povec_temp_TC_pri_MK2`<br>3: — | circuit | Heat pump temperature increase above the mixing-circuit target ('Povišanje temp. TČ za potrebe mešalne veje'). Not on slot 3. Unit is a difference (K). SI: 'Povišanje temp. TČ za potrebe mešalne veje'. | float | ×10 | K | yes | 10..150 (1.0 to 15.0 K) | — | 1: 10 (1.0)<br>2: 50 (5.0)<br>3: — | duo 50 · 50 · —<br>mono 20 · 20 · — | high | J:settings_dyn_1/settings_dyn_2, D |
| `curve_parallel_shift` | 1: `2_Zamik_krivulje_MK1`<br>2: `2_Zamik_krivulje_MK2`<br>3: `2_Zamik_krivulje_DK3` | circuit | Parallel shift of the heating curve; 0.1 step = 0.1 K (B, Duo p. 44). SI: 'Korekcija vzporednega premika ogrevalne krivulje'. | float | ×10 | K | yes | -150..150 (-15.0 to 15.0) | — | 1: -1 (-0.1)<br>2: 50 (5.0)<br>3: 0 (0.0) | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, B, D |
| `curve_slope` | 1: `2_Nagib_krivulje_MK1`<br>2: `2_Nagib_krivulje_MK2`<br>3: `2_Nagib_krivulje_DK3` | circuit | Slope correction of the heating curve; pivots at +5 °C outdoor, value = shift at −10 °C (B, Duo p. 44). SI: 'Korekcija nagiba ogrevalne krivulje'. | float | ×10 | K | yes | -150..150 (-15.0 to 15.0) | — | 1: 0 (0.0)<br>2: 0 (0.0)<br>3: 0 (0.0) | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, B, D |
| `room_sensor_type` | 1: `2_Sobni_DPWT_PGD1`<br>2: `2_Sobni_2_DPWT_PGD1`<br>3: `2_Sobni_3_DPWT_PGD1` | circuit | Room sensor type. All three are 2 (NTC) on ours although no sensor is connected; mono slot 1 = 5 (ThTune). Manual: slot 3 supports only NTC / thermostat. SI: 'Vrsta tipala prostorske temperature'. | enum | ×1 | — | installer | 1..5 | 0 = (empty); 1 = DPWT Carel; 2 = NTC; 3 = ON/OFF thermostat; 4 = Wireless ORCA / Brezžično ORCA; 5 = ThTune | 1: 2 (NTC)<br>2: 2 (NTC)<br>3: 2 (NTC) | duo 2 · 2 · 2<br>mono 5 · 2 · 2 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, B, X, D |
| `min_flow_cooling` | 1: `2_Min_VF_MK1_HL`<br>2: `2_Min_VF_MK2_HL`<br>3: `2_Min_VF_DK3_HL` | circuit | Minimum flow temperature in cooling (condensation guard). SI: 'Min. temperatura vtoka pri hlajenju'. | float | ×10 | °C | yes | 90..400 (9.0 to 40.0 °C) | — | 1: 180 (18.0)<br>2: 175 (17.5)<br>3: 180 (18.0) | duo 180 · 180 · 180<br>mono 180 · 180 · 180 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, D |
| `cooling_flow_at_20` | 1: `2_Tocka_1_20st_HL_MK1`<br>2: `2_Tocka_1_20st_HL_MK2`<br>3: `2_Tocka_1_20st_HL_DK3` | circuit | Cooling curve point 1: desired flow temperature at +20 °C outdoor. SI: 'Želena temp.vtoka pri zunanji temp. +20°C'. | float | ×10 | °C | yes | 90..400 (9.0 to 40.0 °C) | — | 1: 185 (18.5)<br>2: 250 (25.0)<br>3: 250 (25.0) | duo 250 · 250 · 250<br>mono 250 · 250 · 250 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `cooling_flow_at_30` | 1: `2_Tocka_2_30st_HL_MK1`<br>2: `2_Tocka_2_30st_HL_MK2`<br>3: `2_Tocka_2_30st_HL_DK3` | circuit | Cooling curve point 2: desired flow temperature at +30 °C outdoor. SI: 'Želena temp.vtoka pri zunanji temp. +30°C'. | float | ×10 | °C | yes | 90..400 (9.0 to 40.0 °C) | — | 1: 185 (18.5)<br>2: 150 (15.0)<br>3: 150 (15.0) | duo 150 · 150 · 150<br>mono 150 · 150 · 150 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `max_flow_cooling` | 1: `2_Max_VF_MK1_HL`<br>2: `2_Max_VF_MK2_HL`<br>3: — | circuit | Probably maximum flow temperature in cooling. Not in the app; absent on mono; no DK3 variant in all_fields. | float | ×10 | °C | no | ? | — | 1: 250 (25.0)<br>2: 400 (40.0)<br>3: — | duo 250 · 400 · —<br>mono – · – · — | low | N, X, D |
| `pump_stop_delay` | 1: `2_Cas_zakasn_izkl_C1`<br>2: `2_Cas_zakasn_izkl_C2`<br>3: `2_Cas_zakasn_izkl_C3` | circuit | Run-on time of the circuit pump P1/P2/P3 after demand ends. SI: 'Zakasnitev izklopa obtočne črpalke Č1'. | int | ×1 | min | installer | 0..600 | — | 1: 30<br>2: 20<br>3: 1 | duo 1 · 1 · 1<br>mono 0 · 1 · 1 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `mixing_valve_run_time` | 1: `2_Cas_MP1_za_90st`<br>2: `2_Cas_MP2_za_90st`<br>3: — | circuit | Mixing valve actuator 90° run time. Present for slot 1 even on DK1. SI: 'Čas rotacije mot. pogona mešalnega ventila, za 90°'. | int | ×1 | s | installer | 10..600 | — | 1: 120<br>2: 120<br>3: — | duo 120 · 120 · —<br>mono 120 · 120 · — | high | J:settings_dyn_1/settings_dyn_2, D |
| `external_on_contact` | 1: `2_Kontakt_ekst_vklop_NC_NO`<br>2: `2_Kontakt_ekst_vklop_2_NC_NO`<br>3: `2_Kontakt_ekst_vklop_3_NC_NO` | circuit | Contact type of the external switch-on input for the circuit. SI: 'Vrsta kontakta eksternega vklopa'. | enum | ×1 | — | installer | 0..1 | 0 = NO; 1 = NC | 1: 1 (NC)<br>2: 1 (NC)<br>3: 0 (NO) | duo 1 · 1 · 0<br>mono 1 · 1 · 1 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `flow_sensor_calibration` | 1: `2_Kalibracija_VF`<br>2: `2_Kalibracija_VF2`<br>3: — | circuit | Flow sensor offset ('vtok' = flow; EN app says 'MC temperature sensor'). SI: 'Kalibracija tipala vtoka'. | float | ×10 | K | installer | -99..99 (-9.9 to 9.9 K) | — | 1: 0 (0.0)<br>2: 0 (0.0)<br>3: — | duo 0 · 0 · —<br>mono 0 · 0 · — | high | J:settings_dyn_1/settings_dyn_2, D |
| `room_sensor_calibration` | 1: `2_Kalibracija_RF`<br>2: `2_Kalibracija_RF2`<br>3: `2_Kalibracija_RF3` | circuit | Room sensor offset. SI: 'Kalibracija tipala prostorske temperature'. | float | ×10 | K | installer | -99..99 (-9.9 to 9.9 K) | — | 1: 0 (0.0)<br>2: 0 (0.0)<br>3: 0 (0.0) | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_heating_switch` | 1: `2_Aktiv_avtom_preklop_zima_MK1`<br>2: `2_Aktiv_avtom_preklop_zima_MK2`<br>3: `2_Aktiv_avtom_preklop_zima_DK3` | circuit | Automatic heating on/off by outdoor temperature (summer/winter). SI app label is English. SI: 'Automatic switch heating summer-winter'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1: 1<br>2: 0<br>3: 0 | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_heating_switch_temp` | 1: `2_Temp_za_preklop_zima_MK1`<br>2: `2_Temp_za_preklop_zima_MK2`<br>3: `2_Temp_za_preklop_zima_DK3` | circuit | Outdoor temperature for the automatic heating summer/winter switch. SI: 'Zun. temp. za vklop-izklop ogrevanja ZIMA-POLETJE'. | float | ×10 | °C | yes | 50..300 (5.0 to 30.0 °C) | — | 1: 180 (18.0)<br>2: 220 (22.0)<br>3: 160 (16.0) | duo 160 · 160 · 160<br>mono 140 · 160 · 160 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_heating_switch_delay` | 1: `2_Cas_ur_preklop_zima_MK1`<br>2: `2_Cas_ur_preklop_zima_MK2`<br>3: `2_Cas_ur_preklop_zima_DK3` | circuit | Delay for the automatic heating switch. SI: 'Time delay for switch heating summer-winter'. | int | ×1 | h | yes | 1..90 | — | 1: 24<br>2: 10<br>3: 24 | duo 24 · 24 · 24<br>mono 1 · 1 · 1 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_cooling_switch` | 1: `2_Aktiv_avtom_preklop_poletje_MK1`<br>2: `2_Aktiv_avtom_preklop_poletje_MK2`<br>3: `2_Aktiv_avtom_preklop_poletje_DK3` | circuit | Automatic cooling on/off by outdoor temperature. SI: 'Avtom. vklop-izklop hlajenja ZIMA-POLETJE'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1: 0<br>2: 0<br>3: 0 | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_cooling_switch_temp` | 1: `2_Temp_preklop_poletje_MK1_HL`<br>2: `2_Temp_preklop_poletje_MK2_HL`<br>3: `2_Temp_preklop_poletje_DK3_HL` | circuit | Outdoor temperature for the automatic cooling switch. SI: 'Outdoor temp.for aut.sw. cooling winter-summer'. | float | ×10 | °C | yes | 50..300 (5.0 to 30.0 °C) | — | 1: 210 (21.0)<br>2: 210 (21.0)<br>3: 210 (21.0) | duo 210 · 210 · 210<br>mono 210 · 210 · 210 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `auto_cooling_switch_delay` | 1: `2_Cas_ur_preklop_poletje_MK1_HL`<br>2: `2_Cas_ur_preklop_poletje_MK2_HL`<br>3: `2_Cas_ur_preklop_poletje_DK3_HL` | circuit | Delay for the automatic cooling switch. SI: 'Zakasnitev za vklop-izklop hlajenja ZIMA-POLETJE'. | int | ×1 | h | yes | 1..90 | — | 1: 24<br>2: 24<br>3: 24 | duo 24 · 24 · 24<br>mono 24 · 24 · 24 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, D |
| `timer_programme` | 1: `2_Izbira_TIMERJA_MK1`<br>2: `2_Izbira_TIMERJA_MK2`<br>3: `2_Izbira_TIMERJA_MK3` | circuit | Timer programme of the circuit (slot 3 uses `_MK3`). Verified: selects the higher/lower room setpoint (§5). SI: 'Izbira časovnega programa'. | enum | ×1 | — | yes | 0..5 | 0 = 24 hour / 24-urni režim; 1 = According to timer 1 / Po časovnem programu 1; 2 = According to timer 2 / Po časovnem programu 2; 3 = According to timer 3 / Po časovnem programu 3; 4 = According to timer 4 / Po časovnem programu 4; 5 = According to timer 5 / Po časovnem programu 5 | 1: 2 (According to timer 2)<br>2: 5 (According to timer 5)<br>3: 0 (24 hour) | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, C, T, D |
| `low_regime_action` | 1: `2_Ponoci_min_temp_IZKLOP_MK1`<br>2: `2_Ponoci_min_temp_IZKLOP_MK2`<br>3: `2_Ponoci_min_temp_IZKLOP_DK3` | circuit | What the circuit does outside its timer ranges: switch off, or run at the lower temperature. Ours slot 1 = off, which matches P1 off and HP target 9.0 °C at night. SI: 'Delovanje ob preklopu na nižji režim'. | enum | ×1 | — | yes | 0..1 | 0 = OFF / Izklop; 1 = LOWER TEMPERATURE / NIŽJA TEMPERATURA | 1: 0 (OFF)<br>2: 0 (OFF)<br>3: 0 (OFF) | duo 1 · 0 · 0<br>mono 0 · 0 · 0 | high | J:settings_dyn_1/settings_dyn_2/settings_dyn_3, I, D |
| `low_regime_action_cooling` | 1: `2_Ponoci_min_temp_IZKLOP_MK1_HL`<br>2: `2_Ponoci_min_temp_IZKLOP_MK2_HL`<br>3: `2_Ponoci_min_temp_IZKLOP_DK3_HL` | circuit | Cooling counterpart of the low-regime action (by name). Not in the app. `_MK2_HL` is E_UNKNOWNTAG on ours but exists on duo. | enum | ×1 | — | no | 0..1? | presumably as heating: 0 = off; 1 = lower temperature | 1: 0<br>2: E_UNKNOWNTAG<br>3: 0 | duo 0 · 0 · 0<br>mono – · – · – | low | N, X, D |
| `room_setpoint_high` | 1: `2_Temp_prostor_dnevna`<br>2: `2_Temp_prostor_dnevna_OK2`<br>3: `2_Temp_prostor_dnevna_OK3` | circuit | Higher-regime ('day') room setpoint; active inside timer ranges or in 24 h mode. Not in the app recording (no room sensor, widgets inactive); range from old config only. | float | ×10 | °C | yes | 100..350 (10.0–35.0 °C, old config; unverified) | — | 1: 225 (22.5)<br>2: 300 (30.0)<br>3: 220 (22.0) | duo 201 · 220 · 220<br>mono 220 · 225 · 220 | medium | C, T, B, D |
| `room_setpoint_low` | 1: `2_Temp_prostor_nocna`<br>2: `2_Temp_prostor_nocna_OK2`<br>3: `2_Temp_prostor_nocna_OK3` | circuit | Lower-regime ('night') room setpoint; active outside timer ranges. | float | ×10 | °C | yes | 100..350 (10.0–35.0 °C, old config; unverified) | — | 1: 220 (22.0)<br>2: 261 (26.1)<br>3: 190 (19.0) | duo 184 · 190 · 190<br>mono 210 · 210 · 190 | medium | C, T, B, D |

### 2.4 Heating circuits: live values and indicators (slot 1 / 2 / 3)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `room_temperature` | 1: `2_Temp_Prostora`<br>2: `2_Temp_RF2`<br>3: `2_Temp_RF3` | circuit | Room temperature of the circuit; -9999 = no sensor. Home widget value per circuit. | float | ×10 | °C | no | — | — | 1: -9999 (n/c)<br>2: -9999 (n/c)<br>3: -9999 (n/c) | duo 207 · -9999 · -9999<br>mono 219 · 229 · -9999 | high | J:home, C, R, I, H, M, D |
| `room_setpoint_active` | 1: `2_Zahtevana_RF_MK_1`<br>2: `2_Zahtevana_RF_MK_2`<br>3: `2_Zahtevana_RF_DK_3` | circuit | Active ('desired') room setpoint = high or low setpoint depending on the timer. Verified at 3 moments (§5.3). `2_Zahtevana_RF_DK_1` exists only on duo (0). | float | ×10 | °C | no | — | — | 1: 220 (22.0)<br>2: 261 (26.1)<br>3: 220 (22.0) | duo 201 · 220 · 220<br>mono 220 · 225 · 220 | high | C, R, I, M, T, D |
| `flow_temperature` | 1: `2_Poti2`<br>2: `2_Temp_VF2`<br>3: — | circuit | Flow temperature of the circuit (sensors TM1 on B4, TM2 on B10). Slot 3 has no flow sensor. Ours slot 2 = -9999 (MK2 has no flow sensor connected). Duo reads 21.0 °C on VF2 without a circuit 2. | float | ×10 | °C | no | — | — | 1: 228 (22.8)<br>2: -9999 (n/c)<br>3: — | duo 207 · 210 · —<br>mono 306 · -9999 · — | high | C, R, I, M, B, D |
| `flow_target` | 1: `2_Temp_zelena_MK_1`<br>2: `2_Temp_zelena_MK_2`<br>3: — | circuit | Target flow temperature of the circuit. Ours slot 1 = 0 (DK1, no mixing valve), slot 2 = 12.0 although the circuit is off. | float | ×10 | °C | no | — | — | 1: 0 (0.0)<br>2: 120 (12.0)<br>3: — | duo 0 · 120 · —<br>mono 0 · 0 · — | high (tag) / medium (meaning on DK) | C, R, I, M, D |
| `mixing_valve_state` | 1: `2_Delovanje_MP1`<br>2: `2_Delovanje_MP2`<br>3: — | circuit | Mixing valve motor state. Only 0 observed. | enum | ×1 | — | no | 0..2 | 0 = off (Izklop, app); 1 = opening?; 2 = closing? (old config comment) | 1: 0<br>2: 0<br>3: — | duo 0 · 0 · —<br>mono 0 · 0 · — | high (tag) / medium (enum) | C, R, I, M, D |
| `mixing_valve_position` | 1: `2_Odstotki_odprtosti_MP1`<br>2: `2_Odstotki_odprtosti_MP2`<br>3: — | circuit | Mixing valve opening. Ours slot 2 = 90 = '9.0%' in both app snapshots. | float | ×10 | % | no | 0..1000 | — | 1: 0 (0.0)<br>2: 90 (9.0)<br>3: — | duo 0 · 0 · —<br>mono 0 · 0 · — | high | C, R, I, M, D |
| `circuit_pump` | 1: `2_Vklop_C1`<br>2: `2_Vklop_C2`<br>3: `2_Vklop_C3` | circuit | Circuit pump P1/P2/P3 running. **P3 is shared by DK3 and the solar pump** (no schema has both; B Duo p. 41). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 1: 0<br>2: 0<br>3: 0 | duo 0 · 0 · 0<br>mono 1 · 0 · 0 | high (slots 1–2) / medium (slot 3) | C, R, I, M, B, D |
| `room_thermostat_input` | 1: `2_Vhod_ON_OFF_RF1`<br>2: —<br>3: `2_Vhod_ON_OFF_RF3` | circuit | State of an ON/OFF room-thermostat input (by name). `_RF1` E_UNKNOWNTAG on ours, 0 on duo; `_RF3` 0 on ours. | bool | ×1 | — | no | 0..1 | — | 1: E_UNKNOWNTAG<br>2: —<br>3: 0 | duo 0 · — · 0<br>mono – · — · – | low | N, X, D |
| `demand_on` | 1: `2_PogojPGDT_N_OSN_ON_OK1`<br>2: `2_PogojPGDT_N_OSN_ON_OK2`<br>3: `2_PogojPGDT_N_OSN_ON_OK3` | circuit | Home-page indicator. E_UNKNOWNTAG on ours (null in app). On duo/mono exactly one of ON/OFF is 1 for each present element and both are 0 for absent ones; ON matched 'element below its setpoint / requesting heat' in all 5 cases (§7). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 1: E_UNKNOWNTAG<br>2: E_UNKNOWNTAG<br>3: E_UNKNOWNTAG | duo 0 · 0 · 0<br>mono 1 · 0 · 0 | low | J:home, X, D |
| `demand_off` | 1: `2_PogojPGDT_N_OSN_OFF_OK1`<br>2: `2_PogojPGDT_N_OSN_OFF_OK2`<br>3: `2_PogojPGDT_N_OSN_OFF_OK3` | circuit | Complement of `demand_on` (satisfied). E_UNKNOWNTAG on ours. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 1: E_UNKNOWNTAG<br>2: E_UNKNOWNTAG<br>3: E_UNKNOWNTAG | duo 1 · 0 · 0<br>mono 0 · 1 · 0 | low | J:home, X, D |

### 2.5 Hot water (SV)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `dhw_enable` | `2_SV_vklop` | DHW | DHW heating on/off. SI: 'Aktiviranje ogrevanja sanitarne vode'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 1 | duo 1 · mono 1 | high | J:settings_hot_water, C, D |
| `dhw_temp_top` | `2_Poti3` | DHW | DHW tank top temperature (TB on B8). Home DHW widget value; info line 2. | float | ×10 | °C | no | — | — | 391 (39.1) | duo 430 · mono 365 | high | J:home, C, R, I, M, H, B, D |
| `dhw_temp_bottom` | `2_Poti4` | DHW | DHW tank bottom temperature (LB on B11). -9999 on mono (no sensor, `2_Tipalo_BF2` = 0). | float | ×10 | °C | no | — | — | 241 (24.1) | duo 421 · mono -9999 | high | C, R, I, M, B, X, D |
| `dhw_setpoint_high` | `2_Temp_vode_sanitarna` | DHW | Higher DHW setpoint (inside timer ranges or 24 h). SI: 'VIŠJA TEMPERATURA'. | float | ×10 | °C | yes | 80..550 (8.0 to 55.0 °C) | — | 420 (42.0) | duo 445 · mono 440 | high | J:dhw_heating/settings_hot_water, C, B, D |
| `dhw_setpoint_low` | `2_Temp_vode_sanitarna_NIZJA` | DHW | Lower DHW setpoint (outside timer ranges). SI: 'NIŽJA TEMPERATURA'. | float | ×10 | °C | yes | 80..550 (8.0 to 55.0 °C) | — | 360 (36.0) | duo 150 · mono 150 | high | J:dhw_heating/settings_hot_water, B, D |
| `dhw_on_difference` | `2_Diferenca_vklopa_SV` | DHW | DHW switch-on hysteresis. SI: 'Diferenca vklopa'. | float | ×10 | K | yes | 0..80 (0.0 to 8.0 K) | — | 60 (6.0) | duo 40 · mono 35 | high | J:settings_hot_water, C, D |
| `dhw_hp_boost` | `2_Povec_temp_TC_pri_SV` | DHW | HP temperature increase above the DHW setpoint. Mono: HP target 47.0 = DHW 44.0 + 3.0. SI: 'Povišanje temp. TČ za potrebe ogrevanja SV'. | float | ×10 | K | yes | 10..150 (1.0 to 15.0 K) | — | 85 (8.5) | duo 50 · mono 30 | high | J:settings_hot_water, X, D |
| `dhw_timer_programme` | `2_Izbira_TIMERJA_SV` | DHW | DHW timer programme (ours 4). SI: 'Izbira časovnega programa'. | enum | ×1 | — | yes | 0..5 | 0 = 24 hour / 24-urni režim; 1 = According to timer 1 / Po časovnem programu 1; 2 = According to timer 2 / Po časovnem programu 2; 3 = According to timer 3 / Po časovnem programu 3; 4 = According to timer 4 / Po časovnem programu 4; 5 = According to timer 5 / Po časovnem programu 5 | 4 (According to timer 4) | duo 0 · mono 0 | high | J:settings_hot_water, T, D |
| `dhw_24h_flag` | `2_SV_24ur_timer` | DHW | Name says 'DHW on 24 h timer'. Ours = 1 although `2_Izbira_TIMERJA_SV` = 4; duo = 1 with selection 0. Stale or different meaning; do not use. | bool | ×1 | — | no | 0..1 | — | 1 | duo 1 · mono – | low | N, X, D |
| `legionella_enable` | `2_Legionela_vklop` | DHW | Anti-legionella programme on/off. SI: 'Aktiviranje protilegionelnega programa'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:settings_hot_water, D |
| `legionella_temperature` | `2_Temperatura_legionela` | DHW | Anti-legionella target temperature. SI: 'Želena temperatura protilegionelnega programa'. | float | ×10 | °C | yes | 650..700 (65.0 to 70.0 °C) | — | 700 (70.0) | duo 650 · mono 650 | high | J:settings_hot_water, D |
| `legionella_day` | `2_On_Dan_Legionella` | DHW | Weekday the programme starts. SI: 'Dan pričetka delovanja protilegionelnega programa'. | enum | ×1 | — | yes | 1..7 | 0 = (empty); 1 = Monday / Ponedeljek; 2 = Tuesday / Torek; 3 = Wednesday / Sreda; 4 = Thursday / Četrtek; 5 = Friday / Petek; 6 = Saturday / Sobota; 7 = Sunday / Nedelja | 7 (Sunday) | duo 7 · mono 7 | high | J:settings_hot_water, D |
| `legionella_hour` | `2_On_Ura_Legionella` | DHW | Hour the programme starts (app suffix ':00'). SI: 'Ura pričetka delovanja protilegionelnega programa'. | int | ×1 | h (hour of day) | yes | 0..23 | — | 14 | duo 2 · mono 2 | high | J:settings_hot_water, D |
| `legionella_minute` | `2_On_Min_Legionella` | DHW | Start minute (by name; 0 on all pumps; not in the app). | int | ×1 | min | no | 0..59? | — | 0 | duo 0 · mono 0 | medium-low | N, X, D |
| `legionella_cycle` | `2_Legionela_Cikel` | DHW | Repeat interval. SI: 'Cikel delovanja protilegionelnega programa'. | enum | ×1 | — | yes | 1..4 | 0 = (empty); 1 = Every week / Tedenski; 2 = Every two weeks / Dvotedenski; 3 = Every month / Mesečni; 4 = Every two months / Dvomesečni | 1 (Every week) | duo 1 · mono 4 | high | J:settings_hot_water, D |
| `legionella_disabled_flag` | `2_Legionela_IZKLJ` | DHW | 1 on ours/duo where `2_Legionela_vklop` = 0: probably the derived 'disabled' flag. | bool | ×1 | — | no | 0..1 | — | 1 | duo 1 · mono – | low | N, X, D |
| `dhw_configured` | `2_PogojPGDT_Shema_in_tipalo_SV` | DHW | DHW present and its sensor configured (1 on all pumps). See §3. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 1 | duo 1 · mono 1 | high | J:home, X, D |
| `dhw_demand_on` | `2_PogojPGDT_N_OSN_ON_SV` | DHW | Home-page DHW demand indicator (see `demand_on`). E_UNKNOWNTAG on ours. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | E_UNKNOWNTAG | duo 0 · mono 1 | low | J:home, X, D |
| `dhw_demand_off` | `2_PogojPGDT_N_OSN_OFF_SV` | DHW | Complement. E_UNKNOWNTAG on ours. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | E_UNKNOWNTAG | duo 1 · mono 0 | low | J:home, X, D |

### 2.6 Solar

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `solar_collector_temperature` | `2_Poti5` | solar | Collector temperature (TS on B7). Ours 7.5 °C (EN snapshot 7.8). -9999 on duo/mono (no solar). | float | ×10 | °C | no | — | — | 75 (7.5) | duo -9999 · mono -9999 | high | C, R, I, M, B, X, D |
| `solar_pump` | `2_Vklop_C3` | solar | Solar pump state ('Stanje obt. črp. kolektorjev'). Same output P3 as circuit 3's pump. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | C, R, I, M, B, D |
| `solar_enable` | `2_SOLAR_VKLOP` | solar | Solar system activation. SI: 'Aktiviranje solarnega sistema'. | bool | ×1 | — | installer | 0..1 | 0 = off; 1 = on | 1 | duo 1 · mono 1 | high | J:settings_solar, C, D |
| `solar_target` | `2_SOLAR_Prost_SV` | solar | What the solar system heats (hydraulic choice). SI: 'Solarni sistem za ogrevanje'. | enum | ×1 | — | installer | 0..1 | 0 = DHW heating / Sanitarna voda; 1 = Room heating / Prostorov | 0 (DHW heating) | duo 0 · mono 0 | high | J:settings_solar, D |
| `solar_min_collector_temp` | `2_Min_Temp_SOLAR` | solar | Minimum collector temperature for starting DHW heating. SI: 'Min. temp. kolektorjev za vklop ogrevanja SV'. | float | ×10 | °C | yes | 200..700 (20.0 to 70.0 °C) | — | 500 (50.0) | duo 350 · mono 350 | high | J:settings_solar, D |
| `solar_on_difference` | `2_Dif_vklopa_SOLAR` | solar | Collector–tank difference to start the solar pump. SI: 'Diferenca temp. med kolektorji in SV, za vklop'. | float | ×10 | K | yes | 10..200 (1.0 to 20.0 K) | — | 100 (10.0) | duo 60 · mono 60 | high | J:settings_solar, D |
| `solar_off_difference` | `2_Dif_izklopa_SOLAR` | solar | Collector–tank difference to stop the solar pump. SI: 'Diferenca temp. med kolektorji in SV, za izklop'. | float | ×10 | K | yes | 10..100 (1.0 to 10.0 K) | — | 50 (5.0) | duo 30 · mono 30 | high | J:settings_solar, D |
| `solar_max_dhw_temp` | `2_Max_Temp_BF` | solar | Max. DHW temperature when heated by the collectors. SI: 'Max. temperatura SV, pri ogrevanju s kolektorji'. | float | ×10 | °C | installer | 200..850 (20.0 to 85.0 °C) | — | 800 (80.0) | duo 750 · mono 750 | high | J:settings_solar, D |
| `solar_max_collector_temp` | `2_Max_Temp_SOLAR` | solar | Max. collector temperature (protection). SI: 'Max. temperatura kolektorjev'. | float | ×10 | °C | installer | 200..2200 (20.0 to 220.0 °C) | — | 1000 (100.0) | duo 1400 · mono 1400 | high | J:settings_solar, D |
| `solar_dhw_safety_max` | `2_Max_varnostna_Temp_BF` | solar | Safety max. DHW temperature that stops the solar pump. SI: 'Najvišja temp. SV, pri ogrevanju s kolektorji'. | float | ×10 | °C | installer | 700..900 (70.0 to 90.0 °C) | — | 800 (80.0) | duo 850 · mono 850 | high | J:settings_solar, D |
| `dhw_delay_after_solar` | `2_Cas_zakasn_po_solarju` | solar | Delay of HP DHW heating after solar heating (a compressor delay, so installer). SI: 'Zakasnitev ogrevanja SV po delovanju solarja'. | int | ×1 | min | installer | 0..600 | — | 0 | duo 60 · mono 60 | high | J:settings_solar, D |
| `solar_pump_speed` | `2_Odstotki_SOLAR_PWM` | solar | Solar pump PWM speed % (menu: 'Hitrost solarne črpalke'). E_UNKNOWNTAG on ours; 0 on duo/mono. | float? | ? | % | no | ? | — | E_UNKNOWNTAG | duo 0 · mono 0 | medium | M, X, D |

### 2.7 Buffer tank (ZALOG)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `buffer_present` | `2_Shema_ZALOG` | buffer | Schema includes a buffer tank (ours 0, duo 0, mono 1). SI: 'Shema z zalogovnikom'. | bool | ×1 | — | installer | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 1 | high | J:settings_basic, C, X, D |
| `buffer_connected` | `2_ZALOG_Prikljucen` | buffer | Buffer connected (by name). 0 ours/duo; absent on mono. | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | low | N, X, D |
| `buffer_temperature` | `2_Temp_Zalog` | buffer | Buffer temperature (TZ on B9). -9999 on ours/duo; 33.6 °C on mono. | float | ×10 | °C | no | — | — | -9999 (n/c) | duo -9999 · mono 336 | high | C, R, I, M, B, X, D |
| `buffer_target` | `2_Izrac_temp_ZALOG` | buffer | Computed buffer target. 0 without buffer; mono 38.0 (= `2_Izrac_temp_OGR`). | float | ×10 | °C | no | — | — | 0 (0.0) | duo 0 · mono 380 | medium | C, X, D |
| `buffer_target_heating` | `2_Izrac_temp_ZALOG_OGR` | buffer | Computed buffer target for heating; ours 50.0 = `2_VISJA_Temp_ZALOG_OGR`; mono 38.0. | float | ×10 | °C | no | — | — | 500 (50.0) | duo 500 · mono 380 | medium | N, X, D |
| `buffer_target_cooling` | `2_Izrac_temp_ZALOG_HL` | buffer | Computed buffer target for cooling; ours 18.0 = `2_NIZJA_Temp_ZALOG_HL`; mono 9.0. | float | ×10 | °C | no | — | — | 180 (18.0) | duo 180 · mono 90 | medium | N, X, D |
| `buffer_high_heating` | `2_VISJA_Temp_ZALOG_OGR` | buffer | Desired higher buffer temperature in heating. SI: 'Želena višja temperatura pri režimu ogrevanja'. | float | ×10 | °C | yes | 120..550 (12.0 to 55.0 °C) | — | 500 (50.0) | duo 500 · mono 390 | high | J:settings_buffer, C, D |
| `buffer_low_heating` | `2_NIZJA_Temp_ZALOG_OGR` | buffer | Desired lower buffer temperature in heating. SI: 'Želena nižja temperatura pri režimu ogrevanja'. | float | ×10 | °C | yes | 120..550 (12.0 to 55.0 °C) | — | 300 (30.0) | duo 300 · mono 320 | high | J:settings_buffer, C, D |
| `buffer_high_cooling` | `2_VISJA_Temp_ZALOG_HL` | buffer | Desired higher buffer temperature in cooling. SI: 'Želena višja temperatura pri režimu hlajenja'. | float | ×10 | °C | yes | 90..400 (9.0 to 40.0 °C) | — | 300 (30.0) | duo 300 · mono 300 | high | J:settings_buffer, D |
| `buffer_low_cooling` | `2_NIZJA_Temp_ZALOG_HL` | buffer | Desired lower buffer temperature in cooling. SI: 'Želena nižja temperatura pri režimu hlajenja'. | float | ×10 | °C | yes | 90..400 (9.0 to 40.0 °C) | — | 180 (18.0) | duo 180 · mono 180 | high | J:settings_buffer, D |
| `buffer_on_difference` | `2_Diferenca_vklopa_ZALOG` | buffer | Buffer switch-on hysteresis. SI: 'Diferenca vklopa'. | float | ×10 | K | yes | 0..90 (0.0 to 9.0 K) | — | 40 (4.0) | duo 40 · mono 25 | high | J:settings_buffer, C, D |
| `buffer_timer_programme` | `2_Izbira_TIMERJA_ZALOG` | buffer | Buffer timer programme. SI: 'Izbira časovnega programa'. | enum | ×1 | — | yes | 0..5 | 0 = 24 hour / 24-urni režim; 1 = According to timer 1 / Po časovnem programu 1; 2 = According to timer 2 / Po časovnem programu 2; 3 = According to timer 3 / Po časovnem programu 3; 4 = According to timer 4 / Po časovnem programu 4; 5 = According to timer 5 / Po časovnem programu 5 | 0 (24 hour) | duo 0 · mono 0 | high | J:settings_buffer, D |
| `buffer_boost_for_mixing` | `2_Povec_temp_ZALOG_pri_MK` | buffer | Buffer temperature increase for mixing circuits (by name; 2.0 on ours/duo). Not in the app. | float | ×10 | K | no | ? | — | 20 (2.0) | duo 20 · mono – | low | N, X, D |
| `buffer_circuit_targets` | `2_Temp_zelena_MK_1_ZA_ZALOG`, `_MK_2_ZA_ZALOG`, `_DK_1_ZA_ZALOG`, `_DK_2_ZA_ZALOG`, `_DK_3_ZA_ZALOG and the `_HL` variants (MK_1, MK_2, DK_1, DK_2)` | buffer | Per-circuit desired temperature demanded from the buffer (heating / cooling). All 0 on ours/duo; absent on mono. | float | ×10 | °C | no | — | — | 9/9 S_OK; values 0 | duo 9/9 · mono 0/9 present | low | N, X, D |
| `buffer_value_337` | `2_Zalogovnik` | buffer | Unknown; 337 on both ours and duo, absent on mono. Not a temperature that fits anything. | int? | ? | — | no | ? | — | 337 | duo 337 · mono – | low | X, D |
| `buffer_power_limits` | `2_Max_moc_TC_pri_ZALOG`, `2_Min_moc_TC_pri_ZALOG` | buffer | HP power limits when charging the buffer (by analogy with `2_Max_moc_TC_pri_*`; 1000/0). Not in the app. | float | ×10 | % | no | ? | — | 2_Max_moc_TC_pri_ZALOG: 1000<br>2_Min_moc_TC_pri_ZALOG: 0 | duo 1000 · 0<br>mono – · – | low | N, X, D |

### 2.8 Cooling (global)

Per-circuit cooling settings are in the circuit table (`*_HL` rows, cooling curve points, auto switch).

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `cooling_active` | `2_Pogoj_maska_napis_hlajenje` | cooling | Home-page 'cooling' caption/icon condition (0 on all pumps). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | medium-low | J:home, X, D |
| `hp_power_limit_cooling` | `2_Max_moc_TC_pri_HLAJ` | cooling | HP power limit in space cooling. SI: 'Omejitev moči TČ pri hlajenju prostorov'. | float | ×10 | % | yes | 160..1000 (16.0 to 100.0 %) | — | 300 (30.0) | duo 350 · mono 350 | high | J:settings_basic, C, D |
| `hp_difference_limit_cooling` | `2_Limita_moci_pri_HLAJ` | cooling | HP difference limit in cooling. SI: 'Limita diference TČ pri hlajenju'. | float | ×10 | % | installer | 151..300 (15.1 to 30.0 %) | — | 152 (15.2) | duo 170 · mono 170 | high | J:settings_basic, D |

### 2.9 Electric heater / additional source

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `additional_source` | `2_Izbira_DOD_VIRA` | add. source | Which additional source is installed. Hardware choice (proposed installer). SI: 'Choose additional source'. | enum | ×1 | — | installer | 1..3 | 0 = (empty); 1 = ELECTRIC HEATER / ELEKTRIČNI GRELEC; 2 = Additional source / Eksterni dodatni vir; 3 = El. Heater and additional source | 1 (ELECTRIC HEATER) | duo 1 · mono – | high | J:settings_additional_source, D |
| `heater_mode` | `2_Vklop_Elektro_Grelci` | add. source | Electric heater mode. The touch display protects this menu with a user code (B, Touch p. 21). SI: 'Način vklopa električnih grelcev'. | enum | ×1 | — | yes | 0..2 | 0 = OFF / Izklop; 1 = Automatic / Avtomatsko; 2 = Manual / Ročno | 0 (OFF) | duo 1 · mono 0 | high | J:settings_additional_source, B, D |
| `heater_stages` | `2_Izbira_st_grelcev` | add. source | Number of active heater stages (3 kW each). Tied to the fuse sizing, so proposed installer. SI: 'Število aktivnih stopenj'. | enum | ×1 | — | installer | 1..3 | 0 = (empty); 1 = 1 rate (3kW) / 1 stopnja (3kW); 2 = 2 rates (6kW) / 2 stopnji (6kW); 3 = 3 rates (9kW) / 3 stopnje (9kW) | 2 (2 rates (6kW)) | duo 3 · mono 3 | high | J:settings_additional_source, B, D |
| `heater_stage1_delay` | `2_Elektro_Grelec_Zakasnitev_1_ST` | add. source | Start delay of heater stage 1. SI: 'Zakasnitev vklopa 1.stopnje'. | int | ×1 | min | yes | 1..1500 | — | 1 | duo 1 · mono 1 | high | J:settings_additional_source, D |
| `heater_stage2_delay` | `2_Elektro_Grelec_Zakasnitev_2_ST` | add. source | Start delay of heater stage 2. SI: 'Zakasnitev vklopa 2.stopnje'. | int | ×1 | min | yes | 1..1500 | — | 3 | duo 1 · mono 1 | high | J:settings_additional_source, D |
| `heater_stage3_delay` | `2_Elektro_Grelec_Zakasnitev_3_ST` | add. source | Start delay of heater stage 3. SI: 'Zakasnitev vklopa 3.stopnje'. | int | ×1 | min | yes | 1..1500 | — | 36 | duo 1 · mono 1 | high | J:settings_additional_source, D |
| `heater_stage1_outdoor_temp` | `2_Zun_temp_za_vklop_Grelec_1` | add. source | Outdoor temperature below which stage 1 may start. SI: 'Zunanja temperatura za vklop 1. stopnje'. | float | ×10 | °C | yes | -300..300 (-30.0 to 30.0 °C) | — | 220 (22.0) | duo -100 · mono -100 | high | J:settings_additional_source, C, D |
| `heater_stage2_outdoor_temp` | `2_Zun_temp_za_vklop_Grelec_2` | add. source | Outdoor temperature for stage 2 (ours 22.9 °C, outside the old config range). SI: 'Zunanja temperatura za vklop 2. stopnje'. | float | ×10 | °C | yes | -300..300 (-30.0 to 30.0 °C) | — | 229 (22.9) | duo -100 · mono -100 | high | J:settings_additional_source, C, D |
| `heater_stage3_outdoor_temp` | `2_Zun_temp_za_vklop_Grelec_3` | add. source | Outdoor temperature for stage 3. SI: 'Zunanja temperatura za vklop 3. stopnje'. | float | ×10 | °C | yes | -300..300 (-30.0 to 30.0 °C) | — | -299 (-29.9) | duo -100 · mono -100 | high | J:settings_additional_source, C, D |
| `heater_parallel` | `2_Vzporedno_Elektro_Grelci` | add. source | How many heater stages may run in parallel with the HP. SI: 'Vzporedno delovanje el. grelca in toplotne črpalke'. | enum | ×1 | — | yes | 0..3 | 0 = OFF / Izklop; 1 = 1. rates / 1 stopnja; 2 = 2. rates / 2 stopnji; 3 = 3 rates / 3 stopnje | 0 (OFF) | duo 0 · mono 0 | high | J:settings_additional_source, D |
| `additional_source_delay` | `2_Dodatni_Vir_Zakasnitev` | add. source | Start delay of the external additional source. SI: 'Zakasnitev vklopa'. | int | ×1 | min | yes | 0..999 | — | 1 | duo 0 · mono 0 | high | J:settings_additional_source, D |
| `additional_source_outdoor_temp` | `2_Temp_Vklop_Dod_Vir` | add. source | Outdoor temperature for starting the external additional source. SI: 'Zunanja temperatura za vklop'. | float | ×10 | °C | yes | -350..350 (-35.0 to 35.0 °C) | — | 200 (20.0) | duo -150 · mono -150 | high | J:settings_additional_source, D |
| `additional_source_parallel` | `2_Vzporedno_Dod_vir_izklop` | add. source | External source runs in parallel with the HP. SI: 'Vzporedno delovanje s toplotno črpalko'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:settings_additional_source, D |
| `heater_stage1_on` | `2_Vklop_ele_grelca_1` | add. source | Heater stage 1 relay (K1) on. The info page shows it as 'Eksterni dodatni vir' / 'Dodatni vir'. The old config's 'for defrosting the outdoor unit' is unsupported. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:home, C, R, I, M, D |
| `heater_stage2_on` | `2_Vklop_ele_grelca_2` | add. source | Heater stage 2 relay on (by name; 0 ours/duo/mono). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | medium | N, X, D |
| `heater_stage3_on` | `2_Vklop_ele_grelca_3` | add. source | Heater stage 3 relay on (by name). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | medium | N, X, D |
| `heater_icon_stage` | `2_Pogoj_ikona_ele_grelca_1`, `2_Pogoj_ikona_ele_grelca_2`, `2_Pogoj_ikona_ele_grelca_3` | add. source | Home-page heater icon conditions ('n stages on'). E_UNKNOWNTAG on ours; 0 on duo/mono. Derive from `2_Vklop_ele_grelca_n` instead. | bool | ×1 | — | no | 0..1 | — | 2_Pogoj_ikona_ele_grelca_1: E_UNKNOWNTAG<br>2_Pogoj_ikona_ele_grelca_2: E_UNKNOWNTAG<br>2_Pogoj_ikona_ele_grelca_3: E_UNKNOWNTAG | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | medium | J:home, H, X, D |
| `output13_function` | `2_Izhod_13_PEC_ELGR` | add. source | Output 13 assignment, boiler ('peč') vs electric heater (by name). Newer firmware splits it into `2_Izhod_13*`. | bool? | ×1 | — | installer | ? | — | 0 | duo 0 · mono – | low | N, X, D |

### 2.10 Alarms

No alarm texts in any source (R4). All 0 on ours at dump time.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `alarm_active` | `2_JE_ALARM` | alarms | Any alarm active; the app's only alarm signal (ALARM badge). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:home, H, D |
| `no_alarm` | `2_NI_ALARMA` | alarms | Inverse of `2_JE_ALARM` ('no alarm'; 1 on ours). | bool | ×1 | — | no | 0..1 | — | 1 | duo 1 · mono – | medium | N, X, D |
| `alarm_type` | `2_Vrsta_alarma` | alarms | Alarm type/code (menu: 'ALARM'). 0 everywhere; code table unknown. | enum | ×1 | — | no | ? | 0 = none?; others unknown (R4) | 0 | duo 0 · mono 0 | medium | M, N, D |
| `alarm_common_fault` | `2_Alarm_skupna_napaka` | alarms | Common fault, probably the outdoor unit fault input from the PAC-IF (B). | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium-low | N, B, D |
| `alarm_flow_switch` | `2_Alarm_pretocno_stikalo` | alarms | Flow switch alarm; candidate for 'Napaka senzorja pretoka'. | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium-low | N, D |
| `alarm_no_flow` | `2_Alarm_ni_pretoka` | alarms | No flow ('NI PRETOKA'): appears 5 s after flow stops, clears itself 30 s after flow returns (B). | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium | N, B, D |
| `alarm_hp_temp_low` | `2_Alarm_prenizka_temp_TC` | alarms | HP water temperature too low (by name). | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium-low | N, D |
| `alarm_floor_overtemp` | 1: `2_Alarm_Talno`<br>2: `2_Alarm_Talno_VF2`<br>3: — | alarms | Floor-heating over-temperature on flow sensor VF1 / VF2 (by name; TM1 is 'system protection', B). | bool | ×1 | — | no | 0..1 | — | 1: 0<br>2: 0<br>3: — | duo 0 · 0 · —<br>mono – · – · — | medium-low | N, B, D |
| `alarm_reset` | `2_Reset_alarmov` | alarms | Alarm reset command (by name). Candidate for a reset button after R4. | bool | ×1 | — | never | 0..1 | — | 0 | duo 0 · mono – | medium-low | N, D |
| `alarm_reset_hmi` | `2_Reset_ALARMA_iz_PGDT`, `2_Reset_KODE_iz_PGDT` | alarms | Reset requests from the pGD display (alarm, code). Commands. | bool | ×1 | — | never | 0..1 | — | 2_Reset_ALARMA_iz_PGDT: 0<br>2_Reset_KODE_iz_PGDT: 0 | duo 0 · 0<br>mono 0 · 0 | low | N, D |
| `alarm_newer_fw` | `2_NAPAKA`, `2_Alarm_RF1`, `2_Alarm_RF2`, `2_Alarm_RF3`, `2_Cas_zakasn_ALARM_RF1`, `2_Resetiranje_alarmov_FLOW/_OKV_FLOW/_TEMP/_TC/_VTOK` | alarms | Alarm tags of newer firmware (room-sensor alarms, error, per-type resets). All E_UNKNOWNTAG on ours; exist on duo (and partly mono). | bool/int | ×1 | — | never | ? | — | 0/10 S_OK; values  | duo 10/10 · mono 1/10 present | low | N, X, D |

### 2.11 Timers (time programmes)

Encoding and evidence in §5.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `timer_range_start_hour` | `2_TIMER_<p>_Ura_ON_<r> (p 1–5, r 1–3)` | timers | Range start hour ('VKLOP r'). Read-only in v1. | int | ×1 | h | no | 0..23 | — | 15 ranges, all decoded (§5) | present on both | high | T, M, D |
| `timer_range_start_minute` | `2_TIMER_<p>_Minute_ON_<r>` | timers | Range start minute. | int | ×1 | min | no | 0..59 | — | 15 ranges, all decoded (§5) | present on both | high | T, M, D |
| `timer_range_end_hour` | `2_TIMER_<p>_Ura_OFF_<r>` | timers | Range end hour ('IZKLOP r'). | int | ×1 | h | no | 0..23 | — | 15 ranges, all decoded (§5) | present on both | high | T, M, D |
| `timer_range_end_minute` | `2_TIMER_<p>_Minute_OFF_<r>` | timers | Range end minute. | int | ×1 | min | no | 0..59 | — | 15 ranges, all decoded (§5) | present on both | high | T, M, D |
| `timer_range_weekday` | `2_TIMER_<p>_<Ponedeljek\|Torek\|Sreda\|Cetrtek\|Petek\|Sobota\|Nedelja>_<r>` | timers | Range active on that weekday (Mon…Sun). A range with no day set is unused. | bool | ×1 | — | no | 0..1 | — | 15 ranges, all decoded (§5) | present on both | high | T, M, D |
| `quiet_timer_programme` | `2_Izbira_TIMERJA_TISJE` | timers | Quiet-mode timer programme. SI: 'Izbira časovnega programa tišjega delovanja'. | enum | ×1 | — | yes | 0..5 | 0 = 24 hour / 24-urni režim; 1 = According to timer 1 / Po časovnem programu 1; 2 = According to timer 2 / Po časovnem programu 2; 3 = According to timer 3 / Po časovnem programu 3; 4 = According to timer 4 / Po časovnem programu 4; 5 = According to timer 5 / Po časovnem programu 5 | 0 (24 hour) | duo 0 · mono 2 | high | J:settings_basic, D |
| `timer_selection_flags` | `2_Timer_MK1_24_ur`, `2_Timer_MK1_1 … 2_Timer_MK1_5` | timers | One-hot copy of `2_Izbira_TIMERJA_MK1` (ours: `_2` = 1). Newer firmware has the same for MK2, DK3, SV, ZALOG, TISJE. | bool | ×1 | — | no | 0..1 | — | 2_Timer_MK1_24_ur: 0<br>2_Timer_MK1_1: 0<br>2_Timer_MK1_5: 0<br>2_Timer_MK1_4: 0<br>2_Timer_MK1_3: 0<br>2_Timer_MK1_2: 1 | duo 1 · 0 · 0 · 0 · 0 · 0<br>mono – · – · – · – · – · – | high | X, D |
| `timer_24h_flags` | `2_MK1_24ur_timer`, `2_MK2_24ur_timer` | timers | 'Circuit on 24 h timer' flags; 0/0 on ours, consistent with selections 2 and 5. | bool | ×1 | — | no | 0..1 | — | 2_MK1_24ur_timer: 0<br>2_MK2_24ur_timer: 0 | duo 0 · 0<br>mono – · – | medium | N, X, D |
| `timer_edit_context` | `2_Izbiran_TIMER`, `2_Timer_SPREMEMBA_Nast`, `2_Timer_Nast_iz_MK1/_MK2/_SV/_ZALOG` | timers | Touch-display editing state (selected programme = 3 on all pumps, 'changed' flag, 'opened from' flags). | int/bool | ×1 | — | never | ? | — | 2_Izbiran_TIMER: 3<br>2_Timer_SPREMEMBA_Nast: 0<br>2_Timer_Nast_iz_MK1: 0<br>2_Timer_Nast_iz_MK2: 0<br>2_Timer_Nast_iz_SV: 0<br>2_Timer_Nast_iz_ZALOG: 0 | duo 3 · 0 · 0 · 0 · 0 · 0<br>mono 3 · 0 · – · – · – · – | medium-low | N, X, D |

### 2.12 Power limits

Percentages are ×10 (700 = 70.0 %).

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `hp_power_limit_heating` | `2_Max_moc_TC_pri_OGR` | power limits | HP power limit in space heating. SI: 'Omejitev moči TČ pri ogrevanju prostorov'. | float | ×10 | % | yes | 400..1000 (40.0 to 100.0 %) | — | 700 (70.0) | duo 1000 · mono 390 | high | J:settings_basic, C, D |
| `hp_power_limit_dhw` | `2_Max_moc_TC_pri_SV` | power limits | HP power limit in DHW heating. SI: 'Omejitev moči TČ pri ogrevanju SV'. | float | ×10 | % | yes | 400..1000 (40.0 to 100.0 %) | — | 650 (65.0) | duo 570 · mono 500 | high | J:settings_basic, C, D |
| `hp_power_limit_dhw_min` | `2_Min_moc_TC_pri_SV` | power limits | Minimum HP power in DHW heating (by name; 0). Not in app. | float | ×10 | % | no | ? | — | 0 (0.0) | duo 0 · mono – | low | N, D |
| `hp_difference_limit_heating` | `2_Limita_moci_pri_OGR` | power limits | HP difference limit in space heating. SI: 'Limita diference TČ pri ogrevanju prostorov'. | float | ×10 | % | installer | 151..300 (15.1 to 30.0 %) | — | 300 (30.0) | duo 300 · mono 300 | high | J:settings_basic, D |
| `hp_difference_limit_dhw` | `2_Limita_moci_pri_SV` | power limits | HP difference limit in DHW heating. SI: 'Limita diference TČ pri sanitarne vode'. | float | ×10 | % | installer | 151..300 (15.1 to 30.0 %) | — | 300 (30.0) | duo 300 · mono 300 | high | J:settings_basic, D |
| `hp_differential` | `2_Krivulja_TC` | power limits | HP differential 0–100 % (modulation band). SI: 'Diferenca toplotne črpalke 0-100%'. | float | ×10 | K | installer | 10..30 (1.0 to 3.0 K) | — | 20 (2.0) | duo 20 · mono 20 | high | J:settings_basic, D |
| `hp_stop_delay_at_limit` | `2_Zakasnitev_izklopa_TC` | power limits | HP stop delay after reaching the limit. SI: 'Zakasnitev izklopa TČ po doseženi limiti'. | int | ×1 | min | installer | 1..120 | — | 5 | duo 10 · mono 10 | high | J:settings_basic, D |

### 2.13 PV function and EVU (utility block)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pv_function` | `2_PV_Vklop` | PV/EVU | PV function on/off (driven by the PV contact on ID9). SI: 'PV FUNKCIJA'. | bool | ×1 | — | yes | 0..1 | 0 = off; 1 = on | 0 | duo 0 · mono 0 | high | J:settings_pv_function, B, D |
| `pv_contact_type` | `2_Kontakt_PF_f_NC_NO` | PV/EVU | Contact type of the PV input. SI: 'Vrsta kontakta PV funkcije'. | enum | ×1 | — | installer | 0..1 | 0 = NO; 1 = NC | 0 (NO) | duo 0 · mono 0 | high | J:settings_pv_function, D |
| `pv_signal` | `2_Signal_PV` | PV/EVU | PV input active (home 'PV' badge). E_UNKNOWNTAG on ours (null in app); 0 on duo/mono. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | E_UNKNOWNTAG | duo 0 · mono 0 | medium | J:home, H, X, D |
| `evu_signal` | `2_Signal_EVU` | PV/EVU | Utility block (EVU, input SR/ID10) active (home 'EVU' badge). E_UNKNOWNTAG on ours; 0 on duo/mono. | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | E_UNKNOWNTAG | duo 0 · mono 0 | medium | J:home, H, B, X, D |
| `pv_newer_fw` | `2_PV_Cas_za_vklop`, `2_PV_Cas_za_izklop`, `2_PV_Max_moc_TC`, `2_PV_Max_moc_TC_HL`, `2_PV_Elektro_Grelci`, `2_Max_Temp_BF_za_PV_f`, `2_Max_Temp_ZALOG_za_PV_f`, `2_MIN_HL_Temp_ZALOG_za_PV_f`, `2_I_PV`, `2_Signal_EVU_NI`, `2_Pogoj_MASKA_Signal_EVU` | PV/EVU | PV-function parameters and EVU helpers of newer firmware. All E_UNKNOWNTAG on ours. | ? | ? | — | no | ? | — | 0/11 S_OK; values  | duo 11/11 · mono 8/11 present | low | N, X, D |

### 2.14 Quiet mode (outdoor unit)

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `quiet_mode` | `2_Tisje_delov` | quiet mode | Quiet operation of the outdoor unit: how it is triggered. SI: 'Tišje delovanje zunanje enote'. | enum | ×1 | — | yes | 0..4 | 0 = OFF / Izklop; 1 = Manual activation / Ročni vklop; 2 = According to time plan / Po časovnem programu; 3 = According to outdoor temp. / Po zunanji temperaturi; 4 = Acc. to OT and time plan / Po zun.temp. in čas.prog. | 3 (According to outdoor temp.) | duo 0 · mono 2 | high | J:settings_basic, D |
| `quiet_outdoor_temp` | `2_Temp_AF_za_TISJE_DEL` | quiet mode | Outdoor temperature that activates quiet mode. SI: 'Zunanje temp. za vklop tišjega delovanja'. | float | ×10 | °C | yes | -300..300 (-30.0 to 30.0 °C) | — | 150 (15.0) | duo 10 · mono 10 | high | J:settings_basic, D |
| `quiet_power_limit` | `2_Max_moc_TC_TISJA` | quiet mode | HP power limit in quiet mode. SI: 'Omejitev moči TČ pri tišjem delovanju'. | float | ×10 | % | yes | 310..1000 (31.0 to 100.0 %) | — | 650 (65.0) | duo 570 · mono 650 | high | J:settings_basic, D |
| `quiet_active` | `2_Vklop_TISJE_DEL` | quiet mode | Quiet mode currently active (by name). 0 with mode 3 (by outdoor temp 15.0) at 7.4 °C outdoor. | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium-low | N, X, D |

### 2.15 Diagnostics, firmware, hardware identity, commissioning

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `firmware_day` | `2_Verzija_programa_DAN` | diagnostics | Controller program date, day. Ours 12, duo 20, mono 3. | int | ×1 | — | no | 1..31 | — | 12 | duo 20 · mono 3 | high | M, X, D |
| `firmware_month` | `2_Verzija_programa_MESEC` | diagnostics | Program date, month. Ours 12, duo 1, mono 11. | int | ×1 | — | no | 1..12 | — | 12 | duo 1 · mono 11 | high | M, X, D |
| `firmware_year` | `2_Verzija_programa_LETO` | diagnostics | Program date, 2-digit year. Ours 16, duo 20, mono 22. | int | ×1 | — | no | 0..99 | — | 16 | duo 20 · mono 22 | high | M, X, D |
| `firmware_build` | `2_Verzija_programa_ZAPOREDJE` | diagnostics | Program build/sequence number. Ours 61, duo 89, mono 103. Ours is the oldest firmware (2016-12-12). | int | ×1 | — | no | ? | — | 61 | duo 89 · mono 103 | high | M, X, D |
| `controller_type` | `2_Izbira_mPC_pCO3` | diagnostics | Built-in controller: µPC vs pCO3. 1 on all pumps; the info page says 'UPC Kartica' (µPC). | enum | ×1 | — | installer | ? | 1 = µPC ('UPC Kartica'); other = pCO3? | 1 | duo 1 · mono 1 | medium | I, N, X, M, D |
| `controller_flags` | `2_REG_mPC`, `2_REG_pCO3`, `2_REG_Doloci` | diagnostics | One-hot controller flags (ours 1/0/0) and 'to be determined'. | bool | ×1 | — | no | 0..1 | — | 2_REG_mPC: 1<br>2_REG_pCO3: 0<br>2_REG_Doloci: 0 | duo 1 · 0 · 0<br>mono – · – · – | medium | N, X, D |
| `outdoor_unit_brand` | `2_Izbira_Mitsubishi_Fujitsu` | diagnostics | Outdoor unit make. 1 ours/duo (info page: 'Mitsubishi'); 10 on mono (unknown code). | enum | ×1 | — | installer | ? | 1 = Mitsubishi; 10 = ? (mono) | 1 | duo 1 · mono 10 | medium | I, N, X, M, D |
| `outdoor_unit_flags` | `2_ZE_Mitsubishi`, `2_ZE_Fujitsu`, `2_ZE_Doloci` | diagnostics | One-hot outdoor unit flags (ours 1/0/0). | bool | ×1 | — | no | 0..1 | — | 2_ZE_Mitsubishi: 1<br>2_ZE_Fujitsu: 0<br>2_ZE_Doloci: 0 | duo 1 · 0 · 0<br>mono – · – · – | medium | N, X, D |
| `supply_voltage` | `2_DOVOD_230V_400V` | diagnostics | Supply 230 V vs 400 V (0 on ours/duo; which is which unknown). | enum | ×1 | — | installer | 0..1? | ? | 0 | duo 0 · mono – | low | N, X, D |
| `commissioned` | `2_Opravljen_prvi_zagon` | diagnostics | First start (commissioning) done (1 on all pumps). | bool | ×1 | — | never | 0..1 | — | 1 | duo 1 · mono 1 | medium | N, X, D |
| `commissioning_code_ok` | `2_Pravilna_koda_za_prvi_zagon` | diagnostics | Commissioning code accepted. | bool | ×1 | — | never | 0..1 | — | 1 | duo 1 · mono 1 | medium | N, X, D |
| `commissioned_by` | `2_Zagon_opravlja_oseba` | diagnostics | Installer index ('FIRST START MADE BY' on the info page; name not exported). | int | ×1 | — | never | ? | — | 2 | duo 45 · mono 16 | medium | I, N, M, D |
| `commissioning_datetime` | `2_Dan_ZAGONA`, `2_Mesec_ZAGONA`, `2_Leto_ZAGONA`, `2_Ura_ZAGONA`, `2_Min_ZAGONA` | diagnostics | Commissioning date and time (ours: October 2026, matches PLAN §4.2). | int | ×1 | — | no | date parts | — | 2_Dan_ZAGONA: 15<br>2_Mesec_ZAGONA: 10<br>2_Leto_ZAGONA: 26<br>2_Ura_ZAGONA: 13<br>2_Min_ZAGONA: 24 | duo 2 · 6 · 20 · 15 · 11<br>mono 23 · 4 · 24 · 14 · 46 | high | N, X, M, D |
| `clock_second` | `2_CURRENT_SECOND` | diagnostics | Controller clock, seconds. | int | ×1 | s | installer | 0..59 | — | 1 | duo 31 · mono 31 | high | N, X, D |
| `clock_set_values` | `2_NEW_DAY`, `2_NEW_MONTH`, `2_NEW_YEAR`, `2_NEW_HOUR`, `2_NEW_MINUTE` | diagnostics | Staging values for setting the clock: the app writes these, then sets `2_SET_*` = 1 (H: settings_basic page code). Write path for an installer setting. | int | ×1 | — | never | date/time parts (year 2-digit) | — | 2_NEW_DAY: 1<br>2_NEW_MONTH: 1<br>2_NEW_YEAR: 4<br>2_NEW_HOUR: 16<br>2_NEW_MINUTE: 52 | duo 1 · 1 · 4 · 0 · 0<br>mono 1 · 1 · 4 · 0 · 0 | high | H, D |
| `clock_set_triggers` | `2_SET_DAY`, `2_SET_MONTH`, `2_SET_YEAR`, `2_SET_HOUR`, `2_SET_MINUTE` | diagnostics | Clock-set triggers (write 1 after `2_NEW_*`). | bool | ×1 | — | never | 0..1 | — | 2_SET_DAY: 0<br>2_SET_MONTH: 0<br>2_SET_YEAR: 0<br>2_SET_HOUR: 0<br>2_SET_MINUTE: 0 | duo 0 · 0 · 0 · 0 · 0<br>mono 0 · 0 · 0 · 0 · 0 | high | H, D |
| `clock_hmi_buffers` | `2_Nastavitev_Ura`, `2_Nastavitev_Minuta` | diagnostics | Clock edit buffers of the display (7 / 59 on ours). Not the clock. | int | ×1 | — | never | ? | — | 2_Nastavitev_Ura: 7<br>2_Nastavitev_Minuta: 59 | duo 7 · 59<br>mono – · 59 | low | N, X, D |
| `service_mode` | `2_GESLO_PGDT_Vklop` | diagnostics | Service password entered (service mode active). Password tag: value never exposed. | bool | ×1 | — | never | 0..1 | 0 = off; 1 = on | <redacted> | duo <r> · mono <r> | high | J:home, D |

### 2.16 Installer and service settings

Never writable (PLAN §10).

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `schema` | `2_Shema` | installer | Wiring schema number (index into the 45 `wiring_diagrams`). SI: 'Vezalna shema'. | enum (list) | ×1 | — | installer | 1..45 | list `wiring_diagrams` (45 entries, §6) | 23 (DC1+MC2+DHW+SOLAR) | duo 3 · mono 7 | high | J:settings_basic, X, D |
| `contact_3way_valve` | `2_Kontakt_Preklopni_ventil` | installer | Contact type of the 3-way valve. SI: 'Vrsta kontakta preklopnega ventila'. | enum | ×1 | — | installer | 0..1 | 0 = NO; 1 = NC | 0 (NO) | duo 0 · mono 0 | high | J:settings_basic, D |
| `contact_id2` | `2_Kontakt_ID2` | installer | Contact type of input ID2 (external heating/cooling changeover, B). SI: 'Vrsta kontakta vhoda ID2'. | enum | ×1 | — | installer | 1..3 | 0 = (empty); 1 = NO; 2 = NC; 3 = Not activated / Ni aktiviran | 1 (NO) | duo 1 · mono 1 | high | J:settings_basic, B, D |
| `contact_hp_block` | `2_Kontakt_ekst_IZKLOP_TC` | installer | Contact type of the external HP block input. SI: 'Vrsta kontakta eksterne blokade TČ'. | enum | ×1 | — | installer | 0..1 | 0 = NO; 1 = NC | 0 (NO) | duo 0 · mono 0 | high | J:settings_basic, D |
| `contact_flow_switch` | `2_Kontakt_pret_stik_NC_NO` | installer | Contact type of the flow switch. SI: 'Vrsta kontakta pretočnega stikala'. | enum | ×1 | — | installer | 0..1 | 0 = NO; 1 = NC | 0 (NO) | duo 0 · mono 0 | high | J:settings_basic, D |
| `calibration_outdoor` | `2_Kalibracija_AF` | installer | Outdoor sensor offset (ours -1.1 K). SI: 'Kalibracija zunanjega tipala'. | float | ×10 | K | installer | -99..99 (-9.9 to 9.9 K) | — | -11 (-1.1) | duo 0 · mono 0 | high | J:settings_basic, D |
| `calibration_dhw_top` | `2_Kalibracija_BF_1` | installer | DHW top sensor offset. SI: 'Kalibracija tipala sanitarne vode - ZGORAJ'. | float | ×10 | K | installer | -99..99 (-9.9 to 9.9 K) | — | 0 (0.0) | duo 0 · mono 0 | high | J:settings_hot_water, D |
| `calibration_dhw_bottom` | `2_Kalibracija_BF_2` | installer | DHW bottom sensor offset. SI: 'Kalibracija tipala sanitarne vode - SPODAJ'. | float | ×10 | K | installer | -99..99 (-9.9 to 9.9 K) | — | 0 (0.0) | duo 0 · mono 0 | high | J:settings_hot_water, D |
| `p0_start_delay` | `2_Cas_prvega_vklopa_C0` | installer | HP start delay after P0 first starts. SI: 'Zakasnitev vklopa TČ po prvem vklopu Č0'. | int | ×1 | s | installer | 5..30 | — | 20 | duo 20 · mono 20 | high | J:settings_basic, D |
| `hp_min_off_time` | `2_Cas_izklopa_TC` | installer | Minimum outdoor unit off time. SI: 'Minimalni čas mirovanja zunanje enote'. | int | ×1 | min | installer | 1..120 | — | 2 | duo 10 · mono 10 | high | J:settings_basic, D |
| `p0_stop_delay` | `2_Cas_zakasn_izkl_C0` | installer | P0 run-on after the HP stops. SI: 'Zakasnitev izklopa Č0, po izklopu TČ'. | int | ×1 | min | installer | 1..600 | — | 15 | duo 5 · mono 5 | high | J:settings_basic, D |
| `p0_periodic_run` | `2_Cas_vklop_obcasni_C0` | installer | Periodic P0 run time (by name, 20). Not in the app. | int | ×1 | ? | installer | ? | — | 20 | duo 20 · mono – | low | N, X, D |
| `service_password_new` | `2_NOVO_GESLO_PGDT` | installer | Change service password. Never read or expose. SI: 'Sprememba gesla'. | int (4-digit input) | ×1 | — | never | — | — | <redacted> | duo <r> · mono <r> | high | J:settings_basic, D |
| `service_password_timeout` | `2_CAS_GESLO_PGDT` | installer | Service password active time. Never expose. SI: 'Čas aktivnega servisnega gesla'. | int | ×1 | s | never | 60..600 | — | <redacted> | duo <r> · mono <r> | high | J:settings_basic, D |
| `clock` | `2_CURRENT_HOUR`, `2_CURRENT_MINUTE`, `2_CURRENT_DAY`, `2_CURRENT_MONTH`, `2_CURRENT_YEAR` | installer | Controller clock (year 2-digit). Read-only diagnostic; set via `2_NEW_*`/`2_SET_*` only. SI: 'Nastavitev časa'. | int | ×1 | — | installer | hour 0..23, minute 0..59, day 1..31, month 1..12, year 0..99 | — | 2_CURRENT_HOUR: 20<br>2_CURRENT_MINUTE: 25<br>2_CURRENT_DAY: 31<br>2_CURRENT_MONTH: 10<br>2_CURRENT_YEAR: 26 | duo 18 · 45 · 8 · 12 · 25<br>mono 20 · 45 · 10 · 12 · 25 | high | J:home/settings_basic, H, M, D |
| `other_password_tags` | `2_GESLO_PGDT`, `2_Novo_Geslo`, `2_Potrdi_GESLO_Vklop`, `2_Geslo_ZAGON_AAXX`, `2_Geslo_ZAGON_CCXX`, `2_Geslo_ZAGON_XXBB`, `2_Geslo_ZAGON_XXDD`, `GESLO`, `Cas_GESLO` | installer | Password and password-state tags (service, commissioning code in 4 parts, HMI buffers). Never read or expose; values redacted here. | int | ×1 | — | never | — | — | 9/9 S_OK; values <r> | duo 9/9 · mono 9/9 present | high | N, M, D |
| `test_outputs` | `2_Vklop_TESTNI_C0…C3`, `2_Vklop_TESTNI_MP1_ODP/_ZAP`, `2_Vklop_TESTNI_MP2_ODP/_ZAP`, `2_Vklop_TESTNI_PV_OGR/_SV`, `2_TEST_C0…C3`, `2_TEST_MP1_ODP/_ZAP`, `2_TEST_MP2_ODP/_ZAP`, `2_TEST_PV_OGR/_SV`, `2_Preostanek_sekund_C0…C3/_MP1_ODP/_MP1_ZAP/_MP2_ODP/_MP2_ZAP/_PV_OGR/_PV_SV`, `2_Max_cas_test_C0` | installer | Manual output test menu ('TESTNI VKLOPI'): switches pumps, mixing valves and the 3-way valve by hand, with a countdown (max 600 s for P0). Never write. | bool / int (s) | ×1 | — | never | 0..1 / seconds | — | 31/31 S_OK; values 0, 600 | duo 31/31 · mono 21/31 present | high | M, B, N, D |

### 2.17 Topology signals

Meaning and cross-pump evidence in §3.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `schema_flag_mk1` | `2_Shema_MK1` | topology | Schema contains MK1. | bool | ×1 | — | installer | 0..1 | — | 0 | duo 0 · mono 0 | high | C, X, D |
| `schema_flag_dk1` | `2_Shema_DK1` | topology | Schema contains DK1. Absent on mono (newer fw). | bool | ×1 | — | installer | 0..1 | — | 1 | duo 1 · mono – | high | C, X, D |
| `schema_flag_mk2` | `2_Shema_MK2` | topology | Schema contains MK2. | bool | ×1 | — | installer | 0..1 | — | 1 | duo 0 · mono 0 | high | C, X, D |
| `schema_flag_dk2` | `2_Shema_DK2` | topology | Schema contains DK2. Absent on mono. | bool | ×1 | — | installer | 0..1 | — | 0 | duo 0 · mono – | high | C, X, D |
| `schema_flag_dk3` | `2_Shema_DK3` | topology | Schema contains DK3. | bool | ×1 | — | installer | 0..1 | — | 0 | duo 0 · mono 0 | high | X, D |
| `schema_flag_solar` | `2_Shema_SOLAR` | topology | Schema contains solar. | bool | ×1 | — | installer | 0..1 | — | 1 | duo 0 · mono 0 | high | C, X, D |
| `schema_flag_dhw` | `2_Shema_SV` | topology | Schema contains DHW. | bool | ×1 | — | installer | 0..1 | — | 1 | duo 1 · mono 1 | high | C, X, D |
| `circuit_present` | 1: `2_PogojPGDT_Shema_OK1`<br>2: `2_PogojPGDT_Shema_OK2`<br>3: — | topology | Circuit slot present in the schema (independent of on/off: ours slot 2 = 1 while switched off). | bool | ×1 | — | no | 0..1 | — | 1: 1<br>2: 1<br>3: — | duo 1 · 0 · —<br>mono 1 · 1 · — | high | C, X, D |
| `room_sensor_configured` | 1: `2_PogojPGDT_Shema_in_tipalo_OK1`<br>2: `2_PogojPGDT_Shema_in_tipalo_OK2`<br>3: `2_PogojPGDT_Shema_in_tipalo_OK3` | topology | Circuit present and room sensor configured. The app sets the home widget `data-active` from it (all 0 on ours). | bool | ×1 | — | no | 0..1 | 0 = off; 1 = on | 1: 0<br>2: 0<br>3: 0 | duo 1 · 0 · 0<br>mono 1 · 1 · 0 | high | J:home, C, H, X, D |
| `buffer_sensor_configured` | `2_PogojPGDT_Shema_in_tipalo_ZALOG` | topology | Buffer present and sensor configured. | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono – | medium | N, X, D |
| `element_upor` | 1: `2_PogojPGDT_Shema_in_Upor_OK1`<br>2: `2_PogojPGDT_Shema_in_Upor_OK2`<br>3: `2_PogojPGDT_Shema_in_Upor_OK3` | topology | Equals circuit-present on all 3 pumps ('upor' = resistor, i.e. resistive sensor?). `_SV` likewise. | bool | ×1 | — | no | 0..1 | — | 1: 1<br>2: 1<br>3: 0 | duo 1 · 0 · 0<br>mono 1 · 1 · 0 | low | X, D |
| `element_upor_dhw` | `2_PogojPGDT_Shema_in_Upor_SV` | topology | As above for DHW (1 on all). | bool | ×1 | — | no | 0..1 | — | 1 | duo 1 · mono 1 | low | X, D |
| `element_servisni` | 1: `2_PogojPGDT_Shema_in_Servisni_OK1`<br>2: `2_PogojPGDT_Shema_in_Servisni_OK2`<br>3: `2_PogojPGDT_Shema_in_Servisni_OK3` | topology | 0 everywhere (also `_SV`). Probably 'element present and in service mode'. Unknown. | bool | ×1 | — | no | 0..1 | — | 1: 0<br>2: 0<br>3: 0 | duo 0 · 0 · 0<br>mono 0 · 0 · 0 | low | X, D |
| `element_servisni_dhw` | `2_PogojPGDT_Shema_in_Servisni_SV` | topology | As above for DHW (0 on all). | bool | ×1 | — | no | 0..1 | — | 0 | duo 0 · mono 0 | low | X, D |
| `pgdt_1` | `2_PogojPGDT_1` | topology | 1 on ours/duo; unknown condition flag. | bool | ×1 | — | no | 0..1 | — | 1 | duo 1 · mono – | low | X, D |
| `sensor_flags` | `2_Tipalo_AF`, `2_Tipalo_BF1`, `2_Tipalo_BF2`, `2_Tipalo_KF`, `2_Tipalo_RF`, `2_Tipalo_RF2`, `2_Tipalo_RF3`, `2_Tipalo_VF1`, `2_Tipalo_VF2`, `2_Tipalo_Zalog`, `2_Tipalo_B11`, `2_Tipalo_B12` | topology | Per-input 'sensor fitted/enabled' flags (one row per input in §3). `2_Tipalo_AF` is on the app home page. | bool | ×1 | — | installer | 0..1 | — | 12/12 S_OK; values 0, 1 | duo 12/12 · mono 9/12 present | medium | J:home, B, X, D |

### 2.18 Derived HMI helper flags (do not expose)

The touch display derives one-hot flags from enums to show/hide menu rows. Verified against the source enum on ours; useful only as consistency checks.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `flags_circuit_mode` | `2_Rezim_MK1_1`, `2_Rezim_MK1_1_NOT`, `2_Rezim_MK1_4`, `2_Rezim_MK1_4_NOT` | helper | (`2_Rezim_MK1` == 1 / == 4) and negations. Ours 1,0,0,1 with mode 1. | bool | ×1 | — | no | 0..1 | — | 2_Rezim_MK1_1: 1<br>2_Rezim_MK1_1_NOT: 0<br>2_Rezim_MK1_4: 0<br>2_Rezim_MK1_4_NOT: 1 | duo 1 · 0 · 0 · 1<br>mono – · – · – · – | high | X, D |
| `flags_regulation` | `2_Regul_MK1_po_1(_NOT)`, `2_Regul_MK1_po_4(_NOT)`, `2_Regul_MK1_HL_po_1(_NOT)`, `2_Regul_MK1_HL_po_4(_NOT)` | helper | Regulation mode == 1 / == 4 for slot 1 heating and cooling. Ours po_4 = 1. | bool | ×1 | — | no | 0..1 | — | 8/8 S_OK; values 0, 1 | duo 8/8 · mono 0/8 present | high | X, D |
| `flags_room_sensor` | `2_Regul_Sobni1_1(_NOT)`, `2_Regul_Sobni1_3(_NOT)` | helper | Slot-1 room sensor type == 1 (DPWT) / == 3 (thermostat). Ours 0 (type 2). | bool | ×1 | — | no | 0..1 | — | 2_Regul_Sobni1_1: 0<br>2_Regul_Sobni1_1_NOT: 1<br>2_Regul_Sobni1_3: 0<br>2_Regul_Sobni1_3_NOT: 1 | duo 0 · 1 · 0 · 1<br>mono – · – · – · – | high | X, D |
| `flags_pgdt_mk1` | `2_PogojPGDT_MK1_OGR(_NOT)`, `2_PogojPGDT_MK1_HL(_NOT)`, `2_PogojPGDT_MK1_reg_po_RF(_NOT)`, `2_PogojPGDT_MK1_reg_po_RF_HL(_NOT)` | helper | Slot 1 heating/cooling role and 'regulates on room temperature' (ours reg_po_RF 0, duo 1 with mode 3). The HL pair is 0/0 on ours and duo. | bool | ×1 | — | no | 0..1 | — | 8/8 S_OK; values 0, 1 | duo 8/8 · mono 0/8 present | medium | X, D |
| `flags_quiet` | `2_Tisje_delov_1(_NOT)`, `2_Tisje_delov_4(_NOT)` | helper | `2_Tisje_delov` == 1 / == 4. | bool | ×1 | — | no | 0..1 | — | 2_Tisje_delov_1: 0<br>2_Tisje_delov_4: 0<br>2_Tisje_delov_1_NOT: 1<br>2_Tisje_delov_4_NOT: 1 | duo 0 · 0 · 1 · 1<br>mono – · – · – · – | high | X, D |
| `flags_heater` | `2_Vklop_Elektro_Grelci_0(_NOT)`, `_2(_NOT); 2_Izbira_st_grelcev_1(_NOT)`, `_3(_NOT); 2_Vzporedno_Elektro_Grelci_0(_NOT)`, `_3(_NOT); 2_Izbira_DOD_VIRA_1(_NOT)`, `_3(_NOT)` | helper | Heater/additional-source enum flags. | bool | ×1 | — | no | 0..1 | — | 16/16 S_OK; values 0, 1 | duo 16/16 · mono 0/16 present | high | X, D |
| `flags_contact_id2` | `2_Kontakt_ID2_1(_NOT)`, `2_Kontakt_ID2_3(_NOT)` | helper | `2_Kontakt_ID2` == 1 / == 3. | bool | ×1 | — | no | 0..1 | — | 2_Kontakt_ID2_3_NOT: 1<br>2_Kontakt_ID2_3: 0<br>2_Kontakt_ID2_1_NOT: 0<br>2_Kontakt_ID2_1: 1 | duo 1 · 0 · 0 · 1<br>mono – · – · – · – | high | X, D |
| `flags_system_mode` | `2_REZIM_SISTEMA_1(_NOT)`, `2_REZIM_SISTEMA_3(_NOT)` | helper | `2_REZIM_SISTEMA` == 1 / == 3. | bool | ×1 | — | no | 0..1 | — | 2_REZIM_SISTEMA_1: 1<br>2_REZIM_SISTEMA_1_NOT: 0<br>2_REZIM_SISTEMA_3: 0<br>2_REZIM_SISTEMA_3_NOT: 1 | duo 1 · 0 · 0 · 1<br>mono – · – · – · – | high | X, D |
| `flags_legionella` | `2_Legionela_CIKEL_1(_NOT)`, `2_Legionela_CIKEL_4(_NOT)`, `2_Legionela_PONED(_NOT)`, `2_Legionela_NEDELJA(_NOT)` | helper | Legionella cycle == 1 / == 4, day == Monday / Sunday. | bool | ×1 | — | no | 0..1 | — | 8/8 S_OK; values 0, 1 | duo 8/8 · mono 0/8 present | high | X, D |
| `flags_quick_mode` | `2_HITRI_Rezim_Izklop`, `2_HITRI_Rezim_Ogrevanje`, `2_HITRI_Rezim_Hlajenje` | helper | One-hot of `2_HITRI_Rezim` (duo: Ogrevanje = 1 with value 2). | bool | ×1 | — | no | 0..1 | — | 2_HITRI_Rezim_Izklop: 0<br>2_HITRI_Rezim_Ogrevanje: 0<br>2_HITRI_Rezim_Hlajenje: 0 | duo 0 · 1 · 0<br>mono 0 · 0 · 0 | high | X, D |
| `manual_heat_cool` | `2_Ro_no_Avtomatsko` | helper | 'Ročno/Avtomatsko' (manual/automatic); 0 ours/duo. Probably the manual heat/cool state for circuit mode 5. Newer fw: `2_Ro_no_Avtomatsko1..3` per circuit. | bool? | ×1 | — | no | ? | — | 0 | duo 0 · mono – | low | N, X, D |

### 2.19 Legacy `*_DK1` / `*_DK2` duplicates (do not use)

On ours and duo these hold factory-like values identical on both pumps; the app uses the `*_MK1`/`*_MK2` tags for slots 1–2 even on DK circuits, and the newest firmware (mono) no longer has them. Treat as dead.

| key | tag(s) | element | semantics | type | scale | unit | writable | range (raw → decoded) | enum map | ours (2026-10-31) | duo · mono | conf. | src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `legacy_dk_mode` | 1: `2_Rezim_DK1`<br>2: `2_Rezim_DK2`<br>3: — | circuit (legacy) | Legacy mode. | enum | ×1 | — | never | — | presumably as `2_Rezim_MK1/MK2` | 1: 1<br>2: 1<br>3: — | duo 1 · 1 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_max_flow` | 1: `2_Max_VF_DK1`<br>2: `2_Max_VF_DK2`<br>3: — | circuit (legacy) | Legacy max flow. | float | ×10 | °C | never | — | — | 1: 400 (40.0)<br>2: 400 (40.0)<br>3: — | duo 400 · 400 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_min_flow` | 1: `2_Min_VF_DK1`<br>2: `2_Min_VF_DK2`<br>3: — | circuit (legacy) | Legacy min flow. | float | ×10 | °C | never | — | — | 1: 120 (12.0)<br>2: 120 (12.0)<br>3: — | duo 120 · 120 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_min_flow_cooling` | 1: `2_Min_VF_DK1_HL`<br>2: `2_Min_VF_DK2_HL`<br>3: — | circuit (legacy) | Legacy min cooling flow. | float | ×10 | °C | never | — | — | 1: 180 (18.0)<br>2: 180 (18.0)<br>3: — | duo 180 · 180 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_regulation` | 1: `2_Reg_po_RF_AF_KONST_DK1`<br>2: `2_Reg_po_RF_AF_KONST_DK2`<br>3: — | circuit (legacy) | Legacy heating regulation. | enum | ×1 | — | never | — | presumably as `2_Reg_po_RF_AF_KONST_MK*` | 1: 3<br>2: 3<br>3: — | duo 3 · 3 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_regulation_cooling` | 1: `2_Reg_po_RF_AF_KONST_DK1_HL`<br>2: `2_Reg_po_RF_AF_KONST_DK2_HL`<br>3: — | circuit (legacy) | Legacy cooling regulation. | enum | ×1 | — | never | — | presumably as the `_HL` slot tags | 1: 3<br>2: 3<br>3: — | duo 3 · 3 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_installation` | 1: `2_Talno_Radiatorsko_DK1`<br>2: `2_Talno_Radiatorsko_DK2`<br>3: — | circuit (legacy) | Legacy installation type. | enum | ×1 | — | never | — | presumably 0 radiator, 1 floor | 1: 1<br>2: 1<br>3: — | duo 1 · 1 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_shift` | 1: `2_Zamik_krivulje_DK1`<br>2: `2_Zamik_krivulje_DK2`<br>3: — | circuit (legacy) | Legacy curve shift. | float | ×10 | K | never | — | — | 1: 0 (0.0)<br>2: 0 (0.0)<br>3: — | duo 0 · 0 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_slope` | 1: `2_Nagib_krivulje_DK1`<br>2: `2_Nagib_krivulje_DK2`<br>3: — | circuit (legacy) | Legacy curve slope. | float | ×10 | K | never | — | — | 1: 0 (0.0)<br>2: 0 (0.0)<br>3: — | duo 0 · 0 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_cool20` | 1: `2_Tocka_1_20st_HL_DK1`<br>2: `2_Tocka_1_20st_HL_DK2`<br>3: — | circuit (legacy) | Legacy cooling point +20. | float | ×10 | °C | never | — | — | 1: 250 (25.0)<br>2: 250 (25.0)<br>3: — | duo 250 · 250 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_cool30` | 1: `2_Tocka_2_30st_HL_DK1`<br>2: `2_Tocka_2_30st_HL_DK2`<br>3: — | circuit (legacy) | Legacy cooling point +30. | float | ×10 | °C | never | — | — | 1: 150 (15.0)<br>2: 150 (15.0)<br>3: — | duo 150 · 150 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_heat` | 1: `2_Aktiv_avtom_preklop_zima_DK1`<br>2: `2_Aktiv_avtom_preklop_zima_DK2`<br>3: — | circuit (legacy) | Legacy auto heating switch. | bool | ×1 | — | never | — | — | 1: 0<br>2: 0<br>3: — | duo 0 · 0 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_heat_temp` | 1: `2_Temp_za_preklop_zima_DK1`<br>2: `2_Temp_za_preklop_zima_DK2`<br>3: — | circuit (legacy) | Legacy auto heating switch temperature. | float | ×10 | °C | never | — | — | 1: 160 (16.0)<br>2: 160 (16.0)<br>3: — | duo 160 · 160 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_heat_delay` | 1: `2_Cas_ur_preklop_zima_DK1`<br>2: `2_Cas_ur_preklop_zima_DK2`<br>3: — | circuit (legacy) | Legacy auto heating switch delay. | int | ×1 | h | never | — | — | 1: 24<br>2: 24<br>3: — | duo 24 · 24 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_cool` | 1: `2_Aktiv_avtom_preklop_poletje_DK1`<br>2: `2_Aktiv_avtom_preklop_poletje_DK2`<br>3: — | circuit (legacy) | Legacy auto cooling switch. | bool | ×1 | — | never | — | — | 1: 0<br>2: 0<br>3: — | duo 0 · 0 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_cool_temp` | 1: `2_Temp_preklop_poletje_DK1_HL`<br>2: `2_Temp_preklop_poletje_DK2_HL`<br>3: — | circuit (legacy) | Legacy auto cooling switch temperature. | float | ×10 | °C | never | — | — | 1: 210 (21.0)<br>2: 210 (21.0)<br>3: — | duo 210 · 210 · —<br>mono – · – · — | medium | X, D |
| `legacy_dk_auto_cool_delay` | 1: `2_Cas_ur_preklop_poletje_DK1_HL`<br>2: `2_Cas_ur_preklop_poletje_DK2_HL`<br>3: — | circuit (legacy) | Legacy auto cooling switch delay. | int | ×1 | h | never | — | — | 1: 24<br>2: 24<br>3: — | duo 24 · 24 · —<br>mono – · – · — | medium | X, D |

## 3. Topology signal cross-tab (R6 raw material)

Known hardware: ours = DK1 floor (on, no room sensor) + MK2 radiator (off, no room sensor) + DHW + solar, no buffer;
duo = DK1 + DHW, room sensor on circuit 1; mono = DK1 + DK2 + DHW, room sensors on both circuits; the mono dump also
shows a buffer (`2_Shema_ZALOG` = 1, `2_Temp_Zalog` = 33.6 °C).

### 3.1 Schema number vs element flags

| pump | `2_Shema` | name | expected flags | actual `2_Shema_*` (MK1 DK1 MK2 DK2 DK3 SOLAR SV) | `Shema_OK1/OK2` |
|---|---|---|---|---|---|
| ours | 23 | DK1+MK2+SV+SOLAR | MK1=0 DK1=1 MK2=1 DK2=0 DK3=0 SOLAR=1 SV=1 | 0 1 1 0 0 1 1 | 1/1 |
| duo | 3 | DK1+SV | MK1=0 DK1=1 MK2=0 DK2=0 DK3=0 SOLAR=0 SV=1 | 0 1 0 0 0 0 1 | 1/0 |
| mono | 7 | DK1+DK2+SV | MK1=0 DK1=1 MK2=0 DK2=1 DK3=0 SOLAR=0 SV=1 | 0 – 0 – 0 0 1 | 1/1 |

### 3.2 Every `2_Shema*`, `2_PogojPGDT_*` and `2_Tipalo_*` tag

| tag | ours (#23) | duo (#3) | mono (#7) | most likely meaning | consistent with hardware? |
|---|---|---|---|---|---|
| `2_Shema` | 23 | 3 | 7 | Schema number (index into `wiring_diagrams`). | yes: 23/3/7 match the known hardware |
| `2_Shema_DK1` | 1 | 1 | – | Schema has DK1. | yes on ours/duo; **tag absent on mono** although mono is DK1 |
| `2_Shema_DK2` | 0 | 0 | – | Schema has DK2. | ours/duo yes; **absent on mono** although mono is DK2 |
| `2_Shema_DK3` | 0 | 0 | 0 | Schema has DK3. | yes (0/0/0) |
| `2_Shema_MK1` | 0 | 0 | 0 | Schema has MK1. | yes (0/0/0) |
| `2_Shema_MK2` | 1 | 0 | 0 | Schema has MK2. | yes (1/0/0) |
| `2_Shema_SOLAR` | 1 | 0 | 0 | Schema has solar. | yes (1/0/0) |
| `2_Shema_SV` | 1 | 1 | 1 | Schema has DHW. | yes (1/1/1) |
| `2_Shema_ZALOG` | 0 | 0 | 1 | Installer flag 'schema with buffer' (separate from the schema number). | yes: mono has a buffer (TZ reads 33.6 °C) although schema 7's name has none |
| `2_PogojPGDT_Shema_OK1` | 1 | 1 | 1 | Slot 1 present. | yes (1/1/1) |
| `2_PogojPGDT_Shema_OK2` | 1 | 0 | 1 | Slot 2 present (also when switched off). | yes (1/0/1); ours MK2 is off but 1 |
| `2_PogojPGDT_Shema_in_Servisni_OK1` | 0 | 0 | 0 | Unknown ('servisni' = service); 0 everywhere. | uninformative |
| `2_PogojPGDT_Shema_in_Servisni_OK2` | 0 | 0 | 0 | Unknown; 0 everywhere. | uninformative |
| `2_PogojPGDT_Shema_in_Servisni_OK3` | 0 | 0 | 0 | Unknown; 0 everywhere. | uninformative |
| `2_PogojPGDT_Shema_in_Servisni_SOLA` | E_UNKNOWNTAG | 0 | – | Unknown (solar variant); E_UNKNOWNTAG on ours. | — |
| `2_PogojPGDT_Shema_in_Servisni_SV` | 0 | 0 | 0 | Unknown; 0 everywhere. | uninformative |
| `2_PogojPGDT_Shema_in_Upor_OK1` | 1 | 1 | 1 | Unknown; equals slot-present on all pumps ('upor' = resistor?). | consistent |
| `2_PogojPGDT_Shema_in_Upor_OK2` | 1 | 0 | 1 | Unknown; equals slot-present. | consistent (1/0/1) |
| `2_PogojPGDT_Shema_in_Upor_OK3` | 0 | 0 | 0 | Unknown; equals slot-present. | consistent (0/0/0) |
| `2_PogojPGDT_Shema_in_Upor_SV` | 1 | 1 | 1 | Unknown; equals DHW-present. | consistent |
| `2_PogojPGDT_Shema_in_tipalo_OK1` | 0 | 1 | 1 | Slot 1 present and room sensor configured; drives app widget `data-active`. | yes: ours no sensor 0, duo 20.7 °C 1, mono 21.9 °C 1 |
| `2_PogojPGDT_Shema_in_tipalo_OK2` | 0 | 0 | 1 | Slot 2 present and room sensor configured. | yes: ours 0 (-9999), duo 0 (no slot 2), mono 1 (22.9 °C) |
| `2_PogojPGDT_Shema_in_tipalo_OK3` | 0 | 0 | 0 | Slot 3 present and room sensor configured. | yes (no slot 3 anywhere) |
| `2_PogojPGDT_Shema_in_tipalo_SV` | 1 | 1 | 1 | DHW present and sensor configured. | yes (1/1/1) |
| `2_PogojPGDT_Shema_in_tipalo_ZALOG` | 0 | 0 | – | Buffer present and sensor configured. | ours/duo 0 consistent; **absent on mono**, the only pump with a buffer |
| `2_Tipalo_AF` | 1 | 1 | 1 | Outdoor sensor enabled (on the app home page). | yes (1/1/1) |
| `2_Tipalo_B11` | 0 | 0 | – | Input B11 flag (B11 = DHW bottom on the Duo drawing, B). | 0 on ours/duo although BF2 reads |
| `2_Tipalo_B12` | 0 | 0 | – | Input B12 flag (unused in the Duo drawing). | 0/0/absent |
| `2_Tipalo_BF1` | 1 | 1 | 1 | DHW top sensor enabled. | yes (1/1/1) |
| `2_Tipalo_BF2` | 1 | 1 | 0 | DHW bottom sensor enabled. | yes: mono 0 and `2_Poti4` = -9999 |
| `2_Tipalo_KF` | 1 | 1 | – | Collector sensor enabled. | **duo 1 but no solar and `2_Poti5` = -9999**; absent on mono |
| `2_Tipalo_RF` | 0 | 1 | 1 | Room sensor 1 enabled. | yes (0/1/1) |
| `2_Tipalo_RF2` | 0 | 0 | 1 | Room sensor 2 enabled. | yes (0/0/1) |
| `2_Tipalo_RF3` | 0 | 0 | 0 | Room sensor 3 enabled. | yes (0/0/0) |
| `2_Tipalo_VF1` | 1 | 1 | 1 | Flow sensor 1 (TM1) enabled. | yes (1/1/1; TM1 also guards DK1) |
| `2_Tipalo_VF2` | 0 | 1 | 0 | Flow sensor 2 (TM2) enabled. | matches the reading, **not the topology**: duo 1 with no slot 2 (reads 21.0 °C); ours 0 with MK2 present (-9999) |
| `2_Tipalo_Zalog` | 0 | 0 | 1 | Buffer sensor enabled. | yes (0/0/1) |
| `2_PogojPGDT_1` | 1 | 1 | – | Unknown condition flag. | — |
| `2_PogojPGDT_MK1_HL` | 0 | 0 | – | Derived: slot-1 mode is cooling. | ours 0 |
| `2_PogojPGDT_MK1_HL_NOT` | 1 | 1 | – | Negation. | — |
| `2_PogojPGDT_MK1_OGR` | 1 | 1 | – | Derived: slot-1 mode is heating. | ours mode 1 → 1 |
| `2_PogojPGDT_MK1_OGR_NOT` | 0 | 0 | – | Negation. | — |
| `2_PogojPGDT_MK1_reg_po_RF` | 0 | 1 | – | Derived: slot-1 heating regulation uses the room sensor (mode 1/3). | ours mode 4 → 0; duo mode 3 → 1 |
| `2_PogojPGDT_MK1_reg_po_RF_HL` | 0 | 0 | – | Derived, cooling variant (probably also gated by cooling). | 0 on duo despite cooling mode 3 |
| `2_PogojPGDT_MK1_reg_po_RF_HL_NOT` | 0 | 0 | – | Negation; 0 too, so gated. | — |
| `2_PogojPGDT_MK1_reg_po_RF_NOT` | 1 | 0 | – | Negation. | — |
| `2_PogojPGDT_N_OSN_OFF_OK1` | E_UNKNOWNTAG | 1 | 0 | Complement. | duo 1 / mono 0 |
| `2_PogojPGDT_N_OSN_OFF_OK2` | E_UNKNOWNTAG | 0 | 1 | Complement. | duo 0 (absent) / mono 1 (satisfied) |
| `2_PogojPGDT_N_OSN_OFF_OK3` | E_UNKNOWNTAG | 0 | 0 | Complement. | 0/0 |
| `2_PogojPGDT_N_OSN_OFF_SV` | E_UNKNOWNTAG | 1 | 0 | Complement. | duo 1 / mono 0 |
| `2_PogojPGDT_N_OSN_ON_OK1` | E_UNKNOWNTAG | 0 | 1 | Element demand indicator, see §7. | duo 0 / mono 1: matches demand |
| `2_PogojPGDT_N_OSN_ON_OK2` | E_UNKNOWNTAG | 0 | 0 | Demand, slot 2. | duo 0 (absent slot) / mono 0 |
| `2_PogojPGDT_N_OSN_ON_OK3` | E_UNKNOWNTAG | 0 | 0 | Demand, slot 3. | 0/0 (no slot 3) |
| `2_PogojPGDT_N_OSN_ON_SV` | E_UNKNOWNTAG | 0 | 1 | Demand, DHW. | duo 0 (43.0 ≥ 44.5−4.0) / mono 1 (36.5 < 44.0−3.5) |

### 3.3 Conclusions for topology detection

- **Most robust:** `2_Shema` (exists on all firmware) decoded with the 45-entry `wiring_diagrams` list gives the
  circuits per slot (MK/DK), DHW and solar. `2_Shema_ZALOG` adds the buffer. Cross-check with
  `2_PogojPGDT_Shema_OK1/OK2` (no slot-3 variant exists).
- **Do not rely on** `2_Shema_DK1/DK2` (missing on mono), `2_Tipalo_KF`/`2_Tipalo_VF2` (contradict the hardware on
  duo/ours), or the room-sensor type `2_Sobni_*` (2 = NTC on all slots of ours, without any sensor).
- **Room sensor present:** `2_PogojPGDT_Shema_in_tipalo_OKn` = 1, and/or room temperature ≠ -9999; both agree on all
  three pumps. `2_Tipalo_RF/RF2/RF3` agree too.
- **Unknown:** `…_in_Upor_*` (equals element-present everywhere), `…_in_Servisni_*` (0 everywhere), `2_PogojPGDT_1`,
  `2_Tipalo_B11/B12`.
- **Contradictions to keep in mind:** duo `2_Tipalo_KF` = 1 without solar; duo `2_Tipalo_VF2` = 1 with no slot 2
  (input reads 21.0 °C, maybe a repurposed sensor, cf. #30); ours MK2 present with `2_Tipalo_VF2` = 0.

## 4. Info-page matching

SI snapshot taken at 17:16 on Fri 2026-10-30 (`2_CURRENT_*` in J), EN snapshot about 3 h later (~20:09, PLAN §5.4).
Our dump is from Sat 2026-10-31 20:24. "R n" = position n in the old readme's INFO `readTags` request, whose order
is exactly the info-page order for lines 1–23 (positions 15 and 23 are the circuit-title tags `MK1_IME`,
`MK1_IME(2)`).

| # | group | SI label | EN label | SI 10-30 17:16 | EN ~20:09 | proposed tag | our dump 10-31 20:24 | conf. | evidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | — | Zunanja temperatura | Outdoor temperature | 10.6°C | 8.7°C | `2_Temp_Zunanja` | 74 (7.4) | high | R order 1, M; home widget showed the same 10.6 at the SI moment |
| 2 | — | Temp.sanit.vode zgoraj | Temp. DHW top | 40.0°C | 42.4°C | `2_Poti3` | 391 (39.1) | high | R 2, M; home DHW widget showed the same 40.0 |
| 3 | — | Temp.sanit.vode spodaj | Temp. DHW bottom | 37.2°C | 39.9°C | `2_Poti4` | 241 (24.1) | high | R 3, M |
| 4 | — | Temperatura zalogovnika | Buffer temperature | -999.9°C | -999.9°C | `2_Temp_Zalog` | -9999 (n/c) | high | R 4, M; -9999 ↔ -999.9 both times |
| 5 | — | Temp.sončnih kolektorjev | Solar temperature | 13.7°C | 7.8°C | `2_Poti5` | 75 (7.5) | high | R 5, M; dump 7.5 vs EN 7.8 |
| 6 | — | Stanje obt.črp.kolektorjev | Solar pump | Izklop | OFF | `2_Vklop_C3` | 0 | high | R 6, M (shared P3 output) |
| 7 | — | Eksterni dodatni vir | Additional source | Izklop | OFF | `2_Vklop_ele_grelca_1` | 0 | high (tag) / medium (label) | R 7, M ('Dodatni vir'); label text is fixed |
| 8 | TOPLOTNA ČRPALKA | Temperatura toplotne črpalke | HP temperature | 24.5°C | 24.4°C | `2_Poti1` | 235 (23.5) | high | R 8, M; home widget 24.8 vs info 24.5 |
| 9 | TOPLOTNA ČRPALKA | Želena temp.toplotne črpalke | Desired HP temperature | 28.0°C | 9.0°C | `2_Izrac_temp_TC` | 90 (9.0) | high | R 9, M; EN 9.0 = dump 90 |
| 10 | TOPLOTNA ČRPALKA | Stanje obt.črpalke C0 | Pump P0 | Vklop | OFF | `2_Vklop_C0` | 0 | high | R 10, M |
| 11 | TOPLOTNA ČRPALKA | Stanje pretočnega stikala | Flow switch | Pretok O.K. | No flow | `2_Pogoj_maska_pret_stik` | 0 | high | R 11, M; enum from P0 state at both moments |
| 12 | TOPLOTNA ČRPALKA | Stanje zunanje enote | Outdoor unit status | Izklop | OFF | `2_Rezim_delov_TC` | 0 | high | R 12, M |
| 13 | TOPLOTNA ČRPALKA | Delovna moč zunanje enote | Outdoor operation power | 0% | 0% | `2_PRIKAZ_Reg_temp_vode` | 0 (0.0) | high (tag) / low (unit) | R 13, M; see §8 |
| 14 | TOPLOTNA ČRPALKA | Smer prekl.ventila | Position of 3-way valve | Prostori | DHW heating | `2_Preklop_PV1` | 1 | high | R 14, M |
| 15 | circuit 1 (`MK1_IME` = TALNO) | Prostorska temperatura | Room temperature | -999.9°C | -999.9°C | `2_Temp_Prostora` | -9999 (n/c) | high | R 16 (after title `MK1_IME`), M, home widget data-tag |
| 16 | circuit 1 (`MK1_IME` = TALNO) | Želena prostorska temp | Desired room temperature | 22.5°C | 22.0°C | `2_Zahtevana_RF_MK_1` | 220 (22.0) | high | R 17, M; SI 22.5 = `2_Temp_prostor_dnevna`, EN 22.0 = `_nocna` = dump |
| 17 | circuit 1 (`MK1_IME` = TALNO) | Temperatura vtoka | Outlet temperature | 25.0°C | 23.0°C | `2_Poti2` | 228 (22.8) | high | R 18, M; dump 22.8 |
| 18 | circuit 1 (`MK1_IME` = TALNO) | Želena temperatura vtoka | Desired outlet temperature | 0°C | 0°C | `2_Temp_zelena_MK_1` | 0 (0.0) | high | R 19, M; 0 at all three moments |
| 19 | circuit 1 (`MK1_IME` = TALNO) | Stanje mešalnega ventila | Mixing valve status | Izklop | OFF | `2_Delovanje_MP1` | 0 | high | R 20, M |
| 20 | circuit 1 (`MK1_IME` = TALNO) | Odprtost mešalnega ventila | Mixing valve position | 0% | 0% | `2_Odstotki_odprtosti_MP1` | 0 (0.0) | high | R 21, M |
| 21 | circuit 1 (`MK1_IME` = TALNO) | Stanje obtočne črpalke C1 | Pump P1 | Vklop | OFF | `2_Vklop_C1` | 0 | high | R 22, M |
| 22 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Prostorska temperatura | Room temperature | -999.9°C | -999.9°C | `2_Temp_RF2` | -9999 (n/c) | high | R 24 (after title `MK1_IME(2)`), M, home widget |
| 23 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Želena prostorska temp | Desired room temperature | 30.0°C | 26.1°C | `2_Zahtevana_RF_MK_2` | 261 (26.1) | high | R 25, M; SI 30.0 = `_dnevna_OK2`, EN 26.1 = `_nocna_OK2` = dump |
| 24 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Temperatura vtoka | Outlet temperature | -999.9°C | -999.9°C | `2_Temp_VF2` | -9999 (n/c) | medium-high | M, C; R stops before it; -9999 at all moments |
| 25 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Želena temperatura vtoka | Desired outlet temperature | 12.0°C | 12.0°C | `2_Temp_zelena_MK_2` | 120 (12.0) | high | M, C; 12.0 = dump 120 at all moments |
| 26 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Stanje mešalnega ventila | Mixing valve status | Izklop | OFF | `2_Delovanje_MP2` | 0 | medium-high | M, C |
| 27 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Odprtost mešalnega ventila | Mixing valve position | 9.0% | 9.0% | `2_Odstotki_odprtosti_MP2` | 90 (9.0) | high | M, C; 9.0 % = dump 90 at all moments |
| 28 | circuit 2 (`MK1_IME(2)` = RADIATORJI) | Stanje obtočne črpalke C2 | Pump P2 | Izklop | OFF | `2_Vklop_C2` | 0 | medium-high | M, C |
| 29 | circuit 3 (`MK1_IME(3)` = OGREVALNI KROG 3) | Prostorska temperatura | Room temperature | -999.9°C | -999.9°C | `2_Temp_RF3` | -9999 (n/c) | high | M; home widget data-tag for circuit 3 |
| 30 | circuit 3 (`MK1_IME(3)` = OGREVALNI KROG 3) | Želena prostorska temp | Desired room temperature | 22.0°C | 22.0°C | `2_Zahtevana_RF_DK_3` | 220 (22.0) | medium-high | M; 22.0 = dump 220 (24 h timer → `_dnevna_OK3` 220) |
| 31 | circuit 3 (`MK1_IME(3)` = OGREVALNI KROG 3) | Stanje obtočne črpalke C3 | Pump P3 | Izklop | OFF | `2_Vklop_C3` | 0 | medium | M ('Stanje obtočne črpalke C3'); same tag as the solar pump line |

Lines after the 31 in the JSON (from the info page HTML in the SI HAR, group `* * *`):

| label | shown value | proposed tag (our value) | conf. |
|---|---|---|---|
| Zunanja enota | Mitsubishi | `2_Izbira_Mitsubishi_Fujitsu` (1) / `2_ZE_Mitsubishi` (1) | medium |
| Vgrajen regulator | UPC Kartica (µPC) | `2_Izbira_mPC_pCO3` (1) / `2_REG_mPC` (1) | medium |
| FIRST START MADE BY | installer name (redacted in the HAR) | `2_Zagon_opravlja_oseba` (index; the name is not a tag value) | low |

Consistency checks across the three moments:

- Circuit 1 target room temperature 22.5 → 22.0 and circuit 2 30.0 → 26.1 are the high → low setpoints, exactly as
  programmes 2 and 5 predict (§5.3).
- At 17:16 the HP target 28.0 equals `2_Max_VF_MK1` (280) with P0, P1 on and flow OK; at ~20:09 the target is 9.0 with
  P0, P1 off and "No flow", consistent with `2_Ponoci_min_temp_IZKLOP_MK1` = 0 (off in the low regime). Our dump at
  20:24 shows the same idle state (target 90, P0 = P1 = 0, flow switch 0).
- Circuit 1 "desired flow temperature" is 0 at all moments, although the circuit was heating at 17:16: on a DK
  circuit `2_Temp_zelena_MK_1` is not used (no mixing valve); the HP target carries the flow setpoint.

## 5. Timer decoding (R7)

### 5.1 Encoding

- 5 programmes × 3 ranges, global (shared by all consumers). Each range has 11 plain-integer tags:
  `2_TIMER_<p>_Ura_ON_<r>` (start hour 0–23), `2_TIMER_<p>_Minute_ON_<r>` (start minute),
  `2_TIMER_<p>_Ura_OFF_<r>` (end hour), `2_TIMER_<p>_Minute_OFF_<r>` (end minute), and
  `2_TIMER_<p>_<Ponedeljek|Torek|Sreda|Cetrtek|Petek|Sobota|Nedelja>_<r>` (0/1: range active on Mon…Sun).
- 165 tags, all S_OK on ours and present in the duo and mono dumps. No ×10, no bit packing.
- A range is active on a day only if that day's flag is 1. "00:00–00:00" with no days is the unused state.
- The display's editor aliases (`CASOVNIK<p>URAVKLOP(<r>)`, `CASOVNIK<p><weekday>(<r>)`, …) are E_UNKNOWNTAG; the
  menu map's weekday bindings for these pages are garbled (each weekday label bound to two tags).
- The duo firmware additionally has a per-weekday scheme (`2_On_<Pon…Ned>_Ura[_n]`, `2_Off_…`, `_SV_2/_SV_3`,
  `_TISJE`; 204 tags) that is E_UNKNOWNTAG on ours and absent from the mono dump. Ignore it.

### 5.2 Row-by-row evidence (our dump vs the app's ranges)

| prog. | range | `Ura_ON` | `Minute_ON` | `Ura_OFF` | `Minute_OFF` | weekday flags Po To Sr Če Pe So Ne | decoded | JSON ground truth | match |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 6 | 0 | 1 1 1 1 1 0 0 | 00:00–06:00 MON TUE WED THU FRI | 00:00–06:00 MON TUE WED THU FRI | yes |
| 1 | 2 | 20 | 2 | 23 | 0 | 1 1 1 1 1 0 0 | 20:02–23:00 MON TUE WED THU FRI | 20:02–23:00 MON TUE WED THU FRI | yes |
| 1 | 3 | 7 | 0 | 23 | 0 | 0 0 0 0 0 1 1 | 07:00–23:00 SAT SUN | 07:00–23:00 SAT SUN | yes |
| 2 | 1 | 23 | 0 | 6 | 0 | 0 0 0 0 0 0 0 | 23:00–06:00 (no days) | 23:00–06:00 (no days) | yes |
| 2 | 2 | 8 | 0 | 18 | 0 | 1 1 1 1 1 1 1 | 08:00–18:00 MON TUE WED THU FRI SAT SUN | 08:00–18:00 MON TUE WED THU FRI SAT SUN | yes |
| 2 | 3 | 0 | 0 | 0 | 0 | 0 0 0 0 0 0 0 | 00:00–00:00 (no days) | 00:00–00:00 (no days) | yes |
| 3 | 1 | 22 | 5 | 5 | 55 | 0 0 0 0 0 0 0 | 22:05–05:55 (no days) | 22:05–05:55 (no days) | yes |
| 3 | 2 | 20 | 0 | 23 | 0 | 1 1 1 1 1 1 1 | 20:00–23:00 MON TUE WED THU FRI SAT SUN | 20:00–23:00 MON TUE WED THU FRI SAT SUN | yes |
| 3 | 3 | 0 | 0 | 0 | 0 | 0 0 0 0 0 0 0 | 00:00–00:00 (no days) | 00:00–00:00 (no days) | yes |
| 4 | 1 | 11 | 0 | 23 | 0 | 1 1 1 1 1 1 1 | 11:00–23:00 MON TUE WED THU FRI SAT SUN | 11:00–23:00 MON TUE WED THU FRI SAT SUN | yes |
| 4 | 2 | 16 | 0 | 6 | 0 | 0 0 0 0 0 0 0 | 16:00–06:00 (no days) | 16:00–06:00 (no days) | yes |
| 4 | 3 | 0 | 0 | 0 | 0 | 0 0 0 0 0 0 0 | 00:00–00:00 (no days) | 00:00–00:00 (no days) | yes |
| 5 | 1 | 18 | 5 | 21 | 30 | 0 0 0 0 0 0 0 | 18:05–21:30 (no days) | 18:05–21:30 (no days) | yes |
| 5 | 2 | 16 | 0 | 18 | 0 | 1 1 1 1 1 1 1 | 16:00–18:00 MON TUE WED THU FRI SAT SUN | 16:00–18:00 MON TUE WED THU FRI SAT SUN | yes |
| 5 | 3 | 0 | 0 | 0 | 0 | 0 0 0 0 0 0 0 | 00:00–00:00 (no days) | 00:00–00:00 (no days) | yes |

### 5.3 Programme selection and behaviour check

| consumer | selection tag | ours | duo | mono |
|---|---|---|---|---|
| circuit slot 1 | `2_Izbira_TIMERJA_MK1` | 2 | 0 | 0 |
| circuit slot 2 | `2_Izbira_TIMERJA_MK2` | 5 | 0 | 0 |
| circuit slot 3 | `2_Izbira_TIMERJA_MK3` | 0 | 0 | 0 |
| DHW | `2_Izbira_TIMERJA_SV` | 4 | 0 | 0 |
| buffer | `2_Izbira_TIMERJA_ZALOG` | 0 | 0 | 0 |
| quiet mode | `2_Izbira_TIMERJA_TISJE` | 0 | 0 | 2 |

Values: 0 = 24 h (always the high regime), 1–5 = programme. On ours, `2_Timer_MK1_1…5/_24_ur` is the one-hot copy
of the slot-1 selection (`_2` = 1).

| moment | circuit 1 (programme 2: 08:00–18:00 daily) | circuit 2 (programme 5: 16:00–18:00 daily; 18:05–21:30 no days) | circuit 3 (24 h) |
|---|---|---|---|
| Fri 17:16 (app SI) | in range → high 22.5 = `2_Temp_prostor_dnevna` ✓ | in range → high 30.0 = `_dnevna_OK2` ✓ | 22.0 = `_dnevna_OK3` ✓ |
| Fri ~20:09 (app EN) | out → low 22.0 = `_nocna` ✓ | 20:09 lies in 18:05–21:30, but that range has no days → low 26.1 = `_nocna_OK2` ✓ | 22.0 ✓ |
| Sat 20:24 (our dump) | out → `2_Zahtevana_RF_MK_1` = 220 (low) ✓ | out → 261 (low) ✓ | 220 ✓ |

Duo and mono run all circuits on 24 h, and their `2_Zahtevana_RF_MK_1/2` equal their high setpoints, as expected.
DHW (programme 4, 11:00–23:00 daily) was in range at all three moments; ours has no readable "active DHW setpoint"
tag to confirm it (`2_Temp_zelena_SV` is E_UNKNOWNTAG here; on duo it equals the high setpoint).

Open: ranges crossing midnight (23:00–06:00, 22:05–05:55, 16:00–06:00 exist on ours, all without days), overlapping
ranges, and whether the quiet-mode and buffer selections use the same "in range = high/on" semantics.

## 6. Enums (R12)

### 6.1 All enums in J, with observed values

| tag(s) | values (raw = EN / SI) | observed (ours; duo; mono) | values outside the map |
|---|---|---|---|
| `2_Delovanje_MENI` | 0 = Normal operation / Normalno delovanje; 1 = HOLIDAY / POČITNIŠKI REŽIM; 2 = PARTY; 3 = ECO | ours 0; duo 0; mono 0 | none |
| `2_HITRI_Rezim` | 0 = Inactive / Neaktivna funkcija; 1 = OFF / Izklop; 2 = Heating / Ogrevanje; 3 = Cooling / Hlajenje | ours 0; duo 2; mono 0 | none |
| `2_IME_MK1`, `2_IME_MK2`, `2_IME_MK3` | list `settings_titles` (20 entries, §6) | ours 16/15/3; duo 16/2/3; mono 15/16/3 | none |
| `2_Izbira_DOD_VIRA` | 0 = (empty); 1 = ELECTRIC HEATER / ELEKTRIČNI GRELEC; 2 = Additional source / Eksterni dodatni vir; 3 = El. Heater and additional source | ours 1; duo 1; mono – | none |
| `2_Izbira_TIMERJA_MK1`, `2_Izbira_TIMERJA_MK2`, `2_Izbira_TIMERJA_MK3`, `2_Izbira_TIMERJA_SV`, `2_Izbira_TIMERJA_TISJE`, `2_Izbira_TIMERJA_ZALOG` | 0 = 24 hour / 24-urni režim; 1 = According to timer 1 / Po časovnem programu 1; 2 = According to timer 2 / Po časovnem programu 2; 3 = According to timer 3 / Po časovnem programu 3; 4 = According to timer 4 / Po časovnem programu 4; 5 = According to timer 5 / Po časovnem programu 5 | ours 2/5/0/4/0/0; duo 0/0/0/0/0/0; mono 0/0/0/0/2/0 | none |
| `2_Izbira_st_grelcev` | 0 = (empty); 1 = 1 rate (3kW) / 1 stopnja (3kW); 2 = 2 rates (6kW) / 2 stopnji (6kW); 3 = 3 rates (9kW) / 3 stopnje (9kW) | ours 2; duo 3; mono 3 | none |
| `2_Kontakt_ID2` | 0 = (empty); 1 = NO; 2 = NC; 3 = Not activated / Ni aktiviran | ours 1; duo 1; mono 1 | none |
| `2_Kontakt_PF_f_NC_NO`, `2_Kontakt_Preklopni_ventil`, `2_Kontakt_ekst_IZKLOP_TC`, `2_Kontakt_ekst_vklop_2_NC_NO`, `2_Kontakt_ekst_vklop_3_NC_NO`, `2_Kontakt_ekst_vklop_NC_NO`, `2_Kontakt_pret_stik_NC_NO` | 0 = NO; 1 = NC | ours 0/0/0/1/0/1/0; duo 0/0/0/1/0/1/0; mono 0/0/0/1/1/1/0 | none |
| `2_Legionela_Cikel` | 0 = (empty); 1 = Every week / Tedenski; 2 = Every two weeks / Dvotedenski; 3 = Every month / Mesečni; 4 = Every two months / Dvomesečni | ours 1; duo 1; mono 4 | none |
| `2_On_Dan_Legionella` | 0 = (empty); 1 = Monday / Ponedeljek; 2 = Tuesday / Torek; 3 = Wednesday / Sreda; 4 = Thursday / Četrtek; 5 = Friday / Petek; 6 = Saturday / Sobota; 7 = Sunday / Nedelja | ours 7; duo 7; mono 7 | none |
| `2_Ponoci_min_temp_IZKLOP_DK3`, `2_Ponoci_min_temp_IZKLOP_MK1`, `2_Ponoci_min_temp_IZKLOP_MK2` | 0 = OFF / Izklop; 1 = LOWER TEMPERATURE / NIŽJA TEMPERATURA | ours 0/0/0; duo 0/1/0; mono 0/0/0 | none |
| `2_Reg_po_RF_AF_KONST_DK3`, `2_Reg_po_RF_AF_KONST_DK3_HL`, `2_Reg_po_RF_AF_KONST_MK1`, `2_Reg_po_RF_AF_KONST_MK1_HL`, `2_Reg_po_RF_AF_KONST_MK2`, `2_Reg_po_RF_AF_KONST_MK2_HL` | 0 = (empty); 1 = Indoor temperature / Prostorski temperaturi; 2 = Outdoor temperature / Zunanja temperatura; 3 = Indoor+outdoor temp. / Prostorski in zunanji temp.; 4 = Constant temperature / Konstantni temperaturi | ours 3/3/4/4/4/3; duo 3/3/3/3/3/3; mono 4/4/1/1/1/1 | none |
| `2_Rezim_DK3` | 0 = (empty); 1 = Heating / Ogrevanje; 2 = Cooling / Hlajenje; 3 = Automatic sw.HEAT-COOL / Avtomatski preklop ogr.-hl.; 4 = Switch with ID2 input / Preklop preko vhoda ID2 | ours 1; duo 1; mono 1 | none |
| `2_Rezim_MK1`, `2_Rezim_MK2` | 0 = (empty); 1 = Heating / Ogrevanje; 2 = Cooling / Hlajenje; 3 = Automatic sw.HEAT-COOL / Avtomatski preklop ogr.-hl.; 4 = Switch with ID2 input / Preklop preko vhoda ID2; 5 = Manual switching / Ročni preklop | ours 1/1; duo 1/1; mono 1/1 | none |
| `2_SOLAR_Prost_SV` | 0 = DHW heating / Sanitarna voda; 1 = Room heating / Prostorov | ours 0; duo 0; mono 0 | none |
| `2_Shema` | list `wiring_diagrams` (45 entries, §6) | ours 23; duo 3; mono 7 | none |
| `2_Sobni_2_DPWT_PGD1`, `2_Sobni_3_DPWT_PGD1`, `2_Sobni_DPWT_PGD1` | 0 = (empty); 1 = DPWT Carel; 2 = NTC; 3 = ON/OFF thermostat; 4 = Wireless ORCA / Brezžično ORCA; 5 = ThTune | ours 2/2/2; duo 2/2/2; mono 2/2/5 | none |
| `2_Talno_Radiatorsko_DK3`, `2_Talno_Radiatorsko_MK1`, `2_Talno_Radiatorsko_MK2` | 0 = RADIATOR / RADIATORJI; 1 = FLOOR / TALNO | ours 1/1/0; duo 1/1/1; mono 1/0/0 | none |
| `2_Tisje_delov` | 0 = OFF / Izklop; 1 = Manual activation / Ročni vklop; 2 = According to time plan / Po časovnem programu; 3 = According to outdoor temp. / Po zunanji temperaturi; 4 = Acc. to OT and time plan / Po zun.temp. in čas.prog. | ours 3; duo 0; mono 2 | none |
| `2_Vklop_Elektro_Grelci` | 0 = OFF / Izklop; 1 = Automatic / Avtomatsko; 2 = Manual / Ročno | ours 0; duo 1; mono 0 | none |
| `2_Vzporedno_Elektro_Grelci` | 0 = OFF / Izklop; 1 = 1. rates / 1 stopnja; 2 = 2. rates / 2 stopnji; 3 = 3 rates / 3 stopnje | ours 0; duo 0; mono 0 | none |
| `MK1_IME`, `MK1_IME(2)` | list `widget_titles` (20 entries, §6) | ours 16/15; duo 16/2; mono 15/16 | none |
| `MK1_IME(3)` | list `widget_titles2` (18 entries, §6) | ours 3; duo 3; mono 3 | none |

Result: **no observed value is outside the J maps** on any of the three pumps (empty index-0 entries are never
used). Per-slot difference: `2_Rezim_DK3` lacks 5 (manual).

### 6.2 Circuit-name lists (`MK1_IME*`, `2_IME_MK*`)

Observed: ours 16 / 15 / 3 (TALNO / RADIATORJI / OGREVALNI KROG 3), duo 16 / 2 / 3, mono 15 / 16 / 3.
`2_IME_MKn` always equals `MK1_IME…(n)`.

| raw | `widget_titles` / `settings_titles` (slots 1–2; SI = EN) | `widget_titles2` (slot 3 home) | `settings_titles2` (slot 3 settings page) | old config map (slots 1–2) |
|---|---|---|---|---|
| 1 | OGREVALNI KROG 1 = HEATING CIRCLE 1 | OGREVALNI KROG 1 = HEATING CIRCLE 1 | OGREVALNI KROG 1 | Circuit |
| 2 | OGREVALNI KROG 2 = HEATING CIRCLE 2 | OGREVALNI KROG 2 = HEATING CIRCLE 2 | OGREVALNI KROG 2 | Unset |
| 3 | OGREVALNI KROG 3 = HEATING CIRCLE 3 | OGREVALNI KROG 3 = HEATING CIRCLE 3 | OGREVALNI KROG 3 | **missing** |
| 4 | DIREKTNA VEJA 1 = DIRECT CIRCLE 1 | DIREKTNA VEJA 1 = DIRECT CIRCLE 1 | DIREKTNA VEJA 1 | Heating Circuit 2 |
| 5 | DIREKTNA VEJA 2 = DIRECT CIRCLE 2 | DIREKTNA VEJA 2 = DIRECT CIRCLE 2 | DIREKTNA VEJA 2 | Heating Circuit 3 |
| 6 | DIREKTNA VEJA 3 = DIRECT CIRCLE 3 | DIREKTNA VEJA 3 = DIRECT CIRCLE 3 | DIREKTNA VEJA 3 | Direct Circuit 1 |
| 7 | MEŠALNA VEJA 1 = MIXING CIRCLE 1 | KLET = CELLAR | KLET | Direct Circuit 2 |
| 8 | MEŠALNA VEJA 2 = MIXING CIRCLE 2 | PRITLIČJE = GROUND FLOOR | PRITLIČJE | Direct Circuit 3 |
| 9 | KLET = CELLAR | ETAŽA = FLOOR | ETAŽA | Cellar |
| 10 | PRITLIČJE = GROUND FLOOR | 1. NADSTROPJE = 1. FLOOR | 1. NADSTROPJE | Ground Floor |
| 11 | ETAŽA = FLOOR | 2. NADSTROPJE = 2. FLOOR | 2. NADSTROPJE | Floor |
| 12 | 1. NADSTROPJE = 1. FLOOR | MANSARDA = ATTIC | MANSARDA | 1. Floor |
| 13 | 2. NADSTROPJE = 2. FLOOR | RADIATORJI = RADIATOR | RADIATORJI | 2. Floor |
| 14 | MANSARDA = ATTIC | TALNO = FLOOR | TALNO | Attic |
| 15 | RADIATORJI = RADIATOR | KONVEKTORJI = CONVECTOR | KONVEKTORJI | Radiator |
| 16 | TALNO = FLOOR | Ogrevanje = Heating | Ogrevanje | Floor |
| 17 | KONVEKTORJI = CONVECTOR | Hlajenje = Cooling | Hlajenje | Convector |
| 18 | Ogrevanje = Heating | STENSKO = WALL | — | Heating |
| 19 | Hlajenje = Cooling | — | — | Cooling |
| 20 | STENSKO = WALL | — | — | Wall |
| 21 | — | — | — | Heating Circuit 1 |
| 22 | — | — | — | **missing** |
| 23 | — | — | — | Floor |
| 24 | — | — | — | Radiator |
| 28 | — | — | STENSKO | **missing** |

- The old config map (identical for slots 1 and 2) has no entry for 3 or 22, misplaces 4–8 by one, and invents
  21/23/24. Any pump with a circuit named "OGREVALNI KROG 3" (3) crashed it (#38); duo's slot 2 (2) showed "Unset"
  instead of "Heating circuit 2".
- Slot 3 home name uses `widget_titles2`; the slot-3 settings page decodes `2_IME_MK3` with `settings_titles` but
  `MK1_IME(3)` with `settings_titles2`, whose last key is 28 (typo for 18). Proposal: decode slots 1–2 with
  `widget_titles`, slot 3 with `widget_titles2` (+ map 28 → STENSKO), and fall back to "Circuit n" for any unknown
  value instead of failing.

### 6.3 Schema list (`2_Shema`, `wiring_diagrams`)

45 entries, identical to `Citcuit_schemas.md`: 1 MK1+SV, 2 MK1+SV+SOLAR, 3 DK1+SV, 4 DK1+SV+SOLAR, 5 MK1+DK2+SV,
6 MK1+DK2+SV+SOLAR, 7 DK1+DK2+SV, 8 DK1+DK2+SV+SOLAR, 9 MK1+DK2, 10 DK1+DK2, 11 MK1, 12 DK1, 13 DK2, 14 SV ("San.voda"),
15 SV+SOLAR, 16 DK2+SV, 17 DK2+SV+SOLAR, 18 MK2, 19 MK2+SV, 20 MK2+SV+SOLAR, 21 DK1+MK2, 22 DK1+MK2+SV,
23 DK1+MK2+SV+SOLAR, 24 MK1+MK2, 25 MK1+MK2+SV, 26 MK1+MK2+SV+SOLAR, 27 SOLAR, 28 DK3, 29 DK3+SV, 30 DK1+DK3,
31 DK1+DK3+SV, 32 MK1+DK3, 33 MK1+DK3+SV, 34 DK2+DK3, 35 DK2+DK3+SV, 36 MK2+DK3, 37 MK2+DK3+SV, 38 DK1+DK2+DK3,
39 DK1+DK2+DK3+SV, 40 MK1+DK2+DK3, 41 MK1+DK2+DK3+SV, 42 MK1+MK2+DK3, 43 MK1+MK2+DK3+SV, 44 DK1+MK2+DK3,
45 DK1+MK2+DK3+SV. No entry combines DK3 and SOLAR (shared pump output P3).

### 6.4 Enums not in J (inferred; confirm live)

| tag | proposed map | evidence |
|---|---|---|
| `2_Preklop_PV1` | 0 rooms (Prostori), 1 DHW | app SI/EN texts, mono DHW run, C |
| `2_Pogoj_maska_pret_stik` | 0 no flow, 1 flow OK (Pretok O.K.) | app texts vs P0 state at two moments, mono |
| `2_Rezim_delov_TC` | 0 off (Izklop); 1/2/3 heating/cooling/defrost? | app text for 0 only; rest from C |
| `2_Delovanje_MP1/MP2` | 0 off (Izklop); 1 opening?, 2 closing? | app text for 0; C comment |
| `2_Vrsta_alarma` | 0 none; codes unknown | R4 |
| `2_Izbira_mPC_pCO3` | 1 µPC ("UPC Kartica") | info page |
| `2_Izbira_Mitsubishi_Fujitsu` | 1 Mitsubishi; mono has 10 (unknown) | info page |
| `2_REZIM_SISTEMA` | 1 observed; 3 also meaningful (derived flags) | X |
| `2_DOVOD_230V_400V` | 0/1, which is which unknown | N |
| `2_Ponoci_min_temp_IZKLOP_*_HL` | presumably as the heating variant | N |

## 7. Unreadable / empty tags and sensors at -9999

### 7.1 Tags the app showed as `null`

| tag | app value | ours | duo | mono | conclusion |
|---|---|---|---|---|---|
| `2_Signal_PV` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_Signal_EVU` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_Pogoj_ikona_ele_grelca_1` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_Pogoj_ikona_ele_grelca_2` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_Pogoj_ikona_ele_grelca_3` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_OFF_OK1` | null | E_UNKNOWNTAG (both passes) | 1 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_OFF_OK2` | null | E_UNKNOWNTAG (both passes) | 0 | 1 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_OFF_OK3` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_OFF_SV` | null | E_UNKNOWNTAG (both passes) | 1 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_ON_OK1` | null | E_UNKNOWNTAG (both passes) | 0 | 1 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_ON_OK2` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_ON_OK3` | null | E_UNKNOWNTAG (both passes) | 0 | 0 | not in our firmware; the app turns E_UNKNOWNTAG into null |
| `2_PogojPGDT_N_OSN_ON_SV` | null | E_UNKNOWNTAG (both passes) | 0 | 1 | not in our firmware; the app turns E_UNKNOWNTAG into null |

All 13 are **E_UNKNOWNTAG on ours in both dump passes**, not dropped records: the app shows `null` for tags the pump
does not know. On duo/mono they read normally. The `2_PogojPGDT_N_OSN_ON/OFF_*` pairs are complementary per present
element and both 0 for absent elements. In all five testable cases ON = "element below its setpoint / requesting heat"
(duo circuit 1 at 20.7 vs 20.1 → OFF; duo DHW 43.0 ≥ 44.5 − 4.0 → OFF; mono circuit 1 at 21.9 vs 22.0 → ON; mono
circuit 2 at 22.9 vs 22.5 → OFF; mono DHW 36.5 < 44.0 − 3.5 → ON). Not usable on our firmware.

### 7.2 Tags reading -9999

| pump | tags at -9999 | hardware explanation |
|---|---|---|
| ours | `2_Temp_Prostora`, `2_Temp_RF2`, `2_Temp_Zalog`, `2_Temp_RF3`, `2_Temp_VF2` | no room sensors (slots 1–3), no buffer, MK2 has no flow sensor connected |
| duo | `2_Temp_RF2`, `2_Poti5`, `2_Temp_Zalog`, `2_Temp_RF3`, `2_Temp_RF2_VMESNA`, `2_Temp_RF3_VMESNA` | no room sensor 2/3, no collector (no solar), no buffer; the `_VMESNA` mirrors of RF2/RF3 |
| mono | `2_Poti4`, `2_Poti5`, `2_Temp_RF3`, `2_Temp_VF2` | no DHW bottom sensor (`2_Tipalo_BF2` = 0), no collector, no room sensor 3, no TM2 (DK2 is direct) |

No empty values in any dump.

## 8. Discrepancies between sources

| item | one source says | other source says | judgement |
|---|---|---|---|
| `2_Zamik_krivulje_*`, `2_Nagib_krivulje_*` range | C −9.9…9.9 step 0.1 | J −150…150 raw (±15.0) | J |
| `2_Max_moc_TC_pri_OGR/_SV` range | C 10.0–100.0 % | J 400…1000 (40.0–100.0 %) | J; writing below 40 % may be refused or harmful |
| `2_Max_moc_TC_pri_HLAJ` range | C 10.0–100.0 % | J 160…1000 (16.0–100.0 %) | J |
| `2_Zun_temp_za_vklop_Grelec_1..3` range | C −30.0…10.0 | J −300…300 (−30.0…30.0); ours holds 22.0/22.9 | J |
| `2_Temp_vode_sanitarna` range | C 25.0–60.0 | J 80…550 (8.0–55.0) | J |
| `2_VISJA/NIZJA_Temp_ZALOG_OGR` range | C 15.0–55.0 | J 120…550 (12.0–55.0) | J |
| `MK1_IME` enum | C 1 Circuit, 2 Unset, 4 HC2 … 21 HC1, 23/24; no 3, 22 | J lists (1 HC1, 2 HC2, 3 HC3, 4 DC1 …) | J (§6.2) |
| `2_Poti1` meaning | C 'internal temperature' / gas temperature in the HP | J/app 'Temperatura toplotne črpalke'; manual sensor HTT (HP water) | J/B |
| `2_Vklop_ele_grelca_1` meaning | C 'electric heater … for defrosting the outdoor unit' | info page 'Eksterni dodatni vir', menu 'Dodatni vir', heater relay K1 (B) | J/M: heater stage 1 / additional source |
| `2_PRIKAZ_Reg_temp_vode` meaning | C/M outdoor unit power % | name 'display of regulated water temperature'; readme example equals `2_Izrac_temp_TC` | open (§1.3 Q1) |
| `2_Rezim_delov_TC` enum | C 0 idle, 1 heating, 2 cooling, 3 defrost | app shows only 0 = Izklop | C unverified beyond 0 |
| `2_Vklop_C3` element | C solar pump (circuit 3 = solar) | M: both solar pump and circuit-3 pump; manual: shared output P3 | both; map it to whichever the schema has (#39) |
| Presence logic | C uses `2_Shema_MK1/DK1/MK2/DK2` | mono has no `2_Shema_DK1/DK2` | use `2_Shema` number + `2_PogojPGDT_Shema_OKn` |
| Slot-3 name list | J page settings_dyn_3: `2_IME_MK3` with `settings_titles` | J home: `MK1_IME(3)` with `widget_titles2`; settings page `settings_titles2` key 28 | open (§1.3 Q4); app inconsistent |
| `2_Rezim_*` per slot | C same map for slots 1–2 | J slot 3 lacks 5 | J |
| `2_Kalibracija_VF/_VF2` label | — | J EN 'MC temperature sensor calibration'; SI 'tipala vtoka' (flow sensor) | SI |
| EN app wording | — | 'outlet' = flow (vtok), 'HEATING CIRCLE' = circuit, 'FLOOR' = TALNO and ETAŽA, '1. rates', 'diference' | write own EN texts from SI |
| SI app labels in English | — | J `label_sl` is English for 2_Aktiv_avtom_preklop_zima_*, 2_Cas_ur_preklop_zima_*, 2_Temp_preklop_poletje_*_HL (3 each) and 2_Izbira_DOD_VIRA | translate ourselves |
| Timer weekday bindings | M Page201: each weekday label bound to two tags | J ranges decode 15/15 with the obvious mapping | J/T; M parse error |
| M page-title artefacts | M binds many setting labels to `MK1_IME…` (the page title) | — | ignore those M lines |
| `2_SV_24ur_timer` | name: DHW on 24 h | ours 1 while `2_Izbira_TIMERJA_SV` = 4 | trust the selection tag |
| `2_Tipalo_KF`, `2_Tipalo_VF2` | PLAN §5.2: sensor-present flags | duo KF = 1 without solar; VF2 follows the input, not the topology | input flags only (§3) |
| `2_Limita_moci_*` quantity | — | J label 'Limita diference TČ' but unit %, 151…300 | unclear; installer anyway |
| Working tree vs `main` of C | `main`: 72 tags, `2_Rezim_MK1/MK2` read-only | working tree: 74, Rezim writable, adds `2_PogojPGDT_Shema_in_tipalo_OK1/OK2` | user's uncommitted edits; J agrees Rezim is a setting |
| PLAN §5.2 'full circuit-name map in config.yml' | — | J lists | J; C map is wrong |

## 9. Appendix

### 9.1 Remaining S_OK tags on our pump (63)

All tags not in a catalog row are display-local variables of the touch screen (no `2_` prefix). All read 0 on our pump and on both other dumps, except the circuit-name mirrors `MK1_IME*` which are catalogued. They are the touch display's edit buffers, not controller state.

| pattern | count | tags | guess |
|---|---|---|---|
| `^(URA\|MINUTA\|DAN\|MESEC\|LETO)$` | 5 | `URA`, `MINUTA`, `DAN`, `MESEC`, `LETO` | Display-local clock edit variables. |
| `^(PARTY_CAS\|ECO_CAS\|Pocitniski_(DAN\|MESEC\|LETO))$` | 5 | `PARTY_CAS`, `Pocitniski_DAN`, `Pocitniski_MESEC`, `Pocitniski_LETO`, `ECO_CAS` | Display-local edit variables of the programme screens (menu map binds the party/ECO/holiday screens to them). |
| `^OSN_` | 17 | `OSN_Tipalo_B12`, `OSN_Kalib_AF`, `OSN_Shema`, `OSN_Zakasn_VKLOPA_TC`, `OSN_Zakasn_IZKLOPA_TC`, `OSN_Cas_mirovanja_TC`, `OSN_Zakasn_IZKLOPA_C0`, `OSN_Krivulja_TC`, `OSN_MAX_Moc_pri_OGR_PROST`, `OSN_Limita_moci_pri_OGR_PROST`, `OSN_Limita_moci_pri_SV`, `OSN_Limita_moci_pri_HLAJ`, `OSN_Vklop_Izklop`, `OSN_Shema_ZALOG`, `OSN_MAX_Moc_pri_HLAJ_PROSTOROV`, `OSN_MAX_Moc_pri_OGR_SV`, `OSN_MAX_Moc_TISJE` | Display-local aliases of the basic settings ('osnovne nastavitve'): schema, delays, limits, calibration, quiet power. |
| `^SV_` | 10 | `SV_Vklop`, `SV_LEGIONELA_Vklop`, `SV_Rezim_24_timer`, `SV_Diferenca`, `SV_Povisanje`, `SV_Legionela_URA`, `SV_Legionela_DAN`, `SV_Legionela_CIKEL`, `SV_Kalib_BF1`, `SV_Kalib_BF2` | Display-local aliases of DHW settings (enable, difference, boost, legionella, calibration, 24 h). |
| `^(MK1\|MK2\|DK3)_` | 17 | `MK1_Tocka1_HL`, `MK1_Tocka2_HL`, `MK2_Tocka1_HL`, `MK2_Tocka2_HL`, `DK3_Tocka1_HL`, `DK3_Tocka2_HL`, `MK1_Vklop`, `MK1_Vklop(3)`, `MK1_Instalacija`, `MK1_Povisanje`, `MK1_Instalacija(2)`, `MK1_Instalacija(3)`, `MK1_Povisanje(2)`, `MK1_Vklop(2)`, `MK1_Kontakt_RF1`, `MK2_Kontakt_RF2`, `DK3_Kontakt_RF3` | Display-local aliases of circuit settings (enable, installation, boost, room contact, cooling points); `(2)`/`(3)` = slot 2/3. |
| `^TEST_` | 7 | `TEST_CO`, `TEST_C1`, `TEST_C2`, `TEST_C3`, `TEST_MK1_O`, `TEST_MK1_Z`, `TEST_MK2_O` | Display-local output-test buttons. |
| `^(SERVIS\|SOLAR_Vklop)$` | 2 | `SERVIS`, `SOLAR_Vklop` | Display-local service/solar flags. |

Non-zero among them: none.

### 9.2 E_UNKNOWNTAG name patterns (1059 tags)

551 have no `2_` prefix: names of display-local variables from the touch project (63 of them exist on duo/mono, whose display project is newer), 508 are controller tags that our firmware (build 61, 2016-12-12) lacks. Of the 1,059, 532 exist on duo and 203 on mono.

| pattern | count | on duo | on mono | examples | what they are |
|---|---|---|---|---|---|
| `^CASOVNIK` | 190 | 0 | 0 | `CASOVNIK1URAVKLOP`, `CASOVNIK1MINUTAVKLOP`, `CASOVNIK1MINUTAIZKLOP`, `CASOVNIKIzbiraTimerjaMK1(1)` | Display-local timer editor aliases (`CASOVNIK<p>URAVKLOP(<r>)`, weekdays, selection). |
| `^SPREMEMBA` | 148 | 0 | 0 | `SPREMEMBAZALOGTempVisjaOGR`, `SPREMEMBAZALOGDiferencavklopa`, `SPREMEMBAZALOGTempNizjaOGR`, `SPREMEMBAZALOGTempVisjaHL` | Display-local 'value changed' flags for settings screens. |
| `^(MK1\|MK2\|DK3)_` | 97 | 30 | 30 | `MK1_TockaX1_HL`, `MK1_TockaX2_HL`, `MK2_TockaX1_HL`, `MK2_TockaX2_HL` | Display-local circuit aliases written without spaces (e.g. `MK1_TempDNEVNA`) and curve points. |
| `^(OSN\|SV\|SOLAR\|EH\|DODVIR\|DOD\|ZALOG\|PV\|NOVO\|VSTAVI\|Pogoj\|URE\|Cas\|Temp\|Zagon\|TEST\|HITRA\|Vklop\|LEGIONELA)` | 84 | 32 | 32 | `SVTemperatura`, `SV_z_EH_Temperatura`, `PV_Temp_SV_1`, `PV_Temp_ZALOG_1` | Other display-local aliases (basic, DHW, solar, heater, buffer, PV, hours, …). |
| `^(GESLO\|KODA)` | 22 | 0 | 0 | `GESLOServiserja1AA`, `KODAServiserjaAA1`, `KODAServiserjaBB1`, `KODAServiserjaCC1` | Display-local password/service-code aliases (password tags). |
| `^Jezik` | 9 | 0 | 0 | `JezikSLO`, `JezikIT`, `JezikEN`, `JezikD` | Display language selection. |
| `^Tag1$` | 1 | 1 | 1 | `Tag1` | Placeholder. |
| `^2_(On\|Off)_(Pon\|Tor\|Sre\|Cet\|Pet\|Sob\|Ned)_` | 204 | 204 | 0 | `2_Off_Ned_Ura_3`, `2_Off_Ned_Min_3`, `2_Off_Ned_Ura_2`, `2_Off_Ned_Min_2` | Per-weekday on/off timers (circuits, `_SV`, `_TISJE`): another timer scheme, present on duo only. |
| `^2_Timer_(MK2\|DK3\|SV\|ZALOG\|TISJE)_` | 30 | 30 | 0 | `2_Timer_MK2_24_ur`, `2_Timer_MK2_1`, `2_Timer_MK2_2`, `2_Timer_MK2_3` | One-hot programme-selection flags for the other consumers. |
| `^2_(URE\|VKLOPI\|MIN_URE\|MIN_Komp\|Pogoj_PRIKAZ\|Ure_Delov)` | 43 | 43 | 20 | `2_URE_EH3kW_OGR_17`, `2_URE_EH3kW_OGR_MAJ_17`, `2_URE_Komp_HLAJ_MAJ_17`, `2_URE_Komp_OGR_MAJ_17` | Operating hours and start counters (compressor, heater, per month/year) and their display conditions. Not available on our firmware. |
| `DEFROSTA\|Zascita_Defrost\|^2_i_Defrost` | 35 | 32 | 34 | `2_i_Defrost`, `2_Ura_DEFROSTA_1`, `2_Min_DEFROSTA_1`, `2_Dan_DEFROSTA_1` | Defrost log (last 5 defrosts: date/time) and defrost protection. |
| `^2_(PV_\|Signal_\|Pogoj_MASKA_Signal\|I_PV\|Max_Temp_BF_za_PV\|Max_Temp_ZALOG_za_PV\|MIN_HL_Temp_ZALOG_za_PV)` | 15 | 15 | 12 | `2_Signal_PV`, `2_Signal_EVU`, `2_Max_Temp_ZALOG_za_PV_f`, `2_Max_Temp_BF_za_PV_f` | PV function parameters and PV/EVU input signals. |
| `^2_I_` | 9 | 9 | 0 | `2_I_Pretok`, `2_I_Error`, `2_I_Kompresor`, `2_I_ID2` | Digital input mirrors (flow, error, compressor, ID2, heating/cooling, external off/on). |
| `^2_PogojPGDT_` | 9 | 9 | 8 | `2_PogojPGDT_N_OSN_ON_SV`, `2_PogojPGDT_N_OSN_ON_OK3`, `2_PogojPGDT_N_OSN_ON_OK2`, `2_PogojPGDT_N_OSN_ON_OK1` | Home-page demand indicators and the solar service flag. |
| `^2_Pogoj_` | 10 | 10 | 5 | `2_Pogoj_ikona_ele_grelca_3`, `2_Pogoj_ikona_ele_grelca_2`, `2_Pogoj_ikona_ele_grelca_1`, `2_Pogoj_maska_napis` | Display conditions (heater icon, EVU, party caption, DHW heater masks). |
| `OGR_Kr\|^2_Tocka_X` | 29 | 0 | 27 | `2_MK1_OGR_Krivulja_X2`, `2_MK1_OGR_Krivulja_X1`, `2_MK1_OGR_Krivulja_Y1`, `2_MK1_OGR_Krivulja_Y2` | Heating-curve points and cooling-curve X points (mono only). |
| `^2_(DK1\|DK2)_\|_DK1(_HL)?$\|_DK2(_HL)?$` | 8 | 8 | 0 | `2_DK2_vklop`, `2_DK1_24ur_timer`, `2_DK2_24ur_timer`, `2_Ponoci_min_temp_IZKLOP_DK1` | More legacy DK1/DK2 tags (enable, 24 h, low-regime action). |
| `EH\|Elektro_Grel\|ele_grelca_SV\|ELHSV\|Temperatura_z_EH\|Temperatura_SV_z_EH\|Temperatura_ZALOG_z_EH` | 17 | 17 | 12 | `2_Vstavi_Geslo_EH`, `2_Novo_Geslo_EH`, `2_Vstavi_Geslo_EH_MASKA`, `2_RESET_Vstavi_Geslo_EH_MASKA` | DHW electric heater (in-tank) settings and passwords. |
| `Alarm\|ALARM\|NAPAKA\|Reset\|RESET` | 15 | 15 | 1 | `2_Resetiranje_alarmov_OKV_FLOW`, `2_Resetiranje_alarmov_FLOW`, `2_Resetiranje_alarmov_TEMP`, `2_Resetiranje_alarmov_TC` | Newer alarm, error and reset tags. |
| `^2_Vklop_(SV\|OK\d\|Crpalke\|VENTILATOR)$` | 6 | 6 | 0 | `2_Vklop_SV`, `2_Vklop_OK1`, `2_Vklop_OK3`, `2_Vklop_OK2` | Element/pump/fan on-state mirrors (duo). |
| `SOLAR_PWM\|SOLAR_Crpalka\|Reg_PWM` | 4 | 4 | 3 | `2_Dif_za_MAX_SOLAR_PWM`, `2_SOLAR_Crpalka_PWM`, `2_Odstotki_SOLAR_PWM`, `2_Reg_PWM` | Solar pump PWM (speed) settings and output. |
| `ODZRA` | 4 | 4 | 2 | `2_Vklop_TESTNI_ODZRA`, `2_TEST_ODZRA_USPESEN`, `2_TEST_ODZRA`, `2_Preostanek_sekund_ODZRA` | Automatic de-aeration test ('odzračevanje'). |
| `ZALOG\|Zalog` | 7 | 7 | 4 | `2_Kalibracija_Zalog`, `2_Omejitev_temp_ZALOG_za_DK`, `2_Max_Temp_ZALOG_HL`, `2_Min_Temp_ZALOG_OGR` | Further buffer settings (calibration, limits for DK, cooling max, heating min, solar maxima). |
| `Izhod_13` | 5 | 3 | 1 | `2_Izhod_13`, `2_Izhod_13_ELGR`, `2_Izhod_13_PEC_Exsterni_GR`, `2_Izhod_13_HLAJ` | Output 13 function selection (heater, boiler, heating/cooling signal). |
| `CLOCK_CALIBRATION\|WEEKDAY\|Jutri_NOV` | 6 | 6 | 4 | `2_Jutri_NOV_Mesec`, `2_Jutri_NOV_Leto`, `2_CURRENT_CLOCK_CALIBRATION`, `2_NEW_WEEKDAY` | Clock calibration and weekday setting. |
| `Ro_no_Avtomatsko\|Delovanje_(Gretje\|Hlajenje)\|Hitra_izbira_rezima\|HITRI_Rezim_Normalno` | 11 | 7 | 0 | `2_Ro_no_Avtomatsko1`, `2_Delovanje_Hlajenje`, `2_Delovanje_Gretje`, `2_Hitra_izbira_rezima` | Manual heating/cooling switching per circuit and quick-mode helpers. |
| `za_prvi_zagon\|ZAGON_ORO` | 3 | 2 | 1 | `2_Izbrana_enota_za_prvi_zagon`, `2_Izbran_regulator_za_prvi_zagon`, `2_ZAGON_ORO` | Commissioning selections. |
| `^2_(Legionela_MAX_CAS\|Izbira_Urnika_SV\|PON_NED\|Temp_zelena_SV)$` | 4 | 4 | 1 | `2_Legionela_MAX_CAS`, `2_Izbira_Urnika_SV`, `2_PON_NED`, `2_Temp_zelena_SV` | DHW extras (legionella max time, schedule choice, active DHW setpoint `2_Temp_zelena_SV`). |
| `Geslo\|geslo\|Koda\|KODE` | 4 | 4 | 0 | `2_Shranjeno_geslo_za_ZAGON_B`, `2_Shranjeno_geslo_za_ZAGON_A`, `2_Vstavi_Geslo`, `2_vk_Koda_za_ZAGON` | Commissioning/password tags. |
| `Prikaz_display\|Izbira_prikaz` | 8 | 8 | 0 | `2_Izbira_prikaz_display_4`, `2_Prikaz_display_3`, `2_Prikaz_display_2`, `2_Prikaz_display_1` | Configurable display fields 1–4. |
| `^2_(Zunanja\|Prostor_\d\|Kolektorji\|Moc_TC\|TC\|BF\d\|Vtok_\d)$` | 10 | 10 | 0 | `2_Zunanja`, `2_Prostor_1`, `2_Kolektorji`, `2_Moc_TC` | Duo-only raw sensor/value mirrors. |
| `VMESNA\|Cas_osvezevanja_RF\|Vhod_ON_OFF_RF1` | 7 | 7 | 3 | `2_Temp_Prostora_VMESNA`, `2_Vhod_ON_OFF_RF1`, `2_Cas_osvezevanja_RF1`, `2_Temp_RF2_VMESNA` | Room-sensor helpers (intermediate value, refresh time). |
| other | 5 | 5 | 2 | `2_Dod_Vir_Rocno_Avtom`, `2_Izrac_temp_OGR`, `2_Ponoci_min_temp_IZKLOP_MK2_HL`, `2_IME_DK3`, `2_Zahtevana_RF_DK_1` | mixed; see names |
