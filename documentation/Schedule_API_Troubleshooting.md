# Schedule API 400 Bad Request - Troubleshooting Guide

## ✅ Issue Status - RESOLVED!

**Problem**: Schedule API returns 400 Bad Request despite successful authentication  
**Affected APIs**: `schedules/get-actual-lessons` and `letters/get-letters`  
**Status**: ✅ RESOLVED  
**Date**: September 14, 2025  
**Solution**: Added missing `bundleVersion` parameter and fixed response parsing  

## 📊 Detailed Analysis

### ✅ What Works
- **Authentication**: Perfect - Salt retrieval, hash generation, JWT token management
- **Student Data**: Successfully extracted from login response
- **Homework API**: `classbook/get-homework` works flawlessly
- **Exams API**: `exams/get-exams` works with date ranges

### ❌ What Fails
- **Schedule API**: `schedules/get-actual-lessons` returns 400 Bad Request
- **Letters API**: `letters/get-letters` returns identical 400 Bad Request

### 🔍 Debug Log Analysis

#### Successful Authentication
```
🧂 Salt response status: 200
✅ Salt received: 468 characters
Login successful, token expires at 2025-09-14 12:25:14.052476
```

#### Failed Schedule API Call
```
📤 Request payload: {
  'requests': [{
    'moduleName': 'schedules', 
    'endpointName': 'get-actual-lessons',
    'parameters': {
      'student': {
        'id': 4333047, 
        'firstname': 'Marc Cedric', 
        'lastname': 'Wunsch', 
        'sex': 'Male', 
        'classId': 444612
      },
      'start': '2025-09-08', 
      'end': '2025-09-22'
    }
  }]
}

📥 Response status: 400
📄 Response body: Bad Request
❌ Error response is not JSON: Bad Request
```

#### Working Homework API (for comparison)
```
📤 Request payload: {
  'requests': [{
    'moduleName': 'classbook',
    'endpointName': 'get-homework', 
    'parameters': {
      'student': {'id': 4333047}
    }
  }]
}

📥 Response status: 200
✅ Successfully parsed response JSON
```

## 🧪 Tested Variations

All following variations were tested and failed with identical 400 responses:

### 1. Full Student Object (Current Implementation)
```json
{
  "moduleName": "schedules",
  "endpointName": "get-actual-lessons",
  "parameters": {
    "student": {
      "id": 4333047,
      "firstname": "Marc Cedric", 
      "lastname": "Wunsch",
      "sex": "Male",
      "classId": 444612
    },
    "start": "2025-09-08",
    "end": "2025-09-22"
  }
}
```

### 2. Student ID Only
```json
{
  "moduleName": "schedules",
  "endpointName": "get-actual-lessons", 
  "parameters": {
    "student": {"id": 4333047},
    "start": "2025-09-08",
    "end": "2025-09-22"
  }
}
```

### 3. Different Endpoint Name
```json
{
  "moduleName": "schedules",
  "endpointName": "get-lessons",
  "parameters": {
    "student": {"id": 4333047},
    "start": "2025-09-08", 
    "end": "2025-09-22"
  }
}
```

### 4. No Date Range
```json
{
  "moduleName": "schedules",
  "endpointName": "get-actual-lessons",
  "parameters": {
    "student": {"id": 4333047}
  }
}
```

### 5. Legacy Format
```json
{
  "method": "schedules/get-actual-lessons",
  "data": {
    "studentId": 4333047,
    "start": "2025-09-08",
    "end": "2025-09-22"
  }
}
```

## 💡 Hypotheses

### 1. API Deprecation
- **Theory**: Schedule and Letters modules may have been deprecated or moved
- **Evidence**: Both return identical "Bad Request" responses
- **Next Step**: Check for alternative endpoints

### 2. Permission Requirements
- **Theory**: These modules require additional permissions or account types
- **Evidence**: Authentication works but specific modules fail
- **Next Step**: Test with different account types

### 3. Bundle Version Issue
- **Theory**: Current bundle version `"3505280ee7"` may be outdated
- **Evidence**: Working APIs use same bundle version, but these modules might require newer version
- **Next Step**: Investigate current bundle version from browser

### 4. Request Structure Changes
- **Theory**: These modules may require different request structure
- **Evidence**: Plain text "Bad Request" suggests fundamental request issue
- **Next Step**: Reverse engineer current browser requests

## 🔧 Debugging Steps Taken

### 1. Enhanced Logging ✅
- Added detailed request/response logging
- Confirmed exact request payload and response
- Verified authentication flow

### 2. Parameter Variations ✅
- Tested multiple parameter structures
- Tried different endpoint names
- Attempted legacy format

