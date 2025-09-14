"""Schedule sensor methods for Schulmanager Online."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

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


def get_current_lesson_state(student_data: Dict[str, Any]) -> Optional[str]:
    """Get the state for current lesson sensor."""
    current_lesson = student_data.get("current_lesson")
    if not current_lesson:
        return "No current lesson"
    
    subject = current_lesson.get("subject_abbreviation", current_lesson.get("subject", ""))
    room = current_lesson.get("room", "")
    
    if room:
        return f"{subject} in {room}"
    return subject or "Current lesson"


def get_current_lesson_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for current lesson sensor."""
    current_lesson = student_data.get("current_lesson")
    if not current_lesson:
        return {"status": "no_lesson"}

    attributes = {"status": "in_lesson"}
    
    # Basic lesson info
    if current_lesson.get("subject"):
        attributes[ATTR_SUBJECT] = current_lesson["subject"]
    if current_lesson.get("room"):
        attributes[ATTR_ROOM] = current_lesson["room"]
    if current_lesson.get("start_time"):
        attributes[ATTR_START_TIME] = current_lesson["start_time"]
    if current_lesson.get("end_time"):
        attributes[ATTR_END_TIME] = current_lesson["end_time"]
    if current_lesson.get("type"):
        attributes[ATTR_LESSON_TYPE] = current_lesson["type"]
    if current_lesson.get("is_substitution"):
        attributes[ATTR_IS_SUBSTITUTION] = current_lesson["is_substitution"]
    if current_lesson.get("comment"):
        attributes[ATTR_COMMENT] = current_lesson["comment"]

    # Teacher info
    teachers = current_lesson.get("teachers", [])
    if teachers:
        teacher_names = [t.get("name", t.get("abbreviation", "")) for t in teachers]
        attributes[ATTR_TEACHER] = ", ".join(filter(None, teacher_names))

    # Original teacher for substitutions
    if current_lesson.get("original_teacher"):
        orig_teacher = current_lesson["original_teacher"]
        attributes[ATTR_ORIGINAL_TEACHER] = orig_teacher.get("name", orig_teacher.get("abbreviation", ""))

    return attributes


def get_next_lesson_state(student_data: Dict[str, Any]) -> Optional[str]:
    """Get the state for next lesson sensor."""
    next_lesson = student_data.get("next_lesson")
    if not next_lesson:
        return "No upcoming lessons"
    
    subject = next_lesson.get("subject_abbreviation", next_lesson.get("subject", ""))
    start_time = next_lesson.get("start_time", "")
    
    if start_time:
        return f"{subject} at {start_time[:5]}"
    return subject or "Next lesson"


def get_next_lesson_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next lesson sensor."""
    next_lesson = student_data.get("next_lesson")
    if not next_lesson:
        return {"status": "no_lessons"}

    attributes = {"status": "upcoming"}
    
    # Basic lesson info
    if next_lesson.get("subject"):
        attributes[ATTR_SUBJECT] = next_lesson["subject"]
    if next_lesson.get("room"):
        attributes[ATTR_ROOM] = next_lesson["room"]
    if next_lesson.get("start_time"):
        attributes[ATTR_START_TIME] = next_lesson["start_time"]
    if next_lesson.get("end_time"):
        attributes[ATTR_END_TIME] = next_lesson["end_time"]
    if next_lesson.get("type"):
        attributes[ATTR_LESSON_TYPE] = next_lesson["type"]
    if next_lesson.get("is_substitution"):
        attributes[ATTR_IS_SUBSTITUTION] = next_lesson["is_substitution"]
    if next_lesson.get("comment"):
        attributes[ATTR_COMMENT] = next_lesson["comment"]

    # Teacher info
    teachers = next_lesson.get("teachers", [])
    if teachers:
        teacher_names = [t.get("name", t.get("abbreviation", "")) for t in teachers]
        attributes[ATTR_TEACHER] = ", ".join(filter(None, teacher_names))

    # Original teacher for substitutions
    if next_lesson.get("original_teacher"):
        orig_teacher = next_lesson["original_teacher"]
        attributes[ATTR_ORIGINAL_TEACHER] = orig_teacher.get("name", orig_teacher.get("abbreviation", ""))

    return attributes


def get_today_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get count of today's lessons."""
    today_lessons = student_data.get("today_lessons", [])
    return str(len(today_lessons))


