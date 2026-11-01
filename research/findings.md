# Research findings (Phase 1)

Answers to R1–R15 (`PLAN.md` §6.1) with evidence and confidence. Raw
evidence is in `research/captures/` (gitignored). `requests.jsonl` there logs
every request the probe made: time, endpoint, header bytes, HTTP status, size,
duration and response headers. Committed derivatives:

- `tests/fixtures/dumps/schema23_duo300solar_2026-10-31.json`: all 1,767
  known tag names, timer off.
- `tests/fixtures/dumps/schema23_duo300solar_2026-11-01_heating.json`: the
  694 readable tags with the heat pump heating.
- `research/tag_registers.json`: all 1,189 tag definitions on the display.
- `research/alarm_texts.json`: alarm codes and texts in 7 languages.

Sources of the other research files: `catalog_draft.md` (A), `manual_facts.md`
(B), `protocol.md` (C), `requirements.md` (D).

Status: **complete for CP1**, 2026-11-01. Confidence: **high** = observed
live or stated by the manufacturer; **medium** = strong inference from
several sources; **low** = plausible, unverified.

## Live sessions

All read-only, serial, one session at a time, with the endpoint allowlist
enforced in `tools/orca_probe.py`. Before each, no HA instance polled the
pump. `E_TOO_MANY_USERS` was never returned.

| When (CET) | Session | Logins | Requests | Result |
|---|---|---|---|---|
| 10-31 20:23 | Static console files (`orca_probe.py console`) | 0 | 22 | 20 files in `captures/console/` |
| 10-31 20:24 | Full dump, 2 passes (`orca_probe.py dump`) | 1 | 32 | 708 `S_OK`, 1,059 `E_UNKNOWNTAG`; one 408 batch per pass |
| 10-31 23:57 | S1: discovery, limits, reliability (`orca_research.py session1`) | 1 | 93 | complete; 3 requests after logout test dead tokens |
| 11-01 00:01 | S2a: stale-cookie login, R14 `alarms.xml` | 1 | 5 | stopped as designed at `#E_FILEOPENFAIL` (directory path); health check OK |
| 11-01 00:07 | S2b: `Page109.jmx`, `eventconfig.xml` | 1 | 5 | stopped as designed at `#E_FILENOTEXIST` (`propertymap.xml`); health check OK |
| 11-01 00:12 | S2b: `Page109 - Kopija.jmx` (the alarm page) | 1 | 3 | complete |
| 11-01 00:13–00:36 | S3: session lifetime | 1 | 14 | idle timeout 2–3 min |
| 11-01 09:35 | Tag definitions (`orca_research.py meta`) | 1 | 5 | 1,189 definitions |
| 11-01 09:36 | Snapshot of all readable tags | 1 | 7 | heat pump heating, circuit 1 timer on |
| 11-01 10:28 | Phase 2 exit: catalog read through `OrcaClient` (`orca_probe.py read`, read-only session) | 1 | 6 | identity, topology #23, 189 tags; only explained gaps (4 newer-firmware alarm tags, 5 unplugged sensors) |

The R14 stops followed the rule "stop at the first unexpected error". Both
new codes plainly mean "not a file" / "no such file", the display stayed
healthy (health check `GET /` = 200 five minutes later), so the lead resumed
with the remaining **named** files only; no path was guessed.

## Summary for the design

1. **The API does not drop records.** The "flaky API" of `PLAN.md` §5.1 is
   a hard limit: the display answers **HTTP 408 to any request whose header
   block exceeds 4,095 bytes**, at once and every time. Under the limit, 50
   requests / 6,940 records returned every record in request order (R11).
2. **One session lives as long as it is used.** Reads every 2 min kept it
   alive for 20 min; it expires after 2–3 min idle. Errors come back as
   HTTP 500 with a `#E_…` body (R1).
3. **The display has no hardware ID** for the integration: no MAC, serial
   or hostname on any allowed endpoint. Its MAC vendor prefix is Carel's
   (R3, R13).
4. **Alarm texts exist and are now known** (6 codes, 7 languages), from the
   display's own alarm page. The display's IDAL alarm and event system is
   not used for pump alarms, so there is no alarm history (R4, R14).
5. **Constant-temperature regulation is confirmed live:** with the timer on,
   the heat pump target equals `2_Max_VF_MKn` (R8).
