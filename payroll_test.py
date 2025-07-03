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

# Test the payroll management system
def test_payroll_management():
    # Step 1: Initialize admin user and get authentication token
    print("\n--- Initializing Admin User ---")
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        print("Admin user initialized successfully")
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print("Continuing with login...")
    
    # Step 2: Login with admin credentials
    print("\n--- Logging in as Admin ---")
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
        print("Login successful")
    except Exception as e:
        print(f"Error logging in: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return
    
    # Set authorization header for subsequent requests
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Step 3: Create a test employee
    print("\n--- Creating Test Employee ---")
    employee_id = None
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "role": "doctor",
            "department": "Medical",
            "hire_date": date.today().strftime("%Y-%m-%d"),
            "hourly_rate": 25.0
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        employee_id = result["id"]
        print_test_result("Create Test Employee", True, result)
    except Exception as e:
        print(f"Error creating test employee: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Employee", False)
        return
    
    # Step 4: Create a payroll period
    print("\n--- Testing Payroll Period Creation ---")
    period_id = None
    try:
        url = f"{API_URL}/payroll/periods"
        
        # Create a biweekly pay period
        today = date.today()
        period_start = today - timedelta(days=14)
        period_end = today - timedelta(days=1)
        pay_date = today + timedelta(days=5)
        
        data = {
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "pay_date": pay_date.strftime("%Y-%m-%d"),
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
        return
    
    # Step 5: Get payroll periods
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
    
    # Step 6: Create time entries for the employee
    print("\n--- Creating Time Entries for Test Employee ---")
    try:
        # Create time entries for each day in the period
        period_start_date = datetime.strptime(period_start.strftime("%Y-%m-%d"), "%Y-%m-%d").date()
        period_end_date = datetime.strptime(period_end.strftime("%Y-%m-%d"), "%Y-%m-%d").date()
        
        current_date = period_start_date
        while current_date <= period_end_date:
            if current_date.weekday() < 5:  # Monday to Friday
                # Clock in at 9:00 AM
                clock_in_time = datetime.combine(current_date, datetime.strptime("09:00", "%H:%M").time())
                
                url = f"{API_URL}/time-entries"
                data = {
                    "employee_id": employee_id,
                    "entry_type": "clock_in",
                    "timestamp": clock_in_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "location": "Main Office",
                    "manual_entry": True
                }
                
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                # Clock out at 5:00 PM
                clock_out_time = datetime.combine(current_date, datetime.strptime("17:00", "%H:%M").time())
                
                data = {
                    "employee_id": employee_id,
                    "entry_type": "clock_out",
                    "timestamp": clock_out_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "location": "Main Office",
                    "manual_entry": True
                }
                
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
            
            current_date += timedelta(days=1)
        
        print_test_result("Create Time Entries", True, {"message": "Created time entries for the pay period"})
    except Exception as e:
        print(f"Error creating time entries: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Time Entries", False)
    
    # Step 7: Calculate payroll
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
        return
    
    # Step 8: Get payroll records
    print("\n--- Testing Payroll Records Retrieval ---")
    record_id = None
    try:
        url = f"{API_URL}/payroll/records/{period_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result and len(result) > 0:
            record_id = result[0]["id"]
        
        print_test_result("Get Payroll Records", True, result)
    except Exception as e:
        print(f"Error retrieving payroll records: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Payroll Records", False)
        return
    
    # Step 9: Generate paystub
    print("\n--- Testing Paystub Generation ---")
    if record_id:
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
    else:
        print("Skipping paystub generation - no payroll record ID available")
    
    # Step 10: Approve payroll
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
        return
    
    # Step 11: Mark payroll as paid
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
    
    # Step 12: Verify workflow status
    print("\n--- Verifying Payroll Workflow Status ---")
    try:
        url = f"{API_URL}/payroll/periods"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        period = next((p for p in result if p["id"] == period_id), None)
        if period:
            status = period["status"]
            print(f"Final payroll status: {status}")
            if status == "paid":
                print_test_result("Payroll Workflow", True, {"message": "Payroll workflow completed successfully"})
            else:
                print_test_result("Payroll Workflow", False, {"message": f"Unexpected final status: {status}"})
        else:
            print_test_result("Payroll Workflow", False, {"message": "Could not find period in results"})
    except Exception as e:
        print(f"Error verifying workflow status: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Payroll Workflow", False)

if __name__ == "__main__":
    test_payroll_management()