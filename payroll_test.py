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

# Test Payroll Period Management
def test_payroll_periods(auth_token):
    print("\n--- Testing Payroll Period Management ---")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    period_id = None
    
    # Test creating a payroll period
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
        return None
    
    # Test retrieving payroll periods
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
    
    # Test filtering payroll periods by year
    try:
        url = f"{API_URL}/payroll/periods"
        params = {"year": datetime.now().year}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Filter Payroll Periods by Year", True, result)
    except Exception as e:
        print(f"Error filtering payroll periods: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Filter Payroll Periods by Year", False)
    
    return period_id

# Test Payroll Calculation
def test_payroll_calculation(auth_token, period_id):
    print("\n--- Testing Payroll Calculation ---")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First, create an employee for testing
    employee_id = create_test_employee(auth_token)
    if not employee_id:
        print("Skipping payroll calculation tests - could not create test employee")
        return None
    
    # Create time entries for the employee
    create_test_time_entries(auth_token, employee_id, period_id)
    
    # Test calculating payroll
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
        return None
    
    # Test retrieving payroll records
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
    
    return record_id

# Test Paystub Generation
def test_paystub_generation(auth_token, record_id):
    print("\n--- Testing Paystub Generation ---")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not record_id:
        print("Skipping paystub generation test - no payroll record ID available")
        return
    
    try:
        url = f"{API_URL}/payroll/paystub/{record_id}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify paystub structure
        assert "employee_info" in result
        assert "pay_period" in result
        assert "hours_breakdown" in result
        assert "pay_breakdown" in result
        assert "taxes_breakdown" in result
        assert "ytd_totals" in result
        assert "net_pay" in result
        
        print_test_result("Generate Paystub", True, result)
    except Exception as e:
        print(f"Error generating paystub: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Generate Paystub", False)

# Test Payroll Workflow
def test_payroll_workflow(auth_token, period_id):
    print("\n--- Testing Payroll Workflow ---")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not period_id:
        print("Skipping payroll workflow tests - no period ID available")
        return
    
    # Test approving payroll
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
    
    # Test marking payroll as paid
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

# Helper function to create a test employee
def create_test_employee(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "role": "doctor",
            "department": "Medical",
            "hire_date": date.today().isoformat(),
            "hourly_rate": 25.0
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test employee: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return None

# Helper function to create test time entries
def create_test_time_entries(auth_token, employee_id, period_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get period dates
        url = f"{API_URL}/payroll/periods"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        periods = response.json()
        
        period = next((p for p in periods if p["id"] == period_id), None)
        if not period:
            print("Could not find period information")
            return
        
        period_start = datetime.strptime(period["period_start"], "%Y-%m-%d").date()
        period_end = datetime.strptime(period["period_end"], "%Y-%m-%d").date()
        
        # Create time entries for each day in the period
        current_date = period_start
        while current_date <= period_end:
            if current_date.weekday() < 5:  # Monday to Friday
                # Clock in at 9:00 AM
                clock_in_time = datetime.combine(current_date, datetime.strptime("09:00", "%H:%M").time())
                
                url = f"{API_URL}/time-entries"
                data = {
                    "employee_id": employee_id,
                    "entry_type": "clock_in",
                    "timestamp": clock_in_time.isoformat(),
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
                    "timestamp": clock_out_time.isoformat(),
                    "location": "Main Office",
                    "manual_entry": True
                }
                
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
            
            current_date += timedelta(days=1)
        
        print("Created test time entries successfully")
    except Exception as e:
        print(f"Error creating test time entries: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

# Main test function
def main():
    # Get authentication token
    auth_token = get_auth_token()
    if not auth_token:
        print("Failed to get authentication token. Exiting.")
        return
    
    # Test payroll periods
    period_id = test_payroll_periods(auth_token)
    if not period_id:
        print("Failed to create payroll period. Skipping remaining tests.")
        return
    
    # Test payroll calculation
    record_id = test_payroll_calculation(auth_token, period_id)
    
    # Test paystub generation
    if record_id:
        test_paystub_generation(auth_token, record_id)
    
    # Test payroll workflow
    test_payroll_workflow(auth_token, period_id)

if __name__ == "__main__":
    main()