"""Rule evaluation engine for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import time
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from .models import ComfortMode, Condition, ConditionType, CoverConfig, Rule
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
        """Evaluate all conditions of a rule.

        Supports AND and OR operators:
        - AND (default): All conditions must be true
        - OR: At least one condition must be true
        """
        if not rule.conditions:
            return True

        if rule.condition_operator == "or":
            # OR: At least one condition must be true
            for condition in rule.conditions:
                if self._evaluate_condition(condition, cover):
                    return True
            return False
        else:
            # AND (default): All conditions must be true
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
                case ConditionType.TEMPERATURE_COMFORT:
                    return self._eval_temp_comfort(condition)
                case ConditionType.WEATHER_IS:
                    return self._eval_weather_is(condition)
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

    def _eval_temp_comfort(self, condition: Condition) -> bool:
        """Evaluate temperature_comfort condition.

        Checks if current mode matches expected mode (cooling/heating/neutral).
        Uses indoor temp sensor and comfort range from storage.
        """
        expected_mode = condition.params.get("mode", ComfortMode.COOLING)
        sensor_id = condition.params.get("sensor") or self.storage.indoor_temp_sensor

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

        if temp > comfort_max:
            current_mode = ComfortMode.COOLING
        elif temp < comfort_min:
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

        # Map common weather states
        sunny_states = ["sunny", "clear", "clear-night", "partlycloudy", "partly-cloudy"]
        cloudy_states = ["cloudy", "fog", "hazy", "overcast"]
        rainy_states = ["rainy", "pouring", "lightning", "lightning-rainy", "hail"]
        snowy_states = ["snowy", "snowy-rainy"]

        for expected in expected_states:
            expected = expected.lower()
            if expected == "sunny" and current_weather in sunny_states:
                return True
            if expected == "cloudy" and current_weather in cloudy_states:
                return True
            if expected == "rainy" and current_weather in rainy_states:
                return True
            if expected == "snowy" and current_weather in snowy_states:
                return True
            if expected == current_weather:
                return True

        return False
