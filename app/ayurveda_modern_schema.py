"""
Phase 7: Ayurveda <-> Modern Medicine Representation Schema.

Pydantic models for dual-perspective clinical representation.
Defines:
1. Modern Clinical Perspective (purely descriptive, zero diagnosis).
2. Ayurvedic Descriptive Perspective (explicit symptom descriptors, zero diagnosis, no Dosha/Prakriti classification).
3. Explicit Correspondence Layer (traceable mapping, confidence, uncertainty, non-equivalence warnings).
4. Safety Constraints & Physician Review Context.

ZERO-LLM. 100% DETERMINISTIC.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    """Explicit relationship types between Modern and Ayurvedic descriptors."""
    DESCRIPTIVE_CORRESPONDENCE = "descriptive_correspondence"
    CONTEXTUAL_CORRESPONDENCE = "contextual_correspondence"
    PARTIAL_CORRESPONDENCE = "partial_correspondence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NO_SUPPORTED_MAPPING = "no_supported_mapping"


class MappingConfidence(str, Enum):
    """Confidence in the descriptive mapping (NOT disease probability)."""
    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RepresentationStatus(str, Enum):
    """Status of dual-perspective case representation."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ModernSymptomFeature(BaseModel):
    """Individual symptom feature from structured intake."""
    symptom_name: str = Field(..., description="Name or label of symptom")
    character: Optional[str] = Field(None, description="Quality/character (e.g. burning, sharp, dull)")
    location: Optional[str] = Field(None, description="Anatomical location")
    duration: Optional[str] = Field(None, description="Reported duration")
    severity: Optional[str] = Field(None, description="Reported severity")
    source_field: str = Field(..., description="Originating state field")
    raw_evidence: Optional[str] = Field(None, description="Patient wording or extracted phrase")


class ModernRepresentation(BaseModel):
    """
    Modern clinical perspective (Purely descriptive, zero diagnosis).
    Reuses structured Phase 1B/3 clinical information.
    """
    chief_complaint: Optional[str] = Field(None, description="Primary concern")
    symptom_features: list[ModernSymptomFeature] = Field(default_factory=list, description="Structured symptom details")
    duration: Optional[str] = Field(None, description="Duration from intake")
    severity: Optional[str] = Field(None, description="Severity from intake")
    location: Optional[str] = Field(None, description="Location from intake")
    nature_of_pain: Optional[str] = Field(None, description="Nature/quality of pain")
    associated_symptoms: list[str] = Field(default_factory=list, description="Explicitly reported associated symptoms")
    red_flag_status: str = Field(..., description="Phase 2A safety status (unmodified)")
    immediate_attention_required: bool = Field(default=False, description="Phase 2A emergency flag (unmodified)")
    risk_level: Optional[str] = Field(None, description="Phase 2B risk level (unmodified)")
    risk_score: Optional[int] = Field(None, description="Phase 2B risk score (unmodified)")
    source_traceability: dict[str, Any] = Field(default_factory=dict, description="Field-level provenance mapping")


class AyurvedicConceptMapping(BaseModel):
    """
    Curated Ayurvedic descriptive concept mapped from patient observations.
    NOT a disease diagnosis and NOT a doshic determination.
    """
    concept_id: str = Field(..., description="Unique concept identifier in AYURVEDA_KB_V1")
    sanskrit_name: str = Field(..., description="Classical Sanskrit descriptive term (e.g. Vidaha, Shoola)")
    english_descriptor: str = Field(..., description="Literal English descriptive translation")
    category: str = Field(..., description="Category (e.g. symptom_descriptor, sensory_quality)")
    matched_observations: list[str] = Field(default_factory=list, description="Patient observations that triggered this mapping")
    required_evidence: list[str] = Field(default_factory=list, description="Criteria required by the knowledge base")
    mapping_confidence: MappingConfidence = Field(..., description="Confidence in this descriptive mapping")
    limitations: list[str] = Field(default_factory=list, description="Explicit clinical and descriptive limitations")
    source_reference: Optional[str] = Field(None, description="Source reference or literature note if verified; otherwise None/unspecified")
    is_reference_verified: bool = Field(default=False, description="Whether source citation is explicitly verified (no fabricated citations)")
    evidence_notes: list[str] = Field(default_factory=list, description="Traceability notes linking to patient input")


class AyurvedicAssessmentPlaceholder(BaseModel):
    """
    Explicit placeholder for unassessed systemic Ayurvedic concepts (Dosha / Prakriti).
    Strictly locked to 'not_assessed' to prevent speculative single-symptom inference.
    """
    status: str = Field(default="not_assessed", description="Always 'not_assessed'")
    reason: str = Field(..., description="Clinical justification for withholding assessment")


