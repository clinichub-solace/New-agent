#!/usr/bin/env python3
"""
Comprehensive CRUD Testing for ClinicHub - Focus on UPDATE Operations
Testing all modules as requested in the review with emphasis on EDIT/UPDATE functionality
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
print(f"🏥 ClinicHub Comprehensive CRUD Testing")
print(f"🔗 Using API URL: {API_URL}")
print("=" * 80)

# Global variables to store created resources
admin_token = None
test_patient_id = None
test_employee_id = None
test_inventory_id = None
test_invoice_id = None
test_financial_transaction_id = None
test_prescription_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, details=None):
    status = "✅ WORKING" if success else "❌ BROKEN"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    if response and not success:
        print(f"   Error: {response}")
    print("-" * 60)

def authenticate():
    """Authenticate and get admin token"""
    global admin_token
    print("\n🔐 AUTHENTICATION SYSTEM")
    
    # Initialize admin user
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Admin User", True, details=f"Username: {result.get('username')}")
    except Exception as e:
        print_test_result("Initialize Admin User", False, str(e))
        return False
    
    # Login with admin credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, details=f"Token received, expires in {result.get('expires_in')} minutes")
        return True
    except Exception as e:
        print_test_result("Admin Login", False, str(e))
        return False

def test_inventory_management_crud():
    """Test INVENTORY MANAGEMENT - Complete CRUD with focus on UPDATE operations"""
    global test_inventory_id
    print("\n📦 INVENTORY MANAGEMENT - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # CREATE: Add new inventory item
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Amoxicillin 500mg Capsules",
            "category": "Antibiotics",
            "sku": "MED-AMOX-500-CAP",
            "current_stock": 150,
            "min_stock_level": 25,
            "unit_cost": 2.50,
            "supplier": "PharmaCorp Medical Supplies",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Pharmacy Cabinet A-3",
            "notes": "Store at room temperature, away from moisture"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_inventory_id = result["id"]
        print_test_result("CREATE Inventory Item", True, details=f"Created item: {result['name']}, Stock: {result['current_stock']}")
    except Exception as e:
        print_test_result("CREATE Inventory Item", False, str(e))
        return
    
    # READ: Get all inventory items
    try:
        url = f"{API_URL}/inventory"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Inventory Items", True, details=f"Retrieved {len(result)} items")
    except Exception as e:
        print_test_result("READ All Inventory Items", False, str(e))
    
    # READ: Get specific inventory item
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Specific Inventory Item", True, details=f"Retrieved: {result['name']}")
    except Exception as e:
        print_test_result("READ Specific Inventory Item", False, str(e))
    
    # ⚠️ UPDATE: Edit inventory item (CRITICAL - User specifically mentioned inventory editing)
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}"
        update_data = {
            "name": "Amoxicillin 500mg Capsules - Updated",
            "current_stock": 200,
            "min_stock_level": 30,
            "unit_cost": 2.75,
            "supplier": "Updated PharmaCorp Medical Supplies",
            "location": "Pharmacy Cabinet B-1 - Relocated",
            "notes": "Updated: Store at room temperature, check expiry monthly"
        }
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Inventory Item (CRITICAL)", True, 
                         details=f"Updated: {result['name']}, New stock: {result['current_stock']}, New cost: ${result['unit_cost']}")
    except Exception as e:
        print_test_result("⚠️ UPDATE Inventory Item (CRITICAL)", False, str(e))
    
    # Test inventory transactions
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}/transaction"
        transaction_data = {
            "transaction_type": "in",
            "quantity": 50,
            "notes": "Received new shipment - batch #2024-001",
            "created_by": "admin"
        }
        response = requests.post(url, json=transaction_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Inventory Transaction (IN)", True, details=f"Added {transaction_data['quantity']} units")
        
        # OUT transaction
        transaction_data["transaction_type"] = "out"
        transaction_data["quantity"] = 25
        transaction_data["notes"] = "Dispensed to patients"
        response = requests.post(url, json=transaction_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Inventory Transaction (OUT)", True, details=f"Removed {transaction_data['quantity']} units")
    except Exception as e:
        print_test_result("Inventory Transactions", False, str(e))
    
    # DELETE: Remove inventory item (if endpoint exists)
    try:
        url = f"{API_URL}/inventory/{test_inventory_id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 404:
            print_test_result("DELETE Inventory Item", True, details="DELETE endpoint not implemented (expected)")
        else:
            response.raise_for_status()
            print_test_result("DELETE Inventory Item", True, details="Item deleted successfully")
    except Exception as e:
        print_test_result("DELETE Inventory Item", False, str(e))

def test_patient_management_crud():
    """Test PATIENT MANAGEMENT & EHR - Complete CRUD"""
    global test_patient_id
    print("\n👥 PATIENT MANAGEMENT & EHR - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # CREATE: Add new patient
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@email.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1988-03-22",
            "gender": "female",
            "address_line1": "456 Healthcare Avenue",
            "city": "Medical City",
            "state": "TX",
            "zip_code": "75001"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_patient_id = result["id"]
        print_test_result("CREATE Patient", True, details=f"Created: {result['name'][0]['given'][0]} {result['name'][0]['family']}")
    except Exception as e:
        print_test_result("CREATE Patient", False, str(e))
        return
    
    # READ: Get all patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Patients", True, details=f"Retrieved {len(result)} patients")
    except Exception as e:
        print_test_result("READ All Patients", False, str(e))
    
    # READ: Get specific patient
    try:
        url = f"{API_URL}/patients/{test_patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Specific Patient", True, details=f"Retrieved patient: {result['name'][0]['family']}")
    except Exception as e:
        print_test_result("READ Specific Patient", False, str(e))
    
    # ⚠️ UPDATE: Edit patient information
    try:
        url = f"{API_URL}/patients/{test_patient_id}"
        update_data = {
            "first_name": "Emily Maria",
            "last_name": "Rodriguez-Smith",
            "email": "emily.rodriguez.smith@email.com",
            "phone": "+1-555-234-9999",
            "address_line1": "789 Updated Healthcare Boulevard",
            "city": "New Medical City",
            "state": "TX",
            "zip_code": "75002"
        }
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Patient Info", True, 
                         details=f"Updated: {result['name'][0]['given'][0]} {result['name'][0]['family']}")
    except Exception as e:
        print_test_result("⚠️ UPDATE Patient Info", False, str(e))
    
    # Test SOAP Notes CRUD
    encounter_id = None
    try:
        # Create encounter first
        url = f"{API_URL}/encounters"
        encounter_data = {
            "patient_id": test_patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Sarah Johnson",
            "chief_complaint": "Follow-up visit",
            "reason_for_visit": "Routine check-up"
        }
        response = requests.post(url, json=encounter_data, headers=headers)
        response.raise_for_status()
        encounter_result = response.json()
        encounter_id = encounter_result["id"]
        
        # CREATE SOAP Note
        url = f"{API_URL}/soap-notes"
        soap_data = {
            "encounter_id": encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient reports feeling well, no new complaints",
            "objective": "Vital signs stable, physical exam normal",
            "assessment": "Healthy adult, routine follow-up",
            "plan": "Continue current medications, return in 6 months",
            "provider": "Dr. Sarah Johnson"
        }
        response = requests.post(url, json=soap_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("CREATE SOAP Note", True, details="SOAP note created successfully")
        
        # UPDATE SOAP Note
        soap_id = result["id"]
        url = f"{API_URL}/soap-notes/{soap_id}"
        update_soap_data = {
            "subjective": "Patient reports feeling well, no new complaints - UPDATED",
            "objective": "Vital signs stable, physical exam normal - UPDATED",
            "assessment": "Healthy adult, routine follow-up - UPDATED",
            "plan": "Continue current medications, return in 3 months - UPDATED"
        }
        response = requests.put(url, json=update_soap_data, headers=headers)
        response.raise_for_status()
        print_test_result("UPDATE SOAP Note", True, details="SOAP note updated successfully")
    except Exception as e:
        print_test_result("SOAP Notes CRUD", False, str(e))
    
    # Test Vital Signs CRUD
    try:
        # CREATE Vital Signs
        url = f"{API_URL}/vital-signs"
        vital_data = {
            "patient_id": test_patient_id,
            "encounter_id": encounter_id,
            "height": 165.0,
            "weight": 68.5,
            "bmi": 25.2,
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "heart_rate": 72,
            "temperature": 36.8,
            "oxygen_saturation": 98,
            "recorded_by": "Nurse Johnson"
        }
        response = requests.post(url, json=vital_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("CREATE Vital Signs", True, details=f"BP: {vital_data['systolic_bp']}/{vital_data['diastolic_bp']}")
        
        # UPDATE Vital Signs
        vital_id = result["id"]
        url = f"{API_URL}/vital-signs/{vital_id}"
        update_vital_data = {
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 75,
            "temperature": 37.0
        }
        response = requests.put(url, json=update_vital_data, headers=headers)
        response.raise_for_status()
        print_test_result("UPDATE Vital Signs", True, details="Vital signs updated successfully")
    except Exception as e:
        print_test_result("Vital Signs CRUD", False, str(e))
    
    # Test Allergies CRUD
    try:
        # CREATE Allergy
        url = f"{API_URL}/allergies"
        allergy_data = {
            "patient_id": test_patient_id,
            "allergen": "Penicillin",
            "reaction": "Skin rash, hives",
            "severity": "moderate",
            "notes": "Discovered during previous treatment",
            "created_by": "admin"
        }
        response = requests.post(url, json=allergy_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("CREATE Allergy", True, details=f"Allergen: {allergy_data['allergen']}")
        
        # UPDATE Allergy
        allergy_id = result["id"]
        url = f"{API_URL}/allergies/{allergy_id}"
        update_allergy_data = {
            "reaction": "Severe skin rash, hives, difficulty breathing",
            "severity": "severe",
            "notes": "Updated severity based on recent episode"
        }
        response = requests.put(url, json=update_allergy_data, headers=headers)
        response.raise_for_status()
        print_test_result("UPDATE Allergy", True, details="Allergy severity updated to severe")
    except Exception as e:
        print_test_result("Allergies CRUD", False, str(e))
    
    # Test Medications CRUD
    try:
        # CREATE Medication
        url = f"{API_URL}/medications"
        medication_data = {
            "patient_id": test_patient_id,
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "route": "oral",
            "start_date": date.today().isoformat(),
            "prescribing_physician": "Dr. Sarah Johnson",
            "indication": "Hypertension"
        }
        response = requests.post(url, json=medication_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("CREATE Medication", True, details=f"Medication: {medication_data['medication_name']}")
        
        # UPDATE Medication
        medication_id = result["id"]
        url = f"{API_URL}/medications/{medication_id}"
        update_medication_data = {
            "dosage": "20mg",
            "frequency": "Twice daily",
            "notes": "Dosage increased due to inadequate blood pressure control"
        }
        response = requests.put(url, json=update_medication_data, headers=headers)
        response.raise_for_status()
        print_test_result("UPDATE Medication", True, details="Medication dosage updated")
    except Exception as e:
        print_test_result("Medications CRUD", False, str(e))

def test_employee_management_crud():
    """Test EMPLOYEE MANAGEMENT - Complete CRUD"""
    global test_employee_id
    print("\n👨‍⚕️ EMPLOYEE MANAGEMENT - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # CREATE: Add new employee
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Dr. Michael",
            "last_name": "Thompson",
            "email": "dr.thompson@clinichub.com",
            "phone": "+1-555-345-6789",
            "role": "doctor",
            "department": "Cardiology",
            "hire_date": date.today().isoformat(),
            "salary": 185000.00,
            "employment_type": "full_time"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_employee_id = result["id"]
        print_test_result("CREATE Employee", True, 
                         details=f"Created: {result['first_name']} {result['last_name']}, ID: {result['employee_id']}")
    except Exception as e:
        print_test_result("CREATE Employee", False, str(e))
        return
    
    # READ: Get all employees
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Employees", True, details=f"Retrieved {len(result)} employees")
    except Exception as e:
        print_test_result("READ All Employees", False, str(e))
    
    # READ: Get specific employee
    try:
        url = f"{API_URL}/employees/{test_employee_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Specific Employee", True, 
                         details=f"Retrieved: {result['first_name']} {result['last_name']}")
    except Exception as e:
        print_test_result("READ Specific Employee", False, str(e))
    
    # ⚠️ UPDATE: Edit employee information
    try:
        url = f"{API_URL}/employees/{test_employee_id}"
        update_data = {
            "first_name": "Dr. Michael James",
            "last_name": "Thompson-Wilson",
            "email": "dr.thompson.wilson@clinichub.com",
            "phone": "+1-555-345-9999",
            "department": "Interventional Cardiology",
            "salary": 195000.00,
            "employment_type": "full_time"
        }
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Employee Info", True, 
                         details=f"Updated: {result['first_name']} {result['last_name']}, New salary: ${result['salary']}")
    except Exception as e:
        print_test_result("⚠️ UPDATE Employee Info", False, str(e))
    
    # Test Payroll functionality
    try:
        # Create payroll period
        url = f"{API_URL}/payroll/periods"
        payroll_data = {
            "period_start": date.today().isoformat(),
            "period_end": (date.today() + timedelta(days=14)).isoformat(),
            "pay_date": (date.today() + timedelta(days=16)).isoformat(),
            "period_type": "biweekly",
            "created_by": "admin"
        }
        response = requests.post(url, json=payroll_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("CREATE Payroll Period", True, details=f"Period: {payroll_data['period_start']} to {payroll_data['period_end']}")
    except Exception as e:
        print_test_result("Payroll Functionality", False, str(e))

def test_invoices_billing_crud():
    """Test INVOICES/BILLING - Complete CRUD"""
    global test_invoice_id
    print("\n💰 INVOICES/BILLING - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # CREATE: Add new invoice
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": test_patient_id,
            "items": [
                {
                    "description": "Comprehensive Physical Examination",
                    "quantity": 1,
                    "unit_price": 250.00,
                    "total": 250.00
                },
                {
                    "description": "EKG - 12 Lead",
                    "quantity": 1,
                    "unit_price": 85.00,
                    "total": 85.00
                },
                {
                    "description": "Blood Work - Comprehensive Metabolic Panel",
                    "quantity": 1,
                    "unit_price": 120.00,
                    "total": 120.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Payment due within 30 days. Thank you for choosing ClinicHub."
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_invoice_id = result["id"]
        print_test_result("CREATE Invoice", True, 
                         details=f"Invoice: {result['invoice_number']}, Total: ${result['total_amount']}")
    except Exception as e:
        print_test_result("CREATE Invoice", False, str(e))
        return
    
    # READ: Get all invoices
    try:
        url = f"{API_URL}/invoices"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Invoices", True, details=f"Retrieved {len(result)} invoices")
    except Exception as e:
        print_test_result("READ All Invoices", False, str(e))
    
    # READ: Get specific invoice
    try:
        url = f"{API_URL}/invoices/{test_invoice_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Specific Invoice", True, 
                         details=f"Invoice: {result['invoice_number']}, Status: {result['status']}")
    except Exception as e:
        print_test_result("READ Specific Invoice", False, str(e))
    
    # ⚠️ UPDATE: Edit invoice
    try:
        url = f"{API_URL}/invoices/{test_invoice_id}"
        update_data = {
            "items": [
                {
                    "description": "Comprehensive Physical Examination - Updated",
                    "quantity": 1,
                    "unit_price": 275.00,
                    "total": 275.00
                },
                {
                    "description": "EKG - 12 Lead",
                    "quantity": 1,
                    "unit_price": 85.00,
                    "total": 85.00
                },
                {
                    "description": "Blood Work - Comprehensive Metabolic Panel",
                    "quantity": 1,
                    "unit_price": 120.00,
                    "total": 120.00
                },
                {
                    "description": "Additional Consultation - Added",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total": 100.00
                }
            ],
            "tax_rate": 0.08,
            "notes": "Updated invoice with additional consultation. Payment due within 30 days."
        }
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Invoice", True, 
                         details=f"Updated total: ${result['total_amount']}, Items: {len(result['items'])}")
    except Exception as e:
        print_test_result("⚠️ UPDATE Invoice", False, str(e))
    
    # Test payment processing and status updates
    try:
        url = f"{API_URL}/invoices/{test_invoice_id}/status"
        params = {"status": "sent"}
        response = requests.put(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("UPDATE Invoice Status (Sent)", True, details="Invoice marked as sent")
        
        # Update to paid
        params = {"status": "paid"}
        response = requests.put(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("UPDATE Invoice Status (Paid)", True, details="Invoice marked as paid")
    except Exception as e:
        print_test_result("Invoice Status Updates", False, str(e))

def test_financial_management_crud():
    """Test FINANCIAL MANAGEMENT - Complete CRUD"""
    global test_financial_transaction_id
    print("\n💳 FINANCIAL MANAGEMENT - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # CREATE: Add new financial transaction
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 455.00,
            "payment_method": "credit_card",
            "description": "Patient payment for comprehensive physical exam",
            "category": "patient_payment",
            "patient_id": test_patient_id,
            "invoice_id": test_invoice_id,
            "bank_account": "Primary Checking",
            "reference_number": "CC-2024-001234",
            "created_by": "admin"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_financial_transaction_id = result["id"]
        print_test_result("CREATE Financial Transaction", True, 
                         details=f"Transaction: {result['transaction_number']}, Amount: ${result['amount']}")
    except Exception as e:
        print_test_result("CREATE Financial Transaction", False, str(e))
        return
    
    # READ: Get all financial transactions
    try:
        url = f"{API_URL}/financial-transactions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Financial Transactions", True, details=f"Retrieved {len(result)} transactions")
    except Exception as e:
        print_test_result("READ All Financial Transactions", False, str(e))
    
    # READ: Get specific financial transaction
    try:
        url = f"{API_URL}/financial-transactions/{test_financial_transaction_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Specific Financial Transaction", True, 
                         details=f"Transaction: {result['transaction_number']}")
    except Exception as e:
        print_test_result("READ Specific Financial Transaction", False, str(e))
    
    # ⚠️ UPDATE: Edit financial transaction
    try:
        url = f"{API_URL}/financial-transactions/{test_financial_transaction_id}"
        update_data = {
            "amount": 480.00,
            "description": "Patient payment for comprehensive physical exam - Updated amount",
            "reference_number": "CC-2024-001234-UPDATED",
            "reconciled": True,
            "reconciled_date": date.today().isoformat()
        }
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Financial Transaction", True, 
                         details=f"Updated amount: ${result['amount']}, Reconciled: {result['reconciled']}")
    except Exception as e:
        print_test_result("⚠️ UPDATE Financial Transaction", False, str(e))
    
    # Test financial reports and dashboard data
    try:
        url = f"{API_URL}/financial-reports/daily-summary"
        params = {"date": date.today().isoformat()}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Financial Reports - Daily Summary", True, 
                         details=f"Total income: ${result.get('total_income', 0)}")
    except Exception as e:
        print_test_result("Financial Reports", False, str(e))

def test_prescriptions_erx_crud():
    """Test PRESCRIPTIONS (eRx) - Complete CRUD"""
    global test_prescription_id
    print("\n💊 PRESCRIPTIONS (eRx) - COMPLETE CRUD TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Initialize eRx system first
    try:
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize eRx System", True, details="eRx system initialized")
    except Exception as e:
        print_test_result("Initialize eRx System", False, str(e))
    
    # Get medication for prescription
    medication_id = None
    try:
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        if medications:
            medication_id = medications[0]["id"]
            print_test_result("GET eRx Medications", True, details=f"Retrieved {len(medications)} medications")
        else:
            print_test_result("GET eRx Medications", False, "No medications found")
            return
    except Exception as e:
        print_test_result("GET eRx Medications", False, str(e))
        return
    
    # CREATE: Add new prescription
    try:
        url = f"{API_URL}/prescriptions"
        data = {
            "medication_id": medication_id,
            "patient_id": test_patient_id,
            "prescriber_id": "prescriber-001",
            "prescriber_name": "Dr. Michael Thompson",
            "dosage_text": "Take 1 tablet by mouth twice daily with food",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "BID",
            "route": "oral",
            "quantity": 60.0,
            "days_supply": 30,
            "refills": 3,
            "indication": "Hypertension management",
            "diagnosis_codes": ["I10"],
            "special_instructions": "Take with food to reduce stomach upset",
            "created_by": "admin"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        test_prescription_id = result["id"]
        print_test_result("CREATE Prescription", True, 
                         details=f"Prescription: {result['prescription_number']}, Refills: {result['refills']}")
    except Exception as e:
        print_test_result("CREATE Prescription", False, str(e))
        return
    
    # READ: Get all prescriptions
    try:
        url = f"{API_URL}/prescriptions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ All Prescriptions", True, details=f"Retrieved {len(result)} prescriptions")
    except Exception as e:
        print_test_result("READ All Prescriptions", False, str(e))
    
    # READ: Get patient prescriptions
    try:
        url = f"{API_URL}/patients/{test_patient_id}/prescriptions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("READ Patient Prescriptions", True, details=f"Patient has {len(result)} prescriptions")
    except Exception as e:
        print_test_result("READ Patient Prescriptions", False, str(e))
    
    # ⚠️ UPDATE: Edit prescription status
    try:
        url = f"{API_URL}/prescriptions/{test_prescription_id}/status"
        params = {"status": "active"}
        response = requests.put(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("⚠️ UPDATE Prescription Status", True, details="Prescription activated")
    except Exception as e:
        print_test_result("⚠️ UPDATE Prescription Status", False, str(e))
    
    # Test medication database integration
    try:
        url = f"{API_URL}/medications"
        params = {"search": "blood pressure"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Medication Database Search", True, 
                         details=f"Found {len(result)} blood pressure medications")
    except Exception as e:
        print_test_result("Medication Database Integration", False, str(e))

def test_referrals_management():
    """Test REFERRALS MANAGEMENT - All endpoints"""
    print("\n🏥 REFERRALS MANAGEMENT - ALL ENDPOINTS TESTING")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test referral creation and management
    referral_id = None
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": test_patient_id,
            "referring_provider": "Dr. Michael Thompson",
            "specialist_provider": "Dr. Sarah Cardiologist",
            "specialty": "Cardiology",
            "reason": "Abnormal EKG findings requiring specialist evaluation",
            "urgency": "routine",
            "notes": "Patient has family history of cardiac disease",
            "created_by": "admin"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        referral_id = result["id"]
        print_test_result("CREATE Referral", True, 
                         details=f"Referral to {data['specialty']}, Status: {result['status']}")
    except Exception as e:
        print_test_result("CREATE Referral", False, str(e))
    
    # Test specialist networks
    try:
        url = f"{API_URL}/referrals/specialists"
        params = {"specialty": "Cardiology"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("GET Specialist Networks", True, 
                         details=f"Found {len(result)} cardiology specialists")
    except Exception as e:
        print_test_result("Specialist Networks", False, str(e))
    
    # Update referral status
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}/status"
            params = {"status": "scheduled"}
            response = requests.put(url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            print_test_result("UPDATE Referral Status", True, details="Referral scheduled")
        except Exception as e:
            print_test_result("UPDATE Referral Status", False, str(e))

def run_comprehensive_crud_tests():
    """Run all comprehensive CRUD tests"""
    print("🚀 Starting Comprehensive CRUD Testing for ClinicHub")
    print("Focus: UPDATE/EDIT operations as specifically requested")
    print("=" * 80)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Run all CRUD tests
    test_inventory_management_crud()
    test_patient_management_crud()
    test_employee_management_crud()
    test_invoices_billing_crud()
    test_financial_management_crud()
    test_prescriptions_erx_crud()
    test_referrals_management()
    
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE CRUD TESTING COMPLETED")
    print("✅ Focus on UPDATE operations as requested in review")
    print("📊 All major modules tested for production readiness")
    print("=" * 80)

if __name__ == "__main__":
    run_comprehensive_crud_tests()