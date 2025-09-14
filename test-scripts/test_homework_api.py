#!/usr/bin/env python3
"""Test script for Schulmanager Online Homework API."""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.schulmanager_online.api import SchulmanagerAPI, SchulmanagerAPIError


async def test_homework_api():
    """Test the homework API endpoints."""
    
    # Test credentials (same as HA integration)
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("🏠 Testing Schulmanager Online Homework API")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI(email, password, session)
        
        try:
            print("🔐 Authenticating...")
            await api.authenticate()
            print(f"✅ Authentication successful!")
            
            print("\n👥 Getting students...")
            students = await api.get_students()
            print(f"✅ Found {len(students)} students:")
            
            for student in students:
                print(f"   - {student['firstname']} {student['lastname']} (ID: {student['id']})")
            
            if not students:
                print("❌ No students found, cannot test homework API")
                return False
            
            student = students[0]
            student_id = student['id']
            student_name = f"{student['firstname']} {student['lastname']}"
            
            print(f"\n📚 Testing homework API for {student_name}...")
            
            # Test new classbook endpoint
            print("\n1️⃣ Testing classbook/get-homework endpoint...")
            try:
                homework_data = await api.get_homework(student_id)
                print(f"✅ Homework API successful!")
                print(f"📊 Response structure:")
                print(f"   - Keys: {list(homework_data.keys())}")
                
                homeworks = homework_data.get("homeworks", homework_data.get("data", []))
                print(f"   - Found {len(homeworks)} homework assignments")
                
                if homeworks:
                    print("\n📋 Sample homework assignments:")
                    for i, hw in enumerate(homeworks[:3]):  # Show first 3
                        print(f"   {i+1}. Subject: {hw.get('subject', {}).get('name', 'Unknown')}")
                        print(f"      Description: {hw.get('description', 'No description')[:50]}...")
                        print(f"      Due Date: {hw.get('dueDate', 'No due date')}")
                        print(f"      Teacher: {hw.get('teacher', {}).get('name', 'Unknown')}")
                        print(f"      Completed: {hw.get('completed', False)}")
                        print()
                
                # Test homework sensors
                print("🧪 Testing homework sensor logic...")
                from custom_components.schulmanager_online import homework_sensors
                
                student_data = {"homework": homework_data}
                
                print(f"   - Due today: {homework_sensors.get_homework_due_today_count(student_data)}")
                print(f"   - Due tomorrow: {homework_sensors.get_homework_due_tomorrow_count(student_data)}")
                print(f"   - Overdue: {homework_sensors.get_homework_overdue_count(student_data)}")
                print(f"   - Upcoming (7 days): {homework_sensors.get_homework_upcoming_count(student_data)}")
                
                # Show detailed attributes for due today
                today_attrs = homework_sensors.get_homework_due_today_attributes(student_data)
                if today_attrs["count"] > 0:
                    print(f"\n📅 Homework due today details:")
                    for hw in today_attrs["homework"]:
                        print(f"   - {hw['subject']}: {hw['description'][:30]}...")
                
            except Exception as e:
                print(f"❌ Classbook homework API failed: {e}")
                
                # Try legacy endpoint as fallback
                print("\n2️⃣ Testing legacy homeworks/get-homeworks endpoint...")
                try:
                    homework_data = await api.get_homework_legacy(student_id)
                    print(f"✅ Legacy homework API successful!")
                    print(f"📊 Response structure: {list(homework_data.keys())}")
                except Exception as e2:
                    print(f"❌ Legacy homework API also failed: {e2}")
                    return False
            
            print("\n🎉 Homework API test completed successfully!")
            return True
            
        except SchulmanagerAPIError as e:
            print(f"❌ API Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_homework_api_raw():
    """Test the homework API with raw requests to understand the response structure."""
    
    print("\n🔍 Testing raw homework API calls...")
    print("=" * 50)
    
    # Test credentials (same as HA integration)
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI(email, password, session)
        
        try:
            await api.authenticate()
            students = await api.get_students()
            
            if not students:
                print("❌ No students found")
                return False
            
            student_id = students[0]['id']
            
            # Test the exact API call from your curl example
            print(f"\n📡 Testing exact API call for student {student_id}...")
            
            headers = {"Authorization": f"Bearer {api.token}"}
            payload = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": None,
                        "endpointName": "user-can-get-notifications"
                    },
                    {
                        "moduleName": "classbook",
                        "endpointName": "get-homework",
                        "parameters": {"student": {"id": student_id}}
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Raw API call successful!")
                    print(f"📊 Full response structure:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")
                    
                    # Extract homework data
                    results = data.get("results", [])
                    if len(results) >= 2:
                        homework_result = results[1]  # Second request is homework
                        print(f"\n📚 Homework result:")
                        print(f"   - Status: {homework_result.get('status')}")
                        print(f"   - Data keys: {list(homework_result.get('data', {}).keys())}")
                        
                        homework_data = homework_result.get('data', {})
                        homeworks = homework_data.get('homeworks', [])
                        print(f"   - Homework count: {len(homeworks)}")
                        
                        if homeworks:
                            print(f"\n📝 First homework item structure:")
                            first_hw = homeworks[0]
                            print(json.dumps(first_hw, indent=2, ensure_ascii=False)[:500] + "...")
                    
                else:
                    print(f"❌ Raw API call failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text[:200]}...")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Raw API test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("🧪 Schulmanager Online Homework API Test")
    print("=" * 60)
    
    # Run both tests
    success1 = asyncio.run(test_homework_api())
    success2 = asyncio.run(test_homework_api_raw())
    
    if success1 and success2:
        print("\n🎉 All homework API tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some homework API tests failed!")
        sys.exit(1)
