#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE CLINICHUB SYSTEM DEBUGGING - COMPLETE BACKEND TESTING

This test conducts the most thorough and exhaustive testing of the entire ClinicHub backend system.
Tests ALL endpoints and functionality as requested in the comprehensive review.

Test Coverage:
1. Authentication & Security (TOP PRIORITY)
2. Core Medical Modules (CRITICAL)
3. Practice Management (BUSINESS CRITICAL)
4. Advanced Features
5. Integration & Workflows
6. Database & Infrastructure
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
print(f"🚀 Starting Comprehensive ClinicHub Backend Testing")
print(f"📡 Using API URL: {API_URL}")
print("=" * 100)

# Global test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "critical_failures": [],
    "authentication_status": "UNKNOWN",
    "admin_token": None
}

# Helper function to print test results
def print_test_result(test_name, success, response=None, critical=False):
    test_results["total_tests"] += 1
    
    if success:
        test_results["passed_tests"] += 1
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            # Show limited response for readability
            response_str = json.dumps(response, indent=2, default=str)
            if len(response_str) > 300:
                response_str = response_str[:300] + "..."
            print(f"   📄 Response: {response_str}")
    else:
        test_results["failed_tests"] += 1
        print(f"❌ {test_name}: FAILED")
        if critical:
            test_results["critical_failures"].append(test_name)
            print(f"🚨 CRITICAL FAILURE: {test_name}")
        if response:
            print(f"   ⚠️  Error: {response}")
    print("-" * 80)

def test_system_health():
    """Test basic system health and connectivity"""
    print("\n🏥 === SYSTEM HEALTH & CONNECTIVITY ===")
    
    # Test 1: Root endpoint
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        response.raise_for_status()
        result = response.json()
        print_test_result("Backend Root Endpoint", True, result, critical=True)
    except Exception as e:
        print_test_result("Backend Root Endpoint", False, str(e), critical=True)
        return False
    
    # Test 2: Health endpoint
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        response.raise_for_status()
        result = response.json()
        print_test_result("Health Check Endpoint", True, result, critical=True)
    except Exception as e:
        print_test_result("Health Check Endpoint", False, str(e), critical=True)
        return False
    
    # Test 3: API Documentation
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
        response.raise_for_status()
        print_test_result("API Documentation Access", True, {"status": "accessible"})
    except Exception as e:
        print_test_result("API Documentation Access", False, str(e))
    
    return True

def test_authentication_security():
    """Test Authentication & Security (TOP PRIORITY)"""
    print("\n🔐 === AUTHENTICATION & SECURITY (TOP PRIORITY) ===")
    
    # Test 1: Initialize Admin User (or check if already exists)
    try:
        response = requests.post(f"{API_URL}/auth/init-admin", timeout=10)
        
        if response.status_code == 400:
            # Admin user already exists - this is fine
            result = response.json()
            if "Admin user already exists" in result.get("detail", ""):
                print_test_result("Initialize Admin User", True, {"status": "Admin user already exists"}, critical=True)
            else:
                print_test_result("Initialize Admin User", False, result.get("detail", "Unknown error"), critical=True)
                return None
        else:
            response.raise_for_status()
            result = response.json()
            
            assert "username" in result
            assert "password" in result
            assert result["username"] == "admin"
            assert result["password"] == "admin123"
            
            print_test_result("Initialize Admin User", True, result, critical=True)
    except Exception as e:
        print_test_result("Initialize Admin User", False, str(e), critical=True)
        return None
    
    # Test 2: Admin Login (admin/admin123)
    try:
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{API_URL}/auth/login", json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert "access_token" in result
        assert "token_type" in result
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"
        
        admin_token = result["access_token"]
        test_results["admin_token"] = admin_token
        test_results["authentication_status"] = "SUCCESS"
        
        print_test_result("Admin Login (admin/admin123)", True, result, critical=True)
        return admin_token
        
    except Exception as e:
        test_results["authentication_status"] = "FAILED"
        print_test_result("Admin Login (admin/admin123)", False, str(e), critical=True)
        return None

