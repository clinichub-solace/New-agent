from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
from pydantic import validator
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ClinicHub API", description="AI-Powered Practice Management System")

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
    
    @validator('birth_date', pre=True)
    def validate_birth_date(cls, v):
        if isinstance(v, date):
            return v.isoformat()
        return v

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
    type: str  # text, number, date, select, checkbox, textarea
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: List[str] = []  # for select fields
    smart_tag: Optional[str] = None  # {patient_name}, {date}, etc.

class SmartForm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    status: FormStatus = FormStatus.DRAFT
    fhir_mapping: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FormSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    form_id: str
    patient_id: str
    data: Dict[str, Any]
    fhir_data: Optional[Dict[str, Any]] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

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
    
    @validator('issue_date', 'due_date', pre=True)
    def validate_dates(cls, v):
        if isinstance(v, date):
            return v.isoformat()
        return v

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

class InventoryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    transaction_type: str  # in, out, adjustment
    quantity: int
    reference_id: Optional[str] = None  # patient_id, invoice_id, etc.
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Employee Models
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: EmployeeRole
    hire_date: date
    salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    address: Optional[str] = None
    emergency_contact: Optional[Dict[str, str]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: EmployeeRole
    hire_date: date
    salary: Optional[float] = None
    hourly_rate: Optional[float] = None

# Patient Routes
@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate):
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
    
    await db.patients.insert_one(patient.dict())
    return patient

@api_router.get("/patients", response_model=List[Patient])
async def get_patients():
    patients = await db.patients.find({"status": {"$ne": "deceased"}}).to_list(1000)
    return [Patient(**patient) for patient in patients]

@api_router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return Patient(**patient)

# Smart Form Routes
@api_router.post("/forms", response_model=SmartForm)
async def create_form(form: SmartForm):
    await db.forms.insert_one(form.dict())
    return form

@api_router.get("/forms", response_model=List[SmartForm])
async def get_forms():
    forms = await db.forms.find().to_list(1000)
    return [SmartForm(**form) for form in forms]

@api_router.post("/forms/{form_id}/submit", response_model=FormSubmission)
async def submit_form(form_id: str, submission_data: Dict[str, Any], patient_id: str):
    # Process smart tags and create FHIR-compliant data
    form = await db.forms.find_one({"id": form_id})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Create submission
    submission = FormSubmission(
        form_id=form_id,
        patient_id=patient_id,
        data=submission_data
        # TODO: Add FHIR mapping logic
    )
    
    await db.form_submissions.insert_one(submission.dict())
    return submission

# Invoice Routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate):
    # Generate invoice number
    count = await db.invoices.count_documents({})
    invoice_number = f"INV-{count + 1:06d}"
    
    # Calculate totals
    subtotal = sum(item.total for item in invoice_data.items)
    tax_amount = subtotal * invoice_data.tax_rate
    total_amount = subtotal + tax_amount
    
    # Set due date
    due_date = date.today().replace(day=date.today().day + invoice_data.due_days) if invoice_data.due_days else None
    
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
    
    await db.invoices.insert_one(invoice.dict())
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices():
    invoices = await db.invoices.find().to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return Invoice(**invoice)

# Inventory Routes
@api_router.post("/inventory", response_model=InventoryItem)
async def create_inventory_item(item: InventoryItem):
    await db.inventory.insert_one(item.dict())
    return item

@api_router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory():
    items = await db.inventory.find().to_list(1000)
    return [InventoryItem(**item) for item in items]

@api_router.post("/inventory/{item_id}/transaction", response_model=InventoryTransaction)
async def create_inventory_transaction(item_id: str, transaction: InventoryTransaction):
    # Update inventory stock
    item = await db.inventory.find_one({"id": item_id})
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
        {"$set": {"current_stock": new_stock, "updated_at": datetime.utcnow()}}
    )
    
    transaction.item_id = item_id
    await db.inventory_transactions.insert_one(transaction.dict())
    return transaction

# Employee Routes
@api_router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate):
    # Generate employee ID
    count = await db.employees.count_documents({})
    employee_id = f"EMP-{count + 1:04d}"
    
    employee = Employee(
        employee_id=employee_id,
        **employee_data.dict()
    )
    
    await db.employees.insert_one(employee.dict())
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees():
    employees = await db.employees.find({"is_active": True}).to_list(1000)
    return [Employee(**employee) for employee in employees]

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_patients = await db.patients.count_documents({"status": "active"})
    total_invoices = await db.invoices.count_documents({})
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
    low_stock_items = await db.inventory.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}})
    total_employees = await db.employees.count_documents({"is_active": True})
    
    # Recent activity
    recent_patients = await db.patients.find().sort("created_at", -1).limit(5).to_list(5)
    recent_invoices = await db.invoices.find().sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "stats": {
            "total_patients": total_patients,
            "total_invoices": total_invoices,
            "pending_invoices": pending_invoices,
            "low_stock_items": low_stock_items,
            "total_employees": total_employees
        },
        "recent_patients": [Patient(**p) for p in recent_patients],
        "recent_invoices": [Invoice(**i) for i in recent_invoices]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()