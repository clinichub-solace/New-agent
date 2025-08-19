#!/usr/bin/env python3
"""
Focused Employee Management System Test
======================================
Testing specific Employee Management endpoints to assess current implementation.
"""

import requests
import json
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

BACKEND_URL = "http://localhost:8001"  # Use localhost for testing
API_URL = f"{BACKEND_URL}/api"

print(f"🏥 Focused Employee Management Test")
print(f"🔗 API URL: {API_URL}")
print("=" * 60)

def test_basic_connectivity():
    """Test basic API connectivity"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"✅ Backend connectivity: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Backend connectivity failed: {str(e)}")
        return False

def authenticate():
    """Get admin token"""
    try:
        # Try login first
        url = f"{API_URL}/auth/login"
        data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Authentication successful")
            return result["access_token"]
        
        # If login fails, try init admin
        url = f"{API_URL}/auth/init-admin"
        response = requests.post(url, timeout=10)
        
        # Then login
        url = f"{API_URL}/auth/login"
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        print("✅ Authentication successful (after init)")
        return result["access_token"]
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_employee_endpoints(token):
    """Test Employee Management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print("\n📋 Testing Employee Management Endpoints:")
    print("-" * 40)
    
    # Test 1: Create Employee
    try:
        url = f"{API_URL}/employees"
        data = {
            "first_name": "Dr. Michael",
            "last_name": "Thompson",
            "email": "dr.thompson@clinichub.com",
            "phone": "+1-555-234-5678",
            "role": "doctor",
            "department": "Cardiology",
            "hire_date": date.today().isoformat(),
            "salary": 250000.00
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            employee_id = result.get("id")
            results["create_employee"] = {
                "status": "✅ WORKING",
                "employee_id": result.get("employee_id", "N/A"),
                "auto_id": "Yes" if result.get("employee_id", "").startswith("EMP-") else "No"
            }
        else:
            results["create_employee"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
            employee_id = None
            
    except Exception as e:
        results["create_employee"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
        employee_id = None
    
    # Test 2: Get All Employees
    try:
        url = f"{API_URL}/employees"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            employees = response.json()
            results["get_employees"] = {
                "status": "✅ WORKING",
                "count": len(employees),
                "has_data": "Yes" if employees else "No"
            }
        else:
            results["get_employees"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        results["get_employees"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    # Test 3: Get Specific Employee
    if employee_id:
        try:
            url = f"{API_URL}/employees/{employee_id}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                employee = response.json()
                results["get_employee_by_id"] = {
                    "status": "✅ WORKING",
                    "fields": len(employee.keys()),
                    "has_profile": "Complete" if len(employee.keys()) > 10 else "Basic"
                }
            else:
                results["get_employee_by_id"] = {
                    "status": "❌ FAILED",
                    "error": f"Status: {response.status_code}"
                }
        except Exception as e:
            results["get_employee_by_id"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    # Test 4: Update Employee
    if employee_id:
        try:
            url = f"{API_URL}/employees/{employee_id}"
            update_data = {
                "department": "Emergency Medicine",
                "salary": 275000.00
            }
            response = requests.put(url, json=update_data, headers=headers, timeout=10)
            if response.status_code == 200:
                results["update_employee"] = {
                    "status": "✅ WORKING",
                    "updated": "Department & Salary"
                }
            else:
                results["update_employee"] = {
                    "status": "❌ FAILED",
                    "error": f"Status: {response.status_code}"
                }
        except Exception as e:
            results["update_employee"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    return results, employee_id

def test_payroll_endpoints(token, employee_id):
    """Test Payroll-related endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print("\n💰 Testing Payroll Endpoints:")
    print("-" * 40)
    
    # Test 1: Payroll Periods
    try:
        url = f"{API_URL}/payroll/periods"
        data = {
            "period_start": date.today().replace(day=1).isoformat(),
            "period_end": (date.today().replace(day=1) + timedelta(days=30)).isoformat(),
            "pay_date": (date.today() + timedelta(days=35)).isoformat(),
            "period_type": "monthly",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            period_id = result.get("id")
            results["payroll_periods"] = {
                "status": "✅ WORKING",
                "period_type": result.get("period_type", "N/A")
            }
        else:
            results["payroll_periods"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
            period_id = None
            
    except Exception as e:
        results["payroll_periods"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
        period_id = None
    
    # Test 2: Payroll Records
    if employee_id and period_id:
        try:
            url = f"{API_URL}/payroll/records"
            data = {
                "payroll_period_id": period_id,
                "employee_id": employee_id,
                "bonus_pay": 5000.00,
                "deductions": [
                    {
                        "deduction_type": "federal_tax",
                        "description": "Federal Tax",
                        "amount": 2500.00,
                        "is_pre_tax": False
                    }
                ]
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                results["payroll_records"] = {
                    "status": "✅ WORKING",
                    "gross_pay": result.get("gross_pay", "N/A"),
                    "net_pay": result.get("net_pay", "N/A")
                }
            else:
                results["payroll_records"] = {
                    "status": "❌ FAILED",
                    "error": f"Status: {response.status_code}"
                }
        except Exception as e:
            results["payroll_records"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    return results

def test_time_attendance_endpoints(token, employee_id):
    """Test Time & Attendance endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print("\n⏰ Testing Time & Attendance Endpoints:")
    print("-" * 40)
    
    # Test 1: Time Entries
    try:
        url = f"{API_URL}/time-entries"
        data = {
            "employee_id": employee_id,
            "entry_type": "clock_in",
            "timestamp": datetime.now().isoformat(),
            "location": "Main Clinic"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            results["time_entries"] = {
                "status": "✅ WORKING",
                "entry_type": "Clock In/Out"
            }
        else:
            results["time_entries"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        results["time_entries"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    # Test 2: Work Shifts
    try:
        url = f"{API_URL}/work-shifts"
        data = {
            "employee_id": employee_id,
            "shift_date": date.today().isoformat(),
            "start_time": datetime.now().replace(hour=8, minute=0).isoformat(),
            "end_time": datetime.now().replace(hour=17, minute=0).isoformat(),
            "break_duration": 60,
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            results["work_shifts"] = {
                "status": "✅ WORKING",
                "shift_duration": "9 hours"
            }
        else:
            results["work_shifts"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        results["work_shifts"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    return results

def test_hr_management_endpoints(token, employee_id):
    """Test HR Management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print("\n👥 Testing HR Management Endpoints:")
    print("-" * 40)
    
    # Test 1: Employee Documents
    try:
        url = f"{API_URL}/employee-documents"
        data = {
            "employee_id": employee_id,
            "document_type": "performance_review",
            "title": "Annual Performance Review 2024",
            "content": "Excellent performance in all areas",
            "created_by": "admin"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            results["employee_documents"] = {
                "status": "✅ WORKING",
                "document_type": "Performance Review"
            }
        else:
            results["employee_documents"] = {
                "status": "❌ FAILED",
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        results["employee_documents"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    return results

def print_results(category, results):
    """Print test results in a formatted way"""
    print(f"\n{category} Results:")
    for test_name, result in results.items():
        status = result.get("status", "❌ UNKNOWN")
        print(f"  {test_name}: {status}")
        
        # Print additional details
        for key, value in result.items():
            if key != "status":
                print(f"    {key}: {value}")

def main():
    """Main test execution"""
    
    # Test basic connectivity
    if not test_basic_connectivity():
        return
    
    # Authenticate
    token = authenticate()
    if not token:
        return
    
    # Run tests
    employee_results, employee_id = test_employee_endpoints(token)
    print_results("Employee Management", employee_results)
    
    if employee_id:
        payroll_results = test_payroll_endpoints(token, employee_id)
        print_results("Payroll Management", payroll_results)
        
        time_results = test_time_attendance_endpoints(token, employee_id)
        print_results("Time & Attendance", time_results)
        
        hr_results = test_hr_management_endpoints(token, employee_id)
        print_results("HR Management", hr_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏥 EMPLOYEE MANAGEMENT SYSTEM ASSESSMENT SUMMARY")
    print("=" * 60)
    
    all_results = {}
    all_results.update(employee_results)
    if employee_id:
        all_results.update(payroll_results)
        all_results.update(time_results)
        all_results.update(hr_results)
    
    working_count = sum(1 for result in all_results.values() if "✅ WORKING" in result.get("status", ""))
    total_count = len(all_results)
    
    print(f"📊 Overall Results: {working_count}/{total_count} endpoints working")
    print(f"📈 Success Rate: {(working_count/total_count)*100:.1f}%")
    
    if working_count >= total_count * 0.8:
        print("🎉 System Status: EXCELLENT - Most features working")
    elif working_count >= total_count * 0.6:
        print("⚠️  System Status: GOOD - Some issues need attention")
    else:
        print("🚨 System Status: NEEDS WORK - Major issues found")

if __name__ == "__main__":
    main()