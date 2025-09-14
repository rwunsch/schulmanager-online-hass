# Troubleshooting Guide

## 🚨 Häufige Probleme und Lösungen

### 🔐 Authentifizierungs-Probleme

#### Problem: "Authentication failed: Login failed: 401"

**Symptome:**
- Integration kann nicht konfiguriert werden
- Fehler beim Setup in Home Assistant
- Login schlägt fehl

**Mögliche Ursachen:**
1. **Falsche Anmeldedaten**
2. **Hash-Generierung fehlerhaft**
3. **API-Parameter fehlen**

**Lösungsschritte:**

1. **Anmeldedaten überprüfen:**
   ```bash
   # Test mit curl (aus Research/API-call_login-salted.txt)
   curl 'https://login.schulmanager-online.de/api/salt' \
     -H 'content-type: application/json' \
     --data-raw '{"emailOrUsername":"IHRE_EMAIL","mobileApp":false,"institutionId":null}'
   ```

2. **Hash-Parameter validieren:**
   ```python
   # In test-scripts/test_corrected_hash.py
   python test-scripts/test_corrected_hash.py
   ```

3. **API-Parameter prüfen:**
   - `mobileApp: false` muss gesetzt sein
   - `institutionId: null` verwenden
   - Salt als UTF-8 encodieren, nicht als Hex

**Debug-Logs aktivieren:**
```yaml
# In configuration.yaml
logger:
  default: info
  logs:
    custom_components.schulmanager_online: debug
```

#### Problem: "No salt received"

**Symptome:**
- Salt-Abruf schlägt fehl
- 400 Bad Request beim Salt-Endpunkt

**Lösung:**
```python
# Korrekte Salt-Request Parameter
payload = {
    "emailOrUsername": email,
    "mobileApp": False,  # WICHTIG: Muss False sein!
    "institutionId": None
}
```

#### Problem: "'str' object has no attribute 'get'"

**Symptome:**
- Fehler beim Salt-Parsing
- Integration Setup bricht ab

**Lösung:**
```python
# Salt kann als String oder JSON zurückgegeben werden
try:
    data = await response.json()
    if isinstance(data, str):
        salt = data
    else:
        salt = data.get("salt")
except Exception:
    salt = await response.text()
```

### 👥 Schülerdaten-Probleme

#### Problem: "No students found for this account"

**Symptome:**
- Login erfolgreich, aber keine Schüler gefunden
- Integration Setup schlägt fehl

**Mögliche Ursachen:**
1. **Account hat keine Schüler-Berechtigung**
2. **Schülerdaten nicht in Login-Response**
3. **Falsche Datenextraktion**

**Lösungsschritte:**

1. **Login-Response analysieren:**
   ```python
   # Debug-Ausgabe in api.py
   _LOGGER.debug("User data keys: %s", list(self.user_data.keys()))
   _LOGGER.debug("Associated parents: %s", self.user_data.get("associatedParents"))
   ```

2. **Account-Typ überprüfen:**
   - **Eltern-Account**: Schüler in `associatedParents[].student`
   - **Schüler-Account**: Schüler in `associatedStudent`
   - **Lehrer-Account**: Keine Schülerdaten verfügbar

3. **Manuelle Überprüfung:**
   ```bash
   # Test-Script ausführen
   cd test-scripts
   python test_corrected_hash.py
   ```

### 📊 Sensor-Probleme

#### Problem: Sensoren zeigen "Nicht verfügbar"

**Symptome:**
- Alle Sensoren unavailable
- Keine Daten in Attributen

**Lösungsschritte:**

1. **Coordinator-Status prüfen:**
   ```python
   # In Home Assistant Developer Tools > States
   # Suche nach: sensor.{student_name}_*
   ```

2. **Update-Intervall überprüfen:**
   ```python
   # In coordinator.py
   update_interval=timedelta(minutes=15)  # Standard-Intervall
   ```

3. **API-Verbindung testen:**
   ```bash
   # Standalone-Test
   cd test-scripts
   python standalone_api_test.py
   ```

#### Problem: "Kein Unterricht" obwohl Schulzeit

**Symptome:**
- Current Lesson zeigt falsche Werte
- Zeitzone-Probleme

**Lösung:**
```python
# Zeitzone-Konfiguration prüfen
import datetime
now = datetime.datetime.now()
print(f"Current time: {now}")
print(f"Timezone: {now.astimezone().tzinfo}")

# In Home Assistant configuration.yaml
homeassistant:
  time_zone: Europe/Berlin
```

