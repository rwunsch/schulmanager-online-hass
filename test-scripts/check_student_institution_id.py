#!/usr/bin/env python3
"""Check if student objects contain institutionId field."""

import asyncio
import hashlib
import json
import aiohttp

API_BASE_URL = "https://login.schulmanager-online.de"
SALT_URL = f"{API_BASE_URL}/api/get-salt"
LOGIN_URL = f"{API_BASE_URL}/api/login"

EMAIL = "wunsch@gmx.de"
PASSWORD = "Gjns26twr+9_R@Y"


def generate_salted_hash(password: str, salt: str) -> str:
    """Generate PBKDF2-SHA512 hash."""
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
    return hash_bytes.hex()


async def check_student_data():
    """Check what data students have."""
    async with aiohttp.ClientSession() as session:
        # Get salt
        async with session.post(SALT_URL, json={
            "emailOrUsername": EMAIL,
            "mobileApp": False,
            "institutionId": None
        }) as response:
            salt_text = await response.text()
            salt = json.loads(salt_text) if salt_text.startswith('"') else salt_text
            salt = salt.strip('"') if isinstance(salt, str) else salt
        
        # Generate hash
        salted_hash = generate_salted_hash(PASSWORD, salt)
        
        # Login
        async with session.post(LOGIN_URL, json={
            "emailOrUsername": EMAIL,
            "password": PASSWORD,
            "hash": salted_hash,
            "mobileApp": False,
            "institutionId": None
        }) as response:
            login_data = await response.json()
        
        print("=" * 80)
        print("STUDENT DATA STRUCTURE ANALYSIS")
        print("=" * 80)
        
        user_data = login_data.get("user", {})
        
        print(f"\n📋 User Level Data:")
        print(f"   - User ID: {user_data.get('id')}")
        print(f"   - User institutionId: {user_data.get('institutionId')}")
        print()
        
        # Extract students
        students = []
        
        # From associatedParents
        for parent in user_data.get("associatedParents", []):
            student = parent.get("student")
            if student:
                students.append(("associatedParents", student))
        
        # From associatedStudent
        if user_data.get("associatedStudent"):
            students.append(("associatedStudent", user_data.get("associatedStudent")))
        
        print(f"📋 Found {len(students)} student(s)\n")
        
        for i, (source, student) in enumerate(students, 1):
            print(f"{'=' * 80}")
            print(f"STUDENT {i} (from {source})")
            print(f"{'=' * 80}")
            print(f"\nBasic Info:")
            print(f"   - ID: {student.get('id')}")
            print(f"   - Name: {student.get('firstname')} {student.get('lastname')}")
            print(f"   - Class ID: {student.get('classId')}")
            
            print(f"\nInstitution Info:")
            if 'institutionId' in student:
                print(f"   ✅ HAS institutionId: {student.get('institutionId')}")
            else:
                print(f"   ❌ NO institutionId field in student object")
            
            print(f"\nAll Fields in Student Object:")
            for key in sorted(student.keys()):
                value = student.get(key)
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"   - {key}: {value}")
            
            print(f"\nFull JSON:")
            print(json.dumps(student, indent=2, default=str))
            print()
        
        # Check parent objects too
        print(f"{'=' * 80}")
        print("PARENT DATA (from associatedParents)")
        print(f"{'=' * 80}\n")
        
        for i, parent in enumerate(user_data.get("associatedParents", []), 1):
            print(f"Parent {i}:")
            print(f"   - ID: {parent.get('id')}")
            print(f"   - Name: {parent.get('firstname')} {parent.get('lastname')}")
            
            if 'institutionId' in parent:
                print(f"   ✅ HAS institutionId: {parent.get('institutionId')}")
            else:
                print(f"   ❌ NO institutionId field")
            
            print(f"   - All fields: {list(parent.keys())}")
            print()


if __name__ == "__main__":
    asyncio.run(check_student_data())

