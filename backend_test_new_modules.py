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

# Authentication function
def authenticate():
    print("\n--- Authenticating ---")
    try:
        # First try to initialize admin user
        init_url = f"{API_URL}/auth/init-admin"
        try:
            init_response = requests.post(init_url)
            init_response.raise_for_status()
            print("Admin user initialized successfully")
        except:
            print("Admin user already exists, proceeding to login")
        
        # Login with admin credentials
        login_url = f"{API_URL}/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        result = response.json()
        
        token = result["access_token"]
        print_test_result("Authentication", True, {"token": token[:20] + "..."})
        return token
    except Exception as e:
        print(f"Error authenticating: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Authentication", False)
        return None

# Test Referrals Management System
def test_referrals_management(token, patient_id=None):
    print("\n--- Testing Referrals Management System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test patient if none provided
    if not patient_id:
        try:
            patient_url = f"{API_URL}/patients"
            patient_data = {
                "first_name": "Robert",
                "last_name": "Smith",
                "email": "robert.smith@example.com",
                "phone": "+1-555-123-9876",
                "date_of_birth": "1975-08-21",
                "gender": "male",
                "address_line1": "456 Oak Street",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62704"
            }
            
            patient_response = requests.post(patient_url, json=patient_data, headers=headers)
            patient_response.raise_for_status()
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            print(f"Created test patient with ID: {patient_id}")
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            return
    
    # Test 1: Create a referral
    referral_id = None
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": patient_id,
            "referring_provider_id": "provider-123",
            "referring_provider_name": "Dr. John Smith",
            "referred_to_provider_name": "Dr. Jane Specialist",
            "referred_to_specialty": "Cardiology",
            "reason_for_referral": "Abnormal ECG findings, suspected arrhythmia",
            "urgency": "routine",
            "notes": "Patient has family history of heart disease",
            "status": "pending"
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
    
    # Test 4: Update referral
    if referral_id:
        try:
            url = f"{API_URL}/referrals/{referral_id}"
            data = {
                "status": "scheduled",
                "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "Appointment scheduled with Dr. Jane Specialist"
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Referral", True, result)
        except Exception as e:
            print(f"Error updating referral: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Referral", False)
    
    # Test 5: Get referrals by patient
    try:
        url = f"{API_URL}/referrals/patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Referrals by Patient", True, result)
    except Exception as e:
        print(f"Error getting referrals by patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Referrals by Patient", False)
    
    return referral_id, patient_id

# Test Clinical Templates & Protocols System
def test_clinical_templates(token):
    print("\n--- Testing Clinical Templates & Protocols System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create a clinical template
    template_id = None
    try:
        url = f"{API_URL}/clinical-templates"
        data = {
            "name": "Diabetes Management Protocol",
            "template_type": "protocol",
            "specialty": "Endocrinology",
            "version": "1.0",
            "content": {
                "overview": "Standard protocol for managing Type 2 Diabetes",
                "assessment": [
                    "HbA1c every 3 months",
                    "Lipid panel annually",
                    "Kidney function tests annually",
                    "Eye examination annually",
                    "Foot examination at each visit"
                ],
                "treatment": [
                    "Lifestyle modifications (diet, exercise)",
                    "Metformin as first-line therapy",
                    "Consider SGLT2 inhibitors or GLP-1 agonists as second-line",
                    "Insulin therapy for uncontrolled cases"
                ],
                "follow_up": "Every 3 months or as needed"
            },
            "evidence_based_references": [
                "American Diabetes Association Standards of Care 2023",
                "European Association for the Study of Diabetes Guidelines"
            ],
            "status": "active",
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
    
    # Test 2: Get all clinical templates
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
    
    # Test 3: Get clinical template by ID
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
    
    # Test 4: Update clinical template
    if template_id:
        try:
            url = f"{API_URL}/clinical-templates/{template_id}"
            data = {
                "version": "1.1",
                "content": {
                    "overview": "Updated protocol for managing Type 2 Diabetes",
                    "assessment": [
                        "HbA1c every 3 months",
                        "Lipid panel annually",
                        "Kidney function tests annually",
                        "Eye examination annually",
                        "Foot examination at each visit",
                        "Cardiovascular risk assessment annually"
                    ],
                    "treatment": [
                        "Lifestyle modifications (diet, exercise)",
                        "Metformin as first-line therapy",
                        "Consider SGLT2 inhibitors or GLP-1 agonists as second-line",
                        "Insulin therapy for uncontrolled cases"
                    ],
                    "follow_up": "Every 3 months or as needed"
                },
                "evidence_based_references": [
                    "American Diabetes Association Standards of Care 2023",
                    "European Association for the Study of Diabetes Guidelines",
                    "International Diabetes Federation Guidelines 2023"
                ]
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
    
    # Test 5: Initialize standard templates
    try:
        url = f"{API_URL}/clinical-templates/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Standard Templates", True, result)
    except Exception as e:
        print(f"Error initializing standard templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Standard Templates", False)
    
    return template_id

# Test Quality Measures & Reporting System
def test_quality_measures(token):
    print("\n--- Testing Quality Measures & Reporting System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create a quality measure
    measure_id = None
    try:
        url = f"{API_URL}/quality-measures"
        data = {
            "measure_id": str(uuid.uuid4()),
            "name": "Diabetes: HbA1c Poor Control",
            "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
            "measure_type": "process",
            "category": "diabetes",
            "numerator_criteria": {
                "condition": "diabetes",
                "test": "hba1c",
                "value": "> 9.0%"
            },
            "denominator_criteria": {
                "age_range": "18-75",
                "condition": "diabetes",
                "encounter_period": "1 year"
            },
            "exclusion_criteria": {
                "hospice": True,
                "pregnancy": True
            },
            "target_percentage": 15.0,  # Lower is better for this measure
            "reporting_period": "quarterly",
            "is_inverse": True  # Lower percentage is better
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
                "target_percentage": 10.0,  # Updated target
                "description": "Updated: Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
                "reporting_period": "monthly"
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
                "start_date": (datetime.now() - timedelta(days=90)).isoformat(),
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
            "period": "quarterly",
            "year": datetime.now().year,
            "quarter": (datetime.now().month - 1) // 3 + 1
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

# Test Patient Portal System
def test_patient_portal(token, patient_id=None):
    print("\n--- Testing Patient Portal System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test patient if none provided
    if not patient_id:
        try:
            patient_url = f"{API_URL}/patients"
            patient_data = {
                "first_name": "Emily",
                "last_name": "Johnson",
                "email": "emily.johnson@example.com",
                "phone": "+1-555-987-6543",
                "date_of_birth": "1988-03-15",
                "gender": "female",
                "address_line1": "789 Pine Avenue",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62704"
            }
            
            patient_response = requests.post(patient_url, json=patient_data, headers=headers)
            patient_response.raise_for_status()
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            print(f"Created test patient with ID: {patient_id}")
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            return
    
    # Test 1: Create patient portal access
    portal_id = None
    try:
        url = f"{API_URL}/patient-portal"
        data = {
            "patient_id": patient_id,
            "username": f"patient_{patient_id[:8]}",
            "email": "emily.johnson@example.com",
            "password": "SecurePass123!",
            "security_question": "What was your first pet's name?",
            "security_answer": "Fluffy",
            "preferences": {
                "notification_email": True,
                "notification_sms": True,
                "appointment_reminders": True,
                "lab_results_notifications": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
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
    
    # Test 3: Get patient portal by patient ID
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
    
    # Test 4: Schedule appointment through portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/schedule"
            data = {
                "provider_id": "provider-123",  # This would be a real provider ID in production
                "provider_name": "Dr. Sarah Williams",
                "appointment_date": (datetime.now() + timedelta(days=5)).isoformat(),
                "appointment_time": "14:30",
                "reason": "Annual physical examination",
                "notes": "No specific concerns, routine check-up"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Schedule Appointment Through Portal", True, result)
        except Exception as e:
            print(f"Error scheduling appointment through portal: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Schedule Appointment Through Portal", False)
    
    # Test 5: Get patient records through portal
    if portal_id:
        try:
            url = f"{API_URL}/patient-portal/{portal_id}/records"
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
    
    return portal_id, patient_id

# Test Document Management System
def test_document_management(token, patient_id=None):
    print("\n--- Testing Document Management System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test patient if none provided
    if not patient_id:
        try:
            patient_url = f"{API_URL}/patients"
            patient_data = {
                "first_name": "Michael",
                "last_name": "Brown",
                "email": "michael.brown@example.com",
                "phone": "+1-555-456-7890",
                "date_of_birth": "1965-11-30",
                "gender": "male",
                "address_line1": "123 Maple Street",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62704"
            }
            
            patient_response = requests.post(patient_url, json=patient_data, headers=headers)
            patient_response.raise_for_status()
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            print(f"Created test patient with ID: {patient_id}")
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            return
    
    # Test 1: Create a document
    document_id = None
    try:
        url = f"{API_URL}/documents"
        data = {
            "patient_id": patient_id,
            "title": "Lab Results - Complete Blood Count",
            "document_type": "lab_result",
            "category_id": "lab_reports",
            "file_name": "cbc_results.pdf",
            "file_path": "/uploads/lab_results/cbc_results.pdf",
            "mime_type": "application/pdf",
            "description": "Complete blood count results from Springfield Medical Lab",
            "tags": ["lab", "cbc", "hematology"],
            "metadata": {
                "lab_id": "SML-12345",
                "ordering_provider": "Dr. Sarah Williams",
                "collection_date": "2023-06-15"
            },
            "status": "pending",
            "file_size": 1024000,  # 1MB
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
    
    # Test 4: Update document
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}"
            data = {
                "title": "Updated: Lab Results - Complete Blood Count",
                "description": "Updated description: Complete blood count results from Springfield Medical Lab",
                "tags": ["lab", "cbc", "hematology", "updated"],
                "metadata": {
                    "lab_id": "SML-12345",
                    "ordering_provider": "Dr. Sarah Williams",
                    "collection_date": "2023-06-15",
                    "reviewed_by": "Dr. Michael Chen"
                }
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document", True, result)
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document", False)
    
    # Test 5: Upload document (simulated)
    try:
        url = f"{API_URL}/documents/upload"
        data = {
            "patient_id": patient_id,
            "document_type": "consent_form",
            "title": "Surgical Consent Form",
            "description": "Patient consent for appendectomy procedure",
            "file_data": "base64encodeddata",  # In a real test, this would be actual base64 data
            "file_name": "surgical_consent.pdf",
            "mime_type": "application/pdf",
            "uploaded_by": "Dr. John Smith",
            "category_id": "consent_forms",
            "file_size": 512000,  # 500KB
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
    
    # Test 6: Get documents by patient
    try:
        url = f"{API_URL}/documents/patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Documents by Patient", True, result)
    except Exception as e:
        print(f"Error getting documents by patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Documents by Patient", False)
    
    # Test 7: Update document workflow
    if document_id:
        try:
            url = f"{API_URL}/documents/{document_id}/workflow"
            data = {
                "status": "under_review",
                "assigned_to": "Dr. Michael Chen",
                "workflow_step": "physician_review",
                "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "priority": "normal",
                "notes": "Please review lab results and provide feedback"
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Document Workflow", True, result)
        except Exception as e:
            print(f"Error updating document workflow: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Document Workflow", False)
    
    return document_id, patient_id

# Test Telehealth Module System
def test_telehealth_module(token, patient_id=None):
    print("\n--- Testing Telehealth Module System ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test patient if none provided
    if not patient_id:
        try:
            patient_url = f"{API_URL}/patients"
            patient_data = {
                "first_name": "Jennifer",
                "last_name": "Wilson",
                "email": "jennifer.wilson@example.com",
                "phone": "+1-555-789-0123",
                "date_of_birth": "1992-07-18",
                "gender": "female",
                "address_line1": "456 Elm Street",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62704"
            }
            
            patient_response = requests.post(patient_url, json=patient_data, headers=headers)
            patient_response.raise_for_status()
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            print(f"Created test patient with ID: {patient_id}")
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            return
    
    # Test 1: Create a telehealth session
    session_id = None
    try:
        url = f"{API_URL}/telehealth"
        data = {
            "patient_id": patient_id,
            "provider_id": "provider-123",
            "provider_name": "Dr. Robert Wilson",
            "session_type": "follow_up",
            "scheduled_start": (datetime.now() + timedelta(hours=2)).isoformat(),
            "scheduled_end": (datetime.now() + timedelta(hours=2, minutes=30)).isoformat(),
            "reason": "Follow-up for hypertension management",
            "status": "scheduled",
            "meeting_link": f"https://telehealth.clinichub.com/session/{uuid.uuid4()}",
            "patient_instructions": "Please ensure you have a stable internet connection and are in a private location."
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
    
    # Test 4: Update telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}"
            data = {
                "scheduled_start_time": (datetime.now() + timedelta(hours=3)).isoformat(),
                "scheduled_end_time": (datetime.now() + timedelta(hours=3, minutes=30)).isoformat(),
                "reason": "Updated: Follow-up for hypertension management and medication review",
                "patient_instructions": "Updated instructions: Please ensure you have a stable internet connection, are in a private location, and have your current medication list available."
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Telehealth Session", True, result)
        except Exception as e:
            print(f"Error updating telehealth session: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Telehealth Session", False)
    
    # Test 5: Join telehealth session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/join"
            data = {
                "participant_type": "patient",
                "participant_id": patient_id,
                "participant_name": "Jennifer Wilson",
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows",
                    "device": "Desktop",
                    "network_type": "WiFi"
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
    
    # Test 6: Update telehealth session status
    if session_id:
        try:
            url = f"{API_URL}/telehealth/{session_id}/status"
            data = {
                "status": "in_progress",
                "status_notes": "Session started on time, both participants connected successfully."
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Telehealth Session Status", True, result)
            
            # Update to completed
            data = {
                "status": "completed",
                "status_notes": "Session completed successfully. Follow-up appointment scheduled for next month."
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Complete Telehealth Session", True, result)
        except Exception as e:
            print(f"Error updating telehealth session status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Telehealth Session Status", False)
    
    return session_id, patient_id

# Main function to run all tests
def main():
    print("Starting backend tests for newly implemented modules...")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("Authentication failed. Cannot proceed with tests.")
        return
    
    # Create a test patient to use across all tests
    try:
        patient_url = f"{API_URL}/patients"
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test.patient@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1980-01-01",
            "gender": "male",
            "address_line1": "123 Test Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        patient_response = requests.post(patient_url, json=patient_data, headers=headers)
        patient_response.raise_for_status()
        patient_result = patient_response.json()
        patient_id = patient_result["id"]
        print(f"Created shared test patient with ID: {patient_id}")
    except Exception as e:
        print(f"Error creating shared test patient: {str(e)}")
        patient_id = None
    
    # Run all tests
    test_referrals_management(token, patient_id)
    test_clinical_templates(token)
    test_quality_measures(token)
    test_patient_portal(token, patient_id)
    test_document_management(token, patient_id)
    test_telehealth_module(token, patient_id)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()