# Sensors - Detailed Documentation

## 🎯 Overview

The Schulmanager Online integration provides **16 different sensor entities** that cover various aspects of the schedule and school activities. Each sensor is automatically created for every configured student:

- **8 Schedule Sensors** - Current lessons, substitutions, weekly schedules
- **4 Homework Sensors** - Due and upcoming homework assignments
- **4 Exam Sensors** - Upcoming tests and exams

## 🔧 Consistent Data Formatting (Refactoring 2025)

**Important Change**: All sensors now use a unified data format for lesson attributes:

### Unified Subject Handling
- **`subject`**: Full subject name (e.g., "Evangelische Religionslehre (konfessionell kooperativ)")
- **`subject_abbreviation`**: Abbreviation (e.g., "EN")
- **`subject_sanitized`**: Clean subject name without parentheses and commas (e.g., "Evangelische Religionslehre")

### Standardized Lesson Attributes
All lesson sensors now use the same attribute format:
```json
{
  "subject": "Full subject name",
  "subject_abbreviation": "Abbreviation",
  "subject_sanitized": "Clean subject name",
  "time": "08:00-08:45",
  "room": "Room designation",
  "teacher": "Teacher abbreviation",
  "teacher_lastname": "Last name",
  "teacher_firstname": "First name",
  "is_substitution": false,
  "type": "regularLesson",
  "comment": "",
  "date": "2025-09-16",
  "class_hour": "Class hour number"
}
```

**Fixed Inconsistencies**:
- All sensors now use the full subject name in the `subject` field
- Unified time formatting as "HH:MM-HH:MM"
- Consistent teacher information with full name and abbreviation
- Reduced code duplication through shared formatting functions

## 📊 Sensor Overview

### Schedule Sensors
| Sensor | Entity ID | Icon | Update Interval | Description |
|--------|-----------|------|-----------------|-------------|
| **Current Lesson** | `sensor.{student}_current_lesson` | `mdi:school` | 5 minutes | Current class period |
| **Next Lesson** | `sensor.{student}_next_lesson` | `mdi:clock-outline` | 5 minutes | Next class period |
| **Today's Lessons** | `sensor.{student}_todays_lessons` | `mdi:calendar-today` | 15 minutes | All today's lessons |
| **Today's Changes** | `sensor.{student}_todays_changes` | `mdi:swap-horizontal` | 15 minutes | Today's substitutions |
| **Next School Day** | `sensor.{student}_next_school_day` | `mdi:calendar-arrow-right` | 15 minutes | Next school day |
| **This Week** | `sensor.{student}_this_week` | `mdi:calendar-week` | 1 hour | Schedule for this week |
| **Next Week** | `sensor.{student}_next_week` | `mdi:calendar-week-begin` | 1 hour | Schedule for next week |
| **Changes Detected** | `sensor.{student}_changes_detected` | `mdi:alert-circle` | On change | Detected changes |

### Homework Sensors
| Sensor | Entity ID | Icon | Update Interval | Description |
|--------|-----------|------|-----------------|-------------|
| **Homework Due Today** | `sensor.{student}_homework_due_today` | `mdi:alarm-check` | 15 minutes | Homework due today |
| **Homework Due Tomorrow** | `sensor.{student}_homework_due_tomorrow` | `mdi:calendar-arrow-right` | 15 minutes | Homework due tomorrow |
| **Homework Overdue** | `sensor.{student}_homework_overdue` | `mdi:alarm-snooze` | 15 minutes | Overdue homework |
| **Homework Upcoming** | `sensor.{student}_homework_upcoming` | `mdi:notebook-edit-outline` | 15 minutes | Upcoming homework |

### Exam Sensors
| Sensor | Entity ID | Icon | Update Interval | Description |
|--------|-----------|------|-----------------|-------------|
| **Exams Today** | `sensor.{student}_exams_today` | `mdi:clipboard-alert` | 15 minutes | Exams today |
| **Exams This Week** | `sensor.{student}_exams_this_week` | `mdi:calendar-week-begin` | 1 hour | Exams this week |
| **Exams Next Week** | `sensor.{student}_exams_next_week` | `mdi:calendar-week-begin` | 1 hour | Exams next week |
| **Exams Upcoming** | `sensor.{student}_exams_upcoming` | `mdi:clipboard-clock` | 1 hour | Upcoming exams |

## 🔍 Sensor Details

### 1. Current Lesson Sensor

**Entity ID**: `sensor.{student_name}_current_lesson`

**Purpose**: Shows the currently running class period.

