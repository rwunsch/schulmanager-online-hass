#!/usr/bin/env python3
"""
Standalone Schulmanager Online API Client

This is a simplified, standalone version of the API client without Home Assistant dependencies.
Used by the schedule table generator script.
"""

import asyncio
import base64
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

# API URLs
API_BASE_URL = "https://login.schulmanager-online.de"
SALT_URL = f"{API_BASE_URL}/api/get-salt"
LOGIN_URL = f"{API_BASE_URL}/api/login"
CALLS_URL = f"{API_BASE_URL}/api/calls"

_LOGGER = logging.getLogger(__name__)


class SchulmanagerAPIError(Exception):
    """Exception raised for API errors."""


class StandaloneSchulmanagerAPI:
    """Standalone API client for Schulmanager Online."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.session = session
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.user_data: Dict[str, Any] = {}
        self.bundle_version: str = "3505280ee7"  # Known working version

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
            raise SchulmanagerAPIError(f"Authentication failed: {e}") from e

    async def _get_salt(self) -> str:
        """Get salt for password hashing."""
        payload = {
            "emailOrUsername": self.email,
            "mobileApp": False,
            "institutionId": None
        }
        
        async with self.session.post(SALT_URL, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise SchulmanagerAPIError(f"Failed to get salt: {response.status} - {error_text}")
            
            try:
                data = await response.json()
                # Handle both string response and object response
                if isinstance(data, str):
                    salt = data
                else:
                    salt = data.get("salt")
            except Exception:
                # If JSON parsing fails, try text
                salt = await response.text()
            
            if not salt:
                raise SchulmanagerAPIError("No salt received")
            
            return salt

    def _generate_salted_hash(self, password: str, salt: str) -> str:
        """Generate salted hash using PBKDF2-SHA512."""
        try:
            # Password as bytes
            password_bytes = password.encode('utf-8')
            
            # Salt as UTF-8 encoded (IMPORTANT: not hex!)
            salt_bytes = salt.encode('utf-8')
            
            # PBKDF2 with SHA-512, 512 bytes output, 99999 iterations
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
                error_text = await response.text()
                raise SchulmanagerAPIError(f"Login failed: {response.status} - {error_text}")
            
            data = await response.json()
            self.token = data.get("jwt") or data.get("token")
            
            if not self.token:
                raise SchulmanagerAPIError("No token received")
            
            # Store user data for later use
            self.user_data = data.get("user", {})
            
            # Set token expiration (1 hour from now)
            self.token_expires = datetime.now() + timedelta(hours=1)

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid token."""
        if not self.token or not self.token_expires:
            await self.authenticate()
            return
        
        # Check if token is about to expire (refresh 5 minutes early)
        if datetime.now() >= (self.token_expires - timedelta(minutes=5)):
            await self.authenticate()

    async def _make_api_call(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make an authenticated API call."""
        await self._ensure_authenticated()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "bundleVersion": self.bundle_version,
            "requests": requests
        }
        
        async with self.session.post(CALLS_URL, json=payload, headers=headers) as response:
            if response.status == 401:
                # Token might be invalid, try to re-authenticate once
                await self.authenticate()
                headers = {"Authorization": f"Bearer {self.token}"}
                
                async with self.session.post(CALLS_URL, json=payload, headers=headers) as retry_response:
                    if retry_response.status != 200:
                        retry_text = await retry_response.text()
                        raise SchulmanagerAPIError(f"API call failed after retry: {retry_response.status} - {retry_text}")
                    
                    return await retry_response.json()
            
            elif response.status != 200:
                response_text = await response.text()
                raise SchulmanagerAPIError(f"API call failed: {response.status} - {response_text}")
            
            return await response.json()

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
            
            if not students:
                raise SchulmanagerAPIError("No students found for this account")
            
            return students
            
        except Exception as e:
            raise SchulmanagerAPIError(f"Failed to get students: {e}") from e

    async def get_schedule(
        self, 
        student_id: int, 
        start_date, 
        end_date
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
        
        # Convert date objects to ISO format strings
        if hasattr(start_date, 'isoformat'):
            start_date = start_date.isoformat()
        if hasattr(end_date, 'isoformat'):
            end_date = end_date.isoformat()
        
        requests = [
            {
                "moduleName": "schedules",
                "endpointName": "get-actual-lessons",
                "parameters": {
                    "student": student,  # Use full student object
                    "start": start_date,
                    "end": end_date
                }
            }
        ]
        
        try:
            response = await self._make_api_call(requests)
            results = response.get("results", [])
            
            if not results:
                raise SchulmanagerAPIError("No schedule response")
            
            schedule_data = results[0]
            status = schedule_data.get("status")
            
            if status != 200:
                raise SchulmanagerAPIError(f"Schedule API error: {status}")
            
            # Extract lessons from the data field
            data = schedule_data.get("data", [])
            lessons = data if isinstance(data, list) else []
            
            # Return data in the expected format
            return {"lessons": lessons}
            
        except Exception as e:
            raise SchulmanagerAPIError(f"Failed to get schedule: {e}") from e
