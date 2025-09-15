# Sensoren - Detaillierte Dokumentation

## 🎯 Übersicht

Die Schulmanager Online Integration stellt **16 verschiedene Sensor-Entitäten** bereit, die unterschiedliche Aspekte des Stundenplans und der Schulaktivitäten abdecken. Jeder Sensor wird automatisch für jeden konfigurierten Schüler erstellt:

- **8 Stundenplan-Sensoren** - Aktuelle Stunden, Vertretungen, Wochenpläne
- **4 Hausaufgaben-Sensoren** - Fällige und kommende Hausaufgaben
- **4 Klassenarbeiten-Sensoren** - Anstehende Tests und Klassenarbeiten

## 🔧 Konsistente Datenformatierung (Refactoring 2025)

**Wichtige Änderung**: Alle Sensoren verwenden jetzt ein einheitliches Datenformat für Stunden-Attribute:

### Einheitliche Fächerbehandlung
- **`subject`**: Vollständiger Fächername (z.B. "Evangelische Religionslehre (konfessionell kooperativ)")
- **`subject_abbreviation`**: Abkürzung (z.B. "EN")
- **`subject_sanitized`**: Bereinigter Fächername ohne Klammern und Kommas (z.B. "Evangelische Religionslehre")

### Standardisierte Stundenattribute
Alle Stunden-Sensoren verwenden jetzt das gleiche Attributformat:
```json
{
  "subject": "Vollständiger Fächername",
  "subject_abbreviation": "Abkürzung",
  "subject_sanitized": "Bereinigter Fächername",
  "time": "08:00-08:45",
  "room": "Raumbezeichnung",
  "teacher": "Lehrerküzel",
  "teacher_lastname": "Nachname",
  "teacher_firstname": "Vorname",
  "is_substitution": false,
  "type": "regularLesson",
  "comment": "",
  "date": "2025-09-16",
  "class_hour": "Stundennummer"
}
```

**Behobene Inkonsistenzen**:
- Alle Sensoren verwenden jetzt den vollständigen Fächernamen im `subject`-Feld
- Einheitliche Zeitformatierung als "HH:MM-HH:MM"
- Konsistente Lehrerinformationen mit Vollname und Kürzel
- Reduzierte Code-Duplikation durch gemeinsame Formatierungsfunktionen

## 📊 Sensor-Übersicht

### Stundenplan-Sensoren
| Sensor | Entity ID | Icon | Update-Intervall | Beschreibung |
|--------|-----------|------|------------------|--------------|
| **Current Lesson** | `sensor.{student}_current_lesson` | `mdi:school` | 5 Minuten | Aktuelle Unterrichtsstunde |
| **Next Lesson** | `sensor.{student}_next_lesson` | `mdi:clock-outline` | 5 Minuten | Nächste Unterrichtsstunde |
| **Today's Lessons** | `sensor.{student}_todays_lessons` | `mdi:calendar-today` | 15 Minuten | Alle heutigen Stunden |
| **Today's Changes** | `sensor.{student}_todays_changes` | `mdi:swap-horizontal` | 15 Minuten | Heutige Vertretungen |
| **Next School Day** | `sensor.{student}_next_school_day` | `mdi:calendar-arrow-right` | 15 Minuten | Nächster Schultag |
| **This Week** | `sensor.{student}_this_week` | `mdi:calendar-week` | 1 Stunde | Stundenplan diese Woche |
| **Next Week** | `sensor.{student}_next_week` | `mdi:calendar-week-begin` | 1 Stunde | Stundenplan nächste Woche |
| **Changes Detected** | `sensor.{student}_changes_detected` | `mdi:alert-circle` | Bei Änderung | Erkannte Änderungen |

### Hausaufgaben-Sensoren
| Sensor | Entity ID | Icon | Update-Intervall | Beschreibung |
|--------|-----------|------|------------------|--------------|
| **Homework Due Today** | `sensor.{student}_homework_due_today` | `mdi:alarm-check` | 15 Minuten | Hausaufgaben fällig heute |
| **Homework Due Tomorrow** | `sensor.{student}_homework_due_tomorrow` | `mdi:calendar-arrow-right` | 15 Minuten | Hausaufgaben fällig morgen |
| **Homework Overdue** | `sensor.{student}_homework_overdue` | `mdi:alarm-snooze` | 15 Minuten | Überfällige Hausaufgaben |
| **Homework Upcoming** | `sensor.{student}_homework_upcoming` | `mdi:notebook-edit-outline` | 15 Minuten | Kommende Hausaufgaben |

