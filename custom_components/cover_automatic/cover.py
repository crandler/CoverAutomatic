"""Cover platform for CoverAutomatic."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoverAutomaticCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cover entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CoverAutomaticCoordinator = data["coordinator"]

    entities: list[CoverEntity] = []

    for entity_id, cover in coordinator.storage.covers.items():
        entities.append(
            CoverAutomaticCover(coordinator, entity_id, cover.name)
        )

    async_add_entities(entities)


class CoverAutomaticCover(CoordinatorEntity[CoverAutomaticCoordinator], CoverEntity):
    """Wrapper cover entity with automation awareness."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        wrapped_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = cover_name
        self._attr_unique_id = f"{DOMAIN}_{wrapped_entity_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, wrapped_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def _wrapped_state(self):
        """Get the wrapped cover state."""
        return self.hass.states.get(self._wrapped_entity_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._wrapped_state is not None

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        state = self._wrapped_state
        if state is None:
            return None
        return state.state == "closed"

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover."""
        state = self._wrapped_state
        if state is None:
            return None
        return state.attributes.get(ATTR_POSITION)

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Return supported features."""
        state = self._wrapped_state
        if state is None:
            return CoverEntityFeature(0)
        return CoverEntityFeature(state.attributes.get("supported_features", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        status = self.coordinator.get_cover_status(self._wrapped_entity_id)
        cover_data = {}
        if self.coordinator.data:
            cover_data = self.coordinator.data.get("covers", {}).get(
                self._wrapped_entity_id, {}
            )

        return {
            "automation_status": status.value,
            "target_position": cover_data.get("target_position"),
            "wrapped_entity": self._wrapped_entity_id,
        }

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.services.async_call(
            "cover",
            "open_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.hass.services.async_call(
            "cover",
            "close_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.services.async_call(
            "cover",
            "stop_cover",
            {"entity_id": self._wrapped_entity_id},
            blocking=True,
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        await self.hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": self._wrapped_entity_id, "position": position},
            blocking=True,
        )
