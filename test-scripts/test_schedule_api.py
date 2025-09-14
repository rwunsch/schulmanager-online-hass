#!/usr/bin/env python3
"""Test Schedule API directly to debug the 400 error."""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta

# Add the parent directory to the path so we can import the API
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.schulmanager_online.api import SchulmanagerOnlineAPI

async def test_schedule_api():
    """Test the schedule API directly."""
    print("🚀 Testing Schedule API...")
    
    # Initialize API
    api = SchulmanagerOnlineAPI("<schulmanager-login>", "<schulmanager-password>")
    
    try:
        # Login
        print("🔐 Logging in...")
        await api._login()
        print("✅ Login successful")
        
        # Get students
        print("👥 Getting students...")
        students = await api.get_students()
        print(f"✅ Found {len(students)} students")
        
        if students:
            student = students[0]
            student_id = student.get("id")
            student_name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
            print(f"👤 Testing with student: {student_name} (ID: {student_id})")
            
            # Test schedule API with different date ranges
            today = date.today()
            
            # Test 1: Today only
            print(f"\n📅 Test 1: Today only ({today})")
            try:
                schedule = await api.get_schedule(student_id, today, today)
                print(f"✅ Success: {len(schedule.get('data', []))} lessons")
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 2: This week
            monday = today - timedelta(days=today.weekday())
            friday = monday + timedelta(days=4)
            print(f"\n📅 Test 2: This week ({monday} to {friday})")
            try:
                schedule = await api.get_schedule(student_id, monday, friday)
                print(f"✅ Success: {len(schedule.get('data', []))} lessons")
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 3: Next week
            next_monday = monday + timedelta(days=7)
            next_friday = next_monday + timedelta(days=4)
            print(f"\n📅 Test 3: Next week ({next_monday} to {next_friday})")
            try:
                schedule = await api.get_schedule(student_id, next_monday, next_friday)
                print(f"✅ Success: {len(schedule.get('data', []))} lessons")
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 4: Raw API call to see exact error
            print(f"\n🔍 Test 4: Raw API call")
            try:
                requests = [
                    {
                        "moduleName": "schedules",
                        "endpointName": "get-actual-lessons",
                        "parameters": {
                            "student": {"id": student_id},
                            "start": today.isoformat(),
                            "end": (today + timedelta(days=7)).isoformat()
                        }
                    }
                ]
                
                response = await api._make_api_call(requests)
                print(f"✅ Raw response: {response}")
                
                if "responses" in response:
                    for i, resp in enumerate(response["responses"]):
                        print(f"  Response {i}: Status {resp.get('status')}")
                        if resp.get("status") != 200:
                            print(f"    Error: {resp}")
                        else:
                            data = resp.get("data", [])
                            print(f"    Data: {len(data)} items")
                            if data:
                                print(f"    Sample: {data[0] if isinstance(data, list) else data}")
                
            except Exception as e:
                print(f"❌ Raw API call failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schedule_api())
