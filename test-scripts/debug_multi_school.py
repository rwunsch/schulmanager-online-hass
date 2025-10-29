#!/usr/bin/env python3
"""
Schulmanager Online Multi-School Debug & Diagnostic Tool

This script helps diagnose multi-school login issues and collects information
needed to fix integration problems. All sensitive data (passwords, tokens) is
automatically redacted before saving.

WHAT THIS SCRIPT DOES:
  1. Tests login with your credentials
  2. Detects if you have access to multiple schools
  3. Checks student data structure
  4. Tests API endpoints (optional)
  5. Saves redacted debug information to share with developers

USAGE:
  Basic test (single school):
    python3 debug_multi_school.py --email your@email.com --password 'YourPassword'
  
  Test with specific school (multi-school):
    python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --institution-id 12345
  
  Full diagnostic with API tests:
    python3 debug_multi_school.py --email your@email.com --password 'YourPassword' --full-test

OUTPUT:
  - Console: Human-readable summary
  - Files: debug-dumps/*.json (automatically redacted, safe to share)

PRIVACY:
  ✅ Passwords are NEVER saved to files
  ✅ JWT tokens are redacted (only last 8 chars shown)
  ✅ Email addresses are partially masked
  ✅ Student names can be optionally anonymized

For detailed instructions, see: documentation/Debug_Script_Guide.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API_BASE_URL = "https://login.schulmanager-online.de/"
SALT_URL = API_BASE_URL + "api/get-salt"
LOGIN_URL = API_BASE_URL + "api/login"
CALLS_URL = API_BASE_URL + "api/calls"


def _mask_email(email: str) -> str:
    """Mask email address for privacy: user@example.com -> u***@e***.com"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if "." in domain:
        domain_parts = domain.split(".")
        masked_domain = f"{domain_parts[0][0]}***." + ".".join(domain_parts[1:])
    else:
        masked_domain = f"{domain[0]}***"
    return f"{local[0]}***@{masked_domain}"


def _redact_token(token: str) -> str:
    """Redact JWT token, keeping only last 8 chars for identification"""
    if not token or len(token) < 16:
        return "[REDACTED]"
    return f"[REDACTED]...{token[-8:]}"


def _redact_data(data: Any, redact_names: bool = False) -> Any:
    """Recursively redact sensitive data from API responses"""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            # Always redact these fields
            if key_lower in ("password", "hash", "salt"):
                redacted[key] = "[REDACTED]"
            elif key_lower in ("jwt", "token", "authorization"):
                redacted[key] = _redact_token(str(value))
            elif key_lower == "email":
                redacted[key] = _mask_email(str(value))
            elif redact_names and key_lower in ("firstname", "lastname", "name"):
                redacted[key] = f"[STUDENT_{hash(str(value)) % 1000}]"
            else:
                redacted[key] = _redact_data(value, redact_names)
        return redacted
    elif isinstance(data, list):
        return [_redact_data(item, redact_names) for item in data]
    else:
        return data


def _dump_json(name: str, data: Any, redact_names: bool = False) -> None:
    """Save redacted JSON data to debug-dumps directory"""
    outdir = Path(__file__).parent / "debug-dumps"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / name
    
    redacted_data = _redact_data(data, redact_names)
    
    with path.open("w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.utcnow().isoformat(),
            "note": "Sensitive data has been automatically redacted for privacy",
            "data": redacted_data
        }, f, ensure_ascii=False, indent=2)


def pbkdf2_sha512_hex(password: str, salt: str) -> str:
    pw_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha512", pw_bytes, salt_bytes, 99999, dklen=512)
    return dk.hex()


def get_salt(email: str, institution_id: Optional[int] = None) -> str:
    payload = {"emailOrUsername": email, "mobileApp": False, "institutionId": institution_id}
    r = requests.post(SALT_URL, json=payload, timeout=30)
    try:
        data = r.json()
    except Exception:
        data = r.text
    filename = f"01_get_salt_response{'_inst_' + str(institution_id) if institution_id else ''}.json"
    _dump_json(filename, {"status": r.status_code, "body": data if isinstance(data, dict) else str(data)[:500]})
    if r.status_code != 200:
        raise RuntimeError(f"get-salt failed: {r.status_code}")
    if isinstance(data, str):
        return data
    salt = (data or {}).get("salt")
    if not salt:
        raise RuntimeError("no salt in response")
    return salt


