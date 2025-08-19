#!/usr/bin/env python3
"""
Focused UPDATE Operations Testing - Identify specific issues with CRUD operations
"""
import requests
import json
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

def get_auth_token():
    """Get authentication token"""
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result["access_token"]
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_inventory_update_detailed():
    """Test inventory update with detailed error analysis"""
    print("\n🔍 DETAILED INVENTORY UPDATE TESTING")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create an item
    try:
        url = f"{API_URL}/inventory"
        data = {
            "name": "Test Medicine",
            "category": "Medications",
            "current_stock": 100,
            "min_stock_level": 10,
            "unit_cost": 5.00
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        item_id = result["id"]
        print(f"✅ Created inventory item: {item_id}")
        
        # Now try to update it
        url = f"{API_URL}/inventory/{item_id}"
        update_data = {
            "name": "Updated Test Medicine",
            "current_stock": 150,
            "unit_cost": 6.00
        }
        response = requests.put(url, json=update_data, headers=headers)
        print(f"Update response status: {response.status_code}")
        print(f"Update response text: {response.text}")
        
        if response.status_code == 422:
            try:
                error_detail = response.json()
                print(f"Validation error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Inventory update test failed: {e}")

def test_patient_update_detailed():
    """Test patient update with detailed error analysis"""
    print("\n🔍 DETAILED PATIENT UPDATE TESTING")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a patient
    try:
        url = f"{API_URL}/patients"
        data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test@example.com",
            "phone": "+1-555-123-4567"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        patient_id = result["id"]
        print(f"✅ Created patient: {patient_id}")
        
        # Check if PUT endpoint exists
        url = f"{API_URL}/patients/{patient_id}"
        update_data = {
            "first_name": "Updated Test",
            "last_name": "Updated Patient",
            "email": "updated@example.com"
        }
        response = requests.put(url, json=update_data, headers=headers)
        print(f"Update response status: {response.status_code}")
        print(f"Update response text: {response.text}")
        
        if response.status_code == 405:
            print("❌ PUT method not allowed - UPDATE endpoint not implemented")
        elif response.status_code == 422:
            try:
                error_detail = response.json()
                print(f"Validation error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Patient update test failed: {e}")

def test_employee_update_detailed():
    """Test employee update with detailed error analysis"""
    print("\n🔍 DETAILED EMPLOYEE UPDATE TESTING")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing employee
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        employees = response.json()
        
        if employees:
            employee_id = employees[0]["id"]
            print(f"✅ Using existing employee: {employee_id}")
            
            # Try to update
            url = f"{API_URL}/employees/{employee_id}"
            update_data = {
                "first_name": "Updated Name",
                "phone": "+1-555-999-8888"
            }
            response = requests.put(url, json=update_data, headers=headers)
            print(f"Update response status: {response.status_code}")
            print(f"Update response text: {response.text}")
            
            if response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"Validation error details: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
        else:
            print("❌ No employees found to test update")
                
    except Exception as e:
        print(f"❌ Employee update test failed: {e}")

def test_invoice_update_detailed():
    """Test invoice update with detailed error analysis"""
    print("\n🔍 DETAILED INVOICE UPDATE TESTING")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing invoice
    try:
        url = f"{API_URL}/invoices"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        invoices = response.json()
        
        if invoices:
            invoice_id = invoices[0]["id"]
            print(f"✅ Using existing invoice: {invoice_id}")
            
            # Try to update
            url = f"{API_URL}/invoices/{invoice_id}"
            update_data = {
                "notes": "Updated invoice notes"
            }
            response = requests.put(url, json=update_data, headers=headers)
            print(f"Update response status: {response.status_code}")
            print(f"Update response text: {response.text}")
            
            if response.status_code == 405:
                print("❌ PUT method not allowed - UPDATE endpoint not implemented")
        else:
            print("❌ No invoices found to test update")
                
    except Exception as e:
        print(f"❌ Invoice update test failed: {e}")

def check_available_endpoints():
    """Check what endpoints are actually available"""
    print("\n🔍 CHECKING AVAILABLE ENDPOINTS")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check API documentation
    try:
        url = f"{BACKEND_URL}/docs"
        response = requests.get(url)
        print(f"API docs available at: {url} (Status: {response.status_code})")
    except Exception as e:
        print(f"API docs check failed: {e}")

if __name__ == "__main__":
    print("🔍 FOCUSED UPDATE OPERATIONS TESTING")
    print("=" * 60)
    
    check_available_endpoints()
    test_inventory_update_detailed()
    test_patient_update_detailed()
    test_employee_update_detailed()
    test_invoice_update_detailed()
    
    print("\n" + "=" * 60)
    print("🏁 FOCUSED TESTING COMPLETED")