**State Values**:
- `"Mathematics"` - Name of current subject
- `"Break"` - When it's break time
- `"No Class"` - Outside school hours
- `"Unknown"` - On data errors

**Attributes**:
```json
{
  "subject": "Mathematics",
  "teacher": "Mr. Schmidt",
  "room": "R204",
  "start_time": "09:45",
  "end_time": "10:30",
  "class_hour": "3",
  "is_substitution": false,
  "substitution_info": null,
  "student_name": "Marc Cedric Wunsch"
}
```

**Implementation**:
```python
def _get_current_lesson(self):
    """Get the current lesson."""
    now = datetime.now()
    current_date = now.date().isoformat()
    current_time = now.time()
    
    schedule = self._get_schedule_for_date(current_date)
    
    for lesson in schedule:
        start_time = datetime.strptime(lesson["classHour"]["startTime"], "%H:%M").time()
        end_time = datetime.strptime(lesson["classHour"]["endTime"], "%H:%M").time()
        
        if start_time <= current_time <= end_time:
            return lesson["lesson"]["subject"]
    
    return "No Class"
```

### 2. Next Lesson Sensor

**Entity ID**: `sensor.{student_name}_next_lesson`

**Purpose**: Shows the next upcoming class period.

**State Values**:
- `"German (in 15 min)"` - Next subject with time indication
- `"Tomorrow: English (08:00)"` - Next day
- `"No more classes today"` - End of school day

**Attributes**:
```json
{
  "subject": "German",
  "teacher": "Mrs. Müller",
  "room": "R105",
  "start_time": "10:45",
  "end_time": "11:30",
  "minutes_until": 15,
  "is_today": true,
  "date": "2025-09-14",
  "is_substitution": false
}
```

### 3. Today's Lessons Sensor

**Entity ID**: `sensor.{student_name}_todays_lessons`

**Purpose**: Overview of all lessons for the current day.

**State Values**:
- `"6"` - Number of lessons today
- `"0"` - No classes today (weekend/holiday)

**Attributes**:
```json
{
  "lessons": [
    {
      "subject": "Evangelische Religionslehre (konfessionell kooperativ)",
      "subject_abbreviation": "EN",
      "subject_sanitized": "Evangelische Religionslehre",
      "time": "08:00-08:45",
      "room": "RD208",
      "teacher": "SliJ",
      "teacher_lastname": "Schlipp",
      "teacher_firstname": "Julia-Felicitas",
      "is_substitution": false,
      "type": "regularLesson",
      "comment": "",
      "date": "2025-09-16",
      "class_hour": "1"
    },
    {
      "subject": "Mathematics",
      "subject_abbreviation": "M",
      "subject_sanitized": "Mathematics",
      "time": "08:50-09:35",
      "room": "R204",
      "teacher": "Sch",
      "teacher_lastname": "Schmidt",
      "teacher_firstname": "Hans",
      "is_substitution": true,
      "type": "changedLesson",
      "comment": "Substitution",
      "date": "2025-09-16",
      "class_hour": "2"
    }
  ],
  "count": 6
}
```

### 4. Today's Changes Sensor

**Entity ID**: `sensor.{student_name}_todays_changes`

**Purpose**: Shows all substitutions and changes for the current day.

**State Values**:
- `"2"` - Number of substitutions today
- `"0"` - No substitutions

**Attributes**:
```json
{
  "changes": [
    {
      "subject": "Evangelische Religionslehre (konfessionell kooperativ)",
      "subject_abbreviation": "EN",
      "subject_sanitized": "Evangelische Religionslehre",
      "time": "08:00-08:45",
      "room": "RD208",
      "teacher": "SliJ",
      "teacher_lastname": "Schlipp",
      "teacher_firstname": "Julia-Felicitas",
      "is_substitution": true,
      "type": "changedLesson",
      "comment": "Substitution for Mrs. Weber",
      "date": "2025-09-16",
      "class_hour": "1",
      "original_teacher": "Web"
    },
    {
      "subject": "Physical Education",
      "subject_abbreviation": "PE",
      "subject_sanitized": "Physical Education",
      "time": "13:15-14:00",
      "room": "",
      "teacher": "",
      "teacher_lastname": "",
      "teacher_firstname": "",
      "is_substitution": false,
      "type": "cancelledLesson",
      "comment": "Cancelled due to gym renovation",
      "date": "2025-09-16",
      "class_hour": "6"
    }
  ],
  "count": 2
}
```

### 5. Next School Day Sensor

**Entity ID**: `sensor.{student_name}_next_school_day`

**Purpose**: Information about the next school day (skips weekends).

