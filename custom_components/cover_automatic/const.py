"""Constants for CoverAutomatic integration."""
from typing import Final

from homeassistant.components.cover import CoverEntityFeature

DOMAIN: Final = "cover_automatic"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Facade azimuth ranges
FACADE_PRESETS: Final = {
    "north": {"start": 315, "end": 45},
    "east": {"start": 45, "end": 135},
    "south": {"start": 135, "end": 225},
    "west": {"start": 225, "end": 315},
}

# Tilt / slat control
TILT_COMMAND_DELAY: Final = 1.5  # seconds between position and tilt command
TILT_FEATURE_FLAG: Final = CoverEntityFeature.SET_TILT_POSITION
# Covers lacking this feature only support open/close commands
SET_POSITION_FEATURE_FLAG: Final = CoverEntityFeature.SET_POSITION

# Binary sensor on-states for contact sensors
BINARY_SENSOR_ON_STATES: Final = frozenset({"on", "open", "true", "1"})

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_VERSION: Final = 1

# Activity log
LOG_STORAGE_KEY: Final = f"{DOMAIN}.log"
LOG_RETENTION_DAYS: Final = 3
LOG_EVENT_POSITION: Final = "position"
LOG_EVENT_STATUS: Final = "status"
LOG_EVENT_RULE: Final = "rule"
LOG_EVENT_WIND: Final = "wind"

# Panel push signal (dispatched when coordinator data changes). A dispatcher
# signal instead of a bus event: bus events are written to the recorder
# database, which grew by one row per update cycle.
SIGNAL_DATA_UPDATED: Final = f"{DOMAIN}_updated"
