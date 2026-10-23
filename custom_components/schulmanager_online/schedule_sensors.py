"""Schedule sensor methods for Schulmanager Online."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .free_hours_utils import (
    is_free_hour,
    filter_actual_lessons,
    count_lessons_by_type,
    get_subjects_from_lessons,
    get_teachers_from_lessons,
    format_lesson_summary,
)
from .const import (
    ATTR_CLASS_NAME,
    ATTR_COMMENT,
    ATTR_END_TIME,
    ATTR_IS_SUBSTITUTION,
    ATTR_LESSON_TYPE,
    ATTR_ORIGINAL_TEACHER,
    ATTR_ROOM,
    ATTR_START_TIME,
    ATTR_SUBJECT,
    ATTR_TEACHER,
)

def _as_list(value: Any) -> List[Any]:
    """Return value as a list, treating unavailable HA states as empty."""
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> Dict[str, Any]:
    """Return value as a dict, treating unavailable HA states as empty."""
    if isinstance(value, dict):
        return value
    return {}


def _as_lesson_list(value: Any) -> List[Dict[str, Any]]:
    """Return only dict lessons from a value that should be a list."""
    return [item for item in _as_list(value) if isinstance(item, dict)]


def _as_lesson(value: Any) -> Dict[str, Any]:
    """Return value as a lesson dict."""
    return value if isinstance(value, dict) else {}


def _format_lesson_for_attributes(lesson: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a lesson for consistent attribute structure across all sensors.
    
    This ensures all sensors use the same data format:
    - subject: Full subject name (e.g., "Evangelische Religionslehre (konfessionell kooperativ)")
    - subject_abbreviation: Short form (e.g., "EN")  
    - subject_sanitized: Clean subject name without parentheses and commas (e.g., "Evangelische Religionslehre")
    - For free hours: subject fields are empty, type is "freeHour"
    """
    lesson = _as_lesson(lesson)
    lesson_type = lesson.get("type", "regularLesson")
    
    # Handle free hours
    if is_free_hour(lesson):
        return {
            "subject": "",
            "subject_abbreviation": "",
            "subject_sanitized": "",
            "time": f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}",
            "room": "",
            "teacher": "",
            "teacher_lastname": "",
            "teacher_firstname": "",
            "is_substitution": False,
            "type": "freeHour",
            "comment": "",
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
    
    # Handle regular lessons
    full_subject = lesson.get("subject_name", lesson.get("subject", ""))
    
    formatted = {
        "subject": full_subject,
        "subject_abbreviation": lesson.get("subject_abbreviation", ""),
        "subject_sanitized": _sanitize_subject_name(full_subject),
        "time": f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}",
        "room": lesson.get("room", ""),
        "teacher": lesson.get("teacher_abbreviation", ""),
        "teacher_lastname": lesson.get("teacher_lastname", ""),
        "teacher_firstname": lesson.get("teacher_firstname", ""),
        "is_substitution": lesson.get("is_substitution", False),
        "type": lesson_type,
        "comment": lesson.get("comment", ""),
        "date": lesson.get("date", ""),
        "class_hour": lesson.get("class_hour_number", "")
    }

    if lesson_type == "event":
        formatted["event_title"] = full_subject

    if lesson.get("original_subject"):
        formatted["original_subject"] = lesson["original_subject"]
    if lesson.get("original_room"):
        formatted["original_room"] = lesson["original_room"]
    if lesson.get("original_teachers"):
        formatted["original_teacher"] = _format_teachers_for_display(lesson["original_teachers"])
    if lesson.get("original_comment"):
        formatted["original_comment"] = lesson["original_comment"]

    return formatted


def _format_teachers_for_display(teachers: Any) -> str:
    """Format teacher lists as a comma-separated abbreviation string."""
    if not isinstance(teachers, list):
        return ""

    return ", ".join(
        filter(None, [teacher.get("abbreviation", "") for teacher in teachers if isinstance(teacher, dict)])
    )


def _get_subject_for_display(lesson: Dict[str, Any]) -> str:
    """
    Get subject for display purposes (state values, summaries).
    Uses abbreviation for brevity in state display.
    """
    return lesson.get("subject_abbreviation", lesson.get("subject", ""))