### Klassenarbeiten-Sensoren
| Sensor | Entity ID | Icon | Update-Intervall | Beschreibung |
|--------|-----------|------|------------------|--------------|
| **Exams Today** | `sensor.{student}_exams_today` | `mdi:clipboard-alert` | 15 Minuten | Klassenarbeiten heute |
| **Exams This Week** | `sensor.{student}_exams_this_week` | `mdi:calendar-week-begin` | 1 Stunde | Klassenarbeiten diese Woche |
| **Exams Next Week** | `sensor.{student}_exams_next_week` | `mdi:calendar-week-begin` | 1 Stunde | Klassenarbeiten nächste Woche |
| **Exams Upcoming** | `sensor.{student}_exams_upcoming` | `mdi:clipboard-clock` | 1 Stunde | Kommende Klassenarbeiten |

## 🔍 Sensor-Details

### 1. Current Lesson Sensor

**Entity ID**: `sensor.{student_name}_current_lesson`

**Zweck**: Zeigt die aktuell laufende Unterrichtsstunde an.

**State-Werte**:
- `"Mathematik"` - Name des aktuellen Fachs
- `"Pause"` - Wenn gerade Pause ist
- `"Kein Unterricht"` - Außerhalb der Schulzeit
- `"Unbekannt"` - Bei Datenfehlern

**Attribute**:
```json
{
  "subject": "Mathematik",
  "teacher": "Herr Schmidt",
  "room": "R204",
  "start_time": "09:45",
  "end_time": "10:30",
  "class_hour": "3",
  "is_substitution": false,
  "substitution_info": null,
  "student_name": "Marc Cedric Wunsch"
}
```

**Implementierung**:
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
    
    return "Kein Unterricht"
```

### 2. Next Lesson Sensor

**Entity ID**: `sensor.{student_name}_next_lesson`

**Zweck**: Zeigt die nächste anstehende Unterrichtsstunde an.

**State-Werte**:
- `"Deutsch (in 15 min)"` - Nächstes Fach mit Zeitangabe
- `"Morgen: Englisch (08:00)"` - Nächster Tag
- `"Kein weiterer Unterricht heute"` - Ende des Schultags

**Attribute**:
```json
{
  "subject": "Deutsch",
  "teacher": "Frau Müller",
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

**Zweck**: Übersicht über alle Stunden des aktuellen Tages.

**State-Werte**:
- `"6"` - Anzahl der heutigen Stunden
- `"0"` - Kein Unterricht heute (Wochenende/Feiertag)

**Attribute**:
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
      "subject": "Mathematik",
      "subject_abbreviation": "M",
      "subject_sanitized": "Mathematik",
      "time": "08:50-09:35",
      "room": "R204",
      "teacher": "Sch",
      "teacher_lastname": "Schmidt",
      "teacher_firstname": "Hans",
      "is_substitution": true,
      "type": "changedLesson",
      "comment": "Vertretung",
      "date": "2025-09-16",
      "class_hour": "2"
    }
  ],
  "count": 6
}
```

### 4. Today's Changes Sensor

**Entity ID**: `sensor.{student_name}_todays_changes`

**Zweck**: Zeigt alle Vertretungen und Änderungen für den aktuellen Tag.

**State-Werte**:
- `"2"` - Anzahl der Vertretungen heute
- `"0"` - Keine Vertretungen

**Attribute**:
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
      "comment": "Vertretung für Frau Weber",
      "date": "2025-09-16",
      "class_hour": "1",
      "original_teacher": "Web"
    },
    {
      "subject": "Sport",
      "subject_abbreviation": "Sp",
      "subject_sanitized": "Sport",
      "time": "13:15-14:00",
      "room": "",
      "teacher": "",
      "teacher_lastname": "",
      "teacher_firstname": "",
      "is_substitution": false,
      "type": "cancelledLesson",
      "comment": "Ausfall wegen Hallensanierung",
      "date": "2025-09-16",
      "class_hour": "6"
    }
  ],
  "count": 2
}
```

### 5. Next School Day Sensor

**Entity ID**: `sensor.{student_name}_next_school_day`

**Zweck**: Informationen über den nächsten Schultag (überspringt Wochenenden).

**State-Werte**:
- `"Montag, 16.09.2025"` - Nächster Schultag
- `"Heute"` - Wenn heute noch Unterricht ist

