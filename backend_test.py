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

# Test Authentication System
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test variables to store authentication data
    admin_token = None
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
        # Verify admin initialization response
        assert "message" in result
        assert "username" in result
        assert "password" in result
        assert result["username"] == "admin"
        assert result["password"] == "admin123"
        
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Admin User", False)
    
    # Test 2: Login with Admin Credentials
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
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    # Test 3: Get Current User Info
    if admin_token:
        try:
            url = f"{API_URL}/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify user info
            assert result["username"] == "admin"
            assert result["role"] == "admin"
            
            print_test_result("Get Current User", True, result)
        except Exception as e:
            print(f"Error getting current user: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Current User", False)
    
    # Test 4: Access Protected Endpoint
    if admin_token:
        try:
            # Try to access a protected endpoint (get users)
            url = f"{API_URL}/users"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Access Protected Endpoint", True, result)
        except Exception as e:
            print(f"Error accessing protected endpoint: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Access Protected Endpoint", False)
    
    # Test 5: Login with Invalid Credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = requests.post(url, json=data)
        
        # This should fail with 401
        assert response.status_code == 401
        result = response.json()
        assert "detail" in result
        
        print_test_result("Login with Invalid Credentials (Expected to Fail)", True, {"status_code": response.status_code, "detail": result.get("detail")})
    except Exception as e:
        print(f"Error testing invalid login: {str(e)}")
        print_test_result("Login with Invalid Credentials", False)
    
    # Test 6: Logout
    if admin_token:
        try:
            url = f"{API_URL}/auth/logout"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert "message" in result
            
            print_test_result("Logout", True, result)
        except Exception as e:
            print(f"Error logging out: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Logout", False)
    
    return admin_token

def test_erx_system(patient_id, admin_token):
    print("\n--- Testing eRx (Electronic Prescribing) System ---")
    
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
        return None, None
    
    # Test 2: Search Medications
    medication_id = None
    try:
        url = f"{API_URL}/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"search": "Lisinopril"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify FHIR-compliant medication structure
        assert len(result) > 0
        assert result[0]["resource_type"] == "Medication"
        assert "code" in result[0]
        assert "generic_name" in result[0]
        
        medication_id = result[0]["id"]
        print_test_result("Search Medications", True, result)
    except Exception as e:
        print(f"Error searching medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications", False)
    
    # Test 3: Filter Medications by Drug Class
    try:
        url = f"{API_URL}/medications"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"drug_class": "antibiotic"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify filtering works
        assert len(result) > 0
        assert all(med["drug_class"] == "antibiotic" for med in result)
        
        print_test_result("Filter Medications by Drug Class", True, result)
    except Exception as e:
        print(f"Error filtering medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Filter Medications by Drug Class", False)
    
    # Test 4: Get Medication Details
    if medication_id:
        try:
            url = f"{API_URL}/medications/{medication_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify detailed medication information
            assert result["id"] == medication_id
            assert "contraindications" in result
            assert "warnings" in result
            assert "standard_dosing" in result
            
            print_test_result("Get Medication Details", True, result)
        except Exception as e:
            print(f"Error getting medication details: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Medication Details", False)
    
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
            assert "allergies_checked" in result
            assert "interactions_checked" in result
            
            prescription_id = result["id"]
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
    
    return medication_id, prescription_id