def _sanitize_subject_name(subject: str) -> str:
    """
    Sanitize subject name by removing content in parentheses and everything after the first comma.
    
    Examples:
    - "Evangelische Religionslehre (konfessionell kooperativ)" → "Evangelische Religionslehre"
    - "Mathematik, Grundkurs" → "Mathematik"
    - "Deutsch (LK), Leistungskurs" → "Deutsch"
    - "Sport" → "Sport"
    """
    if not subject:
        return ""
    
    # Remove everything in parentheses (including the parentheses)
    subject = re.sub(r'\s*\([^)]*\)', '', subject)
    
    # Remove everything after the first comma
    subject = subject.split(',')[0]
    
    # Clean up any extra whitespace
    return subject.strip()


def _format_lessons_list_attributes(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format a list of lessons with consistent attribute structure."""
    return [_format_lesson_for_attributes(lesson) for lesson in _as_lesson_list(lessons)]


def _get_period_key(lesson: Dict[str, Any], index: int) -> tuple:
    """Build a stable key for one schedule period, even when its hour is absent."""
    date = lesson.get("date", "")
    hour = lesson.get("class_hour_number")
    if hour not in (None, ""):
        return date, str(hour)

    start = lesson.get("start_time", "")
    end = lesson.get("end_time", "")
    if start or end:
        return date, start, end

    return date, lesson.get("id") or f"row-{index}"


def _get_effective_periods(lessons: List[Dict[str, Any]]) -> Dict[tuple, Dict[str, Any]]:
    """Return one active lesson or event per period, preferring replacement events."""
    grouped: Dict[tuple, List[Dict[str, Any]]] = {}
    for index, lesson in enumerate(lessons):
        grouped.setdefault(_get_period_key(lesson, index), []).append(lesson)

    effective = {}
    for key, period_lessons in grouped.items():
        active = [
            lesson for lesson in period_lessons
            if lesson.get("type") not in ("cancelledLesson", "freeHour")
            and not is_free_hour(lesson)
        ]
        if active:
            effective[key] = next(
                (lesson for lesson in active if lesson.get("type") == "event"),
                active[0],
            )
    return effective


def _get_next_week_events(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize event titles and the periods each event occupies."""
    events: Dict[tuple, Dict[str, Any]] = {}
    for period_key, lesson in _get_effective_periods(lessons).items():
        if lesson.get("type") != "event":
            continue
        title = lesson.get("subject_name") or lesson.get("subject") or "Event"
        event_key = (lesson.get("date", ""), title)
        event = events.setdefault(event_key, {
            "title": title,
            "date": lesson.get("date", ""),
            "periods": [],
            "_period_keys": set(),
        })
        event["_period_keys"].add(period_key)
        hour = lesson.get("class_hour_number")
        if hour not in (None, ""):
            event["periods"].append(hour)

    result = list(events.values())
    for event in result:
        event["periods"] = sorted(
            set(event["periods"]),
            key=lambda value: (0, int(value)) if str(value).isdigit() else (1, str(value)),
        )
        event["period_count"] = len(event.pop("_period_keys"))
    return result


def get_current_lesson_state(student_data: Dict[str, Any]) -> Optional[str]:
    """Get the state for current lesson sensor."""
    current_lesson = _as_dict(student_data).get("current_lesson")
    if not current_lesson:
        return "No current lesson"
    current_lesson = _as_lesson(current_lesson)
    
    subject = _get_subject_for_display(current_lesson)
    room = current_lesson.get("room", "")
    
    if room:
        return f"{subject} in {room}"
    return subject or "Current lesson"


def get_current_lesson_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for current lesson sensor."""
    current_lesson = _as_dict(student_data).get("current_lesson")
    if not current_lesson:
        return {"status": "no_lesson"}
    current_lesson = _as_lesson(current_lesson)

    attributes = {"status": "in_lesson"}
    
    # Basic lesson info using unified formatting
    formatted_lesson = _format_lesson_for_attributes(current_lesson)
    attributes.update({
        ATTR_SUBJECT: formatted_lesson["subject"],
        ATTR_ROOM: formatted_lesson["room"],
        ATTR_START_TIME: current_lesson.get("start_time", ""),
        ATTR_END_TIME: current_lesson.get("end_time", ""),
        ATTR_LESSON_TYPE: formatted_lesson["type"],
        ATTR_IS_SUBSTITUTION: formatted_lesson["is_substitution"],
        ATTR_COMMENT: formatted_lesson["comment"],
    })

    # Teacher info
    teachers = _as_list(current_lesson.get("teachers", []))
    if teachers:
        teacher_names = [
            t.get("name", t.get("abbreviation", ""))
            for t in teachers
            if isinstance(t, dict)
        ]
        attributes[ATTR_TEACHER] = ", ".join(filter(None, teacher_names))

    # Original teacher for substitutions
    if current_lesson.get("original_teacher"):
        orig_teacher = current_lesson["original_teacher"]
        attributes[ATTR_ORIGINAL_TEACHER] = orig_teacher.get("name", orig_teacher.get("abbreviation", ""))

    return attributes


def get_next_lesson_state(student_data: Dict[str, Any]) -> Optional[str]:
    """Get the state for next lesson sensor."""
    next_lesson = _as_dict(student_data).get("next_lesson")
    if not next_lesson:
        return "No upcoming lessons"
    next_lesson = _as_lesson(next_lesson)
    
    subject = _get_subject_for_display(next_lesson)
    start_time = next_lesson.get("start_time", "")
    
    if start_time:
        return f"{subject} at {start_time[:5]}"
    return subject or "Next lesson"


def get_next_lesson_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next lesson sensor."""
    next_lesson = _as_dict(student_data).get("next_lesson")
    if not next_lesson:
        return {"status": "no_lessons"}
    next_lesson = _as_lesson(next_lesson)

    attributes = {"status": "upcoming"}
    
    # Basic lesson info using unified formatting
    formatted_lesson = _format_lesson_for_attributes(next_lesson)
    attributes.update({
        ATTR_SUBJECT: formatted_lesson["subject"],
        ATTR_ROOM: formatted_lesson["room"],
        ATTR_START_TIME: next_lesson.get("start_time", ""),
        ATTR_END_TIME: next_lesson.get("end_time", ""),
        ATTR_LESSON_TYPE: formatted_lesson["type"],
        ATTR_IS_SUBSTITUTION: formatted_lesson["is_substitution"],
        ATTR_COMMENT: formatted_lesson["comment"],
    })

    # Teacher info
    teachers = _as_list(next_lesson.get("teachers", []))
    if teachers:
        teacher_names = [
            t.get("name", t.get("abbreviation", ""))
            for t in teachers
            if isinstance(t, dict)
        ]
        attributes[ATTR_TEACHER] = ", ".join(filter(None, teacher_names))

    # Original teacher for substitutions
    if next_lesson.get("original_teacher"):
        orig_teacher = next_lesson["original_teacher"]
        attributes[ATTR_ORIGINAL_TEACHER] = orig_teacher.get("name", orig_teacher.get("abbreviation", ""))

    return attributes


def get_today_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get count of today's lessons."""
    today_lessons = _as_lesson_list(_as_dict(student_data).get("today_lessons", []))
    return str(len(today_lessons))


def get_today_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for today's lessons sensor."""
    today_lessons = _as_lesson_list(_as_dict(student_data).get("today_lessons", []))
    
    # Use utility functions for consistent processing (same as tomorrow sensor)
    actual_lessons = filter_actual_lessons(today_lessons)
    subjects = get_subjects_from_lessons(today_lessons, exclude_free=True)
    teachers = get_teachers_from_lessons(today_lessons, exclude_free=True)
    counts = count_lessons_by_type(today_lessons)
    
    # Count lessons by hour (excluding free hours)
    lessons_by_hour = {}
    changes_count = 0
    
    for lesson in actual_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
    
    return {
        "total_lessons": counts["actual"],
        "free_hours": counts["free"],
        "lessons_by_hour": lessons_by_hour,
        "lessons": _format_lessons_list_attributes(today_lessons),  # Include all lessons (with free hours)
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get count of tomorrow's lessons."""
    tomorrow_lessons = _as_lesson_list(_as_dict(student_data).get("tomorrow_lessons", []))
    return str(len(tomorrow_lessons))


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow's lessons sensor."""
    tomorrow_lessons = _as_lesson_list(_as_dict(student_data).get("tomorrow_lessons", []))
    
    # Use utility functions for consistent processing
    actual_lessons = filter_actual_lessons(tomorrow_lessons)
    subjects = get_subjects_from_lessons(tomorrow_lessons, exclude_free=True)
    teachers = get_teachers_from_lessons(tomorrow_lessons, exclude_free=True)
    counts = count_lessons_by_type(tomorrow_lessons)
    
    # Count lessons by hour (excluding free hours)
    lessons_by_hour = {}
    changes_count = 0
    
    for lesson in actual_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
    
    return {
        "total_lessons": counts["actual"],
        "free_hours": counts["free"],
        "lessons_by_hour": lessons_by_hour,
        "lessons": _format_lessons_list_attributes(tomorrow_lessons),  # Include all lessons (with free hours)
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_today_changes_count(student_data: Dict[str, Any]) -> str:
    """Get count of today's changes."""
    today_changes = _as_lesson_list(_as_dict(student_data).get("today_changes", []))
    count = len(today_changes)
    return str(count)


def get_today_changes_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for today's changes sensor."""
    today_changes = _as_lesson_list(_as_dict(student_data).get("today_changes", []))
    
    changes_list = []
    for change in today_changes:
        change_info = _format_lesson_for_attributes(change)
        # Add specific change fields
        change_info["type"] = change.get("type", "")
        
        # Teacher info
        teachers = change.get("teachers", [])
        if teachers:
            change_info["teacher"] = ", ".join([t.get("abbreviation", "") for t in teachers])
        
        # Original teacher for substitutions
        if change.get("original_teacher"):
            orig_teacher = change["original_teacher"]
            change_info["original_teacher"] = orig_teacher.get("abbreviation", "")
        
        changes_list.append(change_info)

    return {
        "changes": changes_list,
        "count": len(today_changes),
    }


def get_this_week_summary(student_data: Dict[str, Any]) -> str:
    """Get this week summary state."""
    this_week = _as_lesson_list(_as_dict(student_data).get("this_week", []))
    if not this_week:
        return "No lessons this week"
    
    return format_lesson_summary(this_week, include_free_hours=False)


def get_this_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for this week sensor."""
    this_week = _as_lesson_list(_as_dict(student_data).get("this_week", []))
    
    # Use utility functions for consistent processing
    actual_lessons = filter_actual_lessons(this_week)
    subjects = get_subjects_from_lessons(this_week, exclude_free=True)
    teachers = get_teachers_from_lessons(this_week, exclude_free=True)
    counts = count_lessons_by_type(this_week)
    
    # Count lessons by day (excluding free hours)
    lessons_by_day = {}
    changes_count = 0
    
    for lesson in actual_lessons:
        date = lesson.get("date", "")
        if date:
            lessons_by_day[date] = lessons_by_day.get(date, 0) + 1
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
    
    return {
        "total_lessons": counts["actual"],
        "free_hours": counts["free"],
        "lessons_by_day": lessons_by_day,
        "lessons": _format_lessons_list_attributes(this_week),  # Include all lessons (with free hours)
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_week_summary(student_data: Dict[str, Any]) -> str:
    """Get next week summary state."""
    next_week = _as_lesson_list(_as_dict(student_data).get("next_week", []))
    if not next_week:
        return "No lessons next week"

    effective = _get_effective_periods(next_week)
    lessons = [lesson for lesson in effective.values() if lesson.get("type") != "event"]
    cancelled_period_count = len({
        _get_period_key(lesson, index)
        for index, lesson in enumerate(next_week)
        if lesson.get("type") == "cancelledLesson"
    })

    summary_parts = []
    if lessons:
        subject_count = len(get_subjects_from_lessons(lessons, exclude_free=True))
        summary_parts.append(f"{len(lessons)} lessons, {subject_count} subjects")
    events = _get_next_week_events(next_week)
    if events:
        summary_parts.extend(
            f"{event['title']} ({event['period_count']} periods)" for event in events
        )
    if cancelled_period_count:
        summary_parts.append(f"{cancelled_period_count} cancelled")
    return "; ".join(summary_parts) or "No lessons next week"


def get_next_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next week sensor."""
    next_week = _as_lesson_list(_as_dict(student_data).get("next_week", []))

    effective = _get_effective_periods(next_week)
    effective_lessons = list(effective.values())
    actual_lessons = [
        lesson for lesson in effective_lessons if lesson.get("type") != "event"
    ]
    subjects = get_subjects_from_lessons(actual_lessons, exclude_free=True)
    teachers = get_teachers_from_lessons(effective_lessons, exclude_free=True)
    events = _get_next_week_events(next_week)
    cancelled_lessons = [
        lesson for lesson in next_week if lesson.get("type") == "cancelledLesson"
    ]

    # Count effective lessons by day; replacements occupy periods but are events.
    lessons_by_day = {}
    for lesson in actual_lessons:
        date = lesson.get("date", "")
        if date:
            lessons_by_day[date] = lessons_by_day.get(date, 0) + 1

    scheduled_periods_by_day = {}
    for lesson in effective_lessons:
        date = lesson.get("date", "")
        if date:
            scheduled_periods_by_day[date] = scheduled_periods_by_day.get(date, 0) + 1

    cancelled_periods = len({
        _get_period_key(lesson, index)
        for index, lesson in enumerate(next_week)
        if lesson.get("type") == "cancelledLesson"
    })
    return {
        "total_lessons": len(actual_lessons),
        "scheduled_periods": len(effective_lessons),
        "event_periods": sum(event["period_count"] for event in events),
        "cancelled_periods": cancelled_periods,
        "free_hours": sum(1 for lesson in next_week if is_free_hour(lesson)),
        "lessons_by_day": lessons_by_day,
        "scheduled_periods_by_day": scheduled_periods_by_day,
        "events": events,
        "cancelled_lessons": _format_lessons_list_attributes(cancelled_lessons),
        "lessons": _format_lessons_list_attributes(next_week),  # Include all lessons (with free hours)
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
    }


def get_changes_detected_state(student_data: Dict[str, Any]) -> str:
    """Get changes detected state."""
    changes_data = _as_dict(_as_dict(student_data).get("changes_detected", {}))
    
    if not changes_data.get("has_changes", False):
        return "No changes"
    
    change_count = changes_data.get("change_count", 0)
    if change_count == 1:
        return "1 change detected"
    return f"{change_count} changes detected"


def get_changes_detected_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for changes detected sensor."""
    changes_data = _as_dict(_as_dict(student_data).get("changes_detected", {}))
    changes = _as_list(changes_data.get("changes", []))
    
    attributes = {
        "has_changes": changes_data.get("has_changes", False),
        "change_count": changes_data.get("change_count", 0),
        "changes": [],
    }

    for change in changes:
        if not isinstance(change, dict):
            continue
        change_info = {
            "type": change.get("type", ""),
            "date": change.get("date", ""),
            "class_hour": change.get("class_hour", ""),
            "description": change.get("description", ""),
        }
        
        # Add field-level changes for modifications
        field_changes = _as_list(change.get("field_changes", []))
        if change.get("type") == "modified" and field_changes:
            change_info["field_changes"] = field_changes
            for field_change in field_changes:
                if not isinstance(field_change, dict):
                    continue
                field = field_change.get("field", "")
                if field == "teachers":
                    field = "teacher"
                if field:
                    change_info[f"{field}_old"] = field_change.get("previous", "")
                    change_info[f"{field}_new"] = field_change.get("current", "")
        
        # Add lesson details using unified formatting
        if change.get("current"):
            current = change["current"]
            formatted_current = _format_lesson_for_attributes(current)
            change_info["current"] = {
                "subject": formatted_current["subject"],
                "room": formatted_current["room"],
                "teacher": _format_teachers_for_display(current.get("teachers", [])),
                "time": formatted_current["time"],
            }
        
        if change.get("previous"):
            previous = change["previous"]
            formatted_previous = _format_lesson_for_attributes(previous)
            change_info["previous"] = {
                "subject": formatted_previous["subject"],
                "room": formatted_previous["room"],
                "teacher": _format_teachers_for_display(previous.get("teachers", [])),
                "time": formatted_previous["time"],
            }
        
        attributes["changes"].append(change_info)

    return attributes


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = _as_lesson_list(_as_dict(student_data).get("next_school_day", []))
    if not next_school_day:
        return "No upcoming school day"
    
    return format_lesson_summary(next_school_day, include_free_hours=False)


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = _as_lesson_list(_as_dict(student_data).get("next_school_day", []))
    
    # Use utility functions for consistent processing
    actual_lessons = filter_actual_lessons(next_school_day)
    subjects = get_subjects_from_lessons(next_school_day, exclude_free=True)
    teachers = get_teachers_from_lessons(next_school_day, exclude_free=True)
    counts = count_lessons_by_type(next_school_day)
    
    # Count lessons by hour (excluding free hours)
    lessons_by_hour = {}
    changes_count = 0
    
    for lesson in actual_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
    
    return {
        "total_lessons": counts["actual"],
        "free_hours": counts["free"],
        "lessons_by_hour": lessons_by_hour,
        "lessons": _format_lessons_list_attributes(next_school_day),  # Include all lessons (with free hours)
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }
