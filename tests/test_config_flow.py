"""Tests for CoverAutomatic config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from custom_components.cover_automatic.config_flow import (
    CoverAutomaticConfigFlow,
    CoverAutomaticOptionsFlow,
    _sanitize_id,
)
from custom_components.cover_automatic.const import FACADE_PRESETS
from custom_components.cover_automatic.models import (
    Facade,
    Rule,
    Scenario,
)


# ---------------------------------------------------------------------------
# _sanitize_id tests
# ---------------------------------------------------------------------------


class TestSanitizeId:
    """Tests for the _sanitize_id utility function."""

    def test_basic_name(self) -> None:
        """Test basic name sanitization."""
        assert _sanitize_id("Living Room") == "living_room"

    def test_german_umlauts(self) -> None:
        """Test German umlaut replacement."""
        assert _sanitize_id("Südfassade") == "suedfassade"
        assert _sanitize_id("Küche") == "kueche"
        assert _sanitize_id("Böden") == "boeden"
        assert _sanitize_id("Straße") == "strasse"

    def test_uppercase_umlauts(self) -> None:
        """Test uppercase umlaut replacement."""
        assert _sanitize_id("Über") == "ueber"
        assert _sanitize_id("Ärger") == "aerger"
        assert _sanitize_id("Öffnung") == "oeffnung"

    def test_special_characters_replaced(self) -> None:
        """Test special characters are replaced with underscores."""
        assert _sanitize_id("test-name") == "test_name"
        assert _sanitize_id("test.name") == "test_name"
        assert _sanitize_id("test/name") == "test_name"

    def test_multiple_underscores_collapsed(self) -> None:
        """Test multiple consecutive underscores are collapsed."""
        assert _sanitize_id("test   name") == "test_name"
        assert _sanitize_id("test---name") == "test_name"

    def test_leading_trailing_underscores_stripped(self) -> None:
        """Test leading and trailing underscores are stripped."""
        assert _sanitize_id("  test  ") == "test"
        assert _sanitize_id("__test__") == "test"

    def test_empty_name_returns_unnamed(self) -> None:
        """Test empty name returns 'unnamed'."""
        assert _sanitize_id("") == "unnamed"
        assert _sanitize_id("   ") == "unnamed"
        assert _sanitize_id("---") == "unnamed"

    def test_numeric_names(self) -> None:
        """Test names with numbers."""
        assert _sanitize_id("Facade 1") == "facade_1"
        assert _sanitize_id("123") == "123"


# ---------------------------------------------------------------------------
# ConfigFlow tests
# ---------------------------------------------------------------------------


class TestConfigFlow:
    """Tests for the initial ConfigFlow."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock hass instance with cover entities."""
        hass = MagicMock()
        mock_cover_state = MagicMock()
        mock_cover_state.entity_id = "cover.living_room"
        hass.states.async_all.return_value = [mock_cover_state]
        return hass

    @pytest.mark.asyncio
    async def test_step_user_shows_form(self) -> None:
        """Test user step shows form when no input."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = await flow.async_step_user(None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_with_input_proceeds(self) -> None:
        """Test user step proceeds to facades step with input."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "facades"})

        await flow.async_step_user({"name": "My Covers"})

        assert flow._data["name"] == "My Covers"

    @pytest.mark.asyncio
    async def test_step_facades_add_facade(self) -> None:
        """Test adding a facade in the config flow."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        await flow.async_step_facades({
            "facade_name": "South Wall",
            "facade_direction": "south",
            "add_facade": True,
            "done": False,
        })

        assert len(flow._facades) == 1
        assert flow._facades[0]["name"] == "South Wall"
        assert flow._facades[0]["id"] == "south_wall"
        assert flow._facades[0]["direction"] == "south"

    @pytest.mark.asyncio
    async def test_step_facades_done_proceeds(self) -> None:
        """Test finishing facades step proceeds to covers."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        mock_cover = MagicMock()
        mock_cover.entity_id = "cover.test"
        flow.hass.states.async_all.return_value = [mock_cover]
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        flow._facades = [{"id": "south", "name": "South"}]

        await flow.async_step_facades({
            "add_facade": False,
            "done": True,
        })

        assert flow._data["facades"] == flow._facades

    @pytest.mark.asyncio
    async def test_step_covers_no_covers_aborts(self) -> None:
        """Test covers step aborts when no covers found."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        flow.hass.states.async_all.return_value = []
        flow.async_abort = MagicMock(return_value={"type": "abort", "reason": "no_covers"})

        await flow.async_step_covers(None)

        flow.async_abort.assert_called_once_with(reason="no_covers")


# ---------------------------------------------------------------------------
# OptionsFlow tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_storage():
    """Create mock storage with realistic data."""
    storage = MagicMock()
    storage.covers = {}
    storage.facades = {
        "south": Facade(
            id="south", name="South", azimuth_start=135, azimuth_end=225, direction="south"
        ),
    }
    storage.rules = {
        "sun_shade": Rule(id="sun_shade", name="Sun Shade", enabled=True, priority=10),
    }
    storage.scenarios = {
        "everyday": Scenario(id="everyday", name="Everyday"),
    }
    storage.active_scenario = "everyday"
    storage.outdoor_temp_sensor = None
    storage.indoor_temp_sensor = None
    storage.weather_entity = None
    storage.comfort_temp_min = 21.0
    storage.comfort_temp_max = 25.0
    storage.async_add_facade = AsyncMock()
    storage.async_remove_facade = AsyncMock()
    storage.async_add_rule = AsyncMock()
    storage.async_remove_rule = AsyncMock()
    storage.async_add_scenario = AsyncMock()
    storage.async_remove_scenario = AsyncMock()
    storage.async_save = AsyncMock()
    storage.get_cover_raw = MagicMock(return_value=None)
    return storage


@pytest.fixture
def options_flow(mock_storage):
    """Create OptionsFlow instance with mocked dependencies."""
    flow = CoverAutomaticOptionsFlow()
    flow.hass = MagicMock()

    # Mock config_entry
    mock_entry = MagicMock()
    mock_entry.options = {"scan_interval": 60}
    mock_entry.runtime_data = MagicMock()
    mock_entry.runtime_data.storage = mock_storage

    flow.hass.config_entries.async_entries.return_value = [mock_entry]

    # Set config_entry property (normally provided by HA framework)
    type(flow).config_entry = property(lambda self: mock_entry)

    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

    return flow


class TestOptionsFlowMenu:
    """Tests for OptionsFlow main menu."""

    @pytest.mark.asyncio
    async def test_init_shows_menu(self, options_flow) -> None:
        """Test init step shows the main menu."""
        await options_flow.async_step_init(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_init_navigates_to_general(self, options_flow) -> None:
        """Test menu navigates to general settings."""
        options_flow.async_show_form.return_value = {"type": "form", "step_id": "general"}

        await options_flow.async_step_init({"menu_option": "general"})

        options_flow.async_show_form.assert_called()

    @pytest.mark.asyncio
    async def test_init_navigates_to_facades(self, options_flow) -> None:
        """Test menu navigates to facades management."""
        await options_flow.async_step_init({"menu_option": "facades"})

        options_flow.async_show_form.assert_called()

    @pytest.mark.asyncio
    async def test_init_navigates_to_rules(self, options_flow) -> None:
        """Test menu navigates to rules management."""
        await options_flow.async_step_init({"menu_option": "rules"})

        options_flow.async_show_form.assert_called()

    @pytest.mark.asyncio
    async def test_init_navigates_to_scenarios(self, options_flow) -> None:
        """Test menu navigates to scenarios management."""
        await options_flow.async_step_init({"menu_option": "scenarios"})

        options_flow.async_show_form.assert_called()

    @pytest.mark.asyncio
    async def test_init_navigates_to_cover_details(self, options_flow) -> None:
        """Test menu navigates to cover details."""
        await options_flow.async_step_init({"menu_option": "cover:cover.test"})

        assert options_flow._selected_cover == "cover.test"


class TestOptionsFlowGetStorage:
    """Tests for _get_storage helper."""

    def test_get_storage_returns_storage(self, options_flow, mock_storage) -> None:
        """Test _get_storage returns storage from runtime_data."""
        result = options_flow._get_storage()
        assert result is mock_storage

    def test_get_storage_returns_none_when_no_runtime_data(self) -> None:
        """Test _get_storage returns None when config_entry has no runtime_data."""
        flow = CoverAutomaticOptionsFlow()
        flow.hass = MagicMock()
        mock_entry = MagicMock(spec=[])  # No attributes at all
        with patch.object(type(flow), "config_entry", new_callable=PropertyMock, return_value=mock_entry):
            result = flow._get_storage()
        assert result is None


class TestOptionsFlowFacades:
    """Tests for facade management in OptionsFlow."""

    @pytest.mark.asyncio
    async def test_facade_list_shows_existing(self, options_flow) -> None:
        """Test facades step shows existing facades."""
        await options_flow.async_step_facades(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "facades"

    @pytest.mark.asyncio
    async def test_facade_add_shows_form(self, options_flow) -> None:
        """Test facade_add step shows empty form."""
        await options_flow.async_step_facade_add(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "facade_add"

    @pytest.mark.asyncio
    async def test_facade_add_creates_facade(self, options_flow, mock_storage) -> None:
        """Test adding a new facade."""
        await options_flow.async_step_facade_add({
            "name": "East Wall",
            "direction": "east",
        })

        mock_storage.async_add_facade.assert_called_once()
        facade = mock_storage.async_add_facade.call_args[0][0]
        assert facade.name == "East Wall"
        assert facade.id == "east_wall"
        assert facade.direction == "east"
        assert facade.azimuth_start == FACADE_PRESETS["east"]["start"]
        assert facade.azimuth_end == FACADE_PRESETS["east"]["end"]

    @pytest.mark.asyncio
    async def test_facade_add_empty_name_shows_error(self, options_flow) -> None:
        """Test adding facade with empty name shows error."""
        await options_flow.async_step_facade_add({
            "name": "",
            "direction": "south",
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "name_required"

    @pytest.mark.asyncio
    async def test_facade_add_duplicate_shows_error(self, options_flow, mock_storage) -> None:
        """Test adding facade with duplicate ID shows error."""
        await options_flow.async_step_facade_add({
            "name": "South",
            "direction": "south",
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "already_exists"

    @pytest.mark.asyncio
    async def test_facade_edit_shows_form(self, options_flow) -> None:
        """Test facade_edit step shows form with current values."""
        options_flow._selected_facade = "south"
        await options_flow.async_step_facade_edit(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "facade_edit"

    @pytest.mark.asyncio
    async def test_facade_edit_delete(self, options_flow, mock_storage) -> None:
        """Test deleting a facade."""
        options_flow._selected_facade = "south"
        await options_flow.async_step_facade_edit({"delete": True})

        mock_storage.async_remove_facade.assert_called_once_with("south")

    @pytest.mark.asyncio
    async def test_facade_edit_invalid_azimuth(self, options_flow) -> None:
        """Test editing facade with equal azimuth start/end shows error."""
        options_flow._selected_facade = "south"
        await options_flow.async_step_facade_edit({
            "name": "South",
            "direction": "south",
            "azimuth_start": 180,
            "azimuth_end": 180,
            "min_elevation": 0,
            "delete": False,
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["base"] == "invalid_azimuth_range"

    @pytest.mark.asyncio
    async def test_facade_edit_invalid_id_redirects(self, options_flow) -> None:
        """Test editing nonexistent facade redirects to list."""
        options_flow._selected_facade = "nonexistent"
        await options_flow.async_step_facade_edit(None)

        # Should redirect to facades list
        options_flow.async_show_form.assert_called()


class TestOptionsFlowRules:
    """Tests for rule management in OptionsFlow."""

    @pytest.mark.asyncio
    async def test_rule_list_shows_existing(self, options_flow) -> None:
        """Test rules step shows existing rules."""
        await options_flow.async_step_rules(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "rules"

    @pytest.mark.asyncio
    async def test_rule_add_creates_rule(self, options_flow, mock_storage) -> None:
        """Test adding a new rule."""
        await options_flow.async_step_rule_add({
            "name": "Night Shade",
            "enabled": True,
            "priority": 20,
            "target_position": 0,
        })

        mock_storage.async_add_rule.assert_called_once()
        rule = mock_storage.async_add_rule.call_args[0][0]
        assert rule.name == "Night Shade"
        assert rule.id == "night_shade"
        assert rule.priority == 20
        assert rule.target_position == 0

    @pytest.mark.asyncio
    async def test_rule_add_empty_name_shows_error(self, options_flow) -> None:
        """Test adding rule with empty name shows error."""
        await options_flow.async_step_rule_add({
            "name": "",
            "enabled": True,
            "priority": 10,
            "target_position": 0,
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "name_required"

    @pytest.mark.asyncio
    async def test_rule_add_duplicate_shows_error(self, options_flow, mock_storage) -> None:
        """Test adding rule with duplicate ID shows error."""
        await options_flow.async_step_rule_add({
            "name": "Sun Shade",
            "enabled": True,
            "priority": 10,
            "target_position": 0,
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "already_exists"

    @pytest.mark.asyncio
    async def test_rule_edit_delete(self, options_flow, mock_storage) -> None:
        """Test deleting a rule."""
        options_flow._selected_rule = "sun_shade"
        await options_flow.async_step_rule_edit({
            "delete": True,
            "add_condition": False,
        })

        mock_storage.async_remove_rule.assert_called_once_with("sun_shade")

    @pytest.mark.asyncio
    async def test_rule_edit_update(self, options_flow, mock_storage) -> None:
        """Test updating a rule."""
        options_flow._selected_rule = "sun_shade"
        await options_flow.async_step_rule_edit({
            "name": "Updated Name",
            "enabled": False,
            "priority": 50,
            "condition_operator": "or",
            "target_position": 80,
            "add_condition": False,
            "delete": False,
        })

        mock_storage.async_add_rule.assert_called_once()
        rule = mock_storage.async_add_rule.call_args[0][0]
        assert rule.name == "Updated Name"
        assert rule.enabled is False
        assert rule.priority == 50
        assert rule.condition_operator == "or"
        assert rule.target_position == 80

    @pytest.mark.asyncio
    async def test_rule_condition_add_temperature(self, options_flow, mock_storage) -> None:
        """Test adding a temperature condition to a rule."""
        options_flow._selected_rule = "sun_shade"
        await options_flow.async_step_rule_condition({
            "condition_type": "temperature_above",
            "sensor": "sensor.outdoor_temp",
            "value": 25,
        })

        mock_storage.async_add_rule.assert_called_once()
        rule = mock_storage.async_add_rule.call_args[0][0]
        assert len(rule.conditions) == 1
        assert rule.conditions[0].type.value == "temperature_above"
        assert rule.conditions[0].params["sensor"] == "sensor.outdoor_temp"
        assert rule.conditions[0].params["value"] == 25

    @pytest.mark.asyncio
    async def test_rule_condition_add_time_between(self, options_flow, mock_storage) -> None:
        """Test adding a time_between condition to a rule."""
        options_flow._selected_rule = "sun_shade"
        await options_flow.async_step_rule_condition({
            "condition_type": "time_between",
            "time_start": "09:00",
            "time_end": "18:00",
        })

        mock_storage.async_add_rule.assert_called_once()
        rule = mock_storage.async_add_rule.call_args[0][0]
        assert len(rule.conditions) == 1
        assert rule.conditions[0].type.value == "time_between"
        assert rule.conditions[0].params["start"] == "09:00"
        assert rule.conditions[0].params["end"] == "18:00"

    @pytest.mark.asyncio
    async def test_rule_condition_add_weather(self, options_flow, mock_storage) -> None:
        """Test adding a weather condition to a rule."""
        options_flow._selected_rule = "sun_shade"
        await options_flow.async_step_rule_condition({
            "condition_type": "weather_is",
            "weather_state": "sunny",
        })

        mock_storage.async_add_rule.assert_called_once()
        rule = mock_storage.async_add_rule.call_args[0][0]
        assert rule.conditions[0].type.value == "weather_is"
        assert rule.conditions[0].params["states"] == ["sunny"]

    @pytest.mark.asyncio
    async def test_rule_condition_invalid_type_redirects(self, options_flow) -> None:
        """Test invalid condition type redirects to condition form."""
        options_flow._selected_rule = "sun_shade"
        options_flow.async_show_form.return_value = {"type": "form", "step_id": "rule_condition"}

        await options_flow.async_step_rule_condition({
            "condition_type": "invalid_type",
        })


class TestOptionsFlowScenarios:
    """Tests for scenario management in OptionsFlow."""

    @pytest.mark.asyncio
    async def test_scenario_list_shows_existing(self, options_flow) -> None:
        """Test scenarios step shows existing scenarios."""
        await options_flow.async_step_scenarios(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "scenarios"

    @pytest.mark.asyncio
    async def test_scenario_add_creates_scenario(self, options_flow, mock_storage) -> None:
        """Test adding a new scenario."""
        await options_flow.async_step_scenario_add({
            "name": "Vacation",
            "icon": "mdi:beach",
        })

        mock_storage.async_add_scenario.assert_called_once()
        scenario = mock_storage.async_add_scenario.call_args[0][0]
        assert scenario.name == "Vacation"
        assert scenario.id == "vacation"
        assert scenario.icon == "mdi:beach"

    @pytest.mark.asyncio
    async def test_scenario_add_empty_name_shows_error(self, options_flow) -> None:
        """Test adding scenario with empty name shows error."""
        await options_flow.async_step_scenario_add({
            "name": "",
            "icon": "mdi:home",
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "name_required"

    @pytest.mark.asyncio
    async def test_scenario_add_duplicate_shows_error(self, options_flow, mock_storage) -> None:
        """Test adding scenario with duplicate ID shows error."""
        await options_flow.async_step_scenario_add({
            "name": "Everyday",
            "icon": "mdi:home",
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["name"] == "already_exists"

    @pytest.mark.asyncio
    async def test_scenario_edit_delete(self, options_flow, mock_storage) -> None:
        """Test deleting a scenario recreates default when none left."""
        # Make mock actually remove the scenario from the dict
        async def remove_scenario(sid):
            mock_storage.scenarios.pop(sid, None)
        mock_storage.async_remove_scenario = AsyncMock(side_effect=remove_scenario)

        options_flow._selected_scenario = "everyday"
        await options_flow.async_step_scenario_edit({
            "delete": True,
            "activate": False,
        })

        mock_storage.async_remove_scenario.assert_called_once_with("everyday")
        # Since no scenarios remain, a default should be recreated
        mock_storage.async_add_scenario.assert_called_once()

    @pytest.mark.asyncio
    async def test_scenario_edit_activate(self, options_flow, mock_storage) -> None:
        """Test activating a scenario."""
        mock_storage.scenarios["summer"] = Scenario(id="summer", name="Summer")
        options_flow._selected_scenario = "summer"

        await options_flow.async_step_scenario_edit({
            "activate": True,
            "delete": False,
        })

        assert mock_storage.active_scenario == "summer"
        mock_storage.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_scenario_edit_update(self, options_flow, mock_storage) -> None:
        """Test updating a scenario."""
        options_flow._selected_scenario = "everyday"
        await options_flow.async_step_scenario_edit({
            "name": "Daily Routine",
            "icon": "mdi:calendar",
            "rules_disabled": ["sun_shade"],
            "activate": False,
            "delete": False,
        })

        mock_storage.async_add_scenario.assert_called_once()
        scenario = mock_storage.async_add_scenario.call_args[0][0]
        assert scenario.name == "Daily Routine"
        assert scenario.icon == "mdi:calendar"
        assert scenario.rules_disabled == ["sun_shade"]


class TestOptionsFlowGeneral:
    """Tests for general settings in OptionsFlow."""

    @pytest.mark.asyncio
    async def test_general_shows_form(self, options_flow) -> None:
        """Test general step shows form with current values."""
        await options_flow.async_step_general(None)

        options_flow.async_show_form.assert_called_once()
        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["step_id"] == "general"

    @pytest.mark.asyncio
    async def test_general_saves_settings(self, options_flow, mock_storage) -> None:
        """Test general settings are saved correctly."""
        await options_flow.async_step_general({
            "scan_interval": 120,
            "outdoor_temp_sensor": "sensor.temp_outside",
            "indoor_temp_sensor": "sensor.temp_inside",
            "weather_entity": "weather.home",
            "comfort_temp_min": 20.0,
            "comfort_temp_max": 26.0,
        })

        assert mock_storage.outdoor_temp_sensor == "sensor.temp_outside"
        assert mock_storage.indoor_temp_sensor == "sensor.temp_inside"
        assert mock_storage.weather_entity == "weather.home"
        mock_storage.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_comfort_temp_validation(self, options_flow) -> None:
        """Test comfort temperature min must be less than max."""
        await options_flow.async_step_general({
            "scan_interval": 60,
            "comfort_temp_min": 25.0,
            "comfort_temp_max": 20.0,
        })

        call_kwargs = options_flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["comfort_temp_min"] == "min_must_be_less_than_max"


class TestOptionsFlowCoverDetails:
    """Tests for cover detail settings in OptionsFlow."""

    @pytest.mark.asyncio
    async def test_cover_details_no_storage_redirects(self, options_flow) -> None:
        """Test cover details redirects when no storage available."""
        options_flow._selected_cover = None
        options_flow.async_show_form.return_value = {"type": "form", "step_id": "init"}

        await options_flow.async_step_cover_details(None)

    @pytest.mark.asyncio
    async def test_cover_details_saves_settings(self, options_flow, mock_storage) -> None:
        """Test cover detail settings are saved."""
        mock_storage.get_cover_raw.return_value = {
            "entity_id": "cover.test",
            "name": "Test Cover",
            "facade_id": None,
        }
        mock_storage._cache_covers = {"cover.test": MagicMock()}
        options_flow._selected_cover = "cover.test"

        # Mock coordinator for refresh, keep same storage reference
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.storage = mock_storage
        mock_entry.runtime_data.coordinator = MagicMock()
        mock_entry.runtime_data.coordinator.refresh_state_tracking = MagicMock()
        options_flow.hass.config_entries.async_entries.return_value = [mock_entry]

        await options_flow.async_step_cover_details({
            "facade_id": "south",
            "lock_sensor": "binary_sensor.window",
            "lock_position": 100,
            "vent_sensor": None,
            "vent_position": 30,
            "inverted": True,
            "min_position_change": 10,
            "min_time_between_changes": 600,
            "pause_duration": 180,
        })

        cover_raw = mock_storage.get_cover_raw.return_value
        assert cover_raw["facade_id"] == "south"
        assert cover_raw["lock_sensor"] == "binary_sensor.window"
        assert cover_raw["inverted"] is True
        assert cover_raw["min_position_change"] == 10
        assert cover_raw["pause_duration"] == 180
        mock_storage.async_save.assert_called_once()
