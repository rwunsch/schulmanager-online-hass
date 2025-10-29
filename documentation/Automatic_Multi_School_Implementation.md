# Automatic Multi-School Implementation Guide

**Version:** 2.0  
**Date:** 2025-10-29  
**Feature:** Automatic collection of students from all schools without user selection

---

## Executive Summary

This implementation eliminates the need for users to manually select schools when setting up multi-school accounts. Instead, the integration automatically:
1. Detects all schools associated with an account
2. Authenticates with each school
3. Collects all students from all schools
4. Creates one config entry with all students

---

## User Experience

### Before (v1.x): Manual School Selection

```
Multi-School Account Setup (OLD):
1. User: Add Integration
2. User: Enter credentials
3. System: "Select a school: [School A] [School B]"
4. User: Selects "School A"
5. Result: Students from School A added

To get School B students:
6. User: Add Integration AGAIN
7. User: Enter same credentials
8. System: "Select a school: [School A] [School B]"
9. User: Selects "School B"
10. Result: Students from School B added

Final: 2 config entries, extra work for user
```

### After (v2.0+): Automatic Collection

```
Multi-School Account Setup (NEW):
1. User: Add Integration
2. User: Enter credentials
3. System: Automatically detects 2 schools
4. System: Collects students from both schools
5. System: Shows "Found 3 students:
           - Alice (Gymnasium München)
           - Bob (Gymnasium München) 
           - Carol (Realschule Berlin)"
6. Result: ALL students from ALL schools added

Final: 1 config entry, simple one-time setup
```

---

## Technical Implementation

### Phase 1: Config Flow Changes

**File:** `config_flow.py`

#### Key Changes:

1. **`validate_input()` function** - Multi-school detection and collection:
```python
async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    # Authenticate initially
    await api.authenticate()
    
    # Check for multi-school
    multiple_accounts = api.get_multiple_accounts()
    if multiple_accounts:
        all_students = []
        schools = []
        
        # Iterate over ALL schools
        for school in multiple_accounts:
            school_api = SchulmanagerAPI(email, password, session)
            await school_api.authenticate(institution_id=school_id)
            school_students = await school_api.get_students()
            
            # Tag each student with their school
            for student in school_students:
                student["_institution_id"] = school_id
                student["_institution_name"] = school_name
                all_students.append(student)
            
            schools.append({"id": school_id, "name": school_name})
        
        return {
            "students": all_students,
            "schools": schools,
            "multi_school": True
        }
```

2. **Removed `async_step_select_school()`** - No longer needed

3. **Updated `async_step_user()`** - Skip school selection:
```python
# Store schools in config entry data
self._data["schools"] = self._schools

# No school selection - proceed directly to options
return await self.async_step_options()
```

4. **Enhanced `async_step_options()`** - Display school names:
```python
# Show students with their school names
student_list = []
for s in self._students:
    name = f"{s.get('firstname', '')} {s.get('lastname', '')}"
    school = s.get('_institution_name')
    if school:
        student_list.append(f"{name} ({school})")
```

### Phase 2: Multi-API Instance Support

**File:** `__init__.py`

#### Key Changes:

1. **Multiple API Instance Creation**:
```python
api_instances = {}  # Dict of {institution_id: SchulmanagerAPI}

if schools:
    for school in schools:
        school_api = SchulmanagerAPI(email, password, session)
        await school_api.authenticate(institution_id=school_id)
        school_students = await school_api.get_students()
        
        # Tag students
        for student in school_students:
            student["_institution_id"] = school_id
            student["_institution_name"] = school_name
        
        api_instances[school_id] = school_api
```

2. **Helper Function** - Route API calls to correct instance:
```python
def get_api_for_student(student: Dict[str, Any], api_instances: Dict[int, SchulmanagerAPI]):
    """Get the correct API instance for a student based on their institution."""
    institution_id = student.get("_institution_id")
    
    if institution_id and institution_id in api_instances:
        return api_instances[institution_id]
    
    # Fallback: return first available
    return next(iter(api_instances.values()))
```

3. **Store in hass.data**:
```python
hass.data[DOMAIN][entry.entry_id] = {
    "coordinator": coordinator,
    "api_instances": api_instances,  # Multiple APIs
    "students": all_students,
    "schools": schools,
}
```

### Phase 3: Coordinator Updates

**File:** `coordinator.py`

#### Key Changes:

1. **Accept API Instances Dict**:
```python
def __init__(self, hass: HomeAssistant, api_instances: Dict[int, Any], options: Dict[str, Any]):
    self.api_instances = api_instances  # Changed from single api
```

2. **Route API Calls**:
```python
def _get_api_for_student(self, student: Dict[str, Any]):
    """Get the correct API instance for a student."""
    institution_id = student.get("_institution_id")
    return self.api_instances.get(institution_id)
```

3. **Updated Data Fetching**:
```python
# Get students from all API instances
if not self.students:
    all_students = []
    for institution_id, api in self.api_instances.items():
        students = await api.get_students()
        for student in students:
            student["_institution_id"] = institution_id
        all_students.extend(students)
    self.students = all_students

# For each student, use correct API
for student in self.students:
    student_api = self._get_api_for_student(student)
    schedule_data = await student_api.get_schedule(student_id, start_date, end_date)
    homework_data = await student_api.get_homework(student_id)
    # ... etc
```

