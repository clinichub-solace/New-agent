# backend/routes/forms.py
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from io import StringIO
import csv
from typing import Optional
from datetime import datetime
from bson import ObjectId
from backend.dependencies import get_db, get_current_active_user as get_current_user
from backend.utils.forms import (
    FORMS_COLL, SUBMISSIONS_COLL, ensure_form_indexes,
    validate_schema, validate_submission,
    csv_headers_for, flatten_submission,
)
from backend.utils.forms_pdf import render_submission_pdf, render_submissions_summary_pdf
from backend.utils.audit import audit_log
from backend.utils.notify import notify_user

router = APIRouter(prefix="/api/forms", tags=["Forms"])

@router.post("")
async def create_or_update_form(
    payload: dict, 
    upsert: bool = Query(True, description="Whether to update existing form"),
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Create or update a form
    
    Body should contain:
    - **name**: Form display name
    - **key**: Unique form key (used for URLs and references)
    - **schema**: Form schema with fields definition
    - **status**: Form status (draft, published, archived)
    - **version**: Form version number
    - **meta**: Additional metadata
    """
    try:
        await ensure_form_indexes(db)
        
        key = payload.get("key")
        name = payload.get("name")
        schema = payload.get("schema") or {}
        
        if not key or not name:
            raise HTTPException(status_code=400, detail="name and key are required")
        
        # Validate schema
        ok, errs = validate_schema(schema)
        if not ok:
            raise HTTPException(status_code=400, detail={"schema_errors": errs})

        # Prepare form document
        base = {
            "name": name,
            "key": key,
            "status": payload.get("status") or "draft",  # draft|published|archived
            "version": int(payload.get("version") or 1),
            "schema": schema,
            "meta": payload.get("meta") or {},
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": {"id": getattr(user, "id", None), "username": getattr(user, "username", None)},
        }
        
        # Check if form exists
        existing = await db[FORMS_COLL].find_one({"key": key})
        
        if existing and not upsert:
            raise HTTPException(status_code=409, detail="form with key exists")
        
        if existing:
            # Update existing form
            await db[FORMS_COLL].update_one({"_id": existing["_id"]}, {"$set": base})
            doc = await db[FORMS_COLL].find_one({"_id": existing["_id"]})
            action = "forms.update"
        else:
            # Create new form
            base["created_at"] = base["updated_at"]
            base["created_by"] = base["updated_by"]
            res = await db[FORMS_COLL].insert_one(base)
            doc = await db[FORMS_COLL].find_one({"_id": res.inserted_id})
            action = "forms.create"

        # Audit and notify
        await audit_log(db, user, 
                       action=action, 
                       subject_type="form", 
                       subject_id=str(doc["_id"]),
                       meta={"key": key, "status": doc["status"], "version": doc["version"]})
        
        await notify_user(db, 
                         user_id=getattr(user, "id", "system"), 
                         type=action,
                         title="Form saved", 
                         body=f"Form '{doc['name']}' ({doc['key']}) saved successfully.",
                         subject_type="form",
                         subject_id=str(doc["_id"]),
                         severity="success")
        
        # Convert ObjectId to string for JSON response
        doc["_id"] = str(doc["_id"])
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create/update form: {e}")
        raise HTTPException(status_code=500, detail="Failed to create/update form")

@router.post("/{form_id}/publish")
async def publish_form(
    form_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Publish a form (make it available for submissions)
    """
    try:
        # Find form by ID or key
        doc = None
        
        # Try as ObjectId if it looks like one
        if len(form_id) == 24:
            try:
                obj_id = ObjectId(form_id)
                doc = await db[FORMS_COLL].find_one({"_id": obj_id})
            except:
                pass
        
        # If not found by ObjectId, try by key
        if not doc:
            doc = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="form not found")
        
        # Increment version and set status to published
        new_ver = int(doc.get("version", 1)) + 1
        update_data = {
            "status": "published", 
            "version": new_ver,
            "published_at": datetime.utcnow().isoformat(),
            "published_by": {"id": getattr(user, "id", None), "username": getattr(user, "username", None)},
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": {"id": getattr(user, "id", None), "username": getattr(user, "username", None)}
        }
        
        await db[FORMS_COLL].update_one({"_id": doc["_id"]}, {"$set": update_data})
        doc = await db[FORMS_COLL].find_one({"_id": doc["_id"]})
        
        # Audit and notify
        await audit_log(db, user, 
                       action="forms.publish", 
                       subject_type="form", 
                       subject_id=str(doc["_id"]),
                       meta={"key": doc["key"], "version": doc["version"]})
        
        await notify_user(db, 
                         user_id=getattr(user, "id", "system"), 
                         type="forms.publish",
                         title="Form published", 
                         body=f"Form '{doc['name']}' is now live and accepting submissions (v{doc['version']}).",
                         subject_type="form",
                         subject_id=str(doc["_id"]),
                         severity="success")
        
        doc["_id"] = str(doc["_id"])
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to publish form: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish form")

