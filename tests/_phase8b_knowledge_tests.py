"""
Phase 8B: Controlled Ayurveda Knowledge System Test Suite.

Tests the repository, retriever, safety gate, recommendation engine,
and orchestrator integration.
"""

import sys
import os
from pathlib import Path

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ayurveda_knowledge_schema import (
    AuthorityLevel,
    RecordType,
    AyurvedaEligibilityStatus,
    AyurvedaKnowledgeRecord,
    AyurvedaRecommendationOutput,
)
from app.ayurveda_knowledge_repository import get_ayurveda_repository
from app.ayurveda_retriever import get_ayurveda_retriever
from app.ayurveda_safety_gate import evaluate_safety_and_eligibility
from app.ayurveda_recommendation import evaluate_ayurveda_recommendations
from app.orchestrator import process_turn
from tests.fixtures.ayurveda_remedy_fixtures import AYURVEDA_FIXTURES


def run_test(name: str, fn):
    try:
        fn()
        print(f"PASS: {name}")
        return True
    except Exception as e:
        print(f"FAIL: {name} -> {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repository_singleton_and_loading():
    repo = get_ayurveda_repository()
    records = repo.get_all_records()
    assert len(records) > 0, "Repository should load records"


def test_record_types_present():
    repo = get_ayurveda_repository()
    home_remedies = repo.get_records_by_type(RecordType.HOME_REMEDY)
    formulations = repo.get_records_by_type(RecordType.PHARMACOPOEIAL_FORMULATION)
    literature = repo.get_records_by_type(RecordType.SECONDARY_LITERATURE)
    assert len(home_remedies) > 0, "Should contain home remedies"
    assert len(formulations) > 0, "Should contain pharmacopoeial formulations"
    assert len(literature) > 0, "Should contain secondary literature"


def test_source_attribution_integrity():
    repo = get_ayurveda_repository()
    for rec in repo.get_all_records():
        assert rec.provenance.source_id in {"SRC_CCRAS_HOME_REMEDIES_2005", "SRC_API_PART2_VOL2_2008", "SRC_ECAM_REVIEW_2013"}
        assert rec.provenance.page is not None
        assert len(rec.provenance.excerpt) > 5


def test_cough_retrieval():
    retriever = get_ayurveda_retriever()
    candidates = retriever.retrieve_candidates(chief_complaint="dry cough", limit=5)
    assert len(candidates) > 0
    assert any("cough" in c.matched_symptom.lower() or "kasa" in c.matched_symptom.lower() for c in candidates)


def test_indigestion_retrieval():
    retriever = get_ayurveda_retriever()
    candidates = retriever.retrieve_candidates(chief_complaint="indigestion", symptoms=["loss of appetite"], limit=5)
    assert len(candidates) > 0


def test_authority_weighting():
    retriever = get_ayurveda_retriever()
    candidates = retriever.retrieve_candidates(chief_complaint="fever", symptoms=["jwara"], limit=10)
    assert len(candidates) > 0
    top_cand = candidates[0]
    assert top_cand.record.authority_level == AuthorityLevel.PRIMARY_OFFICIAL


def test_emergency_red_flag_blocks_remedy():
    fixture = AYURVEDA_FIXTURES["emergency_blocked"]
    decision = evaluate_safety_and_eligibility(fixture.state_snapshot)
    assert decision.status == AyurvedaEligibilityStatus.BLOCKED
    assert any("emergency" in r.lower() or "immediate" in r.lower() for r in decision.reasons)


def test_high_risk_score_blocks_remedy():
    fixture = AYURVEDA_FIXTURES["high_risk_blocked"]
    decision = evaluate_safety_and_eligibility(fixture.state_snapshot)
    assert decision.status == AyurvedaEligibilityStatus.BLOCKED
    assert any("risk" in r.lower() for r in decision.reasons)


def test_severe_symptom_blocks_remedy():
    fixture = AYURVEDA_FIXTURES["severe_pain_blocked"]
    decision = evaluate_safety_and_eligibility(fixture.state_snapshot)
    assert decision.status == AyurvedaEligibilityStatus.BLOCKED


def test_unknown_pregnancy_requires_review():
    fixture = AYURVEDA_FIXTURES["unknown_pregnancy"]
    state = dict(fixture.state_snapshot)
    state["patient_profile"] = fixture.patient_profile.model_dump()
    decision = evaluate_safety_and_eligibility(state)
    assert decision.status == AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW


def test_mild_cough_eligible_output():
    fixture = AYURVEDA_FIXTURES["mild_cough"]
    output = evaluate_ayurveda_recommendations(fixture.state_snapshot)
    assert output.decision == AyurvedaEligibilityStatus.ELIGIBLE
    assert len(output.recommendations) > 0
    assert output.non_prescription_disclaimer is not None


def test_allergy_filtering():
    fixture = AYURVEDA_FIXTURES["allergy_constraint"]
    state = dict(fixture.state_snapshot)
    state["patient_profile"] = fixture.patient_profile.model_dump()
    output = evaluate_ayurveda_recommendations(state)
    for item in output.recommendations:
        assert "ardraka" not in item.name.lower()
        assert "ginger" not in item.name.lower()
        assert "adrak" not in item.name.lower()


def test_unmapped_symptom_insufficient_info():
    fixture = AYURVEDA_FIXTURES["unmapped_symptom"]
    output = evaluate_ayurveda_recommendations(fixture.state_snapshot)
    assert output.decision == AyurvedaEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(output.recommendations) == 0


def test_turn_response_contains_ayurveda_recommendation():
    fixture = AYURVEDA_FIXTURES["mild_cough"]
    turn_resp = process_turn(fixture)
    assert turn_resp.status == "complete"
    assert turn_resp.clinical_output is not None
    assert "ayurveda_recommendation" in turn_resp.clinical_output
    rec_data = turn_resp.clinical_output["ayurveda_recommendation"]
    assert rec_data["decision"] == "eligible"
    assert len(rec_data["recommendations"]) > 0


def test_phase7_and_phase8b_coexistence():
    fixture = AYURVEDA_FIXTURES["coexistence"]
    turn_resp = process_turn(fixture)
    assert turn_resp.clinical_output is not None
    assert "ayurveda_modern_representation" in turn_resp.clinical_output
    assert "ayurveda_recommendation" in turn_resp.clinical_output


if __name__ == "__main__":
    tests = [
        ("test_repository_singleton_and_loading", test_repository_singleton_and_loading),
        ("test_record_types_present", test_record_types_present),
        ("test_source_attribution_integrity", test_source_attribution_integrity),
        ("test_cough_retrieval", test_cough_retrieval),
        ("test_indigestion_retrieval", test_indigestion_retrieval),
        ("test_authority_weighting", test_authority_weighting),
        ("test_emergency_red_flag_blocks_remedy", test_emergency_red_flag_blocks_remedy),
        ("test_high_risk_score_blocks_remedy", test_high_risk_score_blocks_remedy),
        ("test_severe_symptom_blocks_remedy", test_severe_symptom_blocks_remedy),
        ("test_unknown_pregnancy_requires_review", test_unknown_pregnancy_requires_review),
        ("test_mild_cough_eligible_output", test_mild_cough_eligible_output),
        ("test_allergy_filtering", test_allergy_filtering),
        ("test_unmapped_symptom_insufficient_info", test_unmapped_symptom_insufficient_info),
        ("test_turn_response_contains_ayurveda_recommendation", test_turn_response_contains_ayurveda_recommendation),
        ("test_phase7_and_phase8b_coexistence", test_phase7_and_phase8b_coexistence),
    ]

    print("=" * 70)
    print("PHASE 8B: KNOWLEDGE SYSTEM INTEGRATION TESTS")
    print("=" * 70)
    passed = 0
    failed = 0
    for name, fn in tests:
        if run_test(name, fn):
            passed += 1
        else:
            failed += 1
    print("-" * 70)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)

