"""Tests for the dawn / dusk (civil twilight) rule conditions."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from custom_components.cover_automatic import sun
from custom_components.cover_automatic.engine import RuleEngine
from custom_components.cover_automatic.models import Condition, ConditionType
from tests.test_sun import PARIS, _astral_hass

MOD = "custom_components.cover_automatic.engine"


def _engine() -> RuleEngine:
    return RuleEngine(MagicMock(), MagicMock())


def _eval(engine, ctype, now, *, dawn, dusk, yesterday_dusk=None, offset=0):
    cond = Condition(type=ctype, params={"offset": offset})
    with (
        patch(f"{MOD}.get_dawn_time", return_value=dawn),
        patch(f"{MOD}.get_dusk_time", return_value=dusk),
        patch(f"{MOD}.get_sun_event_time", return_value=yesterday_dusk),
        patch(f"{MOD}.dt_util.now") as mock_now,
    ):
        mock_now.return_value.timestamp.return_value = now
        return engine._evaluate_condition(cond, None)


H = 3600
MIDNIGHT = 1_000_000.0
DAWN = MIDNIGHT + 6 * H
DUSK = MIDNIGHT + 21 * H


class TestDawnDusk:
    @pytest.mark.parametrize(
        ("ctype", "now", "expected"),
        [
            (ConditionType.TIME_AFTER_DAWN, DAWN - 60, False),
            (ConditionType.TIME_AFTER_DAWN, DAWN + 60, True),
            (ConditionType.TIME_BEFORE_DAWN, DAWN - 60, True),
            (ConditionType.TIME_BEFORE_DAWN, DAWN + 60, False),
            (ConditionType.TIME_BEFORE_DUSK, DUSK - 60, True),
            (ConditionType.TIME_BEFORE_DUSK, DUSK + 60, False),
            (ConditionType.TIME_AFTER_DUSK, DUSK - 60, False),
            (ConditionType.TIME_AFTER_DUSK, DUSK + 60, True),
            # after midnight: still "after dusk" (yesterday's) until dawn
            (ConditionType.TIME_AFTER_DUSK, MIDNIGHT + 2 * H, True),
            (ConditionType.TIME_AFTER_DUSK, DAWN + 60, False),
        ],
    )
    def test_evaluation(self, ctype, now, expected) -> None:
        assert _eval(_engine(), ctype, now, dawn=DAWN, dusk=DUSK,
                     yesterday_dusk=DUSK - 24 * H) is expected

    def test_offset(self) -> None:
        engine = _engine()
        assert _eval(engine, ConditionType.TIME_AFTER_DAWN, DAWN + 10 * 60,
                     dawn=DAWN, dusk=DUSK, offset=15) is False
        assert _eval(engine, ConditionType.TIME_AFTER_DAWN, DAWN + 20 * 60,
                     dawn=DAWN, dusk=DUSK, offset=15) is True

    def test_polar_no_event_is_false(self) -> None:
        engine = _engine()
        for ctype in (ConditionType.TIME_AFTER_DAWN, ConditionType.TIME_BEFORE_DAWN,
                      ConditionType.TIME_AFTER_DUSK, ConditionType.TIME_BEFORE_DUSK):
            assert _eval(engine, ctype, MIDNIGHT, dawn=None, dusk=None) is False

    def test_preview_shows_event_time(self) -> None:
        engine = _engine()
        cond = Condition(type=ConditionType.TIME_AFTER_DUSK, params={"offset": 0})
        with patch(f"{MOD}.get_dusk_time", return_value=DUSK):
            result = engine.preview_condition(cond)
        assert result["kind"] == "sun_time" and result["actual"]


class TestAstralTimes:
    def test_dawn_before_sunrise_and_dusk_after_sunset(self) -> None:
        lat, lon, tz = PARIS
        hass = _astral_hass(lat, lon, tz)
        day = datetime.datetime(2026, 6, 21, 12, 0, tzinfo=datetime.UTC)
        with patch("custom_components.cover_automatic.sun.dt_util.now", return_value=day):
            dawn, sunrise = sun.get_dawn_time(hass), sun.get_sunrise_time(hass)
            sunset, dusk = sun.get_sunset_time(hass), sun.get_dusk_time(hass)
        assert dawn < sunrise < sunset < dusk
        # civil twilight lasts roughly 40-50 min in Paris at midsummer
        assert 30 * 60 < sunrise - dawn < 60 * 60
        assert 30 * 60 < dusk - sunset < 60 * 60
