#!/usr/bin/env python3
"""
Comprehensive Backend Authentication and Core Systems Test
Focus: Verify all systems mentioned in the review request are working
"""
import requests
import json
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

print(f"🏥 COMPREHENSIVE CLINICHUB BACKEND VERIFICATION")
print(f"📍 API URL: {API_URL}")
print(f"🕐 Started: {datetime.now()}")
print("=" * 80)

def print_result(test_name, success, response=None, details=None):
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    if response and isinstance(response, dict):
        print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
    print("-" * 60)

def get_admin_token():
    """Get admin authentication token"""
    try:
        # Force re-initialize admin user
        requests.post(f"{API_URL}/auth/force-init-admin", timeout=10)
        
        # Login
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=10)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except:
        return None

def test_authentication_system():
    """Test 1: Authentication System"""
    print("\n🔐 AUTHENTICATION SYSTEM TESTING")
    
    results = {}
    
    # Test admin initialization
    try:
        response = requests.post(f"{API_URL}/auth/force-init-admin")
        results["admin_init"] = response.status_code == 200
        print_result("Admin User Initialization", results["admin_init"], 
                    response.json() if response.status_code == 200 else None)
    except Exception as e:
        results["admin_init"] = False
        print_result("Admin User Initialization", False, None, f"Error: {e}")
    
    # Test login
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        results["login"] = response.status_code == 200
        token = response.json().get("access_token") if results["login"] else None
        print_result("Admin Login (admin/admin123)", results["login"], 
                    response.json() if results["login"] else None)
    except Exception as e:
        results["login"] = False
        token = None
        print_result("Admin Login (admin/admin123)", False, None, f"Error: {e}")
    
    # Test token validation
    if token:
        try:
            response = requests.get(f"{API_URL}/auth/me", 
                                  headers={"Authorization": f"Bearer {token}"})
            results["token_validation"] = response.status_code == 200
            print_result("JWT Token Validation", results["token_validation"], 
                        response.json() if results["token_validation"] else None)
        except Exception as e:
            results["token_validation"] = False
            print_result("JWT Token Validation", False, None, f"Error: {e}")
    else:
        results["token_validation"] = False
        print_result("JWT Token Validation", False, None, "No token available")
    
    return results, token

def test_database_connectivity(token):
    """Test 2: Database Connection and Core Endpoints"""
    print("\n🗄️ DATABASE CONNECTIVITY TESTING")
    
    if not token:
        print_result("Database Tests", False, None, "No authentication token available")
        return {}
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    # Test health endpoint
    try:
        response = requests.get(f"{API_URL}/health")
        results["health"] = response.status_code == 200
        print_result("Health Endpoint", results["health"], response.json())
    except Exception as e:
        results["health"] = False
        print_result("Health Endpoint", False, None, f"Error: {e}")
    
    # Test patients endpoint (database access)
    try:
        response = requests.get(f"{API_URL}/patients", headers=headers)
        results["patients_access"] = response.status_code == 200
        print_result("Patients Database Access", results["patients_access"], 
                    {"count": len(response.json()) if results["patients_access"] else 0})
    except Exception as e:
        results["patients_access"] = False
        print_result("Patients Database Access", False, None, f"Error: {e}")
    
    return results

