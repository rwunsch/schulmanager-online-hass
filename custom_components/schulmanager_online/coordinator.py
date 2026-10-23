"""Data update coordinator for Schulmanager Online."""
from __future__ import annotations

import copy
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SchulmanagerAPI, SchulmanagerAPIError
from .const import DEFAULT_LOOKAHEAD_WEEKS, DOMAIN, UPDATE_INTERVAL
from .free_hours_utils import add_free_hours_to_schedule, parse_time_to_minutes, format_minutes_to_time
from .student_utils import get_api_for_student

_LOGGER = logging.getLogger(__name__)


def _now_local() -> datetime:
    """Current wall-clock time in Home Assistant's configured time zone.

    Uses ``dt_util.now()`` instead of ``datetime.now()`` so "today"/"current
    lesson" calculations follow HA's configured time zone rather than the
    host system's (which can differ, e.g. a container running in UTC). The
    tzinfo is stripped so it stays comparable with the naive datetimes parsed
    from the school's local date/time strings.
    """
    return dt_util.now().replace(tzinfo=None)


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
        self._last_successful_student_data: Dict[int, Dict[str, Any]] = {}
        self._initial_refresh_done = False
        self._seen_homework: set = set()
        self._seen_grades: set = set()
        
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

            if not self.students:
                stale_data = self._get_stale_data("No students loaded")
                if stale_data:
                    return stale_data
            
            # Get options
            weeks_ahead = self.options.get("lookahead_weeks", DEFAULT_LOOKAHEAD_WEEKS)
            include_homework = self.options.get("include_homework", True)
            include_grades = self.options.get("include_grades", False)
            include_exams = self.options.get("include_exams", True)
            
            # Calculate date range
            today = _now_local().date()
            start_date = today - timedelta(days=today.weekday())  # Monday of this week
            end_date = start_date + timedelta(weeks=weeks_ahead)
            
            data = {"students": {}, "last_update": _now_local().isoformat()}

            # Class hours (period-to-time grid) are institution-wide, not
            # per-student, so fetch each institution's grid at most once per
            # refresh cycle instead of once per student.
            class_hours_by_institution: Dict[Any, Any] = {}

            # Get data for each student
            for student in self.students:
                student_id = student.get("id")
                student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
                
                if not student_id:
                    continue
                
                try:
                    # Get the correct API instance for this student
                    student_api = get_api_for_student(student, self.api_instances)
                    
                    # Get schedule and class hours
                    schedule_data = await student_api.get_schedule(
                        student_id, start_date, end_date
                    )
                    
                    # Get class hours configuration (for free hour detection),
                    # cached per institution for the duration of this refresh
                    institution_id = student.get("_institution_id")
                    if institution_id in class_hours_by_institution:
                        class_hours_data = class_hours_by_institution[institution_id]
                    else:
                        try:
                            class_hours_data = await student_api.get_class_hours()
                        except Exception as e:
                            _LOGGER.warning(f"Failed to fetch class hours: {e}")
                            class_hours_data = []
                        class_hours_by_institution[institution_id] = class_hours_data
                    data["class_hours"] = class_hours_data
                    
                    # Process regular schedule data
                    processed_schedule = self._process_schedule_data(schedule_data)
                    
                    # Add free hours using centralized utility
                    processed_schedule = add_free_hours_to_schedule(
                        processed_schedule, data.get("class_hours", []), start_date, end_date
                    )
                    
                    student_data = self._build_student_data(student, processed_schedule, "loaded", "")

                    # Get homework if enabled
                    if include_homework:
                        try:
                            homework_data = await student_api.get_homework(student_id)
                            student_data["homework"] = homework_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get homework for %s: %s", student_name, e)
                            student_data["homework"] = self._get_previous_field(
                                student_id, "homework", {"homeworks": []}
                            )
                            self._mark_student_data_partial(student_data, f"homework: {e}")

                    # Get grades if enabled
                    if include_grades:
                        try:
                            grades_data = await student_api.get_grades(student_id)
                            student_data["grades"] = grades_data
                        except SchulmanagerAPIError as e:
                            _LOGGER.warning("Failed to get grades for %s: %s", student_name, e)
                            student_data["grades"] = self._get_previous_field(
                                student_id, "grades", {"grades": []}
                            )
                            self._mark_student_data_partial(student_data, f"grades: {e}")

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
                            student_data["exams"] = self._get_previous_field(
                                student_id, "exams", {"exams": [], "data": []}
                            )
                            self._mark_student_data_partial(student_data, f"exams: {e}")

                    data["students"][student_id] = student_data
                    self._last_successful_student_data[student_id] = copy.deepcopy(student_data)

                except SchulmanagerAPIError as e:
                    _LOGGER.error("Failed to get data for student %s: %s", student_name, e)
                    data["students"][student_id] = self._get_fallback_student_data(
                        student, f"schedule: {e}"
                    )
                except Exception as e:
                    _LOGGER.error("Unexpected error getting data for student %s: %s", student_name, e)
                    data["students"][student_id] = self._get_fallback_student_data(
                        student, f"unexpected: {e}"
                    )

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
                    await self._detect_and_fire_events(data)
                else:
                    # Seed seen sets but do not fire on initial load
                    self._seed_seen_sets(data)
                    self._initial_refresh_done = True
            except Exception as err:
                _LOGGER.debug("Event detection error: %s", err)

            self.previous_data = {
                student_id: {"schedule": student_data.get("schedule", [])}
                for student_id, student_data in data.get("students", {}).items()
            }

            return data

        except Exception as e:
            _LOGGER.error("Error communicating with API: %s", e)
            raise UpdateFailed(f"Error communicating with API: {e}") from e

    def _build_student_data(
        self,
        student: Dict[str, Any],
        processed_schedule: List[Dict[str, Any]],
        status: str,
        last_error: str,
    ) -> Dict[str, Any]:
        """Build a complete student data payload with stable keys."""
        student_id = student.get("id")
        return {
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
            "homework": {"homeworks": []},
            "grades": {"grades": []},
            "exams": {"exams": [], "data": []},
            "_data_status": status,
            "_last_error": last_error,
        }

    def _get_empty_student_data(
        self,
        student: Dict[str, Any],
        status: str = "not_loaded",
        last_error: str = "",
    ) -> Dict[str, Any]:
        """Return stable empty data for a student."""
        return self._build_student_data(student, [], status, last_error)

    def _get_fallback_student_data(
        self, student: Dict[str, Any], last_error: str
    ) -> Dict[str, Any]:
        """Return last successful student data, or stable empty defaults."""
        student_id = student.get("id")
        previous = self._last_successful_student_data.get(student_id)
        if previous:
            fallback = copy.deepcopy(previous)
            fallback["_data_status"] = "stale"
            fallback["_last_error"] = last_error
            return fallback

        return self._get_empty_student_data(student, "not_loaded", last_error)

    def _get_previous_field(self, student_id: int, field: str, default: Any) -> Any:
        """Return a previous field value or a defensive default."""
        previous = self._last_successful_student_data.get(student_id, {})
        if field in previous:
            return copy.deepcopy(previous[field])
        return copy.deepcopy(default)

    def _mark_student_data_partial(self, student_data: Dict[str, Any], error: str) -> None:
        """Mark otherwise loaded student data as partially stale."""
        student_data["_data_status"] = "partial"
        existing_error = student_data.get("_last_error", "")
        student_data["_last_error"] = "; ".join(filter(None, [existing_error, error]))

    def _get_stale_data(self, last_error: str) -> Optional[Dict[str, Any]]:
        """Return the current coordinator data as stale when startup lookups fail."""
        if not self.data or "students" not in self.data:
            return None

        data = copy.deepcopy(self.data)
        data["last_update"] = _now_local().isoformat()
        for student_data in data.get("students", {}).values():
            if isinstance(student_data, dict):
                student_data["_data_status"] = "stale"
                student_data["_last_error"] = last_error
        return data

    def _process_schedule_data(self, schedule_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and normalize schedule data."""
        if not isinstance(schedule_data, dict):
            return []

        lessons = schedule_data.get("lessons", [])
        if not isinstance(lessons, list):
            return []

        processed_lessons = []
        
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            processed_lesson = self._process_lesson(lesson)
            if processed_lesson:
                processed_lessons.append(processed_lesson)
        
        # Sort by date and time
        processed_lessons.sort(key=lambda x: (x.get("date") or "", x.get("start_time") or ""))
        
        # Post-process to assign correct hour numbers by date
        processed_lessons = self._assign_correct_hour_numbers(processed_lessons)
        
        return processed_lessons

    def _process_lesson(self, lesson: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single lesson."""
        try:
            if not isinstance(lesson, dict):
                return None

            # Extract actual lesson data (API structure: lesson.actualLesson contains the details)
            actual_lesson = lesson.get("actualLesson", {}) or {}
            event_data = lesson.get("event", {}) or {}
            class_hour = lesson.get("classHour", {}) or {}
            lesson_type = lesson.get("type", "regularLesson")
            if not isinstance(actual_lesson, dict):
                actual_lesson = {}
            if not isinstance(event_data, dict):
                event_data = {}
            if not isinstance(class_hour, dict):
                class_hour = {}
            
            # Extract basic information
            class_hour_num = class_hour.get("number")
            if class_hour_num:
                try:
                    class_hour_num = int(class_hour_num)
                except (ValueError, TypeError):
                    class_hour_num = None

            
            # Safely extract subject and room (handle None values)
            subject_data = actual_lesson.get("subject", {}) or {}
            room_data = actual_lesson.get("room", {}) or {}
            event_title = event_data.get("text", "") if lesson.get("type") == "event" else ""
            event_rooms = event_data.get("rooms", [])
            event_room = ""
            if isinstance(event_rooms, list) and event_rooms and isinstance(event_rooms[0], dict):
                event_room = event_rooms[0].get("name", "")
            lesson_teachers = event_data.get("teachers", []) if lesson.get("type") == "event" else actual_lesson.get("teachers", [])
            original_lesson = self._get_original_lesson_data(lesson, actual_lesson)
            original_subject_data = (
                original_lesson.get("subject") or lesson.get("originalSubject") or {}
            )
            original_room_data = (
                original_lesson.get("room") or lesson.get("originalRoom") or {}
            )
            original_subject = self._get_named_value(original_subject_data)
            original_room = self._get_named_value(original_room_data)
            is_cancelled = lesson_type == "cancelledLesson"
            display_subject = event_title or subject_data.get("name", "")
            
            processed = {
                "id": actual_lesson.get("lessonId", lesson.get("id")),
                "date": lesson.get("date"),
                "class_hour_number": class_hour_num,
                "start_time": class_hour.get("from"),
                "end_time": class_hour.get("until"),
                "subject": display_subject,
                "subject_name": display_subject,
                "subject_abbreviation": subject_data.get("abbreviation", ""),
                "room": event_room or room_data.get("name", ""),
                "teachers": lesson_teachers or [],
                "is_substitution": (
                    not is_cancelled
                    and (lesson_type == "substitution" or lesson.get("isSubstitution", False))
                ),
                "type": lesson_type,
                "comment": lesson.get("comment", ""),
            }

            if original_subject:
                processed["original_subject"] = original_subject
                processed["original_subject_abbreviation"] = self._get_abbreviation_value(
                    original_subject_data
                )

            if original_room:
                processed["original_room"] = original_room

            original_teachers = original_lesson.get("teachers") or lesson.get("originalTeachers")
            if not original_teachers and lesson.get("originalTeacher"):
                original_teachers = [lesson["originalTeacher"]]
            if original_teachers:
                processed["original_teachers"] = original_teachers

            original_comment = original_lesson.get("comment") or lesson.get("originalComment")
            if original_comment:
                processed["original_comment"] = original_comment
            
            # If class_hour_number or times are missing, calculate them
            processed = self._enhance_lesson_with_calculated_times(processed)
            
            # Handle teacher information
            teachers = processed["teachers"]
            if teachers and isinstance(teachers, list):
                # Extract teacher names and abbreviations
                teacher_info = self._format_teacher_info(teachers)
                processed["teachers"] = teacher_info
                
                # Add primary teacher info for easy access
                self._set_primary_teacher_fields(processed)
            
            # Handle original teacher for substitutions
            if processed["is_substitution"] and lesson.get("originalTeacher"):
                processed["original_teacher"] = lesson["originalTeacher"]
            
            return processed
            
        except Exception as e:
            _LOGGER.warning("Failed to process lesson: %s", e)
            import traceback
            _LOGGER.debug(traceback.format_exc())
            return None

    def _format_teacher_info(self, teachers: Any) -> List[Dict[str, Any]]:
        """Normalize teacher lists to the integration's attribute shape."""
        teacher_info = []
        if not isinstance(teachers, list):
            return teacher_info

        for teacher in teachers:
            if isinstance(teacher, dict):
                firstname = teacher.get("firstname", "")
                lastname = teacher.get("lastname", "")
                full_name = teacher.get("name") or f"{firstname} {lastname}".strip()
                abbrev = teacher.get("abbreviation", "")
                teacher_info.append({
                    "name": full_name,
                    "firstname": firstname,
                    "lastname": lastname,
                    "abbreviation": abbrev
                })

        return teacher_info

    def _set_primary_teacher_fields(self, lesson: Dict[str, Any]) -> None:
        """Set convenience fields from the first teacher."""
        teachers = lesson.get("teachers", [])
        if not teachers:
            return

        primary_teacher = teachers[0]
        lesson["teacher"] = primary_teacher.get("abbreviation", "")
        lesson["teacher_firstname"] = primary_teacher.get("firstname", "")
        lesson["teacher_lastname"] = primary_teacher.get("lastname", "")
        lesson["teacher_abbreviation"] = primary_teacher.get("abbreviation", "")

    def _get_named_value(self, value: Any) -> str:
        """Return the display name from API objects or plain strings."""
        if isinstance(value, dict):
            return value.get("name", "")
        if isinstance(value, str):
            return value
        return ""

    def _get_abbreviation_value(self, value: Any) -> str:
        """Return the abbreviation from API objects."""
        if isinstance(value, dict):
            return value.get("abbreviation", "")
        return ""

    def _get_original_lesson_data(
        self, lesson: Dict[str, Any], actual_lesson: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract original lesson details from known Schulmanager API shapes."""
        original_lessons = lesson.get("originalLessons")
        if isinstance(original_lessons, list) and original_lessons:
            first_lesson = original_lessons[0]
            if isinstance(first_lesson, dict):
                return first_lesson

        for key in ("originalLesson", "lesson"):
            candidate = lesson.get(key)
            if isinstance(candidate, dict) and candidate is not actual_lesson:
                return candidate

        return lesson

    def _get_next_lesson(self, lessons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the next upcoming lesson."""
        now = _now_local()
        
        for lesson in lessons:
            lesson_datetime = self._parse_lesson_datetime(lesson)
            if lesson_datetime and lesson_datetime > now:
                return lesson
        
        return None

    def _get_today_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get today's lessons."""
        today = _now_local().date().isoformat()
        
        return [lesson for lesson in lessons if lesson.get("date") == today]

    def _get_tomorrow_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get tomorrow's lessons (literal next calendar day)."""
        tomorrow = (_now_local().date() + timedelta(days=1)).isoformat()
        return [lesson for lesson in lessons if lesson.get("date") == tomorrow]

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
        now = _now_local()
        
        for lesson in lessons:
            lesson_start = self._parse_lesson_datetime(lesson)
            lesson_end = self._parse_lesson_end_datetime(lesson)
            
            if lesson_start and lesson_end and lesson_start <= now <= lesson_end:
                return lesson
        
        return None

    def _get_today_changes(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get today's lessons that have changes (substitutions, cancellations)."""
        today = _now_local().date().isoformat()
        changes = []
        
        for lesson in lessons:
            if (lesson.get("date") == today and
                (lesson.get("is_substitution") or 
                 lesson.get("type") in ["changedLesson", "cancelledLesson"])):
                changes.append(lesson)
        
        return changes

    def _get_this_week_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all lessons for this week (Monday to Friday)."""
        now = _now_local()
        # Get Monday of this week
        monday = now - timedelta(days=now.weekday())
        friday = monday + timedelta(days=4)
        
        monday_str = monday.date().isoformat()
        friday_str = friday.date().isoformat()
        
        week_lessons = []
        for lesson in lessons:
            lesson_date = lesson.get("date", "")
            if monday_str <= lesson_date <= friday_str:
                week_lessons.append(lesson)
        
        return week_lessons

    def _get_next_week_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all lessons for next week (Monday to Friday)."""
        now = _now_local()
        # Get Monday of next week
        next_monday = now + timedelta(days=(7 - now.weekday()))
        next_friday = next_monday + timedelta(days=4)
        
        monday_str = next_monday.date().isoformat()
        friday_str = next_friday.date().isoformat()
        
        week_lessons = []
        for lesson in lessons:
            lesson_date = lesson.get("date", "")
            if monday_str <= lesson_date <= friday_str:
                week_lessons.append(lesson)
        
        return week_lessons

    def _get_next_school_day_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get lessons for the next school day (skipping weekends)."""
        now = _now_local()
        current_date = now.date()
        
        # Find next school day (Monday-Friday)
        for days_ahead in range(1, 8):  # Check up to 7 days ahead
            check_date = current_date + timedelta(days=days_ahead)
            # Skip weekends (Saturday=5, Sunday=6)
            if check_date.weekday() < 5:
                date_str = check_date.isoformat()
                day_lessons = [lesson for lesson in lessons if lesson.get("date") == date_str]
                if day_lessons:  # Only return if there are actually lessons
                    return day_lessons
        
        return []

    def _detect_changes(self, student_id: int, current_schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect changes between previous and current schedule."""
        if student_id not in self.previous_data or "schedule" not in self.previous_data[student_id]:
            changes = self._detect_original_lesson_changes(current_schedule)
            return {
                "has_changes": len(changes) > 0,
                "changes": changes,
                "change_count": len(changes)
            }
        
        previous_schedule = self.previous_data[student_id]["schedule"]
        changes = []
        
        # Create lookup dictionaries for easier comparison
        previous_lookup = {}
        for lesson in previous_schedule:
            key = f"{lesson.get('date', '')}_{lesson.get('class_hour_number', '')}"
            previous_lookup[key] = lesson
        
        current_lookup = {}
        for lesson in current_schedule:
            key = f"{lesson.get('date', '')}_{lesson.get('class_hour_number', '')}"
            current_lookup[key] = lesson
        
        # Check for changes in existing lessons
        for key, current_lesson in current_lookup.items():
            # Cancellations and school events are explicit schedule entries, not
            # field edits to the original lesson. Their original values remain
            # available on the schedule item and are rendered as such.
            if current_lesson.get("type") in ("cancelledLesson", "event"):
                continue

            original_change = self._build_original_lesson_change(current_lesson)
            if original_change:
                changes.append(original_change)
                continue

            if key in previous_lookup:
                previous_lesson = previous_lookup[key]
                change = self._compare_lessons(previous_lesson, current_lesson)
                if change:
                    changes.append(change)
            else:
                # New lesson added
                changes.append({
                    "type": "added",
                    "date": current_lesson.get("date", ""),
                    "class_hour": current_lesson.get("class_hour_number", ""),
                    "current": current_lesson,
                    "previous": None,
                    "description": f"New lesson added: {current_lesson.get('subject', 'Unknown')}"
                })
        
        # Check for removed lessons
        for key, previous_lesson in previous_lookup.items():
            if key not in current_lookup:
                changes.append({
                    "type": "removed",
                    "date": previous_lesson.get("date", ""),
                    "class_hour": previous_lesson.get("class_hour_number", ""),
                    "current": None,
                    "previous": previous_lesson,
                    "description": f"Lesson removed: {previous_lesson.get('subject', 'Unknown')}"
                })
        
        return {
            "has_changes": len(changes) > 0,
            "changes": changes,
            "change_count": len(changes)
        }

    def _detect_original_lesson_changes(
        self, current_schedule: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect API-provided changes when no previous poll is available."""
        changes = []

        for current_lesson in current_schedule:
            change = self._build_original_lesson_change(current_lesson)
            if change:
                changes.append(change)

        return changes

    def _build_original_lesson_change(
        self, current: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Build a synthetic previous lesson from API original_* values."""
        if current.get("type") in ("cancelledLesson", "event"):
            return None

        if not self._has_original_lesson_values(current):
            return None

        previous = dict(current)

        if "original_subject" in current:
            previous["subject"] = current["original_subject"]
            previous["subject_name"] = current["original_subject"]
            previous["subject_abbreviation"] = current.get("original_subject_abbreviation", "")

        if "original_room" in current:
            previous["room"] = current["original_room"]

        if "original_teachers" in current:
            previous["teachers"] = self._format_teacher_info(current["original_teachers"])
            self._set_primary_teacher_fields(previous)

        if "original_comment" in current:
            previous["comment"] = current["original_comment"]

        change = self._compare_lessons(previous, current)
        if change:
            change["previous"] = previous
            change["description"] = (
                f"Changes in {current.get('subject', 'Unknown')}: "
                f"{', '.join([c['display_name'] for c in change['field_changes']])}"
            )

        return change

    def _has_original_lesson_values(self, lesson: Dict[str, Any]) -> bool:
        """Return true when the API exposed any before-value for the lesson."""
        return any(
            lesson.get(key) is not None
            for key in (
                "original_subject",
                "original_room",
                "original_teachers",
                "original_comment",
            )
        )

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
                "date": current.get("date", ""),
                "class_hour": current.get("class_hour_number", ""),
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

    async def _detect_and_fire_events(self, data: Dict[str, Any]) -> None:
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
