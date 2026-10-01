"""Tests for localization (backend texts and translation files)."""
# ruff: noqa: F811 -- pytest fixtures are imported from sibling test modules
from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cover_automatic import i18n
from custom_components.cover_automatic.models import CoverConfig, CoverStatus
from tests.test_coordinator import (  # noqa: F401 -- pytest fixtures
    MockState,
    coordinator,
    mock_hass,
    mock_storage,
)

COMPONENT = Path(__file__).parent.parent / "custom_components" / "cover_automatic"
LANGS = ("en", "de", "fr")


def _hass(language: str) -> MagicMock:
    hass = MagicMock()
    hass.config.language = language
    return hass


def _keys(obj, prefix=""):
    keys = set()
    for key, value in obj.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            keys |= _keys(value, path + ".")
        else:
            keys.add(path)
    return keys


class TestBackendTexts:
    @pytest.mark.parametrize(
        ("configured", "expected"),
        [("fr", "fr"), ("fr-CA", "fr"), ("de", "de"), ("en-GB", "en"), ("it", "en"), (None, "en")],
    )
    def test_language_resolution(self, configured, expected) -> None:
        assert i18n.language(_hass(configured)) == expected

    def test_all_languages_have_all_keys(self) -> None:
        reference = set(i18n._TEXTS["en"])
        for lang in LANGS:
            assert set(i18n._TEXTS[lang]) == reference, lang

    def test_placeholders_identical_across_languages(self) -> None:
        for key, template in i18n._TEXTS["en"].items():
            expected = set(re.findall(r"{(\w+)}", template))
            for lang in LANGS:
                assert set(re.findall(r"{(\w+)}", i18n._TEXTS[lang][key])) == expected, (lang, key)

    def test_french_logbook_text(self) -> None:
        text = i18n.text(_hass("fr"), "paused", minutes=10)
        assert text == "en pause pendant 10 min (commande manuelle)"

    def test_logbook_uses_ha_language(self, coordinator, mock_hass, mock_storage) -> None:
        mock_hass.config.language = "fr"
        mock_storage.logbook_enabled = True
        mock_storage.pause_duration = 10
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        with patch("custom_components.cover_automatic.coordinator.async_log_entry") as log:
            coordinator.pause_cover(CoverConfig(entity_id="cover.t", name="T"))
        assert log.call_args.args[2] == "en pause pendant 10 min (commande manuelle)"

    def test_activity_log_has_structured_key(self, coordinator, mock_storage) -> None:
        coordinator.log_storage = MagicMock()
        coordinator._cover_states["cover.t"] = CoverStatus.AUTO
        mock_storage.pause_duration = 10
        coordinator.pause_cover(CoverConfig(entity_id="cover.t", name="T"))
        data = coordinator.log_storage.add_entry.call_args.args[3]
        assert data == {"key": "status_change", "from": "auto", "to": "paused"}


class TestDefaultScenarios:
    @pytest.mark.asyncio
    async def test_created_in_ha_language(self, coordinator, mock_hass, mock_storage) -> None:
        mock_hass.config.language = "fr"
        mock_storage.scenarios = {}
        mock_storage.async_add_scenario = AsyncMock()
        await coordinator._async_setup_default_scenarios()
        names = {c.args[0].id: c.args[0].name for c in mock_storage.async_add_scenario.call_args_list}
        assert names == {
            "everyday": "Quotidien", "summer": "Été", "winter": "Hiver",
            "vacation": "Vacances", "cinema": "Cinéma", "manual": "Manuel",
        }

    @pytest.mark.asyncio
    async def test_untouched_default_names_are_localized(self, coordinator, mock_hass, mock_storage) -> None:
        mock_hass.config.language = "fr"
        mock_storage.scenarios = {"everyday": MagicMock()}
        mock_storage._data["scenarios"] = {
            "everyday": {"id": "everyday", "name": "Everyday"},
            "summer": {"id": "summer", "name": "Mon été à moi"},  # renamed by user
            "custom": {"id": "custom", "name": "Everyday"},  # not a default id
        }
        await coordinator._async_setup_default_scenarios()
        scen = mock_storage._data["scenarios"]
        assert scen["everyday"]["name"] == "Quotidien"
        assert scen["summer"]["name"] == "Mon été à moi"
        assert scen["custom"]["name"] == "Everyday"
        mock_storage.async_save.assert_awaited_once()


