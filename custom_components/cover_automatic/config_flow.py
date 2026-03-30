"""Config flow for CoverAutomatic integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import DOMAIN


class CoverAutomaticConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CoverAutomatic."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zero-config: confirm and create entry."""
        if user_input is not None:
            return self.async_create_entry(title="CoverAutomatic", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> CoverAutomaticOptionsFlow:
        """Get the options flow for this handler."""
        return CoverAutomaticOptionsFlow()


class CoverAutomaticOptionsFlow(OptionsFlow):
    """Redirect to config panel."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show link to panel."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self.config_entry.options)
        return self.async_show_form(step_id="init")
