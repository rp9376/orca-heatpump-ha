"""The tag catalog: every tag the integration reads or writes.

Types, ranges, units and enum orders follow the manufacturer's metadata
(research/moja_orca_catalog.json) wherever it has the tag; the rest comes from
research/catalog_draft.md. Circuit entries name the tag of each slot
explicitly, because the display's names are irregular. Password and code
tags are deliberately absent. tests/client/test_catalog.py checks all of this.
"""

from types import MappingProxyType
from typing import Final

from .models import Element, Kind, TagDef

_TIMER_OPTIONS = MappingProxyType(
    {
        0: "all_day",
        1: "programme_1",
        2: "programme_2",
        3: "programme_3",
        4: "programme_4",
        5: "programme_5",
    }
)
_OPERATING_PROGRAMME_OPTIONS = MappingProxyType(
    {0: "normal", 1: "holiday", 2: "party", 3: "eco"}
)
_QUICK_ROOM_MODE_OPTIONS = MappingProxyType(
    {0: "inactive", 1: "off", 2: "heating", 3: "cooling"}
)
_QUIET_MODE_OPTIONS = MappingProxyType(
    {
        0: "off",
        1: "manual",
        2: "timer",
        3: "outdoor_temperature",
        4: "outdoor_temperature_and_timer",
    }
)
_HEATER_MODE_OPTIONS = MappingProxyType({0: "off", 1: "auto", 2: "manual"})
_HEATER_PARALLEL_OPTIONS = MappingProxyType(
    {0: "off", 1: "one_stage", 2: "two_stages", 3: "three_stages"}
)
_ADDITIONAL_SOURCE_OPTIONS = MappingProxyType(
    {
        1: "electric_heater",
        2: "additional_source",
        3: "electric_heater_and_additional_source",
    }
)
_HEATER_STAGES_OPTIONS = MappingProxyType(
    {1: "one_stage", 2: "two_stages", 3: "three_stages"}
)
_INSTALLATION_TYPE_OPTIONS = MappingProxyType({0: "radiators", 1: "underfloor"})
_CIRCUIT_MODE_OPTIONS = MappingProxyType(
    {1: "heating", 2: "cooling", 3: "auto_heat_cool", 4: "input_id2", 5: "manual"}
)
_HEATING_REGULATION_OPTIONS = MappingProxyType(
    {1: "room", 2: "outdoor", 3: "room_and_outdoor", 4: "constant"}
)
_COOLING_REGULATION_OPTIONS = MappingProxyType(
    {1: "room", 2: "outdoor", 3: "room_and_outdoor", 4: "constant"}
)
_ROOM_SENSOR_TYPE_OPTIONS = MappingProxyType(
    {1: "carel_dpwt", 2: "ntc", 3: "on_off_thermostat", 4: "wireless_orca", 5: "thtune"}
)
_LOW_REGIME_ACTION_OPTIONS = MappingProxyType({0: "off", 1: "lower_temperature"})
_LEGIONELLA_DAY_OPTIONS = MappingProxyType(
    {
        1: "monday",
        2: "tuesday",
        3: "wednesday",
        4: "thursday",
        5: "friday",
        6: "saturday",
        7: "sunday",
    }
)
_LEGIONELLA_CYCLE_OPTIONS = MappingProxyType(
    {1: "weekly", 2: "every_two_weeks", 3: "monthly", 4: "every_two_months"}
)
_SOLAR_TARGET_OPTIONS = MappingProxyType({0: "hot_water", 1: "space_heating"})
_CIRCUIT_NAME_OPTIONS = MappingProxyType(
    {
        1: "heating_circuit_1",
        2: "heating_circuit_2",
        3: "heating_circuit_3",
        4: "direct_circuit_1",
        5: "direct_circuit_2",
        6: "direct_circuit_3",
        7: "mixing_circuit_1",
        8: "mixing_circuit_2",
        9: "cellar",
        10: "ground_floor",
        11: "storey",
        12: "first_floor",
        13: "second_floor",
        14: "attic",
        15: "radiators",
        16: "underfloor",
        17: "convectors",
        18: "heating",
        19: "cooling",
        20: "wall",
    }
)
_OUTDOOR_UNIT_STATE_OPTIONS = MappingProxyType(
    {0: "off", 1: "heating", 2: "cooling", 3: "defrost"}
)
_VALVE_3WAY_OPTIONS = MappingProxyType({0: "space_heating", 1: "hot_water"})
_MIXING_VALVE_STATE_OPTIONS = MappingProxyType({0: "off", 1: "opening", 2: "closing"})
_ALARM_CODE_OPTIONS = MappingProxyType(
    {
        0: "none",
        1: "outdoor_unit",
        2: "flow_temperature_circuit_1",
        3: "flow_temperature_circuit_2",
        4: "no_flow",
        5: "flow_switch",
        6: "hp_temperature_low",
    }
)
_OUTDOOR_UNIT_BRAND_OPTIONS = MappingProxyType({1: "mitsubishi"})
_CIRCUIT_MODE_OPTIONS_SLOT3 = MappingProxyType(
    {1: "heating", 2: "cooling", 3: "auto_heat_cool", 4: "input_id2"}
)

