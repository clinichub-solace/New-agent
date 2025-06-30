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
from datetime import datetime, date, timedelta
from enum import Enum, str
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
    try:
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
    employee = await db.enhanced_employees.find_one({"id": employee_id})
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
    documents = await db.employee_documents.find({"employee_id": employee_id}).sort("created_at", -1).to_list(1000)
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
        
        entries = await db.time_entries.find(query).sort("timestamp", -1).to_list(1000)
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
        
        shifts = await db.work_shifts.find(query).sort("shift_date", 1).to_list(1000)
        return [WorkShift(**shift) for shift in shifts]
    except Exception as e:
        logger.error(f"Error getting employee shifts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting shifts: {str(e)}")

@api_router.get("/work-shifts/date/{shift_date}", response_model=List[WorkShift])
async def get_shifts_by_date(shift_date: date):
    try:
        shifts = await db.work_shifts.find({"shift_date": shift_date}).sort("start_time", 1).to_list(1000)
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

# Employee Dashboard Summary
@api_router.get("/employees/{employee_id}/dashboard")
async def get_employee_dashboard(employee_id: str):
    try:
        # Get employee info
        employee = await db.enhanced_employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Get current status
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
        
        # Get upcoming shifts (next 7 days)
        upcoming_shifts = await db.work_shifts.find({
            "employee_id": employee_id,
            "shift_date": {"$gte": today, "$lte": today.replace(day=today.day + 7)}
        }).sort("shift_date", 1).to_list(10)
        
        # Get pending documents
        pending_docs = await db.employee_documents.find({
            "employee_id": employee_id,
            "status": {"$in": ["pending_signature", "draft"]}
        }).to_list(100)
        
        # Calculate hours this week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        hours_summary = await get_employee_hours_summary(employee_id, week_start, week_end)
        
        return {
            "employee": EnhancedEmployee(**employee),
            "current_status": latest_entry,
            "upcoming_shifts": [WorkShift(**shift) for shift in upcoming_shifts],
            "pending_documents": [EmployeeDocument(**doc) for doc in pending_docs],
            "week_hours": hours_summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employee dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard: {str(e)}")

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
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
    documents = await db.patient_documents.find({"patient_id": patient_id}).sort("upload_date", -1).to_list(100)
    
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
        patient = await db.patients.find_one({"id": patient_id})
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
    documents = await db.patient_documents.find({"patient_id": patient_id}).sort("upload_date", -1).to_list(1000)
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
        invoice = await db.enhanced_invoices.find_one({"id": invoice_id})
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
    invoices = await db.enhanced_invoices.find({"patient_id": patient_id}).sort("created_at", -1).to_list(1000)
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
                inventory_item = await db.inventory.find_one({"id": item["inventory_item_id"]})
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