def get_today_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for today's lessons sensor."""
    today_lessons = student_data.get("today_lessons", [])
    
    attributes = {
        "lessons": [],
        "count": len(today_lessons),
    }

    for lesson in today_lessons:
        lesson_info = {
            "subject": lesson.get("subject_abbreviation", lesson.get("subject", "")),
            "time": f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}",
            "room": lesson.get("room", ""),
            "teacher": ", ".join([t.get("abbreviation", "") for t in lesson.get("teachers", [])]),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", ""),
            "comment": lesson.get("comment", ""),
        }
        attributes["lessons"].append(lesson_info)

    return attributes


def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get count of tomorrow's lessons."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    return str(len(tomorrow_lessons))


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow's lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    attributes = {
        "lessons": [],
        "count": len(tomorrow_lessons),
    }

    for lesson in tomorrow_lessons:
        lesson_info = {
            "subject": lesson.get("subject_abbreviation", lesson.get("subject", "")),
            "time": f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}",
            "room": lesson.get("room", ""),
            "teacher": ", ".join([t.get("abbreviation", "") for t in lesson.get("teachers", [])]),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", ""),
            "comment": lesson.get("comment", ""),
        }
        attributes["lessons"].append(lesson_info)

    return attributes


def get_today_changes_count(student_data: Dict[str, Any]) -> str:
    """Get count of today's changes."""
    today_changes = student_data.get("today_changes", [])
    count = len(today_changes)
    return str(count)


def get_today_changes_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for today's changes sensor."""
    today_changes = student_data.get("today_changes", [])
    
    attributes = {
        "changes": [],
        "count": len(today_changes),
    }

    for change in today_changes:
        change_info = {
            "subject": change.get("subject_abbreviation", change.get("subject", "")),
            "time": f"{change.get('start_time', '')}-{change.get('end_time', '')}",
            "room": change.get("room", ""),
            "type": change.get("type", ""),
            "is_substitution": change.get("is_substitution", False),
            "comment": change.get("comment", ""),
        }
        
        # Teacher info
        teachers = change.get("teachers", [])
        if teachers:
            change_info["teacher"] = ", ".join([t.get("abbreviation", "") for t in teachers])
        
        # Original teacher for substitutions
        if change.get("original_teacher"):
            orig_teacher = change["original_teacher"]
            change_info["original_teacher"] = orig_teacher.get("abbreviation", "")
        
        attributes["changes"].append(change_info)

    return attributes


def get_this_week_summary(student_data: Dict[str, Any]) -> str:
    """Get this week summary state."""
    this_week = student_data.get("this_week", [])
    if not this_week:
        return "No lessons this week"
    
    total_lessons = len(this_week)
    subjects = set()
    
    for lesson in this_week:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_this_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for this week sensor."""
    this_week = student_data.get("this_week", [])
    
    # Count lessons by day
    lessons_by_day = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information (like next_school_day sensor)
    detailed_lessons = []
    
    for lesson in this_week:
        date = lesson.get("date", "")
        if date:
            lessons_by_day[date] = lessons_by_day.get(date, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": date,
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(this_week),
        "lessons_by_day": lessons_by_day,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_week_summary(student_data: Dict[str, Any]) -> str:
    """Get next week summary state."""
    next_week = student_data.get("next_week", [])
    if not next_week:
        return "No lessons next week"
    
    total_lessons = len(next_week)
    subjects = set()
    
    for lesson in next_week:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next week sensor."""
    next_week = student_data.get("next_week", [])
    
    # Count lessons by day
    lessons_by_day = {}
    subjects = set()
    teachers = set()
    
    # Detailed lesson information (like next_school_day sensor)
    detailed_lessons = []
    
    for lesson in next_week:
        date = lesson.get("date", "")
        if date:
            lessons_by_day[date] = lessons_by_day.get(date, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": date,
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_week),
        "lessons_by_day": lessons_by_day,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
    }


def get_changes_detected_state(student_data: Dict[str, Any]) -> str:
    """Get changes detected state."""
    changes_data = student_data.get("changes_detected", {})
    
    if not changes_data.get("has_changes", False):
        return "No changes"
    
    change_count = changes_data.get("change_count", 0)
    if change_count == 1:
        return "1 change detected"
    return f"{change_count} changes detected"


