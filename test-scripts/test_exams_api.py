#!/usr/bin/env python3
"""Simple test script for Schulmanager Online Exams API."""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta


class SimpleSchulmanagerAPI:
    """Simplified API client for testing exams functionality."""
    
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
    
    async def get_exams(self, student_id: int, start_date: str, end_date: str):
        """Get exams using exams module."""
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "bundleVersion": "3505280ee7",
            "requests": [
                {
                    "moduleName": "exams",
                    "endpointName": "get-exams",
                    "parameters": {
                        "student": {"id": student_id},
                        "start": start_date,
                        "end": end_date
                    }
                }
            ]
        }
        
        async with self.session.post(
            "https://login.schulmanager-online.de/api/calls",
            json=payload,
            headers=headers
        ) as response:
            if response.status != 200:
                raise Exception(f"Exams API failed: {response.status}")
            
            data = await response.json()
            results = data.get("results", [])
            
            if not results:
                raise Exception("No results in response")
            
            return results[0]


def analyze_exams_data(exams_data):
    """Analyze exams data and create sensor-like outputs."""
    print("📊 Analyzing exams data...")
    
    # Extract exams - data can be a list directly
    data = exams_data.get("data", [])
    if isinstance(data, list):
        exams = data
    elif isinstance(data, dict):
        exams = data.get("exams", [])
    else:
        exams = exams_data.get("exams", [])
    
    print(f"   - Total exams found: {len(exams)}")
    
    if not exams:
        print("   - No exams found")
        return
    
    # Analyze by date
    today = datetime.now().date()
    this_week_start = today - timedelta(days=today.weekday())
    this_week_end = this_week_start + timedelta(days=4)
    next_week_start = this_week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=4)
    
    exams_today = []
    exams_this_week = []
    exams_next_week = []
    upcoming_exams = []
    
    for exam in exams:
        exam_date_str = exam.get("date", "")
        if not exam_date_str:
            continue
        
        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
            
            if exam_date == today:
                exams_today.append(exam)
            
            if this_week_start <= exam_date <= this_week_end:
                exams_this_week.append(exam)
            elif next_week_start <= exam_date <= next_week_end:
                exams_next_week.append(exam)
            elif exam_date >= today:
                upcoming_exams.append(exam)
        except ValueError:
            print(f"   - Invalid date format: {exam_date_str}")
    
    print(f"   - Exams today: {len(exams_today)}")
    print(f"   - Exams this week: {len(exams_this_week)}")
    print(f"   - Exams next week: {len(exams_next_week)}")
    print(f"   - Upcoming exams: {len(upcoming_exams)}")
    
    # Show sample exams
    if exams:
        print("\n📝 Sample exam entries:")
        for i, exam in enumerate(exams[:3]):
            print(f"   {i+1}. Subject: {exam.get('subject', 'Unknown')}")
            print(f"      Title: {exam.get('title', exam.get('name', 'No title'))}")
            print(f"      Date: {exam.get('date', 'No date')}")
            print(f"      Time: {exam.get('time', exam.get('startTime', 'No time'))}")
            print(f"      Duration: {exam.get('duration', 'No duration')}")
            print(f"      Room: {exam.get('room', 'No room')}")
            print(f"      Type: {exam.get('type', exam.get('examType', 'exam'))}")
            print()
    
    # Show structure of first exam
    if exams:
        print("🔍 Structure of first exam item:")
        first_exam = exams[0]
        print(json.dumps(first_exam, indent=2, ensure_ascii=False)[:800] + "...")


async def test_exams_api():
    """Test the exams API."""
    
    # Test credentials
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("📋 Testing Schulmanager Online Exams API")
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
            
            print(f"\n📋 Testing exams API for {student_name}...")
            
            # Test exams endpoint with date range
            today = datetime.now().date()
            start_date = (today - timedelta(weeks=1)).isoformat()  # Past week
            end_date = (today + timedelta(weeks=8)).isoformat()    # Next 8 weeks
            
            print(f"📡 Calling exams/get-exams for date range {start_date} to {end_date}...")
            exams_data = await api.get_exams(student_id, start_date, end_date)
            
            print(f"✅ Exams API successful!")
            print(f"📊 Response status: {exams_data.get('status')}")
            print(f"📊 Response keys: {list(exams_data.keys())}")
            
            if exams_data.get('status') == 200:
                analyze_exams_data(exams_data)
            else:
                print(f"❌ API returned status: {exams_data.get('status')}")
                print(f"Error: {exams_data.get('error', 'Unknown error')}")
                return False
            
            print("\n🎉 Exams API test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("🧪 Schulmanager Online Exams API Test")
    print("=" * 60)
    
    success = asyncio.run(test_exams_api())
    
    if success:
        print("\n🎉 Exams API test passed!")
    else:
        print("\n❌ Exams API test failed!")
    
    exit(0 if success else 1)
