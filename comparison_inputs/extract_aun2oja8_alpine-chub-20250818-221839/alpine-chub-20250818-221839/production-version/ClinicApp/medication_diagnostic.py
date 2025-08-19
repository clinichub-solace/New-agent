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

# Get authentication token
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

# Diagnostic function to check MongoDB collections
def check_mongodb_collections(token):
    print("\n--- Checking MongoDB Collections ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Use a diagnostic endpoint to check collections
        url = f"{API_URL}/diagnostic/collections"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            print("Diagnostic endpoint not available. Creating one...")
            # We'll need to manually check collections
            print("Checking collections through initialization endpoints...")
            
            # Check ICD-10 collection
            url = f"{API_URL}/icd10/init"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            icd10_result = response.json()
            print(f"ICD-10 collection: {icd10_result}")
            
            # Check comprehensive medications collection
            url = f"{API_URL}/medications/init-comprehensive"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            meds_result = response.json()
            print(f"Comprehensive medications collection: {meds_result}")
            
            print_test_result("Check Collections", True, 
                             {"icd10": icd10_result, "medications": meds_result},
                             "Checked collections through initialization endpoints")
        else:
            response.raise_for_status()
            result = response.json()
            print_test_result("Check Collections", True, result)
            
    except Exception as e:
        print(f"Error checking MongoDB collections: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Check Collections", False)

# Test medication search endpoint with detailed error handling
def test_medication_search_detailed(token):
    print("\n--- Testing Medication Search with Detailed Error Handling ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        url = f"{API_URL}/medications/search"
        params = {"query": "blood pressure"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_json = response.json()
                if "detail" in error_json:
                    error_detail = error_json["detail"]
            except:
                error_detail = response.text
                
            print(f"Error response: {error_detail}")
            
            # Check if it's a 404 medication not found error
            if "404: Medication not found" in error_detail:
                print("Detected 404 Medication not found error. This suggests the collection name might be incorrect.")
                print("The endpoint is trying to access a medication that doesn't exist or using the wrong collection.")
            
            print_test_result("Medication Search Detailed", False, 
                             {"status_code": response.status_code, "error": error_detail},
                             "Failed with error")
        else:
            result = response.json()
            print_test_result("Medication Search Detailed", True, result,
                             f"Found {len(result)} medications")
    except Exception as e:
        print(f"Error in detailed medication search: {str(e)}")
        if 'response' in locals():
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
        print_test_result("Medication Search Detailed", False)

# Main function
def main():
    print("\n=== Medication Database Diagnostic Tool ===\n")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token. Exiting tests.")
        return
    
    # Check MongoDB collections
    check_mongodb_collections(token)
    
    # Test medication search with detailed error handling
    test_medication_search_detailed(token)
    
    print("\n=== Diagnostic Testing Complete ===\n")

if __name__ == "__main__":
    main()