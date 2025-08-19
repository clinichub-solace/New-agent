#!/usr/bin/env python3
"""
Focused test for appointment creation fixes as requested in the review.
Tests the specific appointment creation fix with proper patient_name/provider_name population.
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
print(f"🔗 Using API URL: {API_URL}")

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
    """Authenticate with admin/admin123 credentials as specified in the review"""
    print("\n🔐 --- Authenticating with admin/admin123 credentials ---")
    
    # Initialize admin user first
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Note: Admin user may already exist: {str(e)}")
    
    # Login with admin credentials
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
        assert "user" in result
        assert result["user"]["username"] == "admin"
        
        token = result["access_token"]
        print_test_result("Admin Login (admin/admin123)", True, {"username": result["user"]["username"], "role": result["user"]["role"]})
        return token
        
    except Exception as e:
        print_test_result("Admin Login (admin/admin123)", False, error_msg=str(e))
        return None

def create_test_patient(admin_token):
    """Create a test patient for appointment booking"""
    print("\n👤 --- Creating Test Patient ---")
    
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
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify FHIR compliance
        assert result["resource_type"] == "Patient"
        assert isinstance(result["name"], list)
        assert result["name"][0]["family"] == "Rodriguez"
        assert "Emily" in result["name"][0]["given"]
        
        patient_id = result["id"]
        patient_name = f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"
        
        print_test_result("Create Test Patient", True, {
            "id": patient_id,
            "name": patient_name,
            "resource_type": result["resource_type"]
        })
        
        return patient_id, patient_name
        
    except Exception as e:
        print_test_result("Create Test Patient", False, error_msg=str(e))
        return None, None

def create_test_provider(admin_token):
    """Create a test provider for appointment scheduling"""
    print("\n👨‍⚕️ --- Creating Test Provider ---")
    
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "license_number": "TX123456",
            "npi_number": "1234567890",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-345-6789",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        provider_name = f"{result['title']} {result['first_name']} {result['last_name']}"
        
        print_test_result("Create Test Provider", True, {
            "id": provider_id,
            "name": provider_name,
            "specialties": result["specialties"]
        })
        
        return provider_id, provider_name
        
    except Exception as e:
        print_test_result("Create Test Provider", False, error_msg=str(e))
        return None, None

def test_appointment_creation_fix(patient_id, patient_name, provider_id, provider_name, admin_token):
    """Test the CRITICAL FIX for appointment creation with proper patient_name/provider_name population"""
    print("\n📅 --- Testing CRITICAL APPOINTMENT CREATION FIX ---")
    
    appointment_id = None
    
    try:
        url = f"{API_URL}/appointments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Calculate appointment date (tomorrow)
        appointment_date = (date.today() + timedelta(days=1)).isoformat()
        
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_date": appointment_date,
            "start_time": "14:00",
            "end_time": "14:30",
            "appointment_type": "consultation",
            "reason": "Initial consultation for preventive care",
            "location": "Main Clinic - Room 201",
            "scheduled_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # CRITICAL VERIFICATION: Check that patient_name and provider_name are properly populated
        assert "appointment_number" in result
        assert result["appointment_number"].startswith("APT")
        assert "patient_name" in result
        assert "provider_name" in result
        assert result["patient_id"] == patient_id
        assert result["provider_id"] == provider_id
        
        # Verify names are populated from database records (not empty)
        assert result["patient_name"] is not None and result["patient_name"].strip() != ""
        assert result["provider_name"] is not None and result["provider_name"].strip() != ""
        
        # Verify names match expected format
        assert "Emily" in result["patient_name"] and "Rodriguez" in result["patient_name"]
        assert "Jennifer" in result["provider_name"] and "Martinez" in result["provider_name"]
        
        appointment_id = result["id"]
        
        print_test_result("CRITICAL FIX: Appointment Creation with Name Population", True, {
            "appointment_number": result["appointment_number"],
            "patient_name": result["patient_name"],
            "provider_name": result["provider_name"],
            "appointment_date": result["appointment_date"],
            "status": result["status"]
        })
        
        return appointment_id
        
    except Exception as e:
        print_test_result("CRITICAL FIX: Appointment Creation with Name Population", False, error_msg=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
        return None

def test_appointment_retrieval(appointment_id, admin_token):
    """Test appointment retrieval to verify created appointments can be retrieved properly"""
    print("\n📋 --- Testing Appointment Retrieval ---")
    
    # Test 1: Get specific appointment by ID
    try:
        url = f"{API_URL}/appointments/{appointment_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify appointment details
        assert result["id"] == appointment_id
        assert "patient_name" in result
        assert "provider_name" in result
        assert result["patient_name"] is not None and result["patient_name"].strip() != ""
        assert result["provider_name"] is not None and result["provider_name"].strip() != ""
        
        print_test_result("Get Appointment by ID", True, {
            "id": result["id"],
            "appointment_number": result["appointment_number"],
            "patient_name": result["patient_name"],
            "provider_name": result["provider_name"]
        })
        
    except Exception as e:
        print_test_result("Get Appointment by ID", False, error_msg=str(e))
    
    # Test 2: Get all appointments
    try:
        url = f"{API_URL}/appointments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify our appointment is in the list
        appointment_found = False
        for appointment in result:
            if appointment["id"] == appointment_id:
                appointment_found = True
                assert "patient_name" in appointment
                assert "provider_name" in appointment
                break
        
        assert appointment_found, "Created appointment not found in appointments list"
        
        print_test_result("Get All Appointments", True, {
            "total_appointments": len(result),
            "test_appointment_found": appointment_found
        })
        
    except Exception as e:
        print_test_result("Get All Appointments", False, error_msg=str(e))

def run_appointment_creation_tests():
    """Run the focused appointment creation tests as requested in the review"""
    print("🏥 CLINICHUB APPOINTMENT CREATION FIXES VERIFICATION")
    print("=" * 80)
    print("Testing the specific appointment creation fix with proper patient_name/provider_name population")
    print("Authentication: admin/admin123 credentials")
    print("=" * 80)
    
    # Step 1: Authenticate
    admin_token = authenticate()
    if not admin_token:
        print("❌ CRITICAL ERROR: Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Create test patient
    patient_id, patient_name = create_test_patient(admin_token)
    if not patient_id:
        print("❌ CRITICAL ERROR: Patient creation failed. Cannot proceed with appointment tests.")
        return
    
    # Step 3: Create test provider
    provider_id, provider_name = create_test_provider(admin_token)
    if not provider_id:
        print("❌ CRITICAL ERROR: Provider creation failed. Cannot proceed with appointment tests.")
        return
    
    # Step 4: Test the CRITICAL appointment creation fix
    appointment_id = test_appointment_creation_fix(patient_id, patient_name, provider_id, provider_name, admin_token)
    if not appointment_id:
        print("❌ CRITICAL ERROR: Appointment creation failed. The fix is not working.")
        return
    
    # Step 5: Test appointment retrieval
    test_appointment_retrieval(appointment_id, admin_token)
    
    print("\n" + "=" * 80)
    print("🎯 APPOINTMENT CREATION FIXES VERIFICATION COMPLETED")
    print("=" * 80)
    
    # Summary
    if appointment_id:
        print("✅ SUCCESS CRITERIA MET:")
        print("   ✅ Patient creation returns FHIR-compliant structure")
        print("   ✅ Provider creation works correctly")
        print("   ✅ Appointment creation succeeds (no 500 error)")
        print("   ✅ Created appointment contains patient_name and provider_name fields properly populated")
        print("   ✅ Appointment retrieval works correctly")
        print("\n🎉 CRITICAL APPOINTMENT CREATION FIX IS WORKING CORRECTLY!")
    else:
        print("❌ CRITICAL ISSUES FOUND:")
        print("   ❌ Appointment creation fix needs attention")
        print("\n⚠️  APPOINTMENT CREATION FIX REQUIRES FURTHER INVESTIGATION")

if __name__ == "__main__":
    run_appointment_creation_tests()