"""Aggregate sensor platform for Wildfire Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, UNIT_ACRES
from .coordinator import Fire, WildfireConfigEntry, WildfireDataUpdateCoordinator


def _nearest(fires: list[Fire]) -> Fire | None:
    return min(fires, key=lambda fire: fire.distance_km) if fires else None


def _largest(fires: list[Fire]) -> Fire | None:
    return max(fires, key=lambda fire: fire.acres or 0) if fires else None


def _fire_attrs(fire: Fire | None) -> dict[str, Any]:
    if fire is None:
        return {}
    return {
        "name": fire.name,
        "acres": fire.acres,
        "containment": fire.contained,
        "county": fire.county,
        "distance_km": fire.distance_km,
        "url": fire.url,
    }


@dataclass(frozen=True, kw_only=True)
class WildfireSensorDescription(SensorEntityDescription):
    """Describes a Wildfire Monitor aggregate sensor."""

    value_fn: Callable[[list[Fire]], float | int | None]
    attr_fn: Callable[[list[Fire]], dict[str, Any]] | None = None


SENSORS: tuple[WildfireSensorDescription, ...] = (
    WildfireSensorDescription(
        key="fires_in_range",
        translation_key="fires_in_range",
        icon="mdi:fire",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=len,
    ),
    WildfireSensorDescription(
        key="nearest_distance",
        translation_key="nearest_distance",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fires: nearest.distance_km if (nearest := _nearest(fires)) else None,
        attr_fn=lambda fires: _fire_attrs(_nearest(fires)),
    ),
    WildfireSensorDescription(
        key="largest_acres",
        translation_key="largest_acres",
        icon="mdi:fire-alert",
        native_unit_of_measurement=UNIT_ACRES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fires: largest.acres if (largest := _largest(fires)) else None,
        attr_fn=lambda fires: _fire_attrs(_largest(fires)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the aggregate wildfire sensors."""
    coordinator = entry.runtime_data
    async_add_entities(WildfireSensor(coordinator, description) for description in SENSORS)


class WildfireSensor(CoordinatorEntity[WildfireDataUpdateCoordinator], SensorEntity):
    """An aggregate sensor summarising tracked wildfires."""

    _attr_has_entity_name = True
    entity_description: WildfireSensorDescription

    def __init__(
        self,
        coordinator: WildfireDataUpdateCoordinator,
        description: WildfireSensorDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Wildfire Monitor",
            manufacturer="CAL FIRE",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _fires(self) -> list[Fire]:
        return list(self.coordinator.data.values())

    @property
    def native_value(self) -> float | int | None:
        return self.entity_description.value_fn(self._fires)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self._fires)
