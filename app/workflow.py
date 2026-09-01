from langgraph.graph import StateGraph, START, END

from app.red_flag_rules import evaluate_red_flags as evaluate_red_flag_rules
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


def route_after_missing_check(state: VaidyaArcState):
    missing = state.get("missing_information") or []
    if state.get("information_complete") and not missing:
        return "complete"
    return "need_more_info"


def build_vaidyaarc_graph():

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
    builder.add_edge("care_navigation", END)

    graph = builder.compile()

    return graph