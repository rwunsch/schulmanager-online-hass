#!/usr/bin/env python3
"""
Clean Schedule Table Generator for Schulmanager Online with Free Hours Detection

This script creates a clean, readable schedule table showing:
- Regular lessons
- Cancelled lessons with replacements  
- Free hours as blank cells (including period 7)
"""

import asyncio
import sys
import os
import re
import json
import getpass
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

try:
    import aiohttp
    from standalone_api import StandaloneSchulmanagerAPI, SchulmanagerAPIError
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the test-scripts directory and have installed requirements")
    sys.exit(1)

# Configuration
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '.credentials')
MAX_LESSON_NUMBER = 12
WORKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

class CleanScheduleTableGenerator:
    """Generate a clean schedule table with free hours detection."""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.api: Optional[StandaloneSchulmanagerAPI] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.api = StandaloneSchulmanagerAPI(self.email, self.password, self.session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _sanitize_text(self, text: str) -> str:
        """Clean up text for display."""
        if not text:
            return ""
        # Remove parentheses content and trim
        text = re.sub(r'\s*\([^)]*\)', '', text)
        text = text.split(',')[0].strip()
        return text[:20]  # Limit length
    
    def _extract_lesson_info(self, lesson: Dict[str, Any]) -> tuple[str, str, str]:
        """Extract subject, room, teacher from any lesson type."""
        lesson_type = lesson.get("type", "")
        
        if lesson_type == "freeHour":
            return "", "", ""
            
        elif lesson_type == "event":
            event_data = lesson.get("event", {})
            subject = f"[EVENT] {event_data.get('text', 'Event')}"
            teachers = event_data.get("teachers", [])
            teacher = teachers[0].get("lastname", "") if teachers else ""
            return self._sanitize_text(subject), "", teacher
            
        elif lesson_type == "cancelledLesson":
            original_lessons = lesson.get("originalLessons", [])
            if original_lessons:
                orig = original_lessons[0]
                subject = f"[CANCELLED] {orig.get('subject', {}).get('name', '')}"
                room = orig.get('room', {}).get('name', '')
                teachers = orig.get('teachers', [])
                teacher = teachers[0].get("lastname", "") if teachers else ""
                return self._sanitize_text(subject), room, teacher
            return "[CANCELLED]", "", ""
            
        else:
            # Regular or changed lesson
            actual_lesson = lesson.get("actualLesson", {})
            if actual_lesson:
                subject_name = actual_lesson.get('subject', {}).get('name', '')
                room = actual_lesson.get('room', {}).get('name', '')
                teachers = actual_lesson.get('teachers', [])
                teacher = teachers[0].get("lastname", "") if teachers else ""
                
                if lesson_type == "changedLesson":
                    subject_name = f"[CHANGED] {subject_name}"
                    
                return self._sanitize_text(subject_name), room, teacher
                
        return "", "", ""
    
    def _organize_schedule(self, lessons: List[Dict[str, Any]], class_hours: List[Dict[str, Any]], 
                          start_date: date, end_date: date) -> tuple[Dict[str, Dict[int, List[Dict[str, Any]]]], set]:
        """Organize lessons into a clean grid structure and return available periods."""
        
        # Get available periods from class hours
        available_periods = set()
        for class_hour in class_hours:
            try:
                period_num = int(class_hour.get("number", 0))
                if 1 <= period_num <= MAX_LESSON_NUMBER:
                    available_periods.add(period_num)
            except (ValueError, TypeError):
                continue
        
        print(f"📋 Available periods: {sorted(available_periods)}")
        
        # Initialize grid
        grid = {}
        for weekday in WORKDAYS:
            grid[weekday] = {}
            for period in available_periods:
                grid[weekday][period] = []
        
        # Add actual lessons to grid
        for lesson in lessons:
            lesson_date = lesson.get("date", "")
            if not lesson_date:
                continue
                
            try:
                date_obj = datetime.strptime(lesson_date, "%Y-%m-%d").date()
                if not (start_date <= date_obj <= end_date):
                    continue
                    
                weekday = date_obj.strftime("%A")
                if weekday not in WORKDAYS:
                    continue
                    
                # Get lesson period
                class_hour = lesson.get("classHour", {})
                try:
                    period_num = int(class_hour.get("number", 0))
                    if period_num in available_periods:
                        grid[weekday][period_num].append(lesson)
                except (ValueError, TypeError):
                    continue
                    
            except ValueError:
                continue
        
        # Note: Free hours are left as empty slots (no entries added)
        # This makes them appear as blank cells in the table
        
        return grid, available_periods
    
    def _print_clean_table(self, grid: Dict[str, Dict[int, List[Dict[str, Any]]]], 
                          available_periods: set, start_date: date):
        """Print a clean, readable schedule table showing ALL available periods."""
        end_date = start_date + timedelta(days=4)
        
        print(f"\n📅 Schedule Table: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print("=" * 140)
        
        # Header
        header = "Period │"
        date_row = "   #   │"
        for weekday in WORKDAYS:
            date_str = (start_date + timedelta(days=WORKDAYS.index(weekday))).strftime("%m-%d")
            header += f" {weekday:^26} │"
            date_row += f" {date_str:^26} │"
        
        print(header)
        print(date_row)
        print("─" * 140)
        
        # Print each period - INCLUDING EMPTY ONES
        for period_num in sorted(available_periods):
            if period_num > MAX_LESSON_NUMBER:
                continue
            
            # Always show the period, even if it has no lessons anywhere
            print(f"  {period_num:2d}   │", end="")
            
            # Print each weekday for this period
            for weekday in WORKDAYS:
                lessons_in_slot = grid.get(weekday, {}).get(period_num, [])
                
                if lessons_in_slot:
                    # Sort lessons: cancelled first, then events, then regular
                    sorted_lessons = sorted(lessons_in_slot, key=lambda x: (
                        0 if x.get("type") == "cancelledLesson" else
                        1 if x.get("type") == "event" else
                        2 if x.get("type") == "changedLesson" else
                        3 if x.get("type") == "regularLesson" else
                        4  # freeHour
                    ))
                    
                    # Show primary lesson (first in sorted order)
                    primary_lesson = sorted_lessons[0]
                    subject, room, teacher = self._extract_lesson_info(primary_lesson)
                    
                    # Format for display
                    display_text = subject
                    if len(sorted_lessons) > 1:
                        # Multiple lessons in slot (e.g., cancelled + replacement)
                        secondary = sorted_lessons[1]
                        if secondary.get("type") == "event":
                            event_text = secondary.get("event", {}).get("text", "Event")
                            display_text += f" / {event_text[:8]}..."
                    
                    # Truncate if too long
                    if len(display_text) > 26:
                        display_text = display_text[:23] + "..."
                    
                    print(f" {display_text:^26} │", end="")
                else:
                    # Empty slot - this is a free hour (blank cell)
                    print(f" {'':^26} │", end="")
            
            print()  # End the row
            
            # Print room and teacher info on separate lines
            for info_type in ["room", "teacher"]:
                print("       │", end="")  # Empty period column
                
                for weekday in WORKDAYS:
                    lessons_in_slot = grid.get(weekday, {}).get(period_num, [])
                    
                    if lessons_in_slot:
                        sorted_lessons = sorted(lessons_in_slot, key=lambda x: (
                            0 if x.get("type") == "cancelledLesson" else
                            1 if x.get("type") == "event" else
                            2 if x.get("type") == "changedLesson" else
                            3 if x.get("type") == "regularLesson" else
                            4
                        ))
                        
                        primary_lesson = sorted_lessons[0]
                        subject, room, teacher = self._extract_lesson_info(primary_lesson)
                        
                        if info_type == "room":
                            content = room[:12] if room else ""
                        else:  # teacher
                            content = teacher[:15] if teacher else ""
                        
                        print(f" {content:^26} │", end="")
                    else:
                        # Empty slot - blank cell for room/teacher too
                        print(f" {'':^26} │", end="")
                
                print()  # End the info row
            
            print("─" * 140)  # Separator after each period
        
        # Legend
        print("\n📝 Legend:")
        print("   Empty cells = Free periods (no scheduled lesson)")
        print("   [CANCELLED] Subject = Original lesson was cancelled")
        print("   [EVENT] Event Name = Special school event")
        print("   [CHANGED] Subject = Lesson has substitution/changes")
        print("   Multiple entries show cancelled + replacement")
    
    async def generate_schedule_table(self) -> None:
        """Main method to generate the clean schedule table."""
        try:
            print("🚀 Clean Schulmanager Schedule Table Generator")
            print("=" * 60)
            
            # Authenticate
            print("🔐 Authenticating...")
            await self.api.authenticate()
            print("✅ Authentication successful")
            
            # Get students
            students = await self.api.get_students()
            if not students:
                print("❌ No students found")
                return
            
            student = students[0]
            student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
            print(f"👤 Student: {student_name}")
            
            # Calculate date range (this week)
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())  # Monday
            end_of_week = start_of_week + timedelta(days=4)  # Friday
            
            print(f"📅 Week: {start_of_week} to {end_of_week}")
            
            # Fetch data
            requests = [
                {
                    "moduleName": "schedules",
                    "endpointName": "get-actual-lessons",
                    "parameters": {
                        "student": student,
                        "start": start_of_week.isoformat(),
                        "end": end_of_week.isoformat()
                    }
                },
                {
                    "moduleName": "schedules",
                    "endpointName": "get-class-hours",
                    "parameters": {}
                }
            ]
            
            api_response = await self.api._make_api_call(requests)
            
            # Extract data
            results = api_response.get("results", [])
            if len(results) < 2:
                print("❌ Failed to retrieve complete data")
                return
            
            lessons = results[0].get("data", []) if results[0].get("status") == 200 else []
            class_hours = results[1].get("data", []) if results[1].get("status") == 200 else []
            
            print(f"✅ Retrieved {len(lessons)} lessons and {len(class_hours)} class periods")
            
            # Organize and display
            grid, available_periods = self._organize_schedule(lessons, class_hours, start_of_week, end_of_week)
            self._print_clean_table(grid, available_periods, start_of_week)
            
            print(f"\n✅ Clean schedule table generated successfully!")
            
        except SchulmanagerAPIError as e:
            print(f"❌ API error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


def load_credentials() -> tuple[str, str]:
    """Load credentials from file or prompt user."""
    
    # Try .credentials file
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 2:
                    return lines[0].strip(), lines[1].strip()
        except Exception:
            pass
    
    # Try environment variables
    email = os.getenv('SCHULMANAGER_EMAIL')
    password = os.getenv('SCHULMANAGER_PASSWORD')
    if email and password:
        return email, password
    
    # Prompt user
    print("🔐 Enter your Schulmanager Online credentials:")
    try:
        email = input("📧 Email: ").strip()
        password = getpass.getpass("🔒 Password: ").strip()
        
        if not email or not password:
            return None, None
        
        # Optionally save credentials
        save = input("💾 Save credentials? (y/N): ").strip().lower()
        if save in ['y', 'yes']:
            try:
                with open(CREDENTIALS_FILE, 'w') as f:
                    f.write(f"{email}\n{password}\n")
                os.chmod(CREDENTIALS_FILE, 0o600)
                print(f"✅ Credentials saved to {CREDENTIALS_FILE}")
            except Exception as e:
                print(f"⚠️  Failed to save: {e}")
        
        return email, password
        
    except KeyboardInterrupt:
        return None, None


async def main():
    """Main function."""
    # Check command line arguments
    if len(sys.argv) == 3:
        email, password = sys.argv[1], sys.argv[2]
    else:
        email, password = load_credentials()
    
    if not email or not password:
        print("❌ No valid credentials provided")
        sys.exit(1)
    
    async with CleanScheduleTableGenerator(email, password) as generator:
        await generator.generate_schedule_table()


if __name__ == "__main__":
    asyncio.run(main())
