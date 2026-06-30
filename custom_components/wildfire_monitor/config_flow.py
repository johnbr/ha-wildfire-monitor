"""Config flow for the Wildfire Monitor integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_RADIUS,
    UnitOfLength,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util.unit_conversion import DistanceConverter

from .const import (
    CONF_ALERT_DISTANCE,
    CONF_ALERT_MIN_ACRES,
    CONF_SCAN_INTERVAL,
    DEFAULT_ALERT_DISTANCE,
    DEFAULT_ALERT_MIN_ACRES,
    DEFAULT_MONITORING_RADIUS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

DEFAULT_RADIUS_M = DistanceConverter.convert(DEFAULT_MONITORING_RADIUS, UnitOfLength.KILOMETERS, UnitOfLength.METERS)

LOCATION_SCHEMA = vol.Schema(
    {vol.Required(CONF_LOCATION): selector.LocationSelector(selector.LocationSelectorConfig(radius=True))}
)


class WildfireConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI config flow for Wildfire Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask the user for the area (home location + monitoring radius)."""
        if user_input is None:
            suggested = {
                CONF_LOCATION: {
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                    CONF_RADIUS: DEFAULT_RADIUS_M,
                }
            }
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(LOCATION_SCHEMA, suggested),
            )

        location = user_input[CONF_LOCATION]
        latitude = location[CONF_LATITUDE]
        longitude = location[CONF_LONGITUDE]
        self._async_abort_entries_match({CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude})

        radius_km = round(
            DistanceConverter.convert(location[CONF_RADIUS], UnitOfLength.METERS, UnitOfLength.KILOMETERS),
            1,
        )
        return self.async_create_entry(
            title=f"Wildfires in area near {latitude:.3f}, {longitude:.3f}",
            data={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
                CONF_RADIUS: radius_km,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WildfireOptionsFlow:
        """Return the options flow handler."""
        return WildfireOptionsFlow()


class WildfireOptionsFlow(OptionsFlow):
    """Handle alert/interval options for Wildfire Monitor."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the alert distance, minimum size and scan interval."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ALERT_DISTANCE,
                    default=options.get(CONF_ALERT_DISTANCE, DEFAULT_ALERT_DISTANCE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=500,
                        step=1,
                        unit_of_measurement="km",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_ALERT_MIN_ACRES,
                    default=options.get(CONF_ALERT_MIN_ACRES, DEFAULT_ALERT_MIN_ACRES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=1000000,
                        step=1,
                        unit_of_measurement="acres",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=2,
                        max=120,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
