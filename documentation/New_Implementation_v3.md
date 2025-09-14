# Schulmanager Schedule Card v3.0.0 - Complete Rewrite

## 🎯 Overview

The Schulmanager Schedule Card has been completely rewritten from the ground up with modern ES6+ features, clean architecture, and enhanced functionality. This new implementation provides a responsive, maintainable, and feature-rich schedule display for Home Assistant.

## ✨ Key Features

### 🏗️ Modern Architecture
- **Clean ES6+ Code**: Modern JavaScript with proper class structure
- **Separation of Concerns**: Data handling, rendering, and styling are properly separated
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Debounced Rendering**: Efficient rendering with automatic debouncing
- **Memory Management**: Proper cleanup and resource management

### 📱 Responsive Design
- **Home Assistant Grid Integration**: Automatically adapts to HA's grid system
- **Dynamic Column Sizing**: Responds to `--column-size` CSS custom properties
- **Adaptive Text Display**: Shows full names or abbreviations based on available space
- **Mobile Optimized**: Responsive breakpoints for all screen sizes

### 🎨 Multiple View Modes

#### 1. Weekly Matrix (Default)
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child
view: weekly_matrix
```
- Traditional timetable grid layout
- Days as columns, hours as rows
- Color-coded lessons and substitutions
- Empty cells for free periods
- Responsive text sizing

#### 2. Weekly List
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child
view: weekly_list
```
- Day-by-day column layout
- Scrollable lesson cards per day
- Lesson count statistics
- Substitution highlighting

#### 3. Daily List
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child
view: daily_list
```
- Focus on today's schedule
- Current and next lesson status
- Chronological lesson list
- Clean, minimal design

#### 4. Compact
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child
view: compact
```
- Minimal space usage
- Current/next lesson display
- Statistics summary
- Perfect for small dashboard areas

## 🔧 Configuration Options

### Basic Configuration
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child  # Required
view: weekly_matrix                               # weekly_matrix, weekly_list, daily_list, compact
title: "Schedule"                                # Card title
show_header: true                                # Show/hide header
column_size: null                                # Auto-detect from HA grid or set manually
```

### Advanced Configuration
```yaml
type: custom:schulmanager-schedule-card
entity: sensor.current_lesson_name_of_child
view: weekly_matrix
title: "Marc's Schedule"
show_header: true
show_breaks: true                    # Show break periods (future feature)
highlight_current: true              # Highlight current lesson
highlight_changes: true              # Highlight substitutions
color_scheme: "default"             # Color scheme (future feature)
time_format: "24h"                  # Time format
language: "de"                      # Language
max_days: 7                         # Maximum days to display
```

## 📊 Data Integration

### Sensor Requirements
The card automatically detects and uses the following sensors for a student:
- `sensor.current_lesson_{student}`
- `sensor.next_lesson_{student}`
- `sensor.lessons_today_{student}`
- `sensor.this_week_{student}` ⭐ **Primary data source**
- `sensor.next_week_{student}`
- `sensor.changes_detected_{student}`

### Data Structure
The card expects lesson data in the following format from the `this_week` sensor:
```json
{
  "attributes": {
    "lessons": [
      {
        "subject": "Mathematik",
        "subject_abbreviation": "M",
        "teacher_firstname": "Max",
        "teacher_lastname": "Mustermann",
        "teacher": "MuM",
        "room": "RD205",
        "date": "2024-01-15",
        "time": "08:00:00-08:45:00",
        "start_time": "08:00:00",
        "end_time": "08:45:00",
        "class_hour": "1",
        "is_substitution": false,
        "type": "regularLesson",
        "comment": ""
      }
    ]
  }
}
```

## 🎨 Styling and Theming

### CSS Custom Properties
The card uses Home Assistant's CSS custom properties for theming:
```css
--primary-color: #3f51b5
--secondary-background-color: #f5f5f5
--card-background-color: #ffffff
--primary-text-color: #000000
--secondary-text-color: #666666
--divider-color: #e0e0e0
--warning-color: #ff9500
--error-color: #ff3b30
```

### Responsive Breakpoints
- **Desktop (>768px)**: Full names and detailed layout
- **Tablet (768px)**: Optimized for medium screens
- **Mobile (<768px)**: Compact layout with abbreviations
- **Small Mobile (<480px)**: Minimal layout

### Column Size Adaptation
The card automatically adapts based on Home Assistant's grid column size:
- **Columns 1-4**: Abbreviations only, compact layout
- **Columns 5-6**: Mixed display with smart text sizing
- **Columns 7+**: Full names and detailed information

## 🔍 Technical Implementation

### Architecture
```
SchulmanagerScheduleCard
├── Configuration Management
├── Data Layer
│   ├── Student Detection
│   ├── Sensor Integration  
│   └── Data Parsing
├── Rendering Engine
│   ├── View Mode Routing
│   ├── Matrix Rendering
│   ├── List Rendering
│   └── Error Handling
└── Styling System
    ├── Responsive CSS
    ├── Grid Integration
    └── Theme Support
```

### Key Methods
- `setConfig()`: Configuration initialization
- `set hass()`: Home Assistant integration
- `_updateData()`: Data extraction and parsing
- `_render()`: Main rendering orchestration
- `_renderWeeklyMatrix()`: Matrix view rendering
- `_updateColumnSize()`: Grid system integration

## 🚀 Performance Features

### Optimizations
- **Debounced Rendering**: Prevents excessive re-renders
- **Change Detection**: Only updates when relevant data changes
- **Efficient DOM**: Minimal DOM manipulation
- **CSS-Only Animations**: Hardware-accelerated styling

### Memory Management
- **Proper Cleanup**: Event listeners and timers are cleaned up
- **Efficient Data Structures**: Optimized data parsing and storage
- **Lazy Loading**: Components render only when needed

## 🐛 Error Handling

### User-Friendly Messages
- Connection issues: "Connecting to Home Assistant..."
- Configuration errors: "Student data not found. Check entity configuration."
- No data: "No schedule data available for this week."
- Render errors: "Error rendering schedule: {error message}"

### Debugging
- Comprehensive console logging with prefixed messages
- Debug information for data parsing
- Performance timing information
- Error stack traces in development

## 🔄 Migration from v2.x

### Breaking Changes
- Complete rewrite - no backwards compatibility
- New CSS class names and structure
- Updated configuration options
- Modern ES6+ syntax requirements

### Migration Steps
1. Replace the old card file with the new implementation
2. Update any custom CSS targeting old class names
3. Test all view modes and configurations
4. Update documentation references

## 📈 Future Enhancements

### Planned Features
- **Break Visualization**: Show break periods with appropriate sizing
- **Theme System**: Multiple color schemes and customization
- **Animation System**: Smooth transitions between states
- **Accessibility**: Full ARIA support and keyboard navigation
- **Internationalization**: Multi-language support
- **Advanced Filtering**: Filter by subject, teacher, or room

### Extensibility
The new architecture makes it easy to add:
- New view modes
- Custom renderers
- Additional data sources
- Plugin system for extensions

## 🏁 Conclusion

The v3.0.0 rewrite provides a solid foundation for future development while delivering immediate improvements in:
- **Code Quality**: Modern, maintainable codebase
- **User Experience**: Responsive, intuitive interface
- **Performance**: Efficient rendering and data handling
- **Reliability**: Comprehensive error handling and debugging

This implementation fully meets the requirements for Home Assistant grid integration, responsive text sizing, and proper lesson placement while providing a clean, modern codebase for future enhancements.
