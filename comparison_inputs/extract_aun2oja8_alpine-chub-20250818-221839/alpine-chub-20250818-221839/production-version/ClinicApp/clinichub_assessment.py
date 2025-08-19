#!/usr/bin/env python3
"""
ClinicHub Comprehensive Module Assessment
Evaluates all 16 core modules for completeness and functionality
"""

import requests
import json
from datetime import date, datetime, timedelta
import uuid

# Use localhost for backend access
API_URL = "http://localhost:8001/api"
print(f"🏥 ClinicHub Comprehensive Module Assessment")
print(f"📡 Using API URL: {API_URL}")
print("=" * 80)

# Global variables
admin_token = None
assessment_results = {}

def authenticate():
    """Get admin token for API access"""
    global admin_token
    try:
        # Initialize admin if needed
        response = requests.post(f"{API_URL}/auth/init-admin")
        
        # Login as admin
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": "admin", 
            "password": "admin123"
        })
        
        if response.status_code == 200:
            result = response.json()
            admin_token = result["access_token"]
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def assess_module(module_name, endpoints, description):
    """Assess a module by testing its endpoints"""
    print(f"\n📋 ASSESSING: {module_name}")
    print(f"Description: {description}")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
    
    results = {
        "module_name": module_name,
        "description": description,
        "endpoints_tested": 0,
        "endpoints_working": 0,
        "endpoints_details": [],
        "backend_api_complete": 0,
        "data_models_complete": 0,
        "crud_operations": 0,
        "business_logic": 0,
        "integration_ready": 0,
        "fhir_compliance": 0,
        "production_readiness": 0,
        "status": "Missing",
        "key_endpoints": [],
        "missing_features": [],
        "dependencies": [],
        "priority": "High"
    }
    
    for endpoint_info in endpoints:
        endpoint = endpoint_info["endpoint"]
        method = endpoint_info.get("method", "GET")
        test_data = endpoint_info.get("data", None)
        expected_fields = endpoint_info.get("expected_fields", [])
        
        try:
            results["endpoints_tested"] += 1
            
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{API_URL}{endpoint}", json=test_data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(f"{API_URL}{endpoint}", json=test_data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                results["endpoints_working"] += 1
                status = "✅ Working"
                
                # Check for expected fields in response
                try:
                    response_data = response.json()
                    fields_found = []
                    for field in expected_fields:
                        if field in str(response_data):
                            fields_found.append(field)
                    
                    if fields_found:
                        results["key_endpoints"].append(f"{method} {endpoint}")
                        
                except:
                    pass
                    
            else:
                status = f"❌ Failed ({response.status_code})"
                
            results["endpoints_details"].append({
                "endpoint": f"{method} {endpoint}",
                "status_code": response.status_code,
                "status": status
            })
            
            print(f"  {status}: {method} {endpoint}")
            
        except Exception as e:
            results["endpoints_details"].append({
                "endpoint": f"{method} {endpoint}",
                "status_code": 0,
                "status": f"❌ Error: {str(e)[:50]}"
            })
            print(f"  ❌ Error: {method} {endpoint} - {str(e)[:50]}")
    
    # Calculate completion percentages
    if results["endpoints_tested"] > 0:
        working_ratio = results["endpoints_working"] / results["endpoints_tested"]
        
        # Estimate completeness based on working endpoints
        results["backend_api_complete"] = int(working_ratio * 100)
        results["data_models_complete"] = int(working_ratio * 90)  # Slightly lower
        results["crud_operations"] = int(working_ratio * 85)
        results["business_logic"] = int(working_ratio * 80)
        results["integration_ready"] = int(working_ratio * 75)
        results["fhir_compliance"] = int(working_ratio * 70) if "patient" in module_name.lower() or "ehr" in module_name.lower() else int(working_ratio * 50)
        results["production_readiness"] = int(working_ratio * 85)
        
        # Determine status
        if working_ratio >= 0.8:
            results["status"] = "Complete"
        elif working_ratio >= 0.5:
            results["status"] = "Partial"
        elif working_ratio >= 0.2:
            results["status"] = "Basic"
        else:
            results["status"] = "Missing"
    
    # Add to global results
    assessment_results[module_name] = results
    
    print(f"📊 Assessment: {results['status']} ({results['endpoints_working']}/{results['endpoints_tested']} endpoints working)")
    return results

