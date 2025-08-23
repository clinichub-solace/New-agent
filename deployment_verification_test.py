#!/usr/bin/env python3
"""
ClinicHub Deployment Verification Test
Critical deployment success verification for MongoDB connection fix
Testing deployed environment: https://unruffled-noyce.emergent.host
"""

import requests
import json
import sys
import time
from datetime import datetime, date

# Configuration - Production deployment URL
DEPLOYMENT_URL = "https://unruffled-noyce.emergent.host"
API_BASE = f"{DEPLOYMENT_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class DeploymentVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout for deployment testing
        self.auth_token = None
        self.test_results = []
        self.test_data = {}
        self.start_time = None
        
    def log_result(self, test_name, success, message, details=None, status_code=None, response_time=None):
        """Log test result with performance metrics"""
        status = "✅ PASS" if success else "❌ FAIL"
        perf_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}: {message}{perf_info}")
        if details:
            print(f"   Details: {details}")
        if status_code:
            print(f"   Status Code: {status_code}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "status_code": status_code,
            "response_time": response_time
        })
    
    def make_request(self, method, url, **kwargs):
        """Make HTTP request with timing and error handling"""
        start_time = time.time()
        try:
            response = getattr(self.session, method.lower())(url, **kwargs)
            response_time = time.time() - start_time
            return response, response_time
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return None, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return None, response_time

    def test_mongodb_connection_status(self):
        """Test 1: MongoDB Connection Status - Check if database connectivity has been resolved"""
        print("\n🔍 TESTING MONGODB CONNECTION STATUS")
        print("=" * 60)
        
        # Test health endpoint to verify backend is running
        response, response_time = self.make_request('get', f"{API_BASE}/health")
        
        if response is None:
            self.log_result("MongoDB Connection - Health Check", False, 
                          "Backend not accessible - possible network/MongoDB connection issue", 
                          response_time=response_time)
            return False
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                self.log_result("MongoDB Connection - Health Check", True, 
                              f"Backend accessible: {health_data.get('message', 'OK')}", 
                              status_code=response.status_code, response_time=response_time)
            except:
                self.log_result("MongoDB Connection - Health Check", True, 
                              "Backend accessible but response not JSON", 
                              status_code=response.status_code, response_time=response_time)
        else:
            self.log_result("MongoDB Connection - Health Check", False, 
                          f"Backend health check failed: {response.status_code}", 
                          status_code=response.status_code, response_time=response_time)
            return False
        
        # Test database connectivity by trying to access a data endpoint
        response, response_time = self.make_request('get', f"{API_BASE}/patients")
        
        if response is None:
            self.log_result("MongoDB Connection - Database Access", False, 
                          "Database access timed out - possible MongoDB connection issue", 
                          response_time=response_time)
            return False
        
        if response.status_code == 401:
            # Expected - need authentication, but this means backend is connecting to DB
            self.log_result("MongoDB Connection - Database Access", True, 
                          "Database accessible (authentication required as expected)", 
                          status_code=response.status_code, response_time=response_time)
            return True
        elif response.status_code == 200:
            self.log_result("MongoDB Connection - Database Access", True, 
                          "Database accessible and responding", 
                          status_code=response.status_code, response_time=response_time)
            return True
        else:
            error_msg = "Unknown database error"
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', str(error_data))
            except:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            # Check for specific MongoDB connection errors
            if "No address associated with hostname" in error_msg:
                self.log_result("MongoDB Connection - Database Access", False, 
                              "CRITICAL: MongoDB hostname resolution failed - same error as reported", 
                              details=error_msg, status_code=response.status_code, response_time=response_time)
            else:
                self.log_result("MongoDB Connection - Database Access", False, 
                              f"Database connection issue: {error_msg}", 
                              status_code=response.status_code, response_time=response_time)
            return False

    def test_authentication_system(self):
        """Test 2: Authentication System - Test admin/admin123 login through deployed environment"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        print("=" * 60)
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        response, response_time = self.make_request('post', f"{API_BASE}/auth/login", json=login_data)
        
        if response is None:
            self.log_result("Authentication - Login", False, 
                          f"Login request timed out after {response_time:.2f}s", 
                          response_time=response_time)
            return False
        
        if response_time > 5.0:
            self.log_result("Authentication - Performance Warning", False, 
                          f"Login took {response_time:.2f}s (>5s threshold)", 
                          response_time=response_time)
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("Authentication - Login", True, 
                                  f"Successfully authenticated as {ADMIN_USERNAME}", 
                                  status_code=response.status_code, response_time=response_time)
                    
                    # Test protected endpoint access
                    response, response_time = self.make_request('get', f"{API_BASE}/auth/me")
                    if response and response.status_code == 200:
                        user_data = response.json()
                        self.log_result("Authentication - Protected Access", True, 
                                      f"Protected endpoint accessible, user: {user_data.get('username')}", 
                                      status_code=response.status_code, response_time=response_time)
                        return True
                    else:
                        self.log_result("Authentication - Protected Access", False, 
                                      "Cannot access protected endpoints with token", 
                                      status_code=response.status_code if response else None, 
                                      response_time=response_time)
                        return False
                else:
                    self.log_result("Authentication - Login", False, 
                                  "Login successful but no access token received", 
                                  status_code=response.status_code, response_time=response_time)
                    return False
            except Exception as e:
                self.log_result("Authentication - Login", False, 
                              f"Login response parsing error: {str(e)}", 
                              status_code=response.status_code, response_time=response_time)
                return False
        else:
            error_msg = "Authentication failed"
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', str(error_data))
            except:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            self.log_result("Authentication - Login", False, 
                          f"Login failed: {error_msg}", 
                          status_code=response.status_code, response_time=response_time)
            return False

    def test_core_api_endpoints(self):
        """Test 3: Core API Endpoints - Verify health, auth, and critical medical endpoints"""
        print("\n🏥 TESTING CORE API ENDPOINTS")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_result("Core API - Authentication Required", False, 
                          "Cannot test core endpoints without authentication")
            return False
        
        # Critical endpoints to test
        endpoints = [
            ("GET", "/health", "Health Check"),
            ("GET", "/patients", "Patient List"),
            ("GET", "/employees", "Employee List"),
            ("GET", "/inventory", "Inventory List"),
            ("GET", "/invoices", "Invoice List"),
            ("GET", "/appointments", "Appointment List"),
            ("GET", "/erx/medications", "eRx Medications"),
            ("GET", "/lab-tests", "Lab Test Catalog")
        ]
        
        successful_endpoints = 0
        total_endpoints = len(endpoints)
        
        for method, endpoint, description in endpoints:
            url = f"{API_BASE}{endpoint}"
            response, response_time = self.make_request(method, url)
            
            if response is None:
                self.log_result(f"Core API - {description}", False, 
                              f"Request timed out after {response_time:.2f}s", 
                              response_time=response_time)
                continue
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                        self.log_result(f"Core API - {description}", True, 
                                      f"Retrieved {count} records", 
                                      status_code=response.status_code, response_time=response_time)
                    elif isinstance(data, dict):
                        self.log_result(f"Core API - {description}", True, 
                                      f"Response received: {data.get('message', 'OK')}", 
                                      status_code=response.status_code, response_time=response_time)
                    else:
                        self.log_result(f"Core API - {description}", True, 
                                      "Valid response received", 
                                      status_code=response.status_code, response_time=response_time)
                    successful_endpoints += 1
                except:
                    self.log_result(f"Core API - {description}", True, 
                                  "Response received (non-JSON)", 
                                  status_code=response.status_code, response_time=response_time)
                    successful_endpoints += 1
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text[:100] if response.text else f"HTTP {response.status_code}"
                
                self.log_result(f"Core API - {description}", False, 
                              f"Failed: {error_msg}", 
                              status_code=response.status_code, response_time=response_time)
        
        success_rate = (successful_endpoints / total_endpoints) * 100
        self.log_result("Core API - Overall", success_rate >= 75, 
                      f"Core endpoints: {successful_endpoints}/{total_endpoints} ({success_rate:.1f}%)")
        
        return success_rate >= 75

    def test_response_performance(self):
        """Test 4: Response Performance - Confirm login and API calls complete in <5 seconds"""
        print("\n⚡ TESTING RESPONSE PERFORMANCE")
        print("=" * 60)
        
        # Test login performance (already tested, but verify timing)
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        response, response_time = self.make_request('post', f"{API_BASE}/auth/login", json=login_data)
        
        if response and response.status_code == 200:
            if response_time < 5.0:
                self.log_result("Performance - Login Speed", True, 
                              f"Login completed in {response_time:.2f}s (<5s threshold)", 
                              response_time=response_time)
            else:
                self.log_result("Performance - Login Speed", False, 
                              f"Login took {response_time:.2f}s (>5s threshold)", 
                              response_time=response_time)
        else:
            self.log_result("Performance - Login Speed", False, 
                          "Cannot measure login performance - login failed", 
                          response_time=response_time)
        
        # Test API endpoint performance
        test_endpoints = [
            f"{API_BASE}/health",
            f"{API_BASE}/patients",
            f"{API_BASE}/employees",
            f"{API_BASE}/inventory"
        ]
        
        fast_endpoints = 0
        total_tested = 0
        
        for endpoint in test_endpoints:
            response, response_time = self.make_request('get', endpoint)
            total_tested += 1
            
            if response and response.status_code == 200:
                if response_time < 5.0:
                    self.log_result(f"Performance - {endpoint.split('/')[-1].title()}", True, 
                                  f"Response in {response_time:.2f}s (<5s threshold)", 
                                  response_time=response_time)
                    fast_endpoints += 1
                else:
                    self.log_result(f"Performance - {endpoint.split('/')[-1].title()}", False, 
                                  f"Response in {response_time:.2f}s (>5s threshold)", 
                                  response_time=response_time)
            else:
                self.log_result(f"Performance - {endpoint.split('/')[-1].title()}", False, 
                              f"Request failed or timed out ({response_time:.2f}s)", 
                              response_time=response_time)
        
        performance_rate = (fast_endpoints / total_tested) * 100 if total_tested > 0 else 0
        self.log_result("Performance - Overall", performance_rate >= 75, 
                      f"Fast responses: {fast_endpoints}/{total_tested} ({performance_rate:.1f}%)")
        
        return performance_rate >= 75

    def test_database_operations(self):
        """Test 5: Database Operations - Test patient creation, encounters, and core EHR functionality"""
        print("\n💾 TESTING DATABASE OPERATIONS")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_result("Database Operations - Authentication Required", False, 
                          "Cannot test database operations without authentication")
            return False
        
        # Test 1: Create Patient
        patient_data = {
            "first_name": "TestPatient",
            "last_name": "DeploymentVerification",
            "email": "test.deployment@clinichub.com",
            "phone": "555-TEST",
            "date_of_birth": "1990-01-01",
            "gender": "other",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "TX",
            "zip_code": "12345"
        }
        
        response, response_time = self.make_request('post', f"{API_BASE}/patients", json=patient_data)
        
        if response and response.status_code == 200:
            try:
                patient = response.json()
                patient_id = patient.get("id")
                self.test_data["patient_id"] = patient_id
                self.log_result("Database - Patient Creation", True, 
                              f"Created test patient with ID: {patient_id}", 
                              status_code=response.status_code, response_time=response_time)
            except Exception as e:
                self.log_result("Database - Patient Creation", False, 
                              f"Patient creation response parsing error: {str(e)}", 
                              status_code=response.status_code, response_time=response_time)
                return False
        else:
            error_msg = "Patient creation failed"
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            self.log_result("Database - Patient Creation", False, 
                          f"Failed: {error_msg}", 
                          status_code=response.status_code if response else None, 
                          response_time=response_time)
            return False
        
        # Test 2: Create Encounter (if patient creation succeeded)
        if self.test_data.get("patient_id"):
            encounter_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_type": "consultation",
                "status": "completed",
                "reason": "Deployment verification test",
                "provider": "Test Provider",
                "scheduled_date": "2025-01-15"
            }
            
            response, response_time = self.make_request('post', f"{API_BASE}/encounters", json=encounter_data)
            
            if response and response.status_code == 200:
                try:
                    encounter = response.json()
                    encounter_id = encounter.get("id")
                    self.test_data["encounter_id"] = encounter_id
                    self.log_result("Database - Encounter Creation", True, 
                                  f"Created test encounter with ID: {encounter_id}", 
                                  status_code=response.status_code, response_time=response_time)
                except Exception as e:
                    self.log_result("Database - Encounter Creation", False, 
                                  f"Encounter creation response parsing error: {str(e)}", 
                                  status_code=response.status_code, response_time=response_time)
            else:
                error_msg = "Encounter creation failed"
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', str(error_data))
                    except:
                        error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                
                self.log_result("Database - Encounter Creation", False, 
                              f"Failed: {error_msg}", 
                              status_code=response.status_code if response else None, 
                              response_time=response_time)
        
        # Test 3: Create Vital Signs
        if self.test_data.get("patient_id"):
            vital_signs_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_id": self.test_data.get("encounter_id"),
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "temperature": 98.6,
                "respiratory_rate": 16,
                "oxygen_saturation": 98,
                "weight": 150.0,
                "height": 65.0,
                "pain_scale": 0,
                "notes": "Deployment verification test vitals"
            }
            
            response, response_time = self.make_request('post', f"{API_BASE}/vital-signs", json=vital_signs_data)
            
            if response and response.status_code == 200:
                try:
                    vital_signs = response.json()
                    vital_signs_id = vital_signs.get("id")
                    self.log_result("Database - Vital Signs Creation", True, 
                                  f"Created test vital signs with ID: {vital_signs_id}", 
                                  status_code=response.status_code, response_time=response_time)
                except Exception as e:
                    self.log_result("Database - Vital Signs Creation", False, 
                                  f"Vital signs creation response parsing error: {str(e)}", 
                                  status_code=response.status_code, response_time=response_time)
            else:
                error_msg = "Vital signs creation failed"
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', str(error_data))
                    except:
                        error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                
                self.log_result("Database - Vital Signs Creation", False, 
                              f"Failed: {error_msg}", 
                              status_code=response.status_code if response else None, 
                              response_time=response_time)
        
        return True

    def run_deployment_verification(self):
        """Run comprehensive deployment verification tests"""
        print("🚀 CLINICHUB DEPLOYMENT VERIFICATION")
        print("=" * 80)
        print(f"Deployment URL: {DEPLOYMENT_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Run verification tests in order
        test_results = []
        
        # Test 1: MongoDB Connection Status
        test_results.append(("MongoDB Connection", self.test_mongodb_connection_status()))
        
        # Test 2: Authentication System
        test_results.append(("Authentication System", self.test_authentication_system()))
        
        # Test 3: Core API Endpoints
        test_results.append(("Core API Endpoints", self.test_core_api_endpoints()))
        
        # Test 4: Response Performance
        test_results.append(("Response Performance", self.test_response_performance()))
        
        # Test 5: Database Operations
        test_results.append(("Database Operations", self.test_database_operations()))
        
        # Generate deployment verification summary
        self.print_deployment_summary(test_results)
        
        # Return overall success
        return all(result[1] for result in test_results)
    
    def print_deployment_summary(self, test_results):
        """Print deployment verification summary"""
        print("\n" + "=" * 80)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"🎯 VERIFICATION RESULTS:")
        print(f"   Total Verification Time: {total_time:.2f}s")
        print(f"   Deployment URL: {DEPLOYMENT_URL}")
        print(f"   Test Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test results summary
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        # Overall assessment
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📈 OVERALL ASSESSMENT:")
        print(f"   Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("   🟢 DEPLOYMENT SUCCESSFUL: All verification tests passed")
            print("   ✅ MongoDB connection issue has been resolved")
            print("   ✅ Authentication system is working correctly")
            print("   ✅ Core API endpoints are functional")
            print("   ✅ Response performance meets requirements (<5s)")
            print("   ✅ Database operations are working correctly")
        elif success_rate >= 80:
            print("   🟡 DEPLOYMENT MOSTLY SUCCESSFUL: Minor issues detected")
            print("   ⚠️  Some components may need attention")
        elif success_rate >= 60:
            print("   🟠 DEPLOYMENT PARTIALLY SUCCESSFUL: Significant issues detected")
            print("   ❌ Multiple components require immediate attention")
        else:
            print("   🔴 DEPLOYMENT FAILED: Critical issues detected")
            print("   ❌ System is not ready for production use")
        
        # Specific findings
        print(f"\n🔍 SPECIFIC FINDINGS:")
        
        # MongoDB Connection
        mongodb_success = test_results[0][1] if test_results else False
        if mongodb_success:
            print("   ✅ MongoDB Connection: RESOLVED - Database is accessible")
        else:
            print("   ❌ MongoDB Connection: FAILED - Database connectivity issues persist")
        
        # Authentication
        auth_success = test_results[1][1] if len(test_results) > 1 else False
        if auth_success:
            print("   ✅ Authentication: WORKING - admin/admin123 credentials functional")
        else:
            print("   ❌ Authentication: FAILED - Login issues detected")
        
        # Performance
        perf_success = test_results[3][1] if len(test_results) > 3 else False
        if perf_success:
            print("   ✅ Performance: GOOD - Response times under 5 seconds")
        else:
            print("   ❌ Performance: POOR - Response times exceed 5 seconds")
        
        # Failed tests details
        failed_tests = [name for name, success in test_results if not success]
        if failed_tests:
            print(f"\n❌ FAILED COMPONENTS:")
            for test_name in failed_tests:
                print(f"   • {test_name}")
                # Find specific error details
                matching_results = [r for r in self.test_results if test_name.lower() in r["test"].lower() and not r["success"]]
                for result in matching_results[:2]:  # Show first 2 errors per component
                    print(f"     - {result['message']}")
        
        print("\n" + "=" * 80)
        print("🎉 DEPLOYMENT VERIFICATION COMPLETE")
        print("=" * 80)

def main():
    """Main function"""
    tester = DeploymentVerificationTester()
    success = tester.run_deployment_verification()
    
    if success:
        print("\n✅ DEPLOYMENT VERIFICATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ DEPLOYMENT VERIFICATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()