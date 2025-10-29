# Institution API - Detailed Documentation

## 🎯 Overview

The Institution API provides access to detailed information about schools/institutions in the Schulmanager Online system. This endpoint is essential for retrieving the **actual school name** and other institutional details that are not available in the login response for single-school accounts.

**Generated on:** October 29, 2025  
**Discovery Method:** Systematic API endpoint testing  
**Status:** ✅ Confirmed working with production API

---

## 🔍 Discovery Background

### The Problem
When logging in with a single-school account, the login response only returns:
- `institutionId`: The numeric ID (e.g., 13309)
- **NO** institution name, address, or other details

For multi-school accounts, the school name is available in the `multipleAccounts[].label` field, but single-school accounts don't receive this data structure.

### The Solution
After systematic testing of various API modules and endpoints, we discovered that **5 different endpoints** all provide access to full institution details:

| Module | Endpoint | Status |
|--------|----------|--------|
| `main` | `get-institution` | ✅ Working |
| `settings` | `get-institution` | ✅ Working |
| `admin` | `get-institution` | ✅ Working |
| `profile` | `get-institution` | ✅ Working |
| `user` | `get-institution` | ✅ Working |

**Recommendation:** Use `main/get-institution` as it appears to be the most general-purpose endpoint.

---

## 📡 API Endpoint Details

### Request Format

**Endpoint:** `/api/calls`  
**Method:** POST  
**Authentication:** Required (Bearer token from login)  
**Module:** `main` (recommended)  
**Endpoint Name:** `get-institution`

#### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "main",
      "endpointName": "get-institution",
      "parameters": {}
    }
  ]
}
```

**Note:** No parameters are required. The endpoint automatically returns information for the institution associated with the authenticated user's JWT token.

---

## 📊 Response Structure

### Successful Response

```json
{
  "results": [
    {
      "id": 1,
      "status": 200,
      "data": {
        "id": 13309,
        "name": "Moritz-Fontaine-Gesamtschule Rheda-Wiedenbrück",
        "street": "Fürst-Bentheim-Straße 55",
        "zipcode": "33378",
        "city": "Rheda-Wiedenbrück",
        "website": "www.mfg.nrw",
        "email": "sekretariat@gesamtschule-rh-wd.de",
        "phone": "09876 / 54321 - 0",
        "fax": "09876 / 54321 - 10",
        "region": "DE-NW",
        "schoolTypes": ["Gesamtschule"],
        "timeZone": "Europe/Berlin"
      }
    }
  ]
}
```

### Response Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | `integer` | Institution ID | `13309` |
| `name` | `string` | Full official name of the institution | `"Moritz-Fontaine-Gesamtschule Rheda-Wiedenbrück"` |
| `street` | `string` | Street address | `"Fürst-Bentheim-Straße 55"` |
| `zipcode` | `string` | Postal code | `"33378"` |
| `city` | `string` | City name | `"Rheda-Wiedenbrück"` |
| `website` | `string` | School website URL | `"www.mfg.nrw"` |
| `email` | `string` | School contact email | `"sekretariat@gesamtschule-rh-wd.de"` |
| `phone` | `string` | Phone number | `"09876 / 54321 - 0"` |
| `fax` | `string` | Fax number | `"09876 / 54321 - 10"` |
| `region` | `string` | German state code (ISO 3166-2:DE) | `"DE-NW"` (Nordrhein-Westfalen) |
| `schoolTypes` | `array<string>` | List of school types | `["Gesamtschule"]` |
| `timeZone` | `string` | IANA timezone identifier | `"Europe/Berlin"` |

### Region Codes

Common German state codes returned in the `region` field:

| Code | State (German) | State (English) |
|------|----------------|-----------------|
| `DE-BW` | Baden-Württemberg | Baden-Württemberg |
| `DE-BY` | Bayern | Bavaria |
| `DE-BE` | Berlin | Berlin |
| `DE-BB` | Brandenburg | Brandenburg |
| `DE-HB` | Bremen | Bremen |
| `DE-HH` | Hamburg | Hamburg |
| `DE-HE` | Hessen | Hesse |
| `DE-MV` | Mecklenburg-Vorpommern | Mecklenburg-Vorpommern |
| `DE-NI` | Niedersachsen | Lower Saxony |
| `DE-NW` | Nordrhein-Westfalen | North Rhine-Westphalia |
| `DE-RP` | Rheinland-Pfalz | Rhineland-Palatinate |
| `DE-SL` | Saarland | Saarland |
| `DE-SN` | Sachsen | Saxony |
| `DE-ST` | Sachsen-Anhalt | Saxony-Anhalt |
| `DE-SH` | Schleswig-Holstein | Schleswig-Holstein |
| `DE-TH` | Thüringen | Thuringia |

### School Types

Common values in the `schoolTypes` array:

- `"Grundschule"` - Primary School
- `"Hauptschule"` - Secondary School (basic track)
- `"Realschule"` - Secondary School (intermediate track)
- `"Gymnasium"` - Grammar School (academic track)
- `"Gesamtschule"` - Comprehensive School
- `"Förderschule"` - Special Needs School
- `"Berufsschule"` - Vocational School

---

## 💻 Implementation Examples

### Python (AsyncIO with aiohttp)

```python
async def get_institution_details(token: str, bundle_version: str) -> dict:
    """Fetch institution details from Schulmanager API."""
    url = "https://login.schulmanager-online.de/api/calls"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bundleVersion": bundle_version,
        "requests": [{
            "moduleName": "main",
            "endpointName": "get-institution",
            "parameters": {}
        }]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"API call failed: {response.status}")
            
            data = await response.json()
            results = data.get("results", [])
            
            if not results or results[0].get("status") != 200:
                raise Exception("Institution data not available")
            
            return results[0]["data"]

