"""
Phase 12: Dashavidha Atura Pariksha Schema.

Defines the Pydantic v2 data models for the classical ten-fold patient examination
described in Charaka Samhita, Vimana Sthana 8/94:
1. Prakriti (Natural Constitution)
2. Vikriti (Pathological Morbidity / Alteration)
3. Sara (Tissue Excellence / Dhatu Integrity)
4. Samhanana (Compactness / Musculoskeletal Symmetry)
5. Pramana (Anthropometric Measurements)
6. Satmya (Habituation / Adaptability)
7. Sattva (Psychic Endurance / Mental Strength)
8. Ahara Shakti (Ingestion and Digestive Power)
9. Vyayama Shakti (Physical Work Capacity)
10. Vaya (Chronological Life Stage / Age)

ZERO-LLM. 100% DETERMINISTIC.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class EpistemicStatus(str, Enum):
    """Strict 3-tier epistemic status model for Phase 12."""
    EXPLICITLY_REPORTED = "explicitly_reported"
    STRUCTURALLY_EXTRACTED = "structurally_extracted"
    NOT_ASSESSED = "not_assessed"


class DashavidhaParameterRecord(BaseModel):
    """
    Standardized container for each of the 10 Charaka Dashavidha Atura Pariksha parameters.
    """
    parameter_id: str = Field(..., description="Unique parameter identifier (e.g. 'param_01_prakriti')")
    sanskrit_name: str = Field(..., description="Classical Sanskrit parameter name")
    framework_reference: str = Field(
        default="Charaka Samhita, Vimana Sthana 8/94",
        description="Textual framework reference"
    )
    parameter_reference: Optional[str] = Field(
        default=None,
        description="Verified parameter-specific textual reference"
    )
    status: EpistemicStatus = Field(
        default=EpistemicStatus.NOT_ASSESSED,
        description="Epistemic status of formal assessment"
    )
    reported_observations: list[str] = Field(
        default_factory=list,
        description="Patient-reported observations relevant to this parameter"
    )
    structured_findings: Optional[dict[str, Any]] = Field(
        default=None,
        description="Modern structured facts (e.g. vitals, chronological age)"
    )
    prior_formal_assessment: Optional[dict[str, Any]] = Field(
        default=None,
        description="Explicitly reported previous qualified Ayurvedic assessment if provided by patient"
    )
    clinical_limitations: list[str] = Field(
        default_factory=list,
        description="Explicit clinical boundaries explaining why formal assessment requires physician examination"
    )
    assessment_note: str = Field(
        default="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        description="Clinical context note"
    )
    provenance_sources: list[str] = Field(
        default_factory=list,
        description="Direct provenance state keys"
    )


class DashavidhaAturaParikshaProfileDTO(BaseModel):
    """
    The 10-parameter Dashavidha Atura Pariksha profile (Charaka Samhita Vimana Sthana 8/94).
    """
    prakriti: DashavidhaParameterRecord = Field(..., description="1. Prakriti (Natural Constitution)")
    vikriti: DashavidhaParameterRecord = Field(..., description="2. Vikriti (Pathological Morbidity / Alteration)")
    sara: DashavidhaParameterRecord = Field(..., description="3. Sara (Tissue Excellence / Dhatu Integrity)")
    samhanana: DashavidhaParameterRecord = Field(..., description="4. Samhanana (Compactness / Symmetry)")
    pramana: DashavidhaParameterRecord = Field(..., description="5. Pramana (Anthropometric Proportions)")
    satmya: DashavidhaParameterRecord = Field(..., description="6. Satmya (Habituation / Adaptability)")
    sattva: DashavidhaParameterRecord = Field(..., description="7. Sattva (Psychic Endurance / Mental Strength)")
    ahara_shakti: DashavidhaParameterRecord = Field(..., description="8. Ahara Shakti (Ingestion & Digestive Power)")
    vyayama_shakti: DashavidhaParameterRecord = Field(..., description="9. Vyayama Shakti (Physical Work Capacity)")
    vaya: DashavidhaParameterRecord = Field(..., description="10. Vaya (Chronological Life Stage / Age)")

    parameters_with_observations_count: int = Field(default=0, description="Count of parameters with observations or modern data")
    parameters_formally_assessed_count: int = Field(default=0, description="Count of parameters formally assessed via prior qualified report or exact chronological mapping")
    parameters_not_assessed_count: int = Field(default=10, description="Count of parameters remaining not_assessed")
    summary_narrative: str = Field(..., description="Descriptive non-diagnostic summary narrative")
    safety_context: dict[str, Any] = Field(default_factory=dict, description="Preserved safety findings and risk state")
    disclaimer: str = Field(
        default=(
            "Dashavidha Atura Pariksha representation is a structured descriptive synthesis of patient-reported "
            "observations and chronological facts based on Charaka Samhita Vimana Sthana 8/94. It does NOT constitute "
            "an Ayurvedic diagnosis, Dosha determination, or treatment plan. Complete clinical assessment requires an "
            "in-person qualified Ayurvedic physician."
        ),
        description="Mandatory Ayurvedic descriptive disclaimer"
    )
    version: str = Field(default="phase12_v1", description="Schema version")
    provenance_notes: list[str] = Field(default_factory=list, description="System-wide audit provenance notes")


class Phase12DashavidhaOutputDTO(BaseModel):
    """
    Unified Phase 12 output container.
    """
    dashavidha_atura_pariksha: DashavidhaAturaParikshaProfileDTO = Field(
        ..., description="10-fold Dashavidha Atura Pariksha profile"
    )
    safety_context: dict[str, Any] = Field(default_factory=dict, description="Preserved safety context")
    provenance_notes: list[str] = Field(default_factory=list, description="Audit provenance log")
