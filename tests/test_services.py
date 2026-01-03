"""Tests for CoverAutomatic services."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.services import (
    _validate_config_path,
    async_setup_services,
    async_unload_services,
)


class TestPathValidation:
    """Tests for path validation security."""

    def test_valid_path_in_config(self) -> None:
        """Test valid path within /config is accepted."""
        with patch.object(Path, "resolve") as mock_resolve, patch.object(
            Path, "exists", return_value=True
        ):
            mock_resolve.return_value = Path("/config/backup.yaml")
            result = _validate_config_path("/config/backup.yaml")
            assert result is not None

    def test_valid_path_in_homeassistant(self) -> None:
        """Test valid path within /homeassistant is accepted."""
        with patch.object(Path, "resolve") as mock_resolve, patch.object(
            Path, "exists", return_value=True
        ):
            mock_resolve.return_value = Path("/homeassistant/backup.yaml")
            result = _validate_config_path("/homeassistant/backup.yaml")
            assert result is not None

    def test_path_traversal_rejected(self) -> None:
        """Test path traversal attempts are rejected."""
        # Test that paths outside allowed directories are rejected
        # The actual implementation resolves paths and checks if they're in allowed dirs
        result = _validate_config_path("/etc/passwd")
        assert result is None

    def test_path_outside_allowed_dirs_rejected(self) -> None:
        """Test paths outside allowed directories are rejected."""
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/root/secrets.yaml")
            result = _validate_config_path("/root/secrets.yaml")
            assert result is None

    def test_invalid_path_returns_none(self) -> None:
        """Test invalid path returns None."""
        with patch.object(Path, "resolve", side_effect=ValueError("Bad path")):
            result = _validate_config_path("\x00invalid")
            assert result is None


class TestServiceSetup:
    """Tests for service registration."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()
        hass.services.async_remove = MagicMock()
        hass.data = {}
        return hass

    @pytest.mark.asyncio
    async def test_services_registered(self, mock_hass) -> None:
        """Test all services are registered."""
        await async_setup_services(mock_hass)

        expected_services = [
            "pause",
            "resume",
            "pause_all",
            "resume_all",
            "set_scenario",
            "export_config",
            "import_config",
        ]

        # Check that async_register was called 7 times (once per service)
        assert mock_hass.services.async_register.call_count == 7

        # Verify each service was registered
        registered_services = [
            call[0][1] for call in mock_hass.services.async_register.call_args_list
        ]
        for service in expected_services:
            assert service in registered_services

    @pytest.mark.asyncio
    async def test_services_not_registered_twice(self, mock_hass) -> None:
        """Test services are not registered if already present."""
        mock_hass.services.has_service.return_value = True

        await async_setup_services(mock_hass)

        mock_hass.services.async_register.assert_not_called()

    @pytest.mark.asyncio
    async def test_services_unloaded(self, mock_hass) -> None:
        """Test all services are unloaded."""
        await async_unload_services(mock_hass)

        expected_services = [
            "pause",
            "resume",
            "pause_all",
            "resume_all",
            "set_scenario",
            "export_config",
            "import_config",
        ]

        for service in expected_services:
            mock_hass.services.async_remove.assert_any_call("cover_automatic", service)


class TestPauseResumeServices:
    """Tests for pause and resume services."""

    @pytest.fixture
    def mock_hass_with_data(self):
        """Create mock Home Assistant with cover data."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()

        mock_cover = MagicMock()
        mock_cover.entity_id = "cover.test"

        mock_storage = MagicMock()
        mock_storage.covers = {"cover.test": mock_cover}

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator._pause_cover = MagicMock()
        mock_coordinator.resume_cover = MagicMock()

        hass.data = {
            "cover_automatic": {
                "entry1": {
                    "coordinator": mock_coordinator,
                    "storage": mock_storage,
                }
            }
        }
        return hass, mock_coordinator, mock_cover

    @pytest.mark.asyncio
    async def test_pause_service_calls_coordinator(
        self, mock_hass_with_data
    ) -> None:
        """Test pause service calls coordinator._pause_cover."""
        hass, coordinator, cover = mock_hass_with_data

        # Register services to capture handlers
        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        # Create mock service call
        call = MagicMock()
        call.data = {"entity_id": "cover.test"}

        # Execute pause handler
        await handlers["pause"](call)

        coordinator._pause_cover.assert_called_once_with(cover)

    @pytest.mark.asyncio
    async def test_resume_service_calls_coordinator(
        self, mock_hass_with_data
    ) -> None:
        """Test resume service calls coordinator.resume_cover."""
        hass, coordinator, cover = mock_hass_with_data

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"entity_id": "cover.test"}

        await handlers["resume"](call)

        coordinator.resume_cover.assert_called_once_with("cover.test")


class TestScenarioService:
    """Tests for set_scenario service."""

    @pytest.fixture
    def mock_hass_with_scenarios(self):
        """Create mock Home Assistant with scenario data."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()

        mock_storage = MagicMock()
        mock_storage.scenarios = {"summer": MagicMock(), "winter": MagicMock()}
        mock_storage.active_scenario = "everyday"
        mock_storage.async_save = AsyncMock()

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.async_request_refresh = AsyncMock()

        hass.data = {
            "cover_automatic": {
                "entry1": {
                    "coordinator": mock_coordinator,
                    "storage": mock_storage,
                }
            }
        }
        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_set_scenario_changes_active_scenario(
        self, mock_hass_with_scenarios
    ) -> None:
        """Test set_scenario changes the active scenario."""
        hass, storage, coordinator = mock_hass_with_scenarios

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"scenario": "summer"}

        await handlers["set_scenario"](call)

        assert storage.active_scenario == "summer"
        storage.async_save.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_scenario_invalid_scenario_logs_error(
        self, mock_hass_with_scenarios
    ) -> None:
        """Test set_scenario with invalid scenario logs error."""
        hass, storage, coordinator = mock_hass_with_scenarios

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"scenario": "nonexistent"}

        with patch(
            "custom_components.cover_automatic.services._LOGGER"
        ) as mock_logger:
            await handlers["set_scenario"](call)

            mock_logger.error.assert_called()
            storage.async_save.assert_not_called()


class TestExportImportServices:
    """Tests for export and import configuration services."""

    @pytest.fixture
    def mock_hass_with_export_data(self):
        """Create mock Home Assistant for export/import."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *args: fn(*args) if not args else fn())

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(
            return_value={"facades": {}, "covers": {}}
        )
        mock_storage.async_import_data = AsyncMock()

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.refresh_state_tracking = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        hass.data = {
            "cover_automatic": {
                "entry1": {
                    "coordinator": mock_coordinator,
                    "storage": mock_storage,
                }
            }
        }
        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_export_validates_path(self, mock_hass_with_export_data) -> None:
        """Test export_config validates path before writing."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/etc/passwd"}

        with patch(
            "custom_components.cover_automatic.services._validate_config_path",
            return_value=None,
        ):
            await handlers["export_config"](call)

        # Should not attempt to write
        hass.async_add_executor_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_validates_path(self, mock_hass_with_export_data) -> None:
        """Test import_config validates path before reading."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/etc/passwd"}

        with patch(
            "custom_components.cover_automatic.services._validate_config_path",
            return_value=None,
        ):
            await handlers["import_config"](call)

        storage.async_import_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_requires_path(self, mock_hass_with_export_data) -> None:
        """Test import_config requires path parameter."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {}

        with patch(
            "custom_components.cover_automatic.services._LOGGER"
        ) as mock_logger:
            await handlers["import_config"](call)

            mock_logger.error.assert_called()
            storage.async_import_data.assert_not_called()
