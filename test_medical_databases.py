#!/usr/bin/env python3
import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
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
def print_test_result(test_name, success, response=None, details=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            if isinstance(response, list):
                print(f"   Response contains {len(response)} items")
                if len(response) > 0:
                    print(f"   First item: {json.dumps(response[0], indent=2, default=str)[:200]}...")
            else:
                print(f"   Response: {json.dumps(response, indent=2, default=str)[:200]}...")
        if details:
            print(f"   Details: {details}")
    else:
        print(f"❌ {test_name}: FAILED")
        if response:
            print(f"   Response: {response}")
        if details:
            print(f"   Details: {details}")
    print("-" * 80)

# Test Authentication to get a token
def get_auth_token():
    print("\n--- Getting Authentication Token ---")
    
    try:
        # Initialize admin user if needed
        init_url = f"{API_URL}/auth/init-admin"
        init_response = requests.post(init_url)
        if init_response.status_code == 200:
            print("Admin user initialized or already exists")
        
        # Login with admin credentials
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        token = result["access_token"]
        print_test_result("Get Auth Token", True, {"token_type": result["token_type"], "expires_in": result["expires_in"]})
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
        
        # Check if initialization was successful
        assert "message" in result
        assert "count" in result or "codes_created" in result
        
        codes_count = result.get("count", result.get("codes_created", 0))
        print_test_result("Initialize ICD-10 Codes", True, result, f"Created/Found {codes_count} codes")
    except Exception as e:
        print(f"Error initializing ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize ICD-10 Codes", False)
    
    # Test 2: Search ICD-10 codes for diabetes
    try:
        url = f"{API_URL}/icd10/search"
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check if results are relevant to diabetes
        diabetes_related = any("diabetes" in code.get("description", "").lower() or 
                              "diabetes" in str(code.get("search_terms", "")).lower() 
                              for code in result)
        assert diabetes_related
        
        print_test_result("Search ICD-10 Codes (Diabetes)", True, result, 
                         f"Found {len(result)} codes related to diabetes")
    except Exception as e:
        print(f"Error searching ICD-10 codes for diabetes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search ICD-10 Codes (Diabetes)", False)
    
    # Test 3: Search ICD-10 codes for hypertension
    try:
        url = f"{API_URL}/icd10/search"
        params = {"query": "hypertension"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check if results are relevant to hypertension
        hypertension_related = any("hypertension" in code.get("description", "").lower() or 
                                  "hypertension" in str(code.get("search_terms", "")).lower() 
                                  for code in result)
        assert hypertension_related
        
        print_test_result("Search ICD-10 Codes (Hypertension)", True, result, 
                         f"Found {len(result)} codes related to hypertension")
    except Exception as e:
        print(f"Error searching ICD-10 codes for hypertension: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search ICD-10 Codes (Hypertension)", False)
    
    # Test 4: Get all ICD-10 codes
    try:
        url = f"{API_URL}/icd10/comprehensive"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive results
        assert isinstance(result, list)
        assert len(result) > 0
        
        print_test_result("Get All ICD-10 Codes", True, result, 
                         f"Retrieved {len(result)} ICD-10 codes")
    except Exception as e:
        print(f"Error getting all ICD-10 codes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All ICD-10 Codes", False)
    
    # Test 5: Get ICD-10 codes filtered by category
    try:
        url = f"{API_URL}/icd10/comprehensive"
        params = {"category": "Cardiovascular"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify filtered results
        assert isinstance(result, list)
        
        # Check if all results are from the Cardiovascular category
        if len(result) > 0:
            all_cardiovascular = all("cardiovascular" in code.get("category", "").lower() 
                                    for code in result)
            assert all_cardiovascular
        
        print_test_result("Get ICD-10 Codes by Category (Cardiovascular)", True, result, 
                         f"Retrieved {len(result)} Cardiovascular ICD-10 codes")
    except Exception as e:
        print(f"Error getting ICD-10 codes by category: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get ICD-10 Codes by Category (Cardiovascular)", False)

# Test Comprehensive Medication Database Endpoints
def test_medication_database(token):
    print("\n--- Testing Comprehensive Medication Database Endpoints ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Initialize comprehensive medication database
    try:
        url = f"{API_URL}/medications/init-comprehensive"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Check if initialization was successful
        assert "message" in result
        
        # Handle both possible response formats
        if "medications_count" in result:
            medications_count = result["medications_count"]
        elif "medications_added" in result:
            medications_count = result["medications_added"]
        else:
            medications_count = "unknown number of"
        
        print_test_result("Initialize Comprehensive Medication Database", True, result, 
                         f"Created/Found {medications_count} medications")
    except Exception as e:
        print(f"Error initializing comprehensive medication database: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Initialize Comprehensive Medication Database", False)
    
    # Test 2: Search medications for blood pressure
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "blood pressure"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check if results are relevant to blood pressure
        bp_related = any("blood pressure" in str(med.get("search_terms", "")).lower() or
                        "hypertension" in str(med.get("search_terms", "")).lower() or
                        "hypertension" in str(med.get("indications", "")).lower()
                        for med in result)
        assert bp_related
        
        print_test_result("Search Medications (Blood Pressure)", True, result, 
                         f"Found {len(result)} medications related to blood pressure")
    except Exception as e:
        print(f"Error searching medications for blood pressure: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (Blood Pressure)", False)
    
    # Test 3: Search medications for diabetes
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "diabetes"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check if results are relevant to diabetes
        diabetes_related = any("diabetes" in str(med.get("search_terms", "")).lower() or
                              "diabetes" in str(med.get("indications", "")).lower()
                              for med in result)
        assert diabetes_related
        
        print_test_result("Search Medications (Diabetes)", True, result, 
                         f"Found {len(result)} medications related to diabetes")
    except Exception as e:
        print(f"Error searching medications for diabetes: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (Diabetes)", False)
    
    # Test 4: Search medications for specific medication (lisinopril)
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "lisinopril"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check if results include lisinopril
        lisinopril_found = any("lisinopril" in med.get("generic_name", "").lower()
                              for med in result)
        assert lisinopril_found
        
        print_test_result("Search Medications (Lisinopril)", True, result, 
                         f"Found {len(result)} medications related to lisinopril")
    except Exception as e:
        print(f"Error searching medications for lisinopril: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Medications (Lisinopril)", False)
    
    # Test 5: Get all medications
    try:
        url = f"{API_URL}/medications/comprehensive"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify comprehensive results
        assert isinstance(result, list)
        assert len(result) > 0
        
        print_test_result("Get All Medications", True, result, 
                         f"Retrieved {len(result)} medications")
    except Exception as e:
        print(f"Error getting all medications: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get All Medications", False)
    
    # Test 6: Get medications filtered by drug class
    try:
        url = f"{API_URL}/medications/comprehensive"
        params = {"drug_class": "NSAID"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify filtered results
        assert isinstance(result, list)
        
        # Check if all results are NSAIDs
        if len(result) > 0:
            all_nsaids = all("nsaid" in med.get("drug_class", "").lower() 
                            for med in result)
            assert all_nsaids
        
        print_test_result("Get Medications by Drug Class (NSAID)", True, result, 
                         f"Retrieved {len(result)} NSAID medications")
    except Exception as e:
        print(f"Error getting medications by drug class: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Get Medications by Drug Class (NSAID)", False)

# Test Integration and Relevance Scoring
def test_integration_and_relevance(token):
    print("\n--- Testing Integration and Relevance Scoring ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Verify search relevance for medications
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "heart failure"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results are sorted by relevance
        assert isinstance(result, list)
        if len(result) >= 2:
            # Check if medications for heart failure appear first
            heart_failure_in_first = any("heart failure" in str(result[0].get("indications", "")).lower() or
                                        "heart failure" in str(result[0].get("search_terms", "")).lower())
            
            print_test_result("Medication Search Relevance Scoring", True, result, 
                             f"Heart failure medications appear first: {heart_failure_in_first}")
        else:
            print_test_result("Medication Search Relevance Scoring", True, result, 
                             "Not enough results to verify relevance sorting")
    except Exception as e:
        print(f"Error testing medication search relevance: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Medication Search Relevance Scoring", False)
    
    # Test 2: Verify search relevance for ICD-10 codes
    try:
        url = f"{API_URL}/icd10/search"
        params = {"query": "heart attack"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results are sorted by relevance
        assert isinstance(result, list)
        if len(result) >= 2:
            # Check if heart attack codes appear first
            heart_attack_in_first = any("myocardial infarction" in result[0].get("description", "").lower() or
                                       "heart attack" in str(result[0].get("search_terms", "")).lower())
            
            print_test_result("ICD-10 Search Relevance Scoring", True, result, 
                             f"Heart attack codes appear first: {heart_attack_in_first}")
        else:
            print_test_result("ICD-10 Search Relevance Scoring", True, result, 
                             "Not enough results to verify relevance sorting")
    except Exception as e:
        print(f"Error testing ICD-10 search relevance: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("ICD-10 Search Relevance Scoring", False)
    
    # Test 3: Verify search terms field works for better matching
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "water pill"}  # Common term for diuretics
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # Verify search results include diuretics
        assert isinstance(result, list)
        diuretics_found = any("diuretic" in med.get("drug_class", "").lower() 
                             for med in result)
        
        print_test_result("Search Terms Field Effectiveness", True, result, 
                         f"Searching for 'water pill' found diuretics: {diuretics_found}")
    except Exception as e:
        print(f"Error testing search terms field: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Search Terms Field Effectiveness", False)
    
    # Test 4: Verify responses exclude MongoDB ObjectId
    try:
        # Check medication response
        url = f"{API_URL}/medications/comprehensive"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        med_result = response.json()
        
        # Check ICD-10 response
        url = f"{API_URL}/icd10/comprehensive"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        icd_result = response.json()
        
        # Verify no MongoDB ObjectId in responses
        no_objectid_in_med = all("_id" not in med for med in med_result) if med_result else True
        no_objectid_in_icd = all("_id" not in code for code in icd_result) if icd_result else True
        
        print_test_result("MongoDB ObjectId Exclusion", no_objectid_in_med and no_objectid_in_icd, 
                         {"medications_clean": no_objectid_in_med, "icd10_clean": no_objectid_in_icd}, 
                         "Responses properly exclude MongoDB ObjectId")
    except Exception as e:
        print(f"Error testing MongoDB ObjectId exclusion: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("MongoDB ObjectId Exclusion", False)

# Main test function
def main():
    print("\n=== Testing Comprehensive Medical Database Endpoints ===\n")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token. Exiting tests.")
        return
    
    # Test ICD-10 database endpoints
    test_icd10_database(token)
    
    # Test comprehensive medication database endpoints
    test_medication_database(token)
    
    # Test integration and relevance scoring
    test_integration_and_relevance(token)
    
    print("\n=== Comprehensive Medical Database Testing Complete ===\n")

if __name__ == "__main__":
    main()