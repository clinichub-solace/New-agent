#!/usr/bin/env python3
"""
Enhanced Payroll Workflow Test - Using New Payroll Enhancement Endpoints
Tests the complete end-to-end payroll workflow using the newer payroll enhancement endpoints
that should work around the MongoDB index conflict issue.
"""

import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
from dotenv import load_dotenv
from pathlib import Path
import time

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

# Authentication credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Global variables to store IDs for the workflow
auth_token = None
employee_id = None
pay_period_id = None
payroll_run_id = None

def print_test_result(test_name, success, response=None, error=None):
    """Helper function to print test results"""
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            # Print first few fields of response for brevity
            preview = {k: v for i, (k, v) in enumerate(response.items()) if i < 3}
            print(f"   Response preview: {json.dumps(preview, indent=2, default=str)}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Step 1: Authentication with admin/admin123"""
    global auth_token
    print("\n🔐 STEP 1: Authentication")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        auth_token = result["access_token"]
        print_test_result("Authentication (admin/admin123)", True, {"token_received": True, "user": result.get("user", {}).get("username")})
        return True
    except Exception as e:
        print_test_result("Authentication (admin/admin123)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_tax_configuration():
    """Step 2: Tax configuration setup using new endpoints"""
    print("\n💰 STEP 2: Tax Configuration Setup")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test PUT tax config using new endpoint
    try:
        url = f"{API_URL}/payroll/config/tax"
        data = {
            "jurisdiction": "TX",
            "effective_date": "2025-01-01",
            "federal_tax_rate": 0.22,
            "state_tax_rate": 0.05,
            "social_security_rate": 0.062,
            "medicare_rate": 0.0145,
            "unemployment_rate": 0.006,
            "federal_exemptions": {
                "single": 12950,
                "married_filing_jointly": 25900,
                "married_filing_separately": 12950,
                "head_of_household": 19400
            }
        }
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("PUT Tax Configuration", True, result)
        return True
    except Exception as e:
        print_test_result("PUT Tax Configuration", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_ach_configuration():
    """Step 3: ACH configuration setup using new endpoints"""
    print("\n🏦 STEP 3: ACH Configuration Setup")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test PUT ACH config using new endpoint
    try:
        url = f"{API_URL}/payroll/config/ach"
        data = {
            "company_name": "ClinicHub Medical Practice",
            "company_id": "1234567890",
            "routing_number": "021000021",
            "account_number": "123456789",
            "account_type": "checking",
            "bank_name": "Chase Bank",
            "contact_name": "Admin User",
            "contact_phone": "555-123-4567",
            "batch_header": {
                "service_class_code": "200",
                "company_entry_description": "PAYROLL",
                "company_descriptive_date": datetime.now().strftime("%y%m%d"),
                "effective_entry_date": (datetime.now() + timedelta(days=1)).strftime("%y%m%d")
            }
        }
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("PUT ACH Configuration", True, result)
        return True
    except Exception as e:
        print_test_result("PUT ACH Configuration", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_employee_bank_info():
    """Step 4: Employee bank information setup using new endpoints"""
    global employee_id
    print("\n👤 STEP 4: Employee Bank Information Setup")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First, create an employee if needed
    try:
        url = f"{API_URL}/employees"
        employee_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@clinichub.com",
            "phone": "555-123-4567",
            "role": "nurse",
            "department": "Clinical",
            "hire_date": "2024-01-15",
            "hourly_rate": 25.00
        }
        
        response = requests.post(url, json=employee_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        employee_id = result["id"]
        print_test_result("Create Employee", True, {"employee_id": employee_id, "name": f"{result['first_name']} {result['last_name']}"})
    except Exception as e:
        print_test_result("Create Employee", False, error=str(e))
        # Try to get existing employee
        try:
            url = f"{API_URL}/employees"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            employees = response.json()
            if employees and len(employees) > 0:
                employee_id = employees[0]["id"]
                print(f"Using existing employee ID: {employee_id}")
        except Exception as e2:
            print(f"Error getting existing employees: {str(e2)}")
            return False
    
    if not employee_id:
        print("❌ No employee ID available for bank setup")
        return False
    
    # Test PUT employee bank info using new endpoint
    try:
        url = f"{API_URL}/payroll/employees/{employee_id}/bank"
        data = {
            "name": "John Doe",
            "routing_number": "121000248",
            "account_number": "987654321",
            "account_type": "checking"
        }
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print_test_result("PUT Employee Bank Info", True, result)
        return True
    except Exception as e:
        print_test_result("PUT Employee Bank Info", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def create_pay_period():
    """Step 5: Create pay period using new enhanced endpoints"""
    global pay_period_id
    print("\n📅 STEP 5: Create Pay Period (Enhanced)")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/periods"
        
        # Create a biweekly pay period using the new enhanced endpoint
        today = datetime.now()
        period_start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        period_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        pay_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        
        data = {
            "start_date": period_start,
            "end_date": period_end,
            "pay_date": pay_date,
            "frequency": "biweekly",
            "description": f"Biweekly payroll period {period_start} to {period_end}"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        pay_period_id = result.get("_id") or result.get("id")
        print_test_result("Create Pay Period (Enhanced)", True, {"period_id": pay_period_id, "period_start": period_start, "period_end": period_end})
        return True
    except Exception as e:
        print_test_result("Create Pay Period (Enhanced)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def create_payroll_run():
    """Step 6: Create payroll run using new enhanced endpoints"""
    global payroll_run_id
    print("\n🏃 STEP 6: Create Payroll Run (Enhanced)")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not pay_period_id:
        print("❌ No pay period ID available for payroll run")
        return False
    
    try:
        url = f"{API_URL}/payroll/runs"
        data = {
            "period_id": pay_period_id
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        payroll_run_id = result.get("_id") or result.get("id")
        print_test_result("Create Payroll Run (Enhanced)", True, {"run_id": payroll_run_id, "period_id": pay_period_id})
        return True
    except Exception as e:
        print_test_result("Create Payroll Run (Enhanced)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def seed_test_payroll_records():
    """Step 7: Seed test payroll records using ENV-gated test seeder"""
    print("\n🌱 STEP 7: Seed Test Payroll Records (ENV-gated)")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not payroll_run_id:
        print("❌ No payroll run ID available for seeding records")
        return False
    
    try:
        url = f"{API_URL}/payroll/_test/seed/payroll_records"
        data = {
            "run_id": payroll_run_id,
            "employee_count": 3
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Seed Test Payroll Records (ENV-gated)", True, result)
        return True
    except Exception as e:
        print_test_result("Seed Test Payroll Records (ENV-gated)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def post_payroll_run():
    """Step 8: Post the run using async tax hook integration"""
    print("\n📮 STEP 8: Post Payroll Run (Async Tax Hook Integration)")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not payroll_run_id:
        print("❌ No payroll run ID available for posting")
        return False
    
    try:
        url = f"{API_URL}/payroll/runs/{payroll_run_id}/post"
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Post Payroll Run (Async Tax Hook)", True, result)
        
        # Wait a moment for async processing
        print("⏳ Waiting for async tax processing...")
        time.sleep(3)
        
        return True
    except Exception as e:
        print_test_result("Post Payroll Run (Async Tax Hook)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def test_export_formats():
    """Step 9: Test all export formats (CSV, ACH, PDF)"""
    print("\n📊 STEP 9: Test Export Formats")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    if not payroll_run_id:
        print("❌ No payroll run ID available for exports")
        return False
    
    # Test CSV Export
    try:
        url = f"{API_URL}/payroll/runs/{payroll_run_id}/paystubs.csv"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Check if response is CSV format
        content_type = response.headers.get('content-type', '')
        is_csv = 'csv' in content_type.lower() or 'text' in content_type.lower()
        
        print_test_result("CSV Export", True, {
            "content_type": content_type,
            "content_length": len(response.content),
            "is_csv_format": is_csv
        })
    except Exception as e:
        print_test_result("CSV Export", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text[:200]}...")
    
    # Test ACH Export (Test Mode)
    try:
        url = f"{API_URL}/payroll/runs/{payroll_run_id}/ach?mode=test"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        
        print_test_result("ACH Export (Test Mode)", True, {
            "content_type": content_type,
            "content_length": len(response.content),
            "test_mode": True
        })
    except Exception as e:
        print_test_result("ACH Export (Test Mode)", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text[:200]}...")
    
    # Test PDF Export
    try:
        url = f"{API_URL}/payroll/runs/{payroll_run_id}/paystubs?format=pdf"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        is_pdf = 'pdf' in content_type.lower()
        
        print_test_result("PDF Export", True, {
            "content_type": content_type,
            "content_length": len(response.content),
            "is_pdf_format": is_pdf
        })
    except Exception as e:
        print_test_result("PDF Export", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text[:200]}...")

def run_enhanced_payroll_workflow():
    """Run the complete enhanced payroll workflow test"""
    print("🚀 ENHANCED PAYROLL WORKFLOW TEST")
    print("=" * 80)
    print("Testing with new payroll enhancement endpoints to avoid MongoDB index conflicts")
    print("=" * 80)
    
    # Step 1: Authentication
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with workflow.")
        return
    
    # Step 2: Tax configuration setup
    setup_tax_configuration()
    
    # Step 3: ACH configuration setup
    setup_ach_configuration()
    
    # Step 4: Employee bank information setup
    if not setup_employee_bank_info():
        print("⚠️ Employee bank setup failed, but continuing with workflow...")
    
    # Step 5: Create pay period using enhanced endpoints
    if not create_pay_period():
        print("❌ Pay period creation failed. Cannot proceed with payroll run.")
        return
    
    # Step 6: Create payroll run using enhanced endpoints
    if not create_payroll_run():
        print("❌ Payroll run creation failed. Cannot proceed with seeding and posting.")
        return
    
    # Step 7: Seed test payroll records
    if not seed_test_payroll_records():
        print("⚠️ Seeding test records failed, but continuing with posting...")
    
    # Step 8: Post the run (async tax hook)
    if not post_payroll_run():
        print("⚠️ Payroll run posting failed, but continuing with export tests...")
    
    # Step 9: Test all export formats
    test_export_formats()
    
    print("\n" + "=" * 80)
    print("🎯 ENHANCED PAYROLL WORKFLOW TEST COMPLETED")
    print("=" * 80)
    
    # Summary
    print("\n📋 WORKFLOW SUMMARY:")
    print(f"   • Authentication: {'✅ Success' if auth_token else '❌ Failed'}")
    print(f"   • Employee ID: {employee_id or 'Not created'}")
    print(f"   • Pay Period ID: {pay_period_id or 'Not created'}")
    print(f"   • Payroll Run ID: {payroll_run_id or 'Not created'}")
    print("\n🔍 KEY VERIFICATION POINTS:")
    print("   • MongoDB index conflict resolution with enhanced endpoints")
    print("   • Async tax hook integration during run posting")
    print("   • ENV-gated test seeder accessibility")
    print("   • All export formats (CSV, ACH, PDF)")
    print("   • Complete end-to-end payroll flow")

if __name__ == "__main__":
    run_enhanced_payroll_workflow()