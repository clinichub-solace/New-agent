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

# Test Insurance Verification with a simplified approach
def test_insurance_verification_simple():
    print("\n--- Testing Insurance Verification (Simplified) ---")
    
    # Test 1: Login with Admin Credentials
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
        
        print(f"✅ Admin Login: PASSED")
    except Exception as e:
        print(f"❌ Admin Login: FAILED - {str(e)}")
        return
    
    # Test 2: Create a test patient
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-987-6543",
            "date_of_birth": "1980-01-15",
            "gender": "male",
            "address_line1": "456 Oak Street",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print(f"✅ Create Patient: PASSED - ID: {patient_id}")
    except Exception as e:
        print(f"❌ Create Patient: FAILED - {str(e)}")
        return
    
    # Test 3: Create Insurance Card
    insurance_card_id = None
    try:
        url = f"{API_URL}/insurance/cards"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "insurance_type": "commercial",
            "payer_name": "Aetna",
            "payer_id": "AETNA123",
            "member_id": "ABC123456789",
            "group_number": "GRP54321",
            "policy_number": "POL123456",
            "subscriber_name": "John Doe",
            "subscriber_dob": "1980-01-15",
            "relationship_to_subscriber": "self",
            "effective_date": "2023-01-01"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        insurance_card_id = result["id"]
        print(f"✅ Create Insurance Card: PASSED - ID: {insurance_card_id}")
    except Exception as e:
        print(f"❌ Create Insurance Card: FAILED - {str(e)}")
        return
    
    # Test 4: Get Patient Insurance
    try:
        url = f"{API_URL}/insurance/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Get Patient Insurance: PASSED - Found {len(result)} cards")
    except Exception as e:
        print(f"❌ Get Patient Insurance: FAILED - {str(e)}")
    
    # Test 5: Create Prior Authorization
    try:
        url = f"{API_URL}/insurance/prior-auth"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "insurance_card_id": insurance_card_id,
            "provider_id": "provider-123",
            "service_code": "99214",
            "service_description": "Office visit, established patient, moderate complexity",
            "diagnosis_codes": ["E11.9"],
            "submitted_by": "Dr. Smith"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Create Prior Authorization: PASSED - ID: {result['id']}")
    except Exception as e:
        print(f"❌ Create Prior Authorization: FAILED - {str(e)}")
    
    # Test 6: Get Patient Prior Authorizations
    try:
        url = f"{API_URL}/insurance/prior-auth/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Get Patient Prior Authorizations: PASSED - Found {len(result)} authorizations")
    except Exception as e:
        print(f"❌ Get Patient Prior Authorizations: FAILED - {str(e)}")
    
    print("\nInsurance Verification Testing Complete")

if __name__ == "__main__":
    test_insurance_verification_simple()