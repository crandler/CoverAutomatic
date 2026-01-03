"""CoverAutomatic integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator
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
    coordinator = CoverAutomaticCoordinator(hass, storage)

    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "storage": storage,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    entry.async_on_unload(coordinator.async_shutdown)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator = data["coordinator"]
        coordinator.async_shutdown()

    return unload_ok
