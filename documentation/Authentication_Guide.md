# Authentication Guide - Schulmanager Online API

## 🎯 Overview

The Schulmanager Online API uses a special authentication method with **PBKDF2-SHA512 hashing** and **JWT tokens**. This guide explains the authentication process in detail.

## 🔐 Authentication Flow

### 1. Complete Authentication Process

```mermaid
sequenceDiagram
    participant Client
    participant API
    
    Client->>API: POST /api/salt (email)
    API->>Client: salt string
    
    Note over Client: Generate PBKDF2-SHA512 hash
    Note over Client: hash = pbkdf2(password, salt, 99999, 512)
    
    Client->>API: POST /api/login (email, password, hash)
    API->>Client: JWT token + user data
    
    Note over Client: Store token for API calls
    
    Client->>API: POST /api/calls (with Bearer token)
    API->>Client: API response
```

## 🧂 Step 1: Salt Retrieval

### Request

```http
POST https://login.schulmanager-online.de/api/salt
Content-Type: application/json

{
  "emailOrUsername": "your-email@example.com",
  "mobileApp": false,
  "institutionId": null
}
```

### Response

```json
"random_salt_string_here"
```

### Python Implementation

```python
async def _get_salt(self) -> str:
    """Get salt for password hashing."""
    payload = {
        "emailOrUsername": self.email,
        "mobileApp": False,  # IMPORTANT: false for web clients
        "institutionId": None
    }
    
    async with self.session.post(SALT_URL, json=payload) as response:
        if response.status != 200:
            raise SchulmanagerAPIError(f"Salt request failed: {response.status}")
        
        # Handle both string and JSON responses
        try:
            data = await response.json()
            if isinstance(data, str):
                salt = data
            else:
                salt = data.get("salt")
        except Exception:
            salt = await response.text()
        
        if not salt:
            raise SchulmanagerAPIError("No salt received")
        
        return salt
```

## 🔑 Step 2: Hash Generation

### PBKDF2-SHA512 Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Algorithm** | `PBKDF2-SHA512` | Hash algorithm |
| **Iterations** | `99999` | Number of iterations |
| **Key Length** | `512 bytes` | Output length |
| **Salt Encoding** | `UTF-8` | **NOT Hex!** |
| **Output Format** | `Hex` | 1024 character string |

### Python Implementation

```python
import hashlib

def _generate_salted_hash(self, password: str, salt: str) -> str:
    """Generate salted hash using PBKDF2-SHA512"""
    try:
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')  # CRITICAL: UTF-8, not Hex!
        
        # PBKDF2-SHA512 with 99999 iterations, 512 bytes output
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha512',           # Hash algorithm
            password_bytes,     # Password as bytes
            salt_bytes,         # Salt as bytes (UTF-8!)
            99999,              # Iterations
            dklen=512           # Output length in bytes
        )
        
        # Convert to hex (1024 characters)
        hash_hex = hash_bytes.hex()
        
        return hash_hex
        
    except Exception as e:
        raise SchulmanagerAPIError(f"Hash generation failed: {e}") from e
```

### Common Hash Generation Errors

#### ❌ Wrong Salt Encoding
```python
# WRONG: Hex decoding
salt_bytes = bytes.fromhex(salt)  # DON'T DO THIS!

# CORRECT: UTF-8 encoding
salt_bytes = salt.encode('utf-8')  # CORRECT!
```

#### ❌ Wrong Parameters
```python
# WRONG: Wrong iteration count
hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 100000, dklen=512)

# CORRECT: Exactly 99999 iterations
hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
```

#### ❌ Wrong Output Length
```python
# WRONG: 64 bytes (128 hex chars)
hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=64)

# CORRECT: 512 bytes (1024 hex chars)
hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
```

## 🔓 Step 3: Login

### Request

```http
POST https://login.schulmanager-online.de/api/login
Content-Type: application/json

{
  "emailOrUsername": "your-email@example.com",
  "password": "your-original-password",
  "hash": "1024-character-pbkdf2-hash",
  "mobileApp": false,
  "institutionId": null
}
```

