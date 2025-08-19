# ClinicHub Payroll System Enhancements
# Complete payroll calculations, paystub generation, and check printing

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body, Response
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
from decimal import Decimal, ROUND_HALF_UP
import calendar

# --- ADD (near imports) ---
try:
    from backend.dependencies import get_db, get_current_active_user as get_current_user  # adjust if your project path differs
except Exception:
    # Fallback shims if module path differs in your repo
    async def get_db():
        raise RuntimeError("get_db dependency not found; import path needs adjustment")
    async def get_current_user():
        return type("U", (), {"id": "system", "username": "system"})()

# --- API shape helpers ---

def _with_api_id(doc: dict | None) -> dict | None:
    if not doc:
        return doc
    _id = doc.get("_id") or doc.get("id")
    if _id is not None:
        doc["_id"] = str(_id)
    return doc

def _with_api_id_list(docs: list[dict]) -> list[dict]:
    return [_with_api_id(d) for d in (docs or [])]

def _ensure_totals_count(totals: dict | None) -> dict:
    totals = totals or {}
    if "count" not in totals:
        if "employees" in totals:
            totals["count"] = totals.get("employees", 0)
        else:
            totals["count"] = 0
    return totals

# Enhanced Payroll Models

class PayFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly" 
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"

class TaxFilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_JOINTLY = "married_jointly"
    MARRIED_SEPARATELY = "married_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"

class StateCode(str, Enum):
    AL = "AL"; AK = "AK"; AZ = "AZ"; AR = "AR"; CA = "CA"; CO = "CO"
    CT = "CT"; DE = "DE"; FL = "FL"; GA = "GA"; HI = "HI"; ID = "ID"
    IL = "IL"; IN = "IN"; IA = "IA"; KS = "KS"; KY = "KY"; LA = "LA"
    ME = "ME"; MD = "MD"; MA = "MA"; MI = "MI"; MN = "MN"; MS = "MS"
    MO = "MO"; MT = "MT"; NE = "NE"; NV = "NV"; NH = "NH"; NJ = "NJ"
    NM = "NM"; NY = "NY"; NC = "NC"; ND = "ND"; OH = "OH"; OK = "OK"
    OR = "OR"; PA = "PA"; RI = "RI"; SC = "SC"; SD = "SD"; TN = "TN"
    TX = "TX"; UT = "UT"; VT = "VT"; VA = "VA"; WA = "WA"; WV = "WV"
    WI = "WI"; WY = "WY"; DC = "DC"

class PayrollTaxInfo(BaseModel):
    """Enhanced tax information for payroll processing"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    filing_status: TaxFilingStatus = TaxFilingStatus.SINGLE
    federal_allowances: int = 1
    state_allowances: int = 1
    state_code: StateCode = StateCode.TX
    additional_federal_withholding: Decimal = Field(default=Decimal('0.00'))
    additional_state_withholding: Decimal = Field(default=Decimal('0.00'))
    is_exempt_federal: bool = False
    is_exempt_state: bool = False
    is_exempt_medicare: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EnhancedPayrollRecord(BaseModel):
    """Complete payroll record with all calculations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payroll_period_id: str
    employee_id: str
    employee_name: str
    pay_frequency: PayFrequency
    
    # Earnings
    regular_hours: Decimal = Field(default=Decimal('0.00'))
    overtime_hours: Decimal = Field(default=Decimal('0.00'))
    double_time_hours: Decimal = Field(default=Decimal('0.00'))
    regular_rate: Decimal = Field(default=Decimal('0.00'))
    overtime_rate: Decimal = Field(default=Decimal('0.00'))
    double_time_rate: Decimal = Field(default=Decimal('0.00'))
    
    regular_pay: Decimal = Field(default=Decimal('0.00'))
    overtime_pay: Decimal = Field(default=Decimal('0.00'))
    double_time_pay: Decimal = Field(default=Decimal('0.00'))
    bonus_pay: Decimal = Field(default=Decimal('0.00'))
    commission_pay: Decimal = Field(default=Decimal('0.00'))
    holiday_pay: Decimal = Field(default=Decimal('0.00'))
    sick_pay: Decimal = Field(default=Decimal('0.00'))
    vacation_pay: Decimal = Field(default=Decimal('0.00'))
    other_earnings: Decimal = Field(default=Decimal('0.00'))
    
    # Calculated totals
    gross_pay: Decimal = Field(default=Decimal('0.00'))
    taxable_wages: Decimal = Field(default=Decimal('0.00'))
    
    # Tax withholdings (calculated)
    federal_tax: Decimal = Field(default=Decimal('0.00'))
    state_tax: Decimal = Field(default=Decimal('0.00'))
    social_security_tax: Decimal = Field(default=Decimal('0.00'))
    medicare_tax: Decimal = Field(default=Decimal('0.00'))
    sui_tax: Decimal = Field(default=Decimal('0.00'))  # State Unemployment Insurance
    sdi_tax: Decimal = Field(default=Decimal('0.00'))  # State Disability Insurance
    
    # Pre-tax deductions
    health_insurance: Decimal = Field(default=Decimal('0.00'))
    dental_insurance: Decimal = Field(default=Decimal('0.00'))
    vision_insurance: Decimal = Field(default=Decimal('0.00'))
    retirement_401k: Decimal = Field(default=Decimal('0.00'))
    hsa_contribution: Decimal = Field(default=Decimal('0.00'))
    parking: Decimal = Field(default=Decimal('0.00'))
    
    # Post-tax deductions
    roth_401k: Decimal = Field(default=Decimal('0.00'))
    union_dues: Decimal = Field(default=Decimal('0.00'))
    life_insurance: Decimal = Field(default=Decimal('0.00'))
    garnishments: Decimal = Field(default=Decimal('0.00'))
    other_deductions: Decimal = Field(default=Decimal('0.00'))
    
    # Totals
    total_taxes: Decimal = Field(default=Decimal('0.00'))
    total_pre_tax_deductions: Decimal = Field(default=Decimal('0.00'))
    total_post_tax_deductions: Decimal = Field(default=Decimal('0.00'))
    total_deductions: Decimal = Field(default=Decimal('0.00'))
    net_pay: Decimal = Field(default=Decimal('0.00'))
    
    # YTD Totals
    ytd_gross_pay: Decimal = Field(default=Decimal('0.00'))
    ytd_federal_tax: Decimal = Field(default=Decimal('0.00'))
    ytd_state_tax: Decimal = Field(default=Decimal('0.00'))
    ytd_social_security_tax: Decimal = Field(default=Decimal('0.00'))
    ytd_medicare_tax: Decimal = Field(default=Decimal('0.00'))
    ytd_net_pay: Decimal = Field(default=Decimal('0.00'))
    
    # Check information
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    is_direct_deposit: bool = False
    bank_routing_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    
    # Status
    status: str = "draft"  # draft, calculated, approved, paid, voided
    created_at: datetime = Field(default_factory=datetime.utcnow)
    calculated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

