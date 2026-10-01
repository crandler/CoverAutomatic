"""Tests for native Home Assistant conditions in rules (type ha_condition).

These tests use a real (minimal) HomeAssistant instance so that validation
and evaluation go through Home Assistant's own condition helpers.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from homeassistant import loader
from homeassistant.core import HomeAssistant

from custom_components.cover_automatic import ha_condition as hac
from custom_components.cover_automatic.engine import RuleEngine
from custom_components.cover_automatic.models import (
    Condition,
    ConditionType,
    CoverConfig,
    Rule,
)


@pytest_asyncio.fixture
async def hass(tmp_path):
    """Minimal running-loop HomeAssistant instance with some states."""
    instance = HomeAssistant(str(tmp_path))
    loader.async_setup(instance)
    instance.states.async_set("person.sylvain", "not_home", {"friendly_name": "Sylvain"})
    instance.states.async_set("weather.maison", "sunny", {"temperature": 29})
    instance.states.async_set("sensor.lux", "25000")
    instance.states.async_set("media_player.salon", "playing")
    yield instance
    await instance.async_stop(force=True)


def _ha(config, **params) -> Condition:
    return Condition(type=ConditionType.HA_CONDITION, params={"config": config, **params})


# ---------------------------------------------------------------------------
# Compile / evaluate
# ---------------------------------------------------------------------------

class TestCompileEvaluate:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("config", "expected"),
        [
            ({"condition": "state", "entity_id": "person.sylvain", "state": "not_home"}, True),
            ({"condition": "state", "entity_id": "person.sylvain", "state": ["home"]}, False),
            ({"condition": "not", "conditions": [
                {"condition": "state", "entity_id": "person.sylvain", "state": "home"}]}, True),
            ({"condition": "numeric_state", "entity_id": "weather.maison",
              "attribute": "temperature", "above": 26, "below": 35}, True),
            ({"condition": "numeric_state", "entity_id": "weather.maison",
              "attribute": "temperature", "above": 30}, False),
            ({"condition": "template",
              "value_template": "{{ states('sensor.lux') | float(0) > 20000 }}"}, True),
            # just changed -> not yet "for 15 minutes"
            ({"condition": "state", "entity_id": "person.sylvain", "state": "not_home",
              "for": {"minutes": 15}}, False),
            ({"condition": "or", "conditions": [
                {"condition": "state", "entity_id": "person.sylvain", "state": "home"},
                {"condition": "state", "entity_id": "media_player.salon", "state": ["playing", "paused"]}]}, True),
            # disabled condition is ignored (treated as met), like in automations
            ({"condition": "state", "entity_id": "person.sylvain", "state": "home", "enabled": False}, True),
        ],
    )
    async def test_evaluate(self, hass, config, expected) -> None:
        compiled = await hac.async_compile(hass, config)
        assert compiled.valid, compiled.error
        assert hac.evaluate(hass, compiled) is expected

    @pytest.mark.asyncio
    async def test_entities_include_templates(self, hass) -> None:
        compiled = await hac.async_compile(hass, {"condition": "or", "conditions": [
            {"condition": "state", "entity_id": "person.sylvain", "state": "home"},
            {"condition": "template", "value_template": "{{ is_state('media_player.salon', 'playing') }}"},
        ]})
        assert compiled.entities == {"person.sylvain", "media_player.salon"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("config", "code"),
        [
            (None, "empty"),
            ({}, "empty"),
            ({"condition": "state", "entity_id": "bad id", "state": "x"}, "invalid"),
            ({"condition": "state", "entity_id": "", "state": []}, "invalid"),
            ({"condition": "does_not_exist"}, "invalid"),
        ],
    )
    async def test_invalid_is_reported_and_never_matches(self, hass, config, code) -> None:
        compiled = await hac.async_compile(hass, config)
        assert not compiled.valid
        assert compiled.error_code == code
        assert hac.evaluate(hass, compiled) is False

    @pytest.mark.asyncio
    async def test_evaluation_error_is_false(self, hass) -> None:
        compiled = await hac.async_compile(hass, {
            "condition": "numeric_state", "entity_id": "person.sylvain", "above": 1,
        })
        assert compiled.valid
        assert hac.evaluate(hass, compiled) is False  # "not_home" is not numeric

    @pytest.mark.asyncio
    async def test_stored_config_is_not_mutated(self, hass) -> None:
        config = {"condition": "and", "conditions": [
            {"condition": "state", "entity_id": "person.sylvain", "state": "not_home", "for": "00:01:00"}]}
        snapshot = repr(config)
        await hac.async_compile(hass, config)
        assert repr(config) == snapshot


class TestYaml:
    def test_parse_mapping(self) -> None:
        config, err = hac.parse_yaml("condition: state\nentity_id: person.sylvain\nstate: home\n")
        assert err is None
        assert config == {"condition": "state", "entity_id": "person.sylvain", "state": "home"}

    def test_list_becomes_and(self) -> None:
        config, err = hac.parse_yaml("- condition: state\n  entity_id: a.b\n  state: 'on'\n")
        assert err is None
        assert config["condition"] == "and" and len(config["conditions"]) == 1

    def test_syntax_error_has_position(self) -> None:
        config, err = hac.parse_yaml("condition: state\nfoo:: bar: baz\n")
        assert config is None
        assert err["code"] == "yaml" and err["line"] == 2

    def test_scalar_is_rejected(self) -> None:
        config, err = hac.parse_yaml("just text")
        assert config is None and err["code"] == "not_mapping"

    def test_empty_text(self) -> None:
        assert hac.parse_yaml("   ") == (None, None)

    def test_dump_roundtrip(self) -> None:
        config = {"condition": "state", "entity_id": "person.sylvain", "state": ["home", "Travail"]}
        assert hac.parse_yaml(hac.dump_yaml(config))[0] == config


class TestSimpleReading:
    @pytest.mark.asyncio
    async def test_state_and_attribute(self, hass) -> None:
        assert hac.simple_reading(hass, {"condition": "state", "entity_id": "person.sylvain", "state": "home"}) == {
            "entity_id": "person.sylvain", "attribute": None, "value": "not_home"}
        reading = hac.simple_reading(hass, {"condition": "numeric_state", "entity_id": "weather.maison",
                                            "attribute": "temperature", "above": 1})
        assert reading["value"] == 29

    @pytest.mark.asyncio
    async def test_not_wrapper_and_complex(self, hass) -> None:
        cfg = {"condition": "not", "conditions": [{"condition": "state", "entity_id": "person.sylvain", "state": "x"}]}
        assert hac.simple_reading(hass, cfg)["value"] == "not_home"
        assert hac.simple_reading(hass, {"condition": "template", "value_template": "{{ true }}"}) is None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _engine(hass, rules: dict[str, Rule]) -> RuleEngine:
    storage = MagicMock()
    storage.rules = rules
    storage.scenarios = {}
    storage.active_scenario = "everyday"
    storage.facades = {}
    storage.indoor_temp_sensor = None
    return RuleEngine(hass, storage)


class TestEngine:
    @pytest.mark.asyncio
    async def test_rule_with_ha_condition(self, hass) -> None:
        rule = Rule(id="absent", name="Absent", target_position=0, conditions=[
            _ha({"condition": "state", "entity_id": "person.sylvain", "state": "not_home"}),
        ])
        engine = _engine(hass, {"absent": rule})
        cover = CoverConfig(entity_id="cover.salon", name="Salon")

        # Not compiled yet -> not met (never raises in the sync evaluation)
        assert engine.evaluate_cover(cover) is None

        changed = await engine.async_prepare_ha_conditions()
        assert changed is True
        assert engine.ha_condition_entities() == {"person.sylvain"}
        target = engine.evaluate_cover(cover)
        assert target is not None and target.rule_id == "absent"

        hass.states.async_set("person.sylvain", "home")
        assert engine.evaluate_cover(cover) is None

    @pytest.mark.asyncio
    async def test_prepare_drops_unused_and_reports_status(self, hass) -> None:
        good = _ha({"condition": "state", "entity_id": "person.sylvain", "state": "home"})
        bad = _ha({"condition": "state", "entity_id": "bad id", "state": "x"})
        rules = {"r": Rule(id="r", name="R", conditions=[good, bad])}
        engine = _engine(hass, rules)
        await engine.async_prepare_ha_conditions()
        assert engine.ha_condition_status(good)["valid"] is True
        status = engine.ha_condition_status(bad)
        assert status["valid"] is False and status["error_code"] == "invalid"

        rules["r"].conditions = [good]
        await engine.async_prepare_ha_conditions()
        assert len(engine._ha_compiled) == 1

    @pytest.mark.asyncio
    async def test_preview(self, hass) -> None:
        engine = _engine(hass, {})
        cond = _ha({"condition": "state", "entity_id": "person.sylvain", "state": "not_home"})
        await engine.async_prepare_ha_conditions([cond])
        result = engine.preview_condition(cond)
        assert result["evaluable"] is True and result["matched"] is True
        assert result["kind"] == "ha_reading"
        assert result["actual"]["value"] == "not_home"


# ---------------------------------------------------------------------------
# WebSocket API
# ---------------------------------------------------------------------------

class TestValidateApi:
    async def _call(self, hass, msg):
        from custom_components.cover_automatic.api import ws_condition_validate

        conn = MagicMock()
        await ws_condition_validate(hass, conn, {"id": 1, **msg}, MagicMock(), MagicMock())
        return conn.send_result.call_args.args[1]

    @pytest.mark.asyncio
    async def test_valid_yaml(self, hass) -> None:
        res = await self._call(hass, {"yaml": "condition: state\nentity_id: person.sylvain\nstate: not_home\n"})
        assert res["valid"] is True and res["matched"] is True
        assert res["config"]["entity_id"] == "person.sylvain"
        assert res["entities"] == ["person.sylvain"] and res["unknown_entities"] == []

    @pytest.mark.asyncio
    async def test_unknown_entity_is_flagged(self, hass) -> None:
        res = await self._call(hass, {"config": {"condition": "state", "entity_id": "person.nobody", "state": "home"}})
        assert res["valid"] is True
        assert res["unknown_entities"] == ["person.nobody"]
        assert "entity_id: person.nobody" in res["yaml"]

    @pytest.mark.asyncio
    async def test_yaml_syntax_error(self, hass) -> None:
        res = await self._call(hass, {"yaml": "condition: state\nfoo:: bar: baz\n"})
        assert res["valid"] is False and res["error_code"] == "yaml" and res["error_line"] == 2

    @pytest.mark.asyncio
    async def test_invalid_condition(self, hass) -> None:
        res = await self._call(hass, {"yaml": "condition: state\nentity_id: bad id\nstate: x\n"})
        assert res["valid"] is False and res["error_code"] == "invalid" and res["error"]

    @pytest.mark.asyncio
    async def test_config_response_contains_condition_status(self, hass) -> None:
        from custom_components.cover_automatic.api import _build_config_response

        good = _ha({"condition": "state", "entity_id": "person.sylvain", "state": "home"})
        rules = {"r": Rule(id="r", name="R", conditions=[Condition(type=ConditionType.WORKDAY), good])}
        engine = _engine(hass, rules)
        await engine.async_prepare_ha_conditions()
        storage = engine.storage
        storage.covers, storage.facades = {}, {}
        coordinator = MagicMock()
        coordinator.engine = engine
        response = _build_config_response(storage, None, coordinator)
        assert response["condition_status"] == {"r": {"1": {"valid": True, "error": None, "error_code": None}}}


class TestCoordinatorTracking:
    def test_tracking_includes_engine_entities(self) -> None:
        from custom_components.cover_automatic.coordinator import CoverAutomaticCoordinator

        coord = CoverAutomaticCoordinator.__new__(CoverAutomaticCoordinator)
        coord.hass = MagicMock()
        coord.storage = MagicMock()
        coord.storage._data = {"covers": {}, "rules": {}}
        coord.storage.outdoor_temp_sensor = None
        coord.storage.indoor_temp_sensor = None
        coord.storage.weather_entity = None
        coord.storage.wind_sensor = None
        coord.storage.solar_sensor = None
        coord.storage.workday_sensor = None
        coord.engine = MagicMock()
        coord.engine.ha_condition_entities.return_value = {"person.sylvain"}
        coord._tracked_entities = set()
        coord._unsub_state_change = []
        from unittest.mock import patch

        with patch("custom_components.cover_automatic.coordinator.async_track_state_change_event") as track:
            coord._setup_state_tracking()
        assert "person.sylvain" in track.call_args.args[1]
        assert coord._is_rule_entity("person.sylvain") is True