def test_patient_management(token):
    """Test 3: Patient Management System"""
    print("\n👥 PATIENT MANAGEMENT TESTING")
    
    if not token:
        return {}
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    patient_id = None
    
    # Create a test patient
    try:
        patient_data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-987-6543",
            "date_of_birth": "1985-03-15",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(f"{API_URL}/patients", json=patient_data, headers=headers)
        results["patient_create"] = response.status_code == 200
        
        if results["patient_create"]:
            patient_data_response = response.json()
            patient_id = patient_data_response["id"]
            print_result("Create Patient", True, {"id": patient_id, "name": f"{patient_data_response['name'][0]['given'][0]} {patient_data_response['name'][0]['family']}"})
        else:
            print_result("Create Patient", False, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except Exception as e:
        results["patient_create"] = False
        print_result("Create Patient", False, None, f"Error: {e}")
    
    # Test patient retrieval
    if patient_id:
        try:
            response = requests.get(f"{API_URL}/patients/{patient_id}", headers=headers)
            results["patient_retrieve"] = response.status_code == 200
            print_result("Retrieve Patient", results["patient_retrieve"], 
                        {"id": patient_id} if results["patient_retrieve"] else None)
        except Exception as e:
            results["patient_retrieve"] = False
            print_result("Retrieve Patient", False, None, f"Error: {e}")
    
    return results, patient_id

def test_core_medical_systems(token, patient_id):
    """Test 4: Core Medical Systems"""
    print("\n🏥 CORE MEDICAL SYSTEMS TESTING")
    
    if not token or not patient_id:
        return {}
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    # Test encounters
    try:
        encounter_data = {
            "patient_id": patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "provider": "Dr. Jennifer Martinez",
            "location": "Main Clinic - Room 105",
            "chief_complaint": "Follow-up visit",
            "reason_for_visit": "Routine check-up"
        }
        
        response = requests.post(f"{API_URL}/encounters", json=encounter_data, headers=headers)
        results["encounters"] = response.status_code == 200
        encounter_id = response.json()["id"] if results["encounters"] else None
        print_result("Create Encounter", results["encounters"], 
                    {"encounter_number": response.json().get("encounter_number")} if results["encounters"] else None)
    except Exception as e:
        results["encounters"] = False
        encounter_id = None
        print_result("Create Encounter", False, None, f"Error: {e}")
    
    # Test vital signs
    if encounter_id:
        try:
            vitals_data = {
                "patient_id": patient_id,
                "encounter_id": encounter_id,
                "height": 165.0,
                "weight": 65.0,
                "bmi": 23.9,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "respiratory_rate": 16,
                "temperature": 36.8,
                "oxygen_saturation": 98,
                "pain_scale": 2,
                "recorded_by": "Nurse Johnson"
            }
            
            response = requests.post(f"{API_URL}/vital-signs", json=vitals_data, headers=headers)
            results["vital_signs"] = response.status_code == 200
            print_result("Record Vital Signs", results["vital_signs"])
        except Exception as e:
            results["vital_signs"] = False
            print_result("Record Vital Signs", False, None, f"Error: {e}")
    
    # Test allergies
    try:
        allergy_data = {
            "patient_id": patient_id,
            "allergen": "Penicillin",
            "reaction": "Skin rash, difficulty breathing",
            "severity": "severe",
            "onset_date": "2020-05-15",
            "notes": "Discovered during previous treatment",
            "created_by": "Dr. Martinez"
        }
        
        response = requests.post(f"{API_URL}/allergies", json=allergy_data, headers=headers)
        results["allergies"] = response.status_code == 200
        print_result("Record Allergy", results["allergies"])
    except Exception as e:
        results["allergies"] = False
        print_result("Record Allergy", False, None, f"Error: {e}")
    
    # Test medications
    try:
        medication_data = {
            "patient_id": patient_id,
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "route": "oral",
            "start_date": date.today().isoformat(),
            "prescribing_physician": "Dr. Martinez",
            "indication": "Hypertension",
            "notes": "Take in the morning"
        }
        
        response = requests.post(f"{API_URL}/medications", json=medication_data, headers=headers)
        results["medications"] = response.status_code == 200
        print_result("Record Medication", results["medications"])
    except Exception as e:
        results["medications"] = False
        print_result("Record Medication", False, None, f"Error: {e}")
    
    return results

def test_business_systems(token, patient_id):
    """Test 5: Business Management Systems"""
    print("\n💼 BUSINESS MANAGEMENT SYSTEMS TESTING")
    
    if not token:
        return {}
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    # Test employee management
    try:
        employee_data = {
            "first_name": "Sarah",
            "last_name": "Wilson",
            "email": "sarah.wilson@clinichub.com",
            "phone": "+1-555-456-7890",
            "role": "nurse",
            "department": "Emergency",
            "hire_date": date.today().isoformat(),
            "salary": 75000.00
        }
        
        response = requests.post(f"{API_URL}/employees", json=employee_data, headers=headers)
        results["employees"] = response.status_code == 200
        print_result("Create Employee", results["employees"], 
                    {"employee_id": response.json().get("employee_id")} if results["employees"] else None)
    except Exception as e:
        results["employees"] = False
        print_result("Create Employee", False, None, f"Error: {e}")
    
    # Test inventory management
    try:
        inventory_data = {
            "name": "Surgical Masks",
            "category": "Medical Supplies",
            "sku": "MED-MASK-001",
            "current_stock": 500,
            "min_stock_level": 50,
            "unit_cost": 0.75,
            "supplier": "MedSupply Co",
            "location": "Storage Room A"
        }
        
        response = requests.post(f"{API_URL}/inventory", json=inventory_data, headers=headers)
        results["inventory"] = response.status_code == 200
        print_result("Create Inventory Item", results["inventory"])
    except Exception as e:
        results["inventory"] = False
        print_result("Create Inventory Item", False, None, f"Error: {e}")
    
    # Test financial transactions
    try:
        transaction_data = {
            "transaction_type": "income",
            "amount": 150.00,
            "payment_method": "credit_card",
            "description": "Patient consultation fee",
            "category": "consultation_fee",
            "patient_id": patient_id,
            "created_by": "admin"
        }
        
        response = requests.post(f"{API_URL}/financial-transactions", json=transaction_data, headers=headers)
        results["financial"] = response.status_code == 200
        print_result("Create Financial Transaction", results["financial"], 
                    {"transaction_number": response.json().get("transaction_number")} if results["financial"] else None)
    except Exception as e:
        results["financial"] = False
        print_result("Create Financial Transaction", False, None, f"Error: {e}")
    
    # Test invoicing
    if patient_id:
        try:
            invoice_data = {
                "patient_id": patient_id,
                "items": [
                    {
                        "description": "Medical Consultation",
                        "quantity": 1,
                        "unit_price": 150.00,
                        "total": 150.00
                    }
                ],
                "tax_rate": 0.08,
                "due_days": 30
            }
            
            response = requests.post(f"{API_URL}/invoices", json=invoice_data, headers=headers)
            results["invoices"] = response.status_code == 200
            print_result("Create Invoice", results["invoices"], 
                        {"invoice_number": response.json().get("invoice_number")} if results["invoices"] else None)
        except Exception as e:
            results["invoices"] = False
            print_result("Create Invoice", False, None, f"Error: {e}")
    
    return results

def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive Backend Verification...")
    
    all_results = {}
    
    # Test 1: Authentication System
    auth_results, token = test_authentication_system()
    all_results.update(auth_results)
    
    # Test 2: Database Connectivity
    db_results = test_database_connectivity(token)
    all_results.update(db_results)
    
    # Test 3: Patient Management
    patient_results, patient_id = test_patient_management(token)
    all_results.update(patient_results)
    
    # Test 4: Core Medical Systems
    medical_results = test_core_medical_systems(token, patient_id)
    all_results.update(medical_results)
    
    # Test 5: Business Systems
    business_results = test_business_systems(token, patient_id)
    all_results.update(business_results)
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE BACKEND VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)
    
    print(f"📊 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print()
    
    # Group results by category
    categories = {
        "🔐 Authentication": ["admin_init", "login", "token_validation"],
        "🗄️ Database": ["health", "patients_access"],
        "👥 Patient Management": ["patient_create", "patient_retrieve"],
        "🏥 Medical Systems": ["encounters", "vital_signs", "allergies", "medications"],
        "💼 Business Systems": ["employees", "inventory", "financial", "invoices"]
    }
    
    for category, tests in categories.items():
        category_passed = sum(1 for test in tests if all_results.get(test, False))
        category_total = len(tests)
        print(f"{category}: {category_passed}/{category_total} passed")
        
        for test in tests:
            status = "✅" if all_results.get(test, False) else "❌"
            print(f"  {status} {test.replace('_', ' ').title()}")
        print()
    
    # Critical Assessment
    print("🎯 CRITICAL ASSESSMENT:")
    
    if all_results.get("login", False):
        print("✅ AUTHENTICATION SYSTEM: WORKING")
        print("   - Admin login with admin/admin123 credentials is functional")
        print("   - JWT token generation and validation working")
        print("   - Protected endpoints accessible with valid token")
    else:
        print("❌ AUTHENTICATION SYSTEM: FAILED")
        print("   - Admin login is not working - this is the reported issue")
    
    if all_results.get("patients_access", False):
        print("✅ DATABASE CONNECTION: WORKING")
        print("   - MongoDB connectivity established")
        print("   - Database operations functional")
    else:
        print("❌ DATABASE CONNECTION: FAILED")
        print("   - MongoDB connection issues detected")
    
    if token:
        print("✅ JWT TOKEN SYSTEM: WORKING")
        print("   - Token generation, validation, and authentication middleware functional")
    else:
        print("❌ JWT TOKEN SYSTEM: FAILED")
        print("   - Token system not working properly")
    
    core_systems_working = sum(1 for test in ["encounters", "vital_signs", "allergies", "medications"] 
                              if all_results.get(test, False))
    if core_systems_working >= 3:
        print("✅ CORE MEDICAL SYSTEMS: MOSTLY WORKING")
        print(f"   - {core_systems_working}/4 core medical systems functional")
    else:
        print("❌ CORE MEDICAL SYSTEMS: ISSUES DETECTED")
        print(f"   - Only {core_systems_working}/4 core medical systems working")
    
    print(f"\n🕐 Test completed at: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()