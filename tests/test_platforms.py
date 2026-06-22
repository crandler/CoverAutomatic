"""Tests for CoverAutomatic platform entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.models import CoverConfig, CoverStatus, Facade, Scenario


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.async_request_refresh = AsyncMock()
    coordinator.get_cover_status = MagicMock(return_value=CoverStatus.AUTO)
    coordinator.resume_cover = MagicMock()

    mock_storage = MagicMock()
    mock_storage.covers = {}
    mock_storage.facades = {}
    mock_storage.scenarios = {}
    mock_storage.active_scenario = "everyday"
    mock_storage.async_add_cover = AsyncMock()
    mock_storage.async_add_scenario = AsyncMock()
    mock_storage.async_save = AsyncMock()
    mock_storage.pause_duration = 10

    coordinator.storage = mock_storage
    return coordinator


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


class TestSwitchPlatform:
    """Tests for switch platform (auto enable/disable)."""

    def test_switch_entity_properties(self, mock_coordinator) -> None:
        """Test switch entity has correct properties."""
        from custom_components.cover_automatic.switch import CoverAutomaticAutoSwitch

        mock_cover = CoverConfig(
            entity_id="cover.living_room",
            name="Living Room",
            auto_enabled=True,
        )
        mock_coordinator.storage.covers = {"cover.living_room": mock_cover}

        switch = CoverAutomaticAutoSwitch(
            mock_coordinator, "cover.living_room", "Living Room"
        )
        switch.hass = MagicMock()

        assert switch.unique_id == "cover_automatic_cover.living_room_auto"
        assert switch.is_on is True

    def test_switch_is_off_when_disabled(self, mock_coordinator) -> None:
        """Test switch is off when auto_enabled is False."""
        from custom_components.cover_automatic.switch import CoverAutomaticAutoSwitch

        mock_cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=False,
        )
        mock_coordinator.storage.covers = {"cover.test": mock_cover}

        switch = CoverAutomaticAutoSwitch(mock_coordinator, "cover.test", "Test")
        switch.hass = MagicMock()

        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_enables_automation(self, mock_coordinator) -> None:
        """Test turning on enables automation."""
        from custom_components.cover_automatic.switch import CoverAutomaticAutoSwitch

        mock_cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=False,
        )
        mock_coordinator.storage.covers = {"cover.test": mock_cover}

        switch = CoverAutomaticAutoSwitch(mock_coordinator, "cover.test", "Test")
        switch.hass = MagicMock()
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        assert mock_cover.auto_enabled is True
        mock_coordinator.storage.async_add_cover.assert_called_once_with(mock_cover)
        mock_coordinator.resume_cover.assert_called_once_with("cover.test")

    @pytest.mark.asyncio
    async def test_turn_off_disables_automation(self, mock_coordinator) -> None:
        """Test turning off disables automation."""
        from custom_components.cover_automatic.switch import CoverAutomaticAutoSwitch

        mock_cover = CoverConfig(
            entity_id="cover.test",
            name="Test",
            auto_enabled=True,
        )
        mock_coordinator.storage.covers = {"cover.test": mock_cover}

        switch = CoverAutomaticAutoSwitch(mock_coordinator, "cover.test", "Test")
        switch.hass = MagicMock()
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        assert mock_cover.auto_enabled is False
        mock_coordinator.storage.async_add_cover.assert_called_once_with(mock_cover)


class TestSensorPlatform:
    """Tests for sensor platform (status, sun on facade, sun times)."""

    def test_status_sensor_value(self, mock_coordinator) -> None:
        """Test status sensor returns correct value."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.PAUSED

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.native_value == "paused"

    def test_status_sensor_icon_auto(self, mock_coordinator) -> None:
        """Test status sensor icon for AUTO status."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.AUTO

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:robot"

    def test_status_sensor_icon_paused(self, mock_coordinator) -> None:
        """Test status sensor icon for PAUSED status."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.PAUSED

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:pause-circle"

    def test_status_sensor_icon_locked(self, mock_coordinator) -> None:
        """Test status sensor icon for LOCKED status."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.LOCKED

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:lock"

    def test_status_sensor_icon_manual(self, mock_coordinator) -> None:
        """Test status sensor icon for MANUAL status."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.MANUAL

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:hand-back-right"

    def test_status_sensor_icon_venting(self, mock_coordinator) -> None:
        """Test status sensor icon for VENTING status (regression: not help-circle)."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.VENTING

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:window-open-variant"

    def test_status_sensor_icon_wind_protected(self, mock_coordinator) -> None:
        """Test status sensor icon for WIND_PROTECTED status (regression: not help-circle)."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        mock_coordinator.get_cover_status.return_value = CoverStatus.WIND_PROTECTED

        sensor = CoverAutomaticStatusSensor(
            mock_coordinator, "cover.test", "Test"
        )
        sensor.hass = MagicMock()

        assert sensor.icon == "mdi:weather-windy"

    def test_status_sensor_all_statuses_have_icons(self, mock_coordinator) -> None:
        """Every CoverStatus must map to a real icon, never the help-circle fallback."""
        from custom_components.cover_automatic.sensor import CoverAutomaticStatusSensor

        sensor = CoverAutomaticStatusSensor(mock_coordinator, "cover.test", "Test")
        sensor.hass = MagicMock()
        for status in CoverStatus:
            mock_coordinator.get_cover_status.return_value = status
            assert sensor.icon != "mdi:help-circle", f"{status} has no icon"

    def test_facade_sun_sensor_on(self, mock_coordinator) -> None:
        """Test facade sun sensor when sun is on facade."""
        from custom_components.cover_automatic.sensor import FacadeSunSensor

        mock_coordinator.data = {
            "facades": {
                "south": {"sun_on_facade": True}
            }
        }

        sensor = FacadeSunSensor(mock_coordinator, "south", "South")
        sensor.hass = MagicMock()

        assert sensor.native_value == "on"
        assert sensor.icon == "mdi:white-balance-sunny"

    def test_facade_sun_sensor_off(self, mock_coordinator) -> None:
        """Test facade sun sensor when sun is not on facade."""
        from custom_components.cover_automatic.sensor import FacadeSunSensor

        mock_coordinator.data = {
            "facades": {
                "south": {"sun_on_facade": False}
            }
        }

        sensor = FacadeSunSensor(mock_coordinator, "south", "South")
        sensor.hass = MagicMock()

        assert sensor.native_value == "off"
        assert sensor.icon == "mdi:weather-night"

    def test_facade_sun_entry_sensor(self, mock_coordinator, mock_hass) -> None:
        """Test facade sun entry time sensor."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_facade = Facade(
            id="south",
            name="South",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        mock_coordinator.storage.facades = {"south": mock_facade}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=True)
        sensor.hass = mock_hass

        with patch(
            "custom_components.cover_automatic.sensor.get_facade_sun_times",
            return_value=("10:30", "16:45"),
        ):
            assert sensor.native_value == "10:30"
            assert sensor.icon == "mdi:weather-sunset-up"

    def test_facade_sun_exit_sensor(self, mock_coordinator, mock_hass) -> None:
        """Test facade sun exit time sensor."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_facade = Facade(
            id="south",
            name="South",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        mock_coordinator.storage.facades = {"south": mock_facade}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=False)
        sensor.hass = mock_hass

        with patch(
            "custom_components.cover_automatic.sensor.get_facade_sun_times",
            return_value=("10:30", "16:45"),
        ):
            assert sensor.native_value == "16:45"
            assert sensor.icon == "mdi:weather-sunset-down"


