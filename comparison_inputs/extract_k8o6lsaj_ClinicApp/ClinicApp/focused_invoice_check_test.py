#!/usr/bin/env python3
"""
Focused test for Invoice and Check fixes as requested in the review.
Testing specific endpoints:
1. Invoice UPDATE endpoint - PUT /api/invoices/{id}
2. Financial Transactions PUT endpoint - PUT /api/financial-transactions/{id}
3. Check creation - POST /api/checks
4. Check PRINT endpoint - POST /api/checks/{id}/print
5. Check Status UPDATE - PUT /api/checks/{id}/status
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

# Global variables to store created records
auth_token = None
patient_id = None
invoice_id = None
financial_transaction_id = None
check_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Authenticate with admin/admin123 credentials"""
    global auth_token
    print("\n--- Authentication ---")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        auth_token = result["access_token"]
        print_test_result("Authentication", True, {"token_type": result["token_type"], "user": result["user"]["username"]})
        return True
        
    except Exception as e:
        print_test_result("Authentication", False, error_msg=str(e))
        return False

def get_auth_headers():
    """Get authorization headers"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def create_test_patient():
    """Create a test patient for invoice testing"""
    global patient_id
    print("\n--- Creating Test Patient ---")
    
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "John",
            "last_name": "TestPatient",
            "email": "john.testpatient@example.com",
            "phone": "+1-555-987-6543",
            "date_of_birth": "1980-05-20",
            "gender": "male",
            "address_line1": "456 Test Street",
            "city": "Test City",
            "state": "TX",
            "zip_code": "75001"
        }
        
        response = requests.post(url, json=data, headers=get_auth_headers())
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print_test_result("Create Test Patient", True, {"patient_id": patient_id, "name": f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"})
        return True
        
    except Exception as e:
        print_test_result("Create Test Patient", False, error_msg=str(e))
        return False

def create_test_invoice():
    """Create a test invoice for UPDATE testing"""
    global invoice_id
    print("\n--- Creating Test Invoice ---")
    
    if not patient_id:
        print("❌ Cannot create invoice without patient_id")
        return False
    
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Office Visit",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "total": 150.00
                },
                {
                    "description": "Lab Work",
                    "quantity": 1,
                    "unit_price": 75.00,
                    "total": 75.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Test invoice for UPDATE endpoint testing"
        }
        
        response = requests.post(url, json=data, headers=get_auth_headers())
        response.raise_for_status()
        result = response.json()
        
        invoice_id = result["id"]
        print_test_result("Create Test Invoice", True, {
            "invoice_id": invoice_id,
            "invoice_number": result["invoice_number"],
            "total_amount": result["total_amount"],
            "issue_date": result["issue_date"]
        })
        return True
        
    except Exception as e:
        print_test_result("Create Test Invoice", False, error_msg=str(e))
        return False

def test_invoice_update():
    """Test Invoice UPDATE endpoint - PUT /api/invoices/{id}"""
    print("\n--- Testing Invoice UPDATE Endpoint ---")
    
    if not invoice_id or not patient_id:
        print("❌ Cannot test invoice update without invoice_id and patient_id")
        return False
    
    try:
        url = f"{API_URL}/invoices/{invoice_id}"
        
        # The PUT endpoint requires full InvoiceCreate data structure
        update_data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Updated Office Visit",
                    "quantity": 1,
                    "unit_price": 175.00,
                    "total": 175.00
                },
                {
                    "description": "Updated Lab Work",
                    "quantity": 1,
                    "unit_price": 85.00,
                    "total": 85.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Updated invoice - testing issue_date field fix"
        }
        
        response = requests.put(url, json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice UPDATE", True, {
                "invoice_id": result["id"],
                "invoice_number": result["invoice_number"],
                "issue_date": result["issue_date"],
                "total_amount": result["total_amount"],
                "updated_notes": result["notes"]
            })
            return True
        elif response.status_code == 405:
            print_test_result("Invoice UPDATE", False, error_msg="Method Not Allowed - UPDATE endpoint not implemented")
            return False
        else:
            print_test_result("Invoice UPDATE", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Invoice UPDATE", False, error_msg=str(e))
        return False

def test_invoice_status_update():
    """Test Invoice Status UPDATE endpoint - PUT /api/invoices/{id}/status"""
    print("\n--- Testing Invoice Status UPDATE Endpoint ---")
    
    if not invoice_id:
        print("❌ Cannot test invoice status update without invoice_id")
        return False
    
    try:
        url = f"{API_URL}/invoices/{invoice_id}/status"
        
        # Test updating invoice status
        status_data = {
            "status": "sent"
        }
        
        response = requests.put(url, json=status_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Invoice Status UPDATE", True, {
                "invoice_id": result["id"],
                "status": result["status"],
                "updated_at": result.get("updated_at")
            })
            return True
        elif response.status_code == 404:
            print_test_result("Invoice Status UPDATE", False, error_msg="Not Found - Status UPDATE endpoint missing")
            return False
        else:
            print_test_result("Invoice Status UPDATE", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Invoice Status UPDATE", False, error_msg=str(e))
        return False

def create_test_financial_transaction():
    """Create a test financial transaction for UPDATE testing"""
    global financial_transaction_id
    print("\n--- Creating Test Financial Transaction ---")
    
    try:
        url = f"{API_URL}/financial-transactions"
        data = {
            "transaction_type": "income",
            "amount": 225.00,
            "payment_method": "credit_card",
            "description": "Patient payment for invoice",
            "category": "patient_payment",
            "patient_id": patient_id,
            "invoice_id": invoice_id,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_auth_headers())
        response.raise_for_status()
        result = response.json()
        
        financial_transaction_id = result["id"]
        print_test_result("Create Test Financial Transaction", True, {
            "transaction_id": financial_transaction_id,
            "transaction_number": result["transaction_number"],
            "amount": result["amount"],
            "transaction_type": result["transaction_type"]
        })
        return True
        
    except Exception as e:
        print_test_result("Create Test Financial Transaction", False, error_msg=str(e))
        return False

def test_financial_transaction_update():
    """Test Financial Transaction PUT endpoint - PUT /api/financial-transactions/{id}"""
    print("\n--- Testing Financial Transaction UPDATE Endpoint ---")
    
    if not financial_transaction_id:
        print("❌ Cannot test financial transaction update without transaction_id")
        return False
    
    try:
        url = f"{API_URL}/financial-transactions/{financial_transaction_id}"
        
        # The PUT endpoint requires full FinancialTransactionCreate data structure
        # Include transaction_date to avoid validation error
        update_data = {
            "transaction_type": "income",
            "amount": 250.00,  # Updated amount
            "payment_method": "credit_card",
            "transaction_date": "2025-01-15",  # Provide explicit transaction_date
            "description": "Updated payment description - testing PUT endpoint",
            "category": "patient_payment",
            "patient_id": patient_id,
            "invoice_id": invoice_id,
            "created_by": "admin"
        }
        
        response = requests.put(url, json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Financial Transaction UPDATE", True, {
                "transaction_id": result["id"],
                "transaction_number": result["transaction_number"],
                "amount": result["amount"],
                "description": result["description"],
                "transaction_type": result["transaction_type"],
                "transaction_date": result["transaction_date"]
            })
            return True
        elif response.status_code == 404:
            print_test_result("Financial Transaction UPDATE", False, error_msg="Not Found - UPDATE endpoint missing")
            return False
        elif response.status_code == 405:
            print_test_result("Financial Transaction UPDATE", False, error_msg="Method Not Allowed - UPDATE endpoint not implemented")
            return False
        else:
            print_test_result("Financial Transaction UPDATE", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Financial Transaction UPDATE", False, error_msg=str(e))
        return False

def test_check_creation():
    """Test Check creation - POST /api/checks"""
    global check_id
    print("\n--- Testing Check Creation ---")
    
    try:
        url = f"{API_URL}/checks"
        data = {
            "payee_type": "vendor",
            "payee_name": "Medical Supply Company",
            "amount": 500.00,
            "memo": "Medical supplies payment",
            "check_date": "2025-01-15",  # Provide explicit check_date
            "expense_category": "medical_supplies",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=get_auth_headers())
        
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            check_id = result["id"]
            print_test_result("Check Creation", True, {
                "check_id": check_id,
                "check_number": result["check_number"],
                "payee_name": result["payee_name"],
                "amount": result["amount"],
                "status": result["status"],
                "check_date": result["check_date"]
            })
            return True
        elif response.status_code == 422:
            print_test_result("Check Creation", False, error_msg=f"Validation Error - {response.text}")
            return False
        else:
            print_test_result("Check Creation", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Check Creation", False, error_msg=str(e))
        return False

def test_check_print():
    """Test Check PRINT endpoint - POST /api/checks/{id}/print"""
    print("\n--- Testing Check PRINT Endpoint ---")
    
    if not check_id:
        print("❌ Cannot test check print without check_id")
        return False
    
    try:
        url = f"{API_URL}/checks/{check_id}/print"
        
        response = requests.post(url, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Check PRINT", True, {
                "check_id": check_id,
                "print_status": result.get("status", "printed"),
                "printed_date": result.get("printed_date")
            })
            return True
        elif response.status_code == 404:
            print_test_result("Check PRINT", False, error_msg="Not Found - PRINT endpoint missing")
            return False
        else:
            print_test_result("Check PRINT", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Check PRINT", False, error_msg=str(e))
        return False

def test_check_status_update():
    """Test Check Status UPDATE - PUT /api/checks/{id}/status"""
    print("\n--- Testing Check Status UPDATE ---")
    
    if not check_id:
        print("❌ Cannot test check status update without check_id")
        return False
    
    try:
        url = f"{API_URL}/checks/{check_id}/status"
        
        # Test updating check status with proper request body handling
        update_data = {
            "status": "issued"
        }
        
        response = requests.put(url, json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Check Status UPDATE", True, {
                "check_id": check_id,
                "new_status": result["status"],
                "updated_at": result.get("updated_at")
            })
            return True
        elif response.status_code == 404:
            print_test_result("Check Status UPDATE", False, error_msg="Not Found - Status UPDATE endpoint missing")
            return False
        elif response.status_code == 422:
            print_test_result("Check Status UPDATE", False, error_msg=f"Validation Error - Request body handling issue: {response.text}")
            return False
        else:
            print_test_result("Check Status UPDATE", False, error_msg=f"HTTP {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Check Status UPDATE", False, error_msg=str(e))
        return False

def main():
    """Main test execution"""
    print("🏥 FOCUSED INVOICE AND CHECK FIXES TESTING")
    print("=" * 80)
    print("Testing specific fixes mentioned in review request:")
    print("1. Invoice UPDATE endpoint - PUT /api/invoices/{id}")
    print("2. Financial Transactions PUT endpoint - PUT /api/financial-transactions/{id}")
    print("3. Check creation - POST /api/checks")
    print("4. Check PRINT endpoint - POST /api/checks/{id}/print")
    print("5. Check Status UPDATE - PUT /api/checks/{id}/status")
    print("=" * 80)
    
    # Step 1: Authenticate
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Create test data
    if not create_test_patient():
        print("❌ Failed to create test patient. Cannot proceed with invoice tests.")
        return
    
    if not create_test_invoice():
        print("❌ Failed to create test invoice. Cannot proceed with invoice update test.")
        return
    
    if not create_test_financial_transaction():
        print("❌ Failed to create test financial transaction. Cannot proceed with transaction update test.")
        return
    
    # Step 3: Test the specific endpoints mentioned in review
    print("\n" + "=" * 80)
    print("🎯 TESTING SPECIFIC FIXES")
    print("=" * 80)
    
    results = {
        "invoice_update": test_invoice_update(),
        "invoice_status_update": test_invoice_status_update(),
        "financial_transaction_update": test_financial_transaction_update(),
        "check_creation": test_check_creation(),
        "check_print": test_check_print(),
        "check_status_update": test_check_status_update()
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The invoice and check fixes are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the detailed error messages above.")

if __name__ == "__main__":
    main()