# Homework and grade events

The coordinator fires two Home Assistant events after successful data refreshes.
Create your own automations to turn them into phone notifications, announcements
or dashboard updates. These are event-bus messages, separate from calendar entries.

## Event payloads

| Event | Fields |
| --- | --- |
| `schulmanager_homework_new` | `student_id`, `student_name`, `subject`, `homework`, `date` |
| `schulmanager_grade_new` | `student_id`, `student_name`, `subject`, `grade` |

Values depend on the data returned by the school's API. Homework `subject` and
`homework` fields are forwarded from the source item; templates should accommodate
the source's value shape. Grade subjects are resolved from the subject name or
long name, with a fallback label. Grade values come from the API's `value` field.

The first successful refresh records the existing items without firing events.
Later refreshes emit an event when an item has a previously unseen key:

- Homework: student, date, subject and homework/description text.
- Grade: student, subject identity, value and date/entry date.

An edit that changes that key can therefore appear as a new item. Known keys are
held in memory and are re-seeded after the integration restarts. The integration
polls every 15 minutes; these are refresh-driven notifications, not server push.
Enable homework/grade fetching in the integration options for the corresponding
data to be available. Grade fetching is experimental and off by default.

## Notify about new homework

Replace the placeholder notification action with your device's actual action.
Optionally add a condition on `trigger.event.data.student_id` for one student.

```yaml
alias: School - new homework
triggers:
  - trigger: event
    event_type: schulmanager_homework_new
actions:
  - action: notify.mobile_app_phone
    data:
      title: "New homework"
      message: >-
        {{ trigger.event.data.student_name }}:
        {{ trigger.event.data.subject }} —
        {{ trigger.event.data.homework }}
        ({{ trigger.event.data.date }})
mode: queued
```

## Notify about a new grade

```yaml
alias: School - new grade
triggers:
  - trigger: event
    event_type: schulmanager_grade_new
actions:
  - action: notify.mobile_app_phone
    data:
      title: "New grade"
      message: >-
        {{ trigger.event.data.student_name }}:
        {{ trigger.event.data.subject }} — {{ trigger.event.data.grade }}
mode: queued
```

## Timetable changes

There is no dedicated timetable-change bus event in the current implementation.
Use the **Changes Detected** sensor's `changes` attribute for room, subject,
teacher and other field edits. Explicit school cancellations and events remain
in timetable lesson attributes. See the [sensor reference](Sensors_Documentation.md).

[Back to README](../README.md)
