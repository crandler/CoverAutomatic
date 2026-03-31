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
            return None

        # Sort by priority desc, then by rule ID asc for deterministic order
        matching_rules.sort(key=lambda x: (-x[0], x[1]))
        winner = matching_rules[0][2]
        return CoverTarget(
            position=winner.target_position,
            tilt_position=winner.target_tilt_position,
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

        # Auto comfort check: skip shading in HEATING mode
        comfort_mode = self._get_comfort_mode(cover)
        if comfort_mode == ComfortMode.HEATING:
            return False

        return True

    def _get_comfort_mode(self, cover: CoverConfig) -> ComfortMode | None:
        """Determine comfort mode from indoor temperature sensor.

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

        if temp >= self.storage.comfort_temp_max:
            return ComfortMode.COOLING
        if temp <= self.storage.comfort_temp_min:
            return ComfortMode.HEATING
        return ComfortMode.NEUTRAL

    def _eval_sun_elevation(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate sun elevation above/below threshold."""
        threshold = condition.params.get("value", 0)
        position = get_sun_position(self.hass)
        if position is None:
            return False
        return position[1] > threshold if above else position[1] < threshold

    def _eval_temp_threshold(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate outdoor temperature above/below threshold."""
        sensor_id = condition.params.get("sensor") or self.storage.outdoor_temp_sensor
        threshold = condition.params.get("value", 0)

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
        start_str = condition.params.get("start", "00:00")
        end_str = condition.params.get("end", "23:59")

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
        entity_id = condition.params.get("entity")
        expected_state = condition.params.get("state")

        if not entity_id or expected_state is None:
            return False

        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        return state.state == str(expected_state)

    def _eval_temp_comfort(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate temperature_comfort condition.

        Checks if current mode matches expected mode (cooling/heating/neutral).
        Uses indoor temp sensor (per-cover > global fallback) and comfort range from storage.
        """
        mode_val = condition.params.get("mode", ComfortMode.COOLING.value)
        try:
            expected_mode = ComfortMode(str(mode_val))
        except ValueError:
            expected_mode = ComfortMode.COOLING
        sensor_id = condition.params.get("sensor") or cover.indoor_temp_sensor or self.storage.indoor_temp_sensor

        if not sensor_id:
            return False

        state = self.hass.states.get(sensor_id)
        if state is None:
            return False

        try:
            temp = float(state.state)
        except (ValueError, TypeError):
            return False

        comfort_min = self.storage.comfort_temp_min
        comfort_max = self.storage.comfort_temp_max

        if temp >= comfort_max:
            current_mode = ComfortMode.COOLING
        elif temp <= comfort_min:
            current_mode = ComfortMode.HEATING
        else:
            current_mode = ComfortMode.NEUTRAL

        return current_mode == expected_mode

    def _eval_weather_is(self, condition: Condition) -> bool:
        """Evaluate weather_is condition.

        Checks if current weather matches expected conditions.
        Supports: sunny, cloudy, rainy, snowy, windy, clear
        """
        expected_states = condition.params.get("states", [])
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
