# backend/utils/audit.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Mapping, Any

AUDIT_COLL = "audit_log"

async def ensure_audit_indexes(db):
    """Create audit log indexes if they don't exist"""
    try:
        await db[AUDIT_COLL].create_index([("ts", -1)], background=True)
        await db[AUDIT_COLL].create_index([("subject_type", 1), ("subject_id", 1), ("ts", -1)], background=True)
        await db[AUDIT_COLL].create_index([("action", 1), ("ts", -1)], background=True)
        await db[AUDIT_COLL].create_index([("user.id", 1), ("ts", -1)], background=True)
        print(f"[INFO] Audit indexes ensured for collection {AUDIT_COLL}")
    except Exception as e:
        print(f"[WARN] Failed to create audit indexes: {e}")

async def audit_log(
    db,
    user: Any,
    *,
    action: str,
    subject_type: str,
    subject_id: str,
    meta: Optional[Mapping[str, Any]] = None,
    request_id: Optional[str] = None,
):
    """
    Write an immutable audit record. Keep meta lightweight (ids, totals, flags).
    """
    doc = {
        "ts": datetime.utcnow().isoformat(),
        "action": action,                     # e.g. "payroll.run.post"
        "subject_type": subject_type,         # e.g. "payroll_run"
        "subject_id": str(subject_id),
        "user": {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "email": getattr(user, "email", None),
        },
        "meta": dict(meta or {}),
        "request_id": request_id,             # pass through from X-Request-ID if you have it
    }
    
    try:
        await db[AUDIT_COLL].insert_one(doc)
        return doc
    except Exception as e:
        print(f"[ERROR] Failed to write audit log: {e}")
        # Don't fail the main operation if audit logging fails
        return None