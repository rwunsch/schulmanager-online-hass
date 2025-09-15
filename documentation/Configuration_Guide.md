# Configuration - User Guide

## 🎯 Overview

This guide walks you through the complete configuration of the Schulmanager Online integration in Home Assistant, from initial setup to advanced customization.

## 🚀 Initial Setup

### 1. Add Integration

1. **Open Home Assistant** (http://localhost:8123)
2. Go to **Settings** → **Devices & Services**
3. Click **"+ ADD INTEGRATION"**
4. Search for and select **"Schulmanager Online"**
5. **Enter login credentials**:
   - **Email/Username**: Your Schulmanager Online login credentials
   - **Password**: Your password
6. Click **"SUBMIT"**

### 2. Validate Configuration

After successful setup, you should see:
- ✅ **Integration successfully added**
- ✅ **Student detected**: "Marc Cedric Wunsch" (or your student)
- ✅ **Sensors created**: 8 sensors per student

### 3. Initial Check

```yaml
# Developer Tools > States
# Search for:
sensor.name_of_child_current_lesson
sensor.name_of_child_next_lesson
sensor.name_of_child_todays_lessons
# ... additional sensors
```

## 📊 Sensor Configuration

### Available Sensors

For each student, 8 sensors are automatically created:

| Sensor | Entity ID | Description |
|--------|-----------|-------------|
| **Current Lesson** | `sensor.{student}_current_lesson` | Current lesson |
| **Next Lesson** | `sensor.{student}_next_lesson` | Next lesson |
| **Today's Lessons** | `sensor.{student}_todays_lessons` | Number of lessons today |
| **Today's Changes** | `sensor.{student}_todays_changes` | Number of substitutions today |
| **Next School Day** | `sensor.{student}_next_school_day` | Next school day |
| **This Week** | `sensor.{student}_this_week` | Lessons this week |
| **Next Week** | `sensor.{student}_next_week` | Lessons next week |
| **Changes Detected** | `sensor.{student}_changes_detected` | Detected changes |

### Sensor Customization

```yaml
# configuration.yaml - Customize sensor names
homeassistant:
  customize:
    sensor.name_of_child_current_lesson:
      friendly_name: "Current Lesson"
      icon: mdi:school
    sensor.name_of_child_next_lesson:
      friendly_name: "Next Lesson"
      icon: mdi:clock-outline
```

## 📅 Calendar Integration

### Enable Calendar

The calendar integration is automatically activated with the main integration:

```yaml
# Calendar entity is automatically created:
calendar.name_of_child_schedule
```

### Calendar Configuration

```yaml
# configuration.yaml
calendar:
  - platform: schulmanager_online
    # Automatically configured through integration
```

### Calendar in Lovelace

```yaml
# Dashboard card for calendar
type: calendar
entities:
  - calendar.name_of_child_schedule
title: "Schedule"
initial_view: listWeek
```

## 🎨 Dashboard Integration

### Basic Dashboard

```yaml
# Simple Entity Card
type: entities
title: "Schulmanager - Marc Cedric"
entities:
  - entity: sensor.name_of_child_current_lesson
    name: "Current Lesson"
  - entity: sensor.name_of_child_next_lesson
    name: "Next Lesson"
  - entity: sensor.name_of_child_todays_changes
    name: "Today's Substitutions"
```

### Advanced Dashboard Cards

```yaml
# Glance Card for overview
type: glance
title: "Schedule Overview"
entities:
  - entity: sensor.name_of_child_current_lesson
    name: "Now"
  - entity: sensor.name_of_child_next_lesson
    name: "Next"
  - entity: sensor.name_of_child_todays_lessons
    name: "Today"
  - entity: sensor.name_of_child_todays_changes
    name: "Substitutions"
```

### Custom Card Integration

```yaml
# Schulmanager Custom Card
type: custom:schulmanager-schedule-card
entity: sensor.name_of_child_current_lesson
view: weekly_matrix
title: "Schedule Marc Cedric"
show_header: true
show_breaks: true
```

## 🔔 Notifications

### Substitution Notifications

```yaml
# automations.yaml
- alias: "Schulmanager - New Substitution"
  trigger:
    - platform: state
      entity_id: sensor.name_of_child_changes_detected
      to: "New Changes"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "📚 Schedule Change"
        message: >
          New substitution for {{ state_attr('sensor.name_of_child_changes_detected', 'student_name') }}:
          {% set changes = state_attr('sensor.name_of_child_changes_detected', 'changes') %}
          {% if changes and changes|length > 0 %}
            {{ changes[0].subject }} on {{ changes[0].date }}
            {% if changes[0].new_teacher %}
              with {{ changes[0].new_teacher }}
            {% endif %}
          {% endif %}
        data:
          tag: "schulmanager_changes"
          group: "schulmanager"
```

### Reminders

```yaml
# Reminder before school starts
- alias: "Schulmanager - School starts soon"
  trigger:
    - platform: template
      value_template: >
        {% set next_lesson = states('sensor.name_of_child_next_lesson') %}
        {% set minutes_until = state_attr('sensor.name_of_child_next_lesson', 'minutes_until') %}
        {{ minutes_until is not none and minutes_until == 30 }}
  action:
    - service: notify.family
      data:
        title: "🎒 School starts soon"
        message: >
          {{ state_attr('sensor.name_of_child_next_lesson', 'subject') }} 
          starts in 30 minutes in room {{ state_attr('sensor.name_of_child_next_lesson', 'room') }}
```

## 🎯 Template Sensors

### Advanced Template Sensors

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Next Lesson with Countdown"
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
          
      - name: "School Day Status"
        state: >
          {% set current = states('sensor.name_of_child_current_lesson') %}
          {% set next = states('sensor.name_of_child_next_lesson') %}
          {% if current != 'No lessons' %}
            Lesson in progress
          {% elif next != 'No more lessons today' %}
            Break
          {% else %}
            No school
          {% endif %}
        attributes:
          current_lesson: "{{ states('sensor.name_of_child_current_lesson') }}"
          next_lesson: "{{ states('sensor.name_of_child_next_lesson') }}"
```

### Weekly Statistics

```yaml
template:
  - sensor:
      - name: "Math Hours This Week"
        state: >
          {% set week_data = state_attr('sensor.name_of_child_this_week', 'subjects_summary') %}
          {{ week_data.Mathematics if week_data else 0 }}
        unit_of_measurement: "hours"
        
      - name: "Substitutions This Week"
        state: >
          {{ state_attr('sensor.name_of_child_this_week', 'total_changes') or 0 }}
        unit_of_measurement: "substitutions"
```

## 🔧 Advanced Configuration

### Adjust Update Intervals

```yaml
# Not directly configurable, but possible through customization
homeassistant:
  customize:
    sensor.name_of_child_current_lesson:
      # Sensor-specific settings
      scan_interval: 300  # 5 minutes (default: 15 minutes)
```

### Multi-User Setup (Family)

```yaml
# Multiple integrations for different accounts
# Integration 1: Parent account
# Integration 2: Student account (if available)

# Grouping in dashboard
type: vertical-stack
cards:
  - type: entities
    title: "Marc Cedric"
    entities:
      - sensor.name_of_child_current_lesson
      - sensor.name_of_child_next_lesson
  
  - type: entities
    title: "Anna Wunsch"  # Second child
    entities:
      - sensor.anna_wunsch_current_lesson
      - sensor.anna_wunsch_next_lesson
```

### Timezone Configuration

```yaml
# configuration.yaml
homeassistant:
  time_zone: Europe/Berlin  # Important for correct time calculation
  
# Explicit timezone for sensors
template:
  - sensor:
      - name: "Current Lesson (Timezone-safe)"
        state: >
          {% set now = now().astimezone() %}
          {% set current = states('sensor.name_of_child_current_lesson') %}
          {{ current }}
        attributes:
          local_time: "{{ now().strftime('%H:%M') }}"
          timezone: "{{ now().tzname() }}"
```

## 🎨 Themes and Styling

### Custom Theme for Schulmanager

```yaml
# themes.yaml
schulmanager_theme:
  # Main colors
  primary-color: "#1976d2"          # School blue
  accent-color: "#ff9800"           # Orange for highlights
  
  # Card colors
  card-background-color: "#ffffff"
  card-border-radius: "8px"
  
  # Sensor-specific colors
  state-icon-color: "#1976d2"
  state-icon-active-color: "#ff9800"
  
  # Text colors
  primary-text-color: "#212121"
  secondary-text-color: "#757575"
  
  # Special Schulmanager colors
  schulmanager-current-lesson: "#4caf50"    # Green for current lesson
  schulmanager-next-lesson: "#ff9800"       # Orange for next lesson
  schulmanager-substitution: "#f44336"      # Red for substitutions
```

### Card-specific Styling

```yaml
type: entities
title: "Schedule"
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

## 🔍 Debugging and Logs

### Enable Debug Logging

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

### Log Analysis

```bash
# Filter Home Assistant logs
grep -i "schulmanager" /config/home-assistant.log

# Specific component logs
grep "custom_components.schulmanager_online" /config/home-assistant.log
```

## 🔄 Maintenance and Updates

### Update Integration

1. **Open HACS**
2. **Integrations** → **Schulmanager Online**
3. Click **Update** (if available)
4. **Restart Home Assistant**

### Reset Configuration

```yaml
# Remove integration and add again
# Settings > Devices & Services > Schulmanager Online > Delete
# Then reconfigure
```

### Clear Data Cache

```bash
# Restart Home Assistant to clear cache
# Or via UI: Settings > System > Restart
```

## 🚨 Common Configuration Problems

### Problem: Sensors show "Unavailable"

**Solution:**
```yaml
# Check integration in Settings > Devices & Services
# Reconfigure if necessary
# Enable debug logs for details
```

### Problem: Wrong Timezone

**Solution:**
```yaml
# configuration.yaml
homeassistant:
  time_zone: Europe/Berlin  # Set correct timezone
```

### Problem: Custom Card doesn't load

**Solution:**
```yaml
# Check resource path
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module

# Clear browser cache (Ctrl+F5)
# Restart Home Assistant
```

## 📱 Mobile App Integration

### Mobile Dashboard

```yaml
# Special mobile view
views:
  - title: School
    path: school
    icon: mdi:school
    panel: false
    cards:
      - type: custom:schulmanager-schedule-card
        entity: sensor.name_of_child_current_lesson
        view: compact  # Compact view for mobile
        
      - type: entities
        entities:
          - sensor.name_of_child_todays_changes
          - sensor.name_of_child_next_school_day
```

### Push Notifications

```yaml
# Mobile app notifications
- service: notify.mobile_app_your_phone
  data:
    title: "📚 Schulmanager"
    message: "New substitution detected"
    data:
      tag: "schulmanager"
      group: "school"
      channel: "School Updates"
      importance: high
      icon_url: "/local/icons/school.png"
```

## 📚 Advanced Configuration

### Home Assistant Add-ons

```yaml
# Useful add-ons for Schulmanager integration:
# - File Editor (for configuration)
# - Terminal & SSH (for debugging)
# - Grafana (for advanced visualization)
```

### Backup Configuration

```yaml
# Important files for backup:
# - configuration.yaml
# - automations.yaml
# - /config/custom_components/schulmanager_online/
# - Dashboard configurations
```

## 📚 Further Documentation

- [Integration Architecture](Integration_Architecture.md) - Technical details
- [Sensors Documentation](Sensors_Documentation.md) - Sensor reference
- [Custom Card Documentation](Custom_Card_Documentation.md) - UI components
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solutions
