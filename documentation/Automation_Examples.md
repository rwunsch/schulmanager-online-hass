# Home Assistant Automations - Schulmanager Online Integration

## 🎯 Overview

This documentation shows practical automation examples for the Schulmanager Online integration. All examples use the new unified sensor attributes, especially the `subject_sanitized` field for clean subject names.

## 📢 Voice Announcements (TTS - Text-to-Speech)

### 1. Morning School Announcement (Alexa)

**Purpose**: Daily at 07:10, today's school subjects are announced via Alexa, but only on weekdays and when there are classes.

```yaml
- id: school_announcement_student_weekdays_0710
  alias: School Announcement Student (weekdays 07:10)
  description: Weekday announcement at 07:10 with today's school subjects via Alexa,
    when classes are available.
  
  triggers:
  - trigger: time
    at: 07:10:00
  
  conditions:
  # Only on weekdays
  - condition: time
    weekday:
    - mon
    - tue
    - wed
    - thu
    - fri
  
  # Check if there are classes today (sensor state > 0)
  - condition: template
    value_template: '{{ states("sensor.lessons_today_student_name")|int(0) > 0 }}'
  
  # Additional check: lessons attribute exists and is not empty
  - condition: template
    value_template: >
      {% set lessons = state_attr("sensor.lessons_today_student_name","lessons") %}
      {{ lessons is iterable and lessons|length > 0 }}
  
  actions:
  - action: notify.alexa_media
    data:
      target:
      - media_player.alexa_bedroom
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) | sort(attribute='class_hour') %}
          {% set subjects = lessons | map(attribute='subject_sanitized') | list %}
          Good morning! <break time="400ms"/>
          Today you have the following subjects:
          {{ subjects | join(', ') }}.
          <break time="300ms"/>
          Better prepare your things now. Have fun and success at school!
        </speak>
  
  mode: single
```

**Automation Explanation:**

1. **Trigger**: Daily at 07:10
2. **Conditions**:
   - Only Monday through Friday (weekdays)
   - Sensor state > 0 (classes today)
   - Lessons array exists and is not empty
3. **Action**: 
   - Sorts lessons by `class_hour` (chronological order)
   - Extracts `subject_sanitized` for clean subject names
   - Announces subjects via Alexa

### 2. Dynamic Pre-School Announcement (Advanced)

**Purpose**: Automatically announces today's subjects X minutes before the first lesson starts. The timing is configurable via a Home Assistant helper.

**Prerequisites**: Create a helper in Home Assistant:
- **Name**: `input_number.school_pre_notice_minutes`
- **Minimum**: 0
- **Maximum**: 180
- **Step**: 1
- **Unit**: `min` (optional, for display)
- **Default**: 45

