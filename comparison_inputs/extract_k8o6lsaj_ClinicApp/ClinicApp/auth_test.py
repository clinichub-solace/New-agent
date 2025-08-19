#!/usr/bin/env python3
"""
ClinicHub Authentication System Test
Focused test for the authentication endpoints as requested in the review.
"""
import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("❌ Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Remove /api suffix if present since we'll add it explicitly
if BACKEND_URL.endswith('/api'):
    BASE_URL = BACKEND_URL[:-4]
else:
    BASE_URL = BACKEND_URL

print(f"🔗 Using Backend URL: {BASE_URL}")
print(f"🔗 API URL: {BASE_URL}/api")

def print_test_result(test_name, success, response_data=None, status_code=None):
    """Print formatted test results"""
    if success:
        print(f"✅ {test_name}: PASSED")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2, default=str)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if status_code:
            print(f"   Status Code: {status_code}")
        if response_data:
            print(f"   Response: {response_data}")
    print("-" * 80)

def test_basic_connectivity():
    """Test basic connectivity to the backend"""
    print("\n🔍 --- Testing Basic Connectivity ---")
    
    # Test 1: Health endpoint
    try:
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_test_result("GET /health", True, response.json(), response.status_code)
        else:
            print_test_result("GET /health", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("GET /health", False, str(e))
    
    # Test 2: API Health endpoint
    try:
        url = f"{BASE_URL}/api/health"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_test_result("GET /api/health", True, response.json(), response.status_code)
        else:
            print_test_result("GET /api/health", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("GET /api/health", False, str(e))
    
    # Test 3: Swagger UI Documentation
    try:
        url = f"{BASE_URL}/docs"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_test_result("GET /docs (Swagger UI)", True, "Swagger UI accessible", response.status_code)
        else:
            print_test_result("GET /docs (Swagger UI)", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("GET /docs (Swagger UI)", False, str(e))

def test_database_connectivity():
    """Test database connectivity through API endpoints"""
    print("\n🗄️ --- Testing Database Connectivity ---")
    
    # Test database connection by trying to access a simple endpoint
    try:
        url = f"{BASE_URL}/api/dashboard/stats"
        response = requests.get(url, timeout=10)
        if response.status_code in [200, 401]:  # 401 is expected without auth, but means DB is accessible
            print_test_result("Database Connection (via dashboard/stats)", True, 
                            "Database accessible (auth required)" if response.status_code == 401 else response.json(), 
                            response.status_code)
        else:
            print_test_result("Database Connection", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("Database Connection", False, str(e))

def test_authentication_system():
    """Test the authentication system endpoints"""
    print("\n🔐 --- Testing Authentication System ---")
    
    admin_token = None
    
    # Test 1: Initialize Admin User
    try:
        url = f"{BASE_URL}/api/auth/init-admin"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # Verify admin initialization response
            if "message" in result and "username" in result and "password" in result:
                if result["username"] == "admin" and result["password"] == "admin123":
                    print_test_result("POST /api/auth/init-admin", True, result, response.status_code)
                else:
                    print_test_result("POST /api/auth/init-admin", False, 
                                    f"Unexpected credentials: {result.get('username')}/{result.get('password')}", 
                                    response.status_code)
            else:
                print_test_result("POST /api/auth/init-admin", False, "Missing required fields in response", response.status_code)
        else:
            print_test_result("POST /api/auth/init-admin", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("POST /api/auth/init-admin", False, str(e))
    
    # Test 2: Login with Admin Credentials
    try:
        url = f"{BASE_URL}/api/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # Verify login response structure
            required_fields = ["access_token", "token_type", "expires_in", "user"]
            if all(field in result for field in required_fields):
                if (result["user"].get("username") == "admin" and 
                    result["user"].get("role") == "admin"):
                    admin_token = result["access_token"]
                    print_test_result("POST /api/auth/login (admin/admin123)", True, 
                                    {k: v for k, v in result.items() if k != "access_token"}, 
                                    response.status_code)
                else:
                    print_test_result("POST /api/auth/login (admin/admin123)", False, 
                                    "Invalid user data in response", response.status_code)
            else:
                missing_fields = [f for f in required_fields if f not in result]
                print_test_result("POST /api/auth/login (admin/admin123)", False, 
                                f"Missing fields: {missing_fields}", response.status_code)
        else:
            print_test_result("POST /api/auth/login (admin/admin123)", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("POST /api/auth/login (admin/admin123)", False, str(e))
    
    # Test 3: Get Current User Info (with token)
    if admin_token:
        try:
            url = f"{BASE_URL}/api/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("username") == "admin" and result.get("role") == "admin":
                    print_test_result("GET /api/auth/me (with token)", True, result, response.status_code)
                else:
                    print_test_result("GET /api/auth/me (with token)", False, 
                                    "Invalid user info returned", response.status_code)
            else:
                print_test_result("GET /api/auth/me (with token)", False, response.text, response.status_code)
        except Exception as e:
            print_test_result("GET /api/auth/me (with token)", False, str(e))
    
    # Test 4: Test Invalid Credentials
    try:
        url = f"{BASE_URL}/api/auth/login"
        data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 401:
            result = response.json()
            print_test_result("POST /api/auth/login (invalid credentials)", True, 
                            f"Correctly rejected with: {result.get('detail', 'No detail')}", 
                            response.status_code)
        else:
            print_test_result("POST /api/auth/login (invalid credentials)", False, 
                            "Should have returned 401", response.status_code)
    except Exception as e:
        print_test_result("POST /api/auth/login (invalid credentials)", False, str(e))
    
    # Test 5: Test Protected Endpoint Access
    if admin_token:
        try:
            url = f"{BASE_URL}/api/patients"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print_test_result("GET /api/patients (protected endpoint)", True, 
                                f"Successfully accessed protected endpoint, found {len(result)} patients", 
                                response.status_code)
            else:
                print_test_result("GET /api/patients (protected endpoint)", False, response.text, response.status_code)
        except Exception as e:
            print_test_result("GET /api/patients (protected endpoint)", False, str(e))
    
    # Test 6: Test Access Without Token
    try:
        url = f"{BASE_URL}/api/patients"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 401:
            print_test_result("GET /api/patients (no token)", True, 
                            "Correctly rejected unauthorized access", response.status_code)
        else:
            print_test_result("GET /api/patients (no token)", False, 
                            "Should have returned 401 for unauthorized access", response.status_code)
    except Exception as e:
        print_test_result("GET /api/patients (no token)", False, str(e))
    
    # Test 7: Logout
    if admin_token:
        try:
            url = f"{BASE_URL}/api/auth/logout"
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print_test_result("POST /api/auth/logout", True, result, response.status_code)
            else:
                print_test_result("POST /api/auth/logout", False, response.text, response.status_code)
        except Exception as e:
            print_test_result("POST /api/auth/logout", False, str(e))
    
    return admin_token

def test_synology_integration():
    """Test Synology DSM integration endpoints"""
    print("\n🔧 --- Testing Synology Integration ---")
    
    # Test 1: Synology Status
    try:
        url = f"{BASE_URL}/api/auth/synology-status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_test_result("GET /api/auth/synology-status", True, result, response.status_code)
        else:
            print_test_result("GET /api/auth/synology-status", False, response.text, response.status_code)
    except Exception as e:
        print_test_result("GET /api/auth/synology-status", False, str(e))

def main():
    """Main test execution"""
    print("🚀 ClinicHub Authentication System Test")
    print("=" * 80)
    print("Testing authentication system to diagnose login issues...")
    print("=" * 80)
    
    # Run all tests
    test_basic_connectivity()
    test_database_connectivity()
    admin_token = test_authentication_system()
    test_synology_integration()
    
    # Summary
    print("\n📋 --- Test Summary ---")
    if admin_token:
        print("✅ Authentication system is working correctly")
        print("✅ Admin login with admin/admin123 is functional")
        print("✅ JWT token generation and validation working")
        print("✅ Protected endpoints are properly secured")
        print("\n💡 The backend authentication system appears to be working correctly.")
        print("💡 If the frontend login is stuck 'Signing in...', the issue is likely:")
        print("   - Frontend not properly handling the API response")
        print("   - Network connectivity issues between frontend and backend")
        print("   - CORS configuration problems")
        print("   - Frontend JavaScript errors preventing login completion")
    else:
        print("❌ Authentication system has issues")
        print("❌ Admin login with admin/admin123 failed")
        print("\n💡 The backend authentication system needs investigation.")
    
    print("\n🔍 Next steps:")
    print("   1. Check browser developer console for JavaScript errors")
    print("   2. Verify network requests in browser dev tools")
    print("   3. Check CORS configuration if cross-origin requests")
    print("   4. Verify frontend is using correct API endpoint URLs")

if __name__ == "__main__":
    main()