class PaystubData(BaseModel):
    """Paystub generation data"""
    payroll_record_id: str
    company_info: Dict[str, Any]
    employee_info: Dict[str, Any]
    pay_period_info: Dict[str, Any]
    earnings_details: Dict[str, Any]
    deductions_details: Dict[str, Any]
    tax_details: Dict[str, Any]
    net_pay_info: Dict[str, Any]
    ytd_totals: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class DirectDepositInfo(BaseModel):
    """Direct deposit information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    bank_name: str
    routing_number: str = Field(..., min_length=9, max_length=9)
    account_number: str
    account_type: str = "checking"  # checking, savings
    deposit_type: str = "full"  # full, partial, remainder
    deposit_amount: Optional[Decimal] = None  # for partial deposits
    deposit_percentage: Optional[Decimal] = None  # for percentage deposits
    is_active: bool = True
    is_verified: bool = False
    verification_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaxTable(BaseModel):
    """Tax calculation tables"""
    tax_year: int
    tax_type: str  # federal, state, social_security, medicare
    filing_status: Optional[TaxFilingStatus] = None
    state_code: Optional[StateCode] = None
    brackets: List[Dict[str, Any]] = []  # Tax brackets with rates
    standard_deduction: Decimal = Field(default=Decimal('0.00'))
    personal_exemption: Decimal = Field(default=Decimal('0.00'))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Payroll Calculation Engine

class PayrollCalculator:
    """Advanced payroll calculation engine"""
    
    def __init__(self):
        # 2024 tax rates and limits
        self.social_security_rate = Decimal('0.062')
        self.social_security_limit = Decimal('160200')
        self.medicare_rate = Decimal('0.0145')
        self.medicare_additional_rate = Decimal('0.009')  # for high earners
        self.medicare_additional_threshold = Decimal('200000')
        self.futa_rate = Decimal('0.006')
        self.futa_limit = Decimal('7000')
    
    def calculate_regular_pay(self, hours: Decimal, rate: Decimal) -> Decimal:
        """Calculate regular pay"""
        return (hours * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_overtime_pay(self, hours: Decimal, regular_rate: Decimal, 
                             multiplier: Decimal = Decimal('1.5')) -> Decimal:
        """Calculate overtime pay"""
        overtime_rate = regular_rate * multiplier
        return (hours * overtime_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_gross_pay(self, record: EnhancedPayrollRecord) -> Decimal:
        """Calculate total gross pay"""
        earnings = [
            record.regular_pay,
            record.overtime_pay,
            record.double_time_pay,
            record.bonus_pay,
            record.commission_pay,
            record.holiday_pay,
            record.sick_pay,
            record.vacation_pay,
            record.other_earnings
        ]
        return sum(earnings).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_taxable_wages(self, gross_pay: Decimal, pre_tax_deductions: Decimal) -> Decimal:
        """Calculate taxable wages after pre-tax deductions"""
        return (gross_pay - pre_tax_deductions).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_federal_tax(self, taxable_wages: Decimal, filing_status: TaxFilingStatus,
                            allowances: int, additional_withholding: Decimal = Decimal('0.00'),
                            pay_frequency: PayFrequency = PayFrequency.BIWEEKLY) -> Decimal:
        """Calculate federal income tax withholding"""
        # Simplified federal tax calculation
        # In production, use IRS Publication 15 tables
        
        # Annual taxable income
        annual_wages = self._annualize_wages(taxable_wages, pay_frequency)
        
        # Standard deduction (2024)
        standard_deductions = {
            TaxFilingStatus.SINGLE: Decimal('14600'),
            TaxFilingStatus.MARRIED_JOINTLY: Decimal('29200'),
            TaxFilingStatus.MARRIED_SEPARATELY: Decimal('14600'),
            TaxFilingStatus.HEAD_OF_HOUSEHOLD: Decimal('21900')
        }
        
        standard_deduction = standard_deductions.get(filing_status, Decimal('14600'))
        taxable_income = max(Decimal('0'), annual_wages - standard_deduction)
        
        # 2024 tax brackets (simplified)
        if filing_status == TaxFilingStatus.SINGLE:
            brackets = [
                (Decimal('11000'), Decimal('0.10')),
                (Decimal('44725'), Decimal('0.12')),
                (Decimal('95375'), Decimal('0.22')),
                (Decimal('182050'), Decimal('0.24')),
                (Decimal('231250'), Decimal('0.32')),
                (Decimal('578125'), Decimal('0.35')),
                (float('inf'), Decimal('0.37'))
            ]
        else:  # Simplified - use single rates for now
            brackets = [
                (Decimal('22000'), Decimal('0.10')),
                (Decimal('89450'), Decimal('0.12')),
                (Decimal('190750'), Decimal('0.22')),
                (Decimal('364200'), Decimal('0.24')),
                (Decimal('462500'), Decimal('0.32')),
                (Decimal('693750'), Decimal('0.35')),
                (float('inf'), Decimal('0.37'))
            ]
        
        # Calculate tax using brackets
        annual_tax = Decimal('0')
        previous_bracket = Decimal('0')
        
        for bracket_limit, rate in brackets:
            if taxable_income <= previous_bracket:
                break
            
            taxable_in_bracket = min(taxable_income, Decimal(str(bracket_limit))) - previous_bracket
            annual_tax += taxable_in_bracket * rate
            previous_bracket = Decimal(str(bracket_limit))
            
            if taxable_income <= bracket_limit:
                break
        
        # Convert to pay period amount
        periods_per_year = self._get_periods_per_year(pay_frequency)
        period_tax = (annual_tax / periods_per_year).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return period_tax + additional_withholding
    
    def calculate_state_tax(self, taxable_wages: Decimal, state_code: StateCode,
                          filing_status: TaxFilingStatus, allowances: int,
                          additional_withholding: Decimal = Decimal('0.00'),
                          pay_frequency: PayFrequency = PayFrequency.BIWEEKLY) -> Decimal:
        """Calculate state income tax (simplified - Texas has no state income tax)"""
        
        # States with no income tax
        no_tax_states = [StateCode.TX, StateCode.FL, StateCode.WA, StateCode.NV, 
                        StateCode.TN, StateCode.SD, StateCode.WY, StateCode.AK, StateCode.NH]
        
        if state_code in no_tax_states:
            return Decimal('0.00')
        
        # Simplified state tax calculation (use flat rate for demo)
        state_rates = {
            StateCode.CA: Decimal('0.05'),
            StateCode.NY: Decimal('0.045'),
            StateCode.IL: Decimal('0.0495'),
            # Add more states as needed
        }
        
        rate = state_rates.get(state_code, Decimal('0.03'))  # Default 3%
        annual_wages = self._annualize_wages(taxable_wages, pay_frequency)
        annual_tax = annual_wages * rate
        periods_per_year = self._get_periods_per_year(pay_frequency)
        
        return (annual_tax / periods_per_year + additional_withholding).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_social_security_tax(self, taxable_wages: Decimal, ytd_taxable_wages: Decimal) -> Decimal:
        """Calculate Social Security tax with wage limit"""
        if ytd_taxable_wages >= self.social_security_limit:
            return Decimal('0.00')
        
        taxable_amount = min(taxable_wages, self.social_security_limit - ytd_taxable_wages)
        return (taxable_amount * self.social_security_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_medicare_tax(self, taxable_wages: Decimal, ytd_taxable_wages: Decimal) -> Decimal:
        """Calculate Medicare tax with additional tax for high earners"""
        regular_medicare = (taxable_wages * self.medicare_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Additional Medicare tax for high earners
        if ytd_taxable_wages + taxable_wages > self.medicare_additional_threshold:
            additional_amount = min(taxable_wages, 
                                  (ytd_taxable_wages + taxable_wages) - self.medicare_additional_threshold)
            additional_medicare = (additional_amount * self.medicare_additional_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)
            return regular_medicare + additional_medicare
        
        return regular_medicare
    
    def _annualize_wages(self, wages: Decimal, pay_frequency: PayFrequency) -> Decimal:
        """Convert pay period wages to annual amount"""
        multipliers = {
            PayFrequency.WEEKLY: 52,
            PayFrequency.BIWEEKLY: 26,
            PayFrequency.SEMIMONTHLY: 24,
            PayFrequency.MONTHLY: 12,
            PayFrequency.QUARTERLY: 4,
            PayFrequency.ANNUALLY: 1
        }
        return wages * Decimal(str(multipliers.get(pay_frequency, 26)))
    
    def _get_periods_per_year(self, pay_frequency: PayFrequency) -> Decimal:
        """Get number of pay periods per year"""
        periods = {
            PayFrequency.WEEKLY: 52,
            PayFrequency.BIWEEKLY: 26,
            PayFrequency.SEMIMONTHLY: 24,
            PayFrequency.MONTHLY: 12,
            PayFrequency.QUARTERLY: 4,
            PayFrequency.ANNUALLY: 1
        }
        return Decimal(str(periods.get(pay_frequency, 26)))
    
    def calculate_net_pay(self, gross_pay: Decimal, total_taxes: Decimal, 
                         total_deductions: Decimal) -> Decimal:
        """Calculate net pay"""
        return (gross_pay - total_taxes - total_deductions).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)

# Check Printing Models

class CheckPrintFormat(str, Enum):
    STANDARD = "standard"
    LASER = "laser"
    DOT_MATRIX = "dot_matrix"
    DIRECT_DEPOSIT_STUB = "direct_deposit_stub"

class PayrollCheck(BaseModel):
    """Payroll check generation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payroll_record_id: str
    check_number: str
    check_date: date
    pay_to: str
    amount: Decimal
    amount_in_words: str
    memo: str
    bank_routing_number: str

