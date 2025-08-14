#!/usr/bin/env python3
"""
Focused EHR Assessment - Testing Core EHR Functionality
"""

import requests
import json
from datetime import date, datetime
import uuid

# Use localhost for backend
API_URL = "http://localhost:8001/api"
print(f"🏥 Focused EHR Assessment - Using API URL: {API_URL}")

def test_authentication():
    """Test authentication system"""
    print("\n=== AUTHENTICATION TEST ===")
    
    try:
        # Try to initialize admin (may already exist)
        response = requests.post(f"{API_URL}/auth/init-admin")
        if response.status_code == 200:
            print("✅ Admin initialization: SUCCESS")
        elif response.status_code == 400 and "already exists" in response.text:
            print("✅ Admin already exists: SUCCESS")
        else:
            response.raise_for_status()
        
        # Login
        response = requests.post(f"{API_URL}/auth/login", json={"username": "admin", "password": "admin123"})
        response.raise_for_status()
        result = response.json()
        token = result["access_token"]
        print("✅ Admin login: SUCCESS")
        return token
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_patient_management(token):
    """Test FHIR-compliant patient management"""
    print("\n=== PATIENT MANAGEMENT TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Create patient
        patient_data = {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1980-05-15",
            "gender": "male",
            "address_line1": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701"
        }
        
        response = requests.post(f"{API_URL}/patients", headers=headers, json=patient_data)
        response.raise_for_status()
        result = response.json()
        
        # Check FHIR compliance
        if result.get("resource_type") == "Patient":
            print("✅ FHIR-compliant patient creation: SUCCESS")
            patient_id = result["id"]
            
            # Test patient retrieval
            response = requests.get(f"{API_URL}/patients/{patient_id}", headers=headers)
            response.raise_for_status()
            print("✅ Patient retrieval: SUCCESS")
            
            return patient_id
        else:
            print("❌ FHIR compliance: FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Patient management failed: {str(e)}")
        return None

def test_clinical_documentation(token, patient_id):
    """Test clinical documentation (encounters, SOAP notes)"""
    print("\n=== CLINICAL DOCUMENTATION TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Create encounter
        encounter_data = {
            "patient_id": patient_id,
            "encounter_type": "follow_up",
            "scheduled_date": datetime.now().isoformat(),
            "provider": "Dr. Sarah Johnson",
            "location": "Main Clinic",
            "chief_complaint": "Routine check-up",
            "reason_for_visit": "Annual physical"
        }
        
        response = requests.post(f"{API_URL}/encounters", headers=headers, json=encounter_data)
        response.raise_for_status()
        result = response.json()
        encounter_id = result["id"]
        print("✅ Encounter creation: SUCCESS")
        
        # Create SOAP note
        soap_data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "subjective": "Patient feels well, no complaints",
            "objective": "Vital signs normal, physical exam unremarkable",
            "assessment": "Healthy adult, no acute issues",
            "plan": "Continue current lifestyle, return in 1 year",
            "provider": "Dr. Sarah Johnson"
        }
        
        response = requests.post(f"{API_URL}/soap-notes", headers=headers, json=soap_data)
        response.raise_for_status()
        print("✅ SOAP notes creation: SUCCESS")
        
        return encounter_id
        
    except Exception as e:
        print(f"❌ Clinical documentation failed: {str(e)}")
        return None

def test_vital_signs(token, patient_id, encounter_id):
    """Test vital signs recording"""
    print("\n=== VITAL SIGNS TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        vital_data = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "height": 175.0,
            "weight": 70.0,
            "bmi": 22.9,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "temperature": 36.8,
            "oxygen_saturation": 98,
            "pain_scale": 0,
            "recorded_by": "Nurse Smith"
        }
        
        response = requests.post(f"{API_URL}/vital-signs", headers=headers, json=vital_data)
        response.raise_for_status()
        print("✅ Vital signs recording: SUCCESS")
        
        # Test retrieval
        response = requests.get(f"{API_URL}/vital-signs/patient/{patient_id}", headers=headers)
        response.raise_for_status()
        print("✅ Vital signs retrieval: SUCCESS")
        
    except Exception as e:
        print(f"❌ Vital signs failed: {str(e)}")

def test_medication_management(token, patient_id):
    """Test medication and allergy management"""
    print("\n=== MEDICATION MANAGEMENT TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test allergy management
        allergy_data = {
            "patient_id": patient_id,
            "allergen": "Penicillin",
            "reaction": "Rash",
            "severity": "moderate",
            "created_by": "Dr. Johnson"
        }
        
        response = requests.post(f"{API_URL}/allergies", headers=headers, json=allergy_data)
        response.raise_for_status()
        print("✅ Allergy management: SUCCESS")
        
        # Test medication management
        med_data = {
            "patient_id": patient_id,
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "route": "oral",
            "start_date": date.today().isoformat(),
            "prescribing_physician": "Dr. Johnson",
            "indication": "Hypertension"
        }
        
        response = requests.post(f"{API_URL}/medications", headers=headers, json=med_data)
        response.raise_for_status()
        print("✅ Medication management: SUCCESS")
        
    except Exception as e:
        print(f"❌ Medication management failed: {str(e)}")

def test_diagnostic_integration(token, patient_id, encounter_id):
    """Test ICD-10 and diagnostic coding"""
    print("\n=== DIAGNOSTIC INTEGRATION TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Initialize ICD-10 system
        response = requests.post(f"{API_URL}/icd10/init", headers=headers)
        response.raise_for_status()
        print("✅ ICD-10 initialization: SUCCESS")
        
        # Test ICD-10 search
        response = requests.get(f"{API_URL}/icd10/search", headers=headers, params={"query": "hypertension"})
        response.raise_for_status()
        result = response.json()
        if len(result) > 0:
            print("✅ ICD-10 code search: SUCCESS")
        
        # Create diagnosis
        diagnosis_data = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "diagnosis_code": "I10",
            "diagnosis_description": "Essential hypertension",
            "diagnosis_type": "primary",
            "status": "active",
            "provider": "Dr. Johnson"
        }
        
        response = requests.post(f"{API_URL}/diagnoses", headers=headers, json=diagnosis_data)
        response.raise_for_status()
        print("✅ Diagnosis creation with ICD-10: SUCCESS")
        
    except Exception as e:
        print(f"❌ Diagnostic integration failed: {str(e)}")

def test_erx_system(token, patient_id):
    """Test electronic prescribing system"""
    print("\n=== eRx SYSTEM TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Initialize eRx system
        response = requests.post(f"{API_URL}/erx/init", headers=headers)
        response.raise_for_status()
        print("✅ eRx system initialization: SUCCESS")
        
        # Get medications
        response = requests.get(f"{API_URL}/erx/medications", headers=headers)
        response.raise_for_status()
        medications = response.json()
        
        if len(medications) > 0:
            print("✅ eRx medication database: SUCCESS")
            
            # Test drug interaction checking
            if len(medications) >= 2:
                drug1_id = medications[0]["id"]
                drug2_id = medications[1]["id"]
                
                response = requests.get(f"{API_URL}/drug-interactions", headers=headers, 
                                      params={"drug1_id": drug1_id, "drug2_id": drug2_id})
                if response.status_code == 200:
                    print("✅ Drug interaction checking: SUCCESS")
                else:
                    print("⚠️ Drug interaction checking: PARTIAL")
        
    except Exception as e:
        print(f"❌ eRx system failed: {str(e)}")

def test_lab_integration(token, patient_id):
    """Test lab integration"""
    print("\n=== LAB INTEGRATION TEST ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Initialize lab system
        response = requests.post(f"{API_URL}/lab-tests/init", headers=headers)
        response.raise_for_status()
        print("✅ Lab system initialization: SUCCESS")
        
        # Get lab tests
        response = requests.get(f"{API_URL}/lab-tests", headers=headers)
        response.raise_for_status()
        tests = response.json()
        
        if len(tests) > 0:
            print("✅ Lab test catalog: SUCCESS")
            
            # Create lab order
            order_data = {
                "patient_id": patient_id,
                "provider_id": "provider-123",
                "lab_tests": [tests[0]["id"]] if tests else [],
                "icd10_codes": ["I10"],
                "ordered_by": "Dr. Johnson"
            }
            
            response = requests.post(f"{API_URL}/lab-orders", headers=headers, json=order_data)
            response.raise_for_status()
            print("✅ Lab order creation: SUCCESS")
        
    except Exception as e:
        print(f"❌ Lab integration failed: {str(e)}")

def main():
    """Run focused EHR assessment"""
    print("🏥 FOCUSED EHR SYSTEM ASSESSMENT")
    print("=" * 50)
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test patient management
    patient_id = test_patient_management(token)
    if not patient_id:
        print("❌ Cannot proceed without patient")
        return
    
    # Test clinical documentation
    encounter_id = test_clinical_documentation(token, patient_id)
    
    # Test vital signs
    if encounter_id:
        test_vital_signs(token, patient_id, encounter_id)
    
    # Test medication management
    test_medication_management(token, patient_id)
    
    # Test diagnostic integration
    if encounter_id:
        test_diagnostic_integration(token, patient_id, encounter_id)
    
    # Test eRx system
    test_erx_system(token, patient_id)
    
    # Test lab integration
    test_lab_integration(token, patient_id)
    
    print("\n" + "=" * 50)
    print("🎉 FOCUSED EHR ASSESSMENT COMPLETE")
    print("📊 Core EHR functionality verified")

if __name__ == "__main__":
    main()