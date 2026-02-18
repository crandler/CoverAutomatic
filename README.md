# CoverAutomatic

**Custom HACS integration for Home Assistant - intelligent, automated control of covers (shutters, blinds, roller blinds).**

---

> **DEVELOPMENT VERSION - USE AT YOUR OWN RISK**
>
> This is a private hobby project in active development. It is **not** a finished product.
> Features may be incomplete, buggy, or change without notice.

---

## Disclaimer

**NO WARRANTY - NO LIABILITY**

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement.

In no event shall the author be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

**By using this software, you acknowledge that:**
- This is experimental software that may contain bugs
- Incorrect cover positions could affect your home's security or climate
- You are solely responsible for testing and validating the behavior
- The author assumes no responsibility for any damage to property or equipment

---

## Features

- **Sun-based automation** - Automatic shading when sun hits facade
- **Temperature control** - React to indoor/outdoor temperatures with comfort range
- **Weather integration** - React to weather conditions (sunny, cloudy, rainy)
- **Time schedules** - Open/close at specific times or relative to sunrise/sunset
- **Scenarios** - Switch between modes like "Summer", "Winter", "Vacation"
- **Manual override** - Automatic pause after manual intervention
- **Window contact sensor** - Lock cover open when window is opened (configurable position)
- **Ventilation sensor** - Move cover to ventilation position when vent is opened
- **Sun entry/exit times** - Shows when sun will hit or leave each facade
- **Hysteresis** - Prevents excessive motor wear with min position/time thresholds
- **Inverted covers** - Support for covers where 100% = closed
- **UI-first configuration** - Full setup via Home Assistant UI
- **Device agnostic** - Works with any cover entity (Homematic IP, Shelly, etc.)

## Requirements

- Home Assistant 2025.12.0 or newer
- HACS (Home Assistant Community Store) installed
- Existing cover entities to control

---

## Installation

### Method 1: HACS (Recommended)

#### Step 1: Add Custom Repository

1. Open Home Assistant
2. Navigate to **HACS** in the sidebar
3. Click on **Integrations**
4. Click the **three dots menu** (top right corner)
5. Select **Custom repositories**
6. In the dialog:
   - **Repository:** `https://github.com/crandler/CoverAutomatic`
   - **Category:** `Integration`
7. Click **Add**

#### Step 2: Install the Integration

1. In HACS Integrations, click **+ Explore & Download Repositories**
2. Search for **CoverAutomatic**
3. Click on it and then click **Download**
4. Select the latest version and confirm

#### Step 3: Restart Home Assistant

1. Go to **Settings** > **System** > **Restart**
2. Click **Restart** and wait for Home Assistant to come back online

#### Step 4: Add the Integration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **CoverAutomatic**
4. Follow the setup wizard:
   - Enter a name for the integration
   - Add your facades (building sides by cardinal direction)
   - Select the cover entities you want to automate
   - Optionally configure temperature sensors

---

### Method 2: Manual Installation

1. Download the latest release from GitHub
2. Extract and copy the `custom_components/cover_automatic` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via **Settings** > **Devices & Services** > **Add Integration**

---

## Configuration

After installation, the setup wizard will guide you through:

1. **Facades** - Define your building facades by cardinal direction (North, East, South, West)
2. **Covers** - Select which cover entities to manage
3. **Sensors** - Optionally add temperature sensors for intelligent rules

### Created Entities

For each managed cover, the integration creates:

| Entity | Description |
|--------|-------------|
| `switch.*_auto` | Enable/disable automation |
| `sensor.*_status` | Current status (auto/paused/manual/locked) |
| `number.*_pause_duration` | Pause duration after manual override |

For each facade:
| Entity | Description |
|--------|-------------|
| `sensor.*_sun` | Sun on facade indicator (on/off) |
| `sensor.*_sun_entry` | Time when sun enters facade |
| `sensor.*_sun_exit` | Time when sun leaves facade |

Global:
- `select.cover_automatic_scenario` - Active scenario selector

Note: The integration controls your original cover entities directly. No wrapper entities are created.

### Available Services

| Service | Description |
|---------|-------------|
| `cover_automatic.pause` | Pause automation for a cover |
| `cover_automatic.resume` | Resume automation for a cover |
| `cover_automatic.pause_all` | Pause all covers |
| `cover_automatic.resume_all` | Resume all covers |
| `cover_automatic.set_scenario` | Set active scenario |
| `cover_automatic.export_config` | Export configuration to YAML |
| `cover_automatic.import_config` | Import configuration from YAML |

---

## Version

1.0.27

## Changelog

### 1.0.27 (2026-02-19)

