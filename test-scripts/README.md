# Test Scripts & Debugging Tools

This directory contains various tools for testing and debugging the Schulmanager Online integration.

## 📋 Overview of Tools

| Tool | Purpose | For | When to Use |
|------|---------|-----|-------------|
| `debug_multi_school.py` | End-user diagnostic tool | **Users** | When integration won't install or multi-school issues occur |
| `extract_schulmanager_logs.py` | Extracts integration logs from HA logs | **Users** | To filter only relevant logs from Home Assistant |
| `test_multi_school_curl.sh` | Raw API testing with CURL | **Developers** | To compare API behavior with implementation |

---

## 🔧 For Users

### 1. Debug Multi-School Issues

**Tool:** `debug_multi_school.py`

**When to use:**
- Integration shows "Benutzer oder Passwort falsch" error
- You have children at multiple schools
- School selection dropdown doesn't appear
- Any authentication problems

**Usage:**
```bash
# Basic test
python3 debug_multi_school.py --email your@email.com --password 'YourPassword'

# For multi-school accounts (after first run tells you the IDs)
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345

# Full API testing
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --full-test

# Anonymize student names in output
python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --anonymize-names
```

**Output:**
- Console: Human-readable summary with next steps
- Files: `debug-dumps/*.json` (automatically redacted, safe to share)

**Privacy:**
- ✅ Passwords are NEVER saved
- ✅ Tokens are redacted (only last 8 chars shown)
- ✅ Emails are masked (e.g., `u***@e***.com`)
- ✅ Student names can be anonymized

### 2. Extract Integration Logs

**Tool:** `extract_schulmanager_logs.py`

**When to use:**
- You need to share Home Assistant logs
- The full log file is too large
- You want only Schulmanager-related log lines

**Usage:**

**From downloaded log file:**
```bash
# Download logs from: Settings → System → Logs → Download button
python3 extract_schulmanager_logs.py /path/to/home-assistant.log

# With custom output file
python3 extract_schulmanager_logs.py home-assistant.log --output my_logs.txt
```

**From Docker:**
```bash
# Extracts directly from Docker logs
python3 extract_schulmanager_logs.py --docker

# For custom container name
python3 extract_schulmanager_logs.py --docker --container my_homeassistant
```

**Output:**
- File: `schulmanager_logs.txt` (only lines containing "schulmanager")
- Much smaller and easier to share than full logs

**What it filters:**
- Lines containing "schulmanager"
- Lines containing "custom_components.schulmanager_online"

---

## 👨‍💻 For Developers

### 3. CURL API Testing

**Tool:** `test_multi_school_curl.sh`

**When to use:**
- Debugging discrepancies between API behavior and our implementation
- Testing exact HTTP requests/responses
- Verifying salt generation with/without institutionId
- Isolating Python-specific issues (encoding, JSON parsing)

**Usage:**
```bash
# Test without institution ID (detects multi-school)
./test_multi_school_curl.sh "email@example.com" "password"

# Test with specific institution ID
./test_multi_school_curl.sh "email@example.com" "password" 13309
```

**Output:**
- Console: Detailed HTTP request/response analysis
- Shows: Salt, hash, login response, multi-school detection
- Temp files: Responses are saved to temp files (auto-cleaned)

**Why CURL and not Python?**
- Tests raw HTTP without any Python abstractions
- Can reveal issues with:
  - Character encoding
  - JSON parsing
  - HTTP headers
  - Request/response formats
- Provides independent verification of API behavior

**Example use case:**
If `debug_multi_school.py` works but the integration doesn't, compare:
1. CURL script responses
2. Integration API calls
3. Look for differences in how data is parsed/handled

---

## 🔄 Workflow: User Reporting an Issue

### Step 1: User Runs Debug Script

```bash
cd test-scripts
python3 debug_multi_school.py --email user@email.com --password 'secret'
```

**User gets:**
- Console output with diagnosis
- `debug-dumps/` folder with JSON files
- Clear instructions on what to do next

