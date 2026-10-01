"""Tests for target changes during travel (D) and cover travel time (E)."""
# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.cover_automatic.coordinator import (
    MAX_MEASURED_TRAVEL,
    SETTLE_TIME,
    TRAVEL_TIME_MARGIN,
)
from custom_components.cover_automatic.models import CoverConfig, CoverStatus
from tests.test_coordinator import (  # noqa: F401 -- pytest fixtures
    MockState,
    coordinator,
    mock_hass,
    mock_storage,
)
from tests.test_storage import mock_store, storage  # noqa: F401

MOD = "custom_components.cover_automatic.coordinator"


def _raw(**extra):
    raw = {"min_position_change": 1, "min_time_between_changes": 300, "inverted": False,
           "last_position_change": None}
    raw.update(extra)
    return raw


# ---------------------------------------------------------------------------
# D: own target change during travel is not a manual override
# ---------------------------------------------------------------------------

class TestTargetChangeDuringTravel:
    def _setup(self, coordinator, mock_storage, mock_hass, *, current, new_target, sent=100):
        cover = CoverConfig(entity_id="cover.salon", name="Salon")
        mock_storage.covers = {"cover.salon": cover}
        mock_storage.get_cover_raw.return_value = _raw(last_position_change=9990.0)
        coordinator._cover_states["cover.salon"] = CoverStatus.AUTO
        # Previous apply cycle sent 100 % ("Incendit"), cover still travelling
        coordinator._last_positions["cover.salon"] = sent
        coordinator._last_sent_target["cover.salon"] = sent
        coordinator._last_move_rule["cover.salon"] = "incendit"
        coordinator._pending_settle.add("cover.salon")
        coordinator._last_command_time["cover.salon"] = 1000.0
        coordinator.data = {"covers": {"cover.salon": {
            "status": "auto", "target_position": new_target, "matching_rule_id": "nuit"}}}
        mock_hass.states.get.return_value = MockState("open", {"current_position": current})
        return cover

    @pytest.mark.asyncio
    async def test_rule_change_mid_travel_recommands_instead_of_pausing(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        """The 24/09 incident: 'Incendit' disabled 35 s after its command,
        the cover still reports 17 %; 'Nuit' (0 %) must be sent, no pause."""
        self._setup(coordinator, mock_storage, mock_hass, current=17, new_target=0)
        with patch(f"{MOD}.time_mod") as t, patch.object(coordinator, "pause_cover") as pause:
            t.monotonic.return_value = 1035.0
            await coordinator.async_apply_positions()
        pause.assert_not_called()
        mock_hass.services.async_call.assert_awaited_once()
        assert mock_hass.services.async_call.await_args.args[2]["position"] == 0
        assert coordinator._last_positions["cover.salon"] == 0
        assert "cover.salon" in coordinator._pending_settle

    @pytest.mark.asyncio
    async def test_target_change_within_settle_time_is_sent_immediately(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        self._setup(coordinator, mock_storage, mock_hass, current=40, new_target=0)
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1010.0  # only 10 s after the command
            await coordinator.async_apply_positions()
        assert mock_hass.services.async_call.await_args.args[2]["position"] == 0

    @pytest.mark.asyncio
    async def test_time_hysteresis_does_not_block_own_target_change(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        """Same rule, target edited: min_time_between_changes must not delay it."""
        self._setup(coordinator, mock_storage, mock_hass, current=40, new_target=0)
        coordinator.data["covers"]["cover.salon"]["matching_rule_id"] = "incendit"
        with patch(f"{MOD}.time_mod") as t, patch(f"{MOD}.dt_util") as dt:
            t.monotonic.return_value = 1010.0
            dt.now.return_value.timestamp.return_value = 10000.0  # 10 s after last change
            await coordinator.async_apply_positions()
        mock_hass.services.async_call.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_same_target_still_waits_and_still_detects_manual_moves(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        """Without a target change the existing behaviour is unchanged."""
        self._setup(coordinator, mock_storage, mock_hass, current=17, new_target=100)
        with patch(f"{MOD}.time_mod") as t, patch.object(coordinator, "pause_cover") as pause:
            t.monotonic.return_value = 1010.0  # within settle time: wait
            await coordinator.async_apply_positions()
            pause.assert_not_called()
            mock_hass.services.async_call.assert_not_called()
            t.monotonic.return_value = 1100.0  # long after: real deviation -> pause
            await coordinator.async_apply_positions()
            pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_protective_move_is_not_treated_as_own_target_change(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        """Vent/lock moves (not sent by the apply cycle) keep their settle wait."""
        self._setup(coordinator, mock_storage, mock_hass, current=10, new_target=0)
        coordinator._last_positions["cover.salon"] = 30  # vent command
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1010.0
            await coordinator.async_apply_positions()
        mock_hass.services.async_call.assert_not_called()


# ---------------------------------------------------------------------------
# E: travel time (configured / measured) drives the settle time
# ---------------------------------------------------------------------------

class TestTravelTime:
    def test_default_settle_time(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw()
        assert coordinator._settle_time("cover.salon") == SETTLE_TIME

    def test_measured_travel_extends_settle_time(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw(measured_travel_time=36.0)
        assert coordinator._settle_time("cover.salon") == 36.0 + TRAVEL_TIME_MARGIN

    def test_configured_travel_wins_over_measured(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw(travel_time=50, measured_travel_time=36.0)
        assert coordinator._settle_time("cover.salon") == 50 + TRAVEL_TIME_MARGIN

    def test_fast_cover_keeps_minimum(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw(travel_time=10)
        assert coordinator._settle_time("cover.salon") == SETTLE_TIME

    def test_measure_full_travel(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw()
        coordinator._move_start["cover.salon"] = (1000.0, 0, 100)
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1035.5
            coordinator._measure_travel("cover.salon", MockState("open", {"current_position": 100}))
        mock_storage.update_cover_measured_travel.assert_called_once_with("cover.salon", 35.5)
        assert "cover.salon" not in coordinator._move_start

    def test_partial_move_is_scaled_and_smoothed(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw(measured_travel_time=40.0)
        coordinator._move_start["cover.salon"] = (1000.0, 100, 50)  # half travel in 16 s
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1016.0
            coordinator._measure_travel("cover.salon", MockState("open", {"current_position": 50}))
        # 16 s * 100/50 = 32 s, averaged with 40 s
        mock_storage.update_cover_measured_travel.assert_called_once_with("cover.salon", 36.0)

    def test_intermediate_position_does_not_finish_measurement(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw()
        coordinator._move_start["cover.salon"] = (1000.0, 0, 100)
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1009.0
            coordinator._measure_travel("cover.salon", MockState("open", {"current_position": 17}))
        mock_storage.update_cover_measured_travel.assert_not_called()
        assert "cover.salon" in coordinator._move_start

    def test_small_or_stale_moves_are_ignored(self, coordinator, mock_storage) -> None:
        mock_storage.get_cover_raw.return_value = _raw()
        coordinator._move_start["cover.a"] = (1000.0, 40, 50)  # 10 % only
        coordinator._move_start["cover.b"] = (1000.0, 0, 100)
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 1005.0
            coordinator._measure_travel("cover.a", MockState("open", {"current_position": 50}))
            t.monotonic.return_value = 1000.0 + MAX_MEASURED_TRAVEL + 1
            coordinator._measure_travel("cover.b", MockState("open", {"current_position": 100}))
        mock_storage.update_cover_measured_travel.assert_not_called()
        assert coordinator._move_start == {}

    def test_state_change_uses_cover_settle_time(self, coordinator, mock_storage, mock_hass) -> None:
        """A 36 s cover reporting its final travel at 34 s is not paused."""
        cover = CoverConfig(entity_id="cover.salon", name="Salon")
        mock_storage.covers = {"cover.salon": cover}
        mock_storage.get_cover_raw.return_value = _raw(measured_travel_time=36.0)
        coordinator._cover_states["cover.salon"] = CoverStatus.AUTO
        coordinator._last_positions["cover.salon"] = 100
        coordinator._last_command_time["cover.salon"] = 1000.0
        with patch(f"{MOD}.time_mod") as t, patch.object(coordinator, "pause_cover") as pause:
            t.monotonic.return_value = 1034.0
            coordinator._handle_cover_state_change(
                "cover.salon", MockState("open", {"current_position": 17}),
                MockState("open", {"current_position": 60}),
            )
        pause.assert_not_called()

    @pytest.mark.asyncio
    async def test_apply_move_starts_measurement(self, coordinator, mock_storage, mock_hass) -> None:
        mock_storage.covers = {"cover.salon": CoverConfig(entity_id="cover.salon", name="Salon")}
        mock_storage.get_cover_raw.return_value = _raw(min_time_between_changes=0)
        coordinator._cover_states["cover.salon"] = CoverStatus.AUTO
        coordinator._last_positions["cover.salon"] = 0
        coordinator.data = {"covers": {"cover.salon": {"status": "auto", "target_position": 100}}}
        mock_hass.states.get.return_value = MockState("closed", {"current_position": 0})
        with patch(f"{MOD}.time_mod") as t:
            t.monotonic.return_value = 5000.0
            await coordinator.async_apply_positions()
        assert coordinator._move_start["cover.salon"] == (5000.0, 0, 100)


class TestTravelStorage:
    def test_update_measured_travel(self, storage) -> None:
        storage._data = {"covers": {"cover.a": {"entity_id": "cover.a", "name": "A"}}}
        storage.update_cover_measured_travel("cover.a", 36.5)
        assert storage._data["covers"]["cover.a"]["measured_travel_time"] == 36.5
        assert storage.covers["cover.a"].measured_travel_time == 36.5

    def test_model_roundtrip(self) -> None:
        cover = CoverConfig(entity_id="cover.a", name="A", travel_time=40, measured_travel_time=36.5)
        again = CoverConfig.from_dict(cover.to_dict())
        assert again.travel_time == 40 and again.measured_travel_time == 36.5


class TestTravelApi:
    def _schema(self):
        from unittest.mock import MagicMock

        from homeassistant.components import websocket_api as real_ws

        from custom_components.cover_automatic.api import async_setup_api

        schemas: dict = {}
        with patch("custom_components.cover_automatic.api.websocket_api") as ws:
            ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA
            ws.async_register_command.side_effect = (
                lambda hass, ct, handler=None, schema=None: schemas.__setitem__(ct, schema)
            )
            async_setup_api(MagicMock(), MagicMock(), MagicMock())
        return schemas["cover_automatic/cover/update"]

    def test_travel_time_accepted_and_reset(self) -> None:
        schema = self._schema()
        base = {"id": 1, "type": "cover_automatic/cover/update", "entity_id": "cover.a"}
        assert schema({**base, "travel_time": 40})["travel_time"] == 40
        assert schema({**base, "travel_time": None})["travel_time"] is None
        assert schema({**base, "measured_travel_time": None})["measured_travel_time"] is None

    @pytest.mark.parametrize("payload", [{"travel_time": 0}, {"travel_time": 999}, {"measured_travel_time": 12}])
    def test_invalid_values_rejected(self, payload) -> None:
        import voluptuous as vol

        with pytest.raises(vol.Invalid):
            self._schema()({"id": 1, "type": "cover_automatic/cover/update", "entity_id": "cover.a", **payload})


class TestDefaultTravelTime:
    def test_order_manual_measured_default(self, coordinator, mock_storage) -> None:
        mock_storage.default_travel_time = 40
        mock_storage.get_cover_raw.return_value = _raw()
        assert coordinator._travel_time("cover.a") == 40.0
        assert coordinator._settle_time("cover.a") == 40 + TRAVEL_TIME_MARGIN
        mock_storage.get_cover_raw.return_value = _raw(measured_travel_time=36.0)
        assert coordinator._travel_time("cover.a") == 36.0
        mock_storage.get_cover_raw.return_value = _raw(travel_time=50, measured_travel_time=36.0)
        assert coordinator._travel_time("cover.a") == 50.0

    def test_no_default_keeps_30s(self, coordinator, mock_storage) -> None:
        mock_storage.default_travel_time = None
        mock_storage.get_cover_raw.return_value = _raw()
        assert coordinator._settle_time("cover.a") == SETTLE_TIME

    def test_storage_property(self, storage) -> None:
        storage._data = {}
        assert storage.default_travel_time is None
        storage.default_travel_time = 40
        assert storage.default_travel_time == 40
        storage.default_travel_time = None
        assert storage.default_travel_time is None

    def test_settings_schema(self) -> None:
        from unittest.mock import MagicMock

        import voluptuous as vol
        from homeassistant.components import websocket_api as real_ws

        from custom_components.cover_automatic.api import async_setup_api

        schemas: dict = {}
        with patch("custom_components.cover_automatic.api.websocket_api") as ws:
            ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA
            ws.async_register_command.side_effect = (
                lambda hass, ct, handler=None, schema=None: schemas.__setitem__(ct, schema)
            )
            async_setup_api(MagicMock(), MagicMock(), MagicMock())
        schema = schemas["cover_automatic/settings/update"]
        base = {"id": 1, "type": "cover_automatic/settings/update"}
        assert schema({**base, "default_travel_time": 40.0})["default_travel_time"] == 40
        assert schema({**base, "default_travel_time": None})["default_travel_time"] is None
        with pytest.raises(vol.Invalid):
            schema({**base, "default_travel_time": 0})

    @pytest.mark.asyncio
    async def test_import_keeps_explicit_none_and_carries_over(self, storage) -> None:
        storage._data = {"covers": {}, "default_travel_time": 40}
        await storage.async_import_data({"covers": {}})
        assert storage.default_travel_time == 40
        await storage.async_import_data({"covers": {}, "default_travel_time": None})
        assert storage.default_travel_time is None
