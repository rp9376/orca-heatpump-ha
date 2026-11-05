"""Base entity, descriptions and the write path of the integration."""

from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
import math
from typing import Any, override

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import catalog
from .client.codec import encode
from .client.errors import OrcaError, OrcaValueError
from .client.models import (
    CircuitKind,
    Element,
    Kind,
    PumpTopology,
    Reading,
    Reason,
    Snapshot,
    TagDef,
    Value,
)
from .const import CONF_ALLOW_POWER_LIMITS, DOMAIN
from .coordinator import OrcaConfigEntry, OrcaCoordinator
from .helpers import element_present

type TagWrite = tuple[TagDef, int | None, Value]


@dataclass(frozen=True, slots=True)
class EntityContext:
    """What decides whether an optional entity exists."""

    topology: PumpTopology
    options: Mapping[str, Any]
    snapshot: Snapshot


@dataclass(frozen=True, kw_only=True)
class OrcaEntityDescription(EntityDescription):
    """Ties an entity to one catalog entry; ``key`` is the catalog key."""

    definition: TagDef
    exists_fn: Callable[[EntityContext, int | None], bool] = lambda _, __: True

    def __post_init__(self) -> None:
        """Default the translation key to the catalog key."""
        if self.translation_key is None:
            object.__setattr__(self, "translation_key", self.key)


HEATER_STAGES = {"one_stage": 1, "two_stages": 2, "three_stages": 3}


def heater_stage(stage: int) -> Callable[[EntityContext, int | None], bool]:
    """Return whether the pump's electric heater has this stage."""

    def exists(context: EntityContext, slot: int | None) -> bool:
        stages = context.snapshot.value(catalog.HEATER_STAGES)
        return not isinstance(stages, str) or HEATER_STAGES[stages] >= stage

    return exists


def any_circuit(context: EntityContext, slot: int | None) -> bool:
    """Return whether the pump heats or cools rooms through any circuit."""
    return bool(context.topology.circuits)


def mixing_circuit(context: EntityContext, slot: int | None) -> bool:
    """Return whether the slot is a mixing circuit."""
    return slot is not None and bool(
        (circuit := context.topology.circuit(slot))
        and circuit.kind is CircuitKind.MIXING
    )


def room_sensor(context: EntityContext, slot: int | None) -> bool:
    """Return whether the slot's circuit has a room sensor."""
    return slot is not None and bool(
        (circuit := context.topology.circuit(slot)) and circuit.room_sensor
    )


def power_limit(
    definition: TagDef, *, writable: bool
) -> Callable[[EntityContext, int | None], bool]:
    """Return whether a power limit exists in this form (ADR 0012).

    The option decides between sensor and number; the hot water limit also
    needs hot water.
    """

    def exists(context: EntityContext, slot: int | None) -> bool:
        allowed = bool(context.options.get(CONF_ALLOW_POWER_LIMITS))
        return allowed is writable and (
            context.topology.dhw or definition is not catalog.HP_POWER_LIMIT_DHW
        )

    return exists


def entity_targets[D: OrcaEntityDescription](
    entry: OrcaConfigEntry, descriptions: Iterable[D]
) -> Iterator[tuple[D, int | None]]:
    """Return (description, slot) for every entity this pump needs.

    An entity exists when its element (or circuit slot) is present, it is
    not a mixing-valve value on a direct circuit, its tag exists on this
    firmware and its own ``exists_fn`` agrees.
    """
    data = entry.runtime_data
    context = EntityContext(data.topology, entry.options, data.coordinator.data)
    for description in descriptions:
        definition = description.definition
        for _, slot in definition.refs():
            if not element_present(data.topology, definition.element, slot):
                continue
            circuit = data.topology.circuit(slot) if slot is not None else None
            if definition.mixing_only and (
                circuit is None or circuit.kind is not CircuitKind.MIXING
            ):
                continue
            reading = context.snapshot.reading(definition, slot)
            if reading.reason is Reason.UNKNOWN_TAG:
                continue
            if description.exists_fn(context, slot):
                yield description, slot


def device_identifier(entry_id: str, element: Element, slot: int | None) -> str:
    """Return the identifier of the device an element's entities belong to."""
    if element is Element.CIRCUIT:
        return f"{entry_id}_circuit{slot}"
    if element is Element.SYSTEM:
        return entry_id
    return f"{entry_id}_{element.value}"


async def async_write_value(
    coordinator: OrcaCoordinator, definition: TagDef, slot: int | None, value: Value
) -> None:
    """Write one value through the client, then refresh."""
    await async_write_values(coordinator, ((definition, slot, value),))


def round_to_step(value: float, step: float) -> float:
    """Round a number to a step; NaN and infinity are left for the client to refuse."""
    return round(value / step) * step if math.isfinite(value) else value


async def async_write_values(
    coordinator: OrcaCoordinator, writes: Iterable[TagWrite]
) -> None:
    """Write values in order through the client, then refresh once.

    Every value is checked before the first one is sent, so a bad value can't
    leave a call half done. The client checks again, skips unchanged values
    and reads each value back (PLAN.md §10). One refresh at the end keeps the
    debouncer from delaying the last write's state.
    """
    # Home Assistant converts units without rounding: 70 °F arrives as 21.111 °C.
    rounded = [
        (
            definition,
            slot,
            round_to_step(value, 1 / definition.scale)
            if definition.kind is Kind.NUMBER and isinstance(value, float)
            else value,
        )
        for definition, slot, value in writes
    ]
    try:
        for definition, slot, value in rounded:
            encode(definition, slot, value)
    except OrcaValueError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_value",
            translation_placeholders={"error": str(err)},
        ) from err
    try:
        for definition, slot, value in rounded:
            await coordinator.client.async_write(definition, slot, value)
    except OrcaError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="write_failed",
            translation_placeholders={"error": str(err)},
        ) from err
    finally:
        # A failed write, or one before it, may have taken effect.
        await coordinator.async_request_refresh()


class OrcaEntity(CoordinatorEntity[OrcaCoordinator]):
    """An entity backed by one catalog entry, in one circuit slot or none."""

    _attr_has_entity_name = True
    entity_description: OrcaEntityDescription

    def __init__(
        self,
        coordinator: OrcaCoordinator,
        description: OrcaEntityDescription,
        slot: int | None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self.slot = slot
        entry_id = coordinator.config_entry.entry_id
        key = description.key
        self._attr_unique_id = (
            f"{entry_id}_circuit{slot}_{key}"
            if slot is not None
            else f"{entry_id}_{key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    device_identifier(entry_id, description.definition.element, slot),
                )
            }
        )

    @property
    def reading(self) -> Reading:
        """Return the reading of the entity's own tag."""
        return self.coordinator.data.reading(
            self.entity_description.definition, self.slot
        )

    def value_of(self, definition: TagDef) -> Value | None:
        """Return another catalog entry's value, in this entity's slot if circuit."""
        slot = self.slot if definition.element is Element.CIRCUIT else None
        return self.coordinator.data.value(definition, slot)

    @property
    @override
    def available(self) -> bool:
        """Return false only if the read failed or the sensor isn't connected.

        A value that is missing or nobody has seen yet shows as unknown: the
        display answered. A select can then still set it back.
        """
        return super().available and self.reading.reason is not Reason.NOT_CONNECTED

    async def async_write(self, value: Value) -> None:
        """Write the entity's own tag."""
        await async_write_value(
            self.coordinator, self.entity_description.definition, self.slot, value
        )
