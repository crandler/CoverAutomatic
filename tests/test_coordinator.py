"""Tests for CoverAutomatic coordinator."""
from __future__ import annotations

import asyncio
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
    storage.wind_sensor = None
    storage.wind_speed_threshold = 0.0
    storage.wind_speed_hysteresis = 0.0
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
        coord._last_positions = {}
        coord._last_tilt_positions = {}
        coord._tilt_tasks = {}
        coord._last_command_time = {}
        coord._pre_lock_states = {}
        coord._wind_protected = False
        coord._hysteresis_info = {}
        coord._last_matching_rules = {}
        coord.log_storage = None
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


class TestActiveRules:
    """Tests for active rules tracking."""

    def test_get_active_rules_empty_data(self, coordinator) -> None:
        """Test get_active_rules returns empty when no data."""
        coordinator.data = {}
        assert coordinator.get_active_rules() == {}

    def test_get_active_rules_no_data(self, coordinator) -> None:
        """Test get_active_rules returns empty when data is None."""
        coordinator.data = None
        assert coordinator.get_active_rules() == {}

    def test_get_active_rules_returns_mapping(self, coordinator) -> None:
        """Test get_active_rules returns rule-to-covers mapping."""
        coordinator.data = {
            "active_rules": {
                "rule1": ["cover.a", "cover.b"],
                "rule2": ["cover.c"],
            }
        }
        result = coordinator.get_active_rules()
        assert result == {"rule1": ["cover.a", "cover.b"], "rule2": ["cover.c"]}


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

    def test_sync_sets_locked_when_lock_sensor_open(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _sync_cover_statuses sets LOCKED when lock sensor is open."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "lock_sensor": "binary_sensor.window",
                    "lock_position": 100,
                    "vent_sensor": None,
                    "inverted": False,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]
        mock_hass.states.get.return_value = MockState("on")
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._sync_cover_statuses()

        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED
        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.LOCKED

    def test_sync_sets_locked_when_vent_sensor_open(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _sync_cover_statuses sets VENTING when vent sensor is open."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "lock_sensor": None,
                    "vent_sensor": "binary_sensor.vent",
                    "vent_position": 30,
                    "inverted": False,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]
        mock_hass.states.get.return_value = MockState("on")
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._sync_cover_statuses()

        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        status = coordinator.get_cover_status("cover.test")
        assert status == CoverStatus.VENTING

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

    def test_sync_respects_pause_timeout(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _sync_cover_statuses expires PAUSED based on pause_until."""
        coordinator._cover_states["cover.test"] = CoverStatus.PAUSED
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "pause_until": 500,  # Expired (before current time 1000)
                    "lock_sensor": None,
                    "vent_sensor": None,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000

            coordinator._sync_cover_statuses()

            assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
            status = coordinator.get_cover_status("cover.test")
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
        coordinator.async_set_updated_data.assert_called_once()

    def test_resume_cover_nonexistent_no_op(self, coordinator, mock_storage) -> None:
        """Test resuming a nonexistent cover does nothing."""
        mock_storage.get_cover_raw.return_value = None

        coordinator.resume_cover("cover.nonexistent")

        assert "cover.nonexistent" not in coordinator._cover_states
        mock_storage.update_cover_status.assert_not_called()
        coordinator.async_set_updated_data.assert_not_called()


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

    def test_lock_cover_sets_status(self, coordinator, mock_hass, mock_storage) -> None:
        """Test locking cover updates status to LOCKED."""
        mock_hass.async_create_task = MagicMock()
        mock_storage.get_cover_raw.return_value = {"inverted": False}

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._lock_cover("cover.test", 100)

        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED

    def test_unlock_cover_resets_status(self, coordinator, mock_hass, mock_storage) -> None:
        """Test unlocking cover resets status to AUTO."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        coordinator._pre_lock_states["cover.test"] = CoverStatus.AUTO
        mock_storage.get_cover_raw.return_value = {"pause_until": None}
        mock_hass.states.get.return_value = MockState("open", {"current_position": 50})

        coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.AUTO.value, None
        )

    def test_unlock_cover_noop_without_pre_lock_state(self, coordinator, mock_hass, mock_storage) -> None:
        """Test unlocking cover is a no-op if no pre-lock state exists."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED

        coordinator._unlock_cover("cover.test")

        # Status unchanged, no storage call
        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED
        mock_storage.update_cover_status.assert_not_called()


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

    @pytest.mark.asyncio
    async def test_async_shutdown_unsubscribes_all(self, coordinator, mock_storage) -> None:
        """Test shutdown unsubscribes all state change listeners."""
        mock_unsub1 = MagicMock()
        mock_unsub2 = MagicMock()
        coordinator._unsub_state_change = [mock_unsub1, mock_unsub2]
        mock_storage._save_task = None

        await coordinator.async_shutdown()

        mock_unsub1.assert_called_once()
        mock_unsub2.assert_called_once()
        assert coordinator._unsub_state_change == []


class TestStateChangeRouting:
    """Tests for _async_on_state_change routing logic."""

    def test_state_change_routes_to_cover_handler(
        self, coordinator, mock_storage
    ) -> None:
        """When entity_id is in covers, _handle_cover_state_change is called."""
        mock_storage._data = {"covers": {"cover.living": {}}}

        event = MagicMock()
        event.data = {
            "entity_id": "cover.living",
            "old_state": MockState("open", {"current_position": 50}),
            "new_state": MockState("open", {"current_position": 60}),
        }

        with patch.object(coordinator, "_handle_cover_state_change") as mock_handler:
            coordinator._async_on_state_change(event)
            mock_handler.assert_called_once_with(
                "cover.living",
                event.data["old_state"],
                event.data["new_state"],
            )

    def test_state_change_routes_to_contact_sensor_handler(
        self, coordinator, mock_storage
    ) -> None:
        """When entity_id is a lock/vent sensor, _handle_contact_sensor_change is called."""
        mock_storage._data = {
            "covers": {
                "cover.living": {"lock_sensor": "binary_sensor.window"},
            }
        }

        event = MagicMock()
        event.data = {
            "entity_id": "binary_sensor.window",
            "old_state": MockState("off"),
            "new_state": MockState("on"),
        }

        with patch.object(
            coordinator, "_handle_contact_sensor_change"
        ) as mock_handler:
            coordinator._async_on_state_change(event)
            mock_handler.assert_called_once_with(
                "binary_sensor.window",
                ["cover.living"],
                [],
                event.data["old_state"],
                event.data["new_state"],
            )

    def test_state_change_triggers_refresh_for_other_entities(
        self, coordinator, mock_storage
    ) -> None:
        """Entities not in covers and not sensors trigger async_request_refresh."""
        mock_storage._data = {"covers": {}}

        event = MagicMock()
        event.data = {
            "entity_id": "sensor.outdoor_temp",
            "old_state": MockState("20"),
            "new_state": MockState("22"),
        }

        coordinator._async_on_state_change(event)

        coordinator.hass.async_create_task.assert_called_once()


class TestUnlockCoverRestore:
    """Tests for _unlock_cover previous-state restoration."""

    def test_unlock_restores_paused_when_not_expired(
        self, coordinator, mock_storage
    ) -> None:
        """When previous was PAUSED and pause not yet expired, restores PAUSED."""
        coordinator._pre_lock_states["cover.test"] = CoverStatus.PAUSED
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        mock_storage.get_cover_raw.return_value = {"pause_until": 9999999999.0}
        coordinator.hass.states.get.return_value = MockState(
            "open", {"current_position": 45}
        )

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.PAUSED
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.PAUSED.value, 9999999999.0
        )
        # async_request_refresh must NOT have been scheduled
        coordinator.async_request_refresh.assert_not_awaited()

    def test_unlock_restores_auto_when_pause_expired(
        self, coordinator, mock_storage
    ) -> None:
        """When previous was PAUSED but pause already expired, restores AUTO."""
        coordinator._pre_lock_states["cover.test"] = CoverStatus.PAUSED
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        # pause_until is in the past relative to mocked now (1000.0)
        mock_storage.get_cover_raw.return_value = {"pause_until": 500.0}
        coordinator.hass.states.get.return_value = MockState(
            "open", {"current_position": 45}
        )

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.AUTO.value, None
        )

    def test_unlock_restores_manual_when_was_manual(
        self, coordinator, mock_storage
    ) -> None:
        """When previous was MANUAL, restores MANUAL without scheduling refresh."""
        coordinator._pre_lock_states["cover.test"] = CoverStatus.MANUAL
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        coordinator.hass.states.get.return_value = MockState(
            "open", {"current_position": 60}
        )

        coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.MANUAL
        assert coordinator._last_positions["cover.test"] == 60
        # Must persist MANUAL status to storage
        mock_storage.update_cover_status.assert_called_once_with(
            "cover.test", CoverStatus.MANUAL.value, None
        )
        # Must NOT schedule refresh (stays MANUAL)
        coordinator.async_request_refresh.assert_not_awaited()

    def test_unlock_restores_venting_when_sensor_still_open(
        self, coordinator, mock_storage
    ) -> None:
        """When previous was VENTING and vent sensor still open, restores VENTING."""
        coordinator._pre_lock_states["cover.test"] = CoverStatus.VENTING
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        mock_storage.get_cover_raw.return_value = {"vent_sensor": "binary_sensor.vent"}
        coordinator.hass.states.get.side_effect = lambda eid: {
            "binary_sensor.vent": MockState("on"),
            "cover.test": MockState("open", {"current_position": 30}),
        }.get(eid)

        coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.VENTING.value, None
        )
        coordinator.async_request_refresh.assert_not_awaited()

    def test_unlock_restores_auto_when_venting_sensor_closed(
        self, coordinator, mock_storage
    ) -> None:
        """When previous was VENTING but vent sensor now closed, restores AUTO."""
        coordinator._pre_lock_states["cover.test"] = CoverStatus.VENTING
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        mock_storage.get_cover_raw.return_value = {"vent_sensor": "binary_sensor.vent"}
        coordinator.hass.states.get.side_effect = lambda eid: {
            "binary_sensor.vent": MockState("off"),
            "cover.test": MockState("open", {"current_position": 30}),
        }.get(eid)

        coordinator._unlock_cover("cover.test")

        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_with(
            "cover.test", CoverStatus.AUTO.value, None
        )


class TestManualOverrideDetection:
    """Tests for _handle_cover_state_change manual override detection."""

    def _make_cover(self):
        """Return a minimal CoverConfig mock."""
        from custom_components.cover_automatic.models import CoverConfig

        cover = MagicMock(spec=CoverConfig)
        cover.entity_id = "cover.test"
        cover.auto_enabled = True
        cover.pause_duration = 30
        return cover

    def test_moving_state_ignored(self, coordinator, mock_storage) -> None:
        """opening/closing states do not trigger manual override detection."""
        cover = self._make_cover()
        mock_storage.covers = {"cover.test": cover}
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        coordinator._last_positions["cover.test"] = 80
        # Simulate command issued long ago (outside settle time)
        coordinator._last_command_time["cover.test"] = 0.0

        for moving_state in ("opening", "closing"):
            new_state = MockState(moving_state, {"current_position": 40})
            with patch.object(coordinator, "pause_cover") as mock_pause:
                with patch(
                    "custom_components.cover_automatic.coordinator.time_mod"
                ) as mock_time:
                    mock_time.monotonic.return_value = 9999.0
                    coordinator._handle_cover_state_change(
                        "cover.test", None, new_state
                    )
                mock_pause.assert_not_called()

    def test_within_settle_time_ignored(self, coordinator, mock_storage) -> None:
        """Position change within SETTLE_TIME after a command is ignored."""
        cover = self._make_cover()
        mock_storage.covers = {"cover.test": cover}
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        coordinator._last_positions["cover.test"] = 80
        coordinator._last_command_time["cover.test"] = 1000.0

        new_state = MockState("open", {"current_position": 40})

        with patch.object(coordinator, "pause_cover") as mock_pause:
            with patch(
                "custom_components.cover_automatic.coordinator.time_mod"
            ) as mock_time:
                # Only 5 seconds elapsed, well within SETTLE_TIME (30)
                mock_time.monotonic.return_value = 1005.0
                coordinator._handle_cover_state_change("cover.test", None, new_state)
            mock_pause.assert_not_called()

    def test_manual_override_detected(self, coordinator, mock_storage) -> None:
        """Position mismatch outside settle time with AUTO status triggers pause."""
        cover = self._make_cover()
        mock_storage.covers = {"cover.test": cover}
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        coordinator._last_positions["cover.test"] = 80
        coordinator._last_command_time["cover.test"] = 0.0

        # current_position 40 vs expected 80: diff=40 > MANUAL_OVERRIDE_TOLERANCE=2
        new_state = MockState("open", {"current_position": 40})

        with patch.object(coordinator, "pause_cover") as mock_pause:
            with patch(
                "custom_components.cover_automatic.coordinator.time_mod"
            ) as mock_time:
                mock_time.monotonic.return_value = 9999.0
                coordinator._handle_cover_state_change("cover.test", None, new_state)
            mock_pause.assert_called_once_with(cover)


class TestLockVentTransition:
    """Tests for lock->vent fallback in _handle_contact_sensor_change."""

    def test_lock_to_vent_transition(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Lock sensor closes while vent sensor still open -> switches to VENTING."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        cover_raw = {
            "lock_position": 100,
            "vent_position": 30,
            "vent_sensor": "binary_sensor.vent",
            "vent_tilt_position": None,
            "inverted": False,
        }
        mock_storage.get_cover_raw.return_value = cover_raw

        # Vent sensor is still open
        mock_hass.states.get.return_value = MockState("on")

        coordinator._handle_contact_sensor_change(
            "binary_sensor.window",
            ["cover.test"],  # lock_covers
            [],              # vent_covers
            MockState("on"),
            MockState("off"),
        )
        # Should switch to VENTING, not unlock
        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING


class TestLockCoverInverted:
    """Tests for _lock_cover with inverted cover flag."""

    def test_lock_cover_inverted_position(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Inverted cover applies 100-lock_position as actual position."""
        mock_storage.get_cover_raw.return_value = {"inverted": True}
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._lock_cover("cover.test", 100)

        assert coordinator._last_positions["cover.test"] == 0  # 100 - 100
        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED

        mock_hass.async_create_task.assert_called_once()
        service_call_args = mock_hass.services.async_call.call_args
        assert service_call_args[0][2]["position"] == 0