OUTDOOR_TEMPERATURE = TagDef(
    key="outdoor_temperature",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Temp_Zunanja",
    scale=10,
    unit="°C",
)

HP_TEMPERATURE = TagDef(
    key="hp_temperature",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Poti1",
    scale=10,
    unit="°C",
)

HP_TARGET_TEMPERATURE = TagDef(
    key="hp_target_temperature",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Izrac_temp_TC",
    scale=10,
    unit="°C",
)

OUTDOOR_UNIT_STATE = TagDef(
    key="outdoor_unit_state",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Rezim_delov_TC",
    options=_OUTDOOR_UNIT_STATE_OPTIONS,
)

OUTDOOR_UNIT_POWER = TagDef(
    key="outdoor_unit_power",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_PRIKAZ_Reg_temp_vode",
    scale=10,
    unit="%",
)

PUMP_P0 = TagDef(
    key="pump_p0",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_C0",
)

FLOW_SWITCH = TagDef(
    key="flow_switch",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Pogoj_maska_pret_stik",
)

VALVE_3WAY = TagDef(
    key="valve_3way",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Preklop_PV1",
    options=_VALVE_3WAY_OPTIONS,
)

DEFROST_ACTIVE = TagDef(
    key="defrost_active",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Odtaljevanje_izhod",
)

SYSTEM_ENABLE = TagDef(
    key="system_enable",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_Izklop",
    writable=True,
)

OPERATING_PROGRAMME = TagDef(
    key="operating_programme",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Delovanje_MENI",
    writable=True,
    options=_OPERATING_PROGRAMME_OPTIONS,
)

QUICK_ROOM_MODE = TagDef(
    key="quick_room_mode",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_HITRI_Rezim",
    writable=True,
    options=_QUICK_ROOM_MODE_OPTIONS,
)

HP_POWER_LIMIT_HEATING = TagDef(
    key="hp_power_limit_heating",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Max_moc_TC_pri_OGR",
    scale=10,
    unit="%",
    writable=True,
    minimum=40.0,
    maximum=100.0,
    step=0.1,
)

HP_POWER_LIMIT_DHW = TagDef(
    key="hp_power_limit_dhw",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Max_moc_TC_pri_SV",
    scale=10,
    unit="%",
    writable=True,
    minimum=40.0,
    maximum=100.0,
    step=0.1,
)

HP_POWER_LIMIT_COOLING = TagDef(
    key="hp_power_limit_cooling",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Max_moc_TC_pri_HLAJ",
    scale=10,
    unit="%",
    writable=True,
    minimum=16.0,
    maximum=100.0,
    step=0.1,
)

QUIET_POWER_LIMIT = TagDef(
    key="quiet_power_limit",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Max_moc_TC_TISJA",
    scale=10,
    unit="%",
    writable=True,
    minimum=31.0,
    maximum=100.0,
    step=0.1,
)

QUIET_MODE = TagDef(
    key="quiet_mode",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Tisje_delov",
    writable=True,
    options=_QUIET_MODE_OPTIONS,
)

QUIET_OUTDOOR_TEMP = TagDef(
    key="quiet_outdoor_temp",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Temp_AF_za_TISJE_DEL",
    scale=10,
    unit="°C",
    writable=True,
    minimum=-30.0,
    maximum=30.0,
    step=0.1,
)

QUIET_TIMER_PROGRAMME = TagDef(
    key="quiet_timer_programme",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Izbira_TIMERJA_TISJE",
    writable=True,
    options=_TIMER_OPTIONS,
)

QUIET_ACTIVE = TagDef(
    key="quiet_active",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_TISJE_DEL",
)

HEATER_MODE = TagDef(
    key="heater_mode",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Vklop_Elektro_Grelci",
    writable=True,
    options=_HEATER_MODE_OPTIONS,
)

HEATER_PARALLEL = TagDef(
    key="heater_parallel",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Vzporedno_Elektro_Grelci",
    writable=True,
    options=_HEATER_PARALLEL_OPTIONS,
)

HEATER_STAGE1_DELAY = TagDef(
    key="heater_stage1_delay",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Elektro_Grelec_Zakasnitev_1_ST",
    unit="min",
    writable=True,
    minimum=1,
    maximum=1500,
    step=1,
)

HEATER_STAGE2_DELAY = TagDef(
    key="heater_stage2_delay",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Elektro_Grelec_Zakasnitev_2_ST",
    unit="min",
    writable=True,
    minimum=1,
    maximum=1500,
    step=1,
)

HEATER_STAGE3_DELAY = TagDef(
    key="heater_stage3_delay",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Elektro_Grelec_Zakasnitev_3_ST",
    unit="min",
    writable=True,
    minimum=1,
    maximum=1500,
    step=1,
)

