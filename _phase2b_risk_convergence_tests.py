"""Phase 2B risk convergence deterministic tests."""

from app.workflow import build_vaidyaarc_graph


def fresh_state():
    return {
        "patient_id": "TEST001",
        "session_id": "SESSION001",
        "language": "English",
        "patient_profile": {"age": 30, "medical_conditions": [], "allergies": []},
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],
        "red_flag_status": None,
        "red_flags": [],
        "red_flag_evidence": [],
        "immediate_attention_required": False,
        "red_flag_rule_hits": [],
        "risk_level": None,
        "risk_score": None,
        "risk_signal_summary": [],
        "risk_contributing_factors": [],
        "risk_evidence": [],
        "risk_reasoning": None,
        "risk_override_reason": None,
        "recommended_next_action": None,
        "risk_rule_hits": [],
        "convergence_status": None,
        "risk_context_flags": [],
        "risk_assessment_version": None,
    }


def run_case(label, state):
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    print(f"\n{label}")
    print(result)
    return result


def assert_contains(actual, expected, field_name):
    if expected not in actual:
        raise AssertionError(f"{field_name} expected to contain {expected!r}, got {actual!r}")


# Low risk case
state = fresh_state()
state.update({
    "chief_complaint": "fever",
    "duration": "2 days",
    "severity": "mild",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have mild fever for 2 days",
    "associated_symptoms": [],
})
low_case = run_case("LOW RISK CASE", state)
assert low_case.get("risk_level") == "LOW", low_case
assert low_case.get("risk_score", 0) <= 9, low_case
assert "risk_rule_hits" in low_case, low_case

# Moderate risk case
state = fresh_state()
state.update({
    "chief_complaint": "stomach pain",
    "nature_of_pain": "burning",
    "location": "upper abdomen",
    "duration": "3 days",
    "severity": "moderate",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have burning stomach pain in upper abdomen for 3 days",
    "associated_symptoms": ["nausea", "fatigue"],
})
moderate_case = run_case("MODERATE RISK CASE", state)
assert moderate_case.get("risk_level") == "MODERATE", moderate_case
assert 10 <= moderate_case.get("risk_score", 0) <= 24, moderate_case

# High risk case (worsening severe symptom without red-flag triggers)
state = fresh_state()
state.update({
    "chief_complaint": "abdominal pain",
    "nature_of_pain": "sharp",
    "location": "upper abdomen",
    "duration": "5 days",
    "severity": "severe",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have severe abdominal pain for 5 days and it is worsening",
    "associated_symptoms": ["nausea", "fatigue"],
    "red_flag_status": "no_obvious_red_flags",
    "red_flags": [],
    "red_flag_evidence": [],
    "immediate_attention_required": False,
})
high_case = run_case("HIGH RISK CASE", state)
assert high_case.get("risk_level") == "HIGH", high_case
assert 25 <= high_case.get("risk_score", 0) <= 39, high_case

# Incomplete information case
state = fresh_state()
state.update({
    "chief_complaint": "fever",
    "duration": None,
    "severity": None,
    "information_complete": False,
    "missing_information": ["duration", "severity"],
    "current_message": "I have fever",
})
incomplete_case = run_case("INCOMPLETE CASE", state)
assert incomplete_case.get("risk_level") == "INCOMPLETE", incomplete_case
assert incomplete_case.get("convergence_status") == "incomplete", incomplete_case
assert incomplete_case.get("risk_score") == 0, incomplete_case

# Red flag override
state = fresh_state()
state.update({
    "chief_complaint": "severe chest pain",
    "nature_of_pain": "sharp",
    "location": "center of chest",
    "duration": "today",
    "severity": "very severe",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have severe chest pain and shortness of breath",
    "associated_symptoms": ["shortness of breath"],
    "red_flag_status": "red_flags_detected",
    "red_flags": ["severe chest pain", "difficulty breathing"],
    "red_flag_evidence": ["severe chest pain", "difficulty breathing"],
    "immediate_attention_required": True,
})
urgent_case = run_case("RED FLAG OVERRIDE", state)
assert urgent_case.get("risk_level") == "URGENT", urgent_case
assert urgent_case.get("risk_override_reason") is not None, urgent_case

# Immediate attention override
state = fresh_state()
state.update({
    "chief_complaint": "abdominal pain",
    "nature_of_pain": "cramping",
    "location": "lower abdomen",
    "duration": "2 days",
    "severity": "moderate",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have lower abdominal pain and vomiting",
    "associated_symptoms": ["vomiting", "fainting"],
    "red_flag_status": "no_obvious_red_flags",
    "red_flags": [],
    "red_flag_evidence": [],
    "immediate_attention_required": True,
})
urgent_case_2 = run_case("IMMEDIATE ATTENTION OVERRIDE", state)
assert urgent_case_2.get("risk_level") == "URGENT", urgent_case_2

# Evidence and rule traceability
state = fresh_state()
state.update({
    "chief_complaint": "fever",
    "duration": "5 days",
    "severity": "severe",
    "information_complete": True,
    "missing_information": [],
    "current_message": "I have severe fever for 5 days and I feel worse",
    "associated_symptoms": ["fatigue"],
    "patient_profile": {"age": 72, "medical_conditions": ["diabetes"], "allergies": []},
})
trace_case = run_case("TRACEABILITY CASE", state)
assert trace_case.get("risk_evidence"), trace_case
assert trace_case.get("risk_rule_hits"), trace_case
assert isinstance(trace_case.get("risk_rule_hits"), list), trace_case
assert trace_case.get("risk_assessment_version") == "phase2b_v1", trace_case

print("\nPHASE 2B TEST SUITE: PASS")
