"""Native Home Assistant conditions inside CoverAutomatic rules.

A rule condition of type ``ha_condition`` stores a condition written in the
same format as the ``condition:`` section of a Home Assistant automation
(state, numeric_state, template, zone, and/or/not, ...). Home Assistant
validates and evaluates it; this module wraps that for the rule engine.

The raw configuration (plain JSON-compatible dict) is what gets stored. It is
compiled into a checker once and cached by the engine; evaluation is then a
cheap synchronous call.
"""
from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import voluptuous as vol
import yaml

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import condition as ha_condition
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.template import Template

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CompiledCondition:
    """A validated and compiled Home Assistant condition."""

    checker: Any = None
    entities: set[str] = field(default_factory=set)
    error: str | None = None
    error_code: str | None = None
    # Entities found statically (entity_id fields) and the templates whose
    # referenced entities are re-read by refresh_template_entities().
    static_entities: set[str] = field(default_factory=set)
    templates: list[Any] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """Return True if the condition compiled successfully."""
        return self.checker is not None


def config_key(config: Any) -> str:
    """Stable cache key for a raw condition configuration."""
    return json.dumps(config, sort_keys=True, default=str)


def parse_yaml(text: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Parse YAML text into a condition config.

    A list of conditions is accepted and wrapped in an ``and`` condition,
    like the ``condition:`` list of an automation.
    Returns (config, error). error is a dict {code, detail, line, column}
    so the panel can localize the message.
    """
    if not isinstance(text, str) or not text.strip():
        return None, None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as err:
        mark = getattr(err, "problem_mark", None)
        return None, {
            "code": "yaml",
            "detail": getattr(err, "problem", None) or str(err),
            "line": mark.line + 1 if mark else None,
            "column": mark.column + 1 if mark else None,
        }
    if isinstance(data, list):
        data = {"condition": "and", "conditions": data}
    if not isinstance(data, dict):
        return None, {"code": "not_mapping", "detail": None, "line": None, "column": None}
    return data, None


def dump_yaml(config: dict[str, Any] | None) -> str:
    """Serialize a condition config to YAML (key order preserved)."""
    if not config:
        return ""
    return yaml.safe_dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _find_templates(validated: Any) -> list[Template]:
    """Templates contained in a validated config."""
    templates: list[Template] = []
    stack = [validated]
    while stack:
        item = stack.pop()
        if isinstance(item, Template):
            templates.append(item)
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
    return templates


def _render_entities(hass: HomeAssistant, templates: list[Template]) -> set[str]:
    """Entities the templates currently reference (best effort).

    A template's entities can change from one rendering to the next (e.g.
    {{ states(states('input_text.target')) }}), so this is re-run by
    refresh_template_entities() before every update cycle. Limitation: the
    referenced set is only as current as the last refresh; a change of the
    indirection entity is picked up at the next cycle, not instantly.
    """
    entities: set[str] = set()
    for template in templates:
        try:
            if template.hass is None:
                template.hass = hass
            entities |= set(template.async_render_to_info().entities)
        except Exception:  # noqa: BLE001 -- best effort, rendering may fail
            pass
    return entities


def _template_entities(hass: HomeAssistant, validated: Any) -> set[str]:
    """Collect entities referenced by templates inside a validated config."""
    return _render_entities(hass, _find_templates(validated))


def refresh_template_entities(hass: HomeAssistant, compiled: CompiledCondition) -> bool:
    """Re-render the templates of a compiled condition; True if entities changed."""
    if compiled.checker is None or not compiled.templates:
        return False
    entities = compiled.static_entities | _render_entities(hass, compiled.templates)
    if entities == compiled.entities:
        return False
    compiled.entities = entities
    return True


async def async_compile(hass: HomeAssistant, config: Any) -> CompiledCondition:
    """Validate and compile a raw condition config (never raises)."""
    if not isinstance(config, dict) or not config:
        return CompiledCondition(error="empty condition", error_code="empty")
    try:
        validated = cv.CONDITION_SCHEMA(copy.deepcopy(config))
        validated = await ha_condition.async_validate_condition_config(hass, validated)
        checker = await ha_condition.async_from_config(hass, validated)
    except (vol.Invalid, HomeAssistantError, ValueError, KeyError, TypeError) as err:
        return CompiledCondition(error=str(err), error_code="invalid")
    except Exception as err:  # noqa: BLE001 -- e.g. a failing integration platform
        _LOGGER.warning("Unexpected error compiling Home Assistant condition %s: %s", config, err)
        return CompiledCondition(error=str(err) or type(err).__name__, error_code="invalid")
    try:
        static = set(ha_condition.async_extract_entities(validated))
    except Exception as err:  # noqa: BLE001 -- entities are only used to listen
        _LOGGER.debug("Cannot extract entities of %s: %s", config, err)
        static = set()
    templates = _find_templates(validated)
    entities = static | _render_entities(hass, templates)
    return CompiledCondition(
        checker=checker, entities=entities,
        static_entities=static, templates=templates,
    )


def evaluate(hass: HomeAssistant, compiled: CompiledCondition | None) -> bool:
    """Evaluate a compiled condition. Invalid or failing conditions are False.

    A disabled condition (``enabled: false``) returns None from HA and is
    treated as met, like HA ignores it inside an automation.
    """
    return evaluate_tristate(hass, compiled) is True


def evaluate_tristate(hass: HomeAssistant, compiled: CompiledCondition | None) -> bool | None:
    """Evaluate a compiled condition: True/False, or None when unknown.

    None = not compiled, invalid, or the evaluation raised (e.g. an entity
    without a numeric state), so a negated condition is never met by it.
    """
    if compiled is None or compiled.checker is None:
        return None
    try:
        result = compiled.checker(hass, None)
    except Exception as err:  # noqa: BLE001 -- ConditionError & template errors
        _LOGGER.debug("Home Assistant condition not evaluable (error: %s)", err)
        return None
    return True if result is None else bool(result)


def simple_reading(hass: HomeAssistant, config: Any) -> dict[str, Any] | None:
    """Return the current value a simple state/numeric_state condition reads.

    Used by the rule editor preview to show e.g. "Absent" next to the
    condition. Only for a single entity (optionally inside one ``not``).
    """
    cfg = config
    if isinstance(cfg, dict) and cfg.get("condition") == "not":
        subs = cfg.get("conditions") or []
        cfg = subs[0] if len(subs) == 1 else None
    if not isinstance(cfg, dict) or cfg.get("condition") not in ("state", "numeric_state"):
        return None
    entity_id = cfg.get("entity_id")
    if isinstance(entity_id, list):
        entity_id = entity_id[0] if len(entity_id) == 1 else None
    if not isinstance(entity_id, str):
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    attribute = cfg.get("attribute")
    value = state.attributes.get(attribute) if attribute else state.state
    if value is None:
        return None
    return {"entity_id": entity_id, "attribute": attribute, "value": value}
