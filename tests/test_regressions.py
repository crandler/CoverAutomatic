# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
"""Regression tests for the issues fixed in 1.62.0."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic.const import DOMAIN
from custom_components.cover_automatic.models import (
    Condition,
    ConditionType,
    CoverConfig,
    CoverStatus,
)
from tests.test_api import _make_connection, _make_coordinator, _make_hass, _make_storage
from tests.test_coordinator import (  # noqa: F401 -- pytest fixtures
    MockState,
    coordinator,
    mock_hass,
    mock_storage,
)
from tests.test_storage import mock_store, storage  # noqa: F401 -- pytest fixtures

MOD = "custom_components.cover_automatic"


# ---------------------------------------------------------------------------
# 1. Reload: static panel path registered only once
# ---------------------------------------------------------------------------

class TestReloadStaticPath:
    @pytest.mark.asyncio
    async def test_second_setup_does_not_register_static_path_again(self) -> None:
        from custom_components.cover_automatic import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.http.async_register_static_paths = AsyncMock()
        entry = MagicMock()
        entry.data = {}
        entry.entry_id = "e1"
        integration = MagicMock()
        integration.manifest = {"version": "1.62.0"}

        with (
            patch(f"{MOD}.async_get_integration", AsyncMock(return_value=integration)),
            patch(f"{MOD}.CoverAutomaticStorage") as storage_cls,
            patch(f"{MOD}.ActivityLogStorage") as log_cls,
            patch(f"{MOD}.CoverAutomaticCoordinator") as coord_cls,
            patch(f"{MOD}.async_setup_services", AsyncMock()),
            patch(f"{MOD}.async_setup_api"),
            patch(f"{MOD}.async_register_built_in_panel") as register_panel,
            patch(f"{MOD}.add_extra_js_url") as add_js,
            patch(f"{MOD}.er.async_get", MagicMock()),
            patch(f"{MOD}.async_cleanup_orphan_entities"),
        ):
            storage_cls.return_value.async_load = AsyncMock()
            storage_cls.return_value.covers = {}
            log_cls.return_value.async_load = AsyncMock()
            coord_cls.return_value.async_setup = AsyncMock()
            coord_cls.return_value.async_config_entry_first_refresh = AsyncMock()

            await async_setup_entry(hass, entry)
            await async_setup_entry(hass, entry)  # reload

        hass.http.async_register_static_paths.assert_awaited_once()
        # Dashboard card module added once, with the version for cache busting
        add_js.assert_called_once()
        assert add_js.call_args[0][1] == "/cover_automatic/cover-automatic-card.js?v=1.62.0"
        assert register_panel.call_count == 2
        assert register_panel.call_args.kwargs["update"] is True


# ---------------------------------------------------------------------------
# 2. No cover stuck in LOCKED / VENTING
# ---------------------------------------------------------------------------

def _wind_cover(mock_storage, **extra):
    raw = {
        "entity_id": "cover.t", "name": "T", "auto_enabled": True, "inverted": False,
        "lock_sensor": None, "lock_position": 100, "vent_sensor": None, "vent_position": 30,
    }
    raw.update(extra)
    mock_storage._data["covers"] = {"cover.t": raw}
    mock_storage.get_cover_raw.return_value = raw
    return raw


class TestNoStuckProtectiveStatus:
    def test_lock_released_after_wind_protection(self, coordinator, mock_storage, mock_hass) -> None:
        mock_storage.wind_sensor = "sensor.wind"
        mock_storage.wind_speed_threshold = 50.0
        mock_storage.wind_speed_hysteresis = 10.0
        _wind_cover(mock_storage, lock_sensor="binary_sensor.win")
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        states = {
            "sensor.wind": MockState("60"),
            "binary_sensor.win": MockState("on"),
            "cover.t": MockState("open", {"current_position": 100}),
        }
        mock_hass.states.get = states.get

        coordinator._check_wind_protection()
        states["sensor.wind"] = MockState("30")
        coordinator._check_wind_protection()
        assert coordinator._cover_states["cover.t"] == CoverStatus.LOCKED

        states["binary_sensor.win"] = MockState("off")
        coordinator._handle_contact_sensor_change(
            "binary_sensor.win", ["cover.t"], [], MockState("on"), MockState("off")
        )
        assert coordinator._cover_states["cover.t"] == CoverStatus.AUTO

    def test_venting_released_when_vent_sensor_removed(self, coordinator, mock_storage, mock_hass) -> None:
        _wind_cover(mock_storage, vent_sensor=None)  # sensor removed in the panel
        coordinator._cover_states["cover.t"] = CoverStatus.VENTING
        mock_hass.states.get.return_value = MockState("open", {"current_position": 30})

        coordinator._sync_cover_statuses()

        assert coordinator._cover_states["cover.t"] == CoverStatus.AUTO


# ---------------------------------------------------------------------------
# 3. Import
# ---------------------------------------------------------------------------

class TestImportGlobals:
    @pytest.mark.asyncio
    async def test_export_import_roundtrip_keeps_defaults(self, storage) -> None:
        await storage.async_load()
        await storage.async_import_data(storage.get_raw_data())

        assert storage.enabled is True
        assert storage.min_position_change == 5
        assert storage.min_time_between_changes == 300
        assert storage.pause_duration == 10
        assert storage.command_stagger == 0.0
        assert storage.logbook_enabled is True
        assert "enabled" not in storage._data

    @pytest.mark.asyncio
    async def test_getters_ignore_stored_none(self, storage) -> None:
        storage._data = {"enabled": None, "min_position_change": None, "pause_duration": None}
        assert storage.enabled is True
        assert storage.min_position_change == 5
        assert storage.pause_duration == 10

    @pytest.mark.asyncio
    async def test_explicit_none_sensor_is_kept(self, storage) -> None:
        storage._data = {"outdoor_temp_sensor": "sensor.out", "covers": {}}
        await storage.async_import_data({"covers": {}, "outdoor_temp_sensor": None})
        assert storage.outdoor_temp_sensor is None

    @pytest.mark.asyncio
    async def test_unrelated_yaml_is_rejected(self, storage) -> None:
        storage._data = {"covers": {"cover.a": {"entity_id": "cover.a", "name": "A"}}}
        with pytest.raises(ValueError):
            await storage.async_import_data({"db_password": "secret"})
        assert "cover.a" in storage._data["covers"]


# ---------------------------------------------------------------------------
# 4. End stops reachable despite min_position_change
# ---------------------------------------------------------------------------

class TestEndStops:
    def _setup(self, coordinator, mock_storage, mock_hass, current, target):
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        coordinator._last_positions["cover.t"] = current
        coordinator.data = {"covers": {"cover.t": {"status": "auto", "target_position": target}}}
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5, "min_time_between_changes": 0, "inverted": False,
        }
        mock_hass.states.get.return_value = MockState("open", {"current_position": current})

    @pytest.mark.asyncio
    async def test_closes_fully_from_3_percent(self, coordinator, mock_storage, mock_hass) -> None:
        self._setup(coordinator, mock_storage, mock_hass, current=3, target=0)
        await coordinator.async_apply_positions()
        mock_hass.services.async_call.assert_awaited_once()
        assert mock_hass.services.async_call.await_args.args[2]["position"] == 0

    @pytest.mark.asyncio
    async def test_opens_fully_from_98_percent(self, coordinator, mock_storage, mock_hass) -> None:
        self._setup(coordinator, mock_storage, mock_hass, current=98, target=100)
        await coordinator.async_apply_positions()
        assert mock_hass.services.async_call.await_args.args[2]["position"] == 100

    @pytest.mark.asyncio
    async def test_end_stop_not_resent_once_commanded(self, coordinator, mock_storage, mock_hass) -> None:
        self._setup(coordinator, mock_storage, mock_hass, current=1, target=0)
        coordinator._last_sent_target["cover.t"] = 0  # motor settled at 1%
        await coordinator.async_apply_positions()
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_intermediate_target_keeps_hysteresis(self, coordinator, mock_storage, mock_hass) -> None:
        self._setup(coordinator, mock_storage, mock_hass, current=48, target=50)
        await coordinator.async_apply_positions()
        mock_hass.services.async_call.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Wind / comfort validation
# ---------------------------------------------------------------------------

class TestSettingsValidation:
    @pytest.mark.asyncio
    async def test_wind_hysteresis_must_be_below_threshold(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        conn = _make_connection()
        storage = _make_storage(wind_speed_threshold=50.0)
        storage.house_rotation = 0.0
        msg = {"id": 1, "type": f"{DOMAIN}/settings/update", "wind_speed_hysteresis": 60.0}
        await ws_settings_update(_make_hass(), conn, msg, storage, _make_coordinator())
        conn.send_error.assert_called_once()
        storage.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_comfort_min_must_be_below_max(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        conn = _make_connection()
        storage = _make_storage()
        storage.house_rotation = 0.0
        msg = {"id": 1, "type": f"{DOMAIN}/settings/update", "comfort_temp_min": 26.0}
        await ws_settings_update(_make_hass(), conn, msg, storage, _make_coordinator())
        conn.send_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_cover_comfort_min_must_be_below_max(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        conn = _make_connection()
        storage = _make_storage()
        raw = {"entity_id": "cover.t", "name": "T", "comfort_temp_max": 22.0}
        storage.get_cover_raw = MagicMock(return_value=raw)
        msg = {"id": 1, "type": f"{DOMAIN}/cover/update", "entity_id": "cover.t",
               "comfort_temp_min": 23.0}
        await ws_cover_update(_make_hass(), conn, msg, storage, _make_coordinator())
        conn.send_error.assert_called_once()
        assert "comfort_temp_min" not in raw

    def test_wind_released_when_feature_disabled(self, coordinator, mock_storage, mock_hass) -> None:
        mock_storage.wind_sensor = None
        mock_storage.wind_speed_threshold = 50.0
        _wind_cover(mock_storage)
        coordinator._wind_protected = True
        coordinator._cover_states["cover.t"] = CoverStatus.WIND_PROTECTED
        mock_hass.states.get.return_value = MockState("open", {"current_position": 100})

        coordinator._check_wind_protection()

        assert coordinator._wind_protected is False
        assert coordinator._cover_states["cover.t"] == CoverStatus.AUTO

    def test_invalid_hysteresis_does_not_block_release(self, coordinator, mock_storage, mock_hass) -> None:
        mock_storage.wind_sensor = "sensor.wind"
        mock_storage.wind_speed_threshold = 50.0
        mock_storage.wind_speed_hysteresis = 80.0  # legacy invalid value
        _wind_cover(mock_storage)
        coordinator._wind_protected = True
        coordinator._cover_states["cover.t"] = CoverStatus.WIND_PROTECTED
        mock_hass.states.get.return_value = MockState("20", {"current_position": 100})

        coordinator._check_wind_protection()

        assert coordinator._wind_protected is False


# ---------------------------------------------------------------------------
# 6. State tracking of rule entities
# ---------------------------------------------------------------------------

class TestStateTracking:
    def test_entity_id_param_and_workday_are_tracked(self, coordinator, mock_storage) -> None:
        mock_storage.workday_sensor = "binary_sensor.workday"
        mock_storage.solar_sensor = None
        mock_storage._data["rules"] = {
            "r": {"conditions": [
                {"type": "state_is", "params": {"entity_id": "input_boolean.guest"}},
                {"type": "numeric_state", "params": {"entity_id": "sensor.lux"}},
            ]}
        }
        with patch(f"{MOD}.coordinator.async_track_state_change_event") as track:
            coordinator._setup_state_tracking(full_refresh=True)
        tracked = set(track.call_args.args[1])
        assert {"input_boolean.guest", "sensor.lux", "binary_sensor.workday"} <= tracked

    @pytest.mark.asyncio
    async def test_rule_add_refreshes_tracking(self) -> None:
        from custom_components.cover_automatic.api import ws_rule_add

        coordinator = _make_coordinator()
        msg = {"id": 1, "type": f"{DOMAIN}/rule/add", "name": "R", "conditions": []}
        await ws_rule_add(_make_hass(), _make_connection(), msg, _make_storage(), coordinator)
        coordinator.refresh_state_tracking.assert_called_once()


# ---------------------------------------------------------------------------
# 7. Entity registry sync
# ---------------------------------------------------------------------------

class TestEntitySync:
    def test_expected_unique_ids(self) -> None:
        from custom_components.cover_automatic.entities import expected_unique_ids

        storage = MagicMock()
        storage._data = {"covers": {"cover.a": {}}, "facades": {"south": {}}}
        ids = expected_unique_ids("e1", storage)
        assert ids == {
            f"{DOMAIN}_master", f"{DOMAIN}_e1_scenario",
            f"{DOMAIN}_e1_wind_protection", f"{DOMAIN}_e1_covers_paused",
            f"{DOMAIN}_e1_covers_manual", f"{DOMAIN}_e1_covers_locked",
            f"{DOMAIN}_cover.a_auto", f"{DOMAIN}_cover.a_status",
            f"{DOMAIN}_cover.a_rule", f"{DOMAIN}_cover.a_target",
            f"{DOMAIN}_cover.a_position", f"{DOMAIN}_cover.a_comfort",
            f"{DOMAIN}_cover.a_pause_end",
            f"{DOMAIN}_facade_south_sun", f"{DOMAIN}_facade_south_sun_entry",
            f"{DOMAIN}_facade_south_sun_exit",
        }

    def test_cleanup_removes_orphans_only(self) -> None:
        from custom_components.cover_automatic import entities

        storage = MagicMock()
        storage._data = {"covers": {"cover.a": {}}, "facades": {}}
        entry = MagicMock(entry_id="e1")
        keep = MagicMock(platform=DOMAIN, unique_id=f"{DOMAIN}_cover.a_auto", entity_id="switch.a")
        orphan = MagicMock(platform=DOMAIN, unique_id=f"{DOMAIN}_cover.gone_auto", entity_id="switch.gone")
        ent_reg = MagicMock()
        dev_keep = MagicMock(identifiers={(DOMAIN, "cover.a")}, id="d1")
        dev_orphan = MagicMock(identifiers={(DOMAIN, "cover.gone")}, id="d2")
        dev_reg = MagicMock()
        with (
            patch.object(entities.er, "async_get", return_value=ent_reg),
            patch.object(entities.er, "async_entries_for_config_entry", return_value=[keep, orphan]),
            patch.object(entities.dr, "async_get", return_value=dev_reg),
            patch.object(entities.dr, "async_entries_for_config_entry", return_value=[dev_keep, dev_orphan]),
        ):
            entities.async_cleanup_orphan_entities(MagicMock(), entry, storage)

        ent_reg.async_remove.assert_called_once_with("switch.gone")
        dev_reg.async_update_device.assert_called_once_with("d2", remove_config_entry_id="e1")

    @pytest.mark.asyncio
    async def test_cover_add_and_delete_sync_entities(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_add, ws_cover_delete

        coordinator = _make_coordinator()
        hass = _make_hass()
        await ws_cover_add(hass, _make_connection(), {"id": 1, "entity_ids": ["cover.x"]},
                           _make_storage(), coordinator)
        await ws_cover_delete(hass, _make_connection(), {"id": 2, "entity_id": "cover.x"},
                              _make_storage(), coordinator)
        assert coordinator.async_sync_entities.call_count == 2

    def test_switch_platform_adds_runtime_covers(self) -> None:
        from custom_components.cover_automatic import switch

        coordinator = MagicMock()
        coordinator.storage.covers = {"cover.a": CoverConfig(entity_id="cover.a", name="A")}
        entry = MagicMock()
        entry.runtime_data.coordinator = coordinator
        added: list = []

        import asyncio

        asyncio.run(switch.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(list(ents))))
        assert len(added) == 2  # master + cover.a
        listener = coordinator.async_add_listener.call_args.args[0]

        coordinator.storage.covers = {
            "cover.a": CoverConfig(entity_id="cover.a", name="A"),
            "cover.b": CoverConfig(entity_id="cover.b", name="B"),
        }
        listener()
        listener()  # idempotent
        assert len(added) == 3
        assert added[-1]._cover_entity_id == "cover.b"


# ---------------------------------------------------------------------------
# 8. Shutdown calls the base class
# ---------------------------------------------------------------------------

class TestShutdownBase:
    @pytest.mark.asyncio
    async def test_base_shutdown_called(self, coordinator) -> None:
        coordinator._unsub_state_change = []
        await coordinator.async_shutdown()
        assert coordinator._shutdown_requested is True
        coordinator._debounced_refresh.async_shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# 9. Tilt re-sent after a position move
# ---------------------------------------------------------------------------

class TestTiltResend:
    @pytest.mark.asyncio
    async def test_tilt_resent_after_move_even_if_unchanged(
        self, coordinator, mock_storage, mock_hass
    ) -> None:
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        coordinator._last_positions["cover.t"] = 100
        coordinator._last_tilt_positions["cover.t"] = 50
        coordinator.data = {"covers": {"cover.t": {
            "status": "auto", "target_position": 20, "target_tilt_position": 50,
        }}}
        mock_storage.get_cover_raw.return_value = {
            "min_position_change": 5, "min_time_between_changes": 0,
            "inverted": False, "supports_tilt": True,
        }
        mock_hass.states.get.return_value = MockState(
            "open", {"current_position": 100, "current_tilt_position": 50, "supported_features": 255}
        )
        with patch.object(coordinator, "_schedule_tilt") as schedule:
            await coordinator.async_apply_positions()
        schedule.assert_called_once()
        assert schedule.call_args.args[1] == 50


# ---------------------------------------------------------------------------
# 11. Slow covers: progress towards our target extends the settle window
# ---------------------------------------------------------------------------

class TestSlowCoverSettle:
    def test_progress_is_not_a_manual_override(self, coordinator, mock_storage, mock_hass) -> None:
        cover = CoverConfig(entity_id="cover.t", name="T")
        mock_storage.covers = {"cover.t": cover}
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        coordinator._last_positions["cover.t"] = 0  # commanded to close
        coordinator._last_command_time["cover.t"] = 0.0  # > SETTLE_TIME ago
        coordinator._pending_settle.add("cover.t")

        with patch(f"{MOD}.coordinator.time_mod") as mock_time, \
                patch.object(coordinator, "pause_cover") as pause:
            mock_time.monotonic.return_value = 9999.0
            coordinator._handle_cover_state_change(
                "cover.t",
                MockState("open", {"current_position": 60}),
                MockState("open", {"current_position": 40}),
            )
        pause.assert_not_called()
        assert coordinator._last_command_time["cover.t"] == 9999.0
        assert "cover.t" in coordinator._pending_settle


# ---------------------------------------------------------------------------
# Minor fixes
# ---------------------------------------------------------------------------

class TestMinorFixes:
    def test_pause_ignored_while_locked(self, coordinator, mock_storage) -> None:
        coordinator._cover_states["cover.t"] = CoverStatus.LOCKED
        coordinator.pause_cover(CoverConfig(entity_id="cover.t", name="T"))
        assert coordinator._cover_states["cover.t"] == CoverStatus.LOCKED
        mock_storage.update_cover_status.assert_not_called()

    def test_after_sunset_still_true_after_midnight(self) -> None:
        from custom_components.cover_automatic.engine import RuleEngine

        engine = RuleEngine(MagicMock(), MagicMock())
        cond = Condition(type=ConditionType.TIME_AFTER_SUNSET, params={"offset": 0})
        now = 1_000_000.0  # 01:00
        with (
            patch(f"{MOD}.engine.get_sunset_time", return_value=now + 19 * 3600),
            patch(f"{MOD}.engine.get_sunrise_time", return_value=now + 5 * 3600),
            patch(f"{MOD}.engine.get_sun_event_time", return_value=now - 5 * 3600),
            patch(f"{MOD}.engine.dt_util.now") as mock_now,
        ):
            mock_now.return_value.timestamp.return_value = now
            assert engine._evaluate_condition(cond, None) is True
            # after sunrise, before sunset: false
            mock_now.return_value.timestamp.return_value = now + 8 * 3600
            assert engine._evaluate_condition(cond, None) is False

    @pytest.mark.asyncio
    async def test_house_rotation_rotates_existing_facades(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        storage = _make_storage()
        storage.house_rotation = 0.0
        storage._data = {"facades": {"south": {"azimuth_start": 135.0, "azimuth_end": 225.0}}}
        msg = {"id": 1, "type": f"{DOMAIN}/settings/update", "house_rotation": 10.0}
        await ws_settings_update(_make_hass(), _make_connection(), msg, storage, _make_coordinator())
        assert storage._data["facades"]["south"] == {"azimuth_start": 145.0, "azimuth_end": 235.0}

    def test_subscribe_forwards_dispatcher_signal(self) -> None:
        from custom_components.cover_automatic.api import ws_subscribe_updates

        conn = MagicMock()
        conn.subscriptions = {}
        with patch(f"{MOD}.api.async_dispatcher_connect") as connect:
            ws_subscribe_updates(MagicMock(), conn, {"id": 7})
            forward = connect.call_args.args[2]
        conn.send_result.assert_called_once_with(7)
        assert 7 in conn.subscriptions
        forward()
        conn.send_message.assert_called_once()

    @pytest.mark.parametrize("target", [-1, 101])
    def test_rule_target_position_range(self, target) -> None:
        import voluptuous as vol
        from homeassistant.components import websocket_api as real_ws

        from custom_components.cover_automatic.api import async_setup_api

        schemas: dict = {}
        with patch(f"{MOD}.api.websocket_api") as mock_ws:
            mock_ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA
            mock_ws.async_register_command.side_effect = (
                lambda hass, ct, handler=None, schema=None: schemas.__setitem__(ct, schema)
            )
            async_setup_api(MagicMock(), MagicMock(), MagicMock())
        with pytest.raises(vol.Invalid):
            schemas[f"{DOMAIN}/rule/add"](
                {"id": 1, "type": f"{DOMAIN}/rule/add", "name": "R", "target_position": target}
            )
