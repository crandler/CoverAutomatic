"""Rule evaluation engine for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import time
from time import monotonic
from typing import TYPE_CHECKING, Any

from homeassistant.util import dt as dt_util

from .models import ComfortMode, Condition, ConditionType, CoverConfig, CoverTarget, Rule
from .sun import get_sun_position, get_sunrise_time, get_sunset_time, is_sun_on_facade

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)

# How long to keep using the last known comfort mode when the indoor temp
# sensor goes unavailable (e.g. Zigbee bridge restart). Prevents brief sensor
# outages from dropping the shading rule and triggering a fallback movement.
COMFORT_SENSOR_GRACE_PERIOD = 900  # seconds

_WEATHER_MAP: dict[str, set[str]] = {
    "sunny": {"sunny", "clear", "clear-night"},
    "clear": {"clear", "clear-night"},
    "cloudy": {"cloudy", "fog", "hazy", "overcast", "partlycloudy", "partly-cloudy"},
    "rainy": {"rainy", "pouring", "lightning", "lightning-rainy", "hail"},
    "snowy": {"snowy", "snowy-rainy"},
    "windy": {"windy", "exceptional"},
}

# Condition types whose result depends on a specific cover/facade context
# (facade azimuth, per-cover comfort range/sensor). They cannot be previewed
# in the rule editor without one and report evaluable=False.
_CONTEXT_DEPENDENT_TYPES: frozenset = frozenset(
    {ConditionType.SUN_ON_FACADE, ConditionType.TEMPERATURE_COMFORT}
)


class RuleEngine:
    """Evaluate rules and determine cover positions."""

    def __init__(self, hass: HomeAssistant, storage: CoverAutomaticStorage) -> None:
        """Initialize rule engine."""
        self.hass = hass
        self.storage = storage
        self._last_comfort_mode: dict[str, ComfortMode] = {}
        self._last_comfort_read: dict[str, float] = {}
        # Hysteresis state for temperature_above/below, keyed by
        # (sensor_id, threshold, above) so it survives rule edits and is
        # shared by rules using the identical threshold.
        self._threshold_states: dict[tuple[str, float, bool], bool] = {}

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

    def _evaluate_condition(
        self, condition: Condition, cover: CoverConfig, *, update_state: bool = True
    ) -> bool:
        """Evaluate a single condition.

        update_state=False keeps threshold hysteresis state untouched, so the
        rule editor's live preview cannot shift the runtime deadband.
        """
        try:
            match condition.type:
                case ConditionType.SUN_ON_FACADE:
                    return self._eval_sun_on_facade(condition, cover)
                case ConditionType.SUN_ELEVATION_ABOVE:
                    return self._eval_sun_elevation(condition, above=True)
                case ConditionType.SUN_ELEVATION_BELOW:
                    return self._eval_sun_elevation(condition, above=False)
                case ConditionType.TEMPERATURE_ABOVE:
                    return self._eval_temp_threshold(
                        condition, above=True, update_state=update_state
                    )
                case ConditionType.TEMPERATURE_BELOW:
                    return self._eval_temp_threshold(
                        condition, above=False, update_state=update_state
                    )
                case ConditionType.TIME_BETWEEN:
                    return self._eval_time_between(condition)
                case ConditionType.TIME_AFTER_SUNRISE:
                    return self._eval_time_after_sun_event(condition, get_sunrise_time)
                case ConditionType.TIME_AFTER_SUNSET:
                    return self._eval_time_after_sun_event(condition, get_sunset_time)
                case ConditionType.TIME_BEFORE_SUNRISE:
                    return self._eval_time_before_sun_event(condition, get_sunrise_time)
                case ConditionType.TIME_BEFORE_SUNSET:
                    return self._eval_time_before_sun_event(condition, get_sunset_time)
                case ConditionType.STATE_IS:
                    return self._eval_state_is(condition)
                case ConditionType.NUMERIC_STATE:
                    return self._eval_numeric_state(
                        condition, update_state=update_state
                    )
                case ConditionType.TEMPERATURE_COMFORT:
                    return self._eval_temp_comfort(condition, cover)
                case ConditionType.WEATHER_IS:
                    return self._eval_weather_is(condition)
                case ConditionType.DAY_OF_WEEK:
                    return self._eval_day_of_week(condition)
                case ConditionType.WORKDAY:
                    return self._eval_workday(condition)
                case _:
                    _LOGGER.warning("Unknown condition type: %s", condition.type)
                    return False
        except Exception as err:
            _LOGGER.error("Error evaluating condition %s: %s", condition.type, err, exc_info=True)
            return False

    def preview_condition(self, condition: Condition) -> dict[str, Any]:
        """Evaluate a condition for the rule editor's live preview.

        Returns a context-free snapshot: whether the condition currently
        matches plus the raw, language-neutral actual value (the panel
        localizes it). Context-dependent types (sun_on_facade,
        temperature_comfort) need a cover and return {"evaluable": False}.

        Side-effect free: only the stateless global _eval_* helpers run, so
        the comfort grace-period state is never touched.
        """
        if condition.type in _CONTEXT_DEPENDENT_TYPES:
            return {"evaluable": False}
        try:
            # cover is unused for global condition types (filtered above)
            matched = self._evaluate_condition(
                condition, None, update_state=False,  # type: ignore[arg-type]
            )
            actual, kind = self._preview_actual(condition)
            return {"evaluable": True, "matched": matched, "actual": actual, "kind": kind}
        except Exception as err:  # defensive: preview must never raise
            _LOGGER.debug("preview_condition(%s) failed: %s", condition.type, err)
            return {"evaluable": True, "matched": False, "actual": None, "kind": None}

    def _preview_actual(self, condition: Condition) -> tuple[Any, str | None]:
        """Return (actual_value, kind) for a global condition's current reading."""
        t = condition.type
        if t in (ConditionType.SUN_ELEVATION_ABOVE, ConditionType.SUN_ELEVATION_BELOW):
            position = get_sun_position(self.hass)
            return (round(position[1], 1) if position else None), "elevation"
        if t in (ConditionType.TEMPERATURE_ABOVE, ConditionType.TEMPERATURE_BELOW):
            sensor_id = condition.params.get("sensor") or self.storage.outdoor_temp_sensor
            return self._read_float_state(sensor_id), "temp"
        if t == ConditionType.TIME_BETWEEN:
            return dt_util.now().strftime("%H:%M"), "time"
        if t in (
            ConditionType.TIME_AFTER_SUNRISE, ConditionType.TIME_BEFORE_SUNRISE,
            ConditionType.TIME_AFTER_SUNSET, ConditionType.TIME_BEFORE_SUNSET,
        ):
            return self._preview_sun_time(condition), "sun_time"
        if t == ConditionType.NUMERIC_STATE:
            entity_id = condition.params.get("entity_id") or condition.params.get("entity")
            return self._read_float_state(entity_id), "numeric"
        if t == ConditionType.STATE_IS:
            entity_id = condition.params.get("entity_id") or condition.params.get("entity")
            return self._read_state(entity_id), "state"
        if t == ConditionType.WEATHER_IS:
            entity_id = condition.params.get("entity") or self.storage.weather_entity
            return self._read_state(entity_id), "weather"
        if t == ConditionType.DAY_OF_WEEK:
            codes = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
            return codes[dt_util.now().weekday()], "day"
        if t == ConditionType.WORKDAY:
            entity_id = condition.params.get("entity_id") or self.storage.workday_sensor
            return self._read_state(entity_id), "workday"
        return None, None

    def _preview_sun_time(self, condition: Condition) -> str | None:
        """Compute the threshold clock time (sun event + offset) as HH:MM."""
        event_fn = (
            get_sunrise_time if "sunrise" in condition.type.value else get_sunset_time
        )
        event_time = event_fn(self.hass)
        if event_time is None:
            return None
        try:
            offset = int(condition.params.get("offset", 0))
        except (ValueError, TypeError):
            offset = 0
        target = dt_util.as_local(dt_util.utc_from_timestamp(event_time + offset * 60))
        return target.strftime("%H:%M")

    def _read_state(self, entity_id: str | None) -> str | None:
        """Return an entity's raw state string, or None if missing/unavailable."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown"):
            return None
        return state.state

    def _read_float_state(self, entity_id: str | None) -> float | None:
        """Return an entity's numeric state rounded to 1 decimal, or None."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return round(float(state.state), 1)
        except (ValueError, TypeError):
            return None

    def _eval_sun_on_facade(self, condition: Condition, cover: CoverConfig) -> bool:
        """Evaluate sun_on_facade condition.

        Automatically considers indoor comfort temperature when a sensor is
        configured (per-cover > global fallback). In HEATING mode, returns
        False to let sunlight in and save heating energy.
        When a sensor is configured but unavailable, the last known comfort
        mode is held for COMFORT_SENSOR_GRACE_PERIOD; beyond that (or without
        a prior reading) returns False (wait for reliable data before acting).
        """
        facade_id = condition.params.get("facade") or cover.facade_id
        if not facade_id:
            return False

        facade = self.storage.facades.get(facade_id)
        if not facade:
            return False

        if not is_sun_on_facade(self.hass, facade):
            return False

        # Auto comfort check: shade in COOLING, optionally in NEUTRAL with solar trigger
        sensor_id = cover.indoor_temp_sensor or self.storage.indoor_temp_sensor
        if sensor_id:
            comfort_mode = self._get_comfort_mode(cover)
            if comfort_mode is None:
                _LOGGER.debug(
                    "[%s] sun_on_facade: sensor unavailable, deferring",
                    cover.entity_id,
                )
                return False
            if comfort_mode == ComfortMode.COOLING:
                return True
            if (
                comfort_mode == ComfortMode.NEUTRAL
                and cover.preemptive_shading
                and self._check_solar_intensity()
            ):
                _LOGGER.debug(
                    "[%s] sun_on_facade: preemptive shading (solar above threshold)",
                    cover.entity_id,
                )
                return True
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

        When the sensor goes unavailable, the last known mode is held for
        COMFORT_SENSOR_GRACE_PERIOD so brief outages (e.g. Zigbee bridge
        restart) do not drop active rules. Returns None if no sensor is
        configured, or unavailable beyond the grace period.
        """
        sensor_id = cover.indoor_temp_sensor or self.storage.indoor_temp_sensor
        if not sensor_id:
            return None

        state = self.hass.states.get(sensor_id)
        try:
            temp = float(state.state) if state is not None else None
        except (ValueError, TypeError):
            temp = None

        if temp is None:
            prev = self._last_comfort_mode.get(cover.entity_id)
            last_read = self._last_comfort_read.get(cover.entity_id)
            if (
                prev is not None
                and last_read is not None
                and monotonic() - last_read < COMFORT_SENSOR_GRACE_PERIOD
            ):
                _LOGGER.debug(
                    "[%s] Comfort sensor %s unavailable, holding last mode %s (grace period)",
                    cover.entity_id, sensor_id, prev.value,
                )
                return prev
            return None

        self._last_comfort_read[cover.entity_id] = monotonic()
        h = self.storage.comfort_hysteresis
        prev = self._last_comfort_mode.get(cover.entity_id)
        comfort_min = cover.comfort_temp_min if cover.comfort_temp_min is not None else self.storage.comfort_temp_min
        comfort_max = cover.comfort_temp_max if cover.comfort_temp_max is not None else self.storage.comfort_temp_max

        if comfort_min >= comfort_max:
            _LOGGER.warning("[%s] comfort_min (%.1f) >= comfort_max (%.1f)", cover.entity_id, comfort_min, comfort_max)
            return None

        # Hard boundaries first, then hysteresis in the transition bands.
        # On first evaluation (prev=None, e.g. after restart), use hard
        # boundaries only -- hysteresis should not bias towards COOLING or
        # HEATING when there is no prior mode to maintain.
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

    def _check_solar_intensity(self) -> bool:
        """Check if solar intensity exceeds threshold for preemptive shading."""
        sensor_id = self.storage.solar_sensor
        if not sensor_id:
            return False
        threshold = self.storage.solar_threshold
        if threshold <= 0:
            return False
        state = self.hass.states.get(sensor_id)
        if state is None or state.state in ("unavailable", "unknown"):
            return False
        try:
            return float(state.state) > threshold
        except (ValueError, TypeError):
            return False

    def _eval_sun_elevation(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate sun elevation above/below threshold."""
        elev = condition.params.get("elevation")
        threshold = elev if elev is not None else condition.params.get("value", 0)
        position = get_sun_position(self.hass)
        if position is None:
            return False
        return position[1] > threshold if above else position[1] < threshold

    def _eval_temp_threshold(
        self, condition: Condition, *, above: bool, update_state: bool = True
    ) -> bool:
        """Evaluate outdoor temperature above/below threshold.

        Applies a hysteresis deadband around the threshold so a sensor
        hovering at the boundary does not flip the rule on every reading:
        - above: turns true above threshold + h, false below threshold - h
        - below: mirrored

        On first evaluation (no prior state, e.g. after a restart) the hard
        boundary is used -- the band must not bias the initial reading in
        either direction, same as _get_comfort_mode().
        """
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
            threshold = float(threshold)
        except (ValueError, TypeError):
            return False

        return self._threshold_with_hysteresis(
            sensor_id, temp, threshold, above=above, update_state=update_state,
        )

    def _threshold_with_hysteresis(
        self,
        sensor_id: str,
        value: float,
        threshold: float,
        *,
        above: bool,
        update_state: bool,
        hysteresis: float | None = None,
    ) -> bool:
        """Compare value against threshold with a hysteresis deadband.

        State is keyed by (sensor_id, threshold, above) so it survives rule
        edits and is shared by conditions using the identical threshold.
        hysteresis=None falls back to the global setting (degrees) -- callers
        working in other units must pass their own value.
        """
        key = (sensor_id, threshold, above)
        prev = self._threshold_states.get(key)
        h = self.storage.threshold_hysteresis if hysteresis is None else hysteresis

        if prev is None or h <= 0:
            result = value > threshold if above else value < threshold
        elif above:
            result = value > (threshold - h) if prev else value > (threshold + h)
        else:
            result = value < (threshold + h) if prev else value < (threshold - h)

        if update_state:
            self._threshold_states[key] = result
        return result

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

    def _eval_time_before_sun_event(self, condition: Condition, event_fn) -> bool:
        """Evaluate time before sunrise/sunset with offset.

        Returns True while current time is strictly before the (event + offset)
        moment. Mirrors _eval_time_after_sun_event so that
        time_before_sunset offset=-60 means "until 60 min before sunset".
        """
        try:
            offset_minutes = int(condition.params.get("offset", 0))
        except (ValueError, TypeError):
            return False

        event_time = event_fn(self.hass)
        if event_time is None:
            return False

        target_time = event_time + (offset_minutes * 60)
        return dt_util.now().timestamp() < target_time

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

    def _eval_numeric_state(
        self, condition: Condition, *, update_state: bool = True
    ) -> bool:
        """Evaluate numeric_state condition.

        Compares any numeric entity (illuminance, humidity, power, price)
        against a value. Unlike temperature_above/below the deadband is not
        the global degree-based setting -- the sensor's unit is unknown, so
        the buffer comes from the condition itself (0 = off).
        """
        entity_id = condition.params.get("entity_id") or condition.params.get("entity")
        raw_value = condition.params.get("value")
        if not entity_id or raw_value is None:
            return False

        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        try:
            current = float(state.state)
            threshold = float(raw_value)
            hysteresis = float(condition.params.get("hysteresis") or 0)
        except (ValueError, TypeError):
            return False

        above = str(condition.params.get("operator", "above")) != "below"
        return self._threshold_with_hysteresis(
            entity_id, current, threshold,
            above=above, update_state=update_state, hysteresis=hysteresis,
        )

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
        # Panel sends "weather" as string or list, legacy uses "states" list
        weather_val = condition.params.get("weather")
        if isinstance(weather_val, list):
            expected_states = weather_val
        elif weather_val:
            expected_states = [weather_val]
        else:
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

    def _eval_day_of_week(self, condition: Condition) -> bool:
        """Evaluate day_of_week condition."""
        days = condition.params.get("days", [])
        if not days:
            return True  # No restriction = any day
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        today = dt_util.now().weekday()
        return any(day_map.get(d.lower(), -1) == today for d in days)

    def _eval_workday(self, condition: Condition) -> bool:
        """Evaluate workday condition."""
        entity_id = condition.params.get("entity_id") or self.storage.workday_sensor
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown"):
            return False
        expected = condition.params.get("state") or "on"
        return state.state == expected
