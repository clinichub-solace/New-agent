# ClinicHub Receipts Module - Latest Working Version
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter()

# Receipt Models
class Receipt:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.receipt_number = data.get('receipt_number', f"REC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
        self.patient_id = data['patient_id']
        self.amount = float(data['amount'])
        self.payment_method = data.get('payment_method', 'cash')
        self.services = data.get('services', [])
        self.tax_amount = data.get('tax_amount', 0.0)
        self.total_amount = self.amount + self.tax_amount
        self.status = data.get('status', 'completed')
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.created_by = data.get('created_by', 'system')

@router.post("/receipts")
async def create_receipt(receipt_data: dict, db=Depends(get_database)):
    """Create a new receipt for patient payment"""
    try:
        receipt = Receipt(**receipt_data)
        
        receipt_doc = {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "patient_id": receipt.patient_id,
            "amount": receipt.amount,
            "payment_method": receipt.payment_method,
            "services": receipt.services,
            "tax_amount": receipt.tax_amount,
            "total_amount": receipt.total_amount,
            "status": receipt.status,
            "created_at": receipt.created_at,
            "created_by": receipt.created_by
        }
        
        await db.receipts.insert_one(receipt_doc)
        
        # Create audit trail
        await create_audit_event(
            event_type="create",
            resource_type="receipt",
            resource_id=receipt.id,
            user_id=receipt.created_by,
            user_name=receipt.created_by,
            success=True,
            details=f"Receipt {receipt.receipt_number} created for ${receipt.total_amount}"
        )
        
        return {"id": receipt.id, "receipt_number": receipt.receipt_number, "total_amount": receipt.total_amount}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating receipt: {str(e)}")

@router.get("/receipts")
async def get_receipts(limit: int = 50, db=Depends(get_database)):
    """Get all receipts with pagination"""
    try:
        receipts = await db.receipts.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return receipts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching receipts: {str(e)}")

@router.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str, db=Depends(get_database)):
    """Get specific receipt by ID"""
    try:
        receipt = await db.receipts.find_one({"id": receipt_id}, {"_id": 0})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return receipt
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching receipt: {str(e)}")

@router.get("/receipts/patient/{patient_id}")
async def get_patient_receipts(patient_id: str, db=Depends(get_database)):
    """Get all receipts for a specific patient"""
    try:
        receipts = await db.receipts.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return receipts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient receipts: {str(e)}")

# Helper functions (to be imported)
async def get_database():
    # Database dependency injection
    pass

async def create_audit_event(**kwargs):
    # Audit logging
    pass