HEATER_STAGE1_OUTDOOR_TEMP = TagDef(
    key="heater_stage1_outdoor_temp",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Zun_temp_za_vklop_Grelec_1",
    scale=10,
    unit="°C",
    writable=True,
    minimum=-30.0,
    maximum=30.0,
    step=0.1,
)

HEATER_STAGE2_OUTDOOR_TEMP = TagDef(
    key="heater_stage2_outdoor_temp",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Zun_temp_za_vklop_Grelec_2",
    scale=10,
    unit="°C",
    writable=True,
    minimum=-30.0,
    maximum=30.0,
    step=0.1,
)

HEATER_STAGE3_OUTDOOR_TEMP = TagDef(
    key="heater_stage3_outdoor_temp",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Zun_temp_za_vklop_Grelec_3",
    scale=10,
    unit="°C",
    writable=True,
    minimum=-30.0,
    maximum=30.0,
    step=0.1,
)

HEATER_STAGE1_ON = TagDef(
    key="heater_stage1_on",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_ele_grelca_1",
)

HEATER_STAGE2_ON = TagDef(
    key="heater_stage2_on",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_ele_grelca_2",
)

HEATER_STAGE3_ON = TagDef(
    key="heater_stage3_on",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_ele_grelca_3",
)

ADDITIONAL_SOURCE_DELAY = TagDef(
    key="additional_source_delay",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Dodatni_Vir_Zakasnitev",
    unit="min",
    writable=True,
    minimum=0,
    maximum=999,
    step=1,
)

ADDITIONAL_SOURCE_OUTDOOR_TEMP = TagDef(
    key="additional_source_outdoor_temp",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Temp_Vklop_Dod_Vir",
    scale=10,
    unit="°C",
    writable=True,
    minimum=-35.0,
    maximum=35.0,
    step=0.1,
)

ADDITIONAL_SOURCE_PARALLEL = TagDef(
    key="additional_source_parallel",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vzporedno_Dod_vir_izklop",
    writable=True,
)

PV_FUNCTION = TagDef(
    key="pv_function",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_PV_Vklop",
    writable=True,
)

SCREED_DRYING = TagDef(
    key="screed_drying",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Susenje_estrihov_vklop",
    writable=True,
)

SCREED_DRYING_MIN_FLOW = TagDef(
    key="screed_drying_min_flow",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Min_VF_susenje_estrihov",
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=50.0,
    step=0.1,
)

SCREED_DRYING_MAX_FLOW = TagDef(
    key="screed_drying_max_flow",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Max_VF_susenje_estrihov",
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=55.0,
    step=0.1,
)

SCREED_DRYING_DAYS = TagDef(
    key="screed_drying_days",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Stevilo_dni_susenje_estrihov",
    unit="d",
)

SCREED_DRYING_CURRENT_DAY = TagDef(
    key="screed_drying_current_day",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Tekoci_dan_susenje_estrihov",
    unit="d",
)

ANTI_BLOCK_PROGRAMME = TagDef(
    key="anti_block_programme",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Vklop_ANTI_BLOK_prog",
    writable=True,
)

ALARM_ACTIVE = TagDef(
    key="alarm_active",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_JE_ALARM",
)

ALARM_CODE = TagDef(
    key="alarm_code",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Vrsta_alarma",
    options=_ALARM_CODE_OPTIONS,
)

ALARM_OUTDOOR_UNIT = TagDef(
    key="alarm_outdoor_unit",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Alarm_skupna_napaka",
)

ALARM_FLOW_SWITCH = TagDef(
    key="alarm_flow_switch",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Alarm_pretocno_stikalo",
)

ALARM_NO_FLOW = TagDef(
    key="alarm_no_flow",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Alarm_ni_pretoka",
)

ALARM_HP_TEMPERATURE_LOW = TagDef(
    key="alarm_hp_temperature_low",
    element=Element.SYSTEM,
    kind=Kind.BOOL,
    tag="2_Alarm_prenizka_temp_TC",
)

ALARM_ERROR = TagDef(
    key="alarm_error",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_NAPAKA",
)

ALARM_FLOW_TEMPERATURE = TagDef(
    key="alarm_flow_temperature",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=("2_Alarm_Talno", "2_Alarm_Talno_VF2", None),
)

ALARM_ROOM_SENSOR = TagDef(
    key="alarm_room_sensor",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=("2_Alarm_RF1", "2_Alarm_RF2", "2_Alarm_RF3"),
)

FIRMWARE_BUILD = TagDef(
    key="firmware_build",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Verzija_programa_ZAPOREDJE",
)

FIRMWARE_YEAR = TagDef(
    key="firmware_year",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Verzija_programa_LETO",
)

FIRMWARE_MONTH = TagDef(
    key="firmware_month",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Verzija_programa_MESEC",
)

FIRMWARE_DAY = TagDef(
    key="firmware_day",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Verzija_programa_DAN",
)

OUTDOOR_UNIT_BRAND = TagDef(
    key="outdoor_unit_brand",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Izbira_Mitsubishi_Fujitsu",
    options=_OUTDOOR_UNIT_BRAND_OPTIONS,
)

