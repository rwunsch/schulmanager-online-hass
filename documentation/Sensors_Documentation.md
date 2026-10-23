# Sensors and timetable attributes

This reference describes the implemented sensor platform in release 1.3.0.
There are **nine timetable sensors**, plus **four homework** and **four exam
sensors when enabled**, per student. Experimental grade averages are optional.
The coordinator polls every **15 minutes**; there are no separate five-minute
or hourly polling schedules for individual sensors.

Entity IDs are assigned by Home Assistant and can retain older names or user
renames. Select the actual entities under **Settings → Devices & services →
Schulmanager Online**. Examples below use placeholders. Unique IDs use the
student ID, preserving entity identity across student display-name changes.

## Sensor overview

| Sensor | State / detail attributes |
| --- | --- |
| Current Lesson | Subject/room or `No current lesson`; current lesson fields |
| Next Lesson | Subject/start time or `No upcoming lessons`; next lesson fields |
| Lessons Today | Source row count; `lessons`, `total_lessons`, `free_hours`, `lessons_by_hour`, subjects, teachers, change count |
| Lessons Tomorrow | Source row count; corresponding tomorrow attributes |
| Lessons Next School Day | Summary and lesson attributes for the next weekday with timetable rows, searched up to seven days ahead |
| Changes Today | Change count and details supplied by the current timetable |
| Lessons This Week | Week summary; `lessons`, `total_lessons`, `free_hours`, `lessons_by_day`, subjects, teachers |
| Lessons Next Week | Separate lesson, event and cancellation summary; occupied-period attributes below |
| Changes Detected | Change summary; `has_changes`, `change_count`, `changes` |
| Homework Due Today / Tomorrow | Count and `homework` entries |
| Homework Overdue | Count and `homework` entries, including `days_overdue` |
| Homework Upcoming | Next seven days after today; count and `homework` entries |
| Exams Today / This Week / Next Week / Upcoming | Count and `exams` entries; upcoming covers the next 30 days |

Daily row counts and generic summaries are not interchangeable with attended
period counts. Source lists can contain `freeHour`, `cancelledLesson`, events
and repeated period rows. The next-week occupied-period summary is deliberately
more specific than the generic daily/this-week counters. For dashboard attendance
summaries, filter by lesson type and apply the intended period de-duplication.

## Shared metadata and data freshness

Ordinary timetable, homework and exam sensors include `student_id`,
`student_name`, `class_name`, `data_status` and `last_error`. Available school
metadata includes `institution_id`, `institution_name`, `institution_name_short`,
`institution_city` and `institution_address`.

| `data_status` | Meaning |
| --- | --- |
| `loaded` | Data fetched successfully |
| `partial` | Timetable loaded, but a supplementary request failed; some fields use defaults or previous data |
| `stale` | An update failed and the last successful data is retained |
| `not_loaded` | No successful data is available yet; stable empty defaults are exposed |

An empty list is not proof that the school has no lessons if the data is stale
or has not loaded. Inspect `data_status` together with `last_error`.

## Lesson list format

Schedule list sensors expose formatted rows in `lessons`. This synthetic example
uses times with seconds because those strings are retained from processed data;
consumers should accept both `HH:MM` and `HH:MM:SS` within the interval.

```json
{
  "subject": "Mathematics",
  "subject_abbreviation": "M",
  "subject_sanitized": "Mathematics",
  "time": "09:10:00-09:55:00",
  "room": "R101",
  "teacher": "EX",
  "teacher_lastname": "Teacher",
  "teacher_firstname": "Example",
  "is_substitution": false,
  "type": "regularLesson",
  "comment": "",
  "date": "2026-10-22",
  "class_hour": 2
}
```

`class_hour` may be absent/empty for unnumbered lessons. Do not force an AG onto
the default numbered-period grid. Current/next lesson attributes instead expose
individual timing fields such as `start_time` and `end_time`.

| Field / type | Meaning |
| --- | --- |
| `subject` | Subject display name from the processed timetable |
| `subject_abbreviation` | School abbreviation when supplied |
| `subject_sanitized` | Display name cleaned for speech/templates |
| `regularLesson` | Ordinary timetable lesson |
| `changedLesson` | Explicitly changed lesson |
| `is_substitution` | Substitution marker; cancellations are not classified as substitutions |
| `cancelledLesson` | Officially cancelled source lesson |
| `event` | School event; its title is also exposed as `event_title` |
| `freeHour` | Free-period row; not a calendar event |

Where available, rows also contain `original_subject`, `original_room`,
`original_teacher` and `original_comment`. This preserves the cancelled or
changed lesson's original details. It does not depend on a dashboard trying to
reconstruct the previous lesson from its displayed title.

## Next-week events and occupied periods

The next-week summary can read:

```text
6 lessons, 5 subjects; Project day (6 periods); 6 cancelled
```

Its attributes separate the underlying records from effective occupied periods:

| Attribute | Meaning |
| --- | --- |
| `total_lessons` | Effective active lesson periods excluding school events |
| `scheduled_periods` | Effective active periods including school events |
| `event_periods` | Occupied school-event periods |
| `cancelled_periods` | Distinct periods carrying cancellation entries |
| `lessons_by_day` | Active lesson periods by date, excluding school events |
| `scheduled_periods_by_day` | Active periods by date, including school events |
| `events` | Events grouped by date/title, with `periods` and `period_count` |
| `cancelled_lessons` | Detailed cancelled rows |
| `lessons` | Complete source rows, including events, cancellations and free periods |

For each period, an active event is preferred over another active lesson in the
next-week effective-period calculation. A cancelled original and a replacement
are not counted as two attended periods. Cancellation details remain available
even when the period is occupied by its replacement. For missing period numbers,
the calculation uses available times, then the source ID or a row-specific key.

```jinja
{% set events = state_attr('sensor.lessons_next_week_your_student', 'events') or [] %}
{% for event in events %}
{{ event.title }} on {{ event.date }}: {{ event.periods | join(', ') }}
{% endfor %}
```

## Field-level changes

The **Changes Detected** sensor exposes a `changes` list. Each item contains
`type`, `date`, `class_hour` and `description`; available `current`/`previous`
objects include formatted subject, room, teacher and time. Modified items also
include `field_changes` entries containing `field`, `display_name`, `previous`
and `current`.

Convenience attributes inside a change item include `subject_old`/`subject_new`,
`room_old`/`room_new` and `teacher_old`/`teacher_new` when those fields change.
The teacher-list field is renamed to `teacher` for those convenience keys.

Changes are detected by comparing refreshes, or by comparing API original values
with current values, even on first load. Explicit `cancelledLesson` and `event`
rows are not reported as generic field edits. Removed and added source lessons
can appear with `type: removed` and `type: added`.

## Optional data and dashboard helpers

Homework attributes are under `homework`; exam entries are under `exams` and
contain subject, title, date, time, period, type and available room/teacher/comment
fields. Upcoming exam entries include relative-day information and identify the
next exam. Grade sensors provide an overall mean and per-subject means for the
numeric grades the integration can parse; they are experimental and created
from subjects available at setup.

Fetching letters is an option, but the currently loaded platforms are sensor and
calendar: there is no dedicated letter entity or editable homework to-do list
created by this integration. A `todo.py` source file alone does not enable a
platform.

Sensors for external-calendar additions, cleaned extra-lesson counts,
replacement school events and exams on the next school day belong to the
separately configured dashboard templates. They are not extra entities
created by installing the integration. See [dashboard extensions](Dashboard_Extensions.md)
and [homework/grade events](Integration_Events.md).

[Back to README](../README.md)
