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

# Authentication function to get admin token
def get_admin_token():
    print("\n--- Getting Authentication Token ---")
    
    try:
        # Initialize admin user if needed
        init_url = f"{API_URL}/auth/init-admin"
        init_response = requests.post(init_url)
        init_response.raise_for_status()
        
        # Login with admin credentials
        login_url = f"{API_URL}/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post(login_url, json=login_data)
        login_response.raise_for_status()
        result = login_response.json()
        
        token = result["access_token"]
        print_test_result("Admin Authentication", True, {"token": token[:20] + "..."})
        return token
    except Exception as e:
        print(f"Error authenticating: {str(e)}")
        if 'login_response' in locals():
            print(f"Status code: {login_response.status_code}")
            print(f"Response text: {login_response.text}")
        print_test_result("Admin Authentication", False)
        return None

# Test function for Referrals Management System
def test_referrals_management(admin_token):
    print("\n--- Testing Referrals Management System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    referral_id = None
    
    # Test 1: Create a new referral
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": str(uuid.uuid4()),  # Using a random UUID for testing
            "patient_name": "John Smith",
            "referring_provider": "Dr. Sarah Johnson",
            "specialist_provider": "Dr. Michael Chen",
            "specialty": "Cardiology",
            "reason": "Abnormal ECG findings, suspected arrhythmia",
            "urgency": "medium",
            "notes": "Patient has family history of heart disease",
            "status": "pending",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "insurance_verified": True,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 2: Get all referrals
    try:
        url = f"{API_URL}/referrals"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Referrals", True, result)
    except Exception as e:
        print(f"Error getting referrals: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Referrals", False)
    
    # Test 3: Get referral by ID
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
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
    
    # Test 4: Update referral status
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
            data = {
                "status": "scheduled"
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Referral Status", True, result)
        except Exception as e:
            print(f"Error updating referral status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Referral Status", False)
    
    # Test 5: Get referrals by patient ID
    if referral_id:
        try:
            patient_id = data["patient_id"]
            url = f"{API_URL}/referrals/patient/{patient_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Referrals by Patient ID", True, result)
        except Exception as e:
            print(f"Error getting referrals by patient ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Referrals by Patient ID", False)
    
    return referral_id

# Test function for Clinical Templates & Protocols System
def test_clinical_templates(admin_token):
    print("\n--- Testing Clinical Templates & Protocols System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    template_id = None
    
    # Test 1: Initialize clinical templates
    try:
        url = f"{API_URL}/clinical-templates/init"
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
    
    # Test 2: Create a new clinical template
    try:
        url = f"{API_URL}/clinical-templates"
        data = {
            "name": "Hypertension Management Protocol",
            "description": "Evidence-based protocol for managing hypertension in adults",
            "template_type": "protocol",
            "specialty": "Cardiology",
            "content": {
                "assessment": [
                    "Measure blood pressure at each visit",
                    "Assess cardiovascular risk factors",
                    "Review medication adherence"
                ],
                "plan": [
                    "Lifestyle modifications (diet, exercise, sodium restriction)",
                    "First-line medications: ACE inhibitors, ARBs, CCBs, thiazide diuretics",
                    "Target BP < 130/80 mmHg for most patients"
                ],
                "follow_up": "Every 3-6 months depending on control"
            },
            "evidence_level": "A",
            "references": [
                "2023 ACC/AHA Guideline for the Management of Hypertension"
            ],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 3: Get all clinical templates
    try:
        url = f"{API_URL}/clinical-templates"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Clinical Templates", True, result)
    except Exception as e:
        print(f"Error getting clinical templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Clinical Templates", False)
    
    # Test 4: Get clinical template by ID
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
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
    
    # Test 5: Update clinical template
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
            data = {
                "description": "Updated evidence-based protocol for managing hypertension in adults",
                "content": {
                    "assessment": [
                        "Measure blood pressure at each visit",
                        "Assess cardiovascular risk factors",
                        "Review medication adherence",
                        "Check for end-organ damage"
                    ],
                    "plan": [
                        "Lifestyle modifications (diet, exercise, sodium restriction)",
                        "First-line medications: ACE inhibitors, ARBs, CCBs, thiazide diuretics",
                        "Target BP < 130/80 mmHg for most patients",
                        "Consider combination therapy for BP > 20/10 mmHg above target"
                    ],
                    "follow_up": "Every 3 months until target achieved, then every 6 months"
                }
            }
            
            response = requests.put(url, json=data, headers=headers)
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

# Test function for Quality Measures & Reporting System
def test_quality_measures(admin_token):
    print("\n--- Testing Quality Measures & Reporting System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    measure_id = None
    
    # Test 1: Create a new quality measure
    try:
        url = f"{API_URL}/quality-measures"
        data = {
            "name": "Diabetes HbA1c Control",
            "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
            "measure_type": "HEDIS",
            "measure_id": "CDC-HbA1c-Poor-Control",
            "numerator_criteria": "Patients with most recent HbA1c level > 9.0%",
            "denominator_criteria": "Patients 18-75 years with diabetes diagnosis",
            "exclusion_criteria": "Patients in hospice care",
            "target_percentage": 15.0,  # Lower is better for this measure
            "reporting_period": "annual",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 2: Get all quality measures
    try:
        url = f"{API_URL}/quality-measures"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Quality Measures", True, result)
    except Exception as e:
        print(f"Error getting quality measures: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Quality Measures", False)
    
    # Test 3: Get quality measure by ID
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/{measure_id}"
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
    
    # Test 4: Update quality measure
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/{measure_id}"
            data = {
                "description": "Updated: Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
                "target_percentage": 10.0  # Improved target
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Quality Measure", True, result)
        except Exception as e:
            print(f"Error updating quality measure: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Quality Measure", False)
    
    # Test 5: Calculate quality measure
    if measure_id:
        try:
            url = f"{API_URL}/quality-measures/calculate"
            data = {
                "measure_id": measure_id,
                "start_date": (datetime.now() - timedelta(days=365)).isoformat(),
                "end_date": datetime.now().isoformat()
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Calculate Quality Measure", True, result)
        except Exception as e:
            print(f"Error calculating quality measure: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Calculate Quality Measure", False)
    
    # Test 6: Get quality measures report
    try:
        url = f"{API_URL}/quality-measures/report"
        params = {
            "report_type": "summary",
            "period": "year"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Quality Measures Report", True, result)
    except Exception as e:
        print(f"Error getting quality measures report: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Quality Measures Report", False)
    
    return measure_id

# Test function for Patient Portal System
def test_patient_portal(admin_token):
    print("\n--- Testing Patient Portal System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    patient_id = str(uuid.uuid4())  # Using a random UUID for testing
    portal_id = None
    
    # Test 1: Create a patient portal account
    try:
        url = f"{API_URL}/patient-portal"
        data = {
            "patient_id": patient_id,
            "email": "patient@example.com",
            "phone": "555-123-4567",
            "password": "SecurePassword123",
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1980-05-15",
            "preferences": {
                "notification_email": True,
                "notification_sms": False,
                "language": "English"
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        portal_id = result["id"]
        print_test_result("Create Patient Portal Account", True, result)
    except Exception as e:
        print(f"Error creating patient portal account: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Patient Portal Account", False)
    
    # Test 2: Get all patient portal accounts
    try:
        url = f"{API_URL}/patient-portal"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Patient Portal Accounts", True, result)
    except Exception as e:
        print(f"Error getting patient portal accounts: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Patient Portal Accounts", False)
    
    # Test 3: Get patient portal account by patient ID
    try:
        url = f"{API_URL}/patient-portal/patient/{patient_id}"
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
    
    # Test 4: Schedule appointment through patient portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/schedule"
            data = {
                "provider_id": str(uuid.uuid4()),  # Using a random UUID for testing
                "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "follow_up",
                "reason": "Follow-up for hypertension",
                "notes": "Patient will bring blood pressure log"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Schedule Appointment via Patient Portal", True, result)
        except Exception as e:
            print(f"Error scheduling appointment via patient portal: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Schedule Appointment via Patient Portal", False)
    
    # Test 5: Get patient records through patient portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/records"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Patient Records via Patient Portal", True, result)
        except Exception as e:
            print(f"Error getting patient records via patient portal: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Patient Records via Patient Portal", False)
    
    return portal_id, patient_id

# Test function for Document Management System
def test_document_management(admin_token, patient_id=None):
    print("\n--- Testing Document Management System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    document_id = None
    
    # Use a random patient ID if none is provided
    if not patient_id:
        patient_id = str(uuid.uuid4())
    
    # Test 1: Create a new document
    try:
        url = f"{API_URL}/documents"
        data = {
            "patient_id": patient_id,
            "title": "Lab Results - Complete Blood Count",
            "document_type": "lab_result",
            "content": "Base64EncodedContentWouldGoHere",
            "file_type": "pdf",
            "file_size": 1024,
            "metadata": {
                "lab_date": datetime.now().isoformat(),
                "ordering_provider": "Dr. Sarah Johnson",
                "lab_facility": "LabCorp"
            },
            "tags": ["lab", "cbc", "routine"],
            "status": "pending",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 2: Get all documents
    try:
        url = f"{API_URL}/documents"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Documents", True, result)
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Documents", False)
    
    # Test 3: Get document by ID
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}"
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
    
    # Test 4: Upload document
    try:
        url = f"{API_URL}/documents/upload"
        data = {
            "patient_id": patient_id,
            "title": "Insurance Card - Front",
            "document_type": "insurance",
            "file_data": "Base64EncodedImageDataWouldGoHere",
            "file_type": "jpg",
            "file_size": 512,
            "tags": ["insurance", "card", "front"],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Upload Document", True, result)
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Upload Document", False)
    
    # Test 5: Get documents by patient ID
    try:
        url = f"{API_URL}/documents/patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Documents by Patient ID", True, result)
    except Exception as e:
        print(f"Error getting documents by patient ID: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Documents by Patient ID", False)
    
    # Test 6: Update document workflow status
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}/workflow"
            data = {
                "status": "approved",
                "reviewed_by": "Dr. Michael Chen",
                "review_notes": "Results within normal range"
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document Workflow Status", True, result)
        except Exception as e:
            print(f"Error updating document workflow status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document Workflow Status", False)
    
    return document_id

# Test function for Telehealth Module System
def test_telehealth_module(admin_token):
    print("\n--- Testing Telehealth Module System ---")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    session_id = None
    
    # Test 1: Create a new telehealth session
    try:
        url = f"{API_URL}/telehealth"
        data = {
            "patient_id": str(uuid.uuid4()),  # Using a random UUID for testing
            "patient_name": "John Smith",
            "provider_id": str(uuid.uuid4()),  # Using a random UUID for testing
            "provider_name": "Dr. Sarah Johnson",
            "scheduled_start": (datetime.now() + timedelta(hours=2)).isoformat(),
            "scheduled_end": (datetime.now() + timedelta(hours=3)).isoformat(),
            "session_type": "follow_up",
            "reason": "Follow-up for hypertension medication adjustment",
            "status": "scheduled",
            "meeting_link": f"https://telehealth.clinichub.com/session/{uuid.uuid4()}",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 2: Get all telehealth sessions
    try:
        url = f"{API_URL}/telehealth"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get All Telehealth Sessions", True, result)
    except Exception as e:
        print(f"Error getting telehealth sessions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Telehealth Sessions", False)
    
    # Test 3: Get telehealth session by ID
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}"
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
    
    # Test 4: Join telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/join"
            data = {
                "participant_type": "provider",
                "participant_id": data["provider_id"],
                "participant_name": data["provider_name"],
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows",
                    "has_camera": True,
                    "has_microphone": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Join Telehealth Session", True, result)
        except Exception as e:
            print(f"Error joining telehealth session: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Join Telehealth Session", False)
    
    # Test 5: Update telehealth session status
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/status"
            data = {
                "status": "in_progress",
                "updated_by": "admin"
            }
            
            response = requests.put(url, json=data, headers=headers)
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
    print("\n" + "=" * 80)
    print("TESTING NEW CLINICHUB MODULES")
    print("=" * 80)
    
    # Get admin authentication token
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to authenticate. Exiting tests.")
        return
    
    # Test Referrals Management System
    referral_id = test_referrals_management(admin_token)
    
    # Test Clinical Templates & Protocols System
    template_id = test_clinical_templates(admin_token)
    
    # Test Quality Measures & Reporting System
    measure_id = test_quality_measures(admin_token)
    
    # Test Patient Portal System
    portal_id, patient_id = test_patient_portal(admin_token)
    
    # Test Document Management System (using the patient ID from the portal test if available)
    document_id = test_document_management(admin_token, patient_id)
    
    # Test Telehealth Module System
    session_id = test_telehealth_module(admin_token)
    
    print("\n--- Test Summary ---")
    print(f"Referrals Management System: {'✅ PASSED' if referral_id else '❌ FAILED'}")
    print(f"Clinical Templates & Protocols System: {'✅ PASSED' if template_id else '❌ FAILED'}")
    print(f"Quality Measures & Reporting System: {'✅ PASSED' if measure_id else '❌ FAILED'}")
    print(f"Patient Portal System: {'✅ PASSED' if portal_id else '❌ FAILED'}")
    print(f"Document Management System: {'✅ PASSED' if document_id else '❌ FAILED'}")
    print(f"Telehealth Module System: {'✅ PASSED' if session_id else '❌ FAILED'}")
    
    return {
        "referrals": referral_id is not None,
        "clinical_templates": template_id is not None,
        "quality_measures": measure_id is not None,
        "patient_portal": portal_id is not None,
        "documents": document_id is not None,
        "telehealth": session_id is not None
    }

if __name__ == "__main__":
    main()