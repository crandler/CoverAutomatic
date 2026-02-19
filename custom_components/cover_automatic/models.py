"""Data models for CoverAutomatic."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

_LOGGER = logging.getLogger(__name__)


class CoverStatus(StrEnum):
    """Cover automation status."""

    AUTO = "auto"
    PAUSED = "paused"
    MANUAL = "manual"
    LOCKED = "locked"


class ConditionType(StrEnum):
    """Rule condition types."""

    SUN_ON_FACADE = "sun_on_facade"
    SUN_ELEVATION_ABOVE = "sun_elevation_above"
    SUN_ELEVATION_BELOW = "sun_elevation_below"
    TEMPERATURE_ABOVE = "temperature_above"
    TEMPERATURE_BELOW = "temperature_below"
    TEMPERATURE_COMFORT = "temperature_comfort"
    TIME_BETWEEN = "time_between"
    TIME_AFTER_SUNRISE = "time_after_sunrise"
    TIME_AFTER_SUNSET = "time_after_sunset"
    STATE_IS = "state_is"
    WEATHER_IS = "weather_is"


class ComfortMode(StrEnum):
    """Temperature comfort mode result."""

    COOLING = "cooling"
    HEATING = "heating"
    NEUTRAL = "neutral"


@dataclass
class CoverTarget:
    """Target position and optional tilt for a cover."""

    position: int
    tilt_position: int | None = None


@dataclass
class Facade:
    """Represents a building facade with sun exposure settings."""

    id: str
    name: str
    azimuth_start: float
    azimuth_end: float
    direction: str = "south"
    min_elevation: float = 0.0
    cover_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "azimuth_start": self.azimuth_start,
            "azimuth_end": self.azimuth_end,
            "direction": self.direction,
            "min_elevation": self.min_elevation,
            "cover_ids": self.cover_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Facade:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            azimuth_start=float(data["azimuth_start"]) % 360,
            azimuth_end=float(data["azimuth_end"]) % 360,
            direction=data.get("direction", "south"),
            min_elevation=data.get("min_elevation", 0.0),
            cover_ids=list(data.get("cover_ids") or []),
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
    condition_operator: str = "and"  # "and" or "or"
    facade_ids: list[str] = field(default_factory=list)
    cover_ids: list[str] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    target_position: int = 0
    target_tilt_position: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "condition_operator": self.condition_operator,
            "facade_ids": self.facade_ids,
            "cover_ids": self.cover_ids,
            "conditions": [c.to_dict() for c in self.conditions],
            "target_position": self.target_position,
            "target_tilt_position": self.target_tilt_position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create from dictionary."""
        conditions: list[Condition] = []
        for c in data.get("conditions", []):
            try:
                conditions.append(Condition.from_dict(c))
            except (ValueError, KeyError) as err:
                _LOGGER.warning("Skipping invalid condition in rule '%s': %s", data.get("name", "?"), err)
        return cls(
            id=data["id"],
            name=data["name"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 10),
            condition_operator=data.get("condition_operator", "and")
            if data.get("condition_operator") in ("and", "or")
            else "and",
            facade_ids=list(data.get("facade_ids") or []),
            cover_ids=list(data.get("cover_ids") or []),
            conditions=conditions,
            target_position=data.get("target_position", 0),
            target_tilt_position=data.get("target_tilt_position"),
        )


@dataclass
class Scenario:
    """Automation scenario/mode."""

    id: str
    name: str
    icon: str = "mdi:home"
    rules_disabled: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "rules_disabled": self.rules_disabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data.get("icon", "mdi:home"),
            rules_disabled=list(data.get("rules_disabled") or []),
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
    lock_sensor: str | None = None
    lock_position: int = 100
    vent_sensor: str | None = None
    vent_position: int = 30
    inverted: bool = False
    supports_tilt: bool = False
    lock_tilt_position: int | None = None
    vent_tilt_position: int | None = None
    inverted_tilt: bool = False
    min_position_change: int = 5
    min_time_between_changes: int = 300
    last_position_change: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "facade_id": self.facade_id,
            "auto_enabled": self.auto_enabled,
            "pause_duration": self.pause_duration,
            "status": self.status.value,
            "pause_until": self.pause_until,
            "lock_sensor": self.lock_sensor,
            "lock_position": self.lock_position,
            "vent_sensor": self.vent_sensor,
            "vent_position": self.vent_position,
            "inverted": self.inverted,
            "supports_tilt": self.supports_tilt,
            "lock_tilt_position": self.lock_tilt_position,
            "vent_tilt_position": self.vent_tilt_position,
            "inverted_tilt": self.inverted_tilt,
            "min_position_change": self.min_position_change,
            "min_time_between_changes": self.min_time_between_changes,
            "last_position_change": self.last_position_change,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoverConfig:
        """Create from dictionary."""
        status_val = data.get("status", CoverStatus.AUTO.value)
        try:
            if isinstance(status_val, CoverStatus):
                status = status_val
            elif isinstance(status_val, str):
                status = CoverStatus(status_val)
            else:
                status = CoverStatus.AUTO
        except ValueError:
            _LOGGER.warning("Unknown cover status '%s' for '%s', defaulting to AUTO", status_val, data.get("entity_id", "?"))
            status = CoverStatus.AUTO
        return cls(
            entity_id=data["entity_id"],
            name=data["name"],
            facade_id=data.get("facade_id"),
            auto_enabled=data.get("auto_enabled", True),
            pause_duration=data.get("pause_duration", 120),
            status=status,
            pause_until=data.get("pause_until"),
            lock_sensor=data.get("lock_sensor"),
            lock_position=data.get("lock_position", 100),
            vent_sensor=data.get("vent_sensor"),
            vent_position=data.get("vent_position", 30),
            inverted=data.get("inverted", False),
            supports_tilt=data.get("supports_tilt", False),
            lock_tilt_position=data.get("lock_tilt_position"),
            vent_tilt_position=data.get("vent_tilt_position"),
            inverted_tilt=data.get("inverted_tilt", False),
            min_position_change=data.get("min_position_change", 5),
            min_time_between_changes=data.get("min_time_between_changes", 300),
            last_position_change=data.get("last_position_change"),
        )
