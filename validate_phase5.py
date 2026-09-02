"""
Phase 5 Direct Validation Test Suite (Fast / Zero-LLM).

Validates all 10 core monitoring, trajectory classification, risk comparison,
symptom delta detection, and safety override scenarios.
"""

from app.follow_up_schema import FollowUpMonitoringOutput
from app.follow_up_comparison import (
    compare_clinical_states,
    compare_severity,
    compare_symptoms,
    compare_risk,
    classify_patient_trajectory,
)


def run_phase5_tests():
    print("=" * 80)
    print("RUNNING PHASE 5 DIRECT VALIDATION SUITE (FAST / ZERO-LLM)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST 1: Stable Case
    # -------------------------------------------------------------------------
    prev_1 = {
        "patient_id": "P001",
        "session_id": "S001",
        "chief_complaint": "mild fever",
        "severity": "mild",
        "duration": "2 days",
        "associated_symptoms": [],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    curr_1 = {
        "patient_id": "P001",
        "session_id": "S002",
        "chief_complaint": "mild fever",
        "severity": "mild",
        "duration": "3 days",
        "associated_symptoms": [],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    out_1 = compare_clinical_states(prev_1, curr_1)
    assert out_1.trajectory.trajectory == "stable", f"Test 1 failed: expected 'stable', got '{out_1.trajectory.trajectory}'"
    assert out_1.risk_comparison.risk_trend == "unchanged", f"Test 1 failed: expected 'unchanged', got '{out_1.risk_comparison.risk_trend}'"
    print("TEST 1 (Stable Case): PASS")

    # -------------------------------------------------------------------------
    # TEST 2: Improving Case
    # -------------------------------------------------------------------------
    prev_2 = {
        "patient_id": "P002",
        "session_id": "S001",
        "chief_complaint": "fever",
        "severity": "severe",
        "associated_symptoms": ["fatigue"],
        "risk_level": "HIGH",
        "risk_score": 28,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    curr_2 = {
        "patient_id": "P002",
        "session_id": "S002",
        "chief_complaint": "fever",
        "severity": "mild",
        "associated_symptoms": ["fatigue"],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    out_2 = compare_clinical_states(prev_2, curr_2)
    assert out_2.trajectory.trajectory == "improving", f"Test 2 failed: expected 'improving', got '{out_2.trajectory.trajectory}'"
    assert out_2.risk_comparison.risk_trend == "decreased", f"Test 2 failed: expected 'decreased', got '{out_2.risk_comparison.risk_trend}'"
    print("TEST 2 (Improving Case): PASS")

    # -------------------------------------------------------------------------
    # TEST 3: Worsening Case
    # -------------------------------------------------------------------------
    prev_3 = {
        "patient_id": "P003",
        "session_id": "S001",
        "chief_complaint": "stomach pain",
        "severity": "mild",
        "associated_symptoms": [],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    curr_3 = {
        "patient_id": "P003",
        "session_id": "S002",
        "chief_complaint": "stomach pain",
        "severity": "severe",
        "associated_symptoms": [],
        "risk_level": "HIGH",
        "risk_score": 28,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    out_3 = compare_clinical_states(prev_3, curr_3)
    assert out_3.trajectory.trajectory == "worsening", f"Test 3 failed: expected 'worsening', got '{out_3.trajectory.trajectory}'"
    assert out_3.risk_comparison.risk_trend == "increased", f"Test 3 failed: expected 'increased', got '{out_3.risk_comparison.risk_trend}'"
    print("TEST 3 (Worsening Case): PASS")

    # -------------------------------------------------------------------------
    # TEST 4: New Symptom Emergence with Red Flag Preservation
    # -------------------------------------------------------------------------
    prev_4 = {
        "patient_id": "P004",
        "session_id": "S001",
        "chief_complaint": "fever",
        "severity": "mild",
        "associated_symptoms": ["fatigue"],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    curr_4 = {
        "patient_id": "P004",
        "session_id": "S002",
        "chief_complaint": "fever",
        "severity": "moderate",
        "associated_symptoms": ["fatigue", "difficulty breathing"],
        "risk_level": "URGENT",
        "risk_score": 50,
        "immediate_attention_required": True,
        "red_flag_status": "red_flags_detected",
        "red_flags": ["difficulty breathing"],
    }
    out_4 = compare_clinical_states(prev_4, curr_4)
    assert "difficulty breathing" in out_4.symptom_changes.new_symptoms, "Test 4 failed: 'difficulty breathing' missing from new_symptoms"
    assert out_4.trajectory.trajectory == "escalation_required", f"Test 4 failed: expected 'escalation_required', got '{out_4.trajectory.trajectory}'"
    print("TEST 4 (New Symptom with Red Flag Preservation): PASS")

    # -------------------------------------------------------------------------
    # TEST 5: Risk Increase Tracking
    # -------------------------------------------------------------------------
    prev_5 = {
        "patient_id": "P005",
        "session_id": "S001",
        "risk_level": "LOW",
        "risk_score": 8,
        "severity": "mild",
        "chief_complaint": "cough",
    }
    curr_5 = {
        "patient_id": "P005",
        "session_id": "S002",
        "risk_level": "MODERATE",
        "risk_score": 18,
        "severity": "moderate",
        "chief_complaint": "cough",
    }
    out_5 = compare_clinical_states(prev_5, curr_5)
    assert out_5.risk_comparison.risk_trend == "increased", f"Test 5 failed: expected 'increased', got '{out_5.risk_comparison.risk_trend}'"
    assert out_5.risk_comparison.previous_risk_score == 8
    assert out_5.risk_comparison.current_risk_score == 18
    print("TEST 5 (Risk Increase Tracking): PASS")

    # -------------------------------------------------------------------------
    # TEST 6: Risk Decrease Tracking
    # -------------------------------------------------------------------------
    prev_6 = {
        "patient_id": "P006",
        "session_id": "S001",
        "risk_level": "HIGH",
        "risk_score": 28,
        "severity": "severe",
        "chief_complaint": "fever",
    }
    curr_6 = {
        "patient_id": "P006",
        "session_id": "S002",
        "risk_level": "LOW",
        "risk_score": 8,
        "severity": "mild",
        "chief_complaint": "fever",
    }
    out_6 = compare_clinical_states(prev_6, curr_6)
    assert out_6.risk_comparison.risk_trend == "decreased", f"Test 6 failed: expected 'decreased', got '{out_6.risk_comparison.risk_trend}'"
    assert out_6.risk_comparison.previous_risk_level == "HIGH"
    assert out_6.risk_comparison.current_risk_level == "LOW"
    print("TEST 6 (Risk Decrease Tracking): PASS")

    # -------------------------------------------------------------------------
    # TEST 7: Explicit Symptom Resolution (Missing != Resolved Rule)
    # -------------------------------------------------------------------------
    prev_7 = {
        "patient_id": "P007",
        "session_id": "S001",
        "chief_complaint": "stomach pain",
        "severity": "moderate",
        "associated_symptoms": ["vomiting", "nausea"],
        "risk_level": "MODERATE",
        "risk_score": 18,
    }
    # Case 7A: Explicit statement of resolution
    curr_7a = {
        "patient_id": "P007",
        "session_id": "S002",
        "chief_complaint": "stomach pain",
        "severity": "mild",
        "associated_symptoms": ["nausea"],
        "current_message": "My vomiting has resolved and stopped completely",
        "risk_level": "LOW",
        "risk_score": 8,
    }
    out_7a = compare_clinical_states(prev_7, curr_7a)
    assert "vomiting" in out_7a.symptom_changes.resolved_symptoms, f"Test 7A failed: 'vomiting' not detected in resolved_symptoms: {out_7a.symptom_changes.resolved_symptoms}"

    # Case 7B: Missing != Resolved (vomiting simply not mentioned)
    curr_7b = {
        "patient_id": "P007",
        "session_id": "S002",
        "chief_complaint": "stomach pain",
        "severity": "mild",
        "associated_symptoms": ["nausea"],
        "current_message": "I only have slight nausea today",
        "risk_level": "LOW",
        "risk_score": 8,
    }
    out_7b = compare_clinical_states(prev_7, curr_7b)
    assert "vomiting" not in out_7b.symptom_changes.resolved_symptoms, "Test 7B failed: vomiting must NOT be marked resolved merely because it was unmentioned"
    assert "vomiting" in out_7b.symptom_changes.unmentioned_symptoms, "Test 7B failed: vomiting should be in unmentioned_symptoms"
    print("TEST 7 (Explicit Resolution & Missing != Resolved Invariant): PASS")

    # -------------------------------------------------------------------------
    # TEST 8: Insufficient Information / Vague Statements
    # -------------------------------------------------------------------------
    prev_8 = {
        "patient_id": "P008",
        "session_id": "S001",
        "chief_complaint": "chest pain",
        "severity": "moderate",
        "associated_symptoms": [],
        "risk_level": "MODERATE",
        "risk_score": 18,
    }
    curr_8 = {
        "patient_id": "P008",
        "session_id": "S002",
        "chief_complaint": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "I feel fine I guess",
        "risk_level": None,
        "risk_score": None,
    }
    out_8 = compare_clinical_states(prev_8, curr_8)
    assert out_8.trajectory.trajectory == "insufficient_information", f"Test 8 failed: expected 'insufficient_information', got '{out_8.trajectory.trajectory}'"
    print("TEST 8 (Insufficient Information / Guard Against Vague Inputs): PASS")

    # -------------------------------------------------------------------------
    # TEST 9: Phase 2A Red-Flag Override (Cannot be downgraded)
    # -------------------------------------------------------------------------
    prev_9 = {
        "patient_id": "P009",
        "session_id": "S001",
        "chief_complaint": "fever",
        "severity": "mild",
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    curr_9 = {
        "patient_id": "P009",
        "session_id": "S002",
        "chief_complaint": "severe chest pain",
        "severity": "severe",
        "associated_symptoms": ["shortness of breath"],
        "risk_level": "URGENT",
        "risk_score": 55,
        "immediate_attention_required": True,
        "red_flag_status": "red_flags_detected",
        "red_flags": ["severe chest pain"],
    }
    out_9 = compare_clinical_states(prev_9, curr_9)
    assert out_9.trajectory.trajectory == "escalation_required", f"Test 9 failed: expected 'escalation_required', got '{out_9.trajectory.trajectory}'"
    assert "immediate attention required" in " ".join(out_9.trajectory.evidence).lower(), "Test 9 failed: immediate attention not noted in evidence"
    print("TEST 9 (Phase 2A Red-Flag Override Enforcement): PASS")

    # -------------------------------------------------------------------------
    # TEST 10: Initial Encounter (Clean Baseline Handling)
    # -------------------------------------------------------------------------
    curr_10 = {
        "patient_id": "P010",
        "session_id": "S001",
        "chief_complaint": "fever",
        "severity": "moderate",
        "associated_symptoms": ["fatigue"],
        "risk_level": "MODERATE",
        "risk_score": 18,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
    }
    out_10 = compare_clinical_states(None, curr_10)
    assert out_10.monitoring_status == "initial_encounter", f"Test 10 failed: expected 'initial_encounter', got '{out_10.monitoring_status}'"
    assert out_10.trajectory.trajectory == "initial_encounter", f"Test 10 failed: expected 'initial_encounter', got '{out_10.trajectory.trajectory}'"
    assert out_10.risk_comparison.risk_trend == "unknown"
    print("TEST 10 (Initial Encounter Clean Baseline): PASS")

    print("=" * 80)
    print("ALL 10 PHASE 5 DIRECT VALIDATION TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase5_tests()
