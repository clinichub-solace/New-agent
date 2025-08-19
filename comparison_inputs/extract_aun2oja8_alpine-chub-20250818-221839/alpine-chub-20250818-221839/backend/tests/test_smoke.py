# app/backend/tests/test_smoke.py
from fastapi.testclient import TestClient
from ..server import app

client = TestClient(app)

def test_receipts_list():
    r = client.get("/api/receipts")
    assert r.status_code == 200

def test_receipt_get():
    r = client.get("/api/receipts/abc")
    assert r.status_code in (200, 404)

def test_create_from_soap():
    r = client.post("/api/receipts/soap-note/xyz")
    assert r.status_code == 200

def test_clock_in_out_and_status():
    assert client.post("/api/employees/1/clock-in").status_code == 200
    assert client.get("/api/employees/1/time-status").status_code == 200
    assert client.post("/api/employees/1/clock-out").status_code == 200
    assert client.get("/api/employees/1/time-entries/today").status_code == 200