"""WebSocket API for CoverAutomatic config panel."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN, FACADE_PRESETS
from .models import Condition, CoverConfig, Facade, Rule, Scenario

_MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text())
_VERSION = _MANIFEST["version"]

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
    "min_position_change", "min_time_between_changes",
)

# Settings fields that can be updated via WS API
_SETTINGS_FIELDS = (
    "enabled",
    "outdoor_temp_sensor", "indoor_temp_sensor", "weather_entity",
    "comfort_temp_min", "comfort_temp_max", "comfort_hysteresis", "pause_duration",
    "lock_position", "vent_position", "lock_tilt_position", "vent_tilt_position",
    "min_position_change", "min_time_between_changes",
    "house_rotation", "active_scenario",
    "workday_sensor",
    "wind_sensor", "wind_speed_threshold", "wind_speed_hysteresis",
    "command_stagger",
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
    result = result.lower()
    result = re.sub(r"[^a-z0-9]", "_", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")
    return result or "unnamed"


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
    for idx, item in enumerate(raw):
        try:
            conditions.append(Condition.from_dict(item))
        except (ValueError, KeyError) as err:
            errors.append(f"Condition {idx}: {err}")
    return conditions, errors


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

    # Track facade change for bidirectional sync
    old_facade_id = raw.get("facade_id")

    # Update only fields present in the message
    for key in _UPDATABLE_COVER_FIELDS:
        if key in msg:
            raw[key] = msg[key]

    # Sync facade.cover_ids if facade_id changed
    new_facade_id = raw.get("facade_id")
    if "facade_id" in msg and new_facade_id != old_facade_id:
        _sync_facade_cover_ids(storage, entity_id, new_facade_id, old_facade_id)

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

    rule = Rule(
        id=_unique_id(_sanitize_id(name), storage.rules),
        name=name,
        enabled=msg.get("enabled", True),
        priority=msg.get("priority", 10),
        condition_operator=msg.get("condition_operator", "and"),
        facade_ids=msg.get("facade_ids", []),
        cover_ids=msg.get("cover_ids", []),
        conditions=conditions,
        target_position=msg.get("target_position", 0),
        target_tilt_position=msg.get("target_tilt_position"),
    )
    await storage.async_add_rule(rule)
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

    updated = Rule(
        id=rule_id,
        name=msg.get("name", existing.name),
        enabled=msg.get("enabled", existing.enabled),
        priority=msg.get("priority", existing.priority),
        condition_operator=msg.get("condition_operator", existing.condition_operator),
        facade_ids=msg.get("facade_ids", existing.facade_ids),
        cover_ids=msg.get("cover_ids", existing.cover_ids),
        conditions=conditions,
        target_position=msg.get("target_position", existing.target_position),
        target_tilt_position=msg.get("target_tilt_position", existing.target_tilt_position),
    )
    await storage.async_add_rule(updated)
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


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
    rule_ids: list[str] = msg["rule_ids"]
    rules_data = storage._data.get("rules", {})
    total = len(rule_ids)

    for idx, rid in enumerate(rule_ids):
        if rid in rules_data:
            rules_data[rid]["priority"] = (total - idx) * 10

    storage._invalidate_cache()
    await storage.async_save()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_scenario_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/scenario/add."""
    name = msg["name"]
    scenario = Scenario(
        id=_unique_id(_sanitize_id(name), storage.scenarios),
        name=name,
        icon=msg.get("icon", "mdi:home"),
        rules_disabled=msg.get("rules_disabled", []),
    )
    await storage.async_add_scenario(scenario)
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

    updated = Scenario(
        id=scenario_id,
        name=msg.get("name", existing.name),
        icon=msg.get("icon", existing.icon),
        rules_disabled=msg.get("rules_disabled", existing.rules_disabled),
    )
    if msg.get("activate"):
        storage.active_scenario = scenario_id
    await storage.async_add_scenario(updated)

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
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


