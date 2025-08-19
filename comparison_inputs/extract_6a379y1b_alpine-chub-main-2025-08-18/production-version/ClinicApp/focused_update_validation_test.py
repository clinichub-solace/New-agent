#!/usr/bin/env python3
"""
Focused test to identify and fix validation issues with specific endpoints
"""

import requests
import json
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

def authenticate():
    """Get admin token"""
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

def test_financial_transaction_creation():
    """Test financial transaction creation with proper validation"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== Testing Financial Transaction Creation ===")
    
    # Test with minimal required fields
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 285.00,
            "payment_method": "credit_card",
            "description": "Patient payment test",
            "created_by": "admin"  # This might be required
        }
        
        response = requests.post(url, json=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Financial Transaction Created: {result['id']}")
            return result['id']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return None

def test_check_creation():
    """Test check creation with proper validation"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Check Creation ===")
    
    # Test with required fields
    try:
        url = f"{API_URL}/checks"
        data = {
            "payee_name": "Medical Supply Company",  # Changed from payee to payee_name
            "amount": 1250.00,
            "memo": "Monthly medical supplies order",
            "created_by": "admin"  # This is required
        }
        
        response = requests.post(url, json=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Check Created: {result['id']}")
            return result['id']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return None

def test_invoice_update_issue():
    """Test invoice update to identify the 500 error"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Invoice Update Issue ===")
    
    # First create a patient and invoice
    try:
        # Create patient
        url = f"{API_URL}/patients"
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test@example.com",
            "phone": "+1-555-000-0000",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "address_line1": "123 Test St",
            "city": "Test City",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(url, json=patient_data, headers=headers)
        if response.status_code != 201:
            print(f"❌ Patient creation failed: {response.text}")
            return
        
        patient_id = response.json()["id"]
        print(f"✅ Patient created: {patient_id}")
        
        # Create invoice
        url = f"{API_URL}/invoices"
        invoice_data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Test Service",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total": 100.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Test invoice"
        }
        
        response = requests.post(url, json=invoice_data, headers=headers)
        if response.status_code != 201:
            print(f"❌ Invoice creation failed: {response.text}")
            return
        
        invoice_id = response.json()["id"]
        print(f"✅ Invoice created: {invoice_id}")
        
        # Now try to update the invoice
        url = f"{API_URL}/invoices/{invoice_id}"
        update_data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Updated Test Service",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "total": 150.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Updated test invoice"
        }
        
        response = requests.put(url, json=update_data, headers=headers)
        print(f"Update Status: {response.status_code}")
        print(f"Update Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Invoice update successful")
        else:
            print(f"❌ Invoice update failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_prescription_validation():
    """Test prescription creation validation"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Prescription Validation ===")
    
    # First get a patient and medication
    try:
        # Get patients
        response = requests.get(f"{API_URL}/patients", headers=headers)
        if response.status_code != 200 or not response.json():
            print("❌ No patients available")
            return
        
        patient_id = response.json()[0]["id"]
        print(f"✅ Using patient: {patient_id}")
        
        # Initialize eRx and get medications
        requests.post(f"{API_URL}/erx/init", headers=headers)
        response = requests.get(f"{API_URL}/erx/medications", headers=headers)
        if response.status_code != 200 or not response.json():
            print("❌ No medications available")
            return
        
        medication_id = response.json()[0]["id"]
        print(f"✅ Using medication: {medication_id}")
        
        # Try prescription creation with all required fields
        url = f"{API_URL}/prescriptions"
        data = {
            "medication_id": medication_id,
            "patient_id": patient_id,
            "prescriber_id": "admin",
            "prescriber_name": "Dr. Admin",
            "dosage_text": "Take 1 tablet daily",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "DAILY",
            "route": "oral",
            "quantity": 30.0,
            "days_supply": 30,
            "refills": 2,
            "indication": "Test condition",
            "diagnosis_codes": ["Z00.00"],
            "created_by": "admin",
            # Add the missing required fields
            "status": "active",
            "medication_display": "Test Medication",
            "patient_display": "Test Patient"
        }
        
        response = requests.post(url, json=data, headers=headers)
        print(f"Prescription Status: {response.status_code}")
        print(f"Prescription Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Prescription creation successful")
        else:
            print(f"❌ Prescription creation failed")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_referral_validation():
    """Test referral creation validation"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Referral Validation ===")
    
    try:
        # Get a patient
        response = requests.get(f"{API_URL}/patients", headers=headers)
        if response.status_code != 200 or not response.json():
            print("❌ No patients available")
            return
        
        patient_id = response.json()[0]["id"]
        print(f"✅ Using patient: {patient_id}")
        
        # Try referral creation with corrected field names
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": patient_id,
            "referring_provider_id": "admin",  # Required field
            "referred_to_provider_name": "Dr. Specialist",  # Required field
            "referred_to_specialty": "Cardiology",  # Required field
            "reason_for_referral": "Chest pain evaluation",  # Required field
            "urgency": "routine",
            "preferred_date": (date.today() + timedelta(days=14)).isoformat(),
            "notes": "Patient reports chest pain",
            "diagnosis_codes": ["R06.02"],
            "insurance_authorization_required": True
        }
        
        response = requests.post(url, json=data, headers=headers)
        print(f"Referral Status: {response.status_code}")
        print(f"Referral Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Referral creation successful")
        else:
            print(f"❌ Referral creation failed")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🔍 FOCUSED VALIDATION TESTING")
    print("=" * 50)
    
    test_financial_transaction_creation()
    test_check_creation()
    test_invoice_update_issue()
    test_prescription_validation()
    test_referral_validation()
    
    print("\n" + "=" * 50)
    print("🔍 FOCUSED VALIDATION TESTING COMPLETED")