**Attribute**:
```json
{
  "date": "2025-09-16",
  "day_name": "Montag",
  "days_until": 2,
  "first_lesson": {
    "subject": "Mathematik",
    "teacher": "Herr Schmidt",
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

**Zweck**: Vollständiger Stundenplan für die aktuelle Woche.

**State-Werte**:
- `"32"` - Gesamtanzahl Stunden diese Woche
- `"0"` - Keine Stunden (Ferien)

**Attribute**:
```json
{
  "week_start": "2025-09-14",
  "week_end": "2025-09-20",
  "calendar_week": 38,
  "school_days": [
    {
      "date": "2025-09-14",
      "day_name": "Montag",
      "lessons_count": 6,
      "has_changes": false
    },
    {
      "date": "2025-09-15",
      "day_name": "Dienstag", 
      "lessons_count": 7,
      "has_changes": true
    }
  ],
  "total_lessons": 32,
  "total_changes": 3,
  "subjects_summary": {
    "Mathematik": 5,
    "Deutsch": 4,
    "Englisch": 3,
    "Geschichte": 2
  }
}
```

### 7. Next Week Sensor

**Entity ID**: `sensor.{student_name}_next_week`

**Zweck**: Stundenplan-Vorschau für die kommende Woche.

**State-Werte**:
- `"35"` - Anzahl Stunden nächste Woche
- `"Ferien"` - Wenn Ferien sind

**Attribute**: Ähnlich wie "This Week", aber für die folgende Woche.

### 8. Changes Detected Sensor

**Entity ID**: `sensor.{student_name}_changes_detected`

**Zweck**: Erkennt Änderungen im Stundenplan und benachrichtigt darüber.

**State-Werte**:
- `"Neue Änderungen"` - Wenn Änderungen erkannt wurden
- `"Keine Änderungen"` - Alles unverändert
- `"Erstmalig geladen"` - Bei erstem Laden

**Attribute**:
```json
{
  "last_check": "2025-09-14T10:30:00",
  "changes_detected_at": "2025-09-14T10:15:00",
  "changes": [
    {
      "type": "substitution_added",
      "date": "2025-09-15",
      "class_hour": "3",
      "subject": "Mathematik",
      "old_teacher": "Herr Schmidt",
      "new_teacher": "Frau Weber",
      "reason": "Fortbildung"
    },
    {
      "type": "lesson_cancelled",
      "date": "2025-09-16",
      "class_hour": "6",
      "subject": "Sport",
      "reason": "Hallensanierung"
    }
  ],
  "total_new_changes": 2
}
```

## 📚 Hausaufgaben-Sensoren

### 9. Homework Due Today Sensor

**Entity ID**: `sensor.{student_name}_homework_due_today`

**Zweck**: Zeigt die Anzahl der heute fälligen Hausaufgaben an.

**State-Werte**:
- `"3"` - Anzahl der heute fälligen Hausaufgaben
- `"0"` - Keine Hausaufgaben heute fällig

**Attribute**:
```json
{
  "homeworks": [
    {
      "id": 12345,
      "subject": "Mathematik",
      "homework": "Aufgaben S. 45, Nr. 1-10",
      "date": "2025-09-14",
      "teacher": "Herr Schmidt",
      "completed": false,
      "days_overdue": 0
    }
  ],
  "count": 3,
  "subjects": ["Mathematik", "Deutsch", "Englisch"]
}
```

### 10. Homework Due Tomorrow Sensor

**Entity ID**: `sensor.{student_name}_homework_due_tomorrow`

**Zweck**: Zeigt die Anzahl der morgen fälligen Hausaufgaben an.

**State-Werte**:
- `"2"` - Anzahl der morgen fälligen Hausaufgaben
- `"0"` - Keine Hausaufgaben morgen fällig

### 11. Homework Overdue Sensor

**Entity ID**: `sensor.{student_name}_homework_overdue`

**Zweck**: Zeigt überfällige Hausaufgaben an.

**State-Werte**:
- `"1"` - Anzahl überfälliger Hausaufgaben
- `"0"` - Keine überfälligen Hausaufgaben

**Attribute**:
```json
{
  "homeworks": [
    {
      "id": 12340,
      "subject": "Geschichte",
      "homework": "Referat vorbereiten",
      "date": "2025-09-12",
      "teacher": "Frau Weber",
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

**Zweck**: Zeigt kommende Hausaufgaben (nächste 7 Tage) an.

**State-Werte**:
- `"8"` - Anzahl kommender Hausaufgaben
- `"0"` - Keine kommenden Hausaufgaben

## 📝 Klassenarbeiten-Sensoren

### 13. Exams Today Sensor

**Entity ID**: `sensor.{student_name}_exams_today`

**Zweck**: Zeigt heute anstehende Klassenarbeiten/Tests an.

**State-Werte**:
- `"2"` - Anzahl der heutigen Klassenarbeiten
- `"0"` - Keine Klassenarbeiten heute

**Attribute**:
```json
{
  "exams": [
    {
      "subject": "Deutsch",
      "subject_abbreviation": "D",
      "title": "Klassenarbeit",
      "date": "2025-09-14",
      "time": "11:41-12:26",
      "class_hour": "5",
      "room": "",
      "teacher": "",
      "type": "Klassenarbeit",
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

**Zweck**: Zeigt alle Klassenarbeiten dieser Woche an.

**State-Werte**:
- `"3"` - Anzahl der Klassenarbeiten diese Woche
- `"0"` - Keine Klassenarbeiten diese Woche

**Attribute**:
```json
{
  "exams": [
    {
      "subject": "Mathematik",
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
  "subjects": ["Mathematik", "Deutsch", "Englisch"]
}
```

### 15. Exams Next Week Sensor

**Entity ID**: `sensor.{student_name}_exams_next_week`

**Zweck**: Zeigt Klassenarbeiten der nächsten Woche an.

### 16. Exams Upcoming Sensor

**Entity ID**: `sensor.{student_name}_exams_upcoming`

**Zweck**: Zeigt alle kommenden Klassenarbeiten (nächste 30 Tage) an.

**State-Werte**:
- `"5"` - Anzahl kommender Klassenarbeiten
- `"0"` - Keine kommenden Klassenarbeiten

**Attribute**:
```json
{
  "exams": [
    {
      "subject": "Englisch",
      "title": "Vokabeltest",
      "date": "2025-09-20",
      "time": "10:45-11:30",
      "type": "Lernkontrolle",
      "days_until": 6,
      "is_next_exam": true
    }
  ],
  "count": 5,
  "subjects": ["Englisch", "Physik", "Chemie"],
  "next_exam_date": "2025-09-20"
}
```

## 🔧 Sensor-Implementierung

### Basis-Sensor-Klasse

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

### Sensor-spezifische Implementierungen

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
    # ... weitere Implementierungen
    
    return {}
```

## 📱 Verwendung in Home Assistant

### Dashboard-Integration

```yaml
# Lovelace Dashboard Konfiguration
type: entities
title: Schulmanager - Marc Cedric
entities:
  - entity: sensor.name_of_child_current_lesson
    name: Aktuelle Stunde
  - entity: sensor.name_of_child_next_lesson
    name: Nächste Stunde
  - entity: sensor.name_of_child_todays_changes
    name: Heutige Vertretungen
```

### Automatisierungen

```yaml
# Benachrichtigung bei Vertretungen
automation:
  - alias: "Schulmanager - Vertretung erkannt"
    trigger:
      - platform: state
        entity_id: sensor.name_of_child_changes_detected
        to: "Neue Änderungen"
    action:
      - service: notify.mobile_app
        data:
          title: "Stundenplan-Änderung"
          message: >
            Neue Vertretung für {{ trigger.to_state.attributes.student_name }}:
            {{ trigger.to_state.attributes.changes[0].subject }} 
            am {{ trigger.to_state.attributes.changes[0].date }}
```

### Template-Sensoren

```yaml
# Template für nächste Stunde mit Countdown
template:
  - sensor:
      - name: "Nächste Stunde Countdown"
        state: >
          {% set next_lesson = states('sensor.name_of_child_next_lesson') %}
          {% set minutes = state_attr('sensor.name_of_child_next_lesson', 'minutes_until') %}
          {% if minutes is not none and minutes > 0 %}
            {{ next_lesson }} in {{ minutes }} Minuten
          {% else %}
            {{ next_lesson }}
          {% endif %}
```

## 🔄 Update-Strategien

### Intelligente Updates

```python
async def _async_update_data(self):
    """Update data with intelligent scheduling."""
    now = datetime.now()
    
    # Schnellere Updates während Schulzeit
    if self._is_school_time(now):
        # Update current/next lesson every 5 minutes
        if now.minute % 5 == 0:
            await self._update_current_lessons()
    
    # Normale Updates alle 15 Minuten
    if now.minute % 15 == 0:
        await self._update_daily_schedule()
    
    # Wöchentliche Updates stündlich
    if now.minute == 0:
        await self._update_weekly_schedule()
```

### Caching-Mechanismus

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

## 🚨 Fehlerbehandlung

### Sensor-Verfügbarkeit

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
            return "Nicht verfügbar"
        
        return self._calculate_sensor_value()
        
    except Exception as e:
        _LOGGER.error("Error calculating sensor value for %s: %s", self.entity_id, e)
        return "Fehler"
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
            return "Stundenplan verfügbar"
        
        return "Keine Daten"
```

## 📊 Performance-Optimierung

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
        # ... weitere Berechnungen
    }
    
    return results
```

## 📚 Weiterführende Dokumentation

- [Integration Architecture](Integration_Architecture.md) - Gesamtarchitektur
- [Custom Card Documentation](Custom_Card_Documentation.md) - UI-Integration
- [Configuration Guide](Configuration_Guide.md) - Konfiguration
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problemlösungen