6. **Tag existence differs by firmware** (ours: build 61 from 2016, the
   oldest of three). `browse` lists exactly the tags a pump has; ranges,
   units and enums come only from the manufacturer's app metadata (R2, R5).

## R1. Session model

**Answer.**
- Login: `GET /cgi/login?username=…&password=…` → HTTP 200,
  `1\n#S_OK\nIDALToken=<32 hex>`. The token is sent back as cookie
  `IDALToken`.
- **Reads keep a session alive:** a read every 2 min for 20 min, all
  `S_OK`.
- **Idle timeout: more than 2 and at most 3 minutes.** After a 3-min gap the
  token was dead (`#E_NEED_LOGIN`).
- **Logout** (`GET /cgi/logout`) → `1\n#S_OK`, and the token is dead at
  once: a read with it → HTTP 500 `#E_NEED_LOGIN`; a second logout → HTTP
  500 `#E_NEED_LOGIN`; a read without any token → HTTP 500 `#E_NEED_LOGIN`.
- Logging in while sending a stale (logged-out) cookie → a normal `#S_OK`
  with a new token. `#E_RE-LOGIN_ATTEMPT` was never seen. The console treats
  it as success; it is most likely a login that presents a still-valid token
  (C, low).
- 9 logins over 13 hours, never `E_TOO_MANY_USERS`, including right after
  the old integration's config entry was deleted.