### 🔄 Update-Probleme

#### Problem: Daten werden nicht aktualisiert

**Symptome:**
- Sensoren zeigen veraltete Daten
- Keine automatischen Updates

**Lösungsschritte:**

1. **Coordinator-Logs prüfen:**
   ```bash
   # Docker-Logs anzeigen
   docker logs schulmanager-ha-test | grep -i schulmanager
   ```

2. **Manuelles Update erzwingen:**
   ```python
   # In Home Assistant Developer Tools > Services
   # Service: homeassistant.update_entity
   # Entity: sensor.{student_name}_current_lesson
   ```

3. **Token-Erneuerung prüfen:**
   ```python
   # Token sollte alle 55 Minuten erneuert werden
   _LOGGER.debug("Token expires at: %s", self.token_expires)
   ```

### 🌐 Netzwerk-Probleme

#### Problem: "Connection timeout" / "Cannot connect"

**Symptome:**
- API-Calls schlagen fehl
- Intermittierende Verbindungsfehler

**Lösungsschritte:**

1. **Netzwerk-Konnektivität testen:**
   ```bash
   # DNS-Auflösung testen
   nslookup login.schulmanager-online.de
   
   # HTTPS-Verbindung testen
   curl -I https://login.schulmanager-online.de/api/salt
   ```

2. **Timeout-Werte anpassen:**
   ```python
   # In api.py
   timeout = aiohttp.ClientTimeout(total=30, connect=10)
   session = aiohttp.ClientSession(timeout=timeout)
   ```

3. **Retry-Logic implementieren:**
   ```python
   async def _make_api_call_with_retry(self, requests, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await self._make_api_call(requests)
           except aiohttp.ClientError as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

### 🐳 Docker-Probleme

#### Problem: Home Assistant Container startet nicht

**Symptome:**
- Container-Status: Exited
- Port 8123 nicht erreichbar

**Lösungsschritte:**

1. **Container-Logs prüfen:**
   ```bash
   docker logs schulmanager-ha-test
   ```

2. **Konfigurationsfehler beheben:**
   ```bash
   # Konfiguration validieren
   docker run --rm -v $(pwd)/test-scripts/ha-config:/config \
     ghcr.io/home-assistant/home-assistant:stable \
     python -m homeassistant --script check_config --config /config
   ```

3. **Port-Mapping korrigieren:**
   ```yaml
   # In docker-compose-fixed.yml
   ports:
     - 8123:8123  # Explizites Port-Mapping
   ```

#### Problem: Custom Integration nicht geladen

**Symptome:**
- Integration nicht in Settings sichtbar
- "Domain not found" Fehler

**Lösungsschritte:**

1. **Volume-Mapping prüfen:**
   ```bash
   # Prüfen ob custom_components gemountet ist
   docker exec schulmanager-ha-test ls -la /config/custom_components/
   ```

2. **Integration neu laden:**
   ```bash
   # Home Assistant neu starten
   docker restart schulmanager-ha-test
   ```

3. **Manifest validieren:**
   ```json
   // custom_components/schulmanager_online/manifest.json
   {
     "domain": "schulmanager_online",
     "name": "Schulmanager Online",
     "version": "1.0.0",
     "documentation": "https://github.com/...",
     "dependencies": [],
     "codeowners": [],
     "requirements": ["aiohttp", "python-dateutil"],
     "iot_class": "cloud_polling"
   }
   ```

### 🎨 Custom Card Probleme

#### Problem: Custom Card wird nicht angezeigt

**Symptome:**
- "Custom element doesn't exist" Fehler
- Leere Card in Dashboard

**Lösungsschritte:**

1. **Card-Registration prüfen:**
   ```javascript
   // Browser-Konsole öffnen (F12)
   console.log(customElements.get('schulmanager-schedule-card'));
   ```

2. **Resource-Pfad korrigieren:**
   ```yaml
   # In configuration.yaml
   lovelace:
     resources:
       - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
         type: module
   ```

3. **Card-Konfiguration validieren:**
   ```yaml
   # Dashboard-Card
   type: custom:schulmanager-schedule-card
   entity: sensor.name_of_child_current_lesson
   view: weekly_matrix
   ```

### 🔧 Entwicklungs-Probleme

#### Problem: Test-Scripts schlagen fehl

**Symptome:**
- ModuleNotFoundError
- Import-Fehler

**Lösungsschritte:**

1. **Virtual Environment aktivieren:**
   ```bash
   cd test-scripts
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Python-Path korrigieren:**
   ```python
   # Am Anfang des Scripts
   import sys
   import os
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```

