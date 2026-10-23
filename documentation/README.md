# Documentation index

## Maintained user guides — release 1.3.0

| Guide | Contents |
| --- | --- |
| [Repository README](../README.md) | Installation, feature map, current options, calendars, services and examples |
| [Dashboard extensions](Dashboard_Extensions.md) | Additional lessons, manual period hiding/replacement, calendar descriptions, helpers and day/week plans |
| [Sensor reference](Sensors_Documentation.md) | Sensor inventory, lesson types, original values, occupied periods and freshness |
| [Homework and grade events](Integration_Events.md) | Event payloads, refresh behavior and notification automations |
| [Bundled timetable card](Custom_Card_Documentation.md) | Implemented views, legacy entity discovery and limits; distinct from the extended dashboard |
| [Calendar 1.2.2 verification](Calendar_Fix_2026-10-22.md) | Missing-subject/unnumbered-lesson fixes, tests, backup, deployment and live acceptance |
| [Changelog](../CHANGELOG.md) | Release history |

The current user guides distinguish the integration from separately configured
HA templates and dashboard extensions. The dashboard's installation-specific
YAML and private calendar/sensor data are not part of the release package.

## Architecture, API and historical references

These documents preserve earlier research and implementation notes. Older
entity IDs, screenshots, configuration options or example payloads may describe
a previous version. Use the maintained guides above for current user-facing
behavior.

| Topic | Documents |
| --- | --- |
| Setup and automation history | [Configuration](Configuration_Guide.md), [Automations](Automation_Examples.md), [Troubleshooting](Troubleshooting_Guide.md) |
| Schedule and periods | [Schedule API](Schedules_API_Documentation.md), [Free periods](free-hours-implementation.md), [Schedule troubleshooting](Schedule_API_Troubleshooting.md) |
| Homework, exams, letters | [Homework API](Homework_API_Documentation.md), [Exams API](Exams_API_Documentation.md), [Letters API](Letters_API_Documentation.md) |
| Authentication and API | [Authentication](Authentication_Guide.md), [API analysis](API_Analysis.md), [Implementation](API_Implementation.md), [Token scoping](API_Token_Scope_Review.md) |
| Schools | [Multi-school guide](Multi_School_Complete_Guide.md), [Automatic setup](Automatic_Multi_School_Implementation.md), [Institution API](Institution_API_Documentation.md), [Institution display](Institution_Info_Implementation.md), [Debug script](Multi_School_Debug_Script_Guide.md) |
| Development | [Development setup](Development_Setup.md), [Architecture](Integration_Architecture.md), [Docker](Docker_Guide.md), [Debug information](Debug_Information_Collection.md), [Sensor refactoring](Sensor_Refactoring_2025.md) |

[Releases](https://github.com/tkarle/schulmanager-online-hass/releases) ·
[Issues](https://github.com/tkarle/schulmanager-online-hass/issues)

Last checked: 22 October 2026.
