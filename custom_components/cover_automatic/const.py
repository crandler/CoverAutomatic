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

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.storage"
STORAGE_VERSION: Final = 1
