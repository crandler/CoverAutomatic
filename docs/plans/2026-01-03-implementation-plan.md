# CoverAutomatic Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Home Assistant custom integration for intelligent cover automation based on sun position, time, and temperature.

**Architecture:** Coordinator-based integration with config flow UI. Central engine evaluates rules and controls cover positions. Entities wrap existing covers with automation state tracking.

**Tech Stack:** Home Assistant Core APIs, Python 3.12+, voluptuous for validation, astral for sun calculations (included in HA).

---

## Task 1: Manifest and Constants

**Files:**
- Create: `custom_components/cover_automatic/__init__.py`
- Create: `custom_components/cover_automatic/manifest.json`
- Create: `custom_components/cover_automatic/const.py`

**Step 1: Create directory structure**

```bash
mkdir -p custom_components/cover_automatic/translations
```

**Step 2: Create manifest.json**

```json
{
  "domain": "cover_automatic",
  "name": "CoverAutomatic",
  "codeowners": ["@crandler"],
  "config_flow": true,
  "dependencies": ["sun"],
  "documentation": "https://github.com/crandler/cover_automatic",
  "integration_type": "service",
  "iot_class": "calculated",
  "issue_tracker": "https://github.com/crandler/cover_automatic/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

**Step 3: Create const.py**

```python
"""Constants for CoverAutomatic integration."""
from typing import Final

DOMAIN: Final = "cover_automatic"

# Defaults
DEFAULT_PAUSE_DURATION: Final = 120  # minutes
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Facade azimuth ranges
FACADE_PRESETS: Final = {
    "north": {"start": 315, "end": 45},
    "east": {"start": 45, "end": 135},
    "south": {"start": 135, "end": 225},
    "west": {"start": 225, "end": 315},
}

# Condition types
CONDITION_SUN_ON_FACADE: Final = "sun_on_facade"
CONDITION_SUN_ELEVATION_ABOVE: Final = "sun_elevation_above"
CONDITION_SUN_ELEVATION_BELOW: Final = "sun_elevation_below"
CONDITION_TEMP_ABOVE: Final = "temperature_above"
CONDITION_TEMP_BELOW: Final = "temperature_below"
CONDITION_TIME_BETWEEN: Final = "time_between"
CONDITION_TIME_AFTER_SUNRISE: Final = "time_after_sunrise"
CONDITION_TIME_AFTER_SUNSET: Final = "time_after_sunset"
CONDITION_STATE_IS: Final = "state_is"

# Scenarios
DEFAULT_SCENARIOS: Final = ["everyday", "summer", "winter", "vacation", "cinema", "manual"]

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_VERSION: Final = 1

