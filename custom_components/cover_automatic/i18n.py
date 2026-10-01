"""Backend texts that Home Assistant's translation files cannot cover.

Entity names/states, device names, services and exceptions are translated
through strings.json / translations/*.json. The texts below are generated at
runtime and stored as plain strings (HA logbook entries, default scenario
names, device models), so they are localized here using the language
configured in Home Assistant (hass.config.language).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

SUPPORTED_LANGUAGES = ("en", "de", "fr")

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        # HA logbook entries
        "logbook_name": "Cover Automatic",
        "wind_activated": "wind protection activated ({speed} >= {threshold})",
        "wind_deactivated": "wind protection deactivated ({speed} <= {threshold})",
        "wind_disabled": "wind protection deactivated (disabled in settings)",
        "locked": "locked at {position}% (window open)",
        "unlocked": "unlocked (window closed)",
        "paused": "paused for {minutes} min (manual override)",
        "resumed": "resumed",
        "resumed_venting": "resumed (venting)",
        "resumed_match": "resumed: position matches the rule ({rule})",
        "moved": "moved {from_pos}% -> {to_pos}%",
        "moved_rule": "moved {from_pos}% -> {to_pos}% (rule: {rule})",
        # Default scenario names
        "scenario_everyday": "Everyday",
        "scenario_summer": "Summer",
        "scenario_winter": "Winter",
        "scenario_vacation": "Vacation",
        "scenario_cinema": "Cinema",
        "scenario_manual": "Manual",
        # Device models
        "model_controller": "Controller",
        "model_cover": "Cover controller",
        "no_rule": "No rule",
        "model_facade": "Facade",
    },
    "de": {
        "logbook_name": "Cover Automatic",
        "wind_activated": "Windschutz aktiviert ({speed} >= {threshold})",
        "wind_deactivated": "Windschutz deaktiviert ({speed} <= {threshold})",
        "wind_disabled": "Windschutz deaktiviert (in den Einstellungen ausgeschaltet)",
        "locked": "gesperrt bei {position}% (Fenster offen)",
        "unlocked": "entsperrt (Fenster geschlossen)",
        "paused": "für {minutes} min pausiert (manuelle Bedienung)",
        "resumed": "fortgesetzt",
        "resumed_venting": "fortgesetzt (Lüften)",
        "resumed_match": "fortgesetzt: Position entspricht der Regel ({rule})",
        "moved": "gefahren {from_pos}% -> {to_pos}%",
        "moved_rule": "gefahren {from_pos}% -> {to_pos}% (Regel: {rule})",
        "scenario_everyday": "Alltag",
        "scenario_summer": "Sommer",
        "scenario_winter": "Winter",
        "scenario_vacation": "Urlaub",
        "scenario_cinema": "Kino",
        "scenario_manual": "Manuell",
        "model_controller": "Steuerung",
        "model_cover": "Rollladensteuerung",
        "no_rule": "Keine Regel",
        "model_facade": "Fassade",
    },
    "fr": {
        "logbook_name": "Cover Automatic",
        "wind_activated": "protection vent activée ({speed} >= {threshold})",
        "wind_deactivated": "protection vent désactivée ({speed} <= {threshold})",
        "wind_disabled": "protection vent désactivée (désactivée dans les réglages)",
        "locked": "verrouillé à {position} % (fenêtre ouverte)",
        "unlocked": "déverrouillé (fenêtre fermée)",
        "paused": "en pause pendant {minutes} min (commande manuelle)",
        "resumed": "reprise de l'automatisation",
        "resumed_venting": "reprise de l'automatisation (aération)",
        "resumed_match": "reprise automatique : position conforme à la règle ({rule})",
        "moved": "déplacé {from_pos} % -> {to_pos} %",
        "moved_rule": "déplacé {from_pos} % -> {to_pos} % (règle : {rule})",
        "scenario_everyday": "Quotidien",
        "scenario_summer": "Été",
        "scenario_winter": "Hiver",
        "scenario_vacation": "Vacances",
        "scenario_cinema": "Cinéma",
        "scenario_manual": "Manuel",
        "model_controller": "Contrôleur",
        "model_cover": "Contrôleur de volet",
        "no_rule": "Aucune règle",
        "model_facade": "Façade",
    },
}

# Default scenario ids created on first setup
DEFAULT_SCENARIO_IDS = ("everyday", "summer", "winter", "vacation", "cinema", "manual")


def language(hass: HomeAssistant | None) -> str:
    """Return the supported language matching the HA configuration (fallback en)."""
    lang = getattr(getattr(hass, "config", None), "language", None)
    if not isinstance(lang, str):
        return "en"
    lang = lang.lower()
    if lang in _TEXTS:
        return lang
    base = lang.split("-")[0].split("_")[0]
    return base if base in _TEXTS else "en"


def text(hass: HomeAssistant | None, key: str, **params: Any) -> str:
    """Return the localized text for key, formatted with params."""
    template = _TEXTS[language(hass)].get(key) or _TEXTS["en"].get(key, key)
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return template


def default_scenario_names(scenario_id: str) -> set[str]:
    """Return the default names of a built-in scenario in all languages."""
    key = f"scenario_{scenario_id}"
    return {texts[key] for texts in _TEXTS.values() if key in texts}
