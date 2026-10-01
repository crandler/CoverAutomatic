"""Sensor platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import i18n
from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .models import ComfortMode, CoverStatus
from .sun import get_facade_sun_times

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import CoverAutomaticConfigEntry

_LOGGER = logging.getLogger(__name__)

_STATUS_ICONS: dict[CoverStatus, str] = {
    CoverStatus.AUTO: "mdi:robot",
    CoverStatus.PAUSED: "mdi:pause-circle",
    CoverStatus.MANUAL: "mdi:hand-back-right",
    CoverStatus.LOCKED: "mdi:lock",
    CoverStatus.VENTING: "mdi:window-open-variant",
    CoverStatus.WIND_PROTECTED: "mdi:weather-windy",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CoverAutomaticConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = entry.runtime_data.coordinator

    known_covers: set[str] = set()
    known_facades: set[str] = set()

    def _new_entities() -> list[SensorEntity]:
        """Build entities for covers/facades that have none yet."""
        storage = coordinator.storage
        covers = storage.covers
        facades = storage.facades
        # Forget deleted objects so re-adding them later creates entities again
        known_covers.intersection_update(covers)
        known_facades.intersection_update(facades)

        entities: list[SensorEntity] = []
        for entity_id, cover in covers.items():
            if entity_id in known_covers:
                continue
            known_covers.add(entity_id)
            entities.append(
                CoverAutomaticStatusSensor(coordinator, entity_id, cover.name)
            )
            entities.extend(
                cls(coordinator, entity_id, cover.name)
                for cls in (
                    CoverRuleSensor,
                    CoverTargetPositionSensor,
                    CoverPositionSensor,
                    CoverComfortSensor,
                    CoverPauseEndSensor,
                )
            )
        for facade_id, facade in facades.items():
            if facade_id in known_facades:
                continue
            known_facades.add(facade_id)
            entities.append(FacadeSunSensor(coordinator, facade_id, facade.name))
            entities.append(
                FacadeSunTimeSensor(coordinator, facade_id, facade.name, is_entry=True)
            )
            entities.append(
                FacadeSunTimeSensor(coordinator, facade_id, facade.name, is_entry=False)
            )
        return entities

    async_add_entities(
        [
            *_new_entities(),
            *(
                CoversInStatusSensor(coordinator, entry.entry_id, status)
                for status in COUNTED_STATUSES
            ),
        ]
    )

    @callback
    def _async_add_new() -> None:
        """Add sensors for covers/facades added at runtime (panel/import)."""
        if entities := _new_entities():
            async_add_entities(entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_add_new))


def _cover_device_info(coordinator: CoverAutomaticCoordinator, cover_entity_id: str, cover_name: str) -> dict[str, Any]:
    """Device of a managed cover (shared by all its entities)."""
    return {
        "identifiers": {(DOMAIN, cover_entity_id)},
        "name": f"CoverAutomatic {cover_name}",
        "manufacturer": "CoverAutomatic",
        "model": i18n.text(coordinator.hass, "model_cover"),
    }


def _controller_device_info(coordinator: CoverAutomaticCoordinator, entry_id: str) -> dict[str, Any]:
    """Device of the integration itself (global entities)."""
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "CoverAutomatic",
        "manufacturer": "CoverAutomatic",
        "model": i18n.text(coordinator.hass, "model_controller"),
    }


def _timestamp(value: Any) -> datetime | None:
    """Unix timestamp -> aware datetime (None when unset/invalid)."""
    if value is None:
        return None
    try:
        return dt_util.utc_from_timestamp(float(value))
    except (TypeError, ValueError, OverflowError, OSError):
        return None


class _CoverSensorBase(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Common base of the per-cover sensors."""

    _attr_has_entity_name = True
    _suffix = ""

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_{self._suffix}"
        self._attr_device_info = _cover_device_info(coordinator, cover_entity_id, cover_name)

    @property
    def _live(self) -> dict[str, Any]:
        return self.coordinator.get_cover_live(self._cover_entity_id)


