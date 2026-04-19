"""Storage manager for CoverAutomatic."""
from __future__ import annotations

import asyncio
import copy
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from homeassistant.util import dt as dt_util

from .const import LOG_RETENTION_DAYS, LOG_STORAGE_KEY, STORAGE_KEY, STORAGE_VERSION
from .models import CoverConfig, Facade, Rule, Scenario

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Debounce delay for runtime saves (seconds)
SAVE_DEBOUNCE_DELAY = 2.0

# Required top-level keys for import validation
_REQUIRED_DICT_KEYS = ("facades", "covers", "rules", "scenarios")


class CoverAutomaticStorage:
    """Manage persistent storage for CoverAutomatic."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self._data: dict[str, Any] = {}
        self._save_task: asyncio.Task | None = None
        self._save_lock = asyncio.Lock()
        # Deserialization cache
        self._cache_facades: dict[str, Facade] | None = None
        self._cache_covers: dict[str, CoverConfig] | None = None
        self._cache_rules: dict[str, Rule] | None = None
        self._cache_scenarios: dict[str, Scenario] | None = None

    def _invalidate_cache(self) -> None:
        """Invalidate all deserialization caches."""
        self._cache_facades = None
        self._cache_covers = None
        self._cache_rules = None
        self._cache_scenarios = None

    async def async_load(self) -> None:
        """Load data from storage."""
        data = await self._store.async_load()
        if data is None:
            self._data = {
                "facades": {},
                "covers": {},
                "rules": {},
                "scenarios": {},
                "active_scenario": "everyday",
                "outdoor_temp_sensor": None,
                "indoor_temp_sensor": None,
                "weather_entity": None,
                "comfort_temp_min": 21.0,
                "comfort_temp_max": 25.0,
                "workday_sensor": None,
                "wind_sensor": None,
                "wind_speed_threshold": 0.0,
                "wind_speed_hysteresis": 0.0,
                "solar_sensor": None,
                "solar_threshold": 0.0,
            }
        else:
            self._data = data
            self._migrate()
        self._invalidate_cache()

    def _migrate(self) -> None:
        """Run data migrations for older storage versions."""
        # v1.6.0: Remove per-cover pause_duration if it matches the old default (120)
        for cover_data in self._data.get("covers", {}).values():
            if cover_data.get("pause_duration") == 120:
                cover_data["pause_duration"] = None

    async def async_save(self) -> None:
        """Save data to storage.

        Uses the same lock as debounced saves to prevent concurrent writes.
        """
        # Cancel any pending debounced save since we're saving now
        if self._save_task is not None:
            self._save_task.cancel()
            self._save_task = None

        async with self._save_lock:
            await self._store.async_save(self._data)

    @property
    def facades(self) -> dict[str, Facade]:
        """Get all facades (cached)."""
        if self._cache_facades is None:
            self._cache_facades = {
                k: Facade.from_dict(v) for k, v in self._data.get("facades", {}).items()
            }
        return self._cache_facades

    @property
    def covers(self) -> dict[str, CoverConfig]:
        """Get all cover configurations (cached)."""
        if self._cache_covers is None:
            self._cache_covers = {
                k: CoverConfig.from_dict(v) for k, v in self._data.get("covers", {}).items()
            }
        return self._cache_covers

    @property
    def rules(self) -> dict[str, Rule]:
        """Get all rules (cached)."""
        if self._cache_rules is None:
            self._cache_rules = {
                k: Rule.from_dict(v) for k, v in self._data.get("rules", {}).items()
            }
        return self._cache_rules

    @property
    def scenarios(self) -> dict[str, Scenario]:
        """Get all scenarios (cached)."""
        if self._cache_scenarios is None:
            self._cache_scenarios = {
                k: Scenario.from_dict(v) for k, v in self._data.get("scenarios", {}).items()
            }
        return self._cache_scenarios

    @property
    def active_scenario(self) -> str:
        """Get active scenario ID."""
        return self._data.get("active_scenario", "everyday")

    @active_scenario.setter
    def active_scenario(self, value: str) -> None:
        """Set active scenario ID."""
        self._data["active_scenario"] = value

    @property
    def outdoor_temp_sensor(self) -> str | None:
        """Get outdoor temperature sensor entity ID."""
        return self._data.get("outdoor_temp_sensor")

    @outdoor_temp_sensor.setter
    def outdoor_temp_sensor(self, value: str | None) -> None:
        """Set outdoor temperature sensor entity ID."""
        self._data["outdoor_temp_sensor"] = value

    @property
    def indoor_temp_sensor(self) -> str | None:
        """Get indoor temperature sensor entity ID."""
        return self._data.get("indoor_temp_sensor")

    @indoor_temp_sensor.setter
    def indoor_temp_sensor(self, value: str | None) -> None:
        """Set indoor temperature sensor entity ID."""
        self._data["indoor_temp_sensor"] = value

    @property
    def weather_entity(self) -> str | None:
        """Get weather entity ID."""
        return self._data.get("weather_entity")

    @weather_entity.setter
    def weather_entity(self, value: str | None) -> None:
        """Set weather entity ID."""
        self._data["weather_entity"] = value

    @property
    def comfort_temp_min(self) -> float:
        """Get minimum comfort temperature."""
        return self._data.get("comfort_temp_min", 21.0)

    @comfort_temp_min.setter
    def comfort_temp_min(self, value: float) -> None:
        """Set minimum comfort temperature."""
        self._data["comfort_temp_min"] = value

    @property
    def comfort_temp_max(self) -> float:
        """Get maximum comfort temperature."""
        return self._data.get("comfort_temp_max", 25.0)

    @comfort_temp_max.setter
    def comfort_temp_max(self, value: float) -> None:
        """Set maximum comfort temperature."""
        self._data["comfort_temp_max"] = value

    @property
    def comfort_hysteresis(self) -> float:
        """Get comfort temperature hysteresis."""
        return self._data.get("comfort_hysteresis", 1.0)

    @comfort_hysteresis.setter
    def comfort_hysteresis(self, value: float) -> None:
        """Set comfort temperature hysteresis."""
        self._data["comfort_hysteresis"] = float(value)

    @property
    def enabled(self) -> bool:
        """Get global automation enabled state."""
        return self._data.get("enabled", True)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set global automation enabled state."""
        self._data["enabled"] = bool(value)

    @property
    def pause_duration(self) -> int:
        """Get global default pause duration in seconds."""
        return self._data.get("pause_duration", 10)

    @pause_duration.setter
    def pause_duration(self, value: int) -> None:
        """Set global default pause duration in seconds."""
        self._data["pause_duration"] = int(value)

    @property
    def lock_position(self) -> int:
        """Get global default lock position."""
        return self._data.get("lock_position", 100)

    @lock_position.setter
    def lock_position(self, value: int) -> None:
        """Set global default lock position."""
        self._data["lock_position"] = int(value)

    @property
    def vent_position(self) -> int:
        """Get global default vent position."""
        return self._data.get("vent_position", 30)

    @vent_position.setter
    def vent_position(self, value: int) -> None:
        """Set global default vent position."""
        self._data["vent_position"] = int(value)

    @property
    def lock_tilt_position(self) -> int | None:
        """Get global default lock tilt position."""
        return self._data.get("lock_tilt_position")

    @lock_tilt_position.setter
    def lock_tilt_position(self, value: int | None) -> None:
        """Set global default lock tilt position."""
        self._data["lock_tilt_position"] = value

    @property
    def vent_tilt_position(self) -> int | None:
        """Get global default vent tilt position."""
        return self._data.get("vent_tilt_position")

    @vent_tilt_position.setter
    def vent_tilt_position(self, value: int | None) -> None:
        """Set global default vent tilt position."""
        self._data["vent_tilt_position"] = value

    @property
    def min_position_change(self) -> int:
        """Get global default minimum position change."""
        return self._data.get("min_position_change", 5)

    @min_position_change.setter
    def min_position_change(self, value: int) -> None:
        """Set global default minimum position change."""
        self._data["min_position_change"] = int(value)

    @property
    def min_time_between_changes(self) -> int:
        """Get global default minimum time between changes."""
        return self._data.get("min_time_between_changes", 300)

    @min_time_between_changes.setter
    def min_time_between_changes(self, value: int) -> None:
        """Set global default minimum time between changes."""
        self._data["min_time_between_changes"] = int(value)

    @property
    def workday_sensor(self) -> str | None:
        """Get workday binary sensor entity ID."""
        return self._data.get("workday_sensor")

    @workday_sensor.setter
    def workday_sensor(self, value: str | None) -> None:
        """Set workday binary sensor entity ID."""
        self._data["workday_sensor"] = value

    @property
    def wind_sensor(self) -> str | None:
        """Get wind speed sensor entity ID."""
        return self._data.get("wind_sensor")

    @wind_sensor.setter
    def wind_sensor(self, value: str | None) -> None:
        """Set wind speed sensor entity ID."""
        self._data["wind_sensor"] = value

    @property
    def wind_speed_threshold(self) -> float:
        """Get wind speed activation threshold."""
        return self._data.get("wind_speed_threshold", 0.0)

    @wind_speed_threshold.setter
    def wind_speed_threshold(self, value: float) -> None:
        """Set wind speed activation threshold."""
        self._data["wind_speed_threshold"] = float(value)

    @property
    def wind_speed_hysteresis(self) -> float:
        """Get wind speed deactivation hysteresis."""
        return self._data.get("wind_speed_hysteresis", 0.0)

    @wind_speed_hysteresis.setter
    def wind_speed_hysteresis(self, value: float) -> None:
        """Set wind speed deactivation hysteresis."""
        self._data["wind_speed_hysteresis"] = float(value)

    @property
    def solar_sensor(self) -> str | None:
        """Get solar intensity sensor entity id."""
        return self._data.get("solar_sensor")

    @solar_sensor.setter
    def solar_sensor(self, value: str | None) -> None:
        """Set solar intensity sensor entity id."""
        self._data["solar_sensor"] = value

    @property
    def solar_threshold(self) -> float:
        """Get solar intensity threshold for preemptive shading."""
        return self._data.get("solar_threshold", 0.0)

    @solar_threshold.setter
    def solar_threshold(self, value: float) -> None:
        """Set solar intensity threshold for preemptive shading."""
        self._data["solar_threshold"] = float(value)

    @property
    def house_rotation(self) -> float:
        """Get global house rotation offset in degrees."""
        return self._data.get("house_rotation", 0.0)

    @house_rotation.setter
    def house_rotation(self, value: float) -> None:
        """Set global house rotation offset in degrees."""
        self._data["house_rotation"] = float(value)

    @property
    def command_stagger(self) -> float:
        """Get command stagger delay in seconds between cover commands."""
        return self._data.get("command_stagger", 0.0)

    @command_stagger.setter
    def command_stagger(self, value: float) -> None:
        """Set command stagger delay in seconds."""
        self._data["command_stagger"] = max(0.0, float(value))

    @property
    def logbook_enabled(self) -> bool:
        """Get whether to write HA logbook entries for cover actions."""
        return self._data.get("logbook_enabled", True)

    @logbook_enabled.setter
    def logbook_enabled(self, value: bool) -> None:
        """Set whether to write HA logbook entries for cover actions."""
        self._data["logbook_enabled"] = bool(value)

    async def async_add_facade(self, facade: Facade, *, save: bool = True) -> None:
        """Add or update a facade."""
        if "facades" not in self._data:
            self._data["facades"] = {}
        self._data["facades"][facade.id] = facade.to_dict()
        self._cache_facades = None
        if save:
            await self.async_save()

    async def async_remove_facade(self, facade_id: str) -> None:
        """Remove a facade and clean up references."""
        if facade_id in self._data.get("facades", {}):
            del self._data["facades"][facade_id]
            self._cache_facades = None
            # Clean up cover references
            for cover_data in self._data.get("covers", {}).values():
                if cover_data.get("facade_id") == facade_id:
                    cover_data["facade_id"] = None
            self._cache_covers = None
            # Clean up rule references
            for rule_data in self._data.get("rules", {}).values():
                fids = rule_data.get("facade_ids", [])
                if facade_id in fids:
                    fids.remove(facade_id)
            self._cache_rules = None
            await self.async_save()

    async def async_add_cover(self, cover: CoverConfig, *, save: bool = True) -> None:
        """Add or update a cover configuration."""
        if "covers" not in self._data:
            self._data["covers"] = {}
        self._data["covers"][cover.entity_id] = cover.to_dict()
        self._cache_covers = None
        if save:
            await self.async_save()

    async def async_remove_cover(self, entity_id: str) -> None:
        """Remove a cover configuration and clean up references."""
        if entity_id in self._data.get("covers", {}):
            del self._data["covers"][entity_id]
            self._cache_covers = None
            # Clean up facade references
            for facade_data in self._data.get("facades", {}).values():
                cids = facade_data.get("cover_ids", [])
                if entity_id in cids:
                    cids.remove(entity_id)
            self._cache_facades = None
            # Clean up rule references
            for rule_data in self._data.get("rules", {}).values():
                cids = rule_data.get("cover_ids", [])
                if entity_id in cids:
                    cids.remove(entity_id)
            self._cache_rules = None
            await self.async_save()

    async def async_add_rule(self, rule: Rule, *, save: bool = True) -> None:
        """Add or update a rule."""
        if "rules" not in self._data:
            self._data["rules"] = {}
        self._data["rules"][rule.id] = rule.to_dict()
        self._cache_rules = None
        if save:
            await self.async_save()

    async def async_remove_rule(self, rule_id: str) -> None:
        """Remove a rule and clean up scenario references."""
        if rule_id in self._data.get("rules", {}):
            del self._data["rules"][rule_id]
            self._cache_rules = None
            # Clean up scenario rules_disabled references
            for scenario_data in self._data.get("scenarios", {}).values():
                disabled = scenario_data.get("rules_disabled", [])
                if rule_id in disabled:
                    disabled.remove(rule_id)
            self._cache_scenarios = None
            await self.async_save()

    async def async_add_scenario(self, scenario: Scenario, *, save: bool = True) -> None:
        """Add or update a scenario."""
        if "scenarios" not in self._data:
            self._data["scenarios"] = {}
        self._data["scenarios"][scenario.id] = scenario.to_dict()
        self._cache_scenarios = None
        if save:
            await self.async_save()

    async def async_remove_scenario(self, scenario_id: str) -> None:
        """Remove a scenario."""
        if scenario_id in self._data.get("scenarios", {}):
            del self._data["scenarios"][scenario_id]
            self._cache_scenarios = None
            if self._data.get("active_scenario") == scenario_id:
                remaining = self._data.get("scenarios", {})
                self._data["active_scenario"] = next(iter(remaining), "everyday")
            await self.async_save()

    def get_raw_data(self) -> dict[str, Any]:
        """Get raw data for export (deep copy to prevent race conditions)."""
        return copy.deepcopy(self._data)

    async def async_import_data(self, data: dict[str, Any]) -> None:
        """Import data from dict with validation."""
        if not isinstance(data, dict):
            raise ValueError("Import data must be a dictionary")

        for key in _REQUIRED_DICT_KEYS:
            if key in data and not isinstance(data[key], dict):
                raise ValueError(f"Import data key '{key}' must be a dictionary")

        # Deep copy to prevent external mutation
        data = copy.deepcopy(data)

        # Ensure required keys exist
        for key in _REQUIRED_DICT_KEYS:
            data.setdefault(key, {})
        data.setdefault(
            "active_scenario",
            self._data.get("active_scenario", "everyday"),
        )

        # Validate sub-elements can be deserialized (skip corrupt entries)
        _validators: dict[str, type] = {
            "facades": Facade,
            "covers": CoverConfig,
            "rules": Rule,
            "scenarios": Scenario,
        }
        for section, model_cls in _validators.items():
            valid: dict[str, Any] = {}
            for k, v in data.get(section, {}).items():
                try:
                    model_cls.from_dict(v)
                    valid[k] = v
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning(
                        "Skipping invalid %s entry '%s' during import: %s",
                        section, k, err,
                    )
            data[section] = valid

        # Validate active_scenario exists in imported scenarios
        if data.get("active_scenario") not in data.get("scenarios", {}):
            first_scenario = next(iter(data.get("scenarios", {})), "everyday")
            data["active_scenario"] = first_scenario

        # Preserve global settings not present in import data
        _global_keys = (
            "enabled",
            "outdoor_temp_sensor",
            "indoor_temp_sensor",
            "weather_entity",
            "comfort_temp_min",
            "comfort_temp_max",
            "comfort_hysteresis",
            "pause_duration",
            "lock_position",
            "vent_position",
            "lock_tilt_position",
            "vent_tilt_position",
            "min_position_change",
            "min_time_between_changes",
            "house_rotation",
            "workday_sensor",
            "wind_sensor",
            "wind_speed_threshold",
            "wind_speed_hysteresis",
            "solar_sensor",
            "solar_threshold",
            "command_stagger",
            "logbook_enabled",
        )
        for gkey in _global_keys:
            if gkey not in data:
                data[gkey] = self._data.get(gkey)

        self._data = data
        self._invalidate_cache()
        await self.async_save()

    def update_cover_status(
        self, entity_id: str, status: str, pause_until: float | None = None
    ) -> None:
        """Update cover status directly in storage data.

        Triggers a debounced save to persist changes.
        """
        if entity_id in self._data.get("covers", {}):
            self._data["covers"][entity_id]["status"] = status
            self._data["covers"][entity_id]["pause_until"] = pause_until
            self._cache_covers = None
            self._schedule_save()

    def get_cover_raw(self, entity_id: str) -> dict[str, Any] | None:
        """Get raw cover data dict (not a copy)."""
        return self._data.get("covers", {}).get(entity_id)

    def update_cover_last_change(self, entity_id: str, timestamp: float) -> None:
        """Update cover's last position change timestamp.

        Triggers a debounced save to persist changes.
        """
        if entity_id in self._data.get("covers", {}):
            self._data["covers"][entity_id]["last_position_change"] = timestamp
            self._cache_covers = None
            self._schedule_save()

    def flush_pending_save(self) -> None:
        """Cancel pending debounced save task (public API for coordinator shutdown)."""
        if self._save_task is not None:
            self._save_task.cancel()
            self._save_task = None

    def _schedule_save(self) -> None:
        """Schedule a debounced save operation.

        Multiple rapid updates will be batched into a single save
        after SAVE_DEBOUNCE_DELAY seconds of inactivity.
        """
        if self._save_task is not None:
            self._save_task.cancel()

        self._save_task = self.hass.async_create_task(
            self._debounced_save(),
            name="cover_automatic_debounced_save",
        )

    async def _debounced_save(self) -> None:
        """Perform debounced save after delay."""
        current = asyncio.current_task()
        try:
            await asyncio.sleep(SAVE_DEBOUNCE_DELAY)
            async with self._save_lock:
                await self._store.async_save(self._data)
                _LOGGER.debug("Runtime changes persisted to storage")
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Failed to save runtime changes: %s", err)
        finally:
            if self._save_task is current:
                self._save_task = None


