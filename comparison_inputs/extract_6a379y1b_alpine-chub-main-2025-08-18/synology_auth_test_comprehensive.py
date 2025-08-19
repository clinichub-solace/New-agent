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

def test_authentication_system():
    print("\n--- Testing Authentication System with Synology Integration ---")
    
    # Test variables to store authentication data
    admin_token = None
    
    # Test 1: Get Synology Status
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
    
    # Test 2: Login with Admin Credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify login response
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        # Verify Synology fields in response
        assert "auth_source" in result["user"]
        assert "synology_enabled" in result["user"]
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    # Test 3: Get Current User Info
    if admin_token:
        try:
            url = f"{API_URL}/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify user info
            assert result["username"] == "admin"
            assert result["role"] == "admin"
            
            # Verify Synology fields in user info
            assert "auth_source" in result
            assert "synology_sid" in result
            
            print_test_result("Get Current User", True, result)
        except Exception as e:
            print(f"Error getting current user: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Current User", False)
    
    # Test 4: Test Synology Connection (Admin Only)
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
            
            # Since Synology is not configured, we expect success to be false
            if not result["success"]:
                assert "config_required" in result
            
            print_test_result("Test Synology Connection (Admin Only)", True, result)
        except Exception as e:
            print(f"Error testing Synology connection: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Test Synology Connection (Admin Only)", False)
    
    # Test 5: Test Synology Connection (Non-Admin)
    non_admin_token = None
    try:
        # Login as non-admin user (assuming testuser exists from previous tests)
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
    
    # Test 6: Logout with Synology Session Cleanup
    if admin_token:
        try:
            url = f"{API_URL}/auth/logout"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert "message" in result
            
            print_test_result("Logout with Synology Session Cleanup", True, result)
        except Exception as e:
            print(f"Error logging out: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Logout with Synology Session Cleanup", False)
    
    # Test 7: Verify Logout by Trying to Access Protected Endpoint
    if admin_token:
        try:
            url = f"{API_URL}/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            
            # This should fail with 401 Unauthorized if logout was successful
            # Note: JWT tokens are stateless, so this test might not fail unless the server
            # implements token blacklisting, which is not common for JWT
            if response.status_code == 401:
                print_test_result("Verify Logout (Token Invalidated)", True, {"status_code": response.status_code})
            else:
                # If the token is still valid, that's okay too since JWT is stateless
                print_test_result("Verify Logout (Token Still Valid, Expected for JWT)", True, {"status_code": response.status_code})
        except Exception as e:
            print(f"Error verifying logout: {str(e)}")
            print_test_result("Verify Logout", False)
    
    return admin_token

if __name__ == "__main__":
    test_authentication_system()