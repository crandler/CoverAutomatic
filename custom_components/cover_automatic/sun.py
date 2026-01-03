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
        azimuth = float(sun_state.attributes.get("azimuth", 0))
        elevation = float(sun_state.attributes.get("elevation", 0))
        return (azimuth, elevation)
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
