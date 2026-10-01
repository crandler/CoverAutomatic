"""WebSocket API for CoverAutomatic config panel."""
from __future__ import annotations

import copy
import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, FACADE_PRESETS, SIGNAL_DATA_UPDATED
from . import ha_condition as hac
from .models import (
    MAX_CONDITION_GROUPS,
    Condition,
    ConditionType,
    CoverConfig,
    Facade,
    Rule,
    Scenario,
    finite_float,
    finite_range,
    optional_entity_id,
)
from .storage import SETTING_VALIDATORS, settings_cross_error

# Integration version shown in the panel. Set once by async_setup_api() from
# the cached integration manifest -- reading manifest.json here would be a
# blocking file read inside the event loop, which Home Assistant flags.
_VERSION = "0"

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import CoverAutomaticCoordinator
    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)

# Cover fields that can be updated via WS API
_UPDATABLE_COVER_FIELDS = (
    "name", "facade_id", "auto_enabled", "pause_duration",
    "lock_sensor", "lock_position", "vent_sensor", "vent_position",
    "inverted", "supports_tilt", "lock_tilt_position", "vent_tilt_position",
    "inverted_tilt", "indoor_temp_sensor", "comfort_temp_min", "comfort_temp_max",
    "preemptive_shading", "lock_hold_position",
    "min_position_change", "min_time_between_changes",
    "travel_time", "measured_travel_time",
    "comfort_temp_min_entity", "comfort_temp_max_entity",
    "sun_heating_ignore", "sun_neutral_ignore",
    "occupancy_sensor", "occupancy_states",
    "pause_resume_on_match",
)

# Settings fields that can be updated via WS API
_SETTINGS_FIELDS = (
    "enabled",
    "outdoor_temp_sensor", "indoor_temp_sensor", "weather_entity",
    "comfort_temp_min", "comfort_temp_max", "comfort_hysteresis",
    "threshold_hysteresis", "pause_duration",
    "lock_position", "vent_position", "lock_tilt_position", "vent_tilt_position",
    "min_position_change", "min_time_between_changes",
    "house_rotation", "active_scenario",
    "workday_sensor",
    "wind_sensor", "wind_speed_threshold", "wind_speed_hysteresis",
    "command_stagger",
    "solar_sensor", "solar_threshold", "solar_hysteresis",
    "logbook_enabled", "update_check_enabled",
    "default_travel_time",
    "wind_position",
    "comfort_temp_min_entity", "comfort_temp_max_entity", "solar_threshold_entity",
    "sun_heating_ignore", "sun_neutral_ignore", "preemptive_shading",
    "temp_color_thermometer", "pause_resume_on_match",
)

# Umlaut replacement map
_UMLAUT_MAP: dict[str, str] = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
}


