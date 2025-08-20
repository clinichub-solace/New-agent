#!/usr/bin/env python3
"""
Test Forms Validation Error Handling
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "https://medical-practice-hub-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

async def test_validation():
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
        
        # Get a published form to test with
        async with session.get(f"{API_BASE}/forms?status=published&limit=1", headers=headers) as response:
            if response.status == 200:
                forms = await response.json()
                if forms:
                    form = forms[0]
                    form_id = form["_id"]
                    print(f"✅ Found published form: {form['name']} (ID: {form_id})")
                    
                    # Test validation with missing required fields
                    invalid_data = {
                        "data": {
                            "first_name": "Test"
                            # Missing other required fields
                        }
                    }
                    
                    print("\n🧪 Testing validation with missing required fields...")
                    async with session.post(f"{API_BASE}/forms/{form_id}/submit", headers=headers, json=invalid_data) as submit_response:
                        print(f"Status: {submit_response.status}")
                        response_text = await submit_response.text()
                        print(f"Response: {response_text}")
                        
                        if submit_response.status == 400:
                            try:
                                error_data = json.loads(response_text)
                                print(f"Error data structure: {error_data}")
                                if "validation_errors" in error_data:
                                    print(f"✅ Found validation_errors: {error_data['validation_errors']}")
                                else:
                                    print(f"❌ No validation_errors field found. Available fields: {list(error_data.keys())}")
                            except json.JSONDecodeError:
                                print(f"❌ Response is not valid JSON")
                        else:
                            print(f"❌ Expected 400 status, got {submit_response.status}")
                            
                    # Test validation with invalid data types
                    invalid_types_data = {
                        "data": {
                            "first_name": "Test",
                            "last_name": "User", 
                            "email": "not-an-email",
                            "phone": "123",
                            "date_of_birth": "not-a-date",
                            "emergency_contact": "Contact",
                            "emergency_phone": "(555) 123-4567",
                            "consent_treatment": True,
                            "consent_privacy": True
                        }
                    }
                    
                    print("\n🧪 Testing validation with invalid data types...")
                    async with session.post(f"{API_BASE}/forms/{form_id}/submit", headers=headers, json=invalid_types_data) as submit_response:
                        print(f"Status: {submit_response.status}")
                        response_text = await submit_response.text()
                        print(f"Response: {response_text}")
                        
                        if submit_response.status == 400:
                            try:
                                error_data = json.loads(response_text)
                                print(f"Error data structure: {error_data}")
                                if "validation_errors" in error_data:
                                    print(f"✅ Found validation_errors: {error_data['validation_errors']}")
                                else:
                                    print(f"❌ No validation_errors field found. Available fields: {list(error_data.keys())}")
                            except json.JSONDecodeError:
                                print(f"❌ Response is not valid JSON")
                        else:
                            print(f"❌ Expected 400 status, got {submit_response.status}")
                            
                else:
                    print("❌ No published forms found")
            else:
                print("❌ Failed to get forms")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_validation())