def test_scheduling_system(patient_id, admin_token):
    print("\n--- Testing Scheduling System ---")
    
    # Test 1: Create Provider
    provider_id = None
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Robert",
            "last_name": "Wilson",
            "title": "Dr.",
            "specialties": ["Cardiology", "Internal Medicine"],
            "license_number": "MD12345",
            "npi_number": "1234567890",
            "email": "dr.wilson@clinichub.com",
            "phone": "+1-555-789-0123",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print_test_result("Create Provider", True, result)
    except Exception as e:
        print(f"Error creating provider: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Provider", False)
    
    # Test 2: Get All Providers
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Providers", True, result)
    except Exception as e:
        print(f"Error getting providers: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Providers", False)
    
    # Test 3: Generate Provider Schedule
    if provider_id:
        try:
            url = f"{API_URL}/providers/{provider_id}/schedule"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
            
            response = requests.post(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Generate Provider Schedule", True, result)
        except Exception as e:
            print(f"Error generating provider schedule: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Generate Provider Schedule", False)
    
    # Test 4: Create Appointment
    appointment_id = None
    if provider_id and patient_id:
        try:
            url = f"{API_URL}/appointments"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "appointment_date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "consultation",
                "reason": "Initial cardiology consultation",
                "location": "Main Clinic",
                "scheduled_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify appointment creation
            assert "appointment_number" in result
            assert result["appointment_number"].startswith("APT")
            
            appointment_id = result["id"]
            print_test_result("Create Appointment", True, result)
        except Exception as e:
            print(f"Error creating appointment: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Appointment", False)
    
    # Test 5: Get All Appointments
    try:
        url = f"{API_URL}/appointments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Appointments", True, result)
    except Exception as e:
        print(f"Error getting appointments: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Appointments", False)
    
    # Test 6: Get Patient Appointments
    if patient_id:
        try:
            url = f"{API_URL}/appointments/patient/{patient_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Patient Appointments", True, result)
        except Exception as e:
            print(f"Error getting patient appointments: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Patient Appointments", False)
    
    # Test 7: Update Appointment Status
    if appointment_id:
        try:
            url = f"{API_URL}/appointments/{appointment_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "confirmed"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Appointment Status (Confirmed)", True, result)
            
            # Update to arrived
            params = {"status": "arrived"}
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Appointment Status (Arrived)", True, result)
        except Exception as e:
            print(f"Error updating appointment status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Appointment Status", False)
    
    # Test 8: Get Calendar View
    try:
        url = f"{API_URL}/appointments/calendar"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "view_type": "week",
            "start_date": date.today().isoformat()
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Calendar View (Week)", True, result)
        
        # Test day view
        params["view_type"] = "day"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Calendar View (Day)", True, result)
        
        # Test month view
        params["view_type"] = "month"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Calendar View (Month)", True, result)
    except Exception as e:
        print(f"Error getting calendar view: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Calendar View", False)
    
    # Test 9: Appointment Conflict Detection
    if provider_id and patient_id:
        try:
            # Try to create an overlapping appointment
            url = f"{API_URL}/appointments"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "appointment_date": date.today().isoformat(),
                "start_time": "10:15",  # Overlaps with existing 10:00-10:30 appointment
                "end_time": "10:45",
                "appointment_type": "follow_up",
                "reason": "This should fail due to conflict",
                "location": "Main Clinic",
                "scheduled_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            # This should fail with 409 Conflict
            assert response.status_code == 409
            result = response.json()
            assert "detail" in result
            
            print_test_result("Appointment Conflict Detection (Expected to Fail)", True, {"status_code": response.status_code, "detail": result.get("detail")})
        except Exception as e:
            print(f"Error testing appointment conflict: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Appointment Conflict Detection", False)
    
    return provider_id, appointment_id

