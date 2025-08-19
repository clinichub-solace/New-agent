#!/usr/bin/env python3
"""
Debug payroll authentication issues
"""

import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

print(f"Using API URL: {API_URL}")

# Step 1: Login
login_response = requests.post(f"{API_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})

print(f"Login status: {login_response.status_code}")
print(f"Login response: {login_response.text}")

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Token: {token[:50]}...")
    
    # Test different header formats
    headers_formats = [
        {"Authorization": f"Bearer {token}"},
        {"Authorization": f"bearer {token}"},
        {"authorization": f"Bearer {token}"},
    ]
    
    for i, headers in enumerate(headers_formats):
        print(f"\n--- Testing header format {i+1}: {headers} ---")
        
        # Test payroll periods endpoint
        response = requests.get(f"{API_URL}/payroll/periods", headers=headers)
        print(f"GET /payroll/periods - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            print("Success!")
            
        # Test payroll config endpoint
        response = requests.put(f"{API_URL}/payroll/config/tax", 
                              json={"federal_tax_rate": 0.22}, 
                              headers=headers)
        print(f"PUT /payroll/config/tax - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            print("Success!")