SCHEMA = TagDef(
    key="schema",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Shema",
)

BUFFER_PRESENT = TagDef(
    key="buffer_present",
    element=Element.BUFFER,
    kind=Kind.BOOL,
    tag="2_Shema_ZALOG",
)

CIRCUIT_PRESENT = TagDef(
    key="circuit_present",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=("2_PogojPGDT_Shema_OK1", "2_PogojPGDT_Shema_OK2", None),
)

ROOM_SENSOR_CONFIGURED = TagDef(
    key="room_sensor_configured",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=(
        "2_PogojPGDT_Shema_in_tipalo_OK1",
        "2_PogojPGDT_Shema_in_tipalo_OK2",
        "2_PogojPGDT_Shema_in_tipalo_OK3",
    ),
)

DHW_CONFIGURED = TagDef(
    key="dhw_configured",
    element=Element.DHW,
    kind=Kind.BOOL,
    tag="2_PogojPGDT_Shema_in_tipalo_SV",
)

ADDITIONAL_SOURCE = TagDef(
    key="additional_source",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Izbira_DOD_VIRA",
    options=_ADDITIONAL_SOURCE_OPTIONS,
)

HEATER_STAGES = TagDef(
    key="heater_stages",
    element=Element.SYSTEM,
    kind=Kind.ENUM,
    tag="2_Izbira_st_grelcev",
    options=_HEATER_STAGES_OPTIONS,
)

CIRCUIT_NAME = TagDef(
    key="circuit_name",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=("2_IME_MK1", "2_IME_MK2", "2_IME_MK3"),
    options=_CIRCUIT_NAME_OPTIONS,
)

CIRCUIT_ENABLE = TagDef(
    key="circuit_enable",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=("2_MK1_vklop", "2_MK2_vklop", "2_DK3_vklop"),
    writable=True,
)

INSTALLATION_TYPE = TagDef(
    key="installation_type",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=(
        "2_Talno_Radiatorsko_MK1",
        "2_Talno_Radiatorsko_MK2",
        "2_Talno_Radiatorsko_DK3",
    ),
    options=_INSTALLATION_TYPE_OPTIONS,
)

CIRCUIT_MODE = TagDef(
    key="circuit_mode",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=("2_Rezim_MK1", "2_Rezim_MK2", "2_Rezim_DK3"),
    writable=True,
    options=_CIRCUIT_MODE_OPTIONS,
    slot_options=MappingProxyType({3: _CIRCUIT_MODE_OPTIONS_SLOT3}),
)

HEATING_REGULATION = TagDef(
    key="heating_regulation",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=(
        "2_Reg_po_RF_AF_KONST_MK1",
        "2_Reg_po_RF_AF_KONST_MK2",
        "2_Reg_po_RF_AF_KONST_DK3",
    ),
    writable=True,
    options=_HEATING_REGULATION_OPTIONS,
)

COOLING_REGULATION = TagDef(
    key="cooling_regulation",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=(
        "2_Reg_po_RF_AF_KONST_MK1_HL",
        "2_Reg_po_RF_AF_KONST_MK2_HL",
        "2_Reg_po_RF_AF_KONST_DK3_HL",
    ),
    writable=True,
    options=_COOLING_REGULATION_OPTIONS,
)

MAX_FLOW_HEATING = TagDef(
    key="max_flow_heating",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Max_VF_MK1", "2_Max_VF_MK2", "2_Max_VF_DK3"),
    scale=10,
    unit="°C",
    writable=True,
    minimum=8.0,
    maximum=60.0,
    step=0.1,
)

MIN_FLOW_HEATING = TagDef(
    key="min_flow_heating",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Min_VF_MK1", "2_Min_VF_MK2", "2_Min_VF_DK3"),
    scale=10,
    unit="°C",
    writable=True,
    minimum=8.0,
    maximum=50.0,
    step=0.1,
)

HP_BOOST_FOR_CIRCUIT = TagDef(
    key="hp_boost_for_circuit",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Povec_temp_TC_pri_MK1", "2_Povec_temp_TC_pri_MK2", None),
    scale=10,
    unit="°C",
    writable=True,
    minimum=1.0,
    maximum=15.0,
    step=0.1,
)

CURVE_PARALLEL_SHIFT = TagDef(
    key="curve_parallel_shift",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Zamik_krivulje_MK1", "2_Zamik_krivulje_MK2", "2_Zamik_krivulje_DK3"),
    scale=10,
    unit="°C",
    writable=True,
    minimum=-15.0,
    maximum=15.0,
    step=0.1,
)

CURVE_SLOPE = TagDef(
    key="curve_slope",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Nagib_krivulje_MK1", "2_Nagib_krivulje_MK2", "2_Nagib_krivulje_DK3"),
    scale=10,
    unit="°C",
    writable=True,
    minimum=-15.0,
    maximum=15.0,
    step=0.1,
)

ROOM_SENSOR_TYPE = TagDef(
    key="room_sensor_type",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=("2_Sobni_DPWT_PGD1", "2_Sobni_2_DPWT_PGD1", "2_Sobni_3_DPWT_PGD1"),
    options=_ROOM_SENSOR_TYPE_OPTIONS,
)