4. **Letters Collection** - From all schools:
```python
# Get letters from each school
all_letters = []
for institution_id, api in self.api_instances.items():
    letters_data = await api.get_letters()
    for letter in letters_data.get("data", []):
        letter["_institution_id"] = institution_id
    all_letters.extend(letters_data.get("data", []))
```

### Phase 4: Sensor Updates

**File:** `sensor.py`

#### Key Changes:

1. **Extract Institution from Student**:
```python
for student in students:
    # Get institution info from student data
    student_institution_id = student.get("_institution_id")
    student_institution_name = student.get("_institution_name")
    
    # Pass to sensor
    entities.append(SchulmanagerOnlineSensor(
        coordinator=coordinator,
        student_id=student_id,
        student_info=student,
        institution_id=student_institution_id,
        institution_name=student_institution_name,
    ))
```

No changes needed to sensor attributes - they already display institution info!

---

## Data Structures

### Config Entry Data

```python
entry.data = {
    "email": "parent@example.com",
    "password": "***",
    "schools": [
        {"id": 13309, "name": "Gymnasium München"},
        {"id": 14520, "name": "Realschule Berlin"}
    ]
}
```

### Student Data

```python
student = {
    "id": 12345,
    "firstname": "Alice",
    "lastname": "Johnson",
    "classId": 444612,
    # Added by integration:
    "_institution_id": 13309,
    "_institution_name": "Gymnasium München"
}
```

### hass.data Structure

```python
hass.data[DOMAIN][entry_id] = {
    "coordinator": SchulmanagerDataUpdateCoordinator,
    "api_instances": {
        13309: SchulmanagerAPI,  # Gymnasium München
        14520: SchulmanagerAPI   # Realschule Berlin
    },
    "students": [
        {id: 1001, _institution_id: 13309, ...},  # Alice
        {id: 1002, _institution_id: 13309, ...},  # Bob
        {id: 2001, _institution_id: 14520, ...}   # Carol
    ],
    "schools": [
        {"id": 13309, "name": "Gymnasium München"},
        {"id": 14520, "name": "Realschule Berlin"}
    ]
}
```

---

## Benefits

### For Users

1. **Simpler Setup** - Enter credentials once, get all students
2. **No Confusion** - No need to understand "school selection"
3. **Complete Data** - All children visible immediately
4. **Cleaner UI** - One integration entry instead of multiple
5. **Automatic Updates** - If schools change, reload gets all current schools

### For Developers

1. **Better Architecture** - Multiple API instances properly managed
2. **Scalable** - Handles any number of schools
3. **Maintainable** - Clear routing logic
4. **Robust** - Each school's API is independent
5. **Future-Proof** - Easy to extend with more features

---

## Migration from v1.x to v2.0

### For Existing Users

**Old setup (2 config entries):**
```
Config Entry 1: School A (Alice, Bob)
Config Entry 2: School B (Carol)
```

**Migration path:**
1. Keep existing entries (they still work)
2. Optionally: Delete both entries
3. Optionally: Re-add integration once
4. Result: One entry with all students

**Note:** Old entries continue to work fine. Migration is optional.

### Data Compatibility

v2.0 maintains backward compatibility with v1.x data structures:

```python
# v1.x single-school entry
entry.data = {
    "email": "...",
    "password": "...",
    "institution_id": 13309,
    "institution_name": "Gymnasium München"
}

# v2.0 handles this gracefully in __init__.py:
if schools:
    # New multi-school path
    ...
else:
    # Legacy single-school path
    institution_id = entry.data.get("institution_id")
    api = SchulmanagerAPI(email, password, session)
    await api.authenticate(institution_id=institution_id)
    api_instances[institution_id] = api
```

---

## Testing Checklist

- [x] Single-school account setup
- [x] Multi-school account setup (automatic collection)
- [x] Student data includes institution_id and institution_name
- [x] Sensors show correct institution info in attributes
- [x] Schedule data fetched from correct school
- [x] Homework data fetched from correct school
- [x] Grades data fetched from correct school
- [x] Exams data fetched from correct school
- [x] Letters collected from all schools
- [x] Calendar entities created for all students
- [x] Legacy single-school entries still work
- [x] Service: clear_cache works with multiple API instances
- [x] Service: refresh works with coordinator

---

## Known Limitations

1. **Re-authentication Timing** - Each school requires separate authentication during setup (adds ~2-3 seconds per school)
2. **Token Expiration** - Each API instance manages its own token expiration independently
3. **API Rate Limits** - Multiple schools mean more API calls (still within reasonable limits)

---

## Future Enhancements

1. **Parallel Authentication** - Authenticate with all schools simultaneously (faster setup)
2. **Selective School Disable** - Allow users to disable specific schools without removing entry
3. **School-Level Sensors** - Aggregate data at school level (e.g., "School A Schedule")
4. **Migration Tool** - Automatic migration wizard for v1.x users

---

## Code Files Modified

| File | Changes | Lines Changed |
|------|---------|---------------|
| `config_flow.py` | Multi-school auto-collection | ~100 |
| `__init__.py` | Multiple API instances | ~80 |
| `coordinator.py` | API routing logic | ~50 |
| `sensor.py` | Student-level institution info | ~20 |
| Documentation | Updated guides | ~200 |

**Total:** ~450 lines changed across 5 files

---

## Summary

This implementation transforms the multi-school experience from a confusing multi-step process requiring duplicate integration setups into a seamless one-time setup that automatically discovers and configures all schools and students. The architecture cleanly manages multiple API instances with proper routing, while maintaining full backward compatibility with existing single-school setups.

