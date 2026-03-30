"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import async_setup_api
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .services import async_setup_services, async_unload_services
from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)


@dataclass
class CoverAutomaticRuntimeData:
    """Runtime data for CoverAutomatic integration."""

    coordinator: CoverAutomaticCoordinator
    storage: CoverAutomaticStorage


type CoverAutomaticConfigEntry = ConfigEntry[CoverAutomaticRuntimeData]

PLATFORMS_LIST: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CoverAutomatic from YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CoverAutomaticConfigEntry) -> bool:
    """Set up CoverAutomatic from a config entry."""
    storage = CoverAutomaticStorage(hass)
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator = CoverAutomaticCoordinator(
        hass, storage, scan_interval, config_entry=entry
    )

    await coordinator.async_setup()

    async def async_options_updated(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Handle options update by reloading entry to recreate entities."""
        await hass.config_entries.async_reload(config_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    # Transfer config flow data to storage (first setup only)
    if entry.data.get("covers") and not storage.covers:
        from .models import CoverConfig, Facade

        for facade_data in entry.data.get("facades", []):
            facade = Facade(
                id=facade_data["id"],
                name=facade_data["name"],
                direction=facade_data["direction"],
                azimuth_start=facade_data["azimuth_start"],
                azimuth_end=facade_data["azimuth_end"],
            )
            await storage.async_add_facade(facade)

        for entity_id in entry.data.get("covers", []):
            cover = CoverConfig(
                entity_id=entity_id,
                name=entity_id.split(".")[-1].replace("_", " ").title(),
            )
            await storage.async_add_cover(cover)

        if outdoor_sensor := entry.data.get("outdoor_temp_sensor"):
            storage.outdoor_temp_sensor = outdoor_sensor
            await storage.async_save()

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = CoverAutomaticRuntimeData(
        coordinator=coordinator,
        storage=storage,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    await async_setup_services(hass)

    # Setup WebSocket API for config panel
    async_setup_api(hass, storage, coordinator)

    # Register custom panel
    panel_path = pathlib.Path(__file__).parent / "panel" / "cover-automatic-panel.js"
    hass.http.register_static_path(
        "/cover_automatic/panel.js",
        str(panel_path),
        cache_headers=False,
    )
    hass.components.frontend.async_register_built_in_panel(
        component_name="custom",
        sidebar_title="CoverAutomatic",
        sidebar_icon="mdi:blinds",
        frontend_url_path="cover-automatic",
        require_admin=True,
        config={
            "_panel_custom": {
                "name": "cover-automatic-panel",
                "js_url": "/cover_automatic/panel.js",
                "embed_iframe": False,
            }
        },
    )

    entry.async_on_unload(coordinator.async_shutdown)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CoverAutomaticConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if not unload_ok:
        # Ensure coordinator shutdown even on failed platform unload
        runtime_data = getattr(entry, "runtime_data", None)
        if runtime_data:
            await runtime_data.coordinator.async_shutdown()

    # Unload services only if unload succeeded and no entries remain
    if unload_ok:
        remaining = [
            e for e in hass.config_entries.async_entries(DOMAIN)
            if e.entry_id != entry.entry_id
        ]
        if not remaining:
            await async_unload_services(hass)
            hass.components.frontend.async_remove_panel("cover-automatic")

    return unload_ok
