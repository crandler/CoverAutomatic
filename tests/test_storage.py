"""Tests for CoverAutomatic storage manager."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.models import (
    CoverConfig,
    CoverStatus,
    Facade,
    Rule,
    Scenario,
)
from custom_components.cover_automatic.storage import (
    CoverAutomaticStorage,
    SAVE_DEBOUNCE_DELAY,
)


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.async_create_task = MagicMock(side_effect=lambda coro: asyncio.create_task(coro))
    return hass


@pytest.fixture
def mock_store():
    """Create mock Store instance."""
    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    return store


@pytest.fixture
def storage(mock_hass, mock_store):
    """Create storage instance with mocked store."""
    with patch(
        "custom_components.cover_automatic.storage.Store",
        return_value=mock_store,
    ):
        storage = CoverAutomaticStorage(mock_hass)
        storage._store = mock_store
        return storage


class TestStorageInitialization:
    """Tests for storage initialization."""

    def test_storage_creation(self, mock_hass, mock_store) -> None:
        """Test storage can be created."""
        with patch(
            "custom_components.cover_automatic.storage.Store",
            return_value=mock_store,
        ):
            storage = CoverAutomaticStorage(mock_hass)
            assert storage.hass == mock_hass
            assert storage._data == {}

    @pytest.mark.asyncio
    async def test_load_empty_storage(self, storage, mock_store) -> None:
        """Test loading from empty storage initializes defaults."""
        mock_store.async_load.return_value = None
        await storage.async_load()

        assert storage._data["facades"] == {}
        assert storage._data["covers"] == {}
        assert storage._data["rules"] == {}
        assert storage._data["scenarios"] == {}
        assert storage._data["active_scenario"] == "everyday"
        assert storage._data["outdoor_temp_sensor"] is None
        assert storage._data["comfort_temp_min"] == 21.0
        assert storage._data["comfort_temp_max"] == 25.0

    @pytest.mark.asyncio
    async def test_load_existing_storage(self, storage, mock_store) -> None:
        """Test loading existing data from storage."""
        existing_data = {
            "facades": {"south": {"id": "south", "name": "South"}},
            "covers": {},
            "rules": {},
            "scenarios": {},
            "active_scenario": "summer",
            "outdoor_temp_sensor": "sensor.temp",
            "comfort_temp_min": 20.0,
            "comfort_temp_max": 26.0,
        }
        mock_store.async_load.return_value = existing_data
        await storage.async_load()

        assert storage._data == existing_data
        assert storage.active_scenario == "summer"


class TestStorageProperties:
    """Tests for storage property access."""

    @pytest.mark.asyncio
    async def test_facades_property(self, storage) -> None:
        """Test facades property returns Facade objects."""
        storage._data = {
            "facades": {
                "south": {
                    "id": "south",
                    "name": "South Facade",
                    "azimuth_start": 135.0,
                    "azimuth_end": 225.0,
                    "direction": "south",
                }
            }
        }
        facades = storage.facades
        assert "south" in facades
        assert isinstance(facades["south"], Facade)
        assert facades["south"].name == "South Facade"

    @pytest.mark.asyncio
    async def test_covers_property(self, storage) -> None:
        """Test covers property returns CoverConfig objects."""
        storage._data = {
            "covers": {
                "cover.test": {
                    "entity_id": "cover.test",
                    "name": "Test Cover",
                    "status": "auto",
                }
            }
        }
        covers = storage.covers
        assert "cover.test" in covers
        assert isinstance(covers["cover.test"], CoverConfig)
        assert covers["cover.test"].status == CoverStatus.AUTO

    @pytest.mark.asyncio
    async def test_rules_property(self, storage) -> None:
        """Test rules property returns Rule objects."""
        storage._data = {
            "rules": {
                "rule1": {
                    "id": "rule1",
                    "name": "Test Rule",
                    "enabled": True,
                    "priority": 10,
                }
            }
        }
        rules = storage.rules
        assert "rule1" in rules
        assert isinstance(rules["rule1"], Rule)
        assert rules["rule1"].enabled is True

    @pytest.mark.asyncio
    async def test_scenarios_property(self, storage) -> None:
        """Test scenarios property returns Scenario objects."""
        storage._data = {
            "scenarios": {
                "summer": {
                    "id": "summer",
                    "name": "Summer Mode",
                }
            }
        }
        scenarios = storage.scenarios
        assert "summer" in scenarios
        assert isinstance(scenarios["summer"], Scenario)

    def test_active_scenario_getter_setter(self, storage) -> None:
        """Test active_scenario property getter and setter."""
        storage._data = {"active_scenario": "everyday"}
        assert storage.active_scenario == "everyday"

        storage.active_scenario = "vacation"
        assert storage.active_scenario == "vacation"
        assert storage._data["active_scenario"] == "vacation"

    def test_comfort_temp_properties(self, storage) -> None:
        """Test comfort temperature properties."""
        storage._data = {
            "comfort_temp_min": 20.0,
            "comfort_temp_max": 26.0,
        }
        assert storage.comfort_temp_min == 20.0
        assert storage.comfort_temp_max == 26.0

        storage.comfort_temp_min = 19.0
        storage.comfort_temp_max = 27.0
        assert storage._data["comfort_temp_min"] == 19.0
        assert storage._data["comfort_temp_max"] == 27.0


class TestStorageCRUD:
    """Tests for CRUD operations."""

    @pytest.mark.asyncio
    async def test_add_facade(self, storage, mock_store) -> None:
        """Test adding a facade."""
        storage._data = {"facades": {}}
        facade = Facade(
            id="east",
            name="East Facade",
            azimuth_start=45.0,
            azimuth_end=135.0,
            direction="east",
        )
        await storage.async_add_facade(facade)

        assert "east" in storage._data["facades"]
        assert storage._data["facades"]["east"]["name"] == "East Facade"
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_facade(self, storage, mock_store) -> None:
        """Test removing a facade."""
        storage._data = {
            "facades": {
                "south": {"id": "south", "name": "South"}
            }
        }
        await storage.async_remove_facade("south")

        assert "south" not in storage._data["facades"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_facade(self, storage, mock_store) -> None:
        """Test removing a facade that doesn't exist."""
        storage._data = {"facades": {}}
        await storage.async_remove_facade("nonexistent")
        mock_store.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_cover(self, storage, mock_store) -> None:
        """Test adding a cover configuration."""
        storage._data = {"covers": {}}
        cover = CoverConfig(
            entity_id="cover.bedroom",
            name="Bedroom",
        )
        await storage.async_add_cover(cover)

        assert "cover.bedroom" in storage._data["covers"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_cover(self, storage, mock_store) -> None:
        """Test removing a cover configuration."""
        storage._data = {
            "covers": {
                "cover.test": {"entity_id": "cover.test", "name": "Test"}
            }
        }
        await storage.async_remove_cover("cover.test")

        assert "cover.test" not in storage._data["covers"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_rule(self, storage, mock_store) -> None:
        """Test adding a rule."""
        storage._data = {"rules": {}}
        rule = Rule(
            id="sun_shade",
            name="Sun Shade",
            target_position=30,
        )
        await storage.async_add_rule(rule)

        assert "sun_shade" in storage._data["rules"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_rule(self, storage, mock_store) -> None:
        """Test removing a rule."""
        storage._data = {
            "rules": {
                "rule1": {"id": "rule1", "name": "Rule"}
            }
        }
        await storage.async_remove_rule("rule1")

        assert "rule1" not in storage._data["rules"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_scenario(self, storage, mock_store) -> None:
        """Test adding a scenario."""
        storage._data = {"scenarios": {}}
        scenario = Scenario(
            id="vacation",
            name="Vacation Mode",
        )
        await storage.async_add_scenario(scenario)

        assert "vacation" in storage._data["scenarios"]
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_scenario(self, storage, mock_store) -> None:
        """Test removing a scenario."""
        storage._data = {
            "scenarios": {
                "summer": {"id": "summer", "name": "Summer"}
            }
        }
        await storage.async_remove_scenario("summer")

        assert "summer" not in storage._data["scenarios"]
        mock_store.async_save.assert_called_once()


class TestRuntimeUpdates:
    """Tests for runtime update methods with debounced save."""

    def test_update_cover_status(self, storage) -> None:
        """Test updating cover status triggers debounced save."""
        storage._data = {
            "covers": {
                "cover.test": {
                    "entity_id": "cover.test",
                    "name": "Test",
                    "status": "auto",
                    "pause_until": None,
                }
            }
        }
        storage._schedule_save = MagicMock()

        storage.update_cover_status("cover.test", "paused", 1234567890.0)

        assert storage._data["covers"]["cover.test"]["status"] == "paused"
        assert storage._data["covers"]["cover.test"]["pause_until"] == 1234567890.0
        storage._schedule_save.assert_called_once()

    def test_update_cover_status_nonexistent(self, storage) -> None:
        """Test updating nonexistent cover does nothing."""
        storage._data = {"covers": {}}
        storage._schedule_save = MagicMock()

        storage.update_cover_status("cover.nonexistent", "paused")

        storage._schedule_save.assert_not_called()

    def test_update_cover_last_change(self, storage) -> None:
        """Test updating cover last change timestamp."""
        storage._data = {
            "covers": {
                "cover.test": {
                    "entity_id": "cover.test",
                    "name": "Test",
                    "last_position_change": None,
                }
            }
        }
        storage._schedule_save = MagicMock()

        timestamp = 1234567890.0
        storage.update_cover_last_change("cover.test", timestamp)

        assert storage._data["covers"]["cover.test"]["last_position_change"] == timestamp
        storage._schedule_save.assert_called_once()

    def test_get_cover_raw(self, storage) -> None:
        """Test getting raw cover data."""
        cover_data = {
            "entity_id": "cover.test",
            "name": "Test",
            "status": "auto",
        }
        storage._data = {"covers": {"cover.test": cover_data}}

        result = storage.get_cover_raw("cover.test")
        assert result == cover_data

    def test_get_cover_raw_nonexistent(self, storage) -> None:
        """Test getting raw data for nonexistent cover."""
        storage._data = {"covers": {}}
        result = storage.get_cover_raw("cover.nonexistent")
        assert result is None


class TestExportImport:
    """Tests for data export and import."""

    def test_get_raw_data(self, storage) -> None:
        """Test getting raw data for export."""
        test_data = {
            "facades": {"south": {}},
            "covers": {"cover.test": {}},
            "rules": {},
            "scenarios": {},
            "active_scenario": "everyday",
        }
        storage._data = test_data

        result = storage.get_raw_data()
        assert result == test_data
        assert result is not storage._data

    @pytest.mark.asyncio
    async def test_import_data(self, storage, mock_store) -> None:
        """Test importing data with valid sub-elements."""
        import_data = {
            "facades": {
                "north": {
                    "id": "north",
                    "name": "North",
                    "azimuth_start": 315.0,
                    "azimuth_end": 45.0,
                    "direction": "north",
                }
            },
            "covers": {},
            "rules": {},
            "scenarios": {},
            "active_scenario": "winter",
        }
        await storage.async_import_data(import_data)

        assert storage._data["active_scenario"] == "winter"
        assert "north" in storage._data["facades"]
        mock_store.async_save.assert_called_once()


class TestDebouncedSave:
    """Tests for debounced save mechanism."""

    def test_schedule_save_creates_task(self, storage, mock_hass) -> None:
        """Test _schedule_save creates a task."""
        storage._save_task = None
        mock_hass.async_create_task = MagicMock(return_value=MagicMock())
        storage._schedule_save()

        assert storage._save_task is not None
        mock_hass.async_create_task.assert_called_once()

    def test_schedule_save_cancels_previous_task(self, storage, mock_hass) -> None:
        """Test _schedule_save cancels previous task."""
        mock_task = MagicMock()
        storage._save_task = mock_task
        mock_hass.async_create_task = MagicMock(return_value=MagicMock())
        storage._schedule_save()

        mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_debounced_save_waits_and_saves(self, storage, mock_store) -> None:
        """Test _debounced_save waits before saving."""
        storage._data = {"test": "data"}

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await storage._debounced_save()

            mock_sleep.assert_called_once_with(SAVE_DEBOUNCE_DELAY)
            mock_store.async_save.assert_called_once_with(storage._data)

    @pytest.mark.asyncio
    async def test_debounced_save_handles_cancellation(
        self, storage, mock_store
    ) -> None:
        """Test _debounced_save handles cancellation gracefully."""
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
            await storage._debounced_save()

        mock_store.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_debounced_save_handles_errors(
        self, storage, mock_store
    ) -> None:
        """Test _debounced_save handles save errors."""
        mock_store.async_save.side_effect = Exception("Save failed")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await storage._debounced_save()
