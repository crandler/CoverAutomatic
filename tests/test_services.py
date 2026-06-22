"""Tests for CoverAutomatic services."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.services import (
    _validate_config_path,
    _validate_export_path,
    async_setup_services,
    async_unload_services,
)


@dataclass
class MockRuntimeData:
    """Mock runtime data for tests."""

    coordinator: MagicMock
    storage: MagicMock


def _make_mock_entry(coordinator, storage, entry_id="entry1"):
    """Create a mock config entry with runtime_data."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.runtime_data = MockRuntimeData(coordinator=coordinator, storage=storage)
    return entry


class TestPathValidation:
    """Tests for path validation security."""

    def test_valid_path_in_config_dir(self) -> None:
        """Test valid path within the config dir is accepted."""
        result = _validate_config_path("/config/backup.yaml", "/config")
        assert result is not None

    def test_config_dir_drives_allowed_base(self) -> None:
        """Test the allowed base is the passed config_dir, not a hardcoded list."""
        result = _validate_config_path("/data/ha/backup.yaml", "/data/ha")
        assert result is not None

    def test_path_traversal_rejected(self) -> None:
        """Test path traversal attempts outside the config dir are rejected."""
        result = _validate_config_path("/etc/passwd", "/config")
        assert result is None

    def test_path_outside_config_dir_rejected(self) -> None:
        """Test paths outside the config dir are rejected."""
        result = _validate_config_path("/root/secrets.yaml", "/config")
        assert result is None

    def test_invalid_path_returns_none(self) -> None:
        """Test invalid path returns None."""
        with patch.object(Path, "resolve", side_effect=ValueError("Bad path")):
            result = _validate_config_path("\x00invalid", "/config")
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
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[])
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
        mock_coordinator.pause_cover = MagicMock()
        mock_coordinator.resume_cover = MagicMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_coordinator, mock_cover

    @pytest.mark.asyncio
    async def test_pause_service_calls_coordinator(
        self, mock_hass_with_data
    ) -> None:
        """Test pause service calls coordinator.pause_cover."""
        hass, coordinator, cover = mock_hass_with_data

        # Register services to capture handlers
        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        # Create mock service call
        call = MagicMock()
        call.data = {"entity_id": "cover.test"}

        # Execute pause handler
        await handlers["pause"](call)

        coordinator.pause_cover.assert_called_once_with(cover)

    @pytest.mark.asyncio
    async def test_resume_service_calls_coordinator(
        self, mock_hass_with_data
    ) -> None:
        """Test resume service calls coordinator.resume_cover."""
        hass, coordinator, cover = mock_hass_with_data

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
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

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_set_scenario_changes_active_scenario(
        self, mock_hass_with_scenarios
    ) -> None:
        """Test set_scenario changes the active scenario."""
        hass, storage, coordinator = mock_hass_with_scenarios

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
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

        def capture_register(domain, service, handler, **kwargs):
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

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_export_validates_path(self, mock_hass_with_export_data) -> None:
        """Test export_config validates path before writing."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/etc/passwd"}
        call.context.user_id = None

        with patch(
            "custom_components.cover_automatic.services._validate_export_path",
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

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/etc/passwd"}
        call.context.user_id = None

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

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {}
        call.context.user_id = None

        with patch(
            "custom_components.cover_automatic.services._LOGGER"
        ) as mock_logger:
            await handlers["import_config"](call)

            mock_logger.error.assert_called()
            storage.async_import_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_rejects_oversized_file(
        self, mock_hass_with_export_data
    ) -> None:
        """Test import_config rejects files exceeding MAX_IMPORT_FILE_SIZE."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/big.yaml"}
        call.context.user_id = None

        mock_stat = MagicMock()
        mock_stat.st_size = 2_000_000  # 2 MB, over limit

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = mock_stat

        with (
            patch(
                "custom_components.cover_automatic.services._validate_config_path",
                return_value=mock_path,
            ),
            patch(
                "custom_components.cover_automatic.services._LOGGER"
            ) as mock_logger,
        ):
            await handlers["import_config"](call)

            mock_logger.error.assert_called()
            storage.async_import_data.assert_not_called()


