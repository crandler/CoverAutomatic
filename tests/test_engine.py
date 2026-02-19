"""Tests for CoverAutomatic rule engine."""
from __future__ import annotations

from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from custom_components.cover_automatic.engine import RuleEngine
from custom_components.cover_automatic.models import (
    ComfortMode,
    Condition,
    ConditionType,
    CoverConfig,
    Facade,
    Rule,
    Scenario,
)


class MockState:
    """Mock Home Assistant state object."""

    def __init__(self, state: str) -> None:
        """Initialize mock state."""
        self.state = state


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_storage():
    """Create mock storage instance."""
    storage = MagicMock()
    storage.active_scenario = "everyday"
    storage.facades = {}
    storage.rules = {}
    storage.scenarios = {}
    storage.outdoor_temp_sensor = None
    storage.indoor_temp_sensor = "sensor.indoor_temp"
    storage.weather_entity = "weather.home"
    storage.comfort_temp_min = 21.0
    storage.comfort_temp_max = 25.0
    return storage


@pytest.fixture
def engine(mock_hass, mock_storage):
    """Create rule engine instance."""
    return RuleEngine(mock_hass, mock_storage)


@pytest.fixture
def test_facade():
    """Create test facade."""
    return Facade(
        id="south",
        name="South Facade",
        azimuth_start=135.0,
        azimuth_end=225.0,
        direction="south",
    )


@pytest.fixture
def test_cover():
    """Create test cover config."""
    return CoverConfig(
        entity_id="cover.living_room",
        name="Living Room",
        facade_id="south",
    )


class TestRuleEngine:
    """Tests for RuleEngine class."""

    def test_engine_creation(self, engine, mock_hass, mock_storage) -> None:
        """Test engine initialization."""
        assert engine.hass == mock_hass
        assert engine.storage == mock_storage

    def test_evaluate_no_rules(self, engine, test_cover) -> None:
        """Test evaluation with no rules returns None."""
        result = engine.evaluate_cover(test_cover)
        assert result is None

    def test_evaluate_disabled_rule(
        self, engine, mock_storage, test_cover
    ) -> None:
        """Test disabled rules are skipped."""
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            enabled=False,
            target_position=50,
        )
        mock_storage.rules = {"test_rule": rule}

        result = engine.evaluate_cover(test_cover)
        assert result is None

    def test_evaluate_matching_rule(
        self, engine, mock_storage, test_cover
    ) -> None:
        """Test matching rule returns target position."""
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            enabled=True,
            target_position=30,
            conditions=[],
        )
        mock_storage.rules = {"test_rule": rule}

        result = engine.evaluate_cover(test_cover)
        assert result == 30

    def test_evaluate_priority_ordering(
        self, engine, mock_storage, test_cover
    ) -> None:
        """Test higher priority rules take precedence."""
        low_priority = Rule(
            id="low",
            name="Low Priority",
            enabled=True,
            priority=5,
            target_position=20,
        )
        high_priority = Rule(
            id="high",
            name="High Priority",
            enabled=True,
            priority=15,
            target_position=80,
        )
        mock_storage.rules = {"low": low_priority, "high": high_priority}

        result = engine.evaluate_cover(test_cover)
        assert result == 80


class TestRuleApplies:
    """Tests for rule application logic."""

    def test_rule_applies_to_cover_by_entity_id(
        self, engine, test_cover
    ) -> None:
        """Test rule applies when cover entity_id matches."""
        rule = Rule(
            id="test",
            name="Test",
            cover_ids=["cover.living_room"],
        )
        assert engine._rule_applies_to_cover(rule, test_cover) is True

    def test_rule_applies_to_cover_by_facade(
        self, engine, test_cover
    ) -> None:
        """Test rule applies when facade_id matches."""
        rule = Rule(
            id="test",
            name="Test",
            facade_ids=["south"],
        )
        assert engine._rule_applies_to_cover(rule, test_cover) is True

    def test_rule_applies_to_all_covers(self, engine, test_cover) -> None:
        """Test rule with no filters applies to all covers."""
        rule = Rule(id="test", name="Test")
        assert engine._rule_applies_to_cover(rule, test_cover) is True

    def test_rule_does_not_apply(self, engine, test_cover) -> None:
        """Test rule does not apply to non-matching cover."""
        rule = Rule(
            id="test",
            name="Test",
            cover_ids=["cover.bedroom"],
            facade_ids=["north"],
        )
        assert engine._rule_applies_to_cover(rule, test_cover) is False


