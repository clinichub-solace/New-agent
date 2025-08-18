#!/usr/bin/env python3
"""
ClinicHub Backend Testing - Vital Signs and SOAP Notes Focus
Testing the fixes for vital signs field names and SOAP notes complete workflow
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import uuid

# Configuration
BACKEND_URL = "https://ecf9c07e-b68e-4d07-9324-af4a7e057b56.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class ClinicHubTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
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
    
    def authenticate(self) -> bool:
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Authentication", True, f"Successfully authenticated as {ADMIN_CREDENTIALS['username']}")
                    return True
                else:
                    self.log_test("Authentication", False, "No access token in response")
                    return False
            else:
                self.log_test("Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_patient(self) -> Dict[str, Any]:
        """Create a test patient for testing"""
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
            
            # Add headers to handle the audit decorator issue
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "ClinicHub-Test-Client/1.0"
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            response = self.session.post(
                f"{BACKEND_URL}/patients",
                json=patient_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                patient = response.json()
                self.log_test("Create Test Patient", True, f"Created patient: {patient['name'][0]['given'][0]} {patient['name'][0]['family']}")
                return patient
            else:
                self.log_test("Create Test Patient", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Patient", False, f"Exception: {str(e)}")
            return None
    
    def create_test_encounter(self, patient_id: str) -> Dict[str, Any]:
        """Create a test encounter for SOAP notes testing"""
        try:
            encounter_data = {
                "patient_id": patient_id,
                "encounter_type": "consultation",
                "scheduled_date": datetime.now().isoformat(),
                "provider": "Dr. Smith",
                "location": "Main Office",
                "chief_complaint": "Routine checkup",
                "reason_for_visit": "Annual wellness visit"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/encounters",
                json=encounter_data,
                timeout=30
            )
            
            if response.status_code == 200:
                encounter = response.json()
                self.log_test("Create Test Encounter", True, f"Created encounter: {encounter['id']}")
                return encounter
            else:
                self.log_test("Create Test Encounter", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Encounter", False, f"Exception: {str(e)}")
            return None
    
    def test_vital_signs_creation(self, patient_id: str, encounter_id: str = None) -> str:
        """Test vital signs creation with corrected field names"""
        try:
            # Test data with the corrected field names as specified in the review
            vital_signs_data = {
                "patient_id": patient_id,
                "encounter_id": encounter_id,
                "height": 165.0,  # cm
                "weight": 70.0,   # kg
                "systolic_bp": 120,  # Corrected field name
                "diastolic_bp": 80,  # Corrected field name
                "heart_rate": 72,
                "respiratory_rate": 16,
                "temperature": 36.5,  # Celsius
                "oxygen_saturation": 98,
                "pain_scale": 2,  # Corrected field name
                "recorded_by": "admin"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/vital-signs",
                json=vital_signs_data,
                timeout=30
            )
            
            if response.status_code == 200:
                vital_signs = response.json()
                # Verify the corrected field names are present
                expected_fields = ["systolic_bp", "diastolic_bp", "pain_scale"]
                missing_fields = [field for field in expected_fields if field not in vital_signs or vital_signs[field] is None]
                
                if not missing_fields:
                    self.log_test("Vital Signs Creation - Field Names", True, 
                                f"Successfully created vital signs with corrected field names: systolic_bp={vital_signs['systolic_bp']}, diastolic_bp={vital_signs['diastolic_bp']}, pain_scale={vital_signs['pain_scale']}")
                    return vital_signs['id']
                else:
                    self.log_test("Vital Signs Creation - Field Names", False, 
                                f"Missing or null corrected fields: {missing_fields}")
                    return None
            else:
                self.log_test("Vital Signs Creation - Field Names", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Vital Signs Creation - Field Names", False, f"Exception: {str(e)}")
            return None
    
    def test_vital_signs_retrieval(self, patient_id: str) -> bool:
        """Test vital signs retrieval by patient ID"""
        try:
            response = self.session.get(
                f"{BACKEND_URL}/vital-signs/patient/{patient_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                vital_signs_list = response.json()
                if vital_signs_list and len(vital_signs_list) > 0:
                    # Verify the data structure includes corrected field names
                    vital_signs = vital_signs_list[0]
                    expected_fields = ["systolic_bp", "diastolic_bp", "pain_scale"]
                    present_fields = [field for field in expected_fields if field in vital_signs and vital_signs[field] is not None]
                    
                    self.log_test("Vital Signs Retrieval", True, 
                                f"Retrieved {len(vital_signs_list)} vital signs records with corrected fields: {present_fields}")
                    return True
                else:
                    self.log_test("Vital Signs Retrieval", False, "No vital signs found for patient")
                    return False
            else:
                self.log_test("Vital Signs Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vital Signs Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_soap_note_creation(self, patient_id: str, encounter_id: str) -> str:
        """Test SOAP note creation"""
        try:
            soap_note_data = {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "subjective": "Patient reports feeling well overall. No acute complaints. Some mild fatigue noted over the past week.",
                "objective": "Vital signs stable. Physical examination reveals no acute distress. Heart rate regular, lungs clear to auscultation bilaterally.",
                "assessment": "Healthy adult presenting for routine wellness visit. Mild fatigue likely related to recent work stress.",
                "plan": "Continue current lifestyle. Recommend stress management techniques. Follow-up in 6 months for routine care.",
                "provider": "Dr. Smith"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/soap-notes",
                json=soap_note_data,
                timeout=30
            )
            
            if response.status_code == 200:
                soap_note = response.json()
                self.log_test("SOAP Note Creation", True, 
                            f"Created SOAP note: {soap_note['id']}, Status: {soap_note['status']}")
                return soap_note['id']
            else:
                self.log_test("SOAP Note Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("SOAP Note Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_soap_note_status_update(self, soap_note_id: str) -> bool:
        """Test updating SOAP note status to completed"""
        try:
            # First get the current SOAP note to preserve other fields
            get_response = self.session.get(
                f"{BACKEND_URL}/soap-notes/{soap_note_id}",
                timeout=30
            )
            
            if get_response.status_code != 200:
                self.log_test("SOAP Note Status Update", False, f"Could not retrieve SOAP note: HTTP {get_response.status_code}")
                return False
            
            current_soap_note = get_response.json()
            
            # Update with all required fields
            update_data = {
                "encounter_id": current_soap_note["encounter_id"],
                "patient_id": current_soap_note["patient_id"],
                "subjective": current_soap_note["subjective"],
                "objective": current_soap_note["objective"],
                "assessment": current_soap_note["assessment"],
                "plan": current_soap_note["plan"],
                "provider": current_soap_note["provider"],
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "completed_by": "admin"
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/soap-notes/{soap_note_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                updated_soap_note = response.json()
                if updated_soap_note['status'] == 'completed':
                    self.log_test("SOAP Note Status Update", True, 
                                f"Successfully updated SOAP note status to: {updated_soap_note['status']}")
                    return True
                else:
                    self.log_test("SOAP Note Status Update", False, 
                                f"Status not updated correctly. Expected: completed, Got: {updated_soap_note['status']}")
                    return False
            else:
                self.log_test("SOAP Note Status Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SOAP Note Status Update", False, f"Exception: {str(e)}")
            return False
    
    def test_soap_note_complete_workflow(self, soap_note_id: str) -> bool:
        """Test the CRITICAL complete workflow endpoint for automated receipt generation"""
        try:
            # Test the complete workflow with billable services and medications
            completion_data = {
                "billable_services": [
                    {
                        "description": "Office Visit - Consultation",
                        "code": "99213",
                        "quantity": 1,
                        "unit_price": 150.00
                    },
                    {
                        "description": "Vital Signs Assessment",
                        "code": "99000",
                        "quantity": 1,
                        "unit_price": 25.00
                    }
                ],
                "prescribed_medications": [
                    {
                        "medication_name": "Ibuprofen",
                        "quantity_dispensed": 30,
                        "sku": "IBU-200MG"
                    }
                ],
                "session_duration": 45
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/soap-notes/{soap_note_id}/complete",
                json=completion_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify the automated workflows
                workflows = result.get("automated_workflows", {})
                
                # Check invoice creation
                invoice_created = workflows.get("invoice_created", {})
                invoice_success = invoice_created.get("status") == "created"
                
                # Check activity logging
                activity_logged = workflows.get("activity_logged", {})
                activity_success = activity_logged.get("status") == "logged"
                
                # Check SOAP note status
                soap_note = result.get("soap_note", {})
                soap_completed = soap_note.get("status") == "completed"
                
                success_details = []
                if invoice_success:
                    success_details.append(f"Invoice created: {invoice_created.get('invoice_number')} (${invoice_created.get('total_amount')})")
                if activity_success:
                    success_details.append(f"Activity logged: {activity_logged.get('activity_id')}")
                if soap_completed:
                    success_details.append("SOAP note marked as completed")
                
                overall_success = invoice_success and activity_success and soap_completed
                
                self.log_test("SOAP Note Complete Workflow - CRITICAL", overall_success,
                            f"Automated workflows: {'; '.join(success_details) if success_details else 'Some workflows failed'}")
                
                # Additional verification - check if receipt/invoice was actually created
                if invoice_success:
                    invoice_id = invoice_created.get("invoice_id")
                    if invoice_id:
                        self.verify_invoice_creation(invoice_id)
                
                return overall_success
            else:
                self.log_test("SOAP Note Complete Workflow - CRITICAL", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SOAP Note Complete Workflow - CRITICAL", False, f"Exception: {str(e)}")
            return False
    
    def verify_invoice_creation(self, invoice_id: str) -> bool:
        """Verify that the invoice was actually created and can be retrieved"""
        try:
            response = self.session.get(
                f"{BACKEND_URL}/invoices/{invoice_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                invoice = response.json()
                self.log_test("Invoice Verification", True, 
                            f"Invoice verified: {invoice['invoice_number']}, Total: ${invoice['total_amount']}")
                return True
            else:
                self.log_test("Invoice Verification", False, 
                            f"Could not retrieve created invoice: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invoice Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_integration_workflow(self) -> bool:
        """Test the complete integration workflow: Patient → Encounter → Vital Signs → SOAP Note → Completion → Receipt"""
        try:
            print("\n🔄 TESTING COMPLETE INTEGRATION WORKFLOW")
            print("=" * 60)
            
            # Step 1: Create test patient
            patient = self.create_test_patient()
            if not patient:
                return False
            
            patient_id = patient['id']
            
            # Step 2: Create test encounter
            encounter = self.create_test_encounter(patient_id)
            if not encounter:
                return False
            
            encounter_id = encounter['id']
            
            # Step 3: Create vital signs with corrected field names
            vital_signs_id = self.test_vital_signs_creation(patient_id, encounter_id)
            if not vital_signs_id:
                return False
            
            # Step 4: Verify vital signs retrieval
            if not self.test_vital_signs_retrieval(patient_id):
                return False
            
            # Step 5: Create SOAP note
            soap_note_id = self.test_soap_note_creation(patient_id, encounter_id)
            if not soap_note_id:
                return False
            
            # Step 6: Test SOAP note status update
            if not self.test_soap_note_status_update(soap_note_id):
                return False
            
            # Step 7: Test the CRITICAL complete workflow with automated receipt generation
            if not self.test_soap_note_complete_workflow(soap_note_id):
                return False
            
            self.log_test("Complete Integration Workflow", True, 
                        "Successfully completed entire workflow: Patient → Encounter → Vital Signs → SOAP Note → Completion → Receipt Generation")
            return True
            
        except Exception as e:
            self.log_test("Complete Integration Workflow", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🏥 ClinicHub Backend Testing - Vital Signs & SOAP Notes Focus")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run the complete integration workflow test
        success = self.test_integration_workflow()
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n✅ PASSED TESTS:")
        for test in passed_tests:
            print(f"  - {test['test']}")
        
        return len(failed_tests) == 0

def main():
    """Main test execution"""
    tester = ClinicHubTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! The vital signs and SOAP notes fixes are working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()