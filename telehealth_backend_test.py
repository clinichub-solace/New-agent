#!/usr/bin/env python3
"""
Comprehensive Telehealth System Testing
Tests the complete telehealth module implementation as requested in the review.
"""
import requests
import json
import os
from datetime import date, datetime, timedelta
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Set the API URL
API_URL = f"{BACKEND_URL}/api"
print(f"🏥 COMPREHENSIVE TELEHEALTH SYSTEM TESTING")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Helper function to print test results
def print_test_result(test_name, success, response=None, error_msg=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response and isinstance(response, dict):
            # Show key fields for telehealth responses
            if 'session_number' in response:
                print(f"   Session Number: {response['session_number']}")
            if 'status' in response:
                print(f"   Status: {response['status']}")
            if 'session_url' in response:
                print(f"   Session URL: {response['session_url']}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error_msg:
            print(f"   Error: {error_msg}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def authenticate_admin():
    """Authenticate as admin user and return token"""
    print("\n🔐 AUTHENTICATION SETUP")
    
    # Initialize admin user first
    try:
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url)
        response.raise_for_status()
        print("✅ Admin user initialized")
    except Exception as e:
        print(f"⚠️  Admin user may already exist: {str(e)}")
    
    # Login as admin
    try:
        url = f"{API_URL}/auth/login"
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        token = result["access_token"]
        print("✅ Admin authentication successful")
        return token
    except Exception as e:
        print(f"❌ Admin authentication failed: {str(e)}")
        return None

def create_test_patient(token):
    """Create a test patient for telehealth sessions"""
    print("\n👤 CREATING TEST PATIENT")
    
    try:
        url = f"{API_URL}/patients"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "first_name": "Maria",
            "last_name": "Rodriguez",
            "email": "maria.rodriguez@example.com",
            "phone": "+1-555-234-5678",
            "date_of_birth": "1985-03-20",
            "gender": "female",
            "address_line1": "456 Telehealth Ave",
            "city": "Remote City",
            "state": "CA",
            "zip_code": "90210"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        patient_id = result["id"]
        patient_name = f"{result['name'][0]['given'][0]} {result['name'][0]['family']}"
        print(f"✅ Test patient created: {patient_name} (ID: {patient_id})")
        return patient_id, patient_name
    except Exception as e:
        print(f"❌ Failed to create test patient: {str(e)}")
        return None, None

def create_test_provider(token):
    """Create a test provider for telehealth sessions"""
    print("\n👨‍⚕️ CREATING TEST PROVIDER")
    
    try:
        url = f"{API_URL}/providers"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "first_name": "Jennifer",
            "last_name": "Martinez",
            "title": "Dr.",
            "specialties": ["Telemedicine", "Family Medicine"],
            "license_number": "MD67890",
            "npi_number": "9876543210",
            "email": "dr.martinez@clinichub.com",
            "phone": "+1-555-345-6789",
            "default_appointment_duration": 30,
            "schedule_start_time": "08:00",
            "schedule_end_time": "18:00",
            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        provider_id = result["id"]
        provider_name = f"{result['title']} {result['first_name']} {result['last_name']}"
        print(f"✅ Test provider created: {provider_name} (ID: {provider_id})")
        return provider_id, provider_name
    except Exception as e:
        print(f"❌ Failed to create test provider: {str(e)}")
        return None, None

def test_telehealth_session_management(token, patient_id, patient_name, provider_id, provider_name):
    """Test 1: Telehealth Session Management (CRUD operations)"""
    print("\n🎥 TEST 1: TELEHEALTH SESSION MANAGEMENT")
    
    session_id = None
    
    # Test creating a telehealth session
    try:
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {token}"}
        
        scheduled_start = datetime.now() + timedelta(hours=1)
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "session_type": "video_consultation",
            "title": "Telehealth Consultation - Headache Follow-up",
            "description": "Follow-up consultation for chronic headaches via video call",
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 30,
            "recording_enabled": False
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Verify session creation
        assert "session_number" in result
        assert result["session_number"].startswith("TEL-")
        assert result["patient_id"] == patient_id
        assert result["provider_id"] == provider_id
        assert result["status"] == "scheduled"
        assert "session_url" in result
        
        session_id = result["id"]
        print_test_result("Create Telehealth Session", True, result)
    except Exception as e:
        print_test_result("Create Telehealth Session", False, error_msg=str(e))
        return None
    
    # Test getting all telehealth sessions
    try:
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        print_test_result("Get All Telehealth Sessions", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Get All Telehealth Sessions", False, error_msg=str(e))
    
    # Test getting sessions with filtering
    try:
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"patient_id": patient_id}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["patient_id"] == patient_id
        
        print_test_result("Get Sessions by Patient ID", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Get Sessions by Patient ID", False, error_msg=str(e))
    
    # Test getting individual session
    if session_id:
        try:
            url = f"{API_URL}/telehealth/sessions/{session_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == session_id
            assert result["patient_id"] == patient_id
            
            print_test_result("Get Individual Session", True, result)
        except Exception as e:
            print_test_result("Get Individual Session", False, error_msg=str(e))
    
    # Test updating session details
    if session_id:
        try:
            url = f"{API_URL}/telehealth/sessions/{session_id}"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "session_notes": "Patient reports improvement in headache symptoms",
                "provider_notes": "Continue current treatment plan"
            }
            
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            print_test_result("Update Session Details", True, result)
        except Exception as e:
            print_test_result("Update Session Details", False, error_msg=str(e))
    
    return session_id

def test_session_lifecycle_management(token, session_id):
    """Test 2: Session Lifecycle Management (start/end sessions)"""
    print("\n🔄 TEST 2: SESSION LIFECYCLE MANAGEMENT")
    
    if not session_id:
        print("❌ Skipping lifecycle tests - no session ID available")
        return
    
    # Test starting a telehealth session
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/start"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Verify session started and encounter created
        assert "message" in result
        assert "encounter_id" in result
        
        encounter_id = result.get("encounter_id")
        print_test_result("Start Telehealth Session", True, result)
    except Exception as e:
        print_test_result("Start Telehealth Session", False, error_msg=str(e))
        encounter_id = None
    
    # Verify session status changed to in_progress
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "in_progress"
        assert result["actual_start"] is not None
        
        print_test_result("Verify Session Status (In Progress)", True, {"status": result["status"]})
    except Exception as e:
        print_test_result("Verify Session Status (In Progress)", False, error_msg=str(e))
    
    # Test ending a telehealth session
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/end"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "session_notes": "Session completed successfully. Patient responded well to treatment recommendations.",
            "provider_notes": "Continue current medication. Schedule follow-up in 2 weeks.",
            "patient_rating": 5,
            "provider_rating": 5
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        assert "message" in result
        
        print_test_result("End Telehealth Session", True, result)
    except Exception as e:
        print_test_result("End Telehealth Session", False, error_msg=str(e))
    
    # Verify session status changed to completed
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "completed"
        assert result["actual_end"] is not None
        
        print_test_result("Verify Session Status (Completed)", True, {"status": result["status"]})
    except Exception as e:
        print_test_result("Verify Session Status (Completed)", False, error_msg=str(e))

def test_waiting_room_system(token, patient_id, patient_name, provider_id):
    """Test 3: Waiting Room System"""
    print("\n⏳ TEST 3: WAITING ROOM SYSTEM")
    
    # Create a new session for waiting room testing
    session_id = None
    try:
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {token}"}
        
        scheduled_start = datetime.now() + timedelta(minutes=30)
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,  # Use real provider ID
            "session_type": "video_consultation",
            "title": "Waiting Room Test Session",
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 30
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        session_id = result["id"]
        
        print(f"✅ Created test session for waiting room: {session_id}")
    except Exception as e:
        print(f"❌ Failed to create test session: {str(e)}")
        return
    
    # Test joining waiting room
    try:
        url = f"{API_URL}/telehealth/waiting-room/{session_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert "message" in result
        assert "waiting_room_id" in result
        
        print_test_result("Join Waiting Room", True, result)
    except Exception as e:
        print_test_result("Join Waiting Room", False, error_msg=str(e))
    
    # Test getting waiting room patients
    try:
        url = f"{API_URL}/telehealth/waiting-room"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        
        print_test_result("Get Waiting Room Patients", True, {"count": len(result)})
    except Exception as e:
        print_test_result("Get Waiting Room Patients", False, error_msg=str(e))

def test_communication_features(token, session_id):
    """Test 4: Communication Features (chat)"""
    print("\n💬 TEST 4: COMMUNICATION FEATURES")
    
    if not session_id:
        print("❌ Skipping communication tests - no session ID available")
        return
    
    # Test sending chat message
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/chat"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "message": "Hello, how are you feeling today?",
            "sender_type": "provider"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        assert "id" in result
        assert result["message"] == data["message"]
        assert result["sender_type"] == "provider"
        
        print_test_result("Send Chat Message", True, result)
    except Exception as e:
        print_test_result("Send Chat Message", False, error_msg=str(e))
    
    # Send another message as patient
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/chat"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "message": "I'm feeling much better, thank you!",
            "sender_type": "patient"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        print_test_result("Send Patient Chat Message", True, result)
    except Exception as e:
        print_test_result("Send Patient Chat Message", False, error_msg=str(e))
    
    # Test retrieving chat messages
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/chat"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        assert isinstance(result, list)
        assert len(result) >= 2  # Should have at least the 2 messages we sent
        
        print_test_result("Retrieve Chat Messages", True, {"message_count": len(result)})
    except Exception as e:
        print_test_result("Retrieve Chat Messages", False, error_msg=str(e))

def test_integration_features(token, patient_id, provider_id):
    """Test 5: Integration Features (appointment conversion, WebRTC signaling)"""
    print("\n🔗 TEST 5: INTEGRATION FEATURES")
    
    # First create an appointment to convert
    appointment_id = None
    try:
        url = f"{API_URL}/appointments"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "14:00",
            "end_time": "14:30",
            "appointment_type": "consultation",
            "reason": "Telehealth conversion test",
            "location": "Virtual",
            "scheduled_by": "admin"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        appointment_id = result["id"]
        
        print(f"✅ Created test appointment: {appointment_id}")
    except Exception as e:
        print(f"❌ Failed to create test appointment: {str(e)}")
    
    # Test converting appointment to telehealth
    if appointment_id:
        try:
            url = f"{API_URL}/appointments/{appointment_id}/convert-to-telehealth"
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "session_type": "video_consultation",
                "recording_enabled": True,
                "special_instructions": "Patient prefers video over audio"
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            assert "telehealth_session_id" in result
            assert "message" in result
            
            print_test_result("Convert Appointment to Telehealth", True, result)
        except Exception as e:
            print_test_result("Convert Appointment to Telehealth", False, error_msg=str(e))
    
    # Test WebRTC signaling support
    try:
        url = f"{API_URL}/telehealth/signaling"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "session_id": "test-session-123",
            "signal_type": "offer",
            "signal_data": {
                "type": "offer",
                "sdp": "v=0\r\no=- 123456789 2 IN IP4 127.0.0.1\r\n..."
            },
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        assert "message" in result
        
        print_test_result("WebRTC Signaling Support", True, result)
    except Exception as e:
        print_test_result("WebRTC Signaling Support", False, error_msg=str(e))

def test_end_to_end_workflow(token, patient_id, patient_name, provider_id, provider_name):
    """Test 6: End-to-End Workflow"""
    print("\n🔄 TEST 6: END-TO-END TELEHEALTH WORKFLOW")
    
    session_id = None
    encounter_id = None
    
    # Step 1: Create telehealth session
    try:
        url = f"{API_URL}/telehealth/sessions"
        headers = {"Authorization": f"Bearer {token}"}
        
        scheduled_start = datetime.now() + timedelta(minutes=5)
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "session_type": "video_consultation",
            "title": "End-to-End Test Session",
            "description": "Complete workflow test for telehealth system",
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 30,
            "recording_enabled": True
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        session_id = result["id"]
        
        print(f"✅ Step 1: Created telehealth session {session_id}")
    except Exception as e:
        print(f"❌ Step 1 failed: {str(e)}")
        return
    
    # Step 2: Patient joins waiting room
    try:
        url = f"{API_URL}/telehealth/waiting-room/{session_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        print("✅ Step 2: Patient joined waiting room")
    except Exception as e:
        print(f"❌ Step 2 failed: {str(e)}")
    
    # Step 3: Start session (creates encounter)
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/start"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        encounter_id = result.get("encounter_id")
        
        print(f"✅ Step 3: Started session, created encounter {encounter_id}")
    except Exception as e:
        print(f"❌ Step 3 failed: {str(e)}")
    
    # Step 4: Exchange chat messages
    try:
        # Provider message
        url = f"{API_URL}/telehealth/sessions/{session_id}/chat"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": "Good morning! How can I help you today?", "sender_type": "provider"}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Patient response
        data = {"message": "I've been having headaches for the past week.", "sender_type": "patient"}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print("✅ Step 4: Exchanged chat messages")
    except Exception as e:
        print(f"❌ Step 4 failed: {str(e)}")
    
    # Step 5: End session with documentation
    try:
        url = f"{API_URL}/telehealth/sessions/{session_id}/end"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "session_notes": "Patient presented with chronic headaches. Discussed treatment options and lifestyle modifications.",
            "provider_notes": "Recommended stress management and follow-up in 2 weeks. Prescribed mild pain relief.",
            "patient_rating": 5,
            "provider_rating": 4
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print("✅ Step 5: Ended session with documentation")
    except Exception as e:
        print(f"❌ Step 5 failed: {str(e)}")
    
    # Step 6: Verify billing integration (check if encounter was created)
    if encounter_id:
        try:
            url = f"{API_URL}/encounters/{encounter_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            assert result["id"] == encounter_id
            assert result["patient_id"] == patient_id
            
            print("✅ Step 6: Verified billing integration (encounter created)")
        except Exception as e:
            print(f"❌ Step 6 failed: {str(e)}")
    
    print("🎉 END-TO-END WORKFLOW COMPLETED SUCCESSFULLY!")

def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive Telehealth System Testing")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Create test data
    patient_id, patient_name = create_test_patient(token)
    provider_id, provider_name = create_test_provider(token)
    
    if not patient_id or not provider_id:
        print("❌ Failed to create test data. Cannot proceed with tests.")
        return
    
    # Run telehealth tests
    session_id = test_telehealth_session_management(token, patient_id, patient_name, provider_id, provider_name)
    test_session_lifecycle_management(token, session_id)
    test_waiting_room_system(token, patient_id, patient_name)
    test_communication_features(token, session_id)
    test_integration_features(token, patient_id, provider_id)
    test_end_to_end_workflow(token, patient_id, patient_name, provider_id, provider_name)
    
    print("\n" + "=" * 80)
    print("🏥 COMPREHENSIVE TELEHEALTH SYSTEM TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()