# app/backend/routers/time_tracking.py
from fastapi import APIRouter, HTTPException
router = APIRouter(prefix="/api/employees", tags=["time-tracking"])

@router.post("/{eid}/clock-in")
async def clock_in(eid: str):
    # TODO: record clock-in event
    return {"employee": eid, "status": "clocked-in"}

@router.post("/{eid}/clock-out")
async def clock_out(eid: str):
    # TODO: record clock-out event
    return {"employee": eid, "status": "clocked-out"}

@router.get("/{eid}/time-status")
async def time_status(eid: str):
    # TODO: return current status
    return {"employee": eid, "clocked_in": False}

@router.get("/{eid}/time-entries/today")
async def today_entries(eid: str):
    # TODO: return today's entries
    return {"employee": eid, "entries": []}