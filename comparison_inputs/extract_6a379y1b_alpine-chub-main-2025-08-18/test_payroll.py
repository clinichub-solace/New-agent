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

# Authentication credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Helper function to print test results
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

# Test the payroll management system
def test_payroll_management():
    print("\n--- Testing Payroll Management System ---")
    
    # Step 1: Login with admin credentials
    auth_token = None
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        auth_token = result["access_token"]
        print_test_result("Login with admin credentials", True, result)
    except Exception as e:
        print_test_result("Login with admin credentials", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return
    
    # Set authorization header for subsequent requests
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Step 2: Test GET /api/payroll/periods
    try:
        url = f"{API_URL}/payroll/periods"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/payroll/periods", True, result)
    except Exception as e:
        print_test_result("GET /api/payroll/periods", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Step 3: Test POST /api/payroll/periods
    period_id = None
    try:
        url = f"{API_URL}/payroll/periods"
        
        # Create a biweekly pay period
        today = datetime.now()
        period_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        period_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        pay_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        
        data = {
            "period_start": period_start,
            "period_end": period_end,
            "pay_date": pay_date,
            "period_type": "biweekly",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        period_id = result.get("id")
        print_test_result("POST /api/payroll/periods", True, result)
    except Exception as e:
        print_test_result("POST /api/payroll/periods", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # If we couldn't create a period, try to get an existing one
    if not period_id:
        try:
            url = f"{API_URL}/payroll/periods"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result and len(result) > 0:
                period_id = result[0]["id"]
                print(f"Found existing period ID: {period_id}")
        except Exception as e:
            print(f"Error getting existing period ID: {str(e)}")
    
    # If we still don't have a period ID, we can't continue testing
    if not period_id:
        print("No payroll period ID available. Cannot continue testing.")
        return
    
    # Step 4: Test POST /api/payroll/calculate/{period_id}
    try:
        url = f"{API_URL}/payroll/calculate/{period_id}"
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/payroll/calculate/{period_id}", True, result)
    except Exception as e:
        print_test_result("POST /api/payroll/calculate/{period_id}", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Step 5: Test GET /api/payroll/records/{period_id}
    record_id = None
    try:
        url = f"{API_URL}/payroll/records/{period_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result and len(result) > 0:
            record_id = result[0]["id"]
            print(f"Found record ID: {record_id}")
        
        print_test_result("GET /api/payroll/records/{period_id}", True, result)
    except Exception as e:
        print_test_result("GET /api/payroll/records/{period_id}", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # If we don't have a record ID, we can't test the paystub endpoint
    if not record_id:
        print("No payroll record ID available. Cannot test paystub generation.")
    else:
        # Step 6: Test GET /api/payroll/paystub/{record_id}
        try:
            url = f"{API_URL}/payroll/paystub/{record_id}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("GET /api/payroll/paystub/{record_id}", True, result)
        except Exception as e:
            print_test_result("GET /api/payroll/paystub/{record_id}", False, error=str(e))
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
    
    # Step 7: Test POST /api/payroll/approve/{period_id}
    try:
        url = f"{API_URL}/payroll/approve/{period_id}"
        data = {"approved_by": "admin"}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/payroll/approve/{period_id}", True, result)
    except Exception as e:
        print_test_result("POST /api/payroll/approve/{period_id}", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Step 8: Test POST /api/payroll/pay/{period_id}
    try:
        url = f"{API_URL}/payroll/pay/{period_id}"
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/payroll/pay/{period_id}", True, result)
    except Exception as e:
        print_test_result("POST /api/payroll/pay/{period_id}", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    print("\nPayroll Management System testing completed.")

if __name__ == "__main__":
    test_payroll_management()