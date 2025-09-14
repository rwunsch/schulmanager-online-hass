#!/usr/bin/env python3
"""Test script for Schulmanager Online Letters API."""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta


class SimpleSchulmanagerAPI:
    """Simplified API client for testing letters functionality."""
    
    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        self.email = email
        self.password = password
        self.session = session
        self.token = None
        self.user_data = {}
    
    async def authenticate(self):
        """Authenticate with the API."""
        # Get salt
        salt_payload = {
            "emailOrUsername": self.email,
            "mobileApp": False,
            "institutionId": None
        }
        
        async with self.session.post(
            "https://login.schulmanager-online.de/api/get-salt",
            json=salt_payload
        ) as response:
            if response.status != 200:
                raise Exception(f"Salt request failed: {response.status}")
            
            try:
                data = await response.json()
                salt = data if isinstance(data, str) else data.get("salt")
            except:
                salt = await response.text()
        
        # Generate hash
        password_bytes = self.password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
        salted_hash = hash_bytes.hex()
        
        # Login
        login_payload = {
            "emailOrUsername": self.email,
            "password": salted_hash,
            "mobileApp": False,
            "institutionId": None
        }
        
        async with self.session.post(
            "https://login.schulmanager-online.de/api/login",
            json=login_payload
        ) as response:
            if response.status != 200:
                raise Exception(f"Login failed: {response.status}")
            
            data = await response.json()
            self.token = data.get("jwt") or data.get("token")
            self.user_data = data.get("user", {})
            
            if not self.token:
                raise Exception("No token received")
    
    async def get_students(self):
        """Get students from user data."""
        students = []
        
        # Check for associated parents (parent account)
        for parent in self.user_data.get("associatedParents", []):
            student = parent.get("student")
            if student:
                students.append(student)
        
        # Check for associated student (student account)
        associated_student = self.user_data.get("associatedStudent")
        if associated_student:
            students.append(associated_student)
        
        return students
    
    async def test_letters_api(self):
        """Test the letters API endpoints."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("\n🧪 Testing Letters API...")
        
        # Test 1: Get letters list
        print("\n📋 Test 1: Get Letters List")
        payload = {
            "bundleVersion": "3505280ee7",
            "requests": [
                {
                    "moduleName": None,
                    "endpointName": "user-can-get-notifications"
                },
                {
                    "moduleName": "letters",
                    "endpointName": "get-letters"
                }
            ]
        }
        
        try:
            async with self.session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success!")
                    
                    if "responses" in data and len(data["responses"]) >= 2:
                        letters_response = data["responses"][1]
                        if letters_response.get("status") == 200:
                            letters = letters_response.get("data", [])
                            print(f"   📧 Found {len(letters)} letters")
                            
                            # Show first few letters
                            for i, letter in enumerate(letters[:3]):
                                print(f"   Letter {i+1}:")
                                print(f"     ID: {letter.get('id')}")
                                print(f"     Subject: {letter.get('subject', 'No subject')}")
                                print(f"     Date: {letter.get('createdAt', 'No date')}")
                                print(f"     From: {letter.get('from', 'Unknown sender')}")
                                print(f"     Read: {letter.get('read', 'Unknown')}")
                                
                                # Test letter details for first letter
                                if i == 0 and letter.get('id'):
                                    await self.test_letter_details(letter['id'])
                        else:
                            print(f"   ❌ Letters API error: {letters_response}")
                    else:
                        print(f"   Raw response: {json.dumps(data, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed: {error_text}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    async def test_letter_details(self, letter_id: int):
        """Test getting detailed letter information."""
        print(f"\n📄 Test 2: Get Letter Details (ID: {letter_id})")
        
        # Get first student for the test
        students = await self.get_students()
        if not students:
            print("   ❌ No students found for letter details test")
            return
        
        student_id = students[0].get("id")
        print(f"   Using student ID: {student_id}")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "bundleVersion": "3505280ee7",
            "requests": [
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
        }
        
        try:
            async with self.session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success!")
                    
                    if "responses" in data and len(data["responses"]) >= 1:
                        letter_response = data["responses"][0]
                        if letter_response.get("status") == 200:
                            letter_data = letter_response.get("data")
                            print(f"   📄 Letter Details:")
                            print(f"     Subject: {letter_data.get('subject', 'No subject')}")
                            print(f"     Content: {letter_data.get('content', 'No content')[:100]}...")
                            print(f"     Created: {letter_data.get('createdAt', 'Unknown')}")
                            
                            # Check attachments
                            attachments = letter_data.get('attachments', [])
                            print(f"     Attachments: {len(attachments)}")
                            for att in attachments:
                                print(f"       - {att.get('filename', 'Unknown file')} ({att.get('contentType', 'Unknown type')})")
                            
                            # Check student status
                            student_statuses = letter_data.get('studentStatuses', [])
                            print(f"     Student Statuses: {len(student_statuses)}")
                            for status in student_statuses:
                                print(f"       - Read: {status.get('read', 'Unknown')}")
                                print(f"       - Confirmed: {status.get('confirmed', 'Unknown')}")
                        else:
                            print(f"   ❌ Letter details error: {letter_response}")
                    else:
                        print(f"   Raw response: {json.dumps(data, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed: {error_text}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")


async def main():
    """Main test function."""
    print("🚀 Testing Schulmanager Online Letters API...")
    
    async with aiohttp.ClientSession() as session:
        api = SimpleSchulmanagerAPI("<schulmanager-login>", "<schulmanager-password>", session)
        
        try:
            # Authenticate
            print("🔐 Authenticating...")
            await api.authenticate()
            print("✅ Authentication successful")
            
            # Get students
            print("👥 Getting students...")
            students = await api.get_students()
            print(f"✅ Found {len(students)} students")
            
            if students:
                student = students[0]
                student_id = student.get("id")
                student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
                print(f"👤 Testing with: {student_name} (ID: {student_id})")
                
                # Test letters API
                await api.test_letters_api()
            else:
                print("❌ No students found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
