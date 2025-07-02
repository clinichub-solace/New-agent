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

# Test Authentication to get admin token
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify admin initialization response
        assert "message" in result
        assert "username" in result
        assert "password" in result
        assert result["username"] == "admin"
        assert result["password"] == "admin123"
        
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Admin User", False)
    
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
        
        # Verify login response
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    return admin_token

# Test FHIR-Compliant Patient Management to get a patient ID
def test_patient_management(admin_token):
    print("\n--- Testing FHIR-Compliant Patient Management ---")
    
    # Test creating a patient
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1985-06-15",
            "gender": "female",
            "address_line1": "123 Medical Center Blvd",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify FHIR compliance
        assert result["resource_type"] == "Patient"
        assert isinstance(result["name"], list)
        assert result["name"][0]["family"] == "Johnson"
        assert "Sarah" in result["name"][0]["given"]
        
        patient_id = result["id"]
        print_test_result("Create Patient", True, result)
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Patient", False)
    
    return patient_id

# Test Lab Integration
def test_lab_integration(admin_token, patient_id, provider_id=None):
    print("\n--- Testing Lab Integration ---")
    
    # If no provider_id is provided, create a provider
    if not provider_id:
        try:
            url = f"{API_URL}/providers"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "first_name": "Robert",
                "last_name": "Wilson",
                "title": "Dr.",
                "specialties": ["Cardiology", "Internal Medicine"],
                "license_number": "MD12345",
                "npi_number": "1234567890",
                "email": "dr.wilson@clinichub.com",
                "phone": "+1-555-789-0123"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            provider_id = result["id"]
            print_test_result("Create Provider for Lab Tests", True, result)
        except Exception as e:
            print(f"Error creating provider: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Provider for Lab Tests", False)
            return None
    
    # Test 1: Initialize Lab Tests
    try:
        url = f"{API_URL}/lab-tests/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Lab Tests", True, result)
    except Exception as e:
        print(f"Error initializing lab tests: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Lab Tests", False)
    
    # Test 2: Get Lab Tests
    lab_test_ids = []
    try:
        url = f"{API_URL}/lab-tests"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Store lab test IDs for later use
        if len(result) > 0:
            lab_test_ids = [test["id"] for test in result[:3]]  # Get first 3 tests
        
        print_test_result("Get Lab Tests", True, result)
    except Exception as e:
        print(f"Error getting lab tests: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Lab Tests", False)
    
    # Test 3: Initialize ICD-10 Codes
    try:
        url = f"{API_URL}/icd10/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize ICD-10 Codes", True, result)
    except Exception as e:
        print(f"Error initializing ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize ICD-10 Codes", False)
    
    # Test 4: Search ICD-10 Codes
    icd10_codes = []
    try:
        url = f"{API_URL}/icd10/search"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Store ICD-10 codes for later use
        if len(result) > 0:
            icd10_codes = [code["code"] for code in result[:2]]  # Get first 2 codes
        
        print_test_result("Search ICD-10 Codes", True, result)
    except Exception as e:
        print(f"Error searching ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search ICD-10 Codes", False)
    
    # Test 5: Create Lab Order
    lab_order_id = None
    if patient_id and provider_id and lab_test_ids and icd10_codes:
        try:
            url = f"{API_URL}/lab-orders"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "lab_tests": lab_test_ids,
                "icd10_codes": icd10_codes,
                "status": "ordered",
                "priority": "routine",
                "notes": "Patient fasting for 12 hours"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            lab_order_id = result["id"]
            print_test_result("Create Lab Order", True, result)
        except Exception as e:
            print(f"Error creating lab order: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Lab Order", False)
    else:
        print("Skipping Create Lab Order test - missing required IDs")
    
    # Test 6: Get Lab Orders
    try:
        url = f"{API_URL}/lab-orders"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Lab Orders", True, result)
    except Exception as e:
        print(f"Error getting lab orders: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Lab Orders", False)
    
    # Test 7: Get Specific Lab Order
    if lab_order_id:
        try:
            url = f"{API_URL}/lab-orders/{lab_order_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Lab Order by ID", True, result)
        except Exception as e:
            print(f"Error getting lab order by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Lab Order by ID", False)
    
    return lab_order_id