def login(email: str, password: str, hash_hex: str, institution_id: Optional[int]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "emailOrUsername": email,
        "password": password,
        "hash": hash_hex,
        "mobileApp": False,
        "institutionId": institution_id,
    }
    r = requests.post(LOGIN_URL, json=payload, timeout=60)
    txt = r.text
    try:
        data = r.json()
    except Exception:
        data = {"raw_text": txt[:1000]}
    _dump_json("02_login_response.json", {"status": r.status_code, "body": data})
    if r.status_code != 200:
        raise RuntimeError(f"login failed: {r.status_code}")
    return data


def calls(token: str, requests_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = {"bundleVersion": "auto", "requests": requests_payload}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(CALLS_URL, json=payload, headers=headers, timeout=60)
    txt = r.text
    try:
        data = r.json()
    except Exception:
        data = {"raw_text": txt[:1000]}
    return {"status": r.status_code, "body": data}


def detect_js_bundle_version() -> Optional[str]:
    try:
        r = requests.get(API_BASE_URL, timeout=30)
        if r.status_code != 200:
            return None
        html = r.text
        # naive search for 10-hex bundle near api/calls
        m = re.search(r"bundleVersion\s*[:=]\s*\"([a-f0-9]{10})\"", html, re.IGNORECASE)
        if m:
            return m.group(1)
        # fallback: search common assets
        m2 = re.search(r"/assets/[^\"']+\.js", html)
        if not m2:
            return None
        js_url = API_BASE_URL.rstrip("/") + m2.group(0)
        r2 = requests.get(js_url, timeout=30)
        if r2.status_code != 200:
            return None
        m3 = re.search(r"bundleVersion\s*[:=]\s*\"([a-f0-9]{10})\"", r2.text, re.IGNORECASE)
        return m3.group(1) if m3 else None
    except Exception:
        return None


def probe_endpoints(token: str, student: Dict[str, Any], weeks: int, do: List[str]) -> None:
    sid = int(student.get("id"))
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_range = start_of_week + timedelta(days=(7 * max(1, min(weeks, 4))) - 1)

    bundle = detect_js_bundle_version() or "3505280ee7"

    def reqs(mod: str, ep: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"moduleName": mod, "endpointName": ep, "parameters": params}]

    if "schedule" in do:
        payload = reqs("schedules", "get-actual-lessons", {"student": student, "start": start_of_week.isoformat(), "end": end_of_range.isoformat()})
        res = calls(token, payload)
        _dump_json("10_schedule_response.json", res)

    if "classhours" in do or "classhours" in do:
        payload = reqs("schedules", "get-class-hours", {})
        res = requests.post(CALLS_URL, json={"bundleVersion": bundle, "requests": payload}, headers={"Authorization": f"Bearer {token}"}, timeout=60)
        try:
            data = res.json()
        except Exception:
            data = {"raw_text": res.text[:1000]}
        _dump_json("11_class_hours_response.json", {"status": res.status_code, "body": data})

    if "homework" in do:
        payload = reqs("classbook", "get-homework", {"student": {"id": sid}})
        res = calls(token, payload)
        _dump_json("12_homework_response.json", res)

    if "exams" in do:
        payload = reqs("exams", "get-exams", {"student": {"id": sid}, "start": start_of_week.isoformat(), "end": (start_of_week + timedelta(days=56)).isoformat()})
        res = requests.post(CALLS_URL, json={"bundleVersion": bundle, "requests": payload}, headers={"Authorization": f"Bearer {token}"}, timeout=60)
        try:
            data = res.json()
        except Exception:
            data = {"raw_text": res.text[:1000]}
        _dump_json("13_exams_response.json", {"status": res.status_code, "body": data})

    if "letters" in do:
        payload = [
            {"moduleName": None, "endpointName": "user-can-get-notifications"},
            {"moduleName": "letters", "endpointName": "get-letters"},
        ]
        res = calls(token, payload)
        _dump_json("14_letters_response.json", res)


