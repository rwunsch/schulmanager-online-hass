# Debug Script Quick Start

## 🚀 Quick Usage

```bash
# Install requirement (one time only)
pip3 install requests

# Run basic test
cd test-scripts
python3 debug_multi_school.py --email your@email.com --password 'YourPassword'

# Run with full API tests
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --full-test

# For multi-school accounts (use the ID from first run)
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345

# Anonymize student names in output files
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --anonymize-names
```

## 📖 Full Documentation

See: **[documentation/Debug_Script_Guide.md](../documentation/Debug_Script_Guide.md)**

## 🔒 Privacy

✅ **All sensitive data is automatically redacted**:
- Passwords: NEVER saved
- Tokens: Redacted (only last 8 chars shown)
- Emails: Masked (`u***@e***.com`)

✅ **Output files are safe to share** (`debug-dumps/*.json`)

## 📁 Output Files

Files saved to: `debug-dumps/`

- `01_get_salt_response.json` - Salt retrieval test
- `02_login_response.json` - Login response (redacted)
- `03_login_parsed_user.json` - **Most important** - user & student data
- `10_schedule_response.json` - Schedule data (if `--full-test`)
- `12_homework_response.json` - Homework data (if `--full-test`)
- `13_exams_response.json` - Exams data (if `--full-test`)
- `14_letters_response.json` - Letters data (if `--full-test`)

## 🐛 When to Use

✅ Use this tool if:
- Integration won't load in Home Assistant
- Multi-school login issues
- Need to verify credentials before setup
- Developer requested diagnostics

❌ Don't need if:
- Integration is working fine
- Just setting up (use HA UI instead)

## 🆘 Getting Help

- **Full Guide**: [Debug_Script_Guide.md](../documentation/Debug_Script_Guide.md)
- **Multi-School Info**: [Multi_School_Complete_Guide.md](../documentation/Multi_School_Complete_Guide.md)
- **Issues**: https://github.com/rwunsch/schulmanager-online-hass/issues

## Example Output

```
================================================================================
  Schulmanager Online Multi-School Debug Tool
================================================================================

Step 1/5: Fetching salt for password hashing...
         ✓ Salt received (512 characters)

Step 2/5: Computing PBKDF2-SHA512 hash (99,999 iterations)...
         ✓ Hash computed (1024 characters)

Step 3/5: Testing login (checking for multiple schools)...
         ✓ Login successful (token: ...BZsGc)

Step 4/5: Analyzing user and student data...
         ✓ Found 1 student(s)
         ✓ User object has institutionId: 13309
         ✓ Student 4333047 has NO institutionId (expected)

================================================================================
  DIAGNOSTIC SUMMARY
================================================================================

✓ Login Status: SUCCESS
✓ Institution ID: 13309
✓ Single School Account
✓ Students Found: 1

✓ Debug files saved to: test-scripts/debug-dumps/
  These files are safe to share - all sensitive data is redacted.
================================================================================
```

## Command Reference

| Flag | Description |
|------|-------------|
| `--email` | Your Schulmanager email (required) |
| `--password` | Your password in single quotes (required) |
| `--institution-id` | School ID (for multi-school accounts) |
| `--full-test` | Test all API endpoints |
| `--anonymize-names` | Replace student names with IDs |
| `--weeks` | Number of weeks for schedule/exams (default: 2) |
| `--help` | Show all options |
