"""Data models for CoverAutomatic."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

# Upper bound on condition groups per rule (keeps the editor readable).
MAX_CONDITION_GROUPS = 10


def _to_int(
    value: Any, default: int | None, *, lo: int | None = None, hi: int | None = None
) -> int | None:
    """Coerce a stored/imported value to int (clamped), default on garbage.

    Accepts ints, floats and numeric strings ("10", "10.0"); None, booleans
    and anything unparsable fall back to the default.
    """
    if value is None or isinstance(value, bool):
        return default
    try:
        result = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default
    if lo is not None:
        result = max(lo, result)
    if hi is not None:
        result = min(hi, result)
    return result


def _opt_bool(value: Any) -> bool | None:
    """Coerce a tri-state flag (None = follow the global setting)."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "on", "yes", "1"):
            return True
        if text in ("false", "off", "no", "0"):
            return False
    return None


def _to_float(value: Any, default: float | None) -> float | None:
    """Coerce a stored/imported value to a finite float, default on garbage."""
    if value is None or isinstance(value, bool):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return result if math.isfinite(result) else default


def _to_bool(value: Any, default: bool) -> bool:
    """Coerce a stored/imported flag ("false"/"0" strings are False)."""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)


def _entity_id(value: Any) -> str | None:
    """Coerce an optional entity id (non-empty string, else None)."""
    return value if isinstance(value, str) and value else None


def _str_list(value: Any) -> list[str]:
    """Coerce a list of ids: only a list/tuple of non-empty strings is kept.

    Anything else (notably a bare string, which list() would split into
    characters) gives an empty list. Duplicates are dropped, order kept.
    """
    if not isinstance(value, (list, tuple)):
        return []
    return list(dict.fromkeys(v for v in value if isinstance(v, str) and v))


