# API Implementation - Python Client

## 🎯 Overview

The `SchulmanagerAPI` class is the central Python client for communication with the Schulmanager Online API. It implements all necessary functions for authentication, data retrieval, and session management.

## 🏗️ Class Architecture

### SchulmanagerAPI Class

```python
class SchulmanagerAPI:
    """API client for Schulmanager Online."""
    
    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        self.email = email
        self.password = password
        self.session = session
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.user_data: Dict[str, Any] = {}
```

### Important Attributes

| Attribute | Type | Description |
|----------|-----|--------------|
| `email` | `str` | User email or username |
| `password` | `str` | Original password (not hashed) |
| `session` | `aiohttp.ClientSession` | HTTP session for requests |
| `token` | `Optional[str]` | JWT token for API calls |
| `token_expires` | `Optional[datetime]` | Token expiration time |
| `user_data` | `Dict[str, Any]` | User data from login response |

## 🔐 Authentication Methods

### 1. Main Authentication

```python
async def authenticate(self) -> None:
    """Authenticate with the API."""
    try:
        # Step 1: Get salt
        salt = await self._get_salt()
        
        # Step 2: Generate hash
        salted_hash = self._generate_salted_hash(self.password, salt)
        
        # Step 3: Login with hash
        await self._login(salted_hash)
        
    except Exception as e:
        _LOGGER.error("Authentication failed: %s", e)
        raise SchulmanagerAPIError(f"Authentication failed: {e}") from e
```

### 2. Salt Retrieval

```python
async def _get_salt(self) -> str:
    """Get salt for password hashing."""
    payload = {
        "emailOrUsername": self.email,
        "mobileApp": False,  # Important for web clients
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
        
        _LOGGER.debug("Salt received: %s characters", len(salt))
        return salt
```

### 3. Hash Generation

```python
def _generate_salted_hash(self, password: str, salt: str) -> str:
    """Generate salted hash using PBKDF2-SHA512"""
    try:
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')  # UTF-8, not Hex!
        
        # PBKDF2-SHA512 with 99999 iterations, 512 bytes output
        hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
        
        # Convert to hex (1024 characters)
        hash_hex = hash_bytes.hex()
        
        return hash_hex
        
    except Exception as e:
        raise SchulmanagerAPIError(f"Hash generation failed: {e}") from e
```

### 4. Login

```python
async def _login(self, salted_hash: str) -> None:
    """Login with salted hash."""
    payload = {
        "emailOrUsername": self.email,
        "password": self.password,
        "hash": salted_hash,
        "mobileApp": False,
        "institutionId": None
    }
    
    async with self.session.post(LOGIN_URL, json=payload) as response:
        if response.status != 200:
            raise SchulmanagerAPIError(f"Login failed: {response.status}")
        
        data = await response.json()
        self.token = data.get("jwt") or data.get("token")  # Check both variants
        
        if not self.token:
            raise SchulmanagerAPIError("No token received")
        
        # Store user data for student extraction
        self.user_data = data.get("user", {})
        
        # Set token expiration (1 hour from now)
        self.token_expires = datetime.now() + timedelta(hours=1)
        
        _LOGGER.debug("Login successful, token expires at %s", self.token_expires)
```

## 📊 Data Retrieval Methods

### 1. Get Students

```python
async def get_students(self) -> List[Dict[str, Any]]:
    """Get list of students (children) from user data."""
    await self._ensure_authenticated()
    
    try:
        students = []
        
        # Check for associated parents (parent account)
        associated_parents = self.user_data.get("associatedParents", [])
        for parent in associated_parents:
            student = parent.get("student")
            if student:
                students.append(student)
        
        # Check for associated student (student account)
        associated_student = self.user_data.get("associatedStudent")
        if associated_student:
            students.append(associated_student)
        
        if not students:
            _LOGGER.warning("No students found in user data. User data keys: %s", 
                          list(self.user_data.keys()))
            raise SchulmanagerAPIError("No students found for this account")
        
        _LOGGER.debug("Found %d students", len(students))
        return students
        
    except Exception as e:
        _LOGGER.error("Failed to get students: %s", e)
        raise SchulmanagerAPIError(f"Failed to get students: {e}") from e
```

### 2. Get Schedule

```python
async def get_schedule(
    self, 
    student_id: int, 
    start_date: datetime.date, 
    end_date: datetime.date
) -> Dict[str, Any]:
    """Get schedule for a student."""
    requests = [
        {
            "method": "schedules/get-actual-lessons",
            "data": {
                "studentId": student_id,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        results = response.get("results", [])  # CHANGED: "results" instead of "responses"
        
        if not results:
            raise SchulmanagerAPIError("No schedule response")
        
        schedule_data = results[0]
        
        if schedule_data.get("status") != 200:
            raise SchulmanagerAPIError(f"Schedule request failed: {schedule_data.get('status')}")
        
        return schedule_data.get("data", [])
        
    except Exception as e:
        _LOGGER.error("Failed to get schedule: %s", e)
        raise SchulmanagerAPIError(f"Failed to get schedule: {e}") from e
```

