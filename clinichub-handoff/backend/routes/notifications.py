# ClinicHub Notifications System - Latest Working Version
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter()

class Notification:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.title = data['title']
        self.message = data['message']
        self.notification_type = data.get('notification_type', 'general')  # general, clinical, system, urgent
        self.severity = data.get('severity', 'info')  # info, success, warning, error
        self.recipient_id = data.get('recipient_id')
        self.recipient_type = data.get('recipient_type', 'user')  # user, role, all
        self.related_resource_type = data.get('related_resource_type')
        self.related_resource_id = data.get('related_resource_id')
        self.acknowledged = data.get('acknowledged', False)
        self.acknowledged_at = data.get('acknowledged_at')
        self.acknowledged_by = data.get('acknowledged_by')
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.expires_at = data.get('expires_at')

@router.post("/notifications")
async def create_notification(notification_data: dict, db=Depends(get_database)):
    """Create new notification"""
    try:
        notification = Notification(**notification_data)
        
        notification_doc = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "severity": notification.severity,
            "recipient_id": notification.recipient_id,
            "recipient_type": notification.recipient_type,
            "related_resource_type": notification.related_resource_type,
            "related_resource_id": notification.related_resource_id,
            "acknowledged": notification.acknowledged,
            "acknowledged_at": notification.acknowledged_at,
            "acknowledged_by": notification.acknowledged_by,
            "created_at": notification.created_at,
            "expires_at": notification.expires_at
        }
        
        await db.notifications.insert_one(notification_doc)
        
        return {"id": notification.id, "message": "Notification created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@router.get("/notifications")
async def get_notifications(
    recipient_id: Optional[str] = None,
    notification_type: Optional[str] = None,
    severity: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    db=Depends(get_database)
):
    """Get notifications with filtering"""
    try:
        query = {}
        
        if recipient_id:
            query["$or"] = [
                {"recipient_id": recipient_id},
                {"recipient_type": "all"}
            ]
        
        if notification_type:
            query["notification_type"] = notification_type
            
        if severity:
            query["severity"] = severity
            
        if unread_only:
            query["acknowledged"] = False
        
        # Check for expired notifications
        now = datetime.utcnow().isoformat()
        query["$or"] = query.get("$or", []) + [
            {"expires_at": None},
            {"expires_at": {"$gte": now}}
        ]
        
        notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@router.put("/notifications/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: str, acknowledged_by: str, db=Depends(get_database)):
    """Mark notification as acknowledged"""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id},
            {
                "$set": {
                    "acknowledged": True,
                    "acknowledged_at": datetime.utcnow().isoformat(),
                    "acknowledged_by": acknowledged_by
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error acknowledging notification: {str(e)}")

@router.get("/notifications/count")
async def get_notification_counts(recipient_id: Optional[str] = None, db=Depends(get_database)):
    """Get notification counts by severity and type"""
    try:
        query = {}
        if recipient_id:
            query["$or"] = [
                {"recipient_id": recipient_id},
                {"recipient_type": "all"}
            ]
        
        # Count by severity
        severity_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        
        severity_counts = await db.notifications.aggregate(severity_pipeline).to_list(10)
        
        # Count unread
        unread_count = await db.notifications.count_documents({**query, "acknowledged": False})
        
        return {
            "unread_count": unread_count,
            "by_severity": {item["_id"]: item["count"] for item in severity_counts},
            "recipient_id": recipient_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notification counts: {str(e)}")

# Helper functions for creating specific notification types
async def notify_payroll_event(event_type: str, details: dict, db):
    """Create payroll-related notification"""
    notification_data = {
        "title": f"Payroll {event_type.title()}",
        "message": f"Payroll {event_type} completed successfully",
        "notification_type": "payroll",
        "severity": "info",
        "recipient_type": "role",
        "recipient_id": "admin",
        "related_resource_type": "payroll",
        "details": details
    }
    
    await create_notification(notification_data, db)

async def notify_clinical_alert(alert_type: str, patient_id: str, message: str, db):
    """Create clinical alert notification"""
    notification_data = {
        "title": f"Clinical Alert: {alert_type}",
        "message": message,
        "notification_type": "clinical",
        "severity": "warning",
        "recipient_type": "role",
        "recipient_id": "doctor",
        "related_resource_type": "patient",
        "related_resource_id": patient_id
    }
    
    await create_notification(notification_data, db)

# Index creation
async def ensure_notification_indexes(db):
    """Ensure notification database indexes for performance"""
    try:
        await db.notifications.create_index([("recipient_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("acknowledged", 1), ("created_at", -1)])
        await db.notifications.create_index([("severity", 1)])
        await db.notifications.create_index([("notification_type", 1)])
        await db.notifications.create_index([("expires_at", 1)])
        
        print("[INFO] Notification indexes created successfully")
        
    except Exception as e:
        print(f"[WARN] Failed to create notification indexes: {str(e)}")

# Helper functions
async def get_database():
    # Database dependency injection
    pass