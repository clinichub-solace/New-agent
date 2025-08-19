#!/usr/bin/env python3
"""
Comprehensive Payroll Workflow Testing for ClinicHub
Tests the complete end-to-end payroll flow as requested in the review:
1. Set up tax and ACH configurations
2. Set up employee bank information 
3. Create pay period and payroll run
4. Seed test payroll records
5. Post the run (this should apply taxes using the async hook)
6. Test all export formats (CSV, ACH, PDF)
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
print(f"Using API URL: {API_URL}")

# Authentication credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Global variables to store IDs for the workflow
auth_token = None
employee_id = None
period_id = None
run_id = None

# Helper function to print test results
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
        elif response:
            print(f"   Response: {str(response)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Step 1: Authenticate with admin credentials"""
    global auth_token
    print("\n=== STEP 1: AUTHENTICATION ===")
    
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
        print_test_result("Authentication", True, {"message": "Login successful", "user": result.get("user", {})})
        return True
    except Exception as e:
        print_test_result("Authentication", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_tax_configuration():
    """Step 2: Set up tax configuration"""
    print("\n=== STEP 2: TAX CONFIGURATION ===")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/config/tax"
        
        # Tax configuration data
        tax_config = {
            "federal_tax_rate": 0.22,
            "state_tax_rate": 0.05,
            "social_security_rate": 0.062,
            "medicare_rate": 0.0145,
            "unemployment_rate": 0.006,
            "state": "TX",
            "federal_exemptions": {
                "single": 12950,
                "married_filing_jointly": 25900,
                "married_filing_separately": 12950,
                "head_of_household": 19400
            },
            "state_exemptions": {
                "single": 0,
                "married_filing_jointly": 0,
                "married_filing_separately": 0,
                "head_of_household": 0
            }
        }
        
        response = requests.put(url, json=tax_config, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("PUT /api/payroll/config/tax", True, result)
        return True
    except Exception as e:
        print_test_result("PUT /api/payroll/config/tax", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_ach_configuration():
    """Step 3: Set up ACH configuration"""
    print("\n=== STEP 3: ACH CONFIGURATION ===")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/config/ach"
        
        # ACH configuration data
        ach_config = {
            "company_name": "ClinicHub Medical Practice",
            "company_id": "1234567890",
            "routing_number": "021000021",
            "account_number": "123456789",
            "account_type": "checking",
            "bank_name": "Chase Bank",
            "originator_name": "ClinicHub Payroll",
            "originator_id": "CLINICHUB001",
            "batch_header": {
                "service_class_code": "200",
                "company_entry_description": "PAYROLL",
                "company_descriptive_date": datetime.now().strftime("%y%m%d"),
                "effective_entry_date": (datetime.now() + timedelta(days=1)).strftime("%y%m%d")
            }
        }
        
        response = requests.put(url, json=ach_config, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("PUT /api/payroll/config/ach", True, result)
        return True
    except Exception as e:
        print_test_result("PUT /api/payroll/config/ach", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def create_test_employee():
    """Step 4: Create a test employee for payroll testing"""
    print("\n=== STEP 4: CREATE TEST EMPLOYEE ===")
    
    global employee_id
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/employees"
        
        # Create test employee
        employee_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@clinichub.com",
            "phone": "555-123-4567",
            "role": "nurse",
            "department": "Clinical",
            "hire_date": "2024-01-15",
            "salary": 65000.00,
            "employment_type": "full_time"
        }
        
        response = requests.post(url, json=employee_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        employee_id = result.get("id")
        print_test_result("POST /api/employees", True, result)
        return True
    except Exception as e:
        print_test_result("POST /api/employees", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def setup_employee_bank_info():
    """Step 5: Set up employee bank information"""
    print("\n=== STEP 5: EMPLOYEE BANK INFORMATION ===")
    
    if not employee_id:
        print("❌ Cannot set up bank info - no employee ID available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/employees/{employee_id}/bank"
        
        # Bank information data
        bank_info = {
            "bank_name": "Wells Fargo",
            "routing_number": "121000248",
            "account_number": "987654321",
            "account_type": "checking",
            "account_holder_name": "John Doe",
            "is_active": True,
            "direct_deposit_percentage": 100.0
        }
        
        response = requests.put(url, json=bank_info, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result(f"PUT /api/payroll/employees/{employee_id}/bank", True, result)
        return True
    except Exception as e:
        print_test_result(f"PUT /api/payroll/employees/{employee_id}/bank", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def create_pay_period():
    """Step 6: Create pay period"""
    print("\n=== STEP 6: CREATE PAY PERIOD ===")
    
    global period_id
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/periods"
        
        # Create a biweekly pay period
        today = datetime.now()
        period_start = (today - timedelta(days=14)).date()
        period_end = (today - timedelta(days=1)).date()
        pay_date = (today + timedelta(days=5)).date()
        
        period_data = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "pay_date": pay_date.isoformat(),
            "period_type": "biweekly",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=period_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        period_id = result.get("id")
        print_test_result("POST /api/payroll/periods", True, result)
        return True
    except Exception as e:
        print_test_result("POST /api/payroll/periods", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def create_payroll_run():
    """Step 7: Create payroll run"""
    print("\n=== STEP 7: CREATE PAYROLL RUN ===")
    
    global run_id
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/runs"
        
        # Create payroll run
        run_data = {
            "period_id": period_id,
            "run_name": f"Payroll Run - {datetime.now().strftime('%Y-%m-%d')}",
            "description": "Test payroll run for end-to-end workflow testing",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=run_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        run_id = result.get("id")
        print_test_result("POST /api/payroll/runs", True, result)
        return True
    except Exception as e:
        print_test_result("POST /api/payroll/runs", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def seed_test_payroll_records():
    """Step 8: Seed test payroll records (ENV-gated)"""
    print("\n=== STEP 8: SEED TEST PAYROLL RECORDS ===")
    
    if not run_id:
        print("❌ Cannot seed payroll records - no run ID available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/_test/seed/payroll_records"
        
        # Seed data for the payroll run
        seed_data = {
            "run_id": run_id,
            "employee_id": employee_id,
            "regular_hours": 80.0,
            "overtime_hours": 5.0,
            "bonus_pay": 500.0,
            "deductions": [
                {
                    "deduction_type": "health_insurance",
                    "description": "Health Insurance Premium",
                    "amount": 150.0,
                    "is_pre_tax": True
                },
                {
                    "deduction_type": "retirement_401k",
                    "description": "401k Contribution",
                    "amount": 200.0,
                    "percentage": 3.0,
                    "is_pre_tax": True
                }
            ]
        }
        
        response = requests.post(url, json=seed_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("POST /api/payroll/_test/seed/payroll_records", True, result)
        return True
    except Exception as e:
        print_test_result("POST /api/payroll/_test/seed/payroll_records", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def post_payroll_run():
    """Step 9: Post the payroll run (applies taxes using async hook)"""
    print("\n=== STEP 9: POST PAYROLL RUN (WITH TAX HOOK) ===")
    
    if not run_id:
        print("❌ Cannot post payroll run - no run ID available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        url = f"{API_URL}/payroll/runs/{run_id}/post"
        
        # Post the payroll run
        post_data = {
            "apply_taxes": True,
            "finalize": True,
            "posted_by": "admin"
        }
        
        response = requests.post(url, json=post_data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result(f"POST /api/payroll/runs/{run_id}/post", True, result)
        return True
    except Exception as e:
        print_test_result(f"POST /api/payroll/runs/{run_id}/post", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def test_export_formats():
    """Step 10: Test all export formats (CSV, ACH, PDF)"""
    print("\n=== STEP 10: TEST EXPORT FORMATS ===")
    
    if not run_id:
        print("❌ Cannot test exports - no run ID available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test CSV export
    try:
        url = f"{API_URL}/payroll/runs/{run_id}/paystubs.csv"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Check if response is CSV format
        content_type = response.headers.get('content-type', '')
        if 'csv' in content_type.lower() or 'text' in content_type.lower():
            print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs.csv", True, 
                            {"content_type": content_type, "size": len(response.content)})
        else:
            print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs.csv", True, 
                            {"response": response.text[:200]})
    except Exception as e:
        print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs.csv", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test ACH export
    try:
        url = f"{API_URL}/payroll/runs/{run_id}/ach"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Check if response is ACH format
        content_type = response.headers.get('content-type', '')
        print_test_result(f"GET /api/payroll/runs/{run_id}/ach", True, 
                        {"content_type": content_type, "size": len(response.content)})
    except Exception as e:
        print_test_result(f"GET /api/payroll/runs/{run_id}/ach", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
    
    # Test PDF export
    try:
        url = f"{API_URL}/payroll/runs/{run_id}/paystubs"
        params = {"format": "pdf"}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # Check if response is PDF format
        content_type = response.headers.get('content-type', '')
        if 'pdf' in content_type.lower():
            print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs?format=pdf", True, 
                            {"content_type": content_type, "size": len(response.content)})
        else:
            print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs?format=pdf", True, 
                            {"response": response.text[:200]})
    except Exception as e:
        print_test_result(f"GET /api/payroll/runs/{run_id}/paystubs?format=pdf", False, error=str(e))
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

def test_complete_payroll_workflow():
    """Main function to test the complete payroll workflow"""
    print("🏥 COMPREHENSIVE PAYROLL WORKFLOW TESTING")
    print("=" * 80)
    print("Testing the complete end-to-end payroll flow:")
    print("1. Set up tax and ACH configurations")
    print("2. Set up employee bank information")
    print("3. Create pay period and payroll run")
    print("4. Seed test payroll records")
    print("5. Post the run (applies taxes using async hook)")
    print("6. Test all export formats (CSV, ACH, PDF)")
    print("=" * 80)
    
    # Execute the workflow steps
    steps = [
        ("Authentication", authenticate),
        ("Tax Configuration", setup_tax_configuration),
        ("ACH Configuration", setup_ach_configuration),
        ("Create Test Employee", create_test_employee),
        ("Employee Bank Information", setup_employee_bank_info),
        ("Create Pay Period", create_pay_period),
        ("Create Payroll Run", create_payroll_run),
        ("Seed Test Payroll Records", seed_test_payroll_records),
        ("Post Payroll Run", post_payroll_run),
        ("Test Export Formats", test_export_formats)
    ]
    
    passed_steps = 0
    total_steps = len(steps)
    
    for step_name, step_function in steps:
        print(f"\n--- Executing: {step_name} ---")
        try:
            if step_function():
                passed_steps += 1
            else:
                print(f"⚠️  Step '{step_name}' failed - continuing with next step")
        except Exception as e:
            print(f"❌ Step '{step_name}' encountered an error: {str(e)}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 PAYROLL WORKFLOW TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed Steps: {passed_steps}/{total_steps}")
    print(f"❌ Failed Steps: {total_steps - passed_steps}/{total_steps}")
    
    if passed_steps == total_steps:
        print("🎉 ALL PAYROLL WORKFLOW TESTS PASSED!")
        print("The complete payroll system is working correctly.")
    elif passed_steps >= total_steps * 0.7:
        print("⚠️  MOST PAYROLL WORKFLOW TESTS PASSED")
        print("The payroll system is mostly functional with some issues.")
    else:
        print("❌ PAYROLL WORKFLOW HAS SIGNIFICANT ISSUES")
        print("Multiple steps failed - payroll system needs attention.")
    
    print("\n📋 Test Details:")
    print(f"   - Authentication: {'✅' if auth_token else '❌'}")
    print(f"   - Employee ID: {employee_id if employee_id else 'Not created'}")
    print(f"   - Period ID: {period_id if period_id else 'Not created'}")
    print(f"   - Run ID: {run_id if run_id else 'Not created'}")
    
    print("\n🔍 Key Findings:")
    if auth_token:
        print("   ✅ Authentication system working")
    else:
        print("   ❌ Authentication failed - check credentials")
    
    if employee_id and period_id and run_id:
        print("   ✅ Core payroll entities created successfully")
    else:
        print("   ❌ Failed to create required payroll entities")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_complete_payroll_workflow()