def _sanitize_id(name: str) -> str:
    """Generate a safe ID from a name.

    Lowercase, replace umlauts, replace non-alphanumeric with underscore,
    collapse consecutive underscores, strip leading/trailing underscores.
    """
    result = name
    for char, replacement in _UMLAUT_MAP.items():
        result = result.replace(char, replacement)
    # Other accents (é, è, à, ç…) become their base letter: "Météo" -> "meteo"
    result = "".join(
        c for c in unicodedata.normalize("NFKD", result) if not unicodedata.combining(c)
    )
    result = result.lower()
    result = re.sub(r"[^a-z0-9]", "_", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")
    return result or "unnamed"


# Optional entity id: None/"" -> None, else "domain.object" (shared validator)
_optional_entity_id = optional_entity_id


def _normalize_azimuth(value: float) -> float:
    """Compass bearing in [0, 360): any finite number is taken modulo 360.

    As before v1.87, -90 means 270 and 450 means 90; 360 is stored as 0
    (a facade with start == end covers the full circle).
    """
    bearing = value % 360
    # A tiny negative value rounds up to 360.0; + 0.0 turns -0.0 into 0.0
    return 0.0 if bearing >= 360 else bearing + 0.0


# Facade geometry: any finite bearing, normalised to 0-360 before the range
# check (360 is stored as 0), sun elevation -90-90
_AZIMUTH = vol.All(finite_float, _normalize_azimuth, vol.Range(min=0, max=360))
_ELEVATION = finite_range(-90, 90)
# Per-cover comfort band (same bounds as the global settings)
_COVER_COMFORT_TEMP = vol.Any(None, finite_range(-50, 60))


def _rule_id_for_name(rule_id: str, name: str, rules: dict[str, Any]) -> str:
    """Id a rule should have for its name.

    The current id is kept when it already is the sanitized name, or that
    name plus a numeric uniqueness suffix; otherwise a unique id is derived
    from the name (ignoring the rule itself).
    """
    desired = _sanitize_id(name)
    if rule_id == desired or re.fullmatch(re.escape(desired) + r"_\d+", rule_id):
        return rule_id
    others = {key: value for key, value in rules.items() if key != rule_id}
    return _unique_id(desired, others)


def _unique_id(base_id: str, existing: dict[str, Any]) -> str:
    """Ensure ID is unique by appending a numeric suffix if needed."""
    if base_id not in existing:
        return base_id
    counter = 2
    while f"{base_id}_{counter}" in existing:
        counter += 1
    return f"{base_id}_{counter}"


def _build_config_response(
    storage: CoverAutomaticStorage, hass: HomeAssistant | None = None,
    coordinator: CoverAutomaticCoordinator | None = None,
) -> dict[str, Any]:
    """Build full config response dict from storage."""
    result: dict[str, Any] = {
        "version": _VERSION,
        "enabled": storage.enabled,
        "covers": {k: v.to_dict() for k, v in storage.covers.items()},
        "facades": {k: v.to_dict() for k, v in storage.facades.items()},
        "rules": {k: v.to_dict() for k, v in storage.rules.items()},
        "scenarios": {k: v.to_dict() for k, v in storage.scenarios.items()},
        "settings": {
            "active_scenario": storage.active_scenario,
            "outdoor_temp_sensor": storage.outdoor_temp_sensor,
            "indoor_temp_sensor": storage.indoor_temp_sensor,
            "weather_entity": storage.weather_entity,
            "comfort_temp_min": storage.comfort_temp_min,
            "comfort_temp_max": storage.comfort_temp_max,
            "comfort_hysteresis": storage.comfort_hysteresis,
            "threshold_hysteresis": storage.threshold_hysteresis,
            "pause_duration": storage.pause_duration,
            "lock_position": storage.lock_position,
            "vent_position": storage.vent_position,
            "lock_tilt_position": storage.lock_tilt_position,
            "vent_tilt_position": storage.vent_tilt_position,
            "min_position_change": storage.min_position_change,
            "min_time_between_changes": storage.min_time_between_changes,
            "house_rotation": storage.house_rotation,
            "workday_sensor": storage.workday_sensor,
            "wind_sensor": storage.wind_sensor,
            "wind_speed_threshold": storage.wind_speed_threshold,
            "wind_speed_hysteresis": storage.wind_speed_hysteresis,
            "command_stagger": storage.command_stagger,
            "solar_sensor": storage.solar_sensor,
            "solar_threshold": storage.solar_threshold,
            "solar_hysteresis": storage.solar_hysteresis,
            "logbook_enabled": storage.logbook_enabled,
            "update_check_enabled": storage.update_check_enabled,
            "default_travel_time": storage.default_travel_time,
            "wind_position": storage.wind_position,
            "comfort_temp_min_entity": storage.comfort_temp_min_entity,
            "comfort_temp_max_entity": storage.comfort_temp_max_entity,
            "solar_threshold_entity": storage.solar_threshold_entity,
            "sun_heating_ignore": storage.sun_heating_ignore,
            "sun_neutral_ignore": storage.sun_neutral_ignore,
            "preemptive_shading": storage.preemptive_shading,
            "temp_color_thermometer": storage.temp_color_thermometer,
            "pause_resume_on_match": storage.pause_resume_on_match,
        },
    }
    if hass:
        managed = set(storage.covers.keys())
        result["available_covers"] = [
            {"entity_id": s.entity_id, "name": s.attributes.get("friendly_name", s.entity_id)}
            for s in hass.states.async_all("cover")
            if s.entity_id not in managed
        ]
    if coordinator:
        # Validation status of native HA conditions: {rule_id: {idx: status}}
        status: dict[str, dict[str, Any]] = {}
        engine = getattr(coordinator, "engine", None)
        if engine is not None:
            for rule_id, rule in storage.rules.items():
                for idx, cond in enumerate(rule.conditions):
                    if cond.type == ConditionType.HA_CONDITION:
                        status.setdefault(rule_id, {})[str(idx)] = engine.ha_condition_status(cond)
        result["condition_status"] = status
        result["active_rules"] = coordinator.get_active_rules()
        result["live_covers"] = coordinator.get_live_cover_data()
        result["live_facades"] = coordinator.get_live_facade_data()
    return result


def _sync_cover_facade_ids(
    storage: CoverAutomaticStorage, facade_id: str, cover_ids: list[str],
) -> None:
    """Sync cover.facade_id based on facade.cover_ids assignment.

    - Covers in cover_ids get facade_id set to this facade
    - Covers previously in this facade but removed get facade_id cleared
    - Covers are removed from any other facade's cover_ids (exclusive assignment)
    """
    cover_id_set = set(cover_ids)
    facades_raw = storage._data.get("facades", {})
    for entity_id, raw in storage._data.get("covers", {}).items():
        if entity_id in cover_id_set:
            # Remove from any other facade first
            old_fid = raw.get("facade_id")
            if old_fid and old_fid != facade_id and old_fid in facades_raw:
                other_cids = facades_raw[old_fid].get("cover_ids", [])
                if entity_id in other_cids:
                    other_cids.remove(entity_id)
            raw["facade_id"] = facade_id
        elif raw.get("facade_id") == facade_id:
            raw["facade_id"] = None
    storage._invalidate_cache()


def _sync_facade_cover_ids(
    storage: CoverAutomaticStorage, entity_id: str, new_facade_id: str | None, old_facade_id: str | None,
) -> None:
    """Sync facade.cover_ids based on cover.facade_id change.

    - Remove cover from old facade's cover_ids
    - Add cover to new facade's cover_ids
    """
    facades_raw = storage._data.get("facades", {})
    if old_facade_id and old_facade_id in facades_raw:
        cids = facades_raw[old_facade_id].get("cover_ids", [])
        if entity_id in cids:
            cids.remove(entity_id)
    if new_facade_id and new_facade_id in facades_raw:
        cids = facades_raw[new_facade_id].setdefault("cover_ids", [])
        if entity_id not in cids:
            cids.append(entity_id)
    storage._invalidate_cache()


def _parse_conditions(raw: list[dict[str, Any]]) -> tuple[list[Condition], list[str]]:
    """Parse condition dicts, collecting errors for invalid ones."""
    conditions: list[Condition] = []
    errors: list[str] = []
    if not isinstance(raw, list):
        return conditions, [f"conditions must be a list, got {type(raw).__name__}"]
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"Condition {idx}: must be a dict, got {type(item).__name__}")
            continue
        try:
            conditions.append(Condition.from_dict(item))
        except (ValueError, KeyError, TypeError) as err:
            errors.append(f"Condition {idx}: {err}")
    return conditions, errors


