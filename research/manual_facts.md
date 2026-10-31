# Facts from the Orca manuals (research subagent B)

Offline extraction from the two manufacturer manuals (© Orca Energija d.o.o.).
These are facts in our own words; no passages are copied. Only short UI labels and
menu names are quoted, because they map to display texts and tags.

## How to read this file

- **Citations**
  - "Duo p. N" means PDF page N of `2020-02-01 orca_tc_2020.pdf` (66 pp.). Its printed
    page numbers are mostly PDF page − 3, with some misprints: for example PDF 21 is
    printed "31", and PDFs 40, 42, 43 and 56 are all printed "39".
  - "Touch p. N" means PDF page N of `2020-02-01 orca_tc_un_2020-1.pdf` (35 pp.). Its
    printed page numbers match the PDF page numbers.
- **Confidence markers**
  - **[stated]**: the manual says it directly.
  - **[read from figure]**: taken from a drawing, screenshot or graph.
  - **[inference]**: our conclusion, not said in the manual.
  - **[not in manuals]**: the manuals are silent.
- **Tag hints** (in tables): these come from `research/moja_orca_catalog.json` (label
  match) or `menu_to_field.yaml`, **not from the manuals**. Verify them before use.
- **Bottom line:** both manuals are much thinner on control logic than PLAN.md hoped.
  - The Duo manual is an installation manual. It covers hardware, wiring and
    commissioning, and has no settings chapter.
  - The touch guide is a 35-page how-to for about a dozen user tasks.
  - Neither manual covers these topics:
    - regulation modes, min/max flow, constant mode, low-regime action
    - quiet mode, power limits, screed drying, anti-blocking
    - solar/buffer setpoints, electric-heater delays and thresholds
    - alarm lists, persistence, the web API

---

## 1. Documents

### 1.1 Duo installation, use and maintenance manual (`orca_tc_2020.pdf`)

- **Version and models**
  - The cover gives version "VER 4.1_2019" and the models ORCA DUO 200 and DUO 300
    (SOLAR) (Duo p. 1).
  - The PDF title metadata reads `Montaža_ORCA_DUO_SLO_CPP_V4.1_2019`. "CPP" is also the
    controller's label in the wiring diagram (Duo p. 53).
  - The file is an OCR'd scan, created 2019-03-25.
- **Scope:** safety, water quality, commissioning checklist, dimensions, outdoor-unit
  data, indoor-unit data, piping, refrigerant charge, terminal wiring, heating curves,
  7 hydraulic schemes, controller wiring, DIP switches, room-sensor wiring, outdoor-unit
  base, maintenance and warranty (Duo p. 3 TOC).
- **What it lacks:** there is **no menu or settings chapter**. It mentions a test menu
  and an info menu only in passing (Duo p. 13).
- **Disclaimer:** it states that it covers several device series, so parameters,
  dimensions or pictures may differ from a given unit (Duo p. 2) [stated].
- **Firmware:** the commissioning checklist says to load the newest software version if
  needed (Duo p. 13). It gives no version numbers or firmware differences [stated].

### 1.2 Touch-screen quick guide (`orca_tc_un_2020-1.pdf`)

- **Title and version:** quick guide for operating the ORCA heat pump through the touch
  screen, "MONO & DUO", version "V1_2021" (Touch p. 1).
  - The PDF was created 2021-07-15. The 2020-02-01 date in the file name doesn't match
    the content.
  - Screenshots carry the dates 20.03.2017 (home screen) and 04.03.2021 (programme menu,
    clock), so the touch UI looked the same over roughly 2017–2021 [read from figure].
- **Disclaimer:** the same multi-series disclaimer as the Duo manual (Touch p. 2).
- **Scope:**
  - home screen and quick menus
  - general settings: on/off, language, clock, timer programmes, timer selection
  - hot water: setpoints, legionella programme, electric heaters
  - circuits: setpoints, heating on/off, cooling on/off, curve corrections
  - (Touch p. 3)

### 1.3 Models, outdoor units and differences (R5)

| Item | Fact | Source |
|---|---|---|
| Duo 200 | Indoor unit with integrated 200 L vacuum-enamelled DHW tank, one exchanger coil (1.6 m²), 600×1400×760 mm, 180 kg | Duo p. 6, 30 |
| Duo 300 (solar) | 300 L tank, main coil 2.6 m² plus a second coil 1.3 m² (solar), 600×1840×760 mm, 235 (255) kg | Duo p. 30 |
| Duo 300XL / 300XL SOLAR | Variant used with outdoor unit PUHZ-SHW230YKA (larger refrigerant lines) | Duo p. 15 |
| Common indoor data | Max outlet 60 °C, max pressure 2.5 bar, circulation pump 5–70 W (Wilo Yonos 25/1-8), changeover valve Firšt EMV, SWEP plate exchanger, **controller CAREL, display pGD1 or PGDT**, 12 L heating expansion vessel (24 L optional), 5 L secondary water volume | Duo p. 30, 31, 37 |
| Outdoor units, Mitsubishi Zubadan | PUHZ-SHW80VAA/YAA (8 kW), SHW112VAA/YAA (11.2 kW), SHW140YHA (14 kW), SHW230YKA (23 kW); heating range −25…35 °C outdoor; max water 60 °C | Duo p. 21–24 |
| Outdoor units, Mitsubishi Power Inverter | PUHZ-SW50VKA (5 kW), SW75VAA/YAA (8), SW100VAA/YAA (11.2), SW120VHA/YHA (12), SW160YKA (22), SW200YKA (25); max water 60 °C | Duo p. 25–29 |
| Refrigerant | R410A | Duo p. 7, 21–26 |
| Outdoor-unit interface | Mitsubishi PAC-IF011B(-E) "communication card" in the indoor unit | Duo p. 19, 53, 55 |
| Max outlet vs outdoor temperature | Graphs per family. SHW140/230: about 48 °C below about −16 °C, rising to 60 °C at about −3 °C and above. SHW80/112: about 45 °C below −20 °C, rising to 60 °C at 0 °C and above | Duo p. 21, 22 [read from figure, approximate] |
| Mono vs Duo | The touch guide covers both with one UI (Touch p. 1). **The manuals describe no Mono hardware, no Mono schemes and no Mono/Duo differences** | [not in manuals] |
| Old vs new display | Duo-era units can have a pGD1 (button LCD, "standard display" on controller jack J7) or a PGDT (touch). The schemes show "PGD1 OPTION" | Duo p. 30, 46–53 [read from figure] |

Firmware or version identification beyond "load the newest software" is **not in the
manuals**.

---

## 2. System overview

### 2.1 Indoor-unit components (Duo)

The parts below are named in the photos (Duo p. 19–20) and the unit scheme (Duo p. 32):

- **Electrical:** transformer; controller ("Krmilnik") with an on-board **battery**
  ("Baterija"); communication card (PAC-IF011B); main switch; terminal strips.
