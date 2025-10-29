# Troubleshooting Guide

## 🚨 Common Problems and Solutions

### 🔐 Authentication Problems

#### Problem: "Authentication failed: Login failed: 401"

**Symptoms:**
- Integration cannot be configured
- Setup error in Home Assistant
- Login fails

**Possible Causes:**
1. **Incorrect credentials**
2. **Hash generation error**
3. **Missing API parameters**

**Solution Steps:**

1. **Check credentials:**
   ```bash
   # Test with curl (from Research/API-call_login-salted.txt)
   curl 'https://login.schulmanager-online.de/api/salt' \
     -H 'content-type: application/json' \
     --data-raw '{"emailOrUsername":"YOUR_EMAIL","mobileApp":false,"institutionId":null}'
   ```

2. **Validate hash parameters:**
   ```python
   # In test-scripts/test_corrected_hash.py
   python test-scripts/test_corrected_hash.py
   ```

3. **Check API parameters:**
   - `mobileApp: false` must be set
   - Use `institutionId: null`
   - Encode salt as UTF-8, not as Hex

**Enable debug logs:**
```yaml
# In configuration.yaml
logger:
  default: info
  logs:
    custom_components.schulmanager_online: debug
```

#### Problem: "No salt received"

**Symptoms:**
- Salt retrieval fails
- 400 Bad Request at salt endpoint

**Solution:**
```python
# Correct salt request parameters
payload = {
    "emailOrUsername": email,
    "mobileApp": False,  # IMPORTANT: Must be False!
    "institutionId": None
}
```

#### Problem: "'str' object has no attribute 'get'"

**Symptoms:**
- Error during salt parsing
- Integration setup aborts

**Solution:**
```python
# Salt can be returned as string or JSON
try:
    data = await response.json()
    if isinstance(data, str):
        salt = data
    else:
        salt = data.get("salt")
except Exception:
    salt = await response.text()
```

### 🏫 Multi-School Problems

#### Problem: "Benutzer oder Passwort falsch" with multi-school account

**Symptoms:**
- You have children at different schools
- Integration shows "invalid_auth" error
- You can login to Schulmanager website fine
- After login, website asks you to select a school

**Root Cause:**
The integration may not be detecting the multi-school status and showing the school selection step.

**Diagnostic Steps:**

1. **Run the debug script to confirm multi-school status:**
   ```bash
   cd test-scripts
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword'
   ```
   
   Look for output:
   ```
   ⚠️  MULTI-SCHOOL ACCOUNT DETECTED!
   Found 2 schools:
      - ID: 12345  Name: Elementary School A
      - ID: 67890  Name: High School B
   ```

2. **If multi-school detected, test with specific school:**
   ```bash
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345
   ```

3. **Enable debug logging in Home Assistant:**
   ```yaml
   # configuration.yaml
   logger:
     default: warning
     logs:
       custom_components.schulmanager_online: debug
       custom_components.schulmanager_online.config_flow: debug
   ```

4. **Try adding integration again and check logs:**
   Look for these messages in Settings → System → Logs:
   - `Probing for multi-school account (institutionId=None)`
   - `Multi-school account detected with X schools` ← Should see this!
   - `Multi-school probe failed: ...` ← This indicates a bug

**Solution:**

If the school selection dropdown **does not appear** in the integration setup:

1. **Collect diagnostics:**
   - Output from `debug_multi_school.py`
   - Home Assistant logs (Settings → System → Logs, search "schulmanager")
   - Download diagnostics if integration was partially set up

2. **Report the issue:**
   - Go to: https://github.com/rwunsch/schulmanager-online-hass/issues
   - Use title: "Multi-school account - school selection not appearing"
   - Attach all debug files from `test-scripts/debug-dumps/`
   - Include console output and HA logs

**Workaround (if available):**
If you know your institution ID, you could potentially add it manually to `.storage/core.config_entries` but this is **NOT RECOMMENDED**. Wait for the fix instead.

#### Problem: School selection dropdown appears but re-authentication fails

**Symptoms:**
- School selection dropdown appears
- You select a school
- Error: "cannot_connect" or similar

**Solution:**

1. **Enable debug logging** (see above)

2. **Try again and check logs for:**
   ```
   ERROR: Re-authentication with institution_id=12345 failed: [details]
   ```

3. **Run debug script with that institution ID:**
   ```bash
   python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345
   ```

4. **Report with diagnostics** if the debug script succeeds but HA integration fails

### 👥 Student Data Problems

#### Problem: "No students found for this account"

**Symptoms:**
- Login successful, but no students found
- Integration setup fails

**Possible Causes:**
1. **Account has no student permissions**
2. **Student data not in login response**
3. **Incorrect data extraction**

**Solution Steps:**

1. **Analyze login response:**
   ```python
   # Debug output in api.py
   _LOGGER.debug("User data keys: %s", list(self.user_data.keys()))
   _LOGGER.debug("Associated parents: %s", self.user_data.get("associatedParents"))
   ```