### Step 2: User Enables HA Debug Logging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.schulmanager_online: debug
```

### Step 3: User Extracts HA Logs

```bash
# Download logs from HA UI
python3 extract_schulmanager_logs.py ~/Downloads/home-assistant.log
```

**User gets:**
- `schulmanager_logs.txt` with only relevant logs
- Much easier to upload and read

### Step 4: User Reports Issue

User uploads:
1. Console output from debug script
2. ZIP of `debug-dumps/` folder
3. `schulmanager_logs.txt`

### Step 5: Developer Analyzes

Developer can:
- Review redacted debug dumps
- See exact error messages in logs
- Understand authentication flow
- If needed: Run CURL script to compare with API behavior

---

## 📝 Files Created by Tools

### By `debug_multi_school.py`:

```
test-scripts/debug-dumps/
├── 01_get_salt_response.json          # Salt retrieval response
├── 02_login_response.json              # Login API response
├── 03_login_parsed_user.json          # Parsed user and student data
└── (if --full-test used:)
    ├── 10_schedule_response.json
    ├── 11_class_hours_response.json
    ├── 12_homework_response.json
    ├── 13_exams_response.json
    └── 14_letters_response.json
```

All files include:
- Timestamp of capture
- Note about data redaction
- Redacted data (passwords, tokens, emails, names if requested)

### By `extract_schulmanager_logs.py`:

```
test-scripts/
└── schulmanager_logs.txt    # Filtered HA logs
```

Contains only lines with:
- "schulmanager"
- "custom_components.schulmanager_online"

---

## 🛡️ Security & Privacy

### What is Redacted:

- ✅ Passwords (never saved)
- ✅ JWT tokens (only last 8 chars)
- ✅ Email addresses (masked)
- ✅ Hashes and salts
- ✅ Authorization headers
- ✅ Student names (with `--anonymize-names`)

### What is NOT Redacted:

- ❌ Institution IDs (needed for debugging)
- ❌ Student IDs (needed for debugging)
- ❌ Class IDs (needed for debugging)
- ❌ HTTP status codes
- ❌ Error messages
- ❌ Timestamps

**All output files are SAFE to share publicly in GitHub issues.**

---

## 📖 Related Documentation

- [Multi-School Debug Script Guide](../documentation/Multi_School_Debug_Script_Guide.md) - Detailed user guide
- [Debug Information Collection](../documentation/Debug_Information_Collection.md) - Overall debugging strategy
- [Troubleshooting Guide](../documentation/Troubleshooting_Guide.md) - Common problems
- [Multi-School Complete Guide](../documentation/Multi_School_Complete_Guide.md) - Technical details

---

## 🤔 FAQ

### Q: Which tool should I use?

**For users reporting issues:** `debug_multi_school.py` + `extract_schulmanager_logs.py`  
**For developers debugging:** All three tools, especially CURL for API comparison

### Q: Do I need to install anything?

**For debug_multi_school.py:**
- Python 3.8+
- `requests` library: `pip3 install requests`

**For extract_schulmanager_logs.py:**
- Python 3.8+ (no extra dependencies)

**For test_multi_school_curl.sh:**
- bash
- curl
- python3 (for JSON parsing)

### Q: Can I run these on Windows?

**debug_multi_school.py:** ✅ Yes  
**extract_schulmanager_logs.py:** ✅ Yes  
**test_multi_school_curl.sh:** ⚠️ Needs bash (WSL, Git Bash, or Cygwin)

### Q: Are the output files safe to share?

**Yes!** All sensitive data is automatically redacted. The files contain only:
- Technical information (status codes, IDs, structure)
- Error messages
- Timestamps
- No passwords, tokens, or personal identifiable information

### Q: The debug script says "multi-school detected" but HA integration doesn't show dropdown

This is the bug we're trying to fix! Please:
1. Run the debug script
2. Enable HA debug logging
3. Extract the logs
4. Report the issue with all three outputs

The logs will show us where the multi-school detection is failing in the integration.

---

## 🐛 Debugging Checklist

When reporting a multi-school issue:

- [ ] Ran `debug_multi_school.py`
- [ ] Saved console output
- [ ] Have `debug-dumps/` folder as ZIP
- [ ] Enabled debug logging in HA
- [ ] Restarted HA
- [ ] Tried to add integration again
- [ ] Extracted HA logs with `extract_schulmanager_logs.py`
- [ ] Have `schulmanager_logs.txt` file
- [ ] Ready to upload all three to GitHub issue

---

**Need help?** Open an issue at: https://github.com/rwunsch/schulmanager-online-hass/issues
