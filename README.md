<p align="center">
  <img src="custom_components/cover_automatic/brand/logo.png" alt="CoverAutomatic Logo" width="400">
</p>

<h1 align="center">CoverAutomatic</h1>

<p align="center"><strong>Custom HACS integration for Home Assistant - intelligent, automated control of covers (shutters, blinds, roller blinds).</strong></p>

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

- Home Assistant 2025.1.0 or newer
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

1.11.0

## Changelog

### 1.34.2 (2026-04-05)

- Improve: sensors settings section uses 2-column grid layout (responsive)

### 1.34.1 (2026-04-05)

- Fix: settings section header text left-aligned next to icon instead of spread apart

### 1.34.0 (2026-04-05)

- Add: Lucide SVG icons for settings section headers (house, sensors, comfort, wind, automation, backup)

### 1.33.5 (2026-04-05)

- Fix: hysteresis badge ("too short"/"too small") persisted on covers after status changed to paused/locked/wind-protected

### 1.33.4 (2026-04-05)

- Fix: cover falsely paused after HA restart (unavailable state during shutdown triggered manual override detection)

### 1.33.3 (2026-04-05)

- Fix: position bar fill invisible (span needs display:block for height/width to work)

### 1.33.2 (2026-04-05)

- Fix: resume syncs expected position to current, preventing immediate re-pause by apply cycle override check

### 1.33.1 (2026-04-05)

