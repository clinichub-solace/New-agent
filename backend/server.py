from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Authentication setup
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

# Lab Integration Models
class LabOrderStatus(str, Enum):
    ORDERED = "ordered"
    COLLECTED = "collected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    AMENDED = "amended"

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

class LabOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: str
    encounter_id: Optional[str] = None
    order_number: str
    lab_tests: List[str]  # List of LabTest IDs
    icd10_codes: List[str]  # Diagnosis codes justifying the order
    status: LabOrderStatus
    priority: str = "routine"  # routine, urgent, stat
    notes: Optional[str] = None
    ordered_by: str
    ordered_at: datetime = Field(default_factory=datetime.utcnow)
    collected_at: Optional[datetime] = None
    expected_completion: Optional[datetime] = None
    lab_facility: str = "Internal Lab"

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

async def authenticate_user(username: str, password: str):
    user = await db.users.find_one({"username": username})
    if not user:
        return False
    user_obj = User(**user)
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
    
    patient_user = await db.patient_users.find_one({"id": patient_user_id})
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
    user = await db.users.find_one({"id": user_id})
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user already exists"
            )
        
        # Create default admin user
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
            "warning": "Please change the password immediately!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating admin: {str(e)}")

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
    form = await db.forms.find_one({"id": form_id})
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
    form = await db.forms.find_one({"id": form_id})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Get patient details for smart tag processing
    patient = await db.patients.find_one({"id": patient_id})
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
    
    submissions = await db.form_submissions.find(query).sort("submitted_at", -1).to_list(1000)
    return [FormSubmission(**submission) for submission in submissions]

@api_router.get("/patients/{patient_id}/form-submissions", response_model=List[FormSubmission])
async def get_patient_form_submissions(
    patient_id: str,
    current_user: User = Depends(get_current_active_user)
):
    submissions = await db.form_submissions.find({"patient_id": patient_id}).sort("submitted_at", -1).to_list(1000)
    return [FormSubmission(**submission) for submission in submissions]

@api_router.get("/form-submissions/{submission_id}", response_model=FormSubmission)
async def get_form_submission(
    submission_id: str,
    current_user: User = Depends(get_current_active_user)
):
    submission = await db.form_submissions.find_one({"id": submission_id})
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
    template = await db.forms.find_one({"id": template_id, "is_template": True})
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
        encounter = await db.encounters.find_one({"id": encounter_id})
    
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
    vendors = await db.vendors.find({"status": {"$ne": "inactive"}}).sort("company_name", 1).to_list(1000)
    return [Vendor(**vendor) for vendor in vendors]

