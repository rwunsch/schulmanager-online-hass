# Debug Output Files

This folder contains diagnostic output from the Schulmanager Online debug script.

## 🔒 Privacy & Security

✅ **These files are SAFE to share** with developers!

All sensitive data has been automatically redacted:
- Passwords: **NEVER** saved
- JWT tokens: Redacted (only last 8 chars visible)
- Email addresses: Masked (`u***@e***.com`)
- Hashes: Removed

## 📁 File Descriptions

| File | Description | When Created |
|------|-------------|--------------|
| `01_get_salt_response.json` | Salt retrieval from Schulmanager API | Always |
| `02_login_response.json` | Login API response (token redacted) | Always |
| `03_login_parsed_user.json` | **Most important** - User info, students, multi-school status | Always |
| `10_schedule_response.json` | Schedule/lessons data | With `--full-test` |
| `11_class_hours_response.json` | School time configuration | With `--full-test` |
| `12_homework_response.json` | Homework assignments | With `--full-test` |
| `13_exams_response.json` | Exams and tests | With `--full-test` |
| `14_letters_response.json` | Letters/messages from school | With `--full-test` |

## 📤 Sharing with Developers

### When filing a bug report:

1. **ZIP this entire folder**
2. **Attach to GitHub issue**: https://github.com/rwunsch/schulmanager-online-hass/issues
3. **Include**: Console output from the script
4. **Don't include**: Your actual password (never needed)

### What developers will see:

✅ Technical information:
- API response structures
- Institution ID (school identifier)
- Student IDs (anonymized if you used `--anonymize-names`)
- Error messages and status codes

❌ They will NOT see:
- Your password
- Full JWT tokens
- Your complete email address
- Unhashed credentials

## 🗑️ Cleanup

You can safely delete these files when:
- Issue is resolved
- You no longer need diagnostics
- You want to run a fresh test

**To delete all**: 
```bash
rm -rf debug-dumps/*
```

Or simply delete the `debug-dumps` folder from your file explorer.

## 🔍 Understanding the Output

### Key Fields to Note:

**In `03_login_parsed_user.json`**:
- `has_multi_school`: `true` = You have access to multiple schools
- `selected_institution_id`: Your school's unique ID (e.g., `13309`)
- `student_count`: Number of students found
- `user.institutionId`: Institution ID from user object
- `students[].institutionId`: ⚠️ Should NOT exist (expected to be missing)

**Example**:
```json
{
  "has_multi_school": false,
  "selected_institution_id": 13309,
  "user": {
    "id": 2385948,
    "email": "u***@g***.de",
    "institutionId": 13309,
    "associatedParents": [
      {
        "student": {
          "id": 4333047,
          "firstname": "Marc Cedric",
          "lastname": "Wunsch",
          "classId": 444612
        }
      }
    ]
  },
  "student_count": 1
}
```

## 📖 More Information

- **User Guide**: [../documentation/Debug_Script_Guide.md](../documentation/Debug_Script_Guide.md)
- **Multi-School Info**: [../documentation/Multi_School_Complete_Guide.md](../documentation/Multi_School_Complete_Guide.md)
- **Quick Start**: [../README.md](../README.md)

---

**Last Updated**: 2025-01-28  
**Integration**: Schulmanager Online for Home Assistant  
**Repository**: https://github.com/rwunsch/schulmanager-online-hass