2. **Check account type:**
   - **Parent account**: Students in `associatedParents[].student`
   - **Student account**: Student in `associatedStudent`
   - **Teacher account**: No student data available

3. **Manual verification:**
   ```bash
   # Run test script
   cd test-scripts
   python test_corrected_hash.py
   ```

### 📊 Sensor Problems

#### Problem: Sensors show "Not Available"

**Symptoms:**
- All sensors unavailable
- No data in attributes

**Solution Steps:**

1. **Check coordinator status:**
   ```python
   # In Home Assistant Developer Tools > States
   # Search for: sensor.{student_name}_*
   ```

2. **Check update interval:**
   ```python
   # In coordinator.py
   update_interval=timedelta(minutes=15)  # Default interval
   ```

3. **Test API connection:**
   ```bash
   # Standalone test
   cd test-scripts
   python standalone_api_test.py
   ```

#### Problem: "No Class" despite being school hours

**Symptoms:**
- Current Lesson shows wrong values
- Timezone problems

**Solution:**
```python
# Check timezone configuration
import datetime
now = datetime.datetime.now()
print(f"Current time: {now}")
print(f"Timezone: {now.astimezone().tzinfo}")

# In Home Assistant configuration.yaml
homeassistant:
  time_zone: Europe/Berlin
```

### 🔄 Update Problems

#### Problem: Data is not being updated

**Symptoms:**
- Sensors show outdated data
- No automatic updates

**Solution Steps:**

1. **Check coordinator logs:**
   ```bash
   # Show Docker logs
   docker logs schulmanager-ha-test | grep -i schulmanager
   ```

2. **Force manual update:**
   ```python
   # In Home Assistant Developer Tools > Services
   # Service: homeassistant.update_entity
   # Entity: sensor.{student_name}_current_lesson
   ```

3. **Check token renewal:**
   ```python
   # Token should be renewed every 55 minutes
   _LOGGER.debug("Token expires at: %s", self.token_expires)
   ```

### 🌐 Network Problems

#### Problem: "Connection timeout" / "Cannot connect"

**Symptoms:**
- API calls fail
- Intermittent connection errors

**Solution Steps:**

1. **Test network connectivity:**
   ```bash
   # Test DNS resolution
   nslookup login.schulmanager-online.de
   
   # Test HTTPS connection
   curl -I https://login.schulmanager-online.de/api/salt
   ```

2. **Adjust timeout values:**
   ```python
   # In api.py
   timeout = aiohttp.ClientTimeout(total=30, connect=10)
   session = aiohttp.ClientSession(timeout=timeout)
   ```

3. **Implement retry logic:**
   ```python
   async def _make_api_call_with_retry(self, requests, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await self._make_api_call(requests)
           except aiohttp.ClientError as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

### 🐳 Docker Problems

#### Problem: Home Assistant container won't start

**Symptoms:**
- Container status: Exited
- Port 8123 not reachable

**Solution Steps:**

1. **Check container logs:**
   ```bash
   docker logs schulmanager-ha-test
   ```

2. **Fix configuration errors:**
   ```bash
   # Validate configuration
   docker run --rm -v $(pwd)/test-scripts/ha-config:/config \
     ghcr.io/home-assistant/home-assistant:stable \
     python -m homeassistant --script check_config --config /config
   ```

3. **Correct port mapping:**
   ```yaml
   # In docker-compose-fixed.yml
   ports:
     - 8123:8123  # Explicit port mapping
   ```

#### Problem: Custom integration not loaded

**Symptoms:**
- Integration not visible in Settings
- "Domain not found" error

**Solution Steps:**

1. **Check volume mapping:**
   ```bash
   # Check if custom_components is mounted
   docker exec schulmanager-ha-test ls -la /config/custom_components/
   ```

2. **Reload integration:**
   ```bash
   # Restart Home Assistant
   docker restart schulmanager-ha-test
   ```

3. **Validate manifest:**
   ```json
   // custom_components/schulmanager_online/manifest.json
   {
     "domain": "schulmanager_online",
     "name": "Schulmanager Online",
     "version": "1.0.0",
     "documentation": "https://github.com/...",
     "dependencies": [],
     "codeowners": [],
     "requirements": ["aiohttp", "python-dateutil"],
     "iot_class": "cloud_polling"
   }
   ```

### 🎨 Custom Card Problems

#### Problem: Custom card is not displayed

**Symptoms:**
- "Custom element doesn't exist" error
- Empty card in dashboard

**Solution Steps:**

1. **Check card registration:**
   ```javascript
   // Open browser console (F12)
   console.log(customElements.get('schulmanager-schedule-card'));
   ```

2. **Correct resource path:**
   ```yaml
   # In configuration.yaml
   lovelace:
     resources:
       - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
         type: module
   ```

3. **Validate card configuration:**
   ```yaml
   # Dashboard card
   type: custom:schulmanager-schedule-card
   entity: sensor.name_of_child_current_lesson
   view: weekly_matrix
   ```

### 🔧 Development Problems

#### Problem: Test scripts fail

**Symptoms:**
- ModuleNotFoundError
- Import errors

**Solution Steps:**

1. **Activate virtual environment:**
   ```bash
   cd test-scripts
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Correct Python path:**
   ```python
   # At the beginning of the script
   import sys
   import os
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```

