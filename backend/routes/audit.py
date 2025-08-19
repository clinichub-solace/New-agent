# backend/routes/audit.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.audit import AUDIT_COLL

router = APIRouter(prefix="/api/audit", tags=["Audit"])

@router.get("")
async def list_audit(
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    limit: int = Query(100, ge=1, le=1000),
    db = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Get audit log entries with optional filtering.
    
    - **subject_type**: Filter by subject type (e.g., 'payroll_run', 'payroll_period')
    - **subject_id**: Filter by specific subject ID
    - **action**: Filter by action (e.g., 'payroll.run.post', 'payroll.export.csv')
    - **since**: Filter entries after this ISO timestamp
    - **limit**: Maximum number of entries to return (1-1000)
    """
    q = {}
    if subject_type: q["subject_type"] = subject_type
    if subject_id:   q["subject_id"] = subject_id
    if action:       q["action"] = action
    if since:        q["ts"] = {"$gte": since}

    try:
        cur = db[AUDIT_COLL].find(q).sort("ts", -1).limit(limit)
        items = await cur.to_list(None)
        return items
    except Exception as e:
        print(f"[ERROR] Failed to query audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")

@router.get("/actions")
async def list_audit_actions(
    db = Depends(get_db),
    user = Depends(get_current_user),
):
    """Get list of distinct audit actions for filtering"""
    try:
        actions = await db[AUDIT_COLL].distinct("action")
        return {"actions": sorted(actions)}
    except Exception as e:
        print(f"[ERROR] Failed to get audit actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit actions")

@router.get("/subject-types")
async def list_audit_subject_types(
    db = Depends(get_db),
    user = Depends(get_current_user),
):
    """Get list of distinct subject types for filtering"""
    try:
        types = await db[AUDIT_COLL].distinct("subject_type")
        return {"subject_types": sorted(types)}
    except Exception as e:
        print(f"[ERROR] Failed to get audit subject types: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit subject types")