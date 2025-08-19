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
def get_admin_token():
    print("\n--- Getting Admin Token ---")
    
    try:
        # Try to initialize admin user (may fail if already exists)
        try:
            url = f"{API_URL}/auth/init-admin"
            response = requests.post(url)
            response.raise_for_status()
            print("Admin user initialized successfully")
        except:
            print("Admin user already exists, proceeding with login")
        
        # Login with admin credentials
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, {"token": admin_token[:20] + "..."})
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

# Create a test patient
def create_test_patient(admin_token):
    print("\n--- Creating Test Patient ---")
    
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Insurance",
            "last_name": "TestPatient",
            "email": "insurance.test@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1985-06-15",
            "gender": "female",
            "address_line1": "123 Test Street",
            "city": "Testville",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print_test_result("Create Test Patient", True, result)
        return patient_id
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Patient", False)
        return None

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
            "subscriber_name": "Insurance TestPatient",
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
        return None, None
    
    # Test 2: Verify Eligibility
    eligibility_id = None
    if insurance_card_id:
        try:
            url = f"{API_URL}/insurance/verify-eligibility"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "insurance_card_id": insurance_card_id,
                "service_date": date.today().isoformat(),
                "service_type": "office_visit"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify the response structure
            assert "id" in result
            assert "eligibility_status" in result
            assert "benefits_summary" in result
            assert "copay_amounts" in result
            assert "deductible_info" in result
            assert "coverage_details" in result
            assert "prior_auth_required" in result
            assert "valid_until" in result
            
            eligibility_id = result["id"]
            print_test_result("Verify Eligibility", True, result)
        except Exception as e:
            print(f"Error verifying eligibility: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Verify Eligibility", False)
            return insurance_card_id, None
    
    # Test 3: Get Patient Eligibility
    if patient_id:
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
    
    return insurance_card_id, eligibility_id

def main():
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Exiting.")
        return
    
    # Create test patient
    patient_id = create_test_patient(admin_token)
    if not patient_id:
        print("Failed to create test patient. Exiting.")
        return
    
    # Test insurance verification
    insurance_card_id, eligibility_id = test_insurance_verification(admin_token, patient_id)
    
    if eligibility_id:
        print("\n✅ INSURANCE VERIFICATION TEST PASSED: Successfully created insurance card and verified eligibility")
    else:
        print("\n❌ INSURANCE VERIFICATION TEST FAILED: Could not verify eligibility")

if __name__ == "__main__":
    main()