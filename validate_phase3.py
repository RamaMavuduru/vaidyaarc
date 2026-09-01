#!/usr/bin/env python3
"""
Direct validation of Phase 3 Clinical Case Representation without LLM processing.
Fast deterministic test suite covering all specifications and edge cases.
"""

from app.clinical_case_node import clinical_case_representation, _calculate_completeness_score
from app.clinical_case_schema import ClinicalCase, ClinicalCaseOutput


def fresh_state():
    return {
        "patient_id": "TEST_PATIENT_001",
        "session_id": "SESSION_001",
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
        "red_flag_status": "no_obvious_red_flags",
        "red_flags": [],
        "red_flag_evidence": [],
        "immediate_attention_required": False,
        "red_flag_rule_hits": [],
        "risk_level": "LOW",
        "risk_score": 0,
        "risk_signal_summary": [],
        "risk_contributing_factors": [],
        "risk_evidence": [],
        "risk_reasoning": "Baseline low risk",
        "risk_override_reason": None,
        "recommended_next_action": "Routine follow-up",
        "risk_rule_hits": [],
        "convergence_status": "evaluated",
        "risk_context_flags": [],
        "risk_assessment_version": "phase2b_v1",
    }


def test_complete_high_risk_case():
    """Test 1: Complete High-Risk Case with Red Flags (Emergency Pathway)."""
    state = fresh_state()
    state.update({
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "sharp pressure",
        "location": "center of chest",
        "duration": "since this morning",
        "severity": "very severe",
        "associated_symptoms": ["shortness of breath"],
        "information_complete": True,
        "missing_information": [],
        "red_flag_status": "red_flags_detected",
        "red_flags": ["severe chest pain", "difficulty breathing"],
        "red_flag_evidence": ["severe chest pain", "difficulty breathing"],
        "immediate_attention_required": True,
        "red_flag_rule_hits": [
            {"rule_id": "severe_chest_pain", "label": "Severe chest pain", "evidence": ["severe chest pain"]},
            {"rule_id": "difficulty_breathing", "label": "Difficulty breathing", "evidence": ["difficulty breathing"]},
        ],
        "risk_level": "URGENT",
        "risk_score": 100,
        "risk_signal_summary": ["red_flag_override", "phase2a_red_flag"],
        "risk_contributing_factors": ["Phase 2A emergency safety rule triggered", "difficulty breathing", "severe chest pain"],
        "risk_evidence": ["difficulty breathing", "severe chest pain"],
        "risk_reasoning": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
        "risk_override_reason": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
        "recommended_next_action": "Immediate appropriate medical attention or urgent clinical evaluation.",
        "convergence_status": "overridden_by_red_flag",
    })

    result = clinical_case_representation(state)
    assert result.get("case_generation_status") == "generated", "Case status should be generated"
    case = result.get("clinical_case")
    assert case is not None, "Clinical case dict must exist"
    assert case.get("care_pathway_status") == "emergency", f"Expected emergency, got {case.get('care_pathway_status')}"
    assert case.get("data_quality", {}).get("information_complete") is True
    assert case.get("data_quality", {}).get("completeness_percentage") == 100.0
    assert case.get("safety_findings", {}).get("immediate_attention_required") is True
    assert case.get("safety_findings", {}).get("red_flag_status") == "red_flags_detected"
    assert case.get("risk_assessment", {}).get("risk_level") == "URGENT"
    assert result.get("clinical_case_output", {}).get("case_ready_for_review") is True
    print("TEST 1 (Complete High-Risk / Emergency): PASS")


def test_incomplete_case():
    """Test 2: Incomplete Case with Missing Severity and Duration (Incomplete Pathway)."""
    state = fresh_state()
    state.update({
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "information_complete": False,
        "missing_information": ["severity", "duration"],
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 0,
        "risk_reasoning": "Incomplete information; case deferred.",
        "recommended_next_action": "Collect missing information.",
        "convergence_status": "incomplete",
    })

    result = clinical_case_representation(state)
    assert result.get("case_generation_status") == "generated", "Case should be generated even if incomplete"
    case = result.get("clinical_case")
    assert case is not None
    assert case.get("care_pathway_status") == "incomplete", f"Expected incomplete, got {case.get('care_pathway_status')}"
    assert case.get("data_quality", {}).get("information_complete") is False
    assert result.get("clinical_case_output", {}).get("case_ready_for_review") is False
    assert "severity" in case.get("data_quality", {}).get("missing_fields", [])
    assert "duration" in case.get("data_quality", {}).get("missing_fields", [])
    # Stomach pain has 5 required fields; 3 are populated (complaint, nature, location) -> 60.0%
    assert case.get("data_quality", {}).get("completeness_percentage") == 60.0
    print("TEST 2 (Incomplete Case / Incomplete Pathway): PASS")