# Platforms
PLATFORMS: Final = ["cover", "switch", "sensor", "select", "number"]
```

**Step 4: Create empty __init__.py placeholder**

```python
"""CoverAutomatic integration for Home Assistant."""
```

**Step 5: Commit**

```bash
git add custom_components/
git commit -m "feat: add manifest and constants"
```

---

## Task 2: Data Models

**Files:**
- Create: `custom_components/cover_automatic/models.py`

**Step 1: Create data models**

```python
"""Data models for CoverAutomatic."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CoverStatus(StrEnum):
    """Cover automation status."""

    AUTO = "auto"
    PAUSED = "paused"
    MANUAL = "manual"


class ConditionType(StrEnum):
    """Rule condition types."""

    SUN_ON_FACADE = "sun_on_facade"
    SUN_ELEVATION_ABOVE = "sun_elevation_above"
    SUN_ELEVATION_BELOW = "sun_elevation_below"
    TEMPERATURE_ABOVE = "temperature_above"
    TEMPERATURE_BELOW = "temperature_below"
    TIME_BETWEEN = "time_between"
    TIME_AFTER_SUNRISE = "time_after_sunrise"
    TIME_AFTER_SUNSET = "time_after_sunset"
    STATE_IS = "state_is"


@dataclass
class Facade:
    """Represents a building facade with sun exposure settings."""

    id: str
    name: str
    azimuth_start: float
    azimuth_end: float
    min_elevation: float = 0.0
    cover_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "azimuth_start": self.azimuth_start,
            "azimuth_end": self.azimuth_end,
            "min_elevation": self.min_elevation,
            "cover_ids": self.cover_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Facade:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            azimuth_start=data["azimuth_start"],
            azimuth_end=data["azimuth_end"],
            min_elevation=data.get("min_elevation", 0.0),
            cover_ids=data.get("cover_ids", []),
        )


@dataclass
class Condition:
    """Rule condition."""

    type: ConditionType
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"type": self.type.value, "params": self.params}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Condition:
        """Create from dictionary."""
        return cls(
            type=ConditionType(data["type"]),
            params=data.get("params", {}),
        )


@dataclass
class Rule:
    """Automation rule with conditions and action."""

    id: str
    name: str
    enabled: bool = True
    priority: int = 10
    scenarios: list[str] = field(default_factory=list)
    facade_ids: list[str] = field(default_factory=list)
    cover_ids: list[str] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    target_position: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "scenarios": self.scenarios,
            "facade_ids": self.facade_ids,
            "cover_ids": self.cover_ids,
            "conditions": [c.to_dict() for c in self.conditions],
            "target_position": self.target_position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 10),
            scenarios=data.get("scenarios", []),
            facade_ids=data.get("facade_ids", []),
            cover_ids=data.get("cover_ids", []),
            conditions=[Condition.from_dict(c) for c in data.get("conditions", [])],
            target_position=data.get("target_position", 0),
        )


@dataclass
class Scenario:
    """Automation scenario/mode."""

    id: str
    name: str
    icon: str = "mdi:home"
    rules_enabled: list[str] = field(default_factory=list)
    rules_disabled: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "rules_enabled": self.rules_enabled,
            "rules_disabled": self.rules_disabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data.get("icon", "mdi:home"),
            rules_enabled=data.get("rules_enabled", []),
            rules_disabled=data.get("rules_disabled", []),
        )


@dataclass
class CoverConfig:
    """Configuration for a managed cover."""

    entity_id: str
    name: str
    facade_id: str | None = None
    auto_enabled: bool = True
    pause_duration: int = 120
    status: CoverStatus = CoverStatus.AUTO
    pause_until: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "facade_id": self.facade_id,
            "auto_enabled": self.auto_enabled,
            "pause_duration": self.pause_duration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoverConfig:
        """Create from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            name=data["name"],
            facade_id=data.get("facade_id"),
            auto_enabled=data.get("auto_enabled", True),
            pause_duration=data.get("pause_duration", 120),
        )
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/models.py
git commit -m "feat: add data models for facades, rules, scenarios"
```

---

## Task 3: Storage Manager

**Files:**
- Create: `custom_components/cover_automatic/storage.py`

**Step 1: Create storage manager**

```python
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
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/storage.py
git commit -m "feat: add storage manager for persistent configuration"
```

---

## Task 4: Sun Calculation Engine

**Files:**
- Create: `custom_components/cover_automatic/sun.py`

**Step 1: Create sun calculation module**

```python
"""Sun position calculations for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sun import STATE_ABOVE_HORIZON
from homeassistant.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Facade

_LOGGER = logging.getLogger(__name__)

SUN_ENTITY_ID = "sun.sun"


def get_sun_position(hass: HomeAssistant) -> tuple[float, float] | None:
    """Get current sun azimuth and elevation.

    Returns:
        Tuple of (azimuth, elevation) in degrees, or None if unavailable.
    """
    sun_state = hass.states.get(SUN_ENTITY_ID)
    if sun_state is None:
        _LOGGER.warning("Sun entity not available")
        return None

    try:
        azimuth = float(sun_state.attributes.get("azimuth", 0))
        elevation = float(sun_state.attributes.get("elevation", 0))
        return (azimuth, elevation)
    except (ValueError, TypeError) as err:
        _LOGGER.error("Error reading sun position: %s", err)
        return None


def is_sun_above_horizon(hass: HomeAssistant) -> bool:
    """Check if sun is above horizon."""
    sun_state = hass.states.get(SUN_ENTITY_ID)
    if sun_state is None:
        return False
    return sun_state.state == STATE_ABOVE_HORIZON


def is_sun_on_facade(hass: HomeAssistant, facade: Facade) -> bool:
    """Check if sun is shining on a facade.

    Args:
        hass: Home Assistant instance
        facade: Facade to check

    Returns:
        True if sun is currently shining on the facade.
    """
    position = get_sun_position(hass)
    if position is None:
        return False

    azimuth, elevation = position

    if elevation < facade.min_elevation:
        return False

    start = facade.azimuth_start
    end = facade.azimuth_end

    if start <= end:
        return start <= azimuth <= end
    else:
        return azimuth >= start or azimuth <= end


def get_sunrise_time(hass: HomeAssistant) -> float | None:
    """Get today's sunrise time as timestamp."""
    sunrise = get_astral_event_date(hass, SUN_EVENT_SUNRISE, dt_util.now())
    if sunrise is None:
        return None
    return sunrise.timestamp()