MIN_FLOW_COOLING = TagDef(
    key="min_flow_cooling",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Min_VF_MK1_HL", "2_Min_VF_MK2_HL", "2_Min_VF_DK3_HL"),
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=40.0,
    step=0.1,
)

COOLING_FLOW_AT_20 = TagDef(
    key="cooling_flow_at_20",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Tocka_1_20st_HL_MK1",
        "2_Tocka_1_20st_HL_MK2",
        "2_Tocka_1_20st_HL_DK3",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=40.0,
    step=0.1,
)

COOLING_FLOW_AT_30 = TagDef(
    key="cooling_flow_at_30",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Tocka_2_30st_HL_MK1",
        "2_Tocka_2_30st_HL_MK2",
        "2_Tocka_2_30st_HL_DK3",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=40.0,
    step=0.1,
)

AUTO_HEATING_SWITCH = TagDef(
    key="auto_heating_switch",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=(
        "2_Aktiv_avtom_preklop_zima_MK1",
        "2_Aktiv_avtom_preklop_zima_MK2",
        "2_Aktiv_avtom_preklop_zima_DK3",
    ),
    writable=True,
)

AUTO_HEATING_SWITCH_TEMP = TagDef(
    key="auto_heating_switch_temp",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Temp_za_preklop_zima_MK1",
        "2_Temp_za_preklop_zima_MK2",
        "2_Temp_za_preklop_zima_DK3",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=5.0,
    maximum=30.0,
    step=0.1,
)

AUTO_HEATING_SWITCH_DELAY = TagDef(
    key="auto_heating_switch_delay",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Cas_ur_preklop_zima_MK1",
        "2_Cas_ur_preklop_zima_MK2",
        "2_Cas_ur_preklop_zima_DK3",
    ),
    unit="h",
    writable=True,
    minimum=1,
    maximum=90,
    step=1,
)

AUTO_COOLING_SWITCH = TagDef(
    key="auto_cooling_switch",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=(
        "2_Aktiv_avtom_preklop_poletje_MK1",
        "2_Aktiv_avtom_preklop_poletje_MK2",
        "2_Aktiv_avtom_preklop_poletje_DK3",
    ),
    writable=True,
)

AUTO_COOLING_SWITCH_TEMP = TagDef(
    key="auto_cooling_switch_temp",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Temp_preklop_poletje_MK1_HL",
        "2_Temp_preklop_poletje_MK2_HL",
        "2_Temp_preklop_poletje_DK3_HL",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=5.0,
    maximum=30.0,
    step=0.1,
)

AUTO_COOLING_SWITCH_DELAY = TagDef(
    key="auto_cooling_switch_delay",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Cas_ur_preklop_poletje_MK1_HL",
        "2_Cas_ur_preklop_poletje_MK2_HL",
        "2_Cas_ur_preklop_poletje_DK3_HL",
    ),
    unit="h",
    writable=True,
    minimum=1,
    maximum=90,
    step=1,
)

TIMER_PROGRAMME = TagDef(
    key="timer_programme",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=("2_Izbira_TIMERJA_MK1", "2_Izbira_TIMERJA_MK2", "2_Izbira_TIMERJA_MK3"),
    writable=True,
    options=_TIMER_OPTIONS,
)

LOW_REGIME_ACTION = TagDef(
    key="low_regime_action",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=(
        "2_Ponoci_min_temp_IZKLOP_MK1",
        "2_Ponoci_min_temp_IZKLOP_MK2",
        "2_Ponoci_min_temp_IZKLOP_DK3",
    ),
    writable=True,
    options=_LOW_REGIME_ACTION_OPTIONS,
)

ROOM_SETPOINT_HIGH = TagDef(
    key="room_setpoint_high",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Temp_prostor_dnevna",
        "2_Temp_prostor_dnevna_OK2",
        "2_Temp_prostor_dnevna_OK3",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=10.0,
    maximum=35.0,
    step=0.1,
)

ROOM_SETPOINT_LOW = TagDef(
    key="room_setpoint_low",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=(
        "2_Temp_prostor_nocna",
        "2_Temp_prostor_nocna_OK2",
        "2_Temp_prostor_nocna_OK3",
    ),
    scale=10,
    unit="°C",
    writable=True,
    minimum=10.0,
    maximum=35.0,
    step=0.1,
)

ROOM_TEMPERATURE = TagDef(
    key="room_temperature",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Temp_Prostora", "2_Temp_RF2", "2_Temp_RF3"),
    scale=10,
    unit="°C",
)

ROOM_SETPOINT_ACTIVE = TagDef(
    key="room_setpoint_active",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Zahtevana_RF_MK_1", "2_Zahtevana_RF_MK_2", "2_Zahtevana_RF_DK_3"),
    scale=10,
    unit="°C",
)

FLOW_TEMPERATURE = TagDef(
    key="flow_temperature",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Poti2", "2_Temp_VF2", None),
    scale=10,
    unit="°C",
)

