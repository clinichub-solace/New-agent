from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.audit import audit_log

router = APIRouter(prefix="/api/payroll", tags=["Payroll • Bank"])

def _mask(acct: str) -> str:
    s = (acct or "").strip()
    return ("*" * max(len(s) - 4, 0)) + s[-4:] if s else ""

@router.put("/employees/{employee_id}/bank")
async def put_employee_bank(employee_id: str, payload: dict, db=Depends(get_db), user=Depends(get_current_user)):
    if not payload.get("routing_number") or not payload.get("account_number"):
        raise HTTPException(status_code=400, detail="routing_number and account_number are required")
    doc = {
        "employee_id": employee_id,
        "name": payload.get("name") or employee_id,
        "routing_number": "".join(ch for ch in payload["routing_number"] if ch.isdigit()),
        "account_number": "".join(ch for ch in payload["account_number"] if ch.isalnum()),
        "account_type": (payload.get("account_type") or "checking").lower(),
        "updated_by": getattr(user, "id", "system"),
    }
    await db["payroll_employee_bank"].update_one({"employee_id": employee_id}, {"$set": doc}, upsert=True)
    
    # Audit log the employee bank information update
    await audit_log(db, user,
        action="payroll.employee.bank.put",
        subject_type="employee_bank",
        subject_id=employee_id,
        meta={"name": doc.get("name"), "account_type": doc.get("account_type")}
    )
    
    # Notification for employee bank information update
    from backend.utils.notify import notify_user
    target_user_id = getattr(user, "id", "system")
    
    await notify_user(db,
        user_id=target_user_id,
        type="payroll.employee.bank.put",
        title="Employee bank info updated",
        body=f"Bank information updated for {doc.get('name', employee_id)} - {doc.get('account_type', 'checking').title()} account",
        subject_type="employee_bank",
        subject_id=str(employee_id),
        severity="info",
        meta={"name": doc.get("name"), "account_type": doc.get("account_type")}
    )
    
    out = dict(doc); out["account_number"] = _mask(out["account_number"]) 
    return out

@router.get("/employees/{employee_id}/bank")
async def get_employee_bank(employee_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db["payroll_employee_bank"].find_one({"employee_id": employee_id})
    if not doc:
        raise HTTPException(status_code=404, detail="No bank info for employee")
    doc["account_number"] = _mask(doc.get("account_number"))
    return doc