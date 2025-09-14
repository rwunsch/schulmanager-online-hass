#!/usr/bin/env python3
"""
Test der korrigierten Hash-Implementierung ohne Home Assistant Dependencies
"""

import asyncio
import aiohttp
import hashlib
import json

class SchulmanagerAPIError(Exception):
    """Custom exception for API errors"""
    pass

async def test_corrected_authentication():
    """Test the corrected authentication with proper hash implementation"""
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("=" * 80)
    print("🎓 SCHULMANAGER ONLINE - KORRIGIERTE HASH-IMPLEMENTIERUNG TEST")
    print("=" * 80)
    print(f"📧 Email: {email}")
    print(f"🔐 Password: {password}")
    print()
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Get Salt
            salt_url = "https://login.schulmanager-online.de/api/get-salt"
            salt_payload = {
                "emailOrUsername": email,
                "mobileApp": False,
                "institutionId": None
            }
            
            print("🧂 Hole Salt...")
            async with session.post(salt_url, json=salt_payload) as response:
                if response.status != 200:
                    raise SchulmanagerAPIError(f"Salt request failed: {response.status}")
                
                try:
                    data = await response.json()
                    salt = data if isinstance(data, str) else data.get("salt")
                except:
                    salt = await response.text()
                
                print(f"✅ Salt erhalten: {len(salt)} Zeichen")
            
            # 2. Generate corrected hash
            print("🔐 Generiere korrigierten Hash...")
            print(f"   - PBKDF2 mit SHA-512")
            print(f"   - 512 Bytes Output (1024 Hex-Zeichen)")
            print(f"   - Salt als UTF-8 (nicht Hex!)")
            print(f"   - 99999 Iterationen")
            
            # Corrected implementation
            password_bytes = password.encode('utf-8')
            salt_bytes = salt.encode('utf-8')  # UTF-8, not hex!
            hash_bytes = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 99999, dklen=512)
            hash_hex = hash_bytes.hex()
            
            print(f"✅ Hash generiert: {len(hash_hex)} Zeichen")
            print(f"🔐 Hash (erste 100): {hash_hex[:100]}...")
            
            # 3. Test Login
            login_url = "https://login.schulmanager-online.de/api/login"
            login_payload = {
                "emailOrUsername": email,
                "password": password,
                "hash": hash_hex,
                "mobileApp": False,
                "institutionId": None
            }
            
            headers = {
                'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json',
                'origin': 'https://login.schulmanager-online.de',
                'referer': 'https://login.schulmanager-online.de/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print("🔑 Teste Login...")
            async with session.post(login_url, json=login_payload, headers=headers) as response:
                print(f"📥 Login Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    token = data.get("jwt") or data.get("token")
                    user = data.get("user", {})
                    
                    print("🎉 LOGIN ERFOLGREICH!")
                    print(f"👤 User: {user.get('firstname')} {user.get('lastname')}")
                    print(f"🔑 Token: {token[:50] if token else 'None'}...")
                    
                    return True
                else:
                    response_text = await response.text()
                    print(f"❌ Login fehlgeschlagen: {response.status}")
                    print(f"📥 Response: {response_text[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"💥 Fehler: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test function"""
    print("🚀 Starte Test der korrigierten Hash-Implementierung...")
    print()
    
    success = await test_corrected_authentication()
    
    print()
    print("=" * 80)
    if success:
        print("🎯 ERFOLG: API-AUTHENTIFIZIERUNG VOLLSTÄNDIG GELÖST!")
        print("✅ Alle Probleme behoben:")
        print("   - Salt-Encoding: UTF-8 statt Hex")
        print("   - Hash-Länge: 1024 Zeichen (512 Bytes)")
        print("   - Iterationen: 99999 statt 10000")
        print("   - JWT Token: Korrekt erkannt")
    else:
        print("💥 FEHLER: Authentifizierung noch nicht vollständig gelöst")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
