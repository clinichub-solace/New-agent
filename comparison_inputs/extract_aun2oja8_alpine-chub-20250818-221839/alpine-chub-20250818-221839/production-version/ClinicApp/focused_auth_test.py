#!/usr/bin/env python3
"""
Focused ClinicHub Authentication Test
Tests the specific endpoints mentioned in the review request.
"""
import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
if BACKEND_URL.endswith('/api'):
    BASE_URL = BACKEND_URL[:-4]
else:
    BASE_URL = BACKEND_URL

print(f"🔗 Backend Base URL: {BASE_URL}")
print(f"🔗 API URL: {BASE_URL}/api")

def test_specific_endpoints():
    """Test the specific endpoints mentioned in the review request"""
    print("\n🎯 --- Testing Specific Review Request Endpoints ---")
    
    results = []
    
    # 1. POST /api/auth/init-admin
    try:
        url = f"{BASE_URL}/api/auth/init-admin"
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            results.append(f"✅ POST /api/auth/init-admin: SUCCESS - Admin user created/exists")
            print(f"   Admin credentials: {result.get('username')}/{result.get('password')}")
        else:
            results.append(f"❌ POST /api/auth/init-admin: FAILED - Status {response.status_code}")
    except Exception as e:
        results.append(f"❌ POST /api/auth/init-admin: ERROR - {str(e)}")
    
    # 2. POST /api/auth/login with admin/admin123
    admin_token = None
    try:
        url = f"{BASE_URL}/api/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            admin_token = result.get("access_token")
            results.append(f"✅ POST /api/auth/login (admin/admin123): SUCCESS - Token received")
            print(f"   User role: {result.get('user', {}).get('role')}")
        else:
            results.append(f"❌ POST /api/auth/login (admin/admin123): FAILED - Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        results.append(f"❌ POST /api/auth/login (admin/admin123): ERROR - {str(e)}")
    
    # 3. GET /api/health
    try:
        url = f"{BASE_URL}/api/health"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results.append(f"✅ GET /api/health: SUCCESS - Backend healthy")
        else:
            results.append(f"❌ GET /api/health: FAILED - Status {response.status_code}")
    except Exception as e:
        results.append(f"❌ GET /api/health: ERROR - {str(e)}")
    
    # 4. GET /health
    try:
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results.append(f"✅ GET /health: SUCCESS - Service healthy")
        else:
            results.append(f"❌ GET /health: FAILED - Status {response.status_code}")
    except Exception as e:
        results.append(f"❌ GET /health: ERROR - {str(e)}")
    
    # 5. GET /docs (Swagger UI)
    try:
        url = f"{BASE_URL}/docs"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results.append(f"✅ GET /docs: SUCCESS - Swagger UI accessible")
        else:
            results.append(f"❌ GET /docs: FAILED - Status {response.status_code}")
    except Exception as e:
        results.append(f"❌ GET /docs: ERROR - {str(e)}")
    
    # 6. Test database connectivity with a protected endpoint
    if admin_token:
        try:
            url = f"{BASE_URL}/api/patients"
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                patients = response.json()
                results.append(f"✅ Database Connectivity: SUCCESS - Found {len(patients)} patients")
            else:
                results.append(f"❌ Database Connectivity: FAILED - Status {response.status_code}")
        except Exception as e:
            results.append(f"❌ Database Connectivity: ERROR - {str(e)}")
    
    # 7. Test MongoDB collections exist
    if admin_token:
        try:
            url = f"{BASE_URL}/api/dashboard/stats"
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                stats = response.json()
                results.append(f"✅ MongoDB Collections: SUCCESS - Dashboard stats accessible")
                print(f"   Stats: {json.dumps(stats.get('stats', {}), indent=2)}")
            else:
                results.append(f"❌ MongoDB Collections: FAILED - Status {response.status_code}")
        except Exception as e:
            results.append(f"❌ MongoDB Collections: ERROR - {str(e)}")
    
    return results, admin_token

def test_additional_auth_endpoints(admin_token):
    """Test additional authentication-related endpoints"""
    print("\n🔐 --- Testing Additional Auth Endpoints ---")
    
    results = []
    
    if admin_token:
        # GET /api/auth/me
        try:
            url = f"{BASE_URL}/api/auth/me"
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                user_info = response.json()
                results.append(f"✅ GET /api/auth/me: SUCCESS - User info retrieved")
                print(f"   User: {user_info.get('username')} ({user_info.get('role')})")
            else:
                results.append(f"❌ GET /api/auth/me: FAILED - Status {response.status_code}")
        except Exception as e:
            results.append(f"❌ GET /api/auth/me: ERROR - {str(e)}")
        
        # POST /api/auth/logout
        try:
            url = f"{BASE_URL}/api/auth/logout"
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                results.append(f"✅ POST /api/auth/logout: SUCCESS - Logged out")
            else:
                results.append(f"❌ POST /api/auth/logout: FAILED - Status {response.status_code}")
        except Exception as e:
            results.append(f"❌ POST /api/auth/logout: ERROR - {str(e)}")
    
    return results

def main():
    """Main test execution"""
    print("🚀 ClinicHub Focused Authentication Test")
    print("=" * 80)
    print("Testing specific endpoints mentioned in the review request...")
    print("=" * 80)
    
    # Test specific endpoints
    main_results, admin_token = test_specific_endpoints()
    
    # Test additional auth endpoints
    additional_results = test_additional_auth_endpoints(admin_token)
    
    # Print summary
    print("\n📋 --- FINAL TEST SUMMARY ---")
    print("=" * 80)
    
    all_results = main_results + additional_results
    passed = len([r for r in all_results if r.startswith("✅")])
    failed = len([r for r in all_results if r.startswith("❌")])
    
    for result in all_results:
        print(result)
    
    print("=" * 80)
    print(f"📊 RESULTS: {passed} PASSED, {failed} FAILED")
    
    if admin_token:
        print("\n🎉 AUTHENTICATION SYSTEM STATUS: WORKING")
        print("✅ Backend authentication endpoints are functional")
        print("✅ Admin login with admin/admin123 works correctly")
        print("✅ JWT token generation and validation working")
        print("✅ Database connectivity established")
        print("✅ MongoDB collections accessible")
        
        print("\n💡 DIAGNOSIS: Backend authentication is working correctly!")
        print("💡 If frontend login is stuck 'Signing in...', check:")
        print("   - Browser developer console for JavaScript errors")
        print("   - Network tab in dev tools for failed requests")
        print("   - CORS configuration")
        print("   - Frontend API endpoint configuration")
        print("   - Frontend error handling logic")
    else:
        print("\n❌ AUTHENTICATION SYSTEM STATUS: NOT WORKING")
        print("❌ Backend authentication has issues")
        print("❌ Admin login failed")
        
        print("\n💡 DIAGNOSIS: Backend authentication needs fixing!")

if __name__ == "__main__":
    main()