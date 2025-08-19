# backend/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Literal
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.notify import NOTIF_COLL, ensure_notification_indexes, notify_user, mark_read, mark_all_read, get_unread_count

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
async def list_notifications(
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of notifications to return"),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get notifications for the current user
    
    - **unread_only**: If true, only return unread notifications
    - **since**: Only return notifications after this ISO timestamp
    - **limit**: Maximum number of notifications to return (1-500)
    """
    try:
        q = {"user_id": getattr(user, "id", None)}
        if unread_only:
            q["read"] = False
        if since:
            q["ts"] = {"$gte": since}
        
        cur = db[NOTIF_COLL].find(q).sort("ts", -1).limit(limit)
        notifications = await cur.to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for notif in notifications:
            if "_id" in notif:
                notif["_id"] = str(notif["_id"])
        
        return notifications
    except Exception as e:
        print(f"[ERROR] Failed to list notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

@router.get("/count")
async def get_notification_count(
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """Get total and unread notification counts for the current user"""
    try:
        user_id = getattr(user, "id", None)
        total_count = await db[NOTIF_COLL].count_documents({"user_id": user_id})
        unread_count = await get_unread_count(db, user_id)
        
        return {
            "total": total_count,
            "unread": unread_count
        }
    except Exception as e:
        print(f"[ERROR] Failed to get notification count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification count")

@router.post("")
async def create_notification(
    payload: dict,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create a new notification
    
    Body should contain:
    - **user_id**: Target user ID (optional, defaults to current user)
    - **type**: Notification type (e.g., 'payroll.run.post')
    - **title**: Notification title (max 140 chars)
    - **body**: Notification body (max 3000 chars)
    - **subject_type**: Related subject type (optional)
    - **subject_id**: Related subject ID (optional)
    - **severity**: Severity level (info|warning|error|success, default: info)
    - **meta**: Additional metadata (optional)
    """
    try:
        # Allow users to create notifications for themselves, admins can target others
        target_user_id = payload.get("user_id") or getattr(user, "id", None)
        if not target_user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        # Ensure indexes exist
        await ensure_notification_indexes(db)
        
        doc = await notify_user(
            db,
            user_id=target_user_id,
            type=payload.get("type") or "generic",
            title=payload.get("title") or "Notification",
            body=payload.get("body") or "",
            subject_type=payload.get("subject_type"),
            subject_id=payload.get("subject_id"),
            severity=(payload.get("severity") or "info"),
            meta=payload.get("meta") or {},
        )
        
        if not doc:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        
        # Convert ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.post("/{notif_id}/ack")
async def ack_notification(
    notif_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """Mark a specific notification as read/acknowledged"""
    try:
        doc = await mark_read(db, notif_id, getattr(user, "id", None))
        if not doc:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Convert ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to acknowledge notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge notification")

@router.post("/ack-all")
async def ack_all_notifications(
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    try:
        result = await mark_all_read(db, getattr(user, "id", None))
        return result
    except Exception as e:
        print(f"[ERROR] Failed to acknowledge all notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge all notifications")

@router.delete("/{notif_id}")
async def delete_notification(
    notif_id: str,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """Delete a specific notification"""
    try:
        from bson import ObjectId
        # Handle both string and ObjectId
        if isinstance(notif_id, str):
            try:
                notif_id = ObjectId(notif_id)
            except:
                pass
        
        result = await db[NOTIF_COLL].delete_one({
            "_id": notif_id, 
            "user_id": getattr(user, "id", None)
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")