@router.get("")
async def list_forms(
    status: Optional[str] = Query(None, description="Filter by status (draft, published, archived)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of forms to return"),
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    List all forms with optional status filtering
    """
    try:
        q = {}
        if status: 
            q["status"] = status
        
        items = await db[FORMS_COLL].find(q).sort("updated_at", -1).limit(limit).to_list(None)
        
        # Convert ObjectIds to strings
        for item in items: 
            item["_id"] = str(item["_id"])
        
        return items
        
    except Exception as e:
        print(f"[ERROR] Failed to list forms: {e}")
        raise HTTPException(status_code=500, detail="Failed to list forms")

@router.get("/{form_id}")
async def get_form(
    form_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Get a specific form by ID or key
    """
    try:
        # Try by MongoDB ObjectId first, then by key
        doc = None
        
        # Try as ObjectId if it looks like one
        if len(form_id) == 24:
            try:
                obj_id = ObjectId(form_id)
                doc = await db[FORMS_COLL].find_one({"_id": obj_id})
            except:
                pass
        
        # If not found by ObjectId, try by key
        if not doc:
            doc = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="form not found")
        
        doc["_id"] = str(doc["_id"])
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get form: {e}")
        raise HTTPException(status_code=500, detail="Failed to get form")

@router.get("/by-key/{form_key}")
async def get_form_by_key(
    form_key: str, 
    published_only: bool = Query(True, description="Only return published forms"),
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Get a form by its key, optionally filtering to published forms only
    """
    try:
        q = {"key": form_key}
        if published_only:
            q["status"] = "published"
        
        doc = await db[FORMS_COLL].find_one(q)
        
        if not doc:
            if published_only:
                raise HTTPException(status_code=404, detail="published form not found")
            else:
                raise HTTPException(status_code=404, detail="form not found")
        
        doc["_id"] = str(doc["_id"])
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get form by key: {e}")
        raise HTTPException(status_code=500, detail="Failed to get form by key")

@router.post("/{form_id}/submit")
async def submit_form(
    form_id: str, 
    payload: dict, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Submit form data
    
    Body should contain:
    - **data**: Dictionary of field values keyed by field key
    """
    try:
        # Find form
        form = None
        
        # Try as ObjectId if it looks like one
        if len(form_id) == 24:
            try:
                obj_id = ObjectId(form_id)
                form = await db[FORMS_COLL].find_one({"_id": obj_id})
            except:
                pass
        
        # If not found by ObjectId, try by key
        if not form:
            form = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not form:
            raise HTTPException(status_code=404, detail="form not found")
            
        if form.get("status") != "published":
            raise HTTPException(status_code=400, detail="form is not published and cannot accept submissions")
        
        # Validate submission data
        data = payload.get("data") or {}
        ok, errs = validate_submission(form["schema"], data)
        if not ok:
            raise HTTPException(status_code=400, detail={"validation_errors": errs})
        
        # Create submission document
        submission_doc = {
            "form_id": str(form["_id"]),
            "form_key": form["key"],
            "form_version": form["version"],
            "data": data,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": {"id": getattr(user, "id", None), "username": getattr(user, "username", None)},
            "meta": payload.get("meta", {})
        }
        
        # Insert submission
        res = await db[SUBMISSIONS_COLL].insert_one(submission_doc)
        sub = await db[SUBMISSIONS_COLL].find_one({"_id": res.inserted_id})

        # Audit and notify
        await audit_log(db, user, 
                       action="forms.submit", 
                       subject_type="form", 
                       subject_id=str(form["_id"]),
                       meta={"submission_id": str(res.inserted_id), "form_key": form["key"], "version": form["version"]})
        
        await notify_user(db, 
                         user_id=getattr(user, "id", "system"), 
                         type="forms.submit",
                         title="Form submitted", 
                         body=f"You successfully submitted '{form['name']}'.",
                         subject_type="form", 
                         subject_id=str(form["_id"]),
                         severity="success")

        sub["_id"] = str(sub["_id"])
        return sub
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to submit form: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit form")

@router.get("/{form_id}/submissions")
async def list_submissions(
    form_id: str,
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    limit: int = Query(200, ge=1, le=1000, description="Maximum number of submissions to return"),
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    List submissions for a form
    """
    try:
        # Find form
        form = await db[FORMS_COLL].find_one({"_id": form_id})
        if not form:
            form = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not form:
            raise HTTPException(status_code=404, detail="form not found")
        
        # Build query
        q = {"form_id": str(form["_id"])}
        if since: 
            q["created_at"] = {"$gte": since}
        
        # Get submissions
        items = await db[SUBMISSIONS_COLL].find(q).sort("created_at", -1).limit(limit).to_list(None)
        
        # Convert ObjectIds to strings
        for item in items: 
            item["_id"] = str(item["_id"])
        
        return {
            "form": {
                "_id": str(form["_id"]), 
                "key": form["key"], 
                "name": form["name"],
                "version": form["version"]
            }, 
            "items": items,
            "count": len(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to list submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list submissions")

@router.get("/{form_id}/submissions.csv")
async def export_submissions_csv(
    form_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Export all form submissions as CSV
    """
    try:
        # Find form
        form = await db[FORMS_COLL].find_one({"_id": form_id})
        if not form:
            form = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not form:
            raise HTTPException(status_code=404, detail="form not found")
        
        # Get all submissions for this form
        subs = await db[SUBMISSIONS_COLL].find({"form_id": str(form["_id"])}).sort("created_at", -1).to_list(None)

        # Generate CSV
        buf = StringIO()
        headers = csv_headers_for(form["schema"]) + ["_id", "_created_at", "_form_version", "_created_by"]
        writer = csv.DictWriter(buf, fieldnames=headers)
        
        writer.writeheader()
        for submission in subs:
            row = flatten_submission(form["schema"], submission)
            writer.writerow(row)
        
        csv_content = buf.getvalue().encode("utf-8")
        
        # Audit and notify
        await audit_log(db, user, 
                       action="forms.export.csv", 
                       subject_type="form", 
                       subject_id=str(form["_id"]),
                       meta={"submissions_count": len(subs)})
        
        await notify_user(db, 
                         user_id=getattr(user, "id", "system"), 
                         type="forms.export.csv",
                         title="Form CSV exported", 
                         body=f"Exported CSV for '{form['name']}' with {len(subs)} submissions.",
                         severity="info")
        
        return Response(
            content=csv_content, 
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=form_{form['key']}_submissions.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to export CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to export CSV")

@router.get("/submissions/{submission_id}.pdf")
async def export_submission_pdf(
    submission_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Export a specific form submission as PDF
    """
    try:
        # Find submission
        sub = await db[SUBMISSIONS_COLL].find_one({"_id": submission_id})
        if not sub:
            raise HTTPException(status_code=404, detail="submission not found")
        
        # Find associated form
        form = await db[FORMS_COLL].find_one({"_id": sub["form_id"]})
        if not form:
            raise HTTPException(status_code=404, detail="associated form not found")
        
        # Generate PDF
        pdf_content = render_submission_pdf(form, sub)
        
        # Audit and notify
        await audit_log(db, user, 
                       action="forms.export.pdf", 
                       subject_type="form", 
                       subject_id=str(form["_id"]),
                       meta={"submission_id": submission_id})
        
        await notify_user(db, 
                         user_id=getattr(user, "id", "system"), 
                         type="forms.export.pdf",
                         title="Submission PDF exported", 
                         body=f"Exported PDF for '{form['name']}' submission.",
                         severity="info")
        
        return Response(
            content=pdf_content, 
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="form_{form["key"]}_{submission_id[:8]}.pdf"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to export PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")

@router.get("/{form_id}/summary.pdf") 
async def export_form_summary_pdf(
    form_id: str,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Export form submissions summary as PDF
    """
    try:
        # Find form
        form = await db[FORMS_COLL].find_one({"_id": form_id})
        if not form:
            form = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not form:
            raise HTTPException(status_code=404, detail="form not found")
        
        # Get all submissions
        subs = await db[SUBMISSIONS_COLL].find({"form_id": str(form["_id"])}).sort("created_at", -1).to_list(None)
        
        # Generate PDF summary
        pdf_content = render_submissions_summary_pdf(form, subs)
        
        # Audit and notify
        await audit_log(db, user,
                       action="forms.export.summary_pdf",
                       subject_type="form",
                       subject_id=str(form["_id"]),
                       meta={"submissions_count": len(subs)})
        
        await notify_user(db,
                         user_id=getattr(user, "id", "system"),
                         type="forms.export.summary_pdf",
                         title="Form summary PDF exported",
                         body=f"Exported summary PDF for '{form['name']}' with {len(subs)} submissions.",
                         severity="info")
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="form_{form["key"]}_summary.pdf"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to export summary PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to export summary PDF")

@router.delete("/{form_id}")
async def delete_form(
    form_id: str,
    cascade: bool = Query(False, description="Also delete all submissions"),
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Delete a form and optionally its submissions
    """
    try:
        # Find form
        form = await db[FORMS_COLL].find_one({"_id": form_id})
        if not form:
            form = await db[FORMS_COLL].find_one({"key": form_id})
        
        if not form:
            raise HTTPException(status_code=404, detail="form not found")
        
        form_obj_id = form["_id"]
        submissions_count = 0
        
        if cascade:
            # Delete all submissions
            delete_result = await db[SUBMISSIONS_COLL].delete_many({"form_id": str(form_obj_id)})
            submissions_count = delete_result.deleted_count
        else:
            # Check if form has submissions
            sub_count = await db[SUBMISSIONS_COLL].count_documents({"form_id": str(form_obj_id)})
            if sub_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Form has {sub_count} submissions. Use cascade=true to delete them as well."
                )
        
        # Delete the form
        await db[FORMS_COLL].delete_one({"_id": form_obj_id})
        
        # Audit and notify
        await audit_log(db, user,
                       action="forms.delete",
                       subject_type="form",
                       subject_id=str(form_obj_id),
                       meta={"key": form["key"], "cascade": cascade, "submissions_deleted": submissions_count})
        
        await notify_user(db,
                         user_id=getattr(user, "id", "system"),
                         type="forms.delete",
                         title="Form deleted",
                         body=f"Form '{form['name']}' deleted" + (f" with {submissions_count} submissions" if cascade else ""),
                         severity="warning")
        
        return {
            "deleted": True,
            "form_id": str(form_obj_id),
            "submissions_deleted": submissions_count if cascade else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete form: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete form")