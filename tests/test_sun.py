"""Tests for sun position calculations."""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.util import dt as dt_util

from custom_components.cover_automatic import sun as sun_mod
from custom_components.cover_automatic.models import Facade
from custom_components.cover_automatic.sun import (
    get_facade_sun_times,
    get_sun_position,
    is_sun_on_facade,
)


class MockState:
    """Mock Home Assistant state object."""

    def __init__(self, state: str, attributes: dict | None = None) -> None:
        """Initialize mock state."""
        self.state = state
        self.attributes = attributes or {}


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states.get.return_value = None
    return hass


@pytest.fixture
def south_facade() -> Facade:
    """Create a south-facing facade (135-225 degrees)."""
    return Facade(
        id="south",
        name="South",
        azimuth_start=135.0,
        azimuth_end=225.0,
        direction="south",
    )


@pytest.fixture
def north_facade() -> Facade:
    """Create a north-facing facade with wrap-around (315-45 degrees)."""
    return Facade(
        id="north",
        name="North",
        azimuth_start=315.0,
        azimuth_end=45.0,
        direction="north",
    )


@pytest.fixture
def east_facade() -> Facade:
    """Create an east-facing facade (45-135 degrees)."""
    return Facade(
        id="east",
        name="East",
        azimuth_start=45.0,
        azimuth_end=135.0,
        direction="east",
    )


@pytest.fixture
def west_facade() -> Facade:
    """Create a west-facing facade (225-315 degrees)."""
    return Facade(
        id="west",
        name="West",
        azimuth_start=225.0,
        azimuth_end=315.0,
        direction="west",
    )


class TestGetSunPosition:
    """Tests for get_sun_position function."""

    def test_returns_none_when_sun_entity_missing(self, mock_hass) -> None:
        """Test returns None when sun.sun entity is not available."""
        mock_hass.states.get.return_value = None
        result = get_sun_position(mock_hass)
        assert result is None

    def test_returns_azimuth_elevation(self, mock_hass) -> None:
        """Test returns azimuth and elevation tuple."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 180.5, "elevation": 45.2}
        )
        result = get_sun_position(mock_hass)
        assert result == (180.5, 45.2)

    def test_handles_invalid_attributes(self, mock_hass) -> None:
        """Test handles invalid azimuth/elevation values."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": "invalid", "elevation": None}
        )
        result = get_sun_position(mock_hass)
        assert result is None


class TestIsSunOnFacade:
    """Tests for is_sun_on_facade function."""

    def test_sun_on_south_facade(self, mock_hass, south_facade) -> None:
        """Test sun detection on south facade."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 180.0, "elevation": 30.0}
        )
        result = is_sun_on_facade(mock_hass, south_facade)
        assert result is True

    def test_sun_not_on_south_facade_wrong_azimuth(
        self, mock_hass, south_facade
    ) -> None:
        """Test sun not on south facade when azimuth is outside range."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 90.0, "elevation": 30.0}
        )
        result = is_sun_on_facade(mock_hass, south_facade)
        assert result is False

    def test_sun_on_north_facade_wrap_around_morning(
        self, mock_hass, north_facade
    ) -> None:
        """Test sun on north facade in morning (azimuth < 45)."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 30.0, "elevation": 10.0}
        )
        result = is_sun_on_facade(mock_hass, north_facade)
        assert result is True

    def test_sun_on_north_facade_wrap_around_evening(
        self, mock_hass, north_facade
    ) -> None:
        """Test sun on north facade in evening (azimuth > 315)."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 330.0, "elevation": 10.0}
        )
        result = is_sun_on_facade(mock_hass, north_facade)
        assert result is True

    def test_sun_not_on_north_facade_midday(self, mock_hass, north_facade) -> None:
        """Test sun not on north facade during midday."""
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 180.0, "elevation": 45.0}
        )
        result = is_sun_on_facade(mock_hass, north_facade)
        assert result is False

    def test_sun_below_min_elevation(self, mock_hass, south_facade) -> None:
        """Test sun not on facade when below minimum elevation."""
        south_facade.min_elevation = 20.0
        mock_hass.states.get.return_value = MockState(
            "above_horizon",
            {"azimuth": 180.0, "elevation": 10.0}
        )
        result = is_sun_on_facade(mock_hass, south_facade)
        assert result is False


