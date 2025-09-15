# Home Assistant Automationen - Schulmanager Online Integration

## 🎯 Übersicht

Diese Dokumentation zeigt praktische Automation-Beispiele für die Schulmanager Online Integration. Alle Beispiele nutzen die neuen einheitlichen Sensor-Attribute, insbesondere das `subject_sanitized` Feld für saubere Fächernamen.

## 📢 Sprachansagen (TTS - Text-to-Speech)

### 1. Morgendliche Schulansage (Alexa)

**Zweck**: Täglich um 07:10 Uhr werden die heutigen Schulfächer über Alexa angesagt, aber nur an Werktagen und wenn Unterricht stattfindet.

```yaml
- id: schulansage_student_werktags_0710
  alias: Schulansage Student (werktags 07:10)
  description: Werktags um 07:10 Alexa-Ansage mit den heutigen Schulfächern,
    wenn Unterricht vorhanden ist.
  
  triggers:
  - trigger: time
    at: 07:10:00
  
  conditions:
  # Nur an Werktagen
  - condition: time
    weekday:
    - mon
    - tue
    - wed
    - thu
    - fri
  
  # Prüfen ob heute Unterricht ist (Sensor-State > 0)
  - condition: template
    value_template: '{{ states("sensor.lessons_today_student_name")|int(0) > 0 }}'
  
  # Zusätzliche Prüfung: Lessons-Attribut existiert und ist nicht leer
  - condition: template
    value_template: >
      {% set lessons = state_attr("sensor.lessons_today_student_name","lessons") %}
      {{ lessons is iterable and lessons|length > 0 }}
  
  actions:
  - action: notify.alexa_media
    data:
      target:
      - media_player.alexa_kinderzimmer
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) | sort(attribute='class_hour') %}
          {% set subjects = lessons | map(attribute='subject_sanitized') | list %}
          Guten Morgen! <break time="400ms"/>
          Heute hast Du folgende Fächer:
          {{ subjects | join(', ') }}.
          <break time="300ms"/>
          Bereite am besten jetzt Deine Sachen vor. Viel Spaß und Erfolg in der Schule!
        </speak>
  
  mode: single
```

**Erklärung der Automation:**

1. **Trigger**: Täglich um 07:10 Uhr
2. **Bedingungen**:
   - Nur Montag bis Freitag (Werktage)
   - Sensor-State > 0 (heute ist Unterricht)
   - Lessons-Array existiert und ist nicht leer
3. **Aktion**: 
   - Sortiert Stunden nach `class_hour` (Reihenfolge)
   - Extrahiert `subject_sanitized` für saubere Fächernamen
   - Spricht die Fächer über Alexa aus

### 2. Erweiterte Morgenansage mit Details

```yaml
- id: schulansage_detailliert_werktags_0715
  alias: Detaillierte Schulansage (werktags 07:15)
  description: Erweiterte Ansage mit ersten 3 Stunden und Vertretungen
  
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
      target: [media_player.alexa_wohnzimmer]
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) | sort(attribute='class_hour') %}
          {% set changes = (state_attr('sensor.changes_today_student_name','changes') or []) %}
          
          Guten Morgen! <break time="500ms"/>
          
          {% if lessons|length > 0 %}
            Heute sind {{ lessons|length }} Stunden geplant.
            <break time="400ms"/>
            
            Die ersten drei Stunden sind:
            {% for lesson in lessons[:3] %}
              {{ loop.index }}. Stunde: {{ lesson.subject_sanitized }}
              {% if lesson.is_substitution %} (Vertretung){% endif %}
              <break time="200ms"/>
            {% endfor %}
            
            {% if changes|length > 0 %}
              <break time="400ms"/>
              Achtung! Es gibt {{ changes|length }} Änderung{% if changes|length > 1 %}en{% endif %} heute:
              {% for change in changes %}
                {{ change.subject_sanitized }} in der {{ change.class_hour }}. Stunde
                {% if change.comment %} - {{ change.comment }}{% endif %}
                <break time="200ms"/>
              {% endfor %}
            {% endif %}
          {% endif %}
          
          <break time="400ms"/>
          Einen schönen Schultag!
        </speak>
  
  mode: single
```

## 📱 Benachrichtigungen

