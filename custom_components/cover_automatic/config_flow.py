"""Config flow for CoverAutomatic integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, FACADE_PRESETS
from .models import Condition, ConditionType, Facade, Rule, Scenario

_LOGGER = logging.getLogger(__name__)

_DIRECTION_OPTIONS = [
    {"value": "north", "label": "Nord"},
    {"value": "east", "label": "Ost"},
    {"value": "south", "label": "S\u00fcd"},
    {"value": "west", "label": "West"},
]

# Umlaut replacement map for ID sanitization
# Max conditions per rule (prevent unbounded growth)
MAX_CONDITIONS_PER_RULE = 20

_UMLAUT_MAP = {
    "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue", "\u00df": "ss",
    "\u00c4": "ae", "\u00d6": "oe", "\u00dc": "ue",
}


def _sanitize_id(name: str) -> str:
    """Sanitize name to a valid ID (alphanumeric + underscore only)."""
    result = name.lower().strip()
    for char, replacement in _UMLAUT_MAP.items():
        result = result.replace(char, replacement)
    result = re.sub(r"[^a-z0-9_]", "_", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")
    return result or "unnamed"


class CoverAutomaticConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CoverAutomatic."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._data: dict[str, Any] = {}
        self._facades: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data["name"] = user_input.get("name", "CoverAutomatic")
            return await self.async_step_facades()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default="CoverAutomatic"): vol.All(str, vol.Length(max=255)),
                }
            ),
            errors=errors,
        )

    async def async_step_facades(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle facade configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("add_facade"):
                facade_name = user_input.get("facade_name", "")
                facade_direction = user_input.get("facade_direction", "south")

                if facade_name:
                    preset = FACADE_PRESETS.get(facade_direction, FACADE_PRESETS["south"])
                    self._facades.append(
                        {
                            "id": _sanitize_id(facade_name),
                            "name": facade_name,
                            "direction": facade_direction,
                            "azimuth_start": preset["start"],
                            "azimuth_end": preset["end"],
                        }
                    )

                return await self.async_step_facades()

            if user_input.get("done"):
                self._data["facades"] = self._facades
                return await self.async_step_covers()

        facade_list = ", ".join([f["name"] for f in self._facades]) or "None"

        return self.async_show_form(
            step_id="facades",
            data_schema=vol.Schema(
                {
                    vol.Optional("facade_name"): vol.All(str, vol.Length(max=255)),
                    vol.Optional("facade_direction", default="south"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_DIRECTION_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("add_facade", default=False): bool,
                    vol.Optional("done", default=False): bool,
                }
            ),
            description_placeholders={"facades": facade_list},
            errors=errors,
        )

    async def async_step_covers(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle cover selection."""
        errors: dict[str, str] = {}

        cover_entities = [
            state.entity_id
            for state in self.hass.states.async_all("cover")
        ]

        if not cover_entities:
            return self.async_abort(reason="no_covers")

        if user_input is not None:
            self._data["covers"] = user_input.get("covers", [])
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="covers",
            data_schema=vol.Schema(
                {
                    vol.Required("covers"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="cover",
                            multiple=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle sensor configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data["outdoor_temp_sensor"] = user_input.get("outdoor_temp_sensor")
            return self.async_create_entry(
                title=self._data.get("name", "CoverAutomatic"),
                data=self._data,
            )

        temp_sensors = [
            state.entity_id
            for state in self.hass.states.async_all("sensor")
            if "temperature" in state.entity_id.lower()
            or state.attributes.get("device_class") == "temperature"
        ]

        schema: dict[Any, Any] = {}
        if temp_sensors:
            schema[vol.Optional("outdoor_temp_sensor")] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            )

        if not schema:
            return self.async_create_entry(
                title=self._data.get("name", "CoverAutomatic"),
                data=self._data,
            )

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> CoverAutomaticOptionsFlow:
        """Get the options flow for this handler."""
        return CoverAutomaticOptionsFlow()


class CoverAutomaticOptionsFlow(OptionsFlow):
    """Handle options flow for CoverAutomatic."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._selected_cover: str | None = None
        self._selected_facade: str | None = None
        self._selected_rule: str | None = None
        self._selected_scenario: str | None = None

    def _get_storage(self):
        """Get storage from config entry runtime_data."""
        runtime_data = getattr(self.config_entry, "runtime_data", None)
        if runtime_data:
            return runtime_data.storage
        return None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show main menu."""
        if user_input is not None:
            selected = user_input.get("menu_option")
            if selected == "general":
                return await self.async_step_general()
            elif selected == "facades":
                return await self.async_step_facades()
            elif selected == "rules":
                return await self.async_step_rules()
            elif selected == "scenarios":
                return await self.async_step_scenarios()
            elif selected and selected.startswith("cover:"):
                self._selected_cover = selected[6:]
                return await self.async_step_cover_details()

        # Build menu options
        menu_options = [
            {"value": "general", "label": "Allgemeine Einstellungen"},
            {"value": "facades", "label": "Fassaden verwalten"},
            {"value": "rules", "label": "Regeln verwalten"},
            {"value": "scenarios", "label": "Szenarien verwalten"},
        ]

        storage = self._get_storage()
        if storage:
            for entity_id in storage.covers:
                cover = storage.covers[entity_id]
                menu_options.append({
                    "value": f"cover:{entity_id}",
                    "label": f"Cover: {cover.name or entity_id}",
                })

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("menu_option"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=menu_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_general(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle general settings."""
        storage = self._get_storage()

        if user_input is not None:
            # Validate comfort temp range
            temp_min = user_input.get("comfort_temp_min", 21.0)
            temp_max = user_input.get("comfort_temp_max", 25.0)
            if temp_min >= temp_max:
                return self.async_show_form(
                    step_id="general",
                    data_schema=vol.Schema(
                        {
                            vol.Optional("scan_interval", default=user_input.get("scan_interval", 60)): vol.All(
                                vol.Coerce(int), vol.Range(min=10, max=600)
                            ),
                            vol.Optional(
                                "outdoor_temp_sensor",
                                description={"suggested_value": user_input.get("outdoor_temp_sensor")},
                            ): selector.EntitySelector(
                                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                            ),
                            vol.Optional(
                                "indoor_temp_sensor",
                                description={"suggested_value": user_input.get("indoor_temp_sensor")},
                            ): selector.EntitySelector(
                                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                            ),
                            vol.Optional(
                                "weather_entity",
                                description={"suggested_value": user_input.get("weather_entity")},
                            ): selector.EntitySelector(
                                selector.EntitySelectorConfig(domain="weather")
                            ),
                            vol.Optional("comfort_temp_min", default=temp_min): vol.All(
                                vol.Coerce(float), vol.Range(min=10, max=30)
                            ),
                            vol.Optional("comfort_temp_max", default=temp_max): vol.All(
                                vol.Coerce(float), vol.Range(min=15, max=35)
                            ),
                        }
                    ),
                    errors={"comfort_temp_min": "min_must_be_less_than_max"},
                )

            # Save to options (scan_interval) and storage (sensors)
            new_options = dict(self.config_entry.options)
            new_options["scan_interval"] = user_input.get("scan_interval", 60)

            if storage:
                storage.outdoor_temp_sensor = user_input.get("outdoor_temp_sensor")
                storage.indoor_temp_sensor = user_input.get("indoor_temp_sensor")
                storage.weather_entity = user_input.get("weather_entity")
                storage.comfort_temp_min = temp_min
                storage.comfort_temp_max = temp_max
                await storage.async_save()

            return self.async_create_entry(title="", data=new_options)

        # Current values
        current_scan = self.config_entry.options.get("scan_interval", 60)
        current_outdoor = storage.outdoor_temp_sensor if storage else None
        current_indoor = storage.indoor_temp_sensor if storage else None
        current_weather = storage.weather_entity if storage else None
        current_comfort_min = storage.comfort_temp_min if storage else 21.0
        current_comfort_max = storage.comfort_temp_max if storage else 25.0

        return self.async_show_form(
            step_id="general",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=current_scan,
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                    vol.Optional(
                        "outdoor_temp_sensor",
                        description={"suggested_value": current_outdoor},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        )
                    ),
                    vol.Optional(
                        "indoor_temp_sensor",
                        description={"suggested_value": current_indoor},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        )
                    ),
                    vol.Optional(
                        "weather_entity",
                        description={"suggested_value": current_weather},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="weather",
                        )
                    ),
                    vol.Optional(
                        "comfort_temp_min",
                        default=current_comfort_min,
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Optional(
                        "comfort_temp_max",
                        default=current_comfort_max,
                    ): vol.All(vol.Coerce(float), vol.Range(min=15, max=35)),
                }
            ),
        )

    async def async_step_cover_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle cover-specific settings."""
        storage = self._get_storage()
        entity_id = self._selected_cover

        if not storage or not entity_id:
            return await self.async_step_init()

        cover_raw = storage.get_cover_raw(entity_id)
        if not cover_raw:
            return await self.async_step_init()

        if user_input is not None:
            # Update cover in storage
            cover_raw["facade_id"] = user_input.get("facade_id") or None
            cover_raw["lock_sensor"] = user_input.get("lock_sensor") or None
            cover_raw["lock_position"] = user_input.get("lock_position", 100)
            cover_raw["vent_sensor"] = user_input.get("vent_sensor") or None
            cover_raw["vent_position"] = user_input.get("vent_position", 30)
            cover_raw["inverted"] = user_input.get("inverted", False)
            cover_raw["supports_tilt"] = user_input.get("supports_tilt", False)
            cover_raw["lock_tilt_position"] = user_input.get("lock_tilt_position")
            cover_raw["vent_tilt_position"] = user_input.get("vent_tilt_position")
            cover_raw["inverted_tilt"] = user_input.get("inverted_tilt", False)
            cover_raw["min_position_change"] = user_input.get("min_position_change", 5)
            cover_raw["min_time_between_changes"] = user_input.get("min_time_between_changes", 300)
            cover_raw["pause_duration"] = user_input.get("pause_duration", 120)
            storage._invalidate_cache()
            await storage.async_save()

            # Refresh coordinator state tracking
            runtime_data = getattr(self.config_entry, "runtime_data", None)
            if runtime_data:
                runtime_data.coordinator.refresh_state_tracking()

            return self.async_create_entry(title="", data=self.config_entry.options)

        # Build facade options
        facade_options = [{"value": "", "label": "-- Keine --"}]
        for facade_id, facade in storage.facades.items():
            facade_options.append({"value": facade_id, "label": facade.name})

        # Current values
        current_facade = cover_raw.get("facade_id") or ""
        current_lock_sensor = cover_raw.get("lock_sensor")
        current_lock_position = cover_raw.get("lock_position", 100)
        current_vent_sensor = cover_raw.get("vent_sensor")
        current_vent_position = cover_raw.get("vent_position", 30)
        current_inverted = cover_raw.get("inverted", False)
        current_supports_tilt = cover_raw.get("supports_tilt", False)
        current_lock_tilt = cover_raw.get("lock_tilt_position")
        current_vent_tilt = cover_raw.get("vent_tilt_position")
        current_inverted_tilt = cover_raw.get("inverted_tilt", False)
        current_min_change = cover_raw.get("min_position_change", 5)
        current_min_time = cover_raw.get("min_time_between_changes", 300)
        current_pause = cover_raw.get("pause_duration", 120)

        return self.async_show_form(
            step_id="cover_details",
            description_placeholders={"cover_name": cover_raw.get("name", entity_id)},
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "facade_id",
                        default=current_facade,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=facade_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "lock_sensor",
                        description={"suggested_value": current_lock_sensor},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="binary_sensor",
                        )
                    ),
                    vol.Optional(
                        "lock_position",
                        default=current_lock_position,
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                    vol.Optional(
                        "vent_sensor",
                        description={"suggested_value": current_vent_sensor},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="binary_sensor",
                        )
                    ),
                    vol.Optional(
                        "vent_position",
                        default=current_vent_position,
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                    vol.Optional(
                        "inverted",
                        default=current_inverted,
                    ): bool,
                    vol.Optional(
                        "supports_tilt",
                        default=current_supports_tilt,
                    ): bool,
                    vol.Optional(
                        "lock_tilt_position",
                        description={"suggested_value": current_lock_tilt},
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                    vol.Optional(
                        "vent_tilt_position",
                        description={"suggested_value": current_vent_tilt},
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                    vol.Optional(
                        "inverted_tilt",
                        default=current_inverted_tilt,
                    ): bool,
                    vol.Optional(
                        "min_position_change",
                        default=current_min_change,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                    vol.Optional(
                        "min_time_between_changes",
                        default=current_min_time,
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        "pause_duration",
                        default=current_pause,
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=480)),
                }
            ),
        )

    # -------------------------------------------------------------------------
    # Facade Management
    # -------------------------------------------------------------------------

    async def async_step_facades(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show facade list with add/edit options."""
        if user_input is not None:
            selected = user_input.get("facade_option")
            if selected == "add":
                return await self.async_step_facade_add()
            elif selected and selected.startswith("facade:"):
                self._selected_facade = selected[7:]
                return await self.async_step_facade_edit()

        storage = self._get_storage()
        facade_options = [{"value": "add", "label": "+ Neue Fassade hinzufügen"}]

        if storage:
            for facade_id, facade in storage.facades.items():
                facade_options.append({
                    "value": f"facade:{facade_id}",
                    "label": f"{facade.name} ({facade.direction.upper()})",
                })

        return self.async_show_form(
            step_id="facades",
            data_schema=vol.Schema(
                {
                    vol.Required("facade_option"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=facade_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_facade_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a new facade."""
        storage = self._get_storage()
        errors: dict[str, str] = {}

        if user_input is not None and storage:
            facade_name = user_input.get("name", "").strip()
            facade_direction = user_input.get("direction", "south")

            if not facade_name:
                errors["name"] = "name_required"
            else:
                facade_id = _sanitize_id(facade_name)
                if facade_id in storage.facades:
                    errors["name"] = "already_exists"
                else:
                    preset = FACADE_PRESETS.get(facade_direction, FACADE_PRESETS["south"])
                    new_facade = Facade(
                        id=facade_id,
                        name=facade_name,
                        direction=facade_direction,
                        azimuth_start=preset["start"],
                        azimuth_end=preset["end"],
                    )
                    await storage.async_add_facade(new_facade)
                    return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(
            step_id="facade_add",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(max=255)),
                    vol.Required("direction", default="south"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_DIRECTION_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_facade_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit or delete a facade."""
        storage = self._get_storage()
        facade_id = self._selected_facade

        if not storage or not facade_id or facade_id not in storage.facades:
            return await self.async_step_facades()

        facade = storage.facades[facade_id]

        if user_input is not None:
            if user_input.get("delete"):
                await storage.async_remove_facade(facade_id)
                return self.async_create_entry(title="", data=self.config_entry.options)

            # Update facade
            new_name = user_input.get("name", facade.name)
            new_direction = user_input.get("direction", facade.direction)
            preset = FACADE_PRESETS.get(new_direction, FACADE_PRESETS["south"])

            azimuth_start = user_input.get("azimuth_start", preset["start"])
            azimuth_end = user_input.get("azimuth_end", preset["end"])

            # Validate azimuth range (equal values are invalid)
            if azimuth_start == azimuth_end:
                return self.async_show_form(
                    step_id="facade_edit",
                    errors={"base": "invalid_azimuth_range"},
                    description_placeholders={"facade_name": facade.name},
                    data_schema=vol.Schema(
                        {
                            vol.Required("name", default=new_name): vol.All(str, vol.Length(max=255)),
                            vol.Required("direction", default=new_direction): selector.SelectSelector(
                                selector.SelectSelectorConfig(
                                    options=_DIRECTION_OPTIONS,
                                    mode=selector.SelectSelectorMode.DROPDOWN,
                                )
                            ),
                            vol.Optional("azimuth_start", default=azimuth_start): vol.All(
                                vol.Coerce(float), vol.Range(min=0, max=360)
                            ),
                            vol.Optional("azimuth_end", default=azimuth_end): vol.All(
                                vol.Coerce(float), vol.Range(min=0, max=360)
                            ),
                            vol.Optional("min_elevation", default=user_input.get("min_elevation", 0.0)): vol.All(
                                vol.Coerce(float), vol.Range(min=0, max=90)
                            ),
                            vol.Optional("delete", default=False): bool,
                        }
                    ),
                )

            updated_facade = Facade(
                id=facade_id,
                name=new_name,
                direction=new_direction,
                azimuth_start=azimuth_start,
                azimuth_end=azimuth_end,
                min_elevation=user_input.get("min_elevation", 0.0),
                cover_ids=facade.cover_ids,
            )
            await storage.async_add_facade(updated_facade)
            return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(
            step_id="facade_edit",
            description_placeholders={"facade_name": facade.name},
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=facade.name): vol.All(str, vol.Length(max=255)),
                    vol.Required("direction", default=facade.direction): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_DIRECTION_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("azimuth_start", default=facade.azimuth_start): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=360)
                    ),
                    vol.Optional("azimuth_end", default=facade.azimuth_end): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=360)
                    ),
                    vol.Optional("min_elevation", default=facade.min_elevation): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Optional("delete", default=False): bool,
                }
            ),
        )

    # -------------------------------------------------------------------------
    # Rule Management
    # -------------------------------------------------------------------------

    async def async_step_rules(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show rule list with add/edit options."""
        if user_input is not None:
            selected = user_input.get("rule_option")
            if selected == "add":
                return await self.async_step_rule_add()
            elif selected and selected.startswith("rule:"):
                self._selected_rule = selected[5:]
                return await self.async_step_rule_edit()

        storage = self._get_storage()
        rule_options = [{"value": "add", "label": "+ Neue Regel hinzufügen"}]

        if storage:
            for rule_id, rule in storage.rules.items():
                status = "aktiv" if rule.enabled else "inaktiv"
                rule_options.append({
                    "value": f"rule:{rule_id}",
                    "label": f"{rule.name} ({status})",
                })

        return self.async_show_form(
            step_id="rules",
            data_schema=vol.Schema(
                {
                    vol.Required("rule_option"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=rule_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_rule_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a new rule."""
        storage = self._get_storage()
        errors: dict[str, str] = {}

        if user_input is not None and storage:
            rule_name = user_input.get("name", "").strip()

            if not rule_name:
                errors["name"] = "name_required"
            else:
                rule_id = _sanitize_id(rule_name)
                if rule_id in storage.rules:
                    errors["name"] = "already_exists"
                else:
                    new_rule = Rule(
                        id=rule_id,
                        name=rule_name,
                        enabled=user_input.get("enabled", True),
                        priority=user_input.get("priority", 10),
                        target_position=user_input.get("target_position", 0),
                        target_tilt_position=user_input.get("target_tilt_position"),
                    )
                    await storage.async_add_rule(new_rule)
                    # Go to rule edit to add conditions
                    self._selected_rule = rule_id
                    return await self.async_step_rule_edit()

        return self.async_show_form(
            step_id="rule_add",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(max=255)),
                    vol.Optional("enabled", default=True): bool,
                    vol.Optional("priority", default=10): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=100)
                    ),
                    vol.Optional("target_position", default=0): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=100)
                    ),
                    vol.Optional("target_tilt_position"): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=100)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_rule_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit or delete a rule."""
        storage = self._get_storage()
        rule_id = self._selected_rule

        if not storage or not rule_id or rule_id not in storage.rules:
            return await self.async_step_rules()

        rule = storage.rules[rule_id]

        if user_input is not None:
            if user_input.get("delete"):
                await storage.async_remove_rule(rule_id)
                return self.async_create_entry(title="", data=self.config_entry.options)

            if user_input.get("add_condition"):
                return await self.async_step_rule_condition()

            # Update rule
            updated_rule = Rule(
                id=rule_id,
                name=user_input.get("name", rule.name),
                enabled=user_input.get("enabled", rule.enabled),
                priority=user_input.get("priority", rule.priority),
                condition_operator=user_input.get("condition_operator", rule.condition_operator),
                target_position=user_input.get("target_position", rule.target_position),
                target_tilt_position=user_input.get("target_tilt_position", rule.target_tilt_position),
                conditions=rule.conditions,
                facade_ids=rule.facade_ids,
                cover_ids=rule.cover_ids,
            )
            await storage.async_add_rule(updated_rule)
            return self.async_create_entry(title="", data=self.config_entry.options)

        # Build conditions display
        conditions_str = ", ".join([c.type.value for c in rule.conditions]) or "Keine"

        return self.async_show_form(
            step_id="rule_edit",
            description_placeholders={
                "rule_name": rule.name,
                "conditions": conditions_str,
            },
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=rule.name): vol.All(str, vol.Length(max=255)),
                    vol.Optional("enabled", default=rule.enabled): bool,
                    vol.Optional("priority", default=rule.priority): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=100)
                    ),
                    vol.Optional(
                        "condition_operator", default=rule.condition_operator
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "and", "label": "AND"},
                                {"value": "or", "label": "OR"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("target_position", default=rule.target_position): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=100)
                    ),
                    vol.Optional(
                        "target_tilt_position",
                        description={"suggested_value": rule.target_tilt_position},
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                    vol.Optional("add_condition", default=False): bool,
                    vol.Optional("delete", default=False): bool,
                }
            ),
        )

    async def async_step_rule_condition(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a condition to a rule."""
        storage = self._get_storage()
        rule_id = self._selected_rule

        if not storage or not rule_id or rule_id not in storage.rules:
            return await self.async_step_rules()

        rule = storage.rules[rule_id]

        if len(rule.conditions) >= MAX_CONDITIONS_PER_RULE:
            return await self.async_step_rule_edit()

        if user_input is not None:
            condition_type = user_input.get("condition_type")
            try:
                ConditionType(condition_type)
            except ValueError:
                return await self.async_step_rule_condition()

            params: dict[str, Any] = {}

            # Build params based on condition type
            if condition_type == "sun_on_facade":
                if facade_val := user_input.get("facade"):
                    params["facade"] = facade_val
            elif condition_type in ("sun_elevation_above", "sun_elevation_below"):
                params["value"] = user_input.get("value", 0)
            elif condition_type in ("temperature_above", "temperature_below"):
                params["sensor"] = user_input.get("sensor")
                params["value"] = user_input.get("value", 20)
            elif condition_type == "temperature_comfort":
                params["mode"] = user_input.get("comfort_mode", "cooling")
            elif condition_type == "time_between":
                params["start"] = user_input.get("time_start", "08:00")
                params["end"] = user_input.get("time_end", "20:00")
            elif condition_type in ("time_after_sunrise", "time_after_sunset"):
                params["offset"] = user_input.get("offset", 0)
            elif condition_type == "state_is":
                params["entity"] = user_input.get("entity")
                params["state"] = user_input.get("state")
            elif condition_type == "weather_is":
                params["states"] = [user_input.get("weather_state", "sunny")]

            new_condition = Condition(
                type=ConditionType(condition_type),
                params=params,
            )

            # Update rule with new condition
            updated_rule = Rule(
                id=rule_id,
                name=rule.name,
                enabled=rule.enabled,
                priority=rule.priority,
                condition_operator=rule.condition_operator,
                target_position=rule.target_position,
                target_tilt_position=rule.target_tilt_position,
                conditions=list(rule.conditions) + [new_condition],
                facade_ids=rule.facade_ids,
                cover_ids=rule.cover_ids,
            )
            await storage.async_add_rule(updated_rule)
            return await self.async_step_rule_edit()

        condition_types = [
            {"value": "sun_on_facade", "label": "Sonne auf Fassade"},
            {"value": "sun_elevation_above", "label": "Sonnenhöhe über"},
            {"value": "sun_elevation_below", "label": "Sonnenhöhe unter"},
            {"value": "temperature_above", "label": "Temperatur über"},
            {"value": "temperature_below", "label": "Temperatur unter"},
            {"value": "temperature_comfort", "label": "Komfort-Modus"},
            {"value": "time_between", "label": "Zeit zwischen"},
            {"value": "time_after_sunrise", "label": "Nach Sonnenaufgang"},
            {"value": "time_after_sunset", "label": "Nach Sonnenuntergang"},
            {"value": "state_is", "label": "Entity-Status ist"},
            {"value": "weather_is", "label": "Wetter ist"},
        ]

        # Build facade options for sun_on_facade condition
        facade_options = [{"value": "", "label": "-- Cover-Fassade --"}]
        if storage:
            for fid, f in storage.facades.items():
                facade_options.append({"value": fid, "label": f.name})

        return self.async_show_form(
            step_id="rule_condition",
            description_placeholders={"rule_name": rule.name},
            data_schema=vol.Schema(
                {
                    vol.Required("condition_type"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=condition_types,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("facade", default=""): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=facade_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("value", default=20): vol.Coerce(float),
                    vol.Optional("sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional("entity"): selector.EntitySelector(
                        selector.EntitySelectorConfig()
                    ),
                    vol.Optional("state"): vol.All(str, vol.Length(max=255)),
                    vol.Optional("time_start", default="08:00"): vol.All(str, vol.Length(max=5)),
                    vol.Optional("time_end", default="20:00"): vol.All(str, vol.Length(max=5)),
                    vol.Optional("offset", default=0): vol.All(
                        vol.Coerce(int), vol.Range(min=-180, max=180)
                    ),
                    vol.Optional("comfort_mode", default="cooling"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "cooling", "label": "Kühlung"},
                                {"value": "heating", "label": "Heizung"},
                                {"value": "neutral", "label": "Neutral"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("weather_state", default="sunny"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "sunny", "label": "Sonnig"},
                                {"value": "cloudy", "label": "Bewölkt"},
                                {"value": "rainy", "label": "Regnerisch"},
                                {"value": "windy", "label": "Windig"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    # -------------------------------------------------------------------------
    # Scenario Management
    # -------------------------------------------------------------------------

    async def async_step_scenarios(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show scenario list with add/edit options."""
        if user_input is not None:
            selected = user_input.get("scenario_option")
            if selected == "add":
                return await self.async_step_scenario_add()
            elif selected and selected.startswith("scenario:"):
                self._selected_scenario = selected[9:]
                return await self.async_step_scenario_edit()

        storage = self._get_storage()
        scenario_options = [{"value": "add", "label": "+ Neues Szenario hinzufügen"}]

        if storage:
            active = storage.active_scenario
            for scenario_id, scenario in storage.scenarios.items():
                status = "(aktiv)" if scenario_id == active else ""
                scenario_options.append({
                    "value": f"scenario:{scenario_id}",
                    "label": f"{scenario.name} {status}".strip(),
                })

        return self.async_show_form(
            step_id="scenarios",
            data_schema=vol.Schema(
                {
                    vol.Required("scenario_option"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=scenario_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_scenario_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a new scenario."""
        storage = self._get_storage()
        errors: dict[str, str] = {}

        if user_input is not None and storage:
            scenario_name = user_input.get("name", "").strip()

            if not scenario_name:
                errors["name"] = "name_required"
            else:
                scenario_id = _sanitize_id(scenario_name)
                if scenario_id in storage.scenarios:
                    errors["name"] = "already_exists"
                else:
                    new_scenario = Scenario(
                        id=scenario_id,
                        name=scenario_name,
                        icon=user_input.get("icon", "mdi:home"),
                    )
                    await storage.async_add_scenario(new_scenario)
                    return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(
            step_id="scenario_add",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(max=255)),
                    vol.Optional("icon", default="mdi:home"): selector.IconSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_scenario_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit or delete a scenario."""
        storage = self._get_storage()
        scenario_id = self._selected_scenario

        if not storage or not scenario_id or scenario_id not in storage.scenarios:
            return await self.async_step_scenarios()

        scenario = storage.scenarios[scenario_id]

        if user_input is not None:
            if user_input.get("delete"):
                # Fix active_scenario BEFORE removing to avoid dangling reference
                needs_active_fix = storage.active_scenario == scenario_id
                await storage.async_remove_scenario(scenario_id)
                if needs_active_fix:
                    remaining = list(storage.scenarios.keys())
                    if "everyday" in remaining:
                        storage.active_scenario = "everyday"
                    elif remaining:
                        storage.active_scenario = remaining[0]
                    else:
                        # No scenarios left - recreate default
                        default = Scenario(id="everyday", name="Everyday", icon="mdi:home")
                        await storage.async_add_scenario(default)
                        storage.active_scenario = "everyday"
                    await storage.async_save()
                return self.async_create_entry(title="", data=self.config_entry.options)

            if user_input.get("activate"):
                storage.active_scenario = scenario_id
                await storage.async_save()
                return self.async_create_entry(title="", data=self.config_entry.options)

            # Update scenario (preserve rules_disabled if field not in form)
            updated_scenario = Scenario(
                id=scenario_id,
                name=user_input.get("name", scenario.name),
                icon=user_input.get("icon", scenario.icon),
                rules_disabled=user_input.get("rules_disabled", scenario.rules_disabled),
            )
            await storage.async_add_scenario(updated_scenario)
            return self.async_create_entry(title="", data=self.config_entry.options)

        # Build rule options for multi-select
        rule_options = [
            {"value": rule_id, "label": rule.name}
            for rule_id, rule in storage.rules.items()
        ]

        # Build schema - only show rules_disabled if rules exist
        schema_dict: dict[Any, Any] = {
            vol.Required("name", default=scenario.name): vol.All(str, vol.Length(max=255)),
            vol.Optional("icon", default=scenario.icon or "mdi:home"): selector.IconSelector(),
        }

        if rule_options:
            schema_dict[vol.Optional("rules_disabled", default=scenario.rules_disabled)] = (
                selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=rule_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            )

        schema_dict[vol.Optional("activate", default=False)] = bool
        schema_dict[vol.Optional("delete", default=False)] = bool

        return self.async_show_form(
            step_id="scenario_edit",
            description_placeholders={"scenario_name": scenario.name},
            data_schema=vol.Schema(schema_dict),
        )
