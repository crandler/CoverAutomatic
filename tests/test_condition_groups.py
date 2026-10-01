"""Tests for condition groups ((A or B) and (C or D)) and negated conditions."""
# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.cover_automatic.models import (
    MAX_CONDITION_GROUPS,
    Condition,
    ConditionType,
    Rule,
)
from tests.test_api import _make_connection, _make_coordinator, _make_hass, _make_storage
from tests.test_engine import (  # noqa: F401 -- pytest fixtures
    MockState,
    engine,
    mock_hass,
    mock_storage,
    test_cover,
)


def _state(entity: str, group: int = 0, *, negate: bool = False, state: str = "on") -> Condition:
    return Condition(
        type=ConditionType.STATE_IS,
        params={"entity_id": entity, "state": state},
        group=group,
        negate=negate,
    )


@pytest.fixture
def states(mock_hass):
    """Entity states by id; missing ids are unavailable (None)."""
    values: dict[str, str] = {}
    mock_hass.states.get.side_effect = lambda eid: MockState(values[eid]) if eid in values else None
    return values


class TestModel:
    def test_legacy_rule_is_one_group_with_its_operator(self) -> None:
        rule = Rule.from_dict({"id": "r", "name": "R", "condition_operator": "or", "conditions": []})
        assert rule.group_operators == ["or"]
        assert rule.to_dict()["group_operators"] == ["or"]

    def test_direct_construction_uses_condition_operator(self) -> None:
        rule = Rule(id="r", name="R", condition_operator="or", conditions=[_state("a")])
        assert rule.condition_groups() == [("or", rule.conditions)]

    def test_condition_roundtrip(self) -> None:
        cond = _state("a", 2, negate=True)
        again = Condition.from_dict(cond.to_dict())
        assert (again.group, again.negate) == (2, True)

    def test_legacy_condition_defaults(self) -> None:
        cond = Condition.from_dict({"type": "state_is", "params": {}})
        assert (cond.group, cond.negate) == (0, False)

    def test_invalid_group_is_clamped(self) -> None:
        assert Condition.from_dict({"type": "state_is", "params": {}, "group": "x"}).group == 0
        assert Condition.from_dict({"type": "state_is", "params": {}, "group": -3}).group == 0
        assert Condition.from_dict({"type": "state_is", "params": {}, "group": 99}).group == MAX_CONDITION_GROUPS - 1

    def test_invalid_group_operators_sanitized(self) -> None:
        rule = Rule.from_dict({"id": "r", "name": "R", "group_operators": ["or", "xor"]})
        assert rule.group_operators == ["or", "and"]

    def test_empty_groups_are_skipped(self) -> None:
        rule = Rule(id="r", name="R", group_operators=["and", "or", "or"], conditions=[_state("a", 2)])
        assert rule.condition_groups() == [("or", rule.conditions)]


class TestEvaluation:
    def _or_and_or(self, between: str = "and", inner: str = "or") -> Rule:
        # (a OP b) BETWEEN (c OP d)
        return Rule(
            id="r", name="R", condition_operator=between, group_operators=[inner, inner],
            conditions=[_state("a"), _state("b"), _state("c", 1), _state("d", 1)],
        )

    @pytest.mark.parametrize(
        ("on", "expected"),
        [({"a", "c"}, True), ({"b", "d"}, True), ({"a", "b"}, False), ({"c"}, False), (set(), False)],
    )
    def test_or_groups_joined_by_and(self, engine, states, test_cover, on, expected) -> None:
        states.update({e: ("on" if e in on else "off") for e in "abcd"})
        assert engine._evaluate_conditions(self._or_and_or(), test_cover) is expected

    @pytest.mark.parametrize(
        ("on", "expected"),
        [({"a", "b"}, True), ({"c", "d"}, True), ({"a", "c"}, False), ({"a", "b", "c"}, True)],
    )
    def test_and_groups_joined_by_or(self, engine, states, test_cover, on, expected) -> None:
        states.update({e: ("on" if e in on else "off") for e in "abcd"})
        rule = self._or_and_or(between="or", inner="and")
        assert engine._evaluate_conditions(rule, test_cover) is expected

    def test_single_group_ignores_between_operator(self, engine, states, test_cover) -> None:
        states.update({"a": "on", "b": "off"})
        rule = Rule(
            id="r", name="R", condition_operator="and", group_operators=["or"],
            conditions=[_state("a"), _state("b")],
        )
        assert engine._evaluate_conditions(rule, test_cover) is True


