"""Sensor platform for Schulmanager Online."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CLASS_NAME,
    ATTR_STUDENT_ID,
    ATTR_STUDENT_NAME,
    DOMAIN,
    ICON_ALERT_CIRCLE,
    ICON_BOOK,
    ICON_CALENDAR,
    ICON_CALENDAR_TODAY,
    ICON_CALENDAR_WEEK,
    ICON_CLOCK,
    ICON_CLOCK_ALERT,
    ICON_HOMEWORK,
    ICON_HOMEWORK_DUE,
    ICON_HOMEWORK_OVERDUE,
    ICON_HOMEWORK_UPCOMING,
    ICON_EXAM,
    ICON_EXAM_TODAY,
    ICON_EXAM_UPCOMING,
    ICON_EXAM_WEEK,
    ICON_PLAY_CIRCLE,
    ICON_SCHOOL,
    ICON_SWAP_HORIZONTAL,
    SENSOR_CHANGES_DETECTED,
    SENSOR_CURRENT_LESSON,
    SENSOR_HOMEWORK_DUE_TODAY,
    SENSOR_HOMEWORK_DUE_TOMORROW,
    SENSOR_HOMEWORK_OVERDUE,
    SENSOR_HOMEWORK_UPCOMING,
    SENSOR_EXAMS_TODAY,
    SENSOR_EXAMS_THIS_WEEK,
    SENSOR_EXAMS_NEXT_WEEK,
    SENSOR_EXAMS_UPCOMING,
    SENSOR_NEXT_LESSON,
    SENSOR_NEXT_WEEK,
    SENSOR_THIS_WEEK,
    SENSOR_TODAY_CHANGES,
    SENSOR_TODAY_LESSONS,
    SENSOR_TOMORROW_LESSONS,
    SENSOR_NEXT_SCHOOL_DAY,
)
from .coordinator import SchulmanagerDataUpdateCoordinator
from . import schedule_sensors
from . import homework_sensors
from . import exam_sensors

_LOGGER = logging.getLogger(__name__)


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key=SENSOR_CURRENT_LESSON,
        name="Current Lesson",
        icon=ICON_PLAY_CIRCLE,
    ),
    SensorEntityDescription(
        key=SENSOR_NEXT_LESSON,
        name="Next Lesson",
        icon=ICON_CLOCK,
    ),
    SensorEntityDescription(
        key=SENSOR_TODAY_LESSONS,
        name="Lessons Today",
        icon=ICON_CALENDAR_TODAY,
    ),
    SensorEntityDescription(
        key=SENSOR_TODAY_CHANGES,
        name="Changes Today",
        icon=ICON_CLOCK_ALERT,
    ),
    SensorEntityDescription(
        key=SENSOR_TOMORROW_LESSONS,
        name="Lessons Tomorrow",
        icon=ICON_CALENDAR,
    ),
    SensorEntityDescription(
        key=SENSOR_NEXT_SCHOOL_DAY,
        name="Lessons Next School Day",
        icon=ICON_CALENDAR,
    ),
    SensorEntityDescription(
        key=SENSOR_THIS_WEEK,
        name="Lessons This Week",
        icon=ICON_CALENDAR_WEEK,
    ),
    SensorEntityDescription(
        key=SENSOR_NEXT_WEEK,
        name="Lessons Next Week",
        icon=ICON_CALENDAR_WEEK,
    ),
    SensorEntityDescription(
        key=SENSOR_CHANGES_DETECTED,
        name="Changes Detected",
        icon=ICON_SWAP_HORIZONTAL,
    ),
]

HOMEWORK_SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key=SENSOR_HOMEWORK_DUE_TODAY,
        name="Homework Due Today",
        icon=ICON_HOMEWORK_DUE,
    ),
    SensorEntityDescription(
        key=SENSOR_HOMEWORK_DUE_TOMORROW,
        name="Homework Due Tomorrow",
        icon=ICON_HOMEWORK_UPCOMING,
    ),
    SensorEntityDescription(
        key=SENSOR_HOMEWORK_OVERDUE,
        name="Homework Overdue",
        icon=ICON_HOMEWORK_OVERDUE,
    ),
    SensorEntityDescription(
        key=SENSOR_HOMEWORK_UPCOMING,
        name="Homework Upcoming",
        icon=ICON_HOMEWORK,
    ),
]

EXAM_SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key=SENSOR_EXAMS_TODAY,
        name="Exams Today",
        icon=ICON_EXAM_TODAY,
    ),
    SensorEntityDescription(
        key=SENSOR_EXAMS_THIS_WEEK,
        name="Exams This Week",
        icon=ICON_EXAM_WEEK,
    ),
    SensorEntityDescription(
        key=SENSOR_EXAMS_NEXT_WEEK,
        name="Exams Next Week",
        icon=ICON_EXAM_WEEK,
    ),
    SensorEntityDescription(
        key=SENSOR_EXAMS_UPCOMING,
        name="Exams Upcoming",
        icon=ICON_EXAM_UPCOMING,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    students = hass.data[DOMAIN][config_entry.entry_id]["students"]
    
    entities = []
    
    # Create sensors for each student
    for student in students:
        student_id = student.get("id")
        if not student_id:
            continue
            
        # Schedule sensors
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                SchulmanagerOnlineSensor(
                    coordinator=coordinator,
                    description=description,
                    student_id=student_id,
                    student_info=student,
                )
            )
        
        # Homework sensors (if enabled)
        if config_entry.options.get("include_homework", True):
            for description in HOMEWORK_SENSOR_DESCRIPTIONS:
                entities.append(
                    SchulmanagerOnlineSensor(
                        coordinator=coordinator,
                        description=description,
                        student_id=student_id,
                        student_info=student,
                    )
                )
        
        # Exam sensors (if enabled)
        if config_entry.options.get("include_exams", True):
            for description in EXAM_SENSOR_DESCRIPTIONS:
                entities.append(
                    SchulmanagerOnlineSensor(
                        coordinator=coordinator,
                        description=description,
                        student_id=student_id,
                        student_info=student,
                    )
                )
    
    async_add_entities(entities)


class SchulmanagerOnlineSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Schulmanager Online sensor."""

    def __init__(
        self,
        coordinator: SchulmanagerDataUpdateCoordinator,
        description: SensorEntityDescription,
        student_id: int,
        student_info: Dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.entity_description = description
        self.student_id = student_id
        self.student_info = student_info
        
        # Generate entity ID (reversed format: sensor_type_student_name)
        student_name = f"{student_info.get('firstname', '')} {student_info.get('lastname', '')}"
        safe_name = student_name.lower().replace(" ", "_").replace("-", "_")
        
        self._attr_unique_id = f"schulmanager_{description.key}_{safe_name}"
        self._attr_name = f"{description.name} - {student_name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        student_name = f"{self.student_info.get('firstname', '')} {self.student_info.get('lastname', '')}"
        
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.student_id))},
            name=f"Schulmanager - {student_name}",
            manufacturer="Schulmanager Online",
            model="Student Schedule",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        student_data = self.coordinator.get_student_data(self.student_id)
        if not student_data:
            return None

        # Schedule sensors
        if self.entity_description.key == SENSOR_CURRENT_LESSON:
            return schedule_sensors.get_current_lesson_state(student_data)
        elif self.entity_description.key == SENSOR_NEXT_LESSON:
            return schedule_sensors.get_next_lesson_state(student_data)
        elif self.entity_description.key == SENSOR_TODAY_LESSONS:
            return schedule_sensors.get_today_lessons_count(student_data)
        elif self.entity_description.key == SENSOR_TODAY_CHANGES:
            return schedule_sensors.get_today_changes_count(student_data)
        elif self.entity_description.key == SENSOR_TOMORROW_LESSONS:
            return schedule_sensors.get_tomorrow_lessons_count(student_data)
        elif self.entity_description.key == SENSOR_NEXT_SCHOOL_DAY:
            return schedule_sensors.get_next_school_day_lessons_count(student_data)
        elif self.entity_description.key == SENSOR_THIS_WEEK:
            return schedule_sensors.get_this_week_summary(student_data)
        elif self.entity_description.key == SENSOR_NEXT_WEEK:
            return schedule_sensors.get_next_week_summary(student_data)
        elif self.entity_description.key == SENSOR_CHANGES_DETECTED:
            return schedule_sensors.get_changes_detected_state(student_data)
        
        # Homework sensors
        elif self.entity_description.key == SENSOR_HOMEWORK_DUE_TODAY:
            return homework_sensors.get_homework_due_today_count(student_data)
        elif self.entity_description.key == SENSOR_HOMEWORK_DUE_TOMORROW:
            return homework_sensors.get_homework_due_tomorrow_count(student_data)
        elif self.entity_description.key == SENSOR_HOMEWORK_OVERDUE:
            return homework_sensors.get_homework_overdue_count(student_data)
        elif self.entity_description.key == SENSOR_HOMEWORK_UPCOMING:
            return homework_sensors.get_homework_upcoming_count(student_data)
        
        # Exam sensors
        elif self.entity_description.key == SENSOR_EXAMS_TODAY:
            return exam_sensors.get_exams_today_count(student_data)
        elif self.entity_description.key == SENSOR_EXAMS_THIS_WEEK:
            return exam_sensors.get_exams_this_week_count(student_data)
        elif self.entity_description.key == SENSOR_EXAMS_NEXT_WEEK:
            return exam_sensors.get_exams_next_week_count(student_data)
        elif self.entity_description.key == SENSOR_EXAMS_UPCOMING:
            return exam_sensors.get_exams_upcoming_count(student_data)
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        student_data = self.coordinator.get_student_data(self.student_id)
        if not student_data:
            return {}

        attributes = {
            ATTR_STUDENT_ID: self.student_id,
            ATTR_STUDENT_NAME: f"{self.student_info.get('firstname', '')} {self.student_info.get('lastname', '')}",
        }

        # Add schedule configuration for all sensors
        if "schedule_config" in student_data:
            attributes["schedule_config"] = student_data["schedule_config"]

        # Add student class info
        if "info" in student_data:
            student_info = student_data["info"]
            attributes[ATTR_CLASS_NAME] = student_info.get("classId", "")

        # Schedule sensors
        if self.entity_description.key == SENSOR_CURRENT_LESSON:
            attributes.update(schedule_sensors.get_current_lesson_attributes(student_data))
        elif self.entity_description.key == SENSOR_NEXT_LESSON:
            attributes.update(schedule_sensors.get_next_lesson_attributes(student_data))
        elif self.entity_description.key == SENSOR_TODAY_LESSONS:
            attributes.update(schedule_sensors.get_today_lessons_attributes(student_data))
        elif self.entity_description.key == SENSOR_TODAY_CHANGES:
            attributes.update(schedule_sensors.get_today_changes_attributes(student_data))
        elif self.entity_description.key == SENSOR_TOMORROW_LESSONS:
            attributes.update(schedule_sensors.get_tomorrow_lessons_attributes(student_data))
        elif self.entity_description.key == SENSOR_NEXT_SCHOOL_DAY:
            attributes.update(schedule_sensors.get_next_school_day_lessons_attributes(student_data))
        elif self.entity_description.key == SENSOR_THIS_WEEK:
            attributes.update(schedule_sensors.get_this_week_attributes(student_data))
        elif self.entity_description.key == SENSOR_NEXT_WEEK:
            attributes.update(schedule_sensors.get_next_week_attributes(student_data))
        elif self.entity_description.key == SENSOR_CHANGES_DETECTED:
            attributes.update(schedule_sensors.get_changes_detected_attributes(student_data))
        
        # Homework sensors
        elif self.entity_description.key == SENSOR_HOMEWORK_DUE_TODAY:
            attributes.update(homework_sensors.get_homework_due_today_attributes(student_data))
        elif self.entity_description.key == SENSOR_HOMEWORK_DUE_TOMORROW:
            attributes.update(homework_sensors.get_homework_due_tomorrow_attributes(student_data))
        elif self.entity_description.key == SENSOR_HOMEWORK_OVERDUE:
            attributes.update(homework_sensors.get_homework_overdue_attributes(student_data))
        elif self.entity_description.key == SENSOR_HOMEWORK_UPCOMING:
            attributes.update(homework_sensors.get_homework_upcoming_attributes(student_data))
        
        # Exam sensors
        elif self.entity_description.key == SENSOR_EXAMS_TODAY:
            attributes.update(exam_sensors.get_exams_today_attributes(student_data))
        elif self.entity_description.key == SENSOR_EXAMS_THIS_WEEK:
            attributes.update(exam_sensors.get_exams_this_week_attributes(student_data))
        elif self.entity_description.key == SENSOR_EXAMS_NEXT_WEEK:
            attributes.update(exam_sensors.get_exams_next_week_attributes(student_data))
        elif self.entity_description.key == SENSOR_EXAMS_UPCOMING:
            attributes.update(exam_sensors.get_exams_upcoming_attributes(student_data))

        return attributes
