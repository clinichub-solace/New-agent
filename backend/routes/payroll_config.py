from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.audit import audit_log

router = APIRouter(prefix="/api/payroll/config", tags=["Payroll Config"])

@router.put("/tax")
async def put_tax_table(payload: dict, db=Depends(get_db), user=Depends(get_current_user)):
    key = {"jurisdiction": payload["jurisdiction"], "effective_date": payload["effective_date"]}
    await db["payroll_tax_tables"].update_one(key, {"$set": payload}, upsert=True)
    
    # Audit log the tax configuration update
    await audit_log(db, user,
        action="payroll.tax.put",
        subject_type="payroll_tax_table",
        subject_id=f"{payload.get('jurisdiction')}@{payload.get('effective_date')}",
        meta={"jurisdiction": payload.get("jurisdiction"), "effective_date": payload.get("effective_date")}
    )
    
    return await db["payroll_tax_tables"].find_one(key, {"_id": 0})

@router.get("/tax")
async def get_tax_table(jurisdiction: str, effective_date: str, db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db["payroll_tax_tables"].find_one({"jurisdiction": jurisdiction, "effective_date": effective_date}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Tax table not found")
    return doc