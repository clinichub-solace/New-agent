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

# Global variables for authentication
admin_token = None
patient_id = None

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

def authenticate_admin():
    """Authenticate as admin and return token"""
    global admin_token
    
    print("\n--- Authenticating as Admin ---")
    
    # Initialize admin user first
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        print_test_result("Initialize Admin User", False)
    
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
        print_test_result("Admin Login", True, {"username": result["user"]["username"], "role": result["user"]["role"]})
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

def test_employee_module():
    """Test Employee Module - POST/GET /api/employees"""
    print("\n--- Testing Employee Module ---")
    
    if not admin_token:
        print("❌ No admin token available for Employee Module testing")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    employee_id = None
    
    # Test 1: Create Employee (POST /api/employees)
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-234-5678",
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
        assert result["first_name"] == "Jennifer"
        assert result["last_name"] == "Martinez"
        assert result["role"] == "doctor"
        
        employee_id = result["id"]
        print_test_result("POST /api/employees (Create Employee)", True, result)
    except Exception as e:
        print(f"Error creating employee: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/employees (Create Employee)", False)
        return False
    
    # Test 2: Get All Employees (GET /api/employees)
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our employee is in it
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find our created employee
        found_employee = None
        for emp in result:
            if emp.get("id") == employee_id:
                found_employee = emp
                break
        
        assert found_employee is not None
        assert found_employee["first_name"] == "Jennifer"
        
        print_test_result("GET /api/employees (List Employees)", True, {"count": len(result), "found_our_employee": True})
    except Exception as e:
        print(f"Error getting employees: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/employees (List Employees)", False)
        return False
    
    return True

def test_financial_transactions_module():
    """Test Financial Transactions Module - POST/GET /api/financial-transactions"""
    print("\n--- Testing Financial Transactions Module ---")
    
    if not admin_token:
        print("❌ No admin token available for Financial Transactions testing")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    transaction_id = None
    
    # Test 1: Create Financial Transaction (POST /api/financial-transactions)
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 250.00,
            "payment_method": "credit_card",
            "description": "Patient consultation fee",
            "category": "consultation_fee",
            "transaction_date": date.today().isoformat(),
            "bank_account": "Main Operating Account",
            "reference_number": "CC-12345",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify transaction creation
        assert "transaction_number" in result
        assert result["transaction_type"] == "income"
        assert result["amount"] == 250.00
        assert result["payment_method"] == "credit_card"
        assert result["description"] == "Patient consultation fee"
        
        transaction_id = result["id"]
        print_test_result("POST /api/financial-transactions (Create Transaction)", True, result)
    except Exception as e:
        print(f"Error creating financial transaction: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/financial-transactions (Create Transaction)", False)
        return False
    
    # Test 2: Get All Financial Transactions (GET /api/financial-transactions)
    try:
        url = f"{API_URL}/financial-transactions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our transaction is in it
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find our created transaction
        found_transaction = None
        for txn in result:
            if txn.get("id") == transaction_id:
                found_transaction = txn
                break
        
        assert found_transaction is not None
        assert found_transaction["transaction_type"] == "income"
        assert found_transaction["amount"] == 250.00
        
        print_test_result("GET /api/financial-transactions (List Transactions)", True, {"count": len(result), "found_our_transaction": True})
    except Exception as e:
        print(f"Error getting financial transactions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/financial-transactions (List Transactions)", False)
        return False
    
    return True