class ActivityLogStorage:
    """Persistent activity log with automatic 3-day retention."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, LOG_STORAGE_KEY)
        self._entries: list[dict[str, Any]] = []
        self._save_task: asyncio.Task | None = None
        self._save_lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Load log entries from storage."""
        data = await self._store.async_load()
        if data and isinstance(data.get("entries"), list):
            self._entries = data["entries"]
        else:
            self._entries = []
        self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than LOG_RETENTION_DAYS."""
        cutoff = dt_util.now().timestamp() - (LOG_RETENTION_DAYS * 86400)
        self._entries = [e for e in self._entries if e.get("ts", 0) > cutoff]

    def add_entry(
        self,
        event_type: str,
        entity_id: str | None = None,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add a log entry and schedule debounced save."""
        self._cleanup_old_entries()
        entry: dict[str, Any] = {
            "ts": dt_util.now().timestamp(),
            "type": event_type,
            "entity_id": entity_id,
            "message": message,
        }
        if data:
            entry["data"] = data
        self._entries.append(entry)
        self._schedule_save()

    async def async_clear(self) -> None:
        """Clear all log entries and save immediately."""
        self._entries = []
        if self._save_task is not None:
            self._save_task.cancel()
            self._save_task = None
        async with self._save_lock:
            await self._store.async_save({"entries": self._entries})

    def get_entries(
        self,
        event_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Get log entries, newest first, with optional filters."""
        self._cleanup_old_entries()
        entries = self._entries
        if event_type:
            entries = [e for e in entries if e.get("type") == event_type]
        if entity_id:
            entries = [e for e in entries if e.get("entity_id") == entity_id]
        return list(reversed(entries))[:limit]

    def flush_pending_save(self) -> None:
        """Cancel pending debounced save task."""
        if self._save_task is not None:
            self._save_task.cancel()
            self._save_task = None

    def _schedule_save(self) -> None:
        """Schedule a debounced save."""
        if self._save_task is not None:
            self._save_task.cancel()
        self._save_task = self.hass.async_create_task(
            self._debounced_save(),
            name="cover_automatic_log_save",
        )

    async def _debounced_save(self) -> None:
        """Perform debounced save after delay."""
        current = asyncio.current_task()
        try:
            await asyncio.sleep(SAVE_DEBOUNCE_DELAY)
            async with self._save_lock:
                await self._store.async_save({"entries": self._entries})
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Failed to save activity log: %s", err)
        finally:
            if self._save_task is current:
                self._save_task = None
