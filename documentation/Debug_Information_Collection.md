# Debug Information Collection - Complete Guide

## Overview

This document explains how to collect and share debug information for the Schulmanager Online Home Assistant integration, specifically for **multi-school login issues** reported in [Issue #1](https://github.com/rwunsch/schulmanager-online-hass/issues/1).

## 🎯 Three-Layer Debugging Strategy

We've implemented a comprehensive three-layer approach for collecting debug information:

### Layer 1: External Debug Script (Pre-Installation)
**When:** Before installing the integration or when it won't load  
**Tool:** `test-scripts/debug_multi_school.py`  
**Output:** Redacted JSON files in `test-scripts/debug-dumps/`

### Layer 2: Enhanced Logging (Runtime)
**When:** During integration setup or operation  
**Tool:** Home Assistant debug logging  
**Output:** Detailed logs in HA system logs

### Layer 3: Diagnostics Download (Post-Installation)
**When:** Integration is installed (even if not working correctly)  
**Tool:** Built-in HA diagnostics feature  
**Output:** Comprehensive JSON file with redacted data

---

## 📋 For Users: How to Collect Debug Information

### Scenario 1: Integration Won't Install

**You see error: "Benutzer oder Passwort falsch" but credentials are correct**

1. **Run the external debug script:**
   ```bash
   cd test-scripts
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword'
   ```

2. **Check if multi-school detected:**
   - Look for: `⚠️ MULTI-SCHOOL ACCOUNT DETECTED!`
   - Note the school IDs shown
   - If multi-school: re-run with specific ID:
     ```bash
     python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345
     ```

3. **Collect the output:**
   - Copy the entire console output
   - ZIP the `test-scripts/debug-dumps/` folder

4. **Enable HA debug logging:**
   ```yaml
   # configuration.yaml
   logger:
     default: warning
     logs:
       custom_components.schulmanager_online: debug
       custom_components.schulmanager_online.config_flow: debug
   ```

5. **Try integration setup again** and note what happens

6. **Report the issue:**
   - Go to: https://github.com/rwunsch/schulmanager-online-hass/issues
   - Title: "Multi-school login issue - school selection not appearing"
   - Attach: Console output + debug-dumps ZIP + HA logs

### Scenario 2: School Selection Fails

**School dropdown appears but authentication fails after selection**

1. **Enable debug logging** (see above)

2. **Try integration setup again**

3. **Check HA logs** (Settings → System → Logs) for:
   ```
   ERROR: Re-authentication with institution_id=12345 failed: [details]
   ```

4. **Run debug script with that institution ID:**
   ```bash
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345 --full-test
   ```

5. **Download diagnostics** (if integration partially loaded):
   Settings → Integrations → Schulmanager Online → ⋮ → Download Diagnostics

6. **Report with all collected data**

### Scenario 3: Integration Loaded But Not Working

**Integration is installed but sensors show unavailable or wrong data**

1. **Download diagnostics:**
   Settings → Integrations → Schulmanager Online → ⋮ → Download Diagnostics

2. **Enable debug logging and restart**

3. **Wait for one update cycle** (15 minutes)

4. **Check logs** for errors

5. **Optionally run debug script** for comparison:
   ```bash
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --full-test
   ```

6. **Report with diagnostics + logs + debug script output**

---

## 🔧 For Developers: What We Implemented

### 1. Enhanced Diagnostics (`diagnostics.py`)

**Added multi-school detection information:**
```python
{
  "multi_school": {
    "has_institution_id_in_config": true/false,
    "institution_id_value": 12345 or null,
    "api_has_multiple_accounts": true/false,
    "multiple_accounts_count": 2,
    "api_institution_id": 12345
  },
  "students": {
    "count": 2,
    "details": [
      {
        "id": 4333047,
        "has_institution_id_field": false,
        "institution_id_if_present": null,
        "class_id": 444612
      }
    ]
  }
}
```

**Redaction includes:**
- passwords, tokens, hashes, salts
- email addresses
- student first/last names

### 2. Improved Config Flow Logging (`config_flow.py`)

**Multi-school detection now logs:**
- `DEBUG: Probing for multi-school account (institutionId=None)`
- `INFO: Multi-school account detected with N schools`
- `DEBUG: Single-school account detected`
- `WARNING: Multi-school probe failed: [exception details with traceback]`

**School selection now logs:**
- `DEBUG: Available schools for selection: {...}`
- `INFO: User selected institution ID: 12345`
- `DEBUG: Re-authenticating with institution_id=12345`
- `INFO: Successfully authenticated with institution 12345, found N students`
- `ERROR: Re-authentication with institution_id=12345 failed: [details with traceback]`

**Key change:** We no longer silently swallow exceptions with `except Exception: pass`

### 3. Enhanced Debug Script (`test-scripts/debug_multi_school.py`)

**New features:**
- Better error messages and user guidance
- Clear instructions for GitHub issue reporting
- Multi-school detection with explicit next steps
- Output shows what SHOULD happen in HA integration
- Flags issues when school selection should appear but might not

**Output improvements:**
```
📋 NEXT STEPS FOR HOME ASSISTANT INTEGRATION:
   1. When adding the integration in Home Assistant:
      - You SHOULD see a school selection dropdown
      - Select the school you want to monitor
   
   2. If the school selection dropdown does NOT appear:
      - This is the bug! Please report it with these debug files.
```

### 4. Updated Documentation

**Three documents updated:**
1. **Debug_Script_Guide.md**
   - Added GitHub issue template
   - Added HA diagnostics download instructions
   - Added debug logging setup steps

2. **Troubleshooting_Guide.md**
   - New section: "Multi-School Problems"
   - Three diagnostic collection methods
   - Step-by-step troubleshooting for multi-school issues

3. **Multi_School_Complete_Guide.md**
   - Updated with new debug script features
   - Added debug logging messages to look for
   - Added diagnostics download information

---

## 🔍 What Gets Logged Now

### Multi-School Detection Flow

**Successful Detection:**
```
[config_flow] DEBUG: Probing for multi-school account (institutionId=None)
[api] DEBUG: 🧂 Requesting salt from: https://login.schulmanager-online.de/api/get-salt
[api] DEBUG: 🧂 Salt response status: 200
[api] INFO: Multi-school account detected with 2 schools
[config_flow] INFO: Multi-school account detected with 2 schools
```

**Failed Detection (Bug):**
```
[config_flow] DEBUG: Probing for multi-school account (institutionId=None)
[api] DEBUG: 🧂 Requesting salt from: https://login.schulmanager-online.de/api/get-salt
[api] ERROR: ❌ Salt request failed: 401 - ...
[config_flow] WARNING: Multi-school probe failed (continuing with normal flow): ...
Traceback (most recent call last):
  ...
```

### School Selection Flow

**Successful Selection:**
```
[config_flow] DEBUG: Available schools for selection: {'12345': 'Elementary School', '67890': 'High School'}
[config_flow] INFO: User selected institution ID: 12345
[config_flow] DEBUG: Re-authenticating with institution_id=12345
[api] DEBUG: 🧂 Requesting salt from: ... (with institutionId: 12345)
[api] DEBUG: Login successful, token expires at ...
[config_flow] INFO: Successfully authenticated with institution 12345, found 2 students
[config_flow] DEBUG: Stored institution_id=12345 in config entry data
```

**Failed Re-Authentication (Bug):**
```
[config_flow] INFO: User selected institution ID: 12345
[config_flow] DEBUG: Re-authenticating with institution_id=12345
[api] ERROR: ❌ Salt request failed: 401 - ...
[config_flow] ERROR: Re-authentication with institution_id=12345 failed: Authentication failed: ...
Traceback (most recent call last):
  ...
```

---

## 📤 GitHub Issue Template

When users report multi-school issues, they should use this template:

```markdown
## Problem Description
I have children at 2 different schools and the integration shows "Benutzer oder Passwort falsch" (username or password incorrect), but I can login to the Schulmanager website fine.

## Multi-School Status
- [x] I have children at multiple schools
- [x] I ran the debug script: `debug_multi_school.py`
- [x] The script detected: **Multi-School Account with 2 schools**

## Debug Files Attached
- [x] Console output (pasted below)
- [x] Files from `debug-dumps/` folder (attached as ZIP)
- [ ] Home Assistant diagnostics (integration won't load)

## Console Output
```
[Paste entire output from debug_multi_school.py]
```

## Home Assistant Logs
```
[Paste relevant logs from Settings → System → Logs]
```

## Steps to Reproduce
1. Add Schulmanager Online integration in Home Assistant
2. Enter email and password
3. Expected: School selection dropdown should appear
4. Actual: Error message "Benutzer oder Passwort falsch"

## Environment
- Home Assistant Version: 2024.1.0
- Integration Version: 1.0.7
- Python Version: 3.11.0
```

---

## ✅ Success Criteria

With these improvements, we can now:

1. **Detect** multi-school accounts during integration setup
2. **Log** detailed information when detection succeeds or fails
3. **Provide** users with easy-to-run debug tools
4. **Collect** comprehensive diagnostics automatically
5. **Redact** sensitive information automatically
6. **Guide** users through the reporting process
7. **Debug** issues remotely with complete information

---

## 🎓 Best Practices Summary

### ✅ DO: Use Home Assistant's Built-in Features
- Diagnostics download (automatic redaction)
- Debug logging configuration
- Exception logging with `exc_info=True`

### ✅ DO: Provide External Debug Tools
- Standalone scripts that work outside HA
- Automatic data redaction in outputs
- Clear user guidance and next steps

### ✅ DO: Log Comprehensively
- INFO level: Success milestones
- DEBUG level: Detailed flow
- WARNING level: Non-fatal issues
- ERROR level: Failures with stack traces

### ❌ DON'T: Create Debug Files in Integration Folder
- Violates HA security model
- May not have write permissions
- Files don't survive updates
- No mechanism to collect them

### ❌ DON'T: Silently Swallow Exceptions
- Always log the exception details
- Use `exc_info=True` for stack traces
- Help users understand what went wrong

---

## 📚 Related Documentation

- [Debug Script Guide](Debug_Script_Guide.md) - User guide for `debug_multi_school.py`
- [Troubleshooting Guide](Troubleshooting_Guide.md) - General troubleshooting
- [Multi-School Complete Guide](Multi_School_Complete_Guide.md) - Technical details
- [Authentication Guide](Authentication_Guide.md) - Authentication flow details

---

**Last Updated:** 2025-10-29  
**Applies to:** Integration v1.0.7+  
**Related Issues:** [#1](https://github.com/rwunsch/schulmanager-online-hass/issues/1)

