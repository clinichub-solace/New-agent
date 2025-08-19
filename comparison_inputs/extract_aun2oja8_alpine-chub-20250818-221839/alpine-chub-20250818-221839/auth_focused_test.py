#!/usr/bin/env python3
"""
ClinicHub Backend Authentication System Test
Focus: LOGIN ISSUE PREVENTION CHECK

This test specifically addresses the user's concerns about potential login issues
and conducts a comprehensive authentication system verification.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_backend_connectivity(self):
        """Test if backend is accessible"""
        try:
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Backend Connectivity", 
                    True, 
                    f"Backend accessible at {BACKEND_URL}",
                    {"status_code": response.status_code, "response": data}
                )
                return True
            else:
                self.log_result(
                    "Backend Connectivity", 
                    False, 
                    f"Backend returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_result(
                "Backend Connectivity", 
                False, 
                f"Cannot connect to backend: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_health_endpoint(self):
        """Test backend health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Health Endpoint", 
                    True, 
                    "Health endpoint responding correctly",
                    {"response": data}
                )
                return True
            else:
                self.log_result(
                    "Health Endpoint", 
                    False, 
                    f"Health endpoint returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_result(
                "Health Endpoint", 
                False, 
                f"Health endpoint error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_admin_user_initialization(self):
        """Test admin user initialization"""
        try:
            # First try to initialize admin user
            response = self.session.post(f"{API_BASE}/auth/init-admin", timeout=10)
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_result(
                    "Admin User Initialization", 
                    True, 
                    "Admin user initialized successfully",
                    {"response": data}
                )
                return True
            else:
                self.log_result(
                    "Admin User Initialization", 
                    False, 
                    f"Admin initialization failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
        except Exception as e:
            self.log_result(
                "Admin User Initialization", 
                False, 
                f"Admin initialization error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_admin_login(self):
        """Test admin/admin123 login credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login", 
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.log_result(
                        "Admin Login", 
                        True, 
                        "Admin login successful with valid JWT token",
                        {
                            "token_received": True,
                            "token_length": len(self.auth_token),
                            "user_info": {k: v for k, v in data.items() if k != "access_token"}
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Admin Login", 
                        False, 
                        "Login successful but no access token received",
                        {"response": data}
                    )
                    return False
            else:
                self.log_result(
                    "Admin Login", 
                    False, 
                    f"Login failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Admin Login", 
                False, 
                f"Login error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        if not self.auth_token:
            self.log_result(
                "JWT Token Validation", 
                False, 
                "No auth token available for validation",
                {}
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "JWT Token Validation", 
                    True, 
                    "JWT token validation successful",
                    {"user_data": data}
                )
                return True
            else:
                self.log_result(
                    "JWT Token Validation", 
                    False, 
                    f"Token validation failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "JWT Token Validation", 
                False, 
                f"Token validation error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_protected_endpoint_access(self):
        """Test access to protected endpoints"""
        if not self.auth_token:
            self.log_result(
                "Protected Endpoint Access", 
                False, 
                "No auth token available for protected endpoint test",
                {}
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test multiple protected endpoints
            protected_endpoints = [
                "/patients",
                "/employees", 
                "/inventory",
                "/invoices",
                "/financial-transactions"
            ]
            
            successful_endpoints = []
            failed_endpoints = []
            
            for endpoint in protected_endpoints:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}", headers=headers, timeout=10)
                    if response.status_code in [200, 201]:
                        successful_endpoints.append(endpoint)
                    else:
                        failed_endpoints.append(f"{endpoint} ({response.status_code})")
                except Exception as e:
                    failed_endpoints.append(f"{endpoint} (error: {str(e)})")
            
            if len(successful_endpoints) >= 3:  # At least 3 endpoints should work
                self.log_result(
                    "Protected Endpoint Access", 
                    True, 
                    f"Protected endpoints accessible ({len(successful_endpoints)}/{len(protected_endpoints)})",
                    {
                        "successful": successful_endpoints,
                        "failed": failed_endpoints
                    }
                )
                return True
            else:
                self.log_result(
                    "Protected Endpoint Access", 
                    False, 
                    f"Too many protected endpoints failed ({len(failed_endpoints)}/{len(protected_endpoints)})",
                    {
                        "successful": successful_endpoints,
                        "failed": failed_endpoints
                    }
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Protected Endpoint Access", 
                False, 
                f"Protected endpoint test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_unauthorized_access_prevention(self):
        """Test that endpoints properly reject unauthorized access"""
        try:
            # Test without token
            response = self.session.get(f"{API_BASE}/patients", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthorized Access Prevention", 
                    True, 
                    f"Properly rejected unauthorized access (status {response.status_code})",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_result(
                    "Unauthorized Access Prevention", 
                    False, 
                    f"Failed to reject unauthorized access (status {response.status_code})",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Unauthorized Access Prevention", 
                False, 
                f"Unauthorized access test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_invalid_credentials(self):
        """Test rejection of invalid credentials"""
        try:
            invalid_login_data = {
                "username": "admin",
                "password": "wrongpassword"
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login", 
                json=invalid_login_data,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Invalid Credentials Rejection", 
                    True, 
                    f"Properly rejected invalid credentials (status {response.status_code})",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_result(
                    "Invalid Credentials Rejection", 
                    False, 
                    f"Failed to reject invalid credentials (status {response.status_code})",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Invalid Credentials Rejection", 
                False, 
                f"Invalid credentials test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_database_connectivity(self):
        """Test database connectivity through API"""
        if not self.auth_token:
            self.log_result(
                "Database Connectivity", 
                False, 
                "No auth token available for database test",
                {}
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Try to access a simple endpoint that requires database
            response = self.session.get(f"{API_BASE}/patients", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Database Connectivity", 
                    True, 
                    "Database accessible through API",
                    {"patient_count": len(data) if isinstance(data, list) else "unknown"}
                )
                return True
            else:
                self.log_result(
                    "Database Connectivity", 
                    False, 
                    f"Database access failed (status {response.status_code})",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Database Connectivity", 
                False, 
                f"Database connectivity test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            # Test preflight request
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
            
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers, timeout=10)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            if response.status_code in [200, 204] and cors_headers["Access-Control-Allow-Origin"]:
                self.log_result(
                    "CORS Configuration", 
                    True, 
                    "CORS properly configured for frontend access",
                    {"cors_headers": cors_headers}
                )
                return True
            else:
                self.log_result(
                    "CORS Configuration", 
                    False, 
                    f"CORS configuration issue (status {response.status_code})",
                    {"status_code": response.status_code, "cors_headers": cors_headers}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "CORS Configuration", 
                False, 
                f"CORS test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_session_management(self):
        """Test session management and logout"""
        if not self.auth_token:
            self.log_result(
                "Session Management", 
                False, 
                "No auth token available for session test",
                {}
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test logout
            response = self.session.post(f"{API_BASE}/auth/logout", headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                # Try to use the token after logout (should fail)
                test_response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
                
                if test_response.status_code in [401, 403]:
                    self.log_result(
                        "Session Management", 
                        True, 
                        "Logout successful, token properly invalidated",
                        {"logout_status": response.status_code, "token_invalid": True}
                    )
                    return True
                else:
                    self.log_result(
                        "Session Management", 
                        False, 
                        "Logout successful but token still valid",
                        {"logout_status": response.status_code, "token_still_valid": True}
                    )
                    return False
            else:
                self.log_result(
                    "Session Management", 
                    False, 
                    f"Logout failed (status {response.status_code})",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Session Management", 
                False, 
                f"Session management test error: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def run_comprehensive_authentication_test(self):
        """Run all authentication tests"""
        print("🔍 CLINICHUB AUTHENTICATION SYSTEM TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run all tests in order
        tests = [
            self.test_backend_connectivity,
            self.test_health_endpoint,
            self.test_admin_user_initialization,
            self.test_admin_login,
            self.test_jwt_token_validation,
            self.test_protected_endpoint_access,
            self.test_unauthorized_access_prevention,
            self.test_invalid_credentials,
            self.test_database_connectivity,
            self.test_cors_configuration,
            self.test_session_management
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test.__name__}: {str(e)}")
                print()
        
        # Summary
        print("=" * 60)
        print("🏥 AUTHENTICATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            print("✅ Login system is BULLETPROOF and ready for production")
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"\n⚠️  MOSTLY WORKING ({passed_tests}/{total_tests} tests passed)")
            print("🔧 Minor issues detected but core authentication is functional")
        else:
            print(f"\n🚨 CRITICAL AUTHENTICATION ISSUES DETECTED!")
            print(f"❌ Only {passed_tests}/{total_tests} tests passed")
            print("🛠️  Immediate attention required before production use")
        
        print("\n" + "=" * 60)
        
        # Return summary for test_result.md
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "all_passed": passed_tests == total_tests,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = AuthenticationTester()
    results = tester.run_comprehensive_authentication_test()
    
    # Save detailed results to file
    with open("/app/auth_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Exit with appropriate code
    if results["all_passed"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()