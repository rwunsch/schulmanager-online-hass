# Authentifizierung - Detaillierter Guide

## 🔐 Übersicht

Die Schulmanager Online API verwendet eine zweistufige Authentifizierung:
1. **Salt-basiertes PBKDF2-SHA512 Hashing**
2. **JWT Token-basierte Autorisierung**

## 🧂 Salt-Abruf

### Request
```python
async def _get_salt(self) -> str:
    payload = {
        "emailOrUsername": self.email,
        "mobileApp": False,  # WICHTIG: Muss False sein!
        "institutionId": None
    }
    
    async with self.session.post(SALT_URL, json=payload) as response:
        if response.status != 200:
            raise SchulmanagerAPIError(f"Salt request failed: {response.status}")
        
        # Salt wird als String zurückgegeben, nicht als JSON-Objekt
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

### Wichtige Erkenntnisse
- **`mobileApp: False`** ist erforderlich für Web-Clients
- **Salt wird als String zurückgegeben**, nicht als JSON mit "salt"-Key
- **Fallback auf `response.text()`** für reine String-Responses

## 🔒 PBKDF2-SHA512 Hash-Generierung

### Algorithmus-Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| **Algorithm** | PBKDF2 | Password-Based Key Derivation Function 2 |
| **Hash Function** | SHA-512 | Secure Hash Algorithm 512-bit |
| **Iterations** | 99.999 | Anzahl der Hash-Iterationen |
| **Output Length** | 512 Bytes | 4096 Bits Output |
| **Hex Length** | 1024 Zeichen | Hexadezimale Darstellung |
| **Salt Encoding** | UTF-8 | **NICHT** Hex-Encoding! |
| **Password Encoding** | UTF-8 | Standard UTF-8 Encoding |

### Python-Implementierung

```python
def _generate_salted_hash(self, password: str, salt: str) -> str:
    """
    Generate salted hash using PBKDF2-SHA512
    
    Basierend auf der JavaScript-Implementierung:
    - PBKDF2 mit SHA-512
    - 512 Bytes Output (4096 Bits) = 1024 Hex-Zeichen
    - Salt als UTF-8 encodiert (nicht Hex!)
    - 99999 Iterationen
    """
    try:
        # Encode password and salt as UTF-8
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')  # WICHTIG: UTF-8, nicht Hex!
        
        # Generate hash with PBKDF2-SHA512
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha512',           # Hash algorithm
            password_bytes,     # Password
            salt_bytes,         # Salt
            99999,             # Iterations
            dklen=512          # Output length in bytes
        )
        
        # Convert to hex string (1024 characters)
        hash_hex = hash_bytes.hex()
        
        return hash_hex
        
    except Exception as e:
        raise SchulmanagerAPIError(f"Hash generation failed: {e}") from e
```

### JavaScript-Original (Referenz)

```javascript
// Original JavaScript-Implementierung aus Schulmanager Online
async function generateHash(password, salt) {
    const hashBuffer = await crypto.subtle.deriveBits(
        {
            name: "PBKDF2",
            salt: new TextEncoder().encode(salt),  // UTF-8 encoding
            iterations: 99999,
            hash: "SHA-512"
        },
        await crypto.subtle.importKey(
            "raw",
            new TextEncoder().encode(password),    // UTF-8 encoding
            "PBKDF2",
            false,
            ["deriveBits"]
        ),
        4096  // 512 bytes * 8 bits = 4096 bits
    );
    
    // Convert to hex string
    return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}
```

## 🎫 JWT Token-Authentifizierung

### Login-Request

```python
async def _login(self, salted_hash: str) -> None:
    payload = {
        "emailOrUsername": self.email,
        "password": self.password,      # Original-Passwort
        "hash": salted_hash,            # PBKDF2-SHA512 Hash
        "mobileApp": False,
        "institutionId": None
    }
    
    async with self.session.post(LOGIN_URL, json=payload) as response:
        if response.status != 200:
            raise SchulmanagerAPIError(f"Login failed: {response.status}")
        
        data = await response.json()
        
        # Token kann als "jwt" oder "token" zurückgegeben werden
        self.token = data.get("jwt") or data.get("token")
        
        if not self.token:
            raise SchulmanagerAPIError("No token received")
        
        # Store user data for student extraction
        self.user_data = data.get("user", {})
        
        # Set token expiration (1 hour from now)
        self.token_expires = datetime.now() + timedelta(hours=1)
```

### Token-Verwendung

```python
async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    await self._ensure_authenticated()
    
    headers = {
        "Authorization": f"Bearer {self.token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bundleVersion": "3505280ee7",  # Aktuelle Version
        "requests": requests
    }
    
    async with self.session.post(API_URL, json=payload, headers=headers) as response:
        # Handle response...
