"""Sun position calculations for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from astral import Observer
from astral.sun import zenith_and_azimuth
from homeassistant.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from .models import Facade

_LOGGER = logging.getLogger(__name__)

SUN_ENTITY_ID = "sun.sun"

# Facade sun times: coarse scan of the day, then bisection at each boundary
_SCAN_STEP = timedelta(minutes=5)
_BOUNDARY_PRECISION = timedelta(seconds=15)

# (day, facade geometry, location) -> (entry, exit); holds the current day only
_times_cache: dict[tuple[Any, ...], tuple[str | None, str | None]] = {}


def get_sun_position(hass: HomeAssistant) -> tuple[float, float] | None:
    """Get current sun azimuth and elevation.

    Returns:
        Tuple of (azimuth, elevation) in degrees, or None if unavailable.
    """
    sun_state = hass.states.get(SUN_ENTITY_ID)
    if sun_state is None:
        _LOGGER.warning("Sun entity not available")
        return None

    try:
        azimuth_val = sun_state.attributes.get("azimuth")
        elevation_val = sun_state.attributes.get("elevation")
        if azimuth_val is None or elevation_val is None:
            return None
        return (float(azimuth_val), float(elevation_val))
    except (ValueError, TypeError) as err:
        _LOGGER.error("Error reading sun position: %s", err)
        return None


def is_sun_on_facade(
    hass: HomeAssistant, facade: Facade,
) -> bool:
    """Check if sun is shining on a facade.

    Facade azimuth values are real compass bearings (house rotation already
    applied at configuration time).

    Args:
        hass: Home Assistant instance
        facade: Facade to check

    Returns:
        True if sun is currently shining on the facade.
    """
    position = get_sun_position(hass)
    if position is None:
        return False

    azimuth, elevation = position
    return _sun_hits_facade(facade, azimuth, elevation)


def _sun_hits_facade(facade: Facade, azimuth: float, elevation: float) -> bool:
    """Return True if a sun at azimuth/elevation shines on the facade."""
    if elevation < facade.min_elevation:
        return False

    start = facade.azimuth_start
    end = facade.azimuth_end

    if start <= end:
        return start <= azimuth <= end
    return azimuth >= start or azimuth <= end


def get_sunrise_time(hass: HomeAssistant) -> float | None:
    """Get today's sunrise time as timestamp."""
    sunrise = get_astral_event_date(hass, SUN_EVENT_SUNRISE, dt_util.now())
    if sunrise is None:
        return None
    return sunrise.timestamp()


def get_sunset_time(hass: HomeAssistant) -> float | None:
    """Get today's sunset time as timestamp."""
    sunset = get_astral_event_date(hass, SUN_EVENT_SUNSET, dt_util.now())
    if sunset is None:
        return None
    return sunset.timestamp()


def get_facade_sun_times(
    hass: HomeAssistant, facade: Facade,
) -> tuple[str | None, str | None]:
    """Return today's sun entry and exit time (local HH:MM) for a facade.

    Derived from the real sun path at the configured location with the same
    test as is_sun_on_facade, so the times match when the automation sees the
    sun on the facade. Facade azimuth values are real compass bearings (house
    rotation already applied at configuration time).

    A facade lit in two separate periods (wrap-around facade in summer) reports
    the first one. Returns (None, None) if the sun does not reach it today.
    Computed once per day and facade, both sensors share the result.
    """
    today = dt_util.now().date()
    key = (
        today,
        facade.azimuth_start,
        facade.azimuth_end,
        facade.min_elevation,
        hass.config.latitude,
        hass.config.longitude,
        hass.config.elevation,
    )
    if key not in _times_cache:
        for stale in [k for k in _times_cache if k[0] != today]:
            del _times_cache[stale]
        _times_cache[key] = _compute_facade_sun_times(hass, facade, today)
    return _times_cache[key]


def _compute_facade_sun_times(
    hass: HomeAssistant, facade: Facade, day: date,
) -> tuple[str | None, str | None]:
    """Scan the local day for the first period the sun shines on the facade."""
    observer = Observer(hass.config.latitude, hass.config.longitude, hass.config.elevation)

    def lit(moment: datetime) -> bool:
        zenith, azimuth = zenith_and_azimuth(observer, moment)
        return _sun_hits_facade(facade, azimuth, 90.0 - zenith)

    day_start = dt_util.start_of_local_day(day)
    day_end = dt_util.start_of_local_day(day + timedelta(days=1))

    entry: datetime | None = None
    exit_: datetime | None = None
    previous: datetime | None = None
    moment = day_start
    while moment < day_end:
        if lit(moment):
            if entry is None:
                entry = _boundary(lit, moment, previous) if previous else moment
            exit_ = moment
        elif entry is not None:
            exit_ = _boundary(lit, exit_, moment)
            break
        previous = moment
        moment += _SCAN_STEP

    if entry is None or exit_ is None:
        return None, None
    return _format_local(entry), _format_local(exit_)


def _boundary(
    lit: Callable[[datetime], bool], inside: datetime, outside: datetime,
) -> datetime:
    """Bisect between a lit and an unlit moment, return the lit side of the edge."""
    while abs(outside - inside) > _BOUNDARY_PRECISION:
        middle = inside + (outside - inside) / 2
        if lit(middle):
            inside = middle
        else:
            outside = middle
    return inside


def _format_local(moment: datetime) -> str:
    return dt_util.as_local(moment).strftime("%H:%M")
