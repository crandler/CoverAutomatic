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


def _validate_config_path(path: str, extra_paths: list[str] | None = None) -> Path | None:
    """Validate that path is within allowed directories.

    Prevents path traversal attacks by ensuring the resolved path
    stays within allowed base directories.

    Returns:
        Resolved Path if valid, None if path is unsafe.
    """
    try:
        # Resolve to absolute path (handles ../ etc.)
        resolved = Path(path).resolve()

        # Combine static and dynamic allowed paths
        all_allowed = list(ALLOWED_CONFIG_PATHS)
        if extra_paths:
            all_allowed.extend(extra_paths)

        # Check if path is within any allowed directory
        for allowed_base in all_allowed:
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
            all_allowed,
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

    def _get_entries():
        """Get all integration entry runtime data safely."""
        result = {}
        for entry in hass.config_entries.async_entries(DOMAIN):
            if hasattr(entry, "runtime_data") and entry.runtime_data:
                result[entry.entry_id] = entry.runtime_data
        return result

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in _get_entries().values():
            if entity_id in entry_data.coordinator.storage.covers:
                entry_data.coordinator.pause_cover(
                    entry_data.coordinator.storage.covers[entity_id]
                )
                break

    async def handle_resume(call: ServiceCall) -> None:
        """Handle resume service call."""
        entity_id = call.data.get("entity_id")
        for entry_data in _get_entries().values():
            if entity_id in entry_data.coordinator.storage.covers:
                entry_data.coordinator.resume_cover(entity_id)
                break

    async def handle_pause_all(call: ServiceCall) -> None:
        """Handle pause_all service call."""
        for entry_data in _get_entries().values():
            for cover in entry_data.coordinator.storage.covers.values():
                entry_data.coordinator.pause_cover(cover)

    async def handle_resume_all(call: ServiceCall) -> None:
        """Handle resume_all service call."""
        for entry_data in _get_entries().values():
            for entity_id in entry_data.coordinator.storage.covers:
                entry_data.coordinator.resume_cover(entity_id)

    async def handle_set_scenario(call: ServiceCall) -> None:
        """Handle set_scenario service call."""
        scenario = call.data.get("scenario")
        if not scenario:
            _LOGGER.error("set_scenario: No scenario provided")
            return

        found = False
        for entry_data in _get_entries().values():
            if scenario in entry_data.storage.scenarios:
                entry_data.storage.active_scenario = scenario
                await entry_data.storage.async_save()
                await entry_data.coordinator.async_request_refresh()
                found = True

        if found:
            _LOGGER.info("Scenario changed to: %s", scenario)
        else:
            # Log error once with available scenarios from first entry
            for entry_data in _get_entries().values():
                available = list(entry_data.storage.scenarios.keys())
                _LOGGER.error(
                    "Unknown scenario '%s'. Available: %s",
                    scenario,
                    ", ".join(available),
                )
                break

    async def handle_export_config(call: ServiceCall) -> None:
        """Handle export_config service call."""
        path_str = call.data.get("path") or hass.config.path(
            "cover_automatic_backup.yaml"
        )

        # Validate path to prevent path traversal attacks
        validated_path = _validate_config_path(
            path_str, extra_paths=[hass.config.config_dir]
        )
        if validated_path is None:
            _LOGGER.error(
                "Export rejected: path '%s' is outside allowed directories", path_str
            )
            return

        for entry_data in _get_entries().values():
            data = entry_data.storage.get_raw_data()

            def write_yaml():
                with open(validated_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            try:
                await hass.async_add_executor_job(write_yaml)
            except (OSError, yaml.YAMLError) as err:
                _LOGGER.error("Export failed: %s", err)
                return
            _LOGGER.info("Configuration exported to %s", validated_path)
            break

    async def handle_import_config(call: ServiceCall) -> None:
        """Handle import_config service call."""
        path_str = call.data.get("path")
        if not path_str:
            _LOGGER.error("Import rejected: no path provided")
            return

        # Validate path to prevent path traversal attacks
        validated_path = _validate_config_path(
            path_str, extra_paths=[hass.config.config_dir]
        )
        if validated_path is None:
            _LOGGER.error(
                "Import rejected: path '%s' is outside allowed directories", path_str
            )
            return

        if not validated_path.exists():
            _LOGGER.error("Import file not found: %s", validated_path)
            return

        def read_yaml():
            with open(validated_path, encoding="utf-8") as f:
                return yaml.safe_load(f)

        try:
            data = await hass.async_add_executor_job(read_yaml)
        except (OSError, yaml.YAMLError) as err:
            _LOGGER.error("Import failed: could not read file: %s", err)
            return

        for entry_data in _get_entries().values():
            try:
                await entry_data.storage.async_import_data(data)
            except (ValueError, TypeError) as err:
                _LOGGER.error("Import failed: invalid data format: %s", err)
                return
            entry_data.coordinator.refresh_state_tracking()
            await entry_data.coordinator.async_request_refresh()
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