**Not measured:** how many sessions fit at once, and whether logout frees a
slot immediately. Both need several sessions open at the same time, which
breaks `PLAN.md` §2.2 rule 4 (C's gated Session 4). A related device of the
same server family allows 2 (C, low). Decision at CP1.

**Design consequences.** A 30 s poll keeps one session indefinitely. A
leaked session (crash, kill) frees its slot within 3 min by itself, so the
plan's 1/2/4/8-min backoff is ample. The client re-logs in once on
`E_NEED_LOGIN`, which arrives with HTTP 500, and always logs out on unload.

**Evidence:** `captures/2026-10-31_research/session1/S1-90…93`,
`captures/2026-11-01_research/session2a/S2-01*`, `…/session3/` (timeline).
**Confidence:** high (timeout bracket from one run).

## R2. Tag enumeration and metadata

**Answer.**
- **`browse` enumerates every tag defined on the display:** `where=tagName`,
  `hasValue=*`, paged with `maxResult` and the `#CONTINUATION_PT` line. Ours
  has **1,189**: 640 controller variables (Modbus node 1) and 549
  display-local variables (names with spaces, protocol `prot2`). The 708 tags
  that read `S_OK` are exactly the 640 controller variables plus 68 display
  variables; none of the 1,059 `E_UNKNOWNTAG` names is listed. So browse is
  a reliable per-pump "does this tag exist" check. `hasValue` is a prefix
  pattern.
- **`browse … returnObject=true`** returns each tag's definition:
  `resourceLocator` (`prot1://1?HREG?500083?short` = holding register 500083,
  signed 16-bit), `refreshTime`, `accessMode` and `active`. Areas: OUTP 311
  coils, HREG 294 holding registers, IREG 22 input registers, INP 13 discrete
  inputs; types `boolean` and `short`.
- **`accessMode` is useless:** READ-WRITE for all 1,189, including sensors.
  The register area is informative: **IREG and INP are physically read-only**.
  OUTP and HREG hold both settings and status (e.g. `2_JE_ALARM` is a coil).
- **No units, ranges or scaling anywhere in the API.** `readTags` has no
  `LIMITS` option (the bits are decoded from the quality integer, always
  192 = good). `getProperties` reads display properties, not tag metadata
  (its `propertymap.xml` does not exist on ours).
- **The register address usually reveals the scale:** across all 177
  controller tags that have manufacturer metadata, every ×10 value is at
  `5xxxxx` and every ×1 integer or enum at `7xxxxx`, with no exception.
  Outside that set it is only a hint: the mixing valve position
  (`2_Odstotki_odprtosti_MPn`) sits at `7xxxxx`, yet the app shows its raw
  90 as "9.0%".

**Design consequences.** Types, units, ranges and enum maps come from
`research/moja_orca_catalog.json` (the manufacturer's metadata) and the
catalog. Unit tests check: scale ×10 ⇔ address `5xxxxx`; nothing writable on
IREG/INP; every catalog tag exists in `tag_registers.json`.

**Evidence:** `captures/2026-10-31_research/session1/S1-13…22`,
`captures/2026-11-01_research/meta/`, `research/tag_registers.json`.
**Confidence:** high.

## R3. Device identity

**Answer.** No stable hardware ID is available through the allowed
endpoints. `getTCPIPSettings` returns 5 address lines (address, netmask and
similar) and no MAC; `getPLCStatus` says `PROGRAM_NOT_LOADED` (the display's
unused soft PLC); no tag holds a serial number or MAC.

**Design consequences.** As `PLAN.md` §7.3 provides: entity unique IDs use
the config entry ID as their base, and the config entry's unique ID is the
host. If DHCP discovery is added (R13), the MAC it provides can become the
config entry's unique ID for discovered entries.

**Evidence:** `S1-05`, `S1-06`, fixtures. **Confidence:** high.

## R4. Alarms

**Answer.**
- **The pump's alarms are controller tags; the display's alarm system is not
  used for them.** Its only IDAL alarm, "Alarm1", is a helper that resets
  `2_Legionela_Cikel` (`alarms.xml`, `browse where=alarmName`). `readAlarms`
  works (`#Alarm1\tS_OK\nNOT_TRIGGERED\tNOT_TRIGGERED\t1\t<ISO time>`) but is
  irrelevant. `readEvent` archives (`eventconfig.xml`: `AlarmBuffer1`,
  `AuditTrail`, `Limite GUMBI`) only cover display alarms, so **there is no
  pump alarm history**.
- **Alarm code and texts:** `2_Vrsta_alarma` (input register, read-only) holds
  the active alarm code. The display's alarm page (`Page109 - Kopija.jmx`)
  shows the text, and shows the RESET button only while `2_JE_ALARM` is set.
  Full table in 7 languages: `research/alarm_texts.json`.

  | Code | English (display) | Slovenian (display) | Probable per-alarm tag |
  |---|---|---|---|
  | 0 | (no alarm) | | |
  | 1 | Error outdoor unit | Napaka zunanje enote | `2_Alarm_skupna_napaka` |
  | 2 | Too high flow temp. HC1 | Previsoka temp. vtoka OK1 | `2_Alarm_Talno` |
  | 3 | Too high flow temp. HC2 | Previsoka temp. vtoka OK2 | `2_Alarm_Talno_VF2` |
  | 4 | No flow | Ni pretoka | `2_Alarm_ni_pretoka` |
  | 5 | Flow switch failure | Okvara pretočnega stikala | `2_Alarm_pretocno_stikalo` |
  | 6 | Too low temp. HP | Prenizka temp. topl. črpalke | `2_Alarm_prenizka_temp_TC` |

  The user's two past alarms are codes 4 and 5 ("Napaka senzorja pretoka" is
  the flow switch failure).
- **Flags:** `2_JE_ALARM` (any alarm, coil), `2_NI_ALARMA` (its inverse).
  Newer firmware adds `2_NAPAKA` and room-sensor alarms `2_Alarm_RF1…3`
  (`E_UNKNOWNTAG` on ours).
- **Reset:** `2_Reset_ALARMA_iz_PGDT`, the display's RESET button (writable
  coil). "No flow" clears itself 30 s after flow returns (manual, B); which
  alarms need a reset is not documented. Writing the reset waits for Phase 6.

**Design consequences.** Alarm entities read the tags above: a problem
binary sensor (`2_JE_ALARM`), an enum sensor with the translated text of
`2_Vrsta_alarma` (unknown code → "Unknown alarm (code N)"), per-alarm binary
sensors, and an event entity that fires on changes the coordinator observes.
History is HA's recorder. Tested with emulator scenarios; a real alarm is
never provoked.

**Evidence:** `S1-10…12`, `captures/readfile/`, `research/alarm_texts.json`.
**Confidence:** high for codes and texts; medium for the code → per-alarm
tag column (by name, not observed).

## R5. Firmware and model

**Answer.**
- Controller program: `2_Verzija_programa_LETO/MESEC/DAN/ZAPOREDJE`. Ours:
  **build 61 of 2016-12-12**; duo: build 89 (2020); mono: build 103 (2022).
  Firmware explains most tag differences (1,059 unknown tags on ours).
