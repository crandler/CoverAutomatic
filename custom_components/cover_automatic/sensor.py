"""Sensor platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .models import CoverStatus
from .sun import get_facade_sun_times

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
    """Set up sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[SensorEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            CoverAutomaticStatusSensor(coordinator, entity_id, cover.name)
        )

    for facade_id, facade in coordinator.storage.facades.items():
        entities.append(
            FacadeSunSensor(coordinator, facade_id, facade.name)
        )
        entities.append(
            FacadeSunEntrySensor(coordinator, facade_id, facade.name)
        )
        entities.append(
            FacadeSunExitSensor(coordinator, facade_id, facade.name)
        )

    async_add_entities(entities)


class CoverAutomaticStatusSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing cover automation status."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def native_value(self) -> str:
        """Return the status."""
        status = self.coordinator.get_cover_status(self._cover_entity_id)
        return status.value

    @property
    def icon(self) -> str:
        """Return icon based on status."""
        try:
            status = CoverStatus(self.native_value)
        except ValueError:
            return "mdi:help-circle"
        match status:
            case CoverStatus.AUTO:
                return "mdi:robot"
            case CoverStatus.PAUSED:
                return "mdi:pause-circle"
            case CoverStatus.MANUAL:
                return "mdi:hand-back-right"
            case CoverStatus.LOCKED:
                return "mdi:lock"
            case _:
                return "mdi:help-circle"


class FacadeSunSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing if sun is on facade."""

    _attr_has_entity_name = True
    _attr_translation_key = "sun_on_facade"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        facade_id: str,
        facade_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._facade_id = facade_id
        self._attr_unique_id = f"{DOMAIN}_facade_{facade_id}_sun"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"facade_{facade_id}")},
            "name": f"CoverAutomatic Facade {facade_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Facade",
        }

    @property
    def native_value(self) -> str:
        """Return if sun is on facade."""
        if self.coordinator.data:
            facades = self.coordinator.data.get("facades", {})
            facade_data = facades.get(self._facade_id)
            if facade_data is None:
                return "unknown"
            return "on" if facade_data.get("sun_on_facade", False) else "off"
        return "unknown"

    @property
    def icon(self) -> str:
        """Return icon based on sun status."""
        if self.native_value == "on":
            return "mdi:white-balance-sunny"
        return "mdi:weather-night"


class FacadeSunEntrySensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing when sun enters facade."""

    _attr_has_entity_name = True
    _attr_translation_key = "sun_entry_time"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        facade_id: str,
        facade_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._facade_id = facade_id
        self._attr_unique_id = f"{DOMAIN}_facade_{facade_id}_sun_entry"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"facade_{facade_id}")},
            "name": f"CoverAutomatic Facade {facade_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Facade",
        }

    @property
    def native_value(self) -> str | None:
        """Return sun entry time for facade."""
        facade = self.coordinator.storage.facades.get(self._facade_id)
        if facade is None:
            _LOGGER.debug("Facade %s not found in storage", self._facade_id)
            return None
        try:
            entry_time, _ = get_facade_sun_times(self.hass, facade)
        except Exception:
            _LOGGER.debug("Failed to get sun times for facade %s", self._facade_id)
            return None
        return entry_time

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:weather-sunset-up"


class FacadeSunExitSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing when sun exits facade."""

    _attr_has_entity_name = True
    _attr_translation_key = "sun_exit_time"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        facade_id: str,
        facade_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._facade_id = facade_id
        self._attr_unique_id = f"{DOMAIN}_facade_{facade_id}_sun_exit"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"facade_{facade_id}")},
            "name": f"CoverAutomatic Facade {facade_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Facade",
        }

    @property
    def native_value(self) -> str | None:
        """Return sun exit time for facade."""
        facade = self.coordinator.storage.facades.get(self._facade_id)
        if facade is None:
            _LOGGER.debug("Facade %s not found in storage", self._facade_id)
            return None
        try:
            _, exit_time = get_facade_sun_times(self.hass, facade)
        except Exception:
            _LOGGER.debug("Failed to get sun times for facade %s", self._facade_id)
            return None
        return exit_time

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:weather-sunset-down"