def get_sunset_time(hass: HomeAssistant) -> float | None:
    """Get today's sunset time as timestamp."""
    sunset = get_astral_event_date(hass, SUN_EVENT_SUNSET, dt_util.now())
    if sunset is None:
        return None
    return sunset.timestamp()
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/sun.py
git commit -m "feat: add sun position calculation module"
```

---

## Task 5: Rule Engine

**Files:**
- Create: `custom_components/cover_automatic/engine.py`

**Step 1: Create rule evaluation engine**

```python
"""Rule evaluation engine for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import datetime, time
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from .models import Condition, ConditionType, CoverConfig, Rule
from .sun import get_sun_position, get_sunrise_time, get_sunset_time, is_sun_on_facade

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)


class RuleEngine:
    """Evaluate rules and determine cover positions."""

    def __init__(self, hass: HomeAssistant, storage: CoverAutomaticStorage) -> None:
        """Initialize rule engine."""
        self.hass = hass
        self.storage = storage

    def evaluate_cover(self, cover: CoverConfig) -> int | None:
        """Evaluate rules for a cover and return target position.

        Returns:
            Target position (0-100) or None if no rule matches.
        """
        active_scenario = self.storage.active_scenario
        matching_rules: list[tuple[int, int]] = []

        for rule in self.storage.rules.values():
            if not rule.enabled:
                continue

            if not self._rule_applies_to_cover(rule, cover):
                continue

            if not self._rule_active_in_scenario(rule, active_scenario):
                continue

            if self._evaluate_conditions(rule, cover):
                matching_rules.append((rule.priority, rule.target_position))

        if not matching_rules:
            return None

        matching_rules.sort(key=lambda x: x[0], reverse=True)
        return matching_rules[0][1]

    def _rule_applies_to_cover(self, rule: Rule, cover: CoverConfig) -> bool:
        """Check if rule applies to cover."""
        if rule.cover_ids and cover.entity_id in rule.cover_ids:
            return True

        if rule.facade_ids and cover.facade_id in rule.facade_ids:
            return True

        if not rule.cover_ids and not rule.facade_ids:
            return True

        return False

    def _rule_active_in_scenario(self, rule: Rule, scenario_id: str) -> bool:
        """Check if rule is active in current scenario."""
        scenario = self.storage.scenarios.get(scenario_id)

        if scenario is None:
            return not rule.scenarios or scenario_id in rule.scenarios

        if rule.id in scenario.rules_disabled:
            return False

        if scenario.rules_enabled and rule.id not in scenario.rules_enabled:
            if rule.scenarios and scenario_id not in rule.scenarios:
                return False

        if rule.scenarios and scenario_id not in rule.scenarios:
            return False

        return True

    def _evaluate_conditions(self, rule: Rule, cover: CoverConfig) -> bool:
        """Evaluate all conditions of a rule."""
        for condition in rule.conditions:
            if not self._evaluate_condition(condition, cover):
                return False
        return True

    def _evaluate_condition(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate a single condition."""
        try:
            match condition.type:
                case ConditionType.SUN_ON_FACADE:
                    return self._eval_sun_on_facade(condition, cover)
                case ConditionType.SUN_ELEVATION_ABOVE:
                    return self._eval_sun_elevation_above(condition)
                case ConditionType.SUN_ELEVATION_BELOW:
                    return self._eval_sun_elevation_below(condition)
                case ConditionType.TEMPERATURE_ABOVE:
                    return self._eval_temp_above(condition)
                case ConditionType.TEMPERATURE_BELOW:
                    return self._eval_temp_below(condition)
                case ConditionType.TIME_BETWEEN:
                    return self._eval_time_between(condition)
                case ConditionType.TIME_AFTER_SUNRISE:
                    return self._eval_time_after_sunrise(condition)
                case ConditionType.TIME_AFTER_SUNSET:
                    return self._eval_time_after_sunset(condition)
                case ConditionType.STATE_IS:
                    return self._eval_state_is(condition)
                case _:
                    _LOGGER.warning("Unknown condition type: %s", condition.type)
                    return False
        except Exception as err:
            _LOGGER.error("Error evaluating condition %s: %s", condition.type, err)
            return False

    def _eval_sun_on_facade(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate sun_on_facade condition."""
        facade_id = condition.params.get("facade") or cover.facade_id
        if not facade_id:
            return False

        facade = self.storage.facades.get(facade_id)
        if not facade:
            return False

        return is_sun_on_facade(self.hass, facade)

    def _eval_sun_elevation_above(self, condition: Condition) -> bool:
        """Evaluate sun_elevation_above condition."""
        threshold = condition.params.get("value", 0)
        position = get_sun_position(self.hass)
        if position is None:
            return False
        return position[1] > threshold

    def _eval_sun_elevation_below(self, condition: Condition) -> bool:
        """Evaluate sun_elevation_below condition."""
        threshold = condition.params.get("value", 0)
        position = get_sun_position(self.hass)
        if position is None:
            return False
        return position[1] < threshold

    def _eval_temp_above(self, condition: Condition) -> bool:
        """Evaluate temperature_above condition."""
        sensor_id = condition.params.get("sensor")
        threshold = condition.params.get("value", 0)

        if not sensor_id:
            return False

        state = self.hass.states.get(sensor_id)
        if state is None:
            return False

        try:
            temp = float(state.state)
            return temp > threshold
        except (ValueError, TypeError):
            return False

    def _eval_temp_below(self, condition: Condition) -> bool:
        """Evaluate temperature_below condition."""
        sensor_id = condition.params.get("sensor")
        threshold = condition.params.get("value", 0)

        if not sensor_id:
            return False

        state = self.hass.states.get(sensor_id)
        if state is None:
            return False

        try:
            temp = float(state.state)
            return temp < threshold
        except (ValueError, TypeError):
            return False

    def _eval_time_between(self, condition: Condition) -> bool:
        """Evaluate time_between condition."""
        start_str = condition.params.get("start", "00:00")
        end_str = condition.params.get("end", "23:59")

        try:
            start_parts = start_str.split(":")
            end_parts = end_str.split(":")
            start_time = time(int(start_parts[0]), int(start_parts[1]))
            end_time = time(int(end_parts[0]), int(end_parts[1]))
        except (ValueError, IndexError):
            return False

        now = dt_util.now().time()

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time

    def _eval_time_after_sunrise(self, condition: Condition) -> bool:
        """Evaluate time_after_sunrise condition."""
        offset_minutes = condition.params.get("offset", 0)
        sunrise = get_sunrise_time(self.hass)

        if sunrise is None:
            return False

        target_time = sunrise + (offset_minutes * 60)
        return dt_util.now().timestamp() >= target_time

    def _eval_time_after_sunset(self, condition: Condition) -> bool:
        """Evaluate time_after_sunset condition."""
        offset_minutes = condition.params.get("offset", 0)
        sunset = get_sunset_time(self.hass)

        if sunset is None:
            return False

        target_time = sunset + (offset_minutes * 60)
        return dt_util.now().timestamp() >= target_time

    def _eval_state_is(self, condition: Condition) -> bool:
        """Evaluate state_is condition."""
        entity_id = condition.params.get("entity")
        expected_state = condition.params.get("state")

        if not entity_id or expected_state is None:
            return False

        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        return state.state == str(expected_state)
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/engine.py
git commit -m "feat: add rule evaluation engine"
```

---

## Task 6: Coordinator

**Files:**
- Create: `custom_components/cover_automatic/coordinator.py`

**Step 1: Create data update coordinator**

```python
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

    def __init__(self, hass: HomeAssistant, storage: CoverAutomaticStorage) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
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

    def _setup_state_tracking(self) -> None:
        """Set up state change tracking for relevant entities."""
        entities_to_track: set[str] = {SUN_ENTITY_ID}

        for cover in self.storage.covers.values():
            entities_to_track.add(cover.entity_id)

        if self.storage.outdoor_temp_sensor:
            entities_to_track.add(self.storage.outdoor_temp_sensor)

        for rule in self.storage.rules.values():
            for condition in rule.conditions:
                if sensor := condition.params.get("sensor"):
                    entities_to_track.add(sensor)
                if entity := condition.params.get("entity"):
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

    @callback
    def _async_on_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if entity_id in [c.entity_id for c in self.storage.covers.values()]:
            self._handle_cover_state_change(entity_id, old_state, new_state)
        else:
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
        cover.status = CoverStatus.PAUSED
        cover.pause_until = dt_util.now().timestamp() + (cover.pause_duration * 60)
        self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str) -> None:
        """Resume automation for a cover."""
        cover = self.storage.covers.get(entity_id)
        if cover:
            self._cover_states[entity_id] = CoverStatus.AUTO
            cover.status = CoverStatus.AUTO
            cover.pause_until = None
            self.async_set_updated_data(self.data)

    def get_cover_status(self, entity_id: str) -> CoverStatus:
        """Get automation status for a cover."""
        cover = self.storage.covers.get(entity_id)
        if cover is None:
            return CoverStatus.MANUAL

        if not cover.auto_enabled:
            return CoverStatus.MANUAL

        status = self._cover_states.get(entity_id, CoverStatus.AUTO)

        if status == CoverStatus.PAUSED and cover.pause_until:
            if dt_util.now().timestamp() > cover.pause_until:
                self._cover_states[entity_id] = CoverStatus.AUTO
                cover.status = CoverStatus.AUTO
                cover.pause_until = None
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

        return result

    async def async_apply_positions(self) -> None:
        """Apply calculated positions to covers."""
        if not self.data:
            return

        for entity_id, cover_data in self.data.get("covers", {}).items():
            if cover_data["status"] != CoverStatus.AUTO.value:
                continue

            target = cover_data.get("target_position")
            if target is None:
                continue

            state = self.hass.states.get(entity_id)
            if state is None:
                continue

            try:
                current = int(state.attributes.get("current_position", 0))
            except (ValueError, TypeError):
                continue

            if current != target:
                _LOGGER.debug("Setting %s to position %s", entity_id, target)
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=False,
                )

    def async_shutdown(self) -> None:
        """Shut down coordinator."""
        for unsub in self._unsub_state_change:
            unsub()
        self._unsub_state_change.clear()
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/coordinator.py
git commit -m "feat: add data update coordinator with manual override detection"
```

---

## Task 7: Integration Setup

**Files:**
- Modify: `custom_components/cover_automatic/__init__.py`

**Step 1: Implement integration setup**

```python
"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import CoverAutomaticCoordinator
from .storage import CoverAutomaticStorage

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS_LIST: list[Platform] = [
    Platform.COVER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CoverAutomatic from YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CoverAutomatic from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    storage = CoverAutomaticStorage(hass)
    coordinator = CoverAutomaticCoordinator(hass, storage)

    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "storage": storage,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    entry.async_on_unload(coordinator.async_shutdown)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator = data["coordinator"]
        coordinator.async_shutdown()

    return unload_ok
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/__init__.py
git commit -m "feat: implement integration setup and teardown"
```

---

## Task 8: Config Flow - Basic Setup

**Files:**
- Create: `custom_components/cover_automatic/config_flow.py`

**Step 1: Create config flow**

```python
"""Config flow for CoverAutomatic integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, FACADE_PRESETS

_LOGGER = logging.getLogger(__name__)


class CoverAutomaticConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CoverAutomatic."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._data: dict[str, Any] = {}
        self._facades: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._data["name"] = user_input.get("name", "CoverAutomatic")
            return await self.async_step_facades()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default="CoverAutomatic"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_facades(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle facade configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("add_facade"):
                facade_name = user_input.get("facade_name", "")
                facade_direction = user_input.get("facade_direction", "south")

                if facade_name:
                    preset = FACADE_PRESETS.get(facade_direction, FACADE_PRESETS["south"])
                    self._facades.append(
                        {
                            "id": facade_name.lower().replace(" ", "_"),
                            "name": facade_name,
                            "direction": facade_direction,
                            "azimuth_start": preset["start"],
                            "azimuth_end": preset["end"],
                        }
                    )

                return await self.async_step_facades()

            if user_input.get("done"):
                self._data["facades"] = self._facades
                return await self.async_step_covers()

        facade_list = ", ".join([f["name"] for f in self._facades]) or "None"

        return self.async_show_form(
            step_id="facades",
            data_schema=vol.Schema(
                {
                    vol.Optional("facade_name"): str,
                    vol.Optional("facade_direction", default="south"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "north", "label": "North"},
                                {"value": "east", "label": "East"},
                                {"value": "south", "label": "South"},
                                {"value": "west", "label": "West"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("add_facade", default=False): bool,
                    vol.Optional("done", default=False): bool,
                }
            ),
            description_placeholders={"facades": facade_list},
            errors=errors,
        )

    async def async_step_covers(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle cover selection."""
        errors: dict[str, str] = {}

        cover_entities = [
            state.entity_id
            for state in self.hass.states.async_all("cover")
        ]

        if not cover_entities:
            return self.async_abort(reason="no_covers")

        if user_input is not None:
            self._data["covers"] = user_input.get("covers", [])
            return await self.async_step_sensors()

        facade_options = [{"value": f["id"], "label": f["name"]} for f in self._facades]
        if not facade_options:
            facade_options = [{"value": "none", "label": "No facade"}]

        return self.async_show_form(
            step_id="covers",
            data_schema=vol.Schema(
                {
                    vol.Required("covers"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="cover",
                            multiple=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle sensor configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data["outdoor_temp_sensor"] = user_input.get("outdoor_temp_sensor")
            return self.async_create_entry(
                title=self._data.get("name", "CoverAutomatic"),
                data=self._data,
            )

        temp_sensors = [
            state.entity_id
            for state in self.hass.states.async_all("sensor")
            if "temperature" in state.entity_id.lower()
            or state.attributes.get("device_class") == "temperature"
        ]

        schema: dict[Any, Any] = {}
        if temp_sensors:
            schema[vol.Optional("outdoor_temp_sensor")] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            )

        if not schema:
            return self.async_create_entry(
                title=self._data.get("name", "CoverAutomatic"),
                data=self._data,
            )

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CoverAutomaticOptionsFlow(config_entry)


class CoverAutomaticOptionsFlow(OptionsFlow):
    """Handle options flow for CoverAutomatic."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 60),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                }
            ),
        )
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/config_flow.py
git commit -m "feat: add config flow for UI-based setup"
```

---

## Task 9: Translation Files

**Files:**
- Create: `custom_components/cover_automatic/strings.json`
- Create: `custom_components/cover_automatic/translations/en.json`
- Create: `custom_components/cover_automatic/translations/de.json`

**Step 1: Create strings.json**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "CoverAutomatic Setup",
        "description": "Set up intelligent cover automation.",
        "data": {
          "name": "Integration name"
        }
      },
      "facades": {
        "title": "Configure Facades",
        "description": "Add building facades by cardinal direction. Current facades: {facades}",
        "data": {
          "facade_name": "Facade name",
          "facade_direction": "Direction",
          "add_facade": "Add this facade",
          "done": "Done adding facades"
        }
      },
      "covers": {
        "title": "Select Covers",
        "description": "Select cover entities to manage.",
        "data": {
          "covers": "Covers to manage"
        }
      },
      "sensors": {
        "title": "Temperature Sensors (Optional)",
        "description": "Configure temperature sensors for intelligent rules.",
        "data": {
          "outdoor_temp_sensor": "Outdoor temperature sensor"
        }
      }
    },
    "abort": {
      "already_configured": "CoverAutomatic is already configured.",
      "no_covers": "No cover entities found."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "CoverAutomatic Options",
        "data": {
          "scan_interval": "Scan interval (seconds)"
        }
      }
    }
  },
  "entity": {
    "switch": {
      "auto_enabled": {
        "name": "Automation"
      }
    },
    "sensor": {
      "status": {
        "name": "Status",
        "state": {
          "auto": "Automatic",
          "paused": "Paused",
          "manual": "Manual"
        }
      },
      "sun_on_facade": {
        "name": "Sun on facade"
      }
    },
    "select": {
      "scenario": {
        "name": "Scenario"
      }
    },
    "number": {
      "pause_duration": {
        "name": "Pause duration"
      }
    }
  }
}
```

**Step 2: Create translations/en.json (copy of strings.json)**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "CoverAutomatic Setup",
        "description": "Set up intelligent cover automation.",
        "data": {
          "name": "Integration name"
        }
      },
      "facades": {
        "title": "Configure Facades",
        "description": "Add building facades by cardinal direction. Current facades: {facades}",
        "data": {
          "facade_name": "Facade name",
          "facade_direction": "Direction",
          "add_facade": "Add this facade",
          "done": "Done adding facades"
        }
      },
      "covers": {
        "title": "Select Covers",
        "description": "Select cover entities to manage.",
        "data": {
          "covers": "Covers to manage"
        }
      },
      "sensors": {
        "title": "Temperature Sensors (Optional)",
        "description": "Configure temperature sensors for intelligent rules.",
        "data": {
          "outdoor_temp_sensor": "Outdoor temperature sensor"
        }
      }
    },
    "abort": {
      "already_configured": "CoverAutomatic is already configured.",
      "no_covers": "No cover entities found."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "CoverAutomatic Options",
        "data": {
          "scan_interval": "Scan interval (seconds)"
        }
      }
    }
  },
  "entity": {
    "switch": {
      "auto_enabled": {
        "name": "Automation"
      }
    },
    "sensor": {
      "status": {
        "name": "Status",
        "state": {
          "auto": "Automatic",
          "paused": "Paused",
          "manual": "Manual"
        }
      },
      "sun_on_facade": {
        "name": "Sun on facade"
      }
    },
    "select": {
      "scenario": {
        "name": "Scenario"
      }
    },
    "number": {
      "pause_duration": {
        "name": "Pause duration"
      }
    }
  }
}
```

**Step 3: Create translations/de.json**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "CoverAutomatic Einrichtung",
        "description": "Intelligente Beschattungsautomatik einrichten.",
        "data": {
          "name": "Integrationsname"
        }
      },
      "facades": {
        "title": "Fassaden konfigurieren",
        "description": "Fassaden nach Himmelsrichtung hinzufuegen. Aktuelle Fassaden: {facades}",
        "data": {
          "facade_name": "Fassadenname",
          "facade_direction": "Himmelsrichtung",
          "add_facade": "Diese Fassade hinzufuegen",
          "done": "Fertig mit Fassaden"
        }
      },
      "covers": {
        "title": "Beschattungen auswaehlen",
        "description": "Beschattungen zur Steuerung auswaehlen.",
        "data": {
          "covers": "Zu verwaltende Beschattungen"
        }
      },
      "sensors": {
        "title": "Temperatursensoren (Optional)",
        "description": "Temperatursensoren fuer intelligente Regeln konfigurieren.",
        "data": {
          "outdoor_temp_sensor": "Aussentemperatur-Sensor"
        }
      }
    },
    "abort": {
      "already_configured": "CoverAutomatic ist bereits konfiguriert.",
      "no_covers": "Keine Beschattungen gefunden."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "CoverAutomatic Optionen",
        "data": {
          "scan_interval": "Aktualisierungsintervall (Sekunden)"
        }
      }
    }
  },
  "entity": {
    "switch": {
      "auto_enabled": {
        "name": "Automatik"
      }
    },
    "sensor": {
      "status": {
        "name": "Status",
        "state": {
          "auto": "Automatisch",
          "paused": "Pausiert",
          "manual": "Manuell"
        }
      },
      "sun_on_facade": {
        "name": "Sonne auf Fassade"
      }
    },
    "select": {
      "scenario": {
        "name": "Szenario"
      }
    },
    "number": {
      "pause_duration": {
        "name": "Pausendauer"
      }
    }
  }
}
```

