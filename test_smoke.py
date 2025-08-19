#!/usr/bin/env python3
"""
Smoke test for the payroll system end-to-end flow
"""
import requests
import json
import sys
import os

BASE_URL = "http://localhost:8001/api"

def test_payroll_flow():
    print("🔥 Starting Payroll Smoke Test")
    
    # Create a test user/token manually by directly accessing database
    # For simplicity, we'll create a fake JWT token
    import jwt
    from datetime import datetime, timedelta
    
    # Use the same secret as in the server
    JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key-change-immediately')
    
    # Create a test token
    payload = {
        'sub': 'test_user',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 1) Tax configuration
        print("📋 Setting up tax configuration...")
        tax_config = {
            "jurisdiction": "US-FED",
            "effective_date": "2025-01-01",
            "standard_deduction": 0,
            "components": [
                {
                    "type": "brackets",
                    "base": "taxable",
                    "brackets": [
                        {"up_to": 11000, "rate": 0.10},
                        {"up_to": 44725, "rate": 0.12},
                        {"up_to": None, "rate": 0.22}
                    ]
                },
                {
                    "type": "flat_capped",
                    "name": "social_security",
                    "base": "gross",
                    "rate": 0.062,
                    "cap": 168600
                },
                {
                    "type": "flat",
                    "name": "medicare",
                    "base": "gross",
                    "rate": 0.0145
                }
            ]
        }
        
        response = requests.put(f"{BASE_URL}/payroll/config/tax", headers=headers, json=tax_config)
        if response.status_code not in [200, 201]:
            print(f"❌ Tax config failed: {response.status_code} - {response.text}")
            return False
        print("✅ Tax configuration set up")
        
        # 2) ACH configuration
        print("🏦 Setting up ACH configuration...")
        ach_config = {
            "immediate_destination": "111000025",
            "immediate_destination_name": "BANK NAME",
            "immediate_origin": "1234567890",
            "immediate_origin_name": "CLINIC HUB LLC",
            "originating_dfi_identification": "11100002",
            "company_id": "1234567890",
            "company_name": "Clínica Familia y Salud",
            "entry_description": "PAYROLL"
        }
        
        response = requests.put(f"{BASE_URL}/payroll/config/ach", headers=headers, json=ach_config)
        if response.status_code not in [200, 201]:
            print(f"❌ ACH config failed: {response.status_code} - {response.text}")
            return False
        print("✅ ACH configuration set up")
        
        # 3) Employee bank info
        print("💳 Setting up employee bank info...")
        bank_info = {
            "name": "Jane Doe",
            "routing_number": "111000025", 
            "account_number": "000123456789",
            "account_type": "checking"
        }
        
        response = requests.put(f"{BASE_URL}/payroll/employees/E1/bank", headers=headers, json=bank_info)
        if response.status_code not in [200, 201]:
            print(f"❌ Bank info failed: {response.status_code} - {response.text}")
            return False
        print("✅ Employee bank information set up")
        
        # 4) Create pay period
        print("📅 Creating pay period...")
        period_data = {
            "start_date": "2025-08-01",
            "end_date": "2025-08-15", 
            "frequency": "semimonthly"
        }
        
        response = requests.post(f"{BASE_URL}/payroll/periods", headers=headers, json=period_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Period creation failed: {response.status_code} - {response.text}")
            return False
        
        period_response = response.json()
        period_id = period_response.get('_id')
        print(f"✅ Pay period created: {period_id}")
        
        # 5) Create payroll run
        print("▶️ Creating payroll run...")
        run_data = {"period_id": period_id}
        
        response = requests.post(f"{BASE_URL}/payroll/runs", headers=headers, json=run_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Run creation failed: {response.status_code} - {response.text}")
            return False
        
        run_response = response.json()
        run_id = run_response.get('_id')
        print(f"✅ Payroll run created: {run_id}")
        
        # 6) Seed payroll records (test-only endpoint)
        print("🌱 Seeding payroll records...")
        seed_data = {
            "period_id": period_id,
            "records": [
                {
                    "employee_id": "E1",
                    "employee_name": "Jane Doe",
                    "record_id": "PR-1001",
                    "gross": 1200,
                    "pretax_deductions": 0,
                    "posttax_deductions": 100
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/payroll/_test/seed/payroll_records", headers=headers, json=seed_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Seeding failed: {response.status_code} - {response.text}")
            return False
        print("✅ Payroll records seeded")
        
        # 7) Post run (applies taxes using async hook)
        print("📝 Posting payroll run...")
        response = requests.post(f"{BASE_URL}/payroll/runs/{run_id}/post", headers=headers)
        if response.status_code not in [200, 201]:
            print(f"❌ Run posting failed: {response.status_code} - {response.text}")
            return False
        
        post_response = response.json()
        print(f"✅ Payroll run posted: {json.dumps(post_response, indent=2)}")
        
        # 8) Test exports
        print("📊 Testing CSV export...")
        response = requests.get(f"{BASE_URL}/payroll/runs/{run_id}/paystubs.csv", headers=headers)
        if response.status_code == 200:
            with open("paystubs.csv", "w") as f:
                f.write(response.text)
            print("✅ CSV export successful")
        else:
            print(f"❌ CSV export failed: {response.status_code}")
        
        print("📄 Testing ACH export...")
        response = requests.get(f"{BASE_URL}/payroll/runs/{run_id}/ach?mode=test", headers=headers)
        if response.status_code == 200:
            with open("payroll_test.ach", "w") as f:
                f.write(response.text)
            print("✅ ACH export successful")
        else:
            print(f"❌ ACH export failed: {response.status_code}")
        
        print("📑 Testing PDF export...")
        response = requests.get(f"{BASE_URL}/payroll/runs/{run_id}/paystubs?format=pdf", headers=headers)
        if response.status_code == 200:
            with open("paystubs.pdf", "wb") as f:
                f.write(response.content)
            print("✅ PDF export successful")
        else:
            print(f"❌ PDF export failed: {response.status_code}")
        
        print("\n🎉 Payroll smoke test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    # Set environment for test routes
    os.environ["ENV"] = "TEST"
    
    success = test_payroll_flow()
    sys.exit(0 if success else 1)