class TestScenarioLogic:
    """Tests for scenario-based rule activation."""

    def test_rule_disabled_in_scenario(
        self, engine, mock_storage
    ) -> None:
        """Test rule disabled by scenario."""
        scenario = Scenario(
            id="vacation",
            name="Vacation",
            rules_disabled=["test_rule"],
        )
        rule = Rule(id="test_rule", name="Test")
        mock_storage.scenarios = {"vacation": scenario}
        mock_storage.active_scenario = "vacation"

        assert engine._rule_active_in_scenario(rule, "vacation") is False

    def test_rule_active_in_default_scenario(
        self, engine, mock_storage
    ) -> None:
        """Test rule active when no scenario restrictions."""
        rule = Rule(id="test_rule", name="Test")
        mock_storage.scenarios = {}

        assert engine._rule_active_in_scenario(rule, "everyday") is True


class TestConditionEvaluation:
    """Tests for condition evaluation."""

    def test_eval_temp_above_true(
        self, engine, mock_hass
    ) -> None:
        """Test temperature_above condition when true."""
        mock_hass.states.get.return_value = MockState("28.5")

        condition = Condition(
            type=ConditionType.TEMPERATURE_ABOVE,
            params={"sensor": "sensor.outdoor", "value": 25},
        )
        result = engine._eval_temp_threshold(condition, above=True)
        assert result is True

    def test_eval_temp_above_false(
        self, engine, mock_hass
    ) -> None:
        """Test temperature_above condition when false."""
        mock_hass.states.get.return_value = MockState("20.0")

        condition = Condition(
            type=ConditionType.TEMPERATURE_ABOVE,
            params={"sensor": "sensor.outdoor", "value": 25},
        )
        result = engine._eval_temp_threshold(condition, above=True)
        assert result is False

    def test_eval_temp_above_invalid_state(
        self, engine, mock_hass
    ) -> None:
        """Test temperature_above with invalid state returns false."""
        mock_hass.states.get.return_value = MockState("unavailable")

        condition = Condition(
            type=ConditionType.TEMPERATURE_ABOVE,
            params={"sensor": "sensor.outdoor", "value": 25},
        )
        result = engine._eval_temp_threshold(condition, above=True)
        assert result is False

    def test_eval_temp_above_missing_sensor(
        self, engine, mock_hass
    ) -> None:
        """Test temperature_above with missing sensor returns false."""
        mock_hass.states.get.return_value = None

        condition = Condition(
            type=ConditionType.TEMPERATURE_ABOVE,
            params={"sensor": "sensor.outdoor", "value": 25},
        )
        result = engine._eval_temp_threshold(condition, above=True)
        assert result is False

    def test_eval_temp_below_true(
        self, engine, mock_hass
    ) -> None:
        """Test temperature_below condition when true."""
        mock_hass.states.get.return_value = MockState("15.0")

        condition = Condition(
            type=ConditionType.TEMPERATURE_BELOW,
            params={"sensor": "sensor.outdoor", "value": 20},
        )
        result = engine._eval_temp_threshold(condition, above=False)
        assert result is True

    def test_eval_state_is_true(
        self, engine, mock_hass
    ) -> None:
        """Test state_is condition when matching."""
        mock_hass.states.get.return_value = MockState("on")

        condition = Condition(
            type=ConditionType.STATE_IS,
            params={"entity": "binary_sensor.window", "state": "on"},
        )
        result = engine._eval_state_is(condition)
        assert result is True

    def test_eval_state_is_false(
        self, engine, mock_hass
    ) -> None:
        """Test state_is condition when not matching."""
        mock_hass.states.get.return_value = MockState("off")

        condition = Condition(
            type=ConditionType.STATE_IS,
            params={"entity": "binary_sensor.window", "state": "on"},
        )
        result = engine._eval_state_is(condition)
        assert result is False

    @patch("custom_components.cover_automatic.engine.dt_util")
    def test_eval_time_between_true(
        self, mock_dt_util, engine
    ) -> None:
        """Test time_between condition when in range."""
        mock_now = MagicMock()
        mock_now.time.return_value = time(12, 0)
        mock_dt_util.now.return_value = mock_now

        condition = Condition(
            type=ConditionType.TIME_BETWEEN,
            params={"start": "08:00", "end": "18:00"},
        )
        result = engine._eval_time_between(condition)
        assert result is True

    @patch("custom_components.cover_automatic.engine.dt_util")
    def test_eval_time_between_false(
        self, mock_dt_util, engine
    ) -> None:
        """Test time_between condition when outside range."""
        mock_now = MagicMock()
        mock_now.time.return_value = time(22, 0)
        mock_dt_util.now.return_value = mock_now

        condition = Condition(
            type=ConditionType.TIME_BETWEEN,
            params={"start": "08:00", "end": "18:00"},
        )
        result = engine._eval_time_between(condition)
        assert result is False

    @patch("custom_components.cover_automatic.engine.dt_util")
    def test_eval_time_between_overnight(
        self, mock_dt_util, engine
    ) -> None:
        """Test time_between with overnight range (e.g., 22:00-06:00)."""
        mock_now = MagicMock()
        mock_now.time.return_value = time(23, 0)
        mock_dt_util.now.return_value = mock_now

        condition = Condition(
            type=ConditionType.TIME_BETWEEN,
            params={"start": "22:00", "end": "06:00"},
        )
        result = engine._eval_time_between(condition)
        assert result is True


