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

# Test Authentication System to get admin token
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
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

# Test Patient Management
def test_patient_management():
    print("\n--- Testing Patient Management ---")
    
    # Test creating a patient
    patient_id = None
    try:
        url = f"{API_URL}/patients"
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
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print_test_result("Create Patient", True, result)
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Patient", False)
        return None
    
    # Test getting all patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patients", True, result)
    except Exception as e:
        print(f"Error getting patients: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patients", False)
    
    return patient_id

# Test Encounter Management
def test_encounter_management(patient_id):
    print("\n--- Testing Encounter Management ---")
    
    if not patient_id:
        print("Skipping encounter tests - no patient ID available")
        return None
    
    # Test creating an encounter
    encounter_id = None
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": patient_id,
            "encounter_type": "annual_physical",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "provider": "Dr. Sarah Williams",
            "location": "Main Clinic - Room 203",
            "chief_complaint": "Annual physical examination",
            "reason_for_visit": "Yearly check-up"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        encounter_id = result["id"]
        print_test_result("Create Encounter", True, result)
    except Exception as e:
        print(f"Error creating encounter: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Encounter", False)
        return None
    
    # Test getting all encounters
    try:
        url = f"{API_URL}/encounters"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Encounters", True, result)
    except Exception as e:
        print(f"Error getting all encounters: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Encounters", False)
    
    return encounter_id

# Test Vital Signs Recording
def test_vital_signs(patient_id, encounter_id):
    print("\n--- Testing Vital Signs Recording ---")
    
    if not patient_id or not encounter_id:
        print("Skipping vital signs tests - missing patient or encounter ID")
        return
    
    # Test creating vital signs
    try:
        url = f"{API_URL}/vital-signs"
        data = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "height": 175.5,  # cm
            "weight": 70.3,   # kg
            "bmi": 22.8,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature": 37.0,
            "oxygen_saturation": 98,
            "pain_scale": 0,
            "recorded_by": "Nurse Johnson"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Vital Signs", True, result)
    except Exception as e:
        print(f"Error creating vital signs: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Vital Signs", False)
    
    # Test getting vital signs by patient
    try:
        url = f"{API_URL}/vital-signs/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Vital Signs", True, result)
    except Exception as e:
        print(f"Error getting patient vital signs: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Vital Signs", False)

# Test Medication Management
def test_medication_management(patient_id):
    print("\n--- Testing Medication Management ---")
    
    if not patient_id:
        print("Skipping medication tests - no patient ID available")
        return None
    
    # Test creating a medication
    medication_id = None
    try:
        url = f"{API_URL}/medications"
        data = {
            "patient_id": patient_id,
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "route": "oral",
            "start_date": date.today().isoformat(),
            "prescribing_physician": "Dr. Sarah Williams",
            "indication": "Hypertension",
            "notes": "Take in the morning with food"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        medication_id = result["id"]
        print_test_result("Create Medication", True, result)
    except Exception as e:
        print(f"Error creating medication: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Medication", False)
        return None
    
    # Test getting medications by patient
    try:
        url = f"{API_URL}/medications/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Medications", True, result)
    except Exception as e:
        print(f"Error getting patient medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Medications", False)
    
    return medication_id

# Test eRx (Electronic Prescribing) System
def test_erx_system(patient_id, admin_token):
    print("\n--- Testing eRx (Electronic Prescribing) System ---")
    
    if not patient_id or not admin_token:
        print("Skipping eRx tests - missing patient ID or admin token")
        return
    
    # Test 1: Initialize eRx Data
    try:
        url = f"{API_URL}/init-erx-data"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize eRx Data", True, result)
    except Exception as e:
        print(f"Error initializing eRx data: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize eRx Data", False)
    
    # Test 2: Get FHIR Medications
    medication_id = None
    try:
        url = f"{API_URL}/erx/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if len(result) > 0:
            medication_id = result[0]["id"]
        
        print_test_result("Get FHIR Medications", True, result)
    except Exception as e:
        print(f"Error getting FHIR medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get FHIR Medications", False)
    
    # Test 3: Get Formulary
    try:
        url = f"{API_URL}/erx/formulary"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Formulary", True, result)
    except Exception as e:
        print(f"Error getting formulary: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Formulary", False)
    
    # Test 4: Initialize eRx Session
    try:
        url = f"{API_URL}/erx/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "provider_id": "provider-123"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize eRx Session", True, result)
    except Exception as e:
        print(f"Error initializing eRx session: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize eRx Session", False)
    
    # Test 5: Create Prescription
    if medication_id:
        try:
            url = f"{API_URL}/prescriptions"
            headers = {"Authorization": f"Bearer {admin_token}"}
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
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Create Prescription", True, result)
        except Exception as e:
            print(f"Error creating prescription: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Prescription", False)
    
    # Test 6: Get Prescriptions
    try:
        url = f"{API_URL}/prescriptions"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Prescriptions", True, result)
    except Exception as e:
        print(f"Error getting prescriptions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Prescriptions", False)

def run_ehr_erx_tests():
    print("\n" + "=" * 80)
    print("TESTING EHR AND ERX FUNCTIONALITY")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    # Test patient management to get a patient ID
    patient_id = test_patient_management()
    
    # Test EHR functionality
    encounter_id = test_encounter_management(patient_id)
    test_vital_signs(patient_id, encounter_id)
    test_medication_management(patient_id)
    
    # Test eRx functionality
    if admin_token and patient_id:
        test_erx_system(patient_id, admin_token)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_ehr_erx_tests()