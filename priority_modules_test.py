#!/usr/bin/env python3
"""
ClinicHub Priority Modules Testing
Focus on the 5 high-impact modules mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime, date
import time

# Configuration - Use production URL
BACKEND_URL = "https://mongodb-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class PriorityModulesTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_data = {}
        
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
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}", 
                              status_code=response.status_code)
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}",
                              status_code=response.status_code)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_insurance_verification_detailed(self):
        """Test Insurance Verification System in detail"""
        print("\n🏥 DETAILED INSURANCE VERIFICATION TESTING")
        print("=" * 60)
        
        # Test 1: GET /api/insurance-plans
        try:
            response = self.session.get(f"{API_BASE}/insurance-plans")
            if response.status_code == 200:
                plans = response.json()
                self.log_result("GET /api/insurance-plans", True, 
                              f"Retrieved {len(plans)} insurance plans", 
                              status_code=response.status_code)
                if plans:
                    self.test_data["insurance_plan_id"] = plans[0].get("id")
                    print(f"   Sample Plan: {plans[0].get('name', 'Unknown')} - {plans[0].get('type', 'Unknown')}")
            else:
                self.log_result("GET /api/insurance-plans", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/insurance-plans", False, f"Error: {str(e)}")
        
        # Test 2: Create test patient for insurance testing
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
        
        try:
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            if response.status_code == 200:
                patient = response.json()
                self.test_data["patient_id"] = patient.get("id")
                self.log_result("Create Test Patient for Insurance", True, 
                              f"Created patient Sarah Johnson", 
                              status_code=response.status_code)
            else:
                self.log_result("Create Test Patient for Insurance", False, 
                              f"Failed: {response.status_code}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("Create Test Patient for Insurance", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/insurance-policies
        if self.test_data.get("patient_id") and self.test_data.get("insurance_plan_id"):
            policy_data = {
                "patient_id": self.test_data["patient_id"],
                "plan_id": self.test_data["insurance_plan_id"],
                "policy_number": "POL987654321",
                "group_number": "GRP002",
                "subscriber_id": "SUB456",
                "effective_date": "2025-01-01",
                "expiration_date": "2025-12-31",
                "copay": 30.00,
                "deductible": 1500.00,
                "is_primary": True
            }
            
            try:
                response = self.session.post(f"{API_BASE}/insurance-policies", json=policy_data)
                if response.status_code == 200:
                    policy = response.json()
                    self.test_data["insurance_policy_id"] = policy.get("id")
                    self.log_result("POST /api/insurance-policies", True, 
                                  f"Created insurance policy successfully", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/insurance-policies", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/insurance-policies", False, f"Error: {str(e)}")
        
        # Test 4: POST /api/insurance-verification
        if self.test_data.get("patient_id"):
            verification_data = {
                "patient_id": self.test_data["patient_id"],
                "service_date": "2025-01-25",
                "service_codes": ["99213", "90834"],
                "provider_npi": "1234567890",
                "verification_type": "eligibility"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/insurance-verification", json=verification_data)
                if response.status_code == 200:
                    verification = response.json()
                    self.log_result("POST /api/insurance-verification", True, 
                                  f"Created insurance verification successfully", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/insurance-verification", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/insurance-verification", False, f"Error: {str(e)}")
        
        # Test 5: GET /api/insurance-verifications
        try:
            response = self.session.get(f"{API_BASE}/insurance-verifications")
            if response.status_code == 200:
                verifications = response.json()
                self.log_result("GET /api/insurance-verifications", True, 
                              f"Retrieved {len(verifications)} insurance verifications", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/insurance-verifications", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/insurance-verifications", False, f"Error: {str(e)}")

    def test_telehealth_detailed(self):
        """Test Telehealth Module in detail"""
        print("\n📹 DETAILED TELEHEALTH MODULE TESTING")
        print("=" * 60)
        
        # Test 1: GET /api/telehealth/sessions
        try:
            response = self.session.get(f"{API_BASE}/telehealth/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.log_result("GET /api/telehealth/sessions", True, 
                              f"Retrieved {len(sessions)} telehealth sessions", 
                              status_code=response.status_code)
                if sessions:
                    print(f"   Sample Session: {sessions[0].get('title', 'Unknown')} - Status: {sessions[0].get('status', 'Unknown')}")
            else:
                self.log_result("GET /api/telehealth/sessions", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/telehealth/sessions", False, f"Error: {str(e)}")
        
        # Test 2: Create provider for telehealth testing
        provider_data = {
            "first_name": "Michael",
            "last_name": "Thompson",
            "title": "Dr.",
            "specialties": ["Telemedicine", "Family Medicine"],
            "email": "dr.thompson@clinichub.com",
            "phone": "555-0987",
            "license_number": "TX67890",
            "npi_number": "0987654321"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/providers", json=provider_data)
            if response.status_code == 200:
                provider = response.json()
                self.test_data["provider_id"] = provider.get("id")
                self.log_result("Create Test Provider for Telehealth", True, 
                              f"Created provider Dr. Thompson", 
                              status_code=response.status_code)
            else:
                self.log_result("Create Test Provider for Telehealth", False, 
                              f"Failed: {response.status_code}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("Create Test Provider for Telehealth", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/telehealth/sessions
        if self.test_data.get("patient_id") and self.test_data.get("provider_id"):
            session_data = {
                "patient_id": self.test_data["patient_id"],
                "provider_id": self.test_data["provider_id"],
                "session_type": "video_consultation",
                "title": "Telehealth Follow-up Session",
                "description": "Virtual consultation for ongoing care",
                "scheduled_start": "2025-01-25T15:00:00Z",
                "duration_minutes": 45,
                "recording_enabled": False
            }
            
            try:
                response = self.session.post(f"{API_BASE}/telehealth/sessions", json=session_data)
                if response.status_code == 200:
                    session = response.json()
                    self.test_data["telehealth_session_id"] = session.get("id")
                    session_number = session.get("session_number")
                    self.log_result("POST /api/telehealth/sessions", True, 
                                  f"Created telehealth session {session_number}", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/telehealth/sessions", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/telehealth/sessions", False, f"Error: {str(e)}")
        
        # Test 4: POST /api/telehealth/sessions/{id}/join
        if self.test_data.get("telehealth_session_id"):
            join_data = {
                "user_id": "admin",
                "user_name": "Administrator",
                "user_type": "provider"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/telehealth/sessions/{self.test_data['telehealth_session_id']}/join", 
                                           json=join_data)
                if response.status_code == 200:
                    self.log_result("POST /api/telehealth/sessions/{id}/join", True, 
                                  f"Successfully joined telehealth session", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/telehealth/sessions/{id}/join", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/telehealth/sessions/{id}/join", False, f"Error: {str(e)}")
        
        # Test 5: PUT /api/telehealth/sessions/{id}/end
        if self.test_data.get("telehealth_session_id"):
            end_data = {
                "session_notes": "Successful telehealth session completed",
                "provider_notes": "Patient responded well to virtual consultation",
                "patient_rating": 5,
                "provider_rating": 4
            }
            
            try:
                response = self.session.put(f"{API_BASE}/telehealth/sessions/{self.test_data['telehealth_session_id']}/end", 
                                          json=end_data)
                if response.status_code == 200:
                    self.log_result("PUT /api/telehealth/sessions/{id}/end", True, 
                                  f"Successfully ended telehealth session", 
                                  status_code=response.status_code)
                else:
                    self.log_result("PUT /api/telehealth/sessions/{id}/end", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("PUT /api/telehealth/sessions/{id}/end", False, f"Error: {str(e)}")
        
        # Test 6: GET /api/telehealth/waiting-room
        try:
            response = self.session.get(f"{API_BASE}/telehealth/waiting-room")
            if response.status_code == 200:
                waiting_patients = response.json()
                self.log_result("GET /api/telehealth/waiting-room", True, 
                              f"Retrieved {len(waiting_patients)} patients in waiting room", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/telehealth/waiting-room", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/telehealth/waiting-room", False, f"Error: {str(e)}")

    def test_document_management_detailed(self):
        """Test Document Management System in detail"""
        print("\n📄 DETAILED DOCUMENT MANAGEMENT TESTING")
        print("=" * 60)
        
        # Test 1: GET /api/documents
        try:
            response = self.session.get(f"{API_BASE}/documents")
            if response.status_code == 200:
                documents = response.json()
                self.log_result("GET /api/documents", True, 
                              f"Retrieved {len(documents)} documents", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/documents", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/documents", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/documents
        if self.test_data.get("patient_id"):
            document_data = {
                "title": "Patient Medical History Report",
                "category": "medical_records",
                "patient_id": self.test_data["patient_id"],
                "content": "Comprehensive medical history for Sarah Johnson including past procedures and medications",
                "document_type": "medical_history",
                "status": "pending",
                "created_by": "admin",
                "tags": ["medical_history", "comprehensive", "patient_record"],
                "metadata": {
                    "report_date": "2025-01-24",
                    "reviewing_provider": "Dr. Michael Thompson"
                }
            }
            
            try:
                response = self.session.post(f"{API_BASE}/documents", json=document_data)
                if response.status_code == 200:
                    document = response.json()
                    self.test_data["document_id"] = document.get("id")
                    self.log_result("POST /api/documents", True, 
                                  f"Created document successfully", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/documents", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/documents", False, f"Error: {str(e)}")
        
        # Test 3: PUT /api/documents/{id}
        if self.test_data.get("document_id"):
            update_data = {
                "title": "Patient Medical History Report - Updated",
                "content": "Comprehensive medical history for Sarah Johnson - Updated with recent lab results",
                "tags": ["medical_history", "comprehensive", "patient_record", "updated"],
                "metadata": {
                    "report_date": "2025-01-24",
                    "reviewing_provider": "Dr. Michael Thompson",
                    "last_updated": "2025-01-24",
                    "update_reason": "Added recent lab results"
                }
            }
            
            try:
                response = self.session.put(f"{API_BASE}/documents/{self.test_data['document_id']}", 
                                          json=update_data)
                if response.status_code == 200:
                    self.log_result("PUT /api/documents/{id}", True, 
                                  f"Successfully updated document", 
                                  status_code=response.status_code)
                else:
                    self.log_result("PUT /api/documents/{id}", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("PUT /api/documents/{id}", False, f"Error: {str(e)}")
        
        # Test 4: PUT /api/documents/{id}/status
        if self.test_data.get("document_id"):
            status_data = {
                "status": "approved",
                "status_notes": "Medical history report reviewed and approved",
                "approved_by": "admin"
            }
            
            try:
                response = self.session.put(f"{API_BASE}/documents/{self.test_data['document_id']}/status", 
                                          json=status_data)
                if response.status_code == 200:
                    self.log_result("PUT /api/documents/{id}/status", True, 
                                  f"Successfully updated document status", 
                                  status_code=response.status_code)
                else:
                    self.log_result("PUT /api/documents/{id}/status", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("PUT /api/documents/{id}/status", False, f"Error: {str(e)}")

    def test_patient_portal_detailed(self):
        """Test Patient Portal Integration in detail"""
        print("\n🌐 DETAILED PATIENT PORTAL TESTING")
        print("=" * 60)
        
        # Test 1: POST /api/patient-portal/access
        if self.test_data.get("patient_id"):
            portal_access_data = {
                "patient_id": self.test_data["patient_id"],
                "username": "sarah.johnson",
                "email": "sarah.johnson@email.com",
                "temporary_password": "SecurePass456!",
                "access_level": "full",
                "expires_at": "2025-12-31T23:59:59Z",
                "features_enabled": [
                    "view_records",
                    "schedule_appointments", 
                    "message_provider",
                    "view_lab_results",
                    "pay_bills",
                    "telehealth_access"
                ]
            }
            
            try:
                response = self.session.post(f"{API_BASE}/patient-portal/access", json=portal_access_data)
                if response.status_code == 200:
                    portal_access = response.json()
                    self.log_result("POST /api/patient-portal/access", True, 
                                  f"Created patient portal access successfully", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/patient-portal/access", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/patient-portal/access", False, f"Error: {str(e)}")
        
        # Test 2: GET /api/patient-portal/{patient_id}/messages
        if self.test_data.get("patient_id"):
            try:
                response = self.session.get(f"{API_BASE}/patient-portal/{self.test_data['patient_id']}/messages")
                if response.status_code == 200:
                    messages = response.json()
                    self.log_result("GET /api/patient-portal/{patient_id}/messages", True, 
                                  f"Retrieved {len(messages)} patient messages", 
                                  status_code=response.status_code)
                else:
                    self.log_result("GET /api/patient-portal/{patient_id}/messages", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET /api/patient-portal/{patient_id}/messages", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/patient-portal/{patient_id}/messages
        if self.test_data.get("patient_id"):
            message_data = {
                "sender_id": "admin",
                "sender_name": "Dr. Michael Thompson",
                "sender_type": "provider",
                "subject": "Telehealth Session Scheduled",
                "message": "Your telehealth session has been scheduled for January 25th at 3:00 PM. Please ensure you have a stable internet connection and access to a device with camera and microphone.",
                "message_type": "appointment_notification",
                "priority": "normal",
                "requires_response": False
            }
            
            try:
                response = self.session.post(f"{API_BASE}/patient-portal/{self.test_data['patient_id']}/messages", 
                                           json=message_data)
                if response.status_code == 200:
                    message = response.json()
                    self.log_result("POST /api/patient-portal/{patient_id}/messages", True, 
                                  f"Sent message to patient successfully", 
                                  status_code=response.status_code)
                else:
                    self.log_result("POST /api/patient-portal/{patient_id}/messages", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/patient-portal/{patient_id}/messages", False, f"Error: {str(e)}")

    def run_priority_tests(self):
        """Run priority module tests"""
        print("🏥 CLINICHUB PRIORITY MODULES TESTING")
        print("=" * 80)
        print("🎯 FOCUS: High-Impact Modules from Review Request")
        print("   1. Insurance Verification System")
        print("   2. Telehealth Module")
        print("   3. Document Management System") 
        print("   4. Patient Portal Integration")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run priority tests
        test_suites = [
            ("Insurance Verification System", self.test_insurance_verification_detailed),
            ("Telehealth Module", self.test_telehealth_detailed),
            ("Document Management System", self.test_document_management_detailed),
            ("Patient Portal Integration", self.test_patient_portal_detailed)
        ]
        
        for suite_name, test_method in test_suites:
            try:
                print(f"\n🔄 Running {suite_name}...")
                test_method()
            except Exception as e:
                print(f"❌ Error in {suite_name}: {str(e)}")
                self.log_result(f"{suite_name} - Suite Error", False, f"Test suite failed: {str(e)}")
        
        # Generate summary
        self.print_priority_summary()
        return True
    
    def print_priority_summary(self):
        """Print priority modules test summary"""
        print("\n" + "=" * 80)
        print("📊 PRIORITY MODULES TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests/total_tests)*100 if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Tests Executed: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        # Module-specific results
        modules = {
            "Insurance Verification": ["insurance"],
            "Telehealth": ["telehealth"],
            "Document Management": ["document"],
            "Patient Portal": ["patient-portal"]
        }
        
        print(f"\n📋 RESULTS BY PRIORITY MODULE:")
        for module, keywords in modules.items():
            module_tests = [r for r in self.test_results if any(keyword in r["test"].lower() for keyword in keywords)]
            if module_tests:
                module_passed = sum(1 for r in module_tests if r["success"])
                module_total = len(module_tests)
                module_rate = (module_passed/module_total)*100 if module_total > 0 else 0
                status_icon = "✅" if module_rate >= 80 else "⚠️" if module_rate >= 50 else "❌"
                print(f"   {status_icon} {module}: {module_passed}/{module_total} ({module_rate:.1f}%)")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}")
                    print(f"     Error: {result['message']}")
                    if result.get("status_code"):
                        print(f"     Status Code: {result['status_code']}")
                    print()
        
        # Executive summary
        print(f"\n🎯 PRIORITY MODULES ASSESSMENT:")
        if success_rate >= 90:
            print("   🟢 EXCELLENT: All priority modules are production-ready")
        elif success_rate >= 75:
            print("   🟡 GOOD: Most priority modules are functional with minor issues")
        elif success_rate >= 50:
            print("   🟠 FAIR: Priority modules have significant issues requiring attention")
        else:
            print("   🔴 POOR: Priority modules have critical issues preventing production use")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = PriorityModulesTester()
    success = tester.run_priority_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()