- **Electric heater:** heater contactor; stage relays ("Releji za stopnje
  elektro-grelcev"); flow-through electric heater **FEH**.
- **Hydraulics:** plate heat exchanger **PHE**; circulation pump **P0**; filter **F**;
  flow switch **FS**; 3-way changeover valve **CV** (DHW vs space heating); expansion
  vessel **EN**; safety group; shut-off valves.
- **DHW tank:** magnesium anode(s); DHW sensors **TB** (top) and **LB** (bottom).

The Duo 300 has an air pot and two anodes (Duo p. 20).

### 2.2 Sensors and their names

| Manual name | Meaning | Controller input | Type | Likely tag family [inference] |
|---|---|---|---|---|
| OT / OTS | Outdoor temperature sensor, north wall | B1 | NTC 10 kΩ | `AF` (`2_Temp_Zunanja`, `2_Tipalo_AF`, `2_Kalibracija_AF`) |
| HTT | Heat-pump (outlet) temperature, "Temp. TČ" | B3 | NTC 50 kΩ | `2_Poti1` |
| T1 / M1 (+G) | Room sensor or thermostat, circuit 1 | B2 | DPWT, NTC, NC/NO thermostat, or wireless | `RF` |
| T2 / M2 (+G) | Room sensor or thermostat, circuit 2 | B5 | DPWT, NTC or NC/NO thermostat | `RF2` |
| T3 / M3 | Room sensor or thermostat, circuit 3 | B6 | NTC or NC/NO thermostat only | `RF3` |
| TM1 | Flow temperature, mixing circuit 1 **or "system protection"** | B4 | NTC 50 kΩ | `VF1` / `VF` |
| TM2 | Flow temperature, mixing circuit 2 | B10 | NTC 50 kΩ | `VF2` |
| TB | DHW tank top | B8 | NTC 50 kΩ | `BF1` (`2_Kalibracija_BF_1` "…ZGORAJ") |
| LB | DHW tank bottom | B11 | NTC 50 kΩ | `BF2` (`2_Kalibracija_BF_2` "…SPODAJ"); possibly also `2_Tipalo_B11` |
| TZ | Buffer tank (zalogovnik) | B9 | NTC 50 kΩ | `Zalog` (`2_Temp_Zalog`) |
| TS | Solar collector | B7 | NTC 50 kΩ | `KF` (collector) |
| — | B12 | unused in the Duo drawing | — | `2_Tipalo_B12`: meaning unknown |
| FS | Flow switch ("Pretočno stikalo 1") | digital ID1 | contact | `2_Pogoj_maska_pret_stik` |

Sources:

- Terminal labels, sensor types and the "MK1 or system protection" note: Duo p. 41.
- Controller input numbers: Duo p. 53 [read from figure].
- Legend of the hydraulic schemes: Duo p. 45.
- The abbreviations AF, RF, VF, KF and BF **do not appear in the manuals**. They are the
  usual German names (Außen-, Raum-, Vorlauf-, Kollektor-, Boilerfühler), and the catalog
  labels match them.

Notes:

- In the DK1-only schemes, TM1 sits on the flow line of the direct circuit (Duo p. 46–47)
  [read from figure].
  - Together with the "system protection" label, this suggests that TM1 guards a direct
    floor circuit against over-temperature on DK systems.
  - That would fit `2_Alarm_Talno` [inference].
- Room-sensor options by circuit (Duo p. 41, 45):
  - **Circuit 1:** DPWT, NTC, ON/OFF thermostat, or a wireless room sensor (the terminal
    label names wireless for circuit 1 only).
  - **Circuit 2:** DPWT, NTC or ON/OFF thermostat.
  - **Circuit 3:** NTC or ON/OFF thermostat. The legend lists DPWT1/DPWT2 only.
- **th-Tune** (Carel) room unit (Duo p. 56):
  - It connects straight to the controller over a 3-wire serial **Modbus** link (Rx+,
    Rx−, GND) on jack J10, with a separate 24 V supply.
  - The manual doesn't say which circuit it serves or whether its knob changes the
    setpoint [not in manuals].
- **DPWT** (Carel DPWT010000): both DIP switches must be OFF (the 0…1 V output setting)
  for correct operation (Duo p. 55).

### 2.3 Controller I/O (Duo p. 41, 53, 54)

**Digital inputs**

| Input | Meaning |
|---|---|
| ID1 | Flow switch FS |
| ID2 | **HC**: external heating/cooling changeover contact (NC/NO) |
| ID3–ID7 | Signals from the PAC-IF011B outdoor-unit interface |
| ID9 | **PV**: PV-function contact (NC/NO) |
| ID10 | **SR**: external block of the heaters and/or the heat pump |

- **ID3–ID7:** the I/O block diagram lists the outdoor-unit inputs as operation
  ("Delovanje"), **fault ("Napaka")**, compressor, **defrost ("Odtaljevanje")** and
  cooling/heating.
  - ID5 is defrost: commissioning simulates defrost by bridging G0 and ID5 (Duo p. 13).
  - Which of ID3, ID4, ID6 and ID7 carries which signal isn't stated.
- **SR** (Duo p. 41, 53): the terminal text reads as a contact that blocks the HP and/or
  the electric heaters. This is the EVU/utility-block input [inference: matches the
  "EVU" icon on the touch screen].
- The I/O diagram (Duo p. 54) also lists the inputs "Termostat M1", "Sobni termostat DC"
  and "Regulacija dodatnega MK" (control of an additional mixing circuit).

**Analogue outputs**

| Output | Use |
|---|---|
| Y1 | Relay K6 to the PAC-IF interface |
| Y2 | Relay K10/K7; P3 serves solar/DK3 only with relay K7 on Y2 |
| Y3 | 0–10 V heat-pump demand to the PAC-IF ("Regulacija TČ (0–10V)") |
| Y4 | Depends on the solar pump type (see below) |

- **Y4 with an ON/OFF solar pump:** Y4 outputs 10 V **while cooling is active**.
- **Y4 with a 0–10 V solar pump:** Y4 controls the pump speed (wiring on Duo p. 32).

**Relay outputs**

| Output | Use |
|---|---|
| NO1 | MO1, mixing valve 1 open |
| NO3 | MC1, mixing valve 1 close |
| NO2 | Pump P0 |
| NO4 | 3-way changeover valve |
| NO5 | MC2, mixing valve 2 close |
| NO10 | MO2, mixing valve 2 open |
| NO6 | Pump P1 |
| NO9 | Pump P2 |
| NO7 | HP enable to the PAC-IF A3 |
| NO11, NO12, NO8 | Heater stage relays K1, K2, K3 |
| P3 terminal | "Solar **or** DK3" circulation pump |

- The I/O diagram (Duo p. 54) also lists a "Grelni kabel" output, a heating cable. The
  drawing on Duo p. 42 wires the condensate heating cable through a thermostat from the
  outdoor unit.

**Other terminals and ports**

- 230 V output for external consumers, max 5 A (Duo p. 41).
- Optional separate controller supply, L(0)/N(0) (Duo p. 41).
- RS-485-style serial link (Rx/Tx ±, GND) plus 24 V AC to the touch display (Duo p. 42).
- RJ jack J7 for the pGD1 "standard display" (Duo p. 53) [read from figure].

**DK3 and solar share pump output P3** (Duo p. 41, 53). None of the 7 Duo schemes has
both DK3 and solar (Duo p. 46–52). This hardware sharing likely explains the DK3/solar
confusion in issue #39 [inference].

### 2.4 Hydraulic schemes in the Duo manual (Duo p. 45–52)

| Duo manual scheme | Content | Notes [read from figure] |
|---|---|---|
| Duo 1 | DK1 + SV, up to 150 m² | Direct circuit fed by P0, overflow valve, TM1 on the flow line, room sensor DPWT-1/NTC-1/RT-1 |
| Duo 2 | DK1 + SV, over 150 m² | Hydraulic separator HK + pump P1 |
| Duo 3 | MK1 + MK2 + DK3 + SV | HK, manifold. MK1: P1/MV1/TM1. MK2: P2/MV2/TM2. DK3: P3, with RT-3/NTC-3 |
| Duo 4 | MK1 + MK2 + SV + solar | Solar coil in the DHW tank, P3 = solar pump, collector sensor |
| Duo 5 | MK1 + MK2 + SV + boiler ("peč", gas/oil) + solar | External boiler via a changeover valve ahead of HK |
| Duo 6 | MK1 + MK2 + SV + pool (DK3) | P3 feeds the pool heat exchanger; the pool thermostat gives an "external switch on for DC3" |
| Duo 7 | MK1 + MK2 + SV + solar support for heating | Separate solar buffer with TZ sensor feeding the heating side |

- **Warning:** these "Duo 1–7" numbers are the manual's own. They **do not match** the
  controller's `2_Shema` index (45 entries; for example, the duo dump has `2_Shema` = 3
  meaning DK1+SV) [inference from PLAN §5.2 vs Duo p. 45–52].
