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
    
    # Login with Admin Credentials
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
        return admin_token
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
        return None

# Test 1: Calendar View with proper parameters
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
        
        # Let's try with today's date
        try:
            print("Trying with today's date...")
            params = {
                "date": date.today().isoformat(),
                "view": "week"
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Calendar View (Today)", True, result)
            return True
        except Exception as e:
            print(f"Error getting calendar view with today's date: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Calendar View (Today)", False)
            return False

# Test 2: Communications Templates
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
        template_id = result[0]["id"] if result else None
        return True, template_id
    except Exception as e:
        print(f"Error getting communication templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Communication Templates", False)
        
        # Let's create a template manually
        try:
            print("Creating a template manually...")
            url = f"{API_URL}/communications/templates"
            headers = {
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
            data = {
                "name": "Test Template",
                "message_type": "general",
                "subject_template": "Test Subject for {patient_name}",
                "content_template": "Hello {patient_name}, this is a test message from {provider_name}.",
                "is_active": True
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Create Communication Template", True, result)
            return True, result["id"]
        except Exception as e:
            print(f"Error creating communication template: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Communication Template", False)
            return False, None

# Test 3: Message Sending
def test_message_sending(admin_token, patient_id, template_id):
    print("\n--- Testing Message Sending ---")
    
    # First create a patient if needed
    if not patient_id:
        try:
            url = f"{API_URL}/patients"
            headers = {"Authorization": f"Bearer {admin_token}"}
            data = {
                "first_name": "Test",
                "last_name": "Patient",
                "email": "test.patient@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1990-01-01",
                "gender": "female",
                "address_line1": "123 Test St",
                "city": "Testville",
                "state": "TS",
                "zip_code": "12345"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            patient_id = result["id"]
            print_test_result("Create Test Patient", True, result)
        except Exception as e:
            print(f"Error creating test patient: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Create Test Patient", False)
            return False
    
    try:
        url = f"{API_URL}/communications/send"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        data = {
            "patient_id": patient_id,
            "template_id": template_id,
            "sender_id": "admin",
            "sender_name": "Dr. Admin",
            "variables": {
                "patient_name": "Test Patient",
                "provider_name": "Dr. Admin"
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
        
        # Try with direct message
        try:
            print("Trying with direct message...")
            url = f"{API_URL}/communications/send-direct"
            data = {
                "patient_id": patient_id,
                "subject": "Test Direct Message",
                "content": "This is a test direct message.",
                "message_type": "general",
                "sender_id": "admin",
                "sender_name": "Dr. Admin"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Send Direct Message to Patient", True, result)
            return True
        except Exception as e:
            print(f"Error sending direct message to patient: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Send Direct Message to Patient", False)
            return False

def main():
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC BACKEND API ENDPOINTS")
    print("=" * 80)
    
    # Get authentication token
    admin_token = test_authentication()
    if not admin_token:
        print("Failed to authenticate. Cannot proceed with tests.")
        return
    
    # Test 1: Calendar View
    calendar_success = test_calendar_view(admin_token)
    
    # Test 2: Communications Templates
    templates_success, template_id = test_communications_templates(admin_token)
    
    # Test 3: Message Sending
    if templates_success and template_id:
        message_success = test_message_sending(admin_token, None, template_id)
    else:
        print("Cannot test message sending without templates.")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()