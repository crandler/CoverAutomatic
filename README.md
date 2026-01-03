# CoverAutomatic

Home Assistant custom integration for intelligent, automated control of covers (shutters, blinds, roller blinds).

## Features

- **Sun-based automation** - Automatic shading when sun hits facade
- **Temperature control** - React to indoor/outdoor temperatures
- **Time schedules** - Open/close at specific times or relative to sunrise/sunset
- **Scenarios** - Switch between modes like "Summer", "Winter", "Vacation"
- **Manual override** - Automatic pause after manual intervention
- **UI-first configuration** - Full setup via Home Assistant UI
- **Device agnostic** - Works with any cover entity (Homematic IP, Shelly, etc.)

## Requirements

- Home Assistant 2024.1.0 or newer
- Existing cover entities to control

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots menu, then "Custom repositories"
4. Add this repository URL
5. Install "CoverAutomatic"
6. Restart Home Assistant

### Manual

1. Copy `custom_components/cover_automatic` to your `config/custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "CoverAutomatic"
4. Follow the setup wizard

## Documentation

See [Design Document](docs/plans/2026-01-03-cover-automatic-design.md) for detailed architecture and concepts.

## Version

0.2.0

## Changelog

### 0.2.0 (2026-01-03)
- Add config flow for UI-based setup with multi-step wizard
- Support facade configuration by direction (North, East, South, West)
- Cover entity selection with multi-select
- Optional temperature sensor configuration
- Options flow for scan interval adjustment

### 0.1.0 (2026-01-03)
- Initial project setup
- Design document created

## License

MIT License
