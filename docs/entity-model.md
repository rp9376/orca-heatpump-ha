# Entity and topology model

Status: **accepted at CP1** (user, 2026-11-01; ADRs 0010, 0012, 0013). Built
from `research/findings.md` and `research/catalog_draft.md`; catalog keys
below are the catalog's.

## 1. Topology model

`PumpTopology` is detected once at setup (and compared on reload; a change
raises a repair issue):

| Field | Source, in order of precedence |
|---|---|
| schema | `2_Shema` → one of the 45 `wiring_diagrams` |
| circuit slot n present, kind MK/DK | schema table; cross-check `2_PogojPGDT_Shema_OK1/OK2` (no slot-3 flag exists) |
| circuit n room sensor | `2_PogojPGDT_Shema_in_tipalo_OKn` = 1; cross-check room temperature ≠ -9999 |
| circuit n regulation (heating, cooling) | `2_Reg_po_RF_AF_KONST_MKn[_HL]`: room / outdoor / room+outdoor / constant (read every poll; it decides which setpoint entities are meaningful) |
| hot water | schema table; cross-check `2_PogojPGDT_Shema_in_tipalo_SV` |
| solar | schema table (solar and circuit 3 share output P3, never both) |
| buffer | `2_Shema_ZALOG` (not in the schema name) |
| electric heater / additional source | `2_Izbira_DOD_VIRA`, `2_Izbira_st_grelcev` |
| features per tag | a tag exists if `browse` lists it (per pump, per firmware) |

Rules:
- An element is present only when its signals were actually read and agree.
  A missing record is "unknown", never "absent"; setup retries and then fails
  with `ConfigEntryNotReady` rather than guess.
