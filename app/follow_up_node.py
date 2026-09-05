"""
Phase 5: Follow-up & Patient Monitoring LangGraph Node.

Consumes upstream intake (Phase 1B), safety (Phase 2A), risk convergence (Phase 2B),
clinical case representation (Phase 3), and care navigation (Phase 4) outputs.
Executes deterministic longitudinal comparison against prior encounter state.

ZERO-LLM. 100% DETERMINISTIC.
"""

from typing import Any, Optional

from app.state import VaidyaArcState
from app.follow_up_schema import FollowUpMonitoringOutput
from app.follow_up_comparison import compare_clinical_states
from app.longitudinal_timeline import synthesize_longitudinal_context


def _extract_previous_encounter_state(state: VaidyaArcState) -> Optional[dict[str, Any]]:
    """
    Extract structured prior encounter state if available.
    Supports:
    1. Direct injection via state['previous_case_state']
    2. Last record in state['previous_history']
    """
    direct_prev = state.get("previous_case_state")
    if direct_prev and isinstance(direct_prev, dict):
        return direct_prev

    history = state.get("previous_history") or []
    if history and isinstance(history, list) and len(history) > 0:
        last_entry = history[-1]
        if isinstance(last_entry, dict):
            return last_entry

    return None


def patient_monitoring(state: VaidyaArcState) -> dict[str, Any]:
    """
    Phase 5 Patient Monitoring & Follow-up Node (Enhanced with Phase 9 Longitudinal Context).
    
    Transforms previous encounter state and current encounter state into
    an explainable, structured trajectory and risk trend analysis.
    """
    try:
        previous_state = _extract_previous_encounter_state(state)
        current_message = state.get("current_message", "")

        # Execute deterministic pairwise comparison engine (Phase 5 baseline)
        monitoring_output: FollowUpMonitoringOutput = compare_clinical_states(
            previous_state=previous_state,
            current_state=state,
            current_message=current_message,
        )

        # Synthesize multi-encounter longitudinal patient context (Phase 9)
        longitudinal_dto = synthesize_longitudinal_context(state)

        return {
            "monitoring_status": monitoring_output.monitoring_status,
            "patient_trajectory": monitoring_output.trajectory.trajectory,
            "risk_trend": monitoring_output.risk_comparison.risk_trend,
            "new_signals": monitoring_output.symptom_changes.new_symptoms,
            "resolved_signals": monitoring_output.symptom_changes.resolved_symptoms,
            "next_monitoring_action": monitoring_output.next_monitoring_action,
            "monitoring_explanation": monitoring_output.monitoring_explanation,
            "follow_up_output": monitoring_output.model_dump(),
            "longitudinal_context": longitudinal_dto.model_dump(),
        }

    except Exception as e:
        error_msg = f"Patient monitoring failed: {str(e)}"
        return {
            "monitoring_status": "insufficient_information",
            "patient_trajectory": "insufficient_information",
            "risk_trend": "unknown",
            "new_signals": [],
            "resolved_signals": [],
            "next_monitoring_action": "Clinical assessment recommended to gather structured follow-up information.",
            "monitoring_explanation": error_msg,
            "follow_up_output": None,
            "longitudinal_context": None,
        }

