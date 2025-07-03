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
    
    # Test 1: Create a payroll period
    print("\n--- Testing Payroll Period Creation ---")
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
        
        period_id = result["id"]
        print_test_result("Create Payroll Period", True, result)
    except Exception as e:
        print(f"Error creating payroll period: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Payroll Period", False)
    
    # Test 2: Get payroll periods
    print("\n--- Testing Payroll Period Retrieval ---")
    try:
        url = f"{API_URL}/payroll/periods"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # If we didn't get a period ID from creation, try to get one from the list
        if not period_id and result and len(result) > 0:
            period_id = result[0]["id"]
            print(f"Using existing period ID: {period_id}")
        
        print_test_result("Get Payroll Periods", True, result)
    except Exception as e:
        print(f"Error retrieving payroll periods: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Payroll Periods", False)
    
    if not period_id:
        print("No period ID available. Skipping remaining tests.")
        return
    
    # Test 3: Calculate payroll
    print("\n--- Testing Payroll Calculation ---")
    try:
        url = f"{API_URL}/payroll/calculate/{period_id}"
        
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
    
    # Test 4: Get payroll records
    print("\n--- Testing Payroll Records Retrieval ---")
    record_id = None
    try:
        url = f"{API_URL}/payroll/records/{period_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result and len(result) > 0:
            record_id = result[0]["id"]
            print(f"Found record ID: {record_id}")
        
        print_test_result("Get Payroll Records", True, result)
    except Exception as e:
        print(f"Error retrieving payroll records: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Payroll Records", False)
    
    if not record_id:
        print("No record ID available. Skipping paystub generation test.")
    else:
        # Test 5: Generate paystub
        print("\n--- Testing Paystub Generation ---")
        try:
            url = f"{API_URL}/payroll/paystub/{record_id}"
            
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
    
    # Test 6: Approve payroll
    print("\n--- Testing Payroll Approval ---")
    try:
        url = f"{API_URL}/payroll/approve/{period_id}"
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
    
    # Test 7: Mark payroll as paid
    print("\n--- Testing Payroll Payment ---")
    try:
        url = f"{API_URL}/payroll/pay/{period_id}"
        
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