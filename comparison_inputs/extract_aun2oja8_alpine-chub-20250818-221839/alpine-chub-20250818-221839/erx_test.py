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

def test_authentication():
    print("\n--- Testing Authentication ---")
    
    # Test Login with Admin Credentials
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
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

def test_erx_system():
    print("\n--- Testing eRx (Electronic Prescribing) System ---")
    
    # First, authenticate to get admin token
    admin_token = test_authentication()
    if not admin_token:
        print("Authentication failed, cannot proceed with eRx testing")
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
        return
    
    # Test 2: Get All Medications (without search/filter)
    medication_id = None
    try:
        url = f"{API_URL}/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Check if we got any medications
        if len(result) > 0:
            print(f"Found {len(result)} medications")
            medication_id = result[0]["id"]
            print(f"Using medication ID: {medication_id}")
            print_test_result("Get All Medications", True, result)
        else:
            print("No medications found")
            print_test_result("Get All Medications", False, result)
    except Exception as e:
        print(f"Error getting medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Medications", False)
    
    # Test 3: Get Medication Details
    if medication_id:
        try:
            url = f"{API_URL}/medications/{medication_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify detailed medication information
            assert result["id"] == medication_id
            
            print_test_result("Get Medication Details", True, result)
        except Exception as e:
            print(f"Error getting medication details: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Medication Details", False)
    
    # Test 4: Create a test patient if medication_id is available
    patient_id = None
    if medication_id:
        try:
            url = f"{API_URL}/patients"
            data = {
                "first_name": "Test",
                "last_name": "Patient",
                "email": "test.patient@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1985-06-15",
                "gender": "female",
                "address_line1": "123 Test St",
                "city": "Testville",
                "state": "TS",
                "zip_code": "12345"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            patient_id = result["id"]
            print(f"Created test patient with ID: {patient_id}")
            print_test_result("Create Test Patient", True, result)
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Test Patient", False)
    
    # Test 5: Create Prescription
    prescription_id = None
    if medication_id and patient_id:
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
            
            # Verify FHIR MedicationRequest structure
            assert result["resource_type"] == "MedicationRequest"
            assert result["medication_id"] == medication_id
            assert result["patient_id"] == patient_id
            assert "prescription_number" in result
            assert result["prescription_number"].startswith("RX")
            
            prescription_id = result["id"]
            print(f"Created prescription with ID: {prescription_id}")
            print_test_result("Create Prescription", True, result)
        except Exception as e:
            print(f"Error creating prescription: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Prescription", False)
    
    # Test 6: Get Patient Prescriptions
    if patient_id:
        try:
            url = f"{API_URL}/patients/{patient_id}/prescriptions"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify prescriptions are returned
            assert isinstance(result, list)
            if len(result) > 0:
                assert result[0]["patient_id"] == patient_id
            
            print_test_result("Get Patient Prescriptions", True, result)
        except Exception as e:
            print(f"Error getting patient prescriptions: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Patient Prescriptions", False)
    
    # Test 7: Update Prescription Status
    if prescription_id:
        try:
            url = f"{API_URL}/prescriptions/{prescription_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "active"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Prescription Status", True, result)
        except Exception as e:
            print(f"Error updating prescription status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Prescription Status", False)
    
    # Test 8: Check Prescription Interactions
    if prescription_id:
        try:
            url = f"{API_URL}/prescriptions/{prescription_id}/interactions"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify interaction checking
            assert "interactions" in result
            
            print_test_result("Check Prescription Interactions", True, result)
        except Exception as e:
            print(f"Error checking prescription interactions: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Check Prescription Interactions", False)
    
    # Test 9: Check Drug-Drug Interactions
    try:
        # First get two medication IDs
        url = f"{API_URL}/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if len(medications) >= 2:
            drug1_id = medications[0]["id"]
            drug2_id = medications[1]["id"]
            
            url = f"{API_URL}/drug-interactions"
            params = {"drug1_id": drug1_id, "drug2_id": drug2_id}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Verify interaction data structure
            assert "interaction" in result
            
            print_test_result("Check Drug-Drug Interactions", True, result)
        else:
            print("Not enough medications to test drug interactions")
            print_test_result("Check Drug-Drug Interactions", False)
    except Exception as e:
        print(f"Error checking drug interactions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Check Drug-Drug Interactions", False)

if __name__ == "__main__":
    test_erx_system()