"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass

from homeassistant.components.frontend import (
    add_extra_js_url,
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .api import async_setup_api
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .entities import async_cleanup_orphan_entities
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
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PANEL_JS_URL = "/cover_automatic/panel.js"
# Dashboard card, loaded on every frontend page (custom:cover-automatic-card)
CARD_JS_URL = "/cover_automatic/cover-automatic-card.js"
# hass.data[DOMAIN] flag: static panel route already registered this HA run
_STATIC_PATH_REGISTERED = "static_path_registered"


async def _async_register_card_resource(hass: HomeAssistant, url: str) -> bool:
    """Declare the dashboard card as a Lovelace resource (storage mode).

    Lovelace resources are loaded with the dashboards, so the card is
    defined when they are built (the extra module URL could arrive too late
    and the card then showed "Configuration error" until a refresh). The
    entry is updated when the version changes. Returns False when the
    resources cannot be managed (YAML mode, Lovelace not loaded).
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA
        from homeassistant.components.lovelace.resources import ResourceStorageCollection
    except ImportError:
        return False
    data = hass.data.get(LOVELACE_DATA)
    resources = getattr(data, "resources", None)
    if not isinstance(resources, ResourceStorageCollection):
        return False
    try:
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True
        base = url.split("?", 1)[0]
        for item in resources.async_items():
            if str(item.get("url", "")).split("?", 1)[0] != base:
                continue
            if item.get("url") != url or item.get("type") != "module":
                await resources.async_update_item(item["id"], {"res_type": "module", "url": url})
            return True
        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception as err:  # noqa: BLE001 -- never block the integration setup
        _LOGGER.warning("Could not register the dashboard card resource: %s", err)
        return False
    return True


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
    """Register the panel's static path (YAML setup is not supported).

    Runs once per Home Assistant runtime. aiohttp routes cannot be removed, so
    registering in async_setup_entry would fail on every entry reload.
    """
    panel_path = pathlib.Path(__file__).parent / "panel" / "cover-automatic-panel.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/cover_automatic/panel.js", str(panel_path), False)]
    )
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
    # Entities of covers/facades deleted while HA was running an older
    # version (or deleted before a restart) are dropped here.
    async_cleanup_orphan_entities(hass, entry, storage)

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

    # Version for cache busting and the panel's version display. Taken from the
    # integration object, whose manifest Home Assistant has already loaded and
    # cached -- reading manifest.json here would be blocking I/O in the event loop.
    integration = await async_get_integration(hass, DOMAIN)
    panel_version = integration.manifest.get("version", "0")

    # Setup WebSocket API for config panel
    async_setup_api(hass, storage, coordinator, version=panel_version)

<<<<<<< Updated upstream
    # Register custom panel (version query for cache busting); the static path
    # behind js_url is registered once in async_setup
=======
    # Register custom panel (version query for cache busting). aiohttp routes
    # cannot be removed, and registering the same GET route twice raises
    # RuntimeError -- so the static path is registered once per HA run and
    # survives config entry reloads.
    domain_data: dict = hass.data.setdefault(DOMAIN, {})
    panel_dir = pathlib.Path(__file__).parent / "panel"
    panel_stamp = await _async_asset_stamp(hass, panel_dir / "cover-automatic-panel.js")
    if not domain_data.get(_STATIC_PATH_REGISTERED):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(PANEL_JS_URL, str(panel_dir / "cover-automatic-panel.js"), False),
                StaticPathConfig(CARD_JS_URL, str(panel_dir / "cover-automatic-card.js"), False),
            ]
        )
        domain_data[_STATIC_PATH_REGISTERED] = True
        card_stamp = await _async_asset_stamp(hass, panel_dir / "cover-automatic-card.js")
        card_url = f"{CARD_JS_URL}?v={panel_version}{card_stamp}"
        if not await _async_register_card_resource(hass, card_url):
            # YAML resources / no Lovelace: load the card with every page.
            add_extra_js_url(hass, card_url)
>>>>>>> Stashed changes
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="CoverAutomatic",
        sidebar_icon="mdi:blinds",
        frontend_url_path="cover-automatic",
        require_admin=True,
        # update=True: a failed unload can leave the panel registered; a
        # later setup must replace it instead of raising "Overwriting panel".
        update=True,
        config={
            "_panel_custom": {
                "name": "cover-automatic-panel",
                "js_url": f"{PANEL_JS_URL}?v={panel_version}{panel_stamp}",
                "embed_iframe": False,
            }
        },
    )

    # coordinator.async_shutdown is registered on unload by
    # DataUpdateCoordinator itself (config_entry is passed to it).

    return True


async def _async_asset_stamp(hass: HomeAssistant, path: pathlib.Path) -> str:
    """Modification time of a bundled asset, for cache busting.

    The version alone is not enough: files updated without a version bump
    would keep being served from the browser cache. Read in the executor
    (stat is file I/O); "" when unavailable, the version is then used alone.
    """
    try:
        mtime = await hass.async_add_executor_job(_asset_mtime, path)
    except (OSError, TypeError):
        return ""
    return f"-{mtime}" if isinstance(mtime, int) else ""


def _asset_mtime(path: pathlib.Path) -> int:
    """Integer mtime of a file (executor)."""
    return int(path.stat().st_mtime)


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