def get_changes_detected_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for changes detected sensor."""
    changes_data = student_data.get("changes_detected", {})
    
    attributes = {
        "has_changes": changes_data.get("has_changes", False),
        "change_count": changes_data.get("change_count", 0),
        "changes": [],
    }

    for change in changes_data.get("changes", []):
        change_info = {
            "type": change.get("type", ""),
            "date": change.get("date", ""),
            "class_hour": change.get("class_hour", ""),
            "description": change.get("description", ""),
        }
        
        # Add field-level changes for modifications
        if change.get("type") == "modified" and "field_changes" in change:
            change_info["field_changes"] = change["field_changes"]
        
        # Add lesson details
        if change.get("current"):
            current = change["current"]
            change_info["current"] = {
                "subject": current.get("subject", ""),
                "room": current.get("room", ""),
                "teacher": ", ".join([t.get("abbreviation", "") for t in current.get("teachers", [])]),
                "time": f"{current.get('start_time', '')}-{current.get('end_time', '')}",
            }
        
        if change.get("previous"):
            previous = change["previous"]
            change_info["previous"] = {
                "subject": previous.get("subject", ""),
                "room": previous.get("room", ""),
                "teacher": ", ".join([t.get("abbreviation", "") for t in previous.get("teachers", [])]),
                "time": f"{previous.get('start_time', '')}-{previous.get('end_time', '')}",
            }
        
        attributes["changes"].append(change_info)

    return attributes

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }



def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }

def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_tomorrow_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get tomorrow lessons count state."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    if not tomorrow_lessons:
        return "No lessons tomorrow"
    
    total_lessons = len(tomorrow_lessons)
    subjects = set()
    
    for lesson in tomorrow_lessons:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_tomorrow_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for tomorrow lessons sensor."""
    tomorrow_lessons = student_data.get("tomorrow_lessons", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in tomorrow_lessons:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(tomorrow_lessons),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }


def get_next_school_day_lessons_count(student_data: Dict[str, Any]) -> str:
    """Get next school day lessons count state."""
    next_school_day = student_data.get("next_school_day", [])
    if not next_school_day:
        return "No upcoming school day"
    
    total_lessons = len(next_school_day)
    subjects = set()
    
    for lesson in next_school_day:
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
    
    return f"{total_lessons} lessons, {len(subjects)} subjects"


def get_next_school_day_lessons_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for next school day lessons sensor."""
    next_school_day = student_data.get("next_school_day", [])
    
    # Count lessons by hour
    lessons_by_hour = {}
    subjects = set()
    teachers = set()
    changes_count = 0
    
    # Detailed lesson information
    detailed_lessons = []
    
    for lesson in next_school_day:
        hour = lesson.get("class_hour_number", "")
        if hour:
            lessons_by_hour[hour] = lessons_by_hour.get(hour, 0) + 1
        
        subject = lesson.get("subject_abbreviation", lesson.get("subject", ""))
        if subject:
            subjects.add(subject)
        
        for teacher in lesson.get("teachers", []):
            teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
            if teacher_name:
                teachers.add(teacher_name)
        
        if lesson.get("is_substitution") or lesson.get("type") in ["changedLesson", "cancelledLesson"]:
            changes_count += 1
        
        # Add detailed lesson info
        lesson_detail = {
            "subject": lesson.get("subject_name", lesson.get("subject", "")),
            "subject_abbreviation": lesson.get("subject_abbreviation", ""),
            "time": f"{lesson.get('start_time', 'None')}-{lesson.get('end_time', 'None')}",
            "room": lesson.get("room", ""),
            "teacher": lesson.get("teacher_abbreviation", ""),
            "teacher_lastname": lesson.get("teacher_lastname", ""),
            "teacher_firstname": lesson.get("teacher_firstname", ""),
            "is_substitution": lesson.get("is_substitution", False),
            "type": lesson.get("type", "regularLesson"),
            "comment": lesson.get("comment", ""),
            "date": lesson.get("date", ""),
            "class_hour": lesson.get("class_hour_number", "")
        }
        detailed_lessons.append(lesson_detail)

    return {
        "total_lessons": len(next_school_day),
        "lessons_by_hour": lessons_by_hour,
        "lessons": detailed_lessons,  # Add detailed lesson data
        "subjects": sorted(list(subjects)),
        "teachers": sorted(list(teachers)),
        "subject_count": len(subjects),
        "teacher_count": len(teachers),
        "changes_count": changes_count,
    }