def test_low_risk_routine_case():
    """Test 3: Low-Risk Routine Case (Routine Pathway)."""
    state = fresh_state()
    state.update({
        "chief_complaint": "mild fever",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "missing_information": [],
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 8,
        "risk_signal_summary": ["prolonged_duration"],
        "risk_contributing_factors": ["prolonged duration"],
        "risk_evidence": ["2 days"],
        "risk_reasoning": "Phase 2B aggregated 1 deterministic risk signal.",
        "recommended_next_action": "Routine follow-up and monitoring as appropriate.",
        "convergence_status": "evaluated",
    })

    result = clinical_case_representation(state)
    assert result.get("case_generation_status") == "generated"
    case = result.get("clinical_case")
    assert case is not None
    assert case.get("care_pathway_status") == "routine", f"Expected routine, got {case.get('care_pathway_status')}"
    assert case.get("risk_assessment", {}).get("risk_level") == "LOW"
    assert case.get("safety_findings", {}).get("red_flag_status") == "no_obvious_red_flags"
    assert result.get("clinical_case_output", {}).get("case_ready_for_review") is True
    print("TEST 3 (Low-Risk Routine Case / Routine Pathway): PASS")


def test_elderly_chronic_conditions():
    """Test 4: Elderly Patient with Chronic Conditions (Urgent Pathway)."""
    state = fresh_state()
    state["patient_profile"] = {"age": 72, "medical_conditions": ["diabetes", "hypertension"], "allergies": []}
    state.update({
        "chief_complaint": "severe fever",
        "duration": "5 days",
        "severity": "severe",
        "associated_symptoms": ["fatigue"],
        "information_complete": True,
        "missing_information": [],
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "HIGH",
        "risk_score": 34,
        "risk_signal_summary": ["severe_symptom_present", "prolonged_duration", "age_or_vulnerability_context"],
        "risk_contributing_factors": ["high severity", "prolonged duration", "age-related vulnerability"],
        "risk_evidence": ["severe", "5 days", "age 72"],
        "risk_reasoning": "Phase 2B aggregated 3 deterministic risk signals.",
        "recommended_next_action": "Prompt clinical evaluation and reassessment.",
        "convergence_status": "evaluated",
    })

    result = clinical_case_representation(state)
    assert result.get("case_generation_status") == "generated"
    case = result.get("clinical_case")
    assert case is not None
    assert case.get("care_pathway_status") == "urgent", f"Expected urgent, got {case.get('care_pathway_status')}"
    assert case.get("risk_assessment", {}).get("risk_level") == "HIGH"
    assert case.get("patient_identifier", {}).get("age") == 72
    assert "diabetes" in case.get("patient_identifier", {}).get("known_conditions", [])
    assert "hypertension" in case.get("patient_identifier", {}).get("known_conditions", [])
    assert len(case.get("medical_history_summary", [])) == 2
    assert result.get("clinical_case_output", {}).get("case_ready_for_review") is True
    print("TEST 4 (Elderly with Chronic Conditions / Urgent Pathway): PASS")


