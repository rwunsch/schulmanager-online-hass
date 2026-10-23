# Extended dashboard: additional lessons and calendar overrides

This guide documents the existing school-dashboard extensions for additional
lessons (Zusatzunterricht), hiding periods and replacing lessons with school
events. Their behavior was checked against the local dashboard and the active
HA calendar-bridge/helper templates for release 1.3.0.

## Components and prerequisites

The Python integration provides timetable and exam sensors plus generated
calendars. The extended dashboard combines those sensors with a **separate
writable calendar** using HA templates and `custom:button-card` templates.
Its badges also use Mushroom cards. The complete dashboard and helper YAML are
installation-specific and are not included or installed by this release.
This guide describes their existing contract and how to use an already
configured extended dashboard; it is not a standalone dashboard installer.

The configured dashboard needs:

1. The integration's actual timetable sensor IDs for today, next school day,
   this week and next week, plus exam/change sensors for the relevant displays.
2. A separate calendar for local additions and rules, for example
   `calendar.student_additional_lessons`. Create entries in this calendar,
   rather than the generated Schulmanager timetable calendar.
3. A calendar bridge that calls `calendar.get_events` and exposes its returned
   list as the `events` attribute of helper sensors for today, tomorrow,
   next school day, this week and next week.
4. The extended day/week card templates configured with those helper sensors
   through their `external_sensor` variable. The bundled
   `custom:schulmanager-schedule-card` does not read that variable or these rules.

In the existing bridge, refreshes occur at HA startup, every 15 minutes, when the
source calendar or relevant timetable sensors change, and when a dedicated
refresh input button is pressed. The next-school-day range follows the date in
the integration's next-school-day lessons. If no date is available, its calendar
query falls back to tomorrow; it does not search indefinitely for a future AG.

## What the extended dashboard adds

| Feature | Behavior in the configured dashboard |
| --- | --- |
| Day and week views | Show timetable lessons together with additional calendar entries |
| Manual hiding | Remove selected source periods from the dashboard display on the event's date |
| Manual replacement | Replace selected periods with a titled school event, shown per covered period |
| Status and summaries | Include additional lessons in the current-status display and school-end summaries |
| School-event helpers | Expose whether a replacement exists today/next school day, with its title, periods, room, teacher and icon |
| Cleaned additional-lesson count | Exclude hide and replacement rules from the separate additional-lesson badge |
| Exam badges | Match exam data to lessons by date and available period/subject details |
| Original values | Show changes in subject, teacher and room using supplied original/change fields |
| Cancellation display | Keep explicit cancellations identifiable instead of treating them as generic field edits |
| Internal gaps | Show free periods between lessons; leading/trailing empty week-grid cells stay neutral |
| Split-lesson display | In the day/week plans, duplicate source slots can use the immediately following empty/free placeholder when it is unoccupied |

These features transform the dashboard's displayed data. They do not write back
to Schulmanager, change the integration's sensor attributes or cancel events in
its generated calendar. To view local entries in a standard HA calendar card,
add the separate calendar to that card explicitly; `Action: hide`/`replace`
remain dashboard rules and are not interpreted by the standard calendar card.

## Calendar description format

Create **timed, same-day events** with start/end times and a title. Put one field
on each description line, starting at the left edge. Use the canonical keys below
for consistent behavior across the day, week and summary templates.

| Field | German alias | Meaning |
| --- | --- | --- |
| `Action` | `Aktion` | Omit to add a lesson; `hide` to remove displayed periods; `replace` to replace them |
| `Class Hour` | `Stunde`, `Schulstunde` | A single period such as `3`, or an inclusive range such as `3-4` |
| `Room` | `Raum` | Room label; the calendar location is used if this field is absent |
| `Teacher` | `Lehrer` | Teacher display text |
| `Icon` | `Symbol` | Optional icon such as `mdi:calendar-star` |

Use `Action: hide` and `Action: replace` as the common syntax. The day/week plans
and helper templates also accept `remove`, `delete`, `ausblenden`, `löschen` or
`loeschen` for hiding, and `override`, `ersetzen`, `ueberschreiben` or
`überschreiben` for replacement. Some week-view-only aliases, such as `cancel`
or `Hide: true`, are not shared by all helpers; use the common syntax above.

Use a simple number or hyphen range, not a comma-separated period list. Supply
`Class Hour` for hide/replace rules: the day plan uses period matching, while the
week plan additionally has an exact start/end-time fallback. An arbitrary overlap
is not sufficient. The rule targets all matching periods on that date, regardless
of the original subject or the rule event's title.

## Example: add an AG or extra lesson

Create an event in the separate calendar with:

- Title: `Robotics AG`
- Start/end: the relevant school day, 14:17–15:42
- Description:

```text
Class Hour: 8
Room: R101
Teacher: Example Teacher
Icon: mdi:human-male-board
```

With no `Action`, the entry is added without removing the original timetable.
The title becomes the displayed subject, and the supplied event times remain
the times of the added lesson. This is a local dashboard addition, distinct from
an AG already returned by the school's API.

The calendar itself can carry entries without a period number. The week grid
is period-based, however; supply a suitable `Class Hour` to place local additions
in a numbered row. Unnumbered API AGs retain their real times in the integration's
generated calendar independently of this dashboard feature.

## Example: hide periods 3–4

Create a timed event on the affected date, covering the intended school interval:

- Title: `Personal timetable exception`
- Description:

```text
Action: hide
Class Hour: 3-4
```

The extended day/week views remove the source lessons in those periods. The rule
itself is not displayed as an extra lesson. Deleting the rule from the separate
calendar restores the underlying display after its bridge refreshes.

This hides a local display entry; an official cancellation from Schulmanager
remains a separate `cancelledLesson` source entry.

## Example: replace periods 1–5 with a school event

Create an event titled `Project day`, with the appropriate date and timed interval:

```text
Action: replace
Class Hour: 1-5
Room: Assembly hall
Teacher: Project team
Icon: mdi:calendar-star
```

The renderer removes the original displayed periods and inserts the event title
for each covered period. The existing templates show replacements as school
events, distinct from ordinary additional lessons, and can wrap long titles.
They contain an installation-specific period-to-time table for replacement
rows. Adapt that table to the actual school timetable before reusing them;
it is separate from the integration's API-provided class-hour grid.

## Refresh and troubleshooting

1. Use `calendar.get_events` on the separate calendar to check that the timed
   event, title and full description are returned for the intended date.
2. Check the matching helper sensor's `events` attribute. A calendar entity's
   state alone only describes its current/next event, not the complete agenda.
3. Check that the card's `external_sensor` points to the helper for the same
   day/week range. Helper and integration entity IDs depend on the installation.
4. Use `Action: hide`/`replace` and a valid `Class Hour`; avoid leading spaces
   before description keys and avoid conflicting rules for the same period.
5. Trigger the configured bridge refresh button or wait for its next update.
   `schulmanager_online.refresh` refreshes the school's API data; it does not
   directly call the separate calendar bridge, although changed timetable
   sensors may trigger that bridge.

The described helpers assume timed entries on a single school day. All-day
and multi-day expansion are not part of this documented contract. Keep source
calendar times, the HA time zone and the dashboard's school-hour table aligned.

All examples here are synthetic; no private dashboard YAML or student data is
included in the repository.

[Back to README](../README.md)