**Step 4: Commit**

```bash
git add custom_components/cover_automatic/strings.json custom_components/cover_automatic/translations/
git commit -m "feat: add translation files for EN and DE"
```

---

## Task 10: Entity Platforms - Switch

**Files:**
- Create: `custom_components/cover_automatic/switch.py`

**Step 1: Create switch platform**

```python
"""Switch platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

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
    """Set up switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[SwitchEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            CoverAutomaticAutoSwitch(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class CoverAutomaticAutoSwitch(CoordinatorEntity[CoverAutomaticCoordinator], SwitchEntity):
    """Switch to enable/disable automation for a cover."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_enabled"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_auto"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return true if automation is enabled."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        return cover.auto_enabled if cover else False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = True
            await self.coordinator.storage.async_add_cover(cover)
            self.coordinator.resume_cover(self._cover_entity_id)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = False
            await self.coordinator.storage.async_add_cover(cover)
            self.async_write_ha_state()
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/switch.py
git commit -m "feat: add switch platform for automation enable/disable"
```

---

## Task 11: Entity Platforms - Sensor

**Files:**
- Create: `custom_components/cover_automatic/sensor.py`

**Step 1: Create sensor platform**

```python
"""Sensor platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .models import CoverStatus

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
        status = self.coordinator.get_cover_status(self._cover_entity_id)
        match status:
            case CoverStatus.AUTO:
                return "mdi:robot"
            case CoverStatus.PAUSED:
                return "mdi:pause-circle"
            case CoverStatus.MANUAL:
                return "mdi:hand-back-right"
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
            facade_data = facades.get(self._facade_id, {})
            return "on" if facade_data.get("sun_on_facade", False) else "off"
        return "unknown"

    @property
    def icon(self) -> str:
        """Return icon based on sun status."""
        if self.native_value == "on":
            return "mdi:white-balance-sunny"
        return "mdi:weather-night"
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/sensor.py
git commit -m "feat: add sensor platform for status and sun indicators"
```

