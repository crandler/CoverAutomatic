# CoverAutomatic - Design Document

## Overview

Home Assistant custom integration for intelligent, automated control of covers (shutters, blinds, roller blinds) based on time, sun position, and indoor/outdoor temperatures.

**Key Goals:**
- Energy efficiency (heat protection in summer, solar gain in winter)
- Comfort and privacy (automatic open/close based on daylight)
- Sun/glare protection (prevent direct sunlight on workspaces)
- Flexible, intuitive configuration via UI

## Architecture

```
CoverAutomatic
├── Facades              # Grouping by cardinal direction
├── Cover Entities       # Individual covers with automation state
├── Rules                # Intelligent automation conditions
├── Scenarios            # Modes like "summer", "winter", "vacation"
└── Automation Engine    # Evaluates rules, controls covers
```

### Entities Created

| Entity | Type | Purpose |
|--------|------|---------|
| `cover_automatic.{name}` | Cover | Wrapper with automation status |
| `switch.cover_automatic_{name}_auto` | Switch | Enable/disable automation per cover |
| `select.cover_automatic_scenario` | Select | Active scenario |
| `sensor.cover_automatic_sun_facade_{name}` | Sensor | Sun on facade indicator |
| `sensor.cover_automatic_{name}_status` | Sensor | Status: auto/paused/manual |
| `number.cover_automatic_{name}_pause` | Number | Pause duration config |

## Facades

Facades group covers by cardinal direction and define when sun exposure occurs.

| Facade | Azimuth Range | Typical Sun Exposure |
|--------|---------------|---------------------|
| North  | 315° - 45°    | Rarely direct       |
| East   | 45° - 135°    | Morning             |
| South  | 135° - 225°   | Midday              |
| West   | 225° - 315°   | Afternoon/Evening   |

**Data Model:**
```yaml
facade:
  id: "south"
  name: "South Side"
  azimuth_start: 135
  azimuth_end: 225
  min_elevation: 0
  covers: [...]
```

Covers can be assigned to exactly one facade. Covers without facade (e.g., skylights) only use time/temperature logic.

## Rules

Rules combine conditions with actions. All conditions must be met (AND logic).

**Structure:**
```yaml
rule:
  id: "summer_heat_protection"
  name: "Heat Protection Summer"
  enabled: true
  priority: 10
  scenarios: ["summer"]

  conditions:
    - type: "sun_on_facade"
      facade: "south"
    - type: "temperature_above"
      sensor: "sensor.outdoor_temp"
      value: 25
    - type: "temperature_above"
      sensor: "sensor.living_room_temp"
      value: 23
    - type: "time_between"
      start: "10:00"
      end: "20:00"

  action:
    position: 30
```

**Available Condition Types:**
- `sun_on_facade` - Sun shining on facade
- `sun_elevation_above/below` - Sun elevation threshold
- `temperature_above/below` - Temperature threshold
- `time_between` - Time window
- `time_after_sunrise/sunset` - Relative to sunrise/sunset
- `state_is` - Any HA entity state check

**Rule Evaluation:**
- Rules checked on relevant sensor changes
- Highest priority wins on conflicts
- No matching rule = position unchanged

## Scenarios

Predefined modes that enable/disable rule sets.

| Scenario | Description | Typical Rules |
|----------|-------------|---------------|
| `everyday` | Normal operation | All standard rules |
| `summer` | Heat protection focus | Aggressive shading on heat |
| `winter` | Energy gain focus | Let sun warmth in, insulate at night |
| `vacation` | Presence simulation | Random movements, closed at night |
| `cinema` | Entertainment | All covers closed |
| `manual` | Automation off | No automatic control |

**Data Model:**
```yaml
scenario:
  id: "summer"
  name: "Summer Mode"
  icon: "mdi:white-balance-sunny"
  rules_enabled: ["heat_protection", "morning_open", "evening_close"]
  rules_disabled: ["winter_solar_gain"]
```

## Manual Override

Detection of manual interventions (HA UI, physical switches, other automations).

**Pause Mechanism (per cover):**
```yaml
cover_settings:
  id: "living_room_south"
  manual_override:
    enabled: true
    pause_duration: 120  # minutes
    resume_trigger: "next_rule"
```

**Services:**
- `cover_automatic.pause` - Pause automation
- `cover_automatic.resume` - Resume automation
- `cover_automatic.pause_all` - Pause all covers
- `cover_automatic.resume_all` - Resume all covers

## Configuration UI

### Config Flow (Setup Wizard)

1. **Basic Setup** - Integration name, confirm location
2. **Define Facades** - Add facades with cardinal direction
3. **Assign Covers** - Select cover entities, assign to facades
4. **Sensors (optional)** - Outdoor/indoor temperature sensors
5. **Done** - Default rules created

### Options Flow

All settings modifiable after setup:
- Edit facades and cover assignments
- Add/edit/delete rules
- Manage scenarios

### YAML Import/Export

- `cover_automatic.export_config` - Save to `/config/cover_automatic_backup.yaml`
- `cover_automatic.import_config` - Load from file

## File Structure

```
custom_components/cover_automatic/
├── __init__.py           # Integration setup
├── manifest.json         # Metadata, dependencies
├── const.py              # Constants, defaults
├── config_flow.py        # UI configuration
├── coordinator.py        # Data coordinator (central logic)
├── engine.py             # Rule evaluation, sun calculation
├── models.py             # Data classes (Facade, Rule, Scenario)
├── cover.py              # Cover platform (wrapper entities)
├── switch.py             # Auto switches per cover
├── select.py             # Scenario selector
├── sensor.py             # Status sensors
├── number.py             # Pause duration entities
├── services.yaml         # Service definitions
├── services.py           # Service handlers
├── strings.json          # UI texts (EN)
└── translations/
    └── de.json           # German translations
```

## Dependencies

- Home Assistant Core only (no external packages)
- Uses `sun.sun` entity for sun position
- Uses `astral` (included in HA) for calculations

## Storage

- Configuration in `.storage/cover_automatic` (HA standard)
- No writing to `configuration.yaml`

## Future Extensions

- Jalousie support (tilt/lamella angle)
- Horizon profiles (obstacle shading)
- Weather forecast integration
- Dashboard card