```yaml
- id: dynamic_pre_school_announcement
  alias: Dynamic Pre-School Announcement
  description: >
    Announces today's subjects X minutes before first lesson starts.
    Timing configurable via input_number.school_pre_notice_minutes helper.
    Includes exam notifications.
  
  trigger:
    - platform: template
      value_template: >-
        {% set minutes = states('input_number.school_pre_notice_minutes')|int(45) %}
        {% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or [])
           | sort(attribute='class_hour') %}
        {% if lessons|length > 0 and lessons[0].time %}
          {% set start_raw = lessons[0].time.split('-')[0] %}
          {% set start = start_raw ~ (':00' if start_raw|length == 5 else '') %}
          {% set dt = strptime((now().date()|string) ~ ' ' ~ start, '%Y-%m-%d %H:%M:%S') %}
          {% set announce = as_timestamp(dt) - minutes*60 %}
          {% set nowts = as_timestamp(now()) %}
          {{ nowts >= announce and nowts < (announce + 60) }}
        {% else %}
          false
        {% endif %}

  condition:
    - condition: time
      weekday: [mon, tue, wed, thu, fri]
    - condition: template
      value_template: "{{ states('sensor.lessons_today_student_name')|int(0) > 0 }}"
    - condition: template
      value_template: >-
        {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') %}
        {{ lessons is iterable and lessons|length > 0 }}

  action:
    - variables:
        minutes_before: "{{ states('input_number.school_pre_notice_minutes')|int(45) }}"
        lessons: "{{ (state_attr('sensor.lessons_today_student_name','lessons') or [])
                     | sort(attribute='class_hour') }}"
        # Extract clean subject names
        subjects: >-
          {% set s = lessons | map(attribute='subject_sanitized') | list %}
          {{ s | reject('equalto', none) | reject('equalto', '') | list }}
        subjects_str: >-
          {% if (subjects|length) > 1 %}
            {{ (subjects[:-1] | join(', ')) ~ ' and ' ~ subjects[-1] }}
          {% else %}
            {{ subjects|join('') }}
          {% endif %}
        # Get today's exams (if exam sensor exists)
        exams_today: >-
          {% set today = now().date()|string %}
          {% set exams_all = state_attr('sensor.exams_today_student_name','exams') or [] %}
          {{ exams_all | selectattr('date','equalto',today) | list }}
        exam_subjects: >-
          {% if exams_today|length > 0 %}
            {% set s = exams_today | map(attribute='subject') | list %}
            {% if s|length > 1 %}
              {{ (s[:-1] | join(', ')) ~ ' and ' ~ s[-1] }}
            {% else %}
              {{ s|join('') }}
            {% endif %}
          {% else %}{% endif %}

    - service: notify.alexa_media
      data:
        target:
          - media_player.alexa_bedroom
          - media_player.alexa_kitchen
        data:
          type: tts
        message: >-
          <speak>
            Good morning! <break time="400ms"/>
            Today you have the following subjects: {{ subjects_str }}.
            {% if exams_today|length > 0 %}
              <break time="300ms"/>
              Important: You have an exam in {{ exam_subjects }} today!
            {% endif %}
            <break time="300ms"/>
            School starts in {{ minutes_before }} minutes. Better prepare your things now!
            <break time="200ms"/>
            Have fun and success at school!
          </speak>
  
  mode: single
```

**How it Works:**
1. **Dynamic Timing**: Calculates when to announce based on first lesson start time minus configured minutes
2. **Template Trigger**: Fires when current time matches the calculated announcement time
3. **Smart Subject List**: Uses natural language ("Math, English and Science" vs "Math, English, Science")
4. **Exam Integration**: Announces if there are exams today (requires exam sensor)
5. **Configurable**: Change timing anytime via the helper without editing automation

**Testing the Automation:**

**Method A - Real Time Test (Recommended):**
1. Set `input_number.school_pre_notice_minutes` so that "first lesson - X minutes" equals the next full minute
2. Example: It's 08:14, first lesson at 08:45 → set to 30 (08:45 - 00:30 = 08:15)
3. Wait until 08:15:00 - automation should trigger

**Method B - Quick Test:**
1. Adjust `input_number.school_pre_notice_minutes` until "first lesson - X" falls into the next minute
2. Or temporarily modify the first lesson start time in your test data

**Method C - TTS/Message Test:**
1. Open the automation in Home Assistant
2. Click "Execute" to skip trigger and test the announcement immediately

### 3. Extended Morning Announcement with Details

```yaml
- id: detailed_school_announcement_weekdays_0715
  alias: Detailed School Announcement (weekdays 07:15)
  description: Extended announcement with first 3 lessons and substitutions
  
  triggers:
  - trigger: time
    at: 07:15:00
  
  conditions:
  - condition: time
    weekday: [mon, tue, wed, thu, fri]
  - condition: template
    value_template: '{{ states("sensor.lessons_today_student_name")|int(0) > 0 }}'
  
  actions:
  - action: notify.alexa_media
    data:
      target: [media_player.alexa_living_room]
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) | sort(attribute='class_hour') %}
          {% set changes = (state_attr('sensor.changes_today_student_name','changes') or []) %}
          
          Good morning! <break time="500ms"/>
          
          {% if lessons|length > 0 %}
            Today {{ lessons|length }} lessons are scheduled.
            <break time="400ms"/>
            
            The first three lessons are:
            {% for lesson in lessons[:3] %}
              {{ loop.index }}. Period: {{ lesson.subject_sanitized }}
              {% if lesson.is_substitution %} (Substitution){% endif %}
              <break time="200ms"/>
            {% endfor %}
            
            {% if changes|length > 0 %}
              <break time="400ms"/>
              Attention! There are {{ changes|length }} change{% if changes|length > 1 %}s{% endif %} today:
              {% for change in changes %}
                {{ change.subject_sanitized }} in the {{ change.class_hour }}. period
                {% if change.comment %} - {{ change.comment }}{% endif %}
                <break time="200ms"/>
              {% endfor %}
            {% endif %}
          {% endif %}
          
          <break time="400ms"/>
          Have a great school day!
        </speak>
  
  mode: single
```

