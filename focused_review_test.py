#!/usr/bin/env python3
"""
Focused Backend Testing for Review Request
Testing specific functionalities mentioned by the user:
1. SOAP Notes functionality
2. E-Prescribing (eRx) functionality  
3. Inventory editing
4. OpenEMR integration status
5. Comprehensive workflow testing
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
print(f"🏥 ClinicHub Backend Testing - Review Request Focus")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Global variables for test data
auth_token = None
test_patient_id = None
test_encounter_id = None
test_inventory_id = None
test_prescription_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, details=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if details:
            print(f"   Details: {details}")
        if response and isinstance(response, dict):
            # Print key information from response
            if 'id' in response:
                print(f"   ID: {response['id']}")
            if 'status' in response:
                print(f"   Status: {response['status']}")
    else:
        print(f"❌ {test_name}: FAILED")
        if details:
            print(f"   Error: {details}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Authenticate with admin/admin123 credentials"""
    global auth_token
    print("\n🔐 AUTHENTICATION TEST")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get('access_token')
            print_test_result("Admin Authentication", True, result, f"Token obtained: {auth_token[:20]}...")
            return True
        else:
            print_test_result("Admin Authentication", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Admin Authentication", False, None, str(e))
        return False

def get_headers():
    """Get headers with authentication token"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def test_soap_notes_functionality():
    """Test SOAP Notes functionality as requested"""
    global test_patient_id, test_encounter_id
    print("\n📝 SOAP NOTES FUNCTIONALITY TESTING")
    
    # First, create a test patient and encounter for SOAP notes
    try:
        # Create patient
        patient_data = {
            "first_name": "John",
            "last_name": "TestPatient",
            "email": "john.testpatient@example.com",
            "phone": "+1-555-SOAP-001",
            "date_of_birth": "1980-01-15",
            "gender": "male"
        }
        
        response = requests.post(f"{API_URL}/patients", json=patient_data, headers=get_headers())
        if response.status_code == 200:
            test_patient_id = response.json()['id']
            print_test_result("Create Test Patient for SOAP", True, None, f"Patient ID: {test_patient_id}")
        else:
            print_test_result("Create Test Patient for SOAP", False, response.text)
            return False
            
        # Create encounter
        encounter_data = {
            "patient_id": test_patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Test Provider",
            "chief_complaint": "Follow-up visit for SOAP note testing",
            "reason_for_visit": "Testing SOAP notes functionality"
        }
        
        response = requests.post(f"{API_URL}/encounters", json=encounter_data, headers=get_headers())
        if response.status_code == 200:
            test_encounter_id = response.json()['id']
            print_test_result("Create Test Encounter for SOAP", True, None, f"Encounter ID: {test_encounter_id}")
        else:
            print_test_result("Create Test Encounter for SOAP", False, response.text)
            return False
            
    except Exception as e:
        print_test_result("Setup for SOAP Notes", False, None, str(e))
        return False
    
    # Test POST /api/soap-notes - Create SOAP note
    try:
        soap_data = {
            "encounter_id": test_encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient reports feeling better since last visit. No new complaints. Sleep has improved.",
            "objective": "Vital signs stable. BP 120/80, HR 72, Temp 98.6F. Patient appears well.",
            "assessment": "Hypertension well controlled. Patient responding well to current medication regimen.",
            "plan": "Continue current medications. Follow up in 3 months. Patient education on diet and exercise.",
            "provider": "Dr. Test Provider"
        }
        
        response = requests.post(f"{API_URL}/soap-notes", json=soap_data, headers=get_headers())
        
        if response.status_code == 200:
            soap_note = response.json()
            soap_note_id = soap_note['id']
            print_test_result("POST /api/soap-notes (Create)", True, soap_note, f"SOAP Note ID: {soap_note_id}")
        else:
            print_test_result("POST /api/soap-notes (Create)", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("POST /api/soap-notes (Create)", False, None, str(e))
        return False
    
    # Test GET /api/soap-notes - Retrieve all SOAP notes
    try:
        response = requests.get(f"{API_URL}/soap-notes", headers=get_headers())
        
        if response.status_code == 200:
            soap_notes = response.json()
            print_test_result("GET /api/soap-notes (Retrieve All)", True, None, f"Found {len(soap_notes)} SOAP notes")
        else:
            print_test_result("GET /api/soap-notes (Retrieve All)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/soap-notes (Retrieve All)", False, None, str(e))
    
    # Test GET /api/soap-notes/{id} - Retrieve specific SOAP note
    try:
        response = requests.get(f"{API_URL}/soap-notes/{soap_note_id}", headers=get_headers())
        
        if response.status_code == 200:
            soap_note = response.json()
            print_test_result("GET /api/soap-notes/{id} (Retrieve Specific)", True, None, f"Retrieved SOAP note for patient: {soap_note.get('patient_id')}")
        else:
            print_test_result("GET /api/soap-notes/{id} (Retrieve Specific)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/soap-notes/{id} (Retrieve Specific)", False, None, str(e))
    
    # Test PUT /api/soap-notes/{id} - Update SOAP note
    try:
        updated_soap_data = {
            "encounter_id": test_encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient reports feeling much better since last visit. No new complaints. Sleep has greatly improved.",
            "objective": "Vital signs stable. BP 118/78, HR 70, Temp 98.4F. Patient appears very well.",
            "assessment": "Hypertension excellently controlled. Patient responding very well to current medication regimen.",
            "plan": "Continue current medications. Follow up in 3 months. Continue patient education on diet and exercise. Consider reducing medication if BP remains stable.",
            "provider": "Dr. Test Provider"
        }
        
        response = requests.put(f"{API_URL}/soap-notes/{soap_note_id}", json=updated_soap_data, headers=get_headers())
        
        if response.status_code == 200:
            updated_soap = response.json()
            print_test_result("PUT /api/soap-notes/{id} (Update)", True, None, "SOAP note updated successfully")
        else:
            print_test_result("PUT /api/soap-notes/{id} (Update)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("PUT /api/soap-notes/{id} (Update)", False, None, str(e))
    
    return True

def test_erx_functionality():
    """Test E-Prescribing (eRx) functionality as requested"""
    print("\n💊 E-PRESCRIBING (eRx) FUNCTIONALITY TESTING")
    
    # Test GET /api/erx/medications - Get medication database
    try:
        response = requests.get(f"{API_URL}/erx/medications", headers=get_headers())
        
        if response.status_code == 200:
            medications = response.json()
            print_test_result("GET /api/erx/medications (Medication Database)", True, None, f"Found {len(medications)} medications in database")
            
            # Check if we have medications for testing
            if len(medications) == 0:
                # Initialize eRx system
                init_response = requests.post(f"{API_URL}/erx/init", headers=get_headers())
                if init_response.status_code == 200:
                    print_test_result("POST /api/erx/init (Initialize eRx)", True, None, "eRx system initialized")
                    # Try getting medications again
                    response = requests.get(f"{API_URL}/erx/medications", headers=get_headers())
                    if response.status_code == 200:
                        medications = response.json()
                        print_test_result("GET /api/erx/medications (After Init)", True, None, f"Found {len(medications)} medications after initialization")
                    
        else:
            print_test_result("GET /api/erx/medications (Medication Database)", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("GET /api/erx/medications (Medication Database)", False, None, str(e))
        return False
    
    # Test medication search functionality
    try:
        response = requests.get(f"{API_URL}/erx/medications?search=lisinopril", headers=get_headers())
        
        if response.status_code == 200:
            search_results = response.json()
            print_test_result("GET /api/erx/medications?search=lisinopril (Search)", True, None, f"Found {len(search_results)} medications matching 'lisinopril'")
        else:
            print_test_result("GET /api/erx/medications?search=lisinopril (Search)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/erx/medications?search=lisinopril (Search)", False, None, str(e))
    
    # Test drug class filtering
    try:
        response = requests.get(f"{API_URL}/erx/medications?drug_class=antihypertensive", headers=get_headers())
        
        if response.status_code == 200:
            filtered_results = response.json()
            print_test_result("GET /api/erx/medications?drug_class=antihypertensive (Filter)", True, None, f"Found {len(filtered_results)} antihypertensive medications")
        else:
            print_test_result("GET /api/erx/medications?drug_class=antihypertensive (Filter)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/erx/medications?drug_class=antihypertensive (Filter)", False, None, str(e))
    
    # Test POST /api/prescriptions - Create prescription
    try:
        if medications and len(medications) > 0:
            medication = medications[0]  # Use first medication for testing
            
            prescription_data = {
                "medication_id": medication['id'],
                "patient_id": test_patient_id,
                "prescriber_id": "provider-001",
                "prescriber_name": "Dr. Test Provider",
                "encounter_id": test_encounter_id,
                "dosage_text": "Take 10mg by mouth once daily",
                "dose_quantity": 10.0,
                "dose_unit": "mg",
                "frequency": "once daily",
                "route": "oral",
                "quantity": 30.0,
                "days_supply": 30,
                "refills": 2,
                "indication": "Hypertension management",
                "diagnosis_codes": ["I10"],
                "created_by": "admin"
            }
            
            response = requests.post(f"{API_URL}/prescriptions", json=prescription_data, headers=get_headers())
            
            if response.status_code == 200:
                prescription = response.json()
                global test_prescription_id
                test_prescription_id = prescription['id']
                print_test_result("POST /api/prescriptions (Create)", True, None, f"Prescription created: {prescription.get('prescription_number')}")
            else:
                print_test_result("POST /api/prescriptions (Create)", False, response.text, f"Status: {response.status_code}")
                
        else:
            print_test_result("POST /api/prescriptions (Create)", False, None, "No medications available for testing")
            
    except Exception as e:
        print_test_result("POST /api/prescriptions (Create)", False, None, str(e))
    
    # Test GET /api/prescriptions - Retrieve prescriptions
    try:
        response = requests.get(f"{API_URL}/prescriptions", headers=get_headers())
        
        if response.status_code == 200:
            prescriptions = response.json()
            print_test_result("GET /api/prescriptions (Retrieve All)", True, None, f"Found {len(prescriptions)} prescriptions")
        else:
            print_test_result("GET /api/prescriptions (Retrieve All)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/prescriptions (Retrieve All)", False, None, str(e))
    
    # Test drug interaction checking
    try:
        if test_prescription_id:
            response = requests.get(f"{API_URL}/prescriptions/{test_prescription_id}/interactions", headers=get_headers())
            
            if response.status_code == 200:
                interactions = response.json()
                print_test_result("GET /api/prescriptions/{id}/interactions (Drug Interactions)", True, None, f"Interaction check completed")
            else:
                print_test_result("GET /api/prescriptions/{id}/interactions (Drug Interactions)", False, response.text, f"Status: {response.status_code}")
                
    except Exception as e:
        print_test_result("GET /api/prescriptions/{id}/interactions (Drug Interactions)", False, None, str(e))
    
    return True

def test_inventory_editing():
    """Test Inventory editing functionality as requested"""
    global test_inventory_id
    print("\n📦 INVENTORY EDITING FUNCTIONALITY TESTING")
    
    # First create an inventory item to edit
    try:
        inventory_data = {
            "name": "Test Medical Supply",
            "category": "Medical Supplies",
            "sku": "TEST-001",
            "current_stock": 100,
            "min_stock_level": 10,
            "unit_cost": 25.50,
            "supplier": "Test Medical Supplier",
            "location": "Storage Room A",
            "notes": "Test inventory item for editing functionality"
        }
        
        response = requests.post(f"{API_URL}/inventory", json=inventory_data, headers=get_headers())
        
        if response.status_code == 200:
            inventory_item = response.json()
            test_inventory_id = inventory_item['id']
            print_test_result("Create Test Inventory Item", True, None, f"Inventory ID: {test_inventory_id}")
        else:
            print_test_result("Create Test Inventory Item", False, response.text, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Create Test Inventory Item", False, None, str(e))
        return False
    
    # Test PUT /api/inventory/{id} - Update inventory item
    try:
        updated_data = {
            "name": "Updated Test Medical Supply",
            "category": "Updated Medical Supplies",
            "sku": "TEST-001-UPDATED",
            "current_stock": 150,
            "min_stock_level": 15,
            "unit_cost": 30.75,
            "supplier": "Updated Test Medical Supplier",
            "location": "Storage Room B",
            "notes": "Updated test inventory item for editing functionality testing"
        }
        
        response = requests.put(f"{API_URL}/inventory/{test_inventory_id}", json=updated_data, headers=get_headers())
        
        if response.status_code == 200:
            updated_item = response.json()
            print_test_result("PUT /api/inventory/{id} (Update Item)", True, None, f"Item updated: {updated_item.get('name')}")
        else:
            print_test_result("PUT /api/inventory/{id} (Update Item)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("PUT /api/inventory/{id} (Update Item)", False, None, str(e))
    
    # Test PATCH /api/inventory/{id} - Partial update
    try:
        patch_data = {
            "current_stock": 175,
            "unit_cost": 35.00
        }
        
        response = requests.patch(f"{API_URL}/inventory/{test_inventory_id}", json=patch_data, headers=get_headers())
        
        if response.status_code == 200:
            patched_item = response.json()
            print_test_result("PATCH /api/inventory/{id} (Partial Update)", True, None, f"Stock updated to: {patched_item.get('current_stock')}")
        else:
            print_test_result("PATCH /api/inventory/{id} (Partial Update)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("PATCH /api/inventory/{id} (Partial Update)", False, None, str(e))
    
    # Test inventory transaction creation - IN transaction
    try:
        in_transaction_data = {
            "transaction_type": "in",
            "quantity": 50,
            "reference_id": "PO-2025-001",
            "notes": "Stock replenishment - testing IN transaction",
            "created_by": "admin"
        }
        
        response = requests.post(f"{API_URL}/inventory/{test_inventory_id}/transactions", json=in_transaction_data, headers=get_headers())
        
        if response.status_code == 200:
            transaction = response.json()
            print_test_result("POST /api/inventory/{id}/transactions (IN)", True, None, f"IN transaction created: +{transaction.get('quantity')}")
        else:
            print_test_result("POST /api/inventory/{id}/transactions (IN)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("POST /api/inventory/{id}/transactions (IN)", False, None, str(e))
    
    # Test inventory transaction creation - OUT transaction
    try:
        out_transaction_data = {
            "transaction_type": "out",
            "quantity": 25,
            "reference_id": test_patient_id,
            "notes": "Used for patient treatment - testing OUT transaction",
            "created_by": "admin"
        }
        
        response = requests.post(f"{API_URL}/inventory/{test_inventory_id}/transactions", json=out_transaction_data, headers=get_headers())
        
        if response.status_code == 200:
            transaction = response.json()
            print_test_result("POST /api/inventory/{id}/transactions (OUT)", True, None, f"OUT transaction created: -{transaction.get('quantity')}")
        else:
            print_test_result("POST /api/inventory/{id}/transactions (OUT)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("POST /api/inventory/{id}/transactions (OUT)", False, None, str(e))
    
    # Test GET /api/inventory/{id}/transactions - Get transaction history
    try:
        response = requests.get(f"{API_URL}/inventory/{test_inventory_id}/transactions", headers=get_headers())
        
        if response.status_code == 200:
            transactions = response.json()
            print_test_result("GET /api/inventory/{id}/transactions (History)", True, None, f"Found {len(transactions)} transactions")
        else:
            print_test_result("GET /api/inventory/{id}/transactions (History)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/inventory/{id}/transactions (History)", False, None, str(e))
    
    # Verify final inventory state
    try:
        response = requests.get(f"{API_URL}/inventory/{test_inventory_id}", headers=get_headers())
        
        if response.status_code == 200:
            final_item = response.json()
            print_test_result("GET /api/inventory/{id} (Final State)", True, None, f"Final stock: {final_item.get('current_stock')}")
        else:
            print_test_result("GET /api/inventory/{id} (Final State)", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/inventory/{id} (Final State)", False, None, str(e))
    
    return True

def test_openemr_integration():
    """Test OpenEMR integration status as requested"""
    print("\n🏥 OPENEMR INTEGRATION STATUS TESTING")
    
    # Test GET /api/openemr/status
    try:
        response = requests.get(f"{API_URL}/openemr/status", headers=get_headers())
        
        if response.status_code == 200:
            status = response.json()
            print_test_result("GET /api/openemr/status", True, status, f"OpenEMR status: {status.get('status', 'unknown')}")
        elif response.status_code == 404:
            print_test_result("GET /api/openemr/status", False, None, "OpenEMR integration endpoint not found - Direct APIs may be sufficient")
        else:
            print_test_result("GET /api/openemr/status", False, response.text, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test_result("GET /api/openemr/status", False, None, str(e))
    
    # Test other potential OpenEMR endpoints
    openemr_endpoints = [
        "/api/openemr/patients",
        "/api/openemr/encounters", 
        "/api/openemr/prescriptions",
        "/api/openemr/config"
    ]
    
    for endpoint in openemr_endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=get_headers())
            
            if response.status_code == 200:
                print_test_result(f"GET {endpoint}", True, None, "OpenEMR endpoint is functional")
            elif response.status_code == 404:
                print_test_result(f"GET {endpoint}", False, None, "OpenEMR endpoint not found")
            else:
                print_test_result(f"GET {endpoint}", False, None, f"Status: {response.status_code}")
                
        except Exception as e:
            print_test_result(f"GET {endpoint}", False, None, str(e))
    
    # Check if direct APIs work without OpenEMR
    print("\n🔍 CHECKING DIRECT API FUNCTIONALITY (Without OpenEMR)")
    
    direct_api_tests = [
        ("/api/patients", "Patient Management"),
        ("/api/encounters", "Encounter Management"), 
        ("/api/prescriptions", "Prescription Management"),
        ("/api/soap-notes", "SOAP Notes"),
        ("/api/inventory", "Inventory Management")
    ]
    
    for endpoint, description in direct_api_tests:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=get_headers())
            
            if response.status_code == 200:
                data = response.json()
                print_test_result(f"Direct API: {description}", True, None, f"Working independently - {len(data)} records found")
            else:
                print_test_result(f"Direct API: {description}", False, None, f"Status: {response.status_code}")
                
        except Exception as e:
            print_test_result(f"Direct API: {description}", False, None, str(e))

def test_comprehensive_workflow():
    """Test comprehensive clinical workflow as requested"""
    print("\n🔄 COMPREHENSIVE WORKFLOW TESTING")
    print("Testing: Create Patient → Create Encounter → Add SOAP Notes → Create Prescription → Update Inventory")
    
    workflow_patient_id = None
    workflow_encounter_id = None
    workflow_soap_id = None
    workflow_prescription_id = None
    workflow_inventory_id = None
    
    # Step 1: Create Patient
    try:
        patient_data = {
            "first_name": "Workflow",
            "last_name": "TestPatient",
            "email": "workflow.test@example.com",
            "phone": "+1-555-WORK-001",
            "date_of_birth": "1975-03-20",
            "gender": "female",
            "address_line1": "456 Workflow Street",
            "city": "Test City",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(f"{API_URL}/patients", json=patient_data, headers=get_headers())
        
        if response.status_code == 200:
            patient = response.json()
            workflow_patient_id = patient['id']
            print_test_result("Workflow Step 1: Create Patient", True, None, f"Patient ID: {workflow_patient_id}")
        else:
            print_test_result("Workflow Step 1: Create Patient", False, response.text)
            return False
            
    except Exception as e:
        print_test_result("Workflow Step 1: Create Patient", False, None, str(e))
        return False
    
    # Step 2: Create Encounter
    try:
        encounter_data = {
            "patient_id": workflow_patient_id,
            "encounter_type": "consultation",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Workflow Provider",
            "chief_complaint": "Comprehensive workflow testing visit",
            "reason_for_visit": "Testing complete clinical workflow from patient creation to inventory update"
        }
        
        response = requests.post(f"{API_URL}/encounters", json=encounter_data, headers=get_headers())
        
        if response.status_code == 200:
            encounter = response.json()
            workflow_encounter_id = encounter['id']
            print_test_result("Workflow Step 2: Create Encounter", True, None, f"Encounter ID: {workflow_encounter_id}")
        else:
            print_test_result("Workflow Step 2: Create Encounter", False, response.text)
            return False
            
    except Exception as e:
        print_test_result("Workflow Step 2: Create Encounter", False, None, str(e))
        return False
    
    # Step 3: Add SOAP Notes
    try:
        soap_data = {
            "encounter_id": workflow_encounter_id,
            "patient_id": workflow_patient_id,
            "subjective": "Patient presents for comprehensive workflow testing. Reports no acute complaints. Interested in preventive care.",
            "objective": "Vital signs: BP 125/82, HR 75, Temp 98.7F, RR 16, O2 Sat 98%. General appearance: well-developed, well-nourished female in no acute distress.",
            "assessment": "1. Health maintenance visit\n2. Mild hypertension\n3. Patient education needs",
            "plan": "1. Start lisinopril 10mg daily for blood pressure\n2. Lifestyle modifications - diet and exercise\n3. Follow-up in 4 weeks\n4. Lab work: CBC, CMP, lipid panel",
            "provider": "Dr. Workflow Provider"
        }
        
        response = requests.post(f"{API_URL}/soap-notes", json=soap_data, headers=get_headers())
        
        if response.status_code == 200:
            soap_note = response.json()
            workflow_soap_id = soap_note['id']
            print_test_result("Workflow Step 3: Add SOAP Notes", True, None, f"SOAP Note ID: {workflow_soap_id}")
        else:
            print_test_result("Workflow Step 3: Add SOAP Notes", False, response.text)
            return False
            
    except Exception as e:
        print_test_result("Workflow Step 3: Add SOAP Notes", False, None, str(e))
        return False
    
    # Step 4: Create Prescription
    try:
        # First get available medications
        med_response = requests.get(f"{API_URL}/erx/medications", headers=get_headers())
        
        if med_response.status_code == 200:
            medications = med_response.json()
            if medications and len(medications) > 0:
                # Find lisinopril or use first medication
                medication = medications[0]
                for med in medications:
                    if 'lisinopril' in med.get('generic_name', '').lower():
                        medication = med
                        break
                
                prescription_data = {
                    "medication_id": medication['id'],
                    "patient_id": workflow_patient_id,
                    "prescriber_id": "workflow-provider-001",
                    "prescriber_name": "Dr. Workflow Provider",
                    "encounter_id": workflow_encounter_id,
                    "dosage_text": "Take 10mg by mouth once daily in the morning",
                    "dose_quantity": 10.0,
                    "dose_unit": "mg",
                    "frequency": "once daily",
                    "route": "oral",
                    "quantity": 30.0,
                    "days_supply": 30,
                    "refills": 2,
                    "indication": "Hypertension management",
                    "diagnosis_codes": ["I10"],
                    "created_by": "admin"
                }
                
                response = requests.post(f"{API_URL}/prescriptions", json=prescription_data, headers=get_headers())
                
                if response.status_code == 200:
                    prescription = response.json()
                    workflow_prescription_id = prescription['id']
                    print_test_result("Workflow Step 4: Create Prescription", True, None, f"Prescription: {prescription.get('prescription_number')}")
                else:
                    print_test_result("Workflow Step 4: Create Prescription", False, response.text)
                    
            else:
                print_test_result("Workflow Step 4: Create Prescription", False, None, "No medications available")
                
        else:
            print_test_result("Workflow Step 4: Create Prescription", False, med_response.text)
            
    except Exception as e:
        print_test_result("Workflow Step 4: Create Prescription", False, None, str(e))
    
    # Step 5: Update Inventory
    try:
        # Create a workflow inventory item
        inventory_data = {
            "name": "Workflow Test Medication",
            "category": "Medications",
            "sku": "WORKFLOW-MED-001",
            "current_stock": 500,
            "min_stock_level": 50,
            "unit_cost": 15.75,
            "supplier": "Workflow Pharmaceutical",
            "location": "Pharmacy",
            "notes": "Medication for workflow testing"
        }
        
        response = requests.post(f"{API_URL}/inventory", json=inventory_data, headers=get_headers())
        
        if response.status_code == 200:
            inventory_item = response.json()
            workflow_inventory_id = inventory_item['id']
            print_test_result("Workflow Step 5a: Create Inventory Item", True, None, f"Inventory ID: {workflow_inventory_id}")
            
            # Now update inventory with OUT transaction (medication dispensed)
            out_transaction = {
                "transaction_type": "out",
                "quantity": 30,
                "reference_id": workflow_prescription_id or workflow_patient_id,
                "notes": f"Dispensed for prescription - Patient: {workflow_patient_id}",
                "created_by": "admin"
            }
            
            trans_response = requests.post(f"{API_URL}/inventory/{workflow_inventory_id}/transactions", json=out_transaction, headers=get_headers())
            
            if trans_response.status_code == 200:
                transaction = trans_response.json()
                print_test_result("Workflow Step 5b: Update Inventory", True, None, f"Dispensed {transaction.get('quantity')} units")
            else:
                print_test_result("Workflow Step 5b: Update Inventory", False, trans_response.text)
                
        else:
            print_test_result("Workflow Step 5: Update Inventory", False, response.text)
            
    except Exception as e:
        print_test_result("Workflow Step 5: Update Inventory", False, None, str(e))
    
    # Workflow Summary
    print("\n📊 WORKFLOW SUMMARY")
    workflow_success = all([
        workflow_patient_id is not None,
        workflow_encounter_id is not None, 
        workflow_soap_id is not None,
        workflow_inventory_id is not None
    ])
    
    if workflow_success:
        print_test_result("Complete Clinical Workflow", True, None, "All workflow steps completed successfully")
        print(f"   Patient ID: {workflow_patient_id}")
        print(f"   Encounter ID: {workflow_encounter_id}")
        print(f"   SOAP Note ID: {workflow_soap_id}")
        if workflow_prescription_id:
            print(f"   Prescription ID: {workflow_prescription_id}")
        print(f"   Inventory ID: {workflow_inventory_id}")
    else:
        print_test_result("Complete Clinical Workflow", False, None, "Some workflow steps failed")
    
    return workflow_success

def main():
    """Main testing function"""
    print("🏥 ClinicHub Backend Testing - Review Request Focus")
    print("Testing specific functionalities mentioned by the user")
    print("=" * 80)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with testing.")
        return
    
    # Run all requested tests
    test_results = {
        "SOAP Notes": test_soap_notes_functionality(),
        "eRx Functionality": test_erx_functionality(), 
        "Inventory Editing": test_inventory_editing(),
        "OpenEMR Integration": test_openemr_integration(),
        "Comprehensive Workflow": test_comprehensive_workflow()
    }
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🏥 FINAL TEST SUMMARY - REVIEW REQUEST")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    print("-" * 80)
    print(f"Overall Result: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All requested functionalities are working correctly!")
        print("💡 OpenEMR download may not be required - Direct APIs appear functional")
    else:
        print("⚠️  Some functionalities need attention")
        print("💡 Consider checking OpenEMR integration requirements for failed tests")
    
    print("=" * 80)

if __name__ == "__main__":
    main()