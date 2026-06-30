"""DataUpdateCoordinator for the Wildfire Monitor integration.

Polls the CAL FIRE public incident feed, keeps the active California wildfires
within the configured monitoring radius, computes each fire's distance from the
Home Assistant home location, and fires a bus event when a fire newly crosses the
alert threshold.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.location import distance as location_distance

from .const import (
    CALFIRE_URL,
    CONF_ALERT_DISTANCE,
    CONF_ALERT_MIN_ACRES,
    CONF_SCAN_INTERVAL,
    DEFAULT_ALERT_DISTANCE,
    DEFAULT_ALERT_MIN_ACRES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_WILDFIRE_ALERT,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


@dataclass(slots=True)
class Fire:
    """A single active wildfire near home."""

    uid: str
    name: str
    latitude: float
    longitude: float
    distance_km: float
    acres: float | None
    contained: float | None
    county: str | None
    location: str | None
    fire_type: str | None
    started: str | None
    updated: str | None
    url: str | None
    is_calfire: bool


class WildfireDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Fire]]):
    """Fetch and filter active California wildfires from CAL FIRE."""

    config_entry: WildfireConfigEntry

    def __init__(self, hass: HomeAssistant, entry: WildfireConfigEntry) -> None:
        """Initialise the coordinator from the config entry."""
        # The configured location + radius define the AREA to monitor (which
        # fires to track). Distances ("from home") are measured separately from
        # the live HA home location — see _async_update_data.
        self._area_lat: float = entry.data[CONF_LATITUDE]
        self._area_lon: float = entry.data[CONF_LONGITUDE]
        self._area_radius_km: float = entry.data[CONF_RADIUS]

        options = entry.options
        self._alert_distance_km: float = options.get(CONF_ALERT_DISTANCE, DEFAULT_ALERT_DISTANCE)
        self._alert_min_acres: float = options.get(CONF_ALERT_MIN_ACRES, DEFAULT_ALERT_MIN_ACRES)
        scan_interval: int = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        # Fires currently meeting the alert threshold — read by the binary_sensor.
        self.alerting: dict[str, Fire] = {}
        self._alerting_uids: set[str] = set()

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Fire]:
        """Fetch incidents from CAL FIRE and return those near home."""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await session.get(CALFIRE_URL)
                response.raise_for_status()
                # CAL FIRE serves JSON without a strict content-type header.
                records = await response.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Error fetching CAL FIRE incidents: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Invalid JSON from CAL FIRE: {err}") from err

        if not isinstance(records, list):
            raise UpdateFailed("Unexpected CAL FIRE response (expected a list)")

        # Home location is pulled live from HA so distances always reflect the
        # current home, independent of the monitored area.
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude

        fires: dict[str, Fire] = {}
        for record in records:
            if record.get("Type") != "Wildfire" or not record.get("IsActive"):
                continue
            uid = record.get("UniqueId")
            lat = record.get("Latitude")
            lon = record.get("Longitude")
            if not uid or lat is None or lon is None:
                continue

            # Track the fire only if it falls inside the monitored area.
            area_meters = location_distance(self._area_lat, self._area_lon, lat, lon)
            if area_meters is None or area_meters / 1000 > self._area_radius_km:
                continue

            # The distance shown and alerted on is measured from the HA home.
            home_meters = location_distance(home_lat, home_lon, lat, lon)
            distance_km = round((home_meters if home_meters is not None else area_meters) / 1000, 1)

            fires[uid] = Fire(
                uid=uid,
                name=record.get("Name") or "Unknown fire",
                latitude=lat,
                longitude=lon,
                distance_km=distance_km,
                acres=record.get("AcresBurned"),
                contained=record.get("PercentContained"),
                county=record.get("County"),
                location=record.get("Location"),
                fire_type=record.get("Type"),
                started=record.get("Started"),
                updated=record.get("Updated"),
                url=record.get("Url"),
                is_calfire=bool(record.get("CalFireIncident")),
            )

        self._evaluate_alerts(fires)
        return fires

    def _evaluate_alerts(self, fires: dict[str, Fire]) -> None:
        """Update the alerting set and fire an event for newly qualifying fires."""
        qualifying = {
            uid: fire
            for uid, fire in fires.items()
            if fire.distance_km <= self._alert_distance_km and (fire.acres or 0) >= self._alert_min_acres
        }

        for uid in set(qualifying) - self._alerting_uids:
            fire = qualifying[uid]
            _LOGGER.warning(
                "Wildfire alert: %s is %.1f km from home (%.0f acres, %s%% contained)",
                fire.name,
                fire.distance_km,
                fire.acres or 0,
                fire.contained if fire.contained is not None else "?",
            )
            self.hass.bus.async_fire(
                EVENT_WILDFIRE_ALERT,
                {
                    "entry_id": self.config_entry.entry_id,
                    "name": fire.name,
                    "distance_km": fire.distance_km,
                    "acres": fire.acres,
                    "containment": fire.contained,
                    "county": fire.county,
                    "location": fire.location,
                    "url": fire.url,
                },
            )

        self.alerting = qualifying
        self._alerting_uids = set(qualifying)


type WildfireConfigEntry = ConfigEntry[WildfireDataUpdateCoordinator]