### 3. Get Homework

```python
async def get_homework(self, student_id: int) -> Dict[str, Any]:
    """Get homework for a student using the classbook module."""
    requests = [
        {
            "moduleName": "classbook",
            "endpointName": "get-homework",
            "parameters": {"student": {"id": student_id}}
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        responses = response.get("responses", [])
        
        if not responses:
            raise SchulmanagerAPIError("No homework response")
        
        homework_data = responses[0]
        
        if homework_data.get("status") != 200:
            raise SchulmanagerAPIError(f"Homework request failed: {homework_data.get('status')}")
        
        # Extract homework data - can be direct list or nested
        homeworks = homework_data.get("homeworks", homework_data.get("data", []))
        
        _LOGGER.debug("Found %d homework assignments for student %d", len(homeworks), student_id)
        
        return homework_data
        
    except Exception as e:
        _LOGGER.error("Failed to get homework for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get homework: {e}") from e
```

### 4. Get Exams

```python
async def get_exams(self, student_id: int, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """Get exams/tests for a student in a date range."""
    requests = [
        {
            "moduleName": "exams",
            "endpointName": "get-exams",
            "parameters": {
                "student": {"id": student_id},
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        responses = response.get("responses", [])
        
        if not responses:
            raise SchulmanagerAPIError("No exams response")
        
        exams_data = responses[0]
        
        if exams_data.get("status") != 200:
            raise SchulmanagerAPIError(f"Exams request failed: {exams_data.get('status')}")
        
        exams = exams_data.get("exams", exams_data.get("data", []))
        
        _LOGGER.debug("Found %d exams for student %d", len(exams), student_id)
        
        return exams_data
        
    except Exception as e:
        _LOGGER.error("Failed to get exams for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get exams: {e}") from e
```

### 5. Get Grades (Experimental)

```python
async def get_grades(self, student_id: int) -> Dict[str, Any]:
    """Get grades for a student (experimental feature)."""
    requests = [
        {
            "moduleName": "grades",
            "endpointName": "get-grades",
            "parameters": {"student": {"id": student_id}}
        }
    ]
    
    try:
        response = await self._make_api_call(requests)
        responses = response.get("responses", [])
        
        if not responses:
            raise SchulmanagerAPIError("No grades response")
        
        grades_data = responses[0]
        
        if grades_data.get("status") != 200:
            raise SchulmanagerAPIError(f"Grades request failed: {grades_data.get('status')}")
        
        grades = grades_data.get("grades", grades_data.get("data", []))
        
        _LOGGER.debug("Found %d grades for student %d", len(grades), student_id)
        
        return grades_data
        
    except Exception as e:
        _LOGGER.error("Failed to get grades for student %d: %s", student_id, e)
        raise SchulmanagerAPIError(f"Failed to get grades: {e}") from e
```

### 3. Generic API Calls

```python
async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Make a generic API call."""
    await self._ensure_authenticated()
    
    payload = {
        "bundleVersion": "3505280ee7",  # CRITICAL: Required for all API calls!
        "requests": requests
    }
    
    headers = {
        "Authorization": f"Bearer {self.token}",
        "Content-Type": "application/json"
    }
    
    async with self.session.post(API_URL, json=payload, headers=headers) as response:
        if response.status == 401:
            # Token expired, try to re-authenticate
            await self.authenticate()
            headers["Authorization"] = f"Bearer {self.token}"
            
            # Retry the request
            async with self.session.post(API_URL, json=payload, headers=headers) as retry_response:
                if retry_response.status != 200:
                    raise SchulmanagerAPIError(f"API call failed after retry: {retry_response.status}")
                return await retry_response.json()
                
        elif response.status != 200:
            raise SchulmanagerAPIError(f"API call failed: {response.status}")
        
        return await response.json()
```

## 🔄 Session Management

### Token Validation

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

### Session Configuration

```python
# Recommended aiohttp.ClientSession configuration
timeout = aiohttp.ClientTimeout(total=30)
connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)

session = aiohttp.ClientSession(
    timeout=timeout,
    connector=connector,
    headers={
        "User-Agent": "SchulmanagerOnline-HA-Integration/1.0"
    }
)
```

## 🚨 Error Handling

### Custom Exception

```python
class SchulmanagerAPIError(Exception):
    """Exception raised for API errors."""
    pass
```

