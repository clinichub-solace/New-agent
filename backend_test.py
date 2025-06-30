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
    test_dashboard_analytics()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()