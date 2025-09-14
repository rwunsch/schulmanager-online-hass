# Letters API Documentation

## Overview

The Letters API provides access to Elternbriefe (parent letters/messages) from Schulmanager Online. This includes official communications from the school to parents, announcements, and documents with attachments.

## API Endpoints

### 1. Get Letters List

**Endpoint**: `letters/get-letters`  
**Method**: POST  
**Module**: `letters`

Retrieves a list of all available letters for the authenticated user.

#### Request Format
```json
{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": null,
      "endpointName": "user-can-get-notifications"
    },
    {
      "moduleName": "letters",
      "endpointName": "get-letters"
    }
  ]
}
```

#### Response Structure
```json
{
  "responses": [
    {
      "status": 200,
      "data": {
        // Notification permissions response
      }
    },
    {
      "status": 200,
      "data": [
        {
          "id": 1725733,
          "subject": "Wichtige Mitteilung",
          "content": "Brief content...",
          "from": "Schulleitung",
          "createdAt": "2024-01-15T10:30:00Z",
          "read": false,
          "confirmed": false,
          "attachments": [
            {
              "id": 12345,
              "filename": "document.pdf",
              "contentType": "application/pdf"
            }
          ]
        }
      ]
    }
  ]
}
```

### 2. Get Letter Details

**Endpoint**: `letters/poqa`  
**Method**: POST  
**Module**: `letters`

Retrieves detailed information for a specific letter, including attachments and student status.

#### Request Format
```json
{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "letters",
      "endpointName": "poqa",
      "parameters": {
        "action": {
          "model": "modules/letters/letter",
          "action": "findByPk",
          "parameters": [
            1725733,  // Letter ID
            {
              "include": [
                {
                  "association": "attachments",
                  "required": false,
                  "attributes": ["id", "filename", "file", "contentType", "inline", "letterId"]
                },
                {
                  "association": "studentStatuses",
                  "required": true,
                  "where": {"studentId": {"$in": [4333047]}},
                  "include": [{"association": "student", "required": true}]
                }
              ]
            }
          ]
        },
        "uiState": "main.modules.letters.view.details"
      }
    },
    {
      "moduleName": "letters",
      "endpointName": "get-translation-languages"
    }
  ]
}
```

#### Response Structure
```json
{
  "responses": [
    {
      "status": 200,
      "data": {
        "id": 1725733,
        "subject": "Wichtige Mitteilung",
        "content": "Detailed letter content with HTML formatting...",
        "from": "Schulleitung",
        "createdAt": "2024-01-15T10:30:00Z",
        "attachments": [
          {
            "id": 12345,
            "filename": "elternbrief.pdf",
            "file": "base64-encoded-content",
            "contentType": "application/pdf",
            "inline": false,
            "letterId": 1725733
          }
        ],
        "studentStatuses": [
          {
            "studentId": 4333047,
            "read": true,
            "confirmed": false,
            "readAt": "2024-01-15T14:20:00Z",
            "student": {
              "id": 4333047,
              "firstname": "Marc Cedric",
              "lastname": "Wunsch"
            }
          }
        ]
      }
    },
    {
      "status": 200,
      "data": {
        // Translation languages response
      }
    }
  ]
}
```

## Data Models

### Letter Object
```typescript
interface Letter {
  id: number;
  subject: string;
  content: string;
  from: string;
  createdAt: string;  // ISO 8601 timestamp
  read: boolean;
  confirmed: boolean;
  attachments?: Attachment[];
  studentStatuses?: StudentStatus[];
}
```

### Attachment Object
```typescript
interface Attachment {
  id: number;
  filename: string;
  file?: string;  // Base64 encoded content (only in details)
  contentType: string;
  inline: boolean;
  letterId: number;
}
```

### Student Status Object
```typescript
interface StudentStatus {
  studentId: number;
  read: boolean;
  confirmed: boolean;
  readAt?: string;  // ISO 8601 timestamp
  student: {
    id: number;
    firstname: string;
    lastname: string;
  };
}
```

## Implementation in Home Assistant

### API Client Methods

#### `get_letters()`
Retrieves the list of all letters for the authenticated user.

```python
async def get_letters(self) -> Dict[str, Any]:
    """Get letters (Elternbriefe) for the user."""
    requests = [
        {
            "moduleName": None,
            "endpointName": "user-can-get-notifications"
        },
        {
            "moduleName": "letters",
            "endpointName": "get-letters"
        }
    ]
    
    response = await self._make_api_call(requests)
    responses = response.get("responses", [])
    
    if len(responses) < 2:
        raise SchulmanagerAPIError("Incomplete letters response")
    
    letters_data = responses[1]  # Second response is the letters
    
    if letters_data.get("status") != 200:
        raise SchulmanagerAPIError(f"Letters API error: {letters_data.get('status')}")
    
    return letters_data
```

#### `get_letter_details(letter_id, student_id)`
Retrieves detailed information for a specific letter.

