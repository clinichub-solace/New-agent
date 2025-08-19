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

# Test Authentication
def test_authentication():
    print("\n--- Testing Authentication ---")
    
    # Test 1: Initialize Admin User (if not already initialized)
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        if response.status_code == 400:
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

# Test GET /api/vital-signs
def test_vital_signs_endpoint(admin_token):
    print("\n--- Testing GET /api/vital-signs Endpoint ---")
    
    try:
        url = f"{API_URL}/vital-signs"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/vital-signs", True, result)
        return True
    except Exception as e:
        print(f"Error getting vital signs: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/vital-signs", False)
        return False

# Test GET /api/prescriptions
def test_prescriptions_endpoint():
    print("\n--- Testing GET /api/prescriptions Endpoint ---")
    
    try:
        url = f"{API_URL}/prescriptions"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/prescriptions", True, result)
        return True
    except Exception as e:
        print(f"Error getting prescriptions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/prescriptions", False)
        return False

# Test POST /api/erx/init
def test_erx_init_endpoint(admin_token):
    print("\n--- Testing POST /api/erx/init Endpoint ---")
    
    try:
        url = f"{API_URL}/erx/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/erx/init", True, result)
        return True
    except Exception as e:
        print(f"Error initializing eRx: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/erx/init", False)
        return False

# Test GET /api/erx/medications
def test_erx_medications_endpoint(admin_token):
    print("\n--- Testing GET /api/erx/medications Endpoint ---")
    
    try:
        url = f"{API_URL}/erx/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/medications", True, result)
        return True
    except Exception as e:
        print(f"Error getting eRx medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/erx/medications", False)
        return False

# Test GET /api/erx/formulary
def test_erx_formulary_endpoint(admin_token):
    print("\n--- Testing GET /api/erx/formulary Endpoint ---")
    
    try:
        url = f"{API_URL}/erx/formulary"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/formulary", True, result)
        return True
    except Exception as e:
        print(f"Error getting eRx formulary: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/erx/formulary", False)
        return False

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING EHR AND ERX ENDPOINTS")
    print("=" * 80)
    
    # Test authentication first
    admin_token = test_authentication()
    
    # Test previously fixed endpoints
    vital_signs_ok = test_vital_signs_endpoint()
    prescriptions_ok = test_prescriptions_endpoint()
    
    # Test eRx endpoints
    if admin_token:
        erx_init_ok = test_erx_init_endpoint(admin_token)
        
        # Only test these if initialization succeeded
        if erx_init_ok:
            erx_medications_ok = test_erx_medications_endpoint(admin_token)
            erx_formulary_ok = test_erx_formulary_endpoint(admin_token)
        else:
            erx_medications_ok = False
            erx_formulary_ok = False
    else:
        erx_init_ok = False
        erx_medications_ok = False
        erx_formulary_ok = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"GET /api/vital-signs: {'✅ PASSED' if vital_signs_ok else '❌ FAILED'}")
    print(f"GET /api/prescriptions: {'✅ PASSED' if prescriptions_ok else '❌ FAILED'}")
    print(f"POST /api/erx/init: {'✅ PASSED' if erx_init_ok else '❌ FAILED'}")
    print(f"GET /api/erx/medications: {'✅ PASSED' if erx_medications_ok else '❌ FAILED'}")
    print(f"GET /api/erx/formulary: {'✅ PASSED' if erx_formulary_ok else '❌ FAILED'}")
    print("=" * 80)
    
    # Overall status
    all_passed = vital_signs_ok and prescriptions_ok and erx_init_ok and erx_medications_ok and erx_formulary_ok
    print(f"Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()