# --- Repo helpers ---

async def ensure_indexes(db):
    """Create indexes if they don't exist, handle conflicts gracefully"""
    try:
        indexes_to_create = [
            (db.time_entries, [("employee_id", 1), ("date", 1)], "time_entries_emp_date"),
            (db.payroll_runs, [("period_id", 1), ("status", 1)], "run_period_status"),  # Use consistent name
            (db.financial_transactions, [("source.kind", 1), ("source.id", 1)], "fin_src"),
            (db.payroll_records, [("payroll_period_id", 1), ("employee_id", 1)], "payrec_period_emp"),
        ]
        
        for collection, fields, name in indexes_to_create:
            try:
                # First try to drop any conflicting indexes
                try:
                    existing_indexes = await collection.list_indexes().to_list(length=None)
                    for idx in existing_indexes:
                        idx_name = idx.get("name", "")
                        idx_key = idx.get("key", {})
                        # Check if there's a conflicting index with same fields but different name
                        if (idx_name != name and idx_name != "_id_" and 
                            list(idx_key.items()) == fields):
                            print(f"[INFO] Dropping conflicting index {idx_name} to create {name}")
                            await collection.drop_index(idx_name)
                except Exception as drop_e:
                    print(f"[INFO] Could not check/drop existing indexes: {drop_e}")
                
                await collection.create_index(fields, name=name, background=True)
            except Exception as e:
                # If index already exists with different name or other conflicts, continue
                if "already exists" in str(e) or "IndexOptionsConflict" in str(e):
                    print(f"[INFO] Index {name} already exists or has conflicts, skipping: {e}")
                else:
                    print(f"[WARN] Failed to create index {name}: {e}")
    except Exception as e:
        print(f"[ERROR] Failed to ensure indexes: {e}")

