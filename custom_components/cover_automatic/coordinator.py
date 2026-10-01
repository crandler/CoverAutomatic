"""Data update coordinator for CoverAutomatic."""
from __future__ import annotations

import asyncio
import logging
import time as time_mod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.logbook import async_log_entry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    BINARY_SENSOR_ON_STATES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SIGNAL_DATA_UPDATED,
    LOG_EVENT_POSITION,
    LOG_EVENT_RULE,
    LOG_EVENT_STATUS,
    LOG_EVENT_WIND,
    SET_POSITION_FEATURE_FLAG,
    TILT_COMMAND_DELAY,
    TILT_FEATURE_FLAG,
)
from . import i18n
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

# Margin added to a cover's travel time to get its settle time (seconds)
TRAVEL_TIME_MARGIN = 5

# Travel time measurement: minimum move (%) and maximum duration (seconds).
# Short moves of polled covers are dominated by the polling interval (the
# arrival is only seen at the next poll), which inflated the learned value:
# only moves of at least half the full travel are used.
MIN_MEASURED_DISTANCE = 50
MAX_MEASURED_TRAVEL = 300
# A new travel sample may exceed the previous measurement by this factor at
# most (one late poll must not double the settle time).
MAX_TRAVEL_GROWTH = 1.5

# Resends of a position command the cover did not react to at all (lost
# radio/cloud command) before it is treated as a manual override.
MAX_LOST_COMMAND_RETRIES = 2

# Keys written by the coordinator into storage._data (runtime state only,
# never part of the configuration): wind protection and pre-lock statuses,
# so protections survive a Home Assistant restart.
WIND_STATE_KEY = "wind_protected_state"
PRE_LOCK_STATES_KEY = "pre_lock_states"

_UNUSABLE_STATES = ("unavailable", "unknown")

# Resume on match (manual pause ended when the cover is back at its rule's
# position): no check during the first seconds of a pause -- a cover moved by
# hand still reports its start position, which may be the rule's target --
# and the cover must be still (no report for SETTLE_TIME).
RESUME_MATCH_GRACE = 60

# Seconds after startup before applying positions (sensor stabilization)
STARTUP_GRACE_PERIOD = 120


def _is_safety(result: Any) -> bool:
    """Whether an engine result comes from a safety rule."""
    return result is not None and getattr(result, "safety", False) is True


class CoverAutomaticCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data updates and rule evaluation."""

    # Runtime helpers created lazily (see their accessors): the class
    # defaults keep coordinators built without __init__ (tests) working.
    _wind_tasks: set[asyncio.Task[None]] | None = None
    _lost_command_retries: dict[str, int] | None = None
    _apply_lock: asyncio.Lock | None = None
    _paused_at: dict[str, float] | None = None
    # Origin of each pause: True = manual override detected, False = explicit
    # pause (service). Unknown (e.g. restored after a restart) = manual.
    _pause_manual: dict[str, bool] | None = None
    # Covers that moved at all since our last position command (even during
    # the settle time): a lost-command resend is only for covers that did not
    # react at all -- a user counter-order also ends at the start position.
    _moved_since_command: set[str] | None = None
    # Monotonic time of the last position / motion change of each cover
    # (attribute-only reports such as Zigbee linkquality do not count)
    _position_changed_at: dict[str, float] | None = None
    # Covers whose lock sensor entity no longer exists (logged once)
    _lock_sensor_missing: set[str] | None = None
    # Covers whose move is blocked by an unknown window state (logged once
    # per blocking episode)
    _move_blocked_logged: set[str] | None = None
    # Wind protection restored from storage, still to be confirmed by the
    # wind sensor before the end of the startup grace period
    _wind_restore_pending: bool = False
    # The wind sensor gave a valid numeric value since startup
    _wind_value_seen: bool = False

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
        self._pending_settle: set[str] = set()
        self._pre_lock_states: dict[str, CoverStatus] = {}
        self._wind_protected: bool = False
        self._hysteresis_info: dict[str, str | None] = {}
        self._last_matching_rules: dict[str, str | None] = {}
        self._last_move_rule: dict[str, str | None] = {}
        # Last position actually commanded by the apply cycle (raw, inverted)
        self._last_sent_target: dict[str, int] = {}
        # Moves commanded by the apply cycle, for travel time measurement:
        # entity_id -> (monotonic start, start position, target), raw positions
        self._move_start: dict[str, tuple[float, int, int]] = {}
        # Covers that just exited a protective status (LOCKED / VENTING) and
        # need to bypass the time hysteresis once -- otherwise a long
        # min_time_between_changes leaves the cover at vent/lock position
        # long after the sensor has cleared.
        self._post_protective_exit: set[str] = set()
        # Covers currently driven by a safety rule: entity_id -> rule id
        self._safety_holds: dict[str, str] = {}
        # Covers whose protective status is kept because a lock/vent sensor
        # is unavailable (logged once per outage)
        self._sensor_unknown_kept: set[str] = set()
        # Wind sensor unavailable while protected (warned once per outage)
        self._wind_sensor_warned: bool = False
        # Pending wind command tasks (staggered sends), cancelled when the
        # wind protection ends or is re-activated and on shutdown
        self._wind_tasks = set()
        # Resends of lost position commands per cover (bounded)
        self._lost_command_retries = {}
        # Serialises apply cycles: one may sleep during the command stagger
        self._apply_lock = asyncio.Lock()
        # Start of each manual pause (monotonic), for the resume-on-match grace
        self._paused_at = {}
        self._pause_manual = {}
        self._moved_since_command = set()
        self._position_changed_at = {}
        self._lock_sensor_missing = set()
        self._move_blocked_logged = set()
        self._wind_restore_pending = False
        self._wind_value_seen = False
        self._startup_time: float = time_mod.monotonic()
        self._startup_skip: bool = True
        self._grace_synced: bool = False
        self._unsub_update_listener: Any = None
        self.log_storage: ActivityLogStorage | None = None

    def _runtime_set(self, name: str) -> set[str]:
        """Per-cover runtime set created lazily (coordinators built without __init__)."""
        value = getattr(self, name, None)
        if value is None:
            value = set()
            setattr(self, name, value)
        return value

    def _runtime_dict(self, name: str) -> dict[str, Any]:
        """Per-cover runtime dict created lazily (see _runtime_set)."""
        value = getattr(self, name, None)
        if value is None:
            value = {}
            setattr(self, name, value)
        return value

    def _in_startup_grace(self) -> bool:
        """Whether the startup grace period (sensor stabilisation) is running."""
        return (time_mod.monotonic() - self._startup_time) < STARTUP_GRACE_PERIOD

    def _cover_val(self, cover_raw: dict[str, Any], key: str) -> Any:
        """Get cover config value with global fallback from storage."""
        val = cover_raw.get(key)
        if val is not None:
            return val
        return getattr(self.storage, key, None)

    def _sync_tilt_from_state(self, entity_id: str, state: Any) -> None:
        """Sync _last_tilt_positions from cover state attributes."""
        tilt_val = state.attributes.get("current_tilt_position")
        if tilt_val is not None:
            try:
                self._last_tilt_positions[entity_id] = int(tilt_val)
            except (ValueError, TypeError):
                pass

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self.storage.async_load()
        self._restore_cover_states()
        await self._async_setup_default_scenarios()
        self._setup_state_tracking()
        self._unsub_update_listener = self.async_add_listener(
            self._fire_update_event
        )

    @callback
    def _fire_update_event(self) -> None:
        """Notify panel subscriptions (WebSocket) of data changes."""
        async_dispatcher_send(self.hass, SIGNAL_DATA_UPDATED)

    def _restore_cover_states(self) -> None:
        """Restore cover states from persisted storage data.

        Restores PAUSED (with unexpired timer), the protective statuses
        LOCKED / VENTING (with their pre-lock status) and, when the wind
        protection was active and is still configured, WIND_PROTECTED.
        Everything else starts as AUTO and is re-derived by
        _sync_cover_statuses.

        The protective statuses must survive a restart: battery sensors
        (Zigbee) or alarm integrations often report "unknown" for minutes
        after startup, and an AUTO cover whose window state is unknown would
        otherwise be closed by the next night rule on an open window. While
        the sensor stays unknown the sync keeps the restored status; once it
        reports "closed" the cover is unlocked normally.
        """
        data = self.storage._data
        wind_configured = bool(self.storage.wind_sensor) and self.storage.wind_speed_threshold > 0
        self._wind_protected = data.get(WIND_STATE_KEY) is True and wind_configured
        # Confirmed by the wind sensor before the end of the grace period,
        # otherwise dropped (see _drop_unconfirmed_wind_restore)
        self._wind_restore_pending = self._wind_protected
        if self._wind_protected:
            _LOGGER.info("Startup: wind protection was active, kept until the wind sensor reports")
        stored_pre_lock = data.get(PRE_LOCK_STATES_KEY)
        if not isinstance(stored_pre_lock, dict):
            stored_pre_lock = {}
        kept = {CoverStatus.LOCKED.value, CoverStatus.VENTING.value}
        if self._wind_protected:
            kept.add(CoverStatus.WIND_PROTECTED.value)
        for entity_id, cover_data in data.get("covers", {}).items():
            stored_status = cover_data.get("status", "auto")
            if stored_status == CoverStatus.PAUSED.value:
                pause_until = cover_data.get("pause_until")
                if pause_until and dt_util.now().timestamp() < pause_until:
                    self._cover_states[entity_id] = CoverStatus.PAUSED
                    continue
            if stored_status in kept:
                self._cover_states[entity_id] = CoverStatus(stored_status)
                try:
                    self._pre_lock_states[entity_id] = CoverStatus(stored_pre_lock.get(entity_id))
                except ValueError:
                    pass  # no (or invalid) pre-lock status: unlock falls back to AUTO
                _LOGGER.debug("[%s] Startup: restored %s", entity_id, stored_status)
                continue
            # Reset everything else to AUTO (lock/vent re-detected from sensors)
            if stored_status != CoverStatus.AUTO.value:
                _LOGGER.debug("[%s] Startup: reset %s -> AUTO", entity_id, stored_status)
            self._cover_states[entity_id] = CoverStatus.AUTO
            if stored_status != CoverStatus.AUTO.value:
                self.storage.update_cover_status(
                    entity_id, CoverStatus.AUTO.value, None
                )
        self._persist_runtime_state()

    def _persist_runtime_state(self) -> None:
        """Write the wind state and the pre-lock statuses into the store.

        Only written (debounced save) when changed. Called after every sync
        cycle as well, which also rewrites the keys after an import replaced
        the whole store content.
        """
        data = self.storage._data
        pre_lock = {
            entity_id: status.value
            for entity_id, status in self._pre_lock_states.items()
            if isinstance(status, CoverStatus)
        }
        if data.get(WIND_STATE_KEY) is self._wind_protected and data.get(PRE_LOCK_STATES_KEY) == pre_lock:
            return
        data[WIND_STATE_KEY] = self._wind_protected
        data[PRE_LOCK_STATES_KEY] = pre_lock
        self.storage._schedule_save()

    def _set_wind_protected(self, active: bool) -> None:
        """Change the global wind protection state and persist it.

        Any real change ends the pending confirmation of a wind state
        restored at startup (the sensor has spoken, or settings changed).
        """
        self._wind_protected = active
        self._wind_restore_pending = False
        self._persist_runtime_state()

    async def _async_setup_default_scenarios(self) -> None:
        """Create default scenarios (named in the HA language) if none exist.

        Existing default scenarios whose name was never changed (still one of
        the built-in names in any language) are renamed to the current HA
        language, so an English-named "Everyday" becomes "Quotidien" on a
        French installation. User-chosen names are left untouched.
        """
        from .models import Scenario

        icons = {
            "everyday": "mdi:home",
            "summer": "mdi:white-balance-sunny",
            "winter": "mdi:snowflake",
            "vacation": "mdi:airplane",
            "cinema": "mdi:movie",
            "manual": "mdi:hand-back-right",
        }
        if not self.storage.scenarios:
            for scenario_id in i18n.DEFAULT_SCENARIO_IDS:
                await self.storage.async_add_scenario(
                    Scenario(
                        id=scenario_id,
                        name=i18n.text(self.hass, f"scenario_{scenario_id}"),
                        icon=icons[scenario_id],
                    ),
                    save=False,
                )
            await self.storage.async_save()
            return

        renamed = False
        for scenario_id in i18n.DEFAULT_SCENARIO_IDS:
            raw = self.storage._data.get("scenarios", {}).get(scenario_id)
            if not isinstance(raw, dict):
                continue
            localized = i18n.text(self.hass, f"scenario_{scenario_id}")
            name = raw.get("name")
            if name != localized and name in i18n.default_scenario_names(scenario_id):
                raw["name"] = localized
                renamed = True
        if renamed:
            self.storage._invalidate_cache()
            await self.storage.async_save()

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
                self._hysteresis_info,
                self._last_matching_rules,
                self._last_move_rule,
                self._last_sent_target,
                self._move_start,
                self._safety_holds,
            ):
                orphaned = set(state_dict.keys()) - current_covers
                for entity_id in orphaned:
                    value = state_dict.pop(entity_id)
                    if isinstance(value, asyncio.Task) and not value.done():
                        value.cancel()
            if self._lost_command_retries:
                for entity_id in set(self._lost_command_retries) - current_covers:
                    self._lost_command_retries.pop(entity_id, None)
            if self._paused_at:
                for entity_id in set(self._paused_at) - current_covers:
                    self._paused_at.pop(entity_id, None)
            for name in ("_pause_manual", "_position_changed_at"):
                mapping = self._runtime_dict(name)
                for entity_id in set(mapping) - current_covers:
                    mapping.pop(entity_id, None)
            for name in ("_moved_since_command", "_lock_sensor_missing", "_move_blocked_logged"):
                entries = self._runtime_set(name)
                entries -= set(entries) - current_covers
            # Per-entity sets: drop orphaned entity ids as well
            for state_set in (
                self._pending_settle, self._post_protective_exit, self._sensor_unknown_kept,
            ):
                state_set -= set(state_set) - current_covers
            # Rule engine per-cover caches (comfort mode, warnings)
            engine = getattr(self, "engine", None)
            if engine is not None:
                engine.forget_covers_except(current_covers)

        entities_to_track: set[str] = {SUN_ENTITY_ID}

        for entity_id, cover_data in self.storage._data.get("covers", {}).items():
            entities_to_track.add(entity_id)
            if lock_sensor := cover_data.get("lock_sensor"):
                entities_to_track.add(lock_sensor)
            if vent_sensor := cover_data.get("vent_sensor"):
                entities_to_track.add(vent_sensor)
            if indoor_sensor := cover_data.get("indoor_temp_sensor"):
                entities_to_track.add(indoor_sensor)
            if isinstance(occupancy := cover_data.get("occupancy_sensor"), str) and occupancy:
                entities_to_track.add(occupancy)
            # Entities holding a per-cover comfort band
            for key in ("comfort_temp_min_entity", "comfort_temp_max_entity"):
                if isinstance(ref := cover_data.get(key), str) and ref:
                    entities_to_track.add(ref)

        if self.storage.outdoor_temp_sensor:
            entities_to_track.add(self.storage.outdoor_temp_sensor)

        if self.storage.indoor_temp_sensor:
            entities_to_track.add(self.storage.indoor_temp_sensor)

        if self.storage.weather_entity:
            entities_to_track.add(self.storage.weather_entity)

        if self.storage.wind_sensor:
            entities_to_track.add(self.storage.wind_sensor)

        if self.storage.solar_sensor:
            entities_to_track.add(self.storage.solar_sensor)

        if self.storage.workday_sensor:
            entities_to_track.add(self.storage.workday_sensor)

        # Entities holding global thresholds (a change re-evaluates the rules)
        for key in ("comfort_temp_min_entity", "comfort_temp_max_entity", "solar_threshold_entity"):
            if isinstance(ref := getattr(self.storage, key, None), str) and ref:
                entities_to_track.add(ref)

        for rule_data in self.storage._data.get("rules", {}).values():
            for condition in rule_data.get("conditions", []):
                params = condition.get("params") or {}
                if not isinstance(params, dict):
                    continue
                # The panel stores entities under "entity_id" (state_is,
                # numeric_state, workday); "sensor"/"entity" are legacy keys.
                for key in ("sensor", "entity", "entity_id"):
                    ref = params.get(key)
                    if isinstance(ref, str) and ref:
                        entities_to_track.add(ref)

        # Entities referenced by native Home Assistant conditions (incl. templates)
        try:
            entities_to_track |= set(self.engine.ha_condition_entities())
        except (AttributeError, TypeError):
            pass

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
            speed = float(state.state)
        except (ValueError, TypeError):
            return None
        if speed != speed:  # NaN is no valid reading
            return None
        self._wind_value_seen = True
        return speed

    def _check_wind_protection(self) -> None:
        """Check wind sensor and update global wind protection state.

        Uses hysteresis: activates at threshold, deactivates at
        threshold - hysteresis to prevent oscillation in gusty wind.
        """
        threshold = self.storage.wind_speed_threshold
        hysteresis = self.storage.wind_speed_hysteresis

        # Feature switched off (sensor removed or threshold set to 0) while
        # protection is active: release it, otherwise covers stay blocked.
        if self._wind_protected and (not self.storage.wind_sensor or threshold <= 0):
            _LOGGER.info("Wind protection DEACTIVATED (wind protection disabled in settings)")
            self._set_wind_protected(False)
            self._log(LOG_EVENT_WIND, None, "Deactivated (disabled in settings)",
                      {"key": "wind_disabled"})
            self._logbook(i18n.text(self.hass, "wind_disabled"))
            self._deactivate_wind_protection()
            return

        wind_speed = self._get_wind_speed()
        if self._drop_unconfirmed_wind_restore():
            return
        if wind_speed is None:
            if self._wind_protected and not self._wind_sensor_warned:
                self._wind_sensor_warned = True
                _LOGGER.warning("Wind sensor unavailable while WIND_PROTECTED, keeping protection active")
            return
        self._wind_sensor_warned = False

        if hysteresis >= threshold > 0:
            # Invalid config (e.g. older storage/import): the release level
            # threshold - hysteresis would be <= 0 and never reached.
            _LOGGER.debug(
                "wind_speed_hysteresis (%.1f) >= threshold (%.1f), ignoring hysteresis",
                hysteresis, threshold,
            )
            hysteresis = 0.0

        if not self._wind_protected and wind_speed >= threshold > 0:
            wind_pos = self._wind_position()
            _LOGGER.info(
                "Wind protection ACTIVATED (%.1f >= %.1f), covers -> %d%%",
                wind_speed, threshold, wind_pos,
            )
            self._set_wind_protected(True)
            self._log(LOG_EVENT_WIND, None, f"Activated ({wind_speed:.1f} >= {threshold:.1f})",
                      {"key": "wind_activated", "speed": round(wind_speed, 1),
                       "threshold": round(threshold, 1), "position": wind_pos})
            self._logbook(i18n.text(
                self.hass, "wind_activated",
                speed=f"{wind_speed:.1f}", threshold=f"{threshold:.1f}",
            ))
            self._activate_wind_protection()
        elif self._wind_protected and wind_speed <= threshold - hysteresis:
            _LOGGER.info("Wind protection DEACTIVATED (%.1f <= %.1f)", wind_speed, threshold - hysteresis)
            self._set_wind_protected(False)
            release = threshold - hysteresis
            self._log(LOG_EVENT_WIND, None, f"Deactivated ({wind_speed:.1f} <= {release:.1f})",
                      {"key": "wind_deactivated", "speed": round(wind_speed, 1),
                       "threshold": round(release, 1)})
            self._logbook(i18n.text(
                self.hass, "wind_deactivated",
                speed=f"{wind_speed:.1f}", threshold=f"{release:.1f}",
            ))
            self._deactivate_wind_protection()

    def _drop_unconfirmed_wind_restore(self) -> bool:
        """Drop a wind protection restored at startup the sensor never confirmed.

        The restored state is kept during the startup grace period (wind
        sensors often report late). At its end, a wind sensor entity that
        does not exist (renamed / removed) or that never gave a valid value
        since startup cannot release the protection: the covers would stay
        blocked at the wind position forever. The protection is then ended
        normally (covers back to their previous status) and logged once.
        Returns True when it was dropped.
        """
        if not self._wind_restore_pending or self._in_startup_grace():
            return False
        self._wind_restore_pending = False
        if not self._wind_protected:
            return False
        sensor_id = self.storage.wind_sensor
        if self.hass.states.get(sensor_id) is not None and self._wind_value_seen:
            return False
        _LOGGER.warning(
            "Wind protection restored at startup dropped: wind sensor %s %s",
            sensor_id,
            "does not exist" if self.hass.states.get(sensor_id) is None else "never reported a value",
        )
        self._set_wind_protected(False)
        self._log(LOG_EVENT_WIND, None, f"Restored wind protection dropped (sensor {sensor_id})",
                  {"key": "wind_restore_dropped", "sensor": sensor_id})
        self._deactivate_wind_protection()
        return True

    def _wind_position(self) -> int:
        """Logical position covers move to while wind protection is active."""
        value = getattr(self.storage, "wind_position", 100)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 100
        return max(0, min(100, int(value)))

    def _lock_open_window(self, entity_id: str, cover_raw: dict[str, Any]) -> None:
        """Lock a cover whose window is open (lock position, or held in place)."""
        if self._cover_states.get(entity_id) == CoverStatus.LOCKED:
            return
        lock_pos = self._cover_val(cover_raw, "lock_position")
        current = self._get_current_position(entity_id)
        if self._lock_moves(cover_raw, current, lock_pos):
            lock_tilt = self._cover_val(cover_raw, "lock_tilt_position")
            self._lock_cover(entity_id, lock_pos, lock_tilt=lock_tilt)
        else:
            if entity_id not in self._pre_lock_states:
                prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
                self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
            self._lock_in_place(entity_id, cover_raw)

    def _keeps_lock_sensor_unknown(self, entity_id: str, cover_raw: dict[str, Any]) -> bool:
        """Whether a LOCKED cover must stay locked: its window state is unknown.

        Never close a cover on a possibly open window: an unavailable lock
        sensor is not "closed".
        """
        return (
            self._cover_states.get(entity_id) == CoverStatus.LOCKED
            and self._is_sensor_unknown(cover_raw, "lock_sensor")
        )

    def _protect_one_from_wind(self, entity_id: str, cover_raw: dict[str, Any]) -> None:
        """Wind protection for one cover while it is active.

        An open window (lock sensor) wins over the wind: the cover stays or
        gets locked (emergency exit). Otherwise the cover takes the wind
        status and position -- only this cover is commanded, not all.
        """
        if self._is_sensor_open(cover_raw, "lock_sensor"):
            self._lock_open_window(entity_id, cover_raw)
            return
        status = self._cover_states.get(entity_id)
        if status == CoverStatus.WIND_PROTECTED:
            return
        if self._keeps_lock_sensor_unknown(entity_id, cover_raw):
            return
        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
        if entity_id not in self._pre_lock_states:
            self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
        self._cover_states[entity_id] = CoverStatus.WIND_PROTECTED
        self.storage.update_cover_status(entity_id, CoverStatus.WIND_PROTECTED.value, None)
        self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> wind_protected",
                  {"key": "status_change", "from": prev.value, "to": "wind_protected"})
        if entity_id not in self._safety_holds:
            self._send_wind_position(entity_id)

    def _activate_wind_protection(self) -> None:
        """Set all covers to WIND_PROTECTED and move them to the wind position.

        Covers whose window is open are locked instead: the lock (emergency
        exit) has priority over the wind. A LOCKED cover whose window state
        is unknown stays locked (same guard as _protect_one_from_wind).
        """
        # A previous activation may still be sending: never run two
        # staggered wind sequences in parallel.
        self._cancel_wind_tasks()
        wind_pos = self._wind_position()
        commands: list[tuple[str, int]] = []
        for entity_id in self.storage._data.get("covers", {}):
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            if self._is_sensor_open(cover_raw, "lock_sensor"):
                self._lock_open_window(entity_id, cover_raw)
                continue
            if self._keeps_lock_sensor_unknown(entity_id, cover_raw):
                _LOGGER.debug("[%s] Wind protection: kept LOCKED (window state unknown)", entity_id)
                continue

            prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if prev not in (CoverStatus.WIND_PROTECTED,):
                if entity_id not in self._pre_lock_states:
                    self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev

            self._cover_states[entity_id] = CoverStatus.WIND_PROTECTED
            self.storage.update_cover_status(entity_id, CoverStatus.WIND_PROTECTED.value, None)

            if entity_id in self._safety_holds:
                # A safety rule drives this cover: it keeps the rule's position
                _LOGGER.debug("[%s] Wind protection: kept by safety rule", entity_id)
                continue

            # Move to the wind position (logical, inverted covers mirrored)
            inverted = cover_raw.get("inverted", False)
            actual_position = (100 - wind_pos) if inverted else wind_pos
            self._last_positions[entity_id] = actual_position
            self._last_command_time[entity_id] = time_mod.monotonic()
            commands.append((entity_id, actual_position))

        if commands:
            self._start_wind_commands(commands)

        self._persist_runtime_state()
        if self.data is not None:
            self.async_set_updated_data(self.data)

    def _send_wind_position(self, entity_id: str) -> None:
        """Move one wind protected cover to the wind position."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None:
            return
        wind_pos = self._wind_position()
        actual = (100 - wind_pos) if cover_raw.get("inverted", False) else wind_pos
        self._last_positions[entity_id] = actual
        self._last_command_time[entity_id] = time_mod.monotonic()
        _LOGGER.debug("[%s] Wind protection re-applied -> %d%%", entity_id, wind_pos)
        self._start_wind_commands([(entity_id, actual)])

    def _wind_task_set(self) -> set[asyncio.Task[None]]:
        """Pending wind command tasks (created lazily)."""
        if self._wind_tasks is None:
            self._wind_tasks = set()
        return self._wind_tasks

    def _start_wind_commands(self, commands: list[tuple[str, int]]) -> None:
        """Send wind commands in a tracked task (cancellable on release)."""
        task = self.hass.async_create_task(self._send_staggered_commands(commands))
        if isinstance(task, asyncio.Task):
            tasks = self._wind_task_set()
            tasks.add(task)
            task.add_done_callback(tasks.discard)

    def _cancel_wind_tasks(self) -> None:
        """Cancel pending (staggered) wind commands."""
        tasks = self._wind_task_set()
        for task in list(tasks):
            if not task.done():
                task.cancel()
        tasks.clear()

    async def _send_staggered_commands(
        self, commands: list[tuple[str, int]]
    ) -> None:
        """Send wind position commands with optional stagger delay between them.

        The wind may drop, a window may open (LOCKED) or a safety rule may
        take over during the stagger sleeps: each command is re-checked
        right before it is sent, and the settle window starts at the actual
        send time (a late command must not be read as a manual move).
        """
        stagger = self.storage.command_stagger
        for i, (entity_id, position) in enumerate(commands):
            if i > 0 and stagger > 0:
                await asyncio.sleep(stagger)
            if (
                not self._wind_protected
                or self._cover_states.get(entity_id) != CoverStatus.WIND_PROTECTED
                or entity_id in self._safety_holds
            ):
                _LOGGER.debug("[%s] Wind command dropped: status changed meanwhile", entity_id)
                continue
            self._last_positions[entity_id] = self._effective_position(entity_id, position)
            self._last_command_time[entity_id] = time_mod.monotonic()
            await self._async_send_position(entity_id, position)

    def _deactivate_wind_protection(self) -> None:
        """Remove WIND_PROTECTED status from all covers, re-derive from sensors.

        Evaluates lock/vent sensors inline so covers with open windows
        transition directly to LOCKED/VENTING instead of briefly landing in
        AUTO and waiting for the next scan tick. A cover whose window state
        is unknown is locked in place (possibly open window).
        """
        # Wind commands still waiting for their stagger slot are obsolete
        self._cancel_wind_tasks()
        for entity_id in list(self.storage._data.get("covers", {})):
            if self._cover_states.get(entity_id) != CoverStatus.WIND_PROTECTED:
                continue

            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            pre_wind = self._pre_lock_states.pop(entity_id, None)

            if self._is_sensor_open(cover_raw, "lock_sensor"):
                lock_pos = self._cover_val(cover_raw, "lock_position")
                current = self._get_current_position(entity_id)
                if self._lock_moves(cover_raw, current, lock_pos):
                    lock_tilt = self._cover_val(cover_raw, "lock_tilt_position")
                    self._lock_cover(entity_id, lock_pos, lock_tilt=lock_tilt)
                else:
                    # Record a pre-lock state (the pre-wind one was just
                    # dropped) so the window-closed unlock restores AUTO.
                    self._pre_lock_states[entity_id] = CoverStatus.AUTO
                    self._lock_in_place(entity_id, cover_raw)
                continue

            if self._is_sensor_unknown(cover_raw, "lock_sensor"):
                # Window state unknown (sensor unavailable): treat it as
                # possibly open. Handing the cover back to AUTO would let the
                # next rule close it on an open window; it stays where it is
                # (LOCKED) until the sensor reports again.
                self._pre_lock_states[entity_id] = self._status_for_automation(
                    pre_wind if pre_wind in (CoverStatus.AUTO, CoverStatus.MANUAL) else CoverStatus.AUTO,
                    cover_raw,
                )
                self._lock_in_place(entity_id, cover_raw, sensor_unknown=True)
                continue

            if self._is_sensor_open(cover_raw, "vent_sensor"):
                self._enter_venting(entity_id, cover_raw, "wind protection ended")
                continue

            # Automation switched off during the storm: MANUAL right away
            # (not AUTO until the next sync), whatever the pre-wind status.
            target = self._status_for_automation(CoverStatus.AUTO, cover_raw)
            self._cover_states[entity_id] = target
            self.storage.update_cover_status(entity_id, target.value, None)
            self._sync_expected_after_protective_exit(entity_id)
            # Like the lock/vent exits: return to the rule right away instead
            # of waiting for min_time_between_changes.
            if target == CoverStatus.AUTO:
                self._post_protective_exit.add(entity_id)

        self._persist_runtime_state()
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
            # A managed cover may also feed a rule condition
            if self._is_rule_entity(entity_id):
                self.hass.async_create_task(self.async_request_refresh())
        elif entity_id == self.storage.wind_sensor:
            self._handle_wind_sensor_change(new_state)
        else:
            lock_covers, vent_covers = self._get_covers_by_sensor(entity_id)
            if lock_covers or vent_covers:
                self._handle_contact_sensor_change(
                    entity_id, lock_covers, vent_covers, old_state, new_state
                )
                # The same entity may also feed a rule condition
                if self._is_rule_entity(entity_id):
                    self.hass.async_create_task(self.async_request_refresh())
            else:
                self.hass.async_create_task(self.async_request_refresh())

    def _is_rule_entity(self, entity_id: str) -> bool:
        """Return True if a rule condition references this entity."""
        try:
            if entity_id in self.engine.ha_condition_entities():
                return True
        except (AttributeError, TypeError):
            pass
        for rule_data in self.storage._data.get("rules", {}).values():
            for condition in rule_data.get("conditions", []):
                params = condition.get("params") or {}
                if isinstance(params, dict) and entity_id in (
                    params.get("sensor"), params.get("entity"), params.get("entity_id"),
                ):
                    return True
        return False

    def _is_sensor_open(self, cover_raw: dict[str, Any], key: str) -> bool:
        """Check if a binary sensor (lock/vent) for a cover is open."""
        sensor = cover_raw.get(key)
        if not sensor:
            return False
        sensor_state = self.hass.states.get(sensor)
        if sensor_state is None:
            return False
        return sensor_state.state in BINARY_SENSOR_ON_STATES

    def _is_sensor_unknown(self, cover_raw: dict[str, Any], key: str) -> bool:
        """Check if a configured lock/vent sensor has no usable state.

        "unavailable" / "unknown" always count as unknown (possibly open
        window). A sensor entity that does not exist at all (state None) is
        only unknown during the startup grace period, while integrations are
        still loading: afterwards it was renamed or removed and would block
        the cover forever (restored LOCKED never released, moves down never
        sent), so it is treated like no sensor configured.
        """
        sensor = cover_raw.get(key)
        if not sensor:
            return False
        sensor_state = self.hass.states.get(sensor)
        if sensor_state is None:
            return self._in_startup_grace()
        return sensor_state.state in _UNUSABLE_STATES

    def _track_missing_lock_sensor(self, entity_id: str, cover_raw: dict[str, Any]) -> None:
        """Log once per cover that its lock sensor entity no longer exists.

        Such a sensor is ignored after the grace period (_is_sensor_unknown):
        the activity log tells the user why the window lock no longer acts.
        Logged again only after the sensor came back and disappeared again.
        """
        missing = self._runtime_set("_lock_sensor_missing")
        sensor = cover_raw.get("lock_sensor")
        if (
            not sensor
            or self.hass.states.get(sensor) is not None
            or self._in_startup_grace()
        ):
            missing.discard(entity_id)
            return
        if entity_id in missing:
            return
        missing.add(entity_id)
        _LOGGER.warning(
            "[%s] Lock sensor %s does not exist: window lock ignored", entity_id, sensor
        )
        self._log(LOG_EVENT_STATUS, entity_id, f"Lock sensor {sensor} missing, ignored",
                  {"key": "lock_sensor_missing", "sensor": sensor})

    @staticmethod
    def _is_real_transition(old_state: Any, new_state: Any) -> bool:
        """Whether a sensor event is a real change between two usable states."""
        return (
            old_state is not None
            and old_state.state not in _UNUSABLE_STATES
            and old_state.state != new_state.state
        )

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
                lock_pos = self._cover_val(cover_raw, "lock_position")
                current = self._get_current_position(cover_id)
                if self._lock_moves(cover_raw, current, lock_pos):
                    self._lock_cover(cover_id, lock_pos, lock_tilt=self._cover_val(cover_raw, "lock_tilt_position"))
                else:
                    if cover_id not in self._pre_lock_states:
                        prev = self._cover_states.get(cover_id, CoverStatus.AUTO)
                        self._pre_lock_states[cover_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
                    self._lock_in_place(cover_id, cover_raw)
                    if self.data is not None:
                        self.async_set_updated_data(self.data)
            elif self._cover_states.get(cover_id) == CoverStatus.LOCKED and self._wind_protected:
                # Window closed during a storm: back to the wind protection
                # (this cover only).
                self._protect_one_from_wind(cover_id, cover_raw)
                if self.data is not None:
                    self.async_set_updated_data(self.data)
            elif self._cover_states.get(cover_id) == CoverStatus.LOCKED:
                # Only unlock if vent sensor is also not open
                if not is_sensor_open_cached(cover_raw, "vent_sensor"):
                    _LOGGER.debug("[%s] Lock sensor %s closed -> unlocking", cover_id, sensor_id)
                    self._unlock_cover(cover_id)
                else:
                    # Move to vent position if currently below it
                    self._pre_lock_states.pop(cover_id, None)
                    self._enter_venting(
                        cover_id, cover_raw, f"window {sensor_id} closed, vent still open"
                    )
                    if self.data is not None:
                        self.async_set_updated_data(self.data)

        # A vent sensor coming back from unavailable/unknown (or an event
        # without a state change, e.g. an attribute update) is no real
        # transition: acting on it would e.g. cancel a manual pause. The
        # periodic sync reconciles the status from the current sensor state.
        if not self._is_real_transition(old_state, new_state):
            if vent_covers:
                _LOGGER.debug(
                    "[%s] Vent sensor event without transition (%s -> %s), left to sync",
                    sensor_id, getattr(old_state, "state", None), new_state.state,
                )
            vent_covers = []

        # Handle vent sensor covers (vent open -> min position, automation continues)
        for cover_id in vent_covers:
            cover_raw = self.storage.get_cover_raw(cover_id)
            if cover_raw is None:
                continue

            # Skip if lock sensor is open (lock has priority)
            if is_sensor_open_cached(cover_raw, "lock_sensor"):
                continue
            # A tilted window does not override the wind protection
            if self._wind_protected:
                continue

            current_status = self._cover_states.get(cover_id, CoverStatus.AUTO)

            if is_open and current_status == CoverStatus.PAUSED:
                # A (manual) pause is kept, like the periodic sync does: a
                # window tilted for a few seconds must not cancel it. Only
                # the airflow is ensured (raised to the vent position when
                # below); the pause timer is unchanged.
                _LOGGER.debug(
                    "[%s] Vent sensor %s open while paused: pause kept", cover_id, sensor_id,
                )
                self._raise_to_vent_floor(cover_id, cover_raw)
            elif is_open and current_status not in (CoverStatus.LOCKED, CoverStatus.VENTING):
                # Move up to vent_position if currently below it
                self._enter_venting(cover_id, cover_raw, f"vent sensor {sensor_id} open")
                if self.data is not None:
                    self.async_set_updated_data(self.data)
            elif not is_open and current_status == CoverStatus.VENTING:
                # A PAUSED cover stays PAUSED (pause timer unchanged): the
                # vent sensor closing is no reason to end a manual pause.
                # Mirror the _sync_cover_statuses branch: a cover with automation
                # disabled returns to MANUAL, not AUTO, so the refresh triggered
                # below does not run an AUTO apply cycle (which could move a
                # disabled cover) before the next sync would correct the status.
                target = (
                    CoverStatus.AUTO
                    if cover_raw.get("auto_enabled", True)
                    else CoverStatus.MANUAL
                )
                _LOGGER.info(
                    "[%s] Vent sensor %s closed: %s -> %s",
                    cover_id, sensor_id, current_status.value, target.value,
                )
                self._log(LOG_EVENT_STATUS, cover_id, f"{current_status.value} -> {target.value}",
                          {"key": "status_change", "from": current_status.value,
                           "to": target.value, "sensor": sensor_id})
                self._cover_states[cover_id] = target
                self.storage.update_cover_status(cover_id, target.value, None)
                self._sync_expected_after_protective_exit(cover_id)
                # Mark for one-shot time-hysteresis bypass so the next apply
                # cycle re-applies the matching rule even when
                # min_time_between_changes has not elapsed.
                self._post_protective_exit.add(cover_id)
                if self.data is not None:
                    self.async_set_updated_data(self.data)
                self.hass.async_create_task(self.async_request_refresh())

        # Pre-lock statuses may have changed (lock/unlock): persist them now
        # rather than at the next sync cycle.
        self._persist_runtime_state()

    @staticmethod
    def _raw_position(state: Any) -> int | None:
        """HA position of a cover state (raw, not inverted).

        Covers without a current_position attribute (open/close only) are
        read from their state instead of being taken for closed (0).
        """
        value = state.attributes.get("current_position")
        if value is None:
            return {"open": 100, "closed": 0}.get(state.state)
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _supports_set_position(self, entity_id: str) -> bool:
        """Whether a cover accepts set_cover_position.

        Covers that only support open/close (some RTS / relay covers) must
        get open_cover / close_cover instead; set_cover_position is rejected
        by them. Without a supported_features attribute the cover is assumed
        to support positions (previous behaviour).
        """
        state = self.hass.states.get(entity_id)
        if state is None:
            return True
        features = state.attributes.get("supported_features")
        if isinstance(features, bool) or not isinstance(features, int):
            return True
        return bool(features & SET_POSITION_FEATURE_FLAG)

    def _effective_position(self, entity_id: str, position: int) -> int:
        """Raw position a command really reaches (open/close-only: 0 or 100)."""
        if self._supports_set_position(entity_id):
            return position
        return 100 if position >= 50 else 0

    def _position_call(self, entity_id: str, position: int) -> Any:
        """Service call moving a cover to a raw position (awaitable).

        Open/close-only covers are opened from 50 % up, closed below.
        """
        if self._supports_set_position(entity_id):
            return self.hass.services.async_call(
                "cover", "set_cover_position",
                {"entity_id": entity_id, "position": position},
                blocking=False,
            )
        service = "open_cover" if position >= 50 else "close_cover"
        return self.hass.services.async_call(
            "cover", service, {"entity_id": entity_id}, blocking=False,
        )

    async def _async_send_position(self, entity_id: str, position: int) -> None:
        """Send a raw position to a cover (see _position_call)."""
        await self._position_call(entity_id, position)

    def _get_current_position(self, entity_id: str) -> int | None:
        """Get current cover position (handles inverted covers)."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown"):
            return None
        pos = self._raw_position(state)
        if pos is None:
            return None
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw and cover_raw.get("inverted", False):
            pos = 100 - pos
        return pos

    @staticmethod
    def _lock_moves(cover_raw: dict[str, Any], current: int | None, lock_pos: int) -> bool:
        """Whether locking moves the cover to its lock position.

        With lock_hold_position the cover stays where it is (no position or
        tilt command); otherwise it only moves up to lock_pos, never down.
        """
        if cover_raw.get("lock_hold_position"):
            return False
        return current is None or current < lock_pos

    def _lock_in_place(
        self, entity_id: str, cover_raw: dict[str, Any], *, sensor_unknown: bool = False
    ) -> None:
        """Set a cover LOCKED without moving it (hold option or already above).

        With sensor_unknown the window state is unknown (sensor unavailable)
        rather than open: the cover is held as a precaution. The caller
        records the pre-lock state.
        """
        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
        self._cover_states[entity_id] = CoverStatus.LOCKED
        self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)
        self._update_last_position_from_state(entity_id)
        if prev == CoverStatus.LOCKED:
            return
        current = self._get_current_position(entity_id)
        sensor = cover_raw.get("lock_sensor")
        _LOGGER.info(
            "[%s] Window %s %s: %s -> locked (kept at %s%%)",
            entity_id, sensor, "state unknown" if sensor_unknown else "open", prev.value, current,
        )
        self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> locked (kept at {current}%)",
                  {"key": "status_change", "from": prev.value, "to": "locked",
                   "sensor": sensor, "position": current, "kept": True})

    def _raise_to_vent_floor(self, entity_id: str, cover_raw: dict[str, Any]) -> bool:
        """Raise a cover below its vent position to it (with the vent tilt).

        Returns True when a command was sent; otherwise the expected
        position is synced to where the cover is. Does not change the status:
        shared by _enter_venting and by a paused cover whose vent opens (the
        pause is kept, only the airflow is ensured).
        """
        vent_pos = self._cover_val(cover_raw, "vent_position")
        current = self._get_current_position(entity_id)
        if current is None or current >= vent_pos:
            self._update_last_position_from_state(entity_id)
            return False
        inverted = cover_raw.get("inverted", False)
        actual = (100 - vent_pos) if inverted else vent_pos
        self._last_positions[entity_id] = self._effective_position(entity_id, actual)
        self._last_command_time[entity_id] = time_mod.monotonic()
        self._pending_settle.add(entity_id)
        self.hass.async_create_task(self._position_call(entity_id, actual))
        vent_tilt = self._cover_val(cover_raw, "vent_tilt_position")
        if (
            isinstance(vent_tilt, int)
            and not isinstance(vent_tilt, bool)
            and cover_raw.get("supports_tilt", False)
        ):
            actual_tilt = 100 - vent_tilt if cover_raw.get("inverted_tilt", False) else vent_tilt
            self._last_tilt_positions[entity_id] = actual_tilt
            self._schedule_tilt(entity_id, actual_tilt, TILT_COMMAND_DELAY)
        return True

    def _enter_venting(self, entity_id: str, cover_raw: dict[str, Any], reason: str) -> None:
        """Set a cover VENTING, raising it to the vent position when below.

        When the cover is raised, the vent tilt (slats) is sent after the
        move like the lock tilt, so the configured airflow angle is applied.
        """
        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
        vent_pos = self._cover_val(cover_raw, "vent_position")
        current = self._get_current_position(entity_id)
        if self._raise_to_vent_floor(entity_id, cover_raw):
            detail = f"moving {current}% -> {vent_pos}%"
        else:
            detail = f"kept at {current}%, min {vent_pos}%"
        self._cover_states[entity_id] = CoverStatus.VENTING
        self.storage.update_cover_status(entity_id, CoverStatus.VENTING.value, None)
        if prev == CoverStatus.VENTING:
            return
        _LOGGER.info("[%s] %s: %s -> venting (%s)", entity_id, reason, prev.value, detail)
        self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> venting ({detail})",
                  {"key": "status_change", "from": prev.value, "to": "venting",
                   "sensor": cover_raw.get("vent_sensor"), "position": vent_pos})

    def _lock_cover(
        self, entity_id: str, lock_position: int, *, lock_tilt: int | None = None
    ) -> None:
        """Lock a cover due to open contact sensor."""
        # Save previous state for restoration after unlock
        # If paused, save as AUTO (pause cancelled by lock priority)
        if entity_id not in self._pre_lock_states:
            prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
            self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
        prev_status = self._cover_states.get(entity_id, CoverStatus.AUTO)
        self._cover_states[entity_id] = CoverStatus.LOCKED
        prev_val = self._pre_lock_states.get(entity_id, CoverStatus.AUTO).value
        cover_raw = self.storage.get_cover_raw(entity_id)
        sensor = cover_raw.get("lock_sensor") if cover_raw else None
        _LOGGER.info(
            "[%s] Window %s open: %s -> locked, moving to %s%%",
            entity_id, sensor, prev_status.value, lock_position,
        )
        self._log(LOG_EVENT_STATUS, entity_id, f"{prev_val} -> locked",
                  {"key": "status_change", "from": prev_val, "to": "locked",
                   "sensor": sensor, "position": lock_position})
        self._logbook(i18n.text(self.hass, "locked", position=lock_position), entity_id)
        self.storage.update_cover_status(entity_id, CoverStatus.LOCKED.value, None)

        # Handle inverted covers
        actual_position = lock_position
        if cover_raw and cover_raw.get("inverted", False):
            actual_position = 100 - lock_position

        _LOGGER.debug("Locking cover %s at position %s (actual: %s)", entity_id, lock_position, actual_position)

        # Update expected position to prevent false manual override
        self._last_positions[entity_id] = self._effective_position(entity_id, actual_position)

        self._last_command_time[entity_id] = time_mod.monotonic()
        self.hass.async_create_task(self._position_call(entity_id, actual_position))

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
        """Unlock a cover when its contact sensors are closed (or removed).

        Only acts on covers that are actually LOCKED or VENTING. A missing
        pre-lock state (e.g. VENTING entered directly, or a sensor removed
        from the cover config) falls back to AUTO instead of leaving the
        cover stuck in its protective status forever.
        """
        current = self._cover_states.get(entity_id)
        if current not in (CoverStatus.LOCKED, CoverStatus.VENTING):
            self._pre_lock_states.pop(entity_id, None)
            return

        self._log(LOG_EVENT_STATUS, entity_id, f"{current.value} -> unlocked",
                  {"key": "status_change", "from": current.value, "to": "unlocked"})
        self._logbook(i18n.text(self.hass, "unlocked"), entity_id)

        cover_raw = self.storage.get_cover_raw(entity_id)
        previous = self._pre_lock_states.pop(entity_id, CoverStatus.AUTO)
        # Restore PAUSED (pause not expired), MANUAL, or VENTING (vent
        # sensor still open); everything else returns to AUTO.
        target = CoverStatus.AUTO
        pause_until = None
        if previous == CoverStatus.PAUSED:
            pause_until = cover_raw.get("pause_until") if cover_raw else None
            if pause_until and dt_util.now().timestamp() < pause_until:
                target = CoverStatus.PAUSED
        elif previous == CoverStatus.MANUAL:
            target = CoverStatus.MANUAL
        elif previous == CoverStatus.VENTING:
            if cover_raw and self._is_sensor_open(cover_raw, "vent_sensor"):
                target = CoverStatus.VENTING
        # The automation may have been switched on/off during the lock
        target = self._status_for_automation(target, cover_raw)

        sensors = ", ".join(
            s for s in ((cover_raw or {}).get("lock_sensor"), (cover_raw or {}).get("vent_sensor")) if s
        ) or "-"
        _LOGGER.info(
            "[%s] Window %s closed: %s -> %s (kept at %s%%)",
            entity_id, sensors, current.value, target.value,
            self._get_current_position(entity_id),
        )

        self._cover_states[entity_id] = target
        self.storage.update_cover_status(
            entity_id, target.value, pause_until if target == CoverStatus.PAUSED else None
        )
        # Expected position: where the cover is (or is still going), so
        # neither a finished lock move nor the stop is taken as manual
        self._sync_expected_after_protective_exit(entity_id)
        if target != CoverStatus.AUTO:
            if self.data is not None:
                self.async_set_updated_data(self.data)
            return
        # One-shot time-hysteresis bypass for the next apply cycle.
        self._post_protective_exit.add(entity_id)
        self.hass.async_create_task(self.async_request_refresh())

    @staticmethod
    def _status_for_automation(
        status: CoverStatus, cover_raw: dict[str, Any] | None
    ) -> CoverStatus:
        """Align a status restored after a protection with auto_enabled.

        The pre-lock / pre-wind status was recorded when the protection
        started; the automation may have been switched on or off since then
        (switch, import, resume refused while locked). A MANUAL status with
        the automation now on becomes AUTO -- the cover would otherwise never
        be driven again -- and AUTO / PAUSED with the automation off becomes
        MANUAL. Other statuses (VENTING) are returned unchanged.
        """
        auto_enabled = bool((cover_raw or {}).get("auto_enabled", True))
        if status == CoverStatus.MANUAL and auto_enabled:
            return CoverStatus.AUTO
        if status in (CoverStatus.AUTO, CoverStatus.PAUSED) and not auto_enabled:
            return CoverStatus.MANUAL
        return status

    def _sync_expected_after_protective_exit(self, entity_id: str) -> None:
        """Expected position when a cover leaves LOCKED / VENTING / wind protection.

        Normally the current position (the cover stays where the protection
        left it). But when the window closes while the cover is still
        travelling to its lock / vent / wind position, the current reading is
        a mid-travel value (e.g. 34 % on the way to 100 %): taking it as the
        expected position made the end of our own move look like a manual
        command a few seconds later, and the cover was paused. While our
        command is still settling, the commanded position is kept instead;
        the post-settle check then syncs to where the cover really stopped.
        """
        last_cmd = self._last_command_time.get(entity_id, 0)
        if (
            entity_id in self._pending_settle
            and self._last_positions.get(entity_id) is not None
            and (time_mod.monotonic() - last_cmd) < self._settle_time(entity_id)
        ):
            _LOGGER.debug(
                "[%s] Protection ended during our move: expected position kept at %s%%",
                entity_id, self._last_positions.get(entity_id),
            )
            return
        self._update_last_position_from_state(entity_id)

    def _update_last_position_from_state(self, entity_id: str) -> None:
        """Update _last_positions and _last_tilt_positions from current HA state."""
        state = self.hass.states.get(entity_id)
        if state and state.state not in ("unavailable", "unknown"):
            position = self._raw_position(state)
            if position is not None:
                self._last_positions[entity_id] = position
            else:
                _LOGGER.debug(
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

        # Ignore unavailable/unknown states (e.g. during HA shutdown)
        if new_state.state in ("unavailable", "unknown"):
            return

        # Motion bookkeeping first: it must also see the reports received
        # during the grace, wind and settle periods ignored below.
        self._record_motion(entity_id, old_state, new_state)

        # Learn the cover's travel time from our own moves (feeds the settle time)
        self._measure_travel(entity_id, new_state)

        # Ignore during startup grace period (device reconnection can report
        # positions that differ from HA's persisted state)
        if (time_mod.monotonic() - self._startup_time) < STARTUP_GRACE_PERIOD:
            return

        # Ignore manual overrides during wind protection
        if self._wind_protected:
            return

        # Ignore position changes while cover is moving
        if new_state.state in ("opening", "closing"):
            return

        # Ignore position changes during settle time after our own commands
        last_cmd = self._last_command_time.get(entity_id, 0)
        if (time_mod.monotonic() - last_cmd) < self._settle_time(entity_id):
            return

        current_position = self._raw_position(new_state)
        if current_position is None:
            return

        # Slow covers that do not report opening/closing: while the position
        # keeps moving towards our own target, the cover is still travelling
        # from our command -- extend the settle window instead of reading the
        # intermediate position as a manual override.
        if entity_id in self._pending_settle and self._is_progressing_to_target(
            entity_id, old_state, current_position
        ):
            self._last_command_time[entity_id] = time_mod.monotonic()
            return

        # After settle time, sync actual position before override check
        # (HmIP actuators may not reach exact target position)
        if entity_id in self._pending_settle:
            self._pending_settle.discard(entity_id)
            expected_target = self._last_positions.get(entity_id)
            cover_raw = self.storage.get_cover_raw(entity_id)
            settle_threshold = (
                self._cover_val(cover_raw, "min_position_change") if cover_raw else MANUAL_OVERRIDE_TOLERANCE
            )
            if expected_target is not None and abs(current_position - expected_target) > settle_threshold:
                _LOGGER.debug(
                    "[%s] Post-settle: large deviation %d%% vs expected %d%%, checking override",
                    entity_id, current_position, expected_target,
                )
                if self._resend_if_lost(entity_id, current_position):
                    return
                # Fall through to override check below
            else:
                self._last_positions[entity_id] = current_position
                self._sync_tilt_from_state(entity_id, new_state)
                _LOGGER.debug(
                    "[%s] Post-settle sync: position %d%%",
                    entity_id, current_position,
                )
                return

        expected_position = self._last_positions.get(entity_id)

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
            if entity_id in self._safety_holds:
                # A safety rule drives the cover: no pause, the next cycle
                # re-applies the rule's position.
                _LOGGER.debug("[%s] Position change ignored: safety rule active", entity_id)
                return
            if cover.auto_enabled and self._cover_states.get(entity_id) in (CoverStatus.AUTO, CoverStatus.VENTING):
                _LOGGER.info(
                    "[%s] Manual override -> PAUSED (expected pos %s, got %s, expected tilt %s)",
                    entity_id,
                    expected_position,
                    current_position,
                    expected_tilt,
                )
                self.pause_cover(cover)

    def _record_motion(self, entity_id: str, old_state: Any, new_state: Any) -> None:
        """Record position/motion changes of a cover (not attribute-only reports).

        Two uses:
        - the time of the last real change (position, state, opening /
          closing) feeds the stillness check of resume-on-match: Zigbee
          covers re-report attributes (linkquality) every few seconds, so
          state.last_updated never looks still;
        - whether the cover moved at all since our last command, even during
          the settle time: a user counter-order (up/stop) during our move
          brings the cover back to its start position, which must not be
          read as a lost command and resent.
        """
        new_pos = self._raw_position(new_state)
        moving = new_state.state in ("opening", "closing")
        old_usable = old_state is not None and old_state.state not in _UNUSABLE_STATES
        old_pos = self._raw_position(old_state) if old_usable else None
        if moving or not old_usable or old_state.state != new_state.state or old_pos != new_pos:
            self._runtime_dict("_position_changed_at")[entity_id] = time_mod.monotonic()
        move = self._move_start.get(entity_id)
        if move is not None and (
            moving or (new_pos is not None and abs(new_pos - move[1]) > MANUAL_OVERRIDE_TOLERANCE)
        ):
            self._runtime_set("_moved_since_command").add(entity_id)

    def _data_raw_target(
        self, entity_id: str, cover_raw: dict[str, Any], status: CoverStatus
    ) -> int | None:
        """Raw position the current cycle data asks for (as the apply cycle sends it)."""
        cover_data = ((self.data or {}).get("covers") or {}).get(entity_id) or {}
        target = cover_data.get("target_position")
        if not isinstance(target, (int, float)) or isinstance(target, bool):
            return None
        target = int(target)
        if status == CoverStatus.VENTING:
            vent_min = self._cover_val(cover_raw, "vent_position")
            if isinstance(vent_min, (int, float)) and not isinstance(vent_min, bool):
                target = max(target, int(vent_min))
        if cover_raw.get("inverted", False):
            target = 100 - target
        return self._effective_position(entity_id, target)

    def _resend_if_lost(self, entity_id: str, current: int) -> bool:
        """Resend a position command the cover did not react to at all.

        After the settle time, a cover still at the start position of our
        own move (raw positions) most likely never received the command
        (radio/cloud command lost). That is not a manual override: resend
        the command, at most MAX_LOST_COMMAND_RETRIES times, instead of
        pausing the automation. Returns True when the command was resent.

        Never resent when the cover moved at all since the command (a user
        counter-order also ends at the start position), when the automation
        is off, or when the command is no longer what the rules ask for.
        """
        if not self.storage.enabled:
            return False
        move = self._move_start.get(entity_id)
        if move is None:
            return False
        if entity_id in self._runtime_set("_moved_since_command"):
            _LOGGER.debug("[%s] Cover moved since our command: not a lost command", entity_id)
            return False
        _, start_pos, target = move
        if (
            abs(current - start_pos) > MANUAL_OVERRIDE_TOLERANCE
            or abs(current - target) <= MANUAL_OVERRIDE_TOLERANCE
            or self._last_positions.get(entity_id) != target
            or self._wind_protected
        ):
            return False
        # Only moves the apply cycle may still drive: AUTO/VENTING, or a
        # paused/manual cover held by a safety rule (never LOCKED / wind).
        status = self._cover_states.get(entity_id, CoverStatus.AUTO)
        if status in (CoverStatus.LOCKED, CoverStatus.WIND_PROTECTED) or (
            status not in (CoverStatus.AUTO, CoverStatus.VENTING)
            and entity_id not in self._safety_holds
        ):
            return False
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None or self._data_raw_target(entity_id, cover_raw, status) != target:
            return False
        if self._blocked_by_unknown_lock(entity_id, cover_raw, target, current):
            return False
        if self._lost_command_retries is None:
            self._lost_command_retries = {}
        retries = self._lost_command_retries.get(entity_id, 0)
        if retries >= MAX_LOST_COMMAND_RETRIES:
            _LOGGER.warning(
                "[%s] Cover did not move to %d%% after %d resends (still at %d%%)",
                entity_id, target, retries, current,
            )
            self._lost_command_retries.pop(entity_id, None)
            self._move_start.pop(entity_id, None)
            return False
        self._lost_command_retries[entity_id] = retries + 1
        _LOGGER.warning(
            "[%s] Command %d%% apparently lost (cover still at %d%%), resending (%d/%d)",
            entity_id, target, current, retries + 1, MAX_LOST_COMMAND_RETRIES,
        )
        now = time_mod.monotonic()
        self._last_command_time[entity_id] = now
        self._move_start[entity_id] = (now, start_pos, target)
        self._pending_settle.add(entity_id)
        self.hass.async_create_task(self._position_call(entity_id, target))
        return True

    def _blocked_by_unknown_lock(
        self, entity_id: str, cover_raw: dict[str, Any], raw_target: int, raw_current: int
    ) -> bool:
        """Whether a move must wait: it closes a cover on a possibly open window.

        While the lock sensor (window contact) is unavailable/unknown the
        window may be open: a cover is never driven down below its
        lock_position then. Upward moves stay allowed. Positions are raw
        (HA scale); inverted covers are mirrored here.
        """
        blocked_logged = self._runtime_set("_move_blocked_logged")
        if not self._is_sensor_unknown(cover_raw, "lock_sensor"):
            blocked_logged.discard(entity_id)
            return False
        if cover_raw.get("inverted", False):
            target, current = 100 - raw_target, 100 - raw_current
        else:
            target, current = raw_target, raw_current
        lock_pos = self._cover_val(cover_raw, "lock_position")
        if not isinstance(lock_pos, (int, float)) or isinstance(lock_pos, bool):
            lock_pos = 100
        if target < current and target < lock_pos:
            _LOGGER.debug(
                "[%s] Window state unknown: not lowering %d%% -> %d%% (lock position %d%%)",
                entity_id, current, target, lock_pos,
            )
            # Once per blocking episode: the apply cycle re-checks every scan
            if entity_id not in blocked_logged:
                blocked_logged.add(entity_id)
                sensor = cover_raw.get("lock_sensor")
                self._log(LOG_EVENT_STATUS, entity_id,
                          f"Move to {target}% blocked: window {sensor} state unknown",
                          {"key": "move_blocked_window_unknown", "sensor": sensor,
                           "position": target})
            return True
        blocked_logged.discard(entity_id)
        return False

    def _travel_time(self, entity_id: str) -> float | None:
        """Full travel time of a cover.

        Order: value entered on the cover, then the measured value, then the
        global default travel time; None when none is known (30 s settle).
        """
        def _positive(value: Any) -> float | None:
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                return float(value)
            return None

        cover_raw = self.storage.get_cover_raw(entity_id)
        if isinstance(cover_raw, dict):
            for key in ("travel_time", "measured_travel_time"):
                if (value := _positive(cover_raw.get(key))) is not None:
                    return value
        return _positive(getattr(self.storage, "default_travel_time", None))

    def _settle_time(self, entity_id: str) -> float:
        """Seconds after our own command during which moves are not manual.

        At least SETTLE_TIME; longer for slow covers whose full travel time
        (configured or measured) plus a margin exceeds it.
        """
        travel = self._travel_time(entity_id)
        if travel is None:
            return SETTLE_TIME
        return max(SETTLE_TIME, travel + TRAVEL_TIME_MARGIN)

    def _measure_travel(self, entity_id: str, new_state: Any) -> None:
        """Measure the full travel time when a commanded move reaches its target.

        Only moves of at least MIN_MEASURED_DISTANCE % are used, scaled to a
        full 0-100 % travel, and smoothed with the previous measurement. A
        polled cover reports its arrival late (next poll): a new sample is
        capped at MAX_TRAVEL_GROWTH x the previous value so one late poll
        cannot inflate the settle time.
        """
        start = self._move_start.get(entity_id)
        if start is None:
            return
        started_at, start_pos, target = start
        elapsed = time_mod.monotonic() - started_at
        if elapsed > MAX_MEASURED_TRAVEL:
            self._move_start.pop(entity_id, None)
            return
        if new_state.state in ("opening", "closing"):
            return
        try:
            position = int(new_state.attributes.get("current_position"))
        except (ValueError, TypeError):
            return
        if abs(position - target) > MANUAL_OVERRIDE_TOLERANCE:
            return
        self._move_start.pop(entity_id, None)
        # The command arrived: a later lost command gets fresh resends
        if self._lost_command_retries:
            self._lost_command_retries.pop(entity_id, None)
        distance = abs(start_pos - target)
        if distance < MIN_MEASURED_DISTANCE or elapsed < 1:
            return
        full = min(elapsed * 100 / distance, MAX_MEASURED_TRAVEL)
        cover_raw = self.storage.get_cover_raw(entity_id)
        previous = cover_raw.get("measured_travel_time") if isinstance(cover_raw, dict) else None
        if isinstance(previous, (int, float)) and not isinstance(previous, bool) and previous > 0:
            if full > previous * MAX_TRAVEL_GROWTH:
                # Capped sample: already a bounded step up. Averaging it with
                # the previous value again halved the growth, so a cover whose
                # first measurement was too short needed many moves to reach
                # its real travel time (settle time too short meanwhile).
                full = previous * MAX_TRAVEL_GROWTH
            else:
                full = (previous + full) / 2
        full = round(full, 1)
        _LOGGER.debug("[%s] Measured travel time: %.1f s", entity_id, full)
        self.storage.update_cover_measured_travel(entity_id, full)

    def _is_progressing_to_target(
        self, entity_id: str, old_state: Any, current_position: int
    ) -> bool:
        """Return True if the cover moved strictly closer to its commanded target."""
        target = self._last_positions.get(entity_id)
        if target is None or old_state is None:
            return False
        try:
            old_position = int(old_state.attributes.get("current_position"))
        except (ValueError, TypeError):
            return False
        return abs(current_position - target) < abs(old_position - target)

    def pause_cover(self, cover: CoverConfig, manual: bool = True) -> None:
        """Pause automation for a cover.

        Protective statuses (wind, window lock) and disabled automation
        (MANUAL) take precedence over a pause: overwriting them would only be
        undone by the next sync cycle, re-sending protective commands.

        manual: the pause comes from a detected manual override (the cover
        was moved by hand). Explicit pauses (pause / pause_all services) pass
        False: resume-on-match must not end them -- the user asked for a
        pause, not for a one-off position.
        """
        prev = self._cover_states.get(cover.entity_id, CoverStatus.AUTO)
        if prev in (CoverStatus.WIND_PROTECTED, CoverStatus.LOCKED, CoverStatus.MANUAL):
            _LOGGER.debug(
                "[%s] Pause ignored: cover is %s", cover.entity_id, prev.value
            )
            return
        self._cover_states[cover.entity_id] = CoverStatus.PAUSED
        self._runtime_dict("_pause_manual")[cover.entity_id] = manual
        if prev != CoverStatus.PAUSED:
            if self._paused_at is None:
                self._paused_at = {}
            self._paused_at[cover.entity_id] = time_mod.monotonic()
            self._log(LOG_EVENT_STATUS, cover.entity_id, f"{prev.value} -> paused",
                      {"key": "status_change", "from": prev.value, "to": "paused"})
        duration = cover.pause_duration if cover.pause_duration is not None else self.storage.pause_duration
        pause_until = dt_util.now().timestamp() + (duration * 60)
        self.storage.update_cover_status(
            cover.entity_id, CoverStatus.PAUSED.value, pause_until
        )
        if prev != CoverStatus.PAUSED:
            self._logbook(
                i18n.text(self.hass, "paused", minutes=duration),
                cover.entity_id,
            )
        if self.data is not None:
            self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str, logbook_text: str | None = None) -> None:
        """Resume automation for a cover.

        logbook_text replaces the plain "resumed" logbook entry (automatic
        resume, with its reason).
        """
        # Wind protection cannot be overridden manually
        if self._wind_protected:
            return
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw:
            # Don't override LOCKED status if lock/vent sensor is still active,
            # nor while the window state is unknown (possibly open window).
            # A refused resume is still the user's wish: the unlock restores
            # AUTO instead of the recorded pre-lock status (e.g. MANUAL).
            if self._cover_states.get(entity_id) == CoverStatus.LOCKED:
                if self._is_sensor_open(cover_raw, "lock_sensor") or self._is_sensor_open(cover_raw, "vent_sensor"):
                    self._pre_lock_states[entity_id] = CoverStatus.AUTO
                    self._persist_runtime_state()
                    return
                if self._is_sensor_unknown(cover_raw, "lock_sensor"):
                    _LOGGER.info("[%s] Resume refused: window state unknown, cover stays locked", entity_id)
                    self._pre_lock_states[entity_id] = CoverStatus.AUTO
                    self._persist_runtime_state()
                    return
            prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
            # Resuming ends any protective episode: a stale pre-lock status
            # would otherwise be restored by a later unlock.
            self._pre_lock_states.pop(entity_id, None)
            self._runtime_dict("_pause_manual").pop(entity_id, None)
            # Resume to VENTING if vent sensor is still open
            if self._is_sensor_open(cover_raw, "vent_sensor"):
                target = CoverStatus.VENTING
                self._cover_states[entity_id] = CoverStatus.VENTING
                self.storage.update_cover_status(entity_id, CoverStatus.VENTING.value, None)
                self._logbook(i18n.text(self.hass, "resumed_venting"), entity_id)
            else:
                target = CoverStatus.AUTO
                self._cover_states[entity_id] = CoverStatus.AUTO
                self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
                self._logbook(logbook_text or i18n.text(self.hass, "resumed"), entity_id)
            if prev != target:
                _LOGGER.debug("[%s] Resumed: %s -> %s", entity_id, prev.value, target.value)
                self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> {target.value}",
                          {"key": "status_change", "from": prev.value, "to": target.value})
            # Sync expected position to current to prevent immediate re-pause
            self._update_last_position_from_state(entity_id)
            if self.data is not None:
                self.async_set_updated_data(self.data)

    def _sync_cover_statuses(self) -> None:
        """Sync cover statuses from sensor states.

        Updates _cover_states and storage for all covers. Called once per
        update cycle to avoid side effects in property accessors.
        Priority: LOCKED (window open) > WIND_PROTECTED > VENTING > PAUSED
        > AUTO > MANUAL.
        """
        # Check wind protection first (global)
        self._check_wind_protection()

        for entity_id in self.storage._data.get("covers", {}):
            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue
            self._track_missing_lock_sensor(entity_id, cover_raw)

            # Wind protection: above everything except an open window (lock)
            if self._wind_protected:
                self._protect_one_from_wind(entity_id, cover_raw)
                continue

            # An unavailable lock/vent sensor is not "closed": keep the
            # protective status unchanged this cycle (no lock, no unlock).
            sensor_unknown = (
                self._is_sensor_unknown(cover_raw, "lock_sensor")
                or self._is_sensor_unknown(cover_raw, "vent_sensor")
            )

            # Check lock sensor state (window contact)
            if self._is_sensor_open(cover_raw, "lock_sensor"):
                if self._cover_states.get(entity_id) != CoverStatus.LOCKED:
                    lock_pos = self._cover_val(cover_raw, "lock_position")
                    current = self._get_current_position(entity_id)
                    if self._lock_moves(cover_raw, current, lock_pos):
                        lock_tilt = self._cover_val(cover_raw, "lock_tilt_position")
                        self._lock_cover(entity_id, lock_pos, lock_tilt=lock_tilt)
                    else:
                        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
                        self._pre_lock_states[entity_id] = CoverStatus.AUTO if prev == CoverStatus.PAUSED else prev
                        self._lock_in_place(entity_id, cover_raw)
                self._sensor_unknown_kept.discard(entity_id)
                continue

            if sensor_unknown and self._cover_states.get(entity_id) in (
                CoverStatus.LOCKED, CoverStatus.VENTING,
            ):
                self._keep_status_sensor_unknown(entity_id, cover_raw)
                continue
            if entity_id in self._sensor_unknown_kept:
                self._sensor_unknown_kept.discard(entity_id)
                _LOGGER.debug("[%s] Lock/vent sensor available again", entity_id)

            # Check vent sensor state - also above auto_enabled
            if self._is_sensor_open(cover_raw, "vent_sensor"):
                current_status = self._cover_states.get(entity_id, CoverStatus.AUTO)
                # Respect PAUSED during venting (manual override)
                if current_status == CoverStatus.PAUSED:
                    pause_until = cover_raw.get("pause_until")
                    if pause_until and dt_util.now().timestamp() > pause_until:
                        # Pause expired -> back to VENTING. The cover may have
                        # been lowered manually during the pause: raise it to
                        # the vent position again (logs the status change).
                        _LOGGER.debug("[%s] Pause expired: paused -> venting", entity_id)
                        self._enter_venting(entity_id, cover_raw, "pause expired, vent open")
                elif current_status != CoverStatus.VENTING:
                    self._enter_venting(
                        entity_id, cover_raw, f"vent sensor {cover_raw.get('vent_sensor')} open"
                    )
                continue

            # If was locked/venting but sensors now closed, restore auto
            if self._cover_states.get(entity_id) in (CoverStatus.LOCKED, CoverStatus.VENTING):
                self._unlock_cover(entity_id)
                continue

            if not cover_raw.get("auto_enabled", True):
                # Persist MANUAL like the LOCKED/VENTING branches do, so the
                # status survives a restart (which resets all statuses to AUTO)
                # and the panel, which renders the persisted cover status,
                # reflects the disabled automation instead of showing AUTO.
                prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
                if prev != CoverStatus.MANUAL:
                    _LOGGER.debug("[%s] Automation disabled: %s -> manual", entity_id, prev.value)
                    self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> manual",
                              {"key": "status_change", "from": prev.value, "to": "manual"})
                    self._cover_states[entity_id] = CoverStatus.MANUAL
                    self.storage.update_cover_status(entity_id, CoverStatus.MANUAL.value, None)
                continue

            # Check pause expiry
            status = self._cover_states.get(entity_id, CoverStatus.AUTO)
            if status == CoverStatus.PAUSED:
                pause_until = cover_raw.get("pause_until")
                if pause_until and dt_util.now().timestamp() > pause_until:
                    _LOGGER.debug("[%s] Pause expired: paused -> auto", entity_id)
                    self._log(LOG_EVENT_STATUS, entity_id, "paused -> auto",
                              {"key": "status_change", "from": "paused", "to": "auto"})
                    self._cover_states[entity_id] = CoverStatus.AUTO
                    self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
                    # Sync expected position to prevent false override after resume
                    self._update_last_position_from_state(entity_id)

        # Protective state must survive a restart (see _restore_cover_states)
        self._persist_runtime_state()

    def _keep_status_sensor_unknown(self, entity_id: str, cover_raw: dict[str, Any]) -> None:
        """Keep LOCKED/VENTING while a lock/vent sensor is unavailable (log once)."""
        status = self._cover_states.get(entity_id, CoverStatus.AUTO)
        if entity_id in self._sensor_unknown_kept:
            _LOGGER.debug("[%s] Lock/vent sensor unavailable, keeping %s", entity_id, status.value)
            return
        self._sensor_unknown_kept.add(entity_id)
        sensors = ", ".join(
            s for s in (cover_raw.get("lock_sensor"), cover_raw.get("vent_sensor")) if s
        )
        current = self._get_current_position(entity_id)
        _LOGGER.debug(
            "[%s] Sensor %s unavailable: keeping %s (kept at %s%%)",
            entity_id, sensors, status.value, current,
        )
        self._log(LOG_EVENT_STATUS, entity_id, f"{status.value} kept (sensor unavailable)",
                  {"key": "sensor_unavailable", "status": status.value,
                   "sensor": sensors, "position": current})

    def get_cover_status(self, entity_id: str) -> CoverStatus:
        """Get automation status for a cover (read-only, no side effects)."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None:
            return CoverStatus.MANUAL

        live = self._cover_states.get(entity_id, CoverStatus.AUTO)
        if not cover_raw.get("auto_enabled", True):
            # Protective statuses also act on covers with automation off
            # (window open -> locked, storm -> wind position): report them.
            if live in (CoverStatus.LOCKED, CoverStatus.WIND_PROTECTED):
                return live
            return CoverStatus.MANUAL

        return live

    def get_active_rules(self) -> dict[str, list[str]]:
        """Get currently active rules and their matched covers.

        Returns dict of {rule_id: [cover_entity_ids]}.
        """
        if self.data and "active_rules" in self.data:
            return self.data["active_rules"]
        return {}

    def get_live_cover_data(self) -> dict[str, dict[str, Any]]:
        """Get live runtime data for all covers."""
        if not self.data:
            return {}
        return {
            entity_id: self._live_cover_entry(entity_id, cover_data)
            for entity_id, cover_data in self.data.get("covers", {}).items()
        }

    def get_live_cover(self, entity_id: str) -> dict[str, Any] | None:
        """Get live runtime data for one cover, None before the first refresh."""
        cover_data = (self.data or {}).get("covers", {}).get(entity_id)
        if cover_data is None:
            return None
        return self._live_cover_entry(entity_id, cover_data)

    def _live_cover_entry(self, entity_id: str, cover_data: dict[str, Any]) -> dict[str, Any]:
        """Build the live data dict for one cover from its update-cycle result."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        pause_until = cover_raw.get("pause_until") if cover_raw else None
        rule_id = cover_data.get("matching_rule_id")
        rule_name = None
        if rule_id:
            rule = self.storage.rules.get(rule_id)
            rule_name = rule.name if rule else rule_id
        # Comfort mode from engine cache
        comfort = self.engine._last_comfort_mode.get(entity_id)
        return {
            "target_position": cover_data.get("target_position"),
            "hysteresis": self._hysteresis_info.get(entity_id),
            "pause_until": pause_until,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "comfort_mode": comfort.value if comfort else None,
            "last_change": cover_raw.get("last_position_change") if cover_raw else None,
        }

    # ---- Public read-only accessors for entities / dashboard card ----

    @property
    def wind_protected(self) -> bool:
        """Whether wind protection is currently active."""
        return self._wind_protected

    def get_wind_speed(self) -> float | None:
        """Current wind speed from the configured sensor (None if unknown)."""
        return self._get_wind_speed()

    def get_logical_position(self, entity_id: str) -> int | None:
        """Current position on the rules' scale (inverted covers mirrored)."""
        return self._get_current_position(entity_id)

    def get_cover_live(self, entity_id: str) -> dict[str, Any]:
        """Live runtime data of one cover (rule, target, pause, comfort)."""
        cover_data = (self.data or {}).get("covers", {}).get(entity_id, {})
        cover_raw = self.storage.get_cover_raw(entity_id) or {}
        rule_id = cover_data.get("matching_rule_id")
        rule_name = None
        if rule_id:
            rule = self.storage.rules.get(rule_id)
            rule_name = rule.name if rule else rule_id
        comfort = self.engine._last_comfort_mode.get(entity_id)
        return {
            "target_position": cover_data.get("target_position"),
            "rule_id": rule_id,
            "rule_name": rule_name,
            "safety": bool(cover_data.get("safety", False)),
            "pause_until": cover_raw.get("pause_until"),
            "comfort_mode": comfort.value if comfort else None,
            "last_change": cover_raw.get("last_position_change"),
        }

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

    def _logbook(self, message: str, entity_id: str | None = None) -> None:
        """Write an entry to the HA logbook when enabled in settings."""
        if not self.storage.logbook_enabled:
            return
        async_log_entry(
            self.hass,
            i18n.text(self.hass, "logbook_name"),
            message,
            domain=DOMAIN,
            entity_id=entity_id,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and evaluate rules."""
        # Compile native Home Assistant conditions (async) so the rule
        # evaluation below can run them synchronously; track new entities.
        try:
            if await self.engine.async_prepare_ha_conditions():
                self._setup_state_tracking()
        except Exception:  # noqa: BLE001 -- never block the update cycle
            _LOGGER.exception("Failed to prepare Home Assistant conditions")

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

        # Safety takeovers/releases only act once commands may be sent
        in_grace = (time_mod.monotonic() - self._startup_time) < STARTUP_GRACE_PERIOD

        for entity_id, cover in self.storage.covers.items():
            status = self.get_cover_status(entity_id)
            target_position: int | None = None
            target_tilt_position: int | None = None
            matching_rule_id: str | None = None

            if not in_grace and status == CoverStatus.PAUSED and self._resume_on_match(cover):
                status = self.get_cover_status(entity_id)
            engine_result = self._evaluate_cover_rules(cover, status)
            safety = _is_safety(engine_result)
            if not in_grace and self._update_safety_hold(
                entity_id, engine_result if safety else None, status
            ):
                # Released a paused cover: evaluate it as AUTO right away
                status = self.get_cover_status(entity_id)
                engine_result = self._evaluate_cover_rules(cover, status)
                safety = _is_safety(engine_result)
            if engine_result is not None:
                target_position = engine_result.position
                target_tilt_position = engine_result.tilt_position
                matching_rule_id = engine_result.rule_id
                if matching_rule_id:
                    active_rules.setdefault(matching_rule_id, []).append(entity_id)

            # Always refresh comfort mode for live display (independent of rules)
            self.engine._get_comfort_mode(cover)

            # Log rule match changes
            prev_rule = self._last_matching_rules.get(entity_id)
            if matching_rule_id != prev_rule:
                self._last_matching_rules[entity_id] = matching_rule_id
                if matching_rule_id:
                    rule_name = self.storage.rules.get(matching_rule_id)
                    rn = rule_name.name if rule_name else matching_rule_id
                    self._log(
                        LOG_EVENT_RULE, entity_id, f"{rn} -> {target_position}%",
                        {"key": "rule", "rule_id": matching_rule_id, "rule_name": rn,
                         "position": target_position},
                    )

            result["covers"][entity_id] = {
                "status": status.value,
                "target_position": target_position,
                "target_tilt_position": target_tilt_position,
                "facade_id": cover.facade_id,
                "matching_rule_id": matching_rule_id,
                "safety": safety,
            }

        result["active_rules"] = active_rules

        # Store result first so async_apply_positions can use it
        self.data = result

        # Skip position application during startup grace period to avoid
        # unnecessary movements caused by incomplete sensor data (e.g. sun.sun,
        # temperature sensors not yet stable), which would trigger low-priority
        # fallback rules instead of the correct shading rules.
        startup_elapsed = time_mod.monotonic() - self._startup_time
        if startup_elapsed < STARTUP_GRACE_PERIOD:
            if self._startup_skip:
                self._startup_skip = False
                # Initialize _last_positions from current HA state
                for eid in self.storage._data.get("covers", {}):
                    self._update_last_position_from_state(eid)
                _LOGGER.debug("Startup: initialized positions from HA state")
            _LOGGER.debug(
                "Startup grace period: skipping position application (%ds remaining)",
                int(STARTUP_GRACE_PERIOD - startup_elapsed),
            )
            return result

        # Re-sync positions after grace period ends (devices now fully
        # connected, positions stable -- overwrite stale startup values)
        if not self._grace_synced:
            self._grace_synced = True
            for eid in self.storage._data.get("covers", {}):
                self._update_last_position_from_state(eid)
            _LOGGER.info("Grace period ended: re-synced cover positions from HA state")

        # Apply calculated positions to covers
        await self.async_apply_positions()

        return result

    def _resume_on_match(self, cover: CoverConfig) -> bool:
        """End a manual pause when the cover is back at its rule's position.

        Two cases: the cover was put back by hand where the rule wants it, or
        the winning rule changed and now asks for the position the cover was
        left at. Only a PAUSED cover (never MANUAL, i.e. automation switched
        off, nor a protective status). Conditions: option enabled (cover or
        Settings), grace period after the pause started, cover still (not
        moving, no position report for SETTLE_TIME), a rule gives a target
        and the position (and the rule's tilt, when set) match it within the
        minimum position change. Returns True when the cover was resumed.
        """
        entity_id = cover.entity_id
        if self._cover_states.get(entity_id) != CoverStatus.PAUSED or not self.storage.enabled:
            return False
        enabled = cover.pause_resume_on_match
        if enabled is None:
            enabled = self.storage.pause_resume_on_match
        if not enabled:
            return False
        # Only pauses from a manual override; an explicit pause (service)
        # lasts its duration. Origin unknown (restored after a restart):
        # treated as manual, the previous behaviour.
        if not self._runtime_dict("_pause_manual").get(entity_id, True):
            return False
        now_mono = time_mod.monotonic()
        paused_at = (self._paused_at or {}).get(entity_id)
        if paused_at is not None and now_mono - paused_at < RESUME_MATCH_GRACE:
            return False
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (*_UNUSABLE_STATES, "opening", "closing"):
            return False
        # Stillness from the last real position/motion change: last_updated
        # also moves on attribute-only reports (Zigbee linkquality), so a
        # still cover never looked still. Unknown (no change seen since
        # startup): fall back to the state's last_changed.
        changed_at = self._runtime_dict("_position_changed_at").get(entity_id)
        if changed_at is not None:
            if now_mono - changed_at < SETTLE_TIME:
                return False
        else:
            last_changed = getattr(state, "last_changed", None)
            if isinstance(last_changed, datetime) and (
                (dt_util.utcnow() - last_changed).total_seconds() < SETTLE_TIME
            ):
                return False
        current = self._raw_position(state)
        if current is None:
            return False
        result = self.engine.evaluate_cover(cover)
        if result is None or result.position is None:
            return False
        cover_raw = self.storage.get_cover_raw(entity_id) or {}
        target = int(result.position)
        if self._is_sensor_open(cover_raw, "vent_sensor"):
            target = max(target, int(self._cover_val(cover_raw, "vent_position")))
        if cover_raw.get("inverted", False):
            target = 100 - target
        target = self._effective_position(entity_id, target)
        tolerance = self._cover_val(cover_raw, "min_position_change")
        if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
            tolerance = MANUAL_OVERRIDE_TOLERANCE
        if abs(current - target) > tolerance:
            return False
        tilt_target = getattr(result, "tilt_position", None)
        if tilt_target is not None and cover_raw.get("supports_tilt", False):
            tilt_now = state.attributes.get("current_tilt_position")
            if tilt_now is not None:
                try:
                    tilt_now = int(tilt_now)
                except (TypeError, ValueError):
                    tilt_now = None
            if tilt_now is not None:
                wanted = 100 - int(tilt_target) if cover_raw.get("inverted_tilt", False) else int(tilt_target)
                if abs(tilt_now - wanted) > tolerance:
                    return False
        rule = self.storage.rules.get(result.rule_id) if result.rule_id else None
        rule_name = rule.name if rule else (result.rule_id or "-")
        _LOGGER.info(
            "[%s] Pause ended: position %d%% matches rule %s", entity_id, current, rule_name,
        )
        self.resume_cover(
            entity_id, logbook_text=i18n.text(self.hass, "resumed_match", rule=rule_name),
        )
        if self._cover_states.get(entity_id) == CoverStatus.PAUSED:
            return False  # resume refused (wind protection)
        (self._paused_at or {}).pop(entity_id, None)
        return True

    def _evaluate_cover_rules(self, cover: CoverConfig, status: CoverStatus) -> Any:
        """Evaluate the rules that may drive a cover in its current status.

        AUTO/VENTING covers with the automation enabled use all rules. Covers
        that are paused, manual, wind protected, or with the global automation
        disabled only follow safety rules. LOCKED covers follow none.
        """
        if status in (CoverStatus.AUTO, CoverStatus.VENTING) and self.storage.enabled:
            return self.engine.evaluate_cover(cover)
        if status == CoverStatus.LOCKED:
            return None
        result = self.engine.evaluate_cover(cover, safety_only=True)
        return result if _is_safety(result) else None

    def _update_safety_hold(
        self, entity_id: str, target: Any, status: CoverStatus
    ) -> bool:
        """Track which covers a safety rule drives; handle takeover/release.

        On release a paused cover returns to AUTO, a wind protected one goes
        back to the wind position (wind still active), manual covers and a
        disabled automation get no further command.
        Returns True when the cover status changed (pause cancelled).
        """
        new_rule = target.rule_id if target is not None else None
        prev_rule = self._safety_holds.get(entity_id)
        if new_rule == prev_rule:
            return False
        if new_rule:
            self._safety_holds[entity_id] = new_rule
            if prev_rule is not None:
                _LOGGER.debug("[%s] Safety rule %s -> %s", entity_id, prev_rule, new_rule)
                return False
            rule_name = target.rule_name or new_rule
            status_val = status.value if self.storage.enabled else f"{status.value}, automation off"
            _LOGGER.info(
                "[%s] Safety rule '%s' takes over (%s) -> %d%%",
                entity_id, rule_name, status_val, target.position,
            )
            self._log(LOG_EVENT_RULE, entity_id,
                      f"Safety rule {rule_name} takes over ({status_val}) -> {target.position}%",
                      {"key": "safety_takeover", "rule_id": new_rule, "rule_name": rule_name,
                       "status": status.value, "position": target.position})
            return False

        # Released
        self._safety_holds.pop(entity_id, None)
        rule = self.storage.rules.get(prev_rule)
        rule_name = rule.name if rule else prev_rule
        live = self._cover_states.get(entity_id, CoverStatus.AUTO)
        changed = False
        if status == CoverStatus.PAUSED and live == CoverStatus.PAUSED:
            # The pause is cancelled: the cover returns to normal automation
            self._cover_states[entity_id] = CoverStatus.AUTO
            self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
            self._update_last_position_from_state(entity_id)
            self._log(LOG_EVENT_STATUS, entity_id, "paused -> auto",
                      {"key": "status_change", "from": "paused", "to": "auto"})
            released_to = "paused -> auto"
            changed = True
        elif live == CoverStatus.WIND_PROTECTED and self._wind_protected:
            self._send_wind_position(entity_id)
            released_to = f"wind protection -> {self._wind_position()}%"
        else:
            released_to = status.value if self.storage.enabled else "automation off"
        _LOGGER.info("[%s] Safety rule '%s' released (%s)", entity_id, rule_name, released_to)
        self._log(LOG_EVENT_RULE, entity_id, f"Safety rule {rule_name} released ({released_to})",
                  {"key": "safety_release", "rule_id": prev_rule, "rule_name": rule_name,
                   "status": status.value})
        return changed

    def rename_rule_references(self, old_id: str, new_id: str) -> None:
        """Follow a rule id rename in runtime state (no spurious rule change)."""
        for mapping in (self._last_move_rule, self._last_matching_rules, self._safety_holds):
            for key, value in mapping.items():
                if value == old_id:
                    mapping[key] = new_id
        if not isinstance(self.data, dict):
            return
        for cover_data in (self.data.get("covers") or {}).values():
            if isinstance(cover_data, dict) and cover_data.get("matching_rule_id") == old_id:
                cover_data["matching_rule_id"] = new_id
        active = self.data.get("active_rules")
        if isinstance(active, dict) and old_id in active:
            self.data["active_rules"] = {
                (new_id if key == old_id else key): value for key, value in active.items()
            }

    async def async_apply_positions(self) -> None:
        """Apply calculated positions to covers with hysteresis.

        Serialised: an apply cycle sleeping in the command stagger must not
        interleave with the next one (a stale target could be sent after a
        newer one, or both cycles command the same cover).
        """
        if self._apply_lock is None:
            self._apply_lock = asyncio.Lock()
        async with self._apply_lock:
            await self._async_apply_positions_locked()

    async def _async_apply_positions_locked(self) -> None:
        """Apply calculated positions (caller holds the apply lock)."""
        if not self.data:
            return

        now = dt_util.now().timestamp()
        stagger = self.storage.command_stagger
        command_sent = False

        for entity_id, cover_data in self.data.get("covers", {}).items():
            # Use live status from _cover_states instead of snapshot
            status = self._cover_states.get(entity_id, CoverStatus.AUTO)
            # A safety rule also drives paused/manual/wind covers (never LOCKED)
            safety = cover_data.get("safety") is True and status != CoverStatus.LOCKED
            if status not in (CoverStatus.AUTO, CoverStatus.VENTING) and not safety:
                # A new protective/paused state supersedes a pending
                # protective-exit bypass -- drop it so it cannot skip the
                # time hysteresis on an unrelated move later.
                self._post_protective_exit.discard(entity_id)
                self._hysteresis_info[entity_id] = None
                if cover_data.get("target_position") is not None:
                    _LOGGER.debug("[%s] No command: status %s", entity_id, status.value)
                continue

            target = cover_data.get("target_position")
            if target is None:
                self._hysteresis_info[entity_id] = None
                continue

            cover_raw = self.storage.get_cover_raw(entity_id)
            if cover_raw is None:
                continue

            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unavailable", "unknown"):
                continue

            # Skip covers that are physically moving. HmIP-style actuators keep
            # reporting the pre-move position until travel finishes; for a long
            # move whose travel time exceeds SETTLE_TIME, the override check
            # below would misread that stale position as a manual override and
            # falsely PAUSE the cover. _pending_settle is left intact so the
            # post-settle sync runs once the cover reports its final position.
            if state.state in ("opening", "closing"):
                continue

            current = self._raw_position(state)
            if current is None:
                continue

            # Enforce vent minimum position (logical, before inversion)
            original_target = target
            if status == CoverStatus.VENTING:
                vent_min = self._cover_val(cover_raw, "vent_position")
                if target < vent_min:
                    target = vent_min
                    _LOGGER.debug("[%s] VENTING: clamped %d%% -> %d%% (vent min)", entity_id, original_target, target)

            # Handle inverted covers (100% = closed)
            if cover_raw.get("inverted", False):
                target = 100 - target
            # Open/close-only covers reach 0 or 100 only: compare with that,
            # otherwise an intermediate target is re-commanded every cycle.
            target = self._effective_position(entity_id, target)

            # Our own target changed (rule / scenario / rule disabled / rule
            # edited) while the cover is still travelling to the position this
            # cycle commanded before. The stale position it reports is not a
            # manual override: send the new target right away instead of
            # waiting for the settle time and misreading the travel.
            expected_before = self._last_positions.get(entity_id)
            own_target_change = (
                entity_id in self._pending_settle
                and expected_before is not None
                and self._last_sent_target.get(entity_id) == expected_before
                and target != expected_before
            )
            if own_target_change:
                _LOGGER.info(
                    "[%s] Target changed during travel (%d%% -> %d%%), re-commanding",
                    entity_id, expected_before, target,
                )
                self._pending_settle.discard(entity_id)

            # Skip covers still settling after our commands (vent/lock moves, rule commands)
            last_cmd_t = self._last_command_time.get(entity_id, 0)
            if entity_id in self._pending_settle:
                if (time_mod.monotonic() - last_cmd_t) < self._settle_time(entity_id):
                    continue
                # Settle time passed: check if position deviated significantly (manual override)
                self._pending_settle.discard(entity_id)
                expected_target = self._last_positions.get(entity_id)
                settle_threshold = self._cover_val(cover_raw, "min_position_change")
                if expected_target is not None and abs(current - expected_target) > settle_threshold:
                    _LOGGER.debug(
                        "[%s] Post-settle: large deviation %d%% vs expected %d%%",
                        entity_id, current, expected_target,
                    )
                    # Not moved at all: lost command, resent (not a manual move)
                    if self._resend_if_lost(entity_id, current):
                        continue
                    # Don't sync -- let override check below detect the manual move
                else:
                    self._last_positions[entity_id] = current
                    self._sync_tilt_from_state(entity_id, state)
                    _LOGGER.debug("[%s] Post-settle sync: position %d%%", entity_id, current)

            # Detect manual override missed by state-change handler (e.g. during settle time)
            expected = self._last_positions.get(entity_id)
            if (
                not own_target_change
                and not safety
                and expected is not None
                and abs(current - expected) > MANUAL_OVERRIDE_TOLERANCE
                and (time_mod.monotonic() - self._last_command_time.get(entity_id, 0))
                >= self._settle_time(entity_id)
                and entity_id not in self._pending_settle
                and status in (CoverStatus.AUTO, CoverStatus.VENTING)
            ):
                cover = self.storage.covers.get(entity_id)
                if cover and cover.auto_enabled:
                    _LOGGER.info(
                        "[%s] Manual override detected in apply cycle (expected %d, got %d)",
                        entity_id, expected, current,
                    )
                    self.pause_cover(cover)
                    continue

            # Window state unknown (lock sensor unavailable, e.g. after a
            # restart): never lower the cover below its lock position.
            if self._blocked_by_unknown_lock(entity_id, cover_raw, target, current):
                self._hysteresis_info[entity_id] = None
                continue

            # Check hysteresis: minimum position change
            # Fully open/closed targets are honoured once even below
            # min_change: otherwise a cover resting a few percent short of an
            # end stop (e.g. 3% vs 0%) would never reach it. Once that end
            # stop has been commanded, normal hysteresis applies again so a
            # motor that settles at 1% is not re-commanded forever.
            min_change = self._cover_val(cover_raw, "min_position_change")
            position_diff = abs(current - target)
            endpoint_pending = (
                target in (0, 100)
                and self._last_sent_target.get(entity_id) != target
            )
            # A safety rule's new target is sent once regardless of min_change
            safety_pending = safety and self._last_sent_target.get(entity_id) != target
            if 0 < position_diff < min_change and not endpoint_pending and not safety_pending:
                _LOGGER.debug(
                    "Skipping %s: position change %d < min %d",
                    entity_id, position_diff, min_change
                )
                self._hysteresis_info[entity_id] = "position"
                self._last_positions[entity_id] = current
                self._sync_tilt_from_state(entity_id, state)
                # The position is close enough, but a tilt-only change of the
                # rule must still reach the slats.
                self._apply_rule_tilt(entity_id, cover_raw, cover_data, position_changed=False)
                continue

            # Check hysteresis: minimum time between changes.
            # Skipped on rule change (semantic state change like Day -> Night)
            # OR when the cover just exited a protective status (LOCKED /
            # VENTING) -- otherwise a long min_time_between_changes leaves
            # the cover at vent/lock position long after the sensor cleared.
            min_time = self._cover_val(cover_raw, "min_time_between_changes")
            last_change = cover_raw.get("last_position_change")
            current_rule = cover_data.get("matching_rule_id")
            rule_changed = (
                entity_id in self._last_move_rule
                and current_rule != self._last_move_rule[entity_id]
            )
            status_just_reset = entity_id in self._post_protective_exit
            if (
                position_diff > 0
                and last_change
                and (now - last_change) < min_time
                and not rule_changed
                and not status_just_reset
                and not own_target_change
                and not safety
            ):
                _LOGGER.debug(
                    "Skipping %s: only %ds since last change (min %ds)",
                    entity_id, int(now - last_change), min_time
                )
                self._hysteresis_info[entity_id] = "time"
                self._last_positions[entity_id] = current
                self._sync_tilt_from_state(entity_id, state)
                self._apply_rule_tilt(entity_id, cover_raw, cover_data, position_changed=False)
                continue
            # Past the time-hysteresis check: consume the one-shot bypass.
            self._post_protective_exit.discard(entity_id)

            position_changed = current != target
            if position_changed:
                if command_sent and stagger > 0:
                    await asyncio.sleep(stagger)
                    # The status may have changed during the stagger (manual
                    # pause, window opened, wind): don't send a stale command.
                    if (
                        (not safety and (self._wind_protected or not self.storage.enabled))
                        or self._cover_states.get(entity_id, CoverStatus.AUTO) != status
                    ):
                        _LOGGER.debug(
                            "[%s] Status changed during stagger, skipping command", entity_id
                        )
                        continue
                _LOGGER.info("[%s] Moving %d%% -> %d%%", entity_id, current, target)
                self._hysteresis_info[entity_id] = None
                self._last_positions[entity_id] = target
                self._last_sent_target[entity_id] = target
                self._last_command_time[entity_id] = time_mod.monotonic()
                self._move_start[entity_id] = (time_mod.monotonic(), current, target)
                self._runtime_set("_moved_since_command").discard(entity_id)
                self._last_move_rule[entity_id] = cover_data.get("matching_rule_id")
                self._pending_settle.add(entity_id)
                # A new command: lost-command resends start from zero
                if self._lost_command_retries:
                    self._lost_command_retries.pop(entity_id, None)
                self._log(
                    LOG_EVENT_POSITION, entity_id, f"{current}% -> {target}%",
                    {"key": "position", "from": current, "to": target,
                     "rule_id": cover_data.get("matching_rule_id")},
                )
                rule_id = cover_data.get("matching_rule_id")
                rule_obj = self.storage.rules.get(rule_id) if rule_id else None
                if rule_obj:
                    logbook_msg = i18n.text(
                        self.hass, "moved_rule",
                        from_pos=current, to_pos=target, rule=rule_obj.name,
                    )
                else:
                    logbook_msg = i18n.text(
                        self.hass, "moved", from_pos=current, to_pos=target
                    )
                self._logbook(
                    logbook_msg,
                    entity_id,
                )
                await self._async_send_position(entity_id, target)
                self.storage.update_cover_last_change(entity_id, now)
                command_sent = True
            else:
                self._hysteresis_info[entity_id] = None
                self._last_positions[entity_id] = current
                self._sync_tilt_from_state(entity_id, state)

            self._apply_rule_tilt(entity_id, cover_raw, cover_data, position_changed)

    def _apply_rule_tilt(
        self,
        entity_id: str,
        cover_raw: dict[str, Any],
        cover_data: dict[str, Any],
        position_changed: bool,
    ) -> None:
        """Send the rule's tilt when it differs (after a move with a delay)."""
        target_tilt = cover_data.get("target_tilt_position")
        if target_tilt is None:
            return
        if not (cover_raw.get("supports_tilt", False) and self._supports_tilt(entity_id)):
            return
        actual_tilt = 100 - target_tilt if cover_raw.get("inverted_tilt", False) else target_tilt
        last_tilt = self._last_tilt_positions.get(entity_id)
        # Always re-send after a position move: most venetian blind
        # actuators reset the slat angle while travelling, so an
        # unchanged target tilt would otherwise be lost.
        if (
            position_changed
            or last_tilt is None
            or abs(actual_tilt - last_tilt) > MANUAL_OVERRIDE_TOLERANCE
        ):
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

    @callback
    def async_sync_entities(self) -> None:
        """Sync HA entities with the configured covers/facades.

        Removes registry entries of deleted covers/facades and notifies the
        platforms (coordinator listeners) so they add entities for new ones.
        """
        entry = getattr(self, "config_entry", None)
        if entry is not None:
            from .entities import async_cleanup_orphan_entities

            async_cleanup_orphan_entities(self.hass, entry, self.storage)
        self.async_update_listeners()

    def set_cover_manual(self, entity_id: str) -> None:
        """Set a cover's status to MANUAL (public API for platforms)."""
        prev = self._cover_states.get(entity_id, CoverStatus.AUTO)
        if prev in (CoverStatus.LOCKED, CoverStatus.VENTING) or (
            self._wind_protected and prev == CoverStatus.WIND_PROTECTED
        ):
            # Protections keep acting on a disabled cover: the status stays
            # (no re-broadcast of the wind position to every cover, no lost
            # window lock). Overwriting LOCKED/VENTING would also make the
            # next sync lock/vent the cover again. After the protection ends
            # the sync sets MANUAL from auto_enabled=False.
            _LOGGER.debug("[%s] Automation disabled while %s: status kept", entity_id, prev.value)
            return
        if prev != CoverStatus.MANUAL:
            _LOGGER.debug("[%s] Automation disabled: %s -> manual", entity_id, prev.value)
            self._log(LOG_EVENT_STATUS, entity_id, f"{prev.value} -> manual",
                      {"key": "status_change", "from": prev.value, "to": "manual"})
        self._cover_states[entity_id] = CoverStatus.MANUAL
        self.storage.update_cover_status(entity_id, CoverStatus.MANUAL.value, None)

    def reconcile_after_import(self) -> None:
        """Align the cover statuses with auto_enabled after an import.

        An import can switch a cover's automation on or off without going
        through the switch entity: a re-enabled cover would stay MANUAL (and
        never be driven again), a disabled one would stay AUTO until the next
        sync. Protective statuses are kept by resume_cover/set_cover_manual.
        """
        for entity_id, cover_raw in list(self.storage._data.get("covers", {}).items()):
            if not isinstance(cover_raw, dict):
                continue
            if cover_raw.get("auto_enabled", True):
                if self._cover_states.get(entity_id, CoverStatus.AUTO) == CoverStatus.MANUAL:
                    self.resume_cover(entity_id)
            else:
                self.set_cover_manual(entity_id)

    async def async_shutdown(self) -> None:
        """Shut down coordinator."""
        if self._unsub_update_listener:
            self._unsub_update_listener()
            self._unsub_update_listener = None

        # Pending staggered wind commands must not run after unload
        self._cancel_wind_tasks()
        self._persist_runtime_state()

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
            if self.log_storage:
                await self.log_storage.async_save()
        except Exception:
            _LOGGER.warning("Failed to flush pending save during shutdown")

        # Base class: cancel the scheduled refresh and shut the debouncer
        # down, so no refresh (and no cover command) can run after unload.
        await super().async_shutdown()
