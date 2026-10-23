"""API client for Schulmanager Online."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from .const import API_BASE_URL, CALLS_URL, LOGIN_URL, SALT_URL
from .bundle import BundleDetectionError, detect_bundle_version

_LOGGER = logging.getLogger(__name__)


class SchulmanagerAPIError(Exception):
    """Exception raised for API errors."""


class SchulmanagerAPI:
    """API client for Schulmanager Online."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.session = session
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.user_data: Dict[str, Any] = {}
        self.bundle_version: Optional[str] = None
        self.bundle_version_expires: Optional[datetime] = None
        self.bundle_version_source = "not_detected"
        self.last_successful_bundle_version: Optional[str] = None
        self._bundle_lock = asyncio.Lock()
        # Multi-school support
        self.institution_id: Optional[int] = None
        self.multiple_accounts: Optional[List[Dict[str, Any]]] = None

    async def authenticate(self, *, institution_id: Optional[int] = None) -> None:
        """Authenticate with the API. Pass institution_id to select a school when required."""
        try:
            # Get salt (pass institution_id for multi-school accounts)
            salt = await self._get_salt(institution_id=institution_id)
            
            # Generate salted hash
            salted_hash = self._generate_salted_hash(self.password, salt)
            
            # Login
            await self._login(salted_hash, institution_id=institution_id)
            
        except Exception as e:
            _LOGGER.error("Authentication failed: %s", e)
            raise SchulmanagerAPIError(f"Authentication failed: {e}") from e

    async def _get_salt(self, *, institution_id: Optional[int] = None) -> str:
        """Get salt for password hashing. Pass institution_id for multi-school accounts."""
        payload = {
            "emailOrUsername": self.email,
            "mobileApp": False,
            "institutionId": institution_id
        }
        
        _LOGGER.debug("🧂 Requesting salt from: %s", SALT_URL)
        
        async with self.session.post(SALT_URL, json=payload) as response:
            _LOGGER.debug("🧂 Salt response status: %d", response.status)
            
            if response.status != 200:
                _LOGGER.error("Salt request failed: HTTP %d", response.status)
                raise SchulmanagerAPIError(f"Failed to get salt: {response.status}")
            
            try:
                data = await response.json()
                # Handle both string response and object response
                if isinstance(data, str):
                    salt = data
                else:
                    salt = data.get("salt")
            except Exception as e:
                _LOGGER.debug("🧂 Salt response not JSON, trying as text: %s", e)
                # If JSON parsing fails, try text
                salt = await response.text()
            
            if not salt:
                _LOGGER.error("❌ No salt received in response")
                raise SchulmanagerAPIError("No salt received")
            
            _LOGGER.debug("✅ Salt received: %s characters", len(salt))
            return salt

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
            # Password als bytes (binary)
            password_bytes = password.encode('utf-8')
            
            # Salt als UTF-8 encodiert (WICHTIG: nicht hex!)
            salt_bytes = salt.encode('utf-8')
            
            # PBKDF2 mit SHA-512, 512 Bytes Output, 99999 Iterationen
            hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
            
            # Convert to hex (1024 characters)
            hash_hex = hash_bytes.hex()
            
            return hash_hex
            
        except Exception as e:
            raise SchulmanagerAPIError(f"Hash generation failed: {e}") from e

    async def _login(self, salted_hash: str, *, institution_id: Optional[int] = None) -> None:
        """Login with salted hash."""
        payload = {
            "emailOrUsername": self.email,
            "password": self.password,
            "hash": salted_hash,
            "mobileApp": False,
            "institutionId": institution_id,
        }
        
        async with self.session.post(LOGIN_URL, json=payload) as response:
            if response.status != 200:
                raise SchulmanagerAPIError(f"Login failed: {response.status}")
            
            data = await response.json()
            # Handle multi-school accounts first
            if isinstance(data, dict) and "multipleAccounts" in data:
                accounts = data.get("multipleAccounts") or []
                if isinstance(accounts, list) and accounts:
                    self.multiple_accounts = accounts  # [{ id, label }, ...]
                    self.token = None
                    self.user_data = {}
                    _LOGGER.info("Multi-school account detected with %d schools", len(accounts))
                    return
            
            self.token = data.get("jwt") or data.get("token")  # Try both jwt and token
            
            if not self.token:
                raise SchulmanagerAPIError("No token received (and no multipleAccounts)")
            
            # Store user data for later use
            self.user_data = data.get("user", {})
            
            # Set token expiration (1 hour from now)
            self.token_expires = datetime.now() + timedelta(hours=1)
            
            # Persist institution id if present in response and not passed explicitly
            if institution_id is not None:
                self.institution_id = institution_id
            else:
                try:
                    self.institution_id = int(self.user_data.get("institutionId")) if self.user_data.get("institutionId") is not None else None
                except Exception:
                    self.institution_id = None
            
            _LOGGER.debug("Login successful, token expires at %s", self.token_expires)

    def get_multiple_accounts(self) -> Optional[List[Dict[str, Any]]]:
        """Return multipleAccounts list if the account has multiple schools."""
        return self.multiple_accounts

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid token."""
        if not self.token or not self.token_expires:
            await self.authenticate(institution_id=self.institution_id)
            return
        
        # Check if token is about to expire (refresh 5 minutes early)
        if datetime.now() >= (self.token_expires - timedelta(minutes=5)):
            _LOGGER.debug("Token expiring soon, refreshing...")
            await self.authenticate(institution_id=self.institution_id)

    async def _detect_bundle_version(self) -> str:
        """Discover from the public app; raise on failure, never return a fallback."""
        return await detect_bundle_version(self.session, API_BASE_URL + "/")

    async def _ensure_bundle_version(self) -> str:
        """Cache discovery for one hour; retry failed discovery after five minutes.

        Keep the last API-confirmed version if discovery fails, otherwise retain
        the previous detected value or use the historical emergency fallback.
        The source field explicitly distinguishes all three cases. This cache is
        per API instance, in memory, and serialized to avoid duplicate discovery.
        """
        async with self._bundle_lock:
            if (self.bundle_version and self.bundle_version_expires and
                    datetime.now() < self.bundle_version_expires):
                return self.bundle_version
            try:
                version = await self._detect_bundle_version()
            except BundleDetectionError as err:
                version = self.last_successful_bundle_version or self.bundle_version or "3505280ee7"
                if self.last_successful_bundle_version:
                    self.bundle_version_source = "last_api_success"
                elif self.bundle_version:
                    self.bundle_version_source = "previous_detection"
                else:
                    self.bundle_version_source = "emergency_fallback"
                self.bundle_version_expires = datetime.now() + timedelta(minutes=5)
                _LOGGER.warning(
                    "bundleVersion discovery failed (%s); using %s, retry discovery in 5 minutes",
                    err, self.bundle_version_source,
                )
            else:
                self.bundle_version_source = "detected"
                self.bundle_version_expires = datetime.now() + timedelta(hours=1)
                _LOGGER.debug("Detected bundleVersion %s from public app", version)
            self.bundle_version = version
            return version

    @staticmethod
    def _response_statuses(data: Any) -> list:
        """Read only envelope status fields, never recurse through private API data."""
        if not isinstance(data, dict):
            return []
        return [item.get("status") for key in ("results", "responses")
                if isinstance(data.get(key), list)
                for item in data[key] if isinstance(item, dict)]

    @staticmethod
    def _version_conflict(data: Any) -> bool:
        """Accept an explicit bundle-version rejection, not an arbitrary 4xx."""
        if not isinstance(data, dict):
            return False
        envelopes = [data] + [item for key in ("results", "responses")
                              if isinstance(data.get(key), list)
                              for item in data[key] if isinstance(item, dict)]
        for envelope in envelopes:
            for key in ("code", "error", "message"):
                value = envelope.get(key)
                if not isinstance(value, str):
                    continue
                text = re.sub(r"[^a-z]", "", value.lower())
                if "bundleversion" in text and any(
                    word in text for word in ("invalid", "mismatch", "outdated", "expired", "unsupported")
                ):
                    return True
        return False

    async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call once, then retry at most once for auth or explicit version rejection.

        HTTP and nested 401/403 share one retry budget. Logs contain status/counts
        only: no authorization headers, student objects or server response bodies.
        """
        await self._ensure_authenticated()
        for attempt in range(2):
            version = await self._ensure_bundle_version()
            payload = {"bundleVersion": version, "requests": requests}
            headers = {"Authorization": f"Bearer {self.token}"}
            async with self.session.post(CALLS_URL, json=payload, headers=headers) as response:
                status = response.status
                try:
                    data = await response.json()
                except (ValueError, aiohttp.ContentTypeError) as err:
                    if status not in (401, 403):
                        raise SchulmanagerAPIError(f"API response is not JSON (HTTP {status})") from err
                    data = {}
            statuses = self._response_statuses(data)
            auth_rejected = status in (401, 403) or any(code in (401, 403) for code in statuses)
            version_rejected = self._version_conflict(data)
            _LOGGER.debug("API response HTTP %s, nested statuses %s", status, statuses)
            if (auth_rejected or version_rejected) and attempt == 0:
                _LOGGER.warning(
                    "API rejected %s; refreshing and retrying once",
                    "authentication" if auth_rejected else "bundleVersion",
                )
                # Keep last successful value available if public discovery is down.
                self.bundle_version_expires = None
                if auth_rejected:
                    self.token = None
                    self.token_expires = None
                    await self.authenticate(institution_id=self.institution_id)
                continue
            if status != 200 or auth_rejected or version_rejected:
                raise SchulmanagerAPIError(f"API request rejected (HTTP {status}, nested statuses {statuses})")
            if not isinstance(data, dict):
                raise SchulmanagerAPIError("API response is not an object")
            if statuses and all(code == 200 for code in statuses):
                self.last_successful_bundle_version = version
            return data
        raise SchulmanagerAPIError("API retry budget exhausted")

    async def get_students(self) -> List[Dict[str, Any]]:
        """Get list of students (children) from user data."""
        await self._ensure_authenticated()
        
        try:
            # Extract students from user data (from login response)
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
            
            # If no students found in user data, the account might not have student access
            if not students:
                _LOGGER.warning("No students found in user data. User data keys: %s", list(self.user_data.keys()))
                raise SchulmanagerAPIError("No students found for this account")
            
            _LOGGER.debug("Found %d students", len(students))
            return students
            
        except Exception as e:
            _LOGGER.error("Failed to get students: %s", e)
            raise SchulmanagerAPIError(f"Failed to get students: {e}") from e

    async def get_institution(self) -> Dict[str, Any]:
        """Get institution/school details including name, address, etc.
        
        Returns a dict with institution information:
        {
            "id": 13309,
            "name": "Moritz-Fontaine-Gesamtschule Rheda-Wiedenbrück",
            "street": "Fürst-Bentheim-Straße 55",
            "zipcode": "33378",
            "city": "Rheda-Wiedenbrück",
            "website": "www.mfg.nrw",
            "email": "sekretariat@gesamtschule-rh-wd.de",
            "phone": "...",
            "fax": "...",
            "region": "DE-NW",
            "schoolTypes": ["Gesamtschule"],
            "timeZone": "Europe/Berlin"
        }
        """
        await self._ensure_authenticated()
        
        try:
            _LOGGER.debug("Fetching institution details...")
            
            # Use the main/get-institution endpoint (most reliable)
            result = await self._make_api_call([{
                "moduleName": "main",
                "endpointName": "get-institution",
                "parameters": {}
            }])
            
            results = result.get("results", [])
            if not results:
                raise SchulmanagerAPIError("No results returned from get-institution endpoint")
            
            first_result = results[0]
            if not isinstance(first_result, dict):
                raise SchulmanagerAPIError(f"Unexpected result format: {type(first_result)}")
            
            # Check for successful status
            status = first_result.get("status", 0)
            if status != 200:
                raise SchulmanagerAPIError(f"get-institution returned status {status}")
            
            institution_data = first_result.get("data", {})
            if not institution_data:
                raise SchulmanagerAPIError("No institution data in response")
            
            _LOGGER.debug("✅ Institution details retrieved: %s (ID: %s)", 
                         institution_data.get("name"), 
                         institution_data.get("id"))
            
            return institution_data
            
        except SchulmanagerAPIError:
            raise
        except Exception as e:
            _LOGGER.error("Failed to get institution details: %s", e)
            raise SchulmanagerAPIError(f"Failed to get institution details: {e}") from e

    async def get_schedule(
        self, 
        student_id: int, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get schedule for a student."""
        
        # Get full student object (required for schedule API)
        students = await self.get_students()
        student = None
        for s in students:
            if s.get("id") == student_id:
                student = s
                break
        
        if not student:
            raise SchulmanagerAPIError(f"Student with ID {student_id} not found")
        
        requests = [
            {
                "moduleName": "schedules",
                "endpointName": "get-actual-lessons",
                "parameters": {
                    "student": student,  # Use full student object instead of just ID
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat()
                }
            }
        ]
        
        try:
            _LOGGER.debug("🗓️ Requesting schedule for student %d from %s to %s", 
                         student_id, start_date, end_date)
            
            response = await self._make_api_call(requests)
            results = response.get("results", [])

            _LOGGER.debug("Schedule API response - Got %d results", len(results))
            
            if not results:
                _LOGGER.error("❌ No schedule response received")
                raise SchulmanagerAPIError("No schedule response")
            
            schedule_data = results[0]
            status = schedule_data.get("status")
            
            _LOGGER.debug("Schedule API response status: %s", status)
            
            if status != 200:
                _LOGGER.error("❌ Schedule API returned status %s", status)
                raise SchulmanagerAPIError(f"Schedule API error: {status}")
            
            # Extract lessons from the data field
            data = schedule_data.get("data", [])
            lessons = data if isinstance(data, list) else schedule_data.get("lessons", [])
            
            _LOGGER.info("✅ Found %d lessons for student %d", len(lessons), student_id)
            
            # Return data in the format expected by the coordinator
            return {"lessons": lessons}
            
        except Exception as e:
            _LOGGER.error("❌ Failed to get schedule for student %d: %s", student_id, e)
            _LOGGER.debug("Schedule request details - Student: %d, Start: %s, End: %s", 
                         student_id, start_date, end_date)
            raise SchulmanagerAPIError(f"Failed to get schedule: {e}") from e

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
            responses = response.get("results", [])
            
            if not responses:
                raise SchulmanagerAPIError("No homework response")
            
            homework_data = responses[0]
            homeworks = homework_data.get("homeworks", homework_data.get("data", []))
            
            _LOGGER.debug("Found %d homework assignments for student %d", len(homeworks), student_id)
            
            return homework_data
            
        except Exception as e:
            _LOGGER.error("Failed to get homework for student %d: %s", student_id, e)
            raise SchulmanagerAPIError(f"Failed to get homework: {e}") from e

    async def get_homework_legacy(self, student_id: int) -> Dict[str, Any]:
        """Get homework using legacy method (fallback)."""
        requests = [
            {
                "method": "homeworks/get-homeworks",
                "data": {"studentId": student_id}
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            responses = response.get("results", [])
            
            if not responses:
                raise SchulmanagerAPIError("No homework response")
            
            return responses[0]
            
        except Exception as e:
            _LOGGER.error("Failed to get homework (legacy) for student %d: %s", student_id, e)
            raise SchulmanagerAPIError(f"Failed to get homework (legacy): {e}") from e

    async def get_grades(self, student_id: int) -> Dict[str, Any]:
        """Get grades for a student."""
        # NOTE: previously used the legacy {"method", "data"} request shape,
        # which the backend appears to have dropped (every other endpoint has
        # migrated to moduleName/endpointName/parameters). Aligned with the
        # same convention used by get_homework/get_exams; not yet verified
        # against a live account since grades is an opt-in feature.
        requests = [
            {
                "moduleName": "grades",
                "endpointName": "get-grades",
                "parameters": {"student": {"id": student_id}}
            }
        ]

        try:
            response = await self._make_api_call(requests)
            responses = response.get("results", [])

            if not responses:
                raise SchulmanagerAPIError("No grades response")

            grades_data = responses[0]
            grades = grades_data.get("grades", grades_data.get("data", []))
            
            _LOGGER.debug("Found %d grades for student %d", len(grades), student_id)
            
            return grades_data
            
        except Exception as e:
            _LOGGER.error("Failed to get grades for student %d: %s", student_id, e)
            raise SchulmanagerAPIError(f"Failed to get grades: {e}") from e

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
            responses = response.get("results", [])
            
            if not responses:
                raise SchulmanagerAPIError("No exams response")
            
            exams_data = responses[0]
            exams = exams_data.get("exams", exams_data.get("data", []))
            
            _LOGGER.debug("Found %d exams for student %d", len(exams), student_id)
            
            return exams_data
            
        except Exception as e:
            _LOGGER.error("Failed to get exams for student %d: %s", student_id, e)
            raise SchulmanagerAPIError(f"Failed to get exams: {e}") from e

    async def get_letters(self) -> Dict[str, Any]:
        """Get letters (Elternbriefe) for the user."""
        requests = [
            {
                "moduleName": None,
                "endpointName": "user-can-get-notifications"
            },
            {
                "moduleName": "letters",
                "endpointName": "get-letters"
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            results = response.get("results", [])
            
            if len(results) < 2:
                raise SchulmanagerAPIError("Incomplete letters response")
            
            letters_data = results[1]  # Second response is the letters
            
            if letters_data.get("status") != 200:
                raise SchulmanagerAPIError(f"Letters API error: {letters_data.get('status')}")
            
            _LOGGER.debug("Found %d letters", len(letters_data.get("data", [])))
            
            return letters_data
            
        except Exception as e:
            _LOGGER.error("Failed to get letters: %s", e)
            raise SchulmanagerAPIError(f"Failed to get letters: {e}") from e

    async def get_letter_details(self, letter_id: int, student_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific letter including attachments."""
        requests = [
            {
                "moduleName": "letters",
                "endpointName": "poqa",
                "parameters": {
                    "action": {
                        "model": "modules/letters/letter",
                        "action": "findByPk",
                        "parameters": [
                            letter_id,
                            {
                                "include": [
                                    {
                                        "association": "attachments",
                                        "required": False,
                                        "attributes": ["id", "filename", "file", "contentType", "inline", "letterId"]
                                    },
                                    {
                                        "association": "studentStatuses",
                                        "required": True,
                                        "where": {"studentId": {"$in": [student_id]}},
                                        "include": [{"association": "student", "required": True}]
                                    }
                                ]
                            }
                        ]
                    },
                    "uiState": "main.modules.letters.view.details"
                }
            },
            {
                "moduleName": "letters",
                "endpointName": "get-translation-languages"
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            results = response.get("results", [])
            
            if not results:
                raise SchulmanagerAPIError("No letter details response")
            
            letter_data = results[0]
            
            if letter_data.get("status") != 200:
                raise SchulmanagerAPIError(f"Letter details API error: {letter_data.get('status')}")
            
            _LOGGER.debug("Retrieved letter details for letter %d", letter_id)
            
            return letter_data
            
        except Exception as e:
            _LOGGER.error("Failed to get letter details for letter %d: %s", letter_id, e)
            raise SchulmanagerAPIError(f"Failed to get letter details: {e}") from e

    async def get_class_hours(self) -> List[Dict[str, Any]]:
        """Get class hours configuration."""
        requests = [
            {
                "moduleName": "schedules",
                "endpointName": "get-class-hours",
                "parameters": {}
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            results = response.get("results", [])
            
            if not results:
                raise SchulmanagerAPIError("No class hours response")
            
            class_hours_data = results[0]
            
            if class_hours_data.get("status") != 200:
                raise SchulmanagerAPIError(f"Class hours API error: {class_hours_data.get('status')}")
            
            class_hours = class_hours_data.get("data", [])
            _LOGGER.debug("Retrieved %d class hours", len(class_hours))
            
            return class_hours
            
        except Exception as e:
            _LOGGER.error("Failed to get class hours: %s", e)
            raise SchulmanagerAPIError(f"Failed to get class hours: {e}") from e

    async def refresh_token(self) -> None:
        """Refresh the authentication token."""
        await self.authenticate(institution_id=self.institution_id)