def test_phase2a_override():
    """Test 5: Phase 2A Override (Red Flag Takes Precedence)."""
    state = fresh_state()
    state.update({
        "chief_complaint": "abdominal pain",
        "nature_of_pain": "cramping",
        "location": "lower abdomen",
        "duration": "2 hours",
        "severity": "moderate",
        "associated_symptoms": ["vomiting", "fainting"],
        "information_complete": True,
        "missing_information": [],
        "red_flag_status": "red_flags_detected",
        "red_flags": ["fainting or loss of consciousness"],
        "red_flag_evidence": ["fainting or loss of consciousness"],
        "immediate_attention_required": True,
        "red_flag_rule_hits": [{"rule_id": "fainting_loss_of_consciousness"}],
        "risk_level": "URGENT",
        "risk_score": 100,
        "risk_signal_summary": ["red_flag_override", "phase2a_red_flag"],
        "risk_contributing_factors": ["Phase 2A emergency safety rule triggered"],
        "risk_evidence": ["fainting or loss of consciousness"],
        "risk_reasoning": "Phase 2A red-flag rules identified an immediate safety concern.",
        "risk_override_reason": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
        "recommended_next_action": "Immediate appropriate medical attention or urgent clinical evaluation.",
        "convergence_status": "overridden_by_red_flag",
    })

    result = clinical_case_representation(state)
    assert result.get("case_generation_status") == "generated"
    case = result.get("clinical_case")
    assert case is not None
    assert case.get("care_pathway_status") == "emergency", f"Expected emergency, got {case.get('care_pathway_status')}"
    assert case.get("safety_findings", {}).get("immediate_attention_required") is True
    assert case.get("risk_assessment", {}).get("risk_override_reason") is not None
    assert "Phase 2A" in case.get("risk_assessment", {}).get("risk_override_reason", "")
    print("TEST 5 (Phase 2A Override / Emergency Pathway): PASS")


def test_complaint_specific_completeness():
    """Test 6: Complaint-Specific Completeness Calculation."""
    # Fever: requires chief_complaint, duration, severity (3 fields)
    fever_partial = fresh_state()
    fever_partial.update({
        "chief_complaint": "fever",
        "duration": "2 days",
        "severity": None,
        "information_complete": False,
        "missing_information": ["severity"],
    })
    score_fever = _calculate_completeness_score(fever_partial)
    assert score_fever == 66.7, f"Expected 66.7% for fever (2/3 fields), got {score_fever}"

    # Cough: requires chief_complaint, duration (2 fields)
    cough_complete = fresh_state()
    cough_complete.update({
        "chief_complaint": "cough",
        "duration": "3 days",
        "information_complete": True,
        "missing_information": [],
    })
    score_cough = _calculate_completeness_score(cough_complete)
    assert score_cough == 100.0, f"Expected 100.0% for cough (2/2 fields), got {score_cough}"

    # Stomach pain: requires 5 fields. If only chief_complaint is given -> 20.0%
    stomach_1field = fresh_state()
    stomach_1field.update({
        "chief_complaint": "stomach pain",
        "information_complete": False,
        "missing_information": ["nature_of_pain", "location", "duration", "severity"],
    })
    score_stomach = _calculate_completeness_score(stomach_1field)
    assert score_stomach == 20.0, f"Expected 20.0% for stomach pain (1/5 fields), got {score_stomach}"

    print("TEST 6 (Complaint-Specific Completeness): PASS")


def test_pydantic_schema_validation():
    """Test 7: Pydantic Schema Model Validation and Traceability Integrity."""
    state = fresh_state()
    state.update({
        "chief_complaint": "headache",
        "duration": "1 day",
        "severity": "moderate",
        "location": "frontal",
        "information_complete": True,
        "missing_information": [],
        "risk_level": "LOW",
        "risk_score": 0,
        "red_flag_status": "no_obvious_red_flags",
    })

    result = clinical_case_representation(state)
    case_dict = result.get("clinical_case")
    output_dict = result.get("clinical_case_output")

    # Validate by reconstructing Pydantic models from dicts
    case_model = ClinicalCase(**case_dict)
    output_model = ClinicalCaseOutput(**output_dict)

    assert case_model.case_id == case_dict["case_id"]
    assert output_model.formatting_version == "phase3_v1"
    assert "phase_1b" in case_model.source_phase_evidence
    assert "phase_2a" in case_model.source_phase_evidence
    assert "phase_2b" in case_model.source_phase_evidence
    print("TEST 7 (Pydantic Schema Validation & Traceability): PASS")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RUNNING PHASE 3 DIRECT VALIDATION SUITE (FAST / ZERO-LLM)")
    print("=" * 80)
    test_complete_high_risk_case()
    test_incomplete_case()
    test_low_risk_routine_case()
    test_elderly_chronic_conditions()
    test_phase2a_override()
    test_complaint_specific_completeness()
    test_pydantic_schema_validation()
    print("=" * 80)
    print("ALL 7 PHASE 3 DIRECT VALIDATION TESTS PASSED CLEANLY!")
    print("=" * 80)

