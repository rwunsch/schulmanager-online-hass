/**
 * Schulmanager Schedule Card for Home Assistant
 * 
 * A modern, responsive schedule card with multiple view modes.
 * Fixed version with proper column flow and real sensor data support.
 * 
 * Features:
 * - Multiple view modes: weekly_matrix, weekly_list, daily_list, compact
 * - Responsive design with Home Assistant grid system integration
 * - Dynamic text sizing based on available space
 * - Proper break/pause visualization
 * - Full subject names with abbreviation fallback
 * - Teacher names with abbreviation fallback
 * - Substitution and change highlighting
 * - ResizeObserver for dynamic column sizing
 * - Real sensor data integration with fallback to sample data
 * 
 * @version 3.1.0
 * @author Fixed for column flow and sensor data
 */

class SchulmanagerScheduleCard extends HTMLElement {
  constructor() {
    super();
    this._config = null;
    this._hass = null;
    this._studentData = null;
    this._scheduleData = [];
    this._isInitialized = false;
    this._renderTimeout = null;
    this._resizeObserver = null;
    this._resizeTimeout = null;
    
    // Set up ResizeObserver to detect column changes
    this._setupResizeObserver();
    
    console.log('🎯 Schulmanager Schedule Card v3.1.0 - Constructor initialized');
  }

  /**
   * Setup ResizeObserver to detect Home Assistant column changes
   */
  _setupResizeObserver() {
    if (typeof ResizeObserver !== 'undefined') {
      this._resizeObserver = new ResizeObserver((entries) => {
        // Debounce resize events
        if (this._resizeTimeout) {
          clearTimeout(this._resizeTimeout);
        }
        this._resizeTimeout = setTimeout(() => {
          this._updateColumnSize();
        }, 100);
      });
    }
  }

  /**
   * Start observing for resize changes
   */
  _startResizeObserving() {
    if (this._resizeObserver && this.parentElement) {
      // Observe parent elements for size changes
      let element = this.parentElement;
      let levels = 0;
      while (element && levels < 5) {
        this._resizeObserver.observe(element);
        element = element.parentElement;
        levels++;
      }
    }
  }

