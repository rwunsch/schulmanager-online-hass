# Schulmanager Online - Schedules API Documentation

## 🎯 Overview

The Schedules API is part of the Schulmanager Online API system that provides access to student schedules and class hour configurations. This documentation is based on actual API calls and responses from the live system.

**Generated on:** September 15, 2025  
**API Version:** Current (Bundle Version: 3505280ee7)  
**Test Data:** Live API responses from authenticated session

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Base Configuration](#base-configuration)
3. [API Endpoints](#api-endpoints)
   - [Get Actual Lessons](#get-actual-lessons)
   - [Get Class Hours](#get-class-hours)
4. [Data Structures](#data-structures)
5. [Response Examples](#response-examples)
6. [Error Handling](#error-handling)
7. [Testing Results](#testing-results)
8. [Implementation Notes](#implementation-notes)

---

## 🔐 Authentication

The Schedules API uses the same authentication system as all other Schulmanager Online APIs:

1. **Get Salt** from `/api/salt`
2. **Generate PBKDF2-SHA512 Hash** with 99,999 iterations
3. **Login** with hash to get JWT token
4. **Use JWT Token** in Authorization header for API calls

For detailed authentication, see [Authentication Guide](Authentication_Guide.md).

**Required Headers:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## ⚙️ Base Configuration

### API Endpoints
- **Base URL:** `https://login.schulmanager-online.de`
- **API Calls Endpoint:** `https://login.schulmanager-online.de/api/calls`

### Required Parameters
- **bundleVersion:** `"3505280ee7"` (required for all API calls)
- **Student Object:** Complete student information from login response

---

## 🔗 API Endpoints

### Get Actual Lessons

Retrieves lessons for a student within a specified date range.

#### Request Format

```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
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
        "start": "2025-09-15",
        "end": "2025-09-21"
      }
    }
  ]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student` | Object | ✅ | Complete student object from login response |
| `student.id` | Integer | ✅ | Student ID |
| `student.firstname` | String | ✅ | Student's first name |
| `student.lastname` | String | ✅ | Student's last name |
| `student.sex` | String | ✅ | Student's gender ("Male" or "Female") |
| `student.classId` | Integer | ✅ | Student's class ID |
| `start` | String | ✅ | Start date in ISO format (YYYY-MM-DD) |
| `end` | String | ✅ | End date in ISO format (YYYY-MM-DD) |

#### Response Structure

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-18",
          "classHour": {
            "id": 30172,
            "number": "5"
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

### Get Class Hours

Retrieves the class hour schedule configuration for a specific class.

#### Request Format

```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "schedules",
      "endpointName": "get-class-hours",
      "parameters": {
        "classId": 444612
      }
    }
  ]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `classId` | Integer | ✅ | Class ID from student object |

#### Response Structure

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 30169,
          "number": "2",
          "from": "08:48:00",
          "until": "09:33:00",
          "fromByDay": [
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00"
          ],
          "untilByDay": [
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00"
          ]
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

---

## 📊 Data Structures

### Lesson Object

A lesson object contains the following structure:

```typescript
interface Lesson {
  date: string;                    // ISO date (YYYY-MM-DD)
  classHour: ClassHour;           // Class hour information
  type: LessonType;               // Lesson type (see LessonType enum below)
  actualLesson?: ActualLesson;    // Detailed lesson information (for regular/changed lessons)
  originalLessons?: ActualLesson[]; // Original lesson data (for cancelled/changed lessons)
  event?: EventDetails;           // Event information (for event type lessons)
  comment?: string;               // Additional comments
  isCancelled?: boolean;          // True if lesson is cancelled
  isSubstitution?: boolean;       // True if lesson is a substitution
  isNew?: boolean;                // True if lesson is newly added
}
```

### Lesson Types

The API supports several lesson types that indicate the nature of the lesson:

```typescript
enum LessonType {
  "regularLesson"    // Normal scheduled lesson
  "cancelledLesson"  // Lesson that has been cancelled
  "changedLesson"    // Lesson with substitution/changes
  "event"           // Special event or activity
}
```

#### Lesson Type Details

| Type | Description | Contains | Use Case |
|------|-------------|----------|----------|
| `regularLesson` | Normal scheduled lesson | `actualLesson` | Standard daily lessons |
| `cancelledLesson` | Cancelled lesson | `originalLessons`, `isCancelled: true` | Lessons that are cancelled without replacement |
| `changedLesson` | Modified lesson | `actualLesson`, `originalLessons`, `isSubstitution: true` | Teacher substitutions, room changes |
| `event` | Special event/activity | `event` object | School events, special activities, trips |

#### Handling Multiple Entries

**Important**: When lessons are cancelled and replaced (e.g., by school events), the API returns **multiple entries for the same time slot**:

1. **Cancelled Lesson Entry**: `type: "cancelledLesson"` with original lesson data
2. **Replacement Entry**: `type: "event"` with event details

This allows applications to:
- Show what was originally planned (crossed out)
- Display the replacement activity
- Track schedule changes for notifications

### Class Hour Object

```typescript
interface ClassHour {
  id: number;                     // Unique class hour ID
  number: string;                 // Hour number (e.g., "1", "2", "5")
}
```

### Actual Lesson Object

```typescript
interface ActualLesson {
  room: Room;                     // Room information
  subject: Subject;               // Subject details
  teachers: Teacher[];            // Array of teachers
  classes: Class[];               // Array of classes
  studentGroups: StudentGroup[];  // Array of student groups
  subjectLabel: string;           // Short subject label
  lessonId: number;               // Unique lesson ID
  courseId: number;               // Course ID
}
```

### Room Object

```typescript
interface Room {
  id: number;                     // Unique room ID
  name: string;                   // Room name (e.g., "RD205")
}
```

### Subject Object

```typescript
interface Subject {
  id: number;                     // Unique subject ID
  abbreviation: string;           // Short abbreviation (e.g., "D")
  name: string;                   // Full subject name (e.g., "Deutsch")
  isPseudoSubject: boolean;       // Whether it's a pseudo subject
}
```

### Teacher Object

```typescript
interface Teacher {
  id: number;                     // Unique teacher ID
  abbreviation: string;           // Teacher abbreviation (e.g., "VolN")
  firstname: string;              // Teacher's first name
  lastname: string;               // Teacher's last name
}
```

### Event Details Object

```typescript
interface EventDetails {
  text: string;                   // Event description/title
  teachers: Teacher[];            // Teachers involved in the event
  classes: Class[];               // Classes participating
  rooms: Room[];                  // Rooms used (may be empty for events)
  studentGroups: StudentGroup[];  // Student groups involved
  absenceId?: number;             // Associated absence/event ID
}
```

### Class Hours Configuration Object

```typescript
interface ClassHourConfig {
  id: number;                     // Unique class hour ID
  number: string;                 // Hour number
  from: string;                   // Start time (HH:MM:SS)
  until: string;                  // End time (HH:MM:SS)
  fromByDay: string[];            // Start times by day of week (7 entries)
  untilByDay: string[];           // End times by day of week (7 entries)
}
```

---

## 📝 Response Examples

### 1. Regular Lesson Response

Standard lesson with normal schedule:

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-18",
          "classHour": {
            "id": 30172,
            "number": "5"
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

### 2. Cancelled Lesson Response

Lesson that has been cancelled (often paired with replacement event):

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-19",
          "comment": null,
          "classHour": {
            "id": 30168,
            "number": "1"
          },
          "type": "cancelledLesson",
          "originalLessons": [
            {
              "room": {
                "id": 131223,
                "name": "RSpoN2"
              },
              "subject": {
                "id": 255690,
                "abbreviation": "SP",
                "name": "Sport",
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
              "subjectLabel": "SP",
              "lessonId": 18344545,
              "courseId": 7621169
            }
          ],
          "isCancelled": true
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

### 3. Event Response

Special event or activity (often replaces cancelled lessons):

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-19",
          "classHour": {
            "id": 30168,
            "number": "1"
          },
          "type": "event",
          "event": {
            "text": "Klassenlehrerunterricht und Westenergielauf",
            "teachers": [
              {
                "id": 370267,
                "abbreviation": "VolN",
                "firstname": "Nicole",
                "lastname": "Vollmer"
              },
              {
                "id": 370251,
                "abbreviation": "StuF",
                "firstname": "Frank",
                "lastname": "Stuckstedte"
              }
            ],
            "classes": [
              {
                "id": 444612,
                "name": "7f"
              }
            ],
            "rooms": [],
            "studentGroups": [
              {
                "id": 3575180,
                "name": "7f",
                "classId": 444612
              }
            ],
            "absenceId": 2838410
          },
          "isSubstitution": false,
          "isNew": true
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

### 4. Changed Lesson Response

Lesson with substitution or room change:

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-15",
          "comment": "Raumwechsel beachten",
          "classHour": {
            "id": 30171,
            "number": "4"
          },
          "type": "changedLesson",
          "actualLesson": {
            "room": {
              "id": 131134,
              "name": "RD205"
            },
            "subject": {
              "id": 255690,
              "abbreviation": "SP",
              "name": "Sport",
              "isPseudoSubject": false
            },
            "teachers": [
              {
                "id": 370258,
                "abbreviation": "LenJ",
                "firstname": "Jana",
                "lastname": "Lenkenhoff"
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
            "comment": "Raumwechsel beachten",
            "subjectLabel": "SP",
            "substitutionId": 35035100
          },
          "originalLessons": [
            {
              "room": {
                "id": 131223,
                "name": "RSpoN2"
              },
              "subject": {
                "id": 255690,
                "abbreviation": "SP",
                "name": "Sport",
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
              "subjectLabel": "SP",
              "lessonId": 18344544,
              "courseId": 7621169
            }
          ],
          "isSubstitution": true,
          "isNew": false
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

### Successful Class Hours Response

```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 30168,
          "number": "1",
          "from": "08:00:00",
          "until": "08:45:00",
          "fromByDay": [
            "08:00:00",
            "08:00:00",
            "08:00:00",
            "08:00:00",
            "08:00:00",
            "08:00:00",
            "08:00:00"
          ],
          "untilByDay": [
            "08:45:00",
            "08:45:00",
            "08:45:00",
            "08:45:00",
            "08:45:00",
            "08:45:00",
            "08:45:00"
          ]
        },
        {
          "id": 30169,
          "number": "2",
          "from": "08:48:00",
          "until": "09:33:00",
          "fromByDay": [
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00",
            "08:48:00"
          ],
          "untilByDay": [
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00",
            "09:33:00"
          ]
        }
      ]
    }
  ],
  "systemStatusMessages": []
}
```

---

## ❌ Error Handling

### Common Error Responses

Based on actual testing, the API returns the following error responses:

#### 1. Invalid Student ID (403 Forbidden)
```json
{
  "results": [
    {
      "status": 403,
      "error": "Access denied or invalid student"
    }
  ]
}
```

#### 2. Invalid Date Format (500 Internal Server Error)
```json
{
  "results": [
    {
      "status": 500,
      "error": "Invalid date format"
    }
  ]
}
```

#### 3. Missing Parameters (403 Forbidden)
```json
{
  "results": [
    {
      "status": 403,
      "error": "Missing required parameters"
    }
  ]
}
```

### HTTP Status Codes

| HTTP Code | API Status | Description | Action Required |
|-----------|------------|-------------|-----------------|
| 200 | 200 | Success | Process data normally |
| 200 | 403 | Forbidden | Check student ID and permissions |
| 200 | 500 | Server Error | Check parameters, retry later |
| 401 | N/A | Unauthorized | Re-authenticate |
| 400 | N/A | Bad Request | Check bundleVersion parameter |

---

## 🧪 Testing Results

### Live API Testing Summary

**Test Date:** September 15, 2025  
**Authentication:** ✅ Successful  
**Student Account:** Marc Cedric Wunsch (ID: 4333047)

#### Get Actual Lessons Tests

| Date Range | Days | Lessons Found | Status |
|------------|------|---------------|--------|
| Today (2025-09-15) | 1 | 8 | ✅ Success |
| Tomorrow (2025-09-16) | 1 | 5 | ✅ Success |
| This Week (2025-09-15 to 2025-09-21) | 7 | 42 | ✅ Success |
| Next Week (2025-09-22 to 2025-09-28) | 7 | 36 | ✅ Success |
| Two Weeks (2025-09-15 to 2025-09-28) | 14 | 78 | ✅ Success |
| Past Week (2025-09-08 to 2025-09-14) | 7 | 36 | ✅ Success |

#### Get Class Hours Test

- **Class ID:** 444612
- **Total Hours:** 11 class periods
- **Status:** ✅ Success
- **Time Range:** 08:00:00 to 16:35:00

#### Error Case Tests

| Test Case | Expected Result | Actual Result | Status |
|-----------|----------------|---------------|--------|
| Invalid Student ID | 403 Error | 403 Error | ✅ Pass |
| Invalid Date Format | 500 Error | 500 Error | ✅ Pass |
| Missing Parameters | 403 Error | 403 Error | ✅ Pass |

---

## 💡 Implementation Notes

### Date Range Recommendations

Based on testing results:

- **Single Day:** Returns 5-8 lessons typically
- **One Week:** Returns 30-42 lessons typically
- **Two Weeks:** Optimal for schedule overview (78 lessons)
- **Past Data:** API supports historical data retrieval

### Performance Considerations

1. **Response Size:** Week-long requests return manageable data sizes
2. **Rate Limiting:** No specific limits observed during testing
3. **Caching:** Consider caching class hours (rarely change)
4. **Bundle Version:** Must be updated when Schulmanager updates

### Data Processing Tips

1. **Lesson Types:** Currently observed: `"regularLesson"`
2. **Time Parsing:** Times are in `HH:MM:SS` format
3. **Subject Labels:** Use `subjectLabel` for short display, `subject.name` for full name
4. **Teacher Display:** Use `abbreviation` for compact view, full name for details
5. **Room Names:** Direct display from `room.name`

### Integration Patterns

```python
# Recommended date range for schedule overview
start_date = date.today()
end_date = start_date + timedelta(days=13)  # Two weeks

# Process lessons by date
lessons_by_date = {}
for lesson in response_data:
    lesson_date = lesson["date"]
    if lesson_date not in lessons_by_date:
        lessons_by_date[lesson_date] = []
    lessons_by_date[lesson_date].append(lesson)

# Extract time from class hours for display
def format_lesson_time(lesson, class_hours_map):
    class_hour = lesson["classHour"]
    hour_config = class_hours_map.get(class_hour["id"])
    if hour_config:
        return f"{hour_config['from'][:5]}-{hour_config['until'][:5]}"
    return f"Hour {class_hour['number']}"
```

---

## 📚 Related Documentation

- [API Analysis](API_Analysis.md) - Complete API overview
- [API Implementation](API_Implementation.md) - Python client implementation
- [Authentication Guide](Authentication_Guide.md) - Authentication details
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Common problems and solutions

---

## 📊 API Testing Data

Complete test results and raw API responses are available in:
- `test-scripts/schedules_api_test_results.json` - Full test results
- `test-scripts/schedules_api_tester.py` - Test script for reproduction

---

**Last Updated:** September 15, 2025  
**Tested Against:** Live Schulmanager Online API  
**Bundle Version:** 3505280ee7
