# Debug Script User Guide

## What is this tool?

The **Schulmanager Online Debug Script** is a diagnostic tool that helps identify and fix multi-school login issues with the Home Assistant integration. It's designed to be run **outside of Home Assistant** on your computer.

### When to use this tool:

✅ **Use this if:**
- Your Schulmanager integration isn't loading in Home Assistant
- You have children at multiple schools and the integration isn't working
- You want to verify your credentials before setting up the integration
- A developer asked you to run diagnostics

❌ **Don't need this if:**
- Your integration is working fine
- You just want to set up the integration (use the HA UI instead)

---

## 🔒 Privacy & Security

**This script is SAFE to use and share results from:**

✅ **What IS redacted (hidden)**:
- Your password (NEVER saved to files)
- JWT authentication tokens (only last 8 characters shown)
- Email addresses (partially masked: `u***@e***.com`)
- Hash values

✅ **What CAN be shared**:
- The output files in `debug-dumps/` folder
- These files are automatically cleaned of sensitive data
- Safe to attach to GitHub issues or send to developers

❌ **What you should NOT share**:
- Your actual password (never needed by developers)
- The console output if you used `--anonymize-names` flag
  (it may show real names on screen, but files will be anonymized)

---

## Installation & Requirements

### Step 1: Check if you have Python installed

**On Windows**:
1. Press `Win + R`, type `cmd`, press Enter
2. Type: `python --version` or `python3 --version`
3. You should see: `Python 3.8` or newer

**On Mac/Linux**:
1. Open Terminal
2. Type: `python3 --version`
3. You should see: `Python 3.8` or newer

