#!/usr/bin/env python3
"""Test script to find institution name in API response."""

import asyncio
import aiohttp
import json
import hashlib
import base64

async def test_institution_name():
    """Check where institution name comes from in API response."""
    
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("🔍 Finding Institution Name in API Response")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get salt
            print("1️⃣ Getting salt...")
            salt_payload = {
                "emailOrUsername": email,
                "mobileApp": False,
                "institutionId": None
            }
            
            async with session.post(
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
                    salt = salt.strip('"')  # Remove quotes
                
                print(f"   ✅ Salt received ({len(salt)} chars)")
            
            # Step 2: Generate hash
            print("\n2️⃣ Generating hash...")
            iterations = 10000
            key_length = 64
            password_bytes = password.encode('utf-8')
            salt_bytes = base64.b64decode(salt)
            derived = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, iterations, key_length)
            salted_hash = base64.b64encode(derived).decode('utf-8')
            print(f"   ✅ Hash generated")
            
            # Step 3: Login
            print("\n3️⃣ Logging in...")
            login_payload = {
                "emailOrUsername": email,
                "password": password,
                "hash": salted_hash,
                "mobileApp": False,
                "institutionId": None
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/login",
                json=login_payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Login failed: {response.status}")
                
                data = await response.json()
                print(f"   ✅ Login successful!")
                print(f"\n📋 Top-level response keys: {list(data.keys())}")
                
                # Check user data
                user_data = data.get("user", {})
                print(f"\n👤 User data keys: {list(user_data.keys())}")
                
                # Check for institution-related fields
                print(f"\n🏫 Looking for institution information...")
                
                # Check direct fields
                institution_fields = {}
                for key in user_data.keys():
                    if 'institution' in key.lower() or 'school' in key.lower():
                        institution_fields[key] = user_data[key]
                
                if institution_fields:
                    print(f"\n   ✅ Institution-related fields found:")
                    for key, value in institution_fields.items():
                        if isinstance(value, dict):
                            print(f"      {key}: {json.dumps(value, indent=8)}")
                        else:
                            print(f"      {key}: {value}")
                else:
                    print(f"   ⚠️ No direct institution fields found")
                
                # Check nested objects
                print(f"\n🔍 Checking nested objects...")
                for key, value in user_data.items():
                    if isinstance(value, dict):
                        print(f"\n   Object: user.{key}")
                        print(f"   Keys: {list(value.keys())}")
                        # Look for name-related fields
                        for nested_key in value.keys():
                            if 'name' in nested_key.lower():
                                print(f"      ✅ {nested_key}: {value[nested_key]}")
                
                # Check associated parents for institution info
                if "associatedParents" in user_data:
                    print(f"\n👨‍👩‍👧 Checking associatedParents...")
                    for i, parent in enumerate(user_data["associatedParents"]):
                        print(f"\n   Parent {i}:")
                        print(f"     Keys: {list(parent.keys())}")
                        
                        if "student" in parent:
                            student = parent["student"]
                            print(f"     Student keys: {list(student.keys())}")
                            
                            # Check for institution info in student
                            for key in student.keys():
                                if 'institution' in key.lower() or 'school' in key.lower():
                                    print(f"       ✅ {key}: {student[key]}")
                
                # Print full user data (sanitized)
                print(f"\n📄 Full user data structure (sanitized):")
                sanitized = {k: v for k, v in user_data.items() 
                            if k not in ['id', 'firstname', 'lastname', 'email']}
                print(json.dumps(sanitized, indent=2, default=str))
                
                # Now test with specific institutionId
                print(f"\n\n" + "=" * 60)
                print(f"4️⃣ Testing with specific institutionId (13309)...")
                
                # Get salt with institutionId
                async with session.post(
                    "https://login.schulmanager-online.de/api/get-salt",
                    json={
                        "emailOrUsername": email,
                        "mobileApp": False,
                        "institutionId": 13309
                    }
                ) as response:
                    salt2 = await response.text()
                    salt2 = salt2.strip('"')
                
                # Generate new hash
                salt_bytes2 = base64.b64decode(salt2)
                derived2 = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes2, iterations, key_length)
                salted_hash2 = base64.b64encode(derived2).decode('utf-8')
                
                # Login with institutionId
                async with session.post(
                    "https://login.schulmanager-online.de/api/login",
                    json={
                        "emailOrUsername": email,
                        "password": password,
                        "hash": salted_hash2,
                        "mobileApp": False,
                        "institutionId": 13309
                    }
                ) as response:
                    data2 = await response.json()
                    print(f"   ✅ Login with institutionId=13309 successful!")
                    
                    user_data2 = data2.get("user", {})
                    print(f"\n👤 User data keys: {list(user_data2.keys())}")
                    
                    # Check for institution info
                    print(f"\n🏫 Institution information:")
                    for key in user_data2.keys():
                        if 'institution' in key.lower():
                            value = user_data2[key]
                            if isinstance(value, dict):
                                print(f"   {key}:")
                                print(json.dumps(value, indent=4))
                            else:
                                print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 Schulmanager Institution Name Investigation")
    print("=" * 70)
    
    success = asyncio.run(test_institution_name())
    
    if success:
        print("\n🎉 Investigation completed!")
    else:
        print("\n❌ Investigation failed!")
    
    exit(0 if success else 1)

