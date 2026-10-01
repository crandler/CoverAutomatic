"""Switch platform for CoverAutomatic."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIGNAL_ENTITIES_CHANGED
from .coordinator import CoverAutomaticCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import CoverAutomaticConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CoverAutomaticConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities, and those of covers added later."""
    coordinator = entry.runtime_data.coordinator
    storage = coordinator.storage
    known_covers: set[str] = set()

    async_add_entities([CoverAutomaticMasterSwitch(coordinator, entry.entry_id)])

    @callback
    def _async_add_new_entities() -> None:
        entities: list[SwitchEntity] = [
            CoverAutomaticAutoSwitch(coordinator, entity_id, cover.name)
            for entity_id, cover in storage.covers.items()
            if entity_id not in known_covers
        ]
        # Forget removed ones so a re-added cover gets its switch again
        known_covers.clear()
        known_covers.update(storage.covers)
        if entities:
            async_add_entities(entities)

    _async_add_new_entities()
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_ENTITIES_CHANGED, _async_add_new_entities)
    )


class CoverAutomaticMasterSwitch(CoordinatorEntity[CoverAutomaticCoordinator], SwitchEntity):
    """Global master switch to enable/disable all CoverAutomatic automation."""

    _attr_has_entity_name = True
    _attr_translation_key = "master_enabled"

    def __init__(self, coordinator: CoverAutomaticCoordinator, entry_id: str) -> None:
        """Initialize the master switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_master"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "CoverAutomatic",
            "manufacturer": "CoverAutomatic",
            "model": "Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return true if global automation is enabled."""
        return self.coordinator.storage.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable global automation."""
        self.coordinator.storage.enabled = True
        await self.coordinator.storage.async_save()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable global automation."""
        self.coordinator.storage.enabled = False
        await self.coordinator.storage.async_save()
        self.async_write_ha_state()


class CoverAutomaticAutoSwitch(CoordinatorEntity[CoverAutomaticCoordinator], SwitchEntity):
    """Switch to enable/disable automation for a cover."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_enabled"

    def __init__(
        self,
        coordinator: CoverAutomaticCoordinator,
        cover_entity_id: str,
        cover_name: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._cover_entity_id = cover_entity_id
        self._attr_unique_id = f"{DOMAIN}_{cover_entity_id}_auto"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cover_entity_id)},
            "name": f"CoverAutomatic {cover_name}",
            "manufacturer": "CoverAutomatic",
            "model": "Cover Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return true if automation is enabled."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        return cover.auto_enabled if cover else False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = True
            await self.coordinator.storage.async_add_cover(cover)
            self.coordinator.resume_cover(self._cover_entity_id)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable automation."""
        cover = self.coordinator.storage.covers.get(self._cover_entity_id)
        if cover:
            cover.auto_enabled = False
            await self.coordinator.storage.async_add_cover(cover)
            self.coordinator.set_cover_manual(self._cover_entity_id)
            if self.coordinator.data is not None:
                self.coordinator.async_set_updated_data(self.coordinator.data)
            self.async_write_ha_state()