**If Python is not installed**:
- Windows: Download from [python.org](https://www.python.org/downloads/)
- Mac: Run `brew install python3` (if you have Homebrew)
- Linux: Run `sudo apt install python3` (Ubuntu/Debian)

### Step 2: Install required library

Open Terminal/Command Prompt and run:

```bash
pip3 install requests
```

or on Windows:

```bash
pip install requests
```

**If this fails**, try:
```bash
python3 -m pip install --user requests
```

---

## How to Use the Script

### Basic Usage (Most Common)

1. **Open Terminal/Command Prompt**

2. **Navigate to the script folder**:
   ```bash
   cd /path/to/schulmanager-online-hass/test-scripts
   ```
   
   On Windows, it might look like:
   ```
   cd C:\Users\YourName\schulmanager-online-hass\test-scripts
   ```

3. **Run the script** with your Schulmanager credentials:
   ```bash
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword123'
   ```
   
   **Important**: Put your password in **single quotes** `'like this'` especially if it contains special characters!

### Example Output (Single School):

```
================================================================================
  Schulmanager Online Multi-School Debug Tool
================================================================================

This tool will:
  1. Test your login credentials
  2. Check if you have access to multiple schools
  3. Analyze student data structure
  4. Optionally test API endpoints

All sensitive data (passwords, tokens) will be automatically redacted.
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

Step 5/5: Skipping API endpoint tests (use --full-test to enable)

================================================================================
  DIAGNOSTIC SUMMARY
================================================================================

✓ Login Status: SUCCESS
✓ User ID: 2385948
✓ Institution ID: 13309

✓ Single School Account
   Your account accesses one school only.

✓ Students Found: 1
   1. Marc Cedric Wunsch (ID: 4333047)
      ✓ Student has NO institutionId field (expected)

✓ Debug files saved to: test-scripts/debug-dumps/
  These files are safe to share - all sensitive data is redacted.

================================================================================
```

---

## Advanced Usage

### Multi-School Account

If the script detects multiple schools:

```bash
# First run (to see available schools)
python3 debug_multi_school.py --email your@email.com --password 'YourPassword'

# Output will show:
#   ⚠️  MULTI-SCHOOL ACCOUNT DETECTED!
#   Found 2 schools:
#      - ID: 12345  Name: Elementary School A
#      - ID: 67890  Name: High School B

# Second run (select specific school)
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345
```

### Full API Test

To test all API endpoints (schedule, homework, exams, etc.):

```bash
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --full-test
```

This will:
- Test schedule retrieval
- Test homework retrieval
- Test exams retrieval
- Test letters/messages
- Save all responses to `debug-dumps/` folder

### Anonymize Student Names

If you want to keep student names private when sharing debug files:

```bash
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --anonymize-names
```

Student names will be replaced with: `[STUDENT_123]`, `[STUDENT_456]`, etc.

---

## Understanding the Output

### Console Output

**✓ Green checkmarks** = Everything is working correctly
**⚠️  Yellow warnings** = Something unexpected (but might be OK)
**✗ Red errors** = Something is wrong

### Key Information to Note:

1. **Institution ID**: e.g., `13309`
   - This is YOUR school's unique identifier
   - You'll need this if filing a bug report

2. **User ID**: e.g., `2385948`
   - Your account's unique identifier

3. **Student IDs**: e.g., `4333047`
   - Each child's unique identifier

4. **Multi-School Status**:
   - **Single School**: Most common, means you access one school
   - **Multi-School**: You have access to multiple schools (rare)

### Output Files

Files are saved to: `test-scripts/debug-dumps/`

| File | What It Contains |
|------|------------------|
| `01_get_salt_response.json` | Salt used for password hashing |
| `02_login_response.json` | Login API response (token redacted) |
| `03_login_parsed_user.json` | Your user data and students (safe to share) |
| `10_schedule_response.json` | Schedule data (if --full-test used) |
| `12_homework_response.json` | Homework data (if --full-test used) |
| `13_exams_response.json` | Exams data (if --full-test used) |
| `14_letters_response.json` | Letters/messages (if --full-test used) |

**All files are automatically redacted** - passwords and tokens are removed!

---

## Troubleshooting

### Error: "No module named 'requests'"

**Solution**: Install the requests library:
```bash
pip3 install requests
```

### Error: "Login failed: 401" or "Unauthorized"

**Possible causes**:
1. Wrong email or password
2. Copy-paste error (trailing spaces)
3. Password contains special characters not escaped

**Solution**: 
- Double-check your credentials
- Try wrapping password in single quotes: `'Password123!'`
- If password has a single quote, escape it: `'Pass'\''word'`

### Error: "Multiple schools present, please re-run with --institution-id"

This is **EXPECTED** if you have access to multiple schools!

**Solution**:
1. Note the school IDs shown in the output
2. Re-run with the ID of the school you want to test:
   ```bash
   python3 debug_multi_school.py --email ... --password ... --institution-id 12345
   ```

### Script hangs or takes a long time

**Solution**:
- Check your internet connection
- Schulmanager servers might be slow or down
- Press `Ctrl+C` to cancel and try again later

---

## Sharing Results with Developers

### What to Share:

1. **Console output** (copy the entire text from your terminal)
2. **All files** from `debug-dumps/` folder
3. **Version info**:
   ```bash
   python3 --version
   cat custom_components/schulmanager_online/manifest.json | grep version
   ```

### How to Share:

**Option 1: GitHub Issue**
1. Go to: https://github.com/rwunsch/schulmanager-online-hass/issues
2. Click "New Issue"
3. Attach the `debug-dumps/` folder (drag & drop ZIP file)
4. Paste console output in issue description

**Option 2: Discord/Forum**
- ZIP the `debug-dumps/` folder
- Upload the ZIP file
- Paste console output as code block (using triple backticks)

### What NOT to Share:

❌ Your actual password (developers NEVER need this)
❌ Full JWT tokens (if you accidentally captured them elsewhere)

---

## What This Tool Checks

### 1. Authentication Flow
- ✅ Can retrieve salt from Schulmanager API
- ✅ Can compute correct PBKDF2-SHA512 hash (99,999 iterations)
- ✅ Can successfully login with credentials

### 2. Multi-School Detection
- ✅ Detects if you have access to multiple schools
- ✅ Shows available schools and their IDs
- ✅ Tests login with specific school ID

### 3. Data Structure Analysis
- ✅ Checks where `institutionId` appears (user vs student)
- ✅ Verifies student data structure
- ✅ Confirms expected vs unexpected fields

### 4. API Endpoint Testing (with --full-test)
- ✅ Schedule retrieval
- ✅ Homework retrieval
- ✅ Exams retrieval
- ✅ Letters/messages
- ✅ Class hours configuration

---

## FAQ

### Q: Will this script make changes to my Schulmanager account?
**A**: No! This script only READS data. It never writes or modifies anything.

### Q: Can I run this on my Home Assistant server?
**A**: You can, but it's designed to run on your regular computer. If running on HA server, you might need to install Python packages differently.

### Q: How long does the script take to run?
**A**: Usually 5-15 seconds for basic test, 30-60 seconds with `--full-test`.

### Q: Do I need to run this if the integration is working?
**A**: No! This is only for diagnostics when something is broken.

### Q: What if I have multiple children at different schools?
**A**: The script will detect this! Run it once for each school using different `--institution-id` values.

### Q: Is this the same as the integration?
**A**: No! This is a standalone diagnostic tool. The actual integration runs inside Home Assistant.

---

## Technical Details (For Advanced Users)

### Hash Algorithm
- **Algorithm**: PBKDF2-HMAC-SHA512
- **Iterations**: 99,999 (critical - must be exact!)
- **Key length**: 512 bytes
- **Output format**: Hexadecimal (1024 characters)

### API Endpoints
- **Salt**: `POST https://login.schulmanager-online.de/api/get-salt`
- **Login**: `POST https://login.schulmanager-online.de/api/login`
- **Data**: `POST https://login.schulmanager-online.de/api/calls`

### Multi-School Flow
1. Initial login with `institutionId: null`
2. If `multipleAccounts` in response → show schools
3. User selects school by ID
4. Re-login with `institutionId: <selected_id>`
5. Receive JWT token scoped to that institution

---

## Getting Help

### Something not working?

1. **Check this guide** - most issues are covered above
2. **Run with --help** for command-line options:
   ```bash
   python3 debug_multi_school.py --help
   ```
3. **Check integration logs** in Home Assistant:
   - Settings → System → Logs
   - Search for "schulmanager"
4. **File a bug report**:
   - https://github.com/rwunsch/schulmanager-online-hass/issues
   - Include debug files and console output

### Need more help?

- **GitHub Discussions**: https://github.com/rwunsch/schulmanager-online-hass/discussions
- **Email**: wunsch@adobe.com

---

## Change Log

**Version 2.0** (Current)
- ✅ Automatic data redaction
- ✅ Multi-school detection and guidance
- ✅ User-friendly output with checkmarks
- ✅ `--full-test` and `--anonymize-names` options
- ✅ Detailed error messages and troubleshooting

**Version 1.0**
- Basic login testing
- Raw JSON output

---

**Last Updated**: 2025-01-28
**Script Version**: See `debug_multi_school.py` header
**Integration Version**: See `manifest.json`

