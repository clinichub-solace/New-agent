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

# Test Lab Integration with a simplified approach
def test_lab_integration_simple():
    print("\n--- Testing Lab Integration (Simplified) ---")
    
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
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1975-05-20",
            "gender": "female",
            "address_line1": "789 Pine Avenue",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02108"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print(f"✅ Create Patient: PASSED - ID: {patient_id}")
    except Exception as e:
        print(f"❌ Create Patient: FAILED - {str(e)}")
        return
    
    # Test 3: Create a provider
    provider_id = None
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Emily",
            "last_name": "Johnson",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Pediatrics"],
            "license_number": "MD54321",
            "npi_number": "9876543210",
            "email": "dr.johnson@clinichub.com",
            "phone": "+1-555-789-0123"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print(f"✅ Create Provider: PASSED - ID: {provider_id}")
    except Exception as e:
        print(f"❌ Create Provider: FAILED - {str(e)}")
        return
    
    # Test 4: Initialize Lab Tests
    try:
        url = f"{API_URL}/lab-tests/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Initialize Lab Tests: PASSED - {result.get('message')}")
    except Exception as e:
        print(f"❌ Initialize Lab Tests: FAILED - {str(e)}")
    
    # Test 5: Get Lab Tests
    lab_test_ids = []
    try:
        url = f"{API_URL}/lab-tests"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Store lab test IDs for later use
        if len(result) > 0:
            lab_test_ids = [test["id"] for test in result[:2]]  # Get first 2 tests
        
        print(f"✅ Get Lab Tests: PASSED - Found {len(result)} tests")
    except Exception as e:
        print(f"❌ Get Lab Tests: FAILED - {str(e)}")
    
    # Test 6: Initialize ICD-10 Codes
    try:
        url = f"{API_URL}/icd10/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Initialize ICD-10 Codes: PASSED - {result.get('message')}")
    except Exception as e:
        print(f"❌ Initialize ICD-10 Codes: FAILED - {str(e)}")
    
    # Test 7: Search ICD-10 Codes
    icd10_codes = []
    try:
        url = f"{API_URL}/icd10/search"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"query": "hypertension"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Store ICD-10 codes for later use
        if len(result) > 0:
            icd10_codes = [code["code"] for code in result[:1]]  # Get first code
        
        print(f"✅ Search ICD-10 Codes: PASSED - Found {len(result)} codes")
    except Exception as e:
        print(f"❌ Search ICD-10 Codes: FAILED - {str(e)}")
    
    # Test 8: Create Lab Order
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
            print(f"✅ Create Lab Order: PASSED - ID: {lab_order_id}")
        except Exception as e:
            print(f"❌ Create Lab Order: FAILED - {str(e)}")
    else:
        print("Skipping Create Lab Order test - missing required IDs")
    
    # Test 9: Get Lab Orders
    try:
        url = f"{API_URL}/lab-orders"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Get Lab Orders: PASSED - Found {len(result)} orders")
    except Exception as e:
        print(f"❌ Get Lab Orders: FAILED - {str(e)}")
    
    # Test 10: Get Specific Lab Order
    if lab_order_id:
        try:
            url = f"{API_URL}/lab-orders/{lab_order_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Get Lab Order by ID: PASSED - Order #{result.get('order_number', 'N/A')}")
        except Exception as e:
            print(f"❌ Get Lab Order by ID: FAILED - {str(e)}")
    
    print("\nLab Integration Testing Complete")

if __name__ == "__main__":
    test_lab_integration_simple()