FLOW_TARGET = TagDef(
    key="flow_target",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Temp_zelena_MK_1", "2_Temp_zelena_MK_2", None),
    scale=10,
    unit="°C",
)

MIXING_VALVE_STATE = TagDef(
    key="mixing_valve_state",
    element=Element.CIRCUIT,
    kind=Kind.ENUM,
    slot_tags=("2_Delovanje_MP1", "2_Delovanje_MP2", None),
    options=_MIXING_VALVE_STATE_OPTIONS,
    mixing_only=True,
)

MIXING_VALVE_POSITION = TagDef(
    key="mixing_valve_position",
    element=Element.CIRCUIT,
    kind=Kind.NUMBER,
    slot_tags=("2_Odstotki_odprtosti_MP1", "2_Odstotki_odprtosti_MP2", None),
    scale=10,
    unit="%",
    mixing_only=True,
)

CIRCUIT_PUMP = TagDef(
    key="circuit_pump",
    element=Element.CIRCUIT,
    kind=Kind.BOOL,
    slot_tags=("2_Vklop_C1", "2_Vklop_C2", "2_Vklop_C3"),
)

DHW_ENABLE = TagDef(
    key="dhw_enable",
    element=Element.DHW,
    kind=Kind.BOOL,
    tag="2_SV_vklop",
    writable=True,
)

DHW_TEMP_TOP = TagDef(
    key="dhw_temp_top",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Poti3",
    scale=10,
    unit="°C",
)

DHW_TEMP_BOTTOM = TagDef(
    key="dhw_temp_bottom",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Poti4",
    scale=10,
    unit="°C",
)

DHW_SETPOINT_HIGH = TagDef(
    key="dhw_setpoint_high",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Temp_vode_sanitarna",
    scale=10,
    unit="°C",
    writable=True,
    minimum=8.0,
    maximum=55.0,
    step=0.1,
)

DHW_SETPOINT_LOW = TagDef(
    key="dhw_setpoint_low",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Temp_vode_sanitarna_NIZJA",
    scale=10,
    unit="°C",
    writable=True,
    minimum=8.0,
    maximum=55.0,
    step=0.1,
)

DHW_ON_DIFFERENCE = TagDef(
    key="dhw_on_difference",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Diferenca_vklopa_SV",
    scale=10,
    unit="°C",
    writable=True,
    minimum=0.0,
    maximum=8.0,
    step=0.1,
)

DHW_HP_BOOST = TagDef(
    key="dhw_hp_boost",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Povec_temp_TC_pri_SV",
    scale=10,
    unit="°C",
    writable=True,
    minimum=1.0,
    maximum=15.0,
    step=0.1,
)

DHW_TIMER_PROGRAMME = TagDef(
    key="dhw_timer_programme",
    element=Element.DHW,
    kind=Kind.ENUM,
    tag="2_Izbira_TIMERJA_SV",
    writable=True,
    options=_TIMER_OPTIONS,
)

LEGIONELLA_ENABLE = TagDef(
    key="legionella_enable",
    element=Element.DHW,
    kind=Kind.BOOL,
    tag="2_Legionela_vklop",
    writable=True,
)

LEGIONELLA_TEMPERATURE = TagDef(
    key="legionella_temperature",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_Temperatura_legionela",
    scale=10,
    unit="°C",
    writable=True,
    minimum=65.0,
    maximum=70.0,
    step=0.1,
)

LEGIONELLA_DAY = TagDef(
    key="legionella_day",
    element=Element.DHW,
    kind=Kind.ENUM,
    tag="2_On_Dan_Legionella",
    writable=True,
    options=_LEGIONELLA_DAY_OPTIONS,
)

LEGIONELLA_HOUR = TagDef(
    key="legionella_hour",
    element=Element.DHW,
    kind=Kind.NUMBER,
    tag="2_On_Ura_Legionella",
    unit="h",
    writable=True,
    minimum=0,
    maximum=23,
    step=1,
)

LEGIONELLA_CYCLE = TagDef(
    key="legionella_cycle",
    element=Element.DHW,
    kind=Kind.ENUM,
    tag="2_Legionela_Cikel",
    writable=True,
    options=_LEGIONELLA_CYCLE_OPTIONS,
)

SOLAR_COLLECTOR_TEMPERATURE = TagDef(
    key="solar_collector_temperature",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Poti5",
    scale=10,
    unit="°C",
)

# The same input on a pump without solar, where any sensor can be wired to it (#30).
SOLAR_INPUT_TEMPERATURE = TagDef(
    key="solar_input_temperature",
    element=Element.SYSTEM,
    kind=Kind.NUMBER,
    tag="2_Poti5",
    scale=10,
    unit="°C",
)

SOLAR_PUMP = TagDef(
    key="solar_pump",
    element=Element.SOLAR,
    kind=Kind.BOOL,
    tag="2_Vklop_C3",
)

