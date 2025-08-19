import os
import pytest
from fastapi.testclient import TestClient
from backend.server import app
from backend.dependencies import get_db, get_current_active_user
import mongomock

class FakeUser: 
    def __init__(self):
        self.id = "u_test"
        self.username = "test_user"

@pytest.fixture(scope="function")
def client():
    os.environ["ENV"] = "TEST"
    db = mongomock.MongoClient()["clinichub_test"]
    def _get_db(): return db
    def _user(): return FakeUser()
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_active_user] = _user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_bank_csv_ach_flow(client):
    """Test the complete bank info, CSV export, and ACH flow"""
    # Tax config
    client.put("/api/payroll/config/tax", json={
        "jurisdiction":"US-FED","effective_date":"2025-01-01","standard_deduction":0,
        "components":[{"type":"flat","name":"medicare","base":"gross","rate":0.01}]
    })
    
    # ACH config
    client.put("/api/payroll/config/ach", json={
        "immediate_destination":"111000025","immediate_destination_name":"BANK",
        "immediate_origin":"1234567890","immediate_origin_name":"CLINIC",
        "originating_dfi_identification":"11100002","company_id":"1234567890",
        "company_name":"Clinic","entry_description":"PAYROLL"
    })
    
    # Employee bank info
    bank_response = client.put("/api/payroll/employees/E1/bank", json={
        "name":"Jane","routing_number":"111000025","account_number":"000123456789","account_type":"checking"
    })
    assert bank_response.status_code == 200
    
    # Create period and run
    period_response = client.post("/api/payroll/periods", json={
        "start_date":"2025-08-01","end_date":"2025-08-15","frequency":"semimonthly"
    })
    assert period_response.status_code == 200
    period_data = period_response.json()
    
    run_response = client.post("/api/payroll/runs", json={"period_id": period_data["_id"]})
    assert run_response.status_code == 200
    run_data = run_response.json()
    
    # Seed test records
    seed_response = client.post("/api/payroll/_test/seed/payroll_records", json={
        "period_id": period_data["_id"],
        "records":[{"employee_id":"E1","employee_name":"Jane","record_id":"PR-1","gross":1000,"posttax_deductions":100}]
    })
    assert seed_response.status_code == 200
    
    # Post run (applies taxes)
    post_response = client.post(f"/api/payroll/runs/{run_data['_id']}/post")
    assert post_response.status_code == 200
    
    # Test CSV export
    csv_response = client.get(f"/api/payroll/runs/{run_data['_id']}/paystubs.csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers.get("content-type","")
    
    # Test ACH export
    ach_response = client.get(f"/api/payroll/runs/{run_data['_id']}/ach", params={"mode":"test"})
    assert ach_response.status_code == 200
    assert "text/plain" in ach_response.headers.get("content-type","")
    
    # Test PDF export
    pdf_response = client.get(f"/api/payroll/runs/{run_data['_id']}/paystubs?format=pdf")
    assert pdf_response.status_code == 200
    assert "application/pdf" in pdf_response.headers.get("content-type","")

def test_employee_bank_info_endpoints(client):
    """Test employee bank information endpoints"""
    employee_id = "TEST_EMP_001"
    
    # Test PUT bank info
    bank_data = {
        "name": "Test Employee",
        "routing_number": "111000025",
        "account_number": "000123456789",
        "account_type": "checking"
    }
    
    put_response = client.put(f"/api/payroll/employees/{employee_id}/bank", json=bank_data)
    assert put_response.status_code == 200
    put_result = put_response.json()
    
    # Verify masked account number in response
    assert "account_number" in put_result
    assert put_result["account_number"].startswith("****")
    
    # Test GET bank info
    get_response = client.get(f"/api/payroll/employees/{employee_id}/bank")
    assert get_response.status_code == 200
    get_result = get_response.json()
    
    # Verify masked account number
    assert "account_number" in get_result
    assert get_result["account_number"].startswith("****")
    assert get_result["name"] == bank_data["name"]
    assert get_result["routing_number"] == bank_data["routing_number"]

def test_payroll_run_exports(client):
    """Test all payroll run export formats"""
    # Setup minimal test data
    client.put("/api/payroll/config/tax", json={
        "jurisdiction":"US-FED","effective_date":"2025-01-01","standard_deduction":0,
        "components":[{"type":"flat","name":"test","base":"gross","rate":0.05}]
    })
    
    # Create period and run
    period_response = client.post("/api/payroll/periods", json={
        "start_date":"2025-08-01","end_date":"2025-08-15","frequency":"semimonthly"
    })
    period_data = period_response.json()
    
    run_response = client.post("/api/payroll/runs", json={"period_id": period_data["_id"]})
    run_data = run_response.json()
    
    # Seed and post run
    client.post("/api/payroll/_test/seed/payroll_records", json={
        "period_id": period_data["_id"],
        "records":[{"employee_id":"E1","employee_name":"Jane","record_id":"PR-1","gross":1000}]
    })
    client.post(f"/api/payroll/runs/{run_data['_id']}/post")
    
    # Test CSV export with proper content-type
    csv_response = client.get(f"/api/payroll/runs/{run_data['_id']}/paystubs.csv")
    assert csv_response.status_code == 200
    assert "csv" in csv_response.headers.get("content-type", "").lower()
    assert "Employee ID" in csv_response.text  # Check for CSV header
    
    # Test ACH export
    ach_response = client.get(f"/api/payroll/runs/{run_data['_id']}/ach", params={"mode": "test"})
    assert ach_response.status_code == 200
    assert len(ach_response.text) > 0  # Should have ACH content
    
    # Test PDF export
    pdf_response = client.get(f"/api/payroll/runs/{run_data['_id']}/paystubs?format=pdf")
    assert pdf_response.status_code == 200
    assert "pdf" in pdf_response.headers.get("content-type", "").lower()
    
    # Test JSON export (default)
    json_response = client.get(f"/api/payroll/runs/{run_data['_id']}/paystubs")
    assert json_response.status_code == 200
    json_data = json_response.json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0