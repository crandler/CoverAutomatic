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
