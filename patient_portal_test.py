#!/usr/bin/env python3
"""
Comprehensive Patient Portal System Testing
Tests all patient portal endpoints as requested in the review.
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

# Use local backend URL for testing
BACKEND_URL = "http://localhost:8001"

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

def get_admin_token():
    """Get admin authentication token"""
    try:
        # Try to initialize admin user (ignore if already exists)
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        # Don't raise for status here as admin might already exist
        
        # Login as admin
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["access_token"]
    except Exception as e:
        print(f"Error getting admin token: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return None

def create_test_patient(admin_token):
    """Create a test patient for portal testing"""
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-15",
            "gender": "female",
            "address_line1": "456 Patient Portal Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Test Patient", True, result)
        return result["id"]
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        print_test_result("Create Test Patient", False)
        return None

def test_patient_portal_authentication():
    """Test Patient Portal Authentication endpoints"""
    print("\n=== TESTING PATIENT PORTAL AUTHENTICATION ===")
    
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return None, None
    
    # Create test patient first
    patient_id = create_test_patient(admin_token)
    if not patient_id:
        print("❌ Cannot proceed without test patient")
        return None, None
    
    portal_user_id = None
    portal_token = None
    
    # Test 1: Patient Portal Registration
    try:
        # Use unique username to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        username = f"emily_rodriguez_{unique_id}"
        email = f"emily.rodriguez.{unique_id}@example.com"
        
        url = f"{API_URL}/patient-portal/register"
        data = {
            "patient_id": patient_id,
            "username": username,
            "email": email,
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "date_of_birth": "1990-08-15"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Registration successful, user ID not returned in this response
        portal_user_id = "registered"  # We'll get the actual ID after login
        print_test_result("Patient Portal Registration", True, result)
    except Exception as e:
        print(f"Error in patient portal registration: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Portal Registration", False)
        return None, None
    
    # Test 2: Patient Portal Login
    try:
        url = f"{API_URL}/patient-portal/login"
        data = {
            "username": username,
            "password": "SecurePass123!"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify login response structure
        assert "access_token" in result
        assert "token_type" in result
        assert "patient" in result
        
        portal_token = result["access_token"]
        print_test_result("Patient Portal Login", True, result)
    except Exception as e:
        print(f"Error in patient portal login: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Portal Login", False)
        return None, None
    
    # Test 3: Patient Portal Logout
    if portal_token:
        try:
            url = f"{API_URL}/patient-portal/logout"
            headers = {"Authorization": f"Bearer {portal_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Patient Portal Logout", True, result)
        except Exception as e:
            print(f"Error in patient portal logout: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Patient Portal Logout", False)
    
    return patient_id, portal_token

def test_medical_records_access(patient_id, portal_token, admin_token):
    """Test Medical Records Access endpoints"""
    print("\n=== TESTING MEDICAL RECORDS ACCESS ===")
    
    if not portal_token:
        print("❌ Cannot test medical records without portal token")
        return
    
    # First create some medical data for the patient
    create_test_medical_data(patient_id, admin_token)
    
    # Test 1: Patient Medical Records Access
    try:
        url = f"{API_URL}/patient-portal/medical-records"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify medical records structure
        assert "encounters" in result or "medical_history" in result or "allergies" in result
        
        print_test_result("Patient Medical Records Access", True, result)
    except Exception as e:
        print(f"Error accessing medical records: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Medical Records Access", False)
    
    # Test 2: Patient Appointments View
    try:
        url = f"{API_URL}/patient-portal/appointments"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Patient Appointments View", True, result)
    except Exception as e:
        print(f"Error accessing appointments: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Appointments View", False)
    
    # Test 3: Patient Documents Access
    try:
        url = f"{API_URL}/patient-portal/documents"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Patient Documents Access", True, result)
    except Exception as e:
        print(f"Error accessing documents: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Documents Access", False)

def test_patient_communication(patient_id, portal_token, admin_token):
    """Test Patient Communication endpoints"""
    print("\n=== TESTING PATIENT COMMUNICATION ===")
    
    if not portal_token:
        print("❌ Cannot test communication without portal token")
        return
    
    message_id = None
    
    # Test 1: Patient Messages Retrieval
    try:
        url = f"{API_URL}/patient-portal/messages"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Patient Messages Retrieval", True, result)
    except Exception as e:
        print(f"Error retrieving messages: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Messages Retrieval", False)
    
    # Test 2: Send Message from Patient
    try:
        url = f"{API_URL}/patient-portal/messages"
        headers = {"Authorization": f"Bearer {portal_token}"}
        data = {
            "subject": "Question about my recent lab results",
            "message": "Hi Dr. Smith, I have some questions about my recent blood work results. Could you please explain what the elevated glucose levels mean?",
            "message_type": "general",
            "priority": "normal"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        message_id = result.get("id")
        print_test_result("Send Message from Patient", True, result)
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Send Message from Patient", False)
    
    # Test 3: Message Threading and Reply Functionality
    if message_id:
        try:
            url = f"{API_URL}/patient-portal/messages"
            headers = {"Authorization": f"Bearer {portal_token}"}
            data = {
                "subject": "Re: Question about my recent lab results",
                "message": "Thank you for your quick response. I understand now. Should I schedule a follow-up appointment?",
                "message_type": "general",
                "priority": "normal",
                "reply_to_message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Message Threading and Reply", True, result)
        except Exception as e:
            print(f"Error with message reply: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Message Threading and Reply", False)

def test_appointment_management(patient_id, portal_token, admin_token):
    """Test Appointment Management endpoints"""
    print("\n=== TESTING APPOINTMENT MANAGEMENT ===")
    
    if not portal_token:
        print("❌ Cannot test appointments without portal token")
        return
    
    # First create a provider for appointments
    provider_id = create_test_provider(admin_token)
    if not provider_id:
        print("❌ Cannot test appointments without provider")
        return
    
    appointment_request_id = None
    
    # Test 1: Patient Appointment Requests
    try:
        url = f"{API_URL}/patient-portal/appointment-requests"
        headers = {"Authorization": f"Bearer {portal_token}"}
        data = {
            "provider_id": provider_id,
            "appointment_type": "consultation",
            "preferred_date": (date.today() + timedelta(days=7)).isoformat(),
            "preferred_time": "10:00",
            "alternate_dates": [
                (date.today() + timedelta(days=8)).isoformat(),
                (date.today() + timedelta(days=9)).isoformat()
            ],
            "reason": "Follow-up consultation for recent test results",
            "urgency": "routine"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        appointment_request_id = result.get("id")
        print_test_result("Patient Appointment Request", True, result)
    except Exception as e:
        print(f"Error creating appointment request: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Appointment Request", False)
    
    # Test 2: Appointment Request Approval Workflow (Admin side)
    if appointment_request_id:
        try:
            # Simulate staff approving the request
            url = f"{API_URL}/appointment-requests/{appointment_request_id}/approve"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "approved_date": (date.today() + timedelta(days=7)).isoformat(),
                "approved_time": "10:00",
                "staff_notes": "Approved for requested time slot"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Appointment Request Approval", True, result)
        except Exception as e:
            print(f"Error approving appointment request: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Appointment Request Approval", False)
    
    # Test 3: Integration with Main Appointment System
    try:
        # Check if appointment was created in main system
        url = f"{API_URL}/appointments/patient/{patient_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Integration with Main Appointment System", True, result)
    except Exception as e:
        print(f"Error checking appointment integration: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Integration with Main Appointment System", False)

def test_prescription_management(patient_id, portal_token, admin_token):
    """Test Prescription Management endpoints"""
    print("\n=== TESTING PRESCRIPTION MANAGEMENT ===")
    
    if not portal_token:
        print("❌ Cannot test prescriptions without portal token")
        return
    
    # First create a prescription for the patient
    prescription_id = create_test_prescription(patient_id, admin_token)
    
    # Test 1: Prescription Refill Requests
    try:
        url = f"{API_URL}/patient-portal/prescription-refills"
        headers = {"Authorization": f"Bearer {portal_token}"}
        data = {
            "original_prescription_id": prescription_id,
            "medication_name": "Lisinopril 10mg",
            "dosage": "10mg once daily",
            "quantity_requested": 30,
            "pharmacy_name": "CVS Pharmacy",
            "pharmacy_phone": "555-123-4567",
            "reason": "Running low on medication",
            "urgency": "routine"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Prescription Refill Request", True, result)
    except Exception as e:
        print(f"Error creating refill request: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Prescription Refill Request", False)
    
    # Test 2: Refill Request Processing Workflow
    try:
        # Get refill requests for processing
        url = f"{API_URL}/prescription-refills/pending"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Refill Request Processing Workflow", True, result)
    except Exception as e:
        print(f"Error processing refill requests: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Refill Request Processing Workflow", False)

def test_billing_integration(patient_id, portal_token, admin_token):
    """Test Billing Integration endpoints"""
    print("\n=== TESTING BILLING INTEGRATION ===")
    
    if not portal_token:
        print("❌ Cannot test billing without portal token")
        return
    
    # First create an invoice for the patient
    invoice_id = create_test_invoice(patient_id, admin_token)
    
    # Test 1: Patient Billing Information Access
    try:
        url = f"{API_URL}/patient-portal/billing"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify billing information structure
        assert "invoices" in result or "balance" in result
        
        print_test_result("Patient Billing Information Access", True, result)
    except Exception as e:
        print(f"Error accessing billing information: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Billing Information Access", False)
    
    # Test 2: Invoice Viewing and Payment Status
    if invoice_id:
        try:
            url = f"{API_URL}/patient-portal/billing/invoice/{invoice_id}"
            headers = {"Authorization": f"Bearer {portal_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify invoice details
            assert "invoice_number" in result
            assert "total_amount" in result
            assert "status" in result
            
            print_test_result("Invoice Viewing and Payment Status", True, result)
        except Exception as e:
            print(f"Error viewing invoice: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Invoice Viewing and Payment Status", False)

def test_telehealth_integration(patient_id, portal_token, admin_token):
    """Test Telehealth Integration endpoints"""
    print("\n=== TESTING TELEHEALTH INTEGRATION ===")
    
    if not portal_token:
        print("❌ Cannot test telehealth without portal token")
        return
    
    # First create a telehealth session
    session_id = create_test_telehealth_session(patient_id, admin_token)
    
    # Test 1: Patient Telehealth Sessions Access
    try:
        url = f"{API_URL}/patient-portal/telehealth-sessions"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Patient Telehealth Sessions Access", True, result)
    except Exception as e:
        print(f"Error accessing telehealth sessions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Telehealth Sessions Access", False)
    
    # Test 2: Join Telehealth Session
    if session_id:
        try:
            url = f"{API_URL}/patient-portal/telehealth-sessions/{session_id}/join"
            headers = {"Authorization": f"Bearer {portal_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify session join response
            assert "session_url" in result or "room_id" in result
            
            print_test_result("Join Telehealth Session", True, result)
        except Exception as e:
            print(f"Error joining telehealth session: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Join Telehealth Session", False)

def test_patient_preferences(patient_id, portal_token):
    """Test Patient Preferences endpoints"""
    print("\n=== TESTING PATIENT PREFERENCES ===")
    
    if not portal_token:
        print("❌ Cannot test preferences without portal token")
        return
    
    # Test 1: Get Patient Preferences
    try:
        url = f"{API_URL}/patient-portal/preferences"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify preferences structure
        assert "email_notifications" in result or "sms_notifications" in result
        
        print_test_result("Get Patient Preferences", True, result)
    except Exception as e:
        print(f"Error getting preferences: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Preferences", False)
    
    # Test 2: Update Patient Preferences
    try:
        url = f"{API_URL}/patient-portal/preferences"
        headers = {"Authorization": f"Bearer {portal_token}"}
        data = {
            "email_notifications": True,
            "sms_notifications": False,
            "appointment_reminders": True,
            "lab_result_notifications": True,
            "prescription_reminders": True,
            "marketing_communications": False,
            "preferred_communication_method": "email",
            "language_preference": "en",
            "timezone": "America/Chicago"
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Update Patient Preferences", True, result)
    except Exception as e:
        print(f"Error updating preferences: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Update Patient Preferences", False)

def test_activity_tracking(patient_id, portal_token):
    """Test Activity Tracking endpoints"""
    print("\n=== TESTING ACTIVITY TRACKING ===")
    
    if not portal_token:
        print("❌ Cannot test activity tracking without portal token")
        return
    
    # Test 1: Get Patient Activity Log
    try:
        url = f"{API_URL}/patient-portal/activity"
        headers = {"Authorization": f"Bearer {portal_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify activity log structure
        assert isinstance(result, list) or "activities" in result
        
        print_test_result("Get Patient Activity Log", True, result)
    except Exception as e:
        print(f"Error getting activity log: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Activity Log", False)

# Helper functions to create test data
def create_test_medical_data(patient_id, admin_token):
    """Create test medical data for the patient"""
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create an encounter
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Sarah Johnson",
            "location": "Main Clinic",
            "chief_complaint": "Routine follow-up",
            "reason_for_visit": "Annual check-up"
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Create an allergy
        url = f"{API_URL}/allergies"
        data = {
            "patient_id": patient_id,
            "allergen": "Penicillin",
            "reaction": "Rash",
            "severity": "moderate",
            "onset_date": "2020-01-01",
            "created_by": "admin"
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error creating test medical data: {str(e)}")

def create_test_provider(admin_token):
    """Create a test provider"""
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "title": "Dr.",
            "specialties": ["Family Medicine"],
            "email": "dr.johnson@clinichub.com",
            "phone": "555-123-4567"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["id"]
    except Exception as e:
        print(f"Error creating test provider: {str(e)}")
        return None

def create_test_prescription(patient_id, admin_token):
    """Create a test prescription"""
    try:
        # First initialize eRx system
        url = f"{API_URL}/erx/init"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        # Get medications
        url = f"{API_URL}/erx/medications"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if medications:
            medication_id = medications[0]["id"]
            
            # Create prescription
            url = f"{API_URL}/prescriptions"
            data = {
                "medication_id": medication_id,
                "patient_id": patient_id,
                "prescriber_id": "prescriber-123",
                "prescriber_name": "Dr. Sarah Johnson",
                "dosage_text": "Take 1 tablet by mouth once daily",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "DAILY",
                "route": "oral",
                "quantity": 30.0,
                "days_supply": 30,
                "refills": 2,
                "indication": "Hypertension",
                "created_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["id"]
    except Exception as e:
        print(f"Error creating test prescription: {str(e)}")
        return None

def create_test_invoice(patient_id, admin_token):
    """Create a test invoice"""
    try:
        url = f"{API_URL}/invoices"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Office Visit",
                    "quantity": 1,
                    "unit_price": 150.00,
                    "total": 150.00
                }
            ],
            "tax_rate": 0.08,
            "due_days": 30
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["id"]
    except Exception as e:
        print(f"Error creating test invoice: {str(e)}")
        return None

def create_test_telehealth_session(patient_id, admin_token):
    """Create a test telehealth session"""
    try:
        provider_id = create_test_provider(admin_token)
        if not provider_id:
            return None
            
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "session_type": "video_consultation",
            "title": "Follow-up Consultation",
            "scheduled_start": (datetime.now() + timedelta(hours=1)).isoformat(),
            "duration_minutes": 30
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["id"]
    except Exception as e:
        print(f"Error creating test telehealth session: {str(e)}")
        return None

def main():
    """Main test execution"""
    print("🏥 COMPREHENSIVE PATIENT PORTAL SYSTEM TESTING")
    print("=" * 80)
    
    # Test 1: Patient Portal Authentication
    patient_id, portal_token = test_patient_portal_authentication()
    
    if not patient_id or not portal_token:
        print("❌ Cannot proceed with other tests without patient portal authentication")
        return
    
    # Get admin token for supporting operations
    admin_token = get_admin_token()
    
    # Test 2: Medical Records Access
    test_medical_records_access(patient_id, portal_token, admin_token)
    
    # Test 3: Patient Communication
    test_patient_communication(patient_id, portal_token, admin_token)
    
    # Test 4: Appointment Management
    test_appointment_management(patient_id, portal_token, admin_token)
    
    # Test 5: Prescription Management
    test_prescription_management(patient_id, portal_token, admin_token)
    
    # Test 6: Billing Integration
    test_billing_integration(patient_id, portal_token, admin_token)
    
    # Test 7: Telehealth Integration
    test_telehealth_integration(patient_id, portal_token, admin_token)
    
    # Test 8: Patient Preferences
    test_patient_preferences(patient_id, portal_token)
    
    # Test 9: Activity Tracking
    test_activity_tracking(patient_id, portal_token)
    
    print("\n" + "=" * 80)
    print("🏥 PATIENT PORTAL TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()