def finite_float(value: Any) -> float:
    """Voluptuous validator: a finite float (rejects NaN/inf, "nan", booleans)."""
    if isinstance(value, bool):
        raise vol.Invalid("expected a number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as err:
        raise vol.Invalid(f"expected a number, got {value!r}") from err
    if not math.isfinite(result):
        raise vol.Invalid(f"expected a finite number, got {value!r}")
    return result


def finite_range(min_value: float | None = None, max_value: float | None = None) -> Any:
    """Validator: finite float within [min_value, max_value]."""
    return vol.All(finite_float, vol.Range(min=min_value, max=max_value))


def int_range(min_value: int | None = None, max_value: int | None = None) -> Any:
    """Validator: integer (from a finite number) within [min_value, max_value]."""
    return vol.All(finite_float, vol.Coerce(int), vol.Range(min=min_value, max=max_value))


def optional_entity_id(value: Any) -> str | None:
    """Validate an optional entity id: None/"" -> None, else "domain.object"."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        domain, dot, object_id = value.strip().partition(".")
        if dot and domain and object_id:
            return value.strip()
    raise vol.Invalid(f"Invalid entity id: {value!r}")


# Condition params read as numbers by the engine: a non-finite value (NaN,
# inf, "nan") is refused so it can neither be stored nor crash an update.
_NUMERIC_PARAMS = ("value", "elevation", "temperature", "hysteresis", "delta", "offset")


def _check_numeric_params(params: dict[str, Any]) -> None:
    """Raise ValueError when a numeric condition param is not finite."""
    for key in _NUMERIC_PARAMS:
        raw = params.get(key)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            number = float(raw)
        except (TypeError, ValueError, OverflowError):
            continue  # not numeric: left to the engine (e.g. an entity state)
        if not math.isfinite(number):
            raise ValueError(f"param '{key}' must be a finite number, got {raw!r}")


def _position(value: Any, default: int | None) -> int | None:
    """Coerce a 0-100 position."""
    return _to_int(value, default, lo=0, hi=100)


class CoverStatus(StrEnum):
    """Cover automation status."""

    AUTO = "auto"
    PAUSED = "paused"
    MANUAL = "manual"
    LOCKED = "locked"
    VENTING = "venting"
    WIND_PROTECTED = "wind_protected"


class ConditionType(StrEnum):
    """Rule condition types."""

    SUN_ON_FACADE = "sun_on_facade"
    SUN_ELEVATION_ABOVE = "sun_elevation_above"
    SUN_ELEVATION_BELOW = "sun_elevation_below"
    TEMPERATURE_ABOVE = "temperature_above"
    TEMPERATURE_BELOW = "temperature_below"
    TEMPERATURE_COMFORT = "temperature_comfort"
    # Outdoor air warmer/cooler than the cover's room (params: operator, delta)
    OUTDOOR_VS_INDOOR = "outdoor_vs_indoor"
    # The cover's room is occupied (per-cover occupancy sensor)
    ROOM_OCCUPIED = "room_occupied"
    TIME_BETWEEN = "time_between"
    TIME_AFTER_SUNRISE = "time_after_sunrise"
    TIME_AFTER_SUNSET = "time_after_sunset"
    TIME_BEFORE_SUNRISE = "time_before_sunrise"
    TIME_BEFORE_SUNSET = "time_before_sunset"
    TIME_AFTER_DAWN = "time_after_dawn"
    TIME_BEFORE_DAWN = "time_before_dawn"
    TIME_AFTER_DUSK = "time_after_dusk"
    TIME_BEFORE_DUSK = "time_before_dusk"
    STATE_IS = "state_is"
    NUMERIC_STATE = "numeric_state"
    WEATHER_IS = "weather_is"
    DAY_OF_WEEK = "day_of_week"
    WORKDAY = "workday"
    # Native Home Assistant condition (params: {"config": {...}, "yaml": str, "ui": str})
    HA_CONDITION = "ha_condition"


class ComfortMode(StrEnum):
    """Temperature comfort mode result."""

    COOLING = "cooling"
    HEATING = "heating"
    NEUTRAL = "neutral"


@dataclass(slots=True)
class CoverTarget:
    """Target position and optional tilt for a cover."""

    position: int
    tilt_position: int | None = None
    rule_id: str | None = None
    rule_name: str | None = None
    # True when the winning rule is a safety rule (overrides pause/manual/wind)
    safety: bool = False


@dataclass(slots=True)
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
        azimuths = []
        for key in ("azimuth_start", "azimuth_end"):
            value = _to_float(data[key], None)
            if value is None:
                # No sensible default for an orientation: the entry is corrupt
                raise ValueError(f"{key} must be a finite number, got {data[key]!r}")
            azimuths.append(value % 360)
        min_elevation = _to_float(data.get("min_elevation"), 0.0)
        return cls(
            id=data["id"],
            name=data["name"],
            azimuth_start=azimuths[0],
            azimuth_end=azimuths[1],
            direction=data.get("direction", "south"),
            min_elevation=max(-90.0, min(90.0, min_elevation)),
            cover_ids=_str_list(data.get("cover_ids")),
        )


@dataclass(slots=True)
class Condition:
    """Rule condition."""

    type: ConditionType
    params: dict[str, Any] = field(default_factory=dict)
    # Index of the condition group this condition belongs to (0 = first).
    group: int = 0
    # Invert the result (NOT). An unavailable input never becomes "met".
    negate: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "params": self.params,
            "group": self.group,
            "negate": self.negate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Condition:
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"condition must be a dict, got {type(data).__name__}")
        raw_params = data.get("params", {})
        if not isinstance(raw_params, dict):
            raise ValueError(f"params must be a dict, got {type(raw_params).__name__}")
        _check_numeric_params(raw_params)
        try:
            group = max(0, int(data.get("group") or 0))
        except (TypeError, ValueError):
            group = 0
        return cls(
            type=ConditionType(data["type"]),
            params=dict(raw_params),
            group=min(group, MAX_CONDITION_GROUPS - 1),
            negate=_to_bool(data.get("negate"), False),
        )


@dataclass(slots=True)
class Rule:
    """Automation rule with conditions and action."""

    id: str
    name: str
    enabled: bool = True
    priority: int = 10
    # Operator BETWEEN condition groups ("and"/"or"). With a single group it
    # is unused: the group's own operator (group_operators[0]) applies.
    condition_operator: str = "and"
    facade_ids: list[str] = field(default_factory=list)
    cover_ids: list[str] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    target_position: int = 0
    target_tilt_position: int | None = None
    # Scenarios this rule belongs to (None = all scenarios). Within a member
    # scenario the rule can still be switched off via Scenario.rules_disabled.
    scenario_ids: list[str] | None = None
    # Operator INSIDE each condition group ("and"/"or"), one per group.
    # None = a single group using condition_operator (pre-groups behaviour).
    group_operators: list[str] | None = None
    # Safety rule: also drives covers that are paused, manual, wind protected
    # or with the automation disabled (never window-locked ones).
    safety: bool = False

    def effective_group_operators(self) -> list[str]:
        """Operators per group, falling back to the single-group form."""
        return list(self.group_operators or [self.condition_operator])

    def condition_groups(self) -> list[tuple[str, list[Condition]]]:
        """Return (operator, conditions) per group, empty groups skipped."""
        operators = self.effective_group_operators()
        count = len(operators)
        for cond in self.conditions:
            count = max(count, cond.group + 1)
        groups: list[tuple[str, list[Condition]]] = []
        for index in range(count):
            members = [c for c in self.conditions if c.group == index]
            if not members:
                continue
            op = operators[index] if index < len(operators) else "and"
            groups.append((op, members))
        return groups

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
            "scenario_ids": self.scenario_ids,
            "group_operators": self.effective_group_operators(),
            "safety": self.safety,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create from dictionary."""
        conditions: list[Condition] = []
        dropped = 0
        raw_conditions = data.get("conditions")
        for c in raw_conditions if isinstance(raw_conditions, list) else []:
            try:
                conditions.append(Condition.from_dict(c))
            except (ValueError, KeyError) as err:
                dropped += 1
                _LOGGER.warning("Skipping invalid condition in rule '%s': %s", data.get("name", "?"), err)
        operator = data.get("condition_operator", "and")
        if operator not in ("and", "or"):
            operator = "and"
        raw_groups = data.get("group_operators")
        if isinstance(raw_groups, list) and raw_groups:
            group_operators = [
                op if op in ("and", "or") else "and"
                for op in raw_groups[:MAX_CONDITION_GROUPS]
            ]
        else:
            # Before condition groups: one group using the rule's operator.
            group_operators = [operator]
        facade_ids = _str_list(data.get("facade_ids"))
        cover_ids = _str_list(data.get("cover_ids"))
        enabled = _to_bool(data.get("enabled"), True)
        if enabled and not (facade_ids or cover_ids) and (
            data.get("facade_ids") or data.get("cover_ids")
        ):
            # Unusable assignments must not turn the rule into a global one
            _LOGGER.warning(
                "Rule '%s' has invalid cover/facade references and was disabled",
                data.get("name", "?"),
            )
            enabled = False
        if enabled and dropped:
            # Without the dropped condition(s) the rule would match more
            # often than configured -- always, when none is left. Keep it
            # (the user can fix it) but disabled. A rule configured without
            # conditions is not concerned (dropped == 0).
            _LOGGER.warning(
                "Rule '%s' had %d invalid condition(s) and was disabled",
                data.get("name", "?"), dropped,
            )
            enabled = False
        # Missing or not a list (never split a string): every scenario
        raw_scenarios = data.get("scenario_ids")
        scenario_ids = _str_list(raw_scenarios) if isinstance(raw_scenarios, list) else None
        return cls(
            id=data["id"],
            name=data["name"],
            enabled=enabled,
            priority=_to_int(data.get("priority"), 10),
            condition_operator=operator,
            facade_ids=facade_ids,
            cover_ids=cover_ids,
            conditions=conditions,
            target_position=_position(data.get("target_position"), 0),
            target_tilt_position=_position(data.get("target_tilt_position"), None),
            scenario_ids=scenario_ids,
            group_operators=group_operators,
            safety=_to_bool(data.get("safety"), False),
        )


@dataclass(slots=True)
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
            rules_disabled=_str_list(data.get("rules_disabled")),
        )