**State Values**:
- `"Monday, 16.09.2025"` - Next school day
- `"Today"` - If there are still classes today

**Attributes**:
```json
{
  "date": "2025-09-16",
  "day_name": "Monday",
  "days_until": 2,
  "first_lesson": {
    "subject": "Mathematics",
    "teacher": "Mr. Schmidt",
    "start_time": "08:00",
    "room": "R204"
  },
  "total_lessons": 7,
  "has_changes": true,
  "changes_count": 1
}
```

### 6. This Week Sensor

**Entity ID**: `sensor.{student_name}_this_week`

**Purpose**: Complete schedule for the current week.

**State Values**:
- `"32"` - Total number of lessons this week
- `"0"` - No lessons (holidays)

**Attributes**:
```json
{
  "week_start": "2025-09-14",
  "week_end": "2025-09-20",
  "calendar_week": 38,
  "school_days": [
    {
      "date": "2025-09-14",
      "day_name": "Monday",
      "lessons_count": 6,
      "has_changes": false
    },
    {
      "date": "2025-09-15",
      "day_name": "Tuesday", 
      "lessons_count": 7,
      "has_changes": true
    }
  ],
  "total_lessons": 32,
  "total_changes": 3,
  "subjects_summary": {
    "Mathematics": 5,
    "German": 4,
    "English": 3,
    "History": 2
  }
}
```

### 7. Next Week Sensor

**Entity ID**: `sensor.{student_name}_next_week`

**Purpose**: Schedule preview for the upcoming week.

**State Values**:
- `"35"` - Number of lessons next week
- `"Holidays"` - When on vacation

**Attributes**: Similar to "This Week", but for the following week.

### 8. Changes Detected Sensor

**Entity ID**: `sensor.{student_name}_changes_detected`

**Purpose**: Detects schedule changes and notifies about them.

**State Values**:
- `"New Changes"` - When changes are detected
- `"No Changes"` - Everything unchanged
- `"Initially Loaded"` - On first load

**Attributes**:
```json
{
  "last_check": "2025-09-14T10:30:00",
  "changes_detected_at": "2025-09-14T10:15:00",
  "changes": [
    {
      "type": "substitution_added",
      "date": "2025-09-15",
      "class_hour": "3",
      "subject": "Mathematics",
      "old_teacher": "Mr. Schmidt",
      "new_teacher": "Mrs. Weber",
      "reason": "Training"
    },
    {
      "type": "lesson_cancelled",
      "date": "2025-09-16",
      "class_hour": "6",
      "subject": "Physical Education",
      "reason": "Gym renovation"
    }
  ],
  "total_new_changes": 2
}
```

## 📚 Homework Sensors

### 9. Homework Due Today Sensor

**Entity ID**: `sensor.{student_name}_homework_due_today`

**Purpose**: Shows the number of homework assignments due today.

**State Values**:
- `"3"` - Number of homework assignments due today
- `"0"` - No homework due today

**Attributes**:
```json
{
  "homeworks": [
    {
      "id": 12345,
      "subject": "Mathematics",
      "homework": "Problems p. 45, No. 1-10",
      "date": "2025-09-14",
      "teacher": "Mr. Schmidt",
      "completed": false,
      "days_overdue": 0
    }
  ],
  "count": 3,
  "subjects": ["Mathematics", "German", "English"]
}
```

### 10. Homework Due Tomorrow Sensor

**Entity ID**: `sensor.{student_name}_homework_due_tomorrow`

**Purpose**: Shows the number of homework assignments due tomorrow.

**State Values**:
- `"2"` - Number of homework assignments due tomorrow
- `"0"` - No homework due tomorrow

### 11. Homework Overdue Sensor

**Entity ID**: `sensor.{student_name}_homework_overdue`

**Purpose**: Shows overdue homework assignments.

**State Values**:
- `"1"` - Number of overdue homework assignments
- `"0"` - No overdue homework

**Attributes**:
```json
{
  "homeworks": [
    {
      "id": 12340,
      "subject": "History",
      "homework": "Prepare presentation",
      "date": "2025-09-12",
      "teacher": "Mrs. Weber",
      "completed": false,
      "days_overdue": 2
    }
  ],
  "count": 1,
  "most_overdue_days": 2
}
```

### 12. Homework Upcoming Sensor

**Entity ID**: `sensor.{student_name}_homework_upcoming`

**Purpose**: Shows upcoming homework assignments (next 7 days).

**State Values**:
- `"8"` - Number of upcoming homework assignments
- `"0"` - No upcoming homework

## 📝 Exam Sensors

### 13. Exams Today Sensor

