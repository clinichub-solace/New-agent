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
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            if isinstance(response, dict) or isinstance(response, list):
                print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
            else:
                print(f"   Response: {response}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

# Test Authentication
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print_test_result("Initialize Admin User", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
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
        
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print_test_result("Admin Login", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    return admin_token

# Test Dashboard Stats Endpoint
def test_dashboard_stats(admin_token):
    print("\n--- Testing Dashboard Stats Endpoint ---")
    
    if not admin_token:
        print_test_result("Dashboard Stats", False, error="No authentication token available")
        return
    
    try:
        url = f"{API_URL}/dashboard/stats"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Dashboard Stats", True, result)
    except Exception as e:
        print_test_result("Dashboard Stats", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Test Dashboard eRx Patients Endpoint
def test_dashboard_erx_patients(admin_token):
    print("\n--- Testing Dashboard eRx Patients Endpoint ---")
    
    if not admin_token:
        print_test_result("Dashboard eRx Patients", False, error="No authentication token available")
        return
    
    try:
        url = f"{API_URL}/dashboard/erx-patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Dashboard eRx Patients", True, result)
    except Exception as e:
        print_test_result("Dashboard eRx Patients", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Test Dashboard Daily Log Endpoint
def test_dashboard_daily_log(admin_token):
    print("\n--- Testing Dashboard Daily Log Endpoint ---")
    
    if not admin_token:
        print_test_result("Dashboard Daily Log", False, error="No authentication token available")
        return
    
    try:
        url = f"{API_URL}/dashboard/daily-log"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Dashboard Daily Log", True, result)
    except Exception as e:
        print_test_result("Dashboard Daily Log", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Test Dashboard Patient Queue Endpoint
def test_dashboard_patient_queue(admin_token):
    print("\n--- Testing Dashboard Patient Queue Endpoint ---")
    
    if not admin_token:
        print_test_result("Dashboard Patient Queue", False, error="No authentication token available")
        return
    
    try:
        url = f"{API_URL}/dashboard/patient-queue"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Dashboard Patient Queue", True, result)
    except Exception as e:
        print_test_result("Dashboard Patient Queue", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Test Dashboard Pending Payments Endpoint
def test_dashboard_pending_payments(admin_token):
    print("\n--- Testing Dashboard Pending Payments Endpoint ---")
    
    if not admin_token:
        print_test_result("Dashboard Pending Payments", False, error="No authentication token available")
        return
    
    try:
        url = f"{API_URL}/dashboard/pending-payments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Dashboard Pending Payments", True, result)
    except Exception as e:
        print_test_result("Dashboard Pending Payments", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Test Forms Functionality
def test_forms_functionality(admin_token):
    print("\n--- Testing Forms Functionality ---")
    
    if not admin_token:
        print_test_result("Forms Functionality", False, error="No authentication token available")
        return
    
    # Test 1: Get Forms
    try:
        url = f"{API_URL}/forms"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Forms", True, result)
    except Exception as e:
        print_test_result("Get Forms", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test 2: Initialize Form Templates
    try:
        url = f"{API_URL}/forms/templates/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Form Templates", True, result)
    except Exception as e:
        print_test_result("Initialize Form Templates", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test 3: Initialize Compliant Form Templates
    try:
        url = f"{API_URL}/forms/templates/init-compliant"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Compliant Form Templates", True, result)
    except Exception as e:
        print_test_result("Initialize Compliant Form Templates", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING CLINICHUB BACKEND API - BSON DATETIME ERROR DIAGNOSIS")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    # Test dashboard stats endpoint
    test_dashboard_stats(admin_token)
    
    # Test new dashboard endpoints
    test_dashboard_erx_patients(admin_token)
    test_dashboard_daily_log(admin_token)
    test_dashboard_patient_queue(admin_token)
    test_dashboard_pending_payments(admin_token)
    
    # Test forms functionality
    test_forms_functionality(admin_token)

if __name__ == "__main__":
    run_tests()