"""Calendar platform for Schulmanager Online."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SchulmanagerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("Europe/Berlin")

# Default class times (estimates based on typical German school schedules)
DEFAULT_CLASS_TIMES = {
    "1": ("08:00", "08:45"),
    "2": ("08:50", "09:35"),
    "3": ("09:55", "10:40"),
    "4": ("10:45", "11:30"),
    "5": ("11:40", "12:25"),
    "6": ("12:30", "13:15"),
    "7": ("13:20", "14:05"),
    "8": ("14:10", "14:55"),
    "9": ("15:00", "15:45"),
    "10": ("15:50", "16:35"),
    "11": ("16:40", "17:25"),
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schulmanager Online calendar entities."""
    coordinator: SchulmanagerDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    # Create calendar entities for each student
    students = coordinator.get_all_students()
    for student in students:
        student_id = student["id"]
        student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        
        # Create schedule calendar
        entities.append(
            SchulmanagerOnlineCalendar(
                coordinator=coordinator,
                student_id=student_id,
                student_name=student_name,
                calendar_type="schedule",
            )
        )
        
        # Create homework calendar if enabled
        if coordinator.options.get("include_homework", True):
            entities.append(
                SchulmanagerOnlineCalendar(
                    coordinator=coordinator,
                    student_id=student_id,
                    student_name=student_name,
                    calendar_type="homework",
                )
            )
        
        # Create exams calendar if enabled
        if coordinator.options.get("include_exams", True):
            entities.append(
                SchulmanagerOnlineCalendar(
                    coordinator=coordinator,
                    student_id=student_id,
                    student_name=student_name,
                    calendar_type="exams",
                )
            )
    
    async_add_entities(entities)

