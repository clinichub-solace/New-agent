#!/usr/bin/env python3
"""
ClinicHub Backend Testing - Receipt Generation and Employee Clock-In/Out
Testing the newly added Receipt Generation and Employee Clock-In/Out functionality
"""

import requests
import json
import sys
from datetime import datetime, date
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class ClinicHubTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
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
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def create_test_patient(self):
        """Create a test patient for receipt generation"""
        try:
            patient_data = {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "555-0123",
                "date_of_birth": "1985-03-15",
                "gender": "female",
                "address_line1": "123 Main Street",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            }
            
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            
            if response.status_code == 200:
                patient = response.json()
                patient_id = patient.get("id")
                self.log_result("Create Test Patient", True, f"Created patient Sarah Johnson with ID: {patient_id}")
                return patient_id
            else:
                self.log_result("Create Test Patient", False, f"Failed to create patient: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Patient", False, f"Error creating patient: {str(e)}")
            return None
    
    def create_test_employee(self):
        """Create a test employee for clock-in/out testing"""
        try:
            employee_data = {
                "first_name": "Michael",
                "last_name": "Davis",
                "email": "michael.davis@clinichub.com",
                "phone": "555-0456",
                "role": "nurse",
                "department": "Emergency",
                "hire_date": "2024-01-15",
                "hourly_rate": 35.00
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee.get("id")
                self.log_result("Create Test Employee", True, f"Created employee Michael Davis with ID: {employee_id}")
                return employee_id
            else:
                self.log_result("Create Test Employee", False, f"Failed to create employee: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Employee", False, f"Error creating employee: {str(e)}")
            return None
    
    def create_test_soap_note(self, patient_id):
        """Create a test SOAP note for receipt generation"""
        try:
            soap_data = {
                "patient_id": patient_id,
                "encounter_id": f"ENC-{datetime.now().strftime('%Y%m%d')}-TEST",
                "chief_complaint": "Annual wellness check",
                "subjective": "Patient reports feeling well overall. No acute complaints.",
                "objective": "Vital signs stable. Physical exam unremarkable.",
                "assessment": "Healthy adult, annual wellness visit",
                "plan": "Continue current health maintenance. Return in 1 year for annual check.",
                "provider_name": "Dr. Test Provider"
            }
            
            response = self.session.post(f"{API_BASE}/soap-notes", json=soap_data)
            
            if response.status_code == 200:
                soap_note = response.json()
                soap_id = soap_note.get("id")
                self.log_result("Create Test SOAP Note", True, f"Created SOAP note with ID: {soap_id}")
                return soap_id
            else:
                self.log_result("Create Test SOAP Note", False, f"Failed to create SOAP note: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test SOAP Note", False, f"Error creating SOAP note: {str(e)}")
            return None
    
    def test_receipt_generation_endpoints(self):
        """Test all receipt generation endpoints"""
        print("\n🧾 TESTING RECEIPT GENERATION ENDPOINTS")
        print("=" * 50)
        
        # Create test patient and SOAP note
        patient_id = self.create_test_patient()
        if not patient_id:
            return False
        
        soap_id = self.create_test_soap_note(patient_id)
        if not soap_id:
            return False
        
        # Test 1: GET /api/receipts (should work - list receipts)
        try:
            response = self.session.get(f"{API_BASE}/receipts")
            if response.status_code == 200:
                receipts = response.json()
                self.log_result("GET /api/receipts", True, f"Successfully retrieved {len(receipts)} receipts")
            else:
                self.log_result("GET /api/receipts", False, f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/receipts", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/receipts/soap-note/{id} (receipt generation)
        receipt_id = None
        try:
            response = self.session.post(f"{API_BASE}/receipts/soap-note/{soap_id}")
            if response.status_code == 200:
                result = response.json()
                receipt_id = result.get("receipt", {}).get("id")
                receipt_number = result.get("receipt", {}).get("receipt_number")
                self.log_result("POST /api/receipts/soap-note/{id}", True, 
                              f"Successfully generated receipt {receipt_number} with ID: {receipt_id}")
            else:
                self.log_result("POST /api/receipts/soap-note/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/receipts/soap-note/{id}", False, f"Error: {str(e)}")
        
        # Test 3: GET /api/receipts/{id} (individual receipt fetch)
        if receipt_id:
            try:
                response = self.session.get(f"{API_BASE}/receipts/{receipt_id}")
                if response.status_code == 200:
                    receipt = response.json()
                    patient_name = receipt.get("patient_name")
                    total = receipt.get("total")
                    self.log_result("GET /api/receipts/{id}", True, 
                                  f"Successfully retrieved receipt for {patient_name}, total: ${total}")
                else:
                    self.log_result("GET /api/receipts/{id}", False, 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("GET /api/receipts/{id}", False, f"Error: {str(e)}")
        else:
            self.log_result("GET /api/receipts/{id}", False, "Skipped - no receipt ID available")
        
        return True
    
    def test_employee_clock_endpoints(self):
        """Test all employee clock-in/out endpoints"""
        print("\n⏰ TESTING EMPLOYEE CLOCK-IN/OUT ENDPOINTS")
        print("=" * 50)
        
        # Create test employee
        employee_id = self.create_test_employee()
        if not employee_id:
            return False
        
        # Test 1: GET /api/employees/{id}/time-status (initial status check)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                self.log_result("GET /api/employees/{id}/time-status (initial)", True, 
                              f"Employee status: {current_status}")
            else:
                self.log_result("GET /api/employees/{id}/time-status (initial)", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-status (initial)", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/employees/{id}/clock-in (clock in functionality)
        try:
            response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-in", 
                                       params={"location": "Emergency Department"})
            if response.status_code == 200:
                result = response.json()
                timestamp = result.get("timestamp")
                location = result.get("location")
                self.log_result("POST /api/employees/{id}/clock-in", True, 
                              f"Successfully clocked in at {location}, time: {timestamp}")
            else:
                self.log_result("POST /api/employees/{id}/clock-in", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/employees/{id}/clock-in", False, f"Error: {str(e)}")
        
        # Wait a moment to simulate work time
        print("   ⏳ Waiting 3 seconds to simulate work time...")
        time.sleep(3)
        
        # Test 3: GET /api/employees/{id}/time-status (check clocked in status)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                hours_so_far = status.get("hours_so_far", 0)
                location = status.get("location")
                self.log_result("GET /api/employees/{id}/time-status (clocked in)", True, 
                              f"Status: {current_status}, Hours so far: {hours_so_far}, Location: {location}")
            else:
                self.log_result("GET /api/employees/{id}/time-status (clocked in)", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-status (clocked in)", False, f"Error: {str(e)}")
        
        # Test 4: POST /api/employees/{id}/clock-out (clock out functionality)
        try:
            response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-out")
            if response.status_code == 200:
                result = response.json()
                hours_worked = result.get("hours_worked")
                total_shift_time = result.get("total_shift_time")
                self.log_result("POST /api/employees/{id}/clock-out", True, 
                              f"Successfully clocked out, Hours worked: {hours_worked}, Shift time: {total_shift_time}")
            else:
                self.log_result("POST /api/employees/{id}/clock-out", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/employees/{id}/clock-out", False, f"Error: {str(e)}")
        
        # Test 5: GET /api/employees/{id}/time-entries/today (daily time entries)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-entries/today")
            if response.status_code == 200:
                result = response.json()
                entries = result.get("entries", [])
                total_hours = result.get("total_hours_today", 0)
                date_str = result.get("date")
                self.log_result("GET /api/employees/{id}/time-entries/today", True, 
                              f"Retrieved {len(entries)} entries for {date_str}, Total hours: {total_hours}")
            else:
                self.log_result("GET /api/employees/{id}/time-entries/today", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-entries/today", False, f"Error: {str(e)}")
        
        return True
    
    def test_end_to_end_workflows(self):
        """Test end-to-end workflows"""
        print("\n🔄 TESTING END-TO-END WORKFLOWS")
        print("=" * 50)
        
        # Workflow 1: Create employee → Clock in → Check status → Clock out → Check time entries
        print("\n📋 Workflow 1: Complete Employee Time Tracking")
        employee_id = self.create_test_employee()
        if employee_id:
            # Clock in
            clock_in_response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-in", 
                                                params={"location": "Reception"})
            if clock_in_response.status_code == 200:
                print("   ✅ Employee clocked in successfully")
                
                # Check status
                time.sleep(1)
                status_response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   ✅ Status check: {status.get('status')} at {status.get('location')}")
                    
                    # Clock out
                    time.sleep(2)
                    clock_out_response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-out")
                    if clock_out_response.status_code == 200:
                        result = clock_out_response.json()
                        print(f"   ✅ Clocked out: {result.get('total_shift_time')}")
                        
                        # Check time entries
                        entries_response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-entries/today")
                        if entries_response.status_code == 200:
                            entries = entries_response.json()
                            print(f"   ✅ Time entries: {len(entries.get('entries', []))} entries today")
                            self.log_result("End-to-End Employee Workflow", True, "Complete workflow successful")
                        else:
                            self.log_result("End-to-End Employee Workflow", False, "Failed at time entries step")
                    else:
                        self.log_result("End-to-End Employee Workflow", False, "Failed at clock out step")
                else:
                    self.log_result("End-to-End Employee Workflow", False, "Failed at status check step")
            else:
                self.log_result("End-to-End Employee Workflow", False, "Failed at clock in step")
        
        # Workflow 2: Create patient → Create SOAP note → Generate receipt → Verify receipt
        print("\n📋 Workflow 2: Complete Receipt Generation")
        patient_id = self.create_test_patient()
        if patient_id:
            # Create SOAP note
            soap_id = self.create_test_soap_note(patient_id)
            if soap_id:
                # Generate receipt
                receipt_response = self.session.post(f"{API_BASE}/receipts/soap-note/{soap_id}")
                if receipt_response.status_code == 200:
                    receipt_data = receipt_response.json()
                    receipt_id = receipt_data.get("receipt", {}).get("id")
                    print(f"   ✅ Receipt generated: {receipt_data.get('receipt', {}).get('receipt_number')}")
                    
                    # Verify receipt
                    if receipt_id:
                        verify_response = self.session.get(f"{API_BASE}/receipts/{receipt_id}")
                        if verify_response.status_code == 200:
                            receipt = verify_response.json()
                            print(f"   ✅ Receipt verified: ${receipt.get('total')} for {receipt.get('patient_name')}")
                            self.log_result("End-to-End Receipt Workflow", True, "Complete workflow successful")
                        else:
                            self.log_result("End-to-End Receipt Workflow", False, "Failed at receipt verification step")
                    else:
                        self.log_result("End-to-End Receipt Workflow", False, "No receipt ID returned")
                else:
                    self.log_result("End-to-End Receipt Workflow", False, "Failed at receipt generation step")
            else:
                self.log_result("End-to-End Receipt Workflow", False, "Failed at SOAP note creation step")
        else:
            self.log_result("End-to-End Receipt Workflow", False, "Failed at patient creation step")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🏥 CLINICHUB BACKEND TESTING - RECEIPT GENERATION & EMPLOYEE CLOCK-IN/OUT")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run specific tests
        self.test_receipt_generation_endpoints()
        self.test_employee_clock_endpoints()
        self.test_end_to_end_workflows()
        
        # Summary
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n🎯 CRITICAL FINDINGS:")
        receipt_tests = [r for r in self.test_results if "receipt" in r["test"].lower()]
        clock_tests = [r for r in self.test_results if "clock" in r["test"].lower() or "time" in r["test"].lower()]
        
        receipt_success = sum(1 for r in receipt_tests if r["success"])
        clock_success = sum(1 for r in clock_tests if r["success"])
        
        print(f"   📄 Receipt Generation: {receipt_success}/{len(receipt_tests)} tests passed")
        print(f"   ⏰ Employee Clock System: {clock_success}/{len(clock_tests)} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The newly added functionality is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Review the issues above.")

def main():
    """Main function"""
    tester = ClinicHubTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()