- No tag names the model (Duo / Mono, size). Available: controller type
  (`2_Izbira_mPC_pCO3` = 1: µPC), outdoor unit make
  (`2_Izbira_Mitsubishi_Fujitsu`: 1 = Mitsubishi; mono reads 10, unknown),
  commissioning date (`2_Dan/Mesec/Leto_ZAGONA`).
- The display runs the "IDAL HTTP daemon, ABYSS 0.4" and a JMobile HMI
  project with 7 UI languages (EN, SI, DE, FR, HR, LT, SK).

**Design consequences.** Device info: manufacturer "Orca Energija", model
"Heat pump" (plus the outdoor unit make where known), `sw_version` e.g.
"61 (2016-12-12)". Features are detected per tag, never per firmware build.

**Evidence:** fixtures, A §2.15. **Confidence:** high.

## R6. Topology signals

**Answer** (A §3, three pumps):
- **Schema number `2_Shema`** decoded with the 45 `wiring_diagrams` gives the
  circuit type per slot (MK/DK), DHW and solar. **`2_Shema_ZALOG`** adds the
  buffer (mono has a buffer although schema 7's name has none).
  **`2_PogojPGDT_Shema_OK1/OK2`** confirm slots 1 and 2 (1 even when the
  circuit is switched off). No slot-3 variant exists.
- **Room sensor present:** `2_PogojPGDT_Shema_in_tipalo_OKn` = 1, agreeing
  with a room temperature ≠ -9999 and with `2_Tipalo_RF*` on all three pumps.
- **Do not use:** `2_Shema_DK1/DK2` (missing on the newest firmware),
  `2_Tipalo_KF`/`2_Tipalo_VF2` (per-input enable flags that contradict the
  hardware on two pumps), `2_Sobni_*` (sensor type, set to NTC on ours
  without any sensor). `…_in_Upor_*` equals element-present everywhere,
  `…_in_Servisni_*` is 0 everywhere: ignore both.
- **Electric heater stages and additional source:** settings in A §2.9.
- **Cooling capability:** no tag says "this pump can cool". The circuit mode
  enums offer cooling on every schema; whether cooling is configured shows
  in the mode values and the cooling regulation tags.

**Design consequences.** Topology = schema table + `2_Shema_ZALOG` + the OK
flags, with an element present only when its signals were read and agree;
"not received" never means absent. Options flow overrides stay for repurposed
inputs (#30).

**Confidence:** high for the schema and room sensor; low for cooling.

## R7. Tag semantics per element

**Answer.** `research/catalog_draft.md` §2 (253 rows, 645 of our 708
readable tags), with these live additions:
- **Timers** are fully decoded: 5 programmes × 3 ranges, each
  `2_TIMER_<p>_{Ura|Minute}_{ON|OFF}_<r>` plus seven weekday flags; a range
  without days is inactive. Selection per consumer: `2_Izbira_TIMERJA_MK1/
  MK2/MK3/SV/ZALOG/TISJE` (0 = 24 h, 1–5 = programme).
- **Circuit 3 is DK3 with irregular names** (`*_DK3`, `2_IME_MK3`,
  `2_Izbira_TIMERJA_MK3`). Solar and DK3 share output P3 (`2_Vklop_C3`); no
  schema has both, which is what confused the old integration (#39).
- **Heat pump:** `2_Poti1` = HP water temperature (not "gas"),
  `2_Izrac_temp_TC` = HP target, `2_PRIKAZ_Reg_temp_vode` = **outdoor unit
  power in % ×10** (0 when off, 15.0 % while heating), `2_Preklop_PV1` = 3-way
  valve (1 = DHW), `2_Vklop_C0` = HP circulation pump, `2_Rezim_delov_TC`
  = operating state (0 idle, 1 heating observed; 2 cooling, 3 defrost per
  the old config, unconfirmed).
- **DHW:** the current DHW setpoint is not readable on our firmware
  (`2_Temp_zelena_SV` unknown here); it follows from the DHW timer (higher vs
  lower temperature).

**Confidence:** see the catalog's per-row levels.

## R8. Which setpoints act per regulation mode

**Answer.**
- **Constant temperature (mode 4, ours), confirmed live.** While the circuit's
  timer is on, the heat pump target equals **`2_Max_VF_MKn`** (Sun 09:36,
  programme 2 08:00–18:00: target 28.0 = max flow 28.0, circuit pump and HP
  pump on, operating state heating, valve on space heating). Outside the
  timer, with the low-regime action "OFF" (`2_Ponoci_min_temp_IZKLOP_MKn` =
  0), the circuit stops: target 9.0 (no demand), pump off (Sat 20:24). Same
  at the two app snapshots (A §4).
- With the low-regime action "LOWER TEMPERATURE" (1), `2_Min_VF_MKn` is
  presumably the setpoint. Unverified: it would need a write (Phase 6).
- The required room temperature (`2_Zahtevana_RF_MK_n`) still switches
  between the day and night setpoints with the timer (22.0 → 22.5), but it
  has no effect without a room sensor in constant mode.
- **Room setpoints act only** with a room sensor and regulation by room or
  room + outdoor temperature (manual, B: Touch p. 5).
- Outdoor regulation follows the heating curve (base curve + parallel shift +
  slope, pivot at +5 °C outdoor; B, Duo p. 44).

**Design consequences.** On a constant-temperature circuit the user controls
the **flow setpoint** = `2_Max_VF_MKn` (heating) and its cooling
counterpart: a number entity named as the flow setpoint on the circuit
device, and a climate entity with HVAC modes only. Room-temperature targets
appear only with a room sensor and room-based regulation.

**Evidence:** `tests/fixtures/dumps/schema23_*` (both),
`captures/2026-11-01_research/snapshot/`. **Confidence:** high for
constant mode with the "off" action; low for "lower temperature".

## R9. Mode semantics

**Answer** (manufacturer enums, `moja_orca_catalog.json`):
- **Circuit mode** `2_Rezim_MKn` / `2_Rezim_DK3`: 1 Heating, 2 Cooling,
  3 Automatic heating/cooling switch, 4 Switch by input ID2, 5 Manual
  switching (slots 1–2 only).
- **Circuit on/off:** `2_MKn_vklop` (`2_DK3_vklop` analogue, A §2.3).
- **Regulation** per circuit, heating `2_Reg_po_RF_AF_KONST_MKn` and cooling
  `…_HL`: 1 room, 2 outdoor, 3 room + outdoor, 4 constant.
- **Low regime action** `2_Ponoci_min_temp_IZKLOP_MKn`: 0 off, 1 lower
  temperature.
- **Global:** system on/off `2_Vklop_Izklop` (coil); operating programme
  `2_Delovanje_MENI`: 0 Normal, 1 Holiday, 2 Party, 3 ECO; quick room mode
  `2_HITRI_Rezim`: 0 Inactive, 1 Off, 2 Heating, 3 Cooling; summer/winter
  switch per circuit (A §2.3).

**Confidence:** high for the enums; medium for how "automatic" and "by input"
modes map to HA (`docs/entity-model.md`).

## R10. Non-volatile memory and write wear

**Answer.** Neither manual says anything (B §12). The controller is a Carel
µPC; such controllers keep parameters in non-volatile memory, whose write
endurance is limited (general knowledge, not verified for this model).
Separately, an out-of-range write **restarted a user's controller**
(orca-energy-ha #20, D K8).

**Design consequences.** Unchanged: never write an unchanged value, number
entities in box mode, refresh after a write, range checks against the
manufacturer's limits, and a README note about frequent automations.
**Confidence:** low (assumption kept on purpose).

## R11. Request limits and reliability

**Answer.**
- **Limit:** the request line plus all headers (the "header block") must fit
  in **4,095 bytes**. 4,095 → complete answer; 4,096 → HTTP 408 in 13 ms;
  4,114 with 109 bytes moved into an extra header → 408, so headers count.
  The server is "IDAL HTTP daemon, ABYSS 0.4" with a 4 KiB buffer (C).
- **Reliability:** 10 passes × 694 tags (50 requests, 6,940 records): 0
  missing, 0 extra, 0 out of order, all HTTP 200. Plus 2 × 1,767 records in
  the first dump. Records always come back in request order.
- **Latency:** 14 ms for 25 tags, 19 ms for 50, 27 ms for 100, 36 ms for
  ~150; a full read of all 694 readable tags is 5 requests.
- One TCP connection per request (`Connection: close`). `client=` is
  ignored. POST with a form body is equivalent to GET (the vendor client's
  method).
- Concurrency was not tested and is not needed (one lock in the client).

**Design consequences.** Batch by the encoded header-block size with a
margin (e.g. 3,900 bytes including the headers aiohttp actually sends),
never by tag count; treat HTTP 408 as a client bug. The stale-value carry
in `PLAN.md` §7.2 stays as protection against network hiccups but no longer
compensates for "flaky" records.

**Evidence:** `captures/2026-10-31_research/session1/` (`results.json`).
**Confidence:** high.

## R12. Enums

**Answer.** A §6: every enum in the manufacturer's metadata, with values;
no value in the three dumps falls outside those maps. Issue #38 came from
the old config's circuit-name map (shifted by one from value 4, missing 3
and 22). Slot 3's circuit name uses a different list in the app for values
≥ 7 (open). New: the alarm code enum (R4). Unknown values must decode to
`None` and be logged once.

**Confidence:** high for the listed enums.

## R13. Network discovery

**Answer.** The display's MAC vendor prefix is **00:0A:5C (Carel)**, read
from this host's ARP cache (full MAC not recorded); a user reported the same
in orca-energy-ha #15. No hostname or mDNS service was found through the
API. A DHCP matcher on the Carel prefix would also match other Carel
devices, so a discovery flow must confirm by logging in and reading
`2_Shema`.

**Design consequences.** Proposed: DHCP discovery on the Carel prefix,
confirmed by login; discovered entries use the MAC as unique ID and update
the host when the IP changes. Manual setup keeps the host as unique ID.
Decision in P3.

**Confidence:** medium (prefix seen on one pump).

## R14. Project files over `cgi/readFile`

**Answer.**
- Works with `MODE=ASCII&PATH=<relative path>`: `workspace/Project/config/
  alarms.xml` on the first try. Answer: `#S_OK`, a size line (it counts CRLF
  line ends; LF is sent), then the content.
- **No directory listing:** a directory path → `#E_FILEOPENFAIL`. A missing
  file → `#E_FILENOTEXIST`.
- Files read: `alarms.xml` (the helper alarm), `Page109.jmx` (circuit 1 timer
  page), **`Page109 - Kopija.jmx` (the ALARM page, with the alarm texts)**,
  `eventconfig.xml` (event archives). `propertymap.xml` does not exist.
  Page numbering matches orca-energy-ha's FTP dump (`menu_to_field.yaml`).
- The pages are JMobile XML with multi-language text tables (L1–L7). They
  could give manufacturer UI labels for more settings, if ever needed.

**Confidence:** high.

## R15. Moja Orca app

Done before Phase 1 (`PLAN.md` §5.4, `research/moja_orca_catalog.json`). It
remains the only source of ranges, units and enum texts.

## Sensitive tags

- No tag value holds a MAC, IP address or serial number.
- 12 tags contain `GESLO` (password), among them `2_Geslo_ZAGON_AAXX/CCXX/
  XXBB/XXDD` (apparently a commissioning password in four parts), and two
  concern codes (`2_Pravilna_koda_za_prvi_zagon`, `2_Reset_KODE_iz_PGDT`;
  0/1 flags on ours). The display also has local variables such as
  `KODA Serviserja …` and `GESLO Enota …`. **Proposal for CP1:** no tag whose
  name contains `GESLO`, `KODA` or `KODE` is ever read by the integration or
  exposed; fixtures redact them. The research tools refuse to read them.

## Write safety evidence

- orca-energy-ha #20: an out-of-range power-limit write (old range 10–100 %;
  the manufacturer says 40–100 % for heating and DHW, 16–100 % for cooling)
  **restarted the controller**. Every write must be range-checked against
  the manufacturer's limits.
- IREG/INP tags are physically read-only; OUTP/HREG writability comes only
  from the catalog.

## Corrections to PLAN.md assumptions

| PLAN.md | Finding |
|---|---|
| §5.1, §7.2: the API drops records at random | No: a deterministic 408 above 4,095 header bytes. Batch by bytes. |
| §5.1, R2: `readTags` may return `LIMITS` (min/max) | No such option; no ranges anywhere in the API. |
| §7.3: alarm history from `readEvent` | Not available: the event archives only hold display alarms. |
| §7.3: unique ID from a hardware ID (R3) | None exists; use the config entry ID (the plan's fallback). |
| §5.2: `2_Tipalo_*` may be topology | They are per-input enable flags; unreliable for topology. |
| §8: compressor power % from `2_PRIKAZ_Reg_temp_vode` (doubted in #33) | Confirmed: outdoor unit power % ×10. |
| R14: main hope for alarm texts | Confirmed: the display's alarm page has them in 7 languages. |
