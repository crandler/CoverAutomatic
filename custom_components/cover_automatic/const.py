"""Constants for CoverAutomatic integration."""
from typing import Final

DOMAIN: Final = "cover_automatic"

# Defaults
DEFAULT_PAUSE_DURATION: Final = 120  # minutes
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Facade azimuth ranges
FACADE_PRESETS: Final = {
    "north": {"start": 315, "end": 45},
    "east": {"start": 45, "end": 135},
    "south": {"start": 135, "end": 225},
    "west": {"start": 225, "end": 315},
}

# Condition types
CONDITION_SUN_ON_FACADE: Final = "sun_on_facade"
CONDITION_SUN_ELEVATION_ABOVE: Final = "sun_elevation_above"
CONDITION_SUN_ELEVATION_BELOW: Final = "sun_elevation_below"
CONDITION_TEMP_ABOVE: Final = "temperature_above"
CONDITION_TEMP_BELOW: Final = "temperature_below"
CONDITION_TIME_BETWEEN: Final = "time_between"
CONDITION_TIME_AFTER_SUNRISE: Final = "time_after_sunrise"
CONDITION_TIME_AFTER_SUNSET: Final = "time_after_sunset"
CONDITION_STATE_IS: Final = "state_is"

# Scenarios
DEFAULT_SCENARIOS: Final = ["everyday", "summer", "winter", "vacation", "cinema", "manual"]

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_VERSION: Final = 1

# Platforms
PLATFORMS: Final = ["cover", "switch", "sensor", "select", "number"]