SOLAR_MIN_COLLECTOR_TEMP = TagDef(
    key="solar_min_collector_temp",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Min_Temp_SOLAR",
    scale=10,
    unit="°C",
    writable=True,
    minimum=20.0,
    maximum=70.0,
    step=0.1,
)

SOLAR_ON_DIFFERENCE = TagDef(
    key="solar_on_difference",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Dif_vklopa_SOLAR",
    scale=10,
    unit="°C",
    writable=True,
    minimum=1.0,
    maximum=20.0,
    step=0.1,
)

SOLAR_OFF_DIFFERENCE = TagDef(
    key="solar_off_difference",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Dif_izklopa_SOLAR",
    scale=10,
    unit="°C",
    writable=True,
    minimum=1.0,
    maximum=10.0,
    step=0.1,
)

SOLAR_ENABLE = TagDef(
    key="solar_enable",
    element=Element.SOLAR,
    kind=Kind.BOOL,
    tag="2_SOLAR_VKLOP",
)

SOLAR_TARGET = TagDef(
    key="solar_target",
    element=Element.SOLAR,
    kind=Kind.ENUM,
    tag="2_SOLAR_Prost_SV",
    options=_SOLAR_TARGET_OPTIONS,
)

SOLAR_MAX_DHW_TEMP = TagDef(
    key="solar_max_dhw_temp",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Max_Temp_BF",
    scale=10,
    unit="°C",
)

SOLAR_MAX_COLLECTOR_TEMP = TagDef(
    key="solar_max_collector_temp",
    element=Element.SOLAR,
    kind=Kind.NUMBER,
    tag="2_Max_Temp_SOLAR",
    scale=10,
    unit="°C",
)

BUFFER_TEMPERATURE = TagDef(
    key="buffer_temperature",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_Temp_Zalog",
    scale=10,
    unit="°C",
)

BUFFER_TARGET = TagDef(
    key="buffer_target",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_Izrac_temp_ZALOG",
    scale=10,
    unit="°C",
)

BUFFER_HIGH_HEATING = TagDef(
    key="buffer_high_heating",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_VISJA_Temp_ZALOG_OGR",
    scale=10,
    unit="°C",
    writable=True,
    minimum=12.0,
    maximum=55.0,
    step=0.1,
)

BUFFER_LOW_HEATING = TagDef(
    key="buffer_low_heating",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_NIZJA_Temp_ZALOG_OGR",
    scale=10,
    unit="°C",
    writable=True,
    minimum=12.0,
    maximum=55.0,
    step=0.1,
)

BUFFER_HIGH_COOLING = TagDef(
    key="buffer_high_cooling",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_VISJA_Temp_ZALOG_HL",
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=40.0,
    step=0.1,
)

BUFFER_LOW_COOLING = TagDef(
    key="buffer_low_cooling",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_NIZJA_Temp_ZALOG_HL",
    scale=10,
    unit="°C",
    writable=True,
    minimum=9.0,
    maximum=40.0,
    step=0.1,
)

BUFFER_ON_DIFFERENCE = TagDef(
    key="buffer_on_difference",
    element=Element.BUFFER,
    kind=Kind.NUMBER,
    tag="2_Diferenca_vklopa_ZALOG",
    scale=10,
    unit="°C",
    writable=True,
    minimum=0.0,
    maximum=9.0,
    step=0.1,
)

BUFFER_TIMER_PROGRAMME = TagDef(
    key="buffer_timer_programme",
    element=Element.BUFFER,
    kind=Kind.ENUM,
    tag="2_Izbira_TIMERJA_ZALOG",
    writable=True,
    options=_TIMER_OPTIONS,
)

