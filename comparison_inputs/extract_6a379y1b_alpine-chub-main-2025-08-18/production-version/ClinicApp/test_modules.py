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

# Helper function to get admin token
def get_admin_token():
    try:
        # Try to initialize admin user (may fail if already exists)
        try:
            url = f"{API_URL}/auth/init-admin"
            response = requests.post(url)
            print("Admin user initialized successfully")
        except Exception as e:
            print(f"Admin initialization skipped: {str(e)}")
            # Continue anyway as admin might already exist
        
        # Login with admin credentials
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["access_token"]
    except Exception as e:
        print(f"Error getting admin token: {str(e)}")
        return None

# Helper function to create a test patient
def create_test_patient():
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test.patient@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1985-06-15",
            "gender": "female",
            "address_line1": "123 Test Street",
            "city": "Testville",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        return None

# Helper function to create a test provider
def create_test_provider(admin_token):
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Test",
            "last_name": "Provider",
            "title": "Dr.",
            "specialties": ["Family Medicine"],
            "license_number": "TEST123",
            "npi_number": "1234567890",
            "email": "test.provider@example.com",
            "phone": "+1-555-987-6543"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test provider: {str(e)}")
        return None

# Test Referrals Management System
def test_referrals_management(admin_token, patient_id, provider_id):
    print("\n--- Testing Referrals Management System ---")
    
    # Test creating a referral
    referral_id = None
    try:
        url = f"{API_URL}/referrals"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "referring_provider_id": provider_id,
            "referred_to_provider_name": "Dr. Specialist",
            "referred_to_specialty": "Cardiology",
            "reason_for_referral": "Suspected heart condition",
            "urgency": "routine",
            "notes": "Patient has family history of heart disease",
            "status": "pending"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        referral_id = result["id"]
        print_test_result("Create Referral", True, result)
    except Exception as e:
        print(f"Error creating referral: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Referral", False)
    
    # Test getting all referrals
    try:
        url = f"{API_URL}/referrals"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Referrals", True, result)
    except Exception as e:
        print(f"Error getting all referrals: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Referrals", False)
    
    # Test getting a specific referral
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Referral by ID", True, result)
        except Exception as e:
            print(f"Error getting referral by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Referral by ID", False)
    
    # Test updating a referral
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "notes": "Updated notes for the referral",
                "urgency": "urgent"
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Referral", True, result)
        except Exception as e:
            print(f"Error updating referral: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Referral", False)
    
    # Test updating referral status
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "scheduled"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Referral Status", True, result)
        except Exception as e:
            print(f"Error updating referral status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Referral Status", False)
    
    # Test getting referrals by patient
    try:
        url = f"{API_URL}/referrals/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Referrals", True, result)
    except Exception as e:
        print(f"Error getting patient referrals: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Referrals", False)
    
    # Test adding a referral report
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}/reports"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "report_date": date.today().isoformat(),
                "provider_name": "Dr. Specialist",
                "findings": "Patient has mild hypertension",
                "recommendations": "Lifestyle modifications and follow-up in 3 months",
                "attachments": []
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Add Referral Report", True, result)
        except Exception as e:
            print(f"Error adding referral report: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Add Referral Report", False)
    
    return referral_id

# Test Clinical Templates & Protocols System
def test_clinical_templates(admin_token):
    print("\n--- Testing Clinical Templates & Protocols System ---")
    
    # Test initializing standard templates
    try:
        url = f"{API_URL}/clinical-templates/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Clinical Templates", True, result)
    except Exception as e:
        print(f"Error initializing clinical templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Clinical Templates", False)
    
    # Test creating a custom template
    template_id = None
    try:
        url = f"{API_URL}/clinical-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "name": "Diabetes Management Protocol",
            "description": "Comprehensive protocol for managing type 2 diabetes",
            "template_type": "protocol",
            "specialty": "Endocrinology",
            "content": {
                "assessment": "Comprehensive diabetes assessment including HbA1c, lipid panel, and kidney function",
                "treatment_plan": "Lifestyle modifications, medication management, and regular monitoring",
                "follow_up": "Every 3 months for HbA1c check"
            },
            "is_active": True,
            "created_by": "admin"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        template_id = result["id"]
        print_test_result("Create Clinical Template", True, result)
    except Exception as e:
        print(f"Error creating clinical template: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Clinical Template", False)
    
    # Test getting all templates
    try:
        url = f"{API_URL}/clinical-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Clinical Templates", True, result)
    except Exception as e:
        print(f"Error getting all clinical templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Clinical Templates", False)
    
    # Test getting a specific template
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Clinical Template by ID", True, result)
        except Exception as e:
            print(f"Error getting clinical template by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Clinical Template by ID", False)
    
    # Test updating a template
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "description": "Updated protocol for managing type 2 diabetes with latest guidelines",
                "content": {
                    "assessment": "Comprehensive diabetes assessment including HbA1c, lipid panel, kidney function, and foot exam",
                    "treatment_plan": "Lifestyle modifications, medication management, and regular monitoring",
                    "follow_up": "Every 3 months for HbA1c check"
                }
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Clinical Template", True, result)
        except Exception as e:
            print(f"Error updating clinical template: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Clinical Template", False)
    
    return template_id

