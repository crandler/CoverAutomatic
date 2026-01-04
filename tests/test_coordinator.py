"""Tests for CoverAutomatic coordinator."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.models import CoverStatus


class MockState:
    """Mock Home Assistant state object."""

    def __init__(self, state: str, attributes: dict | None = None) -> None:
        """Initialize mock state."""
        self.state = state
        self.attributes = attributes or {}


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.async_create_task = MagicMock()  # Simple mock, no side effect
    hass.data = {}
    # Required for DataUpdateCoordinator
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def mock_storage():
    """Create mock storage instance."""
    storage = MagicMock()
    storage._data = {
        "covers": {},
        "facades": {},
        "rules": {},
        "scenarios": {},
    }
    storage.covers = {}
    storage.facades = {}
    storage.rules = {}
    storage.scenarios = {}
    storage.active_scenario = "everyday"
    storage.outdoor_temp_sensor = None
    storage.indoor_temp_sensor = None
    storage.weather_entity = None
    storage.async_load = AsyncMock()
    storage.async_save = AsyncMock()
    storage.async_add_scenario = AsyncMock()
    storage.get_cover_raw = MagicMock(return_value=None)
    storage.update_cover_status = MagicMock()
    storage.update_cover_last_change = MagicMock()
    return storage


@pytest.fixture
def coordinator(mock_hass, mock_storage):
    """Create coordinator instance with mocked parent class."""
    from custom_components.cover_automatic.coordinator import CoverAutomaticCoordinator

    with patch(
        "custom_components.cover_automatic.coordinator.async_track_state_change_event"
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coord = CoverAutomaticCoordinator.__new__(CoverAutomaticCoordinator)
        # Manually set attributes that __init__ would set
        coord.hass = mock_hass
        coord.storage = mock_storage
        coord._tracked_entities = set()
        coord._unsub_state_change = []
        coord._cover_states = {}
        coord.data = {}
        coord.logger = MagicMock()
        coord.name = "cover_automatic"
        coord.update_interval = timedelta(seconds=60)
        coord.async_request_refresh = AsyncMock()
        # Additional attributes needed by parent class
        coord._unsub_refresh = None
        coord._debounced_refresh = MagicMock()
        coord._listeners = {}
        coord.last_update_success = True
        coord.async_set_updated_data = MagicMock()
        return coord


class TestCoordinatorInitialization:
    """Tests for coordinator initialization."""

    def test_coordinator_creation(self, coordinator, mock_hass, mock_storage) -> None:
        """Test coordinator can be created."""
        assert coordinator.hass == mock_hass
        assert coordinator.storage == mock_storage
        assert coordinator._tracked_entities == set()
        assert coordinator._cover_states == {}

    @pytest.mark.asyncio
    async def test_async_setup_loads_storage(self, coordinator, mock_storage) -> None:
        """Test async_setup loads storage data."""
        await coordinator.async_setup()
        mock_storage.async_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_creates_default_scenarios(
        self, coordinator, mock_storage
    ) -> None:
        """Test async_setup creates default scenarios when none exist."""
        mock_storage.scenarios = {}
        await coordinator.async_setup()
        # Should create 6 default scenarios
        assert mock_storage.async_add_scenario.call_count == 6


class TestCoverStatus:
    """Tests for cover status management."""

    def test_get_cover_status_returns_manual_when_not_found(
        self, coordinator, mock_storage
    ) -> None:
        """Test status is MANUAL when cover not in storage."""
        mock_storage.get_cover_raw.return_value = None
        status = coordinator.get_cover_status("cover.unknown")
        assert status == CoverStatus.MANUAL

    def test_get_cover_status_returns_manual_when_disabled(
        self, coordinator, mock_storage
    ) -> None:
        """Test status is MANUAL when auto_enabled is False."""
        mock_storage.get_cover_raw.return_value = {"auto_enabled": False}
        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.MANUAL

    def test_get_cover_status_returns_locked_when_lock_sensor_open(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test status is LOCKED when lock sensor is open."""
        mock_storage.get_cover_raw.return_value = {
            "auto_enabled": True,
            "lock_sensor": "binary_sensor.window",
        }
        mock_hass.states.get.return_value = MockState("on")

        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.LOCKED

    def test_get_cover_status_returns_locked_when_vent_sensor_open(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test status is LOCKED when vent sensor is open."""
        mock_storage.get_cover_raw.return_value = {
            "auto_enabled": True,
            "lock_sensor": None,
            "vent_sensor": "binary_sensor.vent",
        }
        mock_hass.states.get.return_value = MockState("on")

        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.LOCKED

    def test_get_cover_status_returns_auto_when_sensors_closed(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test status is AUTO when lock/vent sensors are closed."""
        mock_storage.get_cover_raw.return_value = {
            "auto_enabled": True,
            "lock_sensor": "binary_sensor.window",
            "vent_sensor": None,
        }
        mock_hass.states.get.return_value = MockState("off")

        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.AUTO

    def test_get_cover_status_respects_pause_timeout(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test PAUSED status expires based on pause_until."""
        coordinator._cover_states["cover.test"] = CoverStatus.PAUSED
        mock_storage.get_cover_raw.return_value = {
            "auto_enabled": True,
            "pause_until": 500,  # Expired (before current time 1000)
            "lock_sensor": None,
            "vent_sensor": None,
        }

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            status = coordinator.get_cover_status("cover.test")
            # Status transitions from PAUSED to AUTO when pause_until has expired
            assert status == CoverStatus.AUTO

    def test_resume_cover(self, coordinator, mock_storage) -> None:
        """Test resuming cover automation."""
        coordinator._cover_states["cover.test"] = CoverStatus.PAUSED
        mock_storage.get_cover_raw.return_value = {"entity_id": "cover.test"}

        coordinator.resume_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.AUTO.value, None
        )


class TestContactSensorHandling:
    """Tests for lock/vent sensor handling."""

    def test_get_covers_by_sensor_finds_lock_sensor(
        self, coordinator, mock_storage
    ) -> None:
        """Test finding covers by lock sensor."""
        mock_storage._data = {
            "covers": {
                "cover.living": {"lock_sensor": "binary_sensor.window1"},
                "cover.bedroom": {"lock_sensor": "binary_sensor.window2"},
            }
        }

        lock_covers, vent_covers = coordinator._get_covers_by_sensor(
            "binary_sensor.window1"
        )
        assert lock_covers == ["cover.living"]
        assert vent_covers == []

    def test_get_covers_by_sensor_finds_vent_sensor(
        self, coordinator, mock_storage
    ) -> None:
        """Test finding covers by vent sensor."""
        mock_storage._data = {
            "covers": {
                "cover.living": {"vent_sensor": "binary_sensor.vent1"},
            }
        }

        lock_covers, vent_covers = coordinator._get_covers_by_sensor(
            "binary_sensor.vent1"
        )
        assert lock_covers == []
        assert vent_covers == ["cover.living"]

    def test_lock_cover_sets_status(self, coordinator, mock_hass) -> None:
        """Test locking cover updates status to LOCKED."""
        # Mock to prevent actual async task creation
        mock_hass.async_create_task = MagicMock()

        coordinator._lock_cover("cover.test", 100)

        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED

    def test_unlock_cover_resets_status(self, coordinator, mock_storage) -> None:
        """Test unlocking cover resets status to AUTO."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED

        coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.AUTO.value, None
        )


class TestHysteresis:
    """Tests for hysteresis logic in position application."""

    @pytest.mark.asyncio
    async def test_position_change_below_minimum_is_skipped(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test small position changes are skipped."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 52,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "inverted": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50}
        )

        await coordinator.async_apply_positions()

        # Should not call service because 52-50=2 < 5
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_position_change_above_minimum_is_applied(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test larger position changes are applied."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 60,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50}
        )

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            await coordinator.async_apply_positions()

            mock_hass.services.async_call.assert_called_once_with(
                "cover",
                "set_cover_position",
                {"entity_id": "cover.test", "position": 60},
                blocking=False,
            )

    @pytest.mark.asyncio
    async def test_time_hysteresis_blocks_rapid_changes(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test time-based hysteresis blocks rapid position changes."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 60,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 300,
            "last_position_change": 900,  # 100 seconds ago
            "inverted": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50}
        )

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            await coordinator.async_apply_positions()

            # Should not call because 100 < 300 seconds
            mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_inverted_cover_position_is_flipped(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test inverted covers have position flipped."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 30,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": True,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50}
        )

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            await coordinator.async_apply_positions()

            # Target 30 inverted = 70
            mock_hass.services.async_call.assert_called_once_with(
                "cover",
                "set_cover_position",
                {"entity_id": "cover.test", "position": 70},
                blocking=False,
            )