class TestSelectPlatform:
    """Tests for select platform (scenario selector)."""

    def test_scenario_select_options(self, mock_coordinator) -> None:
        """Test scenario select returns available options."""
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.scenarios = {
            "everyday": Scenario(id="everyday", name="Everyday"),
            "summer": Scenario(id="summer", name="Summer"),
            "winter": Scenario(id="winter", name="Winter"),
        }

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()

        options = select.options
        assert "everyday" in options
        assert "summer" in options
        assert "winter" in options

    def test_scenario_select_current_option(self, mock_coordinator) -> None:
        """Test scenario select returns current active scenario."""
        from custom_components.cover_automatic.models import Scenario
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.active_scenario = "summer"
        mock_coordinator.storage.scenarios = {
            "everyday": Scenario(id="everyday", name="Everyday"),
            "summer": Scenario(id="summer", name="Summer"),
        }

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()

        assert select.current_option == "summer"

    @pytest.mark.asyncio
    async def test_scenario_select_changes_scenario(self, mock_coordinator) -> None:
        """Test selecting a scenario changes active scenario."""
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.active_scenario = "everyday"
        mock_coordinator.storage.scenarios = {
            "everyday": Scenario(id="everyday", name="Everyday"),
            "vacation": Scenario(id="vacation", name="Vacation"),
        }

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()
        select.async_write_ha_state = MagicMock()

        await select.async_select_option("vacation")

        assert mock_coordinator.storage.active_scenario == "vacation"
        mock_coordinator.storage.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_scenario_select_rejects_invalid(self, mock_coordinator) -> None:
        """Test selecting an invalid scenario is rejected."""
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.active_scenario = "everyday"
        mock_coordinator.storage.scenarios = {
            "everyday": Scenario(id="everyday", name="Everyday"),
        }

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()
        select.async_write_ha_state = MagicMock()

        await select.async_select_option("nonexistent")

        assert mock_coordinator.storage.active_scenario == "everyday"
        mock_coordinator.storage.async_save.assert_not_called()


