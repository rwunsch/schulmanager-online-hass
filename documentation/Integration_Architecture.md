# Home Assistant Integration - Architektur

## 🏗️ Übersicht

Die Schulmanager Online Integration für Home Assistant folgt den offiziellen HA-Entwicklungsrichtlinien und implementiert eine vollständige Custom Integration mit Sensoren, Kalender-Integration und Custom UI-Komponenten.

## 📁 Projektstruktur

```
custom_components/schulmanager_online/
├── __init__.py                 # Integration Entry Point
├── manifest.json              # HACS Integration Manifest
├── const.py                   # Konstanten und Konfiguration
├── config_flow.py             # UI-basierte Konfiguration
├── coordinator.py             # Data Update Coordinator
├── api.py                     # API Client
├── sensor.py                  # Sensor Entities
├── calendar.py                # Calendar Integration
├── strings.json               # UI-Strings (Englisch)
├── translations/              # Multi-Language Support
│   ├── de.json               # Deutsche Übersetzung
│   ├── fr.json               # Französische Übersetzung
│   └── ...                   # Weitere Sprachen
└── www/                      # Custom Card Assets
    ├── schulmanager-schedule-card.js
    └── schulmanager-schedule-card-editor.js
```

## 🔄 Datenfluss-Architektur

```mermaid
graph TD
    A[Home Assistant] --> B[Config Flow]
    B --> C[Data Update Coordinator]
    C --> D[Schulmanager API]
    D --> E[Schulmanager Online]
    
    C --> F[Sensor Entities]
    C --> G[Calendar Entities]
    
    F --> H[Home Assistant Dashboard]
    G --> H
    
    I[Custom Lovelace Card] --> H
    
    J[User Configuration] --> B
    K[Automatic Updates] --> C
```

## 🧩 Komponenten-Details

