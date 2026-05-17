"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import json
import logging
import pathlib
from dataclasses import dataclass

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .api import async_setup_api
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .services import async_setup_services, async_unload_services
from .storage import ActivityLogStorage, CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CoverAutomaticRuntimeData:
    """Runtime data for CoverAutomatic integration."""

    coordinator: CoverAutomaticCoordinator
    storage: CoverAutomaticStorage


type CoverAutomaticConfigEntry = ConfigEntry[CoverAutomaticRuntimeData]

PLATFORMS_LIST: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
]


def _cleanup_removed_entities(hass: HomeAssistant) -> None:
    """Remove orphan entities from prior versions (pre-1.52.0: per-cover pause_duration)."""
    registry = er.async_get(hass)
    stale = [
        entry.entity_id
        for entry in registry.entities.values()
        if entry.platform == DOMAIN
        and entry.domain == Platform.NUMBER
        and entry.unique_id.endswith("_pause_duration")
    ]
    for entity_id in stale:
        _LOGGER.info("Removing orphan entity %s (pause_duration moved to panel)", entity_id)
        registry.async_remove(entity_id)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CoverAutomatic from YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CoverAutomaticConfigEntry) -> bool:
    """Set up CoverAutomatic from a config entry."""
    storage = CoverAutomaticStorage(hass)
    log_storage = ActivityLogStorage(hass)
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator = CoverAutomaticCoordinator(
        hass, storage, scan_interval, config_entry=entry
    )
    coordinator.log_storage = log_storage

    await coordinator.async_setup()
    await log_storage.async_load()

    _cleanup_removed_entities(hass)

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

    # Register custom panel (version query for cache busting)
    panel_dir = pathlib.Path(__file__).parent
    panel_path = panel_dir / "panel" / "cover-automatic-panel.js"
    manifest = json.loads((panel_dir / "manifest.json").read_text())
    panel_version = manifest.get("version", "0")
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/cover_automatic/panel.js", str(panel_path), False)]
    )
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="CoverAutomatic",
        sidebar_icon="mdi:blinds",
        frontend_url_path="cover-automatic",
        require_admin=True,
        config={
            "_panel_custom": {
                "name": "cover-automatic-panel",
                "js_url": f"/cover_automatic/panel.js?v={panel_version}",
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
            async_remove_panel(hass, "cover-automatic")

    return unload_ok
