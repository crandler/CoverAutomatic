"""Data update coordinator for CoverAutomatic."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .engine import RuleEngine
from .models import CoverConfig, CoverStatus
from .storage import CoverAutomaticStorage
from .sun import SUN_ENTITY_ID

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant

_LOGGER = logging.getLogger(__name__)


class CoverAutomaticCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data updates and rule evaluation."""

    def __init__(
        self, hass: HomeAssistant, storage: CoverAutomaticStorage, scan_interval: int = DEFAULT_SCAN_INTERVAL
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.storage = storage
        self.engine = RuleEngine(hass, storage)
        self._tracked_entities: set[str] = set()
        self._unsub_state_change: list[Any] = []
        self._cover_states: dict[str, CoverStatus] = {}
        self._last_positions: dict[str, int | None] = {}

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self.storage.async_load()
        await self._async_setup_default_scenarios()
        self._setup_state_tracking()

    async def _async_setup_default_scenarios(self) -> None:
        """Create default scenarios if none exist."""
        if not self.storage.scenarios:
            from .models import Scenario

            defaults = [
                Scenario(
                    id="everyday",
                    name="Everyday",
                    icon="mdi:home",
                ),
                Scenario(
                    id="summer",
                    name="Summer",
                    icon="mdi:white-balance-sunny",
                ),
                Scenario(
                    id="winter",
                    name="Winter",
                    icon="mdi:snowflake",
                ),
                Scenario(
                    id="vacation",
                    name="Vacation",
                    icon="mdi:airplane",
                ),
                Scenario(
                    id="cinema",
                    name="Cinema",
                    icon="mdi:movie",
                ),
                Scenario(
                    id="manual",
                    name="Manual",
                    icon="mdi:hand-back-right",
                ),
            ]
            for scenario in defaults:
                await self.storage.async_add_scenario(scenario)

    def _setup_state_tracking(self) -> None:
        """Set up state change tracking for relevant entities."""
        entities_to_track: set[str] = {SUN_ENTITY_ID}

        for entity_id in self.storage._data.get("covers", {}):
            entities_to_track.add(entity_id)

        if self.storage.outdoor_temp_sensor:
            entities_to_track.add(self.storage.outdoor_temp_sensor)

        for rule_data in self.storage._data.get("rules", {}).values():
            for condition in rule_data.get("conditions", []):
                if sensor := condition.get("params", {}).get("sensor"):
                    entities_to_track.add(sensor)
                if entity := condition.get("params", {}).get("entity"):
                    entities_to_track.add(entity)

        new_entities = entities_to_track - self._tracked_entities

        if new_entities:
            unsub = async_track_state_change_event(
                self.hass,
                list(new_entities),
                self._async_on_state_change,
            )
            self._unsub_state_change.append(unsub)
            self._tracked_entities.update(new_entities)

    def refresh_state_tracking(self) -> None:
        """Refresh state tracking after configuration changes."""
        self._setup_state_tracking()

    @callback
    def _async_on_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if entity_id in self.storage._data.get("covers", {}):
            self._handle_cover_state_change(entity_id, old_state, new_state)
        else:
            self.hass.async_create_task(self.async_request_refresh())

    def _handle_cover_state_change(
        self, entity_id: str, old_state: Any, new_state: Any
    ) -> None:
        """Handle cover position changes to detect manual overrides."""
        if new_state is None:
            return

        cover = self.storage.covers.get(entity_id)
        if cover is None:
            return

        expected_position = self._last_positions.get(entity_id)

        try:
            current_position = int(new_state.attributes.get("current_position", 0))
        except (ValueError, TypeError):
            return

        if expected_position is not None and current_position != expected_position:
            if cover.auto_enabled and self._cover_states.get(entity_id) == CoverStatus.AUTO:
                _LOGGER.debug(
                    "Manual override detected for %s (expected %s, got %s)",
                    entity_id,
                    expected_position,
                    current_position,
                )
                self._pause_cover(cover)

    def _pause_cover(self, cover: CoverConfig) -> None:
        """Pause automation for a cover."""
        self._cover_states[cover.entity_id] = CoverStatus.PAUSED
        pause_until = dt_util.now().timestamp() + (cover.pause_duration * 60)
        self.storage.update_cover_status(
            cover.entity_id, CoverStatus.PAUSED.value, pause_until
        )
        self.async_set_updated_data(self.data)

    def resume_cover(self, entity_id: str) -> None:
        """Resume automation for a cover."""
        if self.storage.get_cover_raw(entity_id):
            self._cover_states[entity_id] = CoverStatus.AUTO
            self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
            self.async_set_updated_data(self.data)

    def get_cover_status(self, entity_id: str) -> CoverStatus:
        """Get automation status for a cover."""
        cover_raw = self.storage.get_cover_raw(entity_id)
        if cover_raw is None:
            return CoverStatus.MANUAL

        if not cover_raw.get("auto_enabled", True):
            return CoverStatus.MANUAL

        status = self._cover_states.get(entity_id, CoverStatus.AUTO)

        if status == CoverStatus.PAUSED:
            pause_until = cover_raw.get("pause_until")
            if pause_until and dt_util.now().timestamp() > pause_until:
                self._cover_states[entity_id] = CoverStatus.AUTO
                self.storage.update_cover_status(entity_id, CoverStatus.AUTO.value, None)
                return CoverStatus.AUTO

        return status

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and evaluate rules."""
        result: dict[str, Any] = {
            "covers": {},
            "facades": {},
            "scenario": self.storage.active_scenario,
        }

        for facade_id, facade in self.storage.facades.items():
            from .sun import is_sun_on_facade

            result["facades"][facade_id] = {
                "sun_on_facade": is_sun_on_facade(self.hass, facade),
            }

        for entity_id, cover in self.storage.covers.items():
            status = self.get_cover_status(entity_id)
            target_position: int | None = None

            if status == CoverStatus.AUTO:
                target_position = self.engine.evaluate_cover(cover)
                if target_position is not None:
                    self._last_positions[entity_id] = target_position

            result["covers"][entity_id] = {
                "status": status.value,
                "target_position": target_position,
                "facade_id": cover.facade_id,
            }

        # Store result first so async_apply_positions can use it
        self.data = result

        # Apply calculated positions to covers
        await self.async_apply_positions()

        return result

    async def async_apply_positions(self) -> None:
        """Apply calculated positions to covers."""
        if not self.data:
            return

        for entity_id, cover_data in self.data.get("covers", {}).items():
            if cover_data["status"] != CoverStatus.AUTO.value:
                continue

            target = cover_data.get("target_position")
            if target is None:
                continue

            state = self.hass.states.get(entity_id)
            if state is None:
                continue

            try:
                current = int(state.attributes.get("current_position", 0))
            except (ValueError, TypeError):
                continue

            if current != target:
                _LOGGER.debug("Setting %s to position %s", entity_id, target)
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=False,
                )

    def async_shutdown(self) -> None:
        """Shut down coordinator."""
        for unsub in self._unsub_state_change:
            unsub()
        self._unsub_state_change.clear()