async def ws_settings_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/settings/update."""
    for key in _SETTINGS_FIELDS:
        if key in msg:
            if key == "active_scenario" and msg[key]:
                if msg[key] not in storage._data.get("scenarios", {}):
                    connection.send_error(msg["id"], "not_found", f"Scenario '{msg[key]}' not found")
                    return
            setattr(storage, key, msg[key])

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
    connection.send_result(msg["id"], {"data": storage.get_raw_data()})


async def ws_import_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/import -- replace config from JSON."""
    data = msg["data"]
    try:
        await storage.async_import_data(data)
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "invalid_data", str(err))
        return
    coordinator.refresh_state_tracking()
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], _build_config_response(storage, hass, coordinator))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def async_setup_api(
    hass: HomeAssistant,
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Register all WebSocket commands."""

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
                vol.Optional("pause_duration"): vol.Any(vol.All(int, vol.Range(min=0, max=480)), None),
                vol.Optional("lock_sensor"): vol.Any(str, None),
                vol.Optional("lock_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("vent_sensor"): vol.Any(str, None),
                vol.Optional("vent_position"): vol.Any(vol.All(int, vol.Range(min=0, max=100)), None),
                vol.Optional("inverted"): bool,
                vol.Optional("supports_tilt"): bool,
                vol.Optional("lock_tilt_position"): vol.Any(int, None),
                vol.Optional("vent_tilt_position"): vol.Any(int, None),
                vol.Optional("inverted_tilt"): bool,
                vol.Optional("indoor_temp_sensor"): vol.Any(str, None),
                vol.Optional("comfort_temp_min"): vol.Any(vol.Coerce(float), None),
                vol.Optional("comfort_temp_max"): vol.Any(vol.Coerce(float), None),
                vol.Optional("min_position_change"): vol.Any(vol.All(int, vol.Range(min=1, max=50)), None),
                vol.Optional("min_time_between_changes"): vol.Any(vol.All(int, vol.Range(min=60, max=3600)), None),
            },
        ),
        (
            f"{DOMAIN}/cover/add",
            ws_cover_add,
            {
                vol.Required("entity_ids"): [str],
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
                vol.Optional("azimuth_start"): vol.Coerce(float),
                vol.Optional("azimuth_end"): vol.Coerce(float),
                vol.Optional("min_elevation"): vol.Coerce(float),
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
                vol.Optional("azimuth_start"): vol.Coerce(float),
                vol.Optional("azimuth_end"): vol.Coerce(float),
                vol.Optional("min_elevation"): vol.Coerce(float),
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
                vol.Required("name"): str,
                vol.Optional("enabled"): bool,
                vol.Optional("priority"): int,
                vol.Optional("condition_operator"): str,
                vol.Optional("facade_ids"): [str],
                vol.Optional("cover_ids"): [str],
                vol.Optional("conditions"): list,
                vol.Optional("target_position"): int,
                vol.Optional("target_tilt_position"): vol.Any(int, None),
            },
        ),
        (
            f"{DOMAIN}/rule/update",
            ws_rule_update,
            {
                vol.Required("rule_id"): str,
                vol.Optional("name"): str,
                vol.Optional("enabled"): bool,
                vol.Optional("priority"): int,
                vol.Optional("condition_operator"): str,
                vol.Optional("facade_ids"): [str],
                vol.Optional("cover_ids"): [str],
                vol.Optional("conditions"): list,
                vol.Optional("target_position"): int,
                vol.Optional("target_tilt_position"): vol.Any(int, None),
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
            f"{DOMAIN}/rule/reorder",
            ws_rule_reorder,
            {
                vol.Required("rule_ids"): [str],
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
                vol.Optional("enabled"): bool,
                vol.Optional("outdoor_temp_sensor"): vol.Any(str, None),
                vol.Optional("indoor_temp_sensor"): vol.Any(str, None),
                vol.Optional("weather_entity"): vol.Any(str, None),
                vol.Optional("comfort_temp_min"): vol.Coerce(float),
                vol.Optional("comfort_temp_max"): vol.Coerce(float),
                vol.Optional("comfort_hysteresis"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
                vol.Optional("pause_duration"): vol.All(vol.Coerce(int), vol.Range(min=1, max=480)),
                vol.Optional("lock_position"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional("vent_position"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional("lock_tilt_position"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=0, max=100)), None),
                vol.Optional("vent_tilt_position"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=0, max=100)), None),
                vol.Optional("min_position_change"): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                vol.Optional("min_time_between_changes"): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Optional("house_rotation"): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
                vol.Optional("active_scenario"): str,
                vol.Optional("workday_sensor"): vol.Any(str, None),
                vol.Optional("wind_sensor"): vol.Any(str, None),
                vol.Optional("wind_speed_threshold"): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("wind_speed_hysteresis"): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("command_stagger"): vol.All(vol.Coerce(float), vol.Range(min=0, max=2.0)),
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

    for command_type, handler_fn, extra_schema in commands:
        # Closure to bind storage and coordinator with async_response decorator
        def _make_handler(fn: Any) -> Any:
            @websocket_api.async_response
            async def _handler(
                hass: HomeAssistant,
                connection: websocket_api.ActiveConnection,
                msg: dict[str, Any],
            ) -> None:
                await fn(hass, connection, msg, storage, coordinator)
            return _handler

        schema = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
            {vol.Required("type"): command_type, **extra_schema}
        )
        websocket_api.async_register_command(
            hass, command_type, _make_handler(handler_fn), schema
        )
