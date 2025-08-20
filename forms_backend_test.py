#!/usr/bin/env python3
"""
Comprehensive Forms System Testing for ClinicHub
Tests all forms functionality including CRUD operations, validation, exports, and audit logging.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, date
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://e74b3bf4-8f20-4982-9905-3152224072c7.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

class FormsTestSuite:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_forms = []
        self.created_submissions = []
        
    async def setup(self):
        """Initialize test session and authenticate"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        
    async def teardown(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=TEST_CREDENTIALS
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.log_result("Authentication", True, "Successfully authenticated with admin credentials")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Authentication", False, f"Failed to authenticate: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
            
    def get_headers(self):
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_phase_1_form_management(self):
        """Phase 1: Form Management - Create, publish, list, and get forms"""
        print("\n🔧 PHASE 1: FORM MANAGEMENT")
        
        # Test 1.1: Create patient intake form
        patient_intake_schema = {
            "fields": [
                {
                    "key": "first_name",
                    "type": "text",
                    "label": "First Name",
                    "required": True
                },
                {
                    "key": "last_name", 
                    "type": "text",
                    "label": "Last Name",
                    "required": True
                },
                {
                    "key": "email",
                    "type": "email", 
                    "label": "Email Address",
                    "required": True
                },
                {
                    "key": "phone",
                    "type": "phone",
                    "label": "Phone Number",
                    "required": True
                },
                {
                    "key": "date_of_birth",
                    "type": "date",
                    "label": "Date of Birth",
                    "required": True
                },
                {
                    "key": "gender",
                    "type": "select",
                    "label": "Gender",
                    "options": ["Male", "Female", "Other", "Prefer not to say"],
                    "required": False
                },
                {
                    "key": "emergency_contact",
                    "type": "text",
                    "label": "Emergency Contact Name",
                    "required": True
                },
                {
                    "key": "emergency_phone",
                    "type": "phone",
                    "label": "Emergency Contact Phone",
                    "required": True
                },
                {
                    "key": "insurance_provider",
                    "type": "text",
                    "label": "Insurance Provider",
                    "required": False
                },
                {
                    "key": "insurance_id",
                    "type": "text",
                    "label": "Insurance ID Number",
                    "required": False
                },
                {
                    "key": "medical_history",
                    "type": "textarea",
                    "label": "Medical History",
                    "required": False
                },
                {
                    "key": "current_medications",
                    "type": "textarea",
                    "label": "Current Medications",
                    "required": False
                },
                {
                    "key": "allergies",
                    "type": "textarea",
                    "label": "Known Allergies",
                    "required": False
                },
                {
                    "key": "consent_treatment",
                    "type": "checkbox",
                    "label": "I consent to medical treatment",
                    "required": True
                },
                {
                    "key": "consent_privacy",
                    "type": "checkbox", 
                    "label": "I acknowledge the privacy policy",
                    "required": True
                }
            ]
        }
        
        form_data = {
            "name": "Patient Intake Form",
            "key": "patient-intake-test",
            "schema": patient_intake_schema,
            "status": "draft",
            "version": 1,
            "meta": {
                "description": "Comprehensive patient intake form for new patients",
                "category": "intake"
            }
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/forms",
                headers=self.get_headers(),
                json=form_data
            ) as response:
                if response.status == 200:
                    form = await response.json()
                    self.created_forms.append(form["_id"])
                    self.log_result("Create Patient Intake Form", True, f"Created form with ID: {form['_id']}")
                    
                    # Store form for later tests
                    self.patient_intake_form = form
                else:
                    error_text = await response.text()
                    self.log_result("Create Patient Intake Form", False, f"Failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.log_result("Create Patient Intake Form", False, f"Error: {str(e)}")
            return False
            
        # Test 1.2: Publish the form (should increment version to 2)
        try:
            form_id = self.patient_intake_form["_id"]
            async with self.session.post(
                f"{API_BASE}/forms/{form_id}/publish",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    published_form = await response.json()
                    if published_form["status"] == "published" and published_form["version"] == 2:
                        self.log_result("Publish Form", True, f"Form published successfully, version incremented to {published_form['version']}")
                        self.patient_intake_form = published_form
                    else:
                        self.log_result("Publish Form", False, f"Form status: {published_form['status']}, version: {published_form['version']}")
                else:
                    error_text = await response.text()
                    self.log_result("Publish Form", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Publish Form", False, f"Error: {str(e)}")
            
        # Test 1.3: List forms and verify status filtering
        try:
            # Test listing all forms
            async with self.session.get(
                f"{API_BASE}/forms",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    all_forms = await response.json()
                    self.log_result("List All Forms", True, f"Retrieved {len(all_forms)} forms")
                else:
                    self.log_result("List All Forms", False, f"Failed: {response.status}")
                    
            # Test filtering by published status
            async with self.session.get(
                f"{API_BASE}/forms?status=published",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    published_forms = await response.json()
                    published_count = len([f for f in published_forms if f["status"] == "published"])
                    self.log_result("List Published Forms", True, f"Retrieved {published_count} published forms")
                else:
                    self.log_result("List Published Forms", False, f"Failed: {response.status}")
                    
        except Exception as e:
            self.log_result("List Forms", False, f"Error: {str(e)}")
            
        # Test 1.4: Get form by key and verify published status
        try:
            async with self.session.get(
                f"{API_BASE}/forms/by-key/patient-intake-test?published_only=true",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    form = await response.json()
                    if form["status"] == "published" and form["key"] == "patient-intake-test":
                        self.log_result("Get Form by Key", True, f"Retrieved published form: {form['name']}")
                    else:
                        self.log_result("Get Form by Key", False, f"Form status: {form['status']}, key: {form['key']}")
                else:
                    error_text = await response.text()
                    self.log_result("Get Form by Key", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Get Form by Key", False, f"Error: {str(e)}")
            
        return True
        
    async def test_phase_2_form_submissions(self):
        """Phase 2: Form Submissions - Submit forms with validation testing"""
        print("\n📝 PHASE 2: FORM SUBMISSIONS")
        
        if not hasattr(self, 'patient_intake_form'):
            self.log_result("Form Submissions Setup", False, "Patient intake form not available from Phase 1")
            return False
            
        # Test 2.1: Submit valid patient intake form
        valid_submission_data = {
            "data": {
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "email": "maria.rodriguez@email.com",
                "phone": "(555) 123-4567",
                "date_of_birth": "1985-03-15",
                "gender": "Female",
                "emergency_contact": "Carlos Rodriguez",
                "emergency_phone": "(555) 987-6543",
                "insurance_provider": "Blue Cross Blue Shield",
                "insurance_id": "BC123456789",
                "medical_history": "Hypertension, managed with medication. No surgeries.",
                "current_medications": "Lisinopril 10mg daily, Metformin 500mg twice daily",
                "allergies": "Penicillin (rash), Shellfish (mild reaction)",
                "consent_treatment": True,
                "consent_privacy": True
            }
        }
        
        try:
            form_id = self.patient_intake_form["_id"]
            async with self.session.post(
                f"{API_BASE}/forms/{form_id}/submit",
                headers=self.get_headers(),
                json=valid_submission_data
            ) as response:
                if response.status == 200:
                    submission = await response.json()
                    self.created_submissions.append(submission["_id"])
                    self.log_result("Submit Valid Form", True, f"Submission created with ID: {submission['_id']}")
                    self.first_submission = submission
                else:
                    error_text = await response.text()
                    self.log_result("Submit Valid Form", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Submit Valid Form", False, f"Error: {str(e)}")
            
        # Test 2.2: Submit second valid form with different data
        second_submission_data = {
            "data": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@email.com", 
                "phone": "555-234-5678",
                "date_of_birth": "1978-11-22",
                "gender": "Male",
                "emergency_contact": "Jane Smith",
                "emergency_phone": "555-876-5432",
                "insurance_provider": "Aetna",
                "insurance_id": "AET987654321",
                "medical_history": "Diabetes Type 2, well controlled. Previous appendectomy in 2010.",
                "current_medications": "Metformin 1000mg twice daily, Atorvastatin 20mg daily",
                "allergies": "None known",
                "consent_treatment": True,
                "consent_privacy": True
            }
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/forms/{form_id}/submit",
                headers=self.get_headers(),
                json=second_submission_data
            ) as response:
                if response.status == 200:
                    submission = await response.json()
                    self.created_submissions.append(submission["_id"])
                    self.log_result("Submit Second Valid Form", True, f"Second submission created with ID: {submission['_id']}")
                else:
                    error_text = await response.text()
                    self.log_result("Submit Second Valid Form", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Submit Second Valid Form", False, f"Error: {str(e)}")
            
        # Test 2.3: Test form validation - missing required fields
        invalid_submission_missing_required = {
            "data": {
                "first_name": "Test",
                # Missing last_name (required)
                "email": "test@email.com",
                # Missing phone (required)
                "date_of_birth": "1990-01-01",
                "gender": "Other"
                # Missing emergency_contact (required)
                # Missing consent_treatment (required)
                # Missing consent_privacy (required)
            }
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/forms/{form_id}/submit",
                headers=self.get_headers(),
                json=invalid_submission_missing_required
            ) as response:
                if response.status == 400:
                    error_data = await response.json()
                    # Check for validation_errors in detail field (FastAPI standard)
                    validation_errors = error_data.get("detail", {}).get("validation_errors") or error_data.get("validation_errors")
                    if validation_errors:
                        self.log_result("Validation - Missing Required Fields", True, f"Correctly rejected submission with validation errors: {len(validation_errors)} errors")
                    else:
                        self.log_result("Validation - Missing Required Fields", False, f"Expected validation_errors in response: {error_data}")
                else:
                    self.log_result("Validation - Missing Required Fields", False, f"Expected 400 status, got {response.status}")
        except Exception as e:
            self.log_result("Validation - Missing Required Fields", False, f"Error: {str(e)}")
            
        # Test 2.4: Test data type validation
        invalid_submission_bad_types = {
            "data": {
                "first_name": "Test",
                "last_name": "User",
                "email": "not-an-email",  # Invalid email format
                "phone": "123",  # Too short phone number
                "date_of_birth": "not-a-date",  # Invalid date format
                "gender": "InvalidGender",  # Not in options list
                "emergency_contact": "Emergency Contact",
                "emergency_phone": "(555) 123-4567",
                "consent_treatment": True,
                "consent_privacy": True
            }
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/forms/{form_id}/submit",
                headers=self.get_headers(),
                json=invalid_submission_bad_types
            ) as response:
                if response.status == 400:
                    error_data = await response.json()
                    if "validation_errors" in error_data:
                        self.log_result("Validation - Data Types", True, f"Correctly rejected submission with type validation errors: {len(error_data['validation_errors'])} errors")
                    else:
                        self.log_result("Validation - Data Types", False, "Expected validation_errors in response")
                else:
                    self.log_result("Validation - Data Types", False, f"Expected 400 status, got {response.status}")
        except Exception as e:
            self.log_result("Validation - Data Types", False, f"Error: {str(e)}")
            
        # Test 2.5: List submissions and verify data integrity
        try:
            async with self.session.get(
                f"{API_BASE}/forms/{form_id}/submissions",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    submissions_data = await response.json()
                    submissions = submissions_data.get("items", [])
                    if len(submissions) >= 2:
                        self.log_result("List Submissions", True, f"Retrieved {len(submissions)} submissions with correct data structure")
                        
                        # Verify data integrity of first submission
                        first_sub = submissions[0] if submissions[0]["_id"] == self.first_submission["_id"] else submissions[1]
                        if (first_sub["data"]["first_name"] == "Maria" and 
                            first_sub["data"]["email"] == "maria.rodriguez@email.com"):
                            self.log_result("Data Integrity Check", True, "Submission data matches original input")
                        else:
                            self.log_result("Data Integrity Check", False, "Submission data does not match original input")
                    else:
                        self.log_result("List Submissions", False, f"Expected at least 2 submissions, got {len(submissions)}")
                else:
                    error_text = await response.text()
                    self.log_result("List Submissions", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("List Submissions", False, f"Error: {str(e)}")
            
        return True
        
    async def test_phase_3_export_testing(self):
        """Phase 3: Export Testing - CSV and PDF exports"""
        print("\n📊 PHASE 3: EXPORT TESTING")
        
        if not hasattr(self, 'patient_intake_form'):
            self.log_result("Export Testing Setup", False, "Patient intake form not available")
            return False
            
        form_id = self.patient_intake_form["_id"]
        
        # Test 3.1: Export submissions as CSV
        try:
            async with self.session.get(
                f"{API_BASE}/forms/{form_id}/submissions.csv",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    csv_content = await response.text()
                    # Verify CSV structure
                    lines = csv_content.strip().split('\n')
                    if len(lines) >= 2:  # Header + at least 1 data row
                        headers = lines[0].split(',')
                        expected_fields = ["first_name", "last_name", "email", "phone", "_id", "_created_at"]
                        has_expected_fields = all(field in headers for field in expected_fields)
                        if has_expected_fields:
                            self.log_result("CSV Export", True, f"CSV exported with {len(lines)-1} data rows and correct structure")
                        else:
                            self.log_result("CSV Export", False, f"CSV missing expected fields. Headers: {headers}")
                    else:
                        self.log_result("CSV Export", False, f"CSV has insufficient data: {len(lines)} lines")
                else:
                    error_text = await response.text()
                    self.log_result("CSV Export", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("CSV Export", False, f"Error: {str(e)}")
            
        # Test 3.2: Export individual submission PDF
        if hasattr(self, 'first_submission'):
            try:
                submission_id = self.first_submission["_id"]
                async with self.session.get(
                    f"{API_BASE}/forms/submissions/{submission_id}.pdf",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        pdf_content = await response.read()
                        if len(pdf_content) > 1000 and pdf_content.startswith(b'%PDF'):
                            self.log_result("Individual PDF Export", True, f"PDF exported successfully ({len(pdf_content)} bytes)")
                        else:
                            self.log_result("Individual PDF Export", False, f"Invalid PDF content ({len(pdf_content)} bytes)")
                    else:
                        error_text = await response.text()
                        self.log_result("Individual PDF Export", False, f"Failed: {response.status} - {error_text}")
            except Exception as e:
                self.log_result("Individual PDF Export", False, f"Error: {str(e)}")
        else:
            self.log_result("Individual PDF Export", False, "No submission available for PDF export")
            
        # Test 3.3: Export form summary PDF
        try:
            async with self.session.get(
                f"{API_BASE}/forms/{form_id}/summary.pdf",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    pdf_content = await response.read()
                    if len(pdf_content) > 1000 and pdf_content.startswith(b'%PDF'):
                        self.log_result("Summary PDF Export", True, f"Summary PDF exported successfully ({len(pdf_content)} bytes)")
                    else:
                        self.log_result("Summary PDF Export", False, f"Invalid PDF content ({len(pdf_content)} bytes)")
                else:
                    error_text = await response.text()
                    self.log_result("Summary PDF Export", False, f"Failed: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Summary PDF Export", False, f"Error: {str(e)}")
            
        return True
        
    async def test_phase_4_audit_notifications(self):
        """Phase 4: Audit & Notifications - Verify audit logs and notifications"""
        print("\n🔍 PHASE 4: AUDIT & NOTIFICATIONS")
        
        # Test 4.1: Verify audit logs are created for form operations
        try:
            async with self.session.get(
                f"{API_BASE}/audit?subject_type=form&limit=20",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    audit_logs = await response.json()
                    form_actions = ["forms.create", "forms.publish", "forms.submit", "forms.export.csv", "forms.export.pdf", "forms.export.summary_pdf"]
                    found_actions = [log["action"] for log in audit_logs if log["action"] in form_actions]
                    
                    if len(found_actions) >= 3:  # At least create, publish, submit
                        self.log_result("Audit Logs", True, f"Found {len(found_actions)} form-related audit entries: {set(found_actions)}")
                    else:
                        self.log_result("Audit Logs", False, f"Expected more audit entries, found: {found_actions}")
                else:
                    error_text = await response.text()
                    self.log_result("Audit Logs", False, f"Failed to retrieve audit logs: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Audit Logs", False, f"Error: {str(e)}")
            
        # Test 4.2: Verify notifications are sent for form operations
        try:
            async with self.session.get(
                f"{API_BASE}/notifications?limit=20",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    notifications = await response.json()
                    form_notifications = [n for n in notifications if n.get("type", "").startswith("forms.")]
                    
                    if len(form_notifications) >= 2:  # At least create and publish notifications
                        self.log_result("Notifications", True, f"Found {len(form_notifications)} form-related notifications")
                    else:
                        self.log_result("Notifications", False, f"Expected more form notifications, found: {len(form_notifications)}")
                else:
                    error_text = await response.text()
                    self.log_result("Notifications", False, f"Failed to retrieve notifications: {response.status} - {error_text}")
        except Exception as e:
            self.log_result("Notifications", False, f"Error: {str(e)}")
            
        # Test 4.3: Test error handling and edge cases
        # Try to submit to non-existent form
        try:
            async with self.session.post(
                f"{API_BASE}/forms/non-existent-form/submit",
                headers=self.get_headers(),
                json={"data": {"test": "value"}}
            ) as response:
                if response.status == 404:
                    self.log_result("Error Handling - Non-existent Form", True, "Correctly returned 404 for non-existent form")
                else:
                    self.log_result("Error Handling - Non-existent Form", False, f"Expected 404, got {response.status}")
        except Exception as e:
            self.log_result("Error Handling - Non-existent Form", False, f"Error: {str(e)}")
            
        # Try to get non-existent submission PDF
        try:
            async with self.session.get(
                f"{API_BASE}/forms/submissions/non-existent-submission.pdf",
                headers=self.get_headers()
            ) as response:
                if response.status == 404:
                    self.log_result("Error Handling - Non-existent Submission", True, "Correctly returned 404 for non-existent submission")
                else:
                    self.log_result("Error Handling - Non-existent Submission", False, f"Expected 404, got {response.status}")
        except Exception as e:
            self.log_result("Error Handling - Non-existent Submission", False, f"Error: {str(e)}")
            
        return True
        
    async def test_phase_5_advanced_features(self):
        """Phase 5: Advanced Features - Form deletion, versioning, filtering"""
        print("\n🚀 PHASE 5: ADVANCED FEATURES")
        
        # Test 5.1: Create a test form for deletion
        test_form_data = {
            "name": "Test Form for Deletion",
            "key": "test-form-delete",
            "schema": {
                "fields": [
                    {
                        "key": "test_field",
                        "type": "text",
                        "label": "Test Field",
                        "required": True
                    }
                ]
            },
            "status": "draft",
            "version": 1
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/forms",
                headers=self.get_headers(),
                json=test_form_data
            ) as response:
                if response.status == 200:
                    test_form = await response.json()
                    self.log_result("Create Test Form for Deletion", True, f"Created test form: {test_form['_id']}")
                    
                    # Test 5.2: Try to delete form without cascade (should fail if has submissions)
                    # First add a submission
                    await self.session.post(
                        f"{API_BASE}/forms/{test_form['_id']}/publish",
                        headers=self.get_headers()
                    )
                    
                    await self.session.post(
                        f"{API_BASE}/forms/{test_form['_id']}/submit",
                        headers=self.get_headers(),
                        json={"data": {"test_field": "test value"}}
                    )
                    
                    # Now try to delete without cascade
                    async with self.session.delete(
                        f"{API_BASE}/forms/{test_form['_id']}?cascade=false",
                        headers=self.get_headers()
                    ) as delete_response:
                        if delete_response.status == 400:
                            self.log_result("Delete Form Without Cascade", True, "Correctly prevented deletion of form with submissions")
                        else:
                            self.log_result("Delete Form Without Cascade", False, f"Expected 400, got {delete_response.status}")
                    
                    # Test 5.3: Delete form with cascade
                    async with self.session.delete(
                        f"{API_BASE}/forms/{test_form['_id']}?cascade=true",
                        headers=self.get_headers()
                    ) as delete_response:
                        if delete_response.status == 200:
                            delete_result = await delete_response.json()
                            if delete_result.get("deleted") and delete_result.get("submissions_deleted", 0) > 0:
                                self.log_result("Delete Form With Cascade", True, f"Successfully deleted form and {delete_result['submissions_deleted']} submissions")
                            else:
                                self.log_result("Delete Form With Cascade", False, "Form deleted but submission count incorrect")
                        else:
                            error_text = await delete_response.text()
                            self.log_result("Delete Form With Cascade", False, f"Failed: {delete_response.status} - {error_text}")
                            
                else:
                    self.log_result("Create Test Form for Deletion", False, f"Failed to create test form: {response.status}")
        except Exception as e:
            self.log_result("Advanced Features - Form Deletion", False, f"Error: {str(e)}")
            
        # Test 5.4: Test form update/versioning workflow
        if hasattr(self, 'patient_intake_form'):
            try:
                # Update the form schema
                updated_form_data = {
                    "name": "Updated Patient Intake Form",
                    "key": "patient-intake-test",
                    "schema": {
                        "fields": [
                            {
                                "key": "first_name",
                                "type": "text",
                                "label": "First Name",
                                "required": True
                            },
                            {
                                "key": "last_name",
                                "type": "text", 
                                "label": "Last Name",
                                "required": True
                            },
                            {
                                "key": "email",
                                "type": "email",
                                "label": "Email Address",
                                "required": True
                            },
                            {
                                "key": "preferred_language",
                                "type": "select",
                                "label": "Preferred Language",
                                "options": ["English", "Spanish", "French", "Other"],
                                "required": False
                            }
                        ]
                    },
                    "status": "draft",
                    "version": 3
                }
                
                async with self.session.post(
                    f"{API_BASE}/forms?upsert=true",
                    headers=self.get_headers(),
                    json=updated_form_data
                ) as response:
                    if response.status == 200:
                        updated_form = await response.json()
                        if updated_form["name"] == "Updated Patient Intake Form" and updated_form["version"] == 3:
                            self.log_result("Form Update/Versioning", True, f"Successfully updated form to version {updated_form['version']}")
                        else:
                            self.log_result("Form Update/Versioning", False, f"Update failed: name={updated_form['name']}, version={updated_form['version']}")
                    else:
                        error_text = await response.text()
                        self.log_result("Form Update/Versioning", False, f"Failed: {response.status} - {error_text}")
            except Exception as e:
                self.log_result("Form Update/Versioning", False, f"Error: {str(e)}")
                
        # Test 5.5: Test filtering and querying capabilities
        try:
            # Test filtering by status
            async with self.session.get(
                f"{API_BASE}/forms?status=published&limit=10",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    published_forms = await response.json()
                    all_published = all(form["status"] == "published" for form in published_forms)
                    if all_published:
                        self.log_result("Filtering by Status", True, f"Successfully filtered {len(published_forms)} published forms")
                    else:
                        self.log_result("Filtering by Status", False, "Some forms in result are not published")
                else:
                    self.log_result("Filtering by Status", False, f"Failed: {response.status}")
                    
            # Test submissions filtering by date
            if hasattr(self, 'patient_intake_form'):
                form_id = self.patient_intake_form["_id"]
                since_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                async with self.session.get(
                    f"{API_BASE}/forms/{form_id}/submissions?since={since_date}&limit=5",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        submissions_data = await response.json()
                        submissions = submissions_data.get("items", [])
                        self.log_result("Submissions Date Filtering", True, f"Retrieved {len(submissions)} submissions since {since_date}")
                    else:
                        self.log_result("Submissions Date Filtering", False, f"Failed: {response.status}")
                        
        except Exception as e:
            self.log_result("Filtering and Querying", False, f"Error: {str(e)}")
            
        return True
        
    async def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        
        # Delete created forms (with cascade to remove submissions)
        for form_id in self.created_forms:
            try:
                async with self.session.delete(
                    f"{API_BASE}/forms/{form_id}?cascade=true",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        print(f"✅ Cleaned up form: {form_id}")
                    else:
                        print(f"⚠️ Failed to clean up form: {form_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up form {form_id}: {str(e)}")
                
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*80)
        print("🏥 CLINICHUB FORMS SYSTEM TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
                    
        print(f"\n🎯 FORMS SYSTEM STATUS:")
        
        # Categorize results by phase
        phases = {
            "Phase 1 - Form Management": [r for r in self.test_results if any(x in r["test"] for x in ["Create Patient", "Publish Form", "List", "Get Form"])],
            "Phase 2 - Form Submissions": [r for r in self.test_results if any(x in r["test"] for x in ["Submit", "Validation", "Data Integrity"])],
            "Phase 3 - Export Testing": [r for r in self.test_results if any(x in r["test"] for x in ["CSV Export", "PDF Export"])],
            "Phase 4 - Audit & Notifications": [r for r in self.test_results if any(x in r["test"] for x in ["Audit", "Notifications", "Error Handling"])],
            "Phase 5 - Advanced Features": [r for r in self.test_results if any(x in r["test"] for x in ["Delete", "Update", "Filtering"])]
        }
        
        for phase_name, phase_results in phases.items():
            if phase_results:
                phase_passed = len([r for r in phase_results if r["success"]])
                phase_total = len(phase_results)
                phase_rate = (phase_passed / phase_total * 100) if phase_total > 0 else 0
                status = "✅ EXCELLENT" if phase_rate >= 90 else "🟡 GOOD" if phase_rate >= 70 else "❌ NEEDS WORK"
                print(f"   {status} {phase_name}: {phase_passed}/{phase_total} ({phase_rate:.0f}%)")
                
        print(f"\n🔧 SYSTEM ASSESSMENT:")
        if success_rate >= 90:
            print("   🎉 EXCELLENT - Forms system is production-ready with comprehensive functionality")
        elif success_rate >= 80:
            print("   ✅ GOOD - Forms system is functional with minor issues to address")
        elif success_rate >= 60:
            print("   🟡 FAIR - Forms system has core functionality but needs improvements")
        else:
            print("   ❌ POOR - Forms system has significant issues requiring immediate attention")
            
        print("="*80)

async def main():
    """Main test execution"""
    print("🏥 CLINICHUB FORMS SYSTEM COMPREHENSIVE TESTING")
    print("="*80)
    print("Testing comprehensive forms system with schema validation, submissions, and exports")
    print("="*80)
    
    test_suite = FormsTestSuite()
    
    try:
        # Setup
        await test_suite.setup()
        
        if not test_suite.auth_token:
            print("❌ CRITICAL: Authentication failed. Cannot proceed with testing.")
            return
            
        # Execute test phases
        await test_suite.test_phase_1_form_management()
        await test_suite.test_phase_2_form_submissions()
        await test_suite.test_phase_3_export_testing()
        await test_suite.test_phase_4_audit_notifications()
        await test_suite.test_phase_5_advanced_features()
        
        # Cleanup
        await test_suite.cleanup_test_data()
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        
    finally:
        # Print summary
        test_suite.print_summary()
        
        # Cleanup
        await test_suite.teardown()

if __name__ == "__main__":
    asyncio.run(main())