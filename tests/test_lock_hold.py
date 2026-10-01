"""Tests for the per-cover "keep position when the window opens" lock option."""
# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from custom_components.cover_automatic.coordinator import CoverAutomaticCoordinator
from custom_components.cover_automatic.models import CoverConfig, CoverStatus
from tests.test_coordinator import (  # noqa: F401 -- pytest fixtures
    MockState,
    coordinator,
    mock_hass,
    mock_storage,
)


class _Cover(MockState):
    def __init__(self, position: int) -> None:
        super().__init__("open")
        self.attributes = {"current_position": position}


def _raw(hold: bool) -> dict:
    return {
        "auto_enabled": True, "lock_sensor": "binary_sensor.window", "lock_position": 100,
        "vent_sensor": None, "inverted": False, "lock_hold_position": hold,
    }


class TestModel:
    def test_default_and_roundtrip(self) -> None:
        cover = CoverConfig(entity_id="cover.t", name="T")
        assert cover.lock_hold_position is False
        cover.lock_hold_position = True
        assert CoverConfig.from_dict(cover.to_dict()).lock_hold_position is True


class TestLockMoves:
    @pytest.mark.parametrize(
        ("hold", "current", "expected"),
        [(False, 20, True), (False, None, True), (False, 100, False), (True, 20, False), (True, None, False)],
    )
    def test_lock_moves(self, hold, current, expected) -> None:
        assert CoverAutomaticCoordinator._lock_moves(_raw(hold), current, 100) is expected


class TestSensorEvent:
    @pytest.mark.parametrize(("hold", "moved"), [(True, False), (False, True)])
    def test_window_opens(self, coordinator, mock_hass, mock_storage, hold, moved) -> None:
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        mock_storage.get_cover_raw.return_value = _raw(hold)
        mock_hass.states.get.return_value = _Cover(20)
        with patch.object(coordinator, "_lock_cover") as lock:
            coordinator._handle_contact_sensor_change(
                "binary_sensor.window", ["cover.t"], [], MockState("off"), MockState("on"),
            )
        assert lock.called is moved
        if not moved:  # _lock_cover (mocked here) sets LOCKED itself when moving
            assert coordinator._cover_states["cover.t"] == CoverStatus.LOCKED


class TestSync:
    @pytest.mark.parametrize(("hold", "moved"), [(True, False), (False, True)])
    def test_sync_locks(self, coordinator, mock_hass, mock_storage, hold, moved) -> None:
        mock_storage._data = {"covers": {"cover.t": _raw(hold)}}
        mock_storage.get_cover_raw.return_value = mock_storage._data["covers"]["cover.t"]
        mock_hass.states.get.side_effect = lambda eid: MockState("on") if eid.startswith("binary_sensor") else _Cover(20)
        mock_hass.async_create_task = MagicMock()
        with patch.object(coordinator, "_lock_cover", wraps=coordinator._lock_cover) as lock, \
                patch("custom_components.cover_automatic.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value.timestamp.return_value = 1000.0
            coordinator._sync_cover_statuses()
        assert coordinator._cover_states["cover.t"] == CoverStatus.LOCKED
        assert lock.called is moved
