"""Service handlers for CoverAutomatic."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from homeassistant.core import ServiceCall

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Allowed base directories for config import/export
ALLOWED_CONFIG_PATHS = ["/config", "/homeassistant"]


def _validate_config_path(path: str) -> Path | None:
    """Validate that path is within allowed directories.

    Prevents path traversal attacks by ensuring the resolved path
    stays within allowed base directories.

    Returns:
        Resolved Path if valid, None if path is unsafe.
    """
    try:
        # Resolve to absolute path (handles ../ etc.)
        resolved = Path(path).resolve()

        # Check if path is within any allowed directory
        for allowed_base in ALLOWED_CONFIG_PATHS:
            allowed_path = Path(allowed_base).resolve()
            if allowed_path.exists():
                try:
                    resolved.relative_to(allowed_path)
                    return resolved
                except ValueError:
                    continue

        _LOGGER.warning(
            "Path validation failed: %s is not within allowed directories %s",
            path,
            ALLOWED_CONFIG_PATHS,
        )
        return None

    except Exception as err:
        _LOGGER.error("Path validation error for %s: %s", path, err)
        return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for CoverAutomatic."""
    # Only register services once
    if hass.services.has_service(DOMAIN, "pause"):
        return

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            if entity_id in coordinator.storage.covers:
                coordinator._pause_cover(coordinator.storage.covers[entity_id])
                break

    async def handle_resume(call: ServiceCall) -> None:
        """Handle resume service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            if entity_id in coordinator.storage.covers:
                coordinator.resume_cover(entity_id)
                break

    async def handle_pause_all(call: ServiceCall) -> None:
        """Handle pause_all service call."""
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            for cover in coordinator.storage.covers.values():
                coordinator._pause_cover(cover)

    async def handle_resume_all(call: ServiceCall) -> None:
        """Handle resume_all service call."""
        for entry_data in hass.data[DOMAIN].values():
            coordinator = entry_data["coordinator"]
            for entity_id in coordinator.storage.covers:
                coordinator.resume_cover(entity_id)

    async def handle_set_scenario(call: ServiceCall) -> None:
        """Handle set_scenario service call."""
        scenario = call.data.get("scenario")
        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            coordinator = entry_data["coordinator"]
            if scenario in storage.scenarios:
                storage.active_scenario = scenario
                await storage.async_save()
                await coordinator.async_request_refresh()

    async def handle_export_config(call: ServiceCall) -> None:
        """Handle export_config service call."""
        path_str = call.data.get("path", "/config/cover_automatic_backup.yaml")

        # Validate path to prevent path traversal attacks
        validated_path = _validate_config_path(path_str)
        if validated_path is None:
            _LOGGER.error(
                "Export rejected: path '%s' is outside allowed directories", path_str
            )
            return

        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            data = storage.get_raw_data()

            def write_yaml():
                with open(validated_path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            await hass.async_add_executor_job(write_yaml)
            _LOGGER.info("Configuration exported to %s", validated_path)
            break

    async def handle_import_config(call: ServiceCall) -> None:
        """Handle import_config service call."""
        path_str = call.data.get("path")
        if not path_str:
            _LOGGER.error("Import rejected: no path provided")
            return

        # Validate path to prevent path traversal attacks
        validated_path = _validate_config_path(path_str)
        if validated_path is None:
            _LOGGER.error(
                "Import rejected: path '%s' is outside allowed directories", path_str
            )
            return

        if not validated_path.exists():
            _LOGGER.error("Import file not found: %s", validated_path)
            return

        def read_yaml():
            with open(validated_path) as f:
                return yaml.safe_load(f)

        data = await hass.async_add_executor_job(read_yaml)

        for entry_data in hass.data[DOMAIN].values():
            storage = entry_data["storage"]
            coordinator = entry_data["coordinator"]
            await storage.async_import_data(data)
            coordinator.refresh_state_tracking()
            await coordinator.async_request_refresh()
            _LOGGER.info("Configuration imported from %s", validated_path)
            break

    hass.services.async_register(DOMAIN, "pause", handle_pause)
    hass.services.async_register(DOMAIN, "resume", handle_resume)
    hass.services.async_register(DOMAIN, "pause_all", handle_pause_all)
    hass.services.async_register(DOMAIN, "resume_all", handle_resume_all)
    hass.services.async_register(DOMAIN, "set_scenario", handle_set_scenario)
    hass.services.async_register(DOMAIN, "export_config", handle_export_config)
    hass.services.async_register(DOMAIN, "import_config", handle_import_config)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, "pause")
    hass.services.async_remove(DOMAIN, "resume")
    hass.services.async_remove(DOMAIN, "pause_all")
    hass.services.async_remove(DOMAIN, "resume_all")
    hass.services.async_remove(DOMAIN, "set_scenario")
    hass.services.async_remove(DOMAIN, "export_config")
    hass.services.async_remove(DOMAIN, "import_config")