class TestPauseAllResumeAllServices:
    """Tests for pause_all and resume_all services."""

    @pytest.fixture
    def mock_hass_with_multiple_covers(self):
        """Create mock Home Assistant with multiple covers."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()

        cover1 = MagicMock()
        cover1.entity_id = "cover.living"
        cover2 = MagicMock()
        cover2.entity_id = "cover.bedroom"

        mock_storage = MagicMock()
        mock_storage.covers = {
            "cover.living": cover1,
            "cover.bedroom": cover2,
        }

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.pause_cover = MagicMock()
        mock_coordinator.resume_cover = MagicMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_coordinator, [cover1, cover2]

    @pytest.mark.asyncio
    async def test_pause_all_pauses_every_cover(
        self, mock_hass_with_multiple_covers
    ) -> None:
        """Test pause_all calls pause_cover for every cover."""
        hass, coordinator, covers = mock_hass_with_multiple_covers

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {}

        await handlers["pause_all"](call)

        assert coordinator.pause_cover.call_count == 2

    @pytest.mark.asyncio
    async def test_resume_all_resumes_every_cover(
        self, mock_hass_with_multiple_covers
    ) -> None:
        """Test resume_all calls resume_cover for every cover."""
        hass, coordinator, covers = mock_hass_with_multiple_covers

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {}

        await handlers["resume_all"](call)

        assert coordinator.resume_cover.call_count == 2


class TestExportHappyPath:
    """Tests for successful export_config execution."""

    @pytest.fixture
    def mock_hass_with_export_data(self):
        """Create mock Home Assistant for export happy path."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *args: fn(*args) if not args else fn())
        hass.config.path = MagicMock(return_value="/config/cover_automatic_backup.yaml")
        hass.config.config_dir = "/config"

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(return_value={"facades": {}, "covers": {}})
        mock_storage.async_import_data = AsyncMock()

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.refresh_state_tracking = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_export_writes_yaml_file(self, mock_hass_with_export_data) -> None:
        """Test export_config attempts to write the YAML file via executor job."""
        hass, storage, coordinator = mock_hass_with_export_data

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/cover_automatic/backup.yaml"}
        call.context.user_id = None

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "custom_components.cover_automatic.services._validate_export_path",
            return_value=mock_path,
        ):
            await handlers["export_config"](call)

        hass.async_add_executor_job.assert_called_once()


class TestExportPathRestrictions:
    """Tests for export path hardening (subdirectory + extension whitelist)."""

    def test_rejects_ha_core_file(self) -> None:
        """Export must not target files outside the export subdirectory."""
        assert _validate_export_path("/config/configuration.yaml", "/config") is None

    def test_rejects_non_yaml_extension(self) -> None:
        """Export must use a .yaml/.yml extension."""
        assert (
            _validate_export_path("/config/cover_automatic/backup.txt", "/config")
            is None
        )

    def test_rejects_traversal_out_of_subdir(self) -> None:
        """Traversal escaping the export subdirectory is rejected."""
        assert (
            _validate_export_path(
                "/config/cover_automatic/../configuration.yaml", "/config"
            )
            is None
        )

    def test_accepts_yaml_in_subdir(self) -> None:
        """Absolute YAML path inside the export subdirectory is accepted."""
        result = _validate_export_path(
            "/config/cover_automatic/backup.yaml", "/config"
        )
        assert result == Path("/config/cover_automatic/backup.yaml")

    def test_accepts_yml_extension(self) -> None:
        """The .yml extension is accepted as well."""
        result = _validate_export_path("/config/cover_automatic/backup.yml", "/config")
        assert result is not None

    def test_relative_path_resolves_into_subdir(self) -> None:
        """Relative paths resolve inside the export subdirectory."""
        result = _validate_export_path("backup.yaml", "/config")
        assert result == Path("/config/cover_automatic/backup.yaml")

    @pytest.fixture
    def mock_hass_for_export(self):
        """Create mock Home Assistant for export path restriction tests."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        hass.config.config_dir = "/config"
        hass.config.path = MagicMock(
            return_value="/config/cover_automatic/cover_automatic_backup.yaml"
        )

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(return_value={"facades": {}, "covers": {}})

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass

    async def _get_export_handler(self, hass):
        """Register services and return the export_config handler."""
        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register
        await async_setup_services(hass)
        return handlers["export_config"]

    @pytest.mark.asyncio
    async def test_export_rejects_path_outside_subdir(
        self, mock_hass_for_export
    ) -> None:
        """Export to a HA core file inside /config is rejected without writing."""
        hass = mock_hass_for_export
        handler = await self._get_export_handler(hass)

        call = MagicMock()
        call.data = {"path": "/config/configuration.yaml"}
        call.context.user_id = None

        await handler(call)

        hass.async_add_executor_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_default_path_in_subdir(self, mock_hass_for_export) -> None:
        """Default export path lands inside the export subdirectory."""
        hass = mock_hass_for_export
        handler = await self._get_export_handler(hass)

        call = MagicMock()
        call.data = {}
        call.context.user_id = None

        await handler(call)

        hass.config.path.assert_called_once_with(
            "cover_automatic", "cover_automatic_backup.yaml"
        )
        hass.async_add_executor_job.assert_called_once()


class TestImportHappyPath:
    """Tests for successful import_config execution."""

    @pytest.fixture
    def mock_hass_with_import_data(self):
        """Create mock Home Assistant for import happy path."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()

        import_data = {"facades": {}, "covers": {}, "rules": {}, "scenarios": {}}
        hass.async_add_executor_job = AsyncMock(return_value=import_data)
        hass.config.config_dir = "/config"

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(return_value={"facades": {}, "covers": {}})
        mock_storage.async_import_data = AsyncMock()

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.refresh_state_tracking = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator, import_data

    @pytest.mark.asyncio
    async def test_import_reads_and_applies_data(
        self, mock_hass_with_import_data
    ) -> None:
        """Test import_config reads the file and applies data to storage and coordinator."""
        hass, storage, coordinator, import_data = mock_hass_with_import_data

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = None

        mock_stat = MagicMock()
        mock_stat.st_size = 100

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = mock_stat

        with patch(
            "custom_components.cover_automatic.services._validate_config_path",
            return_value=mock_path,
        ):
            await handlers["import_config"](call)

        storage.async_import_data.assert_called_once_with(import_data)
        coordinator.refresh_state_tracking.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()


