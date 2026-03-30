"""Storage manager for CoverAutomatic."""
from __future__ import annotations

import asyncio
import copy
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
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
            }
        else:
            self._data = data
        self._invalidate_cache()

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
    def house_rotation(self) -> float:
        """Get global house rotation offset in degrees."""
        return self._data.get("house_rotation", 0.0)

    @house_rotation.setter
    def house_rotation(self, value: float) -> None:
        """Set global house rotation offset in degrees."""
        self._data["house_rotation"] = float(value)

    async def async_add_facade(self, facade: Facade) -> None:
        """Add or update a facade."""
        if "facades" not in self._data:
            self._data["facades"] = {}
        self._data["facades"][facade.id] = facade.to_dict()
        self._cache_facades = None
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

    async def async_add_cover(self, cover: CoverConfig) -> None:
        """Add or update a cover configuration."""
        if "covers" not in self._data:
            self._data["covers"] = {}
        self._data["covers"][cover.entity_id] = cover.to_dict()
        self._cache_covers = None
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

    async def async_add_rule(self, rule: Rule) -> None:
        """Add or update a rule."""
        if "rules" not in self._data:
            self._data["rules"] = {}
        self._data["rules"][rule.id] = rule.to_dict()
        self._cache_rules = None
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

    async def async_add_scenario(self, scenario: Scenario) -> None:
        """Add or update a scenario."""
        if "scenarios" not in self._data:
            self._data["scenarios"] = {}
        self._data["scenarios"][scenario.id] = scenario.to_dict()
        self._cache_scenarios = None
        await self.async_save()

    async def async_remove_scenario(self, scenario_id: str) -> None:
        """Remove a scenario."""
        if scenario_id in self._data.get("scenarios", {}):
            del self._data["scenarios"][scenario_id]
            self._cache_scenarios = None
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
            "outdoor_temp_sensor",
            "indoor_temp_sensor",
            "weather_entity",
            "comfort_temp_min",
            "comfort_temp_max",
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
