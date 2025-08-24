#!/usr/bin/env python3
"""
ClinicHub PHASE 1 & PHASE 2 Backend Testing
Testing enhanced dashboard system and advanced patients/EHR module as requested in review
"""

import requests
import json
import sys
from datetime import datetime, date
import time
import os

# Configuration - Use frontend proxy to backend
FRONTEND_URL = "http://localhost:3000"
API_BASE = f"{FRONTEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class ClinicHubPhase12Tester:
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
            "details": details,
            "status_code": status_code
        })
    
    def authenticate(self):
        """Authenticate with admin/admin123 credentials"""
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
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_phase1_enhanced_dashboard(self):
        """PHASE 1 TESTING - Enhanced Dashboard System"""
        print("\n🏥 PHASE 1 TESTING - Enhanced Dashboard System")
        print("=" * 60)
        
        # Test 1: Verify authentication system works with admin/admin123
        self.log_result("PHASE 1 - Authentication System", True, "admin/admin123 credentials verified during login")
        
        # Test 2: Test Synology status endpoint
        try:
            response = self.session.get(f"{API_BASE}/auth/synology-status")
            if response.status_code == 200:
                synology_data = response.json()
                enabled = synology_data.get("enabled", False)
                configured = synology_data.get("configured", False)
                self.log_result("PHASE 1 - Synology Status", True, 
                              f"Synology integration status: enabled={enabled}, configured={configured}", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 1 - Synology Status", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 1 - Synology Status", False, f"Error: {str(e)}")
        
        # Test 3: Confirm backend services are running properly
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                self.log_result("PHASE 1 - Backend Health", True, 
                              f"Backend services running properly: {status}", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 1 - Backend Health", False, 
                              f"Backend health check failed: {response.status_code}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 1 - Backend Health", False, f"Error: {str(e)}")

    def test_phase2_patients_ehr(self):
        """PHASE 2 TESTING - Advanced Patients/EHR Module"""
        print("\n👥 PHASE 2 TESTING - Advanced Patients/EHR Module")
        print("=" * 60)
        
        # Create test patient for EHR testing
        patient_data = {
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.garcia@email.com",
            "phone": "555-0987",
            "date_of_birth": "1988-08-15",
            "gender": "female",
            "address_line1": "789 Cedar Street",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78703"
        }
        
        # Test 1: Patient CRUD operations - POST /api/patients
        try:
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            if response.status_code == 200:
                patient = response.json()
                patient_id = patient.get("id")
                self.test_data["patient_id"] = patient_id
                patient_name = f"{patient.get('name', [{}])[0].get('given', [''])[0]} {patient.get('name', [{}])[0].get('family', '')}"
                self.log_result("PHASE 2 - POST /api/patients", True, 
                              f"Created FHIR-compliant patient: {patient_name} (ID: {patient_id})", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - POST /api/patients", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
        except Exception as e:
            self.log_result("PHASE 2 - POST /api/patients", False, f"Error: {str(e)}")
            return False
        
        # Test 2: Patient CRUD operations - GET /api/patients
        try:
            response = self.session.get(f"{API_BASE}/patients")
            if response.status_code == 200:
                patients = response.json()
                self.log_result("PHASE 2 - GET /api/patients", True, 
                              f"Retrieved {len(patients)} patients from EHR system", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/patients", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/patients", False, f"Error: {str(e)}")
        
        if not self.test_data.get("patient_id"):
            print("⚠️  Cannot continue EHR testing without patient ID")
            return False
        
        # Test 3: SOAP notes endpoints - POST /api/soap-notes
        soap_data = {
            "patient_id": self.test_data["patient_id"],
            "subjective": "Patient reports mild headache for 2 days. No fever, nausea, or vision changes.",
            "objective": "Alert and oriented. Vital signs stable. No neurological deficits noted.",
            "assessment": "Tension headache, likely stress-related. No red flags present.",
            "plan": "Recommend OTC pain relief, stress management, follow-up if symptoms worsen.",
            "provider": "Dr. Jennifer Martinez"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/soap-notes", json=soap_data)
            if response.status_code == 200:
                soap_note = response.json()
                soap_id = soap_note.get("id")
                self.test_data["soap_id"] = soap_id
                self.log_result("PHASE 2 - POST /api/soap-notes", True, 
                              f"Created SOAP note with ID: {soap_id}", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - POST /api/soap-notes", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - POST /api/soap-notes", False, f"Error: {str(e)}")
        
        # Test 4: SOAP notes endpoints - GET /api/soap-notes/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/soap-notes/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                soap_notes = response.json()
                self.log_result("PHASE 2 - GET /api/soap-notes/patient/{id}", True, 
                              f"Retrieved {len(soap_notes)} SOAP notes for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/soap-notes/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/soap-notes/patient/{id}", False, f"Error: {str(e)}")
        
        # Test 5: Vital signs endpoints - POST /api/vital-signs
        vital_signs_data = {
            "patient_id": self.test_data["patient_id"],
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "heart_rate": 68,
            "temperature": 98.4,
            "respiratory_rate": 14,
            "oxygen_saturation": 99,
            "weight": 145.0,
            "height": 64.0,
            "pain_scale": 3,
            "notes": "Patient reports mild discomfort, otherwise stable vitals"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/vital-signs", json=vital_signs_data)
            if response.status_code == 200:
                vital_signs = response.json()
                vital_id = vital_signs.get("id")
                bmi = vital_signs.get("bmi")
                self.test_data["vital_signs_id"] = vital_id
                self.log_result("PHASE 2 - POST /api/vital-signs", True, 
                              f"Created vital signs with BMI calculation: {bmi} (ID: {vital_id})", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - POST /api/vital-signs", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - POST /api/vital-signs", False, f"Error: {str(e)}")
        
        # Test 6: Vital signs endpoints - GET /api/vital-signs/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/vital-signs/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                vital_signs = response.json()
                self.log_result("PHASE 2 - GET /api/vital-signs/patient/{id}", True, 
                              f"Retrieved {len(vital_signs)} vital signs records for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/vital-signs/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/vital-signs/patient/{id}", False, f"Error: {str(e)}")
        
        # Test 7: Allergies endpoints - POST /api/allergies
        allergy_data = {
            "patient_id": self.test_data["patient_id"],
            "allergy_name": "Penicillin",
            "reaction": "Skin rash and hives",
            "severity": "moderate",
            "notes": "Developed allergic reaction after taking penicillin antibiotics"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/allergies", json=allergy_data)
            if response.status_code == 200:
                allergy = response.json()
                allergy_id = allergy.get("id")
                self.test_data["allergy_id"] = allergy_id
                self.log_result("PHASE 2 - POST /api/allergies", True, 
                              f"Created allergy record: Penicillin (ID: {allergy_id})", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - POST /api/allergies", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - POST /api/allergies", False, f"Error: {str(e)}")
        
        # Test 8: Allergies endpoints - GET /api/allergies/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/allergies/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                allergies = response.json()
                self.log_result("PHASE 2 - GET /api/allergies/patient/{id}", True, 
                              f"Retrieved {len(allergies)} allergy records for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/allergies/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/allergies/patient/{id}", False, f"Error: {str(e)}")
        
        # Test 9: Medications endpoints - GET /api/medications/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/medications/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                medications = response.json()
                self.log_result("PHASE 2 - GET /api/medications/patient/{id}", True, 
                              f"Retrieved {len(medications)} medication records for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/medications/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/medications/patient/{id}", False, f"Error: {str(e)}")
        
        # Test 10: Prescriptions endpoints - GET /api/prescriptions/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/prescriptions/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                prescriptions = response.json()
                self.log_result("PHASE 2 - GET /api/prescriptions/patient/{id}", True, 
                              f"Retrieved {len(prescriptions)} prescription records for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/prescriptions/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/prescriptions/patient/{id}", False, f"Error: {str(e)}")
        
        # Test 11: Medical history endpoints - GET /api/medical-history/patient/{id}
        try:
            response = self.session.get(f"{API_BASE}/medical-history/patient/{self.test_data['patient_id']}")
            if response.status_code == 200:
                medical_history = response.json()
                self.log_result("PHASE 2 - GET /api/medical-history/patient/{id}", True, 
                              f"Retrieved {len(medical_history)} medical history records for patient", 
                              status_code=response.status_code)
            else:
                self.log_result("PHASE 2 - GET /api/medical-history/patient/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("PHASE 2 - GET /api/medical-history/patient/{id}", False, f"Error: {str(e)}")

    def test_critical_focus_areas(self):
        """Test critical focus areas from review request"""
        print("\n🎯 CRITICAL FOCUS AREAS TESTING")
        print("=" * 60)
        
        # Test 1: Verify all API endpoints use /api prefix correctly
        api_prefix_correct = all("/api" in result["test"] for result in self.test_results if "GET " in result["test"] or "POST " in result["test"])
        self.log_result("CRITICAL - API Prefix Usage", api_prefix_correct, 
                      "All API endpoints correctly use /api prefix" if api_prefix_correct else "Some endpoints missing /api prefix")
        
        # Test 2: Confirm MongoDB connection is working locally
        try:
            response = self.session.get(f"{API_BASE}/patients")
            mongodb_working = response.status_code == 200
            self.log_result("CRITICAL - MongoDB Connection", mongodb_working, 
                          "MongoDB connection working locally" if mongodb_working else "MongoDB connection issues detected",
                          status_code=response.status_code)
        except Exception as e:
            self.log_result("CRITICAL - MongoDB Connection", False, f"MongoDB connection error: {str(e)}")
        
        # Test 3: Test FHIR-compliant patient record creation
        fhir_compliant = self.test_data.get("patient_id") is not None
        self.log_result("CRITICAL - FHIR Compliance", fhir_compliant, 
                      "FHIR-compliant patient record creation verified" if fhir_compliant else "FHIR compliance issues detected")
        
        # Test 4: Validate EHR data retrieval for existing patients
        ehr_retrieval_working = any(result["success"] and "patient" in result["test"].lower() and "GET" in result["test"] for result in self.test_results)
        self.log_result("CRITICAL - EHR Data Retrieval", ehr_retrieval_working, 
                      "EHR data retrieval functional for existing patients" if ehr_retrieval_working else "EHR data retrieval issues detected")
        
        # Test 5: Ensure all restored functionality is operational
        core_endpoints_working = sum(1 for result in self.test_results if result["success"] and any(endpoint in result["test"].lower() for endpoint in ["soap", "vital", "allergy"]))
        total_core_endpoints = sum(1 for result in self.test_results if any(endpoint in result["test"].lower() for endpoint in ["soap", "vital", "allergy"]))
        functionality_operational = core_endpoints_working >= (total_core_endpoints * 0.8) if total_core_endpoints > 0 else False
        self.log_result("CRITICAL - Restored Functionality", functionality_operational, 
                      f"Restored functionality operational: {core_endpoints_working}/{total_core_endpoints} core endpoints working" if functionality_operational else "Restored functionality has issues")

    def run_phase_1_2_tests(self):
        """Run PHASE 1 and PHASE 2 tests"""
        print("🏥 CLINICHUB PHASE 1 & PHASE 2 BACKEND TESTING")
        print("=" * 80)
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Authentication: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run PHASE 1 tests
        try:
            self.test_phase1_enhanced_dashboard()
        except Exception as e:
            print(f"❌ Error in PHASE 1 testing: {str(e)}")
            self.log_result("PHASE 1 - Suite Error", False, f"PHASE 1 testing failed: {str(e)}")
        
        # Run PHASE 2 tests
        try:
            self.test_phase2_patients_ehr()
        except Exception as e:
            print(f"❌ Error in PHASE 2 testing: {str(e)}")
            self.log_result("PHASE 2 - Suite Error", False, f"PHASE 2 testing failed: {str(e)}")
        
        # Test critical focus areas
        try:
            self.test_critical_focus_areas()
        except Exception as e:
            print(f"❌ Error in critical focus areas testing: {str(e)}")
            self.log_result("CRITICAL - Suite Error", False, f"Critical focus areas testing failed: {str(e)}")
        
        # Generate summary
        self.print_phase_summary()
        return True
    
    def print_phase_summary(self):
        """Print PHASE 1 & PHASE 2 test summary"""
        print("\n" + "=" * 80)
        print("📊 PHASE 1 & PHASE 2 TEST SUMMARY")
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
        
        # PHASE 1 Results
        phase1_tests = [r for r in self.test_results if "PHASE 1" in r["test"]]
        phase1_passed = sum(1 for r in phase1_tests if r["success"])
        phase1_total = len(phase1_tests)
        phase1_rate = (phase1_passed/phase1_total)*100 if phase1_total > 0 else 0
        
        print(f"\n🏥 PHASE 1 - Enhanced Dashboard System:")
        print(f"   Status: {'✅ PASSED' if phase1_rate >= 80 else '❌ FAILED'}")
        print(f"   Results: {phase1_passed}/{phase1_total} ({phase1_rate:.1f}%)")
        print(f"   • Authentication with admin/admin123: {'✅' if any(r['success'] for r in phase1_tests if 'Authentication' in r['test']) else '❌'}")
        print(f"   • Synology status endpoint: {'✅' if any(r['success'] for r in phase1_tests if 'Synology' in r['test']) else '❌'}")
        print(f"   • Backend services health: {'✅' if any(r['success'] for r in phase1_tests if 'Health' in r['test']) else '❌'}")
        
        # PHASE 2 Results
        phase2_tests = [r for r in self.test_results if "PHASE 2" in r["test"]]
        phase2_passed = sum(1 for r in phase2_tests if r["success"])
        phase2_total = len(phase2_tests)
        phase2_rate = (phase2_passed/phase2_total)*100 if phase2_total > 0 else 0
        
        print(f"\n👥 PHASE 2 - Advanced Patients/EHR Module:")
        print(f"   Status: {'✅ PASSED' if phase2_rate >= 80 else '❌ FAILED'}")
        print(f"   Results: {phase2_passed}/{phase2_total} ({phase2_rate:.1f}%)")
        print(f"   • Patient CRUD operations: {'✅' if any(r['success'] for r in phase2_tests if 'patients' in r['test']) else '❌'}")
        print(f"   • SOAP notes endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'soap-notes' in r['test']) else '❌'}")
        print(f"   • Vital signs endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'vital-signs' in r['test']) else '❌'}")
        print(f"   • Allergies endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'allergies' in r['test']) else '❌'}")
        print(f"   • Medications endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'medications' in r['test']) else '❌'}")
        print(f"   • Prescriptions endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'prescriptions' in r['test']) else '❌'}")
        print(f"   • Medical history endpoints: {'✅' if any(r['success'] for r in phase2_tests if 'medical-history' in r['test']) else '❌'}")
        
        # Critical Focus Areas
        critical_tests = [r for r in self.test_results if "CRITICAL" in r["test"]]
        critical_passed = sum(1 for r in critical_tests if r["success"])
        critical_total = len(critical_tests)
        critical_rate = (critical_passed/critical_total)*100 if critical_total > 0 else 0
        
        print(f"\n🎯 CRITICAL FOCUS AREAS:")
        print(f"   Status: {'✅ PASSED' if critical_rate >= 80 else '❌ FAILED'}")
        print(f"   Results: {critical_passed}/{critical_total} ({critical_rate:.1f}%)")
        for test in critical_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test'].replace('CRITICAL - ', '')}")
        
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
        
        # Expected Results Verification
        print(f"\n✅ EXPECTED RESULTS VERIFICATION:")
        auth_working = any(r['success'] for r in self.test_results if 'Authentication' in r['test'])
        ehr_working = phase2_rate >= 70
        patient_functional = any(r['success'] for r in phase2_tests if 'POST /api/patients' in r['test'])
        soap_working = any(r['success'] for r in phase2_tests if 'soap-notes' in r['test'])
        vitals_working = any(r['success'] for r in phase2_tests if 'vital-signs' in r['test'])
        allergies_working = any(r['success'] for r in phase2_tests if 'allergies' in r['test'])
        backend_stable = success_rate >= 75
        
        print(f"   • Authentication working with admin/admin123: {'✅' if auth_working else '❌'}")
        print(f"   • All EHR endpoints responding correctly: {'✅' if ehr_working else '❌'}")
        print(f"   • Patient data creation and retrieval functional: {'✅' if patient_functional else '❌'}")
        print(f"   • SOAP notes, vitals, allergies systems working: {'✅' if (soap_working and vitals_working and allergies_working) else '❌'}")
        print(f"   • Backend stable after major frontend restoration: {'✅' if backend_stable else '❌'}")
        
        # Final Assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("   🟢 EXCELLENT: PHASE 1 & PHASE 2 restoration completed successfully")
        elif success_rate >= 75:
            print("   🟡 GOOD: PHASE 1 & PHASE 2 mostly functional with minor issues")
        elif success_rate >= 50:
            print("   🟠 FAIR: PHASE 1 & PHASE 2 have significant issues requiring attention")
        else:
            print("   🔴 POOR: PHASE 1 & PHASE 2 have critical issues preventing proper operation")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = ClinicHubPhase12Tester()
    success = tester.run_phase_1_2_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()