- **Sizing rules** (Duo p. 31):
  - A buffer of at least 50 L is required with outdoor units above 16 kW heating.
  - A hydraulic separator is required for heated areas above 150 m².
  - A bypass (overflow) valve is required if automatic shut-off valves could close all
    circuits at once.
- **External heat sources** such as solar must keep the exchanger below 0.5 MPa and the
  water below 80 °C (Duo p. 37).

---

## 3. Operating concepts

### 3.1 Home screen (Touch p. 4)

Tiles and indicators [read from figure]:

- **Circuit tiles 1–3:** each shows the room temperature and an ON/OFF badge. A tap opens
  that circuit's quick menu.
- **DHW tile:** shows the DHW temperature and an ON/OFF badge. A tap opens the DHW quick
  menu.
- **Date, time and outdoor temperature:** a tap opens the INFO menu.
- **"TOPLOTNA ČRPALKA" tile:** shows the HP outlet water temperature.
  - The frame colour shows the space mode: red = heating active, blue = cooling active,
    white = off.
  - A tap opens the quick room mode.
- **Programme button:** shows NORMALNO DELOVANJE / ECO / PARTY / POČITNIŠKI REŽIM.
- **Indicators:**
  - "EVU" lights while the utility block is active.
  - "PV" lights while the PV programme is active.
  - Status icons for heating, cooling and defrost.
  - An electric-heater icon with the **number of active heater stages**.
- **Gear icon:** opens the settings menu.

### 3.2 Editing model (Touch p. 4)

- Up/down arrows change a value. "Nazaj" goes to the previous parameter, "Naprej" to the
  next one, and the home icon returns to the home screen.
- After a change, "Shrani" (save) and "Prekliči" (cancel) appear.
  - "Shrani" commits the value; "Prekliči" restores the previous one.
  - So a value on the touch UI takes effect only when it is saved [stated]. Whether a
    remote `writeTags` acts immediately is **not in the manuals**.

### 3.3 Settings menu (Touch p. 7, 11, 16)

- The settings menu is a scrolling list:
  - "SPLOŠNE NASTAVITVE", "OGREVALNI KROG 1", "OGREVALNI KROG 2", "OGREVALNI KROG 3"
  - then "SANITARNA VODA", "SOLAR", "ZALOGOVNIK", "DODATNI VIR"
  - then "INFO", "ČASOVNI PROGRAMI", "PV FUNKCIJA", "TEST NAPRAVE"
- Side icons:
  - a language flag
  - scroll arrows
  - a **wrench for entering the service code**, which unlocks all service settings
  - home

### 3.4 System on/off (Touch p. 8)

"SPLOŠNE NASTAVITVE" → first screen "Aktiviranje sistema": IZKLOP / VKLOP. This switches
the whole heat pump on or off. The guide doesn't say whether DHW or frost protection
stays active when it is off [not in manuals].

### 3.5 Operating programmes (Touch p. 6–7)

| Programme | Effect | Parameter |
|---|---|---|
| NORMALNO DELOVANJE | Runs by the configured timer programmes | — |
| PARTY | Runs on the **higher-regime** settings for a set time, whatever the timer says | "TRAJANJE PARTY REŽIMA", in hours (screenshot: 2 h) |
| ECO | Runs on the **lower-regime** settings for a set time, whatever the timer says | "TRAJANJE ECO REŽIMA", in hours (screenshot: 4 h) |
| POČITNIŠKI REŽIM (holiday) | Runs on the **lower-regime** settings until an end date | "KONEC POČITNIŠKEGA REŽIMA", a date (screenshot: 08.03.2021) |

Open points:

- What happens when the party or ECO time ends (presumably a return to normal), the
  allowed duration ranges, and whether the overrides also act on DHW are **not in the
  manuals**.
- The menu map (`menu_to_field.yaml`) binds these screens to display aliases
  `PARTY_CAS`, `ECO_CAS` and `Pocitniski_DAN`, not to `2_*` tag names. The real tags are
  still unknown.

### 3.6 Quick room mode (Touch p. 6, 23, 25, 28, 31)

Tap the HP tile. The screen "OGREVANJE/HLAJENJE PROSTOROV" with the item "Hitra izbira
prostorskega režima" offers:

| Value | Effect (Touch p. 6) |
|---|---|
| Neaktivna funkcija | The function is off; circuits follow their own heating/cooling settings |
| Hlajenje | All heating circuits off, all cooling circuits on; DHW stays on |
| Ogrevanje | All heating circuits on, all cooling circuits off; DHW stays on |
| Izklop | All heating and cooling circuits off; **DHW stays on** |

- To switch space heating or cooling on through this screen, choose "Ogrevanje" (or
  "Neaktivna funkcija") for heating, or "Hlajenje" for cooling (Touch p. 25, 28).
- **This method does not work when one circuit serves both heating and cooling** (Touch
  p. 25, 28) [stated].
  - The quick mode switches circuits by their configured role. It does not change a
    circuit's own "Režim delovanja" [inference].
  - For a shared circuit, the mode must be set per circuit (§4.2).
- Catalog hint: `2_HITRI_Rezim`, whose enum order is Neaktivna funkcija, Izklop,
  Ogrevanje, Hlajenje.

