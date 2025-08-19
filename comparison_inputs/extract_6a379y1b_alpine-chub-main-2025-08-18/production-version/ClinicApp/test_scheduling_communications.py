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

# Test Authentication System to get admin token
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
    # Test 1: Initialize Admin User
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
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
    admin_token = None
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("Admin Login", True, result)
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    return admin_token

# Create a test patient
def create_test_patient():
    print("\n--- Creating Test Patient ---")
    
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1980-01-15",
            "gender": "male",
            "address_line1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        print_test_result("Create Test Patient", True, result)
        return patient_id
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Test Patient", False)
        return None

# Test Provider Management System
def test_provider_management(admin_token):
    print("\n--- Testing Provider Management System ---")
    
    # Test 1: Create Provider
    provider_id = None
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "first_name": "Robert",
            "last_name": "Wilson",
            "title": "Dr.",
            "specialties": ["Cardiology", "Internal Medicine"],
            "license_number": "MD12345",
            "npi_number": "1234567890",
            "email": "dr.wilson@clinichub.com",
            "phone": "+1-555-789-0123",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print_test_result("1. Create Provider", True, result)
    except Exception as e:
        print(f"Error creating provider: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("1. Create Provider", False)
    
    # Test 2: Get All Providers
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("2. Get All Providers", True, result)
    except Exception as e:
        print(f"Error getting providers: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("2. Get All Providers", False)
    
    # Test 3: Get Specific Provider
    if provider_id:
        try:
            url = f"{API_URL}/providers/{provider_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("3. Get Provider by ID", True, result)
        except Exception as e:
            print(f"Error getting provider by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("3. Get Provider by ID", False)
    
    # Test 4: Update Provider Information
    if provider_id:
        try:
            url = f"{API_URL}/providers/{provider_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "specialties": ["Cardiology", "Internal Medicine", "Hypertension"],
                "default_appointment_duration": 45
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("4. Update Provider Information", True, result)
        except Exception as e:
            print(f"Error updating provider: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("4. Update Provider Information", False)
    
    # Test 5: Create Provider Schedule
    if provider_id:
        try:
            url = f"{API_URL}/providers/{provider_id}/schedule"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
            
            response = requests.post(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("5. Create Provider Schedule", True, result)
        except Exception as e:
            print(f"Error creating provider schedule: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("5. Create Provider Schedule", False)
    
    # Test 6: Get Provider Schedule
    if provider_id:
        try:
            url = f"{API_URL}/providers/{provider_id}/schedule"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("6. Get Provider Schedule", True, result)
        except Exception as e:
            print(f"Error getting provider schedule: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("6. Get Provider Schedule", False)
    
    return provider_id

# Test Appointment Scheduling System
def test_appointment_scheduling(patient_id, provider_id, admin_token):
    print("\n--- Testing Appointment Scheduling System ---")
    
    # Test 1: Create Appointment
    appointment_id = None
    if provider_id and patient_id:
        try:
            url = f"{API_URL}/appointments"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "appointment_date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "consultation",
                "reason": "Initial cardiology consultation",
                "location": "Main Clinic",
                "scheduled_by": "admin"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            appointment_id = result["id"]
            print_test_result("1. Create Appointment", True, result)
        except Exception as e:
            print(f"Error creating appointment: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("1. Create Appointment", False)
    
    # Test 2: Get All Appointments
    try:
        url = f"{API_URL}/appointments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("2. Get All Appointments", True, result)
    except Exception as e:
        print(f"Error getting appointments: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("2. Get All Appointments", False)
    
    # Test 3: Get Specific Appointment
    if appointment_id:
        try:
            url = f"{API_URL}/appointments/{appointment_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("3. Get Appointment by ID", True, result)
        except Exception as e:
            print(f"Error getting appointment by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("3. Get Appointment by ID", False)
    
    # Test 4: Update Appointment Status
    if appointment_id:
        try:
            url = f"{API_URL}/appointments/{appointment_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "confirmed"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("4. Update Appointment Status", True, result)
        except Exception as e:
            print(f"Error updating appointment status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("4. Update Appointment Status", False)
    
    # Test 5: Cancel Appointment
    if appointment_id:
        try:
            url = f"{API_URL}/appointments/{appointment_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("5. Cancel Appointment", True, result)
        except Exception as e:
            print(f"Error canceling appointment: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("5. Cancel Appointment", False)
    
    # Test 6: Get Calendar View
    try:
        url = f"{API_URL}/appointments/calendar"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "view_type": "week",
            "start_date": date.today().isoformat()
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("6. Get Calendar View", True, result)
    except Exception as e:
        print(f"Error getting calendar view: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("6. Get Calendar View", False)
    
    return appointment_id

# Test Patient Communications System
def test_patient_communications(patient_id, admin_token):
    print("\n--- Testing Patient Communications System ---")
    
    # Test 1: Initialize Message Templates
    try:
        url = f"{API_URL}/communications/init-templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("1. Initialize Message Templates", True, result)
    except Exception as e:
        print(f"Error initializing message templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("1. Initialize Message Templates", False)
    
    # Test 2: Get All Templates
    template_id = None
    try:
        url = f"{API_URL}/communications/templates"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if len(result) > 0:
            template_id = result[0]["id"]
        
        print_test_result("2. Get All Templates", True, result)
    except Exception as e:
        print(f"Error getting templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("2. Get All Templates", False)
    
    # Test 3: Create New Template
    if not template_id:
        try:
            url = f"{API_URL}/communications/templates"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "name": "Lab Results Notification",
                "message_type": "test_results",
                "subject_template": "Your Lab Results from {clinic_name}",
                "content_template": "Dear {patient_name},\n\nYour recent lab results are now available. Please log in to your patient portal to view them or contact our office at {clinic_phone}.\n\nRegards,\n{provider_name}"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            template_id = result["id"]
            print_test_result("3. Create New Template", True, result)
        except Exception as e:
            print(f"Error creating template: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("3. Create New Template", False)
    
    # Test 4: Send Message to Patient
    message_id = None
    if patient_id and template_id:
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
                    "provider_name": "Dr. Admin"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            message_id = result["id"]
            print_test_result("4. Send Message to Patient", True, result)
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("4. Send Message to Patient", False)
    
    # Test 5: Get All Messages
    try:
        url = f"{API_URL}/communications/messages"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("5. Get All Messages", True, result)
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("5. Get All Messages", False)
    
    # Test 6: Get Patient-Specific Messages
    if patient_id:
        try:
            url = f"{API_URL}/communications/messages/patient/{patient_id}"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("6. Get Patient-Specific Messages", True, result)
        except Exception as e:
            print(f"Error getting patient messages: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("6. Get Patient-Specific Messages", False)
    
    # Test 7: Update Message Status
    if message_id:
        try:
            url = f"{API_URL}/communications/messages/{message_id}/status"
            headers = {"Authorization": f"Bearer {admin_token}"}
            params = {"status": "delivered"}
            
            response = requests.put(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("7. Update Message Status", True, result)
        except Exception as e:
            print(f"Error updating message status: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("7. Update Message Status", False)
    
    return template_id, message_id

def main():
    print("\n" + "=" * 80)
    print("TESTING SCHEDULING AND COMMUNICATIONS BACKEND API")
    print("=" * 80)
    
    # Get admin token
    admin_token = test_authentication()
    if not admin_token:
        print("Failed to get admin token. Aborting tests.")
        return
    
    # Create test patient
    patient_id = create_test_patient()
    if not patient_id:
        print("Failed to create test patient. Aborting tests.")
        return
    
    # Test Provider Management
    provider_id = test_provider_management(admin_token)
    
    # Test Appointment Scheduling
    if provider_id and patient_id:
        appointment_id = test_appointment_scheduling(patient_id, provider_id, admin_token)
    
    # Test Patient Communications
    if patient_id:
        test_patient_communications(patient_id, admin_token)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()