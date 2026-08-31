from typing import TypedDict, Optional, Any


class VaidyaArcState(TypedDict, total=False):

    # Patient identification
    patient_id: str
    session_id: str

    # Patient profile
    patient_profile: dict[str, Any]
    previous_history: list[dict[str, Any]]

    # Conversation
    current_message: str
    language: str
    conversation_history: list[dict[str, str]]

    # Temporary extraction buffer from the current message
    extracted_information: dict[str, Any]

    # Structured clinical information
    chief_complaint: Optional[str]
    duration: Optional[str]
    severity: Optional[str]
    nature_of_pain: Optional[str]
    location: Optional[str]
    associated_symptoms: list[str]

    # Adaptive questioning
    missing_information: list[str]
    next_question: Optional[str]
    information_complete: bool

    # Patient-facing response
    conversation_message: Optional[str]

    # Phase 2A safety screening
    red_flag_status: Optional[str]
    red_flags: list[str]
    red_flag_evidence: list[str]
    immediate_attention_required: bool
    red_flag_rule_hits: list[dict[str, Any]]

    # Future risk components
    risk_category: Optional[str]
    risk_factors: list[str]
    risk_convergence_factors: list[str]

    # Future outputs
    recommendations: list[str]
    physician_report: Optional[str]