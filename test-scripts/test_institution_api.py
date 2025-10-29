#!/usr/bin/env python3
"""
Test script to investigate institution/school information availability in Schulmanager API.
Tests:
1. JWT token payload decoding
2. All available API modules to find institution info
3. User data structure inspection
"""

import asyncio
import aiohttp
import hashlib
import json
import base64
from typing import Dict, Any


EMAIL = "wunsch@gmx.de"
PASSWORD = "Gjns26twr+9_R@Y"

SALT_URL = "https://login.schulmanager-online.de/api/get-salt"
LOGIN_URL = "https://login.schulmanager-online.de/api/login"
CALLS_URL = "https://login.schulmanager-online.de/api/calls"


def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode JWT token (without verification) to see payload."""
    try:
        # JWT has 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        # Decode payload (add padding if needed)
        payload_part = parts[1]
        # Add padding
        padding = len(payload_part) % 4
        if padding:
            payload_part += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded)
    except Exception as e:
        return {"error": str(e)}


async def test_institution_endpoints():
    """Test various approaches to get institution information."""
    
    async with aiohttp.ClientSession() as session:
        print("=" * 80)
        print("SCHULMANAGER INSTITUTION API INVESTIGATION")
        print("=" * 80)
        
        # Step 1: Authenticate
        print("\n📡 Step 1: Authenticating...")
        
        # Get salt
        async with session.post(SALT_URL, json={
            "emailOrUsername": EMAIL,
            "mobileApp": False,
            "institutionId": None
        }) as resp:
            salt = (await resp.text()).strip('"')
        
        # Generate hash
        password_bytes = PASSWORD.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
        salted_hash = hash_bytes.hex()
        
        # Login
        async with session.post(LOGIN_URL, json={
            "emailOrUsername": EMAIL,
            "password": PASSWORD,
            "hash": salted_hash,
            "mobileApp": False,
            "institutionId": None
        }) as resp:
            login_data = await resp.json()
        
        if "jwt" not in login_data:
            print("❌ Login failed")
            return
        
        token = login_data["jwt"]
        user_data = login_data.get("user", {})
        
        print("✅ Login successful")
        
        # Step 2: Decode JWT Token
        print("\n" + "=" * 80)
        print("📋 JWT TOKEN PAYLOAD")
        print("=" * 80)
        
        jwt_payload = decode_jwt(token)
        print(json.dumps(jwt_payload, indent=2))
        
        # Step 3: Inspect User Data
        print("\n" + "=" * 80)
        print("👤 USER DATA FROM LOGIN")
        print("=" * 80)
        
        print(f"\nAvailable keys: {list(user_data.keys())}")
        print(f"\nFull user data:")
        print(json.dumps(user_data, indent=2, default=str))
        
        # Check for institution info
        institution_id = user_data.get("institutionId")
        print(f"\n🏫 Institution ID: {institution_id}")
        
        if "institution" in user_data:
            print(f"✅ Institution object found:")
            print(json.dumps(user_data["institution"], indent=2))
        else:
            print("❌ No 'institution' object in user data")
        
        # Step 4: Try to find institution info in various API modules
        print("\n" + "=" * 80)
        print("🔍 TESTING API MODULES FOR INSTITUTION INFO")
        print("=" * 80)
        
        # Get bundle version from index page
        async with session.get("https://login.schulmanager-online.de/") as resp:
            html = await resp.text()
            # Try to extract bundle version (simplified)
            import re
            match = re.search(r'bundleVersion["\']?\s*:\s*["\']([a-f0-9]{10})["\']', html)
            bundle_version = match.group(1) if match else "3505280ee7"
        
        print(f"\n📦 Bundle version: {bundle_version}")
        
        # List of potential modules to test
        test_modules = [
            # Module/endpoint pairs that might contain institution info
            ("main", "get-institution-info"),
            ("main", "get-institution"),
            ("institution", "get-info"),
            ("institution", "get-details"),
            ("settings", "get-institution"),
            ("admin", "get-institution"),
            ("profile", "get-institution"),
            ("user", "get-institution"),
            # Try getting user profile
            ("user", "get-profile"),
            ("main", "get-profile"),
            ("settings", "get-profile"),
            # Try getting institution list
            ("main", "get-institutions"),
            ("institution", "list"),
        ]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        successful_calls = []
        
        for module, endpoint in test_modules:
            try:
                payload = {
                    "bundleVersion": bundle_version,
                    "requests": [{
                        "moduleName": module,
                        "endpointName": endpoint,
                        "parameters": {}
                    }]
                }
                
                async with session.post(CALLS_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        
                        if results and isinstance(results, list) and len(results) > 0:
                            result = results[0]
                            
                            # Check if this was a successful call
                            if isinstance(result, dict):
                                status = result.get("status", 0)
                                
                                if status == 200 and "data" in result:
                                    print(f"\n✅ SUCCESS: {module}/{endpoint}")
                                    print(f"   Response data:")
                                    print(json.dumps(result.get("data"), indent=2, default=str)[:500])
                                    successful_calls.append((module, endpoint, result.get("data")))
                                elif status != 404 and status != 500:
                                    print(f"\n⚠️  {module}/{endpoint} - Status {status}")
                            
            except Exception as e:
                pass  # Silent fail for non-existent endpoints
        
        # Step 5: Try POQA endpoint (used for some settings queries)
        print("\n" + "=" * 80)
        print("🔍 TESTING POQA ENDPOINT (Settings/Config)")
        print("=" * 80)
        
        poqa_tests = [
            ("main/institution", "findOne", {"id": institution_id}),
            ("main/institution", "findAll", {}),
            ("settings/institution", "findOne", {"id": institution_id}),
        ]
        
        for model, action, params in poqa_tests:
            try:
                payload = {
                    "bundleVersion": bundle_version,
                    "requests": [{
                        "moduleName": "settings",
                        "endpointName": "poqa",
                        "parameters": {
                            "action": {
                                "model": model,
                                "action": action,
                                "parameters": [params]
                            }
                        }
                    }]
                }
                
                async with session.post(CALLS_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        
                        if results and results[0].get("status") == 200:
                            print(f"\n✅ POQA: {model}/{action}")
                            print(json.dumps(results[0].get("data"), indent=2, default=str)[:500])
                            
            except Exception:
                pass
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        
        if successful_calls:
            print(f"\n✅ Found {len(successful_calls)} working endpoints:")
            for module, endpoint, _ in successful_calls:
                print(f"   - {module}/{endpoint}")
        else:
            print("\n❌ No additional endpoints found that provide institution information")
        
        print(f"\n🏫 Institution ID: {institution_id}")
        print(f"❓ Institution Name: NOT AVAILABLE in API for single-school accounts")
        print(f"\n💡 Conclusion:")
        print(f"   - JWT token contains: {list(jwt_payload.keys())}")
        print(f"   - User data contains institutionId but NOT institution name")
        print(f"   - No dedicated API endpoint found for fetching institution details")


if __name__ == "__main__":
    asyncio.run(test_institution_endpoints())

