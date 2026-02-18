"""Tests for CoverAutomatic data models."""
from __future__ import annotations


from custom_components.cover_automatic.models import (
    ComfortMode,
    Condition,
    ConditionType,
    CoverConfig,
    CoverStatus,
    Facade,
    Rule,
    Scenario,
)


class TestFacade:
    """Tests for Facade model."""

    def test_facade_creation(self, sample_facade: Facade) -> None:
        """Test facade creation with valid data."""
        assert sample_facade.id == "south_facade"
        assert sample_facade.name == "South Facade"
        assert sample_facade.direction == "south"
        assert sample_facade.azimuth_start == 135.0
        assert sample_facade.azimuth_end == 225.0

    def test_facade_to_dict(self, sample_facade: Facade) -> None:
        """Test facade serialization to dictionary."""
        data = sample_facade.to_dict()
        assert data["id"] == "south_facade"
        assert data["name"] == "South Facade"
        assert data["direction"] == "south"
        assert data["azimuth_start"] == 135.0
        assert data["azimuth_end"] == 225.0

    def test_facade_from_dict(self) -> None:
        """Test facade deserialization from dictionary."""
        data = {
            "id": "east_facade",
            "name": "East Facade",
            "azimuth_start": 45.0,
            "azimuth_end": 135.0,
            "direction": "east",
        }
        facade = Facade.from_dict(data)
        assert facade.id == "east_facade"
        assert facade.direction == "east"

    def test_facade_roundtrip(self, sample_facade: Facade) -> None:
        """Test facade serialization roundtrip."""
        data = sample_facade.to_dict()
        restored = Facade.from_dict(data)
        assert restored.id == sample_facade.id
        assert restored.name == sample_facade.name
        assert restored.azimuth_start == sample_facade.azimuth_start


class TestCoverConfig:
    """Tests for CoverConfig model."""

    def test_cover_creation(self, sample_cover: CoverConfig) -> None:
        """Test cover configuration creation."""
        assert sample_cover.entity_id == "cover.living_room"
        assert sample_cover.name == "Living Room"
        assert sample_cover.facade_id == "south_facade"
        assert sample_cover.auto_enabled is True
        assert sample_cover.status == CoverStatus.AUTO

    def test_cover_defaults(self) -> None:
        """Test cover configuration defaults."""
        cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
        )
        assert cover.pause_duration == 120
        assert cover.lock_position == 100
        assert cover.vent_position == 30
        assert cover.inverted is False
        assert cover.min_position_change == 5
        assert cover.min_time_between_changes == 300

    def test_cover_to_dict(self, sample_cover: CoverConfig) -> None:
        """Test cover serialization."""
        data = sample_cover.to_dict()
        assert data["entity_id"] == "cover.living_room"
        assert data["auto_enabled"] is True
        assert data["status"] == "auto"

    def test_cover_from_dict(self) -> None:
        """Test cover deserialization."""
        data = {
            "entity_id": "cover.bedroom",
            "name": "Bedroom",
            "status": "paused",
            "inverted": True,
        }
        cover = CoverConfig.from_dict(data)
        assert cover.entity_id == "cover.bedroom"
        assert cover.status == CoverStatus.PAUSED
        assert cover.inverted is True


class TestCondition:
    """Tests for Condition model."""

    def test_condition_creation(self) -> None:
        """Test condition creation."""
        condition = Condition(
            type=ConditionType.TEMPERATURE_ABOVE,
            params={"sensor": "sensor.outdoor", "value": 25},
        )
        assert condition.type == ConditionType.TEMPERATURE_ABOVE
        assert condition.params["value"] == 25

    def test_condition_to_dict(self) -> None:
        """Test condition serialization."""
        condition = Condition(
            type=ConditionType.TIME_BETWEEN,
            params={"start": "08:00", "end": "20:00"},
        )
        data = condition.to_dict()
        assert data["type"] == "time_between"
        assert data["params"]["start"] == "08:00"

    def test_condition_from_dict(self) -> None:
        """Test condition deserialization."""
        data = {
            "type": "sun_elevation_above",
            "params": {"value": 10},
        }
        condition = Condition.from_dict(data)
        assert condition.type == ConditionType.SUN_ELEVATION_ABOVE
        assert condition.params["value"] == 10


class TestRule:
    """Tests for Rule model."""

    def test_rule_creation(self, sample_rule: Rule) -> None:
        """Test rule creation."""
        assert sample_rule.id == "sun_shade"
        assert sample_rule.name == "Sun Shade Rule"
        assert sample_rule.enabled is True
        assert sample_rule.priority == 10
        assert len(sample_rule.conditions) == 2
        assert sample_rule.target_position == 30

    def test_rule_defaults(self) -> None:
        """Test rule defaults."""
        rule = Rule(id="test", name="Test Rule")
        assert rule.enabled is True
        assert rule.priority == 10
        assert rule.target_position == 0
        assert rule.conditions == []

    def test_rule_to_dict(self, sample_rule: Rule) -> None:
        """Test rule serialization."""
        data = sample_rule.to_dict()
        assert data["id"] == "sun_shade"
        assert len(data["conditions"]) == 2
        assert data["conditions"][0]["type"] == "sun_on_facade"

    def test_rule_from_dict(self) -> None:
        """Test rule deserialization."""
        data = {
            "id": "night_close",
            "name": "Night Close",
            "enabled": True,
            "priority": 5,
            "target_position": 0,
            "conditions": [
                {"type": "time_after_sunset", "params": {"offset": 30}},
            ],
        }
        rule = Rule.from_dict(data)
        assert rule.id == "night_close"
        assert len(rule.conditions) == 1
        assert rule.conditions[0].type == ConditionType.TIME_AFTER_SUNSET


