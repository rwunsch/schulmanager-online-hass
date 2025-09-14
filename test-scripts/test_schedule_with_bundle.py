#!/usr/bin/env python3
"""
Test Schedule API with bundleVersion parameter to fix 400 error.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date, timedelta

class SimpleSchulmanagerAPI:
    """Simplified API client for testing."""
    
    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        self.email = email
        self.password = password
        self.session = session
        self.token = None
        self.user_data = {}
    
    async def authenticate(self):
        """Authenticate with the API."""
        import hashlib
        
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
            "password": self.password,
            "hash": salted_hash,
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
        associated_parents = self.user_data.get("associatedParents", [])
        for parent in associated_parents:
            student = parent.get("student")
            if student:
                students.append(student)
        
        # Check for associated student (student account)
        associated_student = self.user_data.get("associatedStudent")
        if associated_student:
            students.append(associated_student)
        
        return students

async def test_schedule_api():
    """Test the Schedule API with bundleVersion."""
    
    # Test credentials (same as HA integration)
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("📅 Testing Schulmanager Online Schedule API")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        api = SimpleSchulmanagerAPI(email, password, session)
        
        try:
            print("🔐 Authenticating...")
            await api.authenticate()
            print("✅ Authentication successful!")
            
            print("\n👥 Getting students...")
            students = await api.get_students()
            print(f"✅ Found {len(students)} students:")
            
            for student in students:
                print(f"   - {student['firstname']} {student['lastname']} (ID: {student['id']})")
            
            if not students:
                print("❌ No students found")
                return False
            
            student = students[0]
            student_id = student['id']
            student_name = f"{student['firstname']} {student['lastname']}"
            
            print(f"\n📅 Testing Schedule API for {student_name}...")
            
            # Test Schedule API with bundleVersion
            headers = {"Authorization": f"Bearer {api.token}"}
            
            # Test 1: Current failing request structure WITH bundleVersion
            print("\n1️⃣ Testing with bundleVersion (current structure)...")
            payload1 = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": "schedules",
                        "endpointName": "get-actual-lessons",
                        "parameters": {
                            "student": {"id": student_id},
                            "start": "2025-09-08",
                            "end": "2025-09-22"
                        }
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload1,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ SUCCESS! Response: {json.dumps(data, indent=2)[:500]}...")
                    
                    # Analyze the response
                    results = data.get("results", [])
                    if results:
                        schedule_result = results[0]
                        print(f"   📊 Schedule result status: {schedule_result.get('status')}")
                        schedule_data = schedule_result.get('data', {})
                        print(f"   📊 Schedule data keys: {list(schedule_data.keys())}")
                        
                        lessons = schedule_data.get('lessons', [])
                        print(f"   📚 Found {len(lessons)} lessons")
                        
                        if lessons:
                            print(f"   📝 First lesson: {json.dumps(lessons[0], indent=2)[:200]}...")
                else:
                    error_text = await response.text()
                    print(f"   ❌ FAILED: {error_text}")
            
            # Test 2: Try with full student object
            print("\n2️⃣ Testing with full student object...")
            payload2 = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": "schedules",
                        "endpointName": "get-actual-lessons",
                        "parameters": {
                            "student": student,  # Full student object
                            "start": "2025-09-08",
                            "end": "2025-09-22"
                        }
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload2,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ SUCCESS with full student object!")
                else:
                    error_text = await response.text()
                    print(f"   ❌ FAILED: {error_text}")
            
            # Test 3: Try different endpoint
            print("\n3️⃣ Testing different endpoint (get-lessons)...")
            payload3 = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": "schedules",
                        "endpointName": "get-lessons",  # Different endpoint
                        "parameters": {
                            "student": {"id": student_id},
                            "start": "2025-09-08",
                            "end": "2025-09-22"
                        }
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload3,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ SUCCESS with get-lessons endpoint!")
                else:
                    error_text = await response.text()
                    print(f"   ❌ FAILED: {error_text}")
            
            # Test 4: Compare with working Homework API
            print("\n4️⃣ Testing working Homework API for comparison...")
            payload4 = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": "classbook",
                        "endpointName": "get-homework",
                        "parameters": {"student": {"id": student_id}}
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload4,
                headers=headers
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Homework API still works!")
                    results = data.get("results", [])
                    if results:
                        hw_result = results[0]
                        hw_data = hw_result.get('data', [])
                        print(f"   📚 Found {len(hw_data)} homework assignments")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Even homework API failed: {error_text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🧪 Schulmanager Online Schedule API Test with bundleVersion")
    print("=" * 70)
    
    success = asyncio.run(test_schedule_api())
    
    if success:
        print("\n🎉 Schedule API test completed!")
    else:
        print("\n❌ Schedule API test failed!")
    
    exit(0 if success else 1)