## 📱 Notifications

### 4. Push Notification for Substitutions

```yaml
- id: substitution_notification
  alias: Notification for Substitutions
  description: Sends push notification when new substitutions are detected
  
  triggers:
  - trigger: state
    entity_id: sensor.changes_detected_student_name
    not_from: 
    - "No changes"
    - "unavailable"
    - "unknown"
  
  conditions:
  - condition: template
    value_template: '{{ trigger.to_state.state != "No changes" }}'
  
  actions:
  - action: notify.mobile_app_smartphone
    data:
      title: "📚 Schulmanager: New Substitutions"
      message: >
        {% set changes = state_attr('sensor.changes_detected_student_name', 'changes') or [] %}
        {% if changes|length == 1 %}
          A new substitution was detected:
        {% else %}
          {{ changes|length }} new substitutions were detected:
        {% endif %}
        {% for change in changes[:3] %}
          • {{ change.current.subject_sanitized if change.current else 'Unknown' }}
          {% if change.current and change.current.class_hour %} ({{ change.current.class_hour }}. period){% endif %}
        {% endfor %}
        {% if changes|length > 3 %}
          ... and {{ changes|length - 3 }} more
        {% endif %}
      data:
        actions:
        - action: "open_ha"
          title: "Show Details"
        tag: "schulmanager_changes"
        group: "schulmanager"
  
  mode: single
```

### 5. Daily Summary in the Evening

```yaml
- id: school_preview_evening
  alias: School Preview for Tomorrow (20:00)
  description: Evening summary of tomorrow's school subjects
  
  triggers:
  - trigger: time
    at: "20:00:00"
  
  conditions:
  # Only if tomorrow is a school day
  - condition: template
    value_template: >
      {% set tomorrow = (now() + timedelta(days=1)).strftime('%A') %}
      {{ tomorrow in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] }}
  
  # Only if there are classes tomorrow
  - condition: template
    value_template: '{{ states("sensor.lessons_tomorrow_student_name")|int(0) > 0 }}'
  
  actions:
  - action: notify.family_devices
    data:
      title: "📅 School Tomorrow"
      message: >
        {% set lessons = (state_attr('sensor.lessons_tomorrow_student_name','lessons') or []) | sort(attribute='class_hour') %}
        {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
        {% set changes = (state_attr('sensor.changes_today_student_name','changes') or []) %}
        
        Tomorrow {{ lessons|length }} periods are scheduled:
        {{ subjects | join(', ') }}
        
        {% if changes|length > 0 %}
        
        ⚠️ Attention: {{ changes|length }} substitution{% if changes|length > 1 %}s{% endif %} for tomorrow!
        {% endif %}
        
        School starts: {{ lessons[0].time.split('-')[0] if lessons else 'Unknown' }}
      data:
        tag: "school_preview"
        group: "schulmanager"
```

## 🏠 Smart Home Integration

### 6. Automatic Light in the Morning (only on school days)

```yaml
- id: morning_light_school_days
  alias: Morning Light on School Days
  description: Turns on bedroom light, but only when there's school today
  
  triggers:
  - trigger: time
    at: "06:45:00"
  
  conditions:
  - condition: time
    weekday: [mon, tue, wed, thu, fri]
  - condition: template
    value_template: '{{ states("sensor.lessons_today_student_name")|int(0) > 0 }}'
  - condition: state
    entity_id: light.bedroom
    state: 'off'
  
  actions:
  - action: light.turn_on
    target:
      entity_id: light.bedroom
    data:
      brightness_pct: 30
      color_temp: 400  # Warm light
  
  - delay: "00:00:30"
  
  - action: light.turn_on
    target:
      entity_id: light.bedroom
    data:
      brightness_pct: 80
      transition: 30  # Slowly get brighter
  
  mode: single
```

