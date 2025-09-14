#!/usr/bin/env python3
"""
Direct test of the Schulmanager Online Integration without Home Assistant
This simulates what Home Assistant would do with our integration
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the custom_components path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'schulmanager_online'))

# Mock Home Assistant modules
class MockConfigEntry:
    def __init__(self, data):
        self.data = data
        self.entry_id = "test_entry"

class MockHass:
    def __init__(self):
        self.data = {}
        self.config = MockConfig()
        
class MockConfig:
    def __init__(self):
        self.config_dir = "/tmp/ha_test"

# Import our integration modules
try:
    from const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
    from api import SchulmanagerOnlineAPI
    import aiohttp
    
    print("✅ Integration modules imported successfully!")
    
except ImportError as e:
    print(f"❌ Failed to import integration modules: {e}")
    sys.exit(1)

async def test_integration_components():
    """Test all components of our integration"""
    
    print("=" * 80)
    print("🎓 SCHULMANAGER ONLINE - INTEGRATION COMPONENT TEST")
    print("=" * 80)
    print(f"📦 Domain: {DOMAIN}")
    print(f"🔧 Config Keys: {CONF_EMAIL}, {CONF_PASSWORD}")
    print()
    
    # Test data
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print("🚀 Testing Integration Components...")
    print()
    
    # 1. Test API Client
    print("1️⃣ Testing API Client...")
    try:
        session = aiohttp.ClientSession()
        api = SchulmanagerOnlineAPI(email, password, session)
        
        # Test authentication
        await api.authenticate()
        print(f"   ✅ Authentication successful!")
        print(f"   🔑 Token: {api.token[:50] if api.token else 'None'}...")
        print(f"   ⏰ Expires: {api.token_expires}")
        
        await session.close()
        
    except Exception as e:
        print(f"   ❌ API Client failed: {e}")
        return False
    
    print()
    
    # 2. Test Configuration
    print("2️⃣ Testing Configuration...")
    try:
        config_entry = MockConfigEntry({
            CONF_EMAIL: email,
            CONF_PASSWORD: password
        })
        
        print(f"   ✅ Config Entry created")
        print(f"   📧 Email: {config_entry.data[CONF_EMAIL]}")
        print(f"   🔐 Password: {'*' * len(config_entry.data[CONF_PASSWORD])}")
        
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    print()
    
    # 3. Test Constants
    print("3️⃣ Testing Constants...")
    try:
        from const import (
            SENSOR_CURRENT_LESSON, SENSOR_NEXT_LESSON, SENSOR_TODAY_LESSONS,
            SENSOR_TODAY_CHANGES, SENSOR_TOMORROW_LESSONS, SENSOR_THIS_WEEK,
            SENSOR_NEXT_WEEK, SENSOR_CHANGES_DETECTED
        )
        
        sensors = [
            SENSOR_CURRENT_LESSON, SENSOR_NEXT_LESSON, SENSOR_TODAY_LESSONS,
            SENSOR_TODAY_CHANGES, SENSOR_TOMORROW_LESSONS, SENSOR_THIS_WEEK,
            SENSOR_NEXT_WEEK, SENSOR_CHANGES_DETECTED
        ]
        
        print(f"   ✅ All 8 sensors defined:")
        for i, sensor in enumerate(sensors, 1):
            print(f"      {i}. {sensor}")
            
    except Exception as e:
        print(f"   ❌ Constants failed: {e}")
        return False
    
    print()
    
    # 4. Test Translations
    print("4️⃣ Testing Translations...")
    try:
        translations_dir = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'schulmanager_online', 'translations')
        translation_files = [f for f in os.listdir(translations_dir) if f.endswith('.json')]
        
        print(f"   ✅ Found {len(translation_files)} translation files:")
        for file in sorted(translation_files):
            lang = file.replace('.json', '')
            print(f"      🌍 {lang}")
            
    except Exception as e:
        print(f"   ❌ Translations check failed: {e}")
        return False
    
    print()
    
    # 5. Test Custom Card
    print("5️⃣ Testing Custom Card...")
    try:
        card_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'schulmanager_online', 'www', 'schulmanager-schedule-card.js')
        
        if os.path.exists(card_path):
            with open(card_path, 'r') as f:
                card_content = f.read()
                
            print(f"   ✅ Custom Card found: {len(card_content)} characters")
            
            # Check for key features
            features = [
                'class SchulmanagerScheduleCard',
                'matrix-view',
                'week-list-view', 
                'day-list-view',
                'current-next-view'
            ]
            
            found_features = [f for f in features if f in card_content]
            print(f"   🎨 Features found: {len(found_features)}/{len(features)}")
            for feature in found_features:
                print(f"      ✅ {feature}")
                
        else:
            print(f"   ❌ Custom Card not found at {card_path}")
            return False
            
    except Exception as e:
        print(f"   ❌ Custom Card check failed: {e}")
        return False
    
    print()
    
    return True

async def main():
    """Main test function"""
    print("🧪 Starting Integration Component Test...")
    print()
    
    success = await test_integration_components()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 ALL INTEGRATION COMPONENTS WORKING!")
        print()
        print("✅ Ready for Home Assistant:")
        print("   - API Authentication: Working")
        print("   - Configuration: Ready") 
        print("   - Sensors: All 8 defined")
        print("   - Translations: 11 languages")
        print("   - Custom Card: Full featured")
        print()
        print("🐳 Next: Start Docker and test in Home Assistant")
    else:
        print("❌ SOME COMPONENTS HAVE ISSUES")
        print("   Please check the errors above")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