### 3.7 Summer/winter, seasons and heating/cooling switching

- **Heating/cooling switching** exists in three forms:
  - the quick room mode (§3.6)
  - the per-circuit "Režim delovanja" (§4.2)
  - a hardware contact on input HC/ID2 (Duo p. 41, 53)
- **Automatic summer/winter switching by outdoor temperature is not in the manuals.** The
  catalog has `2_Aktiv_avtom_preklop_*` and `2_Temp_za_preklop_*`.
- **Manual mode ("Ročni preklop") is not in the manuals.** The only "Ročno" (manual) in
  the touch guide is an electric-heater mode (Touch p. 21).
- The DHW electric-heater wiring variants include manual switch-on (Duo p. 42).

---

## 4. Heating circuits (R7, R8, R9)

### 4.1 MK vs DK

- The touch guide's circuit chapter covers "DK1, DK2, DK3, MK1 ter MK2", all shown as
  "OGREVALNI KROG 1/2/3" (Touch p. 22).
  - So slot 1 = DK1 or MK1, slot 2 = DK2 or MK2, slot 3 = DK3 only [stated + inference;
    no MK3 anywhere].
- **MK (mixing circuit)** (Duo p. 41, 48–52, 53):
  - its own pump (P1/P2)
  - a 3-point mixing-valve actuator with separate open and close outputs (MO/MC)
  - a flow sensor (TM1/TM2)
  - a room sensor or thermostat
- **DK (direct circuit)** (Duo p. 46–48):
  - no mixing valve
  - DK1 runs on P0 alone in the small scheme, or on P1 behind a hydraulic separator
  - DK3 uses P3
- **Pump legend:** P1 = pump DK1/MK1, P2 = pump DK2/MK2, P3 = pump DK3/solar (Duo p. 45).

### 4.2 Per-circuit settings shown in the guide

| Screen (path) | Values shown | Source |
|---|---|---|
| Circuit tile → screen 1: "VIŠJA TEMPERATURA" / "NIŽJA TEMPERATURA" (desired room temperature, higher/lower regime) | °C (screenshot 22.0 / 19.0) | Touch p. 5, 22 |
| Circuit tile → screen 2: "VZPOR.KOR.KRIVULJE" / "KOR.NAGIBA KRIVULJE" | 0.0 / 0.0 in the screenshot | Touch p. 5, 33 |
| Circuit tile → screen 3: "IZBIRA ČASOVNEGA PROGRAMA" | "24-urni režim" or programme 1–5 | Touch p. 5, 13 |
| Settings → OGREVALNI KROG n → 1× Naprej: "Aktiviranje" | IZKLOP / VKLOP | Touch p. 24, 26 |
| … → 2× Naprej: "Režim delovanja" | "Ogrevanje", "Hlajenje" shown | Touch p. 26, 29 |
| … → 4× Naprej: "Korekcija vzporednega premika ogrevalne krivulje" | 0.0 | Touch p. 34 |
| … → 5× Naprej: "Korekcija nagiba ogrevalne krivulje" | 0.0 | Touch p. 35 |
| … → 8× Naprej: "Izbira časovnega programa" | "24-urni režim" / "Po časovnem programu 1-5" | Touch p. 14 |

- The other screens in the circuit menu (positions 0, 3, 6, 7) aren't shown or named.
  "Reguliranje ogrevanja po", min/max flow and the low-regime action are probably there,
  but the guide never mentions them [not in manuals].
- **Circuit mode enum:** the guide shows only "Ogrevanje" and "Hlajenje".
  - It doesn't mention "Avtomatski preklop ogr.-hl.", "Preklop preko vhoda ID2" or
    "Ročni preklop" [not in manuals].
  - Wiring gives the meaning of the ID2 option: ID2 is the HC heating/cooling contact
    (Duo p. 41, 53) [inference].
  - What "Ročni preklop" does is **not in the manuals**.
- **Switching a circuit off** with "Aktiviranje" = IZKLOP stops both its heating and its
  cooling (Touch p. 24, 32).
- **Switching cooling on** for a circuit means "Aktiviranje" = VKLOP plus "Režim
  delovanja" = Hlajenje (Touch p. 29).

### 4.3 Regulation modes: which setpoints act (R8)

**What the manuals say (all of it):**

1. **Room setpoints.** The higher and lower desired **room** temperatures can be set only
   when the circuit is regulated by room temperature or by room + outdoor temperature,
   **and** a room sensor is installed for that circuit (Touch p. 5) [stated].
2. **Which room setpoint is active.** The higher-regime room setpoint applies while the
   circuit's timer programme is on or "24-urni režim" is selected. The lower one applies
   otherwise (Touch p. 5, 22) [stated; "programme is on" is our reading of the phrasing].
3. **Heating curve** (Duo p. 44) [stated / read from figure]:
   - **Parallel shift:** the correction moves the whole curve. One step of 0.1 shifts it
     by 0.1 K.
   - **Slope:** the correction changes the curve's value at −10 °C outdoor. The curve
     pivots at +5 °C outdoor, which stays fixed. One step of 0.1 moves the −10 °C point
     by 0.1 K.
   - **Base curves** (two examples, read from the graphs):
     - "TALNO OGREVANJE" (floor): 30 °C flow at +5 °C outdoor, 45 °C at −10 °C.
     - "RADIATORSKO OGREVANJE": 45 °C at +5 °C, 60 °C at −10 °C.
     - Both are straight lines rising about 1 K of flow per 1 K of outdoor drop (for
       example, the floor curve reaches about 55 °C at −20 °C).
     - The two base curves probably correspond to the installation-type setting (catalog
       `2_Talno_Radiatorsko_*`: RADIATORJI / TALNO) [inference].
   - So the curve setpoint is roughly: base(T_out) + shift + slope × (5 − T_out) / 15
     [inference from the pivot description].
   - The section title says "cooling and heating curves", but **only heating curves are
     drawn**. Cooling curves are not in the manuals.
4. **Curve corrections in the quick menu.** The curve corrections are offered in the
   circuit quick menu with no stated conditions (Touch p. 5).

**What the manuals don't say [not in manuals]:**

- the regulation-mode parameter itself ("Reguliranje ogrevanja/hlajenja po": room /
  outdoor / room+outdoor / constant)
- how room + outdoor regulation combines the room error with the curve, and how the room
  setpoint shifts the curve (for example, whether the curve's reference room temperature
  is 20 °C)
- **constant-temperature mode**: no mention at all. The manuals neither confirm nor refute
  that `2_Max_VF_MKn` is the flow setpoint during the timer-on period, or that
  `2_Min_VF_MKn` is the setpoint in the lower regime when the low-regime action is "NIŽJA
  TEMPERATURA". The PLAN §5.4 hypothesis stays open and must be verified live.
- min/max flow temperature limits, and whether they clamp the curve
- the low-regime action ("Delovanje ob preklopu na nižji režim": Izklop / NIŽJA
  TEMPERATURA)
