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

## Screenshots

The integration ships with a custom sidebar panel that replaces the traditional Options Flow. All configuration happens inside Home Assistant, no YAML required. Click any thumbnail for the full-size view.

<table>
  <tr>
    <td width="33%">
      <a href=".github/screenshots/covers-desktop.png"><img src=".github/screenshots/covers-desktop.png" alt="Covers overview" /></a>
      <p align="center"><sub><b>Covers</b> - widget header, merged position column, status badges</sub></p>
    </td>
    <td width="33%">
      <a href=".github/screenshots/rules-desktop.png"><img src=".github/screenshots/rules-desktop.png" alt="Rules" /></a>
      <p align="center"><sub><b>Rules</b> - priority ordering, active indicators, condition chips</sub></p>
    </td>
    <td width="33%">
      <a href=".github/screenshots/scenarios-desktop.png"><img src=".github/screenshots/scenarios-desktop.png" alt="Scenarios" /></a>
      <p align="center"><sub><b>Scenarios</b> - rule sets with active highlight and per-rule toggles</sub></p>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <a href=".github/screenshots/cover-editor.png"><img src=".github/screenshots/cover-editor.png" alt="Cover editor" /></a>
      <p align="center"><sub><b>Cover editor</b> - slide-out with sections, inline toggles, collapsed hints</sub></p>
    </td>
    <td width="33%">
      <a href=".github/screenshots/settings-house.png"><img src=".github/screenshots/settings-house.png" alt="Settings - House" /></a>
      <p align="center"><sub><b>Settings - House</b> - rotation input with visual compass</sub></p>
    </td>
    <td width="33%">
      <a href=".github/screenshots/settings-automation.png"><img src=".github/screenshots/settings-automation.png" alt="Settings - Automation" /></a>
      <p align="center"><sub><b>Settings - Automation</b> - global defaults, sidebar navigation</sub></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%" align="center">
      <a href=".github/screenshots/mobile-covers.png"><img src=".github/screenshots/mobile-covers.png" alt="Mobile - Covers" width="320" /></a>
      <p><sub><b>Mobile - Covers</b> - stacked header, sticky name column</sub></p>
    </td>
    <td width="50%" align="center">
      <a href=".github/screenshots/mobile-settings.png"><img src=".github/screenshots/mobile-settings.png" alt="Mobile - Settings" width="320" /></a>
      <p><sub><b>Mobile - Settings</b> - sidebar collapses to horizontal pills</sub></p>
    </td>
  </tr>
</table>

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

1.53.2

## Changelog

Full version history is maintained in [CHANGELOG.md](CHANGELOG.md), formatted per [Keep a Changelog](https://keepachangelog.com/).

Latest release: [v1.53.2](https://github.com/crandler/CoverAutomatic/releases/tag/v1.53.2) (2026-06-08).

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
