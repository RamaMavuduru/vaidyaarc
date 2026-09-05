"""
Phase 8A: Central VaidyaArc Intelligence Orchestrator.

Coordinates normalized input/output contracts, turn execution, early Phase 2A
safety evaluation, LangGraph workflow execution, and clinical output synthesis.

SAFETY INVARIANTS:
1. Reuses authoritative Phase 2A safety engine (app/red_flag_rules.py) - NO duplicate rules.
2. Emergency red-flag symptoms trigger immediate safe return WITHOUT requiring LLM generation.
3. Preserves Phase 2B risk scoring, Phase 3 case representation, Phase 4 care navigation,
   Phase 5 longitudinal monitoring, and Phase 7 Ayurveda representation immutably.
"""

from typing import Any, Optional

from app.state import VaidyaArcState
from app.workflow import build_vaidyaarc_graph
from app.red_flag_rules import evaluate_red_flags as evaluate_red_flag_rules
from app.nodes import (
    risk_convergence,
)
from app.clinical_case_node import clinical_case_representation
from app.care_navigation_node import care_navigation
from app.follow_up_node import patient_monitoring
from app.ayurveda_modern_node import ayurveda_modern_representation
from app.ayurveda_recommendation import evaluate_ayurveda_recommendations
from app.longitudinal_timeline import synthesize_longitudinal_context
from app.advanced_risk_engine import evaluate_advanced_risk
from app.clinical_summary_engine import generate_clinical_summary_bundle

from app.normalized_schemas import (

    NormalizedClinicalInputDTO,
    TurnResponseDTO,
    StructuredClinicalOutputDTO,
)


EMERGENCY_ALERT_MESSAGE = (
    "EMERGENCY WARNING: Your reported symptoms indicate a potential medical emergency "
    "requiring immediate clinical attention. Please proceed immediately to the nearest "
    "emergency department or contact emergency medical services."
)


# Compile the LangGraph workflow graph once
_WORKFLOW_GRAPH = build_vaidyaarc_graph()


def _build_initial_state_from_input(dto: NormalizedClinicalInputDTO) -> VaidyaArcState:
    """Transforms NormalizedClinicalInputDTO into VaidyaArcState."""
    english_msg = dto.message.english_text or dto.message.original_text
    profile_dict = dto.patient_profile.model_dump() if dto.patient_profile else {}
    location_dict = dto.patient_location.model_dump() if dto.patient_location else None

    # Base fresh state
    state: VaidyaArcState = {
        "patient_id": dto.patient_id or "ANONYMOUS",
        "session_id": dto.episode_id or "EP_DEFAULT",
        "episode_id": dto.episode_id,
        "language": dto.message.original_language or "en",
        "current_message": english_msg,
        "original_transcript": dto.message.original_text,
        "original_language": dto.message.original_language,
        "normalized_english": dto.message.english_text,
        "translation_provenance": dto.message.provenance,
        "patient_profile": profile_dict,
        "patient_location": location_dict,
        "previous_history": dto.previous_encounters,
        "previous_encounters": dto.previous_encounters,
        "previous_conversations": dto.previous_conversations,
        "documents": [d.model_dump() for d in dto.documents],
        "ocr_documents": [d.model_dump() for d in dto.documents],
        "investigations": dto.investigations,
        "conversation_history": [],

        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],
        "conversation_message": None,
        "next_question": None,
    }

    # If previous turn state snapshot is provided, merge it
    if dto.state_snapshot and isinstance(dto.state_snapshot, dict):
        state.update(dto.state_snapshot)
        # Ensure current message and turn context are updated
        state["current_message"] = english_msg
        state["original_transcript"] = dto.message.original_text
        state["original_language"] = dto.message.original_language
        state["normalized_english"] = dto.message.english_text
        state["translation_provenance"] = dto.message.provenance

    return state


def evaluate_early_safety_check(state: VaidyaArcState) -> dict[str, Any]:
    """
    Executes authoritative Phase 2A red-flag evaluation on incoming state.
    Reuses app/red_flag_rules.py without duplicating any rules.
    """
    eval_state = dict(state)
    eval_state["information_complete"] = True
    return evaluate_red_flag_rules(eval_state)