### 3. Push-Benachrichtigung bei Vertretungen

```yaml
- id: vertretung_benachrichtigung
  alias: Benachrichtigung bei Vertretungen
  description: Sendet Push-Benachrichtigung wenn neue Vertretungen erkannt werden
  
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
      title: "📚 Schulmanager: Neue Vertretungen"
      message: >
        {% set changes = state_attr('sensor.changes_detected_student_name', 'changes') or [] %}
        {% if changes|length == 1 %}
          Eine neue Vertretung wurde erkannt:
        {% else %}
          {{ changes|length }} neue Vertretungen wurden erkannt:
        {% endif %}
        {% for change in changes[:3] %}
          • {{ change.current.subject_sanitized if change.current else 'Unbekannt' }}
          {% if change.current and change.current.class_hour %} ({{ change.current.class_hour }}. Stunde){% endif %}
        {% endfor %}
        {% if changes|length > 3 %}
          ... und {{ changes|length - 3 }} weitere
        {% endif %}
      data:
        actions:
        - action: "open_ha"
          title: "Details anzeigen"
        tag: "schulmanager_changes"
        group: "schulmanager"
  
  mode: single
```

### 4. Tägliche Zusammenfassung am Vorabend

```yaml
- id: schulvorschau_abends
  alias: Schulvorschau für morgen (20:00)
  description: Abendliche Zusammenfassung der morgigen Schulfächer
  
  triggers:
  - trigger: time
    at: "20:00:00"
  
  conditions:
  # Nur wenn morgen ein Schultag ist
  - condition: template
    value_template: >
      {% set tomorrow = (now() + timedelta(days=1)).strftime('%A') %}
      {{ tomorrow in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] }}
  
  # Nur wenn morgen Unterricht ist
  - condition: template
    value_template: '{{ states("sensor.lessons_tomorrow_student_name")|int(0) > 0 }}'
  
  actions:
  - action: notify.family_devices
    data:
      title: "📅 Schule morgen"
      message: >
        {% set lessons = (state_attr('sensor.lessons_tomorrow_student_name','lessons') or []) | sort(attribute='class_hour') %}
        {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
        {% set changes = (state_attr('sensor.changes_today_student_name','changes') or []) %}
        
        Morgen stehen {{ lessons|length }} Stunden auf dem Plan:
        {{ subjects | join(', ') }}
        
        {% if changes|length > 0 %}
        
        ⚠️ Achtung: {{ changes|length }} Vertretung{% if changes|length > 1 %}en{% endif %} für morgen!
        {% endif %}
        
        Schulbeginn: {{ lessons[0].time.split('-')[0] if lessons else 'Unbekannt' }}
      data:
        tag: "schulvorschau"
        group: "schulmanager"
```

## 🏠 Smart Home Integration

### 5. Automatisches Licht am Morgen (nur bei Schule)

```yaml
- id: morgenlicht_schultage
  alias: Morgenlicht an Schultagen
  description: Schaltet das Kinderzimmerlicht ein, aber nur wenn heute Schule ist
  
  triggers:
  - trigger: time
    at: "06:45:00"
  
  conditions:
  - condition: time
    weekday: [mon, tue, wed, thu, fri]
  - condition: template
    value_template: '{{ states("sensor.lessons_today_student_name")|int(0) > 0 }}'
  - condition: state
    entity_id: light.kinderzimmer
    state: 'off'
  
  actions:
  - action: light.turn_on
    target:
      entity_id: light.kinderzimmer
    data:
      brightness_pct: 30
      color_temp: 400  # Warmes Licht
  
  - delay: "00:00:30"
  
  - action: light.turn_on
    target:
      entity_id: light.kinderzimmer
    data:
      brightness_pct: 80
      transition: 30  # Langsam heller werden
  
  mode: single
```

### 6. Schultasche-Erinnerung basierend auf Fächern

