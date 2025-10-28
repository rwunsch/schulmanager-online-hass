# Multi-School Complete Implementation Guide

## 🔴 CRITICAL BUG FIX (v1.0.7)

**Issue**: Multi-school authentication was failing with 401 error when selecting a specific school.

**Root Cause**: The salt endpoint returns **different salts** depending on the `institutionId` parameter. When re-authenticating with a specific school after detecting multiple schools, the code was reusing the salt fetched with `institutionId: null`, causing authentication to fail.

**Fix**: Modified `_get_salt()` to accept and pass through the `institution_id` parameter. Now the salt is correctly refetched with the institution_id before re-authentication.

**Affected Users**: Only accounts with access to multiple schools (children at different schools).

---

## Executive Summary

**Account Tested**: `wunsch@gmx.de`  
**Institution ID**: `13309`  
**Student ID**: `4333047` (Marc Cedric Wunsch)  
**Multi-School Status**: ❌ **Single school account** (no `multipleAccounts` response)

**Key Finding**: This account accesses only ONE school. The `institutionId` is returned in the user object and must be stored/reused for session persistence across HA restarts.

---

## Test Results from curl API Testing

### Test 1: Login WITHOUT institutionId
```bash
POST /api/login
{
  "emailOrUsername": "wunsch@gmx.de",
  "hash": "...",
  "institutionId": null
}
```

**Response**:
```json
{
  "user": {
    "id": 2385948,
    "firstname": "Marc Cedric",
    "lastname": "Wunsch",
    "institutionId": 13309,  ← Returned in user object
    "associatedParents": [
      {
        "student": {
          "id": 4333047,
          "firstname": "Marc Cedric",
          "lastname": "Wunsch",
          "classId": 444612
          ← NO institutionId field in student!
        }
      }
    ]
  },
  "jwt": "eyJhbGci..."
}
```

**Observations**:
- ✅ Login successful with JWT token
- ✅ `institutionId: 13309` present in `user` object
- ❌ NO `multipleAccounts` response (single school account)
- ❌ Student object does NOT contain `institutionId` field

### Test 2: Login WITH institutionId=13309
```bash
POST /api/login
{
  "emailOrUsername": "wunsch@gmx.de",
  "hash": "...",
  "institutionId": 13309
}
```

**Response**: Identical to Test 1
- Same user data
- Same JWT token structure
- Same student data (no `institutionId` in student)

**Conclusion**: Passing `institutionId` explicitly doesn't change the response for single-school accounts, but it ensures the API knows which school to authenticate against (critical for multi-school accounts).

---

## Multi-School Architecture Analysis

### Current Implementation ✅ CORRECT

**Storage Level**: Config Entry (Account Level)
```python
entry.data = {
    "email": "wunsch@gmx.de",
    "password": "***",
    "institution_id": 13309  # ONE per account/config entry
}
```

**Why This Is Correct**:
1. ✅ Students do NOT have their own `institutionId` field
2. ✅ JWT token is scoped to one `institutionId` per session
3. ✅ API design: One login = One school
4. ✅ Matches how Schulmanager API works

### Supported Scenarios

| Scenario | Supported? | Solution |
|----------|-----------|----------|
| One account, multiple children at **same** school | ✅ Yes | One config entry |
| One account, multiple children at **different** schools | ✅ Yes | Multiple config entries (one per school) |
| Multi-school account (returns `multipleAccounts`) | ✅ Yes | Select school in config flow, store `institutionId` |

### Multi-School Flow (When Applicable)

**Step 1: Initial Login** (`institutionId: null`)
```json
GET /api/get-salt with {"institutionId": null}
→ Returns salt

POST /api/login with {"institutionId": null, "hash": "..."}
→ Response: {
  "multipleAccounts": [
    {"id": 123, "label": "School A"},
    {"id": 456, "label": "School B"}
  ]
}
```
- No JWT token yet
- User must select a school

**Step 2: Re-Login** (with selected `institutionId`)

⚠️ **CRITICAL**: The salt MUST be refetched with the institution_id!

```json
GET /api/get-salt with {"institutionId": 123}
→ Returns institution-specific salt (DIFFERENT from step 1!)

POST /api/login with {"institutionId": 123, "hash": "..."}
→ Response: {"jwt": "...", "user": {...}}
```
- JWT token received
- `institutionId` stored for future use

