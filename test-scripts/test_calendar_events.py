#!/usr/bin/env python3
"""Test script to verify calendar event creation."""

import json
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the custom component path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'schulmanager_online'))

from calendar import SchulmanagerOnlineCalendar

def test_calendar_events():
    """Test calendar event creation with sample data."""
    
    # Sample student data (based on API logs)
    student_data = {
        "schedule": [
            {
                "date": "2025-09-11",
                "classHour": {"id": 30172, "number": "5"},
                "type": "regularLesson",
                "actualLesson": {
                    "room": {"id": 131134, "name": "RD205"},
                    "subject": {"id": 255645, "abbreviation": "D", "name": "Deutsch"},
                    "teachers": [{"id": 370267, "abbreviation": "VolN", "firstname": "Nicole", "lastname": "Vollmer"}]
                }
            },
            {
                "date": "2025-09-12", 
                "classHour": {"id": 30173, "number": "1"},
                "type": "regularLesson",
                "actualLesson": {
                    "room": {"id": 131135, "name": "R101"},
                    "subject": {"id": 255646, "abbreviation": "M", "name": "Mathematik"},
                    "teachers": [{"id": 370268, "abbreviation": "MuS", "firstname": "Sarah", "lastname": "Müller"}]
                }
            }
        ],
        "homework": [
            {
                "date": "2025-08-28",
                "subject": "Englisch, Beginn in Jahrgangsklasse 5", 
                "homework": "Buch einschlagen\nEnglischordner mit Trennwänden mitbringen"
            },
            {
                "date": "2025-09-01",
                "subject": "Mathematik",
                "homework": "S. 9 Nr. 3 und 4"
            }
        ],
        "exams": {
            "data": [
                {
                    "subject": {"id": 255645, "name": "Deutsch", "abbreviation": "D"},
                    "type": {"id": 2224, "name": "Klassenarbeit", "color": "#c6dcef"},
                    "date": "2025-09-25",
                    "startClassHour": {"id": 30172, "number": "5", "from": "11:41:00", "until": "12:26:00"}
                }
            ]
        }
    }
    
    # Mock coordinator
    class MockCoordinator:
        def get_student_data(self, student_id):
            return student_data
    
    # Test calendar creation
    student_info = {"firstname": "Marc Cedric", "lastname": "Wunsch"}
    
    # Test schedule calendar
    print("=== Testing Schedule Calendar ===")
    schedule_calendar = SchulmanagerOnlineCalendar(
        coordinator=MockCoordinator(),
        student_id=4333047,
        student_info=student_info,
        calendar_type="schedule"
    )
    
    # Test date range
    tz = ZoneInfo("Europe/Berlin")
    start_date = datetime(2025, 9, 10, tzinfo=tz)
    end_date = datetime(2025, 9, 15, tzinfo=tz)
    
    try:
        events = schedule_calendar._get_events(start_date, end_date)
        print(f"Found {len(events)} schedule events")
        for event in events:
            print(f"  - {event.summary}: {event.start} to {event.end}")
            print(f"    Description: {event.description}")
    except Exception as e:
        print(f"Error getting schedule events: {e}")
        import traceback
        traceback.print_exc()
    
    # Test homework calendar  
    print("\n=== Testing Homework Calendar ===")
    homework_calendar = SchulmanagerOnlineCalendar(
        coordinator=MockCoordinator(),
        student_id=4333047,
        student_info=student_info,
        calendar_type="homework"
    )
    
    try:
        events = homework_calendar._get_events(start_date, end_date)
        print(f"Found {len(events)} homework events")
        for event in events:
            print(f"  - {event.summary}: {event.start} to {event.end}")
    except Exception as e:
        print(f"Error getting homework events: {e}")
        import traceback
        traceback.print_exc()
    
    # Test exam calendar
    print("\n=== Testing Exam Calendar ===")
    exam_calendar = SchulmanagerOnlineCalendar(
        coordinator=MockCoordinator(),
        student_id=4333047,
        student_info=student_info,
        calendar_type="exams"
    )
    
    try:
        events = exam_calendar._get_events(start_date, end_date)
        print(f"Found {len(events)} exam events")
        for event in events:
            print(f"  - {event.summary}: {event.start} to {event.end}")
    except Exception as e:
        print(f"Error getting exam events: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar_events()