class TestTranslationFiles:
    def _load(self, name: str) -> dict:
        return json.loads((COMPONENT / name).read_text(encoding="utf-8"))

    def test_strings_equals_english(self) -> None:
        assert self._load("strings.json") == self._load("translations/en.json")

    @pytest.mark.parametrize("lang", ["de", "fr"])
    def test_same_keys_as_english(self, lang) -> None:
        assert _keys(self._load(f"translations/{lang}.json")) == _keys(self._load("translations/en.json"))

    def test_every_service_is_translated(self) -> None:
        import yaml

        services = yaml.safe_load((COMPONENT / "services.yaml").read_text(encoding="utf-8"))
        for lang in LANGS:
            translated = self._load(f"translations/{lang}.json")["services"]
            for service, spec in services.items():
                assert service in translated, (lang, service)
                for field in (spec or {}).get("fields", {}):
                    assert field in translated[service]["fields"], (lang, service, field)

    def test_default_scenarios_have_select_state_translations(self) -> None:
        for lang in LANGS:
            states = self._load(f"translations/{lang}.json")["entity"]["select"]["scenario"]["state"]
            assert set(states) == set(i18n.DEFAULT_SCENARIO_IDS)
            for scenario_id in i18n.DEFAULT_SCENARIO_IDS:
                assert states[scenario_id] == i18n._TEXTS[lang][f"scenario_{scenario_id}"]

    def test_french_panel_dictionary_complete(self) -> None:
        """Every panel i18n key exists in French and German (no English fallback)."""
        src = (COMPONENT / "panel" / "cover-automatic-panel.js").read_text(encoding="utf-8")
        start = src.index("const I18N = {")
        end = src.index("\n};", start)
        body = src[start:end]
        blocks = {}
        for lang in LANGS:
            m = re.search(rf"\n  {lang}: {{\n(.*?)\n  }},?\n", body + "\n", re.S)
            assert m, lang
            # Drop string literals first so text like "condition: state" inside
            # a translation is not mistaken for a key.
            without_strings = re.sub(r'"(?:[^"\\]|\\.)*"', '""', m.group(1))
            blocks[lang] = set(re.findall(r"([a-z0-9_]+)\s*:", without_strings))
        assert blocks["fr"] == blocks["en"]
        assert blocks["de"] == blocks["en"]


class TestWeatherConditions:
    """All Home Assistant weather conditions are selectable and translated."""

    HA_CONDITIONS = {
        "clear-night", "cloudy", "exceptional", "fog", "hail", "lightning",
        "lightning-rainy", "partlycloudy", "pouring", "rainy", "snowy",
        "snowy-rainy", "sunny", "windy", "windy-variant",
    }

    def _panel(self) -> str:
        return (COMPONENT / "panel" / "cover-automatic-panel.js").read_text(encoding="utf-8")

    def test_ha_condition_list_is_current(self) -> None:
        from homeassistant.components import weather

        ha = {
            value for name, value in vars(weather).items()
            if name.startswith("ATTR_CONDITION_") and name != "ATTR_CONDITION_CLASS"
        }
        assert ha == self.HA_CONDITIONS

    def test_panel_offers_every_condition(self) -> None:
        m = re.search(r'weather_is: \[\{ key: "weather", type: "multiselect", options: \[([^\]]*)\]', self._panel())
        assert m
        offered = set(re.findall(r'"([a-z-]+)"', m.group(1)))
        assert offered == self.HA_CONDITIONS

    def test_every_condition_translated(self) -> None:
        src = self._panel()
        for lang in LANGS:
            block = re.search(rf"\n  {lang}: {{\n(.*?)\n  }},?\n", src + "\n", re.S).group(1)
            for cond in self.HA_CONDITIONS:
                assert re.search(rf"\bweather_{cond.replace('-', '_')}:", block), (lang, cond)

    def test_windy_group_includes_windy_variant(self) -> None:
        from custom_components.cover_automatic.engine import _WEATHER_MAP

        assert "windy-variant" in _WEATHER_MAP["windy"]
