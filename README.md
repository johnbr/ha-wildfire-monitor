# Wildfire Monitor for Home Assistant

A custom integration that tracks **active California wildfires** from the public
[CAL FIRE incident feed](https://www.fire.ca.gov/incidents/) and surfaces them in
Home Assistant:

- 🗺️ **Map markers** — every active fire within your configured radius appears on the
  HA map (`geo_location` entities) with its size, containment %, county and distance
  from home.
- 📊 **Aggregate sensors** — number of fires in range, distance to the nearest fire,
  and the largest fire's acreage.
- 🚨 **Close-to-home alert** — a `wildfire_monitor_alert` event fires for each fire that
  comes within your alert distance (and optional minimum size), so you can send
  notifications from an automation, and the *Wildfire alert* binary sensor is on while
  any fire qualifies.

Data comes from CAL FIRE's keyless public API (no API key required). California only.

## Installation

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=johnbr&repository=ha-wildfire-monitor&category=integration)

1. In HACS, search for **Wildfire Monitor**, download it (or use the button above), and
   restart Home Assistant.
2. **Settings → Devices & Services → Add Integration → Wildfire Monitor**.
3. The setup form is pre-centred on your HA home — drag the marker and radius to set the
   **area to monitor** (which fires to track). You can cover a region far wider than home.
   Distances and the close-to-home alert are always measured from your HA home location,
   pulled live, **not** from this area's centre.

If HACS doesn't list it yet, add it as a custom repository instead: HACS → **⋮** →
**Custom repositories** → `https://github.com/johnbr/ha-wildfire-monitor`, category
**Integration**, then continue from step 1.

Manual install: copy `custom_components/wildfire_monitor` into your HA `config/custom_components/`
directory and restart.

Requires Home Assistant 2025.3 or later.

## Options

**Settings → Devices & Services → Wildfire Monitor → Configure**:

| Option | Default | Meaning |
| --- | --- | --- |
| Alert distance (km) | 30 | A fire closer than this fires the alert event and turns on the *Wildfire alert* binary sensor. |
| Minimum fire size (acres) | 0 | Ignore fires smaller than this for alerting. |
| Update interval (minutes) | 10 | How often CAL FIRE is polled. |

The monitored area (centre + radius — which fires are tracked at all) is set on the map
during setup. Distances and alerting are measured from your HA home, which is read live
from Home Assistant and not stored in this integration.

The area can't be edited afterwards. To move or resize it, delete the integration entry
and add it again. Delete first: a second entry for the same fires creates duplicate
`geo_location` entities with a `_2` suffix.

## Entities

| Entity | Description |
| --- | --- |
| `geo_location.*` | One marker per active fire in the monitored area (state = distance from home in km). Attributes: `acres`, `containment`, `county`, `location`, `started`, `updated`, `url`. |
| `binary_sensor.wildfire_monitor_wildfire_alert` | `on` while any fire is within the alert threshold. Attributes describe the nearest qualifying fire. |
| `sensor.wildfire_monitor_wildfires_in_range` | Count of tracked fires. |
| `sensor.wildfire_monitor_nearest_wildfire_distance` | Distance to the closest fire. |
| `sensor.wildfire_monitor_largest_wildfire_size` | Acreage of the largest tracked fire. |

The entity IDs above are the defaults; Home Assistant derives them from the device name,
so they change if you rename the device.

## Dashboard cards

The fires are plain `geo_location` entities, so the built-in **Map** card plots them with no
extra components, and a templated **Markdown** card gives a list sorted by distance from home.
Paste this `vertical-stack` (Map on top, list below — or split them into separate cards):

```yaml
type: vertical-stack
cards:
  - type: map
    auto_fit: true
    entities:
      - zone.home
    geo_location_sources:
      - wildfire_monitor
  - type: markdown
    title: Active wildfires
    content: |
      {% set fires = states.geo_location | selectattr('attributes.source', 'eq', 'wildfire_monitor') | list -%}
      {% if fires | count == 0 -%}
      _No active wildfires in the monitored area._
      {%- else -%}
      {% set ns = namespace(rows=[]) -%}
      {% for e in fires -%}
      {% set ns.rows = ns.rows + [{'name': e.name, 'mi': (e.state | float(0)) * 0.621371, 'acres': e.attributes.get('acres') | float(0), 'cont': e.attributes.get('containment'), 'county': e.attributes.get('county'), 'url': e.attributes.get('url')}] -%}
      {% endfor -%}
      {% set ns2 = namespace(lines=['| # | Fire | Dist | Acres | Cont. | County |', '|--:|:--|--:|--:|--:|:--|']) -%}
      {% for r in ns.rows | sort(attribute='mi') -%}
      {% set ns2.lines = ns2.lines + ['| ' ~ loop.index ~ ' | [' ~ r.name ~ '](' ~ (r.url or '#') ~ ') | ' ~ '%.1f'|format(r.mi) ~ ' mi | ' ~ '{:,.0f}'.format(r.acres) ~ ' | ' ~ ((r.cont|round|int|string ~ '%') if r.cont is not none else '—') ~ ' | ' ~ (r.county or '—') ~ ' |'] -%}
      {% endfor -%}
      {{ ns2.lines | join('\n') }}
      {%- endif %}
```

Distances are shown in miles (the geo_location state is km; the `* 0.621371` converts it —
drop that factor to show km). The Map auto-fits to all markers and home; with a wide monitored
area it may zoom out across the state — set `auto_fit: false` and a `default_zoom:` to keep it
near home.

## The alert event

`wildfire_monitor_alert` fires once for each fire that newly meets the alert threshold:

| Field | Meaning |
| --- | --- |
| `entry_id` | The config entry that raised it |
| `name` | Fire name |
| `distance_km` | Distance from your HA home, in km |
| `acres` | Acres burned (may be `null`) |
| `containment` | Percent contained (may be `null`) |
| `county` | County |
| `location` | CAL FIRE's location description |
| `url` | CAL FIRE incident page |

Which fires have already alerted is held in memory, so after a Home Assistant restart, or
an options change (which reloads the entry), the first update fires the event again for
every fire that still qualifies. That errs on the side of telling you twice rather than not
at all; tag your notification with the fire's name, as below, so the repeat replaces the
first one instead of buzzing again.

## Example notification automation

```yaml
automation:
  - alias: "Notify on nearby wildfire"
    mode: queued
    triggers:
      - trigger: event
        event_type: wildfire_monitor_alert
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "🔥 Wildfire near home"
          message: >-
            {{ trigger.event.data.name }} is {{ trigger.event.data.distance_km }} km away
            ({{ trigger.event.data.acres }} acres, {{ trigger.event.data.containment }}% contained).
          data:
            tag: "wildfire-{{ trigger.event.data.name }}"
            url: "{{ trigger.event.data.url }}"
```

Trigger on the event, not on the binary sensor. The sensor is a roll-up: it is already
`on` while any fire qualifies, so a second fire crossing the threshold doesn't change its
state and a state trigger stays silent in exactly the case that matters. Its `nearest_*`
attributes also describe the nearest fire, which need not be the one that just crossed.
`mode: queued` keeps two fires that cross in the same update from dropping one.

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