def run_comprehensive_assessment():
    """Run assessment on all 16 core modules"""
    
    # 1. Authentication System
    assess_module(
        "Authentication System",
        [
            {"endpoint": "/auth/login", "method": "POST", "data": {"username": "admin", "password": "admin123"}, "expected_fields": ["access_token", "user"]},
            {"endpoint": "/auth/me", "method": "GET", "expected_fields": ["username", "role"]},
            {"endpoint": "/auth/init-admin", "method": "POST", "expected_fields": ["username"]},
            {"endpoint": "/auth/synology-status", "method": "GET", "expected_fields": ["synology_enabled"]},
        ],
        "JWT authentication, user management, role-based access control, Synology SSO integration"
    )
    
    # 2. Patient/EHR Management
    assess_module(
        "Patient/EHR Management",
        [
            {"endpoint": "/patients", "method": "GET", "expected_fields": ["resource_type", "name"]},
            {"endpoint": "/patients", "method": "POST", "data": {
                "first_name": "Test", "last_name": "Patient", "email": "test@example.com",
                "phone": "+1-555-123-4567", "date_of_birth": "1990-01-01", "gender": "male"
            }, "expected_fields": ["id", "resource_type"]},
            {"endpoint": "/encounters", "method": "GET", "expected_fields": ["encounter_number"]},
            {"endpoint": "/soap-notes", "method": "GET", "expected_fields": ["subjective", "objective"]},
            {"endpoint": "/vital-signs", "method": "GET", "expected_fields": ["patient_id"]},
        ],
        "FHIR-compliant patient records, encounters, SOAP notes, vital signs, medical history"
    )
    
    # 3. Electronic Prescribing (eRx)
    assess_module(
        "Electronic Prescribing (eRx)",
        [
            {"endpoint": "/erx/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/erx/medications", "method": "GET", "expected_fields": ["generic_name", "drug_class"]},
            {"endpoint": "/prescriptions", "method": "GET", "expected_fields": ["prescription_number"]},
            {"endpoint": "/drug-interactions", "method": "GET", "expected_fields": ["severity"]},
        ],
        "FHIR-compliant medication management, drug interactions, prescription tracking"
    )
    
    # 4. Appointment Scheduling
    assess_module(
        "Appointment Scheduling",
        [
            {"endpoint": "/appointments", "method": "GET", "expected_fields": ["appointment_number", "patient_name"]},
            {"endpoint": "/providers", "method": "GET", "expected_fields": ["first_name", "specialties"]},
            {"endpoint": "/appointments/calendar", "method": "GET", "expected_fields": ["date"]},
            {"endpoint": "/provider-schedules", "method": "GET", "expected_fields": ["provider_id"]},
        ],
        "Provider scheduling, patient appointments, calendar management, automated reminders"
    )
    
    # 5. Employee Management
    assess_module(
        "Employee Management",
        [
            {"endpoint": "/employees", "method": "GET", "expected_fields": ["employee_id", "role"]},
            {"endpoint": "/employees", "method": "POST", "data": {
                "first_name": "Test", "last_name": "Employee", "email": "test.emp@clinic.com",
                "role": "nurse", "hire_date": date.today().isoformat()
            }, "expected_fields": ["employee_id"]},
            {"endpoint": "/employee-documents", "method": "GET", "expected_fields": ["document_type"]},
            {"endpoint": "/time-entries", "method": "GET", "expected_fields": ["entry_type"]},
            {"endpoint": "/work-shifts", "method": "GET", "expected_fields": ["shift_date"]},
        ],
        "Staff profiles, roles, payroll, time tracking, document management"
    )
    
    # 6. Financial Management
    assess_module(
        "Financial Management",
        [
            {"endpoint": "/invoices", "method": "GET", "expected_fields": ["invoice_number", "total_amount"]},
            {"endpoint": "/financial-transactions", "method": "GET", "expected_fields": ["transaction_number", "amount"]},
            {"endpoint": "/vendors", "method": "GET", "expected_fields": ["company_name"]},
            {"endpoint": "/checks", "method": "GET", "expected_fields": ["check_number"]},
            {"endpoint": "/payroll-periods", "method": "GET", "expected_fields": ["period_start"]},
        ],
        "Invoicing, payments, transactions, accounting, vendor management, payroll"
    )
    
    # 7. Inventory Management
    assess_module(
        "Inventory Management",
        [
            {"endpoint": "/inventory", "method": "GET", "expected_fields": ["name", "current_stock"]},
            {"endpoint": "/inventory", "method": "POST", "data": {
                "name": "Test Supply", "category": "Medical", "current_stock": 100,
                "min_stock_level": 10, "unit_cost": 5.0
            }, "expected_fields": ["id"]},
        ],
        "Medical supplies, stock tracking, ordering, expiry management"
    )
    
    # 8. Smart Forms
    assess_module(
        "Smart Forms",
        [
            {"endpoint": "/forms", "method": "GET", "expected_fields": ["title", "fields"]},
            {"endpoint": "/forms/templates", "method": "GET", "expected_fields": ["name", "category"]},
            {"endpoint": "/form-submissions", "method": "GET", "expected_fields": ["form_id", "patient_id"]},
            {"endpoint": "/forms/templates/init", "method": "POST", "expected_fields": ["message"]},
        ],
        "Form builder, HIPAA compliance, FHIR mapping, smart tags"
    )
    
    # 9. Lab Integration
    assess_module(
        "Lab Integration",
        [
            {"endpoint": "/lab-tests/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/lab-tests", "method": "GET", "expected_fields": ["code", "name"]},
            {"endpoint": "/lab-orders", "method": "GET", "expected_fields": ["order_number"]},
            {"endpoint": "/lab-results", "method": "GET", "expected_fields": ["test_code"]},
        ],
        "Lab orders, LOINC codes, results management, integration"
    )
    
    # 10. Insurance Verification
    assess_module(
        "Insurance Verification",
        [
            {"endpoint": "/insurance-cards", "method": "GET", "expected_fields": ["member_id", "payer_name"]},
            {"endpoint": "/eligibility-responses", "method": "GET", "expected_fields": ["eligibility_status"]},
            {"endpoint": "/prior-authorizations", "method": "GET", "expected_fields": ["auth_number"]},
        ],
        "Eligibility checking, prior authorization, claims management"
    )
    
    # 11. Clinical Templates & Protocols
    assess_module(
        "Clinical Templates & Protocols",
        [
            {"endpoint": "/clinical-templates/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/clinical-templates", "method": "GET", "expected_fields": ["name", "template_type"]},
            {"endpoint": "/clinical-protocols", "method": "GET", "expected_fields": ["protocol_name"]},
        ],
        "Standardized care workflows, clinical decision support"
    )
    
    # 12. Quality Measures & Reporting
    assess_module(
        "Quality Measures & Reporting",
        [
            {"endpoint": "/quality-measures/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/quality-measures", "method": "GET", "expected_fields": ["measure_name"]},
            {"endpoint": "/quality-reports", "method": "GET", "expected_fields": ["report_type"]},
        ],
        "Performance tracking, compliance reporting, quality metrics"
    )
    
    # 13. Patient Portal
    assess_module(
        "Patient Portal",
        [
            {"endpoint": "/patient-portal/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/patient-portal/access", "method": "GET", "expected_fields": ["patient_id"]},
            {"endpoint": "/patient-messages", "method": "GET", "expected_fields": ["message_type"]},
        ],
        "Patient-facing interface, appointment booking, secure messaging"
    )
    
    # 14. Document Management
    assess_module(
        "Document Management",
        [
            {"endpoint": "/documents/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/documents", "method": "GET", "expected_fields": ["document_name"]},
            {"endpoint": "/document-workflows", "method": "GET", "expected_fields": ["workflow_name"]},
        ],
        "Clinical documents, workflow management, approvals"
    )
    
    # 15. Telehealth Module
    assess_module(
        "Telehealth Module",
        [
            {"endpoint": "/telehealth/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/telehealth-sessions", "method": "GET", "expected_fields": ["session_id"]},
            {"endpoint": "/telehealth-sessions", "method": "POST", "data": {
                "patient_id": "test-patient", "provider_id": "test-provider",
                "scheduled_start": datetime.now().isoformat()
            }, "expected_fields": ["id"]},
        ],
        "Video consultations, session management, remote care"
    )
    
    # 16. Referral Management
    assess_module(
        "Referral Management",
        [
            {"endpoint": "/referrals/init", "method": "POST", "expected_fields": ["message"]},
            {"endpoint": "/referrals", "method": "GET", "expected_fields": ["referral_number"]},
            {"endpoint": "/referral-reports", "method": "GET", "expected_fields": ["report_type"]},
        ],
        "Provider coordination, referral tracking, specialist communication"
    )

