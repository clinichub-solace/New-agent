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
    """Create pre-built medical form templates"""
    templates = []
    
    # Patient Intake Form
    intake_fields = [
        FormField(
            type="text",
            label="Patient Name",
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
            label="Gender",
            options=["Male", "Female", "Other", "Prefer not to say"],
            smart_tag="{patient_gender}",
            required=True,
            order=3
        ),
        FormField(
            type="text",
            label="Phone Number",
            smart_tag="{patient_phone}",
            required=True,
            order=4
        ),
        FormField(
            type="textarea",
            label="Address",
            smart_tag="{patient_address}",
            required=True,
            order=5
        ),
        FormField(
            type="textarea",
            label="Chief Complaint",
            placeholder="Describe your primary concern or reason for visit",
            required=True,
            order=6
        ),
        FormField(
            type="textarea",
            label="Current Medications",
            placeholder="List all current medications, supplements, and dosages",
            order=7
        ),
        FormField(
            type="textarea",
            label="Allergies",
            placeholder="List any known allergies to medications, foods, or environmental factors",
            order=8
        ),
        FormField(
            type="textarea",
            label="Medical History",
            placeholder="Previous surgeries, chronic conditions, family history",
            order=9
        ),
        FormField(
            type="checkbox",
            label="Insurance Information Verified",
            order=10
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Patient Intake Form",
        "description": "Comprehensive patient intake and registration form",
        "fields": [jsonable_encoder(field) for field in intake_fields],
        "category": "intake",
        "is_template": True,
        "template_name": "patient_intake",
        "status": "active",
        "fhir_mapping": {
            "patient_name": "Patient.name",
            "dob": "Patient.birthDate",
            "gender": "Patient.gender",
            "phone": "Patient.telecom",
            "address": "Patient.address",
            "chief_complaint": "Encounter.reasonCode",
            "medications": "MedicationStatement.medicationCodeableConcept",
            "allergies": "AllergyIntolerance.code",
            "medical_history": "Condition.code"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Vital Signs Form
    vitals_fields = [
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
            type="number",
            label="Height (inches)",
            placeholder="Height in inches",
            validation_rules={"min": 12, "max": 96},
            required=True,
            order=3
        ),
        FormField(
            type="number",
            label="Weight (lbs)",
            placeholder="Weight in pounds",
            validation_rules={"min": 1, "max": 1000},
            required=True,
            order=4
        ),
        FormField(
            type="text",
            label="Blood Pressure",
            placeholder="120/80",
            required=True,
            order=5
        ),
        FormField(
            type="number",
            label="Heart Rate (BPM)",
            placeholder="Beats per minute",
            validation_rules={"min": 30, "max": 200},
            required=True,
            order=6
        ),
        FormField(
            type="number",
            label="Temperature (°F)",
            placeholder="98.6",
            validation_rules={"min": 90, "max": 110},
            required=True,
            order=7
        ),
        FormField(
            type="number",
            label="Oxygen Saturation (%)",
            placeholder="98",
            validation_rules={"min": 70, "max": 100},
            order=8
        ),
        FormField(
            type="number",
            label="Respiratory Rate",
            placeholder="Breaths per minute",
            validation_rules={"min": 8, "max": 40},
            order=9
        ),
        FormField(
            type="textarea",
            label="Notes",
            placeholder="Additional vital signs notes",
            order=10
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Vital Signs Assessment",
        "description": "Standard vital signs measurement form",
        "fields": [jsonable_encoder(field) for field in vitals_fields],
        "category": "vitals",
        "is_template": True,
        "template_name": "vital_signs",
        "status": "active",
        "fhir_mapping": {
            "height": "Observation.valueQuantity (height)",
            "weight": "Observation.valueQuantity (weight)",
            "blood_pressure": "Observation.component (systolic/diastolic)",
            "heart_rate": "Observation.valueQuantity (heart rate)",
            "temperature": "Observation.valueQuantity (body temperature)",
            "oxygen_saturation": "Observation.valueQuantity (oxygen saturation)",
            "respiratory_rate": "Observation.valueQuantity (respiratory rate)"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Pain Assessment Form
    pain_fields = [
        FormField(
            type="text",
            label="Patient Name",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Assessment Date",
            smart_tag="{current_date}",
            required=True,
            order=2
        ),
        FormField(
            type="select",
            label="Pain Scale (0-10)",
            options=["0 - No Pain", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 - Worst Pain"],
            required=True,
            order=3
        ),
        FormField(
            type="textarea",
            label="Pain Location",
            placeholder="Describe where you feel pain",
            required=True,
            order=4
        ),
        FormField(
            type="select",
            label="Pain Character",
            options=["Sharp", "Dull", "Burning", "Stabbing", "Throbbing", "Cramping", "Aching"],
            order=5
        ),
        FormField(
            type="select",
            label="Pain Duration",
            options=["Constant", "Intermittent", "Only with movement", "Only at rest"],
            order=6
        ),
        FormField(
            type="textarea",
            label="What makes it better?",
            placeholder="Activities, medications, positions that help",
            order=7
        ),
        FormField(
            type="textarea",
            label="What makes it worse?",
            placeholder="Activities, positions, times that worsen pain",
            order=8
        ),
        FormField(
            type="checkbox",
            label="Pain interferes with sleep",
            order=9
        ),
        FormField(
            type="checkbox",
            label="Pain interferes with daily activities",
            order=10
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Pain Assessment",
        "description": "Comprehensive pain evaluation form",
        "fields": [jsonable_encoder(field) for field in pain_fields],
        "category": "assessment",
        "is_template": True,
        "template_name": "pain_assessment",
        "status": "active",
        "fhir_mapping": {
            "pain_scale": "Observation.valueInteger (pain intensity)",
            "pain_location": "Observation.bodySite",
            "pain_character": "Observation.component (pain character)",
            "pain_duration": "Observation.component (pain duration)"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Discharge Instructions Form
    discharge_fields = [
        FormField(
            type="text",
            label="Patient Name",
            smart_tag="{patient_name}",
            required=True,
            order=1
        ),
        FormField(
            type="date",
            label="Discharge Date",
            smart_tag="{current_date}",
            required=True,
            order=2
        ),
        FormField(
            type="text",
            label="Attending Physician",
            smart_tag="{provider_name}",
            required=True,
            order=3
        ),
        FormField(
            type="textarea",
            label="Diagnosis",
            placeholder="Primary diagnosis and any secondary conditions",
            required=True,
            order=4
        ),
        FormField(
            type="textarea",
            label="Treatment Provided",
            placeholder="Summary of treatment received",
            required=True,
            order=5
        ),
        FormField(
            type="textarea",
            label="Medications Prescribed",
            placeholder="List medications, dosages, and instructions",
            order=6
        ),
        FormField(
            type="textarea",
            label="Activity Restrictions",
            placeholder="Physical limitations, work restrictions, etc.",
            order=7
        ),
        FormField(
            type="textarea",
            label="Follow-up Instructions",
            placeholder="When to return, who to see, warning signs",
            required=True,
            order=8
        ),
        FormField(
            type="date",
            label="Follow-up Appointment Date",
            order=9
        ),
        FormField(
            type="textarea",
            label="Warning Signs",
            placeholder="When to seek immediate medical attention",
            required=True,
            order=10
        ),
        FormField(
            type="checkbox",
            label="Patient understands discharge instructions",
            required=True,
            order=11
        )
    ]
    
    templates.append({
        "id": str(uuid.uuid4()),
        "title": "Discharge Instructions",
        "description": "Patient discharge planning and instructions form",
        "fields": [jsonable_encoder(field) for field in discharge_fields],
        "category": "discharge",
        "is_template": True,
        "template_name": "discharge_instructions",
        "status": "active",
        "fhir_mapping": {
            "diagnosis": "Condition.code",
            "treatment": "Procedure.code",
            "medications": "MedicationRequest.medicationCodeableConcept",
            "follow_up": "Appointment.description"
        },
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
    total_patients = await db.patients.count_documents({"status": "active"})
    total_invoices = await db.invoices.count_documents({})
    total_enhanced_invoices = await db.enhanced_invoices.count_documents({})
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
    pending_enhanced_invoices = await db.enhanced_invoices.count_documents({"status": {"$in": ["draft", "sent"]}})
    low_stock_items = await db.inventory.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}})
    total_employees = await db.employees.count_documents({"is_active": True})
    
    # Finance stats
    today = date.today()
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
                    "due_date": invoice.get("due_date"),
                    "days_overdue": (date.today() - date.fromisoformat(invoice.get("due_date", date.today().isoformat()))).days if invoice.get("due_date") else 0,
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
                    "due_date": invoice.get("due_date"),
                    "days_overdue": (date.today() - date.fromisoformat(invoice.get("due_date", date.today().isoformat()))).days if invoice.get("due_date") else 0,
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

# Keep existing dashboard stats for backward compatibility
@api_router.get("/dashboard/legacy-stats")
async def get_legacy_dashboard_stats():
    pass

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
async def create_prescription(
    prescription_data: MedicationRequestCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new prescription with safety checks"""
    try:
        # Get medication details
        medication = await db.fhir_medications.find_one({"id": prescription_data.medication_id})
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        # Get patient details
        patient = await db.patients.find_one({"id": prescription_data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check for allergies
        allergy_alerts = await check_drug_allergies(prescription_data.patient_id, prescription_data.medication_id)
        
        # Check for drug interactions
        interaction_alerts = await check_drug_interactions(prescription_data.patient_id, prescription_data.medication_id)
        
        # Create FHIR-compliant dosage instruction
        dosage_instruction = [{
            "text": prescription_data.dosage_text,
            "timing": {
                "repeat": {
                    "frequency": 1,
                    "period": get_frequency_period(prescription_data.frequency),
                    "periodUnit": "d"
                }
            },
            "route": {
                "coding": [{
                    "code": prescription_data.route,
                    "display": prescription_data.route
                }]
            },
            "doseAndRate": [{
                "doseQuantity": {
                    "value": prescription_data.dose_quantity,
                    "unit": prescription_data.dose_unit,
                    "system": "http://unitsofmeasure.org"
                }
            }]
        }]
        
        # Create dispense request
        dispense_request = {
            "quantity": {
                "value": prescription_data.quantity,
                "unit": medication.get("dosage_forms", ["each"])[0]
            },
            "expectedSupplyDuration": {
                "value": prescription_data.days_supply,
                "unit": "days",
                "system": "http://unitsofmeasure.org"
            },
            "numberOfRepeatsAllowed": prescription_data.refills
        }
        
        # Create prescription
        prescription = MedicationRequest(
            medication_id=prescription_data.medication_id,
            medication_display=medication["generic_name"],
            patient_id=prescription_data.patient_id,
            patient_display=f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            encounter_id=prescription_data.encounter_id,
            prescriber_id=prescription_data.prescriber_id,
            prescriber_name=prescription_data.prescriber_name,
            dosage_instruction=dosage_instruction,
            dispense_request=dispense_request,
            reason_code=[{
                "text": prescription_data.indication
            }] if prescription_data.indication else [],
            days_supply=prescription_data.days_supply,
            quantity=prescription_data.quantity,
            refills=prescription_data.refills,
            allergies_checked=True,
            interactions_checked=True,
            allergy_alerts=allergy_alerts,
            interaction_alerts=interaction_alerts,
            status=PrescriptionStatus.DRAFT,
            created_by=current_user.username
        )
        
        # Save prescription
        prescription_dict = jsonable_encoder(prescription)
        await db.prescriptions.insert_one(prescription_dict)
        
        # Create audit log
        await create_prescription_audit_log(
            prescription.id,
            prescription_data.patient_id,
            "created",
            current_user.id,
            current_user.username,
            {"prescription_created": True}
        )
        
        return prescription
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating prescription: {str(e)}")

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

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    appointment = await db.appointments.find_one({"id": appointment_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment(**appointment)

@api_router.put("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: str, status_data: dict):
    try:
        status_data["updated_at"] = datetime.utcnow()
        result = await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": jsonable_encoder(status_data)}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"message": "Appointment status updated successfully"}
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

# Calendar View
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

# Patient Communications System API Endpoints

# Message Templates
@api_router.post("/communications/init-templates")
async def init_message_templates():
    try:
        # Check if templates already exist
        existing = await db.message_templates.count_documents({})
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
async def get_message_templates(type: str = None):
    try:
        query = {"is_active": True}
        if type:
            query["message_type"] = type
        
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
        
        message = PatientMessage(
            id=str(uuid.uuid4()),
            patient_name=patient["name"]["given"][0] + " " + patient["name"]["family"],
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