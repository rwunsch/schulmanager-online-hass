# 🎓 Schulmanager Online Integration for Home Assistant

A comprehensive Home Assistant integration for **[Schulmanager Online](https://login.schulmanager-online.de/)** with extended sensors and calendar integration. A powerful custom UI card will be available in the future.

## ✨ Features

### 📊 Sensors (8 per child)
- **Current Lesson**: Shows the currently active lesson
- **Next Lesson**: Shows the next upcoming lesson
- **Today's Lessons**: Count and details of today's lessons
- **Today's Changes**: Substitutions and changes for today
- **Next School Day**: Lessons for the next school day (skips weekends)
- **This Week**: Complete overview of the current school week
- **Next Week**: Complete overview of the next school week
- **Changes Detected**: Diff sensor with before/after comparison

### 📅 Calendar (per child)
- **Schedule Calendar**: All lessons as calendar entries ⚠️ *Times are estimates*
- **Homework Calendar**: Homework with due dates (optional)
- **Substitution Plan**: Automatic marking of substitutions

> **⚠️ Important Note**: The Schulmanager Online API only provides class hour numbers (e.g., "5th hour") but **not actual start/end times**. The calendar uses **estimated default times** based on typical German school schedules (1st hour: 08:00-08:45, 5th hour: 11:40-12:25, etc.). Actual lesson times may vary by school.

### 🎨 Custom UI Card (Future Feature)
- **Coming Soon**: A powerful custom card with multiple view modes
- **Planned Features**: Matrix, Week List, Day List, Current/Next Lesson views
- **Multi-Student Support**: Will automatically detect all students
- **Responsive Design**: Will be optimized for desktop and mobile
- **Fully Configurable**: Will be customizable via UI editor

### ⚙️ Configurable Options
- **Time Period**: 1-4 weeks ahead retrievable
- **Homework**: Optional enable/disable
- **Grades**: Optional enable/disable (planned)

### 👨‍👩‍👧‍👦 Multi-Child Support ("Family Mode")
- **Automatic Detection** of all children in the account
- **Separate Entities** per child (sensors + calendar)
- **Shared Configuration** but individual data per child
- **Family Calendar** with all children or separate calendars per child

## 🚀 Installation

### HACS (Recommended)
1. **HACS** → **Integrations** → **⋮** → **Custom Repositories**
2. Add repository: `https://github.com/wunsch/schulmanager-online-hass`
3. Category: **Integration**
4. Install **Schulmanager Online**
5. **Restart** Home Assistant

### Manual Installation
1. Copy `custom_components/schulmanager_online/` to `<config>/custom_components/`
2. Restart Home Assistant

## ⚙️ Configuration

### Via UI (Recommended)
1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"Schulmanager Online"**
3. Enter **Email** and **Password**
4. Configure **Options** (weeks, homework, etc.)
5. **Done!** 🎉

## 📱 Usage

### Sensors in Dashboards

#### Individual Sensors
```yaml
type: entity
entity: sensor.current_lesson_name_of_child
name: "Marc's Current Lesson"
icon: mdi:play-circle-outline
```

### Calendar Integration

The calendars automatically appear in the Home Assistant calendar view and can be used in calendar cards:

#### Basic Calendar Cards

```yaml
# Basic calendar view
type: calendar
entities:
  - calendar.lessons_name_of_child
  - calendar.homework_name_of_child
title: "School Calendar"
```

#### Calendar with Different Views

```yaml
# Monthly view
type: calendar
entities:
  - calendar.lessons_name_of_child
title: "Monthly Schedule"
initial_view: dayGridMonth

# Weekly view
type: calendar
entities:
  - calendar.lessons_name_of_child
title: "Weekly Schedule"
initial_view: listWeek

# Daily view
type: calendar
entities:
  - calendar.lessons_name_of_child
title: "Today's Schedule"
initial_view: listDay
```

> **📝 Calendar Time Estimates**: Since the Schulmanager API doesn't provide actual lesson start/end times, the calendar uses these **estimated default times**:
> - 1st hour: 08:00-08:45
> - 2nd hour: 08:50-09:35  
> - 3rd hour: 09:55-10:40
> - 4th hour: 10:45-11:30
> - 5th hour: 11:40-12:25
> - 6th hour: 12:30-13:15
> - 7th hour: 13:20-14:05
> - 8th hour: 14:10-14:55
> - And so on...
>
> **Your school's actual times may differ!** These are estimates based on typical German school schedules.

#### Complete School Dashboard

```yaml
type: vertical-stack
title: "School Dashboard"
cards:
  # Current Status
  - type: entities
    entities:
      - entity: sensor.current_lesson_name_of_child
        name: "Current Lesson"
      - entity: sensor.next_lesson_name_of_child
        name: "Next Lesson"
    
  # Calendar Integration
  - type: calendar
    entities:
      - calendar.lessons_name_of_child
      - calendar.homework_name_of_child
    initial_view: listWeek
    
  # Quick Stats
  - type: glance
    entities:
      - entity: sensor.lessons_today_name_of_child
        name: "Today"
      - entity: sensor.changes_detected_name_of_child
        name: "Changes"
      - entity: sensor.homework_due_today_name_of_child
        name: "Homework"
```

### Automations

```yaml
# Example: Notification for substitutions
automation:
  - alias: "Substitution Detected"
    trigger:
      - platform: state
        entity_id: sensor.name_of_child_changes_detected
        to: 
          - "1 change detected"
    action:
      - service: notify.mobile_app
        data:
          title: "Schedule Change"
          message: >
            {{ states('sensor.name_of_child_changes_detected') }}
            Details: {{ state_attr('sensor.name_of_child_changes_detected', 'changes')[0]['description'] }}

# Example: Reminder before current lesson
automation:
  - alias: "Current Lesson Reminder"
    trigger:
      - platform: state
        entity_id: sensor.name_of_child_current_lesson
        from: "No current lesson"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Marc now has {{ states('sensor.name_of_child_current_lesson') }}
```

## 🎨 Custom Card (Coming Soon)

### Future Development
A powerful custom schedule card is currently in development and will include:

- **Multiple View Modes**: Weekly matrix, weekly list, daily list, and compact views
- **Interactive Interface**: Easy switching between different display modes
- **Multi-Student Support**: Automatic detection and display of all students
- **Responsive Design**: Optimized for both desktop and mobile devices
- **Customizable Themes**: Multiple color schemes and styling options
- **Advanced Configuration**: Extensive customization options via UI editor

Stay tuned for updates on this exciting feature!

## 🔧 Advanced Configuration

### Adjust Options
1. **Settings** → **Devices & Services** → **Schulmanager Online**
2. Click **Configure**
3. Adjust options:
   - **Weeks Ahead**: 1-4 weeks
   - **Homework**: Enable/Disable
   - **Grades**: Enable/Disable (experimental)

### YAML Configuration
```yaml
# configuration.yaml
schulmanager_online:
  email: "your@email.com"
  password: "YourPassword"
  weeks_ahead: 2
  include_homework: true
  include_grades: false
```

## 🧪 Development & Testing

### Docker Testing Setup
```bash
cd test-scripts
docker compose up -d
```

### Available Services
- **Home Assistant**: http://localhost:8123

### API Testing
```bash
# Run API tests directly
cd test-scripts
python test_api_complete.py
python test_schedule_api.py
python test_homework_api.py
```

## 🐛 Troubleshooting

### Common Issues

#### Login Errors
- **Check Credentials**: Email and password correct?
- **Account Type**: Use parent account (not student account)
- **Two-Factor Authentication**: Currently not supported

#### No Data
- **Students Present**: Are children registered in the account?
- **Permissions**: Does the account have access to schedules?
- **School Holidays**: Often no data available during holidays

#### Calendar Times Don't Match School Schedule
- **Expected Behavior**: Calendar times are estimates only
- **Root Cause**: Schulmanager API doesn't provide actual lesson times
- **Solution**: Times are based on typical German school schedules and may not match your specific school

#### Integration Won't Load
- **Restart Home Assistant** after installation
- **Check Logs**: `Settings → System → Logs`
- **Update HACS** if installed via HACS

### Debug Logs
```yaml
# configuration.yaml
logger:
  logs:
    custom_components.schulmanager_online: debug
```

## 🔧 Troubleshooting

### Custom Card Issues

#### Problem: "Custom element doesn't exist: schulmanager-schedule-card"
**Symptoms:**
- Custom cards show "Configuration error" in dashboard
- Browser console shows: `Failed to resolve module specifier "lit"`

**Root Cause:**
The custom card JavaScript file contains ES6 module imports that aren't compatible with Home Assistant's frontend loading mechanism.

**Solution:**
1. **Check resource configuration** in `configuration.yaml`:
   ```yaml
   lovelace:
     resources:
       - url: /local/schulmanager-schedule-card.js
         type: module
   ```

2. **Restart Home Assistant** to reload the custom card:
   ```bash
   # If using Docker
   docker restart <container-name>
   
   # Or via Home Assistant UI
   Settings → System → Restart
   ```

3. **Clear browser cache** (Ctrl+F5 or Cmd+Shift+R)

4. **Verify file is loaded** by navigating to:
   ```
   http://your-ha-instance:8123/local/schulmanager-schedule-card.js
   ```

**Expected Result:**
- File should start with `class SchulmanagerScheduleCard extends HTMLElement`
- No "lit" import statements should be present
- File size should be ~8-9KB

#### Problem: Cards registered but not displaying data
**Symptoms:**
- Cards appear but show "No student data available"
- Integration is loaded and sensors exist

**Solution:**
1. **Check sensor entities** exist:
   ```
   sensor.{student_name}_current_lesson
   sensor.{student_name}_next_lesson
   ```

2. **Verify entity naming** matches card expectations:
   - Student names are converted to lowercase with underscores
   - Special characters are removed

3. **Check integration status** in Settings → Devices & Services

### API Issues

#### Problem: 400 Bad Request Errors
**Symptoms:**
```
ERROR: Failed to get schedule for student: API call failed: 400
ERROR: Failed to get letters: API call failed: 400
```

**Possible Causes:**
1. **Incorrect API parameters** - Student ID or date format issues
2. **Changed API structure** - Schulmanager Online updated their API
3. **Missing permissions** - Student account lacks access to certain data
4. **Date range issues** - Requesting data too far in the future/past

**Debug Steps:**
1. **Enable debug logging**:
   ```yaml
   logger:
     logs:
       custom_components.schulmanager_online: debug
   ```

2. **Check API request payload** in logs:
   ```
   Schedule request payload: [{'moduleName': 'schedules', 'endpointName': 'get-actual-lessons', ...}]
   ```

3. **Verify authentication** works (login should show status 200)

4. **Test with different date ranges** or parameters

#### Problem: 401 Authentication Errors
**Symptoms:**
```
Exception: Login failed: 401
```

**Solutions:**
1. **Verify credentials** in integration configuration
2. **Check for account lockout** - too many failed attempts
3. **Verify account type** - parent vs. student account differences
4. **Check Schulmanager Online service status**

### Docker Development Issues

#### Problem: File changes not reflected in container
**Solution:**
1. **Restart container** to pick up changes:
   ```bash
   cd test-scripts
   docker compose restart homeassistant
   ```

2. **Clear browser cache** after container restart

### General Debugging

#### Enable Comprehensive Logging
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.schulmanager_online: debug
    homeassistant.components.sensor: info
    homeassistant.components.calendar: info
```

#### Check Integration Health
1. **Settings** → **Devices & Services** → **Schulmanager Online**
2. Look for error messages or warnings
3. Check entity states in **Developer Tools** → **States**

#### Browser Developer Tools
1. **Open DevTools** (F12)
2. **Console tab** - Look for JavaScript errors
3. **Network tab** - Check if resources are loading (200 status)
4. **Application tab** → **Local Storage** - Clear if needed

## 🤝 Contributing

Contributions are welcome! 

1. **Fork** the repository
2. **Create Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push Branch** (`git push origin feature/AmazingFeature`)
5. **Open Pull Request**

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.

## 🙏 Acknowledgments

- **[Schulmanager Online](https://login.schulmanager-online.de/)** for providing the educational platform and API
- **Home Assistant Community** for support
- **HACS** for easy distribution

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wunsch/schulmanager-online-hass/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wunsch/schulmanager-online-hass/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## 🌍 Translations

The integration supports multiple languages:
- 🇩🇪 German (Deutsch)
- 🇺🇸 English
- 🇫🇷 French (Français)
- 🇪🇸 Spanish (Español)
- 🇮🇹 Italian (Italiano)
- 🇳🇱 Dutch (Nederlands)
- 🇵🇱 Polish (Polski)
- 🇵🇹 Portuguese (Português)
- 🇷🇺 Russian (Русский)
- 🇸🇪 Swedish (Svenska)
- 🇩🇰 Danish (Dansk)

## 🚀 Future Enhancements

### Planned Features
- **📊 Advanced Statistics**: Weekly/monthly evaluations, subject distribution charts
- **🔔 Smart Notifications**: Push notifications for substitutions, lesson reminders
- **📱 Mobile App Integration**: Companion app with offline sync
- **🎯 Advanced Automations**: Smart home integration based on schedule
- **📈 Performance Tracking**: Grade trends, homework completion rates
- **👥 Extended Family Features**: Sibling comparisons, family dashboard
- **🔗 External Integrations**: Google Calendar sync, Teams/Zoom integration

### Contribution Ideas
- Additional language translations
- Custom Lovelace card enhancements
- Advanced automation examples
- Performance optimizations
- Additional sensor types

---

**Made with ❤️ for the Home Assistant Community**