# Test Quality Measures & Reporting System
def test_quality_measures(admin_token, patient_id):
    print("\n--- Testing Quality Measures & Reporting System ---")
    
    # Test creating a quality measure
    measure_id = None
    try:
        url = f"{API_URL}/quality-measures"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "measure_id": str(uuid.uuid4()),
            "name": "Diabetes HbA1c Control",
            "description": "Percentage of patients with diabetes who had HbA1c < 8.0%",
            "measure_type": "process",
            "category": "diabetes",
            "numerator_criteria": {"condition": "diabetes", "hba1c_value": "<8.0"},
            "denominator_criteria": {"condition": "diabetes"},
            "exclusion_criteria": {"pregnancy": True, "hospice": True},
            "target_percentage": 75.0,
            "reporting_period": "annual",
            "is_active": True
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        measure_id = result["id"]
        print_test_result("Create Quality Measure", True, result)
    except Exception as e:
        print(f"Error creating quality measure: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Quality Measure", False)
    
    # Test getting all quality measures
    try:
        url = f"{API_URL}/quality-measures"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Quality Measures", True, result)
    except Exception as e:
        print(f"Error getting all quality measures: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Quality Measures", False)
    
    # Test getting a specific quality measure
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/{measure_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Quality Measure by ID", True, result)
        except Exception as e:
            print(f"Error getting quality measure by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Quality Measure by ID", False)
    
    # Test updating a quality measure
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/{measure_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "description": "Updated: Percentage of patients with diabetes who had HbA1c < 8.0%",
                "target_percentage": 80.0
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Quality Measure", True, result)
        except Exception as e:
            print(f"Error updating quality measure: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Quality Measure", False)
    
    # Test calculating quality measures for a patient
    if measure_id and patient_id:
        try:
            url = f"{API_URL}/quality-measures/calculate"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"patient_id": patient_id}
            data = [measure_id]
            
            response = requests.post(url, headers=headers, params=params, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Calculate Quality Measures", True, result)
        except Exception as e:
            print(f"Error calculating quality measures: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Calculate Quality Measures", False)
    
    # Test getting quality measure reports
    try:
        url = f"{API_URL}/quality-measures/report"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat()
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Quality Measure Reports", True, result)
    except Exception as e:
        print(f"Error getting quality measure reports: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Quality Measure Reports", False)
    
    return measure_id

# Test Patient Portal System
def test_patient_portal(admin_token, patient_id):
    print("\n--- Testing Patient Portal System ---")
    
    # Test creating patient portal access
    portal_id = None
    try:
        url = f"{API_URL}/patient-portal"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "username": f"patient_{patient_id[:8]}",
            "email": "test.patient@example.com",
            "password": "TestPassword123",
            "security_question": "What is your mother's maiden name?",
            "security_answer": "Smith",
            "terms_accepted": True,
            "is_active": True
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        portal_id = result["id"]
        print_test_result("Create Patient Portal Access", True, result)
    except Exception as e:
        print(f"Error creating patient portal access: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Patient Portal Access", False)
    
    # Test getting all patient portal accounts
    try:
        url = f"{API_URL}/patient-portal"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Patient Portal Accounts", True, result)
    except Exception as e:
        print(f"Error getting all patient portal accounts: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Patient Portal Accounts", False)
    
    # Test getting patient portal by patient ID
    try:
        url = f"{API_URL}/patient-portal/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Portal by Patient ID", True, result)
    except Exception as e:
        print(f"Error getting patient portal by patient ID: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Portal by Patient ID", False)
    
    # Test scheduling an appointment through the portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/schedule"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "appointment_date": (date.today() + timedelta(days=7)).isoformat(),
                "preferred_time": "morning",
                "reason": "Annual check-up",
                "notes": "Requesting Dr. Smith if available",
                "insurance_changed": False,
                "appointment_type": "consultation"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Schedule Appointment Through Portal", True, result)
        except Exception as e:
            print(f"Error scheduling appointment through portal: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Schedule Appointment Through Portal", False)
    
    # Test getting patient records through the portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/records"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Patient Records Through Portal", True, result)
        except Exception as e:
            print(f"Error getting patient records through portal: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Patient Records Through Portal", False)
    
    return portal_id

# Test Document Management System
def test_document_management(admin_token, patient_id):
    print("\n--- Testing Document Management System ---")
    
    # Test creating a document
    document_id = None
    try:
        url = f"{API_URL}/documents"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "title": "Lab Results",
            "description": "Complete blood count results",
            "document_type": "lab_result",
            "category_id": "lab",
            "file_name": "cbc_results.pdf",
            "file_path": "/virtual/path/to/file.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "tags": ["lab", "cbc", "routine"],
            "created_by": "admin"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        document_id = result["id"]
        print_test_result("Create Document", True, result)
    except Exception as e:
        print(f"Error creating document: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Document", False)
    
    # Test getting all documents
    try:
        url = f"{API_URL}/documents"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Documents", True, result)
    except Exception as e:
        print(f"Error getting all documents: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Documents", False)
    
    # Test getting a specific document
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Document by ID", True, result)
        except Exception as e:
            print(f"Error getting document by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Document by ID", False)
    
    # Test updating a document
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "title": "Updated Lab Results",
                "description": "Updated complete blood count results",
                "tags": ["lab", "cbc", "routine", "updated"]
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document", True, result)
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document", False)
    
    # Test getting documents by patient
    try:
        url = f"{API_URL}/documents/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Documents", True, result)
    except Exception as e:
        print(f"Error getting patient documents: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Documents", False)
    
    # Test document workflow
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}/workflow"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "status": "under_review",
                "assigned_to": "Dr. Reviewer",
                "notes": "Please review these lab results"
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document Workflow", True, result)
        except Exception as e:
            print(f"Error updating document workflow: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document Workflow", False)
    
    # Test document status update
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "approved"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document Status", True, result)
        except Exception as e:
            print(f"Error updating document status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document Status", False)
    
    return document_id

