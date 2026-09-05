"""
Phase 10: Advanced Risk Convergence Schemas.

Pydantic v2 schemas defining:
1. LongitudinalRiskSignal: Granular, explainable risk signal objects.
2. LongitudinalRiskAssessmentDTO: Longitudinal risk score, level, escalation status, and evidence.
3. CompositeRiskOutputDTO: Arbitrated risk synthesis preserving Phase 2B current risk immutably.

100% DETERMINISTIC. ZERO LLM. ZERO DIAGNOSTIC INFERENCE.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


LongitudinalRiskSignalCategory = Literal[
    "recurrence",
    "persistence",
    "historical_escalation",
    "repeated_moderate",
    "multimorbid_burden",
    "biomarker_observation",
    "cross_modal_concordance",
    "data_quality",
]

LongitudinalRiskSignalSeverity = Literal[
    "low",
    "moderate",
    "high",
    "critical",
    "informational",
]

LongitudinalRiskLevel = Literal[
    "LOW",
    "MODERATE",
    "HIGH",
    "URGENT",
]

RiskEscalationStatus = Literal[
    "escalated",
    "stable",
    "de_escalated",
    "insufficient_longitudinal_data",
]

TemporalPersistenceIndex = Literal[
    "acute_isolated",
    "persistent",
    "recurrent",
    "chronic_baseline",
    "unknown",
]

DataCompletenessStatus = Literal[
    "complete",
    "partial",
    "minimal",
    "insufficient",
]

CompositeRiskLevel = Literal[
    "LOW",
    "MODERATE",
    "HIGH",
    "URGENT",
]

EffectiveCarePathway = Literal[
    "routine",
    "urgent",
    "emergency",
    "incomplete",
]


class LongitudinalRiskSignal(BaseModel):
    """
    Granular, deterministic longitudinal risk signal with explicit evidence and provenance.
    """
    signal_id: str = Field(..., description="Unique deterministic signal identifier")
    category: LongitudinalRiskSignalCategory = Field(..., description="Rule category")
    severity: LongitudinalRiskSignalSeverity = Field(..., description="Assessed signal severity")
    weight: float = Field(..., description="Additive point weight")
    evidence: list[str] = Field(default_factory=list, description="Explicit factual evidence supporting this signal")
    rationale: str = Field(..., description="Explainable clinical/observational justification")
    provenance_sources: list[str] = Field(default_factory=list, description="Source encounter IDs, documents, or investigations")


class LongitudinalRiskAssessmentDTO(BaseModel):
    """
    Longitudinal risk convergence assessment bundle derived from historical encounters,
    biomarker observations, and problem registry.
    """
    longitudinal_risk_score: float = Field(default=0.0, description="Additive longitudinal risk score")
    longitudinal_risk_level: LongitudinalRiskLevel = Field(default="LOW", description="Derived longitudinal risk level")
    risk_escalation_status: RiskEscalationStatus = Field(default="stable", description="Longitudinal trajectory status")
    temporal_persistence_index: TemporalPersistenceIndex = Field(default="acute_isolated", description="Chronicity/persistence classification")
    risk_signals: list[LongitudinalRiskSignal] = Field(default_factory=list, description="Active longitudinal risk signals")
    contributing_longitudinal_factors: list[str] = Field(default_factory=list, description="High-level summary of contributing factors")
    longitudinal_evidence: list[str] = Field(default_factory=list, description="Deduplicated evidence items")
    reasoning: str = Field(..., description="Explainable summary of longitudinal risk evaluation")
    data_completeness: DataCompletenessStatus = Field(default="complete", description="Quality and completeness of longitudinal history")
    disclaimer: str = Field(
        default="Longitudinal risk assessment represents deterministic pattern convergence and is not a medical diagnosis.",
        description="Mandatory non-diagnostic disclaimer"
    )


class CompositeRiskOutputDTO(BaseModel):
    """
    Unified risk convergence synthesis combining Phase 2A emergency override,
    Phase 2B current-encounter risk (immutable), and Phase 10 longitudinal risk.
    """
    current_risk: dict[str, Any] = Field(..., description="Phase 2B immutable assessment bundle")
    longitudinal_risk: LongitudinalRiskAssessmentDTO = Field(..., description="Phase 10 longitudinal assessment bundle")
    composite_risk_level: CompositeRiskLevel = Field(..., description="Effective overall risk level")
    effective_care_pathway: EffectiveCarePathway = Field(..., description="Authoritative care pathway")
    composite_reasoning: str = Field(..., description="Unified explainable justification")
    safety_override_applied: bool = Field(default=False, description="True if Phase 2A red flag enforced emergency override")
    override_reason: Optional[str] = Field(default=None, description="Reason for safety override if applied")
    provenance_notes: list[str] = Field(default_factory=list, description="Audit log of risk engines executed")

