"""Utility functions for handling free hours in Schulmanager Online."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

_LOGGER = logging.getLogger(__name__)


def is_free_hour(lesson: Dict[str, Any]) -> bool:
    """Check if a lesson is a free hour."""
    return (
        lesson.get("type") == "freeHour" or 
        lesson.get("is_free_hour", False)
    )


def filter_actual_lessons(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out free hours from a list of lessons, returning only actual lessons."""
    return [lesson for lesson in lessons if not is_free_hour(lesson)]


def get_occupied_periods_for_date(
    lessons: List[Dict[str, Any]], 
    date_str: str
) -> Set[int]:
    """Get set of occupied period numbers for a specific date."""
    occupied = set()
    for lesson in lessons:
        if lesson.get("date") == date_str:
            class_hour_num = lesson.get("class_hour_number")
            if class_hour_num is not None:
                try:
                    occupied.add(int(class_hour_num))
                except (ValueError, TypeError):
                    continue
    return occupied


def create_free_hour_lesson(
    date_str: str, 
    period_num: int, 
    start_time: str, 
    end_time: str
) -> Dict[str, Any]:
    """Create a standardized free hour lesson object."""
    return {
        "id": f"free_{date_str}_{period_num}",
        "date": date_str,
        "class_hour_number": period_num,
        "start_time": start_time,
        "end_time": end_time,
        "subject": "",
        "subject_name": "",
        "subject_abbreviation": "",
        "room": "",
        "teacher": "",
        "teacher_abbreviation": "",
        "teacher_firstname": "",
        "teacher_lastname": "",
        "teachers": [],
        "type": "freeHour",
        "is_substitution": False,
        "comment": "",
        "is_cancelled": False,
        "is_free_hour": True,
    }


def get_available_periods_from_class_hours(
    class_hours: List[Dict[str, Any]]
) -> tuple[Set[int], Dict[int, tuple[str, str]]]:
    """
    Extract available periods and their times from class hours data.
    
    Returns:
        tuple: (available_periods_set, period_times_dict)
    """
    available_periods = set()
    period_times = {}  # period_number -> (start_time, end_time)
    
    for class_hour in class_hours:
        try:
            period_num = int(class_hour.get("number", 0))
            if 1 <= period_num <= 12:  # Reasonable period range
                available_periods.add(period_num)
                period_times[period_num] = (
                    class_hour.get("from", "08:00:00"),
                    class_hour.get("until", "08:45:00")
                )
        except (ValueError, TypeError):
            continue
    
    return available_periods, period_times


def add_free_hours_to_schedule(
    processed_lessons: List[Dict[str, Any]],
    class_hours: List[Dict[str, Any]],
    start_date: datetime.date,
    end_date: datetime.date
) -> List[Dict[str, Any]]:
    """
    Add free hours to a processed schedule.
    
    Args:
        processed_lessons: List of already processed lessons
        class_hours: List of class hour definitions from API
        start_date: Start date for the range
        end_date: End date for the range
        
    Returns:
        List of lessons including free hours
    """
    # Get available periods from class hours
    available_periods, period_times = get_available_periods_from_class_hours(class_hours)
    
    if not available_periods:
        _LOGGER.debug("No class hours available, returning lessons without free hours")
        return processed_lessons
    
    _LOGGER.debug(f"Available periods: {sorted(available_periods)}")
    
    # Group lessons by date
    lessons_by_date = {}
    for lesson in processed_lessons:
        lesson_date = lesson.get("date")
        if lesson_date:
            if lesson_date not in lessons_by_date:
                lessons_by_date[lesson_date] = []
            lessons_by_date[lesson_date].append(lesson)
    
    # Add free hours for each date
    all_lessons_with_free = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.isoformat()
        weekday = current_date.strftime("%A")
        
        # Skip weekends
        if weekday in ["Saturday", "Sunday"]:
            current_date += timedelta(days=1)
            continue
        
        date_lessons = lessons_by_date.get(date_str, [])
        occupied_periods = get_occupied_periods_for_date(date_lessons, date_str)
        
        # Add existing lessons
        all_lessons_with_free.extend(date_lessons)
        
        # Add free hours for unoccupied periods
        for period_num in available_periods:
            if period_num not in occupied_periods:
                start_time, end_time = period_times.get(period_num, ("08:00:00", "08:45:00"))
                free_hour = create_free_hour_lesson(date_str, period_num, start_time, end_time)
                all_lessons_with_free.append(free_hour)
        
        current_date += timedelta(days=1)
    
    # Sort all lessons (including free hours) by date and time
    all_lessons_with_free.sort(key=lambda x: (
        x.get("date", ""), 
        int(x.get("class_hour_number", 0))
    ))
    
    _LOGGER.debug(f"Total lessons with free hours: {len(all_lessons_with_free)}")
    
    return all_lessons_with_free


def count_lessons_by_type(lessons: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count lessons by type (actual vs free hours)."""
    actual_count = 0
    free_count = 0
    
    for lesson in lessons:
        if is_free_hour(lesson):
            free_count += 1
        else:
            actual_count += 1
    
    return {
        "total": len(lessons),
        "actual": actual_count,
        "free": free_count
    }


def get_subjects_from_lessons(lessons: List[Dict[str, Any]], exclude_free: bool = True) -> Set[str]:
    """Extract unique subjects from lessons."""
    subjects = set()
    
    for lesson in lessons:
        if exclude_free and is_free_hour(lesson):
            continue
            
        # Try different subject field names
        subject = (
            lesson.get("subject_abbreviation") or 
            lesson.get("subject") or 
            lesson.get("subject_name")
        )
        if subject:
            subjects.add(subject)
    
    return subjects


def get_teachers_from_lessons(lessons: List[Dict[str, Any]], exclude_free: bool = True) -> Set[str]:
    """Extract unique teachers from lessons."""
    teachers = set()
    
    for lesson in lessons:
        if exclude_free and is_free_hour(lesson):
            continue
            
        # Handle teachers list
        lesson_teachers = lesson.get("teachers", [])
        if lesson_teachers and isinstance(lesson_teachers, list):
            for teacher in lesson_teachers:
                if isinstance(teacher, dict):
                    teacher_name = teacher.get("abbreviation", teacher.get("name", ""))
                    if teacher_name:
                        teachers.add(teacher_name)
        
        # Fallback to single teacher fields
        teacher = lesson.get("teacher_abbreviation") or lesson.get("teacher")
        if teacher:
            teachers.add(teacher)
    
    return teachers


def format_lesson_summary(lessons: List[Dict[str, Any]], include_free_hours: bool = False) -> str:
    """Format a summary string for lessons."""
    if not lessons:
        return "No lessons"
    
    counts = count_lessons_by_type(lessons)
    subjects = get_subjects_from_lessons(lessons, exclude_free=True)
    
    if include_free_hours and counts["free"] > 0:
        return f"{counts['actual']} lessons, {counts['free']} free hours, {len(subjects)} subjects"
    else:
        return f"{counts['actual']} lessons, {len(subjects)} subjects"


def parse_time_to_minutes(time_str: str) -> int:
    """Convert time string (HH:MM) to minutes since midnight."""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except Exception:
        return 8 * 60  # Default to 8:00 AM


def format_minutes_to_time(minutes: int, include_seconds: bool = False) -> str:
    """Convert minutes since midnight to time string (HH:MM or HH:MM:SS)."""
    hours = minutes // 60
    mins = minutes % 60
    if include_seconds:
        return f"{hours:02d}:{mins:02d}:00"
    else:
        return f"{hours:02d}:{mins:02d}"