# Usage
institution = await get_institution_details(jwt_token, "3505280ee7")
print(f"School: {institution['name']}")
print(f"Location: {institution['city']}, {institution['region']}")
```

### Python (Home Assistant Integration)

```python
from typing import Dict, Any
from homeassistant.core import HomeAssistant

class SchulmanagerAPI:
    """API client for Schulmanager Online."""
    
    async def get_institution(self) -> Dict[str, Any]:
        """Get institution/school details including name, address, etc."""
        await self._ensure_authenticated()
        
        # Use the main/get-institution endpoint
        result = await self._make_api_call([{
            "moduleName": "main",
            "endpointName": "get-institution",
            "parameters": {}
        }])
        
        results = result.get("results", [])
        if not results:
            raise Exception("No results from get-institution endpoint")
        
        first_result = results[0]
        if first_result.get("status") != 200:
            raise Exception(f"API returned status {first_result.get('status')}")
        
        institution_data = first_result.get("data", {})
        if not institution_data:
            raise Exception("No institution data in response")
        
        return institution_data
```

### cURL

```bash
# First, authenticate and get JWT token
JWT_TOKEN="your_jwt_token_here"
BUNDLE_VERSION="3505280ee7"

# Then fetch institution details
curl -X POST https://login.schulmanager-online.de/api/calls \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bundleVersion": "'$BUNDLE_VERSION'",
    "requests": [{
      "moduleName": "main",
      "endpointName": "get-institution",
      "parameters": {}
    }]
  }'
```

---

## 🔄 Integration Use Cases

### Use Case 1: Single-School Account Setup
**Problem:** Login returns `institutionId: 13309` but no school name.

**Solution:**
1. Authenticate and get JWT token
2. Call `main/get-institution` endpoint
3. Extract `name` field: `"Moritz-Fontaine-Gesamtschule Rheda-Wiedenbrück"`
4. Store with student data for display

### Use Case 2: Multi-School Account Enhancement
**Problem:** Multi-school accounts get school names from `multipleAccounts[].label`, but want additional details (address, phone, etc.).

**Solution:**
1. Authenticate with specific `institutionId`
2. Call `main/get-institution` endpoint for each school
3. Store extended information for each institution

### Use Case 3: Device Identification
**Problem:** Need to create unique device identifiers including school name.

**Solution:**
```python
institution = await api.get_institution()
device_name = f"{student_name} - {institution['name']}"
device_id = f"schulmanager_{institution['id']}_{student_id}"
```

---

## ⚠️ Important Notes

### Token Scope
The JWT token returned from login is **scoped to a specific institution**. This means:
- The `get-institution` endpoint returns data for the institution associated with the current token
- For multi-school accounts, you need to authenticate separately for each school to get their institution details
- The `institutionId` from the token cannot be changed without re-authenticating

### Authentication Requirement
All institution API endpoints require:
1. Valid JWT token from successful login
2. Token must not be expired (typically 1-hour lifetime)
3. User must have access to the institution (parent/student/teacher account)

### Rate Limiting
- No specific rate limits documented
- Recommended: Cache institution data (it rarely changes)
- Suggested cache duration: 24 hours or until token expires

### Data Freshness
Institution data (name, address, contact details) is relatively static. Suggested caching strategy:
```python
# Cache institution data for 24 hours
cache_duration = timedelta(hours=24)

