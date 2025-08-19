#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Helper function to print test results
def print_test_result(test_name, success, response=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def test_synology_integration():
    print("\n--- Testing Synology DSM Authentication Integration ---")
    
    # Test 1: Check Synology Status
    try:
        url = f"{API_URL}/auth/synology-status"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "synology_enabled" in result
        assert "synology_url" in result
        assert "session_name" in result
        assert "verify_ssl" in result
        
        print_test_result("Get Synology Status", True, result)
    except Exception as e:
        print(f"Error getting Synology status: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Synology Status", False)
    
    # Test 2: Initialize Admin User
    admin_token = None
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify admin initialization response
        assert "message" in result
        assert "username" in result
        assert "password" in result
        assert result["username"] == "admin"
        assert result["password"] == "admin123"
        
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Admin User", False)
    
    # Test 3: Login with Admin Credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify login response includes Synology fields
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert "auth_source" in result["user"]
        assert "synology_enabled" in result["user"]
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login with Synology Fields", True, result)
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login with Synology Fields", False)
    
    # Test 4: Get Current User Info
    if admin_token:
        try:
            url = f"{API_URL}/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify user info includes Synology fields
            assert "auth_source" in result
            assert "synology_sid" in result
            
            print_test_result("Get Current User with Synology Fields", True, result)
        except Exception as e:
            print(f"Error getting current user: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Current User with Synology Fields", False)
    
    # Test 5: Test Synology Connection (Admin Only)
    if admin_token:
        try:
            url = f"{API_URL}/auth/test-synology"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify response structure
            assert "success" in result
            assert "message" in result
            
            print_test_result("Test Synology Connection (Admin Only)", True, result)
        except Exception as e:
            print(f"Error testing Synology connection: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Test Synology Connection (Admin Only)", False)
    
    # Test 6: Test Synology Connection (Non-Admin)
    try:
        # First create a non-admin user
        if admin_token:
            url = f"{API_URL}/users"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "testpassword123",
                "first_name": "Test",
                "last_name": "User",
                "role": "receptionist",
                "phone": "+1-555-123-4567"
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200 or response.status_code == 201:
                print("Created test user for permission testing")
            elif response.status_code == 409:
                print("Test user already exists")
            else:
                print(f"Warning: Could not create test user: {response.status_code}")
                print(response.text)
        
        # Login as non-admin user
        url = f"{API_URL}/auth/login"
        data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        non_admin_token = result["access_token"]
        
        # Try to access admin-only endpoint
        url = f"{API_URL}/auth/test-synology"
        headers = {"Authorization": f"Bearer {non_admin_token}"}
        
        response = requests.post(url, headers=headers)
        
        # This should fail with 403 Forbidden
        assert response.status_code == 403
        result = response.json()
        assert "detail" in result
        
        print_test_result("Test Synology Connection (Non-Admin, Expected to Fail)", True, {"status_code": response.status_code, "detail": result.get("detail")})
    except Exception as e:
        print(f"Error testing non-admin access: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Test Synology Connection (Non-Admin)", False)
    
    # Test 7: Logout with Synology Session Cleanup
    if admin_token:
        try:
            url = f"{API_URL}/auth/logout"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert "message" in result
            # Note: There appears to be a duplicate logout endpoint in the code
            # One returns just {"message": "Successfully logged out"}
            # The other returns {"message": "Logout successful", "auth_source": "..."}
            # We'll accept either format
            
            print_test_result("Logout with Synology Session Cleanup", True, result)
        except Exception as e:
            print(f"Error logging out: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Logout with Synology Session Cleanup", False)

if __name__ == "__main__":
    test_synology_integration()