**Why is this necessary?**
The Schulmanager API generates different salts based on the `institutionId` parameter. When authenticating with a specific school, you MUST:
1. Fetch salt WITH the institution_id
2. Generate hash from that institution-specific salt
3. Login with the institution_id and that hash

Using the salt from Step 1 (fetched with `institutionId: null`) will result in a **401 Unauthorized** error.

**Step 3: Subsequent HA Restarts**
- Read `institutionId` from `entry.data`
- Pass to `api.authenticate(institution_id=...)`
- API will fetch institution-specific salt and authenticate
- Session continues with same school

---

## Implementation Details

### API Client (`api.py`)

#### Storage
```python
class SchulmanagerAPI:
    def __init__(self, email: str, password: str, session):
        self.email = email
        self.password = password
        self.institution_id: Optional[int] = None  # Runtime storage
        self.multiple_accounts: Optional[List[Dict]] = None
```

#### Authentication Method
```python
async def authenticate(self, *, institution_id: Optional[int] = None):
    """Authenticate with optional institutionId for multi-school accounts."""
    # CRITICAL: Pass institution_id to salt request for multi-school accounts
    salt = await self._get_salt(institution_id=institution_id)
    hash = self._generate_salted_hash(self.password, salt)
    await self._login(hash, institution_id=institution_id)
```

#### Salt Retrieval
```python
async def _get_salt(self, *, institution_id: Optional[int] = None) -> str:
    """Get salt for password hashing. Pass institution_id for multi-school accounts."""
    payload = {
        "emailOrUsername": self.email,
        "mobileApp": False,
        "institutionId": institution_id,  # CRITICAL: Must include for multi-school
    }
    
    response = await self.session.post(SALT_URL, json=payload)
    # ... handle response
```

#### Login Handler
```python
async def _login(self, salted_hash: str, *, institution_id: Optional[int] = None):
    payload = {
        "emailOrUsername": self.email,
        "password": self.password,
        "hash": salted_hash,
        "mobileApp": False,
        "institutionId": institution_id,  # Pass through
    }
    
    response = await self.session.post(LOGIN_URL, json=payload)
    data = await response.json()
    
    # Check for multi-school response
    if "multipleAccounts" in data:
        self.multiple_accounts = data["multipleAccounts"]
        self.token = None  # No token yet
        return
    
    # Standard response
    self.token = data.get("jwt")
    
    # Store institutionId
    if institution_id is not None:
        self.institution_id = institution_id
    else:
        # Extract from user data
        self.institution_id = data.get("user", {}).get("institutionId")
```

### Config Flow (`config_flow.py`)

#### Initial Login Step
```python
async def async_step_user(self, user_input):
    api = SchulmanagerAPI(email, password, session)
    await api.authenticate()  # No institutionId yet
    
    # Check for multi-school
    if api.get_multiple_accounts():
        self._multiple_accounts = api.get_multiple_accounts()
        return await self.async_step_select_school()
    
    # Single school - continue with standard flow
    students = await api.get_students()
    ...
```

#### School Selection Step (Multi-School Only)
```python
async def async_step_select_school(self, user_input=None):
    if user_input is None:
        # Show dropdown
        choices = {
            str(acc["id"]): acc["label"]
            for acc in self._multiple_accounts
        }
        schema = vol.Schema({
            vol.Required("institution_id"): vol.In(choices)
        })
        return self.async_show_form(step_id="select_school", data_schema=schema)
    
    # Re-authenticate with selected school
    inst_id = int(user_input["institution_id"])
    api = SchulmanagerAPI(email, password, session)
    await api.authenticate(institution_id=inst_id)
    
    # Store in config entry data
    self._data["institution_id"] = inst_id
    
    return self.async_create_entry(data=self._data)
```

### Integration Setup (`__init__.py`) ✅ FIXED

#### Reading Stored institutionId
```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    institution_id = entry.data.get("institution_id")  # ← CRITICAL FIX
    
    api = SchulmanagerAPI(email, password, session)
    
    # Use stored institutionId on every authentication
    await api.authenticate(institution_id=institution_id)
    
    students = await api.get_students()
    ...
```

**Fix Applied**: We now read `institution_id` from storage and pass it to `authenticate()` on every HA restart.

---

## Hash Generation (Critical Implementation Detail)

**MUST use exactly 99,999 iterations** (not 10,000):

```python
def _generate_salted_hash(self, password: str, salt: str) -> str:
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    # PBKDF2-SHA512: 99999 iterations, 512 bytes output
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha512', 
        password_bytes, 
        salt_bytes, 
        99999,  # ← Critical: must be 99999
        dklen=512
    )
    
    return hash_bytes.hex()  # 1024 hex characters
```

