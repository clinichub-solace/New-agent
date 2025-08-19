#!/usr/bin/env python3
"""
COMPREHENSIVE UPDATE ENDPOINTS TESTING
Focus on ALL missing CRUD operations identified in review
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
print(f"Using API URL: {API_URL}")

# Global variables to store created IDs for testing
auth_token = None
patient_id = None
employee_id = None
inventory_id = None
invoice_id = None
transaction_id = None
prescription_id = None
referral_id = None
soap_note_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_details=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_details:
            print(f"   Error: {error_details}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Authenticate with admin/admin123 credentials"""
    global auth_token
    print("\n=== AUTHENTICATION ===")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get("access_token")
            print_test_result("Authentication", True, {"token_received": bool(auth_token)})
            return True
        else:
            print_test_result("Authentication", False, response.text)
            return False
    except Exception as e:
        print_test_result("Authentication", False, error_details=str(e))
        return False

def get_headers():
    """Get headers with authentication token"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    return {"Content-Type": "application/json"}

def test_patient_update_endpoint():
    """Test Patient UPDATE endpoint - mentioned as existing at line 2653 but showing 405 errors"""
    global patient_id
    print("\n=== PATIENT UPDATE ENDPOINT TESTING ===")
    
    # First create a patient
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "John",
            "last_name": "UpdateTest",
            "email": "john.update@test.com",
            "phone": "+1-555-999-0001",
            "date_of_birth": "1980-01-15",
            "gender": "male",
            "address_line1": "123 Update St",
            "city": "TestCity",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            patient_id = result["id"]
            print_test_result("Create Patient for Update Test", True, {"patient_id": patient_id})
        else:
            print_test_result("Create Patient for Update Test", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Patient for Update Test", False, error_details=str(e))
        return
    
    # Test UPDATE endpoint
    try:
        url = f"{API_URL}/patients/{patient_id}"
        update_data = {
            "first_name": "John",
            "last_name": "UpdatedLastName",
            "email": "john.updated@test.com",
            "phone": "+1-555-999-0002",
            "date_of_birth": "1980-01-15",
            "gender": "male",
            "address_line1": "456 Updated Ave",
            "city": "UpdatedCity",
            "state": "CA",
            "zip_code": "54321"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Patient UPDATE (PUT)", True, result)
        else:
            print_test_result("Patient UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Patient UPDATE (PUT)", False, error_details=str(e))

def test_soap_notes_update_delete():
    """Test SOAP Notes UPDATE/DELETE - mentioned as showing 422 errors on UPDATE, missing endpoints"""
    global soap_note_id
    print("\n=== SOAP NOTES UPDATE/DELETE TESTING ===")
    
    if not patient_id:
        print("Skipping SOAP Notes tests - no patient ID available")
        return
    
    # First create an encounter for the SOAP note
    encounter_id = None
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": patient_id,
            "encounter_type": "consultation",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Test Provider",
            "chief_complaint": "Test complaint",
            "reason_for_visit": "Testing SOAP notes"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            encounter_id = result["id"]
            print_test_result("Create Encounter for SOAP Test", True, {"encounter_id": encounter_id})
        else:
            print_test_result("Create Encounter for SOAP Test", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Encounter for SOAP Test", False, error_details=str(e))
        return
    
    # Create SOAP note
    try:
        url = f"{API_URL}/soap-notes"
        data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "subjective": "Patient reports headache for 2 days",
            "objective": "BP 120/80, HR 72, Temp 98.6F",
            "assessment": "Tension headache",
            "plan": "Rest, hydration, follow up in 1 week",
            "provider": "Dr. Test Provider"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            soap_note_id = result["id"]
            print_test_result("Create SOAP Note", True, {"soap_note_id": soap_note_id})
        else:
            print_test_result("Create SOAP Note", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create SOAP Note", False, error_details=str(e))
        return
    
    # Test UPDATE SOAP note
    try:
        url = f"{API_URL}/soap-notes/{soap_note_id}"
        update_data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "subjective": "Patient reports headache for 2 days, worsening",
            "objective": "BP 125/85, HR 75, Temp 99.1F",
            "assessment": "Tension headache, possible migraine",
            "plan": "Prescribed ibuprofen, rest, hydration, follow up in 3 days",
            "provider": "Dr. Test Provider"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("SOAP Note UPDATE (PUT)", True, result)
        else:
            print_test_result("SOAP Note UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("SOAP Note UPDATE (PUT)", False, error_details=str(e))
    
    # Test DELETE SOAP note
    try:
        url = f"{API_URL}/soap-notes/{soap_note_id}"
        response = requests.delete(url, headers=get_headers())
        if response.status_code == 200 or response.status_code == 204:
            print_test_result("SOAP Note DELETE", True, {"status": "deleted"})
        else:
            print_test_result("SOAP Note DELETE", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("SOAP Note DELETE", False, error_details=str(e))

def test_inventory_update_delete():
    """Test Inventory UPDATE/DELETE - mentioned as having validation issues on UPDATE, DELETE returns 405"""
    global inventory_id
    print("\n=== INVENTORY UPDATE/DELETE TESTING ===")
    
    # Create inventory item
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Test Medication",
            "category": "Medications",
            "sku": "TEST-MED-001",
            "current_stock": 50,
            "min_stock_level": 10,
            "unit_cost": 5.99,
            "supplier": "Test Supplier",
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "location": "Shelf A1",
            "notes": "Test medication for update testing"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            inventory_id = result["id"]
            print_test_result("Create Inventory Item", True, {"inventory_id": inventory_id})
        else:
            print_test_result("Create Inventory Item", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Inventory Item", False, error_details=str(e))
        return
    
    # Test UPDATE inventory item
    try:
        url = f"{API_URL}/inventory/{inventory_id}"
        update_data = {
            "name": "Updated Test Medication",
            "category": "Updated Medications",
            "sku": "TEST-MED-001-UPD",
            "current_stock": 75,
            "min_stock_level": 15,
            "unit_cost": 6.99,
            "supplier": "Updated Test Supplier",
            "expiry_date": (date.today() + timedelta(days=400)).isoformat(),
            "location": "Shelf B2",
            "notes": "Updated test medication"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Inventory UPDATE (PUT)", True, result)
        else:
            print_test_result("Inventory UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Inventory UPDATE (PUT)", False, error_details=str(e))
    
    # Test DELETE inventory item
    try:
        url = f"{API_URL}/inventory/{inventory_id}"
        response = requests.delete(url, headers=get_headers())
        if response.status_code == 200 or response.status_code == 204:
            print_test_result("Inventory DELETE", True, {"status": "deleted"})
        else:
            print_test_result("Inventory DELETE", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Inventory DELETE", False, error_details=str(e))

def test_invoice_update_status():
    """Test Invoice UPDATE/Status Updates - mentioned as missing UPDATE endpoint, status updates failing (404)"""
    global invoice_id
    print("\n=== INVOICE UPDATE/STATUS TESTING ===")
    
    if not patient_id:
        print("Skipping Invoice tests - no patient ID available")
        return
    
    # Create invoice
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Consultation",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total": 100.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Test invoice for update testing"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            invoice_id = result["id"]
            print_test_result("Create Invoice", True, {"invoice_id": invoice_id})
        else:
            print_test_result("Create Invoice", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Invoice", False, error_details=str(e))
        return
    
    # Test UPDATE invoice
    try:
        url = f"{API_URL}/invoices/{invoice_id}"
        update_data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Updated Consultation",
                    "quantity": 1,
                    "unit_price": 120.00,
                    "total": 120.00
                },
                {
                    "description": "Additional Service",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "total": 50.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Updated test invoice"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice UPDATE (PUT)", True, result)
        else:
            print_test_result("Invoice UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Invoice UPDATE (PUT)", False, error_details=str(e))
    
    # Test invoice status update
    try:
        url = f"{API_URL}/invoices/{invoice_id}/status"
        status_data = {"status": "sent"}
        
        response = requests.put(url, json=status_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice Status UPDATE", True, result)
        else:
            print_test_result("Invoice Status UPDATE", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Invoice Status UPDATE", False, error_details=str(e))

def test_financial_transactions_update():
    """Test Financial Transactions UPDATE - mentioned as individual READ/UPDATE failing (404 errors)"""
    global transaction_id
    print("\n=== FINANCIAL TRANSACTIONS UPDATE TESTING ===")
    
    # Create financial transaction
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 250.00,
            "payment_method": "credit_card",
            "description": "Patient payment for consultation",
            "category": "patient_payment",
            "patient_id": patient_id,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            transaction_id = result["id"]
            print_test_result("Create Financial Transaction", True, {"transaction_id": transaction_id})
        else:
            print_test_result("Create Financial Transaction", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Financial Transaction", False, error_details=str(e))
        return
    
    # Test READ individual transaction
    try:
        url = f"{API_URL}/financial-transactions/{transaction_id}"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Financial Transaction READ by ID", True, result)
        else:
            print_test_result("Financial Transaction READ by ID", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Financial Transaction READ by ID", False, error_details=str(e))
    
    # Test UPDATE financial transaction
    try:
        url = f"{API_URL}/financial-transactions/{transaction_id}"
        update_data = {
            "transaction_type": "income",
            "amount": 275.00,
            "payment_method": "credit_card",
            "description": "Updated patient payment for consultation",
            "category": "patient_payment",
            "patient_id": patient_id,
            "created_by": "admin"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Financial Transaction UPDATE (PUT)", True, result)
        else:
            print_test_result("Financial Transaction UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Financial Transaction UPDATE (PUT)", False, error_details=str(e))

def test_prescriptions_creation():
    """Test Prescriptions - mentioned as creation failing with 500 server errors"""
    global prescription_id
    print("\n=== PRESCRIPTIONS CREATION TESTING ===")
    
    if not patient_id:
        print("Skipping Prescription tests - no patient ID available")
        return
    
    # First initialize eRx system
    try:
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Initialize eRx System", True, result)
        else:
            print_test_result("Initialize eRx System", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print_test_result("Initialize eRx System", False, error_details=str(e))
    
    # Get available medications
    medication_id = None
    try:
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0:
                medication_id = result[0]["id"]
                print_test_result("Get eRx Medications", True, {"medication_count": len(result), "first_medication_id": medication_id})
            else:
                print_test_result("Get eRx Medications", False, "No medications found")
                return
        else:
            print_test_result("Get eRx Medications", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Get eRx Medications", False, error_details=str(e))
        return
    
    # Create prescription
    try:
        url = f"{API_URL}/prescriptions"
        data = {
            "medication_id": medication_id,
            "patient_id": patient_id,
            "prescriber_id": "admin",
            "prescriber_name": "Dr. Admin",
            "dosage_text": "Take 1 tablet twice daily with food",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "BID",
            "route": "oral",
            "quantity": 30.0,
            "days_supply": 15,
            "refills": 2,
            "indication": "Bacterial infection",
            "diagnosis_codes": ["Z00.00"],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            prescription_id = result["id"]
            print_test_result("Create Prescription", True, {"prescription_id": prescription_id})
        else:
            print_test_result("Create Prescription", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Create Prescription", False, error_details=str(e))
    
    # Test UPDATE prescription
    if prescription_id:
        try:
            url = f"{API_URL}/prescriptions/{prescription_id}"
            update_data = {
                "medication_id": medication_id,
                "patient_id": patient_id,
                "prescriber_id": "admin",
                "prescriber_name": "Dr. Admin",
                "dosage_text": "Take 1 tablet three times daily with food",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "TID",
                "route": "oral",
                "quantity": 45.0,
                "days_supply": 15,
                "refills": 1,
                "indication": "Bacterial infection - updated",
                "diagnosis_codes": ["Z00.00"],
                "created_by": "admin"
            }
            
            response = requests.put(url, json=update_data, headers=get_headers())
            if response.status_code == 200:
                result = response.json()
                print_test_result("Prescription UPDATE (PUT)", True, result)
            else:
                print_test_result("Prescription UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            print_test_result("Prescription UPDATE (PUT)", False, error_details=str(e))

def test_referrals_endpoints():
    """Test Referrals endpoints - mentioned as all failing with 422/500 errors"""
    global referral_id
    print("\n=== REFERRALS ENDPOINTS TESTING ===")
    
    if not patient_id:
        print("Skipping Referral tests - no patient ID available")
        return
    
    # Create referral
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": patient_id,
            "referring_provider_id": "admin",
            "referring_provider_name": "Dr. Admin",
            "specialist_name": "Dr. Specialist",
            "specialty": "Cardiology",
            "reason": "Chest pain evaluation",
            "urgency": "routine",
            "diagnosis_codes": ["R06.02"],
            "notes": "Patient reports intermittent chest pain",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            referral_id = result["id"]
            print_test_result("Create Referral", True, {"referral_id": referral_id})
        else:
            print_test_result("Create Referral", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Referral", False, error_details=str(e))
        return
    
    # Test GET referrals
    try:
        url = f"{API_URL}/referrals"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Get Referrals", True, {"referral_count": len(result) if isinstance(result, list) else "N/A"})
        else:
            print_test_result("Get Referrals", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Get Referrals", False, error_details=str(e))
    
    # Test UPDATE referral
    try:
        url = f"{API_URL}/referrals/{referral_id}"
        update_data = {
            "patient_id": patient_id,
            "referring_provider_id": "admin",
            "referring_provider_name": "Dr. Admin",
            "specialist_name": "Dr. Updated Specialist",
            "specialty": "Cardiology",
            "reason": "Updated chest pain evaluation",
            "urgency": "urgent",
            "diagnosis_codes": ["R06.02"],
            "notes": "Patient reports worsening chest pain",
            "created_by": "admin"
        }
        
        response = requests.put(url, json=update_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Referral UPDATE (PUT)", True, result)
        else:
            print_test_result("Referral UPDATE (PUT)", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Referral UPDATE (PUT)", False, error_details=str(e))
    
    # Test referral status update
    try:
        url = f"{API_URL}/referrals/{referral_id}/status"
        status_data = {"status": "scheduled"}
        
        response = requests.put(url, json=status_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Referral Status UPDATE", True, result)
        else:
            print_test_result("Referral Status UPDATE", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Referral Status UPDATE", False, error_details=str(e))

def test_check_printing_functionality():
    """Test Check Printing functionality - user specifically requested completion"""
    print("\n=== CHECK PRINTING FUNCTIONALITY TESTING ===")
    
    # Create vendor first
    vendor_id = None
    try:
        url = f"{API_URL}/vendors"
        data = {
            "company_name": "Test Medical Supplies",
            "contact_person": "John Vendor",
            "email": "vendor@test.com",
            "phone": "+1-555-123-4567",
            "address_line1": "123 Vendor St",
            "city": "VendorCity",
            "state": "TX",
            "zip_code": "12345",
            "tax_id": "12-3456789"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            vendor_id = result["id"]
            print_test_result("Create Vendor for Check Test", True, {"vendor_id": vendor_id})
        else:
            print_test_result("Create Vendor for Check Test", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Vendor for Check Test", False, error_details=str(e))
        return
    
    # Create check
    check_id = None
    try:
        url = f"{API_URL}/checks"
        data = {
            "payee_type": "vendor",
            "payee_id": vendor_id,
            "payee_name": "Test Medical Supplies",
            "amount": 500.00,
            "memo": "Medical supplies payment",
            "expense_category": "medical_supplies",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_headers())
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            check_id = result["id"]
            print_test_result("Create Check", True, {"check_id": check_id})
        else:
            print_test_result("Create Check", False, f"Status: {response.status_code}, Response: {response.text}")
            return
    except Exception as e:
        print_test_result("Create Check", False, error_details=str(e))
        return
    
    # Test check printing
    try:
        url = f"{API_URL}/checks/{check_id}/print"
        response = requests.post(url, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Print Check", True, result)
        else:
            print_test_result("Print Check", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Print Check", False, error_details=str(e))
    
    # Test check status update
    try:
        url = f"{API_URL}/checks/{check_id}/status"
        status_data = {"status": "issued"}
        
        response = requests.put(url, json=status_data, headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            print_test_result("Check Status UPDATE", True, result)
        else:
            print_test_result("Check Status UPDATE", False, f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print_test_result("Check Status UPDATE", False, error_details=str(e))

def main():
    """Main test execution"""
    print("=" * 80)
    print("COMPREHENSIVE UPDATE ENDPOINTS TESTING")
    print("Focus on ALL missing CRUD operations identified in review")
    print("=" * 80)
    
    # Authenticate first
    if not authenticate():
        print("Authentication failed. Cannot proceed with tests.")
        return
    
    # Run all UPDATE endpoint tests
    test_patient_update_endpoint()
    test_soap_notes_update_delete()
    test_inventory_update_delete()
    test_invoice_update_status()
    test_financial_transactions_update()
    test_prescriptions_creation()
    test_referrals_endpoints()
    test_check_printing_functionality()
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE UPDATE ENDPOINTS TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()