class TestOrphanCleanup:
    """Tests for orphan runtime dict cleanup during full refresh."""

    def test_full_refresh_cleans_orphan_runtime_dicts(
        self, coordinator, mock_storage
    ) -> None:
        """Orphaned entries in runtime dicts are removed on full_refresh=True."""
        # cover.gone no longer exists in storage; cover.active still does
        mock_storage._data = {"covers": {"cover.active": {}}, "rules": {}}

        coordinator._cover_states["cover.gone"] = CoverStatus.AUTO
        coordinator._cover_states["cover.active"] = CoverStatus.AUTO
        coordinator._last_positions["cover.gone"] = 50
        coordinator._last_positions["cover.active"] = 50
        coordinator._last_tilt_positions["cover.gone"] = 40
        coordinator._last_tilt_positions["cover.active"] = 60
        coordinator._tilt_tasks["cover.gone"] = MagicMock(spec=asyncio.Task, done=MagicMock(return_value=False))
        coordinator._pre_lock_states["cover.gone"] = CoverStatus.AUTO
        coordinator._last_command_time["cover.gone"] = 123.0
        coordinator._last_command_time["cover.active"] = 456.0

        with patch(
            "custom_components.cover_automatic.coordinator.async_track_state_change_event"
        ) as mock_track:
            mock_track.return_value = MagicMock()
            coordinator._setup_state_tracking(full_refresh=True)

        assert "cover.gone" not in coordinator._cover_states
        assert "cover.active" in coordinator._cover_states
        assert "cover.gone" not in coordinator._last_positions
        assert "cover.active" in coordinator._last_positions
        assert "cover.gone" not in coordinator._last_tilt_positions
        assert "cover.active" in coordinator._last_tilt_positions
        assert "cover.gone" not in coordinator._pre_lock_states
        assert "cover.gone" not in coordinator._last_command_time
        assert "cover.active" in coordinator._last_command_time