async def get_payroll_record(db, payroll_record_id: str) -> Dict[str, Any]:
    rec = await db.payroll_records.find_one({"id": payroll_record_id})
    if not rec:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    return rec

async def get_pay_period(db, period_id: str) -> Dict[str, Any]:
    p = await db.pay_periods.find_one({"id": period_id})
    if not p:
        raise HTTPException(status_code=400, detail="Invalid payroll_period_id")
    return p

async def list_time_entries(db, employee_id: str, start_dt: date, end_dt: date) -> List[Dict[str, Any]]:
    cur = db.time_entries.find({"employee_id": employee_id, "date": {"$gte": start_dt.isoformat(), "$lte": end_dt.isoformat()}})
    return [e async for e in cur]

async def get_employee_profile(db, employee_id: str) -> Dict[str, Any]:
    emp = await db.employees.find_one({"id": employee_id})
    if not emp:
        raise HTTPException(status_code=400, detail="Employee not found")
    return emp

async def get_or_create_payroll_check(db, payroll_record_id: str) -> Dict[str, Any]:
    chk = await db.payroll_checks.find_one({"payroll_record_id": payroll_record_id})
    if chk:
        return chk
    chk = {
        "id": str(uuid.uuid4()),
        "payroll_record_id": payroll_record_id,
        "is_void": False,
        "created_at": datetime.utcnow(),
    }
    await db.payroll_checks.insert_one(chk)
    return chk

def D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# API Endpoints Router

payroll_router = APIRouter(prefix="/api/payroll", tags=["payroll"])