class TestComfortCondition:
    """Tests for comfort mode condition."""

    def test_eval_comfort_cooling_mode(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test comfort condition in cooling mode."""
        mock_hass.states.get.return_value = MockState("28.0")

        condition = Condition(
            type=ConditionType.TEMPERATURE_COMFORT,
            params={"mode": ComfortMode.COOLING},
        )
        result = engine._eval_temp_comfort(condition)
        assert result is True

    def test_eval_comfort_heating_mode(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test comfort condition in heating mode."""
        mock_hass.states.get.return_value = MockState("18.0")

        condition = Condition(
            type=ConditionType.TEMPERATURE_COMFORT,
            params={"mode": ComfortMode.HEATING},
        )
        result = engine._eval_temp_comfort(condition)
        assert result is True

    def test_eval_comfort_neutral_mode(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test comfort condition in neutral mode."""
        mock_hass.states.get.return_value = MockState("23.0")

        condition = Condition(
            type=ConditionType.TEMPERATURE_COMFORT,
            params={"mode": ComfortMode.NEUTRAL},
        )
        result = engine._eval_temp_comfort(condition)
        assert result is True


class TestWeatherCondition:
    """Tests for weather condition evaluation."""

    def test_eval_weather_sunny(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test weather condition for sunny."""
        mock_hass.states.get.return_value = MockState("sunny")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": ["sunny"]},
        )
        result = engine._eval_weather_is(condition)
        assert result is True

    def test_eval_weather_clear_matches_sunny(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test clear weather matches sunny group."""
        mock_hass.states.get.return_value = MockState("clear")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": ["sunny"]},
        )
        result = engine._eval_weather_is(condition)
        assert result is True

    def test_eval_weather_cloudy(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test weather condition for cloudy."""
        mock_hass.states.get.return_value = MockState("cloudy")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": ["cloudy"]},
        )
        result = engine._eval_weather_is(condition)
        assert result is True

    def test_eval_weather_rainy(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test weather condition for rainy."""
        mock_hass.states.get.return_value = MockState("pouring")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": ["rainy"]},
        )
        result = engine._eval_weather_is(condition)
        assert result is True

    def test_eval_weather_no_match(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test weather condition when no match."""
        mock_hass.states.get.return_value = MockState("windy")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": ["sunny", "cloudy"]},
        )
        result = engine._eval_weather_is(condition)
        assert result is False

    def test_eval_weather_string_param(
        self, engine, mock_hass, mock_storage
    ) -> None:
        """Test weather condition with string instead of list."""
        mock_hass.states.get.return_value = MockState("sunny")

        condition = Condition(
            type=ConditionType.WEATHER_IS,
            params={"states": "sunny"},
        )
        result = engine._eval_weather_is(condition)
        assert result is True


class TestConditionOperator:
    """Tests for condition operator logic (AND/OR)."""

    def test_and_operator_all_true(
        self, engine, mock_hass, test_cover
    ) -> None:
        """Test AND operator: all conditions true -> True."""
        mock_hass.states.get.return_value = MockState("30.0")

        rule = Rule(
            id="test",
            name="Test",
            condition_operator="and",
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 25},
                ),
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 20},
                ),
            ],
        )

        result = engine._evaluate_conditions(rule, test_cover)
        assert result is True

    def test_and_operator_one_false(
        self, engine, mock_hass, test_cover
    ) -> None:
        """Test AND operator: one condition false -> False."""
        mock_hass.states.get.return_value = MockState("22.0")

        rule = Rule(
            id="test",
            name="Test",
            condition_operator="and",
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 20},
                ),
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 25},
                ),
            ],
        )

        result = engine._evaluate_conditions(rule, test_cover)
        assert result is False

    def test_or_operator_one_true(
        self, engine, mock_hass, test_cover
    ) -> None:
        """Test OR operator: one condition true -> True."""
        mock_hass.states.get.return_value = MockState("22.0")

        rule = Rule(
            id="test",
            name="Test",
            condition_operator="or",
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 20},
                ),
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 25},
                ),
            ],
        )

        result = engine._evaluate_conditions(rule, test_cover)
        assert result is True

    def test_or_operator_all_false(
        self, engine, mock_hass, test_cover
    ) -> None:
        """Test OR operator: all conditions false -> False."""
        mock_hass.states.get.return_value = MockState("15.0")

        rule = Rule(
            id="test",
            name="Test",
            condition_operator="or",
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 20},
                ),
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 25},
                ),
            ],
        )

        result = engine._evaluate_conditions(rule, test_cover)
        assert result is False

    def test_default_operator_is_and(
        self, engine, mock_hass, test_cover
    ) -> None:
        """Test default operator is AND when not specified."""
        mock_hass.states.get.return_value = MockState("22.0")

        rule = Rule(
            id="test",
            name="Test",
            conditions=[
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 20},
                ),
                Condition(
                    type=ConditionType.TEMPERATURE_ABOVE,
                    params={"sensor": "sensor.temp", "value": 25},
                ),
            ],
        )

        # Default is AND, so one false condition should fail
        result = engine._evaluate_conditions(rule, test_cover)
        assert result is False

    def test_empty_conditions_returns_true(
        self, engine, test_cover
    ) -> None:
        """Test empty conditions list returns True for both operators."""
        rule_and = Rule(
            id="test_and",
            name="Test AND",
            condition_operator="and",
            conditions=[],
        )
        rule_or = Rule(
            id="test_or",
            name="Test OR",
            condition_operator="or",
            conditions=[],
        )

        assert engine._evaluate_conditions(rule_and, test_cover) is True
        assert engine._evaluate_conditions(rule_or, test_cover) is True