### Error Categories

| Error Type | HTTP Status | Description | Handling |
|-----------|-------------|-------------|----------|
| **Authentication** | 401 | Token invalid/expired | Automatic re-authentication |
| **Authorization** | 403 | No permission | Forward error to user |
| **Bad Request** | 400 | Invalid parameters | Validate parameters |
| **Not Found** | 404 | Endpoint not found | Check API version |
| **Server Error** | 500+ | Server problem | Retry with backoff |

### Retry Logic

```python
async def _make_api_call_with_retry(self, requests: List[Dict[str, Any]], max_retries: int = 3) -> Dict[str, Any]:
    """Make API call with retry logic."""
    for attempt in range(max_retries):
        try:
            return await self._make_api_call(requests)
        except SchulmanagerAPIError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            wait_time = 2 ** attempt
            _LOGGER.warning("API call failed (attempt %d/%d), retrying in %ds: %s", 
                          attempt + 1, max_retries, wait_time, e)
            await asyncio.sleep(wait_time)
```

## 📝 Logging

### Logger Configuration

```python
import logging

_LOGGER = logging.getLogger(__name__)

# In Home Assistant automatically configured
# For standalone tests:
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Debug Output

```python
# Important debug information
_LOGGER.debug("Salt received: %s characters", len(salt))
_LOGGER.debug("Hash generated: %s characters", len(hash_hex))
_LOGGER.debug("Login successful, token expires at %s", self.token_expires)
_LOGGER.debug("Found %d students", len(students))

# Error logging
_LOGGER.error("Authentication failed: %s", e)
_LOGGER.warning("No students found in user data. User data keys: %s", list(self.user_data.keys()))
```

## 🧪 Testing

### Unit Tests

```python
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch

class TestSchulmanagerAPI:
    
    @pytest.fixture
    async def api_client(self):
        session = aiohttp.ClientSession()
        client = SchulmanagerAPI("test@example.com", "password", session)
        yield client
        await session.close()
    
    @patch('custom_components.schulmanager_online.api.SchulmanagerAPI._get_salt')
    async def test_authenticate_success(self, mock_get_salt, api_client):
        mock_get_salt.return_value = "test_salt"
        
        with patch.object(api_client, '_login') as mock_login:
            await api_client.authenticate()
            mock_login.assert_called_once()
    
    async def test_hash_generation(self, api_client):
        hash_result = api_client._generate_salted_hash("password", "salt")
        assert len(hash_result) == 1024
        assert isinstance(hash_result, str)
```

### Integration Tests

```python
async def test_full_api_flow():
    """Test complete API flow with real credentials."""
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI("test@example.com", "password", session)
        
        # Test authentication
        await api.authenticate()
        assert api.token is not None
        
        # Test student data
        students = await api.get_students()
        assert len(students) > 0
        
        # Test schedule data
        student_id = students[0]["id"]
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=7)
        
        schedule = await api.get_schedule(student_id, start_date, end_date)
        assert isinstance(schedule, list)
```

## 📚 Usage in Home Assistant

### Integration in Coordinator

```python
from .api import SchulmanagerAPI

class SchulmanagerOnlineDataUpdateCoordinator(DataUpdateCoordinator):
    
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        
        self.session = async_get_clientsession(hass)
        self.api = SchulmanagerAPI(email, password, self.session)
    
    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            students = await self.api.get_students()
            # Process students and fetch schedules...
            return processed_data
        except SchulmanagerAPIError as e:
            raise UpdateFailed(f"Error communicating with API: {e}")
```

## 🔧 Configuration

### Constants

```python
# API URLs
SALT_URL = "https://login.schulmanager-online.de/api/salt"
LOGIN_URL = "https://login.schulmanager-online.de/api/login"
API_URL = "https://login.schulmanager-online.de/api/calls"

# Timeouts
DEFAULT_TIMEOUT = 30
TOKEN_REFRESH_BUFFER = timedelta(minutes=5)

# Bundle Version (should be updated regularly)
BUNDLE_VERSION = "3505280ee7"
```

### Environment Variables

```python
import os

# For tests
TEST_EMAIL = os.getenv("SCHULMANAGER_EMAIL")
TEST_PASSWORD = os.getenv("SCHULMANAGER_PASSWORD")

# Debug mode
DEBUG_API = os.getenv("DEBUG_SCHULMANAGER_API", "false").lower() == "true"
```

## 📚 Further Documentation

- [Authentication Guide](Authentication_Guide.md) - Detailed authentication
- [Integration Architecture](Integration_Architecture.md) - Home Assistant integration
- [Troubleshooting](Troubleshooting_Guide.md) - Problem solutions