---

## Task 12: Entity Platforms - Select

**Files:**
- Create: `custom_components/cover_automatic/select.py`

**Step 1: Create select platform**

```python
"""Select platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

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
    """Set up select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    async_add_entities([ScenarioSelect(coordinator, entry.entry_id)])


class ScenarioSelect(CoordinatorEntity[CoverAutomaticCoordinator], SelectEntity):
    """Select entity for choosing active scenario."""

    _attr_has_entity_name = True
    _attr_translation_key = "scenario"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_scenario"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "CoverAutomatic",
            "manufacturer": "CoverAutomatic",
            "model": "Controller",
        }

    @property
    def options(self) -> list[str]:
        """Return available scenarios."""
        return list(self.coordinator.storage.scenarios.keys())

    @property
    def current_option(self) -> str | None:
        """Return current scenario."""
        return self.coordinator.storage.active_scenario

    async def async_select_option(self, option: str) -> None:
        """Change the selected scenario."""
        self.coordinator.storage.active_scenario = option
        await self.coordinator.storage.async_save()
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/select.py
git commit -m "feat: add select platform for scenario selection"
```

---

## Task 13: Entity Platforms - Number

**Files:**
- Create: `custom_components/cover_automatic/number.py`

**Step 1: Create number platform**

```python
"""Number platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

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
    """Set up number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[NumberEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            PauseDurationNumber(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class PauseDurationNumber(CoordinatorEntity[CoverAutomaticCoordinator], NumberEntity):
    """Number entity for pause duration configuration."""

    _attr_has_entity_name = True
    _attr_translation_key = "pause_duration"
    _attr_native_min_value = 0
    _attr_native_max_value = 480
    _attr_native_step = 5
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_pause_duration"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def native_value(self) -> float:
        """Return the current pause duration."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        return float(cover.pause_duration) if cover else 120.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the pause duration."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.pause_duration = int(value)
            await self.coordinator.storage.async_add_cover(cover)
            self.async_write_ha_state()
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/number.py
git commit -m "feat: add number platform for pause duration config"
```