def _missing_ids(ids: list[str], known: dict[str, Any]) -> list[str]:
    """Return the subset of ids that are not present as keys in known."""
    return [i for i in ids if i not in known]


def _unknown_refs_msg(facade_ids: list[str], cover_ids: list[str]) -> str:
    """Build an error message listing unknown facade/cover references."""
    parts: list[str] = []
    if facade_ids:
        parts.append(f"facade(s): {', '.join(facade_ids)}")
    if cover_ids:
        parts.append(f"cover(s): {', '.join(cover_ids)}")
    return "Unknown " + "; ".join(parts)


# ---------------------------------------------------------------------------
# Handler functions (public for testability)
# ---------------------------------------------------------------------------

async def ws_get_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/config."""
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_cover_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/cover/update."""
    entity_id = msg["entity_id"]
    raw = storage.get_cover_raw(entity_id)
    if raw is None:
        connection.send_error(msg["id"], "not_found", f"Cover '{entity_id}' not found")
        return

    # Reject assignment to a non-existent facade (None clears the assignment).
    if "facade_id" in msg and msg["facade_id"] is not None and msg["facade_id"] not in storage.facades:
        connection.send_error(msg["id"], "not_found", f"Facade '{msg['facade_id']}' not found")
        return

    # Per-cover comfort band (falls back to the global values when unset)
    def _eff_comfort(key: str) -> float:
        value = msg[key] if key in msg else raw.get(key)
        return value if value is not None else getattr(storage, key)

    if _eff_comfort("comfort_temp_min") >= _eff_comfort("comfort_temp_max"):
        connection.send_error(
            msg["id"], "invalid_comfort_range",
            "comfort_temp_min must be lower than comfort_temp_max",
        )
        return

    # Track facade change for bidirectional sync
    old_facade_id = raw.get("facade_id")
    # Track auto_enabled change to mirror the switch entity's status transition
    old_auto_enabled = raw.get("auto_enabled", True)

    # Update only fields present in the message
    for key in _UPDATABLE_COVER_FIELDS:
        if key in msg:
            raw[key] = msg[key]

    # Sync facade.cover_ids if facade_id changed
    new_facade_id = raw.get("facade_id")
    if "facade_id" in msg and new_facade_id != old_facade_id:
        _sync_facade_cover_ids(storage, entity_id, new_facade_id, old_facade_id)

    # Mirror the auto_enabled toggle through the coordinator's status
    # transitions (same path as the HA switch entity). Without this the
    # persisted cover status stays "auto" and the panel keeps showing AUTO
    # after disabling automation; on re-enable the cover would stay MANUAL.
    if "auto_enabled" in msg and msg["auto_enabled"] != old_auto_enabled:
        if msg["auto_enabled"]:
            coordinator.resume_cover(entity_id)
        else:
            coordinator.set_cover_manual(entity_id)

    storage._invalidate_cache()
    await storage.async_save()
    coordinator.refresh_state_tracking()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_cover_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/cover/add."""
    entity_ids = msg["entity_ids"]
    added = False
    for entity_id in entity_ids:
        if entity_id in storage.covers:
            continue
        state = hass.states.get(entity_id)
        name = state.attributes.get("friendly_name", entity_id) if state else entity_id
        cover = CoverConfig(entity_id=entity_id, name=name)
        await storage.async_add_cover(cover, save=False)
        added = True
    if added:
        await storage.async_save()
    coordinator.refresh_state_tracking()
    coordinator.async_sync_entities()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_cover_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/cover/delete."""
    await storage.async_remove_cover(msg["entity_id"])
    coordinator.refresh_state_tracking()
    coordinator.async_sync_entities()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_facade_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/facade/add."""
    name = msg["name"]
    direction = msg.get("direction", "south")
    presets = FACADE_PRESETS.get(direction, FACADE_PRESETS["south"])

    new_cover_ids = msg.get("cover_ids", [])
    unknown = _missing_ids(new_cover_ids, storage.covers)
    if unknown:
        connection.send_error(msg["id"], "not_found", _unknown_refs_msg([], unknown))
        return
    facade_id = _unique_id(_sanitize_id(name), storage.facades)
    facade = Facade(
        id=facade_id,
        name=name,
        azimuth_start=msg.get("azimuth_start", presets["start"]),
        azimuth_end=msg.get("azimuth_end", presets["end"]),
        direction=direction,
        min_elevation=msg.get("min_elevation", 0.0),
        cover_ids=new_cover_ids,
    )
    await storage.async_add_facade(facade, save=False)
    _sync_cover_facade_ids(storage, facade_id, new_cover_ids)
    await storage.async_save()
    coordinator.async_sync_entities()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_facade_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/facade/update."""
    facade_id = msg["facade_id"]
    existing = storage.facades.get(facade_id)
    if existing is None:
        connection.send_error(msg["id"], "not_found", f"Facade '{facade_id}' not found")
        return

    if "cover_ids" in msg:
        unknown = _missing_ids(msg["cover_ids"], storage.covers)
        if unknown:
            connection.send_error(msg["id"], "not_found", _unknown_refs_msg([], unknown))
            return

    new_cover_ids = msg.get("cover_ids", existing.cover_ids)
    updated = Facade(
        id=facade_id,
        name=msg.get("name", existing.name),
        azimuth_start=msg.get("azimuth_start", existing.azimuth_start),
        azimuth_end=msg.get("azimuth_end", existing.azimuth_end),
        direction=msg.get("direction", existing.direction),
        min_elevation=msg.get("min_elevation", existing.min_elevation),
        cover_ids=new_cover_ids,
    )
    await storage.async_add_facade(updated, save=False)
    # Sync cover.facade_id with facade.cover_ids
    _sync_cover_facade_ids(storage, facade_id, new_cover_ids)
    await storage.async_save()
    # Like the other updates: a new azimuth/elevation or name must take
    # effect now, not at the next periodic refresh.
    coordinator.refresh_state_tracking()
    coordinator.async_sync_entities()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_facade_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/facade/delete."""
    facade_id = msg["facade_id"]
    if facade_id not in storage.facades:
        connection.send_error(msg["id"], "not_found", f"Facade '{facade_id}' not found")
        return

    await storage.async_remove_facade(facade_id)
    coordinator.async_sync_entities()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_rule_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/add."""
    name = msg["name"]
    conditions, errors = _parse_conditions(msg.get("conditions", []))
    if errors:
        connection.send_error(msg["id"], "invalid_conditions", "; ".join(errors))
        return

    unknown_f = _missing_ids(msg.get("facade_ids", []), storage.facades)
    unknown_c = _missing_ids(msg.get("cover_ids", []), storage.covers)
    if unknown_f or unknown_c:
        connection.send_error(msg["id"], "not_found", _unknown_refs_msg(unknown_f, unknown_c))
        return

    # New rules belong to every scenario unless told otherwise.
    scenario_ids = list(msg.get("scenario_ids", list(storage.scenarios.keys())))
    unknown_s = _missing_ids(scenario_ids, storage.scenarios)
    if unknown_s:
        connection.send_error(msg["id"], "not_found", f"Unknown scenarios: {', '.join(unknown_s)}")
        return

    rule = Rule(
        id=_unique_id(_sanitize_id(name), storage.rules),
        name=name,
        enabled=msg.get("enabled", True),
        priority=msg.get("priority", 10),
        condition_operator=msg.get("condition_operator", "and"),
        # Without explicit groups the operator applies inside the single group.
        group_operators=list(msg.get("group_operators") or [msg.get("condition_operator", "and")]),
        facade_ids=msg.get("facade_ids", []),
        cover_ids=msg.get("cover_ids", []),
        conditions=conditions,
        target_position=msg.get("target_position", 0),
        target_tilt_position=msg.get("target_tilt_position"),
        scenario_ids=scenario_ids,
        safety=bool(msg.get("safety", False)),
    )
    if "priority" in msg:
        await storage.async_add_rule(rule)
    else:
        # A new rule goes to the bottom of the list with its own priority
        # (a shared default priority made its place depend on the id).
        order = storage.rule_order()
        await storage.async_add_rule(rule, save=False)
        storage.renumber_priorities([*order, rule.id])
        await storage.async_save()
    await _async_prepare_ha_conditions(coordinator)
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_rule_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/update."""
    rule_id = msg["rule_id"]
    existing = storage.rules.get(rule_id)
    if existing is None:
        connection.send_error(msg["id"], "not_found", f"Rule '{rule_id}' not found")
        return

    # Parse conditions if provided
    conditions = existing.conditions
    if "conditions" in msg:
        conditions, errors = _parse_conditions(msg["conditions"])
        if errors:
            connection.send_error(msg["id"], "invalid_conditions", "; ".join(errors))
            return

    unknown_f = _missing_ids(msg["facade_ids"], storage.facades) if "facade_ids" in msg else []
    unknown_c = _missing_ids(msg["cover_ids"], storage.covers) if "cover_ids" in msg else []
    if unknown_f or unknown_c:
        connection.send_error(msg["id"], "not_found", _unknown_refs_msg(unknown_f, unknown_c))
        return

    group_operators = existing.effective_group_operators()
    if "group_operators" in msg:
        group_operators = list(msg["group_operators"]) or ["and"]
    elif "condition_operator" in msg and len(existing.condition_groups()) <= 1:
        # Legacy clients: the operator of a single-group rule is its group's.
        group_operators = [msg["condition_operator"], *group_operators[1:]]

    scenario_ids = existing.scenario_ids
    if "scenario_ids" in msg:
        scenario_ids = list(msg["scenario_ids"])
        unknown_s = _missing_ids(scenario_ids, storage.scenarios)
        if unknown_s:
            connection.send_error(msg["id"], "not_found", f"Unknown scenarios: {', '.join(unknown_s)}")
            return

    # The id follows a new name (only when the name actually changed: an
    # unchanged name keeps whatever id the rule has); references move with it
    name = msg.get("name", existing.name)
    new_id = rule_id
    if name != existing.name:
        new_id = _rule_id_for_name(rule_id, name, storage.rules)
    if new_id != rule_id:
        await storage.async_rename_rule(rule_id, new_id, save=False)
        coordinator.rename_rule_references(rule_id, new_id)
        _LOGGER.info("Rule '%s' renamed: id %s -> %s", name, rule_id, new_id)

    updated = Rule(
        id=new_id,
        name=name,
        enabled=msg.get("enabled", existing.enabled),
        priority=msg.get("priority", existing.priority),
        condition_operator=msg.get("condition_operator", existing.condition_operator),
        facade_ids=msg.get("facade_ids", existing.facade_ids),
        cover_ids=msg.get("cover_ids", existing.cover_ids),
        conditions=conditions,
        target_position=msg.get("target_position", existing.target_position),
        target_tilt_position=msg.get("target_tilt_position", existing.target_tilt_position),
        scenario_ids=scenario_ids,
        group_operators=group_operators,
        safety=bool(msg.get("safety", existing.safety)),
    )
    await storage.async_add_rule(updated)
    await _async_prepare_ha_conditions(coordinator)
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    response = _build_config_response(storage, hass, coordinator)
    if new_id != rule_id:
        response["renamed_rule"] = {"from": rule_id, "to": new_id}
    connection.send_result(msg["id"], response)


async def ws_rule_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/delete."""
    rule_id = msg["rule_id"]
    if rule_id not in storage.rules:
        connection.send_error(msg["id"], "not_found", f"Rule '{rule_id}' not found")
        return

    await storage.async_remove_rule(rule_id)
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_rule_duplicate(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/duplicate.

    The copy starts disabled so it cannot move covers while it is being edited,
    and it inherits the source rule's scenario links (rules_disabled).
    """
    rule_id = msg["rule_id"]
    existing = storage.rules.get(rule_id)
    if existing is None:
        connection.send_error(msg["id"], "not_found", f"Rule '{rule_id}' not found")
        return

    name = (msg.get("name") or "").strip() or f"{existing.name} (copy)"
    data = copy.deepcopy(existing.to_dict())
    data.update(
        id=_unique_id(_sanitize_id(name), storage.rules),
        name=name,
        enabled=False,
    )
    duplicate = Rule.from_dict(data)
    await storage.async_add_rule(duplicate, save=False)

    for scenario in storage.scenarios.values():
        if rule_id in scenario.rules_disabled:
            await storage.async_add_scenario(
                Scenario(
                    id=scenario.id,
                    name=scenario.name,
                    icon=scenario.icon,
                    rules_disabled=[*scenario.rules_disabled, duplicate.id],
                ),
                save=False,
            )

    await storage.async_save()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_rule_reorder(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/reorder.

    Array position determines priority: first = highest priority.
    Top of the list wins over bottom.
    """
    rule_ids: list[str] = list(dict.fromkeys(msg["rule_ids"]))  # drop duplicates
    rules_data = storage._data.get("rules", {})

    unknown = _missing_ids(rule_ids, rules_data)
    if unknown:
        connection.send_error(
            msg["id"], "not_found", f"Unknown rule(s): {', '.join(unknown)}"
        )
        return

    # Rules missing from a partial list keep their relative order below the
    # given ones, so no two rules end up sharing a priority.
    rest = [rid for rid in storage.rule_order() if rid not in rule_ids]
    storage.renumber_priorities([*rule_ids, *rest])

    storage._invalidate_cache()
    await storage.async_save()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


# Rule names: shown in entity states (max 255 chars), keep them readable
RULE_NAME_MAX = 100
_RULE_NAME = vol.All(str, vol.Length(min=1, max=RULE_NAME_MAX))


def _copy_name(base: str, rules: dict[str, Any]) -> str:
    """base, or base plus " 2", " 3"... when a rule already has that name."""
    taken = {getattr(rule, "name", None) for rule in rules.values()}
    if base not in taken:
        return base
    counter = 2
    while f"{base} {counter}" in taken:
        counter += 1
    return f"{base} {counter}"


async def ws_rule_duplicate(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/duplicate.

    The copy is placed right below the original and created active: with the
    same conditions it never wins over the original until it is edited.
    """
    rule_id = msg["rule_id"]
    original = storage.rules.get(rule_id)
    if original is None:
        connection.send_error(msg["id"], "not_found", f"Rule '{rule_id}' not found")
        return
    base = (msg.get("name") or "").strip() or f"{original.name} - copy"
    # Leave room for a " 99" uniqueness suffix within the name limit
    base = base[: RULE_NAME_MAX - 3].rstrip()
    name = _copy_name(base, storage.rules)
    new_id = _unique_id(_sanitize_id(name) or f"{rule_id}_copy", storage.rules)
    await storage.async_duplicate_rule(rule_id, new_id, name)
    await _async_prepare_ha_conditions(coordinator)
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    response = _build_config_response(storage, hass, coordinator)
    response["new_rule_id"] = new_id
    connection.send_result(msg["id"], response)


async def ws_rule_preview_conditions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/preview_conditions.

    Live preview for the rule editor: evaluate each given condition against the
    current state and return whether it matches plus the raw actual value.
    Context-dependent conditions return evaluable=False. Read-only, no mutation.
    """
    conditions, errors = _parse_conditions(msg.get("conditions", []))
    if errors:
        connection.send_error(msg["id"], "invalid_conditions", "; ".join(errors))
        return
    await _async_prepare_ha_conditions(coordinator, conditions)
    results = [coordinator.engine.preview_condition(c) for c in conditions]
    connection.send_result(msg["id"], {"results": results})


async def _async_prepare_ha_conditions(
    coordinator: CoverAutomaticCoordinator, conditions: list[Condition] | None = None
) -> None:
    """Compile native HA conditions so their status/preview is current."""
    engine = getattr(coordinator, "engine", None)
    prepare = getattr(engine, "async_prepare_ha_conditions", None)
    if prepare is None:
        return
    try:
        await prepare(conditions)
    except TypeError:
        pass  # mocked engine in tests


async def ws_condition_validate(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/condition/validate.

    Validates a native Home Assistant condition given as YAML text or as a
    config dict (read-only, nothing is stored). Returns the parsed config, a
    YAML rendering of it, the referenced entities (and those that do not
    exist), the validation error if any, and whether it is met right now.
    """
    yaml_error = None
    if "yaml" in msg:
        text = msg["yaml"]
        config, yaml_error = hac.parse_yaml(text)
    else:
        config = msg.get("config")
        text = hac.dump_yaml(config) if isinstance(config, dict) else ""

    response: dict[str, Any] = {
        "valid": False,
        "config": config,
        "yaml": text,
        "error": None,
        "error_code": None,
        "error_line": None,
        "error_column": None,
        "entities": [],
        "unknown_entities": [],
        "matched": None,
    }
    if yaml_error:
        response.update(
            error=yaml_error["detail"], error_code=yaml_error["code"],
            error_line=yaml_error["line"], error_column=yaml_error["column"],
        )
        connection.send_result(msg["id"], response)
        return

    compiled = await hac.async_compile(hass, config)
    entities = sorted(compiled.entities)
    response.update(
        valid=compiled.valid,
        error=compiled.error,
        error_code=compiled.error_code,
        entities=entities,
        unknown_entities=[e for e in entities if hass.states.get(e) is None],
        matched=hac.evaluate(hass, compiled) if compiled.valid else None,
    )
    connection.send_result(msg["id"], response)


async def ws_scenario_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/scenario/add."""
    name = msg["name"]
    rules_disabled = msg.get("rules_disabled", [])
    unknown = _missing_ids(rules_disabled, storage.rules)
    if unknown:
        connection.send_error(
            msg["id"], "not_found", f"Unknown rule(s): {', '.join(unknown)}"
        )
        return
    scenario = Scenario(
        id=_unique_id(_sanitize_id(name), storage.scenarios),
        name=name,
        icon=msg.get("icon", "mdi:home"),
        rules_disabled=rules_disabled,
    )
    await storage.async_add_scenario(scenario)
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_scenario_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/scenario/update."""
    scenario_id = msg["scenario_id"]
    existing = storage.scenarios.get(scenario_id)
    if existing is None:
        connection.send_error(msg["id"], "not_found", f"Scenario '{scenario_id}' not found")
        return

    if "rules_disabled" in msg:
        unknown = _missing_ids(msg["rules_disabled"], storage.rules)
        if unknown:
            connection.send_error(
                msg["id"], "not_found", f"Unknown rule(s): {', '.join(unknown)}"
            )
            return

    updated = Scenario(
        id=scenario_id,
        name=msg.get("name", existing.name),
        icon=msg.get("icon", existing.icon),
        rules_disabled=msg.get("rules_disabled", existing.rules_disabled),
    )
    if msg.get("activate"):
        storage.active_scenario = scenario_id
    await storage.async_add_scenario(updated)

    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_scenario_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/scenario/delete."""
    scenario_id = msg["scenario_id"]
    if scenario_id not in storage.scenarios:
        connection.send_error(msg["id"], "not_found", f"Scenario '{scenario_id}' not found")
        return

    await storage.async_remove_scenario(scenario_id)
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_settings_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/settings/update."""
    # Validate ALL fields up front so a single rejection does not leave the
    # in-memory state half-updated while disk still has the old values.
    if "active_scenario" in msg:
        # An empty or unknown id is rejected (it would otherwise be stored)
        if not msg["active_scenario"] or msg["active_scenario"] not in storage._data.get("scenarios", {}):
            connection.send_error(
                msg["id"], "not_found", f"Scenario '{msg['active_scenario']}' not found"
            )
            return

    # Cross-field checks against the resulting values (new or existing).
    def _effective(key: str) -> Any:
        return msg[key] if key in msg else getattr(storage, key)

    # Comfort band (invalid_comfort_range), wind and solar deadbands
    # (invalid_wind_hysteresis, invalid_solar_hysteresis): shared with import.
    # Only the checks touching a field actually sent: an inconsistent pair
    # stored by an older version must not block saving anything else.
    cross_error = settings_cross_error(_effective, msg.keys())
    if cross_error:
        connection.send_error(msg["id"], *cross_error)
        return

    old_rotation = storage.house_rotation

    # All validations passed -- now apply atomically.
    for key in _SETTINGS_FIELDS:
        if key in msg:
            setattr(storage, key, msg[key])

    # Facade azimuths are stored as real compass bearings with the house
    # rotation already applied. Rotating the house must therefore rotate the
    # existing facades too, or they keep pointing at the old orientation.
    rotation_delta = storage.house_rotation - old_rotation
    if rotation_delta:
        for facade_raw in storage._data.get("facades", {}).values():
            for az_key in ("azimuth_start", "azimuth_end"):
                facade_raw[az_key] = round(
                    (float(facade_raw.get(az_key, 0.0)) + rotation_delta) % 360, 2
                )
        storage._invalidate_cache()

    await storage.async_save()
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_cover_resume(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/cover/resume."""
    entity_id = msg["entity_id"]
    if entity_id not in storage.covers:
        connection.send_error(msg["id"], "not_found", f"Cover '{entity_id}' not found")
        return
    coordinator.resume_cover(entity_id)
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_get_log(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/log."""
    if not coordinator.log_storage:
        connection.send_result(msg["id"], {"entries": []})
        return
    entries = coordinator.log_storage.get_entries(
        event_type=msg.get("event_type"),
        entity_id=msg.get("entity_id"),
        limit=msg.get("limit", 500),
        include_global=msg.get("include_global", False),
    )
    connection.send_result(msg["id"], {"entries": entries})


async def ws_clear_log(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/log/clear."""
    if coordinator.log_storage:
        await coordinator.log_storage.async_clear()
    connection.send_result(msg["id"], {"success": True})


async def ws_export_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/export -- return raw config as JSON."""
    connection.send_result(msg["id"], {"data": storage.get_export_data()})


_MAX_IMPORT_ENTRIES = 1000


async def ws_import_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/import -- replace config from JSON."""
    data = msg["data"]
    # Guard against oversized payloads that would block the event loop in deepcopy.
    total_entries = sum(
        len(data.get(k, {})) if isinstance(data.get(k), dict) else 0
        for k in ("covers", "rules", "scenarios", "facades")
    )
    if total_entries > _MAX_IMPORT_ENTRIES:
        connection.send_error(msg["id"], "too_large", "Import payload exceeds entry limits")
        return
    try:
        await storage.async_import_data(data)
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "invalid_data", str(err))
        return
    # Let the coordinator drop runtime state that no longer matches the
    # imported configuration (removed covers, wind protection...).
    reconcile = getattr(coordinator, "reconcile_after_import", None)
    if callable(reconcile):
        reconcile()
    coordinator.refresh_state_tracking()
    coordinator.async_sync_entities()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


@callback
def ws_subscribe_updates(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle cover_automatic/subscribe -- push a message on every data update.

    Uses a dispatcher signal (not a bus event) so updates are not written to
    the recorder database, and the subscription survives entry reloads.
    """

    @callback
    def _forward() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], {}))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_DATA_UPDATED, _forward
    )
    connection.send_result(msg["id"])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def async_setup_api(
    hass: HomeAssistant,
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
    version: str = "0",
) -> None:
    """Register all WebSocket commands.

    version comes from the integration manifest, resolved by the caller so no
    file is read inside the event loop.
    """
    global _VERSION
    _VERSION = version

    # Command definitions: (command_type, handler, extra_schema)
    commands: list[tuple[str, Any, dict[str, Any]]] = [
        (
            f"{DOMAIN}/config",
            ws_get_config,
            {},
        ),
        (
            f"{DOMAIN}/cover/update",
            ws_cover_update,
            {
                vol.Required("entity_id"): str,
                vol.Optional("name"): str,
                vol.Optional("facade_id"): vol.Any(str, None),
                vol.Optional("auto_enabled"): bool,
                # None follows the global pause duration
                vol.Optional("pause_duration"): vol.Any(vol.All(int, vol.Range(min=1, max=480)), None),
                vol.Optional("lock_sensor"): _optional_entity_id,
                vol.Optional("lock_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("vent_sensor"): _optional_entity_id,
                vol.Optional("vent_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("inverted"): bool,
                vol.Optional("supports_tilt"): bool,
                vol.Optional("lock_tilt_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("vent_tilt_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("inverted_tilt"): bool,
                vol.Optional("indoor_temp_sensor"): _optional_entity_id,
                vol.Optional("comfort_temp_min"): _COVER_COMFORT_TEMP,
                vol.Optional("comfort_temp_max"): _COVER_COMFORT_TEMP,
                # Tri-state: None follows the global setting
                vol.Optional("preemptive_shading"): vol.Any(bool, None),
                vol.Optional("sun_heating_ignore"): vol.Any(bool, None),
                vol.Optional("pause_resume_on_match"): vol.Any(bool, None),
                vol.Optional("sun_neutral_ignore"): vol.Any(bool, None),
                vol.Optional("lock_hold_position"): bool,
                vol.Optional("min_position_change"): vol.Any(vol.All(int, vol.Range(min=1, max=50)), None),
                vol.Optional("min_time_between_changes"): vol.Any(vol.All(int, vol.Range(min=60, max=3600)), None),
                vol.Optional("travel_time"): vol.Any(vol.All(int, vol.Range(min=1, max=300)), None),
                # Only reset is allowed: the measured value is learned by the coordinator
                vol.Optional("measured_travel_time"): None,
                vol.Optional("comfort_temp_min_entity"): _optional_entity_id,
                vol.Optional("comfort_temp_max_entity"): _optional_entity_id,
                vol.Optional("occupancy_sensor"): _optional_entity_id,
                vol.Optional("occupancy_states"): vol.Any(None, vol.All(str, vol.Length(max=200))),
            },
        ),
        (
            f"{DOMAIN}/cover/add",
            ws_cover_add,
            {
                vol.Required("entity_ids"): [cv.entity_domain("cover")],
            },
        ),
        (
            f"{DOMAIN}/cover/delete",
            ws_cover_delete,
            {
                vol.Required("entity_id"): str,
            },
        ),
        (
            f"{DOMAIN}/facade/add",
            ws_facade_add,
            {
                vol.Required("name"): str,
                vol.Optional("direction", default="south"): str,
                vol.Optional("azimuth_start"): _AZIMUTH,
                vol.Optional("azimuth_end"): _AZIMUTH,
                vol.Optional("min_elevation"): _ELEVATION,
                vol.Optional("cover_ids"): [str],
            },
        ),
        (
            f"{DOMAIN}/facade/update",
            ws_facade_update,
            {
                vol.Required("facade_id"): str,
                vol.Optional("name"): str,
                vol.Optional("direction"): str,
                vol.Optional("azimuth_start"): _AZIMUTH,
                vol.Optional("azimuth_end"): _AZIMUTH,
                vol.Optional("min_elevation"): _ELEVATION,
                vol.Optional("cover_ids"): [str],
            },
        ),
        (
            f"{DOMAIN}/facade/delete",
            ws_facade_delete,
            {
                vol.Required("facade_id"): str,
            },
        ),
        (
            f"{DOMAIN}/rule/add",
            ws_rule_add,
            {
                vol.Required("name"): _RULE_NAME,
                vol.Optional("enabled"): bool,
                vol.Optional("priority"): int,
                vol.Optional("condition_operator"): vol.In(["and", "or"]),
                vol.Optional("group_operators"): vol.All(
                    [vol.In(["and", "or"])], vol.Length(max=MAX_CONDITION_GROUPS)
                ),
                vol.Optional("facade_ids"): [str],
                vol.Optional("cover_ids"): [str],
                vol.Optional("conditions"): list,
                vol.Optional("target_position"): vol.All(int, vol.Range(min=0, max=100)),
                vol.Optional("target_tilt_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("scenario_ids"): [str],
                vol.Optional("safety"): bool,
            },
        ),
        (
            f"{DOMAIN}/rule/update",
            ws_rule_update,
            {
                vol.Required("rule_id"): str,
                vol.Optional("name"): _RULE_NAME,
                vol.Optional("enabled"): bool,
                vol.Optional("priority"): int,
                vol.Optional("condition_operator"): vol.In(["and", "or"]),
                vol.Optional("group_operators"): vol.All(
                    [vol.In(["and", "or"])], vol.Length(max=MAX_CONDITION_GROUPS)
                ),
                vol.Optional("facade_ids"): [str],
                vol.Optional("cover_ids"): [str],
                vol.Optional("conditions"): list,
                vol.Optional("target_position"): vol.All(int, vol.Range(min=0, max=100)),
                vol.Optional("target_tilt_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("scenario_ids"): [str],
                vol.Optional("safety"): bool,
            },
        ),
        (
            f"{DOMAIN}/rule/delete",
            ws_rule_delete,
            {
                vol.Required("rule_id"): str,
            },
        ),
        (
            f"{DOMAIN}/rule/duplicate",
            ws_rule_duplicate,
            {
                vol.Required("rule_id"): str,
<<<<<<< Updated upstream
                vol.Optional("name"): str,
=======
                vol.Optional("name"): vol.All(str, vol.Length(max=200)),  # truncated below
>>>>>>> Stashed changes
            },
        ),
        (
            f"{DOMAIN}/rule/reorder",
            ws_rule_reorder,
            {
                vol.Required("rule_ids"): [str],
            },
        ),
        (
            f"{DOMAIN}/rule/preview_conditions",
            ws_rule_preview_conditions,
            {
                vol.Optional("conditions"): list,
            },
        ),
        (
            f"{DOMAIN}/condition/validate",
            ws_condition_validate,
            {
                vol.Exclusive("yaml", "source"): str,
                vol.Exclusive("config", "source"): vol.Any(dict, None),
            },
        ),
        (
            f"{DOMAIN}/scenario/add",
            ws_scenario_add,
            {
                vol.Required("name"): str,
                vol.Optional("icon"): str,
                vol.Optional("rules_disabled"): [str],
            },
        ),
        (
            f"{DOMAIN}/scenario/update",
            ws_scenario_update,
            {
                vol.Required("scenario_id"): str,
                vol.Optional("name"): str,
                vol.Optional("icon"): str,
                vol.Optional("rules_disabled"): [str],
                vol.Optional("activate"): bool,
            },
        ),
        (
            f"{DOMAIN}/scenario/delete",
            ws_scenario_delete,
            {
                vol.Required("scenario_id"): str,
            },
        ),
        (
            f"{DOMAIN}/settings/update",
            ws_settings_update,
            {
                # Same bounds as the import (storage.SETTING_VALIDATORS)
                **{vol.Optional(key): validator for key, validator in SETTING_VALIDATORS.items()},
                vol.Optional("active_scenario"): str,
            },
        ),
        (
            f"{DOMAIN}/cover/resume",
            ws_cover_resume,
            {
                vol.Required("entity_id"): str,
            },
        ),
        (
            f"{DOMAIN}/log",
            ws_get_log,
            {
                vol.Optional("event_type"): str,
                vol.Optional("entity_id"): str,
                vol.Optional("include_global"): bool,
                vol.Optional("limit"): vol.All(int, vol.Range(min=1, max=2000)),
            },
        ),
        (
            f"{DOMAIN}/log/clear",
            ws_clear_log,
            {},
        ),
        (
            f"{DOMAIN}/export",
            ws_export_config,
            {},
        ),
        (
            f"{DOMAIN}/import",
            ws_import_config,
            {
                vol.Required("data"): dict,
            },
        ),
    ]

    # Read-only commands stay accessible to all authenticated HA users.
    # Every other command (writes, log clear, export, import, resume) requires
    # admin privileges -- the sidebar panel is admin-only, so the WS API must
    # mirror that gate to prevent privilege escalation via Long-Lived Tokens.
    read_only_commands = frozenset({f"{DOMAIN}/config", f"{DOMAIN}/log"})

    for command_type, handler_fn, extra_schema in commands:
        # Closure to bind storage and coordinator with async_response decorator
        def _make_handler(fn: Any, ct: str) -> Any:
            @websocket_api.async_response
            async def _handler(
                hass: HomeAssistant,
                connection: websocket_api.ActiveConnection,
                msg: dict[str, Any],
            ) -> None:
                # After the entry was unloaded (and not set up again, which
                # re-registers these commands) the bound storage/coordinator
                # are dead: refuse instead of mutating and saving them.
                entry = getattr(coordinator, "config_entry", None)
                state = getattr(entry, "state", None)
                if isinstance(state, ConfigEntryState) and state is not ConfigEntryState.LOADED:
                    connection.send_error(
                        msg["id"], "not_loaded", "CoverAutomatic is not loaded"
                    )
                    return
                await fn(hass, connection, msg, storage, coordinator)
            if ct not in read_only_commands:
                return websocket_api.require_admin(_handler)
            return _handler

        schema = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
            {vol.Required("type"): command_type, **extra_schema}
        )
        websocket_api.async_register_command(
            hass, command_type, _make_handler(handler_fn, command_type), schema
        )

    websocket_api.async_register_command(
        hass,
        f"{DOMAIN}/subscribe",
        ws_subscribe_updates,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
            {vol.Required("type"): f"{DOMAIN}/subscribe"}
        ),
    )