- the cooling setpoints (catalog: min cooling flow, cooling points at +20/+30 °C)

**Without a room sensor:**

- The only statement is fact 1: the room setpoints are settable only when a room sensor
  is installed and the mode uses room temperature.
- That strongly suggests the day/night room setpoints **do not act** in outdoor-only or
  constant mode, or when no room sensor is present [inference]. Whether they still shift
  the curve in outdoor mode is not stated.
- With an **ON/OFF room thermostat** instead of a sensor (Duo p. 41, 45), the controller
  gets only a demand contact, so there's no room temperature to show [inference].

**Room-sensor types** (Duo p. 41, 45, 55, 56): Carel DPWT (active, 0…1 V), NTC
(passive), ON/OFF room thermostat (NC/NO), wireless room sensor (circuit 1 terminal
label), Carel th-Tune (Modbus). The catalog enum also has "Brezžično ORCA" (wireless
ORCA). The manuals don't describe how each type changes the regulation.

### 4.4 Mixing valve, pumps, floor protection, boost, defrost

- **Mixing valves** are 3-point actuators with separate open and close outputs per MK
  circuit (Duo p. 41, 53).
  - Valve run time, control behaviour and the opening % aren't described [not in
    manuals]. The catalog has a 90° rotation time of 10–600 s.
- **During defrost** (Duo p. 13) [stated]:
  - **all connected circulation pumps run** (except the solar collector pump)
  - **the mixing valve opens**
  - This explains pump and valve activity seen while the outdoor unit defrosts.
- **Floor protection:** TM1's terminal label says "MK1 or system protection" (Duo p. 41),
  and TM1 sits on the DK1 flow line in the DK schemes (Duo p. 46–47) [read from figure].
  - No over-temperature threshold or alarm behaviour is stated [not in manuals].
- **"HP boost for a mixing circuit"** (catalog `2_Povec_temp_TC_pri_MK*`): not in the
  manuals.
- **Pump run-on delays and anti-blocking:** not in the manuals. Commissioning only says
  to start blocked pumps by hand (Duo p. 13).

---

## 5. Timer programmes

- **Five programmes** ("ČASOVNI PROGRAM 1" … "5"), each with **up to three intervals**
  (Touch p. 11) [stated].
- **Each interval** has an on time "VKLOP n" (HH:MM), an off time "IZKLOP n" (HH:MM) and
  weekday toggles PON TOR SRE ČET PET SOB NED (Touch p. 11) [read from figure].
- **The programme overview** lists each interval as "07:00 - 23:00 PON TOR SRE ČET PET".
  Unused intervals show "00:00 - 00:00" (Touch p. 11) [read from figure].
- **Where programmes are set:** settings → scroll → "ČASOVNI PROGRAMI" (Touch p. 11–12).
- **Assignment:** each circuit (1–3) and DHW picks "24-urni režim" or "Po časovnem
  programu 1-5" (Touch p. 5–6, 13–14).
  - Assigning programmes to **quiet mode or the buffer is not in the manuals** (the
    catalog has `2_Izbira_TIMERJA_TISJE` and `_ZALOG`).
- **"24-urni režim"** keeps the higher regime active all the time, because the higher
  regime applies when a programme is on *or* 24-hour operation is chosen (Touch p. 5, 15,
  22) [stated + inference].
- **Outside an interval** the lower regime applies:
  - lower room setpoint for circuits (Touch p. 5, 22)
  - lower DHW temperature for DHW (Touch p. 15)
  - Whether a circuit then switches **off** or runs at a **lower temperature** (the
    "Izklop / NIŽJA TEMPERATURA" choice) is **not in the manuals**.
- **Overrides:** PARTY forces the higher regime, and ECO and holiday force the lower
  regime, regardless of the timer (Touch p. 6–7).
- **Not stated:** minute granularity, intervals crossing midnight, overlapping intervals,
  and what a programme with no days ticked means.

---

## 6. Hot water (SV)

- **Two setpoints** (Touch p. 5, 15–17):
  - "VIŠJA TEMPERATURA" / "Želena višja temperatura sanitarne vode" applies in the higher
    regime (timer on or 24-hour).
  - "NIŽJA TEMPERATURA" / "Želena nižja temperatura sanitarne vode" applies outside it.
  - Screenshot values: 47.0 °C higher; 35.0 °C (Touch p. 5, 15) and 8.0 °C (Touch p. 17)
    lower. These are **examples, not stated defaults**.
- **Path:** settings → SANITARNA VODA → 1× / 2× Naprej (Touch p. 16–17), or the DHW tile
  quick menu (Touch p. 15).
- **Timer:** the DHW quick menu's second screen is "IZBIRA ČASOVNEGA PROGRAMA" (24-urni
  režim / programme 1–5) (Touch p. 6).
- **Legionella programme** (settings → SANITARNA VODA, 4×–8× Naprej) (Touch p. 18–20):

  | Screen | Values |
  |---|---|
  | "Aktiviranje protilegionelnega programa" | IZKLOP / VKLOP |
  | "Želena temperatura protilegionelnega programa" | screenshot 65.0 °C |
  | "Dan pričetka delovanja protilegionelnega programa" | weekday (screenshot "Ponedeljek") |
  | "Ura pričetka delovanja protilegionelnega programa" | hour (screenshot "0:00") |
  | "Cikel delovanja protilegionelnega programa" | every week / every 2 weeks / once a month / once every 2 months (screenshot "Tedenski") |

  The temperature range isn't stated (the catalog gives 65–70 °C).
- **Safety:** water above 50 °C can scald. Take extra care with settings above 50 °C and
  while the legionella programme runs (Duo p. 5).
- **Unnamed DHW menu positions:** the screens at positions 0 and 3 aren't named. They are
  probably DHW enable and the on-difference [inference].
- **Not in the manuals:**
  - the on-difference ("Diferenca vklopa")
  - DHW priority
  - HP boost for DHW
  - whether the electric heater helps reach the legionella temperature
  - the DHW sensor used for control (top TB vs bottom LB)
