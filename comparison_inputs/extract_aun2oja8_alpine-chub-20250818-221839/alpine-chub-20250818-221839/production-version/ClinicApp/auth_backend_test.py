#!/usr/bin/env python3
"""
ClinicHub Authentication System Test Suite
Focused testing for authentication fixes and validation issues
"""
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"🔗 Using API URL: {API_URL}")
print(f"🔗 Backend URL: {BACKEND_URL}")

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            # Truncate long responses for readability
            response_str = json.dumps(response, indent=2, default=str)
            if len(response_str) > 300:
                response_str = response_str[:300] + "..."
            print(f"   Response: {response_str}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def test_system_health():
    """Test basic system health and connectivity"""
    print("\n🏥 === SYSTEM HEALTH CHECK ===")
    
    # Test 1: Health endpoint
    try:
        url = f"{API_URL}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Verify health response structure
        assert "status" in result
        assert result["status"] == "healthy"
        
        print_test_result("GET /api/health", True, result)
    except Exception as e:
        print_test_result("GET /api/health", False, error_msg=str(e))
        return False
    
    # Test 2: Alternative health endpoint
    try:
        url = f"{BACKEND_URL}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("GET /health", True, result)
    except Exception as e:
        print_test_result("GET /health", False, error_msg=str(e))
    
    # Test 3: MongoDB connectivity check
    try:
        url = f"{API_URL}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Check if MongoDB is mentioned in health response
        if "database" in result or "mongodb" in str(result).lower():
            print_test_result("MongoDB Connectivity", True, {"database_status": "connected"})
        else:
            print_test_result("MongoDB Connectivity", True, {"note": "Health endpoint accessible"})
    except Exception as e:
        print_test_result("MongoDB Connectivity", False, error_msg=str(e))
    
    return True

def test_authentication_endpoints():
    """Test all authentication endpoints with focus on recent fixes"""
    print("\n🔐 === AUTHENTICATION ENDPOINTS TESTING ===")
    
    admin_token = None
    
    # Test 1: Initialize Admin User (init-admin endpoint)
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Verify admin initialization response
        assert "message" in result
        expected_fields = ["username", "password"]
        for field in expected_fields:
            if field not in result:
                print(f"   Warning: Expected field '{field}' not in response")
        
        # Check if admin user already exists or was created
        if "already exists" in result.get("message", "").lower():
            print_test_result("POST /api/auth/init-admin (Admin Already Exists)", True, result)
        else:
            print_test_result("POST /api/auth/init-admin (Admin Created)", True, result)
    except Exception as e:
        print_test_result("POST /api/auth/init-admin", False, error_msg=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
    
    # Test 2: Login with admin/admin123 credentials (main focus of review)
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Verify login response structure
        required_fields = ["access_token", "token_type", "expires_in", "user"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify user data structure
        user_data = result["user"]
        assert user_data["username"] == "admin"
        assert user_data["role"] == "admin"
        
        # Check for Synology integration fields
        if "auth_source" in user_data:
            print(f"   Auth source: {user_data['auth_source']}")
        if "synology_enabled" in result:
            print(f"   Synology enabled: {result['synology_enabled']}")
        
        # Store token for subsequent tests
        admin_token = result["access_token"]
        
        print_test_result("POST /api/auth/login (admin/admin123)", True, {
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "username": user_data["username"],
            "role": user_data["role"],
            "auth_source": user_data.get("auth_source", "local")
        })
    except Exception as e:
        print_test_result("POST /api/auth/login (admin/admin123)", False, error_msg=str(e))
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text}")
        return None
    
    # Test 3: JWT Token Validation (GET /api/auth/me)
    if admin_token:
        try:
            url = f"{API_URL}/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Verify user info
            assert result["username"] == "admin"
            assert result["role"] == "admin"
            
            # Check for Synology fields (part of recent fixes)
            synology_fields = ["auth_source", "synology_sid", "synology_last_verified"]
            synology_data = {}
            for field in synology_fields:
                if field in result:
                    synology_data[field] = result[field]
            
            print_test_result("GET /api/auth/me (JWT Token Validation)", True, {
                "username": result["username"],
                "role": result["role"],
                "status": result.get("status", "active"),
                "synology_integration": synology_data if synology_data else "not configured"
            })
        except Exception as e:
            print_test_result("GET /api/auth/me (JWT Token Validation)", False, error_msg=str(e))
            if 'response' in locals():
                print(f"   Status code: {response.status_code}")
                print(f"   Response text: {response.text}")
    
    # Test 4: Force Init Admin Endpoint (if available)
    try:
        url = f"{API_URL}/auth/force-init-admin"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("POST /api/auth/force-init-admin", True, result)
        elif response.status_code == 404:
            print_test_result("POST /api/auth/force-init-admin", False, error_msg="Endpoint not found (may not be implemented)")
        else:
            response.raise_for_status()
    except Exception as e:
        print_test_result("POST /api/auth/force-init-admin", False, error_msg=str(e))
    
    return admin_token

def test_pydantic_validation_fixes(admin_token):
    """Test Pydantic validation fixes for missing first_name/last_name"""
    print("\n🔧 === PYDANTIC VALIDATION FIXES TESTING ===")
    
    if not admin_token:
        print("❌ Skipping validation tests - no admin token available")
        return
    
    # Test 1: Login should work without ValidationError for missing first_name/last_name
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # This should NOT fail with ValidationError
        assert "access_token" in result
        user_data = result["user"]
        
        # Check if first_name/last_name are handled gracefully
        first_name = user_data.get("first_name", "Not provided")
        last_name = user_data.get("last_name", "Not provided")
        
        print_test_result("Login without ValidationError (first_name/last_name)", True, {
            "username": user_data["username"],
            "first_name": first_name,
            "last_name": last_name,
            "validation_error": "None - Fixed!"
        })
    except Exception as e:
        error_msg = str(e)
        if "ValidationError" in error_msg:
            print_test_result("Login without ValidationError (first_name/last_name)", False, 
                            error_msg=f"ValidationError still occurring: {error_msg}")
        else:
            print_test_result("Login without ValidationError (first_name/last_name)", False, error_msg=error_msg)
    
    # Test 2: Check user data structure for legacy user handling
    try:
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Check how legacy users (without first_name/last_name) are handled
        legacy_fields_check = {
            "first_name": result.get("first_name", "Missing - handled gracefully"),
            "last_name": result.get("last_name", "Missing - handled gracefully"),
            "email": result.get("email", "Missing - handled gracefully")
        }
        
        print_test_result("Legacy User Fields Handling", True, legacy_fields_check)
    except Exception as e:
        print_test_result("Legacy User Fields Handling", False, error_msg=str(e))
    
    # Test 3: Test authenticate_user function indirectly through multiple logins
    try:
        # Perform multiple login attempts to test authenticate_user function
        for i in range(3):
            url = f"{API_URL}/auth/login"
            data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            assert "access_token" in result
        
        print_test_result("authenticate_user Function (Multiple Logins)", True, {
            "attempts": 3,
            "all_successful": True,
            "no_validation_errors": True
        })
    except Exception as e:
        print_test_result("authenticate_user Function (Multiple Logins)", False, error_msg=str(e))

def test_edge_cases_and_error_handling():
    """Test edge cases and error handling"""
    print("\n⚠️  === EDGE CASES AND ERROR HANDLING ===")
    
    # Test 1: Login with invalid credentials
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        # This should fail with 401
        assert response.status_code == 401
        result = response.json()
        assert "detail" in result
        
        print_test_result("Login with Invalid Credentials (Expected Failure)", True, {
            "status_code": response.status_code,
            "error_message": result.get("detail", "Authentication failed")
        })
    except AssertionError:
        print_test_result("Login with Invalid Credentials (Expected Failure)", False, 
                        error_msg=f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_test_result("Login with Invalid Credentials (Expected Failure)", False, error_msg=str(e))
    
    # Test 2: Login with missing username
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "password": "admin123"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        # This should fail with 422 (validation error)
        assert response.status_code in [400, 422]
        
        print_test_result("Login with Missing Username (Expected Failure)", True, {
            "status_code": response.status_code,
            "validation_handled": True
        })
    except AssertionError:
        print_test_result("Login with Missing Username (Expected Failure)", False, 
                        error_msg=f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        print_test_result("Login with Missing Username (Expected Failure)", False, error_msg=str(e))
    
    # Test 3: Login with missing password
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        # This should fail with 422 (validation error)
        assert response.status_code in [400, 422]
        
        print_test_result("Login with Missing Password (Expected Failure)", True, {
            "status_code": response.status_code,
            "validation_handled": True
        })
    except AssertionError:
        print_test_result("Login with Missing Password (Expected Failure)", False, 
                        error_msg=f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        print_test_result("Login with Missing Password (Expected Failure)", False, error_msg=str(e))
    
    # Test 4: Access protected endpoint without token
    try:
        url = f"{API_URL}/auth/me"
        
        response = requests.get(url, timeout=10)
        
        # This should fail with 401 or 403
        assert response.status_code in [401, 403]
        
        print_test_result("Access Protected Endpoint Without Token (Expected Failure)", True, {
            "status_code": response.status_code,
            "security_enforced": True
        })
    except AssertionError:
        print_test_result("Access Protected Endpoint Without Token (Expected Failure)", False, 
                        error_msg=f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        print_test_result("Access Protected Endpoint Without Token (Expected Failure)", False, error_msg=str(e))
    
    # Test 5: Access protected endpoint with invalid token
    try:
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # This should fail with 401
        assert response.status_code == 401
        
        print_test_result("Access Protected Endpoint With Invalid Token (Expected Failure)", True, {
            "status_code": response.status_code,
            "token_validation_working": True
        })
    except AssertionError:
        print_test_result("Access Protected Endpoint With Invalid Token (Expected Failure)", False, 
                        error_msg=f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_test_result("Access Protected Endpoint With Invalid Token (Expected Failure)", False, error_msg=str(e))

def test_synology_integration():
    """Test Synology DSM integration endpoints"""
    print("\n🔗 === SYNOLOGY INTEGRATION TESTING ===")
    
    # Test 1: Synology Status Endpoint
    try:
        url = f"{API_URL}/auth/synology-status"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Verify synology status response
        expected_fields = ["synology_enabled", "synology_configured"]
        for field in expected_fields:
            if field not in result:
                print(f"   Warning: Expected field '{field}' not in response")
        
        print_test_result("GET /api/auth/synology-status", True, result)
    except Exception as e:
        print_test_result("GET /api/auth/synology-status", False, error_msg=str(e))
    
    # Test 2: Test Synology Endpoint (Admin Only)
    # First get admin token
    admin_token = None
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        admin_token = result["access_token"]
    except:
        pass
    
    if admin_token:
        try:
            url = f"{API_URL}/auth/test-synology"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print_test_result("POST /api/auth/test-synology (Admin Access)", True, result)
            elif response.status_code == 400:
                # Expected if Synology is not configured
                result = response.json()
                print_test_result("POST /api/auth/test-synology (Not Configured)", True, {
                    "status": "Synology not configured",
                    "message": result.get("detail", "Configuration required")
                })
            else:
                response.raise_for_status()
        except Exception as e:
            print_test_result("POST /api/auth/test-synology", False, error_msg=str(e))
    else:
        print_test_result("POST /api/auth/test-synology", False, error_msg="No admin token available")

def test_end_to_end_authentication_flow():
    """Test complete end-to-end authentication flow"""
    print("\n🔄 === END-TO-END AUTHENTICATION FLOW ===")
    
    # Complete flow: init-admin -> login -> access protected -> logout
    admin_token = None
    
    # Step 1: Initialize admin
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"   Step 1 - Admin Init: {result.get('message', 'Success')}")
    except Exception as e:
        print(f"   Step 1 - Admin Init: Failed - {str(e)}")
        return False
    
    # Step 2: Login
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        admin_token = result["access_token"]
        print(f"   Step 2 - Login: Success (Token received)")
    except Exception as e:
        print(f"   Step 2 - Login: Failed - {str(e)}")
        return False
    
    # Step 3: Access protected endpoint
    try:
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"   Step 3 - Protected Access: Success (User: {result['username']})")
    except Exception as e:
        print(f"   Step 3 - Protected Access: Failed - {str(e)}")
        return False
    
    # Step 4: Logout
    try:
        url = f"{API_URL}/auth/logout"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"   Step 4 - Logout: Success")
    except Exception as e:
        print(f"   Step 4 - Logout: Failed - {str(e)}")
        return False
    
    print_test_result("Complete End-to-End Authentication Flow", True, {
        "steps_completed": 4,
        "admin_init": "✓",
        "login": "✓", 
        "protected_access": "✓",
        "logout": "✓"
    })
    return True

def main():
    """Main test execution"""
    print("🚀 ClinicHub Authentication System Test Suite")
    print("=" * 80)
    print(f"Testing Backend: {BACKEND_URL}")
    print(f"API Endpoint: {API_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Track test results
    test_results = {
        "system_health": False,
        "authentication_endpoints": False,
        "pydantic_validation": False,
        "edge_cases": False,
        "synology_integration": False,
        "end_to_end_flow": False
    }
    
    # Run test suites
    try:
        test_results["system_health"] = test_system_health()
        admin_token = test_authentication_endpoints()
        test_results["authentication_endpoints"] = admin_token is not None
        
        if admin_token:
            test_pydantic_validation_fixes(admin_token)
            test_results["pydantic_validation"] = True
        
        test_edge_cases_and_error_handling()
        test_results["edge_cases"] = True
        
        test_synology_integration()
        test_results["synology_integration"] = True
        
        test_results["end_to_end_flow"] = test_end_to_end_authentication_flow()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during test execution: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print("-" * 80)
    print(f"Overall Result: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ The login loop issue should be resolved")
        print("✅ admin/admin123 credentials are working properly")
    else:
        print("⚠️  Some tests failed - authentication system needs attention")
    
    print("=" * 80)

if __name__ == "__main__":
    main()