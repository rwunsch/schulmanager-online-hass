#!/usr/bin/env python3
"""Simple test script for Schulmanager Online Homework API."""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta


class SimpleSchulmanagerAPI:
    """Simplified API client for testing homework functionality."""
    
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
    
    async def get_homework_classbook(self, student_id: int):
        """Get homework using classbook module."""
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "bundleVersion": "3505280ee7",
            "requests": [
                {
                    "moduleName": "classbook",
                    "endpointName": "get-homework",
                    "parameters": {"student": {"id": student_id}}
                }
            ]
        }
        
        async with self.session.post(
            "https://login.schulmanager-online.de/api/calls",
            json=payload,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Homework API failed: {response.status}")
            
            data = await response.json()
            results = data.get("results", [])
            
            if not results:
                raise Exception("No results in response")
            
            return results[0]


def analyze_homework_data(homework_data):
    """Analyze homework data and create sensor-like outputs."""
    print("📊 Analyzing homework data...")
    
    # Extract homeworks - data can be a list directly
    data = homework_data.get("data", [])
    if isinstance(data, list):
        homeworks = data
    elif isinstance(data, dict):
        homeworks = data.get("homeworks", [])
    else:
        homeworks = homework_data.get("homeworks", [])
    
    print(f"   - Total homework assignments: {len(homeworks)}")
    
    if not homeworks:
        print("   - No homework found")
        return
    
    # Analyze by due date
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    due_today = []
    due_tomorrow = []
    overdue = []
    upcoming = []
    
    for hw in homeworks:
        due_date_str = hw.get("dueDate", "")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            
            if due_date == today:
                due_today.append(hw)
            elif due_date == tomorrow:
                due_tomorrow.append(hw)
            elif due_date < today and not hw.get("completed", False):
                overdue.append(hw)
            elif today < due_date <= next_week:
                upcoming.append(hw)
        except ValueError:
            print(f"   - Invalid date format: {due_date_str}")
    
    print(f"   - Due today: {len(due_today)}")
    print(f"   - Due tomorrow: {len(due_tomorrow)}")
    print(f"   - Overdue: {len(overdue)}")
    print(f"   - Upcoming (7 days): {len(upcoming)}")
    
    # Show structure of first homework to understand the data format
    if homeworks:
        print("🔍 Structure of first homework item:")
        first_hw = homeworks[0]
        print(json.dumps(first_hw, indent=2, ensure_ascii=False)[:800] + "...")
        
        print("\n📝 Sample homework assignments:")
        for i, hw in enumerate(homeworks[:3]):
            # Handle different data structures
            if isinstance(hw, dict):
                subject = hw.get('subject', {})
                if isinstance(subject, dict):
                    subject_name = subject.get('name', 'Unknown')
                else:
                    subject_name = str(subject)
                
                teacher = hw.get('teacher', {})
                if isinstance(teacher, dict):
                    teacher_name = teacher.get('name', 'Unknown')
                else:
                    teacher_name = str(teacher)
                
                print(f"   {i+1}. Subject: {subject_name}")
                print(f"      Description: {str(hw.get('description', 'No description'))[:50]}...")
                print(f"      Due Date: {hw.get('dueDate', 'No due date')}")
                print(f"      Teacher: {teacher_name}")
                print(f"      Completed: {hw.get('completed', False)}")
            else:
                print(f"   {i+1}. Raw data: {str(hw)[:100]}...")
            print()


async def test_homework_api():
    """Test the homework API."""
    
    # Test credentials (same as HA integration)
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("🏠 Testing Schulmanager Online Homework API")
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
            
            print(f"\n📚 Testing homework API for {student_name}...")
            
            # Test classbook homework endpoint
            print("📡 Calling classbook/get-homework...")
            homework_data = await api.get_homework_classbook(student_id)
            
            print(f"✅ Homework API successful!")
            print(f"📊 Response status: {homework_data.get('status')}")
            print(f"📊 Response keys: {list(homework_data.keys())}")
            
            if homework_data.get('status') == 200:
                analyze_homework_data(homework_data)
            else:
                print(f"❌ API returned status: {homework_data.get('status')}")
                print(f"Error: {homework_data.get('error', 'Unknown error')}")
                return False
            
            print("\n🎉 Homework API test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("🧪 Schulmanager Online Homework API Test")
    print("=" * 60)
    
    success = asyncio.run(test_homework_api())
    
    if success:
        print("\n🎉 Homework API test passed!")
    else:
        print("\n❌ Homework API test failed!")
    
    exit(0 if success else 1)
