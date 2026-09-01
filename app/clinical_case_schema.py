"""
Clinical Case Schema for Phase 3.

Pydantic models for structured clinical case representation.
Output from Phase 3: clinical_case_representation node.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class PatientIdentifier(BaseModel):
    """Patient context and demographics."""
    patient_id: str = Field(..., description="Unique patient identifier")
    session_id: str = Field(..., description="Unique session identifier")
    age: Optional[int] = Field(None, description="Patient age in years")
    known_conditions: list[str] = Field(
        default_factory=list,
        description="List of known medical conditions from patient profile"
    )
    known_allergies: list[str] = Field(
        default_factory=list,
        description="List of known allergies from patient profile"
    )


class SymptomDescriptors(BaseModel):
    """Symptom characteristics from structured intake."""
    severity: Optional[str] = Field(None, description="Severity level from Phase 1B")
    character: Optional[str] = Field(None, description="Nature/character of pain from Phase 1B")
    location: Optional[str] = Field(None, description="Body location from Phase 1B")
    associated_symptoms: list[str] = Field(
        default_factory=list,
        description="Associated symptoms from Phase 1B"
    )


class SafetyFindings(BaseModel):
    """Red flag detection results from Phase 2A (unmodified)."""
    red_flag_status: str = Field(
        ...,
        description="One of: red_flags_detected, no_obvious_red_flags, insufficient_information"
    )
    red_flags_detected: list[str] = Field(
        default_factory=list,
        description="List of red flags detected by Phase 2A"
    )
    red_flag_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence for each red flag"
    )
    immediate_attention_required: bool = Field(
        default=False,
        description="Whether immediate clinical attention is required"
    )
    red_flag_rule_summary: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Rule IDs and evidence from Phase 2A"
    )


class RiskAssessment(BaseModel):
    """Risk assessment results from Phase 2B (unmodified)."""
    risk_level: str = Field(
        ...,
        description="Risk classification: LOW, MODERATE, HIGH, URGENT"
    )
    risk_score: int = Field(
        ...,
        description="Risk score (0-100 scale)"
    )
    risk_signals: list[str] = Field(
        default_factory=list,
        description="List of risk signal rule IDs from Phase 2B"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Contributing risk factors from Phase 2B"
    )
    risk_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence items supporting risk assessment"
    )
    risk_reasoning: str = Field(
        ...,
        description="Phase 2B explanation of risk aggregation"
    )
    risk_override_reason: Optional[str] = Field(
        None,
        description="If Phase 2A red flag overrides base risk, explanation here"
    )
    recommended_action: str = Field(
        ...,
        description="Recommended next action from Phase 2B"
    )


class DataQuality(BaseModel):
    """Data quality and completeness metrics."""
    information_complete: bool = Field(
        ...,
        description="Whether all required information was collected"
    )
    completeness_percentage: float = Field(
        ...,
        ge=0.0, le=100.0,
        description="Percentage of expected fields populated (0-100)"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that were not collected in Phase 1B"
    )
    uncertain_fields: list[str] = Field(
        default_factory=list,
        description="Fields with low confidence or ambiguity"
    )
    data_gaps: list[str] = Field(
        default_factory=list,
        description="Gaps in the clinical narrative"
    )


class ClinicalCase(BaseModel):
    """
    Structured clinical case representation.
    
    Combines Phase 1B (intake), Phase 2A (red flags), and Phase 2B (risk)
    into a physician-ready clinical case without diagnosis or treatment.
    """
    
    # 1. Case Metadata
    case_id: str = Field(..., description="Auto-generated case ID")
    created_at: str = Field(..., description="ISO 8601 timestamp of case generation")
    case_status: str = Field(
        ...,
        description="One of: complete, incomplete, pending_review"
    )
    
    # 2. Patient Context
    patient_identifier: PatientIdentifier = Field(
        ...,
        description="Patient identifiers and demographics"
    )
    
    # 3. Chief Complaint & Present Concern
    chief_complaint: Optional[str] = Field(
        None,
        description="Verbatim chief complaint from Phase 1B"
    )
    complaint_narrative: str = Field(
        ...,
        description="Structured narrative of the complaint"
    )
    
    # 4. Temporal Information
    onset_description: Optional[str] = Field(
        None,
        description="Duration/onset from Phase 1B"
    )
    
    # 5. Symptom Characteristics
    symptom_descriptors: SymptomDescriptors = Field(
        ...,
        description="Structured symptom characteristics"
    )
    
    # 6. Patient History Context
    medical_history_summary: list[str] = Field(
        default_factory=list,
        description="Summary of known medical conditions"
    )
    relevant_history_notes: list[str] = Field(
        default_factory=list,
        description="Relevant historical information"
    )
    
    # 7. Safety Signal Integration (Phase 2A - UNMODIFIED)
    safety_findings: SafetyFindings = Field(
        ...,
        description="Red flag detection from Phase 2A"
    )
    
    # 8. Risk Assessment (Phase 2B - UNMODIFIED)
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Risk assessment from Phase 2B"
    )
    
    # 9. Data Quality & Completeness
    data_quality: DataQuality = Field(
        ...,
        description="Data quality metrics"
    )
    
    # 10. Care Pathway Indication
    care_pathway_status: str = Field(
        ...,
        description="One of: emergency, urgent, routine, follow_up, incomplete"
    )
    
    # 11. Physician Notes
    case_summary: str = Field(
        ...,
        description="Deterministic 1-2 sentence clinical summary"
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Suggested next actions (non-prescriptive)"
    )
    follow_up_required: bool = Field(
        ...,
        description="Whether follow-up assessment is needed"
    )
    
    # 12. Traceability
    source_phase_evidence: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Mapping of phase to evidence items"
    )


class ClinicalCaseOutput(BaseModel):
    """
    Validated clinical case output container.
    """
    case_representation: ClinicalCase = Field(
        ...,
        description="The structured clinical case"
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Validation errors (blocking)"
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings (non-blocking)"
    )
    case_ready_for_review: bool = Field(
        ...,
        description="Whether physician can review this case"
    )
    formatting_version: str = Field(
        default="phase3_v1",
        description="Version of clinical case format"
    )
