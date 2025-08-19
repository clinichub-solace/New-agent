from fastapi import APIRouter, Depends
from typing import Dict, Any
from backend.dependencies import get_db, get_current_active_user as get_current_user

router = APIRouter(prefix="/api/payroll/_test", tags=["TEST-ONLY"])

@router.post("/seed/payroll_records")
async def seed_payroll_records(payload: Dict[str, Any], db=Depends(get_db), user=Depends(get_current_user)):
    """
    payload: {"period_id": "...", "records": [{employee_id, gross, net, deductions, record_id}]}
    Inserts normalized payroll_records for deterministic posting.
    """
    period_id = payload.get("period_id")
    records = payload.get("records", [])
    inserted = 0
    for r in records:
        gross = float(r.get("gross", 0.0))
        net = float(r.get("net", 0.0))
        deductions = float(r.get("deductions", 0.0))
        taxes = float(r.get("taxes", gross - net - deductions))
        doc = {
            "id": r.get("record_id") or str(r.get("employee_id")) + "-" + (period_id or ""),
            "payroll_period_id": period_id,
            "employee_id": r.get("employee_id"),
            "employee_name": r.get("employee_id"),
            "gross_pay": str(gross),
            "total_taxes": str(taxes),
            "total_pre_tax_deductions": str(deductions),
            "total_post_tax_deductions": "0.00",
            "net_pay": str(net),
            "status": "calculated",
            "created_at": __import__("datetime").datetime.utcnow(),
        }
        await db.payroll_records.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
        inserted += 1
    return {"inserted": inserted}