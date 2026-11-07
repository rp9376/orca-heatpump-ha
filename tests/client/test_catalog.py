"""The catalog matches the manufacturer's metadata and the real pumps."""

import re

import pytest

from custom_components.orca_heatpump.client import catalog
from custom_components.orca_heatpump.client.catalog import (
    CATALOG,
    TIMER_PROGRAMMES,
    TIMER_RANGES,
    timer_tags,
)
from custom_components.orca_heatpump.client.models import SLOTS, Kind, TagDef

from .helpers import DUO, MONO, ROOT, load_dump, load_json

MANUFACTURER = load_json(ROOT / "research" / "moja_orca_catalog.json")["tags"]
REGISTERS = load_json(ROOT / "research" / "tag_registers.json")["tags"]
NEWER_FIRMWARE = set(load_dump(DUO)) | set(load_dump(MONO))
# The topology needs the schema number itself, not the diagram's name.
KIND_EXCEPTIONS = {"2_Shema": Kind.NUMBER}
# Integer registers whose values the manufacturer's info page still shows
# with one decimal (raw 90 as "9.0%").
SCALE_EXCEPTIONS = {"2_Odstotki_odprtosti_MP1", "2_Odstotki_odprtosti_MP2"}
KIND_OF_TYPE = {
    "boolean": Kind.BOOL,
    "float": Kind.NUMBER,
    "integer": Kind.NUMBER,
    "input": Kind.NUMBER,
    "enum": Kind.ENUM,
    "list": Kind.ENUM,
}


def slot_tags(definition: TagDef) -> list[tuple[int | None, str]]:
    """Return (slot, tag) for every tag of an entry."""
    slots = SLOTS if definition.slot_tags else (None,)
    return [
        (slot, tag) for slot in slots if (tag := definition.tag_name(slot)) is not None
    ]


ALL = [
    pytest.param(definition, slot, tag, id=f"{definition.key}-{tag}")
    for definition in CATALOG
    for slot, tag in slot_tags(definition)
]
FROM_MANUFACTURER = [p for p in ALL if p.values[2] in MANUFACTURER]
ON_REGISTERS = [p for p in ALL if "area" in REGISTERS.get(p.values[2], {})]


def test_keys_unique_and_named() -> None:
    """Keys are unique and each entry is the module constant of its key."""
    keys = [definition.key for definition in CATALOG]

    assert len(keys) == len(set(keys))
    assert all(
        getattr(catalog, key.upper()) is d for key, d in zip(keys, CATALOG, strict=True)
    )


@pytest.mark.parametrize("definition", CATALOG, ids=lambda d: d.key)
def test_entry_shape(definition: TagDef) -> None:
    """Each entry names its tag once, or once per slot, and nothing secret."""
    assert (definition.tag is None) != (definition.slot_tags is None)
    assert definition.tag_names()
    assert not any(
        re.search(r"geslo|kod[ae]", t, re.IGNORECASE) for t in definition.tag_names()
    )
    assert definition.scale in (1, 10)


@pytest.mark.parametrize(
    "definition",
    [d for d in CATALOG if d.writable and d.kind is Kind.NUMBER],
    ids=lambda d: d.key,
)
def test_writable_numbers_have_range(definition: TagDef) -> None:
    """Writable numbers have a range and a step matching their scale."""
    assert definition.minimum is not None
    assert definition.maximum is not None
    assert definition.minimum < definition.maximum
    assert definition.step == 1 / definition.scale


@pytest.mark.parametrize(("definition", "slot", "tag"), FROM_MANUFACTURER)
def test_matches_manufacturer(definition: TagDef, slot: int | None, tag: str) -> None:
    """Kind, scale, range and enum options follow the manufacturer's metadata."""
    info = MANUFACTURER[tag]

    assert definition.kind is KIND_EXCEPTIONS.get(tag, KIND_OF_TYPE[info["type"]])
    if definition.kind is Kind.NUMBER and tag not in KIND_EXCEPTIONS:
        assert definition.scale == (10 if info["type"] == "float" else 1)
    if definition.writable and info.get("min") is not None:
        assert (definition.minimum, definition.maximum) == (
            info["min"] / definition.scale,
            info["max"] / definition.scale,
        )
    if info.get("values_en"):
        assert set(definition.options_for(slot)) == {
            raw for raw, text in enumerate(info["values_en"]) if text
        }


@pytest.mark.parametrize(("definition", "slot", "tag"), ON_REGISTERS)
def test_matches_registers(definition: TagDef, slot: int | None, tag: str) -> None:
    """Writability and scale agree with where the controller keeps the tag."""
    register = REGISTERS[tag]
    del slot

    if definition.writable:
        assert register["area"] in ("HREG", "OUTP")
    if register["area"] in ("HREG", "IREG") and tag not in SCALE_EXCEPTIONS:
        analog = 500000 <= register["address"] < 600000
        assert analog == (definition.kind is Kind.NUMBER and definition.scale == 10)


@pytest.mark.parametrize(("definition", "slot", "tag"), ALL)
def test_tag_exists_somewhere(definition: TagDef, slot: int | None, tag: str) -> None:
    """Every tag exists on our pump or on a pump with newer firmware."""
    del definition, slot

    assert tag in REGISTERS or tag in NEWER_FIRMWARE


def test_power_limit_ranges() -> None:
    """The opt-in power limits keep the manufacturer's minimums (ADR 0012)."""
    assert [
        (d.minimum, d.maximum)
        for d in (
            catalog.HP_POWER_LIMIT_HEATING,
            catalog.HP_POWER_LIMIT_DHW,
            catalog.HP_POWER_LIMIT_COOLING,
            catalog.QUIET_POWER_LIMIT,
        )
    ] == [(40.0, 100.0), (40.0, 100.0), (16.0, 100.0), (31.0, 100.0)]


def test_timer_tags() -> None:
    """All 165 timer tags exist on our pump and are distinct."""
    tags = [
        tag
        for programme in TIMER_PROGRAMMES
        for time_range in TIMER_RANGES
        for tag in timer_tags(programme, time_range)
    ]

    assert len(tags) == len(set(tags)) == 165
    assert all(tag in REGISTERS for tag in tags)
    assert timer_tags(2, 2)[:2] == ("2_TIMER_2_Ura_ON_2", "2_TIMER_2_Minute_ON_2")


NEVER_WRITABLE = re.compile(
    r"2_Shema"
    r"|Kontakt"
    r"|Kalibracija"
    r"|GESLO|Geslo|KODA|KODE"
    r"|CURRENT"
    r"|Cas_MP"
    r"|Krivulja_TC"
    r"|Limita_moci"
    r"|Sobni"
    r"|Talno_Radiatorsko"
)


def test_installer_settings_never_writable() -> None:
    """The installer settings are never writable."""
    assert not [
        tag
        for definition in CATALOG
        if definition.writable
        for tag in definition.tag_names()
        if NEVER_WRITABLE.search(tag)
    ]
