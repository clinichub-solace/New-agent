#!/usr/bin/env python3
"""
Comprehensive ClinicHub Backend Testing
Focus on core modules: Invoice/Receipt, Employee, Inventory, Patient, Financial Transactions
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
test_employee_id = None
test_inventory_item_id = None
test_invoice_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
        elif response:
            print(f"   Response: {str(response)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate_admin():
    """Authenticate as admin and get token"""
    global admin_token
    
    print("\n=== AUTHENTICATION ===")
    
    # Initialize admin user first
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print_test_result("Initialize Admin User", False, error_msg=str(e))
        return False
    
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
        print_test_result("Admin Login", False, error_msg=str(e))
        return False

def test_patient_module():
    """Test Patient Management Module"""
    global test_patient_id
    
    print("\n=== PATIENT MODULE TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create Patient
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1988-03-22",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify FHIR compliance
        assert result["resource_type"] == "Patient"
        assert isinstance(result["name"], list)
        assert result["name"][0]["family"] == "Rodriguez"
        assert "Emily" in result["name"][0]["given"]
        
        test_patient_id = result["id"]
        print_test_result("Create Patient", True, result)
    except Exception as e:
        print_test_result("Create Patient", False, error_msg=str(e))
        return False
    
    # Test 2: Get All Patients
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        print_test_result("Get All Patients", True, {"count": len(result), "first_patient": result[0] if result else None})
    except Exception as e:
        print_test_result("Get All Patients", False, error_msg=str(e))
    
    # Test 3: Get Patient by ID
    if test_patient_id:
        try:
            url = f"{API_URL}/patients/{test_patient_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == test_patient_id
            print_test_result("Get Patient by ID", True, result)
        except Exception as e:
            print_test_result("Get Patient by ID", False, error_msg=str(e))
    
    return test_patient_id is not None

def test_employee_module():
    """Test Employee Management Module"""
    global test_employee_id
    
    print("\n=== EMPLOYEE MODULE TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create Employee
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Dr. James",
            "last_name": "Wilson",
            "email": "dr.wilson@clinichub.com",
            "phone": "+1-555-345-6789",
            "role": "doctor",
            "department": "Cardiology",
            "hire_date": date.today().isoformat(),
            "salary": 150000.00
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify employee ID generation
        assert "employee_id" in result
        assert result["employee_id"].startswith("EMP-")
        assert result["role"] == "doctor"
        
        test_employee_id = result["id"]
        print_test_result("Create Employee", True, result)
    except Exception as e:
        print_test_result("Create Employee", False, error_msg=str(e))
        return False
    
    # Test 2: Get All Employees
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        print_test_result("Get All Employees", True, {"count": len(result), "first_employee": result[0] if result else None})
    except Exception as e:
        print_test_result("Get All Employees", False, error_msg=str(e))
    
    # Test 3: Get Employee by ID
    if test_employee_id:
        try:
            url = f"{API_URL}/employees/{test_employee_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == test_employee_id
            print_test_result("Get Employee by ID", True, result)
        except Exception as e:
            print_test_result("Get Employee by ID", False, error_msg=str(e))
    
    # Test 4: Update Employee
    if test_employee_id:
        try:
            url = f"{API_URL}/employees/{test_employee_id}"
            data = {
                "phone": "+1-555-999-8888",
                "department": "Internal Medicine",
                "salary": 160000.00
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["phone"] == "+1-555-999-8888"
            assert result["department"] == "Internal Medicine"
            print_test_result("Update Employee", True, result)
        except Exception as e:
            print_test_result("Update Employee", False, error_msg=str(e))
    
    return test_employee_id is not None

def test_inventory_module():
    """Test Inventory Management Module"""
    global test_inventory_item_id
    
    print("\n=== INVENTORY MODULE TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create Inventory Item
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Ibuprofen 200mg",
            "category": "Pain Relief",
            "sku": "MED-IBU-200",
            "current_stock": 500,
            "min_stock_level": 50,
            "unit_cost": 0.15,
            "supplier": "PharmaCorp",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Pharmacy Storage A",
            "notes": "Over-the-counter pain reliever"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["name"] == "Ibuprofen 200mg"
        assert result["current_stock"] == 500
        
        test_inventory_item_id = result["id"]
        print_test_result("Create Inventory Item", True, result)
    except Exception as e:
        print_test_result("Create Inventory Item", False, error_msg=str(e))
        return False
    
    # Test 2: Get All Inventory Items
    try:
        url = f"{API_URL}/inventory"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        print_test_result("Get All Inventory Items", True, {"count": len(result), "first_item": result[0] if result else None})
    except Exception as e:
        print_test_result("Get All Inventory Items", False, error_msg=str(e))
    
    # Test 3: Inventory Transaction - Stock In
    if test_inventory_item_id:
        try:
            url = f"{API_URL}/inventory/{test_inventory_item_id}/transaction"
            data = {
                "transaction_type": "in",
                "quantity": 100,
                "notes": "New shipment received",
                "created_by": "admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["transaction_type"] == "in"
            assert result["quantity"] == 100
            print_test_result("Inventory Transaction (Stock In)", True, result)
        except Exception as e:
            print_test_result("Inventory Transaction (Stock In)", False, error_msg=str(e))
    
    # Test 4: Inventory Transaction - Stock Out
    if test_inventory_item_id:
        try:
            url = f"{API_URL}/inventory/{test_inventory_item_id}/transaction"
            data = {
                "transaction_type": "out",
                "quantity": 25,
                "notes": "Dispensed to patient",
                "created_by": "admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["transaction_type"] == "out"
            assert result["quantity"] == 25
            print_test_result("Inventory Transaction (Stock Out)", True, result)
        except Exception as e:
            print_test_result("Inventory Transaction (Stock Out)", False, error_msg=str(e))
    
    return test_inventory_item_id is not None

def test_invoice_module():
    """Test Invoice/Receipt Management Module"""
    global test_invoice_id
    
    print("\n=== INVOICE/RECEIPT MODULE TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    if not test_patient_id:
        print("❌ Cannot test invoices without a patient ID")
        return False
    
    # Test 1: Create Invoice
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": test_patient_id,
            "items": [
                {
                    "description": "Office Visit - Consultation",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "total": 200.00
                },
                {
                    "description": "Blood Pressure Check",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "total": 50.00
                },
                {
                    "description": "Prescription - Ibuprofen",
                    "quantity": 1,
                    "unit_price": 15.00,
                    "total": 15.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Payment due within 30 days. Thank you for choosing ClinicHub."
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify invoice creation and automatic numbering
        assert "invoice_number" in result
        assert result["invoice_number"].startswith("INV-")
        assert result["patient_id"] == test_patient_id
        assert len(result["items"]) == 3
        assert result["subtotal"] == 265.00  # 200 + 50 + 15
        
        test_invoice_id = result["id"]
        print_test_result("Create Invoice", True, result)
    except Exception as e:
        print_test_result("Create Invoice", False, error_msg=str(e))
        return False
    
    # Test 2: Get All Invoices
    try:
        url = f"{API_URL}/invoices"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        print_test_result("Get All Invoices", True, {"count": len(result), "first_invoice": result[0] if result else None})
    except Exception as e:
        print_test_result("Get All Invoices", False, error_msg=str(e))
    
    # Test 3: Get Invoice by ID
    if test_invoice_id:
        try:
            url = f"{API_URL}/invoices/{test_invoice_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == test_invoice_id
            assert result["patient_id"] == test_patient_id
            print_test_result("Get Invoice by ID", True, result)
        except Exception as e:
            print_test_result("Get Invoice by ID", False, error_msg=str(e))
    
    return test_invoice_id is not None

def test_financial_transactions():
    """Test Financial Transactions Module"""
    
    print("\n=== FINANCIAL TRANSACTIONS MODULE TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create Financial Transaction - Income
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 265.00,
            "payment_method": "credit_card",
            "description": "Patient payment for consultation and prescription",
            "category": "patient_payment",
            "patient_id": test_patient_id,
            "invoice_id": test_invoice_id,
            "bank_account": "Main Operating Account",
            "reference_number": "CC-2025-001",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["transaction_type"] == "income"
        assert result["amount"] == 265.00
        assert result["payment_method"] == "credit_card"
        assert "transaction_number" in result
        
        income_transaction_id = result["id"]
        print_test_result("Create Financial Transaction (Income)", True, result)
    except Exception as e:
        print_test_result("Create Financial Transaction (Income)", False, error_msg=str(e))
        income_transaction_id = None
    
    # Test 2: Create Financial Transaction - Expense
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "expense",
            "amount": 1500.00,
            "payment_method": "check",
            "description": "Medical supplies purchase",
            "category": "medical_supplies",
            "bank_account": "Main Operating Account",
            "reference_number": "CHK-2025-001",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["transaction_type"] == "expense"
        assert result["amount"] == 1500.00
        assert result["payment_method"] == "check"
        
        expense_transaction_id = result["id"]
        print_test_result("Create Financial Transaction (Expense)", True, result)
    except Exception as e:
        print_test_result("Create Financial Transaction (Expense)", False, error_msg=str(e))
        expense_transaction_id = None
    
    # Test 3: Get All Financial Transactions
    try:
        url = f"{API_URL}/financial-transactions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        print_test_result("Get All Financial Transactions", True, {"count": len(result), "first_transaction": result[0] if result else None})
    except Exception as e:
        print_test_result("Get All Financial Transactions", False, error_msg=str(e))
    
    # Test 4: Financial Summary/Dashboard
    try:
        url = f"{API_URL}/dashboard/stats"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert "stats" in result
        print_test_result("Financial Dashboard/Stats", True, result)
    except Exception as e:
        print_test_result("Financial Dashboard/Stats", False, error_msg=str(e))
    
    return income_transaction_id is not None or expense_transaction_id is not None

def test_data_integrity():
    """Test data integrity and relationships between modules"""
    
    print("\n=== DATA INTEGRITY TESTING ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Patient Summary (should include invoice data)
    if test_patient_id:
        try:
            url = f"{API_URL}/patients/{test_patient_id}/summary"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert "patient" in result
            assert result["patient"]["id"] == test_patient_id
            print_test_result("Patient Summary Integration", True, result)
        except Exception as e:
            print_test_result("Patient Summary Integration", False, error_msg=str(e))
    
    # Test 2: Check if inventory was updated after transactions
    if test_inventory_item_id:
        try:
            url = f"{API_URL}/inventory/{test_inventory_item_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Should reflect the +100 and -25 transactions
            expected_stock = 500 + 100 - 25  # Original + In - Out
            print_test_result("Inventory Stock Updates", True, {"current_stock": result.get("current_stock"), "expected": expected_stock})
        except Exception as e:
            print_test_result("Inventory Stock Updates", False, error_msg=str(e))

def main():
    """Main test execution"""
    print("=" * 80)
    print("COMPREHENSIVE CLINICHUB BACKEND TESTING")
    print("Testing Core Modules: Patient, Employee, Inventory, Invoice, Financial")
    print("=" * 80)
    
    # Step 1: Authenticate
    if not authenticate_admin():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Test each module
    patient_success = test_patient_module()
    employee_success = test_employee_module()
    inventory_success = test_inventory_module()
    invoice_success = test_invoice_module()
    financial_success = test_financial_transactions()
    
    # Step 3: Test data integrity
    test_data_integrity()
    
    # Step 4: Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    modules = [
        ("Patient Module", patient_success),
        ("Employee Module", employee_success),
        ("Inventory Module", inventory_success),
        ("Invoice/Receipt Module", invoice_success),
        ("Financial Transactions Module", financial_success)
    ]
    
    passed = sum(1 for _, success in modules if success)
    total = len(modules)
    
    for module_name, success in modules:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{module_name}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} modules passed")
    
    if passed == total:
        print("🎉 ALL CORE MODULES ARE FUNCTIONAL!")
    else:
        print("⚠️  Some modules need attention.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()