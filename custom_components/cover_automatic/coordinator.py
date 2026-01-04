"""Data update coordinator for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .engine import RuleEngine
from .models import CoverConfig, CoverStatus
from .storage import CoverAutomaticStorage
from .sun import SUN_ENTITY_ID

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant

_LOGGER = logging.getLogger(__name__)


class CoverAutomaticCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data updates and rule evaluation."""

    def __init__(
        self, hass: HomeAssistant, storage: CoverAutomaticStorage, scan_interval: int = DEFAULT_SCAN_INTERVAL
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.storage = storage
        self.engine = RuleEngine(hass, storage)
        self._tracked_entities: set[str] = set()
        self._unsub_state_change: list[Any] = []
        self._cover_states: dict[str, CoverStatus] = {}
        self._last_positions: dict[str, int | None] = {}

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self.storage.async_load()
        await self._async_setup_default_scenarios()
        self._setup_state_tracking()

    async def _async_setup_default_scenarios(self) -> None:
        """Create default scenarios if none exist."""
        if not self.storage.scenarios:
            from .models import Scenario

            defaults = [
                Scenario(
                    id="everyday",
                    name="Everyday",
                    icon="mdi:home",
                ),
                Scenario(
                    id="summer",
                    name="Summer",
                    icon="mdi:white-balance-sunny",
                ),
                Scenario(
                    id="winter",
                    name="Winter",
                    icon="mdi:snowflake",
                ),
                Scenario(
                    id="vacation",
                    name="Vacation",
                    icon="mdi:airplane",
                ),
                Scenario(
                    id="cinema",
                    name="Cinema",
                    icon="mdi:movie",
                ),
                Scenario(
                    id="manual",
                    name="Manual",
                    icon="mdi:hand-back-right",
                ),
            ]
            for scenario in defaults:
                await self.storage.async_add_scenario(scenario)

    def _setup_state_tracking(self, full_refresh: bool = False) -> None:
        """Set up state change tracking for relevant entities.

        Args:
            full_refresh: If True, remove all existing listeners and re-register.
                         If False, only add listeners for new entities.
        """
        if full_refresh:
            # Remove all existing listeners
            for unsub in self._unsub_state_change:
                unsub()
            self._unsub_state_change.clear()
            self._tracked_entities.clear()

            # Cleanup orphaned entries from runtime state dicts
            current_covers = set(self.storage._data.get("covers", {}).keys())
            orphaned_states = set(self._cover_states.keys()) - current_covers
            orphaned_positions = set(self._last_positions.keys()) - current_covers
            for entity_id in orphaned_states:
                del self._cover_states[entity_id]
            for entity_id in orphaned_positions:
                del self._last_positions[entity_id]

        entities_to_track: set[str] = {SUN_ENTITY_ID}

        for entity_id, cover_data in self.storage._data.get("covers", {}).items():
            entities_to_track.add(entity_id)
            if lock_sensor := cover_data.get("lock_sensor"):
                entities_to_track.add(lock_sensor)
            if vent_sensor := cover_data.get("vent_sensor"):
                entities_to_track.add(vent_sensor)

        if self.storage.outdoor_temp_sensor:
            entities_to_track.add(self.storage.outdoor_temp_sensor)

        if self.storage.indoor_temp_sensor:
            entities_to_track.add(self.storage.indoor_temp_sensor)

        if self.storage.weather_entity:
            entities_to_track.add(self.storage.weather_entity)

        for rule_data in self.storage._data.get("rules", {}).values():
            for condition in rule_data.get("conditions", []):
                if sensor := condition.get("params", {}).get("sensor"):
                    entities_to_track.add(sensor)
                if entity := condition.get("params", {}).get("entity"):
                    entities_to_track.add(entity)

        new_entities = entities_to_track - self._tracked_entities

        if new_entities:
            unsub = async_track_state_change_event(
                self.hass,
                list(new_entities),
                self._async_on_state_change,
            )
            self._unsub_state_change.append(unsub)
            self._tracked_entities.update(new_entities)

    def refresh_state_tracking(self) -> None:
        """Refresh state tracking after configuration changes.

        Performs a full refresh to ensure removed entities are no longer tracked.
        """
        self._setup_state_tracking(full_refresh=True)

    def _get_covers_by_sensor(self, sensor_id: str) -> tuple[list[str], list[str]]:
        """Get cover entity IDs that use a specific sensor.

        Returns:
            Tuple of (lock_covers, vent_covers) - covers using this as lock/vent sensor.
        """
        lock_covers = []
        vent_covers = []
        for entity_id, cover_data in self.storage._data.get("covers", {}).items():
            if cover_data.get("lock_sensor") == sensor_id:
                lock_covers.append(entity_id)
            if cover_data.get("vent_sensor") == sensor_id:
                vent_covers.append(entity_id)
        return lock_covers, vent_covers

    @callback
    def _async_on_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if entity_id in self.storage._data.get("covers", {}):
            self._handle_cover_state_change(entity_id, old_state, new_state)
        else:
            lock_covers, vent_covers = self._get_covers_by_sensor(entity_id)
            if lock_covers or vent_covers:
                self._handle_contact_sensor_change(
                    entity_id, lock_covers, vent_covers, old_state, new_state
                )
            else:
                self.hass.async_create_task(self.async_request_refresh())

    def _is_lock_sensor_open(self, cover_raw: dict[str, Any]) -> bool:
        """Check if the lock sensor for a cover is open."""
        lock_sensor = cover_raw.get("lock_sensor")
        if not lock_sensor:
            return False
        sensor_state = self.hass.states.get(lock_sensor)
        if sensor_state is None or not hasattr(sensor_state, "state"):
            return False
        return sensor_state.state in ("on", "open", "true", "1")

    def _handle_contact_sensor_change(
        self,
        sensor_id: str,
        lock_covers: list[str],
        vent_covers: list[str],
        old_state: Any,
        new_state: Any,
    ) -> None:
        """Handle contact sensor state changes (lock or vent)."""
        if new_state is None or not hasattr(new_state, "state"):
            return

        is_open = new_state.state in ("on", "open", "true", "1")

        # Handle lock sensor covers (window open -> fully open)
        # Lock sensor has priority over vent sensor
        for cover_id in lock_covers:
            cover_raw = self.storage.get_cover_raw(cover_id)
            if cover_raw is None:
                continue

            current_status = self._cover_states.get(cover_id, CoverStatus.AUTO)

            if is_open and current_status != CoverStatus.LOCKED:
                self._lock_cover(cover_id, cover_raw.get("lock_position", 100))
            elif not is_open and current_status == CoverStatus.LOCKED:
                # Only unlock if vent sensor is also not open
                if not self._is_vent_sensor_open(cover_raw):
                    self._unlock_cover(cover_id)
                else:
                    # Lock sensor closed but vent still open -> switch to vent position
                    self._lock_cover(cover_id, cover_raw.get("vent_position", 30))

        # Handle vent sensor covers (vent open -> ventilation position)
        for cover_id in vent_covers:
            cover_raw = self.storage.get_cover_raw(cover_id)
            if cover_raw is None:
                continue

            current_status = self._cover_states.get(cover_id, CoverStatus.AUTO)

            # Skip if lock sensor is open (lock has priority)
            if self._is_lock_sensor_open(cover_raw):
                continue

            if is_open and current_status != CoverStatus.LOCKED:
                self._lock_cover(cover_id, cover_raw.get("vent_position", 30))
            elif not is_open and current_status == CoverStatus.LOCKED:
                self._unlock_cover(cover_id)

    def _is_vent_sensor_open(self, cover_raw: dict[str, Any]) -> bool:
        """Check if the vent sensor for a cover is open."""
        vent_sensor = cover_raw.get("vent_sensor")
        if not vent_sensor:
            return False
        sensor_state = self.hass.states.get(vent_sensor)
        if sensor_state is None or not hasattr(sensor_state, "state"):
            return False
        return sensor_state.state in ("on", "open", "true", "1")

    def _lock_cover(self, entity_id: str, lock_position: int) -> None:
        """Lock a cover due to open contact sensor."""
        self._cover_states[entity_id] = CoverStatus.LOCKED
        self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)

        # Handle inverted covers
        cover_raw = self.storage.get_cover_raw(entity_id)
        actual_position = lock_position
        if cover_raw and cover_raw.get("inverted", False):
            actual_position = 100 - lock_position

        _LOGGER.debug("Locking cover %s at position %s (actual: %s)", entity_id, lock_position, actual_position)

        self.hass.async_create_task(
            self.hass.services.async_call(
                "cover",
                "set_cover_position",
                {"entity_id": entity_id, "position": actual_position},
                blocking=False,
            )
        )
        self.async_set_updated_data(self.data)

    def _unlock_cover(self, entity_id: str) -> None:
        """Unlock a cover when contact sensor closes."""
        _LOGGER.debug("Unlocking cover %s", entity_id)
        self._cover_states[entity_id] = CoverStatus.AUTO
        self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
        self.hass.async_create_task(self.async_request_refresh())

    def _handle_cover_state_change(
        self, entity_id: str, old_state: Any, new_state: Any
    ) -> None:
        """Handle cover position changes to detect manual overrides."""
        if new_state is None:
            return

        cover = self.storage.covers.get(entity_id)
        if cover is None:
            return

        expected_position = self._last_positions.get(entity_id)

        try:
            current_position = int(new_state.attributes.get("current_position", 0))
        except (ValueError, TypeError):
            return

        if expected_position is not None and current_position != expected_position:
            if cover.auto_enabled and self._cover_states.get(entity_id) == CoverStatus.AUTO:
                _LOGGER.debug(
                    "Manual override detected for %s (expected %s, got %s)",
                    entity_id,
                    expected_position,
                    current_position,
                )
                self._pause_cover(cover)

    def _pause_cover(self, cover: CoverConfig) -> None:
        """Pause automation for a cover."""
        self._cover_states[cover.entity_id] = CoverStatus.PAUSED
        pause_until = dt_util.now().timestamp() + (cover.pause_duration * 60)
        self.storage.update_cover_status(
            cover.entity_id, CoverStatus.PAUSED.value, pause_until
        )
        self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str) -> None:
        """Resume automation for a cover."""
        if self.storage.get_cover_raw(entity_id):
            self._cover_states[entity_id] = CoverStatus.AUTO
            self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
            self.async_set_updated_data(self.data)

    def get_cover_status(self, entity_id: str) -> CoverStatus:
        """Get automation status for a cover."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None:
            return CoverStatus.MANUAL

        if not cover_raw.get("auto_enabled", True):
            return CoverStatus.MANUAL

        # Check lock sensor state (window contact)
        if lock_sensor := cover_raw.get("lock_sensor"):
            sensor_state = self.hass.states.get(lock_sensor)
            if sensor_state and sensor_state.state in ("on", "open", "true", "1"):
                if self._cover_states.get(entity_id) != CoverStatus.LOCKED:
                    self._cover_states[entity_id] = CoverStatus.LOCKED
                    self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)
                return CoverStatus.LOCKED

        # Check vent sensor state (ventilation contact)
        if vent_sensor := cover_raw.get("vent_sensor"):
            sensor_state = self.hass.states.get(vent_sensor)
            if sensor_state and sensor_state.state in ("on", "open", "true", "1"):
                if self._cover_states.get(entity_id) != CoverStatus.LOCKED:
                    self._cover_states[entity_id] = CoverStatus.LOCKED
                    self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)
                return CoverStatus.LOCKED

        # If was locked but both sensors now closed, unlock
        if self._cover_states.get(entity_id) == CoverStatus.LOCKED:
            self._cover_states[entity_id] = CoverStatus.AUTO
            self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)

        status = self._cover_states.get(entity_id, CoverStatus.AUTO)

        if status == CoverStatus.PAUSED:
            pause_until = cover_raw.get("pause_until")
            if pause_until and dt_util.now().timestamp() > pause_until:
                self._cover_states[entity_id] = CoverStatus.AUTO
                self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
                return CoverStatus.AUTO

        return status

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and evaluate rules."""
        result: dict[str, Any] = {
            "covers": {},
            "facades": {},
            "scenario": self.storage.active_scenario,
        }

        for facade_id, facade in self.storage.facades.items():
            from .sun import is_sun_on_facade

            result["facades"][facade_id] = {
                "sun_on_facade": is_sun_on_facade(self.hass, facade),
            }

        for entity_id, cover in self.storage.covers.items():
            status = self.get_cover_status(entity_id)
            target_position: int | None = None

            if status == CoverStatus.AUTO:
                target_position = self.engine.evaluate_cover(cover)
                if target_position is not None:
                    self._last_positions[entity_id] = target_position

            result["covers"][entity_id] = {
                "status": status.value,
                "target_position": target_position,
                "facade_id": cover.facade_id,
            }

        # Store result first so async_apply_positions can use it
        self.data = result

        # Apply calculated positions to covers
        await self.async_apply_positions()

        return result

    async def async_apply_positions(self) -> None:
        """Apply calculated positions to covers with hysteresis."""
        if not self.data:
            return

        now = dt_util.now().timestamp()

        for entity_id, cover_data in self.data.get("covers", {}).items():
            if cover_data["status"] != CoverStatus.AUTO.value:
                continue

            target = cover_data.get("target_position")
            if target is None:
                continue

            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            state = self.hass.states.get(entity_id)
            if state is None:
                continue

            try:
                current = int(state.attributes.get("current_position", 0))
            except (ValueError, TypeError):
                continue

            # Handle inverted covers (100% = closed)
            if cover_raw.get("inverted", False):
                target = 100 - target

            # Check hysteresis: minimum position change
            min_change = cover_raw.get("min_position_change", 5)
            position_diff = abs(current - target)
            if position_diff < min_change and position_diff > 0:
                _LOGGER.debug(
                    "Skipping %s: position change %d < min %d",
                    entity_id, position_diff, min_change
                )
                continue

            # Check hysteresis: minimum time between changes
            min_time = cover_raw.get("min_time_between_changes", 300)
            last_change = cover_raw.get("last_position_change")
            if last_change and (now - last_change) < min_time:
                _LOGGER.debug(
                    "Skipping %s: only %ds since last change (min %ds)",
                    entity_id, int(now - last_change), min_time
                )
                continue

            if current != target:
                _LOGGER.debug("Setting %s to position %s", entity_id, target)
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=False,
                )
                # Update last change timestamp
                self.storage.update_cover_last_change(entity_id, now)

    def async_shutdown(self) -> None:
        """Shut down coordinator."""
        for unsub in self._unsub_state_change:
            unsub()
        self._unsub_state_change.clear()
