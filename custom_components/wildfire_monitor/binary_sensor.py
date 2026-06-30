"""Binary sensor platform for Wildfire Monitor — the close-to-home alert."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WildfireConfigEntry, WildfireDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the wildfire alert binary sensor."""
    async_add_entities([WildfireAlertBinarySensor(entry.runtime_data)])


class WildfireAlertBinarySensor(CoordinatorEntity[WildfireDataUpdateCoordinator], BinarySensorEntity):
    """On when at least one tracked fire is within the alert threshold."""

    _attr_has_entity_name = True
    _attr_translation_key = "wildfire_alert"
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:fire-alert"

    def __init__(self, coordinator: WildfireDataUpdateCoordinator) -> None:
        """Initialise the alert binary sensor."""
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_wildfire_alert"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Wildfire Monitor",
            manufacturer="CAL FIRE",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.alerting)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        alerting = self.coordinator.alerting
        if not alerting:
            return {"fire_count": 0}
        nearest = min(alerting.values(), key=lambda fire: fire.distance_km)
        return {
            "fire_count": len(alerting),
            "nearest_name": nearest.name,
            "nearest_distance_km": nearest.distance_km,
            "nearest_acres": nearest.acres,
            "nearest_containment": nearest.contained,
            "nearest_county": nearest.county,
            "nearest_url": nearest.url,
        }