class TestSunOnFacadeCondition:
    """Tests for sun_on_facade condition evaluation."""

    @patch("custom_components.cover_automatic.engine.is_sun_on_facade")
    def test_eval_sun_on_facade_with_explicit_facade_param(
        self, mock_is_sun_on_facade, engine, mock_storage
    ) -> None:
        """Test sun_on_facade uses explicit facade param from condition."""
        facade = Facade(
            id="north",
            name="North Facade",
            azimuth_start=315.0,
            azimuth_end=45.0,
            direction="north",
        )
        mock_storage.facades = {"north": facade}
        mock_is_sun_on_facade.return_value = True

        condition = Condition(
            type=ConditionType.SUN_ON_FACADE,
            params={"facade": "north"},
        )
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            facade_id="south",
        )

        result = engine._eval_sun_on_facade(condition, cover)

        assert result is True
        mock_is_sun_on_facade.assert_called_once_with(engine.hass, facade)

    @patch("custom_components.cover_automatic.engine.is_sun_on_facade")
    def test_eval_sun_on_facade_falls_back_to_cover_facade(
        self, mock_is_sun_on_facade, engine, mock_storage, test_cover
    ) -> None:
        """Test sun_on_facade falls back to cover.facade_id when no param given."""
        facade = Facade(
            id="south",
            name="South Facade",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        mock_storage.facades = {"south": facade}
        mock_is_sun_on_facade.return_value = True

        condition = Condition(
            type=ConditionType.SUN_ON_FACADE,
            params={},
        )

        result = engine._eval_sun_on_facade(condition, test_cover)

        assert result is True
        mock_is_sun_on_facade.assert_called_once_with(engine.hass, facade)

    def test_eval_sun_on_facade_no_facade_returns_false(
        self, engine, mock_storage
    ) -> None:
        """Test sun_on_facade returns False when no facade id available."""
        mock_storage.facades = {}

        condition = Condition(
            type=ConditionType.SUN_ON_FACADE,
            params={},
        )
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            facade_id=None,
        )

        result = engine._eval_sun_on_facade(condition, cover)

        assert result is False

    def test_eval_sun_on_facade_facade_not_in_storage(
        self, engine, mock_storage, test_cover
    ) -> None:
        """Test sun_on_facade returns False when facade_id not found in storage."""
        mock_storage.facades = {}

        condition = Condition(
            type=ConditionType.SUN_ON_FACADE,
            params={},
        )

        result = engine._eval_sun_on_facade(condition, test_cover)

        assert result is False


