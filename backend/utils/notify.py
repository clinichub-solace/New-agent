# backend/utils/notify.py
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping, Optional

NOTIF_COLL = "notifications"

async def ensure_notification_indexes(db):
    """Create notification indexes if they don't exist"""
    try:
        await db[NOTIF_COLL].create_index([("ts", -1)], background=True)
        await db[NOTIF_COLL].create_index([("user_id", 1), ("read", 1), ("ts", -1)], background=True)
        await db[NOTIF_COLL].create_index([("type", 1), ("ts", -1)], background=True)
        await db[NOTIF_COLL].create_index([("subject_type", 1), ("subject_id", 1), ("ts", -1)], background=True)
        print(f"[INFO] Notification indexes ensured for collection {NOTIF_COLL}")
    except Exception as e:
        print(f"[WARN] Failed to create notification indexes: {e}")

async def notify_user(
    db,
    *,
    user_id: str,
    type: str,
    title: str,
    body: str,
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    severity: str = "info",  # info | warning | error | success
    meta: Optional[Mapping[str, Any]] = None,
):
    """
    Create a notification for a specific user
    """
    doc = {
        "ts": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "type": type,
        "title": title[:140],  # Truncate title to reasonable length
        "body": body[:3000],   # Truncate body to reasonable length
        "subject_type": subject_type,
        "subject_id": subject_id,
        "severity": severity,
        "meta": dict(meta or {}),
        "read": False,
        "read_ts": None,
    }
    
    try:
        await db[NOTIF_COLL].insert_one(doc)
        return doc
    except Exception as e:
        print(f"[ERROR] Failed to create notification: {e}")
        return None

async def notify_many(
    db,
    *,
    user_ids: list[str],
    **kwargs
):
    """
    Create notifications for multiple users
    """
    out = []
    for uid in user_ids:
        doc = await notify_user(db, user_id=uid, **kwargs)
        if doc:
            out.append(doc)
    return out

async def mark_read(db, notif_id: Any, user_id: str):
    """
    Mark a specific notification as read
    """
    try:
        from bson import ObjectId
        # Handle both string and ObjectId
        if isinstance(notif_id, str):
            try:
                notif_id = ObjectId(notif_id)
            except:
                # If not a valid ObjectId, keep as string
                pass
        
        ts = datetime.utcnow().isoformat()
        await db[NOTIF_COLL].update_one(
            {"_id": notif_id, "user_id": user_id}, 
            {"$set": {"read": True, "read_ts": ts}}
        )
        return await db[NOTIF_COLL].find_one({"_id": notif_id, "user_id": user_id})
    except Exception as e:
        print(f"[ERROR] Failed to mark notification as read: {e}")
        return None

async def mark_all_read(db, user_id: str):
    """
    Mark all notifications as read for a user
    """
    try:
        ts = datetime.utcnow().isoformat()
        result = await db[NOTIF_COLL].update_many(
            {"user_id": user_id, "read": False}, 
            {"$set": {"read": True, "read_ts": ts}}
        )
        return {"updated": True, "count": result.modified_count}
    except Exception as e:
        print(f"[ERROR] Failed to mark all notifications as read: {e}")
        return {"updated": False, "count": 0}

async def get_unread_count(db, user_id: str):
    """
    Get count of unread notifications for a user
    """
    try:
        count = await db[NOTIF_COLL].count_documents({"user_id": user_id, "read": False})
        return count
    except Exception as e:
        print(f"[ERROR] Failed to get unread count: {e}")
        return 0