"""Sun position calculations for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sun import STATE_ABOVE_HORIZON
from homeassistant.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Facade

_LOGGER = logging.getLogger(__name__)

SUN_ENTITY_ID = "sun.sun"


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


def is_sun_above_horizon(hass: HomeAssistant) -> bool:
    """Check if sun is above horizon."""
    sun_state = hass.states.get(SUN_ENTITY_ID)
    if sun_state is None:
        return False
    return sun_state.state == STATE_ABOVE_HORIZON


def is_sun_on_facade(hass: HomeAssistant, facade: Facade) -> bool:
    """Check if sun is shining on a facade.

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

    if elevation < facade.min_elevation:
        return False

    start = facade.azimuth_start
    end = facade.azimuth_end

    if start <= end:
        return start <= azimuth <= end
    else:
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


def _azimuth_to_time(
    azimuth: float,
    sunrise: float,
    day_length: float,
    az_sunrise: float,
    az_range: float,
) -> str | None:
    """Convert azimuth to time string if within sun path range."""
    fraction = (azimuth - az_sunrise) / az_range
    if not 0 <= fraction <= 1:
        return None
    timestamp = sunrise + (fraction * day_length)
    dt_local = dt_util.as_local(dt_util.utc_from_timestamp(timestamp))
    return dt_local.strftime("%H:%M")


def get_facade_sun_times(
    hass: HomeAssistant, facade: Facade
) -> tuple[str | None, str | None]:
    """Calculate approximate sun entry and exit times for a facade.

    Uses linear interpolation based on typical sun path for temperate latitudes.
    Returns times in HH:MM format or None if unavailable.

    For wrap-around facades (e.g., north: 315-45), calculates times for both
    morning (0-end) and evening (start-360) sun exposure periods.
    """
    sunrise = get_sunrise_time(hass)
    sunset = get_sunset_time(hass)

    if sunrise is None or sunset is None:
        return None, None

    day_length = sunset - sunrise
    if day_length <= 0:
        return None, None

    # Realistic azimuth range for temperate latitudes (e.g., Central Europe)
    # Summer: sunrise ~50-60, sunset ~300-310
    # Winter: sunrise ~120-130, sunset ~230-240
    # Using moderate values that work year-round
    az_sunrise = 60.0
    az_sunset = 300.0
    az_range = az_sunset - az_sunrise  # 240 degrees

    start_az = facade.azimuth_start
    end_az = facade.azimuth_end

    # Handle wrap-around facades (e.g., north: 315-45)
    if start_az > end_az:
        # Facade wraps around 0/360. Sun can hit it in two periods:
        # 1. Morning: azimuth 60 -> end_az (e.g., 60 -> 45 = early morning)
        # 2. Evening: start_az -> 300 (e.g., 315 -> 300 = won't happen if start > sunset)

        # Morning period: sun rises at az_sunrise, facade ends at end_az
        # Sun hits facade from sunrise until it passes end_az
        if end_az >= az_sunrise:
            # Facade end is reachable from sunrise
            entry_time = _azimuth_to_time(az_sunrise, sunrise, day_length, az_sunrise, az_range)
            exit_time = _azimuth_to_time(end_az, sunrise, day_length, az_sunrise, az_range)
            if entry_time and exit_time:
                return entry_time, exit_time

        # Evening period: sun enters at start_az, sets at az_sunset
        if start_az <= az_sunset:
            entry_time = _azimuth_to_time(start_az, sunrise, day_length, az_sunrise, az_range)
            exit_time = _azimuth_to_time(az_sunset, sunrise, day_length, az_sunrise, az_range)
            if entry_time and exit_time:
                return entry_time, exit_time

        # Facade is outside sun path (e.g., winter when sun stays in south)
        return None, None

    # Normal case: start <= end (e.g., south: 135-225)
    entry_time = _azimuth_to_time(start_az, sunrise, day_length, az_sunrise, az_range)
    exit_time = _azimuth_to_time(end_az, sunrise, day_length, az_sunrise, az_range)

    return entry_time, exit_time
