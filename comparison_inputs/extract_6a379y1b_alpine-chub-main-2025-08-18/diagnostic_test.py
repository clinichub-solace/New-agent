#!/usr/bin/env python3
"""
FOCUSED UPDATE ENDPOINTS DIAGNOSTIC TEST
Identify exact missing endpoints and validation issues
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
API_URL = f"{BACKEND_URL}/api"

# Global variables
auth_token = None

def authenticate():
    """Authenticate with admin/admin123 credentials"""
    global auth_token
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get("access_token")
            return True
        return False
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def get_headers():
    """Get headers with authentication token"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    return {"Content-Type": "application/json"}

def test_endpoint_exists(method, endpoint, data=None):
    """Test if an endpoint exists and what error it returns"""
    try:
        url = f"{API_URL}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, headers=get_headers())
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=get_headers())
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=get_headers())
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=get_headers())
        
        print(f"{method.upper()} {endpoint}: Status {response.status_code}")
        if response.status_code == 404:
            print("   ❌ ENDPOINT NOT FOUND")
        elif response.status_code == 405:
            print("   ❌ METHOD NOT ALLOWED")
        elif response.status_code == 422:
            print("   ⚠️ VALIDATION ERROR")
            try:
                error_detail = response.json()
                print(f"   Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Details: {response.text}")
        elif response.status_code == 500:
            print("   ❌ SERVER ERROR")
            print(f"   Details: {response.text}")
        else:
            print(f"   ✅ ENDPOINT EXISTS (Status: {response.status_code})")
        
        return response.status_code, response.text
    except Exception as e:
        print(f"{method.upper()} {endpoint}: ERROR - {e}")
        return None, str(e)

def main():
    print("=" * 80)
    print("FOCUSED UPDATE ENDPOINTS DIAGNOSTIC TEST")
    print("=" * 80)
    
    if not authenticate():
        print("Authentication failed")
        return
    
    print("\n=== TESTING SPECIFIC ENDPOINTS MENTIONED IN REVIEW ===")
    
    # Create test data first
    print("\n--- Creating Test Data ---")
    
    # Create patient
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": "test@example.com",
        "phone": "+1-555-123-4567",
        "date_of_birth": "1990-01-01",
        "gender": "male"
    }
    status, response = test_endpoint_exists("POST", "/patients", patient_data)
    patient_id = None
    if status == 200:
        try:
            patient_id = json.loads(response)["id"]
            print(f"   Created patient ID: {patient_id}")
        except:
            pass
    
    # Test Patient UPDATE endpoint (line 2653)
    print("\n--- Patient UPDATE Endpoint (mentioned at line 2653) ---")
    if patient_id:
        update_data = {
            "first_name": "Updated",
            "last_name": "Patient",
            "email": "updated@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1990-01-01",
            "gender": "male"
        }
        test_endpoint_exists("PUT", f"/patients/{patient_id}", update_data)
    else:
        print("Cannot test - no patient ID")
    
    # Test SOAP Notes endpoints
    print("\n--- SOAP Notes UPDATE/DELETE ---")
    test_endpoint_exists("PUT", "/soap-notes/test-id", {"subjective": "test"})
    test_endpoint_exists("DELETE", "/soap-notes/test-id")
    
    # Test Inventory endpoints
    print("\n--- Inventory UPDATE/DELETE ---")
    test_endpoint_exists("PUT", "/inventory/test-id", {"name": "test"})
    test_endpoint_exists("DELETE", "/inventory/test-id")
    
    # Test Invoice endpoints
    print("\n--- Invoice UPDATE/Status Updates ---")
    test_endpoint_exists("PUT", "/invoices/test-id", {"patient_id": "test"})
    test_endpoint_exists("PUT", "/invoices/test-id/status", {"status": "sent"})
    
    # Test Financial Transactions endpoints
    print("\n--- Financial Transactions Individual READ/UPDATE ---")
    test_endpoint_exists("GET", "/financial-transactions/test-id")
    test_endpoint_exists("PUT", "/financial-transactions/test-id", {"amount": 100})
    
    # Test Prescriptions creation
    print("\n--- Prescriptions Creation ---")
    prescription_data = {
        "medication_id": "test-med-id",
        "patient_id": patient_id or "test-patient-id",
        "prescriber_id": "admin",
        "prescriber_name": "Dr. Admin",
        "dosage_text": "Take 1 tablet daily",
        "dose_quantity": 1.0,
        "dose_unit": "tablet",
        "frequency": "daily",
        "route": "oral",
        "quantity": 30.0,
        "days_supply": 30,
        "refills": 2,
        "indication": "Test condition",
        "created_by": "admin",
        "status": "active",
        "medication_display": "Test Medication",
        "patient_display": "Test Patient"
    }
    test_endpoint_exists("POST", "/prescriptions", prescription_data)
    
    # Test Referrals endpoints
    print("\n--- Referrals Endpoints ---")
    referral_data = {
        "patient_id": patient_id or "test-patient-id",
        "referring_provider_id": "admin",
        "referring_provider_name": "Dr. Admin",
        "referred_to_provider_name": "Dr. Specialist",
        "referred_to_specialty": "Cardiology",
        "reason_for_referral": "Chest pain evaluation",
        "urgency": "routine",
        "diagnosis_codes": ["R06.02"],
        "notes": "Test referral",
        "created_by": "admin"
    }
    test_endpoint_exists("POST", "/referrals", referral_data)
    test_endpoint_exists("GET", "/referrals")
    test_endpoint_exists("PUT", "/referrals/test-id", referral_data)
    
    # Test Check Printing endpoints
    print("\n--- Check Printing Functionality ---")
    check_data = {
        "payee_type": "vendor",
        "payee_name": "Test Vendor",
        "amount": 500.00,
        "memo": "Test payment",
        "check_date": date.today().isoformat(),
        "created_by": "admin"
    }
    test_endpoint_exists("POST", "/checks", check_data)
    test_endpoint_exists("POST", "/checks/test-id/print")
    test_endpoint_exists("PUT", "/checks/test-id/status", {"status": "issued"})
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()