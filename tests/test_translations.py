"""Translation completeness: every language covers exactly the English keys."""

import json
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "cover_automatic"
TRANSLATIONS = COMPONENT / "translations"
PANEL_JS = COMPONENT / "panel" / "cover-automatic-panel.js"
LANGUAGES = ("de", "fr")

PLACEHOLDER = re.compile(r"\{\w+\}")


def _flatten(tree: dict, prefix: str = "") -> dict[str, str]:
    """Map dotted key paths to leaf strings."""
    flat: dict[str, str] = {}
    for key, value in tree.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{path}."))
        else:
            flat[path] = value
    return flat


def _load_translation(lang: str) -> dict[str, str]:
    return _flatten(json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8")))


def _load_panel_i18n() -> dict[str, dict[str, str]]:
    """Parse the panel's I18N object literal (string leaves, unquoted keys)."""
    src = PANEL_JS.read_text(encoding="utf-8")
    start = src.index("const I18N = {") + len("const I18N = ")
    end = src.index("\n};", start) + len("\n}")
    block = re.sub(r"^\s*//.*$", "", src[start:end], flags=re.M)
    block = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', block)
    block = re.sub(r",(\s*})", r"\1", block)
    return {lang: _flatten(tree) for lang, tree in json.loads(block).items()}


def _assert_same_keys_and_placeholders(reference: dict[str, str], other: dict[str, str]) -> None:
    assert sorted(set(reference) - set(other)) == [], "missing keys"
    assert sorted(set(other) - set(reference)) == [], "keys not in English"
    mismatched = [
        key for key, text in reference.items() if set(PLACEHOLDER.findall(text)) != set(PLACEHOLDER.findall(other[key]))
    ]
    assert mismatched == [], "placeholders differ from English"


def test_strings_json_matches_english() -> None:
    strings = _flatten(json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8")))
    assert strings == _load_translation("en")


@pytest.mark.parametrize("lang", LANGUAGES)
def test_backend_translation_matches_english(lang: str) -> None:
    _assert_same_keys_and_placeholders(_load_translation("en"), _load_translation(lang))


@pytest.mark.parametrize("lang", LANGUAGES)
def test_panel_translation_matches_english(lang: str) -> None:
    i18n = _load_panel_i18n()
    assert lang in i18n
    _assert_same_keys_and_placeholders(i18n["en"], i18n[lang])