@dataclass(slots=True)
class CoverConfig:
    """Configuration for a managed cover."""

    entity_id: str
    name: str
    facade_id: str | None = None
    auto_enabled: bool = True
    pause_duration: int | None = None
    status: CoverStatus = CoverStatus.AUTO
    pause_until: float | None = None
    lock_sensor: str | None = None
    lock_position: int | None = None
    vent_sensor: str | None = None
    vent_position: int | None = None
    inverted: bool = False
    supports_tilt: bool = False
    lock_tilt_position: int | None = None
    vent_tilt_position: int | None = None
    inverted_tilt: bool = False
    indoor_temp_sensor: str | None = None
    comfort_temp_min: float | None = None
    comfort_temp_max: float | None = None
    # Entities (input_number/number/sensor) overriding the comfort band
    comfort_temp_min_entity: str | None = None
    comfort_temp_max_entity: str | None = None
    # Sun-on-facade comfort switches: None = follow the global setting
    preemptive_shading: bool | None = None
    sun_heating_ignore: bool | None = None
    sun_neutral_ignore: bool | None = None
    # End a manual pause once the cover is back at its rule's position
    # (None = follow the global setting)
    pause_resume_on_match: bool | None = None
    # Window open: keep the current position (True) instead of moving to lock_position
    lock_hold_position: bool = False
    # Room occupancy (condition "room occupied"): entity and the states that
    # mean occupied (comma-separated; None = usual defaults, e.g. on/home/Présent)
    occupancy_sensor: str | None = None
    occupancy_states: str | None = None
    min_position_change: int | None = None
    min_time_between_changes: int | None = None
    last_position_change: float | None = None
    # Full 0-100 % travel time in seconds: configured, and learned from moves
    travel_time: int | None = None
    measured_travel_time: float | None = None

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
            "indoor_temp_sensor": self.indoor_temp_sensor,
            "comfort_temp_min": self.comfort_temp_min,
            "comfort_temp_max": self.comfort_temp_max,
            "comfort_temp_min_entity": self.comfort_temp_min_entity,
            "comfort_temp_max_entity": self.comfort_temp_max_entity,
            "preemptive_shading": self.preemptive_shading,
            "sun_heating_ignore": self.sun_heating_ignore,
            "sun_neutral_ignore": self.sun_neutral_ignore,
            "pause_resume_on_match": self.pause_resume_on_match,
            "lock_hold_position": self.lock_hold_position,
            "occupancy_sensor": self.occupancy_sensor,
            "occupancy_states": self.occupancy_states,
            "min_position_change": self.min_position_change,
            "min_time_between_changes": self.min_time_between_changes,
            "last_position_change": self.last_position_change,
            "travel_time": self.travel_time,
            "measured_travel_time": self.measured_travel_time,
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
            _LOGGER.warning(
                "Unknown cover status '%s' for '%s', defaulting to AUTO",
                status_val, data.get("entity_id", "?"),
            )
            status = CoverStatus.AUTO
        return cls(
            entity_id=data["entity_id"],
            name=data["name"],
            facade_id=_entity_id(data.get("facade_id")),
            auto_enabled=_to_bool(data.get("auto_enabled"), True),
            # Minimum 1 minute (a 0 stored by an older version becomes 1)
            pause_duration=_to_int(data.get("pause_duration"), None, lo=1),
            status=status,
            pause_until=_to_float(data.get("pause_until"), None),
            lock_sensor=_entity_id(data.get("lock_sensor")),
            lock_position=_position(data.get("lock_position"), None),
            vent_sensor=_entity_id(data.get("vent_sensor")),
            vent_position=_position(data.get("vent_position"), None),
            inverted=_to_bool(data.get("inverted"), False),
            supports_tilt=_to_bool(data.get("supports_tilt"), False),
            lock_tilt_position=_position(data.get("lock_tilt_position"), None),
            vent_tilt_position=_position(data.get("vent_tilt_position"), None),
            inverted_tilt=_to_bool(data.get("inverted_tilt"), False),
            indoor_temp_sensor=_entity_id(data.get("indoor_temp_sensor")),
            comfort_temp_min=_to_float(data.get("comfort_temp_min"), None),
            comfort_temp_max=_to_float(data.get("comfort_temp_max"), None),
            comfort_temp_min_entity=_entity_id(data.get("comfort_temp_min_entity")),
            comfort_temp_max_entity=_entity_id(data.get("comfort_temp_max_entity")),
            preemptive_shading=_opt_bool(data.get("preemptive_shading")),
            sun_heating_ignore=_opt_bool(data.get("sun_heating_ignore")),
            sun_neutral_ignore=_opt_bool(data.get("sun_neutral_ignore")),
            pause_resume_on_match=_opt_bool(data.get("pause_resume_on_match")),
            lock_hold_position=_to_bool(data.get("lock_hold_position"), False),
            occupancy_sensor=_entity_id(data.get("occupancy_sensor")),
            occupancy_states=(str(data["occupancy_states"]).strip() or None)
            if data.get("occupancy_states") is not None else None,
            min_position_change=_to_int(data.get("min_position_change"), None, lo=0, hi=100),
            min_time_between_changes=_to_int(data.get("min_time_between_changes"), None, lo=0),
            last_position_change=_to_float(data.get("last_position_change"), None),
            travel_time=_to_int(data.get("travel_time"), None, lo=0),
            measured_travel_time=_to_float(data.get("measured_travel_time"), None),
        )
