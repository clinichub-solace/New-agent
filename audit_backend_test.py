#!/usr/bin/env python3
"""
Comprehensive Audit Logging System Test for ClinicHub Payroll Workflows

This test validates the complete audit workflow as requested:
1. Authentication with admin/admin123 credentials
2. Payroll workflow operations to generate audit entries
3. Audit query endpoints testing
4. Verification of audit data integrity
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import uuid

# Configuration
BASE_URL = "https://mongodb-fix.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AuditTestRunner:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_resources = {
            "employees": [],
            "periods": [],
            "runs": [],
            "tax_configs": [],
            "ach_configs": [],
            "bank_configs": []
        }

    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)

    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    async def authenticate(self) -> bool:
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    if self.auth_token:
                        print("✅ Authentication successful")
                        return True
                    else:
                        print("❌ No access token in response")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    async def test_audit_endpoints_basic(self) -> bool:
        """Test basic audit endpoints availability"""
        print("\n🔍 Testing Basic Audit Endpoints...")
        
        endpoints = [
            "/audit",
            "/audit/actions", 
            "/audit/subject-types"
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            try:
                async with self.session.get(f"{BASE_URL}{endpoint}", headers=self.get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ GET {endpoint} - Status: {response.status}")
                        if endpoint == "/audit":
                            print(f"   📊 Returned {len(data)} audit entries")
                        elif endpoint == "/audit/actions":
                            actions = data.get("actions", [])
                            print(f"   📊 Available actions: {len(actions)}")
                        elif endpoint == "/audit/subject-types":
                            types = data.get("subject_types", [])
                            print(f"   📊 Available subject types: {len(types)}")
                    else:
                        print(f"❌ GET {endpoint} - Status: {response.status}")
                        all_passed = False
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
                all_passed = False
        
        return all_passed

    async def create_test_employee(self) -> str:
        """Create a test employee for payroll operations"""
        try:
            employee_data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": f"john.doe.{uuid.uuid4().hex[:8]}@test.com",
                "phone": "555-0123",
                "role": "admin",
                "department": "Administration",
                "hire_date": date.today().isoformat(),
                "salary": 75000.0,
                "employment_type": "full_time"
            }
            
            async with self.session.post(f"{BASE_URL}/employees", json=employee_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    employee_id = data.get("id")
                    self.created_resources["employees"].append(employee_id)
                    print(f"✅ Created test employee: {employee_id}")
                    return employee_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create employee: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating employee: {e}")
            return None

    async def test_tax_configuration_audit(self) -> bool:
        """Test tax configuration with audit logging"""
        print("\n🏛️ Testing Tax Configuration Audit...")
        
        try:
            tax_config = {
                "jurisdiction": "TX",
                "effective_date": "2025-01-01",
                "tax_type": "state",
                "rate": 0.0625,
                "brackets": [
                    {"min": 0, "max": 50000, "rate": 0.0}
                ]
            }
            
            async with self.session.put(f"{BASE_URL}/payroll/config/tax", json=tax_config, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    config_id = f"{tax_config['jurisdiction']}@{tax_config['effective_date']}"
                    self.created_resources["tax_configs"].append(config_id)
                    print(f"✅ Tax configuration updated: {config_id}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Tax configuration failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in tax configuration: {e}")
            return False

    async def test_ach_configuration_audit(self) -> bool:
        """Test ACH configuration with audit logging"""
        print("\n🏦 Testing ACH Configuration Audit...")
        
        try:
            ach_config = {
                "company_name": "Test Clinic",
                "company_id": "1234567890",
                "immediate_destination": "123456789",
                "immediate_origin": "987654321",
                "entry_description": "PAYROLL",
                "originating_dfi_identification": "12345678"
            }
            
            async with self.session.put(f"{BASE_URL}/payroll/config/ach", json=ach_config, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    self.created_resources["ach_configs"].append("ACH_DEFAULT")
                    print(f"✅ ACH configuration updated")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ ACH configuration failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in ACH configuration: {e}")
            return False

    async def test_employee_bank_info_audit(self, employee_id: str) -> bool:
        """Test employee bank info update with audit logging"""
        print("\n💳 Testing Employee Bank Info Audit...")
        
        try:
            bank_info = {
                "name": "John Doe",
                "routing_number": "123456789",
                "account_number": "987654321",
                "account_type": "checking"
            }
            
            async with self.session.put(f"{BASE_URL}/payroll/employees/{employee_id}/bank", json=bank_info, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    self.created_resources["bank_configs"].append(employee_id)
                    print(f"✅ Employee bank info updated for: {employee_id}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Employee bank info failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in employee bank info: {e}")
            return False

    async def test_pay_period_creation_audit(self) -> str:
        """Test pay period creation with audit logging"""
        print("\n📅 Testing Pay Period Creation Audit...")
        
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=13)  # 2-week period
            
            period_data = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "frequency": "biweekly",
                "closed": False
            }
            
            async with self.session.post(f"{BASE_URL}/payroll/periods", json=period_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    period_id = data.get("id")
                    self.created_resources["periods"].append(period_id)
                    print(f"✅ Pay period created: {period_id}")
                    return period_id
                else:
                    error_text = await response.text()
                    print(f"❌ Pay period creation failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating pay period: {e}")
            return None

    async def test_payroll_run_creation_audit(self, period_id: str) -> str:
        """Test payroll run creation with audit logging"""
        print("\n🏃 Testing Payroll Run Creation Audit...")
        
        try:
            run_data = {
                "period_id": period_id
            }
            
            async with self.session.post(f"{BASE_URL}/payroll/runs", json=run_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    run_id = data.get("id")
                    self.created_resources["runs"].append(run_id)
                    print(f"✅ Payroll run created: {run_id}")
                    return run_id
                else:
                    error_text = await response.text()
                    print(f"❌ Payroll run creation failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating payroll run: {e}")
            return None

    async def test_payroll_run_posting_audit(self, run_id: str) -> bool:
        """Test payroll run posting with audit logging"""
        print("\n📮 Testing Payroll Run Posting Audit...")
        
        try:
            async with self.session.post(f"{BASE_URL}/payroll/runs/{run_id}/post", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Payroll run posted: {run_id}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Payroll run posting failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error posting payroll run: {e}")
            return False

    async def test_payroll_run_voiding_audit(self, run_id: str) -> bool:
        """Test payroll run voiding with audit logging"""
        print("\n🚫 Testing Payroll Run Voiding Audit...")
        
        try:
            void_data = "Test void reason for audit testing"
            
            async with self.session.post(f"{BASE_URL}/payroll/runs/{run_id}/void", json=void_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Payroll run voided: {run_id}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Payroll run voiding failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error voiding payroll run: {e}")
            return False

    async def test_csv_export_audit(self, run_id: str) -> bool:
        """Test CSV export with audit logging"""
        print("\n📊 Testing CSV Export Audit...")
        
        try:
            async with self.session.get(f"{BASE_URL}/payroll/runs/{run_id}/paystubs.csv", headers=self.get_headers()) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ CSV export successful for run: {run_id}")
                    print(f"   📄 CSV content length: {len(content)} characters")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ CSV export failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in CSV export: {e}")
            return False

    async def test_ach_export_audit(self, run_id: str) -> bool:
        """Test ACH export with audit logging"""
        print("\n🏦 Testing ACH Export Audit...")
        
        try:
            async with self.session.get(f"{BASE_URL}/payroll/runs/{run_id}/ach?mode=test", headers=self.get_headers()) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ ACH export successful for run: {run_id}")
                    print(f"   📄 ACH content length: {len(content)} characters")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ ACH export failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in ACH export: {e}")
            return False

    async def test_audit_queries(self) -> bool:
        """Test comprehensive audit query functionality"""
        print("\n🔍 Testing Audit Query Functionality...")
        
        all_passed = True
        
        # Test 1: List recent audit entries
        try:
            async with self.session.get(f"{BASE_URL}/audit?limit=10", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Recent audit entries: {len(data)} entries")
                    
                    # Verify audit entry structure
                    if data:
                        entry = data[0]
                        required_fields = ["ts", "action", "subject_type", "subject_id", "user", "meta"]
                        missing_fields = [field for field in required_fields if field not in entry]
                        if missing_fields:
                            print(f"❌ Missing fields in audit entry: {missing_fields}")
                            all_passed = False
                        else:
                            print("✅ Audit entry structure is correct")
                            print(f"   📝 Sample entry: {entry['action']} on {entry['subject_type']}")
                else:
                    print(f"❌ Failed to get recent audit entries: {response.status}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error getting recent audit entries: {e}")
            all_passed = False

        # Test 2: Filter by action
        try:
            async with self.session.get(f"{BASE_URL}/audit?action=payroll.run.post", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Filtered by action 'payroll.run.post': {len(data)} entries")
                    
                    # Verify all entries have the correct action
                    if data:
                        wrong_actions = [entry for entry in data if entry.get("action") != "payroll.run.post"]
                        if wrong_actions:
                            print(f"❌ Found entries with wrong action: {len(wrong_actions)}")
                            all_passed = False
                        else:
                            print("✅ All entries have correct action filter")
                else:
                    print(f"❌ Failed to filter by action: {response.status}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error filtering by action: {e}")
            all_passed = False

        # Test 3: Filter by subject type
        try:
            async with self.session.get(f"{BASE_URL}/audit?subject_type=payroll_run", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Filtered by subject_type 'payroll_run': {len(data)} entries")
                    
                    # Verify all entries have the correct subject type
                    if data:
                        wrong_types = [entry for entry in data if entry.get("subject_type") != "payroll_run"]
                        if wrong_types:
                            print(f"❌ Found entries with wrong subject type: {len(wrong_types)}")
                            all_passed = False
                        else:
                            print("✅ All entries have correct subject type filter")
                else:
                    print(f"❌ Failed to filter by subject type: {response.status}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error filtering by subject type: {e}")
            all_passed = False

        # Test 4: Get available actions
        try:
            async with self.session.get(f"{BASE_URL}/audit/actions", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    actions = data.get("actions", [])
                    print(f"✅ Available actions: {len(actions)} actions")
                    
                    # Check for expected payroll actions
                    expected_actions = [
                        "payroll.tax.put",
                        "payroll.ach.put", 
                        "payroll.employee.bank.put",
                        "payroll.period.create",
                        "payroll.run.create_or_get",
                        "payroll.run.post",
                        "payroll.run.void",
                        "payroll.export.csv",
                        "payroll.export.ach"
                    ]
                    
                    found_actions = [action for action in expected_actions if action in actions]
                    print(f"   📊 Found expected payroll actions: {len(found_actions)}/{len(expected_actions)}")
                    
                    if len(found_actions) < len(expected_actions):
                        missing_actions = [action for action in expected_actions if action not in actions]
                        print(f"   ⚠️ Missing actions: {missing_actions}")
                else:
                    print(f"❌ Failed to get available actions: {response.status}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error getting available actions: {e}")
            all_passed = False

        # Test 5: Get available subject types
        try:
            async with self.session.get(f"{BASE_URL}/audit/subject-types", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    subject_types = data.get("subject_types", [])
                    print(f"✅ Available subject types: {len(subject_types)} types")
                    
                    # Check for expected payroll subject types
                    expected_types = [
                        "payroll_tax_table",
                        "payroll_ach_config",
                        "employee_bank",
                        "payroll_period",
                        "payroll_run"
                    ]
                    
                    found_types = [stype for stype in expected_types if stype in subject_types]
                    print(f"   📊 Found expected payroll subject types: {len(found_types)}/{len(expected_types)}")
                    
                    if len(found_types) < len(expected_types):
                        missing_types = [stype for stype in expected_types if stype not in subject_types]
                        print(f"   ⚠️ Missing subject types: {missing_types}")
                else:
                    print(f"❌ Failed to get available subject types: {response.status}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error getting available subject types: {e}")
            all_passed = False

        return all_passed

    async def verify_audit_data_integrity(self) -> bool:
        """Verify audit data contains proper timestamps, user info, and metadata"""
        print("\n🔒 Verifying Audit Data Integrity...")
        
        try:
            async with self.session.get(f"{BASE_URL}/audit?limit=20", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data:
                        print("⚠️ No audit entries found for integrity verification")
                        return True
                    
                    print(f"📊 Verifying {len(data)} audit entries...")
                    
                    integrity_issues = []
                    
                    for i, entry in enumerate(data):
                        # Check timestamp format
                        try:
                            datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
                        except (ValueError, KeyError):
                            integrity_issues.append(f"Entry {i}: Invalid timestamp format")
                        
                        # Check user information
                        user_info = entry.get("user", {})
                        if not user_info.get("username"):
                            integrity_issues.append(f"Entry {i}: Missing user.username")
                        
                        # Check required fields
                        required_fields = ["action", "subject_type", "subject_id"]
                        for field in required_fields:
                            if not entry.get(field):
                                integrity_issues.append(f"Entry {i}: Missing {field}")
                        
                        # Check metadata exists (can be empty dict)
                        if "meta" not in entry:
                            integrity_issues.append(f"Entry {i}: Missing meta field")
                    
                    if integrity_issues:
                        print(f"❌ Found {len(integrity_issues)} integrity issues:")
                        for issue in integrity_issues[:10]:  # Show first 10 issues
                            print(f"   • {issue}")
                        if len(integrity_issues) > 10:
                            print(f"   ... and {len(integrity_issues) - 10} more issues")
                        return False
                    else:
                        print("✅ All audit entries have proper data integrity")
                        
                        # Show sample of good entries
                        print("📝 Sample audit entries:")
                        for entry in data[:3]:
                            print(f"   • {entry['ts'][:19]} | {entry['action']} | {entry['subject_type']} | User: {entry['user'].get('username')}")
                        
                        return True
                else:
                    print(f"❌ Failed to get audit entries for integrity check: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error verifying audit data integrity: {e}")
            return False

    async def run_comprehensive_test(self):
        """Run the complete audit logging test suite"""
        print("🚀 Starting Comprehensive Audit Logging System Test")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Step 1: Authentication
            if not await self.authenticate():
                print("❌ Authentication failed - cannot continue")
                return
            
            # Step 2: Test basic audit endpoints
            if not await self.test_audit_endpoints_basic():
                print("❌ Basic audit endpoints failed")
                return
            
            # Step 3: Create test employee for payroll operations
            employee_id = await self.create_test_employee()
            if not employee_id:
                print("❌ Failed to create test employee - cannot continue payroll tests")
                return
            
            # Step 4: Execute payroll workflow operations to generate audit entries
            print("\n🏗️ Executing Payroll Workflow Operations...")
            
            # Tax configuration
            await self.test_tax_configuration_audit()
            
            # ACH configuration  
            await self.test_ach_configuration_audit()
            
            # Employee bank info
            await self.test_employee_bank_info_audit(employee_id)
            
            # Pay period creation
            period_id = await self.test_pay_period_creation_audit()
            if not period_id:
                print("❌ Failed to create pay period - skipping run operations")
            else:
                # Payroll run creation
                run_id = await self.test_payroll_run_creation_audit(period_id)
                if run_id:
                    # Payroll run posting
                    await self.test_payroll_run_posting_audit(run_id)
                    
                    # CSV export
                    await self.test_csv_export_audit(run_id)
                    
                    # ACH export
                    await self.test_ach_export_audit(run_id)
                    
                    # Payroll run voiding
                    await self.test_payroll_run_voiding_audit(run_id)
            
            # Step 5: Test audit query functionality
            await self.test_audit_queries()
            
            # Step 6: Verify audit data integrity
            await self.verify_audit_data_integrity()
            
            print("\n" + "=" * 60)
            print("🎉 Comprehensive Audit Logging System Test Completed")
            
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test_runner = AuditTestRunner()
    await test_runner.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())