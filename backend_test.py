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

# Test FHIR-Compliant Patient Management
def test_patient_management():
    print("\n--- Testing FHIR-Compliant Patient Management ---")
    
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
        
        # Verify FHIR compliance
        assert result["resource_type"] == "Patient"
        assert isinstance(result["name"], list)
        assert result["name"][0]["family"] == "Johnson"
        assert "Sarah" in result["name"][0]["given"]
        
        patient_id = result["id"]
        print_test_result("Create Patient", True, result)
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Patient", False)
        return
    
    # Test getting all patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patients", True, result)
    except Exception as e:
        print(f"Error getting patients: {str(e)}")
        print_test_result("Get Patients", False)
    
    # Test getting a specific patient
    if patient_id:
        try:
            url = f"{API_URL}/patients/{patient_id}"
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == patient_id
            print_test_result("Get Patient by ID", True, result)
        except Exception as e:
            print(f"Error getting patient by ID: {str(e)}")
            print_test_result("Get Patient by ID", False)
    
    return patient_id

# Test SmartForm System
def test_smartform_system(patient_id):
    print("\n--- Testing SmartForm System ---")
    
    # Test creating a form
    form_id = None
    try:
        url = f"{API_URL}/forms"
        data = {
            "title": "Comprehensive Medical Assessment",
            "description": "Standard medical assessment form with FHIR mapping",
            "fields": [
                {
                    "type": "text",
                    "label": "Chief Complaint",
                    "placeholder": "Patient's main concern",
                    "required": True,
                    "smart_tag": "{patient_complaint}"
                },
                {
                    "type": "select",
                    "label": "Pain Level",
                    "required": True,
                    "options": ["None", "Mild", "Moderate", "Severe", "Very Severe"],
                    "smart_tag": "{pain_level}"
                }
            ],
            "status": "active",
            "fhir_mapping": {
                "chief_complaint": "Observation.code.text",
                "pain_level": "Observation.valueQuantity"
            }
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        form_id = result["id"]
        print_test_result("Create Form", True, result)
    except Exception as e:
        print(f"Error creating form: {str(e)}")
        print_test_result("Create Form", False)
        return
    
    # Test getting all forms
    try:
        url = f"{API_URL}/forms"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Forms", True, result)
    except Exception as e:
        print(f"Error getting forms: {str(e)}")
        print_test_result("Get Forms", False)
    
    # Test submitting a form
    if form_id and patient_id:
        try:
            url = f"{API_URL}/forms/{form_id}/submit"
            data = {
                "chief_complaint": "Persistent headache for 3 days",
                "pain_level": "Moderate"
            }
            params = {"patient_id": patient_id}
            
            response = requests.post(url, json=data, params=params)
            response.raise_for_status()
            result = response.json()
            
            assert result["form_id"] == form_id
            assert result["patient_id"] == patient_id
            print_test_result("Submit Form", True, result)
        except Exception as e:
            print(f"Error submitting form: {str(e)}")
            print_test_result("Submit Form", False)
    
    return form_id

# Test Invoice/Receipt Management
def test_invoice_management(patient_id):
    print("\n--- Testing Invoice/Receipt Management ---")
    
    # Test creating an invoice
    invoice_id = None
    if not patient_id:
        print("Skipping invoice tests - no patient ID available")
        return
    
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Initial Consultation",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "total": 150.00
                },
                {
                    "description": "Blood Test - Complete Blood Count",
                    "quantity": 1,
                    "unit_price": 75.00,
                    "total": 75.00
                }
            ],
            "tax_rate": 0.07,
            "due_days": 30,
            "notes": "Please pay within 30 days of receipt."
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify invoice creation and automatic numbering
        assert "invoice_number" in result
        assert result["invoice_number"].startswith("INV-")
        
        invoice_id = result["id"]
        print_test_result("Create Invoice", True, result)
    except Exception as e:
        print(f"Error creating invoice: {str(e)}")
        print_test_result("Create Invoice", False)
        return
    
    # Test getting all invoices
    try:
        url = f"{API_URL}/invoices"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Invoices", True, result)
    except Exception as e:
        print(f"Error getting invoices: {str(e)}")
        print_test_result("Get Invoices", False)
    
    # Test getting a specific invoice
    if invoice_id:
        try:
            url = f"{API_URL}/invoices/{invoice_id}"
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == invoice_id
            print_test_result("Get Invoice by ID", True, result)
        except Exception as e:
            print(f"Error getting invoice by ID: {str(e)}")
            print_test_result("Get Invoice by ID", False)
    
    return invoice_id

