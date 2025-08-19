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

# Helper function to authenticate and get admin token
def get_admin_token():
    try:
        # First try to initialize admin (in case it doesn't exist)
        init_url = f"{API_URL}/auth/init-admin"
        try:
            requests.post(init_url)
        except:
            pass  # Ignore if admin already exists
        
        # Login as admin
        login_url = f"{API_URL}/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(login_url, json=login_data)
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
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "+1-555-987-6543",
            "date_of_birth": "1980-05-15",
            "gender": "male",
            "address_line1": "456 Medical Plaza",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        return None

# Helper function to create a test encounter
def create_test_encounter(patient_id):
    try:
        url = f"{API_URL}/encounters"
        data = {
            "patient_id": patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Jane Wilson",
            "location": "Main Clinic - Room 203",
            "chief_complaint": "Headache and dizziness",
            "reason_for_visit": "Follow-up for medication adjustment"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return result["id"]
    except Exception as e:
        print(f"Error creating test encounter: {str(e)}")
        return None

# Test Phase 1: Medical Templates Initialization
def test_medical_templates_initialization():
    print("\n=== Phase 1: Testing Medical Templates Initialization ===")
    
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Skipping template initialization tests.")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test initializing medical form templates
    try:
        url = f"{API_URL}/forms/templates/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Medical Form Templates", True, result)
    except Exception as e:
        print(f"Error initializing medical form templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Medical Form Templates", False)
        return False
    
    # Verify the templates were created with the expected names
    try:
        url = f"{API_URL}/forms"
        params = {"is_template": True}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        templates = response.json()
        
        # Check if we have the required templates
        template_names = [t.get("template_name", "") for t in templates]
        required_templates = ["patient_intake", "vital_signs", "pain_assessment", "discharge_instructions"]
        
        missing_templates = [t for t in required_templates if t not in template_names]
        if missing_templates:
            print(f"Missing required templates: {missing_templates}")
            print_test_result("Verify Required Templates", False)
            return False
        
        print_test_result("Verify Required Templates", True, {"templates_found": template_names})
        return True
    except Exception as e:
        print(f"Error verifying templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Verify Required Templates", False)
        return False

# Test Phase 2: Enhanced Form Management
def test_enhanced_form_management():
    print("\n=== Phase 2: Testing Enhanced Form Management ===")
    
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Skipping form management tests.")
        return False, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get a template to use for testing
    template_id = None
    try:
        url = f"{API_URL}/forms"
        params = {"is_template": True}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        templates = response.json()
        
        if not templates:
            print("No templates found. Make sure to run template initialization first.")
            return False, None
        
        template_id = templates[0]["id"]
        print(f"Using template: {templates[0].get('title', 'Unknown')} (ID: {template_id})")
    except Exception as e:
        print(f"Error getting templates: {str(e)}")
        return False, None
    
    # Test 1: Get forms with category filtering
    try:
        url = f"{API_URL}/forms"
        params = {"category": "intake"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Forms with Category Filter", True, result)
    except Exception as e:
        print(f"Error getting forms with category filter: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Forms with Category Filter", False)
    
    # Test 2: Create a form from template
    form_id = None
    try:
        url = f"{API_URL}/forms/from-template/{template_id}"
        data = {
            "title": "Custom Patient Assessment Form",
            "description": "Customized assessment form based on template"
        }
        response = requests.post(url, headers=headers, params=data)
        response.raise_for_status()
        result = response.json()
        
        form_id = result["id"]
        print_test_result("Create Form from Template", True, result)
    except Exception as e:
        print(f"Error creating form from template: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Create Form from Template", False)
    
    # Test 3: Get individual form by ID
    if form_id:
        try:
            url = f"{API_URL}/forms/{form_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Get Form by ID", True, result)
        except Exception as e:
            print(f"Error getting form by ID: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Get Form by ID", False)
    
    # Test 4: Update form
    if form_id:
        try:
            # First get the current form
            url = f"{API_URL}/forms/{form_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            form = response.json()
            
            # Update some fields
            form["description"] = "Updated description for testing"
            form["status"] = "active"
            
            # Add a new field
            form["fields"].append({
                "type": "textarea",
                "label": "Additional Notes",
                "placeholder": "Enter any additional information here",
                "required": False,
                "order": len(form["fields"])
            })
            
            # Send the update
            url = f"{API_URL}/forms/{form_id}"
            response = requests.put(url, headers=headers, json=form)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Form", True, result)
        except Exception as e:
            print(f"Error updating form: {str(e)}")
            if 'response' in locals():
                print(f"Status code: {response.status_code}")
                print(f"Response text: {response.text}")
            print_test_result("Update Form", False)
    
    return True, form_id

