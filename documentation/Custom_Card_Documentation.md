# Custom Card - Detailed Documentation

## 🎯 Overview

The Schulmanager Schedule Card is a custom Lovelace card for Home Assistant that provides a user-friendly display of the schedule. It offers four different views and is fully configurable.

## 🎨 Available Views

### 1. Weekly Matrix (Week Matrix)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
```

**Description**: Shows the schedule as a traditional weekly matrix with days as columns and hours as rows.

**Features**:
- Clear table view
- Color coding by subjects
- Substitutions highlighted
- Current lesson marked

### 2. Weekly List (Week List)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_list
```

**Description**: Lists all lessons of the week chronologically.

**Features**:
- Chronological listing
- Detailed information per lesson
- Substitution notices
- Day grouping

### 3. Daily List (Day List)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: daily_list
```

**Description**: Shows only today's lessons.

**Features**:
- Focus on today
- Current/next lesson highlighted
- Countdown to next lesson
- Break times displayed

### 4. Compact (Compact)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: compact
```

**Description**: Minimal view for small dashboard areas.

**Features**:
- Only current and next lesson
- Space-saving
- Most important information
- Ideal for mobile

## 🔧 Configuration Options

### Basic Configuration

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson  # Required
view: weekly_matrix                               # Default: weekly_matrix
title: "Schedule Marc Cedric"                    # Optional
show_header: true                                # Default: true
show_breaks: true                                # Default: true
```

### Advanced Configuration

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
title: "Schedule"
show_header: true
show_breaks: true
color_scheme: "default"                          # default, dark, colorful
highlight_current: true                          # Highlight current lesson
highlight_changes: true                          # Highlight substitutions
max_days: 7                                     # Maximum number of days
time_format: "24h"                              # 24h or 12h
language: "de"                                  # de, en, fr, etc.
```

### Styling Options

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

## 🎨 Design System

### Color Schemes

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

### CSS Classes

| Class | Description |
|-------|-------------|
| `.schedule-card` | Main container |
| `.schedule-header` | Card header |
| `.schedule-content` | Main content area |
| `.schedule-matrix` | Matrix view container |
| `.schedule-list` | List view container |
| `.lesson-cell` | Individual lesson cell |
| `.current-lesson` | Current lesson |
| `.next-lesson` | Next lesson |
| `.substitution` | Substitution lesson |
| `.cancelled` | Cancelled lesson |
| `.break-time` | Break time |
| `.no-lesson` | Free period |

## 🔄 Data Binding

### Entity Attributes

The card expects the following attributes from the sensor:

```javascript
// Example Entity State
{
  "state": "Mathematics",
  "attributes": {
    "student_name": "Marc Cedric Wunsch",
    "current_lesson": {
      "subject": "Mathematics",
      "teacher": "Mr. Schmidt",
      "room": "R204",
      "start_time": "09:45",
      "end_time": "10:30"
    },
    "todays_lessons": [
      {
        "class_hour": "1",
        "start_time": "08:00",
        "end_time": "08:45",
        "subject": "German",
        "teacher": "Mrs. Müller",
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

### Data Transformation

```javascript
// In card implementation
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

## 🎭 UI Components

### Matrix View

```javascript
_renderMatrixView(scheduleData) {
  return html`
    <div class="schedule-matrix">
      <table>
        <thead>
          <tr>
            <th>Time</th>
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

### List View

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
            Substitution
          </div>
        ` : ''}
      </div>
    </div>
  `;
}
```

### Compact View

```javascript
_renderCompactView(scheduleData) {
  const currentLesson = scheduleData.currentLesson;
  const nextLesson = scheduleData.nextLesson;
  
  return html`
    <div class="schedule-compact">
      ${currentLesson ? html`
        <div class="current-lesson-compact">
          <div class="lesson-label">Now:</div>
          <div class="lesson-info">
            <span class="subject">${currentLesson.subject}</span>
            <span class="room">${currentLesson.room}</span>
            <span class="time">${currentLesson.start_time} - ${currentLesson.end_time}</span>
          </div>
        </div>
      ` : html`
        <div class="no-current-lesson">No lessons</div>
      `}
      
      ${nextLesson ? html`
        <div class="next-lesson-compact">
          <div class="lesson-label">Next:</div>
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

## 🔧 Card Editor

### Editor Configuration

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

### Mobile Optimizations

```javascript
_isMobile() {
  return window.innerWidth < 768;
}

_renderMobileOptimized(scheduleData) {
  if (this._isMobile() && this.config.view === 'weekly_matrix') {
    // Automatically switch to daily_list on mobile
    return this._renderDailyList(scheduleData);
  }
  
  return this._renderView(scheduleData);
}
```

## 🔄 Performance Optimization

### Lazy Rendering

```javascript
_shouldUpdate(changedProps) {
  // Only re-render when relevant properties have changed
  if (changedProps.has('hass')) {
    const oldHass = changedProps.get('hass');
    if (oldHass) {
      const oldEntity = oldHass.states[this.config.entity];
      const newEntity = this.hass.states[this.config.entity];
      
      // Only update when entity state or relevant attributes have changed
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
  
  // Limit cache size
  if (this._scheduleCache.size > 10) {
    const firstKey = this._scheduleCache.keys().next().value;
    this._scheduleCache.delete(firstKey);
  }
  
  return scheduleData;
}
```

## 🌍 Internationalization

### Language Support

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
    // ... more translations
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
    // ... more translations
  }
};

_translate(key) {
  const language = this.config.language || this.hass.language || 'en';
  return TRANSLATIONS[language]?.[key] || TRANSLATIONS.en[key] || key;
}
```

## 📚 Installation and Setup

### HACS Installation

1. **Open HACS** in Home Assistant
2. **Integrations** → **Custom Repositories**
3. **Add Repository**: `https://github.com/your-repo/schulmanager-online`
4. **Category**: Integration
5. **Download** and **Restart** Home Assistant

### Manual Installation

```bash
# Copy custom components
cp -r custom_components/schulmanager_online /config/custom_components/

# Copy card files
mkdir -p /config/www/schulmanager_online/
cp custom_components/schulmanager_online/www/* /config/www/schulmanager_online/

# Restart Home Assistant
```

### Resource Registration

```yaml
# configuration.yaml
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module
```

## 📚 Further Documentation

- [Integration Architecture](Integration_Architecture.md) - Overall architecture
- [Sensors Documentation](Sensors_Documentation.md) - Sensor details
- [Development Setup](Development_Setup.md) - Development environment
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solutions
