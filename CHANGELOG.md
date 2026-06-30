# Changelog

All notable changes to this project are documented in this file. Versions are managed
automatically by [release-please](https://github.com/googleapis/release-please) from
Conventional Commit messages.

## 0.1.0

- Initial release: track active California wildfires from the CAL FIRE incident feed.
- `geo_location` map markers per fire (size, containment %, county, distance from home).
- Aggregate sensors: fires in range, nearest-fire distance, largest-fire acreage.
- `binary_sensor.wildfire_alert` plus a `wildfire_monitor_alert` event for close-to-home alerting.
- UI config flow (home location + monitoring radius) with options for alert distance,
  minimum fire size, and scan interval.