# Test Telehealth Module System
def test_telehealth_module(admin_token, patient_id, provider_id):
    print("\n--- Testing Telehealth Module System ---")
    
    # Test creating a telehealth session
    session_id = None
    try:
        url = f"{API_URL}/telehealth"
        headers = {"Authorization": f"Bearer {admin_token}"}
        scheduled_datetime = datetime.combine(date.today() + timedelta(days=1), datetime.strptime("14:00", "%H:%M").time())
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_date": (date.today() + timedelta(days=1)).isoformat(),
            "scheduled_time": "14:00",
            "scheduled_start": scheduled_datetime.isoformat(),
            "duration_minutes": 30,
            "reason": "Follow-up consultation",
            "session_type": "video",
            "status": "scheduled"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        session_id = result["id"]
        print_test_result("Create Telehealth Session", True, result)
    except Exception as e:
        print(f"Error creating telehealth session: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Telehealth Session", False)
    
    # Test getting all telehealth sessions
    try:
        url = f"{API_URL}/telehealth"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Telehealth Sessions", True, result)
    except Exception as e:
        print(f"Error getting all telehealth sessions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Telehealth Sessions", False)
    
    # Test getting a specific telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Telehealth Session by ID", True, result)
        except Exception as e:
            print(f"Error getting telehealth session by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Telehealth Session by ID", False)
    
    # Test updating a telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "reason": "Updated follow-up consultation",
                "notes": "Patient requested longer session"
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Telehealth Session", True, result)
        except Exception as e:
            print(f"Error updating telehealth session: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Telehealth Session", False)
    
    # Test joining a telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/join"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "participant_type": "provider",
                "participant_id": provider_id,
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows",
                    "device": "Desktop"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Join Telehealth Session", True, result)
        except Exception as e:
            print(f"Error joining telehealth session: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Join Telehealth Session", False)
    
    # Test updating telehealth session status
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {"status": "in_progress"}
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Telehealth Session Status", True, result)
        except Exception as e:
            print(f"Error updating telehealth session status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Telehealth Session Status", False)
    
    return session_id

# Main function to run all tests
def main():
    print("Starting comprehensive testing of 6 backend modules...")
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Exiting.")
        return
    
    # Create test patient
    patient_id = create_test_patient()
    if not patient_id:
        print("Failed to create test patient. Exiting.")
        return
    
    # Create test provider
    provider_id = create_test_provider(admin_token)
    if not provider_id:
        print("Failed to create test provider. Exiting.")
        return
    
    # Test all 6 modules
    test_referrals_management(admin_token, patient_id, provider_id)
    test_clinical_templates(admin_token)
    test_quality_measures(admin_token, patient_id)
    test_patient_portal(admin_token, patient_id)
    test_document_management(admin_token, patient_id)
    test_telehealth_module(admin_token, patient_id, provider_id)
    
    print("\nTesting completed!")

if __name__ == "__main__":
    main()