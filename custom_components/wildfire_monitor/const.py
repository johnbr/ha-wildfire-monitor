"""Constants for the Wildfire Monitor integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "wildfire_monitor"
SOURCE: Final = "wildfire_monitor"

# CAL FIRE public incident feed (keyless JSON array of active incidents).
CALFIRE_URL: Final = "https://incidents.fire.ca.gov/umbraco/Api/IncidentApi/List?inactive=false"

# Config / options keys.
CONF_ALERT_DISTANCE: Final = "alert_distance_km"
CONF_ALERT_MIN_ACRES: Final = "alert_min_acres"
CONF_SCAN_INTERVAL: Final = "scan_interval_min"

# Defaults (all user-editable).
DEFAULT_MONITORING_RADIUS: Final = 150.0  # km — which fires to track at all
DEFAULT_ALERT_DISTANCE: Final = 30.0  # km — "close to home" threshold
DEFAULT_ALERT_MIN_ACRES: Final = 0  # acres — minimum size to alert on
DEFAULT_SCAN_INTERVAL: Final = 10  # minutes

# Bus event fired when a new fire crosses the alert threshold.
EVENT_WILDFIRE_ALERT: Final = "wildfire_monitor_alert"

# Entity attribute keys.
ATTR_EXTERNAL_ID: Final = "external_id"
ATTR_ACRES: Final = "acres"
ATTR_CONTAINMENT: Final = "containment"
ATTR_COUNTY: Final = "county"
ATTR_LOCATION: Final = "location"
ATTR_TYPE: Final = "type"
ATTR_STARTED: Final = "started"
ATTR_UPDATED: Final = "updated"
ATTR_URL: Final = "url"

# Unit label for acreage (no core constant exists for acres).
UNIT_ACRES: Final = "acres"