**Entity ID**: `sensor.{student_name}_exams_today`

**Purpose**: Shows exams/tests scheduled for today.

**State Values**:
- `"2"` - Number of exams today
- `"0"` - No exams today

**Attributes**:
```json
{
  "exams": [
    {
      "subject": "German",
      "subject_abbreviation": "D",
      "title": "Class Test",
      "date": "2025-09-14",
      "time": "11:41-12:26",
      "class_hour": "5",
      "room": "",
      "teacher": "",
      "type": "Class Test",
      "type_color": "#c6dcef",
      "comment": "",
      "days_until": 0
    }
  ],
  "count": 2
}
```

### 14. Exams This Week Sensor

**Entity ID**: `sensor.{student_name}_exams_this_week`

**Purpose**: Shows all exams for this week.

**State Values**:
- `"3"` - Number of exams this week
- `"0"` - No exams this week

**Attributes**:
```json
{
  "exams": [
    {
      "subject": "Mathematics",
      "subject_abbreviation": "M",
      "title": "Test",
      "date": "2025-09-16",
      "time": "08:00-08:45",
      "class_hour": "1",
      "type": "Test",
      "type_color": "#ffeb3b",
      "days_until": 2
    }
  ],
  "count": 3,
  "subjects": ["Mathematics", "German", "English"]
}
```

### 15. Exams Next Week Sensor

**Entity ID**: `sensor.{student_name}_exams_next_week`

**Purpose**: Shows exams for next week.

### 16. Exams Upcoming Sensor

**Entity ID**: `sensor.{student_name}_exams_upcoming`

**Purpose**: Shows all upcoming exams (next 30 days).

**State Values**:
- `"5"` - Number of upcoming exams
- `"0"` - No upcoming exams

**Attributes**:
```json
{
  "exams": [
    {
      "subject": "English",
      "title": "Vocabulary Test",
      "date": "2025-09-20",
      "time": "10:45-11:30",
      "type": "Quiz",
      "days_until": 6,
      "is_next_exam": true
    }
  ],
  "count": 5,
  "subjects": ["English", "Physics", "Chemistry"],
  "next_exam_date": "2025-09-20"
}
```

## 🔧 Sensor Implementation

### Base Sensor Class

```python
class SchulmanagerOnlineSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Schulmanager Online sensor."""
    
    def __init__(
        self,
        coordinator: SchulmanagerOnlineDataUpdateCoordinator,
        student_id: int,
        sensor_type: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.student_id = student_id
        self.sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_{student_id}_{sensor_type}"
        
        # Get student info
        student = self._get_student_info()
        student_name = f"{student['firstname']} {student['lastname']}"
        
        # Set entity properties based on sensor type
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = f"{student_name} {sensor_config['name']}"
        self._attr_icon = sensor_config['icon']
        self._attr_device_class = sensor_config.get('device_class')
        self._attr_state_class = sensor_config.get('state_class')
        
        # Device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"student_{student_id}")},
            name=student_name,
            manufacturer="Schulmanager Online",
            model="Student Schedule",
        )
    
    def _get_student_info(self) -> Dict[str, Any]:
        """Get student information."""
        for student_id, data in self.coordinator.data.items():
            if student_id == self.student_id:
                return data["student"]
        return {}
    
    def _get_schedule_data(self) -> List[Dict[str, Any]]:
        """Get schedule data for this student."""
        student_data = self.coordinator.data.get(self.student_id, {})
        return student_data.get("schedule", [])
```

### Sensor-Specific Implementations

```python
@property
def native_value(self):
    """Return the native value of the sensor."""
    if self.sensor_type == "current_lesson":
        return self._get_current_lesson()
    elif self.sensor_type == "next_lesson":
        return self._get_next_lesson()
    elif self.sensor_type == "todays_lessons":
        return self._get_todays_lessons_count()
    elif self.sensor_type == "todays_changes":
        return self._get_todays_changes_count()
    elif self.sensor_type == "next_school_day":
        return self._get_next_school_day()
    elif self.sensor_type == "this_week":
        return self._get_this_week_count()
    elif self.sensor_type == "next_week":
        return self._get_next_week_count()
    elif self.sensor_type == "changes_detected":
        return self._get_changes_status()
    
    return None

@property
def extra_state_attributes(self):
    """Return the state attributes."""
    if self.sensor_type == "current_lesson":
        return self._get_current_lesson_attributes()
    elif self.sensor_type == "next_lesson":
        return self._get_next_lesson_attributes()
    # ... more implementations
    
    return {}
```

## 📱 Usage in Home Assistant