def test_patient_communications(patient_id, admin_token):
    print("\n--- Testing Patient Communications System ---")
    
    # Test 1: Initialize Communication Templates
    try:
        url = f"{API_URL}/communications/init-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Communication Templates", True, result)
    except Exception as e:
        print(f"Error initializing communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Communication Templates", False)
    
    # Test 2: Get Communication Templates
    template_id = None
    try:
        url = f"{API_URL}/communications/templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if len(result) > 0:
            template_id = result[0]["id"]
        
        print_test_result("Get Communication Templates", True, result)
    except Exception as e:
        print(f"Error getting communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Communication Templates", False)
    
    # Test 3: Create Custom Template
    if not template_id:
        try:
            url = f"{API_URL}/communications/templates"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "name": "Lab Results Notification",
                "message_type": "test_results",
                "subject_template": "Your Lab Results from {clinic_name}",
                "content_template": "Dear {patient_name},\n\nYour recent lab results are now available. Please log in to your patient portal to view them or contact our office at {clinic_phone}.\n\nRegards,\n{provider_name}"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            template_id = result["id"]
            print_test_result("Create Custom Template", True, result)
        except Exception as e:
            print(f"Error creating custom template: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Custom Template", False)
    
    # Test 4: Send Message to Patient
    message_id = None
    if patient_id and template_id:
        try:
            url = f"{API_URL}/communications/send"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "template_id": template_id,
                "sender_id": "admin",
                "sender_name": "Dr. Admin",
                "template_variables": {
                    "clinic_name": "ClinicHub Medical Center",
                    "clinic_phone": "555-123-4567",
                    "provider_name": "Dr. Admin"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            message_id = result["id"]
            print_test_result("Send Message to Patient", True, result)
        except Exception as e:
            print(f"Error sending message to patient: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Send Message to Patient", False)
    
    # Test 5: Get All Messages
    try:
        url = f"{API_URL}/communications/messages"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Messages", True, result)
    except Exception as e:
        print(f"Error getting all messages: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Messages", False)
    
    # Test 6: Get Patient Messages
    if patient_id:
        try:
            url = f"{API_URL}/communications/messages/patient/{patient_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Patient Messages", True, result)
        except Exception as e:
            print(f"Error getting patient messages: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Patient Messages", False)
    
    # Test 7: Update Message Status
    if message_id:
        try:
            url = f"{API_URL}/communications/messages/{message_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "delivered"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Message Status (Delivered)", True, result)
            
            # Update to read
            params = {"status": "read"}
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Message Status (Read)", True, result)
        except Exception as e:
            print(f"Error updating message status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Message Status", False)
    
    # Test 8: Send Direct Message (without template)
    try:
        url = f"{API_URL}/communications/send-direct"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "subject": "Important Information About Your Next Visit",
            "content": "Please remember to bring your insurance card and a list of current medications to your next appointment.",
            "message_type": "general",
            "sender_id": "admin",
            "sender_name": "Dr. Admin"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Send Direct Message", True, result)
    except Exception as e:
        print(f"Error sending direct message: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Send Direct Message", False)
    
    return template_id, message_id

def test_lab_integration(admin_token, patient_id, provider_id=None):
    print("\n--- Testing Lab Integration ---")
    
    # If no provider_id is provided, create a provider
    if not provider_id:
        try:
            url = f"{API_URL}/providers"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "first_name": "Robert",
                "last_name": "Wilson",
                "title": "Dr.",
                "specialties": ["Cardiology", "Internal Medicine"],
                "license_number": "MD12345",
                "npi_number": "1234567890",
                "email": "dr.wilson@clinichub.com",
                "phone": "+1-555-789-0123"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            provider_id = result["id"]
            print_test_result("Create Provider for Lab Tests", True, result)
        except Exception as e:
            print(f"Error creating provider: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Provider for Lab Tests", False)
            return None
    
    # Test 1: Initialize Lab Tests
    try:
        url = f"{API_URL}/lab-tests/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Lab Tests", True, result)
    except Exception as e:
        print(f"Error initializing lab tests: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Lab Tests", False)
    
    # Test 2: Get Lab Tests
    lab_test_ids = []
    try:
        url = f"{API_URL}/lab-tests"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Store lab test IDs for later use
        if len(result) > 0:
            lab_test_ids = [test["id"] for test in result[:3]]  # Get first 3 tests
        
        print_test_result("Get Lab Tests", True, result)
    except Exception as e:
        print(f"Error getting lab tests: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Lab Tests", False)
    
    # Test 3: Initialize ICD-10 Codes
    try:
        url = f"{API_URL}/icd10/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize ICD-10 Codes", True, result)
    except Exception as e:
        print(f"Error initializing ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize ICD-10 Codes", False)
    
    # Test 4: Search ICD-10 Codes
    icd10_codes = []
    try:
        url = f"{API_URL}/icd10/search"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Store ICD-10 codes for later use
        if len(result) > 0:
            icd10_codes = [code["code"] for code in result[:2]]  # Get first 2 codes
        
        print_test_result("Search ICD-10 Codes", True, result)
    except Exception as e:
        print(f"Error searching ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search ICD-10 Codes", False)
    
    # Test 5: Create Lab Order
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
                "notes": "Patient fasting for 12 hours",
                "ordered_by": "Dr. Robert Wilson"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            lab_order_id = result["id"]
            print_test_result("Create Lab Order", True, result)
        except Exception as e:
            print(f"Error creating lab order: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Lab Order", False)
    else:
        print("Skipping Create Lab Order test - missing required IDs")
    
    # Test 6: Get Lab Orders
    try:
        url = f"{API_URL}/lab-orders"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Lab Orders", True, result)
    except Exception as e:
        print(f"Error getting lab orders: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Lab Orders", False)
    
    # Test 7: Get Specific Lab Order
    if lab_order_id:
        try:
            url = f"{API_URL}/lab-orders/{lab_order_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Lab Order by ID", True, result)
        except Exception as e:
            print(f"Error getting lab order by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Lab Order by ID", False)
    
    return lab_order_id

