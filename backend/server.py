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
from enum import Enum
from fastapi.encoders import jsonable_encoder

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

# Enhanced EHR Models

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
    patient_id: str
    allergen: str
    reaction: str
    severity: AllergySeverity
    onset_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: str

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
    
    # Use jsonable_encoder to handle date serialization
    patient_dict = jsonable_encoder(patient)
    await db.patients.insert_one(patient_dict)
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
    form_dict = jsonable_encoder(form)
    await db.forms.insert_one(form_dict)
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
    
    submission_dict = jsonable_encoder(submission)
    await db.form_submissions.insert_one(submission_dict)
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
    
    invoice_dict = jsonable_encoder(invoice)
    await db.invoices.insert_one(invoice_dict)
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
    item_dict = jsonable_encoder(item)
    await db.inventory.insert_one(item_dict)
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
        {"$set": {"current_stock": new_stock, "updated_at": jsonable_encoder(datetime.utcnow())}}
    )
    
    transaction.item_id = item_id
    transaction_dict = jsonable_encoder(transaction)
    await db.inventory_transactions.insert_one(transaction_dict)
    return transaction
    await db.inventory_transactions.insert_one(transaction_dict)
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
    
    employee_dict = jsonable_encoder(employee)
    await db.employees.insert_one(employee_dict)
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
    
    # Additional EHR stats
    total_encounters = await db.encounters.count_documents({})
    pending_encounters = await db.encounters.count_documents({"status": {"$in": ["planned", "arrived"]}})
    completed_encounters_today = await db.encounters.count_documents({
        "status": "completed",
        "actual_end": {"$gte": datetime.combine(date.today(), datetime.min.time())}
    })
    
    # Recent activity
    recent_patients = await db.patients.find().sort("created_at", -1).limit(5).to_list(5)
    recent_invoices = await db.invoices.find().sort("created_at", -1).limit(5).to_list(5)
    recent_encounters = await db.encounters.find().sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "stats": {
            "total_patients": total_patients,
            "total_invoices": total_invoices,
            "pending_invoices": pending_invoices,
            "low_stock_items": low_stock_items,
            "total_employees": total_employees,
            "total_encounters": total_encounters,
            "pending_encounters": pending_encounters,
            "completed_encounters_today": completed_encounters_today
        },
        "recent_patients": [Patient(**p) for p in recent_patients],
        "recent_invoices": [Invoice(**i) for i in recent_invoices],
        "recent_encounters": [Encounter(**e) for e in recent_encounters]
    }

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
    encounters = await db.encounters.find({"patient_id": patient_id}).sort("scheduled_date", -1).to_list(1000)
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

@api_router.get("/soap-notes/encounter/{encounter_id}", response_model=List[SOAPNote])
async def get_encounter_soap_notes(encounter_id: str):
    notes = await db.soap_notes.find({"encounter_id": encounter_id}).to_list(1000)
    return [SOAPNote(**note) for note in notes]

@api_router.get("/soap-notes/patient/{patient_id}", response_model=List[SOAPNote])
async def get_patient_soap_notes(patient_id: str):
    notes = await db.soap_notes.find({"patient_id": patient_id}).sort("created_at", -1).to_list(1000)
    return [SOAPNote(**note) for note in notes]

# Vital Signs
@api_router.post("/vital-signs", response_model=VitalSigns)
async def create_vital_signs(vitals_data: VitalSigns):
    vitals_dict = jsonable_encoder(vitals_data)
    await db.vital_signs.insert_one(vitals_dict)
    return vitals_data

@api_router.get("/vital-signs/patient/{patient_id}", response_model=List[VitalSigns])
async def get_patient_vital_signs(patient_id: str):
    vitals = await db.vital_signs.find({"patient_id": patient_id}).sort("recorded_at", -1).to_list(1000)
    return [VitalSigns(**vital) for vital in vitals]

# Allergies
@api_router.post("/allergies", response_model=Allergy)
async def create_allergy(allergy_data: AllergyCreate):
    allergy = Allergy(**allergy_data.dict())
    allergy_dict = jsonable_encoder(allergy)
    await db.allergies.insert_one(allergy_dict)
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
    medications = await db.medications.find({"patient_id": patient_id}).to_list(1000)
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
    diagnoses = await db.diagnoses.find({"patient_id": patient_id}).sort("created_at", -1).to_list(1000)
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
    procedures = await db.procedures.find({"patient_id": patient_id}).sort("created_at", -1).to_list(1000)
    return [Procedure(**procedure) for procedure in procedures]

# Comprehensive Patient Summary
@api_router.get("/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    # Get patient basic info
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get all related medical data
    encounters = await db.encounters.find({"patient_id": patient_id}).sort("scheduled_date", -1).limit(10).to_list(10)
    allergies = await db.allergies.find({"patient_id": patient_id}).to_list(100)
    medications = await db.medications.find({"patient_id": patient_id, "status": "active"}).to_list(100)
    medical_history = await db.medical_history.find({"patient_id": patient_id}).to_list(100)
    recent_vitals = await db.vital_signs.find({"patient_id": patient_id}).sort("recorded_at", -1).limit(1).to_list(1)
    recent_soap_notes = await db.soap_notes.find({"patient_id": patient_id}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "patient": Patient(**patient),
        "recent_encounters": [Encounter(**e) for e in encounters],
        "allergies": [Allergy(**a) for a in allergies],
        "active_medications": [Medication(**m) for m in medications],
        "medical_history": [MedicalHistory(**h) for h in medical_history],
        "recent_vitals": [VitalSigns(**v) for v in recent_vitals],
        "recent_soap_notes": [SOAPNote(**s) for s in recent_soap_notes]
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