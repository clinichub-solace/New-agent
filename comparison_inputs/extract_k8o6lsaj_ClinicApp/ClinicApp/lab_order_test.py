#!/usr/bin/env python3
"""
Focused Lab Order Creation Test
Testing the specific lab order creation endpoint that had the model conflict fixed.
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

def test_authentication():
    """Test admin/admin123 credentials work"""
    print("\n=== TESTING AUTHENTICATION ===")
    
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
        print_test_result("Initialize Admin User", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
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
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login (admin/admin123)", True, result)
    except Exception as e:
        print_test_result("Admin Login (admin/admin123)", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return None
    
    return admin_token

def test_lab_order_creation(admin_token):
    """Test POST /api/lab-orders endpoint to confirm the duplicate LabOrder class issue has been resolved"""
    print("\n=== TESTING LAB ORDER CREATION FIX ===")
    
    if not admin_token:
        print("❌ Cannot test lab orders without authentication token")
        return None, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First, create a test patient for lab orders
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-22",
            "gender": "female",
            "address_line1": "456 Health Street",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print_test_result("Create Test Patient for Lab Orders", True, {"patient_id": patient_id, "name": f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"})
    except Exception as e:
        print_test_result("Create Test Patient for Lab Orders", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return None, None
    
    # Create a test provider for lab orders
    provider_id = None
    try:
        url = f"{API_URL}/providers"
        data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "license_number": "TX98765",
            "npi_number": "9876543210",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-345-6789"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print_test_result("Create Test Provider for Lab Orders", True, {"provider_id": provider_id, "name": f"{result['title']} {result['first_name']} {result['last_name']}"})
    except Exception as e:
        print_test_result("Create Test Provider for Lab Orders", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return patient_id, None
    
    # Initialize lab tests if needed
    try:
        url = f"{API_URL}/lab-tests/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Lab Tests", True, result)
    except Exception as e:
        print_test_result("Initialize Lab Tests", False, error_msg=str(e))
        # Continue even if this fails, as tests might already be initialized
    
    # Get available lab tests
    lab_tests = []
    try:
        url = f"{API_URL}/lab-tests"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        lab_tests = response.json()
        print_test_result("Get Available Lab Tests", True, {"count": len(lab_tests), "first_test": lab_tests[0] if lab_tests else "None"})
    except Exception as e:
        print_test_result("Get Available Lab Tests", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test the critical lab order creation endpoint
    lab_order_id = None
    if patient_id and provider_id and lab_tests:
        try:
            url = f"{API_URL}/lab-orders"
            
            # Use the first available lab test
            test_item = {
                "test_id": lab_tests[0]["id"],
                "test_code": lab_tests[0]["code"],  # Fixed: use "code" not "test_code"
                "test_name": lab_tests[0]["name"],  # Fixed: use "name" not "test_name"
                "quantity": 1,
                "specimen_type": lab_tests[0]["specimen_type"],
                "fasting_required": lab_tests[0].get("fasting_required", False),
                "priority": "routine"
            }
            
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "tests": [test_item],
                "priority": "routine",
                "clinical_info": "Routine annual physical examination",
                "diagnosis_codes": ["Z00.00"],  # ICD-10 code for routine general medical examination
                "lab_provider": "internal",
                "ordered_by": "admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify lab order creation
            assert "id" in result
            assert "order_number" in result
            assert result["order_number"].startswith("LAB-")
            assert result["patient_id"] == patient_id
            assert result["provider_id"] == provider_id
            assert len(result["tests"]) == 1
            assert result["tests"][0]["test_id"] == lab_tests[0]["id"]
            
            lab_order_id = result["id"]
            print_test_result("Create Lab Order (CRITICAL FIX)", True, result)
            
        except Exception as e:
            print_test_result("Create Lab Order (CRITICAL FIX)", False, error_msg=str(e))
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
                # This is the critical test - if it fails, we need to report the exact error
                if response.status_code == 500:
                    print("🚨 CRITICAL: 500 Server Error - Model conflict issue may still exist!")
                elif response.status_code == 422:
                    print("🚨 CRITICAL: 422 Validation Error - Field mismatch between models!")
    else:
        print("❌ Cannot test lab order creation - missing prerequisites (patient, provider, or lab tests)")
    
    return patient_id, lab_order_id

def test_lab_order_retrieval(admin_token, lab_order_id):
    """Test GET /api/lab-orders to verify created orders work"""
    print("\n=== TESTING LAB ORDER RETRIEVAL ===")
    
    if not admin_token:
        print("❌ Cannot test lab order retrieval without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Get all lab orders
    try:
        url = f"{API_URL}/lab-orders"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Lab Orders", True, {"count": len(result), "orders": result})
        
        # If we have orders, verify structure
        if result and len(result) > 0:
            order = result[0]
            assert "id" in order
            assert "order_number" in order
            assert "patient_id" in order
            assert "provider_id" in order
            assert "tests" in order
            print("✅ Lab order structure validation passed")
        
    except Exception as e:
        print_test_result("Get All Lab Orders", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test 2: Get specific lab order by ID (if we created one)
    if lab_order_id:
        try:
            url = f"{API_URL}/lab-orders/{lab_order_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify the specific order
            assert result["id"] == lab_order_id
            assert "order_number" in result
            assert "tests" in result
            
            print_test_result("Get Lab Order by ID", True, result)
            
        except Exception as e:
            print_test_result("Get Lab Order by ID", False, error_msg=str(e))
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")

def test_additional_apis(admin_token):
    """Briefly verify that Clinical Templates, Quality Measures, and Document Management APIs are still working"""
    print("\n=== TESTING ADDITIONAL APIS (BRIEF VERIFICATION) ===")
    
    if not admin_token:
        print("❌ Cannot test additional APIs without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Clinical Templates API
    try:
        url = f"{API_URL}/clinical-templates"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Clinical Templates API", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Clinical Templates API", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
    
    # Test Quality Measures API
    try:
        url = f"{API_URL}/quality-measures"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Quality Measures API", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Quality Measures API", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
    
    # Test Document Management API
    try:
        url = f"{API_URL}/documents"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Document Management API", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Document Management API", False, error_msg=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")

def main():
    """Main test execution"""
    print("🏥 ClinicHub Lab Order Creation Fix Testing")
    print("=" * 60)
    print("Focus: Testing the lab order creation endpoint that had the model conflict fixed")
    print("Requirements:")
    print("1. Authentication: Verify admin/admin123 credentials work")
    print("2. Lab Order Creation Fix: Test POST /api/lab-orders endpoint")
    print("3. Lab Order Retrieval: Test GET /api/lab-orders")
    print("4. Brief verification of other APIs")
    print("=" * 60)
    
    # Test 1: Authentication
    admin_token = test_authentication()
    
    # Test 2: Lab Order Creation (Critical Fix)
    patient_id, lab_order_id = test_lab_order_creation(admin_token)
    
    # Test 3: Lab Order Retrieval
    test_lab_order_retrieval(admin_token, lab_order_id)
    
    # Test 4: Additional APIs (Brief)
    test_additional_apis(admin_token)
    
    print("\n" + "=" * 60)
    print("🏥 Lab Order Creation Fix Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()