- Validate active_scenario on import: reset to first available if referenced scenario missing
- Add missing `facade` translation key in rule_condition step (en.json + de.json)
- Add Voluptuous schemas for all service registrations (pause, resume, set_scenario, export, import)
- Add file size limit (1 MB) for YAML import to prevent resource exhaustion
- Add input length validation (max 255 chars) for name fields in config flow
- Validate condition_operator in Rule.from_dict: reject invalid values, default to "and"
- Extend CI ruff check to include tests/ directory
- Bump min HA version to 2025.1.0 in hacs.json
- Fix service test helpers to accept schema kwargs
- Add 14 new tests: condition_operator validation, azimuth normalization, file size limit, pause_all/resume_all, import scenario validation (249 total)

### 1.0.26 (2026-02-19)

- Remove 10 unused constants from `const.py` (dead code cleanup)
- Add scenario validation in `select.py`: reject invalid scenario selections
- Fix German Umlaute in `config_flow.py` UI labels (10 labels corrected)
- Add comprehensive `test_config_flow.py` (53 new tests for ConfigFlow + OptionsFlow)
- Update existing select platform test for new validation behavior

### 1.0.25 (2026-02-19)

- Fix OptionsFlow: remove deprecated manual `self.config_entry` assignment (HA 2025.12+ compatibility)
- Fix DataUpdateCoordinator: pass `config_entry` explicitly to `super().__init__()` (HA 2026.8 deprecation)
- Migrate `hass.data[DOMAIN]` to `entry.runtime_data` with typed dataclass
- Add missing `strings.json` keys: `condition_operator`, `rules_disabled`, error messages
- Fix `de.json` umlaut: `muessen` -> `müssen`
- Remove dead code: `is_sun_above_horizon()`, `DEFAULT_SCENARIOS`, `PLATFORMS`
- Update CI to Python 3.12/3.13

### 1.0.24 (2026-02-14)

- Harden facade azimuth: normalize values to 0-360 range in `Facade.from_dict()`
- Fix import: preserve current active_scenario when not present in import data
- 182 unit tests

### 1.0.23 (2026-02-14)

- Fix sensor crash: protect facade sun entry/exit sensors against `get_facade_sun_times()` exceptions
- 182 unit tests

### 1.0.22 (2026-02-14)

- Fix pre-lock state restoration: eliminate double-pop in sync and unlock paths
- Fix orphan cleanup: include `_pre_lock_states` and `_last_command_time` in full refresh
- Fix manual override detection: keep last valid position on parse error instead of deleting
- Fix settle time: use monotonic clock instead of wall clock to prevent NTP drift issues
- Fix shutdown data loss: flush pending debounced save before cancelling task
- Fix coordinator shutdown on failed unload: ensure cleanup even when platforms fail
- Fix `pause_cover` API: renamed from private `_pause_cover` to public method
- Fix export/import I/O: catch `OSError` and `yaml.YAMLError` with proper logging
- Fix switch turn_off: persist MANUAL status to storage instead of only in-memory
- Fix sensor facade handling: return "unknown" when facade_id missing from data
- Fix comfort mode boundary: use `>=`/`<=` for cooling/heating thresholds (no dead zone)
- Fix offset type validation: protect `time_after_sunrise`/`sunset` against non-numeric offset
- Fix facade azimuth validation: reject equal start/end values in config flow
- 182 unit tests

### 1.0.21 (2026-02-14)

- Fix rule deletion: clean up stale references in scenario `rules_disabled` lists
- Fix import data mutation: deep copy imported data to prevent external corruption
- Fix import validation: validate all sub-elements via `from_dict`, skip corrupt entries
- Fix import: preserve global settings (sensors, comfort temps) not present in import data
- Fix debounced save: reset `_save_task` to None in finally block to prevent stale refs
- Fix comfort temperature validation: reject min >= max with user-facing error message
- Fix config flow cache: invalidate cover deserialization cache after raw mutation
- Fix config flow: protect against invalid ConditionType values with graceful redirect
- Fix scenario editing: preserve `rules_disabled` when form field is not submitted
- Fix sun position: return None when sun entity attributes are missing (not 0,0)
- Fix services KeyError: safe `.get()` access for `hass.data[DOMAIN]`
- Fix config export/import paths: allow `config_dir` as valid base directory
- Fix unload entry: safe `.get()`/`.pop()` with defaults to prevent KeyError
- Fix scenario select: return `["everyday"]` fallback when no scenarios exist
- Fix time condition: end time defaults to :59 seconds for full-minute coverage
- Fix rule priority: deterministic sort by rule ID when priorities are equal
- Fix switch turn_off: set MANUAL status in coordinator immediately
- Fix sensor icon: protect against invalid CoverStatus values
- 182 unit tests

### 1.0.20 (2026-02-14)