### 7. School Bag Reminder Based on Subjects

```yaml
- id: school_bag_reminder
  alias: School Bag Reminder by Subjects
  description: Specific reminders based on tomorrow's subjects
  
  triggers:
  - trigger: time
    at: "19:30:00"
  
  conditions:
  - condition: template
    value_template: '{{ states("sensor.lessons_tomorrow_student_name")|int(0) > 0 }}'
  
  actions:
  - action: notify.alexa_media
    data:
      target: [media_player.alexa_bedroom]
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_tomorrow_student_name','lessons') or []) %}
          {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
          
          Time to pack your school bag for tomorrow! <break time="500ms"/>
          
          Tomorrow you have: {{ subjects | join(', ') }}.
          <break time="400ms"/>
          
          {% if 'Physical Education' in subjects %}
            Don't forget your sports gear! <break time="300ms"/>
          {% endif %}
          
          {% if 'Art' in subjects or 'Crafts' in subjects %}
            Remember your art supplies! <break time="300ms"/>
          {% endif %}
          
          {% if 'Mathematics' in subjects or 'Physics' in subjects %}
            Pack your calculator! <break time="300ms"/>
          {% endif %}
          
          {% if 'Chemistry' in subjects or 'Biology' in subjects %}
            Don't forget your lab notebook! <break time="300ms"/>
          {% endif %}
          
          Good luck tomorrow at school!
        </speak>
  
  mode: single
```

## 📊 Dashboard Cards

### 8. Conditional Dashboard Display

```yaml
# In Lovelace Dashboard
type: conditional
conditions:
  - entity: sensor.lessons_today_student_name
    state_not: "0"
card:
  type: entities
  title: "🏫 Today at School"
  entities:
    - type: custom:template-entity-row
      entity: sensor.lessons_today_student_name
      name: "Lessons today"
      state: >
        {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
        {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
        {{ lessons|length }} lessons: {{ subjects | join(', ') }}
    
    - type: conditional
      conditions:
        - entity: sensor.changes_today_student_name
          state_not: "0"
      row:
        type: custom:template-entity-row
        entity: sensor.changes_today_student_name
        name: "⚠️ Substitutions"
        state: >
          {% set changes = state_attr('sensor.changes_today_student_name','changes') or [] %}
          {{ changes|length }} change{% if changes|length != 1 %}s{% endif %}
```

## 🔧 Utility Functions

### Template Sensors for Extended Functions

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Next School Lesson"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {% set now_time = now().strftime('%H:%M') %}
          {% for lesson in lessons | sort(attribute='class_hour') %}
            {% if lesson.time.split('-')[0] > now_time %}
              {{ lesson.subject_sanitized }} at {{ lesson.time.split('-')[0] }}
              {% break %}
            {% endif %}
          {% else %}
            No more lessons today
          {% endfor %}
        
      - name: "School Subjects Today (short)"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {% set subjects = lessons | map(attribute='subject_abbreviation') | unique | list %}
          {{ subjects | join(', ') if subjects else 'No school' }}
        
      - name: "Substitutions Today (count)"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {{ lessons | selectattr('is_substitution', 'equalto', true) | list | length }}
```

## 💡 Tips and Best Practices

### Using the Different Subject Fields:

- **`subject`**: For complete displays and logs
- **`subject_abbreviation`**: For compact UI elements  
- **`subject_sanitized`**: For voice output and user-friendly displays

### Template Debugging:

```yaml
# Test template in Developer Tools
{% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
{% for lesson in lessons %}
  Original: {{ lesson.subject }}
  Abbreviation: {{ lesson.subject_abbreviation }}  
  Sanitized: {{ lesson.subject_sanitized }}
  ---
{% endfor %}
```

### Error Handling:

Always use fallbacks in templates:
```yaml
{% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) %}
```

All examples use the new unified sensor attributes and the `subject_sanitized` field for optimal user-friendliness! 🎯
