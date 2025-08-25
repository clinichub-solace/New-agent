# ClinicHub Time Tracking Module - Latest Working Version
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, time, timedelta
from typing import List, Optional
import uuid

router = APIRouter()

class TimeEntry:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.employee_id = data['employee_id']
        self.clock_in = data.get('clock_in')
        self.clock_out = data.get('clock_out')
        self.break_start = data.get('break_start')
        self.break_end = data.get('break_end')
        self.total_hours = data.get('total_hours', 0.0)
        self.overtime_hours = data.get('overtime_hours', 0.0)
        self.entry_date = data.get('entry_date', datetime.now().strftime('%Y-%m-%d'))
        self.notes = data.get('notes', '')
        self.approved = data.get('approved', False)
        self.approved_by = data.get('approved_by')
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())

@router.post("/time-tracking/clock-in")
async def clock_in(employee_id: str, db=Depends(get_database)):
    """Clock in employee"""
    try:
        # Check if already clocked in
        existing = await db.time_entries.find_one({
            "employee_id": employee_id,
            "entry_date": datetime.now().strftime('%Y-%m-%d'),
            "clock_out": None
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Employee already clocked in")
        
        time_entry = {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "clock_in": datetime.now().isoformat(),
            "clock_out": None,
            "entry_date": datetime.now().strftime('%Y-%m-%d'),
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.time_entries.insert_one(time_entry)
        
        return {"message": "Clocked in successfully", "time": time_entry["clock_in"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clocking in: {str(e)}")

@router.post("/time-tracking/clock-out")
async def clock_out(employee_id: str, db=Depends(get_database)):
    """Clock out employee and calculate hours"""
    try:
        # Find active time entry
        time_entry = await db.time_entries.find_one({
            "employee_id": employee_id,
            "entry_date": datetime.now().strftime('%Y-%m-%d'),
            "clock_out": None
        })
        
        if not time_entry:
            raise HTTPException(status_code=400, detail="No active clock-in found")
        
        clock_out_time = datetime.now().isoformat()
        
        # Calculate total hours
        clock_in = datetime.fromisoformat(time_entry["clock_in"])
        clock_out = datetime.now()
        total_hours = (clock_out - clock_in).total_seconds() / 3600
        
        # Calculate overtime (over 8 hours)
        overtime_hours = max(0, total_hours - 8)
        
        # Update time entry
        await db.time_entries.update_one(
            {"id": time_entry["id"]},
            {
                "$set": {
                    "clock_out": clock_out_time,
                    "total_hours": round(total_hours, 2),
                    "overtime_hours": round(overtime_hours, 2)
                }
            }
        )
        
        return {
            "message": "Clocked out successfully",
            "total_hours": round(total_hours, 2),
            "overtime_hours": round(overtime_hours, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clocking out: {str(e)}")

@router.get("/time-tracking/employee/{employee_id}")
async def get_employee_time_entries(
    employee_id: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_database)
):
    """Get time entries for employee within date range"""
    try:
        query = {"employee_id": employee_id}
        
        if start_date and end_date:
            query["entry_date"] = {"$gte": start_date, "$lte": end_date}
        
        entries = await db.time_entries.find(query, {"_id": 0}).sort("entry_date", -1).to_list(100)
        
        # Calculate totals
        total_hours = sum(entry.get("total_hours", 0) for entry in entries)
        total_overtime = sum(entry.get("overtime_hours", 0) for entry in entries)
        
        return {
            "entries": entries,
            "summary": {
                "total_hours": round(total_hours, 2),
                "total_overtime": round(total_overtime, 2),
                "total_entries": len(entries)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching time entries: {str(e)}")

@router.put("/time-tracking/{entry_id}/approve")
async def approve_time_entry(entry_id: str, approved_by: str, db=Depends(get_database)):
    """Approve time entry for payroll processing"""
    try:
        result = await db.time_entries.update_one(
            {"id": entry_id},
            {
                "$set": {
                    "approved": True,
                    "approved_by": approved_by,
                    "approved_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        return {"message": "Time entry approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving time entry: {str(e)}")

# Helper functions
async def get_database():
    # Database dependency - implement based on your setup
    pass