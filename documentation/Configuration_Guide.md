# Konfiguration - Benutzer-Guide

## 🎯 Übersicht

Dieser Guide führt Sie durch die komplette Konfiguration der Schulmanager Online Integration in Home Assistant, von der ersten Einrichtung bis zur erweiterten Anpassung.

## 🚀 Erste Einrichtung

### 1. Integration hinzufügen

1. **Home Assistant öffnen** (http://localhost:8123)
2. **Settings** → **Devices & Services** aufrufen
3. **"+ ADD INTEGRATION"** klicken
4. **"Schulmanager Online"** suchen und auswählen
5. **Anmeldedaten eingeben**:
   - **Email/Username**: Ihre Schulmanager Online Anmeldedaten
   - **Password**: Ihr Passwort
6. **"SUBMIT"** klicken

### 2. Konfiguration validieren

Nach erfolgreicher Einrichtung sollten Sie sehen:
- ✅ **Integration erfolgreich hinzugefügt**
- ✅ **Schüler erkannt**: "Marc Cedric Wunsch" (oder Ihr Schüler)
- ✅ **Sensoren erstellt**: 8 Sensoren pro Schüler

### 3. Erste Überprüfung

```yaml
# Developer Tools > States
# Suchen Sie nach:
sensor.name_of_child_current_lesson
sensor.name_of_child_next_lesson
sensor.name_of_child_todays_lessons
# ... weitere Sensoren
```

## 📊 Sensor-Konfiguration

### Verfügbare Sensoren

Für jeden Schüler werden automatisch 8 Sensoren erstellt:

| Sensor | Entity ID | Beschreibung |
|--------|-----------|--------------|
| **Current Lesson** | `sensor.{student}_current_lesson` | Aktuelle Unterrichtsstunde |
| **Next Lesson** | `sensor.{student}_next_lesson` | Nächste Unterrichtsstunde |
| **Today's Lessons** | `sensor.{student}_todays_lessons` | Anzahl heutiger Stunden |
| **Today's Changes** | `sensor.{student}_todays_changes` | Anzahl heutiger Vertretungen |
| **Next School Day** | `sensor.{student}_next_school_day` | Nächster Schultag |
| **This Week** | `sensor.{student}_this_week` | Stunden diese Woche |
| **Next Week** | `sensor.{student}_next_week` | Stunden nächste Woche |
| **Changes Detected** | `sensor.{student}_changes_detected` | Erkannte Änderungen |

### Sensor-Anpassungen

```yaml
# configuration.yaml - Sensor-Namen anpassen
homeassistant:
  customize:
    sensor.name_of_child_current_lesson:
      friendly_name: "Aktuelle Stunde"
      icon: mdi:school
    sensor.name_of_child_next_lesson:
      friendly_name: "Nächste Stunde"
      icon: mdi:clock-outline
```

## 📅 Kalender-Integration

### Kalender aktivieren

Die Kalender-Integration wird automatisch mit der Hauptintegration aktiviert:

```yaml
# Kalender-Entity wird automatisch erstellt:
calendar.name_of_child_schedule
```

### Kalender-Konfiguration

```yaml
# configuration.yaml
calendar:
  - platform: schulmanager_online
    # Automatisch konfiguriert durch Integration
```

### Kalender in Lovelace

```yaml
# Dashboard-Card für Kalender
type: calendar
entities:
  - calendar.name_of_child_schedule
title: "Stundenplan"
initial_view: listWeek
```

## 🎨 Dashboard-Integration

### Basis-Dashboard

```yaml
# Einfache Entity-Card
type: entities
title: "Schulmanager - Marc Cedric"
entities:
  - entity: sensor.name_of_child_current_lesson
    name: "Aktuelle Stunde"
  - entity: sensor.name_of_child_next_lesson
    name: "Nächste Stunde"
  - entity: sensor.name_of_child_todays_changes
    name: "Heutige Vertretungen"
```

### Erweiterte Dashboard-Karten

```yaml
# Glance-Card für Übersicht
type: glance
title: "Stundenplan Übersicht"
entities:
  - entity: sensor.name_of_child_current_lesson
    name: "Jetzt"
  - entity: sensor.name_of_child_next_lesson
    name: "Als nächstes"
  - entity: sensor.name_of_child_todays_lessons
    name: "Heute"
  - entity: sensor.name_of_child_todays_changes
    name: "Vertretungen"
```

### Custom Card Integration

```yaml
# Schulmanager Custom Card
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
title: "Stundenplan Marc Cedric"
show_header: true
show_breaks: true
```

## 🔔 Benachrichtigungen

### Vertretungs-Benachrichtigungen

```yaml
# automations.yaml
- alias: "Schulmanager - Neue Vertretung"
  trigger:
    - platform: state
      entity_id: sensor.name_of_child_changes_detected
      to: "Neue Änderungen"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "📚 Stundenplan-Änderung"
        message: >
          Neue Vertretung für {{ state_attr('sensor.name_of_child_changes_detected', 'student_name') }}:
          {% set changes = state_attr('sensor.name_of_child_changes_detected', 'changes') %}
          {% if changes and changes|length > 0 %}
            {{ changes[0].subject }} am {{ changes[0].date }}
            {% if changes[0].new_teacher %}
              bei {{ changes[0].new_teacher }}
            {% endif %}
          {% endif %}
        data:
          tag: "schulmanager_changes"
          group: "schulmanager"
```

### Erinnerungen

```yaml
# Erinnerung vor Schulbeginn
- alias: "Schulmanager - Schule beginnt bald"
  trigger:
    - platform: template
      value_template: >
        {% set next_lesson = states('sensor.name_of_child_next_lesson') %}
        {% set minutes_until = state_attr('sensor.name_of_child_next_lesson', 'minutes_until') %}
        {{ minutes_until is not none and minutes_until == 30 }}
  action:
    - service: notify.family
      data:
        title: "🎒 Schule beginnt bald"
        message: >
          {{ state_attr('sensor.name_of_child_next_lesson', 'subject') }} 
          beginnt in 30 Minuten in Raum {{ state_attr('sensor.name_of_child_next_lesson', 'room') }}
```

## 🎯 Template-Sensoren

### Erweiterte Template-Sensoren

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Nächste Stunde mit Countdown"
        state: >
          {% set next_lesson = states('sensor.name_of_child_next_lesson') %}
          {% set minutes = state_attr('sensor.name_of_child_next_lesson', 'minutes_until') %}
          {% if minutes is not none and minutes > 0 %}
            {{ next_lesson }} (in {{ minutes }} min)
          {% else %}
            {{ next_lesson }}
          {% endif %}
        attributes:
          icon: mdi:clock-outline
          
      - name: "Schultag Status"
        state: >
          {% set current = states('sensor.name_of_child_current_lesson') %}
          {% set next = states('sensor.name_of_child_next_lesson') %}
          {% if current != 'Kein Unterricht' %}
            Unterricht läuft
          {% elif next != 'Kein weiterer Unterricht heute' %}
            Pause
          {% else %}
            Schulfrei
          {% endif %}
        attributes:
          current_lesson: "{{ states('sensor.name_of_child_current_lesson') }}"
          next_lesson: "{{ states('sensor.name_of_child_next_lesson') }}"
```

### Wöchentliche Statistiken

```yaml
template:
  - sensor:
      - name: "Wochenstunden Mathematik"
        state: >
          {% set week_data = state_attr('sensor.name_of_child_this_week', 'subjects_summary') %}
          {{ week_data.Mathematik if week_data else 0 }}
        unit_of_measurement: "Stunden"
        
      - name: "Vertretungen diese Woche"
        state: >
          {{ state_attr('sensor.name_of_child_this_week', 'total_changes') or 0 }}
        unit_of_measurement: "Vertretungen"
```

## 🔧 Erweiterte Konfiguration

### Update-Intervalle anpassen

```yaml
# Nicht direkt konfigurierbar, aber über Customization möglich
homeassistant:
  customize:
    sensor.name_of_child_current_lesson:
      # Sensor-spezifische Einstellungen
      scan_interval: 300  # 5 Minuten (Standard: 15 Minuten)
```

### Multi-User Setup (Familie)

```yaml
# Mehrere Integrationen für verschiedene Accounts
# Integration 1: Eltern-Account
# Integration 2: Schüler-Account (falls vorhanden)

# Gruppierung in Dashboard
type: vertical-stack
cards:
  - type: entities
    title: "Marc Cedric"
    entities:
      - sensor.name_of_child_current_lesson
      - sensor.name_of_child_next_lesson
  
  - type: entities
    title: "Anna Wunsch"  # Zweites Kind
    entities:
      - sensor.anna_wunsch_current_lesson
      - sensor.anna_wunsch_next_lesson
```

### Zeitzone-Konfiguration

```yaml
# configuration.yaml
homeassistant:
  time_zone: Europe/Berlin  # Wichtig für korrekte Zeitberechnung
  
# Explizite Zeitzone für Sensoren
template:
  - sensor:
      - name: "Aktuelle Stunde (Zeitzone-sicher)"
        state: >
          {% set now = now().astimezone() %}
          {% set current = states('sensor.name_of_child_current_lesson') %}
          {{ current }}
        attributes:
          local_time: "{{ now().strftime('%H:%M') }}"
          timezone: "{{ now().tzname() }}"
```

## 🎨 Themes und Styling

### Custom Theme für Schulmanager

```yaml
# themes.yaml
schulmanager_theme:
  # Hauptfarben
  primary-color: "#1976d2"          # Schulblau
  accent-color: "#ff9800"           # Orange für Highlights
  
  # Card-Farben
  card-background-color: "#ffffff"
  card-border-radius: "8px"
  
  # Sensor-spezifische Farben
  state-icon-color: "#1976d2"
  state-icon-active-color: "#ff9800"
  
  # Text-Farben
  primary-text-color: "#212121"
  secondary-text-color: "#757575"
  
  # Spezielle Schulmanager-Farben
  schulmanager-current-lesson: "#4caf50"    # Grün für aktuelle Stunde
  schulmanager-next-lesson: "#ff9800"       # Orange für nächste Stunde
  schulmanager-substitution: "#f44336"      # Rot für Vertretungen
```

### Card-spezifisches Styling

```yaml
type: entities
title: "Stundenplan"
style: |
  ha-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  .entity {
    color: white !important;
  }
entities:
  - sensor.name_of_child_current_lesson
```

## 🔍 Debugging und Logs

### Debug-Logging aktivieren

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
    custom_components.schulmanager_online.coordinator: debug
    custom_components.schulmanager_online.sensor: debug
    custom_components.schulmanager_online.calendar: debug
```

### Log-Analyse

```bash
# Home Assistant Logs filtern
grep -i "schulmanager" /config/home-assistant.log

# Spezifische Komponenten-Logs
grep "custom_components.schulmanager_online" /config/home-assistant.log
```

## 🔄 Wartung und Updates

### Integration aktualisieren

1. **HACS öffnen**
2. **Integrations** → **Schulmanager Online**
3. **Update** klicken (falls verfügbar)
4. **Home Assistant neu starten**

### Konfiguration zurücksetzen

```yaml
# Integration entfernen und neu hinzufügen
# Settings > Devices & Services > Schulmanager Online > Delete
# Dann neu konfigurieren
```

### Daten-Cache leeren

```bash
# Home Assistant neu starten um Cache zu leeren
# Oder über UI: Settings > System > Restart
```

## 🚨 Häufige Konfigurationsprobleme

### Problem: Sensoren zeigen "Unavailable"

**Lösung:**
```yaml
# Prüfen Sie die Integration in Settings > Devices & Services
# Neu konfigurieren falls nötig
# Debug-Logs aktivieren für Details
```

### Problem: Falsche Zeitzone

**Lösung:**
```yaml
# configuration.yaml
homeassistant:
  time_zone: Europe/Berlin  # Korrekte Zeitzone setzen
```

### Problem: Custom Card lädt nicht

**Lösung:**
```yaml
# Resource-Pfad prüfen
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module

# Browser-Cache leeren (Ctrl+F5)
# Home Assistant neu starten
```

## 📱 Mobile App Integration

### Mobile Dashboard

```yaml
# Spezielle Mobile-Ansicht
views:
  - title: Schule
    path: school
    icon: mdi:school
    panel: false
    cards:
      - type: custom:schulmanager-schedule-card
        entity: sensor.name_of_child_current_lesson
        view: compact  # Kompakte Ansicht für Mobile
        
      - type: entities
        entities:
          - sensor.name_of_child_todays_changes
          - sensor.name_of_child_next_school_day
```

### Push-Benachrichtigungen

```yaml
# Mobile App Benachrichtigungen
- service: notify.mobile_app_your_phone
  data:
    title: "📚 Schulmanager"
    message: "Neue Vertretung erkannt"
    data:
      tag: "schulmanager"
      group: "school"
      channel: "School Updates"
      importance: high
      icon_url: "/local/icons/school.png"
```

## 📚 Weiterführende Konfiguration

### Home Assistant Add-ons

```yaml
# Nützliche Add-ons für Schulmanager Integration:
# - File Editor (für Konfiguration)
# - Terminal & SSH (für Debugging)
# - Grafana (für erweiterte Visualisierung)
```

### Backup-Konfiguration

```yaml
# Wichtige Dateien für Backup:
# - configuration.yaml
# - automations.yaml
# - /config/custom_components/schulmanager_online/
# - Dashboard-Konfigurationen
```

## 📚 Weiterführende Dokumentation

- [Integration Architecture](Integration_Architecture.md) - Technische Details
- [Sensors Documentation](Sensors_Documentation.md) - Sensor-Referenz
- [Custom Card Documentation](Custom_Card_Documentation.md) - UI-Komponenten
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problemlösungen
