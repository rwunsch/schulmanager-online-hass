# Schulmanager Online API - Detaillierte Analyse

## 🎯 Übersicht

Die Schulmanager Online API ist eine REST-API, die über HTTPS kommuniziert und JWT-Token für die Authentifizierung verwendet. Die API erfordert eine spezielle PBKDF2-SHA512 Hash-Authentifizierung.

## 🔗 API-Endpunkte

### Base URLs
- **Login/Auth**: `https://login.schulmanager-online.de/api/`
- **API Calls**: `https://login.schulmanager-online.de/api/calls`

### Authentifizierung-Endpunkte

#### 1. Salt abrufen
```http
POST /api/salt
Content-Type: application/json

{
  "emailOrUsername": "user@example.com",
  "mobileApp": false,
  "institutionId": null
}
```

**Response:**
```json
"random_salt_string_here"
```

#### 2. Login mit Hash
```http
POST /api/login
Content-Type: application/json

{
  "emailOrUsername": "user@example.com",
  "password": "original_password",
  "hash": "pbkdf2_sha512_hash_1024_chars",
  "mobileApp": false,
  "institutionId": null
}
```

**Response:**
```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2385948,
    "email": "user@example.com",
    "firstname": "Max",
    "lastname": "Mustermann",
    "associatedParents": [
      {
        "student": {
          "id": 4333047,
          "firstname": "Marc Cedric",
          "lastname": "Wunsch",
          "sex": "Male",
          "classId": 444612
        }
      }
    ]
  }
}
```

### Daten-Endpunkte

#### 3. API Calls (Hauptendpunkt)

**Stundenplan abrufen:**
```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "schedules",
      "endpointName": "get-actual-lessons",
      "parameters": {
        "student": {
          "id": 4333047,
          "firstname": "Marc Cedric",
          "lastname": "Wunsch",
          "sex": "Male",
          "classId": 444612
        },
        "start": "2025-09-08",
        "end": "2025-09-14"
      }
    }
  ]
}
```

**Hausaufgaben abrufen:**
```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "classbook",
      "endpointName": "get-homework",
      "parameters": {
        "student": {"id": 4333047}
      }
    }
  ]
}
```

**Klassenarbeiten abrufen:**
```http
POST /api/calls
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bundleVersion": "3505280ee7",
  "requests": [
    {
      "moduleName": "exams",
      "endpointName": "get-exams",
      "parameters": {
        "student": {"id": 4333047},
        "start": "2025-09-14",
        "end": "2025-10-25"
      }
    }
  ]
}
```

## 🔐 Authentifizierung im Detail

### PBKDF2-SHA512 Hashing

Die API verwendet eine spezielle Hash-Funktion basierend auf PBKDF2-SHA512:

**Parameter:**
- **Algorithm**: PBKDF2 mit SHA-512
- **Iterationen**: 99.999
- **Output-Länge**: 512 Bytes (4096 Bits)
- **Hex-Länge**: 1024 Zeichen
- **Salt-Encoding**: UTF-8 (nicht Hex!)
- **Password-Encoding**: UTF-8

**JavaScript-Implementierung (Original):**
```javascript
const hashBuffer = await crypto.subtle.deriveBits(
  {
    name: "PBKDF2",
    salt: new TextEncoder().encode(salt),
    iterations: 99999,
    hash: "SHA-512"
  },
  await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  ),
  4096  // 512 bytes * 8 bits = 4096 bits
);
```

**Python-Implementierung:**
```python
def _generate_salted_hash(self, password: str, salt: str) -> str:
    """Generate salted hash using PBKDF2-SHA512"""
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
    hash_hex = hash_bytes.hex()
    return hash_hex
```

### JWT Token Management

**Token-Eigenschaften:**
- **Typ**: JWT (JSON Web Token)
- **Gültigkeit**: 1 Stunde
- **Verwendung**: Authorization Header als Bearer Token
- **Erneuerung**: Automatisch bei Ablauf

## 📊 API-Module und Endpunkte

### Schedules Module
- **`get-actual-lessons`**: Aktuelle Stunden abrufen
- **`get-class-hours`**: Schulstunden-Schema abrufen

### Classbook Module
- **`get-homework`**: Hausaufgaben für einen Schüler abrufen

### Exams Module
- **`get-exams`**: Klassenarbeiten/Tests für einen Schüler abrufen

### Grades Module (Experimental)
- **`get-grades`**: Noten für einen Schüler abrufen

### Verfügbare Parameter
- **`student`**: Schüler-Objekt mit ID, Name, Geschlecht, Klassen-ID
- **`start`**: Start-Datum (ISO Format: YYYY-MM-DD)
- **`end`**: End-Datum (ISO Format: YYYY-MM-DD)

## 🔄 API Response-Struktur

**WICHTIG**: Alle API-Responses verwenden `"results"` statt `"responses"` als Hauptfeld!

