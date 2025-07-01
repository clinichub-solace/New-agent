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

# Test Authentication System to get a token
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        if response.status_code == 400:
            # Admin already exists, try to login
            print("Admin already exists, trying to login...")
        else:
            response.raise_for_status()
            result = response.json()
            print_test_result("Initialize Admin User", True, result)
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Admin User", False)
    
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
        assert "expires_in" in result
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

# Create a test patient
def create_test_patient(admin_token):
    print("\n--- Creating Test Patient ---")
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1980-01-15",
            "gender": "male",
            "address_line1": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Test Patient", True, result)
        return result["id"]
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Patient", False)
        return None

# Create a test provider
def create_test_provider(admin_token):
    print("\n--- Creating Test Provider ---")
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "title": "Dr.",
            "specialties": ["Family Medicine"],
            "license_number": "MD12345",
            "npi_number": "1234567890",
            "email": "dr.smith@example.com",
            "phone": "+1-555-987-6543",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Test Provider", True, result)
        return result["id"]
    except Exception as e:
        print(f"Error creating test provider: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Provider", False)
        return None

# Create a test appointment
def create_test_appointment(admin_token, patient_id, provider_id):
    print("\n--- Creating Test Appointment ---")
    try:
        # First get patient and provider details to include names
        patient_url = f"{API_URL}/patients/{patient_id}"
        provider_url = f"{API_URL}/providers/{provider_id}"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        patient_response = requests.get(patient_url, headers=headers)
        patient_response.raise_for_status()
        patient_data = patient_response.json()
        
        provider_response = requests.get(provider_url, headers=headers)
        provider_response.raise_for_status()
        provider_data = provider_response.json()
        
        # Extract patient name
        patient_name = ""
        if "name" in patient_data and len(patient_data["name"]) > 0:
            name_obj = patient_data["name"][0]
            given = name_obj.get("given", [""])[0] if name_obj.get("given") else ""
            family = name_obj.get("family", "")
            patient_name = f"{given} {family}".strip()
        
        # Extract provider name
        provider_name = f"{provider_data['title']} {provider_data['first_name']} {provider_data['last_name']}".strip()
        
        url = f"{API_URL}/appointments"
        data = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "provider_id": provider_id,
            "provider_name": provider_name,
            "appointment_date": date.today().isoformat(),
            "start_time": "10:00",
            "end_time": "10:30",
            "appointment_type": "consultation",
            "reason": "Initial consultation",
            "location": "Main Clinic",
            "scheduled_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Create Test Appointment", True, result)
        return result["id"]
    except Exception as e:
        print(f"Error creating test appointment: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Appointment", False)
        return None

# Test 1: Appointment Status Update
def test_appointment_status_update(admin_token, appointment_id):
    print("\n--- Testing Appointment Status Update ---")
    try:
        url = f"{API_URL}/appointments/{appointment_id}/status"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {"status": "confirmed"}
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Update Appointment Status", True, result)
        return True
    except Exception as e:
        print(f"Error updating appointment status: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Update Appointment Status", False)
        return False

# Test 2: Calendar View
def test_calendar_view(admin_token):
    print("\n--- Testing Calendar View ---")
    try:
        url = f"{API_URL}/appointments/calendar"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "date": "2025-01-15",
            "view": "week"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Calendar View", True, result)
        return True
    except Exception as e:
        print(f"Error getting calendar view: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Calendar View", False)
        return False

# Test 3: Communications Templates
def test_communications_templates(admin_token):
    print("\n--- Testing Communications Templates ---")
    
    # First initialize templates
    try:
        url = f"{API_URL}/communications/init-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Communication Templates", True, result)
    except Exception as e:
        print(f"Error initializing communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Communication Templates", False)
    
    # Then get templates
    try:
        url = f"{API_URL}/communications/templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Communication Templates", True, result)
        return True, result[0]["id"] if result else None
    except Exception as e:
        print(f"Error getting communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Communication Templates", False)
        return False, None

# Test 4: Message Sending
def test_message_sending(admin_token, patient_id, template_id):
    print("\n--- Testing Message Sending ---")
    try:
        url = f"{API_URL}/communications/send"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "patient_id": patient_id,
            "template_id": template_id,
            "sender_id": "admin",
            "sender_name": "Dr. Admin",
            "template_variables": {
                "clinic_name": "ClinicHub Medical Center",
                "clinic_phone": "555-123-4567",
                "provider_name": "Dr. Admin",
                "appointment_date": "January 20, 2025",
                "appointment_time": "10:00 AM"
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Send Message to Patient", True, result)
        return True
    except Exception as e:
        print(f"Error sending message to patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Send Message to Patient", False)
        return False

def main():
    print("\n" + "=" * 80)
    print("TESTING FIXED BACKEND API ENDPOINTS")
    print("=" * 80)
    
    # Get authentication token
    admin_token = test_authentication()
    if not admin_token:
        print("Failed to authenticate. Cannot proceed with tests.")
        return
    
    # Create test data
    patient_id = create_test_patient(admin_token)
    provider_id = create_test_provider(admin_token)
    
    if not patient_id or not provider_id:
        print("Failed to create test data. Cannot proceed with tests.")
        return
    
    appointment_id = create_test_appointment(admin_token, patient_id, provider_id)
    if not appointment_id:
        print("Failed to create test appointment. Cannot proceed with appointment status test.")
    else:
        # Test 1: Appointment Status Update
        test_appointment_status_update(admin_token, appointment_id)
    
    # Test 2: Calendar View
    test_calendar_view(admin_token)
    
    # Test 3: Communications Templates
    templates_success, template_id = test_communications_templates(admin_token)
    
    # Test 4: Message Sending
    if templates_success and template_id and patient_id:
        test_message_sending(admin_token, patient_id, template_id)
    else:
        print("Cannot test message sending without templates or patient.")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()