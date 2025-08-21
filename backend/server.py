from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse, quote
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, date, timedelta
from enum import Enum
from fastapi.encoders import jsonable_encoder
import hashlib
import jwt
from passlib.context import CryptContext
import base64
import aiohttp
import ssl
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from openemr_integration import openemr

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# SECURITY: Helper function to read Docker secrets
def read_secret(secret_name: str, fallback_env: str = None) -> str:
    """Read Docker secret or fall back to environment variable"""
    secret_file = f"/run/secrets/{secret_name}"
    env_file = os.environ.get(f"{fallback_env}_FILE") if fallback_env else None
    
    # Try Docker secret first
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    # Try _FILE environment variable
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            return f.read().strip()
    
    # Fall back to direct environment variable
    if fallback_env:
        return os.environ.get(fallback_env, '')
    
    return ''

# MongoDB connection with secure secret handling
try:
    mongo_url = read_secret('mongo_connection_string', 'MONGO_URL')
    if not mongo_url:
        # No fallback - require proper environment configuration
        raise ValueError("MONGO_URL must be set in environment or secrets")
    
    def sanitize_mongo_uri(uri: str) -> str:
        """Ensure username/password are percent-encoded in the Mongo URI."""
        p = urlparse(uri)
        # If no user/pass present, return as-is
        if not (p.username or p.password):
            return uri

        user = quote(p.username or '', safe='')
        pw   = quote(p.password or '', safe='')
        query = f'?{p.query}' if p.query else ''
        path  = p.path or '/clinichub'
        host  = p.hostname or 'localhost'
        port  = f":{p.port}" if p.port else ''

        return f"mongodb://{user}:{pw}@{host}{port}{path}{query}"

    mongo_url = sanitize_mongo_uri(mongo_url)
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'clinichub')]
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    raise

# Authentication setup with secure secrets
try:
    SECRET_KEY = read_secret('app_secret_key', 'SECRET_KEY')
    JWT_SECRET_KEY = read_secret('jwt_secret_key', 'JWT_SECRET_KEY')
    
    if not SECRET_KEY:
        SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key-change-immediately')
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key-change-immediately')
        
except Exception as e:
    logging.error(f"Failed to load authentication secrets: {e}")
    raise

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Insurance adapter DI (Task 4)
INSURANCE_ADAPTER = os.environ.get("INSURANCE_ADAPTER", "mock").lower()

async def mock_eligibility_adapter(patient: Dict[str, Any], card: Dict[str, Any], payload: "EligibilityCheckRequest") -> "EligibilityCheckResponse":
    """Deterministic MOCK adapter returns coverage & valid_until."""
    from datetime import datetime as _dt, timedelta as _td
    base_copay = 25.0
    deductible = 1000.0
    coins = 0.2
    plan = (card.get("plan_name") or "").lower()
    if "gold" in plan:
        base_copay, deductible, coins = 15.0, 500.0, 0.1
    elif "silver" in plan:
        base_copay, deductible, coins = 25.0, 1000.0, 0.2
    elif "bronze" in plan:
        base_copay, deductible, coins = 40.0, 3000.0, 0.3
    return EligibilityCheckResponse(
        eligible=True,
        coverage={"copay": base_copay, "deductible": deductible, "coinsurance": coins},
        valid_until=(_dt.utcnow() + _td(days=1)).date().isoformat(),
        raw={"adapter": "mock", "transaction_id": str(uuid.uuid4())}
    )

# Domain Event Publishing System for Interoperability
class DomainEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str  # patient.created, encounter.completed, lab.ordered, etc.
    aggregate_type: str  # patient, encounter, lab_order, etc.
    aggregate_id: str
    version: int = 1
    data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class EventPublisher:
    """Event publisher for healthcare interoperability"""
    
    def __init__(self):
        self.events = []  # In-memory for now, will add message queue later
    
    async def publish(self, event_type: str, aggregate_type: str, aggregate_id: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Publish domain event for integration processing"""
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            data=data,
            metadata=metadata or {}
        )
        
        # Store event in database for audit and replay
        await db.domain_events.insert_one(jsonable_encoder(event))
        
        # Log event for external processors (Mirth, FHIR server, etc.)
        logging.info(f"DOMAIN_EVENT: {jsonable_encoder(event)}")
        
        # TODO: Add message queue publishing (RabbitMQ/NATS)
        # await self.message_queue.publish(event_type, event)
        
        return event

# Global event publisher
event_publisher = EventPublisher()

# FHIR R4 Resource Conversion Helpers
class FHIRConverter:
    """Convert ClinicHub data models to FHIR R4 resources"""
    
    @staticmethod
    def patient_to_fhir(patient: "Patient") -> Dict[str, Any]:
        """Convert Patient to FHIR Patient resource"""
        fhir_patient = {
            "resourceType": "Patient",
            "id": patient.id,
            "meta": {
                "profile": ["http://hl7.org/fhir/R4/Patient"]
            },
            "active": patient.status == "active",
            "name": [],
            "telecom": [],
            "gender": patient.gender.lower() if patient.gender else "unknown",
            "birthDate": patient.birth_date.isoformat() if patient.birth_date else None,
            "address": []
        }
        
        # Convert names
        if patient.name:
            for name in patient.name:
                fhir_name = {
                    "use": "official",
                    "family": name.family,
                    "given": name.given
                }
                fhir_patient["name"].append(fhir_name)
        
        # Convert telecom
        if patient.telecom:
            for telecom in patient.telecom:
                fhir_telecom = {
                    "system": telecom.system,
                    "value": telecom.value,
                    "use": "home"
                }
                fhir_patient["telecom"].append(fhir_telecom)
        
        # Convert addresses
        if patient.address:
            for address in patient.address:
                fhir_address = {
                    "use": "home",
                    "line": [address.line] if hasattr(address, 'line') and address.line else [],
                    "city": address.city,
                    "state": address.state,
                    "postalCode": address.postal_code,
                    "country": address.country or "US"
                }
                fhir_patient["address"].append(fhir_address)
        
        return fhir_patient
    
    @staticmethod
    def encounter_to_fhir(encounter: "Encounter", patient: "Patient") -> Dict[str, Any]:
        """Convert Encounter to FHIR Encounter resource"""
        return {
            "resourceType": "Encounter",
            "id": encounter.id,
            "meta": {
                "profile": ["http://hl7.org/fhir/R4/Encounter"]
            },
            "status": encounter.status.lower(),
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB" if hasattr(encounter, 'encounter_type') and encounter.encounter_type == "outpatient" else "IMP",
                "display": "ambulatory" if hasattr(encounter, 'encounter_type') and encounter.encounter_type == "outpatient" else "inpatient encounter"
            },
            "type": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "185349003",
                    "display": "Encounter for check up"
                }]
            }],
            "subject": {
                "reference": f"Patient/{patient.id}",
                "display": f"{patient.name[0].given[0]} {patient.name[0].family}" if patient.name else "Unknown"
            },
            "period": {
                "start": encounter.start_time.isoformat() if hasattr(encounter, 'start_time') and encounter.start_time else None,
                "end": encounter.end_time.isoformat() if hasattr(encounter, 'end_time') and encounter.end_time else None
            }
        }
    
    @staticmethod
    def lab_order_to_fhir(lab_order: "LabOrder", patient: "Patient") -> Dict[str, Any]:
        """Convert LabOrder to FHIR ServiceRequest resource"""
        return {
            "resourceType": "ServiceRequest",
            "id": lab_order.id,
            "meta": {
                "profile": ["http://hl7.org/fhir/R4/ServiceRequest"]
            },
            "status": lab_order.status.lower(),
            "intent": "order",
            "category": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "108252007",
                    "display": "Laboratory procedure"
                }]
            }],
            "priority": lab_order.priority.lower() if hasattr(lab_order, 'priority') else "routine",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "33747-0",
                    "display": "General laboratory studies"
                }]
            },
            "subject": {
                "reference": f"Patient/{patient.id}"
            },
            "authoredOn": lab_order.ordered_date.isoformat() if hasattr(lab_order, 'ordered_date') and lab_order.ordered_date else lab_order.created_at.isoformat(),
            "requester": {
                "display": lab_order.provider_name if hasattr(lab_order, 'provider_name') else lab_order.ordered_by if hasattr(lab_order, 'ordered_by') else "Unknown"
            }
        }

# Global FHIR converter
fhir_converter = FHIRConverter()

# Synology DSM Integration Configuration
SYNOLOGY_DSM_URL = os.environ.get('SYNOLOGY_DSM_URL', None)  # e.g., "https://your-nas:5001"
SYNOLOGY_VERIFY_SSL = os.environ.get('SYNOLOGY_VERIFY_SSL', 'true').lower() == 'true'
SYNOLOGY_SESSION_NAME = os.environ.get('SYNOLOGY_SESSION_NAME', 'ClinicHub')
SYNOLOGY_ENABLED = SYNOLOGY_DSM_URL is not None

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HIPAA Audit Logging System
class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str  # create, read, update, delete, login, logout, access
    resource_type: str  # patient, encounter, medication, etc.
    resource_id: Optional[str] = None
    user_id: str
    user_name: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action_details: Dict[str, Any] = {}
    phi_accessed: bool = False  # Critical for HIPAA compliance
    success: bool = True
    error_message: Optional[str] = None

async def create_audit_event(
    event_type: str,
    resource_type: str,
    user_id: str,
    user_name: str,
    resource_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    action_details: Dict[str, Any] = None,
    phi_accessed: bool = False,
    success: bool = True,
    error_message: str = None
):
    """Create and store HIPAA-compliant audit event"""
    try:
        audit_event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            ip_address=ip_address,
            user_agent=user_agent,
            action_details=action_details or {},
            phi_accessed=phi_accessed,
            success=success,
            error_message=error_message
        )
        
        # Store in database
        await db.audit_events.insert_one(jsonable_encoder(audit_event))
        
        # Also log to stdout for external systems (ELK, Wazuh)
        logging.info(f"AUDIT: {jsonable_encoder(audit_event)}")
        
    except Exception as e:
        # Critical: audit failures should be logged but not break the app
        logging.error(f"AUDIT FAILURE: Failed to create audit event: {e}")

# Audit decorator for PHI-sensitive endpoints
def audit_phi_access(resource_type: str, event_type: str = "read"):
    def decorator(func):
        import inspect
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request info
            request = kwargs.get('request') or (args[0] if args else None)
            current_user = None
            
            # Find current_user in args/kwargs
            for arg in args:
                if hasattr(arg, 'username'):
                    current_user = arg
                    break
            for value in kwargs.values():
                if hasattr(value, 'username'):
                    current_user = value
                    break
            
            # Get function signature and filter kwargs to match expected parameters
            sig = inspect.signature(func)
            filtered_kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name in kwargs:
                    filtered_kwargs[param_name] = kwargs[param_name]
            
            # Execute the function with filtered arguments
            try:
                result = await func(*args, **filtered_kwargs)
                
                # Create audit event for successful access
                if current_user:
                    await create_audit_event(
                        event_type=event_type,
                        resource_type=resource_type,
                        user_id=current_user.id if hasattr(current_user, 'id') else 'unknown',
                        user_name=current_user.username,
                        ip_address=request.client.host if request and hasattr(request, 'client') else None,
                        user_agent=request.headers.get('user-agent') if request and hasattr(request, 'headers') else None,
                        phi_accessed=True,
                        success=True
                    )
                
                return result
                
            except Exception as e:
                # Audit failed access attempts
                if current_user:
                    await create_audit_event(
                        event_type=event_type,
                        resource_type=resource_type,
                        user_id=current_user.id if hasattr(current_user, 'id') else 'unknown',
                        user_name=current_user.username,
                        ip_address=request.client.host if request and hasattr(request, 'client') else None,
                        user_agent=request.headers.get('user-agent') if request and hasattr(request, 'headers') else None,
                        phi_accessed=True,
                        success=False,
                        error_message=str(e)
                    )
                raise
        
        return wrapper
    return decorator

# Create the main app without a prefix
app = FastAPI(title="ClinicHub API", description="AI-Powered Practice Management System")

# Register error handlers
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from .errors import validation_exception_handler, generic_exception_handler

app.add_exception_handler(ValidationError, validation_exception_handler)

# Optional: centralize HTTPException to always use {"detail": ...}
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# last-resort catch-all
@app.exception_handler(Exception)
async def all_exception_handler(request, exc: Exception):
    return await generic_exception_handler(request, exc)

# Include additive routers
from .routers import receipts, time_tracking
from .payroll_enhancements import payroll_router, ensure_indexes
from .routes import payroll_config, payroll_bank, payroll_ach_config, payroll_exports, audit, notifications, forms
app.include_router(receipts.router)
app.include_router(time_tracking.router)

# Startup: ensure indexes for payroll, audit, notifications, and forms
@app.on_event("startup")
async def on_startup():
    try:
        # We have a global db via dependencies; import here to avoid cycles
        from .dependencies import db as _db
        await ensure_indexes(_db)
        
        # Ensure audit indexes
        from .utils.audit import ensure_audit_indexes
        await ensure_audit_indexes(_db)
        
        # Ensure notification indexes
        from .utils.notify import ensure_notification_indexes
        await ensure_notification_indexes(_db)
        
        # Ensure forms indexes
        from .utils.forms import ensure_form_indexes
        await ensure_form_indexes(_db)
    except Exception as e:
        print(f"[startup] index creation failed: {e}")

app.include_router(payroll_router)
app.include_router(payroll_config.router)
app.include_router(payroll_bank.router)
app.include_router(payroll_ach_config.router)
app.include_router(payroll_exports.router)
app.include_router(audit.router)
app.include_router(notifications.router)
app.include_router(forms.router)

# Gate the test-only seeder by ENV
if os.getenv("ENV", "TEST") in {"TEST", "DEV", "DEVELOPMENT"}:
    from .routes import payroll_test_helpers
    app.include_router(payroll_test_helpers.router)


# Add root route for health verification
@app.get("/")
async def root():
    return {
        "message": "ClinicHub API is running", 
        "status": "healthy", 
        "version": "1.0.0",
        "docs": "/docs",
        "api_endpoints": "/api"
    }

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class PatientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"

class FormStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

class ReferralStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class QualityMeasureStatus(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    PENDING = "pending"
    EXCLUDED = "excluded"

class TelehealthStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class TemplateType(str, Enum):
    VISIT_TEMPLATE = "visit_template"
    ASSESSMENT_TEMPLATE = "assessment_template"
    PROCEDURE_TEMPLATE = "procedure_template"
    PROTOCOL = "protocol"
    CARE_PLAN = "care_plan"
    ARCHIVED = "archived"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"  
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class EmployeeRole(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    TECHNICIAN = "technician"

class EncounterType(str, Enum):
    ANNUAL_PHYSICAL = "annual_physical"
    FOLLOW_UP = "follow_up"
    ACUTE_CARE = "acute_care"
    PREVENTIVE_CARE = "preventive_care"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    TELEMEDICINE = "telemedicine"

class EncounterStatus(str, Enum):
    PLANNED = "planned"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AllergySeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"

class MedicationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"

# Authentication and User Management Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    MANAGER = "manager"
    TECHNICIAN = "technician"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# FHIR-Compliant Patient Model
class PatientAddress(BaseModel):
    line: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class PatientTelecom(BaseModel):
    system: str  # phone, email, fax
    value: str
    use: Optional[str] = None  # home, work, mobile

class PatientName(BaseModel):
    family: str
    given: List[str]
    prefix: List[str] = []
    suffix: List[str] = []

class Patient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: str = "Patient"
    name: List[PatientName]
    telecom: List[PatientTelecom] = []
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    address: List[PatientAddress] = []
    marital_status: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    insurance_info: Optional[Dict[str, Any]] = None
    status: PatientStatus = PatientStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

# Smart Form Models
class FormField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # text, number, date, select, checkbox, textarea, signature, file
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: List[str] = []  # for select fields
    smart_tag: Optional[str] = None  # {patient_name}, {date}, etc.
    validation_rules: Dict[str, Any] = {}  # min, max, pattern, etc.
    conditional_logic: Optional[Dict[str, Any]] = None  # show/hide conditions
    order: int = 0

class SmartForm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    status: FormStatus = FormStatus.DRAFT
    fhir_mapping: Optional[Dict[str, str]] = None
    category: str = "custom"  # intake, assessment, vitals, discharge, custom
    is_template: bool = False
    template_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class FormSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    form_id: str
    form_title: str
    patient_id: str
    patient_name: str
    encounter_id: Optional[str] = None
    data: Dict[str, Any]
    processed_data: Dict[str, Any] = {}  # Smart tags processed
    fhir_data: Optional[Dict[str, Any]] = None
    submitted_by: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"  # draft, completed, reviewed

class FormTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    fields: List[FormField]
    fhir_mapping: Dict[str, str] = {}
    is_active: bool = True

# Invoice/Receipt Models
class InvoiceItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    total: float

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    patient_id: str
    items: List[InvoiceItem]
    subtotal: float
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issue_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceCreate(BaseModel):
    patient_id: str
    items: List[InvoiceItem]
    tax_rate: float = 0.0
    due_days: int = 30
    notes: Optional[str] = None

# Inventory Models
class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    sku: Optional[str] = None
    current_stock: int = 0
    min_stock_level: int = 0
    unit_cost: float = 0.0
    supplier: Optional[str] = None
    expiry_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryItemCreate(BaseModel):
    name: str
    category: str
    sku: Optional[str] = None
    current_stock: int = 0
    min_stock_level: int = 0
    unit_cost: float = 0.0
    supplier: Optional[str] = None
    expiry_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class InventoryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: Optional[str] = None  # Made optional since it's set from URL
    transaction_type: str  # in, out, adjustment
    quantity: int
    reference_id: Optional[str] = None  # patient_id, invoice_id, etc.
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Employee Models
# Enhanced Employee Management Models

# Employee Document Types
class EmployeeDocumentType(str, Enum):
    WARNING = "warning"
    VACATION_REQUEST = "vacation_request"
    SICK_LEAVE = "sick_leave"
    PERFORMANCE_REVIEW = "performance_review"
    POLICY_ACKNOWLEDGMENT = "policy_acknowledgment"
    TRAINING_CERTIFICATE = "training_certificate"
    CONTRACT = "contract"
    DISCIPLINARY_ACTION = "disciplinary_action"

class EmployeeDocumentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class TimeEntryType(str, Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"

class ShiftStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"

# Enhanced Employee Profile
class EnhancedEmployee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: EmployeeRole
    department: Optional[str] = None
    hire_date: date
    termination_date: Optional[date] = None
    salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    
    # Personal Information
    date_of_birth: Optional[date] = None
    ssn_last_four: Optional[str] = None  # Only last 4 digits for security
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Employment Details
    manager_id: Optional[str] = None
    work_location: Optional[str] = None
    employment_type: str = "full_time"  # full_time, part_time, contract
    benefits_eligible: bool = True
    vacation_days_allocated: int = 20
    vacation_days_used: int = 0
    sick_days_allocated: int = 10
    sick_days_used: int = 0
    
    # Status
    is_active: bool = True
    profile_picture: Optional[str] = None  # base64 encoded
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# For backward compatibility
class Employee(EnhancedEmployee):
    pass

class EnhancedEmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: EmployeeRole
    department: Optional[str] = None
    hire_date: date
    salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    manager_id: Optional[str] = None
    employment_type: str = "full_time"

# For backward compatibility
class EmployeeCreate(EnhancedEmployeeCreate):
    pass

# Employee Documents
class EmployeeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    document_type: EmployeeDocumentType
    title: str
    content: str  # HTML or text content
    status: EmployeeDocumentStatus = EmployeeDocumentStatus.DRAFT
    
    # Approval Workflow
    created_by: str
    approved_by: Optional[str] = None
    signed_by: Optional[str] = None
    signature_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    
    # Document Data
    template_data: Optional[Dict[str, Any]] = None  # For form fields
    file_attachments: List[str] = []  # base64 encoded files
    
    # Dates
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    due_date: Optional[date] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmployeeDocumentCreate(BaseModel):
    employee_id: str
    document_type: EmployeeDocumentType
    title: str
    content: str
    template_data: Optional[Dict[str, Any]] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    due_date: Optional[date] = None
    created_by: str

# Time Tracking
class TimeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    entry_type: TimeEntryType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    manual_entry: bool = False
    approved_by: Optional[str] = None

class TimeEntryCreate(BaseModel):
    employee_id: str
    entry_type: TimeEntryType
    timestamp: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    manual_entry: bool = False

# Work Schedule
class WorkShift(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    shift_date: date
    start_time: datetime
    end_time: datetime
    break_duration: int = 30  # minutes
    position: Optional[str] = None
    location: Optional[str] = None
    status: ShiftStatus = ShiftStatus.SCHEDULED
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WorkShiftCreate(BaseModel):
    employee_id: str
    shift_date: date
    start_time: datetime
    end_time: datetime
    break_duration: int = 30
    position: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_by: str

# Payroll Models
class PayPeriodType(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"

class PayrollStatus(str, Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
    VOIDED = "voided"

class DeductionType(str, Enum):
    FEDERAL_TAX = "federal_tax"
    STATE_TAX = "state_tax"
    SOCIAL_SECURITY = "social_security"
    MEDICARE = "medicare"
    HEALTH_INSURANCE = "health_insurance"
    DENTAL_INSURANCE = "dental_insurance"
    VISION_INSURANCE = "vision_insurance"
    RETIREMENT_401K = "retirement_401k"
    LIFE_INSURANCE = "life_insurance"
    CUSTOM = "custom"

class PayrollPeriod(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: date
    period_end: date
    pay_date: date
    period_type: PayPeriodType
    status: PayrollStatus = PayrollStatus.DRAFT
    total_gross_pay: float = 0.0
    total_net_pay: float = 0.0
    total_deductions: float = 0.0
    total_taxes: float = 0.0
    employee_count: int = 0
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PayrollDeduction(BaseModel):
    deduction_type: DeductionType
    description: str
    amount: float
    percentage: Optional[float] = None  # If percentage-based
    is_pre_tax: bool = False

class PayrollRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payroll_period_id: str
    employee_id: str
    
    # Time and Pay Data
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    double_time_hours: float = 0.0
    sick_hours: float = 0.0
    vacation_hours: float = 0.0
    holiday_hours: float = 0.0
    
    # Pay Rates
    regular_rate: float
    overtime_rate: Optional[float] = None
    double_time_rate: Optional[float] = None
    
    # Gross Pay Calculations
    regular_pay: float = 0.0
    overtime_pay: float = 0.0
    double_time_pay: float = 0.0
    sick_pay: float = 0.0
    vacation_pay: float = 0.0
    holiday_pay: float = 0.0
    bonus_pay: float = 0.0
    commission_pay: float = 0.0
    other_pay: float = 0.0
    gross_pay: float = 0.0
    
    # Deductions
    deductions: List[PayrollDeduction] = []
    total_deductions: float = 0.0
    
    # Tax Calculations
    federal_tax: float = 0.0
    state_tax: float = 0.0
    social_security_tax: float = 0.0
    medicare_tax: float = 0.0
    total_taxes: float = 0.0
    
    # Net Pay
    net_pay: float = 0.0
    
    # YTD Totals (Year to Date)
    ytd_gross_pay: float = 0.0
    ytd_net_pay: float = 0.0
    ytd_federal_tax: float = 0.0
    ytd_state_tax: float = 0.0
    ytd_social_security_tax: float = 0.0
    ytd_medicare_tax: float = 0.0
    
    # Check Information
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    check_status: PayrollStatus = PayrollStatus.DRAFT
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PayrollRecordCreate(BaseModel):
    payroll_period_id: str
    employee_id: str
    bonus_pay: float = 0.0
    commission_pay: float = 0.0
    other_pay: float = 0.0
    deductions: List[PayrollDeduction] = []

class PaystubData(BaseModel):
    employee_info: Dict[str, Any]
    pay_period: Dict[str, Any]
    hours_breakdown: Dict[str, float]
    pay_breakdown: Dict[str, float]
    deductions_breakdown: List[Dict[str, Any]]
    taxes_breakdown: Dict[str, float]
    ytd_totals: Dict[str, float]
    net_pay: float
    check_number: Optional[str] = None
    check_date: Optional[date] = None

# Finance Module Models

# Finance-related Enums
class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class IncomeCategory(str, Enum):
    PATIENT_PAYMENT = "patient_payment"
    INSURANCE_PAYMENT = "insurance_payment"
    CONSULTATION_FEE = "consultation_fee"
    PROCEDURE_FEE = "procedure_fee"
    MEDICATION_SALE = "medication_sale"
    OTHER_INCOME = "other_income"

class ExpenseCategory(str, Enum):
    PAYROLL = "payroll"
    RENT = "rent"
    UTILITIES = "utilities"
    MEDICAL_SUPPLIES = "medical_supplies"
    INSURANCE = "insurance"
    MARKETING = "marketing"
    MAINTENANCE = "maintenance"
    PROFESSIONAL_FEES = "professional_fees"
    OFFICE_SUPPLIES = "office_supplies"
    OTHER_EXPENSE = "other_expense"

class CheckStatus(str, Enum):
    DRAFT = "draft"
    PRINTED = "printed"
    ISSUED = "issued"
    CASHED = "cashed"
    VOID = "void"
    CANCELLED = "cancelled"

class VendorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Vendor Management
class Vendor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_code: str
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Address Information
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    
    # Business Information
    tax_id: Optional[str] = None  # EIN or SSN
    payment_terms: str = "Net 30"  # Net 30, Net 15, COD, etc.
    preferred_payment_method: PaymentMethod = PaymentMethod.CHECK
    
    # Banking Information (for ACH/Wire transfers)
    bank_name: Optional[str] = None
    routing_number: Optional[str] = None
    account_number: Optional[str] = None
    
    # Status and Notes
    status: VendorStatus = VendorStatus.ACTIVE
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VendorCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    tax_id: Optional[str] = None
    payment_terms: str = "Net 30"
    preferred_payment_method: PaymentMethod = PaymentMethod.CHECK

# Check Management
class Check(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    check_number: str
    payee_type: str = "vendor"  # vendor, employee, other
    payee_id: Optional[str] = None  # vendor_id or employee_id
    payee_name: str
    amount: float
    memo: Optional[str] = None
    
    # Check Details
    check_date: date = Field(default_factory=date.today)
    void_date: Optional[date] = None
    printed_date: Optional[datetime] = None
    issued_date: Optional[datetime] = None
    cashed_date: Optional[datetime] = None
    
    # Status and References
    status: CheckStatus = CheckStatus.DRAFT
    expense_category: Optional[ExpenseCategory] = None
    reference_invoice_id: Optional[str] = None
    reference_payroll_id: Optional[str] = None
    
    # Approval Workflow
    created_by: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CheckCreate(BaseModel):
    payee_type: str = "vendor"
    payee_id: Optional[str] = None
    payee_name: str
    amount: float
    memo: Optional[str] = None
    check_date: Optional[date] = None
    expense_category: Optional[ExpenseCategory] = None
    reference_invoice_id: Optional[str] = None
    created_by: str

# Financial Transactions
class FinancialTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_number: str
    transaction_type: TransactionType
    amount: float
    payment_method: PaymentMethod
    
    # Transaction Details
    transaction_date: date = Field(default_factory=date.today)
    description: str
    category: Optional[str] = None  # IncomeCategory or ExpenseCategory
    
    # References
    patient_id: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_id: Optional[str] = None
    check_id: Optional[str] = None
    
    # Banking Details
    bank_account: Optional[str] = None
    reference_number: Optional[str] = None  # Check number, transaction ID, etc.
    
    # Reconciliation
    reconciled: bool = False
    reconciled_date: Optional[date] = None
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FinancialTransactionCreate(BaseModel):
    transaction_type: TransactionType
    amount: float
    payment_method: PaymentMethod
    transaction_date: Optional[date] = None
    description: str
    category: Optional[str] = None
    patient_id: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_id: Optional[str] = None
    bank_account: Optional[str] = None
    reference_number: Optional[str] = None
    created_by: str

# Vendor Invoices (Bills from vendors)
class VendorInvoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    vendor_id: str
    invoice_date: date
    due_date: date
    amount: float
    tax_amount: float = 0.0
    total_amount: float
    
    # Invoice Details
    description: str
    expense_category: ExpenseCategory
    purchase_order_number: Optional[str] = None
    
    # Payment Status
    payment_status: str = "unpaid"  # unpaid, partial, paid
    amount_paid: float = 0.0
    payment_date: Optional[date] = None
    check_id: Optional[str] = None
    
    # Document Management
    invoice_file: Optional[str] = None  # base64 encoded
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VendorInvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: str
    invoice_date: date
    due_date: date
    amount: float
    tax_amount: float = 0.0
    description: str
    expense_category: ExpenseCategory
    purchase_order_number: Optional[str] = None
    invoice_file: Optional[str] = None
    created_by: str

# Daily Financial Summary
class DailyFinancialSummary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary_date: date = Field(default_factory=date.today)
    
    # Income Breakdown
    cash_income: float = 0.0
    credit_card_income: float = 0.0
    check_income: float = 0.0
    other_income: float = 0.0
    total_income: float = 0.0
    
    # Expense Breakdown
    cash_expenses: float = 0.0
    check_expenses: float = 0.0
    credit_card_expenses: float = 0.0
    other_expenses: float = 0.0
    total_expenses: float = 0.0
    
    # Net Summary
    net_amount: float = 0.0
    
    # Transaction Counts
    income_transaction_count: int = 0
    expense_transaction_count: int = 0
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# eRx (Electronic Prescribing) Models - FHIR R4 Compliant

class DrugClass(str, Enum):
    ANTIBIOTIC = "antibiotic"
    ANTIHYPERTENSIVE = "antihypertensive"
    ANTIDIABETIC = "antidiabetic"
    ANALGESIC = "analgesic"
    ANTICOAGULANT = "anticoagulant"
    ANTIDEPRESSANT = "antidepressant"
    BRONCHODILATOR = "bronchodilator"
    STEROID = "steroid"
    ANTIHISTAMINE = "antihistamine"
    OTHER = "other"

class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"

class DrugInteractionSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"

# FHIR-compliant Medication Resource
class FHIRMedication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # FHIR Medication Resource Fields
    resource_type: str = "Medication"
    identifier: List[Dict[str, Any]] = []  # NDC, RxNorm codes
    code: Dict[str, Any]  # CodeableConcept for medication coding
    status: str = "active"  # active | inactive | entered-in-error
    manufacturer: Optional[str] = None
    form: Optional[Dict[str, Any]] = None  # tablet, capsule, liquid, etc.
    
    # Clinical Information
    generic_name: str
    brand_names: List[str] = []
    strength: str  # e.g., "500mg", "10mg/5ml"
    dosage_forms: List[str] = []  # tablet, capsule, injection, etc.
    route_of_administration: List[str] = []  # oral, IV, IM, topical, etc.
    drug_class: DrugClass
    controlled_substance_schedule: Optional[str] = None  # I, II, III, IV, V
    
    # Safety Information
    contraindications: List[str] = []
    warnings: List[str] = []
    pregnancy_category: Optional[str] = None  # A, B, C, D, X
    
    # Prescribing Information
    standard_dosing: Dict[str, Any] = {}  # age/weight-based dosing
    max_daily_dose: Optional[str] = None
    duration_limits: Optional[str] = None
    
    # Reference Information
    rxnorm_code: Optional[str] = None
    ndc_codes: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# FHIR-compliant MedicationRequest Resource
class MedicationRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # FHIR MedicationRequest Resource Fields
    resource_type: str = "MedicationRequest"
    identifier: List[Dict[str, Any]] = []
    status: PrescriptionStatus
    intent: str = "order"  # proposal | plan | order | original-order
    category: List[Dict[str, Any]] = []  # inpatient | outpatient | community
    priority: str = "routine"  # routine | urgent | asap | stat
    
    # Medication Reference
    medication_id: str  # Reference to Medication resource
    medication_display: str  # Human-readable medication name
    
    # Patient Information
    patient_id: str  # Reference to Patient resource
    patient_display: str
    
    # Encounter Context
    encounter_id: Optional[str] = None
    
    # Prescriber Information (FHIR Practitioner)
    prescriber_id: str
    prescriber_name: str
    prescriber_npi: Optional[str] = None
    prescriber_dea: Optional[str] = None
    
    # Prescription Details
    authored_on: datetime = Field(default_factory=datetime.utcnow)
    dosage_instruction: List[Dict[str, Any]] = []  # FHIR Dosage datatype
    
    # Dispense Request
    dispense_request: Dict[str, Any] = {}
    substitution: Dict[str, Any] = {"allowed": True}
    
    # Clinical Information
    reason_code: List[Dict[str, Any]] = []  # ICD-10 codes
    reason_reference: List[str] = []  # Reference to conditions
    note: List[Dict[str, Any]] = []  # Additional instructions
    
    # Prescription Tracking
    prescription_number: str = Field(default_factory=lambda: f"RX{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}")
    days_supply: Optional[int] = None
    quantity: Optional[float] = None
    refills: int = 0
    
    # Safety Checks
    allergies_checked: bool = False
    interactions_checked: bool = False
    allergy_alerts: List[Dict[str, Any]] = []
    interaction_alerts: List[Dict[str, Any]] = []
    
    # Pharmacy Information
    pharmacy_id: Optional[str] = None
    pharmacy_name: Optional[str] = None
    
    # Audit Trail
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Electronic Signature
    electronically_signed: bool = False
    signature_timestamp: Optional[datetime] = None

class MedicationRequestCreate(BaseModel):
    medication_id: str
    patient_id: str
    prescriber_id: str
    prescriber_name: str
    encounter_id: Optional[str] = None
    
    # Dosage Information
    dosage_text: str  # Human-readable dosage instruction
    dose_quantity: float
    dose_unit: str
    frequency: str  # BID, TID, QID, etc.
    route: str  # oral, IV, IM, topical, etc.
    
    # Prescription Details
    quantity: float
    days_supply: int
    refills: int = 0
    generic_substitution_allowed: bool = True
    
    # Clinical Context
    indication: str  # Reason for prescription
    diagnosis_codes: List[str] = []  # ICD-10 codes
    special_instructions: Optional[str] = None
    
    # Pharmacy (optional)
    pharmacy_id: Optional[str] = None
    
    created_by: str

# Drug Interaction Model
class DrugInteraction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drug1_id: str
    drug1_name: str
    drug2_id: str
    drug2_name: str
    severity: DrugInteractionSeverity
    description: str
    clinical_consequence: str
    management_recommendation: str
    evidence_level: str  # established, probable, theoretical
    onset: str  # rapid, delayed
    documentation: str  # excellent, good, fair, poor
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Prescription Audit Log for HIPAA Compliance
class PrescriptionAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prescription_id: str
    patient_id: str
    action: str  # created, modified, viewed, cancelled, transmitted
    performed_by: str  # User ID
    performed_by_name: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Detailed Action Information
    action_details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # HIPAA Audit Requirements
    access_reason: Optional[str] = None
    changes_made: Dict[str, Any] = {}
    
    # System Information
    system_version: Optional[str] = None
    
class DrugAllergy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    medication_id: str
    medication_name: str
    allergen: str
    reaction_type: str  # allergy, intolerance, side_effect
    severity: str  # mild, moderate, severe, life_threatening
    reaction_description: str
    onset_date: Optional[date] = None
    documented_by: str
    documentation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # FHIR AllergyIntolerance fields
    clinical_status: str = "active"  # active, inactive, resolved
    verification_status: str = "confirmed"  # unconfirmed, confirmed, refuted
    category: str = "medication"  # food, medication, environment, biologic
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Scheduling System Models

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    PROCEDURE = "procedure"
    URGENT = "urgent"
    PHYSICAL_EXAM = "physical_exam"
    VACCINATION = "vaccination"
    LAB_WORK = "lab_work"
    TELEMEDICINE = "telemedicine"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

# Enhanced Appointment Business Rules
class AppointmentTypeConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "Annual Physical", "Consultation", etc.
    appointment_type: AppointmentType
    duration_minutes: int
    buffer_before_minutes: int = 0  # Time before appointment
    buffer_after_minutes: int = 0   # Time after appointment
    max_advance_booking_days: int = 90  # How far in advance can be booked
    min_advance_booking_hours: int = 2   # Minimum notice required
    requires_referral: bool = False
    allowed_patient_ages: Optional[Dict[str, int]] = None  # {"min": 18, "max": 65}
    provider_specialties_required: List[str] = []  # Required provider specialties
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Communication Templates and Services
class CommunicationService(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    VOICE = "voice"

class NotificationTrigger(str, Enum):
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_REMINDER_24H = "appointment_reminder_24h"
    APPOINTMENT_REMINDER_2H = "appointment_reminder_2h"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_COMPLETED = "appointment_completed"
    NO_SHOW_RECORDED = "no_show_recorded"

class AutomatedNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger: NotificationTrigger
    service: CommunicationService
    template_id: str
    delay_minutes: int = 0  # Delay after trigger (negative for before)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Provider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: Optional[str] = None  # Link to employee record
    first_name: str
    last_name: str
    title: str  # Dr., PA, NP, etc.
    specialties: List[str] = []
    license_number: Optional[str] = None
    npi_number: Optional[str] = None
    email: str
    phone: str
    is_active: bool = True
    
    # Schedule Settings
    default_appointment_duration: int = 30  # minutes
    schedule_start_time: str = "08:00"  # 24h format
    schedule_end_time: str = "17:00"
    working_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TimeSlot(BaseModel):
    start_time: str  # HH:MM format
    end_time: str
    is_available: bool = True
    appointment_id: Optional[str] = None

class ProviderSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    date: date
    time_slots: List[TimeSlot] = []
    is_available: bool = True  # Provider working this day
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    appointment_number: str = Field(default_factory=lambda: f"APT{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}")
    
    # Core Information
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    
    # Scheduling Details
    appointment_date: date
    start_time: str  # HH:MM
    end_time: str
    duration_minutes: int = 30
    
    # Appointment Details
    appointment_type: AppointmentType
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reason: str
    notes: Optional[str] = None
    
    # Location
    location: str = "Main Office"
    room: Optional[str] = None
    
    # Tracking
    scheduled_by: str  # User who created the appointment
    confirmed_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Related Records
    encounter_id: Optional[str] = None  # Link to encounter when appointment becomes visit
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced Scheduling Models for Advanced Features
class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# Telehealth System Models
class TelehealthSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_ISSUES = "technical_issues"

class TelehealthSessionType(str, Enum):
    VIDEO_CONSULTATION = "video_consultation"
    AUDIO_ONLY = "audio_only"
    FOLLOW_UP = "follow_up"
    THERAPY_SESSION = "therapy_session"
    GROUP_SESSION = "group_session"
    EMERGENCY_CONSULT = "emergency_consult"

class TelehealthParticipant(BaseModel):
    user_id: str
    user_name: str
    user_type: str  # "patient", "provider", "observer"
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    connection_quality: Optional[str] = None  # "excellent", "good", "fair", "poor"
    is_video_enabled: bool = True
    is_audio_enabled: bool = True
    is_screen_sharing: bool = False

class TelehealthTechnicalSpecs(BaseModel):
    video_quality: str = "HD"  # "HD", "SD", "Low"
    audio_quality: str = "High"  # "High", "Medium", "Low"
    bandwidth_usage: Optional[float] = None  # Mbps
    connection_type: Optional[str] = None  # "wifi", "cellular", "ethernet"
    device_type: Optional[str] = None  # "desktop", "mobile", "tablet"
    browser_info: Optional[str] = None

class TelehealthChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sender_id: str
    sender_name: str
    sender_type: str  # "patient", "provider", "system"
    message: str
    message_type: str = "text"  # "text", "file", "system", "prescription"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_private: bool = False  # For provider-only messages
    file_url: Optional[str] = None

class TelehealthSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_number: str = Field(default_factory=lambda: f"TEL-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
    
    # Core Session Information
    appointment_id: Optional[str] = None  # Link to scheduled appointment
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    
    # Session Details
    session_type: TelehealthSessionType
    status: TelehealthSessionStatus = TelehealthSessionStatus.SCHEDULED
    title: str
    description: Optional[str] = None
    
    # Scheduling
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration_minutes: int = 30
    
    # Technical Configuration
    session_url: Optional[str] = None  # Meeting room URL
    room_id: Optional[str] = None  # Video conferencing room ID
    access_code: Optional[str] = None  # Optional meeting passcode
    recording_enabled: bool = False
    recording_url: Optional[str] = None
    
    # Participants
    participants: List[TelehealthParticipant] = []
    max_participants: int = 10
    
    # Session Data
    technical_specs: Optional[TelehealthTechnicalSpecs] = None
    chat_messages: List[TelehealthChatMessage] = []
    session_notes: Optional[str] = None
    provider_notes: Optional[str] = None
    
    # Quality and Feedback
    patient_rating: Optional[int] = None  # 1-5 stars
    provider_rating: Optional[int] = None
    technical_issues: List[str] = []
    
    # Billing and Documentation
    billable: bool = True
    billing_code: Optional[str] = None
    encounter_id: Optional[str] = None  # Link to created encounter
    soap_note_id: Optional[str] = None  # Link to SOAP note
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TelehealthSessionCreate(BaseModel):
    patient_id: str
    provider_id: str
    session_type: TelehealthSessionType
    title: str
    description: Optional[str] = None
    scheduled_start: datetime
    duration_minutes: int = 30
    appointment_id: Optional[str] = None
    recording_enabled: bool = False
    access_code: Optional[str] = None

class TelehealthSessionUpdate(BaseModel):
    status: Optional[TelehealthSessionStatus] = None
    session_notes: Optional[str] = None
    provider_notes: Optional[str] = None
    patient_rating: Optional[int] = None
    provider_rating: Optional[int] = None
    technical_issues: Optional[List[str]] = None

class TelehealthWaitingRoom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    patient_id: str
    patient_name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    pre_session_form_completed: bool = False
    technical_check_completed: bool = False
    ready_to_join: bool = False
    estimated_wait_time: Optional[int] = None  # minutes
    provider_notified: bool = False

# Patient Portal System Models
class PatientPortalUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str  # Link to main patient record
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientPortalSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    session_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PatientMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: Optional[str] = None
    subject: str
    message: str
    message_type: str = "general"  # general, appointment, prescription, billing, urgent
    priority: str = "normal"  # low, normal, high, urgent
    status: str = "unread"  # unread, read, replied, closed
    is_patient_sender: bool = True
    sender_type: str = "patient"  # patient, provider, system
    reply_to_message_id: Optional[str] = None
    attachments: List[str] = []
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientAppointmentRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: Optional[str] = None
    appointment_type: str
    preferred_date: date
    preferred_time: Optional[str] = None
    alternate_dates: List[date] = []
    reason: str
    urgency: str = "routine"  # routine, urgent, emergency
    status: str = "pending"  # pending, approved, denied, scheduled
    notes: Optional[str] = None
    staff_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    appointment_id: Optional[str] = None  # Link to created appointment
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PrescriptionRefillRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    original_prescription_id: Optional[str] = None
    medication_name: str
    dosage: str
    quantity_requested: int
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    reason: Optional[str] = None
    urgency: str = "routine"  # routine, urgent
    status: str = "pending"  # pending, approved, denied, filled
    provider_id: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    staff_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientPortalActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    activity_type: str  # login, appointment_request, message_sent, bill_viewed, document_downloaded
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PatientPortalPreferences(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    email_notifications: bool = True
    sms_notifications: bool = False
    appointment_reminders: bool = True
    lab_result_notifications: bool = True
    prescription_reminders: bool = True
    marketing_communications: bool = False
    preferred_communication_method: str = "email"  # email, sms, phone, portal
    language_preference: str = "en"
    timezone: str = "America/Chicago"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    document_type: str  # lab_result, imaging, form, consent, discharge_summary
    title: str
    description: Optional[str] = None
    file_url: str
    file_size: Optional[int] = None
    file_type: str  # pdf, jpg, png, doc
    is_patient_accessible: bool = True
    requires_acknowledgment: bool = False
    acknowledged_at: Optional[datetime] = None
    uploaded_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Lab Orders and Insurance Verification System Models

# Lab Orders Models
class LabOrderStatus(str, Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    COLLECTED = "collected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESULTED = "resulted"

class LabOrderPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    ASAP = "asap"

class LabProvider(str, Enum):
    LABCORP = "labcorp"
    QUEST = "quest"
    INTERNAL = "internal"
    OTHER = "other"

class LabTest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_code: str  # LOINC code
    test_name: str
    description: Optional[str] = None
    category: str  # chemistry, hematology, microbiology, etc.
    specimen_type: str  # blood, urine, saliva, etc.
    collection_method: str  # venipuncture, fingerstick, etc.
    fasting_required: bool = False
    special_instructions: Optional[str] = None
    turnaround_time_hours: int = 24
    reference_ranges: Dict[str, Any] = {}
    lab_provider: LabProvider = LabProvider.INTERNAL
    cost: Optional[float] = None
    cpt_code: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LabOrderItem(BaseModel):
    test_id: str
    test_code: str
    test_name: str
    quantity: int = 1
    specimen_type: str
    collection_instructions: Optional[str] = None
    fasting_required: bool = False
    priority: LabOrderPriority = LabOrderPriority.ROUTINE

class LabOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"LAB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
    
    # Patient and Provider Information
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    encounter_id: Optional[str] = None
    
    # Order Details
    tests: List[LabOrderItem]
    priority: LabOrderPriority = LabOrderPriority.ROUTINE
    clinical_info: Optional[str] = None  # ICD-10 codes, clinical notes
    diagnosis_codes: List[str] = []
    
    # Lab Processing
    lab_provider: LabProvider = LabProvider.INTERNAL
    external_order_id: Optional[str] = None  # External lab's order ID
    specimen_collection_date: Optional[datetime] = None
    specimen_collected_by: Optional[str] = None
    
    # Status and Tracking
    status: LabOrderStatus = LabOrderStatus.DRAFT
    ordered_date: Optional[datetime] = None
    expected_completion: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    
    # Results
    results_available: bool = False
    results_reviewed: bool = False
    results_communicated: bool = False
    critical_values: bool = False
    
    # Billing and Insurance
    insurance_pre_auth: bool = False
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    
    # Integration Data
    hl7_message_id: Optional[str] = None
    external_system_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    ordered_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lab_order_id: str
    test_id: str
    test_code: str  # LOINC code
    test_name: str
    
    # Result Data
    result_value: Optional[str] = None
    result_numeric: Optional[float] = None
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None  # H, L, HH, LL, A, AA
    
    # Status and Quality
    result_status: str = "final"  # preliminary, final, corrected, cancelled
    performed_date: datetime
    reported_date: datetime
    critical_value: bool = False
    
    # Laboratory Information
    performing_lab: str
    lab_provider: LabProvider
    technician: Optional[str] = None
    pathologist: Optional[str] = None
    
    # Integration Data
    hl7_segment_data: Optional[Dict[str, Any]] = None
    external_result_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Insurance Verification Models
class InsuranceType(str, Enum):
    COMMERCIAL = "commercial"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    WORKERS_COMP = "workers_comp"
    AUTO_INSURANCE = "auto_insurance"
    SELF_PAY = "self_pay"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DENIED = "denied"
    EXPIRED = "expired"
    REQUIRES_AUTH = "requires_auth"
    ERROR = "error"

class InsurancePlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insurance_company: str
    plan_name: str
    plan_type: InsuranceType
    payer_id: str  # For electronic transactions
    
    # Contact Information
    phone_number: str
    website: Optional[str] = None
    claims_address: Optional[str] = None
    
    # Network and Coverage
    network_type: str = "PPO"  # PPO, HMO, EPO, POS
    requires_referrals: bool = False
    requires_prior_auth: bool = False
    
    # Service Integration
    eligibility_service_url: Optional[str] = None
    claims_service_url: Optional[str] = None
    api_credentials: Optional[Dict[str, str]] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InsurancePolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    insurance_plan_id: str
    
    # Policy Details
    policy_number: str
    group_number: Optional[str] = None
    subscriber_id: str
    subscriber_name: str
    relationship_to_subscriber: str = "self"  # self, spouse, child, other
    
    # Coverage Dates
    effective_date: date
    termination_date: Optional[date] = None
    
    # Coverage Details
    is_primary: bool = True
    copay_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    deductible_met: Optional[float] = None
    out_of_pocket_max: Optional[float] = None
    out_of_pocket_met: Optional[float] = None
    
    # Verification Status
    last_verified: Optional[datetime] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_notes: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EligibilityVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    insurance_policy_id: str
    provider_id: str
    
    # Verification Request
    service_type: str = "medical_care"  # medical_care, pharmacy, mental_health, etc.
    service_codes: List[str] = []  # CPT codes being verified
    verification_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Verification Response
    status: VerificationStatus = VerificationStatus.PENDING
    is_covered: Optional[bool] = None
    coverage_percentage: Optional[float] = None
    copay_amount: Optional[float] = None
    deductible_remaining: Optional[float] = None
    
    # Prior Authorization
    requires_prior_auth: bool = False
    prior_auth_number: Optional[str] = None
    prior_auth_expiry: Optional[date] = None
    
    # Service Limits
    annual_limit: Optional[float] = None
    visits_remaining: Optional[int] = None
    benefit_period: Optional[str] = None
    
    # External System Data
    external_transaction_id: Optional[str] = None
    raw_response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Processing Info
    verified_by: str
    verification_method: str = "api"  # api, phone, manual, portal
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PriorAuthorization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    authorization_number: str = Field(default_factory=lambda: f"PA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
    
    # Patient and Provider
    patient_id: str
    provider_id: str
    insurance_policy_id: str
    
    # Authorization Details
    service_type: str
    procedure_codes: List[str]  # CPT codes
    diagnosis_codes: List[str]  # ICD-10 codes
    
    # Request Information
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    requested_by: str
    clinical_justification: str
    supporting_documentation: List[str] = []
    
    # Authorization Response
    status: str = "pending"  # pending, approved, denied, expired
    approved_date: Optional[datetime] = None
    expiry_date: Optional[date] = None
    approved_units: Optional[int] = None
    used_units: int = 0
    
    # External System
    external_auth_id: Optional[str] = None
    payer_reference: Optional[str] = None
    denial_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# External Service Integration Models
class ExternalServiceConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str  # "labcorp_api", "quest_api", "availity_eligibility"
    service_type: str  # "lab_orders", "insurance_verification"
    
    # Connection Details
    base_url: str
    api_version: str = "v1"
    authentication_type: str = "api_key"  # api_key, oauth2, basic_auth
    
    # Credentials (encrypted in production)
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Configuration
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rate_limit_per_minute: int = 60
    
    # Status
    is_active: bool = True
    last_tested: Optional[datetime] = None
    test_result: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Service Request/Response Models
class LabOrderRequest(BaseModel):
    lab_order_id: str
    external_lab_provider: LabProvider
    priority: LabOrderPriority = LabOrderPriority.ROUTINE

class InsuranceVerificationRequest(BaseModel):
    patient_id: str
    insurance_policy_id: str
    service_codes: List[str]
    provider_npi: Optional[str] = None

# Patient Portal Authentication Models
class PatientPortalLogin(BaseModel):
    username: str
    password: str

class PatientPortalRegister(BaseModel):
    patient_id: str
    username: str
    email: str
    password: str
    confirm_password: str
    date_of_birth: date  # For verification
    last_four_ssn: Optional[str] = None  # Additional verification

class PatientPortalPasswordReset(BaseModel):
    email: str

class PatientPortalPasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
class WebRTCSignal(BaseModel):
    session_id: str
    from_user_id: str
    to_user_id: str
    signal_type: str  # "offer", "answer", "ice-candidate", "join", "leave"
    signal_data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AppointmentRecurrence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_appointment_id: str
    recurrence_type: RecurrenceType
    recurrence_interval: int = 1  # Every X days/weeks/months
    recurrence_end_date: Optional[date] = None
    max_occurrences: Optional[int] = None
    days_of_week: Optional[List[int]] = None  # For weekly: [0,2,4] = Mon,Wed,Fri
    day_of_month: Optional[int] = None  # For monthly: 15 = 15th of month
    created_instances: List[str] = []  # List of created appointment IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WaitingListEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    provider_id: str
    provider_name: str
    preferred_date: date
    preferred_time_start: Optional[str] = None  # HH:MM
    preferred_time_end: Optional[str] = None    # HH:MM
    appointment_type: AppointmentType
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=urgent
    duration_minutes: int = 30
    reason: str
    notes: Optional[str] = None
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AppointmentConflict(BaseModel):
    conflicting_appointment_id: str
    conflict_type: str  # "overlap", "double_booking", "provider_unavailable"
    conflict_message: str

class CalendarView(BaseModel):
    view_type: str  # "day", "week", "month"
    start_date: date
    end_date: date
    appointments: List[Appointment]
    providers: List[Provider]
    available_slots: List[TimeSlot]

# Patient Communications Models

class MessageType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    GENERAL = "general"
    FOLLOW_UP = "follow_up"
    TEST_RESULTS = "test_results"
    BILLING = "billing"
    PRESCRIPTION = "prescription"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class PatientMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Message Details
    message_type: MessageType
    subject: str
    content: str
    
    # Participants
    patient_id: str
    patient_name: str
    sender_id: str  # User/Provider ID
    sender_name: str
    sender_type: str = "clinic"  # clinic, patient
    
    # Delivery
    status: MessageStatus = MessageStatus.SENT
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    
    # Context
    appointment_id: Optional[str] = None
    encounter_id: Optional[str] = None
    
    # Threading
    reply_to: Optional[str] = None  # Parent message ID for replies
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class CommunicationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    message_type: MessageType
    subject_template: str
    content_template: str
    is_active: bool = True
    
    # Template variables: {patient_name}, {appointment_date}, {provider_name}, etc.
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# User and Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    
    # Security
    password_hash: str
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Profile
    profile_picture: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None  # Link to employee record
    
    # Permissions - role-based access control
    permissions: List[str] = []
    
    # Synology Integration
    auth_source: str = "local"  # "local" or "synology"
    synology_sid: Optional[str] = None  # Synology session ID
    synology_last_verified: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    employee_id: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None

# Role Permissions Configuration
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "patients:read", "patients:write", "patients:delete",
        "ehr:read", "ehr:write", "ehr:delete",
        "forms:read", "forms:write", "forms:delete",
        "inventory:read", "inventory:write", "inventory:delete",
        "invoices:read", "invoices:write", "invoices:delete",
        "employees:read", "employees:write", "employees:delete",
        "finance:read", "finance:write", "finance:delete",
        "users:read", "users:write", "users:delete",
        "reports:read", "settings:read", "settings:write"
    ],
    UserRole.DOCTOR: [
        "patients:read", "patients:write",
        "ehr:read", "ehr:write",
        "forms:read", "forms:write",
        "inventory:read",
        "invoices:read", "invoices:write",
        "finance:read",
        "reports:read"
    ],
    UserRole.NURSE: [
        "patients:read", "patients:write",
        "ehr:read", "ehr:write",
        "forms:read", "forms:write",
        "inventory:read", "inventory:write",
        "invoices:read",
        "finance:read",
        "reports:read"
    ],
    UserRole.RECEPTIONIST: [
        "patients:read", "patients:write",
        "ehr:read",
        "forms:read",
        "invoices:read", "invoices:write",
        "finance:read"
    ],
    UserRole.MANAGER: [
        "patients:read",
        "ehr:read",
        "inventory:read", "inventory:write",
        "invoices:read", "invoices:write",
        "employees:read", "employees:write",
        "finance:read", "finance:write",
        "reports:read"
    ],
    UserRole.TECHNICIAN: [
        "patients:read",
        "ehr:read", "ehr:write",
        "forms:read",
        "inventory:read", "inventory:write"
    ]
}

# Patient Authentication Models
class PatientUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str  # Link to existing patient record
    email: str
    phone: Optional[str] = None
    password_hash: str
    is_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientLogin(BaseModel):
    email: str
    password: str

class PatientRegister(BaseModel):
    patient_id: str
    email: str
    phone: Optional[str] = None
    password: str

class PatientToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    patient: Dict[str, Any]

# Mock Communication Services
class MockSMSService:
    """Mock SMS service for testing - replace with Twilio integration"""
    
    @staticmethod
    async def send_sms(to_phone: str, message: str) -> Dict[str, Any]:
        print(f"📱 MOCK SMS to {to_phone}: {message}")
        return {
            "status": "sent",
            "message_id": str(uuid.uuid4()),
            "service": "mock_sms",
            "to": to_phone,
            "cost": 0.0075  # Mock cost
        }

class MockEmailService:
    """Mock Email service for testing - replace with SendGrid integration"""
    
    @staticmethod
    async def send_email(to_email: str, subject: str, content: str) -> Dict[str, Any]:
        print(f"📧 MOCK EMAIL to {to_email}")
        print(f"Subject: {subject}")
        print(f"Content: {content[:100]}...")
        return {
            "status": "sent", 
            "message_id": str(uuid.uuid4()),
            "service": "mock_email",
            "to": to_email
        }

# Enhanced EHR Models

# Lab Integration Models - Using comprehensive definitions from above
# Duplicate LabOrderStatus and LabOrder classes removed to prevent conflicts

class LabResultStatus(str, Enum):
    PENDING = "pending"
    FINAL = "final"
    CORRECTED = "corrected"
    CRITICAL = "critical"
    ABNORMAL = "abnormal"

class ICD10Code(BaseModel):
    code: str
    description: str
    category: str

class LabTest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # LOINC code
    name: str
    description: str
    specimen_type: str  # blood, urine, etc.
    reference_ranges: Dict[str, Any]  # Normal ranges by age/gender
    critical_values: Dict[str, Any]  # Critical high/low values
    turnaround_time_hours: int
    cost: float
    is_active: bool = True

class LabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lab_order_id: str
    patient_id: str
    test_code: str  # LOINC code
    test_name: str
    value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: LabResultStatus
    is_critical: bool = False
    is_abnormal: bool = False
    result_date: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None

# Insurance Models

# Task 4 additions: V2 models for cards, eligibility, prior auth (lightweight)
class InsuranceCardV2Create(BaseModel):
    patient_id: str
    payer_name: str
    member_id: str
    group_number: Optional[str] = None
    plan_name: Optional[str] = None
    effective_date: Optional[str] = None  # YYYY-MM-DD
    valid_until: Optional[str] = None     # optional metadata only; not used by eligibility req

class InsuranceCardV2Update(BaseModel):
    payer_name: Optional[str] = None
    member_id: Optional[str] = None
    group_number: Optional[str] = None
    plan_name: Optional[str] = None
    effective_date: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None

class EligibilityCheckRequest(BaseModel):
    patient_id: str
    card_id: str
    service_date: str  # YYYY-MM-DD
    cpt_codes: Optional[List[str]] = []
    place_of_service: Optional[str] = None

class EligibilityCheckResponse(BaseModel):
    eligible: bool
    coverage: Dict[str, Any] = {}
    valid_until: str
    raw: Optional[Dict[str, Any]] = None

class PriorAuthRequestCreate(BaseModel):
    patient_id: str
    card_id: str
    cpt_codes: List[str]
    icd10_codes: List[str]
    notes: Optional[str] = None

class PriorAuthRequestUpdate(BaseModel):
    status: str  # PENDING|APPROVED|DENIED|EXPIRED
    approval_code: Optional[str] = None
    reason: Optional[str] = None

class InsuranceType(str, Enum):
    COMMERCIAL = "commercial"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    SELF_PAY = "self_pay"
    WORKERS_COMP = "workers_comp"

class EligibilityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    PENDING = "pending"

class InsuranceCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    insurance_type: InsuranceType
    payer_name: str
    payer_id: str
    member_id: str
    group_number: Optional[str] = None
    policy_number: Optional[str] = None
    subscriber_name: str
    subscriber_dob: str
    relationship_to_subscriber: str = "self"
    effective_date: str
    termination_date: Optional[str] = None
    copay_primary: Optional[float] = None
    copay_specialist: Optional[float] = None
    deductible: Optional[float] = None
    deductible_met: Optional[float] = None
    out_of_pocket_max: Optional[float] = None
    out_of_pocket_met: Optional[float] = None
    is_primary: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EligibilityResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    insurance_card_id: str
    eligibility_status: EligibilityStatus
    benefits_summary: Dict[str, Any]
    copay_amounts: Dict[str, float]
    deductible_info: Dict[str, Any]
    coverage_details: Dict[str, Any]
    prior_auth_required: List[str]  # Services requiring prior auth
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime
    raw_response: Optional[Dict[str, Any]] = None

class PriorAuthorization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    insurance_card_id: str
    provider_id: str
    service_code: str  # CPT code
    service_description: str
    diagnosis_codes: List[str]  # ICD-10 codes
    status: str = "pending"  # pending, approved, denied, expired
    auth_number: Optional[str] = None
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    decision_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    notes: Optional[str] = None
    submitted_by: str

# Vital Signs Model
class VitalSigns(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    encounter_id: Optional[str] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    bmi: Optional[float] = None
    systolic_bp: Optional[int] = None  # mmHg
    diastolic_bp: Optional[int] = None  # mmHg
    heart_rate: Optional[int] = None  # bpm
    respiratory_rate: Optional[int] = None  # breaths per minute
    temperature: Optional[float] = None  # in Celsius
    oxygen_saturation: Optional[int] = None  # percentage
    pain_scale: Optional[int] = None  # 0-10 scale
    recorded_by: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

class VitalSignsCreate(BaseModel):
    patient_id: str
    encounter_id: Optional[str] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    bmi: Optional[float] = None
    systolic_bp: Optional[int] = None  # mmHg
    diastolic_bp: Optional[int] = None  # mmHg
    heart_rate: Optional[int] = None  # bpm
    respiratory_rate: Optional[int] = None  # breaths per minute
    temperature: Optional[float] = None  # in Celsius
    oxygen_saturation: Optional[int] = None  # percentage
    pain_scale: Optional[int] = None  # 0-10 scale

# Allergy Model
class Allergy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    allergen: str
    reaction: str
    severity: AllergySeverity
    onset_date: Optional[date] = None
    notes: Optional[str] = None
    verified: bool = False
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AllergyCreate(BaseModel):
    # patient_id handled explicitly to return 400 on missing/invalid
    patient_id: Optional[str] = None
    allergen: str = Field(..., alias="allergy_name")
    reaction: str
    severity: AllergySeverity
    onset_date: Optional[date] = None
    notes: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

# Medication Model
class Medication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    medication_name: str
    dosage: str
    frequency: str
    route: str  # oral, injection, topical, etc.
    start_date: date
    end_date: Optional[date] = None
    prescribing_physician: str
    indication: str
    status: MedicationStatus = MedicationStatus.ACTIVE
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MedicationCreate(BaseModel):
    patient_id: str
    medication_name: str
    dosage: str
    frequency: str
    route: str
    start_date: date
    end_date: Optional[date] = None
    prescribing_physician: str
    indication: str
    notes: Optional[str] = None

# Medical History Model
class MedicalHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    condition: str
    icd10_code: Optional[str] = None
    diagnosis_date: Optional[date] = None
    status: str  # active, resolved, chronic
    notes: Optional[str] = None
    diagnosed_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MedicalHistoryCreate(BaseModel):
    patient_id: str
    condition: str
    icd10_code: Optional[str] = None
    diagnosis_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
    diagnosed_by: str

# Encounter/Visit Model
class Encounter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    encounter_number: str
    patient_id: str
    encounter_type: EncounterType
    status: EncounterStatus = EncounterStatus.PLANNED
    scheduled_date: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    provider: str
    location: Optional[str] = None
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EncounterCreate(BaseModel):
    patient_id: str
    encounter_type: EncounterType
    scheduled_date: datetime
    provider: str
    location: Optional[str] = None
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None

# SOAP Notes Model
class SOAPNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    encounter_id: str
    patient_id: str
    subjective: str  # Patient's description of symptoms
    objective: str   # Physical examination findings
    assessment: str  # Diagnosis and clinical impressions
    plan: str       # Treatment plan and follow-up
    provider: str
    status: str = "draft"  # draft, completed, reviewed, signed
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SOAPNoteCreate(BaseModel):
    encounter_id: str
    patient_id: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    provider: str

# Diagnosis Model
class Diagnosis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    encounter_id: str
    patient_id: str
    diagnosis_code: str  # ICD-10 code
    diagnosis_description: str
    diagnosis_type: str  # primary, secondary, etc.
    status: str  # active, resolved, etc.
    onset_date: Optional[date] = None
    provider: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DiagnosisCreate(BaseModel):
    encounter_id: str
    patient_id: str
    diagnosis_code: str
    diagnosis_description: str
    diagnosis_type: str
    status: str
    onset_date: Optional[date] = None
    provider: str

# Procedure Model
class Procedure(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    encounter_id: str
    patient_id: str
    procedure_code: str  # CPT code
    procedure_description: str
    procedure_date: date
    provider: str
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProcedureCreate(BaseModel):
    encounter_id: str
    patient_id: str
    procedure_code: str
    procedure_description: str
    procedure_date: date
    provider: str
    location: Optional[str] = None
    notes: Optional[str] = None

# Enhanced Models for Document Upload and Advanced Features

# Patient Documents Model
class PatientDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    document_name: str
    document_type: str  # lab_result, imaging, insurance, consent_form, etc.
    file_data: str  # base64 encoded file data
    file_extension: str  # pdf, jpg, png, etc.
    file_size: int  # in bytes
    uploaded_by: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class PatientDocumentCreate(BaseModel):
    patient_id: str
    document_name: str
    document_type: str
    file_data: str  # base64 encoded
    file_extension: str
    file_size: int
    uploaded_by: str
    notes: Optional[str] = None

# Enhanced Invoice Item with Inventory Linking
class EnhancedInvoiceItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    total: float
    inventory_item_id: Optional[str] = None  # Link to inventory
    service_type: str = "service"  # service, product, lab, injectable

# Enhanced Invoice Model
class EnhancedInvoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    patient_id: str
    encounter_id: Optional[str] = None  # Link to encounter
    items: List[EnhancedInvoiceItem]
    subtotal: float
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issue_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    notes: Optional[str] = None
    auto_generated: bool = False  # True if generated from SOAP notes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EnhancedInvoiceCreate(BaseModel):
    patient_id: str
    encounter_id: Optional[str] = None
    items: List[EnhancedInvoiceItem]
    tax_rate: float = 0.0
    due_days: int = 30
    notes: Optional[str] = None
    auto_generated: bool = False

# Enhanced SOAP Note with Plan Items
class PlanItem(BaseModel):
    item_type: str  # lab, injectable, medication, procedure, follow_up
    description: str
    quantity: int = 1
    unit_price: float = 0.0
    approved_by_patient: bool = False
    inventory_item_id: Optional[str] = None

class EnhancedSOAPNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    encounter_id: str
    patient_id: str
    subjective: str  # Patient's description of symptoms
    objective: str   # Physical examination findings
    assessment: str  # Diagnosis and clinical impressions
    plan: str       # Treatment plan and follow-up (text)
    plan_items: List[PlanItem] = []  # Structured plan items for billing
    provider: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EnhancedSOAPNoteCreate(BaseModel):
    encounter_id: str
    patient_id: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    plan_items: List[PlanItem] = []
    provider: str

# Authentication Helper Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.permissions and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission}"
            )
        return current_user
    return permission_checker

# Synology DSM Authentication Integration
class SynologyAuthService:
    """Service for integrating with Synology DSM authentication"""
    
    def __init__(self):
        self.base_url = SYNOLOGY_DSM_URL
        self.verify_ssl = SYNOLOGY_VERIFY_SSL
        self.session_name = SYNOLOGY_SESSION_NAME
        
    async def authenticate_with_synology(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with Synology DSM API"""
        if not self.base_url:
            return None
            
        try:
            # Configure SSL context
            ssl_context = ssl.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Synology DSM API authentication endpoint
                auth_url = f"{self.base_url}/webapi/auth.cgi"
                auth_params = {
                    'api': 'SYNO.API.Auth',
                    'version': '2',
                    'method': 'login',
                    'account': username,
                    'passwd': password,
                    'session': self.session_name,
                    'format': 'sid'
                }
                
                async with session.get(auth_url, params=auth_params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('success'):
                            # Get user info from DSM
                            user_info = await self._get_synology_user_info(
                                session, result['data']['sid'], username
                            )
                            
                            return {
                                'sid': result['data']['sid'],
                                'username': username,
                                'synology_user': user_info
                            }
                        else:
                            logging.error(f"Synology auth failed: {result.get('error')}")
                            return None
                    else:
                        logging.error(f"Synology API error: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logging.error(f"Synology authentication error: {str(e)}")
            return None
    
    async def _get_synology_user_info(self, session: aiohttp.ClientSession, sid: str, username: str) -> Dict:
        """Get user information from Synology DSM"""
        try:
            # Try to get user info - this might vary depending on DSM version and available APIs
            user_info_url = f"{self.base_url}/webapi/entry.cgi"
            user_params = {
                'api': 'SYNO.Core.User',
                'version': '1',
                'method': 'get',
                '_sid': sid
            }
            
            async with session.get(user_info_url, params=user_params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        return result.get('data', {})
                        
        except Exception as e:
            logging.warning(f"Could not fetch Synology user info: {str(e)}")
            
        # Return basic info if detailed info fails
        return {
            'username': username,
            'display_name': username,
            'is_admin': False  # Default, would need additional API calls to determine
        }
    
    async def logout_synology(self, sid: str) -> bool:
        """Logout from Synology DSM session"""
        if not self.base_url or not sid:
            return True
            
        try:
            ssl_context = ssl.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                logout_url = f"{self.base_url}/webapi/auth.cgi"
                logout_params = {
                    'api': 'SYNO.API.Auth',
                    'version': '2',
                    'method': 'logout',
                    'session': self.session_name,
                    '_sid': sid
                }
                
                async with session.get(logout_url, params=logout_params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('success', False)
                        
        except Exception as e:
            logging.error(f"Synology logout error: {str(e)}")
            
        return False

# Initialize Synology auth service
synology_auth = SynologyAuthService()

async def get_or_create_synology_user(synology_data: Dict) -> User:
    """Get existing user or create new user from Synology authentication"""
    username = synology_data['username']
    synology_user_info = synology_data.get('synology_user', {})
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": username})
    
    if existing_user:
        # Update last login and sync any changed info
        await db.users.update_one(
            {"username": username},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "synology_sid": synology_data['sid'],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return User(**existing_user)
    else:
        # Create new user from Synology data
        new_user = User(
            username=username,
            email=synology_user_info.get('email', f"{username}@local"),
            first_name=synology_user_info.get('first_name', username),
            last_name=synology_user_info.get('last_name', 'User'),
            role=UserRole.DOCTOR if synology_user_info.get('is_admin') else UserRole.RECEPTIONIST,
            password_hash="",  # No password needed for Synology users
            phone=synology_user_info.get('phone'),
            permissions=ROLE_PERMISSIONS.get(
                UserRole.DOCTOR if synology_user_info.get('is_admin') else UserRole.RECEPTIONIST, 
                []
            ),
            last_login=datetime.utcnow(),
            synology_sid=synology_data['sid'],
            auth_source="synology"
        )
        
        user_dict = jsonable_encoder(new_user)
        await db.users.insert_one(user_dict)
        
        return new_user

async def authenticate_user(username: str, password: str):
    """Authenticate user with both local and Synology authentication support"""
    
    # First, try Synology authentication if enabled
    if SYNOLOGY_ENABLED:
        try:
            synology_data = await synology_auth.authenticate_with_synology(username, password)
            if synology_data:
                # Get or create user from Synology data
                user = await get_or_create_synology_user(synology_data)
                return user
        except Exception as e:
            logging.error(f"Synology authentication failed for {username}: {str(e)}")
            # Continue to local authentication as fallback
    
    # Fallback to local authentication
    user = await db.users.find_one({"username": username})
    if not user:
        return False
    
    # Handle legacy users that might not have first_name/last_name fields
    if "first_name" not in user:
        user["first_name"] = "User"
    if "last_name" not in user:
        user["last_name"] = "Unknown"
        
    user_obj = User(**user)
    
    # Skip password verification for Synology users
    if user_obj.auth_source == "synology":
        # Update last login for Synology users who fall back to local auth
        await db.users.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return user_obj
    
    # Verify password for local users
    if not verify_password(password, user_obj.password_hash):
        # Increment failed login attempts
        await db.users.update_one(
            {"username": username},
            {"$inc": {"failed_login_attempts": 1}}
        )
        # Lock account after 5 failed attempts
        if user_obj.failed_login_attempts >= 4:  # Will be 5 after increment
            lock_until = datetime.utcnow() + timedelta(minutes=30)
            await db.users.update_one(
                {"username": username},
                {"$set": {"locked_until": jsonable_encoder(lock_until)}}
            )
        return False
    
    # Check if account is locked
    if user_obj.locked_until and datetime.utcnow() < user_obj.locked_until:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to failed login attempts"
        )
    
    # Reset failed attempts on successful login
    await db.users.update_one(
        {"username": username},
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login": jsonable_encoder(datetime.utcnow())
        }}
    )
    
    return user_obj

# Patient Authentication Functions
async def get_current_patient(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate patient credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        patient_user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if patient_user_id is None or token_type != "patient":
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception
    
    patient_user = await db.patient_users.find_one({"id": patient_user_id}, {"_id": 0})
    if patient_user is None:
        raise credentials_exception
    
    return {
        "id": patient_user["id"],
        "patient_id": patient_user["patient_id"],
        "email": patient_user["email"]
    }

# Authentication Routes
@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "permissions": user.permissions,
            "auth_source": user.auth_source,
            "synology_enabled": SYNOLOGY_ENABLED,
            "profile_picture": user.profile_picture
        }
    }

@api_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    # In a production system, you might want to blacklist the token
    return {"message": "Successfully logged out"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@api_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user and cleanup Synology session if applicable"""
    try:
        # If user authenticated via Synology, cleanup the Synology session
        if current_user.auth_source == "synology" and current_user.synology_sid:
            await synology_auth.logout_synology(current_user.synology_sid)
            
            # Clear Synology session from database
            await db.users.update_one(
                {"id": current_user.id},
                {
                    "$set": {
                        "synology_sid": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        return {"message": "Logout successful", "auth_source": current_user.auth_source}
        
    except Exception as e:
        logging.error(f"Error during logout: {str(e)}")
        return {"message": "Logout completed with warnings"}

@api_router.post("/auth/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user)
):
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    new_password_hash = get_password_hash(new_password)
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"password_hash": new_password_hash, "updated_at": jsonable_encoder(datetime.utcnow())}}
    )
    
    return {"message": "Password changed successfully"}

@api_router.get("/auth/synology-status")
async def get_synology_status():
    """Get Synology integration status and configuration"""
    return {
        "synology_enabled": SYNOLOGY_ENABLED,
        "synology_url": SYNOLOGY_DSM_URL if SYNOLOGY_ENABLED else None,
        "session_name": SYNOLOGY_SESSION_NAME,
        "verify_ssl": SYNOLOGY_VERIFY_SSL
    }

@api_router.post("/auth/test-synology")
async def test_synology_connection(current_user: User = Depends(get_current_active_user)):
    """Test Synology DSM connection (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not SYNOLOGY_ENABLED:
        return {
            "success": False,
            "message": "Synology integration not configured",
            "config_required": ["SYNOLOGY_DSM_URL"]
        }
    
    try:
        # Test connection by trying to access the API info endpoint
        ssl_context = ssl.create_default_context()
        if not SYNOLOGY_VERIFY_SSL:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            test_url = f"{SYNOLOGY_DSM_URL}/webapi/query.cgi"
            test_params = {
                'api': 'SYNO.API.Info',
                'version': '1',
                'method': 'query',
                'query': 'SYNO.API.Auth'
            }
            
            async with session.get(test_url, params=test_params, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": "Synology DSM connection successful",
                        "dsm_info": result.get('data', {})
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Synology DSM returned HTTP {response.status}",
                        "url_tested": SYNOLOGY_DSM_URL
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "url_tested": SYNOLOGY_DSM_URL
        }

# User Management Routes (Admin only)
@api_router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("users:write"))
):
    try:
        # Check if username or email already exists
        existing_user = await db.users.find_one({
            "$or": [{"username": user_data.username}, {"email": user_data.email}]
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Get role permissions
        permissions = ROLE_PERMISSIONS.get(user_data.role, [])
        
        # Create user
        password_hash = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            phone=user_data.phone,
            employee_id=user_data.employee_id,
            password_hash=password_hash,
            permissions=permissions,
            created_by=current_user.id
        )
        
        user_dict = jsonable_encoder(user)
        await db.users.insert_one(user_dict)
        
        # Remove password hash from response
        user_dict.pop("password_hash", None)
        return User(**user_dict, password_hash="[REDACTED]")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_permission("users:read"))):
    users = await db.users.find({}).to_list(1000)
    # Remove password hashes from response
    for user in users:
        user.pop("password_hash", None)
    return [User(**user, password_hash="[REDACTED]") for user in users]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission("users:read"))
):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("password_hash", None)
    return User(**user, password_hash="[REDACTED]")

@api_router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("users:write"))
):
    try:
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        # Update role permissions if role changed
        if "role" in update_data:
            update_data["permissions"] = ROLE_PERMISSIONS.get(update_data["role"], [])
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": jsonable_encoder(update_data)}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission("users:delete"))
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Initialize Default Admin User
@api_router.post("/auth/init-admin")
async def initialize_admin():
    try:
        # Check if any admin users exist
        admin_exists = await db.users.find_one({"role": "admin"})
        if admin_exists:
            # Check if existing admin has required fields
            if "first_name" not in admin_exists or "last_name" not in admin_exists:
                # Delete old incomplete admin user and recreate
                await db.users.delete_many({"username": "admin"})
                print("Deleted incomplete admin user, recreating...")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin user already exists"
                )
        
        # Create default admin user with all required fields
        admin_user = User(
            username="admin",
            email="admin@clinichub.com",
            first_name="System",
            last_name="Administrator",
            role=UserRole.ADMIN,
            password_hash=get_password_hash("admin123"),  # Change this in production!
            permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
            status=UserStatus.ACTIVE
        )
        
        user_dict = jsonable_encoder(admin_user)
        await db.users.insert_one(user_dict)
        
        return {
            "message": "Default admin user created successfully",
            "username": "admin",
            "password": "admin123",
            "note": "Please change the default password after first login"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating admin: {str(e)}")

# Force reinitialize admin user (for fixing corrupted users)
@api_router.post("/auth/force-init-admin")
async def force_initialize_admin():
    try:
        # Delete any existing admin users
        await db.users.delete_many({"username": "admin"})
        
        # Create fresh admin user with all required fields
        admin_user = User(
            username="admin",
            email="admin@clinichub.com",
            first_name="System",
            last_name="Administrator",
            role=UserRole.ADMIN,
            password_hash=get_password_hash("admin123"),
            permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
            status=UserStatus.ACTIVE
        )
        
        user_dict = jsonable_encoder(admin_user)
        await db.users.insert_one(user_dict)
        
        return {
            "message": "Admin user forcibly recreated successfully",
            "username": "admin",
            "password": "admin123",
            "note": "Old admin user was deleted and recreated with proper fields"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin user: {str(e)}"
        )

# Patient Routes
@api_router.post("/patients", response_model=Patient)
@audit_phi_access("patient", "create")
async def create_patient(patient_data: PatientCreate, request: Request, current_user: User = Depends(get_current_active_user)):
    # Convert to FHIR-compliant format
    patient = Patient(
        name=[PatientName(
            family=patient_data.last_name,
            given=[patient_data.first_name]
        )],
        telecom=[
            PatientTelecom(system="email", value=patient_data.email) if patient_data.email else None,
            PatientTelecom(system="phone", value=patient_data.phone) if patient_data.phone else None
        ],
        gender=patient_data.gender,
        birth_date=patient_data.date_of_birth,
        address=[PatientAddress(
            line=[patient_data.address_line1] if patient_data.address_line1 else [],
            city=patient_data.city,
            state=patient_data.state,
            postal_code=patient_data.zip_code
        )] if patient_data.address_line1 else []
    )
    # Filter out None values from telecom
    patient.telecom = [t for t in patient.telecom if t is not None]
    
    # Use jsonable_encoder to handle date serialization
    patient_dict = jsonable_encoder(patient)
    await db.patients.insert_one(patient_dict)
    
    # INTEROP: Publish domain event with FHIR data for external systems
    try:
        fhir_patient = fhir_converter.patient_to_fhir(patient)
        await event_publisher.publish(
            event_type="patient.created",
            aggregate_type="patient",
            aggregate_id=patient.id,
            data={
                "fhir_resource": fhir_patient,
                "source_system": "clinichub",
                "created_by": current_user.username
            },
            metadata={
                "user_id": current_user.id if hasattr(current_user, 'id') else 'unknown',
                "user_name": current_user.username,
                "ip_address": request.client.host if hasattr(request, 'client') else None
            }
        )
    except Exception as e:
        # Log error but don't fail patient creation
        logging.error(f"Failed to publish patient.created event: {e}")
    
    return patient

@api_router.get("/patients", response_model=List[Patient])
@audit_phi_access("patient", "list")
async def get_patients(request: Request, current_user: User = Depends(get_current_active_user)):
    patients = await db.patients.find({"status": {"$ne": "deceased"}}).to_list(1000)
    return [Patient(**patient) for patient in patients]

@api_router.get("/patients/{patient_id}", response_model=Patient)
@audit_phi_access("patient", "read")
async def get_patient(patient_id: str, request: Request, current_user: User = Depends(get_current_active_user)):
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return Patient(**patient)

@api_router.put("/patients/{patient_id}", response_model=Patient)
@audit_phi_access("patient", "update")
async def update_patient(patient_id: str, patient_data: PatientCreate, request: Request, current_user: User = Depends(get_current_active_user)):
    """Update existing patient"""
    # Check if patient exists
    existing_patient = await db.patients.find_one({"id": patient_id})
    if not existing_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Convert PatientCreate to FHIR-compliant format (same as create_patient)
    updated_patient = Patient(
        id=patient_id,
        created_at=existing_patient["created_at"],  # Preserve original creation time
        updated_at=datetime.utcnow(),
        name=[PatientName(
            family=patient_data.last_name,
            given=[patient_data.first_name]
        )],
        telecom=[
            PatientTelecom(system="email", value=patient_data.email) if patient_data.email else None,
            PatientTelecom(system="phone", value=patient_data.phone) if patient_data.phone else None
        ],
        gender=patient_data.gender,
        birth_date=patient_data.date_of_birth,
        address=[PatientAddress(
            line=[patient_data.address_line1] if patient_data.address_line1 else [],
            city=patient_data.city,
            state=patient_data.state,
            postal_code=patient_data.zip_code
        )] if patient_data.address_line1 else []
    )
    # Filter out None values from telecom
    updated_patient.telecom = [t for t in updated_patient.telecom if t is not None]
    
    updated_patient_dict = jsonable_encoder(updated_patient)
    await db.patients.replace_one({"id": patient_id}, updated_patient_dict)
    return updated_patient

# Smart Form Routes
@api_router.post("/forms", response_model=SmartForm)
async def create_form(form: SmartForm, current_user: User = Depends(get_current_active_user)):
    form.created_by = current_user.username
    form_dict = jsonable_encoder(form)
    await db.forms.insert_one(form_dict)
    return form

@api_router.get("/forms", response_model=List[SmartForm])
async def get_forms(
    category: Optional[str] = None,
    is_template: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    query = {}
    if category:
        query["category"] = category
    if is_template is not None:
        query["is_template"] = is_template
    
    forms = await db.forms.find(query).to_list(1000)
    return [SmartForm(**form) for form in forms]

@api_router.get("/forms/{form_id}", response_model=SmartForm)
async def get_form(form_id: str, current_user: User = Depends(get_current_active_user)):
    form = await db.forms.find_one({"id": form_id}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return SmartForm(**form)

@api_router.put("/forms/{form_id}", response_model=SmartForm)
async def update_form(
    form_id: str, 
    form_update: SmartForm, 
    current_user: User = Depends(get_current_active_user)
):
    form_update.updated_at = datetime.utcnow()
    form_dict = jsonable_encoder(form_update)
    
    result = await db.forms.update_one(
        {"id": form_id},
        {"$set": form_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return form_update

@api_router.delete("/forms/{form_id}")
async def delete_form(form_id: str, current_user: User = Depends(get_current_active_user)):
    result = await db.forms.delete_one({"id": form_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    return {"message": "Form deleted successfully"}

@api_router.post("/forms/{form_id}/submit", response_model=FormSubmission)
async def submit_form(
    form_id: str, 
    submission_data: Dict[str, Any],
    patient_id: str,
    encounter_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    # Get form details
    form = await db.forms.find_one({"id": form_id}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Get patient details for smart tag processing
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Process smart tags in the data
    processed_data = await process_smart_tags(submission_data, patient, encounter_id)
    
    # Generate FHIR data if mapping exists
    fhir_data = None
    if form.get("fhir_mapping"):
        fhir_data = await generate_fhir_data(processed_data, form["fhir_mapping"], patient)
    
    # Create submission
    submission = FormSubmission(
        form_id=form_id,
        form_title=form["title"],
        patient_id=patient_id,
        patient_name=f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
        encounter_id=encounter_id,
        data=submission_data,
        processed_data=processed_data,
        fhir_data=fhir_data,
        submitted_by=current_user.username
    )
    
    submission_dict = jsonable_encoder(submission)
    await db.form_submissions.insert_one(submission_dict)
    
    # Link to patient record if encounter provided
    if encounter_id:
        await link_form_to_encounter(encounter_id, submission.id)
    
    return submission

@api_router.get("/forms/{form_id}/submissions", response_model=List[FormSubmission])
async def get_form_submissions(
    form_id: str,
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    query = {"form_id": form_id}
    if patient_id:
        query["patient_id"] = patient_id
    
    submissions = await db.form_submissions.find(query, {"_id": 0}).sort("submitted_at", -1).to_list(1000)
    return [FormSubmission(**submission) for submission in submissions]

@api_router.get("/patients/{patient_id}/form-submissions", response_model=List[FormSubmission])
async def get_patient_form_submissions(
    patient_id: str,
    current_user: User = Depends(get_current_active_user)
):
    submissions = await db.form_submissions.find({"patient_id": patient_id}, {"_id": 0}).sort("submitted_at", -1).to_list(1000)
    return [FormSubmission(**submission) for submission in submissions]

@api_router.get("/form-submissions/{submission_id}", response_model=FormSubmission)
async def get_form_submission(
    submission_id: str,
    current_user: User = Depends(get_current_active_user)
):
    submission = await db.form_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Form submission not found")
    return FormSubmission(**submission)

@api_router.post("/forms/templates/init")
async def initialize_form_templates(current_user: User = Depends(get_current_active_user)):
    """Initialize pre-built medical form templates"""
    try:
        # Check if templates already exist
        existing_templates = await db.forms.count_documents({"is_template": True})
        if existing_templates > 0:
            return {"message": "Form templates already initialized", "templates_count": existing_templates}
        
        templates = await create_medical_form_templates()
        
        # Insert templates
        await db.forms.insert_many(templates)
        
        return {
            "message": "Medical form templates initialized successfully",
            "templates_added": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing templates: {str(e)}")

@api_router.post("/forms/templates/init-compliant")
async def initialize_compliant_form_templates(current_user: User = Depends(get_current_active_user)):
    """Initialize HIPAA and Texas compliant medical form templates (replaces existing)"""
    try:
        # Clear existing templates
        await db.forms.delete_many({"is_template": True})
        
        templates = await create_medical_form_templates()
        
        # Insert new compliant templates
        await db.forms.insert_many(templates)
        
        return {
            "message": "HIPAA and Texas compliant form templates initialized successfully",
            "templates_added": len(templates),
            "compliance_info": "Forms are compliant with HIPAA Privacy Rule, Texas Medical Practice Act, and Texas Medical Board requirements"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing compliant templates: {str(e)}")

@api_router.post("/forms/from-template/{template_id}", response_model=SmartForm)
async def create_form_from_template(
    template_id: str,
    title: str,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new form from a template"""
    template = await db.forms.find_one({"id": template_id, "is_template": True}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create new form from template
    new_form = SmartForm(
        title=title,
        description=description or template.get("description"),
        fields=template["fields"],
        category=template.get("category", "custom"),
        fhir_mapping=template.get("fhir_mapping"),
        is_template=False,
        created_by=current_user.username
    )
    
    form_dict = jsonable_encoder(new_form)
    await db.forms.insert_one(form_dict)
    
    return new_form

# Helper Functions for Smart Forms

async def process_smart_tags(data: Dict[str, Any], patient: Dict[str, Any], encounter_id: Optional[str] = None) -> Dict[str, Any]:
    """Process smart tags in form submission data"""
    processed = data.copy()
    
    # Get encounter if provided
    encounter = None
    if encounter_id:
        encounter = await db.encounters.find_one({"id": encounter_id}, {"_id": 0})
    
    # Smart tag mappings
    smart_tag_values = {
        "{patient_name}": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
        "{patient_dob}": patient.get("birth_date", ""),
        "{patient_gender}": patient.get("gender", ""),
        "{patient_phone}": patient.get("telecom", [{}])[0].get("value", ""),
        "{patient_address}": f"{patient.get('address', [{}])[0].get('line', [''])[0]}, {patient.get('address', [{}])[0].get('city', '')}",
        "{current_date}": date.today().isoformat(),
        "{current_time}": datetime.now().strftime("%H:%M"),
        "{current_datetime}": datetime.now().isoformat(),
        "{provider_name}": encounter.get("provider", "Dr. Provider") if encounter else "Dr. Provider",
        "{clinic_name}": "ClinicHub Medical Center",
        "{encounter_date}": encounter.get("scheduled_date", "").split("T")[0] if encounter else "",
        "{chief_complaint}": encounter.get("chief_complaint", "") if encounter else ""
    }
    
    # Replace smart tags in all string values
    for key, value in processed.items():
        if isinstance(value, str):
            for tag, replacement in smart_tag_values.items():
                value = value.replace(tag, str(replacement))
            processed[key] = value
    
    return processed

async def generate_fhir_data(data: Dict[str, Any], fhir_mapping: Dict[str, str], patient: Dict[str, Any]) -> Dict[str, Any]:
    """Generate FHIR-compliant data from form submission"""
    fhir_data = {
        "resourceType": "QuestionnaireResponse",
        "id": str(uuid.uuid4()),
        "status": "completed",
        "subject": {
            "reference": f"Patient/{patient['id']}"
        },
        "authored": datetime.utcnow().isoformat(),
        "item": []
    }
    
    # Map form data to FHIR structure based on mapping
    for field_id, value in data.items():
        if field_id in fhir_mapping:
            fhir_path = fhir_mapping[field_id]
            fhir_data["item"].append({
                "linkId": field_id,
                "text": fhir_path,
                "answer": [{"valueString": str(value)}]
            })
    
    return fhir_data

async def link_form_to_encounter(encounter_id: str, submission_id: str):
    """Link form submission to patient encounter"""
    await db.encounters.update_one(
        {"id": encounter_id},
        {"$addToSet": {"form_submissions": submission_id}}
    )

async def create_medical_form_templates():
    """Create HIPAA and Texas compliant medical form templates"""
    templates = []
    
    # 1. HIPAA and Texas Compliant Patient Intake Form
    intake_fields = [
        FormField(
            type="text",
            label="Patient Legal Name (First, Middle, Last)",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Date of Birth",
            smart_tag="{patient_dob}",
            required=True,
            order=2
        ),
        FormField(
            type="select",
            label="Biological Sex Assigned at Birth",
            options=["Male", "Female", "Intersex"],
            required=True,
            order=3
        ),
        FormField(
            type="select",
            label="Gender Identity",
            options=["Male", "Female", "Non-binary", "Transgender Male", "Transgender Female", "Other", "Prefer not to answer"],
            order=4
        ),
        FormField(
            type="text",
            label="Social Security Number",
            placeholder="XXX-XX-XXXX",
            validation_rules={"pattern": "^\\d{3}-\\d{2}-\\d{4}$"},
            required=True,
            order=5
        ),
        FormField(
            type="text",
            label="Primary Phone Number",
            smart_tag="{patient_phone}",
            required=True,
            order=6
        ),
        FormField(
            type="text",
            label="Emergency Contact Name",
            required=True,
            order=7
        ),
        FormField(
            type="text",
            label="Emergency Contact Phone",
            required=True,
            order=8
        ),
        FormField(
            type="text",
            label="Emergency Contact Relationship",
            required=True,
            order=9
        ),
        FormField(
            type="textarea",
            label="Home Address",
            smart_tag="{patient_address}",
            placeholder="Street Address, City, State, ZIP Code",
            required=True,
            order=10
        ),
        FormField(
            type="text",
            label="Email Address",
            validation_rules={"pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"},
            order=11
        ),
        FormField(
            type="select",
            label="Preferred Language",
            options=["English", "Spanish", "Other"],
            required=True,
            order=12
        ),
        FormField(
            type="select",
            label="Race/Ethnicity (Optional - for statistical purposes only)",
            options=["White", "Black or African American", "Hispanic or Latino", "Asian", "Native American", "Pacific Islander", "Other", "Prefer not to answer"],
            order=13
        ),
        FormField(
            type="text",
            label="Primary Insurance Provider",
            order=14
        ),
        FormField(
            type="text",
            label="Insurance Policy Number",
            order=15
        ),
        FormField(
            type="text",
            label="Insurance Group Number",
            order=16
        ),
        FormField(
            type="text",
            label="Secondary Insurance (if applicable)",
            order=17
        ),
        FormField(
            type="textarea",
            label="Chief Complaint/Reason for Visit",
            placeholder="Describe your primary concern or reason for today's visit",
            required=True,
            order=18
        ),
        FormField(
            type="textarea",
            label="Current Medications (include dosage and frequency)",
            placeholder="List all prescription medications, over-the-counter drugs, vitamins, and supplements",
            order=19
        ),
        FormField(
            type="textarea",
            label="Known Allergies",
            placeholder="Include medications, foods, environmental factors, and reactions",
            order=20
        ),
        FormField(
            type="textarea",
            label="Past Medical History",
            placeholder="Previous surgeries, hospitalizations, chronic conditions, mental health history",
            order=21
        ),
        FormField(
            type="textarea",
            label="Family Medical History",
            placeholder="Significant family medical conditions (cancer, heart disease, diabetes, etc.)",
            order=22
        ),
        FormField(
            type="textarea",
            label="Social History",
            placeholder="Tobacco, alcohol, recreational drug use; occupation; living situation",
            order=23
        ),
        FormField(
            type="select",
            label="Have you been a victim of abuse or domestic violence?",
            options=["No", "Yes", "Prefer not to answer"],
            order=24
        ),
        FormField(
            type="checkbox",
            label="I acknowledge that the information I have provided is complete and accurate to the best of my knowledge",
            required=True,
            order=25
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "HIPAA & Texas Compliant Patient Intake Form",
        "description": "Comprehensive patient intake form compliant with HIPAA privacy rules and Texas medical practice requirements",
        "fields": [jsonable_encoder(field) for field in intake_fields],
        "category": "intake",
        "is_template": True,
        "template_name": "patient_intake_compliant",
        "status": "active",
        "compliance_notes": "HIPAA compliant, Texas Medical Practice Act compliant, includes required demographic data collection",
        "fhir_mapping": {
            "patient_name": "Patient.name",
            "dob": "Patient.birthDate",
            "gender": "Patient.gender",
            "phone": "Patient.telecom",
            "address": "Patient.address",
            "emergency_contact": "Patient.contact",
            "insurance": "Coverage.identifier"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # 2. Consent to Treat Form (Texas Compliant)
    consent_fields = [
        FormField(
            type="text",
            label="Patient Name",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Date",
            smart_tag="{current_date}",
            required=True,
            order=2
        ),
        FormField(
            type="textarea",
            label="Consent to Treatment Statement",
            placeholder="I understand and consent to the following treatment...",
            value="I voluntarily consent to medical treatment by the healthcare providers at this facility. I understand that:\n\n1. No guarantee has been made regarding the outcome of treatment or procedures.\n2. Medical practice is not an exact science, and results cannot be guaranteed.\n3. I have been informed of the risks, benefits, and alternatives to the proposed treatment.\n4. I have had the opportunity to ask questions, and all questions have been answered to my satisfaction.\n5. I understand that if I am a female patient, I should inform my healthcare provider if I am or might be pregnant.\n6. I consent to photography or video recording for medical documentation purposes only.\n7. I understand that medical students, residents, or other healthcare professionals may be involved in my care for educational purposes.\n8. I authorize the release of my medical information to insurance companies and other entities as necessary for treatment, payment, and healthcare operations.\n\nI have read and understand this consent form. I voluntarily give my consent to treatment.",
            required=True,
            order=3
        ),
        FormField(
            type="text",
            label="Specific Treatment or Procedure (if applicable)",
            placeholder="Enter specific treatment being consented to",
            order=4
        ),
        FormField(
            type="textarea",
            label="Risks Explained",
            placeholder="Specific risks discussed with patient",
            order=5
        ),
        FormField(
            type="textarea",
            label="Alternatives Discussed",
            placeholder="Alternative treatments discussed",
            order=6
        ),
        FormField(
            type="checkbox",
            label="I acknowledge that I have read and understand this consent form",
            required=True,
            order=7
        ),
        FormField(
            type="checkbox",
            label="I voluntarily consent to the proposed treatment",
            required=True,
            order=8
        ),
        FormField(
            type="signature",
            label="Patient Signature",
            required=True,
            order=9
        ),
        FormField(
            type="text",
            label="Witness Name (if required)",
            order=10
        ),
        FormField(
            type="signature",
            label="Witness Signature (if required)",
            order=11
        ),
        FormField(
            type="signature",
            label="Healthcare Provider Signature",
            required=True,
            order=12
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Informed Consent to Medical Treatment",
        "description": "Texas Medical Practice Act compliant informed consent form for medical treatment",
        "fields": [jsonable_encoder(field) for field in consent_fields],
        "category": "consent",
        "is_template": True,
        "template_name": "consent_to_treat",
        "status": "active",
        "compliance_notes": "Compliant with Texas Medical Practice Act, Texas Health and Safety Code Chapter 313, includes informed consent requirements",
        "legal_requirements": "Texas Medical Practice Act Section 164.012, Texas Health and Safety Code Chapter 313",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # 3. Telemedicine Consent Form (Texas Compliant)
    telemedicine_fields = [
        FormField(
            type="text",
            label="Patient Name",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Date",
            smart_tag="{current_date}",
            required=True,
            order=2
        ),
        FormField(
            type="text",
            label="Healthcare Provider Name",
            smart_tag="{provider_name}",
            required=True,
            order=3
        ),
        FormField(
            type="textarea",
            label="Telemedicine Consent Statement",
            value="TELEMEDICINE INFORMED CONSENT\n\nI understand that telemedicine involves the use of electronic communications to enable healthcare providers at different locations to share individual patient medical information for the purpose of improving patient care. The information may be used for diagnosis, therapy, follow-up and/or education.\n\nI understand that telemedicine may involve electronic communication of my personal medical information to other medical practitioners who may be located in other areas, including out of state.\n\nI understand that I have the following rights with respect to telemedicine:\n\n1. I have the right to withhold or withdraw my consent to the use of telemedicine in the course of my care at any time, without affecting my right to future care or treatment.\n\n2. The laws that protect the privacy and the confidentiality of medical information also apply to telemedicine, and information disclosed by me during the course of my telemedicine consultation will be kept confidential.\n\n3. I understand that there are risks and consequences from telemedicine, including, but not limited to, the possibility that:\n   a. Information transmitted may not be sufficient (e.g., poor resolution of images) to allow for appropriate medical decision making by the healthcare provider;\n   b. Delays in medical evaluation and treatment could occur due to deficiencies or failures of the equipment;\n   c. In rare instances, security protocols could fail, causing a breach of privacy of personal medical information;\n   d. In rare instances, a lack of access to complete medical records may result in adverse drug interactions or allergic reactions or other judgment errors;\n\n4. I understand that telemedicine may involve electronic communication of my personal medical information to other medical practitioners who may be located in other areas, including out of state.\n\n5. I understand that I may expect the anticipated benefits from the use of telemedicine in my care, but that no results can be guaranteed or assured.\n\n6. I understand that my healthcare information may be shared with other individuals for scheduling and billing purposes. Others may also be present during the telemedicine consultation other than my healthcare provider in order to operate the video equipment. The above-mentioned people will all maintain confidentiality of the information obtained. I further understand that I will be informed of their presence in the consultation and thus will have the right to request the following: (1) omit specific details of my medical history/examination that are personally sensitive to me; (2) ask non-medical personnel to leave the telemedicine examination room: and/or (3) terminate the consultation at any time.\n\n7. I understand that I have the right to access my medical information and copies of medical records in accordance with Texas law.\n\n8. I understand that if I am experiencing a medical emergency, I should call 911 immediately and that the providers cannot directly intervene in the case of a medical emergency that may occur during a telemedicine consultation.\n\nPATIENT CONSENT TO THE USE OF TELEMEDICINE\n\nI have read and understand the information provided above regarding telemedicine, have discussed it with my physician or such assistants as may be designated, and all of my questions have been answered to my satisfaction. I hereby give my informed consent for the use of telemedicine in my medical care.",
            required=True,
            order=4
        ),
        FormField(
            type="checkbox",
            label="I understand the risks and benefits of telemedicine as described above",
            required=True,
            order=5
        ),
        FormField(
            type="checkbox",
            label="I understand that I can withdraw consent for telemedicine at any time",
            required=True,
            order=6
        ),
        FormField(
            type="checkbox",
            label="I understand that no results can be guaranteed from telemedicine consultations",
            required=True,
            order=7
        ),
        FormField(
            type="checkbox",
            label="I understand the limitations of telemedicine technology",
            required=True,
            order=8
        ),
        FormField(
            type="checkbox",
            label="I consent to the use of telemedicine for my healthcare",
            required=True,
            order=9
        ),
        FormField(
            type="signature",
            label="Patient Signature",
            required=True,
            order=10
        ),
        FormField(
            type="signature",
            label="Healthcare Provider Signature",
            required=True,
            order=11
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Telemedicine Informed Consent",
        "description": "Texas compliant telemedicine consent form per Texas Medical Board requirements",
        "fields": [jsonable_encoder(field) for field in telemedicine_fields],
        "category": "telemedicine",
        "is_template": True,
        "template_name": "telemedicine_consent",
        "status": "active",
        "compliance_notes": "Compliant with Texas Medical Board Rule 174.6 - Telemedicine Medical Services",
        "legal_requirements": "Texas Medical Board Rule 174.6, Texas Occupations Code Chapter 111",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # 4. HIPAA Privacy Notice and Disclosure Agreement
    hipaa_fields = [
        FormField(
            type="text",
            label="Patient Name",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Date",
            smart_tag="{current_date}",
            required=True,
            order=2
        ),
        FormField(
            type="textarea",
            label="HIPAA Privacy Notice",
            value="NOTICE OF PRIVACY PRACTICES\n\nThis notice describes how medical information about you may be used and disclosed and how you can get access to this information. Please review it carefully.\n\nOUR COMMITMENT TO YOUR PRIVACY\n\nOur practice is dedicated to maintaining the privacy of your protected health information (PHI). We are required by law to maintain the confidentiality of PHI and to provide you with notice of our legal duties and privacy practices with respect to PHI.\n\nHOW WE MAY USE AND DISCLOSE YOUR HEALTH INFORMATION\n\nFor Treatment: We may use and disclose your PHI to provide, coordinate, or manage your health care and related services. This may include communicating with other health care providers regarding your treatment and coordinating and managing your health care with others.\n\nFor Payment: We may use and disclose your PHI to obtain payment for the health care services provided to you and to determine your eligibility or coverage for insurance or other payment purposes.\n\nFor Health Care Operations: We may use and disclose your PHI to operate our practice. These uses and disclosures are necessary to make sure that all of our patients receive quality care and for certain administrative and business functions.\n\nOther Uses and Disclosures:\n- Public Health Activities\n- Health Oversight Activities  \n- Judicial and Administrative Proceedings\n- Law Enforcement Purposes\n- Coroners, Funeral Directors, Organ Donation\n- Research\n- Serious Threats to Health or Safety\n- Military and National Security\n- Workers' Compensation\n\nYOUR RIGHTS REGARDING YOUR PHI\n\nYou have the right to:\n1. Request restrictions on uses and disclosures of your PHI\n2. Request confidential communications\n3. Inspect and copy your PHI\n4. Amend your PHI\n5. Receive an accounting of disclosures\n6. Obtain a paper copy of this notice\n7. File a complaint\n\nCOMPLAINTS\n\nIf you believe your privacy rights have been violated, you may file a complaint with our Privacy Officer or with the Secretary of Health and Human Services. You will not be retaliated against for filing a complaint.\n\nCONTACT INFORMATION\n\nFor more information about our privacy practices or to file a complaint, contact our Privacy Officer at [Phone Number].\n\nEFFECTIVE DATE\n\nThis notice is effective as of [Date] and will remain in effect until replaced or amended.",
            required=True,
            order=3
        ),
        FormField(
            type="checkbox",
            label="I acknowledge that I have received a copy of the Notice of Privacy Practices",
            required=True,
            order=4
        ),
        FormField(
            type="checkbox",
            label="I understand my rights under HIPAA regarding my protected health information",
            required=True,
            order=5
        ),
        FormField(
            type="checkbox",
            label="I understand how my health information may be used and disclosed",
            required=True,
            order=6
        ),
        FormField(
            type="select",
            label="May we leave detailed messages on your voicemail?",
            options=["Yes", "No"],
            required=True,
            order=7
        ),
        FormField(
            type="select",
            label="May we send you appointment reminders via text message?",
            options=["Yes", "No"],
            required=True,
            order=8
        ),
        FormField(
            type="select",
            label="May we send you appointment reminders via email?",
            options=["Yes", "No"],
            required=True,
            order=9
        ),
        FormField(
            type="text",
            label="Authorized persons who may receive your health information (family members, etc.)",
            placeholder="Name and relationship",
            order=10
        ),
        FormField(
            type="checkbox",
            label="I authorize the disclosure of my health information as described above",
            required=True,
            order=11
        ),
        FormField(
            type="signature",
            label="Patient Signature",
            required=True,
            order=12
        ),
        FormField(
            type="text",
            label="Legal Guardian/Representative Name (if applicable)",
            order=13
        ),
        FormField(
            type="signature",
            label="Legal Guardian/Representative Signature (if applicable)",
            order=14
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "HIPAA Privacy Notice and Authorization",
        "description": "HIPAA compliant privacy notice and authorization for use and disclosure of protected health information",
        "fields": [jsonable_encoder(field) for field in hipaa_fields],
        "category": "privacy",
        "is_template": True,
        "template_name": "hipaa_disclosure",
        "status": "active",
        "compliance_notes": "Fully compliant with HIPAA Privacy Rule 45 CFR Part 164, includes all required elements",
        "legal_requirements": "HIPAA Privacy Rule 45 CFR §164.520, 45 CFR §164.508",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    return templates
# Invoice Routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate):
    try:
        # Generate invoice number
        count = await db.invoices.count_documents({})
        invoice_number = f"INV-{count + 1:06d}"
        
        # Calculate totals
        subtotal = sum(item.total for item in invoice_data.items)
        tax_amount = subtotal * invoice_data.tax_rate
        total_amount = subtotal + tax_amount
        
        # Set due date - Fix the date calculation
        due_date = None
        if invoice_data.due_days:
            from datetime import timedelta
            due_date = date.today() + timedelta(days=invoice_data.due_days)
        
        invoice = Invoice(
            invoice_number=invoice_number,
            patient_id=invoice_data.patient_id,
            items=invoice_data.items,
            subtotal=subtotal,
            tax_rate=invoice_data.tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            due_date=due_date,
            notes=invoice_data.notes
        )
        
        invoice_dict = jsonable_encoder(invoice)
        await db.invoices.insert_one(invoice_dict)
        return invoice
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices():
    invoices = await db.invoices.find().to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return Invoice(**invoice)

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_data: InvoiceCreate, current_user: User = Depends(get_current_active_user)):
    """Update existing invoice"""
    # Check if invoice exists
    existing_invoice = await db.invoices.find_one({"id": invoice_id})
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Calculate totals
    subtotal = sum(item.quantity * item.unit_price for item in invoice_data.items)
    tax_amount = subtotal * invoice_data.tax_rate
    total_amount = subtotal + tax_amount
    
    # Set totals in items
    for item in invoice_data.items:
        item.total = item.quantity * item.unit_price
    
    # Create updated invoice
    # Get issue_date from existing invoice and handle conversion
    existing_issue_date = existing_invoice.get("issue_date")
    if isinstance(existing_issue_date, str):
        # Convert string to date object
        from datetime import datetime as dt
        existing_issue_date = dt.fromisoformat(existing_issue_date).date()
    elif isinstance(existing_issue_date, datetime):
        existing_issue_date = existing_issue_date.date()
    elif existing_issue_date is None:
        existing_issue_date = date.today()
    
    updated_invoice = Invoice(
        id=invoice_id,
        invoice_number=existing_invoice["invoice_number"],  # Keep original invoice number
        patient_id=invoice_data.patient_id,
        items=invoice_data.items,
        subtotal=subtotal,
        tax_rate=invoice_data.tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        issue_date=existing_issue_date,  # Preserve original issue date
        due_date=existing_issue_date + timedelta(days=invoice_data.due_days) if invoice_data.due_days else None,
        notes=invoice_data.notes,
        created_at=existing_invoice["created_at"],  # Preserve creation time
        updated_at=datetime.utcnow()
    )
    
    updated_invoice_dict = jsonable_encoder(updated_invoice)
    await db.invoices.replace_one({"id": invoice_id}, updated_invoice_dict)
    return updated_invoice

@api_router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status_data: Dict[str, str], current_user: User = Depends(get_current_active_user)):
    """Update invoice status"""
    # Check if invoice exists
    existing_invoice = await db.invoices.find_one({"id": invoice_id})
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Validate status
    new_status = status_data.get("status")
    valid_statuses = ["draft", "sent", "paid", "overdue", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Update only the status field
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": new_status, "updated_at": jsonable_encoder(datetime.utcnow())}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Return updated invoice
    updated_invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    return Invoice(**updated_invoice)

# Inventory Routes
@api_router.post("/inventory", response_model=InventoryItem)
async def create_inventory_item(item: InventoryItem):
    item_dict = jsonable_encoder(item)
    await db.inventory.insert_one(item_dict)
    return item

@api_router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory():
    items = await db.inventory.find().to_list(1000)
    return [InventoryItem(**item) for item in items]

@api_router.get("/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str):
    """Get specific inventory item by ID"""
    item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return InventoryItem(**item)

@api_router.put("/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory_item(item_id: str, item_data: InventoryItemCreate, current_user: User = Depends(get_current_active_user)):
    """Update existing inventory item"""
    # Check if item exists
    existing_item = await db.inventory.find_one({"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Update the inventory item while preserving created_at
    updated_item = InventoryItem(
        id=item_id,
        created_at=existing_item["created_at"],  # Preserve original creation time
        updated_at=datetime.utcnow(),
        **item_data.dict()
    )
    
    updated_item_dict = jsonable_encoder(updated_item)
    await db.inventory.replace_one({"id": item_id}, updated_item_dict)
    return updated_item

@api_router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str, current_user: User = Depends(get_current_active_user)):
    """Delete inventory item"""
    result = await db.inventory.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Inventory item deleted successfully"}

@api_router.post("/inventory/{item_id}/transaction", response_model=InventoryTransaction)
async def create_inventory_transaction(item_id: str, transaction: InventoryTransaction):
    try:
        # Update inventory stock
        item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        new_stock = item["current_stock"]
        if transaction.transaction_type == "in":
            new_stock += transaction.quantity
        elif transaction.transaction_type == "out":
            new_stock -= transaction.quantity
        elif transaction.transaction_type == "adjustment":
            new_stock = transaction.quantity
        
        await db.inventory.update_one(
            {"id": item_id},
            {"$set": {"current_stock": new_stock, "updated_at": jsonable_encoder(datetime.utcnow())}}
        )
        
        # Set the item_id in the transaction
        transaction.item_id = item_id
        transaction_dict = jsonable_encoder(transaction)
        await db.inventory_transactions.insert_one(transaction_dict)
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating inventory transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating inventory transaction: {str(e)}")

# Enhanced Employee Management Routes

@api_router.post("/enhanced-employees", response_model=EnhancedEmployee)
async def create_enhanced_employee(employee_data: EnhancedEmployeeCreate):
    try:
        # Generate employee ID
        count = await db.employees.count_documents({})
        employee_id = f"EMP-{count + 1:04d}"
        
        employee = EnhancedEmployee(
            employee_id=employee_id,
            **employee_data.dict()
        )
        
        employee_dict = jsonable_encoder(employee)
        await db.enhanced_employees.insert_one(employee_dict)
        return employee
    except Exception as e:
        logger.error(f"Error creating enhanced employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

@api_router.get("/enhanced-employees", response_model=List[EnhancedEmployee])
async def get_enhanced_employees():
    employees = await db.enhanced_employees.find({"is_active": True}).to_list(1000)
    return [EnhancedEmployee(**employee) for employee in employees]

@api_router.get("/enhanced-employees/{employee_id}", response_model=EnhancedEmployee)
async def get_enhanced_employee(employee_id: str):
    employee = await db.enhanced_employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EnhancedEmployee(**employee)

@api_router.put("/enhanced-employees/{employee_id}")
async def update_enhanced_employee(employee_id: str, employee_data: Dict[str, Any]):
    try:
        employee_data["updated_at"] = datetime.utcnow()
        result = await db.enhanced_employees.update_one(
            {"id": employee_id},
            {"$set": jsonable_encoder(employee_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"message": "Employee updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

# Standard Employee Management Routes (for frontend compatibility)
@api_router.post("/employees", response_model=EnhancedEmployee)
async def create_employee(employee_data: EnhancedEmployeeCreate):
    try:
        # Generate employee ID
        count = await db.employees.count_documents({})
        employee_id = f"EMP-{count + 1:04d}"
        
        employee = EnhancedEmployee(
            employee_id=employee_id,
            **employee_data.dict()
        )
        
        employee_dict = jsonable_encoder(employee)
        await db.enhanced_employees.insert_one(employee_dict)
        return employee
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

@api_router.get("/employees", response_model=List[EnhancedEmployee])
async def get_employees():
    employees = await db.enhanced_employees.find({"is_active": True}).to_list(1000)
    return [EnhancedEmployee(**employee) for employee in employees]

@api_router.get("/employees/{employee_id}", response_model=EnhancedEmployee)
async def get_employee(employee_id: str):
    employee = await db.enhanced_employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EnhancedEmployee(**employee)

@api_router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, employee_data: Dict[str, Any]):
    try:
        employee_data["updated_at"] = datetime.utcnow()
        result = await db.enhanced_employees.update_one(
            {"id": employee_id},
            {"$set": jsonable_encoder(employee_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"message": "Employee updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str):
    try:
        # Soft delete by setting is_active to False
        result = await db.enhanced_employees.update_one(
            {"id": employee_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"message": "Employee deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

# Employee Documents Management
@api_router.post("/employee-documents", response_model=EmployeeDocument)
async def create_employee_document(document_data: EmployeeDocumentCreate):
    try:
        document = EmployeeDocument(**document_data.dict())
        document_dict = jsonable_encoder(document)
        await db.employee_documents.insert_one(document_dict)
        return document
    except Exception as e:
        logger.error(f"Error creating employee document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

@api_router.get("/employee-documents/employee/{employee_id}", response_model=List[EmployeeDocument])
async def get_employee_documents(employee_id: str):
    documents = await db.employee_documents.find({"employee_id": employee_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [EmployeeDocument(**doc) for doc in documents]

@api_router.put("/employee-documents/{document_id}/sign")
async def sign_employee_document(document_id: str, signed_by: str):
    try:
        result = await db.employee_documents.update_one(
            {"id": document_id},
            {"$set": {
                "status": "signed",
                "signed_by": signed_by,
                "signature_date": jsonable_encoder(datetime.utcnow()),
                "updated_at": jsonable_encoder(datetime.utcnow())
            }}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document signed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error signing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error signing document: {str(e)}")

@api_router.put("/employee-documents/{document_id}/approve")
async def approve_employee_document(document_id: str, approved_by: str):
    try:
        result = await db.employee_documents.update_one(
            {"id": document_id},
            {"$set": {
                "status": "approved",
                "approved_by": approved_by,
                "approval_date": jsonable_encoder(datetime.utcnow()),
                "updated_at": jsonable_encoder(datetime.utcnow())
            }}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error approving document: {str(e)}")

# Time Tracking
@api_router.post("/time-entries", response_model=TimeEntry)
async def create_time_entry(time_data: TimeEntryCreate):
    try:
        # If no timestamp provided, use current time
        if not time_data.timestamp:
            time_data.timestamp = datetime.utcnow()
        
        time_entry = TimeEntry(**time_data.dict())
        time_dict = jsonable_encoder(time_entry)
        await db.time_entries.insert_one(time_dict)
        return time_entry
    except Exception as e:
        logger.error(f"Error creating time entry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating time entry: {str(e)}")

@api_router.get("/time-entries/employee/{employee_id}", response_model=List[TimeEntry])
async def get_employee_time_entries(employee_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    try:
        query = {"employee_id": employee_id}
        
        if start_date and end_date:
            query["timestamp"] = {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            }
        
        entries = await db.time_entries.find(query, {"_id": 0}).sort("timestamp", -1).to_list(1000)
        return [TimeEntry(**entry) for entry in entries]
    except Exception as e:
        logger.error(f"Error getting time entries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting time entries: {str(e)}")

@api_router.get("/time-entries/employee/{employee_id}/current-status")
async def get_employee_current_status(employee_id: str):
    try:
        # Get the latest time entry for the employee today
        today = date.today()
        latest_entry = await db.time_entries.find_one(
            {
                "employee_id": employee_id,
                "timestamp": {
                    "$gte": datetime.combine(today, datetime.min.time()),
                    "$lte": datetime.combine(today, datetime.max.time())
                }
            },
            sort=[("timestamp", -1)]
        )
        
        if not latest_entry:
            return {"status": "not_clocked_in", "last_entry": None}
        
        entry = TimeEntry(**latest_entry)
        status = "not_clocked_in"
        
        if entry.entry_type == "clock_in":
            status = "clocked_in"
        elif entry.entry_type == "clock_out":
            status = "clocked_out"
        elif entry.entry_type == "break_start":
            status = "on_break"
        elif entry.entry_type == "break_end":
            status = "clocked_in"
        
        return {"status": status, "last_entry": entry}
    except Exception as e:
        logger.error(f"Error getting current status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting current status: {str(e)}")

# Work Schedule Management
@api_router.post("/work-shifts", response_model=WorkShift)
async def create_work_shift(shift_data: WorkShiftCreate):
    try:
        shift = WorkShift(**shift_data.dict())
        shift_dict = jsonable_encoder(shift)
        await db.work_shifts.insert_one(shift_dict)
        return shift
    except Exception as e:
        logger.error(f"Error creating work shift: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating shift: {str(e)}")

@api_router.get("/work-shifts/employee/{employee_id}", response_model=List[WorkShift])
async def get_employee_shifts(employee_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    try:
        query = {"employee_id": employee_id}
        
        if start_date and end_date:
            query["shift_date"] = {"$gte": start_date, "$lte": end_date}
        
        shifts = await db.work_shifts.find(query, {"_id": 0}).sort("shift_date", 1).to_list(1000)
        return [WorkShift(**shift) for shift in shifts]
    except Exception as e:
        logger.error(f"Error getting employee shifts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting shifts: {str(e)}")

@api_router.get("/work-shifts/date/{shift_date}", response_model=List[WorkShift])
async def get_shifts_by_date(shift_date: date):
    try:
        shifts = await db.work_shifts.find({"shift_date": shift_date}, {"_id": 0}).sort("start_time", 1).to_list(1000)
        return [WorkShift(**shift) for shift in shifts]
    except Exception as e:
        logger.error(f"Error getting shifts by date: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting shifts: {str(e)}")

@api_router.put("/work-shifts/{shift_id}/status")
async def update_shift_status(shift_id: str, status: ShiftStatus):
    try:
        result = await db.work_shifts.update_one(
            {"id": shift_id},
            {"$set": {"status": status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Shift not found")
        return {"message": "Shift status updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shift status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating shift: {str(e)}")

# Payroll and Hours Calculation
@api_router.get("/employees/{employee_id}/hours-summary")
async def get_employee_hours_summary(employee_id: str, start_date: date, end_date: date):
    try:
        # Get all time entries for the period
        entries = await db.time_entries.find({
            "employee_id": employee_id,
            "timestamp": {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            }
        }).sort("timestamp", 1).to_list(1000)
        
        # Calculate hours worked
        total_hours = 0.0
        daily_hours = {}
        current_clock_in = None
        
        for entry_data in entries:
            entry = TimeEntry(**entry_data)
            entry_date = entry.timestamp.date()
            
            if entry.entry_type == "clock_in":
                current_clock_in = entry.timestamp
            elif entry.entry_type == "clock_out" and current_clock_in:
                hours_worked = (entry.timestamp - current_clock_in).total_seconds() / 3600
                daily_hours[entry_date] = daily_hours.get(entry_date, 0) + hours_worked
                total_hours += hours_worked
                current_clock_in = None
        
        # Calculate regular vs overtime (assuming 8 hours/day, 40 hours/week is regular)
        regular_hours = min(total_hours, 40.0)
        overtime_hours = max(0, total_hours - 40.0)
        
        return {
            "employee_id": employee_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_hours": round(total_hours, 2),
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "daily_breakdown": {str(k): round(v, 2) for k, v in daily_hours.items()}
        }
    except Exception as e:
        logger.error(f"Error calculating hours: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating hours: {str(e)}")

# ===== PAYROLL MANAGEMENT ENDPOINTS =====

@api_router.post("/payroll/periods")
async def create_payroll_period(period_data: Dict):
    """Create a new payroll period"""
    try:
        # Convert date strings to date objects for validation, then back to datetime for MongoDB
        period_start = datetime.strptime(period_data["period_start"], "%Y-%m-%d")
        period_end = datetime.strptime(period_data["period_end"], "%Y-%m-%d")
        pay_date = datetime.strptime(period_data["pay_date"], "%Y-%m-%d")
        
        payroll_period = {
            "id": str(uuid.uuid4()),
            "period_start": period_start,
            "period_end": period_end,
            "pay_date": pay_date,
            "period_type": period_data["period_type"],
            "status": "draft",
            "total_gross_pay": 0.0,
            "total_net_pay": 0.0,
            "total_deductions": 0.0,
            "total_taxes": 0.0,
            "employee_count": 0,
            "created_by": period_data["created_by"],
            "approved_by": None,
            "approved_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.payroll_periods.insert_one(payroll_period)
        if result.inserted_id:
            return {"id": payroll_period["id"], "message": "Payroll period created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create payroll period")
    except Exception as e:
        logger.error(f"Error creating payroll period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating payroll period: {str(e)}")

@api_router.get("/payroll/periods")
async def get_payroll_periods(year: Optional[int] = None, status: Optional[str] = None):
    """Get all payroll periods with optional filtering"""
    try:
        query = {}
        if year:
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            query["period_start"] = {"$gte": start_date, "$lte": end_date}
        if status:
            query["status"] = status
            
        periods = []
        async for period in db.payroll_periods.find(query, {"_id": 0}).sort("period_start", -1):
            periods.append(period)
            
        return periods
    except Exception as e:
        logger.error(f"Error fetching payroll periods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching payroll periods: {str(e)}")

@api_router.post("/payroll/calculate/{period_id}")
async def calculate_payroll(period_id: str):
    """Calculate payroll for all employees in a period"""
    try:
        # Get payroll period
        period = await db.payroll_periods.find_one({"id": period_id}, {"_id": 0})
        if not period:
            raise HTTPException(status_code=404, detail="Payroll period not found")
            
        period_start = period["period_start"]
        period_end = period["period_end"]
        
        # Get all active employees
        employees = []
        async for emp in db.employees.find({"is_active": True}, {"_id": 0}):
            employees.append(emp)
        
        payroll_records = []
        
        for employee in employees:
            # Calculate hours worked from timesheet
            hours_data = await calculate_employee_hours(employee["id"], period_start, period_end)
            
            # Determine pay rate
            regular_rate = employee.get("hourly_rate", 0.0)
            if regular_rate == 0.0 and employee.get("salary"):
                # Convert salary to hourly (assuming 40 hours/week, 52 weeks/year)
                regular_rate = employee["salary"] / (40 * 52)
                
            overtime_rate = regular_rate * 1.5
            double_time_rate = regular_rate * 2.0
            
            # Calculate gross pay
            regular_pay = hours_data["regular_hours"] * regular_rate
            overtime_pay = hours_data["overtime_hours"] * overtime_rate
            double_time_pay = hours_data.get("double_time_hours", 0.0) * double_time_rate
            
            gross_pay = regular_pay + overtime_pay + double_time_pay
            
            # Calculate taxes (simplified - real implementation would use tax tables)
            federal_tax = gross_pay * 0.12  # Simplified 12% federal tax
            state_tax = gross_pay * 0.05    # Simplified 5% state tax
            social_security_tax = gross_pay * 0.062  # 6.2% social security
            medicare_tax = gross_pay * 0.0145        # 1.45% medicare
            
            total_taxes = federal_tax + state_tax + social_security_tax + medicare_tax
            
            # Calculate net pay (simplified - would include other deductions)
            net_pay = gross_pay - total_taxes
            
            # Get current YTD totals (simplified)
            ytd_gross = await get_ytd_total(employee["id"], "gross_pay")
            ytd_net = await get_ytd_total(employee["id"], "net_pay")
            ytd_federal = await get_ytd_total(employee["id"], "federal_tax")
            ytd_state = await get_ytd_total(employee["id"], "state_tax")
            ytd_ss = await get_ytd_total(employee["id"], "social_security_tax")
            ytd_medicare = await get_ytd_total(employee["id"], "medicare_tax")
            
            # Create payroll record
            payroll_record = PayrollRecord(
                payroll_period_id=period_id,
                employee_id=employee["id"],
                regular_hours=hours_data["regular_hours"],
                overtime_hours=hours_data["overtime_hours"],
                regular_rate=regular_rate,
                overtime_rate=overtime_rate,
                double_time_rate=double_time_rate,
                regular_pay=regular_pay,
                overtime_pay=overtime_pay,
                double_time_pay=double_time_pay,
                gross_pay=gross_pay,
                federal_tax=federal_tax,
                state_tax=state_tax,
                social_security_tax=social_security_tax,
                medicare_tax=medicare_tax,
                total_taxes=total_taxes,
                net_pay=net_pay,
                ytd_gross_pay=ytd_gross + gross_pay,
                ytd_net_pay=ytd_net + net_pay,
                ytd_federal_tax=ytd_federal + federal_tax,
                ytd_state_tax=ytd_state + state_tax,
                ytd_social_security_tax=ytd_ss + social_security_tax,
                ytd_medicare_tax=ytd_medicare + medicare_tax
            )
            
            payroll_records.append(payroll_record.dict())
        
        # Save all payroll records
        if payroll_records:
            result = await db.payroll_records.insert_many(payroll_records)
            
            # Update payroll period totals
            total_gross = sum(r["gross_pay"] for r in payroll_records)
            total_net = sum(r["net_pay"] for r in payroll_records)
            total_taxes = sum(r["total_taxes"] for r in payroll_records)
            
            await db.payroll_periods.update_one(
                {"id": period_id},
                {"$set": {
                    "status": "calculated",
                    "total_gross_pay": total_gross,
                    "total_net_pay": total_net,
                    "total_taxes": total_taxes,
                    "employee_count": len(payroll_records),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return {
                "message": f"Payroll calculated for {len(payroll_records)} employees",
                "total_gross_pay": total_gross,
                "total_net_pay": total_net,
                "employee_count": len(payroll_records)
            }
        else:
            return {"message": "No employees found for payroll calculation"}
            
    except Exception as e:
        logger.error(f"Error calculating payroll: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating payroll: {str(e)}")

@api_router.get("/payroll/records/{period_id}")
async def get_payroll_records(period_id: str):
    """Get all payroll records for a specific period"""
    try:
        records = []
        async for record in db.payroll_records.find({"payroll_period_id": period_id}, {"_id": 0}):
            # Get employee name
            employee = await db.employees.find_one({"id": record["employee_id"]}, {"_id": 0})
            if employee:
                record["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
            records.append(record)
            
        return records
    except Exception as e:
        logger.error(f"Error fetching payroll records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching payroll records: {str(e)}")

@api_router.get("/payroll/paystub/{record_id}")
async def generate_paystub(record_id: str):
    """Generate paystub data for a specific payroll record"""
    try:
        # Get payroll record
        payroll_record = await db.payroll_records.find_one({"id": record_id}, {"_id": 0})
        if not payroll_record:
            raise HTTPException(status_code=404, detail="Payroll record not found")
            
        # Get employee info
        employee = await db.employees.find_one({"id": payroll_record["employee_id"]}, {"_id": 0})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        # Get payroll period info
        period = await db.payroll_periods.find_one({"id": payroll_record["payroll_period_id"]}, {"_id": 0})
        if not period:
            raise HTTPException(status_code=404, detail="Payroll period not found")
        
        # Generate check number if not exists
        check_number = payroll_record.get("check_number")
        if not check_number:
            check_number = f"CHK-{record_id[:8].upper()}"
            await db.payroll_records.update_one(
                {"id": record_id},
                {"$set": {"check_number": check_number, "check_date": period["pay_date"]}}
            )
        
        # Build paystub data
        paystub_data = PaystubData(
            employee_info={
                "name": f"{employee['first_name']} {employee['last_name']}",
                "employee_id": employee.get("employee_id", employee["id"]),
                "address": f"{employee.get('address', '')}, {employee.get('city', '')}, {employee.get('state', '')} {employee.get('zip_code', '')}".strip(", "),
                "ssn_last_four": employee.get("ssn_last_four", "")
            },
            pay_period={
                "start_date": period["period_start"],
                "end_date": period["period_end"],
                "pay_date": period["pay_date"],
                "period_type": period["period_type"]
            },
            hours_breakdown={
                "regular_hours": payroll_record["regular_hours"],
                "overtime_hours": payroll_record["overtime_hours"],
                "double_time_hours": payroll_record.get("double_time_hours", 0.0),
                "sick_hours": payroll_record.get("sick_hours", 0.0),
                "vacation_hours": payroll_record.get("vacation_hours", 0.0),
                "holiday_hours": payroll_record.get("holiday_hours", 0.0)
            },
            pay_breakdown={
                "regular_pay": payroll_record["regular_pay"],
                "overtime_pay": payroll_record["overtime_pay"],
                "double_time_pay": payroll_record.get("double_time_pay", 0.0),
                "sick_pay": payroll_record.get("sick_pay", 0.0),
                "vacation_pay": payroll_record.get("vacation_pay", 0.0),
                "holiday_pay": payroll_record.get("holiday_pay", 0.0),
                "bonus_pay": payroll_record.get("bonus_pay", 0.0),
                "commission_pay": payroll_record.get("commission_pay", 0.0),
                "other_pay": payroll_record.get("other_pay", 0.0),
                "gross_pay": payroll_record["gross_pay"]
            },
            deductions_breakdown=[
                {"description": "Health Insurance", "amount": 0.0},  # Would be populated from actual deductions
                {"description": "401k", "amount": 0.0}
            ],
            taxes_breakdown={
                "federal_tax": payroll_record["federal_tax"],
                "state_tax": payroll_record["state_tax"],
                "social_security_tax": payroll_record["social_security_tax"],
                "medicare_tax": payroll_record["medicare_tax"],
                "total_taxes": payroll_record["total_taxes"]
            },
            ytd_totals={
                "ytd_gross_pay": payroll_record["ytd_gross_pay"],
                "ytd_net_pay": payroll_record["ytd_net_pay"],
                "ytd_federal_tax": payroll_record["ytd_federal_tax"],
                "ytd_state_tax": payroll_record["ytd_state_tax"],
                "ytd_social_security_tax": payroll_record["ytd_social_security_tax"],
                "ytd_medicare_tax": payroll_record["ytd_medicare_tax"]
            },
            net_pay=payroll_record["net_pay"],
            check_number=check_number,
            check_date=period["pay_date"]
        )
        
        return paystub_data.dict()
        
    except Exception as e:
        logger.error(f"Error generating paystub: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating paystub: {str(e)}")

@api_router.post("/payroll/approve/{period_id}")
async def approve_payroll(period_id: str, approval_data: Dict):
    """Approve a calculated payroll period"""
    try:
        result = await db.payroll_periods.update_one(
            {"id": period_id, "status": "calculated"},
            {"$set": {
                "status": "approved",
                "approved_by": approval_data["approved_by"],
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Payroll period not found or not in calculated status")
            
        # Update all payroll records to approved status
        await db.payroll_records.update_many(
            {"payroll_period_id": period_id},
            {"$set": {"check_status": "approved"}}
        )
        
        return {"message": "Payroll period approved successfully"}
        
    except Exception as e:
        logger.error(f"Error approving payroll: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error approving payroll: {str(e)}")

@api_router.post("/payroll/pay/{period_id}")
async def mark_payroll_paid(period_id: str):
    """Mark payroll period as paid (checks issued)"""
    try:
        result = await db.payroll_periods.update_one(
            {"id": period_id, "status": "approved"},
            {"$set": {
                "status": "paid",
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Payroll period not found or not approved")
            
        # Update all payroll records to paid status
        await db.payroll_records.update_many(
            {"payroll_period_id": period_id},
            {"$set": {"check_status": "paid"}}
        )
        
        return {"message": "Payroll marked as paid successfully"}
        
    except Exception as e:
        logger.error(f"Error marking payroll as paid: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error marking payroll as paid: {str(e)}")

# Helper functions for payroll calculations
async def calculate_employee_hours(employee_id: str, start_date, end_date) -> Dict[str, float]:
    """Calculate employee hours from timesheet entries"""
    try:
        # Ensure dates are datetime objects for MongoDB queries
        if isinstance(start_date, datetime):
            start_datetime = start_date
        else:
            start_datetime = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
            
        if isinstance(end_date, datetime):
            end_datetime = end_date
        else:
            end_datetime = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.max.time())
        
        # Get all time entries for the period
        entries = []
        async for entry in db.time_entries.find({
            "employee_id": employee_id,
            "timestamp": {
                "$gte": start_datetime,
                "$lte": end_datetime
            }
        }, {"_id": 0}).sort("timestamp", 1):
            entries.append(entry)
        
        # Calculate hours worked
        total_hours = 0.0
        daily_hours = {}
        current_clock_in = None
        
        for entry in entries:
            entry_date = entry["timestamp"].date()
            
            if entry["entry_type"] == "clock_in":
                current_clock_in = entry["timestamp"]
            elif entry["entry_type"] == "clock_out" and current_clock_in:
                hours_worked = (entry["timestamp"] - current_clock_in).total_seconds() / 3600
                daily_hours[entry_date] = daily_hours.get(entry_date, 0) + hours_worked
                total_hours += hours_worked
                current_clock_in = None
        
        # Calculate regular vs overtime (assuming 40 hours/week is regular)
        regular_hours = min(total_hours, 40.0)
        overtime_hours = max(0, total_hours - 40.0)
        
        return {
            "total_hours": round(total_hours, 2),
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "double_time_hours": 0.0,  # Would be calculated based on company policy
            "daily_breakdown": {str(k): round(v, 2) for k, v in daily_hours.items()}
        }
    except Exception as e:
        logger.error(f"Error calculating employee hours: {str(e)}")
        return {"total_hours": 0.0, "regular_hours": 0.0, "overtime_hours": 0.0, "double_time_hours": 0.0}

async def get_ytd_total(employee_id: str, field: str) -> float:
    """Get year-to-date total for a specific field"""
    try:
        current_year = datetime.now().year
        start_of_year = datetime(current_year, 1, 1)
        
        pipeline = [
            {
                "$match": {
                    "employee_id": employee_id,
                    "payroll_period_id": {
                        "$exists": True
                    }
                }
            },
            {
                "$lookup": {
                    "from": "payroll_periods",
                    "localField": "payroll_period_id",
                    "foreignField": "id",
                    "as": "period"
                }
            },
            {
                "$match": {
                    "period.period_start": {"$gte": start_of_year}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": f"${field}"}
                }
            }
        ]
        
        result = await db.payroll_records.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0.0
        
    except Exception as e:
        logger.error(f"Error calculating YTD total: {str(e)}")
        return 0.0

# Finance Module Routes

# Vendor Management
@api_router.post("/vendors", response_model=Vendor)
async def create_vendor(vendor_data: VendorCreate):
    try:
        # Generate vendor code
        count = await db.vendors.count_documents({})
        vendor_code = f"VND-{count + 1:04d}"
        
        vendor = Vendor(
            vendor_code=vendor_code,
            **vendor_data.dict()
        )
        
        vendor_dict = jsonable_encoder(vendor)
        await db.vendors.insert_one(vendor_dict)
        return vendor
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating vendor: {str(e)}")

@api_router.get("/vendors", response_model=List[Vendor])
async def get_vendors():
    vendors = await db.vendors.find({"status": {"$ne": "inactive"}}, {"_id": 0}).sort("company_name", 1).to_list(1000)
    return [Vendor(**vendor) for vendor in vendors]

@api_router.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str):
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return Vendor(**vendor)

@api_router.put("/vendors/{vendor_id}")
async def update_vendor(vendor_id: str, vendor_data: Dict[str, Any]):
    try:
        vendor_data["updated_at"] = datetime.utcnow()
        result = await db.vendors.update_one(
            {"id": vendor_id},
            {"$set": jsonable_encoder(vendor_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return {"message": "Vendor updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating vendor: {str(e)}")

# Check Management
@api_router.post("/checks", response_model=Check)
async def create_check(check_data: CheckCreate):
    try:
        # Generate check number
        count = await db.checks.count_documents({})
        check_number = f"{count + 1001:04d}"  # Start from 1001
        
        # Calculate total amount
        total_amount = check_data.amount
        
        check = Check(
            check_number=check_number,
            **check_data.dict()
        )
        
        check_dict = jsonable_encoder(check)
        await db.checks.insert_one(check_dict)
        
        # Create corresponding expense transaction
        if check.expense_category:
            transaction = FinancialTransaction(
                transaction_number=f"EXP-{check_number}",
                transaction_type=TransactionType.EXPENSE,
                amount=check.amount,
                payment_method=PaymentMethod.CHECK,
                transaction_date=check.check_date,
                description=f"Check #{check_number} - {check.memo or 'Payment to ' + check.payee_name}",
                category=check.expense_category,
                vendor_id=check.payee_id if check.payee_type == "vendor" else None,
                check_id=check.id,
                reference_number=check_number,
                created_by=check.created_by
            )
            
            transaction_dict = jsonable_encoder(transaction)
            await db.financial_transactions.insert_one(transaction_dict)
        
        return check
    except Exception as e:
        logger.error(f"Error creating check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating check: {str(e)}")

@api_router.get("/checks", response_model=List[Check])
async def get_checks():
    checks = await db.checks.find().sort("created_at", -1).to_list(1000)
    return [Check(**check) for check in checks]

@api_router.put("/checks/{check_id}/status")
async def update_check_status(check_id: str, status_data: Dict[str, str], current_user: User = Depends(get_current_active_user)):
    """Update check status"""
    try:
        # Validate status
        new_status = status_data.get("status")
        valid_statuses = ["draft", "printed", "issued", "cleared", "voided"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Check if check exists
        existing_check = await db.checks.find_one({"id": check_id})
        if not existing_check:
            raise HTTPException(status_code=404, detail="Check not found")
        
        update_data = {"status": new_status, "updated_at": jsonable_encoder(datetime.utcnow())}
        
        # Set appropriate date fields based on status
        if new_status == "printed":
            update_data["printed_date"] = jsonable_encoder(datetime.utcnow())
        elif new_status == "issued":
            update_data["issued_date"] = jsonable_encoder(datetime.utcnow())
        elif new_status == "cleared":
            update_data["cleared_date"] = jsonable_encoder(datetime.utcnow())
        elif new_status == "voided":
            update_data["void_date"] = jsonable_encoder(date.today())
        
        result = await db.checks.update_one(
            {"id": check_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Check not found")
        
        # Return updated check
        updated_check = await db.checks.find_one({"id": check_id}, {"_id": 0})
        return Check(**updated_check)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating check status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating check: {str(e)}")

@api_router.get("/checks/{check_id}/print-data")
async def get_check_print_data(check_id: str):
    try:
        check = await db.checks.find_one({"id": check_id}, {"_id": 0})
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")
        
        check_obj = Check(**check)
        
        # Get payee details if vendor
        payee_details = None
        if check_obj.payee_type == "vendor" and check_obj.payee_id:
            vendor = await db.vendors.find_one({"id": check_obj.payee_id}, {"_id": 0})
            if vendor:
                payee_details = Vendor(**vendor)
        
        # Format amount in words (basic implementation)
        def amount_to_words(amount):
            # Simple implementation - in production, use a proper library
            return f"***** {amount:.2f} DOLLARS *****"
        
        print_data = {
            "check": check_obj,
            "payee_details": payee_details,
            "amount_in_words": amount_to_words(check_obj.amount),
            "clinic_info": {
                "name": "ClinicHub Medical Practice",
                "address": "123 Healthcare Drive",
                "city_state_zip": "Medical City, HC 12345",
                "phone": "(555) 123-CARE"
            }
        }
        
        return print_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting check print data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting print data: {str(e)}")

@api_router.post("/checks/{check_id}/print")
async def print_check(check_id: str, current_user: User = Depends(get_current_active_user)):
    """Print check and update status to printed"""
    try:
        # Check if check exists
        check = await db.checks.find_one({"id": check_id}, {"_id": 0})
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")
        
        check_obj = Check(**check)
        
        # Validate that check can be printed (not already printed or voided)
        if check_obj.status in ["printed", "issued", "cleared", "voided"]:
            raise HTTPException(status_code=400, detail=f"Check cannot be printed - current status: {check_obj.status}")
        
        # Update check status to printed
        result = await db.checks.update_one(
            {"id": check_id},
            {"$set": {"status": "printed", "updated_at": jsonable_encoder(datetime.utcnow())}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Check not found")
        
        # Get updated check for response
        updated_check = await db.checks.find_one({"id": check_id}, {"_id": 0})
        
        return {
            "message": "Check printed successfully",
            "check": Check(**updated_check),
            "print_job_id": f"PRINT-{check_id[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error printing check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error printing check: {str(e)}")

# Financial Transactions
@api_router.post("/financial-transactions", response_model=FinancialTransaction)
async def create_financial_transaction(transaction_data: FinancialTransactionCreate):
    try:
        # Generate transaction number
        count = await db.financial_transactions.count_documents({})
        prefix = "INC" if transaction_data.transaction_type == TransactionType.INCOME else "EXP"
        transaction_number = f"{prefix}-{count + 1:06d}"
        
        # Prepare transaction data with defaults
        transaction_dict = transaction_data.dict()
        if transaction_dict.get("transaction_date") is None:
            transaction_dict["transaction_date"] = date.today()
        
        transaction = FinancialTransaction(
            transaction_number=transaction_number,
            **transaction_dict
        )
        
        transaction_dict = jsonable_encoder(transaction)
        await db.financial_transactions.insert_one(transaction_dict)
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")

@api_router.get("/financial-transactions", response_model=List[FinancialTransaction])
async def get_financial_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[TransactionType] = None
):
    try:
        query = {}
        
        if start_date and end_date:
            query["transaction_date"] = {"$gte": start_date, "$lte": end_date}
        
        if transaction_type:
            query["transaction_type"] = transaction_type
        
        transactions = await db.financial_transactions.find(query, {"_id": 0}).sort("transaction_date", -1).to_list(1000)
        return [FinancialTransaction(**trans) for trans in transactions]
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transactions: {str(e)}")

@api_router.get("/financial-transactions/{transaction_id}", response_model=FinancialTransaction)
async def get_financial_transaction(transaction_id: str):
    """Get specific financial transaction by ID"""
    transaction = await db.financial_transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Financial transaction not found")
    return FinancialTransaction(**transaction)

@api_router.put("/financial-transactions/{transaction_id}", response_model=FinancialTransaction)
async def update_financial_transaction(transaction_id: str, transaction_data: FinancialTransactionCreate, current_user: User = Depends(get_current_active_user)):
    """Update existing financial transaction"""
    # Check if transaction exists
    existing_transaction = await db.financial_transactions.find_one({"id": transaction_id})
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Financial transaction not found")
    
    # Create updated transaction
    updated_transaction = FinancialTransaction(
        id=transaction_id,
        transaction_number=existing_transaction["transaction_number"],  # Keep original transaction number
        created_at=existing_transaction["created_at"],  # Preserve creation time
        updated_at=datetime.utcnow(),
        **transaction_data.dict()
    )
    
    updated_transaction_dict = jsonable_encoder(updated_transaction)
    await db.financial_transactions.replace_one({"id": transaction_id}, updated_transaction_dict)
    return updated_transaction

# Vendor Invoice Management
@api_router.post("/vendor-invoices", response_model=VendorInvoice)
async def create_vendor_invoice(invoice_data: VendorInvoiceCreate):
    try:
        # Calculate total amount
        total_amount = invoice_data.amount + invoice_data.tax_amount
        
        invoice = VendorInvoice(
            total_amount=total_amount,
            **invoice_data.dict()
        )
        
        invoice_dict = jsonable_encoder(invoice)
        await db.vendor_invoices.insert_one(invoice_dict)
        return invoice
    except Exception as e:
        logger.error(f"Error creating vendor invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")

@api_router.get("/vendor-invoices", response_model=List[VendorInvoice])
async def get_vendor_invoices():
    invoices = await db.vendor_invoices.find().sort("invoice_date", -1).to_list(1000)
    return [VendorInvoice(**inv) for inv in invoices]

@api_router.get("/vendor-invoices/unpaid", response_model=List[VendorInvoice])
async def get_unpaid_vendor_invoices():
    invoices = await db.vendor_invoices.find({"payment_status": "unpaid"}, {"_id": 0}).sort("due_date", 1).to_list(1000)
    return [VendorInvoice(**inv) for inv in invoices]

@api_router.put("/vendor-invoices/{invoice_id}/pay")
async def pay_vendor_invoice(invoice_id: str, check_id: str):
    try:
        # Get invoice and check
        invoice = await db.vendor_invoices.find_one({"id": invoice_id}, {"_id": 0})
        check = await db.checks.find_one({"id": check_id}, {"_id": 0})
        
        if not invoice or not check:
            raise HTTPException(status_code=404, detail="Invoice or check not found")
        
        # Update invoice payment status
        result = await db.vendor_invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "payment_status": "paid",
                "amount_paid": invoice["total_amount"],
                "payment_date": date.today(),
                "check_id": check_id,
                "updated_at": jsonable_encoder(datetime.utcnow())
            }}
        )
        
        # Update check reference
        await db.checks.update_one(
            {"id": check_id},
            {"$set": {"reference_invoice_id": invoice_id}}
        )
        
        return {"message": "Invoice marked as paid"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error paying invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error paying invoice: {str(e)}")

# Daily Financial Summary
@api_router.get("/financial-summary/{summary_date}")
async def get_daily_financial_summary(summary_date: date):
    try:
        # Get all transactions for the date
        transactions = await db.financial_transactions.find({
            "transaction_date": summary_date
        }).to_list(1000)
        
        # Calculate totals
        cash_income = 0.0
        credit_card_income = 0.0
        check_income = 0.0
        other_income = 0.0
        
        cash_expenses = 0.0
        check_expenses = 0.0
        credit_card_expenses = 0.0
        other_expenses = 0.0
        
        income_count = 0
        expense_count = 0
        
        for trans_data in transactions:
            trans = FinancialTransaction(**trans_data)
            
            if trans.transaction_type == TransactionType.INCOME:
                income_count += 1
                if trans.payment_method == PaymentMethod.CASH:
                    cash_income += trans.amount
                elif trans.payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                    credit_card_income += trans.amount
                elif trans.payment_method == PaymentMethod.CHECK:
                    check_income += trans.amount
                else:
                    other_income += trans.amount
            
            elif trans.transaction_type == TransactionType.EXPENSE:
                expense_count += 1
                if trans.payment_method == PaymentMethod.CASH:
                    cash_expenses += trans.amount
                elif trans.payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                    credit_card_expenses += trans.amount
                elif trans.payment_method == PaymentMethod.CHECK:
                    check_expenses += trans.amount
                else:
                    other_expenses += trans.amount
        
        total_income = cash_income + credit_card_income + check_income + other_income
        total_expenses = cash_expenses + check_expenses + credit_card_expenses + other_expenses
        net_amount = total_income - total_expenses
        
        summary = DailyFinancialSummary(
            summary_date=summary_date,
            cash_income=cash_income,
            credit_card_income=credit_card_income,
            check_income=check_income,
            other_income=other_income,
            total_income=total_income,
            cash_expenses=cash_expenses,
            check_expenses=check_expenses,
            credit_card_expenses=credit_card_expenses,
            other_expenses=other_expenses,
            total_expenses=total_expenses,
            net_amount=net_amount,
            income_transaction_count=income_count,
            expense_transaction_count=expense_count,
            created_by="System"
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error generating financial summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@api_router.get("/financial-reports/monthly/{year}/{month}")
async def get_monthly_financial_report(year: int, month: int):
    try:
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get all transactions for the month
        transactions = await db.financial_transactions.find({
            "transaction_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(10000)
        
        # Calculate category-wise totals
        income_by_category = {}
        expense_by_category = {}
        total_income = 0.0
        total_expenses = 0.0
        
        for trans_data in transactions:
            trans = FinancialTransaction(**trans_data)
            
            if trans.transaction_type == TransactionType.INCOME:
                total_income += trans.amount
                category = trans.category or "other_income"
                income_by_category[category] = income_by_category.get(category, 0) + trans.amount
            
            elif trans.transaction_type == TransactionType.EXPENSE:
                total_expenses += trans.amount
                category = trans.category or "other_expense"
                expense_by_category[category] = expense_by_category.get(category, 0) + trans.amount
        
        # Get unpaid vendor invoices
        unpaid_invoices = await db.vendor_invoices.find({
            "payment_status": "unpaid",
            "due_date": {"$lte": end_date}
        }).to_list(1000)
        
        total_payables = sum(inv["total_amount"] for inv in unpaid_invoices)
        
        return {
            "period": {"year": year, "month": month, "start_date": start_date, "end_date": end_date},
            "summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_income": total_income - total_expenses,
                "total_payables": total_payables
            },
            "income_breakdown": income_by_category,
            "expense_breakdown": expense_by_category,
            "unpaid_invoices_count": len(unpaid_invoices),
            "transaction_count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# Dashboard Integration - Update existing dashboard
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    try:
        total_patients = await db.patients.count_documents({"status": "active"})
        total_invoices = await db.invoices.count_documents({})
        total_enhanced_invoices = await db.enhanced_invoices.count_documents({})
        pending_invoices = await db.invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        pending_enhanced_invoices = await db.enhanced_invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        low_stock_items = await db.inventory.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}})
        total_employees = await db.employees.count_documents({"is_active": True})
        
        # Finance stats
        today = datetime.combine(date.today(), datetime.min.time())  # Convert date to datetime for MongoDB
        today_income = await db.financial_transactions.aggregate([
            {"$match": {"transaction_date": today, "transaction_type": "income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        unpaid_vendor_invoices = await db.vendor_invoices.count_documents({"payment_status": "unpaid"})
        pending_checks = await db.checks.count_documents({"status": {"$in": ["draft", "printed"]}})
        
        # Recent activity (removed encounters from dashboard)
        recent_patients = await db.patients.find().sort("created_at", -1).limit(5).to_list(5)
        recent_invoices = await db.invoices.find().sort("created_at", -1).limit(3).to_list(3)
        recent_enhanced_invoices = await db.enhanced_invoices.find().sort("created_at", -1).limit(2).to_list(2)
        
        # Combine recent invoices
        all_recent_invoices = []
        for inv in recent_invoices:
            all_recent_invoices.append(Invoice(**inv))
        for inv in recent_enhanced_invoices:
            all_recent_invoices.append(EnhancedInvoice(**inv))
        
        return {
            "stats": {
                "total_patients": total_patients,
                "total_invoices": total_invoices + total_enhanced_invoices,
                "pending_invoices": pending_invoices + pending_enhanced_invoices,
                "low_stock_items": low_stock_items,
                "total_employees": total_employees,
                "today_income": today_income[0]["total"] if today_income else 0.0,
                "unpaid_vendor_invoices": unpaid_vendor_invoices,
                "pending_checks": pending_checks
            },
            "recent_patients": [Patient(**p) for p in recent_patients],
            "recent_invoices": all_recent_invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard stats: {str(e)}")

# New Dashboard Views for Clinic Operations
@api_router.get("/dashboard/erx-patients")
async def get_erx_patients(current_user: User = Depends(get_current_active_user)):
    """Get patients scheduled for today (for eRx management)"""
    try:
        today = date.today()
        
        # Get patients with encounters scheduled for today
        todays_encounters = await db.encounters.find({
            "scheduled_date": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
            }
        }).sort("scheduled_date", 1).to_list(100)
        
        # Get patient details for each encounter
        erx_patients = []
        for encounter in todays_encounters:
            patient = await db.patients.find_one({"id": encounter["patient_id"]}, {"_id": 0})
            if patient:
                # Get active prescriptions count
                active_prescriptions = await db.prescriptions.count_documents({
                    "patient_id": encounter["patient_id"],
                    "status": {"$in": ["active", "draft"]}
                })
                
                erx_patients.append({
                    "encounter_id": encounter["id"],
                    "encounter_number": encounter["encounter_number"],
                    "patient_id": patient["id"],
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                    "scheduled_time": encounter["scheduled_date"],
                    "encounter_type": encounter["encounter_type"],
                    "status": encounter["status"],
                    "provider": encounter.get("provider", "Not assigned"),
                    "chief_complaint": encounter.get("chief_complaint", ""),
                    "active_prescriptions": active_prescriptions,
                    "allergies_count": len(await db.allergies.find({"patient_id": patient["id"]}).to_list(100))
                })
        
        return {
            "date": today.isoformat(),
            "total_scheduled": len(erx_patients),
            "patients": erx_patients
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving eRx patients: {str(e)}")

@api_router.get("/dashboard/daily-log")
async def get_daily_log(current_user: User = Depends(get_current_active_user)):
    """Get patients seen today with visit types and payment information"""
    try:
        today = date.today()
        
        # Get completed encounters for today
        completed_encounters = await db.encounters.find({
            "status": "completed",
            "actual_end_time": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
            }
        }).sort("actual_end_time", -1).to_list(100)
        
        daily_log = []
        total_revenue = 0
        total_paid = 0
        
        for encounter in completed_encounters:
            patient = await db.patients.find_one({"id": encounter["patient_id"]}, {"_id": 0})
            if patient:
                # Get related invoices
                invoices = await db.invoices.find({"encounter_id": encounter["id"]}).to_list(100)
                enhanced_invoices = await db.enhanced_invoices.find({"encounter_id": encounter["id"]}).to_list(100)
                
                # Calculate totals
                encounter_total = 0
                encounter_paid = 0
                payment_status = "unpaid"
                
                for invoice in invoices:
                    encounter_total += invoice.get("total_amount", 0)
                    if invoice.get("status") == "paid":
                        encounter_paid += invoice.get("total_amount", 0)
                
                for invoice in enhanced_invoices:
                    encounter_total += invoice.get("total_amount", 0)
                    if invoice.get("payment_status") == "paid":
                        encounter_paid += invoice.get("total_amount", 0)
                
                if encounter_paid >= encounter_total and encounter_total > 0:
                    payment_status = "paid"
                elif encounter_paid > 0:
                    payment_status = "partial"
                
                total_revenue += encounter_total
                total_paid += encounter_paid
                
                daily_log.append({
                    "encounter_id": encounter["id"],
                    "encounter_number": encounter["encounter_number"],
                    "patient_id": patient["id"],
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                    "visit_type": encounter["encounter_type"].replace("_", " ").title(),
                    "completed_time": encounter.get("actual_end_time"),
                    "provider": encounter.get("provider", "Not specified"),
                    "total_amount": encounter_total,
                    "paid_amount": encounter_paid,
                    "payment_status": payment_status,
                    "chief_complaint": encounter.get("chief_complaint", "")
                })
        
        return {
            "date": today.isoformat(),
            "summary": {
                "total_patients_seen": len(daily_log),
                "total_revenue": total_revenue,
                "total_paid": total_paid,
                "outstanding_amount": total_revenue - total_paid
            },
            "visits": daily_log
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving daily log: {str(e)}")

@api_router.get("/dashboard/patient-queue")
async def get_patient_queue(current_user: User = Depends(get_current_active_user)):
    """Get current patient locations in the clinic"""
    try:
        today = date.today()
        
        # Get today's encounters that are in progress
        active_encounters = await db.encounters.find({
            "scheduled_date": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
            },
            "status": {"$in": ["arrived", "in_progress", "waiting"]}
        }).sort("scheduled_date", 1).to_list(100)
        
        # Define clinic locations
        locations = {
            "lobby": [],
            "room_1": [],
            "room_2": [],
            "room_3": [],
            "room_4": [],
            "iv_room": [],
            "checkout": []
        }
        
        queue_data = []
        
        for encounter in active_encounters:
            patient = await db.patients.find_one({"id": encounter["patient_id"]}, {"_id": 0})
            if patient:
                # Determine location based on encounter status and time
                location = "lobby"  # default
                if encounter["status"] == "arrived":
                    location = "lobby"
                elif encounter["status"] == "in_progress":
                    # Assign to rooms based on encounter type or randomly for demo
                    if "iv" in encounter.get("encounter_type", "").lower():
                        location = "iv_room"
                    else:
                        # Simple assignment based on encounter number
                        room_num = (len(encounter.get("encounter_number", "")) % 4) + 1
                        location = f"room_{room_num}"
                elif encounter["status"] == "waiting":
                    location = "checkout"
                
                # Calculate wait time
                arrival_time = encounter.get("actual_start_time", encounter["scheduled_date"])
                if isinstance(arrival_time, str):
                    arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
                wait_minutes = int((datetime.utcnow() - arrival_time).total_seconds() / 60)
                
                patient_info = {
                    "encounter_id": encounter["id"],
                    "encounter_number": encounter["encounter_number"],
                    "patient_id": patient["id"],
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                    "scheduled_time": encounter["scheduled_date"],
                    "encounter_type": encounter["encounter_type"].replace("_", " ").title(),
                    "status": encounter["status"],
                    "location": location,
                    "wait_time_minutes": max(0, wait_minutes),
                    "provider": encounter.get("provider", "Not assigned"),
                    "priority": "normal"  # Could be enhanced with priority logic
                }
                
                # Add to appropriate location
                locations[location].append(patient_info)
                queue_data.append(patient_info)
        
        # Calculate summary stats
        total_waiting = len(queue_data)
        avg_wait_time = sum(p["wait_time_minutes"] for p in queue_data) / total_waiting if total_waiting > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_patients": total_waiting,
                "average_wait_time": round(avg_wait_time, 1),
                "locations_in_use": len([loc for loc, patients in locations.items() if patients])
            },
            "locations": locations,
            "all_patients": queue_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient queue: {str(e)}")

@api_router.get("/dashboard/pending-payments")
async def get_pending_payments(current_user: User = Depends(get_current_active_user)):
    """Get patients with unpaid invoices"""
    try:
        # Get all unpaid invoices
        unpaid_invoices = await db.invoices.find({
            "status": {"$in": ["draft", "sent"]}
        }).sort("created_at", -1).to_list(100)
        
        unpaid_enhanced_invoices = await db.enhanced_invoices.find({
            "payment_status": {"$in": ["unpaid", "partial"]}
        }).sort("created_at", -1).to_list(100)
        
        pending_payments = []
        total_outstanding = 0
        today = datetime.now().date()
        
        # Process regular invoices
        for invoice in unpaid_invoices:
            patient = await db.patients.find_one({"id": invoice["patient_id"]}, {"_id": 0})
            if patient:
                outstanding_amount = invoice.get("total_amount", 0)
                total_outstanding += outstanding_amount
                
                # Get encounter details if available
                encounter = None
                if "encounter_id" in invoice:
                    encounter = await db.encounters.find_one({"id": invoice["encounter_id"]}, {"_id": 0})
                
                # Handle due date calculation safely
                due_date = invoice.get("due_date")
                days_overdue = 0
                if due_date:
                    if isinstance(due_date, str):
                        try:
                            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
                            days_overdue = (today - due_date).days
                        except (ValueError, TypeError):
                            days_overdue = 0
                    elif isinstance(due_date, date):
                        days_overdue = (today - due_date).days
                
                pending_payments.append({
                    "invoice_id": invoice["id"],
                    "invoice_number": invoice["invoice_number"],
                    "invoice_type": "standard",
                    "patient_id": patient["id"],
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                    "patient_phone": patient.get("telecom", [{}])[0].get("value", ""),
                    "total_amount": invoice.get("total_amount", 0),
                    "outstanding_amount": outstanding_amount,
                    "invoice_date": invoice.get("issue_date"),
                    "due_date": due_date,
                    "days_overdue": max(0, days_overdue),
                    "encounter_type": encounter.get("encounter_type", "").replace("_", " ").title() if encounter else "N/A",
                    "status": invoice.get("status", "draft")
                })
        
        # Process enhanced invoices
        for invoice in unpaid_enhanced_invoices:
            patient = await db.patients.find_one({"id": invoice["patient_id"]}, {"_id": 0})
            if patient:
                outstanding_amount = invoice.get("total_amount", 0) - invoice.get("amount_paid", 0)
                total_outstanding += outstanding_amount
                
                # Get encounter details if available
                encounter = None
                if "encounter_id" in invoice:
                    encounter = await db.encounters.find_one({"id": invoice["encounter_id"]}, {"_id": 0})
                
                # Handle due date calculation safely
                due_date = invoice.get("due_date")
                days_overdue = 0
                if due_date:
                    if isinstance(due_date, str):
                        try:
                            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
                            days_overdue = (today - due_date).days
                        except (ValueError, TypeError):
                            days_overdue = 0
                    elif isinstance(due_date, date):
                        days_overdue = (today - due_date).days
                
                pending_payments.append({
                    "invoice_id": invoice["id"],
                    "invoice_number": invoice["invoice_number"],
                    "invoice_type": "enhanced",
                    "patient_id": patient["id"],
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                    "patient_phone": patient.get("telecom", [{}])[0].get("value", ""),
                    "total_amount": invoice.get("total_amount", 0),
                    "outstanding_amount": outstanding_amount,
                    "invoice_date": invoice.get("issue_date"),
                    "due_date": due_date,
                    "days_overdue": max(0, days_overdue),
                    "encounter_type": encounter.get("encounter_type", "").replace("_", " ").title() if encounter else "N/A",
                    "status": invoice.get("payment_status", "unpaid"),
                    "amount_paid": invoice.get("amount_paid", 0)
                })
        
        # Sort by days overdue (most overdue first)
        pending_payments.sort(key=lambda x: x["days_overdue"], reverse=True)
        
        # Calculate summary statistics
        overdue_count = len([p for p in pending_payments if p["days_overdue"] > 0])
        avg_days_overdue = sum(max(0, p["days_overdue"]) for p in pending_payments) / len(pending_payments) if pending_payments else 0
        
        return {
            "summary": {
                "total_outstanding_amount": total_outstanding,
                "total_pending_invoices": len(pending_payments),
                "overdue_invoices": overdue_count,
                "average_days_overdue": round(avg_days_overdue, 1)
            },
            "pending_payments": pending_payments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pending payments: {str(e)}")

@api_router.get("/dashboard/legacy-stats")
async def get_legacy_dashboard_stats():
    try:
        total_patients = await db.patients.count_documents({"status": "active"})
        total_invoices = await db.invoices.count_documents({})
        total_enhanced_invoices = await db.enhanced_invoices.count_documents({})
        pending_invoices = await db.invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        pending_enhanced_invoices = await db.enhanced_invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        low_stock_items = await db.inventory.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}})
        total_employees = await db.employees.count_documents({"is_active": True})
        
        # Recent activity (removed encounters from dashboard)
        recent_patients = await db.patients.find().sort("created_at", -1).limit(5).to_list(5)
        recent_invoices = await db.invoices.find().sort("created_at", -1).limit(3).to_list(3)
        recent_enhanced_invoices = await db.enhanced_invoices.find().sort("created_at", -1).limit(2).to_list(2)
        
        # Combine recent invoices
        all_recent_invoices = []
        for inv in recent_invoices:
            all_recent_invoices.append(Invoice(**inv))
        for inv in recent_enhanced_invoices:
            all_recent_invoices.append(EnhancedInvoice(**inv))
        
        return {
            "stats": {
                "total_patients": total_patients,
                "total_invoices": total_invoices + total_enhanced_invoices,
                "pending_invoices": pending_invoices + pending_enhanced_invoices,
                "low_stock_items": low_stock_items,
                "total_employees": total_employees
            },
            "recent_patients": [Patient(**p) for p in recent_patients],
            "recent_invoices": all_recent_invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving legacy dashboard stats: {str(e)}")

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    try:
        total_patients = await db.patients.count_documents({"status": "active"})
        total_invoices = await db.invoices.count_documents({})
        total_enhanced_invoices = await db.enhanced_invoices.count_documents({})
        pending_invoices = await db.invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        pending_enhanced_invoices = await db.enhanced_invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
        low_stock_items = await db.inventory.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}})
        total_employees = await db.employees.count_documents({"is_active": True})
        
        # Recent activity (removed encounters from dashboard)
        recent_patients = await db.patients.find().sort("created_at", -1).limit(5).to_list(5)
        recent_invoices = await db.invoices.find().sort("created_at", -1).limit(3).to_list(3)
        recent_enhanced_invoices = await db.enhanced_invoices.find().sort("created_at", -1).limit(2).to_list(2)
        
        # Combine recent invoices
        all_recent_invoices = []
        for inv in recent_invoices:
            all_recent_invoices.append(Invoice(**inv))
        for inv in recent_enhanced_invoices:
            all_recent_invoices.append(EnhancedInvoice(**inv))
        
        return {
            "stats": {
                "total_patients": total_patients,
                "total_invoices": total_invoices + total_enhanced_invoices,
                "pending_invoices": pending_invoices + pending_enhanced_invoices,
                "low_stock_items": low_stock_items,
                "total_employees": total_employees
            },
            "recent_patients": [Patient(**p) for p in recent_patients],
            "recent_invoices": all_recent_invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard stats: {str(e)}")

# Enhanced EHR Routes

# Encounter/Visit Management
@api_router.post("/encounters", response_model=Encounter)
async def create_encounter(encounter_data: EncounterCreate):
    # Generate encounter number
    count = await db.encounters.count_documents({})
    encounter_number = f"ENC-{count + 1:06d}"
    
    encounter = Encounter(
        encounter_number=encounter_number,
        **encounter_data.dict()
    )
    
    encounter_dict = jsonable_encoder(encounter)
    await db.encounters.insert_one(encounter_dict)
    return encounter

@api_router.get("/encounters", response_model=List[Encounter])
async def get_encounters():
    encounters = await db.encounters.find().sort("scheduled_date", -1).to_list(1000)
    return [Encounter(**encounter) for encounter in encounters]

@api_router.get("/encounters/patient/{patient_id}", response_model=List[Encounter])
async def get_patient_encounters(patient_id: str):
    encounters = await db.encounters.find({"patient_id": patient_id}, {"_id": 0}).sort("scheduled_date", -1).to_list(1000)
    return [Encounter(**encounter) for encounter in encounters]

@api_router.put("/encounters/{encounter_id}/status")
async def update_encounter_status(encounter_id: str, status: EncounterStatus):
    update_data = {"status": status, "updated_at": datetime.utcnow()}
    
    if status == EncounterStatus.IN_PROGRESS:
        update_data["actual_start"] = datetime.utcnow()
    elif status == EncounterStatus.COMPLETED:
        update_data["actual_end"] = datetime.utcnow()
    
    await db.encounters.update_one(
        {"id": encounter_id},
        {"$set": jsonable_encoder(update_data)}
    )
    return {"message": "Encounter status updated"}

# SOAP Notes
@api_router.post("/soap-notes", response_model=SOAPNote)
async def create_soap_note(soap_data: SOAPNoteCreate):
    soap_note = SOAPNote(**soap_data.dict())
    soap_dict = jsonable_encoder(soap_note)
    await db.soap_notes.insert_one(soap_dict)
    return soap_note

@api_router.post("/soap-notes/{soap_note_id}/complete")
async def complete_soap_note(soap_note_id: str, completion_data: Dict[str, Any], current_user: User = Depends(get_current_active_user)):
    """Complete SOAP note and trigger automatic workflows (receipt generation, inventory updates, etc.)"""
    
    # Get the SOAP note
    soap_note = await db.soap_notes.find_one({"id": soap_note_id}, {"_id": 0})
    if not soap_note:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    
    # Get patient information for invoice creation
    patient = await db.patients.find_one({"id": soap_note["patient_id"]}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get encounter information
    encounter = await db.encounters.find_one({"id": soap_note["encounter_id"]}, {"_id": 0})
    
    # Mark SOAP note as completed
    await db.soap_notes.update_one(
        {"id": soap_note_id},
        {"$set": {
            "status": "completed",
            "completed_at": jsonable_encoder(datetime.utcnow()),
            "completed_by": current_user.username,
            "updated_at": jsonable_encoder(datetime.utcnow())
        }}
    )
    
    # WORKFLOW 1: Automatic Receipt/Invoice Generation
    workflow_results = {}
    
    # Get billable services from completion data or use default encounter-based billing
    billable_services = completion_data.get("billable_services", [])
    
    # Default billing based on encounter type if no specific services provided
    if not billable_services and encounter:
        encounter_type = encounter.get("encounter_type", "consultation")
        if encounter_type == "annual_physical":
            billable_services = [
                {"description": "Annual Physical Examination", "code": "99395", "quantity": 1, "unit_price": 200.00},
                {"description": "Preventive Care Counseling", "code": "99401", "quantity": 1, "unit_price": 75.00}
            ]
        elif encounter_type == "consultation":
            billable_services = [
                {"description": "Office Visit - Consultation", "code": "99213", "quantity": 1, "unit_price": 150.00}
            ]
        elif encounter_type == "follow_up":
            billable_services = [
                {"description": "Follow-up Office Visit", "code": "99212", "quantity": 1, "unit_price": 100.00}
            ]
        else:
            billable_services = [
                {"description": "Medical Service", "code": "99211", "quantity": 1, "unit_price": 75.00}
            ]
    
    # Create invoice if billable services exist
    if billable_services:
        try:
            # Prepare invoice items
            invoice_items = []
            for service in billable_services:
                item_total = service["quantity"] * service["unit_price"]
                invoice_items.append({
                    "description": service["description"],
                    "quantity": service["quantity"],
                    "unit_price": service["unit_price"],
                    "total": item_total
                })
            
            # Calculate totals
            subtotal = sum(item["total"] for item in invoice_items)
            tax_rate = 0.08  # 8% default tax rate
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            # Generate invoice number
            count = await db.invoices.count_documents({})
            invoice_number = f"INV-{count + 1001:06d}"
            
            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                patient_id=soap_note["patient_id"],
                items=invoice_items,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total_amount,
                status="draft",
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                notes=f"Services rendered during encounter on {encounter.get('scheduled_date', datetime.utcnow().isoformat())}"
            )
            
            invoice_dict = jsonable_encoder(invoice)
            await db.invoices.insert_one(invoice_dict)
            
            workflow_results["invoice_created"] = {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "total_amount": invoice.total_amount,
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice from SOAP note: {str(e)}")
            workflow_results["invoice_created"] = {"status": "error", "message": str(e)}
    
    # WORKFLOW 2: Inventory Updates (if medications were prescribed/dispensed)
    prescribed_medications = completion_data.get("prescribed_medications", [])
    if prescribed_medications:
        try:
            inventory_updates = []
            for med in prescribed_medications:
                # Find inventory item by medication name/SKU
                inventory_item = await db.inventory.find_one({
                    "$or": [
                        {"name": {"$regex": med.get("medication_name", ""), "$options": "i"}},
                        {"sku": med.get("sku", "")}
                    ]
                }, {"_id": 0})
                
                if inventory_item:
                    # Update stock (subtract dispensed quantity)
                    dispensed_qty = med.get("quantity_dispensed", 1)
                    new_stock = inventory_item["current_stock"] - dispensed_qty
                    
                    await db.inventory.update_one(
                        {"id": inventory_item["id"]},
                        {"$set": {"current_stock": new_stock, "updated_at": jsonable_encoder(datetime.utcnow())}}
                    )
                    
                    # Create inventory transaction
                    transaction = InventoryTransaction(
                        item_id=inventory_item["id"],
                        transaction_type="out",
                        quantity=dispensed_qty,
                        reason="dispensed_to_patient",
                        notes=f"Dispensed to {patient['name'][0]['given'][0]} {patient['name'][0]['family']} - SOAP note {soap_note_id}",
                        created_by=current_user.username
                    )
                    
                    transaction_dict = jsonable_encoder(transaction)
                    await db.inventory_transactions.insert_one(transaction_dict)
                    
                    inventory_updates.append({
                        "item_id": inventory_item["id"],
                        "item_name": inventory_item["name"],
                        "previous_stock": inventory_item["current_stock"],
                        "new_stock": new_stock,
                        "dispensed_quantity": dispensed_qty
                    })
            
            workflow_results["inventory_updated"] = inventory_updates
            
        except Exception as e:
            logger.error(f"Error updating inventory from SOAP note: {str(e)}")
            workflow_results["inventory_updated"] = {"status": "error", "message": str(e)}
    
    # WORKFLOW 3: Staff Activity Tracking
    try:
        # Record staff activity
        activity_log = {
            "id": str(uuid.uuid4()),
            "staff_id": current_user.id if hasattr(current_user, 'id') else current_user.username,
            "staff_name": getattr(current_user, 'full_name', current_user.username),
            "activity_type": "soap_note_completion",
            "patient_id": soap_note["patient_id"],
            "encounter_id": soap_note["encounter_id"],
            "soap_note_id": soap_note_id,
            "activity_description": f"Completed SOAP note for {patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            "duration_minutes": completion_data.get("session_duration", 30),
            "timestamp": jsonable_encoder(datetime.utcnow())
        }
        
        await db.staff_activities.insert_one(activity_log)
        workflow_results["activity_logged"] = {
            "activity_id": activity_log["id"],
            "status": "logged"
        }
        
    except Exception as e:
        logger.error(f"Error logging staff activity: {str(e)}")
        workflow_results["activity_logged"] = {"status": "error", "message": str(e)}
    
    # Get updated SOAP note
    updated_soap_note = await db.soap_notes.find_one({"id": soap_note_id}, {"_id": 0})
    
    return {
        "message": "SOAP note completed successfully",
        "soap_note": SOAPNote(**updated_soap_note),
        "automated_workflows": workflow_results,
        "billable_services_processed": len(billable_services),
        "inventory_items_updated": len(prescribed_medications) if prescribed_medications else 0
    }

@api_router.get("/soap-notes/encounter/{encounter_id}", response_model=List[SOAPNote])
async def get_encounter_soap_notes(encounter_id: str):
    notes = await db.soap_notes.find({"encounter_id": encounter_id}).to_list(1000)
    return [SOAPNote(**note) for note in notes]

@api_router.get("/soap-notes/patient/{patient_id}", response_model=List[SOAPNote])
async def get_patient_soap_notes(patient_id: str):
    notes = await db.soap_notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [SOAPNote(**note) for note in notes]

@api_router.get("/soap-notes", response_model=List[SOAPNote])
async def get_all_soap_notes():
    """Get all SOAP notes"""
    notes = await db.soap_notes.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [SOAPNote(**note) for note in notes]

@api_router.get("/soap-notes/{soap_note_id}", response_model=SOAPNote)
async def get_soap_note(soap_note_id: str):
    """Get specific SOAP note by ID"""
    note = await db.soap_notes.find_one({"id": soap_note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    return SOAPNote(**note)

@api_router.put("/soap-notes/{soap_note_id}", response_model=SOAPNote)
async def update_soap_note(soap_note_id: str, soap_note_data: SOAPNoteCreate, current_user: User = Depends(get_current_active_user)):
    """Update existing SOAP note"""
    # Check if SOAP note exists
    existing_note = await db.soap_notes.find_one({"id": soap_note_id})
    if not existing_note:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    
    # Update the SOAP note while preserving created_at
    updated_note = SOAPNote(
        id=soap_note_id,
        created_at=existing_note["created_at"],  # Preserve original creation time
        updated_at=datetime.utcnow(),
        **soap_note_data.dict()
    )
    
    updated_note_dict = jsonable_encoder(updated_note)
    await db.soap_notes.replace_one({"id": soap_note_id}, updated_note_dict)
    return updated_note

@api_router.delete("/soap-notes/{soap_note_id}")
async def delete_soap_note(soap_note_id: str, current_user: User = Depends(get_current_active_user)):
    """Delete existing SOAP note"""
    # Check if SOAP note exists
    existing_note = await db.soap_notes.find_one({"id": soap_note_id})
    if not existing_note:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    
    # Delete the SOAP note
    result = await db.soap_notes.delete_one({"id": soap_note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    
    return {"message": "SOAP note deleted successfully", "id": soap_note_id}

# Vital Signs
@api_router.post("/vital-signs", response_model=VitalSigns)
async def create_vital_signs(vital_signs_data: VitalSignsCreate, current_user: User = Depends(get_current_active_user)):
    vital_signs = VitalSigns(
        id=str(uuid.uuid4()),
        recorded_by=current_user.username,
        **vital_signs_data.dict()
    )
    vital_signs_dict = jsonable_encoder(vital_signs)
    await db.vital_signs.insert_one(vital_signs_dict)
    return vital_signs

@api_router.get("/vital-signs", response_model=List[VitalSigns])
async def get_all_vital_signs(current_user: User = Depends(get_current_active_user)):
    """Get all vital signs across all patients"""
    vital_signs = await db.vital_signs.find().sort("recorded_at", -1).limit(100).to_list(100)
    return [VitalSigns(**vs) for vs in vital_signs]

@api_router.get("/vital-signs/patient/{patient_id}", response_model=List[VitalSigns])
async def get_patient_vital_signs(patient_id: str):
    vitals = await db.vital_signs.find({"patient_id": patient_id}, {"_id": 0}).sort("recorded_at", -1).to_list(1000)
    return [VitalSigns(**vital) for vital in vitals]

# Allergies
@api_router.post("/allergies", response_model=Allergy)
async def create_allergy(allergy_data: AllergyCreate, current_user: User = Depends(get_current_user)):
    # Validate patient_id
    pid = allergy_data.patient_id
    if not pid:
        raise HTTPException(status_code=400, detail="patient_id is required")
    patient = await db.patients.find_one({"id": pid}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid patient_id")

    # Build record with attribution
    allergy = Allergy(
        patient_id=pid,
        allergen=allergy_data.allergen,
        reaction=allergy_data.reaction,
        severity=allergy_data.severity,
        onset_date=allergy_data.onset_date,
        notes=allergy_data.notes,
        created_by=current_user.username,
    )

    await db.allergies.insert_one(jsonable_encoder(allergy))

    await create_audit_event(
        event_type="create",
        resource_type="allergy",
        user_id=current_user.id,
        user_name=current_user.username,
        resource_id=allergy.id,
        action_details={"patient_id": pid, "allergen": allergy.allergen, "severity": allergy.severity},
        phi_accessed=True,
        success=True,
    )

    return allergy

@api_router.get("/allergies/patient/{patient_id}", response_model=List[Allergy])
async def get_patient_allergies(patient_id: str):
    allergies = await db.allergies.find({"patient_id": patient_id}).to_list(1000)
    return [Allergy(**allergy) for allergy in allergies]

# Medications
@api_router.post("/medications", response_model=Medication)
async def create_medication(medication_data: MedicationCreate):
    medication = Medication(**medication_data.dict())
    medication_dict = jsonable_encoder(medication)
    await db.medications.insert_one(medication_dict)
    return medication

@api_router.get("/medications/patient/{patient_id}", response_model=List[Medication])
async def get_patient_medications(patient_id: str):
    medications = await db.medications.find({"patient_id": patient_id}, {"_id": 0}).to_list(1000)
    return [Medication(**medication) for medication in medications]

@api_router.put("/medications/{medication_id}/status")
async def update_medication_status(medication_id: str, status: MedicationStatus):
    await db.medications.update_one(
        {"id": medication_id},
        {"$set": {"status": status, "updated_at": jsonable_encoder(datetime.utcnow())}}
    )
    return {"message": "Medication status updated"}

# Medical History
@api_router.post("/medical-history", response_model=MedicalHistory)
async def create_medical_history(history_data: MedicalHistoryCreate):
    history = MedicalHistory(**history_data.dict())
    history_dict = jsonable_encoder(history)
    await db.medical_history.insert_one(history_dict)
    return history

@api_router.get("/medical-history/patient/{patient_id}", response_model=List[MedicalHistory])
async def get_patient_medical_history(patient_id: str):
    history = await db.medical_history.find({"patient_id": patient_id}).to_list(1000)
    return [MedicalHistory(**item) for item in history]

# Diagnoses
@api_router.post("/diagnoses", response_model=Diagnosis)
async def create_diagnosis(diagnosis_data: DiagnosisCreate):
    diagnosis = Diagnosis(**diagnosis_data.dict())
    diagnosis_dict = jsonable_encoder(diagnosis)
    await db.diagnoses.insert_one(diagnosis_dict)
    return diagnosis

@api_router.get("/diagnoses/encounter/{encounter_id}", response_model=List[Diagnosis])
async def get_encounter_diagnoses(encounter_id: str):
    diagnoses = await db.diagnoses.find({"encounter_id": encounter_id}).to_list(1000)
    return [Diagnosis(**diagnosis) for diagnosis in diagnoses]

@api_router.get("/diagnoses/patient/{patient_id}", response_model=List[Diagnosis])
async def get_patient_diagnoses(patient_id: str):
    diagnoses = await db.diagnoses.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Diagnosis(**diagnosis) for diagnosis in diagnoses]

# Procedures
@api_router.post("/procedures", response_model=Procedure)
async def create_procedure(procedure_data: ProcedureCreate):
    procedure = Procedure(**procedure_data.dict())
    procedure_dict = jsonable_encoder(procedure)
    await db.procedures.insert_one(procedure_dict)
    return procedure

@api_router.get("/procedures/encounter/{encounter_id}", response_model=List[Procedure])
async def get_encounter_procedures(encounter_id: str):
    procedures = await db.procedures.find({"encounter_id": encounter_id}).to_list(1000)
    return [Procedure(**procedure) for procedure in procedures]

@api_router.get("/procedures/patient/{patient_id}", response_model=List[Procedure])
async def get_patient_procedures(patient_id: str):
    procedures = await db.procedures.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Procedure(**procedure) for procedure in procedures]

# Comprehensive Patient Summary
@api_router.get("/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    # Get patient basic info
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get all related medical data
    encounters = await db.encounters.find({"patient_id": patient_id}, {"_id": 0}).sort("scheduled_date", -1).limit(10).to_list(10)
    allergies = await db.allergies.find({"patient_id": patient_id}).to_list(100)
    medications = await db.medications.find({"patient_id": patient_id, "status": "active"}).to_list(100)
    medical_history = await db.medical_history.find({"patient_id": patient_id}).to_list(100)
    recent_vitals = await db.vital_signs.find({"patient_id": patient_id}, {"_id": 0}).sort("recorded_at", -1).limit(1).to_list(1)
    recent_soap_notes = await db.soap_notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    documents = await db.patient_documents.find({"patient_id": patient_id}, {"_id": 0}).sort("upload_date", -1).to_list(100)
    
    return {
        "patient": Patient(**patient),
        "recent_encounters": [Encounter(**e) for e in encounters],
        "allergies": [Allergy(**a) for a in allergies],
        "active_medications": [Medication(**m) for m in medications],
        "medical_history": [MedicalHistory(**h) for h in medical_history],
        "recent_vitals": [VitalSigns(**v) for v in recent_vitals],
        "recent_soap_notes": [SOAPNote(**s) for s in recent_soap_notes],
        "documents": [PatientDocument(**d) for d in documents]
    }

# Enhanced Features - Document Management
@api_router.post("/patients/{patient_id}/documents", response_model=PatientDocument)
async def upload_patient_document(patient_id: str, document: PatientDocumentCreate):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create document record
        doc = PatientDocument(**document.dict())
        doc_dict = jsonable_encoder(doc)
        await db.patient_documents.insert_one(doc_dict)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@api_router.get("/patients/{patient_id}/documents", response_model=List[PatientDocument])
async def get_patient_documents(patient_id: str):
    documents = await db.patient_documents.find({"patient_id": patient_id}, {"_id": 0}).sort("upload_date", -1).to_list(1000)
    return [PatientDocument(**doc) for doc in documents]

@api_router.delete("/documents/{document_id}")
async def delete_patient_document(document_id: str):
    result = await db.patient_documents.delete_one({"id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

# Enhanced SOAP Notes with Plan Items and Auto-Billing
@api_router.post("/enhanced-soap-notes", response_model=EnhancedSOAPNote)
async def create_enhanced_soap_note(soap_data: EnhancedSOAPNoteCreate):
    try:
        soap_note = EnhancedSOAPNote(**soap_data.dict())
        soap_dict = jsonable_encoder(soap_note)
        await db.enhanced_soap_notes.insert_one(soap_dict)
        
        # Auto-generate invoice if plan items are approved
        approved_items = [item for item in soap_note.plan_items if item.approved_by_patient and item.unit_price > 0]
        if approved_items:
            await auto_generate_invoice_from_plan(soap_note.patient_id, soap_note.encounter_id, approved_items)
        
        return soap_note
    except Exception as e:
        logger.error(f"Error creating enhanced SOAP note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating SOAP note: {str(e)}")

@api_router.get("/enhanced-soap-notes/encounter/{encounter_id}", response_model=List[EnhancedSOAPNote])
async def get_enhanced_encounter_soap_notes(encounter_id: str):
    notes = await db.enhanced_soap_notes.find({"encounter_id": encounter_id}).to_list(1000)
    return [EnhancedSOAPNote(**note) for note in notes]

# Enhanced Invoice Management with Inventory Integration
@api_router.post("/enhanced-invoices", response_model=EnhancedInvoice)
async def create_enhanced_invoice(invoice_data: EnhancedInvoiceCreate):
    try:
        # Generate invoice number
        count = await db.enhanced_invoices.count_documents({})
        invoice_number = f"INV-{count + 1:06d}"
        
        # Calculate totals
        subtotal = sum(item.total for item in invoice_data.items)
        tax_amount = subtotal * invoice_data.tax_rate
        total_amount = subtotal + tax_amount
        
        # Set due date
        due_date = None
        if invoice_data.due_days:
            from datetime import timedelta
            due_date = date.today() + timedelta(days=invoice_data.due_days)
        
        invoice = EnhancedInvoice(
            invoice_number=invoice_number,
            patient_id=invoice_data.patient_id,
            encounter_id=invoice_data.encounter_id,
            items=invoice_data.items,
            subtotal=subtotal,
            tax_rate=invoice_data.tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            due_date=due_date,
            notes=invoice_data.notes,
            auto_generated=invoice_data.auto_generated
        )
        
        invoice_dict = jsonable_encoder(invoice)
        await db.enhanced_invoices.insert_one(invoice_dict)
        return invoice
    except Exception as e:
        logger.error(f"Error creating enhanced invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")

@api_router.put("/enhanced-invoices/{invoice_id}/status")
async def update_enhanced_invoice_status(invoice_id: str, status: InvoiceStatus):
    try:
        # Get the invoice
        invoice = await db.enhanced_invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        
        # If invoice is being marked as paid, deduct inventory items
        if status == InvoiceStatus.PAID and invoice["status"] != "paid":
            update_data["paid_date"] = date.today()
            await process_inventory_deductions(invoice["items"])
        
        await db.enhanced_invoices.update_one(
            {"id": invoice_id},
            {"$set": jsonable_encoder(update_data)}
        )
        
        return {"message": "Invoice status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating invoice status: {str(e)}")

@api_router.get("/enhanced-invoices", response_model=List[EnhancedInvoice])
async def get_enhanced_invoices():
    invoices = await db.enhanced_invoices.find().sort("created_at", -1).to_list(1000)
    return [EnhancedInvoice(**invoice) for invoice in invoices]

@api_router.get("/enhanced-invoices/patient/{patient_id}", response_model=List[EnhancedInvoice])
async def get_patient_enhanced_invoices(patient_id: str):
    invoices = await db.enhanced_invoices.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [EnhancedInvoice(**invoice) for invoice in invoices]

# Helper Functions for Enhanced Features
async def auto_generate_invoice_from_plan(patient_id: str, encounter_id: str, plan_items: List[PlanItem]):
    """Auto-generate invoice from approved SOAP note plan items"""
    try:
        invoice_items = []
        for item in plan_items:
            invoice_item = EnhancedInvoiceItem(
                description=f"{item.item_type.title()}: {item.description}",
                quantity=item.quantity,
                unit_price=item.unit_price,
                total=item.quantity * item.unit_price,
                inventory_item_id=item.inventory_item_id,
                service_type=item.item_type
            )
            invoice_items.append(invoice_item)
        
        # Create invoice
        invoice_data = EnhancedInvoiceCreate(
            patient_id=patient_id,
            encounter_id=encounter_id,
            items=invoice_items,
            tax_rate=0.08,  # Default tax rate
            due_days=30,
            notes="Auto-generated from medical plan",
            auto_generated=True
        )
        
        await create_enhanced_invoice(invoice_data)
    except Exception as e:
        logger.error(f"Error auto-generating invoice: {str(e)}")

async def process_inventory_deductions(invoice_items: List[dict]):
    """Process inventory deductions when invoice is paid"""
    try:
        for item in invoice_items:
            if item.get("inventory_item_id") and item.get("service_type") in ["product", "injectable"]:
                # Find inventory item
                inventory_item = await db.inventory.find_one({"id": item["inventory_item_id"]}, {"_id": 0})
                if inventory_item:
                    # Create inventory transaction (deduction)
                    transaction = InventoryTransaction(
                        item_id=item["inventory_item_id"],
                        transaction_type="out",
                        quantity=item["quantity"],
                        reference_id=item.get("invoice_id"),
                        notes=f"Auto-deducted from paid invoice: {item['description']}",
                        created_by="System"
                    )
                    
                    # Update inventory stock
                    new_stock = inventory_item["current_stock"] - item["quantity"]
                    await db.inventory.update_one(
                        {"id": item["inventory_item_id"]},
                        {"$set": {"current_stock": max(0, new_stock), "updated_at": jsonable_encoder(datetime.utcnow())}}
                    )
                    
                    # Record transaction
                    transaction_dict = jsonable_encoder(transaction)
                    await db.inventory_transactions.insert_one(transaction_dict)
    except Exception as e:
        logger.error(f"Error processing inventory deductions: {str(e)}")

# Get Inventory Items for Billing/Plan Integration
@api_router.get("/inventory/billable", response_model=List[InventoryItem])
async def get_billable_inventory_items():
    """Get inventory items that can be billed (injectables, medical supplies, etc.)"""
    items = await db.inventory.find({
        "category": {"$in": ["injectable", "medication", "medical_supply", "lab_supply"]},
        "current_stock": {"$gt": 0}
    }).to_list(1000)
    return [InventoryItem(**item) for item in items]

# eRx API Endpoints

@api_router.get("/medications", response_model=List[FHIRMedication])
async def get_medications(
    search: Optional[str] = None,
    drug_class: Optional[DrugClass] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Get medications with optional search and filtering"""
    try:
        query = {}
        
        if search:
            query["$or"] = [
                {"generic_name": {"$regex": search, "$options": "i"}},
                {"brand_names": {"$regex": search, "$options": "i"}}
            ]
        
        if drug_class:
            query["drug_class"] = drug_class
        
        medications = await db.fhir_medications.find(query, {"_id": 0}).limit(limit).to_list(limit)
        return medications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving medications: {str(e)}")

@api_router.get("/medications/{medication_id}", response_model=FHIRMedication)
async def get_medication(
    medication_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific medication details"""
    try:
        medication = await db.fhir_medications.find_one({"id": medication_id}, {"_id": 0})
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        return medication
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving medication: {str(e)}")

@api_router.post("/prescriptions", response_model=MedicationRequest)
async def create_prescription(prescription_data: dict, current_user: User = Depends(get_current_active_user)):
    try:
        # Validate patient exists
        patient = await db.patients.find_one({"id": prescription_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get medication details if medication_id provided
        medication_display = prescription_data.get("medication_display", "Unknown Medication")
        if prescription_data.get("medication_id"):
            medication = await db.medications.find_one({"id": prescription_data["medication_id"]}, {"_id": 0})
            if medication:
                medication_display = medication.get("generic_name", medication.get("brand_name", "Unknown Medication"))
        
        # Prepare patient display name
        patient_name = "Unknown Patient"
        if patient.get("name") and len(patient["name"]) > 0:
            name_obj = patient["name"][0]
            given_names = name_obj.get("given", [])
            family_name = name_obj.get("family", "")
            if given_names and family_name:
                patient_name = f"{' '.join(given_names)} {family_name}"
            elif family_name:
                patient_name = family_name
            elif given_names:
                patient_name = ' '.join(given_names)
        
        # Create prescription object with required fields
        prescription_dict = {
            "id": str(uuid.uuid4()),
            "resource_type": "MedicationRequest",
            "status": prescription_data.get("status", "active"),
            "intent": prescription_data.get("intent", "order"),
            "priority": prescription_data.get("priority", "routine"),
            
            # Medication Information
            "medication_id": prescription_data.get("medication_id", "unknown"),
            "medication_display": medication_display,
            
            # Patient Information
            "patient_id": prescription_data["patient_id"],
            "patient_display": patient_name,
            
            # Encounter Context
            "encounter_id": prescription_data.get("encounter_id"),
            
            # Prescriber Information
            "prescriber_id": current_user.id if hasattr(current_user, 'id') else 'unknown',
            "prescriber_name": getattr(current_user, 'first_name', '') + ' ' + getattr(current_user, 'last_name', ''),
            "prescriber_npi": prescription_data.get("prescriber_npi"),
            "prescriber_dea": prescription_data.get("prescriber_dea"),
            
            # Dosage and Instructions
            "dosage_instruction": prescription_data.get("dosage_instruction", []),
            "quantity": prescription_data.get("quantity"),
            "supply_duration": prescription_data.get("supply_duration"),
            "refills_allowed": prescription_data.get("refills_allowed", 0),
            
            # Additional fields
            "reason_code": prescription_data.get("reason_code", []),
            "reason_reference": prescription_data.get("reason_reference", []),
            "note": prescription_data.get("note", []),
            
            # Timestamps
            "authored_on": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            
            # Audit Trail
            "created_by": current_user.id if hasattr(current_user, 'id') else current_user.username
        }
        
        # Create MedicationRequest object for validation
        prescription = MedicationRequest(**prescription_dict)
        
        # Store in database
        prescription_dict = jsonable_encoder(prescription)
        await db.prescriptions.insert_one(prescription_dict)
        
        return prescription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating prescription: {str(e)}")

@api_router.get("/prescriptions", response_model=List[MedicationRequest])
async def get_all_prescriptions(current_user: User = Depends(get_current_active_user)):
    """Get all prescriptions across all patients"""
    try:
        prescriptions = await db.prescriptions.find().sort("created_at", -1).limit(100).to_list(100)
        return [MedicationRequest(**prescription) for prescription in prescriptions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescriptions: {str(e)}")

@api_router.get("/patients/{patient_id}/prescriptions", response_model=List[MedicationRequest])
async def get_patient_prescriptions(
    patient_id: str,
    status: Optional[PrescriptionStatus] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get all prescriptions for a patient"""
    try:
        query = {"patient_id": patient_id}
        if status:
            query["status"] = status
        
        prescriptions = await db.prescriptions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        # Log access for HIPAA compliance
        await create_prescription_audit_log(
            None,
            patient_id,
            "viewed",
            current_user.id,
            current_user.username,
            {"prescriptions_accessed": len(prescriptions)}
        )
        
        return prescriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescriptions: {str(e)}")

@api_router.put("/prescriptions/{prescription_id}/status")
async def update_prescription_status(
    prescription_id: str,
    status: PrescriptionStatus,
    current_user: User = Depends(get_current_active_user)
):
    """Update prescription status"""
    try:
        prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        old_status = prescription["status"]
        
        # Update prescription
        update_result = await db.prescriptions.update_one(
            {"id": prescription_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Create audit log
        await create_prescription_audit_log(
            prescription_id,
            prescription["patient_id"],
            "modified",
            current_user.id,
            current_user.username,
            {
                "status_changed": {
                    "from": old_status,
                    "to": status
                }
            }
        )
        
        return {"message": "Prescription status updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prescription: {str(e)}")

@api_router.get("/prescriptions/{prescription_id}/interactions")
async def check_prescription_interactions(
    prescription_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Check for drug interactions for a specific prescription"""
    try:
        prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        interactions = await check_drug_interactions(
            prescription["patient_id"], 
            prescription["medication_id"]
        )
        
        return {"interactions": interactions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking interactions: {str(e)}")

@api_router.get("/drug-interactions")
async def search_drug_interactions(
    drug1_id: str,
    drug2_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Search for interactions between two specific drugs"""
    try:
        interaction = await db.drug_interactions.find_one({
            "$or": [
                {"drug1_id": drug1_id, "drug2_id": drug2_id},
                {"drug1_id": drug2_id, "drug2_id": drug1_id}
            ]
        })
        
        return {"interaction": interaction}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking drug interaction: {str(e)}")

# Helper Functions

async def check_drug_allergies(patient_id: str, medication_id: str) -> List[Dict[str, Any]]:
    """Check for drug allergies"""
    try:
        # Get patient allergies
        allergies = await db.allergies.find({"patient_id": patient_id}).to_list(100)
        
        # Get medication details
        medication = await db.fhir_medications.find_one({"id": medication_id}, {"_id": 0})
        
        alerts = []
        for allergy in allergies:
            # Check direct medication match
            if allergy["allergen"].lower() in medication["generic_name"].lower():
                alerts.append({
                    "type": "allergy",
                    "severity": allergy["severity"],
                    "message": f"Patient is allergic to {allergy['allergen']}",
                    "reaction": allergy["reaction"]
                })
            
            # Check drug class allergies
            if allergy["allergen"].lower() in medication.get("drug_class", "").lower():
                alerts.append({
                    "type": "class_allergy",
                    "severity": allergy["severity"],
                    "message": f"Patient is allergic to {medication['drug_class']} class drugs",
                    "reaction": allergy["reaction"]
                })
        
        return alerts
        
    except Exception as e:
        print(f"Error checking allergies: {str(e)}")
        return []

async def check_drug_interactions(patient_id: str, new_medication_id: str) -> List[Dict[str, Any]]:
    """Check for drug-drug interactions"""
    try:
        # Get patient's current active prescriptions
        current_prescriptions = await db.prescriptions.find({
            "patient_id": patient_id,
            "status": {"$in": ["active", "draft"]}
        }).to_list(100)
        
        alerts = []
        for prescription in current_prescriptions:
            if prescription["medication_id"] != new_medication_id:
                # Check for interaction
                interaction = await db.drug_interactions.find_one({
                    "$or": [
                        {"drug1_id": prescription["medication_id"], "drug2_id": new_medication_id},
                        {"drug1_id": new_medication_id, "drug2_id": prescription["medication_id"]}
                    ]
                })
                
                if interaction:
                    alerts.append({
                        "type": "drug_interaction",
                        "severity": interaction["severity"],
                        "message": f"Interaction with {prescription['medication_display']}",
                        "description": interaction["description"],
                        "clinical_consequence": interaction["clinical_consequence"],
                        "management": interaction["management_recommendation"]
                    })
        
        return alerts
        
    except Exception as e:
        print(f"Error checking interactions: {str(e)}")
        return []

async def create_prescription_audit_log(
    prescription_id: Optional[str],
    patient_id: str,
    action: str,
    performed_by: str,
    performed_by_name: str,
    action_details: Dict[str, Any]
):
    """Create audit log entry for HIPAA compliance"""
    try:
        audit_log = PrescriptionAuditLog(
            prescription_id=prescription_id or "N/A",
            patient_id=patient_id,
            action=action,
            performed_by=performed_by,
            performed_by_name=performed_by_name,
            action_details=action_details
        )
        
        audit_dict = jsonable_encoder(audit_log)
        await db.prescription_audit_logs.insert_one(audit_dict)
        
    except Exception as e:
        print(f"Error creating audit log: {str(e)}")

def get_frequency_period(frequency: str) -> int:
    """Convert frequency to period for FHIR timing"""
    frequency_map = {
        "QD": 1, "DAILY": 1, "ONCE_DAILY": 1,
        "BID": 2, "TWICE_DAILY": 2,
        "TID": 3, "THREE_TIMES_DAILY": 3,
        "QID": 4, "FOUR_TIMES_DAILY": 4,
        "Q6H": 4, "Q8H": 3, "Q12H": 2
    }
    return frequency_map.get(frequency.upper(), 1)

@api_router.post("/init-erx-data")
async def initialize_erx_data(current_user: User = Depends(get_current_active_user)):
    """Initialize sample medication database and drug interactions"""
    try:
        # Check if FHIR medications already exist
        existing_meds = await db.fhir_medications.count_documents({})
        if existing_meds > 0:
            return {"message": "eRx data already initialized", "medications_count": existing_meds}
        
        # Sample medications with FHIR compliance
        medications = [
            {
                "id": str(uuid.uuid4()),
                "resource_type": "Medication",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "617993",
                        "display": "Lisinopril 10 MG Oral Tablet"
                    }]
                },
                "generic_name": "Lisinopril",
                "brand_names": ["Prinivil", "Zestril"],
                "strength": "10mg",
                "dosage_forms": ["tablet"],
                "route_of_administration": ["oral"],
                "drug_class": "antihypertensive",
                "contraindications": ["pregnancy", "angioedema", "bilateral renal artery stenosis"],
                "warnings": ["hyperkalemia", "renal impairment", "hypotension"],
                "pregnancy_category": "D",
                "standard_dosing": {
                    "adult": "Initial: 10mg once daily, Maintenance: 20-40mg once daily",
                    "elderly": "Initial: 2.5-5mg once daily"
                },
                "max_daily_dose": "80mg",
                "rxnorm_code": "617993",
                "ndc_codes": ["0378-1010-01", "0378-1015-01"]
            },
            {
                "id": str(uuid.uuid4()),
                "resource_type": "Medication",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "860975",
                        "display": "Metformin 500 MG Oral Tablet"
                    }]
                },
                "generic_name": "Metformin",
                "brand_names": ["Glucophage", "Fortamet"],
                "strength": "500mg",
                "dosage_forms": ["tablet", "extended-release tablet"],
                "route_of_administration": ["oral"],
                "drug_class": "antidiabetic",
                "contraindications": ["severe renal impairment", "acute metabolic acidosis"],
                "warnings": ["lactic acidosis", "renal impairment", "contrast dye procedures"],
                "pregnancy_category": "B",
                "standard_dosing": {
                    "adult": "Initial: 500mg twice daily, Maintenance: 500-1000mg twice daily",
                    "max": "2550mg daily"
                },
                "max_daily_dose": "2550mg",
                "rxnorm_code": "860975"
            },
            {
                "id": str(uuid.uuid4()),
                "resource_type": "Medication",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "308136",
                        "display": "Warfarin 5 MG Oral Tablet"
                    }]
                },
                "generic_name": "Warfarin",
                "brand_names": ["Coumadin", "Jantoven"],
                "strength": "5mg",
                "dosage_forms": ["tablet"],
                "route_of_administration": ["oral"],
                "drug_class": "anticoagulant",
                "contraindications": ["active bleeding", "pregnancy", "severe liver disease"],
                "warnings": ["bleeding risk", "INR monitoring required", "multiple drug interactions"],
                "pregnancy_category": "X",
                "standard_dosing": {
                    "adult": "Initial: 2-5mg daily, adjusted based on INR",
                    "elderly": "Initial: 1-2mg daily"
                },
                "max_daily_dose": "10mg typically",
                "rxnorm_code": "308136"
            },
            {
                "id": str(uuid.uuid4()),
                "resource_type": "Medication",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "197696",
                        "display": "Amoxicillin 500 MG Oral Capsule"
                    }]
                },
                "generic_name": "Amoxicillin",
                "brand_names": ["Amoxil", "Moxatag"],
                "strength": "500mg",
                "dosage_forms": ["capsule", "tablet", "suspension"],
                "route_of_administration": ["oral"],
                "drug_class": "antibiotic",
                "contraindications": ["penicillin allergy"],
                "warnings": ["allergic reactions", "C. diff colitis", "renal dosing adjustment"],
                "pregnancy_category": "B",
                "standard_dosing": {
                    "adult": "250-500mg every 8 hours or 500-875mg every 12 hours",
                    "pediatric": "20-40mg/kg/day divided every 8 hours"
                },
                "max_daily_dose": "3000mg",
                "rxnorm_code": "197696"
            },
            {
                "id": str(uuid.uuid4()),
                "resource_type": "Medication",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "152923",
                        "display": "Ibuprofen 600 MG Oral Tablet"
                    }]
                },
                "generic_name": "Ibuprofen",
                "brand_names": ["Advil", "Motrin"],
                "strength": "600mg",
                "dosage_forms": ["tablet", "capsule", "suspension"],
                "route_of_administration": ["oral"],
                "drug_class": "analgesic",
                "contraindications": ["aspirin allergy", "severe heart failure", "active GI bleeding"],
                "warnings": ["GI bleeding", "cardiovascular risk", "renal impairment"],
                "pregnancy_category": "C",
                "standard_dosing": {
                    "adult": "400-800mg every 6-8 hours",
                    "max_daily": "3200mg"
                },
                "max_daily_dose": "3200mg",
                "rxnorm_code": "152923"
            }
        ]
        
        # Insert medications
        await db.fhir_medications.insert_many(medications)
        
        # Create drug interactions
        med_lookup = {med["generic_name"]: med["id"] for med in medications}
        
        interactions = [
            {
                "id": str(uuid.uuid4()),
                "drug1_id": med_lookup["Warfarin"],
                "drug1_name": "Warfarin",
                "drug2_id": med_lookup["Ibuprofen"],
                "drug2_name": "Ibuprofen",
                "severity": "major",
                "description": "NSAIDs may increase the risk of bleeding when used with warfarin",
                "clinical_consequence": "Increased risk of serious bleeding, including GI bleeding",
                "management_recommendation": "Monitor INR closely. Consider alternative analgesic. If NSAID necessary, use lowest effective dose for shortest duration.",
                "evidence_level": "established",
                "onset": "delayed",
                "documentation": "excellent"
            },
            {
                "id": str(uuid.uuid4()),
                "drug1_id": med_lookup["Lisinopril"],
                "drug1_name": "Lisinopril",
                "drug2_id": med_lookup["Ibuprofen"],
                "drug2_name": "Ibuprofen",
                "severity": "moderate",
                "description": "NSAIDs may reduce the antihypertensive effect of ACE inhibitors",
                "clinical_consequence": "Reduced blood pressure control, potential renal function impairment",
                "management_recommendation": "Monitor blood pressure and renal function. Consider alternative analgesic.",
                "evidence_level": "established",
                "onset": "delayed",
                "documentation": "good"
            },
            {
                "id": str(uuid.uuid4()),
                "drug1_id": med_lookup["Metformin"],
                "drug1_name": "Metformin",
                "drug2_id": med_lookup["Warfarin"],
                "drug2_name": "Warfarin",
                "severity": "minor",
                "description": "Metformin may potentiate the anticoagulant effect of warfarin",
                "clinical_consequence": "Slight increase in anticoagulant effect",
                "management_recommendation": "Monitor INR when starting or stopping metformin",
                "evidence_level": "probable",
                "onset": "delayed",
                "documentation": "fair"
            }
        ]
        
        # Insert interactions
        await db.drug_interactions.insert_many(interactions)
        
        return {
            "message": "eRx data initialized successfully",
            "medications_added": len(medications),
            "interactions_added": len(interactions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing eRx data: {str(e)}")
@api_router.post("/comprehensive-medications/init")
async def initialize_comprehensive_medication_database(current_user: User = Depends(get_current_active_user)):
    """Initialize comprehensive medication database for offline-first operation"""
    try:
        # Check if comprehensive medications already exist
        existing_meds = await db.comprehensive_medications.count_documents({})
        if existing_meds > 0:
            return {"message": "Comprehensive medication database already initialized", "medications_count": existing_meds}
        
        # Comprehensive medication database for primary care
        comprehensive_medications = [
            # Cardiovascular Medications
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Lisinopril",
                "brand_names": ["Prinivil", "Zestril"],
                "drug_class": "ACE Inhibitor",
                "strength": ["2.5mg", "5mg", "10mg", "20mg", "40mg"],
                "dosage_forms": ["tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["314076", "617993", "206765"],
                "search_terms": ["ace inhibitor", "blood pressure", "hypertension", "heart"],
                "indications": ["Hypertension", "Heart failure", "Post-MI", "Diabetic nephropathy"],
                "contraindications": ["Pregnancy", "Bilateral renal artery stenosis", "Angioedema"],
                "common_side_effects": ["Dry cough", "Hyperkalemia", "Hypotension", "Angioedema"],
                "interactions": ["NSAIDs", "Potassium supplements", "ARBs"],
                "standard_dosing": {
                    "hypertension": "Initial: 10mg daily, Target: 20-40mg daily",
                    "heart_failure": "Initial: 2.5-5mg daily, Target: 20-35mg daily"
                },
                "pregnancy_category": "D",
                "monitoring": ["Blood pressure", "Serum creatinine", "Potassium"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Amlodipine",
                "brand_names": ["Norvasc"],
                "drug_class": "Calcium Channel Blocker",
                "strength": ["2.5mg", "5mg", "10mg"],
                "dosage_forms": ["tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["17767", "197361"],
                "search_terms": ["calcium channel blocker", "blood pressure", "hypertension", "angina"],
                "indications": ["Hypertension", "Coronary artery disease", "Angina"],
                "contraindications": ["Severe aortic stenosis"],
                "common_side_effects": ["Peripheral edema", "Dizziness", "Flushing", "Fatigue"],
                "interactions": ["CYP3A4 inhibitors", "Simvastatin"],
                "standard_dosing": {
                    "hypertension": "Initial: 5mg daily, Max: 10mg daily",
                    "angina": "5-10mg daily"
                },
                "pregnancy_category": "C",
                "monitoring": ["Blood pressure", "Ankle swelling"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Metoprolol",
                "brand_names": ["Lopressor", "Toprol-XL"],
                "drug_class": "Beta Blocker",
                "strength": ["25mg", "50mg", "100mg", "200mg"],
                "dosage_forms": ["tablet", "extended-release tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["6918", "866511"],
                "search_terms": ["beta blocker", "blood pressure", "heart rate", "angina"],
                "indications": ["Hypertension", "Angina", "Heart failure", "Post-MI"],
                "contraindications": ["Severe bradycardia", "Heart block", "Cardiogenic shock"],
                "common_side_effects": ["Fatigue", "Dizziness", "Bradycardia", "Cold extremities"],
                "interactions": ["Calcium channel blockers", "Insulin", "Clonidine"],
                "standard_dosing": {
                    "hypertension": "Initial: 25-50mg BID, Max: 200mg BID",
                    "heart_failure": "Initial: 12.5mg BID, Target: 200mg BID"
                },
                "pregnancy_category": "C",
                "monitoring": ["Heart rate", "Blood pressure", "Signs of HF"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Atorvastatin",
                "brand_names": ["Lipitor"],
                "drug_class": "Statin",
                "strength": ["10mg", "20mg", "40mg", "80mg"],
                "dosage_forms": ["tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["83367", "617318"],
                "search_terms": ["statin", "cholesterol", "lipid", "cardiovascular"],
                "indications": ["Hyperlipidemia", "Cardiovascular disease prevention"],
                "contraindications": ["Active liver disease", "Pregnancy", "Breastfeeding"],
                "common_side_effects": ["Myalgia", "Elevated liver enzymes", "Headache"],
                "interactions": ["CYP3A4 inhibitors", "Warfarin", "Digoxin"],
                "standard_dosing": {
                    "hyperlipidemia": "Initial: 10-20mg daily, Max: 80mg daily"
                },
                "pregnancy_category": "X",
                "monitoring": ["Lipid panel", "Liver function tests", "CK if symptoms"]
            },
            
            # Diabetes Medications
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Metformin",
                "brand_names": ["Glucophage", "Fortamet", "Glumetza"],
                "drug_class": "Biguanide",
                "strength": ["500mg", "850mg", "1000mg"],
                "dosage_forms": ["tablet", "extended-release tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["6809", "860975"],
                "search_terms": ["diabetes", "blood sugar", "glucose", "metformin"],
                "indications": ["Type 2 diabetes mellitus", "Prediabetes", "PCOS"],
                "contraindications": ["Severe renal impairment", "Metabolic acidosis", "Heart failure"],
                "common_side_effects": ["GI upset", "Diarrhea", "Metallic taste", "B12 deficiency"],
                "interactions": ["Contrast agents", "Alcohol", "Carbonic anhydrase inhibitors"],
                "standard_dosing": {
                    "diabetes": "Initial: 500mg BID, Max: 2550mg daily"
                },
                "pregnancy_category": "B",
                "monitoring": ["HbA1c", "Renal function", "B12 levels"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Glipizide",
                "brand_names": ["Glucotrol"],
                "drug_class": "Sulfonylurea",
                "strength": ["5mg", "10mg"],
                "dosage_forms": ["tablet", "extended-release tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["4821", "310534"],
                "search_terms": ["diabetes", "blood sugar", "sulfonylurea", "insulin"],
                "indications": ["Type 2 diabetes mellitus"],
                "contraindications": ["Type 1 diabetes", "Diabetic ketoacidosis", "Severe renal/hepatic impairment"],
                "common_side_effects": ["Hypoglycemia", "Weight gain", "GI upset"],
                "interactions": ["Beta blockers", "Warfarin", "NSAIDs"],
                "standard_dosing": {
                    "diabetes": "Initial: 5mg daily, Max: 20mg daily"
                },
                "pregnancy_category": "C",
                "monitoring": ["Blood glucose", "HbA1c", "Signs of hypoglycemia"]
            },
            
            # Antibiotics
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Amoxicillin",
                "brand_names": ["Amoxil"],
                "drug_class": "Penicillin Antibiotic",
                "strength": ["250mg", "500mg", "875mg"],
                "dosage_forms": ["capsule", "tablet", "suspension"],
                "route": ["oral"],
                "rxnorm_codes": ["723", "308192"],
                "search_terms": ["antibiotic", "infection", "penicillin", "bacterial"],
                "indications": ["Bacterial infections", "Strep throat", "UTI", "Pneumonia"],
                "contraindications": ["Penicillin allergy"],
                "common_side_effects": ["Diarrhea", "Nausea", "Rash", "Yeast infections"],
                "interactions": ["Oral contraceptives", "Warfarin", "Methotrexate"],
                "standard_dosing": {
                    "general_infection": "500mg TID or 875mg BID for 7-10 days",
                    "strep_throat": "500mg BID for 10 days"
                },
                "pregnancy_category": "B",
                "monitoring": ["Clinical response", "Allergic reactions"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Azithromycin",
                "brand_names": ["Zithromax", "Z-Pak"],
                "drug_class": "Macrolide Antibiotic",
                "strength": ["250mg", "500mg"],
                "dosage_forms": ["tablet", "suspension"],
                "route": ["oral"],
                "rxnorm_codes": ["18631", "141963"],
                "search_terms": ["antibiotic", "z-pak", "respiratory", "atypical"],
                "indications": ["Respiratory tract infections", "Skin infections", "STIs"],
                "contraindications": ["Macrolide allergy", "Severe hepatic impairment"],
                "common_side_effects": ["GI upset", "Diarrhea", "QT prolongation"],
                "interactions": ["Warfarin", "Digoxin", "QT-prolonging drugs"],
                "standard_dosing": {
                    "respiratory": "500mg day 1, then 250mg daily x 4 days",
                    "skin": "500mg daily x 3 days"
                },
                "pregnancy_category": "B",
                "monitoring": ["Clinical response", "QT interval if risk factors"]
            },
            
            # Pain/Anti-inflammatory
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Ibuprofen",
                "brand_names": ["Advil", "Motrin"],
                "drug_class": "NSAID",
                "strength": ["200mg", "400mg", "600mg", "800mg"],
                "dosage_forms": ["tablet", "capsule", "suspension"],
                "route": ["oral"],
                "rxnorm_codes": ["5640", "310965"],
                "search_terms": ["nsaid", "pain", "inflammation", "fever", "arthritis"],
                "indications": ["Pain", "Inflammation", "Fever", "Arthritis"],
                "contraindications": ["GI bleeding", "Severe heart failure", "Advanced kidney disease"],
                "common_side_effects": ["GI upset", "Bleeding", "Renal impairment", "Hypertension"],
                "interactions": ["ACE inhibitors", "Warfarin", "Lithium", "Methotrexate"],
                "standard_dosing": {
                    "pain": "400-600mg q6-8h, Max: 2400mg daily",
                    "arthritis": "1200-3200mg daily divided"
                },
                "pregnancy_category": "C/D (3rd trimester)",
                "monitoring": ["GI symptoms", "Renal function", "Blood pressure"]
            },
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Acetaminophen",
                "brand_names": ["Tylenol"],
                "drug_class": "Analgesic/Antipyretic",
                "strength": ["325mg", "500mg", "650mg"],
                "dosage_forms": ["tablet", "capsule", "suspension"],
                "route": ["oral"],
                "rxnorm_codes": ["161", "313782"],
                "search_terms": ["pain", "fever", "tylenol", "analgesic", "safe"],
                "indications": ["Pain", "Fever"],
                "contraindications": ["Severe hepatic impairment"],
                "common_side_effects": ["Hepatotoxicity (overdose)", "Rare: skin reactions"],
                "interactions": ["Warfarin", "Alcohol"],
                "standard_dosing": {
                    "pain_fever": "325-650mg q4-6h, Max: 3000mg daily"
                },
                "pregnancy_category": "B",
                "monitoring": ["Liver function if chronic use", "Total daily dose"]
            },
            
            # Mental Health
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Sertraline",
                "brand_names": ["Zoloft"],
                "drug_class": "SSRI",
                "strength": ["25mg", "50mg", "100mg"],
                "dosage_forms": ["tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["36437", "883805"],
                "search_terms": ["antidepressant", "ssri", "depression", "anxiety", "serotonin"],
                "indications": ["Depression", "Anxiety disorders", "PTSD", "OCD"],
                "contraindications": ["MAOI use", "Pimozide use"],
                "common_side_effects": ["Nausea", "Sexual dysfunction", "Insomnia", "Dizziness"],
                "interactions": ["MAOIs", "Warfarin", "NSAIDs", "Triptans"],
                "standard_dosing": {
                    "depression": "Initial: 50mg daily, Range: 50-200mg daily",
                    "anxiety": "Initial: 25mg daily, Target: 50-200mg daily"
                },
                "pregnancy_category": "C",
                "monitoring": ["Mood", "Suicidal ideation", "Sexual function"]
            },
            
            # Gastrointestinal
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Omeprazole",
                "brand_names": ["Prilosec"],
                "drug_class": "Proton Pump Inhibitor",
                "strength": ["10mg", "20mg", "40mg"],
                "dosage_forms": ["capsule", "tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["7646", "312961"],
                "search_terms": ["ppi", "acid reflux", "gerd", "stomach", "ulcer"],
                "indications": ["GERD", "Peptic ulcer disease", "Dyspepsia"],
                "contraindications": ["Hypersensitivity to PPIs"],
                "common_side_effects": ["Headache", "Diarrhea", "Nausea", "B12 deficiency"],
                "interactions": ["Clopidogrel", "Warfarin", "Atazanavir"],
                "standard_dosing": {
                    "gerd": "20mg daily x 4-8 weeks",
                    "ulcer": "20-40mg daily"
                },
                "pregnancy_category": "C",
                "monitoring": ["Symptom improvement", "Magnesium if long-term"]
            },
            
            # Thyroid
            {
                "id": str(uuid.uuid4()),
                "generic_name": "Levothyroxine",
                "brand_names": ["Synthroid", "Levoxyl"],
                "drug_class": "Thyroid Hormone",
                "strength": ["25mcg", "50mcg", "75mcg", "100mcg", "125mcg", "150mcg"],
                "dosage_forms": ["tablet"],
                "route": ["oral"],
                "rxnorm_codes": ["6387", "966246"],
                "search_terms": ["thyroid", "hypothyroid", "hormone", "tsh", "metabolism"],
                "indications": ["Hypothyroidism", "Thyroid cancer"],
                "contraindications": ["Uncorrected adrenal insufficiency", "Recent MI with hyperthyroidism"],
                "common_side_effects": ["Hyperthyroid symptoms if overdosed", "Hair loss initially"],
                "interactions": ["Iron", "Calcium", "Coffee", "Soybean products"],
                "standard_dosing": {
                    "hypothyroidism": "1.6 mcg/kg/day, adjust based on TSH"
                },
                "pregnancy_category": "A",
                "monitoring": ["TSH", "T4", "Heart rate", "Symptoms"]
            }
        ]
        
        # Add timestamps to medications
        for medication in comprehensive_medications:
            medication["created_at"] = datetime.utcnow()
            medication["updated_at"] = datetime.utcnow()
        
        await db.comprehensive_medications.insert_many(comprehensive_medications)
        
        return {
            "message": "Comprehensive medication database initialized successfully",
            "medications_added": len(comprehensive_medications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing comprehensive medication database: {str(e)}")

@api_router.get("/comprehensive-medications/search")
async def search_comprehensive_medications(
    query: str,
    drug_class: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """Search comprehensive medication database with intelligent matching"""
    try:
        # Build search query
        search_conditions = []
        
        # Text search across multiple fields
        text_search = {
            "$or": [
                {"generic_name": {"$regex": query, "$options": "i"}},
                {"brand_names": {"$regex": query, "$options": "i"}},
                {"drug_class": {"$regex": query, "$options": "i"}},
                {"search_terms": {"$regex": query, "$options": "i"}},
                {"indications": {"$regex": query, "$options": "i"}}
            ]
        }
        search_conditions.append(text_search)
        
        # Drug class filter
        if drug_class:
            search_conditions.append({"drug_class": {"$regex": drug_class, "$options": "i"}})
        
        # Combine conditions
        final_query = {"$and": search_conditions} if len(search_conditions) > 1 else search_conditions[0]
        
        # Execute search
        medications = await db.comprehensive_medications.find(final_query).limit(limit).to_list(limit)
        
        # Process results with relevance scoring
        results = []
        query_lower = query.lower()
        
        for med in medications:
            if "_id" in med:
                del med["_id"]
            
            # Calculate relevance score
            relevance_score = 0
            
            # Exact generic name match
            if query_lower == med["generic_name"].lower():
                relevance_score = 100
            # Generic name starts with query
            elif med["generic_name"].lower().startswith(query_lower):
                relevance_score = 90
            # Brand name exact match
            elif any(query_lower == brand.lower() for brand in med["brand_names"]):
                relevance_score = 95
            # Brand name starts with query
            elif any(brand.lower().startswith(query_lower) for brand in med["brand_names"]):
                relevance_score = 85
            # Drug class match
            elif query_lower in med["drug_class"].lower():
                relevance_score = 75
            # Search terms match
            elif any(query_lower in term.lower() for term in med.get("search_terms", [])):
                relevance_score = 70
            # Indication match
            elif any(query_lower in indication.lower() for indication in med.get("indications", [])):
                relevance_score = 65
            # Generic name contains query
            elif query_lower in med["generic_name"].lower():
                relevance_score = 60
            else:
                relevance_score = 50
            
            med["relevance_score"] = relevance_score
            results.append(med)
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Remove relevance score from final results
        for result in results:
            del result["relevance_score"]
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching medications: {str(e)}")

@api_router.get("/comprehensive-medications")
async def get_comprehensive_medications(
    drug_class: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Get all medications from comprehensive database with optional filtering"""
    try:
        query = {}
        if drug_class:
            query["drug_class"] = {"$regex": drug_class, "$options": "i"}
        
        medications = await db.comprehensive_medications.find(query, {"_id": 0}).limit(limit).to_list(limit)
        
        return medications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving comprehensive medications: {str(e)}")

# Scheduling System API Endpoints

# Provider Management
@api_router.post("/providers", response_model=Provider)
async def create_provider(provider_data: dict):
    try:
        provider = Provider(
            id=str(uuid.uuid4()),
            **provider_data
        )
        
        provider_dict = jsonable_encoder(provider)
        await db.providers.insert_one(provider_dict)
        return provider
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating provider: {str(e)}")

@api_router.get("/providers", response_model=List[Provider])
async def get_providers():
    providers = await db.providers.find({"status": {"$ne": "inactive"}}, {"_id": 0}).sort("name", 1).to_list(1000)
    return [Provider(**provider) for provider in providers]

@api_router.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(provider_id: str):
    provider = await db.providers.find_one({"id": provider_id}, {"_id": 0})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return Provider(**provider)

@api_router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, provider_data: dict):
    try:
        provider_data["updated_at"] = datetime.utcnow()
        result = await db.providers.update_one(
            {"id": provider_id},
            {"$set": jsonable_encoder(provider_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating provider: {str(e)}")

# Provider Schedule Management
@api_router.post("/providers/{provider_id}/schedule")
async def create_provider_schedule(provider_id: str, schedule_data: dict):
    try:
        # Verify provider exists
        provider = await db.providers.find_one({"id": provider_id}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        schedule = ProviderSchedule(
            id=str(uuid.uuid4()),
            provider_id=provider_id,
            **schedule_data
        )
        
        schedule_dict = jsonable_encoder(schedule)
        await db.provider_schedules.insert_one(schedule_dict)
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating schedule: {str(e)}")

@api_router.get("/providers/{provider_id}/schedule")
async def get_provider_schedule(provider_id: str, date: str = None):
    try:
        query = {"provider_id": provider_id}
        if date:
            query["date"] = date
        
        schedules = await db.provider_schedules.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
        return [ProviderSchedule(**schedule) for schedule in schedules]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schedule: {str(e)}")

# Appointment Management
@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment_data: dict, current_user: User = Depends(get_current_active_user)):
    try:
        # Basic required fields
        required = ["patient_id", "provider_id", "appointment_date", "start_time", "end_time", "appointment_type", "reason", "scheduled_by"]
        missing = [f for f in required if f not in appointment_data or appointment_data.get(f) in (None, "")]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing required fields: {', '.join(missing)}")

        # Verify patient exists and get patient name
        patient = await db.patients.find_one({"id": appointment_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient_name = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"

        # Verify provider exists and get provider name
        provider = await db.providers.find_one({"id": appointment_data["provider_id"]}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        provider_name = provider.get("name", f"{provider.get('first_name', '')} {provider.get('last_name', '')}").strip()

        # Compute duration_minutes if not provided
        from datetime import datetime as _dt
        try:
            start_dt = _dt.strptime(f"{appointment_data['appointment_date']} {appointment_data['start_time']}", "%Y-%m-%d %H:%M")
            end_dt = _dt.strptime(f"{appointment_data['appointment_date']} {appointment_data['end_time']}", "%Y-%m-%d %H:%M")
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM")
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        if duration_minutes <= 0:
            raise HTTPException(status_code=422, detail="end_time must be after start_time")
        appointment_data["duration_minutes"] = duration_minutes

        # Check provider availability (schedule)
        day_of_week = start_dt.date().weekday()
        provider_schedule = await db.provider_schedules.find_one({
            "provider_id": appointment_data["provider_id"],
            "day_of_week": day_of_week,
            "is_available": True
        })
        if not provider_schedule:
            raise HTTPException(status_code=409, detail="Provider not available on this day")
        # Within schedule hours
        sch_start = _dt.strptime(provider_schedule["start_time"], "%H:%M").time()
        sch_end = _dt.strptime(provider_schedule["end_time"], "%H:%M").time()
        if not (sch_start <= start_dt.time() and end_dt.time() <= sch_end):
            raise HTTPException(status_code=409, detail="Appointment time outside provider schedule")

        # Check conflicts (overlaps)
        conflicts = await check_appointment_conflicts(
            provider_id=appointment_data["provider_id"],
            appointment_date=start_dt.date(),
            start_time=appointment_data["start_time"],
            duration_minutes=duration_minutes
        )
        if conflicts:
            raise HTTPException(status_code=409, detail="Provider has a conflicting appointment at that time")

        # Create appointment with populated names
        appointment_data_with_names = {
            **appointment_data,
            "patient_name": patient_name,
            "provider_name": provider_name
        }
        appointment = Appointment(id=str(uuid.uuid4()), **appointment_data_with_names)
        await db.appointments.insert_one(jsonable_encoder(appointment))
        return appointment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appointment: {str(e)}")

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments(
    patient_id: str = None,
    provider_id: str = None,
    date: str = None,
    status: str = None
):
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if provider_id:
            query["provider_id"] = provider_id
        if date:
            query["appointment_date"] = date
        if status:
            query["status"] = status
        
        appointments = await db.appointments.find(query, {"_id": 0}).sort("appointment_date", 1).to_list(1000)
        return [Appointment(**appointment) for appointment in appointments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointments: {str(e)}")

# Calendar View (must be before {appointment_id} route)
@api_router.get("/appointments/calendar")
async def get_calendar_view(provider_id: str, date: str, view: str = "day"):
    """Return normalized slots for a provider and date range.
    Response structure: { view, start_date, end_date, slots: [{appointment_id, patient_id, provider_id, start_time, end_time, status}] }
    """
    try:
        from datetime import datetime, timedelta

        # Parse date
        base_date = datetime.strptime(date, "%Y-%m-%d")

        # Compute range
        if view == "day":
            start_date = base_date.date()
            end_date = start_date
        elif view == "week":
            start_date = (base_date - timedelta(days=base_date.weekday())).date()
            end_date = start_date + timedelta(days=6)
        elif view == "month":
            start_date = base_date.replace(day=1).date()
            if base_date.month == 12:
                next_month = base_date.replace(year=base_date.year + 1, month=1, day=1)
            else:
                next_month = base_date.replace(month=base_date.month + 1, day=1)
            end_date = (next_month - timedelta(days=1)).date()
        else:
            raise HTTPException(status_code=400, detail="Invalid view type. Use 'day', 'week', or 'month'")

        # Query provider's appointments in range (exclude cancelled/no_show)
        appts = await db.appointments.find({
            "provider_id": provider_id,
            "status": {"$nin": ["cancelled", "no_show"]},
            "appointment_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        }, {"_id": 0}).sort([("appointment_date", 1), ("start_time", 1)]).to_list(2000)

        # Normalize to slots shape
        slots = []
        for a in appts:
            slots.append({
                "appointment_id": a.get("id"),
                "patient_id": a.get("patient_id"),
                "provider_id": a.get("provider_id"),
                "start_time": f"{a.get('appointment_date')}T{a.get('start_time')}:00",
                "end_time": f"{a.get('appointment_date')}T{a.get('end_time')}:00",
                "status": a.get("status", "scheduled")
            })

        # Validate no overlaps in output for the same provider
        def _to_dt(ts):
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        for i in range(len(slots)):
            si, ei = _to_dt(slots[i]["start_time"]), _to_dt(slots[i]["end_time"])
            for j in range(i+1, len(slots)):
                sj, ej = _to_dt(slots[j]["start_time"]), _to_dt(slots[j]["end_time"])
                if si < ej and ei > sj:
                    # Overlap detected; this should not happen due to create validation
                    # Log and continue; frontend will still receive consistent slots
                    logging.warning(f"Calendar overlap detected for provider {provider_id}: {slots[i]['appointment_id']} with {slots[j]['appointment_id']}")

        return {
            "view": view,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "slots": slots
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendar: {str(e)}")

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment(**appointment)

@api_router.put("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: str, status_data: dict):
    try:
        # Validate that status is provided
        if "status" not in status_data:
            raise HTTPException(status_code=422, detail="Status field is required")
        
        update_data = {
            "status": status_data["status"],
            "updated_at": datetime.utcnow()
        }
        
        result = await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": jsonable_encoder(update_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"message": "Appointment status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appointment: {str(e)}")

@api_router.delete("/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: str):
    try:
        result = await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"message": "Appointment cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling appointment: {str(e)}")

# Enhanced Appointment Management Endpoints
@api_router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, appointment_data: dict, current_user: User = Depends(get_current_active_user)):
    """Update appointment details with conflict checking"""
    try:
        # Check if appointment exists
        existing_appointment = await db.appointments.find_one({"id": appointment_id})
        if not existing_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # If changing date/time, check for conflicts
        if "appointment_date" in appointment_data or "start_time" in appointment_data:
            new_date = appointment_data.get("appointment_date", existing_appointment["appointment_date"])
            new_start_time = appointment_data.get("start_time", existing_appointment["start_time"])
            provider_id = existing_appointment["provider_id"]
            duration = appointment_data.get("duration_minutes", existing_appointment["duration_minutes"])
            
            # Check for conflicts (excluding current appointment)
            conflicts = await check_appointment_conflicts(provider_id, new_date, new_start_time, duration, exclude_appointment_id=appointment_id)
            if conflicts:
                return {"conflicts": conflicts, "message": "Appointment conflicts detected. Please resolve or force update."}
        
        # Update appointment
        update_data = {**appointment_data, "updated_at": jsonable_encoder(datetime.utcnow())}
        result = await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Get updated appointment
        updated_appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
        return Appointment(**updated_appointment)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appointment: {str(e)}")

async def check_appointment_conflicts(provider_id: str, appointment_date: date, start_time: str, duration_minutes: int, exclude_appointment_id: str = None):
    """Check for appointment conflicts"""
    try:
        # Convert times for comparison
        from datetime import datetime, timedelta
        
        # Parse start time
        start_hour, start_min = map(int, start_time.split(':'))
        appointment_start = datetime.combine(appointment_date, datetime.min.time().replace(hour=start_hour, minute=start_min))
        appointment_end = appointment_start + timedelta(minutes=duration_minutes)
        
        # Query for overlapping appointments
        query = {
            "provider_id": provider_id,
            "appointment_date": jsonable_encoder(appointment_date),
            "status": {"$nin": ["cancelled", "no_show"]}
        }
        
        if exclude_appointment_id:
            query["id"] = {"$ne": exclude_appointment_id}
        
        existing_appointments = await db.appointments.find(query, {"_id": 0}).to_list(100)
        
        conflicts = []
        for existing in existing_appointments:
            # Parse existing appointment times
            existing_start_hour, existing_start_min = map(int, existing["start_time"].split(':'))
            existing_start = datetime.combine(appointment_date, datetime.min.time().replace(hour=existing_start_hour, minute=existing_start_min))
            existing_end = existing_start + timedelta(minutes=existing["duration_minutes"])
            
            # Check for overlap
            if (appointment_start < existing_end and appointment_end > existing_start):
                conflicts.append(AppointmentConflict(
                    conflicting_appointment_id=existing["id"],
                    conflict_type="overlap",
                    conflict_message=f"Overlaps with {existing['patient_name']} at {existing['start_time']}"
                ))
        
        return conflicts
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {str(e)}")
        return []

@api_router.get("/appointments/available-slots")
async def get_available_slots(
    provider_id: str,
    date: str,  # YYYY-MM-DD
    duration_minutes: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get available time slots for a provider on a specific date"""
    try:
        from datetime import datetime, timedelta
        
        appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get provider schedule for the day
        day_of_week = appointment_date.weekday()  # 0=Monday
        provider_schedule = await db.provider_schedules.find_one({
            "provider_id": provider_id,
            "day_of_week": day_of_week,
            "is_available": True
        })
        
        if not provider_schedule:
            return {"available_slots": [], "message": "Provider not available on this day"}
        
        # Parse schedule times
        schedule_start = datetime.strptime(provider_schedule["start_time"], "%H:%M").time()
        schedule_end = datetime.strptime(provider_schedule["end_time"], "%H:%M").time()
        
        # Generate all possible slots
        available_slots = []
        current_time = datetime.combine(appointment_date, schedule_start)
        end_time = datetime.combine(appointment_date, schedule_end)
        
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_start = current_time.time().strftime("%H:%M")
            slot_end = (current_time + timedelta(minutes=duration_minutes)).time().strftime("%H:%M")
            
            # Check if slot is available (no conflicting appointments)
            conflicts = await check_appointment_conflicts(provider_id, appointment_date, slot_start, duration_minutes)
            
            available_slots.append(TimeSlot(
                date=appointment_date,
                start_time=slot_start,
                end_time=slot_end,
                provider_id=provider_id,
                provider_name=provider_schedule.get("provider_name", ""),
                is_available=len(conflicts) == 0,
                duration_minutes=duration_minutes
            ))
            
            current_time += timedelta(minutes=duration_minutes)
        
        return {"available_slots": [slot.dict() for slot in available_slots]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available slots: {str(e)}")

# Recurring Appointments
@api_router.post("/appointments/recurring")
async def create_recurring_appointment(recurrence_data: dict, current_user: User = Depends(get_current_active_user)):
    """Create recurring appointments"""
    try:
        from datetime import datetime, timedelta
        
        base_appointment_data = recurrence_data["appointment"]
        recurrence_type = recurrence_data.get("recurrence_type", "weekly")
        recurrence_interval = recurrence_data.get("recurrence_interval", 1)
        recurrence_end_date = recurrence_data.get("recurrence_end_date")
        max_occurrences = recurrence_data.get("max_occurrences", 12)
        
        # Parse dates
        start_date = datetime.strptime(base_appointment_data["appointment_date"], "%Y-%m-%d").date()
        if recurrence_end_date:
            end_date = datetime.strptime(recurrence_end_date, "%Y-%m-%d").date()
        else:
            end_date = start_date + timedelta(days=365)  # Default 1 year
        
        # Create parent appointment
        parent_appointment = Appointment(
            **base_appointment_data,
            scheduled_by=current_user.username,
            is_recurring=True
        )
        parent_dict = jsonable_encoder(parent_appointment)
        await db.appointments.insert_one(parent_dict)
        
        # Create recurrence record
        recurrence_record = AppointmentRecurrence(
            parent_appointment_id=parent_appointment.id,
            recurrence_type=RecurrenceType(recurrence_type),
            recurrence_interval=recurrence_interval,
            recurrence_end_date=end_date,
            max_occurrences=max_occurrences
        )
        recurrence_dict = jsonable_encoder(recurrence_record)
        await db.appointment_recurrences.insert_one(recurrence_dict)
        
        # Generate recurring appointments
        created_appointments = [parent_appointment.id]
        current_date = start_date
        occurrence_count = 1
        
        while occurrence_count < max_occurrences and current_date <= end_date:
            # Calculate next occurrence
            if recurrence_type == "daily":
                current_date += timedelta(days=recurrence_interval)
            elif recurrence_type == "weekly":
                current_date += timedelta(weeks=recurrence_interval)
            elif recurrence_type == "monthly":
                # Add months (approximation)
                current_date = current_date.replace(month=current_date.month + recurrence_interval if current_date.month + recurrence_interval <= 12 else current_date.month + recurrence_interval - 12, year=current_date.year + (current_date.month + recurrence_interval - 1) // 12)
            
            if current_date > end_date:
                break
            
            # Create recurring appointment
            recurring_appointment_data = base_appointment_data.copy()
            recurring_appointment_data["appointment_date"] = current_date.isoformat()
            recurring_appointment_data["appointment_number"] = f"APT{current_date.strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
            
            recurring_appointment = Appointment(
                **recurring_appointment_data,
                scheduled_by=current_user.username,
                is_recurring=True,
                parent_appointment_id=parent_appointment.id
            )
            recurring_dict = jsonable_encoder(recurring_appointment)
            await db.appointments.insert_one(recurring_dict)
            
            created_appointments.append(recurring_appointment.id)
            occurrence_count += 1
        
        # Update recurrence record with created instances
        await db.appointment_recurrences.update_one(
            {"parent_appointment_id": parent_appointment.id},
            {"$set": {"created_instances": created_appointments}}
        )
        
        return {
            "message": "Recurring appointments created successfully",
            "parent_appointment_id": parent_appointment.id,
            "total_appointments": len(created_appointments),
            "created_appointments": created_appointments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating recurring appointments: {str(e)}")

# Waiting List Management
@api_router.post("/waiting-list", response_model=WaitingListEntry)
async def add_to_waiting_list(waiting_list_data: dict, current_user: User = Depends(get_current_active_user)):
    """Add patient to waiting list"""
    try:
        # Get patient details
        patient = await db.patients.find_one({"id": waiting_list_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get provider details
        provider = await db.providers.find_one({"id": waiting_list_data["provider_id"]}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        waiting_entry = WaitingListEntry(
            patient_id=waiting_list_data["patient_id"],
            patient_name=f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            patient_phone=patient.get("telecom", [{}])[0].get("value"),
            patient_email=next((t["value"] for t in patient.get("telecom", []) if t.get("system") == "email"), None),
            provider_id=waiting_list_data["provider_id"],
            provider_name=provider["name"],
            preferred_date=datetime.strptime(waiting_list_data["preferred_date"], "%Y-%m-%d").date(),
            preferred_time_start=waiting_list_data.get("preferred_time_start"),
            preferred_time_end=waiting_list_data.get("preferred_time_end"),
            appointment_type=AppointmentType(waiting_list_data["appointment_type"]),
            priority=waiting_list_data.get("priority", 1),
            duration_minutes=waiting_list_data.get("duration_minutes", 30),
            reason=waiting_list_data["reason"],
            notes=waiting_list_data.get("notes"),
            created_by=current_user.username
        )
        
        waiting_dict = jsonable_encoder(waiting_entry)
        await db.waiting_list.insert_one(waiting_dict)
        
        return waiting_entry
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to waiting list: {str(e)}")

@api_router.get("/waiting-list", response_model=List[WaitingListEntry])
async def get_waiting_list(
    provider_id: str = None,
    priority: int = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """Get waiting list entries"""
    try:
        query = {}
        if provider_id:
            query["provider_id"] = provider_id
        if priority:
            query["priority"] = priority
        if active_only:
            query["is_active"] = True
        
        waiting_entries = await db.waiting_list.find(query, {"_id": 0}).sort("priority", -1).sort("created_at", 1).to_list(100)
        return [WaitingListEntry(**entry) for entry in waiting_entries]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waiting list: {str(e)}")

@api_router.post("/waiting-list/{entry_id}/convert-to-appointment")
async def convert_waiting_list_to_appointment(entry_id: str, appointment_data: dict, current_user: User = Depends(get_current_active_user)):
    """Convert waiting list entry to appointment"""
    try:
        # Get waiting list entry
        waiting_entry = await db.waiting_list.find_one({"id": entry_id}, {"_id": 0})
        if not waiting_entry:
            raise HTTPException(status_code=404, detail="Waiting list entry not found")
        
        # Create appointment from waiting list entry
        appointment_creation_data = {
            "patient_id": waiting_entry["patient_id"],
            "patient_name": waiting_entry["patient_name"],
            "provider_id": waiting_entry["provider_id"],
            "provider_name": waiting_entry["provider_name"],
            "appointment_date": appointment_data["appointment_date"],
            "start_time": appointment_data["start_time"],
            "duration_minutes": waiting_entry["duration_minutes"],
            "appointment_type": waiting_entry["appointment_type"],
            "reason": waiting_entry["reason"],
            "notes": f"Converted from waiting list. Original notes: {waiting_entry.get('notes', '')}",
            "scheduled_by": current_user.username
        }
        
        # Check for conflicts
        conflicts = await check_appointment_conflicts(
            appointment_creation_data["provider_id"],
            datetime.strptime(appointment_data["appointment_date"], "%Y-%m-%d").date(),
            appointment_data["start_time"],
            appointment_creation_data["duration_minutes"]
        )
        
        if conflicts:
            return {"conflicts": conflicts, "message": "Cannot create appointment due to conflicts"}
        
        # Create appointment
        appointment = Appointment(**appointment_creation_data)
        appointment_dict = jsonable_encoder(appointment)
        await db.appointments.insert_one(appointment_dict)
        
        # Mark waiting list entry as inactive
        await db.waiting_list.update_one(
            {"id": entry_id},
            {"$set": {"is_active": False, "updated_at": jsonable_encoder(datetime.utcnow())}}
        )
        
        return {
            "message": "Waiting list entry converted to appointment successfully",
            "appointment_id": appointment.id,
            "appointment": appointment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting waiting list entry: {str(e)}")

# Patient Communications System API Endpoints

# Message Templates
@api_router.post("/communications/init-templates")
async def init_message_templates():
    try:
        # Check if templates already exist
        existing = await db.communication_templates.count_documents({})
        if existing > 0:
            return {"message": "Templates already initialized", "count": existing}
        
        templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "Appointment Reminder",
                "message_type": "appointment_reminder",
                "subject_template": "Appointment Reminder - {{CLINIC_NAME}}",
                "content_template": "Dear {{PATIENT_NAME}},\n\nThis is a reminder of your upcoming appointment:\n\nDate: {{APPOINTMENT_DATE}}\nTime: {{APPOINTMENT_TIME}}\nProvider: {{PROVIDER_NAME}}\nLocation: {{CLINIC_ADDRESS}}\n\nPlease arrive 15 minutes early for check-in.\n\nIf you need to reschedule, please call us at {{CLINIC_PHONE}}.\n\nThank you,\n{{CLINIC_NAME}}",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Lab Results Available",
                "message_type": "lab_results",
                "subject_template": "Lab Results Available - {{CLINIC_NAME}}",
                "content_template": "Dear {{PATIENT_NAME}},\n\nYour lab results from {{TEST_DATE}} are now available.\n\nPlease log into your patient portal or call our office at {{CLINIC_PHONE}} to discuss your results with your provider.\n\nProvider: {{PROVIDER_NAME}}\n\nThank you,\n{{CLINIC_NAME}}",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Prescription Ready",
                "message_type": "prescription",
                "subject_template": "Prescription Ready for Pickup - {{PHARMACY_NAME}}",
                "content_template": "Dear {{PATIENT_NAME}},\n\nYour prescription for {{MEDICATION_NAME}} is ready for pickup at:\n\n{{PHARMACY_NAME}}\n{{PHARMACY_ADDRESS}}\n{{PHARMACY_PHONE}}\n\nPrescribed by: {{PROVIDER_NAME}}\nPrescription #: {{PRESCRIPTION_NUMBER}}\n\nThank you,\n{{CLINIC_NAME}}",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Payment Reminder",
                "message_type": "billing",
                "subject_template": "Payment Reminder - {{CLINIC_NAME}}",
                "content_template": "Dear {{PATIENT_NAME}},\n\nThis is a friendly reminder that you have an outstanding balance:\n\nInvoice #: {{INVOICE_NUMBER}}\nService Date: {{SERVICE_DATE}}\nAmount Due: ${{AMOUNT_DUE}}\n\nYou can pay online through our patient portal or call us at {{CLINIC_PHONE}}.\n\nThank you for your prompt attention to this matter.\n\n{{CLINIC_NAME}}",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        
        await db.communication_templates.insert_many(templates)
        
        return {
            "message": "Message templates initialized successfully",
            "templates_added": len(templates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing templates: {str(e)}")

@api_router.get("/communications/templates")
async def get_message_templates(template_type: str = None):
    try:
        query = {}
        if template_type:
            query["message_type"] = template_type
        templates = await db.communication_templates.find(query, {"_id": 0}).sort("name", 1).to_list(1000)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@api_router.post("/communications/templates")
async def create_message_template(template_data: dict):
    try:
        # Enforce fields: title, body, variables (list of placeholders)
        required = ["title", "body"]
        missing = [f for f in required if f not in template_data or not template_data.get(f)]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing fields: {', '.join(missing)}")
        template_data["id"] = str(uuid.uuid4())
        template_data["variables"] = template_data.get("variables", [])
        template_data["created_at"] = datetime.utcnow()
        await db.communication_templates.insert_one(jsonable_encoder(template_data))
        return {"message": "Template created successfully", "id": template_data["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@api_router.put("/communications/templates/{template_id}")
async def update_message_template(template_id: str, template_data: dict):
    try:
        update = {k: v for k, v in template_data.items() if k not in ("id", "created_at")}
        update["updated_at"] = datetime.utcnow()
        result = await db.communication_templates.update_one({"id": template_id}, {"$set": jsonable_encoder(update)})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")

@api_router.delete("/communications/templates/{template_id}")
async def delete_message_template(template_id: str):
    try:
        result = await db.communication_templates.delete_one({"id": template_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

async def create_message_template(template_data: dict):
    try:
        template_data["id"] = str(uuid.uuid4())
        template_data["created_at"] = datetime.utcnow()
        
        await db.communication_templates.insert_one(jsonable_encoder(template_data))
        return {"message": "Template created successfully", "id": template_data["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

# Message Management
@api_router.post("/communications/send")
async def send_message(message_data: dict):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": message_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Process template variables if template_id provided
        if "template_id" in message_data:
            template = await db.communication_templates.find_one({"id": message_data["template_id"]}, {"_id": 0})
            if template:
                # Unified 'title' and 'body' fields preferred; fallback to legacy subject/content templates
                subject = template.get("title") or template.get("subject_template", "")
                content = template.get("body") or template.get("content_template", "")
                
                # Build default variables from patient/appointment/invoice context when available
                variables = {
                    "patient_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
                }
                variables.update(message_data.get("variables", {}))
                # Replace placeholders in content: support both {{VAR}} and {var}
                # Normalize variables: allow lower/upper and underscores
                for var, value in variables.items():
                    # Legacy double-brace style
                    content = content.replace(f"{{{{{var}}}}}", str(value))
                    subject = subject.replace(f"{{{{{var}}}}}", str(value))
                    # Curly-brace style used in new spec
                    content = content.replace(f"{{{var}}}", str(value))
                    subject = subject.replace(f"{{{var}}}", str(value))
                
                message_data["content"] = content
                message_data["subject"] = subject
                message_data["message_type"] = template["message_type"]
        
        # Extract patient name properly
        patient_name = ""
        if "name" in patient:
            if isinstance(patient["name"], dict):
                # Single name object
                given = patient["name"].get("given", [""])[0] if patient["name"].get("given") else ""
                family = patient["name"].get("family", "")
                patient_name = f"{given} {family}".strip()
            elif isinstance(patient["name"], list) and len(patient["name"]) > 0:
                # Array of name objects - use first one
                name_obj = patient["name"][0]
                given = name_obj.get("given", [""])[0] if name_obj.get("given") else ""
                family = name_obj.get("family", "")
                patient_name = f"{given} {family}".strip()
            else:
                patient_name = "Unknown Patient"
        else:
            patient_name = "Unknown Patient"
        
        message = PatientMessage(
            id=str(uuid.uuid4()),
            patient_name=patient_name,
            **message_data
        )
        
        message_dict = jsonable_encoder(message)
        await db.patient_messages.insert_one(message_dict)
        
        return {"message": "Message sent successfully", "id": message.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@api_router.get("/communications/messages")
async def get_messages(
    patient_id: str = None,
    type: str = None,
    status: str = None,
    limit: int = 100
):
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if type:
            query["message_type"] = type
        if status:
            query["status"] = status
        
        messages = await db.patient_messages.find(query, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
        return [PatientMessage(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@api_router.get("/communications/messages/patient/{patient_id}")
async def get_patient_messages(patient_id: str):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        messages = await db.patient_messages.find({"patient_id": patient_id}, {"_id": 0}).sort("sent_at", -1).to_list(1000)
        return [PatientMessage(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient messages: {str(e)}")

@api_router.put("/communications/messages/{message_id}/status")
async def update_message_status(message_id: str, status_data: dict):
    try:
        update_data = {"status": status_data["status"]}
        if status_data["status"] == "read":
            update_data["read_at"] = datetime.utcnow()
        
        result = await db.patient_messages.update_one(
            {"id": message_id},
            {"$set": jsonable_encoder(update_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {"message": "Message status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating message status: {str(e)}")

# System Initialization Endpoints
@api_router.post("/system/init-appointment-types")
async def init_appointment_types():
    """Initialize default appointment types with business rules"""
    try:
        # Check if types already exist
        existing = await db.appointment_types.count_documents({})
        if existing > 0:
            return {"message": "Appointment types already initialized", "count": existing}
        
        default_types = [
            {
                "name": "General Consultation",
                "appointment_type": "consultation",
                "duration_minutes": 30,
                "buffer_before_minutes": 5,
                "buffer_after_minutes": 5,
                "max_advance_booking_days": 90,
                "min_advance_booking_hours": 2,
                "requires_referral": False,
                "provider_specialties_required": [],
                "is_active": True
            },
            {
                "name": "Annual Physical Exam",
                "appointment_type": "physical_exam",
                "duration_minutes": 60,
                "buffer_before_minutes": 10,
                "buffer_after_minutes": 10,
                "max_advance_booking_days": 180,
                "min_advance_booking_hours": 24,
                "requires_referral": False,
                "allowed_patient_ages": {"min": 18},
                "provider_specialties_required": ["Family Medicine", "Internal Medicine"],
                "is_active": True
            },
            {
                "name": "Follow-up Visit",
                "appointment_type": "follow_up",
                "duration_minutes": 20,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 5,
                "max_advance_booking_days": 60,
                "min_advance_booking_hours": 1,
                "requires_referral": False,
                "provider_specialties_required": [],
                "is_active": True
            },
            {
                "name": "Urgent Care",
                "appointment_type": "urgent",
                "duration_minutes": 45,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 15,
                "max_advance_booking_days": 7,
                "min_advance_booking_hours": 0,
                "requires_referral": False,
                "provider_specialties_required": [],
                "is_active": True
            },
            {
                "name": "Vaccination",
                "appointment_type": "vaccination",
                "duration_minutes": 15,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 5,
                "max_advance_booking_days": 30,
                "min_advance_booking_hours": 2,
                "requires_referral": False,
                "provider_specialties_required": [],
                "is_active": True
            }
        ]
        
        # Add IDs and timestamps
        for apt_type in default_types:
            apt_type["id"] = str(uuid.uuid4())
            apt_type["created_at"] = datetime.utcnow()
        
        await db.appointment_types.insert_many(default_types)
        
        return {
            "message": "Appointment types initialized successfully",
            "types_added": len(default_types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing appointment types: {str(e)}")

@api_router.post("/system/init-automated-notifications")
async def init_automated_notifications():
    """Initialize default automated notification triggers"""
    try:
        # Check if notifications already exist
        existing = await db.automated_notifications.count_documents({})
        if existing > 0:
            return {"message": "Automated notifications already initialized", "count": existing}
        
        # First ensure we have templates
        templates = await db.communication_templates.find({"is_active": True}).to_list(10)
        if not templates:
            # Initialize templates first
            await init_message_templates()
            templates = await db.communication_templates.find({"is_active": True}).to_list(10)
        
        # Get template IDs
        template_map = {template["message_type"]: template["id"] for template in templates}
        
        default_notifications = [
            {
                "trigger": "appointment_scheduled",
                "service": "email",
                "template_id": template_map.get("appointment_reminder", templates[0]["id"]),
                "delay_minutes": 0,  # Immediate
                "is_active": True
            },
            {
                "trigger": "appointment_reminder_24h",
                "service": "sms",
                "template_id": template_map.get("appointment_reminder", templates[0]["id"]),
                "delay_minutes": -1440,  # 24 hours before (negative)
                "is_active": True
            },
            {
                "trigger": "appointment_reminder_2h",
                "service": "sms",
                "template_id": template_map.get("appointment_reminder", templates[0]["id"]),
                "delay_minutes": -120,  # 2 hours before
                "is_active": True
            },
            {
                "trigger": "appointment_confirmed",
                "service": "email",
                "template_id": template_map.get("appointment_reminder", templates[0]["id"]),
                "delay_minutes": 0,
                "is_active": True
            }
        ]
        
        # Add IDs and timestamps
        for notification in default_notifications:
            notification["id"] = str(uuid.uuid4())
            notification["created_at"] = datetime.utcnow()
        
        await db.automated_notifications.insert_many(default_notifications)
        
        return {
            "message": "Automated notifications initialized successfully",
            "notifications_added": len(default_notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing automated notifications: {str(e)}")

# eRx (Electronic Prescribing) API Endpoints

# Initialize sample FHIR medications
async def initialize_fhir_medications():
    """Initialize sample FHIR medications for electronic prescribing"""
    default_medications = [
        {
            "id": str(uuid.uuid4()),
            "resource_type": "Medication",
            "code": {"coding": [{"system": "RxNorm", "code": "314076"}]},
            "status": "active",
            "generic_name": "Lisinopril",
            "brand_names": ["Prinivil", "Zestril"],
            "strength": "10mg",
            "dosage_forms": ["tablet"],
            "route_of_administration": ["oral"],
            "drug_class": "antihypertensive",
            "standard_dosing": {"adult": "10-40mg once daily"}
        },
        {
            "id": str(uuid.uuid4()),
            "resource_type": "Medication",
            "code": {"coding": [{"system": "RxNorm", "code": "860981"}]},
            "status": "active",
            "generic_name": "Metformin",
            "brand_names": ["Glucophage"],
            "strength": "500mg",
            "dosage_forms": ["tablet"],
            "route_of_administration": ["oral"],
            "drug_class": "antidiabetic",
            "standard_dosing": {"adult": "500-2000mg daily in divided doses"}
        }
    ]
    await db.fhir_medications.insert_many(default_medications)
    return len(default_medications)

@api_router.get("/erx/medications")
async def get_erx_medications(current_user: User = Depends(get_current_active_user)):
    """Get FHIR medications for electronic prescribing"""
    try:
        medications = await db.fhir_medications.find().sort("generic_name", 1).to_list(1000)
        # Remove MongoDB ObjectId and return clean data
        clean_medications = []
        for med in medications:
            if "_id" in med:
                del med["_id"]
            clean_medications.append(med)
        return clean_medications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving eRx medications: {str(e)}")

@api_router.post("/erx/init")
async def initialize_erx_system(current_user: User = Depends(get_current_active_user)):
    """Initialize electronic prescribing system with sample medications"""
    try:
        # Check if eRx medications already exist
        existing = await db.fhir_medications.count_documents({})
        if existing > 0:
            return {"message": "eRx system already initialized", "medications_count": existing}
        
        # Initialize with sample FHIR medications
        count = await initialize_fhir_medications()
        
        return {"message": "eRx system initialized successfully", "status": "ready", "medications_added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing eRx system: {str(e)}")

@api_router.get("/erx/formulary")
async def get_formulary(current_user: User = Depends(get_current_active_user)):
    """Get formulary medications (preferred drug list)"""
    try:
        # Get commonly prescribed medications from the FHIR medications list
        formulary = await db.fhir_medications.find({
            "generic_name": {"$in": [
                "Lisinopril", "Metformin", "Atorvastatin", "Amlodipine", "Metoprolol",
                "Omeprazole", "Albuterol", "Hydrochlorothiazide", "Losartan", "Simvastatin"
            ]}
        }).sort("generic_name", 1).to_list(100)
        
        # Remove MongoDB ObjectId and return clean data
        clean_formulary = []
        for med in formulary:
            if "_id" in med:
                del med["_id"]
            clean_formulary.append(med)
        
        return {
            "formulary_medications": clean_formulary,
            "total_count": len(clean_formulary),
            "description": "Preferred drug list for electronic prescribing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving formulary: {str(e)}")

# eRx Integration within Patient Chart
@api_router.get("/patients/{patient_id}/erx/current-medications", response_model=List[Dict[str, Any]])
async def get_patient_current_medications(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get patient's current medications for eRx prescribing interface"""
    try:
        # Get current active medications for the patient
        medications = await db.medications.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).sort("start_date", -1).to_list(100)
        
        return medications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient medications: {str(e)}")

@api_router.get("/patients/{patient_id}/erx/allergies", response_model=List[Dict[str, Any]])
async def get_patient_allergies_for_erx(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get patient allergies for drug interaction checking during prescribing"""
    try:
        allergies = await db.allergies.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return allergies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient allergies: {str(e)}")

@api_router.post("/patients/{patient_id}/erx/prescribe")
async def prescribe_medication_from_chart(
    patient_id: str, 
    prescription_data: Dict[str, Any], 
    current_user: User = Depends(get_current_active_user)
):
    """Prescribe medication from within patient chart with full interaction checking"""
    
    try:
        # Validate patient exists
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get medication details from FHIR medication database
        medication_id = prescription_data.get("medication_id")
        medication = await db.fhir_medications.find_one({"id": medication_id}, {"_id": 0})
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        # Check for drug allergies
        patient_allergies = await db.allergies.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).to_list(100)
        
        allergy_alerts = []
        for allergy in patient_allergies:
            if medication["generic_name"].lower() in allergy.get("allergen", "").lower():
                allergy_alerts.append({
                    "type": "allergy_alert",
                    "severity": allergy.get("severity", "moderate"),
                    "message": f"Patient has documented allergy to {allergy['allergen']} - {allergy.get('reaction', '')}"
                })
        
        # Check for drug-drug interactions with current medications
        current_meds = await db.medications.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).to_list(100)
        
        interaction_alerts = []
        for current_med in current_meds:
            # Simple interaction check (in production, use comprehensive drug interaction database)
            interaction_risk = check_drug_interaction(medication["generic_name"], current_med.get("medication_name", ""))
            if interaction_risk:
                interaction_alerts.append({
                    "type": "drug_interaction",
                    "severity": interaction_risk["severity"],
                    "message": f"Potential interaction between {medication['generic_name']} and {current_med['medication_name']}: {interaction_risk['description']}"
                })
        
        # If there are critical alerts, require override confirmation
        critical_alerts = [alert for alert in (allergy_alerts + interaction_alerts) if alert.get("severity") in ["severe", "critical"]]
        if critical_alerts and not prescription_data.get("override_alerts", False):
            return {
                "status": "alerts_found",
                "critical_alerts": critical_alerts,
                "all_alerts": allergy_alerts + interaction_alerts,
                "requires_override": True,
                "message": "Critical drug safety alerts found. Please review and confirm to override."
            }
        
        # Generate prescription number
        count = await db.prescriptions.count_documents({})
        prescription_number = f"RX{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"
        
        # Create prescription
        prescription = MedicationRequest(
            prescription_number=prescription_number,
            medication_id=medication_id,
            medication_display=medication.get("display_name", medication.get("generic_name", "Unknown Medication")),
            patient_id=patient_id,
            patient_display=f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            prescriber_id=current_user.username,
            prescriber_name=getattr(current_user, 'full_name', current_user.username),
            dosage_text=prescription_data["dosage_text"],
            dose_quantity=prescription_data.get("dose_quantity", 1.0),
            dose_unit=prescription_data.get("dose_unit", "tablet"),
            frequency=prescription_data["frequency"],
            route=prescription_data.get("route", "oral"),
            quantity=prescription_data["quantity"],
            days_supply=prescription_data.get("days_supply", 30),
            refills=prescription_data.get("refills", 0),
            indication=prescription_data.get("indication", ""),
            created_by=current_user.username,
            status=PrescriptionStatus.ACTIVE
        )
        
        prescription_dict = jsonable_encoder(prescription)
        await db.prescriptions.insert_one(prescription_dict)
        
        # Add medication to patient's current medications
        patient_medication = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "medication_name": medication["generic_name"],
            "dosage": prescription_data["dosage_text"],
            "frequency": prescription_data["frequency"],
            "route": prescription_data.get("route", "oral"),
            "start_date": date.today(),
            "end_date": None,
            "status": "active",
            "prescribed_by": current_user.username,
            "prescription_id": prescription.id,
            "indication": prescription_data.get("indication", ""),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        patient_medication_dict = jsonable_encoder(patient_medication)
        await db.medications.insert_one(patient_medication_dict)
        
        return {
            "status": "success",
            "prescription": prescription,
            "patient_medication_added": patient_medication["id"],
            "alerts_reviewed": len(allergy_alerts + interaction_alerts),
            "critical_alerts_overridden": len(critical_alerts),
            "message": f"Prescription {prescription_number} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating prescription: {str(e)}")

def check_drug_interaction(drug1: str, drug2: str):
    """Basic drug interaction checker (in production, use comprehensive database)"""
    # Simple interaction database - in production, integrate with comprehensive drug interaction API
    interactions = {
        ("warfarin", "aspirin"): {"severity": "severe", "description": "Increased bleeding risk"},
        ("lisinopril", "potassium"): {"severity": "moderate", "description": "Hyperkalemia risk"},
        ("metformin", "contrast"): {"severity": "moderate", "description": "Lactic acidosis risk"},
        ("simvastatin", "amlodipine"): {"severity": "mild", "description": "Increased statin levels"},
    }
    
    # Check both directions
    key1 = (drug1.lower(), drug2.lower())
    key2 = (drug2.lower(), drug1.lower())
    
    return interactions.get(key1) or interactions.get(key2)

@api_router.get("/patients/{patient_id}/erx/prescription-history", response_model=List[Dict[str, Any]])
async def get_patient_prescription_history(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get complete prescription history for patient within chart context"""
    try:
        prescriptions = await db.prescriptions.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return prescriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescription history: {str(e)}")

@api_router.put("/patients/{patient_id}/erx/prescriptions/{prescription_id}/status")
async def update_prescription_status_from_chart(
    patient_id: str,
    prescription_id: str,
    status_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """Update prescription status from within patient chart"""
    try:
        new_status = status_data.get("status")
        valid_statuses = ["active", "completed", "cancelled", "discontinued"]
        
        if new_status not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Update prescription
        result = await db.prescriptions.update_one(
            {"id": prescription_id, "patient_id": patient_id},
            {"$set": {"status": new_status, "updated_at": jsonable_encoder(datetime.utcnow())}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # If discontinuing, also update patient's current medications
        if new_status in ["cancelled", "discontinued"]:
            await db.medications.update_one(
                {"prescription_id": prescription_id, "patient_id": patient_id},
                {"$set": {"status": "discontinued", "end_date": jsonable_encoder(date.today()), "updated_at": jsonable_encoder(datetime.utcnow())}}
            )
        
        # Get updated prescription
        updated_prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
        return MedicationRequest(**updated_prescription)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prescription status: {str(e)}")

# Telehealth System API Endpoints
@api_router.post("/telehealth/sessions", response_model=TelehealthSession)
async def create_telehealth_session(session_data: TelehealthSessionCreate, current_user: User = Depends(get_current_active_user)):
    """Create a new telehealth session"""
    try:
        # Get patient details
        patient = await db.patients.find_one({"id": session_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_name = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
        
        # Get provider details
        provider = await db.providers.find_one({"id": session_data.provider_id}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        provider_name = f"{provider.get('title', 'Dr.')} {provider.get('first_name', '')} {provider.get('last_name', '')}".strip()
        
        # Calculate session end time
        scheduled_end = session_data.scheduled_start + timedelta(minutes=session_data.duration_minutes)
        
        # Generate room ID and session URL
        room_id = f"room_{session_data.patient_id}_{session_data.provider_id}_{int(datetime.utcnow().timestamp())}"
        session_url = f"/telehealth/room/{room_id}"
        
        # Create session
        session = TelehealthSession(
            patient_id=session_data.patient_id,
            patient_name=patient_name,
            provider_id=session_data.provider_id,
            provider_name=provider_name,
            session_type=session_data.session_type,
            title=session_data.title,
            description=session_data.description,
            scheduled_start=session_data.scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=session_data.duration_minutes,
            appointment_id=session_data.appointment_id,
            room_id=room_id,
            session_url=session_url,
            recording_enabled=session_data.recording_enabled,
            access_code=session_data.access_code,
            created_by=current_user.username
        )
        
        session_dict = jsonable_encoder(session)
        await db.telehealth_sessions.insert_one(session_dict)
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating telehealth session: {str(e)}")

@api_router.get("/telehealth/sessions", response_model=List[TelehealthSession])
async def get_telehealth_sessions(
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    status: Optional[TelehealthSessionStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get telehealth sessions with filtering options"""
    try:
        query = {}
        
        if patient_id:
            query["patient_id"] = patient_id
        if provider_id:
            query["provider_id"] = provider_id
        if status:
            query["status"] = status
        
        if start_date and end_date:
            query["scheduled_start"] = {
                "$gte": datetime.fromisoformat(start_date),
                "$lte": datetime.fromisoformat(end_date)
            }
        
        sessions = await db.telehealth_sessions.find(query, {"_id": 0}).sort("scheduled_start", -1).to_list(100)
        
        # Populate missing fields for sessions that were created with old model
        populated_sessions = []
        for session in sessions:
            try:
                # If missing required fields, populate them
                if "patient_name" not in session and session.get("patient_id"):
                    patient = await db.patients.find_one({"id": session["patient_id"]}, {"_id": 0})
                    if patient:
                        session["patient_name"] = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
                    else:
                        session["patient_name"] = "Unknown Patient"
                
                if "provider_name" not in session and session.get("provider_id"):
                    provider = await db.providers.find_one({"id": session["provider_id"]}, {"_id": 0})
                    if provider:
                        session["provider_name"] = f"{provider.get('title', 'Dr.')} {provider.get('first_name', '')} {provider.get('last_name', '')}".strip()
                    else:
                        session["provider_name"] = "Unknown Provider"
                
                if "title" not in session:
                    session["title"] = f"Telehealth Session - {session.get('session_type', 'consultation').replace('_', ' ').title()}"
                
                if "scheduled_end" not in session:
                    if session.get("scheduled_start") and session.get("duration_minutes"):
                        scheduled_start = session["scheduled_start"]
                        if isinstance(scheduled_start, str):
                            # Handle different datetime string formats
                            try:
                                scheduled_start = datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
                            except:
                                try:
                                    scheduled_start = datetime.strptime(scheduled_start, "%Y-%m-%dT%H:%M:%S.%f")
                                except:
                                    scheduled_start = datetime.utcnow()
                        elif not isinstance(scheduled_start, datetime):
                            scheduled_start = datetime.utcnow()
                        session["scheduled_end"] = scheduled_start + timedelta(minutes=session.get("duration_minutes", 30))
                    else:
                        # Default to 30 minutes from now if no scheduled_start
                        session["scheduled_end"] = datetime.utcnow() + timedelta(minutes=30)
                
                # Ensure all required fields have default values
                if "duration_minutes" not in session:
                    session["duration_minutes"] = 30
                if "session_type" not in session:
                    session["session_type"] = "video_consultation"
                if "status" not in session:
                    session["status"] = "scheduled"
                if "recording_enabled" not in session:
                    session["recording_enabled"] = False
                if "billable" not in session:
                    session["billable"] = True
                if "max_participants" not in session:
                    session["max_participants"] = 10
                if "participants" not in session:
                    session["participants"] = []
                if "chat_messages" not in session:
                    session["chat_messages"] = []
                if "technical_issues" not in session:
                    session["technical_issues"] = []
                if "created_by" not in session:
                    session["created_by"] = "system"
                
                # Convert string dates to datetime objects if needed
                for date_field in ["scheduled_start", "scheduled_end", "actual_start", "actual_end", "created_at", "updated_at"]:
                    if date_field in session and isinstance(session[date_field], str):
                        try:
                            session[date_field] = datetime.fromisoformat(session[date_field].replace('Z', '+00:00'))
                        except:
                            try:
                                session[date_field] = datetime.strptime(session[date_field], "%Y-%m-%dT%H:%M:%S.%f")
                            except:
                                if date_field in ["created_at", "updated_at"]:
                                    session[date_field] = datetime.utcnow()
                                else:
                                    session[date_field] = None
                
                populated_sessions.append(TelehealthSession(**session))
            except Exception as e:
                # Skip sessions that can't be converted
                print(f"Skipping session {session.get('id', 'unknown')}: {str(e)}")
                continue
        
        return populated_sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving telehealth sessions: {str(e)}")

@api_router.get("/telehealth/sessions/{session_id}", response_model=TelehealthSession)
async def get_telehealth_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Get specific telehealth session"""
    session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Telehealth session not found")
    return TelehealthSession(**session)

@api_router.put("/telehealth/sessions/{session_id}", response_model=TelehealthSession)
async def update_telehealth_session(
    session_id: str, 
    session_data: TelehealthSessionUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Update telehealth session"""
    try:
        # Check if session exists
        existing_session = await db.telehealth_sessions.find_one({"id": session_id})
        if not existing_session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Prepare update data
        update_data = {k: v for k, v in session_data.dict().items() if v is not None}
        update_data["updated_at"] = jsonable_encoder(datetime.utcnow())
        
        # Update session
        result = await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Return updated session
        updated_session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        return TelehealthSession(**updated_session)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating telehealth session: {str(e)}")

@api_router.post("/telehealth/sessions/{session_id}/start")
async def start_telehealth_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Start a telehealth session"""
    try:
        # Check if session exists
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Update session status and start time
        update_data = {
            "status": TelehealthSessionStatus.IN_PROGRESS.value,
            "actual_start": jsonable_encoder(datetime.utcnow()),
            "updated_at": jsonable_encoder(datetime.utcnow())
        }
        
        await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        # Create encounter if linked to appointment
        encounter_id = None
        if session.get("appointment_id"):
            try:
                encounter_data = {
                    "patient_id": session["patient_id"],
                    "provider_id": session["provider_id"],
                    "encounter_type": "telemedicine",
                    "date": datetime.utcnow().date().isoformat(),
                    "time": datetime.utcnow().time().isoformat(),
                    "status": "in_progress",
                    "location": "Telehealth Session",
                    "appointment_id": session["appointment_id"],
                    "telehealth_session_id": session_id
                }
                
                encounter = Encounter(**encounter_data)
                encounter_dict = jsonable_encoder(encounter)
                await db.encounters.insert_one(encounter_dict)
                encounter_id = encounter.id
                
                # Link encounter to session
                await db.telehealth_sessions.update_one(
                    {"id": session_id},
                    {"$set": {"encounter_id": encounter_id}}
                )
                
            except Exception as e:
                logger.warning(f"Could not create encounter for telehealth session: {str(e)}")
        
        return {
            "message": "Telehealth session started successfully",
            "session_id": session_id,
            "encounter_id": encounter_id,
            "room_url": session.get("session_url"),
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting telehealth session: {str(e)}")

@api_router.post("/telehealth/sessions/{session_id}/end")
async def end_telehealth_session(session_id: str, session_summary: Dict[str, Any] = None, current_user: User = Depends(get_current_active_user)):
    """End a telehealth session and finalize documentation"""
    try:
        # Check if session exists
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Calculate actual duration
        actual_start = datetime.fromisoformat(session["actual_start"]) if session.get("actual_start") else datetime.utcnow()
        actual_end = datetime.utcnow()
        actual_duration = int((actual_end - actual_start).total_seconds() / 60)
        
        # Update session status and end time
        update_data = {
            "status": TelehealthSessionStatus.COMPLETED.value,
            "actual_end": jsonable_encoder(actual_end),
            "updated_at": jsonable_encoder(datetime.utcnow())
        }
        
        # Add session summary if provided
        if session_summary:
            if "session_notes" in session_summary:
                update_data["session_notes"] = session_summary["session_notes"]
            if "provider_notes" in session_summary:
                update_data["provider_notes"] = session_summary["provider_notes"]
            if "technical_issues" in session_summary:
                update_data["technical_issues"] = session_summary["technical_issues"]
        
        await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        # Complete associated encounter
        if session.get("encounter_id"):
            try:
                await db.encounters.update_one(
                    {"id": session["encounter_id"]},
                    {"$set": {
                        "status": "completed",
                        "notes": session_summary.get("session_notes", "Telehealth session completed"),
                        "updated_at": jsonable_encoder(datetime.utcnow())
                    }}
                )
            except Exception as e:
                logger.warning(f"Could not complete encounter: {str(e)}")
        
        return {
            "message": "Telehealth session ended successfully",
            "session_id": session_id,
            "actual_duration": actual_duration,
            "ended_at": actual_end.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending telehealth session: {str(e)}")

# Waiting Room Management
@api_router.post("/telehealth/waiting-room/{session_id}")
async def join_waiting_room(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Join telehealth waiting room"""
    try:
        # Check if session exists
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Get patient details (assuming current user is patient or authorized)
        patient_id = session["patient_id"]
        patient_name = session["patient_name"]
        
        # Create waiting room entry
        waiting_entry = TelehealthWaitingRoom(
            session_id=session_id,
            patient_id=patient_id,
            patient_name=patient_name
        )
        
        waiting_dict = jsonable_encoder(waiting_entry)
        await db.telehealth_waiting_room.insert_one(waiting_dict)
        
        # Update session status
        await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": TelehealthSessionStatus.WAITING.value}}
        )
        
        return {
            "message": "Joined waiting room successfully",
            "waiting_entry_id": waiting_entry.id,
            "estimated_wait_time": 5  # minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining waiting room: {str(e)}")

@api_router.get("/telehealth/waiting-room")
async def get_waiting_room_patients(current_user: User = Depends(get_current_active_user)):
    """Get patients in waiting room (for providers)"""
    try:
        waiting_patients = await db.telehealth_waiting_room.find({}, {"_id": 0}).sort("joined_at", 1).to_list(50)
        return [TelehealthWaitingRoom(**patient) for patient in waiting_patients]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving waiting room: {str(e)}")

# Chat and Communication
@api_router.post("/telehealth/sessions/{session_id}/chat")
async def send_chat_message(
    session_id: str, 
    message_data: Dict[str, Any], 
    current_user: User = Depends(get_current_active_user)
):
    """Send chat message during telehealth session"""
    try:
        # Create chat message
        chat_message = TelehealthChatMessage(
            session_id=session_id,
            sender_id=current_user.id if hasattr(current_user, 'id') else current_user.username,
            sender_name=getattr(current_user, 'full_name', current_user.username),
            sender_type=message_data.get("sender_type", "provider"),
            message=message_data["message"],
            message_type=message_data.get("message_type", "text"),
            is_private=message_data.get("is_private", False)
        )
        
        # Add message to session
        await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$push": {"chat_messages": jsonable_encoder(chat_message)}}
        )
        
        return chat_message
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending chat message: {str(e)}")

@api_router.get("/telehealth/sessions/{session_id}/chat")
async def get_chat_messages(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Get chat messages for telehealth session"""
    try:
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        messages = session.get("chat_messages", [])
        return [TelehealthChatMessage(**msg) for msg in messages]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat messages: {str(e)}")

# WebRTC Signaling Support
@api_router.post("/telehealth/signaling")
async def handle_webrtc_signal(signal_data: Dict[str, Any], current_user: User = Depends(get_current_active_user)):
    """Handle WebRTC signaling for video calls"""
    try:
        signal = WebRTCSignal(
            session_id=signal_data["session_id"],
            from_user_id=signal_data["from_user_id"],
            to_user_id=signal_data["to_user_id"],
            signal_type=signal_data["signal_type"],
            signal_data=signal_data["signal_data"]
        )
        
        # Store signal temporarily for real-time delivery
        signal_dict = jsonable_encoder(signal)
        await db.webrtc_signals.insert_one(signal_dict)
        
        # In a production system, this would use WebSocket or Server-Sent Events
        # to deliver the signal to the target user in real-time
        
        return {"message": "Signal processed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing WebRTC signal: {str(e)}")

# Integration with Appointment System
@api_router.post("/appointments/{appointment_id}/convert-to-telehealth")
async def convert_appointment_to_telehealth(
    appointment_id: str, 
    telehealth_data: Dict[str, Any], 
    current_user: User = Depends(get_current_active_user)
):
    """Convert existing appointment to telehealth session"""
    try:
        # Get appointment
        appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Create telehealth session from appointment
        session_data = TelehealthSessionCreate(
            patient_id=appointment["patient_id"],
            provider_id=appointment["provider_id"],
            session_type=TelehealthSessionType(telehealth_data.get("session_type", "video_consultation")),
            title=f"Telehealth: {appointment.get('reason', appointment.get('appointment_type'))}",
            description=f"Converted from appointment {appointment['appointment_number']}",
            scheduled_start=datetime.combine(
                datetime.fromisoformat(appointment["appointment_date"]).date(),
                datetime.strptime(appointment["start_time"], "%H:%M").time()
            ),
            duration_minutes=appointment.get("duration_minutes", 30),
            appointment_id=appointment_id,
            recording_enabled=telehealth_data.get("recording_enabled", False)
        )
        
        # Create the telehealth session using the same logic as the main endpoint
        # Get patient details
        patient = await db.patients.find_one({"id": session_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_name = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
        
        # Get provider details
        provider = await db.providers.find_one({"id": session_data.provider_id}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        provider_name = f"{provider.get('title', 'Dr.')} {provider.get('first_name', '')} {provider.get('last_name', '')}".strip()
        
        # Calculate session end time
        scheduled_end = session_data.scheduled_start + timedelta(minutes=session_data.duration_minutes)
        
        # Generate room ID and session URL
        room_id = f"room_{session_data.patient_id}_{session_data.provider_id}_{int(datetime.utcnow().timestamp())}"
        session_url = f"/telehealth/room/{room_id}"
        
        # Create session
        session = TelehealthSession(
            patient_id=session_data.patient_id,
            patient_name=patient_name,
            provider_id=session_data.provider_id,
            provider_name=provider_name,
            session_type=session_data.session_type,
            title=session_data.title,
            description=session_data.description,
            scheduled_start=session_data.scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=session_data.duration_minutes,
            appointment_id=session_data.appointment_id,
            room_id=room_id,
            session_url=session_url,
            recording_enabled=session_data.recording_enabled,
            access_code=session_data.access_code,
            created_by=current_user.username
        )
        
        session_dict = jsonable_encoder(session)
        await db.telehealth_sessions.insert_one(session_dict)
        
        # Update appointment to indicate it's now a telehealth session
        await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": {
                "appointment_type": "telemedicine",
                "location": "Telehealth Session",
                "telehealth_session_id": session.id,
                "updated_at": jsonable_encoder(datetime.utcnow())
            }}
        )
        
        return {
            "message": "Appointment converted to telehealth session successfully",
            "telehealth_session_id": session.id,
            "session_number": session.session_number,
            "session_url": session.session_url,
            "appointment_updated": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting appointment to telehealth: {str(e)}")

# Patient Portal System API Endpoints
import hashlib
import secrets
import smtplib
# Email imports removed - not needed for current functionality

# Patient Portal Authentication
@api_router.post("/patient-portal/register")
async def register_patient_portal(registration_data: PatientPortalRegister):
    """Register a new patient portal account"""
    try:
        # Verify patient exists and data matches
        patient = await db.patients.find_one({"id": registration_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient record not found")
        
        # Verify date of birth matches
        patient_dob = patient.get("birth_date")
        if isinstance(patient_dob, str):
            patient_dob = datetime.fromisoformat(patient_dob).date()
        
        if patient_dob != registration_data.date_of_birth:
            raise HTTPException(status_code=400, detail="Date of birth does not match our records")
        
        # Check if username/email already exists
        existing_user = await db.patient_portal_users.find_one({
            "$or": [
                {"username": registration_data.username},
                {"email": registration_data.email}
            ]
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Validate password match
        if registration_data.password != registration_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Hash password
        password_hash = hashlib.sha256(registration_data.password.encode()).hexdigest()
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create portal user
        portal_user = PatientPortalUser(
            patient_id=registration_data.patient_id,
            username=registration_data.username,
            email=registration_data.email,
            password_hash=password_hash,
            verification_token=verification_token
        )
        
        portal_user_dict = jsonable_encoder(portal_user)
        await db.patient_portal_users.insert_one(portal_user_dict)
        
        # Create default preferences
        preferences = PatientPortalPreferences(patient_id=registration_data.patient_id)
        preferences_dict = jsonable_encoder(preferences)
        await db.patient_portal_preferences.insert_one(preferences_dict)
        
        # Log activity
        activity = PatientPortalActivity(
            patient_id=registration_data.patient_id,
            activity_type="registration",
            description="Patient portal account created"
        )
        activity_dict = jsonable_encoder(activity)
        await db.patient_portal_activities.insert_one(activity_dict)
        
        return {
            "message": "Patient portal account created successfully",
            "verification_required": True,
            "verification_token": verification_token  # In production, send via email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating patient portal account: {str(e)}")

@api_router.post("/patient-portal/login")
async def login_patient_portal(login_data: PatientPortalLogin):
    """Patient portal login"""
    try:
        # Find user
        portal_user = await db.patient_portal_users.find_one({
            "username": login_data.username,
            "is_active": True
        }, {"_id": 0})
        
        if not portal_user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Check if account is locked
        if portal_user.get("locked_until") and datetime.utcnow() < datetime.fromisoformat(portal_user["locked_until"]):
            raise HTTPException(status_code=423, detail="Account is temporarily locked due to too many failed attempts")
        
        # Verify password
        password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
        if portal_user["password_hash"] != password_hash:
            # Increment failed attempts
            await db.patient_portal_users.update_one(
                {"id": portal_user["id"]},
                {"$inc": {"login_attempts": 1}}
            )
            
            # Lock account after 5 failed attempts
            if portal_user.get("login_attempts", 0) >= 4:
                lock_until = datetime.utcnow() + timedelta(minutes=30)
                await db.patient_portal_users.update_one(
                    {"id": portal_user["id"]},
                    {"$set": {"locked_until": jsonable_encoder(lock_until)}}
                )
            
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Check if account is verified
        if not portal_user.get("is_verified", True):
            raise HTTPException(status_code=403, detail="Account not verified. Please check your email for verification instructions.")
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=8)
        
        # Create session
        session = PatientPortalSession(
            patient_id=portal_user["patient_id"],
            session_token=session_token,
            expires_at=expires_at
        )
        session_dict = jsonable_encoder(session)
        await db.patient_portal_sessions.insert_one(session_dict)
        
        # Update user login info
        await db.patient_portal_users.update_one(
            {"id": portal_user["id"]},
            {"$set": {
                "last_login": jsonable_encoder(datetime.utcnow()),
                "login_attempts": 0,
                "locked_until": None
            }}
        )
        
        # Log activity
        activity = PatientPortalActivity(
            patient_id=portal_user["patient_id"],
            activity_type="login",
            description="Patient logged into portal"
        )
        activity_dict = jsonable_encoder(activity)
        await db.patient_portal_activities.insert_one(activity_dict)
        
        # Get patient info
        patient = await db.patients.find_one({"id": portal_user["patient_id"]}, {"_id": 0})
        patient_info = {
            "id": patient["id"],
            "name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            "email": next((t["value"] for t in patient.get("telecom", []) if t.get("system") == "email"), ""),
            "phone": next((t["value"] for t in patient.get("telecom", []) if t.get("system") == "phone"), "")
        }
        
        return {
            "message": "Login successful",
            "access_token": session_token,
            "expires_at": expires_at.isoformat(),
            "patient": patient_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@api_router.post("/patient-portal/logout")
async def logout_patient_portal(session_token: str):
    """Patient portal logout"""
    try:
        # Invalidate session
        result = await db.patient_portal_sessions.delete_one({"session_token": session_token})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Logged out successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during logout: {str(e)}")

# Patient Portal Authentication Middleware
async def get_current_portal_patient(session_token: str):
    """Get current authenticated portal patient"""
    session = await db.patient_portal_sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": jsonable_encoder(datetime.utcnow())}
    }, {"_id": 0})
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    patient = await db.patients.find_one({"id": session["patient_id"]}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient

# Patient Medical Records Access
@api_router.get("/patient-portal/medical-records")
async def get_patient_medical_records(session_token: str):
    """Get patient's medical records"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        # Get recent appointments
        appointments = await db.appointments.find({
            "patient_id": patient_id,
            "status": {"$in": ["completed", "in_progress"]}
        }, {"_id": 0}).sort("appointment_date", -1).limit(10).to_list(10)
        
        # Get SOAP notes
        soap_notes = await db.soap_notes.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
        
        # Get vital signs
        vital_signs = await db.vital_signs.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("recorded_date", -1).limit(10).to_list(10)
        
        # Get medications
        medications = await db.medications.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).sort("start_date", -1).to_list(50)
        
        # Get allergies
        allergies = await db.allergies.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).sort("created_at", -1).to_list(50)
        
        # Get lab results (recent)
        lab_results = await db.lab_results.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("result_date", -1).limit(10).to_list(10)
        
        return {
            "patient_info": {
                "name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
                "date_of_birth": patient.get("birth_date"),
                "gender": patient.get("gender"),
                "phone": next((t["value"] for t in patient.get("telecom", []) if t.get("system") == "phone"), ""),
                "email": next((t["value"] for t in patient.get("telecom", []) if t.get("system") == "email"), "")
            },
            "recent_appointments": appointments,
            "soap_notes": soap_notes,
            "vital_signs": vital_signs,
            "current_medications": medications,
            "allergies": allergies,
            "recent_lab_results": lab_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving medical records: {str(e)}")

# Patient Appointment Management
@api_router.get("/patient-portal/appointments")
async def get_patient_appointments(session_token: str):
    """Get patient's appointments"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        # Get upcoming appointments
        upcoming_appointments = await db.appointments.find({
            "patient_id": patient_id,
            "appointment_date": {"$gte": date.today().isoformat()},
            "status": {"$nin": ["cancelled", "no_show"]}
        }, {"_id": 0}).sort("appointment_date", 1).to_list(20)
        
        # Get past appointments
        past_appointments = await db.appointments.find({
            "patient_id": patient_id,
            "appointment_date": {"$lt": date.today().isoformat()}
        }, {"_id": 0}).sort("appointment_date", -1).limit(20).to_list(20)
        
        return {
            "upcoming_appointments": upcoming_appointments,
            "past_appointments": past_appointments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving appointments: {str(e)}")

@api_router.post("/patient-portal/appointment-requests")
async def create_appointment_request(session_token: str, request_data: Dict[str, Any]):
    """Create appointment request"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        appointment_request = PatientAppointmentRequest(
            patient_id=patient_id,
            provider_id=request_data.get("provider_id"),
            appointment_type=request_data["appointment_type"],
            preferred_date=datetime.strptime(request_data["preferred_date"], "%Y-%m-%d").date(),
            preferred_time=request_data.get("preferred_time"),
            reason=request_data["reason"],
            urgency=request_data.get("urgency", "routine"),
            notes=request_data.get("notes")
        )
        
        request_dict = jsonable_encoder(appointment_request)
        await db.patient_appointment_requests.insert_one(request_dict)
        
        # Log activity
        activity = PatientPortalActivity(
            patient_id=patient_id,
            activity_type="appointment_request",
            description=f"Appointment request submitted for {request_data['preferred_date']}"
        )
        activity_dict = jsonable_encoder(activity)
        await db.patient_portal_activities.insert_one(activity_dict)
        
        return {
            "message": "Appointment request submitted successfully",
            "request_id": appointment_request.id,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appointment request: {str(e)}")

# Patient Messaging System
@api_router.get("/patient-portal/messages")
async def get_patient_messages(session_token: str):
    """Get patient's messages"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        messages = await db.patient_messages.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("created_at", -1).to_list(50)
        
        return {"messages": messages}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@api_router.post("/patient-portal/messages")
async def send_patient_message(session_token: str, message_data: Dict[str, Any]):
    """Send message from patient"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        message = PatientMessage(
            patient_id=patient_id,
            provider_id=message_data.get("provider_id"),
            subject=message_data["subject"],
            message=message_data["message"],
            message_type=message_data.get("message_type", "general"),
            priority=message_data.get("priority", "normal"),
            is_patient_sender=True
        )
        
        message_dict = jsonable_encoder(message)
        await db.patient_messages.insert_one(message_dict)
        
        # Log activity
        activity = PatientPortalActivity(
            patient_id=patient_id,
            activity_type="message_sent",
            description=f"Message sent: {message_data['subject']}"
        )
        activity_dict = jsonable_encoder(activity)
        await db.patient_portal_activities.insert_one(activity_dict)
        
        return {
            "message": "Message sent successfully",
            "message_id": message.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

# Patient Billing
@api_router.get("/patient-portal/billing")
async def get_patient_billing(session_token: str):
    """Get patient's billing information"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        # Get invoices
        invoices = await db.invoices.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("issue_date", -1).to_list(50)
        
        # Get financial transactions
        transactions = await db.financial_transactions.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("transaction_date", -1).to_list(50)
        
        # Calculate summary
        total_balance = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("status") not in ["paid", "cancelled"])
        total_paid = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("status") == "paid")
        
        return {
            "billing_summary": {
                "current_balance": total_balance,
                "total_paid_ytd": total_paid,
                "pending_invoices": len([i for i in invoices if i.get("status") == "sent"])
            },
            "invoices": invoices,
            "transactions": transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving billing information: {str(e)}")

# Prescription Refill Requests
@api_router.post("/patient-portal/prescription-refills")
async def create_refill_request(session_token: str, refill_data: Dict[str, Any]):
    """Create prescription refill request"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        refill_request = PrescriptionRefillRequest(
            patient_id=patient_id,
            original_prescription_id=refill_data.get("original_prescription_id"),
            medication_name=refill_data["medication_name"],
            dosage=refill_data["dosage"],
            quantity_requested=refill_data["quantity_requested"],
            pharmacy_name=refill_data.get("pharmacy_name"),
            pharmacy_phone=refill_data.get("pharmacy_phone"),
            reason=refill_data.get("reason"),
            urgency=refill_data.get("urgency", "routine")
        )
        
        request_dict = jsonable_encoder(refill_request)
        await db.prescription_refill_requests.insert_one(request_dict)
        
        # Log activity
        activity = PatientPortalActivity(
            patient_id=patient_id,
            activity_type="refill_request",
            description=f"Refill request for {refill_data['medication_name']}"
        )
        activity_dict = jsonable_encoder(activity)
        await db.patient_portal_activities.insert_one(activity_dict)
        
        return {
            "message": "Prescription refill request submitted successfully",
            "request_id": refill_request.id,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating refill request: {str(e)}")

# Patient Documents
@api_router.get("/patient-portal/documents")
async def get_patient_documents(session_token: str):
    """Get patient's documents"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        documents = await db.patient_documents.find({
            "patient_id": patient_id,
            "is_patient_accessible": True
        }, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return {"documents": documents}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

# Patient Telehealth Portal Access
@api_router.get("/patient-portal/telehealth-sessions")
async def get_patient_telehealth_sessions(session_token: str):
    """Get patient's telehealth sessions"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        sessions = await db.telehealth_sessions.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("scheduled_start", -1).to_list(20)
        
        return {"telehealth_sessions": sessions}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving telehealth sessions: {str(e)}")

@api_router.post("/patient-portal/telehealth-sessions/{session_id}/join")
async def join_telehealth_session_portal(session_id: str, session_token: str):
    """Join telehealth session from patient portal"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        # Verify session belongs to patient
        session = await db.telehealth_sessions.find_one({
            "id": session_id,
            "patient_id": patient_id
        }, {"_id": 0})
        
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Check if session is ready to join
        if session["status"] not in ["scheduled", "waiting", "in_progress"]:
            raise HTTPException(status_code=400, detail="Session is not available to join")
        
        # Add to waiting room if not already in progress
        if session["status"] == "scheduled":
            await db.telehealth_waiting_room.insert_one({
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "patient_id": patient_id,
                "patient_name": session["patient_name"],
                "joined_at": jsonable_encoder(datetime.utcnow()),
                "ready_to_join": True
            })
            
            # Update session status
            await db.telehealth_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "waiting"}}
            )
        
        return {
            "message": "Joined telehealth session successfully",
            "session_url": session.get("session_url"),
            "room_id": session.get("room_id"),
            "status": "waiting" if session["status"] == "scheduled" else session["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining telehealth session: {str(e)}")

# Patient Portal Preferences
@api_router.get("/patient-portal/preferences")
async def get_patient_preferences(session_token: str):
    """Get patient portal preferences"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        preferences = await db.patient_portal_preferences.find_one({
            "patient_id": patient_id
        }, {"_id": 0})
        
        if not preferences:
            # Create default preferences
            preferences = PatientPortalPreferences(patient_id=patient_id)
            preferences_dict = jsonable_encoder(preferences)
            await db.patient_portal_preferences.insert_one(preferences_dict)
            return preferences_dict
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving preferences: {str(e)}")

@api_router.put("/patient-portal/preferences")
async def update_patient_preferences(session_token: str, preferences_data: Dict[str, Any]):
    """Update patient portal preferences"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        preferences_data["updated_at"] = jsonable_encoder(datetime.utcnow())
        
        result = await db.patient_portal_preferences.update_one(
            {"patient_id": patient_id},
            {"$set": preferences_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        return {"message": "Preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

# Patient Portal Activity Log
@api_router.get("/patient-portal/activity")
async def get_patient_activity(session_token: str):
    """Get patient portal activity log"""
    try:
        patient = await get_current_portal_patient(session_token)
        patient_id = patient["id"]
        
        activities = await db.patient_portal_activities.find({
            "patient_id": patient_id
        }, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
        
        return {"activities": activities}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving activity log: {str(e)}")

# Lab Orders and Insurance Verification API Endpoints
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
import json

# External Service Integration Classes
class LabService:
    """Base class for lab service integration"""
    
    def __init__(self, config: ExternalServiceConfig):
        self.config = config
        self.session = None
    
    async def create_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def submit_order(self, lab_order: LabOrder) -> Dict[str, Any]:
        """Submit order to external lab - Mock implementation"""
        # In production, this would make actual API calls to LabCorp, Quest, etc.
        session = await self.create_session()
        
        # Mock response for testing
        mock_response = {
            "external_order_id": f"EXT-{lab_order.order_number}",
            "status": "accepted",
            "estimated_completion": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "specimen_collection_required": True,
            "collection_locations": [
                {"name": "Main Lab", "address": "123 Lab St", "phone": "555-0123"}
            ]
        }
        
        return mock_response
    
    async def get_results(self, external_order_id: str) -> List[Dict[str, Any]]:
        """Get results from external lab - Mock implementation"""
        # Mock lab results
        mock_results = [{
            "test_code": "33747-0",
            "test_name": "Complete Blood Count",
            "result_value": "Normal",
            "result_status": "final",
            "performed_date": datetime.utcnow().isoformat(),
            "reported_date": datetime.utcnow().isoformat()
        }]
        
        return mock_results

class InsuranceService:
    """Base class for insurance verification integration"""
    
    def __init__(self, config: ExternalServiceConfig):
        self.config = config
        self.session = None
    
    async def create_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def verify_eligibility(self, patient_id: str, insurance_policy: InsurancePolicy, service_codes: List[str]) -> Dict[str, Any]:
        """Verify insurance eligibility - Mock implementation"""
        # In production, this would integrate with Availity, Change Healthcare, etc.
        
        # Mock eligibility response
        mock_response = {
            "is_covered": True,
            "coverage_percentage": 80.0,
            "copay_amount": 25.0,
            "deductible_remaining": 500.0,
            "requires_prior_auth": False,
            "annual_limit": 10000.0,
            "visits_remaining": 20,
            "verification_successful": True,
            "external_transaction_id": f"TXN-{str(uuid.uuid4())[:8]}"
        }
        
        return mock_response

# Lab Orders API Endpoints
@api_router.get("/lab-tests", response_model=List[LabTest])
async def get_available_lab_tests(
    category: Optional[str] = None,
    lab_provider: Optional[LabProvider] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get available lab tests catalog"""
    try:
        query = {"is_active": True}
        
        if category:
            query["category"] = category
        if lab_provider:
            query["lab_provider"] = lab_provider.value
        if search:
            query["$or"] = [
                {"test_name": {"$regex": search, "$options": "i"}},
                {"test_code": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # If no tests exist, create some default ones
        test_count = await db.lab_tests.count_documents({"is_active": True})
        if test_count == 0:
            default_tests = [
                LabTest(
                    test_code="33747-0",
                    test_name="Complete Blood Count (CBC)",
                    description="Comprehensive blood panel",
                    category="hematology",
                    specimen_type="blood",
                    collection_method="venipuncture",
                    turnaround_time_hours=24,
                    cpt_code="85025"
                ),
                LabTest(
                    test_code="33743-4",
                    test_name="Basic Metabolic Panel",
                    description="Basic chemistry panel",
                    category="chemistry",
                    specimen_type="blood",
                    collection_method="venipuncture",
                    fasting_required=True,
                    turnaround_time_hours=12,
                    cpt_code="80048"
                ),
                LabTest(
                    test_code="33747-1",
                    test_name="Lipid Panel",
                    description="Cholesterol and triglycerides",
                    category="chemistry",
                    specimen_type="blood",
                    collection_method="venipuncture",
                    fasting_required=True,
                    turnaround_time_hours=24,
                    cpt_code="80061"
                )
            ]
            
            for test in default_tests:
                test_dict = jsonable_encoder(test)
                await db.lab_tests.insert_one(test_dict)
        
        tests = await db.lab_tests.find(query, {"_id": 0}).sort("test_name", 1).to_list(100)
        return [LabTest(**test) for test in tests]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab tests: {str(e)}")

@api_router.post("/lab-orders", response_model=LabOrder)
async def create_lab_order(lab_order_data: Dict[str, Any], current_user: User = Depends(get_current_active_user)):
    """Create new lab order"""
    try:
        # Get patient and provider details
        patient = await db.patients.find_one({"id": lab_order_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        provider = await db.providers.find_one({"id": lab_order_data["provider_id"]}, {"_id": 0})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Safely extract patient name
        patient_name = "Unknown Patient"
        if patient.get("name") and len(patient["name"]) > 0:
            name_obj = patient["name"][0]
            given_names = name_obj.get("given", [])
            family_name = name_obj.get("family", "")
            if given_names and family_name:
                patient_name = f"{given_names[0]} {family_name}"
            elif family_name:
                patient_name = family_name
            elif given_names:
                patient_name = given_names[0]
        
        # Safely extract provider name
        provider_name = "Unknown Provider"
        if provider.get("name"):
            provider_name = provider["name"]
        elif provider.get("first_name") or provider.get("last_name"):
            first_name = provider.get("first_name", "")
            last_name = provider.get("last_name", "")
            provider_name = f"{first_name} {last_name}".strip()
        elif provider.get("provider_name"):
            provider_name = provider["provider_name"]
        
        # Process tests data - handle both formats
        processed_tests = []
        for test_data in lab_order_data.get("tests", []):
            if isinstance(test_data, dict):
                processed_test = LabOrderItem(
                    test_id=test_data.get("test_id", str(uuid.uuid4())),
                    test_code=test_data.get("test_code", "UNKNOWN"),
                    test_name=test_data.get("test_name", "Unknown Test"),
                    quantity=test_data.get("quantity", 1),
                    specimen_type=test_data.get("specimen_type", "blood"),
                    collection_instructions=test_data.get("collection_instructions"),
                    fasting_required=test_data.get("fasting_required", False),
                    priority=LabOrderPriority(test_data.get("priority", "routine"))
                )
                processed_tests.append(processed_test)
        
        # Create lab order
        lab_order = LabOrder(
            patient_id=lab_order_data["patient_id"],
            patient_name=patient_name,
            provider_id=lab_order_data["provider_id"],
            provider_name=provider_name,
            tests=processed_tests,
            priority=LabOrderPriority(lab_order_data.get("priority", "routine")),
            clinical_info=lab_order_data.get("clinical_info"),
            diagnosis_codes=lab_order_data.get("diagnosis_codes", []),
            lab_provider=LabProvider(lab_order_data.get("lab_provider", "internal")),
            encounter_id=lab_order_data.get("encounter_id"),
            ordered_by=current_user.username
        )
        
        lab_order_dict = jsonable_encoder(lab_order)
        await db.lab_orders.insert_one(lab_order_dict)
        
        return lab_order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lab order: {str(e)}")

@api_router.get("/lab-orders", response_model=List[LabOrder])
async def get_lab_orders(
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    status: Optional[LabOrderStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get lab orders with filtering"""
    try:
        query = {}
        
        if patient_id:
            query["patient_id"] = patient_id
        if provider_id:
            query["provider_id"] = provider_id
        if status:
            query["status"] = status.value
        
        if start_date and end_date:
            query["created_at"] = {
                "$gte": jsonable_encoder(datetime.fromisoformat(start_date)),
                "$lte": jsonable_encoder(datetime.fromisoformat(end_date))
            }
        
        orders = await db.lab_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        return [LabOrder(**order) for order in orders]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab orders: {str(e)}")

@api_router.post("/lab-orders/{order_id}/submit")
async def submit_lab_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Submit lab order to external lab"""
    try:
        # Get lab order
        order = await db.lab_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Lab order not found")
        
        lab_order_obj = LabOrder(**order)
        
        # Get external service configuration
        service_config = ExternalServiceConfig(
            service_name="mock_lab_service",
            service_type="lab_orders",
            base_url="https://api.mocklabservice.com",
            api_key="mock_key"
        )
        
        # Submit to external lab
        lab_service = LabService(service_config)
        try:
            external_response = await lab_service.submit_order(lab_order_obj)
            
            # Update order with external information
            update_data = {
                "status": LabOrderStatus.ORDERED.value,
                "ordered_date": jsonable_encoder(datetime.utcnow()),
                "external_order_id": external_response.get("external_order_id"),
                "expected_completion": external_response.get("estimated_completion"),
                "external_system_data": external_response,
                "updated_at": jsonable_encoder(datetime.utcnow())
            }
            
            await db.lab_orders.update_one(
                {"id": order_id},
                {"$set": update_data}
            )
            
            return {
                "message": "Lab order submitted successfully",
                "external_order_id": external_response.get("external_order_id"),
                "status": "ordered"
            }
            
        finally:
            await lab_service.close_session()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting lab order: {str(e)}")

@api_router.post("/lab-orders/{order_id}/results")
async def retrieve_lab_results(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Retrieve lab results from external lab"""
    try:
        # Get lab order
        order = await db.lab_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Lab order not found")
        
        if not order.get("external_order_id"):
            raise HTTPException(status_code=400, detail="No external order ID found")
        
        # Get results from external lab
        service_config = ExternalServiceConfig(
            service_name="mock_lab_service",
            service_type="lab_orders",
            base_url="https://api.mocklabservice.com",
            api_key="mock_key"
        )
        
        lab_service = LabService(service_config)
        try:
            external_results = await lab_service.get_results(order["external_order_id"])
            
            # Create lab result records
            created_results = []
            for result_data in external_results:
                lab_result = LabResult(
                    lab_order_id=order_id,
                    test_id=str(uuid.uuid4()),
                    test_code=result_data["test_code"],
                    test_name=result_data["test_name"],
                    result_value=result_data.get("result_value"),
                    result_status=result_data.get("result_status", "final"),
                    performed_date=datetime.fromisoformat(result_data["performed_date"]),
                    reported_date=datetime.fromisoformat(result_data["reported_date"]),
                    performing_lab=order.get("lab_provider", "external"),
                    lab_provider=LabProvider(order.get("lab_provider", "internal"))
                )
                
                result_dict = jsonable_encoder(lab_result)
                await db.lab_results.insert_one(result_dict)
                created_results.append(lab_result)
            
            # Update order status
            await db.lab_orders.update_one(
                {"id": order_id},
                {"$set": {
                    "status": LabOrderStatus.RESULTED.value,
                    "results_available": True,
                    "completed_date": jsonable_encoder(datetime.utcnow()),
                    "updated_at": jsonable_encoder(datetime.utcnow())
                }}
            )
            
            return {
                "message": "Lab results retrieved successfully",
                "results_count": len(created_results),
                "results": [result.dict() for result in created_results]
            }
            
        finally:
            await lab_service.close_session()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab results: {str(e)}")

@api_router.get("/lab-results", response_model=List[LabResult])
async def get_lab_results(
    patient_id: Optional[str] = None,
    lab_order_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get lab results"""
    try:
        query = {}
        
        if lab_order_id:
            query["lab_order_id"] = lab_order_id
        elif patient_id:
            # Get lab orders for patient, then get results
            lab_orders = await db.lab_orders.find({"patient_id": patient_id}, {"_id": 0}).to_list(100)
            order_ids = [order["id"] for order in lab_orders]
            query["lab_order_id"] = {"$in": order_ids}
        
        results = await db.lab_results.find(query, {"_id": 0}).sort("reported_date", -1).to_list(100)
        return [LabResult(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab results: {str(e)}")

# Insurance Verification API Endpoints
@api_router.get("/insurance-plans", response_model=List[InsurancePlan])
async def get_insurance_plans(current_user: User = Depends(get_current_active_user)):
    """Get available insurance plans"""
    try:
        # Create default insurance plans if none exist
        plan_count = await db.insurance_plans.count_documents({"is_active": True})
        if plan_count == 0:
            default_plans = [
                InsurancePlan(
                    insurance_company="Blue Cross Blue Shield",
                    plan_name="BCBS PPO",
                    plan_type=InsuranceType.COMMERCIAL,
                    payer_id="BCBS001",
                    phone_number="1-800-BCBS-PPO",
                    network_type="PPO"
                ),
                InsurancePlan(
                    insurance_company="Aetna",
                    plan_name="Aetna Better Health",
                    plan_type=InsuranceType.COMMERCIAL,
                    payer_id="AETNA001",
                    phone_number="1-800-AETNA",
                    network_type="HMO",
                    requires_referrals=True
                ),
                InsurancePlan(
                    insurance_company="Medicare",
                    plan_name="Medicare Part B",
                    plan_type=InsuranceType.MEDICARE,
                    payer_id="MEDICARE",
                    phone_number="1-800-MEDICARE",
                    network_type="Medicare"
                )
            ]
            
            for plan in default_plans:
                plan_dict = jsonable_encoder(plan)
                await db.insurance_plans.insert_one(plan_dict)
        
        plans = await db.insurance_plans.find({"is_active": True}, {"_id": 0}).sort("insurance_company", 1).to_list(100)
        return [InsurancePlan(**plan) for plan in plans]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving insurance plans: {str(e)}")

@api_router.post("/insurance-policies", response_model=InsurancePolicy)
async def create_insurance_policy(policy_data: Dict[str, Any], current_user: User = Depends(get_current_active_user)):
    """Create insurance policy for patient"""
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": policy_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify insurance plan exists
        plan = await db.insurance_plans.find_one({"id": policy_data["insurance_plan_id"]}, {"_id": 0})
        if not plan:
            raise HTTPException(status_code=404, detail="Insurance plan not found")
        
        policy = InsurancePolicy(**policy_data)
        policy_dict = jsonable_encoder(policy)
        await db.insurance_policies.insert_one(policy_dict)
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating insurance policy: {str(e)}")

@api_router.post("/insurance-verification")
async def verify_insurance_eligibility(
    verification_request: InsuranceVerificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Verify insurance eligibility"""
    try:
        # Get patient and insurance policy
        patient = await db.patients.find_one({"id": verification_request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        policy = await db.insurance_policies.find_one({"id": verification_request.insurance_policy_id}, {"_id": 0})
        if not policy:
            raise HTTPException(status_code=404, detail="Insurance policy not found")
        
        policy_obj = InsurancePolicy(**policy)
        
        # Get insurance service configuration
        service_config = ExternalServiceConfig(
            service_name="mock_insurance_service",
            service_type="insurance_verification",
            base_url="https://api.mockinsurance.com",
            api_key="mock_key"
        )
        
        # Perform eligibility verification
        insurance_service = InsuranceService(service_config)
        try:
            verification_result = await insurance_service.verify_eligibility(
                verification_request.patient_id,
                policy_obj,
                verification_request.service_codes
            )
            
            # Create eligibility verification record
            eligibility_verification = EligibilityVerification(
                patient_id=verification_request.patient_id,
                insurance_policy_id=verification_request.insurance_policy_id,
                provider_id=verification_request.provider_npi or current_user.username,
                service_codes=verification_request.service_codes,
                status=VerificationStatus.VERIFIED if verification_result["verification_successful"] else VerificationStatus.ERROR,
                is_covered=verification_result.get("is_covered"),
                coverage_percentage=verification_result.get("coverage_percentage"),
                copay_amount=verification_result.get("copay_amount"),
                deductible_remaining=verification_result.get("deductible_remaining"),
                requires_prior_auth=verification_result.get("requires_prior_auth", False),
                annual_limit=verification_result.get("annual_limit"),
                visits_remaining=verification_result.get("visits_remaining"),
                external_transaction_id=verification_result.get("external_transaction_id"),
                raw_response_data=verification_result,
                verified_by=current_user.username
            )
            
            verification_dict = jsonable_encoder(eligibility_verification)
            await db.eligibility_verifications.insert_one(verification_dict)
            
            # Update insurance policy last verified date
            await db.insurance_policies.update_one(
                {"id": verification_request.insurance_policy_id},
                {"$set": {
                    "last_verified": jsonable_encoder(datetime.utcnow()),
                    "verification_status": eligibility_verification.status.value,
                    "updated_at": jsonable_encoder(datetime.utcnow())
                }}
            )
            
            return {
                "verification_id": eligibility_verification.id,
                "status": eligibility_verification.status.value,
                "is_covered": verification_result.get("is_covered"),
                "coverage_details": {
                    "coverage_percentage": verification_result.get("coverage_percentage"),
                    "copay_amount": verification_result.get("copay_amount"),
                    "deductible_remaining": verification_result.get("deductible_remaining"),
                    "requires_prior_auth": verification_result.get("requires_prior_auth"),
                    "annual_limit": verification_result.get("annual_limit"),
                    "visits_remaining": verification_result.get("visits_remaining")
                },
                "message": "Insurance eligibility verified successfully"
            }
            
        finally:
            await insurance_service.close_session()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying insurance eligibility: {str(e)}")

@api_router.get("/insurance-verifications")
async def get_insurance_verifications(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get insurance verification history"""
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        
        verifications = await db.eligibility_verifications.find(query, {"_id": 0}).sort("verification_date", -1).to_list(100)
        return verifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving insurance verifications: {str(e)}")

# Lab Integration API Endpoints

# Lab Tests Management
@api_router.post("/lab-tests/init")
async def initialize_lab_tests(current_user: User = Depends(get_current_active_user)):
    """Initialize common lab tests with LOINC codes"""
    try:
        existing = await db.lab_tests.count_documents({})
        if existing > 0:
            return {"message": "Lab tests already initialized", "count": existing}
        
        common_lab_tests = [
            {
                "id": str(uuid.uuid4()),
                "code": "718-7",
                "name": "Hemoglobin",
                "description": "Hemoglobin [Mass/volume] in Blood",
                "specimen_type": "blood",
                "reference_ranges": {
                    "male": "13.8-17.2 g/dL",
                    "female": "12.1-15.1 g/dL"
                },
                "critical_values": {"low": 7.0, "high": 20.0},
                "turnaround_time_hours": 2,
                "cost": 15.00,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "code": "33747-0", 
                "name": "Glucose",
                "description": "Glucose [Mass/volume] in Blood",
                "specimen_type": "blood",
                "reference_ranges": {
                    "fasting": "70-100 mg/dL",
                    "random": "70-140 mg/dL"
                },
                "critical_values": {"low": 40, "high": 400},
                "turnaround_time_hours": 1,
                "cost": 12.00,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "code": "2093-3",
                "name": "Cholesterol Total",
                "description": "Cholesterol [Mass/volume] in Serum or Plasma", 
                "specimen_type": "blood",
                "reference_ranges": {
                    "optimal": "<200 mg/dL",
                    "borderline": "200-239 mg/dL",
                    "high": "≥240 mg/dL"
                },
                "critical_values": {"low": 0, "high": 500},
                "turnaround_time_hours": 4,
                "cost": 20.00,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "code": "33762-6",
                "name": "TSH",
                "description": "Thyroid stimulating hormone [Units/volume] in Serum or Plasma",
                "specimen_type": "blood", 
                "reference_ranges": {
                    "normal": "0.27-4.20 mIU/L"
                },
                "critical_values": {"low": 0.01, "high": 100},
                "turnaround_time_hours": 24,
                "cost": 35.00,
                "is_active": True
            }
        ]
        
        await db.lab_tests.insert_many(common_lab_tests)
        
        return {
            "message": "Lab tests initialized successfully",
            "tests_added": len(common_lab_tests)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing lab tests: {str(e)}")

@api_router.get("/lab-tests")
async def get_lab_tests(current_user: User = Depends(get_current_active_user)):
    """Get all available lab tests"""
    try:
        tests = await db.lab_tests.find({"is_active": True}, {"_id": 0}).sort("name", 1).to_list(1000)
        # Remove MongoDB ObjectId
        for test in tests:
            if "_id" in test:
                del test["_id"]
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab tests: {str(e)}")

# Lab Orders Management (Duplicate endpoint removed - using comprehensive implementation above)

@api_router.get("/lab-orders")
async def get_lab_orders(
    patient_id: str = None,
    status: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get lab orders with optional filtering"""
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        
        orders = await db.lab_orders.find(query, {"_id": 0}).sort("ordered_at", -1).to_list(100)
        return [LabOrder(**order) for order in orders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab orders: {str(e)}")

@api_router.get("/lab-orders/{order_id}")
async def get_lab_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Get specific lab order details"""
    try:
        order = await db.lab_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Lab order not found")
        return LabOrder(**order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab order: {str(e)}")

# Lab Results Management
@api_router.post("/lab-results")
async def create_lab_result(result_data: dict, current_user: User = Depends(get_current_active_user)):
    """Create/receive lab results"""
    try:
        # Verify lab order exists
        order = await db.lab_orders.find_one({"id": result_data["lab_order_id"]}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Lab order not found")
        
        # Get test details for critical value checking
        test = await db.lab_tests.find_one({"code": result_data["test_code"]})
        
        # Check for critical values
        is_critical = False
        is_abnormal = False
        
        if test and result_data.get("numeric_value") is not None:
            critical_vals = test.get("critical_values", {})
            numeric_val = float(result_data["numeric_value"])
            
            if (critical_vals.get("low") and numeric_val <= critical_vals["low"]) or \
               (critical_vals.get("high") and numeric_val >= critical_vals["high"]):
                is_critical = True
                is_abnormal = True
        
        result_data["is_critical"] = is_critical
        result_data["is_abnormal"] = is_abnormal
        result_data["status"] = "critical" if is_critical else "final"
        
        lab_result = LabResult(**result_data)
        result_dict = jsonable_encoder(lab_result)
        await db.lab_results.insert_one(result_dict)
        
        # Update lab order status
        await db.lab_orders.update_one(
            {"id": result_data["lab_order_id"]},
            {"$set": {"status": "completed"}}
        )
        
        # Send critical value alert if needed
        if is_critical:
            await send_critical_value_alert(lab_result)
        
        return lab_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lab result: {str(e)}")

@api_router.get("/lab-results/patient/{patient_id}")
async def get_patient_lab_results(
    patient_id: str,
    test_code: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get lab results for a patient with optional filtering"""
    try:
        query = {"patient_id": patient_id}
        if test_code:
            query["test_code"] = test_code
        
        results = await db.lab_results.find(query, {"_id": 0}).sort("result_date", -1).to_list(100)
        return [LabResult(**result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab results: {str(e)}")

@api_router.get("/lab-results/trends/{patient_id}/{test_code}")
async def get_lab_trends(
    patient_id: str,
    test_code: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get trending data for a specific lab test"""
    try:
        results = await db.lab_results.find({
            "patient_id": patient_id,
            "test_code": test_code,
            "numeric_value": {"$exists": True}
        }).sort("result_date", 1).to_list(100)
        
        trend_data = []
        for result in results:
            trend_data.append({
                "date": result["result_date"].isoformat(),
                "value": result["numeric_value"],
                "unit": result.get("unit", ""),
                "is_abnormal": result.get("is_abnormal", False),
                "is_critical": result.get("is_critical", False)
            })
        
        return {
            "patient_id": patient_id,
            "test_code": test_code,
            "test_name": results[0]["test_name"] if results else "",
            "data": trend_data,
            "total_results": len(trend_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab trends: {str(e)}")

# Critical Value Alert Function
async def send_critical_value_alert(lab_result: LabResult):
    """Send alert for critical lab values"""
    try:
        # Get patient info
        patient = await db.patients.find_one({"id": lab_result.patient_id}, {"_id": 0})
        patient_name = "Unknown"
        if patient and patient.get("name"):
            name_obj = patient["name"][0] if isinstance(patient["name"], list) else patient["name"]
            given = name_obj.get("given", [""])[0] if name_obj.get("given") else ""
            family = name_obj.get("family", "")
            patient_name = f"{given} {family}".strip()
        
        # Create alert message
        alert_message = f"🚨 CRITICAL LAB VALUE ALERT\n\n" \
                       f"Patient: {patient_name}\n" \
                       f"Test: {lab_result.test_name}\n" \
                       f"Result: {lab_result.value}\n" \
                       f"Date: {lab_result.result_date}\n\n" \
                       f"Immediate physician review required!"
        
        # Mock alert system (in production, would integrate with paging/SMS)
        print(f"🚨 CRITICAL VALUE ALERT: {lab_result.test_name} = {lab_result.value} for patient {patient_name}")
        
        # Store alert in database
        await db.critical_alerts.insert_one({
            "id": str(uuid.uuid4()),
            "type": "critical_lab_value",
            "patient_id": lab_result.patient_id,
            "result_id": lab_result.id,
            "message": alert_message,
            "sent_at": datetime.utcnow(),
            "acknowledged": False
        })
        
    except Exception as e:
        print(f"Error sending critical value alert: {str(e)}")

# Insurance Verification & Eligibility API Endpoints

@api_router.post("/insurance/cards")
async def create_insurance_card(card_data: InsuranceCardV2Create, current_user: User = Depends(get_current_active_user)):
    """Add insurance card information for a patient"""
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": card_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Map V2 -> stored model; keep backward fields when available
        mapped = {
            "patient_id": card_data.patient_id,
            "payer_name": card_data.payer_name,
            "member_id": card_data.member_id,
            "group_number": card_data.group_number,
            "policy_number": None,
            "insurance_type": InsuranceType.COMMERCIAL,
            "payer_id": card_data.payer_name.upper().replace(" ", "_")[:12],
            "subscriber_name": ((patient.get('name') or [{}])[0].get('given',[""])[0] + ' ' + (patient.get('name') or [{}])[0].get('family','')).strip(),
            "subscriber_dob": (lambda bd: bd.isoformat() if isinstance(bd, date) else (bd if isinstance(bd, str) else date.today().isoformat()))(patient.get('birth_date')),
            "effective_date": (card_data.effective_date or date.today().isoformat()),
            "termination_date": None,
            "copay_primary": None,
            "copay_specialist": None,
            "deductible": None,
            "deductible_met": None,
            "out_of_pocket_max": None,
            "out_of_pocket_met": None,
            "is_primary": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        insurance_card = InsuranceCard(**mapped)
        card_dict = jsonable_encoder(insurance_card)
        await db.insurance_cards.insert_one(card_dict)

        # Audit: Insurance.CardCreated
        await create_audit_event(
            event_type="Insurance.CardCreated",
            resource_type="insurance",
            user_id=current_user.id,
            user_name=current_user.username,
            resource_id=insurance_card.id,
            action_details={"patient_id": insurance_card.patient_id, "payer_name": insurance_card.payer_name, "member_id": insurance_card.member_id},
            phi_accessed=True,
            success=True
        )
        
        return insurance_card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating insurance card: {str(e)}")

@api_router.get("/insurance/cards/patient/{patient_id}")
async def get_patient_insurance_cards(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get insurance cards for a patient"""
    try:
        cards = await db.insurance_cards.find({
            "patient_id": patient_id,
            "is_active": True
        }).sort("is_primary", -1).to_list(10)
        
        return [InsuranceCard(**card) for card in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving insurance cards: {str(e)}")

@api_router.post("/insurance/eligibility/check")
async def verify_eligibility(verification_data: EligibilityCheckRequest, current_user: User = Depends(get_current_active_user)):
    """Verify insurance eligibility (mock implementation)"""
    try:
        patient_id = verification_data.patient_id
        insurance_card_id = verification_data.card_id
        service_date = verification_data.service_date
        
        # Get patient and card
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=400, detail="Invalid patient_id")
        card = await db.insurance_cards.find_one({"id": insurance_card_id}, {"_id": 0})
        if not card:
            raise HTTPException(status_code=404, detail="Insurance card not found")
        
        # Use DI adapter
        try:
            if INSURANCE_ADAPTER == "mock":
                adapter_resp = await mock_eligibility_adapter(patient, card, verification_data)
            else:
                raise HTTPException(status_code=501, detail="Eligibility adapter not configured")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Eligibility adapter error: {str(e)}")

        # Persist eligibility (compatibility with existing EligibilityResponse)
        eligibility_doc = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "insurance_card_id": insurance_card_id,
            "eligibility_status": "active" if adapter_resp.eligible else "inactive",
            "benefits_summary": {},
            "copay_amounts": {},
            "deductible_info": {},
            "coverage_details": adapter_resp.coverage,
            "prior_auth_required": [],
            "checked_at": datetime.utcnow(),
            "valid_until": datetime.combine(datetime.strptime(adapter_resp.valid_until, "%Y-%m-%d").date(), datetime.min.time()),
            "raw_response": adapter_resp.raw,
        }
        await db.eligibility_responses.insert_one(jsonable_encoder(eligibility_doc))

        # Audit
        await create_audit_event(
            event_type="Insurance.EligibilityChecked",
            resource_type="insurance",
            user_id=current_user.id,
            user_name=current_user.username,
            resource_id=eligibility_doc["id"],
            action_details={"patient_id": patient_id, "card_id": insurance_card_id, "service_date": service_date},
            phi_accessed=True,
            success=True
        )

        # Response for API contract
        return adapter_resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying eligibility: {str(e)}")

@api_router.get("/insurance/eligibility/patient/{patient_id}")
async def get_patient_eligibility(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get recent eligibility verification for patient"""
    try:
        # Get most recent eligibility response
        eligibility = await db.eligibility_responses.find_one(
            {"patient_id": patient_id},
            sort=[("checked_at", -1)]
        )
        
        if not eligibility:
            return {"message": "No eligibility verification found", "patient_id": patient_id}
        
        return EligibilityResponse(**eligibility)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving eligibility: {str(e)}")

@api_router.post("/insurance/prior-auth")
async def create_prior_authorization(auth_data: dict, current_user: User = Depends(get_current_active_user)):
    """Create prior authorization request"""
    try:
        auth_data["submitted_by"] = current_user.username
        
        prior_auth = PriorAuthorization(**auth_data)
        auth_dict = jsonable_encoder(prior_auth)
        await db.prior_authorizations.insert_one(auth_dict)
        
        return prior_auth
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating prior authorization: {str(e)}")

@api_router.get("/insurance/prior-auth/patient/{patient_id}")
async def get_patient_prior_auths(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get prior authorizations for patient"""
    try:
        auths = await db.prior_authorizations.find({
            "patient_id": patient_id
        }).sort("requested_date", -1).to_list(50)
        
        return [PriorAuthorization(**auth) for auth in auths]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prior authorizations: {str(e)}")

# ICD-10 Diagnosis Codes Support
@api_router.post("/icd10/init")
async def initialize_icd10_codes(current_user: User = Depends(get_current_active_user)):
    """Initialize comprehensive ICD-10 diagnosis codes"""
    try:
        existing = await db.icd10_codes.count_documents({})
        if existing > 0:
            return {"message": "ICD-10 codes already initialized", "count": existing}
        
        # Comprehensive ICD-10 codes for primary care
        comprehensive_codes = [
            # Preventive Care
            {"code": "Z00.00", "description": "Encounter for general adult medical examination without abnormal findings", "category": "Preventive Care", "search_terms": ["physical", "checkup", "annual", "exam", "wellness"]},
            {"code": "Z00.01", "description": "Encounter for general adult medical examination with abnormal findings", "category": "Preventive Care", "search_terms": ["physical", "checkup", "annual", "exam", "abnormal"]},
            {"code": "Z00.121", "description": "Encounter for routine child health examination with abnormal findings", "category": "Preventive Care", "search_terms": ["child", "pediatric", "routine", "checkup"]},
            {"code": "Z00.129", "description": "Encounter for routine child health examination without abnormal findings", "category": "Preventive Care", "search_terms": ["child", "pediatric", "routine", "checkup"]},
            {"code": "Z12.31", "description": "Encounter for screening mammogram for malignant neoplasm of breast", "category": "Preventive Care", "search_terms": ["mammogram", "breast", "screening", "cancer"]},
            {"code": "Z12.11", "description": "Encounter for screening for malignant neoplasm of colon", "category": "Preventive Care", "search_terms": ["colonoscopy", "colon", "screening", "cancer"]},
            
            # Endocrine/Metabolic
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "category": "Endocrine", "search_terms": ["diabetes", "type 2", "dm", "blood sugar", "glucose"]},
            {"code": "E11.40", "description": "Type 2 diabetes mellitus with diabetic neuropathy, unspecified", "category": "Endocrine", "search_terms": ["diabetes", "neuropathy", "nerve", "tingling"]},
            {"code": "E11.319", "description": "Type 2 diabetes mellitus with unspecified diabetic nephropathy", "category": "Endocrine", "search_terms": ["diabetes", "kidney", "nephropathy", "renal"]},
            {"code": "E11.3213", "description": "Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema, bilateral", "category": "Endocrine", "search_terms": ["diabetes", "retinopathy", "eye", "vision"]},
            {"code": "E10.9", "description": "Type 1 diabetes mellitus without complications", "category": "Endocrine", "search_terms": ["diabetes", "type 1", "insulin", "juvenile"]},
            {"code": "E78.5", "description": "Hyperlipidemia, unspecified", "category": "Endocrine", "search_terms": ["cholesterol", "lipids", "hyperlipidemia", "dyslipidemia"]},
            {"code": "E78.0", "description": "Pure hypercholesterolemia", "category": "Endocrine", "search_terms": ["cholesterol", "high cholesterol", "hypercholesterolemia"]},
            {"code": "E66.9", "description": "Obesity, unspecified", "category": "Endocrine", "search_terms": ["obesity", "overweight", "weight", "bmi"]},
            {"code": "E03.9", "description": "Hypothyroidism, unspecified", "category": "Endocrine", "search_terms": ["hypothyroid", "thyroid", "underactive", "tsh"]},
            {"code": "E05.90", "description": "Thyrotoxicosis, unspecified without thyrotoxic crisis", "category": "Endocrine", "search_terms": ["hyperthyroid", "thyroid", "overactive", "thyrotoxicosis"]},
            
            # Cardiovascular
            {"code": "I10", "description": "Essential hypertension", "category": "Cardiovascular", "search_terms": ["hypertension", "high blood pressure", "htn", "bp"]},
            {"code": "I25.10", "description": "Atherosclerotic heart disease of native coronary artery without angina pectoris", "category": "Cardiovascular", "search_terms": ["coronary", "heart disease", "atherosclerosis", "cad"]},
            {"code": "I25.111", "description": "Atherosclerotic heart disease of native coronary artery with angina pectoris with documented spasm", "category": "Cardiovascular", "search_terms": ["angina", "chest pain", "coronary", "heart"]},
            {"code": "I48.91", "description": "Unspecified atrial fibrillation", "category": "Cardiovascular", "search_terms": ["atrial fibrillation", "afib", "irregular", "rhythm"]},
            {"code": "I50.9", "description": "Heart failure, unspecified", "category": "Cardiovascular", "search_terms": ["heart failure", "chf", "congestive", "shortness"]},
            {"code": "I73.9", "description": "Peripheral vascular disease, unspecified", "category": "Cardiovascular", "search_terms": ["peripheral", "vascular", "circulation", "pvd"]},
            {"code": "I83.90", "description": "Asymptomatic varicose veins of unspecified lower extremity", "category": "Cardiovascular", "search_terms": ["varicose", "veins", "legs", "spider"]},
            
            # Respiratory
            {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified", "category": "Respiratory", "search_terms": ["upper respiratory", "uri", "cold", "congestion"]},
            {"code": "J44.1", "description": "Chronic obstructive pulmonary disease with acute exacerbation", "category": "Respiratory", "search_terms": ["copd", "emphysema", "chronic", "breathing"]},
            {"code": "J44.0", "description": "Chronic obstructive pulmonary disease with acute lower respiratory infection", "category": "Respiratory", "search_terms": ["copd", "emphysema", "infection", "breathing"]},
            {"code": "J45.9", "description": "Asthma, unspecified", "category": "Respiratory", "search_terms": ["asthma", "wheezing", "breathing", "bronchospasm"]},
            {"code": "J18.9", "description": "Pneumonia, unspecified organism", "category": "Respiratory", "search_terms": ["pneumonia", "lung infection", "chest infection"]},
            {"code": "J20.9", "description": "Acute bronchitis, unspecified", "category": "Respiratory", "search_terms": ["bronchitis", "acute", "cough", "chest"]},
            {"code": "J32.9", "description": "Chronic sinusitis, unspecified", "category": "Respiratory", "search_terms": ["sinusitis", "chronic", "sinus", "nasal"]},
            {"code": "J01.90", "description": "Acute sinusitis, unspecified", "category": "Respiratory", "search_terms": ["sinusitis", "acute", "sinus", "nasal"]},
            
            # Musculoskeletal
            {"code": "M79.3", "description": "Panniculitis, unspecified", "category": "Musculoskeletal", "search_terms": ["panniculitis", "inflammation", "fat", "tissue"]},
            {"code": "M25.50", "description": "Pain in unspecified joint", "category": "Musculoskeletal", "search_terms": ["joint pain", "arthralgia", "ache", "stiffness"]},
            {"code": "M54.5", "description": "Low back pain", "category": "Musculoskeletal", "search_terms": ["back pain", "lumbar", "lower back", "lumbago"]},
            {"code": "M54.2", "description": "Cervicalgia", "category": "Musculoskeletal", "search_terms": ["neck pain", "cervical", "cervicalgia", "stiff neck"]},
            {"code": "M19.90", "description": "Unspecified osteoarthritis, unspecified site", "category": "Musculoskeletal", "search_terms": ["osteoarthritis", "arthritis", "joint", "degenerative"]},
            {"code": "M06.9", "description": "Rheumatoid arthritis, unspecified", "category": "Musculoskeletal", "search_terms": ["rheumatoid", "arthritis", "autoimmune", "ra"]},
            {"code": "M70.03", "description": "Crepitant synovitis (acute) (chronic) of wrist", "category": "Musculoskeletal", "search_terms": ["synovitis", "wrist", "inflammation", "joint"]},
            {"code": "M75.30", "description": "Calcific tendinitis of unspecified shoulder", "category": "Musculoskeletal", "search_terms": ["tendinitis", "shoulder", "calcific", "pain"]},
            
            # Mental Health
            {"code": "F32.9", "description": "Major depressive disorder, single episode, unspecified", "category": "Mental Health", "search_terms": ["depression", "depressive", "mood", "sad"]},
            {"code": "F33.9", "description": "Major depressive disorder, recurrent, unspecified", "category": "Mental Health", "search_terms": ["depression", "recurrent", "chronic", "mood"]},
            {"code": "F41.9", "description": "Anxiety disorder, unspecified", "category": "Mental Health", "search_terms": ["anxiety", "anxious", "worry", "panic"]},
            {"code": "F41.0", "description": "Panic disorder [episodic paroxysmal anxiety] without agoraphobia", "category": "Mental Health", "search_terms": ["panic", "anxiety", "attack", "episode"]},
            {"code": "F43.10", "description": "Post-traumatic stress disorder, unspecified", "category": "Mental Health", "search_terms": ["ptsd", "trauma", "stress", "flashback"]},
            {"code": "F90.9", "description": "Attention-deficit hyperactivity disorder, unspecified type", "category": "Mental Health", "search_terms": ["adhd", "attention", "hyperactivity", "deficit"]},
            
            # Gastrointestinal
            {"code": "K21.9", "description": "Gastro-esophageal reflux disease without esophagitis", "category": "Gastrointestinal", "search_terms": ["gerd", "reflux", "heartburn", "acid"]},
            {"code": "K59.00", "description": "Constipation, unspecified", "category": "Gastrointestinal", "search_terms": ["constipation", "bowel", "stool", "hard"]},
            {"code": "K58.9", "description": "Irritable bowel syndrome without diarrhea", "category": "Gastrointestinal", "search_terms": ["ibs", "irritable", "bowel", "abdominal"]},
            {"code": "K29.70", "description": "Gastritis, unspecified, without bleeding", "category": "Gastrointestinal", "search_terms": ["gastritis", "stomach", "inflammation", "pain"]},
            {"code": "K80.20", "description": "Calculus of gallbladder without cholecystitis without obstruction", "category": "Gastrointestinal", "search_terms": ["gallstones", "gallbladder", "calculus", "stone"]},
            {"code": "K92.2", "description": "Gastrointestinal hemorrhage, unspecified", "category": "Gastrointestinal", "search_terms": ["gi bleed", "bleeding", "hemorrhage", "blood"]},
            
            # Genitourinary
            {"code": "N39.0", "description": "Urinary tract infection, site not specified", "category": "Genitourinary", "search_terms": ["uti", "urinary", "infection", "bladder"]},
            {"code": "N18.6", "description": "End stage renal disease", "category": "Genitourinary", "search_terms": ["kidney", "renal", "esrd", "failure"]},
            {"code": "N18.3", "description": "Chronic kidney disease, stage 3 (moderate)", "category": "Genitourinary", "search_terms": ["kidney", "renal", "ckd", "chronic"]},
            {"code": "N40.1", "description": "Enlarged prostate with lower urinary tract symptoms", "category": "Genitourinary", "search_terms": ["prostate", "enlarged", "bph", "urinary"]},
            {"code": "N92.0", "description": "Excessive and frequent menstruation with regular cycle", "category": "Genitourinary", "search_terms": ["menorrhagia", "heavy", "period", "bleeding"]},
            
            # Symptoms and Signs
            {"code": "R06.02", "description": "Shortness of breath", "category": "Symptoms", "search_terms": ["shortness", "breath", "dyspnea", "sob"]},
            {"code": "R50.9", "description": "Fever, unspecified", "category": "Symptoms", "search_terms": ["fever", "temperature", "pyrexia", "hot"]},
            {"code": "R06.00", "description": "Dyspnea, unspecified", "category": "Symptoms", "search_terms": ["dyspnea", "breathing", "shortness", "air"]},
            {"code": "R51", "description": "Headache", "category": "Symptoms", "search_terms": ["headache", "head pain", "cephalgia", "migraine"]},
            {"code": "R11.10", "description": "Vomiting, unspecified", "category": "Symptoms", "search_terms": ["vomiting", "nausea", "throw up", "emesis"]},
            {"code": "R19.7", "description": "Diarrhea, unspecified", "category": "Symptoms", "search_terms": ["diarrhea", "loose", "stool", "bowel"]},
            {"code": "R42", "description": "Dizziness and giddiness", "category": "Symptoms", "search_terms": ["dizziness", "dizzy", "vertigo", "lightheaded"]},
            {"code": "R53.83", "description": "Fatigue", "category": "Symptoms", "search_terms": ["fatigue", "tired", "exhausted", "weakness"]},
            {"code": "R10.9", "description": "Unspecified abdominal pain", "category": "Symptoms", "search_terms": ["abdominal", "stomach", "belly", "pain"]},
            
            # Dermatology
            {"code": "L30.9", "description": "Dermatitis, unspecified", "category": "Dermatology", "search_terms": ["dermatitis", "rash", "skin", "inflammation"]},
            {"code": "L20.9", "description": "Atopic dermatitis, unspecified", "category": "Dermatology", "search_terms": ["eczema", "atopic", "dermatitis", "itchy"]},
            {"code": "L40.9", "description": "Psoriasis, unspecified", "category": "Dermatology", "search_terms": ["psoriasis", "plaque", "scaling", "skin"]},
            {"code": "L29.9", "description": "Pruritus, unspecified", "category": "Dermatology", "search_terms": ["itching", "pruritus", "itch", "scratching"]},
            {"code": "L02.90", "description": "Cutaneous abscess, unspecified", "category": "Dermatology", "search_terms": ["abscess", "boil", "pus", "infection"]},
            
            # Injury and Poisoning
            {"code": "S72.001A", "description": "Fracture of unspecified part of neck of right femur, initial encounter", "category": "Injury", "search_terms": ["fracture", "femur", "hip", "break"]},
            {"code": "S06.0X0A", "description": "Concussion without loss of consciousness, initial encounter", "category": "Injury", "search_terms": ["concussion", "head", "injury", "brain"]},
            {"code": "S93.401A", "description": "Sprain of unspecified ligament of right ankle, initial encounter", "category": "Injury", "search_terms": ["sprain", "ankle", "ligament", "twist"]},
            {"code": "T78.40XA", "description": "Allergy, unspecified, initial encounter", "category": "Injury", "search_terms": ["allergy", "allergic", "reaction", "hypersensitivity"]},
            
            # Infectious Diseases
            {"code": "A09", "description": "Infectious gastroenteritis and colitis, unspecified", "category": "Infectious", "search_terms": ["gastroenteritis", "food poisoning", "stomach bug", "diarrhea"]},
            {"code": "B34.9", "description": "Viral infection, unspecified", "category": "Infectious", "search_terms": ["viral", "virus", "infection", "bug"]},
            {"code": "A46", "description": "Erysipelas", "category": "Infectious", "search_terms": ["erysipelas", "cellulitis", "skin infection", "strep"]},
            {"code": "B37.9", "description": "Candidiasis, unspecified", "category": "Infectious", "search_terms": ["candidiasis", "yeast", "thrush", "fungal"]},
            
            # Pregnancy and Childbirth
            {"code": "Z34.00", "description": "Encounter for supervision of normal first pregnancy, unspecified trimester", "category": "Pregnancy", "search_terms": ["pregnancy", "prenatal", "antepartum", "supervision"]},
            {"code": "O09.90", "description": "Supervision of high risk pregnancy, unspecified, unspecified trimester", "category": "Pregnancy", "search_terms": ["high risk", "pregnancy", "supervision", "prenatal"]},
            {"code": "Z37.0", "description": "Single live birth", "category": "Pregnancy", "search_terms": ["delivery", "birth", "newborn", "live"]},
            
            # Neoplasms
            {"code": "C50.911", "description": "Malignant neoplasm of unspecified site of right female breast", "category": "Neoplasm", "search_terms": ["breast cancer", "malignant", "neoplasm", "carcinoma"]},
            {"code": "C78.00", "description": "Secondary malignant neoplasm of unspecified lung", "category": "Neoplasm", "search_terms": ["lung cancer", "secondary", "metastatic", "malignant"]},
            {"code": "C25.9", "description": "Malignant neoplasm of pancreas, unspecified", "category": "Neoplasm", "search_terms": ["pancreatic cancer", "pancreas", "malignant", "neoplasm"]},
            {"code": "D12.6", "description": "Benign neoplasm of colon, unspecified", "category": "Neoplasm", "search_terms": ["colon polyp", "benign", "neoplasm", "polyp"]},
            
            # Other Common Conditions
            {"code": "H10.9", "description": "Unspecified conjunctivitis", "category": "Ophthalmology", "search_terms": ["conjunctivitis", "pink eye", "red eye", "infection"]},
            {"code": "H61.23", "description": "Impacted cerumen, bilateral", "category": "Otolaryngology", "search_terms": ["ear wax", "cerumen", "impacted", "blocked"]},
            {"code": "H65.90", "description": "Unspecified nonsuppurative otitis media, unspecified ear", "category": "Otolaryngology", "search_terms": ["otitis media", "ear infection", "middle ear", "fluid"]},
            {"code": "H66.90", "description": "Otitis media, unspecified, unspecified ear", "category": "Otolaryngology", "search_terms": ["otitis media", "ear infection", "middle ear", "pain"]},
            {"code": "M62.830", "description": "Muscle spasm of back", "category": "Musculoskeletal", "search_terms": ["muscle spasm", "back spasm", "cramp", "tightness"]},
            {"code": "G43.909", "description": "Migraine, unspecified, not intractable, without status migrainosus", "category": "Neurology", "search_terms": ["migraine", "headache", "severe", "throbbing"]},
            {"code": "G47.00", "description": "Insomnia, unspecified", "category": "Neurology", "search_terms": ["insomnia", "sleeplessness", "sleep", "trouble"]},
            {"code": "F17.210", "description": "Nicotine dependence, cigarettes, uncomplicated", "category": "Substance Use", "search_terms": ["smoking", "tobacco", "nicotine", "cigarettes"]},
            {"code": "F10.10", "description": "Alcohol abuse, uncomplicated", "category": "Substance Use", "search_terms": ["alcohol", "abuse", "drinking", "dependence"]},
            {"code": "Z71.3", "description": "Dietary counseling and surveillance", "category": "Counseling", "search_terms": ["diet", "nutrition", "counseling", "weight"]},
            {"code": "Z23", "description": "Encounter for immunization", "category": "Preventive Care", "search_terms": ["vaccination", "immunization", "vaccine", "shot"]},
            {"code": "Z51.11", "description": "Encounter for antineoplastic chemotherapy", "category": "Treatment", "search_terms": ["chemotherapy", "cancer", "treatment", "chemo"]},
            {"code": "Z79.01", "description": "Long term (current) use of anticoagulants", "category": "Medication", "search_terms": ["anticoagulant", "blood thinner", "warfarin", "long term"]},
            {"code": "Z79.4", "description": "Long term (current) use of insulin", "category": "Medication", "search_terms": ["insulin", "diabetes", "long term", "injection"]},
            {"code": "Z87.891", "description": "Personal history of nicotine dependence", "category": "History", "search_terms": ["smoking", "tobacco", "history", "former"]},
            {"code": "Z91.19", "description": "Patient's noncompliance with other medical treatment and regimen", "category": "Factors", "search_terms": ["noncompliance", "adherence", "medication", "treatment"]}
        ]
        
        # Add IDs to codes
        for code in comprehensive_codes:
            code["id"] = str(uuid.uuid4())
        
        await db.icd10_codes.insert_many(comprehensive_codes)
        
        return {
            "message": "Comprehensive ICD-10 codes initialized successfully",
            "codes_added": len(comprehensive_codes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing ICD-10 codes: {str(e)}")

@api_router.get("/icd10/comprehensive")
async def get_comprehensive_icd10_codes(
    category: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """Get all ICD-10 codes with optional category filtering"""
    try:
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        codes = await db.icd10_codes.find(query, {"_id": 0}).limit(limit).to_list(limit)
        
        return codes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ICD-10 codes: {str(e)}")

@api_router.get("/icd10/search")
async def search_icd10_codes(
    query: str,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """Search ICD-10 codes by description, code, or search terms with fuzzy matching"""
    try:
        # Enhanced search query with multiple fields and fuzzy matching
        search_query = {
            "$or": [
                {"description": {"$regex": query, "$options": "i"}},
                {"code": {"$regex": query, "$options": "i"}},
                {"category": {"$regex": query, "$options": "i"}},
                {"search_terms": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Find exact matches first, then partial matches
        codes = await db.icd10_codes.find(search_query).limit(limit).to_list(limit)
        
        # Remove MongoDB ObjectId and add relevance scoring
        results = []
        for code in codes:
            if "_id" in code:
                del code["_id"]
            
            # Calculate relevance score for better sorting
            relevance_score = 0
            query_lower = query.lower()
            
            # Exact code match gets highest score
            if query_lower == code["code"].lower():
                relevance_score = 100
            # Code starts with query
            elif code["code"].lower().startswith(query_lower):
                relevance_score = 90
            # Description starts with query
            elif code["description"].lower().startswith(query_lower):
                relevance_score = 80
            # Search terms contain query
            elif any(term.lower().startswith(query_lower) for term in code.get("search_terms", [])):
                relevance_score = 70
            # Query found in description
            elif query_lower in code["description"].lower():
                relevance_score = 60
            # Query found in search terms
            elif any(query_lower in term.lower() for term in code.get("search_terms", [])):
                relevance_score = 50
            else:
                relevance_score = 30
            
            code["relevance_score"] = relevance_score
            results.append(code)
        
        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Remove relevance score from final results
        for result in results:
            del result["relevance_score"]
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching ICD-10 codes: {str(e)}")

# Include the router in the main app
# =====================================
# NEW MODULES: PYDANTIC MODELS
# =====================================

# 1. Referrals Management Models
class Referral(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    referring_provider_id: str
    referred_to_provider_name: str
    referred_to_specialty: str
    referred_to_phone: Optional[str] = None
    referred_to_fax: Optional[str] = None
    reason_for_referral: str
    diagnosis_codes: List[str] = []
    urgency: str = "routine"  # routine, urgent, stat
    status: ReferralStatus = ReferralStatus.PENDING
    referral_date: datetime = Field(default_factory=datetime.now)
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None
    reports_received: List[Dict] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# 2. Clinical Templates & Protocols Models
class ClinicalTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    template_type: TemplateType
    specialty: Optional[str] = None
    condition: Optional[str] = None
    age_group: Optional[str] = None  # pediatric, adult, geriatric
    sections: List[Dict] = []  # template sections with fields
    protocols: List[Dict] = []  # associated protocols
    guidelines: Optional[str] = None
    evidence_level: Optional[str] = None
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ClinicalProtocol(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    condition: str
    steps: List[Dict] = []
    decision_points: List[Dict] = []
    medications: List[Dict] = []
    lab_tests: List[str] = []
    follow_up_instructions: str
    contraindications: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

# 3. Quality Measures & Reporting Models
class QualityMeasure(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    measure_id: str  # CMS measure ID
    name: str
    description: str
    measure_type: str  # process, outcome, structure
    population_criteria: Dict = {}
    numerator_criteria: Dict = {}
    denominator_criteria: Dict = {}
    exclusion_criteria: Dict = {}
    reporting_period: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

class PatientQualityMeasure(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    measure_id: str
    status: QualityMeasureStatus
    reporting_period: str
    numerator_met: bool = False
    denominator_eligible: bool = True
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    last_evaluated: datetime = Field(default_factory=datetime.now)
    next_due_date: Optional[datetime] = None
    interventions: List[Dict] = []

# 4. Patient Portal Models
class PatientPortalUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

class PatientMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: Optional[str] = None
    sender_type: str  # patient, provider, staff
    subject: str
    message: str
    message_type: str = "general"  # general, prescription_refill, appointment_request
    is_read: bool = False
    parent_message_id: Optional[str] = None
    attachments: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)

class PortalAppointmentRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: Optional[str] = None
    appointment_type: str
    preferred_dates: List[str] = []
    reason: str
    urgency: str = "routine"
    status: str = "pending"  # pending, approved, scheduled, denied
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# 5. Document Management Models
class DocumentCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    parent_category_id: Optional[str] = None
    retention_period_years: Optional[int] = None
    is_active: bool = True

class ClinicalDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    document_type: str
    category_id: str
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    provider_id: Optional[str] = None
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    content: Optional[str] = None  # base64 encoded file content
    tags: List[str] = []
    status: DocumentStatus = DocumentStatus.PENDING
    is_confidential: bool = False
    expiry_date: Optional[datetime] = None
    workflow_step: str = "uploaded"
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    version: int = 1
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# 6. Telehealth Models - Using comprehensive model defined earlier

class TelehealthSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    platform: str = "jitsi"  # jitsi, zoom, teams, custom
    auto_record: bool = False
    waiting_room_enabled: bool = True
    allow_patient_chat: bool = True
    session_timeout_minutes: int = 60
    require_patient_verification: bool = True
    enable_screen_sharing: bool = True
    quality_settings: Dict = {"video": "720p", "audio": "high"}
    notification_preferences: Dict = {}
    integration_settings: Dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# =====================================
# NEW MODULES: API ENDPOINTS
# =====================================

# 1. REFERRALS MANAGEMENT ENDPOINTS
@api_router.post("/referrals")
async def create_referral(referral: Referral):
    try:
        referral_dict = referral.dict()
        referral_dict["created_at"] = datetime.now()
        referral_dict["updated_at"] = datetime.now()
        
        result = await db.referrals.insert_one(referral_dict)
        if result.inserted_id:
            return {"id": referral.id, "message": "Referral created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create referral")
    except Exception as e:
        logger.error(f"Error creating referral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating referral: {str(e)}")

@api_router.get("/referrals")
async def get_referrals(status: Optional[str] = None, patient_id: Optional[str] = None):
    try:
        query = {}
        if status:
            query["status"] = status
        if patient_id:
            query["patient_id"] = patient_id
            
        referrals = []
        async for referral in db.referrals.find(query, {"_id": 0}).sort("created_at", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": referral["patient_id"]}, {"_id": 0})
            provider = await db.providers.find_one({"id": referral.get("referring_provider_id")}, {"_id": 0})
            
            referral["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            referral["referring_provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
            referrals.append(referral)
            
        return referrals
    except Exception as e:
        logger.error(f"Error fetching referrals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching referrals: {str(e)}")

@api_router.put("/referrals/{referral_id}/status")
async def update_referral_status(referral_id: str, status: str, notes: Optional[str] = None):
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        if notes:
            update_data["notes"] = notes
            
        result = await db.referrals.update_one(
            {"id": referral_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Referral not found")
            
        return {"message": "Referral status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating referral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating referral: {str(e)}")

@api_router.post("/referrals/{referral_id}/reports")
async def add_referral_report(referral_id: str, report_data: Dict):
    try:
        report = {
            "id": str(uuid.uuid4()),
            "report_date": datetime.now(),
            "report_type": report_data.get("report_type", "consultation_note"),
            "content": report_data.get("content", ""),
            "provider_name": report_data.get("provider_name", ""),
            "received_at": datetime.now()
        }
        
        result = await db.referrals.update_one(
            {"id": referral_id},
            {
                "$push": {"reports_received": report},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Referral not found")
            
        return {"message": "Report added successfully", "report_id": report["id"]}
    except Exception as e:
        logger.error(f"Error adding referral report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding report: {str(e)}")

@api_router.get("/referrals/{referral_id}")
async def get_referral_by_id(referral_id: str):
    try:
        referral = await db.referrals.find_one({"id": referral_id}, {"_id": 0})
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        # Get patient and provider names
        patient = await db.patients.find_one({"id": referral["patient_id"]}, {"_id": 0})
        provider = await db.providers.find_one({"id": referral.get("referring_provider_id")}, {"_id": 0})
        
        referral["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
        referral["referring_provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
        
        return referral
    except Exception as e:
        logger.error(f"Error fetching referral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching referral: {str(e)}")

@api_router.put("/referrals/{referral_id}")
async def update_referral(referral_id: str, update_data: Dict):
    try:
        update_data["updated_at"] = datetime.now()
        
        result = await db.referrals.update_one(
            {"id": referral_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Referral not found")
            
        # Get updated referral
        updated_referral = await db.referrals.find_one({"id": referral_id}, {"_id": 0})
        return updated_referral
    except Exception as e:
        logger.error(f"Error updating referral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating referral: {str(e)}")

@api_router.get("/referrals/patient/{patient_id}")
async def get_referrals_by_patient(patient_id: str):
    try:
        referrals = []
        async for referral in db.referrals.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": referral["patient_id"]}, {"_id": 0})
            provider = await db.providers.find_one({"id": referral.get("referring_provider_id")}, {"_id": 0})
            
            referral["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            referral["referring_provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
            referrals.append(referral)
            
        return referrals
    except Exception as e:
        logger.error(f"Error fetching patient referrals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching patient referrals: {str(e)}")

# 2. CLINICAL TEMPLATES & PROTOCOLS ENDPOINTS
@api_router.post("/clinical-templates")
async def create_clinical_template(template: ClinicalTemplate):
    try:
        template_dict = template.dict()
        result = await db.clinical_templates.insert_one(template_dict)
        if result.inserted_id:
            return {"id": template.id, "message": "Clinical template created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create template")
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@api_router.get("/clinical-templates")
async def get_clinical_templates(template_type: Optional[str] = None, specialty: Optional[str] = None):
    try:
        query = {"is_active": True}
        if template_type:
            query["template_type"] = template_type
        if specialty:
            query["specialty"] = specialty
            
        templates = []
        async for template in db.clinical_templates.find(query, {"_id": 0}).sort("name", 1):
            templates.append(template)
            
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@api_router.get("/clinical-templates/{template_id}")
async def get_clinical_template_by_id(template_id: str):
    try:
        template = await db.clinical_templates.find_one({"id": template_id}, {"_id": 0})
        if not template:
            raise HTTPException(status_code=404, detail="Clinical template not found")
        return template
    except Exception as e:
        logger.error(f"Error fetching template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")

@api_router.put("/clinical-templates/{template_id}")
async def update_clinical_template(template_id: str, update_data: Dict):
    try:
        update_data["updated_at"] = datetime.now()
        
        result = await db.clinical_templates.update_one(
            {"id": template_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Clinical template not found")
            
        # Get updated template
        updated_template = await db.clinical_templates.find_one({"id": template_id}, {"_id": 0})
        return updated_template
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")

@api_router.post("/clinical-templates/init")
async def init_clinical_templates():
    try:
        # Initialize some basic clinical templates
        templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "Diabetes Management Template",
                "template_type": "care_plan",
                "specialty": "Endocrinology",
                "condition": "Diabetes Mellitus Type 2",
                "age_group": "adult",
                "sections": [
                    {"name": "Assessment", "fields": ["HbA1c", "Blood Glucose", "Blood Pressure", "Weight"]},
                    {"name": "Management", "fields": ["Medications", "Diet Plan", "Exercise Plan"]},
                    {"name": "Monitoring", "fields": ["Follow-up Schedule", "Lab Tests"]}
                ],
                "protocols": [],
                "guidelines": "ADA Guidelines for Diabetes Management",
                "evidence_level": "A",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Hypertension Protocol",
                "template_type": "protocol",
                "specialty": "Cardiology",
                "condition": "Hypertension",
                "age_group": "adult",
                "sections": [
                    {"name": "Initial Assessment", "fields": ["Blood Pressure", "Risk Factors", "Target Organ Damage"]},
                    {"name": "Treatment Plan", "fields": ["Lifestyle Modifications", "Medications", "Monitoring"]}
                ],
                "protocols": [],
                "guidelines": "ACC/AHA Hypertension Guidelines",
                "evidence_level": "A",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        for template in templates:
            await db.clinical_templates.insert_one(template)
        
        return {"message": f"Initialized {len(templates)} clinical templates successfully"}
    except Exception as e:
        logger.error(f"Error initializing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing templates: {str(e)}")

@api_router.post("/clinical-protocols")
async def create_clinical_protocol(protocol: ClinicalProtocol):
    try:
        protocol_dict = protocol.dict()
        result = await db.clinical_protocols.insert_one(protocol_dict)
        if result.inserted_id:
            return {"id": protocol.id, "message": "Clinical protocol created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create protocol")
    except Exception as e:
        logger.error(f"Error creating protocol: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating protocol: {str(e)}")

@api_router.get("/clinical-protocols")
async def get_clinical_protocols(condition: Optional[str] = None):
    try:
        query = {"is_active": True}
        if condition:
            query["condition"] = {"$regex": condition, "$options": "i"}
            
        protocols = []
        async for protocol in db.clinical_protocols.find(query, {"_id": 0}).sort("name", 1):
            protocols.append(protocol)
            
        return protocols
    except Exception as e:
        logger.error(f"Error fetching protocols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching protocols: {str(e)}")

# 3. QUALITY MEASURES & REPORTING ENDPOINTS
@api_router.post("/quality-measures")
async def create_quality_measure(measure: QualityMeasure):
    try:
        measure_dict = measure.dict()
        result = await db.quality_measures.insert_one(measure_dict)
        if result.inserted_id:
            return {"id": measure.id, "message": "Quality measure created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create quality measure")
    except Exception as e:
        logger.error(f"Error creating quality measure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating quality measure: {str(e)}")

@api_router.get("/quality-measures")
async def get_quality_measures():
    try:
        measures = []
        async for measure in db.quality_measures.find({"is_active": True}, {"_id": 0}).sort("name", 1):
            measures.append(measure)
        return measures
    except Exception as e:
        logger.error(f"Error fetching quality measures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching quality measures: {str(e)}")

@api_router.get("/quality-measures/{measure_id}")
async def get_quality_measure_by_id(measure_id: str):
    try:
        measure = await db.quality_measures.find_one({"id": measure_id}, {"_id": 0})
        if not measure:
            raise HTTPException(status_code=404, detail="Quality measure not found")
        return measure
    except Exception as e:
        logger.error(f"Error fetching quality measure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching quality measure: {str(e)}")

@api_router.put("/quality-measures/{measure_id}")
async def update_quality_measure(measure_id: str, update_data: Dict):
    try:
        update_data["updated_at"] = datetime.now()
        
        result = await db.quality_measures.update_one(
            {"id": measure_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Quality measure not found")
            
        # Get updated measure
        updated_measure = await db.quality_measures.find_one({"id": measure_id}, {"_id": 0})
        return updated_measure
    except Exception as e:
        logger.error(f"Error updating quality measure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating quality measure: {str(e)}")

@api_router.post("/quality-measures/calculate")
async def calculate_quality_measures(patient_id: str, measure_ids: List[str] = None):
    try:
        # Mock calculation for demonstration
        calculations = []
        
        if measure_ids:
            for measure_id in measure_ids:
                measure = await db.quality_measures.find_one({"id": measure_id}, {"_id": 0})
                if measure:
                    calculations.append({
                        "measure_id": measure_id,
                        "measure_name": measure["name"],
                        "patient_id": patient_id,
                        "result": "passed",  # Mock result
                        "score": 85.5,
                        "calculated_at": datetime.now()
                    })
        else:
            # Calculate all active measures
            async for measure in db.quality_measures.find({"is_active": True}, {"_id": 0}):
                calculations.append({
                    "measure_id": measure["id"],
                    "measure_name": measure["name"],
                    "patient_id": patient_id,
                    "result": "passed",  # Mock result
                    "score": 85.5,
                    "calculated_at": datetime.now()
                })
        
        return {"patient_id": patient_id, "calculations": calculations}
    except Exception as e:
        logger.error(f"Error calculating quality measures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating quality measures: {str(e)}")

@api_router.get("/quality-measures/report")
async def get_quality_measures_report(start_date: str = None, end_date: str = None, measure_type: str = None):
    try:
        # Mock report generation
        report = {
            "report_period": {
                "start_date": start_date or datetime.now().replace(day=1).isoformat(),
                "end_date": end_date or datetime.now().isoformat()
            },
            "summary": {
                "total_measures": 5,
                "passed_measures": 4,
                "failed_measures": 1,
                "overall_score": 88.2
            },
            "measures": [
                {
                    "measure_name": "Diabetes HbA1c Control",
                    "measure_type": "clinical",
                    "numerator": 45,
                    "denominator": 50,
                    "percentage": 90.0,
                    "status": "passed"
                },
                {
                    "measure_name": "Blood Pressure Control",
                    "measure_type": "clinical", 
                    "numerator": 38,
                    "denominator": 42,
                    "percentage": 90.5,
                    "status": "passed"
                }
            ],
            "generated_at": datetime.now()
        }
        
        return report
    except Exception as e:
        logger.error(f"Error generating quality measures report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@api_router.post("/patient-quality-measures")
async def evaluate_patient_quality_measures(patient_id: str):
    try:
        # This would implement quality measure evaluation logic
        # For now, return a simple response
        return {"message": f"Quality measures evaluated for patient {patient_id}"}
    except Exception as e:
        logger.error(f"Error evaluating quality measures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating measures: {str(e)}")

@api_router.get("/quality-reports/dashboard")
async def get_quality_dashboard():
    try:
        # Get summary statistics
        total_measures = await db.quality_measures.count_documents({"is_active": True})
        total_patients = await db.patients.count_documents({"active": True})
        
        # Get recent quality assessments
        recent_assessments = []
        async for assessment in db.patient_quality_measures.find().sort("last_evaluated", -1).limit(10):
            patient = await db.patients.find_one({"id": assessment["patient_id"]}, {"_id": 0})
            measure = await db.quality_measures.find_one({"id": assessment["measure_id"]}, {"_id": 0})
            
            assessment["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            assessment["measure_name"] = measure["name"] if measure else "Unknown"
            recent_assessments.append(assessment)
        
        return {
            "total_measures": total_measures,
            "total_patients": total_patients,
            "recent_assessments": recent_assessments,
            "compliance_rate": 85.2  # This would be calculated
        }
    except Exception as e:
        logger.error(f"Error fetching quality dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")

# 4. PATIENT PORTAL ENDPOINTS
@api_router.post("/portal/register")
async def register_portal_user(user_data: Dict):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": user_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if portal user already exists
        existing_user = await db.portal_users.find_one({"patient_id": user_data["patient_id"]}, {"_id": 0})
        if existing_user:
            raise HTTPException(status_code=400, detail="Portal account already exists")
        
        # Hash password
        password_hash = pwd_context.hash(user_data["password"])
        
        portal_user = PatientPortalUser(
            patient_id=user_data["patient_id"],
            username=user_data["username"],
            email=user_data["email"],
            password_hash=password_hash
        )
        
        result = await db.portal_users.insert_one(portal_user.dict())
        if result.inserted_id:
            return {"id": portal_user.id, "message": "Portal account created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create portal account")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")

@api_router.post("/portal/login")
async def portal_login(login_data: Dict):
    try:
        user = await db.portal_users.find_one({"username": login_data["username"]})
        if not user or not pwd_context.verify(login_data["password"], user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user["is_active"]:
            raise HTTPException(status_code=401, detail="Account is inactive")
        
        # Update last login
        await db.portal_users.update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.now()}}
        )
        
        # Create JWT token
        token_data = {
            "sub": user["id"],
            "patient_id": user["patient_id"],
            "user_type": "patient",
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {"access_token": token, "token_type": "bearer", "patient_id": user["patient_id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during portal login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/portal/patient/{patient_id}/summary")
async def get_patient_portal_summary(patient_id: str):
    try:
        # Get patient basic info
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get recent encounters
        recent_encounters = []
        async for encounter in db.encounters.find({"patient_id": patient_id}, {"_id": 0}).sort("date", -1).limit(5):
            recent_encounters.append({
                "id": encounter["id"],
                "date": encounter["date"],
                "type": encounter.get("encounter_type", "Office Visit"),
                "provider": encounter.get("provider_name", ""),
                "chief_complaint": encounter.get("chief_complaint", "")
            })
        
        # Get upcoming appointments
        upcoming_appointments = []
        async for appointment in db.appointments.find({
            "patient_id": patient_id,
            "date": {"$gte": datetime.now().strftime("%Y-%m-%d")}
        }).sort("date", 1).limit(5):
            upcoming_appointments.append(appointment)
        
        # Get recent lab results
        recent_labs = []
        async for lab_order in db.lab_orders.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).limit(5):
            recent_labs.append({
                "id": lab_order["id"],
                "order_date": lab_order["created_at"],
                "status": lab_order.get("status", "pending"),
                "tests": lab_order.get("lab_tests", [])
            })
        
        return {
            "patient_info": {
                "name": f"{patient['name'][0]['given']} {patient['name'][0]['family']}",
                "dob": patient.get("birthDate", ""),
                "phone": patient.get("telecom", [{}])[0].get("value", "")
            },
            "recent_encounters": recent_encounters,
            "upcoming_appointments": upcoming_appointments,
            "recent_labs": recent_labs,
            "unread_messages": 0  # Would be calculated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portal summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")

@api_router.post("/portal/messages")
async def send_patient_message(message: PatientMessage):
    try:
        message_dict = message.dict()
        result = await db.patient_messages.insert_one(message_dict)
        if result.inserted_id:
            return {"id": message.id, "message": "Message sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@api_router.get("/portal/messages/patient/{patient_id}")
async def get_patient_messages(patient_id: str):
    try:
        messages = []
        async for message in db.patient_messages.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1):
            messages.append(message)
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

# Patient Portal endpoints with correct URL structure expected by testing
@api_router.post("/patient-portal")
async def create_patient_portal_access(portal_data: Dict):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": portal_data["patient_id"]}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create portal access record
        portal_access = {
            "id": str(uuid.uuid4()),
            "patient_id": portal_data["patient_id"],
            "access_level": portal_data.get("access_level", "full"),
            "features_enabled": portal_data.get("features_enabled", ["appointments", "records", "messages", "payments"]),
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await db.patient_portal_access.insert_one(portal_access)
        if result.inserted_id:
            return {"id": portal_access["id"], "message": "Patient portal access created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create portal access")
    except Exception as e:
        logger.error(f"Error creating portal access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating portal access: {str(e)}")

@api_router.get("/patient-portal")
async def get_patient_portal_access():
    try:
        portal_access_list = []
        async for access in db.patient_portal_access.find({"is_active": True}, {"_id": 0}).sort("created_at", -1):
            # Get patient name
            patient = await db.patients.find_one({"id": access["patient_id"]}, {"_id": 0})
            if patient:
                access["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}"
            else:
                access["patient_name"] = "Unknown"
            
            portal_access_list.append(access)
        
        return portal_access_list
    except Exception as e:
        logger.error(f"Error fetching portal access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching portal access: {str(e)}")

@api_router.get("/patient-portal/patient/{patient_id}")
async def get_patient_portal_for_patient(patient_id: str):
    try:
        # Get patient portal access
        portal_access = await db.patient_portal_access.find_one({"patient_id": patient_id, "is_active": True}, {"_id": 0})
        if not portal_access:
            raise HTTPException(status_code=404, detail="Patient portal access not found")
        
        # Get patient basic info
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if patient:
            portal_access["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}"
        
        return portal_access
    except Exception as e:
        logger.error(f"Error fetching patient portal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching patient portal: {str(e)}")

@api_router.post("/patient-portal/{portal_id}/schedule")
async def schedule_via_patient_portal(portal_id: str, appointment_data: Dict):
    try:
        # Verify portal access exists
        portal_access = await db.patient_portal_access.find_one({"id": portal_id}, {"_id": 0})
        if not portal_access:
            raise HTTPException(status_code=404, detail="Portal access not found")
        
        if "appointments" not in portal_access.get("features_enabled", []):
            raise HTTPException(status_code=403, detail="Appointment scheduling not enabled for this portal")
        
        # Create appointment request
        appointment_request = PortalAppointmentRequest(
            patient_id=portal_access["patient_id"],
            provider_id=appointment_data.get("provider_id"),
            appointment_type=appointment_data["appointment_type"],
            preferred_dates=appointment_data.get("preferred_dates", []),
            reason=appointment_data["reason"],
            urgency=appointment_data.get("urgency", "routine"),
            notes=appointment_data.get("notes")
        )
        
        result = await db.portal_appointment_requests.insert_one(appointment_request.dict())
        if result.inserted_id:
            return {"id": appointment_request.id, "message": "Appointment request submitted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit appointment request")
    except Exception as e:
        logger.error(f"Error scheduling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling appointment: {str(e)}")

@api_router.get("/patient-portal/{portal_id}/records")
async def get_patient_records_via_portal(portal_id: str):
    try:
        # Verify portal access exists
        portal_access = await db.patient_portal_access.find_one({"id": portal_id}, {"_id": 0})
        if not portal_access:
            raise HTTPException(status_code=404, detail="Portal access not found")
        
        if "records" not in portal_access.get("features_enabled", []):
            raise HTTPException(status_code=403, detail="Medical records access not enabled for this portal")
        
        patient_id = portal_access["patient_id"]
        
        # Get patient summary data
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get recent encounters
        encounters = []
        async for encounter in db.encounters.find({"patient_id": patient_id}, {"_id": 0}).sort("encounter_date", -1).limit(10):
            encounters.append(encounter)
        
        # Get medications
        medications = []
        async for med in db.medications.find({"patient_id": patient_id, "status": "active"}):
            medications.append(med)
        
        # Get allergies
        allergies = []
        async for allergy in db.allergies.find({"patient_id": patient_id}):
            allergies.append(allergy)
        
        # Get lab results (last 6 months)
        lab_results = []
        six_months_ago = datetime.now() - timedelta(days=180)
        async for lab in db.lab_orders.find({
            "patient_id": patient_id, 
            "status": "completed",
            "created_at": {"$gte": six_months_ago}
        }).sort("created_at", -1):
            lab_results.append(lab)
        
        return {
            "patient": patient,
            "encounters": encounters,
            "medications": medications,
            "allergies": allergies,
            "lab_results": lab_results
        }
    except Exception as e:
        logger.error(f"Error fetching patient records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching patient records: {str(e)}")

# 5. DOCUMENT MANAGEMENT ENDPOINTS
@api_router.post("/documents")
async def upload_document(document: ClinicalDocument):
    try:
        document_dict = document.dict()
        result = await db.clinical_documents.insert_one(document_dict)
        if result.inserted_id:
            return {"id": document.id, "message": "Document uploaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to upload document")
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@api_router.get("/documents")
async def get_documents(patient_id: Optional[str] = None, category_id: Optional[str] = None, status: Optional[str] = None):
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if category_id:
            query["category_id"] = category_id
        if status:
            query["status"] = status
            
        documents = []
        async for document in db.clinical_documents.find(query, {"_id": 0}).sort("created_at", -1):
            # Get category name
            category = await db.document_categories.find_one({"id": document.get("category_id")}, {"_id": 0})
            document["category_name"] = category["name"] if category else "Uncategorized"
            
            # Get patient name if applicable
            if document.get("patient_id"):
                patient = await db.patients.find_one({"id": document["patient_id"]}, {"_id": 0})
                document["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            
            documents.append(document)
            
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@api_router.get("/documents/{document_id}")
async def get_document_by_id(document_id: str):
    try:
        document = await db.clinical_documents.find_one({"id": document_id}, {"_id": 0})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get category name
        category = await db.document_categories.find_one({"id": document.get("category_id")}, {"_id": 0})
        document["category_name"] = category["name"] if category else "Uncategorized"
        
        # Get patient name if applicable
        if document.get("patient_id"):
            patient = await db.patients.find_one({"id": document["patient_id"]}, {"_id": 0})
            document["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
        
        return document
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching document: {str(e)}")

@api_router.put("/documents/{document_id}")
async def update_document(document_id: str, update_data: Dict):
    try:
        update_data["updated_at"] = datetime.now()
        
        result = await db.clinical_documents.update_one(
            {"id": document_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Get updated document
        updated_document = await db.clinical_documents.find_one({"id": document_id}, {"_id": 0})
        return updated_document
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@api_router.post("/documents/upload")
async def upload_document_file(file_data: Dict):
    try:
        # This would handle actual file upload logic
        # For now, creating a document record with file metadata
        document = ClinicalDocument(
            title=file_data["title"],
            document_type=file_data.get("document_type", "general"),
            patient_id=file_data.get("patient_id"),
            provider_id=file_data.get("provider_id"),
            category_id=file_data.get("category_id"),
            content=file_data.get("content", ""),
            file_name=file_data.get("file_name"),
            file_size=file_data.get("file_size", 0),
            mime_type=file_data.get("mime_type"),
            file_path="/uploads/documents/" + file_data.get("file_name", "unknown"),
            tags=file_data.get("tags", []),
            is_confidential=file_data.get("is_confidential", False)
        )
        
        document_dict = document.dict()
        result = await db.clinical_documents.insert_one(document_dict)
        if result.inserted_id:
            return {"id": document.id, "message": "Document uploaded successfully", "file_path": document.file_path}
        else:
            raise HTTPException(status_code=500, detail="Failed to upload document")
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@api_router.get("/documents/patient/{patient_id}")
async def get_documents_by_patient(patient_id: str):
    try:
        documents = []
        async for document in db.clinical_documents.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1):
            # Get category name
            category = await db.document_categories.find_one({"id": document.get("category_id")}, {"_id": 0})
            document["category_name"] = category["name"] if category else "Uncategorized"
            
            documents.append(document)
            
        return documents
    except Exception as e:
        logger.error(f"Error fetching patient documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching patient documents: {str(e)}")

@api_router.put("/documents/{document_id}/workflow")
async def update_document_workflow(document_id: str, workflow_data: Dict):
    try:
        # Update document workflow status
        update_data = {
            "workflow_status": workflow_data.get("workflow_status", "pending"),
            "workflow_stage": workflow_data.get("workflow_stage", "review"),
            "assigned_to": workflow_data.get("assigned_to"),
            "workflow_notes": workflow_data.get("workflow_notes", ""),
            "updated_at": datetime.now()
        }
        
        result = await db.clinical_documents.update_one(
            {"id": document_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return {"message": "Document workflow updated successfully"}
    except Exception as e:
        logger.error(f"Error updating document workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document workflow: {str(e)}")

@api_router.put("/documents/{document_id}/status")
async def update_document_status(document_id: str, status: str, notes: Optional[str] = None):
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        if notes:
            update_data["notes"] = notes
            
        result = await db.clinical_documents.update_one(
            {"id": document_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return {"message": "Document status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@api_router.get("/document-categories")
async def get_document_categories():
    try:
        categories = []
        async for category in db.document_categories.find({"is_active": True}, {"_id": 0}).sort("name", 1):
            categories.append(category)
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

# 6. TELEHEALTH ENDPOINTS
# Add endpoints with correct URL structure expected by testing
@api_router.post("/telehealth")
async def create_telehealth_session_v2(session: TelehealthSession):
    try:
        # Generate meeting URL and credentials (using Jitsi as default)
        meeting_id = f"clinichub-{session.patient_id}-{int(datetime.now().timestamp())}"
        meeting_url = f"https://meet.jit.si/{meeting_id}"
        
        session_dict = session.dict()
        session_dict["meeting_id"] = meeting_id
        session_dict["meeting_url"] = meeting_url
        session_dict["patient_join_url"] = f"{meeting_url}#config.prejoinPageEnabled=false"
        session_dict["provider_join_url"] = f"{meeting_url}#config.moderator=true"
        
        result = await db.telehealth_sessions.insert_one(session_dict)
        if result.inserted_id:
            return {
                "id": session.id, 
                "message": "Telehealth session created successfully",
                "meeting_url": meeting_url,
                "patient_join_url": session_dict["patient_join_url"],
                "provider_join_url": session_dict["provider_join_url"]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create session")
    except Exception as e:
        logger.error(f"Error creating telehealth session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@api_router.get("/telehealth")
async def get_telehealth_sessions_v2(patient_id: Optional[str] = None, provider_id: Optional[str] = None, status: Optional[str] = None):
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if provider_id:
            query["provider_id"] = provider_id
        if status:
            query["status"] = status
            
        sessions = []
        async for session in db.telehealth_sessions.find(query, {"_id": 0}).sort("scheduled_start", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": session["patient_id"]}, {"_id": 0})
            provider = await db.providers.find_one({"id": session["provider_id"]}, {"_id": 0})
            
            session["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            session["provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
            
            sessions.append(session)
            
        return sessions
    except Exception as e:
        logger.error(f"Error fetching telehealth sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@api_router.get("/telehealth/{session_id}")
async def get_telehealth_session_by_id(session_id: str):
    try:
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Get patient and provider names
        patient = await db.patients.find_one({"id": session["patient_id"]}, {"_id": 0})
        provider = await db.providers.find_one({"id": session["provider_id"]}, {"_id": 0})
        
        session["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
        session["provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
        
        return session
    except Exception as e:
        logger.error(f"Error fetching telehealth session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")

@api_router.put("/telehealth/{session_id}")
async def update_telehealth_session(session_id: str, update_data: Dict):
    try:
        update_data["updated_at"] = datetime.now()
        
        result = await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
            
        # Get updated session
        updated_session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        return updated_session
    except Exception as e:
        logger.error(f"Error updating telehealth session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")

@api_router.post("/telehealth/{session_id}/join")
async def join_telehealth_session(session_id: str, join_data: Dict):
    try:
        session = await db.telehealth_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        user_type = join_data.get("user_type", "patient")  # patient or provider
        
        # Update session status to active if joining
        if session["status"] == "scheduled":
            await db.telehealth_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "active", "actual_start": datetime.now()}}
            )
        
        # Return appropriate join URL
        if user_type == "provider":
            return {
                "join_url": session.get("provider_join_url", session["meeting_url"]),
                "meeting_id": session["meeting_id"],
                "session_id": session_id,
                "role": "moderator"
            }
        else:
            return {
                "join_url": session.get("patient_join_url", session["meeting_url"]),
                "meeting_id": session["meeting_id"],
                "session_id": session_id,
                "role": "participant"
            }
    except Exception as e:
        logger.error(f"Error joining telehealth session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error joining session: {str(e)}")

@api_router.put("/telehealth/{session_id}/status")
async def update_telehealth_session_status(session_id: str, status_data: Dict):
    try:
        status = status_data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        # Add timestamps based on status
        if status == "active" and not await db.telehealth_sessions.find_one({"id": session_id, "actual_start": {"$exists": True}}):
            update_data["actual_start"] = datetime.now()
        elif status == "completed":
            update_data["actual_end"] = datetime.now()
        
        result = await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
            
        return {"message": f"Telehealth session status updated to {status}"}
    except Exception as e:
        logger.error(f"Error updating session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session status: {str(e)}")

# ===== PHASE 3: INTEGRATION & WORKFLOW ENDPOINTS =====

# 1. Workflow Integration Endpoints
@api_router.post("/workflows/referral-to-appointment")
async def create_referral_appointment_workflow(workflow_data: Dict):
    """Create a workflow from referral to appointment to potential telehealth session"""
    try:
        referral_id = workflow_data["referral_id"]
        appointment_data = workflow_data["appointment_data"]
        telehealth_option = workflow_data.get("enable_telehealth", False)
        
        # Get referral details
        referral = await db.referrals.find_one({"id": referral_id}, {"_id": 0})
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        # Create appointment based on referral
        appointment = {
            "id": str(uuid.uuid4()),
            "patient_id": referral["patient_id"],
            "provider_id": appointment_data.get("provider_id"),
            "appointment_type": "referral_follow_up",
            "status": "scheduled",
            "date": appointment_data["date"],
            "time": appointment_data["time"],
            "duration": appointment_data.get("duration", 30),
            "notes": f"Follow-up for referral: {referral['reason_for_referral']}",
            "referral_id": referral_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        appointment_result = await db.appointments.insert_one(appointment)
        
        # Create telehealth session if requested
        telehealth_session = None
        if telehealth_option:
            session = TelehealthSession(
                patient_id=referral["patient_id"],
                provider_id=appointment_data.get("provider_id"),
                session_type="referral_consultation",
                scheduled_start=datetime.strptime(f"{appointment_data['date']} {appointment_data['time']}", "%Y-%m-%d %H:%M"),
                scheduled_end=datetime.strptime(f"{appointment_data['date']} {appointment_data['time']}", "%Y-%m-%d %H:%M") + timedelta(minutes=appointment_data.get("duration", 30)),
                notes=f"Telehealth session for referral: {referral['reason_for_referral']}",
                appointment_id=appointment["id"]
            )
            
            session_dict = session.dict()
            meeting_id = f"clinichub-{session.patient_id}-{int(datetime.now().timestamp())}"
            meeting_url = f"https://meet.jit.si/{meeting_id}"
            session_dict["meeting_id"] = meeting_id
            session_dict["meeting_url"] = meeting_url
            
            telehealth_result = await db.telehealth_sessions.insert_one(session_dict)
            telehealth_session = session_dict
        
        # Update referral status
        await db.referrals.update_one(
            {"id": referral_id},
            {"$set": {"status": "scheduled", "appointment_id": appointment["id"], "updated_at": datetime.now()}}
        )
        
        # Create workflow record
        workflow_record = {
            "id": str(uuid.uuid4()),
            "type": "referral_to_appointment",
            "referral_id": referral_id,
            "appointment_id": appointment["id"],
            "telehealth_session_id": telehealth_session["id"] if telehealth_session else None,
            "status": "active",
            "created_at": datetime.now(),
            "steps": [
                {"step": "referral_created", "status": "completed", "timestamp": referral["created_at"]},
                {"step": "appointment_scheduled", "status": "completed", "timestamp": datetime.now()},
                {"step": "telehealth_prepared", "status": "completed" if telehealth_session else "skipped", "timestamp": datetime.now() if telehealth_session else None}
            ]
        }
        
        await db.workflows.insert_one(workflow_record)
        
        return {
            "workflow_id": workflow_record["id"],
            "referral_id": referral_id,
            "appointment_id": appointment["id"],
            "telehealth_session_id": telehealth_session["id"] if telehealth_session else None,
            "status": "workflow_created",
            "next_steps": ["appointment_reminder", "provider_notification"]
        }
        
    except Exception as e:
        logger.error(f"Error creating referral workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

@api_router.get("/workflows")
async def get_workflows(workflow_type: Optional[str] = None, status: Optional[str] = None):
    """Get all workflows with optional filtering"""
    try:
        query = {}
        if workflow_type:
            query["type"] = workflow_type
        if status:
            query["status"] = status
            
        workflows = []
        async for workflow in db.workflows.find(query, {"_id": 0}).sort("created_at", -1):
            workflows.append(workflow)
            
        return workflows
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching workflows: {str(e)}")

@api_router.get("/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    """Get detailed workflow information with related records"""
    try:
        workflow = await db.workflows.find_one({"id": workflow_id}, {"_id": 0})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get related records
        if workflow["referral_id"]:
            referral = await db.referrals.find_one({"id": workflow["referral_id"]}, {"_id": 0})
            workflow["referral_details"] = referral
            
        if workflow["appointment_id"]:
            appointment = await db.appointments.find_one({"id": workflow["appointment_id"]}, {"_id": 0})
            workflow["appointment_details"] = appointment
            
        if workflow.get("telehealth_session_id"):
            session = await db.telehealth_sessions.find_one({"id": workflow["telehealth_session_id"]}, {"_id": 0})
            workflow["telehealth_details"] = session
            
        return workflow
    except Exception as e:
        logger.error(f"Error fetching workflow details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching workflow details: {str(e)}")

# 2. Global Search Endpoint
@api_router.get("/search")
async def global_search(query: str, modules: Optional[str] = None, limit: int = 50):
    """Global search across all modules"""
    try:
        search_results = {
            "query": query,
            "results": [],
            "total_count": 0
        }
        
        search_modules = modules.split(",") if modules else ["patients", "referrals", "appointments", "documents", "templates", "telehealth"]
        
        # Search patients
        if "patients" in search_modules:
            async for patient in db.patients.find({
                "$or": [
                    {"name.0.given": {"$regex": query, "$options": "i"}},
                    {"name.0.family": {"$regex": query, "$options": "i"}},
                    {"mrn": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(10):
                search_results["results"].append({
                    "type": "patient",
                    "id": patient["id"],
                    "title": f"{patient['name'][0]['given']} {patient['name'][0]['family']}",
                    "subtitle": f"MRN: {patient.get('mrn', 'N/A')}",
                    "module": "patients",
                    "data": patient
                })
        
        # Search referrals
        if "referrals" in search_modules:
            async for referral in db.referrals.find({
                "$or": [
                    {"reason_for_referral": {"$regex": query, "$options": "i"}},
                    {"referred_to_provider_name": {"$regex": query, "$options": "i"}},
                    {"referred_to_specialty": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(10):
                search_results["results"].append({
                    "type": "referral",
                    "id": referral["id"],
                    "title": f"Referral to {referral['referred_to_specialty']}",
                    "subtitle": referral["reason_for_referral"],
                    "module": "referrals",
                    "data": referral
                })
        
        # Search documents
        if "documents" in search_modules:
            async for document in db.clinical_documents.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}},
                    {"tags": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(10):
                search_results["results"].append({
                    "type": "document",
                    "id": document["id"],
                    "title": document["title"],
                    "subtitle": f"Type: {document['document_type']}",
                    "module": "documents",
                    "data": document
                })
        
        # Search clinical templates
        if "templates" in search_modules:
            async for template in db.clinical_templates.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"specialty": {"$regex": query, "$options": "i"}},
                    {"condition": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(10):
                search_results["results"].append({
                    "type": "template",
                    "id": template["id"],
                    "title": template["name"],
                    "subtitle": f"Specialty: {template.get('specialty', 'General')}",
                    "module": "clinical-templates",
                    "data": template
                })
        
        # Search telehealth sessions
        if "telehealth" in search_modules:
            async for session in db.telehealth_sessions.find({
                "$or": [
                    {"notes": {"$regex": query, "$options": "i"}},
                    {"session_type": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(10):
                search_results["results"].append({
                    "type": "telehealth",
                    "id": session["id"],
                    "title": f"Telehealth Session - {session['session_type']}",
                    "subtitle": f"Status: {session['status']}",
                    "module": "telehealth",
                    "data": session
                })
        
        search_results["total_count"] = len(search_results["results"])
        return search_results
        
    except Exception as e:
        logger.error(f"Error performing global search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")

# 3. Notification System Endpoints
@api_router.post("/notifications")
async def create_notification(notification_data: Dict):
    """Create a new notification"""
    try:
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": notification_data["user_id"],
            "type": notification_data["type"],  # workflow, reminder, alert, info
            "title": notification_data["title"],
            "message": notification_data["message"],
            "module": notification_data.get("module"),
            "related_id": notification_data.get("related_id"),
            "priority": notification_data.get("priority", "normal"),  # low, normal, high, urgent
            "is_read": False,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=30)
        }
        
        result = await db.notifications.insert_one(notification)
        if result.inserted_id:
            return {"id": notification["id"], "message": "Notification created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create notification")
            
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@api_router.get("/notifications")
async def get_notifications(user_id: Optional[str] = None, is_read: Optional[bool] = None, limit: int = 50):
    """Get notifications for a user"""
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if is_read is not None:
            query["is_read"] = is_read
        
        # Only get non-expired notifications
        query["expires_at"] = {"$gt": datetime.now()}
        
        notifications = []
        async for notification in db.notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
            notifications.append(notification)
            
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"is_read": True, "read_at": datetime.now()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return {"message": "Notification marked as read"}
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")

# 4. User Preferences Endpoints
@api_router.post("/user-preferences")
async def save_user_preferences(preferences_data: Dict):
    """Save user preferences"""
    try:
        user_id = preferences_data["user_id"]
        preferences = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dashboard_layout": preferences_data.get("dashboard_layout", "default"),
            "module_order": preferences_data.get("module_order", []),
            "theme": preferences_data.get("theme", "dark"),
            "notifications_enabled": preferences_data.get("notifications_enabled", True),
            "default_module": preferences_data.get("default_module", "dashboard"),
            "items_per_page": preferences_data.get("items_per_page", 25),
            "auto_refresh": preferences_data.get("auto_refresh", False),
            "mobile_optimized": preferences_data.get("mobile_optimized", True),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Upsert user preferences
        result = await db.user_preferences.update_one(
            {"user_id": user_id},
            {"$set": preferences},
            upsert=True
        )
        
        return {"message": "User preferences saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")

@api_router.get("/user-preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        preferences = await db.user_preferences.find_one({"user_id": user_id}, {"_id": 0})
        if not preferences:
            # Return default preferences
            return {
                "user_id": user_id,
                "dashboard_layout": "default",
                "module_order": [],
                "theme": "dark",
                "notifications_enabled": True,
                "default_module": "dashboard",
                "items_per_page": 25,
                "auto_refresh": False,
                "mobile_optimized": True
            }
        return preferences
    except Exception as e:
        logger.error(f"Error fetching user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching preferences: {str(e)}")

# Configure logging

@api_router.get("/telehealth/sessions")
async def get_telehealth_sessions(patient_id: Optional[str] = None, provider_id: Optional[str] = None, status: Optional[str] = None):
    try:
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if provider_id:
            query["provider_id"] = provider_id
        if status:
            query["status"] = status
            
        sessions = []
        async for session in db.telehealth_sessions.find(query, {"_id": 0}).sort("scheduled_start", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": session["patient_id"]}, {"_id": 0})
            provider = await db.providers.find_one({"id": session["provider_id"]}, {"_id": 0})
            
            session["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            session["provider_name"] = f"{provider['first_name']} {provider['last_name']}" if provider else "Unknown"
            sessions.append(session)
            
        return sessions
    except Exception as e:
        logger.error(f"Error fetching telehealth sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@api_router.put("/telehealth/sessions/{session_id}/start")
async def start_telehealth_session(session_id: str):
    try:
        result = await db.telehealth_sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": TelehealthStatus.IN_PROGRESS,
                    "actual_start": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {"message": "Session started successfully"}
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

@api_router.put("/telehealth/sessions/{session_id}/end")
async def end_telehealth_session(session_id: str, session_notes: Optional[str] = None):
    try:
        update_data = {
            "status": TelehealthStatus.COMPLETED,
            "actual_end": datetime.now(),
            "updated_at": datetime.now()
        }
        if session_notes:
            update_data["session_notes"] = session_notes
            
        result = await db.telehealth_sessions.update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {"message": "Session ended successfully"}
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")

# Initialize default data for new modules
@api_router.post("/system/init-new-modules")
async def initialize_new_modules():
    try:
        results = {}
        
        # Initialize document categories
        existing_categories = await db.document_categories.count_documents({})
        if existing_categories == 0:
            default_categories = [
                {"id": str(uuid.uuid4()), "name": "Patient Records", "description": "General patient documentation", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Lab Results", "description": "Laboratory test results", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Imaging", "description": "X-rays, MRIs, CTs, etc.", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Prescriptions", "description": "Medication prescriptions", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Insurance", "description": "Insurance documentation", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Consent Forms", "description": "Patient consent documentation", "is_active": True},
                {"id": str(uuid.uuid4()), "name": "Referrals", "description": "Specialist referral documentation", "is_active": True}
            ]
            await db.document_categories.insert_many(default_categories)
            results["document_categories"] = len(default_categories)
        
        # Initialize quality measures
        existing_measures = await db.quality_measures.count_documents({})
        if existing_measures == 0:
            default_measures = [
                {
                    "id": str(uuid.uuid4()),
                    "measure_id": "CMS122",
                    "name": "Diabetes: Hemoglobin A1c (HbA1c) Poor Control (>9%)",
                    "description": "Percentage of patients 18-75 years of age with diabetes who had hemoglobin A1c > 9.0% during the measurement period",
                    "measure_type": "outcome",
                    "population_criteria": {"age_range": "18-75", "diagnosis": "diabetes"},
                    "numerator_criteria": {"hba1c_value": ">9.0"},
                    "denominator_criteria": {"diagnosis": "diabetes", "age": "18-75"},
                    "reporting_period": "annual",
                    "is_active": True,
                    "created_at": datetime.now()
                },
                {
                    "id": str(uuid.uuid4()),
                    "measure_id": "CMS134",
                    "name": "Diabetes: Medical Attention for Nephropathy",
                    "description": "Percentage of patients 18-75 years of age with diabetes who had a nephropathy screening test or evidence of nephropathy during the measurement period",
                    "measure_type": "process",
                    "population_criteria": {"age_range": "18-75", "diagnosis": "diabetes"},
                    "numerator_criteria": {"nephropathy_screening": "completed"},
                    "denominator_criteria": {"diagnosis": "diabetes", "age": "18-75"},
                    "reporting_period": "annual",
                    "is_active": True,
                    "created_at": datetime.now()
                }
            ]
            await db.quality_measures.insert_many(default_measures)
            results["quality_measures"] = len(default_measures)
        
        # Initialize clinical templates
        existing_templates = await db.clinical_templates.count_documents({})
        if existing_templates == 0:
            default_templates = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Annual Physical Exam",
                    "template_type": "visit_template",
                    "specialty": "family_medicine",
                    "age_group": "adult",
                    "sections": [
                        {"name": "Review of Systems", "fields": ["constitutional", "cardiovascular", "respiratory", "gastrointestinal"]},
                        {"name": "Physical Examination", "fields": ["vital_signs", "general_appearance", "cardiovascular", "respiratory", "abdominal"]},
                        {"name": "Assessment and Plan", "fields": ["problems", "medications", "health_maintenance"]}
                    ],
                    "protocols": [],
                    "is_active": True,
                    "created_by": "system",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Diabetes Management",
                    "template_type": "care_plan",
                    "specialty": "endocrinology",
                    "condition": "diabetes",
                    "sections": [
                        {"name": "Glucose Monitoring", "fields": ["hba1c", "blood_glucose_logs", "symptoms"]},
                        {"name": "Medications", "fields": ["insulin", "oral_medications", "adherence"]},
                        {"name": "Lifestyle", "fields": ["diet", "exercise", "weight_management"]}
                    ],
                    "protocols": ["diabetes_protocol"],
                    "is_active": True,
                    "created_by": "system",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
            await db.clinical_templates.insert_many(default_templates)
            results["clinical_templates"] = len(default_templates)
        
        return {"message": "New modules initialized successfully", "initialized": results}
    except Exception as e:
        logger.error(f"Error initializing new modules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing modules: {str(e)}")

# =====================================
# COMMUNICATION GATEWAY ENDPOINTS
# =====================================

@api_router.post("/communication/send-email")
async def send_email(
    email_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Send email through communication gateway"""
    try:
        # Communication gateway URL (for now, simulate locally)
        gateway_url = "http://localhost:8100"  # Will be updated when gateway is deployed
        
        # Format email data for gateway
        email_payload = {
            "to": [email_data.get("to")],
            "subject": email_data.get("subject"),
            "body": email_data.get("body"),
            "patient_id": email_data.get("patient_id"),
            "priority": email_data.get("priority", "normal")
        }
        
        # For now, simulate successful email sending
        # In production, this will call the actual gateway
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{gateway_url}/email/send", json=email_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
        except Exception as gateway_error:
            # Gateway not available, return mock success for development
            logger.info(f"Communication gateway not available, simulating email send: {email_payload}")
            return {
                "success": True,
                "message": "Email sent successfully (simulated)",
                "communication_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "details": {"recipients": email_payload["to"], "subject": email_payload["subject"]}
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@api_router.post("/communication/send-fax")
async def send_fax(
    fax_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Send fax through communication gateway"""
    try:
        gateway_url = "http://localhost:8100"
        
        # Format fax data for gateway
        fax_payload = {
            "to_number": fax_data.get("to"),
            "document_path": fax_data.get("document", "uploaded_document.pdf"),
            "patient_id": fax_data.get("patient_id"),
            "priority": fax_data.get("priority", "normal"),
            "cover_page": fax_data.get("cover_page", True),
            "cover_text": fax_data.get("cover_text")
        }
        
        # For now, simulate successful fax sending
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{gateway_url}/fax/send", json=fax_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
        except Exception as gateway_error:
            # Gateway not available, return mock success for development
            logger.info(f"Communication gateway not available, simulating fax send: {fax_payload}")
            return {
                "success": True,
                "message": "Fax sent successfully (simulated)",
                "communication_id": f"fax_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "details": {"to_number": fax_payload["to_number"], "document": fax_payload["document_path"]}
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending fax: {str(e)}")

@api_router.post("/communication/voip-call")
async def initiate_voip_call(
    call_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Initiate VoIP call through communication gateway"""
    try:
        gateway_url = "http://localhost:8100"
        
        # Format call data for gateway
        call_payload = {
            "from_number": call_data.get("from_number"),
            "to_number": call_data.get("to_number"),
            "patient_id": call_data.get("patient_id"),
            "call_type": call_data.get("call_type", "outbound")
        }
        
        # For now, simulate successful call initiation
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{gateway_url}/voip/call", json=call_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
        except Exception as gateway_error:
            # Gateway not available, return mock success for development
            logger.info(f"Communication gateway not available, simulating VoIP call: {call_payload}")
            return {
                "success": True,
                "message": "Call initiated successfully (simulated)",
                "communication_id": f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "details": {"from": call_payload["from_number"], "to": call_payload["to_number"]}
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating call: {str(e)}")

@api_router.get("/communication/status")
async def get_communication_status(
    current_user: dict = Depends(get_current_user)
):
    """Get communication gateway status"""
    try:
        gateway_url = "http://localhost:8100"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{gateway_url}/status") as response:
                    if response.status == 200:
                        gateway_status = await response.json()
                        return {
                            "gateway_connected": True,
                            "gateway_url": gateway_url,
                            "services": gateway_status.get("services", {}),
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as gateway_error:
            # Gateway not available, return status info
            return {
                "gateway_connected": False,
                "gateway_url": gateway_url,
                "error": "Communication gateway not available",
                "services": {
                    "mailu": {"status": "not_deployed", "description": "Email server"},
                    "hylafax": {"status": "not_deployed", "description": "Fax server"},
                    "freeswitch": {"status": "not_deployed", "description": "VoIP server"}
                },
                "timestamp": datetime.now().isoformat(),
                "note": "Communication services will be available when deployed to Synology NAS"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking communication status: {str(e)}")

# =====================================
# OPENEMR INTEGRATION ENDPOINTS
# =====================================

@api_router.get("/openemr/patients")
async def get_openemr_patients(
    current_user: dict = Depends(get_current_user)
):
    """Get patients from OpenEMR"""
    try:
        # Authenticate with OpenEMR if not already done
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        patients = await openemr.get_patients()
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OpenEMR patients: {str(e)}")

@api_router.get("/openemr/patients/{patient_id}")
async def get_openemr_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific patient from OpenEMR"""
    try:
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        patient = await openemr.get_patient(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return patient
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OpenEMR patient: {str(e)}")

@api_router.post("/openemr/patients")
async def create_openemr_patient(
    patient_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create new patient in OpenEMR"""
    try:
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        patient = await openemr.create_patient(patient_data)
        if not patient:
            raise HTTPException(status_code=400, detail="Failed to create patient")
        
        return patient
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating OpenEMR patient: {str(e)}")

@api_router.get("/openemr/patients/{patient_id}/encounters")
async def get_openemr_encounters(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient encounters from OpenEMR"""
    try:
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        encounters = await openemr.get_encounters(patient_id)
        return encounters
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OpenEMR encounters: {str(e)}")

@api_router.post("/openemr/patients/{patient_id}/encounters")
async def create_openemr_encounter(
    patient_id: str,
    encounter_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create new encounter in OpenEMR"""
    try:
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        encounter = await openemr.create_encounter(patient_id, encounter_data)
        if not encounter:
            raise HTTPException(status_code=400, detail="Failed to create encounter")
        
        return encounter
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating OpenEMR encounter: {str(e)}")

@api_router.get("/openemr/patients/{patient_id}/prescriptions")
async def get_openemr_prescriptions(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient prescriptions from OpenEMR"""
    try:
        if not openemr.api_token:
            await openemr.authenticate("admin", "admin123")
        
        prescriptions = await openemr.get_prescriptions(patient_id)
        return prescriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OpenEMR prescriptions: {str(e)}")

@api_router.get("/openemr/status")
async def get_openemr_status(
    current_user: dict = Depends(get_current_user)
):
    """Get OpenEMR integration status"""
    try:
        # Try to authenticate to test connection
        token = await openemr.authenticate("admin", "admin123")
        
        return {
            "status": "connected" if token else "disconnected",
            "base_url": openemr.base_url,
            "authenticated": bool(openemr.api_token),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "base_url": openemr.base_url,
            "authenticated": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Include API router (MUST be after all endpoint definitions)
app.include_router(api_router)

# Health endpoint for Docker health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint with CORS debugging info"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cors_enabled": True,
        "frontend_origin": os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
        "environment": os.getenv("ENV", "development")
    }

@app.get("/health")
async def root_health_check():
    return {"status": "healthy", "service": "ClinicHub API"}

# Root route for API verification
@app.get("/")
async def root():
    return {
        "message": "ClinicHub API is running", 
        "status": "healthy", 
        "version": "1.0.0",
        "docs": "/docs",
        "api_endpoints": "/api",
        "health": "/health"
    }

# Configure CORS origins for multiple environments with dynamic detection
def get_frontend_origin():
    """Get frontend origin from environment or detect dynamically"""
    env_origin = os.getenv("FRONTEND_ORIGIN", "")
    if env_origin:
        return env_origin
    # For production, we'll need to accept the requesting origin
    return "http://localhost:3000"  # fallback for development

FRONTEND_ORIGIN = get_frontend_origin()

# Updated CORS configuration for production flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployed environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple connectivity test endpoint for deployment debugging
@api_router.get("/ping")
def ping():
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()