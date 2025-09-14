#!/usr/bin/env python3
"""Test script to check if bundleVersion is provided in login response."""

import asyncio
import aiohttp
import json
import hashlib

async def test_login_response():
    """Check login response for bundleVersion information."""
    
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("🔍 Investigating bundleVersion source in login process")
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
                
                print(f"   Salt response type: {type(salt)}")
                print(f"   Salt length: {len(salt) if isinstance(salt, str) else 'N/A'}")
                
                # Check if bundleVersion is in salt response
                if isinstance(salt, dict):
                    print(f"   Salt response keys: {list(salt.keys())}")
                    if "bundleVersion" in salt:
                        print(f"   ✅ bundleVersion found in salt response: {salt['bundleVersion']}")
                    else:
                        print("   ❌ bundleVersion NOT found in salt response")
                else:
                    print("   ❌ Salt response is string, no bundleVersion")
            
            # Step 2: Generate hash
            print("\n2️⃣ Generating hash...")
            password_bytes = password.encode('utf-8')
            salt_bytes = salt.encode('utf-8') if isinstance(salt, str) else str(salt).encode('utf-8')
            hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
            salted_hash = hash_bytes.hex()
            print(f"   Hash generated: {len(salted_hash)} characters")
            
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
                print(f"   Login successful!")
                print(f"   Response keys: {list(data.keys())}")
                
                # Check for bundleVersion in login response
                if "bundleVersion" in data:
                    print(f"   ✅ bundleVersion found in login response: {data['bundleVersion']}")
                else:
                    print("   ❌ bundleVersion NOT found in login response")
                
                # Check user data for bundleVersion
                user_data = data.get("user", {})
                print(f"   User data keys: {list(user_data.keys())}")
                if "bundleVersion" in user_data:
                    print(f"   ✅ bundleVersion found in user data: {user_data['bundleVersion']}")
                else:
                    print("   ❌ bundleVersion NOT found in user data")
                
                # Check for any version-related fields
                version_fields = []
                for key, value in data.items():
                    if "version" in key.lower() or "bundle" in key.lower():
                        version_fields.append(f"{key}: {value}")
                
                if version_fields:
                    print(f"   📋 Version-related fields found:")
                    for field in version_fields:
                        print(f"      - {field}")
                else:
                    print("   ❌ No version-related fields found")
                
                # Check nested objects for version info
                for key, value in data.items():
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if "version" in nested_key.lower() or "bundle" in nested_key.lower():
                                print(f"   📋 Version field in {key}.{nested_key}: {nested_value}")
            
            # Step 4: Test API call without bundleVersion
            print("\n4️⃣ Testing API call WITHOUT bundleVersion...")
            token = data.get("jwt") or data.get("token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Try homework API without bundleVersion
            payload_no_bundle = {
                "requests": [
                    {
                        "moduleName": "classbook",
                        "endpointName": "get-homework",
                        "parameters": {"student": {"id": 4333047}}
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload_no_bundle,
                headers=headers
            ) as response:
                print(f"   Status without bundleVersion: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                else:
                    result = await response.json()
                    print(f"   ✅ SUCCESS without bundleVersion!")
                    print(f"   Response keys: {list(result.keys())}")
            
            # Step 5: Test with bundleVersion
            print("\n5️⃣ Testing API call WITH bundleVersion...")
            payload_with_bundle = {
                "bundleVersion": "3505280ee7",
                "requests": [
                    {
                        "moduleName": "classbook",
                        "endpointName": "get-homework",
                        "parameters": {"student": {"id": 4333047}}
                    }
                ]
            }
            
            async with session.post(
                "https://login.schulmanager-online.de/api/calls",
                json=payload_with_bundle,
                headers=headers
            ) as response:
                print(f"   Status with bundleVersion: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                else:
                    result = await response.json()
                    print(f"   ✅ SUCCESS with bundleVersion!")
                    print(f"   Response keys: {list(result.keys())}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 Schulmanager Online bundleVersion Investigation")
    print("=" * 70)
    
    success = asyncio.run(test_login_response())
    
    if success:
        print("\n🎉 Investigation completed!")
    else:
        print("\n❌ Investigation failed!")
    
    exit(0 if success else 1)
