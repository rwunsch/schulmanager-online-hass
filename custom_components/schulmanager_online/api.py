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

    async def authenticate(self) -> None:
        """Authenticate with the API."""
        try:
            # Get salt
            salt = await self._get_salt()
            
            # Generate salted hash
            salted_hash = self._generate_salted_hash(self.password, salt)
            
            # Login
            await self._login(salted_hash)
            
        except Exception as e:
            _LOGGER.error("Authentication failed: %s", e)
            raise SchulmanagerAPIError(f"Authentication failed: {e}") from e

    async def _get_salt(self) -> str:
        """Get salt for password hashing."""
        payload = {
            "emailOrUsername": self.email,
            "mobileApp": False,
            "institutionId": None
        }
        
        _LOGGER.debug("🧂 Requesting salt from: %s", SALT_URL)
        _LOGGER.debug("🧂 Salt request payload: %s", payload)
        
        async with self.session.post(SALT_URL, json=payload) as response:
            _LOGGER.debug("🧂 Salt response status: %d", response.status)
            
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.error("❌ Salt request failed: %d - %s", response.status, error_text)
                raise SchulmanagerAPIError(f"Failed to get salt: {response.status}")
            
            try:
                data = await response.json()
                _LOGGER.debug("🧂 Salt response JSON: %s", data)
                # Handle both string response and object response
                if isinstance(data, str):
                    salt = data
                else:
                    salt = data.get("salt")
            except Exception as e:
                _LOGGER.debug("🧂 Salt response not JSON, trying as text: %s", e)
                # If JSON parsing fails, try text
                salt = await response.text()
                _LOGGER.debug("🧂 Salt response text: %s", salt[:50] + "..." if len(salt) > 50 else salt)
            
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
            self.token = data.get("jwt") or data.get("token")  # Try both jwt and token
            
            if not self.token:
                raise SchulmanagerAPIError("No token received")
            
            # Store user data for later use
            self.user_data = data.get("user", {})
            
            # Set token expiration (1 hour from now)
            self.token_expires = datetime.now() + timedelta(hours=1)
            
            _LOGGER.debug("Login successful, token expires at %s", self.token_expires)

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid token."""
        if not self.token or not self.token_expires:
            await self.authenticate()
            return
        
        # Check if token is about to expire (refresh 5 minutes early)
        if datetime.now() >= (self.token_expires - timedelta(minutes=5)):
            _LOGGER.debug("Token expiring soon, refreshing...")
            await self.authenticate()

    async def _detect_bundle_version(self) -> str:
        """
        Detect the current bundleVersion from Schulmanager Online JavaScript files.
        
        The bundleVersion is embedded in the main JavaScript bundle and is required
        for all API calls to work properly. This method fetches the main page,
        extracts JavaScript bundle URLs, and searches for the bundleVersion.
        
        Returns:
            str: The detected bundleVersion (e.g., "3505280ee7")
            
        Raises:
            SchulmanagerAPIError: If bundleVersion cannot be detected
        """
        try:
            _LOGGER.debug("🔍 Detecting bundleVersion from JavaScript files...")
            
            # Step 1: Get the main page to find JavaScript bundle URLs
            async with self.session.get(API_BASE_URL) as response:
                if response.status != 200:
                    _LOGGER.warning("Failed to fetch main page for bundleVersion detection: %d", response.status)
                    raise SchulmanagerAPIError(f"Failed to fetch main page: {response.status}")
                
                html_content = await response.text()
                _LOGGER.debug("✅ Main page fetched (%d characters)", len(html_content))
            
            # Step 2: Extract JavaScript bundle URLs from HTML
            js_urls = self._extract_js_urls(html_content)
            _LOGGER.debug("📋 Found %d JavaScript files", len(js_urls))
            
            # Step 3: Search for bundleVersion in JavaScript files
            for js_url in js_urls:
                # Convert relative URLs to absolute
                if js_url.startswith('/'):
                    full_url = f"{API_BASE_URL}{js_url}"
                elif js_url.startswith('http'):
                    full_url = js_url
                else:
                    # Handle relative URLs like "static/main-SUJO2BNM.js"
                    full_url = f"{API_BASE_URL}/{js_url}"
                
                bundle_version = await self._search_bundle_version_in_js(full_url)
                if bundle_version:
                    _LOGGER.info("✅ Detected bundleVersion: %s from %s", bundle_version, js_url)
                    return bundle_version
            
            # Fallback: Try the known main JavaScript file directly
            known_js_patterns = [
                "/static/main-*.js",
                "/assets/main-*.js",
                "/js/main-*.js"
            ]
            
            for pattern in known_js_patterns:
                # Try to find files matching the pattern in the HTML
                pattern_regex = pattern.replace("*", r"[A-Za-z0-9]+")
                matches = re.findall(f'["\']({pattern_regex})["\']', html_content)
                for match in matches:
                    full_url = f"{API_BASE_URL}{match}"
                    bundle_version = await self._search_bundle_version_in_js(full_url)
                    if bundle_version:
                        _LOGGER.info("✅ Detected bundleVersion: %s from pattern %s", bundle_version, pattern)
                        return bundle_version
            
            # If all else fails, return the known working version as fallback
            fallback_version = "3505280ee7"
            _LOGGER.warning("⚠️  Could not detect bundleVersion, using fallback: %s", fallback_version)
            return fallback_version
            
        except Exception as e:
            # If detection fails, use fallback version
            fallback_version = "3505280ee7"
            _LOGGER.warning("❌ bundleVersion detection failed (%s), using fallback: %s", e, fallback_version)
            return fallback_version

    def _extract_js_urls(self, html_content: str) -> List[str]:
        """Extract JavaScript file URLs from HTML content."""
        js_urls = []
        
        # Look for script tags with src attributes
        script_pattern = r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\'][^>]*>'
        matches = re.findall(script_pattern, html_content, re.IGNORECASE)
        js_urls.extend(matches)
        
        # Look for module imports
        module_pattern = r'import\(["\']([^"\']+\.js[^"\']*)["\']'
        module_matches = re.findall(module_pattern, html_content)
        js_urls.extend(module_matches)
        
        # Look for asset references
        asset_pattern = r'["\']([/][^"\']*main[^"\']*\.js[^"\']*)["\']'
        asset_matches = re.findall(asset_pattern, html_content)
        js_urls.extend(asset_matches)
        
        # Remove duplicates and filter
        unique_urls = list(set(js_urls))
        _LOGGER.debug("📋 Extracted JS URLs: %s", unique_urls)
        
        return unique_urls

    async def _search_bundle_version_in_js(self, js_url: str) -> Optional[str]:
        """Search for bundleVersion in a JavaScript file."""
        try:
            _LOGGER.debug("🔍 Checking %s for bundleVersion...", js_url)
            
            async with self.session.get(js_url) as response:
                if response.status != 200:
                    _LOGGER.debug("❌ Failed to fetch %s: %d", js_url, response.status)
                    return None
                
                js_content = await response.text()
                _LOGGER.debug("📄 File size: %d characters", len(js_content))
                
                # Search for bundleVersion patterns
                patterns = [
                    r'bundleVersion["\']?\s*[:=]\s*["\']([a-f0-9]{8,})["\']',  # bundleVersion: "hash"
                    r'["\']bundleVersion["\']?\s*[:=]\s*["\']([a-f0-9]{8,})["\']',  # "bundleVersion": "hash"
                    r'bundleVersion\s*=\s*["\']([a-f0-9]{8,})["\']',  # bundleVersion = "hash"
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if self._validate_bundle_version(js_content, match):
                            _LOGGER.debug("✅ Found valid bundleVersion: %s", match)
                            return match
                
                # Fallback: Look for the known version pattern
                known_version = "3505280ee7"
                if known_version in js_content:
                    _LOGGER.debug("✅ Found known bundleVersion: %s", known_version)
                    return known_version
                
                # Look for any hex string that might be a bundle version
                hex_pattern = r'["\']([a-f0-9]{10})["\']'
                hex_matches = re.findall(hex_pattern, js_content, re.IGNORECASE)
                for match in hex_matches:
                    if self._validate_bundle_version(js_content, match):
                        _LOGGER.debug("✅ Found candidate bundleVersion: %s", match)
                        return match
                
                return None
                
        except Exception as e:
            _LOGGER.debug("❌ Error processing %s: %s", js_url, e)
            return None

    def _validate_bundle_version(self, js_content: str, candidate: str) -> bool:
        """Validate that the candidate appears in API-related context."""
        # Check if the candidate appears near API-related terms
        context_terms = [
            'api/calls',
            'requests',
            'httpClient',
            'post',
            'axios',
            'fetch',
            '/api/',
            'bundleVersion'
        ]
        
        # Find the position of the candidate
        candidate_pos = js_content.find(candidate)
        if candidate_pos == -1:
            return False
        
        # Check surrounding context (1000 chars before and after)
        start = max(0, candidate_pos - 1000)
        end = min(len(js_content), candidate_pos + 1000)
        context = js_content[start:end].lower()
        
        # Check if any API-related terms appear in context
        for term in context_terms:
            if term in context:
                _LOGGER.debug("✅ Validated bundleVersion %s: found '%s' in context", candidate, term)
                return True
        
        return False

    async def _ensure_bundle_version(self) -> str:
        """Ensure we have a valid bundleVersion, detecting it if necessary."""
        # Check if we have a cached version that's still valid (cache for 1 hour)
        if (self.bundle_version and self.bundle_version_expires and 
            datetime.now() < self.bundle_version_expires):
            return self.bundle_version
        
        # Detect new bundleVersion
        _LOGGER.debug("🔄 Detecting/refreshing bundleVersion...")
        self.bundle_version = await self._detect_bundle_version()
        self.bundle_version_expires = datetime.now() + timedelta(hours=1)
        
        return self.bundle_version

    async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make an authenticated API call with detailed logging."""
        await self._ensure_authenticated()
        
        # Get current bundleVersion (detect dynamically if needed)
        bundle_version = await self._ensure_bundle_version()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "bundleVersion": bundle_version,  # Dynamically detected bundleVersion
            "requests": requests
        }
        
        # Enhanced debug logging
        _LOGGER.debug("🌐 Making API call to: %s", CALLS_URL)
        _LOGGER.debug("📤 Request payload: %s", payload)
        _LOGGER.debug("📋 Request headers: %s", {k: v[:20] + "..." if k == "Authorization" else v for k, v in headers.items()})
        
        async with self.session.post(CALLS_URL, json=payload, headers=headers) as response:
            _LOGGER.debug("📥 Response status: %d", response.status)
            _LOGGER.debug("📋 Response headers: %s", dict(response.headers))
            
            # Get response text for detailed error analysis
            response_text = await response.text()
            _LOGGER.debug("📄 Response body (first 500 chars): %s", response_text[:500])
            
            if response.status == 401:
                # Token might be invalid, try to re-authenticate once
                _LOGGER.debug("🔄 Got 401, trying to re-authenticate...")
                await self.authenticate()
                headers = {"Authorization": f"Bearer {self.token}"}
                
                _LOGGER.debug("🔄 Retrying API call with new token...")
                async with self.session.post(CALLS_URL, json=payload, headers=headers) as retry_response:
                    retry_text = await retry_response.text()
                    _LOGGER.debug("🔄 Retry response status: %d", retry_response.status)
                    _LOGGER.debug("🔄 Retry response body: %s", retry_text[:500])
                    
                    if retry_response.status != 200:
                        _LOGGER.error("❌ API call failed after retry: %d - %s", retry_response.status, retry_text)
                        raise SchulmanagerAPIError(f"API call failed after retry: {retry_response.status}")
                    
                    try:
                        return await retry_response.json()
                    except Exception as e:
                        _LOGGER.error("❌ Failed to parse retry response JSON: %s", e)
                        raise SchulmanagerAPIError(f"Invalid JSON in retry response: {e}")
            
            elif response.status != 200:
                _LOGGER.error("❌ API call failed: %d - %s", response.status, response_text)
                
                # Try to parse error response for more details
                try:
                    error_data = await response.json()
                    _LOGGER.error("❌ Error response JSON: %s", error_data)
                except:
                    _LOGGER.error("❌ Error response is not JSON: %s", response_text)
                
                raise SchulmanagerAPIError(f"API call failed: {response.status}")
            
            # Parse successful response
            try:
                response_data = await response.json()
                _LOGGER.debug("✅ Successfully parsed response JSON")
                _LOGGER.debug("📊 Response structure: %s", list(response_data.keys()) if isinstance(response_data, dict) else type(response_data))
                
                # Log details about responses array
                if isinstance(response_data, dict) and "responses" in response_data:
                    responses = response_data["responses"]
                    _LOGGER.debug("📊 Found %d responses in response array", len(responses))
                    for i, resp in enumerate(responses):
                        if isinstance(resp, dict):
                            status = resp.get("status", "unknown")
                            data_type = type(resp.get("data", None))
                            data_len = len(resp.get("data", [])) if isinstance(resp.get("data"), (list, dict)) else "N/A"
                            _LOGGER.debug("📊 Response %d: status=%s, data_type=%s, data_len=%s", i, status, data_type, data_len)
                            
                            if status != 200:
                                _LOGGER.error("❌ Response %d failed with status %s: %s", i, status, resp)
                
                return response_data
                
            except Exception as e:
                _LOGGER.error("❌ Failed to parse response JSON: %s", e)
                _LOGGER.error("❌ Raw response text: %s", response_text)
                raise SchulmanagerAPIError(f"Invalid JSON in response: {e}")

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
                    "end": end_date.isoformat()
                }
            }
        ]
        
        try:
            _LOGGER.debug("🗓️ Requesting schedule for student %d from %s to %s", 
                         student_id, start_date, end_date)
            _LOGGER.debug("Schedule request payload: %s", requests)
            
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
                _LOGGER.debug("Full schedule response: %s", schedule_data)
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

    async def get_class_hours(self, class_id: int) -> Dict[str, Any]:
        """Get class hours definition."""
        requests = [
            {
                "method": "schedules/get-class-hours",
                "data": {"classId": class_id}
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            responses = response.get("results", [])
            
            if not responses:
                raise SchulmanagerAPIError("No class hours response")
            
            return responses[0]
            
        except Exception as e:
            _LOGGER.error("Failed to get class hours for class %d: %s", class_id, e)
            raise SchulmanagerAPIError(f"Failed to get class hours: {e}") from e

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
        requests = [
            {
                "method": "grades/get-grades",
                "data": {"studentId": student_id}
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            responses = response.get("results", [])
            
            if not responses:
                raise SchulmanagerAPIError("No grades response")
            
            grades_data = responses[0]
            grades = grades_data.get("grades", [])
            
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
        await self.authenticate()
