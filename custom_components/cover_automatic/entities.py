"""Entity/device registry housekeeping for CoverAutomatic.

Entities are created per managed cover and per facade. Covers and facades can
be added or removed at runtime from the panel, so the registries have to be
kept in sync: new objects get entities via coordinator listeners in the
platforms, removed objects are cleaned up here.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .storage import CoverAutomaticStorage

_LOGGER = logging.getLogger(__name__)


def expected_unique_ids(entry_id: str, storage: CoverAutomaticStorage) -> set[str]:
    """Return the unique_ids of all entities the current config should have."""
    ids = {
        f"{DOMAIN}_master",
        f"{DOMAIN}_{entry_id}_scenario",
        f"{DOMAIN}_{entry_id}_wind_protection",
        f"{DOMAIN}_{entry_id}_covers_paused",
        f"{DOMAIN}_{entry_id}_covers_manual",
        f"{DOMAIN}_{entry_id}_covers_locked",
    }
    for entity_id in storage._data.get("covers", {}):
        ids.add(f"{DOMAIN}_{entity_id}_auto")
        for suffix in ("status", "rule", "target", "position", "comfort", "pause_end"):
            ids.add(f"{DOMAIN}_{entity_id}_{suffix}")
    for facade_id in storage._data.get("facades", {}):
        ids.add(f"{DOMAIN}_facade_{facade_id}_sun")
        ids.add(f"{DOMAIN}_facade_{facade_id}_sun_entry")
        ids.add(f"{DOMAIN}_facade_{facade_id}_sun_exit")
    return ids


def expected_device_identifiers(entry_id: str, storage: CoverAutomaticStorage) -> set[str]:
    """Return the (DOMAIN, x) identifier values the current config should have."""
    idents = {entry_id}
    idents.update(storage._data.get("covers", {}).keys())
    idents.update(f"facade_{fid}" for fid in storage._data.get("facades", {}))
    return idents


@callback
def async_cleanup_orphan_entities(
    hass: HomeAssistant, entry: ConfigEntry, storage: CoverAutomaticStorage
) -> None:
    """Remove registry entities/devices whose cover or facade no longer exists.

    Also removes legacy entities from older versions (e.g. the per-cover
    pause_duration number entities removed in 1.52.0).
    """
    expected = expected_unique_ids(entry.entry_id, storage)
    ent_reg = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if reg_entry.platform == DOMAIN and reg_entry.unique_id not in expected:
            _LOGGER.info("Removing orphan entity %s", reg_entry.entity_id)
            ent_reg.async_remove(reg_entry.entity_id)

    expected_devices = expected_device_identifiers(entry.entry_id, storage)
    dev_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        own = {value for (domain, value) in device.identifiers if domain == DOMAIN}
        if own and not own & expected_devices:
            _LOGGER.info("Removing orphan device %s", device.name)
            dev_reg.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )
