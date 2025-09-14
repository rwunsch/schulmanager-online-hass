# Custom Card - Detaillierte Dokumentation

## 🎯 Übersicht

Die Schulmanager Schedule Card ist eine Custom Lovelace Card für Home Assistant, die eine benutzerfreundliche Darstellung des Stundenplans ermöglicht. Sie bietet vier verschiedene Ansichten und ist vollständig konfigurierbar.

## 🎨 Verfügbare Ansichten

### 1. Weekly Matrix (Wochenmatrix)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
```

**Beschreibung**: Zeigt den Stundenplan als traditionelle Wochenmatrix mit Tagen als Spalten und Stunden als Zeilen.

**Features**:
- Übersichtliche Tabellenansicht
- Farbkodierung nach Fächern
- Vertretungen hervorgehoben
- Aktuelle Stunde markiert

### 2. Weekly List (Wochenliste)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_list
```

**Beschreibung**: Listet alle Stunden der Woche chronologisch auf.

**Features**:
- Chronologische Auflistung
- Detaillierte Informationen pro Stunde
- Vertretungshinweise
- Tagesgruppierung

### 3. Daily List (Tagesliste)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: daily_list
```

**Beschreibung**: Zeigt nur die Stunden des aktuellen Tages.

**Features**:
- Fokus auf heute
- Aktuelle/nächste Stunde hervorgehoben
- Countdown bis zur nächsten Stunde
- Pausenzeiten angezeigt

### 4. Compact (Kompakt)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: compact
```

**Beschreibung**: Minimale Ansicht für kleine Dashboard-Bereiche.

**Features**:
- Nur aktuelle und nächste Stunde
- Platzsparend
- Wichtigste Informationen
- Ideal für Mobile

## 🔧 Konfigurationsoptionen

### Basis-Konfiguration

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson  # Erforderlich
view: weekly_matrix                               # Standard: weekly_matrix
title: "Stundenplan Marc Cedric"                 # Optional
show_header: true                                # Standard: true
show_breaks: true                                # Standard: true
```

### Erweiterte Konfiguration

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
title: "Stundenplan"
show_header: true
show_breaks: true
color_scheme: "default"                          # default, dark, colorful
highlight_current: true                          # Aktuelle Stunde hervorheben
highlight_changes: true                          # Vertretungen hervorheben
max_days: 7                                     # Maximale Anzahl Tage
time_format: "24h"                              # 24h oder 12h
language: "de"                                  # de, en, fr, etc.
```

### Styling-Optionen

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
style: |
  ha-card {
    --primary-color: #1976d2;
    --accent-color: #ff9800;
    --card-background-color: #fafafa;
  }
  .current-lesson {
    background-color: var(--accent-color) !important;
    color: white !important;
  }
  .substitution {
    border-left: 4px solid #f44336 !important;
  }
```

## 🎨 Design-System

### Farbschemas

#### Default Theme
```css
:host {
  --primary-color: #1976d2;
  --secondary-color: #424242;
  --accent-color: #ff9800;
  --error-color: #f44336;
  --warning-color: #ff9800;
  --success-color: #4caf50;
  --background-color: #fafafa;
  --card-background-color: #ffffff;
  --text-primary-color: #212121;
  --text-secondary-color: #757575;
}
```

#### Dark Theme
```css
:host([theme="dark"]) {
  --primary-color: #90caf9;
  --secondary-color: #b0bec5;
  --accent-color: #ffb74d;
  --background-color: #121212;
  --card-background-color: #1e1e1e;
  --text-primary-color: #ffffff;
  --text-secondary-color: #b0bec5;
}
```

### CSS-Klassen

| Klasse | Beschreibung |
|--------|--------------|
| `.schedule-card` | Haupt-Container |
| `.schedule-header` | Card-Header |
| `.schedule-content` | Haupt-Inhaltsbereich |
| `.schedule-matrix` | Matrix-Ansicht Container |
| `.schedule-list` | Listen-Ansicht Container |
| `.lesson-cell` | Einzelne Stunden-Zelle |
| `.current-lesson` | Aktuelle Stunde |
| `.next-lesson` | Nächste Stunde |
| `.substitution` | Vertretungsstunde |
| `.cancelled` | Ausgefallene Stunde |
| `.break-time` | Pausenzeit |
| `.no-lesson` | Freistunde |

## 🔄 Datenanbindung

### Entity-Attribute

Die Card erwartet folgende Attribute vom Sensor:

```javascript
// Beispiel-Entity-State
{
  "state": "Mathematik",
  "attributes": {
    "student_name": "Marc Cedric Wunsch",
    "current_lesson": {
      "subject": "Mathematik",
      "teacher": "Herr Schmidt",
      "room": "R204",
      "start_time": "09:45",
      "end_time": "10:30"
    },
    "todays_lessons": [
      {
        "class_hour": "1",
        "start_time": "08:00",
        "end_time": "08:45",
        "subject": "Deutsch",
        "teacher": "Frau Müller",
        "room": "R105"
      }
    ],
    "this_week": {
      "school_days": [
        {
          "date": "2025-09-14",
          "lessons": [...]
        }
      ]
    }
  }
}
```

### Daten-Transformation

```javascript
// In der Card-Implementierung
_transformScheduleData(entity) {
  const attributes = entity.attributes;
  
  return {
    currentLesson: attributes.current_lesson,
    nextLesson: attributes.next_lesson,
    todaysLessons: attributes.todays_lessons || [],
    weeklySchedule: attributes.this_week?.school_days || [],
    changes: attributes.todays_changes?.changes || []
  };
}
```

## 🎭 UI-Komponenten

### Matrix-Ansicht

```javascript
_renderMatrixView(scheduleData) {
  return html`
    <div class="schedule-matrix">
      <table>
        <thead>
          <tr>
            <th>Zeit</th>
            ${this._renderDayHeaders(scheduleData)}
          </tr>
        </thead>
        <tbody>
          ${this._renderTimeSlots(scheduleData)}
        </tbody>
      </table>
    </div>
  `;
}

_renderTimeSlots(scheduleData) {
  const timeSlots = this._getTimeSlots(scheduleData);
  
  return timeSlots.map(slot => html`
    <tr>
      <td class="time-slot">
        ${slot.startTime} - ${slot.endTime}
      </td>
      ${this._renderLessonsForTimeSlot(slot, scheduleData)}
    </tr>
  `);
}
```

### Listen-Ansicht

```javascript
_renderListView(scheduleData) {
  return html`
    <div class="schedule-list">
      ${scheduleData.weeklySchedule.map(day => html`
        <div class="day-section">
          <h3 class="day-header">${this._formatDate(day.date)}</h3>
          <div class="lessons-container">
            ${day.lessons.map(lesson => this._renderLessonItem(lesson))}
          </div>
        </div>
      `)}
    </div>
  `;
}

_renderLessonItem(lesson) {
  const isSubstitution = lesson.is_substitution;
  const isCurrent = this._isCurrentLesson(lesson);
  
  return html`
    <div class="lesson-item ${isSubstitution ? 'substitution' : ''} ${isCurrent ? 'current-lesson' : ''}">
      <div class="lesson-time">
        ${lesson.start_time} - ${lesson.end_time}
      </div>
      <div class="lesson-details">
        <div class="lesson-subject">${lesson.subject}</div>
        <div class="lesson-teacher">${lesson.teacher}</div>
        <div class="lesson-room">${lesson.room}</div>
        ${isSubstitution ? html`
          <div class="substitution-info">
            <mwc-icon>swap_horiz</mwc-icon>
            Vertretung
          </div>
        ` : ''}
      </div>
    </div>
  `;
}
```

### Kompakt-Ansicht

```javascript
_renderCompactView(scheduleData) {
  const currentLesson = scheduleData.currentLesson;
  const nextLesson = scheduleData.nextLesson;
  
  return html`
    <div class="schedule-compact">
      ${currentLesson ? html`
        <div class="current-lesson-compact">
          <div class="lesson-label">Jetzt:</div>
          <div class="lesson-info">
            <span class="subject">${currentLesson.subject}</span>
            <span class="room">${currentLesson.room}</span>
            <span class="time">${currentLesson.start_time} - ${currentLesson.end_time}</span>
          </div>
        </div>
      ` : html`
        <div class="no-current-lesson">Kein Unterricht</div>
      `}
      
      ${nextLesson ? html`
        <div class="next-lesson-compact">
          <div class="lesson-label">Als nächstes:</div>
          <div class="lesson-info">
            <span class="subject">${nextLesson.subject}</span>
            <span class="room">${nextLesson.room}</span>
            <span class="time">${nextLesson.start_time}</span>
          </div>
        </div>
      ` : ''}
    </div>
  `;
}
```

## 🔧 Card-Editor

### Editor-Konfiguration

```javascript
// schulmanager-schedule-card-editor.js
class SchulmanagerScheduleCardEditor extends LitElement {
  
  static get properties() {
    return {
      hass: {},
      config: {}
    };
  }
  
  setConfig(config) {
    this.config = config;
  }
  
  render() {
    return html`
      <div class="card-config">
        <paper-input
          label="Entity"
          .value=${this.config.entity || ''}
          .configValue=${'entity'}
          @value-changed=${this._valueChanged}
        ></paper-input>
        
        <paper-dropdown-menu label="View">
          <paper-listbox 
            slot="dropdown-content" 
            .selected=${this._getViewIndex()}
            @iron-select=${this._viewChanged}
          >
            <paper-item>Weekly Matrix</paper-item>
            <paper-item>Weekly List</paper-item>
            <paper-item>Daily List</paper-item>
            <paper-item>Compact</paper-item>
          </paper-listbox>
        </paper-dropdown-menu>
        
        <paper-input
          label="Title"
          .value=${this.config.title || ''}
          .configValue=${'title'}
          @value-changed=${this._valueChanged}
        ></paper-input>
        
        <ha-switch
          .checked=${this.config.show_header !== false}
          .configValue=${'show_header'}
          @change=${this._valueChanged}
        >
          Show Header
        </ha-switch>
        
        <ha-switch
          .checked=${this.config.show_breaks !== false}
          .configValue=${'show_breaks'}
          @change=${this._valueChanged}
        >
          Show Breaks
        </ha-switch>
      </div>
    `;
  }
  
  _valueChanged(ev) {
    const target = ev.target;
    const configValue = target.configValue;
    const value = target.checked !== undefined ? target.checked : target.value;
    
    if (this.config[configValue] === value) {
      return;
    }
    
    const newConfig = { ...this.config };
    newConfig[configValue] = value;
    
    const event = new CustomEvent('config-changed', {
      detail: { config: newConfig },
      bubbles: true,
      composed: true
    });
    this.dispatchEvent(event);
  }
}

customElements.define('schulmanager-schedule-card-editor', SchulmanagerScheduleCardEditor);
```

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile (< 768px) */
@media (max-width: 767px) {
  .schedule-matrix table {
    font-size: 0.8rem;
  }
  
  .lesson-cell {
    padding: 4px;
    min-height: 40px;
  }
  
  .schedule-list .lesson-item {
    padding: 8px;
  }
}

/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
  .schedule-matrix {
    overflow-x: auto;
  }
  
  .lesson-cell {
    min-width: 120px;
  }
}

/* Desktop (> 1024px) */
@media (min-width: 1025px) {
  .schedule-matrix table {
    width: 100%;
    table-layout: fixed;
  }
  
  .lesson-cell {
    min-height: 60px;
  }
}
```

### Mobile-Optimierungen

```javascript
_isMobile() {
  return window.innerWidth < 768;
}

_renderMobileOptimized(scheduleData) {
  if (this._isMobile() && this.config.view === 'weekly_matrix') {
    // Automatisch zu daily_list wechseln auf Mobile
    return this._renderDailyList(scheduleData);
  }
  
  return this._renderView(scheduleData);
}
```

## 🔄 Performance-Optimierung

### Lazy Rendering

```javascript
_shouldUpdate(changedProps) {
  // Nur re-rendern wenn sich relevante Properties geändert haben
  if (changedProps.has('hass')) {
    const oldHass = changedProps.get('hass');
    if (oldHass) {
      const oldEntity = oldHass.states[this.config.entity];
      const newEntity = this.hass.states[this.config.entity];
      
      // Nur updaten wenn sich Entity-State oder relevante Attribute geändert haben
      return !oldEntity || 
             oldEntity.state !== newEntity.state ||
             JSON.stringify(oldEntity.attributes) !== JSON.stringify(newEntity.attributes);
    }
  }
  
  return changedProps.has('config');
}
```

### Caching

```javascript
constructor() {
  super();
  this._scheduleCache = new Map();
  this._lastCacheUpdate = null;
}

_getCachedScheduleData(entity) {
  const cacheKey = `${entity.entity_id}_${entity.last_updated}`;
  
  if (this._scheduleCache.has(cacheKey)) {
    return this._scheduleCache.get(cacheKey);
  }
  
  const scheduleData = this._transformScheduleData(entity);
  this._scheduleCache.set(cacheKey, scheduleData);
  
  // Cache-Größe begrenzen
  if (this._scheduleCache.size > 10) {
    const firstKey = this._scheduleCache.keys().next().value;
    this._scheduleCache.delete(firstKey);
  }
  
  return scheduleData;
}
```

## 🌍 Internationalisierung

### Sprach-Support

```javascript
const TRANSLATIONS = {
  de: {
    current_lesson: 'Aktuelle Stunde',
    next_lesson: 'Nächste Stunde',
    no_lesson: 'Kein Unterricht',
    break_time: 'Pause',
    substitution: 'Vertretung',
    cancelled: 'Entfällt',
    room: 'Raum',
    teacher: 'Lehrer',
    time: 'Zeit',
    monday: 'Montag',
    tuesday: 'Dienstag',
    // ... weitere Übersetzungen
  },
  en: {
    current_lesson: 'Current Lesson',
    next_lesson: 'Next Lesson',
    no_lesson: 'No Lesson',
    break_time: 'Break',
    substitution: 'Substitution',
    cancelled: 'Cancelled',
    room: 'Room',
    teacher: 'Teacher',
    time: 'Time',
    monday: 'Monday',
    tuesday: 'Tuesday',
    // ... weitere Übersetzungen
  }
};

_translate(key) {
  const language = this.config.language || this.hass.language || 'en';
  return TRANSLATIONS[language]?.[key] || TRANSLATIONS.en[key] || key;
}
```

## 📚 Installation und Setup

### HACS-Installation

1. **HACS öffnen** in Home Assistant
2. **Integrations** → **Custom Repositories**
3. **Repository hinzufügen**: `https://github.com/your-repo/schulmanager-online`
4. **Kategorie**: Integration
5. **Download** und **Restart** Home Assistant

### Manuelle Installation

```bash
# Custom Components kopieren
cp -r custom_components/schulmanager_online /config/custom_components/

# Card-Dateien kopieren
mkdir -p /config/www/schulmanager_online/
cp custom_components/schulmanager_online/www/* /config/www/schulmanager_online/

# Home Assistant neu starten
```

### Resource-Registration

```yaml
# configuration.yaml
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module
```

## 📚 Weiterführende Dokumentation

- [Integration Architecture](Integration_Architecture.md) - Gesamtarchitektur
- [Sensors Documentation](Sensors_Documentation.md) - Sensor-Details
- [Development Setup](Development_Setup.md) - Entwicklungsumgebung
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problemlösungen