# Test Insurance Verification
def test_insurance_verification(admin_token, patient_id):
    print("\n--- Testing Insurance Verification ---")
    
    # Test 1: Create Insurance Card
    insurance_card_id = None
    try:
        url = f"{API_URL}/insurance/cards"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "insurance_type": "commercial",
            "payer_name": "Blue Cross Blue Shield",
            "payer_id": "BCBS123",
            "member_id": "XYZ987654321",
            "group_number": "GRP12345",
            "policy_number": "POL987654",
            "subscriber_name": "Sarah Johnson",
            "subscriber_dob": "1985-06-15",
            "relationship_to_subscriber": "self",
            "effective_date": "2023-01-01",
            "copay_primary": 25.00,
            "copay_specialist": 40.00,
            "deductible": 1500.00,
            "deductible_met": 500.00,
            "out_of_pocket_max": 5000.00,
            "out_of_pocket_met": 1200.00,
            "is_primary": True
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        insurance_card_id = result["id"]
        print_test_result("Create Insurance Card", True, result)
    except Exception as e:
        print(f"Error creating insurance card: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Insurance Card", False)
    
    # Test 2: Get Patient Insurance
    try:
        url = f"{API_URL}/insurance/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Insurance", True, result)
    except Exception as e:
        print(f"Error getting patient insurance: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Insurance", False)
    
    # Test 3: Verify Eligibility
    eligibility_id = None
    if insurance_card_id:
        try:
            url = f"{API_URL}/insurance/verify-eligibility"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "insurance_card_id": insurance_card_id,
                "service_date": date.today().isoformat(),
                "service_type": "office_visit"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            eligibility_id = result["id"]
            print_test_result("Verify Eligibility", True, result)
        except Exception as e:
            print(f"Error verifying eligibility: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Verify Eligibility", False)
    else:
        print("Skipping Verify Eligibility test - no insurance card ID available")
    
    # Test 4: Get Patient Eligibility
    try:
        url = f"{API_URL}/insurance/eligibility/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Eligibility", True, result)
    except Exception as e:
        print(f"Error getting patient eligibility: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Eligibility", False)
    
    return insurance_card_id, eligibility_id

def run_all_tests():
    print("\n" + "=" * 80)
    print("TESTING CLINICHUB BACKEND API")
    print("=" * 80)
    
    # Test authentication first
    admin_token = test_authentication()
    
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
    
    # Test eRx system
    if admin_token and patient_id:
        test_erx_system(patient_id, admin_token)
    
    # Test new Scheduling and Communications systems
    if admin_token and patient_id:
        provider_id, appointment_id = test_scheduling_system(patient_id, admin_token)
        test_patient_communications(patient_id, admin_token)
        
        # Test Lab Integration and Insurance Verification
        test_lab_integration(admin_token, patient_id, provider_id)
        test_insurance_verification(admin_token, patient_id)
    
    test_dashboard_analytics()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()