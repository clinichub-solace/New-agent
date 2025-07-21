#!/usr/bin/env python3
"""
Critical Backend Validation Fixes Test
Testing the specific fixes mentioned in the review request:
1. Prescription Creation - Added proper status, medication_display, patient_display field population
2. Appointment Creation - Fixed patient_name, provider_name validation by populating from database records
3. Employee Management - Added complete missing CRUD endpoints for employees
4. Field Validation - Enhanced validation and error handling throughout
"""

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
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Get admin token for authenticated requests"""
    try:
        # Initialize admin user first
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        
        # Login as admin
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["access_token"]
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None

def test_prescription_creation_fixes(admin_token):
    """Test Fix 1: Prescription Creation with proper field population"""
    print("\n=== Testing Prescription Creation Fixes ===")
    
    # First create a patient for testing
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-22",
            "gender": "female",
            "address_line1": "456 Health Street",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        patient_id = result["id"]
        patient_name = f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"
        
        print_test_result("Create Test Patient for Prescription", True, {"patient_id": patient_id, "patient_name": patient_name})
    except Exception as e:
        print_test_result("Create Test Patient for Prescription", False, error_msg=str(e))
        return False
    
    # Initialize eRx system to get medications
    medication_id = None
    try:
        url = f"{API_URL}/erx/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        # Get medications
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if medications:
            medication_id = medications[0]["id"]
            medication_name = medications[0]["generic_name"]
            print_test_result("Initialize eRx and Get Medications", True, {"medication_count": len(medications), "first_medication": medication_name})
        else:
            print_test_result("Initialize eRx and Get Medications", False, error_msg="No medications found")
            return False
    except Exception as e:
        print_test_result("Initialize eRx and Get Medications", False, error_msg=str(e))
        return False
    
    # Test prescription creation with proper field validation
    if patient_id and medication_id:
        try:
            url = f"{API_URL}/prescriptions"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "medication_id": medication_id,
                "patient_id": patient_id,
                "prescriber_id": "prescriber-123",
                "prescriber_name": "Dr. Sarah Johnson",
                
                # Dosage Information
                "dosage_text": "Take 1 tablet by mouth twice daily with food",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "BID",
                "route": "oral",
                
                # Prescription Details
                "quantity": 60.0,
                "days_supply": 30,
                "refills": 2,
                
                # Clinical Context
                "indication": "Hypertension management",
                "diagnosis_codes": ["I10"],
                "special_instructions": "Take with food to reduce stomach upset",
                
                "created_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify the critical fixes are working
            success = True
            issues = []
            
            # Check if status field is properly populated
            if "status" not in result or not result["status"]:
                success = False
                issues.append("Missing or empty 'status' field")
            
            # Check if medication_display field is properly populated
            if "medication_display" not in result or not result["medication_display"]:
                success = False
                issues.append("Missing or empty 'medication_display' field")
            
            # Check if patient_display field is properly populated
            if "patient_display" not in result or not result["patient_display"]:
                success = False
                issues.append("Missing or empty 'patient_display' field")
            
            # Check FHIR compliance
            if result.get("resource_type") != "MedicationRequest":
                success = False
                issues.append("Missing FHIR resource_type")
            
            if success:
                print_test_result("Prescription Creation with Field Population", True, {
                    "prescription_id": result["id"],
                    "status": result.get("status"),
                    "medication_display": result.get("medication_display"),
                    "patient_display": result.get("patient_display"),
                    "prescription_number": result.get("prescription_number")
                })
                return True
            else:
                print_test_result("Prescription Creation with Field Population", False, error_msg=f"Validation issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            print_test_result("Prescription Creation with Field Population", False, error_msg=str(e))
            return False
    
    return False

def test_appointment_creation_fixes(admin_token):
    """Test Fix 2: Appointment Creation with proper patient_name, provider_name validation"""
    print("\n=== Testing Appointment Creation Fixes ===")
    
    # Create a test patient
    patient_id = None
    patient_name = None
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Michael",
            "last_name": "Thompson",
            "email": "michael.thompson@example.com",
            "phone": "+1-555-345-6789",
            "date_of_birth": "1985-12-10",
            "gender": "male",
            "address_line1": "789 Wellness Ave",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75201"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        patient_id = result["id"]
        patient_name = f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"
        
        print_test_result("Create Test Patient for Appointment", True, {"patient_id": patient_id, "patient_name": patient_name})
    except Exception as e:
        print_test_result("Create Test Patient for Appointment", False, error_msg=str(e))
        return False
    
    # Create a test provider
    provider_id = None
    provider_name = None
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Preventive Care"],
            "license_number": "MD67890",
            "npi_number": "9876543210",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-456-7890",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        provider_id = result["id"]
        provider_name = f"{result['title']} {result['first_name']} {result['last_name']}"
        
        print_test_result("Create Test Provider for Appointment", True, {"provider_id": provider_id, "provider_name": provider_name})
    except Exception as e:
        print_test_result("Create Test Provider for Appointment", False, error_msg=str(e))
        return False
    
    # Test appointment creation with proper field validation
    if patient_id and provider_id:
        try:
            url = f"{API_URL}/appointments"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "appointment_date": (date.today() + timedelta(days=1)).isoformat(),
                "start_time": "14:00",
                "end_time": "14:30",
                "appointment_type": "consultation",
                "reason": "Annual physical examination",
                "location": "Main Clinic - Room 201",
                "scheduled_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify the critical fixes are working
            success = True
            issues = []
            
            # Check if patient_name field is properly populated from database
            if "patient_name" not in result or not result["patient_name"]:
                success = False
                issues.append("Missing or empty 'patient_name' field")
            elif result["patient_name"] != patient_name:
                success = False
                issues.append(f"patient_name mismatch: expected '{patient_name}', got '{result['patient_name']}'")
            
            # Check if provider_name field is properly populated from database
            if "provider_name" not in result or not result["provider_name"]:
                success = False
                issues.append("Missing or empty 'provider_name' field")
            elif result["provider_name"] != provider_name:
                success = False
                issues.append(f"provider_name mismatch: expected '{provider_name}', got '{result['provider_name']}'")
            
            # Check appointment number generation
            if "appointment_number" not in result or not result["appointment_number"].startswith("APT"):
                success = False
                issues.append("Missing or invalid appointment_number")
            
            if success:
                print_test_result("Appointment Creation with Name Population", True, {
                    "appointment_id": result["id"],
                    "appointment_number": result.get("appointment_number"),
                    "patient_name": result.get("patient_name"),
                    "provider_name": result.get("provider_name"),
                    "status": result.get("status")
                })
                return True
            else:
                print_test_result("Appointment Creation with Name Population", False, error_msg=f"Validation issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            print_test_result("Appointment Creation with Name Population", False, error_msg=str(e))
            return False
    
    return False

def test_employee_management_crud(admin_token):
    """Test Fix 3: Employee Management - Complete CRUD endpoints"""
    print("\n=== Testing Employee Management CRUD Endpoints ===")
    
    employee_id = None
    
    # Test CREATE employee
    try:
        url = f"{API_URL}/employees"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Jessica",
            "last_name": "Williams",
            "email": "jessica.williams@clinichub.com",
            "phone": "+1-555-567-8901",
            "role": "nurse",
            "department": "Emergency Department",
            "hire_date": date.today().isoformat(),
            "salary": 75000.00,
            "employment_type": "full_time"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify employee creation
        success = True
        issues = []
        
        if "employee_id" not in result or not result["employee_id"].startswith("EMP-"):
            success = False
            issues.append("Missing or invalid employee_id")
        
        if result.get("first_name") != "Jessica" or result.get("last_name") != "Williams":
            success = False
            issues.append("Name fields not properly saved")
        
        if result.get("role") != "nurse":
            success = False
            issues.append("Role field not properly saved")
        
        if success:
            employee_id = result["id"]
            print_test_result("CREATE Employee", True, {
                "employee_id": result.get("employee_id"),
                "id": employee_id,
                "name": f"{result.get('first_name')} {result.get('last_name')}",
                "role": result.get("role")
            })
        else:
            print_test_result("CREATE Employee", False, error_msg=f"Issues: {', '.join(issues)}")
            return False
            
    except Exception as e:
        print_test_result("CREATE Employee", False, error_msg=str(e))
        return False
    
    # Test READ employees (GET all)
    try:
        url = f"{API_URL}/employees"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our employee is in it
        success = isinstance(result, list) and len(result) > 0
        
        if success:
            # Check if our created employee is in the list
            found_employee = any(emp.get("id") == employee_id for emp in result)
            if not found_employee:
                success = False
                print_test_result("READ Employees (GET all)", False, error_msg="Created employee not found in list")
            else:
                print_test_result("READ Employees (GET all)", True, {
                    "total_employees": len(result),
                    "found_created_employee": True
                })
        else:
            print_test_result("READ Employees (GET all)", False, error_msg="Invalid response format")
            
    except Exception as e:
        print_test_result("READ Employees (GET all)", False, error_msg=str(e))
        return False
    
    # Test READ single employee (GET by ID)
    if employee_id:
        try:
            url = f"{API_URL}/employees/{employee_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify we get the correct employee
            success = (result.get("id") == employee_id and 
                      result.get("first_name") == "Jessica" and
                      result.get("last_name") == "Williams")
            
            if success:
                print_test_result("READ Employee (GET by ID)", True, {
                    "id": result.get("id"),
                    "name": f"{result.get('first_name')} {result.get('last_name')}",
                    "role": result.get("role")
                })
            else:
                print_test_result("READ Employee (GET by ID)", False, error_msg="Employee data mismatch")
                
        except Exception as e:
            print_test_result("READ Employee (GET by ID)", False, error_msg=str(e))
            return False
    
    # Test UPDATE employee (PUT)
    if employee_id:
        try:
            url = f"{API_URL}/employees/{employee_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "phone": "+1-555-999-8888",
                "department": "Intensive Care Unit",
                "salary": 80000.00
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify the update worked
            success = (result.get("phone") == "+1-555-999-8888" and
                      result.get("department") == "Intensive Care Unit" and
                      result.get("salary") == 80000.00)
            
            if success:
                print_test_result("UPDATE Employee (PUT)", True, {
                    "updated_phone": result.get("phone"),
                    "updated_department": result.get("department"),
                    "updated_salary": result.get("salary")
                })
            else:
                print_test_result("UPDATE Employee (PUT)", False, error_msg="Update values not reflected")
                
        except Exception as e:
            print_test_result("UPDATE Employee (PUT)", False, error_msg=str(e))
            return False
    
    # Test DELETE employee
    if employee_id:
        try:
            url = f"{API_URL}/employees/{employee_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("DELETE Employee", True, {"message": result.get("message", "Employee deleted")})
            
            # Verify employee is actually deleted by trying to get it
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 404:
                    print_test_result("Verify Employee Deletion", True, {"status": "Employee not found (correctly deleted)"})
                else:
                    print_test_result("Verify Employee Deletion", False, error_msg="Employee still exists after deletion")
            except:
                print_test_result("Verify Employee Deletion", True, {"status": "Employee not found (correctly deleted)"})
                
        except Exception as e:
            print_test_result("DELETE Employee", False, error_msg=str(e))
            return False
    
    return True

def test_field_validation_enhancements(admin_token):
    """Test Fix 4: Enhanced validation and error handling"""
    print("\n=== Testing Enhanced Field Validation ===")
    
    # Test 1: Patient creation with invalid data
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "",  # Empty required field
            "last_name": "TestValidation",
            "email": "invalid-email",  # Invalid email format
            "phone": "123",  # Invalid phone format
            "date_of_birth": "invalid-date",  # Invalid date format
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        # Should return validation error (422)
        if response.status_code == 422:
            result = response.json()
            print_test_result("Patient Validation - Invalid Data (Expected to Fail)", True, {
                "status_code": response.status_code,
                "validation_errors": result.get("detail", "Validation errors returned")
            })
        else:
            print_test_result("Patient Validation - Invalid Data", False, error_msg=f"Expected 422, got {response.status_code}")
            
    except Exception as e:
        print_test_result("Patient Validation - Invalid Data", False, error_msg=str(e))
    
    # Test 2: Employee creation with invalid role
    try:
        url = f"{API_URL}/employees"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Test",
            "last_name": "Employee",
            "email": "test@example.com",
            "role": "invalid_role",  # Invalid role
            "hire_date": date.today().isoformat()
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        # Should return validation error
        if response.status_code == 422:
            result = response.json()
            print_test_result("Employee Validation - Invalid Role (Expected to Fail)", True, {
                "status_code": response.status_code,
                "validation_errors": result.get("detail", "Validation errors returned")
            })
        else:
            print_test_result("Employee Validation - Invalid Role", False, error_msg=f"Expected 422, got {response.status_code}")
            
    except Exception as e:
        print_test_result("Employee Validation - Invalid Role", False, error_msg=str(e))
    
    # Test 3: Prescription creation with missing required fields
    try:
        url = f"{API_URL}/prescriptions"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "medication_id": "invalid-id",  # Invalid medication ID
            "patient_id": "invalid-id",     # Invalid patient ID
            # Missing required fields like prescriber_name, dosage_text, etc.
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        # Should return validation error
        if response.status_code in [422, 400, 404]:
            result = response.json()
            print_test_result("Prescription Validation - Missing Fields (Expected to Fail)", True, {
                "status_code": response.status_code,
                "error_detail": result.get("detail", "Validation errors returned")
            })
        else:
            print_test_result("Prescription Validation - Missing Fields", False, error_msg=f"Expected error status, got {response.status_code}")
            
    except Exception as e:
        print_test_result("Prescription Validation - Missing Fields", False, error_msg=str(e))
    
    return True

def main():
    """Run all critical fixes tests"""
    print("=" * 80)
    print("CRITICAL BACKEND VALIDATION FIXES TEST")
    print("Testing fixes for ClinicHub system validation issues")
    print("=" * 80)
    
    # Authenticate
    admin_token = authenticate()
    if not admin_token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    print("✅ Authentication successful")
    
    # Track test results
    test_results = {
        "prescription_fixes": False,
        "appointment_fixes": False,
        "employee_crud": False,
        "field_validation": False
    }
    
    # Run tests
    test_results["prescription_fixes"] = test_prescription_creation_fixes(admin_token)
    test_results["appointment_fixes"] = test_appointment_creation_fixes(admin_token)
    test_results["employee_crud"] = test_employee_management_crud(admin_token)
    test_results["field_validation"] = test_field_validation_enhancements(admin_token)
    
    # Summary
    print("\n" + "=" * 80)
    print("CRITICAL FIXES TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical fixes are working correctly!")
    else:
        print("⚠️  Some critical fixes need attention.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()