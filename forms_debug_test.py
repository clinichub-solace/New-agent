#!/usr/bin/env python3
"""
Debug Forms API Issues
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "https://api-pathway.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

async def debug_forms():
    session = aiohttp.ClientSession()
    
    try:
        # Authenticate
        async with session.post(f"{API_BASE}/auth/login", json=TEST_CREDENTIALS) as response:
            if response.status == 200:
                data = await response.json()
                auth_token = data.get("access_token")
                print("✅ Authentication successful")
            else:
                print("❌ Authentication failed")
                return
                
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Create a simple form
        simple_form = {
            "name": "Debug Test Form",
            "key": "debug-test-form",
            "schema": {
                "fields": [
                    {
                        "key": "test_field",
                        "type": "text",
                        "label": "Test Field",
                        "required": True
                    }
                ]
            },
            "status": "draft",
            "version": 1
        }
        
        print("\n1. Creating form...")
        async with session.post(f"{API_BASE}/forms", headers=headers, json=simple_form) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Response: {response_text}")
            
            if response.status == 200:
                form_data = json.loads(response_text)
                form_id = form_data["_id"]
                print(f"✅ Form created with ID: {form_id}")
                
                # Test 2: Try to get the form by ID
                print(f"\n2. Getting form by ID: {form_id}")
                async with session.get(f"{API_BASE}/forms/{form_id}", headers=headers) as get_response:
                    print(f"Status: {get_response.status}")
                    get_text = await get_response.text()
                    print(f"Response: {get_text}")
                    
                # Test 3: Try to get the form by key
                print(f"\n3. Getting form by key: debug-test-form")
                async with session.get(f"{API_BASE}/forms/by-key/debug-test-form", headers=headers) as key_response:
                    print(f"Status: {key_response.status}")
                    key_text = await key_response.text()
                    print(f"Response: {key_text}")
                    
                # Test 4: Try to publish the form
                print(f"\n4. Publishing form...")
                async with session.post(f"{API_BASE}/forms/{form_id}/publish", headers=headers) as pub_response:
                    print(f"Status: {pub_response.status}")
                    pub_text = await pub_response.text()
                    print(f"Response: {pub_text}")
                    
                # Test 5: Check ObjectId validity
                print(f"\n5. Checking ObjectId validity...")
                print(f"Form ID: {form_id}, Length: {len(form_id)}")
                
                # Test 6: Try direct MongoDB query simulation
                print(f"\n6. Testing direct form lookup...")
                async with session.get(f"{API_BASE}/forms", headers=headers) as list_response:
                    if list_response.status == 200:
                        forms = await list_response.json()
                        print(f"Found {len(forms)} forms in database")
                        for form in forms:
                            if form.get("key") == "debug-test-form":
                                print(f"Found our form: ID={form['_id']}, Key={form['key']}")
                                break
                        else:
                            print("Our form not found in list")
            else:
                print("❌ Form creation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(debug_forms())