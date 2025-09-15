# Free Hours Implementation

## Overview

This document describes the implementation of free hours detection and handling in the Schulmanager Online Home Assistant integration.

## What are Free Hours?

Free hours are periods in the school schedule where no lesson is scheduled, but the time slot is available. For example:
- Tomorrow (Sep 15) the first lesson is free
- Every day the 7th lesson is free  
- Any period where no subject is scheduled but the school has defined class hours

## Key Changes Made

### 1. Created Centralized Utility Module (`free_hours_utils.py`)

A new utility module was created to centralize all free hours logic and eliminate code duplication:

**Key Functions:**
- `is_free_hour()` - Detects if a lesson is a free hour
- `filter_actual_lessons()` - Filters out free hours from lesson lists
- `count_lessons_by_type()` - Counts actual lessons vs free hours
- `get_subjects_from_lessons()` - Extracts subjects excluding free hours
- `get_teachers_from_lessons()` - Extracts teachers excluding free hours
- `format_lesson_summary()` - Creates consistent summary strings
- `add_free_hours_to_schedule()` - Adds free hours to processed schedules
- `parse_time_to_minutes()` - Centralized time parsing
- `format_minutes_to_time()` - Centralized time formatting

### 2. Updated Coordinator (`coordinator.py`)

**Changes:**
- Simplified `_process_schedule_data_with_free_hours` by using centralized utility
- Removed duplicate time parsing/formatting methods
- **CRITICAL FIX**: Removed incorrect hour number reassignment in `_assign_correct_hour_numbers`
- Now preserves API-provided period numbers (e.g., period 2, 3, 4, 5) instead of reassigning sequential numbers (1, 2, 3, 4)
- Free hours are now consistently added to all schedule data
- Times are correctly calculated using API class hours data
- Improved error handling and logging

**Free Hours Detection Logic:**
1. Get available periods from class hours API
2. Group existing lessons by date
3. Identify unoccupied periods for each school day
4. Create free hour objects for empty periods
5. Sort all lessons (including free hours) by date and time

### 3. Updated Schedule Sensors (`schedule_sensors.py`)

**Changes:**
- Replaced duplicate filtering logic with utility functions
- All sensor attributes now include both `total_lessons` and `free_hours` counts
- Consistent handling of free hours across all sensors
- Simplified code with better maintainability

**Sensor Behavior:**
- **State values**: Show count of actual lessons only (excluding free hours)
- **Attributes**: Include both actual lesson count and free hours count
- **Lesson lists**: Include all lessons (actual + free hours) for complete schedule view

### 4. Updated Calendar (`calendar.py`)

**Changes:**
- Uses centralized `is_free_hour()` function
- Removed duplicate time parsing/formatting methods
- **CRITICAL FIX**: `_get_configurable_class_times` now prioritizes API class hours data over calculated times
- Ensures calendar events use correct times from API instead of user configuration estimates
- Free hours are properly skipped in calendar events (they appear as gaps)

### 5. Code Simplification

**Removed Duplicates:**
- Time parsing functions (3 copies → 1 centralized)
- Time formatting functions (3 copies → 1 centralized)  
- Free hour detection logic (multiple places → 1 centralized)
- Lesson filtering logic (5+ copies → 1 centralized)

## Data Structure

### Free Hour Object
```python
{
    "id": "free_2025-09-15_7",
    "date": "2025-09-15",
    "class_hour_number": 7,
    "start_time": "13:20:00",
    "end_time": "14:05:00",
    "subject": "",
    "subject_name": "",
    "subject_abbreviation": "",
    "room": "",
    "teacher": "",
    "teachers": [],
    "type": "freeHour",
    "is_substitution": False,
    "comment": "",
    "is_cancelled": False,
    "is_free_hour": True,
}
```

### Sensor Attributes Example
```python
{
    "total_lessons": 5,      # Actual lessons only
    "free_hours": 2,         # Free hours count
    "lessons": [...],        # All lessons including free hours
    "subjects": ["M", "E", "P", "C", "H"],
    "teachers": ["SM", "JD", "AB"],
    "subject_count": 5,
    "teacher_count": 3,
    "changes_count": 0
}
```

## Benefits

### 1. **Accurate Counting**
- Sensors now properly distinguish between actual lessons and free hours
- Total schedule visibility includes all periods (lessons + free hours)
- Statistics exclude free hours for meaningful metrics

### 2. **Consistent Behavior**
- All components use the same free hour detection logic
- Unified data structures across sensors, calendar, and coordinator
- Predictable behavior for automations and UI

