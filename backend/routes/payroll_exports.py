from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from typing import Optional
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.audit import audit_log
import csv
import io

router = APIRouter(prefix="/api/payroll", tags=["payroll-exports"])

@router.get("/runs/{run_id}/paystubs.csv")
async def export_paystubs_csv(
    run_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export paystubs for a payroll run as CSV"""
    # Find the run
    run = await db.payroll_runs.find_one({"id": run_id})
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    # Find the period
    period = await db.pay_periods.find_one({"id": run.get("period_id")})
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    
    # Find payroll records for this period
    records_cursor = db.payroll_records.find({"payroll_period_id": period["id"]})
    records = [r async for r in records_cursor]
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Employee ID', 'Employee Name', 'Period Start', 'Period End',
        'Gross Pay', 'Taxes', 'Deductions', 'Net Pay'
    ])
    
    # Write data rows
    for record in records:
        writer.writerow([
            record.get('employee_id', ''),
            record.get('employee_name', ''),
            period.get('start_date', ''),
            period.get('end_date', ''),
            record.get('gross_pay', '0.00'),
            record.get('total_taxes', '0.00'),
            str(float(record.get('total_pre_tax_deductions', '0.00')) + float(record.get('total_post_tax_deductions', '0.00'))),
            record.get('net_pay', '0.00')
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    # Audit log the CSV export
    await audit_log(db, current_user,
        action="payroll.export.csv",
        subject_type="payroll_run",
        subject_id=run_id,
        meta={"record_count": len(records), "period_id": period.get("id")}
    )
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=paystubs_{run_id}.csv"}
    )

@router.get("/runs/{run_id}/ach")
async def export_ach_file(
    run_id: str,
    mode: Optional[str] = Query(default="live", pattern="^(live|test)$"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export ACH file for payroll run in NACHA PPD format"""
    # Find the run
    run = await db.payroll_runs.find_one({"id": run_id})
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    # Find the period
    period = await db.pay_periods.find_one({"id": run.get("period_id")})
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    
    # Get ACH configuration
    ach_config = await db.payroll_ach_config.find_one({})
    if not ach_config:
        raise HTTPException(status_code=400, detail="ACH configuration not found")
    
    # Find payroll records for this period
    records_cursor = db.payroll_records.find({"payroll_period_id": period["id"]})
    records = [r async for r in records_cursor]
    
    # Generate NACHA PPD format content
    lines = []
    
    # File header record (Type 1)
    lines.append(f"101 {ach_config.get('immediate_destination', '').ljust(10)}{ach_config.get('immediate_origin', '').ljust(10)}{''.ljust(6)}{''.ljust(4)}{'1'.ljust(6)}{''.ljust(33)}")
    
    # Batch header record (Type 5)
    lines.append(f"5200{ach_config.get('company_name', '').ljust(16)}{ach_config.get('company_id', '').ljust(10)}PPD{ach_config.get('entry_description', 'PAYROLL').ljust(10)}{''.ljust(6)}{''.ljust(6)}1{ach_config.get('originating_dfi_identification', '').ljust(8)}0000001")
    
    # Entry detail records (Type 6) - one per employee with direct deposit
    entry_count = 0
    total_amount = 0
    
    for record in records:
        # Check if employee has direct deposit setup
        bank_info = await db.payroll_employee_bank.find_one({"employee_id": record.get("employee_id")})
        if bank_info and float(record.get('net_pay', 0)) > 0:
            entry_count += 1
            amount_cents = int(float(record.get('net_pay', 0)) * 100)
            total_amount += amount_cents
            
            lines.append(f"622{bank_info.get('routing_number', '')}{bank_info.get('account_number', '').ljust(17)}{str(amount_cents).zfill(10)}{record.get('employee_id', '').ljust(15)}{record.get('employee_name', '').ljust(22)}  1{ach_config.get('originating_dfi_identification', '').ljust(8)}{str(entry_count).zfill(7)}")
    
    # Batch control record (Type 8)
    lines.append(f"8200{str(entry_count).zfill(6)}{str(entry_count * 10000000000).zfill(10)}{str(total_amount).zfill(12)}{''.zfill(12)}{ach_config.get('company_id', '').ljust(10)}{''.ljust(19)}{ach_config.get('originating_dfi_identification', '').ljust(8)}0000001")
    
    # File control record (Type 9)
    lines.append(f"9000001{str(entry_count + 2).zfill(6)}1{str(entry_count).zfill(8)}{str(total_amount).zfill(12)}{''.zfill(12)}{''.ljust(39)}")
    
    # Pad to multiple of 10 lines
    while len(lines) % 10 != 0:
        lines.append("9" * 94)
    
    ach_content = "\n".join(lines)
    
    # Audit log the ACH export
    await audit_log(db, current_user,
        action="payroll.export.ach",
        subject_type="payroll_run",
        subject_id=run_id,
        meta={"mode": mode, "entries": entry_count, "total_amount": total_amount / 100, "period_id": period.get("id")}
    )
    
    filename_suffix = "_test" if mode == "test" else ""
    
    return Response(
        content=ach_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=payroll{filename_suffix}_{run_id}.ach"}
    )