```python
async def get_letter_details(self, letter_id: int, student_id: int) -> Dict[str, Any]:
    """Get detailed information for a specific letter including attachments."""
    requests = [
        {
            "moduleName": "letters",
            "endpointName": "poqa",
            "parameters": {
                "action": {
                    "model": "modules/letters/letter",
                    "action": "findByPk",
                    "parameters": [
                        letter_id,
                        {
                            "include": [
                                {
                                    "association": "attachments",
                                    "required": False,
                                    "attributes": ["id", "filename", "file", "contentType", "inline", "letterId"]
                                },
                                {
                                    "association": "studentStatuses",
                                    "required": True,
                                    "where": {"studentId": {"$in": [student_id]}},
                                    "include": [{"association": "student", "required": True}]
                                }
                            ]
                        }
                    ]
                },
                "uiState": "main.modules.letters.view.details"
            }
        },
        {
            "moduleName": "letters",
            "endpointName": "get-translation-languages"
        }
    ]
    
    response = await self._make_api_call(requests)
    responses = response.get("responses", [])
    
    if not responses:
        raise SchulmanagerAPIError("No letter details response")
    
    letter_data = responses[0]
    
    if letter_data.get("status") != 200:
        raise SchulmanagerAPIError(f"Letter details API error: {letter_data.get('status')}")
    
    return letter_data
```

### Configuration

The Letters API can be enabled/disabled via the integration configuration:

```python
# In config_flow.py
vol.Optional("include_letters", default=True): bool
```

### Data Coordinator Integration

Letters are fetched account-wide (not per student) in the coordinator:

```python
# Get letters (Elternbriefe) - these are account-wide, not per student
include_letters = self.options.get("include_letters", True)
if include_letters:
    try:
        letters_data = await self.api.get_letters()
        data["letters"] = letters_data
        _LOGGER.debug("Retrieved %d letters", len(letters_data.get("data", [])))
    except SchulmanagerAPIError as e:
        _LOGGER.warning("Failed to get letters: %s", e)
        data["letters"] = {"data": []}
```

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid parameters or malformed request
- **401 Unauthorized**: Invalid or expired authentication token
- **403 Forbidden**: Insufficient permissions to access letters
- **404 Not Found**: Letter ID does not exist
- **500 Internal Server Error**: Server-side error

### Current Issues

As of the current implementation, the Letters API returns a 400 error:

```
ERROR [custom_components.schulmanager_online.api] Failed to get letters: API call failed: 400
```

This suggests that the API parameters or request format may need adjustment. The exact cause is under investigation.

## Future Enhancements

### Planned Features

1. **Letter Sensors**: Create Home Assistant sensors for:
   - Unread letters count
   - Recent letters
   - Letters requiring confirmation

2. **Calendar Integration**: Display letter dates in Home Assistant calendar

3. **Custom Card Integration**: Add letters view to the custom Lovelace card

4. **Notification Service**: Send Home Assistant notifications for new letters

### Sensor Implementation (Planned)

```python
# Example sensor for unread letters count
def get_unread_letters_count(letters_data: Dict[str, Any]) -> int:
    """Get count of unread letters."""
    letters = letters_data.get("data", [])
    return len([letter for letter in letters if not letter.get("read", True)])
```

## Testing

### Manual Testing with curl

```bash
# Get letters list
curl 'https://login.schulmanager-online.de/api/calls' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'content-type: application/json' \
  --data-raw '{"bundleVersion":"3505280ee7","requests":[{"moduleName":null,"endpointName":"user-can-get-notifications"},{"moduleName":"letters","endpointName":"get-letters"}]}'

# Get letter details
curl 'https://login.schulmanager-online.de/api/calls' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'content-type: application/json' \
  --data-raw '{"bundleVersion":"3505280ee7","requests":[{"moduleName":"letters","endpointName":"poqa","parameters":{"action":{"model":"modules/letters/letter","action":"findByPk","parameters":[LETTER_ID,{"include":[{"association":"attachments","required":false,"attributes":["id","filename","file","contentType","inline","letterId"]},{"association":"studentStatuses","required":true,"where":{"studentId":{"$in":[STUDENT_ID]}},"include":[{"association":"student","required":true}]}]}]},"uiState":"main.modules.letters.view.details"}},{"moduleName":"letters","endpointName":"get-translation-languages"}]}'
```

## Security Considerations

1. **Authentication**: All requests require valid JWT token
2. **Student Privacy**: Letter details are filtered by student ID
3. **Attachment Handling**: Large attachments should be handled carefully
4. **Data Storage**: Consider caching policies for letter content

## Troubleshooting

### Common Issues

1. **400 Error**: Check request format and parameters
2. **Empty Response**: Verify user has access to letters
3. **Missing Attachments**: Check attachment permissions and file size limits

### Debug Logging

Enable debug logging to see detailed API requests:

```python
_LOGGER.debug("Letters API request: %s", requests)
_LOGGER.debug("Letters API response: %s", response)
```
