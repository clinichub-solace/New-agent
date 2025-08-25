# ClinicHub Smart Forms - Latest Working Version
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

router = APIRouter()

class SmartForm:
    def __init__(self, **data):
        self.id = data.get('id', str(uuid.uuid4()))
        self.form_name = data['form_name']
        self.form_type = data.get('form_type', 'intake')  # intake, consent, assessment
        self.version = data.get('version', '1.0')
        self.fields = data['fields']  # List of field definitions
        self.is_active = data.get('is_active', True)
        self.fhir_mapping = data.get('fhir_mapping', {})
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())

@router.post("/forms")
async def create_form(form_data: dict, db=Depends(get_database)):
    """Create new smart form"""
    try:
        form = SmartForm(**form_data)
        
        form_doc = {
            "id": form.id,
            "form_name": form.form_name,
            "form_type": form.form_type,
            "version": form.version,
            "fields": form.fields,
            "is_active": form.is_active,
            "fhir_mapping": form.fhir_mapping,
            "created_at": form.created_at
        }
        
        await db.forms.insert_one(form_doc)
        return {"id": form.id, "message": "Smart form created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating form: {str(e)}")

@router.get("/forms")
async def get_forms(form_type: Optional[str] = None, active_only: bool = True, db=Depends(get_database)):
    """Get all forms with filtering"""
    try:
        query = {}
        if form_type:
            query["form_type"] = form_type
        if active_only:
            query["is_active"] = True
            
        forms = await db.forms.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        return forms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forms: {str(e)}")

@router.post("/forms/{form_id}/submit")
async def submit_form(form_id: str, submission_data: dict, db=Depends(get_database)):
    """Submit form data and convert to FHIR if mapped"""
    try:
        # Get form definition
        form = await db.forms.find_one({"id": form_id}, {"_id": 0})
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Create submission record
        submission = {
            "id": str(uuid.uuid4()),
            "form_id": form_id,
            "form_name": form["form_name"],
            "submission_data": submission_data,
            "patient_id": submission_data.get("patient_id"),
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "submitted"
        }
        
        await db.form_submissions.insert_one(submission)
        
        # Convert to FHIR if mapping exists
        if form.get("fhir_mapping"):
            fhir_resource = convert_to_fhir(submission_data, form["fhir_mapping"])
            await db.fhir_resources.insert_one(fhir_resource)
        
        return {"id": submission["id"], "message": "Form submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting form: {str(e)}")

def convert_to_fhir(data: dict, mapping: dict) -> dict:
    """Convert form data to FHIR resource"""
    # Simplified FHIR conversion
    fhir_resource = {
        "resourceType": mapping.get("resourceType", "Patient"),
        "id": str(uuid.uuid4()),
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.utcnow().isoformat()
        }
    }
    
    # Apply field mappings
    for form_field, fhir_path in mapping.get("fieldMappings", {}).items():
        if form_field in data:
            # Simple dot notation to FHIR path conversion
            fhir_resource[fhir_path] = data[form_field]
    
    return fhir_resource

# Helper functions
async def get_database():
    pass