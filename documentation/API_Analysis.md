# Schulmanager Online API - Detailed Analysis

## 🎯 Overview

The Schulmanager Online API is a REST API that communicates over HTTPS and uses JWT tokens for authentication. The API requires special PBKDF2-SHA512 hash authentication.

## 🔗 API Endpoints

### Base URLs
- **Login/Auth**: `https://login.schulmanager-online.de/api/`
- **API Calls**: `https://login.schulmanager-online.de/api/calls`

### Authentication Endpoints

#### 1. Get Salt
```http
POST /api/salt
Content-Type: application/json

{
  "emailOrUsername": "user@example.com",
  "mobileApp": false,
  "institutionId": null
}
```

**Response:**
```json
"random_salt_string_here"
```

#### 2. Login with Hash
```http
POST /api/login
Content-Type: application/json

{
  "emailOrUsername": "user@example.com",
  "password": "original_password",
  "hash": "pbkdf2_sha512_hash_1024_chars",
  "mobileApp": false,
  "institutionId": null
}
```

**Response:**
```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2385948,
    "email": "user@example.com",
    "firstname": "Max",
    "lastname": "Mustermann",
    "associatedParents": [
      {
        "student": {
          "id": 4333047,
          "firstname": "Marc Cedric",
          "lastname": "Wunsch",
          "sex": "Male",
          "classId": 444612
        }
      }
    ]
  }
}
```

### Data Endpoints

#### 3. API Calls (Main Endpoint)

**Get Schedule:**
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
        "start": "2025-09-08",
        "end": "2025-09-14"
      }
    }
  ]
}
```

**Get Homework:**
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

**Get Exams:**
```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "exams",
      "endpointName": "get-exams",
      "parameters": {
        "student": {"id": 4333047},
        "start": "2025-09-14",
        "end": "2025-10-25"
      }
    }
  ]
}
```

## 🔐 Authentication Details

### PBKDF2-SHA512 Hashing

The API uses a special hash function based on PBKDF2-SHA512:

**Parameters:**
- **Algorithm**: PBKDF2 with SHA-512
- **Iterations**: 99,999
- **Output Length**: 512 bytes (4096 bits)
- **Hex Length**: 1024 characters
- **Salt Encoding**: UTF-8 (not Hex!)
- **Password Encoding**: UTF-8

**JavaScript Implementation (Original):**
```javascript
const hashBuffer = await crypto.subtle.deriveBits(
  {
    name: "PBKDF2",
    salt: new TextEncoder().encode(salt),
    iterations: 99999,
    hash: "SHA-512"
  },
  await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  ),
  4096  // 512 bytes * 8 bits = 4096 bits
);
```

**Python Implementation:**
```python
def _generate_salted_hash(self, password: str, salt: str) -> str:
    """Generate salted hash using PBKDF2-SHA512"""
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
    hash_hex = hash_bytes.hex()
    return hash_hex
```

### JWT Token Management

**Token Properties:**
- **Type**: JWT (JSON Web Token)
- **Validity**: 1 hour
- **Usage**: Authorization Header as Bearer Token
- **Renewal**: Automatic on expiry

## 📊 API Modules and Endpoints

### Schedules Module
- **`get-actual-lessons`**: Get current lessons
- **`get-class-hours`**: Get school hour schema

### Classbook Module
- **`get-homework`**: Get homework for a student

### Exams Module
- **`get-exams`**: Get exams/tests for a student

### Grades Module (Experimental)
- **`get-grades`**: Get grades for a student

### Available Parameters
- **`student`**: Student object with ID, name, gender, class ID
- **`start`**: Start date (ISO format: YYYY-MM-DD)
- **`end`**: End date (ISO format: YYYY-MM-DD)

## 🔄 API Response Structure

**IMPORTANT**: All API responses use `"results"` instead of `"responses"` as the main field!

### Schedule Response
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
            "startTime": "11:30",
            "endTime": "12:15"
          },
          "lesson": {
            "id": 123456,
            "subject": "Mathematics",
            "teacher": "Mr. Schmidt",
            "room": "R204"
          },
          "substitution": null
        }
      ]
    }
  ]
}
```