---

## API Endpoints Reference

| Endpoint | Method | Purpose | institutionId Location |
|----------|--------|---------|----------------------|
| `/api/get-salt` | POST | Get salt for hashing | Payload: `{"institutionId": null \| 123}` ⚠️ MUST match login! |
| `/api/login` | POST | Authenticate | Payload: `{"institutionId": null \| 123}` |
| `/api/calls` | POST | All data requests | Implicit in JWT token |

**Key Insights**: 
1. The salt endpoint returns **different salts** depending on the `institutionId` parameter
2. Once authenticated with an `institutionId`, the JWT token is **scoped to that institution**
3. All subsequent API calls use that token without needing to pass `institutionId` explicitly
4. ⚠️ **CRITICAL BUG FIX** (v1.0.7): For multi-school accounts, the salt MUST be fetched with the same `institutionId` used for login, otherwise authentication fails with 401

---

## Testing Multi-School Accounts

### Prerequisites
- Account with access to multiple schools
- Initial login returns `multipleAccounts` response

### Test Script Available
```bash
cd /home/wunsch/git/schulmanager-online-hass

# Test basic login
python3 test-scripts/test_institution_login.py \
  --email your@email.com \
  --password 'your_password'

# Test with specific institutionId
python3 test-scripts/test_institution_login.py \
  --email your@email.com \
  --password 'your_password' \
  --institution-id 13309
```

**Script Shows**:
- Whether `multipleAccounts` is returned
- Student data structure
- Whether students have `institutionId` field
- Full API response for debugging

### Debugging in Home Assistant

Enable debug logging in `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
```

**Look for**:
- `Multi-school account detected with X schools` (if applicable)
- `Login successful, token expires at...`
- `Institution ID: 13309` in user data

---

## Common Questions & Answers

### Q: Do students have their own `institutionId`?
**A**: ❌ No. Students do NOT have an `institutionId` field based on testing.

### Q: Can one config entry support multiple schools?
**A**: ❌ No, by design. Each config entry = One school session.

### Q: How to support children at different schools?
**A**: Add the integration multiple times (once per school).

### Q: Does passing `institutionId` change the JWT token?
**A**: No, the JWT is the same structure, but it's **scoped** to that institution.

### Q: What if I don't pass `institutionId` for a multi-school account?
**A**: You get `multipleAccounts` response instead of a JWT token. Must select a school and re-login.

### Q: Is `institutionId` required for single-school accounts?
**A**: No, but it's returned in the user data and can be passed (doesn't hurt).

---

## Migration Notes

### For Existing Users
If your integration was set up before the fix:
1. Your `institutionId` is NOT currently being used on HA restart
2. Login still works because the API extracts it from user data
3. **Fix deployed**: Now correctly reads and uses stored `institutionId`
4. No action needed - will work correctly after update

### For New Multi-School Users
1. Add integration in HA
2. Enter credentials
3. **If multi-school**: Select school from dropdown
4. Integration stores `institutionId` automatically
5. Works correctly across HA restarts

---

## Verification Checklist

After deployment, verify:
- [ ] Integration loads without errors
- [ ] Students appear correctly
- [ ] HA restart maintains login (no re-prompting)
- [ ] Check logs for `institutionId: 13309` on authentication
- [ ] All entities update normally

---

## Conclusion

**Current Implementation Status**: ✅ **CORRECT & COMPLETE**

Our implementation:
1. ✅ Correctly stores `institutionId` at config entry level
2. ✅ Handles multi-school accounts via selection flow
3. ✅ **FIXED**: Now reads and uses stored `institutionId` on HA restart
4. ✅ Matches Schulmanager API design (one session = one school)
5. ✅ Supports multiple students at same school
6. ✅ Supports multiple schools via multiple config entries

**No architecture changes needed** - the current design correctly reflects how Schulmanager's API works.

---

## Test Data Summary

| Item | Value |
|------|-------|
| Email | wunsch@gmx.de |
| User ID | 2385948 |
| Institution ID | 13309 |
| Student ID | 4333047 |
| Student Name | Marc Cedric Wunsch |
| Class ID | 444612 |
| Multi-School | No (single school) |

**Hash Parameters**: PBKDF2-SHA512, 99,999 iterations, 512 bytes output, hex encoding (1024 chars)


