"""Exam sensor methods for Schulmanager Online - Updated for real API structure."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List


def _extract_exams(exams_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract exams list from API response."""
    # Handle different data structures
    data = exams_data.get("data", [])
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("exams", [])
    else:
        return exams_data.get("exams", [])


def _format_exam_info(exam: Dict[str, Any]) -> Dict[str, Any]:
    """Format exam data for consistent output."""
    # Extract subject name
    subject = exam.get("subject", {})
    subject_name = subject.get("name", "Unknown") if isinstance(subject, dict) else str(subject)
    
    # Extract exam type
    exam_type = exam.get("type", {})
    type_name = exam_type.get("name", "Exam") if isinstance(exam_type, dict) else str(exam_type)
    
    # Extract time from startClassHour
    start_class_hour = exam.get("startClassHour", {})
    time_str = ""
    class_hour_number = ""
    
    if isinstance(start_class_hour, dict):
        time_from = start_class_hour.get("from", "")
        time_until = start_class_hour.get("until", "")
        if time_from and time_until:
            time_str = f"{time_from[:5]}-{time_until[:5]}"  # Format: HH:MM-HH:MM
        elif time_from:
            time_str = time_from[:5]
        class_hour_number = start_class_hour.get("number", "")
    
    return {
        "subject": subject_name,
        "subject_abbreviation": subject.get("abbreviation", "") if isinstance(subject, dict) else "",
        "title": exam.get("title", exam.get("name", type_name)),
        "date": exam.get("date", ""),
        "time": time_str,
        "class_hour": class_hour_number,
        "room": exam.get("room", ""),  # May be empty in current data
        "teacher": exam.get("teacher", ""),  # May be empty in current data
        "type": type_name,
        "type_color": exam_type.get("color", "") if isinstance(exam_type, dict) else "",
        "comment": exam.get("comment", ""),
        "days_until": calculate_days_until(exam.get("date", "")),
    }


def get_exams_today_count(student_data: Dict[str, Any]) -> str:
    """Get count of exams today."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date().isoformat()
    exams_today = [exam for exam in exams if exam.get("date") == today]
    return str(len(exams_today))


def get_exams_today_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for exams today sensor."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date().isoformat()
    exams_today = [exam for exam in exams if exam.get("date") == today]
    
    attributes = {
        "exams": [_format_exam_info(exam) for exam in exams_today],
        "count": len(exams_today),
    }
    return attributes


def get_exams_this_week_count(student_data: Dict[str, Any]) -> str:
    """Get count of exams this week."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    monday_str = monday.isoformat()
    friday_str = friday.isoformat()
    
    exams_this_week = [exam for exam in exams 
                      if monday_str <= exam.get("date", "") <= friday_str]
    return str(len(exams_this_week))


def get_exams_this_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for exams this week sensor."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    monday_str = monday.isoformat()
    friday_str = friday.isoformat()
    
    exams_this_week = [exam for exam in exams 
                      if monday_str <= exam.get("date", "") <= friday_str]
    
    # Sort by date
    exams_this_week.sort(key=lambda x: x.get("date", ""))
    
    # Get unique subjects
    subjects = set()
    for exam in exams_this_week:
        subject = exam.get("subject", {})
        if isinstance(subject, dict):
            subjects.add(subject.get("name", "Unknown"))
        else:
            subjects.add(str(subject))
    
    attributes = {
        "exams": [_format_exam_info(exam) for exam in exams_this_week],
        "count": len(exams_this_week),
        "subjects": sorted(list(subjects)),
    }
    return attributes


def get_exams_next_week_count(student_data: Dict[str, Any]) -> str:
    """Get count of exams next week."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    next_friday = next_monday + timedelta(days=4)
    
    monday_str = next_monday.isoformat()
    friday_str = next_friday.isoformat()
    
    exams_next_week = [exam for exam in exams 
                      if monday_str <= exam.get("date", "") <= friday_str]
    return str(len(exams_next_week))


def get_exams_next_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for exams next week sensor."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    next_friday = next_monday + timedelta(days=4)
    
    monday_str = next_monday.isoformat()
    friday_str = next_friday.isoformat()
    
    exams_next_week = [exam for exam in exams 
                      if monday_str <= exam.get("date", "") <= friday_str]
    
    # Sort by date
    exams_next_week.sort(key=lambda x: x.get("date", ""))
    
    # Get unique subjects
    subjects = set()
    for exam in exams_next_week:
        subject = exam.get("subject", {})
        if isinstance(subject, dict):
            subjects.add(subject.get("name", "Unknown"))
        else:
            subjects.add(str(subject))
    
    attributes = {
        "exams": [_format_exam_info(exam) for exam in exams_next_week],
        "count": len(exams_next_week),
        "subjects": sorted(list(subjects)),
    }
    return attributes


def get_exams_upcoming_count(student_data: Dict[str, Any]) -> str:
    """Get count of upcoming exams (next 30 days)."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    future_limit = (today + timedelta(days=30)).isoformat()
    today_str = today.isoformat()
    
    upcoming_exams = [exam for exam in exams 
                     if today_str <= exam.get("date", "") <= future_limit]
    return str(len(upcoming_exams))


def get_exams_upcoming_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for upcoming exams sensor."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    future_limit = (today + timedelta(days=30)).isoformat()
    today_str = today.isoformat()
    
    upcoming_exams = [exam for exam in exams 
                     if today_str <= exam.get("date", "") <= future_limit]
    
    # Sort by date
    upcoming_exams.sort(key=lambda x: x.get("date", ""))
    
    # Get unique subjects
    subjects = set()
    for exam in upcoming_exams:
        subject = exam.get("subject", {})
        if isinstance(subject, dict):
            subjects.add(subject.get("name", "Unknown"))
        else:
            subjects.add(str(subject))
    
    attributes = {
        "exams": [_format_exam_info(exam) for exam in upcoming_exams],
        "count": len(upcoming_exams),
        "subjects": sorted(list(subjects)),
        "next_exam_date": upcoming_exams[0].get("date", "") if upcoming_exams else "",
    }
    
    # Mark the next exam
    for i, exam_info in enumerate(attributes["exams"]):
        exam_info["is_next_exam"] = (i == 0)
    
    return attributes


def calculate_days_until(date_str: str) -> int:
    """Calculate how many days until exam date."""
    try:
        exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (exam_date - today).days
    except (ValueError, TypeError):
        return 0


def get_exam_priority(exam: Dict[str, Any]) -> int:
    """Get exam priority for sorting (lower number = higher priority)."""
    exam_type = exam.get("type", {})
    if isinstance(exam_type, dict):
        type_name = exam_type.get("name", "").lower()
    else:
        type_name = str(exam_type).lower()
    
    # Priority order: Klassenarbeit > Test > Lernkontrolle > other
    if "klassenarbeit" in type_name or "klausur" in type_name:
        return 1
    elif "test" in type_name:
        return 2
    elif "lernkontrolle" in type_name or "lk" in type_name:
        return 3
    else:
        return 4


def format_exam_time_range(start_class_hour: Dict[str, Any]) -> str:
    """Format exam time range for display."""
    if not isinstance(start_class_hour, dict):
        return ""
    
    time_from = start_class_hour.get("from", "")
    time_until = start_class_hour.get("until", "")
    
    if time_from and time_until:
        return f"{time_from[:5]}-{time_until[:5]}"
    elif time_from:
        return time_from[:5]
    else:
        return ""