from typing import TypedDict, Optional, Any


class VaidyaArcState(TypedDict, total=False):

    # Patient identification
    patient_id: str
    session_id: str

    # Patient profile
    patient_profile: dict[str, Any]
    previous_history: list[dict[str, Any]]
    previous_encounters: list[dict[str, Any]]
    previous_conversations: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    ocr_documents: list[dict[str, Any]]
    investigations: list[dict[str, Any]]


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
    questions_asked: list[str]

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

    # Phase 2B: Risk Convergence Engine
    risk_level: Optional[str]
    risk_score: Optional[int]
    risk_signal_summary: list[str]
    risk_contributing_factors: list[str]
    risk_evidence: list[str]
    risk_reasoning: Optional[str]
    risk_override_reason: Optional[str]
    recommended_next_action: Optional[str]
    risk_rule_hits: list[dict[str, Any]]
    convergence_status: Optional[str]
    risk_context_flags: list[str]
    risk_assessment_version: Optional[str]

    # Phase 3: Clinical Case Representation
    clinical_case: Optional[dict[str, Any]]
    clinical_case_output: Optional[dict[str, Any]]
    case_generation_status: Optional[str]
    case_validation_errors: list[str]

    # Phase 4: Care Navigation & Facility Matching
    patient_location: Optional[dict[str, Any]]
    care_navigation_status: Optional[str]
    matched_facilities: list[dict[str, Any]]
    navigation_explanation: Optional[str]
    navigation_source: Optional[str]
    care_navigation_output: Optional[dict[str, Any]]

    # Phase 5: Follow-up & Patient Monitoring Intelligence
    previous_case_state: Optional[dict[str, Any]]
    follow_up_output: Optional[dict[str, Any]]
    monitoring_status: Optional[str]
    patient_trajectory: Optional[str]
    risk_trend: Optional[str]
    new_signals: list[str]
    resolved_signals: list[str]
    next_monitoring_action: Optional[str]
    monitoring_explanation: Optional[str]

    # Phase 7: Ayurveda <-> Modern Medicine Representation
    ayurveda_modern_output: Optional[dict[str, Any]]
    modern_representation: Optional[dict[str, Any]]
    ayurvedic_representation: Optional[dict[str, Any]]
    correspondence_summary: Optional[dict[str, Any]]
    representation_status: Optional[str]
    ayurveda_safety_notes: list[str]

    # Phase 9: Longitudinal Patient Intelligence
    longitudinal_context: Optional[dict[str, Any]]

    # Phase 10: Advanced Risk Convergence
    advanced_risk_output: Optional[dict[str, Any]]

    # Future outputs
    recommendations: list[str]
    physician_report: Optional[str]