- Never used: `2_Shema_DK1/DK2`, `2_Tipalo_*`, `2_Sobni_*` (R6).
- The options flow can force an element or a room sensor present/absent
  (repurposed inputs, #30).

## 2. Devices and unique IDs

| Device | Created when | Name | Via |
|---|---|---|---|
| Heat pump (main) | always | "Orca heat pump" (translated) | — |
| Circuit 1–3 | slot present | the circuit's own name from its name enum, e.g. "Floor"; fallback "Circuit n" (translation placeholder) | main |
| Hot water | DHW present | "Hot water" | main |
| Solar | solar present | "Solar" | main |
| Buffer tank | buffer present | "Buffer tank" | main |

- Manufacturer "Orca Energija", model "Heat pump" (+ outdoor unit make when
  known), `sw_version` "61 (2016-12-12)" from the program version tags.
- Device identifiers and entity unique IDs use `base` = the config entry ID
  (no hardware ID exists, R3): `{base}_{key}` for system and element keys,
  `{base}_circuit{n}_{key}` for circuit keys. The circuit's name never
  appears in an ID.
- Config entry unique ID: the host. No network discovery (ADR 0013); the
  reconfigure flow changes the host.

## 3. Entities

Legend: **on** = enabled by default, **off** = disabled by default;
**cfg** = entity category config, **diag** = diagnostic. Writable entities
write only through `OrcaClient.async_write` with the manufacturer's range.

### 3.1 Heat pump (main device)

| Key | Platform | Tag | Default | Notes |
|---|---|---|---|---|
| `outdoor_temperature` | sensor | `2_Temp_Zunanja` | on | °C |
| `hp_temperature` | sensor | `2_Poti1` | on | HP water temperature |
| `hp_target_temperature` | sensor | `2_Izrac_temp_TC` | on | |
| `outdoor_unit_power` | sensor | `2_PRIKAZ_Reg_temp_vode` | on | %, ×10 (R7) |
| `outdoor_unit_state` | sensor (enum) | `2_Rezim_delov_TC` | on | off / heating / cooling / defrost (2–3 to confirm) |
| `valve_3way` | sensor (enum) | `2_Preklop_PV1` | on | space heating / hot water |
| `pump_p0` | binary_sensor (running) | `2_Vklop_C0` | on | |
| `flow_switch` | binary_sensor | `2_Pogoj_maska_pret_stik` | off, diag | flow OK |
| `defrost_active` | binary_sensor | `2_Odtaljevanje_izhod` | on | |
| `system_enable` | switch | `2_Vklop_Izklop` | on | system on/off |
| `operating_programme` | select | `2_Delovanje_MENI` | on | normal / holiday / party / ECO |
| `quick_room_mode` | select | `2_HITRI_Rezim` | on | inactive / off / heating / cooling |
| `hp_power_limit_heating`, `_dhw`, `_cooling`, `quiet_power_limit` | number if "Allow changing power limits" is on, else sensor | `2_Max_moc_TC_pri_OGR/SV/HLAJ`, `2_Max_moc_TC_TISJA` | on, cfg | opt-in, ranges enforced in code (ADR 0012): 40–100 %, cooling 16–100 %, quiet 31–100 % |
| `quiet_mode`, `quiet_outdoor_temp`, `quiet_timer_programme` | select / number / select | `2_Tisje_delov`, `2_Temp_AF_za_TISJE_DEL`, `2_Izbira_TIMERJA_TISJE` | off, cfg | |
| `quiet_active` | binary_sensor | `2_Vklop_TISJE_DEL` | off | |
| `heater_mode` | select | `2_Vklop_Elektro_Grelci` | on if heater, cfg | off / auto / manual |
| `heater_stage1…3_on` | binary_sensor | `2_Vklop_ele_grelca_1…3` | on if stage exists | |
| `heater_stage*_delay`, `heater_stage*_outdoor_temp`, `additional_source_*`, `heater_parallel` | number / select / switch | A §2.9 | off, cfg | |
| `pv_function` | switch | `2_PV_Vklop` | off, cfg | |
| `screed_drying` + min/max flow; days, current day | switch, number; sensor | A §2.1 | off | advanced |
| `anti_block_programme` | switch | `2_Vklop_ANTI_BLOK_prog` | off, cfg | advanced |
| alarms | see §5 | | | |
| installer settings | sensor | §6 | off, diag | read-only |

### 3.2 Heating circuit n (slots 1–3; slot 3 = DK3 names)

| Key | Platform | Tag (slot 1) | Default | Notes |
|---|---|---|---|---|
| `climate` | climate | §4 | on | |
| `flow_temperature` | sensor | `2_Poti2` | on | -9999 → unavailable |
| `flow_target` | sensor | `2_Temp_zelena_MK_1` | on | |
| `room_temperature` | sensor | `2_Temp_Prostora` | on | only with a room sensor |
| `room_setpoint_active` | sensor | `2_Zahtevana_RF_MK_1` | off, diag | |
| `circuit_pump` | binary_sensor (running) | `2_Vklop_C1` | on | |
| `mixing_valve_state`, `mixing_valve_position` | sensor | `2_Delovanje_MP1`, `2_Odstotki_odprtosti_MP1` | on | MK circuits only |
| `flow_setpoint_heating` | number | `2_Max_VF_MK1` | on | **named "Flow temperature" in constant mode** (R8), "Maximum flow temperature" otherwise; 8–60 °C |
| `min_flow_heating` | number | `2_Min_VF_MK1` | off, cfg | 8–50 °C |
| `curve_parallel_shift`, `curve_slope` | number | `2_Zamik/Nagib_krivulje_MK1` | on with outdoor-based regulation, else off | ±15.0 |
| `room_setpoint_high`, `room_setpoint_low` | number | `2_Temp_prostor_dnevna/nocna` | only with a room sensor | high also via climate |
| `hp_boost_for_circuit` | number | `2_Povec_temp_TC_pri_MK1` | off, cfg | MK slots 1–2 only |
| cooling: `min_flow_cooling`, `cooling_flow_at_20`, `cooling_flow_at_30` | number | A §2.3 | off, cfg | |
| `circuit_mode` | select | `2_Rezim_MK1` | on, cfg | raw mode, lossless (slot 3 lacks "manual") |
| `heating_regulation`, `cooling_regulation` | select | `2_Reg_po_RF_AF_KONST_MK1[_HL]` | off, cfg | |
| `timer_programme` | select | `2_Izbira_TIMERJA_MK1` | on, cfg | 24 h / programme 1–5 |
| `low_regime_action` | select | `2_Ponoci_min_temp_IZKLOP_MK1` | off, cfg | off / lower temperature |
| `auto_heating_switch` (+ temp, delay), `auto_cooling_switch` (+ temp, delay) | switch, number | A §2.3 | off, cfg | summer/winter switch |
| `installation_type`, `room_sensor_type` | sensor | `2_Talno_Radiatorsko_MK1`, `2_Sobni_DPWT_PGD1` | off, diag | installer |

Circuit on/off is the climate's off mode; there is no duplicate switch.

### 3.3 Hot water

| Key | Platform | Tag | Default | Notes |
|---|---|---|---|---|
| `water_heater` | water_heater | §4.2 | on | |
| `dhw_temp_top`, `dhw_temp_bottom` | sensor | `2_Poti3`, `2_Poti4` | on | |
| `dhw_setpoint_low` | number | `2_Temp_vode_sanitarna_NIZJA` | on, cfg | 8–55 °C; high setpoint via the water heater |
| `dhw_on_difference`, `dhw_hp_boost` | number | `2_Diferenca_vklopa_SV`, `2_Povec_temp_TC_pri_SV` | off, cfg | |
| `dhw_timer_programme` | select | `2_Izbira_TIMERJA_SV` | on, cfg | |
| `legionella_enable` | switch | `2_Legionela_vklop` | on, cfg | |
| `legionella_temperature`, `legionella_hour` | number | A §2.5 | off, cfg | 65–70 °C |
| `legionella_day`, `legionella_cycle` | select | A §2.5 | off, cfg | |

### 3.4 Solar and buffer

| Key | Platform | Tag | Default |
|---|---|---|---|
| `solar_collector_temperature` | sensor | `2_Poti5` | on |
| `solar_pump` | binary_sensor | `2_Vklop_C3` | on |
| `solar_min_collector_temp`, `solar_on_difference`, `solar_off_difference` | number | A §2.6 | off, cfg |
| solar installer settings (enable, target, max temps) | sensor | A §2.6 | off, diag |
| `buffer_temperature`, `buffer_target` | sensor | `2_Temp_Zalog`, `2_Izrac_temp_ZALOG` | on |
| `buffer_high/low_heating`, `buffer_high/low_cooling`, `buffer_on_difference` | number | A §2.7 | on, cfg |
| `buffer_timer_programme` | select | `2_Izbira_TIMERJA_ZALOG` | off, cfg |

The README explains the buffer logic of #39 (computed target from the
higher/lower setpoints and the timer).

