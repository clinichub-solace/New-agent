# ClinicHub EHR Enhancements
# Additional endpoints and models to complete the EHR system

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid

# Enhanced Clinical Decision Support Models

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(str, Enum):
    PREVENTIVE_CARE = "preventive_care"
    DRUG_INTERACTION = "drug_interaction"  
    ALLERGY = "allergy"
    CRITICAL_VALUE = "critical_value"
    CARE_GAP = "care_gap"
    AGE_REMINDER = "age_reminder"

class ClinicalAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    recommended_action: str
    trigger_data: Dict[str, Any] = {}
    is_active: bool = True
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

# Enhanced Lab Integration Models

class LabResultStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    AMENDED = "amended"

class CriticalValueLevel(str, Enum):
    NORMAL = "normal"
    ABNORMAL_LOW = "abnormal_low"
    ABNORMAL_HIGH = "abnormal_high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    PANIC = "panic"

class LabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lab_order_id: str
    patient_id: str
    test_code: str  # LOINC code
    test_name: str
    result_value: str
    result_unit: str
    reference_range: str
    status: LabResultStatus = LabResultStatus.PENDING
    critical_level: CriticalValueLevel = CriticalValueLevel.NORMAL
    result_date: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Preventive Care Models

class PreventiveCareType(str, Enum):
    SCREENING = "screening"
    IMMUNIZATION = "immunization"
    COUNSELING = "counseling"
    MEDICATION = "medication"

class AgeGroup(str, Enum):
    INFANT = "infant"  # 0-1 years
    TODDLER = "toddler"  # 1-3 years
    CHILD = "child"  # 3-12 years
    ADOLESCENT = "adolescent"  # 12-18 years
    ADULT = "adult"  # 18-65 years
    SENIOR = "senior"  # 65+ years

class PreventiveCareGuideline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    care_type: PreventiveCareType
    age_group: AgeGroup
    gender: Optional[str] = None  # "male", "female", or None for both
    start_age: int  # in years
    end_age: Optional[int] = None  # None for no upper limit
    frequency_months: int  # How often this should be done
    description: str
    clinical_indication: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PreventiveCareReminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    guideline_id: str
    guideline_name: str
    due_date: date
    overdue_days: int = 0
    is_completed: bool = False
    completed_date: Optional[date] = None
    provider_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced Family/Social History Models

class RelationshipType(str, Enum):
    MOTHER = "mother"
    FATHER = "father"
    SIBLING = "sibling"
    GRANDPARENT = "grandparent"
    AUNT_UNCLE = "aunt_uncle"
    COUSIN = "cousin"
    CHILD = "child"
    OTHER = "other"

class FamilyHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    relationship: RelationshipType
    relationship_detail: Optional[str] = None  # e.g., "maternal grandmother"
    condition: str
    icd10_code: Optional[str] = None
    age_at_diagnosis: Optional[int] = None
    age_at_death: Optional[int] = None
    cause_of_death: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SmokingStatus(str, Enum):
    NEVER = "never_smoker"
    FORMER = "former_smoker"
    CURRENT = "current_smoker"
    UNKNOWN = "unknown"

class AlcoholUse(str, Enum):
    NEVER = "never"
    OCCASIONAL = "occasional"
    MODERATE = "moderate" 
    HEAVY = "heavy"
    FORMER = "former_user"
    UNKNOWN = "unknown"

class SocialHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    smoking_status: SmokingStatus = SmokingStatus.UNKNOWN
    smoking_packs_per_day: Optional[float] = None
    smoking_years: Optional[int] = None
    quit_smoking_date: Optional[date] = None
    alcohol_use: AlcoholUse = AlcoholUse.UNKNOWN
    alcohol_drinks_per_week: Optional[int] = None
    substance_use: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    education_level: Optional[str] = None
    living_situation: Optional[str] = None
    exercise_frequency: Optional[str] = None
    diet_type: Optional[str] = None
    notes: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Pediatric Growth Chart Models

class GrowthMeasurement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    encounter_id: Optional[str] = None
    age_months: int
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    head_circumference_cm: Optional[float] = None
    bmi: Optional[float] = None
    height_percentile: Optional[float] = None
    weight_percentile: Optional[float] = None
    bmi_percentile: Optional[float] = None
    head_circumference_percentile: Optional[float] = None
    measurement_date: date
    measured_by: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Care Gap Analysis Models

class CareGapType(str, Enum):
    OVERDUE_SCREENING = "overdue_screening"
    MISSING_IMMUNIZATION = "missing_immunization"
    MEDICATION_ADHERENCE = "medication_adherence"
    FOLLOW_UP_VISIT = "follow_up_visit"
    SPECIALIST_REFERRAL = "specialist_referral"
    LAB_MONITORING = "lab_monitoring"

class CareGap(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    gap_type: CareGapType
    title: str
    description: str
    priority: AlertSeverity
    due_date: Optional[date] = None
    overdue_days: int = 0
    recommended_action: str
    responsible_provider: Optional[str] = None
    is_resolved: bool = False
    resolved_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Clinical Pathway Models

class PathwayStep(BaseModel):
    step_number: int
    title: str
    description: str
    criteria: str
    action: str
    next_step: Optional[int] = None
    alternative_step: Optional[int] = None

class ClinicalPathway(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str
    icd10_codes: List[str] = []
    specialty: Optional[str] = None
    steps: List[PathwayStep] = []
    evidence_level: str  # "A", "B", "C"
    guideline_source: str
    version: str = "1.0"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced Medication Adherence Models

class AdherenceStatus(str, Enum):
    EXCELLENT = "excellent"  # >90%
    GOOD = "good"  # 70-90%
    POOR = "poor"  # <70%
    UNKNOWN = "unknown"

class MedicationAdherence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    medication_id: str
    medication_name: str
    prescribed_date: date
    last_refill_date: Optional[date] = None
    days_supply: int
    refills_remaining: int
    adherence_percentage: Optional[float] = None
    adherence_status: AdherenceStatus = AdherenceStatus.UNKNOWN
    barriers: List[str] = []  # cost, side effects, forgetfulness, etc.
    interventions: List[str] = []  # pill box, reminders, education, etc.
    last_assessment_date: Optional[date] = None
    assessed_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)