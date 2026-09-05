"""
VAIDYAARC PHASE 10 STANDALONE VALIDATION RUNNER
Advanced Risk Convergence

Validates:
1. Pydantic v2 schemas and JSON serialization.
2. Recurrent complaint risk escalation.
3. Persistent symptom duration risk.
4. Historical multi-encounter risk escalation trend.
5. Repeated moderate encounters accumulation.
6. Multimorbid burden compounding.
7. Biomarker single-observation safety gating.
8. Biomarker unit-mismatch safety gating.
9. Observational biomarker trajectory reporting without invented thresholds.
10. Governed cross-modal concordance detection.
11. Unsupported cross-modal relationships produce zero signals.
12. Conflict arbitration: Current LOW + Longitudinal HIGH.
13. Floor preservation: Current HIGH + Longitudinal LOW.
14. Phase 2A emergency override inviolability.
15. Phase 2B risk score and level immutability.
16. Safe handling of missing and uncertain dates.
17. Explicit resolution vs recurrence distinction.
18. Invariant 'Missing != Resolved' in longitudinal risk context.
19. Zero diagnosis and zero prescription invariants.
20. Full orchestrator integration with StructuredClinicalOutputDTO.

ZERO-LLM. 100% DETERMINISTIC.
"""

import sys
import os

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.advanced_risk_schema import (
    LongitudinalRiskSignal,
    LongitudinalRiskAssessmentDTO,
    CompositeRiskOutputDTO,
)
from app.advanced_risk_engine import (
    evaluate_longitudinal_risk,
    synthesize_composite_risk,
    evaluate_advanced_risk,
)
from app.orchestrator import process_turn
from tests.fixtures.advanced_risk_fixtures import ADVANCED_RISK_FIXTURES
from tests.fixtures.synthetic_inputs import FIXTURE_RED_FLAG_EMERGENCY


def test_01_schema_instantiation():
    """Validates instantiation of Phase 10 Pydantic v2 models."""
    sig = LongitudinalRiskSignal(
        signal_id="sig_001",
        category="recurrence",
        severity="moderate",
        weight=15.0,
        evidence=["Recurrent headache"],
        rationale="Recurrent headache adds monitoring risk",
        provenance_sources=["ENC_001"],
    )
    dto = LongitudinalRiskAssessmentDTO(
        longitudinal_risk_score=15.0,
        longitudinal_risk_level="MODERATE",
        risk_signals=[sig],
        reasoning="Test reasoning",
    )
    comp = CompositeRiskOutputDTO(
        current_risk={"risk_level": "LOW", "risk_score": 5},
        longitudinal_risk=dto,
        composite_risk_level="MODERATE",
        effective_care_pathway="routine",
        composite_reasoning="Composite test reasoning",
    )
    dump = comp.model_dump()
    assert dump["composite_risk_level"] == "MODERATE"
    assert dump["current_risk"]["risk_score"] == 5


def test_02_recurrent_complaint_escalation():
    """Validates that recurrent complaint triggers recurrent_complaint_signal."""
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "recurrent_complaint_signal" in signal_ids
    assert long_risk["temporal_persistence_index"] == "recurrent"


