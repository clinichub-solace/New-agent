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
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            if isinstance(response, dict) or isinstance(response, list):
                print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
            else:
                print(f"   Response: {response}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

# Test Authentication System to get admin token
def test_authentication():
    print("\n--- Testing Authentication ---")
    
    # Login with Admin Credentials
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
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print_test_result("Admin Login", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    return admin_token

def test_ehr_endpoints(admin_token):
    print("\n--- Testing EHR Endpoints ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
    
    # Test 1: GET /api/patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/patients", True, result)
    except Exception as e:
        print_test_result("GET /api/patients", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 2: GET /api/encounters
    try:
        url = f"{API_URL}/encounters"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/encounters", True, result)
    except Exception as e:
        print_test_result("GET /api/encounters", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 3: POST /api/encounters
    # First get a patient ID to use
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        patients = response.json()
        
        if patients and len(patients) > 0:
            patient_id = patients[0]["id"]
    except Exception:
        pass
    
    if patient_id:
        try:
            url = f"{API_URL}/encounters"
            data = {
                "patient_id": patient_id,
                "encounter_type": "follow_up",
                "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "provider": "Dr. Michael Chen",
                "location": "Main Clinic - Room 105",
                "chief_complaint": "Persistent headache",
                "reason_for_visit": "Follow-up for headache treatment"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("POST /api/encounters", True, result)
        except Exception as e:
            print_test_result("POST /api/encounters", False, error=str(e))
            if 'response' in locals():
                print(f"   Status code: {response.status_code}")
                print(f"   Response text: {response.text}")
    else:
        print_test_result("POST /api/encounters", False, error="No patient ID available for testing")
    
    # Test 4: GET /api/vitals
    try:
        url = f"{API_URL}/vital-signs"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/vitals", True, result)
    except Exception as e:
        print_test_result("GET /api/vitals", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 5: GET /api/medications
    try:
        url = f"{API_URL}/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/medications", True, result)
    except Exception as e:
        print_test_result("GET /api/medications", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")

def test_erx_endpoints(admin_token):
    print("\n--- Testing eRx (Electronic Prescribing) Endpoints ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
    
    # Test 1: GET /api/prescriptions
    try:
        url = f"{API_URL}/prescriptions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/prescriptions", True, result)
    except Exception as e:
        print_test_result("GET /api/prescriptions", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 2: POST /api/prescriptions
    # First get a patient ID and medication ID to use
    patient_id = None
    medication_id = None
    
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        patients = response.json()
        
        if patients and len(patients) > 0:
            patient_id = patients[0]["id"]
    except Exception:
        pass
    
    try:
        # Try to get a medication ID from the regular medications endpoint
        url = f"{API_URL}/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if medications and len(medications) > 0:
            # Check if this is a list of patient medications or FHIR medications
            if "medication_name" in medications[0]:
                # This is a patient medication, not a FHIR medication
                medication_id = None
            else:
                medication_id = medications[0]["id"]
    except Exception:
        pass
    
    if patient_id and medication_id:
        try:
            url = f"{API_URL}/prescriptions"
            data = {
                "medication_id": medication_id,
                "patient_id": patient_id,
                "prescriber_id": "prescriber-123",
                "prescriber_name": "Dr. Sarah Johnson",
                
                # Dosage Information
                "dosage_text": "Take 1 tablet by mouth once daily",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "DAILY",
                "route": "oral",
                
                # Prescription Details
                "quantity": 30.0,
                "days_supply": 30,
                "refills": 2,
                
                # Clinical Context
                "indication": "Hypertension",
                "diagnosis_codes": ["I10"],
                "special_instructions": "Take in the morning",
                
                "created_by": "admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("POST /api/prescriptions", True, result)
        except Exception as e:
            print_test_result("POST /api/prescriptions", False, error=str(e))
            if 'response' in locals():
                print(f"   Status code: {response.status_code}")
                print(f"   Response text: {response.text}")
    else:
        print_test_result("POST /api/prescriptions", False, error="Missing patient ID or medication ID for testing")
    
    # Test 3: GET /api/erx/medications
    try:
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/medications", True, result)
    except Exception as e:
        print_test_result("GET /api/erx/medications", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 4: POST /api/erx/init
    if patient_id:
        try:
            url = f"{API_URL}/erx/init"
            data = {
                "patient_id": patient_id,
                "provider_id": "provider-123"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("POST /api/erx/init", True, result)
        except Exception as e:
            print_test_result("POST /api/erx/init", False, error=str(e))
            if 'response' in locals():
                print(f"   Status code: {response.status_code}")
                print(f"   Response text: {response.text}")
    else:
        print_test_result("POST /api/erx/init", False, error="No patient ID available for testing")
    
    # Test 5: GET /api/erx/formulary
    try:
        url = f"{API_URL}/erx/formulary"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /api/erx/formulary", True, result)
    except Exception as e:
        print_test_result("GET /api/erx/formulary", False, error=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING EHR AND ERX FUNCTIONALITY")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    # Test EHR endpoints
    test_ehr_endpoints(admin_token)
    
    # Test eRx endpoints
    test_erx_endpoints(admin_token)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()