class TestNegate:
    def test_negated_condition(self, engine, states, test_cover) -> None:
        states["a"] = "off"
        rule = Rule(id="r", name="R", conditions=[_state("a", negate=True)])
        assert engine._evaluate_conditions(rule, test_cover) is True
        states["a"] = "on"
        assert engine._evaluate_conditions(rule, test_cover) is False

    def test_negated_unavailable_entity_is_not_met(self, engine, states, test_cover) -> None:
        rule = Rule(id="r", name="R", conditions=[_state("missing", negate=True)])
        assert engine._evaluate_conditions(rule, test_cover) is False

    def test_negated_weather_without_entity_is_not_met(self, engine, mock_storage, states, test_cover) -> None:
        mock_storage.weather_entity = "weather.home"
        cond = Condition(type=ConditionType.WEATHER_IS, params={"weather": ["rainy"]}, negate=True)
        rule = Rule(id="r", name="R", conditions=[cond])
        assert engine._evaluate_conditions(rule, test_cover) is False
        states["weather.home"] = "sunny"
        assert engine._evaluate_conditions(rule, test_cover) is True
        states["weather.home"] = "rainy"
        assert engine._evaluate_conditions(rule, test_cover) is False

    def test_negated_time_condition(self, engine, test_cover) -> None:
        cond = Condition(type=ConditionType.DAY_OF_WEEK, params={"days": ["mon"]}, negate=True)
        rule = Rule(id="r", name="R", conditions=[cond])
        with patch.object(engine, "_eval_day_of_week", return_value=True):
            assert engine._evaluate_conditions(rule, test_cover) is False
        with patch.object(engine, "_eval_day_of_week", return_value=False):
            assert engine._evaluate_conditions(rule, test_cover) is True

    def test_preview_applies_negation(self, engine, states) -> None:
        states["a"] = "off"
        assert engine.preview_condition(_state("a", negate=True))["matched"] is True
        assert engine.preview_condition(_state("missing", negate=True))["matched"] is False


class TestApi:
    @pytest.mark.asyncio
    async def test_add_without_groups_uses_operator(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        storage = _make_storage()
        msg = {"id": 1, "name": "N", "condition_operator": "or"}
        await ws_rule_add(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        assert storage.async_add_rule.call_args[0][0].group_operators == ["or"]

    @pytest.mark.asyncio
    async def test_update_with_groups(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        storage = _make_storage()
        storage.rules = {"r": Rule(id="r", name="R")}
        msg = {
            "id": 1, "rule_id": "r", "condition_operator": "and", "group_operators": ["or", "or"],
            "conditions": [
                {"type": "state_is", "params": {}, "group": 0},
                {"type": "state_is", "params": {}, "group": 1, "negate": True},
            ],
        }
        await ws_rule_update(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        rule = storage.async_add_rule.call_args[0][0]
        assert rule.group_operators == ["or", "or"]
        assert rule.condition_operator == "and"
        assert [(c.group, c.negate) for c in rule.conditions] == [(0, False), (1, True)]

    @pytest.mark.asyncio
    async def test_legacy_update_of_single_group_operator(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        storage = _make_storage()
        storage.rules = {"r": Rule(id="r", name="R", group_operators=["and"])}
        msg = {"id": 1, "rule_id": "r", "condition_operator": "or"}
        await ws_rule_update(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        assert storage.async_add_rule.call_args[0][0].group_operators == ["or"]

    @pytest.mark.asyncio
    async def test_update_keeps_existing_groups(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_update

        storage = _make_storage()
        storage.rules = {"r": Rule(
            id="r", name="R", group_operators=["or", "or"],
            conditions=[_state("a"), _state("b", 1)],
        )}
        msg = {"id": 1, "rule_id": "r", "name": "Renamed", "condition_operator": "or"}
        await ws_rule_update(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        rule = storage.async_add_rule.call_args[0][0]
        assert rule.group_operators == ["or", "or"]
        assert rule.condition_operator == "or"
