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

    coordinator = MagicMock()
    coordinator.storage = storage
    coordinator.config_entry = entry
    coordinator.data = {}
    coordinator.get_live_cover = MagicMock(return_value=None)
    coordinator.get_active_rules = MagicMock(return_value={})
    coordinator.get_live_cover_data = MagicMock(return_value={})
    coordinator.get_live_facade_data = MagicMock(return_value={})
    entry.runtime_data = SimpleNamespace(coordinator=coordinator, storage=storage)

    for domain, module in (("sensor", sensor), ("switch", switch)):
        platform = EntityPlatform(
            hass=hass, logger=logging.getLogger(__name__), domain=domain,
            platform_name=DOMAIN, platform=None,
            scan_interval=timedelta(seconds=60), entity_namespace=None,
        )
        platform.config_entry = entry
        entities: list = []
        await module.async_setup_entry(hass, entry, entities.extend)
        await platform.async_add_entities(entities)
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
