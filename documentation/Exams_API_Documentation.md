# Klassenarbeiten-API - Detaillierte Dokumentation

## 🎯 Übersicht

Die Klassenarbeiten-API ermöglicht das Abrufen von Klassenarbeiten, Tests und Lernkontrollen für Schüler über das `exams`-Modul der Schulmanager Online API. Diese Dokumentation beschreibt die Implementierung, Datenstrukturen und Verwendung.

## 📡 API-Endpunkt

### Klassenarbeiten abrufen

**Endpunkt**: `exams/get-exams`
**Methode**: POST
**Modul**: `exams`

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

### Parameter

| Parameter | Typ | Beschreibung | Erforderlich |
|-----------|-----|--------------|--------------|
| `student.id` | `number` | ID des Schülers | ✅ |
| `start` | `string` | Start-Datum (YYYY-MM-DD) | ✅ |
| `end` | `string` | End-Datum (YYYY-MM-DD) | ✅ |

## 📊 Response-Struktur

### Erfolgreiche Response

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
            "name": "Deutsch",
            "abbreviation": "D"
          },
          "type": {
            "id": 2224,
            "name": "Klassenarbeit",
            "color": "#c6dcef",
            "visibleForStudents": true
          },
          "date": "2025-09-25",
          "startClassHour": {
            "id": 30172,
            "number": "5",
            "from": "11:41:00",
            "until": "12:26:00",
            "fromByDay": ["11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00", "11:41:00"],
            "untilByDay": ["12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00", "12:26:00"]
          },
          "endClassHour": null,
          "comment": "",
          "subjectText": null,
          "createdAt": "2025-09-11T08:08:56.598Z",
          "updatedAt": "2025-09-11T08:08:56.598Z"
        },
        {
          "id": 3163061,
          "subject": {
            "id": 255652,
            "name": "Englisch, Beginn in Jahrgangsklasse 5",
            "abbreviation": "E"
          },
          "type": {
            "id": 2225,
            "name": "Test",
            "color": "#ffeb3b",
            "visibleForStudents": true
          },
          "date": "2025-10-02",
          "startClassHour": {
            "id": 30170,
            "number": "3",
            "from": "09:45:00",
            "until": "10:30:00"
          },
          "comment": "Vocabulary Unit 1-3",
          "createdAt": "2025-09-11T08:10:15.234Z",
          "updatedAt": "2025-09-11T08:10:15.234Z"
        }
      ]
    }
  ]
}
```

### Datenfeld-Beschreibung

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | `number` | Eindeutige ID der Klassenarbeit |
| `subject` | `object` | Fach-Informationen |
| `subject.id` | `number` | Fach-ID |
| `subject.name` | `string` | Vollständiger Fach-Name |
| `subject.abbreviation` | `string` | Fach-Kürzel (z.B. "D", "M", "E") |
| `type` | `object` | Prüfungstyp-Informationen |
| `type.id` | `number` | Typ-ID |
| `type.name` | `string` | Typ-Name (z.B. "Klassenarbeit", "Test") |
| `type.color` | `string` | Hex-Farbcode für UI-Darstellung |
| `type.visibleForStudents` | `boolean` | Sichtbarkeit für Schüler |
| `date` | `string` | Prüfungsdatum (YYYY-MM-DD) |
| `startClassHour` | `object` | Schulstunden-Informationen |
| `startClassHour.number` | `string` | Stundennummer |
| `startClassHour.from` | `string` | Startzeit (HH:MM:SS) |
| `startClassHour.until` | `string` | Endzeit (HH:MM:SS) |
| `comment` | `string` | Zusätzliche Kommentare/Hinweise |
| `createdAt` | `string` | Erstellungsdatum (ISO-Format) |
| `updatedAt` | `string` | Letzte Aktualisierung (ISO-Format) |

## 🐍 Python-Implementierung

### API-Client-Methode

```python
async def get_exams(self, student_id: int, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """Get exams/tests for a student in a date range."""
    requests = [
        {
            "moduleName": "exams",
            "endpointName": "get-exams",
            "parameters": {
                "student": {"id": student_id},
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        responses = response.get("responses", [])
        
        if not responses:
            raise SchulmanagerAPIError("No exams response")
        
        exams_data = responses[0]
        exams = exams_data.get("exams", exams_data.get("data", []))
        
        _LOGGER.debug("Found %d exams for student %d", len(exams), student_id)
        
        return exams_data
        
    except Exception as e:
        _LOGGER.error("Failed to get exams for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get exams: {e}") from e
```

### Coordinator-Integration

```python
# In coordinator.py
async def _async_update_data(self):
    """Update data including exams."""
    
    # Get exams if enabled
    if include_exams:
        try:
            # Get exams for extended period (8 weeks for better coverage)
            exam_start_date = today - timedelta(weeks=1)  # Include past week
            exam_end_date = start_date + timedelta(weeks=8)  # Extended range
            exams_data = await self.api.get_exams(student_id, exam_start_date, exam_end_date)
            student_data["exams"] = exams_data
        except SchulmanagerAPIError as e:
            _LOGGER.warning("Failed to get exams for %s: %s", student_name, e)
            student_data["exams"] = {"exams": []}
```

## 📊 Sensor-Integration

### Klassenarbeiten-Sensoren

Die Klassenarbeiten-API wird in 4 verschiedene Sensoren integriert:

1. **Exams Today** - Heute anstehende Klassenarbeiten
2. **Exams This Week** - Klassenarbeiten dieser Woche
3. **Exams Next Week** - Klassenarbeiten nächster Woche
4. **Exams Upcoming** - Kommende Klassenarbeiten (30 Tage)

### Sensor-Logik

```python
def get_exams_today_count(student_data: Dict[str, Any]) -> str:
    """Get count of exams today."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date().isoformat()
    exams_today = [exam for exam in exams if exam.get("date") == today]
    return str(len(exams_today))

def get_exams_this_week_attributes(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get attributes for exams this week sensor."""
    exams_data = student_data.get("exams", {})
    exams = _extract_exams(exams_data)
    
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    monday_str = monday.isoformat()
    friday_str = friday.isoformat()
    
    exams_this_week = [exam for exam in exams 
                      if monday_str <= exam.get("date", "") <= friday_str]
    
    # Sort by date
    exams_this_week.sort(key=lambda x: x.get("date", ""))
    
    # Get unique subjects
    subjects = set()
    for exam in exams_this_week:
        subject = exam.get("subject", {})
        if isinstance(subject, dict):
            subjects.add(subject.get("name", "Unknown"))
        else:
            subjects.add(str(subject))
    
    attributes = {
        "exams": [_format_exam_info(exam) for exam in exams_this_week],
        "count": len(exams_this_week),
        "subjects": sorted(list(subjects)),
    }
    return attributes
```

### Daten-Transformation

```python
def _format_exam_info(exam: Dict[str, Any]) -> Dict[str, Any]:
    """Format exam data for consistent output."""
    # Extract subject name
    subject = exam.get("subject", {})
    subject_name = subject.get("name", "Unknown") if isinstance(subject, dict) else str(subject)
    
    # Extract exam type
    exam_type = exam.get("type", {})
    type_name = exam_type.get("name", "Exam") if isinstance(exam_type, dict) else str(exam_type)
    
    # Extract time from startClassHour
    start_class_hour = exam.get("startClassHour", {})
    time_str = ""
    class_hour_number = ""
    
    if isinstance(start_class_hour, dict):
        time_from = start_class_hour.get("from", "")
        time_until = start_class_hour.get("until", "")
        if time_from and time_until:
            time_str = f"{time_from[:5]}-{time_until[:5]}"  # Format: HH:MM-HH:MM
        elif time_from:
            time_str = time_from[:5]
        class_hour_number = start_class_hour.get("number", "")
    
    return {
        "subject": subject_name,
        "subject_abbreviation": subject.get("abbreviation", "") if isinstance(subject, dict) else "",
        "title": exam.get("title", exam.get("name", type_name)),
        "date": exam.get("date", ""),
        "time": time_str,
        "class_hour": class_hour_number,
        "room": exam.get("room", ""),  # May be empty in current data
        "teacher": exam.get("teacher", ""),  # May be empty in current data
        "type": type_name,
        "type_color": exam_type.get("color", "") if isinstance(exam_type, dict) else "",
        "comment": exam.get("comment", ""),
        "days_until": calculate_days_until(exam.get("date", "")),
    }
```

### Prüfungstyp-Prioritäten

```python
def get_exam_priority(exam: Dict[str, Any]) -> int:
    """Get exam priority for sorting (lower number = higher priority)."""
    exam_type = exam.get("type", {})
    if isinstance(exam_type, dict):
        type_name = exam_type.get("name", "").lower()
    else:
        type_name = str(exam_type).lower()
    
    # Priority order: Klassenarbeit > Test > Lernkontrolle > other
    if "klassenarbeit" in type_name or "klausur" in type_name:
        return 1
    elif "test" in type_name:
        return 2
    elif "lernkontrolle" in type_name or "lk" in type_name:
        return 3
    else:
        return 4
```

## 🎨 Farbkodierung

### Standard-Farben

| Prüfungstyp | Hex-Code | RGB | Beschreibung |
|-------------|----------|-----|--------------|
| **Klassenarbeit** | `#c6dcef` | (198, 220, 239) | Hellblau |
| **Test** | `#ffeb3b` | (255, 235, 59) | Gelb |
| **Lernkontrolle** | `#81c784` | (129, 199, 132) | Hellgrün |
| **Klausur** | `#f48fb1` | (244, 143, 177) | Rosa |

### UI-Integration

```python
def get_exam_color_class(exam_type: str) -> str:
    """Get CSS class for exam type color."""
    type_lower = exam_type.lower()
    
    if "klassenarbeit" in type_lower:
        return "exam-klassenarbeit"
    elif "test" in type_lower:
        return "exam-test"
    elif "lernkontrolle" in type_lower:
        return "exam-lernkontrolle"
    elif "klausur" in type_lower:
        return "exam-klausur"
    else:
        return "exam-default"
```

## 🧪 Test-Implementation

### Test-Script

```python
#!/usr/bin/env python3
"""Test script for Exams API."""

import asyncio
import aiohttp
from datetime import datetime, timedelta

async def test_exams_api():
    """Test exams API functionality."""
    
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
            student_name = f"{students[0]['firstname']} {students[0]['lastname']}"
            
            # Test exams API with date range
            today = datetime.now().date()
            start_date = (today - timedelta(weeks=1)).isoformat()  # Past week
            end_date = (today + timedelta(weeks=8)).isoformat()    # Next 8 weeks
            
            print(f"\n📋 Testing exams API for {student_name}...")
            print(f"📡 Date range: {start_date} to {end_date}")
            
            exams_data = await api.get_exams(student_id, start_date, end_date)
            
            # Analyze data
            exams = exams_data.get("data", [])
            print(f"📊 Found {len(exams)} exams")
            
            if exams:
                print("\n📝 Sample exam entries:")
                for i, exam in enumerate(exams[:3]):
                    subject = exam.get('subject', {})
                    subject_name = subject.get('name', 'Unknown') if isinstance(subject, dict) else str(subject)
                    
                    exam_type = exam.get('type', {})
                    type_name = exam_type.get('name', 'Exam') if isinstance(exam_type, dict) else str(exam_type)
                    
                    print(f"   {i+1}. {subject_name} - {type_name}")
                    print(f"      Date: {exam.get('date')}")
                    print(f"      Time: {exam.get('startClassHour', {}).get('from', 'No time')}")
                    print(f"      Comment: {exam.get('comment', 'No comment')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exams_api())
```

### Curl-Test

```bash
# Test exams API with curl
curl 'https://login.schulmanager-online.de/api/calls' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'content-type: application/json' \
  --data-raw '{
    "bundleVersion":"3505280ee7",
    "requests":[{
      "moduleName":"exams",
      "endpointName":"get-exams",
      "parameters":{
        "student":{"id":4333047},
        "start":"2025-09-14",
        "end":"2025-10-25"
      }
    }]
  }'
```

## 🚨 Fehlerbehandlung

### Häufige Fehler

| Fehler | Status | Ursache | Lösung |
|--------|--------|---------|--------|
| `No exams response` | - | API-Response leer | Retry-Logic implementieren |
| `Exams request failed: 400` | 400 | Ungültige Parameter | Datumsformat validieren |
| `Exams request failed: 401` | 401 | Token abgelaufen | Token erneuern |
| `Exams request failed: 403` | 403 | Keine Berechtigung | Account-Typ prüfen |

### Datumsvalidierung

```python
def validate_date_range(start_date: datetime.date, end_date: datetime.date) -> None:
    """Validate date range for exams API."""
    if start_date > end_date:
        raise ValueError("Start date must be before end date")
    
    # Limit range to reasonable timeframe (max 1 year)
    max_range = timedelta(days=365)
    if (end_date - start_date) > max_range:
        raise ValueError("Date range too large (max 1 year)")
    
    # Don't allow dates too far in the past
    min_date = datetime.now().date() - timedelta(days=30)
    if start_date < min_date:
        raise ValueError("Start date too far in the past")
```

## 📱 Dashboard-Integration

### Lovelace-Karten

```yaml
# Klassenarbeiten-Übersicht
type: entities
title: "Klassenarbeiten - Marc Cedric"
entities:
  - entity: sensor.name_of_child_exams_today
    name: "Heute"
  - entity: sensor.name_of_child_exams_this_week
    name: "Diese Woche"
  - entity: sensor.name_of_child_exams_next_week
    name: "Nächste Woche"
  - entity: sensor.name_of_child_exams_upcoming
    name: "Kommend (30 Tage)"

# Detaillierte Klassenarbeiten-Card
type: custom:schulmanager-exams-card
entity: sensor.name_of_child_exams_upcoming
view: upcoming
show_colors: true
show_countdown: true
```

### Automatisierungen

```yaml
# Erinnerung vor Klassenarbeiten
automation:
  - alias: "Klassenarbeiten - Erinnerung"
    trigger:
      - platform: template
        value_template: >
          {% set exams = state_attr('sensor.name_of_child_exams_upcoming', 'exams') %}
          {% if exams %}
            {% for exam in exams %}
              {% if exam.days_until == 3 %}
                true
              {% endif %}
            {% endfor %}
          {% endif %}
    action:
      - service: notify.family
        data:
          title: "📝 Klassenarbeit in 3 Tagen"
          message: >
            {% set exams = state_attr('sensor.name_of_child_exams_upcoming', 'exams') %}
            {% for exam in exams %}
              {% if exam.days_until == 3 %}
                {{ exam.subject }} {{ exam.type }} am {{ exam.date }}
                {% if exam.comment %}
                  Hinweis: {{ exam.comment }}
                {% endif %}
              {% endif %}
            {% endfor %}
```

## 📊 Kalender-Integration

### Calendar Events

```python
# In calendar.py
async def async_get_events(self, hass, start_date, end_date):
    """Return calendar events for exams."""
    events = []
    
    for student_id, data in self.coordinator.data.items():
        exams_data = data.get("exams", {})
        exams = exams_data.get("data", [])
        student = data["student"]
        
        for exam in exams:
            exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()
            
            if start_date <= exam_date <= end_date:
                # Extract subject and type info
                subject = exam.get("subject", {})
                subject_name = subject.get("name", "Unknown") if isinstance(subject, dict) else str(subject)
                
                exam_type = exam.get("type", {})
                type_name = exam_type.get("name", "Exam") if isinstance(exam_type, dict) else str(exam_type)
                
                # Extract time info
                start_class_hour = exam.get("startClassHour", {})
                if isinstance(start_class_hour, dict):
                    start_time_str = start_class_hour.get("from", "08:00")
                    end_time_str = start_class_hour.get("until", "08:45")
                else:
                    start_time_str = "08:00"
                    end_time_str = "08:45"
                
                start_time = datetime.strptime(start_time_str[:5], "%H:%M").time()
                end_time = datetime.strptime(end_time_str[:5], "%H:%M").time()
                
                event = CalendarEvent(
                    start=datetime.combine(exam_date, start_time),
                    end=datetime.combine(exam_date, end_time),
                    summary=f"📝 {type_name}: {subject_name}",
                    description=f"Schüler: {student['firstname']} {student['lastname']}\n"
                               f"Typ: {type_name}\n"
                               f"Fach: {subject_name}\n"
                               f"{exam.get('comment', '')}".strip(),
                    uid=f"exam_{exam['id']}_{student_id}",
                )
                events.append(event)
    
    return events
```

## 📚 Weiterführende Dokumentation

- [API Analysis](API_Analysis.md) - Vollständige API-Dokumentation
- [Sensors Documentation](Sensors_Documentation.md) - Sensor-Details
- [Integration Architecture](Integration_Architecture.md) - Architektur-Übersicht
- [Calendar Integration](Calendar_Integration.md) - Kalender-Integration
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problemlösungen