3. **Install dependencies:**
   ```bash
   pip install aiohttp python-dateutil
   ```

## 🔍 Debug Strategies

### Enable Logging

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
    custom_components.schulmanager_online.coordinator: debug
```

### Track API Calls

```python
# In api.py - Temporarily for debugging
async def _make_api_call(self, requests):
    _LOGGER.debug("API Request: %s", requests)
    
    response = await self.session.post(API_URL, json=payload, headers=headers)
    
    _LOGGER.debug("API Response Status: %s", response.status)
    _LOGGER.debug("API Response Headers: %s", dict(response.headers))
    
    data = await response.json()
    _LOGGER.debug("API Response Data: %s", data)
    
    return data
```

### State Debugging

```python
# Developer Tools > Template
{{ states('sensor.name_of_child_current_lesson') }}
{{ state_attr('sensor.name_of_child_current_lesson', 'subject') }}
{{ states.sensor.name_of_child_current_lesson.last_updated }}
```

### Network Debugging

```bash
# Wireshark/tcpdump for HTTP traffic
sudo tcpdump -i any -A -s 0 'host login.schulmanager-online.de'

# curl for API tests
curl -v 'https://login.schulmanager-online.de/api/salt' \
  -H 'content-type: application/json' \
  --data-raw '{"emailOrUsername":"test@example.com","mobileApp":false,"institutionId":null}'
```

## 📋 Problem Diagnosis Checklist

### ✅ Basic Checks

- [ ] Home Assistant is running and accessible (http://localhost:8123)
- [ ] Custom integration is present in `/config/custom_components/`
- [ ] Credentials are correct
- [ ] Internet connection works
- [ ] Schulmanager Online website is accessible

### ✅ API Checks

- [ ] Salt retrieval works
- [ ] Hash generation correct (1024 characters)
- [ ] Login successful (JWT token received)
- [ ] Student data available
- [ ] Schedule data retrievable

### ✅ Integration Checks

- [ ] Integration visible in Settings > Integrations
- [ ] Configuration successful
- [ ] Sensors are created
- [ ] Sensors have data
- [ ] Updates work

### ✅ UI Checks

- [ ] Sensors visible in States
- [ ] Attributes correctly filled
- [ ] Custom card loads
- [ ] Dashboard shows data

## 📊 Collecting Diagnostic Information

### Method 1: Download Diagnostics (EASIEST)

Home Assistant has a built-in diagnostics feature that automatically collects and redacts all necessary information:

**Steps:**
1. Go to **Settings → Integrations**
2. Find **Schulmanager Online**
3. Click the **three dots (⋮)** on the integration
4. Select **Download Diagnostics**
5. Save the JSON file

**What it includes:**
- Configuration data (passwords redacted)
- Multi-school detection status
- Student count and structure (names redacted)
- API connection status
- Token expiration
- Last errors
- Institution ID information

**This file is SAFE to share** - all sensitive data is automatically redacted.

### Method 2: Run External Debug Script

For pre-installation testing or when the integration won't load:

```bash
cd test-scripts
python3 debug_multi_school.py --email your@email.com --password 'YourPassword'
```

Outputs to: `test-scripts/debug-dumps/` (all files are automatically redacted)

### Method 3: Enable Debug Logging

For detailed troubleshooting:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
    custom_components.schulmanager_online.config_flow: debug
```

Then view logs in: **Settings → System → Logs** (search for "schulmanager")

## 🆘 Support and Help

### Log Collection for Support

```bash
# Collect complete logs
docker logs schulmanager-ha-test > ha_logs.txt 2>&1

# Only Schulmanager-relevant logs
docker logs schulmanager-ha-test 2>&1 | grep -i schulmanager > schulmanager_logs.txt

# System information
echo "=== System Info ===" > debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
echo "=== Container Status ===" >> debug_info.txt
docker ps >> debug_info.txt
```

### Minimal Reproduction

```python
# Minimal test script for error reproduction
import asyncio
import aiohttp
from custom_components.schulmanager_online.api import SchulmanagerAPI

async def minimal_test():
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI("EMAIL", "PASSWORD", session)
        
        try:
            await api.authenticate()
            print("✅ Authentication successful")
            
            students = await api.get_students()
            print(f"✅ Found {len(students)} students")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(minimal_test())
```

### Community Support

- **GitHub Issues**: For bug reports and feature requests
- **Home Assistant Community**: For general questions
- **Discord/Forum**: For real-time help

## 📚 Further Documentation

- [API Analysis](API_Analysis.md) - API details
- [Authentication Guide](Authentication_Guide.md) - Authentication
- [Integration Architecture](Integration_Architecture.md) - Architecture
- [Development Setup](Development_Setup.md) - Development environment