class CoverAutomaticStatusSensor(_CoverSensorBase):
    """Sensor showing cover automation status.

    Its attributes gather everything the dashboard card needs for one cover.
    """

    _attr_translation_key = "status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [status.value for status in CoverStatus]
    _suffix = "status"

    @property
    def native_value(self) -> str:
        """Return the status."""
        status = self.coordinator.get_cover_status(self._cover_entity_id)
        return status.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Cover, rule, positions and pause info (used by the dashboard card)."""
        live = self._live
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        pause_end = _timestamp(live.get("pause_until"))
        last_change = _timestamp(live.get("last_change"))
        switch_id = er.async_get(self.hass).async_get_entity_id(
            "switch", DOMAIN, f"{DOMAIN}_{self._cover_entity_id}_auto"
        ) if self.hass else None
        return {
            "cover_entity_id": self._cover_entity_id,
            "cover_name": cover.name if cover else None,
            "auto_enabled": cover.auto_enabled if cover else False,
            "auto_switch": switch_id,
            "inverted": cover.inverted if cover else False,
            "position": self.coordinator.get_logical_position(self._cover_entity_id),
            "target_position": live.get("target_position"),
            "rule": live.get("rule_name"),
            "rule_id": live.get("rule_id"),
            "safety_rule": live.get("safety", False),
            "comfort_mode": live.get("comfort_mode"),
            "pause_until": pause_end.isoformat() if pause_end else None,
            "last_change": last_change.isoformat() if last_change else None,
        }

    @property
    def icon(self) -> str:
        """Return icon based on status."""
        status = self.coordinator.get_cover_status(self._cover_entity_id)
        return _STATUS_ICONS.get(status, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the winning rule and its target position (None when no rule applies)."""
        live = self.coordinator.get_live_cover(self._cover_entity_id) or {}
        return {
            "rule_id": live.get("rule_id"),
            "rule_name": live.get("rule_name"),
            "target_position": live.get("target_position"),
        }


