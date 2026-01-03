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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 60),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                }
            ),
        )