### 3. **Better User Experience**
- Clear indication when periods are free vs scheduled
- Complete schedule view showing all time slots
- Proper time calculations accounting for free periods

### 4. **Code Quality**
- Eliminated duplicate code (reduced maintenance burden)
- Centralized utilities for better testing and debugging
- More maintainable and extensible architecture

## Example Usage

For a day with lessons in periods 2-6 and free hours in periods 1 and 7:

**Before:** 
- Sensor state: "7 lessons, 5 subjects" (incorrect - counted free hours as lessons)
- Calendar: Missing time slots (free hours not represented)

**After:**
- Sensor state: "5 lessons, 5 subjects" (correct - actual lessons only)  
- Sensor attributes: `total_lessons: 5, free_hours: 2`
- Calendar: Proper gaps for free hours, events only for actual lessons

## Critical Bug Fix

### Problem Identified
The original implementation had a critical bug in the `_assign_correct_hour_numbers` method:

1. **API provides correct period numbers**: Lessons come with correct `classHour.number` (e.g., 2, 3, 4, 5, 6)
2. **Bug was reassigning sequential numbers**: Method was overriding API periods with sequential numbers (1, 2, 3, 4, 5)
3. **Free hour detection failed**: When lesson in period 2 was reassigned to period 1, free hour detection thought period 2 was free
4. **Calendar showed wrong times**: First lesson showed at 8:00 AM instead of 8:50 AM (correct period 2 time)

### Example Scenario
**API Data:** Lessons in periods 2, 3, 4, 5, 6 (period 1 is free)
**Before Fix:** 
- Lessons reassigned to periods 1, 2, 3, 4, 5 
- Free hours detected in periods 6-11 (wrong!)
- Calendar shows first lesson at 8:00 AM (period 1 time)

**After Fix:**
- Lessons keep original periods 2, 3, 4, 5, 6
- Free hours detected in periods 1, 7-11 (correct!)
- Calendar shows first lesson at 8:50 AM (period 2 time)

### Solution
1. **Preserve API period numbers**: Don't reassign `class_hour_number` from API
2. **Use API class hours for times**: Prioritize actual class hours data over calculated estimates
3. **Correct free hour detection**: Compare actual occupied periods vs available periods

## Testing

The implementation was verified with comprehensive unit tests covering:
- Free hour detection accuracy
- Lesson filtering and counting
- Time utilities functionality  
- Schedule processing with free hours
- Summary formatting
- **Critical**: Period number preservation and correct time calculation

All tests pass, confirming the implementation works correctly and maintains backward compatibility while adding the new free hours functionality.

## Configuration Removal ✅ COMPLETED

**BREAKING CHANGE**: Removed unnecessary user configuration options since the API provides authoritative class hours:

### Removed Configuration Options:
- ~~`lesson_duration_minutes`~~ - Now from API `class_hours[].from/until`
- ~~`short_break_minutes`~~ - Now calculated from API class hour gaps
- ~~`long_break_1_minutes`~~ - Now calculated from API class hour gaps
- ~~`long_break_2_minutes`~~ - Now calculated from API class hour gaps
- ~~`lunch_break_minutes`~~ - Now calculated from API class hour gaps
- ~~`school_start_time`~~ - Now from API `class_hours[0].from`

### Files Modified:
- `custom_components/schulmanager_online/const.py` - Removed timing constants
- `custom_components/schulmanager_online/config_flow.py` - Removed UI configuration options
- `custom_components/schulmanager_online/coordinator.py` - Removed `_get_schedule_config()`, simplified `_calculate_times_for_hour()`
- `custom_components/schulmanager_online/calendar.py` - Removed user config fallback
- `custom_components/schulmanager_online/sensor.py` - Removed schedule_config from attributes

### Impact:
- **Existing installations**: Configuration options removed from UI, but no data loss
- **Accuracy**: Calendar now shows **exact** times from school's system instead of estimates
- **Simplicity**: No user configuration needed for timing - fully automatic

### API Discovery:
The key discovery was that the Schulmanager Online API provides **two separate endpoints**:
1. **`get-actual-lessons`**: Returns lesson data with period numbers
2. **`get-class-hours`**: Returns the actual start/end times for each period

Example API class hours data:
```json
{
  "number": "2",
  "from": "08:48:00",
  "until": "09:33:00"
}
```

This means period 2 runs from 08:48-09:33, not the estimated 08:50-09:35 from user configuration.