def test_invoice_receipt_module():
    """Test Invoice/Receipt Module - POST/GET /api/invoices"""
    print("\n--- Testing Invoice/Receipt Module ---")
    
    if not admin_token:
        print("❌ No admin token available for Invoice/Receipt testing")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    invoice_id = None
    
    # First create a patient for the invoice
    patient_id = create_test_patient()
    if not patient_id:
        print("❌ Could not create test patient for invoice testing")
        return False
    
    # Test 1: Create Invoice (POST /api/invoices)
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Annual Physical Examination",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "total": 200.00
                },
                {
                    "description": "Blood Work - Comprehensive Panel",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "total": 150.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Payment due within 30 days"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify invoice creation
        assert "invoice_number" in result
        assert result["invoice_number"].startswith("INV-")
        assert result["patient_id"] == patient_id
        assert len(result["items"]) == 2
        assert result["subtotal"] == 350.00
        assert result["tax_rate"] == 0.08
        
        invoice_id = result["id"]
        print_test_result("POST /api/invoices (Create Invoice)", True, result)
    except Exception as e:
        print(f"Error creating invoice: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/invoices (Create Invoice)", False)
        return False
    
    # Test 2: Get All Invoices (GET /api/invoices)
    try:
        url = f"{API_URL}/invoices"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our invoice is in it
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find our created invoice
        found_invoice = None
        for inv in result:
            if inv.get("id") == invoice_id:
                found_invoice = inv
                break
        
        assert found_invoice is not None
        assert found_invoice["patient_id"] == patient_id
        
        print_test_result("GET /api/invoices (List Invoices)", True, {"count": len(result), "found_our_invoice": True})
    except Exception as e:
        print(f"Error getting invoices: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/invoices (List Invoices)", False)
        return False
    
    return True

def test_inventory_module():
    """Test Inventory Module - POST/GET /api/inventory"""
    print("\n--- Testing Inventory Module ---")
    
    if not admin_token:
        print("❌ No admin token available for Inventory testing")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    item_id = None
    
    # Test 1: Create Inventory Item (POST /api/inventory)
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Acetaminophen 500mg",
            "category": "Pain Relief",
            "sku": "MED-ACET-500",
            "current_stock": 200,
            "min_stock_level": 50,
            "unit_cost": 0.75,
            "supplier": "PharmaCorp Supplies",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Pharmacy Storage Room A",
            "notes": "Store at room temperature, keep dry"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify inventory item creation
        assert result["name"] == "Acetaminophen 500mg"
        assert result["category"] == "Pain Relief"
        assert result["sku"] == "MED-ACET-500"
        assert result["current_stock"] == 200
        assert result["min_stock_level"] == 50
        assert result["unit_cost"] == 0.75
        
        item_id = result["id"]
        print_test_result("POST /api/inventory (Create Inventory Item)", True, result)
    except Exception as e:
        print(f"Error creating inventory item: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/inventory (Create Inventory Item)", False)
        return False
    
    # Test 2: Get All Inventory Items (GET /api/inventory)
    try:
        url = f"{API_URL}/inventory"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our item is in it
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find our created item
        found_item = None
        for item in result:
            if item.get("id") == item_id:
                found_item = item
                break
        
        assert found_item is not None
        assert found_item["name"] == "Acetaminophen 500mg"
        assert found_item["current_stock"] == 200
        
        print_test_result("GET /api/inventory (List Inventory Items)", True, {"count": len(result), "found_our_item": True})
    except Exception as e:
        print(f"Error getting inventory items: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/inventory (List Inventory Items)", False)
        return False
    
    return True

def test_patient_module():
    """Test Patient Module - POST/GET /api/patients"""
    print("\n--- Testing Patient Module ---")
    
    if not admin_token:
        print("❌ No admin token available for Patient testing")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    patient_id = None
    
    # Test 1: Create Patient (POST /api/patients)
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Michael",
            "last_name": "Thompson",
            "email": "michael.thompson@example.com",
            "phone": "+1-555-345-6789",
            "date_of_birth": "1978-09-22",
            "gender": "male",
            "address_line1": "456 Healthcare Drive",
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
        assert result["name"][0]["family"] == "Thompson"
        assert "Michael" in result["name"][0]["given"]
        assert result["gender"] == "male"
        
        patient_id = result["id"]
        print_test_result("POST /api/patients (Create Patient)", True, result)
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("POST /api/patients (Create Patient)", False)
        return False
    
    # Test 2: Get All Patients (GET /api/patients)
    try:
        url = f"{API_URL}/patients"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list and our patient is in it
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find our created patient
        found_patient = None
        for patient in result:
            if patient.get("id") == patient_id:
                found_patient = patient
                break
        
        assert found_patient is not None
        assert found_patient["resource_type"] == "Patient"
        assert found_patient["name"][0]["family"] == "Thompson"
        
        print_test_result("GET /api/patients (List Patients)", True, {"count": len(result), "found_our_patient": True})
    except Exception as e:
        print(f"Error getting patients: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("GET /api/patients (List Patients)", False)
        return False
    
    return True

def create_test_patient():
    """Helper function to create a test patient for other tests"""
    if not admin_token:
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test.patient@example.com",
            "phone": "+1-555-999-0000",
            "date_of_birth": "1990-01-01",
            "gender": "other",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        return None

def main():
    """Main test execution function"""
    print("=" * 80)
    print("CLINICHUB BACKEND VERIFICATION TEST")
    print("Testing core modules after recent fixes")
    print("=" * 80)
    
    # Step 1: Authenticate as admin
    if not authenticate_admin():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Test all modules
    test_results = {}
    
    test_results["Employee Module"] = test_employee_module()
    test_results["Financial Transactions"] = test_financial_transactions_module()
    test_results["Invoice/Receipt Module"] = test_invoice_receipt_module()
    test_results["Inventory Module"] = test_inventory_module()
    test_results["Patient Module"] = test_patient_module()
    
    # Step 3: Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for module, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{module}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} modules passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! All major modules are operational.")
    else:
        print("⚠️  Some modules failed. Check the detailed output above.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()