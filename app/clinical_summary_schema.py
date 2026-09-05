"""
Phase 11: Clinical Summary & Consultation Questions Schemas.

Pydantic v2 models defining:
1. ClinicalSummarySection: Granular section descriptor with content, status, and provenance.
2. ClinicalSummaryDTO: Structured physician-facing clinical summary covering all 12 key clinical domains.
3. ConsultationQuestionDTO: Patient-facing consultation question with clinical rationale and priority.
4. ConsultationQuestionsDTO: Comprehensive question bundle for patient-physician discussion.
5. Phase11ClinicalSummaryOutputDTO: Combined output bundle.

100% DETERMINISTIC. ZERO DIAGNOSIS. ZERO PRESCRIPTION. ZERO INFERRED NEGATIVES.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


SectionStatus = Literal[
    "reported",
    "not_reported",
    "insufficient_information",
    "conflicting",
]

DataCompletenessLevel = Literal[
    "complete",
    "partial",
    "minimal",
    "insufficient",
]

QuestionPriority = Literal[
    "high",
    "medium",
    "standard",
]


class ClinicalSummarySection(BaseModel):
    """
    Granular, explainable clinical summary section.
    """
    section_name: str = Field(..., description="Standardized clinical section name")
    content: str = Field(..., description="Concise, factual, non-diagnostic text summary")
    status: SectionStatus = Field(..., description="Reporting status of this section")
    structured_data: Optional[Any] = Field(default=None, description="Underlying structured payload if applicable")
    provenance: list[str] = Field(default_factory=list, description="Source provenance tags or references")


class ClinicalSummaryDTO(BaseModel):
    """
    Physician-ready structured clinical summary synthesizing all available clinical intelligence.
    """
    chief_complaint: ClinicalSummarySection = Field(..., description="Section 1: Chief Complaint")
    history_of_present_illness: ClinicalSummarySection = Field(..., description="Section 2: History of Present Illness (HPI)")
    past_medical_history: ClinicalSummarySection = Field(..., description="Section 3: Past Medical History (PMH)")
    past_surgical_history: ClinicalSummarySection = Field(..., description="Section 4: Past Surgical History (PSH)")
    medication_history: ClinicalSummarySection = Field(..., description="Section 5: Drug / Medication History")
    allergy_history: ClinicalSummarySection = Field(..., description="Section 6: Allergy History")
    family_history: ClinicalSummarySection = Field(..., description="Section 7: Family History")
    personal_social_history: ClinicalSummarySection = Field(..., description="Section 8: Personal / Social History")
    review_of_systems: ClinicalSummarySection = Field(..., description="Section 9: Review of Systems (ROS)")
    prior_investigations: ClinicalSummarySection = Field(..., description="Section 10: Prior Investigations & Diagnostics")
    longitudinal_context: ClinicalSummarySection = Field(..., description="Section 11: Longitudinal & Follow-up Context")
    safety_and_risk_summary: ClinicalSummarySection = Field(..., description="Section 12: Current Safety & Risk Summary")
    
    data_completeness: DataCompletenessLevel = Field(default="complete", description="Overall intake data completeness level")
    conflicts_identified: list[str] = Field(default_factory=list, description="Any documented conflicting patient statements")
    summary_narrative: str = Field(..., description="Concise multi-line clinical case narrative")
    disclaimer: str = Field(
        default="Clinical summary is a descriptive synthesis of reported facts and does not constitute a medical diagnosis or treatment plan.",
        description="Mandatory non-diagnostic disclaimer"
    )
    version: str = Field(default="phase11_v1", description="Schema version")
    provenance_notes: list[str] = Field(default_factory=list, description="Summary generation provenance notes")


class ConsultationQuestionDTO(BaseModel):
    """
    Patient-facing consultation question for doctor discussion.
    """
    question_id: str = Field(..., description="Unique deterministic question identifier")
    question: str = Field(..., description="Contextual question phrasing for the doctor")
    category: str = Field(..., description="Question focus category (e.g., 'symptom_cause', 'information_gap')")
    rationale: str = Field(..., description="Clinical reason why this question is valuable")
    priority: QuestionPriority = Field(default="standard", description="Discussion priority level")
    source_evidence: list[str] = Field(default_factory=list, description="Factual evidence supporting this question")
    provenance: str = Field(default="deterministic_engine", description="Origin tag")


class ConsultationQuestionsDTO(BaseModel):
    """
    Bundle of contextual questions for patient-physician discussion.
    """
    questions: list[ConsultationQuestionDTO] = Field(default_factory=list, description="Ordered list of consultation questions")
    generated_from: list[str] = Field(default_factory=list, description="Categories of evidence and gaps utilized")
    safety_context: str = Field(..., description="Current safety status context")
    disclaimer: str = Field(
        default="Consultation questions are suggested patient communication prompts for discussion with a qualified healthcare professional and do not constitute medical advice or instructions.",
        description="Mandatory patient communication disclaimer"
    )
    version: str = Field(default="phase11_v1", description="Schema version")


class Phase11ClinicalSummaryOutputDTO(BaseModel):
    """
    Unified Phase 11 output bundle.
    """
    clinical_summary: ClinicalSummaryDTO = Field(..., description="Physician-facing clinical summary")
    consultation_questions: ConsultationQuestionsDTO = Field(..., description="Patient-facing consultation questions")
    provenance_notes: list[str] = Field(default_factory=list, description="Audit provenance log")

