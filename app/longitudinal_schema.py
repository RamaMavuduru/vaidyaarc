"""
Phase 9: Longitudinal Patient Intelligence Schemas.

Pydantic v2 schemas defining:
1. Encounter summaries and chronological timeline events.
2. Biomarker records and numerical trajectory models (without clinical overinterpretation).
3. Active, resolved, and recurrent problem records.
4. Comprehensive LongitudinalPatientContextDTO.

100% DETERMINISTIC. ZERO DIAGNOSTIC INFERENCE. 100% Pydantic v2.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


BiomarkerTrajectoryType = Literal[
    "increasing",
    "decreasing",
    "stable",
    "fluctuating",
    "insufficient_data",
]

ProblemStatus = Literal[
    "active",
    "resolved",
    "recurrent",
    "unresolved",
    "unknown",
]

TimelineEventType = Literal[
    "encounter",
    "document",
    "investigation",
    "conversation",
    "patient_profile",
    "clinical_note",
]


class EncounterSummary(BaseModel):
    """Normalized historical encounter summary."""
    encounter_id: str = Field(..., description="Unique encounter identifier")
    timestamp: Optional[str] = Field(None, description="ISO 8601 or normalized date string of the encounter")
    date_certainty: str = Field(default="exact", description="'exact', 'approximate', or 'unspecified'")
    chief_complaint: Optional[str] = Field(None, description="Primary reported complaint")
    severity: Optional[str] = Field(None, description="Reported severity (mild, moderate, severe, etc.)")
    duration: Optional[str] = Field(None, description="Reported duration of symptoms")
    associated_symptoms: list[str] = Field(default_factory=list, description="Associated symptoms reported")
    risk_level: Optional[str] = Field(None, description="Assessed risk level if explicitly present (LOW, MODERATE, HIGH, URGENT)")
    risk_score: Optional[float] = Field(None, description="Calculated risk score (0-100) if explicitly recorded")
    red_flags: list[str] = Field(default_factory=list, description="Red flags detected in this encounter")
    immediate_attention_required: bool = Field(default=False, description="Whether immediate emergency attention was required")
    trajectory: Optional[str] = Field(None, description="Trajectory classification recorded in follow-up")
    resolved_symptoms: list[str] = Field(default_factory=list, description="Symptoms explicitly confirmed as resolved")
    source: str = Field(default="historical_encounter", description="Provenance source tag")
    completeness_score: Optional[float] = Field(None, description="Data completeness percentage")


class TimelineEvent(BaseModel):
    """Chronological event entry in the patient's longitudinal timeline."""
    event_id: str = Field(..., description="Unique identifier for the timeline event")
    event_type: TimelineEventType = Field(..., description="Type of event ('encounter', 'document', 'investigation', etc.)")
    date: Optional[str] = Field(None, description="ISO 8601 date/time or normalized date string")
    date_certainty: str = Field(default="exact", description="'exact', 'approximate', or 'unspecified'")
    source_id: Optional[str] = Field(None, description="ID of the originating encounter, document, or investigation")
    source_type: str = Field(default="encounter", description="Source category")
    title: str = Field(..., description="Short factual title of the timeline event")
    description: str = Field(..., description="Factual narrative summary of the event")
    structured_data: dict[str, Any] = Field(default_factory=dict, description="Structured attributes associated with event")
    provenance: str = Field(..., description="Traceability provenance string")


class BiomarkerRecord(BaseModel):
    """Single historical or current biomarker observation."""
    test_name: str = Field(..., description="Raw name of the laboratory test / biomarker")
    normalized_name: str = Field(..., description="Normalized lowercase test identifier")
    value: float = Field(..., description="Numeric value of the observation")
    unit: str = Field(..., description="Measurement unit (e.g. 'mg/dL', 'g/dL', '%', '/mcL')")
    reference_range: Optional[str] = Field(None, description="Explicit reference range provided by source")
    is_abnormal: Optional[bool] = Field(None, description="Flag indicating if observation is abnormal based on explicit source status")
    status: Optional[str] = Field(None, description="Explicit status tag: 'normal', 'high', 'low', 'critical_high', 'critical_low'")
    observation_date: Optional[str] = Field(None, description="Date when the lab test was performed")
    source_document_id: Optional[str] = Field(None, description="Source document or investigation identifier")
    provenance: str = Field(default="structured_biomarker", description="Provenance tag")


