"""Storage manager for CoverAutomatic."""
from __future__ import annotations

import asyncio
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

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    @property
    def facades(self) -> dict[str, Facade]:
        """Get all facades."""
        return {
            k: Facade.from_dict(v) for k, v in self._data.get("facades", {}).items()
        }

    @property
    def covers(self) -> dict[str, CoverConfig]:
        """Get all cover configurations."""
        return {
            k: CoverConfig.from_dict(v) for k, v in self._data.get("covers", {}).items()
        }

    @property
    def rules(self) -> dict[str, Rule]:
        """Get all rules."""
        return {
            k: Rule.from_dict(v) for k, v in self._data.get("rules", {}).items()
        }

    @property
    def scenarios(self) -> dict[str, Scenario]:
        """Get all scenarios."""
        return {
            k: Scenario.from_dict(v) for k, v in self._data.get("scenarios", {}).items()
        }

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

    async def async_add_facade(self, facade: Facade) -> None:
        """Add or update a facade."""
        if "facades" not in self._data:
            self._data["facades"] = {}
        self._data["facades"][facade.id] = facade.to_dict()
        await self.async_save()

    async def async_remove_facade(self, facade_id: str) -> None:
        """Remove a facade."""
        if facade_id in self._data.get("facades", {}):
            del self._data["facades"][facade_id]
            await self.async_save()

    async def async_add_cover(self, cover: CoverConfig) -> None:
        """Add or update a cover configuration."""
        if "covers" not in self._data:
            self._data["covers"] = {}
        self._data["covers"][cover.entity_id] = cover.to_dict()
        await self.async_save()

    async def async_remove_cover(self, entity_id: str) -> None:
        """Remove a cover configuration."""
        if entity_id in self._data.get("covers", {}):
            del self._data["covers"][entity_id]
            await self.async_save()

    async def async_add_rule(self, rule: Rule) -> None:
        """Add or update a rule."""
        if "rules" not in self._data:
            self._data["rules"] = {}
        self._data["rules"][rule.id] = rule.to_dict()
        await self.async_save()

    async def async_remove_rule(self, rule_id: str) -> None:
        """Remove a rule."""
        if rule_id in self._data.get("rules", {}):
            del self._data["rules"][rule_id]
            await self.async_save()

    async def async_add_scenario(self, scenario: Scenario) -> None:
        """Add or update a scenario."""
        if "scenarios" not in self._data:
            self._data["scenarios"] = {}
        self._data["scenarios"][scenario.id] = scenario.to_dict()
        await self.async_save()

    async def async_remove_scenario(self, scenario_id: str) -> None:
        """Remove a scenario."""
        if scenario_id in self._data.get("scenarios", {}):
            del self._data["scenarios"][scenario_id]
            await self.async_save()

    def get_raw_data(self) -> dict[str, Any]:
        """Get raw data for export."""
        return self._data.copy()

    async def async_import_data(self, data: dict[str, Any]) -> None:
        """Import data from dict."""
        self._data = data
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
            self._schedule_save()

    def _schedule_save(self) -> None:
        """Schedule a debounced save operation.

        Multiple rapid updates will be batched into a single save
        after SAVE_DEBOUNCE_DELAY seconds of inactivity.
        """
        if self._save_task is not None:
            self._save_task.cancel()

        self._save_task = self.hass.async_create_task(self._debounced_save())

    async def _debounced_save(self) -> None:
        """Perform debounced save after delay."""
        try:
            await asyncio.sleep(SAVE_DEBOUNCE_DELAY)
            async with self._save_lock:
                await self._store.async_save(self._data)
                _LOGGER.debug("Runtime changes persisted to storage")
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Failed to save runtime changes: %s", err)