---

## Task 14: Entity Platforms - Cover (Wrapper)

**Files:**
- Create: `custom_components/cover_automatic/cover.py`

**Step 1: Create cover platform**

```python
"""Cover platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

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
    """Set up cover entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[CoverEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            CoverAutomaticCover(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class CoverAutomaticCover(CoordinatorEntity[CoverAutomaticCoordinator], CoverEntity):
    """Wrapper cover entity with automation awareness."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        wrapped_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = cover_name
        self._attr_unique_id = f"{DOMAIN}_{wrapped_entity_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, wrapped_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def _wrapped_state(self):
        """Get the wrapped cover state."""
        return self.hass.states.get(self._wrapped_entity_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._wrapped_state is not None

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        state = self._wrapped_state
        if state is None:
            return None
        return state.state == "closed"

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover."""
        state = self._wrapped_state
        if state is None:
            return None
        return state.attributes.get(ATTR_POSITION)

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Return supported features."""
        state = self._wrapped_state
        if state is None:
            return CoverEntityFeature(0)
        return CoverEntityFeature(state.attributes.get("supported_features", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        status = self.coordinator.get_cover_status(self._wrapped_entity_id)
        cover_data = {}
        if self.coordinator.data:
            cover_data = self.coordinator.data.get("covers", {}).get(
                self._wrapped_entity_id, {}
            )

        return {
            "automation_status": status.value,
            "target_position": cover_data.get("target_position"),
            "wrapped_entity": self._wrapped_entity_id,
        }

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.services.async_call(
            "cover",
            "open_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.hass.services.async_call(
            "cover",
            "close_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.services.async_call(
            "cover",
            "stop_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        await self.hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": self._wrapped_entity_id, "position": position},
            blocking=True,
        )
```

