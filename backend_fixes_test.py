#!/usr/bin/env python3
"""
Backend Fixes Verification Test
Tests the 3 specific backend issues that were just fixed:
1. Appointment Enum Fix - Test GET /api/appointments to ensure 'telemedicine' type is now accepted
2. Prescription Creation Fix - Test POST /api/prescriptions with basic prescription data
3. Lab Order Patient Validation Fix - Test POST /api/lab-orders with proper patient and provider data
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
print(f"🔧 BACKEND FIXES VERIFICATION")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Global variables for test data
auth_token = None
test_patient_id = None
test_provider_id = None
test_medication_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, details=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if details:
            print(f"   Details: {details}")
        if response and isinstance(response, dict):
            # Print key response fields
            if 'id' in response:
                print(f"   ID: {response['id']}")
            if 'status' in response:
                print(f"   Status: {response['status']}")
    else:
        print(f"❌ {test_name}: FAILED")
        if details:
            print(f"   Error: {details}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Authenticate with admin credentials"""
    global auth_token
    print("\n🔐 AUTHENTICATION TEST")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get("access_token")
            print_test_result("Admin Authentication", True, result, "Successfully authenticated with admin/admin123")
            return True
        else:
            print_test_result("Admin Authentication", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Admin Authentication", False, None, str(e))
        return False

def get_auth_headers():
    """Get authentication headers"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def setup_test_data():
    """Create test patient, provider, and medication for testing"""
    global test_patient_id, test_provider_id, test_medication_id
    print("\n📋 SETTING UP TEST DATA")
    
    # Create test patient
    try:
        url = f"{API_URL}/patients"
        patient_data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-987-6543",
            "date_of_birth": "1990-03-15",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=patient_data, headers=get_auth_headers())
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_patient_id = result.get("id")
            print_test_result("Test Patient Creation", True, result, f"Created patient: Emily Rodriguez")
        else:
            print_test_result("Test Patient Creation", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Test Patient Creation", False, None, str(e))
        return False
    
    # Create test provider
    try:
        url = f"{API_URL}/providers"
        provider_data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "license_number": "TX123456",
            "npi_number": "1234567890",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-555-0123"
        }
        
        response = requests.post(url, json=provider_data, headers=get_auth_headers())
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_provider_id = result.get("id")
            print_test_result("Test Provider Creation", True, result, f"Created provider: Dr. Jennifer Martinez")
        else:
            print_test_result("Test Provider Creation", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Test Provider Creation", False, None, str(e))
        return False
    
    # Initialize eRx system and get a medication
    try:
        # Initialize eRx system
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=get_auth_headers())
        
        if response.status_code in [200, 201]:
            print_test_result("eRx System Initialization", True, None, "eRx system initialized")
        
        # Get medications list
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=get_auth_headers())
        
        if response.status_code == 200:
            medications = response.json()
            if medications and len(medications) > 0:
                test_medication_id = medications[0].get("id")
                print_test_result("Test Medication Setup", True, None, f"Using medication: {medications[0].get('generic_name', 'Unknown')}")
            else:
                print_test_result("Test Medication Setup", False, None, "No medications available")
                return False
        else:
            print_test_result("Test Medication Setup", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Test Medication Setup", False, None, str(e))
        return False
    
    return True

def test_appointment_enum_fix():
    """Test ISSUE 1: Appointment Enum Fix - 'telemedicine' type acceptance"""
    print("\n🏥 ISSUE 1: APPOINTMENT ENUM FIX TEST")
    print("Testing GET /api/appointments to ensure 'telemedicine' type is now accepted")
    
    # First create an appointment with telemedicine type
    try:
        url = f"{API_URL}/appointments"
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": test_provider_id,
            "appointment_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "10:30",
            "appointment_type": "telemedicine",  # This was causing 500 errors before
            "reason": "Follow-up consultation via telemedicine",
            "scheduled_by": "admin"
        }
        
        response = requests.post(url, json=appointment_data, headers=get_auth_headers())
        
        if response.status_code in [200, 201]:
            result = response.json()
            appointment_id = result.get("id")
            print_test_result("Create Telemedicine Appointment", True, result, "Successfully created appointment with 'telemedicine' type")
            
            # Now test GET /api/appointments to ensure no 500 errors
            url = f"{API_URL}/appointments"
            response = requests.get(url, headers=get_auth_headers())
            
            if response.status_code == 200:
                appointments = response.json()
                telemedicine_found = False
                for apt in appointments:
                    if apt.get("appointment_type") == "telemedicine":
                        telemedicine_found = True
                        break
                
                if telemedicine_found:
                    print_test_result("GET Appointments with Telemedicine", True, None, "Successfully retrieved appointments including telemedicine type")
                    return True
                else:
                    print_test_result("GET Appointments with Telemedicine", False, None, "Telemedicine appointment not found in results")
                    return False
            else:
                print_test_result("GET Appointments with Telemedicine", False, response.text, f"Status: {response.status_code}")
                return False
                
        else:
            print_test_result("Create Telemedicine Appointment", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Appointment Enum Fix Test", False, None, str(e))
        return False

def test_prescription_creation_fix():
    """Test ISSUE 2: Prescription Creation Fix - MedicationRequest model validation"""
    print("\n💊 ISSUE 2: PRESCRIPTION CREATION FIX TEST")
    print("Testing POST /api/prescriptions with basic prescription data")
    
    try:
        url = f"{API_URL}/prescriptions"
        prescription_data = {
            "medication_id": test_medication_id,
            "patient_id": test_patient_id,
            "prescriber_id": test_provider_id,
            "prescriber_name": "Dr. Jennifer Martinez",
            "dosage_text": "Take 1 tablet by mouth twice daily",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "BID",
            "route": "oral",
            "quantity": 30.0,
            "days_supply": 15,
            "refills": 2,
            "indication": "Hypertension management",
            "diagnosis_codes": ["I10"],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=prescription_data, headers=get_auth_headers())
        
        if response.status_code == 201:
            result = response.json()
            print_test_result("Prescription Creation", True, result, "Successfully created prescription with proper MedicationRequest validation")
            
            # Verify the prescription has required fields populated
            required_fields = ["status", "medication_display", "patient_display", "prescription_number"]
            missing_fields = []
            for field in required_fields:
                if field not in result or not result[field]:
                    missing_fields.append(field)
            
            if not missing_fields:
                print_test_result("Prescription Field Population", True, None, "All required fields properly populated")
                return True
            else:
                print_test_result("Prescription Field Population", False, None, f"Missing fields: {missing_fields}")
                return False
                
        else:
            print_test_result("Prescription Creation", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Prescription Creation Fix Test", False, None, str(e))
        return False

def test_lab_order_patient_validation_fix():
    """Test ISSUE 3: Lab Order Patient Validation Fix - patient name extraction"""
    print("\n🧪 ISSUE 3: LAB ORDER PATIENT VALIDATION FIX TEST")
    print("Testing POST /api/lab-orders with proper patient and provider data")
    
    try:
        # First initialize lab tests
        url = f"{API_URL}/lab-tests/init"
        response = requests.post(url, headers=get_auth_headers())
        
        if response.status_code in [200, 201]:
            print_test_result("Lab Tests Initialization", True, None, "Lab tests initialized")
        
        # Get available lab tests
        url = f"{API_URL}/lab-tests"
        response = requests.get(url, headers=get_auth_headers())
        
        if response.status_code == 200:
            lab_tests = response.json()
            if not lab_tests:
                print_test_result("Lab Tests Availability", False, None, "No lab tests available")
                return False
            
            test_lab_test = lab_tests[0]
            print_test_result("Lab Tests Availability", True, None, f"Using lab test: {test_lab_test.get('test_name', 'Unknown')}")
        else:
            print_test_result("Lab Tests Availability", False, response.text, f"Status: {response.status_code}")
            return False
        
        # Create lab order
        url = f"{API_URL}/lab-orders"
        lab_order_data = {
            "patient_id": test_patient_id,
            "provider_id": test_provider_id,
            "lab_tests": [
                {
                    "test_id": test_lab_test.get("id"),
                    "test_code": test_lab_test.get("test_code"),
                    "test_name": test_lab_test.get("test_name"),
                    "specimen_type": test_lab_test.get("specimen_type", "blood")
                }
            ],
            "icd10_codes": ["Z00.00"],  # General medical examination
            "priority": "routine",
            "clinical_notes": "Routine lab work for annual physical",
            "ordered_by": "admin"
        }
        
        response = requests.post(url, json=lab_order_data, headers=get_auth_headers())
        
        if response.status_code == 201:
            result = response.json()
            print_test_result("Lab Order Creation", True, result, "Successfully created lab order")
            
            # Verify patient name extraction works safely
            patient_name = result.get("patient_name")
            provider_name = result.get("provider_name")
            
            if patient_name and provider_name:
                print_test_result("Patient/Provider Name Extraction", True, None, f"Patient: {patient_name}, Provider: {provider_name}")
                return True
            else:
                print_test_result("Patient/Provider Name Extraction", False, None, f"Missing names - Patient: {patient_name}, Provider: {provider_name}")
                return False
                
        else:
            print_test_result("Lab Order Creation", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Lab Order Patient Validation Fix Test", False, None, str(e))
        return False

def test_no_regressions():
    """Test that authentication and other endpoints still work correctly"""
    print("\n🔍 REGRESSION TESTING")
    print("Verifying no regressions in other endpoints")
    
    # Test authentication still works
    try:
        url = f"{API_URL}/auth/me"
        response = requests.get(url, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Authentication Regression Test", True, result, "Authentication system still working")
        else:
            print_test_result("Authentication Regression Test", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Authentication Regression Test", False, None, str(e))
        return False
    
    # Test basic patient endpoint
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=get_auth_headers())
        
        if response.status_code == 200:
            patients = response.json()
            print_test_result("Patients Endpoint Regression Test", True, None, f"Retrieved {len(patients)} patients")
        else:
            print_test_result("Patients Endpoint Regression Test", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Patients Endpoint Regression Test", False, None, str(e))
        return False
    
    return True

def main():
    """Main test execution"""
    print("🔧 BACKEND FIXES VERIFICATION TEST")
    print("Testing 3 specific backend issues that were just fixed")
    print("=" * 80)
    
    # Track test results
    test_results = {
        "authentication": False,
        "test_data_setup": False,
        "appointment_enum_fix": False,
        "prescription_creation_fix": False,
        "lab_order_validation_fix": False,
        "no_regressions": False
    }
    
    # Run tests in sequence
    if authenticate():
        test_results["authentication"] = True
        
        if setup_test_data():
            test_results["test_data_setup"] = True
            
            # Test the 3 specific fixes
            test_results["appointment_enum_fix"] = test_appointment_enum_fix()
            test_results["prescription_creation_fix"] = test_prescription_creation_fix()
            test_results["lab_order_validation_fix"] = test_lab_order_patient_validation_fix()
            
            # Test for regressions
            test_results["no_regressions"] = test_no_regressions()
    
    # Print final summary
    print("\n" + "=" * 80)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print("-" * 80)
    print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL BACKEND FIXES VERIFIED SUCCESSFULLY!")
        print("✅ Issue 1: Appointment 'telemedicine' type now accepted")
        print("✅ Issue 2: Prescription creation with proper validation working")
        print("✅ Issue 3: Lab order patient validation with safe name extraction working")
        print("✅ No regressions detected in authentication or other endpoints")
    else:
        print("⚠️  SOME TESTS FAILED - Backend fixes need attention")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")
    
    print("=" * 80)

if __name__ == "__main__":
    main()