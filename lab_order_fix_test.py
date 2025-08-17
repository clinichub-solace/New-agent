#!/usr/bin/env python3
"""
ClinicHub Lab Order Creation Fix Testing Script
Focus: Test the specific requirements mentioned in the review request
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
    """Test admin/admin123 credentials work correctly"""
    print("\n=== 1. AUTHENTICATION TESTING ===")
    
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
        return None
    
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
        return None
    
    # Test 3: Verify Token Works
    try:
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["username"] == "admin"
        assert result["role"] == "admin"
        
        print_test_result("Verify JWT Token", True, result)
    except Exception as e:
        print_test_result("Verify JWT Token", False, error_msg=str(e))
        return None
    
    return admin_token

def test_lab_order_creation_fix(admin_token):
    """Test POST /api/lab-orders endpoint to ensure duplicate endpoint issue is resolved"""
    print("\n=== 2. LAB ORDER CREATION FIX TESTING ===")
    
    if not admin_token:
        print("❌ Cannot test lab orders without authentication token")
        return None, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First, create a test patient for lab orders
    patient_id = None
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emma",
            "last_name": "Rodriguez",
            "email": "emma.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-20",
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
        print_test_result("Create Test Patient for Lab Orders", True, result)
    except Exception as e:
        print_test_result("Create Test Patient for Lab Orders", False, error_msg=str(e))
        return None, None
    
    # Create a test provider for lab orders
    provider_id = None
    try:
        url = f"{API_URL}/providers"
        data = {
            "first_name": "Maria",
            "last_name": "Garcia",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "license_number": "TX98765",
            "npi_number": "9876543210",
            "email": "dr.garcia@clinichub.com",
            "phone": "+1-555-345-6789"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print_test_result("Create Test Provider for Lab Orders", True, result)
    except Exception as e:
        print_test_result("Create Test Provider for Lab Orders", False, error_msg=str(e))
        return None, None
    
    # Initialize lab tests if needed
    try:
        url = f"{API_URL}/lab-tests/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("Initialize Lab Tests", True, result)
    except Exception as e:
        print_test_result("Initialize Lab Tests", False, error_msg=str(e))
    
    # Get available lab tests
    lab_test_id = None
    try:
        url = f"{API_URL}/lab-tests"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if len(result) > 0:
            lab_test_id = result[0]["id"]
            print_test_result("Get Available Lab Tests", True, result)
        else:
            print_test_result("Get Available Lab Tests", False, error_msg="No lab tests available")
    except Exception as e:
        print_test_result("Get Available Lab Tests", False, error_msg=str(e))
    
    # Test Lab Order Creation (CRITICAL FIX)
    lab_order_id = None
    if patient_id and provider_id and lab_test_id:
        try:
            url = f"{API_URL}/lab-orders"
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "tests": [
                    {
                        "test_id": lab_test_id,
                        "test_code": "CBC",
                        "test_name": "Complete Blood Count",
                        "specimen_type": "blood",
                        "priority": "routine"
                    }
                ],
                "priority": "routine",
                "clinical_info": "Routine annual physical examination",
                "diagnosis_codes": ["Z00.00"],
                "ordered_by": "admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify lab order creation
            assert "order_number" in result
            assert result["order_number"].startswith("LAB-")
            assert result["patient_id"] == patient_id
            assert result["provider_id"] == provider_id
            assert len(result["tests"]) > 0
            
            lab_order_id = result["id"]
            print_test_result("Lab Order Creation (CRITICAL FIX)", True, result)
        except Exception as e:
            print_test_result("Lab Order Creation (CRITICAL FIX)", False, error_msg=str(e))
            return None, None
    else:
        print_test_result("Lab Order Creation (CRITICAL FIX)", False, error_msg="Missing required data (patient, provider, or lab test)")
        return None, None
    
    return lab_order_id, patient_id

def test_lab_order_retrieval(admin_token, lab_order_id, patient_id):
    """Test GET /api/lab-orders to verify created orders can be retrieved"""
    print("\n=== 3. LAB ORDER RETRIEVAL TESTING ===")
    
    if not admin_token:
        print("❌ Cannot test lab order retrieval without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Get All Lab Orders
    try:
        url = f"{API_URL}/lab-orders"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list of lab orders
        assert isinstance(result, list)
        if len(result) > 0:
            assert "order_number" in result[0]
            assert "patient_id" in result[0]
            assert "provider_id" in result[0]
        
        print_test_result("Get All Lab Orders", True, result)
    except Exception as e:
        print_test_result("Get All Lab Orders", False, error_msg=str(e))
    
    # Test 2: Get Specific Lab Order by ID
    if lab_order_id:
        try:
            url = f"{API_URL}/lab-orders/{lab_order_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify specific lab order retrieval
            assert result["id"] == lab_order_id
            assert "order_number" in result
            assert "tests" in result
            
            print_test_result("Get Lab Order by ID", True, result)
        except Exception as e:
            print_test_result("Get Lab Order by ID", False, error_msg=str(e))
    
    # Test 3: Get Lab Orders by Patient
    if patient_id:
        try:
            url = f"{API_URL}/lab-orders/patient/{patient_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify patient-specific lab orders
            assert isinstance(result, list)
            if len(result) > 0:
                assert result[0]["patient_id"] == patient_id
            
            print_test_result("Get Lab Orders by Patient", True, result)
        except Exception as e:
            print_test_result("Get Lab Orders by Patient", False, error_msg=str(e))

def test_clinical_templates_apis(admin_token):
    """Test /api/clinical-templates endpoints (GET, POST)"""
    print("\n=== 4. CLINICAL TEMPLATES APIs TESTING ===")
    
    if not admin_token:
        print("❌ Cannot test clinical templates without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Initialize Clinical Templates
    try:
        url = f"{API_URL}/clinical-templates/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Clinical Templates", True, result)
    except Exception as e:
        print_test_result("Initialize Clinical Templates", False, error_msg=str(e))
    
    # Test 2: Get All Clinical Templates
    try:
        url = f"{API_URL}/clinical-templates"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list of templates
        assert isinstance(result, list)
        
        print_test_result("GET Clinical Templates", True, result)
    except Exception as e:
        print_test_result("GET Clinical Templates", False, error_msg=str(e))
    
    # Test 3: Create New Clinical Template
    template_id = None
    try:
        url = f"{API_URL}/clinical-templates"
        data = {
            "name": "Hypertension Management Protocol",
            "template_type": "protocol",
            "specialty": "Cardiology",
            "description": "Standard protocol for managing hypertension patients",
            "content": {
                "assessment_criteria": [
                    "Blood pressure readings",
                    "Patient history",
                    "Current medications"
                ],
                "treatment_steps": [
                    "Lifestyle modifications",
                    "Medication adjustment",
                    "Follow-up scheduling"
                ]
            },
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify template creation
        assert "id" in result
        assert result["name"] == "Hypertension Management Protocol"
        assert result["template_type"] == "protocol"
        
        template_id = result["id"]
        print_test_result("POST Clinical Template (Create)", True, result)
    except Exception as e:
        print_test_result("POST Clinical Template (Create)", False, error_msg=str(e))
    
    # Test 4: Get Specific Clinical Template
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify specific template retrieval
            assert result["id"] == template_id
            assert "content" in result
            
            print_test_result("GET Clinical Template by ID", True, result)
        except Exception as e:
            print_test_result("GET Clinical Template by ID", False, error_msg=str(e))

def test_quality_measures_apis(admin_token):
    """Test /api/quality-measures endpoints (GET, POST)"""
    print("\n=== 5. QUALITY MEASURES APIs TESTING ===")
    
    if not admin_token:
        print("❌ Cannot test quality measures without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Initialize Quality Measures
    try:
        url = f"{API_URL}/quality-measures/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Quality Measures", True, result)
    except Exception as e:
        print_test_result("Initialize Quality Measures", False, error_msg=str(e))
    
    # Test 2: Get All Quality Measures
    try:
        url = f"{API_URL}/quality-measures"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list of quality measures
        assert isinstance(result, list)
        
        print_test_result("GET Quality Measures", True, result)
    except Exception as e:
        print_test_result("GET Quality Measures", False, error_msg=str(e))
    
    # Test 3: Create New Quality Measure
    measure_id = None
    try:
        url = f"{API_URL}/quality-measures"
        data = {
            "measure_name": "Diabetes HbA1c Control",
            "measure_code": "CMS122v10",
            "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
            "category": "clinical_quality",
            "target_population": "Patients with diabetes aged 18-75",
            "numerator_criteria": "HbA1c > 9.0%",
            "denominator_criteria": "Patients with diabetes diagnosis",
            "measurement_period": "Annual",
            "target_percentage": 90.0,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify quality measure creation
        assert "id" in result
        assert result["measure_name"] == "Diabetes HbA1c Control"
        assert result["measure_code"] == "CMS122v10"
        
        measure_id = result["id"]
        print_test_result("POST Quality Measure (Create)", True, result)
    except Exception as e:
        print_test_result("POST Quality Measure (Create)", False, error_msg=str(e))
    
    # Test 4: Get Specific Quality Measure
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/{measure_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify specific measure retrieval
            assert result["id"] == measure_id
            assert "target_percentage" in result
            
            print_test_result("GET Quality Measure by ID", True, result)
        except Exception as e:
            print_test_result("GET Quality Measure by ID", False, error_msg=str(e))

def test_document_management_apis(admin_token):
    """Test /api/documents endpoints (GET, POST)"""
    print("\n=== 6. DOCUMENT MANAGEMENT APIs TESTING ===")
    
    if not admin_token:
        print("❌ Cannot test document management without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Initialize Document Management
    try:
        url = f"{API_URL}/documents/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Document Management", True, result)
    except Exception as e:
        print_test_result("Initialize Document Management", False, error_msg=str(e))
    
    # Test 2: Get All Documents
    try:
        url = f"{API_URL}/documents"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify we get a list of documents
        assert isinstance(result, list)
        
        print_test_result("GET Documents", True, result)
    except Exception as e:
        print_test_result("GET Documents", False, error_msg=str(e))
    
    # Test 3: Create New Document
    document_id = None
    try:
        url = f"{API_URL}/documents"
        data = {
            "title": "Patient Consent Form Template",
            "document_type": "consent_form",
            "category": "legal",
            "description": "Standard patient consent form for medical procedures",
            "content": "I, [PATIENT_NAME], hereby consent to the medical treatment proposed by [PROVIDER_NAME]...",
            "version": "1.0",
            "is_template": True,
            "requires_signature": True,
            "retention_period_years": 7,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify document creation
        assert "id" in result
        assert result["title"] == "Patient Consent Form Template"
        assert result["document_type"] == "consent_form"
        
        document_id = result["id"]
        print_test_result("POST Document (Create)", True, result)
    except Exception as e:
        print_test_result("POST Document (Create)", False, error_msg=str(e))
    
    # Test 4: Get Specific Document
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify specific document retrieval
            assert result["id"] == document_id
            assert "content" in result
            
            print_test_result("GET Document by ID", True, result)
        except Exception as e:
            print_test_result("GET Document by ID", False, error_msg=str(e))
    
    # Test 5: Get Documents by Type
    try:
        url = f"{API_URL}/documents"
        params = {"document_type": "consent_form"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify filtered document retrieval
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["document_type"] == "consent_form"
        
        print_test_result("GET Documents by Type", True, result)
    except Exception as e:
        print_test_result("GET Documents by Type", False, error_msg=str(e))

def main():
    """Main test execution function"""
    print("=" * 80)
    print("CLINICHUB LAB ORDER CREATION FIX - FOCUSED TESTING")
    print("=" * 80)
    print("Testing Priority:")
    print("1. Authentication (admin/admin123)")
    print("2. Lab Order Creation Fix (POST /api/lab-orders)")
    print("3. Lab Order Retrieval (GET /api/lab-orders)")
    print("4. Clinical Templates APIs (GET, POST)")
    print("5. Quality Measures APIs (GET, POST)")
    print("6. Document Management APIs (GET, POST)")
    print("=" * 80)
    
    # Test 1: Authentication
    admin_token = test_authentication()
    if not admin_token:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with other tests.")
        return
    
    # Test 2 & 3: Lab Order Creation Fix and Retrieval
    lab_order_id, patient_id = test_lab_order_creation_fix(admin_token)
    test_lab_order_retrieval(admin_token, lab_order_id, patient_id)
    
    # Test 4: Clinical Templates APIs
    test_clinical_templates_apis(admin_token)
    
    # Test 5: Quality Measures APIs
    test_quality_measures_apis(admin_token)
    
    # Test 6: Document Management APIs
    test_document_management_apis(admin_token)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETED")
    print("=" * 80)
    print("Review the results above to verify:")
    print("✅ Lab order creation works without conflicts")
    print("✅ The three module APIs are functional for frontend integration")
    print("=" * 80)

if __name__ == "__main__":
    main()