def synthesize_clinical_output(state: VaidyaArcState) -> StructuredClinicalOutputDTO:
    """
    Assembles unified StructuredClinicalOutputDTO from completed VaidyaArcState.
    """
    case_id = state.get("clinical_case", {}).get("case_id") or f"{state.get('patient_id')}_{state.get('session_id')}"
    
    ayurveda_rec_output = evaluate_ayurveda_recommendations(state)
    ayurveda_rec_dict = ayurveda_rec_output.model_dump()

    long_ctx = state.get("longitudinal_context")
    if long_ctx is None:
        long_ctx_dto = synthesize_longitudinal_context(state)
        long_ctx = long_ctx_dto.model_dump()

    adv_risk_output = evaluate_advanced_risk(state)
    adv_risk_dict = adv_risk_output.model_dump()

    # Phase 11: Clinical Summary & Consultation Questions
    summary_bundle = generate_clinical_summary_bundle(state)
    clin_sum_dict = summary_bundle.clinical_summary.model_dump()
    cons_q_dict = summary_bundle.consultation_questions.model_dump()

    provenance_notes = [
        "Phase 2A deterministic safety rules (app/red_flag_rules.py)",
        "Phase 2B deterministic risk convergence scoring (phase2b_v1)",
        "Phase 3 clinical case representation schema (phase3_v1)",
        "Phase 4 care navigation facility matching engine",
        "Phase 5 longitudinal comparison engine (Missing != Resolved)",
        "Phase 7 Ayurveda descriptive taxonomy (AYURVEDA_KB_V1)",
        "Phase 8B controlled Ayurveda knowledge retrieval and safety gate",
        "Phase 9 deterministic longitudinal patient context & biomarker engine",
        "Phase 10 deterministic advanced risk convergence (app/advanced_risk_engine.py)",
        "Phase 11 deterministic clinical summary & consultation questions engine",
    ]

    intake_summary = {
        "chief_complaint": state.get("chief_complaint"),
        "nature_of_pain": state.get("nature_of_pain"),
        "location": state.get("location"),
        "duration": state.get("duration"),
        "severity": state.get("severity"),
        "associated_symptoms": state.get("associated_symptoms") or [],
    }

    safety_findings = {
        "red_flag_status": state.get("red_flag_status"),
        "red_flags": state.get("red_flags") or [],
        "red_flag_evidence": state.get("red_flag_evidence") or [],
        "immediate_attention_required": state.get("immediate_attention_required", False),
        "red_flag_rule_hits": state.get("red_flag_rule_hits") or [],
    }

    risk_assessment = {
        "risk_level": state.get("risk_level"),
        "risk_score": state.get("risk_score"),
        "risk_signals": state.get("risk_signal_summary") or [],
        "risk_contributing_factors": state.get("risk_contributing_factors") or [],
        "risk_reasoning": state.get("risk_reasoning"),
        "recommended_next_action": state.get("recommended_next_action"),
    }

    return StructuredClinicalOutputDTO(
        case_id=case_id,
        patient_id=state.get("patient_id") or "ANONYMOUS",
        intake_summary=intake_summary,
        safety_findings=safety_findings,
        risk_assessment=risk_assessment,
        clinical_case=state.get("clinical_case") or {},
        care_navigation=state.get("care_navigation_output"),
        follow_up_monitoring=state.get("follow_up_output"),
        ayurveda_modern_representation=state.get("ayurveda_modern_output"),
        ayurveda_recommendation=ayurveda_rec_dict,
        longitudinal_context=long_ctx,
        advanced_risk_assessment=adv_risk_dict,
        clinical_summary=clin_sum_dict,
        consultation_questions=cons_q_dict,
        provenance_notes=provenance_notes,
    )



def process_turn(normalized_input: NormalizedClinicalInputDTO) -> TurnResponseDTO:
    """
    Main entry point for processing a clinical turn.
    
    1. Normalizes input into VaidyaArcState.
    2. Performs early Phase 2A safety evaluation using existing red_flag_rules.py.
    3. If emergency red flag detected -> Immediately executes deterministic downstream
       nodes and returns emergency response WITHOUT requiring LLM generation.
    4. Otherwise -> Invokes LangGraph workflow.
    5. Formulates and returns validated TurnResponseDTO.
    """
    state = _build_initial_state_from_input(normalized_input)

    # 1. Early Authoritative Phase 2A Red Flag Safety Check
    early_safety = evaluate_early_safety_check(state)

    if early_safety.get("immediate_attention_required"):
        # Emergency Red Flag Triggered - Short-circuit pipeline immediately
        state["red_flag_status"] = early_safety["red_flag_status"]
        state["red_flags"] = early_safety["red_flags"]
        state["red_flag_evidence"] = early_safety["red_flag_evidence"]
        state["immediate_attention_required"] = True
        state["red_flag_rule_hits"] = early_safety["red_flag_rule_hits"]
        state["information_complete"] = True
        state["missing_information"] = []
        state["conversation_message"] = EMERGENCY_ALERT_MESSAGE

        # If chief complaint not yet extracted, seed it from message for case generation
        if not state.get("chief_complaint"):
            state["chief_complaint"] = state.get("current_message")

        # Execute downstream deterministic pipelines (zero-LLM)
        risk_res = risk_convergence(state)
        state.update(risk_res)

        case_res = clinical_case_representation(state)
        state.update(case_res)

        nav_res = care_navigation(state)
        state.update(nav_res)

        mon_res = patient_monitoring(state)
        state.update(mon_res)

        ayur_res = ayurveda_modern_representation(state)
        state.update(ayur_res)

        clinical_output = synthesize_clinical_output(state)

        return TurnResponseDTO(
            session_id=state["session_id"],
            patient_id=state["patient_id"],
            status="emergency",
            conversation_message=EMERGENCY_ALERT_MESSAGE,
            information_complete=True,
            missing_information=[],
            immediate_attention_required=True,
            red_flag_status=state["red_flag_status"],
            red_flags=state["red_flags"],
            updated_state=state,
            clinical_output=clinical_output.model_dump(),
        )

    # 2. Standard LangGraph Turn Execution
    result = _WORKFLOW_GRAPH.invoke(state)
    state.update(result)

    is_complete = bool(state.get("information_complete", False))
    is_emergency = bool(state.get("immediate_attention_required", False))

    if is_emergency:
        status = "emergency"
    elif is_complete:
        status = "complete"
    else:
        status = "in_progress"

    clinical_output_dict = None
    if is_complete or is_emergency:
        clinical_output_dict = synthesize_clinical_output(state).model_dump()

    return TurnResponseDTO(
        session_id=state["session_id"],
        patient_id=state["patient_id"],
        status=status,
        conversation_message=state.get("conversation_message"),
        information_complete=is_complete,
        missing_information=state.get("missing_information") or [],
        immediate_attention_required=is_emergency,
        red_flag_status=state.get("red_flag_status") or "no_obvious_red_flags",
        red_flags=state.get("red_flags") or [],
        updated_state=state,
        clinical_output=clinical_output_dict,
    )

