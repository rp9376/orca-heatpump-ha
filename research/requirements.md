# Requirements, bugs and feature parity from orca-energy-ha (research D)

Research subagent D ("history miner"), Phase 1, 2026-10-31. Offline only:
no pump access, read-only git and the public GitHub REST API.

## 0. Sources and conventions

| Source | What was read |
|---|---|
| Old integration, branch `main` (`73a8741`, v2.4.3) | Every file in `custom_components/orca/`, `README.md`, `hacs.json`, `dashboards/`, `measuring_power_consumption/`, `development_resources/readme.md` and `dump_all/`, `.github/workflows/` |
| Old repo history | All 66 commits on `main`; every remote branch (`origin/*`, `rp9376/*`); `git blame` where noted |
| The user's uncommitted work | `git diff main` in the working tree (branch `climate-without-room-sensor`): a stop-gap fix for B1–B3 |
| GitHub `Tomasinjo/orca-energy-ha` | All 41 numbers: 22 issues and 19 PRs, open and closed; all 117 issue/PR comments; 4 PR review comments; PR list with merge state; contributors; commit authors (`author.login`); 8 forks (2 compared) |
| `../ORCA_FIX_NOTES.md` | Code review: flaws R1–R4, A1–A7, B1–B7 (unrelated to the research questions R1–R15) |
| `research/moja_orca_catalog.json` | Cross-check of the old ranges and enum maps against the manufacturer's tag metadata |
| `PLAN.md` §1, §5, §7, §8, §10 | The new design that each item is mapped to |

Conventions:
- `#N` links to issue or PR N of Tomasinjo/orca-energy-ha (all 41 numbers are referenced at least once).
- Short hashes are commits in `../orca-energy-ha/`.
- `file:line` means the file on `main`, i.e. `git show main:custom_components/orca/<file>`; `config.yml:N` is the line of that tag's `- tag:` entry.
- "WT" is the user's uncommitted working-tree fix on `climate-without-room-sensor`.
- People are named by GitHub handle only.
- **Tag count:** `config.yml` on `main` has **72** entries (72 distinct tags). The brief's "74" counts the working tree, which adds `2_PogojPGDT_Shema_in_tipalo_OK1/OK2`.

---

## 1. User requirements

"Users" counts distinct GitHub handles who asked for it (the maintainer is not counted unless he raised it himself).

