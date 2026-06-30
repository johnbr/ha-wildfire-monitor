"""Geolocation (map marker) platform for Wildfire Monitor.

Each active fire near home is a transient ``geo_location`` entity that renders as
a marker on the Home Assistant map. Entities are added/removed dynamically as
fires appear in and drop out of the coordinator data.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACRES,
    ATTR_CONTAINMENT,
    ATTR_COUNTY,
    ATTR_EXTERNAL_ID,
    ATTR_LOCATION,
    ATTR_STARTED,
    ATTR_TYPE,
    ATTR_UPDATED,
    ATTR_URL,
    SOURCE,
)
from .coordinator import Fire, WildfireConfigEntry, WildfireDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up wildfire map markers and keep them in sync with the coordinator."""
    coordinator = entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _async_sync_markers() -> None:
        new_entities = [
            WildfireLocationEvent(coordinator, uid, tracked) for uid in coordinator.data if uid not in tracked
        ]
        for entity in new_entities:
            tracked.add(entity.uid)
        if new_entities:
            async_add_entities(new_entities)

    _async_sync_markers()
    entry.async_on_unload(coordinator.async_add_listener(_async_sync_markers))


class WildfireLocationEvent(CoordinatorEntity[WildfireDataUpdateCoordinator], GeolocationEvent):
    """A single wildfire shown as a map marker."""

    _attr_should_poll = False
    _attr_source = SOURCE
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: WildfireDataUpdateCoordinator,
        uid: str,
        tracked: set[str],
    ) -> None:
        """Initialise the marker for a given incident id."""
        super().__init__(coordinator)
        self.uid = uid
        self._tracked = tracked
        self._removing = False
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{uid}"

    @property
    def _fire(self) -> Fire | None:
        return self.coordinator.data.get(self.uid)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Remove the marker when its fire is no longer active / in range."""
        if self._fire is None and not self._removing:
            self._removing = True
            self._tracked.discard(self.uid)
            self.hass.async_create_task(self.async_remove(force_remove=True))
            return
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        return super().available and self._fire is not None

    @property
    def name(self) -> str | None:
        fire = self._fire
        return fire.name if fire else None

    @property
    def distance(self) -> float | None:
        fire = self._fire
        return fire.distance_km if fire else None

    @property
    def latitude(self) -> float | None:
        fire = self._fire
        return fire.latitude if fire else None

    @property
    def longitude(self) -> float | None:
        fire = self._fire
        return fire.longitude if fire else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fire = self._fire
        if fire is None:
            return None
        attrs = {
            ATTR_EXTERNAL_ID: fire.uid,
            ATTR_ACRES: fire.acres,
            ATTR_CONTAINMENT: fire.contained,
            ATTR_COUNTY: fire.county,
            ATTR_LOCATION: fire.location,
            ATTR_TYPE: fire.fire_type,
            ATTR_STARTED: fire.started,
            ATTR_UPDATED: fire.updated,
            ATTR_URL: fire.url,
        }
        return {key: value for key, value in attrs.items() if value is not None}
