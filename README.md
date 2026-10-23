# Schulmanager Online for Home Assistant

[![Latest release](https://img.shields.io/github/v/release/tkarle/schulmanager-online-hass)](https://github.com/tkarle/schulmanager-online-hass/releases)
[![HACS custom repository](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License](https://img.shields.io/github/license/tkarle/schulmanager-online-hass)](LICENSE)

A custom Home Assistant integration for [Schulmanager Online](https://login.schulmanager-online.de/). It provides timetable, change, homework and exam sensors, calendars, and a bundled Lovelace timetable card. Multiple students and accounts with access to multiple schools are supported.

The extended school dashboard also supports **additional lessons (Zusatzunterricht), hiding individual periods, and replacing lessons with school events through a separate calendar**. These features use separately configured HA templates and dashboard cards. They are documented in the [dashboard extensions guide](documentation/Dashboard_Extensions.md); installing the integration alone does not install that dashboard.

Version 1.3.1 requires **Home Assistant 2026.10.0 or newer** for entry-scoped device registry APIs. Existing device/entity identifiers and calendar behavior are retained. See the [maintenance notes](documentation/Maintenance_2026-10.md) for bundle discovery, fallback policy and migration details.

## Feature map

| Feature | Provided by | Details |
| --- | --- | --- |
| Nine timetable sensors per student | Integration | Current/next lesson, today, tomorrow, next school day, both weeks, changes today, detected changes |
| AGs and lessons without a period number | Integration | Actual start/end times are retained in calendar events |
| Substitutions and original values | Integration | Subject, room, teacher and comment before/after values where supplied by the API |
| Cancellations and school events | Integration | Explicit lesson types, calendar cancellation controls, next-week event and occupied-period totals |
| Additional lessons from a personal calendar | Extended dashboard | Extra entries with time, period, room, teacher and optional icon |
| Manually hide or replace periods | Extended dashboard | Calendar description rules such as `Action: hide` or `Action: replace` |
| Day/week plans, exam badges, end-of-school summaries | Extended dashboard | Combines timetable attributes, exams and calendar additions |
| New homework and grade notifications | Integration + your automations | `schulmanager_homework_new` and `schulmanager_grade_new` events |
| Last successful data after API failures | Integration | `data_status` and `last_error` expose freshness and errors |

The dashboard extensions are separate from the bundled experimental `schulmanager-schedule-card`. Their installation-specific dashboard YAML and helper sensors are not shipped as an automatically installed add-on. The guide explains the requirements and the calendar format used by the existing extension.

## Features

### Timetable sensors

Each student gets sensors for:

- Current lesson and next lesson
- Lessons today, tomorrow, and on the next school day
- Lessons this week and next week
- Changes today and detected timetable changes

Schedule sensors include structured `lessons` attributes with date, period, time, subject, room, teacher, lesson type, and substitution details where the API provides them. Subject names are also exposed as `subject_sanitized` for templates and voice announcements. API failures are marked with `data_status` and `last_error`; the integration keeps the last successful data when an update fails.

Changed lessons can retain `original_subject`, `original_room`, `original_teacher` and `original_comment`. The **Changes Detected** sensor exposes field-level before/after values, including `subject_old`/`subject_new`, `room_old`/`room_new` and `teacher_old`/`teacher_new` when those fields changed. API-provided original values can be used on the first refresh, without needing a previous poll. See the [current sensor reference](documentation/Sensors_Documentation.md).

Free periods are represented as `type: freeHour` in timetable attributes and are omitted from calendar entries. The extended dashboard distinguishes internal free periods from empty cells before and after school. Raw sensor row counts can include free periods and cancellation rows; use the documented attributes and lesson types for attendance summaries.

The **Lessons Next Week** sensor reports active lessons, school events, and cancelled periods separately. If a school event replaces cancelled lessons, the event and cancellation entries remain available in the `lessons` attribute, while counts are de-duplicated by date and period. For example:

```text
6 lessons, 5 subjects; Franziskustag (6 periods); 6 cancelled
```

Its attributes include `total_lessons`, `scheduled_periods`, `event_periods`, `cancelled_periods`, `lessons_by_day`, `scheduled_periods_by_day`, `events`, `cancelled_lessons`, and the complete `lessons` list. Event lesson rows use `type: event` and expose the event name as `subject` and `event_title`. Cancelled rows use `type: cancelledLesson` and preserve original subject, room, and teacher values when available.

### Homework, exams, and grades

- Optional homework sensors: due today, due tomorrow, overdue, and upcoming in the next seven days.
- Optional exam sensors: today, this week, next week, and the next 30 days.
- Optional experimental grade sensors: an overall average and one average per subject, when grade data is available.
- A schedule calendar is created for each student. Homework and exam calendars can be enabled in the integration options.

### Timetable calendars, AGs, and cancellations

Numbered calendar lessons use the school's API class-hour grid when available, with estimated fallback times if it is missing. **Unnumbered AGs and special lessons use their actual supplied start/end times**. For example, an AG from 14:17 to 15:42 keeps that interval. A missing or empty subject falls back to `subject_name`, then `Lesson`; it no longer drops the calendar event.

Calendar entries include subject, period when present, room, teachers, lesson type and comment when available. With highlighting enabled, substitutions use `🔄` and cancellations use `❌ … (Cancelled)`. With highlighting disabled, substitutions use a plain title and visible cancellations use `X … (Cancelled)`.

| Highlight schedule changes | Hide cancellations when highlight is off | Calendar result |
| --- | --- | --- |
| On | Either | Highlighted substitutions and visible cancellations |
| Off | Off (default) | Plain substitution titles; cancellations remain visible |
| Off | On | Plain substitution titles; cancellation-only groups are hidden |

When the source entries share a day and period, an active replacement takes precedence over the cancelled original. Repeated cancellation entries in that group produce one event. This calendar grouping does not remove the detailed source rows from timetable sensor attributes.

The integration's timetable calendar is generated from Schulmanager data. To add a personal lesson, hide a period, or replace several periods in the extended dashboard, use a **separate writable calendar** as described below. Those local display rules do not edit the school's timetable or the integration's generated calendar.

### Additional lessons and manual calendar rules

The extended dashboard reads a separate calendar through template sensors with an `events` attribute. A timed entry with a title adds a lesson; its description can specify:

```text
Class Hour: 8
Room: R101
Teacher: Example Teacher
Icon: mdi:human-male-board
```

Use `Action: hide` with `Class Hour: 3-4` to hide those periods on the entry's date. Use `Action: replace` with a title such as `Project day` and `Class Hour: 1-5` to show a school event in place of those lessons. The supported German keys include `Aktion`, `Stunde`, `Raum`, `Lehrer` and `Symbol`.

The [dashboard extensions guide](documentation/Dashboard_Extensions.md) includes complete add/hide/replace examples, refresh behavior, helper sensor requirements, day/week views and the limits of these local overrides.

### Lovelace timetable card

The integration bundles `schulmanager-schedule-card`, with weekly matrix, weekly list, daily list, and compact views. Home Assistant copies it to `/local/` and registers it when the integration starts. The card is experimental and uses legacy entity-name discovery; if discovery fails, it can display generated sample data. Check actual sensor attributes before relying on its display. It does not implement the external-calendar `Action` rules. See the [bundled card reference](documentation/Custom_Card_Documentation.md).

The examples below use placeholder entity IDs. Select the actual IDs created for your student under **Settings → Devices & services → Schulmanager Online**.

## Installation

### HACS

1. In HACS, open **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/tkarle/schulmanager-online-hass` and choose **Integration**.
3. Download **Schulmanager Online** and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration**, search for **Schulmanager Online**, and sign in.

### Manual

Copy `custom_components/schulmanager_online` from a release into `<config>/custom_components/schulmanager_online`, then restart Home Assistant and add the integration from **Settings → Devices & services**.

## Setup and options

Sign in with the email address and password for your Schulmanager Online account. The integration discovers the students associated with the account. For accounts with access to more than one school, school information is discovered during setup.

In the integration's **Configure** dialog, you can set:

| Option | Description | Default |
| --- | --- | --- |
| Weeks to look ahead | Timetable range, from 1 to 4 weeks | 2 |
| Include homework | Create homework sensors and calendar | On |
| Include exams/tests | Create exam sensors and calendar | On |
| Include letters/messages | Fetch letter data | On |
| Include grades | Fetch grades and create average sensors | Off |
| Highlight schedule changes | Use emoji markers for substitutions and cancellations in the timetable calendar | On |
| Hide cancellations when highlight is off | Hide cancellation-only calendar entries while highlighting is disabled | Off |

The integration polls Schulmanager Online every 15 minutes. Timetable sensor calculations use Home Assistant's configured local time zone.

## Dashboard examples

### Schedule summary

```yaml
type: entities
title: School
entities:
  - entity: sensor.current_lesson_your_student
    name: Current lesson
  - entity: sensor.next_lesson_your_student
    name: Next lesson
  - entity: sensor.lessons_today_your_student
    name: Lessons today
  - entity: sensor.lessons_changes_today_your_student
    name: Changes today
```

### Next-week event and cancellation details

```yaml
type: entities
title: Next week
entities:
  - entity: sensor.lessons_next_week_your_student
    name: Lessons, events, and cancellations
    secondary_info: last-changed
```

To build a grid or a custom card, use the sensor's `lessons` attribute. Each row contains a `date`, `class_hour`, `time`, `type`, and display fields. Event rows contain `event_title`; cancelled lessons retain `original_subject`, `original_room`, and `original_teacher` where available. The separate `events` attribute groups an event by title and date and lists its periods.

For example, a template can show the event periods without counting the cancelled originals again:

```jinja
{% set events = state_attr('sensor.lessons_next_week_your_student', 'events') or [] %}
{% for event in events %}
{{ event.title }} on {{ event.date }}: periods {{ event.periods | join(', ') }}
{% endfor %}
```

### Calendar

```yaml
type: calendar
initial_view: listWeek
entities:
  - calendar.lessons_your_student
  - calendar.homework_your_student
  - calendar.exams_your_student
```

Homework and exam calendar entities only exist when their options are enabled.

## Automation example

Notify when the state of the next-week summary changes:

```yaml
alias: School schedule update
triggers:
  - trigger: state
    entity_id: sensor.lessons_next_week_your_student
actions:
  - action: notify.mobile_app_phone
    data:
      title: School timetable update
      message: >-
        {{ states('sensor.lessons_next_week_your_student') }}
mode: single
```

For detailed changes, read the `changes` attribute from the **Changes Detected** sensor. Each item includes a date, period, change type, previous and current lesson data, and a description. Explicit cancellations and school events are represented in the timetable rather than being reported as field edits.

### New homework and grade events

The integration also fires `schulmanager_homework_new` and `schulmanager_grade_new` on Home Assistant's event bus. Both include `student_id`, `student_name` and `subject`; homework events add `homework` and `date`, while grade events add `grade`. Grade fetching must be enabled for grade events.

The first successful load seeds the known items without notifying about existing homework or grades. Later refreshes emit events for newly seen keys. This tracking is held in memory and starts again after the integration restarts. The events do not create notifications by themselves. See [event payloads and notification examples](documentation/Integration_Events.md).

## Services

The integration provides these `schulmanager_online` services:

- `refresh`: request an immediate data refresh; limited to once every five minutes.
- `clear_cache`: clear cached authentication tokens so the next update authenticates again.
- `clear_debug`: remove debug dump files created by the integration.

## Troubleshooting

1. Confirm the integration is loaded under **Settings → Devices & services** and that its student device has entities.
2. Check **Developer tools → States** for each sensor's `data_status` and `last_error` attributes.
3. Use the `schulmanager_online.refresh` service to request an update.
4. If authentication fails, check the account credentials and try `schulmanager_online.clear_cache`.
5. For detailed logs, add this to `configuration.yaml` and restart Home Assistant:

   ```yaml
   logger:
     logs:
       custom_components.schulmanager_online: debug
   ```

Please remove credentials and personal student information before attaching logs or diagnostics to an issue.

## Development and support

- [Issues](https://github.com/tkarle/schulmanager-online-hass/issues)
- [Releases](https://github.com/tkarle/schulmanager-online-hass/releases)
- [Sensor attribute reference](documentation/Sensors_Documentation.md)
- [Additional lessons, manual cancellations, and dashboard extensions](documentation/Dashboard_Extensions.md)
- [Homework and grade events](documentation/Integration_Events.md)
- [Documentation index](documentation/README.md)
- [API troubleshooting](documentation/Schedule_API_Troubleshooting.md)

This project is not affiliated with Schulmanager Online. See [LICENSE](LICENSE) for license terms.