@api_router.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str):
    vendor = await db.vendors.find_one({"id": vendor_id})
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
async def update_check_status(check_id: str, status: CheckStatus):
    try:
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        
        if status == CheckStatus.PRINTED:
            update_data["printed_date"] = datetime.utcnow()
        elif status == CheckStatus.ISSUED:
            update_data["issued_date"] = datetime.utcnow()
        elif status == CheckStatus.CASHED:
            update_data["cashed_date"] = datetime.utcnow()
        elif status == CheckStatus.VOID:
            update_data["void_date"] = date.today()
        
        result = await db.checks.update_one(
            {"id": check_id},
            {"$set": jsonable_encoder(update_data)}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Check not found")
        
        return {"message": "Check status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating check status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating check: {str(e)}")

@api_router.get("/checks/{check_id}/print-data")
async def get_check_print_data(check_id: str):
    try:
        check = await db.checks.find_one({"id": check_id})
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")
        
        check_obj = Check(**check)
        
        # Get payee details if vendor
        payee_details = None
        if check_obj.payee_type == "vendor" and check_obj.payee_id:
            vendor = await db.vendors.find_one({"id": check_obj.payee_id})
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

# Financial Transactions
@api_router.post("/financial-transactions", response_model=FinancialTransaction)
async def create_financial_transaction(transaction_data: FinancialTransactionCreate):
    try:
        # Generate transaction number
        count = await db.financial_transactions.count_documents({})
        prefix = "INC" if transaction_data.transaction_type == TransactionType.INCOME else "EXP"
        transaction_number = f"{prefix}-{count + 1:06d}"
        
        transaction = FinancialTransaction(
            transaction_number=transaction_number,
            **transaction_data.dict()
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
        
        transactions = await db.financial_transactions.find(query).sort("transaction_date", -1).to_list(1000)
        return [FinancialTransaction(**trans) for trans in transactions]
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transactions: {str(e)}")

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
    invoices = await db.vendor_invoices.find({"payment_status": "unpaid"}).sort("due_date", 1).to_list(1000)
    return [VendorInvoice(**inv) for inv in invoices]

@api_router.put("/vendor-invoices/{invoice_id}/pay")
async def pay_vendor_invoice(invoice_id: str, check_id: str):
    try:
        # Get invoice and check
        invoice = await db.vendor_invoices.find_one({"id": invoice_id})
        check = await db.checks.find_one({"id": check_id})
        
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
            patient = await db.patients.find_one({"id": encounter["patient_id"]})
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
            patient = await db.patients.find_one({"id": encounter["patient_id"]})
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
            patient = await db.patients.find_one({"id": encounter["patient_id"]})
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
            patient = await db.patients.find_one({"id": invoice["patient_id"]})
            if patient:
                outstanding_amount = invoice.get("total_amount", 0)
                total_outstanding += outstanding_amount
                
                # Get encounter details if available
                encounter = None
                if "encounter_id" in invoice:
                    encounter = await db.encounters.find_one({"id": invoice["encounter_id"]})
                
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
            patient = await db.patients.find_one({"id": invoice["patient_id"]})
            if patient:
                outstanding_amount = invoice.get("total_amount", 0) - invoice.get("amount_paid", 0)
                total_outstanding += outstanding_amount
                
                # Get encounter details if available
                encounter = None
                if "encounter_id" in invoice:
                    encounter = await db.encounters.find_one({"id": invoice["encounter_id"]})
                
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
        
        medications = await db.fhir_medications.find(query).limit(limit).to_list(limit)
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
        medication = await db.fhir_medications.find_one({"id": medication_id})
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        return medication
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving medication: {str(e)}")

@api_router.post("/prescriptions", response_model=MedicationRequest)
async def create_prescription(prescription_data: dict, current_user: User = Depends(get_current_active_user)):
    try:
        # Validate patient exists
        patient = await db.patients.find_one({"id": prescription_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create prescription object
        prescription = MedicationRequest(
            id=str(uuid.uuid4()),
            **prescription_data
        )
        
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
        
        prescriptions = await db.prescriptions.find(query).sort("created_at", -1).to_list(100)
        
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
        prescription = await db.prescriptions.find_one({"id": prescription_id})
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
        prescription = await db.prescriptions.find_one({"id": prescription_id})
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
        medication = await db.fhir_medications.find_one({"id": medication_id})
        
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
    providers = await db.providers.find({"status": {"$ne": "inactive"}}).sort("name", 1).to_list(1000)
    return [Provider(**provider) for provider in providers]

@api_router.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(provider_id: str):
    provider = await db.providers.find_one({"id": provider_id})
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
        provider = await db.providers.find_one({"id": provider_id})
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
        
        schedules = await db.provider_schedules.find(query).sort("date", 1).to_list(1000)
        return [ProviderSchedule(**schedule) for schedule in schedules]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schedule: {str(e)}")

# Appointment Management
@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment_data: dict):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": appointment_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify provider exists
        provider = await db.providers.find_one({"id": appointment_data["provider_id"]})
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        appointment = Appointment(
            id=str(uuid.uuid4()),
            **appointment_data
        )
        
        appointment_dict = jsonable_encoder(appointment)
        await db.appointments.insert_one(appointment_dict)
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
        
        appointments = await db.appointments.find(query).sort("appointment_date", 1).to_list(1000)
        return [Appointment(**appointment) for appointment in appointments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointments: {str(e)}")

# Calendar View (must be before {appointment_id} route)
@api_router.get("/appointments/calendar")
async def get_calendar_view(date: str, view: str = "week"):
    try:
        from datetime import datetime, timedelta
        
        # Parse date
        base_date = datetime.fromisoformat(date)
        
        if view == "day":
            start_date = base_date.date()
            end_date = start_date
        elif view == "week":
            # Get start of week (Monday)
            start_date = (base_date - timedelta(days=base_date.weekday())).date()
            end_date = start_date + timedelta(days=6)
        elif view == "month":
            start_date = base_date.replace(day=1).date()
            # Get last day of month
            if base_date.month == 12:
                next_month = base_date.replace(year=base_date.year + 1, month=1, day=1)
            else:
                next_month = base_date.replace(month=base_date.month + 1, day=1)
            end_date = (next_month - timedelta(days=1)).date()
        else:
            raise HTTPException(status_code=400, detail="Invalid view type. Use 'day', 'week', or 'month'")
        
        # Get appointments in date range
        appointments = await db.appointments.find({
            "appointment_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }).sort("appointment_date", 1).to_list(1000)
        
        return {
            "view": view,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "appointments": [Appointment(**apt) for apt in appointments]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendar: {str(e)}")

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    appointment = await db.appointments.find_one({"id": appointment_id})
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
        query = {"is_active": True}
        if template_type:
            query["message_type"] = template_type
        
        templates = await db.communication_templates.find(query).sort("name", 1).to_list(1000)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@api_router.post("/communications/templates")
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
        patient = await db.patients.find_one({"id": message_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Process template variables if template_id provided
        if "template_id" in message_data:
            template = await db.communication_templates.find_one({"id": message_data["template_id"]})
            if template:
                content = template["content_template"]
                subject = template.get("subject_template", "")
                
                # Replace variables with actual values
                variables = message_data.get("variables", {})
                for var, value in variables.items():
                    content = content.replace(f"{{{{{var}}}}}", str(value))
                    subject = subject.replace(f"{{{{{var}}}}}", str(value))
                
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
        
        messages = await db.patient_messages.find(query).sort("sent_at", -1).limit(limit).to_list(limit)
        return [PatientMessage(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@api_router.get("/communications/messages/patient/{patient_id}")
async def get_patient_messages(patient_id: str):
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        messages = await db.patient_messages.find({"patient_id": patient_id}).sort("sent_at", -1).to_list(1000)
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
        tests = await db.lab_tests.find({"is_active": True}).sort("name", 1).to_list(1000)
        # Remove MongoDB ObjectId
        for test in tests:
            if "_id" in test:
                del test["_id"]
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab tests: {str(e)}")

# Lab Orders Management
@api_router.post("/lab-orders")
async def create_lab_order(order_data: dict, current_user: User = Depends(get_current_active_user)):
    """Create a new lab order"""
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": order_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Generate order number
        count = await db.lab_orders.count_documents({})
        order_number = f"LAB-{count + 1:06d}"
        
        # Create lab order
        lab_order = LabOrder(
            order_number=order_number,
            ordered_by=current_user.username,
            **order_data
        )
        
        lab_order_dict = jsonable_encoder(lab_order)
        await db.lab_orders.insert_one(lab_order_dict)
        
        return lab_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lab order: {str(e)}")

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
        
        orders = await db.lab_orders.find(query).sort("ordered_at", -1).to_list(100)
        return [LabOrder(**order) for order in orders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lab orders: {str(e)}")

@api_router.get("/lab-orders/{order_id}")
async def get_lab_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Get specific lab order details"""
    try:
        order = await db.lab_orders.find_one({"id": order_id})
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
        order = await db.lab_orders.find_one({"id": result_data["lab_order_id"]})
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
        
        results = await db.lab_results.find(query).sort("result_date", -1).to_list(100)
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
        patient = await db.patients.find_one({"id": lab_result.patient_id})
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
async def create_insurance_card(card_data: dict, current_user: User = Depends(get_current_active_user)):
    """Add insurance card information for a patient"""
    try:
        # Verify patient exists
        patient = await db.patients.find_one({"id": card_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        insurance_card = InsuranceCard(**card_data)
        card_dict = jsonable_encoder(insurance_card)
        await db.insurance_cards.insert_one(card_dict)
        
        return insurance_card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating insurance card: {str(e)}")

@api_router.get("/insurance/patient/{patient_id}")
async def get_patient_insurance(patient_id: str, current_user: User = Depends(get_current_active_user)):
    """Get insurance cards for a patient"""
    try:
        cards = await db.insurance_cards.find({
            "patient_id": patient_id,
            "is_active": True
        }).sort("is_primary", -1).to_list(10)
        
        return [InsuranceCard(**card) for card in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving insurance cards: {str(e)}")

@api_router.post("/insurance/verify-eligibility")
async def verify_eligibility(verification_data: dict, current_user: User = Depends(get_current_active_user)):
    """Verify insurance eligibility (mock implementation)"""
    try:
        patient_id = verification_data["patient_id"]
        insurance_card_id = verification_data["insurance_card_id"]
        
        # Get insurance card
        card = await db.insurance_cards.find_one({"id": insurance_card_id})
        if not card:
            raise HTTPException(status_code=404, detail="Insurance card not found")
        
        # Mock eligibility response (in production, would call real payer APIs)
        mock_response = {
            "patient_id": patient_id,
            "insurance_card_id": insurance_card_id,
            "eligibility_status": "active",
            "benefits_summary": {
                "plan_type": "PPO" if card["insurance_type"] == "commercial" else card["insurance_type"].upper(),
                "network_status": "in_network",
                "effective_date": card["effective_date"],
                "plan_description": f"{card['payer_name']} {card['insurance_type'].title()} Plan"
            },
            "copay_amounts": {
                "primary_care": card.get("copay_primary", 25.00),
                "specialist": card.get("copay_specialist", 45.00),
                "emergency_room": 150.00,
                "urgent_care": 75.00
            },
            "deductible_info": {
                "annual_deductible": card.get("deductible", 1500.00),
                "deductible_met": card.get("deductible_met", 0.00),
                "remaining_deductible": card.get("deductible", 1500.00) - card.get("deductible_met", 0.00)
            },
            "coverage_details": {
                "preventive_care": "100% covered",
                "lab_work": "80% after deductible",
                "imaging": "70% after deductible",
                "prescription_drugs": "Generic: $10, Brand: $35"
            },
            "prior_auth_required": [
                "MRI", "CT Scan", "Specialist referrals", "Durable medical equipment"
            ],
            "raw_response": {
                "mock_payer_response": "Eligibility verified successfully",
                "transaction_id": str(uuid.uuid4()),
                "response_time": datetime.utcnow().isoformat()
            }
        }
        
        # Create eligibility response record
        eligibility = EligibilityResponse(
            **mock_response,
            checked_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
        
        eligibility_dict = jsonable_encoder(eligibility)
        await db.eligibility_responses.insert_one(eligibility_dict)
        
        return eligibility
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
    """Initialize common ICD-10 diagnosis codes"""
    try:
        existing = await db.icd10_codes.count_documents({})
        if existing > 0:
            return {"message": "ICD-10 codes already initialized", "count": existing}
        
        common_codes = [
            {"code": "Z00.00", "description": "Encounter for general adult medical examination without abnormal findings", "category": "Preventive Care"},
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "category": "Endocrine"},
            {"code": "I10", "description": "Essential hypertension", "category": "Cardiovascular"},
            {"code": "E78.5", "description": "Hyperlipidemia, unspecified", "category": "Endocrine"},
            {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified", "category": "Respiratory"},
            {"code": "M79.3", "description": "Panniculitis, unspecified", "category": "Musculoskeletal"},
            {"code": "R06.02", "description": "Shortness of breath", "category": "Symptoms"},
            {"code": "R50.9", "description": "Fever, unspecified", "category": "Symptoms"},
            {"code": "F32.9", "description": "Major depressive disorder, single episode, unspecified", "category": "Mental Health"},
            {"code": "Z51.11", "description": "Encounter for antineoplastic chemotherapy", "category": "Treatment"}
        ]
        
        # Add IDs to codes
        for code in common_codes:
            code["id"] = str(uuid.uuid4())
        
        await db.icd10_codes.insert_many(common_codes)
        
        return {
            "message": "ICD-10 codes initialized successfully",
            "codes_added": len(common_codes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing ICD-10 codes: {str(e)}")

@api_router.get("/icd10/search")
async def search_icd10_codes(
    query: str,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """Search ICD-10 codes by description"""
    try:
        # Search by description or code
        search_query = {
            "$or": [
                {"description": {"$regex": query, "$options": "i"}},
                {"code": {"$regex": query, "$options": "i"}}
            ]
        }
        
        codes = await db.icd10_codes.find(search_query).limit(limit).to_list(limit)
        
        # Remove MongoDB ObjectId
        for code in codes:
            if "_id" in code:
                del code["_id"]
        
        return codes
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

# 6. Telehealth Models
class TelehealthSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: str
    appointment_id: Optional[str] = None
    session_type: str = "video_call"  # video_call, phone_call, chat
    scheduled_start: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: TelehealthStatus = TelehealthStatus.SCHEDULED
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    patient_join_url: Optional[str] = None
    provider_join_url: Optional[str] = None
    recording_available: bool = False
    recording_url: Optional[str] = None
    tech_issues: List[Dict] = []
    session_notes: Optional[str] = None
    follow_up_required: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

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
        async for referral in db.referrals.find({"patient_id": patient_id}).sort("created_at", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": referral["patient_id"]})
            provider = await db.providers.find_one({"id": referral.get("referring_provider_id")})
            
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
        async for protocol in db.clinical_protocols.find(query).sort("name", 1):
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
        async for measure in db.quality_measures.find({"is_active": True}).sort("name", 1):
            measures.append(measure)
        return measures
    except Exception as e:
        logger.error(f"Error fetching quality measures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching quality measures: {str(e)}")

@api_router.get("/quality-measures/{measure_id}")
async def get_quality_measure_by_id(measure_id: str):
    try:
        measure = await db.quality_measures.find_one({"id": measure_id})
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
        updated_measure = await db.quality_measures.find_one({"id": measure_id})
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
                measure = await db.quality_measures.find_one({"id": measure_id})
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
            async for measure in db.quality_measures.find({"is_active": True}):
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
            patient = await db.patients.find_one({"id": assessment["patient_id"]})
            measure = await db.quality_measures.find_one({"id": assessment["measure_id"]})
            
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
        patient = await db.patients.find_one({"id": user_data["patient_id"]})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if portal user already exists
        existing_user = await db.portal_users.find_one({"patient_id": user_data["patient_id"]})
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
        patient = await db.patients.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get recent encounters
        recent_encounters = []
        async for encounter in db.encounters.find({"patient_id": patient_id}).sort("date", -1).limit(5):
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
        async for lab_order in db.lab_orders.find({"patient_id": patient_id}).sort("created_at", -1).limit(5):
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
        async for message in db.patient_messages.find({"patient_id": patient_id}).sort("created_at", -1):
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
        patient = await db.patients.find_one({"id": portal_data["patient_id"]})
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
        async for access in db.patient_portal_access.find({"is_active": True}).sort("created_at", -1):
            # Get patient name
            patient = await db.patients.find_one({"id": access["patient_id"]})
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
        portal_access = await db.patient_portal_access.find_one({"patient_id": patient_id, "is_active": True})
        if not portal_access:
            raise HTTPException(status_code=404, detail="Patient portal access not found")
        
        # Get patient basic info
        patient = await db.patients.find_one({"id": patient_id})
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
        portal_access = await db.patient_portal_access.find_one({"id": portal_id})
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
        portal_access = await db.patient_portal_access.find_one({"id": portal_id})
        if not portal_access:
            raise HTTPException(status_code=404, detail="Portal access not found")
        
        if "records" not in portal_access.get("features_enabled", []):
            raise HTTPException(status_code=403, detail="Medical records access not enabled for this portal")
        
        patient_id = portal_access["patient_id"]
        
        # Get patient summary data
        patient = await db.patients.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get recent encounters
        encounters = []
        async for encounter in db.encounters.find({"patient_id": patient_id}).sort("encounter_date", -1).limit(10):
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
        async for document in db.clinical_documents.find(query).sort("created_at", -1):
            # Get category name
            category = await db.document_categories.find_one({"id": document.get("category_id")})
            document["category_name"] = category["name"] if category else "Uncategorized"
            
            # Get patient name if applicable
            if document.get("patient_id"):
                patient = await db.patients.find_one({"id": document["patient_id"]})
                document["patient_name"] = f"{patient['name'][0]['given']} {patient['name'][0]['family']}" if patient else "Unknown"
            
            documents.append(document)
            
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@api_router.get("/documents/{document_id}")
async def get_document_by_id(document_id: str):
    try:
        document = await db.clinical_documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get category name
        category = await db.document_categories.find_one({"id": document.get("category_id")})
        document["category_name"] = category["name"] if category else "Uncategorized"
        
        # Get patient name if applicable
        if document.get("patient_id"):
            patient = await db.patients.find_one({"id": document["patient_id"]})
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
        updated_document = await db.clinical_documents.find_one({"id": document_id})
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
        async for document in db.clinical_documents.find({"patient_id": patient_id}).sort("created_at", -1):
            # Get category name
            category = await db.document_categories.find_one({"id": document.get("category_id")})
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
        async for category in db.document_categories.find({"is_active": True}).sort("name", 1):
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
        async for session in db.telehealth_sessions.find(query).sort("scheduled_start", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": session["patient_id"]})
            provider = await db.providers.find_one({"id": session["provider_id"]})
            
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
        session = await db.telehealth_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Get patient and provider names
        patient = await db.patients.find_one({"id": session["patient_id"]})
        provider = await db.providers.find_one({"id": session["provider_id"]})
        
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
        updated_session = await db.telehealth_sessions.find_one({"id": session_id})
        return updated_session
    except Exception as e:
        logger.error(f"Error updating telehealth session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")

@api_router.post("/telehealth/{session_id}/join")
async def join_telehealth_session(session_id: str, join_data: Dict):
    try:
        session = await db.telehealth_sessions.find_one({"id": session_id})
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

# Original endpoints with /telehealth/sessions structure (kept for backwards compatibility)
@api_router.post("/telehealth/sessions")
async def create_telehealth_session(session: TelehealthSession):
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
        async for session in db.telehealth_sessions.find(query).sort("scheduled_start", -1):
            # Get patient and provider names
            patient = await db.patients.find_one({"id": session["patient_id"]})
            provider = await db.providers.find_one({"id": session["provider_id"]})
            
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