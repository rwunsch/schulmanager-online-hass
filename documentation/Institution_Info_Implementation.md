# Institution/School Information Added to Students

**Date:** 2025-10-29  
**Status:** ✅ **IMPLEMENTED**

---

## Summary

Added institution/school information (ID and name) to all student sensors as attributes. This allows users to see which school each student belongs to, especially useful for multi-school scenarios.

---

## What Was Added

### New Sensor Attributes

All student sensors now include two new attributes:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `institution_id` | int | Unique ID of the school | `13309` |
| `institution_name` | string | Name of the school | `"Gymnasium München"` |

### Where These Appear

The attributes are added to **all sensors** for each student:

**Schedule Sensors:**
- `sensor.lesson_current_<student>`
- `sensor.lesson_next_<student>`
- `sensor.lessons_today_<student>`
- `sensor.lessons_changes_today_<student>`
- `sensor.lessons_tomorrow_<student>`
- `sensor.lessons_this_week_<student>`
- `sensor.lessons_next_week_<student>`
- `sensor.lessons_next_school_day_<student>`
- `sensor.changes_detected_<student>`

**Homework Sensors** (if enabled):
- `sensor.homework_due_today_<student>`
- `sensor.homework_due_tomorrow_<student>`
- `sensor.homework_overdue_<student>`
- `sensor.homework_upcoming_<student>`
- `sensor.homework_recent_<student>`

**Exam Sensors** (if enabled):
- `sensor.exams_today_<student>`
- `sensor.exams_this_week_<student>`
- `sensor.exams_next_week_<student>`
- `sensor.exams_upcoming_<student>`

**Grade Sensors** (if enabled):
- Grade average sensors

---

## How To Use

### View in Developer Tools

1. Go to **Developer Tools → States**
2. Find any student sensor (e.g., `sensor.lesson_current_alice`)
3. Click on the sensor
4. Scroll to **Attributes**
5. See `institution_id` and `institution_name`

### Use in Automations

```yaml
automation:
  - alias: "Notify when lesson starts at School A"
    trigger:
      - platform: state
        entity_id: sensor.lesson_current_alice
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.lesson_current_alice', 'institution_name') == 'Gymnasium München' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Alice's lesson at {{ state_attr('sensor.lesson_current_alice', 'institution_name') }} is starting"
```

### Use in Templates

```yaml
# Show which school each student is at
{{ state_attr('sensor.lesson_current_alice', 'institution_name') }}
# Returns: "Gymnasium München"

# Check institution ID
{{ state_attr('sensor.lesson_current_alice', 'institution_id') }}
# Returns: 13309

# Create a list of students by school
{% for entity in states.sensor 
   if 'lesson_current' in entity.entity_id 
   and state_attr(entity.entity_id, 'institution_id') == 13309 %}
  - {{ state_attr(entity.entity_id, 'student_name') }}
{% endfor %}
```

### Use in Lovelace Cards

```yaml
type: entities
entities:
  - entity: sensor.lesson_current_alice
    secondary_info: last-changed
  - type: attribute
    entity: sensor.lesson_current_alice
    attribute: institution_name
    name: School
  - type: attribute
    entity: sensor.lesson_current_alice
    attribute: institution_id
    name: School ID
```

---

## Example Output

### Single-School Account

```json
{
  "state": "Math",
  "attributes": {
    "student_id": 4333047,
    "student_name": "Marc Cedric Wunsch",
    "institution_id": 13309,
    "institution_name": null,
    "subject": "Math",
    "teacher": "Mr. Smith",
    ...
  }
}
```

**Note:** For single-school accounts, `institution_name` may be `null` since the API doesn't provide the school name in the login response. Only `institution_id` is available.

### Multi-School Account

```json
{
  "state": "English",
  "attributes": {
    "student_id": 5001,
    "student_name": "Alice Johnson",
    "institution_id": 13309,
    "institution_name": "Gymnasium München",
    "subject": "English",
    "teacher": "Mrs. Brown",
    ...
  }
}
```

**Note:** For multi-school accounts, `institution_name` is available because the user selected the school from a list during setup.

---

## Implementation Details

### Files Modified

1. **`config_flow.py`**
   - Line 184-185: Extract institution name during school selection
   - Line 206: Store `institution_name` in config entry data

2. **`__init__.py`**
   - Line 31: Retrieve `institution_name` from config entry
   - Line 64: Store in `hass.data` for access by sensors

3. **`sensor.py`**
   - Lines 167-168: Get institution info from `hass.data`
   - Lines 186-187, 200-201, 214-215: Pass to sensor constructors
   - Lines 253-254: Add institution parameters to `__init__`
   - Lines 262-263: Store as instance variables
   - Lines 346-350: Add to sensor attributes

### Data Flow