class TestSyncCoverStatuses:
    """Tests for _sync_cover_statuses."""

    def test_sync_auto_enabled_false_sets_manual(
        self, coordinator, mock_storage
    ) -> None:
        """auto_enabled=False causes the cover to be set to MANUAL status."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": False,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {"auto_enabled": False}

        coordinator._sync_cover_statuses()

        assert coordinator._cover_states["cover.test"] == CoverStatus.MANUAL


class TestRestoreCoverStates:
    """Tests for _restore_cover_states on startup."""

    def test_restore_paused_with_valid_pause_until(self, coordinator, mock_storage) -> None:
        """PAUSED covers with unexpired pause_until are restored."""
        from homeassistant.util import dt as dt_util

        future_ts = dt_util.now().timestamp() + 3600  # 1 hour from now
        mock_storage._data = {
            "covers": {
                "cover.bedroom": {
                    "entity_id": "cover.bedroom",
                    "name": "Bedroom",
                    "status": "paused",
                    "pause_until": future_ts,
                    "auto_enabled": True,
                },
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }

        coordinator._restore_cover_states()

        assert coordinator._cover_states["cover.bedroom"] == CoverStatus.PAUSED
        mock_storage.update_cover_status.assert_not_called()

    def test_restore_paused_expired_resets_to_auto(self, coordinator, mock_storage) -> None:
        """PAUSED covers with expired pause_until are reset to AUTO."""
        from homeassistant.util import dt as dt_util

        past_ts = dt_util.now().timestamp() - 100  # expired
        mock_storage._data = {
            "covers": {
                "cover.living": {
                    "entity_id": "cover.living",
                    "name": "Living",
                    "status": "paused",
                    "pause_until": past_ts,
                    "auto_enabled": True,
                },
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }

        coordinator._restore_cover_states()

        assert coordinator._cover_states["cover.living"] == CoverStatus.AUTO
        mock_storage.update_cover_status.assert_called_once_with(
            "cover.living", "auto", None
        )

    def test_restore_locked_resets_to_auto(self, coordinator, mock_storage) -> None:
        """LOCKED covers are reset to AUTO (re-derived from sensors on sync)."""
        mock_storage._data = {
            "covers": {
                "cover.kitchen": {
                    "entity_id": "cover.kitchen",
                    "name": "Kitchen",
                    "status": "locked",
                    "auto_enabled": True,
                },
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }

        coordinator._restore_cover_states()

        assert coordinator._cover_states["cover.kitchen"] == CoverStatus.AUTO

    def test_restore_auto_stays_auto(self, coordinator, mock_storage) -> None:
        """AUTO covers stay AUTO."""
        mock_storage._data = {
            "covers": {
                "cover.office": {
                    "entity_id": "cover.office",
                    "name": "Office",
                    "status": "auto",
                    "auto_enabled": True,
                },
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }

        coordinator._restore_cover_states()

        assert coordinator._cover_states["cover.office"] == CoverStatus.AUTO

    def test_restore_paused_no_pause_until(self, coordinator, mock_storage) -> None:
        """PAUSED without pause_until is reset to AUTO."""
        mock_storage._data = {
            "covers": {
                "cover.bath": {
                    "entity_id": "cover.bath",
                    "name": "Bath",
                    "status": "paused",
                    "pause_until": None,
                    "auto_enabled": True,
                },
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }

        coordinator._restore_cover_states()

        assert coordinator._cover_states["cover.bath"] == CoverStatus.AUTO


class TestShutdownPendingSave:
    """Tests for async_shutdown pending-save flush."""

    @pytest.mark.asyncio
    async def test_shutdown_flushes_pending_save(
        self, coordinator, mock_storage
    ) -> None:
        """When _save_task is not None it is cancelled via flush_pending_save and async_save is called."""
        mock_task = MagicMock()
        mock_storage._save_task = mock_task
        coordinator._unsub_state_change = []

        await coordinator.async_shutdown()

        mock_storage.flush_pending_save.assert_called_once()
        mock_storage.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_handles_save_error(
        self, coordinator, mock_storage
    ) -> None:
        """When async_save raises during shutdown, no exception propagates."""
        mock_storage.async_save.side_effect = OSError("disk full")
        coordinator._unsub_state_change = []

        # Must not raise
        await coordinator.async_shutdown()

        mock_storage.flush_pending_save.assert_called_once()
        mock_storage.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_tilt_tasks(
        self, coordinator, mock_storage
    ) -> None:
        """Shutdown cancels all pending tilt tasks."""
        mock_task = MagicMock()
        mock_task.done.return_value = False
        coordinator._tilt_tasks = {"cover.test": mock_task}
        coordinator._unsub_state_change = []

        await coordinator.async_shutdown()

        mock_task.cancel.assert_called_once()
        assert coordinator._tilt_tasks == {}


class TestTiltHandling:
    """Tests for tilt/slat control in coordinator."""

    @pytest.mark.asyncio
    async def test_apply_positions_sends_tilt(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test tilt command is sent after position when tilt changes."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 30,
                    "target_tilt_position": 50,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 80, "supported_features": 143}
        )
        mock_hass.async_create_task = MagicMock()

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            await coordinator.async_apply_positions()

        # Position command was sent via async_call
        mock_hass.services.async_call.assert_called_once()
        # Tilt command was sent via async_create_task
        mock_hass.async_create_task.assert_called()
        assert coordinator._last_tilt_positions["cover.test"] == 50

    @pytest.mark.asyncio
    async def test_apply_positions_no_tilt_when_not_supported(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test tilt command is not sent when cover doesn't support tilt."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 30,
                    "target_tilt_position": 50,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
            "supports_tilt": False,
            "inverted_tilt": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 80, "supported_features": 15}
        )

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000
            await coordinator.async_apply_positions()

        # Tilt should NOT have been tracked
        assert "cover.test" not in coordinator._last_tilt_positions

    @pytest.mark.asyncio
    async def test_apply_positions_inverted_tilt(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test inverted tilt: 100 - target_tilt applied."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 30,
                    "target_tilt_position": 20,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": True,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 80, "supported_features": 143}
        )
        mock_hass.async_create_task = MagicMock()

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000
            await coordinator.async_apply_positions()

        # 100 - 20 = 80
        assert coordinator._last_tilt_positions["cover.test"] == 80

    def test_lock_cover_sends_tilt(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _lock_cover sends tilt when configured."""
        mock_storage.get_cover_raw.return_value = {
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._lock_cover("cover.test", 100, lock_tilt=0)

        assert coordinator._last_tilt_positions["cover.test"] == 0
        # Two async_create_task calls: position + tilt
        assert mock_hass.async_create_task.call_count == 2

    def test_lock_cover_no_tilt_when_none(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _lock_cover skips tilt when lock_tilt is None."""
        mock_storage.get_cover_raw.return_value = {
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._lock_cover("cover.test", 100, lock_tilt=None)

        assert "cover.test" not in coordinator._last_tilt_positions
        # Only one async_create_task call: position only
        assert mock_hass.async_create_task.call_count == 1

    def test_lock_cover_inverted_tilt(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test _lock_cover applies tilt inversion."""
        mock_storage.get_cover_raw.return_value = {
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": True,
        }
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._lock_cover("cover.test", 100, lock_tilt=30)

        # 100 - 30 = 70
        assert coordinator._last_tilt_positions["cover.test"] == 70

    def test_supports_tilt_check(self, coordinator, mock_hass) -> None:
        """Test _supports_tilt helper checks feature flag."""
        # With tilt support (bit 7 = 128)
        mock_hass.states.get.return_value = MockState(
            "open", {"supported_features": 143}
        )
        assert coordinator._supports_tilt("cover.test") is True

        # Without tilt support
        mock_hass.states.get.return_value = MockState(
            "open", {"supported_features": 15}
        )
        assert coordinator._supports_tilt("cover.test") is False

        # No state
        mock_hass.states.get.return_value = None
        assert coordinator._supports_tilt("cover.test") is False

    def test_manual_override_tilt_mismatch(
        self, coordinator, mock_storage
    ) -> None:
        """Test tilt mismatch triggers manual override detection."""
        from custom_components.cover_automatic.models import CoverConfig

        cover = MagicMock(spec=CoverConfig)
        cover.entity_id = "cover.test"
        cover.auto_enabled = True
        cover.pause_duration = 30

        mock_storage.covers = {"cover.test": cover}
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        coordinator._last_positions["cover.test"] = 50
        coordinator._last_tilt_positions["cover.test"] = 80
        coordinator._last_command_time["cover.test"] = 0.0

        # Position matches but tilt changed significantly
        new_state = MockState("open", {"current_position": 50, "current_tilt_position": 20})

        with patch.object(coordinator, "pause_cover") as mock_pause:
            with patch(
                "custom_components.cover_automatic.coordinator.time_mod"
            ) as mock_time:
                mock_time.monotonic.return_value = 9999.0
                coordinator._handle_cover_state_change("cover.test", None, new_state)
            mock_pause.assert_called_once_with(cover)

    @pytest.mark.asyncio
    async def test_send_tilt_delayed(self, coordinator, mock_hass) -> None:
        """Test _send_tilt_delayed sends tilt command."""
        await coordinator._send_tilt_delayed("cover.test", 50, 0)

        mock_hass.services.async_call.assert_called_once_with(
            "cover",
            "set_cover_tilt_position",
            {"entity_id": "cover.test", "tilt_position": 50},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_send_tilt_delayed_updates_command_time(
        self, coordinator, mock_hass
    ) -> None:
        """Test _send_tilt_delayed updates _last_command_time after sending."""
        coordinator._last_command_time["cover.test"] = 0.0

        await coordinator._send_tilt_delayed("cover.test", 50, 0)

        assert coordinator._last_command_time["cover.test"] > 0.0

    @pytest.mark.asyncio
    async def test_tilt_only_update_no_position_change(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test tilt-only update when position is already at target."""
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 50,
                    "target_tilt_position": 70,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50, "supported_features": 143}
        )
        mock_hass.async_create_task = MagicMock()

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000

            await coordinator.async_apply_positions()

        # Position service should NOT be called (already at target)
        mock_hass.services.async_call.assert_not_called()
        # Tilt task should have been scheduled (via async_create_task)
        mock_hass.async_create_task.assert_called()
        assert coordinator._last_tilt_positions["cover.test"] == 70
        # Command time should be updated for tilt-only
        assert coordinator._last_command_time["cover.test"] > 0

    @pytest.mark.asyncio
    async def test_tilt_unchanged_not_resent(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test tilt is not resent when it already matches the target."""
        coordinator._last_tilt_positions["cover.test"] = 70
        coordinator.data = {
            "covers": {
                "cover.test": {
                    "status": "auto",
                    "target_position": 50,
                    "target_tilt_position": 70,
                }
            }
        }
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5,
            "min_time_between_changes": 0,
            "last_position_change": None,
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 50, "supported_features": 143}
        )
        mock_hass.async_create_task = MagicMock()

        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value.timestamp.return_value = 1000
            await coordinator.async_apply_positions()

        # Neither position nor tilt should be sent
        mock_hass.services.async_call.assert_not_called()
        mock_hass.async_create_task.assert_not_called()

    def test_schedule_tilt_cancels_pending(
        self, coordinator, mock_hass
    ) -> None:
        """Test _schedule_tilt cancels any pending tilt task for the same cover."""
        old_task = MagicMock(spec=asyncio.Task)
        old_task.done.return_value = False
        coordinator._tilt_tasks["cover.test"] = old_task
        mock_hass.async_create_task = MagicMock()

        coordinator._schedule_tilt("cover.test", 50, 1.5)

        old_task.cancel.assert_called_once()
        assert coordinator._tilt_tasks["cover.test"] is not old_task

    def test_schedule_tilt_skips_cancel_for_done_task(
        self, coordinator, mock_hass
    ) -> None:
        """Test _schedule_tilt does not cancel already-done tasks."""
        old_task = MagicMock(spec=asyncio.Task)
        old_task.done.return_value = True
        coordinator._tilt_tasks["cover.test"] = old_task
        mock_hass.async_create_task = MagicMock()

        coordinator._schedule_tilt("cover.test", 50, 1.5)

        old_task.cancel.assert_not_called()


class TestUpdateLastPositionFromState:
    """Tests for _update_last_position_from_state error handling."""

    def test_update_position_from_state_normal(
        self, coordinator, mock_hass
    ) -> None:
        """Test normal position update from HA state."""
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 75, "current_tilt_position": 40}
        )

        coordinator._update_last_position_from_state("cover.test")

        assert coordinator._last_positions["cover.test"] == 75
        assert coordinator._last_tilt_positions["cover.test"] == 40

    def test_update_position_invalid_value_resets_to_none(
        self, coordinator, mock_hass
    ) -> None:
        """Test invalid position attribute resets tracked position to None."""
        coordinator._last_positions["cover.test"] = 50
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": "unavailable"}
        )

        coordinator._update_last_position_from_state("cover.test")

        # Reset to None to prevent false manual override detection
        assert coordinator._last_positions["cover.test"] is None

    def test_update_position_none_value_resets_to_none(
        self, coordinator, mock_hass
    ) -> None:
        """Test None position attribute resets tracked position to None."""
        coordinator._last_positions["cover.test"] = 50
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": None}
        )

        coordinator._update_last_position_from_state("cover.test")

        # int(None) raises TypeError, reset to None
        assert coordinator._last_positions["cover.test"] is None

    def test_update_tilt_invalid_value_resets_to_none(
        self, coordinator, mock_hass
    ) -> None:
        """Test invalid tilt attribute resets to None."""
        coordinator._last_tilt_positions["cover.test"] = 60
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 75, "current_tilt_position": "abc"}
        )

        coordinator._update_last_position_from_state("cover.test")

        assert coordinator._last_positions["cover.test"] == 75
        assert coordinator._last_tilt_positions["cover.test"] is None

    def test_update_tilt_none_not_tracked(
        self, coordinator, mock_hass
    ) -> None:
        """Test None tilt attribute does not update tracking."""
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 75}  # No current_tilt_position
        )

        coordinator._update_last_position_from_state("cover.test")

        assert coordinator._last_positions["cover.test"] == 75
        assert "cover.test" not in coordinator._last_tilt_positions

    def test_update_no_state_noop(
        self, coordinator, mock_hass
    ) -> None:
        """Test no HA state does nothing."""
        mock_hass.states.get.return_value = None

        coordinator._update_last_position_from_state("cover.test")

        assert "cover.test" not in coordinator._last_positions
        assert "cover.test" not in coordinator._last_tilt_positions


