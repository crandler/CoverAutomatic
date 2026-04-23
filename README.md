<p align="center">
  <img src="https://raw.githubusercontent.com/crandler/CoverAutomatic/main/custom_components/cover_automatic/brand/logo@2x.png" alt="CoverAutomatic Logo" width="331">
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

- Home Assistant 2026.3.0 or newer
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
4. Confirm the setup (zero-config, no input needed)
5. A new **CoverAutomatic** entry appears in the sidebar for full configuration

---

### Method 2: Manual Installation

1. Download the latest release from GitHub
2. Extract and copy the `custom_components/cover_automatic` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via **Settings** > **Devices & Services** > **Add Integration**

---

## Configuration

After installation, all configuration is done via the **CoverAutomatic** sidebar panel:

1. **Covers** - Add cover entities to manage
2. **Facades** - Define building facades by cardinal direction (with compass visualization)
3. **Rules** - Create automation rules with conditions (sun, temperature, time, weather, etc.)
4. **Scenarios** - Define modes like "Summer", "Winter", "Vacation" to disable specific rules
5. **Settings** - Configure sensors, comfort temperatures, wind protection, and more

### Created Entities

For each managed cover, the integration creates:

| Entity | Description |
|--------|-------------|
| `switch.*_auto` | Enable/disable automation |
| `sensor.*_status` | Current status (auto/paused/manual/locked/venting/wind_protected) |
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

1.45.0

## Changelog

### 1.45.0 (2026-04-23)

- UX: Settings tab is redesigned with a vertical sidebar navigation. The seven sections (House, Sensors, Comfort, Wind, Preemptive shading, Automation, Backup) can now be selected individually without scrolling through the whole page. The active section stays sticky on the left on desktop.
- UX: on mobile (< 768px) the sidebar collapses into a horizontal scrollable pill strip above the section content.
- UX: the save button now appears at the bottom of the active section only (except Backup, which has its own export/import actions).

### 1.44.0 (2026-04-23)

- UX: the "current" and "target" position columns in the cover table are merged into a single "Position" column. When current and target differ, the bar shows the current fill, a primary-colored marker at the target position, and a compact "30% → 60%" label. When they match, a normal single bar is shown.
- UX: hardcoded accent colors (sun, warning, info, danger, success) are now CSS custom properties (`--ca-sun`, `--ca-warning`, `--ca-info`, `--ca-danger`, `--ca-success-strong`). Custom HA themes can override them.
- Chore: reduced inline `style=` attributes from 41 down to 4 (remaining ones are legitimately dynamic). Replaced with a set of utility and semantic CSS classes (`.nowrap`, `.mt-16`, `.facade-meta-row`, `.rule-conditions-label`, `.sc-actions`, etc.).

### 1.43.1 (2026-04-23)

- UX: hint texts under settings and cover fields are now collapsed behind a small info icon. Click the icon to reveal the hint. The page is much easier to scan once configured.
- UX: "last change" time is now formatted naturally ("vor 1 Std. 53 Min." / "1 h 53 min ago") instead of the previous "1:53 Std." notation.
- UX: on mobile, the first column of the cover table stays visible while scrolling horizontally, so you always see which cover a row belongs to.

### 1.43.0 (2026-04-23)

- UX: redesigned the panel header info bar as a widget strip. Sun position, outdoor temperature, weather state and solar intensity each get their own pill-shaped widget with icon and tooltip, replacing the previous pipe-separated text line. Solar widget turns orange when preemptive shading is active.
- UX: individual widgets wrap cleanly on narrow viewports without breaking the layout.

### 1.42.1 (2026-04-23)

- UX: rule cards now show the target position as a small inline progress bar instead of a percent text, matching the cover table.
- UX: slide-out section headers in the cover editor now have a distinctive icon, accent color and a divider between sections for clearer hierarchy.
- UX: replaced the Material-style hamburger icon in the panel header with the matching Lucide icon for consistency with other icons.

### 1.42.0 (2026-04-22)

- UX: panel header now wraps correctly on mobile; the master switch and scenario badge are no longer pushed off-screen by the info bar.
- UX: weather state in the header is now localized (e.g. "Klare Nacht" instead of "clear-night") and paired with a Lucide weather icon.
- UX: clickable cover rows now show a chevron affordance and a stronger hover highlight so users discover the slide-out editor.
- UX: table sort arrows now only show direction on the active column; inactive columns display a neutral indicator.
- UX: active scenario card now stands out with a tinted background and colored primary glow instead of a subtle border.
- Chore: replaced several inline `style=` attributes in the panel header and info bar with reusable CSS classes.

### 1.41.2 (2026-04-22)

- UX: merged version number and update badge in the panel header into a single element to avoid duplication. When an update is available, the badge now shows both versions ("v1.41.1 -> v1.41.2") and links to the release notes of the new version.

### 1.41.1 (2026-04-22)

- UX: version number in the panel header is now a link to the release notes of the installed version on GitHub.

