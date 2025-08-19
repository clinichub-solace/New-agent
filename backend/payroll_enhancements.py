# ClinicHub Payroll System Enhancements
# Complete payroll calculations, paystub generation, and check printing

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
from decimal import Decimal, ROUND_HALF_UP
import calendar

# --- ADD (near imports) ---
try:
    from backend.dependencies import get_db, get_current_user  # adjust if your project path differs
except Exception:
    # Fallback shims if module path differs in your repo
    async def get_db():
        raise RuntimeError("get_db dependency not found; import path needs adjustment")
    async def get_current_user():
        return type("U", (), {"id": "system", "username": "system"})()

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
    await db.time_entries.create_index([("employee_id", 1), ("date", 1)], name="time_entries_emp_date", background=True)
    await db.payroll_runs.create_index([("period_id", 1), ("status", 1)], name="runs_period_status", background=True)
    await db.financial_transactions.create_index([("source.kind", 1), ("source.id", 1)], name="fin_src", background=True)
    await db.payroll_records.create_index([("payroll_period_id", 1), ("employee_id", 1)], name="payrec_period_emp", background=True)

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

    bank_account_number: str
    check_format: CheckPrintFormat = CheckPrintFormat.STANDARD
    is_void: bool = False
    void_reason: Optional[str] = None
    void_date: Optional[date] = None
    printed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# API Endpoints Router

payroll_router = APIRouter(prefix="/api/payroll", tags=["payroll"])

@payroll_router.post("/calculate/{payroll_record_id}")
async def calculate_payroll(payroll_record_id: str):
    """Calculate payroll for a specific record"""
    # Implementation for payroll calculations
    pass

@payroll_router.get("/paystub/{payroll_record_id}")
async def generate_paystub(payroll_record_id: str):
    """Generate paystub for employee"""
    pass

@payroll_router.post("/check/print/{payroll_record_id}")
async def print_check(payroll_record_id: str):
    """Print payroll check"""
    pass

@payroll_router.get("/tax-tables/{tax_year}")
async def get_tax_tables(tax_year: int):
    """Get tax tables for calculations"""
    pass

@payroll_router.post("/direct-deposit")
async def setup_direct_deposit(deposit_info: DirectDepositInfo):
    """Setup employee direct deposit"""
    pass