# Test Inventory Management
def test_inventory_management():
    print("\n--- Testing Inventory Management ---")
    
    # Test creating an inventory item
    item_id = None
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Amoxicillin 500mg",
            "category": "Antibiotics",
            "sku": "MED-AMOX-500",
            "current_stock": 100,
            "min_stock_level": 20,
            "unit_cost": 1.25,
            "supplier": "MedPharm Supplies",
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "location": "Pharmacy Cabinet B",
            "notes": "Keep at room temperature"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        item_id = result["id"]
        print_test_result("Create Inventory Item", True, result)
    except Exception as e:
        print(f"Error creating inventory item: {str(e)}")
        print_test_result("Create Inventory Item", False)
        return
    
    # Test getting all inventory items
    try:
        url = f"{API_URL}/inventory"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Inventory", True, result)
    except Exception as e:
        print(f"Error getting inventory: {str(e)}")
        print_test_result("Get Inventory", False)
    
    # Test inventory transactions
    if item_id:
        try:
            url = f"{API_URL}/inventory/{item_id}/transaction"
            data = {
                "transaction_type": "in",
                "quantity": 50,
                "notes": "Received new shipment",
                "created_by": "Dr. Smith"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Inventory Transaction (IN)", True, result)
            
            # Test "out" transaction
            data = {
                "transaction_type": "out",
                "quantity": 25,
                "notes": "Dispensed to patient",
                "created_by": "Nurse Johnson"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Inventory Transaction (OUT)", True, result)
        except Exception as e:
            print(f"Error with inventory transaction: {str(e)}")
            print_test_result("Inventory Transaction", False)
    
    return item_id

# Test Employee Management
def test_employee_management():
    print("\n--- Testing Employee Management ---")
    
    # Test creating an employee
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "dr.chen@clinichub.com",
            "phone": "+1-555-987-6543",
            "role": "doctor",
            "hire_date": date.today().isoformat(),
            "salary": 120000.00
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify employee ID generation
        assert "employee_id" in result
        assert result["employee_id"].startswith("EMP-")
        
        print_test_result("Create Employee", True, result)
    except Exception as e:
        print(f"Error creating employee: {str(e)}")
        print_test_result("Create Employee", False)
        return
    
    # Test getting all employees
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Employees", True, result)
    except Exception as e:
        print(f"Error getting employees: {str(e)}")
        print_test_result("Get Employees", False)

# Test Dashboard Analytics
def test_dashboard_analytics():
    print("\n--- Testing Dashboard Analytics ---")
    
    try:
        url = f"{API_URL}/dashboard/stats"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify dashboard stats structure
        assert "stats" in result
        assert "total_patients" in result["stats"]
        assert "total_invoices" in result["stats"]
        assert "pending_invoices" in result["stats"]
        assert "low_stock_items" in result["stats"]
        assert "total_employees" in result["stats"]
        
        print_test_result("Dashboard Stats", True, result)
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        print_test_result("Dashboard Stats", False)

# Test SOAP Notes System
def test_soap_notes_system(patient_id):
    print("\n--- Testing SOAP Notes System ---")
    
    # First, create an encounter for the patient
    encounter_id = None
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
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify encounter creation and auto-numbering
        assert "encounter_number" in result
        assert result["encounter_number"].startswith("ENC-")
        
        encounter_id = result["id"]
        print_test_result("Create Encounter for SOAP Notes", True, result)
    except Exception as e:
        print(f"Error creating encounter: {str(e)}")
        print_test_result("Create Encounter for SOAP Notes", False)
        return None
    
    # Test creating a SOAP note
    soap_note_id = None
    if encounter_id:
        try:
            url = f"{API_URL}/soap-notes"
            data = {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "subjective": "Patient reports persistent headache for 5 days, describes it as throbbing pain behind the eyes. Pain level 7/10. Reports light sensitivity and nausea. No fever.",
                "objective": "Vital signs stable. BP 120/80, HR 72, Temp 98.6°F. HEENT: Pupils equal and reactive. No sinus tenderness. Neurological exam normal.",
                "assessment": "Migraine headache, possibly triggered by recent stress and lack of sleep.",
                "plan": "1. Prescribed sumatriptan 50mg PRN for acute episodes. 2. Recommended stress reduction techniques. 3. Follow up in 2 weeks. 4. If symptoms worsen, return to clinic immediately.",
                "provider": "Dr. Michael Chen"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            soap_note_id = result["id"]
            print_test_result("Create SOAP Note", True, result)
        except Exception as e:
            print(f"Error creating SOAP note: {str(e)}")
            print_test_result("Create SOAP Note", False)
    
    # Test getting SOAP notes by encounter
    if encounter_id:
        try:
            url = f"{API_URL}/soap-notes/encounter/{encounter_id}"
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get SOAP Notes by Encounter", True, result)
        except Exception as e:
            print(f"Error getting SOAP notes by encounter: {str(e)}")
            print_test_result("Get SOAP Notes by Encounter", False)
    
    # Test getting SOAP notes by patient
    try:
        url = f"{API_URL}/soap-notes/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get SOAP Notes by Patient", True, result)
    except Exception as e:
        print(f"Error getting SOAP notes by patient: {str(e)}")
        print_test_result("Get SOAP Notes by Patient", False)
    
    return encounter_id

# Test Encounter/Visit Management
def test_encounter_management(patient_id):
    print("\n--- Testing Encounter/Visit Management ---")
    
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
        
        # Verify encounter creation and auto-numbering
        assert "encounter_number" in result
        assert result["encounter_number"].startswith("ENC-")
        
        encounter_id = result["id"]
        print_test_result("Create Encounter", True, result)
    except Exception as e:
        print(f"Error creating encounter: {str(e)}")
        print_test_result("Create Encounter", False)
        return
    
    # Test getting all encounters
    try:
        url = f"{API_URL}/encounters"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Encounters", True, result)
    except Exception as e:
        print(f"Error getting all encounters: {str(e)}")
        print_test_result("Get All Encounters", False)
    
    # Test getting encounters by patient
    try:
        url = f"{API_URL}/encounters/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Encounters", True, result)
    except Exception as e:
        print(f"Error getting patient encounters: {str(e)}")
        print_test_result("Get Patient Encounters", False)
    
    # Test updating encounter status
    if encounter_id:
        try:
            url = f"{API_URL}/encounters/{encounter_id}/status"
            params = {"status": "arrived"}
            
            response = requests.put(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Encounter Status (Arrived)", True, result)
            
            # Update to in_progress
            params = {"status": "in_progress"}
            response = requests.put(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Encounter Status (In Progress)", True, result)
            
            # Update to completed
            params = {"status": "completed"}
            response = requests.put(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Encounter Status (Completed)", True, result)
        except Exception as e:
            print(f"Error updating encounter status: {str(e)}")
            print_test_result("Update Encounter Status", False)
    
    return encounter_id

# Test Vital Signs Recording
def test_vital_signs(patient_id, encounter_id):
    print("\n--- Testing Vital Signs Recording ---")
    
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
        print_test_result("Get Patient Vital Signs", False)

# Test Allergy Management
def test_allergy_management(patient_id):
    print("\n--- Testing Allergy Management ---")
    
    # Test creating an allergy
    allergy_id = None
    try:
        url = f"{API_URL}/allergies"
        data = {
            "patient_id": patient_id,
            "allergen": "Penicillin",
            "reaction": "Hives, difficulty breathing",
            "severity": "severe",
            "onset_date": "2018-05-10",
            "notes": "First discovered during treatment for strep throat",
            "created_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        allergy_id = result["id"]
        print_test_result("Create Allergy", True, result)
    except Exception as e:
        print(f"Error creating allergy: {str(e)}")
        print_test_result("Create Allergy", False)
    
    # Test getting allergies by patient
    try:
        url = f"{API_URL}/allergies/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Allergies", True, result)
    except Exception as e:
        print(f"Error getting patient allergies: {str(e)}")
        print_test_result("Get Patient Allergies", False)
    
    return allergy_id

# Test Medication Management
def test_medication_management(patient_id):
    print("\n--- Testing Medication Management ---")
    
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
        print_test_result("Create Medication", False)
    
    # Test getting medications by patient
    try:
        url = f"{API_URL}/medications/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Medications", True, result)
    except Exception as e:
        print(f"Error getting patient medications: {str(e)}")
        print_test_result("Get Patient Medications", False)
    
    # Test updating medication status
    if medication_id:
        try:
            url = f"{API_URL}/medications/{medication_id}/status"
            params = {"status": "discontinued"}
            
            response = requests.put(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Medication Status", True, result)
        except Exception as e:
            print(f"Error updating medication status: {str(e)}")
            print_test_result("Update Medication Status", False)
    
    return medication_id

# Test Medical History
def test_medical_history(patient_id):
    print("\n--- Testing Medical History ---")
    
    # Test creating a medical history entry
    try:
        url = f"{API_URL}/medical-history"
        data = {
            "patient_id": patient_id,
            "condition": "Essential (primary) hypertension",
            "icd10_code": "I10",
            "diagnosis_date": "2020-03-15",
            "status": "active",
            "notes": "Well-controlled with medication",
            "diagnosed_by": "Dr. Sarah Williams"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Medical History", True, result)
    except Exception as e:
        print(f"Error creating medical history: {str(e)}")
        print_test_result("Create Medical History", False)
    
    # Test getting medical history by patient
    try:
        url = f"{API_URL}/medical-history/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Medical History", True, result)
    except Exception as e:
        print(f"Error getting patient medical history: {str(e)}")
        print_test_result("Get Patient Medical History", False)

# Test Diagnosis and Procedure Coding
def test_diagnosis_procedure(patient_id, encounter_id):
    print("\n--- Testing Diagnosis and Procedure Coding ---")
    
    # Test creating a diagnosis
    try:
        url = f"{API_URL}/diagnoses"
        data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "diagnosis_code": "J45.909",
            "diagnosis_description": "Unspecified asthma, uncomplicated",
            "diagnosis_type": "primary",
            "status": "active",
            "onset_date": "2021-06-10",
            "provider": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Diagnosis", True, result)
    except Exception as e:
        print(f"Error creating diagnosis: {str(e)}")
        print_test_result("Create Diagnosis", False)
    
    # Test creating a procedure
    try:
        url = f"{API_URL}/procedures"
        data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "procedure_code": "94010",
            "procedure_description": "Spirometry, including graphic record, total and timed vital capacity",
            "procedure_date": date.today().isoformat(),
            "provider": "Dr. Michael Chen",
            "location": "Pulmonary Function Lab",
            "notes": "Patient tolerated procedure well"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Procedure", True, result)
    except Exception as e:
        print(f"Error creating procedure: {str(e)}")
        print_test_result("Create Procedure", False)
    
    # Test getting diagnoses by encounter
    try:
        url = f"{API_URL}/diagnoses/encounter/{encounter_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Encounter Diagnoses", True, result)
    except Exception as e:
        print(f"Error getting encounter diagnoses: {str(e)}")
        print_test_result("Get Encounter Diagnoses", False)
    
    # Test getting diagnoses by patient
    try:
        url = f"{API_URL}/diagnoses/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Diagnoses", True, result)
    except Exception as e:
        print(f"Error getting patient diagnoses: {str(e)}")
        print_test_result("Get Patient Diagnoses", False)
    
    # Test getting procedures by encounter
    try:
        url = f"{API_URL}/procedures/encounter/{encounter_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Encounter Procedures", True, result)
    except Exception as e:
        print(f"Error getting encounter procedures: {str(e)}")
        print_test_result("Get Encounter Procedures", False)
    
    # Test getting procedures by patient
    try:
        url = f"{API_URL}/procedures/patient/{patient_id}"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Procedures", True, result)
    except Exception as e:
        print(f"Error getting patient procedures: {str(e)}")
        print_test_result("Get Patient Procedures", False)

# Test Patient Summary
def test_patient_summary(patient_id):
    print("\n--- Testing Comprehensive Patient Summary ---")
    
    try:
        url = f"{API_URL}/patients/{patient_id}/summary"
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive summary structure
        assert "patient" in result
        assert "recent_encounters" in result
        assert "allergies" in result
        assert "active_medications" in result
        assert "medical_history" in result
        
        print_test_result("Get Patient Summary", True, result)
    except Exception as e:
        print(f"Error getting patient summary: {str(e)}")
        print_test_result("Get Patient Summary", False)

def run_all_tests():
    print("\n" + "=" * 80)
    print("TESTING CLINICHUB BACKEND API")
    print("=" * 80)
    
    # Run all tests in sequence
    patient_id = test_patient_management()
    test_smartform_system(patient_id)
    test_invoice_management(patient_id)
    test_inventory_management()
    test_employee_management()
    
    # Test new EHR features
    soap_encounter_id = test_soap_notes_system(patient_id)
    encounter_id = test_encounter_management(patient_id)
    test_vital_signs(patient_id, encounter_id)
    test_allergy_management(patient_id)
    test_medication_management(patient_id)
    test_medical_history(patient_id)
    test_diagnosis_procedure(patient_id, encounter_id if encounter_id else soap_encounter_id)
    test_patient_summary(patient_id)
    
    test_dashboard_analytics()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()