### 1.41.0 (2026-04-22)

- Feature: per-cover opt-out for preemptive (solar-triggered) shading. New "Preemptive shading enabled" toggle in the Sensors section of each cover. When disabled, the global solar sensor no longer triggers shading inside the comfort zone for that cover -- useful for rooms that should reach comfort temperature quickly (e.g. bathroom). Default is enabled (backward compatible).

### 1.40.0 (2026-04-19)

- Feature: write cover movements, lock/unlock, pause/resume and wind protection events to Home Assistant's built-in logbook. New setting `Write logbook entries` (default on) in the System card of the panel.

### 1.39.11 (2026-04-19)

- Fix: rule condition add/delete no longer mutates the panel config before the websocket call; on WS failure the local state stays in sync with the backend instead of silently diverging (#140)

### 1.39.10 (2026-04-19)

- Fix: pause duration number entity now resets to the global fallback when set to 0 instead of persisting 0 and breaking the per-cover fallback chain (#141)

### 1.39.9 (2026-04-19)

- Fix: wind protection deactivation now re-derives LOCKED/VENTING from sensors inline, preventing brief AUTO state and wrong position until next scan tick when a window is open (#134)
- Docs: CLAUDE.md WebSocket command count corrected to 20 (#129)
- CI: drop Python 3.13 matrix -- HA 2026.3 requires 3.14 (#130)

### 1.39.8 (2026-04-17)

- Fix: panel number inputs with comma or invalid content now safely resolve to null instead of NaN being sent to backend
- Fix: target_tilt_position from panel sends null instead of NaN when input is invalid
- Fix: facade sun time calculation errors are now logged at warning level with traceback instead of silently on debug
- Fix: cover/add API now rejects non-cover entity IDs (e.g. light.foo) at schema validation time

### 1.39.7 (2026-04-17)

- Fix: backup-import button was dead -- typo `this._shadowRoot` (should be `shadowRoot`), file picker never opened
- Fix: silent error after successful backup import -- call to nonexistent `_showSaved()` (now `_showToast()`)
- Fix: deleting the active scenario left `active_scenario` pointing at a dead ID; storage now falls back to first remaining scenario
- Fix: log entries from last 2 seconds were lost on HA shutdown -- log storage was cancelled without `async_save()`

### 1.39.6 (2026-04-17)

- Fix: falsy-0 patterns discarded legitimate zero values in panel sorting -- rules with priority=0, facades pointing north (azimuth=0), and house-rotation input "0" were treated as missing
- Chore: remove 10 unused i18n keys from panel translations (en/de)
- Chore: remove unused constant DEFAULT_COMMAND_STAGGER

### 1.39.5 (2026-04-14)

- Chore: README overhaul -- fix outdated version, HA requirement, setup instructions, status list, condense changelog

### 1.39.4 (2026-04-11)

- Chore: raise minimum Home Assistant version to 2026.3.0 (brand proxy API, StaticPathConfig, Python 3.14)

### 1.39.3 (2026-04-11)

- Chore: README logo uses absolute raw.githubusercontent.com URL and sharper @2x asset

### 1.39.2 (2026-04-11)

- Chore: new brand logo, regenerated all HA brand assets (icon, logo, dark variants in 1x/2x)

### 1.39.1 (2026-04-09)

- Fix: state-change handler now respects startup grace period (prevents false PAUSED from device reconnection after HA restart)
- Fix: positions re-synced from HA state at end of grace period (ensures correct tracking after sensor stabilization)
- Fix: tilt position synced alongside position in all sync paths (post-settle, hysteresis skip, no-move) to prevent false tilt mismatch overrides

### 1.39.0 (2026-04-09)

- Fix: manual override during VENTING not detected within settle time (cover was pushed back instead of pausing)
- Feat: vent/lock-to-vent moves now use _pending_settle mechanism for proper settle handling
- Feat: post-settle sync uses min_position_change threshold to distinguish actuator settling from manual overrides
- Feat: apply cycle skips covers during settle time to prevent overriding manual positions

### 1.38.3 (2026-04-09)

- Fix: resume_cover restores VENTING (not AUTO) when vent sensor is still open
- Fix: lock-to-vent transition syncs _last_positions when no move needed (prevents false override after manual move during LOCKED)

### 1.38.2 (2026-04-09)

- Fix: sync _last_positions when entering VENTING without move (prevents false override loop after PAUSED -> VENTING transition)

### 1.38.1 (2026-04-09)

- Fix: vent sensor closing while paused (from venting override) now immediately restores AUTO instead of leaving stale pause

### 1.38.0 (2026-04-09)

- Fix: manual overrides during VENTING status are now detected and respected (cover pauses instead of being reset)
- Fix: pause timer runs to completion while vent sensor is open, then resumes VENTING

### 1.37.0 (2026-04-09)

- Feat: solar sensor value displayed in header info bar with threshold indicator (orange highlight + arrow when exceeded)

### 1.36.0 (2026-04-08)

- Feat: preemptive shading -- configurable solar intensity sensor + threshold for early shading within comfort zone
- Feat: sun_on_facade shades in NEUTRAL comfort mode when solar intensity exceeds threshold (HEATING still blocks)
- Feat: weather entity state displayed in header info bar alongside outdoor temperature

### 1.35.0 (2026-04-07)

- Feat: startup grace period (120s) prevents wrong cover movements from incomplete sensor data after HA restart
- Feat: initialize cover positions from HA state on startup for correct override detection
- Fix: false manual override detection after own position commands (pending settle sync)
- Fix: pause expiry now syncs expected position to prevent immediate re-pause

### 1.34.0 - 1.34.4 (2026-04-05 - 2026-04-06)

- Lucide SVG icons for settings section headers
- Fix: stale comfort mode display, settings update triggers immediate re-evaluation
- Fix: time hysteresis badge shown when position already matches target
- Fix: settings section header alignment, sensors 2-column grid layout

### 1.33.0 - 1.33.5 (2026-04-05)

- Manual override detection in apply cycle (catches overrides missed during settle time)
- Position bar visual improvements (colors, display fix, inline badges)
- Resume button replaced with compact X icon
- Fix: cover falsely paused after HA restart, hysteresis badge persistence

### 1.32.0 - 1.32.10 (2026-04-05)

- Clickable cover table rows with slide-out panel
- Position columns with visual progress bars and percentage labels
- Delete button moved to slide-out panel (prevents accidental deletes)

### 1.31.0 - 1.31.3 (2026-04-05)

- Global info bar with sun position and outdoor temperature in header
- SVG icon system (`_sunIconSvg()` helper)
- Facade card grid limited to 2 columns

### 1.30.0 - 1.30.3 (2026-04-05)

- Real-time status updates via event push (coordinator fires `cover_automatic_updated`)
- Comfort icons, sun-on-facade icon styling, venting badge style
- Fix: language change detection, resume button persistence

### 1.29.0 - 1.29.2 (2026-04-03 - 2026-04-04)

- Command stagger delay for radio-based systems (Z-Wave, Zigbee)
- Fix: comfort mode first-evaluation hysteresis, nullable per-cover fields, falsy-0 bugs
- XSS hardening in panel, memory leak fix in disconnectedCallback

### 1.28.0 - 1.28.3 (2026-04-03)

- Sortable cover table columns, facades sorted by azimuth
- Fix: confirm dialog transparency

### 1.26.0 - 1.27.9 (2026-04-02 - 2026-04-03)

- Settings tab redesign: 6 cards (House, Sensors, Comfort, Wind, Automation, Backup)
- Live compass SVG with sun position, light cone, and facade arcs
- Hamburger menu for mobile sidebar navigation
- Cache busting via version query parameter
- Clear log button with confirmation dialog
- Remove all inline CSS, replace with CSS classes

### 1.22.0 - 1.25.2 (2026-04-02)

- Export/import configuration via panel settings (JSON)
- Workday condition type with global sensor
- Global defaults for lock/vent tilt positions
- Temperature column colored by comfort mode
- Indoor temperature in covers table with live updates

### 1.15.0 - 1.21.1 (2026-04-01)

- Covers table: position columns (Ist/Soll), hysteresis indicator, resume button, rule name, comfort icons
- Activity log tab with 3-day retention and type filter
- Rule priority by drag order, weather multi-select
- Global master switch, wind protection (WIND_PROTECTED status)
- Global defaults for lock/vent position, min position/time change
- Per-cover comfort temperature ranges
- Scenario icons via ha-icon

### 1.7.0 - 1.14.0 (2026-03-31 - 2026-04-01)

- VENTING status: vent sensor sets minimum position, automation continues
- Comfort shading with hysteresis (COOLING/NEUTRAL/HEATING modes)
- Day-of-week condition type
- Configurable comfort temperature hysteresis
- Detailed logging for all state changes

### 1.4.0 - 1.6.2 (2026-03-31)

- Panel refactored to event delegation with partial rendering
- Global default pause duration with per-cover fallback
- Auto comfort shading based on indoor temperature
- Compass bearings for facade azimuths with house rotation

### 1.1.0 - 1.3.4 (2026-03-30)

- Custom config panel as sidebar entry (replacing Options Flow)
- WebSocket API backend, drag & drop rule ordering
- Cover/facade management via panel
- House rotation setting, per-cover indoor temp sensor
- Bidirectional facade-cover sync

### 1.0.13 - 1.0.41 (2026-01-03 - 2026-03-30)

First stable release through pre-panel development. Core features: facade-based sun tracking, rule engine with 11 condition types, priority-based matching, scenario support, lock/vent sensors, comfort temperature system, tilt/slat control, inverted cover support. Extensive hardening: 182+ unit tests, storage robustness, race condition fixes, HA API compatibility updates, brand images, CI pipeline (Python 3.13/3.14, HACS validation, Ruff linting).

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