class TestSelectCurrentOptionFallback:
    """Tests for ScenarioSelect fallback logic when active scenario is unavailable."""

    def test_current_option_fallback_when_active_not_in_options(self, mock_coordinator) -> None:
        """Test current_option falls back to first available when active_scenario is not in options."""
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.active_scenario = "deleted_scenario"
        mock_coordinator.storage.scenarios = {
            "everyday": Scenario(id="everyday", name="Everyday"),
            "summer": Scenario(id="summer", name="Summer"),
        }

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()

        current = select.current_option
        available = select.options
        assert current == available[0]
        assert current != "deleted_scenario"

    def test_options_empty_returns_everyday_fallback(self, mock_coordinator) -> None:
        """Test options returns ['everyday'] and current_option returns 'everyday' when no scenarios exist."""
        from custom_components.cover_automatic.select import ScenarioSelect

        mock_coordinator.storage.scenarios = {}
        mock_coordinator.storage.active_scenario = None

        select = ScenarioSelect(mock_coordinator, "entry123")
        select.hass = MagicMock()

        assert select.options == ["everyday"]
        assert select.current_option == "everyday"


class TestFacadeSunSensorUnknown:
    """Tests for FacadeSunSensor returning None in edge cases."""

    def test_facade_sun_sensor_unknown_when_no_data(self, mock_coordinator) -> None:
        """Test facade sun sensor returns None when coordinator.data is None."""
        from custom_components.cover_automatic.sensor import FacadeSunSensor

        mock_coordinator.data = None

        sensor = FacadeSunSensor(mock_coordinator, "south", "South")
        sensor.hass = MagicMock()

        assert sensor.native_value is None

    def test_facade_sun_sensor_unknown_when_facade_missing(self, mock_coordinator) -> None:
        """Test facade sun sensor returns None when facade_id is absent from data."""
        from custom_components.cover_automatic.sensor import FacadeSunSensor

        mock_coordinator.data = {
            "facades": {
                "north": {"sun_on_facade": True}
            }
        }

        sensor = FacadeSunSensor(mock_coordinator, "south", "South")
        sensor.hass = MagicMock()

        assert sensor.native_value is None


class TestFacadeSunTimeSensorExceptions:
    """Tests for FacadeSunTimeSensor exception handling."""

    def test_sun_entry_sensor_returns_none_on_exception(self, mock_coordinator, mock_hass) -> None:
        """Test sun entry sensor returns None when get_facade_sun_times raises."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_facade = Facade(
            id="south",
            name="South",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        mock_coordinator.storage.facades = {"south": mock_facade}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=True)
        sensor.hass = mock_hass

        with patch(
            "custom_components.cover_automatic.sensor.get_facade_sun_times",
            side_effect=RuntimeError("test error"),
        ):
            assert sensor.native_value is None

    def test_sun_exit_sensor_returns_none_on_exception(self, mock_coordinator, mock_hass) -> None:
        """Test sun exit sensor returns None when get_facade_sun_times raises."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_facade = Facade(
            id="south",
            name="South",
            azimuth_start=135.0,
            azimuth_end=225.0,
            direction="south",
        )
        mock_coordinator.storage.facades = {"south": mock_facade}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=False)
        sensor.hass = mock_hass

        with patch(
            "custom_components.cover_automatic.sensor.get_facade_sun_times",
            side_effect=RuntimeError("test error"),
        ):
            assert sensor.native_value is None

    def test_sun_entry_sensor_returns_none_when_facade_missing(self, mock_coordinator, mock_hass) -> None:
        """Test sun entry sensor returns None when facade is not in storage."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_coordinator.storage.facades = {}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=True)
        sensor.hass = mock_hass

        assert sensor.native_value is None

    def test_sun_exit_sensor_returns_none_when_facade_missing(self, mock_coordinator, mock_hass) -> None:
        """Test sun exit sensor returns None when facade is not in storage."""
        from custom_components.cover_automatic.sensor import FacadeSunTimeSensor

        mock_coordinator.storage.facades = {}

        sensor = FacadeSunTimeSensor(mock_coordinator, "south", "South", is_entry=False)
        sensor.hass = mock_hass

        assert sensor.native_value is None