```
Config Flow:
  User selects school → institution_name extracted from choices
                           ↓
  Stored in config entry: entry.data["institution_name"]
  
Integration Setup:
  entry.data["institution_name"] → hass.data[entry_id]["institution_name"]
  
Sensor Setup:
  hass.data["institution_name"] → sensor.institution_name
                                      ↓
  Added to sensor.extra_state_attributes
```

---

## Multi-School Clarification

### How Multi-School Setup Works (v2.0+)

**NEW:** One config entry **DOES** automatically create all students across all schools! ✅

**Automatic Process:**

```
Parent with 3 kids at 2 schools:
├── Alice (School A - Gymnasium München)
├── Bob (School A - Gymnasium München)
└── Carol (School B - Realschule Berlin)

Step 1: Add Integration (ONE TIME ONLY)
  → Enter email/password
  → System detects 2 schools
  → System AUTOMATICALLY collects students from BOTH schools
  → Shows: "Found 3 students:
           - Alice (Gymnasium München)
           - Bob (Gymnasium München)
           - Carol (Realschule Berlin)"
  → ONE Config Entry created
  → Alice, Bob & Carol ALL added to HA ✅

Result:
  - 1 config entry in Home Assistant (not 2!)
  - All 3 students included
  - Alice: _institution_id=13309, _institution_name="Gymnasium München"
  - Bob: _institution_id=13309, _institution_name="Gymnasium München"
  - Carol: _institution_id=14520, _institution_name="Realschule Berlin"
  - All 3 students have their school info in attributes ✅
```

### Why This Works

The Schulmanager API:
- Returns ONLY students from the selected school during each authentication
- One token = One school = Students from that school

Our NEW implementation (v2.0+):
- ✅ Creates **multiple API instances** (one per school)
- ✅ Each API instance has its own token for its school
- ✅ All API calls are routed to the correct API instance based on student's `_institution_id`
- ✅ Students know which school they belong to (via `_institution_id` and `_institution_name`)
- ✅ **One config entry = All schools = All students**

### Comparison: Old vs New

| Aspect | Old (v1.x) | New (v2.0+) |
|--------|-----------|-------------|
| **Config entries needed** | One per school | **One for all schools** |
| **User steps** | Add integration N times | **Add once** |
| **School selection** | Manual selection required | **Automatic collection** |
| **Student visibility** | Only from selected school | **All students from all schools** |
| **Token management** | One token per entry | **Multiple tokens per entry** |

---

## Benefits

### For Users with Single School
- Can see which school their students belong to
- Useful for verification and clarity

### For Users with Multiple Schools
- **Essential for distinguishing students**
- Can filter/group students by school in automations
- Can create school-specific dashboards
- Can handle different schedules per school

### For Developers
- Enables school-based filtering in custom cards
- Allows school-specific logic in automations
- Provides context for debugging

---

## Future Enhancements (Optional)

### 1. School Name for Single-School Accounts

Currently, single-school accounts don't get the school name because the API doesn't provide it in the login response.

**Possible solutions:**
- Make an additional API call to fetch school info
- Extract from another endpoint
- Allow manual entry in options

### 2. Dedicated Institution Sensor

Create a dedicated sensor showing only institution information:
```
sensor.student_alice_school
  State: "Gymnasium München"
  Attributes:
    - institution_id: 13309
    - institution_name: "Gymnasium München"
    - student_count: 2
    - last_update: 2025-10-29T10:00:00
```

### 3. School-Level Device

Create a school device (parent of student devices):
```
Device: Gymnasium München (ID: 13309)
  ├── Student: Alice
  └── Student: Bob
```

---

## Testing

### Tested Scenarios

✅ Single-school account (wunsch@gmx.de)
- `institution_id` correctly added to attributes
- `institution_name` is `null` (expected)

⚠️ Multi-school account (not tested yet)
- Should have both `institution_id` and `institution_name`
- Requires actual multi-school account for testing

### How to Test

1. **Check Existing Integration:**
   ```python
   # In Developer Tools → Template:
   {{ state_attr('sensor.lesson_current_marc_cedric_wunsch', 'institution_id') }}
   {{ state_attr('sensor.lesson_current_marc_cedric_wunsch', 'institution_name') }}
   ```

2. **For Multi-School Accounts:**
   - Add integration
   - Select first school
   - Verify sensors have correct institution info
   - Add integration again
   - Select second school
   - Verify sensors have different institution info

---

## Backward Compatibility

✅ **Fully backward compatible**

- Existing integrations will work without changes
- New attributes are optional (can be `None`)
- No breaking changes to existing sensors
- No migration needed

---

## Conclusion

Institution/school information is now available on all student sensors as attributes. This enables:
- ✅ Better identification of students in multi-school scenarios
- ✅ School-based filtering in automations
- ✅ More context for debugging
- ✅ Foundation for future school-level features

**All changes are backward compatible and ready to use!**

