"""Data update coordinator for Schulmanager Online."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SchulmanagerAPI, SchulmanagerAPIError
from .const import DEFAULT_LOOKAHEAD_WEEKS, DOMAIN, UPDATE_INTERVAL
from .free_hours_utils import add_free_hours_to_schedule, parse_time_to_minutes, format_minutes_to_time

_LOGGER = logging.getLogger(__name__)


class SchulmanagerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        api_instances: Dict[int, Any],  # Changed from single api to api_instances dict
        options: Dict[str, Any]
    ) -> None:
        """Initialize the coordinator."""
        self.api_instances = api_instances  # Dict of {institution_id: SchulmanagerAPI}
        self.options = options
        self.students: List[Dict[str, Any]] = []
        self.previous_data: Dict[str, Any] = {}  # For change detection
        self._initial_refresh_done = False
        self._seen_homework: set = set()
        self._seen_grades: set = set()
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
    
    def _get_api_for_student(self, student: Dict[str, Any]):
        """Get the correct API instance for a student."""
        institution_id = student.get("_institution_id")
        
        if institution_id and institution_id in self.api_instances:
            return self.api_instances[institution_id]
        
        # Fallback: return first available API instance
        if self.api_instances:
            return next(iter(self.api_instances.values()))
        
        raise ValueError(f"No API instance found for student {student.get('id')}")

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            # Get students if not already cached
            if not self.students:
                # Collect students from all API instances
                all_students = []
                for institution_id, api in self.api_instances.items():
                    try:
                        students = await api.get_students()
                        # Ensure institution info is set
                        for student in students:
                            if "_institution_id" not in student:
                                student["_institution_id"] = institution_id
                        all_students.extend(students)
                    except Exception as e:
                        _LOGGER.error("Failed to get students from institution %d: %s", institution_id, e)
                        continue
                self.students = all_students
            
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
                    # Get the correct API instance for this student
                    student_api = self._get_api_for_student(student)
                    
                    # Get schedule and class hours
                    schedule_data = await student_api.get_schedule(
                        student_id, start_date, end_date
                    )
                    
                    # Get class hours configuration (for free hour detection)
                    try:
                        class_hours_data = await student_api.get_class_hours()
                        data["class_hours"] = class_hours_data
                    except Exception as e:
                        _LOGGER.warning(f"Failed to fetch class hours: {e}")
                        data["class_hours"] = []
                    
                    # Process regular schedule data
                    processed_schedule = self._process_schedule_data(schedule_data)
                    
                    # Add free hours using centralized utility
                    processed_schedule = add_free_hours_to_schedule(
                        processed_schedule, data.get("class_hours", []), start_date, end_date
                    )
                    
                    student_data = {
                        "info": student,
                        "schedule": processed_schedule,
                        # NOTE: schedule_config removed - timing now comes from API class_hours
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
                            homework_data = await student_api.get_homework(student_id)
                            student_data["homework"] = homework_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get homework for %s: %s", student_name, e)
                            student_data["homework"] = {"homeworks": []}

                    # Get grades if enabled
                    if include_grades:
                        try:
                            grades_data = await student_api.get_grades(student_id)
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
                            exams_data = await student_api.get_exams(student_id, exam_start_date, exam_end_date)
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
            # Try to get letters from each school's API
            include_letters = self.options.get("include_letters", True)
            if include_letters:
                all_letters = []
                for institution_id, api in self.api_instances.items():
                    try:
                        letters_data = await api.get_letters()
                        letters_list = letters_data.get("data", [])
                        # Add institution info to each letter to avoid duplicates
                        for letter in letters_list:
                            letter["_institution_id"] = institution_id
                        all_letters.extend(letters_list)
                    except SchulmanagerAPIError as e:
                        _LOGGER.warning("Failed to get letters from institution %d: %s", institution_id, e)
                        continue
                
                data["letters"] = {"data": all_letters}
                _LOGGER.debug("Retrieved %d letters across all schools", len(all_letters))

            # Detect new homework/grades after the first successful refresh only
            try:
                if self._initial_refresh_done:
                    self._detect_and_fire_events(data)
                else:
                    # Seed seen sets but do not fire on initial load
                    self._seed_seen_sets(data)
                    self._initial_refresh_done = True
            except Exception as err:
                _LOGGER.debug("Event detection error: %s", err)

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
            class_hour_num = class_hour.get("number")
            if class_hour_num:
                try:
                    class_hour_num = int(class_hour_num)
                except (ValueError, TypeError):
                    class_hour_num = None
            
            processed = {
                "id": actual_lesson.get("lessonId", lesson.get("id")),
                "date": lesson.get("date"),
                "class_hour_number": class_hour_num,
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

    # NOTE: _get_schedule_config() removed - timing now comes from API class_hours data

    def _enhance_lesson_with_calculated_times(self, lesson: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance lesson with calculated times and hour numbers if missing."""
        # If we already have complete data, return as-is
        if (lesson.get("class_hour_number") and 
            lesson.get("start_time") and 
            lesson.get("end_time")):
            return lesson
            
        # If class_hour_number is missing, leave it as None (like AGs, special events)
        # These lessons will use their actual start_time and end_time directly
        
        # Only calculate times if we have a class_hour_number but missing times
        if lesson.get("class_hour_number") and (not lesson.get("start_time") or not lesson.get("end_time")):
            hour_number = lesson.get("class_hour_number")
            start_time, end_time = self._calculate_times_for_hour(hour_number)
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
        
    def _calculate_times_for_hour(self, hour_number) -> tuple[str, str]:
        """Get start and end time for a given hour number from API class hours data."""
        try:
            # Convert hour_number to int if it's a string
            if isinstance(hour_number, str):
                hour_number = int(hour_number)
            elif hour_number is None:
                hour_number = 1
        except (ValueError, TypeError):
            hour_number = 1
        
        # Get class hours from API data
        if self.data and "class_hours" in self.data:
            class_hours = self.data["class_hours"]
            for class_hour in class_hours:
                if str(class_hour.get("number", "")) == str(hour_number):
                    start_time = class_hour.get("from", "08:00:00")
                    end_time = class_hour.get("until", "08:45:00")
                    return start_time, end_time
        
        # Fallback to default times if API data not available (should not happen)
        default_times = {
            "1": ("08:00:00", "08:45:00"),
            "2": ("08:48:00", "09:33:00"),
            "3": ("09:53:00", "10:38:00"),
            "4": ("10:43:00", "11:28:00"),
            "5": ("11:38:00", "12:23:00"),
            "6": ("12:28:00", "13:13:00"),
            "7": ("14:08:00", "14:53:00"),
            "8": ("14:58:00", "15:43:00"),
            "9": ("15:48:00", "16:33:00"),
            "10": ("16:38:00", "17:23:00"),
            "11": ("17:28:00", "18:13:00"),
        }
        return default_times.get(str(hour_number), ("08:00:00", "08:45:00"))
        

    def _assign_correct_hour_numbers(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure lessons have correct times based on their API-provided period numbers."""
        # The API already provides correct class_hour_number in classHour.number
        # We should NOT reassign these numbers as they indicate the actual periods
        # We just need to ensure times are correctly set from class hours data
        
        for lesson in lessons:
            # Only update times if we have a valid class_hour_number from API
            if lesson.get("class_hour_number") and not lesson.get("start_time"):
                hour_number = lesson.get("class_hour_number")
                start_time, end_time = self._calculate_times_for_hour(hour_number)
                lesson["start_time"] = start_time
                lesson["end_time"] = end_time
        
        return lessons

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

    def _seed_seen_sets(self, data: Dict[str, Any]) -> None:
        """Seed seen sets with initial data to avoid firing events on first load."""
        for student_id, student_data in data.get("students", {}).items():
            # Seed homework
            homework_data = student_data.get("homework", {}) or {}
            homeworks = homework_data.get("homeworks", []) or []
            for item in homeworks:
                key = self._homework_key(student_id, item)
                if key:
                    self._seen_homework.add(key)
            
            # Seed grades
            grades_data = student_data.get("grades", {}) or {}
            grade_items = []
            if isinstance(grades_data, dict):
                grade_items = grades_data.get("grades", []) or []
            elif isinstance(grades_data, list):
                grade_items = grades_data
            for g in grade_items:
                key = self._grade_key(student_id, g)
                if key:
                    self._seen_grades.add(key)

    def _detect_and_fire_events(self, data: Dict[str, Any]) -> None:
        """Detect new homework and grades and fire Home Assistant events."""
        # Build student name lookup
        student_names = {}
        for student_id, student_data in data.get("students", {}).items():
            info = student_data.get("info", {})
            name = f"{info.get('firstname', '')} {info.get('lastname', '')}".strip()
            student_names[student_id] = name
        
        # Homework events
        for student_id, student_data in data.get("students", {}).items():
            homework_data = student_data.get("homework", {}) or {}
            homeworks = homework_data.get("homeworks", []) or []
            for item in homeworks:
                key = self._homework_key(student_id, item)
                if not key or key in self._seen_homework:
                    continue
                self._seen_homework.add(key)
                self.hass.bus.async_fire(
                    "schulmanager_homework_new",
                    {
                        "student_id": student_id,
                        "student_name": student_names.get(student_id, ""),
                        "subject": item.get("subject", ""),
                        "homework": item.get("homework") or item.get("description", ""),
                        "date": item.get("date", ""),
                    },
                )
                _LOGGER.debug(
                    "Fired schulmanager_homework_new event for student %s: %s",
                    student_id,
                    item.get("subject", ""),
                )
        
        # Grade events
        for student_id, student_data in data.get("students", {}).items():
            grades_data = student_data.get("grades", {}) or {}
            grade_items = []
            if isinstance(grades_data, dict):
                grade_items = grades_data.get("grades", []) or []
            elif isinstance(grades_data, list):
                grade_items = grades_data
            for g in grade_items:
                key = self._grade_key(student_id, g)
                if not key or key in self._seen_grades:
                    continue
                self._seen_grades.add(key)
                subj = g.get("subject") or {}
                if isinstance(subj, dict):
                    subject_name = subj.get("name") or subj.get("longName") or "Subject"
                else:
                    subject_name = str(subj)
                self.hass.bus.async_fire(
                    "schulmanager_grade_new",
                    {
                        "student_id": student_id,
                        "student_name": student_names.get(student_id, ""),
                        "subject": subject_name,
                        "grade": g.get("value", ""),
                    },
                )
                _LOGGER.debug(
                    "Fired schulmanager_grade_new event for student %s: %s - %s",
                    student_id,
                    subject_name,
                    g.get("value", ""),
                )

    def _homework_key(self, student_id: int, item: Dict[str, Any]) -> Optional[str]:
        """Generate unique key for homework item."""
        date = str(item.get("date") or "").strip()
        subject = str(item.get("subject") or "").strip()
        homework = str(item.get("homework") or item.get("description") or "").strip()
        if not date or not (subject or homework):
            return None
        return f"{student_id}_{date}_{subject}_{homework}"

    def _grade_key(self, student_id: int, grade: Dict[str, Any]) -> Optional[str]:
        """Generate unique key for grade item."""
        subj = grade.get("subject") or {}
        if isinstance(subj, dict):
            subject_id = subj.get("id") or subj.get("abbreviation") or subj.get("name")
        else:
            subject_id = str(subj)
        value = str(grade.get("value") or "").strip()
        date = str(grade.get("date") or grade.get("enteredAt") or "").strip()
        if not subject_id or not value:
            return None
        return f"{student_id}_{subject_id}_{value}_{date}"