class TestStateTracking:
    """Tests for state change tracking."""

    def test_setup_state_tracking_tracks_sun(self, coordinator, mock_storage) -> None:
        """Test state tracking includes sun entity."""
        mock_storage._data = {"covers": {}, "rules": {}}

        with patch(
            "custom_components.cover_automatic.coordinator.async_track_state_change_event"
        ) as mock_track:
            coordinator._setup_state_tracking()

            # Should track sun.sun
            call_args = mock_track.call_args
            tracked_entities = call_args[0][1]
            assert "sun.sun" in tracked_entities

    def test_setup_state_tracking_tracks_sensors(
        self, coordinator, mock_storage
    ) -> None:
        """Test state tracking includes configured sensors."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "lock_sensor": "binary_sensor.window",
                    "vent_sensor": "binary_sensor.vent",
                }
            },
            "rules": {},
        }
        mock_storage.outdoor_temp_sensor = "sensor.outdoor_temp"
        mock_storage.indoor_temp_sensor = "sensor.indoor_temp"
        mock_storage.weather_entity = "weather.home"

        with patch(
            "custom_components.cover_automatic.coordinator.async_track_state_change_event"
        ) as mock_track:
            coordinator._setup_state_tracking()

            call_args = mock_track.call_args
            tracked_entities = call_args[0][1]

            assert "binary_sensor.window" in tracked_entities
            assert "binary_sensor.vent" in tracked_entities
            assert "sensor.outdoor_temp" in tracked_entities
            assert "sensor.indoor_temp" in tracked_entities
            assert "weather.home" in tracked_entities

    def test_refresh_state_tracking_calls_full_refresh(self, coordinator) -> None:
        """Test refresh_state_tracking calls setup with full_refresh=True."""
        with patch.object(coordinator, "_setup_state_tracking") as mock_setup:
            coordinator.refresh_state_tracking()
            mock_setup.assert_called_once_with(full_refresh=True)

    def test_full_refresh_clears_old_listeners(self, coordinator, mock_storage) -> None:
        """Test full_refresh removes old listeners before re-registering."""
        mock_storage._data = {"covers": {}, "rules": {}}

        # Simulate existing listeners
        mock_unsub1 = MagicMock()
        mock_unsub2 = MagicMock()
        coordinator._unsub_state_change = [mock_unsub1, mock_unsub2]
        coordinator._tracked_entities = {"sun.sun", "cover.old"}

        with patch(
            "custom_components.cover_automatic.coordinator.async_track_state_change_event"
        ) as mock_track:
            mock_track.return_value = MagicMock()
            coordinator._setup_state_tracking(full_refresh=True)

            # Old listeners should be unsubscribed
            mock_unsub1.assert_called_once()
            mock_unsub2.assert_called_once()

            # Tracked entities should be cleared and rebuilt
            assert "cover.old" not in coordinator._tracked_entities
            assert "sun.sun" in coordinator._tracked_entities

    def test_incremental_tracking_keeps_old_listeners(
        self, coordinator, mock_storage
    ) -> None:
        """Test incremental tracking (full_refresh=False) keeps existing listeners."""
        mock_storage._data = {"covers": {"cover.new": {}}, "rules": {}}

        # Simulate existing listeners
        mock_unsub = MagicMock()
        coordinator._unsub_state_change = [mock_unsub]
        coordinator._tracked_entities = {"sun.sun"}

        with patch(
            "custom_components.cover_automatic.coordinator.async_track_state_change_event"
        ) as mock_track:
            mock_track.return_value = MagicMock()
            coordinator._setup_state_tracking(full_refresh=False)

            # Old listener should NOT be unsubscribed
            mock_unsub.assert_not_called()

            # New entity should be added
            assert "cover.new" in coordinator._tracked_entities
            assert "sun.sun" in coordinator._tracked_entities


class TestShutdown:
    """Tests for coordinator shutdown."""

    def test_async_shutdown_unsubscribes_all(self, coordinator) -> None:
        """Test shutdown unsubscribes all state change listeners."""
        mock_unsub1 = MagicMock()
        mock_unsub2 = MagicMock()
        coordinator._unsub_state_change = [mock_unsub1, mock_unsub2]

        coordinator.async_shutdown()

        mock_unsub1.assert_called_once()
        mock_unsub2.assert_called_once()
        assert coordinator._unsub_state_change == []
