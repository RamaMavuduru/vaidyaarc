"""
VaidyaArc Brain - Clinical Workflow Definition.

Defines the LangGraph execution graph connecting clinical intelligence nodes.
Supports both the legacy intake pipeline and the new adaptive clinical history-taking pipeline
via the VAIDYAARC_ENABLE_ADAPTIVE_INTAKE configuration flag.
"""

from __future__ import annotations
import os
from typing import Optional
from langgraph.graph import StateGraph, START, END

from app.state import VaidyaArcState
from app.nodes import (
    intake_brain,
    merge_intake_information,
    validate_patient_state,
    determine_missing_information,
    select_next_question,
    ask_next_question,
    evaluate_red_flags,
    risk_convergence,
)
from app.clinical_case_node import clinical_case_representation
from app.care_navigation_node import care_navigation
from app.follow_up_node import patient_monitoring
from app.ayurveda_modern_node import ayurveda_modern_representation

from app.agents.adaptive_intake_nodes import (
    tier1_safety_precheck_node,
    clinical_delta_extractor_node,
    state_consolidation_ledger_node,
    deterministic_governance_node,
    adaptive_question_generator_node,
    safety_scope_sanitizer_node,
    casesheet_synthesizer_node,
)


def route_after_missing_check(state: VaidyaArcState):
    missing = state.get("missing_information") or []
    if state.get("information_complete") and not missing:
        return "complete"
    return "need_more_info"


def route_adaptive_governance(state: VaidyaArcState):
    if state.get("tier1_emergency_triggered"):
        return "emergency"
    if state.get("governance_verdict") == "complete" or state.get("information_complete"):
        return "complete"
    return "need_more_info"


def build_legacy_graph():
    """Builds the legacy slot-filling intake workflow graph."""
    builder = StateGraph(VaidyaArcState)

    builder.add_node("intake_brain", intake_brain)
    builder.add_node("merge_intake_information", merge_intake_information)
    builder.add_node("validate_patient_state", validate_patient_state)
    builder.add_node("determine_missing_information", determine_missing_information)
    builder.add_node("select_next_question", select_next_question)
    builder.add_node("ask_next_question", ask_next_question)
    builder.add_node("evaluate_red_flags", evaluate_red_flags)
    builder.add_node("risk_convergence", risk_convergence)
    builder.add_node("clinical_case_representation", clinical_case_representation)
    builder.add_node("care_navigation", care_navigation)
    builder.add_node("patient_monitoring", patient_monitoring)
    builder.add_node("ayurveda_modern_representation", ayurveda_modern_representation)

    builder.add_edge(START, "intake_brain")
    builder.add_edge("intake_brain", "merge_intake_information")
    builder.add_edge("merge_intake_information", "validate_patient_state")
    builder.add_edge("validate_patient_state", "determine_missing_information")

    builder.add_conditional_edges(
        "determine_missing_information",
        route_after_missing_check,
        {
            "need_more_info": "select_next_question",
            "complete": "evaluate_red_flags"
        }
    )

    builder.add_edge("select_next_question", "ask_next_question")
    builder.add_edge("ask_next_question", END)
    builder.add_edge("evaluate_red_flags", "risk_convergence")
    builder.add_edge("risk_convergence", "clinical_case_representation")
    builder.add_edge("clinical_case_representation", "care_navigation")
    builder.add_edge("care_navigation", "patient_monitoring")
    builder.add_edge("patient_monitoring", "ayurveda_modern_representation")
    builder.add_edge("ayurveda_modern_representation", END)

    return builder.compile()


def build_adaptive_graph():
    """Builds the adaptive, LLM-driven clinical history-taking workflow graph."""
    builder = StateGraph(VaidyaArcState)

    builder.add_node("tier1_safety_precheck", tier1_safety_precheck_node)
    builder.add_node("clinical_delta_extractor", clinical_delta_extractor_node)
    builder.add_node("state_consolidation_ledger", state_consolidation_ledger_node)
    builder.add_node("deterministic_governance", deterministic_governance_node)
    builder.add_node("adaptive_question_generator", adaptive_question_generator_node)
    builder.add_node("safety_scope_sanitizer", safety_scope_sanitizer_node)
    builder.add_node("casesheet_synthesizer", casesheet_synthesizer_node)

    # Downstream clinical nodes (Phases 2A through 12.5)
    builder.add_node("evaluate_red_flags", evaluate_red_flags)
    builder.add_node("risk_convergence", risk_convergence)
    builder.add_node("clinical_case_representation", clinical_case_representation)
    builder.add_node("care_navigation", care_navigation)
    builder.add_node("patient_monitoring", patient_monitoring)
    builder.add_node("ayurveda_modern_representation", ayurveda_modern_representation)

    builder.add_edge(START, "tier1_safety_precheck")
    builder.add_edge("tier1_safety_precheck", "clinical_delta_extractor")
    builder.add_edge("clinical_delta_extractor", "state_consolidation_ledger")
    builder.add_edge("state_consolidation_ledger", "deterministic_governance")

    builder.add_conditional_edges(
        "deterministic_governance",
        route_adaptive_governance,
        {
            "need_more_info": "adaptive_question_generator",
            "complete": "casesheet_synthesizer",
            "emergency": "evaluate_red_flags",
        }
    )

    builder.add_edge("adaptive_question_generator", "safety_scope_sanitizer")
    builder.add_edge("safety_scope_sanitizer", END)

    builder.add_edge("casesheet_synthesizer", "evaluate_red_flags")
    builder.add_edge("evaluate_red_flags", "risk_convergence")
    builder.add_edge("risk_convergence", "clinical_case_representation")
    builder.add_edge("clinical_case_representation", "care_navigation")
    builder.add_edge("care_navigation", "patient_monitoring")
    builder.add_edge("patient_monitoring", "ayurveda_modern_representation")
    builder.add_edge("ayurveda_modern_representation", END)

    return builder.compile()


def build_vaidyaarc_graph(enable_adaptive: Optional[bool] = None):
    """
    Builds the VaidyaArc workflow graph.
    If enable_adaptive is True (or env VAIDYAARC_ENABLE_ADAPTIVE_INTAKE is 'true'),
    builds the new adaptive clinical history-taking pipeline.
    Otherwise builds the legacy pipeline.
    """
    if enable_adaptive is None:
        enable_adaptive = os.getenv("VAIDYAARC_ENABLE_ADAPTIVE_INTAKE", "false").lower() in ("true", "1")

    if enable_adaptive:
        return build_adaptive_graph()
    return build_legacy_graph()
