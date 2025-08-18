#!/usr/bin/env python3
"""
Focused Test Suite for ClinicHub Vital Signs and SOAP Notes Functionality
This test focuses specifically on the requested endpoints and functionality
"""

import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Global variables
admin_token = None

def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            if isinstance(response, dict):
                print(f"   Response: {json.dumps(response, indent=2, default=str)[:300]}...")
            else:
                print(f"   Response: {str(response)[:300]}...")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate():
    """Get admin token"""
    global admin_token
    
    print("\n=== AUTHENTICATION ===")
    
    try:
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        admin_token = result["access_token"]
        print_test_result("Admin Login", True, {"token_received": True})
        return True
    except Exception as e:
        print_test_result("Admin Login", False, error_msg=str(e))
        return False

def create_test_data():
    """Create minimal test data needed for testing"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a simple patient using direct database approach
    patient_id = str(uuid.uuid4())
    encounter_id = str(uuid.uuid4())
    
    print(f"Using test patient ID: {patient_id}")
    print(f"Using test encounter ID: {encounter_id}")
    
    return patient_id, encounter_id

def test_vital_signs_endpoints():
    """Test vital signs endpoints"""
    print("\n=== VITAL SIGNS ENDPOINTS TESTING ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create test IDs
    patient_id = str(uuid.uuid4())
    encounter_id = str(uuid.uuid4())
    
    # Test 1: POST /api/vital-signs - Create vital signs
    vital_signs_id = None
    try:
        url = f"{API_URL}/vital-signs"
        data = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "height": 170.0,
            "weight": 70.0,
            "bmi": 24.2,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature": 36.5,
            "oxygen_saturation": 98,
            "pain_scale": 0
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        vital_signs_id = result["id"]
        assert result["patient_id"] == patient_id
        assert result["systolic_bp"] == 120
        assert result["diastolic_bp"] == 80
        
        print_test_result("POST /api/vital-signs", True, {
            "vital_signs_id": vital_signs_id,
            "patient_id": result["patient_id"],
            "bp": f"{result['systolic_bp']}/{result['diastolic_bp']}"
        })
    except Exception as e:
        print_test_result("POST /api/vital-signs", False, error_msg=str(e))
    
    # Test 2: GET /api/vital-signs - Get all vital signs
    try:
        url = f"{API_URL}/vital-signs"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("GET /api/vital-signs", True, {"count": len(result)})
    except Exception as e:
        print_test_result("GET /api/vital-signs", False, error_msg=str(e))
    
    # Test 3: GET /api/vital-signs/patient/{patient_id} - Get patient vital signs
    try:
        url = f"{API_URL}/vital-signs/patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["patient_id"] == patient_id
        
        print_test_result("GET /api/vital-signs/patient/{patient_id}", True, {
            "count": len(result),
            "patient_id": patient_id
        })
    except Exception as e:
        print_test_result("GET /api/vital-signs/patient/{patient_id}", False, error_msg=str(e))
    
    # Test 4: Create another vital signs record (simulating PUT update)
    try:
        url = f"{API_URL}/vital-signs"
        data = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "height": 170.0,
            "weight": 69.5,  # Updated weight
            "bmi": 24.0,     # Updated BMI
            "systolic_bp": 118,  # Updated BP
            "diastolic_bp": 78,
            "heart_rate": 70,    # Updated HR
            "respiratory_rate": 16,
            "temperature": 36.6,  # Updated temp
            "oxygen_saturation": 99,  # Updated O2
            "pain_scale": 0
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["weight"] == 69.5
        assert result["systolic_bp"] == 118
        
        print_test_result("POST /api/vital-signs (Update Simulation)", True, {
            "updated_weight": result["weight"],
            "updated_bp": f"{result['systolic_bp']}/{result['diastolic_bp']}"
        })
    except Exception as e:
        print_test_result("POST /api/vital-signs (Update Simulation)", False, error_msg=str(e))
    
    return patient_id, encounter_id

def test_soap_notes_endpoints(patient_id, encounter_id):
    """Test SOAP notes endpoints"""
    print("\n=== SOAP NOTES ENDPOINTS TESTING ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: POST /api/soap-notes - Create SOAP note
    soap_note_id = None
    try:
        url = f"{API_URL}/soap-notes"
        data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "subjective": "Patient reports feeling well. No acute complaints. Routine follow-up visit.",
            "objective": "Vital signs stable: BP 118/78, HR 70, Temp 36.6°C, RR 16, O2 Sat 99%. Physical exam unremarkable.",
            "assessment": "1. Routine health maintenance\n2. Overall good health status",
            "plan": "1. Continue current health habits\n2. Return for routine follow-up in 6 months\n3. Contact office with any concerns",
            "provider": "Dr. Test Provider"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        soap_note_id = result["id"]
        assert result["patient_id"] == patient_id
        assert result["encounter_id"] == encounter_id
        assert result["status"] == "draft"
        
        print_test_result("POST /api/soap-notes", True, {
            "soap_note_id": soap_note_id,
            "status": result["status"],
            "provider": result["provider"]
        })
    except Exception as e:
        print_test_result("POST /api/soap-notes", False, error_msg=str(e))
    
    # Test 2: GET /api/soap-notes - Get all SOAP notes
    try:
        url = f"{API_URL}/soap-notes"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        print_test_result("GET /api/soap-notes", True, {"count": len(result)})
    except Exception as e:
        print_test_result("GET /api/soap-notes", False, error_msg=str(e))
    
    # Test 3: GET /api/soap-notes/{id} - Get specific SOAP note
    if soap_note_id:
        try:
            url = f"{API_URL}/soap-notes/{soap_note_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == soap_note_id
            assert "subjective" in result
            assert "objective" in result
            assert "assessment" in result
            assert "plan" in result
            
            print_test_result("GET /api/soap-notes/{id}", True, {
                "soap_note_id": result["id"],
                "has_all_sections": all(key in result for key in ["subjective", "objective", "assessment", "plan"])
            })
        except Exception as e:
            print_test_result("GET /api/soap-notes/{id}", False, error_msg=str(e))
    
    # Test 4: PUT /api/soap-notes/{id} - Update SOAP note
    if soap_note_id:
        try:
            url = f"{API_URL}/soap-notes/{soap_note_id}"
            data = {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "subjective": "Patient reports feeling well. No acute complaints. Routine follow-up visit. UPDATED: Patient mentions occasional mild fatigue.",
                "objective": "Vital signs stable: BP 118/78, HR 70, Temp 36.6°C, RR 16, O2 Sat 99%. Physical exam unremarkable. UPDATED: Patient appears slightly tired but alert.",
                "assessment": "1. Routine health maintenance\n2. Overall good health status\n3. UPDATED: Mild fatigue, likely work-related",
                "plan": "1. Continue current health habits\n2. Recommend adequate sleep and stress management\n3. Return for routine follow-up in 6 months\n4. Contact office with any concerns",
                "provider": "Dr. Test Provider"
            }
            
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == soap_note_id
            assert "UPDATED:" in result["subjective"]
            assert "UPDATED:" in result["objective"]
            assert "UPDATED:" in result["assessment"]
            
            print_test_result("PUT /api/soap-notes/{id}", True, {
                "soap_note_id": result["id"],
                "updated": "UPDATED:" in result["subjective"]
            })
        except Exception as e:
            print_test_result("PUT /api/soap-notes/{id}", False, error_msg=str(e))
    
    # Test 5: GET /api/soap-notes/encounter/{encounter_id} - Get SOAP notes by encounter
    try:
        url = f"{API_URL}/soap-notes/encounter/{encounter_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["encounter_id"] == encounter_id
        
        print_test_result("GET /api/soap-notes/encounter/{encounter_id}", True, {
            "count": len(result),
            "encounter_id": encounter_id
        })
    except Exception as e:
        print_test_result("GET /api/soap-notes/encounter/{encounter_id}", False, error_msg=str(e))
    
    # Test 6: GET /api/soap-notes/patient/{patient_id} - Get SOAP notes by patient
    try:
        url = f"{API_URL}/soap-notes/patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["patient_id"] == patient_id
        
        print_test_result("GET /api/soap-notes/patient/{patient_id}", True, {
            "count": len(result),
            "patient_id": patient_id
        })
    except Exception as e:
        print_test_result("GET /api/soap-notes/patient/{patient_id}", False, error_msg=str(e))
    
    return soap_note_id

def test_soap_notes_completion_and_receipt(soap_note_id, patient_id):
    """Test SOAP notes completion and receipt generation"""
    print("\n=== SOAP NOTES COMPLETION & RECEIPT TESTING ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: POST /api/soap-notes/{id}/complete - Complete SOAP note with automated workflows
    if soap_note_id:
        try:
            url = f"{API_URL}/soap-notes/{soap_note_id}/complete"
            completion_data = {
                "billable_services": [
                    {
                        "description": "Office Visit - Routine Follow-up",
                        "code": "99213",
                        "quantity": 1,
                        "unit_price": 150.00
                    },
                    {
                        "description": "Vital Signs Assessment",
                        "code": "99000",
                        "quantity": 1,
                        "unit_price": 30.00
                    }
                ],
                "prescribed_medications": [],
                "session_duration": 25
            }
            
            response = requests.post(url, json=completion_data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Verify completion response
            assert "message" in result
            assert "soap_note" in result
            assert "automated_workflows" in result
            assert result["soap_note"]["status"] == "completed"
            
            # Check automated workflows
            workflows = result["automated_workflows"]
            invoice_created = "invoice_created" in workflows
            
            print_test_result("POST /api/soap-notes/{id}/complete", True, {
                "soap_note_completed": True,
                "status": result["soap_note"]["status"],
                "invoice_created": invoice_created,
                "workflows": list(workflows.keys())
            })
            
            # Test receipt functionality if invoice was created
            if invoice_created and workflows["invoice_created"].get("status") != "error":
                invoice_id = workflows["invoice_created"].get("invoice_id")
                if invoice_id:
                    try:
                        url = f"{API_URL}/invoices/{invoice_id}"
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        invoice_result = response.json()
                        
                        assert invoice_result["id"] == invoice_id
                        assert invoice_result["patient_id"] == patient_id
                        assert len(invoice_result["items"]) == 2
                        
                        print_test_result("GET /api/invoices/{id} (Receipt Verification)", True, {
                            "invoice_id": invoice_id,
                            "invoice_number": invoice_result["invoice_number"],
                            "total_amount": invoice_result["total_amount"],
                            "items_count": len(invoice_result["items"])
                        })
                    except Exception as e:
                        print_test_result("GET /api/invoices/{id} (Receipt Verification)", False, error_msg=str(e))
            
        except Exception as e:
            print_test_result("POST /api/soap-notes/{id}/complete", False, error_msg=str(e))

def test_integration_scenarios(patient_id, encounter_id):
    """Test integration between vital signs and SOAP notes"""
    print("\n=== INTEGRATION TESTING ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: Create vital signs with specific values and reference in SOAP note
    try:
        # Create vital signs with notable values
        url = f"{API_URL}/vital-signs"
        vital_data = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "height": 175.0,
            "weight": 85.0,
            "bmi": 27.8,  # Overweight
            "systolic_bp": 140,  # Elevated
            "diastolic_bp": 90,  # Elevated
            "heart_rate": 88,
            "respiratory_rate": 18,
            "temperature": 37.2,  # Slightly elevated
            "oxygen_saturation": 97,
            "pain_scale": 3
        }
        
        response = requests.post(url, json=vital_data, headers=headers)
        response.raise_for_status()
        vital_result = response.json()
        
        # Create SOAP note that references the vital signs
        url = f"{API_URL}/soap-notes"
        soap_data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "subjective": "Patient reports mild discomfort and fatigue. Pain level 3/10. Has been experiencing stress at work.",
            "objective": f"Vital signs notable: BP 140/90 (elevated), HR 88, Temp 37.2°C (slightly elevated), BMI 27.8 (overweight). Patient appears mildly uncomfortable.",
            "assessment": "1. Hypertension, stage 1\n2. Overweight (BMI 27.8)\n3. Mild hyperthermia\n4. Work-related stress",
            "plan": "1. Blood pressure monitoring and lifestyle counseling\n2. Weight management discussion\n3. Stress reduction techniques\n4. Follow-up in 2 weeks\n5. Return if symptoms worsen",
            "provider": "Dr. Integration Test"
        }
        
        response = requests.post(url, json=soap_data, headers=headers)
        response.raise_for_status()
        soap_result = response.json()
        
        # Verify integration
        assert vital_result["systolic_bp"] == 140
        assert vital_result["bmi"] == 27.8
        assert "BP 140/90" in soap_result["objective"]
        assert "BMI 27.8" in soap_result["objective"]
        
        print_test_result("Vital Signs Integration with SOAP Notes", True, {
            "vital_signs_id": vital_result["id"],
            "soap_note_id": soap_result["id"],
            "bp_recorded": f"{vital_result['systolic_bp']}/{vital_result['diastolic_bp']}",
            "bmi_recorded": vital_result["bmi"],
            "referenced_in_soap": "BP 140/90" in soap_result["objective"]
        })
        
    except Exception as e:
        print_test_result("Vital Signs Integration with SOAP Notes", False, error_msg=str(e))

def run_focused_test():
    """Run focused vital signs and SOAP notes tests"""
    print("=" * 80)
    print("CLINICHUB VITAL SIGNS & SOAP NOTES FOCUSED TEST SUITE")
    print("=" * 80)
    
    # Step 1: Authentication
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Test vital signs endpoints
    patient_id, encounter_id = test_vital_signs_endpoints()
    
    # Step 3: Test SOAP notes endpoints
    soap_note_id = test_soap_notes_endpoints(patient_id, encounter_id)
    
    # Step 4: Test SOAP notes completion and receipt generation
    if soap_note_id:
        test_soap_notes_completion_and_receipt(soap_note_id, patient_id)
    
    # Step 5: Test integration scenarios
    test_integration_scenarios(patient_id, encounter_id)
    
    print("\n" + "=" * 80)
    print("FOCUSED TEST SUITE COMPLETED")
    print("=" * 80)
    print(f"✅ Test Patient ID: {patient_id}")
    print(f"✅ Test Encounter ID: {encounter_id}")
    if soap_note_id:
        print(f"✅ Test SOAP Note ID: {soap_note_id}")
    print("=" * 80)

if __name__ == "__main__":
    run_focused_test()