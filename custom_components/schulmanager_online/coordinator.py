"""Data update coordinator for Schulmanager Online."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SchulmanagerAPI, SchulmanagerAPIError
from .const import DEFAULT_LOOKAHEAD_WEEKS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SchulmanagerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        api: SchulmanagerAPI, 
        options: Dict[str, Any]
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.options = options
        self.students: List[Dict[str, Any]] = []
        self.previous_data: Dict[str, Any] = {}  # For change detection
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            # Get students if not already cached
            if not self.students:
                self.students = await self.api.get_students()
            
            # Get options
            weeks_ahead = self.options.get("weeks_ahead", DEFAULT_LOOKAHEAD_WEEKS)
            include_homework = self.options.get("include_homework", True)
            include_grades = self.options.get("include_grades", False)
            include_exams = self.options.get("include_exams", True)
            
            # Calculate date range
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())  # Monday of this week
            end_date = start_date + timedelta(weeks=weeks_ahead)
            
            data = {"students": {}, "last_update": datetime.now().isoformat()}
            
            # Get data for each student
            for student in self.students:
                student_id = student.get("id")
                student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
                
                if not student_id:
                    continue
                
                try:
                    # Get schedule
                    schedule_data = await self.api.get_schedule(
                        student_id, start_date, end_date
                    )
                    
                    processed_schedule = self._process_schedule_data(schedule_data)
                    
                    student_data = {
                        "info": student,
                        "schedule": processed_schedule,
                        "schedule_config": self._get_schedule_config(),
                        "current_lesson": self._get_current_lesson(processed_schedule),
                        "next_lesson": self._get_next_lesson(processed_schedule),
                        "today_lessons": self._get_today_lessons(processed_schedule),
                        "today_changes": self._get_today_changes(processed_schedule),
                        "tomorrow_lessons": self._get_tomorrow_lessons(processed_schedule),
                        "next_school_day": self._get_next_school_day_lessons(processed_schedule),
                        "this_week": self._get_this_week_lessons(processed_schedule),
                        "next_week": self._get_next_week_lessons(processed_schedule),
                        "changes_detected": self._detect_changes(student_id, processed_schedule),
                    }

                    # Get homework if enabled
                    if include_homework:
                        try:
                            homework_data = await self.api.get_homework(student_id)
                            student_data["homework"] = homework_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get homework for %s: %s", student_name, e)
                            student_data["homework"] = {"homeworks": []}

                    # Get grades if enabled
                    if include_grades:
                        try:
                            grades_data = await self.api.get_grades(student_id)
                            student_data["grades"] = grades_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get grades for %s: %s", student_name, e)
                            student_data["grades"] = {"grades": []}

                    # Get exams if enabled
                    if include_exams:
                        try:
                            # Get exams for extended period (8 weeks for better coverage)
                            exam_start_date = today - timedelta(weeks=1)  # Include past week
                            exam_end_date = start_date + timedelta(weeks=8)  # Extended range
                            exams_data = await self.api.get_exams(student_id, exam_start_date, exam_end_date)
                            student_data["exams"] = exams_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get exams for %s: %s", student_name, e)
                            student_data["exams"] = {"exams": []}

                    data["students"][student_id] = student_data

                except SchulmanagerAPIError as e:
                    _LOGGER.error("Failed to get data for student %s: %s", student_name, e)
                    # Continue with other students even if one fails
                    continue

            # Get letters (Elternbriefe) - these are account-wide, not per student
            include_letters = self.options.get("include_letters", True)
            if include_letters:
                try:
                    letters_data = await self.api.get_letters()
                    data["letters"] = letters_data
                    _LOGGER.debug("Retrieved %d letters", len(letters_data.get("data", [])))
                except SchulmanagerAPIError as e:
                    _LOGGER.warning("Failed to get letters: %s", e)
                    data["letters"] = {"data": []}

            return data

        except Exception as e:
            _LOGGER.error("Error communicating with API: %s", e)
            raise UpdateFailed(f"Error communicating with API: {e}") from e

    def _process_schedule_data(self, schedule_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and normalize schedule data."""
        lessons = schedule_data.get("lessons", [])
        processed_lessons = []
        
        for lesson in lessons:
            processed_lesson = self._process_lesson(lesson)
            if processed_lesson:
                processed_lessons.append(processed_lesson)
        
        # Sort by date and time
        processed_lessons.sort(key=lambda x: (x.get("date", ""), x.get("start_time", "")))
        
        # Post-process to assign correct hour numbers by date
        processed_lessons = self._assign_correct_hour_numbers(processed_lessons)
        
        return processed_lessons

    def _process_lesson(self, lesson: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single lesson."""
        try:
            # Extract actual lesson data (API structure: lesson.actualLesson contains the details)
            actual_lesson = lesson.get("actualLesson", {})
            class_hour = lesson.get("classHour", {})
            
            # Extract basic information
            processed = {
                "id": actual_lesson.get("lessonId", lesson.get("id")),
                "date": lesson.get("date"),
                "class_hour_number": class_hour.get("number"),
                "start_time": class_hour.get("from"),
                "end_time": class_hour.get("until"),
                "subject": actual_lesson.get("subject", {}).get("name", ""),
                "subject_name": actual_lesson.get("subject", {}).get("name", ""),
                "subject_abbreviation": actual_lesson.get("subject", {}).get("abbreviation", ""),
                "room": actual_lesson.get("room", {}).get("name", ""),
                "teachers": actual_lesson.get("teachers", []),
                "is_substitution": lesson.get("type") == "substitution",
                "type": lesson.get("type", "regularLesson"),
                "comment": lesson.get("comment", ""),
            }
            
            # If class_hour_number or times are missing, calculate them
            processed = self._enhance_lesson_with_calculated_times(processed)
            
            # Handle teacher information
            teachers = processed["teachers"]
            if teachers and isinstance(teachers, list):
                # Extract teacher names and abbreviations
                teacher_info = []
                for teacher in teachers:
                    if isinstance(teacher, dict):
                        firstname = teacher.get("firstname", "")
                        lastname = teacher.get("lastname", "")
                        full_name = f"{firstname} {lastname}".strip()
                        abbrev = teacher.get("abbreviation", "")
                        teacher_info.append({
                            "name": full_name,
                            "firstname": firstname,
                            "lastname": lastname,
                            "abbreviation": abbrev
                        })
                processed["teachers"] = teacher_info
                
                # Add primary teacher info for easy access
                if teacher_info:
                    primary_teacher = teacher_info[0]
                    processed["teacher"] = primary_teacher["abbreviation"]  # Keep abbreviation as main teacher field
                    processed["teacher_firstname"] = primary_teacher["firstname"]
                    processed["teacher_lastname"] = primary_teacher["lastname"]
                    processed["teacher_abbreviation"] = primary_teacher["abbreviation"]
            
            # Handle original teacher for substitutions
            if processed["is_substitution"] and lesson.get("originalTeacher"):
                processed["original_teacher"] = lesson["originalTeacher"]
            
            return processed
            
        except Exception as e:
            _LOGGER.warning("Failed to process lesson: %s", e)
            return None

    def _get_next_lesson(self, lessons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the next upcoming lesson."""
        now = datetime.now()
        
        for lesson in lessons:
            lesson_datetime = self._parse_lesson_datetime(lesson)
            if lesson_datetime and lesson_datetime > now:
                return lesson
        
        return None

    def _get_today_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get today's lessons."""
        today = datetime.now().date().isoformat()
        
        return [lesson for lesson in lessons if lesson["date"] == today]

    def _get_tomorrow_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get tomorrow's lessons (literal next calendar day)."""
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        return [lesson for lesson in lessons if lesson["date"] == tomorrow]

    def _parse_lesson_datetime(self, lesson: Dict[str, Any]) -> Optional[datetime]:
        """Parse lesson date and time into datetime object."""
        try:
            date_str = lesson["date"]
            time_str = lesson["start_time"]
            
            if not date_str or not time_str:
                return None
                
            datetime_str = f"{date_str} {time_str}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            
        except (ValueError, KeyError) as e:
            _LOGGER.debug("Failed to parse lesson datetime: %s", e)
            return None

    def get_student_data(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific student."""
        if not self.data or "students" not in self.data:
            return None
        
        return self.data["students"].get(student_id)

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Get all students."""
        return self.students

    def _get_schedule_config(self) -> Dict[str, Any]:
        """Get schedule timing configuration from options."""
        from .const import (
            CONF_LESSON_DURATION, CONF_SHORT_BREAK, CONF_LONG_BREAK_1,
            CONF_LONG_BREAK_2, CONF_LUNCH_BREAK, CONF_SCHOOL_START_TIME,
            DEFAULT_LESSON_DURATION, DEFAULT_SHORT_BREAK, DEFAULT_LONG_BREAK_1,
            DEFAULT_LONG_BREAK_2, DEFAULT_LUNCH_BREAK, DEFAULT_SCHOOL_START_TIME
        )
        
        return {
            "lesson_duration_minutes": self.options.get(CONF_LESSON_DURATION, DEFAULT_LESSON_DURATION),
            "short_break_minutes": self.options.get(CONF_SHORT_BREAK, DEFAULT_SHORT_BREAK),
            "long_break_1_minutes": self.options.get(CONF_LONG_BREAK_1, DEFAULT_LONG_BREAK_1),
            "long_break_2_minutes": self.options.get(CONF_LONG_BREAK_2, DEFAULT_LONG_BREAK_2),
            "lunch_break_minutes": self.options.get(CONF_LUNCH_BREAK, DEFAULT_LUNCH_BREAK),
            "school_start_time": self.options.get(CONF_SCHOOL_START_TIME, DEFAULT_SCHOOL_START_TIME),
        }

    def _enhance_lesson_with_calculated_times(self, lesson: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance lesson with calculated times and hour numbers if missing."""
        # If we already have complete data, return as-is
        if (lesson.get("class_hour_number") and 
            lesson.get("start_time") and 
            lesson.get("end_time")):
            return lesson
            
        # Get schedule configuration
        schedule_config = self._get_schedule_config()
        
        # If class_hour_number is missing, leave it as None (like AGs, special events)
        # These lessons will use their actual start_time and end_time directly
        
        # Only calculate times if we have a class_hour_number but missing times
        if lesson.get("class_hour_number") and (not lesson.get("start_time") or not lesson.get("end_time")):
            hour_number = lesson.get("class_hour_number")
            start_time, end_time = self._calculate_times_for_hour(hour_number, schedule_config)
            lesson["start_time"] = start_time
            lesson["end_time"] = end_time
            _LOGGER.debug(f"Calculated times {start_time}-{end_time} for hour {hour_number}")
        
        # For lessons without class_hour_number (AGs, etc.), keep original times from API
            
        return lesson
    
    def _get_lessons_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all lessons for a specific date from current data."""
        if not self.data or "students" not in self.data:
            return []
            
        all_lessons = []
        for student_data in self.data["students"].values():
            schedule = student_data.get("schedule", [])
            date_lessons = [lesson for lesson in schedule if lesson.get("date") == date]
            all_lessons.extend(date_lessons)
            
        return all_lessons
        
    def _calculate_times_for_hour(self, hour_number, config: Dict[str, Any]) -> tuple[str, str]:
        """Calculate start and end time for a given hour number."""
        try:
            # Convert hour_number to int if it's a string
            if isinstance(hour_number, str):
                hour_number = int(hour_number)
            elif hour_number is None:
                hour_number = 1
        except (ValueError, TypeError):
            hour_number = 1
            
        start_minutes = self._parse_time_to_minutes(config.get("school_start_time", "08:00"))
        lesson_duration = config.get("lesson_duration_minutes", 45)
        short_break = config.get("short_break_minutes", 5)
        long_break_1 = config.get("long_break_1_minutes", 20)
        long_break_2 = config.get("long_break_2_minutes", 10)
        lunch_break = config.get("lunch_break_minutes", 45)
        
        # Calculate accumulated time for this hour
        for h in range(1, hour_number):
            start_minutes += lesson_duration  # Previous lesson duration
            
            # Add appropriate break
            if h == 2:
                start_minutes += long_break_1  # After 2nd hour
            elif h == 4:
                start_minutes += long_break_2  # After 4th hour
            elif h == 6:
                start_minutes += lunch_break  # After 6th hour
            else:
                start_minutes += short_break  # Regular break
        
        # Calculate end time
        end_minutes = start_minutes + lesson_duration
        
        return (
            self._format_minutes_to_time(start_minutes),
            self._format_minutes_to_time(end_minutes)
        )
        
    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except Exception:
            return 8 * 60  # Default to 8:00 AM
            
    def _format_minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to time string (HH:MM:SS)."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}:00"

    def _assign_correct_hour_numbers(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign correct hour numbers to lessons grouped by date."""
        # Group lessons by date
        lessons_by_date = {}
        for lesson in lessons:
            date = lesson.get("date")
            if date:
                if date not in lessons_by_date:
                    lessons_by_date[date] = []
                lessons_by_date[date].append(lesson)
        
        # Process each date separately
        updated_lessons = []
        schedule_config = self._get_schedule_config()
        
        for date, date_lessons in lessons_by_date.items():
            # Sort lessons by existing time if available
            date_lessons.sort(key=lambda x: x.get("start_time") or "00:00:00")
            
            # Assign sequential hour numbers and recalculate times
            for i, lesson in enumerate(date_lessons):
                hour_number = i + 1
                lesson["class_hour_number"] = hour_number
                
                # Recalculate times based on correct hour number  
                start_time, end_time = self._calculate_times_for_hour(hour_number, schedule_config)
                lesson["start_time"] = start_time
                lesson["end_time"] = end_time
                
                updated_lessons.append(lesson)
        
        return updated_lessons

    def _get_current_lesson(self, lessons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the currently active lesson."""
        now = datetime.now()
        
        for lesson in lessons:
            lesson_start = self._parse_lesson_datetime(lesson)
            lesson_end = self._parse_lesson_end_datetime(lesson)
            
            if lesson_start and lesson_end and lesson_start <= now <= lesson_end:
                return lesson
        
        return None

    def _get_today_changes(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get today's lessons that have changes (substitutions, cancellations)."""
        today = datetime.now().date().isoformat()
        changes = []
        
        for lesson in lessons:
            if (lesson["date"] == today and 
                (lesson.get("is_substitution") or 
                 lesson.get("type") in ["changedLesson", "cancelledLesson"])):
                changes.append(lesson)
        
        return changes

    def _get_this_week_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all lessons for this week (Monday to Friday)."""
        now = datetime.now()
        # Get Monday of this week
        monday = now - timedelta(days=now.weekday())
        friday = monday + timedelta(days=4)
        
        monday_str = monday.date().isoformat()
        friday_str = friday.date().isoformat()
        
        week_lessons = []
        for lesson in lessons:
            if monday_str <= lesson["date"] <= friday_str:
                week_lessons.append(lesson)
        
        return week_lessons

    def _get_next_week_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all lessons for next week (Monday to Friday)."""
        now = datetime.now()
        # Get Monday of next week
        next_monday = now + timedelta(days=(7 - now.weekday()))
        next_friday = next_monday + timedelta(days=4)
        
        monday_str = next_monday.date().isoformat()
        friday_str = next_friday.date().isoformat()
        
        week_lessons = []
        for lesson in lessons:
            if monday_str <= lesson["date"] <= friday_str:
                week_lessons.append(lesson)
        
        return week_lessons

    def _get_next_school_day_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get lessons for the next school day (skipping weekends)."""
        now = datetime.now()
        current_date = now.date()
        
        # Find next school day (Monday-Friday)
        for days_ahead in range(1, 8):  # Check up to 7 days ahead
            check_date = current_date + timedelta(days=days_ahead)
            # Skip weekends (Saturday=5, Sunday=6)
            if check_date.weekday() < 5:
                date_str = check_date.isoformat()
                day_lessons = [lesson for lesson in lessons if lesson["date"] == date_str]
                if day_lessons:  # Only return if there are actually lessons
                    return day_lessons
        
        return []

    def _detect_changes(self, student_id: int, current_schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect changes between previous and current schedule."""
        if student_id not in self.previous_data or "schedule" not in self.previous_data[student_id]:
            return {"has_changes": False, "changes": []}
        
        previous_schedule = self.previous_data[student_id]["schedule"]
        changes = []
        
        # Create lookup dictionaries for easier comparison
        previous_lookup = {}
        for lesson in previous_schedule:
            key = f"{lesson['date']}_{lesson['class_hour_number']}"
            previous_lookup[key] = lesson
        
        current_lookup = {}
        for lesson in current_schedule:
            key = f"{lesson['date']}_{lesson['class_hour_number']}"
            current_lookup[key] = lesson
        
        # Check for changes in existing lessons
        for key, current_lesson in current_lookup.items():
            if key in previous_lookup:
                previous_lesson = previous_lookup[key]
                change = self._compare_lessons(previous_lesson, current_lesson)
                if change:
                    changes.append(change)
            else:
                # New lesson added
                changes.append({
                    "type": "added",
                    "date": current_lesson["date"],
                    "class_hour": current_lesson["class_hour_number"],
                    "current": current_lesson,
                    "previous": None,
                    "description": f"New lesson added: {current_lesson.get('subject', 'Unknown')}"
                })
        
        # Check for removed lessons
        for key, previous_lesson in previous_lookup.items():
            if key not in current_lookup:
                changes.append({
                    "type": "removed",
                    "date": previous_lesson["date"],
                    "class_hour": previous_lesson["class_hour_number"],
                    "current": None,
                    "previous": previous_lesson,
                    "description": f"Lesson removed: {previous_lesson.get('subject', 'Unknown')}"
                })
        
        return {
            "has_changes": len(changes) > 0,
            "changes": changes,
            "change_count": len(changes)
        }

    def _compare_lessons(self, previous: Dict[str, Any], current: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Compare two lessons and return change information if different."""
        changes_found = []
        
        # Check key fields for changes
        fields_to_check = [
            ("subject", "Subject"),
            ("room", "Room"),
            ("start_time", "Start time"),
            ("end_time", "End time"),
            ("teachers", "Teachers"),
            ("is_substitution", "Substitution status"),
            ("type", "Lesson type"),
            ("comment", "Comment")
        ]
        
        for field, display_name in fields_to_check:
            prev_value = previous.get(field)
            curr_value = current.get(field)
            
            # Special handling for teachers (list comparison)
            if field == "teachers":
                prev_teachers = [t.get("abbreviation", "") for t in (prev_value or [])]
                curr_teachers = [t.get("abbreviation", "") for t in (curr_value or [])]
                if prev_teachers != curr_teachers:
                    changes_found.append({
                        "field": field,
                        "display_name": display_name,
                        "previous": ", ".join(prev_teachers),
                        "current": ", ".join(curr_teachers)
                    })
            else:
                if prev_value != curr_value:
                    changes_found.append({
                        "field": field,
                        "display_name": display_name,
                        "previous": prev_value,
                        "current": curr_value
                    })
        
        if changes_found:
            return {
                "type": "modified",
                "date": current["date"],
                "class_hour": current["class_hour_number"],
                "current": current,
                "previous": previous,
                "field_changes": changes_found,
                "description": f"Changes in {current.get('subject', 'Unknown')}: {', '.join([c['display_name'] for c in changes_found])}"
            }
        
        return None

    def _parse_lesson_end_datetime(self, lesson: Dict[str, Any]) -> Optional[datetime]:
        """Parse lesson end date and time into datetime object."""
        try:
            date_str = lesson["date"]
            time_str = lesson["end_time"]
            
            if not date_str or not time_str:
                return None
                
            datetime_str = f"{date_str} {time_str}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            
        except (ValueError, KeyError) as e:
            _LOGGER.debug("Failed to parse lesson end datetime: %s", e)
            return None
