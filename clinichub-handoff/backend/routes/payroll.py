# ClinicHub Payroll System - Latest Working Version  
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import csv
import io

router = APIRouter()

class PayrollPeriod:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.period_start = data['period_start']
        self.period_end = data['period_end']
        self.pay_date = data['pay_date']
        self.status = data.get('status', 'open')  # open, processing, completed
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())

class PayrollRun:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.run_number = data.get('run_number', f"PR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
        self.period_id = data['period_id']
        self.employee_id = data['employee_id']
        self.regular_hours = data.get('regular_hours', 0.0)
        self.overtime_hours = data.get('overtime_hours', 0.0)
        self.gross_pay = data.get('gross_pay', 0.0)
        self.taxes_withheld = data.get('taxes_withheld', 0.0)
        self.deductions = data.get('deductions', 0.0)
        self.net_pay = data.get('net_pay', 0.0)
        self.status = data.get('status', 'draft')
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())

@router.post("/payroll/periods")
async def create_payroll_period(period_data: dict, db=Depends(get_database)):
    """Create new payroll period"""
    try:
        period = PayrollPeriod(**period_data)
        
        period_doc = {
            "id": period.id,
            "period_start": period.period_start,
            "period_end": period.period_end,
            "pay_date": period.pay_date,
            "status": period.status,
            "created_at": period.created_at
        }
        
        await db.payroll_periods.insert_one(period_doc)
        
        return {"id": period.id, "message": "Payroll period created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payroll period: {str(e)}")

@router.get("/payroll/periods")
async def get_payroll_periods(db=Depends(get_database)):
    """Get all payroll periods"""
    try:
        periods = await db.payroll_periods.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return periods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payroll periods: {str(e)}")

@router.post("/payroll/run")
async def process_payroll(period_id: str, db=Depends(get_database)):
    """Process payroll for a period"""
    try:
        # Get all employees
        employees = await db.employees.find({"is_active": True}, {"_id": 0}).to_list(1000)
        
        # Get period details
        period = await db.payroll_periods.find_one({"id": period_id}, {"_id": 0})
        if not period:
            raise HTTPException(status_code=404, detail="Payroll period not found")
        
        payroll_runs = []
        
        for employee in employees:
            # Get time entries for period
            time_entries = await db.time_entries.find({
                "employee_id": employee["id"],
                "entry_date": {
                    "$gte": period["period_start"],
                    "$lte": period["period_end"]
                },
                "approved": True
            }, {"_id": 0}).to_list(1000)
            
            # Calculate hours
            regular_hours = sum(min(entry.get("total_hours", 0), 40) for entry in time_entries)
            overtime_hours = sum(max(entry.get("total_hours", 0) - 40, 0) for entry in time_entries)
            
            # Calculate pay
            hourly_rate = employee.get("hourly_rate", 15.0)
            gross_pay = (regular_hours * hourly_rate) + (overtime_hours * hourly_rate * 1.5)
            
            # Calculate deductions (simplified)
            taxes_withheld = gross_pay * 0.22  # 22% tax withholding
            deductions = employee.get("other_deductions", 0.0)
            net_pay = gross_pay - taxes_withheld - deductions
            
            payroll_run = PayrollRun(
                period_id=period_id,
                employee_id=employee["id"],
                regular_hours=regular_hours,
                overtime_hours=overtime_hours,
                gross_pay=gross_pay,
                taxes_withheld=taxes_withheld,
                deductions=deductions,
                net_pay=net_pay,
                status="processed"
            )
            
            run_doc = {
                "id": payroll_run.id,
                "run_number": payroll_run.run_number,
                "period_id": payroll_run.period_id,
                "employee_id": payroll_run.employee_id,
                "regular_hours": payroll_run.regular_hours,
                "overtime_hours": payroll_run.overtime_hours,
                "gross_pay": payroll_run.gross_pay,
                "taxes_withheld": payroll_run.taxes_withheld,
                "deductions": payroll_run.deductions,
                "net_pay": payroll_run.net_pay,
                "status": payroll_run.status,
                "created_at": payroll_run.created_at
            }
            
            await db.payroll_runs.insert_one(run_doc)
            payroll_runs.append(run_doc)
        
        # Update period status
        await db.payroll_periods.update_one(
            {"id": period_id},
            {"$set": {"status": "processed", "processed_at": datetime.utcnow().isoformat()}}
        )
        
        return {
            "message": f"Payroll processed for {len(payroll_runs)} employees",
            "period_id": period_id,
            "total_runs": len(payroll_runs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing payroll: {str(e)}")

@router.get("/payroll/export/{period_id}")
async def export_payroll_csv(period_id: str, db=Depends(get_database)):
    """Export payroll data as CSV"""
    try:
        payroll_runs = await db.payroll_runs.find({"period_id": period_id}, {"_id": 0}).to_list(1000)
        
        if not payroll_runs:
            raise HTTPException(status_code=404, detail="No payroll data found for period")
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Employee ID', 'Run Number', 'Regular Hours', 'Overtime Hours',
            'Gross Pay', 'Taxes Withheld', 'Deductions', 'Net Pay', 'Status'
        ])
        
        # Data rows
        for run in payroll_runs:
            writer.writerow([
                run['employee_id'],
                run['run_number'],
                run['regular_hours'],
                run['overtime_hours'],
                f"${run['gross_pay']:.2f}",
                f"${run['taxes_withheld']:.2f}",
                f"${run['deductions']:.2f}",
                f"${run['net_pay']:.2f}",
                run['status']
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            "filename": f"payroll_export_{period_id}.csv",
            "content": csv_content,
            "total_records": len(payroll_runs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting payroll: {str(e)}")

# Index creation for performance
async def ensure_payroll_indexes(db):
    """Ensure payroll-related database indexes"""
    try:
        # Time entries indexes
        await db.time_entries.create_index([("employee_id", 1), ("entry_date", -1)])
        await db.time_entries.create_index([("approved", 1)])
        
        # Payroll runs indexes  
        await db.payroll_runs.create_index([("period_id", 1)])
        await db.payroll_runs.create_index([("employee_id", 1), ("created_at", -1)])
        
        # Payroll periods indexes
        await db.payroll_periods.create_index([("status", 1)])
        await db.payroll_periods.create_index([("period_start", 1), ("period_end", 1)])
        
        print("[INFO] Payroll indexes created successfully")
        
    except Exception as e:
        print(f"[WARN] Failed to create payroll indexes: {str(e)}")

# Helper functions
async def get_database():
    # Database dependency injection
    pass