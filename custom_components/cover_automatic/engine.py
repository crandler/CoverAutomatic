"""Rule evaluation engine for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import time
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from .models import ComfortMode, Condition, ConditionType, CoverConfig, CoverTarget, Rule
from .sun import get_sun_position, get_sunrise_time, get_sunset_time, is_sun_on_facade

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)

_WEATHER_MAP: dict[str, set[str]] = {
    "sunny": {"sunny", "clear", "clear-night"},
    "clear": {"clear", "clear-night"},
    "cloudy": {"cloudy", "fog", "hazy", "overcast", "partlycloudy", "partly-cloudy"},
    "rainy": {"rainy", "pouring", "lightning", "lightning-rainy", "hail"},
    "snowy": {"snowy", "snowy-rainy"},
    "windy": {"windy", "exceptional"},
}


class RuleEngine:
    """Evaluate rules and determine cover positions."""

    def __init__(self, hass: HomeAssistant, storage: CoverAutomaticStorage) -> None:
        """Initialize rule engine."""
        self.hass = hass
        self.storage = storage
        self._last_comfort_mode: dict[str, ComfortMode] = {}

    def evaluate_cover(self, cover: CoverConfig) -> CoverTarget | None:
        """Evaluate rules for a cover and return target position/tilt.

        Returns:
            CoverTarget with position (and optional tilt) or None if no rule matches.
        """
        active_scenario = self.storage.active_scenario
        matching_rules: list[tuple[int, str, Rule]] = []

        for rule in self.storage.rules.values():
            if not rule.enabled:
                continue

            if not self._rule_applies_to_cover(rule, cover):
                continue

            if not self._rule_active_in_scenario(rule, active_scenario):
                continue

            if self._evaluate_conditions(rule, cover):
                matching_rules.append((rule.priority, rule.id, rule))

        if not matching_rules:
            _LOGGER.debug("[%s] No rule matched", cover.entity_id)
            return None

        # Sort by priority desc, then by rule ID asc for deterministic order
        matching_rules.sort(key=lambda x: (-x[0], x[1]))
        winner = matching_rules[0][2]
        _LOGGER.debug(
            "[%s] Rule '%s' (P%d) -> position %d",
            cover.entity_id, winner.name, winner.priority, winner.target_position,
        )
        return CoverTarget(
            position=winner.target_position,
            tilt_position=winner.target_tilt_position,
            rule_id=winner.id,
            rule_name=winner.name,
        )

    def _rule_applies_to_cover(self, rule: Rule, cover: CoverConfig) -> bool:
        """Check if rule applies to cover.

        Rules without conditions AND without cover/facade assignments are
        treated as incomplete and do not match any cover.
        """
        if rule.cover_ids and cover.entity_id in rule.cover_ids:
            return True

        if rule.facade_ids and cover.facade_id in rule.facade_ids:
            return True

        # Global rule (no specific assignments) requires at least one condition
        if not rule.cover_ids and not rule.facade_ids:
            return bool(rule.conditions)

        return False

    def _rule_active_in_scenario(self, rule: Rule, scenario_id: str) -> bool:
        """Check if rule is active in current scenario.

        Uses simple blacklist logic: rules are active unless explicitly
        disabled in the scenario's rules_disabled list.
        """
        scenario = self.storage.scenarios.get(scenario_id)
        if scenario is None:
            return True
        return rule.id not in scenario.rules_disabled

    def _evaluate_conditions(self, rule: Rule, cover: CoverConfig) -> bool:
        """Evaluate all conditions of a rule.

        Supports AND and OR operators:
        - AND (default): All conditions must be true
        - OR: At least one condition must be true
        """
        if not rule.conditions:
            return True
        evaluator = any if rule.condition_operator == "or" else all
        return evaluator(
            self._evaluate_condition(c, cover) for c in rule.conditions
        )

    def _evaluate_condition(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate a single condition."""
        try:
            match condition.type:
                case ConditionType.SUN_ON_FACADE:
                    return self._eval_sun_on_facade(condition, cover)
                case ConditionType.SUN_ELEVATION_ABOVE:
                    return self._eval_sun_elevation(condition, above=True)
                case ConditionType.SUN_ELEVATION_BELOW:
                    return self._eval_sun_elevation(condition, above=False)
                case ConditionType.TEMPERATURE_ABOVE:
                    return self._eval_temp_threshold(condition, above=True)
                case ConditionType.TEMPERATURE_BELOW:
                    return self._eval_temp_threshold(condition, above=False)
                case ConditionType.TIME_BETWEEN:
                    return self._eval_time_between(condition)
                case ConditionType.TIME_AFTER_SUNRISE:
                    return self._eval_time_after_sun_event(condition, get_sunrise_time)
                case ConditionType.TIME_AFTER_SUNSET:
                    return self._eval_time_after_sun_event(condition, get_sunset_time)
                case ConditionType.STATE_IS:
                    return self._eval_state_is(condition)
                case ConditionType.TEMPERATURE_COMFORT:
                    return self._eval_temp_comfort(condition, cover)
                case ConditionType.WEATHER_IS:
                    return self._eval_weather_is(condition)
                case ConditionType.DAY_OF_WEEK:
                    return self._eval_day_of_week(condition)
                case _:
                    _LOGGER.warning("Unknown condition type: %s", condition.type)
                    return False
        except Exception as err:
            _LOGGER.error("Error evaluating condition %s: %s", condition.type, err)
            return False

    def _eval_sun_on_facade(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate sun_on_facade condition.

        Automatically considers indoor comfort temperature when a sensor is
        configured (per-cover > global fallback). In HEATING mode, returns
        False to let sunlight in and save heating energy.
        """
        facade_id = condition.params.get("facade") or cover.facade_id
        if not facade_id:
            return False

        facade = self.storage.facades.get(facade_id)
        if not facade:
            return False

        if not is_sun_on_facade(self.hass, facade):
            return False

        # Auto comfort check: only shade in COOLING mode
        comfort_mode = self._get_comfort_mode(cover)
        if comfort_mode is not None and comfort_mode != ComfortMode.COOLING:
            _LOGGER.debug(
                "[%s] sun_on_facade: skipping shading (%s mode)",
                cover.entity_id, comfort_mode.value,
            )
            return False

        return True

    def _get_comfort_mode(self, cover: CoverConfig) -> ComfortMode | None:
        """Determine comfort mode from indoor temperature sensor.

        Applies hysteresis to prevent oscillation at threshold boundaries:
        - Exit HEATING only when temp >= comfort_min + hysteresis
        - Exit COOLING only when temp <= comfort_max - hysteresis

        Returns None if no sensor is configured or unavailable.
        """
        sensor_id = cover.indoor_temp_sensor or self.storage.indoor_temp_sensor
        if not sensor_id:
            return None

        state = self.hass.states.get(sensor_id)
        if state is None:
            return None

        try:
            temp = float(state.state)
        except (ValueError, TypeError):
            return None

        h = self.storage.comfort_hysteresis
        prev = self._last_comfort_mode.get(cover.entity_id)
        comfort_min = cover.comfort_temp_min if cover.comfort_temp_min is not None else self.storage.comfort_temp_min
        comfort_max = cover.comfort_temp_max if cover.comfort_temp_max is not None else self.storage.comfort_temp_max

        if comfort_min >= comfort_max:
            _LOGGER.warning("[%s] comfort_min (%.1f) >= comfort_max (%.1f)", cover.entity_id, comfort_min, comfort_max)
            return None

        # Hard boundaries first, then hysteresis in the transition bands
        if temp >= comfort_max:
            mode = ComfortMode.COOLING
        elif temp <= comfort_min:
            mode = ComfortMode.HEATING
        elif prev == ComfortMode.HEATING and temp < comfort_min + h:
            mode = ComfortMode.HEATING
        elif prev == ComfortMode.COOLING and temp > comfort_max - h:
            mode = ComfortMode.COOLING
        else:
            mode = ComfortMode.NEUTRAL

        if mode != prev:
            _LOGGER.debug(
                "[%s] Comfort mode: %s -> %s (%.1f°, range %.1f-%.1f)",
                cover.entity_id, prev, mode.value, temp, comfort_min, comfort_max,
            )
        self._last_comfort_mode[cover.entity_id] = mode
        return mode

    def _eval_sun_elevation(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate sun elevation above/below threshold."""
        elev = condition.params.get("elevation")
        threshold = elev if elev is not None else condition.params.get("value", 0)
        position = get_sun_position(self.hass)
        if position is None:
            return False
        return position[1] > threshold if above else position[1] < threshold

    def _eval_temp_threshold(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate outdoor temperature above/below threshold."""
        sensor_id = condition.params.get("sensor") or self.storage.outdoor_temp_sensor
        temp_val = condition.params.get("temperature")
        threshold = temp_val if temp_val is not None else condition.params.get("value", 0)

        if not sensor_id:
            return False

        state = self.hass.states.get(sensor_id)
        if state is None:
            return False

        try:
            temp = float(state.state)
            return temp > threshold if above else temp < threshold
        except (ValueError, TypeError):
            return False

    def _eval_time_between(self, condition: Condition) -> bool:
        """Evaluate time_between condition."""
        start_str = condition.params.get("start_time") or condition.params.get("start", "00:00")
        end_str = condition.params.get("end_time") or condition.params.get("end", "23:59")

        try:
            start_parts = start_str.split(":")
            end_parts = end_str.split(":")
            start_time = time(int(start_parts[0]), int(start_parts[1]))
            # End time includes seconds for full-minute coverage
            end_sec = int(end_parts[2]) if len(end_parts) > 2 else 59
            end_time = time(int(end_parts[0]), int(end_parts[1]), end_sec)
        except (ValueError, IndexError):
            return False

        now = dt_util.now().time()

        # Same start and end means all day
        if start_time == end_time:
            return True

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time

    def _eval_time_after_sun_event(self, condition: Condition, event_fn) -> bool:
        """Evaluate time after sunrise/sunset with offset."""
        try:
            offset_minutes = int(condition.params.get("offset", 0))
        except (ValueError, TypeError):
            return False

        event_time = event_fn(self.hass)
        if event_time is None:
            return False

        target_time = event_time + (offset_minutes * 60)
        return dt_util.now().timestamp() >= target_time

    def _eval_state_is(self, condition: Condition) -> bool:
        """Evaluate state_is condition."""
        entity_id = condition.params.get("entity_id") or condition.params.get("entity")
        expected_state = condition.params.get("state")

        if not entity_id or expected_state is None:
            return False

        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        return state.state == str(expected_state)

    def _eval_temp_comfort(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate temperature_comfort condition.

        Uses hysteresis-aware _get_comfort_mode() for consistent behavior.
        """
        mode_val = condition.params.get("mode", ComfortMode.COOLING.value)
        try:
            expected_mode = ComfortMode(str(mode_val))
        except ValueError:
            expected_mode = ComfortMode.COOLING

        current_mode = self._get_comfort_mode(cover)
        if current_mode is None:
            return False
        return current_mode == expected_mode

    def _eval_weather_is(self, condition: Condition) -> bool:
        """Evaluate weather_is condition.

        Checks if current weather matches expected conditions.
        Supports: sunny, cloudy, rainy, snowy, windy, clear
        """
        # Panel sends single "weather" key, legacy uses "states" list
        weather_val = condition.params.get("weather")
        expected_states = [weather_val] if weather_val else condition.params.get("states", [])
        if isinstance(expected_states, str):
            expected_states = [expected_states]

        weather_entity = condition.params.get("entity") or self.storage.weather_entity
        if not weather_entity:
            return False

        state = self.hass.states.get(weather_entity)
        if state is None:
            return False

        current_weather = state.state.lower()

        for raw_expected in expected_states:
            expected = raw_expected.lower()
            mapped = _WEATHER_MAP.get(expected, set())
            if current_weather in mapped or expected == current_weather:
                return True

        return False

    def _eval_day_of_week(self, condition: Condition) -> bool:
        """Evaluate day_of_week condition."""
        days = condition.params.get("days", [])
        if not days:
            return True  # No restriction = any day
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        today = dt_util.now().weekday()
        return any(day_map.get(d.lower(), -1) == today for d in days)