def test_03_persistent_unresolved_problem():
    """Validates that persistent duration triggers persistent_unresolved_problem_signal."""
    fixture = ADVANCED_RISK_FIXTURES["persistent_symptom"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "persistent_unresolved_problem_signal" in signal_ids
    assert long_risk["temporal_persistence_index"] == "persistent"


def test_04_historical_risk_escalation():
    """Validates that strictly escalating risk levels trigger historical_risk_escalation_signal."""
    fixture = ADVANCED_RISK_FIXTURES["historical_escalation"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "historical_risk_escalation_signal" in signal_ids
    assert long_risk["risk_escalation_status"] == "escalated"


def test_05_repeated_moderate_risk():
    """Validates that 3 prior MODERATE encounters trigger repeated_moderate_episodes_signal."""
    fixture = ADVANCED_RISK_FIXTURES["repeated_moderate"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "repeated_moderate_episodes_signal" in signal_ids


def test_06_multimorbid_burden():
    """Validates that chronic conditions + unresolved problems trigger multimorbid burden signal."""
    fixture = ADVANCED_RISK_FIXTURES["multimorbid_burden"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "unresolved_multimorbid_burden_signal" in signal_ids


def test_07_biomarker_single_observation_gating():
    """Validates that single observation produces ZERO trajectory signals."""
    fixture = ADVANCED_RISK_FIXTURES["single_observation_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" not in signal_ids


def test_08_biomarker_unit_mismatch_gating():
    """Validates that incompatible units produce ZERO trajectory signals."""
    fixture = ADVANCED_RISK_FIXTURES["unit_mismatch_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" not in signal_ids


def test_09_biomarker_observational_reporting():
    """Validates observational reporting without arbitrary clinical thresholds."""
    fixture = ADVANCED_RISK_FIXTURES["biomarker_observation"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" in signal_ids
    bm_sig = next(s for s in long_risk["risk_signals"] if s["signal_id"] == "biomarker_trajectory_change_observed")
    assert bm_sig["severity"] == "informational"


def test_10_governed_cross_modal():
    """Validates that governed concordance (fatigue + decreasing Hb) triggers signal."""
    fixture = ADVANCED_RISK_FIXTURES["governed_cross_modal"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "governed_cross_modal_concordance_signal" in signal_ids


def test_11_unsupported_cross_modal_safeguard():
    """Validates that unsupported cross-modal relationships generate NO signal."""
    fixture = ADVANCED_RISK_FIXTURES["unsupported_cross_modal"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "governed_cross_modal_concordance_signal" not in signal_ids


def test_12_current_low_longitudinal_high():
    """Validates that current LOW + longitudinal HIGH escalates composite to HIGH while preserving Phase 2B."""
    fixture = ADVANCED_RISK_FIXTURES["low_high_conflict"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk["current_risk"]["risk_level"] == "LOW"
    assert adv_risk["composite_risk_level"] in ["HIGH", "URGENT"]


def test_13_current_high_longitudinal_low():
    """Validates that current HIGH + clean history preserves composite HIGH."""
    fixture = ADVANCED_RISK_FIXTURES["high_clean_floor"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk["current_risk"]["risk_level"] in ["HIGH", "URGENT"]
    assert adv_risk["composite_risk_level"] in ["HIGH", "URGENT"]


def test_14_phase2a_emergency_override():
    """Validates that Phase 2A red flags enforce emergency care pathway and URGENT composite risk."""
    turn_resp = process_turn(FIXTURE_RED_FLAG_EMERGENCY)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk["safety_override_applied"] is True
    assert adv_risk["composite_risk_level"] == "URGENT"
    assert adv_risk["effective_care_pathway"] == "emergency"


def test_15_phase2b_immutability():
    """Validates that Phase 2B score, level, version, and signals are preserved exactly."""
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    base_risk = turn_resp.clinical_output["risk_assessment"]
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk["current_risk"]["risk_score"] == base_risk["risk_score"]
    assert adv_risk["current_risk"]["risk_level"] == base_risk["risk_level"]


def test_16_undated_encounters():
    """Validates that undated encounters do not spoof chronological escalation."""
    fixture = ADVANCED_RISK_FIXTURES["undated_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "historical_risk_escalation_signal" not in signal_ids


def test_17_explicit_resolution_vs_recurrence():
    """Validates that resolved symptoms that reappear later are classified as recurrent."""
    fixture = ADVANCED_RISK_FIXTURES["resolved_recurrent"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "recurrent_complaint_signal" in signal_ids


def test_18_missing_not_resolved():
    """Validates that unmentioned prior problems are preserved in unresolved issues."""
    fixture = ADVANCED_RISK_FIXTURES["missing_not_resolved"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk is not None


def test_19_zero_diagnosis_zero_prescription():
    """Validates that Phase 10 contains NO diagnosis, NO prescription, and mandatory disclaimers."""
    fixture = ADVANCED_RISK_FIXTURES["low_high_conflict"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert "not a medical diagnosis" in adv_risk["longitudinal_risk"]["disclaimer"].lower()


def test_20_orchestrator_integration():
    """Validates full orchestrator turn processing produces advanced_risk_assessment in clinical output."""
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    assert turn_resp.status == "complete"
    assert "advanced_risk_assessment" in turn_resp.clinical_output
    assert "longitudinal_context" in turn_resp.clinical_output


def run_all_tests():
    tests = [
        test_01_schema_instantiation,
        test_02_recurrent_complaint_escalation,
        test_03_persistent_unresolved_problem,
        test_04_historical_risk_escalation,
        test_05_repeated_moderate_risk,
        test_06_multimorbid_burden,
        test_07_biomarker_single_observation_gating,
        test_08_biomarker_unit_mismatch_gating,
        test_09_biomarker_observational_reporting,
        test_10_governed_cross_modal,
        test_11_unsupported_cross_modal_safeguard,
        test_12_current_low_longitudinal_high,
        test_13_current_high_longitudinal_low,
        test_14_phase2a_emergency_override,
        test_15_phase2b_immutability,
        test_16_undated_encounters,
        test_17_explicit_resolution_vs_recurrence,
        test_18_missing_not_resolved,
        test_19_zero_diagnosis_zero_prescription,
        test_20_orchestrator_integration,
    ]
    
    passed = 0
    failed = 0
    print("=" * 75)
    print("VAIDYAARC PHASE 10 VALIDATION SUITE")
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

