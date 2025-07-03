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

# Get authentication token
def get_auth_token():
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["access_token"]
    except Exception as e:
        print(f"Error getting authentication token: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return None

def main():
    # Get authentication token
    auth_token = get_auth_token()
    if not auth_token:
        print("Failed to get authentication token. Exiting.")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test 1: Get payroll periods
    print("\n--- Testing Payroll Period Retrieval ---")
    try:
        url = f"{API_URL}/payroll/periods"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Payroll Periods", True, result)
    except Exception as e:
        print(f"Error retrieving payroll periods: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Payroll Periods", False)
    
    # Create a mock period ID for testing
    mock_period_id = str(uuid.uuid4())
    print(f"\nUsing mock period ID: {mock_period_id} for testing")
    
    # Test 2: Calculate payroll
    print("\n--- Testing Payroll Calculation ---")
    try:
        url = f"{API_URL}/payroll/calculate/{mock_period_id}"
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Calculate Payroll", True, result)
    except Exception as e:
        print(f"Error calculating payroll: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Calculate Payroll", False)
    
    # Test 3: Get payroll records
    print("\n--- Testing Payroll Records Retrieval ---")
    try:
        url = f"{API_URL}/payroll/records/{mock_period_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Payroll Records", True, result)
    except Exception as e:
        print(f"Error retrieving payroll records: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Payroll Records", False)
    
    # Create a mock record ID for testing
    mock_record_id = str(uuid.uuid4())
    print(f"\nUsing mock record ID: {mock_record_id} for testing")
    
    # Test 4: Generate paystub
    print("\n--- Testing Paystub Generation ---")
    try:
        url = f"{API_URL}/payroll/paystub/{mock_record_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Generate Paystub", True, result)
    except Exception as e:
        print(f"Error generating paystub: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Generate Paystub", False)
    
    # Test 5: Approve payroll
    print("\n--- Testing Payroll Approval ---")
    try:
        url = f"{API_URL}/payroll/approve/{mock_period_id}"
        data = {"approved_by": "admin"}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Approve Payroll", True, result)
    except Exception as e:
        print(f"Error approving payroll: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Approve Payroll", False)
    
    # Test 6: Mark payroll as paid
    print("\n--- Testing Payroll Payment ---")
    try:
        url = f"{API_URL}/payroll/pay/{mock_period_id}"
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Mark Payroll as Paid", True, result)
    except Exception as e:
        print(f"Error marking payroll as paid: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Mark Payroll as Paid", False)

if __name__ == "__main__":
    main()