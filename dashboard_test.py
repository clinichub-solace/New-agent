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
        # First try to initialize admin user (if not already done)
        init_url = f"{API_URL}/auth/init-admin"
        try:
            requests.post(init_url)
        except:
            pass  # Ignore errors if admin already exists
        
        # Login with admin credentials
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

# Test eRx Patients Dashboard
def test_erx_patients_dashboard(token):
    print("\n--- Testing eRx Patients Dashboard ---")
    
    try:
        url = f"{API_URL}/dashboard/erx-patients"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "date" in result
        assert "total_scheduled" in result
        assert "patients" in result
        assert isinstance(result["patients"], list)
        
        # Check if each patient has the required fields
        if result["patients"]:
            patient = result["patients"][0]
            assert "encounter_id" in patient
            assert "patient_id" in patient
            assert "patient_name" in patient
            assert "scheduled_time" in patient
            assert "active_prescriptions" in patient
            assert "allergies_count" in patient
        
        print_test_result("eRx Patients Dashboard", True, result)
        return True
    except Exception as e:
        print(f"Error testing eRx patients dashboard: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("eRx Patients Dashboard", False)
        return False

# Test Daily Log Dashboard
def test_daily_log_dashboard(token):
    print("\n--- Testing Daily Log Dashboard ---")
    
    try:
        url = f"{API_URL}/dashboard/daily-log"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "date" in result
        assert "summary" in result
        assert "visits" in result
        assert isinstance(result["visits"], list)
        
        # Check summary fields
        summary = result["summary"]
        assert "total_patients_seen" in summary
        assert "total_revenue" in summary
        assert "total_paid" in summary
        assert "outstanding_amount" in summary
        
        # Check visit fields if any visits exist
        if result["visits"]:
            visit = result["visits"][0]
            assert "encounter_id" in visit
            assert "patient_id" in visit
            assert "patient_name" in visit
            assert "visit_type" in visit
            assert "total_amount" in visit
            assert "paid_amount" in visit
            assert "payment_status" in visit
        
        print_test_result("Daily Log Dashboard", True, result)
        return True
    except Exception as e:
        print(f"Error testing daily log dashboard: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Daily Log Dashboard", False)
        return False

# Test Patient Queue Dashboard
def test_patient_queue_dashboard(token):
    print("\n--- Testing Patient Queue Dashboard ---")
    
    try:
        url = f"{API_URL}/dashboard/patient-queue"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "timestamp" in result
        assert "summary" in result
        assert "locations" in result
        assert "all_patients" in result
        assert isinstance(result["all_patients"], list)
        
        # Check summary fields
        summary = result["summary"]
        assert "total_patients" in summary
        assert "average_wait_time" in summary
        assert "locations_in_use" in summary
        
        # Check locations
        locations = result["locations"]
        assert "lobby" in locations
        assert "room_1" in locations
        assert "room_2" in locations
        assert "room_3" in locations
        assert "room_4" in locations
        assert "iv_room" in locations
        assert "checkout" in locations
        
        # Check patient fields if any patients exist
        if result["all_patients"]:
            patient = result["all_patients"][0]
            assert "encounter_id" in patient
            assert "patient_id" in patient
            assert "patient_name" in patient
            assert "location" in patient
            assert "wait_time_minutes" in patient
            assert "status" in patient
        
        print_test_result("Patient Queue Dashboard", True, result)
        return True
    except Exception as e:
        print(f"Error testing patient queue dashboard: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Patient Queue Dashboard", False)
        return False

# Test Pending Payments Dashboard
def test_pending_payments_dashboard(token):
    print("\n--- Testing Pending Payments Dashboard ---")
    
    try:
        url = f"{API_URL}/dashboard/pending-payments"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify response structure
        assert "summary" in result
        assert "pending_payments" in result
        assert isinstance(result["pending_payments"], list)
        
        # Check summary fields
        summary = result["summary"]
        assert "total_outstanding_amount" in summary
        assert "total_pending_invoices" in summary
        assert "overdue_invoices" in summary
        assert "average_days_overdue" in summary
        
        # Check payment fields if any payments exist
        if result["pending_payments"]:
            payment = result["pending_payments"][0]
            assert "invoice_id" in payment
            assert "invoice_number" in payment
            assert "patient_id" in payment
            assert "patient_name" in payment
            assert "total_amount" in payment
            assert "outstanding_amount" in payment
            assert "days_overdue" in payment
            assert "status" in payment
        
        print_test_result("Pending Payments Dashboard", True, result)
        return True
    except Exception as e:
        print(f"Error testing pending payments dashboard: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Pending Payments Dashboard", False)
        return False

# Create test data to populate the dashboard views
def create_test_data(token):
    print("\n--- Creating Test Data for Dashboard Testing ---")
    
    patient_id = None
    encounter_id = None
    
    # 1. Create a test patient
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {token}"}
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
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        patient_id = result["id"]
        print_test_result("Create Test Patient", True, result)
    except Exception as e:
        print(f"Error creating test patient: {str(e)}")
        print_test_result("Create Test Patient", False)
    
    # 2. Create an encounter for today (for eRx patients dashboard)
    if patient_id:
        try:
            url = f"{API_URL}/encounters"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "patient_id": patient_id,
                "encounter_type": "follow_up",
                "scheduled_date": datetime.now().isoformat(),
                "provider": "Dr. Smith",
                "location": "Main Clinic - Room 101",
                "chief_complaint": "Follow-up visit",
                "reason_for_visit": "Medication review"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            encounter_id = result["id"]
            print_test_result("Create Test Encounter", True, result)
        except Exception as e:
            print(f"Error creating test encounter: {str(e)}")
            print_test_result("Create Test Encounter", False)
    
    # 3. Create an allergy for the patient (for eRx patients dashboard)
    if patient_id:
        try:
            url = f"{API_URL}/allergies"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "patient_id": patient_id,
                "allergen": "Penicillin",
                "reaction": "Rash",
                "severity": "moderate",
                "created_by": "Dr. Smith"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            print_test_result("Create Test Allergy", True, result)
        except Exception as e:
            print(f"Error creating test allergy: {str(e)}")
            print_test_result("Create Test Allergy", False)
    
    # 4. Create an invoice for the patient (for pending payments dashboard)
    if patient_id:
        try:
            url = f"{API_URL}/invoices"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "patient_id": patient_id,
                "items": [
                    {
                        "description": "Office Visit",
                        "quantity": 1,
                        "unit_price": 150.00,
                        "total": 150.00
                    },
                    {
                        "description": "Lab Work",
                        "quantity": 1,
                        "unit_price": 75.00,
                        "total": 75.00
                    }
                ],
                "tax_rate": 0.07,
                "due_days": 30,
                "notes": "Please pay within 30 days"
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            print_test_result("Create Test Invoice", True, result)
        except Exception as e:
            print(f"Error creating test invoice: {str(e)}")
            print_test_result("Create Test Invoice", False)
    
    return patient_id, encounter_id

def run_dashboard_tests():
    print("\n" + "=" * 80)
    print("TESTING CLINICHUB DASHBOARD API ENDPOINTS")
    print("=" * 80)
    
    # Get admin token for authentication
    token = get_admin_token()
    if not token:
        print("Failed to get admin token. Cannot proceed with tests.")
        return
    
    # Create test data (optional)
    # create_test_data(token)
    
    # Run all dashboard tests
    erx_result = test_erx_patients_dashboard(token)
    daily_log_result = test_daily_log_dashboard(token)
    queue_result = test_patient_queue_dashboard(token)
    payments_result = test_pending_payments_dashboard(token)
    
    # Print summary
    print("\n" + "=" * 80)
    print("DASHBOARD TESTING SUMMARY")
    print("=" * 80)
    print(f"eRx Patients Dashboard: {'PASSED' if erx_result else 'FAILED'}")
    print(f"Daily Log Dashboard: {'PASSED' if daily_log_result else 'FAILED'}")
    print(f"Patient Queue Dashboard: {'PASSED' if queue_result else 'FAILED'}")
    print(f"Pending Payments Dashboard: {'PASSED' if payments_result else 'FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    run_dashboard_tests()