# Test Insurance Verification
def test_insurance_verification(admin_token, patient_id):
    print("\n--- Testing Insurance Verification ---")
    
    # Test 1: Create Insurance Card
    insurance_card_id = None
    try:
        url = f"{API_URL}/insurance/cards"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "insurance_type": "commercial",
            "payer_name": "Blue Cross Blue Shield",
            "payer_id": "BCBS123",
            "member_id": "XYZ987654321",
            "group_number": "GRP12345",
            "policy_number": "POL987654",
            "subscriber_name": "Sarah Johnson",
            "subscriber_dob": "1985-06-15",
            "relationship_to_subscriber": "self",
            "effective_date": "2023-01-01",
            "copay_primary": 25.00,
            "copay_specialist": 40.00,
            "deductible": 1500.00,
            "deductible_met": 500.00,
            "out_of_pocket_max": 5000.00,
            "out_of_pocket_met": 1200.00,
            "is_primary": True
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        insurance_card_id = result["id"]
        print_test_result("Create Insurance Card", True, result)
    except Exception as e:
        print(f"Error creating insurance card: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Insurance Card", False)
    
    # Test 2: Get Patient Insurance
    try:
        url = f"{API_URL}/insurance/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Insurance", True, result)
    except Exception as e:
        print(f"Error getting patient insurance: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Insurance", False)
    
    # Test 3: Verify Eligibility
    eligibility_id = None
    if insurance_card_id:
        try:
            url = f"{API_URL}/insurance/verify-eligibility"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "insurance_card_id": insurance_card_id,
                "service_date": date.today().isoformat(),
                "service_type": "office_visit"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            eligibility_id = result["id"]
            print_test_result("Verify Eligibility", True, result)
        except Exception as e:
            print(f"Error verifying eligibility: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Verify Eligibility", False)
    else:
        print("Skipping Verify Eligibility test - no insurance card ID available")
    
    # Test 4: Get Patient Eligibility
    try:
        url = f"{API_URL}/insurance/eligibility/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Eligibility", True, result)
    except Exception as e:
        print(f"Error getting patient eligibility: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Eligibility", False)
    
    # Test 5: Create Prior Authorization (optional)
    if insurance_card_id and patient_id:
        try:
            url = f"{API_URL}/insurance/prior-auth"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "insurance_card_id": insurance_card_id,
                "provider_id": "provider-123",  # This is a placeholder
                "service_code": "99214",  # CPT code for office visit
                "service_description": "Office visit, established patient, moderate complexity",
                "diagnosis_codes": ["E11.9"],  # Type 2 diabetes without complications
                "submitted_by": "Dr. Robert Wilson"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Create Prior Authorization", True, result)
        except Exception as e:
            print(f"Error creating prior authorization: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Prior Authorization", False)
    
    # Test 6: Get Patient Prior Authorizations (optional)
    try:
        url = f"{API_URL}/insurance/prior-auth/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Prior Authorizations", True, result)
    except Exception as e:
        print(f"Error getting patient prior authorizations: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Prior Authorizations", False)
    
    return insurance_card_id, eligibility_id

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING LAB INTEGRATION AND INSURANCE VERIFICATION")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    if not admin_token:
        print("Authentication failed. Cannot proceed with tests.")
        return
    
    # Create a test patient
    patient_id = test_patient_management(admin_token)
    if not patient_id:
        print("Patient creation failed. Cannot proceed with tests.")
        return
    
    # Test Lab Integration
    lab_order_id = test_lab_integration(admin_token, patient_id)
    
    # Test Insurance Verification
    insurance_card_id, eligibility_id = test_insurance_verification(admin_token, patient_id)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()