### Homework Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 12345,
          "subject": "Mathematics",
          "homework": "Problems p. 45, No. 1-10",
          "date": "2025-09-16",
          "teacher": "Mr. Schmidt",
          "completed": false,
          "createdAt": "2025-09-11T08:30:00.000Z"
        },
        {
          "id": 12346,
          "subject": "German",
          "homework": "Memorize poem",
          "date": "2025-09-17",
          "teacher": "Mrs. Müller",
          "completed": true,
          "createdAt": "2025-09-10T14:20:00.000Z"
        }
      ]
    }
  ]
}
```

### Exams Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 3163060,
          "subject": {
            "id": 255645,
            "name": "German",
            "abbreviation": "D"
          },
          "type": {
            "id": 2224,
            "name": "Class Test",
            "color": "#c6dcef",
            "visibleForStudents": true
          },
          "date": "2025-09-25",
          "startClassHour": {
            "id": 30172,
            "number": "5",
            "from": "11:41:00",
            "until": "12:26:00"
          },
          "comment": "",
          "createdAt": "2025-09-11T08:08:56.598Z",
          "updatedAt": "2025-09-11T08:08:56.598Z"
        }
      ]
    }
  ]
}
```

### Error Response
```json
{
  "results": [
    {
      "status": 400,
      "error": "Invalid parameters"
    }
  ]
}
```

## 🚨 Common API Problems

### 1. Authentication Failed (401)
- **Cause**: Wrong hash or expired token
- **Solution**: Check hash parameters, renew token

### 2. Student Data Not Found (400)
- **Cause**: Wrong API method or missing permission
- **Solution**: Extract student data from login response

### 3. Salt Retrieval Failed
- **Cause**: Missing parameters or wrong email
- **Solution**: Add `mobileApp: false` parameter

### 4. Schedule/Letters API 400 Bad Request (SOLVED!)
- **Cause**: Missing `bundleVersion` parameter in API requests
- **Solution**: Add `"bundleVersion": "3505280ee7"` to all API calls
- **bundleVersion Source**: Embedded in JavaScript bundle file (e.g., `main-SUJO2BNM.js`)
- **Dynamic Detection**: Integration detects bundleVersion automatically by:
  1. Fetching the main HTML page from `https://login.schulmanager-online.de`
  2. Extracting JavaScript bundle URLs from HTML
  3. Searching for bundleVersion in JavaScript files
  4. Caching detected version for 1 hour
- **Fallback**: When detection fails, uses known version `"3505280ee7"`
- **Symptoms (before)**: 
  - Authentication works perfectly
  - Homework and Exams APIs work (had bundleVersion in standalone tests)
  - Schedule and Letters APIs returned identical 400 errors
  - Server response: Plain text "Bad Request" instead of JSON
- **Status**: ✅ FIXED + DYNAMIC DETECTION IMPLEMENTED
- **Additional Fixes**:
  1. Response structure changed from `"responses"` to `"results"`
  2. All API calls need bundleVersion parameter
  3. Standalone scripts need correct password credentials
  4. Dynamic bundleVersion detection implemented

## 🔍 Reverse Engineering Insights

### JavaScript Files Analyzed:
- **`chunk-M5BNGULW.js`**: Contains hash function `SWe`
- **`main-SUJO2BNM.js`**: Contains login logic

### Important Findings:
1. **Salt is returned as string**, not as JSON object
2. **Hash iterations are 99,999**, not 10,000
3. **Output length is 512 bytes**, not 256
4. **Salt encoding is UTF-8**, not Hex

## 📝 API Versioning

- **Bundle Version**: `3505280ee7` (current)
- **API Version**: Not explicitly versioned
- **Compatibility**: Backward compatible

## 🔧 Implementation Notes

1. **Session Management**: Use `aiohttp.ClientSession` for connection pooling
2. **Error Handling**: Implement retry logic for temporary errors
3. **Rate Limiting**: Observe API limits (not documented)
4. **Caching**: Cache student data from login response
5. **Logging**: Detailed logging for debugging

## 📚 Further Documentation

- [Authentication Guide](Authentication_Guide.md) - Detailed authentication
- [API Implementation](API_Implementation.md) - Python implementation
- [Troubleshooting](Troubleshooting_Guide.md) - Problem solutions
