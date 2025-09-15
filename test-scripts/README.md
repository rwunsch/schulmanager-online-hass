# Test Scripts - Schulmanager Online

This directory contains test scripts and standalone tools for the Schulmanager Online integration.

## 📋 Available Scripts

### Schedule Table Generator
**File**: `schedule_table_generator.py`

A standalone console tool that creates a two-week schedule table with lesson numbers on the Y-axis and workdays on the X-axis.

**Usage**:
```bash
pip install -r requirements.txt
python3 schedule_table_generator.py
```

**Features**:
- Two-week schedule view
- Console table format
- Sanitized lesson, room, and teacher data
- Credential management
- No Home Assistant dependencies

### Other Test Scripts
- `test_api_complete.py` - Comprehensive API testing
- `test_schedule_api.py` - Schedule API testing
- `test_homework_api.py` - Homework API testing
- `test_exams_api.py` - Exams API testing
- `test_letters_api.py` - Letters API testing

## 🔧 Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy credentials template:
```bash
cp .credentials.template .credentials
```

3. Edit `.credentials` with your Schulmanager credentials:
```
your-email@example.com
your-password
```

## 🔐 Security

- Never commit `.credentials` file to version control
- The `.credentials` file contains plain text passwords
- Consider using environment variables for production use

## 📚 Documentation

See `../documentation/Schedule_Table_Generator.md` for detailed documentation of the schedule table generator.
