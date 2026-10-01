"""Binary sensor platform for CoverAutomatic."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import i18n
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
    """Set up binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([WindProtectionBinarySensor(coordinator, entry.entry_id)])


class WindProtectionBinarySensor(CoordinatorEntity[CoverAutomaticCoordinator], BinarySensorEntity):
    """On while wind protection drives the covers."""

    _attr_has_entity_name = True
    _attr_translation_key = "wind_protection"
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator: CoverAutomaticCoordinator, entry_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_wind_protection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "CoverAutomatic",
            "manufacturer": "CoverAutomatic",
            "model": i18n.text(coordinator.hass, "model_controller"),
        }

    @property
    def is_on(self) -> bool:
        """Whether wind protection is active."""
        return self.coordinator.wind_protected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Wind speed, threshold and hysteresis."""
        storage = self.coordinator.storage
        return {
            "wind_speed": self.coordinator.get_wind_speed(),
            "threshold": storage.wind_speed_threshold,
            "hysteresis": storage.wind_speed_hysteresis,
            "wind_sensor": storage.wind_sensor,
        }