- **Changeover:** the 3-way valve CV switches the HP output between DHW ("NA OGREVANJE
  SV") and space heating ("NA OGREVANJE PROSTOROV") (Duo p. 13, 32), so DHW and space
  heating can't run at once [inference].
- **External DHW electric heater** (a heater inside the tank) can be wired three ways
  (Duo p. 42):
  - **V1:** manual switch-on, separate supply.
  - **V2:** switched by the controller through relay KR3, separate supply.
  - **V3:** manual or automatic.
  - Wiring for V2/V3 is on Duo p. 43.

---

## 7. Solar, buffer tank (ZALOG), cooling

### Solar

- **Settings:** the menu entry "SOLAR" exists (Touch p. 16). **No solar settings are
  documented** [not in manuals]: no setpoints, no differences, no collector limits.
- **Hardware** (Duo p. 32, 53):
  - collector sensor TS (B7)
  - pump on P3: ON/OFF, or 0–10 V via Y4/GND
  - The Duo 300 SOLAR has a second tank coil of 1.3 m² (Duo p. 30).
- **Heat-source limits:** solar or other external sources must not push the exchanger
  above 0.5 MPa or the water above 80 °C (Duo p. 37).

### Buffer tank (ZALOG)

- **Settings:** the menu entry "ZALOGOVNIK" exists (Touch p. 16). **No buffer settings or
  logic are documented** [not in manuals]. In particular, the manuals say nothing about
  separate heating and cooling buffer setpoints (#39).
- **Hardware:** buffer sensor TZ (B9) (Duo p. 41, 53). A buffer of at least 50 L is
  required for outdoor units above 16 kW (Duo p. 31). Duo 7 uses a solar buffer for
  heating support (Duo p. 52).

### Cooling

- **Glycol:** if cooling with a desired outlet water below 12 °C, the system must be
  filled with glycol (frost protection to at least −10 °C), at most 30 % glycol (Duo
  p. 13) [stated].
- **Insulation:** all water piping must be insulated against condensation during cooling.
  Above 30 °C and 80 % RH, use at least 20 mm of insulation (Duo p. 36).
- **Indoor-unit room conditions:** 5–35 °C in cooling and 5–30 °C in heating, at most
  85 % RH (Duo p. 34).
- **Outdoor cooling operating ranges** (outdoor air temperature, Duo p. 21–26):
  - Zubadan SHW140/230: −15…43 °C
  - SHW80/112 and SW75/100: −15…46 °C
  - SW50/120/160/200: −5…46 °C
- **Cooling-active signal:** Y4 gives 10 V while cooling is active if the solar pump is an
  ON/OFF type (Duo p. 53).
- **Not in the manuals:** dew-point protection, minimum cooling flow temperature and
  cooling curves.

---

## 8. Additional source / electric heater

- **Built-in heater** (Duo p. 19–20, 43, 53):
  - The flow-through electric heater FEH has **three stages**: elements HT1–HT3 switched
    by stage relays K1–K3 (controller outputs NO11, NO12, NO8) and a common contactor
    KM5.
  - The KM5 coil is wired in series with a **94 °C thermal fuse (FU)** and an **80 °C
    overheat thermostat (OTH)**, a hardware cut-out with no software involvement [read
    from figure].
- **Stage size:** the manual states no kW per stage.
  - The outdoor-unit tables say that for parallel operation of the HP and the built-in
    heater, the fuses must be raised by 13 A per phase (Duo p. 21–26).
  - That is consistent with about 9 kW three-phase, so 3 kW per stage, matching the
    catalog's 3/6/9 kW [inference].
- **Mode** (Touch p. 21):
  - Settings → page 2 → "DODATNI VIR". This menu **asks for a password**: a fixed 4-digit
    user code printed in the guide, not reproduced here.
  - The screen "Način vklopa električnih grelcev" (header "ELEKTRIČNI GRELEC") offers
    Avtomatsko / Ročno / Izklop.
  - What "Ročno" (manual) does is not explained.
- **Cold start** (Duo p. 13): first heat the water to at least 20 °C with the electric
  heaters, then switch them off and start the HP.
- **Display:** the home screen shows a heater icon with the number of active stages
  (Touch p. 4).
- **External additional source** (Duo p. 43): a potential-free relay contact can switch
  an external additional source; the manual describes rewiring a relay for this.
- **External block:** input SR blocks the HP and/or the heaters (Duo p. 41, 53).
- **Not in the manuals:**
  - number of active stages
  - per-stage delays
  - outdoor-temperature thresholds
  - parallel operation settings
  - source choice (heater / external / both)
  - emergency mode

---

## 9. Quiet mode, power limits, PV, EVU, screed drying, anti-blocking

| Topic | What the manuals say | Source |
|---|---|---|
| Quiet mode | Nothing | [not in manuals] |
| Power limits | Nothing about settings. Hardware: the controller drives the outdoor unit with a 0–10 V demand (Y3 → PAC-IF) and an enable relay, so a "% power" limit probably caps that signal | Duo p. 53, 54 [inference] |
| PV | Menu entry "PV FUNKCIJA"; home-screen "PV" indicator while the PV programme is active; NC/NO input contact "PV" on ID9 activates the PV function. What it does (for example raising setpoints) isn't described | Touch p. 4, 11; Duo p. 41, 53 |
| EVU / utility block | Home-screen "EVU" indicator; input SR (ID10) is an external block of the heaters and/or HP | Touch p. 4; Duo p. 41, 53 |
| Screed drying | Nothing | [not in manuals] |
| Anti-blocking programme | Nothing; commissioning only says to free blocked pumps by hand | Duo p. 13 |
| Test menu | "TEST NAPRAVE" in settings (Touch p. 11); "TESTNI VKLOPI" in the basic menu is used at commissioning to check each component (Duo p. 13) | Touch p. 11; Duo p. 13 |
| Info menu | "INFO" (touch) / "INFORMACIJE": component states | Touch p. 4, 11; Duo p. 13 |

---

## 10. Alarms (R4)

**The manuals contain no alarm list, no alarm code table, no alarm reset procedure and no
alarm screen description.** The touch guide doesn't mention alarms at all; its home-screen
callouts show no alarm indicator (Touch p. 4).

Every alarm-related fact in the manuals:

| Display text | Meaning / cause | Reset | Source |
|---|---|---|---|
| "NI PRETOKA" (no flow) | The flow switch FS (input ID1) detects no water flow. Causes named: flow below the nominal/minimum flow of the outdoor unit, closed floor-heating or radiator valves, or a closed valve on the secondary side. The alarm appears **5 s** after flow stops. On the Duo, closing a valve on the heating side triggers it only while the changeover valve is in the space-heating position | **Self-resetting:** once flow is back, the alarm clears itself **after 30 s** and the unit carries on normally. No manual reset needed | Duo p. 13 (stated twice: commissioning flow check and flow-switch test) |
| "Napaka senzorja pretoka" (flow sensor fault) | **Not in the manuals.** The flow device is a switch ("Pretočno stikalo", "Stikalo pretoka"), not an analogue sensor (Duo p. 19–20, 32, 53). Hypothesis only: a plausibility fault of the switch (for example flow reported while P0 is off) [inference, unverified] | Unknown | — |
| Outdoor-unit fault | The controller receives a "Napaka" (fault) digital input from the Mitsubishi interface PAC-IF011B (one of ID3/ID4/ID6/ID7). The manuals don't say how it is shown. A candidate for `2_Alarm_skupna_napaka` (common fault) [inference] | Unknown | Duo p. 53, 54 |
| Heater over-temperature | Hardware only: a 94 °C thermal fuse and an 80 °C overheat thermostat in the heater contactor circuit. No display text is stated | A thermal fuse doesn't reset (service part); OTH behaviour isn't stated | Duo p. 43 [read from figure] |
| Compressor issues from wrong refrigerant charge | SHW230 with a short line: excess charge can cause compressor pre-heating or mechanical locking. A Mitsubishi-side condition, no Orca text | — | Duo p. 40 |

No manual mentions these PLAN alarm tags or their topics: `2_Alarm_prenizka_temp_TC` (HP
temperature too low), `_Talno` (floor over-temperature; see the TM1 note in §4.4), `_RF1..3`
(room-sensor faults), `2_Cas_zakasn_ALARM_RF1`, or the reset tags. Their texts must come
from `readAlarms` or R14.

---

## 11. Parameters and ranges

**Level** key:

- **U**: user. The guide reaches it without any code.
- **P**: behind the user password (DODATNI VIR).
- **S**: service code (the wrench). Nothing below is service-level in the manuals; service
  settings exist but aren't listed (Touch p. 7).

The manuals state almost no ranges and no defaults. "Screenshot" values are examples. The
range column gives the **catalog** range for orientation; the catalog isn't a manual
source.

| # | Menu path (SI labels) | Meaning (EN) | Values / range | Unit | Level | Source | Tag hint (catalog/menu map, verify) |
|---|---|---|---|---|---|---|---|
| 1 | SPLOŠNE NASTAVITVE → "Aktiviranje sistema" | System on/off | IZKLOP / VKLOP | — | U | Touch p. 8 | `2_Vklop_Izklop` |
| 2 | SPLOŠNE NASTAVITVE → "Nastavitev ure" | Controller time | HH:MM | — | U | Touch p. 10 | `2_CURRENT_HOUR`, `_MINUTE` |
| 3 | SPLOŠNE NASTAVITVE → "Nastavitev datuma" | Controller date | DD.MM.YYYY | — | U | Touch p. 10 | `2_CURRENT_DAY`, `_MONTH`, `_YEAR` (0–99) |
| 4 | Flag icon | UI language | EN, PL, IT, FR, SL, DE, HR, SK | — | U | Touch p. 9 | (display-local?) |
| 5 | HP tile → "Hitra izbira prostorskega režima" | Quick room mode | Neaktivna funkcija / Hlajenje / Ogrevanje / Izklop | — | U | Touch p. 6, 23 | `2_HITRI_Rezim` |
| 6 | Programme button | Operating programme | NORMALNO DELOVANJE / PARTY / ECO / POČITNIŠKI REŽIM | — | U | Touch p. 6–7 | `2_Delovanje_MENI` |
| 7 | PARTY → "TRAJANJE PARTY REŽIMA" | Party duration (higher regime) | screenshot 2; range not stated | h | U | Touch p. 6 | alias `PARTY_CAS` (tag unknown) |
| 8 | ECO → "TRAJANJE ECO REŽIMA" | ECO duration (lower regime) | screenshot 4; range not stated | h | U | Touch p. 7 | alias `ECO_CAS` (tag unknown) |
| 9 | POČITNIŠKI REŽIM → "KONEC POČITNIŠKEGA REŽIMA" | Holiday end date (lower regime until then) | date | — | U | Touch p. 7 | alias `Pocitniski_DAN` (tag unknown) |
| 10 | Circuit tile → "VIŠJA TEMPERATURA" | Desired room temp., higher regime (day) | screenshot 22.0; only with room / room+outdoor regulation and a room sensor | °C | U | Touch p. 5, 22 | alias `MK1_Temp DNEVNA` (tag unknown) |
| 11 | Circuit tile → "NIŽJA TEMPERATURA" | Desired room temp., lower regime (night) | screenshot 19.0; same condition | °C | U | Touch p. 5, 22 | alias `MK1_Temp NOCNA` (tag unknown) |
| 12 | Circuit tile → "VZPOR.KOR.KRIVULJE"; OGREVALNI KROG n → 4× "Korekcija vzporednega premika ogrevalne krivulje" | Heating-curve parallel shift | step 0.1 = 0.1 K over the whole curve; screenshot 0.0; catalog −15.0…+15.0 | K | U | Touch p. 5, 33–34; Duo p. 44 | `2_Zamik_krivulje_MK1/MK2/DK3` |
| 13 | Circuit tile → "KOR.NAGIBA KRIVULJE"; OGREVALNI KROG n → 5× "Korekcija nagiba ogrevalne krivulje" | Heating-curve slope correction | step 0.1 = 0.1 K at −10 °C outdoor, pivot +5 °C; screenshot 0.0; catalog −15.0…+15.0 | K | U | Touch p. 5, 35; Duo p. 44 | `2_Nagib_krivulje_MK1/MK2/DK3` |
| 14 | Circuit tile screen 3; OGREVALNI KROG n → 8× "Izbira časovnega programa" | Circuit timer | 24-urni režim / Po časovnem programu 1–5 | — | U | Touch p. 5, 13–14 | `2_Izbira_TIMERJA_MK1/MK2/MK3` |
| 15 | OGREVALNI KROG n → 1× "Aktiviranje" | Circuit enable | IZKLOP / VKLOP | — | U | Touch p. 24, 26, 32 | `2_MK1_vklop`, `2_MK2_vklop`, `2_DK3_vklop` |
| 16 | OGREVALNI KROG n → 2× "Režim delovanja" | Circuit mode | Ogrevanje / Hlajenje shown; other values not documented | — | U | Touch p. 26, 29 | `2_Rezim_MK1/MK2/DK3` |
| 17 | DHW tile / SANITARNA VODA → 1× "Želena višja temperatura sanitarne vode" | DHW setpoint, higher regime | screenshot 47.0; catalog 8.0–55.0 | °C | U | Touch p. 5, 15–16 | `2_Temp_vode_sanitarna` |
| 18 | DHW tile / SANITARNA VODA → 2× "Želena nižja temperatura sanitarne vode" | DHW setpoint, lower regime | screenshots 35.0 and 8.0; catalog 8.0–55.0 | °C | U | Touch p. 5, 15, 17 | `2_Temp_vode_sanitarna_NIZJA` |
| 19 | DHW tile screen 2 "IZBIRA ČASOVNEGA PROGRAMA" | DHW timer | 24-urni režim / programme 1–5 | — | U | Touch p. 6 | `2_Izbira_TIMERJA_SV` |
| 20 | SANITARNA VODA → 4× "Aktiviranje protilegionelnega programa" | Legionella enable | IZKLOP / VKLOP | — | U | Touch p. 18 | `2_Legionela_vklop` |
| 21 | … 5× "Želena temperatura protilegionelnega programa" | Legionella temperature | screenshot 65.0; catalog 65.0–70.0 | °C | U | Touch p. 19 | `2_Temperatura_legionela` |
| 22 | … 6× "Dan pričetka delovanja protilegionelnega programa" | Legionella weekday | Monday … Sunday (screenshot Ponedeljek) | — | U | Touch p. 19 | `2_On_Dan_Legionella` |
| 23 | … 7× "Ura pričetka delovanja protilegionelnega programa" | Legionella start hour | screenshot 0:00; catalog 0–23 | h | U | Touch p. 19 | `2_On_Ura_Legionella` |
| 24 | … 8× "Cikel delovanja protilegionelnega programa" | Legionella cycle | weekly / 2-weekly / monthly / 2-monthly | — | U | Touch p. 20 | `2_Legionela_Cikel` |
| 25 | DODATNI VIR (password) → "Način vklopa električnih grelcev" | Electric-heater mode | Avtomatsko / Ročno / Izklop | — | P | Touch p. 21 | `2_Vklop_Elektro_Grelci` |
| 26 | ČASOVNI PROGRAMI → "ČASOVNI PROGRAM 1–5" → interval 1–3 | Timer interval: "VKLOP n" / "IZKLOP n" times + weekdays PON…NED | HH:MM; 7 day toggles; unused = 00:00–00:00 | — | U | Touch p. 11–12 | `2_TIMER_<p>_<day>_<k>` + on/off hour/minute tags |
| 27 | Wrench icon | Service code entry (unlocks all service settings) | code | — | — | Touch p. 7 | never expose (`GESLO` tags) |
| 28 | Menu entries without documented content: "SOLAR", "ZALOGOVNIK", "PV FUNKCIJA", "INFO", "TEST NAPRAVE" | — | — | — | ? | Touch p. 11, 16 | — |

Installer-only hardware settings in the Duo manual (not software parameters):

- PAC-IF011B DIP switches SW1–SW3, set to a fixed pattern shown in a figure (Duo p. 55)
- outdoor-unit DIP switches, set per the label inside its cover (Duo p. 55)
- DPWT DIP switches, both OFF (Duo p. 55)

---

## 12. Persistence (R10)

- **Save step:** on the touch UI, a changed value takes effect only after "Shrani"
  (Touch p. 4).
- **Non-volatile memory, write limits, power-loss behaviour: nothing** [not in manuals].
  Nothing in either manual says where settings are stored, how many writes the memory
  allows, or what happens to settings, clock or running programmes after a power cut.
- **Clock:**
  - Time and date are set by hand in SPLOŠNE NASTAVITVE (Touch p. 10). There's no
    mention of NTP, time zones or daylight-saving changes.
  - The controller board carries a **battery** ("Baterija" in the component photos, Duo
    p. 19–20), probably the backup for the controller's real-time clock [inference; the
    manual doesn't say what it powers].
- **Controller brand:** CAREL (Duo p. 30), labelled "CPP" in the wiring (Duo p. 53).
  - Carel's own pCO-family documentation would be the place to check permanent-memory
    write limits [inference; model not named in the manuals].
  - Until then, follow PLAN §7.2 and assume writes are wear-limited.
- **Separate controller supply:** an optional separate supply exists (Duo p. 41). That
  would keep the controller running while the main supply is cut, but the manual doesn't
  say why it is offered.

---

## 13. Network and remote access

- **LAN is on the touch display:** a twisted-pair LAN cable runs from the router to the
  touch display ("Zaslon na dotik"). The display connects to the controller by a serial
  bus (Rx−/Tx−, Rx+/Tx+, GND) plus a 24 V AC supply (G/G0) (Duo p. 42) [read from
  figure].
  - So the HTTP endpoint (`cgi/*`) lives on the display, not on the Carel controller, and
    talks to the controller over that serial link [inference].
- **Modbus** is mentioned only for the th-Tune room unit, a serial link on controller
  jack J10 (Duo p. 56).
  - There's nothing about Modbus TCP, BMS integration or exposing the controller to
    third parties.
- **Not in the manuals:** web access, Moja Orca, cloud, IP settings, DHCP, logins or
  usernames.
- **Passwords and codes:**
  - The touch UI has a **service code** entry behind the wrench icon (Touch p. 7).
  - The DODATNI VIR menu asks for a **fixed numeric user password** that is printed in
    the guide (Touch p. 21; not reproduced here).
  - Both are display-level access codes. Nothing links them to the web API login.

---

## 14. Open questions the manuals don't answer

**Regulation and setpoints (R8)**

1. Which setpoints act per regulation mode, above all **constant mode**: is
   `2_Max_VF_MKn` the timer-on flow setpoint and `2_Min_VF_MKn` the lower-regime one?
   Live verification is needed (observe `2_Izrac_temp_TC` and the desired flow at a
   timer boundary).
2. Do day/night room setpoints shift the curve in outdoor-only mode? What reference room
   temperature does the curve assume? How does room + outdoor mode combine the two?
3. Do min/max flow clamp the curve? What do the cooling curve points (+20/+30 °C) and the
   minimum cooling flow do? Is there any dew-point logic?
4. Low-regime action "Izklop" vs "NIŽJA TEMPERATURA", and how it interacts with ECO and
   holiday.

**Modes, timers and overrides (R9, R7)**

5. Meaning of the circuit modes "Avtomatski preklop ogr.-hl." (presumably outdoor
   temperature with a delay) and **"Ročni preklop"**. Where are the "Preklop preko vhoda
   ID2" semantics (HC contact polarity) set?
6. Real tags for party duration, ECO duration and holiday end date (only display aliases
   are known), and their ranges. Does an override end by itself?
7. Timer edge cases: minute granularity, crossing midnight, overlaps. What does
   "24-urni režim" mean for quiet mode (catalog default "unused")?

**Hot water and other functions**

8. DHW on-difference, control sensor (TB or LB), DHW priority, HP boost for DHW, and
   whether the heater is used for legionella.
9. All solar, buffer, quiet-mode, power-limit, PV, screed-drying and anti-blocking
   settings and their logic. The manuals only name the menus. Buffer heating vs cooling
   setpoints (#39) need live or catalog work.
10. Electric heater: what "Ročno" does; stage delays and thresholds; source choice;
    emergency or backup mode when the outdoor unit faults.

**Alarms (R4)**

11. **The full alarm catalogue:** texts, codes (`2_Vrsta_alarma` enum), which alarms latch
    and how they are reset (`2_Reset*`).
    - Only "NI PRETOKA" is documented: it appears after 5 s of no flow and clears itself
      30 s after flow returns.
    - "Napaka senzorja pretoka" is absent. Its trigger and reset need R14 or
      `readAlarms`.
    - `menu_to_field.yaml` shows an "ALARM:" display page bound to `2_Vrsta_alarma`, so
      the enum texts should be in the display project XML (R14).
12. How the outdoor-unit "Napaka" input surfaces: a separate alarm tag? Does it carry the
    Mitsubishi error code?
13. Whether TM1 "system protection" on DK circuits is what `2_Alarm_Talno` reports, and
    its threshold.

**Hardware, persistence and network**

14. Sensor flags `2_Tipalo_B11` / `2_Tipalo_B12`. B11 is the DHW bottom sensor (LB) on the
    Duo, which would duplicate BF2. B12 is unused on the Duo. Is the meaning different on
    the Mono?
15. Mono hardware and its schemes: not covered by either manual (R5). Firmware
    identification beyond the version tags is also missing.
16. Persistence and write endurance of the Carel controller (R10). Is the clock kept
    across power loss (the battery suggests yes)? Does the controller apply a remote write
    at once, as "Shrani" does on the display?
17. Display/network: whether the display or the controller holds settings, and the
    display's session limits. Nothing in the manuals covers this (R1, R11).