def print_banner():
    """Print welcome banner with instructions"""
    print("=" * 80)
    print("  Schulmanager Online Multi-School Debug Tool")
    print("=" * 80)
    print()
    print("This tool will:")
    print("  1. Test your login credentials")
    print("  2. Check if you have access to multiple schools")
    print("  3. Analyze student data structure")
    print("  4. Optionally test API endpoints")
    print()
    print("All sensitive data (passwords, tokens) will be automatically redacted.")
    print("=" * 80)
    print()


def print_summary(has_multi_school: bool, institution_id: Optional[int], students: List[Dict], user: Dict):
    """Print human-readable summary of findings"""
    print()
    print("=" * 80)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print()
    
    print(f"✓ Login Status: SUCCESS")
    print(f"✓ User ID: {user.get('id', 'Unknown')}")
    print(f"✓ Institution ID: {institution_id or user.get('institutionId', 'Not found')}")
    print()
    
    if has_multi_school:
        print("⚠️  MULTI-SCHOOL ACCOUNT DETECTED")
        print("   Your account has access to multiple schools.")
        print("   You must select one school during integration setup.")
        print()
        print("📋 NEXT STEPS FOR HOME ASSISTANT INTEGRATION:")
        print("   1. When adding the integration in Home Assistant:")
        print("      - Enter your email and password")
        print("      - You SHOULD see a school selection dropdown")
        print("      - Select the school you want to monitor")
        print()
        print("   2. If the school selection dropdown does NOT appear:")
        print("      - This is the bug! Please report it with these debug files.")
        print("      - Enable debug logging in Home Assistant (see Debug_Script_Guide.md)")
        print("      - Try to add the integration again")
        print("      - Download diagnostics from HA")
        print("      - Report issue at: https://github.com/rwunsch/schulmanager-online-hass/issues")
        print()
        print("   3. To monitor BOTH schools:")
        print("      - Add the integration TWICE (once for each school)")
        print("      - Use the SAME credentials both times")
        print("      - Select different school each time")
    else:
        print("✓ Single School Account")
        print("   Your account accesses one school only.")
        print("   Standard integration setup should work.")
    print()
    
    print(f"✓ Students Found: {len(students)}")
    for i, st in enumerate(students, 1):
        print(f"   {i}. {st.get('firstname', '')} {st.get('lastname', '')} (ID: {st.get('id')})")
        if 'institutionId' in st:
            print(f"      ⚠️  Student has institutionId: {st['institutionId']}")
        else:
            print(f"      ✓ Student has NO institutionId field (expected)")
    print()
    
    print("✓ Debug files saved to: test-scripts/debug-dumps/")
    print("  These files are safe to share - all sensitive data is redacted.")
    print()
    print("📤 TO REPORT AN ISSUE:")
    print("   1. Go to: https://github.com/rwunsch/schulmanager-online-hass/issues")
    print("   2. Create a new issue with title: 'Multi-school login issue'")
    print("   3. Attach ALL files from test-scripts/debug-dumps/ folder")
    print("   4. Copy-paste this console output")
    print("   5. If possible, also attach Home Assistant diagnostics:")
    print("      Settings → Integrations → Schulmanager → Download Diagnostics")
    print()
    print("=" * 80)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Schulmanager Online Multi-School Debug Tool",
        epilog="Example: python3 debug_multi_school.py --email user@example.com --password 'secret'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--email", required=True, help="Your Schulmanager login email")
    ap.add_argument("--password", required=True, help="Your Schulmanager password")
    ap.add_argument("--institution-id", type=int, default=None, 
                    help="Institution ID (only needed if you have multiple schools)")
    ap.add_argument("--full-test", action="store_true",
                    help="Run full API endpoint tests (schedule, homework, exams, letters)")
    ap.add_argument("--anonymize-names", action="store_true",
                    help="Replace student names with anonymous IDs in output files")
    ap.add_argument("--weeks", type=int, default=2,
                    help="Number of weeks to fetch for schedule/exams (default: 2)")
    args = ap.parse_args()

    print_banner()

    try:
        print("Step 1/5: Fetching salt for password hashing...")
        salt = get_salt(args.email)
        print(f"         ✓ Salt received ({len(salt)} characters)")
        print()

        print("Step 2/5: Computing PBKDF2-SHA512 hash (99,999 iterations)...")
        hash_hex = pbkdf2_sha512_hex(args.password, salt)
        print(f"         ✓ Hash computed ({len(hash_hex)} characters)")
        print()

        print("Step 3/5: Testing login (checking for multiple schools)...")
        data = login(args.email, args.password, hash_hex, institution_id=None)
        
        has_multi_school = False
        selected_inst_id = args.institution_id
        
        if isinstance(data, dict) and "multipleAccounts" in data:
            has_multi_school = True
            accounts = data.get("multipleAccounts") or []
            print(f"         ⚠️  MULTI-SCHOOL ACCOUNT DETECTED!")
            print(f"         Found {len(accounts)} schools:")
            for a in accounts:
                print(f"            - ID: {a.get('id'):5d}  Name: {a.get('label')}")
            
            if selected_inst_id is None:
                print()
                print("         ERROR: You have multiple schools but didn't specify which one.")
                print("         Please re-run with: --institution-id <ID>")
                print()
                print("         Example:")
                print(f"            python3 debug_multi_school.py --email {args.email} \\")
                print(f"                --password 'YOUR_PASSWORD' --institution-id {accounts[0].get('id')}")
                return 2
            
            print()
            print(f"Step 3b/5: Re-fetching salt with Institution ID {selected_inst_id}...")
            salt = get_salt(args.email, institution_id=selected_inst_id)
            print(f"         ✓ Institution-specific salt received ({len(salt)} characters)")
            
            print()
            print(f"Step 3c/5: Re-computing hash with institution-specific salt...")
            hash_hex = pbkdf2_sha512_hex(args.password, salt)
            print(f"         ✓ Institution-specific hash computed ({len(hash_hex)} characters)")
            
            print()
            print(f"Step 3d/5: Re-authenticating with Institution ID {selected_inst_id}...")
            data = login(args.email, args.password, hash_hex, institution_id=selected_inst_id)

        token = data.get("jwt") or data.get("token")
        if not token:
            print("         ✗ ERROR: Login did not return a JWT token")
            return 3
        
        print(f"         ✓ Login successful (token: ...{token[-8:]})")
        print()

        print("Step 4/6: Analyzing user and student data...")
        user = data.get("user", {})
        students: List[Dict[str, Any]] = []
        
        # Extract students from associatedParents
        for p in user.get("associatedParents", []) or []:
            st = (p or {}).get("student")
            if st:
                students.append(st)
        
        # Check for associatedStudent (student account)
        if not students and user.get("associatedStudent"):
            students.append(user.get("associatedStudent"))
        
        print(f"         ✓ Found {len(students)} student(s)")
        
        # Check for institutionId in various places
        user_inst_id = user.get("institutionId")
        if user_inst_id:
            print(f"         ✓ User object has institutionId: {user_inst_id}")
        
        for st in students:
            if "institutionId" in st:
                print(f"         ⚠️  UNEXPECTED: Student {st.get('id')} has institutionId: {st['institutionId']}")
            else:
                print(f"         ✓ Student {st.get('id')} has NO institutionId (expected)")
        
        _dump_json("03_login_parsed_user.json", {
            "has_multi_school": has_multi_school,
            "selected_institution_id": selected_inst_id or user_inst_id,
            "user": user,
            "students": students,
            "student_count": len(students)
        }, redact_names=args.anonymize_names)
        print()

        if students and args.full_test:
            print("Step 5/6: Testing API endpoints...")
            probe_list = ["schedule", "homework", "exams", "letters", "classhours"]
            probe_endpoints(token, students[0], args.weeks, probe_list)
            print("         ✓ API tests complete")
        elif students:
            print("Step 5/6: Skipping API endpoint tests (use --full-test to enable)")
        else:
            print("Step 5/6: Skipping API tests (no students found)")
        
        print()
        print_summary(has_multi_school, selected_inst_id or user_inst_id, students, user)
        
        return 0
    
    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


