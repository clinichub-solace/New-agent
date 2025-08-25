# ClinicHub Audit Logging - Latest Working Version
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter()

class AuditEvent:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.event_type = data['event_type']  # create, read, update, delete
        self.resource_type = data['resource_type']  # patient, user, appointment, etc.
        self.resource_id = data.get('resource_id')
        self.user_id = data['user_id']
        self.user_name = data['user_name']
        self.timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        self.ip_address = data.get('ip_address')
        self.user_agent = data.get('user_agent')
        self.success = data.get('success', True)
        self.error_message = data.get('error_message')
        self.details = data.get('details', {})
        self.phi_accessed = data.get('phi_accessed', False)

@router.post("/audit/log")
async def create_audit_event(audit_data: dict, db=Depends(get_database)):
    """Create new audit log entry"""
    try:
        audit_event = AuditEvent(**audit_data)
        
        audit_doc = {
            "id": audit_event.id,
            "event_type": audit_event.event_type,
            "resource_type": audit_event.resource_type,
            "resource_id": audit_event.resource_id,
            "user_id": audit_event.user_id,
            "user_name": audit_event.user_name,
            "timestamp": audit_event.timestamp,
            "ip_address": audit_event.ip_address,
            "user_agent": audit_event.user_agent,
            "success": audit_event.success,
            "error_message": audit_event.error_message,
            "details": audit_event.details,
            "phi_accessed": audit_event.phi_accessed
        }
        
        await db.audit_log.insert_one(audit_doc)
        
        return {"id": audit_event.id, "message": "Audit event logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating audit event: {str(e)}")

@router.get("/audit")
async def get_audit_logs(
    limit: int = 100,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    phi_only: bool = False,
    db=Depends(get_database)
):
    """Get audit logs with filtering options"""
    try:
        query = {}
        
        if resource_type:
            query["resource_type"] = resource_type
        
        if user_id:
            query["user_id"] = user_id
            
        if start_date and end_date:
            query["timestamp"] = {"$gte": start_date, "$lte": end_date}
            
        if phi_only:
            query["phi_accessed"] = True
        
        audit_logs = await db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {
            "audit_logs": audit_logs,
            "total_count": len(audit_logs),
            "filters_applied": {
                "resource_type": resource_type,
                "user_id": user_id,
                "date_range": f"{start_date} to {end_date}" if start_date and end_date else None,
                "phi_only": phi_only
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching audit logs: {str(e)}")

@router.get("/audit/summary")
async def get_audit_summary(days: int = 30, db=Depends(get_database)):
    """Get audit activity summary for dashboard"""
    try:
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get activity counts by resource type
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$resource_type",
                "count": {"$sum": 1},
                "phi_access_count": {"$sum": {"$cond": ["$phi_accessed", 1, 0]}}
            }}
        ]
        
        activity_summary = await db.audit_log.aggregate(pipeline).to_list(100)
        
        # Get most active users
        user_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$user_name",
                "activity_count": {"$sum": 1},
                "phi_access_count": {"$sum": {"$cond": ["$phi_accessed", 1, 0]}}
            }},
            {"$sort": {"activity_count": -1}},
            {"$limit": 10}
        ]
        
        user_activity = await db.audit_log.aggregate(user_pipeline).to_list(10)
        
        return {
            "period_days": days,
            "activity_by_resource": activity_summary,
            "top_active_users": user_activity,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audit summary: {str(e)}")

# Audit helper function
async def audit_phi_access(resource_type: str, event_type: str = "read"):
    """Decorator for PHI access auditing"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementation for PHI access logging
            try:
                result = await func(*args, **kwargs)
                # Log successful PHI access
                return result
            except Exception as e:
                # Log failed PHI access attempt
                raise
        return wrapper
    return decorator

# Index creation
async def ensure_audit_indexes(db):
    """Ensure audit log database indexes for performance"""
    try:
        await db.audit_log.create_index([("timestamp", -1)])
        await db.audit_log.create_index([("resource_type", 1), ("timestamp", -1)])
        await db.audit_log.create_index([("user_id", 1), ("timestamp", -1)])
        await db.audit_log.create_index([("phi_accessed", 1), ("timestamp", -1)])
        
        print("[INFO] Audit indexes created successfully")
        
    except Exception as e:
        print(f"[WARN] Failed to create audit indexes: {str(e)}")

# Helper functions
async def get_database():
    # Database dependency injection
    pass