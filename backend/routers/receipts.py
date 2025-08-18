# app/backend/routers/receipts.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

@router.get("")
async def list_receipts():
    # TODO: fetch receipts from DB
    return []

@router.get("/{rid}")
async def get_receipt(rid: str):
    # TODO: fetch single receipt
    # raise HTTPException(status_code=404, detail="Receipt not found")
    return {"id": rid}

@router.post("/soap-note/{note_id}")
async def create_from_soap(note_id: str):
    # TODO: generate receipt from SOAP note
    return {"created": True, "note": note_id}