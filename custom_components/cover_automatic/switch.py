"""Switch platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .models import CoverStatus

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[SwitchEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            CoverAutomaticAutoSwitch(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class CoverAutomaticAutoSwitch(CoordinatorEntity[CoverAutomaticCoordinator], SwitchEntity):
    """Switch to enable/disable automation for a cover."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_enabled"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_auto"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return true if automation is enabled."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        return cover.auto_enabled if cover else False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = True
            await self.coordinator.storage.async_add_cover(cover)
            self.coordinator.resume_cover(self._cover_entity_id)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = False
            await self.coordinator.storage.async_add_cover(cover)
            self.coordinator.storage.update_cover_status(
                self._cover_entity_id, CoverStatus.MANUAL.value, None
            )
            self.async_write_ha_state()
