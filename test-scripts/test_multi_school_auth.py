#!/usr/bin/env python3
"""Test script for Schulmanager Online authentication flow."""

import asyncio
import hashlib
import json
import sys
import aiohttp

# API endpoints
API_BASE_URL = "https://login.schulmanager-online.de"
SALT_URL = f"{API_BASE_URL}/api/get-salt"
LOGIN_URL = f"{API_BASE_URL}/api/login"

# Test credentials
EMAIL = "wunsch@gmx.de"
PASSWORD = "Gjns26twr+9_R@Y"


def generate_salted_hash(password: str, salt: str) -> str:
    """
    Generate salted hash using PBKDF2-SHA512.
    - PBKDF2 with SHA-512
    - 512 bytes output (4096 bits) = 1024 hex characters
    - Salt as UTF-8 encoded (not hex!)
    - 99999 iterations
    """
    # Password as bytes (binary)
    password_bytes = password.encode('utf-8')
    
    # Salt as UTF-8 encoded (IMPORTANT: not hex!)
    salt_bytes = salt.encode('utf-8')
    
    # PBKDF2 with SHA-512, 512 bytes output, 99999 iterations
    hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
    
    # Convert to hex (1024 characters)
    hash_hex = hash_bytes.hex()
    
    return hash_hex


