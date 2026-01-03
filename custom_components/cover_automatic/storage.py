"""Storage manager for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .models import CoverConfig, Facade, Rule, Scenario

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class CoverAutomaticStorage:
    """Manage persistent storage for CoverAutomatic."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self._data: dict[str, Any] = {}

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
