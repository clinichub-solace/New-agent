#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Newly Implemented UPDATE Endpoints
Testing all the fixed/implemented UPDATE and CRUD operations as requested in the review.
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

# Global variables for test data
admin_token = None
test_patient_id = None
test_invoice_id = None
test_soap_note_id = None
test_financial_transaction_id = None
test_check_id = None
test_inventory_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, status_code=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            if isinstance(response, dict):
                print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
            else:
                print(f"   Response: {str(response)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if status_code:
            print(f"   Status Code: {status_code}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate_admin():
    """Authenticate with admin credentials and get token"""
    global admin_token
    
    print("\n=== AUTHENTICATION SETUP ===")
    
    # Initialize admin user first
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Admin initialization (may already exist): {str(e)}")
    
    # Login with admin credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, {"token_received": True, "user": result.get("user", {})})
        return True
    except Exception as e:
        print_test_result("Admin Login", False, str(e), getattr(response, 'status_code', None))
        return False

def create_test_data():
    """Create test data needed for UPDATE endpoint testing"""
    global test_patient_id, test_invoice_id, test_soap_note_id, test_financial_transaction_id, test_check_id, test_inventory_id
    
    print("\n=== CREATING TEST DATA ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Create test patient
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emma",
            "last_name": "Thompson",
            "email": "emma.thompson@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-20",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_patient_id = result["id"]
        print_test_result("Create Test Patient", True, {"patient_id": test_patient_id, "name": f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"})
    except Exception as e:
        print_test_result("Create Test Patient", False, str(e), getattr(response, 'status_code', None))
        return False
    
    # 2. Create test encounter for SOAP notes
    encounter_id = None
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": test_patient_id,
            "encounter_type": "consultation",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Sarah Wilson",
            "location": "Main Clinic - Room 201",
            "chief_complaint": "Routine check-up",
            "reason_for_visit": "Annual physical examination"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        encounter_id = result["id"]
        print_test_result("Create Test Encounter", True, {"encounter_id": encounter_id, "encounter_number": result.get("encounter_number")})
    except Exception as e:
        print_test_result("Create Test Encounter", False, str(e), getattr(response, 'status_code', None))
    
    # 3. Create test SOAP note
    if encounter_id:
        try:
            url = f"{API_URL}/soap-notes"
            data = {
                "encounter_id": encounter_id,
                "patient_id": test_patient_id,
                "subjective": "Patient reports feeling well overall. No acute complaints. Requests routine physical examination.",
                "objective": "Vital signs stable. BP 118/76, HR 68, Temp 98.4°F. General appearance healthy and alert.",
                "assessment": "Healthy adult female presenting for routine annual physical examination.",
                "plan": "Continue current health maintenance. Recommend annual mammogram and colonoscopy screening. Follow up in 1 year.",
                "provider": "Dr. Sarah Wilson"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            test_soap_note_id = result["id"]
            print_test_result("Create Test SOAP Note", True, {"soap_note_id": test_soap_note_id})
        except Exception as e:
            print_test_result("Create Test SOAP Note", False, str(e), getattr(response, 'status_code', None))
    
    # 4. Create test invoice
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": test_patient_id,
            "items": [
                {
                    "description": "Annual Physical Examination",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "total": 200.00
                },
                {
                    "description": "Basic Metabolic Panel",
                    "quantity": 1,
                    "unit_price": 85.00,
                    "total": 85.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Payment due within 30 days."
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_invoice_id = result["id"]
        print_test_result("Create Test Invoice", True, {"invoice_id": test_invoice_id, "invoice_number": result.get("invoice_number"), "total": result.get("total_amount")})
    except Exception as e:
        print_test_result("Create Test Invoice", False, str(e), getattr(response, 'status_code', None))
    
    # 5. Create test financial transaction
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 285.00,
            "description": "Patient payment for annual physical",
            "payment_method": "credit_card",
            "reference_number": "PAY-TEST-001",
            "patient_id": test_patient_id,
            "invoice_id": test_invoice_id
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_financial_transaction_id = result["id"]
        print_test_result("Create Test Financial Transaction", True, {"transaction_id": test_financial_transaction_id, "transaction_number": result.get("transaction_number")})
    except Exception as e:
        print_test_result("Create Test Financial Transaction", False, str(e), getattr(response, 'status_code', None))
    
    # 6. Create test inventory item
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Ibuprofen 200mg",
            "category": "Pain Relief",
            "sku": "MED-IBU-200",
            "current_stock": 150,
            "min_stock_level": 25,
            "unit_cost": 0.75,
            "supplier": "PharmaCorp Supplies",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Pharmacy Cabinet A",
            "notes": "Over-the-counter pain reliever"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_inventory_id = result["id"]
        print_test_result("Create Test Inventory Item", True, {"inventory_id": test_inventory_id, "name": result.get("name"), "stock": result.get("current_stock")})
    except Exception as e:
        print_test_result("Create Test Inventory Item", False, str(e), getattr(response, 'status_code', None))
    
    # 7. Create test check
    try:
        url = f"{API_URL}/checks"
        data = {
            "payee": "Medical Supply Company",
            "amount": 1250.00,
            "memo": "Monthly medical supplies order",
            "account": "Operating Account",
            "category": "Medical Supplies"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_check_id = result["id"]
        print_test_result("Create Test Check", True, {"check_id": test_check_id, "check_number": result.get("check_number"), "payee": result.get("payee")})
    except Exception as e:
        print_test_result("Create Test Check", False, str(e), getattr(response, 'status_code', None))
    
    return True

def test_patient_update_endpoint():
    """Test Patient UPDATE endpoint - PUT /api/patients/{id} - Test FHIR structure fix"""
    print("\n=== TESTING PATIENT UPDATE ENDPOINT ===")
    
    if not test_patient_id:
        print("❌ No test patient available for UPDATE testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        url = f"{API_URL}/patients/{test_patient_id}"
        # Update patient data with FHIR-compliant structure
        data = {
            "first_name": "Emma",
            "last_name": "Thompson-Wilson",  # Changed last name
            "email": "emma.wilson@example.com",  # Changed email
            "phone": "+1-555-234-9999",  # Changed phone
            "date_of_birth": "1990-08-20",
            "gender": "female",
            "address_line1": "789 Updated Healthcare Ave",  # Changed address
            "city": "Austin",
            "state": "TX",
            "zip_code": "78702"  # Changed zip
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            # Verify FHIR structure is maintained
            assert result["resource_type"] == "Patient"
            assert isinstance(result["name"], list)
            assert result["name"][0]["family"] == "Thompson-Wilson"
            assert "Emma" in result["name"][0]["given"]
            
            print_test_result("Patient UPDATE Endpoint", True, {
                "patient_id": result["id"],
                "updated_name": f"{result['name'][0]['given'][0]} {result['name'][0]['family']}",
                "updated_email": result["telecom"][0]["value"] if result.get("telecom") else "N/A",
                "fhir_compliant": True
            })
        else:
            print_test_result("Patient UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Patient UPDATE Endpoint", False, str(e))

def test_soap_notes_delete_endpoint():
    """Test SOAP Notes DELETE endpoint - DELETE /api/soap-notes/{id} - Test new implementation"""
    print("\n=== TESTING SOAP NOTES DELETE ENDPOINT ===")
    
    if not test_soap_note_id:
        print("❌ No test SOAP note available for DELETE testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First verify the SOAP note exists
    try:
        url = f"{API_URL}/soap-notes/{test_soap_note_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("❌ Test SOAP note not found for DELETE testing")
            return
        print_test_result("Verify SOAP Note Exists Before Delete", True, {"soap_note_id": test_soap_note_id})
    except Exception as e:
        print_test_result("Verify SOAP Note Exists Before Delete", False, str(e))
        return
    
    # Now test DELETE endpoint
    try:
        url = f"{API_URL}/soap-notes/{test_soap_note_id}"
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("SOAP Notes DELETE Endpoint", True, result)
            
            # Verify the SOAP note is actually deleted
            verify_response = requests.get(url, headers=headers)
            if verify_response.status_code == 404:
                print_test_result("Verify SOAP Note Deleted", True, {"status": "SOAP note successfully deleted"})
            else:
                print_test_result("Verify SOAP Note Deleted", False, "SOAP note still exists after delete")
        else:
            print_test_result("SOAP Notes DELETE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("SOAP Notes DELETE Endpoint", False, str(e))

def test_invoice_update_endpoints():
    """Test Invoice UPDATE endpoints - PUT /api/invoices/{id} and PUT /api/invoices/{id}/status"""
    print("\n=== TESTING INVOICE UPDATE ENDPOINTS ===")
    
    if not test_invoice_id:
        print("❌ No test invoice available for UPDATE testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Invoice UPDATE endpoint - PUT /api/invoices/{id}
    try:
        url = f"{API_URL}/invoices/{test_invoice_id}"
        data = {
            "patient_id": test_patient_id,
            "items": [
                {
                    "description": "Annual Physical Examination - Updated",
                    "quantity": 1,
                    "unit_price": 220.00,  # Increased price
                    "total": 220.00
                },
                {
                    "description": "Comprehensive Metabolic Panel",  # Updated description
                    "quantity": 1,
                    "unit_price": 95.00,  # Increased price
                    "total": 95.00
                },
                {
                    "description": "Lipid Panel",  # New item
                    "quantity": 1,
                    "unit_price": 65.00,
                    "total": 65.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Updated invoice with additional tests. Payment due within 30 days."
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice UPDATE Endpoint", True, {
                "invoice_id": result["id"],
                "invoice_number": result.get("invoice_number"),
                "updated_total": result.get("total_amount"),
                "items_count": len(result.get("items", [])),
                "status": result.get("status")
            })
        else:
            print_test_result("Invoice UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Invoice UPDATE Endpoint", False, str(e))
    
    # Test 2: Invoice Status UPDATE endpoint - PUT /api/invoices/{id}/status
    try:
        url = f"{API_URL}/invoices/{test_invoice_id}/status"
        data = {"status": "paid"}
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice Status UPDATE Endpoint", True, {
                "invoice_id": result["id"],
                "updated_status": result.get("status"),
                "payment_date": result.get("payment_date")
            })
        else:
            print_test_result("Invoice Status UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Invoice Status UPDATE Endpoint", False, str(e))

def test_financial_transactions_individual_endpoints():
    """Test Financial Transactions Individual endpoints - GET/PUT /api/financial-transactions/{id}"""
    print("\n=== TESTING FINANCIAL TRANSACTIONS INDIVIDUAL ENDPOINTS ===")
    
    if not test_financial_transaction_id:
        print("❌ No test financial transaction available for testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Individual GET endpoint - GET /api/financial-transactions/{id}
    try:
        url = f"{API_URL}/financial-transactions/{test_financial_transaction_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Financial Transaction Individual GET Endpoint", True, {
                "transaction_id": result["id"],
                "transaction_number": result.get("transaction_number"),
                "amount": result.get("amount"),
                "type": result.get("transaction_type"),
                "status": result.get("status")
            })
        else:
            print_test_result("Financial Transaction Individual GET Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Financial Transaction Individual GET Endpoint", False, str(e))
    
    # Test 2: Individual PUT endpoint - PUT /api/financial-transactions/{id}
    try:
        url = f"{API_URL}/financial-transactions/{test_financial_transaction_id}"
        data = {
            "transaction_type": "income",
            "amount": 315.00,  # Updated amount
            "description": "Patient payment for annual physical - Updated with additional tests",  # Updated description
            "payment_method": "check",  # Changed payment method
            "reference_number": "PAY-TEST-001-UPDATED",  # Updated reference
            "patient_id": test_patient_id,
            "invoice_id": test_invoice_id
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Financial Transaction Individual PUT Endpoint", True, {
                "transaction_id": result["id"],
                "updated_amount": result.get("amount"),
                "updated_payment_method": result.get("payment_method"),
                "updated_description": result.get("description")[:50] + "..." if result.get("description") else "N/A"
            })
        else:
            print_test_result("Financial Transaction Individual PUT Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Financial Transaction Individual PUT Endpoint", False, str(e))

def test_check_print_endpoint():
    """Test Check PRINT endpoint - POST /api/checks/{id}/print"""
    print("\n=== TESTING CHECK PRINT ENDPOINT ===")
    
    if not test_check_id:
        print("❌ No test check available for PRINT testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        url = f"{API_URL}/checks/{test_check_id}/print"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Check PRINT Endpoint", True, {
                "check_id": result["id"],
                "check_number": result.get("check_number"),
                "status": result.get("status"),
                "print_date": result.get("print_date"),
                "payee": result.get("payee"),
                "amount": result.get("amount")
            })
        else:
            print_test_result("Check PRINT Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Check PRINT Endpoint", False, str(e))

def test_check_status_update_endpoint():
    """Test Check Status UPDATE - PUT /api/checks/{id}/status - Test request body fix"""
    print("\n=== TESTING CHECK STATUS UPDATE ENDPOINT ===")
    
    if not test_check_id:
        print("❌ No test check available for status UPDATE testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        url = f"{API_URL}/checks/{test_check_id}/status"
        data = {"status": "cleared"}  # Using request body instead of query parameters
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Check Status UPDATE Endpoint", True, {
                "check_id": result["id"],
                "updated_status": result.get("status"),
                "check_number": result.get("check_number"),
                "clear_date": result.get("clear_date")
            })
        else:
            print_test_result("Check Status UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Check Status UPDATE Endpoint", False, str(e))

def test_soap_notes_update_endpoint():
    """Test SOAP Notes UPDATE - PUT /api/soap-notes/{id} - Verify still working"""
    print("\n=== TESTING SOAP NOTES UPDATE ENDPOINT ===")
    
    # Create a new SOAP note for UPDATE testing since we deleted the previous one
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First create a new encounter and SOAP note
    encounter_id = None
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": test_patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Michael Chen",
            "location": "Main Clinic - Room 105",
            "chief_complaint": "Follow-up visit",
            "reason_for_visit": "Review test results"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        encounter_id = result["id"]
        print_test_result("Create New Encounter for SOAP UPDATE Test", True, {"encounter_id": encounter_id})
    except Exception as e:
        print_test_result("Create New Encounter for SOAP UPDATE Test", False, str(e))
        return
    
    # Create new SOAP note
    soap_note_id = None
    try:
        url = f"{API_URL}/soap-notes"
        data = {
            "encounter_id": encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient returns for follow-up. Reports improvement in symptoms.",
            "objective": "Vital signs stable. Patient appears comfortable and alert.",
            "assessment": "Condition improving as expected.",
            "plan": "Continue current treatment plan. Follow up in 2 weeks.",
            "provider": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        soap_note_id = result["id"]
        print_test_result("Create New SOAP Note for UPDATE Test", True, {"soap_note_id": soap_note_id})
    except Exception as e:
        print_test_result("Create New SOAP Note for UPDATE Test", False, str(e))
        return
    
    # Now test UPDATE endpoint
    try:
        url = f"{API_URL}/soap-notes/{soap_note_id}"
        data = {
            "encounter_id": encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient returns for follow-up. Reports significant improvement in symptoms. No new complaints.",
            "objective": "Vital signs stable. BP 115/75, HR 70, Temp 98.2°F. Patient appears comfortable, alert, and in good spirits.",
            "assessment": "Condition improving better than expected. Treatment plan is effective.",
            "plan": "Continue current treatment plan with slight modification. Reduce medication frequency. Follow up in 3 weeks instead of 2.",
            "provider": "Dr. Michael Chen"
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("SOAP Notes UPDATE Endpoint", True, {
                "soap_note_id": result["id"],
                "updated_assessment": result.get("assessment")[:50] + "..." if result.get("assessment") else "N/A",
                "updated_plan": result.get("plan")[:50] + "..." if result.get("plan") else "N/A",
                "provider": result.get("provider")
            })
        else:
            print_test_result("SOAP Notes UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("SOAP Notes UPDATE Endpoint", False, str(e))

def test_inventory_update_delete_endpoints():
    """Test Inventory UPDATE/DELETE - PUT/DELETE /api/inventory/{id} - Verify still working"""
    print("\n=== TESTING INVENTORY UPDATE/DELETE ENDPOINTS ===")
    
    if not test_inventory_id:
        print("❌ No test inventory item available for UPDATE/DELETE testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Inventory UPDATE endpoint - PUT /api/inventory/{id}
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}"
        data = {
            "name": "Ibuprofen 200mg - Updated",
            "category": "Pain Relief",
            "sku": "MED-IBU-200-UPD",  # Updated SKU
            "current_stock": 175,  # Updated stock
            "min_stock_level": 30,  # Updated minimum
            "unit_cost": 0.85,  # Updated cost
            "supplier": "PharmaCorp Supplies - Premium",  # Updated supplier
            "expiry_date": (date.today() + timedelta(days=800)).isoformat(),  # Updated expiry
            "location": "Pharmacy Cabinet A - Shelf 2",  # Updated location
            "notes": "Over-the-counter pain reliever - Updated formulation"  # Updated notes
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Inventory UPDATE Endpoint", True, {
                "inventory_id": result["id"],
                "updated_name": result.get("name"),
                "updated_stock": result.get("current_stock"),
                "updated_cost": result.get("unit_cost"),
                "updated_sku": result.get("sku")
            })
        else:
            print_test_result("Inventory UPDATE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Inventory UPDATE Endpoint", False, str(e))
    
    # Test 2: Inventory DELETE endpoint - DELETE /api/inventory/{id}
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}"
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Inventory DELETE Endpoint", True, result)
            
            # Verify the inventory item is actually deleted
            verify_response = requests.get(url, headers=headers)
            if verify_response.status_code == 404:
                print_test_result("Verify Inventory Item Deleted", True, {"status": "Inventory item successfully deleted"})
            else:
                print_test_result("Verify Inventory Item Deleted", False, "Inventory item still exists after delete")
        else:
            print_test_result("Inventory DELETE Endpoint", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Inventory DELETE Endpoint", False, str(e))

def test_prescriptions_creation():
    """Test Prescriptions creation - POST /api/prescriptions - Test if 500 errors resolved"""
    print("\n=== TESTING PRESCRIPTIONS CREATION ===")
    
    if not test_patient_id:
        print("❌ No test patient available for prescription testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First initialize eRx system and get a medication
    medication_id = None
    try:
        # Initialize eRx system
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        print_test_result("Initialize eRx System", True, response.json())
        
        # Get medications
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if medications:
            medication_id = medications[0]["id"]
            print_test_result("Get eRx Medications", True, {"medication_count": len(medications), "first_medication": medications[0].get("generic_name")})
        else:
            print_test_result("Get eRx Medications", False, "No medications available")
            return
            
    except Exception as e:
        print_test_result("eRx System Setup", False, str(e))
        return
    
    # Test prescription creation
    try:
        url = f"{API_URL}/prescriptions"
        data = {
            "medication_id": medication_id,
            "patient_id": test_patient_id,
            "prescriber_id": "prescriber-admin",
            "prescriber_name": "Dr. Admin User",
            
            # Dosage Information
            "dosage_text": "Take 1 tablet by mouth twice daily with food",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "BID",
            "route": "oral",
            
            # Prescription Details
            "quantity": 60.0,
            "days_supply": 30,
            "refills": 3,
            
            # Clinical Context
            "indication": "Hypertension management",
            "diagnosis_codes": ["I10"],
            "special_instructions": "Take with food to reduce stomach upset",
            
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print_test_result("Prescription Creation", True, {
                "prescription_id": result["id"],
                "prescription_number": result.get("prescription_number"),
                "medication_display": result.get("medication_display"),
                "patient_display": result.get("patient_display"),
                "status": result.get("status"),
                "allergies_checked": result.get("allergies_checked"),
                "interactions_checked": result.get("interactions_checked")
            })
        else:
            print_test_result("Prescription Creation", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Prescription Creation", False, str(e))

def test_referrals_endpoints():
    """Test Referrals endpoints - POST/GET /api/referrals - Test if 422/500 errors resolved"""
    print("\n=== TESTING REFERRALS ENDPOINTS ===")
    
    if not test_patient_id:
        print("❌ No test patient available for referrals testing")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create referral - POST /api/referrals
    referral_id = None
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": test_patient_id,
            "referring_provider": "Dr. Sarah Wilson",
            "specialist_name": "Dr. Robert Cardiology",
            "specialty": "Cardiology",
            "reason": "Evaluate chest pain and shortness of breath",
            "urgency": "routine",
            "preferred_date": (date.today() + timedelta(days=14)).isoformat(),
            "notes": "Patient reports intermittent chest pain with exertion. EKG normal. Recommend stress test.",
            "diagnosis_codes": ["R06.02", "R50.9"],
            "insurance_authorization_required": True
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            referral_id = result["id"]
            print_test_result("Create Referral", True, {
                "referral_id": result["id"],
                "referral_number": result.get("referral_number"),
                "specialist": result.get("specialist_name"),
                "specialty": result.get("specialty"),
                "status": result.get("status")
            })
        else:
            print_test_result("Create Referral", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Create Referral", False, str(e))
    
    # Test 2: Get all referrals - GET /api/referrals
    try:
        url = f"{API_URL}/referrals"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Get All Referrals", True, {
                "referrals_count": len(result),
                "first_referral": result[0] if result else "No referrals found"
            })
        else:
            print_test_result("Get All Referrals", False, response.text, response.status_code)
            
    except Exception as e:
        print_test_result("Get All Referrals", False, str(e))
    
    # Test 3: Get referral by ID - GET /api/referrals/{id}
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print_test_result("Get Referral by ID", True, {
                    "referral_id": result["id"],
                    "patient_id": result.get("patient_id"),
                    "specialist": result.get("specialist_name"),
                    "status": result.get("status")
                })
            else:
                print_test_result("Get Referral by ID", False, response.text, response.status_code)
                
        except Exception as e:
            print_test_result("Get Referral by ID", False, str(e))

def test_error_handling():
    """Test error handling for non-existent IDs (404 errors)"""
    print("\n=== TESTING ERROR HANDLING FOR NON-EXISTENT IDs ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    fake_id = "non-existent-id-12345"
    
    # Test 404 errors for various endpoints
    endpoints_to_test = [
        ("GET", f"/patients/{fake_id}", "Get Non-existent Patient"),
        ("PUT", f"/patients/{fake_id}", "Update Non-existent Patient"),
        ("GET", f"/invoices/{fake_id}", "Get Non-existent Invoice"),
        ("PUT", f"/invoices/{fake_id}", "Update Non-existent Invoice"),
        ("PUT", f"/invoices/{fake_id}/status", "Update Non-existent Invoice Status"),
        ("GET", f"/financial-transactions/{fake_id}", "Get Non-existent Financial Transaction"),
        ("PUT", f"/financial-transactions/{fake_id}", "Update Non-existent Financial Transaction"),
        ("DELETE", f"/soap-notes/{fake_id}", "Delete Non-existent SOAP Note"),
        ("PUT", f"/soap-notes/{fake_id}", "Update Non-existent SOAP Note"),
        ("POST", f"/checks/{fake_id}/print", "Print Non-existent Check"),
        ("PUT", f"/checks/{fake_id}/status", "Update Non-existent Check Status"),
        ("GET", f"/inventory/{fake_id}", "Get Non-existent Inventory Item"),
        ("PUT", f"/inventory/{fake_id}", "Update Non-existent Inventory Item"),
        ("DELETE", f"/inventory/{fake_id}", "Delete Non-existent Inventory Item")
    ]
    
    for method, endpoint, test_name in endpoints_to_test:
        try:
            url = f"{API_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json={"test": "data"}, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            
            if response.status_code == 404:
                print_test_result(f"{test_name} (Expected 404)", True, {"status_code": 404, "message": "Not found as expected"})
            else:
                print_test_result(f"{test_name} (Expected 404)", False, f"Expected 404, got {response.status_code}", response.status_code)
                
        except Exception as e:
            print_test_result(f"{test_name} (Expected 404)", False, str(e))

def main():
    """Main test execution function"""
    print("🏥 COMPREHENSIVE UPDATE ENDPOINTS TESTING")
    print("=" * 80)
    print("Testing all newly implemented UPDATE and CRUD operations")
    print("Authentication: admin/admin123")
    print("=" * 80)
    
    # Step 1: Authenticate
    if not authenticate_admin():
        print("❌ Authentication failed. Cannot proceed with testing.")
        return
    
    # Step 2: Create test data
    if not create_test_data():
        print("❌ Test data creation failed. Some tests may not run.")
    
    # Step 3: Test PRIMARY FOCUS endpoints (newly implemented/fixed)
    print("\n" + "=" * 80)
    print("PRIMARY TESTING FOCUS - Newly Implemented/Fixed Endpoints")
    print("=" * 80)
    
    test_patient_update_endpoint()  # 1. Patient UPDATE endpoint
    test_soap_notes_delete_endpoint()  # 2. SOAP Notes DELETE endpoint
    test_invoice_update_endpoints()  # 3. Invoice UPDATE and Status UPDATE endpoints
    test_financial_transactions_individual_endpoints()  # 4. Financial Transactions Individual endpoints
    test_check_print_endpoint()  # 5. Check PRINT endpoint
    test_check_status_update_endpoint()  # 6. Check Status UPDATE endpoint
    
    # Step 4: Test SECONDARY FOCUS endpoints (verify still working)
    print("\n" + "=" * 80)
    print("SECONDARY TESTING FOCUS - Verify Other CRUD Operations")
    print("=" * 80)
    
    test_soap_notes_update_endpoint()  # 7. SOAP Notes UPDATE endpoint
    test_inventory_update_delete_endpoints()  # 8. Inventory UPDATE/DELETE endpoints
    test_prescriptions_creation()  # 9. Prescriptions creation
    test_referrals_endpoints()  # 10. Referrals endpoints
    
    # Step 5: Test error handling
    test_error_handling()
    
    print("\n" + "=" * 80)
    print("🏥 COMPREHENSIVE UPDATE ENDPOINTS TESTING COMPLETED")
    print("=" * 80)
    print("All requested endpoints have been tested.")
    print("Review the results above for detailed status of each endpoint.")
    print("✅ = Working correctly")
    print("❌ = Issues found")

if __name__ == "__main__":
    main()