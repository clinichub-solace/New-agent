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

# Test Authentication System
def test_authentication():
    print("\n--- Testing Authentication System ---")
    
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

# Test HIPAA and Texas Compliant Form Templates
def test_compliant_form_templates(admin_token):
    print("\n--- Testing HIPAA and Texas Compliant Form Templates ---")
    
    if not admin_token:
        print("Skipping form template tests - no authentication token available")
        return
    
    # Test 1: Initialize Compliant Form Templates
    try:
        url = f"{API_URL}/forms/templates/init-compliant"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify initialization response
        assert "message" in result
        assert "templates_added" in result
        assert "compliance_info" in result
        assert result["templates_added"] == 4  # Should create 4 templates
        
        print_test_result("Initialize Compliant Form Templates", True, result)
    except Exception as e:
        print(f"Error initializing compliant form templates: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Compliant Form Templates", False)
        return
    
    # Test 2: Get All Forms (to verify templates were created)
    try:
        url = f"{API_URL}/forms"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify forms were created
        assert len(result) >= 4  # Should have at least 4 templates
        
        # Check for the expected template titles
        template_titles = [form["title"] for form in result]
        expected_titles = [
            "HIPAA & Texas Compliant Patient Intake Form",
            "Informed Consent to Medical Treatment",
            "Telemedicine Informed Consent",
            "HIPAA Privacy Notice and Authorization"
        ]
        
        for title in expected_titles:
            assert title in template_titles, f"Template '{title}' not found"
        
        print_test_result("Get All Forms", True, {"count": len(result), "titles": template_titles})
        
        # Save the forms for detailed inspection
        forms = result
        return forms
    except Exception as e:
        print(f"Error getting forms: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Forms", False)
        return None

# Test specific form template details
def test_form_template_details(forms):
    print("\n--- Testing Form Template Details ---")
    
    if not forms:
        print("Skipping form template details tests - no forms available")
        return
    
    # Print all form titles to debug
    print("Available form titles:")
    for form in forms:
        print(f"- {form.get('title')}")
    
    # Find each template by title (exact match)
    patient_intake = next((form for form in forms if form.get("title") == "HIPAA & Texas Compliant Patient Intake Form"), None)
    consent_form = next((form for form in forms if form.get("title") == "Informed Consent to Medical Treatment"), None)
    telemedicine_form = next((form for form in forms if form.get("title") == "Telemedicine Informed Consent"), None)
    hipaa_form = next((form for form in forms if form.get("title") == "HIPAA Privacy Notice and Authorization"), None)
    
    # Test 1: Verify Patient Intake Form
    if patient_intake:
        try:
            # Check fields
            assert "fields" in patient_intake
            field_labels = [field["label"] for field in patient_intake["fields"]]
            expected_fields = [
                "Patient Legal Name (First, Middle, Last)",
                "Date of Birth",
                "Emergency Contact Name",
                "Primary Insurance Provider"
            ]
            
            for field in expected_fields:
                assert field in field_labels, f"Field '{field}' not found in Patient Intake Form"
            
            # Check FHIR mapping if available
            fhir_mapping = patient_intake.get("fhir_mapping", {})
            
            print_test_result("Patient Intake Form Verification", True, {
                "title": patient_intake["title"],
                "field_count": len(patient_intake["fields"]),
                "has_fhir_mapping": bool(fhir_mapping)
            })
        except Exception as e:
            print(f"Error verifying Patient Intake Form: {str(e)}")
            print_test_result("Patient Intake Form Verification", False)
    else:
        print_test_result("Patient Intake Form Verification", False, "Form not found")
    
    # Test 2: Verify Informed Consent Form
    if consent_form:
        try:
            # Check fields
            assert "fields" in consent_form
            field_labels = [field["label"] for field in consent_form["fields"]]
            expected_fields = [
                "Patient Name",
                "Consent to Treatment Statement",
                "Patient Signature"
            ]
            
            for field in expected_fields:
                assert field in field_labels, f"Field '{field}' not found in Consent Form"
            
            # Check for signature fields
            signature_fields = [field for field in consent_form["fields"] if field["type"] == "signature"]
            assert len(signature_fields) >= 1, "Consent form should have at least 1 signature field"
            
            print_test_result("Informed Consent Form Verification", True, {
                "title": consent_form["title"],
                "field_count": len(consent_form["fields"]),
                "signature_fields": len(signature_fields)
            })
        except Exception as e:
            print(f"Error verifying Informed Consent Form: {str(e)}")
            print_test_result("Informed Consent Form Verification", False)
    else:
        print_test_result("Informed Consent Form Verification", False, "Form not found")
    
    # Test 3: Verify Telemedicine Consent Form
    if telemedicine_form:
        try:
            # Check fields
            assert "fields" in telemedicine_form
            field_labels = [field["label"] for field in telemedicine_form["fields"]]
            expected_fields = [
                "Patient Name",
                "Healthcare Provider Name",
                "Telemedicine Consent Statement",
                "Patient Signature"
            ]
            
            for field in expected_fields:
                assert field in field_labels, f"Field '{field}' not found in Telemedicine Form"
            
            # Check for signature fields
            signature_fields = [field for field in telemedicine_form["fields"] if field["type"] == "signature"]
            assert len(signature_fields) >= 1, "Telemedicine form should have at least 1 signature field"
            
            print_test_result("Telemedicine Consent Form Verification", True, {
                "title": telemedicine_form["title"],
                "field_count": len(telemedicine_form["fields"]),
                "signature_fields": len(signature_fields)
            })
        except Exception as e:
            print(f"Error verifying Telemedicine Consent Form: {str(e)}")
            print_test_result("Telemedicine Consent Form Verification", False)
    else:
        print_test_result("Telemedicine Consent Form Verification", False, "Form not found")
    
    # Test 4: Verify HIPAA Privacy Notice Form
    if hipaa_form:
        try:
            # Check fields
            assert "fields" in hipaa_form
            field_labels = [field["label"] for field in hipaa_form["fields"]]
            expected_fields = [
                "Patient Name",
                "HIPAA Privacy Notice",
                "Patient Signature"
            ]
            
            for field in expected_fields:
                assert field in field_labels, f"Field '{field}' not found in HIPAA Form"
            
            # Check for signature fields
            signature_fields = [field for field in hipaa_form["fields"] if field["type"] == "signature"]
            assert len(signature_fields) >= 1, "HIPAA form should have at least 1 signature field"
            
            print_test_result("HIPAA Privacy Notice Form Verification", True, {
                "title": hipaa_form["title"],
                "field_count": len(hipaa_form["fields"]),
                "signature_fields": len(signature_fields)
            })
        except Exception as e:
            print(f"Error verifying HIPAA Privacy Notice Form: {str(e)}")
            print_test_result("HIPAA Privacy Notice Form Verification", False)
    else:
        print_test_result("HIPAA Privacy Notice Form Verification", False, "Form not found")

def run_tests():
    print("\n" + "=" * 80)
    print("TESTING HIPAA AND TEXAS COMPLIANT FORM TEMPLATES")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    # Test form templates
    forms = test_compliant_form_templates(admin_token)
    
    # Test form template details
    test_form_template_details(forms)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()