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
    
    # Test variables to store authentication data
    admin_token = None
    
    # Test 1: Login with Admin Credentials
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
    except Exception as e:
        print(f"Error logging in as admin: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Admin Login", False)
    
    return admin_token

# Test Dashboard Stats Endpoint
def test_dashboard_stats(admin_token):
    print("\n--- Testing Dashboard Stats Endpoint ---")
    
    try:
        url = f"{API_URL}/dashboard/stats"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify dashboard stats structure
        assert "stats" in result
        assert "total_patients" in result["stats"]
        assert "total_invoices" in result["stats"]
        assert "pending_invoices" in result["stats"]
        assert "low_stock_items" in result["stats"]
        assert "total_employees" in result["stats"]
        
        print_test_result("Dashboard Stats", True, result)
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Dashboard Stats", False)

# Test Pending Payments Endpoint
def test_pending_payments(admin_token):
    print("\n--- Testing Pending Payments Endpoint ---")
    
    try:
        url = f"{API_URL}/dashboard/pending-payments"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify pending payments structure
        assert "summary" in result
        assert "pending_payments" in result
        
        # Verify summary structure
        assert "total_outstanding_amount" in result["summary"]
        assert "total_pending_invoices" in result["summary"]
        
        # If there are pending payments, verify their structure
        if len(result["pending_payments"]) > 0:
            payment = result["pending_payments"][0]
            assert "invoice_id" in payment
            assert "patient_id" in payment
            assert "patient_name" in payment
            assert "outstanding_amount" in payment
            assert "days_overdue" in payment
        
        print_test_result("Pending Payments", True, result)
    except Exception as e:
        print(f"Error getting pending payments: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Pending Payments", False)

# Test HIPAA and Texas Compliant Forms
def test_compliant_forms(admin_token):
    print("\n--- Testing HIPAA and Texas Compliant Forms ---")
    
    # Test 1: Initialize Compliant Forms
    try:
        url = f"{API_URL}/forms/templates/init-compliant"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify initialization response
        assert "message" in result
        assert "templates_added" in result
        assert result["templates_added"] == 4  # Should create 4 compliant templates
        assert "compliance_info" in result
        
        print_test_result("Initialize Compliant Forms", True, result)
    except Exception as e:
        print(f"Error initializing compliant forms: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Compliant Forms", False)

# Test Forms Access
def test_forms_access(admin_token):
    print("\n--- Testing Forms Access ---")
    
    # Test 1: Get All Forms
    try:
        url = f"{API_URL}/forms"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify forms are returned
        assert isinstance(result, list)
        
        # Check if compliant forms are included
        compliant_forms = [form for form in result if "HIPAA" in form.get("title", "")]
        
        print_test_result("Get All Forms", True, {"total_forms": len(result), "compliant_forms_count": len(compliant_forms)})
    except Exception as e:
        print(f"Error getting all forms: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Forms", False)
    
    # Test 2: Filter Forms by Category
    try:
        url = f"{API_URL}/forms"
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"category": "compliant"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify compliant forms are returned
        assert isinstance(result, list)
        
        # Check if all returned forms are compliant
        if len(result) > 0:
            assert all("compliant" in form.get("category", "") for form in result)
        
        print_test_result("Filter Forms by Category", True, {"compliant_forms_count": len(result)})
    except Exception as e:
        print(f"Error filtering forms by category: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Filter Forms by Category", False)

def run_verification_tests():
    print("\n" + "=" * 80)
    print("VERIFICATION TESTING FOR CLINICHUB BACKEND API")
    print("=" * 80)
    
    # Test authentication first to get admin token
    admin_token = test_authentication()
    
    if admin_token:
        # Test dashboard endpoints
        test_dashboard_stats(admin_token)
        test_pending_payments(admin_token)
        
        # Test compliant forms
        test_compliant_forms(admin_token)
        test_forms_access(admin_token)
    else:
        print("Authentication failed. Cannot proceed with further tests.")

if __name__ == "__main__":
    run_verification_tests()