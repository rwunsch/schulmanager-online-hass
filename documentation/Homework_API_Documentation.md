# Homework API - Detailed Documentation

## 🎯 Overview

The Homework API enables retrieving homework assignments for students via the `classbook` module of the Schulmanager Online API. This documentation describes the implementation, data structures, and usage.

## 📡 API Endpoint

### Retrieve Homework

**Endpoint**: `classbook/get-homework`
**Method**: POST
**Module**: `classbook`

```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "classbook",
      "endpointName": "get-homework",
      "parameters": {
        "student": {"id": 4333047}
      }
    }
  ]
}
```

## 📊 Response Structure

### Successful Response

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 12345,
          "subject": "Mathematics",
          "homework": "Work on problems p. 45, No. 1-10",
          "date": "2025-09-16",
          "teacher": "Mr. Schmidt",
          "completed": false,
          "createdAt": "2025-09-11T08:30:00.000Z",
          "updatedAt": "2025-09-11T08:30:00.000Z"
        },
        {
          "id": 12346,
          "subject": "German",
          "homework": "Memorize poem 'Der Erlkönig'",
          "date": "2025-09-17",
          "teacher": "Mrs. Müller",
          "completed": true,
          "createdAt": "2025-09-10T14:20:00.000Z",
          "updatedAt": "2025-09-12T16:45:00.000Z"
        },
        {
          "id": 12347,
          "subject": "English",
          "homework": "Learn Vocabulary Unit 3",
          "date": "2025-09-18",
          "teacher": "Mrs. Johnson",
          "completed": false,
          "createdAt": "2025-09-12T10:15:00.000Z",
          "updatedAt": "2025-09-12T10:15:00.000Z"
        }
      ]
    }
  ]
}
```

### Data Field Description

| Field | Type | Description |
|-------|------|-------------|
| `id` | `number` | Unique homework assignment ID |
| `subject` | `string` | Subject name (direct string) |
| `homework` | `string` | Homework description |
| `date` | `string` | Due date (ISO format: YYYY-MM-DD) |
| `teacher` | `string` | Teacher name |
| `completed` | `boolean` | Status: completed (true) or pending (false) |
| `createdAt` | `string` | Creation date (ISO format) |
| `updatedAt` | `string` | Last update (ISO format) |

## 🐍 Python Implementation

### API Client Method

```python
async def get_homework(self, student_id: int) -> Dict[str, Any]:
    """Get homework for a student using the classbook module."""
    requests = [
        {
            "moduleName": "classbook",
            "endpointName": "get-homework",
            "parameters": {"student": {"id": student_id}}
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        responses = response.get("responses", [])
        
        if not responses:
            raise SchulmanagerAPIError("No homework response")
        
        homework_data = responses[0]
        
        if homework_data.get("status") != 200:
            raise SchulmanagerAPIError(f"Homework request failed: {homework_data.get('status')}")
        
        # Extract homework data - can be direct list or nested
        homeworks = homework_data.get("homeworks", homework_data.get("data", []))
        
        _LOGGER.debug("Found %d homework assignments for student %d", len(homeworks), student_id)
        
        return homework_data
        
    except Exception as e:
        _LOGGER.error("Failed to get homework for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get homework: {e}") from e
```

### Fallback Implementation

```python
async def get_homework_legacy(self, student_id: int) -> Dict[str, Any]:
    """Get homework using legacy method (fallback)."""
    requests = [
        {
            "method": "homeworks/get-homeworks",
            "data": {"studentId": student_id}
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        # ... similar implementation
        return homework_data
        
    except Exception as e:
        _LOGGER.error("Failed to get homework (legacy) for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get homework (legacy): {e}") from e
```

## 📊 Sensor Integration

### Homework Sensors

The Homework API is integrated into 4 different sensors:

1. **Homework Due Today** - Homework due today
2. **Homework Due Tomorrow** - Homework due tomorrow
3. **Homework Overdue** - Overdue homework
4. **Homework Upcoming** - Upcoming homework (7 days)

### Sensor Logic

```python
def get_homework_due_today_count(student_data: Dict[str, Any]) -> str:
    """Get count of homework due today."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    
    # Filter homework due today
    due_today = [hw for hw in homeworks 
                 if hw.get("date") == today and not hw.get("completed", False)]
    
    return str(len(due_today))

def get_homework_due_today_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for homework due today sensor."""
    homework_data = student_data.get("homework", {})
    homeworks = _extract_homeworks(homework_data)
    
    today = datetime.now().date().isoformat()
    due_today = [hw for hw in homeworks 
                 if hw.get("date") == today and not hw.get("completed", False)]
    
    # Get unique subjects
    subjects = list(set(hw.get("subject", "Unknown") for hw in due_today))
    
    attributes = {
        "homeworks": [_format_homework_info(hw) for hw in due_today],
        "count": len(due_today),
        "subjects": subjects,
    }
    
    return attributes
```

### Data Transformation

```python
def _format_homework_info(homework: Dict[str, Any]) -> Dict[str, Any]:
    """Format homework data for consistent output."""
    return {
        "id": homework.get("id"),
        "subject": homework.get("subject", "Unknown"),
        "homework": homework.get("homework", "No description"),
        "date": homework.get("date", ""),
        "teacher": homework.get("teacher", ""),
        "completed": homework.get("completed", False),
        "days_until": calculate_days_until(homework.get("date", "")),
        "days_overdue": calculate_days_overdue(homework.get("date", "")),
    }

def calculate_days_until(date_str: str) -> int:
    """Calculate days until due date."""
    try:
        due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (due_date - today).days
    except (ValueError, TypeError):
        return 0

def calculate_days_overdue(date_str: str) -> int:
    """Calculate days overdue (negative if not overdue)."""
    try:
        due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_diff = (today - due_date).days
        return max(0, days_diff)  # Only positive values (overdue)
    except (ValueError, TypeError):
        return 0
```

## 🔄 Update Strategy

### Coordinator Integration

```python
# In coordinator.py
async def _async_update_data(self):
    """Update data including homework."""
    
    # Get homework if enabled
    if include_homework:
        try:
            homework_data = await self.api.get_homework(student_id)
            student_data["homework"] = homework_data
        except SchulmanagerAPIError as e:
            _LOGGER.warning("Failed to get homework for %s: %s", student_name, e)
            student_data["homework"] = {"homeworks": []}
```

### Update Interval

- **Standard**: 15 minutes
- **During school hours**: 15 minutes (no change needed)
- **Outside school hours**: 1 hour (planned)

## 🧪 Test Implementation

### Test Script

```python
#!/usr/bin/env python3
"""Test script for Homework API."""

import asyncio
import aiohttp
from datetime import datetime

async def test_homework_api():
    """Test homework API functionality."""
    
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    async with aiohttp.ClientSession() as session:
        api = SimpleSchulmanagerAPI(email, password, session)
        
        try:
            # Authenticate
            await api.authenticate()
            print("✅ Authentication successful!")
            
            # Get students
            students = await api.get_students()
            student_id = students[0]['id']
            
            # Test homework API
            homework_data = await api.get_homework(student_id)
            
            # Analyze data
            homeworks = homework_data.get("data", [])
            print(f"📚 Found {len(homeworks)} homework assignments")
            
            for i, hw in enumerate(homeworks[:3]):
                print(f"   {i+1}. {hw.get('subject')}: {hw.get('homework')[:50]}...")
                print(f"      Due: {hw.get('date')}, Completed: {hw.get('completed')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_homework_api())
```

### Curl Test

```bash
# Test homework API with curl
curl 'https://login.schulmanager-online.de/api/calls' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'content-type: application/json' \
  --data-raw '{
    "bundleVersion":"3505280ee7",
    "requests":[{
      "moduleName":"classbook",
      "endpointName":"get-homework",
      "parameters":{"student":{"id":4333047}}
    }]
  }'
```

## 🚨 Error Handling

### Common Errors

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `No homework response` | - | API response empty | Implement retry logic |
| `Homework request failed: 400` | 400 | Invalid parameters | Validate student ID |
| `Homework request failed: 401` | 401 | Token expired | Renew token |
| `Homework request failed: 403` | 403 | No permission | Check account type |

### Error Recovery

```python
async def get_homework_with_retry(self, student_id: int, max_retries: int = 3) -> Dict[str, Any]:
    """Get homework with automatic retry."""
    
    for attempt in range(max_retries):
        try:
            return await self.get_homework(student_id)
        except SchulmanagerAPIError as e:
            if "401" in str(e) and attempt < max_retries - 1:
                # Token expired, re-authenticate
                await self.authenticate()
                continue
            elif attempt == max_retries - 1:
                # Last attempt failed
                raise
            else:
                # Other error, wait and retry
                await asyncio.sleep(2 ** attempt)
    
    raise SchulmanagerAPIError("Max retries exceeded")
```

## 📱 Dashboard Integration

### Lovelace Cards

```yaml
# Homework Overview
type: entities
title: "Homework - Marc Cedric"
entities:
  - entity: sensor.name_of_child_homework_due_today
    name: "Due Today"
  - entity: sensor.name_of_child_homework_due_tomorrow  
    name: "Due Tomorrow"
  - entity: sensor.name_of_child_homework_overdue
    name: "Overdue"
  - entity: sensor.name_of_child_homework_upcoming
    name: "Upcoming"
```

### Automations

```yaml
# Reminder for overdue homework
automation:
  - alias: "Homework - Overdue"
    trigger:
      - platform: numeric_state
        entity_id: sensor.name_of_child_homework_overdue
        above: 0
    action:
      - service: notify.family
        data:
          title: "📚 Overdue Homework"
          message: >
            {{ states('sensor.name_of_child_homework_overdue') }} 
            homework assignments are overdue!
```

## 📚 Further Documentation

- [API Analysis](API_Analysis.md) - Complete API documentation
- [Sensors Documentation](Sensors_Documentation.md) - Sensor details
- [Integration Architecture](Integration_Architecture.md) - Architecture overview
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solutions