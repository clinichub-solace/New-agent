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

# Test Authentication System
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test variables to store authentication data
    admin_token = None
    
    # Test 1: Login with Admin Credentials
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
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    return admin_token

# Test Dashboard ERx Patients Endpoint
def test_erx_patients(admin_token):
    print("\n--- Testing ERx Patients Dashboard Endpoint ---")
    
    try:
        url = f"{API_URL}/dashboard/erx-patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify ERx patients structure
        assert "patients" in result
        
        print_test_result("ERx Patients Dashboard", True, result)
    except Exception as e:
        print(f"Error getting ERx patients: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("ERx Patients Dashboard", False)

# Test Dashboard Daily Log Endpoint
def test_daily_log(admin_token):
    print("\n--- Testing Daily Log Dashboard Endpoint ---")
    
    try:
        url = f"{API_URL}/dashboard/daily-log"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify daily log structure
        assert "date" in result
        assert "summary" in result
        assert "visits" in result
        
        print_test_result("Daily Log Dashboard", True, result)
    except Exception as e:
        print(f"Error getting daily log: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Daily Log Dashboard", False)

# Test Dashboard Patient Queue Endpoint
def test_patient_queue(admin_token):
    print("\n--- Testing Patient Queue Dashboard Endpoint ---")
    
    try:
        url = f"{API_URL}/dashboard/patient-queue"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify patient queue structure
        assert "active_encounters" in result
        
        print_test_result("Patient Queue Dashboard", True, result)
    except Exception as e:
        print(f"Error getting patient queue: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Queue Dashboard", False)

def run_additional_tests():
    print("\n" + "=" * 80)
    print("ADDITIONAL DASHBOARD TESTING FOR CLINICHUB BACKEND API")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    if admin_token:
        # Test additional dashboard endpoints
        test_erx_patients(admin_token)
        test_daily_log(admin_token)
        test_patient_queue(admin_token)
    else:
        print("Authentication failed. Cannot proceed with further tests.")

if __name__ == "__main__":
    run_additional_tests()