**Step 2: Commit**

```bash
git add custom_components/cover_automatic/cover.py
git commit -m "feat: add cover platform as wrapper with automation status"
```

---

## Task 15: Services

**Files:**
- Create: `custom_components/cover_automatic/services.yaml`
- Create: `custom_components/cover_automatic/services.py`
- Modify: `custom_components/cover_automatic/__init__.py`

**Step 1: Create services.yaml**

```yaml
pause:
  name: Pause Automation
  description: Pause automation for a cover.
  fields:
    entity_id:
      name: Entity
      description: Cover entity to pause.
      required: true
      selector:
        entity:
          domain: cover

resume:
  name: Resume Automation
  description: Resume automation for a cover.
  fields:
    entity_id:
      name: Entity
      description: Cover entity to resume.
      required: true
      selector:
        entity:
          domain: cover

pause_all:
  name: Pause All
  description: Pause automation for all covers.

resume_all:
  name: Resume All
  description: Resume automation for all covers.

set_scenario:
  name: Set Scenario
  description: Set the active scenario.
  fields:
    scenario:
      name: Scenario
      description: Scenario to activate.
      required: true
      selector:
        text:

export_config:
  name: Export Configuration
  description: Export configuration to YAML file.
  fields:
    path:
      name: Path
      description: File path for export.
      default: "/config/cover_automatic_backup.yaml"
      selector:
        text:

import_config:
  name: Import Configuration
  description: Import configuration from YAML file.
  fields:
    path:
      name: Path
      description: File path to import from.
      required: true
      selector:
        text:
```

**Step 2: Create services.py**

