# Bundled timetable card

The integration includes `custom:schulmanager-schedule-card` in
`custom_components/schulmanager_online/www/schulmanager-schedule-card.js`.
At startup it copies/registers the JavaScript resource for Lovelace. This card
is experimental and separate from the extended school dashboard built using
`custom:button-card` and HA helper templates.

For additional lessons, manual period hiding/replacement, school-event helpers
and the extended day/week plans, use the [dashboard extensions guide](Dashboard_Extensions.md).
Those features are not implemented by this bundled card.

## Views and configuration

| `view` | Display |
| --- | --- |
| `weekly_matrix` | Week as a grid of days and periods; default |
| `weekly_list` | Weekly lesson list |
| `daily_list` | Today's lessons |
| `compact` | Compact lesson display |

The card requires an `entity` and supports `title`, `view` and a `column_size`
override. Select your real entity ID; the following is only a placeholder:

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.schulmanager_your_student_this_week
view: weekly_matrix
title: School timetable
```

The source also declares defaults for options such as `show_header`,
`show_breaks`, `highlight_current`, `highlight_changes`, `color_scheme`,
`time_format`, `language` and `max_days`, but the current renderer does not read
those configuration fields. They should not be advertised as working controls.
Source-defined display styles and substitution markers still exist independently
of those unused settings.

## Entity discovery and sample data

The card extracts a student identifier from legacy entity-name patterns and then
looks for sensors such as `sensor.schulmanager_<student>_this_week`. Current HA
entity names can differ, especially after migrations or user renames. Pointing
`entity` at a valid sensor does not guarantee that all related sensors will be
found.

The card attempts to read arrays under `lessons`, `schedule`, `data` or `items`
from discovered sensors. If discovery yields no usable lessons, it can generate
sample timetable data. Check the actual sensor's `lessons` and `data_status`
attributes to distinguish source data from a demonstration display.

For a dependable display with current entities, standard HA calendar/entities
cards can consume the integration directly. The separate extended dashboard
uses explicit sensor attributes and separately configured calendar helpers.

[Back to README](../README.md)
