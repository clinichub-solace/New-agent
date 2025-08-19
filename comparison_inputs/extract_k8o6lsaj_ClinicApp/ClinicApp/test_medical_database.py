#!/usr/bin/env python3
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
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Helper function to print test results
def print_test_result(test_name, success, response=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

# Test Authentication to get a token
def get_auth_token():
    print("\n--- Getting Authentication Token ---")
    
    try:
        # First, initialize admin if needed
        init_url = f"{API_URL}/auth/init-admin"
        requests.post(init_url)
        
        # Login to get token
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        token = result["access_token"]
        print_test_result("Get Auth Token", True, {"token": token[:20] + "..."})
        return token
    except Exception as e:
        print(f"Error getting auth token: {str(e)}")
        print_test_result("Get Auth Token", False)
        return None

# Test ICD-10 Database Endpoints
def test_icd10_database(token):
    print("\n--- Testing ICD-10 Database Endpoints ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Initialize ICD-10 codes
    try:
        url = f"{API_URL}/icd10/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize ICD-10 Codes", True, result)
    except Exception as e:
        print(f"Error initializing ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize ICD-10 Codes", False)
    
    # Test 2: Search ICD-10 codes
    try:
        url = f"{API_URL}/icd10/search"
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        if len(result) > 0:
            assert "code" in result[0]
            assert "description" in result[0]
            
        print_test_result("Search ICD-10 Codes (diabetes)", True, result)
    except Exception as e:
        print(f"Error searching ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search ICD-10 Codes (diabetes)", False)
    
    # Test 3: Get all ICD-10 codes
    try:
        url = f"{API_URL}/icd10/comprehensive"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive codes
        assert isinstance(result, list)
        if len(result) > 0:
            assert "code" in result[0]
            assert "description" in result[0]
            
        print_test_result("Get All ICD-10 Codes", True, {"count": len(result), "sample": result[:2]})
    except Exception as e:
        print(f"Error getting all ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All ICD-10 Codes", False)

# Test Comprehensive Medication Database Endpoints
def test_comprehensive_medications(token):
    print("\n--- Testing Comprehensive Medication Database Endpoints ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Initialize comprehensive medication database
    try:
        url = f"{API_URL}/comprehensive-medications/init"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Initialize Comprehensive Medications", True, result)
    except Exception as e:
        print(f"Error initializing comprehensive medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Comprehensive Medications", False)
    
    # Test 2: Search medications for blood pressure
    try:
        url = f"{API_URL}/comprehensive-medications/search"
        params = {"query": "blood pressure"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        if len(result) > 0:
            assert "generic_name" in result[0]
            assert "drug_class" in result[0]
            
        print_test_result("Search Medications (blood pressure)", True, result)
    except Exception as e:
        print(f"Error searching medications for blood pressure: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (blood pressure)", False)
    
    # Test 3: Search medications for diabetes
    try:
        url = f"{API_URL}/comprehensive-medications/search"
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Search Medications (diabetes)", True, result)
    except Exception as e:
        print(f"Error searching medications for diabetes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (diabetes)", False)
    
    # Test 4: Search medications for exact medication name
    try:
        url = f"{API_URL}/comprehensive-medications/search"
        params = {"query": "lisinopril"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Search Medications (lisinopril)", True, result)
    except Exception as e:
        print(f"Error searching medications for lisinopril: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (lisinopril)", False)
    
    # Test 5: Get all medications
    try:
        url = f"{API_URL}/comprehensive-medications"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive medications
        assert isinstance(result, list)
        if len(result) > 0:
            assert "generic_name" in result[0]
            assert "drug_class" in result[0]
            
        print_test_result("Get All Medications", True, {"count": len(result), "sample": result[:2]})
    except Exception as e:
        print(f"Error getting all medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Medications", False)
    
    # Test 6: Filter medications by drug class
    try:
        url = f"{API_URL}/comprehensive-medications"
        params = {"drug_class": "NSAID"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Filter Medications by Drug Class (NSAID)", True, result)
    except Exception as e:
        print(f"Error filtering medications by drug class: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Filter Medications by Drug Class (NSAID)", False)

# Main function
def main():
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication token")
        return
    
    # Test ICD-10 Database Endpoints
    test_icd10_database(token)
    
    # Test Comprehensive Medication Database Endpoints
    test_comprehensive_medications(token)
    
    print("\n--- Testing Summary ---")
    print("All tests completed. Check the results above for any failures.")

if __name__ == "__main__":
    main()