class CoverRuleSensor(_CoverSensorBase):
    """Name of the rule currently driving the cover (None = no rule)."""

    _attr_translation_key = "active_rule"
    _attr_icon = "mdi:script-text-outline"
    _suffix = "rule"

    @property
    def native_value(self) -> str:
        """Rule name, or the translated 'none' text."""
        # HA rejects states longer than 255 characters
        return (self._live.get("rule_name") or i18n.text(self.hass, "no_rule"))[:255]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Rule id, its target and whether it is a safety rule."""
        live = self._live
        return {
            "rule_id": live.get("rule_id"),
            "target_position": live.get("target_position"),
            "safety_rule": live.get("safety", False),
        }


class CoverTargetPositionSensor(_CoverSensorBase):
    """Position requested by the active rule (rules' scale, %)."""

    _attr_translation_key = "target_position"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:target"
    _suffix = "target"

    @property
    def native_value(self) -> int | None:
        """Target position, None without an active rule."""
        return self._live.get("target_position")


class CoverPositionSensor(_CoverSensorBase):
    """Current position on the rules' scale (inverted covers mirrored)."""

    _attr_translation_key = "position"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:window-shutter-settings"
    _suffix = "position"

    @property
    def native_value(self) -> int | None:
        """Logical current position."""
        return self.coordinator.get_logical_position(self._cover_entity_id)


class CoverComfortSensor(_CoverSensorBase):
    """Comfort mode of the cover's room (heating / neutral / cooling)."""

    _attr_translation_key = "comfort_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [mode.value for mode in ComfortMode]
    _attr_icon = "mdi:home-thermometer"
    _suffix = "comfort"

    @property
    def native_value(self) -> str | None:
        """Comfort mode, None without an indoor temperature."""
        return self._live.get("comfort_mode")


class CoverPauseEndSensor(_CoverSensorBase):
    """End of the current pause (None when not paused)."""

    _attr_translation_key = "pause_end"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:timer-pause-outline"
    _suffix = "pause_end"

    @property
    def native_value(self) -> datetime | None:
        """Pause end, only while the cover is paused."""
        if self.coordinator.get_cover_status(self._cover_entity_id) != CoverStatus.PAUSED:
            return None
        return _timestamp(self._live.get("pause_until"))


# Statuses counted by the global "covers in status" sensors
COUNTED_STATUSES: tuple[CoverStatus, ...] = (
    CoverStatus.PAUSED,
    CoverStatus.MANUAL,
    CoverStatus.LOCKED,
)


class CoversInStatusSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Number of covers in a status (paused / manual / locked), names as attribute."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        entry_id: str,
        status: CoverStatus,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._status = status
        self._attr_translation_key = f"covers_{status.value}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_covers_{status.value}"
        self._attr_device_info = _controller_device_info(coordinator, entry_id)
        self._attr_icon = _STATUS_ICONS.get(status)

    def _matching(self) -> list[tuple[str, str]]:
        return [
            (entity_id, cover.name)
            for entity_id, cover in self.coordinator.storage.covers.items()
            if self.coordinator.get_cover_status(entity_id) == self._status
        ]

    @property
    def native_value(self) -> int:
        """How many covers are in this status."""
        return len(self._matching())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Names and entity ids of those covers."""
        matching = self._matching()
        return {
            "covers": [name for _, name in matching],
            "entity_ids": [entity_id for entity_id, _ in matching],
        }


class FacadeSunSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing if sun is on facade."""

    _attr_has_entity_name = True
    _attr_translation_key = "sun_on_facade"
    # ENUM so the frontend shows the translated state (e.g. "Oui"/"Non")
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["on", "off"]

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
            # Name translated by HA ("device.facade.name" in translations)
            "translation_key": "facade",
            "translation_placeholders": {"name": facade_name},
            "manufacturer": "CoverAutomatic",
            "model": i18n.text(coordinator.hass, "model_facade"),
        }

    @property
    def native_value(self) -> str | None:
        """Return if sun is on facade."""
        if self.coordinator.data:
            facades = self.coordinator.data.get("facades", {})
            facade_data = facades.get(self._facade_id)
            if facade_data is None:
                return None
            return "on" if facade_data.get("sun_on_facade", False) else "off"
        return None

    @property
    def icon(self) -> str:
        """Return icon based on sun status."""
        if self.native_value == "on":
            return "mdi:white-balance-sunny"
        return "mdi:weather-night"


class FacadeSunTimeSensor(CoordinatorEntity[CoverAutomaticCoordinator], SensorEntity):
    """Sensor showing when sun enters or exits a facade."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        facade_id: str,
        facade_name: str,
        *,
        is_entry: bool,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._facade_id = facade_id
        self._is_entry = is_entry
        suffix = "sun_entry" if is_entry else "sun_exit"
        self._attr_translation_key = f"{suffix}_time"
        self._attr_unique_id = f"{DOMAIN}_facade_{facade_id}_{suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"facade_{facade_id}")},
            # Name translated by HA ("device.facade.name" in translations)
            "translation_key": "facade",
            "translation_placeholders": {"name": facade_name},
            "manufacturer": "CoverAutomatic",
            "model": i18n.text(coordinator.hass, "model_facade"),
        }

    @property
    def native_value(self) -> str | None:
        """Return sun entry/exit time for facade."""
        facade = self.coordinator.storage.facades.get(self._facade_id)
        if facade is None:
            return None
        try:
            entry_time, exit_time = get_facade_sun_times(self.hass, facade)
        except Exception:
            _LOGGER.warning(
                "Failed to calculate sun times for facade %s",
                self._facade_id,
                exc_info=True,
            )
            return None
        return entry_time if self._is_entry else exit_time

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:weather-sunset-up" if self._is_entry else "mdi:weather-sunset-down"
