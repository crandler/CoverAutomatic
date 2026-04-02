"""Number platform for CoverAutomatic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import CoverAutomaticConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CoverAutomaticConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator = entry.runtime_data.coordinator

    entities: list[NumberEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            PauseDurationNumber(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class PauseDurationNumber(CoordinatorEntity[CoverAutomaticCoordinator], NumberEntity):
    """Number entity for pause duration configuration."""

    _attr_has_entity_name = True
    _attr_translation_key = "pause_duration"
    _attr_native_min_value = 0
    _attr_native_max_value = 480
    _attr_native_step = 5
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_pause_duration"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def native_value(self) -> float:
        """Return the current pause duration."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover is None:
            return float(self.coordinator.storage.pause_duration)
        duration = cover.pause_duration if cover.pause_duration is not None else self.coordinator.storage.pause_duration
        return float(duration)

    async def async_set_native_value(self, value: float) -> None:
        """Set the pause duration."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.pause_duration = int(value)
            await self.coordinator.storage.async_add_cover(cover)
            self.async_write_ha_state()
