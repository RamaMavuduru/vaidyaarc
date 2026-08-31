from langgraph.graph import StateGraph, START, END

from app.state import VaidyaArcState

from app.nodes import (
    intake_brain,
    merge_intake_information,
    validate_patient_state,
    determine_missing_information,
    select_next_question,
    ask_next_question,
    evaluate_red_flags
)


def route_after_missing_check(state: VaidyaArcState):

    if state.get("information_complete"):
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
    builder.add_edge("evaluate_red_flags", END)

    graph = builder.compile()

    return graph