class TestImportValidationErrors:
    """Tests for import_config error handling from storage."""

    @pytest.fixture
    def mock_hass_for_import_errors(self):
        """Create mock Home Assistant for import error scenarios."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()

        import_data = {"facades": {}, "covers": {}, "rules": {}, "scenarios": {}}
        hass.async_add_executor_job = AsyncMock(return_value=import_data)
        hass.config.config_dir = "/config"

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(return_value={"facades": {}, "covers": {}})

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.refresh_state_tracking = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_import_value_error_from_storage(
        self, mock_hass_for_import_errors
    ) -> None:
        """Test import_config catches ValueError from storage gracefully."""
        hass, storage, coordinator = mock_hass_for_import_errors
        storage.async_import_data = AsyncMock(side_effect=ValueError("bad data"))

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = None

        mock_stat = MagicMock()
        mock_stat.st_size = 100

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = mock_stat

        with patch(
            "custom_components.cover_automatic.services._validate_config_path",
            return_value=mock_path,
        ):
            # Must not raise
            await handlers["import_config"](call)

        coordinator.refresh_state_tracking.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_type_error_from_storage(
        self, mock_hass_for_import_errors
    ) -> None:
        """Test import_config catches TypeError from storage gracefully."""
        hass, storage, coordinator = mock_hass_for_import_errors
        storage.async_import_data = AsyncMock(side_effect=TypeError("wrong type"))

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register

        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = None

        mock_stat = MagicMock()
        mock_stat.st_size = 100

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = mock_stat

        with patch(
            "custom_components.cover_automatic.services._validate_config_path",
            return_value=mock_path,
        ):
            # Must not raise
            await handlers["import_config"](call)

        coordinator.refresh_state_tracking.assert_not_called()


class TestAdminRequirement:
    """Tests for admin-only service access control."""

    @pytest.fixture
    def mock_hass_with_auth(self):
        """Create mock Home Assistant with auth support."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.services.async_register = MagicMock()
        hass.config.path = MagicMock(return_value="/config/cover_automatic_backup.yaml")
        hass.config.config_dir = "/config"

        mock_storage = MagicMock()
        mock_storage.get_raw_data = MagicMock(return_value={"facades": {}, "covers": {}})
        mock_storage.async_import_data = AsyncMock()

        mock_coordinator = MagicMock()
        mock_coordinator.storage = mock_storage
        mock_coordinator.refresh_state_tracking = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        mock_entry = _make_mock_entry(mock_coordinator, mock_storage)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        return hass, mock_storage, mock_coordinator

    @pytest.mark.asyncio
    async def test_export_rejects_non_admin_user(self, mock_hass_with_auth) -> None:
        """Test export_config rejects non-admin users."""
        from homeassistant.exceptions import HomeAssistantError

        hass, storage, coordinator = mock_hass_with_auth

        mock_user = MagicMock()
        mock_user.is_admin = False
        hass.auth = MagicMock()
        hass.auth.async_get_user = AsyncMock(return_value=mock_user)

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register
        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = "non_admin_user_123"

        with pytest.raises(HomeAssistantError, match="Admin access required"):
            await handlers["export_config"](call)

    @pytest.mark.asyncio
    async def test_import_rejects_non_admin_user(self, mock_hass_with_auth) -> None:
        """Test import_config rejects non-admin users."""
        from homeassistant.exceptions import HomeAssistantError

        hass, storage, coordinator = mock_hass_with_auth

        mock_user = MagicMock()
        mock_user.is_admin = False
        hass.auth = MagicMock()
        hass.auth.async_get_user = AsyncMock(return_value=mock_user)

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register
        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = "non_admin_user_123"

        with pytest.raises(HomeAssistantError, match="Admin access required"):
            await handlers["import_config"](call)

    @pytest.mark.asyncio
    async def test_export_allows_admin_user(self, mock_hass_with_auth) -> None:
        """Test export_config allows admin users."""
        hass, storage, coordinator = mock_hass_with_auth

        mock_user = MagicMock()
        mock_user.is_admin = True
        hass.auth = MagicMock()
        hass.auth.async_get_user = AsyncMock(return_value=mock_user)
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *args: fn(*args) if not args else fn())

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register
        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = "admin_user_123"

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "custom_components.cover_automatic.services._validate_export_path",
            return_value=mock_path,
        ):
            # Should not raise
            await handlers["export_config"](call)

    @pytest.mark.asyncio
    async def test_export_allows_internal_call(self, mock_hass_with_auth) -> None:
        """Test export_config allows internal calls without user context."""
        hass, storage, coordinator = mock_hass_with_auth
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *args: fn(*args) if not args else fn())

        handlers = {}

        def capture_register(domain, service, handler, **kwargs):
            handlers[service] = handler

        hass.services.async_register = capture_register
        await async_setup_services(hass)

        call = MagicMock()
        call.data = {"path": "/config/backup.yaml"}
        call.context.user_id = None

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch(
            "custom_components.cover_automatic.services._validate_export_path",
            return_value=mock_path,
        ):
            # Should not raise -- internal/automation calls pass through
            await handlers["export_config"](call)
