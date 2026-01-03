"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import CoverAutomaticCoordinator
from .services import async_setup_services, async_unload_services
from .storage import CoverAutomaticStorage

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS_LIST: list[Platform] = [
    Platform.COVER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CoverAutomatic from YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CoverAutomatic from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    storage = CoverAutomaticStorage(hass)
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator = CoverAutomaticCoordinator(hass, storage, scan_interval)

    await coordinator.async_setup()

    async def async_options_updated(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Handle options update."""
        new_interval = config_entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        coordinator.update_interval = timedelta(seconds=new_interval)
        await coordinator.async_request_refresh()

    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    # Transfer config flow data to storage (first setup only)
    if entry.data.get("facades") and not storage.facades:
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

        # Get first facade id for default assignment
        first_facade_id = entry.data["facades"][0]["id"] if entry.data.get("facades") else None

        for entity_id in entry.data.get("covers", []):
            cover = CoverConfig(
                entity_id=entity_id,
                name=entity_id.split(".")[-1].replace("_", " ").title(),
                facade_id=first_facade_id,
            )
            await storage.async_add_cover(cover)

        if outdoor_sensor := entry.data.get("outdoor_temp_sensor"):
            storage.outdoor_temp_sensor = outdoor_sensor
            await storage.async_save()

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "storage": storage,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    await async_setup_services(hass)

    entry.async_on_unload(coordinator.async_shutdown)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator = data["coordinator"]
        coordinator.async_shutdown()

    if not hass.data[DOMAIN]:
        await async_unload_services(hass)

    return unload_ok