```python
"""Service handlers for CoverAutomatic."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from homeassistant.core import ServiceCall

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for CoverAutomatic."""

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            if entity_id in coordinator.storage.covers:
                coordinator._pause_cover(coordinator.storage.covers[entity_id])
                break

    async def handle_resume(call: ServiceCall) -> None:
        """Handle resume service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            if entity_id in coordinator.storage.covers:
                coordinator.resume_cover(entity_id)
                break

    async def handle_pause_all(call: ServiceCall) -> None:
        """Handle pause_all service call."""
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            for cover in coordinator.storage.covers.values():
                coordinator._pause_cover(cover)

    async def handle_resume_all(call: ServiceCall) -> None:
        """Handle resume_all service call."""
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            for entity_id in coordinator.storage.covers:
                coordinator.resume_cover(entity_id)

    async def handle_set_scenario(call: ServiceCall) -> None:
        """Handle set_scenario service call."""
        scenario = call.data.get("scenario")
        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            coordinator = entry_data["coordinator"]
            if scenario in storage.scenarios:
                storage.active_scenario = scenario
                await storage.async_save()
                await coordinator.async_request_refresh()

    async def handle_export_config(call: ServiceCall) -> None:
        """Handle export_config service call."""
        path = call.data.get("path", "/config/cover_automatic_backup.yaml")
        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            data = storage.get_raw_data()

            def write_yaml():
                with open(path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            await hass.async_add_executor_job(write_yaml)
            _LOGGER.info("Configuration exported to %s", path)
            break

    async def handle_import_config(call: ServiceCall) -> None:
        """Handle import_config service call."""
        path = call.data.get("path")
        if not path:
            return

        file_path = Path(path)
        if not file_path.exists():
            _LOGGER.error("Import file not found: %s", path)
            return

        def read_yaml():
            with open(path) as f:
                return yaml.safe_load(f)

        data = await hass.async_add_executor_job(read_yaml)

        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            coordinator = entry_data["coordinator"]
            await storage.async_import_data(data)
            await coordinator.async_request_refresh()
            _LOGGER.info("Configuration imported from %s", path)
            break

    hass.services.async_register(DOMAIN, "pause", handle_pause)
    hass.services.async_register(DOMAIN, "resume", handle_resume)
    hass.services.async_register(DOMAIN, "pause_all", handle_pause_all)
    hass.services.async_register(DOMAIN, "resume_all", handle_resume_all)
    hass.services.async_register(DOMAIN, "set_scenario", handle_set_scenario)
    hass.services.async_register(DOMAIN, "export_config", handle_export_config)
    hass.services.async_register(DOMAIN, "import_config", handle_import_config)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, "pause")
    hass.services.async_remove(DOMAIN, "resume")
    hass.services.async_remove(DOMAIN, "pause_all")
    hass.services.async_remove(DOMAIN, "resume_all")
    hass.services.async_remove(DOMAIN, "set_scenario")
    hass.services.async_remove(DOMAIN, "export_config")
    hass.services.async_remove(DOMAIN, "import_config")
```

**Step 3: Update __init__.py to register services**

Add after `await hass.config_entries.async_forward_entry_setups`:

```python
from .services import async_setup_services, async_unload_services

# In async_setup_entry, after forwarding platforms:
await async_setup_services(hass)

# In async_unload_entry, before return:
if not hass.data[DOMAIN]:
    await async_unload_services(hass)
```

**Step 4: Commit**

```bash
git add custom_components/cover_automatic/services.yaml custom_components/cover_automatic/services.py custom_components/cover_automatic/__init__.py
git commit -m "feat: add service handlers for pause, resume, scenarios, import/export"
```

---

## Task 16: Final Integration Test

**Files:**
- Verify all files exist and are properly linked

**Step 1: Verify file structure**

```bash
find custom_components/cover_automatic -type f | sort
```

Expected output:
```
custom_components/cover_automatic/__init__.py
custom_components/cover_automatic/config_flow.py
custom_components/cover_automatic/const.py
custom_components/cover_automatic/coordinator.py
custom_components/cover_automatic/cover.py
custom_components/cover_automatic/engine.py
custom_components/cover_automatic/manifest.json
custom_components/cover_automatic/models.py
custom_components/cover_automatic/number.py
custom_components/cover_automatic/select.py
custom_components/cover_automatic/sensor.py
custom_components/cover_automatic/services.py
custom_components/cover_automatic/services.yaml
custom_components/cover_automatic/storage.py
custom_components/cover_automatic/strings.json
custom_components/cover_automatic/sun.py
custom_components/cover_automatic/switch.py
custom_components/cover_automatic/translations/de.json
custom_components/cover_automatic/translations/en.json
```

**Step 2: Update README with version**

Update version in README.md to reflect completed implementation.

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete initial CoverAutomatic implementation v0.1.0"
```

---

## Summary

This plan implements CoverAutomatic in 16 tasks:

1. **Manifest/Constants** - Basic integration structure
2. **Data Models** - Facade, Rule, Scenario, CoverConfig
3. **Storage** - Persistent configuration management
4. **Sun Calculations** - Facade sun exposure detection
5. **Rule Engine** - Condition evaluation logic
6. **Coordinator** - Central data management
7. **Integration Setup** - Entry points
8. **Config Flow** - UI wizard
9. **Translations** - EN/DE support
10. **Switch Platform** - Auto enable/disable
11. **Sensor Platform** - Status indicators
12. **Select Platform** - Scenario selector
13. **Number Platform** - Pause duration
14. **Cover Platform** - Wrapper entities
15. **Services** - pause, resume, export, import
16. **Verification** - Final checks
