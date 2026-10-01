"""Tests for the sun-on-facade comfort switches (global + per-cover override)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

from custom_components.cover_automatic import engine as engine_mod
from custom_components.cover_automatic.models import (
    Condition,
    ConditionType,
    CoverConfig,
    Facade,
)
from custom_components.cover_automatic.storage import (
    _ALL_MIGRATIONS,
    MIGRATION_PAUSE_DURATION_120,
    MIGRATION_PREEMPTIVE_TRISTATE,
)
from tests.test_api import _make_connection, _make_coordinator, _make_hass, _make_storage
from tests.test_engine import MockState, engine, mock_hass, mock_storage  # noqa: F401
from tests.test_storage import mock_store, storage  # noqa: F401

HEATING, NEUTRAL, COOLING = "18.0", "23.0", "26.0"  # comfort band 21-25
SOLAR_HIGH, SOLAR_LOW = "6000.0", "1000.0"

SUN = Condition(type=ConditionType.SUN_ON_FACADE, params={})
NOT_SUN = Condition(type=ConditionType.SUN_ON_FACADE, params={}, negate=True)


def _setup(hass, store, *, temp: str | None, solar: str = SOLAR_HIGH,
           heating: bool = True, neutral: bool = True, preemptive: bool = True,
           sensor: str | None = "sensor.indoor_temp") -> None:
    store.facades = {"south": Facade(id="south", name="S", azimuth_start=90, azimuth_end=270)}
    store.indoor_temp_sensor = sensor
    store.solar_sensor = "sensor.pv_power"
    store.solar_threshold = 5000.0
    store.solar_threshold_entity = None
    store.comfort_temp_min_entity = None
    store.comfort_temp_max_entity = None
    store.sun_heating_ignore = heating
    store.sun_neutral_ignore = neutral
    store.preemptive_shading = preemptive
    states = {"sensor.pv_power": MockState(solar)}
    if temp is not None:
        states["sensor.indoor_temp"] = MockState(temp)
    hass.states.get = lambda eid: states.get(eid)


def _cover(**kw) -> CoverConfig:
    return CoverConfig(entity_id="cover.test", name="Test", facade_id="south", **kw)


def _eval(engine, cover, cond=SUN, *, on_facade: bool = True) -> bool:  # noqa: F811
    with (
        patch.object(engine_mod, "is_sun_on_facade", return_value=on_facade),
        patch.object(engine_mod, "get_sun_position", return_value=(180.0, 30.0)),
    ):
        return engine._evaluate_final(cond, cover)


# ---------------------------------------------------------------------------
# Engine semantics
# ---------------------------------------------------------------------------

class TestEngineSemantics:
    @pytest.mark.parametrize(
        ("temp", "heating", "neutral", "preemptive", "solar", "expected"),
        [
            # Defaults (current behaviour)
            (COOLING, True, True, True, SOLAR_LOW, True),
            (HEATING, True, True, True, SOLAR_HIGH, False),
            (NEUTRAL, True, True, True, SOLAR_HIGH, True),
            (NEUTRAL, True, True, True, SOLAR_LOW, False),
            (NEUTRAL, True, True, False, SOLAR_HIGH, False),
            # Heating switch off: sun counts in heating
            (HEATING, False, True, True, SOLAR_LOW, True),
            (NEUTRAL, False, True, True, SOLAR_LOW, False),
            # Neutral switch off: sun counts in neutral, preemptive irrelevant
            (NEUTRAL, True, False, False, SOLAR_LOW, True),
            (HEATING, True, False, True, SOLAR_HIGH, False),
            # Both off: position only
            (HEATING, False, False, False, SOLAR_LOW, True),
            (NEUTRAL, False, False, False, SOLAR_LOW, True),
            (COOLING, False, False, False, SOLAR_LOW, True),
        ],
    )
    def test_mode_by_flags(
        self, engine, mock_hass, mock_storage,  # noqa: F811
        temp, heating, neutral, preemptive, solar, expected,
    ) -> None:
        _setup(mock_hass, mock_storage, temp=temp, solar=solar,
               heating=heating, neutral=neutral, preemptive=preemptive)
        assert _eval(engine, _cover()) is expected

    def test_sun_off_facade_always_false(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=COOLING, heating=False, neutral=False)
        assert _eval(engine, _cover(), on_facade=False) is False

    def test_no_sensor_position_only(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=HEATING, sensor=None)
        assert _eval(engine, _cover()) is True

    def test_cover_override_beats_global(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=HEATING)
        assert _eval(engine, _cover()) is False
        assert _eval(engine, _cover(sun_heating_ignore=False)) is True
        # Global off, cover forces it back on
        _setup(mock_hass, mock_storage, temp=HEATING, heating=False)
        assert _eval(engine, _cover()) is True
        assert _eval(engine, _cover(sun_heating_ignore=True)) is False

    def test_neutral_override(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=NEUTRAL, solar=SOLAR_LOW)
        assert _eval(engine, _cover()) is False
        assert _eval(engine, _cover(sun_neutral_ignore=False)) is True
        _setup(mock_hass, mock_storage, temp=NEUTRAL, solar=SOLAR_LOW, neutral=False)
        assert _eval(engine, _cover(sun_neutral_ignore=True)) is False

    def test_preemptive_override(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=NEUTRAL, preemptive=False)
        assert _eval(engine, _cover()) is False
        assert _eval(engine, _cover(preemptive_shading=True)) is True
        _setup(mock_hass, mock_storage, temp=NEUTRAL, preemptive=True)
        assert _eval(engine, _cover()) is True
        assert _eval(engine, _cover(preemptive_shading=False)) is False

    def test_sun_flags_resolution(self, engine, mock_storage) -> None:  # noqa: F811
        mock_storage.sun_heating_ignore = True
        mock_storage.sun_neutral_ignore = False
        mock_storage.preemptive_shading = True
        assert engine._sun_flags(_cover()) == (True, False, True)
        assert engine._sun_flags(
            _cover(sun_heating_ignore=False, sun_neutral_ignore=True, preemptive_shading=False)
        ) == (False, True, False)


class TestUnknownMode:
    def test_unknown_defaults_false(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=None)
        assert _eval(engine, _cover()) is False

    @pytest.mark.parametrize(("heating", "neutral"), [(True, False), (False, True)])
    def test_unknown_one_switch_false(
        self, engine, mock_hass, mock_storage, heating, neutral,  # noqa: F811
    ) -> None:
        _setup(mock_hass, mock_storage, temp=None, heating=heating, neutral=neutral)
        assert _eval(engine, _cover()) is False

    def test_unknown_both_off_position_only(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=None, heating=False, neutral=False)
        assert _eval(engine, _cover()) is True
        # Per-cover override off on a global-on install
        _setup(mock_hass, mock_storage, temp=None)
        assert _eval(engine, _cover(sun_heating_ignore=False, sun_neutral_ignore=False)) is True


class TestNegateKnown:
    def test_negate_unknown_comfort_not_met(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=None)
        assert _eval(engine, _cover(), NOT_SUN) is False
        with patch.object(engine_mod, "get_sun_position", return_value=(180.0, 30.0)), \
                patch.object(engine_mod, "is_sun_on_facade", return_value=True):
            assert engine._input_available(SUN, _cover()) is False

    def test_negate_both_off_sensor_irrelevant(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=None, heating=False, neutral=False)
        with patch.object(engine_mod, "get_sun_position", return_value=(180.0, 30.0)), \
                patch.object(engine_mod, "is_sun_on_facade", return_value=True):
            assert engine._input_available(SUN, _cover()) is True
        # Sun on the facade -> NOT not met; off the facade -> NOT met
        assert _eval(engine, _cover(), NOT_SUN) is False
        assert _eval(engine, _cover(), NOT_SUN, on_facade=False) is True

    def test_negate_heating_switch_off_known(self, engine, mock_hass, mock_storage) -> None:  # noqa: F811
        _setup(mock_hass, mock_storage, temp=HEATING, heating=False)
        assert _eval(engine, _cover(), NOT_SUN) is False
        _setup(mock_hass, mock_storage, temp=HEATING)
        assert _eval(engine, _cover(), NOT_SUN) is True


# ---------------------------------------------------------------------------
# Storage migration / settings
# ---------------------------------------------------------------------------

def _legacy_data() -> dict:
    return {
        "covers": {
            "cover.a": {"entity_id": "cover.a", "name": "A", "preemptive_shading": True},
            "cover.b": {"entity_id": "cover.b", "name": "B", "preemptive_shading": False},
            "cover.c": {"entity_id": "cover.c", "name": "C"},
        },
        "rules": {}, "scenarios": {}, "facades": {},
        "migrations": [MIGRATION_PAUSE_DURATION_120],
    }


class TestMigration:
    @pytest.mark.asyncio
    async def test_preemptive_tristate(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = _legacy_data()
        await storage.async_load()
        covers = storage._data["covers"]
        assert covers["cover.a"]["preemptive_shading"] is None
        assert covers["cover.b"]["preemptive_shading"] is False
        assert "preemptive_shading" not in covers["cover.c"]
        assert MIGRATION_PREEMPTIVE_TRISTATE in storage._data["migrations"]
        mock_store.async_delay_save.assert_called()
        assert storage.covers["cover.a"].preemptive_shading is None
        assert storage.covers["cover.b"].preemptive_shading is False
        assert storage.covers["cover.c"].preemptive_shading is None

    @pytest.mark.asyncio
    async def test_runs_once(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = _legacy_data()
        await storage.async_load()
        # Explicit True set afterwards survives the next load
        storage._data["covers"]["cover.a"]["preemptive_shading"] = True
        mock_store.async_load.return_value = storage._data
        mock_store.async_delay_save.reset_mock()
        await storage.async_load()
        assert storage._data["covers"]["cover.a"]["preemptive_shading"] is True
        mock_store.async_delay_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_new_install_marker(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = None
        await storage.async_load()
        assert MIGRATION_PREEMPTIVE_TRISTATE in storage._data["migrations"]
        assert MIGRATION_PREEMPTIVE_TRISTATE in _ALL_MIGRATIONS

    @pytest.mark.asyncio
    async def test_import_legacy_export_converted(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = None
        await storage.async_load()
        await storage.async_import_data(_legacy_data())
        assert storage._data["covers"]["cover.a"]["preemptive_shading"] is None
        assert storage._data["covers"]["cover.b"]["preemptive_shading"] is False

    @pytest.mark.asyncio
    async def test_import_current_export_kept(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = None
        await storage.async_load()
        data = _legacy_data()
        data["migrations"] = list(_ALL_MIGRATIONS)
        await storage.async_import_data(data)
        assert storage._data["covers"]["cover.a"]["preemptive_shading"] is True


class TestGlobalSettings:
    @pytest.mark.asyncio
    async def test_defaults_and_setters(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = None
        await storage.async_load()
        assert storage.sun_heating_ignore is True
        assert storage.sun_neutral_ignore is True
        assert storage.preemptive_shading is True
        storage.sun_heating_ignore = False
        storage.sun_neutral_ignore = False
        storage.preemptive_shading = False
        assert (storage.sun_heating_ignore, storage.sun_neutral_ignore, storage.preemptive_shading) == (
            False, False, False,
        )

    @pytest.mark.asyncio
    async def test_import_keeps_local_settings(self, storage, mock_store) -> None:  # noqa: F811
        mock_store.async_load.return_value = None
        await storage.async_load()
        storage.sun_heating_ignore = False
        await storage.async_import_data({"covers": {}})
        assert storage.sun_heating_ignore is False
        await storage.async_import_data({"covers": {}, "sun_heating_ignore": True})
        assert storage.sun_heating_ignore is True
        exported = storage.get_raw_data()
        assert exported["sun_heating_ignore"] is True


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TestModels:
    @pytest.mark.parametrize("value", [None, True, False])
    def test_roundtrip(self, value) -> None:
        cover = _cover(sun_heating_ignore=value, sun_neutral_ignore=value, preemptive_shading=value)
        restored = CoverConfig.from_dict(cover.to_dict())
        assert restored.sun_heating_ignore is value
        assert restored.sun_neutral_ignore is value
        assert restored.preemptive_shading is value

    def test_defaults_none(self) -> None:
        cover = CoverConfig.from_dict({"entity_id": "cover.x", "name": "X"})
        assert cover.sun_heating_ignore is None
        assert cover.sun_neutral_ignore is None
        assert cover.preemptive_shading is None

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("true", True), ("off", False), (1, True), (0, False), ("garbage", None), ([], None)],
    )
    def test_legacy_values(self, raw, expected) -> None:
        cover = CoverConfig.from_dict({"entity_id": "cover.x", "name": "X", "preemptive_shading": raw})
        assert cover.preemptive_shading is expected


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _schemas() -> dict:
    from homeassistant.components import websocket_api as real_ws

    from custom_components.cover_automatic.api import async_setup_api

    schemas: dict = {}
    with patch("custom_components.cover_automatic.api.websocket_api") as mock_ws:
        mock_ws.BASE_COMMAND_MESSAGE_SCHEMA = real_ws.BASE_COMMAND_MESSAGE_SCHEMA
        mock_ws.async_register_command.side_effect = (
            lambda hass, command_type, handler=None, schema=None: schemas.__setitem__(command_type, schema)
        )
        async_setup_api(_make_hass(), _make_storage(), _make_coordinator())
    return schemas


class TestApi:
    @pytest.mark.parametrize("value", [None, True, False])
    def test_cover_update_schema_tristate(self, value) -> None:
        schema = _schemas()["cover_automatic/cover/update"]
        msg = {"id": 1, "type": "cover_automatic/cover/update", "entity_id": "cover.a",
               "sun_heating_ignore": value, "sun_neutral_ignore": value, "preemptive_shading": value}
        out = schema(msg)
        assert out["sun_heating_ignore"] is value
        assert out["preemptive_shading"] is value

    def test_cover_update_schema_rejects_garbage(self) -> None:
        schema = _schemas()["cover_automatic/cover/update"]
        with pytest.raises(vol.Invalid):
            schema({"id": 1, "type": "cover_automatic/cover/update", "entity_id": "cover.a",
                    "sun_neutral_ignore": "maybe"})

    def test_settings_schema_bool_only(self) -> None:
        schema = _schemas()["cover_automatic/settings/update"]
        out = schema({"id": 1, "type": "cover_automatic/settings/update",
                      "sun_heating_ignore": False, "sun_neutral_ignore": True, "preemptive_shading": False})
        assert out["sun_heating_ignore"] is False
        with pytest.raises(vol.Invalid):
            schema({"id": 1, "type": "cover_automatic/settings/update", "preemptive_shading": None})

    @pytest.mark.asyncio
    async def test_cover_update_stores_null(self) -> None:
        from custom_components.cover_automatic.api import ws_cover_update

        st = _make_storage()
        raw = {"entity_id": "cover.a", "name": "A", "preemptive_shading": False}
        st.get_cover_raw = MagicMock(return_value=raw)
        msg = {"id": 1, "type": "cover_automatic/cover/update", "entity_id": "cover.a",
               "preemptive_shading": None, "sun_heating_ignore": False}
        await ws_cover_update(_make_hass(), _make_connection(), msg, st, _make_coordinator())
        assert raw["preemptive_shading"] is None
        assert raw["sun_heating_ignore"] is False

    @pytest.mark.asyncio
    async def test_settings_update_and_response(self) -> None:
        from custom_components.cover_automatic.api import ws_settings_update

        st = _make_storage()
        st.async_save = AsyncMock()
        conn = _make_connection()
        msg = {"id": 1, "type": "cover_automatic/settings/update",
               "sun_heating_ignore": False, "sun_neutral_ignore": False, "preemptive_shading": False}
        await ws_settings_update(_make_hass(), conn, msg, st, _make_coordinator())
        assert st.sun_heating_ignore is False
        assert st.sun_neutral_ignore is False
        assert st.preemptive_shading is False
        settings = conn.send_result.call_args[0][1]["settings"]
        assert settings["sun_heating_ignore"] is False
        assert settings["preemptive_shading"] is False
