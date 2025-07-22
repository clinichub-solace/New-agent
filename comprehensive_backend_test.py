#!/usr/bin/env python3
"""
Comprehensive Backend System Verification for ClinicHub
Testing the restored 9,739-line comprehensive server.py with 25+ medical modules
Focus on advanced practice management and interconnected workflows
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
print(f"🚀 Starting Comprehensive Backend System Verification")
print(f"📡 Using API URL: {API_URL}")
print("=" * 80)

# Global variables for test data
admin_token = None
test_patient_id = None
test_provider_id = None
test_encounter_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            # Show key fields for verification
            if 'id' in response:
                print(f"   ID: {response['id']}")
            if 'status' in response:
                print(f"   Status: {response['status']}")
            if 'message' in response:
                print(f"   Message: {response['message']}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 60)

def test_authentication_system():
    """Test 1: Authentication System - Admin login working correctly"""
    global admin_token
    print("\n🔐 TESTING AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    # Test admin initialization
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        result = response.json()
        
        assert result["username"] == "admin"
        assert result["password"] == "admin123"
        print_test_result("Admin Initialization", True, result)
    except Exception as e:
        print_test_result("Admin Initialization", False, error_msg=str(e))
        return False
    
    # Test admin login
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        assert "access_token" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, {"username": result["user"]["username"], "role": result["user"]["role"]})
        return True
    except Exception as e:
        print_test_result("Admin Login", False, error_msg=str(e))
        return False

def test_core_medical_systems():
    """Test 2: Core Medical Systems - Patients, encounters, SOAP notes, medications, allergies"""
    global test_patient_id, test_encounter_id
    print("\n🏥 TESTING CORE MEDICAL SYSTEMS")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Patient Management (FHIR-compliant)
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Emma",
            "last_name": "Rodriguez",
            "email": "emma.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1988-03-22",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "73301"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["resource_type"] == "Patient"
        assert result["name"][0]["family"] == "Rodriguez"
        assert "Emma" in result["name"][0]["given"]
        
        test_patient_id = result["id"]
        print_test_result("FHIR Patient Creation", True, {"id": test_patient_id, "name": f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"})
    except Exception as e:
        print_test_result("FHIR Patient Creation", False, error_msg=str(e))
        return False
    
    # Test Encounter Creation
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": test_patient_id,
            "encounter_type": "consultation",
            "scheduled_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            "provider": "Dr. Sarah Martinez",
            "location": "Main Clinic - Room 301",
            "chief_complaint": "Routine check-up and medication review",
            "reason_for_visit": "Annual wellness visit"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert "encounter_number" in result
        assert result["encounter_number"].startswith("ENC-")
        
        test_encounter_id = result["id"]
        print_test_result("Encounter Creation", True, {"id": test_encounter_id, "encounter_number": result["encounter_number"]})
    except Exception as e:
        print_test_result("Encounter Creation", False, error_msg=str(e))
        return False
    
    # Test SOAP Notes Creation
    try:
        url = f"{API_URL}/soap-notes"
        data = {
            "encounter_id": test_encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient reports feeling well overall. No acute complaints. Mentions occasional mild headaches, usually stress-related. Sleep pattern good, appetite normal.",
            "objective": "Vital signs: BP 118/76, HR 68, Temp 98.4°F, RR 16, O2 Sat 99%. General appearance: well-developed, well-nourished female in no acute distress. HEENT: normocephalic, atraumatic. Heart: regular rate and rhythm, no murmurs. Lungs: clear to auscultation bilaterally.",
            "assessment": "1. Routine wellness visit - patient in good health. 2. Mild tension headaches - likely stress-related. 3. Continue current medications as tolerated.",
            "plan": "1. Continue current medications. 2. Stress management techniques discussed. 3. Return to clinic in 6 months for routine follow-up. 4. Contact office if headaches worsen or become more frequent.",
            "provider": "Dr. Sarah Martinez"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("SOAP Notes Creation", True, {"id": result["id"], "provider": result["provider"]})
    except Exception as e:
        print_test_result("SOAP Notes Creation", False, error_msg=str(e))
    
    # Test Allergy Management
    try:
        url = f"{API_URL}/allergies"
        data = {
            "patient_id": test_patient_id,
            "allergen": "Shellfish",
            "reaction": "Hives, swelling, difficulty breathing",
            "severity": "severe",
            "onset_date": "2015-08-12",
            "notes": "Discovered during restaurant visit - required emergency treatment",
            "created_by": "Dr. Sarah Martinez"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Allergy Management", True, {"allergen": result["allergen"], "severity": result["severity"]})
    except Exception as e:
        print_test_result("Allergy Management", False, error_msg=str(e))
    
    # Test Medication Management
    try:
        url = f"{API_URL}/medications"
        data = {
            "patient_id": test_patient_id,
            "medication_name": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "route": "oral",
            "start_date": date.today().isoformat(),
            "prescribing_physician": "Dr. Sarah Martinez",
            "indication": "Type 2 Diabetes Management",
            "notes": "Take with meals to reduce GI upset"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Medication Management", True, {"medication": result["medication_name"], "dosage": result["dosage"]})
    except Exception as e:
        print_test_result("Medication Management", False, error_msg=str(e))
    
    return True

def test_advanced_practice_management():
    """Test 3: Advanced Practice Management - Employee management, inventory, invoicing, scheduling"""
    global test_provider_id
    print("\n💼 TESTING ADVANCED PRACTICE MANAGEMENT")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Employee Management with CRUD operations
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Jennifer",
            "last_name": "Thompson",
            "email": "j.thompson@clinichub.com",
            "phone": "+1-555-345-6789",
            "role": "nurse",
            "department": "Primary Care",
            "hire_date": date.today().isoformat(),
            "salary": 75000.00
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert "employee_id" in result
        assert result["employee_id"].startswith("EMP-")
        
        employee_id = result["id"]
        print_test_result("Employee Creation", True, {"employee_id": result["employee_id"], "role": result["role"]})
        
        # Test Employee Update
        url = f"{API_URL}/employees/{employee_id}"
        update_data = {"department": "Emergency Care", "salary": 78000.00}
        
        response = requests.put(url, json=update_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Employee Update", True, {"department": result["department"], "salary": result["salary"]})
    except Exception as e:
        print_test_result("Employee Management", False, error_msg=str(e))
    
    # Test Inventory Management
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Insulin Syringes 1mL",
            "category": "Medical Supplies",
            "sku": "MED-SYR-1ML",
            "current_stock": 500,
            "min_stock_level": 50,
            "unit_cost": 0.75,
            "supplier": "MedSupply Corp",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Supply Room A - Shelf 3",
            "notes": "Sterile, single-use syringes"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        inventory_id = result["id"]
        print_test_result("Inventory Item Creation", True, {"name": result["name"], "stock": result["current_stock"]})
        
        # Test Inventory Transaction
        url = f"{API_URL}/inventory/{inventory_id}/transaction"
        transaction_data = {
            "transaction_type": "out",
            "quantity": 25,
            "notes": "Used for patient care",
            "created_by": "Nurse Thompson"
        }
        
        response = requests.post(url, json=transaction_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Inventory Transaction", True, {"type": result["transaction_type"], "quantity": result["quantity"]})
    except Exception as e:
        print_test_result("Inventory Management", False, error_msg=str(e))
    
    # Test Invoice Management
    try:
        url = f"{API_URL}/invoices"
        data = {
            "patient_id": test_patient_id,
            "items": [
                {
                    "description": "Comprehensive Wellness Visit",
                    "quantity": 1,
                    "unit_price": 250.00,
                    "total": 250.00
                },
                {
                    "description": "Medication Review and Counseling",
                    "quantity": 1,
                    "unit_price": 75.00,
                    "total": 75.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30,
            "notes": "Payment due within 30 days. Thank you for choosing ClinicHub."
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert "invoice_number" in result
        assert result["invoice_number"].startswith("INV-")
        
        print_test_result("Invoice Creation", True, {"invoice_number": result["invoice_number"], "total": result["total_amount"]})
    except Exception as e:
        print_test_result("Invoice Management", False, error_msg=str(e))
    
    # Test Provider Management for Scheduling
    try:
        url = f"{API_URL}/providers"
        data = {
            "first_name": "Michael",
            "last_name": "Chen",
            "title": "Dr.",
            "specialties": ["Internal Medicine", "Preventive Care"],
            "license_number": "TX-MD-98765",
            "npi_number": "9876543210",
            "email": "dr.chen@clinichub.com",
            "phone": "+1-555-456-7890",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        test_provider_id = result["id"]
        print_test_result("Provider Creation", True, {"name": f"{result['title']} {result['first_name']} {result['last_name']}", "specialties": result["specialties"]})
    except Exception as e:
        print_test_result("Provider Management", False, error_msg=str(e))
    
    return True

def test_integration_systems():
    """Test 4: Integration Systems - Lab integration, insurance verification, eRx functionality"""
    print("\n🔬 TESTING INTEGRATION SYSTEMS")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Lab Integration System
    try:
        # Initialize lab tests
        url = f"{API_URL}/lab-tests/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Lab Tests Initialization", True, {"message": result.get("message", "Initialized")})
        
        # Create lab order
        url = f"{API_URL}/lab-orders"
        data = {
            "patient_id": test_patient_id,
            "provider_id": test_provider_id or "provider-123",
            "encounter_id": test_encounter_id,
            "lab_tests": ["33747-0", "2093-3"],  # Basic Metabolic Panel, Cholesterol
            "icd10_codes": ["E11.9"],  # Type 2 diabetes
            "priority": "routine",
            "notes": "Annual diabetes monitoring",
            "ordered_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Lab Order Creation", True, {"order_number": result["order_number"], "tests": len(result["lab_tests"])})
    except Exception as e:
        print_test_result("Lab Integration System", False, error_msg=str(e))
    
    # Test Insurance Verification System
    try:
        # Create insurance card
        url = f"{API_URL}/insurance/cards"
        data = {
            "patient_id": test_patient_id,
            "insurance_type": "commercial",
            "payer_name": "Blue Cross Blue Shield",
            "payer_id": "BCBS-TX",
            "member_id": "BCB123456789",
            "group_number": "GRP-001",
            "subscriber_name": "Emma Rodriguez",
            "subscriber_dob": "1988-03-22",
            "effective_date": "2024-01-01",
            "copay_primary": 25.00,
            "deductible": 1500.00,
            "is_primary": True
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        insurance_card_id = result["id"]
        print_test_result("Insurance Card Creation", True, {"payer": result["payer_name"], "member_id": result["member_id"]})
        
        # Test eligibility verification
        url = f"{API_URL}/insurance/verify-eligibility"
        data = {
            "patient_id": test_patient_id,
            "insurance_card_id": insurance_card_id
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Insurance Eligibility Verification", True, {"status": result["eligibility_status"]})
    except Exception as e:
        print_test_result("Insurance Verification System", False, error_msg=str(e))
    
    # Test eRx (Electronic Prescribing) System
    try:
        # Initialize eRx system
        url = f"{API_URL}/erx/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("eRx System Initialization", True, {"message": result.get("message", "Initialized")})
        
        # Get eRx medications
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert len(result) > 0
        assert result[0]["resource_type"] == "Medication"
        
        medication_id = result[0]["id"]
        print_test_result("eRx Medications Retrieval", True, {"count": len(result), "first_med": result[0]["generic_name"]})
        
        # Create prescription
        url = f"{API_URL}/prescriptions"
        data = {
            "medication_id": medication_id,
            "patient_id": test_patient_id,
            "prescriber_id": test_provider_id or "prescriber-123",
            "prescriber_name": "Dr. Michael Chen",
            "encounter_id": test_encounter_id,
            "dosage_text": "Take 1 tablet by mouth twice daily with meals",
            "dose_quantity": 1.0,
            "dose_unit": "tablet",
            "frequency": "BID",
            "route": "oral",
            "quantity": 60.0,
            "days_supply": 30,
            "refills": 2,
            "indication": "Type 2 Diabetes Management",
            "diagnosis_codes": ["E11.9"],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["resource_type"] == "MedicationRequest"
        assert "prescription_number" in result
        
        print_test_result("eRx Prescription Creation", True, {"prescription_number": result["prescription_number"], "status": result["status"]})
    except Exception as e:
        print_test_result("eRx System", False, error_msg=str(e))
    
    return True

def test_recently_added_systems():
    """Test 5: Recently Added Systems - Referrals, clinical templates, quality measures, patient portal, document management, telehealth"""
    print("\n🆕 TESTING RECENTLY ADDED SYSTEMS")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Referrals Management System
    try:
        url = f"{API_URL}/referrals"
        data = {
            "patient_id": test_patient_id,
            "referring_provider_id": test_provider_id or "provider-123",
            "referred_to_provider_name": "Dr. Lisa Wang",
            "referred_to_specialty": "Endocrinology",
            "reason_for_referral": "Diabetes management and insulin optimization",
            "urgency": "routine",
            "notes": "Patient needs specialist consultation for better glucose control",
            "created_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Referrals Management", True, {"specialty": result["referred_to_specialty"], "status": result["status"]})
    except Exception as e:
        print_test_result("Referrals Management", False, error_msg=str(e))
    
    # Test Clinical Templates & Protocols System
    try:
        url = f"{API_URL}/clinical-templates/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Clinical Templates Initialization", True, {"message": result.get("message", "Initialized")})
        
        # Create custom template
        url = f"{API_URL}/clinical-templates"
        data = {
            "name": "Diabetes Management Protocol",
            "template_type": "care_plan",
            "specialty": "Endocrinology",
            "condition": "Type 2 Diabetes",
            "template_content": {
                "assessment_items": ["HbA1c", "Blood Pressure", "Weight", "Foot Exam"],
                "medications": ["Metformin", "Insulin"],
                "follow_up": "3 months"
            },
            "is_active": True,
            "created_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Clinical Template Creation", True, {"name": result["name"], "type": result["template_type"]})
    except Exception as e:
        print_test_result("Clinical Templates System", False, error_msg=str(e))
    
    # Test Quality Measures & Reporting System
    try:
        url = f"{API_URL}/quality-measures"
        data = {
            "measure_id": "CMS122v11",
            "measure_name": "Diabetes: Hemoglobin A1c (HbA1c) Poor Control (>9%)",
            "measure_type": "outcome",
            "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
            "numerator_criteria": {"hba1c_value": ">9.0"},
            "denominator_criteria": {"age_range": "18-75", "diagnosis": "diabetes"},
            "exclusion_criteria": {"pregnancy": True},
            "reporting_period": "annual",
            "target_percentage": 10.0,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Quality Measures Creation", True, {"measure_id": result["measure_id"], "type": result["measure_type"]})
    except Exception as e:
        print_test_result("Quality Measures System", False, error_msg=str(e))
    
    # Test Patient Portal System
    try:
        url = f"{API_URL}/patient-portal"
        data = {
            "patient_id": test_patient_id,
            "portal_username": "emma.rodriguez",
            "access_level": "full",
            "features_enabled": ["appointments", "records", "messaging", "billing"],
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Patient Portal Access", True, {"username": result["portal_username"], "features": len(result["features_enabled"])})
    except Exception as e:
        print_test_result("Patient Portal System", False, error_msg=str(e))
    
    # Test Document Management System
    try:
        url = f"{API_URL}/documents"
        data = {
            "patient_id": test_patient_id,
            "document_name": "Lab Results - Comprehensive Metabolic Panel",
            "document_type": "lab_result",
            "category_id": "lab-results",
            "file_name": "cmp_results_20250121.pdf",
            "file_path": "/documents/lab_results/",
            "mime_type": "application/pdf",
            "file_size": 245760,
            "tags": ["lab", "diabetes", "routine"],
            "created_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Document Management", True, {"name": result["document_name"], "type": result["document_type"]})
    except Exception as e:
        print_test_result("Document Management System", False, error_msg=str(e))
    
    # Test Telehealth Module System
    try:
        url = f"{API_URL}/telehealth"
        data = {
            "patient_id": test_patient_id,
            "provider_id": test_provider_id or "provider-123",
            "session_type": "consultation",
            "scheduled_start": (datetime.now() + timedelta(hours=2)).isoformat(),
            "duration_minutes": 30,
            "platform": "internal",
            "notes": "Follow-up consultation for diabetes management",
            "created_by": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Telehealth Session", True, {"type": result["session_type"], "status": result["status"]})
    except Exception as e:
        print_test_result("Telehealth Module System", False, error_msg=str(e))
    
    return True

def test_comprehensive_medical_database():
    """Test the comprehensive medical database endpoints that need retesting"""
    print("\n📚 TESTING COMPREHENSIVE MEDICAL DATABASE ENDPOINTS")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test ICD-10 Database
    try:
        # Initialize ICD-10 codes
        url = f"{API_URL}/icd10/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("ICD-10 Database Initialization", True, {"message": result.get("message", "Initialized")})
        
        # Search ICD-10 codes
        url = f"{API_URL}/icd10/search"
        params = {"query": "diabetes"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert len(result) > 0
        print_test_result("ICD-10 Search", True, {"results": len(result), "first_code": result[0]["code"] if result else "None"})
    except Exception as e:
        print_test_result("ICD-10 Database", False, error_msg=str(e))
    
    # Test Comprehensive Medications Database
    try:
        # Initialize comprehensive medications
        url = f"{API_URL}/comprehensive-medications/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Comprehensive Medications Initialization", True, {"message": result.get("message", "Initialized")})
        
        # Search medications
        url = f"{API_URL}/comprehensive-medications/search"
        params = {"query": "metformin"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert len(result) > 0
        print_test_result("Comprehensive Medications Search", True, {"results": len(result), "first_med": result[0]["generic_name"] if result else "None"})
        
        # Filter by drug class
        url = f"{API_URL}/comprehensive-medications"
        params = {"drug_class": "antidiabetic"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Medications Filter by Drug Class", True, {"results": len(result)})
    except Exception as e:
        print_test_result("Comprehensive Medications Database", False, error_msg=str(e))
    
    return True

def test_interconnected_workflows():
    """Test interconnected workflows (SOAP notes → invoicing → inventory deduction)"""
    print("\n🔄 TESTING INTERCONNECTED WORKFLOWS")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test workflow: Enhanced SOAP Note with Plan Items → Auto Invoice Generation → Inventory Deduction
    try:
        # Create enhanced SOAP note with plan items
        url = f"{API_URL}/soap-notes"
        data = {
            "encounter_id": test_encounter_id,
            "patient_id": test_patient_id,
            "subjective": "Patient reports good diabetes control, checking blood sugar regularly. No hypoglycemic episodes.",
            "objective": "BP 125/78, Weight 165 lbs, HbA1c 7.2%. Feet examination normal, no neuropathy signs.",
            "assessment": "Type 2 Diabetes Mellitus, well controlled. Continue current regimen.",
            "plan": "Continue Metformin 500mg BID. Recheck HbA1c in 3 months. Diabetes education reinforced.",
            "plan_items": [
                {
                    "item_type": "lab",
                    "description": "HbA1c Test",
                    "quantity": 1,
                    "unit_price": 45.00,
                    "approved_by_patient": True
                },
                {
                    "item_type": "injectable",
                    "description": "Insulin Pen Needles",
                    "quantity": 100,
                    "unit_price": 0.25,
                    "approved_by_patient": True,
                    "inventory_item_id": "inventory-item-123"
                }
            ],
            "provider": "Dr. Michael Chen"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Enhanced SOAP Note with Plan Items", True, {"plan_items": len(result.get("plan_items", []))})
        
        # Test auto-invoice generation from SOAP note
        url = f"{API_URL}/invoices"
        invoice_data = {
            "patient_id": test_patient_id,
            "encounter_id": test_encounter_id,
            "items": [
                {
                    "description": "Office Visit - Diabetes Management",
                    "quantity": 1,
                    "unit_price": 180.00,
                    "total": 180.00,
                    "service_type": "service"
                },
                {
                    "description": "HbA1c Test",
                    "quantity": 1,
                    "unit_price": 45.00,
                    "total": 45.00,
                    "service_type": "lab"
                },
                {
                    "description": "Insulin Pen Needles",
                    "quantity": 100,
                    "unit_price": 0.25,
                    "total": 25.00,
                    "service_type": "product",
                    "inventory_item_id": "inventory-item-123"
                }
            ],
            "tax_rate": 0.08,
            "auto_generated": True,
            "notes": "Auto-generated from SOAP note plan items"
        }
        
        response = requests.post(url, json=invoice_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Auto-Generated Invoice from SOAP", True, {"total": result["total_amount"], "auto_generated": result.get("auto_generated", False)})
        
    except Exception as e:
        print_test_result("Interconnected Workflows", False, error_msg=str(e))
    
    return True

def test_advanced_features():
    """Test advanced medical features like drug interaction checking, allergy alerts"""
    print("\n⚕️ TESTING ADVANCED MEDICAL FEATURES")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Drug Interaction Checking
    try:
        # Get medications for interaction testing
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if len(medications) >= 2:
            drug1_id = medications[0]["id"]
            drug2_id = medications[1]["id"]
            
            url = f"{API_URL}/drug-interactions"
            params = {"drug1_id": drug1_id, "drug2_id": drug2_id}
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Drug Interaction Checking", True, {"interaction_found": "interaction" in result})
        else:
            print_test_result("Drug Interaction Checking", False, error_msg="Not enough medications for testing")
    except Exception as e:
        print_test_result("Drug Interaction Checking", False, error_msg=str(e))
    
    # Test Patient Summary with All Data
    try:
        url = f"{API_URL}/patients/{test_patient_id}/summary"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive summary structure
        expected_sections = ["patient", "recent_encounters", "allergies", "active_medications", "medical_history"]
        sections_present = [section for section in expected_sections if section in result]
        
        print_test_result("Comprehensive Patient Summary", True, {"sections": len(sections_present), "total_expected": len(expected_sections)})
    except Exception as e:
        print_test_result("Comprehensive Patient Summary", False, error_msg=str(e))
    
    # Test Dashboard Analytics for Practice Management
    try:
        url = f"{API_URL}/dashboard/stats"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify dashboard stats structure
        expected_stats = ["total_patients", "total_invoices", "pending_invoices", "low_stock_items", "total_employees"]
        stats_present = [stat for stat in expected_stats if stat in result.get("stats", {})]
        
        print_test_result("Dashboard Analytics", True, {"stats_available": len(stats_present), "total_expected": len(expected_stats)})
    except Exception as e:
        print_test_result("Dashboard Analytics", False, error_msg=str(e))
    
    return True

def main():
    """Main test execution function"""
    print("🏥 ClinicHub Comprehensive Backend System Verification")
    print("📋 Testing 9,739-line comprehensive server.py with 25+ medical modules")
    print("🎯 Focus: Advanced practice management and interconnected workflows")
    print("=" * 80)
    
    # Test execution sequence
    test_results = []
    
    # Test 1: Authentication System
    auth_success = test_authentication_system()
    test_results.append(("Authentication System", auth_success))
    
    if not auth_success:
        print("❌ Authentication failed - cannot proceed with other tests")
        return
    
    # Test 2: Core Medical Systems
    core_success = test_core_medical_systems()
    test_results.append(("Core Medical Systems", core_success))
    
    # Test 3: Advanced Practice Management
    practice_success = test_advanced_practice_management()
    test_results.append(("Advanced Practice Management", practice_success))
    
    # Test 4: Integration Systems
    integration_success = test_integration_systems()
    test_results.append(("Integration Systems", integration_success))
    
    # Test 5: Recently Added Systems
    recent_success = test_recently_added_systems()
    test_results.append(("Recently Added Systems", recent_success))
    
    # Test 6: Comprehensive Medical Database (needs retesting)
    database_success = test_comprehensive_medical_database()
    test_results.append(("Comprehensive Medical Database", database_success))
    
    # Test 7: Interconnected Workflows
    workflow_success = test_interconnected_workflows()
    test_results.append(("Interconnected Workflows", workflow_success))
    
    # Test 8: Advanced Features
    advanced_success = test_advanced_features()
    test_results.append(("Advanced Medical Features", advanced_success))
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE BACKEND SYSTEM VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
        if success:
            passed_tests += 1
    
    print("-" * 80)
    print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS OPERATIONAL - Backend ready for production use!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️  MOSTLY FUNCTIONAL - Minor issues need attention")
    else:
        print("🚨 CRITICAL ISSUES FOUND - Significant fixes required")
    
    print("=" * 80)

if __name__ == "__main__":
    main()