class BiomarkerTrajectory(BaseModel):
    """
    Observed numerical trajectory for a specific laboratory biomarker over time.
    
    SAFETY INVARIANT:
    Separates NUMERIC DIRECTION from CLINICAL INTERPRETATION.
    Does NOT equate numeric increase with worsening or numeric decrease with improving.
    """
    test_name: str = Field(..., description="Display name of the biomarker test")
    normalized_name: str = Field(..., description="Normalized key for the biomarker test")
    observations: list[BiomarkerRecord] = Field(default_factory=list, description="Chronologically ordered observations")
    observation_count: int = Field(default=0, description="Total number of observations recorded")
    earliest_observation: Optional[BiomarkerRecord] = Field(None, description="First chronologically recorded observation")
    latest_observation: Optional[BiomarkerRecord] = Field(None, description="Most recent chronologically recorded observation")
    absolute_delta: Optional[float] = Field(None, description="Absolute numeric delta (latest - earliest)")
    percentage_change: Optional[float] = Field(None, description="Percentage change ((latest - earliest) / earliest * 100)")
    direction: Optional[str] = Field(None, description="'upward', 'downward', 'unchanged', 'fluctuating', or 'insufficient_data'")
    trajectory: BiomarkerTrajectoryType = Field(default="insufficient_data", description="Observed trajectory classification")
    unit: Optional[str] = Field(None, description="Consistent unit of measurement")
    unit_mismatch: bool = Field(default=False, description="True if observations have incompatible units")
    provenance_sources: list[str] = Field(default_factory=list, description="List of source document IDs")
    interpretation_note: str = Field(
        default="Numeric observation only; clinical significance requires licensed medical evaluation.",
        description="Mandatory non-diagnostic disclaimer"
    )


class ProblemRecord(BaseModel):
    """
    Structured active, resolved, or recurrent clinical problem record.
    
    SAFETY INVARIANT:
    'Missing later' != 'Resolved'. Problems move to resolved ONLY with explicit evidence.
    """
    problem_id: str = Field(..., description="Unique problem identifier")
    label: str = Field(..., description="Original clinical symptom or condition label")
    normalized_label: str = Field(..., description="Normalized lowercase clinical problem tag")
    status: ProblemStatus = Field(default="active", description="Problem status ('active', 'resolved', 'recurrent', 'unresolved')")
    first_observed_date: Optional[str] = Field(None, description="Earliest date problem was documented")
    last_observed_date: Optional[str] = Field(None, description="Latest date problem was documented")
    encounter_ids: list[str] = Field(default_factory=list, description="All encounter IDs where this problem appeared")
    episode_count: int = Field(default=1, description="Number of distinct episodes/encounters recorded")
    is_recurrent: bool = Field(default=False, description="True if problem re-appeared after a symptom-free interval or non-consecutive visits")
    resolution_evidence: Optional[str] = Field(None, description="Explicit clinical text or encounter confirming resolution")
    resolution_encounter_id: Optional[str] = Field(None, description="Encounter ID where resolution was documented")
    associated_symptoms: list[str] = Field(default_factory=list, description="Associated symptoms noted with this problem")
    provenance: str = Field(default="problem_registry", description="Provenance tag")


class LongitudinalPatientContextDTO(BaseModel):
    """
    Unified, explainable longitudinal patient intelligence bundle.
    
    Synthesizes multi-encounter clinical history, chronological timeline,
    biomarker time-series trajectories, and active/recurrent problem registries.
    """
    patient_id: str = Field(default="ANONYMOUS", description="Unique patient identifier or explicit anonymous tag")
    total_encounters: int = Field(default=0, description="Total historical + current encounters in timeline")
    timeline: list[TimelineEvent] = Field(default_factory=list, description="Chronologically sorted unified clinical timeline")
    active_problems: list[ProblemRecord] = Field(default_factory=list, description="Currently active clinical issues")
    resolved_problems: list[ProblemRecord] = Field(default_factory=list, description="Explicitly resolved clinical issues")
    recurrent_complaints: list[ProblemRecord] = Field(default_factory=list, description="Complaints identified as recurrent episodes")
    unresolved_issues: list[ProblemRecord] = Field(default_factory=list, description="Historical issues unmentioned in current encounter (Missing != Resolved)")
    chronic_baseline_conditions: list[str] = Field(default_factory=list, description="Known baseline chronic medical conditions")
    known_allergies: list[str] = Field(default_factory=list, description="Documented patient allergies")
    chronic_medications: list[str] = Field(default_factory=list, description="Documented chronic medications")
    biomarker_trajectories: list[BiomarkerTrajectory] = Field(default_factory=list, description="Time-series biomarker trajectories")

    provenance_summary: list[str] = Field(default_factory=list, description="Traceability audit log of all ingested sources")
    data_quality_notes: list[str] = Field(default_factory=list, description="Notes on missing dates, unit mismatches, or gaps")
