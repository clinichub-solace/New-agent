#!/usr/bin/env python3
"""
ClinicHub Comprehensive Backend Testing
Testing all major backend endpoints as requested in the review
"""

import requests
import json
import sys
from datetime import datetime, date
import time
import os

# Configuration - Use production URL from frontend/.env
BACKEND_URL = "https://medical-practice-hub.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class ClinicHubTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.test_data = {}  # Store created test data for cross-test usage
        
    def log_result(self, test_name, success, message, details=None, status_code=None, payload=None):
        """Log test result with enhanced details"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        if status_code:
            print(f"   Status Code: {status_code}")
        if payload and isinstance(payload, dict):
            print(f"   Sample Payload: {json.dumps(payload, indent=2, default=str)[:200]}...")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "status_code": status_code,
            "payload": payload
        })
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}", 
                              status_code=response.status_code, payload={"username": ADMIN_USERNAME})
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_authentication_endpoints(self):
        """Test all authentication endpoints (/api/auth/*)"""
        print("\n🔐 TESTING AUTHENTICATION ENDPOINTS")
        print("=" * 50)
        
        # Test 1: Health check
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log_result("GET /api/health", True, "Backend health check passed", 
                              status_code=response.status_code, payload=health_data)
            else:
                self.log_result("GET /api/health", False, f"Health check failed: {response.status_code}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/health", False, f"Error: {str(e)}")
        
        # Test 2: Login endpoint (already tested in authenticate)
        self.log_result("POST /api/auth/login", True, "Login functionality verified during authentication")
        
        # Test 3: Get current user info
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            if response.status_code == 200:
                user_data = response.json()
                self.log_result("GET /api/auth/me", True, f"Retrieved user info for {user_data.get('username')}", 
                              status_code=response.status_code, payload=user_data)
            else:
                self.log_result("GET /api/auth/me", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/auth/me", False, f"Error: {str(e)}")
        
        # Test 4: Synology status
        try:
            response = self.session.get(f"{API_BASE}/auth/synology-status")
            if response.status_code == 200:
                synology_data = response.json()
                self.log_result("GET /api/auth/synology-status", True, f"Synology integration status retrieved", 
                              status_code=response.status_code, payload=synology_data)
            else:
                self.log_result("GET /api/auth/synology-status", False, f"Failed: {response.status_code}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/auth/synology-status", False, f"Error: {str(e)}")

    def test_patients_crud_ehr(self):
        """Test Patients CRUD + EHR flows (encounters, vital signs, SOAP notes)"""
        print("\n👥 TESTING PATIENTS CRUD + EHR FLOWS")
        print("=" * 50)
        
        # Test 1: Create Patient
        patient_data = {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@email.com",
            "phone": "555-0789",
            "date_of_birth": "1990-05-20",
            "gender": "female",
            "address_line1": "456 Oak Avenue",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78702"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            if response.status_code == 200:
                patient = response.json()
                patient_id = patient.get("id")
                self.test_data["patient_id"] = patient_id
                self.log_result("POST /api/patients", True, f"Created patient Emily Rodriguez with ID: {patient_id}", 
                              status_code=response.status_code, payload=patient)
            else:
                self.log_result("POST /api/patients", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
        except Exception as e:
            self.log_result("POST /api/patients", False, f"Error: {str(e)}")
            return False
        
        # Test 2: Get All Patients
        try:
            response = self.session.get(f"{API_BASE}/patients")
            if response.status_code == 200:
                patients = response.json()
                self.log_result("GET /api/patients", True, f"Retrieved {len(patients)} patients", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/patients", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/patients", False, f"Error: {str(e)}")
        
        # Test 3: Get Specific Patient
        if self.test_data.get("patient_id"):
            try:
                response = self.session.get(f"{API_BASE}/patients/{self.test_data['patient_id']}")
                if response.status_code == 200:
                    patient = response.json()
                    self.log_result("GET /api/patients/{id}", True, f"Retrieved patient: {patient.get('name', [{}])[0].get('given', [''])[0]} {patient.get('name', [{}])[0].get('family', '')}", 
                                  status_code=response.status_code, payload=patient)
                else:
                    self.log_result("GET /api/patients/{id}", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET /api/patients/{id}", False, f"Error: {str(e)}")
        
        # Test 4: Create Encounter
        if self.test_data.get("patient_id"):
            encounter_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_type": "consultation",
                "status": "completed",
                "reason": "Annual wellness visit",
                "provider": "Dr. Jennifer Martinez"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/encounters", json=encounter_data)
                if response.status_code == 200:
                    encounter = response.json()
                    encounter_id = encounter.get("id")
                    self.test_data["encounter_id"] = encounter_id
                    self.log_result("POST /api/encounters", True, f"Created encounter with ID: {encounter_id}", 
                                  status_code=response.status_code, payload=encounter)
                else:
                    self.log_result("POST /api/encounters", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/encounters", False, f"Error: {str(e)}")
        
        # Test 5: Create Vital Signs
        if self.test_data.get("patient_id"):
            vital_signs_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_id": self.test_data.get("encounter_id"),
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "temperature": 98.6,
                "respiratory_rate": 16,
                "oxygen_saturation": 98,
                "weight": 150.0,
                "height": 65.0,
                "pain_scale": 2,
                "notes": "Patient reports feeling well"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/vital-signs", json=vital_signs_data)
                if response.status_code == 200:
                    vital_signs = response.json()
                    vital_signs_id = vital_signs.get("id")
                    self.test_data["vital_signs_id"] = vital_signs_id
                    self.log_result("POST /api/vital-signs", True, f"Created vital signs with ID: {vital_signs_id}", 
                                  status_code=response.status_code, payload=vital_signs)
                else:
                    self.log_result("POST /api/vital-signs", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/vital-signs", False, f"Error: {str(e)}")
        
        # Test 6: Create SOAP Note
        if self.test_data.get("patient_id"):
            soap_data = {
                "patient_id": self.test_data["patient_id"],
                "encounter_id": self.test_data.get("encounter_id"),
                "subjective": "Patient reports feeling well overall. No acute complaints. Sleeping well, good appetite.",
                "objective": "Vital signs stable. Physical exam unremarkable. Alert and oriented x3.",
                "assessment": "Healthy adult, annual wellness visit. No acute issues identified.",
                "plan": "Continue current health maintenance. Return in 1 year for annual check. Discussed preventive care.",
                "provider": "Dr. Jennifer Martinez"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/soap-notes", json=soap_data)
                if response.status_code == 200:
                    soap_note = response.json()
                    soap_id = soap_note.get("id")
                    self.test_data["soap_id"] = soap_id
                    self.log_result("POST /api/soap-notes", True, f"Created SOAP note with ID: {soap_id}", 
                                  status_code=response.status_code, payload=soap_note)
                else:
                    self.log_result("POST /api/soap-notes", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/soap-notes", False, f"Error: {str(e)}")
        
        return True
    
    def test_receipts_api(self):
        """Test Receipts API (/api/receipts, /api/receipts/soap-note/{id})"""
        print("\n🧾 TESTING RECEIPTS API")
        print("=" * 50)
        
        # Test 1: Get All Receipts
        try:
            response = self.session.get(f"{API_BASE}/receipts")
            if response.status_code == 200:
                receipts = response.json()
                self.log_result("GET /api/receipts", True, f"Retrieved {len(receipts)} receipts", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/receipts", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/receipts", False, f"Error: {str(e)}")
        
        # Test 2: Generate Receipt from SOAP Note
        if self.test_data.get("soap_id"):
            try:
                response = self.session.post(f"{API_BASE}/receipts/soap-note/{self.test_data['soap_id']}")
                if response.status_code == 200:
                    result = response.json()
                    receipt_id = result.get("receipt", {}).get("id")
                    receipt_number = result.get("receipt", {}).get("receipt_number")
                    self.test_data["receipt_id"] = receipt_id
                    self.log_result("POST /api/receipts/soap-note/{id}", True, 
                                  f"Generated receipt {receipt_number} with ID: {receipt_id}", 
                                  status_code=response.status_code, payload=result)
                else:
                    self.log_result("POST /api/receipts/soap-note/{id}", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/receipts/soap-note/{id}", False, f"Error: {str(e)}")
        
        # Test 3: Get Specific Receipt
        if self.test_data.get("receipt_id"):
            try:
                response = self.session.get(f"{API_BASE}/receipts/{self.test_data['receipt_id']}")
                if response.status_code == 200:
                    receipt = response.json()
                    patient_name = receipt.get("patient_name")
                    total = receipt.get("total")
                    self.log_result("GET /api/receipts/{id}", True, 
                                  f"Retrieved receipt for {patient_name}, total: ${total}", 
                                  status_code=response.status_code, payload=receipt)
                else:
                    self.log_result("GET /api/receipts/{id}", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET /api/receipts/{id}", False, f"Error: {str(e)}")

    def test_employee_time_tracking(self):
        """Test Employee time-tracking (/api/employees/*, clock-in/out, time-status, today entries)"""
        print("\n👨‍⚕️ TESTING EMPLOYEE TIME-TRACKING")
        print("=" * 50)
        
        # Test 1: Create Employee
        employee_data = {
            "first_name": "Michael",
            "last_name": "Davis",
            "email": "michael.davis@clinichub.com",
            "phone": "555-0456",
            "role": "nurse",
            "department": "Emergency",
            "hire_date": "2024-01-15",
            "hourly_rate": 35.00
        }
        
        try:
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee.get("id")
                self.test_data["employee_id"] = employee_id
                self.log_result("POST /api/employees", True, f"Created employee Michael Davis with ID: {employee_id}", 
                              status_code=response.status_code, payload=employee)
            else:
                self.log_result("POST /api/employees", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
        except Exception as e:
            self.log_result("POST /api/employees", False, f"Error: {str(e)}")
            return False
        
        # Test 2: Get All Employees
        try:
            response = self.session.get(f"{API_BASE}/employees")
            if response.status_code == 200:
                employees = response.json()
                self.log_result("GET /api/employees", True, f"Retrieved {len(employees)} employees", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/employees", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/employees", False, f"Error: {str(e)}")
        
        # Test 3: Get Employee Time Status
        if self.test_data.get("employee_id"):
            try:
                response = self.session.get(f"{API_BASE}/employees/{self.test_data['employee_id']}/time-status")
                if response.status_code == 200:
                    status = response.json()
                    current_status = status.get("status")
                    self.log_result("GET /api/employees/{id}/time-status", True, 
                                  f"Employee status: {current_status}", 
                                  status_code=response.status_code, payload=status)
                else:
                    self.log_result("GET /api/employees/{id}/time-status", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET /api/employees/{id}/time-status", False, f"Error: {str(e)}")
        
        # Test 4: Clock In
        if self.test_data.get("employee_id"):
            try:
                response = self.session.post(f"{API_BASE}/employees/{self.test_data['employee_id']}/clock-in", 
                                           params={"location": "Emergency Department"})
                if response.status_code == 200:
                    result = response.json()
                    timestamp = result.get("timestamp")
                    location = result.get("location")
                    self.log_result("POST /api/employees/{id}/clock-in", True, 
                                  f"Clocked in at {location}, time: {timestamp}", 
                                  status_code=response.status_code, payload=result)
                else:
                    self.log_result("POST /api/employees/{id}/clock-in", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/employees/{id}/clock-in", False, f"Error: {str(e)}")
        
        # Wait a moment to simulate work time
        time.sleep(2)
        
        # Test 5: Clock Out
        if self.test_data.get("employee_id"):
            try:
                response = self.session.post(f"{API_BASE}/employees/{self.test_data['employee_id']}/clock-out")
                if response.status_code == 200:
                    result = response.json()
                    hours_worked = result.get("hours_worked")
                    total_shift_time = result.get("total_shift_time")
                    self.log_result("POST /api/employees/{id}/clock-out", True, 
                                  f"Clocked out, Hours: {hours_worked}, Shift: {total_shift_time}", 
                                  status_code=response.status_code, payload=result)
                else:
                    self.log_result("POST /api/employees/{id}/clock-out", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/employees/{id}/clock-out", False, f"Error: {str(e)}")
        
        # Test 6: Get Today's Time Entries
        if self.test_data.get("employee_id"):
            try:
                response = self.session.get(f"{API_BASE}/employees/{self.test_data['employee_id']}/time-entries/today")
                if response.status_code == 200:
                    result = response.json()
                    entries = result.get("entries", [])
                    total_hours = result.get("total_hours_today", 0)
                    date_str = result.get("date")
                    self.log_result("GET /api/employees/{id}/time-entries/today", True, 
                                  f"Retrieved {len(entries)} entries for {date_str}, Total hours: {total_hours}", 
                                  status_code=response.status_code, payload=result)
                else:
                    self.log_result("GET /api/employees/{id}/time-entries/today", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("GET /api/employees/{id}/time-entries/today", False, f"Error: {str(e)}")

    def test_inventory_management(self):
        """Test Inventory (/api/inventory, transactions)"""
        print("\n📦 TESTING INVENTORY MANAGEMENT")
        print("=" * 50)
        
        # Test 1: Create Inventory Item
        inventory_data = {
            "name": "Surgical Gloves",
            "category": "Medical Supplies",
            "sku": "SG-001",
            "current_stock": 500,
            "min_stock_level": 50,
            "unit_cost": 0.25,
            "supplier": "MedSupply Corp",
            "location": "Storage Room A",
            "notes": "Latex-free surgical gloves, size M"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/inventory", json=inventory_data)
            if response.status_code == 200:
                inventory_item = response.json()
                item_id = inventory_item.get("id")
                self.test_data["inventory_id"] = item_id
                self.log_result("POST /api/inventory", True, f"Created inventory item with ID: {item_id}", 
                              status_code=response.status_code, payload=inventory_item)
            else:
                self.log_result("POST /api/inventory", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
                return False
        except Exception as e:
            self.log_result("POST /api/inventory", False, f"Error: {str(e)}")
            return False
        
        # Test 2: Get All Inventory Items
        try:
            response = self.session.get(f"{API_BASE}/inventory")
            if response.status_code == 200:
                inventory_items = response.json()
                self.log_result("GET /api/inventory", True, f"Retrieved {len(inventory_items)} inventory items", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/inventory", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/inventory", False, f"Error: {str(e)}")
        
        # Test 3: Create Inventory Transaction
        if self.test_data.get("inventory_id"):
            transaction_data = {
                "transaction_type": "out",
                "quantity": 10,
                "reference_id": self.test_data.get("patient_id"),
                "notes": "Used for patient procedure",
                "created_by": "admin"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/inventory/{self.test_data['inventory_id']}/transactions", 
                                           json=transaction_data)
                if response.status_code == 200:
                    transaction = response.json()
                    transaction_id = transaction.get("id")
                    self.log_result("POST /api/inventory/{id}/transactions", True, 
                                  f"Created inventory transaction with ID: {transaction_id}", 
                                  status_code=response.status_code, payload=transaction)
                else:
                    self.log_result("POST /api/inventory/{id}/transactions", False, 
                                  f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/inventory/{id}/transactions", False, f"Error: {str(e)}")

    def test_invoices_finance(self):
        """Test Invoices & finance (/api/invoices, /api/financial-transactions)"""
        print("\n💰 TESTING INVOICES & FINANCE")
        print("=" * 50)
        
        # Test 1: Create Invoice
        if self.test_data.get("patient_id"):
            invoice_data = {
                "patient_id": self.test_data["patient_id"],
                "items": [
                    {
                        "description": "Annual Wellness Visit",
                        "quantity": 1,
                        "unit_price": 250.00,
                        "total": 250.00
                    },
                    {
                        "description": "Vital Signs Assessment",
                        "quantity": 1,
                        "unit_price": 50.00,
                        "total": 50.00
                    }
                ],
                "tax_rate": 0.08,
                "due_days": 30,
                "notes": "Annual wellness visit and assessment"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/invoices", json=invoice_data)
                if response.status_code == 200:
                    invoice = response.json()
                    invoice_id = invoice.get("id")
                    invoice_number = invoice.get("invoice_number")
                    total_amount = invoice.get("total_amount")
                    self.test_data["invoice_id"] = invoice_id
                    self.log_result("POST /api/invoices", True, 
                                  f"Created invoice {invoice_number} with ID: {invoice_id}, Total: ${total_amount}", 
                                  status_code=response.status_code, payload=invoice)
                else:
                    self.log_result("POST /api/invoices", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/invoices", False, f"Error: {str(e)}")
        
        # Test 2: Get All Invoices
        try:
            response = self.session.get(f"{API_BASE}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                self.log_result("GET /api/invoices", True, f"Retrieved {len(invoices)} invoices", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/invoices", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/invoices", False, f"Error: {str(e)}")
        
        # Test 3: Create Financial Transaction
        transaction_data = {
            "transaction_type": "income",
            "amount": 300.00,
            "payment_method": "credit_card",
            "description": "Payment for annual wellness visit",
            "category": "patient_payment",
            "patient_id": self.test_data.get("patient_id"),
            "invoice_id": self.test_data.get("invoice_id"),
            "created_by": "admin"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/financial-transactions", json=transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                transaction_id = transaction.get("id")
                transaction_number = transaction.get("transaction_number")
                self.test_data["financial_transaction_id"] = transaction_id
                self.log_result("POST /api/financial-transactions", True, 
                              f"Created financial transaction {transaction_number} with ID: {transaction_id}", 
                              status_code=response.status_code, payload=transaction)
            else:
                self.log_result("POST /api/financial-transactions", False, 
                              f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("POST /api/financial-transactions", False, f"Error: {str(e)}")
        
        # Test 4: Get All Financial Transactions
        try:
            response = self.session.get(f"{API_BASE}/financial-transactions")
            if response.status_code == 200:
                transactions = response.json()
                self.log_result("GET /api/financial-transactions", True, f"Retrieved {len(transactions)} financial transactions", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/financial-transactions", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/financial-transactions", False, f"Error: {str(e)}")

    def test_appointments_scheduling(self):
        """Test Appointments (/api/appointments + status/calendar if present)"""
        print("\n📅 TESTING APPOINTMENTS & SCHEDULING")
        print("=" * 50)
        
        # Test 1: Create Provider first
        provider_data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Family Medicine", "Internal Medicine"],
            "email": "dr.martinez@clinichub.com",
            "phone": "555-0321",
            "license_number": "TX12345",
            "npi_number": "1234567890"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/providers", json=provider_data)
            if response.status_code == 200:
                provider = response.json()
                provider_id = provider.get("id")
                self.test_data["provider_id"] = provider_id
                self.log_result("POST /api/providers", True, f"Created provider Dr. Martinez with ID: {provider_id}", 
                              status_code=response.status_code, payload=provider)
            else:
                self.log_result("POST /api/providers", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("POST /api/providers", False, f"Error: {str(e)}")
        
        # Test 2: Create Appointment
        if self.test_data.get("patient_id") and self.test_data.get("provider_id"):
            appointment_data = {
                "patient_id": self.test_data["patient_id"],
                "provider_id": self.test_data["provider_id"],
                "appointment_date": "2025-01-20",
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "consultation",
                "reason": "Follow-up consultation",
                "scheduled_by": "admin"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/appointments", json=appointment_data)
                if response.status_code == 200:
                    appointment = response.json()
                    appointment_id = appointment.get("id")
                    appointment_number = appointment.get("appointment_number")
                    self.test_data["appointment_id"] = appointment_id
                    self.log_result("POST /api/appointments", True, 
                                  f"Created appointment {appointment_number} with ID: {appointment_id}", 
                                  status_code=response.status_code, payload=appointment)
                else:
                    self.log_result("POST /api/appointments", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/appointments", False, f"Error: {str(e)}")
        
        # Test 3: Get All Appointments
        try:
            response = self.session.get(f"{API_BASE}/appointments")
            if response.status_code == 200:
                appointments = response.json()
                self.log_result("GET /api/appointments", True, f"Retrieved {len(appointments)} appointments", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/appointments", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/appointments", False, f"Error: {str(e)}")
        
        # Test 4: Calendar View (if present)
        try:
            response = self.session.get(f"{API_BASE}/appointments/calendar", 
                                      params={"date": "2025-01-20", "view": "week"})
            if response.status_code == 200:
                calendar_data = response.json()
                self.log_result("GET /api/appointments/calendar", True, "Calendar view retrieved successfully", 
                              status_code=response.status_code, payload=calendar_data)
            else:
                self.log_result("GET /api/appointments/calendar", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/appointments/calendar", False, f"Error: {str(e)}")

    def test_erx_prescriptions(self):
        """Test eRx (/api/erx/*, prescriptions)"""
        print("\n💊 TESTING eRx & PRESCRIPTIONS")
        print("=" * 50)
        
        # Test 1: Initialize eRx System
        try:
            response = self.session.post(f"{API_BASE}/erx/init")
            if response.status_code == 200:
                result = response.json()
                self.log_result("POST /api/erx/init", True, f"eRx system initialized: {result.get('message')}", 
                              status_code=response.status_code, payload=result)
            else:
                self.log_result("POST /api/erx/init", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("POST /api/erx/init", False, f"Error: {str(e)}")
        
        # Test 2: Get eRx Medications
        try:
            response = self.session.get(f"{API_BASE}/erx/medications")
            if response.status_code == 200:
                medications = response.json()
                self.log_result("GET /api/erx/medications", True, f"Retrieved {len(medications)} eRx medications", 
                              status_code=response.status_code)
                # Store first medication for prescription testing
                if medications:
                    self.test_data["medication_id"] = medications[0].get("id")
            else:
                self.log_result("GET /api/erx/medications", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/erx/medications", False, f"Error: {str(e)}")
        
        # Test 3: Create Prescription
        if self.test_data.get("patient_id") and self.test_data.get("provider_id") and self.test_data.get("medication_id"):
            prescription_data = {
                "medication_id": self.test_data["medication_id"],
                "patient_id": self.test_data["patient_id"],
                "prescriber_id": self.test_data["provider_id"],
                "prescriber_name": "Dr. Jennifer Martinez",
                "dosage_text": "Take 1 tablet by mouth twice daily with food",
                "dose_quantity": 1.0,
                "dose_unit": "tablet",
                "frequency": "BID",
                "route": "oral",
                "quantity": 60.0,
                "days_supply": 30,
                "refills": 2,
                "indication": "Hypertension management",
                "diagnosis_codes": ["I10"],
                "created_by": "admin"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/prescriptions", json=prescription_data)
                if response.status_code == 200:
                    prescription = response.json()
                    prescription_id = prescription.get("id")
                    prescription_number = prescription.get("prescription_number")
                    self.test_data["prescription_id"] = prescription_id
                    self.log_result("POST /api/prescriptions", True, 
                                  f"Created prescription {prescription_number} with ID: {prescription_id}", 
                                  status_code=response.status_code, payload=prescription)
                else:
                    self.log_result("POST /api/prescriptions", False, f"Failed: {response.status_code} - {response.text}",
                                  status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/prescriptions", False, f"Error: {str(e)}")
        
        # Test 4: Get All Prescriptions
        try:
            response = self.session.get(f"{API_BASE}/prescriptions")
            if response.status_code == 200:
                prescriptions = response.json()
                self.log_result("GET /api/prescriptions", True, f"Retrieved {len(prescriptions)} prescriptions", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/prescriptions", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/prescriptions", False, f"Error: {str(e)}")

    def test_lab_orders_catalog(self):
        """Test Lab orders (/api/lab-orders, catalog)"""
        print("\n🧪 TESTING LAB ORDERS & CATALOG")
        print("=" * 50)
        
        # Test 1: Get Lab Test Catalog
        try:
            response = self.session.get(f"{API_BASE}/lab-tests")
            if response.status_code == 200:
                lab_tests = response.json()
                self.log_result("GET /api/lab-tests", True, f"Retrieved {len(lab_tests)} lab tests from catalog", 
                              status_code=response.status_code)
                # Store first lab test for order testing
                if lab_tests:
                    self.test_data["lab_test_id"] = lab_tests[0].get("id")
            else:
                self.log_result("GET /api/lab-tests", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/lab-tests", False, f"Error: {str(e)}")
        
        # Test 2: Create Lab Order
        if self.test_data.get("patient_id") and self.test_data.get("provider_id"):
            lab_order_data = {
                "patient_id": self.test_data["patient_id"],
                "provider_id": self.test_data["provider_id"],
                "lab_tests": [self.test_data.get("lab_test_id")] if self.test_data.get("lab_test_id") else ["CBC"],
                "icd10_codes": ["Z00.00"],
                "priority": "routine",
                "clinical_notes": "Annual wellness lab work",
                "ordered_by": "admin"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/lab-orders", json=lab_order_data)
                if response.status_code == 200:
                    lab_order = response.json()
                    lab_order_id = lab_order.get("id")
                    order_number = lab_order.get("order_number")
                    self.test_data["lab_order_id"] = lab_order_id
                    self.log_result("POST /api/lab-orders", True, 
                                  f"Created lab order {order_number} with ID: {lab_order_id}", 
                                  status_code=response.status_code, payload=lab_order)
                else:
                    self.log_result("POST /api/lab-orders", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
            except Exception as e:
                self.log_result("POST /api/lab-orders", False, f"Error: {str(e)}")
        
        # Test 3: Get All Lab Orders
        try:
            response = self.session.get(f"{API_BASE}/lab-orders")
            if response.status_code == 200:
                lab_orders = response.json()
                self.log_result("GET /api/lab-orders", True, f"Retrieved {len(lab_orders)} lab orders", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/lab-orders", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/lab-orders", False, f"Error: {str(e)}")

    def test_additional_endpoints(self):
        """Test Communications, Clinical Templates, Quality Measures, Documents, Referrals, Telehealth"""
        print("\n🔧 TESTING ADDITIONAL ENDPOINTS")
        print("=" * 50)
        
        # Test 1: Clinical Templates
        try:
            response = self.session.get(f"{API_BASE}/clinical-templates")
            if response.status_code == 200:
                templates = response.json()
                self.log_result("GET /api/clinical-templates", True, f"Retrieved {len(templates)} clinical templates", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/clinical-templates", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/clinical-templates", False, f"Error: {str(e)}")
        
        # Test 2: Quality Measures
        try:
            response = self.session.get(f"{API_BASE}/quality-measures")
            if response.status_code == 200:
                measures = response.json()
                self.log_result("GET /api/quality-measures", True, f"Retrieved {len(measures)} quality measures", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/quality-measures", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/quality-measures", False, f"Error: {str(e)}")
        
        # Test 3: Document Management
        try:
            response = self.session.get(f"{API_BASE}/documents")
            if response.status_code == 200:
                documents = response.json()
                self.log_result("GET /api/documents", True, f"Retrieved {len(documents)} documents", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/documents", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/documents", False, f"Error: {str(e)}")
        
        # Test 4: Referrals
        try:
            response = self.session.get(f"{API_BASE}/referrals")
            if response.status_code == 200:
                referrals = response.json()
                self.log_result("GET /api/referrals", True, f"Retrieved {len(referrals)} referrals", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/referrals", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/referrals", False, f"Error: {str(e)}")
        
        # Test 5: Communications
        try:
            response = self.session.get(f"{API_BASE}/communications/templates")
            if response.status_code == 200:
                comm_templates = response.json()
                self.log_result("GET /api/communications/templates", True, f"Retrieved {len(comm_templates)} communication templates", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/communications/templates", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/communications/templates", False, f"Error: {str(e)}")
        
        # Test 6: Telehealth
        try:
            response = self.session.get(f"{API_BASE}/telehealth/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.log_result("GET /api/telehealth/sessions", True, f"Retrieved {len(sessions)} telehealth sessions", 
                              status_code=response.status_code)
            else:
                self.log_result("GET /api/telehealth/sessions", False, f"Failed: {response.status_code} - {response.text}",
                              status_code=response.status_code)
        except Exception as e:
            self.log_result("GET /api/telehealth/sessions", False, f"Error: {str(e)}")

        return True
        """Create a test patient for receipt generation"""
        try:
            patient_data = {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "555-0123",
                "date_of_birth": "1985-03-15",
                "gender": "female",
                "address_line1": "123 Main Street",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            }
            
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            
            if response.status_code == 200:
                patient = response.json()
                patient_id = patient.get("id")
                self.log_result("Create Test Patient", True, f"Created patient Sarah Johnson with ID: {patient_id}")
                return patient_id
            else:
                self.log_result("Create Test Patient", False, f"Failed to create patient: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Patient", False, f"Error creating patient: {str(e)}")
            return None
    
    def create_test_employee(self):
        """Create a test employee for clock-in/out testing"""
        try:
            employee_data = {
                "first_name": "Michael",
                "last_name": "Davis",
                "email": "michael.davis@clinichub.com",
                "phone": "555-0456",
                "role": "nurse",
                "department": "Emergency",
                "hire_date": "2024-01-15",
                "hourly_rate": 35.00
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee.get("id")
                self.log_result("Create Test Employee", True, f"Created employee Michael Davis with ID: {employee_id}")
                return employee_id
            else:
                self.log_result("Create Test Employee", False, f"Failed to create employee: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Employee", False, f"Error creating employee: {str(e)}")
            return None
    
    def create_test_soap_note(self, patient_id):
        """Create a test SOAP note for receipt generation"""
        try:
            soap_data = {
                "patient_id": patient_id,
                "encounter_id": f"ENC-{datetime.now().strftime('%Y%m%d')}-TEST",
                "subjective": "Patient reports feeling well overall. No acute complaints.",
                "objective": "Vital signs stable. Physical exam unremarkable.",
                "assessment": "Healthy adult, annual wellness visit",
                "plan": "Continue current health maintenance. Return in 1 year for annual check.",
                "provider": "Dr. Test Provider"
            }
            
            response = self.session.post(f"{API_BASE}/soap-notes", json=soap_data)
            
            if response.status_code == 200:
                soap_note = response.json()
                soap_id = soap_note.get("id")
                self.log_result("Create Test SOAP Note", True, f"Created SOAP note with ID: {soap_id}")
                return soap_id
            else:
                self.log_result("Create Test SOAP Note", False, f"Failed to create SOAP note: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test SOAP Note", False, f"Error creating SOAP note: {str(e)}")
            return None
    
    def test_receipt_generation_endpoints(self):
        """Test all receipt generation endpoints"""
        print("\n🧾 TESTING RECEIPT GENERATION ENDPOINTS")
        print("=" * 50)
        
        # Create test patient and SOAP note
        patient_id = self.create_test_patient()
        if not patient_id:
            return False
        
        soap_id = self.create_test_soap_note(patient_id)
        if not soap_id:
            return False
        
        # Test 1: GET /api/receipts (should work - list receipts)
        try:
            response = self.session.get(f"{API_BASE}/receipts")
            if response.status_code == 200:
                receipts = response.json()
                self.log_result("GET /api/receipts", True, f"Successfully retrieved {len(receipts)} receipts")
            else:
                self.log_result("GET /api/receipts", False, f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/receipts", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/receipts/soap-note/{id} (receipt generation)
        receipt_id = None
        try:
            response = self.session.post(f"{API_BASE}/receipts/soap-note/{soap_id}")
            if response.status_code == 200:
                result = response.json()
                receipt_id = result.get("receipt", {}).get("id")
                receipt_number = result.get("receipt", {}).get("receipt_number")
                self.log_result("POST /api/receipts/soap-note/{id}", True, 
                              f"Successfully generated receipt {receipt_number} with ID: {receipt_id}")
            else:
                self.log_result("POST /api/receipts/soap-note/{id}", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/receipts/soap-note/{id}", False, f"Error: {str(e)}")
        
        # Test 3: GET /api/receipts/{id} (individual receipt fetch)
        if receipt_id:
            try:
                response = self.session.get(f"{API_BASE}/receipts/{receipt_id}")
                if response.status_code == 200:
                    receipt = response.json()
                    patient_name = receipt.get("patient_name")
                    total = receipt.get("total")
                    self.log_result("GET /api/receipts/{id}", True, 
                                  f"Successfully retrieved receipt for {patient_name}, total: ${total}")
                else:
                    self.log_result("GET /api/receipts/{id}", False, 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("GET /api/receipts/{id}", False, f"Error: {str(e)}")
        else:
            self.log_result("GET /api/receipts/{id}", False, "Skipped - no receipt ID available")
        
        return True
    
    def test_employee_clock_endpoints(self):
        """Test all employee clock-in/out endpoints"""
        print("\n⏰ TESTING EMPLOYEE CLOCK-IN/OUT ENDPOINTS")
        print("=" * 50)
        
        # Create test employee
        employee_id = self.create_test_employee()
        if not employee_id:
            return False
        
        # Test 1: GET /api/employees/{id}/time-status (initial status check)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                self.log_result("GET /api/employees/{id}/time-status (initial)", True, 
                              f"Employee status: {current_status}")
            else:
                self.log_result("GET /api/employees/{id}/time-status (initial)", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-status (initial)", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/employees/{id}/clock-in (clock in functionality)
        try:
            response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-in", 
                                       params={"location": "Emergency Department"})
            if response.status_code == 200:
                result = response.json()
                timestamp = result.get("timestamp")
                location = result.get("location")
                self.log_result("POST /api/employees/{id}/clock-in", True, 
                              f"Successfully clocked in at {location}, time: {timestamp}")
            else:
                self.log_result("POST /api/employees/{id}/clock-in", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/employees/{id}/clock-in", False, f"Error: {str(e)}")
        
        # Wait a moment to simulate work time
        print("   ⏳ Waiting 3 seconds to simulate work time...")
        time.sleep(3)
        
        # Test 3: GET /api/employees/{id}/time-status (check clocked in status)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                hours_so_far = status.get("hours_so_far", 0)
                location = status.get("location")
                self.log_result("GET /api/employees/{id}/time-status (clocked in)", True, 
                              f"Status: {current_status}, Hours so far: {hours_so_far}, Location: {location}")
            else:
                self.log_result("GET /api/employees/{id}/time-status (clocked in)", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-status (clocked in)", False, f"Error: {str(e)}")
        
        # Test 4: POST /api/employees/{id}/clock-out (clock out functionality)
        try:
            response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-out")
            if response.status_code == 200:
                result = response.json()
                hours_worked = result.get("hours_worked")
                total_shift_time = result.get("total_shift_time")
                self.log_result("POST /api/employees/{id}/clock-out", True, 
                              f"Successfully clocked out, Hours worked: {hours_worked}, Shift time: {total_shift_time}")
            else:
                self.log_result("POST /api/employees/{id}/clock-out", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("POST /api/employees/{id}/clock-out", False, f"Error: {str(e)}")
        
        # Test 5: GET /api/employees/{id}/time-entries/today (daily time entries)
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-entries/today")
            if response.status_code == 200:
                result = response.json()
                entries = result.get("entries", [])
                total_hours = result.get("total_hours_today", 0)
                date_str = result.get("date")
                self.log_result("GET /api/employees/{id}/time-entries/today", True, 
                              f"Retrieved {len(entries)} entries for {date_str}, Total hours: {total_hours}")
            else:
                self.log_result("GET /api/employees/{id}/time-entries/today", False, 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("GET /api/employees/{id}/time-entries/today", False, f"Error: {str(e)}")
        
        return True
    
    def test_end_to_end_workflows(self):
        """Test end-to-end workflows"""
        print("\n🔄 TESTING END-TO-END WORKFLOWS")
        print("=" * 50)
        
        # Workflow 1: Create employee → Clock in → Check status → Clock out → Check time entries
        print("\n📋 Workflow 1: Complete Employee Time Tracking")
        employee_id = self.create_test_employee()
        if employee_id:
            # Clock in
            clock_in_response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-in", 
                                                params={"location": "Reception"})
            if clock_in_response.status_code == 200:
                print("   ✅ Employee clocked in successfully")
                
                # Check status
                time.sleep(1)
                status_response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   ✅ Status check: {status.get('status')} at {status.get('location')}")
                    
                    # Clock out
                    time.sleep(2)
                    clock_out_response = self.session.post(f"{API_BASE}/employees/{employee_id}/clock-out")
                    if clock_out_response.status_code == 200:
                        result = clock_out_response.json()
                        print(f"   ✅ Clocked out: {result.get('total_shift_time')}")
                        
                        # Check time entries
                        entries_response = self.session.get(f"{API_BASE}/employees/{employee_id}/time-entries/today")
                        if entries_response.status_code == 200:
                            entries = entries_response.json()
                            print(f"   ✅ Time entries: {len(entries.get('entries', []))} entries today")
                            self.log_result("End-to-End Employee Workflow", True, "Complete workflow successful")
                        else:
                            self.log_result("End-to-End Employee Workflow", False, "Failed at time entries step")
                    else:
                        self.log_result("End-to-End Employee Workflow", False, "Failed at clock out step")
                else:
                    self.log_result("End-to-End Employee Workflow", False, "Failed at status check step")
            else:
                self.log_result("End-to-End Employee Workflow", False, "Failed at clock in step")
        
        # Workflow 2: Create patient → Create SOAP note → Generate receipt → Verify receipt
        print("\n📋 Workflow 2: Complete Receipt Generation")
        patient_id = self.create_test_patient()
        if patient_id:
            # Create SOAP note
            soap_id = self.create_test_soap_note(patient_id)
            if soap_id:
                # Generate receipt
                receipt_response = self.session.post(f"{API_BASE}/receipts/soap-note/{soap_id}")
                if receipt_response.status_code == 200:
                    receipt_data = receipt_response.json()
                    receipt_id = receipt_data.get("receipt", {}).get("id")
                    print(f"   ✅ Receipt generated: {receipt_data.get('receipt', {}).get('receipt_number')}")
                    
                    # Verify receipt
                    if receipt_id:
                        verify_response = self.session.get(f"{API_BASE}/receipts/{receipt_id}")
                        if verify_response.status_code == 200:
                            receipt = verify_response.json()
                            print(f"   ✅ Receipt verified: ${receipt.get('total')} for {receipt.get('patient_name')}")
                            self.log_result("End-to-End Receipt Workflow", True, "Complete workflow successful")
                        else:
                            self.log_result("End-to-End Receipt Workflow", False, "Failed at receipt verification step")
                    else:
                        self.log_result("End-to-End Receipt Workflow", False, "No receipt ID returned")
                else:
                    self.log_result("End-to-End Receipt Workflow", False, "Failed at receipt generation step")
            else:
                self.log_result("End-to-End Receipt Workflow", False, "Failed at SOAP note creation step")
        else:
            self.log_result("End-to-End Receipt Workflow", False, "Failed at patient creation step")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🏥 CLINICHUB BACKEND TESTING - RECEIPT GENERATION & EMPLOYEE CLOCK-IN/OUT")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run specific tests
        self.test_receipt_generation_endpoints()
        self.test_employee_clock_endpoints()
        self.test_end_to_end_workflows()
        
        # Summary
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n🎯 CRITICAL FINDINGS:")
        receipt_tests = [r for r in self.test_results if "receipt" in r["test"].lower()]
        clock_tests = [r for r in self.test_results if "clock" in r["test"].lower() or "time" in r["test"].lower()]
        
        receipt_success = sum(1 for r in receipt_tests if r["success"])
        clock_success = sum(1 for r in clock_tests if r["success"])
        
        print(f"   📄 Receipt Generation: {receipt_success}/{len(receipt_tests)} tests passed")
        print(f"   ⏰ Employee Clock System: {clock_success}/{len(clock_tests)} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The newly added functionality is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Review the issues above.")

def main():
    """Main function"""
    tester = ClinicHubTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()