"""Integration tests for CoverAutomatic coordinator flows."""
from __future__ import annotations

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
        coord._pre_lock_states = {}
        coord.data = {}
        coord.logger = MagicMock()

        # Mock parent class methods
        coord.async_set_updated_data = MagicMock()
        coord.async_request_refresh = AsyncMock()

        # Create real engine
        from custom_components.cover_automatic.engine import RuleEngine
        coord.engine = RuleEngine(mock_hass, mock_storage)

        return coord


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

        with patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
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

        # Cover should be locked at vent position
        assert coordinator._cover_states["cover.test"] == CoverStatus.LOCKED


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
