# Changelog

All notable changes to this project are documented in this file. Versions are managed
automatically by [release-please](https://github.com/googleapis/release-please) from
Conventional Commit messages.

## [0.2.0](https://github.com/johnbr/ha-wildfire-monitor/compare/v0.1.0...v0.2.0) (2026-06-30)


### Features

* initial Wildfire Monitor integration ([6b8296c](https://github.com/johnbr/ha-wildfire-monitor/commit/6b8296c9ff0d89244b10f5d87bc13dd9788c2e5b))


### Bug Fixes

* measure fire distance from HA home, separate from monitored area ([69e5fea](https://github.com/johnbr/ha-wildfire-monitor/commit/69e5fea7fc911b84cd0ebf6a88c3667813816e7b))

## 0.1.0

- Initial release: track active California wildfires from the CAL FIRE incident feed.
- `geo_location` map markers per fire (size, containment %, county, distance from home).
- Aggregate sensors: fires in range, nearest-fire distance, largest-fire acreage.
- `binary_sensor.wildfire_alert` plus a `wildfire_monitor_alert` event for close-to-home alerting.
- UI config flow (home location + monitoring radius) with options for alert distance,
  minimum fire size, and scan interval.
