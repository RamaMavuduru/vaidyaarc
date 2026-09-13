"""
VaidyaArc Brain - Schema Version 2.2.0
Clinical History Domain Schemas with Attribute-Level Provenance,
Unified Epistemic States, and Versioned Supersession Support.
"""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

SCHEMA_VERSION: str = "2.2.0"


class SourceType(str, Enum):
    """Origin classification of clinical data."""
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    CLINICIAN = "clinician"
    DOCUMENT = "document"
    LAB = "lab"
    SYSTEM = "system"


class EpistemicStatus(str, Enum):
    """Strict epistemic state of clinical findings."""
    REPORTED = "reported"          # Explicitly affirmed by source
    DENIED = "denied"              # Explicitly asked and denied by source
    UNCERTAIN = "uncertain"        # Source expressed doubt, contradiction, or ungrounded
    NOT_ELICITED = "not_elicited"  # Never evaluated or asked during encounter


class ConversationRole(str, Enum):
    """Participant role in the clinical dialogue."""
    PATIENT = "patient"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationTurn(BaseModel):
    """Immutable record of an individual dialogue turn."""
    turn_id: int = Field(..., description="Monotonically increasing turn index")
    request_id: str = Field(..., description="Idempotency key for client request deduplication")
    role: ConversationRole = Field(..., description="Speaker role")
    raw_text: str = Field(..., description="Verbatim raw utterance received or dispatched")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = Field(default="en", description="Detected language/dialect code")
    source_type: SourceType = Field(default=SourceType.PATIENT)


class AttributeEvidence(BaseModel):
    """Fine-grained evidence linking a specific clinical attribute to source dialogue."""
    source_turn_id: int
    source_type: SourceType = SourceType.PATIENT
    evidence_text: str = Field(..., description="Verbatim quote supporting this attribute")
    char_start: Optional[int] = Field(None, description="Nullable start character offset")
    char_end: Optional[int] = Field(None, description="Nullable end character offset")
    extraction_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Calibrated extraction confidence; None if model calibration unavailable"
    )


class VersionedAttribute(BaseModel):
    """Attribute container supporting supersession and historical tracking."""
    attribute_name: str
    current_value: Any
    is_superseded: bool = False
    superseded_at_turn: Optional[int] = None
    superseded_by_turn: Optional[int] = None
    evidence: AttributeEvidence


class SupersessionRecord(BaseModel):
    """Strongly typed record of an explicit clinical correction."""
    entity_id: str
    attribute_name: str
    previous_value: Any
    new_value: Any
    superseded_at_turn: int
    superseded_by_turn: int
    previous_evidence: AttributeEvidence
    new_evidence: AttributeEvidence
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClinicalFinding(BaseModel):
    """Unified clinical entity representation across symptoms, medical history, and ROS."""
    entity_id: str = Field(..., description="Persistent unique identifier for this finding instance")
    canonical_name: str = Field(..., description="Standardized clinical concept name")
    epistemic_status: EpistemicStatus
    verbatim_patient_term: str
    
    # Versioned clinical attributes with individual evidence
    anatomical_site: Optional[VersionedAttribute] = None
    laterality: Optional[VersionedAttribute] = None
    onset: Optional[VersionedAttribute] = None
    duration: Optional[VersionedAttribute] = None
    severity: Optional[VersionedAttribute] = None
    character: Optional[VersionedAttribute] = None
    timing: Optional[VersionedAttribute] = None
    radiation: Optional[VersionedAttribute] = None
    aggravating_factors: List[VersionedAttribute] = Field(default_factory=list)
    relieving_factors: List[VersionedAttribute] = Field(default_factory=list)
    triggers: Optional[VersionedAttribute] = None
    functional_impact: Optional[VersionedAttribute] = None
    
    status_evidence: AttributeEvidence
    superseded_attributes: List[VersionedAttribute] = Field(default_factory=list)
    is_active: bool = True


class DemographicProfile(BaseModel):
    """Demographic and communication profile with explicit epistemic tracking."""
    age: Optional[int] = None
    age_status: EpistemicStatus = EpistemicStatus.NOT_ELICITED
    sex: Optional[str] = None
    sex_status: EpistemicStatus = EpistemicStatus.NOT_ELICITED
    primary_language: str = "en"
    source_type: SourceType = SourceType.PATIENT


class ClinicalDelta(BaseModel):
    """Output produced by LLM cognitive extraction on each patient turn."""
    schema_version: str = Field(default=SCHEMA_VERSION)
    turn_id: int
    extracted_findings: List[ClinicalFinding] = Field(default_factory=list)
    supersessions: List[SupersessionRecord] = Field(default_factory=list)
    unresolved_clarifications: List[str] = Field(default_factory=list)
    llm_sufficiency_recommendation: bool = Field(
        ..., description="Advisory recommendation from LLM on whether intake is sufficient"
    )
    sufficiency_rationale: str = Field(..., description="Clinical justification for recommendation")
    detected_language: str = Field(default="en")


class InterviewStatus(str, Enum):
    """Session lifecycle state."""
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"                 # Approved by deterministic governance
    BOUNDED_PARTIAL = "bounded_partial"   # Reached technical turn ceiling; requires clinician review
    SAFETY_ESCALATED = "safety_escalated" # Interrupted due to emergency safety trigger


class ConsentStatus(str, Enum):
    """Informed consent lifecycle state."""
    CONSENT_PENDING = "consent_pending"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_WITHDRAWN = "consent_withdrawn"


class EvolvingClinicalHistory(BaseModel):
    """The master clinical intake session object holding the append-only ledger and active projection."""
    schema_version: str = Field(default=SCHEMA_VERSION)
    session_id: str
    patient_id: Optional[str] = None
    consent_status: ConsentStatus = ConsentStatus.CONSENT_GRANTED
    turn_count: int = 0
    max_turn_ceiling: int = Field(default=8, description="Configurable technical safety ceiling")
    interview_status: InterviewStatus = InterviewStatus.IN_PROGRESS
    
    demographics: DemographicProfile = Field(default_factory=DemographicProfile)
    
    # Active Clinical Projection (Computed deterministically over versioned ledger)
    chief_complaint: Optional[ClinicalFinding] = None
    associated_findings: List[ClinicalFinding] = Field(default_factory=list)
    review_of_systems: Dict[str, List[ClinicalFinding]] = Field(
        default_factory=dict,
        description="Structured findings keyed by organ system; supports multiple findings per system"
    )
    
    past_medical_history: List[ClinicalFinding] = Field(default_factory=list)
    medications_disclosed: List[ClinicalFinding] = Field(default_factory=list)
    allergies_disclosed: List[ClinicalFinding] = Field(default_factory=list)
    functional_impact: Optional[VersionedAttribute] = None
    relevant_past_episodes: List[Dict[str, Any]] = Field(default_factory=list)
    trauma_history: Optional[VersionedAttribute] = None
    triggers_or_context: Optional[VersionedAttribute] = None
    local_inflammatory_signs: Dict[str, Any] = Field(default_factory=dict)
    casesheet_markdown: Optional[str] = None
    
    conversation_turns: List[ConversationTurn] = Field(default_factory=list)
    prior_question_intents: List[str] = Field(
        default_factory=list,
        description="Log of clinical intents already queried to prevent duplicate questions"
    )
    
    advisory_entropy_score: Optional[float] = None
    unresolved_safety_questions: List[str] = Field(default_factory=list)
    governance_conclusion_rationale: Optional[str] = None
