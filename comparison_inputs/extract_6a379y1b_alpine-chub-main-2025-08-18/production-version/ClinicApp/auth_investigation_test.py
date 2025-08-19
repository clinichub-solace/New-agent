#!/usr/bin/env python3
"""
Critical Authentication Investigation Test for ClinicHub
Focus: Investigate "Incorrect username or password" error with admin/admin123
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
    print("❌ Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"🔍 CRITICAL AUTHENTICATION INVESTIGATION")
print(f"📍 Using API URL: {API_URL}")
print(f"🕐 Test started at: {datetime.now()}")
print("=" * 80)

def print_test_result(test_name, success, response=None, details=None):
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} {test_name}")
    if details:
        print(f"   Details: {details}")
    if response:
        if isinstance(response, dict):
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:500]}...")
        else:
            print(f"   Response: {str(response)[:500]}...")
    print("-" * 80)

def test_backend_connectivity():
    """Test 1: Basic Backend Connectivity"""
    print("\n🔍 TEST 1: Backend Connectivity")
    
    try:
        # Test root endpoint
        response = requests.get(BACKEND_URL, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Backend Root Endpoint", True, result, f"Status: {response.status_code}")
        return True
    except Exception as e:
        print_test_result("Backend Root Endpoint", False, None, f"Error: {str(e)}")
        return False

def test_health_endpoint():
    """Test 2: Health Endpoint"""
    print("\n🔍 TEST 2: Health Endpoint")
    
    try:
        url = f"{API_URL}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Health Endpoint", True, result, f"Status: {response.status_code}")
        return True
    except Exception as e:
        print_test_result("Health Endpoint", False, None, f"Error: {str(e)}")
        return False

def test_database_connection():
    """Test 3: Database Connection via Backend"""
    print("\n🔍 TEST 3: Database Connection Test")
    
    try:
        # Try to access an endpoint that requires database
        url = f"{API_URL}/patients"
        response = requests.get(url, timeout=10)
        
        # Even if it returns 401 (unauthorized), it means the backend is running and can connect to DB
        if response.status_code in [200, 401, 403]:
            print_test_result("Database Connection", True, None, f"Backend responding with status: {response.status_code}")
            return True
        else:
            print_test_result("Database Connection", False, None, f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Database Connection", False, None, f"Error: {str(e)}")
        return False

def test_admin_initialization():
    """Test 4: Admin User Initialization"""
    print("\n🔍 TEST 4: Admin User Initialization")
    
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Admin Initialization", True, result, "Admin user initialized successfully")
            return True
        elif response.status_code == 409:
            result = response.json()
            print_test_result("Admin Initialization", True, result, "Admin user already exists")
            return True
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Admin Initialization", False, result, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Admin Initialization", False, None, f"Error: {str(e)}")
        return False

def test_force_admin_initialization():
    """Test 5: Force Admin User Re-initialization"""
    print("\n🔍 TEST 5: Force Admin User Re-initialization")
    
    try:
        url = f"{API_URL}/auth/force-init-admin"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("Force Admin Initialization", True, result, "Admin user forcefully re-initialized")
            return True
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Force Admin Initialization", False, result, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Force Admin Initialization", False, None, f"Error: {str(e)}")
        return False

def test_admin_login():
    """Test 6: Critical Admin Login Test"""
    print("\n🔍 TEST 6: CRITICAL - Admin Login with admin/admin123")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print(f"   Attempting login to: {url}")
        print(f"   Credentials: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Verify required fields in response
            required_fields = ["access_token", "token_type", "user"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                print_test_result("Admin Login", False, result, f"Missing fields: {missing_fields}")
                return None
            
            print_test_result("Admin Login", True, result, "Login successful - JWT token received")
            return result["access_token"]
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Admin Login", False, result, f"Login failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        print_test_result("Admin Login", False, None, f"Error: {str(e)}")
        return None

def test_invalid_login():
    """Test 7: Invalid Login Test (Should Fail)"""
    print("\n🔍 TEST 7: Invalid Login Test (Expected to Fail)")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 401:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Invalid Login (Expected Failure)", True, result, "Correctly rejected invalid credentials")
            return True
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Invalid Login (Expected Failure)", False, result, f"Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Invalid Login (Expected Failure)", False, None, f"Error: {str(e)}")
        return False

def test_jwt_validation(token):
    """Test 8: JWT Token Validation"""
    print("\n🔍 TEST 8: JWT Token Validation")
    
    if not token:
        print_test_result("JWT Token Validation", False, None, "No token available for testing")
        return False
    
    try:
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("JWT Token Validation", True, result, "Token is valid and user info retrieved")
            return True
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("JWT Token Validation", False, result, f"Token validation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("JWT Token Validation", False, None, f"Error: {str(e)}")
        return False

def test_protected_endpoint(token):
    """Test 9: Protected Endpoint Access"""
    print("\n🔍 TEST 9: Protected Endpoint Access")
    
    if not token:
        print_test_result("Protected Endpoint Access", False, None, "No token available for testing")
        return False
    
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code in [200, 404]:  # 200 = success, 404 = no patients but auth worked
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Protected Endpoint Access", True, result, f"Successfully accessed protected endpoint: {response.status_code}")
            return True
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_test_result("Protected Endpoint Access", False, result, f"Access denied: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Protected Endpoint Access", False, None, f"Error: {str(e)}")
        return False

def test_cors_configuration():
    """Test 10: CORS Configuration"""
    print("\n🔍 TEST 10: CORS Configuration")
    
    try:
        url = f"{API_URL}/health"
        headers = {
            "Origin": "https://ecf9c07e-b68e-4d07-9324-af4a7e057b56.preview.emergentagent.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        # Send OPTIONS request to check CORS
        response = requests.options(url, headers=headers, timeout=10)
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        print_test_result("CORS Configuration", True, cors_headers, f"CORS preflight status: {response.status_code}")
        return True
        
    except Exception as e:
        print_test_result("CORS Configuration", False, None, f"Error: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🚀 Starting Critical Authentication Investigation...")
    
    # Track test results
    results = {}
    
    # Run all tests
    results["connectivity"] = test_backend_connectivity()
    results["health"] = test_health_endpoint()
    results["database"] = test_database_connection()
    results["admin_init"] = test_admin_initialization()
    results["force_admin_init"] = test_force_admin_initialization()
    
    # Critical login test
    token = test_admin_login()
    results["admin_login"] = token is not None
    
    results["invalid_login"] = test_invalid_login()
    results["jwt_validation"] = test_jwt_validation(token)
    results["protected_access"] = test_protected_endpoint(token)
    results["cors"] = test_cors_configuration()
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 CRITICAL AUTHENTICATION INVESTIGATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"📊 Overall Results: {passed}/{total} tests passed")
    print()
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print()
    
    # Critical findings
    if results["admin_login"]:
        print("🎉 CRITICAL FINDING: Admin login with admin/admin123 is WORKING!")
        print("   The authentication system is functional.")
        if token:
            print(f"   JWT Token received and validated successfully.")
    else:
        print("🚨 CRITICAL ISSUE: Admin login with admin/admin123 is FAILING!")
        print("   This confirms the reported authentication problem.")
    
    print()
    print("🔍 Next Steps:")
    if not results["connectivity"]:
        print("   1. Check backend server status and network connectivity")
    elif not results["database"]:
        print("   1. Check MongoDB connection and database configuration")
    elif not results["admin_init"]:
        print("   1. Check admin user initialization process")
    elif not results["admin_login"]:
        print("   1. Check password hashing and validation logic")
        print("   2. Check user authentication function")
        print("   3. Verify admin user exists in database with correct credentials")
    else:
        print("   1. Authentication system appears to be working correctly")
        print("   2. Issue may be in frontend implementation or network layer")
    
    print(f"\n🕐 Test completed at: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()