class AyurvedicRepresentation(BaseModel):
    """
    Ayurvedic descriptive perspective.
    Grounds observations in curated classical descriptors without disease diagnosis or Dosha determination.
    """
    observed_descriptors: list[str] = Field(default_factory=list, description="Patient-reported descriptors identified")
    mapped_concepts: list[AyurvedicConceptMapping] = Field(default_factory=list, description="Explicitly matched concepts from AYURVEDA_KB_V1")
    unmapped_observations: list[str] = Field(default_factory=list, description="Observed symptoms lacking supported Ayurvedic entries")
    dosha_assessment: AyurvedicAssessmentPlaceholder = Field(
        default_factory=lambda: AyurvedicAssessmentPlaceholder(
            status="not_assessed",
            reason="Dosha assessment requires comprehensive clinical examination and is intentionally omitted to prevent speculative inference."
        ),
        description="Explicitly unassessed Dosha placeholder"
    )
    prakriti_assessment: AyurvedicAssessmentPlaceholder = Field(
        default_factory=lambda: AyurvedicAssessmentPlaceholder(
            status="not_assessed",
            reason="Prakriti determination requires individualized constitution evaluation and is intentionally omitted."
        ),
        description="Explicitly unassessed Prakriti placeholder"
    )
    representation_limitations: list[str] = Field(default_factory=list, description="Boundary statements and constraints")
    source_traceability: dict[str, Any] = Field(default_factory=dict, description="Provenance mapping to patient statements")


class CorrespondenceItem(BaseModel):
    """
    Individual correspondence between a Modern clinical feature and an Ayurvedic descriptor.
    """
    modern_concept: str = Field(..., description="Modern clinical feature/symptom")
    ayurvedic_concept: str = Field(..., description="Ayurvedic descriptive concept (or 'none')")
    relationship_type: RelationshipType = Field(..., description="Nature of correspondence")
    confidence: MappingConfidence = Field(..., description="Confidence in mapping")
    evidence: list[str] = Field(default_factory=list, description="Observed evidence connecting concepts")
    uncertainty: str = Field(..., description="Explicit statement of clinical uncertainty")
    limitations: list[str] = Field(default_factory=list, description="Specific limitations of this correspondence")
    equivalence_disclaimer: str = Field(
        default="This correspondence represents descriptive similarity only and does NOT imply clinical or medical equivalence.",
        description="Non-equivalence disclaimer"
    )


class CorrespondenceLayer(BaseModel):
    """
    Correspondence container analyzing the relationship between Modern and Ayurvedic representations.
    """
    correspondences: list[CorrespondenceItem] = Field(default_factory=list, description="List of mapped correspondences")
    overall_correspondence_status: str = Field(..., description="Status (e.g. established_correspondence, partial_correspondence, insufficient_evidence)")
    unmapped_modern_symptoms: list[str] = Field(default_factory=list, description="Modern symptoms with no supported Ayurvedic descriptor")
    summary_explanation: str = Field(..., description="Explainable summary of relationships")


class Phase7SafetyConstraints(BaseModel):
    """
    Safety constraints and clinical disclaimers enforced across Phase 7.
    """
    red_flag_alert_preserved: bool = Field(default=False, description="Whether Phase 2A red flags were detected and preserved")
    emergency_warning: Optional[str] = Field(None, description="Urgent emergency precedence warning if red flags exist")
    risk_assessment_preserved: bool = Field(default=True, description="Whether Phase 2B risk assessment was immutably preserved")
    no_diagnosis_disclaimer: str = Field(
        default="Phase 7 provides structured dual-perspective descriptive representation only. It does NOT generate medical or Ayurvedic diagnoses.",
        description="No diagnosis disclaimer"
    )
    no_treatment_disclaimer: str = Field(
        default="Phase 7 does NOT prescribe medications, herbs, dietary plans, or dosages.",
        description="No treatment disclaimer"
    )
    non_equivalence_disclaimer: str = Field(
        default="Ayurvedic descriptive concepts and modern clinical features are distinct observational frameworks and are NOT medically equivalent.",
        description="Non-equivalence disclaimer"
    )
    missing_not_absent_disclaimer: str = Field(
        default="Symptoms or features not explicitly mentioned by the patient are treated as unassessed, NOT confirmed absent.",
        description="Missing != absent disclaimer"
    )
    physician_review_required: bool = Field(default=True, description="Physician review remains the sole clinical authority")


class AyurvedaModernOutput(BaseModel):
    """
    Final output container for Phase 7: Ayurveda <-> Modern Medicine Representation.
    """
    representation_status: RepresentationStatus = Field(..., description="Overall status of dual representation")
    case_id: str = Field(..., description="Associated clinical case ID or session ID")
    modern_representation: ModernRepresentation = Field(..., description="Structured modern clinical perspective")
    ayurvedic_representation: AyurvedicRepresentation = Field(..., description="Structured Ayurvedic descriptive perspective")
    correspondence: CorrespondenceLayer = Field(..., description="Correspondence layer between perspectives")
    safety_constraints: Phase7SafetyConstraints = Field(default_factory=Phase7SafetyConstraints, description="Safety invariants and disclaimers")
    physician_summary: str = Field(..., description="Concise, non-diagnostic synthesis for physician review")
    formatting_version: str = Field(default="phase7_v1", description="Phase 7 format version")
