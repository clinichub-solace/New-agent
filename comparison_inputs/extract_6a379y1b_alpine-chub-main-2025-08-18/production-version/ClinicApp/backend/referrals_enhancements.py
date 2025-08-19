# ClinicHub Referrals Management System
# Comprehensive Provider Network & Referral Coordination

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

# Referral Models

class ReferralStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DECLINED = "declined"

class ReferralUrgency(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"

class InsuranceStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    APPEALING = "appealing"

class CommunicationMethod(str, Enum):
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PORTAL = "portal"
    MAIL = "mail"

class ReferralType(str, Enum):
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    ONGOING_CARE = "ongoing_care"
    SECOND_OPINION = "second_opinion"
    EMERGENCY = "emergency"

# Specialist Models

class SpecialtyType(str, Enum):
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    HEMATOLOGY = "hematology"
    NEPHROLOGY = "nephrology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    ORTHOPEDICS = "orthopedics"
    PSYCHIATRY = "psychiatry"
    PULMONOLOGY = "pulmonology"
    RHEUMATOLOGY = "rheumatology"
    UROLOGY = "urology"
    GENERAL_SURGERY = "general_surgery"
    PEDIATRICS = "pediatrics"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    OPHTHALMOLOGY = "ophthalmology"  
    OTOLARYNGOLOGY = "otolaryngology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    ANESTHESIOLOGY = "anesthesiology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    FAMILY_MEDICINE = "family_medicine"
    INTERNAL_MEDICINE = "internal_medicine"
    OTHER = "other"

class ContactInfo(BaseModel):
    phone: str
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    portal_url: Optional[str] = None

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

class OfficeHours(BaseModel):
    day_of_week: str  # monday, tuesday, etc.
    open_time: str   # HH:MM format
    close_time: str  # HH:MM format
    is_closed: bool = False

class InsuranceNetwork(BaseModel):
    network_name: str
    plan_types: List[str] = []  # HMO, PPO, EPO, POS
    contact_info: Optional[str] = None

class Specialist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    npi_number: Optional[str] = None
    name: str
    credentials: Optional[str] = None  # MD, DO, PA, NP, etc.
    specialty: SpecialtyType
    subspecialty: Optional[str] = None
    
    # Practice Information
    practice_name: str
    practice_type: str = "private"  # private, hospital, clinic, academic
    department: Optional[str] = None
    
    # Contact Information
    contact_info: ContactInfo
    address: Address
    office_hours: List[OfficeHours] = []
    
    # Professional Information
    board_certifications: List[str] = []
    languages_spoken: List[str] = ["English"]
    years_in_practice: Optional[int] = None
    medical_school: Optional[str] = None
    residency: Optional[str] = None
    fellowship: Optional[str] = None
    
    # Referral Information
    accepts_new_patients: bool = True
    typical_wait_time_days: Optional[int] = None
    preferred_referral_method: CommunicationMethod = CommunicationMethod.FAX
    referral_coordinator: Optional[str] = None
    referral_coordinator_phone: Optional[str] = None
    
    # Insurance & Networks
    insurance_networks: List[InsuranceNetwork] = []
    participates_in_medicare: bool = False
    participates_in_medicaid: bool = False
    
    # Rating & Quality
    patient_rating: Optional[float] = None
    total_reviews: int = 0
    quality_scores: Dict[str, Any] = {}
    
    # Metadata
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReferralDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_type: str  # referral_letter, authorization, report, imaging, lab_results
    file_name: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None

class ReferralCommunication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    communication_type: str  # sent, received, follow_up
    method: CommunicationMethod
    direction: str  # outbound, inbound
    subject: Optional[str] = None
    content: str
    sender: str
    recipient: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    response_required: bool = False
    response_deadline: Optional[date] = None

class ReferralAppointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    appointment_type: str  # consultation, procedure, follow_up
    duration_minutes: int = 60
    location: Optional[str] = None
    status: str = "scheduled"  # scheduled, confirmed, cancelled, completed, no_show
    confirmation_method: Optional[CommunicationMethod] = None
    confirmed_at: Optional[datetime] = None
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None
    notes: Optional[str] = None

class ComprehensiveReferral(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referral_number: str = Field(default_factory=lambda: f"REF-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    
    # Core Information
    patient_id: str
    referring_provider_id: str
    specialist_id: str
    referral_type: ReferralType = ReferralType.CONSULTATION
    status: ReferralStatus = ReferralStatus.DRAFT
    urgency: ReferralUrgency = ReferralUrgency.ROUTINE
    
    # Medical Information
    primary_diagnosis: str
    icd10_codes: List[str] = []
    reason_for_referral: str
    clinical_question: Optional[str] = None
    requested_services: List[str] = []
    
    # Patient Information
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    relevant_medical_history: Optional[str] = None
    current_medications: List[str] = []
    allergies: List[str] = []
    vital_signs: Dict[str, Any] = {}
    recent_lab_results: Optional[str] = None
    recent_imaging: Optional[str] = None
    
    # Provider Communication
    clinical_notes: Optional[str] = None
    specific_questions: List[str] = []
    follow_up_instructions: Optional[str] = None
    return_communication_requested: bool = True
    
    # Insurance & Authorization
    insurance_status: InsuranceStatus = InsuranceStatus.NOT_REQUIRED
    authorization_number: Optional[str] = None
    authorization_date: Optional[date] = None
    authorization_expiry: Optional[date] = None
    insurance_notes: Optional[str] = None
    
    # Scheduling Information
    preferred_appointment_date: Optional[date] = None
    preferred_time_of_day: Optional[str] = None  # morning, afternoon, evening
    patient_availability: Optional[str] = None
    transportation_needs: Optional[str] = None
    language_interpreter_needed: Optional[str] = None
    
    # Appointment Details
    appointment: Optional[ReferralAppointment] = None
    
    # Communication History
    communications: List[ReferralCommunication] = []
    
    # Documents
    documents: List[ReferralDocument] = []
    
    # Tracking Information
    date_created: date = Field(default_factory=date.today)
    date_sent: Optional[date] = None
    date_acknowledged: Optional[date] = None
    date_scheduled: Optional[date] = None
    date_completed: Optional[date] = None
    
    # Follow-up Information
    outcome_summary: Optional[str] = None
    specialist_recommendations: Optional[str] = None
    follow_up_needed: bool = False
    follow_up_with_pcp: bool = True
    return_communication_received: bool = False
    
    # Quality & Satisfaction
    patient_satisfaction_score: Optional[int] = None  # 1-5 scale
    referral_quality_score: Optional[int] = None  # 1-5 scale
    time_to_appointment_days: Optional[int] = None
    
    # Internal Tracking
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    internal_notes: Optional[str] = None

class ReferralTemplate(BaseModel):
    """Template for common referral types"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    specialty: SpecialtyType
    referral_type: ReferralType
    reason_template: str
    clinical_notes_template: str
    requested_services: List[str] = []
    standard_questions: List[str] = []
    requires_authorization: bool = False
    typical_urgency: ReferralUrgency = ReferralUrgency.ROUTINE
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReferralOutcome(BaseModel):
    """Track referral outcomes for quality improvement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referral_id: str
    outcome_type: str  # completed, cancelled, no_show, declined
    completion_date: date
    
    # Clinical Outcomes
    diagnosis_confirmed: Optional[bool] = None
    new_diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    procedures_performed: List[str] = []
    medications_prescribed: List[str] = []
    
    # Follow-up Requirements
    follow_up_required: bool = False
    follow_up_specialty: Optional[str] = None
    follow_up_timeframe: Optional[str] = None
    return_to_pcp: bool = True
    
    # Quality Metrics
    time_to_appointment_days: int
    patient_satisfaction: Optional[int] = None
    referring_provider_satisfaction: Optional[int] = None
    
    # Communication
    report_received: bool = False
    report_date: Optional[date] = None
    communication_quality: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReferralAnalytics(BaseModel):
    """Analytics for referral patterns and outcomes"""
    specialty: str
    total_referrals: int
    completed_referrals: int
    completion_rate: float
    average_time_to_appointment: float
    average_patient_satisfaction: float
    top_referral_reasons: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
    quality_metrics: Dict[str, Any]

# Integration Classes

class ReferralLetterGenerator:
    """Generate professional referral letters"""
    
    @staticmethod
    def generate_referral_letter(
        referral: ComprehensiveReferral,
        referring_provider: Dict[str, Any],
        specialist: Specialist,
        patient: Dict[str, Any]
    ) -> str:
        """Generate professional referral letter"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        letter = f"""
{referring_provider.get('practice_name', 'Medical Practice')}
{referring_provider.get('address', '')}
{referring_provider.get('phone', '')}

{current_date}

{specialist.name}, {specialist.credentials or 'MD'}
{specialist.practice_name}
{specialist.address.street}
{specialist.address.city}, {specialist.address.state} {specialist.address.zip_code}

RE: {patient.get('name', 'Patient')}
DOB: {patient.get('date_of_birth', 'N/A')}
MRN: {patient.get('id', 'N/A')}

Dear Dr. {specialist.name.split()[-1]},

I am referring {patient.get('name', 'this patient')} for {referral.referral_type.value} regarding {referral.primary_diagnosis}.

REASON FOR REFERRAL:
{referral.reason_for_referral}

CLINICAL HISTORY:
{referral.history_of_present_illness or 'Patient presents with ' + referral.chief_complaint}

CURRENT MEDICATIONS:
{chr(10).join(f"• {med}" for med in referral.current_medications) if referral.current_medications else "None reported"}

ALLERGIES:
{chr(10).join(f"• {allergy}" for allergy in referral.allergies) if referral.allergies else "NKDA"}

RECENT STUDIES:
{referral.recent_lab_results or 'None available'}
{referral.recent_imaging or ''}

CLINICAL QUESTION:
{referral.clinical_question or f'Please evaluate and provide recommendations for {referral.primary_diagnosis}'}

SPECIFIC SERVICES REQUESTED:
{chr(10).join(f"• {service}" for service in referral.requested_services) if referral.requested_services else "Consultation and recommendations"}

URGENCY: {referral.urgency.value.upper()}

{referral.clinical_notes or ''}

Please contact me at {referring_provider.get('phone', '')} if you need any additional information. I would appreciate a report of your findings and recommendations.

Thank you for your time and expertise in caring for our mutual patient.

Sincerely,

{referring_provider.get('name', 'Referring Provider')}, MD
{referring_provider.get('specialty', '')}

cc: Patient Chart
"""
        return letter

class ReferralWorkflowManager:
    """Manage referral workflow and status updates"""
    
    @staticmethod
    async def create_referral(referral_data: ComprehensiveReferral) -> ComprehensiveReferral:
        """Create new referral with workflow initialization"""
        
        # Set initial status and tracking
        referral_data.status = ReferralStatus.DRAFT
        referral_data.date_created = date.today()
        
        # Auto-assign referral number if not provided
        if not referral_data.referral_number:
            referral_data.referral_number = f"REF-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Add initial communication record
        initial_comm = ReferralCommunication(
            communication_type="created",
            method=CommunicationMethod.PORTAL,
            direction="internal",
            content="Referral created",
            sender=referral_data.created_by,
            recipient="system"
        )
        referral_data.communications.append(initial_comm)
        
        return referral_data
    
    @staticmethod
    async def send_referral(referral_id: str, method: CommunicationMethod) -> bool:
        """Send referral to specialist"""
        # Implementation would:
        # 1. Update status to SENT
        # 2. Record communication
        # 3. Set date_sent
        # 4. Schedule follow-up reminders
        pass
    
    @staticmethod
    async def schedule_appointment(referral_id: str, appointment_data: ReferralAppointment) -> bool:
        """Schedule appointment and update referral status"""
        # Implementation would:
        # 1. Update status to SCHEDULED
        # 2. Add appointment details
        # 3. Set date_scheduled
        # 4. Send confirmation to patient and provider
        pass

class ReferralReporting:
    """Generate referral analytics and reports"""
    
    @staticmethod
    def generate_specialty_analytics(specialty: SpecialtyType, date_range: tuple) -> ReferralAnalytics:
        """Generate analytics for specific specialty"""
        # Implementation would calculate metrics
        pass
    
    @staticmethod
    def generate_provider_referral_report(provider_id: str, date_range: tuple) -> Dict[str, Any]:
        """Generate referral report for specific provider"""
        pass
    
    @staticmethod
    def generate_quality_metrics() -> Dict[str, Any]:
        """Generate overall referral quality metrics"""
        return {
            "completion_rate": 0.85,
            "average_time_to_appointment": 14.5,
            "patient_satisfaction": 4.2,
            "communication_quality": 4.0,
            "authorization_approval_rate": 0.92
        }

# API Router for Referral Management

referral_router = APIRouter(prefix="/api/referrals", tags=["referrals"])

@referral_router.post("/", response_model=ComprehensiveReferral)
async def create_referral(referral: ComprehensiveReferral):
    """Create new referral"""
    return await ReferralWorkflowManager.create_referral(referral)

@referral_router.get("/", response_model=List[ComprehensiveReferral])
async def get_referrals(
    status: Optional[ReferralStatus] = None,
    specialty: Optional[SpecialtyType] = None,
    urgency: Optional[ReferralUrgency] = None
):
    """Get referrals with optional filtering"""
    pass

@referral_router.get("/{referral_id}", response_model=ComprehensiveReferral)
async def get_referral(referral_id: str):
    """Get specific referral"""
    pass

@referral_router.put("/{referral_id}/status")
async def update_referral_status(referral_id: str, status: ReferralStatus):
    """Update referral status"""
    pass

@referral_router.post("/{referral_id}/send")
async def send_referral(referral_id: str, method: CommunicationMethod):
    """Send referral to specialist"""
    return await ReferralWorkflowManager.send_referral(referral_id, method)

@referral_router.post("/{referral_id}/appointment")
async def schedule_appointment(referral_id: str, appointment: ReferralAppointment):
    """Schedule appointment for referral"""
    return await ReferralWorkflowManager.schedule_appointment(referral_id, appointment)

@referral_router.get("/{referral_id}/letter")
async def generate_referral_letter(referral_id: str):
    """Generate referral letter"""
    pass

# Specialist Management Endpoints

specialist_router = APIRouter(prefix="/api/specialists", tags=["specialists"])

@specialist_router.post("/", response_model=Specialist)
async def create_specialist(specialist: Specialist):
    """Add new specialist to network"""
    pass

@specialist_router.get("/", response_model=List[Specialist])
async def get_specialists(
    specialty: Optional[SpecialtyType] = None,
    accepts_new_patients: Optional[bool] = None,
    insurance_network: Optional[str] = None
):
    """Get specialists with optional filtering"""
    pass

@specialist_router.get("/{specialist_id}", response_model=Specialist)
async def get_specialist(specialist_id: str):
    """Get specific specialist"""
    pass

@specialist_router.put("/{specialist_id}")
async def update_specialist(specialist_id: str, specialist: Specialist):
    """Update specialist information"""
    pass

@specialist_router.get("/search")
async def search_specialists(
    query: str,
    specialty: Optional[SpecialtyType] = None,
    location: Optional[str] = None
):
    """Search specialists by name, specialty, or location"""
    pass

# Analytics Endpoints

analytics_router = APIRouter(prefix="/api/referrals/analytics", tags=["referral-analytics"])

@analytics_router.get("/specialty/{specialty}")
async def get_specialty_analytics(specialty: SpecialtyType):
    """Get analytics for specific specialty"""
    return ReferralReporting.generate_specialty_analytics(specialty, None)

@analytics_router.get("/quality-metrics")
async def get_quality_metrics():
    """Get overall referral quality metrics"""
    return ReferralReporting.generate_quality_metrics()

@analytics_router.get("/provider/{provider_id}")
async def get_provider_referral_report(provider_id: str):
    """Get referral report for specific provider"""
    return ReferralReporting.generate_provider_referral_report(provider_id, None)