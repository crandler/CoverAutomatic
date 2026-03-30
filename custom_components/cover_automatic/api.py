"""WebSocket API for CoverAutomatic config panel."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN, FACADE_PRESETS
from .models import Condition, Facade, Rule, Scenario

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
    "inverted_tilt", "min_position_change", "min_time_between_changes",
)

# Settings fields that can be updated via WS API
_SETTINGS_FIELDS = (
    "outdoor_temp_sensor", "indoor_temp_sensor", "weather_entity",
    "comfort_temp_min", "comfort_temp_max", "active_scenario",
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


def _build_config_response(storage: CoverAutomaticStorage) -> dict[str, Any]:
    """Build full config response dict from storage."""
    return {
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
        },
    }


def _parse_conditions(raw: list[dict[str, Any]]) -> list[Condition]:
    """Parse condition dicts, skipping invalid ones with a warning."""
    conditions: list[Condition] = []
    for item in raw:
        try:
            conditions.append(Condition.from_dict(item))
        except (ValueError, KeyError) as err:
            _LOGGER.warning("Skipping invalid condition: %s", err)
    return conditions


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
    connection.send_result(msg["id"], _build_config_response(storage))


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

    # Update only fields present in the message
    for key in _UPDATABLE_COVER_FIELDS:
        if key in msg:
            raw[key] = msg[key]

    storage._invalidate_cache()
    await storage.async_save()
    coordinator.refresh_state_tracking()
    connection.send_result(msg["id"], _build_config_response(storage))


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

    facade = Facade(
        id=_sanitize_id(name),
        name=name,
        azimuth_start=msg.get("azimuth_start", presets["start"]),
        azimuth_end=msg.get("azimuth_end", presets["end"]),
        direction=direction,
        min_elevation=msg.get("min_elevation", 0.0),
        cover_ids=msg.get("cover_ids", []),
    )
    await storage.async_add_facade(facade)
    connection.send_result(msg["id"], _build_config_response(storage))


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

    updated = Facade(
        id=facade_id,
        name=msg.get("name", existing.name),
        azimuth_start=msg.get("azimuth_start", existing.azimuth_start),
        azimuth_end=msg.get("azimuth_end", existing.azimuth_end),
        direction=msg.get("direction", existing.direction),
        min_elevation=msg.get("min_elevation", existing.min_elevation),
        cover_ids=msg.get("cover_ids", existing.cover_ids),
    )
    await storage.async_add_facade(updated)
    connection.send_result(msg["id"], _build_config_response(storage))


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
    connection.send_result(msg["id"], _build_config_response(storage))


async def ws_rule_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/add."""
    name = msg["name"]
    conditions = _parse_conditions(msg.get("conditions", []))

    rule = Rule(
        id=_sanitize_id(name),
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
    connection.send_result(msg["id"], _build_config_response(storage))


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
        conditions = _parse_conditions(msg["conditions"])

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
    connection.send_result(msg["id"], _build_config_response(storage))


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
    connection.send_result(msg["id"], _build_config_response(storage))


async def ws_rule_reorder(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    storage: CoverAutomaticStorage,
    coordinator: CoverAutomaticCoordinator,
) -> None:
    """Handle cover_automatic/rule/reorder.

    Array position determines priority: first = highest (10), then 20, 30, ...
    """
    rule_ids: list[str] = msg["rule_ids"]
    rules_data = storage._data.get("rules", {})

    for idx, rid in enumerate(rule_ids):
        if rid in rules_data:
            rules_data[rid]["priority"] = (idx + 1) * 10

    storage._invalidate_cache()
    await storage.async_save()
    connection.send_result(msg["id"], _build_config_response(storage))


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
        id=_sanitize_id(name),
        name=name,
        icon=msg.get("icon", "mdi:home"),
        rules_disabled=msg.get("rules_disabled", []),
    )
    await storage.async_add_scenario(scenario)
    connection.send_result(msg["id"], _build_config_response(storage))


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
    await storage.async_add_scenario(updated)

    if msg.get("activate"):
        storage.active_scenario = scenario_id
        await storage.async_save()

    connection.send_result(msg["id"], _build_config_response(storage))


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
    connection.send_result(msg["id"], _build_config_response(storage))


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
            setattr(storage, key, msg[key])

    await storage.async_save()
    coordinator.refresh_state_tracking()
    connection.send_result(msg["id"], _build_config_response(storage))


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
                vol.Optional("pause_duration"): vol.All(int, vol.Range(min=0, max=480)),
                vol.Optional("lock_sensor"): vol.Any(str, None),
                vol.Optional("lock_position"): vol.All(int, vol.Range(min=0, max=100)),
                vol.Optional("vent_sensor"): vol.Any(str, None),
                vol.Optional("vent_position"): vol.All(int, vol.Range(min=0, max=100)),
                vol.Optional("inverted"): bool,
                vol.Optional("supports_tilt"): bool,
                vol.Optional("lock_tilt_position"): vol.Any(int, None),
                vol.Optional("vent_tilt_position"): vol.Any(int, None),
                vol.Optional("inverted_tilt"): bool,
                vol.Optional("min_position_change"): vol.All(int, vol.Range(min=1, max=50)),
                vol.Optional("min_time_between_changes"): vol.All(int, vol.Range(min=60, max=3600)),
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
                vol.Optional("outdoor_temp_sensor"): vol.Any(str, None),
                vol.Optional("indoor_temp_sensor"): vol.Any(str, None),
                vol.Optional("weather_entity"): vol.Any(str, None),
                vol.Optional("comfort_temp_min"): vol.Coerce(float),
                vol.Optional("comfort_temp_max"): vol.Coerce(float),
                vol.Optional("active_scenario"): str,
            },
        ),
    ]

    for command_type, handler_fn, extra_schema in commands:
        # Closure to bind storage and coordinator
        def _make_handler(fn: Any) -> Any:
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
            hass, _make_handler(handler_fn), schema
        )
