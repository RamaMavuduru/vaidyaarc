"""
Phase 3 Clinical Case Representation Tests.

Comprehensive test suite for Phase 3 case representation.
Tests all 5 use cases from specification.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflow import build_vaidyaarc_graph
from app.clinical_case_node import clinical_case_representation


def fresh_state():
    """Create a fresh patient state for each test."""
    return {
        "patient_id": "TEST001",
        "session_id": "SESSION001",
        "language": "English",
        "patient_profile": {
            "age": 30,
            "medical_conditions": [],
            "allergies": []
        },
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
    """Run a test case through the workflow."""
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    print(f"\n{label}")
    print(f"Case Generation Status: {result.get('case_generation_status')}")
    print(f"Case Ready for Review: {result.get('clinical_case_output', {}).get('case_ready_for_review')}")
    if result.get("clinical_case"):
        case = result["clinical_case"]
        print(f"  Care Pathway: {case.get('care_pathway_status')}")
        print(f"  Risk Level: {case.get('risk_assessment', {}).get('risk_level')}")
        print(f"  Red Flag Status: {case.get('safety_findings', {}).get('red_flag_status')}")
        print(f"  Immediate Attention Required: {case.get('safety_findings', {}).get('immediate_attention_required')}")
        print(f"  Data Completeness: {case.get('data_quality', {}).get('completeness_percentage')}%")
        print(f"  Case Summary: {case.get('case_summary')}")
    if result.get("case_validation_errors"):
        print(f"  Validation Errors: {result.get('case_validation_errors')}")
    return result


# =============================================================================
# TEST 1: Complete High-Risk Case with Red Flags
# =============================================================================
print("\n" + "="*80)
print("TEST 1: COMPLETE HIGH-RISK CASE WITH RED FLAGS (Emergency Pathway)")
print("="*80)

state1 = fresh_state()
state1.update({
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
        {"rule_id": "difficulty_breathing", "label": "Difficulty breathing", "evidence": ["difficulty breathing"]}
    ],
    "risk_level": "URGENT",
    "risk_score": 100,
    "risk_signal_summary": ["red_flag_override", "phase2a_red_flag"],
    "risk_contributing_factors": ["Phase 2A emergency safety rule triggered", "difficulty breathing", "severe chest pain"],
    "risk_evidence": ["difficulty breathing", "severe chest pain"],
    "risk_reasoning": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
    "risk_override_reason": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
    "recommended_next_action": "Immediate appropriate medical attention or urgent clinical evaluation.",
    "risk_rule_hits": [
        {"rule_id": "red_flag_override", "category": "safety_override", "weight": 100}
    ],
    "convergence_status": "overridden_by_red_flag",
})

result1 = run_case("TEST 1: Complete High-Risk with Red Flags", state1)
assert result1.get("case_generation_status") == "generated", "Case should be generated"
case1 = result1.get("clinical_case")
assert case1 is not None, "Clinical case should exist"
assert case1.get("care_pathway_status") == "emergency", f"Expected emergency, got {case1.get('care_pathway_status')}"
assert case1.get("data_quality", {}).get("information_complete") is True, "Information should be complete"
assert case1.get("safety_findings", {}).get("red_flag_status") == "red_flags_detected", "Red flags should be detected"
assert case1.get("safety_findings", {}).get("immediate_attention_required") is True, "Immediate attention should be required"
print("[PASS] TEST 1 PASSED")


# =============================================================================
# TEST 2: Incomplete Case with Missing Severity
# =============================================================================
print("\n" + "="*80)
print("TEST 2: INCOMPLETE CASE WITH MISSING SEVERITY (Incomplete Pathway)")
print("="*80)

state2 = fresh_state()
state2.update({
    "chief_complaint": "stomach pain",
    "nature_of_pain": "burning",
    "location": "upper abdomen",
    "duration": None,
    "severity": None,
    "associated_symptoms": [],
    "information_complete": False,
    "missing_information": ["severity", "duration"],
    "red_flag_status": "no_obvious_red_flags",
    "red_flags": [],
    "red_flag_evidence": [],
    "immediate_attention_required": False,
    "risk_level": "LOW",
    "risk_score": 0,
    "risk_signal_summary": [],
    "risk_contributing_factors": [],
    "risk_evidence": [],
    "risk_reasoning": "Incomplete information; case deferred.",
    "recommended_next_action": "Collect missing information.",
    "convergence_status": "incomplete",
})

result2 = clinical_case_representation(state2)
print("\nTEST 2: Incomplete Case (Direct Node Evaluation)")
print(f"Case Generation Status: {result2.get('case_generation_status')}")
print(f"Case Ready for Review: {result2.get('clinical_case_output', {}).get('case_ready_for_review')}")
case2 = result2.get("clinical_case")
if case2:
    print(f"  Care Pathway: {case2.get('care_pathway_status')}")
    print(f"  Data Completeness: {case2.get('data_quality', {}).get('completeness_percentage')}%")
    print(f"  Missing Fields: {case2.get('data_quality', {}).get('missing_fields')}")
    print(f"  Case Summary: {case2.get('case_summary')}")

assert result2.get("case_generation_status") == "generated", "Case should still be generated even if incomplete"
assert case2 is not None, "Clinical case should exist"
assert result2.get("clinical_case_output", {}).get("case_ready_for_review") is False, "Case should not be ready for review"
assert case2.get("care_pathway_status") == "incomplete", f"Expected incomplete, got {case2.get('care_pathway_status')}"
assert case2.get("data_quality", {}).get("information_complete") is False, "Information should be incomplete"
assert "severity" in case2.get("data_quality", {}).get("missing_fields", []), "Severity should be in missing fields"
assert "duration" in case2.get("data_quality", {}).get("missing_fields", []), "Duration should be in missing fields"
print("[PASS] TEST 2 PASSED")


# =============================================================================
# TEST 3: Low-Risk Routine Case
# =============================================================================
print("\n" + "="*80)
print("TEST 3: LOW-RISK ROUTINE CASE (Routine Pathway)")
print("="*80)

state3 = fresh_state()
state3.update({
    "chief_complaint": "mild fever",
    "duration": "2 days",
    "severity": "mild",
    "associated_symptoms": [],
    "information_complete": True,
    "missing_information": [],
    "red_flag_status": "no_obvious_red_flags",
    "red_flags": [],
    "red_flag_evidence": [],
    "immediate_attention_required": False,
    "risk_level": "LOW",
    "risk_score": 8,
    "risk_signal_summary": ["prolonged_duration"],
    "risk_contributing_factors": ["prolonged duration"],
    "risk_evidence": ["2 days"],
    "risk_reasoning": "Phase 2B aggregated 1 deterministic risk signals. Persistent or prolonged symptoms can increase overall risk.",
    "recommended_next_action": "Routine follow-up and monitoring as appropriate.",
    "convergence_status": "evaluated",
})

result3 = run_case("TEST 3: Low-Risk Routine Case", state3)
assert result3.get("case_generation_status") == "generated", "Case should be generated"
case3 = result3.get("clinical_case")
assert case3 is not None, "Clinical case should exist"
assert result3.get("clinical_case_output", {}).get("case_ready_for_review") is True, "Case should be ready for review"
assert case3.get("care_pathway_status") == "routine", f"Expected routine, got {case3.get('care_pathway_status')}"
assert case3.get("risk_assessment", {}).get("risk_level") == "LOW", "Risk level should be LOW"
assert case3.get("safety_findings", {}).get("red_flag_status") == "no_obvious_red_flags", "No red flags"
print("[PASS] TEST 3 PASSED")


# =============================================================================
# TEST 4: Elderly Patient with Chronic Conditions
# =============================================================================
print("\n" + "="*80)
print("TEST 4: ELDERLY WITH CHRONIC CONDITIONS (High-Risk Pathway)")
print("="*80)

state4 = fresh_state()
state4["patient_profile"]["age"] = 72
state4["patient_profile"]["medical_conditions"] = ["diabetes", "hypertension"]
state4.update({
    "chief_complaint": "severe fever",
    "duration": "5 days",
    "severity": "severe",
    "associated_symptoms": ["fatigue"],
    "information_complete": True,
    "missing_information": [],
    "red_flag_status": "no_obvious_red_flags",
    "red_flags": [],
    "red_flag_evidence": [],
    "immediate_attention_required": False,
    "risk_level": "HIGH",
    "risk_score": 34,
    "risk_signal_summary": ["severe_symptom_present", "prolonged_duration", "age_or_vulnerability_context"],
    "risk_contributing_factors": ["high severity", "prolonged duration", "age-related vulnerability"],
    "risk_evidence": ["severe", "5 days", "age 72"],
    "risk_reasoning": "Phase 2B aggregated 3 deterministic risk signals. High severity, prolonged symptoms, and age-related vulnerability increase overall risk.",
    "recommended_next_action": "Prompt clinical evaluation and reassessment.",
    "convergence_status": "evaluated",
})

result4 = run_case("TEST 4: Elderly with Chronic Conditions", state4)
assert result4.get("case_generation_status") == "generated", "Case should be generated"
case4 = result4.get("clinical_case")
assert case4 is not None, "Clinical case should exist"
assert result4.get("clinical_case_output", {}).get("case_ready_for_review") is True, "Case should be ready for review"
assert case4.get("care_pathway_status") == "urgent", f"Expected urgent, got {case4.get('care_pathway_status')}"
assert case4.get("risk_assessment", {}).get("risk_level") == "HIGH", f"Risk level should be HIGH, got {case4.get('risk_assessment', {}).get('risk_level')}"
assert case4.get("patient_identifier", {}).get("age") == 72, "Age should be 72"
assert "diabetes" in case4.get("patient_identifier", {}).get("known_conditions", []), "Diabetes should be in known conditions"
assert "hypertension" in case4.get("patient_identifier", {}).get("known_conditions", []), "Hypertension should be in known conditions"
print("[PASS] TEST 4 PASSED")


# =============================================================================
# TEST 5: Phase 2A Override (Red Flag Takes Precedence)
# =============================================================================
print("\n" + "="*80)
print("TEST 5: PHASE 2A OVERRIDE (Red Flag Takes Precedence, Emergency Pathway)")
print("="*80)

state5 = fresh_state()
state5.update({
    "chief_complaint": "abdominal pain",
    "nature_of_pain": "cramping",
    "location": "lower abdomen",
    "duration": "2 hours",
    "severity": "moderate",
    "associated_symptoms": ["vomiting", "fainted"],
    "current_message": "I fainted and passed out",
    "information_complete": True,
    "missing_information": [],
    "red_flag_status": "red_flags_detected",
    "red_flags": ["fainting or loss of consciousness", "vomiting"],
    "red_flag_evidence": ["fainting or loss of consciousness", "vomiting"],
    "immediate_attention_required": True,
    "red_flag_rule_hits": [
        {"rule_id": "fainting_loss_of_consciousness"},
        {"rule_id": "vomiting_blood"}
    ],
    "risk_level": "URGENT",
    "risk_score": 100,
    "risk_signal_summary": ["red_flag_override", "phase2a_red_flag"],
    "risk_contributing_factors": ["Phase 2A emergency safety rule triggered"],
    "risk_evidence": ["fainting or loss of consciousness", "vomiting"],
    "risk_reasoning": "Phase 2A red-flag rules identified an immediate safety concern.",
    "risk_override_reason": "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk.",
    "recommended_next_action": "Immediate appropriate medical attention or urgent clinical evaluation.",
    "convergence_status": "overridden_by_red_flag",
})

result5 = run_case("TEST 5: Phase 2A Override", state5)
assert result5.get("case_generation_status") == "generated", "Case should be generated"
case5 = result5.get("clinical_case")
assert case5 is not None, "Clinical case should exist"
assert case5.get("care_pathway_status") == "emergency", f"Expected emergency, got {case5.get('care_pathway_status')}"
assert case5.get("safety_findings", {}).get("immediate_attention_required") is True, "Immediate attention required"
assert case5.get("risk_assessment", {}).get("risk_override_reason") is not None, "Risk override reason should be present"
assert "Phase 2A" in case5.get("risk_assessment", {}).get("risk_override_reason", ""), "Override reason should mention Phase 2A"
print("[PASS] TEST 5 PASSED")


# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*80)
print("PHASE 3 TEST SUITE SUMMARY")
print("="*80)
print("[PASS] TEST 1: Complete High-Risk Case with Red Flags - PASSED")
print("[PASS] TEST 2: Incomplete Case with Missing Severity - PASSED")
print("[PASS] TEST 3: Low-Risk Routine Case - PASSED")
print("[PASS] TEST 4: Elderly Patient with Chronic Conditions - PASSED")
print("[PASS] TEST 5: Phase 2A Override (Red Flag Takes Precedence) - PASSED")
print("\nALL PHASE 3 TESTS PASSED!")
print("="*80)