```yaml
- id: schultasche_erinnerung
  alias: Schultasche-Erinnerung nach Fächern
  description: Spezifische Erinnerungen basierend auf morgigen Fächern
  
  triggers:
  - trigger: time
    at: "19:30:00"
  
  conditions:
  - condition: template
    value_template: '{{ states("sensor.lessons_tomorrow_student_name")|int(0) > 0 }}'
  
  actions:
  - action: notify.alexa_media
    data:
      target: [media_player.alexa_kinderzimmer]
      data:
        type: tts
      message: >
        <speak>
          {% set lessons = (state_attr('sensor.lessons_tomorrow_student_name','lessons') or []) %}
          {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
          
          Zeit, die Schultasche für morgen zu packen! <break time="500ms"/>
          
          Morgen hast Du: {{ subjects | join(', ') }}.
          <break time="400ms"/>
          
          {% if 'Sport' in subjects %}
            Vergiss nicht Deine Sportsachen! <break time="300ms"/>
          {% endif %}
          
          {% if 'Kunst' in subjects or 'Werken' in subjects %}
            Denk an Deine Kunstmaterialien! <break time="300ms"/>
          {% endif %}
          
          {% if 'Mathematik' in subjects or 'Physik' in subjects %}
            Pack Deinen Taschenrechner ein! <break time="300ms"/>
          {% endif %}
          
          {% if 'Chemie' in subjects or 'Biologie' in subjects %}
            Vergiss nicht Dein Laborbuch! <break time="300ms"/>
          {% endif %}
          
          Viel Erfolg morgen in der Schule!
        </speak>
  
  mode: single
```

## 📊 Dashboard-Karten

### 7. Bedingte Dashboard-Anzeige

```yaml
# In Lovelace Dashboard
type: conditional
conditions:
  - entity: sensor.lessons_today_student_name
    state_not: "0"
card:
  type: entities
  title: "🏫 Heute in der Schule"
  entities:
    - type: custom:template-entity-row
      entity: sensor.lessons_today_student_name
      name: "Stunden heute"
      state: >
        {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
        {% set subjects = lessons | map(attribute='subject_sanitized') | unique | list %}
        {{ lessons|length }} Stunden: {{ subjects | join(', ') }}
    
    - type: conditional
      conditions:
        - entity: sensor.changes_today_student_name
          state_not: "0"
      row:
        type: custom:template-entity-row
        entity: sensor.changes_today_student_name
        name: "⚠️ Vertretungen"
        state: >
          {% set changes = state_attr('sensor.changes_today_student_name','changes') or [] %}
          {{ changes|length }} Änderung{% if changes|length != 1 %}en{% endif %}
```

## 🔧 Utility-Funktionen

### Template-Sensoren für erweiterte Funktionen

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Nächste Schulstunde"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {% set now_time = now().strftime('%H:%M') %}
          {% for lesson in lessons | sort(attribute='class_hour') %}
            {% if lesson.time.split('-')[0] > now_time %}
              {{ lesson.subject_sanitized }} um {{ lesson.time.split('-')[0] }}
              {% break %}
            {% endif %}
          {% else %}
            Keine weiteren Stunden heute
          {% endfor %}
        
      - name: "Schulfächer heute (kurz)"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {% set subjects = lessons | map(attribute='subject_abbreviation') | unique | list %}
          {{ subjects | join(', ') if subjects else 'Keine Schule' }}
        
      - name: "Vertretungen heute (Anzahl)"
        state: >
          {% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
          {{ lessons | selectattr('is_substitution', 'equalto', true) | list | length }}
```

## 💡 Tipps und Best Practices

### Verwendung der verschiedenen Subject-Felder:

- **`subject`**: Für vollständige Anzeigen und Logs
- **`subject_abbreviation`**: Für kompakte UI-Elemente  
- **`subject_sanitized`**: Für Sprachausgabe und benutzerfreundliche Anzeigen

### Template-Debugging:

```yaml
# Test-Template im Developer Tools
{% set lessons = state_attr('sensor.lessons_today_student_name','lessons') or [] %}
{% for lesson in lessons %}
  Original: {{ lesson.subject }}
  Abbreviation: {{ lesson.subject_abbreviation }}  
  Sanitized: {{ lesson.subject_sanitized }}
  ---
{% endfor %}
```

### Fehlerbehandlung:

Verwende immer Fallbacks in Templates:
```yaml
{% set lessons = (state_attr('sensor.lessons_today_student_name','lessons') or []) %}
```

Alle Beispiele nutzen die neuen einheitlichen Sensor-Attribute und das `subject_sanitized` Feld für optimale Benutzerfreundlichkeit! 🎯