### 1. Integration Entry Point (`__init__.py`)

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schulmanager Online from a config entry."""
    
    # Extract configuration
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    
    # Create coordinator
    coordinator = SchulmanagerOnlineDataUpdateCoordinator(hass, email, password)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True
```

**Verantwortlichkeiten:**
- Integration initialisieren
- Coordinator erstellen und konfigurieren
- Plattformen (Sensor, Calendar) laden
- Fehlerbehandlung und Cleanup

### 2. Data Update Coordinator (`coordinator.py`)

```python
class SchulmanagerOnlineDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""
    
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),  # Update alle 15 Minuten
        )
        
        self.session = async_get_clientsession(hass)
        self.api = SchulmanagerAPI(email, password, self.session)
        self.students = []
    
    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get students if not cached
            if not self.students:
                self.students = await self.api.get_students()
            
            # Fetch schedule data for all students
            data = {}
            for student in self.students:
                student_id = student["id"]
                
                # Get current week and next week
                today = datetime.date.today()
                start_date = today - timedelta(days=today.weekday())  # Monday
                end_date = start_date + timedelta(days=13)  # 2 weeks
                
                schedule = await self.api.get_schedule(student_id, start_date, end_date)
                data[student_id] = {
                    "student": student,
                    "schedule": schedule,
                    "last_updated": datetime.now()
                }
            
            return data
            
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}")
```

**Verantwortlichkeiten:**
- Regelmäßige Datenaktualisierung (alle 15 Minuten)
- API-Calls koordinieren
- Daten für alle Entitäten bereitstellen
- Fehlerbehandlung und Retry-Logic

### 3. Configuration Flow (`config_flow.py`)

```python
class SchulmanagerOnlineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schulmanager Online."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }),
                errors={}
            )
        
        errors = {}
        
        try:
            # Test the connection
            session = async_get_clientsession(self.hass)
            api = SchulmanagerAPI(user_input[CONF_EMAIL], user_input[CONF_PASSWORD], session)
            
            await api.authenticate()
            students = await api.get_students()
            
            if not students:
                errors["base"] = "no_students"
            else:
                # Create entry
                return self.async_create_entry(
                    title=f"Schulmanager ({user_input[CONF_EMAIL]})",
                    data=user_input,
                )
                
        except SchulmanagerAPIError as e:
            _LOGGER.error("Authentication failed: %s", e)
            errors["base"] = "invalid_auth"
        except Exception as e:
            _LOGGER.exception("Unexpected exception: %s", e)
            errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL, default=user_input[CONF_EMAIL]): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors
        )
```

**Verantwortlichkeiten:**
- UI-basierte Konfiguration
- Credential-Validierung
- Benutzerfreundliche Fehlermeldungen
- Integration-Entry erstellen

## 📊 Sensor-Architektur

### Sensor-Typen

| Sensor | Beschreibung | Update-Frequenz |
|--------|--------------|-----------------|
| **Current Lesson** | Aktuelle Stunde | Alle 5 Minuten |
| **Next Lesson** | Nächste Stunde | Alle 5 Minuten |
| **Today's Lessons** | Alle heutigen Stunden | Alle 15 Minuten |
| **Today's Changes** | Heutige Vertretungen | Alle 15 Minuten |
| **Next School Day** | Nächster Schultag | Alle 15 Minuten |
| **This Week** | Diese Woche | Stündlich |
| **Next Week** | Nächste Woche | Stündlich |
| **Changes Detected** | Änderungen erkannt | Bei Änderungen |

### Sensor-Implementierung

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
        
        # Set entity properties
        self._attr_name = f"{student_name} {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_icon = SENSOR_TYPES[sensor_type]['icon']
        self._attr_device_class = SENSOR_TYPES[sensor_type].get('device_class')
    
    @property
    def native_value(self):
        """Return the native value of the sensor."""
        if self.sensor_type == "current_lesson":
            return self._get_current_lesson()
        elif self.sensor_type == "next_lesson":
            return self._get_next_lesson()
        # ... weitere Sensor-Typen
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        
        if self.sensor_type == "current_lesson":
            lesson = self._get_current_lesson_details()
            if lesson:
                attributes.update({
                    "subject": lesson.get("subject"),
                    "teacher": lesson.get("teacher"),
                    "room": lesson.get("room"),
                    "start_time": lesson.get("start_time"),
                    "end_time": lesson.get("end_time"),
                })
        
        return attributes
```

## 📅 Kalender-Integration

### Calendar Entity

```python
class SchulmanagerOnlineCalendar(CoordinatorEntity, CalendarEntity):
    """Representation of a Schulmanager Online calendar."""
    
    @property
    def event(self):
        """Return the next upcoming event."""
        events = self._get_upcoming_events()
        return events[0] if events else None
    
    async def async_get_events(self, hass, start_date, end_date):
        """Return calendar events within a datetime range."""
        events = []
        
        for student_id, data in self.coordinator.data.items():
            schedule = data["schedule"]
            student = data["student"]
            
            for lesson in schedule:
                lesson_date = datetime.strptime(lesson["date"], "%Y-%m-%d").date()
                
                if start_date <= lesson_date <= end_date:
                    event = CalendarEvent(
                        start=datetime.combine(lesson_date, 
                                             datetime.strptime(lesson["classHour"]["startTime"], "%H:%M").time()),
                        end=datetime.combine(lesson_date,
                                           datetime.strptime(lesson["classHour"]["endTime"], "%H:%M").time()),
                        summary=f"{lesson['lesson']['subject']} - {lesson['lesson']['teacher']}",
                        description=f"Raum: {lesson['lesson']['room']}",
                    )
                    events.append(event)
        
        return events
```

## 🎨 Custom Card Integration

### Card Registration

```javascript
// schulmanager-schedule-card.js
class SchulmanagerScheduleCard extends LitElement {
    
    static get properties() {
        return {
            hass: {},
            config: {},
        };
    }
    
    setConfig(config) {
        if (!config.entity) {
            throw new Error('You need to define an entity');
        }
        this.config = config;
    }
    
    render() {
        const entity = this.hass.states[this.config.entity];
        
        if (!entity) {
            return html`<ha-card>Entity not found</ha-card>`;
        }
        
        return html`
            <ha-card>
                <div class="card-content">
                    ${this._renderSchedule(entity)}
                </div>
            </ha-card>
        `;
    }
}

customElements.define('schulmanager-schedule-card', SchulmanagerScheduleCard);
```

## 🔧 Konfiguration und Konstanten

### Konstanten (`const.py`)

```python
# Domain
DOMAIN = "schulmanager_online"

# Configuration
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Platforms
PLATFORMS = ["sensor", "calendar"]

# Update intervals
UPDATE_INTERVAL = timedelta(minutes=15)
FAST_UPDATE_INTERVAL = timedelta(minutes=5)

# Sensor types
SENSOR_TYPES = {
    "current_lesson": {
        "name": "Current Lesson",
        "icon": "mdi:school",
        "device_class": None,
    },
    "next_lesson": {
        "name": "Next Lesson", 
        "icon": "mdi:clock-outline",
        "device_class": None,
    },
    # ... weitere Sensor-Typen
}

# API URLs
SALT_URL = "https://login.schulmanager-online.de/api/salt"
LOGIN_URL = "https://login.schulmanager-online.de/api/login"
API_URL = "https://login.schulmanager-online.de/api/calls"
```

## 🌍 Internationalisierung

### String-Verwaltung

```python
# strings.json (Englisch - Basis)
{
    "config": {
        "step": {
            "user": {
                "title": "Schulmanager Online",
                "description": "Enter your Schulmanager Online credentials",
                "data": {
                    "email": "Email or Username",
                    "password": "Password"
                }
            }
        },
        "error": {
            "invalid_auth": "Invalid authentication",
            "no_students": "No students found for this account",
            "unknown": "Unknown error occurred"
        }
    }
}
```

```python
# translations/de.json (Deutsch)
{
    "config": {
        "step": {
            "user": {
                "title": "Schulmanager Online",
                "description": "Geben Sie Ihre Schulmanager Online Zugangsdaten ein",
                "data": {
                    "email": "E-Mail oder Benutzername",
                    "password": "Passwort"
                }
            }
        },
        "error": {
            "invalid_auth": "Ungültige Anmeldedaten",
            "no_students": "Keine Schüler für dieses Konto gefunden",
            "unknown": "Unbekannter Fehler aufgetreten"
        }
    }
}
```

## 🔄 Lifecycle Management

### Setup-Prozess

1. **Config Entry Creation**: Benutzer konfiguriert Integration
2. **Coordinator Initialization**: Data Update Coordinator wird erstellt
3. **API Authentication**: Erste Authentifizierung mit API
4. **Platform Setup**: Sensoren und Kalender werden geladen
5. **Initial Data Fetch**: Erste Datenabfrage
6. **Regular Updates**: Regelmäßige Updates starten

### Update-Zyklen

| Komponente | Intervall | Trigger |
|------------|-----------|---------|
| **Coordinator** | 15 Minuten | Timer |
| **Current/Next Lesson** | 5 Minuten | Timer |
| **Schedule Changes** | Bei Änderung | Data Comparison |
| **Token Refresh** | 55 Minuten | Token Expiry |

### Cleanup-Prozess

```python
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Close API session
        if hasattr(coordinator.api, 'session'):
            await coordinator.api.session.close()
    
    return unload_ok
```

## 📊 Performance-Optimierungen

### Caching-Strategien

1. **Student Data**: Einmalig bei Login, dann gecacht
2. **Schedule Data**: 15-Minuten Cache mit Smart Updates
3. **Token Management**: Automatische Erneuerung mit Buffer
4. **API Rate Limiting**: Intelligent Request Batching

### Memory Management

- **Lazy Loading**: Daten nur bei Bedarf laden
- **Data Pruning**: Alte Daten automatisch entfernen
- **Session Reuse**: HTTP-Session wiederverwenden
- **Garbage Collection**: Explizite Cleanup-Routinen

## 🚨 Fehlerbehandlung

### Error Recovery

```python
async def _async_update_data(self):
    """Update data with error handling."""
    try:
        return await self._fetch_data()
    except SchulmanagerAPIError as e:
        if "authentication" in str(e).lower():
            # Try to re-authenticate
            await self.api.authenticate()
            return await self._fetch_data()
        raise UpdateFailed(f"API Error: {e}")
    except Exception as e:
        _LOGGER.exception("Unexpected error during update")
        raise UpdateFailed(f"Unexpected error: {e}")
```

### Graceful Degradation

- **Partial Data**: Bei teilweisen Fehlern verfügbare Daten anzeigen
- **Offline Mode**: Letzte bekannte Daten verwenden
- **User Feedback**: Klare Fehlermeldungen in UI
- **Automatic Recovery**: Automatische Wiederherstellung nach Fehlern

## 📚 Weiterführende Dokumentation

- [API Implementation](API_Implementation.md) - API Client Details
- [Sensors Documentation](Sensors_Documentation.md) - Sensor-Implementierung
- [Custom Card Documentation](Custom_Card_Documentation.md) - UI-Komponenten
- [Configuration Guide](Configuration_Guide.md) - Benutzer-Konfiguration