CATALOG: Final[tuple[TagDef, ...]] = (
    OUTDOOR_TEMPERATURE,
    HP_TEMPERATURE,
    HP_TARGET_TEMPERATURE,
    OUTDOOR_UNIT_STATE,
    OUTDOOR_UNIT_POWER,
    PUMP_P0,
    FLOW_SWITCH,
    VALVE_3WAY,
    DEFROST_ACTIVE,
    SYSTEM_ENABLE,
    OPERATING_PROGRAMME,
    QUICK_ROOM_MODE,
    HP_POWER_LIMIT_HEATING,
    HP_POWER_LIMIT_DHW,
    HP_POWER_LIMIT_COOLING,
    QUIET_POWER_LIMIT,
    QUIET_MODE,
    QUIET_OUTDOOR_TEMP,
    QUIET_TIMER_PROGRAMME,
    QUIET_ACTIVE,
    HEATER_MODE,
    HEATER_PARALLEL,
    HEATER_STAGE1_DELAY,
    HEATER_STAGE2_DELAY,
    HEATER_STAGE3_DELAY,
    HEATER_STAGE1_OUTDOOR_TEMP,
    HEATER_STAGE2_OUTDOOR_TEMP,
    HEATER_STAGE3_OUTDOOR_TEMP,
    HEATER_STAGE1_ON,
    HEATER_STAGE2_ON,
    HEATER_STAGE3_ON,
    ADDITIONAL_SOURCE_DELAY,
    ADDITIONAL_SOURCE_OUTDOOR_TEMP,
    ADDITIONAL_SOURCE_PARALLEL,
    PV_FUNCTION,
    SCREED_DRYING,
    SCREED_DRYING_MIN_FLOW,
    SCREED_DRYING_MAX_FLOW,
    SCREED_DRYING_DAYS,
    SCREED_DRYING_CURRENT_DAY,
    ANTI_BLOCK_PROGRAMME,
    ALARM_ACTIVE,
    ALARM_CODE,
    ALARM_OUTDOOR_UNIT,
    ALARM_FLOW_SWITCH,
    ALARM_NO_FLOW,
    ALARM_HP_TEMPERATURE_LOW,
    ALARM_ERROR,
    ALARM_FLOW_TEMPERATURE,
    ALARM_ROOM_SENSOR,
    FIRMWARE_BUILD,
    FIRMWARE_YEAR,
    FIRMWARE_MONTH,
    FIRMWARE_DAY,
    OUTDOOR_UNIT_BRAND,
    SCHEMA,
    BUFFER_PRESENT,
    CIRCUIT_PRESENT,
    ROOM_SENSOR_CONFIGURED,
    DHW_CONFIGURED,
    ADDITIONAL_SOURCE,
    HEATER_STAGES,
    CIRCUIT_NAME,
    CIRCUIT_ENABLE,
    INSTALLATION_TYPE,
    CIRCUIT_MODE,
    HEATING_REGULATION,
    COOLING_REGULATION,
    MAX_FLOW_HEATING,
    MIN_FLOW_HEATING,
    HP_BOOST_FOR_CIRCUIT,
    CURVE_PARALLEL_SHIFT,
    CURVE_SLOPE,
    ROOM_SENSOR_TYPE,
    MIN_FLOW_COOLING,
    COOLING_FLOW_AT_20,
    COOLING_FLOW_AT_30,
    AUTO_HEATING_SWITCH,
    AUTO_HEATING_SWITCH_TEMP,
    AUTO_HEATING_SWITCH_DELAY,
    AUTO_COOLING_SWITCH,
    AUTO_COOLING_SWITCH_TEMP,
    AUTO_COOLING_SWITCH_DELAY,
    TIMER_PROGRAMME,
    LOW_REGIME_ACTION,
    ROOM_SETPOINT_HIGH,
    ROOM_SETPOINT_LOW,
    ROOM_TEMPERATURE,
    ROOM_SETPOINT_ACTIVE,
    FLOW_TEMPERATURE,
    FLOW_TARGET,
    MIXING_VALVE_STATE,
    MIXING_VALVE_POSITION,
    CIRCUIT_PUMP,
    DHW_ENABLE,
    DHW_TEMP_TOP,
    DHW_TEMP_BOTTOM,
    DHW_SETPOINT_HIGH,
    DHW_SETPOINT_LOW,
    DHW_ON_DIFFERENCE,
    DHW_HP_BOOST,
    DHW_TIMER_PROGRAMME,
    LEGIONELLA_ENABLE,
    LEGIONELLA_TEMPERATURE,
    LEGIONELLA_DAY,
    LEGIONELLA_HOUR,
    LEGIONELLA_CYCLE,
    SOLAR_COLLECTOR_TEMPERATURE,
    SOLAR_INPUT_TEMPERATURE,
    SOLAR_PUMP,
    SOLAR_MIN_COLLECTOR_TEMP,
    SOLAR_ON_DIFFERENCE,
    SOLAR_OFF_DIFFERENCE,
    SOLAR_ENABLE,
    SOLAR_TARGET,
    SOLAR_MAX_DHW_TEMP,
    SOLAR_MAX_COLLECTOR_TEMP,
    BUFFER_TEMPERATURE,
    BUFFER_TARGET,
    BUFFER_HIGH_HEATING,
    BUFFER_LOW_HEATING,
    BUFFER_HIGH_COOLING,
    BUFFER_LOW_COOLING,
    BUFFER_ON_DIFFERENCE,
    BUFFER_TIMER_PROGRAMME,
)


WEEKDAYS: Final = (
    "Ponedeljek",
    "Torek",
    "Sreda",
    "Cetrtek",
    "Petek",
    "Sobota",
    "Nedelja",
)
TIMER_PROGRAMMES: Final = (1, 2, 3, 4, 5)
TIMER_RANGES: Final = (1, 2, 3)


def timer_tags(programme: int, time_range: int) -> tuple[str, ...]:
    """Return the tags of one timer range.

    The order is start hour, start minute, end hour, end minute, then the
    Monday to Sunday flags. Unlike circuit tags, timer names are regular on
    every known firmware.
    """
    p, r = programme, time_range
    return (
        f"2_TIMER_{p}_Ura_ON_{r}",
        f"2_TIMER_{p}_Minute_ON_{r}",
        f"2_TIMER_{p}_Ura_OFF_{r}",
        f"2_TIMER_{p}_Minute_OFF_{r}",
        *(f"2_TIMER_{p}_{day}_{r}" for day in WEEKDAYS),
    )