async def test_authentication():
    """Test the authentication flow."""
    async with aiohttp.ClientSession() as session:
        print("=" * 80)
        print("STEP 1: Getting salt (without institution_id)")
        print("=" * 80)
        
        # Step 1: Get salt without institution_id
        salt_payload = {
            "emailOrUsername": EMAIL,
            "mobileApp": False,
            "institutionId": None
        }
        
        print(f"\n📤 Request to: {SALT_URL}")
        print(f"📤 Payload: {json.dumps(salt_payload, indent=2)}")
        
        async with session.post(SALT_URL, json=salt_payload) as response:
            print(f"\n📥 Response status: {response.status}")
            salt_response = await response.text()
            print(f"📥 Response: {salt_response[:100]}...")
            
            if response.status != 200:
                print(f"❌ Failed to get salt: {response.status}")
                return
            
            # Parse salt (might be JSON string or plain text)
            try:
                salt = json.loads(salt_response)
                if isinstance(salt, dict):
                    salt = salt.get("salt", salt_response)
            except:
                salt = salt_response.strip('"')
            
            print(f"\n✅ Salt received: {len(salt)} characters")
        
        # Step 2: Generate salted hash
        print("\n" + "=" * 80)
        print("STEP 2: Generating salted hash")
        print("=" * 80)
        
        salted_hash = generate_salted_hash(PASSWORD, salt)
        print(f"\n✅ Hash generated: {len(salted_hash)} characters")
        print(f"   First 50 chars: {salted_hash[:50]}...")
        
        # Step 3: Login without institution_id
        print("\n" + "=" * 80)
        print("STEP 3: Login (without institution_id)")
        print("=" * 80)
        
        login_payload = {
            "emailOrUsername": EMAIL,
            "password": PASSWORD,
            "hash": salted_hash,
            "mobileApp": False,
            "institutionId": None
        }
        
        print(f"\n📤 Request to: {LOGIN_URL}")
        print(f"📤 Payload: {json.dumps({**login_payload, 'password': '***', 'hash': salted_hash[:50] + '...'}, indent=2)}")
        
        async with session.post(LOGIN_URL, json=login_payload) as response:
            print(f"\n📥 Response status: {response.status}")
            login_response = await response.json()
            print(f"📥 Response: {json.dumps(login_response, indent=2)[:500]}...")
            
            if response.status != 200:
                print(f"❌ Login failed: {response.status}")
                return
            
            # Check if multi-school account
            if "multipleAccounts" in login_response:
                print("\n" + "=" * 80)
                print("🏫 MULTI-SCHOOL ACCOUNT DETECTED!")
                print("=" * 80)
                accounts = login_response.get("multipleAccounts", [])
                print(f"\nFound {len(accounts)} schools:")
                for i, account in enumerate(accounts):
                    print(f"  {i+1}. ID: {account.get('id')}, Label: {account.get('label')}")
                
                print("\n⚠️  No token received - school selection required")
                print("⚠️  User would need to select a school and re-authenticate")
                
                # Simulate selecting first school
                if accounts:
                    selected_school = accounts[0]
                    print("\n" + "=" * 80)
                    print(f"STEP 4: Re-authenticating with selected school (ID: {selected_school['id']})")
                    print("=" * 80)
                    
                    # Get salt with institution_id
                    salt_payload_with_id = {
                        "emailOrUsername": EMAIL,
                        "mobileApp": False,
                        "institutionId": selected_school['id']
                    }
                    
                    print(f"\n📤 Request to: {SALT_URL}")
                    print(f"📤 Payload: {json.dumps(salt_payload_with_id, indent=2)}")
                    
                    async with session.post(SALT_URL, json=salt_payload_with_id) as response:
                        salt_response = await response.text()
                        try:
                            salt = json.loads(salt_response)
                            if isinstance(salt, dict):
                                salt = salt.get("salt", salt_response)
                        except:
                            salt = salt_response.strip('"')
                        
                        print(f"\n✅ Salt received with institution_id: {len(salt)} characters")
                    
                    # Generate new hash
                    salted_hash = generate_salted_hash(PASSWORD, salt)
                    
                    # Login with institution_id
                    login_payload_with_id = {
                        "emailOrUsername": EMAIL,
                        "password": PASSWORD,
                        "hash": salted_hash,
                        "mobileApp": False,
                        "institutionId": selected_school['id']
                    }
                    
                    print(f"\n📤 Request to: {LOGIN_URL}")
                    print(f"📤 Payload: {json.dumps({**login_payload_with_id, 'password': '***', 'hash': salted_hash[:50] + '...'}, indent=2)}")
                    
                    async with session.post(LOGIN_URL, json=login_payload_with_id) as response:
                        print(f"\n📥 Response status: {response.status}")
                        login_response_with_id = await response.json()
                        print(f"📥 Response keys: {list(login_response_with_id.keys())}")
                        
                        if "jwt" in login_response_with_id or "token" in login_response_with_id:
                            token = login_response_with_id.get("jwt") or login_response_with_id.get("token")
                            print(f"\n✅ Token received: {token[:50]}...")
                            
                            user_data = login_response_with_id.get("user", {})
                            print(f"\n👤 User data:")
                            print(f"   - Institution ID: {user_data.get('institutionId')}")
                            print(f"   - Associated Parents: {len(user_data.get('associatedParents', []))}")
                            associated_student = user_data.get('associatedStudent')
                            student_id = associated_student.get('id') if associated_student else 'None'
                            print(f"   - Associated Student: {student_id}")
                            
                            # Extract students
                            students = []
                            for parent in user_data.get("associatedParents", []):
                                student = parent.get("student")
                                if student:
                                    students.append(student)
                            
                            if user_data.get("associatedStudent"):
                                students.append(user_data.get("associatedStudent"))
                            
                            print(f"\n👨‍🎓 Found {len(students)} students:")
                            for student in students:
                                print(f"   - ID: {student.get('id')}, Name: {student.get('firstname')} {student.get('lastname')}")
                        else:
                            print(f"\n❌ No token received even with institution_id")
                            print(f"Response: {json.dumps(login_response_with_id, indent=2)[:500]}")
                
            else:
                # Single school account
                print("\n" + "=" * 80)
                print("🏫 SINGLE-SCHOOL ACCOUNT")
                print("=" * 80)
                
                token = login_response.get("jwt") or login_response.get("token")
                if token:
                    print(f"\n✅ Token received: {token[:50]}...")
                    
                    user_data = login_response.get("user", {})
                    print(f"\n👤 User data:")
                    print(f"   - Institution ID: {user_data.get('institutionId')}")
                    print(f"   - Associated Parents: {len(user_data.get('associatedParents', []))}")
                    associated_student = user_data.get('associatedStudent')
                    student_id = associated_student.get('id') if associated_student else 'None'
                    print(f"   - Associated Student: {student_id}")
                    
                    # Extract students
                    students = []
                    for parent in user_data.get("associatedParents", []):
                        student = parent.get("student")
                        if student:
                            students.append(student)
                    
                    if user_data.get("associatedStudent"):
                        students.append(user_data.get("associatedStudent"))
                    
                    print(f"\n👨‍🎓 Found {len(students)} students:")
                    for student in students:
                        print(f"   - ID: {student.get('id')}, Name: {student.get('firstname')} {student.get('lastname')}")
                else:
                    print(f"\n❌ No token received")
                    print(f"Response: {json.dumps(login_response, indent=2)[:500]}")


if __name__ == "__main__":
    print("\n🔐 Schulmanager Online Authentication Test")
    print(f"Testing with user: {EMAIL}\n")
    
    asyncio.run(test_authentication())
    
    print("\n" + "=" * 80)
    print("✅ Test completed")
    print("=" * 80)

