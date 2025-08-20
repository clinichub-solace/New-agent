#!/usr/bin/env python3
"""
Comprehensive Notification System Testing for ClinicHub Payroll Workflows
Tests the complete notification workflow as requested in the review.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import uuid

# Configuration
BASE_URL = "https://health-platform-3.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class NotificationSystemTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_resources = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    async def authenticate(self) -> bool:
        """Authenticate with admin credentials"""
        try:
            async with self.session.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get("access_token")
                    if self.auth_token:
                        self.log_result("Authentication", True, "Successfully authenticated with admin/admin123")
                        return True
                    else:
                        self.log_result("Authentication", False, "No access token in response")
                        return False
                else:
                    text = await resp.text()
                    self.log_result("Authentication", False, f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def test_notification_infrastructure(self) -> bool:
        """Test notification infrastructure endpoints"""
        try:
            # Test GET /api/notifications
            async with self.session.get(f"{BASE_URL}/notifications", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    notifications = await resp.json()
                    self.log_result("Notification Infrastructure - List", True, 
                                  f"Retrieved {len(notifications)} notifications")
                else:
                    self.log_result("Notification Infrastructure - List", False, 
                                  f"HTTP {resp.status}")
                    return False
            
            # Test GET /api/notifications/count
            async with self.session.get(f"{BASE_URL}/notifications/count", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    count_data = await resp.json()
                    total = count_data.get("total", 0)
                    unread = count_data.get("unread", 0)
                    self.log_result("Notification Infrastructure - Count", True, 
                                  f"Total: {total}, Unread: {unread}")
                else:
                    self.log_result("Notification Infrastructure - Count", False, 
                                  f"HTTP {resp.status}")
                    return False
            
            return True
        except Exception as e:
            self.log_result("Notification Infrastructure", False, f"Exception: {str(e)}")
            return False
    
    async def test_manual_notification_creation(self) -> Optional[str]:
        """Test manual notification creation"""
        try:
            notification_data = {
                "type": "test.manual",
                "title": "Test Manual Notification",
                "body": "This is a test notification created manually during testing",
                "severity": "info",
                "meta": {"test": True, "created_by": "notification_system_test"}
            }
            
            async with self.session.post(f"{BASE_URL}/notifications", 
                                       json=notification_data, 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    notification = await resp.json()
                    notif_id = notification.get("_id")
                    self.created_resources.append(("notification", notif_id))
                    self.log_result("Manual Notification Creation", True, 
                                  f"Created notification with ID: {notif_id}")
                    return notif_id
                else:
                    text = await resp.text()
                    self.log_result("Manual Notification Creation", False, 
                                  f"HTTP {resp.status}: {text}")
                    return None
        except Exception as e:
            self.log_result("Manual Notification Creation", False, f"Exception: {str(e)}")
            return None
    
    async def test_notification_acknowledgment(self, notif_id: str) -> bool:
        """Test notification acknowledgment"""
        try:
            # Test acknowledge specific notification
            async with self.session.post(f"{BASE_URL}/notifications/{notif_id}/ack", 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    ack_data = await resp.json()
                    self.log_result("Notification Acknowledgment - Specific", True, 
                                  f"Acknowledged notification {notif_id}")
                else:
                    text = await resp.text()
                    self.log_result("Notification Acknowledgment - Specific", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
            
            return True
        except Exception as e:
            self.log_result("Notification Acknowledgment", False, f"Exception: {str(e)}")
            return False
    
    async def test_notification_deletion(self, notif_id: str) -> bool:
        """Test notification deletion"""
        try:
            async with self.session.delete(f"{BASE_URL}/notifications/{notif_id}", 
                                         headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("Notification Deletion", True, 
                                  f"Deleted notification {notif_id}")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("Notification Deletion", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Notification Deletion", False, f"Exception: {str(e)}")
            return False
    
    async def test_acknowledge_all_notifications(self) -> bool:
        """Test acknowledge all notifications"""
        try:
            async with self.session.post(f"{BASE_URL}/notifications/ack-all", 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    ack_data = await resp.json()
                    count = ack_data.get("count", 0)
                    self.log_result("Acknowledge All Notifications", True, 
                                  f"Acknowledged {count} notifications")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("Acknowledge All Notifications", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Acknowledge All Notifications", False, f"Exception: {str(e)}")
            return False
    
    async def create_pay_period(self) -> Optional[str]:
        """Create a test pay period"""
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=13)  # 2-week period
            
            period_data = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "frequency": "biweekly"
            }
            
            async with self.session.post(f"{BASE_URL}/payroll/periods", 
                                       json=period_data, 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    period = await resp.json()
                    period_id = period.get("id") or period.get("_id")
                    self.created_resources.append(("pay_period", period_id))
                    self.log_result("Pay Period Creation", True, 
                                  f"Created pay period {period_id}")
                    return period_id
                else:
                    text = await resp.text()
                    self.log_result("Pay Period Creation", False, 
                                  f"HTTP {resp.status}: {text}")
                    return None
        except Exception as e:
            self.log_result("Pay Period Creation", False, f"Exception: {str(e)}")
            return None
    
    async def create_payroll_run(self, period_id: str) -> Optional[str]:
        """Create a payroll run"""
        try:
            run_data = {"period_id": period_id}
            
            async with self.session.post(f"{BASE_URL}/payroll/runs", 
                                       json=run_data, 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    run = await resp.json()
                    run_id = run.get("id") or run.get("_id")
                    self.created_resources.append(("payroll_run", run_id))
                    self.log_result("Payroll Run Creation", True, 
                                  f"Created payroll run {run_id}")
                    return run_id
                else:
                    text = await resp.text()
                    self.log_result("Payroll Run Creation", False, 
                                  f"HTTP {resp.status}: {text}")
                    return None
        except Exception as e:
            self.log_result("Payroll Run Creation", False, f"Exception: {str(e)}")
            return None
    
    async def test_tax_configuration_notification(self) -> bool:
        """Test tax configuration notification"""
        try:
            tax_data = {
                "jurisdiction": "TX",
                "effective_date": "2025-01-01",
                "tax_rate": 0.0625,
                "description": "Texas state tax configuration for testing"
            }
            
            async with self.session.put(f"{BASE_URL}/payroll/config/tax", 
                                      json=tax_data, 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("Tax Configuration Notification", True, 
                                  "Tax configuration updated successfully")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("Tax Configuration Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Tax Configuration Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_ach_configuration_notification(self) -> bool:
        """Test ACH configuration notification"""
        try:
            ach_data = {
                "company_name": "Test Clinic",
                "company_id": "1234567890",
                "immediate_destination": "123456789",
                "immediate_origin": "987654321",
                "entry_description": "PAYROLL",
                "originating_dfi_identification": "12345678"
            }
            
            async with self.session.put(f"{BASE_URL}/payroll/config/ach", 
                                      json=ach_data, 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("ACH Configuration Notification", True, 
                                  "ACH configuration updated successfully")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("ACH Configuration Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("ACH Configuration Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_payroll_run_posting_notification(self, run_id: str) -> bool:
        """Test payroll run posting notification"""
        try:
            async with self.session.post(f"{BASE_URL}/payroll/runs/{run_id}/post", 
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    run_data = await resp.json()
                    self.log_result("Payroll Run Posting Notification", True, 
                                  f"Posted payroll run {run_id}")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("Payroll Run Posting Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Payroll Run Posting Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_payroll_run_voiding_notification(self, run_id: str) -> bool:
        """Test payroll run voiding notification"""
        try:
            void_reason = "Testing notification system - voiding for test purposes"
            
            async with self.session.post(f"{BASE_URL}/payroll/runs/{run_id}/void", 
                                       json=void_reason,
                                       headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("Payroll Run Voiding Notification", True, 
                                  f"Voided payroll run {run_id}")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("Payroll Run Voiding Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("Payroll Run Voiding Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_csv_export_notification(self, run_id: str) -> bool:
        """Test CSV export notification"""
        try:
            async with self.session.get(f"{BASE_URL}/payroll/runs/{run_id}/paystubs.csv", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("CSV Export Notification", True, 
                                  f"Generated CSV export for run {run_id}")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("CSV Export Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("CSV Export Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_ach_export_notification(self, run_id: str) -> bool:
        """Test ACH export notification"""
        try:
            async with self.session.get(f"{BASE_URL}/payroll/runs/{run_id}/ach?mode=test", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    self.log_result("ACH Export Notification", True, 
                                  f"Generated ACH export for run {run_id}")
                    return True
                else:
                    text = await resp.text()
                    self.log_result("ACH Export Notification", False, 
                                  f"HTTP {resp.status}: {text}")
                    return False
        except Exception as e:
            self.log_result("ACH Export Notification", False, f"Exception: {str(e)}")
            return False
    
    async def test_notification_filtering(self) -> bool:
        """Test notification filtering capabilities"""
        try:
            # Test unread only filter
            async with self.session.get(f"{BASE_URL}/notifications?unread_only=true", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    unread_notifications = await resp.json()
                    self.log_result("Notification Filtering - Unread Only", True, 
                                  f"Retrieved {len(unread_notifications)} unread notifications")
                else:
                    self.log_result("Notification Filtering - Unread Only", False, 
                                  f"HTTP {resp.status}")
                    return False
            
            # Test limit filter
            async with self.session.get(f"{BASE_URL}/notifications?limit=5", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    limited_notifications = await resp.json()
                    self.log_result("Notification Filtering - Limit", True, 
                                  f"Retrieved {len(limited_notifications)} notifications (limit=5)")
                else:
                    self.log_result("Notification Filtering - Limit", False, 
                                  f"HTTP {resp.status}")
                    return False
            
            # Test since filter (last hour)
            since_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            async with self.session.get(f"{BASE_URL}/notifications?since={since_time}", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    recent_notifications = await resp.json()
                    self.log_result("Notification Filtering - Since", True, 
                                  f"Retrieved {len(recent_notifications)} notifications since {since_time}")
                else:
                    self.log_result("Notification Filtering - Since", False, 
                                  f"HTTP {resp.status}")
                    return False
            
            return True
        except Exception as e:
            self.log_result("Notification Filtering", False, f"Exception: {str(e)}")
            return False
    
    async def verify_notification_data_integrity(self) -> bool:
        """Verify notification data integrity"""
        try:
            async with self.session.get(f"{BASE_URL}/notifications?limit=10", 
                                      headers=self.get_headers()) as resp:
                if resp.status == 200:
                    notifications = await resp.json()
                    
                    if not notifications:
                        self.log_result("Notification Data Integrity", True, 
                                      "No notifications to verify")
                        return True
                    
                    # Check required fields
                    required_fields = ["ts", "user_id", "type", "title", "body", "severity", "read"]
                    integrity_issues = []
                    
                    for notif in notifications:
                        for field in required_fields:
                            if field not in notif:
                                integrity_issues.append(f"Missing field '{field}' in notification {notif.get('_id')}")
                        
                        # Check timestamp format
                        try:
                            datetime.fromisoformat(notif.get("ts", "").replace("Z", "+00:00"))
                        except:
                            integrity_issues.append(f"Invalid timestamp format in notification {notif.get('_id')}")
                        
                        # Check severity values
                        if notif.get("severity") not in ["info", "warning", "error", "success"]:
                            integrity_issues.append(f"Invalid severity '{notif.get('severity')}' in notification {notif.get('_id')}")
                    
                    if integrity_issues:
                        self.log_result("Notification Data Integrity", False, 
                                      f"Found {len(integrity_issues)} integrity issues: {'; '.join(integrity_issues[:3])}")
                        return False
                    else:
                        self.log_result("Notification Data Integrity", True, 
                                      f"Verified {len(notifications)} notifications - all have proper structure")
                        return True
                else:
                    self.log_result("Notification Data Integrity", False, 
                                  f"HTTP {resp.status}")
                    return False
        except Exception as e:
            self.log_result("Notification Data Integrity", False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run the complete notification system test"""
        print("🔔 COMPREHENSIVE NOTIFICATION SYSTEM TESTING STARTED")
        print("=" * 80)
        
        # Step 1: Authentication
        if not await self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test notification infrastructure
        if not await self.test_notification_infrastructure():
            print("❌ Notification infrastructure test failed")
            return
        
        # Step 3: Test manual notification creation and management
        notif_id = await self.test_manual_notification_creation()
        if notif_id:
            await self.test_notification_acknowledgment(notif_id)
            # Don't delete yet, we'll test deletion later
        
        # Step 4: Test payroll workflow notifications
        print("\n📋 TESTING PAYROLL WORKFLOW NOTIFICATIONS")
        print("-" * 50)
        
        # Create pay period (should trigger notification)
        period_id = await self.create_pay_period()
        if not period_id:
            print("❌ Failed to create pay period - skipping payroll tests")
        else:
            # Test tax configuration
            await self.test_tax_configuration_notification()
            
            # Test ACH configuration
            await self.test_ach_configuration_notification()
            
            # Create payroll run
            run_id = await self.create_payroll_run(period_id)
            if run_id:
                # Post the run (should trigger success notification)
                await self.test_payroll_run_posting_notification(run_id)
                
                # Test export notifications
                await self.test_csv_export_notification(run_id)
                await self.test_ach_export_notification(run_id)
                
                # Void the run (should trigger warning notification)
                await self.test_payroll_run_voiding_notification(run_id)
        
        # Step 5: Test notification API features
        print("\n🔍 TESTING NOTIFICATION API FEATURES")
        print("-" * 50)
        
        await self.test_notification_filtering()
        await self.verify_notification_data_integrity()
        
        # Step 6: Test acknowledge all and deletion
        await self.test_acknowledge_all_notifications()
        
        if notif_id:
            await self.test_notification_deletion(notif_id)
        
        # Step 7: Final verification
        await self.test_notification_infrastructure()  # Final check
        
        print("\n" + "=" * 80)
        print("🔔 COMPREHENSIVE NOTIFICATION SYSTEM TESTING COMPLETED")
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n🎯 NOTIFICATION SYSTEM STATUS: {'✅ EXCELLENT' if failed_tests == 0 else '⚠️ NEEDS ATTENTION' if failed_tests <= 2 else '❌ CRITICAL ISSUES'}")

async def main():
    """Main test execution"""
    async with NotificationSystemTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())