if not cached_institution or (datetime.now() - cache_time) > cache_duration:
    cached_institution = await api.get_institution()
    cache_time = datetime.now()
```

---

## 🧪 Testing

### Test Script

A standalone test script is available to verify the endpoint:

```bash
cd test-scripts
python3 test_institution_api.py
```

This script:
1. Authenticates with provided credentials
2. Decodes JWT token payload
3. Tests all 5 institution endpoints
4. Displays full institution data
5. Confirms endpoint availability

### Manual Testing

```python
import asyncio
import aiohttp
import hashlib
import json

async def test_institution_endpoint():
    email = "your@email.com"
    password = "your_password"
    
    async with aiohttp.ClientSession() as session:
        # 1. Get salt
        async with session.post(
            "https://login.schulmanager-online.de/api/get-salt",
            json={"emailOrUsername": email, "mobileApp": False, "institutionId": None}
        ) as resp:
            salt = (await resp.text()).strip('"')
        
        # 2. Generate hash
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha512', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            99999, 
            dklen=512
        )
        salted_hash = hash_bytes.hex()
        
        # 3. Login
        async with session.post(
            "https://login.schulmanager-online.de/api/login",
            json={
                "emailOrUsername": email,
                "password": password,
                "hash": salted_hash,
                "mobileApp": False,
                "institutionId": None
            }
        ) as resp:
            login_data = await resp.json()
            token = login_data["jwt"]
        
        # 4. Get institution
        async with session.post(
            "https://login.schulmanager-online.de/api/calls",
            json={
                "bundleVersion": "3505280ee7",
                "requests": [{
                    "moduleName": "main",
                    "endpointName": "get-institution",
                    "parameters": {}
                }]
            },
            headers={"Authorization": f"Bearer {token}"}
        ) as resp:
            data = await resp.json()
            institution = data["results"][0]["data"]
            print(json.dumps(institution, indent=2))

asyncio.run(test_institution_endpoint())
```

---

## 📚 Related Documentation

- [Authentication Guide](Authentication_Guide.md) - How to authenticate and get JWT tokens
- [Multi-School Complete Guide](Multi_School_Complete_Guide.md) - Multi-school account handling
- [API Analysis](API_Analysis.md) - General API structure and patterns
- [API Implementation](API_Implementation.md) - Integration implementation details

---

## 🔍 API Endpoint Comparison

All five endpoints return identical data:

| Endpoint | Performance | Use Case | Recommendation |
|----------|-------------|----------|----------------|
| `main/get-institution` | Fast | General purpose | ✅ **Recommended** |
| `settings/get-institution` | Fast | Settings context | Alternative |
| `admin/get-institution` | Fast | Admin context | Alternative |
| `profile/get-institution` | Fast | User profile context | Alternative |
| `user/get-institution` | Fast | User context | Alternative |

**Conclusion:** Use `main/get-institution` as the primary endpoint for consistency.

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-29 | 1.0 | Initial documentation - discovered 5 working institution endpoints |

---

## 🎯 Quick Reference

**Need institution name for a single-school account?**
```python
institution_data = await api.get_institution()
school_name = institution_data["name"]
```

**Need full school details?**
```python
institution = await api.get_institution()
# institution contains: id, name, street, zipcode, city, website, 
# email, phone, fax, region, schoolTypes, timeZone
```

**Testing the endpoint?**
```bash
cd test-scripts
python3 test_institution_api.py
```

---

*This documentation was created through systematic API endpoint discovery and testing with production credentials on October 29, 2025.*

