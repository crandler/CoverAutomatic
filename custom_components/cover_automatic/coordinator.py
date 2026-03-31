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
    TILT_COMMAND_DELAY,
    TILT_FEATURE_FLAG,
)
from .engine import RuleEngine
from .models import CoverConfig, CoverStatus
from .storage import CoverAutomaticStorage
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
                    self._cover_states[cover_id] = CoverStatus.VENTING
                    self.storage.update_cover_status(cover_id, CoverStatus.VENTING.value, None)

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
            if cover.auto_enabled and self._cover_states.get(entity_id) in (CoverStatus.AUTO, CoverStatus.VENTING):
                _LOGGER.info(
                    "[%s] Manual override -> PAUSED (expected pos %s, got %s)",
                    entity_id,
                    expected_position,
                    current_position,
                    expected_tilt,
                )
                self.pause_cover(cover)

    def pause_cover(self, cover: CoverConfig) -> None:
        """Pause automation for a cover."""
        self._cover_states[cover.entity_id] = CoverStatus.PAUSED
        duration = cover.pause_duration or self.storage.pause_duration
        pause_until = dt_util.now().timestamp() + (duration * 60)
        self.storage.update_cover_status(
            cover.entity_id, CoverStatus.PAUSED.value, pause_until
        )
        if self.data is not None:
            self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str) -> None:
        """Resume automation for a cover."""
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
        Lock/vent sensors always have highest priority (safety feature),
        even when auto_enabled is False.
        """
        for entity_id in self.storage._data.get("covers", {}):
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            # Check lock sensor state (window contact) - always highest priority
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and evaluate rules."""
        # Sync cover statuses from sensors before evaluation
        self._sync_cover_statuses()

        result: dict[str, Any] = {
            "covers": {},
            "facades": {},
            "scenario": self.storage.active_scenario,
        }

        for facade_id, facade in self.storage.facades.items():
            result["facades"][facade_id] = {
                "sun_on_facade": is_sun_on_facade(self.hass, facade),
            }

        for entity_id, cover in self.storage.covers.items():
            status = self.get_cover_status(entity_id)
            target_position: int | None = None
            target_tilt_position: int | None = None

            if status == CoverStatus.AUTO:
                engine_result = self.engine.evaluate_cover(cover)
                if engine_result is not None:
                    target_position = engine_result.position
                    target_tilt_position = engine_result.tilt_position

            result["covers"][entity_id] = {
                "status": status.value,
                "target_position": target_position,
                "target_tilt_position": target_tilt_position,
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
            # Use live status from _cover_states instead of snapshot
            status = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if status not in (CoverStatus.AUTO, CoverStatus.VENTING):
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
                # Accept current position as expected
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
                # Accept current position as expected
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
                self._last_positions[entity_id] = target
                self._last_command_time[entity_id] = time_mod.monotonic()
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=False,
                )
                self.storage.update_cover_last_change(entity_id, now)
            else:
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
        # Flush pending debounced save to prevent data loss
        self.storage.flush_pending_save()
        try:
            await self.storage.async_save()
        except Exception:
            _LOGGER.warning("Failed to flush pending save during shutdown")