@payroll_router.post("/calculate/{payroll_record_id}")
async def calculate_payroll(
    payroll_record_id: str,
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Calculate payroll for a specific record (gross → net).
    - Pulls time entries for period
    - Applies pre/post-tax deductions and taxes
    - Updates payroll_record totals and sets status=calculated
    """
    await ensure_indexes(db)

    record = await get_payroll_record(db, payroll_record_id)
    period = await get_pay_period(db, record["payroll_period_id"])
    employee = await get_employee_profile(db, record["employee_id"])

    # Pull hours from time_entries (if hours not already finalized in record)
    entries = await list_time_entries(db, record["employee_id"], date.fromisoformat(period["start_date"]), date.fromisoformat(period["end_date"]))
    hours_reg = sum(D(e.get("hours_regular", 0)) for e in entries)
    hours_ot  = sum(D(e.get("hours_ot", 0)) for e in entries)
    hours_dt  = sum(D(e.get("hours_double", 0)) for e in entries)

    # Resolve rates
    regular_rate = D(record.get("regular_rate") or employee.get("hourly_rate") or 0)
    overtime_rate = D(record.get("overtime_rate") or (regular_rate * D("1.5")))
    double_rate = D(record.get("double_time_rate") or (regular_rate * D("2.0")))

    calc = PayrollCalculator()

    regular_pay = calc.calculate_regular_pay(hours_reg, regular_rate)
    overtime_pay = calc.calculate_overtime_pay(hours_ot, regular_rate, D("1.5"))
    double_pay = calc.calculate_overtime_pay(hours_dt, regular_rate, D("2.0"))

    # Other earnings from record (defaults 0)
    bonus = D(record.get("bonus_pay"))
    commission = D(record.get("commission_pay"))
    holiday = D(record.get("holiday_pay"))
    sick = D(record.get("sick_pay"))
    vacation = D(record.get("vacation_pay"))
    other = D(record.get("other_earnings"))

    gross_pay = sum([regular_pay, overtime_pay, double_pay, bonus, commission, holiday, sick, vacation, other]).quantize(Decimal("0.01"))

    # Pre-tax deductions
    pretax = sum([
        D(record.get("health_insurance")),
        D(record.get("dental_insurance")),
        D(record.get("vision_insurance")),
        D(record.get("retirement_401k")),
        D(record.get("hsa_contribution")),
        D(record.get("parking")),
    ]).quantize(Decimal("0.01"))

    taxable_wages = calc.calculate_taxable_wages(gross_pay, pretax)

    # Tax info
    tax_info = (record.get("tax_info") or {})  # could embed a light structure on the record
    filing_status = TaxFilingStatus(tax_info.get("filing_status", "single"))
    state_code = StateCode(tax_info.get("state_code", "TX"))
    fed_allow = int(tax_info.get("federal_allowances", 1) or 1)
    addl_fed = D(tax_info.get("additional_federal_withholding"))
    addl_state = D(tax_info.get("additional_state_withholding"))
    pay_freq = PayFrequency(record.get("pay_frequency", "biweekly"))

    # YTD taxable wages (simplified: sum posted payroll_records for employee this year)
    this_year = str(datetime.utcnow().year)
    ytd_cur = db.payroll_records.aggregate([
        {"$match": {"employee_id": record["employee_id"], "status": "paid", "created_at": {"$gte": datetime(int(this_year), 1, 1)}}},
        {"$group": {"_id": None, "ytd_taxable": {"$sum": "$taxable_wages"}}}
    ])
    ytd_doc = None
    async for d in ytd_cur:
        ytd_doc = d
    ytd_taxable = D((ytd_doc or {}).get("ytd_taxable", 0))

    # Taxes (simplified but deterministic)
    federal_tax = calc.calculate_federal_tax(taxable_wages, filing_status, fed_allow, addl_fed, pay_freq)
    state_tax = calc.calculate_state_tax(taxable_wages, state_code, filing_status, fed_allow, addl_state, pay_freq)
    ss_tax = calc.calculate_social_security_tax(taxable_wages, ytd_taxable)
    medicare_tax = calc.calculate_medicare_tax(taxable_wages, ytd_taxable)

    total_taxes = sum([federal_tax, state_tax, ss_tax, medicare_tax]).quantize(Decimal("0.01"))

    # Post-tax deductions
    posttax = sum([
        D(record.get("roth_401k")),
        D(record.get("union_dues")),
        D(record.get("life_insurance")),
        D(record.get("garnishments")),
        D(record.get("other_deductions")),
    ]).quantize(Decimal("0.01"))

    total_deductions = (pretax + posttax + total_taxes).quantize(Decimal("0.01"))
    net_pay = calc.calculate_net_pay(gross_pay, total_taxes, pretax + posttax)

    # Persist computed fields
    updates = {
        "regular_hours": str(hours_reg), "overtime_hours": str(hours_ot), "double_time_hours": str(hours_dt),
        "regular_rate": str(regular_rate), "overtime_rate": str(overtime_rate), "double_time_rate": str(double_rate),
        "regular_pay": str(regular_pay), "overtime_pay": str(overtime_pay), "double_time_pay": str(double_pay),
        "gross_pay": str(gross_pay), "taxable_wages": str(taxable_wages),
        "federal_tax": str(federal_tax), "state_tax": str(state_tax),
        "social_security_tax": str(ss_tax), "medicare_tax": str(medicare_tax),
        "total_taxes": str(total_taxes), "total_pre_tax_deductions": str(pretax),
        "total_post_tax_deductions": str(posttax), "total_deductions": str(total_deductions),
        "net_pay": str(net_pay),
        "status": "calculated",
        "calculated_at": datetime.utcnow(),
        "updated_by": current_user.username,
    }
    await db.payroll_records.update_one({"id": payroll_record_id}, {"$set": updates})
    record.update(updates)
    return record

@payroll_router.get("/paystub/{payroll_record_id}")
async def generate_paystub(
    payroll_record_id: str,
    db=Depends(get_db),
):
    """
    Generate a paystub JSON (PDF rendering can be handled by a separate service or added later).
    Returns structured PaystubData; FE/print service can convert to PDF.
    """
    record = await get_payroll_record(db, payroll_record_id)
    emp = await get_employee_profile(db, record["employee_id"])
    period = await get_pay_period(db, record["payroll_period_id"])

    stub = {
        "payroll_record_id": payroll_record_id,
        "company_info": {"name": "Your Clinic", "address": "—"},
        "employee_info": {"name": emp.get("name"), "employee_id": emp.get("id"), "last4": (emp.get("ssn_last4") or "XXXX")},
        "pay_period_info": {"start_date": period["start_date"], "end_date": period["end_date"], "pay_date": record.get("check_date") or date.today().isoformat()},
        "earnings_details": {
            "regular_hours": record.get("regular_hours"), "regular_pay": record.get("regular_pay"),
            "overtime_hours": record.get("overtime_hours"), "overtime_pay": record.get("overtime_pay"),
            "double_time_hours": record.get("double_time_hours"), "double_time_pay": record.get("double_time_pay"),
            "other_earnings": {
                "bonus_pay": record.get("bonus_pay"), "commission_pay": record.get("commission_pay"),
                "holiday_pay": record.get("holiday_pay"), "sick_pay": record.get("sick_pay"),
                "vacation_pay": record.get("vacation_pay"), "other_earnings": record.get("other_earnings"),
            },
            "gross_pay": record.get("gross_pay"),
        },
        "deductions_details": {
            "pre_tax": {
                "health_insurance": record.get("health_insurance"),
                "dental_insurance": record.get("dental_insurance"),
                "vision_insurance": record.get("vision_insurance"),
                "retirement_401k": record.get("retirement_401k"),
                "hsa_contribution": record.get("hsa_contribution"),
                "parking": record.get("parking"),
            },
            "post_tax": {
                "roth_401k": record.get("roth_401k"),
                "union_dues": record.get("union_dues"),
                "life_insurance": record.get("life_insurance"),
                "garnishments": record.get("garnishments"),
                "other_deductions": record.get("other_deductions"),
            }
        },
        "tax_details": {
            "federal_tax": record.get("federal_tax"),
            "state_tax": record.get("state_tax"),
            "social_security_tax": record.get("social_security_tax"),
            "medicare_tax": record.get("medicare_tax"),
            "total_taxes": record.get("total_taxes"),
        },
        "net_pay_info": {"net_pay": record.get("net_pay")},
        "ytd_totals": {
            "ytd_gross_pay": record.get("ytd_gross_pay", "0.00"),
            "ytd_federal_tax": record.get("ytd_federal_tax", "0.00"),
            "ytd_state_tax": record.get("ytd_state_tax", "0.00"),
            "ytd_social_security_tax": record.get("ytd_social_security_tax", "0.00"),
            "ytd_medicare_tax": record.get("ytd_medicare_tax", "0.00"),
            "ytd_net_pay": record.get("ytd_net_pay", "0.00"),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
    return stub

@payroll_router.post("/check/print/{payroll_record_id}")
async def print_check(
    payroll_record_id: str,
    body: Dict[str, Any] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Assign/check number, capture bank last4 (mask rest), and persist a printable check record.
    """
    record = await get_payroll_record(db, payroll_record_id)
    if D(record.get("net_pay")) <= D("0"):
        raise HTTPException(status_code=400, detail="Net pay is zero or not calculated")

    req = body or {}
    check_no = req.get("check_number") or str(uuid.uuid4())[:8]
    check_date = req.get("check_date") or date.today().isoformat()

    chk = await get_or_create_payroll_check(db, payroll_record_id)
    chk.update({
        "check_number": check_no,
        "check_date": check_date,
        "pay_to": record.get("employee_name", record.get("employee_id")),
        "amount": record.get("net_pay"),
        "printed_at": datetime.utcnow(),
        "printed_by": current_user.username,
    })
    await db.payroll_checks.update_one({"id": chk["id"]}, {"$set": chk}, upsert=True)

    # Optionally: create a Finance EXPENSE posting if not posted yet (idempotent)
    if not record.get("ledger_post_id"):
        fin = {
            "id": str(uuid.uuid4()),
            "direction": "EXPENSE",
            "category": "payroll",
            "amount": record.get("net_pay"),
            "source": {"kind": "payroll_record", "id": payroll_record_id},
            "timestamp": datetime.utcnow(),
        }
        await db.financial_transactions.insert_one(fin)
        await db.payroll_records.update_one({"id": payroll_record_id}, {"$set": {"ledger_post_id": fin["id"]}})

    return {"check": chk, "financial_posted": True}

@payroll_router.get("/tax-tables/{tax_year}")
async def get_tax_tables(
    tax_year: int,
    db=Depends(get_db),
):
    """
    Retrieve tax tables (federal/state) for offline calc; shipped & overrideable.
    """
    cur = db.tax_tables.find({"tax_year": tax_year})
    tables = [t async for t in cur]
    return {"tax_year": tax_year, "tables": tables}

@payroll_router.post("/direct-deposit")
async def setup_direct_deposit(
    deposit_info: DirectDepositInfo,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upsert direct deposit info for employee. Stores masked account; keeps routing full only server-side.
    """
    di = deposit_info.dict()
    di["id"] = di.get("id") or str(uuid.uuid4())
    di["account_last4"] = di["account_number"][-4:] if di.get("account_number") else None
    di["created_by"] = current_user.username
    # Store full routing/account if your security policy allows; otherwise use KMS/Hash
    await db.direct_deposits.update_one({"employee_id": di["employee_id"], "is_active": True}, {"$set": di}, upsert=True)
    # Return masked
    di_masked = {**di, "routing_number": "*********", "account_number": f"****{di['account_last4']}" if di.get("account_last4") else None}
    return di_masked

# ---------- helpers for periods/runs ----------
async def _period_exists(db, start_date: str, end_date: str) -> bool:
    return await db.pay_periods.find_one({"start_date": start_date, "end_date": end_date}) is not None

async def _get_run(db, run_id: str):
    run = await db.payroll_runs.find_one({"id": run_id})
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    return run

async def _ensure_run_indexes(db):
    await db.pay_periods.create_index([("start_date", 1), ("end_date", 1)], name="period_range", background=True)
    await db.payroll_records.create_index([("payroll_period_id", 1)], name="payrec_period", background=True)
    await db.payroll_runs.create_index([("period_id", 1), ("status", 1)], name="run_period_status", background=True)

# ---------- models for periods/runs ----------
class PayPeriodIn(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    frequency: str = Field(..., pattern="^(weekly|biweekly|semimonthly|monthly|quarterly|annually)$")
    closed: bool = False

class RunCreateIn(BaseModel):
    period_id: str

# ---------- endpoints for periods/runs ----------
@payroll_router.post("/periods")
async def create_pay_period(
    body: PayPeriodIn,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    await _ensure_run_indexes(db)
    if await _period_exists(db, body.start_date, body.end_date):
        existing = await db.pay_periods.find_one({"start_date": body.start_date, "end_date": body.end_date})
        return _with_api_id(existing)

    period = {
        "id": str(uuid.uuid4()),
        "start_date": body.start_date,
        "end_date": body.end_date,
        "frequency": body.frequency,
        "closed": body.closed,
        "created_at": datetime.utcnow(),
        "created_by": current_user.username,
    }
    await db.pay_periods.insert_one(period)
    
    # Audit log the period creation
    from backend.utils.audit import audit_log
    await audit_log(db, current_user,
        action="payroll.period.create",
        subject_type="payroll_period",
        subject_id=period["id"],
        meta={"start_date": period["start_date"], "end_date": period["end_date"], "frequency": period["frequency"]}
    )
    
    return _with_api_id(period)

@payroll_router.get("/periods")
async def list_pay_periods(
    open: Optional[bool] = Query(None),
    db=Depends(get_db),
):
    q = {}
    if open is True:
        q["closed"] = False
    cur = db.pay_periods.find(q).sort("start_date", 1)
    items = [p async for p in cur]
    return _with_api_id_list(items)

@payroll_router.post("/runs")
async def create_run(
    body: RunCreateIn,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    await _ensure_run_indexes(db)
    period = await get_pay_period(db, body.period_id)

    existing = await db.payroll_runs.find_one({"period_id": period["id"], "status": {"$in": ["DRAFT", "POSTED"]}})
    if existing:
        existing["totals"] = _ensure_totals_count(existing.get("totals"))
        
        # Audit log for returning existing run
        from backend.utils.audit import audit_log
        await audit_log(db, current_user,
            action="payroll.run.create_or_get",
            subject_type="payroll_run",
            subject_id=existing["id"],
            meta={"period_id": existing["period_id"], "status": existing["status"], "existing": True}
        )
        
        return _with_api_id(existing)

    run = {
        "id": str(uuid.uuid4()),
        "period_id": period["id"],
        "status": "DRAFT",
        "created_at": datetime.utcnow(),
        "created_by": current_user.username,
        "totals": {
            "employees": 0, "gross": "0.00", "taxes": "0.00",
            "deductions": "0.00", "net": "0.00"
        }
    }
    await db.payroll_runs.insert_one(run)
    run["totals"] = _ensure_totals_count(run.get("totals"))
    
    # Audit log for new run creation
    from backend.utils.audit import audit_log
    await audit_log(db, current_user,
        action="payroll.run.create_or_get",
        subject_type="payroll_run",
        subject_id=run["id"],
        meta={"period_id": run["period_id"], "status": run["status"], "existing": False}
    )
    
    return _with_api_id(run)

@payroll_router.get("/runs/{run_id}")
async def get_run(run_id: str, db=Depends(get_db)):
    run = await _get_run(db, run_id)
    run["totals"] = _ensure_totals_count(run.get("totals"))
    return _with_api_id(run)

from backend.payroll_enhancements_taxhook import post_payroll_run_apply_taxes

@payroll_router.post("/runs/{run_id}/post")
async def post_run(
    run_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    # uses the async tax hook: computes taxes if first time, persists breakdown,
    # posts EXPENSE idempotently, marks paid, aggregates totals
    run_doc = await post_payroll_run_apply_taxes(db, run_id, current_user)
    # ensure consistent API shape
    try:
        run_doc["_id"] = str(run_doc.get("_id") or run_doc.get("id"))
    except Exception:
        pass
    # ensure totals.count alias exists (for tests/consumers expecting it)
    if isinstance(run_doc, dict) and "totals" in run_doc:
        totals = run_doc.get("totals") or {}
        if "count" not in totals:
            totals["count"] = totals.get("employees", 0)
            run_doc["totals"] = totals
    
    # Audit log the run posting
    from backend.utils.audit import audit_log
    await audit_log(db, current_user,
        action="payroll.run.post",
        subject_type="payroll_run",
        subject_id=run_id,
        meta={"period_id": run_doc.get("period_id"), "totals": run_doc.get("totals")}
    )
    
    # Notification for run posting
    from backend.utils.notify import notify_user
    target_user_id = getattr(current_user, "id", "system")
    net_amount = run_doc.get('totals', {}).get('net', 0)
    try:
        net_float = float(net_amount)
    except (ValueError, TypeError):
        net_float = 0.0
    
    await notify_user(db,
        user_id=target_user_id,
        type="payroll.run.post",
        title="Payroll run posted",
        body=f"Run {run_doc.get('_id')} posted successfully. Net payroll: ${net_float:,.2f}",
        subject_type="payroll_run",
        subject_id=str(run_doc.get("_id")),
        severity="success",
        meta={"period_id": run_doc.get("period_id"), "totals": run_doc.get("totals")}
    )
    
    return run_doc

@payroll_router.post("/runs/{run_id}/void")
async def void_run(
    run_id: str,
    reason: Optional[str] = Body(default=""),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    run = await _get_run(db, run_id)
    if run.get("status") == "VOID":
        run["totals"] = _ensure_totals_count(run.get("totals"))
        return _with_api_id(run)

    await db.payroll_runs.update_one(
        {"id": run_id},
        {"$set": {"status": "VOID", "void_at": datetime.utcnow(), "void_by": current_user.username, "void_reason": reason or ""}}
    )
    run.update({"status": "VOID", "void_at": datetime.utcnow(), "void_by": current_user.username, "void_reason": reason or ""})
    run["totals"] = _ensure_totals_count(run.get("totals"))
    
    # Audit log the run voiding
    from backend.utils.audit import audit_log
    await audit_log(db, current_user,
        action="payroll.run.void",
        subject_type="payroll_run",
        subject_id=run_id,
        meta={"reason": reason or "", "period_id": run.get("period_id")}
    )
    
    # Notification for run voiding
    from backend.utils.notify import notify_user
    target_user_id = getattr(current_user, "id", "system")
    
    await notify_user(db,
        user_id=target_user_id,
        type="payroll.run.void",
        title="Payroll run voided",
        body=f"Run {run.get('id')} has been marked as VOID. Reason: {reason or 'No reason provided'}",
        subject_type="payroll_run",
        subject_id=str(run.get("id")),
        severity="warning",
        meta={"reason": reason or "", "period_id": run.get("period_id")}
    )
    
    return _with_api_id(run)

@payroll_router.get("/runs/{run_id}/paystubs")
async def list_run_paystubs(
    run_id: str,
    format: Optional[str] = Query(default="json", pattern="^(json|pdf)$"),
    db=Depends(get_db),
):
    run = await _get_run(db, run_id)
    period = await get_pay_period(db, run["period_id"])
    recs_cur = db.payroll_records.find({"payroll_period_id": period["id"]})
    recs = [r async for r in recs_cur]
    stubs = []
    for r in recs:
        stubs.append({
            "payroll_record_id": r.get("id"),
            "employee_id": r.get("employee_id"),
            "employee_name": r.get("employee_name"),
            "period": {"start_date": period["start_date"], "end_date": period["end_date"]},
            "gross": r.get("gross_pay"), "taxes": r.get("total_taxes"),
            "deductions": str(D(r.get("total_pre_tax_deductions")) + D(r.get("total_post_tax_deductions"))),
            "net": r.get("net_pay"),
        })
    if format == "json":
        return stubs
    elif format == "pdf":
        from backend.utils.paystubs_pdf import render_paystubs_pdf
        pdf = render_paystubs_pdf(stubs, clinic_info={
            "name": "Clínica Familia y Salud",
            "address": "13626 Veterans Memorial Dr Suite F, Houston, TX 77014",
            "phone": "(281) 580-8880",
            "email": "info@clinicafamiliaysalud.com",
        })
        
        # Audit log the PDF export
        from backend.utils.audit import audit_log
        # We need to get current_user, but it's not a dependency here, so we'll add it
        # For now, we'll skip audit logging for PDF export from this endpoint
        # The main PDF export will be handled by the dedicated export router
        
        return Response(content=pdf, media_type="application/pdf")
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")