- Fix inverted covers: position tracking now uses physical position after inversion
- Fix manual override false positives during cover movement (opening/closing states ignored)
- Fix manual override detection: tolerance-based comparison (threshold: 2%)
- Fix lock sensor priority: always applies lock position even when already locked by vent
- Fix `async_shutdown` signature: changed from sync to async def
- Fix `get_cover_status()` side effects: extracted status mutations into `_sync_cover_statuses()`
- Fix `_last_positions` tracking in all code paths (lock, hysteresis skip, same-position)
- Fix storage import validation: reject non-dict data, validate required keys
- Fix storage `get_raw_data()`: use deep copy instead of shallow copy
- Add storage deserialization cache with proper invalidation
- Fix weather mapping: moved "partlycloudy" from sunny to cloudy states, added windy states
- Fix time condition: equal start/end times now match all day
- Fix config flow: sanitize IDs with umlaut conversion and regex cleanup
- Fix config flow: added facade parameter to `sun_on_facade` condition builder
- Fix config flow: recreate default scenario when all scenarios deleted
- Fix options update listener: reload config entry for dynamic entity creation
- Fix double shutdown in `async_unload_entry`
- Fix `set_scenario` service: proper logging with found/not-found tracking
- Fix scenario select: validate active scenario against available options
- 182 unit tests

### 1.0.19 (2026-01-04)

- Fix Lock/Vent race condition: lock sensor now has priority over vent sensor
- Fix memory leak: cleanup orphaned entries from `_last_positions` and `_cover_states`
- Fix AttributeError: guard against corrupt sensor states
- Fix inverted cover lock/vent position: apply inversion to lock/vent positions
- Fix scenario deletion: fallback to valid scenario when deleting active scenario
- Fix async save race condition: use lock and cancel pending debounced saves
- 182 unit tests

### 1.0.18 (2026-01-04)

- Add comprehensive integration tests for coordinator flows
- Tests cover: Happy Path, State Transitions, Hysteresis, Scenarios, Inverted Covers
- 182 unit tests (+15 integration tests)

### 1.0.17 (2026-01-04)

- Simplified scenario logic: removed `rule.scenarios` and `scenario.rules_enabled`
- Scenarios now use blacklist-only approach via `rules_disabled`
- Cleaner, more predictable rule activation logic
- Breaking change: existing `rules_enabled` and `rule.scenarios` data will be ignored

### 1.0.16 (2026-01-04)

- Fix wrap-around facade sun times calculation (north facade bug)
- Extended azimuth model range from 90-270 to 60-300 degrees for temperate latitudes
- Proper handling of wrap-around facades (e.g., north: 315-45 degrees)
- Extracted `_azimuth_to_time()` helper function for cleaner code
- 167 unit tests (+21 for sun position calculations)

### 1.0.15 (2026-01-04)

- Fix state tracking memory leak: removed entities are now properly untracked
- `refresh_state_tracking()` now performs full cleanup before re-registering listeners
- 146 unit tests (+2 for state tracking cleanup)

### 1.0.14 (2026-01-04)

- Add OR logic for rule conditions (condition_operator field)
- Rules can now use AND (all conditions must match) or OR (any condition must match)
- 144 unit tests (+6 for condition operator)

### 1.0.13 (2026-01-03)

First stable release with comprehensive test coverage.

**Core Features:**
- Facade-based sun tracking (North, East, South, West)
- Rule engine with 11 condition types (sun, temperature, time, weather, state, comfort)
- Priority-based rule matching with scenario support
- 6 default scenarios (Everyday, Summer, Winter, Vacation, Cinema, Manual)
- Manual override detection with configurable pause duration

**Sensors & Automation:**
- Lock sensor support (window contact) - locks cover when open
- Vent sensor support - moves cover to ventilation position
- Weather entity integration (sunny/cloudy/rainy conditions)
- Comfort temperature range with cooling/heating/neutral mode
- Sun entry/exit time sensors per facade
- Hysteresis (min position change, min time between changes)
- Inverted cover support (100% = closed)

**UI Configuration:**
- Full Options Flow for all settings (no YAML required)
- Facade management UI (add, edit, delete)
- Rule management UI with condition builder
- Scenario management UI with icon selector
- Scenario-rule linking (disable rules per scenario)
- Cover settings (facade, sensors, hysteresis, inverted)
- General settings (weather, temperature sensors, comfort range)

**Services:**
- pause / resume / pause_all / resume_all
- set_scenario (dynamic scenario support)
- export_config / import_config (with path validation)

**Quality:**
- 138 unit tests (models, engine, storage, coordinator, services, platforms)
- GitHub Actions CI (Python 3.11/3.12, HACS validation, Ruff linting)
- Security: Path traversal protection in import/export
- Debounced save for runtime persistence
- Translations: English and German

---

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Author

Private project by [@crandler](https://github.com/crandler)

**This is not an official product. Use at your own risk.**

---

## Development

This project was developed with AI assistance (Claude by Anthropic) under human supervision and review. All code has been reviewed and approved by a human developer before being committed.

**AI-Assisted | Human-in-the-Loop | Code Reviewed**
