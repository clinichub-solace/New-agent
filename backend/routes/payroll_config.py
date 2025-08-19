from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_db, get_current_active_user as get_current_user

router = APIRouter(prefix="/api/payroll/config", tags=["Payroll Config"])

@router.put("/tax")
async def put_tax_table(payload: dict, db=Depends(get_db), user=Depends(get_current_user)):
    key = {"jurisdiction": payload["jurisdiction"], "effective_date": payload["effective_date"]}
    await db["payroll_tax_tables"].update_one(key, {"$set": payload}, upsert=True)
    return await db["payroll_tax_tables"].find_one(key, {"_id": 0})

@router.get("/tax")
async def get_tax_table(jurisdiction: str, effective_date: str, db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db["payroll_tax_tables"].find_one({"jurisdiction": jurisdiction, "effective_date": effective_date}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Tax table not found")
    return doc