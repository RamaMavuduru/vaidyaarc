"""
Phase 8A: Normalized Input & Output Schemas.

Defines decoupled Pydantic v2 schemas for:
- Normalized clinical input contracts (accommodating text, translated voice transcripts,
  patient profiles, prior encounters, and OCR document summaries).
- Normalized turn response contracts.
- Structured clinical output contracts.

ZERO external SDK dependencies. 100% Pydantic v2.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class NormalizedMessageDTO(BaseModel):
    """Normalized incoming message payload."""
    original_text: str = Field(..., description="Original raw transcript or text entered by the patient")
    original_language: Optional[str] = Field(default="en", description="Language code of original text (e.g. 'te-IN', 'hi-IN', 'en')")
    english_text: Optional[str] = Field(default=None, description="Normalized English translation if translated by NMT")
    source: Optional[str] = Field(default="patient", description="Source of message: 'patient', 'kiosk', 'clinician'")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Optional STT or NMT confidence score")
    provenance: Optional[str] = Field(default=None, description="Provenance origin tag (e.g. 'stt_sarvam', 'patient_typed')")


class PatientProfileDTO(BaseModel):
    """Baseline patient profile context."""
    age: Optional[int] = Field(default=None, ge=0, le=130, description="Patient age in years")
    sex: Optional[str] = Field(default=None, description="Patient sex/gender ('male', 'female', 'other')")
    medical_conditions: list[str] = Field(default_factory=list, description="Known chronic conditions (e.g. 'Hypertension')")
    allergies: list[str] = Field(default_factory=list, description="Known allergies (e.g. 'Penicillin')")
    chronic_medications: list[dict[str, Any]] = Field(default_factory=list, description="Current chronic medications")
    surgical_history: list[str] = Field(default_factory=list, description="Prior surgical procedures")
    family_history: list[str] = Field(default_factory=list, description="Relevant family medical history")


class PatientLocationDTO(BaseModel):
    """Geographical location metadata for care navigation."""
    city: Optional[str] = Field(default=None, description="City name")
    pincode: Optional[str] = Field(default=None, description="Postal pincode")
    latitude: Optional[float] = Field(default=None, description="GPS Latitude")
    longitude: Optional[float] = Field(default=None, description="GPS Longitude")


class DocumentDTO(BaseModel):
    """Normalized document or lab report summary."""
    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="Document type: 'lab_report', 'prescription', 'discharge_summary'")
    document_date: Optional[str] = Field(default=None, description="Date of investigation or document")
    extracted_text: Optional[str] = Field(default=None, description="Raw OCR text extracted from document")
    structured_biomarkers: list[dict[str, Any]] = Field(default_factory=list, description="Extracted lab tests and values")
    provenance: Optional[str] = Field(default="ocr_extracted", description="Provenance tag")


class NormalizedClinicalInputDTO(BaseModel):
    """
    Standardized, decoupled clinical input payload consumed by the VaidyaArc Brain.
    """
    patient_id: Optional[str] = Field(default="ANONYMOUS", description="Unique patient identifier")
    episode_id: Optional[str] = Field(default="EP_DEFAULT", description="Unique consultation episode identifier")
    channel: Optional[str] = Field(default="text", description="Interaction channel: 'mobile_app', 'kiosk', 'web'")
    message: NormalizedMessageDTO = Field(..., description="Current message turn from patient")
    patient_profile: Optional[PatientProfileDTO] = Field(default_factory=PatientProfileDTO, description="Baseline patient profile")
    patient_location: Optional[PatientLocationDTO] = Field(default=None, description="Patient location for facility matching")
    conversation_context: Optional[dict[str, Any]] = Field(default=None, description="Turn tracking and prior questions")
    previous_encounters: list[dict[str, Any]] = Field(default_factory=list, description="List of structured previous encounter states")
    previous_conversations: list[dict[str, Any]] = Field(default_factory=list, description="Historical conversation transcripts")
    documents: list[DocumentDTO] = Field(default_factory=list, description="Uploaded lab reports and clinical documents")
    investigations: list[dict[str, Any]] = Field(default_factory=list, description="Extracted prior investigations")
    state_snapshot: Optional[dict[str, Any]] = Field(default=None, description="Serialized VaidyaArcState from previous turn")


class TurnResponseDTO(BaseModel):
    """
    Turn-level response delivered back to the client or gateway.
    """
    session_id: str = Field(..., description="Session identifier")
    patient_id: str = Field(..., description="Patient identifier")
    status: str = Field(..., description="'in_progress', 'complete', or 'emergency'")
    conversation_message: Optional[str] = Field(default=None, description="Text prompt for the patient")
    information_complete: bool = Field(default=False, description="Whether required intake information is complete")
    missing_information: list[str] = Field(default_factory=list, description="Remaining required intake slots")
    immediate_attention_required: bool = Field(default=False, description="Phase 2A emergency flag")
    red_flag_status: str = Field(default="no_obvious_red_flags", description="Phase 2A safety status")
    red_flags: list[str] = Field(default_factory=list, description="Detected red flags")
    updated_state: dict[str, Any] = Field(default_factory=dict, description="Updated internal state snapshot")
    clinical_output: Optional[dict[str, Any]] = Field(default=None, description="Full clinical case output if complete")


class StructuredClinicalOutputDTO(BaseModel):
    """
    Comprehensive structured output bundle emitted upon intake completion.
    """
    case_id: str = Field(..., description="Clinical case identifier")
    patient_id: str = Field(..., description="Patient identifier")
    intake_summary: dict[str, Any] = Field(..., description="Phase 1B structured intake fields")
    safety_findings: dict[str, Any] = Field(..., description="Phase 2A safety results")
    risk_assessment: dict[str, Any] = Field(..., description="Phase 2B risk convergence results")
    clinical_case: dict[str, Any] = Field(..., description="Phase 3 structured clinical case")
    care_navigation: Optional[dict[str, Any]] = Field(default=None, description="Phase 4 matched facilities & pathway")
    follow_up_monitoring: Optional[dict[str, Any]] = Field(default=None, description="Phase 5 longitudinal comparison")
    ayurveda_modern_representation: Optional[dict[str, Any]] = Field(default=None, description="Phase 7 dual-perspective representation")
    provenance_notes: list[str] = Field(default_factory=list, description="System traceability metadata")

