#!/usr/bin/env python3
import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Helper function to format dates for JSON serialization
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Helper function to print test results
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=json_serial)[:200]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

# Test class for FHIR-Compliant Patient Management
class TestPatientManagement:
    def __init__(self):
        self.patient_id = None
    
    def test_create_patient(self):
        """Test creating a patient with FHIR-compliant data structure"""
        url = f"{API_URL}/patients"
        print(f"Making POST request to: {url}")
        
        # Create a patient with realistic healthcare data
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
        
        try:
            print(f"Request data: {json.dumps(data)}")
            response = requests.post(url, json=data)
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
            response.raise_for_status()
            result = response.json()
            
            # Verify FHIR compliance
            assert result["resource_type"] == "Patient"
            assert isinstance(result["name"], list)
            assert result["name"][0]["family"] == "Johnson"
            assert "Sarah" in result["name"][0]["given"]
            assert isinstance(result["telecom"], list)
            assert len(result["telecom"]) == 2  # Email and phone
            
            # Save patient ID for later tests
            self.patient_id = result["id"]
            
            print_test_result("Create Patient", True, result)
            return True
        except Exception as e:
            print(f"Exception: {str(e)}")
            print_test_result("Create Patient", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_patients(self):
        """Test retrieving all patients"""
        url = f"{API_URL}/patients"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got a list of patients
            assert isinstance(result, list)
            
            print_test_result("Get Patients", True, {"count": len(result), "sample": result[0] if result else None})
            return True
        except Exception as e:
            print_test_result("Get Patients", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_patient_by_id(self):
        """Test retrieving a specific patient by ID"""
        if not self.patient_id:
            print_test_result("Get Patient by ID", False, None, "No patient ID available from previous test")
            return False
        
        url = f"{API_URL}/patients/{self.patient_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got the correct patient
            assert result["id"] == self.patient_id
            
            print_test_result("Get Patient by ID", True, result)
            return True
        except Exception as e:
            print_test_result("Get Patient by ID", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

# Test class for SmartForm System
class TestSmartFormSystem:
    def __init__(self):
        self.form_id = None
        self.patient_id = None
    
    def set_patient_id(self, patient_id):
        self.patient_id = patient_id
    
    def test_create_form(self):
        """Test creating a form with drag-and-drop fields"""
        url = f"{API_URL}/forms"
        
        # Create a medical assessment form with FHIR mapping
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
                },
                {
                    "type": "textarea",
                    "label": "Medical History",
                    "placeholder": "Relevant medical history",
                    "required": False,
                    "smart_tag": "{medical_history}"
                },
                {
                    "type": "number",
                    "label": "Blood Pressure (Systolic)",
                    "required": True,
                    "smart_tag": "{bp_systolic}"
                },
                {
                    "type": "number",
                    "label": "Blood Pressure (Diastolic)",
                    "required": True,
                    "smart_tag": "{bp_diastolic}"
                }
            ],
            "status": "active",
            "fhir_mapping": {
                "chief_complaint": "Observation.code.text",
                "pain_level": "Observation.valueQuantity",
                "medical_history": "Condition.notes",
                "bp_systolic": "Observation.component[0].valueQuantity.value",
                "bp_diastolic": "Observation.component[1].valueQuantity.value"
            }
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Save form ID for later tests
            self.form_id = result["id"]
            
            print_test_result("Create Form", True, result)
            return True
        except Exception as e:
            print_test_result("Create Form", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_forms(self):
        """Test retrieving all forms"""
        url = f"{API_URL}/forms"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got a list of forms
            assert isinstance(result, list)
            
            print_test_result("Get Forms", True, {"count": len(result), "sample": result[0] if result else None})
            return True
        except Exception as e:
            print_test_result("Get Forms", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_submit_form(self):
        """Test form submission with patient linking"""
        if not self.form_id or not self.patient_id:
            print_test_result("Submit Form", False, None, "No form ID or patient ID available from previous tests")
            return False
        
        url = f"{API_URL}/forms/{self.form_id}/submit"
        
        # Form submission data
        data = {
            "chief_complaint": "Persistent headache for 3 days",
            "pain_level": "Moderate",
            "medical_history": "Patient has history of migraines, controlled with sumatriptan",
            "bp_systolic": 128,
            "bp_diastolic": 85
        }
        
        params = {"patient_id": self.patient_id}
        
        try:
            response = requests.post(url, json=data, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Verify form submission
            assert result["form_id"] == self.form_id
            assert result["patient_id"] == self.patient_id
            
            print_test_result("Submit Form", True, result)
            return True
        except Exception as e:
            print_test_result("Submit Form", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

# Test class for Invoice/Receipt Management
class TestInvoiceManagement:
    def __init__(self):
        self.invoice_id = None
        self.patient_id = None
    
    def set_patient_id(self, patient_id):
        self.patient_id = patient_id
    
    def test_create_invoice(self):
        """Test invoice creation with automatic numbering"""
        if not self.patient_id:
            print_test_result("Create Invoice", False, None, "No patient ID available from previous tests")
            return False
        
        url = f"{API_URL}/invoices"
        
        # Create an invoice with medical services
        data = {
            "patient_id": self.patient_id,
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
                },
                {
                    "description": "X-Ray - Chest",
                    "quantity": 1,
                    "unit_price": 250.00,
                    "total": 250.00
                }
            ],
            "tax_rate": 0.07,  # 7% tax
            "due_days": 30,
            "notes": "Please pay within 30 days of receipt."
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify invoice creation and automatic numbering
            assert "invoice_number" in result
            assert result["invoice_number"].startswith("INV-")
            
            # Verify tax calculations
            subtotal = sum(item["total"] for item in data["items"])
            expected_tax = subtotal * data["tax_rate"]
            expected_total = subtotal + expected_tax
            
            assert abs(result["subtotal"] - subtotal) < 0.01
            assert abs(result["tax_amount"] - expected_tax) < 0.01
            assert abs(result["total_amount"] - expected_total) < 0.01
            
            # Save invoice ID for later tests
            self.invoice_id = result["id"]
            
            print_test_result("Create Invoice", True, result)
            return True
        except Exception as e:
            print_test_result("Create Invoice", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_invoices(self):
        """Test retrieving all invoices"""
        url = f"{API_URL}/invoices"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got a list of invoices
            assert isinstance(result, list)
            
            print_test_result("Get Invoices", True, {"count": len(result), "sample": result[0] if result else None})
            return True
        except Exception as e:
            print_test_result("Get Invoices", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_invoice_by_id(self):
        """Test retrieving a specific invoice by ID"""
        if not self.invoice_id:
            print_test_result("Get Invoice by ID", False, None, "No invoice ID available from previous test")
            return False
        
        url = f"{API_URL}/invoices/{self.invoice_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got the correct invoice
            assert result["id"] == self.invoice_id
            
            print_test_result("Get Invoice by ID", True, result)
            return True
        except Exception as e:
            print_test_result("Get Invoice by ID", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

# Test class for Inventory Management
class TestInventoryManagement:
    def __init__(self):
        self.item_id = None
    
    def test_create_inventory_item(self):
        """Test medical inventory item creation"""
        url = f"{API_URL}/inventory"
        
        # Create a medical inventory item
        data = {
            "name": "Amoxicillin 500mg",
            "category": "Antibiotics",
            "sku": "MED-AMOX-500",
            "current_stock": 100,
            "min_stock_level": 20,
            "unit_cost": 1.25,
            "supplier": "MedPharm Supplies",
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),  # 1 year from now
            "location": "Pharmacy Cabinet B",
            "notes": "Keep at room temperature"
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Save item ID for later tests
            self.item_id = result["id"]
            
            print_test_result("Create Inventory Item", True, result)
            return True
        except Exception as e:
            print_test_result("Create Inventory Item", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_inventory(self):
        """Test retrieving all inventory items"""
        url = f"{API_URL}/inventory"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got a list of inventory items
            assert isinstance(result, list)
            
            print_test_result("Get Inventory", True, {"count": len(result), "sample": result[0] if result else None})
            return True
        except Exception as e:
            print_test_result("Get Inventory", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_inventory_transaction(self):
        """Test inventory transactions (in/out/adjustment)"""
        if not self.item_id:
            print_test_result("Inventory Transaction", False, None, "No item ID available from previous test")
            return False
        
        url = f"{API_URL}/inventory/{self.item_id}/transaction"
        
        # Create an "in" transaction
        data = {
            "transaction_type": "in",
            "quantity": 50,
            "notes": "Received new shipment",
            "created_by": "Dr. Smith"
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Inventory Transaction (IN)", True, result)
            
            # Create an "out" transaction
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
            
            # Create an "adjustment" transaction
            data = {
                "transaction_type": "adjustment",
                "quantity": 120,
                "notes": "Inventory count adjustment",
                "created_by": "Admin User"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Inventory Transaction (ADJUSTMENT)", True, result)
            return True
        except Exception as e:
            print_test_result("Inventory Transaction", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

# Test class for Employee Management
class TestEmployeeManagement:
    def __init__(self):
        self.employee_id = None
    
    def test_create_employee(self):
        """Test healthcare employee creation with medical roles"""
        url = f"{API_URL}/employees"
        
        # Create a healthcare employee
        data = {
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "dr.chen@clinichub.com",
            "phone": "+1-555-987-6543",
            "role": "doctor",
            "hire_date": date.today().isoformat(),
            "salary": 120000.00
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Verify employee ID generation
            assert "employee_id" in result
            assert result["employee_id"].startswith("EMP-")
            
            # Save database ID for later tests
            self.employee_id = result["id"]
            
            print_test_result("Create Employee", True, result)
            return True
        except Exception as e:
            print_test_result("Create Employee", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False
    
    def test_get_employees(self):
        """Test retrieving all employees"""
        url = f"{API_URL}/employees"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            # Verify we got a list of employees
            assert isinstance(result, list)
            
            print_test_result("Get Employees", True, {"count": len(result), "sample": result[0] if result else None})
            return True
        except Exception as e:
            print_test_result("Get Employees", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

# Test class for Dashboard Analytics
class TestDashboardAnalytics:
    def test_dashboard_stats(self):
        """Test dashboard statistics API"""
        url = f"{API_URL}/dashboard/stats"
        
        try:
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
            
            # Verify recent activity
            assert "recent_patients" in result
            assert "recent_invoices" in result
            
            print_test_result("Dashboard Stats", True, result)
            return True
        except Exception as e:
            print_test_result("Dashboard Stats", False, response.json() if hasattr(response, 'json') else None, str(e))
            return False

def run_all_tests():
    print("\n" + "=" * 80)
    print("TESTING CLINICHUB BACKEND API")
    print("=" * 80)
    
    # Test Patient Management
    print("\n--- Testing FHIR-Compliant Patient Management ---")
    patient_tests = TestPatientManagement()
    patient_tests.test_create_patient()
    patient_tests.test_get_patients()
    patient_tests.test_get_patient_by_id()
    
    # Test SmartForm System
    print("\n--- Testing SmartForm System ---")
    form_tests = TestSmartFormSystem()
    if patient_tests.patient_id:
        form_tests.set_patient_id(patient_tests.patient_id)
    form_tests.test_create_form()
    form_tests.test_get_forms()
    form_tests.test_submit_form()
    
    # Test Invoice Management
    print("\n--- Testing Invoice/Receipt Management ---")
    invoice_tests = TestInvoiceManagement()
    if patient_tests.patient_id:
        invoice_tests.set_patient_id(patient_tests.patient_id)
    invoice_tests.test_create_invoice()
    invoice_tests.test_get_invoices()
    invoice_tests.test_get_invoice_by_id()
    
    # Test Inventory Management
    print("\n--- Testing Inventory Management ---")
    inventory_tests = TestInventoryManagement()
    inventory_tests.test_create_inventory_item()
    inventory_tests.test_get_inventory()
    inventory_tests.test_inventory_transaction()
    
    # Test Employee Management
    print("\n--- Testing Employee Management ---")
    employee_tests = TestEmployeeManagement()
    employee_tests.test_create_employee()
    employee_tests.test_get_employees()
    
    # Test Dashboard Analytics
    print("\n--- Testing Dashboard Analytics ---")
    dashboard_tests = TestDashboardAnalytics()
    dashboard_tests.test_dashboard_stats()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()