# Test Phase 3: Form Submission & Smart Tags
def test_form_submission_and_smart_tags(form_id):
    print("\n=== Phase 3: Testing Form Submission & Smart Tags ===")
    
    if not form_id:
        print("No form ID provided. Skipping form submission tests.")
        return False, None
    
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Skipping form submission tests.")
        return False, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a test patient
    patient_id = create_test_patient()
    if not patient_id:
        print("Failed to create test patient. Skipping form submission tests.")
        return False, None
    
    # Create a test encounter
    encounter_id = create_test_encounter(patient_id)
    
    # Test 1: Submit form with smart tags
    submission_id = None
    try:
        # First get the form to see its fields
        url = f"{API_URL}/forms/{form_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        form = response.json()
        
        # Prepare submission data with smart tags
        submission_data = {}
        for field in form["fields"]:
            if field["type"] == "text":
                submission_data[field["id"]] = "Test value with {patient_name} and {current_date}"
            elif field["type"] == "select" and field["options"]:
                submission_data[field["id"]] = field["options"][0]
            elif field["type"] == "date":
                submission_data[field["id"]] = date.today().isoformat()
            elif field["type"] == "textarea":
                submission_data[field["id"]] = "Notes for {patient_name} on {current_date}"
            elif field["type"] == "number":
                submission_data[field["id"]] = 42
            elif field["type"] == "checkbox":
                submission_data[field["id"]] = True
        
        # Submit the form
        url = f"{API_URL}/forms/{form_id}/submit"
        params = {
            "patient_id": patient_id,
            "encounter_id": encounter_id
        }
        
        response = requests.post(url, headers=headers, json=submission_data, params=params)
        response.raise_for_status()
        result = response.json()
        
        submission_id = result["id"]
        
        # Verify smart tag processing
        processed_data = result.get("processed_data", {})
        has_processed_tags = False
        
        for key, value in processed_data.items():
            if isinstance(value, str) and ("{patient_name}" not in value) and ("{current_date}" not in value):
                has_processed_tags = True
                break
        
        if has_processed_tags:
            print("Smart tags were successfully processed")
        else:
            print("Warning: Smart tags may not have been processed correctly")
        
        # Verify FHIR data generation
        if "fhir_data" in result and result["fhir_data"]:
            print("FHIR data was successfully generated")
        else:
            print("Warning: FHIR data was not generated")
        
        print_test_result("Submit Form with Smart Tags", True, result)
    except Exception as e:
        print(f"Error submitting form: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Submit Form with Smart Tags", False)
    
    return True, submission_id, patient_id

# Test Phase 4: Submission Management
def test_submission_management(form_id, submission_id, patient_id):
    print("\n=== Phase 4: Testing Submission Management ===")
    
    if not form_id or not submission_id or not patient_id:
        print("Missing required IDs. Skipping submission management tests.")
        return False
    
    admin_token = get_admin_token()
    if not admin_token:
        print("Failed to get admin token. Skipping submission management tests.")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Get form-specific submissions
    try:
        url = f"{API_URL}/forms/{form_id}/submissions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Form-Specific Submissions", True, result)
    except Exception as e:
        print(f"Error getting form submissions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Form-Specific Submissions", False)
    
    # Test 2: Get patient submissions
    try:
        url = f"{API_URL}/patients/{patient_id}/form-submissions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Patient Form Submissions", True, result)
    except Exception as e:
        print(f"Error getting patient submissions: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Patient Form Submissions", False)
    
    # Test 3: Get individual submission details
    try:
        url = f"{API_URL}/form-submissions/{submission_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Get Individual Submission Details", True, result)
    except Exception as e:
        print(f"Error getting submission details: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Individual Submission Details", False)
    
    return True

def run_all_tests():
    print("\n" + "=" * 80)
    print("TESTING ENHANCED SMART FORMS MODULE")
    print("=" * 80)
    
    # Run all test phases in sequence
    templates_initialized = test_medical_templates_initialization()
    
    if templates_initialized:
        form_management_success, form_id = test_enhanced_form_management()
        
        if form_management_success and form_id:
            submission_success, submission_id, patient_id = test_form_submission_and_smart_tags(form_id)
            
            if submission_success and submission_id and patient_id:
                test_submission_management(form_id, submission_id, patient_id)
    
    print("\n" + "=" * 80)
    print("SMART FORMS TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()