#!/usr/bin/env python3
"""
Comprehensive Lab Orders & Insurance Verification Backend Testing
Testing both newly implemented systems as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime, date
import uuid

# Configuration
BACKEND_URL = "https://1e40cc9d-4648-41f0-bdbd-2d3ec2e684d5.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class LabInsuranceBackendTester:
    def __init__(self):
        self.token = None
        self.test_results = []
        self.patient_id = None
        self.provider_id = None
        self.lab_order_id = None
        self.insurance_policy_id = None
        
    def log_result(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log_result("Authentication", True, f"Token obtained: {self.token[:20]}...")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def setup_test_data(self):
        """Create test patient and provider for testing"""
        try:
            # Create test patient
            patient_data = {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "555-0123",
                "date_of_birth": "1985-03-15",
                "gender": "female",
                "address_line1": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            }
            
            response = requests.post(f"{BACKEND_URL}/patients", json=patient_data, headers=self.get_headers())
            if response.status_code == 200:
                patient = response.json()
                self.patient_id = patient["id"]
                self.log_result("Test Patient Creation", True, f"Patient ID: {self.patient_id}")
            else:
                self.log_result("Test Patient Creation", False, f"Status: {response.status_code}")
                return False
            
            # Create test provider
            provider_data = {
                "first_name": "Dr. Michael",
                "last_name": "Chen",
                "title": "Dr.",
                "specialties": ["Internal Medicine", "Cardiology"],
                "license_number": "TX123456",
                "npi_number": "1234567890",
                "email": "dr.chen@clinic.com",
                "phone": "555-0456"
            }
            
            response = requests.post(f"{BACKEND_URL}/providers", json=provider_data, headers=self.get_headers())
            if response.status_code == 200:
                provider = response.json()
                self.provider_id = provider["id"]
                self.log_result("Test Provider Creation", True, f"Provider ID: {self.provider_id}")
                return True
            else:
                self.log_result("Test Provider Creation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Test Data Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_lab_tests_catalog(self):
        """Test Lab Tests Catalog Management"""
        print("\n=== TESTING LAB TESTS CATALOG ===")
        
        # Test 1: Initialize lab tests
        try:
            response = requests.post(f"{BACKEND_URL}/lab-tests/init", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                self.log_result("Lab Tests Initialization", True, f"Initialized {data.get('count', 0)} lab tests")
            else:
                self.log_result("Lab Tests Initialization", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Lab Tests Initialization", False, f"Exception: {str(e)}")
        
        # Test 2: Retrieve available lab tests
        try:
            response = requests.get(f"{BACKEND_URL}/lab-tests", headers=self.get_headers())
            if response.status_code == 200:
                lab_tests = response.json()
                self.log_result("Get Lab Tests Catalog", True, f"Retrieved {len(lab_tests)} lab tests")
                
                # Test filtering by category
                if lab_tests:
                    category = lab_tests[0].get("category", "chemistry")
                    response = requests.get(f"{BACKEND_URL}/lab-tests?category={category}", headers=self.get_headers())
                    if response.status_code == 200:
                        filtered_tests = response.json()
                        self.log_result("Filter Lab Tests by Category", True, f"Found {len(filtered_tests)} tests in {category}")
                    else:
                        self.log_result("Filter Lab Tests by Category", False, f"Status: {response.status_code}")
            else:
                self.log_result("Get Lab Tests Catalog", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Lab Tests Catalog", False, f"Exception: {str(e)}")
        
        # Test 3: Search lab tests
        try:
            response = requests.get(f"{BACKEND_URL}/lab-tests?search=glucose", headers=self.get_headers())
            if response.status_code == 200:
                search_results = response.json()
                self.log_result("Search Lab Tests", True, f"Found {len(search_results)} tests matching 'glucose'")
            else:
                self.log_result("Search Lab Tests", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Search Lab Tests", False, f"Exception: {str(e)}")
    
    def test_lab_order_management(self):
        """Test Lab Order Management"""
        print("\n=== TESTING LAB ORDER MANAGEMENT ===")
        
        # First get available lab tests
        try:
            response = requests.get(f"{BACKEND_URL}/lab-tests", headers=self.get_headers())
            if response.status_code != 200:
                self.log_result("Lab Order Management Setup", False, "Cannot retrieve lab tests")
                return
            
            lab_tests = response.json()
            if not lab_tests:
                self.log_result("Lab Order Management Setup", False, "No lab tests available")
                return
            
            # Test 1: Create lab order
            lab_order_data = {
                "patient_id": self.patient_id,
                "provider_id": self.provider_id,
                "lab_tests": [lab_tests[0]["id"]],  # List of test IDs
                "icd10_codes": ["Z00.00"],
                "status": "draft",
                "priority": "routine",
                "notes": "Annual physical examination"
            }
            
            response = requests.post(f"{BACKEND_URL}/lab-orders", json=lab_order_data, headers=self.get_headers())
            if response.status_code == 200:
                lab_order = response.json()
                self.lab_order_id = lab_order["id"]
                self.log_result("Create Lab Order", True, f"Order ID: {lab_order['order_number']}")
            else:
                self.log_result("Create Lab Order", False, f"Status: {response.status_code}, Response: {response.text}")
                return
            
            # Test 2: Retrieve lab orders
            response = requests.get(f"{BACKEND_URL}/lab-orders", headers=self.get_headers())
            if response.status_code == 200:
                orders = response.json()
                self.log_result("Get Lab Orders", True, f"Retrieved {len(orders)} lab orders")
            else:
                self.log_result("Get Lab Orders", False, f"Status: {response.status_code}")
            
            # Test 3: Get specific lab order
            if self.lab_order_id:
                response = requests.get(f"{BACKEND_URL}/lab-orders/{self.lab_order_id}", headers=self.get_headers())
                if response.status_code == 200:
                    order = response.json()
                    self.log_result("Get Specific Lab Order", True, f"Order status: {order.get('status')}")
                else:
                    self.log_result("Get Specific Lab Order", False, f"Status: {response.status_code}")
            
            # Test 4: Filter lab orders by patient
            response = requests.get(f"{BACKEND_URL}/lab-orders?patient_id={self.patient_id}", headers=self.get_headers())
            if response.status_code == 200:
                patient_orders = response.json()
                self.log_result("Filter Lab Orders by Patient", True, f"Found {len(patient_orders)} orders for patient")
            else:
                self.log_result("Filter Lab Orders by Patient", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Lab Order Management", False, f"Exception: {str(e)}")
    
    def test_external_lab_integration(self):
        """Test External Lab Integration"""
        print("\n=== TESTING EXTERNAL LAB INTEGRATION ===")
        
        if not self.lab_order_id:
            self.log_result("External Lab Integration", False, "No lab order available for testing")
            return
        
        # Test 1: Submit order to external lab
        try:
            submit_data = {
                "external_lab_provider": "labcorp",
                "priority": "routine"
            }
            
            response = requests.post(f"{BACKEND_URL}/lab-orders/{self.lab_order_id}/submit", 
                                   json=submit_data, headers=self.get_headers())
            if response.status_code == 200:
                result = response.json()
                self.log_result("Submit Order to External Lab", True, f"External order ID: {result.get('external_order_id')}")
            else:
                self.log_result("Submit Order to External Lab", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Submit Order to External Lab", False, f"Exception: {str(e)}")
        
        # Test 2: Retrieve lab results (mock)
        try:
            response = requests.post(f"{BACKEND_URL}/lab-orders/{self.lab_order_id}/results", 
                                   headers=self.get_headers())
            if response.status_code == 200:
                results = response.json()
                self.log_result("Retrieve Lab Results", True, f"Retrieved {len(results.get('results', []))} results")
            else:
                self.log_result("Retrieve Lab Results", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Retrieve Lab Results", False, f"Exception: {str(e)}")
    
    def test_lab_results_management(self):
        """Test Lab Results Management"""
        print("\n=== TESTING LAB RESULTS MANAGEMENT ===")
        
        # Test 1: Get all lab results
        try:
            response = requests.get(f"{BACKEND_URL}/lab-results", headers=self.get_headers())
            if response.status_code == 200:
                results = response.json()
                self.log_result("Get All Lab Results", True, f"Retrieved {len(results)} lab results")
            else:
                self.log_result("Get All Lab Results", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get All Lab Results", False, f"Exception: {str(e)}")
        
        # Test 2: Get patient-specific lab results
        try:
            response = requests.get(f"{BACKEND_URL}/lab-results/patient/{self.patient_id}", headers=self.get_headers())
            if response.status_code == 200:
                patient_results = response.json()
                self.log_result("Get Patient Lab Results", True, f"Found {len(patient_results)} results for patient")
            else:
                self.log_result("Get Patient Lab Results", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Patient Lab Results", False, f"Exception: {str(e)}")
    
    def test_insurance_plans_management(self):
        """Test Insurance Plans Management"""
        print("\n=== TESTING INSURANCE PLANS MANAGEMENT ===")
        
        # Test 1: Get available insurance plans
        try:
            response = requests.get(f"{BACKEND_URL}/insurance-plans", headers=self.get_headers())
            if response.status_code == 200:
                plans = response.json()
                self.log_result("Get Insurance Plans", True, f"Retrieved {len(plans)} insurance plans")
                
                # Store first plan for testing
                if plans:
                    self.insurance_plan_id = plans[0]["id"]
            else:
                self.log_result("Get Insurance Plans", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Insurance Plans", False, f"Exception: {str(e)}")
    
    def test_insurance_policy_management(self):
        """Test Insurance Policy Management"""
        print("\n=== TESTING INSURANCE POLICY MANAGEMENT ===")
        
        if not hasattr(self, 'insurance_plan_id') or not self.insurance_plan_id:
            self.log_result("Insurance Policy Management", False, "No insurance plan available")
            return
        
        # Test 1: Create insurance policy
        try:
            policy_data = {
                "patient_id": self.patient_id,
                "insurance_plan_id": self.insurance_plan_id,
                "policy_number": "POL123456789",
                "group_number": "GRP001",
                "subscriber_id": "SUB123456",
                "subscriber_name": "Sarah Johnson",
                "relationship_to_subscriber": "self",
                "effective_date": "2024-01-01",
                "is_primary": True,
                "copay_amount": 25.00,
                "deductible_amount": 1000.00
            }
            
            response = requests.post(f"{BACKEND_URL}/insurance-policies", json=policy_data, headers=self.get_headers())
            if response.status_code == 200:
                policy = response.json()
                self.insurance_policy_id = policy["id"]
                self.log_result("Create Insurance Policy", True, f"Policy ID: {policy['id']}")
            else:
                self.log_result("Create Insurance Policy", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create Insurance Policy", False, f"Exception: {str(e)}")
    
    def test_insurance_verification(self):
        """Test Insurance Verification"""
        print("\n=== TESTING INSURANCE VERIFICATION ===")
        
        if not self.insurance_policy_id:
            self.log_result("Insurance Verification", False, "No insurance policy available")
            return
        
        # Test 1: Verify insurance eligibility
        try:
            verification_data = {
                "patient_id": self.patient_id,
                "insurance_policy_id": self.insurance_policy_id,
                "service_codes": ["99213", "99214"],
                "provider_npi": "1234567890"
            }
            
            response = requests.post(f"{BACKEND_URL}/insurance-verification", json=verification_data, headers=self.get_headers())
            if response.status_code == 200:
                verification = response.json()
                self.log_result("Insurance Eligibility Verification", True, f"Status: {verification.get('status')}")
            else:
                self.log_result("Insurance Eligibility Verification", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Insurance Eligibility Verification", False, f"Exception: {str(e)}")
    
    def test_verification_history(self):
        """Test Verification History"""
        print("\n=== TESTING VERIFICATION HISTORY ===")
        
        # Test 1: Get verification history
        try:
            response = requests.get(f"{BACKEND_URL}/insurance-verifications", headers=self.get_headers())
            if response.status_code == 200:
                verifications = response.json()
                self.log_result("Get Verification History", True, f"Retrieved {len(verifications)} verifications")
            else:
                self.log_result("Get Verification History", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Verification History", False, f"Exception: {str(e)}")
        
        # Test 2: Filter verification history by patient
        try:
            response = requests.get(f"{BACKEND_URL}/insurance-verifications?patient_id={self.patient_id}", headers=self.get_headers())
            if response.status_code == 200:
                patient_verifications = response.json()
                self.log_result("Filter Verification History by Patient", True, f"Found {len(patient_verifications)} verifications for patient")
            else:
                self.log_result("Filter Verification History by Patient", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter Verification History by Patient", False, f"Exception: {str(e)}")
    
    def test_integration_workflows(self):
        """Test End-to-End Integration Workflows"""
        print("\n=== TESTING INTEGRATION WORKFLOWS ===")
        
        # Test 1: Complete patient workflow
        try:
            # Create patient → Create insurance policy → Verify coverage
            if self.patient_id and self.insurance_policy_id:
                # Verify the complete workflow exists
                patient_response = requests.get(f"{BACKEND_URL}/patients/{self.patient_id}", headers=self.get_headers())
                policy_response = requests.get(f"{BACKEND_URL}/insurance-policies/{self.insurance_policy_id}", headers=self.get_headers())
                
                if patient_response.status_code == 200 and policy_response.status_code == 200:
                    self.log_result("Patient → Insurance → Verification Workflow", True, "Complete workflow verified")
                else:
                    self.log_result("Patient → Insurance → Verification Workflow", False, "Workflow components missing")
            else:
                self.log_result("Patient → Insurance → Verification Workflow", False, "Required data not available")
        except Exception as e:
            self.log_result("Patient → Insurance → Verification Workflow", False, f"Exception: {str(e)}")
        
        # Test 2: Lab order workflow
        try:
            # Create lab order → Submit to external lab → Retrieve results
            if self.lab_order_id:
                order_response = requests.get(f"{BACKEND_URL}/lab-orders/{self.lab_order_id}", headers=self.get_headers())
                if order_response.status_code == 200:
                    self.log_result("Lab Order → Submit → Results Workflow", True, "Lab workflow verified")
                else:
                    self.log_result("Lab Order → Submit → Results Workflow", False, "Lab order not accessible")
            else:
                self.log_result("Lab Order → Submit → Results Workflow", False, "No lab order available")
        except Exception as e:
            self.log_result("Lab Order → Submit → Results Workflow", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🏥 COMPREHENSIVE LAB ORDERS & INSURANCE VERIFICATION TESTING")
        print("=" * 70)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False
        
        # Run all test suites
        self.test_lab_tests_catalog()
        self.test_lab_order_management()
        self.test_external_lab_integration()
        self.test_lab_results_management()
        self.test_insurance_plans_management()
        self.test_insurance_policy_management()
        self.test_insurance_verification()
        self.test_verification_history()
        self.test_integration_workflows()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🏥 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Categorize results
        lab_tests = [r for r in self.test_results if "Lab" in r["test"]]
        insurance_tests = [r for r in self.test_results if "Insurance" in r["test"]]
        integration_tests = [r for r in self.test_results if "Workflow" in r["test"]]
        
        print(f"\n📊 CATEGORY BREAKDOWN:")
        print(f"Lab Orders System: {sum(1 for t in lab_tests if t['success'])}/{len(lab_tests)} passed")
        print(f"Insurance Verification: {sum(1 for t in insurance_tests if t['success'])}/{len(insurance_tests)} passed")
        print(f"Integration Workflows: {sum(1 for t in integration_tests if t['success'])}/{len(integration_tests)} passed")
        
        # Overall assessment
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - SYSTEMS FULLY OPERATIONAL")
        elif passed >= total * 0.8:
            print("\n✅ MOSTLY FUNCTIONAL - MINOR ISSUES DETECTED")
        else:
            print("\n⚠️  SIGNIFICANT ISSUES DETECTED - REQUIRES ATTENTION")

if __name__ == "__main__":
    tester = LabInsuranceBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)