class TestTimeAfterSunriseCondition:
    """Tests for time_after_sunrise condition evaluation."""

    @patch("custom_components.cover_automatic.engine.dt_util")
    @patch("custom_components.cover_automatic.engine.get_sunrise_time")
    def test_time_after_sunrise_true(
        self, mock_get_sunrise, mock_dt_util, engine
    ) -> None:
        """Test time_after_sunrise returns True when current time is past sunrise + offset."""
        sunrise_ts = 1_700_000_000.0
        mock_get_sunrise.return_value = sunrise_ts
        mock_dt_util.now.return_value.timestamp.return_value = sunrise_ts + 3600.0

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNRISE,
            params={"offset": 30},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunrise)

        assert result is True

    @patch("custom_components.cover_automatic.engine.dt_util")
    @patch("custom_components.cover_automatic.engine.get_sunrise_time")
    def test_time_after_sunrise_false(
        self, mock_get_sunrise, mock_dt_util, engine
    ) -> None:
        """Test time_after_sunrise returns False when current time is before sunrise + offset."""
        sunrise_ts = 1_700_000_000.0
        mock_get_sunrise.return_value = sunrise_ts
        # 10 minutes before sunrise+60 minutes offset
        mock_dt_util.now.return_value.timestamp.return_value = sunrise_ts + 600.0 - 1

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNRISE,
            params={"offset": 10},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunrise)

        assert result is False

    @patch("custom_components.cover_automatic.engine.get_sunrise_time")
    def test_time_after_sunrise_no_sunrise(
        self, mock_get_sunrise, engine
    ) -> None:
        """Test time_after_sunrise returns False when sunrise time is unavailable."""
        mock_get_sunrise.return_value = None

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNRISE,
            params={"offset": 0},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunrise)

        assert result is False

    @patch("custom_components.cover_automatic.engine.get_sunrise_time")
    def test_time_after_sunrise_invalid_offset(
        self, mock_get_sunrise, engine
    ) -> None:
        """Test time_after_sunrise returns False when offset is non-numeric."""
        mock_get_sunrise.return_value = 1_700_000_000.0

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNRISE,
            params={"offset": "abc"},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunrise)

        assert result is False


class TestTimeAfterSunsetCondition:
    """Tests for time_after_sunset condition evaluation."""

    @patch("custom_components.cover_automatic.engine.dt_util")
    @patch("custom_components.cover_automatic.engine.get_sunset_time")
    def test_time_after_sunset_true(
        self, mock_get_sunset, mock_dt_util, engine
    ) -> None:
        """Test time_after_sunset returns True when current time is past sunset + offset."""
        sunset_ts = 1_700_070_000.0
        mock_get_sunset.return_value = sunset_ts
        mock_dt_util.now.return_value.timestamp.return_value = sunset_ts + 1800.0

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNSET,
            params={"offset": 15},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunset)

        assert result is True

    @patch("custom_components.cover_automatic.engine.dt_util")
    @patch("custom_components.cover_automatic.engine.get_sunset_time")
    def test_time_after_sunset_false(
        self, mock_get_sunset, mock_dt_util, engine
    ) -> None:
        """Test time_after_sunset returns False when current time is before sunset + offset."""
        sunset_ts = 1_700_070_000.0
        mock_get_sunset.return_value = sunset_ts
        # 5 seconds before sunset + 30-minute offset
        mock_dt_util.now.return_value.timestamp.return_value = sunset_ts + 1800.0 - 5

        condition = Condition(
            type=ConditionType.TIME_AFTER_SUNSET,
            params={"offset": 30},
        )

        result = engine._eval_time_after_sun_event(condition, mock_get_sunset)

        assert result is False


class TestConditionExceptionHandling:
    """Tests for exception handling in condition evaluation."""

    def test_evaluate_condition_exception_returns_false(
        self, engine, mock_storage, test_cover
    ) -> None:
        """Test _evaluate_condition returns False when evaluation raises an exception."""
        mock_storage.facades = None  # Causes AttributeError on .get()

        condition = Condition(
            type=ConditionType.SUN_ON_FACADE,
            params={},
        )

        result = engine._evaluate_condition(condition, test_cover)

        assert result is False