class SchulmanagerOnlineCalendar(CoordinatorEntity, CalendarEntity):
    """Representation of a Schulmanager Online calendar."""

    def __init__(
        self,
        coordinator: SchulmanagerDataUpdateCoordinator,
        student_id: int,
        student_name: str,
        calendar_type: str,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self.student_id = student_id
        self.student_name = student_name
        self.calendar_type = calendar_type
        
        # Create safe name for entity ID
        safe_name = student_name.lower().replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        
        # Set entity attributes
        calendar_names = {
            "schedule": "Lessons",
            "homework": "Homework", 
            "exams": "Exams"
        }
        
        self._attr_name = f"{calendar_names[calendar_type]} - {student_name}"
        self._attr_unique_id = f"schulmanager_{calendar_type}_{safe_name}"
        
        # Set icons
        icons = {
            "schedule": "mdi:school",
            "homework": "mdi:book-open-page-variant",
            "exams": "mdi:clipboard-text"
        }
        self._attr_icon = icons[calendar_type]

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, str(self.student_id))},
            "name": f"Schulmanager - {self.student_name}",
            "manufacturer": "Schulmanager Online",
            "model": "Student Schedule",
            "sw_version": "1.0.0",
        }

    @property
    def student_info(self) -> Dict[str, Any]:
        """Get student information."""
        student_data = self.coordinator.get_student_data(self.student_id)
        if student_data:
            return student_data.get("info", {})
        return {}

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event or current event."""
        try:
            now = datetime.now(TIMEZONE)
            
            # Look ahead 30 days to find the next event
            events = self._get_events(now, now + timedelta(days=30))
            
            if not events:
                return None
            
            # Find current event (happening now)
            for event in events:
                if event.start <= now <= event.end:
                    _LOGGER.debug(f"Current event found: {event.summary}")
                    return event
            
            # Find next upcoming event
            for event in events:
                if event.start > now:
                    _LOGGER.debug(f"Next event found: {event.summary}")
                    return event
            
            return None
            
        except Exception as e:
            _LOGGER.error(f"Error getting next event: {e}")
            return None

    @property
    def state(self) -> str:
        """Return the state of the calendar."""
        try:
            now = datetime.now(TIMEZONE)
            # Check for events in a small window around now
            events = self._get_events(now - timedelta(minutes=1), now + timedelta(minutes=1))
            
            # Check if any event is currently active
            for event in events:
                if event.start <= now <= event.end:
                    return "on"
            
            return "off"
            
        except Exception as e:
            _LOGGER.error(f"Error getting calendar state: {e}")
            return "off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = {
            "calendar_type": self.calendar_type,
            "student_name": self.student_name,
        }
        
        try:
            # Get the next or current event
            event = self.event
            if event:
                attributes.update({
                    "message": event.summary,
                    "description": event.description or "",
                    "start_time": event.start.isoformat(),
                    "end_time": event.end.isoformat(),
                    "all_day": getattr(event, 'all_day', False),
                    "location": getattr(event, 'location', ""),
                })
            else:
                # No events found
                attributes.update({
                    "message": "No upcoming events",
                    "description": "",
                    "start_time": None,
                    "end_time": None,
                    "all_day": False,
                    "location": "",
                })
        
        except Exception as e:
            _LOGGER.error(f"Error getting calendar attributes: {e}")
            attributes.update({
                "message": "Error loading events",
                "description": str(e),
                "start_time": None,
                "end_time": None,
                "all_day": False,
                "location": "",
            })
        
        return attributes

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        """Return calendar events within a datetime range."""
        try:
            return self._get_events(start_date, end_date)
            
        except Exception as e:
            _LOGGER.error(f"Error in async_get_events: {e}")
            return []

    def _get_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Get events for the specified date range."""
        try:
            student_data = self.coordinator.get_student_data(self.student_id)
            if not student_data:
                _LOGGER.debug(f"No student data available for student {self.student_id}")
                return []

            _LOGGER.debug(f"Getting {self.calendar_type} events for student {self.student_id} from {start_date} to {end_date}")
            
            events = []
            
            if self.calendar_type == "schedule":
                schedule_data = student_data.get("schedule", [])
                _LOGGER.debug(f"Found {len(schedule_data)} schedule items")
                events.extend(self._get_schedule_events(student_data, start_date, end_date))
            elif self.calendar_type == "homework":
                homework_data = student_data.get("homework", [])
                if isinstance(homework_data, dict):
                    homework_data = homework_data.get("homeworks", [])
                _LOGGER.debug(f"Found {len(homework_data)} homework items")
                events.extend(self._get_homework_events(student_data, start_date, end_date))
            elif self.calendar_type == "exams":
                exams_data = student_data.get("exams", {})
                if isinstance(exams_data, dict):
                    exam_list = exams_data.get("data", [])
                else:
                    exam_list = exams_data
                _LOGGER.debug(f"Found {len(exam_list)} exam items")
                events.extend(self._get_exam_events(student_data, start_date, end_date))
            
            # Sort events by start time
            events.sort(key=lambda x: x.start)
            
            _LOGGER.debug(f"Created {len(events)} calendar events for {self.calendar_type}")
            
            return events
            
        except Exception as e:
            _LOGGER.error(f"Error getting events: {e}")
            import traceback
            _LOGGER.error(traceback.format_exc())
            return []

    def _get_schedule_events(
        self, 
        student_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get schedule events."""
        events = []
        schedule = student_data.get("schedule", [])
        
        _LOGGER.debug(f"Processing {len(schedule)} schedule items for date range {start_date} to {end_date}")
        
        for i, lesson in enumerate(schedule):
            try:
                _LOGGER.debug(f"Processing lesson {i+1}: date={lesson.get('date')}, class_hour={lesson.get('classHour', {}).get('number')}")
                event = self._create_lesson_event(lesson)
                if event:
                    _LOGGER.debug(f"Created event: {event.summary} from {event.start} to {event.end}")
                    if self._event_in_range(event, start_date, end_date):
                        events.append(event)
                        _LOGGER.debug(f"Event added to calendar (in range)")
                    else:
                        _LOGGER.debug(f"Event not in range: event={event.start} to {event.end}, range={start_date} to {end_date}")
                else:
                    _LOGGER.debug(f"Failed to create event for lesson {i+1}")
            except Exception as e:
                _LOGGER.warning(f"Failed to create lesson event: {e}")
                import traceback
                _LOGGER.debug(traceback.format_exc())
                continue
        
        _LOGGER.debug(f"Created {len(events)} schedule events")
        return events

    def _get_homework_events(
        self, 
        student_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get homework events."""
        events = []
        homework_data = student_data.get("homework", [])
        
        _LOGGER.debug(f"Homework data type: {type(homework_data)}, content: {homework_data}")
        
        # Handle different data structures
        if isinstance(homework_data, dict):
            homeworks = homework_data.get("homeworks", [])
        else:
            homeworks = homework_data
        
        _LOGGER.debug(f"Processing {len(homeworks)} homework items for date range {start_date} to {end_date}")
        
        for i, homework in enumerate(homeworks):
            try:
                _LOGGER.debug(f"Processing homework {i+1}: date={homework.get('date')}")
                event = self._create_homework_event(homework)
                if event:
                    _LOGGER.debug(f"Created homework event: {event.summary} from {event.start} to {event.end}")
                    if self._event_in_range(event, start_date, end_date):
                        events.append(event)
                        _LOGGER.debug(f"Homework event added to calendar (in range)")
                    else:
                        _LOGGER.debug(f"Homework event not in range")
                else:
                    _LOGGER.debug(f"Failed to create homework event for item {i+1}")
            except Exception as e:
                _LOGGER.warning(f"Failed to create homework event: {e}")
                import traceback
                _LOGGER.debug(traceback.format_exc())
                continue
        
        _LOGGER.debug(f"Created {len(events)} homework events")
        return events

    def _get_exam_events(
        self, 
        student_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get exam events."""
        events = []
        exams_data = student_data.get("exams", {})
        
        # Handle different data structures
        if isinstance(exams_data, dict):
            exams = exams_data.get("data", [])
        else:
            exams = exams_data
        
        for exam in exams:
            try:
                event = self._create_exam_event(exam)
                if event and self._event_in_range(event, start_date, end_date):
                    events.append(event)
            except Exception as e:
                _LOGGER.warning(f"Failed to create exam event: {e}")
                continue
        
        return events

    def _event_in_range(self, event: CalendarEvent, start_date: datetime, end_date: datetime) -> bool:
        """Check if event is within the date range."""
        try:
            return event.start <= end_date and event.end >= start_date
        except Exception as e:
            _LOGGER.warning(f"Error checking event range: {e}")
            return False

    def _create_lesson_event(self, lesson: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Create a calendar event from a lesson (processed data structure)."""
        try:
            # Parse date - format is "2025-09-11"
            date_str = lesson.get("date")
            if not date_str:
                return None
            
            # Parse date
            lesson_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Get class hour number (from processed structure)
            class_hour_raw = lesson.get("class_hour_number")
            if class_hour_raw is None or class_hour_raw == "":
                # For lessons without hour number (like AGs), use actual times from lesson data
                start_time_str = lesson.get("start_time", "08:00:00")[:5]  # Extract HH:MM
                end_time_str = lesson.get("end_time", "08:45:00")[:5]      # Extract HH:MM
            else:
                class_hour_number = str(class_hour_raw)
                start_time_str, end_time_str = self._get_configurable_class_times(class_hour_number)
            
            # Create datetime objects
            start_datetime = datetime.combine(
                lesson_date, 
                datetime.strptime(start_time_str, "%H:%M").time()
            ).replace(tzinfo=TIMEZONE)
            
            end_datetime = datetime.combine(
                lesson_date, 
                datetime.strptime(end_time_str, "%H:%M").time()
            ).replace(tzinfo=TIMEZONE)
            
            # Get subject information (from processed structure)
            subject = lesson.get("subject", lesson.get("subject_name", "Lesson"))
            
            # Get room information (from processed structure)
            room = lesson.get("room", "")
            
            # Check lesson type
            lesson_type = lesson.get("type", "regularLesson")
            is_substitution = lesson.get("is_substitution", False)
            
            # Create title
            if lesson_type == "cancelledLesson":
                title = f"❌ {subject} (Cancelled)"
            elif lesson_type == "substitution" or is_substitution:
                title = f"🔄 {subject}"
            else:
                title = subject
            
            if room:
                title += f" ({room})"
            
            # Create description
            description_parts = []
            description_parts.append(f"Subject: {subject}")
            description_parts.append(f"Class Hour: {class_hour_number}")
            
            if room:
                description_parts.append(f"Room: {room}")
            
            # Add teacher information (from processed structure)
            teachers = lesson.get("teachers", [])
            if teachers:
                if isinstance(teachers, list):
                    # Handle list of teacher objects
                    teacher_names = []
                    for teacher in teachers:
                        if isinstance(teacher, dict):
                            name = teacher.get("name", teacher.get("abbreviation", ""))
                            if name:
                                teacher_names.append(name)
                        elif isinstance(teacher, str):
                            teacher_names.append(teacher)
                    if teacher_names:
                        description_parts.append(f"Teacher: {', '.join(teacher_names)}")
                elif isinstance(teachers, str):
                    description_parts.append(f"Teacher: {teachers}")
            
            # Add lesson type info
            if lesson_type != "regularLesson":
                description_parts.append(f"Type: {lesson_type}")
            
            # Add comment if available
            comment = lesson.get("comment", "")
            if comment:
                description_parts.append(f"Comment: {comment}")
            
            description = "\n".join(description_parts)
            
            return CalendarEvent(
                start=start_datetime,
                end=end_datetime,
                summary=title,
                description=description,
            )
            
        except Exception as e:
            _LOGGER.warning(f"Failed to create lesson event: {e}")
            import traceback
            _LOGGER.debug(traceback.format_exc())
            return None

    def _create_homework_event(self, homework: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Create a calendar event from homework."""
        try:
            # Parse date - API format is "date": "2025-08-28"
            date_str = homework.get("date")
            if not date_str:
                return None
            
            # Parse date
            hw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Set event time (homework due at 6 PM)
            start_datetime = datetime.combine(
                hw_date, 
                time(18, 0)
            ).replace(tzinfo=TIMEZONE)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Extract homework details from nested structure
            homework_details = homework.get("homework", {})
            
            # Get subject information
            subject_info = homework_details.get("subject", {})
            if isinstance(subject_info, dict):
                subject = subject_info.get("name", subject_info.get("abbreviation", "Homework"))
            else:
                subject = str(subject_info) if subject_info else "Homework"
            
            # Get homework title/task
            hw_title = homework_details.get("title", homework_details.get("task", ""))
            
            # Create event title
            title = f"📝 {subject}"
            if hw_title:
                title += f" - {hw_title}"
            else:
                title += " - Homework Due"
            
            # Create description
            description_parts = []
            
            # Homework task/title
            if hw_title:
                description_parts.append(f"Task: {hw_title}")
            
            # Subject
            description_parts.append(f"Subject: {subject}")
            
            # Date assigned
            description_parts.append(f"Due Date: {date_str}")
            
            description = "\n".join(description_parts)
            
            return CalendarEvent(
                start=start_datetime,
                end=end_datetime,
                summary=title,
                description=description,
            )
            
        except Exception as e:
            _LOGGER.warning(f"Failed to create homework event: {e}")
            return None

    def _create_exam_event(self, exam: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Create a calendar event from an exam."""
        try:
            # Parse exam date
            date_str = exam.get("date")
            if not date_str:
                return None
            
            # Parse date
            exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Get time from startClassHour
            start_class_hour = exam.get("startClassHour", {})
            if isinstance(start_class_hour, dict) and start_class_hour.get("from"):
                time_from = start_class_hour.get("from", "08:00:00")
                time_until = start_class_hour.get("until", "09:00:00")
                
                # Parse time (format: "11:41:00")
                start_time = datetime.strptime(time_from[:5], "%H:%M").time()
                end_time = datetime.strptime(time_until[:5], "%H:%M").time()
                
                start_datetime = datetime.combine(exam_date, start_time).replace(tzinfo=TIMEZONE)
                end_datetime = datetime.combine(exam_date, end_time).replace(tzinfo=TIMEZONE)
            else:
                # Default to 2-hour exam starting at 8 AM
                start_datetime = datetime.combine(exam_date, time(8, 0)).replace(tzinfo=TIMEZONE)
                end_datetime = start_datetime + timedelta(hours=2)
            
            # Create event title
            subject = exam.get("subject", {})
            if isinstance(subject, dict):
                subject_name = subject.get("name", "Unknown Subject")
            else:
                subject_name = str(subject)
            
            exam_type = exam.get("type", {})
            if isinstance(exam_type, dict):
                type_name = exam_type.get("name", "Exam")
            else:
                type_name = str(exam_type)
            
            title = f"📝 {subject_name} - {type_name}"
            
            # Create description
            description_parts = []
            description_parts.append(f"Subject: {subject_name}")
            description_parts.append(f"Type: {type_name}")
            
            # Add class hour info
            class_hour = exam.get("classHour", {})
            if class_hour:
                class_hour_number = class_hour.get("number")
                if class_hour_number:
                    description_parts.append(f"Class Hour: {class_hour_number}")
            
            # Add color
            color = exam.get("color")
            if color:
                description_parts.append(f"Color: {color}")
            
            description = "\n".join(description_parts)
            
            return CalendarEvent(
                start=start_datetime,
                end=end_datetime,
                summary=title,
                description=description,
            )
            
        except Exception as e:
            _LOGGER.warning(f"Failed to create exam event: {e}")
            return None

    def _get_configurable_class_times(self, class_hour_number: str) -> tuple[str, str]:
        """Get configurable class times based on hour number and schedule configuration."""
        try:
            student_data = self.coordinator.get_student_data(self.student_id)
            if not student_data or "schedule_config" not in student_data:
                # Fallback to default times
                return DEFAULT_CLASS_TIMES.get(class_hour_number, ("08:00", "08:45"))
            
            config = student_data["schedule_config"]
            try:
                hour = int(class_hour_number)
                if hour < 1 or hour > 10:  # Invalid hour number
                    raise ValueError(f"Invalid hour number: {hour}")
            except (ValueError, TypeError):
                # Fallback to default times for invalid hour numbers
                return DEFAULT_CLASS_TIMES.get(class_hour_number, ("08:00", "08:45"))
            
            # Calculate start time based on configuration
            start_minutes = self._parse_time_to_minutes(config.get("school_start_time", "08:00"))
            lesson_duration = config.get("lesson_duration_minutes", 45)
            short_break = config.get("short_break_minutes", 5)
            long_break_1 = config.get("long_break_1_minutes", 20)
            long_break_2 = config.get("long_break_2_minutes", 10)
            lunch_break = config.get("lunch_break_minutes", 45)
            
            # Calculate accumulated time for each hour
            for h in range(1, hour):
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
            
        except Exception as e:
            _LOGGER.debug(f"Error calculating configurable class times: {e}")
            # Fallback to default times
            return DEFAULT_CLASS_TIMES.get(class_hour_number, ("08:00", "08:45"))

    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except Exception:
            return 8 * 60  # Default to 8:00 AM

    def _format_minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to time string (HH:MM)."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"