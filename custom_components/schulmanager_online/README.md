# Schulmanager Online Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/wunsch/schulmanager-online-hass.svg)](https://github.com/wunsch/schulmanager-online-hass/releases)
[![License](https://img.shields.io/github/license/wunsch/schulmanager-online-hass.svg)](LICENSE)

A comprehensive Home Assistant integration for **[Schulmanager Online](https://login.schulmanager-online.de/)**, providing real-time access to student schedules, homework assignments, and school information.

## ✨ Features

### 📊 **8 Comprehensive Sensors**
- **Current Lesson** - Shows the currently active lesson
- **Next Lesson** - Displays the upcoming lesson with countdown
- **Today's Lessons** - Count and details of today's classes
- **Today's Changes** - Substitutions and cancellations for today
- **Next School Day** - Information about the next school day (skips weekends)
- **This Week** - Complete schedule overview for current week
- **Next Week** - Schedule preview for upcoming week
- **Changes Detected** - Real-time detection of schedule modifications

### 📅 **Calendar Integration**
- **Schedule Calendar** - All lessons as calendar events ⚠️ *Times are estimates*
- **Homework Calendar** - Homework assignments with due dates
- **Smart Event Details** - Teacher, room, and substitution information

> **⚠️ Important Limitation**: The Schulmanager Online API only provides class hour numbers (e.g., "5th hour") but **not actual start/end times**. Calendar events use **estimated default times** based on typical German school schedules. Your school's actual lesson times may vary significantly.

### 🎨 **Custom Lovelace Card**
- **4 Different Views**: Matrix, Weekly List, Daily List, Compact
- **Responsive Design** - Optimized for mobile and desktop
- **Real-time Updates** - Automatic refresh with schedule changes
- **Multi-student Support** - Family mode for multiple children

### 🌍 **Multi-language Support**
Supports 12 languages: English, German, French, Spanish, Italian, Dutch, Portuguese, Polish, Russian, Swedish, Danish

## 🚀 Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click **Custom Repositories**
4. Add repository: `https://github.com/wunsch/schulmanager-online-hass`
5. Category: **Integration**
6. Click **Download**
7. **Restart Home Assistant**

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/wunsch/schulmanager-online-hass/releases)
2. Extract to `custom_components/schulmanager_online/`
3. Restart Home Assistant

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"**
3. Search for **"Schulmanager Online"**
4. Enter your credentials:
   - **Email/Username**: Your Schulmanager Online login
   - **Password**: Your password
5. Configure options:
   - **Weeks to look ahead**: 1-4 weeks (default: 2)
   - **Include homework calendar**: Enable homework tracking
   - **Include grades**: Experimental grades support

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `lookahead_weeks` | How many weeks ahead to fetch | 2 |
| `include_homework` | Enable homework calendar | `true` |
| `include_grades` | Enable grades (experimental) | `false` |

## 📱 Usage Examples

### Basic Dashboard Card

```yaml
type: entities
title: "School Schedule"
entities:
  - entity: sensor.student_name_current_lesson
    name: "Current Lesson"
  - entity: sensor.student_name_next_lesson
    name: "Next Lesson"
  - entity: sensor.student_name_today_changes
    name: "Today's Changes"
```

### Custom Schedule Card - 4 Different Views

**1. Weekly Matrix View (Traditional Schedule Grid)**
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: weekly_matrix
title: "Weekly Schedule"
show_header: true
show_breaks: true
highlight_current: true
highlight_changes: true
```

**2. Weekly List View (Chronological List)**
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: weekly_list
title: "This Week's Lessons"
show_header: true
```

**3. Daily List View (Today's Focus)**
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: daily_list
title: "Today's Schedule"
highlight_current: true
```

**4. Compact View (Mobile-Optimized)**
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: compact
title: "Current Status"
```

### Advanced Card Configuration

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: weekly_matrix
title: "Marc's Schedule"
show_header: true
show_breaks: true
color_scheme: "default"                    # default, dark, colorful
highlight_current: true                    # Highlight current lesson
highlight_changes: true                    # Highlight substitutions
max_days: 7                               # Maximum days to show
time_format: "24h"                        # 24h or 12h
language: "de"                            # de, en, fr, etc.
```

### Custom Styling

```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
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

### Automation Example

```yaml
automation:
  - alias: "School - Substitution Alert"
    trigger:
      - platform: state
        entity_id: sensor.student_name_changes_detected
        to: "1 change detected"
    action:
      - service: notify.mobile_app
        data:
          title: "📚 Schedule Change"
          message: "New substitution detected for {{ trigger.to_state.attributes.student_name }}"
```

## 🔧 Advanced Configuration

### Calendar Integration

#### Basic Calendar Cards

```yaml
# Basic calendar view
type: calendar
entities:
  - calendar.lessons_student_name
  - calendar.homework_student_name
title: "School Calendar"
```

#### Calendar with Different Views

```yaml
# Monthly view
type: calendar
entities:
  - calendar.lessons_student_name
title: "Monthly Schedule"
initial_view: dayGridMonth

# Weekly view
type: calendar
entities:
  - calendar.lessons_student_name
title: "Weekly Schedule"
initial_view: listWeek

# Daily view
type: calendar
entities:
  - calendar.lessons_student_name
title: "Today's Schedule"
initial_view: listDay
```

#### ⏰ Calendar Time Estimates

Since the Schulmanager Online API only provides class hour numbers without actual times, the integration uses these **default time estimates**:

| Class Hour | Estimated Time | Break After |
|------------|----------------|-------------|
| 1st hour  | 08:00 - 08:45  | 5 min       |
| 2nd hour  | 08:50 - 09:35  | 20 min      |
| 3rd hour  | 09:55 - 10:40  | 5 min       |
| 4th hour  | 10:45 - 11:30  | 10 min      |
| 5th hour  | 11:40 - 12:25  | 5 min       |
| 6th hour  | 12:30 - 13:15  | 5 min       |
| 7th hour  | 13:20 - 14:05  | 5 min       |
| 8th hour  | 14:10 - 14:55  | -           |

> **🏫 School-Specific Times**: These are estimates based on common German school schedules. Your school may have different lesson and break durations. The integration cannot determine actual times from the API data.

#### Complete School Dashboard

```yaml
type: vertical-stack
title: "School Dashboard"
cards:
  # Current Status (Compact)
  - type: custom:schulmanager-schedule-card
    entity: sensor.current_lesson_student_name
    view: compact
    
  # Today's Schedule (Daily List)
  - type: custom:schulmanager-schedule-card
    entity: sensor.current_lesson_student_name
    view: daily_list
    title: "Today's Lessons"
    
  # Calendar Integration
  - type: calendar
    entities:
      - calendar.lessons_student_name
      - calendar.homework_student_name
    initial_view: listWeek
    
  # Quick Stats
  - type: glance
    entities:
      - entity: sensor.lessons_today_student_name
        name: "Today"
      - entity: sensor.changes_detected_student_name
        name: "Changes"
      - entity: sensor.homework_due_today_student_name
        name: "Homework"
```

### Custom Card Configuration Options

| Option | Description | Default | Values |
|--------|-------------|---------|---------|
| `view` | Display mode | `weekly_matrix` | `weekly_matrix`, `weekly_list`, `daily_list`, `compact` |
| `show_header` | Show card header | `true` | `true`, `false` |
| `show_breaks` | Show break times | `true` | `true`, `false` |
| `highlight_current` | Highlight current lesson | `true` | `true`, `false` |
| `highlight_changes` | Highlight substitutions | `true` | `true`, `false` |
| `color_scheme` | Color theme | `default` | `default`, `dark`, `colorful` |
| `time_format` | Time display format | `24h` | `24h`, `12h` |
| `language` | Interface language | `de` | `de`, `en`, `fr`, `es`, etc. |
| `max_days` | Maximum days to display | `7` | `1-7` |

### Mobile-Optimized Configuration

```yaml
# Automatically adapts to mobile screens
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_student_name
view: daily_list  # Better for mobile
title: "Today's Schedule"
show_header: false  # Save space on mobile
```

### Custom Card Installation

Add to your Lovelace resources:

```yaml
# configuration.yaml
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module
```

### Template Sensors

```yaml
template:
  - sensor:
      - name: "Next Lesson Countdown"
        state: >
          {% set next_lesson = states('sensor.student_name_next_lesson') %}
          {% set minutes = state_attr('sensor.student_name_next_lesson', 'minutes_until') %}
          {% if minutes is not none and minutes > 0 %}
            {{ next_lesson }} in {{ minutes }} minutes
          {% else %}
            {{ next_lesson }}
          {% endif %}
```

## 🏗️ Architecture

### Data Flow
```
Schulmanager Online API → Authentication (PBKDF2-SHA512) → JWT Token → Data Coordinator → Sensors/Calendar → UI
```

### Update Intervals
- **Current/Next Lesson**: Every 5 minutes during school hours
- **Daily Schedule**: Every 15 minutes
- **Weekly Schedule**: Every hour
- **Change Detection**: Real-time comparison

## 🔐 Security & Privacy

- **Local Processing**: All data processing happens locally in Home Assistant
- **Secure Authentication**: Uses PBKDF2-SHA512 hashing with 99,999 iterations
- **Token Management**: Automatic JWT token renewal
- **No Data Storage**: No sensitive data is permanently stored

## 🐛 Troubleshooting

### Custom Card Issues

#### Problem: "Custom element doesn't exist: schulmanager-schedule-card"
**Symptoms:**
- Custom cards show "Configuration error" in dashboard
- Browser console shows: `Failed to resolve module specifier "lit"`

**Solution:**
1. **Check resource configuration** in `configuration.yaml`:
   ```yaml
   lovelace:
     resources:
       - url: /local/schulmanager-schedule-card.js
         type: module
   ```

2. **Restart Home Assistant** to reload the custom card
3. **Clear browser cache** (Ctrl+F5 or Cmd+Shift+R)
4. **Verify file loads** at: `http://your-ha:8123/local/schulmanager-schedule-card.js`

**Expected:** File should start with `class SchulmanagerScheduleCard extends HTMLElement`

### API Issues

#### Problem: 400 Bad Request Errors
**Symptoms:**
```
ERROR: Failed to get schedule for student: API call failed: 400
ERROR: Failed to get letters: API call failed: 400
```

**Possible Causes:**
- Incorrect API parameters or date format
- Changed Schulmanager Online API structure
- Missing permissions for student account
- Date range too far in future/past

**Debug Steps:**
1. Enable debug logging (see below)
2. Check API request payload in logs
3. Verify authentication works (status 200)
4. Test with different date ranges

#### Problem: 401 Authentication Errors
**Solutions:**
- Verify credentials in integration configuration
- Check for account lockout (too many failed attempts)
- Verify account type (parent vs. student account)
- Check Schulmanager Online service status

### Common Issues

**Authentication Failed**
- Verify your Schulmanager Online credentials
- Check if your account has student access
- Ensure 2FA is disabled for the integration account

**No Students Found**
- Confirm your account is linked to student profiles
- Check if you're using a parent or student account

**Sensors Show "Unavailable"**
- Check Home Assistant logs for API errors
- Verify internet connection
- Restart the integration

**Calendar Times Don't Match My School**
- This is expected behavior - times are estimates only
- Schulmanager API doesn't provide actual lesson start/end times
- Integration uses default German school schedule times
- Your school's actual times may be completely different

**Custom Cards Not Displaying Data**
- Check sensor entities exist: `sensor.{student_name}_current_lesson`
- Verify entity naming (lowercase with underscores)
- Check integration status in Settings → Devices & Services

### Debug Logging

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.schulmanager_online: debug
    homeassistant.components.sensor: info
    homeassistant.components.calendar: info
```

### Browser Developer Tools
1. **Open DevTools** (F12)
2. **Console tab** - Look for JavaScript errors
3. **Network tab** - Check resource loading (200 status)
4. **Clear cache** if needed

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/wunsch/schulmanager-online-hass.git

# Install development dependencies
cd test-scripts
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python test_api_complete.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Schulmanager Online](https://login.schulmanager-online.de/)** for providing the educational platform and API access
- **[Home Assistant](https://www.home-assistant.io/)** community for the excellent integration framework
- All contributors and testers who helped improve this integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wunsch/schulmanager-online-hass/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wunsch/schulmanager-online-hass/discussions)
- **Documentation**: [Full Documentation](../../documentation/README.md)

---

**⭐ If you find this integration useful, please consider giving it a star on GitHub!**
