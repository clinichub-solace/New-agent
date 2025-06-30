#!/usr/bin/env python3
import requests
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

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test GET /api/patients
try:
    print("\nTesting GET /api/patients")
    response = requests.get(f"{API_URL}/patients")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test POST /api/patients
try:
    print("\nTesting POST /api/patients")
    data = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": "test@example.com",
        "phone": "555-1234",
        "gender": "male"
    }
    response = requests.post(f"{API_URL}/patients", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")