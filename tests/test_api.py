"""Tests for CoverAutomatic WebSocket API."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.api import (
    _build_config_response,
    _parse_conditions,
    _sanitize_id,
    _unique_id,
    async_setup_api,
)
from custom_components.cover_automatic.models import (
    Condition,
    ConditionType,
    CoverConfig,
    Facade,
    Rule,
    Scenario,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_storage(
    *,
    facades: dict | None = None,
    covers: dict | None = None,
    rules: dict | None = None,
    scenarios: dict | None = None,
    enabled: bool = True,
    active_scenario: str = "everyday",
    outdoor_temp_sensor: str | None = None,
    indoor_temp_sensor: str | None = None,
    weather_entity: str | None = None,
    comfort_temp_min: float = 21.0,
    comfort_temp_max: float = 25.0,
    comfort_hysteresis: float = 1.0,
    wind_sensor: str | None = None,
    wind_speed_threshold: float = 0.0,
    wind_speed_hysteresis: float = 0.0,
    solar_sensor: str | None = None,
    solar_threshold: float = 0.0,
) -> MagicMock:
    """Create a mock storage object."""
    storage = MagicMock()
    storage.facades = facades or {}
    storage.covers = covers or {}
    storage.rules = rules or {}
    storage.scenarios = scenarios or {}
    storage.enabled = enabled
    storage.active_scenario = active_scenario
    storage.outdoor_temp_sensor = outdoor_temp_sensor
    storage.indoor_temp_sensor = indoor_temp_sensor
    storage.weather_entity = weather_entity
    storage.comfort_temp_min = comfort_temp_min
    storage.comfort_temp_max = comfort_temp_max
    storage.comfort_hysteresis = comfort_hysteresis
    storage.wind_sensor = wind_sensor
    storage.wind_speed_threshold = wind_speed_threshold
    storage.wind_speed_hysteresis = wind_speed_hysteresis
    storage.solar_sensor = solar_sensor
    storage.solar_threshold = solar_threshold
    storage.lock_tilt_position = None
    storage.vent_tilt_position = None
    storage.command_stagger = 0.0
    storage.logbook_enabled = True
    storage.async_add_facade = AsyncMock()
    storage.async_remove_facade = AsyncMock()
    storage.async_add_cover = AsyncMock()
    storage.async_remove_cover = AsyncMock()
    storage.async_add_rule = AsyncMock()
    storage.async_remove_rule = AsyncMock()
    storage.async_add_scenario = AsyncMock()
    storage.async_remove_scenario = AsyncMock()
    storage.async_save = AsyncMock()
    storage._invalidate_cache = MagicMock()
    storage._data = {
        "facades": {},
        "covers": {},
        "rules": {},
        "scenarios": {},
    }
    storage.get_cover_raw = MagicMock(return_value=None)
    return storage


def _make_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.refresh_state_tracking = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.get_active_rules = MagicMock(return_value={})
    coordinator.get_live_cover_data = MagicMock(return_value={})
    coordinator.get_live_facade_data = MagicMock(return_value={})
    coordinator.log_storage = None
    return coordinator


def _make_connection() -> MagicMock:
    """Create a mock WebSocket connection."""
    connection = MagicMock()
    connection.send_result = MagicMock()
    connection.send_error = MagicMock()
    return connection


def _make_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    return hass


# ---------------------------------------------------------------------------
# _sanitize_id
# ---------------------------------------------------------------------------

class TestSanitizeId:
    """Tests for ID sanitization."""

    def test_simple_name(self) -> None:
        assert _sanitize_id("living room") == "living_room"

    def test_uppercase(self) -> None:
        assert _sanitize_id("My Facade") == "my_facade"

    def test_umlaut_replacement(self) -> None:
        assert _sanitize_id("Küche Süd") == "kueche_sued"

    def test_sz_replacement(self) -> None:
        assert _sanitize_id("Straße") == "strasse"

    def test_uppercase_umlauts(self) -> None:
        assert _sanitize_id("Über Öffnung Ähre") == "ueber_oeffnung_aehre"

    def test_special_characters_replaced(self) -> None:
        # Trailing underscores are stripped
        assert _sanitize_id("test@#$%") == "test"

    def test_consecutive_underscores_collapsed(self) -> None:
        assert _sanitize_id("a - b - c") == "a_b_c"

    def test_leading_trailing_underscores_stripped(self) -> None:
        assert _sanitize_id("  test  ") == "test"

    def test_empty_string_fallback(self) -> None:
        result = _sanitize_id("!!!!")
        assert result == "unnamed"


# ---------------------------------------------------------------------------
# _parse_conditions
# ---------------------------------------------------------------------------

class TestParseConditions:
    """Tests for condition parsing."""

    def test_valid_conditions_no_errors(self) -> None:
        raw = [
            {"type": "sun_on_facade", "params": {"facade_id": "s1"}},
            {"type": "temperature_above", "params": {"threshold": 25}},
        ]
        conditions, errors = _parse_conditions(raw)
        assert len(conditions) == 2
        assert errors == []

    def test_invalid_condition_returns_errors(self) -> None:
        raw = [
            {"type": "sun_on_facade", "params": {"facade_id": "s1"}},
            {"type": "INVALID", "params": {}},
        ]
        conditions, errors = _parse_conditions(raw)
        assert len(conditions) == 1
        assert len(errors) == 1
        assert "Condition 1" in errors[0]

    def test_all_invalid_returns_empty_conditions(self) -> None:
        raw = [
            {"type": "BOGUS", "params": {}},
            {"type": "ALSO_BOGUS", "params": {}},
        ]
        conditions, errors = _parse_conditions(raw)
        assert len(conditions) == 0
        assert len(errors) == 2

    def test_empty_input_returns_empty(self) -> None:
        conditions, errors = _parse_conditions([])
        assert conditions == []
        assert errors == []


# ---------------------------------------------------------------------------
# _build_config_response
# ---------------------------------------------------------------------------

class TestBuildConfigResponse:
    """Tests for config response builder."""

    def test_empty_config(self) -> None:
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["covers"] == {}
        assert result["facades"] == {}
        assert result["rules"] == {}
        assert result["scenarios"] == {}
        assert result["settings"]["active_scenario"] == "everyday"

    def test_with_data(self) -> None:
        facade = Facade(id="south_1", name="South", azimuth_start=135, azimuth_end=225)
        cover = CoverConfig(entity_id="cover.test", name="Test Cover")
        rule = Rule(id="r1", name="Rule 1")
        scenario = Scenario(id="everyday", name="Everyday")
        storage = _make_storage(
            facades={"south_1": facade},
            covers={"cover.test": cover},
            rules={"r1": rule},
            scenarios={"everyday": scenario},
            outdoor_temp_sensor="sensor.temp",
            comfort_temp_min=20.0,
            comfort_temp_max=26.0,
        )
        result = _build_config_response(storage)
        assert "south_1" in result["facades"]
        assert "cover.test" in result["covers"]
        assert "r1" in result["rules"]
        assert "everyday" in result["scenarios"]
        assert result["settings"]["outdoor_temp_sensor"] == "sensor.temp"
        assert result["settings"]["comfort_temp_min"] == 20.0
        assert result["settings"]["comfort_temp_max"] == 26.0

    def test_wind_settings_in_response(self) -> None:
        storage = _make_storage(
            wind_sensor="sensor.wind_speed",
            wind_speed_threshold=50.0,
            wind_speed_hysteresis=10.0,
        )
        result = _build_config_response(storage)
        assert result["settings"]["wind_sensor"] == "sensor.wind_speed"
        assert result["settings"]["wind_speed_threshold"] == 50.0
        assert result["settings"]["wind_speed_hysteresis"] == 10.0

    def test_wind_settings_defaults(self) -> None:
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["settings"]["wind_sensor"] is None
        assert result["settings"]["wind_speed_threshold"] == 0.0
        assert result["settings"]["wind_speed_hysteresis"] == 0.0

    def test_solar_settings_in_response(self) -> None:
        storage = _make_storage(
            solar_sensor="sensor.solar_radiation",
            solar_threshold=200.0,
        )
        result = _build_config_response(storage)
        assert result["settings"]["solar_sensor"] == "sensor.solar_radiation"
        assert result["settings"]["solar_threshold"] == 200.0

    def test_solar_settings_defaults(self) -> None:
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["settings"]["solar_sensor"] is None
        assert result["settings"]["solar_threshold"] == 0.0

    def test_comfort_hysteresis_in_response(self) -> None:
        storage = _make_storage(comfort_hysteresis=1.5)
        result = _build_config_response(storage)
        assert result["settings"]["comfort_hysteresis"] == 1.5

    def test_comfort_hysteresis_default(self) -> None:
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["settings"]["comfort_hysteresis"] == 1.0

    def test_enabled_default_true(self) -> None:
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["enabled"] is True

    def test_enabled_false(self) -> None:
        storage = _make_storage()
        storage.enabled = False
        result = _build_config_response(storage)
        assert result["enabled"] is False


# ---------------------------------------------------------------------------
# async_setup_api
# ---------------------------------------------------------------------------

class TestApiSetup:
    """Tests for API registration."""

    def test_registers_all_commands(self) -> None:
        hass = _make_hass()
        storage = _make_storage()
        coordinator = _make_coordinator()

        # 13 commands total
        from homeassistant.components import websocket_api as real_ws

        with patch(
            "custom_components.cover_automatic.api.websocket_api"
        ) as mock_ws:
            mock_ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA
            async_setup_api(hass, storage, coordinator)
            assert mock_ws.async_register_command.call_count == 20

    def test_command_names_registered(self) -> None:
        hass = _make_hass()
        storage = _make_storage()
        coordinator = _make_coordinator()

        from homeassistant.components import websocket_api as real_ws

        registered_schemas = []
        with patch(
            "custom_components.cover_automatic.api.websocket_api"
        ) as mock_ws:
            mock_ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA

            def capture_register(hass, command_type, handler=None, schema=None):
                # async_register_command(hass, command_type, handler, schema)
                registered_schemas.append(schema)

            mock_ws.async_register_command.side_effect = capture_register
            async_setup_api(hass, storage, coordinator)

        assert len(registered_schemas) == 20


# ---------------------------------------------------------------------------
# WS Handler Tests
# ---------------------------------------------------------------------------

class TestWsGetConfig:
    """Tests for cover_automatic/config handler."""

    @pytest.mark.asyncio
    async def test_returns_full_config(self) -> None:
        from custom_components.cover_automatic.api import ws_get_config

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        msg = {"id": 1, "type": "cover_automatic/config"}

        await ws_get_config(hass, conn, msg, storage, coordinator)

        conn.send_result.assert_called_once()
        result = conn.send_result.call_args[0]
        assert result[0] == 1
        assert "covers" in result[1]
        assert "facades" in result[1]
        assert "rules" in result[1]
        assert "scenarios" in result[1]
        assert "settings" in result[1]
        assert "active_rules" in result[1]

    @pytest.mark.asyncio
    async def test_active_rules_from_coordinator(self) -> None:
        from custom_components.cover_automatic.api import ws_get_config

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        coordinator.get_active_rules.return_value = {"rule1": ["cover.a"]}
        msg = {"id": 1, "type": "cover_automatic/config"}

        await ws_get_config(hass, conn, msg, storage, coordinator)

        result = conn.send_result.call_args[0][1]
        assert result["active_rules"] == {"rule1": ["cover.a"]}


class TestWsCoverUpdate:
    """Tests for cover_automatic/cover/update handler."""

    @pytest.mark.asyncio
    async def test_update_existing_cover(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        raw_cover = {
            "entity_id": "cover.test",
            "name": "Test",
            "facade_id": None,
            "auto_enabled": True,
            "pause_duration": 120,
        }
        storage.get_cover_raw = MagicMock(return_value=raw_cover)

        msg = {
            "id": 1,
            "type": "cover_automatic/cover/update",
            "entity_id": "cover.test",
            "facade_id": "south_1",
            "pause_duration": 60,
        }

        await ws_cover_update(hass, conn, msg, storage, coordinator)

        # Verify raw dict was updated
        assert raw_cover["facade_id"] == "south_1"
        assert raw_cover["pause_duration"] == 60
        storage._invalidate_cache.assert_called()
        storage.async_save.assert_awaited_once()
        coordinator.refresh_state_tracking.assert_called_once()
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_unknown_cover_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        storage.get_cover_raw = MagicMock(return_value=None)

        msg = {
            "id": 1,
            "type": "cover_automatic/cover/update",
            "entity_id": "cover.unknown",
        }

        await ws_cover_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()
        assert "not_found" in conn.send_error.call_args[0][1]


class TestWsCoverAdd:
    """Tests for cover_automatic/cover/add handler."""

    @pytest.mark.asyncio
    async def test_add_multiple_covers_saves_once(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        state1 = MagicMock()
        state1.attributes = {"friendly_name": "Cover 1"}
        state2 = MagicMock()
        state2.attributes = {"friendly_name": "Cover 2"}
        hass.states.get = MagicMock(side_effect=lambda eid: {
            "cover.one": state1,
            "cover.two": state2,
        }.get(eid))

        msg = {
            "id": 1,
            "type": "cover_automatic/cover/add",
            "entity_ids": ["cover.one", "cover.two"],
        }

        await ws_cover_add(hass, conn, msg, storage, coordinator)

        assert storage.async_add_cover.await_count == 2
        # save=False on each call, then one explicit save
        for call in storage.async_add_cover.call_args_list:
            assert call.kwargs.get("save") is False
        storage.async_save.assert_awaited_once()
        conn.send_result.assert_called_once()


class TestWsFacadeAdd:
    """Tests for cover_automatic/facade/add handler."""

    @pytest.mark.asyncio
    async def test_add_facade_south(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/facade/add",
            "name": "Süd Fassade",
            "direction": "south",
        }

        await ws_facade_add(hass, conn, msg, storage, coordinator)

        storage.async_add_facade.assert_awaited_once()
        facade_arg = storage.async_add_facade.call_args[0][0]
        assert isinstance(facade_arg, Facade)
        assert facade_arg.id == "sued_fassade"
        assert facade_arg.direction == "south"
        assert facade_arg.azimuth_start == 135
        assert facade_arg.azimuth_end == 225
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_facade_with_custom_azimuth(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/facade/add",
            "name": "Custom",
            "direction": "east",
            "azimuth_start": 50,
            "azimuth_end": 140,
        }

        await ws_facade_add(hass, conn, msg, storage, coordinator)

        facade_arg = storage.async_add_facade.call_args[0][0]
        assert facade_arg.azimuth_start == 50
        assert facade_arg.azimuth_end == 140


class TestWsFacadeUpdate:
    """Tests for cover_automatic/facade/update handler."""

    @pytest.mark.asyncio
    async def test_update_existing_facade(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_update

        hass = _make_hass()
        conn = _make_connection()
        facade = Facade(id="south_1", name="South", azimuth_start=135, azimuth_end=225)
        storage = _make_storage(facades={"south_1": facade})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/facade/update",
            "facade_id": "south_1",
            "name": "South Updated",
            "azimuth_start": 130,
        }

        await ws_facade_update(hass, conn, msg, storage, coordinator)

        storage.async_add_facade.assert_awaited_once()
        updated = storage.async_add_facade.call_args[0][0]
        assert updated.name == "South Updated"
        assert updated.azimuth_start == 130
        assert updated.azimuth_end == 225  # unchanged

    @pytest.mark.asyncio
    async def test_update_unknown_facade_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/facade/update",
            "facade_id": "unknown",
        }

        await ws_facade_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsFacadeDelete:
    """Tests for cover_automatic/facade/delete handler."""

    @pytest.mark.asyncio
    async def test_delete_existing_facade(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_delete

        hass = _make_hass()
        conn = _make_connection()
        facade = Facade(id="south_1", name="South", azimuth_start=135, azimuth_end=225)
        storage = _make_storage(facades={"south_1": facade})
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/facade/delete", "facade_id": "south_1"}

        await ws_facade_delete(hass, conn, msg, storage, coordinator)

        storage.async_remove_facade.assert_awaited_once_with("south_1")
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_unknown_facade_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_facade_delete

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/facade/delete", "facade_id": "nope"}

        await ws_facade_delete(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsRuleAdd:
    """Tests for cover_automatic/rule/add handler."""

    @pytest.mark.asyncio
    async def test_add_rule_with_conditions(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/add",
            "name": "Sun Protection",
            "enabled": True,
            "priority": 50,
            "condition_operator": "and",
            "facade_ids": ["south_1"],
            "cover_ids": [],
            "target_position": 20,
            "target_tilt_position": 50,
            "conditions": [
                {"type": "sun_on_facade", "params": {"facade_id": "south_1"}},
                {"type": "temperature_above", "params": {"threshold": 25}},
            ],
        }

        await ws_rule_add(hass, conn, msg, storage, coordinator)

        storage.async_add_rule.assert_awaited_once()
        rule_arg = storage.async_add_rule.call_args[0][0]
        assert isinstance(rule_arg, Rule)
        assert rule_arg.name == "Sun Protection"
        assert rule_arg.priority == 50
        assert len(rule_arg.conditions) == 2

    @pytest.mark.asyncio
    async def test_add_rule_rejects_invalid_conditions(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/add",
            "name": "Test Rule",
            "conditions": [
                {"type": "sun_on_facade", "params": {"facade_id": "s1"}},
                {"type": "INVALID_TYPE", "params": {}},  # invalid
            ],
        }

        await ws_rule_add(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()
        assert "invalid_conditions" in conn.send_error.call_args[0][1]
        storage.async_add_rule.assert_not_awaited()


class TestWsRuleUpdate:
    """Tests for cover_automatic/rule/update handler."""

    @pytest.mark.asyncio
    async def test_update_existing_rule(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        hass = _make_hass()
        conn = _make_connection()
        rule = Rule(id="r1", name="Old Name", priority=10)
        storage = _make_storage(rules={"r1": rule})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/update",
            "rule_id": "r1",
            "name": "New Name",
            "priority": 99,
        }

        await ws_rule_update(hass, conn, msg, storage, coordinator)

        storage.async_add_rule.assert_awaited_once()
        updated = storage.async_add_rule.call_args[0][0]
        assert updated.name == "New Name"
        assert updated.priority == 99

    @pytest.mark.asyncio
    async def test_update_rule_conditions(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        hass = _make_hass()
        conn = _make_connection()
        rule = Rule(id="r1", name="Rule", conditions=[
            Condition(type=ConditionType.SUN_ON_FACADE, params={"facade_id": "s1"}),
        ])
        storage = _make_storage(rules={"r1": rule})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/update",
            "rule_id": "r1",
            "conditions": [
                {"type": "temperature_above", "params": {"threshold": 30}},
            ],
        }

        await ws_rule_update(hass, conn, msg, storage, coordinator)

        updated = storage.async_add_rule.call_args[0][0]
        assert len(updated.conditions) == 1
        assert updated.conditions[0].type == ConditionType.TEMPERATURE_ABOVE

    @pytest.mark.asyncio
    async def test_update_rule_rejects_invalid_conditions(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        hass = _make_hass()
        conn = _make_connection()
        rule = Rule(id="r1", name="Rule", conditions=[
            Condition(type=ConditionType.SUN_ON_FACADE, params={"facade_id": "s1"}),
        ])
        storage = _make_storage(rules={"r1": rule})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/update",
            "rule_id": "r1",
            "conditions": [
                {"type": "BOGUS", "params": {}},
            ],
        }

        await ws_rule_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()
        assert "invalid_conditions" in conn.send_error.call_args[0][1]
        storage.async_add_rule.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_unknown_rule_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/rule/update", "rule_id": "nope"}

        await ws_rule_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsRuleDelete:
    """Tests for cover_automatic/rule/delete handler."""

    @pytest.mark.asyncio
    async def test_delete_existing_rule(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_delete

        hass = _make_hass()
        conn = _make_connection()
        rule = Rule(id="r1", name="Rule")
        storage = _make_storage(rules={"r1": rule})
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/rule/delete", "rule_id": "r1"}

        await ws_rule_delete(hass, conn, msg, storage, coordinator)

        storage.async_remove_rule.assert_awaited_once_with("r1")
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_unknown_rule_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_delete

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/rule/delete", "rule_id": "nope"}

        await ws_rule_delete(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsRuleReorder:
    """Tests for cover_automatic/rule/reorder handler."""

    @pytest.mark.asyncio
    async def test_reorder_sets_priorities(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_reorder

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        storage._data = {
            "rules": {
                "r1": {"id": "r1", "name": "A", "priority": 10},
                "r2": {"id": "r2", "name": "B", "priority": 20},
                "r3": {"id": "r3", "name": "C", "priority": 30},
            },
            "facades": {},
            "covers": {},
            "scenarios": {},
        }

        msg = {
            "id": 1,
            "type": "cover_automatic/rule/reorder",
            "rule_ids": ["r3", "r1", "r2"],
        }

        await ws_rule_reorder(hass, conn, msg, storage, coordinator)

        assert storage._data["rules"]["r3"]["priority"] == 30
        assert storage._data["rules"]["r1"]["priority"] == 20
        assert storage._data["rules"]["r2"]["priority"] == 10
        storage._invalidate_cache.assert_called()
        storage.async_save.assert_awaited_once()
        conn.send_result.assert_called_once()


class TestWsScenarioAdd:
    """Tests for cover_automatic/scenario/add handler."""

    @pytest.mark.asyncio
    async def test_add_scenario(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_add

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/scenario/add",
            "name": "Urlaub",
            "icon": "mdi:beach",
            "rules_disabled": ["r1"],
        }

        await ws_scenario_add(hass, conn, msg, storage, coordinator)

        storage.async_add_scenario.assert_awaited_once()
        scenario_arg = storage.async_add_scenario.call_args[0][0]
        assert isinstance(scenario_arg, Scenario)
        assert scenario_arg.id == "urlaub"
        assert scenario_arg.icon == "mdi:beach"
        assert scenario_arg.rules_disabled == ["r1"]


class TestWsScenarioUpdate:
    """Tests for cover_automatic/scenario/update handler."""

    @pytest.mark.asyncio
    async def test_update_existing_scenario(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_update

        hass = _make_hass()
        conn = _make_connection()
        scenario = Scenario(id="holiday", name="Holiday", icon="mdi:beach")
        storage = _make_storage(scenarios={"holiday": scenario})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/scenario/update",
            "scenario_id": "holiday",
            "name": "Vacation",
            "icon": "mdi:airplane",
        }

        await ws_scenario_update(hass, conn, msg, storage, coordinator)

        storage.async_add_scenario.assert_awaited_once()
        updated = storage.async_add_scenario.call_args[0][0]
        assert updated.name == "Vacation"
        assert updated.icon == "mdi:airplane"

    @pytest.mark.asyncio
    async def test_update_scenario_activates(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_update

        hass = _make_hass()
        conn = _make_connection()
        scenario = Scenario(id="holiday", name="Holiday")
        storage = _make_storage(scenarios={"holiday": scenario})
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/scenario/update",
            "scenario_id": "holiday",
            "activate": True,
        }

        await ws_scenario_update(hass, conn, msg, storage, coordinator)

        assert storage.active_scenario == "holiday"

    @pytest.mark.asyncio
    async def test_update_unknown_scenario_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/scenario/update",
            "scenario_id": "nope",
        }

        await ws_scenario_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsScenarioDelete:
    """Tests for cover_automatic/scenario/delete handler."""

    @pytest.mark.asyncio
    async def test_delete_existing_scenario(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_delete

        hass = _make_hass()
        conn = _make_connection()
        scenario = Scenario(id="holiday", name="Holiday")
        storage = _make_storage(scenarios={"holiday": scenario})
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/scenario/delete", "scenario_id": "holiday"}

        await ws_scenario_delete(hass, conn, msg, storage, coordinator)

        storage.async_remove_scenario.assert_awaited_once_with("holiday")
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_unknown_scenario_sends_error(self) -> None:
        from custom_components.cover_automatic.api import ws_scenario_delete

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {"id": 1, "type": "cover_automatic/scenario/delete", "scenario_id": "nope"}

        await ws_scenario_delete(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()


class TestWsSettingsUpdate:
    """Tests for cover_automatic/settings/update handler."""

    @pytest.mark.asyncio
    async def test_update_sensors(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/settings/update",
            "outdoor_temp_sensor": "sensor.outdoor",
            "indoor_temp_sensor": "sensor.indoor",
            "weather_entity": "weather.home",
        }

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        assert storage.outdoor_temp_sensor == "sensor.outdoor"
        assert storage.indoor_temp_sensor == "sensor.indoor"
        assert storage.weather_entity == "weather.home"
        storage.async_save.assert_awaited_once()
        coordinator.refresh_state_tracking.assert_called_once()
        coordinator.async_request_refresh.assert_awaited_once()
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_comfort_temps(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/settings/update",
            "comfort_temp_min": 19.5,
            "comfort_temp_max": 27.0,
        }

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        assert storage.comfort_temp_min == 19.5
        assert storage.comfort_temp_max == 27.0

    @pytest.mark.asyncio
    async def test_partial_update(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage(outdoor_temp_sensor="sensor.old")
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/settings/update",
            "comfort_temp_min": 18.0,
        }

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        assert storage.comfort_temp_min == 18.0
        # outdoor_temp_sensor not in msg, should not be changed
        # (we check it wasn't overwritten by verifying send_result was called)
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_enabled(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()

        msg = {
            "id": 1,
            "type": "cover_automatic/settings/update",
            "enabled": False,
        }

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        assert storage.enabled is False
        storage.async_save.assert_awaited_once()
        conn.send_result.assert_called_once()


# ---------------------------------------------------------------------------
# _unique_id
# ---------------------------------------------------------------------------

class TestUniqueId:
    """Tests for _unique_id."""

    def test_returns_base_when_no_collision(self):
        assert _unique_id("test", {}) == "test"

    def test_appends_suffix_on_collision(self):
        existing = {"test": {}}
        assert _unique_id("test", existing) == "test_2"

    def test_increments_suffix_on_multiple_collisions(self):
        existing = {"test": {}, "test_2": {}, "test_3": {}}
        assert _unique_id("test", existing) == "test_4"


# ---------------------------------------------------------------------------
# Global tilt defaults in config response
# ---------------------------------------------------------------------------

class TestConfigResponseTiltDefaults:
    """Tests for tilt defaults in config response."""

    def test_tilt_defaults_in_settings(self):
        storage = _make_storage()
        storage.lock_tilt_position = 50
        storage.vent_tilt_position = 80
        result = _build_config_response(storage)
        assert result["settings"]["lock_tilt_position"] == 50
        assert result["settings"]["vent_tilt_position"] == 80

    def test_tilt_defaults_none(self):
        storage = _make_storage()
        result = _build_config_response(storage)
        assert result["settings"]["lock_tilt_position"] is None
        assert result["settings"]["vent_tilt_position"] is None


class TestWsExportConfig:
    """Tests for cover_automatic/export handler."""

    @pytest.mark.asyncio
    async def test_export_returns_raw_data(self) -> None:
        from custom_components.cover_automatic.api import ws_export_config

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        raw = {"facades": {}, "covers": {}, "rules": {}}
        storage.get_raw_data.return_value = raw
        msg = {"id": 1, "type": "cover_automatic/export"}

        await ws_export_config(hass, conn, msg, storage, coordinator)

        conn.send_result.assert_called_once_with(1, {"data": raw})


class TestWsImportConfig:
    """Tests for cover_automatic/import handler."""

    @pytest.mark.asyncio
    async def test_import_success(self) -> None:
        from custom_components.cover_automatic.api import ws_import_config

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        coordinator.async_request_refresh = AsyncMock()
        storage.async_import_data = AsyncMock()
        data = {"facades": {}, "covers": {}, "rules": {}, "scenarios": {}}
        msg = {"id": 1, "type": "cover_automatic/import", "data": data}

        await ws_import_config(hass, conn, msg, storage, coordinator)

        storage.async_import_data.assert_called_once_with(data)
        coordinator.refresh_state_tracking.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()
        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_invalid_data(self) -> None:
        from custom_components.cover_automatic.api import ws_import_config

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        storage.async_import_data = AsyncMock(side_effect=ValueError("bad data"))
        msg = {"id": 1, "type": "cover_automatic/import", "data": {"bad": True}}

        await ws_import_config(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once_with(1, "invalid_data", "bad data")
        coordinator.refresh_state_tracking.assert_not_called()


class TestWsClearLog:
    """Tests for cover_automatic/log/clear WebSocket command."""

    @pytest.mark.asyncio
    async def test_clear_log_with_storage(self) -> None:
        from custom_components.cover_automatic.api import ws_clear_log

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        coordinator.log_storage = MagicMock()
        coordinator.log_storage.async_clear = AsyncMock()
        msg = {"id": 1, "type": "cover_automatic/log/clear"}

        await ws_clear_log(hass, conn, msg, storage, coordinator)

        coordinator.log_storage.async_clear.assert_called_once()
        conn.send_result.assert_called_once_with(1, {"success": True})

    @pytest.mark.asyncio
    async def test_clear_log_without_storage(self) -> None:
        from custom_components.cover_automatic.api import ws_clear_log

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        coordinator.log_storage = None
        msg = {"id": 1, "type": "cover_automatic/log/clear"}

        await ws_clear_log(hass, conn, msg, storage, coordinator)

        conn.send_result.assert_called_once_with(1, {"success": True})


class TestSettingsValidation:
    """Tests for settings update validation."""

    @pytest.mark.asyncio
    async def test_active_scenario_rejects_nonexistent(self) -> None:
        """Test that setting a non-existent scenario is rejected."""
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        storage._data["scenarios"] = {"everyday": {"name": "Everyday"}}
        coordinator = _make_coordinator()
        msg = {"id": 1, "type": "cover_automatic/settings/update", "active_scenario": "nonexistent"}

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        conn.send_error.assert_called_once()
        assert "not_found" in conn.send_error.call_args[0]

    @pytest.mark.asyncio
    async def test_active_scenario_accepts_existing(self) -> None:
        """Test that setting an existing scenario works."""
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        storage._data["scenarios"] = {"everyday": {"name": "Everyday"}, "night": {"name": "Night"}}
        coordinator = _make_coordinator()
        msg = {"id": 1, "type": "cover_automatic/settings/update", "active_scenario": "night"}

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_active_scenario_accepts_empty_string(self) -> None:
        """Test that clearing the scenario (empty string = falsy) is accepted."""
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        storage._data["scenarios"] = {}
        coordinator = _make_coordinator()
        msg = {"id": 1, "type": "cover_automatic/settings/update", "active_scenario": ""}

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        conn.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_stagger_in_config_response(self) -> None:
        """Test that command_stagger appears in config response."""
        from custom_components.cover_automatic.api import _build_config_response

        storage = _make_storage()
        storage.command_stagger = 0.5

        result = _build_config_response(storage)

        assert result["settings"]["command_stagger"] == 0.5

    @pytest.mark.asyncio
    async def test_logbook_enabled_in_config_response(self) -> None:
        """Test that logbook_enabled appears in config response."""
        from custom_components.cover_automatic.api import _build_config_response

        storage = _make_storage()
        storage.logbook_enabled = False

        result = _build_config_response(storage)

        assert result["settings"]["logbook_enabled"] is False

    @pytest.mark.asyncio
    async def test_logbook_enabled_update_persists(self) -> None:
        """Test that logbook_enabled update is written to storage."""
        from custom_components.cover_automatic.api import ws_settings_update

        hass = _make_hass()
        conn = _make_connection()
        storage = _make_storage()
        coordinator = _make_coordinator()
        msg = {
            "id": 1,
            "type": "cover_automatic/settings/update",
            "logbook_enabled": False,
        }

        await ws_settings_update(hass, conn, msg, storage, coordinator)

        assert storage.logbook_enabled is False
        conn.send_result.assert_called_once()
