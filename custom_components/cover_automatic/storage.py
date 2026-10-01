"""Storage manager for CoverAutomatic."""
from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Callable, Collection
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.core import valid_entity_id
from homeassistant.helpers.storage import Store

from homeassistant.util import dt as dt_util

from .const import LOG_RETENTION_DAYS, LOG_STORAGE_KEY, STORAGE_KEY, STORAGE_VERSION
from .models import (
    Condition,
    CoverConfig,
    Facade,
    Rule,
    Scenario,
    _opt_bool,
    _to_bool,
    _to_float,
    _to_int,
    finite_range,
    int_range,
    optional_entity_id,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Debounce delay for runtime saves (seconds)
SAVE_DEBOUNCE_DELAY = 2.0

# Required top-level keys for import validation
_REQUIRED_DICT_KEYS = ("facades", "covers", "rules", "scenarios")

# Every global setting: exported with its effective value, restored on import.
GLOBAL_SETTING_KEYS = (
        "enabled",
        "outdoor_temp_sensor",
        "indoor_temp_sensor",
        "weather_entity",
        "comfort_temp_min",
        "comfort_temp_max",
        "comfort_hysteresis",
        "threshold_hysteresis",
        "pause_duration",
        "lock_position",
        "vent_position",
        "lock_tilt_position",
        "vent_tilt_position",
        "min_position_change",
        "min_time_between_changes",
        "house_rotation",
        "workday_sensor",
        "wind_sensor",
        "wind_speed_threshold",
        "wind_speed_hysteresis",
        "solar_sensor",
        "solar_threshold",
        "solar_hysteresis",
        "command_stagger",
        "logbook_enabled",
        "update_check_enabled",
        "default_travel_time",
        "wind_position",
        "solar_threshold_entity",
        "comfort_temp_min_entity",
        "comfort_temp_max_entity",
        "sun_heating_ignore",
        "sun_neutral_ignore",
        "preemptive_shading",
        "temp_color_thermometer",
        "pause_resume_on_match",
)
# Value types of the global settings, checked on import (a hand-edited
# file may hold "false" or "15" as text).
_BOOL_SETTINGS = frozenset({
    "enabled", "logbook_enabled", "update_check_enabled",
    "sun_heating_ignore", "sun_neutral_ignore", "preemptive_shading",
    "temp_color_thermometer", "pause_resume_on_match",
})
_INT_SETTINGS = frozenset({
    "pause_duration", "lock_position", "vent_position", "lock_tilt_position",
    "vent_tilt_position", "min_position_change", "min_time_between_changes",
    "default_travel_time", "wind_position",
})
_FLOAT_SETTINGS = frozenset({
    "comfort_temp_min", "comfort_temp_max", "comfort_hysteresis",
    "threshold_hysteresis", "house_rotation", "wind_speed_threshold",
    "wind_speed_hysteresis", "solar_threshold", "solar_hysteresis", "command_stagger",
})

# Accepted values of every global setting: shared by the settings/update
# WebSocket command and the import, so both apply the same bounds.
_COMFORT_TEMP = finite_range(-50, 60)
SETTING_VALIDATORS: dict[str, Any] = {
    "enabled": bool,
    "outdoor_temp_sensor": optional_entity_id,
    "indoor_temp_sensor": optional_entity_id,
    "weather_entity": optional_entity_id,
    "comfort_temp_min": _COMFORT_TEMP,
    "comfort_temp_max": _COMFORT_TEMP,
    "comfort_hysteresis": finite_range(0.1, 5.0),
    "threshold_hysteresis": finite_range(0, 5.0),
    "pause_duration": int_range(1, 480),
    "lock_position": int_range(0, 100),
    "vent_position": int_range(0, 100),
    "lock_tilt_position": vol.Any(None, int_range(0, 100)),
    "vent_tilt_position": vol.Any(None, int_range(0, 100)),
    "min_position_change": int_range(1, 50),
    "min_time_between_changes": int_range(60, 3600),
    "house_rotation": finite_range(-180, 180),
    "workday_sensor": optional_entity_id,
    "wind_sensor": optional_entity_id,
    "wind_speed_threshold": finite_range(0),
    "wind_speed_hysteresis": finite_range(0),
    "solar_sensor": optional_entity_id,
    "solar_threshold": finite_range(0),
    "solar_hysteresis": finite_range(0),
    "command_stagger": finite_range(0, 2.0),
    "logbook_enabled": bool,
    "update_check_enabled": bool,
    "default_travel_time": vol.Any(None, int_range(1, 300)),
    "wind_position": int_range(0, 100),
    "solar_threshold_entity": optional_entity_id,
    "comfort_temp_min_entity": optional_entity_id,
    "comfort_temp_max_entity": optional_entity_id,
    "sun_heating_ignore": bool,
    "sun_neutral_ignore": bool,
    "preemptive_shading": bool,
    "temp_color_thermometer": bool,
    "pause_resume_on_match": bool,
}
_SETTING_SCHEMAS = {key: vol.Schema(validator) for key, validator in SETTING_VALIDATORS.items()}


def _check_comfort(get: Callable[[str], Any]) -> str | None:
    low, high = get("comfort_temp_min"), get("comfort_temp_max")
    if low >= high:
        return f"comfort_temp_min ({low}) must be lower than comfort_temp_max ({high})"
    return None


def _check_wind(get: Callable[[str], Any]) -> str | None:
    # Deactivation happens at threshold - hysteresis; <= 0 would keep wind
    # protection (and the block on all automation) on forever.
    threshold, hysteresis = get("wind_speed_threshold"), get("wind_speed_hysteresis")
    if threshold > 0 and hysteresis >= threshold:
        return (
            f"wind_speed_hysteresis ({hysteresis}) must be lower than "
            f"wind_speed_threshold ({threshold})"
        )
    return None


def _check_solar(get: Callable[[str], Any]) -> str | None:
    # Same deadband logic as the wind: release at threshold - hysteresis.
    threshold, hysteresis = get("solar_threshold"), get("solar_hysteresis")
    if threshold > 0 and hysteresis >= threshold:
        return (
            f"solar_hysteresis ({hysteresis}) must be lower than "
            f"solar_threshold ({threshold})"
        )
    return None


# (error code, settings involved, check) -- the code is the WS error code
SETTINGS_CROSS_CHECKS: tuple[tuple[str, tuple[str, str], Callable[..., str | None]], ...] = (
    ("invalid_comfort_range", ("comfort_temp_min", "comfort_temp_max"), _check_comfort),
    ("invalid_wind_hysteresis", ("wind_speed_threshold", "wind_speed_hysteresis"), _check_wind),
    ("invalid_solar_hysteresis", ("solar_threshold", "solar_hysteresis"), _check_solar),
)


def settings_cross_error(
    get: Callable[[str], Any], changed: Collection[str] | None = None
) -> tuple[str, str] | None:
    """First failing cross-field check as (error code, message), else None.

    get(key) returns the resulting value of a setting (new or current).
    When changed is given, only the checks involving at least one of those
    keys run: a pair stored before a check existed (e.g. solar_hysteresis >=
    solar_threshold accepted before v1.87) must not block saving unrelated
    settings, only a change of one of its own fields.
    """
    for code, keys, check in SETTINGS_CROSS_CHECKS:
        if changed is not None and not any(key in changed for key in keys):
            continue
        message = check(get)
        if message:
            return code, message
    return None


# Per-cover runtime state: kept from this installation on import, never
# taken from the file (a stale pause or lock would not match the automation),
# and not exported.
_COVER_RUNTIME_FIELDS = ("status", "pause_until", "last_position_change")

# Per-cover learned values: exported (a restore on a new installation keeps
# them), taken from the file on import only for covers that do not exist
# locally -- an existing cover keeps the value learned here.
_COVER_LEARNED_FIELDS = ("measured_travel_time",)

# Internal runtime keys the coordinator may keep in the store: never
# exported, never taken from a file, kept across an import.
_RUNTIME_TOP_KEYS = ("wind_protected_state", "pre_lock_states")

_INVALID = object()


def _coerce_setting(key: str, value: Any) -> Any:
    """Imported global setting in its proper type, _INVALID if unusable.

    The value is then checked against the same bounds as the settings/update
    WebSocket command. None is passed through (handled by the nullable
    logic of the import).
    """
    if value is None:
        return None
    if key in _BOOL_SETTINGS:
        result = _opt_bool(value)
    elif key in _INT_SETTINGS:
        result = _to_int(value, None)
    elif key in _FLOAT_SETTINGS:
        result = _to_float(value, None)
    elif isinstance(value, str):
        # Entity ids / sensors: non-empty text or nothing
        result = value.strip()
        if not result:
            return None
    else:
        return _INVALID
    if result is None:
        return _INVALID
    schema = _SETTING_SCHEMAS.get(key)
    if schema is None:
        return result
    try:
        return schema(result)
    except vol.Invalid:
        return _INVALID


# Settings where None is a meaningful value ("no sensor configured").
NULLABLE_SETTING_KEYS = frozenset({
        "outdoor_temp_sensor", "indoor_temp_sensor", "weather_entity",
        "workday_sensor", "wind_sensor", "solar_sensor",
        "lock_tilt_position", "vent_tilt_position", "default_travel_time",
        "solar_threshold_entity", "comfort_temp_min_entity", "comfort_temp_max_entity",
})

# One-shot data migrations; applied ids are persisted in _data["migrations"]
MIGRATION_PAUSE_DURATION_120 = "pause_duration_120"
MIGRATION_PREEMPTIVE_TRISTATE = "preemptive_tristate"
_ALL_MIGRATIONS = (MIGRATION_PAUSE_DURATION_120, MIGRATION_PREEMPTIVE_TRISTATE)

# Top-level keys of a configuration: everything else in an imported file is
# dropped, and only these are exported.
_CONFIG_TOP_KEYS = frozenset({
    "facades", "covers", "rules", "scenarios", "active_scenario", "migrations",
    *GLOBAL_SETTING_KEYS,
})


def _migrate_pause_duration_120(covers: Any) -> None:
    """v1.6.0: remove per-cover pause_duration matching the old default (120)."""
    if not isinstance(covers, dict):
        return
    for cover_data in covers.values():
        if isinstance(cover_data, dict) and cover_data.get("pause_duration") == 120:
            cover_data["pause_duration"] = None


def _migrate_preemptive_tristate(covers: Any) -> None:
    """Per-cover preemptive_shading True becomes None (follow global, default True).

    False stays an explicit override, so behaviour is unchanged.
    """
    if not isinstance(covers, dict):
        return
    for cover_data in covers.values():
        if isinstance(cover_data, dict) and cover_data.get("preemptive_shading") is True:
            cover_data["preemptive_shading"] = None


def _apply_migrations(data: dict[str, Any], done: list[str]) -> bool:
    """Run on data every one-shot migration missing from done (in place).

    done is extended with the applied ids. Returns True if one ran.
    """
    steps = (
        # Runs once only: a deliberate 120 set later must survive.
        (MIGRATION_PAUSE_DURATION_120, _migrate_pause_duration_120),
        # Per-cover preemptive_shading became tri-state (None = global)
        (MIGRATION_PREEMPTIVE_TRISTATE, _migrate_preemptive_tristate),
    )
    changed = False
    for migration_id, step in steps:
        if migration_id in done:
            continue
        step(data.get("covers"))
        done.append(migration_id)
        changed = True
    return changed


def _has_invalid_condition(rule_data: dict[str, Any]) -> bool:
    """True when a condition of the rule cannot be loaded (Rule.from_dict drops it)."""
    raw = rule_data.get("conditions")
    for cond in raw if isinstance(raw, list) else []:
        try:
            Condition.from_dict(cond)
        except (ValueError, KeyError):
            return True
    return False


def _normalize_stored_data(data: dict[str, Any]) -> bool:
    """Align the raw stored data with what the models load (in place, idempotent).

    - a per-cover pause_duration of 0 (allowed by older versions, now at
      least 1 minute) is stored as 1;
    - an enabled rule with a condition that cannot be loaded (non-finite
      param, unknown type...) is stored disabled: without that condition it
      would match more often than configured (always, when none is left).
    Returns True if something changed.
    """
    changed = False
    covers = data.get("covers")
    for cover_data in covers.values() if isinstance(covers, dict) else ():
        if not isinstance(cover_data, dict):
            continue
        duration = _to_int(cover_data.get("pause_duration"), None)
        if duration is not None and duration < 1:
            cover_data["pause_duration"] = 1
            changed = True
    rules = data.get("rules")
    for rule_id, rule_data in rules.items() if isinstance(rules, dict) else ():
        if not isinstance(rule_data, dict) or not _to_bool(rule_data.get("enabled"), True):
            continue
        if _has_invalid_condition(rule_data):
            _LOGGER.warning(
                "Rule '%s' has invalid condition(s) and was disabled",
                rule_data.get("name", rule_id),
            )
            rule_data["enabled"] = False
            changed = True
    return changed


def _is_cover_entity_id(value: Any) -> bool:
    """True for a valid entity id of the cover domain."""
    return isinstance(value, str) and value.startswith("cover.") and valid_entity_id(value)


def resolve_active_scenario(active: str | None, scenarios: Any) -> str:
    """Return the effective active scenario id.

    An empty or unknown id resolves to the first scenario, like the scenario
    select entity shows it ("everyday" when no scenario exists).
    """
    available = list(scenarios or ()) or ["everyday"]
    if active and active in available:
        return active
    return available[0]


def _entry_key(section: str, entry: Any) -> str:
    """Storage key of an imported entry (its id, entity_id for covers)."""
    return entry.entity_id if section == "covers" else entry.id


class CoverAutomaticStorage:
    """Manage persistent storage for CoverAutomatic."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self._data: dict[str, Any] = {}
        self._save_lock = asyncio.Lock()
        # Deserialization cache
        self._cache_facades: dict[str, Facade] | None = None
        self._cache_covers: dict[str, CoverConfig] | None = None
        self._cache_rules: dict[str, Rule] | None = None
        self._cache_scenarios: dict[str, Scenario] | None = None

    def _setting(self, key: str, default: Any) -> Any:
        """Return a global setting, falling back to default when unset or None.

        A key present with value None (e.g. from an older import) must not
        leak None into the coordinator/engine, which compare these numerically.
        """
        value = self._data.get(key)
        return default if value is None else value

    def _entity_setting(self, key: str) -> str | None:
        """Return an optional entity id setting (None when unset/invalid)."""
        value = self._data.get(key)
        return value if isinstance(value, str) and value else None

    def _invalidate_cache(self) -> None:
        """Invalidate all deserialization caches."""
        self._cache_facades = None
        self._cache_covers = None
        self._cache_rules = None
        self._cache_scenarios = None

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
                "indoor_temp_sensor": None,
                "weather_entity": None,
                "comfort_temp_min": 21.0,
                "comfort_temp_max": 25.0,
                "workday_sensor": None,
                "wind_sensor": None,
                "wind_speed_threshold": 0.0,
                "wind_speed_hysteresis": 0.0,
                "solar_sensor": None,
                "solar_threshold": 0.0,
                # New installs have nothing to migrate
                "migrations": list(_ALL_MIGRATIONS),
            }
        else:
            self._data = data
            if self._migrate():
                # Persist the migrated data and the migration markers
                self._schedule_save()
        self._invalidate_cache()

    def _migrate(self) -> bool:
        """Run data migrations for older storage versions.

        Returns True if the data changed (and must be saved).
        """
        done = self._data.get("migrations")
        if not isinstance(done, list):
            done = []
        changed = _apply_migrations(self._data, done)
        self._data["migrations"] = done
        if self._migrate_rule_scenarios():
            changed = True
        if _normalize_stored_data(self._data):
            changed = True
        return changed

    def _migrate_rule_scenarios(self) -> bool:
        """v1.68.0: give every rule an explicit scenario list (all scenarios).

        Rules created before per-rule scenario selection belong to every
        scenario. Switching a rule off inside a scenario is unchanged
        (Scenario.rules_disabled), so existing behaviour is preserved.
        Returns True if a rule was changed.
        """
        all_ids = list(self._data.get("scenarios", {}).keys())
        changed = False
        for rule_data in self._data.get("rules", {}).values():
            if not isinstance(rule_data.get("scenario_ids"), list):
                rule_data["scenario_ids"] = list(all_ids)
                changed = True
        return changed

    async def async_save(self) -> None:
        """Save data to storage.

        Uses the same lock as debounced saves to prevent concurrent writes.
        """
        # Store.async_save supersedes any pending async_delay_save.
        async with self._save_lock:
            await self._store.async_save(self._data)

    def _load_section(self, section: str, model_cls: Any) -> dict[str, Any]:
        """Deserialize one section, skipping (and logging) corrupted entries.

        A single bad entry (e.g. a NaN azimuth written as null) must not make
        the whole section -- and every caller -- raise.
        """
        raw = self._data.get(section)
        result: dict[str, Any] = {}
        if not isinstance(raw, dict):
            return result
        for key, value in raw.items():
            try:
                result[key] = model_cls.from_dict(value)
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Ignoring corrupted %s entry '%s' in storage: %s", section, key, err)
        return result

    @property
    def facades(self) -> dict[str, Facade]:
        """Get all facades (cached)."""
        if self._cache_facades is None:
            self._cache_facades = self._load_section("facades", Facade)
        return self._cache_facades

    @property
    def covers(self) -> dict[str, CoverConfig]:
        """Get all cover configurations (cached)."""
        if self._cache_covers is None:
            self._cache_covers = self._load_section("covers", CoverConfig)
        return self._cache_covers

    @property
    def rules(self) -> dict[str, Rule]:
        """Get all rules (cached)."""
        if self._cache_rules is None:
            self._cache_rules = self._load_section("rules", Rule)
        return self._cache_rules

    @property
    def scenarios(self) -> dict[str, Scenario]:
        """Get all scenarios (cached)."""
        if self._cache_scenarios is None:
            self._cache_scenarios = self._load_section("scenarios", Scenario)
        return self._cache_scenarios

    @property
    def active_scenario(self) -> str:
        """Get active scenario ID."""
        return self._setting("active_scenario", "everyday")

    @active_scenario.setter
    def active_scenario(self, value: str) -> None:
        """Set active scenario ID."""
        self._data["active_scenario"] = value

    @property
    def effective_active_scenario(self) -> str:
        """Active scenario ID, an unknown/empty one resolved to the first."""
        return resolve_active_scenario(self.active_scenario, self._data.get("scenarios", {}))

    @property
    def outdoor_temp_sensor(self) -> str | None:
        """Get outdoor temperature sensor entity ID."""
        return self._data.get("outdoor_temp_sensor")

    @outdoor_temp_sensor.setter
    def outdoor_temp_sensor(self, value: str | None) -> None:
        """Set outdoor temperature sensor entity ID."""
        self._data["outdoor_temp_sensor"] = value

    @property
    def indoor_temp_sensor(self) -> str | None:
        """Get indoor temperature sensor entity ID."""
        return self._data.get("indoor_temp_sensor")

    @indoor_temp_sensor.setter
    def indoor_temp_sensor(self, value: str | None) -> None:
        """Set indoor temperature sensor entity ID."""
        self._data["indoor_temp_sensor"] = value

    @property
    def weather_entity(self) -> str | None:
        """Get weather entity ID."""
        return self._data.get("weather_entity")

    @weather_entity.setter
    def weather_entity(self, value: str | None) -> None:
        """Set weather entity ID."""
        self._data["weather_entity"] = value

    @property
    def comfort_temp_min(self) -> float:
        """Get minimum comfort temperature."""
        return self._setting("comfort_temp_min", 21.0)

    @comfort_temp_min.setter
    def comfort_temp_min(self, value: float) -> None:
        """Set minimum comfort temperature."""
        self._data["comfort_temp_min"] = value

    @property
    def comfort_temp_max(self) -> float:
        """Get maximum comfort temperature."""
        return self._setting("comfort_temp_max", 25.0)

    @comfort_temp_max.setter
    def comfort_temp_max(self, value: float) -> None:
        """Set maximum comfort temperature."""
        self._data["comfort_temp_max"] = value

    @property
    def comfort_hysteresis(self) -> float:
        """Get comfort temperature hysteresis."""
        return self._setting("comfort_hysteresis", 1.0)

    @comfort_hysteresis.setter
    def comfort_hysteresis(self, value: float) -> None:
        """Set comfort temperature hysteresis."""
        self._data["comfort_hysteresis"] = float(value)

    @property
    def threshold_hysteresis(self) -> float:
        """Get deadband for temperature_above/below conditions."""
        return self._setting("threshold_hysteresis", 0.5)

    @threshold_hysteresis.setter
    def threshold_hysteresis(self, value: float) -> None:
        """Set deadband for temperature_above/below conditions."""
        self._data["threshold_hysteresis"] = float(value)

    @property
    def enabled(self) -> bool:
        """Get global automation enabled state."""
        return self._setting("enabled", True)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set global automation enabled state."""
        self._data["enabled"] = bool(value)

    @property
    def pause_duration(self) -> int:
        """Get global default pause duration in minutes."""
        return self._setting("pause_duration", 10)

    @pause_duration.setter
    def pause_duration(self, value: int) -> None:
        """Set global default pause duration in minutes."""
        self._data["pause_duration"] = int(value)

    @property
    def lock_position(self) -> int:
        """Get global default lock position."""
        return self._setting("lock_position", 100)

    @lock_position.setter
    def lock_position(self, value: int) -> None:
        """Set global default lock position."""
        self._data["lock_position"] = int(value)

    @property
    def vent_position(self) -> int:
        """Get global default vent position."""
        return self._setting("vent_position", 30)

    @vent_position.setter
    def vent_position(self, value: int) -> None:
        """Set global default vent position."""
        self._data["vent_position"] = int(value)

    @property
    def lock_tilt_position(self) -> int | None:
        """Get global default lock tilt position."""
        return self._data.get("lock_tilt_position")

    @lock_tilt_position.setter
    def lock_tilt_position(self, value: int | None) -> None:
        """Set global default lock tilt position."""
        self._data["lock_tilt_position"] = value

    @property
    def vent_tilt_position(self) -> int | None:
        """Get global default vent tilt position."""
        return self._data.get("vent_tilt_position")

    @vent_tilt_position.setter
    def vent_tilt_position(self, value: int | None) -> None:
        """Set global default vent tilt position."""
        self._data["vent_tilt_position"] = value

    @property
    def min_position_change(self) -> int:
        """Get global default minimum position change."""
        return self._setting("min_position_change", 5)

    @min_position_change.setter
    def min_position_change(self, value: int) -> None:
        """Set global default minimum position change."""
        self._data["min_position_change"] = int(value)

    @property
    def min_time_between_changes(self) -> int:
        """Get global default minimum time between changes."""
        return self._setting("min_time_between_changes", 300)

    @min_time_between_changes.setter
    def min_time_between_changes(self, value: int) -> None:
        """Set global default minimum time between changes."""
        self._data["min_time_between_changes"] = int(value)

    @property
    def workday_sensor(self) -> str | None:
        """Get workday binary sensor entity ID."""
        return self._data.get("workday_sensor")

    @workday_sensor.setter
    def workday_sensor(self, value: str | None) -> None:
        """Set workday binary sensor entity ID."""
        self._data["workday_sensor"] = value

    @property
    def wind_sensor(self) -> str | None:
        """Get wind speed sensor entity ID."""
        return self._data.get("wind_sensor")

    @wind_sensor.setter
    def wind_sensor(self, value: str | None) -> None:
        """Set wind speed sensor entity ID."""
        self._data["wind_sensor"] = value

    @property
    def wind_speed_threshold(self) -> float:
        """Get wind speed activation threshold."""
        return self._setting("wind_speed_threshold", 0.0)

    @wind_speed_threshold.setter
    def wind_speed_threshold(self, value: float) -> None:
        """Set wind speed activation threshold."""
        self._data["wind_speed_threshold"] = float(value)

    @property
    def wind_speed_hysteresis(self) -> float:
        """Get wind speed deactivation hysteresis."""
        return self._setting("wind_speed_hysteresis", 0.0)

    @wind_speed_hysteresis.setter
    def wind_speed_hysteresis(self, value: float) -> None:
        """Set wind speed deactivation hysteresis."""
        self._data["wind_speed_hysteresis"] = float(value)

    @property
    def solar_sensor(self) -> str | None:
        """Get solar intensity sensor entity id."""
        return self._data.get("solar_sensor")

    @solar_sensor.setter
    def solar_sensor(self, value: str | None) -> None:
        """Set solar intensity sensor entity id."""
        self._data["solar_sensor"] = value

    @property
    def solar_threshold(self) -> float:
        """Get solar intensity threshold for preemptive shading."""
        return self._setting("solar_threshold", 0.0)

    @solar_threshold.setter
    def solar_threshold(self, value: float) -> None:
        """Set solar intensity threshold for preemptive shading."""
        self._data["solar_threshold"] = float(value)

    @property
    def solar_hysteresis(self) -> float:
        """Get deadband for the preemptive-shading solar threshold."""
        return self._setting("solar_hysteresis", 0.0)

    @solar_hysteresis.setter
    def solar_hysteresis(self, value: float) -> None:
        """Set deadband for the preemptive-shading solar threshold."""
        self._data["solar_hysteresis"] = float(value)

    @property
    def sun_heating_ignore(self) -> bool:
        """Sun on facade: answer 'no sun' in heating mode."""
        return bool(self._setting("sun_heating_ignore", True))

    @sun_heating_ignore.setter
    def sun_heating_ignore(self, value: bool) -> None:
        """Set the heating-mode sun switch."""
        self._data["sun_heating_ignore"] = bool(value)

    @property
    def sun_neutral_ignore(self) -> bool:
        """Sun on facade: answer 'no sun' in neutral mode (unless preemptive)."""
        return bool(self._setting("sun_neutral_ignore", True))

    @sun_neutral_ignore.setter
    def sun_neutral_ignore(self, value: bool) -> None:
        """Set the neutral-mode sun switch."""
        self._data["sun_neutral_ignore"] = bool(value)

    @property
    def preemptive_shading(self) -> bool:
        """Global default for preemptive shading (per-cover override wins)."""
        return bool(self._setting("preemptive_shading", True))

    @preemptive_shading.setter
    def preemptive_shading(self, value: bool) -> None:
        """Set the global preemptive shading default."""
        self._data["preemptive_shading"] = bool(value)

    @property
    def temp_color_thermometer(self) -> bool:
        """Display only: cold room blue / hot room red (False: cold red, hot blue)."""
        return bool(self._setting("temp_color_thermometer", False))

    @temp_color_thermometer.setter
    def temp_color_thermometer(self, value: bool) -> None:
        """Set the temperature colour convention."""
        self._data["temp_color_thermometer"] = bool(value)

    @property
    def pause_resume_on_match(self) -> bool:
        """End a manual pause once the cover is back at its rule's position."""
        return bool(self._setting("pause_resume_on_match", True))

    @pause_resume_on_match.setter
    def pause_resume_on_match(self, value: bool) -> None:
        """Set the global resume-on-match default (per-cover override wins)."""
        self._data["pause_resume_on_match"] = bool(value)

    @property
    def solar_threshold_entity(self) -> str | None:
        """Entity holding the solar threshold (overrides solar_threshold)."""
        return self._entity_setting("solar_threshold_entity")

    @solar_threshold_entity.setter
    def solar_threshold_entity(self, value: str | None) -> None:
        """Set the entity holding the solar threshold."""
        self._data["solar_threshold_entity"] = value or None

    @property
    def comfort_temp_min_entity(self) -> str | None:
        """Entity holding the minimum comfort temperature."""
        return self._entity_setting("comfort_temp_min_entity")

    @comfort_temp_min_entity.setter
    def comfort_temp_min_entity(self, value: str | None) -> None:
        """Set the entity holding the minimum comfort temperature."""
        self._data["comfort_temp_min_entity"] = value or None

    @property
    def comfort_temp_max_entity(self) -> str | None:
        """Entity holding the maximum comfort temperature."""
        return self._entity_setting("comfort_temp_max_entity")

    @comfort_temp_max_entity.setter
    def comfort_temp_max_entity(self, value: str | None) -> None:
        """Set the entity holding the maximum comfort temperature."""
        self._data["comfort_temp_max_entity"] = value or None

    @property
    def wind_position(self) -> int:
        """Logical position covers move to while wind protection is active."""
        value = self._data.get("wind_position")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 100
        return max(0, min(100, int(value)))

    @wind_position.setter
    def wind_position(self, value: int) -> None:
        """Set the wind protection position (0-100)."""
        self._data["wind_position"] = max(0, min(100, int(value)))

    @property
    def house_rotation(self) -> float:
        """Get global house rotation offset in degrees."""
        return self._setting("house_rotation", 0.0)

    @house_rotation.setter
    def house_rotation(self, value: float) -> None:
        """Set global house rotation offset in degrees."""
        self._data["house_rotation"] = float(value)

    @property
    def default_travel_time(self) -> int | None:
        """Default full travel time (s) for covers without own/measured value."""
        value = self._data.get("default_travel_time")
        return int(value) if isinstance(value, (int, float)) and value > 0 else None

    @default_travel_time.setter
    def default_travel_time(self, value: int | None) -> None:
        """Set the default travel time (None = no default, 30 s settle)."""
        self._data["default_travel_time"] = int(value) if value else None

    @property
    def command_stagger(self) -> float:
        """Get command stagger delay in seconds between cover commands."""
        return self._setting("command_stagger", 0.0)

    @command_stagger.setter
    def command_stagger(self, value: float) -> None:
        """Set command stagger delay in seconds."""
        self._data["command_stagger"] = max(0.0, float(value))

    @property
    def logbook_enabled(self) -> bool:
        """Get whether to write HA logbook entries for cover actions."""
        return self._setting("logbook_enabled", True)

    @logbook_enabled.setter
    def logbook_enabled(self, value: bool) -> None:
        """Set whether to write HA logbook entries for cover actions."""
        self._data["logbook_enabled"] = bool(value)

    @property
    def update_check_enabled(self) -> bool:
        """Get whether the panel may query GitHub for the latest release."""
        return self._setting("update_check_enabled", True)

    @update_check_enabled.setter
    def update_check_enabled(self, value: bool) -> None:
        """Set whether the panel may query GitHub for the latest release."""
        self._data["update_check_enabled"] = bool(value)

    async def async_add_facade(self, facade: Facade, *, save: bool = True) -> None:
        """Add or update a facade."""
        if "facades" not in self._data:
            self._data["facades"] = {}
        self._data["facades"][facade.id] = facade.to_dict()
        self._cache_facades = None
        if save:
            await self.async_save()

    async def async_remove_facade(self, facade_id: str) -> None:
        """Remove a facade and clean up references."""
        if facade_id in self._data.get("facades", {}):
            del self._data["facades"][facade_id]
            self._cache_facades = None
            # Clean up cover references
            for cover_data in self._data.get("covers", {}).values():
                if cover_data.get("facade_id") == facade_id:
                    cover_data["facade_id"] = None
            self._cache_covers = None
            # Clean up rule references
            for rule_data in self._data.get("rules", {}).values():
                fids = rule_data.get("facade_ids", [])
                if facade_id in fids:
                    fids.remove(facade_id)
                    self._disable_if_unassigned(rule_data)
            self._cache_rules = None
            await self.async_save()

    async def async_add_cover(self, cover: CoverConfig, *, save: bool = True) -> None:
        """Add or update a cover configuration."""
        if "covers" not in self._data:
            self._data["covers"] = {}
        self._data["covers"][cover.entity_id] = cover.to_dict()
        self._cache_covers = None
        if save:
            await self.async_save()

    async def async_remove_cover(self, entity_id: str) -> None:
        """Remove a cover configuration and clean up references."""
        if entity_id in self._data.get("covers", {}):
            del self._data["covers"][entity_id]
            self._cache_covers = None
            # Clean up facade references
            for facade_data in self._data.get("facades", {}).values():
                cids = facade_data.get("cover_ids", [])
                if entity_id in cids:
                    cids.remove(entity_id)
            self._cache_facades = None
            # Clean up rule references
            for rule_data in self._data.get("rules", {}).values():
                cids = rule_data.get("cover_ids", [])
                if entity_id in cids:
                    cids.remove(entity_id)
                    self._disable_if_unassigned(rule_data)
            self._cache_rules = None
            await self.async_save()

    @staticmethod
    def _disable_if_unassigned(rule_data: dict[str, Any]) -> None:
        """Disable a rule whose last cover/facade assignment was removed.

        Without any assignment the engine treats a rule as global (applies
        to every cover), which the removal must not silently turn it into.
        """
        if rule_data.get("cover_ids") or rule_data.get("facade_ids"):
            return
        if rule_data.get("enabled", True):
            _LOGGER.warning(
                "Rule '%s' has no cover or facade left and was disabled",
                rule_data.get("name", rule_data.get("id", "?")),
            )
        rule_data["enabled"] = False

    @staticmethod
    def _disable_if_no_scenario(rule_data: dict[str, Any]) -> None:
        """Disable a rule whose last scenario was removed.

        Consistent with facade/cover removal: a rule left without any
        scenario is switched off (and logged) rather than kept dangling.
        """
        ids = rule_data.get("scenario_ids")
        if not isinstance(ids, list) or ids:
            return
        if rule_data.get("enabled", True):
            _LOGGER.warning(
                "Rule '%s' has no scenario left and was disabled",
                rule_data.get("name", rule_data.get("id", "?")),
            )
        rule_data["enabled"] = False

    async def async_add_rule(self, rule: Rule, *, save: bool = True) -> None:
        """Add or update a rule."""
        if "rules" not in self._data:
            self._data["rules"] = {}
        self._data["rules"][rule.id] = rule.to_dict()
        self._cache_rules = None
        if save:
            await self.async_save()

    async def async_remove_rule(self, rule_id: str) -> None:
        """Remove a rule and clean up scenario references."""
        if rule_id in self._data.get("rules", {}):
            del self._data["rules"][rule_id]
            self._cache_rules = None
            # Clean up scenario rules_disabled references
            for scenario_data in self._data.get("scenarios", {}).values():
                disabled = scenario_data.get("rules_disabled", [])
                if rule_id in disabled:
                    disabled.remove(rule_id)
            self._cache_scenarios = None
            await self.async_save()

    async def async_rename_rule(self, old_id: str, new_id: str, *, save: bool = True) -> bool:
        """Move a rule to a new id, keeping its position and references.

        Scenario rules_disabled entries follow the new id. Returns False
        (nothing changed) when old_id is unknown or new_id is already taken.
        """
        rules = self._data.get("rules", {})
        if old_id not in rules or old_id == new_id or new_id in rules:
            return False
        # Rebuild the dict so the rule keeps its place in the order
        self._data["rules"] = {
            (new_id if key == old_id else key): value for key, value in rules.items()
        }
        self._data["rules"][new_id]["id"] = new_id
        for scenario_data in self._data.get("scenarios", {}).values():
            disabled = scenario_data.get("rules_disabled")
            if isinstance(disabled, list) and old_id in disabled:
                scenario_data["rules_disabled"] = [
                    new_id if rid == old_id else rid for rid in disabled
                ]
        self._cache_rules = None
        self._cache_scenarios = None
        if save:
            await self.async_save()
        return True

    def rule_order(self) -> list[str]:
        """Rule ids from highest to lowest priority (ties by id), as evaluated."""
        rules = self._data.get("rules", {})

        def key(rid: str) -> tuple[float, str]:
            try:
                prio = float(rules[rid].get("priority") or 0)
            except (TypeError, ValueError):
                prio = 0.0
            return (-prio, rid)

        return sorted(rules, key=key)

    def renumber_priorities(self, ordered_ids: list[str]) -> None:
        """Give priorities from the list order: first = highest."""
        rules = self._data.get("rules", {})
        total = len(ordered_ids)
        for idx, rid in enumerate(ordered_ids):
            rules[rid]["priority"] = (total - idx) * 10
        self._cache_rules = None

    async def async_duplicate_rule(self, rule_id: str, new_id: str, name: str) -> bool:
        """Copy a rule right below the original, active.

        The copy keeps every setting (conditions, targets, scenarios, safety)
        and is switched off in the same scenarios as the original. Returns
        False when rule_id is unknown or new_id is already taken.
        """
        rules = self._data.get("rules", {})
        if rule_id not in rules or new_id in rules:
            return False
        order = self.rule_order()
        copy_data = copy.deepcopy(rules[rule_id])
        copy_data.update({"id": new_id, "name": name, "enabled": True})
        rules[new_id] = copy_data
        order.insert(order.index(rule_id) + 1, new_id)
        self.renumber_priorities(order)
        for scenario_data in self._data.get("scenarios", {}).values():
            disabled = scenario_data.get("rules_disabled")
            if isinstance(disabled, list) and rule_id in disabled and new_id not in disabled:
                disabled.append(new_id)
        self._cache_scenarios = None
        await self.async_save()
        return True

    async def async_add_scenario(self, scenario: Scenario, *, save: bool = True) -> None:
        """Add or update a scenario.

        A new scenario is added to the scenario list of every rule (rules
        belong to all scenarios by default; deselect them per rule).
        """
        if "scenarios" not in self._data:
            self._data["scenarios"] = {}
        is_new = scenario.id not in self._data["scenarios"]
        self._data["scenarios"][scenario.id] = scenario.to_dict()
        self._cache_scenarios = None
        if is_new:
            for rule_data in self._data.get("rules", {}).values():
                ids = rule_data.get("scenario_ids")
                if isinstance(ids, list) and scenario.id not in ids:
                    ids.append(scenario.id)
            self._cache_rules = None
        if save:
            await self.async_save()

    async def async_remove_scenario(self, scenario_id: str) -> None:
        """Remove a scenario."""
        if scenario_id in self._data.get("scenarios", {}):
            del self._data["scenarios"][scenario_id]
            self._cache_scenarios = None
            for rule_data in self._data.get("rules", {}).values():
                ids = rule_data.get("scenario_ids")
                if isinstance(ids, list) and scenario_id in ids:
                    ids.remove(scenario_id)
                    self._disable_if_no_scenario(rule_data)
            self._cache_rules = None
            if self._data.get("active_scenario") == scenario_id:
                remaining = self._data.get("scenarios", {})
                self._data["active_scenario"] = next(iter(remaining), "everyday")
            await self.async_save()

    def get_raw_data(self) -> dict[str, Any]:
        """Get raw data (deep copy to prevent race conditions)."""
        return copy.deepcopy(self._data)

    def get_export_data(self) -> dict[str, Any]:
        """Complete configuration for a backup.

        Unlike the raw store, every global setting is written with its
        effective value (defaults included) and every entry in its full
        normalised form, so a restore reproduces exactly what is in use
        even when a setting was never saved or a field added later.

        Runtime state (cover status, pause, last move) and internal keys
        (e.g. wind_protected_state) are not exported; the learned travel
        time is (see _COVER_LEARNED_FIELDS). The
        migration markers are, so an import does not replay migrations on
        data already in the current format.
        """
        data: dict[str, Any] = {}
        for key in GLOBAL_SETTING_KEYS:
            data[key] = getattr(self, key)
        data["active_scenario"] = self.active_scenario
        sections = {
            "facades": self.facades,
            "covers": self.covers,
            "rules": self.rules,
            "scenarios": self.scenarios,
        }
        for section, entries in sections.items():
            data[section] = {key: entry.to_dict() for key, entry in entries.items()}
        for cover_data in data["covers"].values():
            for runtime_field in _COVER_RUNTIME_FIELDS:
                cover_data.pop(runtime_field, None)
        # Exported entries are normalised: every known migration applies
        data["migrations"] = list(_ALL_MIGRATIONS)
        return data

    async def async_import_data(self, data: dict[str, Any]) -> None:
        """Import data from dict with validation."""
        if not isinstance(data, dict):
            raise ValueError("Import data must be a dictionary")

        for key in _REQUIRED_DICT_KEYS:
            if key in data and not isinstance(data[key], dict):
                raise ValueError(f"Import data key '{key}' must be a dictionary")

        # Refuse files that are not a CoverAutomatic export at all: without
        # this, any YAML mapping (e.g. secrets.yaml) silently replaced the
        # whole configuration with empty sections.
        if not any(key in data for key in _REQUIRED_DICT_KEYS):
            raise ValueError(
                "Import data is not a CoverAutomatic configuration "
                f"(none of {', '.join(_REQUIRED_DICT_KEYS)} found)"
            )

        # Only configuration keys are taken from the file (deep copy to
        # prevent external mutation); unknown or internal keys are dropped.
        unknown_keys = sorted(str(key) for key in data if key not in _CONFIG_TOP_KEYS)
        if unknown_keys:
            _LOGGER.warning("Import: ignoring unknown keys %s", ", ".join(unknown_keys))
        data = copy.deepcopy({k: v for k, v in data.items() if k in _CONFIG_TOP_KEYS})

        # Ensure required keys exist
        for key in _REQUIRED_DICT_KEYS:
            data.setdefault(key, {})
        data.setdefault(
            "active_scenario",
            self._data.get("active_scenario", "everyday"),
        )

        # Deserialize sub-elements (skip corrupt entries) and store the
        # normalised form, keyed by the entry's own id, so bad types cannot
        # crash the update cycle later.
        _validators: dict[str, type] = {
            "facades": Facade,
            "covers": CoverConfig,
            "rules": Rule,
            "scenarios": Scenario,
        }
        for section, model_cls in _validators.items():
            valid: dict[str, Any] = {}
            for k, v in data.get(section, {}).items():
                try:
                    entry = model_cls.from_dict(v)
                    key = _entry_key(section, entry)
                    if not isinstance(key, str) or not key:
                        raise ValueError("missing id")
                    if section == "covers" and not _is_cover_entity_id(key):
                        raise ValueError(f"'{key}' is not a cover entity id")
                    normalised = entry.to_dict()
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning(
                        "Skipping invalid %s entry '%s' during import: %s",
                        section, k, err,
                    )
                    continue
                if key != k:
                    _LOGGER.warning(
                        "Import: %s entry '%s' stored under its id '%s'", section, k, key
                    )
                if key in valid:
                    _LOGGER.warning("Import: duplicate %s id '%s', keeping the last", section, key)
                valid[key] = normalised
            data[section] = valid

        self._reconcile_import_references(data)

        # Validate active_scenario exists in imported scenarios
        if data.get("active_scenario") not in data.get("scenarios", {}):
            first_scenario = next(iter(data.get("scenarios", {})), "everyday")
            data["active_scenario"] = first_scenario

        # Imported global settings in their proper type and within the bounds
        # of the settings form; unusable values are dropped (the local value
        # is then kept, as for a missing key).
        for gkey in GLOBAL_SETTING_KEYS:
            if gkey not in data:
                continue
            coerced = _coerce_setting(gkey, data[gkey])
            if coerced is _INVALID:
                _LOGGER.warning(
                    "Import: invalid value %r for setting '%s', keeping the current one",
                    data[gkey], gkey,
                )
                data.pop(gkey)
            else:
                data[gkey] = coerced

        # Cross-field checks (comfort band, wind/solar deadbands) on the
        # resulting values: an inconsistent imported pair keeps the local one.
        def _resulting(key: str) -> Any:
            value = data.get(key)
            return getattr(self, key) if value is None else value

        for code, keys, check in SETTINGS_CROSS_CHECKS:
            message = check(_resulting)
            if message and any(data.get(key) is not None for key in keys):
                _LOGGER.warning(
                    "Import: %s (%s), keeping the current values", message, code
                )
                for key in keys:
                    data.pop(key, None)

        # Runtime state of the covers stays the one of this installation
        local_covers = self._data.get("covers", {})
        for entity_id, cover_data in data.get("covers", {}).items():
            local = local_covers.get(entity_id) or {}
            for field in _COVER_RUNTIME_FIELDS:
                cover_data[field] = local.get(field)
            for field in _COVER_LEARNED_FIELDS:
                if entity_id in local_covers:
                    cover_data[field] = local.get(field)
                else:
                    # New cover: the file's value, if usable (positive)
                    value = _to_float(cover_data.get(field), None)
                    cover_data[field] = value if value is not None and value > 0 else None
            if cover_data.get("status") is None:
                cover_data["status"] = "auto"

        # Preserve global settings not present in import data
        for gkey in GLOBAL_SETTING_KEYS:
            if gkey in NULLABLE_SETTING_KEYS and gkey in data:
                continue  # explicit value (including None) wins
            if data.get(gkey) is not None:
                continue
            # Only carry over settings that actually exist locally; copying
            # an absent key would store None and override the getter default
            # (e.g. enabled=None silently disabled all automation).
            if self._data.get(gkey) is not None:
                data[gkey] = self._data[gkey]
            else:
                data.pop(gkey, None)

        # Replay on the imported entries every migration the file has not
        # been through yet (older exports, hand-written files): idempotent,
        # as each applied id is recorded.
        imported_done = data.get("migrations")
        done = (
            [m for m in imported_done if isinstance(m, str)]
            if isinstance(imported_done, list) else []
        )
        _apply_migrations(data, done)
        data["migrations"] = list(dict.fromkeys(done))

        # Internal runtime keys stay the ones of this installation
        for key in _RUNTIME_TOP_KEYS:
            if key in self._data:
                data[key] = self._data[key]

        self._data = data
        self._migrate_rule_scenarios()
        self._invalidate_cache()
        await self.async_save()

    def _reconcile_import_references(self, data: dict[str, Any]) -> None:
        """Make the references between imported entries consistent (in place).

        Unknown facade/cover/scenario/rule ids are dropped, the facade cover
        lists are rebuilt from cover.facade_id (the source of truth), and a
        rule left without any of its covers/facades or scenarios is disabled
        instead of silently becoming global.
        """
        facades = data["facades"]
        covers = data["covers"]
        rules = data["rules"]
        scenarios = data["scenarios"]

        for entity_id, cover_data in covers.items():
            fid = cover_data.get("facade_id")
            if fid is not None and fid not in facades:
                _LOGGER.warning(
                    "Import: cover '%s' refers to unknown facade '%s', unassigned", entity_id, fid
                )
                cover_data["facade_id"] = None

        for fid, facade_data in facades.items():
            members = [eid for eid, c in covers.items() if c.get("facade_id") == fid]
            listed = [eid for eid in facade_data.get("cover_ids", []) if eid in members]
            facade_data["cover_ids"] = list(dict.fromkeys([*listed, *members]))

        for rule_data in rules.values():
            assigned = bool(rule_data.get("facade_ids") or rule_data.get("cover_ids"))
            rule_data["facade_ids"] = [f for f in rule_data.get("facade_ids", []) if f in facades]
            rule_data["cover_ids"] = [c for c in rule_data.get("cover_ids", []) if c in covers]
            if assigned:
                self._disable_if_unassigned(rule_data)
            ids = rule_data.get("scenario_ids")
            if isinstance(ids, list) and ids:
                rule_data["scenario_ids"] = [s for s in ids if s in scenarios]
                self._disable_if_no_scenario(rule_data)

        for scenario_data in scenarios.values():
            scenario_data["rules_disabled"] = [
                r for r in scenario_data.get("rules_disabled", []) if r in rules
            ]

    def update_cover_status(
        self, entity_id: str, status: str, pause_until: float | None = None
    ) -> None:
        """Update cover status directly in storage data.

        Triggers a debounced save to persist changes.
        """
        if entity_id in self._data.get("covers", {}):
            self._data["covers"][entity_id]["status"] = status
            self._data["covers"][entity_id]["pause_until"] = pause_until
            self._cache_covers = None
            self._schedule_save()

    def get_cover_raw(self, entity_id: str) -> dict[str, Any] | None:
        """Get raw cover data dict (not a copy)."""
        return self._data.get("covers", {}).get(entity_id)

    def update_cover_last_change(self, entity_id: str, timestamp: float) -> None:
        """Update cover's last position change timestamp.

        Triggers a debounced save to persist changes.
        """
        if entity_id in self._data.get("covers", {}):
            self._data["covers"][entity_id]["last_position_change"] = timestamp
            self._cache_covers = None
            self._schedule_save()

    def update_cover_measured_travel(self, entity_id: str, seconds: float | None) -> None:
        """Store the measured full travel time of a cover (debounced save)."""
        if entity_id in self._data.get("covers", {}):
            self._data["covers"][entity_id]["measured_travel_time"] = seconds
            self._cache_covers = None
            self._schedule_save()

    def flush_pending_save(self) -> None:
        """Kept for API compatibility.

        Pending delayed writes are owned by the HA Store: they are replaced by
        the next async_save() and flushed by HA itself on shutdown
        (EVENT_HOMEASSISTANT_FINAL_WRITE), so nothing needs cancelling here.
        """

    def _schedule_save(self) -> None:
        """Schedule a debounced save through the HA Store.

        Multiple rapid updates are batched into a single write after
        SAVE_DEBOUNCE_DELAY seconds. Unlike a hand-rolled task, the Store
        also writes pending data when Home Assistant stops.
        """
        self._store.async_delay_save(lambda: self._data, SAVE_DEBOUNCE_DELAY)


class ActivityLogStorage:
    """Persistent activity log with automatic 3-day retention."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, LOG_STORAGE_KEY)
        self._entries: list[dict[str, Any]] = []
        self._save_lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Load log entries from storage."""
        data = await self._store.async_load()
        if data and isinstance(data.get("entries"), list):
            self._entries = data["entries"]
        else:
            self._entries = []
        self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than LOG_RETENTION_DAYS."""
        cutoff = dt_util.now().timestamp() - (LOG_RETENTION_DAYS * 86400)
        self._entries = [e for e in self._entries if e.get("ts", 0) > cutoff]

    def add_entry(
        self,
        event_type: str,
        entity_id: str | None = None,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add a log entry and schedule debounced save."""
        self._cleanup_old_entries()
        entry: dict[str, Any] = {
            "ts": dt_util.now().timestamp(),
            "type": event_type,
            "entity_id": entity_id,
            "message": message,
        }
        if data:
            entry["data"] = data
        self._entries.append(entry)
        self._schedule_save()

    async def async_clear(self) -> None:
        """Clear all log entries and save immediately."""
        self._entries = []
        async with self._save_lock:
            await self._store.async_save({"entries": self._entries})

    async def async_save(self) -> None:
        """Save log entries to storage immediately.

        Supersedes any pending delayed save so the in-memory state wins.
        """
        async with self._save_lock:
            await self._store.async_save({"entries": self._entries})

    def get_entries(
        self,
        event_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 500,
        include_global: bool = False,
    ) -> list[dict[str, Any]]:
        """Get log entries, newest first, with optional filters.

        include_global keeps, with an entity filter, the entries that concern
        no cover in particular (wind protection on/off) for context.
        """
        self._cleanup_old_entries()
        entries = self._entries
        if event_type:
            entries = [e for e in entries if e.get("type") == event_type]
        if entity_id:
            entries = [
                e for e in entries
                if e.get("entity_id") == entity_id or (include_global and not e.get("entity_id"))
            ]
        return list(reversed(entries))[:limit]

    def flush_pending_save(self) -> None:
        """Kept for API compatibility (the HA Store owns pending writes)."""

    def _schedule_save(self) -> None:
        """Schedule a debounced save through the HA Store."""
        self._store.async_delay_save(
            lambda: {"entries": self._entries}, SAVE_DEBOUNCE_DELAY
        )
