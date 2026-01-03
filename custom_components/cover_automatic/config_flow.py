"""Config flow for CoverAutomatic integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, FACADE_PRESETS

_LOGGER = logging.getLogger(__name__)


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

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._data["name"] = user_input.get("name", "CoverAutomatic")
            return await self.async_step_facades()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default="CoverAutomatic"): str,
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
                            "id": facade_name.lower().replace(" ", "_"),
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
                    vol.Optional("facade_name"): str,
                    vol.Optional("facade_direction", default="south"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "north", "label": "North"},
                                {"value": "east", "label": "East"},
                                {"value": "south", "label": "South"},
                                {"value": "west", "label": "West"},
                            ],
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

        facade_options = [{"value": f["id"], "label": f["name"]} for f in self._facades]
        if not facade_options:
            facade_options = [{"value": "none", "label": "No facade"}]

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
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CoverAutomaticOptionsFlow(config_entry)


class CoverAutomaticOptionsFlow(OptionsFlow):
    """Handle options flow for CoverAutomatic."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._selected_cover: str | None = None

    def _get_storage(self):
        """Get storage from hass.data."""
        if DOMAIN not in self.hass.data:
            return None
        for entry_data in self.hass.data[DOMAIN].values():
            if "storage" in entry_data:
                return entry_data["storage"]
        return None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show menu with general settings and all covers."""
        if user_input is not None:
            selected = user_input.get("menu_option")
            if selected == "general":
                return await self.async_step_general()
            elif selected and selected.startswith("cover:"):
                self._selected_cover = selected[6:]  # Remove "cover:" prefix
                return await self.async_step_cover_details()

        # Build menu options: General + all covers
        menu_options = [{"value": "general", "label": "Allgemeine Einstellungen"}]

        storage = self._get_storage()
        if storage:
            for entity_id in storage.covers:
                cover = storage.covers[entity_id]
                menu_options.append({
                    "value": f"cover:{entity_id}",
                    "label": cover.name or entity_id,
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
            # Save to options (scan_interval) and storage (sensors)
            new_options = dict(self.config_entry.options)
            new_options["scan_interval"] = user_input.get("scan_interval", 60)

            if storage:
                storage.outdoor_temp_sensor = user_input.get("outdoor_temp_sensor")
                storage.indoor_temp_sensor = user_input.get("indoor_temp_sensor")
                storage.weather_entity = user_input.get("weather_entity")
                storage.comfort_temp_min = user_input.get("comfort_temp_min", 21.0)
                storage.comfort_temp_max = user_input.get("comfort_temp_max", 25.0)
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
            cover_raw["min_position_change"] = user_input.get("min_position_change", 5)
            cover_raw["min_time_between_changes"] = user_input.get("min_time_between_changes", 300)
            cover_raw["pause_duration"] = user_input.get("pause_duration", 120)
            await storage.async_save()

            # Refresh coordinator state tracking
            for entry_data in self.hass.data[DOMAIN].values():
                if "coordinator" in entry_data:
                    entry_data["coordinator"].refresh_state_tracking()

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