### 3. API Comparison ✅
- Confirmed working APIs (homework, exams) use same authentication
- Identified that only schedule/letters modules fail

## 🎯 Next Steps

### Immediate Actions
1. **Browser Network Analysis**: Capture actual working requests from browser
2. **Bundle Version Investigation**: Find current bundle version
3. **Alternative Endpoints**: Search for new schedule API endpoints
4. **Account Type Testing**: Test with different account permissions

### Investigation Priorities
1. **High Priority**: Browser request capture
2. **Medium Priority**: Bundle version update
3. **Low Priority**: Alternative authentication methods

## 📝 Technical Details

### Request Headers (Working)
```
Authorization: Bearer eyJhbGciOiJIU...
Content-Type: application/json
```

### Response Headers (Failing)
```
Content-Type: text/plain; charset=utf-8
Content-Length: 11
Cache-Control: no-cache
Etag: W/"b-EFiDB1U+dmqzx9Mo2UjcZ1SJPO8"
```

### Key Observations
- Response is plain text, not JSON
- ETag suggests cached error response
- Content-Length of 11 matches "Bad Request" exactly
- No additional error details provided

## 🔄 Status Updates

**2025-09-14 (Morning)**: Initial investigation completed
- Enhanced logging implemented
- Multiple parameter variations tested
- All variations fail with identical 400 responses
- Working APIs confirmed for comparison

**2025-09-14 (Afternoon)**: ✅ ISSUE RESOLVED!
- **Root Cause Found**: Missing `bundleVersion` parameter in HA integration
- **Solution Implemented**: Added `"bundleVersion": "3505280ee7"` to all API calls
- **Additional Fix**: Changed response parsing from `"responses"` to `"results"`
- **Result**: Both Schedule and Letters APIs now return 200 with actual data
- **Authentication Issue**: Fixed standalone scripts with correct password

## 🎯 Final Solution Summary

### Changes Made:
1. **Added bundleVersion to HA Integration**:
   ```python
   payload = {
       "bundleVersion": "3505280ee7",  # Required for API calls to work
       "requests": requests
   }
   ```

2. **Fixed Response Parsing**:
   ```python
   # Changed from:
   results = response.get("responses", [])
   # To:
   results = response.get("results", [])
   ```

3. **Updated Standalone Scripts**:
   - Fixed password credentials to match HA config
   - All test scripts now work correctly

### Verification:
- ✅ Schedule API: Returns 200 with lesson data (rooms, subjects, teachers)
- ✅ Letters API: Returns 200 with letter data (titles, dates, read status)
- ✅ Homework API: Still working perfectly
- ✅ Exams API: Still working perfectly

## 📋 Schedule API Response Structure

### Successful Schedule API Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-11",
          "classHour": {
            "id": 30172,
            "number": "5",
            "from": "11:41:00",
            "until": "12:26:00",
            "fromByDay": ["11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00"],
            "untilByDay": ["12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00"]
          },
          "type": "regularLesson",
          "actualLesson": {
            "room": {
              "id": 131134,
              "name": "RD205"
            },
            "subject": {
              "id": 255645,
              "abbreviation": "D",
              "name": "Deutsch",
              "isPseudoSubject": false
            },
            "teachers": [
              {
                "id": 370267,
                "abbreviation": "VolN",
                "firstname": "Nicole",
                "lastname": "Vollmer"
              }
            ],
            "classes": [
              {
                "id": 444612,
                "name": "7f"
              }
            ],
            "studentGroups": [
              {
                "id": 3575180,
                "name": "7f",
                "classId": 444612
              }
            ],
            "subjectLabel": "D",
            "lessonId": 18344522,
            "courseId": 7621162
          }
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

### Key Data Structure Notes:
- **Main Structure**: `results[0].data[]` contains the lesson array
- **Lesson Details**: Located in `actualLesson` object, not at root level
- **Time Information**: In `classHour` object with `from`/`until` fields
- **Subject Info**: Full name and abbreviation in `actualLesson.subject`
- **Teacher Info**: Array with firstname, lastname, and abbreviation
- **Room Info**: Object with id and name
- **Lesson Types**: `regularLesson`, `substitution`, `cancelledLesson`, etc.

### Processing Requirements:
1. Access lesson data via `lesson.actualLesson.*` not `lesson.*`
2. Time comes from `lesson.classHour.from/until`
3. Teacher info requires parsing firstname + lastname
4. Subject has both `name` (full) and `abbreviation` fields
5. Room name is in `actualLesson.room.name`

---

*Issue successfully resolved on September 14, 2025.*