def generate_report():
    """Generate comprehensive assessment report"""
    print("\n" + "=" * 80)
    print("📊 CLINICHUB COMPREHENSIVE MODULE ASSESSMENT REPORT")
    print("=" * 80)
    
    for module_name, results in assessment_results.items():
        print(f"\nMODULE NAME: {module_name}")
        print(f"Status: {results['status']}")
        print(f"Backend API: {results['backend_api_complete']}% complete")
        
        if results['key_endpoints']:
            print(f"Key Endpoints: {', '.join(results['key_endpoints'][:3])}")
        
        # Determine missing features based on status
        if results['status'] == 'Missing':
            results['missing_features'] = ["All core functionality", "API endpoints", "Data models"]
        elif results['status'] == 'Basic':
            results['missing_features'] = ["Advanced features", "Integration capabilities", "Production optimizations"]
        elif results['status'] == 'Partial':
            results['missing_features'] = ["Some endpoints", "Error handling", "Validation"]
        else:
            results['missing_features'] = ["Minor optimizations"]
        
        print(f"Missing Features: {', '.join(results['missing_features'])}")
        
        # Set dependencies
        if 'patient' in module_name.lower() or 'ehr' in module_name.lower():
            results['dependencies'] = ["Authentication System"]
        elif 'employee' in module_name.lower():
            results['dependencies'] = ["Authentication System", "User Management"]
        else:
            results['dependencies'] = ["Authentication System", "Patient/EHR Management"]
        
        print(f"Dependencies: {', '.join(results['dependencies'])}")
        print(f"Priority: {results['priority']} for completion")
        print("-" * 60)

if __name__ == "__main__":
    if authenticate():
        run_comprehensive_assessment()
        generate_report()
    else:
        print("❌ Cannot proceed without authentication")