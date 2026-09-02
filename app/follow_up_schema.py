"""
Phase 5: Follow-up & Patient Monitoring Intelligence Schema.

Pydantic models for structured clinical state comparison, risk trend tracking,
symptom delta detection, trajectory classification, and monitoring outputs.
Deterministic and 100% serializable.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime


ChangeType = Literal[
    "UNCHANGED",
    "IMPROVED",
    "WORSENED",
    "NEW",
    "RESOLVED",
    "INSUFFICIENT_DATA",
]

RiskTrend = Literal[
    "increased",
    "decreased",
    "unchanged",
    "unknown",
]

TrajectoryType = Literal[
    "initial_encounter",
    "improving",
    "stable",
    "worsening",
    "new_risk_signal",
    "escalation_required",
    "insufficient_information",
]


class FieldComparison(BaseModel):
    """Structured comparison result for a single clinical field."""
    field_name: str = Field(..., description="Name of the clinical field compared (e.g. 'severity', 'duration', 'chief_complaint')")
    previous_value: Optional[Any] = Field(None, description="Value from the previous encounter/state")
    current_value: Optional[Any] = Field(None, description="Value from the current encounter/state")
    change_type: ChangeType = Field(..., description="Categorical change classification")
    evidence: str = Field(..., description="Factual, explainable observation supporting this change classification")


class RiskComparison(BaseModel):
    """Comparison of Phase 2B risk assessment outputs across encounters."""
    previous_risk_level: Optional[str] = Field(None, description="Previous risk level (LOW, MODERATE, HIGH, URGENT)")
    current_risk_level: Optional[str] = Field(None, description="Current risk level (LOW, MODERATE, HIGH, URGENT)")
    previous_risk_score: Optional[int] = Field(None, description="Previous risk score (0-100)")
    current_risk_score: Optional[int] = Field(None, description="Current risk score (0-100)")
    risk_trend: RiskTrend = Field(..., description="Direction of overall risk progression ('increased', 'decreased', 'unchanged', 'unknown')")
    contributing_changes: list[str] = Field(
        default_factory=list,
        description="List of specific clinical changes contributing to risk shift"
    )


class SymptomChangeSummary(BaseModel):
    """Structured delta summary of symptoms across encounters."""
    new_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptoms present in the current encounter that were not in the previous encounter"
    )
    resolved_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptoms with explicit confirmation of cessation/resolution"
    )
    persisting_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptoms present in both encounters"
    )
    unmentioned_symptoms: list[str] = Field(
        default_factory=list,
        description="Previous symptoms not discussed in current encounter (NOT assumed resolved)"
    )


class PatientTrajectory(BaseModel):
    """Deterministic classification of patient trajectory over time."""
    trajectory: TrajectoryType = Field(..., description="Overall trajectory category")
    confidence: str = Field(
        default="high",
        description="Confidence level in the trajectory assessment ('high', 'moderate', 'low')"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Traceable, factual evidence supporting the trajectory decision"
    )


class FollowUpMonitoringOutput(BaseModel):
    """
    Complete output container for Phase 5: Follow-up & Patient Monitoring Intelligence.
    """
    monitoring_status: str = Field(
        ...,
        description="One of: 'initial_encounter', 'stable', 'improving', 'worsening', 'new_risk_signal', 'escalation_required', 'insufficient_information'"
    )
    patient_id: str = Field(..., description="Unique patient identifier")
    session_id: str = Field(..., description="Current session/encounter identifier")
    previous_session_id: Optional[str] = Field(None, description="Prior session identifier if available")
    evaluated_at: str = Field(..., description="ISO 8601 timestamp of evaluation")
    trajectory: PatientTrajectory = Field(..., description="Trajectory classification and evidence")
    risk_comparison: RiskComparison = Field(..., description="Phase 2B risk comparison metrics")
    symptom_changes: SymptomChangeSummary = Field(..., description="Symptom additions, resolutions, and persistences")
    field_comparisons: list[FieldComparison] = Field(
        default_factory=list,
        description="Field-by-field comparison details"
    )
    next_monitoring_action: str = Field(
        ...,
        description="Recommended next monitoring/operational step (non-diagnostic)"
    )
    monitoring_explanation: str = Field(
        ...,
        description="Explainable, evidence-backed narrative summary of the monitoring outcome"
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking data warnings or gaps"
    )