3. **Dependencies installieren:**
   ```bash
   pip install aiohttp python-dateutil
   ```

## 🔍 Debug-Strategien

### Logging aktivieren

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
    custom_components.schulmanager_online.coordinator: debug
```

### API-Calls verfolgen

```python
# In api.py - Temporär für Debugging
async def _make_api_call(self, requests):
    _LOGGER.debug("API Request: %s", requests)
    
    response = await self.session.post(API_URL, json=payload, headers=headers)
    
    _LOGGER.debug("API Response Status: %s", response.status)
    _LOGGER.debug("API Response Headers: %s", dict(response.headers))
    
    data = await response.json()
    _LOGGER.debug("API Response Data: %s", data)
    
    return data
```

### State-Debugging

```python
# Developer Tools > Template
{{ states('sensor.name_of_child_current_lesson') }}
{{ state_attr('sensor.name_of_child_current_lesson', 'subject') }}
{{ states.sensor.name_of_child_current_lesson.last_updated }}
```

### Network-Debugging

```bash
# Wireshark/tcpdump für HTTP-Traffic
sudo tcpdump -i any -A -s 0 'host login.schulmanager-online.de'

# curl für API-Tests
curl -v 'https://login.schulmanager-online.de/api/salt' \
  -H 'content-type: application/json' \
  --data-raw '{"emailOrUsername":"test@example.com","mobileApp":false,"institutionId":null}'
```

## 📋 Checkliste für Problemdiagnose

### ✅ Basis-Checks

- [ ] Home Assistant läuft und ist erreichbar (http://localhost:8123)
- [ ] Custom Integration ist in `/config/custom_components/` vorhanden
- [ ] Anmeldedaten sind korrekt
- [ ] Internetverbindung funktioniert
- [ ] Schulmanager Online Website ist erreichbar

### ✅ API-Checks

- [ ] Salt-Abruf funktioniert
- [ ] Hash-Generierung korrekt (1024 Zeichen)
- [ ] Login erfolgreich (JWT-Token erhalten)
- [ ] Schülerdaten verfügbar
- [ ] Stundenplan-Daten abrufbar

### ✅ Integration-Checks

- [ ] Integration in Settings > Integrations sichtbar
- [ ] Konfiguration erfolgreich
- [ ] Sensoren werden erstellt
- [ ] Sensoren haben Daten
- [ ] Updates funktionieren

### ✅ UI-Checks

- [ ] Sensoren in States sichtbar
- [ ] Attribute korrekt gefüllt
- [ ] Custom Card lädt
- [ ] Dashboard zeigt Daten

## 🆘 Support und Hilfe

### Log-Sammlung für Support

```bash
# Vollständige Logs sammeln
docker logs schulmanager-ha-test > ha_logs.txt 2>&1

# Nur Schulmanager-relevante Logs
docker logs schulmanager-ha-test 2>&1 | grep -i schulmanager > schulmanager_logs.txt

# System-Informationen
echo "=== System Info ===" > debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
echo "=== Container Status ===" >> debug_info.txt
docker ps >> debug_info.txt
```

### Minimal-Reproduktion

```python
# Minimales Test-Script für Fehlerreproduktion
import asyncio
import aiohttp
from custom_components.schulmanager_online.api import SchulmanagerAPI

async def minimal_test():
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI("EMAIL", "PASSWORD", session)
        
        try:
            await api.authenticate()
            print("✅ Authentication successful")
            
            students = await api.get_students()
            print(f"✅ Found {len(students)} students")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(minimal_test())
```

### Community-Support

- **GitHub Issues**: Für Bug-Reports und Feature-Requests
- **Home Assistant Community**: Für allgemeine Fragen
- **Discord/Forum**: Für Echtzeit-Hilfe

## 📚 Weiterführende Dokumentation

- [API Analysis](API_Analysis.md) - API-Details
- [Authentication Guide](Authentication_Guide.md) - Authentifizierung
- [Integration Architecture](Integration_Architecture.md) - Architektur
- [Development Setup](Development_Setup.md) - Entwicklungsumgebung
