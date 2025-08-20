# backend/utils/forms.py
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

FORMS_COLL = "forms"
SUBMISSIONS_COLL = "form_submissions"

async def ensure_form_indexes(db):
    """Create form indexes if they don't exist"""
    try:
        await db[FORMS_COLL].create_index([("key", 1)], unique=True, background=True)
        await db[FORMS_COLL].create_index([("status", 1), ("updated_at", -1)], background=True)
        await db[SUBMISSIONS_COLL].create_index([("form_id", 1), ("created_at", -1)], background=True)
        await db[SUBMISSIONS_COLL].create_index([("form_key", 1), ("created_at", -1)], background=True)
        print(f"[INFO] Form indexes ensured for collections {FORMS_COLL} and {SUBMISSIONS_COLL}")
    except Exception as e:
        print(f"[WARN] Failed to create form indexes: {e}")

def _now_iso():
    """Get current timestamp as ISO string"""
    return datetime.utcnow().isoformat()

ALLOWED_TYPES = {"text", "textarea", "number", "date", "checkbox", "select", "radio", "email", "phone"}

def validate_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a form schema structure and field definitions
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errs: List[str] = []
    
    if not isinstance(schema, dict):
        errs.append("schema must be a dictionary")
        return False, errs
    
    fields = schema.get("fields", [])
    if not isinstance(fields, list) or not fields:
        errs.append("schema.fields must be a non-empty array")
        return False, errs
    
    seen_keys = set()
    for i, f in enumerate(fields):
        if not isinstance(f, dict):
            errs.append(f"field {i}: must be a dictionary")
            continue
            
        k = f.get("key")
        t = f.get("type")
        lbl = f.get("label")
        
        # Validate key
        if not k or not isinstance(k, str):
            errs.append(f"field {i}: requires a string key")
        elif k in seen_keys:
            errs.append(f"duplicate field key: {k}")
        else:
            seen_keys.add(k)
        
        # Validate type
        if t not in ALLOWED_TYPES:
            errs.append(f"field {k}: unsupported type '{t}' (allowed: {', '.join(ALLOWED_TYPES)})")
        
        # Validate label
        if not lbl:
            errs.append(f"field {k}: label is required")
        
        # Type-specific validation
        if t in {"select", "radio"}:
            opts = f.get("options", [])
            if not isinstance(opts, list) or not opts:
                errs.append(f"field {k}: {t} requires non-empty options[]")
        
        # Validate required flag
        if "required" in f and not isinstance(f["required"], bool):
            errs.append(f"field {k}: required must be boolean")
    
    return len(errs) == 0, errs

def validate_submission(schema: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate form submission data against schema
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errs: List[str] = []
    fields = {f["key"]: f for f in schema.get("fields", [])}
    
    # Check all fields in schema
    for key, cfg in fields.items():
        required = bool(cfg.get("required", False))
        
        # Check required fields
        if required and (key not in data or data[key] is None or data[key] == ""):
            errs.append(f"missing required field '{key}'")
            continue
        
        # Skip validation for empty optional fields
        if key not in data or data[key] is None:
            continue
        
        val = data[key]
        t = cfg["type"]
        
        try:
            # Type-specific validation and conversion
            if t in {"text", "textarea", "email", "phone"}:
                if val is None: 
                    raise ValueError("cannot be null")
                data[key] = str(val).strip()
                
                # Email validation
                if t == "email" and data[key]:
                    if "@" not in data[key] or "." not in data[key]:
                        raise ValueError("invalid email format")
                
                # Phone validation
                if t == "phone" and data[key]:
                    # Basic phone validation - allow digits, spaces, dashes, parentheses
                    cleaned = ''.join(c for c in data[key] if c.isdigit())
                    if len(cleaned) < 10:
                        raise ValueError("phone number too short")
                        
            elif t == "number":
                data[key] = float(val)
                
            elif t == "date":
                # Validate ISO date format (YYYY-MM-DD)
                s = str(val).strip()
                if len(s) != 10 or s[4] != "-" or s[7] != "-":
                    raise ValueError("must be YYYY-MM-DD format")
                # Additional validation
                try:
                    datetime.strptime(s, "%Y-%m-%d")
                    data[key] = s
                except ValueError:
                    raise ValueError("invalid date")
                    
            elif t == "checkbox":
                data[key] = bool(val)
                
            elif t in {"select", "radio"}:
                opts = cfg.get("options", [])
                if str(val) not in [str(opt) for opt in opts]:
                    raise ValueError(f"invalid option '{val}' (allowed: {', '.join(map(str, opts))})")
                data[key] = str(val)
                
            else:
                raise ValueError(f"unsupported type {t}")
                
        except Exception as e:
            errs.append(f"field '{key}': {e}")
    
    # Check for extra fields not in schema
    for key in data:
        if key not in fields:
            errs.append(f"unexpected field '{key}' not in schema")
    
    return len(errs) == 0, errs

def csv_headers_for(schema: Dict[str, Any]) -> List[str]:
    """Get CSV headers from form schema"""
    return [f["key"] for f in schema.get("fields", [])]

def flatten_submission(schema: Dict[str, Any], sub: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a submission for CSV export
    
    Args:
        schema: Form schema
        sub: Submission document
        
    Returns:
        Flattened row dictionary
    """
    data = sub.get("data", {})
    row = {}
    
    # Add form field values
    for field_key in csv_headers_for(schema):
        val = data.get(field_key, "")
        # Convert boolean values to Yes/No for readability
        if isinstance(val, bool):
            val = "Yes" if val else "No"
        row[field_key] = val
    
    # Add metadata fields
    row["_id"] = str(sub.get("_id"))
    row["_created_at"] = sub.get("created_at")
    row["_form_version"] = sub.get("form_version")
    row["_created_by"] = (sub.get("created_by") or {}).get("id")
    
    return row

def get_field_display_value(field_config: Dict[str, Any], value: Any) -> str:
    """
    Get display-friendly value for a form field
    
    Args:
        field_config: Field configuration from schema
        value: Field value
        
    Returns:
        Display-friendly string
    """
    if value is None or value == "":
        return ""
    
    field_type = field_config.get("type")
    
    if field_type == "checkbox":
        return "Yes" if bool(value) else "No"
    elif field_type == "date":
        try:
            # Convert YYYY-MM-DD to more readable format
            dt = datetime.strptime(str(value), "%Y-%m-%d")
            return dt.strftime("%B %d, %Y")
        except:
            return str(value)
    else:
        return str(value)