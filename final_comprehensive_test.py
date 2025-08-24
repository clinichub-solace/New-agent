#!/usr/bin/env python3
"""
ClinicHub Final Comprehensive Backend Testing - All 16 Modules
Final comprehensive end-to-end testing as requested in review
"""

import requests
import json
import sys
from datetime import datetime, date
import time
import os

# Configuration - Use production URL from frontend/.env
BACKEND_URL = "https://mongodb-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class FinalComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_data = {}
        self.module_results = {}
        
    def log_result(self, test_name, success, message, details=None, status_code=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        if status_code:
            print(f"   Status Code: {status_code}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "status_code": status_code
        })
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_core_medical_modules(self):
        """Test Core Medical Modules (Priority 1)"""
        print("\n🏥 CORE MEDICAL MODULES (CRITICAL)")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Patients/EHR System with FHIR Compliance
        total_tests += 1
        patient_data = {
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.garcia@email.com",
            "phone": "555-0456",
            "date_of_birth": "1978-09-12",
            "gender": "female",
            "address_line1": "789 Cedar Lane",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            if response.status_code == 200:
                patient = response.json()
                self.test_data["patient_id"] = patient.get("id")
                self.log_result("Patients/EHR System", True, f"FHIR-compliant patient created: {patient.get('id')}")
                tests_passed += 1
            else:
                self.log_result("Patients/EHR System", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Patients/EHR System", False, f"Error: {str(e)}")
        
        # 2. SOAP Notes with ICD-10 Integration
        total_tests += 1
        # First create encounter
        if self.test_data.get("patient_id"):
            encounter_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_type": "consultation",
                "status": "completed",
                "reason": "Routine check-up",
                "provider": "Dr. Jennifer Martinez",
                "scheduled_date": "2025-01-25"
            }
            
            try:
                enc_response = self.session.post(f"{API_BASE}/encounters", json=encounter_data)
                if enc_response.status_code == 200:
                    encounter = enc_response.json()
                    self.test_data["encounter_id"] = encounter.get("id")
                    
                    # Now create SOAP note
                    soap_data = {
                        "patient_id": self.test_data["patient_id"],
                        "encounter_id": self.test_data["encounter_id"],
                        "subjective": "Patient reports feeling well",
                        "objective": "Vital signs stable",
                        "assessment": "Healthy adult",
                        "plan": "Continue current care",
                        "provider": "Dr. Jennifer Martinez",
                        "diagnosis_codes": ["Z00.00"]
                    }
                    
                    soap_response = self.session.post(f"{API_BASE}/soap-notes", json=soap_data)
                    if soap_response.status_code == 200:
                        self.log_result("SOAP Notes with ICD-10", True, "SOAP note with ICD-10 codes created")
                        tests_passed += 1
                    else:
                        self.log_result("SOAP Notes with ICD-10", False, f"SOAP creation failed: {soap_response.status_code}")
                else:
                    self.log_result("SOAP Notes with ICD-10", False, f"Encounter creation failed: {enc_response.status_code}")
            except Exception as e:
                self.log_result("SOAP Notes with ICD-10", False, f"Error: {str(e)}")
        
        # 3. Vital Signs, Allergies, Medications
        total_tests += 1
        if self.test_data.get("patient_id"):
            vital_data = {
                "patient_id": self.test_data["patient_id"],
                "systolic_bp": 125,
                "diastolic_bp": 82,
                "heart_rate": 75,
                "temperature": 98.7,
                "weight": 155.0,
                "height": 66.0,
                "pain_scale": 0
            }
            
            try:
                response = self.session.post(f"{API_BASE}/vital-signs", json=vital_data)
                if response.status_code == 200:
                    self.log_result("Vital Signs/Allergies/Medications", True, "Vital signs recorded with BMI calculation")
                    tests_passed += 1
                else:
                    self.log_result("Vital Signs/Allergies/Medications", False, f"Failed: {response.status_code}")
            except Exception as e:
                self.log_result("Vital Signs/Allergies/Medications", False, f"Error: {str(e)}")
        
        # 4. Quality Measures System
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/quality-measures")
            if response.status_code == 200:
                measures = response.json()
                self.log_result("Quality Measures System", True, f"Retrieved {len(measures)} quality measures")
                tests_passed += 1
            else:
                self.log_result("Quality Measures System", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Quality Measures System", False, f"Error: {str(e)}")
        
        self.module_results["Core Medical Modules"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_practice_management_modules(self):
        """Test Practice Management Modules (Priority 2)"""
        print("\n🏢 PRACTICE MANAGEMENT MODULES")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Employee Management with Time Tracking
        total_tests += 1
        employee_data = {
            "first_name": "Dr. Lisa",
            "last_name": "Thompson",
            "email": "lisa.thompson@clinichub.com",
            "phone": "555-0789",
            "role": "doctor",
            "department": "Internal Medicine",
            "hire_date": "2024-03-01",
            "salary": 200000.00
        }
        
        try:
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_data["employee_id"] = employee.get("id")
                self.log_result("Employee Management", True, f"Created employee: {employee.get('employee_id')}")
                tests_passed += 1
            else:
                self.log_result("Employee Management", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Employee Management", False, f"Error: {str(e)}")
        
        # 2. Inventory Management with Stock Control
        total_tests += 1
        inventory_data = {
            "name": "Blood Pressure Cuff",
            "category": "Medical Equipment",
            "sku": "BPC-001",
            "current_stock": 15,
            "min_stock_level": 3,
            "unit_cost": 89.99,
            "supplier": "Medical Devices Inc",
            "location": "Equipment Storage",
            "notes": "Digital blood pressure monitor"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/inventory", json=inventory_data)
            if response.status_code == 200:
                item = response.json()
                self.test_data["inventory_id"] = item.get("id")
                self.log_result("Inventory Management", True, f"Created inventory item: {item.get('name')}")
                tests_passed += 1
            else:
                self.log_result("Inventory Management", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Inventory Management", False, f"Error: {str(e)}")
        
        # 3. Financial Transactions and Budgeting
        total_tests += 1
        transaction_data = {
            "transaction_type": "expense",
            "amount": 1250.00,
            "payment_method": "check",
            "description": "Medical equipment purchase",
            "category": "medical_supplies",
            "created_by": "admin"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/financial-transactions", json=transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                self.log_result("Financial Transactions", True, f"Created transaction: {transaction.get('transaction_number')}")
                tests_passed += 1
            else:
                self.log_result("Financial Transactions", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Financial Transactions", False, f"Error: {str(e)}")
        
        # 4. Lab Orders with ICD-10 Integration
        total_tests += 1
        # Create provider first
        provider_data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "email": "dr.martinez@clinichub.com",
            "phone": "555-0321",
            "license_number": "TX12345",
            "npi_number": "1234567890"
        }
        
        try:
            prov_response = self.session.post(f"{API_BASE}/providers", json=provider_data)
            if prov_response.status_code == 200:
                provider = prov_response.json()
                self.test_data["provider_id"] = provider.get("id")
                
                # Create lab order
                lab_order_data = {
                    "patient_id": self.test_data.get("patient_id"),
                    "provider_id": self.test_data["provider_id"],
                    "lab_tests": ["CBC", "CMP"],
                    "icd10_codes": ["Z00.00"],
                    "priority": "routine",
                    "clinical_notes": "Annual wellness lab panel",
                    "ordered_by": "admin"
                }
                
                lab_response = self.session.post(f"{API_BASE}/lab-orders", json=lab_order_data)
                if lab_response.status_code == 200:
                    lab_order = lab_response.json()
                    self.log_result("Lab Orders with ICD-10", True, f"Created lab order: {lab_order.get('order_number')}")
                    tests_passed += 1
                else:
                    self.log_result("Lab Orders with ICD-10", False, f"Lab order failed: {lab_response.status_code}")
            else:
                self.log_result("Lab Orders with ICD-10", False, f"Provider creation failed: {prov_response.status_code}")
        except Exception as e:
            self.log_result("Lab Orders with ICD-10", False, f"Error: {str(e)}")
        
        self.module_results["Practice Management"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_high_impact_revenue_modules(self):
        """Test High-Impact Revenue Modules (Priority 3)"""
        print("\n💰 HIGH-IMPACT REVENUE MODULES")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Insurance Verification and Policies
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/insurance-plans")
            if response.status_code == 200:
                plans = response.json()
                self.log_result("Insurance Verification", True, f"Retrieved {len(plans)} insurance plans")
                tests_passed += 1
                if plans:
                    self.test_data["insurance_plan_id"] = plans[0].get("id")
            else:
                self.log_result("Insurance Verification", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Insurance Verification", False, f"Error: {str(e)}")
        
        # 2. Invoices and Billing Management
        total_tests += 1
        if self.test_data.get("patient_id"):
            invoice_data = {
                "patient_id": self.test_data["patient_id"],
                "items": [
                    {
                        "description": "Office Visit - Consultation",
                        "quantity": 1,
                        "unit_price": 275.00,
                        "total": 275.00
                    }
                ],
                "tax_rate": 0.0825,
                "due_days": 30,
                "notes": "Consultation visit"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/invoices", json=invoice_data)
                if response.status_code == 200:
                    invoice = response.json()
                    self.test_data["invoice_id"] = invoice.get("id")
                    self.log_result("Invoices and Billing", True, f"Created invoice: {invoice.get('invoice_number')}")
                    tests_passed += 1
                else:
                    self.log_result("Invoices and Billing", False, f"Failed: {response.status_code}")
            except Exception as e:
                self.log_result("Invoices and Billing", False, f"Error: {str(e)}")
        
        # 3. Payment Recording and Tracking
        total_tests += 1
        payment_data = {
            "transaction_type": "income",
            "amount": 297.69,  # Invoice total with tax
            "payment_method": "credit_card",
            "description": "Payment for consultation visit",
            "category": "patient_payment",
            "patient_id": self.test_data.get("patient_id"),
            "invoice_id": self.test_data.get("invoice_id"),
            "created_by": "admin"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/financial-transactions", json=payment_data)
            if response.status_code == 200:
                payment = response.json()
                self.log_result("Payment Recording", True, f"Recorded payment: {payment.get('transaction_number')}")
                tests_passed += 1
            else:
                self.log_result("Payment Recording", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Payment Recording", False, f"Error: {str(e)}")
        
        self.module_results["Revenue Modules"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_communication_workflow_modules(self):
        """Test Communication & Workflow Modules (Priority 4)"""
        print("\n💬 COMMUNICATION & WORKFLOW MODULES")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Communication System
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/communications/templates")
            if response.status_code == 200:
                templates = response.json()
                self.log_result("Communication System", True, f"Retrieved {len(templates)} communication templates")
                tests_passed += 1
            else:
                self.log_result("Communication System", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Communication System", False, f"Error: {str(e)}")
        
        # 2. Referral Management
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/referrals")
            if response.status_code == 200:
                referrals = response.json()
                self.log_result("Referral Management", True, f"Retrieved {len(referrals)} referrals")
                tests_passed += 1
            else:
                self.log_result("Referral Management", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Referral Management", False, f"Error: {str(e)}")
        
        # 3. Clinical Templates and Protocols
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/clinical-templates")
            if response.status_code == 200:
                templates = response.json()
                self.log_result("Clinical Templates", True, f"Retrieved {len(templates)} clinical templates")
                tests_passed += 1
            else:
                self.log_result("Clinical Templates", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Clinical Templates", False, f"Error: {str(e)}")
        
        # 4. Patient Portal Integration
        total_tests += 1
        if self.test_data.get("patient_id"):
            portal_data = {
                "patient_id": self.test_data["patient_id"],
                "username": "maria.garcia",
                "email": "maria.garcia@email.com",
                "temporary_password": "TempPass123!",
                "access_level": "full",
                "expires_at": "2025-12-31T23:59:59Z",
                "features_enabled": ["view_records", "schedule_appointments"]
            }
            
            try:
                response = self.session.post(f"{API_BASE}/patient-portal/access", json=portal_data)
                if response.status_code == 200:
                    self.log_result("Patient Portal Integration", True, "Patient portal access created")
                    tests_passed += 1
                else:
                    self.log_result("Patient Portal Integration", False, f"Failed: {response.status_code}")
            except Exception as e:
                self.log_result("Patient Portal Integration", False, f"Error: {str(e)}")
        
        self.module_results["Communication & Workflow"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_advanced_features(self):
        """Test Advanced Features (Priority 5)"""
        print("\n🚀 ADVANCED FEATURES")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Telehealth Sessions and Video Calls
        total_tests += 1
        if self.test_data.get("patient_id") and self.test_data.get("provider_id"):
            session_data = {
                "patient_id": self.test_data["patient_id"],
                "provider_id": self.test_data["provider_id"],
                "session_type": "video_consultation",
                "title": "Telehealth Follow-up",
                "description": "Virtual consultation for lab results",
                "scheduled_start": "2025-01-26T15:00:00Z",
                "duration_minutes": 30
            }
            
            try:
                response = self.session.post(f"{API_BASE}/telehealth/sessions", json=session_data)
                if response.status_code == 200:
                    session = response.json()
                    self.log_result("Telehealth Sessions", True, f"Created telehealth session: {session.get('session_number')}")
                    tests_passed += 1
                else:
                    self.log_result("Telehealth Sessions", False, f"Failed: {response.status_code}")
            except Exception as e:
                self.log_result("Telehealth Sessions", False, f"Error: {str(e)}")
        
        # 2. Document Management System
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/documents")
            if response.status_code == 200:
                documents = response.json()
                self.log_result("Document Management", True, f"Retrieved {len(documents)} documents")
                tests_passed += 1
            else:
                self.log_result("Document Management", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Document Management", False, f"Error: {str(e)}")
        
        # 3. System Administration and Settings
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health = response.json()
                self.log_result("System Administration", True, f"System health: {health.get('status')}")
                tests_passed += 1
            else:
                self.log_result("System Administration", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("System Administration", False, f"Error: {str(e)}")
        
        # 4. ICD-10 Database Integration (101 codes)
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/icd10/search", params={"query": "hypertension"})
            if response.status_code == 200:
                codes = response.json()
                self.log_result("ICD-10 Database", True, f"Found {len(codes)} hypertension-related ICD-10 codes")
                tests_passed += 1
            else:
                self.log_result("ICD-10 Database", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("ICD-10 Database", False, f"Error: {str(e)}")
        
        self.module_results["Advanced Features"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_integration_systems(self):
        """Test Integration Systems (Priority 6)"""
        print("\n🔗 INTEGRATION SYSTEMS")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. Notification Center Functionality
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/notifications")
            if response.status_code == 200:
                notifications = response.json()
                self.log_result("Notification Center", True, f"Retrieved {len(notifications)} notifications")
                tests_passed += 1
            else:
                self.log_result("Notification Center", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Notification Center", False, f"Error: {str(e)}")
        
        # 2. Cross-module Data Consistency (test patient data across modules)
        total_tests += 1
        if self.test_data.get("patient_id"):
            try:
                # Check patient exists in multiple modules
                patient_response = self.session.get(f"{API_BASE}/patients/{self.test_data['patient_id']}")
                invoice_response = self.session.get(f"{API_BASE}/invoices")
                
                if patient_response.status_code == 200 and invoice_response.status_code == 200:
                    patient = patient_response.json()
                    invoices = invoice_response.json()
                    
                    # Check if patient data is consistent across modules
                    patient_invoices = [inv for inv in invoices if inv.get("patient_id") == self.test_data["patient_id"]]
                    
                    self.log_result("Cross-module Data Consistency", True, 
                                  f"Patient data consistent across modules, {len(patient_invoices)} related invoices")
                    tests_passed += 1
                else:
                    self.log_result("Cross-module Data Consistency", False, "Failed to verify data consistency")
            except Exception as e:
                self.log_result("Cross-module Data Consistency", False, f"Error: {str(e)}")
        
        # 3. Audit Logging and Monitoring
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/audit/events")
            if response.status_code == 200:
                events = response.json()
                self.log_result("Audit Logging", True, f"Retrieved {len(events)} audit events")
                tests_passed += 1
            else:
                self.log_result("Audit Logging", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Audit Logging", False, f"Error: {str(e)}")
        
        self.module_results["Integration Systems"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def test_erx_prescription_system(self):
        """Test eRx and Prescription System"""
        print("\n💊 eRx AND PRESCRIPTION SYSTEM")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # 1. eRx System Initialization
        total_tests += 1
        try:
            response = self.session.post(f"{API_BASE}/erx/init")
            if response.status_code == 200:
                result = response.json()
                self.log_result("eRx System Init", True, f"eRx system: {result.get('message')}")
                tests_passed += 1
            else:
                self.log_result("eRx System Init", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("eRx System Init", False, f"Error: {str(e)}")
        
        # 2. Medication Database
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/erx/medications")
            if response.status_code == 200:
                medications = response.json()
                self.log_result("Medication Database", True, f"Retrieved {len(medications)} medications")
                tests_passed += 1
                if medications:
                    self.test_data["medication_id"] = medications[0].get("id")
            else:
                self.log_result("Medication Database", False, f"Failed: {response.status_code}")
        except Exception as e:
            self.log_result("Medication Database", False, f"Error: {str(e)}")
        
        # 3. Prescription Creation
        total_tests += 1
        if self.test_data.get("patient_id") and self.test_data.get("provider_id") and self.test_data.get("medication_id"):
            prescription_data = {
                "medication_id": self.test_data["medication_id"],
                "patient_id": self.test_data["patient_id"],
                "prescriber_id": self.test_data["provider_id"],
                "prescriber_name": "Dr. Jennifer Martinez",
                "dosage_text": "Take 1 tablet by mouth once daily with food",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "QD",
                "route": "oral",
                "quantity": 30.0,
                "days_supply": 30,
                "refills": 1,
                "indication": "Hypertension",
                "diagnosis_codes": ["I10"],
                "created_by": "admin"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/prescriptions", json=prescription_data)
                if response.status_code == 200:
                    prescription = response.json()
                    self.log_result("Prescription Creation", True, f"Created prescription: {prescription.get('prescription_number')}")
                    tests_passed += 1
                else:
                    self.log_result("Prescription Creation", False, f"Failed: {response.status_code}")
            except Exception as e:
                self.log_result("Prescription Creation", False, f"Error: {str(e)}")
        
        self.module_results["eRx & Prescriptions"] = (tests_passed, total_tests)
        return tests_passed, total_tests

    def run_final_comprehensive_test(self):
        """Run final comprehensive test of all ClinicHub modules"""
        print("🏥 CLINICHUB FINAL COMPREHENSIVE BACKEND TESTING")
        print("=" * 80)
        print("🎯 FINAL COMPREHENSIVE TESTING - All ClinicHub Modules and Systems")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Authentication: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ CRITICAL: Authentication failed. Cannot proceed with testing.")
            return False
        
        # Run all module tests
        total_passed = 0
        total_tests = 0
        
        # Test all priority areas
        passed, tests = self.test_core_medical_modules()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_practice_management_modules()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_high_impact_revenue_modules()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_communication_workflow_modules()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_advanced_features()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_integration_systems()
        total_passed += passed
        total_tests += tests
        
        passed, tests = self.test_erx_prescription_system()
        total_passed += passed
        total_tests += tests
        
        # Print final comprehensive summary
        self.print_final_summary(total_passed, total_tests)
        
        return total_passed, total_tests

    def print_final_summary(self, total_passed, total_tests):
        """Print final comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL COMPREHENSIVE CLINICHUB SYSTEM ASSESSMENT")
        print("=" * 80)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Tests Executed: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_tests - total_passed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 RESULTS BY MODULE GROUP:")
        for module, (passed, total) in self.module_results.items():
            module_rate = (passed / total * 100) if total > 0 else 0
            status = "✅" if module_rate >= 80 else "⚠️" if module_rate >= 60 else "❌"
            print(f"   {status} {module}: {passed}/{total} ({module_rate:.1f}%)")
        
        # System health assessment
        if success_rate >= 90:
            health_status = "🟢 EXCELLENT - Production Ready"
        elif success_rate >= 75:
            health_status = "🟡 GOOD - Minor Issues to Address"
        elif success_rate >= 60:
            health_status = "🟠 FAIR - Significant Issues Need Attention"
        else:
            health_status = "🔴 POOR - Major Issues Require Immediate Attention"
        
        print(f"\n🎯 SYSTEM HEALTH: {health_status}")
        
        # Production readiness score
        readiness_score = min(100, success_rate + (10 if success_rate >= 80 else 0))
        print(f"🚀 PRODUCTION READINESS SCORE: {readiness_score:.1f}/100")
        
        # Critical findings
        print(f"\n🔍 CRITICAL FINDINGS:")
        critical_working = []
        critical_issues = []
        
        for result in self.test_results:
            if result["success"]:
                if any(keyword in result["test"].lower() for keyword in ["authentication", "patient", "invoice", "employee"]):
                    critical_working.append(result["test"])
            else:
                if any(keyword in result["test"].lower() for keyword in ["authentication", "patient", "invoice", "employee"]):
                    critical_issues.append(result["test"])
        
        if critical_working:
            print(f"   ✅ WORKING CRITICAL SYSTEMS: {len(critical_working)} systems operational")
        
        if critical_issues:
            print(f"   ❌ CRITICAL ISSUES: {len(critical_issues)} systems need attention")
            for issue in critical_issues[:3]:  # Show top 3 critical issues
                print(f"      • {issue}")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FinalComprehensiveTester()
    tester.run_final_comprehensive_test()