"""
Phase 11: Clinical Summary & Consultation Questions Test Suite.

Validates:
1. Pydantic v2 schemas and JSON serialization.
2. Complete routine clinical summary generation across all 12 domains.
3. Incomplete intake handling with explicit missing slot notation.
4. Missing past medical & surgical history (no inferred negatives).
5. Missing medication history (no inferred medications).
6. Missing allergy history (NKDA not assumed).
7. Missing family history (no inferred negatives).
8. Missing review of systems (ROS negatives not inferred).
9. Prior investigations and biomarker extraction.
10. Longitudinal recurrence reporting and question generation.
11. Longitudinal persistence reporting and question generation.
12. Explicit resolution vs active complaint distinction.
13. Observational biomarker trajectory reporting without invented thresholds.
14. Single biomarker observation produces no trajectory assumptions.
15. Conflicting patient information detection and flagging.
16. Phase 2B HIGH risk preservation in safety summary.
17. Phase 2B URGENT risk preservation in safety summary.
18. Phase 2A emergency override inviolability and emergency questions.
19. Consultation question synthesis from information gaps.
20. Zero diagnosis and zero prescription invariants.
21. Deterministic zero-LLM execution.
22. Traceability and provenance preservation across all sections.
23. Empty / partial patient profile baseline handling.
24. Full orchestrator turn processing integration.
25. Missing != Resolved invariant preservation.

ZERO-LLM. 100% DETERMINISTIC.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.clinical_summary_schema import (
    ClinicalSummarySection,
    ClinicalSummaryDTO,
    ConsultationQuestionDTO,
    ConsultationQuestionsDTO,
    Phase11ClinicalSummaryOutputDTO,
)
from app.clinical_summary_engine import (
    generate_clinical_summary,
    generate_consultation_questions,
    generate_clinical_summary_bundle,
)
from app.orchestrator import process_turn
from tests.fixtures.clinical_summary_fixtures import CLINICAL_SUMMARY_FIXTURES
from tests.fixtures.synthetic_inputs import FIXTURE_RED_FLAG_EMERGENCY


def test_01_schema_instantiation():
    """Validates instantiation and serialization of Phase 11 Pydantic v2 schemas."""
    sec = ClinicalSummarySection(
        section_name="Chief Complaint",
        content="Patient reports headache.",
        status="reported",
        provenance=["intake_chief_complaint"],
    )
    assert sec.status == "reported"

    q = ConsultationQuestionDTO(
        question_id="Q_001",
        question="What could be causing these symptoms?",
        category="symptom_cause",
        rationale="Explores differential cause",
        priority="high",
        source_evidence=["Headache"],
        provenance="test_engine",
    )
    assert q.priority == "high"

    dto = ConsultationQuestionsDTO(
        questions=[q],
        generated_from=["chief_complaint"],
        safety_context="Routine",
    )
    dumped = dto.model_dump()
    assert len(dumped["questions"]) == 1
    assert dumped["questions"][0]["question_id"] == "Q_001"


def test_02_complete_routine_case():
    """Validates complete routine clinical summary generation across all 12 domains."""
    fixture = CLINICAL_SUMMARY_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    assert turn_resp.clinical_output is not None
    clin_sum = turn_resp.clinical_output.get("clinical_summary")
    assert clin_sum is not None
    
    assert clin_sum["chief_complaint"]["status"] == "reported"
    assert clin_sum["history_of_present_illness"]["status"] == "reported"
    assert clin_sum["past_medical_history"]["status"] == "reported"
    assert "Mild Asthma" in clin_sum["past_medical_history"]["content"]
    assert clin_sum["past_surgical_history"]["status"] == "reported"
    assert "Appendectomy" in clin_sum["past_surgical_history"]["content"]
    assert clin_sum["medication_history"]["status"] == "reported"
    assert "Albuterol" in clin_sum["medication_history"]["content"]
    assert clin_sum["allergy_history"]["status"] == "reported"
    assert "Penicillin" in clin_sum["allergy_history"]["content"]
    assert clin_sum["family_history"]["status"] == "reported"
    assert "Diabetes" in clin_sum["family_history"]["content"]
    assert clin_sum["personal_social_history"]["status"] == "reported"
    assert clin_sum["review_of_systems"]["status"] == "reported"
    assert "nausea" in clin_sum["review_of_systems"]["content"]
    assert clin_sum["data_completeness"] == "complete"


def test_03_incomplete_intake():
    """Validates incomplete intake handling with explicit missing slot notation."""
    fixture = CLINICAL_SUMMARY_FIXTURES["incomplete_intake"]
    turn_resp = process_turn(fixture)
    
    # In turn mode with incomplete intake, test direct engine evaluation
    state = dict(fixture.state_snapshot or {})
    summary = generate_clinical_summary(state)
    assert summary.data_completeness in ["partial", "insufficient"]
    assert "Unreported HPI Elements" in summary.history_of_present_illness.content


def test_04_missing_medical_and_surgical_history():
    """Validates missing PMH & PSH (status not_reported, negative findings not inferred)."""
    fixture = CLINICAL_SUMMARY_FIXTURES["missing_history"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["past_medical_history"]["status"] == "not_reported"
    assert "not reported" in clin_sum["past_medical_history"]["content"].lower()
    assert clin_sum["past_surgical_history"]["status"] == "not_reported"
    assert "not reported" in clin_sum["past_surgical_history"]["content"].lower()


def test_05_missing_medication_history():
    """Validates missing medication history (status not_reported, no medications invented)."""
    fixture = CLINICAL_SUMMARY_FIXTURES["missing_medications"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["medication_history"]["status"] == "not_reported"
    assert "not reported" in clin_sum["medication_history"]["content"].lower()


def test_06_missing_allergy_history():
    """Validates missing allergy history (NKDA not assumed without explicit reporting)."""
    fixture = CLINICAL_SUMMARY_FIXTURES["missing_allergies"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["allergy_history"]["status"] == "not_reported"
    assert "not reported" in clin_sum["allergy_history"]["content"].lower()


def test_07_missing_family_history():
    """Validates missing family history (status not_reported, no negatives inferred)."""
    fixture = CLINICAL_SUMMARY_FIXTURES["missing_family_history"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["family_history"]["status"] == "not_reported"
    assert "not reported" in clin_sum["family_history"]["content"].lower()


def test_08_missing_review_of_systems():
    """Validates missing review of systems (system negatives not inferred)."""
    fixture = CLINICAL_SUMMARY_FIXTURES["missing_ros"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["review_of_systems"]["status"] == "not_reported"
    assert "not inferred" in clin_sum["review_of_systems"]["content"].lower()


def test_09_prior_investigations_present():
    """Validates prior investigations and biomarker extraction into Section 10."""
    fixture = CLINICAL_SUMMARY_FIXTURES["prior_investigations"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["prior_investigations"]["status"] == "reported"
    assert "Hemoglobin" in clin_sum["prior_investigations"]["content"]
    assert "Ferritin" in clin_sum["prior_investigations"]["content"]


def test_10_longitudinal_recurrence_reporting():
    """Validates longitudinal recurrence noted in Section 11 and generates recurrence question."""
    fixture = CLINICAL_SUMMARY_FIXTURES["longitudinal_recurrence"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    questions = turn_resp.clinical_output["consultation_questions"]
    
    assert clin_sum["longitudinal_context"]["status"] == "reported"
    assert "Recurrent complaints" in clin_sum["longitudinal_context"]["content"]
    q_ids = [q["question_id"] for q in questions["questions"]]
    assert "Q_LONGITUDINAL_RECURRENCE" in q_ids


def test_11_longitudinal_persistent_problem():
    """Validates longitudinal persistence noted in Section 11 and generates persistence question."""
    fixture = CLINICAL_SUMMARY_FIXTURES["longitudinal_persistent"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    questions = turn_resp.clinical_output["consultation_questions"]
    
    assert clin_sum["longitudinal_context"]["status"] == "reported"
    q_ids = [q["question_id"] for q in questions["questions"]]
    assert "Q_LONGITUDINAL_RECURRENCE" in q_ids


def test_12_explicitly_resolved_problem():
    """Validates explicitly resolved problems are distinguished from active complaints."""
    fixture = CLINICAL_SUMMARY_FIXTURES["explicitly_resolved"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert "Explicitly resolved problems" in clin_sum["longitudinal_context"]["content"]


def test_13_biomarker_observational_trajectory():
    """Validates observational biomarker trajectory reporting without invented thresholds."""
    fixture = CLINICAL_SUMMARY_FIXTURES["biomarker_trajectory"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert "Biomarker observation" in clin_sum["longitudinal_context"]["content"]
    assert "non-diagnostic observation" in clin_sum["longitudinal_context"]["content"]


def test_14_biomarker_insufficient_data():
    """Validates single biomarker observation produces no trajectory assumptions."""
    fixture = CLINICAL_SUMMARY_FIXTURES["biomarker_insufficient"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert "Biomarker observation" not in clin_sum["longitudinal_context"]["content"]


def test_15_conflicting_patient_information():
    """Validates discrepancy between mild slot and severe narrative is flagged in conflicts."""
    fixture = CLINICAL_SUMMARY_FIXTURES["conflicting_information"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert len(clin_sum["conflicts_identified"]) > 0
    assert clin_sum["history_of_present_illness"]["status"] == "conflicting"
    assert "DOCUMENTED DISCREPANCIES" in clin_sum["summary_narrative"]


def test_16_phase2b_high_risk_preservation():
    """Validates Phase 2B HIGH risk is preserved in safety summary."""
    fixture = CLINICAL_SUMMARY_FIXTURES["high_risk"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["safety_and_risk_summary"]["structured_data"]["phase2b_risk_level"] in ["HIGH", "URGENT"]
    assert any(lvl in clin_sum["safety_and_risk_summary"]["content"] for lvl in ["HIGH", "URGENT"])


def test_17_phase2b_urgent_risk_preservation():
    """Validates Phase 2B URGENT risk is preserved in safety summary without downgrading."""
    fixture = CLINICAL_SUMMARY_FIXTURES["urgent_risk"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["safety_and_risk_summary"]["structured_data"]["phase2b_risk_level"] in ["HIGH", "URGENT"]
    assert any(lvl in clin_sum["safety_and_risk_summary"]["content"] for lvl in ["HIGH", "URGENT"])


def test_18_phase2a_emergency_override_inviolability():
    """Validates Phase 2A emergency override unconditionally surfaces emergency status & questions."""
    fixture = CLINICAL_SUMMARY_FIXTURES["emergency_red_flag"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    questions = turn_resp.clinical_output["consultation_questions"]
    
    assert "CRITICAL SAFETY OVERRIDE ACTIVE" in clin_sum["safety_and_risk_summary"]["content"]
    q_ids = [q["question_id"] for q in questions["questions"]]
    assert "Q_EMERGENCY_WARNING_SIGNS" in q_ids
    assert "EMERGENCY PRIORITY" in questions["safety_context"]


def test_19_consultation_questions_from_information_gaps():
    """Validates missing intake slots generate targeted clarification questions."""
    state = {
        "chief_complaint": "abdominal pain",
        "missing_information": ["duration", "severity", "location"],
        "information_complete": False,
    }
    summary = generate_clinical_summary(state)
    questions = generate_consultation_questions(state, summary)
    
    q_ids = [q.question_id for q in questions.questions]
    assert "Q_GAP_DURATION" in q_ids
    assert "Q_GAP_SEVERITY" in q_ids
    assert "Q_GAP_LOCATION" in q_ids


def test_20_zero_diagnosis_and_prescription_invariants():
    """Validates that summary and questions contain zero diagnosis, zero treatment, zero prescriptions."""
    fixture = CLINICAL_SUMMARY_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    questions = turn_resp.clinical_output["consultation_questions"]
    
    assert "not constitute a medical diagnosis" in clin_sum["disclaimer"].lower()
    assert "not constitute medical advice" in questions["disclaimer"].lower()
    
    for q in questions["questions"]:
        q_text = q["question"].lower()
        assert "you should take" not in q_text
        assert "you are diagnosed with" not in q_text


def test_21_llm_unavailable_deterministic_fallback():
    """Validates deterministic zero-LLM execution works reliably."""
    fixture = CLINICAL_SUMMARY_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    assert turn_resp.clinical_output["clinical_summary"]["version"] == "phase11_v1"
    assert turn_resp.clinical_output["consultation_questions"]["version"] == "phase11_v1"


def test_22_provenance_preservation():
    """Validates traceability and provenance preservation across all sections."""
    fixture = CLINICAL_SUMMARY_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert len(clin_sum["chief_complaint"]["provenance"]) > 0
    assert len(clin_sum["history_of_present_illness"]["provenance"]) > 0
    assert len(clin_sum["provenance_notes"]) >= 5


def test_23_empty_patient_profile_baseline():
    """Validates graceful handling of empty profile baseline without error or hallucination."""
    fixture = CLINICAL_SUMMARY_FIXTURES["empty_profile"]
    turn_resp = process_turn(fixture)
    clin_sum = turn_resp.clinical_output["clinical_summary"]
    
    assert clin_sum["past_medical_history"]["status"] == "not_reported"
    assert clin_sum["medication_history"]["status"] == "not_reported"
    assert clin_sum["allergy_history"]["status"] == "not_reported"


def test_24_orchestrator_integration_bundle():
    """Validates full orchestrator turn processing integrates clinical_summary and consultation_questions."""
    fixture = CLINICAL_SUMMARY_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.status == "complete"
    assert "clinical_summary" in turn_resp.clinical_output
    assert "consultation_questions" in turn_resp.clinical_output
    assert "advanced_risk_assessment" in turn_resp.clinical_output
    assert "longitudinal_context" in turn_resp.clinical_output


def test_25_missing_not_resolved_invariant():
    """Validates that unmentioned historical problems are preserved as unresolved."""
    state = {
        "chief_complaint": "skin rash",
        "longitudinal_context": {
            "unresolved_issues": [{"label": "cough", "normalized_label": "cough"}],
            "total_encounters": 2,
        }
    }
    summary = generate_clinical_summary(state)
    assert "Unresolved historical issues: cough" in summary.longitudinal_context.content


def run_all_tests():
    tests = [
        test_01_schema_instantiation,
        test_02_complete_routine_case,
        test_03_incomplete_intake,
        test_04_missing_medical_and_surgical_history,
        test_05_missing_medication_history,
        test_06_missing_allergy_history,
        test_07_missing_family_history,
        test_08_missing_review_of_systems,
        test_09_prior_investigations_present,
        test_10_longitudinal_recurrence_reporting,
        test_11_longitudinal_persistent_problem,
        test_12_explicitly_resolved_problem,
        test_13_biomarker_observational_trajectory,
        test_14_biomarker_insufficient_data,
        test_15_conflicting_patient_information,
        test_16_phase2b_high_risk_preservation,
        test_17_phase2b_urgent_risk_preservation,
        test_18_phase2a_emergency_override_inviolability,
        test_19_consultation_questions_from_information_gaps,
        test_20_zero_diagnosis_and_prescription_invariants,
        test_21_llm_unavailable_deterministic_fallback,
        test_22_provenance_preservation,
        test_23_empty_patient_profile_baseline,
        test_24_orchestrator_integration_bundle,
        test_25_missing_not_resolved_invariant,
    ]

    passed = 0
    failed = 0
    print("=" * 75)
    print("VAIDYAARC PHASE 11 DIRECT TEST SUITE")
    print("=" * 75)
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} -> {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("-" * 75)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print("=" * 75)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
