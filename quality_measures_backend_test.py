#!/usr/bin/env python3
"""
Quality Measures Module Backend Testing
Testing the newly implemented Quality Measures functionality as requested in the review
"""

import requests
import json
import sys
from datetime import datetime, date
import time
import os

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://mongodb-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class QualityMeasuresTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_data = {}  # Store created test data for cross-test usage
        
    def log_result(self, test_name, success, message, details=None, status_code=None, payload=None):
        """Log test result with enhanced details"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        if status_code:
            print(f"   Status Code: {status_code}")
        if payload and isinstance(payload, dict):
            print(f"   Sample Payload: {json.dumps(payload, indent=2, default=str)[:200]}...")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "status_code": status_code,
            "payload": payload
        })
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            auth_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}", 
                              status_code=response.status_code)
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.text}", 
                              status_code=response.status_code)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_quality_measures_crud(self):
        """Test Quality Measures CRUD Operations"""
        print("\n🔍 TESTING QUALITY MEASURES CRUD OPERATIONS")
        
        # Test 1: GET /api/quality-measures (fetch all measures)
        try:
            response = self.session.get(f"{API_BASE}/quality-measures")
            if response.status_code == 200:
                measures = response.json()
                self.log_result("GET Quality Measures", True, 
                              f"Successfully retrieved {len(measures)} quality measures", 
                              status_code=response.status_code, payload=measures[:2] if measures else [])
                self.test_data['existing_measures'] = measures
            else:
                self.log_result("GET Quality Measures", False, 
                              f"Failed to retrieve quality measures: {response.text}", 
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET Quality Measures", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/quality-measures (create new measure)
        test_measure = {
            "measure_id": "CMS122",
            "name": "Diabetes HbA1c Poor Control",
            "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
            "measure_type": "outcome",
            "calculation_method": "proportion",
            "target_value": 90.0,
            "target_operator": "gte",
            "population_criteria": {
                "age_range": {"min": 18, "max": 75},
                "conditions": ["diabetes"]
            },
            "numerator_criteria": {
                "lab_values": {"hba1c": {"operator": "lte", "value": 9.0}}
            },
            "denominator_criteria": {
                "diagnosis_codes": ["E11", "E10"]
            },
            "reporting_period": "annual",
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{API_BASE}/quality-measures", json=test_measure)
            if response.status_code == 200:
                result = response.json()
                self.log_result("POST Quality Measure", True, 
                              f"Successfully created quality measure: {result.get('message')}", 
                              status_code=response.status_code, payload=result)
                self.test_data['created_measure_id'] = result.get('id')
            else:
                self.log_result("POST Quality Measure", False, 
                              f"Failed to create quality measure: {response.text}", 
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("POST Quality Measure", False, f"Error: {str(e)}")
        
        # Test 3: GET /api/quality-measures/{id} (get specific measure)
        if self.test_data.get('created_measure_id'):
            try:
                measure_id = self.test_data['created_measure_id']
                response = self.session.get(f"{API_BASE}/quality-measures/{measure_id}")
                if response.status_code == 200:
                    measure = response.json()
                    self.log_result("GET Quality Measure by ID", True, 
                                  f"Successfully retrieved measure: {measure.get('name')}", 
                                  status_code=response.status_code, payload=measure)
                else:
                    self.log_result("GET Quality Measure by ID", False, 
                                  f"Failed to retrieve measure: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET Quality Measure by ID", False, f"Error: {str(e)}")
        
        # Test 4: PUT /api/quality-measures/{id} (update measure)
        if self.test_data.get('created_measure_id'):
            update_data = {
                "description": "Updated: Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
                "target_value": 85.0,
                "is_active": True
            }
            
            try:
                measure_id = self.test_data['created_measure_id']
                response = self.session.put(f"{API_BASE}/quality-measures/{measure_id}", json=update_data)
                if response.status_code == 200:
                    updated_measure = response.json()
                    self.log_result("PUT Quality Measure", True, 
                                  f"Successfully updated measure: {updated_measure.get('name')}", 
                                  status_code=response.status_code, payload=updated_measure)
                else:
                    self.log_result("PUT Quality Measure", False, 
                                  f"Failed to update measure: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("PUT Quality Measure", False, f"Error: {str(e)}")
    
    def test_quality_measures_calculation_reporting(self):
        """Test Quality Measures Calculation & Reporting"""
        print("\n📊 TESTING QUALITY MEASURES CALCULATION & REPORTING")
        
        # First, get a patient ID for testing
        try:
            response = self.session.get(f"{API_BASE}/patients")
            if response.status_code == 200:
                patients = response.json()
                if patients:
                    test_patient_id = patients[0].get('id')
                    self.test_data['test_patient_id'] = test_patient_id
                    self.log_result("Get Test Patient", True, 
                                  f"Found test patient ID: {test_patient_id}", 
                                  status_code=response.status_code)
                else:
                    self.log_result("Get Test Patient", False, "No patients found for testing")
                    return
            else:
                self.log_result("Get Test Patient", False, f"Failed to get patients: {response.text}")
                return
        except Exception as e:
            self.log_result("Get Test Patient", False, f"Error: {str(e)}")
            return
        
        # Test 5: POST /api/quality-measures/calculate (trigger calculations)
        if self.test_data.get('test_patient_id'):
            try:
                patient_id = self.test_data['test_patient_id']
                # Test with specific measure IDs
                measure_ids = []
                if self.test_data.get('created_measure_id'):
                    measure_ids.append(self.test_data['created_measure_id'])
                
                calc_data = {
                    "patient_id": patient_id,
                    "measure_ids": measure_ids if measure_ids else None
                }
                
                response = self.session.post(f"{API_BASE}/quality-measures/calculate", 
                                           params={"patient_id": patient_id})
                if response.status_code == 200:
                    calculations = response.json()
                    self.log_result("POST Quality Measures Calculate", True, 
                                  f"Successfully calculated measures for patient {patient_id}", 
                                  details=f"Calculated {len(calculations.get('calculations', []))} measures",
                                  status_code=response.status_code, payload=calculations)
                else:
                    self.log_result("POST Quality Measures Calculate", False, 
                                  f"Failed to calculate measures: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST Quality Measures Calculate", False, f"Error: {str(e)}")
        
        # Test 6: GET /api/quality-measures/report (fetch calculated results)
        try:
            # Test with various parameters
            params = {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "measure_type": "outcome"
            }
            
            response = self.session.get(f"{API_BASE}/quality-measures/report", params=params)
            if response.status_code == 200:
                report = response.json()
                self.log_result("GET Quality Measures Report", True, 
                              f"Successfully generated quality measures report", 
                              details=f"Report period: {report.get('report_period', {}).get('start_date')} to {report.get('report_period', {}).get('end_date')}",
                              status_code=response.status_code, payload=report)
            else:
                self.log_result("GET Quality Measures Report", False, 
                              f"Failed to generate report: {response.text}", 
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET Quality Measures Report", False, f"Error: {str(e)}")
    
    def test_data_validation(self):
        """Test Data Validation"""
        print("\n✅ TESTING DATA VALIDATION")
        
        # Test 7: Test measure_type values
        valid_measure_types = ["outcome", "process", "structure", "patient_experience"]
        for measure_type in valid_measure_types:
            test_measure = {
                "measure_id": f"TEST_{measure_type.upper()}",
                "name": f"Test {measure_type.title()} Measure",
                "description": f"Test measure for {measure_type} validation",
                "measure_type": measure_type,
                "calculation_method": "proportion",
                "target_value": 80.0,
                "target_operator": "gte",
                "reporting_period": "annual",
                "is_active": True
            }
            
            try:
                response = self.session.post(f"{API_BASE}/quality-measures", json=test_measure)
                if response.status_code == 200:
                    self.log_result(f"Validate measure_type: {measure_type}", True, 
                                  f"Successfully accepted measure_type: {measure_type}", 
                                  status_code=response.status_code)
                else:
                    self.log_result(f"Validate measure_type: {measure_type}", False, 
                                  f"Failed to accept measure_type {measure_type}: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result(f"Validate measure_type: {measure_type}", False, f"Error: {str(e)}")
        
        # Test 8: Test target_operator values
        valid_operators = ["gte", "lte", "eq", "gt", "lt"]
        for operator in valid_operators:
            test_measure = {
                "measure_id": f"TEST_OP_{operator.upper()}",
                "name": f"Test Operator {operator.upper()} Measure",
                "description": f"Test measure for {operator} operator validation",
                "measure_type": "outcome",
                "calculation_method": "proportion",
                "target_value": 75.0,
                "target_operator": operator,
                "reporting_period": "annual",
                "is_active": True
            }
            
            try:
                response = self.session.post(f"{API_BASE}/quality-measures", json=test_measure)
                if response.status_code == 200:
                    self.log_result(f"Validate target_operator: {operator}", True, 
                                  f"Successfully accepted target_operator: {operator}", 
                                  status_code=response.status_code)
                else:
                    self.log_result(f"Validate target_operator: {operator}", False, 
                                  f"Failed to accept target_operator {operator}: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result(f"Validate target_operator: {operator}", False, f"Error: {str(e)}")
        
        # Test 9: Test required fields validation
        required_fields = ["name", "description", "measure_type"]
        for field in required_fields:
            incomplete_measure = {
                "measure_id": "TEST_INCOMPLETE",
                "name": "Test Incomplete Measure",
                "description": "Test measure for required field validation",
                "measure_type": "outcome",
                "calculation_method": "proportion",
                "target_value": 80.0,
                "target_operator": "gte",
                "reporting_period": "annual",
                "is_active": True
            }
            
            # Remove the required field
            del incomplete_measure[field]
            
            try:
                response = self.session.post(f"{API_BASE}/quality-measures", json=incomplete_measure)
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Required field validation: {field}", True, 
                                  f"Correctly rejected measure missing {field}", 
                                  status_code=response.status_code)
                elif response.status_code == 200:
                    self.log_result(f"Required field validation: {field}", False, 
                                  f"Incorrectly accepted measure missing required field {field}", 
                                  status_code=response.status_code)
                else:
                    self.log_result(f"Required field validation: {field}", False, 
                                  f"Unexpected response for missing {field}: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result(f"Required field validation: {field}", False, f"Error: {str(e)}")
    
    def test_integration(self):
        """Test Integration with existing patient/clinical data"""
        print("\n🔗 TESTING INTEGRATION WITH PATIENT/CLINICAL DATA")
        
        # Test 10: Verify measures integrate with patient data
        try:
            response = self.session.get(f"{API_BASE}/patients")
            if response.status_code == 200:
                patients = response.json()
                if patients:
                    patient_count = len(patients)
                    self.log_result("Patient Data Integration", True, 
                                  f"Successfully accessed {patient_count} patients for quality measure integration", 
                                  status_code=response.status_code)
                    
                    # Test patient-specific quality measure evaluation
                    if patient_count > 0:
                        test_patient = patients[0]
                        patient_id = test_patient.get('id')
                        
                        try:
                            response = self.session.post(f"{API_BASE}/patient-quality-measures", 
                                                       params={"patient_id": patient_id})
                            if response.status_code == 200:
                                result = response.json()
                                self.log_result("Patient Quality Measure Evaluation", True, 
                                              f"Successfully evaluated quality measures for patient {patient_id}", 
                                              status_code=response.status_code, payload=result)
                            else:
                                self.log_result("Patient Quality Measure Evaluation", False, 
                                              f"Failed to evaluate patient measures: {response.text}", 
                                              status_code=response.status_code)
                        except Exception as e:
                            self.log_result("Patient Quality Measure Evaluation", False, f"Error: {str(e)}")
                else:
                    self.log_result("Patient Data Integration", False, "No patients found for integration testing")
            else:
                self.log_result("Patient Data Integration", False, 
                              f"Failed to access patient data: {response.text}", 
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("Patient Data Integration", False, f"Error: {str(e)}")
        
        # Test 11: Test measure status calculations
        try:
            # Get quality measures report to check status calculations
            response = self.session.get(f"{API_BASE}/quality-measures/report")
            if response.status_code == 200:
                report = response.json()
                measures = report.get('measures', [])
                if measures:
                    status_types = set()
                    for measure in measures:
                        status = measure.get('status')
                        if status:
                            status_types.add(status)
                    
                    self.log_result("Measure Status Calculations", True, 
                                  f"Successfully calculated measure statuses: {', '.join(status_types)}", 
                                  details=f"Found {len(measures)} measures with calculated statuses",
                                  status_code=response.status_code)
                else:
                    self.log_result("Measure Status Calculations", False, 
                                  "No measures found in report for status calculation testing")
            else:
                self.log_result("Measure Status Calculations", False, 
                              f"Failed to get report for status testing: {response.text}", 
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("Measure Status Calculations", False, f"Error: {str(e)}")
    
    def test_authentication_security(self):
        """Test Authentication & Security"""
        print("\n🔐 TESTING AUTHENTICATION & SECURITY")
        
        # Test 12: Verify admin/admin123 credentials work
        # This was already tested in authenticate() method
        if self.auth_token:
            self.log_result("Admin Credentials Verification", True, 
                          "admin/admin123 credentials are working correctly")
        else:
            self.log_result("Admin Credentials Verification", False, 
                          "admin/admin123 credentials failed")
        
        # Test 13: Test protected endpoints require authentication
        # Create a new session without authentication
        unauth_session = requests.Session()
        
        protected_endpoints = [
            "/quality-measures",
            "/quality-measures/report",
            "/patient-quality-measures"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = unauth_session.get(f"{API_BASE}{endpoint}")
                if response.status_code in [401, 403]:  # Unauthorized or Forbidden
                    self.log_result(f"Protected Endpoint: {endpoint}", True, 
                                  f"Correctly rejected unauthorized access", 
                                  status_code=response.status_code)
                elif response.status_code == 200:
                    self.log_result(f"Protected Endpoint: {endpoint}", False, 
                                  f"Incorrectly allowed unauthorized access", 
                                  status_code=response.status_code)
                else:
                    self.log_result(f"Protected Endpoint: {endpoint}", False, 
                                  f"Unexpected response: {response.text}", 
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result(f"Protected Endpoint: {endpoint}", False, f"Error: {str(e)}")
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("🏥 QUALITY MEASURES MODULE TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {success_rate:.1f}% Success Rate ({passed_tests}/{total_tests} tests passed)")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🎯 PRIORITY TESTING AREAS COVERAGE:")
        print(f"   ✅ Quality Measures CRUD Operations: Tested")
        print(f"   ✅ Quality Measures Calculation & Reporting: Tested")
        print(f"   ✅ Authentication & Security: Tested")
        print(f"   ✅ Data Validation: Tested")
        print(f"   ✅ Integration Testing: Tested")
        
        return success_rate >= 80  # Consider 80%+ success rate as overall success

def main():
    """Main test execution"""
    print("🏥 QUALITY MEASURES MODULE BACKEND TESTING")
    print("="*60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
    print("="*60)
    
    tester = QualityMeasuresTester()
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ CRITICAL: Authentication failed. Cannot proceed with testing.")
        sys.exit(1)
    
    # Run all test suites
    tester.test_quality_measures_crud()
    tester.test_quality_measures_calculation_reporting()
    tester.test_data_validation()
    tester.test_integration()
    tester.test_authentication_security()
    
    # Generate summary
    success = tester.generate_summary()
    
    if success:
        print("\n🎉 QUALITY MEASURES MODULE TESTING COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n⚠️  QUALITY MEASURES MODULE TESTING COMPLETED WITH ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()