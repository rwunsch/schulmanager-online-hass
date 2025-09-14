#!/usr/bin/env python3
"""
Test script to interact with Home Assistant and test our Schulmanager integration
"""

import asyncio
import aiohttp
import json
import time

class HomeAssistantTester:
    def __init__(self, base_url="http://localhost:8123"):
        self.base_url = base_url
        self.session = None
        self.token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def wait_for_ha_ready(self, max_attempts=30):
        """Wait for Home Assistant to be ready"""
        print("🏠 Waiting for Home Assistant to be ready...")
        
        for attempt in range(max_attempts):
            try:
                async with self.session.get(f"{self.base_url}/api/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Home Assistant ready! Version: {data.get('version', 'unknown')}")
                        return True
            except Exception as e:
                pass
                
            print(f"   Attempt {attempt + 1}/{max_attempts} - waiting...")
            await asyncio.sleep(2)
        
        return False
    
    async def get_integrations(self):
        """Get list of loaded integrations"""
        try:
            async with self.session.get(f"{self.base_url}/api/config/integrations") as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"❌ Failed to get integrations: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting integrations: {e}")
            return None
    
    async def get_entities(self):
        """Get all entities"""
        try:
            async with self.session.get(f"{self.base_url}/api/states") as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"❌ Failed to get entities: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting entities: {e}")
            return None
    
    async def check_schulmanager_entities(self):
        """Check for Schulmanager entities"""
        entities = await self.get_entities()
        if not entities:
            return []
        
        schulmanager_entities = [
            entity for entity in entities 
            if entity.get('entity_id', '').startswith('sensor.schulmanager_') or
               entity.get('entity_id', '').startswith('calendar.schulmanager_')
        ]
        
        return schulmanager_entities
    
    async def test_integration_status(self):
        """Test the current status of our integration"""
        print("=" * 80)
        print("🎓 SCHULMANAGER ONLINE - HOME ASSISTANT INTEGRATION TEST")
        print("=" * 80)
        
        # 1. Check if HA is ready
        if not await self.wait_for_ha_ready():
            print("❌ Home Assistant not ready after waiting")
            return False
        
        print()
        
        # 2. Check integrations
        print("🔌 Checking loaded integrations...")
        integrations = await self.get_integrations()
        if integrations:
            print(f"   Found {len(integrations)} integrations")
            
            # Look for our integration
            schulmanager_found = any(
                'schulmanager' in str(integration).lower() 
                for integration in integrations
            )
            
            if schulmanager_found:
                print("   ✅ Schulmanager integration found!")
            else:
                print("   ⚠️  Schulmanager integration not yet configured")
        
        print()
        
        # 3. Check entities
        print("📊 Checking for Schulmanager entities...")
        schulmanager_entities = await self.check_schulmanager_entities()
        
        if schulmanager_entities:
            print(f"   ✅ Found {len(schulmanager_entities)} Schulmanager entities:")
            for entity in schulmanager_entities:
                entity_id = entity.get('entity_id')
                state = entity.get('state')
                print(f"      - {entity_id}: {state}")
        else:
            print("   ⚠️  No Schulmanager entities found yet")
            print("   💡 This is expected if the integration isn't configured")
        
        print()
        
        # 4. Check custom components directory
        print("📁 Integration files should be available at:")
        print("   /config/custom_components/schulmanager_online/")
        print("   - manifest.json")
        print("   - __init__.py")
        print("   - api.py")
        print("   - sensor.py")
        print("   - calendar.py")
        print("   - config_flow.py")
        print("   - www/schulmanager-schedule-card.js")
        
        print()
        print("=" * 80)
        print("🎯 NEXT STEPS:")
        print("1. Open Home Assistant at http://localhost:8123")
        print("2. Go to Settings > Devices & Services")
        print("3. Click '+ ADD INTEGRATION'")
        print("4. Search for 'Schulmanager Online'")
        print("5. Configure with your credentials:")
        print("   - Email: <schulmanager-login>")
        print("   - Password: <schulmanager-password>")
        print("=" * 80)
        
        return True

async def main():
    """Main test function"""
    print("🧪 Starting Home Assistant Integration Test...")
    print()
    
    async with HomeAssistantTester() as tester:
        success = await tester.test_integration_status()
        
        if success:
            print("\n🎉 Home Assistant is ready for integration testing!")
        else:
            print("\n❌ Issues found with Home Assistant setup")
        
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
