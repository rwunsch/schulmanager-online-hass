#!/usr/bin/env python3
"""
Test script to investigate multi-school / institutionId behavior.

This script helps answer:
1. Do students have an institutionId field?
2. Can we login with a specific institutionId?
3. What students are returned after institutionId-specific login?
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "schulmanager_online"))

import aiohttp
from api import SchulmanagerAPI


async def test_multi_school_login(email: str, password: str, institution_id: int = None):
    """Test login flow with optional institutionId."""
    
    print("=" * 80)
    print("MULTI-SCHOOL / INSTITUTION LOGIN TEST")
    print("=" * 80)
    print(f"Email: {email}")
    print(f"Institution ID: {institution_id or 'None (initial login)'}")
    print()
    
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI(email, password, session)
        
        try:
            # Step 1: Authenticate
            print("🔐 Step 1: Authenticating...")
            await api.authenticate(institution_id=institution_id)
            
            # Check for multi-school response
            multiple_accounts = api.get_multiple_accounts()
            if multiple_accounts:
                print("✅ Multi-school account detected!")
                print(f"   Found {len(multiple_accounts)} schools:")
                for acc in multiple_accounts:
                    print(f"   - ID: {acc.get('id')}, Label: {acc.get('label')}")
                print()
                print("⚠️  No JWT token yet - need to select a school and re-login")
                return
            
            # Step 2: Check authentication result
            if not api.token:
                print("❌ No token received and no multipleAccounts response")
                return
            
            print("✅ Authentication successful!")
            print(f"   Token: {api.token[:50]}...")
            print(f"   Institution ID in API: {api.institution_id}")
            print()
            
            # Step 3: Get students
            print("👨‍👩‍👧‍👦 Step 2: Fetching students...")
            students = await api.get_students()
            
            if not students:
                print("⚠️  No students found")
                return
            
            print(f"✅ Found {len(students)} student(s):")
            print()
            
            # Step 4: Inspect student structure
            for i, student in enumerate(students, 1):
                print(f"📋 Student {i}:")
                print(f"   ID: {student.get('id')}")
                print(f"   Name: {student.get('firstname')} {student.get('lastname')}")
                print(f"   Class: {student.get('classId', 'N/A')}")
                
                # Check for institutionId field
                if 'institutionId' in student:
                    print(f"   ✅ Institution ID: {student.get('institutionId')}")
                else:
                    print(f"   ❌ No institutionId field in student data")
                
                # Show all fields
                print(f"   All fields: {list(student.keys())}")
                print()
            
            # Step 5: Dump full student data
            print("📄 Full student data:")
            print(json.dumps(students, indent=2, default=str))
            print()
            
            # Step 6: Test API call with first student
            if students:
                print("🧪 Step 3: Testing API call (schedule)...")
                from datetime import datetime, timedelta
                student_id = students[0].get('id')
                today = datetime.now().date()
                start_date = today - timedelta(days=7)
                end_date = today + timedelta(days=7)
                
                try:
                    schedule = await api.get_schedule(student_id, start_date, end_date)
                    print(f"✅ Schedule API call successful!")
                    print(f"   Lessons retrieved: {len(schedule.get('lessons', []))}")
                except Exception as e:
                    print(f"❌ Schedule API call failed: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test multi-school login flow")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--institution-id", type=int, help="Institution ID to test with")
    
    args = parser.parse_args()
    
    await test_multi_school_login(
        email=args.email,
        password=args.password,
        institution_id=args.institution_id
    )


if __name__ == "__main__":
    asyncio.run(main())

