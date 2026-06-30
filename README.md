# Wildfire Monitor for Home Assistant

A custom integration that tracks **active California wildfires** from the public
[CAL FIRE incident feed](https://www.fire.ca.gov/incidents/) and surfaces them in
Home Assistant:

- 🗺️ **Map markers** — every active fire within your configured radius appears on the
  HA map (`geo_location` entities) with its size, containment %, county and distance
  from home.
- 📊 **Aggregate sensors** — number of fires in range, distance to the nearest fire,
  and the largest fire's acreage.
- 🚨 **Close-to-home alert** — `binary_sensor.wildfire_alert` turns on when a fire is
  within your alert distance (and optional minimum size), and a `wildfire_monitor_alert`
  event is fired so you can send notifications from an automation.

Data comes from CAL FIRE's keyless public API (no API key required). California only.

## Installation (HACS)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/johnbr/ha-wildfire-monitor`
   as an **Integration**.
2. Install **Wildfire Monitor**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Wildfire Monitor**.
4. The setup form is pre-centred on your HA home — drag the marker and radius to set the
   **area to monitor** (which fires to track). You can cover a region far wider than home.
   Distances and the close-to-home alert are always measured from your HA home location,
   pulled live, **not** from this area's centre.

Manual install: copy `custom_components/wildfire_monitor` into your HA `config/custom_components/`
directory and restart.

## Options

**Settings → Devices & Services → Wildfire Monitor → Configure**:

| Option | Default | Meaning |
| --- | --- | --- |
| Alert distance (km) | 30 | A fire closer than this trips `binary_sensor.wildfire_alert`. |
| Minimum fire size (acres) | 0 | Ignore fires smaller than this for alerting. |
| Update interval (minutes) | 10 | How often CAL FIRE is polled. |

The monitored area (centre + radius — which fires are tracked at all) is set on the map
during setup. Distances and alerting are measured from your HA home, which is read live
from Home Assistant and not stored in this integration.

## Entities

| Entity | Description |
| --- | --- |
| `geo_location.*` | One marker per active fire in the monitored area (state = distance from home in km). Attributes: `acres`, `containment`, `county`, `location`, `started`, `updated`, `url`. |
| `binary_sensor.wildfire_alert` | `on` when a fire is within the alert threshold. Attributes describe the nearest qualifying fire. |
| `sensor.*_wildfires_in_range` | Count of tracked fires. |
| `sensor.*_nearest_wildfire_distance` | Distance (km) to the closest fire. |
| `sensor.*_largest_wildfire_size` | Acreage of the largest tracked fire. |

## Example notification automation

```yaml
automation:
  - alias: "Notify on nearby wildfire"
    trigger:
      - platform: event
        event_type: wildfire_monitor_alert
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🔥 Wildfire near home"
          message: >-
            {{ trigger.event.data.name }} is {{ trigger.event.data.distance_km }} km away
            ({{ trigger.event.data.acres }} acres, {{ trigger.event.data.containment }}% contained).
          data:
            url: "{{ trigger.event.data.url }}"
```

You can equally trigger on `binary_sensor.wildfire_alert` turning `on`.

## Data source & attribution

Incident data © [CAL FIRE](https://www.fire.ca.gov/). This project is not affiliated with
or endorsed by CAL FIRE. The feed reports point locations only (no burn-perimeter polygons).

## Development

This repo mirrors the tooling of its sibling integrations: `ruff` (lint + format), `pytest`
for repo sanity checks, `pre-commit` hooks, and `release-please` for versioning. Hassfest and
HACS validation run in CI.

```bash
ruff check .
ruff format .
pytest tests/ -v
```

## Roadmap

- NIFC WFIGS perimeter polygons rendered via the `ha-map-card` frontend card.
- Optional NASA FIRMS satellite hotspot early-detection layer.

## License

MIT — see [LICENSE](LICENSE).
