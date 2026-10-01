"""Rule evaluation engine for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import time
from time import monotonic
from typing import TYPE_CHECKING, Any

from homeassistant.const import SUN_EVENT_SUNSET
from homeassistant.util import dt as dt_util

from . import ha_condition as hac
from .models import ComfortMode, Condition, ConditionType, CoverConfig, CoverTarget, Rule
from .storage import resolve_active_scenario
from .sun import (
    SUN_EVENT_DUSK,
    get_dawn_time,
    get_dusk_time,
    get_sun_event_time,
    get_sun_position,
    get_sunrise_time,
    get_sunset_time,
    is_sun_on_facade,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)

# How long to keep using the last known comfort mode when the indoor temp
# sensor goes unavailable (e.g. Zigbee bridge restart). Prevents brief sensor
# outages from dropping the shading rule and triggering a fallback movement.
COMFORT_SENSOR_GRACE_PERIOD = 900  # seconds

# Minimum delay before a failed ha_condition compilation is retried (a
# transient failure at startup must recover, a truly invalid one must not be
# recompiled on every refresh).
HA_CONDITION_RETRY_INTERVAL = 60  # seconds

# Age beyond which a remembered hysteresis state (threshold deadband, previous
# comfort mode) is no longer trusted: about 10x the default update interval
# (60 s). A condition that was not evaluated for that long (e.g. its rule was
# skipped, or sun_on_facade short-circuited before the comfort check) starts
# again from the hard boundary instead of a state from hours ago.
HYSTERESIS_STATE_MAX_AGE = 600  # seconds

_UNAVAILABLE_STATES = ("unavailable", "unknown")

_WEATHER_MAP: dict[str, set[str]] = {
    "sunny": {"sunny", "clear", "clear-night"},
    "clear": {"clear", "clear-night"},
    "cloudy": {"cloudy", "fog", "hazy", "overcast", "partlycloudy", "partly-cloudy"},
    "rainy": {"rainy", "pouring", "lightning", "lightning-rainy", "hail"},
    "snowy": {"snowy", "snowy-rainy"},
    "windy": {"windy", "windy-variant", "exceptional"},
}

# Condition types whose result depends on a specific cover/facade context
# (facade azimuth, per-cover comfort range/sensor). They cannot be previewed
# in the rule editor without one and report evaluable=False.
_CONTEXT_DEPENDENT_TYPES: frozenset = frozenset(
    {
        ConditionType.SUN_ON_FACADE,
        ConditionType.TEMPERATURE_COMFORT,
        ConditionType.OUTDOOR_VS_INDOOR,
        ConditionType.ROOM_OCCUPIED,
    }
)

# States meaning "occupied" when a cover sets no explicit list (compared
# case-insensitively): binary sensors, person/device trackers, input_select.
_DEFAULT_OCCUPIED_STATES = frozenset(
    {"on", "home", "present", "présent", "occupied", "occupé", "detected", "true", "1"}
)


class RuleEngine:
    """Evaluate rules and determine cover positions."""

    def __init__(self, hass: HomeAssistant, storage: CoverAutomaticStorage) -> None:
        """Initialize rule engine."""
        self.hass = hass
        self.storage = storage
        self._last_comfort_mode: dict[str, ComfortMode] = {}
        self._last_comfort_read: dict[str, float] = {}
        # Hysteresis state for threshold comparisons, keyed by
        # (sensor_id, threshold, above, hysteresis) so it survives rule edits
        # and is shared only by genuinely identical checks.
        self._threshold_states: dict[tuple[str, float, bool, float], bool] = {}
        # monotonic() of the last update of each _threshold_states entry: an
        # entry older than HYSTERESIS_STATE_MAX_AGE is ignored, then purged.
        self._threshold_stamps: dict[tuple[str, float, bool, float], float] = {}
        self._threshold_purged_at = monotonic()
        # Compiled native HA conditions, keyed by hac.config_key(config)
        self._ha_compiled: dict[str, hac.CompiledCondition] = {}
        # monotonic() of the last failed compilation per key (for retries)
        self._ha_failed_at: dict[str, float] = {}
        # Covers already warned about an invalid comfort range override
        self._comfort_range_warned: set[str] = set()
        # Threshold entities currently unreadable (warned once per outage)
        self._threshold_entity_failed: set[str] = set()
        # Condition errors already logged with a traceback (once each)
        self._condition_errors_logged: set[str] = set()

    def _log_condition_error(self, condition: Condition, err: Exception) -> None:
        """Log a failing condition once with its traceback, then at debug level.

        The same error would otherwise fill the log every cycle for every cover.
        """
        key = f"{condition.type}:{type(err).__name__}:{err}"
        if key in self._condition_errors_logged:
            _LOGGER.debug("Error evaluating condition %s: %s", condition.type, err)
            return
        if len(self._condition_errors_logged) > 200:
            self._condition_errors_logged.clear()
        self._condition_errors_logged.add(key)
        _LOGGER.error("Error evaluating condition %s: %s", condition.type, err, exc_info=True)

    def forget_covers_except(self, keep: set[str]) -> None:
        """Drop per-cover caches of covers that no longer exist."""
        for cache in (self._last_comfort_mode, self._last_comfort_read):
            for entity_id in set(cache) - keep:
                cache.pop(entity_id, None)
        self._comfort_range_warned &= keep

    def _forget_comfort(self, entity_id: str) -> None:
        """No usable comfort mode any more: stop reporting a stale one."""
        self._last_comfort_mode.pop(entity_id, None)
        self._last_comfort_read.pop(entity_id, None)

    def evaluate_cover(
        self, cover: CoverConfig, *, safety_only: bool = False
    ) -> CoverTarget | None:
        """Evaluate rules for a cover and return target position/tilt.

        safety_only=True considers safety rules only (covers that are paused,
        manual, wind protected or with the automation disabled).

        Among matching rules the highest priority wins, ties broken by rule
        id. The safety flag never changes that order: it only lets a rule act
        while the cover is paused/manual/wind protected.

        Returns:
            CoverTarget with position (and optional tilt) or None if no rule matches.
        """
        # Unknown/empty scenario resolves like the select entity (first one)
        active_scenario = resolve_active_scenario(
            self.storage.active_scenario, self.storage.scenarios
        )
        matching_rules: list[tuple[int, str, Rule]] = []

        for rule in self.storage.rules.values():
            if not rule.enabled:
                continue

            if safety_only and not rule.safety:
                continue

            if not self._rule_applies_to_cover(rule, cover):
                continue

            if not self._rule_active_in_scenario(rule, active_scenario):
                continue

            if self._evaluate_conditions(rule, cover):
                matching_rules.append((rule.priority, rule.id, rule))

        if not matching_rules:
            _LOGGER.debug(
                "[%s] No %srule matched", cover.entity_id, "safety " if safety_only else ""
            )
            return None

        # Sort by priority desc, then by rule ID asc for deterministic order
        matching_rules.sort(key=lambda x: (-x[0], x[1]))
        winner = matching_rules[0][2]
        _LOGGER.debug(
            "[%s] Rule '%s' (P%d%s) -> position %d",
            cover.entity_id, winner.name, winner.priority,
            ", safety" if winner.safety else "", winner.target_position,
        )
        return CoverTarget(
            position=winner.target_position,
            tilt_position=winner.target_tilt_position,
            rule_id=winner.id,
            rule_name=winner.name,
            safety=bool(winner.safety),
        )

    # ------------------------------------------------------------------
    # Native Home Assistant conditions
    # ------------------------------------------------------------------

    def ha_compiled(self, condition: Condition) -> hac.CompiledCondition | None:
        """Return the compiled form of an ha_condition (None if not prepared)."""
        return self._ha_compiled.get(hac.config_key(condition.params.get("config")))

    async def async_prepare_ha_conditions(
        self, conditions: list[Condition] | None = None
    ) -> bool:
        """Compile the ha_conditions of all rules (or the given ones).

        Compilation is async in Home Assistant, evaluation is sync: rules are
        compiled here before each update cycle, then evaluated cheaply.
        Unused compiled entries are dropped when preparing all rules.
        Returns True if the set of referenced entities changed.
        """
        before = self.ha_condition_entities()
        if conditions is None:
            conditions = [
                c for rule in self.storage.rules.values() for c in rule.conditions
                if c.type == ConditionType.HA_CONDITION
            ]
            wanted = {hac.config_key(c.params.get("config")) for c in conditions}
            for key in list(self._ha_compiled):
                if key not in wanted:
                    del self._ha_compiled[key]
                    self._ha_failed_at.pop(key, None)
        for cond in conditions:
            if cond.type != ConditionType.HA_CONDITION:
                continue
            # One broken condition must never stop the others from compiling
            try:
                await self._async_prepare_one(cond)
            except Exception as err:  # noqa: BLE001
                config = cond.params.get("config")
                _LOGGER.warning("Cannot compile Home Assistant condition %s: %s", config, err)
                key = hac.config_key(config)
                self._ha_compiled[key] = hac.CompiledCondition(
                    error=str(err), error_code="invalid"
                )
                self._ha_failed_at[key] = monotonic()
        return self.ha_condition_entities() != before

    async def _async_prepare_one(self, cond: Condition) -> None:
        """Compile one ha_condition (or refresh its template entities)."""
        config = cond.params.get("config")
        key = hac.config_key(config)
        compiled = self._ha_compiled.get(key)
        if compiled is not None:
            failed_at = self._ha_failed_at.get(key)
            if failed_at is None:
                # Valid: templates may reference other entities now (e.g.
                # {{ states(states('input_text.x')) }}), re-read them so the
                # coordinator listens to the right entities.
                hac.refresh_template_entities(self.hass, compiled)
                return
            # Failed compilations are retried after a delay (the failed
            # entry stays cached meanwhile so the panel sees the error).
            if monotonic() - failed_at < HA_CONDITION_RETRY_INTERVAL:
                return
        compiled = await hac.async_compile(self.hass, config)
        if compiled.error:
            _LOGGER.debug("Invalid Home Assistant condition %s: %s", config, compiled.error)
            self._ha_failed_at[key] = monotonic()
        else:
            self._ha_failed_at.pop(key, None)
        self._ha_compiled[key] = compiled

    def ha_condition_entities(self) -> set[str]:
        """Entities referenced by the compiled Home Assistant conditions."""
        entities: set[str] = set()
        for compiled in self._ha_compiled.values():
            entities |= compiled.entities
        return entities

    def ha_condition_status(self, condition: Condition) -> dict[str, Any] | None:
        """Validation status of an ha_condition for the panel."""
        if condition.type != ConditionType.HA_CONDITION:
            return None
        compiled = self.ha_compiled(condition)
        if compiled is None:
            return {"valid": False, "error": None, "error_code": "pending"}
        return {
            "valid": compiled.valid,
            "error": compiled.error,
            "error_code": compiled.error_code,
        }

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

        A rule is active in a scenario when it belongs to it (its
        scenario_ids) and is not switched off in the scenario's
        rules_disabled list.
        """
        scenario = self.storage.scenarios.get(scenario_id)
        if scenario is None:
            return True
        # The rule must belong to the scenario (None = all scenarios) ...
        if rule.scenario_ids is not None and scenario_id not in rule.scenario_ids:
            return False
        # ... and not be switched off inside it
        return rule.id not in scenario.rules_disabled

    def _evaluate_conditions(self, rule: Rule, cover: CoverConfig) -> bool:
        """Evaluate all conditions of a rule.

        Conditions are organised in groups. Inside a group they are combined
        with the group's operator (group_operators), the groups themselves
        with the rule's condition_operator -- e.g. (A or B) and (C or D).
        With a single group only its own operator applies. Empty groups are
        ignored; a condition can be negated (NOT).
        """
        groups = rule.condition_groups()
        if not groups:
            return True

        # Evaluate every condition first (no short-circuit) so the
        # hysteresis state of each threshold condition stays current.
        evaluated = [
            (op, [self._evaluate_final(c, cover) for c in members])
            for op, members in groups
        ]

        def group_result(op: str, results: list[bool]) -> bool:
            return any(results) if op == "or" else all(results)

        if len(evaluated) == 1:
            return group_result(*evaluated[0])
        group_results = [group_result(op, results) for op, results in evaluated]
        return any(group_results) if rule.condition_operator == "or" else all(group_results)

    def _evaluate_final(
        self, condition: Condition, cover: CoverConfig | None, *, update_state: bool = True
    ) -> bool:
        """Evaluate a condition including its NOT flag.

        A negated condition is only met when its input is actually known:
        an unavailable sensor must not turn "NOT rain" into "met".
        """
        if not condition.negate:
            return self._evaluate_condition(condition, cover, update_state=update_state)  # type: ignore[arg-type]
        return self._evaluate_tristate(condition, cover, update_state=update_state) is False

    def _evaluate_tristate(
        self, condition: Condition, cover: CoverConfig | None, *, update_state: bool = True
    ) -> bool | None:
        """Evaluate a condition (without NOT): True/False, or None when unknown.

        Unknown = the input cannot be read, the condition is misconfigured
        (missing or non-numeric threshold/offset), the evaluation raised, or
        the native HA condition failed to evaluate.
        """
        if condition.type == ConditionType.HA_CONDITION:
            return hac.evaluate_tristate(self.hass, self.ha_compiled(condition))
        if not self._params_valid(condition):
            _LOGGER.debug("Condition %s misconfigured: %s", condition.type, condition.params)
            return None
        try:
            result = self._dispatch_condition(condition, cover, update_state=update_state)  # type: ignore[arg-type]
        except Exception as err:  # noqa: BLE001
            self._log_condition_error(condition, err)
            return None
        if not self._input_available(condition, cover):
            return None
        return result

    @staticmethod
    def _params_valid(condition: Condition) -> bool:
        """Whether a condition's own parameters can be evaluated.

        The evaluators return False on invalid parameters; for a negated
        condition that would read as "met", so _evaluate_tristate reports
        such a condition as unknown instead (NOT is then not met either).
        Mirrors the parsing done by the evaluators.
        """
        params = condition.params

        def is_number(value: Any) -> bool:
            try:
                float(value)
            except (TypeError, ValueError):
                return False
            return True

        match condition.type:
            case ConditionType.NUMERIC_STATE:
                return is_number(params.get("value")) and is_number(
                    params.get("hysteresis") or 0
                )
            case ConditionType.TEMPERATURE_ABOVE | ConditionType.TEMPERATURE_BELOW:
                temp = params.get("temperature")
                return is_number(temp if temp is not None else params.get("value", 0))
            case ConditionType.SUN_ELEVATION_ABOVE | ConditionType.SUN_ELEVATION_BELOW:
                elev = params.get("elevation")
                return is_number(elev if elev is not None else params.get("value", 0))
            case (
                ConditionType.TIME_AFTER_SUNRISE | ConditionType.TIME_BEFORE_SUNRISE
                | ConditionType.TIME_AFTER_SUNSET | ConditionType.TIME_BEFORE_SUNSET
                | ConditionType.TIME_AFTER_DAWN | ConditionType.TIME_BEFORE_DAWN
                | ConditionType.TIME_AFTER_DUSK | ConditionType.TIME_BEFORE_DUSK
            ):
                try:
                    int(params.get("offset", 0))
                except (TypeError, ValueError):
                    return False
                return True
            case ConditionType.STATE_IS:
                return params.get("state") is not None
            case _:
                return True

    def _input_available(self, condition: Condition, cover: CoverConfig | None) -> bool:
        """Whether the value a condition reads is currently known."""
        params = condition.params
        match condition.type:
            case ConditionType.STATE_IS:
                entity_id = params.get("entity_id") or params.get("entity")
                if not entity_id:
                    return False
                if str(params.get("state")) in _UNAVAILABLE_STATES:
                    # Checking for "unavailable" itself: any existing state is known
                    return self.hass.states.get(entity_id) is not None
                return self._read_state(entity_id) is not None
            case ConditionType.NUMERIC_STATE:
                entity_id = params.get("entity_id") or params.get("entity")
                return self._read_float_state(entity_id) is not None
            case ConditionType.TEMPERATURE_ABOVE | ConditionType.TEMPERATURE_BELOW:
                sensor_id = params.get("sensor") or self.storage.outdoor_temp_sensor
                return self._read_float_state(sensor_id) is not None
            case ConditionType.WEATHER_IS:
                return self._read_state(params.get("entity") or self.storage.weather_entity) is not None
            case ConditionType.WORKDAY:
                return self._read_state(params.get("entity_id") or self.storage.workday_sensor) is not None
            case ConditionType.TEMPERATURE_COMFORT:
                return cover is not None and self._comfort_known(cover)
            case ConditionType.OUTDOOR_VS_INDOOR:
                return cover is not None and all(
                    self._read_float_state(s) is not None
                    for s in self._outdoor_indoor_sensors(cover)
                )
            case ConditionType.ROOM_OCCUPIED:
                sensor = cover.occupancy_sensor if cover is not None else None
                return not sensor or self._read_state(sensor) is not None
            case ConditionType.SUN_ON_FACADE:
                return self._sun_on_facade_known(condition, cover)
            case ConditionType.SUN_ELEVATION_ABOVE | ConditionType.SUN_ELEVATION_BELOW:
                return get_sun_position(self.hass) is not None
            case ConditionType.TIME_BEFORE_SUNRISE:
                return get_sunrise_time(self.hass) is not None
            case ConditionType.TIME_AFTER_SUNSET:
                return get_sunset_time(self.hass) is not None
            case ConditionType.TIME_BEFORE_DAWN:
                return get_dawn_time(self.hass) is not None
            case ConditionType.TIME_AFTER_DUSK:
                return get_dusk_time(self.hass) is not None
            # Daytime windows need both of today's events
            case ConditionType.TIME_AFTER_SUNRISE | ConditionType.TIME_BEFORE_SUNSET:
                return (
                    get_sunrise_time(self.hass) is not None
                    and get_sunset_time(self.hass) is not None
                )
            case ConditionType.TIME_AFTER_DAWN | ConditionType.TIME_BEFORE_DUSK:
                return (
                    get_dawn_time(self.hass) is not None
                    and get_dusk_time(self.hass) is not None
                )
            case ConditionType.HA_CONDITION:
                compiled = self.ha_compiled(condition)
                return compiled is not None and compiled.checker is not None
            case _:
                return True

    def _sun_on_facade_known(self, condition: Condition, cover: CoverConfig | None) -> bool:
        """Whether sun_on_facade can be decided (mirrors _eval_sun_on_facade)."""
        if cover is None or get_sun_position(self.hass) is None:
            return False
        facade_id = condition.params.get("facade") or cover.facade_id
        facade = self.storage.facades.get(facade_id) if facade_id else None
        if not facade:
            return False
        # The comfort mode only matters while the sun is on the facade
        if not self._sun_uses_comfort(cover):
            return True
        if not is_sun_on_facade(self.hass, facade):
            return True
        if not self._comfort_known(cover):
            return False
        # Neutral mode with preemptive shading: the answer depends on the
        # solar sensor, unknown while it cannot be read.
        _, neutral_ignore, preemptive = self._sun_flags(cover)
        if (
            neutral_ignore
            and preemptive
            and self._last_comfort_mode.get(cover.entity_id) == ComfortMode.NEUTRAL
        ):
            return self._solar_known()
        return True

    def _solar_known(self) -> bool:
        """Whether the preemptive-shading solar check can be decided."""
        sensor_id = self.storage.solar_sensor
        if not sensor_id or self.effective_solar_threshold() <= 0:
            return True  # no sensor: preemptive shading simply never applies
        return self._read_float_state(sensor_id) is not None

    def _sun_flags(self, cover: CoverConfig) -> tuple[bool, bool, bool]:
        """Effective (heating_ignore, neutral_ignore, preemptive) for a cover.

        A per-cover value overrides the global setting when not None.
        """
        def pick(own: bool | None, default: bool) -> bool:
            return default if own is None else bool(own)

        return (
            pick(cover.sun_heating_ignore, self.storage.sun_heating_ignore),
            pick(cover.sun_neutral_ignore, self.storage.sun_neutral_ignore),
            pick(cover.preemptive_shading, self.storage.preemptive_shading),
        )

    def _sun_uses_comfort(self, cover: CoverConfig) -> bool:
        """Whether sun_on_facade depends on the comfort mode for this cover.

        Needs an indoor sensor and at least one active ignore switch;
        otherwise only the sun position counts.
        """
        if not (cover.indoor_temp_sensor or self.storage.indoor_temp_sensor):
            return False
        heating_ignore, neutral_ignore, _ = self._sun_flags(cover)
        return heating_ignore or neutral_ignore

    def _comfort_known(self, cover: CoverConfig) -> bool:
        """Whether a comfort mode is known (sensor readable or held in grace)."""
        sensor_id = cover.indoor_temp_sensor or self.storage.indoor_temp_sensor
        if not sensor_id:
            return False
        if self._read_float_state(sensor_id) is not None:
            return True
        prev = self._last_comfort_mode.get(cover.entity_id)
        last_read = self._last_comfort_read.get(cover.entity_id)
        return (
            prev is not None
            and last_read is not None
            and monotonic() - last_read < COMFORT_SENSOR_GRACE_PERIOD
        )

    def _evaluate_condition(
        self, condition: Condition, cover: CoverConfig, *, update_state: bool = True
    ) -> bool:
        """Evaluate a single condition.

        update_state=False keeps threshold hysteresis state untouched, so the
        rule editor's live preview cannot shift the runtime deadband.
        Errors count as not met.
        """
        try:
            return self._dispatch_condition(condition, cover, update_state=update_state)
        except Exception as err:  # noqa: BLE001
            self._log_condition_error(condition, err)
            return False

    def _dispatch_condition(
        self, condition: Condition, cover: CoverConfig, *, update_state: bool = True
    ) -> bool:
        """Run the evaluator of a condition type (may raise)."""
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
                return self._eval_time_after_morning_event(
                    condition, get_sunrise_time, get_sunset_time,
                    ConditionType.TIME_AFTER_SUNSET,
                )
            case ConditionType.TIME_AFTER_SUNSET:
                return self._eval_time_after_sunset(condition)
            case ConditionType.TIME_BEFORE_SUNRISE:
                return self._eval_time_before_morning_event(
                    condition, get_sunrise_time, get_sunset_time
                )
            case ConditionType.TIME_BEFORE_SUNSET:
                return self._eval_time_before_evening_event(
                    condition, get_sunset_time, get_sunrise_time,
                    ConditionType.TIME_BEFORE_SUNRISE,
                )
            case ConditionType.TIME_AFTER_DAWN:
                return self._eval_time_after_morning_event(
                    condition, get_dawn_time, get_dusk_time,
                    ConditionType.TIME_AFTER_DUSK,
                )
            case ConditionType.TIME_BEFORE_DAWN:
                return self._eval_time_before_morning_event(
                    condition, get_dawn_time, get_dusk_time
                )
            case ConditionType.TIME_AFTER_DUSK:
                return self._eval_time_after_dusk(condition)
            case ConditionType.TIME_BEFORE_DUSK:
                return self._eval_time_before_evening_event(
                    condition, get_dusk_time, get_dawn_time,
                    ConditionType.TIME_BEFORE_DAWN,
                )
            case ConditionType.STATE_IS:
                return self._eval_state_is(condition)
            case ConditionType.NUMERIC_STATE:
                return self._eval_numeric_state(
                    condition, update_state=update_state
                )
            case ConditionType.TEMPERATURE_COMFORT:
                return self._eval_temp_comfort(condition, cover)
            case ConditionType.OUTDOOR_VS_INDOOR:
                return self._eval_outdoor_vs_indoor(
                    condition, cover, update_state=update_state
                )
            case ConditionType.ROOM_OCCUPIED:
                return self._eval_room_occupied(cover)
            case ConditionType.WEATHER_IS:
                return self._eval_weather_is(condition)
            case ConditionType.DAY_OF_WEEK:
                return self._eval_day_of_week(condition)
            case ConditionType.WORKDAY:
                return self._eval_workday(condition)
            case ConditionType.HA_CONDITION:
                return hac.evaluate(self.hass, self.ha_compiled(condition))
            case _:
                _LOGGER.warning("Unknown condition type: %s", condition.type)
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
            matched = self._evaluate_final(condition, None, update_state=False)
            actual, kind = self._preview_actual(condition)
            return {"evaluable": True, "matched": matched, "actual": actual, "kind": kind}
        except Exception as err:  # defensive: preview must never raise
            _LOGGER.debug("preview_condition(%s) failed: %s", condition.type, err)
            return {"evaluable": True, "matched": False, "actual": None, "kind": None}

    def _preview_actual(self, condition: Condition) -> tuple[Any, str | None]:
        """Return (actual_value, kind) for a global condition's current reading."""
        t = condition.type
        if t == ConditionType.HA_CONDITION:
            reading = hac.simple_reading(self.hass, condition.params.get("config"))
            return reading, ("ha_reading" if reading else None)
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
            ConditionType.TIME_AFTER_DAWN, ConditionType.TIME_BEFORE_DAWN,
            ConditionType.TIME_AFTER_DUSK, ConditionType.TIME_BEFORE_DUSK,
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
        value = condition.type.value
        if "dawn" in value:
            event_fn = get_dawn_time
        elif "dusk" in value:
            event_fn = get_dusk_time
        elif "sunrise" in value:
            event_fn = get_sunrise_time
        else:
            event_fn = get_sunset_time
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

        Considers the indoor comfort mode when a sensor is configured
        (per-cover > global fallback) and an ignore switch is active
        (sun_heating_ignore / sun_neutral_ignore, per-cover > global):
        COOLING -> True; HEATING -> not heating_ignore; NEUTRAL -> True
        unless neutral_ignore, then preemptive shading with solar above
        threshold. With both switches off only the sun position counts.
        When the sensor is unavailable, the last known comfort mode is held
        for COMFORT_SENSOR_GRACE_PERIOD; beyond that (or without a prior
        reading) returns False (wait for reliable data before acting).
        """
        facade_id = condition.params.get("facade") or cover.facade_id
        if not facade_id:
            return False

        facade = self.storage.facades.get(facade_id)
        if not facade:
            return False

        if not is_sun_on_facade(self.hass, facade):
            return False

        # Comfort check (indoor sensor + at least one ignore switch active)
        if not self._sun_uses_comfort(cover):
            return True
        heating_ignore, neutral_ignore, preemptive = self._sun_flags(cover)
        comfort_mode = self._get_comfort_mode(cover)
        if comfort_mode is None:
            _LOGGER.debug(
                "[%s] sun_on_facade: sensor unavailable, deferring",
                cover.entity_id,
            )
            return False
        if comfort_mode == ComfortMode.COOLING:
            return True
        if comfort_mode == ComfortMode.HEATING:
            if not heating_ignore:
                return True
        elif not neutral_ignore:
            return True
        elif preemptive and self._check_solar_intensity():
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

    def _get_comfort_mode(self, cover: CoverConfig) -> ComfortMode | None:
        """Determine comfort mode from indoor temperature sensor.

        Applies hysteresis to prevent oscillation at threshold boundaries:
        - Exit HEATING only when temp >= comfort_min + hysteresis
        - Exit COOLING only when temp <= comfort_max - hysteresis

        When the sensor goes unavailable, the last known mode is held for
        COMFORT_SENSOR_GRACE_PERIOD so brief outages (e.g. Zigbee bridge
        restart) do not drop active rules. Returns None if no sensor is
        configured, or unavailable beyond the grace period.

        The previous mode only feeds the hysteresis when it was computed
        less than HYSTERESIS_STATE_MAX_AGE ago; otherwise the hard
        boundaries decide, as on the first evaluation.
        """
        sensor_id = cover.indoor_temp_sensor or self.storage.indoor_temp_sensor
        if not sensor_id:
            self._forget_comfort(cover.entity_id)
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
            self._forget_comfort(cover.entity_id)
            return None

        now = monotonic()
        last_read = self._last_comfort_read.get(cover.entity_id)
        prev = self._last_comfort_mode.get(cover.entity_id)
        if last_read is None or now - last_read > HYSTERESIS_STATE_MAX_AGE:
            # Not evaluated for a while (e.g. sun_on_facade stops before the
            # comfort check while the sun is off the facade): a mode from
            # hours ago must not bias the bands, use the hard boundaries.
            prev = None
        self._last_comfort_read[cover.entity_id] = now
        h = self.storage.comfort_hysteresis
        comfort_min, comfort_max = self._comfort_range(cover)
        if comfort_min >= comfort_max:
            _LOGGER.warning("[%s] comfort_min (%.1f) >= comfort_max (%.1f)", cover.entity_id, comfort_min, comfort_max)
            self._forget_comfort(cover.entity_id)
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

    def _setting_entity(self, key: str) -> str | None:
        """Return a global entity id setting (None when unset)."""
        value = getattr(self.storage, key, None)
        return value if isinstance(value, str) and value else None

    def _read_threshold_entity(self, entity_id: str, fallback: Any) -> float | None:
        """Numeric value of a threshold entity, None when not readable.

        Logs once when the entity becomes unreadable (and once when it
        recovers), not on every evaluation.
        """
        state = self.hass.states.get(entity_id)
        value: float | None = None
        if state is not None and state.state not in _UNAVAILABLE_STATES:
            try:
                value = float(state.state)
            except (ValueError, TypeError):
                value = None
            if value is not None and (value != value or abs(value) == float("inf")):
                value = None
        if value is None:
            if entity_id not in self._threshold_entity_failed:
                self._threshold_entity_failed.add(entity_id)
                _LOGGER.warning(
                    "Threshold entity %s is unavailable or not numeric (%s), using %s",
                    entity_id, state.state if state is not None else "missing",
                    fallback if fallback is not None else "the next fallback",
                )
            return None
        if entity_id in self._threshold_entity_failed:
            self._threshold_entity_failed.discard(entity_id)
            _LOGGER.info("Threshold entity %s is readable again (%s)", entity_id, value)
        return value

    def _threshold_level(self, entity_id: str | None, number: Any) -> Any:
        """Value of one threshold level: the entity when readable, else the number."""
        if entity_id:
            value = self._read_threshold_entity(entity_id, number)
            if value is not None:
                return value
        return number

    def effective_solar_threshold(self) -> float:
        """Solar threshold: entity value when readable, else the static number."""
        return float(self._threshold_level(
            self._setting_entity("solar_threshold_entity"), self.storage.solar_threshold
        ))

    def _global_comfort_range(self) -> tuple[float, float]:
        """Global comfort range (entities override the static numbers).

        An invalid pair coming from entities falls back to the static numbers,
        which the API keeps valid.
        """
        static_min = self.storage.comfort_temp_min
        static_max = self.storage.comfort_temp_max
        global_min = self._threshold_level(
            self._setting_entity("comfort_temp_min_entity"), static_min
        )
        global_max = self._threshold_level(
            self._setting_entity("comfort_temp_max_entity"), static_max
        )
        if global_min >= global_max and (global_min, global_max) != (static_min, static_max):
            if "__global__" not in self._comfort_range_warned:
                self._comfort_range_warned.add("__global__")
                _LOGGER.warning(
                    "Invalid comfort range %.1f-%.1f from entities, using %.1f-%.1f",
                    global_min, global_max, static_min, static_max,
                )
            return static_min, static_max
        self._comfort_range_warned.discard("__global__")
        return global_min, global_max

    def _comfort_range(self, cover: CoverConfig) -> tuple[float, float]:
        """Effective comfort range of a cover.

        Per level (cover, then global) a readable entity wins over the
        number. A per-cover override mixed with a changed global value can
        produce min >= max; the global pair is then used instead of
        disabling comfort.
        """
        global_min, global_max = self._global_comfort_range()
        comfort_min = self._threshold_level(
            getattr(cover, "comfort_temp_min_entity", None), cover.comfort_temp_min
        )
        comfort_max = self._threshold_level(
            getattr(cover, "comfort_temp_max_entity", None), cover.comfort_temp_max
        )
        if comfort_min is None:
            comfort_min = global_min
        if comfort_max is None:
            comfort_max = global_max
        if comfort_min < comfort_max:
            self._comfort_range_warned.discard(cover.entity_id)
            return comfort_min, comfort_max
        if (comfort_min, comfort_max) != (global_min, global_max):
            if cover.entity_id not in self._comfort_range_warned:
                self._comfort_range_warned.add(cover.entity_id)
                _LOGGER.warning(
                    "[%s] Invalid comfort range %.1f-%.1f, using global range %.1f-%.1f",
                    cover.entity_id, comfort_min, comfort_max, global_min, global_max,
                )
            return global_min, global_max
        return comfort_min, comfort_max

    def _check_solar_intensity(self, *, update_state: bool = True) -> bool:
        """Check if solar intensity exceeds threshold for preemptive shading.

        Applies solar_hysteresis as a deadband so a sensor drifting around the
        threshold does not drop sun_on_facade on every reading. The buffer is
        a separate setting because the sensor's unit is unknown (lx, W/m2),
        which rules out the degree-based global threshold_hysteresis.
        """
        sensor_id = self.storage.solar_sensor
        if not sensor_id:
            return False
        threshold_entity = self._setting_entity("solar_threshold_entity")
        threshold = self.effective_solar_threshold()
        if threshold <= 0:
            return False
        state = self.hass.states.get(sensor_id)
        if state is None or state.state in ("unavailable", "unknown"):
            return False
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return False
        return self._threshold_with_hysteresis(
            sensor_id, value, float(threshold),
            above=True, update_state=update_state,
            hysteresis=self._solar_hysteresis(float(threshold)),
            # A threshold read from an entity may change: keep one state
            # instead of a new entry (and lost hysteresis) per value.
            state_key=(
                (f"{sensor_id}|{threshold_entity}", 0.0, True, self.storage.solar_hysteresis)
                if threshold_entity else None
            ),
        )

    def _solar_hysteresis(self, threshold: float) -> float:
        """Solar deadband, bounded so the shading can be released again.

        The sensor never reads below 0, so a buffer >= threshold would put the
        release point (threshold - h) at or below 0: once on, preemptive
        shading would never turn off. Such a buffer is clamped to half the
        threshold.
        """
        h = self.storage.solar_hysteresis
        if threshold > 0 and h >= threshold:
            return threshold / 2
        return h

    def _eval_sun_elevation(self, condition: Condition, *, above: bool) -> bool:
        """Evaluate sun elevation above/below threshold."""
        elev = condition.params.get("elevation")
        threshold = elev if elev is not None else condition.params.get("value", 0)
        try:
            threshold = float(threshold)
        except (ValueError, TypeError):
            return False
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
        state_key: tuple[str, float, bool, float] | None = None,
    ) -> bool:
        """Compare value against threshold with a hysteresis deadband.

        State is keyed by (sensor_id, threshold, above, h) so it survives rule
        edits and is shared by conditions that are truly identical. The buffer
        belongs in the key: the same entity may back both solar_sensor and a
        numeric_state condition on the same threshold but with different
        buffers, and a shared bool would let them overwrite each other.
        hysteresis=None falls back to the global setting (degrees) -- callers
        working in other units must pass their own value.

        A state older than HYSTERESIS_STATE_MAX_AGE (the condition was not
        evaluated for a while) is ignored like a missing one: the hard
        boundary decides, not a result remembered from hours ago.
        """
        h = self.storage.threshold_hysteresis if hysteresis is None else hysteresis
        key = state_key or (sensor_id, threshold, above, h)
        now = monotonic()
        prev = self._threshold_states.get(key)
        if prev is not None and now - self._threshold_stamps.get(key, 0.0) > HYSTERESIS_STATE_MAX_AGE:
            prev = None

        if prev is None or h <= 0:
            result = value > threshold if above else value < threshold
        elif above:
            result = value > (threshold - h) if prev else value > (threshold + h)
        else:
            result = value < (threshold + h) if prev else value < (threshold - h)

        if update_state:
            self._threshold_states[key] = result
            self._threshold_stamps[key] = now
            self._purge_threshold_states(now)
        return result

    def _purge_threshold_states(self, now: float) -> None:
        """Drop expired hysteresis states (at most once per max age)."""
        if now - self._threshold_purged_at < HYSTERESIS_STATE_MAX_AGE:
            return
        self._threshold_purged_at = now
        for key in list(self._threshold_states):
            if now - self._threshold_stamps.get(key, 0.0) > HYSTERESIS_STATE_MAX_AGE:
                self._threshold_states.pop(key, None)
                self._threshold_stamps.pop(key, None)

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

        # Same start and end (HH:MM) means all day
        if (start_time.hour, start_time.minute) == (end_time.hour, end_time.minute):
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

    def _eval_time_after_sunset(self, condition: Condition) -> bool:
        """Evaluate time_after_sunset: true from (sunset + offset) until sunrise.

        Comparing against today's sunset only made the condition turn false
        at midnight, so a night rule stopped matching (and a lower-priority
        rule could take over) in the middle of the night. After midnight the
        condition now stays true until today's sunrise as long as yesterday's
        sunset + offset has passed.
        """
        if self._eval_time_after_sun_event(condition, get_sunset_time):
            return True
        try:
            offset_minutes = int(condition.params.get("offset", 0))
        except (ValueError, TypeError):
            return False
        sunrise = get_sunrise_time(self.hass)
        yesterday_sunset = get_sun_event_time(self.hass, SUN_EVENT_SUNSET, -1)
        if sunrise is None or yesterday_sunset is None:
            return False
        now = dt_util.now().timestamp()
        return yesterday_sunset + offset_minutes * 60 <= now < sunrise

    def _eval_time_after_dusk(self, condition: Condition) -> bool:
        """Evaluate time_after_dusk: true from (dusk + offset) until dawn.

        Same night-spanning semantics as time_after_sunset: after midnight it
        stays true until today's dawn when yesterday's dusk + offset passed.
        """
        if self._eval_time_after_sun_event(condition, get_dusk_time):
            return True
        try:
            offset_minutes = int(condition.params.get("offset", 0))
        except (ValueError, TypeError):
            return False
        dawn = get_dawn_time(self.hass)
        yesterday_dusk = get_sun_event_time(self.hass, SUN_EVENT_DUSK, -1)
        if dawn is None or yesterday_dusk is None:
            return False
        now = dt_util.now().timestamp()
        return yesterday_dusk + offset_minutes * 60 <= now < dawn

    def _eval_time_before_morning_event(
        self, condition: Condition, morning_fn, evening_fn
    ) -> bool:
        """time_before_sunrise / time_before_dawn, spanning the night.

        Mirror of time_after_sunset / time_after_dusk: true from the evening
        event (sunset / dusk) until the next morning event + offset, not only
        between midnight and the morning event.
        """
        if self._eval_time_before_sun_event(condition, morning_fn):
            return True
        evening = evening_fn(self.hass)
        return evening is not None and dt_util.now().timestamp() >= evening

    def _configured_offsets(self, condition_type: ConditionType) -> list[int]:
        """Offsets (minutes) of the conditions of this type in the enabled rules.

        Read from storage on each call (a few rules, cheap): always in step
        with the configured rules.
        """
        offsets: list[int] = []
        for rule in self.storage.rules.values():
            if not rule.enabled:
                continue
            for cond in rule.conditions:
                if cond.type != condition_type:
                    continue
                try:
                    offsets.append(int(cond.params.get("offset", 0)))
                except (TypeError, ValueError):
                    continue
        return offsets

    def _eval_time_after_morning_event(
        self, condition: Condition, morning_fn, evening_fn,
        closing_type: ConditionType,
    ) -> bool:
        """time_after_sunrise / time_after_dawn: a daytime window.

        True from (today's morning event + offset) until today's evening
        event (sunset / dusk) EXTENDED by the largest positive offset of the
        night condition taking over (closing_type: time_after_sunset /
        time_after_dusk) in the enabled rules. Without it, a closing rule
        "after dusk +15" left 15 minutes where neither matched and a
        low-priority fallback rule won. Without positive offsets it ends at
        the evening event: the exact complement of time_before_sunrise /
        time_before_dawn. Staying true until midnight overlapped the night
        conditions in the evening. Unknown events (polar day/night) give
        False, reported as unknown for NOT.
        """
        if not self._eval_time_after_sun_event(condition, morning_fn):
            return False
        evening = evening_fn(self.hass)
        if evening is None:
            return False
        extension = max([0, *self._configured_offsets(closing_type)])
        return dt_util.now().timestamp() < evening + extension * 60

    def _eval_time_before_evening_event(
        self, condition: Condition, evening_fn, morning_fn,
        night_type: ConditionType,
    ) -> bool:
        """time_before_sunset / time_before_dusk: a daytime window.

        True from today's morning event (sunrise / dawn) until (today's
        evening event + offset). The start is brought FORWARD by the largest
        negative offset of the night condition ending in the morning
        (night_type: time_before_sunrise / time_before_dawn) in the enabled
        rules, so "before sunrise -15" followed by this condition leaves no
        gap. Without negative offsets it starts at the morning event: the
        exact complement of time_after_sunset / time_after_dusk. Being true
        from midnight overlapped the night conditions before sunrise.
        Unknown events (polar day/night) give False, reported as unknown
        for NOT.
        """
        if not self._eval_time_before_sun_event(condition, evening_fn):
            return False
        morning = morning_fn(self.hass)
        if morning is None:
            return False
        lead = -min([0, *self._configured_offsets(night_type)])
        return dt_util.now().timestamp() >= morning - lead * 60

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

    def _outdoor_indoor_sensors(self, cover: CoverConfig) -> tuple[str | None, str | None]:
        """(outdoor sensor, indoor sensor of the cover's room)."""
        return (
            self.storage.outdoor_temp_sensor,
            cover.indoor_temp_sensor or self.storage.indoor_temp_sensor,
        )

    def _eval_outdoor_vs_indoor(
        self, condition: Condition, cover: CoverConfig | None, *, update_state: bool = True
    ) -> bool:
        """Outdoor air warmer/cooler than the cover's room.

        operator "warmer": outdoor > indoor + delta; "cooler": outdoor <
        indoor - delta. The rule temperature hysteresis applies to the
        difference, so two sensors a few tenths apart do not flip the rule
        on every reading. False when a temperature cannot be read.
        """
        if cover is None:
            return False
        outdoor_id, indoor_id = self._outdoor_indoor_sensors(cover)
        outdoor = self._read_float_state(outdoor_id)
        indoor = self._read_float_state(indoor_id)
        if outdoor is None or indoor is None:
            return False
        try:
            delta = abs(float(condition.params.get("delta") or 0))
        except (TypeError, ValueError):
            delta = 0.0
        warmer = str(condition.params.get("operator", "cooler")) == "warmer"
        threshold = delta if warmer else -delta
        h = self.storage.threshold_hysteresis
        return self._threshold_with_hysteresis(
            f"{outdoor_id}|{indoor_id}", round(outdoor - indoor, 1), threshold,
            above=warmer, update_state=update_state,
            state_key=(f"ovi|{outdoor_id}|{indoor_id}", threshold, warmer, h),
        )

    def _eval_room_occupied(self, cover: CoverConfig | None) -> bool:
        """The cover's room is occupied according to its occupancy sensor.

        No sensor: never occupied. Unavailable sensor: False, and the input
        is reported unknown so "NOT occupied" is not met either (the cover
        does not open onto a possibly occupied room).
        """
        sensor = cover.occupancy_sensor if cover is not None else None
        if not sensor:
            return False
        state = self._read_state(sensor)
        if state is None:
            return False
        if cover.occupancy_states:
            occupied = {s.strip().casefold() for s in cover.occupancy_states.split(",") if s.strip()}
        else:
            occupied = _DEFAULT_OCCUPIED_STATES
        return state.strip().casefold() in occupied

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
