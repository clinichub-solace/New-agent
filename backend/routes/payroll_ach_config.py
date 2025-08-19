from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.audit import audit_log

router = APIRouter(prefix="/api/payroll/config", tags=["Payroll • ACH Config"])

@router.put("/ach")
async def put_ach_config(payload: dict, db=Depends(get_db), user=Depends(get_current_user)):
    key = {"_id": "ACH_DEFAULT"}
    payload = {**payload, "updated_by": getattr(user, "id", "system")}
    await db["payroll_ach_config"].update_one(key, {"$set": payload}, upsert=True)
    
    # Audit log the ACH configuration update
    await audit_log(db, user,
        action="payroll.ach.put",
        subject_type="payroll_ach_config",
        subject_id="ACH_DEFAULT",
        meta={"company_name": payload.get("company_name"), "company_id": payload.get("company_id")}
    )
    
    # Notification for ACH configuration update
    from backend.utils.notify import notify_user
    target_user_id = getattr(user, "id", "system")
    
    await notify_user(db,
        user_id=target_user_id,
        type="payroll.ach.put",
        title="ACH configuration updated",
        body=f"ACH settings updated for {payload.get('company_name', 'company')} (ID: {payload.get('company_id', 'N/A')})",
        subject_type="payroll_ach_config",
        subject_id="ACH_DEFAULT",
        severity="info",
        meta={"company_name": payload.get("company_name"), "company_id": payload.get("company_id")}
    )
    
    return {"status": "ok"}

@router.get("/ach")
async def get_ach_config(db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db["payroll_ach_config"].find_one({"_id": "ACH_DEFAULT"})
    if not doc:
        raise HTTPException(status_code=404, detail="ACH config not set")
    return doc