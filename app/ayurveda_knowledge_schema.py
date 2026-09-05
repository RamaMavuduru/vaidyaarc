"""
Phase 8B: Ayurveda Knowledge System Schemas.

Pydantic v2 schemas defining:
1. Source provenance & knowledge records (grounded in approved source documents).
2. Deterministic retrieval candidate models.
3. Safety screening & eligibility decision models.
4. Structured recommendation outputs (with strict non-prescription disclaimers).

ZERO diagnostic inference. ZERO invented remedies. 100% Pydantic v2.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class AuthorityLevel(str, Enum):
    """Source authority hierarchy."""
    PRIMARY_OFFICIAL = "primary_official"
    SECONDARY = "secondary"


class RecordType(str, Enum):
    """Classification of knowledge record."""
    HOME_REMEDY = "home_remedy"
    PHARMACOPOEIAL_FORMULATION = "pharmacopoeial_formulation"
    SECONDARY_LITERATURE = "secondary_literature"


class EvidenceType(str, Enum):
    """Type of grounding evidence."""
    OFFICIAL_PRACTICAL = "official_practical"
    OFFICIAL_PHARMACOPOEIAL = "official_pharmacopoeial"
    SECONDARY_REVIEW = "secondary_review"


class AyurvedaEligibilityStatus(str, Enum):
    """Ayurveda intervention safety/eligibility status."""
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    REQUIRES_CLINICIAN_REVIEW = "requires_clinician_review"


class SourceProvenance(BaseModel):
    """Verifiable source document provenance."""
    source_id: str = Field(..., description="Unique source identifier (e.g. 'SRC_CCRAS_HOME_REMEDIES_2005')")
    document_title: str = Field(..., description="Full document title")
    page: Optional[int] = Field(None, description="Page number in original document where record appears")
    section: Optional[str] = Field(None, description="Section, chapter, or monograph heading")
    excerpt: Optional[str] = Field(None, description="Direct text excerpt from source")


class AyurvedaKnowledgeRecord(BaseModel):
    """
    Standardized, source-grounded Ayurveda Knowledge Record.
    Derived strictly from approved source PDFs without hallucination.
    """
    record_id: str = Field(..., description="Unique knowledge record identifier")
    name: str = Field(..., description="Primary name of plant, remedy, or classical formulation")
    aliases: list[str] = Field(default_factory=list, description="Alternative/Sanskrit/common names")
    botanical_name: Optional[str] = Field(None, description="Botanical binomial nomenclature if given in source")
    record_type: RecordType = Field(..., description="Home remedy, pharmacopoeial monograph, or literature entry")
    authority_level: AuthorityLevel = Field(..., description="Source authority ranking")
    evidence_type: EvidenceType = Field(..., description="Evidence category")
    formulation_form: Optional[str] = Field(None, description="Preparation form (e.g. powder, decoction, oil, asava)")
    ingredients: list[str] = Field(default_factory=list, description="Listed botanical/mineral ingredients")
    traditional_indications: list[str] = Field(default_factory=list, description="Indexed symptoms/conditions from source")
    indication_details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed mappings: [{'indication': '...', 'preparation': '...', 'source_dosage': '...'}]"
    )
    preparation_method: Optional[str] = Field(None, description="Source preparation directions")
    source_dosage_info: Optional[str] = Field(None, description="Source dosage guidance (static reference, NOT prescription)")
    anupana: Optional[str] = Field(None, description="Vehicle/adjuvant if specified in source")
    warnings: list[str] = Field(default_factory=list, description="Explicit source warnings or precautions")
    contraindications: list[str] = Field(default_factory=list, description="Explicit source contraindications")
    safety_notes: list[str] = Field(default_factory=list, description="Clinical safety boundaries")
    limitations: list[str] = Field(default_factory=list, description="Scope and usage limitations")
    provenance: SourceProvenance = Field(..., description="Mandatory source document provenance")


class AyurvedaMatchCandidate(BaseModel):
    """Candidate knowledge record matched to patient clinical presentation."""
    record: AyurvedaKnowledgeRecord = Field(..., description="Matched knowledge record")
    matched_symptom: str = Field(..., description="Patient symptom that matched this record")
    match_strength: str = Field(..., description="'direct_indication', 'alias_match', or 'secondary_evidence'")
    rank_score: float = Field(..., description="Deterministic ranking score (authority weighted)")


class SafetyScreeningDecision(BaseModel):
    """Safety and eligibility screening outcome."""
    status: AyurvedaEligibilityStatus = Field(..., description="Final eligibility classification")
    reasons: list[str] = Field(default_factory=list, description="Machine-readable policy and clinical reasons")
    is_emergency_blocked: bool = Field(default=False, description="True if Phase 2A emergency triggered block")
    is_risk_blocked: bool = Field(default=False, description="True if Phase 2B high/urgent risk triggered block")
    is_contraindication_blocked: bool = Field(default=False, description="True if explicit contraindication matched")
    missing_safety_fields: list[str] = Field(default_factory=list, description="Safety context fields that are unknown")


class AyurvedaRecommendationItem(BaseModel):
    """Individual structured recommendation presented for physician review or patient guidance."""
    name: str = Field(..., description="Remedy / formulation name")
    remedy_type: str = Field(..., description="Category: 'practical_home_remedy', 'pharmacopoeial_reference', 'secondary_evidence'")
    matching_symptom: str = Field(..., description="Patient symptom addressed")
    authority_level: str = Field(..., description="Primary official vs Secondary")
    preparation_summary: Optional[str] = Field(None, description="Descriptive preparation from source")
    source_dosage_reference: Optional[str] = Field(None, description="Source dosage for general guidance (NOT prescription)")
    anupana_reference: Optional[str] = Field(None, description="Vehicle if mentioned in source")
    safety_notes: list[str] = Field(default_factory=list, description="Relevant safety reminders and warnings")
    limitations: list[str] = Field(default_factory=list, description="Limitations from source")
    provenance: SourceProvenance = Field(..., description="Verifiable document provenance")
    prescription_disclaimer: str = Field(
        default="This reference is provided for informational and supportive purposes only based on official classical texts. It is NOT a medical prescription or individualized treatment plan. Consult a qualified Ayurvedic physician.",
        description="Mandatory non-prescription disclaimer"
    )


class AyurvedaRecommendationOutput(BaseModel):
    """Unified Phase 8B recommendation output bundle."""
    decision: AyurvedaEligibilityStatus = Field(..., description="Eligibility status")
    summary: str = Field(..., description="Explainable outcome summary")
    recommendations: list[AyurvedaRecommendationItem] = Field(default_factory=list, description="Approved eligible recommendations")
    blocked_reasons: list[str] = Field(default_factory=list, description="Detailed reasons if blocked or deferred")
    safety_findings_summary: dict[str, Any] = Field(default_factory=dict, description="Summary of upstream safety inputs evaluated")
    provenance_sources: list[str] = Field(default_factory=list, description="List of source IDs utilized")
    disclaimer: str = Field(
        default="Ayurveda knowledge in VaidyaArc is grounded strictly in approved government references (API Part II Vol II, CCRAS Home Remedies) and peer-reviewed literature (eCAM). Recommendations require qualified clinician review and do not replace emergency medical care.",
        description="System governance disclaimer"
    )
    non_prescription_disclaimer: str = Field(
        default="This reference is provided for informational and supportive home care guidance only. It does not constitute a medical prescription or diagnostic claim. Consult a qualified Ayurvedic physician or medical practitioner for individualized treatment.",
        description="Mandatory non-prescription disclaimer"
    )
