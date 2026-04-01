"""Data update coordinator for CoverAutomatic."""
from __future__ import annotations

import asyncio
import logging
import time as time_mod
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    BINARY_SENSOR_ON_STATES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOG_EVENT_POSITION,
    LOG_EVENT_RULE,
    LOG_EVENT_STATUS,
    LOG_EVENT_WIND,
    TILT_COMMAND_DELAY,
    TILT_FEATURE_FLAG,
)
from .engine import RuleEngine
from .models import CoverConfig, CoverStatus
from .storage import ActivityLogStorage, CoverAutomaticStorage
from .sun import SUN_ENTITY_ID, is_sun_on_facade

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Tolerance for manual override detection (positions)
MANUAL_OVERRIDE_TOLERANCE = 2

# Seconds to ignore position changes after our own commands
SETTLE_TIME = 30


class CoverAutomaticCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data updates and rule evaluation."""

    def __init__(
        self,
        hass: HomeAssistant,
        storage: CoverAutomaticStorage,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=config_entry,
        )
        self.storage = storage
        self.engine = RuleEngine(hass, storage)
        self._tracked_entities: set[str] = set()
        self._unsub_state_change: list[Any] = []
        self._cover_states: dict[str, CoverStatus] = {}
        self._last_positions: dict[str, int | None] = {}
        self._last_tilt_positions: dict[str, int | None] = {}
        self._tilt_tasks: dict[str, asyncio.Task[None]] = {}
        self._last_command_time: dict[str, float] = {}
        self._pre_lock_states: dict[str, CoverStatus] = {}
        self._wind_protected: bool = False
        self._hysteresis_info: dict[str, str | None] = {}
        self._last_matching_rules: dict[str, str | None] = {}
        self.log_storage: ActivityLogStorage | None = None

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self.storage.async_load()
        self._restore_cover_states()
        await self._async_setup_default_scenarios()
        self._setup_state_tracking()

    def _restore_cover_states(self) -> None:
        """Restore cover states from persisted storage data.

        Only restores PAUSED (with unexpired timer). All other statuses start
        as AUTO and get re-derived from sensor states by _sync_cover_statuses.
        """
        for entity_id, cover_data in self.storage._data.get("covers", {}).items():
            stored_status = cover_data.get("status", "auto")
            if stored_status == CoverStatus.PAUSED.value:
                pause_until = cover_data.get("pause_until")
                if pause_until and dt_util.now().timestamp() < pause_until:
                    self._cover_states[entity_id] = CoverStatus.PAUSED
                    continue
            # Reset everything else to AUTO (lock/vent re-detected from sensors)
            if stored_status != CoverStatus.AUTO.value:
                _LOGGER.debug("[%s] Startup: reset %s -> AUTO", entity_id, stored_status)
            self._cover_states[entity_id] = CoverStatus.AUTO
            if stored_status != CoverStatus.AUTO.value:
                self.storage.update_cover_status(
                    entity_id, CoverStatus.AUTO.value, None
                )

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
            for state_dict in (
                self._cover_states,
                self._last_positions,
                self._last_tilt_positions,
                self._pre_lock_states,
                self._last_command_time,
                self._tilt_tasks,
            ):
                orphaned = set(state_dict.keys()) - current_covers
                for entity_id in orphaned:
                    value = state_dict.pop(entity_id)
                    if isinstance(value, asyncio.Task) and not value.done():
                        value.cancel()

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

        if self.storage.wind_sensor:
            entities_to_track.add(self.storage.wind_sensor)

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

    def _get_wind_speed(self) -> float | None:
        """Get current wind speed from sensor."""
        sensor_id = self.storage.wind_sensor
        if not sensor_id:
            return None
        state = self.hass.states.get(sensor_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _check_wind_protection(self) -> None:
        """Check wind sensor and update global wind protection state.

        Uses hysteresis: activates at threshold, deactivates at
        threshold - hysteresis to prevent oscillation in gusty wind.
        """
        wind_speed = self._get_wind_speed()
        if wind_speed is None:
            if self._wind_protected:
                _LOGGER.warning("Wind sensor unavailable while WIND_PROTECTED, keeping protection active")
            return

        threshold = self.storage.wind_speed_threshold
        hysteresis = self.storage.wind_speed_hysteresis

        if not self._wind_protected and wind_speed >= threshold > 0:
            _LOGGER.info("Wind protection ACTIVATED (%.1f >= %.1f)", wind_speed, threshold)
            self._wind_protected = True
            self._log(LOG_EVENT_WIND, None, f"Activated ({wind_speed:.1f} >= {threshold:.1f})")
            self._activate_wind_protection()
        elif self._wind_protected and wind_speed <= threshold - hysteresis:
            _LOGGER.info("Wind protection DEACTIVATED (%.1f <= %.1f)", wind_speed, threshold - hysteresis)
            self._wind_protected = False
            self._log(LOG_EVENT_WIND, None, f"Deactivated ({wind_speed:.1f} <= {threshold - hysteresis:.1f})")
            self._deactivate_wind_protection()

    def _activate_wind_protection(self) -> None:
        """Set all covers to WIND_PROTECTED and move to fully open."""
        for entity_id in self.storage._data.get("covers", {}):
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if prev not in (CoverStatus.WIND_PROTECTED,):
                if entity_id not in self._pre_lock_states:
                    self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev

            self._cover_states[entity_id] = CoverStatus.WIND_PROTECTED
            self.storage.update_cover_status(entity_id, CoverStatus.WIND_PROTECTED.value, None)

            # Move to fully open (position 100)
            inverted = cover_raw.get("inverted", False)
            actual_position = 0 if inverted else 100
            self._last_positions[entity_id] = actual_position
            self._last_command_time[entity_id] = time_mod.monotonic()
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "cover", "set_cover_position",
                    {"entity_id": entity_id, "position": actual_position},
                    blocking=False,
                )
            )

        if self.data is not None:
            self.async_set_updated_data(self.data)

    def _deactivate_wind_protection(self) -> None:
        """Remove WIND_PROTECTED status from all covers, re-derive from sensors."""
        for entity_id in self.storage._data.get("covers", {}):
            if self._cover_states.get(entity_id) == CoverStatus.WIND_PROTECTED:
                self._cover_states[entity_id] = CoverStatus.AUTO
                self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
                self._pre_lock_states.pop(entity_id, None)
                self._update_last_position_from_state(entity_id)

        if self.data is not None:
            self.async_set_updated_data(self.data)

    @callback
    def _handle_wind_sensor_change(self, new_state: Any) -> None:
        """Handle wind sensor state change."""
        if new_state is None:
            return
        if new_state.state in ("unavailable", "unknown"):
            _LOGGER.warning("Wind sensor unavailable, keeping current protection state")
            return
        self._check_wind_protection()
        self.hass.async_create_task(self.async_request_refresh())

    @callback
    def _async_on_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if entity_id in self.storage._data.get("covers", {}):
            self._handle_cover_state_change(entity_id, old_state, new_state)
        elif entity_id == self.storage.wind_sensor:
            self._handle_wind_sensor_change(new_state)
        else:
            lock_covers, vent_covers = self._get_covers_by_sensor(entity_id)
            if lock_covers or vent_covers:
                self._handle_contact_sensor_change(
                    entity_id, lock_covers, vent_covers, old_state, new_state
                )
            else:
                self.hass.async_create_task(self.async_request_refresh())

    def _is_sensor_open(self, cover_raw: dict[str, Any], key: str) -> bool:
        """Check if a binary sensor (lock/vent) for a cover is open."""
        sensor = cover_raw.get(key)
        if not sensor:
            return False
        sensor_state = self.hass.states.get(sensor)
        if sensor_state is None:
            return False
        return sensor_state.state in BINARY_SENSOR_ON_STATES

    def _handle_contact_sensor_change(
        self,
        sensor_id: str,
        lock_covers: list[str],
        vent_covers: list[str],
        old_state: Any,
        new_state: Any,
    ) -> None:
        """Handle contact sensor state changes (lock or vent)."""
        if new_state is None:
            return

        if new_state.state in ("unavailable", "unknown"):
            _LOGGER.warning("[%s] Sensor unavailable, ignoring state change", sensor_id)
            return

        is_open = new_state.state in BINARY_SENSOR_ON_STATES

        # Cache sensor states to avoid repeated hass.states.get() calls
        sensor_state_cache: dict[str, bool] = {}

        def is_sensor_open_cached(cover_raw: dict[str, Any], key: str) -> bool:
            sensor = cover_raw.get(key)
            if not sensor:
                return False
            if sensor not in sensor_state_cache:
                state = self.hass.states.get(sensor)
                sensor_state_cache[sensor] = (
                    state is not None and state.state in BINARY_SENSOR_ON_STATES
                )
            return sensor_state_cache[sensor]

        # Handle lock sensor covers (window open -> fully open)
        # Lock sensor always has priority - override even if already locked by vent
        for cover_id in lock_covers:
            cover_raw = self.storage.get_cover_raw(cover_id)
            if cover_raw is None:
                continue

            if is_open:
                lock_pos = cover_raw.get("lock_position", 100)
                current = self._get_current_position(cover_id)
                if current is None or current < lock_pos:
                    _LOGGER.info("[%s] Lock sensor open -> LOCKED at %d%%", cover_id, lock_pos)
                    self._lock_cover(cover_id, lock_pos, lock_tilt=cover_raw.get("lock_tilt_position"))
                else:
                    _LOGGER.info("[%s] Lock sensor open -> LOCKED (already at %d%%)", cover_id, current)
                    if cover_id not in self._pre_lock_states:
                        prev = self._cover_states.get(cover_id, CoverStatus.AUTO)
                        self._pre_lock_states[cover_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
                    self._cover_states[cover_id] = CoverStatus.LOCKED
                    self.storage.update_cover_status(cover_id, CoverStatus.LOCKED.value, None)
                    self._update_last_position_from_state(cover_id)
                    if self.data is not None:
                        self.async_set_updated_data(self.data)
            elif self._cover_states.get(cover_id) == CoverStatus.LOCKED:
                # Only unlock if vent sensor is also not open
                if not is_sensor_open_cached(cover_raw, "vent_sensor"):
                    _LOGGER.info("[%s] Lock sensor closed -> unlocking", cover_id)
                    self._unlock_cover(cover_id)
                else:
                    _LOGGER.info("[%s] Lock sensor closed, vent still open -> VENTING", cover_id)
                    # Move to vent position if currently below it
                    vent_pos = cover_raw.get("vent_position", 30)
                    current = self._get_current_position(cover_id)
                    if current is not None and current < vent_pos:
                        inverted = cover_raw.get("inverted", False)
                        actual = (100 - vent_pos) if inverted else vent_pos
                        self._last_positions[cover_id] = actual
                        self._last_command_time[cover_id] = time_mod.monotonic()
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                "cover", "set_cover_position",
                                {"entity_id": cover_id, "position": actual},
                                blocking=False,
                            )
                        )
                    self._pre_lock_states.pop(cover_id, None)
                    self._cover_states[cover_id] = CoverStatus.VENTING
                    self.storage.update_cover_status(cover_id, CoverStatus.VENTING.value, None)
                    if self.data is not None:
                        self.async_set_updated_data(self.data)

        # Handle vent sensor covers (vent open -> min position, automation continues)
        for cover_id in vent_covers:
            cover_raw = self.storage.get_cover_raw(cover_id)
            if cover_raw is None:
                continue

            # Skip if lock sensor is open (lock has priority)
            if is_sensor_open_cached(cover_raw, "lock_sensor"):
                continue

            current_status = self._cover_states.get(cover_id, CoverStatus.AUTO)

            if is_open and current_status not in (CoverStatus.LOCKED, CoverStatus.VENTING):
                vent_pos = cover_raw.get("vent_position", 30)
                current = self._get_current_position(cover_id)
                # Move up to vent_position if currently below it
                if current is not None and current < vent_pos:
                    _LOGGER.info("[%s] Vent sensor open -> VENTING, moving %d%% -> %d%%", cover_id, current, vent_pos)
                    inverted = cover_raw.get("inverted", False)
                    actual = (100 - vent_pos) if inverted else vent_pos
                    self._last_positions[cover_id] = actual
                    self._last_command_time[cover_id] = time_mod.monotonic()
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "cover", "set_cover_position",
                            {"entity_id": cover_id, "position": actual},
                            blocking=False,
                        )
                    )
                else:
                    _LOGGER.info(
                        "[%s] Vent sensor open -> VENTING (at %d%%, min %d%%)",
                        cover_id, current or 0, vent_pos,
                    )
                self._cover_states[cover_id] = CoverStatus.VENTING
                self.storage.update_cover_status(cover_id, CoverStatus.VENTING.value, None)
                if self.data is not None:
                    self.async_set_updated_data(self.data)
            elif not is_open and current_status == CoverStatus.VENTING:
                _LOGGER.info("[%s] Vent sensor closed -> AUTO", cover_id)
                self._cover_states[cover_id] = CoverStatus.AUTO
                self.storage.update_cover_status(cover_id, CoverStatus.AUTO.value, None)
                if self.data is not None:
                    self.async_set_updated_data(self.data)

    def _get_current_position(self, entity_id: str) -> int | None:
        """Get current cover position (handles inverted covers)."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            pos = int(state.attributes.get("current_position", 0))
        except (ValueError, TypeError):
            return None
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw and cover_raw.get("inverted", False):
            pos = 100 - pos
        return pos

    def _lock_cover(
        self, entity_id: str, lock_position: int, *, lock_tilt: int | None = None
    ) -> None:
        """Lock a cover due to open contact sensor."""
        # Save previous state for restoration after unlock
        # If paused, save as AUTO (pause cancelled by lock priority)
        if entity_id not in self._pre_lock_states:
            prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
            self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
        self._cover_states[entity_id] = CoverStatus.LOCKED
        prev_val = self._pre_lock_states.get(entity_id, CoverStatus.AUTO).value
        self._log(LOG_EVENT_STATUS, entity_id, f"{prev_val} -> locked")
        self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)

        # Handle inverted covers
        cover_raw = self.storage.get_cover_raw(entity_id)
        actual_position = lock_position
        if cover_raw and cover_raw.get("inverted", False):
            actual_position = 100 - lock_position

        _LOGGER.debug("Locking cover %s at position %s (actual: %s)", entity_id, lock_position, actual_position)

        # Update expected position to prevent false manual override
        self._last_positions[entity_id] = actual_position

        self._last_command_time[entity_id] = time_mod.monotonic()
        self.hass.async_create_task(
            self.hass.services.async_call(
                "cover",
                "set_cover_position",
                {"entity_id": entity_id, "position": actual_position},
                blocking=False,
            )
        )

        # Send tilt command if supported and configured
        if lock_tilt is not None and cover_raw and cover_raw.get("supports_tilt", False):
            actual_tilt = lock_tilt
            if cover_raw.get("inverted_tilt", False):
                actual_tilt = 100 - lock_tilt
            self._last_tilt_positions[entity_id] = actual_tilt
            self._schedule_tilt(entity_id, actual_tilt, TILT_COMMAND_DELAY)

        if self.data is not None:
            self.async_set_updated_data(self.data)

    def _unlock_cover(self, entity_id: str) -> None:
        """Unlock a cover when contact sensor closes."""
        if entity_id not in self._pre_lock_states:
            return

        _LOGGER.debug("Unlocking cover %s", entity_id)
        self._log(LOG_EVENT_STATUS, entity_id, "locked -> unlocked")

        # Restore previous state if was PAUSED and pause not expired
        previous = self._pre_lock_states.pop(entity_id, CoverStatus.AUTO)
        if previous == CoverStatus.PAUSED:
            cover_raw = self.storage.get_cover_raw(entity_id)
            pause_until = cover_raw.get("pause_until") if cover_raw else None
            if pause_until and dt_util.now().timestamp() < pause_until:
                self._cover_states[entity_id] = CoverStatus.PAUSED
                self.storage.update_cover_status(
                    entity_id, CoverStatus.PAUSED.value, pause_until
                )
                # Update expected position to current to prevent false override
                self._update_last_position_from_state(entity_id)
                if self.data is not None:
                    self.async_set_updated_data(self.data)
                return

        # Restore MANUAL if cover was manual before lock
        if previous == CoverStatus.MANUAL:
            self._cover_states[entity_id] = CoverStatus.MANUAL
            self.storage.update_cover_status(
                entity_id, CoverStatus.MANUAL.value, None
            )
            self._update_last_position_from_state(entity_id)
            if self.data is not None:
                self.async_set_updated_data(self.data)
            return

        # Restore VENTING if vent sensor is still open
        if previous == CoverStatus.VENTING:
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw and self._is_sensor_open(cover_raw, "vent_sensor"):
                self._cover_states[entity_id] = CoverStatus.VENTING
                self.storage.update_cover_status(
                    entity_id, CoverStatus.VENTING.value, None
                )
                self._update_last_position_from_state(entity_id)
                if self.data is not None:
                    self.async_set_updated_data(self.data)
                return

        self._cover_states[entity_id] = CoverStatus.AUTO
        self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
        # Update expected position to current to prevent false override
        self._update_last_position_from_state(entity_id)
        self.hass.async_create_task(self.async_request_refresh())

    def _update_last_position_from_state(self, entity_id: str) -> None:
        """Update _last_positions and _last_tilt_positions from current HA state."""
        state = self.hass.states.get(entity_id)
        if state:
            try:
                self._last_positions[entity_id] = int(
                    state.attributes.get("current_position", 0)
                )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid position attribute for %s, resetting tracked position",
                    entity_id,
                )
                self._last_positions[entity_id] = None
            tilt_val = state.attributes.get("current_tilt_position")
            if tilt_val is not None:
                try:
                    self._last_tilt_positions[entity_id] = int(tilt_val)
                except (ValueError, TypeError):
                    self._last_tilt_positions[entity_id] = None

    def _handle_cover_state_change(
        self, entity_id: str, old_state: Any, new_state: Any
    ) -> None:
        """Handle cover position changes to detect manual overrides."""
        if new_state is None:
            return

        cover = self.storage.covers.get(entity_id)
        if cover is None:
            return

        # Ignore manual overrides during wind protection
        if self._wind_protected:
            return

        # Ignore position changes while cover is moving
        if new_state.state in ("opening", "closing"):
            return

        # Ignore position changes during settle time after our own commands
        last_cmd = self._last_command_time.get(entity_id, 0)
        if (time_mod.monotonic() - last_cmd) < SETTLE_TIME:
            return

        expected_position = self._last_positions.get(entity_id)

        try:
            current_position = int(new_state.attributes.get("current_position", 0))
        except (ValueError, TypeError):
            return

        position_mismatch = (
            expected_position is not None
            and abs(current_position - expected_position) > MANUAL_OVERRIDE_TOLERANCE
        )

        # Check tilt mismatch if cover supports tilt
        tilt_mismatch = False
        expected_tilt = self._last_tilt_positions.get(entity_id)
        if expected_tilt is not None:
            current_tilt_val = new_state.attributes.get("current_tilt_position")
            if current_tilt_val is not None:
                try:
                    current_tilt = int(current_tilt_val)
                    if abs(current_tilt - expected_tilt) > MANUAL_OVERRIDE_TOLERANCE:
                        tilt_mismatch = True
                except (ValueError, TypeError):
                    pass

        if position_mismatch or tilt_mismatch:
            if cover.auto_enabled and self._cover_states.get(entity_id) == CoverStatus.AUTO:
                _LOGGER.info(
                    "[%s] Manual override -> PAUSED (expected pos %s, got %s, expected tilt %s)",
                    entity_id,
                    expected_position,
                    current_position,
                    expected_tilt,
                )
                self.pause_cover(cover)

    def pause_cover(self, cover: CoverConfig) -> None:
        """Pause automation for a cover."""
        prev = self._cover_states.get(cover.entity_id, CoverStatus.AUTO)
        self._cover_states[cover.entity_id] = CoverStatus.PAUSED
        if prev != CoverStatus.PAUSED:
            self._log(LOG_EVENT_STATUS, cover.entity_id, f"{prev.value} -> paused")
        duration = cover.pause_duration or self.storage.pause_duration
        pause_until = dt_util.now().timestamp() + (duration * 60)
        self.storage.update_cover_status(
            cover.entity_id, CoverStatus.PAUSED.value, pause_until
        )
        if self.data is not None:
            self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str) -> None:
        """Resume automation for a cover."""
        # Wind protection cannot be overridden manually
        if self._wind_protected:
            return
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw:
            # Don't override LOCKED status if lock/vent sensor is still active
            if self._cover_states.get(entity_id) == CoverStatus.LOCKED:
                if self._is_sensor_open(cover_raw, "lock_sensor") or self._is_sensor_open(cover_raw, "vent_sensor"):
                    return
            self._cover_states[entity_id] = CoverStatus.AUTO
            self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
            if self.data is not None:
                self.async_set_updated_data(self.data)

    def _sync_cover_statuses(self) -> None:
        """Sync cover statuses from sensor states.

        Updates _cover_states and storage for all covers. Called once per
        update cycle to avoid side effects in property accessors.
        Priority: WIND_PROTECTED > LOCKED > VENTING > PAUSED > AUTO > MANUAL.
        """
        # Check wind protection first (global, highest priority)
        self._check_wind_protection()

        for entity_id in self.storage._data.get("covers", {}):
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            # Wind protection has highest priority - skip all other checks
            if self._wind_protected:
                if self._cover_states.get(entity_id) != CoverStatus.WIND_PROTECTED:
                    self._activate_wind_protection()
                continue

            # Check lock sensor state (window contact)
            if self._is_sensor_open(cover_raw, "lock_sensor"):
                if self._cover_states.get(entity_id) != CoverStatus.LOCKED:
                    lock_pos = cover_raw.get("lock_position", 100)
                    current = self._get_current_position(entity_id)
                    if current is None or current < lock_pos:
                        self._lock_cover(entity_id, lock_pos, lock_tilt=cover_raw.get("lock_tilt_position"))
                    else:
                        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
                        self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
                        self._cover_states[entity_id] = CoverStatus.LOCKED
                        self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)
                        self._update_last_position_from_state(entity_id)
                continue

            # Check vent sensor state - also above auto_enabled
            if self._is_sensor_open(cover_raw, "vent_sensor"):
                if self._cover_states.get(entity_id) != CoverStatus.VENTING:
                    vent_pos = cover_raw.get("vent_position", 30)
                    current = self._get_current_position(entity_id)
                    if current is not None and current < vent_pos:
                        inverted = cover_raw.get("inverted", False)
                        actual = (100 - vent_pos) if inverted else vent_pos
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                "cover", "set_cover_position",
                                {"entity_id": entity_id, "position": actual},
                                blocking=False,
                            )
                        )
                    self._cover_states[entity_id] = CoverStatus.VENTING
                    self.storage.update_cover_status(entity_id, CoverStatus.VENTING.value, None)
                continue

            # If was locked/venting but sensors now closed, restore auto
            if self._cover_states.get(entity_id) in (CoverStatus.LOCKED, CoverStatus.VENTING):
                self._unlock_cover(entity_id)
                continue

            if not cover_raw.get("auto_enabled", True):
                self._cover_states[entity_id] = CoverStatus.MANUAL
                continue

            # Check pause expiry
            status = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if status == CoverStatus.PAUSED:
                pause_until = cover_raw.get("pause_until")
                if pause_until and dt_util.now().timestamp() > pause_until:
                    self._cover_states[entity_id] = CoverStatus.AUTO
                    self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)

    def get_cover_status(self, entity_id: str) -> CoverStatus:
        """Get automation status for a cover (read-only, no side effects)."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None:
            return CoverStatus.MANUAL

        if not cover_raw.get("auto_enabled", True):
            return CoverStatus.MANUAL

        return self._cover_states.get(entity_id, CoverStatus.AUTO)

    def get_active_rules(self) -> dict[str, list[str]]:
        """Get currently active rules and their matched covers.

        Returns dict of {rule_id: [cover_entity_ids]}.
        """
        if self.data and "active_rules" in self.data:
            return self.data["active_rules"]
        return {}

    def get_live_cover_data(self) -> dict[str, dict[str, Any]]:
        """Get live runtime data for all covers."""
        result: dict[str, dict[str, Any]] = {}
        if self.data:
            for entity_id, cover_data in self.data.get("covers", {}).items():
                cover_raw = self.storage.get_cover_raw(entity_id)
                pause_until = cover_raw.get("pause_until") if cover_raw else None
                rule_id = cover_data.get("matching_rule_id")
                rule_name = None
                if rule_id:
                    rule = self.storage.rules.get(rule_id)
                    rule_name = rule.name if rule else rule_id
                # Comfort mode from engine cache
                comfort = self.engine._last_comfort_mode.get(entity_id)
                result[entity_id] = {
                    "target_position": cover_data.get("target_position"),
                    "hysteresis": self._hysteresis_info.get(entity_id),
                    "pause_until": pause_until,
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "comfort_mode": comfort.value if comfort else None,
                    "last_change": cover_raw.get("last_position_change") if cover_raw else None,
                }
        return result

    def get_live_facade_data(self) -> dict[str, dict[str, Any]]:
        """Get live runtime data for facades (sun on facade)."""
        if self.data:
            return self.data.get("facades", {})
        return {}

    def _log(
        self, event_type: str, entity_id: str | None = None,
        message: str = "", data: dict[str, Any] | None = None,
    ) -> None:
        """Add an activity log entry if log_storage is available."""
        if self.log_storage:
            self.log_storage.add_entry(event_type, entity_id, message, data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and evaluate rules."""
        # Sync cover statuses from sensors before evaluation
        self._sync_cover_statuses()

        result: dict[str, Any] = {
            "covers": {},
            "facades": {},
            "scenario": self.storage.active_scenario,
        }
        # Track which rules are currently winning for which covers
        active_rules: dict[str, list[str]] = {}

        for facade_id, facade in self.storage.facades.items():
            result["facades"][facade_id] = {
                "sun_on_facade": is_sun_on_facade(self.hass, facade),
            }

        for entity_id, cover in self.storage.covers.items():
            status = self.get_cover_status(entity_id)
            target_position: int | None = None
            target_tilt_position: int | None = None
            matching_rule_id: str | None = None

            if status in (CoverStatus.AUTO, CoverStatus.VENTING) and self.storage.enabled:
                engine_result = self.engine.evaluate_cover(cover)
                if engine_result is not None:
                    target_position = engine_result.position
                    target_tilt_position = engine_result.tilt_position
                    matching_rule_id = engine_result.rule_id
                    if matching_rule_id:
                        active_rules.setdefault(matching_rule_id, []).append(entity_id)

            # Log rule match changes
            prev_rule = self._last_matching_rules.get(entity_id)
            if matching_rule_id != prev_rule:
                self._last_matching_rules[entity_id] = matching_rule_id
                if matching_rule_id:
                    rule_name = self.storage.rules.get(matching_rule_id)
                    rn = rule_name.name if rule_name else matching_rule_id
                    self._log(
                        LOG_EVENT_RULE, entity_id, f"{rn} -> {target_position}%",
                        {"rule_id": matching_rule_id, "position": target_position},
                    )

            result["covers"][entity_id] = {
                "status": status.value,
                "target_position": target_position,
                "target_tilt_position": target_tilt_position,
                "facade_id": cover.facade_id,
                "matching_rule_id": matching_rule_id,
            }

        result["active_rules"] = active_rules

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
            # Use live status from _cover_states instead of snapshot
            status = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if status not in (CoverStatus.AUTO, CoverStatus.VENTING):
                continue

            target = cover_data.get("target_position")
            if target is None:
                self._hysteresis_info[entity_id] = None
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

            # Enforce vent minimum position (logical, before inversion)
            original_target = target
            if status == CoverStatus.VENTING:
                vent_min = cover_raw.get("vent_position", 30)
                if target < vent_min:
                    target = vent_min
                    _LOGGER.debug("[%s] VENTING: clamped %d%% -> %d%% (vent min)", entity_id, original_target, target)

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
                self._hysteresis_info[entity_id] = "position"
                self._last_positions[entity_id] = current
                continue

            # Check hysteresis: minimum time between changes
            min_time = cover_raw.get("min_time_between_changes", 300)
            last_change = cover_raw.get("last_position_change")
            if last_change and (now - last_change) < min_time:
                _LOGGER.debug(
                    "Skipping %s: only %ds since last change (min %ds)",
                    entity_id, int(now - last_change), min_time
                )
                self._hysteresis_info[entity_id] = "time"
                self._last_positions[entity_id] = current
                continue

            # Determine target tilt (if applicable)
            target_tilt = cover_data.get("target_tilt_position")
            supports_tilt = cover_raw.get("supports_tilt", False) and self._supports_tilt(entity_id)
            actual_tilt: int | None = None
            if target_tilt is not None and supports_tilt:
                actual_tilt = target_tilt
                if cover_raw.get("inverted_tilt", False):
                    actual_tilt = 100 - target_tilt

            position_changed = current != target
            if position_changed:
                _LOGGER.info("[%s] Moving %d%% -> %d%%", entity_id, current, target)
                self._hysteresis_info[entity_id] = None
                self._last_positions[entity_id] = target
                self._last_command_time[entity_id] = time_mod.monotonic()
                self._log(
                    LOG_EVENT_POSITION, entity_id, f"{current}% -> {target}%",
                    {"from": current, "to": target, "rule_id": cover_data.get("matching_rule_id")},
                )
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=False,
                )
                self.storage.update_cover_last_change(entity_id, now)
            else:
                self._hysteresis_info[entity_id] = None
                self._last_positions[entity_id] = current

            # Send tilt if changed (after position with delay, or immediately)
            if actual_tilt is not None:
                last_tilt = self._last_tilt_positions.get(entity_id)
                if last_tilt is None or abs(actual_tilt - last_tilt) > MANUAL_OVERRIDE_TOLERANCE:
                    self._last_tilt_positions[entity_id] = actual_tilt
                    tilt_delay = TILT_COMMAND_DELAY if position_changed else 0
                    if not position_changed:
                        self._last_command_time[entity_id] = time_mod.monotonic()
                    self._schedule_tilt(entity_id, actual_tilt, tilt_delay)

    def _supports_tilt(self, entity_id: str) -> bool:
        """Check if a cover entity supports tilt via HA features."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        features = state.attributes.get("supported_features", 0)
        return bool(features & TILT_FEATURE_FLAG)

    def _schedule_tilt(
        self, entity_id: str, tilt: int, delay: float
    ) -> None:
        """Schedule a tilt command, cancelling any pending one for the same cover."""
        old_task = self._tilt_tasks.get(entity_id)
        if old_task and not old_task.done():
            old_task.cancel()
        self._tilt_tasks[entity_id] = self.hass.async_create_task(
            self._send_tilt_delayed(entity_id, tilt, delay)
        )

    async def _send_tilt_delayed(
        self, entity_id: str, tilt: int, delay: float
    ) -> None:
        """Send tilt command after optional delay."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_command_time[entity_id] = time_mod.monotonic()
            await self.hass.services.async_call(
                "cover",
                "set_cover_tilt_position",
                {"entity_id": entity_id, "tilt_position": tilt},
                blocking=False,
            )
        except Exception as err:
            _LOGGER.error("Failed to send tilt to %s: %s", entity_id, err)
        finally:
            # Clean up task reference (guard against cancelled task clearing new ref)
            if self._tilt_tasks.get(entity_id) is asyncio.current_task():
                del self._tilt_tasks[entity_id]

    def set_cover_manual(self, entity_id: str) -> None:
        """Set a cover's status to MANUAL (public API for platforms)."""
        self._cover_states[entity_id] = CoverStatus.MANUAL
        self.storage.update_cover_status(entity_id, CoverStatus.MANUAL.value, None)

    async def async_shutdown(self) -> None:
        """Shut down coordinator."""
        # Cancel pending tilt tasks
        for task in self._tilt_tasks.values():
            if not task.done():
                task.cancel()
        self._tilt_tasks.clear()

        for unsub in self._unsub_state_change:
            unsub()
        self._unsub_state_change.clear()
        # Flush pending debounced saves to prevent data loss
        self.storage.flush_pending_save()
        if self.log_storage:
            self.log_storage.flush_pending_save()
        try:
            await self.storage.async_save()
        except Exception:
            _LOGGER.warning("Failed to flush pending save during shutdown")