  /**
   * Stop observing for resize changes
   */
  _stopResizeObserving() {
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
    }
  }

  /**
   * Set the card configuration
   * @param {Object} config - Card configuration
   */
  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }

    this._config = {
      // Default configuration
      view: 'weekly_matrix',
      title: 'Schedule',
      show_header: true,
      show_breaks: true,
      highlight_current: true,
      highlight_changes: true,
      color_scheme: 'default',
      time_format: '24h',
      language: 'de',
      max_days: 7,
      column_size: null, // Will be auto-detected from HA grid
      // Override with user config
      ...config
    };

    console.log('🔧 Config set:', this._config);
    this._isInitialized = true;
    this._scheduleRender();
  }

  /**
   * Set Home Assistant object and trigger update
   * @param {Object} hass - Home Assistant object
   */
  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Update column size first
    this._updateColumnSize();
    
    // Check if relevant entities changed
    if (this._hasRelevantChanges(oldHass, hass)) {
      this._updateData();
      this._scheduleRender();
    }
  }

  /**
   * Check if there are relevant changes in Home Assistant state
   * @param {Object} oldHass - Previous Home Assistant object
   * @param {Object} newHass - New Home Assistant object
   * @returns {boolean} True if relevant changes detected
   */
  _hasRelevantChanges(oldHass, newHass) {
    if (!oldHass || !this._config) return true;
    
    const entityId = this._config.entity;
    const oldEntity = oldHass.states[entityId];
    const newEntity = newHass.states[entityId];
    
    if (!oldEntity && !newEntity) return false;
    if (!oldEntity || !newEntity) return true;
    
    // Check if state or attributes changed
    return oldEntity.state !== newEntity.state || 
           JSON.stringify(oldEntity.attributes) !== JSON.stringify(newEntity.attributes);
  }

  /**
   * Update column size from Home Assistant grid system with enhanced detection
   */
  _updateColumnSize() {
    try {
      let columnSize = null;
      
      // Method 1: Try to get column-size from parent elements using CSS properties
      let element = this.parentElement;
      while (element && !columnSize) {
        if (element.style && element.style.getPropertyValue('--column-size')) {
          columnSize = parseInt(element.style.getPropertyValue('--column-size'));
          break;
        }
        
        // Method 2: Style attribute parsing
        const styleAttr = element.getAttribute('style');
        if (styleAttr) {
          const match = styleAttr.match(/--column-size:\s*(\d+)/);
          if (match) {
            columnSize = parseInt(match[1]);
            break;
          }
        }
        
        // Method 3: Check computed styles
        try {
          const computedStyle = window.getComputedStyle(element);
          const computedColumnSize = computedStyle.getPropertyValue('--column-size');
          if (computedColumnSize && computedColumnSize !== '') {
            columnSize = parseInt(computedColumnSize);
            break;
          }
        } catch (e) {
          // Ignore errors in computed style access
        }
        
        element = element.parentElement;
      }
      
      // Method 4: Try using closest() to find element with column-size
      if (!columnSize) {
        try {
          const parentElement = this.closest('[style*="--column-size"]');
          if (parentElement) {
            const style = parentElement.getAttribute('style');
            const columnMatch = style.match(/--column-size:\s*(\d+)/);
            if (columnMatch) {
              columnSize = parseInt(columnMatch[1]);
            }
          }
        } catch (e) {
          // Ignore errors
        }
      }
      
      // Fallback: use config or default
      if (!columnSize) {
        columnSize = this._config.column_size || this._getDefaultColumnSize();
      }
      
      // Apply column size and trigger re-render if changed
      const currentColumnSize = parseInt(this.style.getPropertyValue('--column-size'));
      if (currentColumnSize !== columnSize) {
        this.style.setProperty('--column-size', columnSize);
        console.log(`🔧 Column size updated: ${currentColumnSize} → ${columnSize}`);
        
        // Schedule re-render to update responsive elements
        this._scheduleRender();
      }
      
    } catch (error) {
      console.error('🔧 Error updating column size:', error);
    }
  }

  /**
   * Get default column size based on view mode
   * @returns {number} Default column size
   */
  _getDefaultColumnSize() {
    switch (this._config.view) {
      case 'weekly_matrix': return 12;
      case 'weekly_list': return 8;
      case 'daily_list': return 6;
      case 'compact': return 4;
      default: return 8;
    }
  }

  /**
   * Update internal data from Home Assistant
   */
  _updateData() {
    if (!this._hass || !this._config) return;
    
    try {
      // Get student name from entity
      const student = this._extractStudentFromEntity();
      if (!student) {
        console.warn('🔧 No student found');
        this._studentData = null;
        this._scheduleData = this._generateSampleData();
        return;
      }
      
      // Get all student sensors
      this._studentData = this._getStudentSensors(student);
      
      // Check if we have the required sensors
      if (!this._studentData || Object.keys(this._studentData).length === 0) {
        console.warn('🔧 No student sensors found, using sample data');
        this._scheduleData = this._generateSampleData();
        return;
      }
      
      // Extract schedule data from sensors
      this._scheduleData = this._extractScheduleData();
      
      console.log(`🔧 Updated data for student: ${student}`, {
        sensors: Object.keys(this._studentData),
        lessons: this._scheduleData?.length || 0
      });
      
    } catch (error) {
      console.error('🔧 Error updating data:', error);
      this._studentData = null;
      this._scheduleData = this._generateSampleData();
    }
  }

  /**
   * Extract student name from configured entity
   * @returns {string|null} Student name
   */
  _extractStudentFromEntity() {
    const entityId = this._config.entity;
    
    // Try different patterns to extract student name
    const patterns = [
      /sensor\.schulmanager_(.+)_schedule/,
      /sensor\.schulmanager_(.+)_this_week/,
      /sensor\.schulmanager_(.+)/
    ];
    
    for (const pattern of patterns) {
      const match = entityId.match(pattern);
      if (match) {
        return match[1];
      }
    }
    
    console.warn(`🔧 Could not extract student from entity: ${entityId}`);
    return null;
  }

  /**
   * Get all sensors for a student
   * @param {string} student - Student name
   * @returns {Object} Student sensors
   */
  _getStudentSensors(student) {
    const sensors = {};
    const sensorTypes = ['this_week', 'schedule', 'lessons', 'current_lesson', 'next_lesson', 'lessons_today'];
    
    for (const type of sensorTypes) {
      const entityId = `sensor.schulmanager_${student}_${type}`;
      const entity = this._hass.states[entityId];
      
      if (entity) {
        sensors[type] = entity;
        console.log(`🔧 Found sensor: ${entityId}`);
      }
    }
    
    console.log(`🔧 Found ${Object.keys(sensors).length} sensors for student: ${student}`);
    return sensors;
  }

  /**
   * Extract schedule data from sensors with enhanced data parsing
   * @returns {Array} Schedule data array
   */
  _extractScheduleData() {
    if (!this._studentData) {
      console.warn('🔧 No student data available');
      return this._generateSampleData();
    }

    // Try different sensor sources in order of preference
    const possibleSensors = [
      this._studentData.this_week,
      this._studentData.schedule,
      this._studentData.lessons
    ].filter(sensor => sensor && sensor.attributes);

    for (const sensor of possibleSensors) {
      // Try different attribute names that might contain lesson data
      const possibleAttributes = ['lessons', 'schedule', 'data', 'items'];
      
      for (const attrName of possibleAttributes) {
        const lessons = sensor.attributes[attrName];
        
        if (Array.isArray(lessons) && lessons.length > 0) {
          console.log(`🔧 Found ${lessons.length} lessons in sensor attribute '${attrName}'`);
          console.log('🔧 Sample lesson data:', lessons[0]);
          
          const parsedLessons = lessons.map((lesson, index) => {
            const parsedLesson = {
              // Basic info
              date: lesson.date,
              day: this._convertDateToDay(lesson.date),
              hour: this._parseHour(lesson),
              
              // Subject info
              subject: lesson.subject || lesson.name || lesson.title || 'Unknown',
              subject_abbreviation: lesson.subject_abbreviation || lesson.abbreviation || lesson.short || this._createAbbreviation(lesson.subject || lesson.name),
              
              // Teacher info
              teacher: this._getTeacherName(lesson),
              teacher_abbreviation: lesson.teacher_abbreviation || lesson.teacher_short || lesson.teacher || '',
              teacher_firstname: lesson.teacher_firstname || lesson.teacher_first || '',
              teacher_lastname: lesson.teacher_lastname || lesson.teacher_last || '',
              
              // Location and timing
              room: lesson.room || lesson.classroom || lesson.location || '',
              time: lesson.time || lesson.period || '',
              start_time: lesson.start_time || lesson.start || '',
              end_time: lesson.end_time || lesson.end || '',
              
              // Status
              type: lesson.type || lesson.kind || 'regularLesson',
              is_substitution: lesson.is_substitution || lesson.substitution || lesson.is_replacement || false,
              comment: lesson.comment || lesson.note || lesson.remark || '',
              
              // Internal
              class_hour: lesson.class_hour || lesson.hour || lesson.period_number || null
            };
            
            // Debug first few lessons
            if (index < 3) {
              console.log(`🔧 Parsed lesson ${index + 1}:`, parsedLesson);
            }
            
            return parsedLesson;
          }).filter(lesson => lesson.day && lesson.subject !== 'Unknown'); // Filter out invalid lessons
          
          if (parsedLessons.length > 0) {
            console.log(`🔧 Successfully parsed ${parsedLessons.length} real lessons`);
            return parsedLessons;
          }
        }
      }
    }
    
    console.warn('🔧 No valid lesson data found in sensors, using sample data');
    console.log('🔧 Available sensors:', Object.keys(this._studentData));
    
    // Log sensor contents for debugging
    Object.entries(this._studentData).forEach(([key, sensor]) => {
      if (sensor && sensor.attributes) {
        console.log(`🔧 Sensor ${key} attributes:`, Object.keys(sensor.attributes));
        Object.entries(sensor.attributes).forEach(([attrKey, attrValue]) => {
          if (Array.isArray(attrValue)) {
            console.log(`🔧 ${key}.${attrKey}: array with ${attrValue.length} items`);
            if (attrValue.length > 0) {
              console.log(`🔧 ${key}.${attrKey}[0]:`, attrValue[0]);
            }
          }
        });
      }
    });
    
    return this._generateSampleData();
  }

  /**
   * Extract teacher name from lesson data
   * @param {Object} lesson - Lesson data
   * @returns {string} Teacher name
   */
  _getTeacherName(lesson) {
    if (lesson.teacher_firstname && lesson.teacher_lastname) {
      return `${lesson.teacher_firstname} ${lesson.teacher_lastname}`;
    }
    
    return lesson.teacher || lesson.teacher_name || lesson.instructor || '';
  }

  /**
   * Generate sample data for testing when no real data is available
   * @returns {Array} Sample lesson data
   */
  _generateSampleData() {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const subjects = [
      { name: 'Mathematics', abbr: 'Math' },
      { name: 'English', abbr: 'Eng' },
      { name: 'Science', abbr: 'Sci' },
      { name: 'History', abbr: 'Hist' },
      { name: 'Physical Education', abbr: 'PE' },
      { name: 'German', abbr: 'Ger' },
      { name: 'Biology', abbr: 'Bio' },
      { name: 'Chemistry', abbr: 'Chem' }
    ];
    const teachers = [
      { first: 'John', last: 'Smith', abbr: 'JS' },
      { first: 'Mary', last: 'Johnson', abbr: 'MJ' },
      { first: 'David', last: 'Brown', abbr: 'DB' },
      { first: 'Sarah', last: 'Wilson', abbr: 'SW' },
      { first: 'Michael', last: 'Davis', abbr: 'MD' }
    ];
    
    const sampleLessons = [];
    const today = new Date();
    const monday = new Date(today.setDate(today.getDate() - today.getDay() + 1));
    
    days.forEach((day, dayIndex) => {
      const lessonDate = new Date(monday);
      lessonDate.setDate(monday.getDate() + dayIndex);
      
      for (let hour = 1; hour <= 6; hour++) {
        if (Math.random() > 0.2) { // 80% chance of having a lesson
          const subject = subjects[Math.floor(Math.random() * subjects.length)];
          const teacher = teachers[Math.floor(Math.random() * teachers.length)];
          
          sampleLessons.push({
            date: lessonDate.toISOString().split('T')[0],
            day: day,
            hour: hour,
            subject: subject.name,
            subject_abbreviation: subject.abbr,
            teacher: `${teacher.first} ${teacher.last}`,
            teacher_abbreviation: teacher.abbr,
            teacher_firstname: teacher.first,
            teacher_lastname: teacher.last,
            room: `Room ${Math.floor(Math.random() * 30) + 101}`,
            time: `${7 + hour}:00-${8 + hour}:00`,
            start_time: `${7 + hour}:00`,
            end_time: `${8 + hour}:00`,
            type: 'regularLesson',
            is_substitution: Math.random() > 0.9,
            comment: Math.random() > 0.8 ? 'Sample note' : '',
            class_hour: hour
          });
        }
      }
    });
    
    console.log('🔧 Generated sample data with', sampleLessons.length, 'lessons');
    return sampleLessons;
  }

  /**
   * Convert date string to day name
   * @param {string} dateStr - Date string
   * @returns {string|null} Day name
   */
  _convertDateToDay(dateStr) {
    if (!dateStr) return null;
    
    try {
      const date = new Date(dateStr);
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      return days[date.getDay()];
    } catch (error) {
      console.warn(`🔧 Could not convert date: ${dateStr}`);
      return null;
    }
  }

  /**
   * Parse hour from lesson data
   * @param {Object} lesson - Lesson data
   * @returns {number|null} Hour number
   */
  _parseHour(lesson) {
    // Try different hour fields
    const hourFields = ['hour', 'class_hour', 'period', 'period_number'];
    
    for (const field of hourFields) {
      if (lesson[field] && !isNaN(lesson[field])) {
        return parseInt(lesson[field]);
      }
    }
    
    // Try to extract from time string
    if (lesson.time) {
      const match = lesson.time.match(/(\d+)/);
      if (match) {
        return parseInt(match[1]);
      }
    }
    
    return null;
  }

  /**
   * Create abbreviation from subject name
   * @param {string} subject - Subject name
   * @returns {string} Abbreviation
   */
  _createAbbreviation(subject) {
    if (!subject) return '';
    
    // Split by spaces and take first letter of each word
    return subject
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .join('')
      .substring(0, 4); // Max 4 characters
  }

  /**
   * Schedule a render with debouncing
   */
  _scheduleRender() {
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
    }
    
    this._renderTimeout = setTimeout(() => {
      this._render();
    }, 50);
  }

  /**
   * Render the card
   */
  _render() {
    if (!this._isInitialized) return;
    
    try {
      this.innerHTML = `
        <ha-card>
          <div class="card-content">
            ${this._renderContent()}
          </div>
        </ha-card>
        <style>
          ${this._getStyles()}
        </style>
      `;
      
      // Start resize observing after render
      setTimeout(() => {
        this._startResizeObserving();
      }, 100);
      
      console.log('🔧 Card rendered successfully');
      
    } catch (error) {
      console.error('🔧 Error rendering card:', error);
      this.innerHTML = `
        <ha-card>
          <div class="card-content error">
            <div class="error-message">
              <h3>Error rendering schedule card</h3>
              <p>${error.message}</p>
              <small>Check the browser console for more details</small>
            </div>
          </div>
        </ha-card>
        <style>
          .error-message {
            padding: 16px;
            background: var(--error-color, #ff5252);
            color: white;
            border-radius: 4px;
            text-align: center;
          }
        </style>
      `;
    }
  }

  /**
   * Render content based on current state
   */
  _renderContent() {
    if (!this._config) {
      return '<div class="error">Configuration required</div>';
    }
    
    if (!this._hass) {
      return '<div class="loading">Loading Home Assistant...</div>';
    }
    
    if (!this._scheduleData || this._scheduleData.length === 0) {
      return `
        <div class="no-data">
          <h3>No schedule data available</h3>
          <p>Make sure the Schulmanager integration is configured and the entity "${this._config.entity}" exists.</p>
          <small>Using sample data for demonstration</small>
        </div>
      `;
    }
    
    const viewMode = this._config.view || 'weekly_matrix';
    
    switch (viewMode) {
      case 'weekly_matrix':
        return this._renderWeeklyMatrix();
      case 'weekly_list':
        return this._renderWeeklyList();
      case 'daily_list':
        return this._renderDailyList();
      case 'compact':
        return this._renderCompact();
      default:
        return this._renderWeeklyMatrix();
    }
  }

  /**
   * Render weekly matrix view
   * @returns {string} HTML content
   */
  _renderWeeklyMatrix() {
    const lessonsByDay = this._groupLessonsByDayAndHour();
    const timeSlots = this._getTimeSlots();
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    
    let html = `
      <div class="schedule-header">
        <h2>${this._config.title}</h2>
        <div class="week-info">${this._getCurrentWeek()}</div>
      </div>
      <div class="weekly-matrix">
        <div class="time-column">
          <div class="time-header">Time</div>
    `;
    
    timeSlots.forEach(hour => {
      html += `<div class="time-slot" data-hour="${hour}">${hour}.</div>`;
    });
    
    html += '</div>';
    
    days.forEach(day => {
      html += `
        <div class="day-column">
          <div class="day-header">${day}</div>
      `;
      
      timeSlots.forEach(hour => {
        const lesson = lessonsByDay[day] && lessonsByDay[day][hour];
        html += this._renderMatrixCell(lesson, day, hour);
      });
      
      html += '</div>';
    });
    
    html += '</div>';
    return html;
  }

  /**
   * Render a matrix cell
   * @param {Object|null} lesson - Lesson data
   * @param {string} day - Day name
   * @param {number} hour - Hour number
   * @returns {string} HTML content
   */
  _renderMatrixCell(lesson, day, hour) {
    if (!lesson) {
      return `<div class="lesson-cell empty" data-day="${day}" data-hour="${hour}"></div>`;
    }
    
    const classes = ['lesson-cell'];
    if (lesson.is_substitution) classes.push('substitution');
    if (lesson.type === 'break') classes.push('break');
    
    return `
      <div class="${classes.join(' ')}" data-day="${day}" data-hour="${hour}">
        <div class="lesson-subject">
          <span class="full-name">${lesson.subject}</span>
          <span class="abbreviation">${lesson.subject_abbreviation}</span>
        </div>
        <div class="lesson-teacher">
          <span class="full-name">${lesson.teacher}</span>
          <span class="abbreviation">${lesson.teacher_abbreviation}</span>
        </div>
        <div class="lesson-room">${lesson.room}</div>
        ${lesson.comment ? `<div class="lesson-comment">${lesson.comment}</div>` : ''}
      </div>
    `;
  }

  /**
   * Group lessons by day and hour
   * @returns {Object} Lessons grouped by day and hour
   */
  _groupLessonsByDayAndHour() {
    const grouped = {};
    
    this._scheduleData.forEach(lesson => {
      if (!grouped[lesson.day]) {
        grouped[lesson.day] = {};
      }
      if (lesson.hour) {
        grouped[lesson.day][lesson.hour] = lesson;
      }
    });
    
    return grouped;
  }

  /**
   * Get available time slots
   * @returns {Array} Time slots
   */
  _getTimeSlots() {
    const slots = new Set();
    this._scheduleData.forEach(lesson => {
      if (lesson.hour) {
        slots.add(lesson.hour);
      }
    });
    
    const sortedSlots = Array.from(slots).sort((a, b) => a - b);
    
    // If no real data, return default slots
    if (sortedSlots.length === 0) {
      return [1, 2, 3, 4, 5, 6];
    }
    
    return sortedSlots;
  }

  /**
   * Get current week info
   * @returns {string} Week info
   */
  _getCurrentWeek() {
    const now = new Date();
    const monday = new Date(now.setDate(now.getDate() - now.getDay() + 1));
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    
    const formatDate = (date) => {
      return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
    };
    
    return `Week ${formatDate(monday)} - ${formatDate(sunday)}`;
  }

  /**
   * Render weekly list view
   * @returns {string} HTML content
   */
  _renderWeeklyList() {
    const lessonsByDay = this._groupLessonsByDay();
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    
    let html = `
      <div class="schedule-header">
        <h2>${this._config.title}</h2>
        <div class="week-info">${this._getCurrentWeek()}</div>
      </div>
      <div class="weekly-list">
    `;
    
    days.forEach(day => {
      const lessons = lessonsByDay[day] || [];
      html += `
        <div class="day-section">
          <h3 class="day-title">${day}</h3>
          <div class="day-lessons">
      `;
      
      if (lessons.length === 0) {
        html += '<div class="no-lessons">No lessons</div>';
      } else {
        lessons.forEach(lesson => {
          html += this._renderLessonCard(lesson);
        });
      }
      
      html += '</div></div>';
    });
    
    html += '</div>';
    return html;
  }

  /**
   * Group lessons by day
   * @returns {Object} Lessons grouped by day
   */
  _groupLessonsByDay() {
    const grouped = {};
    
    this._scheduleData.forEach(lesson => {
      if (!grouped[lesson.day]) {
        grouped[lesson.day] = [];
      }
      grouped[lesson.day].push(lesson);
    });
    
    // Sort lessons by hour within each day
    Object.keys(grouped).forEach(day => {
      grouped[day].sort((a, b) => (a.hour || 0) - (b.hour || 0));
    });
    
    return grouped;
  }

  /**
   * Render a lesson card
   * @param {Object} lesson - Lesson data
   * @returns {string} HTML content
   */
  _renderLessonCard(lesson) {
    const classes = ['lesson-card'];
    if (lesson.is_substitution) classes.push('substitution');
    
    return `
      <div class="${classes.join(' ')}">
        <div class="lesson-time">${lesson.time || lesson.hour + '.'}</div>
        <div class="lesson-info">
          <div class="lesson-subject">
            <span class="full-name">${lesson.subject}</span>
            <span class="abbreviation">${lesson.subject_abbreviation}</span>
          </div>
          <div class="lesson-details">
            <span class="teacher">
              <span class="full-name">${lesson.teacher}</span>
              <span class="abbreviation">${lesson.teacher_abbreviation}</span>
            </span>
            ${lesson.room ? `<span class="room">${lesson.room}</span>` : ''}
          </div>
          ${lesson.comment ? `<div class="comment">${lesson.comment}</div>` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Render daily list view
   * @returns {string} HTML content
   */
  _renderDailyList() {
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
    const todayLessons = this._scheduleData.filter(lesson => lesson.day === today);
    
    let html = `
      <div class="schedule-header">
        <h2>${this._config.title}</h2>
        <div class="day-info">Today - ${today}</div>
      </div>
      <div class="daily-list">
    `;
    
    if (todayLessons.length === 0) {
      html += '<div class="no-lessons">No lessons today</div>';
    } else {
      todayLessons
        .sort((a, b) => (a.hour || 0) - (b.hour || 0))
        .forEach(lesson => {
          html += this._renderLessonItem(lesson);
        });
    }
    
    html += '</div>';
    return html;
  }

  /**
   * Render a lesson item
   * @param {Object} lesson - Lesson data
   * @returns {string} HTML content
   */
  _renderLessonItem(lesson) {
    const classes = ['lesson-item'];
    if (lesson.is_substitution) classes.push('substitution');
    
    return `
      <div class="${classes.join(' ')}">
        <div class="lesson-time">${lesson.time || lesson.hour + '.'}</div>
        <div class="lesson-content">
          <div class="subject-teacher">
            <span class="subject">
              <span class="full-name">${lesson.subject}</span>
              <span class="abbreviation">${lesson.subject_abbreviation}</span>
            </span>
            <span class="teacher">
              <span class="full-name">${lesson.teacher}</span>
              <span class="abbreviation">${lesson.teacher_abbreviation}</span>
            </span>
          </div>
          ${lesson.room ? `<div class="room">${lesson.room}</div>` : ''}
          ${lesson.comment ? `<div class="comment">${lesson.comment}</div>` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Render compact view
   * @returns {string} HTML content
   */
  _renderCompact() {
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
    const todayLessons = this._scheduleData.filter(lesson => lesson.day === today);
    const nextLessons = todayLessons.slice(0, 3);
    
    let html = `
      <div class="compact-header">
        <h3>${this._config.title}</h3>
      </div>
      <div class="compact-lessons">
    `;
    
    if (nextLessons.length === 0) {
      html += '<div class="no-lessons">No lessons</div>';
    } else {
      nextLessons.forEach(lesson => {
        const classes = ['compact-lesson'];
        if (lesson.is_substitution) classes.push('substitution');
        
        html += `
          <div class="${classes.join(' ')}">
            <span class="time">${lesson.time || lesson.hour + '.'}</span>
            <span class="subject">${lesson.subject_abbreviation || lesson.subject}</span>
            <span class="teacher">${lesson.teacher_abbreviation || lesson.teacher}</span>
            ${lesson.room ? `<span class="room">${lesson.room}</span>` : ''}
          </div>
        `;
      });
    }
    
    html += '</div>';
    return html;
  }

  /**
   * Get styles for the card with responsive column-based sizing
   * @returns {string} CSS styles
   */
  _getStyles() {
    return `
      ha-card {
        --column-size: var(--column-size, 8);
        overflow: hidden;
      }

      .card-content {
        padding: 16px;
      }

      .schedule-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--divider-color);
      }

      .schedule-header h2 {
        margin: 0;
        color: var(--primary-text-color);
        font-size: calc(var(--column-size) * 0.15rem + 1rem);
      }

      .week-info, .day-info {
        font-size: calc(var(--column-size) * 0.1rem + 0.8rem);
        color: var(--secondary-text-color);
      }

      /* Weekly Matrix View */
      .weekly-matrix {
        display: grid;
        grid-template-columns: auto repeat(5, 1fr);
        gap: 2px;
        background: var(--divider-color);
        border-radius: 4px;
        overflow: hidden;
      }

      .time-column, .day-column {
        display: flex;
        flex-direction: column;
      }

      .time-header, .day-header {
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: calc(var(--column-size) * 0.5px + 8px);
        text-align: center;
        font-weight: bold;
        font-size: calc(var(--column-size) * 0.08rem + 0.75rem);
      }

      .time-slot {
        background: var(--card-background-color);
        padding: calc(var(--column-size) * 0.5px + 8px);
        text-align: center;
        font-size: calc(var(--column-size) * 0.06rem + 0.7rem);
        border-bottom: 1px solid var(--divider-color);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: calc(var(--column-size) * 2px + 40px);
      }

      .lesson-cell {
        background: var(--card-background-color);
        padding: calc(var(--column-size) * 0.3px + 4px);
        border-bottom: 1px solid var(--divider-color);
        min-height: calc(var(--column-size) * 2px + 40px);
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
      }

      .lesson-cell.empty {
        background: var(--disabled-text-color);
        opacity: 0.1;
      }

      .lesson-cell.substitution {
        background: var(--warning-color);
        color: var(--text-primary-color);
      }

      .lesson-cell.break {
        background: var(--info-color);
        color: var(--text-primary-color);
      }

      /* Responsive text display based on column size */
      .lesson-subject, .lesson-teacher {
        font-size: calc(var(--column-size) * 0.08rem + 0.65rem);
        line-height: 1.2;
        margin-bottom: 2px;
      }

      .lesson-subject .full-name,
      .lesson-teacher .full-name {
        display: var(--column-size) >= 8 ? inline : none;
      }

      .lesson-subject .abbreviation,
      .lesson-teacher .abbreviation {
        display: var(--column-size) < 8 ? inline : none;
      }

      .lesson-room {
        font-size: calc(var(--column-size) * 0.06rem + 0.6rem);
        color: var(--secondary-text-color);
        display: var(--column-size) >= 6 ? block : none;
      }

      .lesson-comment {
        font-size: calc(var(--column-size) * 0.05rem + 0.55rem);
        color: var(--accent-color);
        font-style: italic;
        display: var(--column-size) >= 10 ? block : none;
      }

      /* Weekly List View */
      .weekly-list {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .day-section {
        background: var(--card-background-color);
        border-radius: 8px;
        padding: 12px;
        border: 1px solid var(--divider-color);
      }

      .day-title {
        margin: 0 0 12px 0;
        color: var(--primary-color);
        font-size: calc(var(--column-size) * 0.1rem + 1rem);
        border-bottom: 1px solid var(--divider-color);
        padding-bottom: 4px;
      }

      .day-lessons {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .lesson-card {
        display: flex;
        gap: 12px;
        padding: 8px;
        background: var(--secondary-background-color);
        border-radius: 4px;
        border-left: 3px solid var(--primary-color);
      }

      .lesson-card.substitution {
        border-left-color: var(--warning-color);
        background: var(--warning-color);
        color: var(--text-primary-color);
      }

      .lesson-time {
        font-weight: bold;
        min-width: 60px;
        font-size: calc(var(--column-size) * 0.08rem + 0.8rem);
      }

      .lesson-info {
        flex: 1;
      }

      .lesson-details {
        display: flex;
        gap: 12px;
        margin-top: 4px;
        font-size: calc(var(--column-size) * 0.07rem + 0.75rem);
        color: var(--secondary-text-color);
      }

      /* Daily List View */
      .daily-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .lesson-item {
        display: flex;
        gap: 16px;
        padding: 12px;
        background: var(--secondary-background-color);
        border-radius: 6px;
        border-left: 4px solid var(--primary-color);
      }

      .lesson-item.substitution {
        border-left-color: var(--warning-color);
        background: var(--warning-color);
        color: var(--text-primary-color);
      }

      .lesson-content {
        flex: 1;
      }

      .subject-teacher {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
      }

      .subject {
        font-weight: bold;
        font-size: calc(var(--column-size) * 0.1rem + 0.9rem);
      }

      .teacher {
        font-size: calc(var(--column-size) * 0.08rem + 0.8rem);
        color: var(--secondary-text-color);
      }

      /* Compact View */
      .compact-header {
        margin-bottom: 12px;
      }

      .compact-header h3 {
        margin: 0;
        font-size: calc(var(--column-size) * 0.15rem + 1rem);
        color: var(--primary-text-color);
      }

      .compact-lessons {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .compact-lesson {
        display: flex;
        gap: 8px;
        padding: 6px 8px;
        background: var(--secondary-background-color);
        border-radius: 4px;
        font-size: calc(var(--column-size) * 0.08rem + 0.75rem);
      }

      .compact-lesson.substitution {
        background: var(--warning-color);
        color: var(--text-primary-color);
      }

      .compact-lesson .time {
        font-weight: bold;
        min-width: 50px;
      }

      .compact-lesson .subject {
        flex: 1;
        font-weight: 500;
      }

      .compact-lesson .teacher,
      .compact-lesson .room {
        color: var(--secondary-text-color);
      }

      /* Error and Loading States */
      .loading, .no-data, .error {
        text-align: center;
        padding: 32px 16px;
        color: var(--secondary-text-color);
      }

      .no-data h3 {
        color: var(--primary-text-color);
        margin-bottom: 8px;
      }

      .no-lessons {
        text-align: center;
        padding: 16px;
        color: var(--secondary-text-color);
        font-style: italic;
      }

      .error {
        color: var(--error-color);
        background: var(--error-color);
        color: white;
        border-radius: 4px;
      }

      .comment {
        font-size: calc(var(--column-size) * 0.06rem + 0.7rem);
        color: var(--accent-color);
        font-style: italic;
        margin-top: 4px;
      }

      /* Responsive breakpoints */
      @container (max-width: 400px) {
        .lesson-subject .full-name,
        .lesson-teacher .full-name,
        .teacher .full-name,
        .subject .full-name {
          display: none;
        }
        
        .lesson-subject .abbreviation,
        .lesson-teacher .abbreviation,
        .teacher .abbreviation,
        .subject .abbreviation {
          display: inline;
        }
        
        .lesson-room,
        .lesson-comment {
          display: none;
        }
      }

      @container (min-width: 600px) {
        .lesson-subject .full-name,
        .lesson-teacher .full-name,
        .teacher .full-name,
        .subject .full-name {
          display: inline;
        }
        
        .lesson-subject .abbreviation,
        .lesson-teacher .abbreviation,
        .teacher .abbreviation,
        .subject .abbreviation {
          display: none;
        }
      }
    `;
  }

  /**
   * Get card size for Home Assistant
   * @returns {number} Card size
   */
  getCardSize() {
    const columnSize = parseInt(this.style.getPropertyValue('--column-size')) || this._getDefaultColumnSize();
    return Math.max(3, Math.min(columnSize, 20));
  }

  /**
   * Cleanup when element is removed
   */
  disconnectedCallback() {
    this._stopResizeObserving();
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
    }
    if (this._resizeTimeout) {
      clearTimeout(this._resizeTimeout);
    }
  }
}

// Register the custom element
customElements.define('schulmanager-schedule-card', SchulmanagerScheduleCard);

// Register with Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'schulmanager-schedule-card',
  name: 'Schulmanager Schedule Card',
  description: 'A responsive schedule card for Schulmanager Online integration'
});

console.log('🎯 Schulmanager Schedule Card v3.1.0 loaded successfully');