class TestVentSensorWithTilt:
    """Tests for vent sensor handling with tilt position."""

    def test_vent_sensor_open_sets_venting_and_moves_if_below(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test vent sensor sets VENTING and moves cover up if below vent_position."""
        cover_raw = {
            "lock_sensor": None,
            "vent_sensor": "binary_sensor.vent",
            "vent_position": 30,
            "inverted": False,
        }
        mock_storage.get_cover_raw.return_value = cover_raw
        # Current position 10 < vent_position 30
        mock_hass.states.get.return_value = MockState("on", {"current_position": 10})
        mock_hass.async_create_task = MagicMock()

        coordinator._cover_states["cover.test"] = CoverStatus.AUTO

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._handle_contact_sensor_change(
                "binary_sensor.vent",
                [],
                ["cover.test"],
                MockState("off"),
                MockState("on"),
            )

        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        assert mock_hass.async_create_task.call_count == 1

    def test_vent_sensor_open_no_move_if_above(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test vent sensor sets VENTING but does not move if already above vent_position."""
        cover_raw = {
            "lock_sensor": None,
            "vent_sensor": "binary_sensor.vent",
            "vent_position": 30,
            "inverted": False,
        }
        mock_storage.get_cover_raw.return_value = cover_raw
        # Current position 100 > vent_position 30
        mock_hass.states.get.return_value = MockState("on", {"current_position": 100})
        mock_hass.async_create_task = MagicMock()

        coordinator._cover_states["cover.test"] = CoverStatus.AUTO

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._handle_contact_sensor_change(
                "binary_sensor.vent",
                [],
                ["cover.test"],
                MockState("off"),
                MockState("on"),
            )

        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        # No move command
        assert mock_hass.async_create_task.call_count == 0

    def test_lock_to_vent_transition_sets_venting(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test lock->vent transition switches to VENTING status."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        cover_raw = {
            "lock_position": 100,
            "lock_tilt_position": 0,
            "vent_position": 30,
            "vent_sensor": "binary_sensor.vent",
            "vent_tilt_position": 50,
            "inverted": False,
            "supports_tilt": True,
            "inverted_tilt": False,
        }
        mock_storage.get_cover_raw.return_value = cover_raw
        mock_hass.states.get.return_value = MockState("on")  # Vent still open
        mock_hass.async_create_task = MagicMock()

        coordinator._handle_contact_sensor_change(
            "binary_sensor.window",
            ["cover.test"],
            [],
            MockState("on"),
            MockState("off"),  # Lock sensor closes
        )
        # Lock closed but vent still open -> switches to VENTING
        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        # Must update UI
        coordinator.async_set_updated_data.assert_called()

    def test_lock_to_vent_moves_cover_if_below_vent_position(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test lock->vent transition moves cover to vent_position if below it."""
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        coordinator._pre_lock_states["cover.test"] = CoverStatus.AUTO
        cover_raw = {
            "lock_position": 100,
            "vent_position": 30,
            "vent_sensor": "binary_sensor.vent",
            "inverted": False,
        }
        mock_storage.get_cover_raw.return_value = cover_raw
        # Vent sensor open, cover at position 10 (below vent_position 30)
        mock_hass.states.get.side_effect = lambda eid: {
            "binary_sensor.vent": MockState("on"),
            "cover.test": MockState("open", {"current_position": 10}),
        }.get(eid)
        mock_hass.async_create_task = MagicMock()

        with patch("custom_components.cover_automatic.coordinator.time_mod"):
            coordinator._handle_contact_sensor_change(
                "binary_sensor.window",
                ["cover.test"],
                [],
                MockState("on"),
                MockState("off"),
            )

        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING
        assert coordinator._last_positions["cover.test"] == 30
        # Must issue move command
        mock_hass.services.async_call.assert_called_with(
            "cover", "set_cover_position",
            {"entity_id": "cover.test", "position": 30},
            blocking=False,
        )
        # Must clean up pre_lock_states
        assert "cover.test" not in coordinator._pre_lock_states


class TestWindProtection:
    """Tests for wind protection feature."""

    def _setup_wind(self, coordinator, mock_storage, mock_hass, wind_speed="55"):
        """Helper to set up wind protection test scenario."""
        mock_storage.wind_sensor = "sensor.wind_speed"
        mock_storage.wind_speed_threshold = 50.0
        mock_storage.wind_speed_hysteresis = 10.0
        mock_storage._data["covers"] = {
            "cover.test": {
                "entity_id": "cover.test",
                "name": "Test",
                "auto_enabled": True,
                "inverted": False,
                "lock_sensor": None,
                "vent_sensor": None,
            }
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        mock_hass.states.get.return_value = MockState(wind_speed, {"current_position": 50})

    def test_wind_activates_above_threshold(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection activates when speed >= threshold."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        assert coordinator._cover_states["cover.test"] == CoverStatus.WIND_PROTECTED

    def test_wind_does_not_activate_below_threshold(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection does not activate below threshold."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "40")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is False
        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO

    def test_wind_activates_at_exact_threshold(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection activates at exactly the threshold."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "50")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True

    def test_wind_deactivates_below_hysteresis(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection deactivates at threshold - hysteresis."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        # Wind drops to 40 (= 50 - 10), should deactivate
        mock_hass.states.get.return_value = MockState("40", {"current_position": 100})
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is False
        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO

    def test_wind_stays_active_in_hysteresis_band(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection stays active within hysteresis band."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        # Wind drops to 45 (still above 50-10=40), should stay protected
        mock_hass.states.get.return_value = MockState("45", {"current_position": 100})
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True

    def test_wind_moves_cover_to_100(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection moves covers to fully open (100)."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        mock_hass.async_create_task.assert_called()
        assert coordinator._last_positions["cover.test"] == 100

    def test_wind_overrides_locked(self, coordinator, mock_storage, mock_hass) -> None:
        """Test wind protection overrides LOCKED status (highest priority)."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        assert coordinator._cover_states["cover.test"] == CoverStatus.WIND_PROTECTED

    def test_wind_no_sensor_configured(self, coordinator, mock_storage, mock_hass) -> None:
        """Test no action when wind sensor not configured."""
        mock_storage.wind_sensor = None
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is False

    def test_wind_sensor_unavailable_keeps_state(self, coordinator, mock_storage, mock_hass) -> None:
        """Test unavailable sensor preserves current protection state."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        # Sensor becomes unavailable
        mock_hass.states.get.return_value = MockState("unavailable")
        coordinator._check_wind_protection()
        # Should keep protection active
        assert coordinator._wind_protected is True

    def test_wind_threshold_zero_no_activation(self, coordinator, mock_storage, mock_hass) -> None:
        """Test threshold=0 does not activate (opt-in guard)."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "5")
        mock_storage.wind_speed_threshold = 0.0
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is False

    def test_wind_inverted_cover_position(self, coordinator, mock_storage, mock_hass) -> None:
        """Test inverted cover gets position 0 (= fully open for inverted)."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        mock_storage._data["covers"]["cover.test"]["inverted"] = True
        coordinator._check_wind_protection()
        assert coordinator._last_positions["cover.test"] == 0

    def test_wind_blocks_manual_override(self, coordinator, mock_storage, mock_hass) -> None:
        """Test manual overrides are ignored during wind protection."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        assert coordinator._wind_protected is True
        # Simulate cover state change (manual override attempt)
        new_state = MockState("open", {"current_position": 50})
        coordinator._handle_cover_state_change("cover.test", None, new_state)
        # Should still be WIND_PROTECTED
        assert coordinator._cover_states["cover.test"] == CoverStatus.WIND_PROTECTED

    def test_wind_blocks_resume(self, coordinator, mock_storage, mock_hass) -> None:
        """Test resume_cover is blocked during wind protection."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        coordinator._check_wind_protection()
        coordinator.resume_cover("cover.test")
        # Should still be WIND_PROTECTED
        assert coordinator._cover_states["cover.test"] == CoverStatus.WIND_PROTECTED

    def test_wind_sync_cover_statuses_skips_lock_vent(self, coordinator, mock_storage, mock_hass) -> None:
        """Test _sync_cover_statuses skips lock/vent checks during wind protection."""
        self._setup_wind(coordinator, mock_storage, mock_hass, "55")
        mock_storage._data["covers"]["cover.test"]["lock_sensor"] = "binary_sensor.window"
        mock_storage.enabled = True
        mock_storage.covers = {}
        coordinator._sync_cover_statuses()
        # Wind should override, even with lock sensor
        assert coordinator._cover_states["cover.test"] == CoverStatus.WIND_PROTECTED