def test_jwt_token_validation(admin_token):
    """Test JWT token generation and validation"""
    if not admin_token:
        print_test_result("JWT Token Validation", False, "No admin token available", critical=True)
        return
    
    # Test 3: Get Current User (JWT validation)
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert result["username"] == "admin"
        assert result["role"] == "admin"
        
        print_test_result("JWT Token Validation", True, result, critical=True)
    except Exception as e:
        print_test_result("JWT Token Validation", False, str(e), critical=True)
    
    # Test 4: Protected Endpoint Access
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_URL}/users", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Protected Endpoint Access", True, result)
    except Exception as e:
        print_test_result("Protected Endpoint Access", False, str(e))
    
    # Test 5: Invalid Credentials Test
    try:
        data = {"username": "admin", "password": "wrongpassword"}
        response = requests.post(f"{API_URL}/auth/login", json=data, timeout=10)
        
        assert response.status_code == 401
        result = response.json()
        assert "detail" in result
        
        print_test_result("Invalid Credentials Rejection", True, {"status": "correctly rejected"})
    except Exception as e:
        print_test_result("Invalid Credentials Rejection", False, str(e))

def test_patient_management(admin_token):
    """Test Patient Management (FHIR compliance, CRUD operations, data validation)"""
    print("\n👥 === PATIENT MANAGEMENT (CORE MEDICAL) ===")
    
    if not admin_token:
        print("⚠️ Skipping Patient Management tests - no admin token")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    patient_id = None
    
    # Test 1: Create Patient (FHIR-compliant)
    try:
        data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1990-08-15",
            "gender": "female",
            "address_line1": "456 Healthcare Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(f"{API_URL}/patients", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Verify FHIR compliance
        assert result["resource_type"] == "Patient"
        assert isinstance(result["name"], list)
        assert result["name"][0]["family"] == "Rodriguez"
        assert "Emily" in result["name"][0]["given"]
        
        patient_id = result["id"]
        print_test_result("Create Patient (FHIR-compliant)", True, result, critical=True)
        
    except Exception as e:
        print_test_result("Create Patient (FHIR-compliant)", False, str(e), critical=True)
        return None
    
    # Test 2: Get All Patients
    try:
        response = requests.get(f"{API_URL}/patients", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        print_test_result("Get All Patients", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Get All Patients", False, str(e), critical=True)
    
    # Test 3: Get Patient by ID
    if patient_id:
        try:
            response = requests.get(f"{API_URL}/patients/{patient_id}", headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == patient_id
            print_test_result("Get Patient by ID", True, result)
        except Exception as e:
            print_test_result("Get Patient by ID", False, str(e))
    
    return patient_id

def test_employee_management(admin_token):
    """Test Employee Management (Complete CRUD operations, payroll features)"""
    print("\n👨‍⚕️ === EMPLOYEE MANAGEMENT (BUSINESS CRITICAL) ===")
    
    if not admin_token:
        print("⚠️ Skipping Employee Management tests - no admin token")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    employee_id = None
    
    # Test 1: Create Employee
    try:
        data = {
            "first_name": "Dr. Michael",
            "last_name": "Thompson",
            "email": "dr.thompson@clinichub.com",
            "phone": "+1-555-345-6789",
            "role": "doctor",
            "department": "Cardiology",
            "hire_date": date.today().isoformat(),
            "salary": 180000.00
        }
        
        response = requests.post(f"{API_URL}/employees", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert "employee_id" in result
        assert result["employee_id"].startswith("EMP-")
        
        employee_id = result["id"]
        print_test_result("Create Employee", True, result, critical=True)
        
    except Exception as e:
        print_test_result("Create Employee", False, str(e), critical=True)
        return None
    
    # Test 2: Get All Employees
    try:
        response = requests.get(f"{API_URL}/employees", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get All Employees", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get All Employees", False, str(e), critical=True)
    
    # Test 3: Update Employee
    if employee_id:
        try:
            data = {
                "phone": "+1-555-999-8888",
                "department": "Internal Medicine",
                "salary": 185000.00
            }
            
            response = requests.put(f"{API_URL}/employees/{employee_id}", json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Employee", True, result)
            
        except Exception as e:
            print_test_result("Update Employee", False, str(e))
    
    return employee_id

def test_inventory_management(admin_token):
    """Test Inventory Management (Stock tracking, suppliers, transactions)"""
    print("\n📦 === INVENTORY MANAGEMENT (BUSINESS CRITICAL) ===")
    
    if not admin_token:
        print("⚠️ Skipping Inventory Management tests - no admin token")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    item_id = None
    
    # Test 1: Create Inventory Item
    try:
        data = {
            "name": "Acetaminophen 500mg",
            "category": "Pain Relief",
            "sku": "MED-ACET-500",
            "current_stock": 250,
            "min_stock_level": 50,
            "unit_cost": 0.85,
            "supplier": "PharmaCorp Supplies",
            "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            "location": "Pharmacy Storage - Shelf A3",
            "notes": "Store at room temperature, away from moisture"
        }
        
        response = requests.post(f"{API_URL}/inventory", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        item_id = result["id"]
        print_test_result("Create Inventory Item", True, result, critical=True)
        
    except Exception as e:
        print_test_result("Create Inventory Item", False, str(e), critical=True)
        return None
    
    # Test 2: Get All Inventory Items
    try:
        response = requests.get(f"{API_URL}/inventory", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get All Inventory Items", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get All Inventory Items", False, str(e), critical=True)
    
    # Test 3: Inventory Transaction (Stock In)
    if item_id:
        try:
            data = {
                "transaction_type": "in",
                "quantity": 100,
                "notes": "New shipment received",
                "created_by": "admin"
            }
            
            response = requests.post(f"{API_URL}/inventory/{item_id}/transaction", json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Inventory Transaction (Stock In)", True, result)
            
        except Exception as e:
            print_test_result("Inventory Transaction (Stock In)", False, str(e))
    
    return item_id

def test_financial_system(patient_id, admin_token):
    """Test Financial System (Invoicing, billing, financial transactions, reporting)"""
    print("\n💰 === FINANCIAL SYSTEM (BUSINESS CRITICAL) ===")
    
    if not admin_token:
        print("⚠️ Skipping Financial System tests - no admin token")
        return None, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    invoice_id = None
    transaction_id = None
    
    # Test 1: Create Invoice
    if patient_id:
        try:
            data = {
                "patient_id": patient_id,
                "items": [
                    {
                        "description": "Annual Physical Examination",
                        "quantity": 1,
                        "unit_price": 250.00,
                        "total": 250.00
                    },
                    {
                        "description": "Lab Work - Comprehensive Metabolic Panel",
                        "quantity": 1,
                        "unit_price": 85.00,
                        "total": 85.00
                    }
                ],
                "tax_rate": 0.08,
                "due_days": 30,
                "notes": "Payment due within 30 days. Thank you for choosing ClinicHub."
            }
            
            response = requests.post(f"{API_URL}/invoices", json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            assert "invoice_number" in result
            assert result["invoice_number"].startswith("INV-")
            
            invoice_id = result["id"]
            print_test_result("Create Invoice", True, result, critical=True)
            
        except Exception as e:
            print_test_result("Create Invoice", False, str(e), critical=True)
    
    # Test 2: Get All Invoices
    try:
        response = requests.get(f"{API_URL}/invoices", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get All Invoices", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get All Invoices", False, str(e), critical=True)
    
    # Test 3: Create Financial Transaction
    try:
        data = {
            "transaction_type": "income",
            "amount": 335.00,
            "payment_method": "credit_card",
            "description": "Patient payment for annual physical",
            "category": "patient_payment",
            "patient_id": patient_id,
            "invoice_id": invoice_id,
            "created_by": "admin"
        }
        
        response = requests.post(f"{API_URL}/financial-transactions", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert "transaction_number" in result
        assert result["transaction_number"].startswith("INC-")
        
        transaction_id = result["id"]
        print_test_result("Create Financial Transaction", True, result, critical=True)
        
    except Exception as e:
        print_test_result("Create Financial Transaction", False, str(e), critical=True)
    
    # Test 4: Get All Financial Transactions
    try:
        response = requests.get(f"{API_URL}/financial-transactions", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get All Financial Transactions", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get All Financial Transactions", False, str(e))
    
    return invoice_id, transaction_id

def test_erx_system(patient_id, admin_token):
    """Test Electronic Prescribing (eRx) System"""
    print("\n💊 === ELECTRONIC PRESCRIBING (eRx) SYSTEM ===")
    
    if not admin_token or not patient_id:
        print("⚠️ Skipping eRx tests - missing admin token or patient ID")
        return None, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    medication_id = None
    prescription_id = None
    
    # Test 1: Initialize eRx System
    try:
        response = requests.post(f"{API_URL}/erx/init", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize eRx System", True, result)
        
    except Exception as e:
        print_test_result("Initialize eRx System", False, str(e))
    
    # Test 2: Get eRx Medications Database
    try:
        response = requests.get(f"{API_URL}/erx/medications", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["resource_type"] == "Medication"
        
        medication_id = result[0]["id"]
        print_test_result("Get eRx Medications Database", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get eRx Medications Database", False, str(e))
    
    # Test 3: Create Prescription
    if medication_id:
        try:
            data = {
                "medication_id": medication_id,
                "patient_id": patient_id,
                "prescriber_id": "prescriber-001",
                "prescriber_name": "Dr. Sarah Williams",
                
                # Dosage Information
                "dosage_text": "Take 1 tablet by mouth twice daily with food",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "BID",
                "route": "oral",
                
                # Prescription Details
                "quantity": 60.0,
                "days_supply": 30,
                "refills": 2,
                
                # Clinical Context
                "indication": "Hypertension",
                "diagnosis_codes": ["I10"],
                "special_instructions": "Take with food to reduce stomach upset",
                
                "created_by": "admin"
            }
            
            response = requests.post(f"{API_URL}/prescriptions", json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            assert result["resource_type"] == "MedicationRequest"
            assert "prescription_number" in result
            assert result["prescription_number"].startswith("RX")
            
            prescription_id = result["id"]
            print_test_result("Create Prescription", True, result, critical=True)
            
        except Exception as e:
            print_test_result("Create Prescription", False, str(e), critical=True)
    
    return medication_id, prescription_id

def test_appointment_scheduling(patient_id, admin_token):
    """Test Appointment Scheduling (Booking, calendar, provider schedules)"""
    print("\n📅 === APPOINTMENT SCHEDULING (BUSINESS CRITICAL) ===")
    
    if not admin_token or not patient_id:
        print("⚠️ Skipping Appointment Scheduling tests - missing admin token or patient ID")
        return None, None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    provider_id = None
    appointment_id = None
    
    # Test 1: Create Provider
    try:
        data = {
            "first_name": "Dr. Sarah",
            "last_name": "Williams",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Preventive Care"],
            "license_number": "TX-MD-98765",
            "npi_number": "9876543210",
            "email": "dr.williams@clinichub.com",
            "phone": "+1-555-456-7890",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "17:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(f"{API_URL}/providers", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        print_test_result("Create Provider", True, result)
        
    except Exception as e:
        print_test_result("Create Provider", False, str(e))
    
    # Test 2: Create Appointment
    if provider_id:
        try:
            data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "appointment_date": (date.today() + timedelta(days=7)).isoformat(),
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "consultation",
                "reason": "Follow-up consultation for annual physical results",
                "location": "Main Clinic",
                "scheduled_by": "admin"
            }
            
            response = requests.post(f"{API_URL}/appointments", json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            assert "appointment_number" in result
            assert result["appointment_number"].startswith("APT")
            assert "patient_name" in result
            assert "provider_name" in result
            
            appointment_id = result["id"]
            print_test_result("Create Appointment", True, result, critical=True)
            
        except Exception as e:
            print_test_result("Create Appointment", False, str(e), critical=True)
    
    # Test 3: Get All Appointments
    try:
        response = requests.get(f"{API_URL}/appointments", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get All Appointments", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get All Appointments", False, str(e))
    
    return provider_id, appointment_id

def test_lab_integration(patient_id, admin_token):
    """Test Lab Integration (Lab orders, lab results, test catalogs)"""
    print("\n🧪 === LAB INTEGRATION (CRITICAL) ===")
    
    if not admin_token or not patient_id:
        print("⚠️ Skipping Lab Integration tests - missing admin token or patient ID")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Initialize Lab Tests
    try:
        response = requests.post(f"{API_URL}/lab-tests/init", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Lab Tests", True, result)
        
    except Exception as e:
        print_test_result("Initialize Lab Tests", False, str(e))
    
    # Test 2: Get Lab Tests Catalog
    try:
        response = requests.get(f"{API_URL}/lab-tests", headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("Get Lab Tests Catalog", True, {"count": len(result)})
        
    except Exception as e:
        print_test_result("Get Lab Tests Catalog", False, str(e))
    
    # Test 3: Create Lab Order
    try:
        data = {
            "patient_id": patient_id,
            "provider_name": "Dr. Jennifer Martinez",
            "lab_tests": ["CBC", "CMP"],
            "icd10_codes": ["Z00.00"],
            "priority": "routine",
            "notes": "Annual physical lab work"
        }
        
        response = requests.post(f"{API_URL}/lab-orders", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        assert "order_number" in result
        assert result["order_number"].startswith("LAB-")
        
        print_test_result("Create Lab Order", True, result, critical=True)
        
    except Exception as e:
        print_test_result("Create Lab Order", False, str(e), critical=True)

def generate_final_report():
    """Generate comprehensive final test report"""
    print("\n" + "=" * 100)
    print("🏥 COMPREHENSIVE CLINICHUB BACKEND TEST REPORT")
    print("=" * 100)
    
    # Calculate success rate
    success_rate = (test_results["passed_tests"] / test_results["total_tests"] * 100) if test_results["total_tests"] > 0 else 0
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Tests: {test_results['total_tests']}")
    print(f"   Passed: {test_results['passed_tests']} ✅")
    print(f"   Failed: {test_results['failed_tests']} ❌")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Authentication Status: {test_results['authentication_status']}")
    
    # System Status Assessment
    if success_rate >= 90:
        status = "🟢 EXCELLENT - Production Ready"
    elif success_rate >= 75:
        status = "🟡 GOOD - Minor Issues"
    elif success_rate >= 50:
        status = "🟠 FAIR - Needs Attention"
    else:
        status = "🔴 POOR - Critical Issues"
    
    print(f"\n🎯 SYSTEM STATUS: {status}")
    
    # Critical Failures
    if test_results["critical_failures"]:
        print(f"\n🚨 CRITICAL FAILURES ({len(test_results['critical_failures'])}):")
        for failure in test_results["critical_failures"]:
            print(f"   ❌ {failure}")
    else:
        print(f"\n✅ NO CRITICAL FAILURES DETECTED")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    if test_results["authentication_status"] == "SUCCESS":
        print("   ✅ Authentication system is working correctly")
    else:
        print("   🚨 URGENT: Fix authentication system immediately")
    
    if success_rate >= 80:
        print("   ✅ System is ready for production use")
        print("   📈 Focus on optimizing performance and user experience")
    else:
        print("   ⚠️  System needs significant fixes before production")
        print("   🔧 Address critical failures first")
    
    print("\n" + "=" * 100)
    print("🏁 COMPREHENSIVE TESTING COMPLETED")
    print("=" * 100)

def main():
    """Main test execution function"""
    print("🚀 Starting Comprehensive ClinicHub Backend Testing...")
    
    # Phase 1: System Health & Connectivity
    if not test_system_health():
        print("🚨 CRITICAL: System health check failed. Aborting tests.")
        return
    
    # Phase 2: Authentication & Security (TOP PRIORITY)
    admin_token = test_authentication_security()
    test_jwt_token_validation(admin_token)
    
    # Phase 3: Core Medical Modules (CRITICAL)
    patient_id = test_patient_management(admin_token)
    
    # Phase 4: Practice Management (BUSINESS CRITICAL)
    employee_id = test_employee_management(admin_token)
    inventory_id = test_inventory_management(admin_token)
    invoice_id, transaction_id = test_financial_system(patient_id, admin_token)
    provider_id, appointment_id = test_appointment_scheduling(patient_id, admin_token)
    
    # Phase 5: Advanced Features
    medication_id, prescription_id = test_erx_system(patient_id, admin_token)
    
    # Phase 6: Lab Integration
    test_lab_integration(patient_id, admin_token)
    
    # Generate Final Report
    generate_final_report()

if __name__ == "__main__":
    main()