class TestScenario:
    """Tests for Scenario model."""

    def test_scenario_creation(self, sample_scenario: Scenario) -> None:
        """Test scenario creation."""
        assert sample_scenario.id == "summer"
        assert sample_scenario.name == "Summer Mode"
        assert sample_scenario.icon == "mdi:white-balance-sunny"

    def test_scenario_to_dict(self, sample_scenario: Scenario) -> None:
        """Test scenario serialization."""
        data = sample_scenario.to_dict()
        assert data["id"] == "summer"
        assert data["icon"] == "mdi:white-balance-sunny"

    def test_scenario_from_dict(self) -> None:
        """Test scenario deserialization."""
        data = {
            "id": "vacation",
            "name": "Vacation",
            "rules_disabled": ["comfort_rule"],
        }
        scenario = Scenario.from_dict(data)
        assert scenario.id == "vacation"
        assert scenario.name == "Vacation"
        assert "comfort_rule" in scenario.rules_disabled


class TestRuleConditionOperatorValidation:
    """Tests for Rule.from_dict condition_operator validation."""

    def test_valid_and_operator(self) -> None:
        """Test valid 'and' operator is preserved."""
        data = {"id": "r1", "name": "R", "condition_operator": "and"}
        rule = Rule.from_dict(data)
        assert rule.condition_operator == "and"

    def test_valid_or_operator(self) -> None:
        """Test valid 'or' operator is preserved."""
        data = {"id": "r1", "name": "R", "condition_operator": "or"}
        rule = Rule.from_dict(data)
        assert rule.condition_operator == "or"

    def test_invalid_operator_falls_back_to_and(self) -> None:
        """Test invalid operator defaults to 'and'."""
        data = {"id": "r1", "name": "R", "condition_operator": "xor"}
        rule = Rule.from_dict(data)
        assert rule.condition_operator == "and"

    def test_empty_operator_falls_back_to_and(self) -> None:
        """Test empty string operator defaults to 'and'."""
        data = {"id": "r1", "name": "R", "condition_operator": ""}
        rule = Rule.from_dict(data)
        assert rule.condition_operator == "and"

    def test_missing_operator_defaults_to_and(self) -> None:
        """Test missing operator defaults to 'and'."""
        data = {"id": "r1", "name": "R"}
        rule = Rule.from_dict(data)
        assert rule.condition_operator == "and"


class TestFacadeAzimuthNormalization:
    """Tests for Facade.from_dict azimuth normalization."""

    def test_azimuth_above_360_normalized(self) -> None:
        """Test azimuth values above 360 are normalized."""
        data = {"id": "f1", "name": "F", "azimuth_start": 400.0, "azimuth_end": 500.0}
        facade = Facade.from_dict(data)
        assert facade.azimuth_start == 40.0
        assert facade.azimuth_end == 140.0

    def test_negative_azimuth_normalized(self) -> None:
        """Test negative azimuth values are normalized to positive."""
        data = {"id": "f1", "name": "F", "azimuth_start": -90.0, "azimuth_end": 180.0}
        facade = Facade.from_dict(data)
        assert facade.azimuth_start == 270.0
        assert facade.azimuth_end == 180.0

    def test_exact_360_becomes_zero(self) -> None:
        """Test that azimuth 360 normalizes to 0."""
        data = {"id": "f1", "name": "F", "azimuth_start": 0.0, "azimuth_end": 360.0}
        facade = Facade.from_dict(data)
        assert facade.azimuth_end == 0.0

    def test_normal_values_unchanged(self) -> None:
        """Test normal azimuth values pass through unchanged."""
        data = {"id": "f1", "name": "F", "azimuth_start": 135.0, "azimuth_end": 225.0}
        facade = Facade.from_dict(data)
        assert facade.azimuth_start == 135.0
        assert facade.azimuth_end == 225.0


class TestCoverStatus:
    """Tests for CoverStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert CoverStatus.AUTO.value == "auto"
        assert CoverStatus.PAUSED.value == "paused"
        assert CoverStatus.MANUAL.value == "manual"
        assert CoverStatus.LOCKED.value == "locked"


class TestConditionType:
    """Tests for ConditionType enum."""

    def test_condition_type_values(self) -> None:
        """Test condition type enum values."""
        assert ConditionType.SUN_ON_FACADE.value == "sun_on_facade"
        assert ConditionType.TEMPERATURE_ABOVE.value == "temperature_above"
        assert ConditionType.WEATHER_IS.value == "weather_is"
        assert len(ConditionType) == 11


class TestComfortMode:
    """Tests for ComfortMode enum."""

    def test_comfort_mode_values(self) -> None:
        """Test comfort mode enum values."""
        assert ComfortMode.COOLING.value == "cooling"
        assert ComfortMode.HEATING.value == "heating"
        assert ComfortMode.NEUTRAL.value == "neutral"