- Fix: position bar fill color changed to bright blue (#5bb8f5) for clear visibility on dark themes

### 1.33.0 (2026-04-05)

- Fix: manual override now detected in apply cycle (catches overrides missed during settle time)
- Test: 2 new tests for apply-cycle override detection (454 total)

### 1.32.10 (2026-04-05)

- Fix: position bar fill now green (#4CAF50) with darker track for clear contrast on all themes

### 1.32.9 (2026-04-05)

- Fix: position bar track more visible (wider, higher contrast, subtle border)

### 1.32.8 (2026-04-05)

- Fix: duplicate hysteresis badge (initial render missing `hysteresis-badge` class, live update added second)

### 1.32.7 (2026-04-05)

- Fix: table column headers no longer wrap (white-space: nowrap on all th)

### 1.32.6 (2026-04-05)

- Fix: facade name + sun icon no longer wraps in covers table (white-space: nowrap)

### 1.32.5 (2026-04-05)

- Fix: hysteresis badge stays inline next to target position bar

### 1.32.4 (2026-04-05)

- Fix: resume X stays inline with paused badge and timer (no line break)

### 1.32.3 (2026-04-05)

- Fix: paused status resume button replaced with compact X icon next to badge

### 1.32.2 (2026-04-05)

- Fix: increased spacing between version label and update badge in header

### 1.32.1 (2026-04-05)

- Feat: position columns show visual progress bars with percentage labels
- Live updates animate bar width smoothly via CSS transition

### 1.32.0 (2026-04-05)

- Feat: entire cover table row is now clickable to open slide-out (not just name/facade cells)
- Feat: delete button moved from table to slide-out panel bottom (prevents accidental deletes)
- Remove: actions column from covers table (one less column)

### 1.31.3 (2026-04-05)

- Fix: facade card grid limited to 2 columns for better spacing of icons and buttons
- Fix: reverted header to single row layout (sun info inline with controls)

### 1.31.1 (2026-04-05)

- Fix: sun/moon info bar moved into header (right-aligned), all sun/moon icons replaced with SVGs
- Fix: `_sunIconSvg()` helper for consistent sun icon rendering across all views

### 1.31.0 (2026-04-05)

- Feat: global info bar with sun position and outdoor temperature (visible on all tabs)
- Feat: update badge moved next to version number in header
- Remove: redundant sun info bar from facades tab (replaced by global bar)
- Remove: redundant comfort icons from cover name column (temp color already indicates mode)

### 1.30.3 (2026-04-05)

- Remove: redundant comfort icons from cover name column (temp color already indicates mode)

### 1.30.2 (2026-04-05)

- Fix: heating comfort icon changed from thermometer to flame

### 1.30.1 (2026-04-05)

- Fix: comfort icons improved (cooling = blue snowflake, heating = red thermometer, neutral = no icon)
- Fix: sun-on-facade icon now yellow with proper styling instead of generic star
- Fix: venting status now has its own badge style (indigo) instead of unstyled text
- Fix: temperature color for heating mode changed from orange to red

### 1.30.0 (2026-04-05)

- Feat: real-time status updates via event push (coordinator fires `cover_automatic_updated` event, panel subscribes)
- Feat: immediate data refresh on covers tab switch (no more 30s wait)
- Fix: language change not detected, required F5 to apply translations
- Fix: resume button disappeared after live cell update when cover was paused

### 1.29.2 (2026-04-04)

- Fix: consistent null-safe pattern for globalPause placeholder in panel
- Test: first-eval comfort mode boundary tests (4 cases)
- Test: from_dict nullable fields roundtrip test

### 1.29.1 (2026-04-04)

- Fix: comfort mode first-evaluation used hysteresis-extended boundaries, causing false COOLING/HEATING on restart
- Fix: per-cover fields (lock_position, vent_position, min_position_change, min_time_between_changes) could not be cleared to use global defaults
- Fix: pause_duration API schema rejected null values

### 1.29.0 (2026-04-03)

- Feature: configurable command stagger delay for radio-based systems (Z-Wave, Zigbee)
- Fix: falsy-0 bug in panel for min_elevation and target_position fields (value 0 was lost)
- Fix: null crash on backup-import button when file input element missing
- Fix: memory leak in panel disconnectedCallback (save timers not cleared)
- Fix: XSS hardening in panel _hint() function (escape translation text)
- Fix: engine condition error logging now includes full traceback
- Fix: settings API rejects non-existent scenario IDs for active_scenario

### 1.28.3 (2026-04-03)

- Feature: facades sorted by azimuth (clockwise from north)

### 1.28.2 (2026-04-03)

- Fix: version label spacing from title in header

### 1.28.1 (2026-04-03)

- Feature: sortable cover table columns (name, facade, status, temperature) with click-to-sort headers

### 1.28.0 (2026-04-03)

- Fix: confirm dialog used transparent background, now solid with darker overlay

### 1.27.9 (2026-04-03)

- Fix: clear log button called non-existent _confirm instead of _showConfirm

### 1.27.8 (2026-04-03)

- Fix: skip position application on first refresh after startup to avoid unnecessary cover movements from incomplete sensor data

### 1.27.7 (2026-04-03)

- Compass: wider light cone, extended 20px further, solid house background

### 1.27.6 (2026-04-03)

- Compass: light cone extends behind house, house rendered on top so sun does not shine through

### 1.27.5 (2026-04-03)

- Compass: house shape with sharp corners, uniform stroke width for roof indicator
- Compass: sun elevation label moved further away from sun symbol

### 1.27.4 (2026-04-03)

- Fix: cover edit slide panel had transparent background on themes with semi-transparent card colors
- Feature: clear log button in protocol tab with confirmation dialog

### 1.27.3 (2026-04-03)

- Panel: active rule indicators more prominent with green left border, tinted background, and glowing dot

### 1.27.2 (2026-04-03)

- Fix: settings tab crash due to svgH variable used before initialization in compass SVG

### 1.27.1 (2026-04-03)

- Compass: sun elevation label prefixed with angle symbol to distinguish from temperature
- Compass: outdoor temperature shown below compass when sensor configured

### 1.27.0 (2026-04-03)

- Fix: hamburger menu click handler was in _handleChange instead of _handleClick (never fired for buttons)

### 1.26.9 (2026-04-03)

- Fix: hamburger menu toggles HA sidebar by directly setting ha-drawer.open property

### 1.26.8 (2026-04-03)

- Cache busting: panel JS URL includes version query parameter to prevent stale browser cache

### 1.26.7 (2026-04-03)

- Fix: hamburger menu dispatches event on home-assistant element to cross shadow DOM boundaries

### 1.26.6 (2026-04-03)

- Add hamburger menu button on mobile to toggle HA sidebar navigation
- Fixes inability to navigate away from panel on mobile devices

### 1.26.5 (2026-04-02)

- Compass: sun symbol moved further out (r+28) to avoid overlapping cardinal direction letters
- Compass: SVG enlarged to 280x288 with centered compass at 140,140

### 1.26.4 (2026-04-02)

- Compass: sun symbol moved further out from compass ring (r+14 instead of r+2)
- Compass: facade labels allow 8 chars (fixes "Süd-Os" truncation to "Süd-Ost")
- Compass: SVG enlarged to 250x258 for more room around edges

### 1.26.3 (2026-04-02)

- Compass: sun light cone (trapezoid) instead of parallel lines, illuminates full facade width

### 1.26.2 (2026-04-02)

- Compass: fix S label clipped by expanding SVG viewBox height
- Compass: sun symbol with radiating rays instead of plain circle
- Compass: light beams from sun toward house showing illumination direction
- Compass: sun elevation label moved below symbol for better readability
- Settings: add unit (%) to min. position change label and hint

### 1.26.1 (2026-04-02)

- Remove all inline CSS from settings tab, live cells, and cover table; replace with CSS classes
- Add `settings-hint-intro`, `settings-hint`, `sensor-current-value`, `pause-remaining`, `hysteresis-badge`, `live-icon` CSS classes
- Add `align-items: start` to `.form-row` to prevent height coupling between columns
- Add `border-bottom` separator and corrected padding to `.settings-stack .card-header`
- Extract house card layout into `.settings-house-layout/input/compass` utility classes
- Move hysteresis field out of 3-column `form-row` into standalone `form-group`
- Use `hintIntro` for section-level hints (Comfort, Wind, Backup) vs `hint` for field-level hints
- Remove redundant `cursor:pointer` inline style from cover table cells

### 1.26.0 (2026-04-02)

- Settings tab redesign: 6 separate cards with logical grouping (House, Sensors, Comfort, Wind, Automation, Backup)
- Workday sensor moved into Sensors card for better discoverability
- Replaced inline section headers with proper card layout

### 1.25.2 (2026-04-02)

- Temperature column colored by comfort mode (blue=cooling, orange=heating) with tooltip

### 1.25.1 (2026-04-02)

- Show indoor temperature from assigned sensor in covers table (with live updates)

### 1.25.0 (2026-04-02)

- Export/import configuration via panel settings (JSON download/upload)
- WebSocket API: `cover_automatic/export` and `cover_automatic/import` endpoints

### 1.24.0 (2026-04-02)

- Workday condition: selectable state (on/off) to match workdays or non-workdays
- Translated select option labels in condition parameters

### 1.23.2 (2026-04-02)

- Workday condition uses global sensor automatically (no manual entity_id input)

### 1.23.1 (2026-04-02)

- Global workday sensor setting with live status display
- Workday condition falls back to global sensor when no entity_id specified

### 1.23.0 (2026-04-02)

- New condition type: `workday` -- use a HA workday binary sensor to match workdays/holidays

### 1.22.2 (2026-04-02)

- Fix: sun/comfort icon tooltips not updated by live refresh (stayed in initial render language)

### 1.22.1 (2026-04-02)

- Fix: hysteresis icons in target column lose tooltips after live update (DOM rebuild)
- Fix: sun-on-facade icon tooltip was hardcoded English instead of translated

### 1.22.0 (2026-04-02)

- Global defaults for lock/vent tilt positions in settings
- Per-cover comfort_temp_min/max now settable via WS API
- Fix: pause_cover falsy-0 when cover.pause_duration is explicitly 0
- Fix: per-cover indoor_temp_sensor now tracked for state changes (was only global)
- Fix: import preserves all global settings (enabled, pause_duration, tilt positions, etc.)
- Fix: unique ID generation prevents silent overwrites on name collisions
- Fix: number entity crash when cover.pause_duration is None (global fallback)
- Fix: _sync_cover_statuses vent path now updates position tracking (prevents redundant service calls)
- Fix: _sync_cover_statuses lock path now uses global tilt fallback

### 1.21.1 (2026-04-01)

- Fix: scenario icons now rendered as actual icons via ha-icon instead of plain text
- Icons shown in scenario card header and active scenario badge in panel header

### 1.21.0 (2026-04-01)

- Global defaults for lock_position, vent_position, min_position_change, min_time_between_changes
- Per-cover values now optional with fallback to global defaults (empty = use global)
- New settings fields in Automation section for all 4 parameters
- Updated cover hints to indicate global fallback behavior

### 1.20.2 (2026-04-01)

- Fix: all WS responses now include live data (active_rules, live_covers, live_facades)
- Rule active indicators, cover positions, and facade sun status no longer lost after config changes

### 1.20.1 (2026-04-01)

- Fix: adding/deleting rule conditions now auto-saves immediately (no more lost changes when collapsing rule)

### 1.20.0 (2026-04-01)

- Rule priority now determined entirely by drag order (top = wins)
- Removed manual priority number field from rule editor
- Priority auto-assigned on reorder: top rule gets highest priority
- Rules sorted highest priority first in the list
- Position badge shows #1, #2, #3 instead of P10, P20, P30

### 1.19.1 (2026-04-01)

- Fix: priority field was missing from rule editor (only shown as badge, not editable)
- Priority now editable in expanded rule editor, saved with rule data

### 1.19.0 (2026-04-01)

- Weather condition now supports multiple values (e.g. sunny + partlycloudy) via toggle buttons
- Fix: day_of_week condition type was missing from condition selector dropdown
- Engine: weather param accepts both string and array format (backwards compatible)

### 1.18.1 (2026-04-01)

- Fix: resume from pause now triggers immediate rule re-evaluation, no page refresh needed

### 1.18.0 (2026-04-01)

- Facades tab: sun position info bar (azimuth/elevation) at top
- Facades tab: sun icon on facade cards when sun is shining on them
- Settings tab: live sensor values shown next to sensor dropdowns
- Settings tab: validation prevents saving when comfort min >= max

### 1.17.0 (2026-04-01)

- Covers table: sun-on-facade indicator (sun icon next to facade name when sun is shining on it)
- Covers table: "Last change" column showing relative time since last position change
- Live facade data (sun_on_facade) exposed via WebSocket API

### 1.16.0 (2026-04-01)

- Covers table: active rule name column shows which rule is currently winning
- Covers table: comfort mode icon per cover (snowflake=cooling, sun=heating, dot=neutral)
- Covers table: resume button to cancel pause immediately
- New WebSocket command: cover_automatic/cover/resume
- Replaced "Auto Enabled" column with more useful "Rule" column

### 1.15.8 (2026-04-01)

- Fix: settings save failed because pause_duration was missing from WebSocket schema validation

### 1.15.7 (2026-04-01)

- Fix: global pause_duration default was 600 minutes (10 hours) instead of 10 minutes (typo)

### 1.15.6 (2026-04-01)

- Add covers form collapsed by default, toggle via "+ Behaenge hinzufuegen" button
- Fix: duplicate pause countdown rendering (was shown twice per cover)

### 1.15.5 (2026-04-01)

- Covers table: show remaining pause time as countdown (m:ss) next to "Paused" status badge
- Countdown updates live via HA state change propagation

### 1.15.4 (2026-04-01)

- Fix: covers table live refresh now updates only position/status cells instead of re-rendering entire tab
- Add covers form and slide-out panel no longer disrupted by auto-refresh

### 1.15.3 (2026-04-01)

- Covers table: live auto-refresh of current position (via HA state updates) and target/hysteresis (every 30s)
- Timer cleanup on tab switch and panel disconnect

### 1.15.2 (2026-04-01)

- Fix: sun_on_facade now waits for sensor data before acting after restart
- When indoor temp sensor is configured but unavailable, shading is deferred instead of blindly activated
- On first comfort evaluation, hysteresis bands conservatively assigned to prevent mode jumps

### 1.15.0 (2026-04-01)

- Covers table: current position (Ist) and target position (Soll) columns
- Covers table: hysteresis indicator when position change or time threshold blocks movement
- New "Log" tab with persistent activity log (3-day retention, survives restarts)
- Log tracks position changes, status transitions, rule matches, wind protection events
- Log filter by event type (position, status, rule, wind)
- Live cover data (target position, hysteresis state) exposed via WebSocket API

### 1.14.0 (2026-04-01)

- Configurable comfort temperature hysteresis (default changed from 0.5 to 1.0 degree)
- New setting in panel: comfort hysteresis with range 0.1-5.0
- Panel i18n: replaced "Rollo/Rollos" with generic "Behang/Behänge" (covers all types: blinds, shutters, raffstores)
- Fix: umlauts in changelog release notes

### 1.13.0 (2026-04-01)

- Global master switch toggle in panel header to enable/disable all automation
- Master switch state exposed via WebSocket API (config response + settings/update)

### 1.12.1 (2026-04-01)

- Show active rule indicator in rules tab (green dot for currently matching rules)
- Rules tab shows which rules are winning for which covers (tooltip with count)

### 1.12.0 (2026-04-01)

- Wind protection: safety feature that raises all covers when wind speed exceeds configurable threshold
- New CoverStatus `WIND_PROTECTED` with highest priority (above LOCKED)
- Global settings: wind sensor, activation threshold, configurable hysteresis
- Opt-in: only active when wind sensor is configured
- Translated status labels in cover table (EN/DE)

### 1.11.0 (2026-03-31)

- New condition type: `day_of_week` - filter rules by weekday (e.g., workdays vs weekends)
- Panel: toggle buttons for day selection with full en/de i18n

### 1.10.3 (2026-03-31)

- Fix: Lock-to-vent transition now moves cover to vent_position and updates UI (was status-only)

### 1.10.2 (2026-03-31)

- Fix: Rule edit no longer sends NaN when target_position field is empty (parseInt guard)
- Fix: Manual override log now includes expected tilt position (missing format placeholder)
- Fix: VENTING state properly restored after unlock (was incorrectly reset to AUTO)

### 1.10.1 (2026-03-31)

- Fix: Unavailable/unknown sensors ignored with warning (prevents false unlock on sensor failure)
- Fix: VENTING no longer falsely detected as manual override (prevents unwanted pause)
- Fix: Elevation/temperature value 0 no longer treated as empty (falsy value bug)
- Fix: Validate comfort_temp_min < comfort_temp_max (log warning on invalid config)

### 1.10.0 (2026-03-31)

- Global master switch to enable/disable all CoverAutomatic automation (switch.cover_automatic_master)
- Lock/vent sensors continue working when master switch is off (safety)
- Added "venting" status to translations (EN/DE)

### 1.9.1 (2026-03-31)

- Fix critical param key mismatch between panel and engine for: time_between, sun_elevation, temperature, state_is, weather_is conditions
- All conditions now accept both panel keys and legacy keys

### 1.9.0 (2026-03-31)

- Per-cover comfort temperature ranges (comfort_temp_min/max per room, fallback to global)
- Fix temperature_comfort condition to use hysteresis-aware comfort mode (consistent with sun_on_facade)
- Pause cancelled when lock/vent sensor activates (safety has priority over pause)

### 1.8.1 (2026-03-31)

- Fix comfort hysteresis: hard boundaries checked first, prevents wrong mode on large temperature jumps

### 1.8.0 (2026-03-31)

- Comfort shading: only shade in COOLING mode (above max). NEUTRAL (between min/max) now keeps current position instead of shading.
- Comfort temperature hysteresis (0.5 degree): prevents oscillation at threshold boundaries
- Detailed logging for all cover state changes, rule matches, and comfort mode transitions

### 1.7.3 (2026-03-31)

- Add detailed logging for all cover state changes (lock, vent, rule match, position move, manual override, comfort mode)

### 1.7.2 (2026-03-31)

- All cover statuses (except PAUSED with valid timer) reset to AUTO on restart, then re-derived from sensor states

### 1.7.1 (2026-03-31)

- Fix vent sensor stuck as LOCKED after upgrade: sync now corrects old LOCKED status to VENTING when only vent sensor is open

### 1.7.0 (2026-03-31)

- New VENTING status: vent sensor now sets minimum position but allows automation to continue (shading works with tilted windows)
- Lock sensor: skip redundant commands when cover is already at or above lock position
- Fix false manual override detection during lock/vent transitions

### 1.6.2 (2026-03-31)

- Fix vent sensor: only move to vent position if cover is currently below it (don't close an open cover)

### 1.6.1 (2026-03-31)

- Auto-migrate existing covers with pause_duration 120 (old default) to null (use global default)

### 1.6.0 (2026-03-31)

- Global default pause duration setting (default 10 min, was 2 min per cover)
- Per-cover pause duration is now optional, falls back to global default
- Description hints for all form fields across covers, facades, rules, and settings tabs

### 1.5.2 (2026-03-31)

- Temperature conditions now use global outdoor sensor from settings (no longer broken)
- Rename labels to "Outdoor temperature above/below" for clarity
- Fix German umlauts in settings description hints
- Fix ruff lint error (module-level import order in api.py)

### 1.5.1 (2026-03-31)

- Show current version in panel header
- Show update badge with link to release when a newer version is available on GitHub

### 1.5.0 (2026-03-31)

- Auto comfort shading: sun_on_facade condition now automatically considers indoor temperature - skips shading in heating mode to use solar heat, shades in cooling/neutral mode
- Add description hints for all settings fields (sensors, comfort range, house rotation)

### 1.4.5 (2026-03-31)

- Fix azimuth value 0 rejected as falsy when saving facades

### 1.4.4 (2026-03-31)

- Facade azimuth values are now real compass bearings (house rotation applied at config time, not runtime)
- Direction picker presets now include house rotation offset automatically
- Compass SVG shows facade arcs at their real compass positions

### 1.4.3 (2026-03-31)

- Show house rotation hint next to azimuth values in facade overview cards (e.g. "+10 Rotation")

### 1.4.2 (2026-03-31)

- Change sun elevation step to 0.5 in rule conditions and facade min elevation

### 1.4.1 (2026-03-31)

- Fix panel stuck on loading screen after config fetch (partial render skipped full render when shell had no data-region elements)

### 1.4.0 (2026-03-31)

- Refactor panel to event delegation (single click/change/input listener on shadow root)
- Add partial rendering: header, tabs, content, slide-out, and confirm dialog update independently
- Remove per-render querySelectorAll rebinding (~30 selector loops eliminated)
- Eliminate double disk writes in API handlers via save=False pattern
- Reject invalid rule conditions strictly instead of silently skipping
- Add idempotency guard for unlock to prevent double-unlock errors
- Add exception logging for tilt command failures
- Cache sensor states in contact sensor handler to reduce redundant lookups
- Reset tracked position/tilt on parse failure to prevent false manual override detection
- Reorder CI: lint runs before tests for fail-fast behavior
- Add description field to manifest.json

### 1.3.4 (2026-03-30)

- Fix rules without conditions and without cover/facade assignments triggering on all covers

### 1.3.3 (2026-03-30)

- Add live compass visualization for house rotation with sun position and facade arcs

### 1.3.2 (2026-03-30)

- Enforce exclusive facade assignment: covers can only belong to one facade
- Facade editor shows current facade assignment for each cover

### 1.3.1 (2026-03-30)

- Fix facade cover assignment: bidirectional sync between facade.cover_ids and cover.facade_id

### 1.3.0 (2026-03-30)

- Add per-cover indoor temperature sensor (falls back to global setting)
- Cover sensor fields (lock, vent, indoor temp) now use entity dropdowns instead of text inputs

### 1.2.2 (2026-03-30)

- Allow negative house rotation values (-180 to 180 degrees)

### 1.2.1 (2026-03-30)

- Settings: Replace text inputs with entity dropdowns for sensor and weather selection

### 1.2.0 (2026-03-30)

- Add global house rotation setting (clockwise offset from true north)
- All facade azimuth calculations now respect house rotation
- Sun entry/exit time sensors account for house rotation

### 1.1.6 (2026-03-30)

- Add cover management: add and remove covers via panel
- Panel shows available HA cover entities for selection
- Config response includes available_covers list

### 1.1.5 (2026-03-30)

- Fix WebSocket handlers: add async_response decorator required by HA for async handlers

### 1.1.4 (2026-03-30)

- Fix panel WebSocket calls: use hass.callWS() instead of connection.sendMessagePromise()

### 1.1.3 (2026-03-30)

- Fix WebSocket command registration: pass command_type as separate argument
- Add frontend, http, websocket_api to manifest dependencies

### 1.1.2 (2026-03-30)

- Fix panel registration: use direct imports instead of deprecated hass.components accessor

### 1.1.1 (2026-03-30)

- Fix panel registration: use async_register_static_paths with StaticPathConfig (HA 2026.3 API)

### 1.1.0 (2026-03-30)

- Add custom config panel as sidebar entry, replacing Options Flow for all configuration
- Full CRUD for covers, facades, rules, scenarios and settings in a single-page panel
- Drag & drop rule priority ordering
- Inline condition editor with add, edit and delete support for all 11 condition types
- Slide-out cover detail editor with auto-save
- Dark/light mode support via HA CSS custom properties
- Responsive design (desktop table + slide-out, mobile stacked cards)
- WebSocket API backend for panel communication (13 commands)
- Config Flow simplified to zero-config (panel handles everything)
- i18n support (English default, German translation)

### 1.0.41 (2026-03-30)

- Fix covers not created in storage when no facades configured during initial setup
- Storage initialization now triggers on covers (not facades) being present in entry data

### 1.0.40 (2026-03-30)

- Simplify initial setup: 4 steps reduced to 1 (select covers + optional sensor)
- Dynamic rule conditions: 2-step flow shows only relevant fields per condition type
- Smart cover details: auto-detect tilt support, hide tilt fields for non-tilt covers
- Remove redundant name and facade steps from initial config flow
- Add rule_condition_params step for cleaner condition parameter entry
- Update translations (EN + DE) for simplified UI

### 1.0.39 (2026-03-30)

- Fix "already_in_progress" error when HA Assist or discovery starts a parallel config flow
- Remove redundant unique_id check (single_config_entry in manifest already prevents duplicates)

### 1.0.38 (2026-03-30)

- Add brand images (icon + logo, light/dark, normal/hDPI) for HA 2026.3+ native brand support
- Update CI lint to Python 3.14 (matching HA 2026.3 requirement)
- Verified full compatibility with Home Assistant 2026.3.4 (Python 3.14, 365 tests passing)

### 1.0.37 (2026-02-24)

- Remove unused constants DEFAULT_TILT_OPEN, DEFAULT_TILT_CLOSED from const.py
- Remove unused logger instances from switch.py and number.py
- Inline single-use _is_vent_sensor_open wrapper in coordinator.py
- Add vol.Length(max=255) to all name fields in edit forms (facade, rule, scenario, setup)
- Add vol.Length(max=5) to time_start/time_end and vol.Length(max=255) to state field in rule conditions
- Add MAX_CONDITIONS_PER_RULE (20) limit to prevent unbounded condition growth
- Add admin-only check for import_config and export_config services
- Add empty schema for pause_all and resume_all services
- Add .env to .gitignore for secret file prevention
- Add ruff.toml with explicit rule sets (E, F, UP, B)
- Add too_many_conditions error to all translation files
- Fix B023 loop variable binding in export_config write_yaml
- Fix 4 pre-existing E501 line-length violations (config_flow, models)
- Fix CLAUDE.md: update test count (361), add 3 missing test files, fix CI Python versions
- Add 4 admin access control tests (365 tests)

### 1.0.36 (2026-02-23)

- Fix _sync_cover_statuses: lock/vent sensors now override even when auto_enabled=False (safety)
- Fix _send_tilt_delayed: clean up _tilt_tasks reference after completion (memory leak)
- Fix async_shutdown: cancel all pending tilt tasks before teardown
- Fix scenario deletion: capture active_scenario state before removing to avoid dangling reference
- Fix Condition.from_dict: validate params is dict, shallow copy to prevent mutation
- Fix _eval_temp_comfort: always convert mode_val via str() for robust enum comparison
- Fix _eval_weather_is: resolve shadow variable in for-loop
- Add "clear" entry to _WEATHER_MAP for explicit weather matching
- Add set_cover_manual() public API, replace direct _cover_states access in switch
- Add flush_pending_save() public API, replace direct _save_task access in coordinator
- Replace storage._cache_covers with storage._invalidate_cache() in config_flow
- Replace all hasattr(entry, "runtime_data") with getattr pattern
- Add ConfigEntry type hint to async_get_options_flow signature
- Add vol.Length(max=255) to setup wizard facade name input
- Add debug logging to FacadeSunTimeSensor exception handler
- Replace TILT_FEATURE_FLAG magic number with CoverEntityFeature.SET_TILT_POSITION
- Coerce Facade.min_elevation with float() in from_dict
- Guard async_set_updated_data calls against None data
- Add homeassistant minimum version to manifest.json
- Add named tasks for async_create_task calls (debuggability)
- Add test for tilt task cancellation during shutdown (361 tests)

### 1.0.35 (2026-02-19)

- Fix rule_edit: preserve target_tilt_position when field is not in user_input (silent data loss)
- Fix _unlock_cover: persist MANUAL status to storage on unlock (was only set in memory)
- Fix switch async_turn_off: set _cover_states to MANUAL and notify entities immediately (60s delay)
- Fix resume_cover: skip resume when lock/vent sensor is still active (LOCKED override)
- Fix FacadeSunSensor: return None instead of string "unknown" (HA convention)
- Fix async_unload_entry: only remove services when platform unload succeeded
- Fix orphan cleanup: rename misleading variable "task" to "value" for non-task dicts

### 1.0.34 (2026-02-19)

- Sync strings.json with en.json: add 6 missing tilt translation keys (cover_details, rule_add, rule_edit)
- Fix _unlock_cover: restore MANUAL status when cover was manual before lock (previously fell through to AUTO)
- Fix test mocks: patch time_mod instead of dt_util in lock_cover and manual_override tests (tests passed by coincidence)
- Add test for MANUAL restore path in _unlock_cover (360 tests total)

### 1.0.33 (2026-02-19)

- Add 31 new tests closing coverage gaps identified by code review (359 total)
- Engine: sun elevation above/below, comfort mode string params and invalid fallback
- Coordinator: tilt-only update (no position change), _schedule_tilt cancellation, _update_last_position_from_state error handling
- Coordinator: vent sensor with tilt position, resume_cover assertions, _send_tilt_delayed timing
- Integration: tilt end-to-end (rule -> evaluation -> position + tilt), inverted tilt flow
- Fix misleading test comment in test_time_after_sunrise_false

### 1.0.32 (2026-02-19)

- Fix target_tilt_position=0 silently discarded in rule add/edit (falsy `or None` pattern)
- Fix target_tilt_position lost when adding condition to existing rule
- Fix stale tilt task firing after cover status change (cancel pending tilt on new command)
- Update _last_command_time after tilt delay to prevent false manual override detection
- Consolidate duplicate tilt-sending logic in async_apply_positions into single block
- Merge _is_lock_sensor_open / _is_vent_sensor_open into parameterized _is_sensor_open
- Extract BINARY_SENSOR_ON_STATES constant (replaces 5x duplicated string tuple)
- Simplify _evaluate_conditions to use any()/all() instead of manual loops
- Use _DIRECTION_OPTIONS constant in ConfigFlow initial setup (was EN, now consistent DE)
- Simplify tautological ternary for tilt position assignment in cover_details

### 1.0.31 (2026-02-19)

- Add tilt/slat control for Raffstores/Jalousien (Venetian blinds)
- Auto-detect tilt capability via HA supported_features (SET_TILT_POSITION)
- New CoverTarget dataclass: engine returns position + optional tilt_position
- Sequential command: position first, tilt via fire-and-forget task with 1.5s delay
- Per-cover tilt settings: lock_tilt_position, vent_tilt_position, inverted_tilt
- Tilt inversion support (100 - target) for covers where 100% = closed slats
- Manual override detection extended to include tilt position mismatch
- Lock/vent sensor handlers send tilt after position when configured
- Rule engine supports optional target_tilt_position per rule
- Config flow UI: tilt fields in cover details, target tilt in rule add/edit
- Full backward compatibility: all new fields have defaults, no storage migration needed

### 1.0.30 (2026-02-19)

- Fix debounced save race: guard _save_task clearing with asyncio.current_task() to prevent stale overwrites
- Harden models deserialization: validate list fields (cover_ids, facade_ids, rules_disabled) against None/non-list values
- Harden CoverConfig.from_dict: explicit type dispatch for status field (CoverStatus, str, fallback)
- Fix ComfortMode comparison in engine: explicit enum conversion prevents silent failures on value changes
- Consolidate duplicate engine methods: merge temp_above/below, sunrise/sunset, extract weather map constants
- Merge FacadeSunEntrySensor/ExitSensor into parameterized FacadeSunTimeSensor (saves ~50 lines)
- Simplify status sensor icon via lookup dict instead of str-to-enum roundtrip
- Extract direction options as module constant in config_flow (deduplicate 4 occurrences)
- Move 9 inline model imports to top-level in config_flow
- Remove dead code: unused facade_options in ConfigFlow covers step
- Simplify _get_storage() and coordinator refresh to use self.config_entry directly
- Remove 5x redundant hasattr(state, "state") checks in coordinator (HA guarantees attribute exists)
- Remove redundant `not is_open` check in elif branch, prefix unused old_state parameter
- Move is_sun_on_facade import from loop body to module top-level in coordinator
- Use DEFAULT_SCAN_INTERVAL constant instead of hardcoded 60 in __init__.py
- Simplify CoverConfig.to_dict: remove unnecessary isinstance check for status field
- HA 2026.2 compatibility verified: no breaking changes, fully compatible

### 1.0.29 (2026-02-19)

- Fix PAUSED cover status lost on HA restart (restore from persisted storage)
- Fix pre-populate LOCKED status on restart to avoid unnecessary motor commands
- Harden Rule.from_dict: skip invalid conditions instead of crashing entire rules cache
- Harden CoverConfig.from_dict: fallback to AUTO on unknown status values
- Preserve cover_ids when editing facade in options flow
- Add missing `facade` key to strings.json rule_condition step
- Add `single_config_entry: true` to manifest.json
- Update CI to Python 3.13/3.14 (drop 3.12, HA 2026.x requires >= 3.13.2)

### 1.0.28 (2026-02-19)

- Add 45 new tests closing coverage gaps across all modules (294 total)
- Coordinator: state change routing, unlock restore, manual override detection, lock/vent transition, inverted lock, orphan cleanup, shutdown save flush
- Engine: sun_on_facade facade resolution, time_after_sunrise/sunset, condition exception handling
- Storage: corrupt entry import skip, global settings preservation, facade/cover/rule removal reference cleanup
- Platforms: select fallback logic, facade sun sensor unknown states, sun time sensor exception handling
- Services: export/import happy paths, import validation errors

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
