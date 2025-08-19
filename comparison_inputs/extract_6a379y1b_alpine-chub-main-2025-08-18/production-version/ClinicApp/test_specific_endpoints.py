#!/usr/bin/env python3
import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
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

# Test Authentication to get token
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        if response.status_code == 400:
            # Admin already exists, this is fine
            print("Admin user already exists, proceeding to login")
        else:
            response.raise_for_status()
            result = response.json()
            print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Admin User", False)
    
    # Test 2: Login with Admin Credentials
    admin_token = None
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    return admin_token

# Test Calendar View Endpoint
def test_calendar_view(admin_token):
    print("\n--- Testing Calendar View Endpoint ---")
    
    # Test with parameters
    try:
        url = f"{API_URL}/appointments/calendar"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "date": "2025-01-15",
            "view": "week"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "view" in result
        assert "start_date" in result
        assert "end_date" in result
        assert "appointments" in result
        
        print_test_result("Calendar View with Parameters", True, result)
    except Exception as e:
        print(f"Error getting calendar view with parameters: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Calendar View with Parameters", False)
    
    # Test without parameters
    try:
        url = f"{API_URL}/appointments/calendar"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        
        # Check if it returns 422 (missing required parameter) or other error
        if response.status_code == 422:
            print_test_result("Calendar View without Parameters", True, 
                             {"status_code": response.status_code, 
                              "detail": "Missing required parameter 'date' as expected"})
        else:
            response.raise_for_status()
            result = response.json()
            print_test_result("Calendar View without Parameters", True, result)
    except Exception as e:
        print(f"Error getting calendar view without parameters: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Calendar View without Parameters", False)

# Test Communications Templates Endpoint
def test_communications_templates(admin_token):
    print("\n--- Testing Communications Templates Endpoint ---")
    
    # First, initialize templates if needed
    try:
        url = f"{API_URL}/communications/init-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Communication Templates", True, result)
    except Exception as e:
        print(f"Error initializing communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Communication Templates", False)
    
    # Test getting templates
    try:
        url = f"{API_URL}/communications/templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify templates are returned
        assert isinstance(result, list)
        if len(result) > 0:
            assert "id" in result[0]
            assert "name" in result[0]
            assert "message_type" in result[0]
            assert "subject_template" in result[0]
            assert "content_template" in result[0]
        
        print_test_result("Get Communication Templates", True, result)
    except Exception as e:
        print(f"Error getting communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Communication Templates", False)

def main():
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC ENDPOINTS")
    print("=" * 80)
    
    # Get authentication token
    admin_token = test_authentication()
    
    if admin_token:
        # Test Calendar View endpoint
        test_calendar_view(admin_token)
        
        # Test Communications Templates endpoint
        test_communications_templates(admin_token)
    else:
        print("Authentication failed. Cannot proceed with endpoint testing.")

if __name__ == "__main__":
    main()