### 3.5 Weekly timers

Read-only in v1: the five programmes are exposed as diagnostic attributes of
the timer-programme selects and in diagnostics; editing them is in the
backlog.

## 4. Climate and water heater mapping

### 4.1 Climate (one per circuit)

- **HVAC mode** from `circuit_enable` and `circuit_mode`: enable 0 → `off`;
  mode 1 → `heat`, 2 → `cool`, 3 → `heat_cool`, 4 (switched by input ID2) and
  5 (manual switching) → `auto`. Setting `heat` / `cool` / `heat_cool` writes
  the mode (and enable = 1); `off` writes enable = 0 and keeps the mode;
  `auto` is only shown, never set (the raw `circuit_mode` select changes it).
- **Offered modes:** off, heat, cool, heat_cool on every circuit (Orca pumps
  can cool their heating circuits; user, CP1), plus auto while the circuit is
  in mode 4 or 5.
- **With a room sensor** and room or room + outdoor regulation (R8): a normal
  climate entity with current room temperature and the comfort (high) room
  setpoint as target, in the catalog's range (10–35 °C). Regulation is read
  every poll, so the target appears and disappears with it.
- **Without a room sensor** (the user's pump): a stripped-down, **mode-only**
  climate: on/off and heat/cool modes, no temperatures (user, CP1). On a
  constant-temperature circuit the flow setpoint is the separate number
  entity, because a climate target means a room temperature in HA.
- **Current temperature:** room temperature with a sensor, else none.
- **HVAC action:** `off` when the circuit or the whole system is disabled;
  `defrosting` while defrost is active; `heating`/`cooling` while the circuit
  pump runs and the HP state is heating/cooling; `idle` otherwise.
- **Presets:** none. The operating programme is global; it is the main
  device's select (a per-circuit preset would change all circuits).
- `native_*` temperature API; turn on/off supported.

### 4.2 Water heater

- Current temperature: `dhw_temp_top`. Target: `2_Temp_vode_sanitarna`
  (higher temperature, 8–55 °C).
- Operation modes: `off` (`2_SV_vklop` = 0) and `heat_pump` (on). No away
  mode (holiday is global).
- The currently active DHW setpoint is not readable on old firmware; the
  timer decides between higher and lower temperature (attributes show both).

## 5. Alarms

| Key | Platform | Source | Default |
|---|---|---|---|
| `alarm` | binary_sensor (problem) | `2_JE_ALARM` | on |
| `active_alarm` | sensor (enum) | `2_Vrsta_alarma` → texts of `research/alarm_texts.json`; unknown code → "Unknown alarm (code N)" | on |
| `alarm_outdoor_unit`, `alarm_flow_temp_circuit1/2`, `alarm_no_flow`, `alarm_flow_switch`, `alarm_hp_temp_low` | binary_sensor (problem) | `2_Alarm_*` (R4 table) | off |
| `alarm_event` | event | changes of `2_Vrsta_alarma`/`2_JE_ALARM`: `alarm_raised` / `alarm_cleared` with code and text | on |
| `reset_alarms` | button | `2_Reset_ALARMA_iz_PGDT` | off; works only after the Phase 6 test |
| newer firmware (`2_NAPAKA`, `2_Alarm_RF1…3`) | binary_sensor | when the tags exist | off |

No alarm history from the display exists (R4); HA's recorder keeps it.

## 6. Never exposed

- Passwords are not this integration's business (user, CP1): no password or
  code tag is in the catalog, so none is ever read, shown or written. No
  further machinery.
- Clock setting (`2_NEW_*`, `2_SET_*`), test outputs (`2_Vklop_TESTNI_*`),
  commissioning (`2_Opravljen_prvi_zagon`, `2_Zagon_opravlja_oseba`).
- HMI helper flags and legacy `*_DK1/*_DK2` duplicates (A §2.18–2.19);
  display-local variables (names with spaces).
- Installer settings are read-only diagnostic sensors, disabled by default:
  `PLAN.md` §10 plus A's proposals (solar enable/target/max temperatures,
  additional source choice, number of heater stages, delay after solar).

## 7. Parity with orca-energy-ha

Every one of its 54 entities maps to an entity above (D §4). Two that §8 of
the plan only implied are now explicit: `buffer_target` and
`buffer_on_difference`. Differences: its "gas temperature" is the HP water
temperature; circuit 3 is a real circuit (#39) instead of solar entities;
ranges follow the manufacturer (#20, K8).

## 8. Open points

- Room setpoint ranges (no pump with a room sensor recorded yet).
- Outdoor unit states 2 and 3; slot-3 circuit names above 6.
- Midnight-crossing timer ranges.
- `2_Min_VF_MKn` as setpoint with the "lower temperature" low-regime action
  (needs a write, Phase 6).
