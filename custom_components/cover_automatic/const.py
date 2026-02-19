"""Constants for CoverAutomatic integration."""
from typing import Final

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
DEFAULT_TILT_OPEN: Final = 100
DEFAULT_TILT_CLOSED: Final = 0
TILT_COMMAND_DELAY: Final = 1.5  # seconds between position and tilt command
TILT_FEATURE_FLAG: Final = 128  # CoverEntityFeature.SET_TILT_POSITION

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_VERSION: Final = 1