### Response

```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 12345,
    "email": "your-email@example.com",
    "associatedParents": [
      {
        "student": {
          "id": 67890,
          "firstName": "Max",
          "lastName": "Mustermann",
          "class": "10a"
        }
      }
    ]
  }
}
```

### Python Implementation

```python
async def _login(self, salted_hash: str) -> None:
    """Login with salted hash."""
    payload = {
        "emailOrUsername": self.email,
        "password": self.password,  # Original password!
        "hash": salted_hash,        # PBKDF2 hash
        "mobileApp": False,
        "institutionId": None
    }
    
    async with self.session.post(LOGIN_URL, json=payload) as response:
        if response.status != 200:
            raise SchulmanagerAPIError(f"Login failed: {response.status}")
        
        data = await response.json()
        
        # Extract JWT token (check both variants)
        self.token = data.get("jwt") or data.get("token")
        
        if not self.token:
            raise SchulmanagerAPIError("No token received")
        
        # Store user data for student extraction
        self.user_data = data.get("user", {})
        
        # Set token expiration (1 hour from now)
        self.token_expires = datetime.now() + timedelta(hours=1)
```

## 🎫 JWT Token Usage

### Token Structure

JWT tokens have three parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                                                                │
│            Header                    │                          Payload                                               │                    Signature
```

### Using Token for API Calls

```python
async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Make authenticated API call."""
    await self._ensure_authenticated()
    
    headers = {
        "Authorization": f"Bearer {self.token}",  # JWT token as Bearer
        "Content-Type": "application/json"
    }
    
    payload = {
        "bundleVersion": "3505280ee7",  # REQUIRED!
        "requests": requests
    }
    
    async with self.session.post(API_URL, json=payload, headers=headers) as response:
        if response.status == 401:
            # Token expired - re-authenticate
            await self.authenticate()
            headers["Authorization"] = f"Bearer {self.token}"
            
            # Retry request
            async with self.session.post(API_URL, json=payload, headers=headers) as retry_response:
                return await retry_response.json()
        
        elif response.status != 200:
            raise SchulmanagerAPIError(f"API call failed: {response.status}")
        
        return await response.json()
```

## ⏰ Token Management

### Token Expiration

JWT tokens expire after **1 hour**. The integration automatically handles token renewal:

```python
async def _ensure_authenticated(self) -> None:
    """Ensure we have a valid token."""
    if not self.token or not self.token_expires:
        await self.authenticate()
        return
    
    # Check if token expires soon (5-minute buffer)
    if datetime.now() >= (self.token_expires - timedelta(minutes=5)):
        _LOGGER.debug("Token expired, re-authenticating")
        await self.authenticate()
```

### Automatic Retry on 401

```python
# In _make_api_call method
if response.status == 401:
    # Token expired, try to re-authenticate
    await self.authenticate()
    headers["Authorization"] = f"Bearer {self.token}"
    
    # Retry the request once
    async with self.session.post(API_URL, json=payload, headers=headers) as retry_response:
        if retry_response.status != 200:
            raise SchulmanagerAPIError(f"API call failed after retry: {retry_response.status}")
        return await retry_response.json()
```

## 🧪 Testing Authentication

### Manual Test with curl

```bash
# Step 1: Get salt
curl 'https://login.schulmanager-online.de/api/salt' \
  -H 'content-type: application/json' \
  --data-raw '{"emailOrUsername":"your-email@example.com","mobileApp":false,"institutionId":null}'

# Step 2: Generate hash (use Python script)
python3 -c "
import hashlib
password = 'your-password'
salt = 'salt-from-step-1'
hash_bytes = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt.encode('utf-8'), 99999, dklen=512)
print(hash_bytes.hex())
"

# Step 3: Login
curl 'https://login.schulmanager-online.de/api/login' \
  -H 'content-type: application/json' \
  --data-raw '{
    "emailOrUsername":"your-email@example.com",
    "password":"your-password",
    "hash":"hash-from-step-2",
    "mobileApp":false,
    "institutionId":null
  }'
```

### Python Test Script

```python
#!/usr/bin/env python3
"""Test authentication with Schulmanager Online API."""

import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta

async def test_authentication():
    async with aiohttp.ClientSession() as session:
        email = "your-email@example.com"
        password = "your-password"
        
        # Step 1: Get salt
        salt_payload = {
            "emailOrUsername": email,
            "mobileApp": False,
            "institutionId": None
        }
        
        async with session.post(
            "https://login.schulmanager-online.de/api/salt",
            json=salt_payload
        ) as response:
            if response.status != 200:
                print(f"Salt request failed: {response.status}")
                return
            
            salt = await response.text()
            salt = salt.strip('"')  # Remove quotes if present
            print(f"Salt received: {salt[:20]}... ({len(salt)} chars)")
        
        # Step 2: Generate hash
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
        salted_hash = hash_bytes.hex()
        
        print(f"Hash generated: {salted_hash[:20]}... ({len(salted_hash)} chars)")
        
        # Step 3: Login
        login_payload = {
            "emailOrUsername": email,
            "password": password,
            "hash": salted_hash,
            "mobileApp": False,
            "institutionId": None
        }
        
        async with session.post(
            "https://login.schulmanager-online.de/api/login",
            json=login_payload
        ) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text}")
                return
            
            data = await response.json()
            token = data.get("jwt") or data.get("token")
            
            if token:
                print(f"Login successful! Token: {token[:50]}...")
                print(f"User ID: {data.get('user', {}).get('id')}")
                
                # Test API call
                await test_api_call(session, token)
            else:
                print("No token received!")
                print(f"Response: {data}")

async def test_api_call(session: aiohttp.ClientSession, token: str):
    """Test an API call with the token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bundleVersion": "3505280ee7",
        "requests": [
            {
                "method": "user/get-user-data",
                "data": {}
            }
        ]
    }
    
    async with session.post(
        "https://login.schulmanager-online.de/api/calls",
        json=payload,
        headers=headers
    ) as response:
        if response.status == 200:
            data = await response.json()
            print(f"API call successful! Response keys: {list(data.keys())}")
        else:
            print(f"API call failed: {response.status}")
            error_text = await response.text()
            print(f"Error: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_authentication())
```

## 🚨 Common Authentication Problems

### Problem 1: Salt Encoding Error

**Symptoms:**
- Hash generation works but login fails
- Error: "Invalid credentials" despite correct password

**Solution:**
```python
# WRONG
salt_bytes = bytes.fromhex(salt)

# CORRECT
salt_bytes = salt.encode('utf-8')
```

### Problem 2: Wrong Iteration Count

**Symptoms:**
- Login fails with "Invalid credentials"
- Hash length is correct (1024 chars)

**Solution:**
```python
# Check iteration count - must be exactly 99999
hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
```

### Problem 3: Missing Bundle Version

**Symptoms:**
- Authentication works but API calls fail
- Error: "Bundle version required"

**Solution:**
```python
payload = {
    "bundleVersion": "3505280ee7",  # REQUIRED!
    "requests": requests
}
```

### Problem 4: Token Expiration

**Symptoms:**
- First API calls work, later calls fail with 401
- Error: "Token expired"

**Solution:**
```python
# Implement automatic token renewal
if response.status == 401:
    await self.authenticate()
    # Retry request
```

## 🔧 Configuration

### Environment Variables for Testing

```bash
export SCHULMANAGER_EMAIL="your-email@example.com"
export SCHULMANAGER_PASSWORD="your-password"
export DEBUG_SCHULMANAGER_API="true"
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# In production (Home Assistant)
_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Authentication successful, token expires at %s", self.token_expires)
```

## 📚 Further Documentation

- [API Implementation](API_Implementation.md) - Complete API client
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solutions
- [Integration Architecture](Integration_Architecture.md) - Home Assistant integration