# ---------------------------------------------------------------------------
# Facade sun entry/exit times from the real sun path.
# Reference values come from an independent 10-second brute-force scan with
# astral for lat 50.4, lon 7.8, 0 m, Europe/Berlin, using the same rule as
# is_sun_on_facade: azimuth inside the facade range and elevation >= min_elevation.
# ---------------------------------------------------------------------------

_BERLIN = ZoneInfo("Europe/Berlin")


@pytest.fixture
def located_hass():
    """Mock hass with a real location, dt_util switched to its time zone."""
    hass = MagicMock()
    hass.config.latitude = 50.4
    hass.config.longitude = 7.8
    hass.config.elevation = 0
    hass.config.time_zone = "Europe/Berlin"
    previous = dt_util.get_default_time_zone()
    dt_util.set_default_time_zone(_BERLIN)
    sun_mod._times_cache.clear()
    yield hass
    sun_mod._times_cache.clear()
    dt_util.set_default_time_zone(previous)


def _on(day: date):
    """Freeze 'today' for get_facade_sun_times."""
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=_BERLIN)
    return patch("homeassistant.util.dt.now", return_value=noon)


def _facade(start: float, end: float, min_elevation: float = 0.0) -> Facade:
    return Facade(
        id="f", name="F", azimuth_start=start, azimuth_end=end,
        direction="custom", min_elevation=min_elevation,
    )


def _assert_near(actual: str | None, expected: str, tolerance_min: int = 1) -> None:
    assert actual is not None, f"expected ~{expected}, got None"
    ah, am = map(int, actual.split(":"))
    eh, em = map(int, expected.split(":"))
    assert abs((ah * 60 + am) - (eh * 60 + em)) <= tolerance_min, f"{actual} vs {expected}"


OCT_1 = date(2026, 10, 1)


class TestGetFacadeSunTimes:
    """Entry/exit times follow the real sun path, not a fixed 60-300 degree model."""

    @pytest.mark.parametrize(
        ("start", "end", "entry", "exit_"),
        [
            # Start below 60 degrees: the old model reported no entry at all
            pytest.param(1, 170, "07:30", "12:46", id="east-1-170"),
            # End above 300 degrees: the old model reported no exit at all
            pytest.param(170, 350, "12:46", "19:05", id="west-170-350"),
            pytest.param(260, 359, "18:37", "19:05", id="north-260-359"),
            # Inside 60-300 the old model was off by up to 1.5 h in October
            pytest.param(95, 260, "07:34", "18:37", id="south-95-260"),
            pytest.param(95, 210, "07:34", "14:58", id="south-east-95-210"),
        ],
    )
    def test_times_match_real_sun_path(self, located_hass, start, end, entry, exit_) -> None:
        with _on(OCT_1):
            got_entry, got_exit = get_facade_sun_times(located_hass, _facade(start, end))
        _assert_near(got_entry, entry)
        _assert_near(got_exit, exit_)

    def test_facade_never_lit_returns_none(self, located_hass) -> None:
        """In October the sun never reaches 330-30 degrees."""
        with _on(OCT_1):
            assert get_facade_sun_times(located_hass, _facade(330, 30)) == (None, None)

    def test_wrap_around_facade_reports_first_period(self, located_hass) -> None:
        """At midsummer 300-60 is lit in the morning and the evening; the morning wins."""
        with _on(date(2026, 6, 21)):
            entry, exit_ = get_facade_sun_times(located_hass, _facade(300, 60))
        _assert_near(entry, "05:19")
        _assert_near(exit_, "06:09")

    def test_min_elevation_narrows_window(self, located_hass) -> None:
        with _on(OCT_1):
            entry, exit_ = get_facade_sun_times(located_hass, _facade(95, 260, min_elevation=20))
        _assert_near(entry, "09:47")
        _assert_near(exit_, "16:48")

    def test_computed_once_per_day(self, located_hass) -> None:
        """Both sensors of a facade and every refresh cycle share one daily result."""
        facade = _facade(95, 260)
        with patch(
            "custom_components.cover_automatic.sun.zenith_and_azimuth",
            wraps=sun_mod.zenith_and_azimuth,
        ) as calc:
            with _on(OCT_1):
                first = get_facade_sun_times(located_hass, facade)
                calls = calc.call_count
                assert calls > 0
                assert get_facade_sun_times(located_hass, facade) == first
                assert calc.call_count == calls
            with _on(date(2026, 10, 2)):
                get_facade_sun_times(located_hass, facade)
                assert calc.call_count > calls
        # Only the current day is kept
        assert {key[0] for key in sun_mod._times_cache} == {date(2026, 10, 2)}
