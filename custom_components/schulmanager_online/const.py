"""Constants for the Schulmanager Online integration."""
from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "schulmanager_online"

# Configuration keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_STUDENT_ID: Final = "student_id"
CONF_LOOKAHEAD_WEEKS: Final = "lookahead_weeks"

# Schedule timing configuration keys
CONF_LESSON_DURATION: Final = "lesson_duration_minutes"
CONF_SHORT_BREAK: Final = "short_break_minutes"
CONF_LONG_BREAK_1: Final = "long_break_1_minutes"
CONF_LONG_BREAK_2: Final = "long_break_2_minutes"
CONF_LUNCH_BREAK: Final = "lunch_break_minutes"
CONF_SCHOOL_START_TIME: Final = "school_start_time"

# Default values
DEFAULT_LOOKAHEAD_WEEKS: Final = 2
DEFAULT_SCAN_INTERVAL: Final = 900  # 15 minutes
DEFAULT_TIMEOUT: Final = 30
DEFAULT_ATTEMPTS: Final = 3
DEFAULT_BACKOFF_FACTOR: Final = 2

# Default schedule timing values (German school standard)
DEFAULT_LESSON_DURATION: Final = 45  # minutes
DEFAULT_SHORT_BREAK: Final = 5       # minutes
DEFAULT_LONG_BREAK_1: Final = 20     # minutes (after 2nd hour)
DEFAULT_LONG_BREAK_2: Final = 10     # minutes (after 4th hour) 
DEFAULT_LUNCH_BREAK: Final = 45      # minutes (after 6th hour)
DEFAULT_SCHOOL_START_TIME: Final = "08:00"

# Platforms
PLATFORMS: Final = [Platform.SENSOR, Platform.CALENDAR]

# API Configuration
API_BASE_URL: Final = "https://login.schulmanager-online.de"
LOGIN_URL: Final = f"{API_BASE_URL}/api/login"
SALT_URL: Final = f"{API_BASE_URL}/api/get-salt"
CALLS_URL: Final = f"{API_BASE_URL}/api/calls"

# Token and session management
TOKEN_REFRESH_INTERVAL: Final = 3600  # 1 hour
UPDATE_INTERVAL: Final = 900  # 15 minutes

# Entity types
ENTITY_TYPE_SENSOR: Final = "sensor"
ENTITY_TYPE_CALENDAR: Final = "calendar"

# Sensor types (with schulmanager prefix for clarity)
SENSOR_CURRENT_LESSON: Final = "lesson_current"
SENSOR_NEXT_LESSON: Final = "lesson_next"
SENSOR_TODAY_LESSONS: Final = "lessons_today"
SENSOR_TODAY_CHANGES: Final = "lessons_changes_today"
SENSOR_TOMORROW_LESSONS: Final = "lessons_tomorrow"
SENSOR_THIS_WEEK: Final = "lessons_this_week"
SENSOR_NEXT_WEEK: Final = "lessons_next_week"
SENSOR_NEXT_SCHOOL_DAY: Final = "lessons_next_school_day"
SENSOR_CHANGES_DETECTED: Final = "changes_detected"
SENSOR_HOMEWORK_DUE_TODAY: Final = "homework_due_today"
SENSOR_HOMEWORK_DUE_TOMORROW: Final = "homework_due_tomorrow"
SENSOR_HOMEWORK_OVERDUE: Final = "homework_overdue"
SENSOR_HOMEWORK_UPCOMING: Final = "homework_upcoming"
SENSOR_HOMEWORK_RECENT: Final = "homework_recent"
SENSOR_EXAMS_TODAY: Final = "exams_today"
SENSOR_EXAMS_THIS_WEEK: Final = "exams_this_week"
SENSOR_EXAMS_NEXT_WEEK: Final = "exams_next_week"
SENSOR_EXAMS_UPCOMING: Final = "exams_upcoming"

# Calendar types
CALENDAR_SCHEDULE: Final = "schedule"
CALENDAR_HOMEWORK: Final = "homework"
CALENDAR_EXAMS: Final = "exams"

# Attributes
ATTR_STUDENT_ID: Final = "student_id"
ATTR_STUDENT_NAME: Final = "student_name"
ATTR_CLASS_NAME: Final = "class_name"
ATTR_SUBJECT: Final = "subject"
ATTR_TEACHER: Final = "teacher"
ATTR_ROOM: Final = "room"
ATTR_START_TIME: Final = "start_time"
ATTR_END_TIME: Final = "end_time"
ATTR_LESSON_TYPE: Final = "lesson_type"
ATTR_IS_SUBSTITUTION: Final = "is_substitution"
ATTR_ORIGINAL_TEACHER: Final = "original_teacher"
ATTR_COMMENT: Final = "comment"

# Icons
ICON_SCHOOL: Final = "mdi:school"
ICON_BOOK: Final = "mdi:book-open-page-variant"
ICON_CALENDAR: Final = "mdi:calendar-clock"
ICON_ACCOUNT_GROUP: Final = "mdi:account-group"
ICON_CLOCK: Final = "mdi:clock-outline"
ICON_CLOCK_ALERT: Final = "mdi:clock-alert-outline"
ICON_CALENDAR_TODAY: Final = "mdi:calendar-today"
ICON_CALENDAR_WEEK: Final = "mdi:calendar-week"
ICON_ALERT_CIRCLE: Final = "mdi:alert-circle-outline"
ICON_SWAP_HORIZONTAL: Final = "mdi:swap-horizontal"
ICON_PLAY_CIRCLE: Final = "mdi:play-circle-outline"
ICON_HOMEWORK: Final = "mdi:notebook-edit-outline"
ICON_HOMEWORK_DUE: Final = "mdi:alarm-check"
ICON_HOMEWORK_OVERDUE: Final = "mdi:alarm-snooze"
ICON_HOMEWORK_UPCOMING: Final = "mdi:calendar-arrow-right"
ICON_HOMEWORK_RECENT: Final = "mdi:history"
ICON_EXAM: Final = "mdi:clipboard-text"
ICON_EXAM_TODAY: Final = "mdi:clipboard-alert"
ICON_EXAM_UPCOMING: Final = "mdi:clipboard-clock"
ICON_EXAM_WEEK: Final = "mdi:calendar-week-begin"
