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

# Authentication function to get admin token
def get_admin_token():
    try:
        # First try to initialize admin
        init_url = f"{API_URL}/auth/init-admin"
        requests.post(init_url)
        
        # Login with admin credentials
        login_url = f"{API_URL}/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        result = response.json()
        
        return result["access_token"]
    except Exception as e:
        print(f"Error getting admin token: {str(e)}")
        return None

# Test Enhanced Employee Management
def test_enhanced_employee_management(admin_token):
    print("\n--- Testing Enhanced Employee Management ---")
    
    # Test creating an employee with different roles
    employee_ids = []
    roles = ["doctor", "nurse", "admin", "receptionist", "technician"]
    
    for i, role in enumerate(roles):
        try:
            url = f"{API_URL}/enhanced-employees"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "first_name": f"Test{i+1}",
                "last_name": f"Employee{role.capitalize()}",
                "email": f"test.{role}@clinichub.com",
                "phone": f"+1-555-{100+i:03d}-{2000+i:04d}",
                "role": role,
                "department": "Medical" if role in ["doctor", "nurse"] else "Administrative",
                "hire_date": (date.today() - timedelta(days=30*i)).isoformat(),
                "salary": 120000.00 if role in ["doctor", "admin"] else None,
                "hourly_rate": None if role in ["doctor", "admin"] else 25.00 + i*5,
                "employment_type": "full_time" if i % 2 == 0 else "part_time"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify employee ID generation
            assert "employee_id" in result
            assert result["employee_id"].startswith("EMP-")
            
            employee_ids.append(result["id"])
            print_test_result(f"Create {role.capitalize()} Employee", True, result)
        except Exception as e:
            print(f"Error creating {role} employee: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result(f"Create {role.capitalize()} Employee", False)
    
    # Test getting all employees
    try:
        url = f"{API_URL}/enhanced-employees"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we have at least the employees we just created
        assert len(result) >= len(employee_ids)
        
        print_test_result("Get All Employees", True, result)
    except Exception as e:
        print(f"Error getting employees: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Employees", False)
    
    # Test getting a specific employee
    if employee_ids:
        try:
            url = f"{API_URL}/enhanced-employees/{employee_ids[0]}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == employee_ids[0]
            print_test_result("Get Employee by ID", True, result)
        except Exception as e:
            print(f"Error getting employee by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Employee by ID", False)
    
    # Test updating an employee
    if employee_ids:
        try:
            url = f"{API_URL}/enhanced-employees/{employee_ids[0]}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "phone": "+1-555-999-8888",
                "emergency_contact_name": "Jane Doe",
                "emergency_contact_phone": "+1-555-123-4567",
                "emergency_contact_relationship": "Spouse",
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Employee", True, result)
            
            # Verify the update worked by getting the employee again
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["phone"] == "+1-555-999-8888"
            assert result["emergency_contact_name"] == "Jane Doe"
            print_test_result("Verify Employee Update", True, result)
        except Exception as e:
            print(f"Error updating employee: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Employee", False)
    
    return employee_ids

# Test Employee Documents
def test_employee_documents(admin_token, employee_id):
    print("\n--- Testing Employee Documents ---")
    
    if not employee_id:
        print("Skipping document tests - no employee ID available")
        return None
    
    # Test creating different types of employee documents
    document_ids = []
    document_types = [
        ("warning", "Performance Warning"),
        ("vacation_request", "Vacation Request"),
        ("sick_leave", "Sick Leave Request"),
        ("performance_review", "Annual Performance Review"),
        ("policy_acknowledgment", "COVID-19 Policy Acknowledgment"),
        ("training_certificate", "CPR Training Certificate")
    ]
    
    for doc_type, title in document_types:
        try:
            url = f"{API_URL}/employee-documents"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "employee_id": employee_id,
                "document_type": doc_type,
                "title": title,
                "content": f"This is a test {doc_type} document for employee testing.",
                "effective_date": date.today().isoformat(),
                "expiry_date": (date.today() + timedelta(days=365)).isoformat() if doc_type in ["training_certificate", "policy_acknowledgment"] else None,
                "due_date": (date.today() + timedelta(days=14)).isoformat() if doc_type in ["performance_review"] else None,
                "created_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            document_ids.append(result["id"])
            print_test_result(f"Create {doc_type.replace('_', ' ').title()} Document", True, result)
        except Exception as e:
            print(f"Error creating {doc_type} document: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result(f"Create {doc_type.replace('_', ' ').title()} Document", False)
    
    # Test getting employee documents
    try:
        url = f"{API_URL}/employee-documents/employee/{employee_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we have the documents we just created
        assert len(result) >= len(document_ids)
        
        print_test_result("Get Employee Documents", True, result)
    except Exception as e:
        print(f"Error getting employee documents: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Employee Documents", False)
    
    # Test document signing workflow
    if document_ids:
        try:
            url = f"{API_URL}/employee-documents/{document_ids[0]}/sign"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"signed_by": "Test Employee"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Sign Employee Document", True, result)
        except Exception as e:
            print(f"Error signing document: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Sign Employee Document", False)
    
    # Test document approval workflow
    if document_ids:
        try:
            url = f"{API_URL}/employee-documents/{document_ids[0]}/approve"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"approved_by": "Admin User"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Approve Employee Document", True, result)
        except Exception as e:
            print(f"Error approving document: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Approve Employee Document", False)
    
    return document_ids

# Test Time Tracking
def test_time_tracking(admin_token, employee_id):
    print("\n--- Testing Time Tracking ---")
    
    if not employee_id:
        print("Skipping time tracking tests - no employee ID available")
        return
    
    # Test creating time entries for a full day
    time_entry_ids = []
    entry_types = [
        ("clock_in", datetime.now().replace(hour=9, minute=0)),
        ("break_start", datetime.now().replace(hour=12, minute=0)),
        ("break_end", datetime.now().replace(hour=13, minute=0)),
        ("clock_out", datetime.now().replace(hour=17, minute=0))
    ]
    
    for entry_type, timestamp in entry_types:
        try:
            url = f"{API_URL}/time-entries"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "employee_id": employee_id,
                "entry_type": entry_type,
                "timestamp": timestamp.isoformat(),
                "location": "Main Office",
                "notes": f"Test {entry_type} entry",
                "manual_entry": True
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            time_entry_ids.append(result["id"])
            print_test_result(f"Create {entry_type.replace('_', ' ').title()} Entry", True, result)
        except Exception as e:
            print(f"Error creating time entry: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result(f"Create {entry_type.replace('_', ' ').title()} Entry", False)
    
    # Test getting employee time entries
    try:
        url = f"{API_URL}/time-entries/employee/{employee_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we have the time entries we just created
        assert len(result) >= len(time_entry_ids)
        
        print_test_result("Get Employee Time Entries", True, result)
    except Exception as e:
        print(f"Error getting time entries: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Employee Time Entries", False)
    
    # Test getting employee current status
    try:
        url = f"{API_URL}/time-entries/employee/{employee_id}/current-status"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Employee Current Status", True, result)
    except Exception as e:
        print(f"Error getting current status: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Employee Current Status", False)
    
    return time_entry_ids

# Test Work Shifts
def test_work_shifts(admin_token, employee_id):
    print("\n--- Testing Work Shifts ---")
    
    if not employee_id:
        print("Skipping work shift tests - no employee ID available")
        return
    
    # Test creating work shifts for a week
    shift_ids = []
    today = date.today()
    
    for i in range(5):  # Monday to Friday
        shift_date = today + timedelta(days=i)
        try:
            url = f"{API_URL}/work-shifts"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "employee_id": employee_id,
                "shift_date": shift_date.isoformat(),
                "start_time": datetime.combine(shift_date, datetime.min.time()).replace(hour=9, minute=0).isoformat(),
                "end_time": datetime.combine(shift_date, datetime.min.time()).replace(hour=17, minute=0).isoformat(),
                "break_duration": 60,
                "position": "Doctor",
                "location": "Main Clinic",
                "notes": f"Regular shift for day {i+1}",
                "created_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            shift_ids.append(result["id"])
            print_test_result(f"Create Work Shift for {shift_date.strftime('%A')}", True, result)
        except Exception as e:
            print(f"Error creating work shift: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result(f"Create Work Shift for {shift_date.strftime('%A')}", False)
    
    # Test getting employee shifts
    try:
        url = f"{API_URL}/work-shifts/employee/{employee_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": (today + timedelta(days=6)).strftime("%Y-%m-%d")
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify we have the shifts we just created
        assert len(result) >= len(shift_ids)
        
        print_test_result("Get Employee Shifts", True, result)
    except Exception as e:
        print(f"Error getting employee shifts: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Employee Shifts", False)
    
    # Test getting shifts by date
    try:
        url = f"{API_URL}/work-shifts/date/{today.isoformat()}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Shifts by Date", True, result)
    except Exception as e:
        print(f"Error getting shifts by date: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Shifts by Date", False)
    
    # Test updating shift status
    if shift_ids:
        try:
            url = f"{API_URL}/work-shifts/{shift_ids[0]}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "in_progress"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Shift Status (In Progress)", True, result)
            
            # Update to completed
            params = {"status": "completed"}
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Shift Status (Completed)", True, result)
        except Exception as e:
            print(f"Error updating shift status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Shift Status", False)
    
    return shift_ids

# Test Hours Summary
def test_hours_summary(admin_token, employee_id):
    print("\n--- Testing Hours Summary ---")
    
    if not employee_id:
        print("Skipping hours summary tests - no employee ID available")
        return
    
    try:
        url = f"{API_URL}/employees/{employee_id}/hours-summary"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat()
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Employee Hours Summary", True, result)
    except Exception as e:
        print(f"Error getting hours summary: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Employee Hours Summary", False)

# Main test function
def main():
    print("\n=== EMPLOYEE MANAGEMENT SYSTEM TESTS ===\n")
    
    # Get admin token for authenticated requests
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Cannot proceed with tests.")
        return
    
    # Run all tests
    employee_ids = test_enhanced_employee_management(admin_token)
    
    if employee_ids:
        # Use the first employee for further tests
        employee_id = employee_ids[0]
        
        # Test employee documents
        document_ids = test_employee_documents(admin_token, employee_id)
        
        # Test time tracking
        test_time_tracking(admin_token, employee_id)
        
        # Test work shifts
        test_work_shifts(admin_token, employee_id)
        
        # Test hours summary
        test_hours_summary(admin_token, employee_id)
    
    print("\n=== EMPLOYEE MANAGEMENT SYSTEM TESTS COMPLETED ===\n")

if __name__ == "__main__":
    main()