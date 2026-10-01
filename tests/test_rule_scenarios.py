"""Tests for per-rule scenario membership (Rule.scenario_ids)."""
# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
from __future__ import annotations

import pytest

from custom_components.cover_automatic.models import Rule, Scenario
from tests.test_api import _make_connection, _make_coordinator, _make_hass, _make_storage
from tests.test_engine import engine, mock_hass, mock_storage  # noqa: F401 -- pytest fixtures
from tests.test_storage import mock_store, storage  # noqa: F401 -- pytest fixtures


def _raw_rule(rule_id: str, **extra) -> dict:
    return {"id": rule_id, "name": rule_id, "conditions": [], "target_position": 0, **extra}


class TestModel:
    def test_default_is_none(self) -> None:
        assert Rule(id="r", name="R").scenario_ids is None

    def test_roundtrip(self) -> None:
        rule = Rule(id="r", name="R", scenario_ids=["everyday", "summer"])
        assert Rule.from_dict(rule.to_dict()).scenario_ids == ["everyday", "summer"]

    def test_missing_or_invalid_field_means_all(self) -> None:
        assert Rule.from_dict(_raw_rule("r")).scenario_ids is None
        assert Rule.from_dict(_raw_rule("r", scenario_ids="everyday")).scenario_ids is None


class TestMigration:
    def test_existing_rules_get_every_scenario(self, storage) -> None:
        storage._data = {
            "rules": {"r1": _raw_rule("r1"), "r2": _raw_rule("r2", scenario_ids=["summer"])},
            "scenarios": {"everyday": {"id": "everyday"}, "summer": {"id": "summer"}},
        }
        storage._migrate_rule_scenarios()
        assert storage._data["rules"]["r1"]["scenario_ids"] == ["everyday", "summer"]
        # An explicit selection is kept as is.
        assert storage._data["rules"]["r2"]["scenario_ids"] == ["summer"]

    @pytest.mark.asyncio
    async def test_import_migrates_old_export(self, storage) -> None:
        await storage.async_import_data({
            "rules": {"r1": _raw_rule("r1")},
            "scenarios": {"everyday": {"id": "everyday", "name": "E"}, "cinema": {"id": "cinema", "name": "C"}},
        })
        assert storage.rules["r1"].scenario_ids == ["everyday", "cinema"]


class TestScenarioSync:
    @pytest.mark.asyncio
    async def test_new_scenario_added_to_every_rule(self, storage) -> None:
        storage._data = {
            "rules": {"r1": _raw_rule("r1", scenario_ids=["everyday"]), "r2": _raw_rule("r2", scenario_ids=[])},
            "scenarios": {"everyday": {"id": "everyday", "name": "E"}},
        }
        await storage.async_add_scenario(Scenario(id="party", name="Party"))
        assert storage.rules["r1"].scenario_ids == ["everyday", "party"]
        assert storage.rules["r2"].scenario_ids == ["party"]

    @pytest.mark.asyncio
    async def test_updating_scenario_does_not_reselect_it(self, storage) -> None:
        storage._data = {
            "rules": {"r1": _raw_rule("r1", scenario_ids=["everyday"])},
            "scenarios": {"everyday": {"id": "everyday", "name": "E"}, "party": {"id": "party", "name": "P"}},
        }
        await storage.async_add_scenario(Scenario(id="party", name="Party renamed"))
        assert storage.rules["r1"].scenario_ids == ["everyday"]

    @pytest.mark.asyncio
    async def test_removed_scenario_dropped_from_rules(self, storage) -> None:
        storage._data = {
            "rules": {"r1": _raw_rule("r1", scenario_ids=["everyday", "party"])},
            "scenarios": {"everyday": {"id": "everyday", "name": "E"}, "party": {"id": "party", "name": "P"}},
            "active_scenario": "everyday",
        }
        await storage.async_remove_scenario("party")
        assert storage.rules["r1"].scenario_ids == ["everyday"]


class TestEngineMembership:
    def test_rule_outside_scenario_is_inactive(self, engine, mock_storage) -> None:
        mock_storage.scenarios = {"cinema": Scenario(id="cinema", name="Cinema")}
        rule = Rule(id="r", name="R", scenario_ids=["everyday"])
        assert engine._rule_active_in_scenario(rule, "cinema") is False

    def test_member_rule_is_active(self, engine, mock_storage) -> None:
        mock_storage.scenarios = {"cinema": Scenario(id="cinema", name="Cinema")}
        rule = Rule(id="r", name="R", scenario_ids=["cinema"])
        assert engine._rule_active_in_scenario(rule, "cinema") is True

    def test_member_rule_switched_off_in_scenario(self, engine, mock_storage) -> None:
        mock_storage.scenarios = {"cinema": Scenario(id="cinema", name="Cinema", rules_disabled=["r"])}
        rule = Rule(id="r", name="R", scenario_ids=["cinema"])
        assert engine._rule_active_in_scenario(rule, "cinema") is False

    def test_none_means_every_scenario(self, engine, mock_storage) -> None:
        mock_storage.scenarios = {"cinema": Scenario(id="cinema", name="Cinema")}
        assert engine._rule_active_in_scenario(Rule(id="r", name="R"), "cinema") is True


class TestApi:
    def _storage(self):
        return _make_storage(scenarios={
            "everyday": Scenario(id="everyday", name="E"),
            "cinema": Scenario(id="cinema", name="C"),
        })

    @pytest.mark.asyncio
    async def test_add_defaults_to_all_scenarios(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        storage = self._storage()
        await ws_rule_add(_make_hass(), _make_connection(), {"id": 1, "name": "New"}, storage, _make_coordinator())
        assert storage.async_add_rule.call_args[0][0].scenario_ids == ["everyday", "cinema"]

    @pytest.mark.asyncio
    async def test_add_with_selection(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        storage = self._storage()
        msg = {"id": 1, "name": "New", "scenario_ids": ["cinema"]}
        await ws_rule_add(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        assert storage.async_add_rule.call_args[0][0].scenario_ids == ["cinema"]

    @pytest.mark.asyncio
    async def test_add_rejects_unknown_scenario(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        storage, conn = self._storage(), _make_connection()
        msg = {"id": 1, "name": "New", "scenario_ids": ["nope"]}
        await ws_rule_add(_make_hass(), conn, msg, storage, _make_coordinator())
        assert conn.send_error.call_args[0][1] == "not_found"
        storage.async_add_rule.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_changes_and_keeps_selection(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        storage = self._storage()
        storage.rules = {"r": Rule(id="r", name="R", scenario_ids=["everyday"])}
        coord = _make_coordinator()
        await ws_rule_update(_make_hass(), _make_connection(), {"id": 1, "rule_id": "r", "name": "R2"}, storage, coord)
        assert storage.async_add_rule.call_args[0][0].scenario_ids == ["everyday"]
        msg = {"id": 2, "rule_id": "r", "scenario_ids": ["cinema", "everyday"]}
        await ws_rule_update(_make_hass(), _make_connection(), msg, storage, coord)
        assert storage.async_add_rule.call_args[0][0].scenario_ids == ["cinema", "everyday"]

    @pytest.mark.asyncio
    async def test_update_rejects_unknown_scenario(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        storage, conn = self._storage(), _make_connection()
        storage.rules = {"r": Rule(id="r", name="R")}
        msg = {"id": 1, "rule_id": "r", "scenario_ids": ["nope"]}
        await ws_rule_update(_make_hass(), conn, msg, storage, _make_coordinator())
        assert conn.send_error.call_args[0][1] == "not_found"
        storage.async_add_rule.assert_not_awaited()