### Stundenplan Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "date": "2025-09-11",
          "classHour": {
            "id": 30172,
            "number": "5",
            "startTime": "11:30",
            "endTime": "12:15"
          },
          "lesson": {
            "id": 123456,
            "subject": "Mathematik",
            "teacher": "Herr Schmidt",
            "room": "R204"
          },
          "substitution": null
        }
      ]
    }
  ]
}
```

### Hausaufgaben Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 12345,
          "subject": "Mathematik",
          "homework": "Aufgaben S. 45, Nr. 1-10",
          "date": "2025-09-16",
          "teacher": "Herr Schmidt",
          "completed": false,
          "createdAt": "2025-09-11T08:30:00.000Z"
        },
        {
          "id": 12346,
          "subject": "Deutsch",
          "homework": "Gedicht auswendig lernen",
          "date": "2025-09-17",
          "teacher": "Frau Müller",
          "completed": true,
          "createdAt": "2025-09-10T14:20:00.000Z"
        }
      ]
    }
  ]
}
```

### Klassenarbeiten Response
```json
{
  "results": [
    {
      "status": 200,
      "data": [
        {
          "id": 3163060,
          "subject": {
            "id": 255645,
            "name": "Deutsch",
            "abbreviation": "D"
          },
          "type": {
            "id": 2224,
            "name": "Klassenarbeit",
            "color": "#c6dcef",
            "visibleForStudents": true
          },
          "date": "2025-09-25",
          "startClassHour": {
            "id": 30172,
            "number": "5",
            "from": "11:41:00",
            "until": "12:26:00"
          },
          "comment": "",
          "createdAt": "2025-09-11T08:08:56.598Z",
          "updatedAt": "2025-09-11T08:08:56.598Z"
        }
      ]
    }
  ]
}
```

### Fehler-Response
```json
{
  "results": [
    {
      "status": 400,
      "error": "Invalid parameters"
    }
  ]
}
```

## 🚨 Häufige API-Probleme

### 1. Authentifizierung fehlgeschlagen (401)
- **Ursache**: Falscher Hash oder abgelaufener Token
- **Lösung**: Hash-Parameter überprüfen, Token erneuern

### 2. Schülerdaten nicht gefunden (400)
- **Ursache**: Falsche API-Methode oder fehlende Berechtigung
- **Lösung**: Schülerdaten aus Login-Response extrahieren

### 3. Salt-Abruf fehlgeschlagen
- **Ursache**: Fehlende Parameter oder falsche Email
- **Lösung**: `mobileApp: false` Parameter hinzufügen

### 4. Schedule/Letters API 400 Bad Request (GELÖST!)
- **Ursache**: Fehlender `bundleVersion` Parameter in API-Requests
- **Lösung**: `"bundleVersion": "3505280ee7"` zu allen API-Calls hinzufügen
- **bundleVersion Quelle**: Embedded in JavaScript bundle file (z.B. `main-SUJO2BNM.js`)
- **Dynamische Erkennung**: Integration erkennt bundleVersion automatisch durch:
  1. Abrufen der Haupt-HTML-Seite von `https://login.schulmanager-online.de`
  2. Extrahieren der JavaScript-Bundle-URLs aus dem HTML
  3. Suchen nach bundleVersion in den JavaScript-Dateien
  4. Caching der erkannten Version für 1 Stunde
- **Fallback**: Bei Erkennungsfehlern wird die bekannte Version `"3505280ee7"` verwendet
- **Symptome (vorher)**: 
  - Authentifizierung funktioniert perfekt
  - Homework und Exams APIs funktionieren (hatten bundleVersion in Standalone-Tests)
  - Schedule und Letters APIs gaben identische 400-Fehler zurück
  - Server-Response: Plain text "Bad Request" statt JSON
- **Status**: ✅ BEHOBEN + DYNAMISCHE ERKENNUNG IMPLEMENTIERT
- **Zusätzliche Fixes**:
  1. Response-Struktur von `"responses"` auf `"results"` geändert
  2. Alle API-Calls benötigen bundleVersion Parameter
  3. Standalone-Scripts benötigen korrekte Passwort-Credentials
  4. Dynamische bundleVersion-Erkennung implementiert

## 🔍 Reverse Engineering Erkenntnisse

### JavaScript-Dateien analysiert:
- **`chunk-M5BNGULW.js`**: Enthält Hash-Funktion `SWe`
- **`main-SUJO2BNM.js`**: Enthält Login-Logic

### Wichtige Erkenntnisse:
1. **Salt wird als String zurückgegeben**, nicht als JSON-Objekt
2. **Hash-Iterationen sind 99.999**, nicht 10.000
3. **Output-Länge ist 512 Bytes**, nicht 256
4. **Salt-Encoding ist UTF-8**, nicht Hex

## 📝 API-Versionierung

- **Bundle Version**: `3505280ee7` (aktuell)
- **API-Version**: Nicht explizit versioniert
- **Kompatibilität**: Rückwärtskompatibel

## 🔧 Implementierungs-Hinweise

1. **Session Management**: Verwende `aiohttp.ClientSession` für Connection Pooling
2. **Error Handling**: Implementiere Retry-Logic für temporäre Fehler
3. **Rate Limiting**: Beachte API-Limits (nicht dokumentiert)
4. **Caching**: Cache Schülerdaten aus Login-Response
5. **Logging**: Detailliertes Logging für Debugging

## 📚 Weiterführende Dokumentation

- [Authentication Guide](Authentication_Guide.md) - Detaillierte Authentifizierung
- [API Implementation](API_Implementation.md) - Python-Implementierung
- [Troubleshooting](Troubleshooting_Guide.md) - Problemlösungen