### Dashboard Integration

```yaml
# Lovelace Dashboard Configuration
type: entities
title: Schulmanager - Marc Cedric
entities:
  - entity: sensor.name_of_child_current_lesson
    name: Current Lesson
  - entity: sensor.name_of_child_next_lesson
    name: Next Lesson
  - entity: sensor.name_of_child_todays_changes
    name: Today's Changes
```

### Automations

```yaml
# Notification for substitutions
automation:
  - alias: "Schulmanager - Substitution detected"
    trigger:
      - platform: state
        entity_id: sensor.name_of_child_changes_detected
        to: "New Changes"
    action:
      - service: notify.mobile_app
        data:
          title: "Schedule Change"
          message: >
            New substitution for {{ trigger.to_state.attributes.student_name }}:
            {{ trigger.to_state.attributes.changes[0].subject }} 
            on {{ trigger.to_state.attributes.changes[0].date }}
```

### Template Sensors

```yaml
# Template for next lesson with countdown
template:
  - sensor:
      - name: "Next Lesson Countdown"
        state: >
          {% set next_lesson = states('sensor.name_of_child_next_lesson') %}
          {% set minutes = state_attr('sensor.name_of_child_next_lesson', 'minutes_until') %}
          {% if minutes is not none and minutes > 0 %}
            {{ next_lesson }} in {{ minutes }} minutes
          {% else %}
            {{ next_lesson }}
          {% endif %}
```

## 🔄 Update Strategies

### Intelligent Updates

```python
async def _async_update_data(self):
    """Update data with intelligent scheduling."""
    now = datetime.now()
    
    # Faster updates during school hours
    if self._is_school_time(now):
        # Update current/next lesson every 5 minutes
        if now.minute % 5 == 0:
            await self._update_current_lessons()
    
    # Normal updates every 15 minutes
    if now.minute % 15 == 0:
        await self._update_daily_schedule()
    
    # Weekly updates hourly
    if now.minute == 0:
        await self._update_weekly_schedule()
```

### Caching Mechanism

```python
class ScheduleCache:
    """Cache for schedule data to reduce API calls."""
    
    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
    
    def get(self, key: str, max_age: timedelta = timedelta(minutes=15)):
        """Get cached data if still valid."""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp and datetime.now() - timestamp < max_age:
                return self._cache[key]
        return None
    
    def set(self, key: str, data: Any):
        """Cache data with timestamp."""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now()
```

## 🚨 Error Handling

### Sensor Availability

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    return (
        self.coordinator.last_update_success and
        self.student_id in self.coordinator.data and
        self.coordinator.data[self.student_id].get("schedule") is not None
    )

@property
def native_value(self):
    """Return the native value with error handling."""
    try:
        if not self.available:
            return "Not Available"
        
        return self._calculate_sensor_value()
        
    except Exception as e:
        _LOGGER.error("Error calculating sensor value for %s: %s", self.entity_id, e)
        return "Error"
```

### Graceful Degradation

```python
def _get_current_lesson_safe(self):
    """Get current lesson with fallback."""
    try:
        return self._get_current_lesson()
    except Exception as e:
        _LOGGER.warning("Could not determine current lesson: %s", e)
        
        # Fallback: Check if we have any lesson data for today
        today_lessons = self._get_todays_lessons_safe()
        if today_lessons:
            return "Schedule Available"
        
        return "No Data"
```

## 📊 Performance Optimization

### Lazy Loading

```python
@cached_property
def _processed_schedule(self):
    """Process schedule data once and cache it."""
    schedule = self._get_schedule_data()
    
    # Process and sort lessons
    processed = []
    for lesson in schedule:
        processed_lesson = self._process_lesson(lesson)
        processed.append(processed_lesson)
    
    return sorted(processed, key=lambda x: (x['date'], x['start_time']))
```

### Batch Processing

```python
def _update_all_sensors_batch(self):
    """Update multiple sensors in one pass."""
    schedule_data = self._get_schedule_data()
    now = datetime.now()
    
    # Calculate all sensor values in one pass
    results = {
        'current_lesson': self._calculate_current_lesson(schedule_data, now),
        'next_lesson': self._calculate_next_lesson(schedule_data, now),
        'todays_lessons': self._calculate_todays_lessons(schedule_data, now.date()),
        # ... more calculations
    }
    
    return results
```

## 📚 Further Documentation

- [Integration Architecture](Integration_Architecture.md) - Overall architecture
- [Custom Card Documentation](Custom_Card_Documentation.md) - UI integration
- [Configuration Guide](Configuration_Guide.md) - Configuration
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solving