```

## 👥 Schülerdaten-Extraktion

### Aus Login-Response

Die Schülerdaten sind bereits in der Login-Response enthalten und müssen **nicht** über separate API-Calls abgerufen werden:

```python
async def get_students(self) -> List[Dict[str, Any]]:
    await self._ensure_authenticated()
    
    students = []
    
    # Eltern-Account: associatedParents
    associated_parents = self.user_data.get("associatedParents", [])
    for parent in associated_parents:
        student = parent.get("student")
        if student:
            students.append(student)
    
    # Schüler-Account: associatedStudent
    associated_student = self.user_data.get("associatedStudent")
    if associated_student:
        students.append(associated_student)
    
    if not students:
        raise SchulmanagerAPIError("No students found for this account")
    
    return students
```

### Schüler-Datenstruktur

```json
{
  "id": 4333047,
  "firstname": "Marc Cedric",
  "lastname": "Wunsch",
  "sex": "Male",
  "classId": 444612
}
```

## 🔄 Token-Management

### Automatische Erneuerung

```python
async def _ensure_authenticated(self) -> None:
    """Ensure we have a valid token."""
    if not self.token or not self.token_expires:
        await self.authenticate()
        return
    
    # Check if token is expired (with 5-minute buffer)
    if datetime.now() >= (self.token_expires - timedelta(minutes=5)):
        _LOGGER.debug("Token expired, re-authenticating")
        await self.authenticate()
```

### Token-Eigenschaften

| Eigenschaft | Wert | Beschreibung |
|-------------|------|--------------|
| **Format** | JWT | JSON Web Token |
| **Gültigkeit** | 1 Stunde | Automatische Erneuerung |
| **Header** | `Authorization: Bearer <token>` | HTTP-Header |
| **Erneuerung** | 5 Min vor Ablauf | Puffer für nahtlose Nutzung |

## 🚨 Häufige Authentifizierungs-Probleme

### 1. Hash-Generierung fehlgeschlagen

**Symptome:**
- Login schlägt mit 401 fehl
- Hash hat falsche Länge

**Lösungen:**
```python
# Überprüfe Hash-Parameter
assert len(hash_hex) == 1024, f"Hash length should be 1024, got {len(hash_hex)}"

# Überprüfe Salt-Encoding
salt_bytes = salt.encode('utf-8')  # NICHT: bytes.fromhex(salt)

# Überprüfe Iterationen
iterations = 99999  # NICHT: 10000
```

### 2. Salt-Abruf fehlgeschlagen

**Symptome:**
- "No salt received" Fehler
- 400 Bad Request beim Salt-Abruf

**Lösungen:**
```python
# Füge mobileApp Parameter hinzu
payload = {
    "emailOrUsername": self.email,
    "mobileApp": False,  # WICHTIG!
    "institutionId": None
}

# Handle String-Response
if isinstance(data, str):
    salt = data
else:
    salt = data.get("salt")
```

### 3. Token-Extraktion fehlgeschlagen

**Symptome:**
- "No token received" Fehler
- Login erfolgreich, aber kein Token

**Lösungen:**
```python
# Prüfe beide Token-Keys
self.token = data.get("jwt") or data.get("token")

# Debug Login-Response
_LOGGER.debug("Login response keys: %s", list(data.keys()))
```

## 🔧 Debug-Tipps

### 1. Hash-Vergleich

```python
# Vergleiche mit Browser-Hash
browser_hash = "dc17df60e0e8ce0ed835433d8103ca1de38f0c6ce52068515d62fcc8381302ba..."
python_hash = self._generate_salted_hash(password, salt)

print(f"Browser: {browser_hash}")
print(f"Python:  {python_hash}")
print(f"Match:   {browser_hash == python_hash}")
```

### 2. Salt-Debugging

```python
# Überprüfe Salt-Format
print(f"Salt: '{salt}'")
print(f"Salt length: {len(salt)}")
print(f"Salt type: {type(salt)}")
print(f"Salt bytes: {salt.encode('utf-8')}")
```

### 3. Token-Debugging

```python
# Überprüfe Token-Format
import base64
import json

# Decode JWT (ohne Signatur-Verifikation)
header, payload, signature = token.split('.')
decoded_payload = base64.urlsafe_b64decode(payload + '==')
token_data = json.loads(decoded_payload)

print(f"Token expires: {datetime.fromtimestamp(token_data['exp'])}")
print(f"User ID: {token_data['sub']}")
```

## 📚 Weiterführende Dokumentation

- [API Analysis](API_Analysis.md) - Vollständige API-Dokumentation
- [API Implementation](API_Implementation.md) - Python-Implementierung
- [Troubleshooting](Troubleshooting_Guide.md) - Problemlösungen
