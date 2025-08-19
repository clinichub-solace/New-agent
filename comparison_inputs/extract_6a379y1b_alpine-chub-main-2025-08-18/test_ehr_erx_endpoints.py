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

# Test Authentication - Login as admin to get token
def test_authentication():
    print("\n--- Testing Authentication ---")
    
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
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

# Test EHR Core Endpoints
def test_ehr_core_endpoints(admin_token):
    print("\n--- Testing EHR Core Endpoints ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/patients", True, result)
    except Exception as e:
        print(f"Error getting patients: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/patients", False)
    
    # Test GET /api/encounters
    try:
        url = f"{API_URL}/encounters"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/encounters", True, result)
    except Exception as e:
        print(f"Error getting encounters: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/encounters", False)
    
    # Test GET /api/medications
    try:
        url = f"{API_URL}/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/medications", True, result)
    except Exception as e:
        print(f"Error getting medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/medications", False)

# Test Previously Broken, Now Fixed Endpoints
def test_previously_broken_endpoints(admin_token):
    print("\n--- Testing Previously Broken, Now Fixed Endpoints ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/vital-signs
    try:
        url = f"{API_URL}/vital-signs"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/vital-signs", True, result)
    except Exception as e:
        print(f"Error getting vital signs: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/vital-signs", False)
    
    # Test GET /api/prescriptions
    try:
        url = f"{API_URL}/prescriptions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/prescriptions", True, result)
    except Exception as e:
        print(f"Error getting prescriptions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/prescriptions", False)

# Test eRx System (New Endpoints)
def test_erx_system_endpoints(admin_token):
    print("\n--- Testing eRx System (New Endpoints) ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test POST /api/erx/init
    try:
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/erx/init", True, result)
    except Exception as e:
        print(f"Error initializing eRx system: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/erx/init", False)
    
    # Test GET /api/erx/medications
    try:
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/medications", True, result)
    except Exception as e:
        print(f"Error getting eRx medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/erx/medications", False)
    
    # Test GET /api/erx/formulary
    try:
        url = f"{API_URL}/erx/formulary"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/formulary", True, result)
    except Exception as e:
        print(f"Error getting eRx formulary: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/erx/formulary", False)

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING EHR AND ERX ENDPOINTS")
    print("=" * 80)
    
    # Test authentication first to get token
    admin_token = test_authentication()
    
    if admin_token:
        # Run all tests with the admin token
        test_ehr_core_endpoints(admin_token)
        test_previously_broken_endpoints(admin_token)
        test_erx_system_endpoints(admin_token)
    else:
        print("Authentication failed. Cannot proceed with tests.")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()