| ID | Requirement | Raised by | Users | References | Status in orca-energy-ha | New design (PLAN) |
|---|---|---|---|---|---|---|
| U1 | Support **more than one heating circuit** (2 thermostats/branches), named as on the pump | @mohoricd-stack | 1 | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) | Done in 2.0 (multi-setup rewrite, [#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21)) | §8 circuits 1–3 |
| U2 | Expose **circuit 3 (DK3)** as a full heating circuit (min/max outlet heating, min outlet cooling, outlet temperature, climate). Both reporters run schema 39 (DK1+DK2+DK3+SV) | @truzzman, @sinjorgo | 2 | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39), [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) (comment 2026-05-05), [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) comment by @sinjorgo with the DK3 tag list | Open; maintainer: "hard to implement", slot 3 treated as solar | §8 circuits 1–3; §5.4 per-slot tags |
| U3 | **Climate without a room sensor**: HVAC mode control only, no room target | @rp9376, @truzzman (setup has "no room temperature sensors") | 2 | [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27), [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35), [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39), ORCA_FIX_NOTES §1, §3 | Open upstream (PR [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) stalled); WT fix | §7.3 climate rule (R8) |
| U4 | **Shared room sensor**: circuit 2 should show circuit 1's room temperature when only one room sensor is installed | @SuskoksuS (fork only, no issue) | 1 | fork `SuskoksuS/orca-energy-ha` README and `orca_api.py` (2026-03-06) | Not upstream | Not covered by the plan (R6/R8 question, Q6) |
| U5 | **Detect circuits from the pump's schema**, not by probing sensors that may be absent | @rp9376, @SuskoksuS (fork), one unnamed user ([#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27) comment 2026-04-25) | 3 | [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27), [#29](https://github.com/Tomasinjo/orca-energy-ha/pull/29), `1dc8349`, `92c3741` | Done in 2.3.0/2.3.1 | §7.2 `async_detect_topology` |
| U6 | **Manual override** when detection is wrong or an input is repurposed (solar input used for an external sensor) | @sinjorgo | 1 | [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30), [#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31), [#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32) | Done in 2.4.0 (options checkboxes); user praised it | §7.3 options flow: topology overrides |
| U7 | **Power limits** for heating, DHW and cooling, e.g. to save power in expensive tariff blocks | @mohoricd-stack, @truzzman | 2 | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14), [#19](https://github.com/Tomasinjo/orca-energy-ha/issues/19), [#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20), [#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33) | Done (2.0, cooling in 2.4.2), but ranges wrong (K8) | §8 max power heating/cooling/DHW |
| U8 | **Flow temperature control**: max/min outlet temperature for heating, min outlet temperature for cooling (dew-point automation) | @truzzman, @sinjorgo | 2 | [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24) | Done for circuits 1–2 (2.1.0, 2.2.0) | §8 min/max flow temperature (R8) |
| U9 | **Heating curve** parallel shift and slope | @truzzistefano61-dev | 1 | [#16](https://github.com/Tomasinjo/orca-energy-ha/issues/16), [#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21) | Done in 2.0 | §8 curve shift and slope |
| U10 | **DHW setpoint** from HA, varied by weather or PV surplus | @truzzman | 1 | [#40](https://github.com/Tomasinjo/orca-energy-ha/issues/40) | Water heater exists, but the reporter sees only the on-difference (K10) | §7.3 water heater, §8 hot water |
| U11 | DHW **lower temperature** and **on-difference** | @mohoricd-stack | 1 | [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18) | On-difference done (2.0.3-b); lower temperature not (maintainer: only acts with a timer programme) | §8 higher/lower setpoints, on-difference |
| U12 | **Buffer setpoints for cooling** (below 25 °C) | @truzzman | 1 | [#34](https://github.com/Tomasinjo/orca-energy-ha/issues/34) | Workaround: heating setpoints' minimum lowered to 15 °C (`7699a58`); the cooling buffer tags were not added | §8 buffer setpoints; catalog has `2_VISJA/NIZJA_Temp_ZALOG_HL` (9–40 °C) |
| U13 | **Document the buffer logic**: low/high buffer setpoints don't drive the buffer target in heating mode | @truzzman | 1 | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) | Open | §8 buffer: "explaining the actual logic from #39 in the docs" |
| U14 | Switch the **operating programme** (Party / Normal) from HA, to hand over between a pellet stove and the heat pump on PV surplus | @sinjorgo | 1 | [#17](https://github.com/Tomasinjo/orca-energy-ha/issues/17) | Not done (maintainer suggested set_temperature/hvac_mode instead) | §8 operating programme select `2_Delovanje_MENI` |
| U15 | **Reset** the pump remotely after it trips | @truzzman | 1 | [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24), [#25](https://github.com/Tomasinjo/orca-energy-ha/issues/25) | [#25](https://github.com/Tomasinjo/orca-energy-ha/issues/25) closed "completed" but nothing implemented on `main` | §7.3 optional reset button (R4) |
| U16 | **Solar**: collector temperature, solar pump, solar enable | @rp9376 | 1 | [#12](https://github.com/Tomasinjo/orca-energy-ha/pull/12), [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) | Done (2024); enable made read-only for safety ([#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26)) | §8 solar |
| U17 | Support circuit modes **external input (ID2)** and **manual** | @FloGerl | 1 | [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36) | Done (2.4.3), read-only, shown as `heat_cool` | §7.3 lossless mode select |
| U18 | Tolerate **empty values** with `S_OK` | @romanorac | 1 | [#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37) | Done (2.4.3) | §7.2 snapshot reasons |
| U19 | **Slovenian** entity names | maintainer; Slovenian-speaking users ([#22](https://github.com/Tomasinjo/orca-energy-ha/issues/22) is in Slovenian) | 1+ | [#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21), `const.py:12-15`, `dashboards/orca-tab-si.yml` | Done as a config option | §7.3 `en` + `sl` translations following the HA language |
| U20 | **0.1 resolution** for power and temperature settings (box input) | @mohoricd-stack | 1 | [#19](https://github.com/Tomasinjo/orca-energy-ha/issues/19), `a9c74e8`, `294b0ff` | Done | §7.3 numbers: box mode, step from catalog |
| U21 | **Long-term statistics** | maintainer | 0 | [#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21) | Done (`state_class: measurement` on °C and %) | §7.3 state classes |
| U22 | **Change the pump's IP** without deleting the integration | @maticnarobe | 1 | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) | Not possible (entry unique ID = host) | §7.3 reconfigure flow |
| U23 | **Find the pump** on the network | @marksev1 (answer by @timrosu: DHCP reservation, mDNS, MAC vendor "Carel s.p.a.") | 1 | [#15](https://github.com/Tomasinjo/orca-energy-ha/issues/15) | Docs only | R13 discovery |
| U24 | Older **LCD units** without the touch display / network port | @klobucaric2000-cmd | 1 | [#41](https://github.com/Tomasinjo/orca-energy-ha/issues/41) | Not supported (no network port; RS-485 J8 port only) | §8 "Not in v1" |
| U25 | **Coexist with Moja Orca** (cloud web/app) | @marksev1, @truzzistefano61-dev | 2 | [#15](https://github.com/Tomasinjo/orca-energy-ha/issues/15), [#23](https://github.com/Tomasinjo/orca-energy-ha/issues/23) | "Shouldn't conflict" ([#15](https://github.com/Tomasinjo/orca-energy-ha/issues/15)); [#23](https://github.com/Tomasinjo/orca-energy-ha/issues/23) not reproducible | §7.2 session handling; §5.4 (app holds one session) |
| U26 | The integration must **never change settings on its own** | @mohoricd-stack | 1 | [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18) | Principle (the report was a false alarm) | §10 write safety |
| U27 | Settings must not accept values the controller rejects (an out-of-range power value **restarted the controller**) | @mohoricd-stack | 1 | [#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20) | Not fixed (K8) | §7.2 range check from catalog/`LIMITS` |
| U28 | Example **dashboard** that covers two circuits; list card dependencies | @mohoricd-stack | 1 | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) comments, `dashboards/readme.md` | Single-circuit dashboard only | Not covered by the plan (Q12) |
| U29 | **Power consumption** metering | maintainer | 0 | `README.md` "Measuring power", `measuring_power_consumption/readme.md` | ESPHome guide | §8 "Not in v1" (link with credit) |
| U30 | Work on **older HA cores** | @marksev1 | 1 | [#22](https://github.com/Tomasinjo/orca-energy-ha/issues/22) | Won't fix (needs HA ≥ 2025.1 for pydantic v2) | D6: latest HA only, minimum in `hacs.json` |
| U31 | Read the **contact types** (3-way valve, ID2, flow switch, external block NO/NC) to compare setups | @truzzman (asked another user) | 1 | [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) comments 2026-05-03 | Not exposed | §10: installer settings, at most read-only diagnostics |

Setups seen in issues: Duo 300 (owner, [#13](https://github.com/Tomasinjo/orca-energy-ha/issues/13); @rp9376 "Duo 300 Solar", schema 23; @Speijtuut, Mitsubishi 12 kW outdoor unit, [#38](https://github.com/Tomasinjo/orca-energy-ha/issues/38)), Duo 200 ([#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3)), Mono with the Carel touch screen (@timrosu, [#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3)), a 10 kW unit with two circuits ([#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14)), schema 39 with three direct circuits and a buffer (@truzzman, @sinjorgo; [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30), [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39)), Mono 2023 with the LCD display ([#41](https://github.com/Tomasinjo/orca-energy-ha/issues/41)). Languages used in issues: English, Slovenian ([#22](https://github.com/Tomasinjo/orca-energy-ha/issues/22)). Units: only °C and %; nobody asked for °F.

---

## 2. Known bugs

Severity: H = breaks a platform, writes or the controller; M = wrong or missing data; L = cosmetic or dev tooling.

| ID | Sev | Symptom | Root cause | Affected setups | Upstream status | References |
|---|---|---|---|---|---|---|
| K1 | H | No climate entities; the config entry shows "Failed to set up" (`KeyError: 'hc_room_temp_1'`) | Climate is anchored on the room-temperature tag; `OrcaEntity` looks it up with `[]`; `-9999` values are dropped before | Every circuit without a room sensor (ours, schema 39 users) | **Open**; PR [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) open since 2026-07-19, maintainer pointed to the manual override, which doesn't help. WT fix anchors on `hc_name_N` | ORCA_FIX_NOTES §1 (B1), `climate.py:76`, `entity.py:30`, `orca_api.py:274`, [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) |
| K2 | H | Climate platform crashes with `AttributeError` when the circuit name is unmapped | `MK1_IME` = 1 had no `value_map` entry, so `hc_name_1` was missing and `climate.py:79` dereferenced `None` | Pumps with the factory circuit name | Fixed only for value 1 (`7e136c8`, 2.4.3); the suggested None-guard was not added; value 3 and any value outside the map still crash | [#38](https://github.com/Tomasinjo/orca-energy-ha/issues/38), `climate.py:79` |
| K3 | H | Changing the HVAC mode from HA fails with `ValueError` | `set_value_by_id("hc_turned_on")` / `("hc_mode")` without the `_N` circuit suffix | Everyone | **Open**; fixed in [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) and WT | B2, `climate.py:188-192` |
| K4 | H | Even with K3 fixed, the mode write is refused | `hc_mode` has `adjustable: false`; flipping it silently removes the "mode of operation" sensor (no select platform) | Everyone | **Open**; [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) flips the flag (hidden regression); WT flips it and adds an `orca_mode` attribute | B3, `config.yml:172,451`, `sensor.py:28-34`, ORCA_FIX_NOTES §2 |
| K5 | H | Climate crashes with `KeyError` in Slovenian | `CIRCUIT_NAME_MAP_SI[eng_name]` hard index; "Circuit", "Unset" are not in the map | SI users with unmapped circuit names | **Open**; fixed in [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) | B4, `climate.py:81`, `orca_api.py:40-58` |
| K6 | L | Wrong Slovenian names: "Heating Circuit 3" → "ogrevalni krog 1"; "tadiatorji" | Typos | SI users | **Open**; [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) and the fork `SuskoksuS/orca-energy-ha` fix only "radiatorji" | B5, `orca_api.py:43,53` |
| K7 | M | Circuits show the wrong name | The `MK1_IME` map disagrees with the manufacturer's list (`widget_titles` in the catalog) for values 1–8: e.g. 4 is shown as "Heating Circuit 2" but is "Direct circuit 1", 7 "Direct Circuit 2" is "Mixing circuit 1"; 3 is missing; 11 (ETAŽA, storey) and 16 (TALNO, floor heating) are both "Floor" and both become "talno" in SI; 21/23/24 are not in the manufacturer's list. `MK1_IME(3)` uses a different list (`widget_titles2`) | Pumps whose circuit name is a default/numbered name or "ETAŽA" | Not reported | `config.yml:27-49` (`e6e0df5`, `1dc8349`, `7e136c8`), `research/moja_orca_catalog.json` `lists.widget_titles` |
| K8 | H | Power limits accept values below the controller's minimum; an out-of-range value written by an automation **restarted the controller** | Hard-coded range 10–100 %; the manufacturer's metadata says 40–100 % (heating, DHW) and 16–100 % (cooling) on our pump | Everyone with power-limit automations | [#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20) closed 2026-01-15, but the range on `main` is unchanged | [#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20), `config.yml:679,695,711`, catalog `2_Max_moc_TC_pri_*` |
| K9 | M | DHW setpoint range 25–60 °C | Hard-coded; the manufacturer allows 8–55 °C, so 55.1–60 can be written and 8–24.9 can't | DHW users | Not reported | `config.yml:811`, `water_heater.py:43-44`, catalog `2_Temp_vode_sanitarna` |
| K10 | H | "Only the activation differential is displayed", no DHW setpoint | Unconfirmed hypothesis: the water heater is anchored on `wh_temp_top` (`2_Poti3`); if that tag reads `-9999` at setup the platform crashes like K1, and `wh_desired_temp` is excluded from the number platform, so the setpoint is exposed nowhere. @sinjorgo reports `2_Poti3` is not reported on the same schema 39 | Schema 39 (reporter) | **Open** | [#40](https://github.com/Tomasinjo/orca-energy-ha/issues/40), [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) comment, `water_heater.py:35,52`, `const.py:26-27` |
| K11 | M | Circuit 3 (DK3) is not exposed; the circuit-3 slot only carries solar entities | Slot 3 is hard-wired to solar (`heating_circuit: 3`); no DK3 tags in `config.yml`; climate only for circuits 1–2 | Schemas 28–45 (all with DK3) | **Open**; @sinjorgo runs a local patch (internal circuit id 6, presence `2_Shema_DK3`) | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39), [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30), `climate.py:58-62`, `orca_api.py:193-199` |
| K12 | M | Circuit 1 outlet temperature missing on schema 39; on our pump circuit 2's outlet temperature is missing instead | `2_Poti2` (circuit 1) or `2_Temp_VF2` (circuit 2) reads `-9999`; which physical sensor each tag is, per schema, is unknown | Schema 39, schema 23 | Open | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39), ORCA_FIX_NOTES §1 |
| K13 | M | Solar collector temperature disappeared after 2.3.x | With schema detection, circuit 3 is dropped when `2_Shema_SOLAR` = 0, although the solar input carries an external sensor (DK3 setup) | Setups that repurpose the solar input | Closed: manual override ([#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32), 2.4.0). The override also creates "solar pump" and "solar heating" entities that are meaningless on a DK3 setup. PR [#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31) (`force_include`) rejected | [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30), [#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31), [#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32) |
| K14 | H | Circuits not detected when a room or outlet sensor is absent | 2.0–2.2 detected circuits by probing sensor tags (`2_Temp_Prostora`, `2_Temp_RF2`, `2_Poti5`, …) | Pumps without room sensors | Fixed: `1dc8349` ([#29](https://github.com/Tomasinjo/orca-energy-ha/pull/29), schema tags) and `92c3741` (adds `2_PogojPGDT_Shema_OKn` for pumps whose `2_Shema_MKn/DKn` read 0) | [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27), `68fe790:custom_components/orca/orca_api.py` (old `circuit_tags`) |
| K15 | M | Max power heating had no effect in cooling | Missing tag `2_Max_moc_TC_pri_HLAJ` | Cooling users | Fixed `53a3ed9` (2.4.2), confirmed by the reporter | [#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33) |
| K16 | M | Buffer setpoint can't go below 25 °C for cooling | Only the heating buffer setpoints exist | Buffer + cooling | Workaround `7699a58` (min 15 °C); the cooling setpoints `2_VISJA/NIZJA_Temp_ZALOG_HL` were never added | [#34](https://github.com/Tomasinjo/orca-energy-ha/issues/34) |
| K17 | M | Buffer low/high setpoints appear to do nothing in heating mode; the buffer target follows the circuits' min/max outlet temperatures and drops to 10 °C during DHW cycles | Pump logic, not documented; the integration names suggest otherwise | Buffer schemas (reporter: schema 39 + buffer, no room sensors) | Open | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) |
| K18 | M | Circuit mode values 4 and 5 failed conversion | `value_map` covered 1–3 only | Pumps on external input or manual switching | Fixed `8962b90` ([#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36)) | [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36) |
| K19 | L | Conversion errors for empty values | Empty strings with `S_OK` reached the converter | Intermittent | Fixed `f01b60c` ([#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37)) | [#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37), `orca_api.py:274` |
| K20 | M | Bad values became 0.0 or raw strings | The converter returned `0.0`/raw value on failure | All | Fixed `3f99c70` (returns `None` and logs) | `3f99c70` |
| K21 | M | Circuit 2's min/max outlet numbers changed circuit 1 | Circuit 2 entries used `2_Max_VF_MK1`/`2_Min_VF_MK1` | 2-circuit pumps, 2.1.0 | Fixed `68fe790` (2.2.0); the fix **renamed unique IDs** (`hc_max_outlet_temp` → `hc_max_outlet_temp_heating`), orphaning entities | [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24) (2026-04-13 comments), `68fe790` |
| K22 | M | Circuit 2 entities named wrongly | The name tag was `MK2_IME` (doesn't exist) instead of `MK1_IME(2)` | 2-circuit pumps, 2.0 betas | Fixed `476cb74` | `476cb74` |
| K23 | H | `KeyError` on models without the 24-hour mode tag | `2_Timer_MK1_24_ur` missing on Mono | Mono | Fixed `a7b221b` ([#5](https://github.com/Tomasinjo/orca-energy-ha/pull/5)); tag later replaced by `2_Izbira_TIMERJA_MKn` (`476cb74`) | [#5](https://github.com/Tomasinjo/orca-energy-ha/pull/5), `a7b221b` |
| K24 | H | Writes from climate/water heater did nothing | Sync `set_*` methods called the async API | All (v1, 2024) | Fixed `2c8d51f`, `26b8e0d` ([#6](https://github.com/Tomasinjo/orca-energy-ha/pull/6), [#7](https://github.com/Tomasinjo/orca-energy-ha/pull/7)) | [#6](https://github.com/Tomasinjo/orca-energy-ha/pull/6), [#7](https://github.com/Tomasinjo/orca-energy-ha/pull/7) |
| K25 | M | Config flow shows raw `[%key:common::config_flow::error::cannot_connect%]` / `…::unknown%]` | v1 connection test failed (fixed by [#4](https://github.com/Tomasinjo/orca-energy-ha/pull/4)); the raw keys appear because `translations/en.json` contains `[%key:…]` references, which only HA core's build resolves | All custom installs | Connection test fixed; **raw keys still in `translations/en.json` on `main`**; the flow also shows `str(err)` | [#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3), [#4](https://github.com/Tomasinjo/orca-energy-ha/pull/4), [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14), `translations/en.json:4-9`, `config_flow.py:57` |
| K26 | M | Setup fails with `ConnectionTimeoutError` | Network (double NAT, unstable Wi-Fi); no reconfigure, untranslated error | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) reporters | Closed (network) | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) |
| K27 | L | Log warns about a blocking `open()` of `config.yml` | v1 read the YAML in the event loop | v1 | Closed; v2 uses `aiofiles` (`orca_api.py:157`) | [#17](https://github.com/Tomasinjo/orca-energy-ha/issues/17) |
| K28 | M | `RequirementsNotFound: pydantic>=2.0.6` | pydantic v2 needs HA ≥ 2025.1; `hacs.json` declares no minimum HA version | Older HA cores | Closed (won't fix) | [#22](https://github.com/Tomasinjo/orca-energy-ha/issues/22), `hacs.json`, `manifest.json:11-16` |
| K29 | L | Power settings rejected decimals | Step 1 / slider | All | Fixed `a9c74e8`, `294b0ff` | [#19](https://github.com/Tomasinjo/orca-energy-ha/issues/19) |
| K30 | – | Suspected unprompted write of the DHW lower temperature | Not a bug: the value was already 15 °C in an earlier dump | – | Closed | [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18) |
| K31 | M | No way to reset the pump after a trip | Not implemented | Pumps that trip (reporter) | [#25](https://github.com/Tomasinjo/orca-energy-ha/issues/25) closed "completed" without code (no reset tag on `main`) | [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24), [#25](https://github.com/Tomasinjo/orca-energy-ha/issues/25) |
| K32 | L | hassfest fails | `aiohttp` and `PyYAML` in `requirements` | CI | Open | B6, `manifest.json:11-16` |
| K33 | M | Deprecated climate/water-heater temperature properties | `temperature_unit`, `current_temperature`, `target_temperature*` | All; per ORCA_FIX_NOTES stops working in HA 2027.11 | Open | B7, `climate.py:69-117`, `water_heater.py:42-70` |
| K34 | H | Sessions pile up (`E_TOO_MANY_USERS`), and setup can hang | No `logout` anywhere; config flow, options flow and every reload create new sessions; `_authenticate` retries `E_TOO_MANY_USERS` every 5 s forever, inside the coordinator update | All | Open (not reported as such) | R2, `orca_api.py:313-341`, `config_flow.py:51-54,119-121` |
| K35 | M | Second climate entity rejected, or a new climate entity after renaming a circuit | Climate unique ID = `{entry_id}_climate_{name}`: two circuits with the same name (e.g. both TALNO) collide; a name change creates a new entity | Same-named circuits | Open (not reported) | A4, `climate.py:84-86` |
| K36 | M | An entity never appears until a reload | Entities are created only for tags with a valid value at the first refresh; a transient miss or `-9999` at boot means no entity. @rp9376 saw "unknown tag" on a first read that succeeded on the second | All | Open | `sensor.py:28-34`, `binary_sensor.py:24-30`, `number.py:24-30`, [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) (2026-04-30 comment) |
| K37 | M | All entities unavailable after one bad record | Any `#E_` code other than `E_UNKNOWNTAG` in a response fails the whole poll | Pumps returning e.g. `E_READFORBIDDEN`/`E_UNACTIVETAG` for a tag | Latent | `orca_api.py:309-310` |
| K38 | M | A batch of tags silently missing | HTTP status never checked; batches of 150 tags by count, and the pump answers HTTP 408 to request lines over ~4 KiB (`research/findings.md`, R11) | Latent with the 72-tag poll; hits long tag lists | Latent | `orca_api.py:290-311,343-357` |
| K39 | L | The first batch of every tag dump is the text `None` | The dump tool discards the response after re-login (`self.fetch_data(url)` then `return`) and never logs out; flagged by Copilot in [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) | Dumps made with `dump_to_file.py` (the maintainer asked users for these in [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39)) | Open on `main`; fixed only on `rp9376/Playing-with-climate-controls` (`2a827a8`) | `development_resources/dump_all/orca_api.py:73-77`, [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) review |
| K40 | L | Login fails for passwords with `&`, `#`, `+` or spaces | Username and password are interpolated into the URL unencoded | Non-default passwords | Latent | `orca_api.py:315` |
| K41 | L | Defrost shown as "heating" | `ACTION_MAPPING["defrost"] = HEATING` | All | Open | `climate.py:40-45` |
| K42 | L | Setting 7–9.9 °C from the climate card raises an error | Climate keeps HA's default 7–35 °C while the write range is 10–35 °C | Room-sensor users | Open | `climate.py:66-71`, `orca_api.py:418-424` |
| K43 | L | Odd entities: mixing-valve entities on direct circuits; `%` values with device class power factor; enum sensors show raw `room_heating`, `external_input_id2` | No element model; unit-driven device class | All | Open | `sensor.py:50-58`, `config.yml:134-159` |
| K44 | L | The SI dashboard doesn't match SI installs; dashboards cover one circuit | Entity IDs in `orca-tab-si.yml` are the English ones | SI users, 2-circuit users | Open | `dashboards/orca-tab-si.yml`, `dashboards/readme.md` |
| K45 | L | `22.35` is written as 22.3, `-0.15` as -0.1 | Write conversion truncates (`int(v * 10)`) instead of rounding; write responses aren't checked or read back | Automations passing extra decimals | Latent | `orca_api.py:425`, `orca_api.py:141-144` |
| K46 | M | A wrongly detected circuit can't be removed | In the options flow, unchecking every circuit means "auto-detect" | Rare | Open | `config_flow.py:93-103` |
| K47 | L | `test.py` with a hard-coded IP and credentials ships to users | Dev script inside the integration folder | All installs | Open | `custom_components/orca/test.py:6`, ORCA_FIX_NOTES §3b |

---

## 3. Design flaws to design out

Each: the flaw, then how the new design avoids it.

### From ORCA_FIX_NOTES.md

| ID | Flaw (old) | How PLAN avoids it |
|---|---|---|
| R1 | `__init__.py:40-44` catches every exception and returns `False`: a pump offline at boot leaves the integration dead until a manual reload. | §7.3 Setup: connection errors → `ConfigEntryNotReady`, auth errors → `ConfigEntryAuthFailed` (reauth), too many users → `ConfigEntryNotReady` with a translated message. |
| R2 | `_authenticate` loops forever on `E_TOO_MANY_USERS` with `sleep(5)` (`orca_api.py:317-337`). | §7.2 Login: `OrcaTooManyUsersError` raised immediately, no sleeping in the client; HA's retry handles backoff; §7.3 repair issue when sessions stay exhausted. |
| R3 | A new `aiohttp.ClientSession` per request (`orca_api.py:295,319`). | §7.2: the session is injected (`async_get_clientsession`), never created per request. |
| R4 | Hard lookups of optional tags at entity init crash whole platforms (K1, K2, K10). | §7.2: a snapshot contains every requested tag, with `None` and a reason; consumers never `KeyError`. §7.3: entities come from the topology, availability from the value. |
| A1 | `orca_api.py` mixes transport, auth, parsing, conversion, YAML loading, detection and HA naming. | §7.1/§7.2: `client/` package (client, protocol, codec, catalog, topology, models, errors) with no `homeassistant` imports, 100 % tested. |
| A2 | The platform is implied by `type` + `adjustable` + `EXCLUDED_IDS`; flipping a flag moves or deletes entities (K4); no select platform. | §7.1 `descriptions/` per platform (explicit), §7.3 select for every writable enum; §7.3a never silently remove an entity. |
| A3 | Language is a config option, names live in `config.yml`, `has_entity_name = False`. | §7.3 `has_entity_name = True` + `translation_key`; `en` and `sl` translations follow the HA language. |
| A4 | Entry unique ID = host (IP change → duplicate); climate unique ID = circuit name (K35). | §7.3: unique ID `{base}_{catalog_key}`, base = hardware ID (R3) or entry ID, circuit keys use the circuit number; config entry ID from R3; reconfigure flow. |
| A5 | `hass.data[DOMAIN]` instead of `entry.runtime_data`. | §7.3: typed `runtime_data` dataclass. |
| A6 | Config flow shows `str(err)`; the defined error keys are unused; options flow writes to `entry.data`, does network I/O on open, duplicates labels in Python. | §7.3 Flows: standard error keys, `unknown` logged with `_LOGGER.exception`, options in `entry.options`, config flow logs out. **Partly covered:** the plan doesn't say the options flow must avoid pump I/O; suggest pre-filling it from the stored topology. |
| A7 | Dependencies `aiofiles`, `pydantic`, `aiohttp`, `PyYAML`. | D4/D5: typed Python catalog, no runtime dependencies; §7.1 manifest without requirements. |
| B1 | Climate anchored on the room sensor (K1). | §7.3: climate per circuit from the topology; target temperature only with a room sensor and a room-based regulation mode (R8). |
| B2 | HVAC writes without the circuit suffix (K3). | §7.2 catalog: explicit tag per slot; §7.3 climate mapping is a tested table; P6 live write tests. |
| B3 | `hc_mode` not writable; making it writable removes its sensor (K4). | Explicit descriptions (A2): mode is a select **and** feeds the climate; writability lives in the catalog only. |
| B4 | SI name map with a hard index (K5). | Translations instead of a Python map; device names via `translation_key` + placeholders; unknown enum values decode to `None`. |
| B5 | Wrong SI names (K6). | §5.4: `sl` texts written from the Moja Orca SI UI texts (in `research/moja_orca_catalog.json`), not hand-typed maps. |
| B6 | hassfest fails on `requirements` (K32). | No requirements; hassfest in CI (§7.1 workflows). |
| B7 | Deprecated temperature properties (K33). | §7.3 `native_*` temperature API; D6 minimum HA 2026.11; CI against HA beta. |

### Found in this research

| ID | Flaw (old) | How PLAN avoids it |
|---|---|---|
| X1 | Never logs out; config flow, options flow and reloads leak sessions (K34). | §7.3: logout on unload and on HA stop; the config flow logs out; §7.2 idempotent `async_logout`. |
| X2 | Entity creation depends on values at the first refresh (K36). | §7.3: entities are created when the topology says the element exists; §7.2 "not received" never counts as "not present". |
| X3 | One bad record fails the whole poll (K37). | §7.2: per-tag reasons in the snapshot. |
| X4 | HTTP status unchecked; batching by tag count (K38). | §7.2 batching per R11 (by request length per `findings.md`). Add a test: HTTP 408 → protocol error, not "tags absent". |
| X5 | Ranges hard-coded and wrong (K8, K9, and §4 "catalog range" column). | §7.2: types and ranges from `research/moja_orca_catalog.json`, `LIMITS` if R2 allows; a unit test checks the catalog against the JSON. |
| X6 | Unique-ID churn on renames (K21) and platform moves (solar switch → binary sensor in `3bbb25a`; mode sensor in [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35)). | §7.3a compatibility rules: IDs never change; renames need a registry migration and a test. |
| X7 | Circuit-name enum misaligned (K7). | §7.2: enum maps from the catalog (`widget_titles` for `MK1_IME`/`MK1_IME(2)`, `widget_titles2` for `MK1_IME(3)`); unknown values → `None`, logged once. |
| X8 | Slot 3 conflated with solar (K11, K13). | §5.4/§7.2: explicit per-slot tags; topology knows DK3 and solar separately. |
| X9 | HVAC modes always off/heat/cool/heat_cool, whatever the pump can do; defrost reported as heating (K41). | §7.3: HVAC modes from capability, `hvac_action` from valve, pump and compressor. **Defrost not covered**: suggest `HVACAction.DEFROSTING`. |
| X10 | Mixing-valve entities on direct circuits, power-factor device class for `%`, untranslated enum states (K43). | §8 mixing valve "MK only"; §7.3 correct device/state classes, enum states translated. |
| X11 | The override can't force an element absent, and forcing circuit 3 brings solar entities to a DK3 setup (K13, K46). | §7.3 options: force present/absent per element and room sensor; repurposed input (#30) as its own override. |
| X12 | Credentials put into the URL unencoded (K40). | **Not covered by the plan**: build the login query with proper encoding (yarl `params`) and test with special characters. |
| X13 | Write path truncates, never checks the write response or reads back (K45). | §7.2 `async_write`: validate, encode, write, read back, skip if unchanged. **Rounding not specified**: the codec should round to the tag's resolution (test `22.35`, `-0.15`). |
| X14 | `[%key:…]` references in a custom integration's `translations/en.json` show raw (K25). | §7.3 complete `en`/`sl` translations. **Partly covered:** add a test that no `translations/*.json` contains `[%key:`. |
| X15 | Writes (circuit on, then mode) are separate, unlocked requests that race with polls; a failure between them leaves a half-applied state. | §7.2 one lock for all requests; read-back after each write. |
| X16 | Day/night setpoints exist only inside the climate entity, so they vanish when climate has no target temperature (ORCA_FIX_NOTES §3 caveat). | §8 circuit: day/night/desired room temperatures as their own entities (R8). |
| X17 | No tests, diagnostics, `PARALLEL_UPDATES`; coordinator without `config_entry`; dev script shipped (K47). | §7.1 tests and fixtures, §7.3 diagnostics, `PARALLEL_UPDATES`, coordinator with `config_entry`. |
| X18 | Service-level settings (min/max outlet temperatures, power limits; behind the service code on the panel per [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24), [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14)) are plain writable numbers with no warning. | **Partly covered:** §10 lists installer settings that are never writable, but not these. Decide at CP1 (Q9). |
| X19 | No minimum HA version in `hacs.json` (K28). | D6 / ADR 0006: minimum HA in `hacs.json`, raised when needed. |
| X20 | Example dashboards out of date (K44). | **Not covered by the plan** (Q12). |

---

## 4. Feature parity list

### 4.1 How the old integration creates entities

- One device, "Orca Heat Pump", manufacturer "Orca", model "Heat Pump", identifier `(orca, entry_id)`, no firmware (`entity.py:59-67`).
- **Unique ID:** `{entry_id}_{key}`; `key` = `id_N` for circuits 1 and 2, `id` otherwise (`entity.py:43`, `orca_api.py:227-244`). Climate and water heater override it (below).
- **Name:** `has_entity_name = False`. Circuit entities: `f"{circuit name} {name}".capitalize()`, where the circuit name is the English `MK1_IME`/`MK1_IME(2)` text or, in SI, `CIRCUIT_NAME_MAP_SI[...]` (fallback: the circuit number). Others: `name.capitalize()` (`orca_api.py:227-244`). Entity IDs in current HA get the device-name prefix (`number.orca_heat_pump_1_floor_min_outlet_temperature_heating`, [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39)).
- **Platform rules** (`sensor.py:28-34`, `binary_sensor.py:24-30`, `number.py:24-30`, `switch.py:26-32`, `const.py:19-30`):
  - `float`/`multimode`, not adjustable → sensor; °C → device class temperature, `%` → power factor, both `state_class: measurement`, else none
  - `boolean`, not adjustable → binary sensor (no device class)
  - `float`, adjustable → number (box mode, range/step from `config.yml`, entity category config)
  - `boolean`, adjustable → switch (entity category config)
  - adjustable `multimode` → **nothing** (no select platform)
  - `EXCLUDED_IDS` (`hc_desired_day_temp`, `hc_desired_night_temp`, `hc_turned_on`, `timer_programme`, `wh_turned_on`, `wh_desired_temp`, `hc_name`) → no own entity
- **Creation condition** (all platforms): the element is in `available_circuits` **and** the tag had a valid value at the first refresh.
  - Circuit 0 (heat pump): always.
  - Circuit 1: `2_Shema_MK1` or `2_Shema_DK1` or `2_PogojPGDT_Shema_OK1` = 1; circuit 2: same with `MK2/DK2/OK2`; circuit 3 (solar): `2_Shema_SOLAR` = 1; circuit 4 (DHW): `2_Shema_SV` = 1; circuit 5 (buffer): `2_Shema_ZALOG` = 1 (`orca_api.py:193-219`).
  - Or the options override, which replaces detection completely (`orca_api.py:209-210`).
  - Below, "C1/2+V" etc. means "circuit detected (or overridden) and value valid at first refresh".
- **Switch platform: creates no entities on `main`.** The only adjustable booleans are `hc_turned_on_N` and `wh_turned_on` (both excluded); "solar heating" was a switch until `3bbb25a` made it read-only.
- **Attributes:** none beyond HA's standard ones on `main`. The WT adds `orca_mode` (raw circuit mode) to climate.
- **Services:** none registered (no `services.yaml`). Only the platforms' standard services: `climate.set_temperature`, `climate.set_hvac_mode`, `water_heater.set_temperature`, `water_heater.turn_away_mode_on/off`, `number.set_value` (and `climate.turn_on/off` in the WT).
- **Options:** language (English/Slovenščina) and circuit override checkboxes 1–5, stored in `entry.data` (`config_flow.py:80-157`).
- **Maximum entity count:** 54 (25 sensors, 6 binary sensors, 20 numbers, 2 climate, 1 water heater, 0 switches) from 72 tags; 9 tags are detection-only, 1 is naming-only, 10 feed climate/water heater without their own entity.

Catalog range = the manufacturer's raw min/max from `research/moja_orca_catalog.json` ÷ 10 (all these tags are ×10). "≠" marks a disagreement with the old range.

### 4.2 Heating circuits 1 and 2 (one row per key; tags listed as circuit 1 / circuit 2)

| # | Key (`_N` = circuit) | Platform | Tag(s) read → written | Name EN / SI (`config.yml`) | Unit | Device / state class | Writable, old range [catalog] | Created when | `config.yml` lines | New counterpart (PLAN §8) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `hc_name_N` | none (naming, climate setup) | `MK1_IME` / `MK1_IME(2)` | name heating circuit / ime ogrevalnega kroga | – | – | no; enum (K7) | read at setup | 20, 299 | Circuit sub-device name (translation placeholder). Also `MK1_IME(3)` for slot 3 |
| 2 | `hc_room_temp_N` | sensor | `2_Temp_Prostora` / `2_Temp_RF2` | room temperature / prostorska temperatura | °C | temperature / measurement | no | C1/2+V | 54, 333 | Circuit n: room temperature (only with a sensor) + climate current temperature |
| 3 | `hc_desired_room_temp_N` | sensor | `2_Zahtevana_RF_MK_1` / `2_Zahtevana_RF_MK_2` | desired room temperature / željena prostorska temperatura | °C | temperature / measurement | no | C1/2+V | 66, 345 | Circuit n: desired room temperature (R8) |
| 4 | `hc_desired_day_temp_N` | none (climate `target_temperature` / `target_temperature_high`) | `2_Temp_prostor_dnevna` / `2_Temp_prostor_dnevna_OK2` → same | desired day temperature / željena dnevna temperatura | °C | – | yes, 10–35, step 0.1 [not in catalog] | excluded | 78, 357 | Climate target + circuit n day temperature number (R8) |
| 5 | `hc_desired_night_temp_N` | none (climate `target_temperature_low`) | `2_Temp_prostor_nocna` / `2_Temp_prostor_nocna_OK2` → same | desired night temperature / željena nočna temperatura | °C | – | yes, 10–35, step 0.1 [not in catalog] | excluded | 94, 373 | Climate target low + night temperature number (R8) |
| 6 | `hc_outlet_temp_N` | sensor | `2_Poti2` / `2_Temp_VF2` | outlet temperature / temperatura vtoka | °C | temperature / measurement | no | C1/2+V | 110, 389 | Circuit n: flow temperature (tag per slot to confirm, K12) |
| 7 | `hc_desired_outlet_temp_N` | sensor | `2_Temp_zelena_MK_1` / `2_Temp_zelena_MK_2` | desired outlet temperature / željena temperatura vtoka | °C | temperature / measurement | no | C1/2+V | 122, 401 | Circuit n: flow temperature target |
| 8 | `hc_mix_valve_status_N` | sensor (text) | `2_Delovanje_MP1` / `2_Delovanje_MP2` | mixing valve status / stanje mešalnega ventila | – | none | no; 0 off, 1 opening, 2 closing | C1/2+V (also on DK circuits) | 134, 413 | Circuit n: mixing valve status, MK only (enum sensor) |
| 9 | `hc_mix_valve_pos_N` | sensor | `2_Odstotki_odprtosti_MP1` / `2_Odstotki_odprtosti_MP2` | mixing valve position / odprtost mešalnega ventila | % | power factor / measurement (wrong) | no | C1/2+V (also on DK circuits) | 149, 428 | Circuit n: mixing valve position, MK only |
| 10 | `hc_pump_status_N` | binary sensor | `2_Vklop_C1` / `2_Vklop_C2` | pump status / stanje obtočne črpalke | – | none | no | C1/2+V | 161, 440 | Circuit n: pump status (binary sensor, `running`) |
| 11 | `hc_mode_N` | sensor (text); climate reads it and writes it (broken: K3, K4) | `2_Rezim_MK1` / `2_Rezim_MK2` → same | mode of operation / način delovanja | – | none | `adjustable: false`; 1 heat, 2 cool, 3 auto, 4 external_input_id2, 5 manual [catalog enum agrees; 0 = empty] | C1/2+V | 172, 451 | Climate HVAC mode + circuit n mode **select** (lossless). Slot 3 (`2_Rezim_DK3`) lacks value 5 |
| 12 | `timer_programme_N` | none (climate: single vs range target) | `2_Izbira_TIMERJA_MK1` / `_MK2` | timer programme / časovni program | – | – | no; 0 24h, 1–5 program 1–5 [catalog agrees] | excluded | 189, 468 | Circuit n: timer programme select |
| 13 | `hc_turned_on_N` | none (climate off) | `2_MK1_vklop` / `2_MK2_vklop` → same | turned on / vklopljeno | – | – | yes (bool) | excluded | 207, 486 | Climate on/off (no duplicate switch, §8) |
| 14 | `hc_curve_shift_paralell_N` | number | `2_Zamik_krivulje_MK1` / `_MK2` → same | parallel curve shift / vzporedna korekcija krivulje | none | – | yes, −9.9…9.9, step 0.1 [≠ −15.0…15.0] | C1/2+V | 218, 497 | Circuit n: heating curve parallel shift |
| 15 | `hc_curve_shift_slope_N` | number | `2_Nagib_krivulje_MK1` / `_MK2` → same | slope curve shift / korekcija nagiba krivulje | none | – | yes, −9.9…9.9, step 0.1 [≠ −15.0…15.0] | C1/2+V | 234, 513 | Circuit n: heating curve slope |
| 16 | `hc_max_outlet_temp_heating_N` | number | `2_Max_VF_MK1` / `_MK2` → same | max outlet temperature heating / max temperatura vtoka ogrevanje | °C | – | yes, 8–60, step 0.1 [8–60] | C1/2+V | 250, 529 | Circuit n: max flow temperature heating (maybe the constant-mode flow setpoint, R8) |
| 17 | `hc_min_outlet_temp_heating_N` | number | `2_Min_VF_MK1` / `_MK2` → same | min outlet temperature heating / min temperatura vtoka ogrevanje | °C | – | yes, 8–50, step 0.1 [8–50] | C1/2+V | 266, 545 | Circuit n: min flow temperature heating |
| 18 | `hc_min_outlet_temp_cooling_N` | number | `2_Min_VF_MK1_HL` / `_MK2_HL` → same | min outlet temperature cooling / min temperatura vtoka hlajenje | °C | – | yes, 9–40, step 0.1 [9–40] | C1/2+V | 282, 561 | Circuit n: min flow temperature cooling |
| 19 | climate, unique ID `{entry_id}_climate_{english circuit name, lower case}` | climate | reads rows 2, 4, 5, 11, 12, 13, 10 + `2_Preklop_PV1`, `2_Rezim_delov_TC`; writes rows 4, 5, 13, 11 | EN: circuit name (e.g. "Floor"); SI: `CIRCUIT_NAME_MAP_SI` + `.title()` (e.g. "Talno") | °C | features target temperature + target range; HVAC modes off/heat/cool/heat_cool; step 0.1; min/max HA default 7–35 | – | circuits 1, 2 in `available_circuits`; crashes without room temperature (K1) or name (K2) | `climate.py:48-194` | Circuit n climate entity (circuits 1–3), §7.3 |

### 4.3 Heat pump (circuit 0)

| # | Key | Platform | Tag read → written | Name EN / SI | Unit | Device / state class | Writable, old range [catalog] | Created when | `config.yml` line | New counterpart (PLAN §8) |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | `outdoor_temp` | sensor | `2_Temp_Zunanja` | outside temperature / zunanja temperatura | °C | temperature / measurement | no | C0+V | 579 | Heat pump: outdoor temperature |
| 21 | `internal_temp` | sensor | `2_Poti1` | internal temperature / interna temperatura (description: gas temperature in the HP) | °C | temperature / measurement | no | C0+V | 591 | Heat pump: flow temperature (Moja Orca "HP temperature"; confirm in R7) |
| 22 | `desired_internal_temp` | sensor | `2_Izrac_temp_TC` | internal desired temperature / interna tarčna temperatura | °C | temperature / measurement | no | C0+V | 603 | Heat pump: flow temperature target ("Desired HP temperature") |
| 23 | `outdoor_unit_power` | sensor | `2_PRIKAZ_Reg_temp_vode` | outdoor unit power / zunanja enota moč | % | power factor / measurement (wrong) | no | C0+V | 615 | Heat pump: compressor power % ([#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33) doubts the tag; confirm in R7) |
| 24 | `valve_pos` | sensor (text) | `2_Preklop_PV1` | position of 3-way valve / preklopni ventil | – | none | no; 0 room_heating, 1 hot_water | C0+V | 627 | Heat pump: 3-way valve position (enum) |
| 25 | `outdoor_unit_pump` | binary sensor | `2_Vklop_C0` | outdoor unit pump / zunanja enota črpalka | – | none | no | C0+V | 641 | Heat pump: circulation pump C0 |
| 26 | `electric_heater` | binary sensor | `2_Vklop_ele_grelca_1` | electric heater / delovanje električnega grelca (description: for defrosting the outdoor unit) | – | none | no | C0+V | 652 | Heat pump: electric heater status (stage 1) |
| 27 | `current_state` | sensor (text) | `2_Rezim_delov_TC` | current state / stanje delovanja | – | none | no; 0 idle, 1 heating, 2 cooling, 3 defrost | C0+V | 663 | Heat pump: operating state (enum); input to `hvac_action` |
| 28 | `max_power_heating` | number | `2_Max_moc_TC_pri_OGR` → same | max power heating / max moč ogrevanje | % | – | yes, 10–100, step 0.1 [≠ 40–100] | C0+V | 679 | Heat pump: max power heating (K8; Q9) |
| 29 | `max_power_cooling` | number | `2_Max_moc_TC_pri_HLAJ` → same | max power cooling / max moč hlajenje | % | – | yes, 10–100, step 0.1 [≠ 16–100] | C0+V | 695 | Heat pump: max power cooling |
| 30 | `max_power_water` | number | `2_Max_moc_TC_pri_SV` → same | max power hot water / max moč sanitarna voda | % | – | yes, 10–100, step 0.1 [≠ 40–100] | C0+V | 711 | Heat pump: max power DHW |
| 31 | `electric_heater_on_temp_1` | number | `2_Zun_temp_za_vklop_Grelec_1` → same | electric heater level 1 / vklop električnega grelca stopnja 1 | °C | – | yes, −30…10, step 0.1 [≠ −30…30] | C0+V | 727 | Heat pump: electric heater stage 1 outdoor threshold |
| 32 | `electric_heater_on_temp_2` | number | `2_Zun_temp_za_vklop_Grelec_2` → same | electric heater level 2 / … stopnja 2 | °C | – | yes, −30…10 [≠ −30…30] | C0+V | 743 | Stage 2 outdoor threshold |
| 33 | `electric_heater_on_temp_3` | number | `2_Zun_temp_za_vklop_Grelec_3` → same | electric heater level 3 / … stopnja 3 | °C | – | yes, −30…10 [≠ −30…30] | C0+V | 759 | Stage 3 outdoor threshold |

### 4.4 Hot water (circuit 4)

| # | Key | Platform | Tag read → written | Name EN / SI | Unit | Device / state class | Writable, old range [catalog] | Created when | `config.yml` line | New counterpart (PLAN §8) |
|---|---|---|---|---|---|---|---|---|---|---|
| 34 | `wh_turned_on` | none (water heater away mode, inverted) | `2_SV_vklop` → same | hot water enabled / sanitarna voda vklop | – | – | yes (bool) | excluded | 776 | Hot water: enable (switch) and/or water heater operation "off" |
| 35 | `wh_temp_top` | sensor (+ water heater current temperature and anchor) | `2_Poti3` | hot water top / sanitarna voda zgoraj | °C | temperature / measurement | no | C4+V | 787 | Hot water: top temperature + water heater current temperature |
| 36 | `wh_temp_bottom` | sensor | `2_Poti4` | hot water bottom / sanitarna voda spodaj | °C | temperature / measurement | no | C4+V | 799 | Hot water: bottom temperature |
| 37 | `wh_desired_temp` | none (water heater target) | `2_Temp_vode_sanitarna` → same | hot water desired temperature / sanitarna voda željena temperatura | °C | – | yes, 25–60, step 0.1 [≠ 8–55] | excluded | 811 | Water heater target + hot water higher setpoint ([#40](https://github.com/Tomasinjo/orca-energy-ha/issues/40), K9) |
| 38 | `wh_on_diff` | number | `2_Diferenca_vklopa_SV` → same | hot water on difference / sanitarna voda diferenca vklopa | °C | – | yes, 0–8, step 0.1 [0–8] | C4+V | 827 | Hot water: on-difference |
| 39 | water heater, unique ID `{entry_id}_water_heater` | water_heater | reads rows 35, 37, 34 + `2_Preklop_PV1`, `2_Vklop_C0`; writes rows 37, 34 | "Water Heater" / "Bojler" | °C | features target temperature + away mode; operation list idle/heating (display only: heating when valve = hot_water and C0 on); min 25, max 60 | – | C4 and `2_Poti3` valid at setup (else crash, K10) | `water_heater.py:24-104` | Water heater entity (§7.3), operation modes from R7 |

### 4.5 Solar (circuit 3)

| # | Key | Platform | Tag read → written | Name EN / SI | Unit | Device / state class | Writable | Created when | `config.yml` line | New counterpart (PLAN §8) |
|---|---|---|---|---|---|---|---|---|---|---|
| 40 | `wh_solar_turned_on` | binary sensor (switch until `3bbb25a`) | `2_SOLAR_VKLOP` | solar heating / sončna energija | – | none | no (made read-only for safety, [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26)) | C3+V | 844 | Solar: enable, **read-only** (Q8) |
| 41 | `wh_solar_pump` | binary sensor | `2_Vklop_C3` | solar pump / sončna energija črpalka | – | none | no | C3+V | 855 | Solar: pump |
| 42 | `wh_solar_temp` | sensor | `2_Poti5` | solar collector temperature / sončni kolektorji temperatura | °C | temperature / measurement | no | C3+V | 866 | Solar: collector temperature; repurposed-input override ([#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30)) |

### 4.6 Buffer (circuit 5)

| # | Key | Platform | Tag read → written | Name EN / SI | Unit | Device / state class | Writable, old range [catalog] | Created when | `config.yml` line | New counterpart (PLAN §8) |
|---|---|---|---|---|---|---|---|---|---|---|
| 43 | `buffer_temp` | sensor | `2_Temp_Zalog` | buffer temperature / zalogovnik temperatura | °C | temperature / measurement | no | C5+V | 879 | Buffer: temperature |
| 44 | `buffer_desired_temp` | sensor | `2_Izrac_temp_ZALOG` | buffer desired temperature / zalogovnik željena temperatura | °C | temperature / measurement | no | C5+V | 891 | Buffer: computed target sensor. Only implied by §8 "Buffer: temperature, setpoints"; list it explicitly at CP1 (semantics [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39)) |
| 45 | `buffer_high_temp` | number | `2_VISJA_Temp_ZALOG_OGR` → same | buffer high temperature / zalogovnik višja temperatura | °C | – | yes, 15–55, step 0.1 [≠ 12–55] | C5+V | 903 | Buffer: higher setpoint heating (+ cooling `…_HL`, [#34](https://github.com/Tomasinjo/orca-energy-ha/issues/34)) |
| 46 | `buffer_low_temp` | number | `2_NIZJA_Temp_ZALOG_OGR` → same | buffer low temperature / zalogovnik nižja temperatura | °C | – | yes, 15–55, step 0.1 [≠ 12–55] | C5+V | 919 | Buffer: lower setpoint heating (+ cooling) |
| 47 | `buffer_on_diff` | number | `2_Diferenca_vklopa_ZALOG` → same | buffer on difference / zalogovnik diferenca vklopa | °C | – | yes, 0–9, step 0.1 [0–9] | C5+V | 935 | Buffer: on-difference. Only implied by §8 "setpoints" (§5.4 names it); list it explicitly at CP1 |

### 4.7 Detection-only tags (circuit 99, never polled, no entity)

| # | Key | Tag | Purpose | `config.yml` line | New counterpart |
|---|---|---|---|---|---|
| 48 | `shema1_1` | `2_Shema_MK1` | circuit 1 present | 952 | Topology (§7.2); optional read-only diagnostic, disabled by default (§10 lists `2_Shema_*` as installer settings) |
| 49 | `shema1_2` | `2_Shema_DK1` | circuit 1 present | 963 | Topology |
| 50 | `shema1_3` | `2_PogojPGDT_Shema_OK1` | circuit 1 present, newer models | 974 | Topology |
| 51 | `shema2_1` | `2_Shema_MK2` | circuit 2 present | 985 | Topology |
| 52 | `shema2_2` | `2_Shema_DK2` | circuit 2 present | 996 | Topology |
| 53 | `shema2_3` | `2_PogojPGDT_Shema_OK2` | circuit 2 present, newer models | 1007 | Topology |
| 54 | `shema3` | `2_Shema_SOLAR` | solar present | 1018 | Topology |
| 55 | `shema4` | `2_Shema_SV` | DHW present | 1029 | Topology |
| 56 | `shema5` | `2_Shema_ZALOG` | buffer present | 1040 | Topology |
| WT | `room_sensor1/2` | `2_PogojPGDT_Shema_in_tipalo_OK1/OK2` | room sensor configured (WT only, not on `main`) | WT `config.yml` | Topology: room sensor yes/no (§5.2) |

**Coverage check:** rows 1–18 cover the 36 circuit tags, rows 20–33 the 14 heat-pump tags, rows 34–38 the 5 DHW tags, rows 40–42 the 3 solar tags, rows 43–47 the 5 buffer tags and rows 48–56 the 9 detection tags: 72 tags. Rows 19 and 39 are the two platform-code entities without their own tag. Every old entity has a counterpart in PLAN §8, so none needs a "no counterpart" reason; rows 44 and 47 are only implied by §8's wording and should be named explicitly at CP1. Behaviour that changes on purpose: mixing-valve entities only on MK circuits; `wh_solar_turned_on` stays read-only; numbers get catalog ranges; circuit 3 no longer means solar.

---

## 5. Behaviour worth keeping

| ID | Behaviour | Evidence |
|---|---|---|
| BK1 | Login → `IDALToken` cookie; on `E_NEED_LOGIN` log in again once and repeat the request once. | `orca_api.py:290-341` |
| BK2 | Some firmware returns an extra `INFO={"g":"admin","ot":0,"ex":…,"pwdd":3,"clientID":1}` line after the token (`ex` was 3950–4311 in three logins); after a power cycle the pump answered `#E_RE-LOGIN_ATTEMPT`, later a normal token. Input for R1 (the `ex` field may be a session lifetime). | [#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3), [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) |
| BK3 | `readTags` accepts any `client` value (`OrcaTouch1172` from the Moja Orca proxy; `client=Test` worked for a user). | `orca_api.py:352`, `development_resources/readme.md`, [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) |
| BK4 | Decoding: float = int ÷ 10 rounded to 1 decimal; boolean strictly 0/1; enum via map; `-9999` and empty = unavailable; anything else that fails → `None` with a log naming tag, raw value and type. | `orca_api.py:274-286,382-408`, [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36), [#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37) |
| BK5 | Encoding: float × 10, boolean `1`/`0`, enum by reverse map, range check before the write (fix the truncation, K45). | `orca_api.py:410-441` |
| BK6 | Per-record status: skip records that aren't `S_OK`; `E_UNKNOWNTAG` is normal for tags a model lacks. | `orca_api.py:359-380`, `findings.md` (1,059 unknown tags on our pump) |
| BK7 | Circuit detection from schema flags: circuit 1 = `2_Shema_MK1` OR `2_Shema_DK1` OR `2_PogojPGDT_Shema_OK1`, circuit 2 likewise, plus `2_Shema_SOLAR`, `_SV`, `_ZALOG`. History: sensor probing failed (K14); some pumps report `2_Shema_*` = 0 for a circuit that `2_PogojPGDT_Shema_OKn` reports. The maintainer wants one clean approach. | `orca_api.py:193-219`, [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27), [#29](https://github.com/Tomasinjo/orca-energy-ha/pull/29), `92c3741` |
| BK8 | Real schema-flag values from three pumps: owner DK1+SV; @rp9376 DK1+MK2+SOLAR+SV with `2_PogojPGDT_Shema_OK1/OK2` = 1, `in_tipalo_OK1/OK2/OK3` = 0, `in_tipalo_SV` = 1, `in_Upor_OK1/OK2/SV` = 1, `in_Servisni_*` = 0; one more user with circuit 1 only visible via `PogojPGDT`. Use as fixtures and for R6. | [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27) comments |
| BK9 | Room sensor present = `2_PogojPGDT_Shema_in_tipalo_OKn` (fallback: room temperature valid); without it, climate offers HVAC mode only. | WT `orca_api.py`/`climate.py`, ORCA_FIX_NOTES §3 |
| BK10 | Manual override with the detected elements pre-selected; users liked it ("much cleaner", [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30)). | `config_flow.py:110-150`, [#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32) |
| BK11 | Circuit names come from the pump (`MK1_IME*`) and name the devices/entities; never use them in unique IDs. | `orca_api.py:232-244`, A4 |
| BK12 | HVAC mapping: `2_MKn_vklop` = 0 → off; mode 1 heat → heat, 2 cool → cool, 3 auto → heat_cool, 4 external input and 5 manual → heat_cool (read only, never written). Write off → `vklop = 0`; other modes → `vklop = 1`, then the mode. Turn on keeps the current mode (WT). | `climate.py:25-38,119-127,180-194`, [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36), WT |
| BK13 | `hvac_action`: if the 3-way valve is on room heating and the circuit pump runs, map `2_Rezim_delov_TC` (idle/heating/cooling/defrost); otherwise idle. | `climate.py:129-139` |
| BK14 | Single vs range target: timer programme 0 (24 h) → one target = day temperature; programme 1–5 → low = night, high = day. The DHW lower temperature also only acts with a timer programme (owner, [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18)). | `climate.py:98-117,153-158`, [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18) |
| BK15 | Water heater: current = top sensor, target = `2_Temp_vode_sanitarna`, away mode = DHW disabled (`2_SV_vklop` = 0), "heating" when the valve is on hot water and pump C0 runs. | `water_heater.py:60-104` |
| BK16 | Solar enable never writable: turning it off from HA could overheat the collectors. | [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26), `3bbb25a` |
| BK17 | Numbers in box mode, step 0.1, entity category config; refresh right after every write. | `number.py:52`, `entity.py:48-57`, `294b0ff`, `a9c74e8`, [#19](https://github.com/Tomasinjo/orca-energy-ha/issues/19) |
| BK18 | `state_class: measurement` on temperatures for long-term statistics. | `sensor.py:50-52`, [#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21) |
| BK19 | A missing value makes the entity unavailable instead of crashing (keep, with the plan's stale tolerance). | `entity.py:74-77` |
| BK20 | Debug log of the full coordinator data solved [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30); the plan's diagnostics should carry the same (raw values per tag). | `coordinator.py:34-36`, `4ac0f59`, [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) |
| BK21 | Maintainer's tag-finding method: dump all tags while the panel shows a value, search the dump for value × 10; or watch Moja Orca's requests. | [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39), `development_resources/readme.md` |
| BK22 | Settings visible in the panel or Moja Orca can be added; the owner relied on screenshots of the service menus. | [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24) |

---

## 6. Contributors (for CREDITS.md)

Handles resolved through the GitHub commits API (`author.login`) and the issue/PR authors; no other lookups were needed.

| Handle | Check | Contribution |
|---|---|---|
| @Tomasinjo | **verified** (owner; git authors "Tomasinjo", "Tom" and "Tom Kern" all resolve to this login; 2 merge commits `1cbb6d8`, `9c18e0c` use an address not linked to the account and show as anonymous "Tom Kern" in the contributors API) | Author and maintainer (Tom Kern): protocol and tag discovery, v1 (2022), async rewrite and config-flow fix ([#4](https://github.com/Tomasinjo/orca-energy-ha/pull/4)), HACS support ([#8](https://github.com/Tomasinjo/orca-energy-ha/pull/8), [#9](https://github.com/Tomasinjo/orca-energy-ha/pull/9), [#10](https://github.com/Tomasinjo/orca-energy-ha/pull/10), [#11](https://github.com/Tomasinjo/orca-energy-ha/pull/11)), multi-setup rewrite with circuit detection, SI names, buffer, power limits and curve settings ([#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21)), schema detection ([#29](https://github.com/Tomasinjo/orca-energy-ha/pull/29)), circuit override ([#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32)), dashboards, ESPHome power metering guide, development resources and dumps; 54 commits |
| @thranduil | **verified** (git author "Robert", 5 commits) | [#1](https://github.com/Tomasinjo/orca-energy-ha/pull/1) (merged 2023-05-08): water heater entity, HVAC action, turning the pump off, 24 h vs timer target handling, defrost status, rename `orca-ha` → `orca` (`0d36f30`, `7b43623`, `03d203d`, `b45c05a`, `cbfec4b`) |
| @romanorac | **verified** (git author "Roman Orac") | [#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37): skip empty tag values, better conversion logging (`f01b60c`) |
| @FloGerl | **verified** | [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36): external-input and manual circuit modes (`8962b90`, co-authored by @Tomasinjo) |
| @rp9376 | **verified** (git authors "rp9376" and "420Cupcake" both resolve to this login) | [#12](https://github.com/Tomasinjo/orca-energy-ha/pull/12) solar tags (`7e17160`); [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) solar toggle made read-only + dump tool (`3bbb25a`, `8531371`); [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27) schema-based detection idea, schema table (`Citcuit_schemas.md`) and tag values; [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) climate without room sensor (open); testing. Owner of this rewrite |
| @sinjorgo | **verified** handle; not a commit author ([#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31) closed unmerged) | [#30](https://github.com/Tomasinjo/orca-energy-ha/issues/30) (repurposed solar input) and [#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31) (`force_include`), which led to the override in [#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32); [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24) request and service-menu screenshots for min/max outlet temperatures; [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) comment with the DK3 tag list; [#17](https://github.com/Tomasinjo/orca-energy-ha/issues/17) |
| @truzzman | **verified** | Reporter and tester: [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24) (flow temperatures, reset request), [#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33) (cooling power limit, tested), [#34](https://github.com/Tomasinjo/orca-energy-ha/issues/34) (buffer cooling), [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) (circuit 3, buffer logic findings), [#40](https://github.com/Tomasinjo/orca-energy-ha/issues/40) (DHW setpoint) |
| @Speijtuut | **verified** | [#38](https://github.com/Tomasinjo/orca-energy-ha/issues/38): root cause and fix for the unmapped circuit-name crash |

Other notable people (all handles verified as issue/comment authors):

| Handle | Contribution |
|---|---|
| @mohoricd-stack | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) (two circuits → the 2.0 rewrite; remote debugging with the owner), beta tester [#18](https://github.com/Tomasinjo/orca-energy-ha/issues/18)–[#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20) (DHW, decimals, power-limit crash) |
| @timrosu | Helped troubleshoot [#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3) (thanked by the owner); [#15](https://github.com/Tomasinjo/orca-energy-ha/issues/15): DHCP reservation, mDNS, Carel MAC vendor |
| @54m5p33d | [#3](https://github.com/Tomasinjo/orca-energy-ha/issues/3) (config flow failure, Duo 200) |
| @maticnarobe | [#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14) (setup failure after IP change) |
| @marksev1 | [#15](https://github.com/Tomasinjo/orca-energy-ha/issues/15), [#22](https://github.com/Tomasinjo/orca-energy-ha/issues/22) |
| @truzzistefano61-dev | [#16](https://github.com/Tomasinjo/orca-energy-ha/issues/16) (heating curve), [#23](https://github.com/Tomasinjo/orca-energy-ha/issues/23) |
| @Navaroff, @metalcamp, @klobucaric2000-cmd, @zigastegu | [#2](https://github.com/Tomasinjo/orca-energy-ha/issues/2), [#13](https://github.com/Tomasinjo/orca-energy-ha/issues/13), [#41](https://github.com/Tomasinjo/orca-energy-ha/issues/41), [#23](https://github.com/Tomasinjo/orca-energy-ha/issues/23) comment |
| @SuskoksuS | Fork with shared-room-sensor handling (no PR) |

The PR review comments on [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) came from the Copilot bot, not a person.

---

## 7. Other repos and branches

| Branch / repo | State | Useful content |
|---|---|---|
| `origin/multi-setup-support-rewrite` (`b81d966`) | Fully merged ([#21](https://github.com/Tomasinjo/orca-energy-ha/pull/21)) | Nothing beyond `main` |
| `origin/config_flow_fix_and_async_rewrite` (`64e1e63`) | Merged ([#4](https://github.com/Tomasinjo/orca-energy-ha/pull/4)) | Nothing beyond `main` |
| `origin/fix_for_models_without_24_hour_mode` (`26b8e0d`) | Merged ([#5](https://github.com/Tomasinjo/orca-energy-ha/pull/5), [#7](https://github.com/Tomasinjo/orca-energy-ha/pull/7); [#6](https://github.com/Tomasinjo/orca-energy-ha/pull/6) closed duplicate) | Nothing beyond `main` |
| `origin/hacs_support` (`9578584`) | Merged ([#8](https://github.com/Tomasinjo/orca-energy-ha/pull/8), [#9](https://github.com/Tomasinjo/orca-energy-ha/pull/9), [#10](https://github.com/Tomasinjo/orca-energy-ha/pull/10), [#11](https://github.com/Tomasinjo/orca-energy-ha/pull/11)) | Nothing beyond `main` |
| `origin/rp9376-main` (`ac5f12c`) | Merged ([#28](https://github.com/Tomasinjo/orca-energy-ha/pull/28), the owner's merge of [#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26)) | Nothing beyond `main` |
| `rp9376/better_circuit_selection` (`1dc8349`) | The owner's [#29](https://github.com/Tomasinjo/orca-energy-ha/pull/29) branch, merged | Nothing beyond `main` |
| `rp9376/main` (`2a67bb5`) | = open PR [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35): `cc2af6c` SI "radiatorji", `fed5a88` `.gitignore`, `2a67bb5` climate without room sensor | Optional anchor in `OrcaEntity`, name fallback "Heating Circuit N", `.get()` on the SI map, B2/B3 fixes. The WT fix goes further (room-sensor detection, turn on/off, `orca_mode` attribute) |
| `rp9376/Playing-with-climate-controls` (`1be11f1`) | Older attempt, superseded by [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) | `sensor.py` keeps adjustable enums as sensors (avoids the [#35](https://github.com/Tomasinjo/orca-energy-ha/pull/35) regression); `2a827a8` dump tool: `--host`/`--tag` options, caches the token in a file to reuse the session, fixes K39 |
| Fork `sinjorgo/orca-energy-ha` `patch-1` | = [#31](https://github.com/Tomasinjo/orca-energy-ha/pull/31), closed | `force_include` flag for one tag (rejected in favour of [#32](https://github.com/Tomasinjo/orca-energy-ha/pull/32)) |
| Fork `SuskoksuS/orca-energy-ha` (3 commits, 2026-03-06) | Not proposed upstream | Circuit 2 detected by any of `2_Vklop_C2`, `2_Zahtevana_RF_MK_2`, `2_Delovanje_MP2`; circuit 2 falls back to circuit 1's room temperature (U4). Its `climate.py` was overwritten with `orca_api.py` content, so the fork is broken |
| Fork `thranduil/orca-energy-ha` (2 commits, 2024-05-04) | Not proposed upstream | v1 `TEMP_CELSIUS` → `UnitOfTemperature`; nothing new |
| Forks `FloGerl/…`, `romanorac/…` (`agent/…` branches) | Merged as [#36](https://github.com/Tomasinjo/orca-energy-ha/pull/36), [#37](https://github.com/Tomasinjo/orca-energy-ha/pull/37) | Nothing beyond `main` |
| @sinjorgo's local DK3 patch (unpublished, [#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39) comment) | – | Slot-3 tags seen on a pump: `MK1_IME(3)`, `2_Temp_RF3`, `2_Zahtevana_RF_DK_3`, `2_Temp_prostor_dnevna_OK3`/`_nocna_OK3`, `2_Vklop_OK3` (pump), `2_Rezim_DK3` (read-only there), `2_DK3_vklop`, `2_Zamik_krivulje_DK3`, `2_Nagib_krivulje_DK3`, `2_Max_VF_DK3`, `2_Min_VF_DK3`, `2_Min_VF_DK3_HL`, presence `2_Shema_DK3`; no outlet-temperature tag found. Input for subagent A / R7 |

---

## 8. Open questions for the lead

| ID | Question | Why it matters |
|---|---|---|
| Q1 | The brief says `config.yml` has 74 tags; `main` has 72 (the WT adds 2). Use 72 + the WT's 2 as the parity baseline? | Parity bookkeeping |
| Q2 | `MK1_IME` map: is the manufacturer's `widget_titles` list authoritative for values 1–8, and where do the old values 21, 23, 24 come from (older firmware)? (K7) | Device names; R12 |
| Q3 | Which tag is each circuit's flow temperature? On our pump `2_Temp_VF2` (circuit 2) reads `-9999`; on schema 39 `2_Poti2` (circuit 1) does; no slot-3 tag is known. (K12) | Circuit flow-temperature entity per slot; R7 |
| Q4 | [#40](https://github.com/Tomasinjo/orca-energy-ha/issues/40): confirm the hypothesis that the water heater crashed because `2_Poti3` was missing (K10). Either way, the new water heater must not depend on the top sensor. | DHW setpoint must always be reachable |
| Q5 | Buffer semantics ([#39](https://github.com/Tomasinjo/orca-energy-ha/issues/39)): what drives `2_Izrac_temp_ZALOG`? Do the `…_ZALOG_OGR/_HL` setpoints act only with a buffer timer, a room sensor or a regulation mode? | Buffer entity naming and docs (U12, U13) |
| Q6 | Shared room sensor (U4): with one sensor, does the pump use it for circuit 2, and should circuit 2's climate show it? | Climate current temperature; R6/R8 |
| Q7 | `2_PRIKAZ_Reg_temp_vode` ([#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33)) and `2_Poti1` ("gas temperature" in the old description, "HP temperature" in Moja Orca): confirm meaning before naming. | Main-device sensor names; R7 |
| Q8 | Keep `2_SOLAR_VKLOP` read-only forever ([#26](https://github.com/Tomasinjo/orca-energy-ha/pull/26) safety argument)? Same question for other enables whose misuse can damage hardware. | Write safety §10 |
| Q9 | Power limits and min/max outlet temperatures sit behind the service code on the panel ([#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14), [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24)), but users rely on them in automations ([#20](https://github.com/Tomasinjo/orca-energy-ha/issues/20), [#24](https://github.com/Tomasinjo/orca-energy-ha/issues/24), [#33](https://github.com/Tomasinjo/orca-energy-ha/issues/33)). Writable as in the old integration, or installer settings under §10? | Parity vs safety (X18) |
| Q10 | Power-limit minimum: the catalog says 40 % (heating/DHW) and 16 % (cooling) on our pump, but a user with a 10 kW unit set 15–100 % in service mode ([#14](https://github.com/Tomasinjo/orca-energy-ha/issues/14)). Per-model limits? Does `LIMITS` (R2) give them? | Range validation (K8) |
| Q11 | Defrost: map `2_Rezim_delov_TC` = 3 to `HVACAction.DEFROSTING`? (X9) | Climate `hvac_action` |
| Q12 | Ship an example dashboard (the old one was popular but single-circuit and outdated, K44), or only document entities? | Docs scope (X20) |
| Q13 | The `INFO={…"ex":…}` field after login on some firmware (BK2): a session lifetime in seconds? Check in R1. | Session model |
| Q14 | [#25](https://github.com/Tomasinjo/orca-energy-ha/issues/25) (reset after trip) was closed without code. Does R4 find a safe reset tag (`2_Reset_ALARMA_iz_PGDT`, seen as 0 in [#27](https://github.com/Tomasinjo/orca-energy-ha/issues/27))? | Reset button (U15) |
| Q15 | The old `climate` entity is "mode only" for constant-temperature circuits in the WT; does R8 confirm that `2_Max_VF_MKn` is the flow setpoint there, so the climate (or a number) can offer it? | Climate features for the user's own pump |
