"""Select platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

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
    """Set up select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    async_add_entities([ScenarioSelect(coordinator, entry.entry_id)])


class ScenarioSelect(CoordinatorEntity[CoverAutomaticCoordinator], SelectEntity):
    """Select entity for choosing active scenario."""

    _attr_has_entity_name = True
    _attr_translation_key = "scenario"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_scenario"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "CoverAutomatic",
            "manufacturer": "CoverAutomatic",
            "model": "Controller",
        }

    @property
    def options(self) -> list[str]:
        """Return available scenarios."""
        return list(self.coordinator.storage.scenarios.keys())

    @property
    def current_option(self) -> str | None:
        """Return current scenario."""
        return self.coordinator.storage.active_scenario

    async def async_select_option(self, option: str) -> None:
        """Change the selected scenario."""
        self.coordinator.storage.active_scenario = option
        await self.coordinator.storage.async_save()
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
