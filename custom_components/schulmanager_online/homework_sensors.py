"""Homework sensor methods for Schulmanager Online - Updated for real API structure."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List


def _extract_homeworks(homework_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract homework list from API response."""
    # Handle different data structures
    data = homework_data.get("data", [])
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("homeworks", [])
    else:
        return homework_data.get("homeworks", [])


def get_homework_due_today_count(student_data: Dict[str, Any]) -> str:
    """Get count of homework due today."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    
    # Use 'date' field (actual field name from API)
    due_today = [hw for hw in homeworks if hw.get("date") == today]
    return str(len(due_today))


def get_homework_due_today_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for homework due today sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    due_today = [hw for hw in homeworks if hw.get("date") == today]
    
    attributes = {
        "homework": [],
        "count": len(due_today),
    }

    for hw in due_today:
        hw_info = {
            "subject": hw.get("subject", "Unknown"),
            "homework": hw.get("homework", "No homework description"),
            "date": hw.get("date", ""),
        }
        attributes["homework"].append(hw_info)

    return attributes


def get_homework_due_tomorrow_count(student_data: Dict[str, Any]) -> str:
    """Get count of homework due tomorrow."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
    
    due_tomorrow = [hw for hw in homeworks if hw.get("date") == tomorrow]
    return str(len(due_tomorrow))


def get_homework_due_tomorrow_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for homework due tomorrow sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
    due_tomorrow = [hw for hw in homeworks if hw.get("date") == tomorrow]
    
    attributes = {
        "homework": [],
        "count": len(due_tomorrow),
    }

    for hw in due_tomorrow:
        hw_info = {
            "subject": hw.get("subject", "Unknown"),
            "homework": hw.get("homework", "No homework description"),
            "date": hw.get("date", ""),
        }
        attributes["homework"].append(hw_info)

    return attributes


def get_homework_overdue_count(student_data: Dict[str, Any]) -> str:
    """Get count of overdue homework (past dates)."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    
    # Consider homework overdue if date is in the past
    overdue = [hw for hw in homeworks if hw.get("date", "") < today]
    return str(len(overdue))


def get_homework_overdue_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for overdue homework sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    overdue = [hw for hw in homeworks if hw.get("date", "") < today]
    
    attributes = {
        "homework": [],
        "count": len(overdue),
    }

    for hw in overdue:
        hw_info = {
            "subject": hw.get("subject", "Unknown"),
            "homework": hw.get("homework", "No homework description"),
            "date": hw.get("date", ""),
            "days_overdue": calculate_days_overdue(hw.get("date", "")),
        }
        attributes["homework"].append(hw_info)

    return attributes


def get_homework_upcoming_count(student_data: Dict[str, Any]) -> str:
    """Get count of upcoming homework (next 7 days)."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date()
    next_week = (today + timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    
    upcoming = [hw for hw in homeworks 
               if today_str < hw.get("date", "") <= next_week]
    return str(len(upcoming))


def get_homework_upcoming_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for upcoming homework sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date()
    next_week = (today + timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    
    upcoming = [hw for hw in homeworks 
               if today_str < hw.get("date", "") <= next_week]
    
    # Sort by date
    upcoming.sort(key=lambda x: x.get("date", ""))
    
    attributes = {
        "homework": [],
        "count": len(upcoming),
    }

    for hw in upcoming:
        hw_info = {
            "subject": hw.get("subject", "Unknown"),
            "homework": hw.get("homework", "No homework description"),
            "date": hw.get("date", ""),
            "days_until_due": calculate_days_until_due(hw.get("date", "")),
        }
        attributes["homework"].append(hw_info)

    return attributes


def get_homework_recent_count(student_data: Dict[str, Any]) -> str:
    """Get count of recent homework (last 7 days)."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date()
    last_week = (today - timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    
    recent = [hw for hw in homeworks 
             if last_week <= hw.get("date", "") <= today_str]
    return str(len(recent))


def get_homework_recent_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for recent homework sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date()
    last_week = (today - timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    
    recent = [hw for hw in homeworks 
             if last_week <= hw.get("date", "") <= today_str]
    
    # Sort by date (newest first)
    recent.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    attributes = {
        "homework": [],
        "count": len(recent),
        "subjects": list(set(hw.get("subject", "Unknown") for hw in recent)),
    }

    for hw in recent:
        hw_info = {
            "subject": hw.get("subject", "Unknown"),
            "homework": hw.get("homework", "No homework description"),
            "date": hw.get("date", ""),
            "days_ago": calculate_days_ago(hw.get("date", "")),
        }
        attributes["homework"].append(hw_info)

    return attributes


def calculate_days_overdue(date_str: str) -> int:
    """Calculate how many days homework is overdue."""
    try:
        hw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (today - hw_date).days
    except (ValueError, TypeError):
        return 0


def calculate_days_until_due(date_str: str) -> int:
    """Calculate how many days until homework is due."""
    try:
        hw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (hw_date - today).days
    except (ValueError, TypeError):
        return 0


def calculate_days_ago(date_str: str) -> int:
    """Calculate how many days ago homework was assigned."""
    try:
        hw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (today - hw_date).days
    except (ValueError, TypeError):
        return 0