"""Integration tests for CoverAutomatic coordinator flows."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.coordinator import CoverAutomaticCoordinator
from custom_components.cover_automatic.models import (
    Condition,
    ConditionType,
    CoverConfig,
    CoverStatus,
    Facade,
    Rule,
    Scenario,
)
from custom_components.cover_automatic.storage import CoverAutomaticStorage


class MockState:
    """Mock Home Assistant state object."""

    def __init__(self, state: str, attributes: dict | None = None) -> None:
        """Initialize mock state."""
        self.state = state
        self.attributes = attributes or {}


def _consume_coroutine(coro):
    """Consume coroutine without running it (avoids event loop requirement)."""
    coro.close()
    return None


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    # Consume coroutines without requiring event loop
    hass.async_create_task = MagicMock(side_effect=_consume_coroutine)
    return hass


@pytest.fixture
def mock_storage():
    """Create mock storage with realistic data."""
    storage = MagicMock(spec=CoverAutomaticStorage)

    # Default data structure
    storage._data = {
        "covers": {},
        "facades": {},
        "rules": {},
        "scenarios": {},
    }

    storage.facades = {}
    storage.covers = {}
    storage.rules = {}
    storage.scenarios = {"everyday": Scenario(id="everyday", name="Everyday")}
    storage.active_scenario = "everyday"
    storage.outdoor_temp_sensor = "sensor.outdoor_temp"
    storage.indoor_temp_sensor = "sensor.indoor_temp"
    storage.weather_entity = "weather.home"
    storage.comfort_temp_min = 21.0
    storage.comfort_temp_max = 25.0
    storage.comfort_hysteresis = 1.0
    storage.wind_sensor = None
    storage.wind_speed_threshold = 0.0
    storage.wind_speed_hysteresis = 0.0
    storage.logbook_enabled = True

    storage.async_load = AsyncMock()
    storage.async_save = AsyncMock()
    storage.async_add_scenario = AsyncMock()
    storage.update_cover_status = MagicMock()
    storage.update_cover_last_change = MagicMock()
    storage.get_cover_raw = MagicMock(return_value=None)

    return storage


@pytest.fixture
def coordinator(mock_hass, mock_storage):
    """Create coordinator instance with mocked dependencies."""
    with patch.object(CoverAutomaticCoordinator, "__init__", lambda self, *args, **kwargs: None):
        coord = CoverAutomaticCoordinator.__new__(CoverAutomaticCoordinator)
        coord.hass = mock_hass
        coord.storage = mock_storage
        coord._tracked_entities = set()
        coord._unsub_state_change = []
        coord._cover_states = {}
        coord._last_positions = {}
        coord._last_tilt_positions = {}
        coord._tilt_tasks = {}
        coord._last_command_time = {}
        coord._pending_settle = set()
        coord._pre_lock_states = {}
        coord._wind_protected = False
        coord._hysteresis_info = {}
        coord._last_matching_rules = {}
        coord._last_move_rule = {}
        coord._post_protective_exit = set()
        coord._lock_to_restore = set()
        coord._startup_time = -999.0
        coord._startup_skip = False
        coord._grace_synced = True
        coord.log_storage = None
        coord.data = {}
        coord.logger = MagicMock()

        # Mock parent class methods
        coord.async_set_updated_data = MagicMock()
        coord.async_request_refresh = AsyncMock()

        # Create real engine
        from custom_components.cover_automatic.engine import RuleEngine
        coord.engine = RuleEngine(mock_hass, mock_storage)

        return coord


class TestStartupSkipIntegration:
    """Test that first refresh after startup skips position application."""

    @staticmethod
    def _setup(coordinator, mock_hass, mock_storage):
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            facade_id="south",
            min_position_change=1,
            min_time_between_changes=0,
        )
        facade = Facade(id="south", name="South", azimuth_start=135.0, azimuth_end=225.0, direction="south")
        rule = Rule(
            id="r1", name="Sun", enabled=True, priority=10,
            conditions=[Condition(type=ConditionType.TEMPERATURE_ABOVE, params={"sensor": "sensor.temp", "value": 10})],
            target_position=50,
        )
        mock_storage.facades = {"south": facade}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"r1": rule}
        cover_raw = {
            "entity_id": "cover.test", "auto_enabled": True,
            "min_position_change": 1, "min_time_between_changes": 0,
            "last_position_change": None, "inverted": False,
        }
        mock_storage._data = {"covers": {"cover.test": cover_raw}, "facades": {}, "rules": {}, "scenarios": {}}
        mock_storage.get_cover_raw.return_value = cover_raw
        mock_hass.states.get.side_effect = lambda eid: {
            "sensor.temp": MockState("25.0"),
            "cover.test": MockState("open", {"current_position": 100}),
            "sun.sun": MockState("above_horizon", {"azimuth": 180, "elevation": 45}),
        }.get(eid)
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO

    @pytest.mark.asyncio
    async def test_first_refresh_skips_position_apply(self, coordinator, mock_hass, mock_storage) -> None:
        """First refresh during grace period should evaluate rules but not move covers."""
        self._setup(coordinator, mock_hass, mock_storage)
        coordinator._startup_skip = True

        with patch(
            "custom_components.cover_automatic.coordinator.time_mod"
        ) as mock_time:
            # 10s after startup -> within grace period
            mock_time.monotonic.return_value = coordinator._startup_time + 10
            result = await coordinator._async_update_data()

        assert result["covers"]["cover.test"]["target_position"] == 50
        mock_hass.services.async_call.assert_not_called()
        assert coordinator._startup_skip is False

    @pytest.mark.asyncio
    async def test_grace_period_still_skips(self, coordinator, mock_hass, mock_storage) -> None:
        """Refresh within grace period (but after first) still skips."""
        self._setup(coordinator, mock_hass, mock_storage)
        coordinator._startup_skip = False

        with patch(
            "custom_components.cover_automatic.coordinator.time_mod"
        ) as mock_time:
            # 90s after startup -> still within 120s grace period
            mock_time.monotonic.return_value = coordinator._startup_time + 90
            await coordinator._async_update_data()

        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_after_grace_period_applies_positions(self, coordinator, mock_hass, mock_storage) -> None:
        """Refresh after grace period should apply positions normally."""
        self._setup(coordinator, mock_hass, mock_storage)
        coordinator._startup_skip = False

        with patch(
            "custom_components.cover_automatic.coordinator.time_mod"
        ) as mock_time:
            mock_time.monotonic.return_value = coordinator._startup_time + 200
            with patch("homeassistant.util.dt.now") as mock_now:
                mock_now.return_value.timestamp.return_value = 1000
                await coordinator._async_update_data()

        mock_hass.services.async_call.assert_called()


class TestHappyPathIntegration:
    """Integration tests for the happy path: rule matches -> cover moves."""

    @pytest.mark.asyncio
    async def test_rule_matches_and_cover_moves(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test complete flow: rule evaluation -> position calculation -> service call."""
        # Setup: facade, cover, and rule
        facade = Facade(
            id="south",
            name="South",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        cover = CoverConfig(
            entity_id="cover.living_room",
            name="Living Room",
            facade_id="south",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=0,  # Disable time hysteresis for test
        )
        rule = Rule(
            id="sun_shade",
            name="Sun Shade",
            enabled=True,
            priority=10,
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.outdoor_temp", "value": 20},
                ),
            ],
            target_position=30,
        )

        # Configure storage
        mock_storage.facades = {"south": facade}
        mock_storage.covers = {"cover.living_room": cover}
        mock_storage.rules = {"sun_shade": rule}
        mock_storage._data = {
            "covers": {
                "cover.living_room": {
                    "entity_id": "cover.living_room",
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.living_room"]

        # Mock states
        mock_hass.states.get.side_effect = lambda entity_id: {
            "sensor.outdoor_temp": MockState("25.0"),
            "cover.living_room": MockState("open", {"current_position": 100}),
            "sun.sun": MockState("above_horizon", {"azimuth": 180, "elevation": 45}),
        }.get(entity_id)

        # Execute the update cycle
        result = await coordinator._async_update_data()

        # Verify rule was evaluated and position calculated
        assert result["covers"]["cover.living_room"]["status"] == "auto"
        assert result["covers"]["cover.living_room"]["target_position"] == 30

        # Verify service was called to move the cover
        mock_hass.services.async_call.assert_called_once_with(
            "cover",
            "set_cover_position",
            {"entity_id": "cover.living_room", "position": 30},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_no_matching_rule_no_movement(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that cover doesn't move when no rules match."""
        cover = CoverConfig(
            entity_id="cover.bedroom",
            name="Bedroom",
            auto_enabled=True,
        )
        rule = Rule(
            id="temp_rule",
            name="Temp Rule",
            enabled=True,
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.outdoor_temp", "value": 30},
                ),
            ],
            target_position=0,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.bedroom": cover}
        mock_storage.rules = {"temp_rule": rule}
        mock_storage._data = {"covers": {}, "facades": {}, "rules": {}, "scenarios": {}}
        mock_storage.get_cover_raw.return_value = None

        # Temperature is 25, rule requires > 30
        mock_hass.states.get.return_value = MockState("25.0")

        result = await coordinator._async_update_data()

        # No target position calculated
        assert result["covers"]["cover.bedroom"]["target_position"] is None

        # No service call
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_rule_not_evaluated(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that disabled rules are not evaluated."""
        cover = CoverConfig(entity_id="cover.test", name="Test", auto_enabled=True)
        rule = Rule(
            id="disabled_rule",
            name="Disabled",
            enabled=False,  # Disabled
            conditions=[],
            target_position=50,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"disabled_rule": rule}
        mock_storage._data = {"covers": {}, "facades": {}, "rules": {}, "scenarios": {}}
        mock_storage.get_cover_raw.return_value = None

        result = await coordinator._async_update_data()

        assert result["covers"]["cover.test"]["target_position"] is None


class TestStateTransitionIntegration:
    """Integration tests for state transitions."""

    def test_manual_override_pauses_cover(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that manual position change pauses automation."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            pause_duration=120,
        )

        mock_storage.covers = {"cover.test": cover}
        coordinator._cover_states["cover.test"] = CoverStatus.AUTO
        coordinator._last_positions["cover.test"] = 30  # Expected position

        # Simulate manual change to different position
        old_state = MockState("open", {"current_position": 30})
        new_state = MockState("open", {"current_position": 80})  # Manual change

        with patch(
            "custom_components.cover_automatic.coordinator.time_mod"
        ) as mock_time:
            mock_time.monotonic.return_value = 9999.0  # Well past SETTLE_TIME
            coordinator._handle_cover_state_change("cover.test", old_state, new_state)

        # Cover should be paused
        assert coordinator._cover_states["cover.test"] == CoverStatus.PAUSED
        mock_storage.update_cover_status.assert_called()

    def test_pause_timeout_resumes_automation(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that paused cover resumes after timeout via _sync_cover_statuses."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "pause_until": 500.0,  # Pause ended
                    "lock_sensor": None,
                    "vent_sensor": None,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        coordinator._cover_states["cover.test"] = CoverStatus.PAUSED

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0  # After pause_until
            coordinator._sync_cover_statuses()
            status = coordinator.get_cover_status("cover.test")

        assert status == CoverStatus.AUTO

    def test_lock_sensor_locks_cover(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that opening lock sensor locks the cover."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "lock_sensor": "binary_sensor.window",
                    "lock_position": 100,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        coordinator._cover_states["cover.test"] = CoverStatus.AUTO

        # Simulate window opening
        old_state = MockState("off")
        new_state = MockState("on")  # Window opened

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._handle_contact_sensor_change(
                "binary_sensor.window",
                lock_covers=["cover.test"],
                vent_covers=[],
                old_state=old_state,
                new_state=new_state,
            )

        # Cover should be locked
        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED

    def test_lock_sensor_unlocks_cover(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that closing lock sensor unlocks the cover."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "lock_sensor": "binary_sensor.window",
                    "lock_position": 100,
                    "vent_sensor": None,
                    "inverted": False,
                    "pause_until": None,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        coordinator._cover_states["cover.test"] = CoverStatus.LOCKED
        coordinator._pre_lock_states["cover.test"] = CoverStatus.AUTO
        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        # Simulate window closing
        old_state = MockState("on")
        new_state = MockState("off")  # Window closed

        coordinator._handle_contact_sensor_change(
            "binary_sensor.window",
            lock_covers=["cover.test"],
            vent_covers=[],
            old_state=old_state,
            new_state=new_state,
        )

        # Cover should be unlocked (AUTO)
        assert coordinator._cover_states["cover.test"] == CoverStatus.AUTO

    def test_vent_sensor_moves_to_vent_position(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that opening vent sensor moves cover to vent position."""
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "vent_sensor": "binary_sensor.vent",
                    "vent_position": 30,
                    "lock_sensor": None,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        coordinator._cover_states["cover.test"] = CoverStatus.AUTO

        # Simulate vent opening
        old_state = MockState("off")
        new_state = MockState("on")

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._handle_contact_sensor_change(
                "binary_sensor.vent",
                lock_covers=[],
                vent_covers=["cover.test"],
                old_state=old_state,
                new_state=new_state,
            )

        # Cover should be in VENTING state (automation continues with min position)
        assert coordinator._cover_states["cover.test"] == CoverStatus.VENTING


class TestHysteresisIntegration:
    """Integration tests for hysteresis logic."""

    @pytest.mark.asyncio
    async def test_small_position_change_blocked(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that small position changes are blocked by hysteresis."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            min_position_change=10,  # Require at least 10% change
        )
        rule = Rule(
            id="test_rule",
            name="Test",
            enabled=True,
            conditions=[],
            target_position=55,  # Only 5% change from current 50
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"test_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "min_position_change": 10,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        # Current position is 50, target is 55 (5% change < 10% minimum)
        mock_hass.states.get.return_value = MockState("open", {"current_position": 50})

        await coordinator._async_update_data()

        # Service should NOT be called (change too small)
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_large_position_change_allowed(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that large position changes are allowed."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            min_position_change=10,
        )
        rule = Rule(
            id="test_rule",
            name="Test",
            enabled=True,
            conditions=[],
            cover_ids=["cover.test"],
            target_position=30,  # 70% change from current 100
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"test_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "min_position_change": 10,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        await coordinator._async_update_data()

        # Service should be called (change is large enough)
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_hysteresis_blocks_rapid_changes(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that rapid position changes are blocked by time hysteresis."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=300,  # 5 minutes minimum
        )
        rule = Rule(
            id="test_rule",
            name="Test",
            enabled=True,
            conditions=[],
            target_position=30,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"test_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 300,
                    "last_position_change": 900.0,  # Changed 100s ago
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0  # Only 100s since last change
            await coordinator._async_update_data()

        # Service should NOT be called (too soon)
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_hysteresis_allows_after_delay(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that position changes are allowed after sufficient delay."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=300,
        )
        rule = Rule(
            id="test_rule",
            name="Test",
            enabled=True,
            conditions=[],
            cover_ids=["cover.test"],
            target_position=30,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"test_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 300,
                    "last_position_change": 500.0,  # Changed 500s ago
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0  # 500s since last change
            await coordinator._async_update_data()

        # Service should be called (enough time passed)
        mock_hass.services.async_call.assert_called_once()


class TestScenarioIntegration:
    """Integration tests for scenario-based rule activation."""

    @pytest.mark.asyncio
    async def test_rule_disabled_in_scenario_not_evaluated(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that rules disabled in active scenario are not evaluated."""
        cover = CoverConfig(entity_id="cover.test", name="Test", auto_enabled=True)
        rule = Rule(
            id="disabled_in_vacation",
            name="Disabled in Vacation",
            enabled=True,
            conditions=[],
            target_position=50,
        )
        scenario = Scenario(
            id="vacation",
            name="Vacation",
            rules_disabled=["disabled_in_vacation"],
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"disabled_in_vacation": rule}
        mock_storage.scenarios = {"vacation": scenario}
        mock_storage.active_scenario = "vacation"
        mock_storage._data = {"covers": {}, "facades": {}, "rules": {}, "scenarios": {}}
        mock_storage.get_cover_raw.return_value = None

        result = await coordinator._async_update_data()

        # Rule should not produce a target position
        assert result["covers"]["cover.test"]["target_position"] is None

    @pytest.mark.asyncio
    async def test_rule_active_in_scenario_evaluated(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that rules not disabled in scenario are evaluated."""
        cover = CoverConfig(entity_id="cover.test", name="Test", auto_enabled=True)
        rule = Rule(
            id="active_rule",
            name="Active Rule",
            enabled=True,
            conditions=[],
            cover_ids=["cover.test"],
            target_position=50,
        )
        scenario = Scenario(
            id="vacation",
            name="Vacation",
            rules_disabled=["other_rule"],  # Different rule disabled
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.test": cover}
        mock_storage.rules = {"active_rule": rule}
        mock_storage.scenarios = {"vacation": scenario}
        mock_storage.active_scenario = "vacation"
        mock_storage._data = {
            "covers": {
                "cover.test": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.test"]

        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        result = await coordinator._async_update_data()

        # Rule should produce target position
        assert result["covers"]["cover.test"]["target_position"] == 50


class TestTiltEndToEndIntegration:
    """Integration tests for tilt control end-to-end flow."""

    @pytest.mark.asyncio
    async def test_rule_with_tilt_applies_both(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test complete flow: rule with tilt -> evaluation -> position + tilt commands."""
        cover = CoverConfig(
            entity_id="cover.raffstore",
            name="Raffstore",
            facade_id="south",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=0,
        )
        rule = Rule(
            id="sun_tilt",
            name="Sun Tilt",
            enabled=True,
            priority=10,
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.outdoor_temp", "value": 20},
                ),
            ],
            target_position=30,
            target_tilt_position=50,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.raffstore": cover}
        mock_storage.rules = {"sun_tilt": rule}
        mock_storage._data = {
            "covers": {
                "cover.raffstore": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                    "supports_tilt": True,
                    "inverted_tilt": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.raffstore"]

        mock_hass.states.get.side_effect = lambda entity_id: {
            "sensor.outdoor_temp": MockState("25.0"),
            "cover.raffstore": MockState(
                "open", {"current_position": 100, "supported_features": 143}
            ),
        }.get(entity_id)

        result = await coordinator._async_update_data()

        # Verify rule evaluated with tilt
        assert result["covers"]["cover.raffstore"]["target_position"] == 30
        assert result["covers"]["cover.raffstore"]["target_tilt_position"] == 50

        # Verify position service was called
        mock_hass.services.async_call.assert_called_once_with(
            "cover",
            "set_cover_position",
            {"entity_id": "cover.raffstore", "position": 30},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_rule_without_tilt_no_tilt_sent(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test rule without tilt_position does not send tilt command."""
        cover = CoverConfig(
            entity_id="cover.basic",
            name="Basic",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=0,
        )
        rule = Rule(
            id="basic_rule",
            name="Basic Rule",
            enabled=True,
            conditions=[],
            cover_ids=["cover.basic"],
            target_position=40,
            # No target_tilt_position
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.basic": cover}
        mock_storage.rules = {"basic_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.basic": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                    "supports_tilt": True,
                    "inverted_tilt": False,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.basic"]

        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 100, "supported_features": 143}
        )

        result = await coordinator._async_update_data()

        assert result["covers"]["cover.basic"]["target_position"] == 40
        assert result["covers"]["cover.basic"]["target_tilt_position"] is None

        # Only position call, no tilt
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_tilt_inverted_end_to_end(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test inverted tilt end-to-end: 100 - target_tilt applied."""
        cover = CoverConfig(
            entity_id="cover.inv_tilt",
            name="Inverted Tilt",
            auto_enabled=True,
            min_position_change=5,
            min_time_between_changes=0,
        )
        rule = Rule(
            id="inv_tilt_rule",
            name="Inv Tilt",
            enabled=True,
            conditions=[],
            cover_ids=["cover.inv_tilt"],
            target_position=30,
            target_tilt_position=20,
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.inv_tilt": cover}
        mock_storage.rules = {"inv_tilt_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.inv_tilt": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": False,
                    "supports_tilt": True,
                    "inverted_tilt": True,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.inv_tilt"]

        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 100, "supported_features": 143}
        )

        await coordinator._async_update_data()

        # Tilt should be inverted: 100 - 20 = 80
        assert coordinator._last_tilt_positions.get("cover.inv_tilt") == 80


class TestInvertedCoverIntegration:
    """Integration tests for inverted covers."""

    @pytest.mark.asyncio
    async def test_inverted_cover_position_flipped(
        self, coordinator, mock_hass, mock_storage
    ) -> None:
        """Test that inverted cover positions are correctly flipped."""
        cover = CoverConfig(
            entity_id="cover.inverted",
            name="Inverted",
            auto_enabled=True,
            inverted=True,
        )
        rule = Rule(
            id="test_rule",
            name="Test",
            enabled=True,
            conditions=[],
            cover_ids=["cover.inverted"],
            target_position=30,  # Logical position
        )

        mock_storage.facades = {}
        mock_storage.covers = {"cover.inverted": cover}
        mock_storage.rules = {"test_rule": rule}
        mock_storage._data = {
            "covers": {
                "cover.inverted": {
                    "auto_enabled": True,
                    "min_position_change": 5,
                    "min_time_between_changes": 0,
                    "last_position_change": None,
                    "inverted": True,
                }
            },
            "facades": {},
            "rules": {},
            "scenarios": {},
        }
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.inverted"]

        mock_hass.states.get.return_value = MockState("open", {"current_position": 0})

        await coordinator._async_update_data()

        # Service should be called with flipped position (100 - 30 = 70)
        mock_hass.services.async_call.assert_called_once_with(
            "cover",
            "set_cover_position",
            {"entity_id": "cover.inverted", "position": 70},
            blocking=False,
        )


class TestSetupEntryVersionResolution:
    """Tests for how async_setup_entry resolves the integration version.

    Reading manifest.json from disk inside the event loop made Home Assistant
    log "Detected blocking call to read_text". The version now comes from the
    already-cached integration object, and this path had no coverage before.
    """

    @pytest.mark.asyncio
    async def test_version_comes_from_cached_manifest(self) -> None:
        """Setup pulls the version from async_get_integration, not from disk."""
        from custom_components.cover_automatic import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.http.async_register_static_paths = AsyncMock()

        entry = MagicMock()
        entry.data = {}
        entry.entry_id = "test_entry"
        entry.add_update_listener = MagicMock()

        integration = MagicMock()
        integration.manifest = {"version": "9.9.9"}

        mod = "custom_components.cover_automatic"
        with (
            patch(f"{mod}.async_get_integration", AsyncMock(return_value=integration)) as get_integration,
            patch(f"{mod}.CoverAutomaticStorage") as storage_cls,
            patch(f"{mod}.ActivityLogStorage") as log_cls,
            patch(f"{mod}.CoverAutomaticCoordinator") as coord_cls,
            patch(f"{mod}.async_setup_services", AsyncMock()),
            patch(f"{mod}.async_setup_api") as setup_api,
            patch(f"{mod}.async_register_built_in_panel") as register_panel,
            patch(f"{mod}.er.async_get", MagicMock()),
        ):
            storage_cls.return_value.async_load = AsyncMock()
            storage_cls.return_value.covers = {}
            log_cls.return_value.async_load = AsyncMock()
            coord_cls.return_value.async_setup = AsyncMock()
            coord_cls.return_value.async_config_entry_first_refresh = AsyncMock()
            coord_cls.return_value.async_add_listener = MagicMock()

            await async_setup_entry(hass, entry)

        get_integration.assert_awaited_once()
        assert get_integration.await_args.args[1] == "cover_automatic"

        # Version reaches the WebSocket API ...
        assert setup_api.call_args.kwargs["version"] == "9.9.9"
        # ... and the panel URL used for cache busting
        panel_kwargs = register_panel.call_args.kwargs
        assert "9.9.9" in str(panel_kwargs.get("config"))

    @pytest.mark.asyncio
    async def test_missing_version_falls_back(self) -> None:
        """A manifest without a version must not break setup."""
        from custom_components.cover_automatic import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.http.async_register_static_paths = AsyncMock()

        entry = MagicMock()
        entry.data = {}
        entry.entry_id = "test_entry"
        entry.add_update_listener = MagicMock()

        integration = MagicMock()
        integration.manifest = {}

        mod = "custom_components.cover_automatic"
        with (
            patch(f"{mod}.async_get_integration", AsyncMock(return_value=integration)),
            patch(f"{mod}.CoverAutomaticStorage") as storage_cls,
            patch(f"{mod}.ActivityLogStorage") as log_cls,
            patch(f"{mod}.CoverAutomaticCoordinator") as coord_cls,
            patch(f"{mod}.async_setup_services", AsyncMock()),
            patch(f"{mod}.async_setup_api") as setup_api,
            patch(f"{mod}.async_register_built_in_panel"),
            patch(f"{mod}.er.async_get", MagicMock()),
        ):
            storage_cls.return_value.async_load = AsyncMock()
            storage_cls.return_value.covers = {}
            log_cls.return_value.async_load = AsyncMock()
            coord_cls.return_value.async_setup = AsyncMock()
            coord_cls.return_value.async_config_entry_first_refresh = AsyncMock()
            coord_cls.return_value.async_add_listener = MagicMock()

            await async_setup_entry(hass, entry)

        assert setup_api.call_args.kwargs["version"] == "0"


class TestSetupEntryReload:
    """Reloading the config entry must not re-register the panel's static path.

    aiohttp routes cannot be removed, so registering /cover_automatic/panel.js
    in every async_setup_entry made the second setup (a reload) fail with
    "RuntimeError: Added route will never be executed" -- GitHub issue #3.
    The router here is a real aiohttp one driven by Home Assistant's own
    registration code, so a duplicate registration fails exactly as in HA.
    """

    PANEL_URL = "/cover_automatic/panel.js"

    @staticmethod
    def _make_hass(app):
        from types import SimpleNamespace

        from homeassistant.components.http.server import HomeAssistantHTTP

        server = SimpleNamespace(app=app)

        async def register_static_paths(configs):
            HomeAssistantHTTP._async_register_static_paths(
                server, configs, {c.url_path: None for c in configs}
            )

        hass = MagicMock()
        hass.data = {}
        hass.http.async_register_static_paths = register_static_paths
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.config_entries.async_entries = MagicMock(return_value=[])
        return hass

    @pytest.mark.asyncio
    async def test_reload_registers_panel_route_once(self) -> None:
        """Setup, unload and setup again succeeds with one panel route."""
        from aiohttp import web
        from homeassistant.helpers.http import KEY_ALLOW_CONFIGURED_CORS

        from custom_components.cover_automatic import (
            async_setup,
            async_setup_entry,
            async_unload_entry,
        )

        app = web.Application()
        app[KEY_ALLOW_CONFIGURED_CORS] = lambda _route: None
        hass = self._make_hass(app)

        entry = MagicMock()
        entry.data = {}
        entry.entry_id = "test_entry"
        entry.add_update_listener = MagicMock()

        integration = MagicMock()
        integration.manifest = {"version": "1.0.0"}

        mod = "custom_components.cover_automatic"
        with (
            patch(f"{mod}.async_get_integration", AsyncMock(return_value=integration)),
            patch(f"{mod}.CoverAutomaticStorage") as storage_cls,
            patch(f"{mod}.ActivityLogStorage") as log_cls,
            patch(f"{mod}.CoverAutomaticCoordinator") as coord_cls,
            patch(f"{mod}.async_setup_services", AsyncMock()),
            patch(f"{mod}.async_unload_services", AsyncMock()),
            patch(f"{mod}.async_setup_api"),
            patch(f"{mod}.async_register_built_in_panel"),
            patch(f"{mod}.async_remove_panel"),
            patch(f"{mod}.er.async_get", MagicMock()),
        ):
            storage_cls.return_value.async_load = AsyncMock()
            storage_cls.return_value.covers = {}
            log_cls.return_value.async_load = AsyncMock()
            coord_cls.return_value.async_setup = AsyncMock()
            coord_cls.return_value.async_config_entry_first_refresh = AsyncMock()
            coord_cls.return_value.async_add_listener = MagicMock()

            # Home Assistant runs async_setup once per runtime, entries on every (re)load
            assert await async_setup(hass, {})
            assert await async_setup_entry(hass, entry)
            assert await async_unload_entry(hass, entry)
            assert await async_setup_entry(hass, entry)

        panel_routes = [
            route
            for route in app.router.routes()
            if route.method == "GET" and route.resource.canonical == self.PANEL_URL
        ]
        assert len(panel_routes) == 1


@asynccontextmanager
async def _real_instance(tmp_path, cover_ids, facade_ids):
    """Real Home Assistant with real registries and the integration's entities.

    Sensor and switch entities come from the integration's own platform setup,
    added through real EntityPlatforms, so devices, registry entries and states
    match what a user sees in Home Assistant.
    """
    import logging
    from datetime import timedelta
    from types import SimpleNamespace

    from homeassistant import loader
    from homeassistant.config_entries import ConfigEntries, ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers.entity_platform import EntityPlatform

    from custom_components.cover_automatic import sensor, switch
    from custom_components.cover_automatic.const import DOMAIN

    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    hass.config_entries = ConfigEntries(hass, {})
    await hass.config_entries.async_initialize()
    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    await er.async_load(hass, load_empty=True)

    entry = ConfigEntry(
        domain=DOMAIN, data={}, options={}, title="CoverAutomatic", source="user",
        version=1, minor_version=1, unique_id=None, discovery_keys={},
        subentries_data=None,
    )
    hass.config_entries._entries[entry.entry_id] = entry

    storage = CoverAutomaticStorage(hass)
    await storage.async_load()
    for cover_id in cover_ids:
        await storage.async_add_cover(CoverConfig(entity_id=cover_id, name=cover_id))
    for facade_id in facade_ids:
        await storage.async_add_facade(
            Facade(id=facade_id, name=facade_id, azimuth_start=135.0, azimuth_end=225.0)
        )

    coordinator = CoverAutomaticCoordinator(hass, storage, 60, config_entry=entry)
    entry.runtime_data = SimpleNamespace(coordinator=coordinator, storage=storage)

    for domain, module in (("sensor", sensor), ("switch", switch)):
        platform = EntityPlatform(
            hass=hass, logger=logging.getLogger(__name__), domain=domain,
            platform_name=DOMAIN, platform=module,
            scan_interval=timedelta(seconds=60), entity_namespace=None,
        )
        assert await platform.async_setup_entry(entry)
    await hass.async_block_till_done()

    try:
        yield hass, entry, storage, coordinator
    finally:
        await hass.async_stop(force=True)


def _device_entities(hass, entry, identifier):
    """Return (device, entity ids) for a CoverAutomatic device identifier."""
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    from custom_components.cover_automatic.const import DOMAIN

    device = next(
        (
            d for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
            if (DOMAIN, identifier) in d.identifiers
        ),
        None,
    )
    if device is None:
        return None, []
    entities = er.async_entries_for_device(er.async_get(hass), device.id)
    return device, [e.entity_id for e in entities]


class TestDeleteRemovesDevice:
    """Deleting a cover or facade in the panel removes its device and entities.

    Both delete handlers only touched the storage, so the device and its
    entities stayed in Home Assistant (reported on PR #4).
    """

    @pytest.mark.asyncio
    async def test_cover_delete_removes_device_entities_and_states(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_delete

        async with _real_instance(tmp_path, ["cover.a", "cover.b"], []) as (
            hass, entry, storage, coordinator,
        ):
            _, entity_ids = _device_entities(hass, entry, "cover.a")
            assert len(entity_ids) == 2  # status sensor + automation switch

            msg = {"id": 1, "entity_id": "cover.a"}
            await ws_cover_delete(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            device, remaining = _device_entities(hass, entry, "cover.a")
            assert device is None
            assert remaining == []
            assert all(hass.states.get(e) is None for e in entity_ids)
            # Other covers and the integration device are untouched
            assert len(_device_entities(hass, entry, "cover.b")[1]) == 2
            assert len(_device_entities(hass, entry, entry.entry_id)[1]) == 1

    @pytest.mark.asyncio
    async def test_facade_delete_removes_device_and_entities(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_facade_delete

        async with _real_instance(tmp_path, ["cover.a"], ["south", "west"]) as (
            hass, entry, storage, coordinator,
        ):
            _, entity_ids = _device_entities(hass, entry, "facade_south")
            assert len(entity_ids) == 3  # sun on facade + entry/exit time

            msg = {"id": 1, "facade_id": "south"}
            await ws_facade_delete(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            device, remaining = _device_entities(hass, entry, "facade_south")
            assert device is None
            assert remaining == []
            assert all(hass.states.get(e) is None for e in entity_ids)
            assert len(_device_entities(hass, entry, "facade_west")[1]) == 3
            assert len(_device_entities(hass, entry, "cover.a")[1]) == 2


class TestRemoveConfigEntryDevice:
    """Orphaned devices from earlier versions can be deleted in Home Assistant."""

    @pytest.mark.asyncio
    async def test_only_orphaned_devices_are_removable(self, tmp_path) -> None:
        from custom_components.cover_automatic import async_remove_config_entry_device

        async with _real_instance(tmp_path, ["cover.a", "cover.gone"], ["south"]) as (
            hass, entry, storage, coordinator,
        ):
            # Pre-fix delete: storage only, device stays behind
            await storage.async_remove_cover("cover.gone")

            def removable(identifier: str) -> bool:
                device, _ = _device_entities(hass, entry, identifier)
                return async_remove_config_entry_device(hass, entry, device)

            assert await removable("cover.gone") is True
            assert await removable("cover.a") is False
            assert await removable("facade_south") is False
            assert await removable(entry.entry_id) is False


class TestEntitiesFollowStorage:
    """Covers and facades get their device and entities without a restart.

    The platforms created entities only in async_setup_entry, so anything
    added at runtime (panel or import) stayed without entities until Home
    Assistant restarted, and an import that dropped covers or facades left
    their devices behind.
    """

    @pytest.mark.asyncio
    async def test_cover_add_creates_device_and_entities(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_add

        async with _real_instance(tmp_path, ["cover.a"], []) as (
            hass, entry, storage, coordinator,
        ):
            msg = {"id": 1, "entity_ids": ["cover.new"]}
            await ws_cover_add(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            device, entity_ids = _device_entities(hass, entry, "cover.new")
            assert device is not None
            assert len(entity_ids) == 2
            assert all(hass.states.get(e) is not None for e in entity_ids)
            assert len(_device_entities(hass, entry, "cover.a")[1]) == 2

    @pytest.mark.asyncio
    async def test_facade_add_creates_device_and_entities(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_facade_add

        async with _real_instance(tmp_path, [], ["south"]) as (
            hass, entry, storage, coordinator,
        ):
            msg = {"id": 1, "name": "West", "direction": "west"}
            await ws_facade_add(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            device, entity_ids = _device_entities(hass, entry, "facade_west")
            assert device is not None
            assert len(entity_ids) == 3
            assert all(hass.states.get(e) is not None for e in entity_ids)
            assert len(_device_entities(hass, entry, "facade_south")[1]) == 3

    @pytest.mark.asyncio
    async def test_cover_readded_after_delete_gets_entities_again(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_add, ws_cover_delete

        async with _real_instance(tmp_path, ["cover.a"], []) as (
            hass, entry, storage, coordinator,
        ):
            await ws_cover_delete(hass, MagicMock(), {"id": 1, "entity_id": "cover.a"}, storage, coordinator)
            await hass.async_block_till_done()
            await ws_cover_add(hass, MagicMock(), {"id": 2, "entity_ids": ["cover.a"]}, storage, coordinator)
            await hass.async_block_till_done()

            _, entity_ids = _device_entities(hass, entry, "cover.a")
            assert len(entity_ids) == 2
            assert all(hass.states.get(e) is not None for e in entity_ids)

    @pytest.mark.asyncio
    async def test_import_adds_and_removes_devices(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_import_config

        async with _real_instance(tmp_path, ["cover.a", "cover.b"], ["south"]) as (
            hass, entry, storage, coordinator,
        ):
            data = {
                "covers": {
                    cid: CoverConfig(entity_id=cid, name=cid).to_dict()
                    for cid in ("cover.b", "cover.c")
                },
                "facades": {
                    "north": Facade(
                        id="north", name="North", azimuth_start=315.0, azimuth_end=45.0,
                    ).to_dict(),
                },
                "rules": {},
                "scenarios": {},
            }
            await ws_import_config(hass, MagicMock(), {"id": 1, "data": data}, storage, coordinator)
            await hass.async_block_till_done()

            assert _device_entities(hass, entry, "cover.a") == (None, [])
            assert _device_entities(hass, entry, "facade_south") == (None, [])
            assert len(_device_entities(hass, entry, "cover.b")[1]) == 2
            assert len(_device_entities(hass, entry, "cover.c")[1]) == 2
            assert len(_device_entities(hass, entry, "facade_north")[1]) == 3


class TestPanelAutoToggleUpdatesEntities:
    """Toggling automation in the panel updates the HA entities right away.

    ws_cover_update changed status and storage but notified no entity on
    disable and evaluated no rule on enable, so the automation switch and the
    status sensor lagged until the next coordinator cycle (up to 60 s).
    """

    async def _setup(self, hass, entry, storage, coordinator):
        """Add a global rule that matches, refresh, return (switch, sensor) ids."""
        hass.states.async_set("sensor.outdoor_temp", "25")
        await storage.async_add_rule(Rule(
            id="shade", name="Shade", enabled=True, priority=10,
            conditions=[Condition(
                type=ConditionType.TEMPERATURE_ABOVE,
                params={"sensor": "sensor.outdoor_temp", "value": 20},
            )],
            target_position=30,
        ))
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        _, entity_ids = _device_entities(hass, entry, "cover.a")
        switch_id = next(e for e in entity_ids if e.startswith("switch."))
        sensor_id = next(e for e in entity_ids if e.startswith("sensor."))
        return switch_id, sensor_id

    @pytest.mark.asyncio
    async def test_disable_updates_switch_and_status_sensor(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        async with _real_instance(tmp_path, ["cover.a"], []) as (
            hass, entry, storage, coordinator,
        ):
            switch_id, sensor_id = await self._setup(hass, entry, storage, coordinator)
            assert hass.states.get(switch_id).state == "on"
            assert hass.states.get(sensor_id).state == "auto"
            assert hass.states.get(sensor_id).attributes["rule_id"] == "shade"

            msg = {"id": 1, "entity_id": "cover.a", "auto_enabled": False}
            await ws_cover_update(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            assert hass.states.get(switch_id).state == "off"
            sensor = hass.states.get(sensor_id)
            assert sensor.state == "manual"
            assert sensor.attributes["rule_id"] is None

    @pytest.mark.asyncio
    async def test_enable_updates_switch_and_status_sensor(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        async with _real_instance(tmp_path, ["cover.a"], []) as (
            hass, entry, storage, coordinator,
        ):
            storage.get_cover_raw("cover.a")["auto_enabled"] = False
            storage._invalidate_cache()
            coordinator.set_cover_manual("cover.a")
            switch_id, sensor_id = await self._setup(hass, entry, storage, coordinator)
            assert hass.states.get(switch_id).state == "off"
            assert hass.states.get(sensor_id).state == "manual"

            msg = {"id": 1, "entity_id": "cover.a", "auto_enabled": True}
            await ws_cover_update(hass, MagicMock(), msg, storage, coordinator)
            await hass.async_block_till_done()

            assert hass.states.get(switch_id).state == "on"
            sensor = hass.states.get(sensor_id)
            assert sensor.state == "auto"
            assert sensor.attributes["rule_id"] == "shade"
            assert sensor.attributes["target_position"] == 30

    @pytest.mark.asyncio
    async def test_rapid_disable_updates_switch_during_refresh_cooldown(self, tmp_path) -> None:
        """Toggling again within the 10 s refresh cooldown still updates at once.

        set_cover_manual() notifies via async_set_updated_data, which also
        cancels the debouncer cooldown, so the requested refresh is not deferred.
        """
        from custom_components.cover_automatic.api import ws_cover_update

        async with _real_instance(tmp_path, ["cover.a"], []) as (
            hass, entry, storage, coordinator,
        ):
            switch_id, sensor_id = await self._setup(hass, entry, storage, coordinator)
            for msg_id, enabled in enumerate((False, True, False), start=1):
                msg = {"id": msg_id, "entity_id": "cover.a", "auto_enabled": enabled}
                await ws_cover_update(hass, MagicMock(), msg, storage, coordinator)
                await hass.async_block_till_done()

            assert hass.states.get(switch_id).state == "off"
            assert hass.states.get(sensor_id).state == "manual"


class _LockSensorScenario:
    """Real instance with a window-sensor cover; shared by the lock test classes."""

    WINDOW = "binary_sensor.window"
    TILT = "binary_sensor.tilt"
    WIND = "sensor.wind"
    CLOSE = {"entity_id": "cover.a", "position": 0}

    @pytest.fixture(autouse=True)
    def _instant_save(self, monkeypatch) -> None:
        """Skip the 2 s save debounce that async_block_till_done would wait for."""
        monkeypatch.setattr("custom_components.cover_automatic.storage.SAVE_DEBOUNCE_DELAY", 0)

    async def _setup(self, hass, storage, window_state: str = "on", *, wind: bool = False):
        """Cover at 100 % with a window sensor and a rule closing it to 0 %.

        Returns the list that records every set_cover_position call.
        """
        calls: list[dict] = []

        async def _record(call) -> None:
            calls.append(dict(call.data))

        hass.services.async_register("cover", "set_cover_position", _record)
        hass.states.async_set("cover.a", "open", {"current_position": 100})
        hass.states.async_set(self.WINDOW, window_state)
        hass.states.async_set("sensor.outdoor_temp", "25")
        storage.get_cover_raw("cover.a")["lock_sensor"] = self.WINDOW
        storage._invalidate_cache()
        if wind:
            hass.states.async_set(self.WIND, "0")
            storage.wind_sensor = self.WIND
            storage.wind_speed_threshold = 10.0
        await storage.async_add_rule(Rule(
            id="close", name="Close", enabled=True, priority=10, cover_ids=["cover.a"],
            conditions=[Condition(
                type=ConditionType.TEMPERATURE_ABOVE,
                params={"sensor": "sensor.outdoor_temp", "value": 20},
            )],
            target_position=0,
        ))
        return calls

    @staticmethod
    def _start(coordinator):
        """Past the startup grace period, listening to sensor changes."""
        coordinator._startup_time = -999.0
        coordinator._setup_state_tracking()
        return coordinator

    def _restart(self, hass, entry, storage):
        """A fresh coordinator on the stored state, as after an HA restart."""
        restarted = CoverAutomaticCoordinator(hass, storage, 60, config_entry=entry)
        restarted._restore_cover_states()
        return self._start(restarted)

    async def _cycle(self, hass, coordinator) -> None:
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    async def _set(self, hass, entity_id: str, state: str) -> None:
        hass.states.async_set(entity_id, state)
        await hass.async_block_till_done()


class TestUnreadableLockSensor(_LockSensorScenario):
    """An unreadable window sensor must not release a lock.

    The sync treated an unavailable, unknown or missing lock sensor as a
    closed window: a LOCKED cover was unlocked on the next cycle and the
    matching rule could lower it at a window that is still open (Zigbee
    bridge restart, empty battery, sensor not loaded yet after a restart).
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("unreadable", ["unavailable", "unknown"])
    async def test_unreadable_sensor_keeps_cover_locked(self, tmp_path, unreadable) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage)
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED

            await self._set(hass, self.WINDOW, unreadable)
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED
            assert calls == []

    @pytest.mark.asyncio
    async def test_missing_sensor_entity_keeps_cover_locked(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage)
            self._start(coordinator)
            await self._cycle(hass, coordinator)

            hass.states.async_remove(self.WINDOW)
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED
            assert calls == []

    @pytest.mark.asyncio
    async def test_lock_released_once_sensor_reports_closed(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage)
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            await self._set(hass, self.WINDOW, "unavailable")
            await self._cycle(hass, coordinator)
            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED
            assert calls == []

            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls == [self.CLOSE]

    @pytest.mark.asyncio
    async def test_lock_held_after_restart_while_sensor_unreadable(self, tmp_path) -> None:
        """A cover locked at shutdown stays locked until its sensor reports."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, entry, storage, _):
            calls = await self._setup(hass, storage, "unavailable")
            storage.update_cover_status("cover.a", CoverStatus.LOCKED.value, None)

            restarted = self._restart(hass, entry, storage)
            await self._cycle(hass, restarted)

            assert restarted.get_cover_status("cover.a") == CoverStatus.LOCKED
            assert calls == []

            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, restarted)

            assert restarted.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls == [self.CLOSE]

    @pytest.mark.asyncio
    async def test_restart_with_known_closed_sensor_does_not_lock(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, entry, storage, _):
            calls = await self._setup(hass, storage, "off")
            storage.update_cover_status("cover.a", CoverStatus.LOCKED.value, None)

            restarted = self._restart(hass, entry, storage)
            await self._cycle(hass, restarted)

            assert restarted.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls == [self.CLOSE]

    @pytest.mark.asyncio
    async def test_resume_releases_a_held_lock(self, tmp_path) -> None:
        """Resume stays the way out when the sensor never comes back."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, entry, storage, _):
            calls = await self._setup(hass, storage, "unavailable")
            storage.update_cover_status("cover.a", CoverStatus.LOCKED.value, None)
            restarted = self._restart(hass, entry, storage)
            await self._cycle(hass, restarted)
            assert restarted.get_cover_status("cover.a") == CoverStatus.LOCKED

            restarted.resume_cover("cover.a")
            await self._cycle(hass, restarted)

            assert restarted.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls == [self.CLOSE]

    @pytest.mark.asyncio
    async def test_resume_with_open_vent_sensor_releases_to_venting(self, tmp_path) -> None:
        """Resume refused a held lock while the tilt sensor was open."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage)
            hass.states.async_set(self.TILT, "on")
            storage.get_cover_raw("cover.a")["vent_sensor"] = self.TILT
            storage._invalidate_cache()
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            await self._set(hass, self.WINDOW, "unavailable")
            await self._cycle(hass, coordinator)
            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED

            coordinator.resume_cover("cover.a")
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.VENTING
            assert calls == [{"entity_id": "cover.a", "position": 30}]  # vent minimum

    @pytest.mark.asyncio
    async def test_held_lock_survives_wind_protection(self, tmp_path) -> None:
        """Wind ending must not turn a held lock into AUTO."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, wind=True)
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            await self._set(hass, self.WINDOW, "unavailable")
            await self._cycle(hass, coordinator)

            await self._set(hass, self.WIND, "20")
            await self._cycle(hass, coordinator)
            assert coordinator.get_cover_status("cover.a") == CoverStatus.WIND_PROTECTED
            await self._set(hass, self.WIND, "0")
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.LOCKED
            assert self.CLOSE not in calls

    @pytest.mark.asyncio
    async def test_restored_lock_dropped_when_sensor_reports_during_wind(self, tmp_path) -> None:
        """A readable sensor state ends the restored lock, even during wind."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, entry, storage, _):
            calls = await self._setup(hass, storage, "unavailable", wind=True)
            storage.update_cover_status("cover.a", CoverStatus.LOCKED.value, None)
            hass.states.async_set(self.WIND, "20")

            restarted = self._restart(hass, entry, storage)
            await self._cycle(hass, restarted)
            assert restarted.get_cover_status("cover.a") == CoverStatus.WIND_PROTECTED
            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, restarted)
            await self._set(hass, self.WINDOW, "unavailable")
            await self._set(hass, self.WIND, "0")
            await self._cycle(hass, restarted)

            assert restarted.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls[-1] == self.CLOSE

    @pytest.mark.asyncio
    async def test_unreadable_sensor_does_not_lock_an_unlocked_cover(self, tmp_path) -> None:
        """Without a lock to hold, an unreadable sensor changes nothing."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, "unavailable")
            self._start(coordinator)
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls == [self.CLOSE]


class TestLockAfterWindProtection(_LockSensorScenario):
    """A window still open when the storm ends must not keep the cover locked.

    Ending wind protection re-locked such a cover without remembering its
    previous status, so closing the window left it LOCKED until a resume,
    the automation switch or a restart.
    """

    @staticmethod
    def _shown(storage) -> str:
        """Persisted status, the one the panel shows."""
        return storage.get_cover_raw("cover.a")["status"]

    async def _storm(self, hass, storage, coordinator, calls, position_at_end: int = 100) -> None:
        """Window open before the storm and still open when the wind drops."""
        self._start(coordinator)
        await self._cycle(hass, coordinator)
        assert self._shown(storage) == CoverStatus.LOCKED.value
        await self._set(hass, self.WIND, "20")
        await self._cycle(hass, coordinator)
        assert self._shown(storage) == CoverStatus.WIND_PROTECTED.value

        hass.states.async_set("cover.a", "open", {"current_position": position_at_end})
        await self._set(hass, self.WIND, "0")
        await self._cycle(hass, coordinator)

        assert self._shown(storage) == CoverStatus.LOCKED.value
        assert self.CLOSE not in calls
        # The cover reaches the lock position before the window closes
        hass.states.async_set("cover.a", "open", {"current_position": 100})
        await hass.async_block_till_done()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("position_at_end", [100, 50])
    async def test_closing_the_window_releases_the_lock(self, tmp_path, position_at_end) -> None:
        """100 = already at the lock position, 50 = moved there again."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, wind=True)
            await self._storm(hass, storage, coordinator, calls, position_at_end)

            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, coordinator)

            assert self._shown(storage) == CoverStatus.AUTO.value
            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls[-1] == self.CLOSE

    @pytest.mark.asyncio
    async def test_disabled_cover_returns_to_manual_without_moving(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, wind=True)
            storage.get_cover_raw("cover.a")["auto_enabled"] = False
            storage._invalidate_cache()
            await self._storm(hass, storage, coordinator, calls)
            moves = len(calls)

            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, coordinator)

            assert self._shown(storage) == CoverStatus.MANUAL.value
            assert len(calls) == moves


class TestWindowOpenedDuringStorm(_LockSensorScenario):
    """A window opened during wind protection must not override it.

    The contact sensor handler set LOCKED or VENTING over WIND_PROTECTED and
    could send the lock or vent position to a cover still opening for the
    storm. The next sync then re-activated wind protection for every cover.
    """

    OPEN = {"entity_id": "cover.a", "position": 100}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("sensor", "after_storm"),
        [("lock", CoverStatus.LOCKED), ("vent", CoverStatus.VENTING)],
    )
    async def test_window_opened_during_storm(self, tmp_path, sensor, after_storm) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, "off", wind=True)
            hass.states.async_set(self.TILT, "off")
            storage.get_cover_raw("cover.a")["vent_sensor"] = self.TILT
            storage._invalidate_cache()
            hass.states.async_set("cover.a", "open", {"current_position": 20})  # still opening
            hass.states.async_set(self.WIND, "20")
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            assert calls == [self.OPEN]

            await self._set(hass, self.WINDOW if sensor == "lock" else self.TILT, "on")
            assert calls == [self.OPEN]
            assert storage.get_cover_raw("cover.a")["status"] == CoverStatus.WIND_PROTECTED.value
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.WIND_PROTECTED
            assert calls == [self.OPEN]

            await self._set(hass, self.WIND, "0")
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == after_storm


class TestWindowClosedDuringLockMove(_LockSensorScenario):
    """Closing the window while the cover still travels to the lock position.

    The unlock took the intermediate or stale position as the expected one.
    The arrival at the lock position then read as a manual override and the
    cover stayed open for the pause duration (door opened briefly).
    """

    OPEN = {"entity_id": "cover.a", "position": 100}

    @pytest.fixture
    def clock(self, monkeypatch) -> list[float]:
        """Controllable monotonic clock for the settle time checks."""
        from types import SimpleNamespace

        now = [1000.0]
        monkeypatch.setattr(
            "custom_components.cover_automatic.coordinator.time_mod",
            SimpleNamespace(monotonic=lambda: now[0]),
        )
        return now

    async def _report(self, hass, state: str, position: int) -> None:
        hass.states.async_set("cover.a", state, {"current_position": position})
        await hass.async_block_till_done()

    async def _lock_closed_cover(self, hass, storage, coordinator) -> list[dict]:
        """Closed cover in AUTO, then the window opens."""
        calls = await self._setup(hass, storage, "off")
        await self._report(hass, "closed", 0)
        self._start(coordinator)
        await self._cycle(hass, coordinator)
        assert calls == []
        await self._set(hass, self.WINDOW, "on")
        assert calls == [self.OPEN]
        return calls

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("moving", "unlock_at", "arrive_at"),
        [(30, 10, 25), (None, 10, 25), (80, 35, 45)],
        ids=["reports-motion", "silent-until-arrival", "slower-than-settle"],
    )
    async def test_cover_returns_to_rule_target(
        self, tmp_path, clock, moving, unlock_at, arrive_at
    ) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._lock_closed_cover(hass, storage, coordinator)
            start = clock[0]

            if moving is not None:
                clock[0] = start + unlock_at - 1
                await self._report(hass, "opening", moving)
            clock[0] = start + unlock_at
            await self._set(hass, self.WINDOW, "off")
            clock[0] = start + arrive_at
            await self._report(hass, "open", 100)
            clock[0] = start + arrive_at + 60
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls[-1] == self.CLOSE

    @pytest.mark.asyncio
    async def test_window_tilted_during_lock_move_keeps_venting(self, tmp_path, clock) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            hass.states.async_set(self.TILT, "off")
            storage.get_cover_raw("cover.a")["vent_sensor"] = self.TILT
            storage._invalidate_cache()
            calls = await self._lock_closed_cover(hass, storage, coordinator)
            start = clock[0]

            clock[0] = start + 9
            await self._report(hass, "opening", 50)
            await self._set(hass, self.TILT, "on")
            clock[0] = start + 10
            await self._set(hass, self.WINDOW, "off")
            clock[0] = start + 25
            await self._report(hass, "open", 100)
            clock[0] = start + 85
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.VENTING
            assert calls[-1] == {"entity_id": "cover.a", "position": 30}  # vent minimum

    @pytest.mark.asyncio
    async def test_window_closed_after_arrival_applies_rule_at_once(self, tmp_path, clock) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._lock_closed_cover(hass, storage, coordinator)
            clock[0] += 20
            await self._report(hass, "open", 100)
            clock[0] += 5

            await self._set(hass, self.WINDOW, "off")

            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls[-1] == self.CLOSE

    @pytest.mark.asyncio
    async def test_manual_move_during_long_lock_does_not_pause(self, tmp_path, clock) -> None:
        """Closing the window hands a cover moved by hand back to the rules."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._lock_closed_cover(hass, storage, coordinator)
            clock[0] += 20
            await self._report(hass, "open", 100)
            clock[0] += 600
            await self._report(hass, "open", 50)
            clock[0] += 10

            await self._set(hass, self.WINDOW, "off")
            await self._cycle(hass, coordinator)

            assert coordinator.get_cover_status("cover.a") == CoverStatus.AUTO
            assert calls[-1] == self.CLOSE


class TestWindowOpenedDuringStagger(_LockSensorScenario):
    """A window opened during the stagger pause between two cover commands.

    The apply cycle read the status before the pause and sent the stale rule
    target afterwards: a cover locked by the open window closed anyway, a
    tilted one went below the vent minimum.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("sensor", "status", "follow_up"),
        [
            ("lock", CoverStatus.LOCKED, []),
            ("vent", CoverStatus.VENTING, [{"entity_id": "cover.a", "position": 30}]),
            (None, CoverStatus.AUTO, [{"entity_id": "cover.a", "position": 0}]),
        ],
        ids=["window-opened", "window-tilted", "nothing-changed"],
    )
    async def test_window_opened_during_stagger_pause(
        self, tmp_path, sensor, status, follow_up
    ) -> None:
        async with _real_instance(tmp_path, ["cover.b", "cover.a"], []) as (hass, _, storage, coordinator):
            calls = await self._setup(hass, storage, "off")
            hass.states.async_set(self.TILT, "off")
            storage.get_cover_raw("cover.a")["vent_sensor"] = self.TILT
            storage._invalidate_cache()
            hass.states.async_set("cover.b", "open", {"current_position": 100})
            await storage.async_add_rule(Rule(
                id="close_b", name="Close B", enabled=True, priority=10, cover_ids=["cover.b"],
                conditions=[Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.outdoor_temp", "value": 20},
                )],
                target_position=0,
            ))
            storage.command_stagger = 0.1
            opened = {"lock": self.WINDOW, "vent": self.TILT}.get(sensor)

            async def _record(call) -> None:
                calls.append(dict(call.data))
                if call.data["entity_id"] == "cover.b" and opened:
                    # Handler runs eagerly inside async_call, so delay the window
                    # into the 0.1 s pause the apply cycle takes before cover.a.
                    hass.loop.call_later(0.05, hass.states.async_set, opened, "on")

            hass.services.async_register("cover", "set_cover_position", _record)
            self._start(coordinator)
            await self._cycle(hass, coordinator)
            assert coordinator.get_cover_status("cover.a") == status
            await self._cycle(hass, coordinator)

            assert calls == [{"entity_id": "cover.b", "position": 0}, *follow_up]


class TestDeleteKeepsRuleScope:
    """Deleting the last cover or facade of a rule must not make it global.

    Deleting only removed the reference. A rule left without any cover or
    facade counts as global and applied to every cover, so a bathroom-only
    rule suddenly moved the whole house.
    """

    @staticmethod
    def _rule(rule_id: str, cover_ids=(), facade_ids=()) -> Rule:
        return Rule(
            id=rule_id, name=rule_id, enabled=True, priority=10,
            cover_ids=list(cover_ids), facade_ids=list(facade_ids),
            conditions=[Condition(
                type=ConditionType.TEMPERATURE_ABOVE,
                params={"sensor": "sensor.outdoor_temp", "value": 20},
            )],
            target_position=0,
        )

    @pytest.mark.asyncio
    async def test_cover_delete_disables_rule_that_lost_its_last_cover(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_delete

        async with _real_instance(tmp_path, ["cover.a", "cover.b"], []) as (
            hass, _, storage, coordinator,
        ):
            hass.states.async_set("sensor.outdoor_temp", "25")
            await storage.async_add_rule(self._rule("bath", cover_ids=["cover.a"]))

            await ws_cover_delete(hass, MagicMock(), {"id": 1, "entity_id": "cover.a"}, storage, coordinator)

            rule = storage.rules["bath"]
            assert rule.enabled is False
            assert coordinator.engine.evaluate_cover(storage.covers["cover.b"]) is None

    @pytest.mark.asyncio
    async def test_facade_delete_disables_rule_that_lost_its_last_facade(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_facade_delete

        async with _real_instance(tmp_path, ["cover.a"], ["south"]) as (
            hass, _, storage, coordinator,
        ):
            hass.states.async_set("sensor.outdoor_temp", "25")
            await storage.async_add_rule(self._rule("south_rule", facade_ids=["south"]))

            await ws_facade_delete(hass, MagicMock(), {"id": 1, "facade_id": "south"}, storage, coordinator)

            assert storage.rules["south_rule"].enabled is False
            assert coordinator.engine.evaluate_cover(storage.covers["cover.a"]) is None

    @pytest.mark.asyncio
    async def test_rule_with_remaining_targets_stays_enabled(self, tmp_path) -> None:
        from custom_components.cover_automatic.api import ws_cover_delete, ws_facade_delete

        async with _real_instance(tmp_path, ["cover.a", "cover.b"], ["south"]) as (
            hass, _, storage, coordinator,
        ):
            await storage.async_add_rule(self._rule("two_covers", cover_ids=["cover.a", "cover.b"]))
            await storage.async_add_rule(
                self._rule("cover_and_facade", cover_ids=["cover.a"], facade_ids=["south"])
            )

            await ws_cover_delete(hass, MagicMock(), {"id": 1, "entity_id": "cover.a"}, storage, coordinator)

            assert storage.rules["two_covers"].enabled is True
            assert storage.rules["two_covers"].cover_ids == ["cover.b"]
            assert storage.rules["cover_and_facade"].enabled is True
            assert storage.rules["cover_and_facade"].facade_ids == ["south"]

            await ws_facade_delete(hass, MagicMock(), {"id": 2, "facade_id": "south"}, storage, coordinator)

            assert storage.rules["cover_and_facade"].enabled is False

    @pytest.mark.asyncio
    async def test_global_rule_is_left_alone(self, tmp_path) -> None:
        """A rule that was global on purpose is not touched by a delete."""
        from custom_components.cover_automatic.api import ws_cover_delete

        async with _real_instance(tmp_path, ["cover.a", "cover.b"], []) as (
            hass, _, storage, coordinator,
        ):
            await storage.async_add_rule(self._rule("everywhere"))

            await ws_cover_delete(hass, MagicMock(), {"id": 1, "entity_id": "cover.a"}, storage, coordinator)

            assert storage.rules["everywhere"].enabled is True


class TestImportKeepsSettingsUsable:
    """Importing a backup must not empty settings that were never saved.

    The panel saves settings per section, so a fresh or partly configured
    instance has no stored value for many of them. The import copied the
    current value for every setting missing in the file and wrote None where
    there was none: the master switch read as off and the next move raised a
    TypeError on min_position_change.
    """

    @pytest.fixture(autouse=True)
    def _instant_save(self, monkeypatch) -> None:
        """Skip the 2 s save debounce that async_block_till_done would wait for."""
        monkeypatch.setattr("custom_components.cover_automatic.storage.SAVE_DEBOUNCE_DELAY", 0)

    @staticmethod
    async def _export(hass, storage, coordinator) -> dict:
        from custom_components.cover_automatic.api import ws_export_config

        connection = MagicMock()
        await ws_export_config(hass, connection, {"id": 1}, storage, coordinator)
        return connection.send_result.call_args[0][1]["data"]

    @staticmethod
    async def _import(hass, storage, coordinator, data: dict) -> None:
        from custom_components.cover_automatic.api import ws_import_config

        await ws_import_config(hass, MagicMock(), {"id": 2, "data": data}, storage, coordinator)
        await hass.async_block_till_done()

    @pytest.mark.asyncio
    async def test_roundtrip_of_fresh_install_keeps_automation_working(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            calls: list[dict] = []

            async def _record(call) -> None:
                calls.append(dict(call.data))

            hass.services.async_register("cover", "set_cover_position", _record)
            hass.states.async_set("cover.a", "open", {"current_position": 100})
            hass.states.async_set("sensor.outdoor_temp", "25")
            await storage.async_add_rule(Rule(
                id="close", name="Close", enabled=True, priority=10, cover_ids=["cover.a"],
                conditions=[Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.outdoor_temp", "value": 20},
                )],
                target_position=0,
            ))

            await self._import(hass, storage, coordinator, await self._export(hass, storage, coordinator))

            assert storage.enabled is True
            assert storage.min_position_change == 5
            assert storage.pause_duration == 10
            assert storage.command_stagger == 0.0
            coordinator._startup_time = -999.0
            await coordinator.async_refresh()
            await hass.async_block_till_done()
            assert coordinator.last_update_success is True
            assert calls == [{"entity_id": "cover.a", "position": 0}]

    @pytest.mark.asyncio
    async def test_import_keeps_current_value_of_settings_missing_in_file(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            storage.update_check_enabled = False
            storage.min_position_change = 8
            data = await self._export(hass, storage, coordinator)
            del data["update_check_enabled"], data["min_position_change"]

            await self._import(hass, storage, coordinator, data)

            assert storage.update_check_enabled is False
            assert storage.min_position_change == 8

    @pytest.mark.asyncio
    async def test_import_repairs_empty_settings_in_file(self, tmp_path) -> None:
        """Backups written after the faulty import carry the empty values."""
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            data = await self._export(hass, storage, coordinator)
            data.update(enabled=None, min_position_change=None, lock_position=None, wind_sensor=None)

            await self._import(hass, storage, coordinator, data)

            assert storage.enabled is False  # None read as off before, stays off
            assert storage.min_position_change == 5
            assert storage.lock_position == 100
            assert storage.wind_sensor is None  # None is a valid "not set" here

    @pytest.mark.asyncio
    async def test_load_repairs_settings_emptied_by_an_earlier_import(self, tmp_path) -> None:
        async with _real_instance(tmp_path, [], []) as (hass, _, storage, _coordinator):
            raw = storage.get_raw_data()
            raw.update(
                enabled=None, logbook_enabled=None, min_position_change=None,
                min_time_between_changes=None, comfort_temp_min=None,
                lock_tilt_position=None, outdoor_temp_sensor=None,
            )
            await storage._store.async_save(raw)

            reloaded = CoverAutomaticStorage(hass)
            await reloaded.async_load()

            assert reloaded.enabled is False
            assert reloaded.logbook_enabled is False
            assert reloaded.min_position_change == 5
            assert reloaded.min_time_between_changes == 300
            assert reloaded.comfort_temp_min == 21.0
            assert reloaded.lock_tilt_position is None
            assert reloaded.outdoor_temp_sensor is None


class TestImportKeepsRuntimeStatus:
    """A backup must not bring back the runtime status stored in it.

    The import replaced each cover's status, pause_until and
    last_position_change with the values from the file. A cover paused live
    got pause_until None and its pause never expired, and a file status
    "locked" made the cover count as locked at shutdown on the next restart.
    """

    @pytest.fixture(autouse=True)
    def _instant_save(self, monkeypatch) -> None:
        """Skip the 2 s save debounce that async_block_till_done would wait for."""
        monkeypatch.setattr("custom_components.cover_automatic.storage.SAVE_DEBOUNCE_DELAY", 0)

    @staticmethod
    async def _import(hass, storage, coordinator, data: dict) -> None:
        from custom_components.cover_automatic.api import ws_import_config

        await ws_import_config(hass, MagicMock(), {"id": 1, "data": data}, storage, coordinator)
        await hass.async_block_till_done()

    @staticmethod
    def _file(*covers: CoverConfig) -> dict:
        return {
            "covers": {c.entity_id: c.to_dict() for c in covers},
            "facades": {}, "rules": {}, "scenarios": {},
        }

    @pytest.mark.asyncio
    async def test_import_keeps_live_status_of_existing_cover(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            coordinator.pause_cover(storage.covers["cover.a"])
            paused_until = storage.get_cover_raw("cover.a")["pause_until"]
            assert paused_until is not None

            await self._import(hass, storage, coordinator, self._file(
                CoverConfig(entity_id="cover.a", name="A", status=CoverStatus.AUTO, pause_until=None),
            ))

            raw = storage.get_cover_raw("cover.a")
            assert raw["status"] == CoverStatus.PAUSED.value
            assert raw["pause_until"] == paused_until

    @pytest.mark.asyncio
    async def test_import_starts_new_cover_without_runtime_status(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, _, storage, coordinator):
            await self._import(hass, storage, coordinator, self._file(CoverConfig(
                entity_id="cover.new", name="New", status=CoverStatus.LOCKED,
                pause_until=1.0, last_position_change=2.0,
            )))

            raw = storage.get_cover_raw("cover.new")
            assert raw["status"] == CoverStatus.AUTO.value
            assert raw["pause_until"] is None
            assert raw["last_position_change"] is None

    @pytest.mark.asyncio
    async def test_imported_locked_status_does_not_lock_after_restart(self, tmp_path) -> None:
        async with _real_instance(tmp_path, ["cover.a"], []) as (hass, entry, storage, coordinator):
            hass.states.async_set("binary_sensor.window", "unavailable")
            await self._import(hass, storage, coordinator, self._file(CoverConfig(
                entity_id="cover.a", name="A", status=CoverStatus.LOCKED,
                lock_sensor="binary_sensor.window",
            )))

            restarted = CoverAutomaticCoordinator(hass, storage, 60, config_entry=entry)
            restarted._restore_cover_states()
            await restarted.async_refresh()

            assert restarted.get_cover_status("cover.a") == CoverStatus.AUTO
