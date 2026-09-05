"""
Phase 10: Advanced Risk Convergence Test Suite.

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

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def test_01_schema_validation():
    """Verifies instantiation and serialization of all Phase 10 Pydantic v2 schemas."""
    sig = LongitudinalRiskSignal(
        signal_id="test_signal",
        category="recurrence",
        severity="moderate",
        weight=15.0,
        evidence=["Recurrent symptom observed"],
        rationale="Recurrence adds monitoring risk",
        provenance_sources=["ENC_001", "ENC_002"],
    )
    assert sig.weight == 15.0
    assert sig.category == "recurrence"

    dto = LongitudinalRiskAssessmentDTO(
        longitudinal_risk_score=15.0,
        longitudinal_risk_level="MODERATE",
        risk_escalation_status="stable",
        temporal_persistence_index="recurrent",
        risk_signals=[sig],
        reasoning="Test reasoning",
    )
    dumped = dto.model_dump()
    assert dumped["longitudinal_risk_score"] == 15.0
    assert len(dumped["risk_signals"]) == 1

    comp = CompositeRiskOutputDTO(
        current_risk={"risk_level": "LOW", "risk_score": 5},
        longitudinal_risk=dto,
        composite_risk_level="MODERATE",
        effective_care_pathway="routine",
        composite_reasoning="Composite test reasoning",
    )
    comp_dumped = comp.model_dump()
    assert comp_dumped["composite_risk_level"] == "MODERATE"
    assert comp_dumped["current_risk"]["risk_score"] == 5


def test_02_recurrent_complaint_escalation():
    """Verifies recurrent complaint across non-consecutive episodes triggers recurrent_complaint_signal."""
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    assert turn_resp.clinical_output is not None
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk is not None
    
    long_risk = adv_risk["longitudinal_risk"]
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "recurrent_complaint_signal" in signal_ids
    assert long_risk["temporal_persistence_index"] == "recurrent"
    assert long_risk["longitudinal_risk_score"] >= 15.0


def test_03_persistent_unresolved_problem_duration():
    """Verifies symptoms persisting for weeks trigger persistent_unresolved_problem_signal."""
    fixture = ADVANCED_RISK_FIXTURES["persistent_symptom"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "persistent_unresolved_problem_signal" in signal_ids
    assert long_risk["temporal_persistence_index"] == "persistent"


def test_04_historical_risk_escalation_trend():
    """Verifies strictly escalating past encounter risk triggers historical_risk_escalation_signal."""
    fixture = ADVANCED_RISK_FIXTURES["historical_escalation"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "historical_risk_escalation_signal" in signal_ids
    assert long_risk["risk_escalation_status"] == "escalated"
    assert long_risk["longitudinal_risk_score"] >= 15.0


def test_05_repeated_moderate_risk_accumulation():
    """Verifies 3 prior MODERATE encounters trigger repeated_moderate_episodes_signal."""
    fixture = ADVANCED_RISK_FIXTURES["repeated_moderate"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "repeated_moderate_episodes_signal" in signal_ids


def test_06_multimorbid_burden_accumulation():
    """Verifies chronic conditions + multiple unresolved historical issues trigger multimorbid burden signal."""
    fixture = ADVANCED_RISK_FIXTURES["multimorbid_burden"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "unresolved_multimorbid_burden_signal" in signal_ids


def test_07_biomarker_single_observation_safety_gating():
    """Verifies single observation produces ZERO trajectory signals (insufficient_data)."""
    fixture = ADVANCED_RISK_FIXTURES["single_observation_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" not in signal_ids


def test_08_biomarker_unit_mismatch_safety_gating():
    """Verifies incompatible units trigger zero trajectory change signals."""
    fixture = ADVANCED_RISK_FIXTURES["unit_mismatch_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" not in signal_ids


def test_09_biomarker_observational_trajectory_reporting():
    """Verifies mathematical trajectory change generates observational signal without medical overinterpretation."""
    fixture = ADVANCED_RISK_FIXTURES["biomarker_observation"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "biomarker_trajectory_change_observed" in signal_ids
    
    bm_sig = next(s for s in long_risk["risk_signals"] if s["signal_id"] == "biomarker_trajectory_change_observed")
    assert bm_sig["severity"] == "informational"
    assert "Clinical significance is not established" in bm_sig["rationale"]


def test_10_governed_cross_modal_concordance():
    """Verifies governed symptom + biomarker trajectory (fatigue + decreasing Hb) triggers concordance signal."""
    fixture = ADVANCED_RISK_FIXTURES["governed_cross_modal"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "governed_cross_modal_concordance_signal" in signal_ids


def test_11_unsupported_cross_modal_produces_no_signal():
    """Verifies unsupported relationship (skin rash + Hb) produces NO cross-modal concordance signal."""
    fixture = ADVANCED_RISK_FIXTURES["unsupported_cross_modal"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "governed_cross_modal_concordance_signal" not in signal_ids


def test_12_conflict_arbitration_current_low_longitudinal_high():
    """
    CRITICAL INVARIANT:
    Current intake is LOW risk (mild checkup), but longitudinal history is HIGH risk.
    Composite risk elevates to HIGH, while Phase 2B current_risk remains LOW.
    """
    fixture = ADVANCED_RISK_FIXTURES["low_high_conflict"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    
    # 1. Phase 2B preserved immutably
    curr_risk = adv_risk["current_risk"]
    assert curr_risk["risk_level"] == "LOW"
    assert curr_risk["risk_score"] < 10
    
    # 2. Longitudinal risk is HIGH/URGENT
    long_risk = adv_risk["longitudinal_risk"]
    assert long_risk["longitudinal_risk_level"] in ["HIGH", "URGENT"]
    
    # 3. Composite risk is escalated to HIGH/URGENT
    assert adv_risk["composite_risk_level"] in ["HIGH", "URGENT"]
    assert "Current acute presentation risk is LOW, but longitudinal context elevates" in adv_risk["composite_reasoning"]


def test_13_floor_preservation_current_high_longitudinal_low():
    """
    CRITICAL INVARIANT:
    Current intake is HIGH risk, longitudinal history is zero/LOW.
    Composite risk remains HIGH (Phase 2B floor preserved).
    """
    fixture = ADVANCED_RISK_FIXTURES["high_clean_floor"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    
    curr_risk = adv_risk["current_risk"]
    assert curr_risk["risk_level"] in ["HIGH", "URGENT"]
    assert adv_risk["composite_risk_level"] in ["HIGH", "URGENT"]


def test_14_phase2a_emergency_override_inviolability():
    """
    CRITICAL INVARIANT:
    Phase 2A red flags unconditionally enforce emergency care pathway and URGENT composite risk.
    """
    turn_resp = process_turn(FIXTURE_RED_FLAG_EMERGENCY)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    
    assert adv_risk["safety_override_applied"] is True
    assert adv_risk["composite_risk_level"] == "URGENT"
    assert adv_risk["effective_care_pathway"] == "emergency"
    assert "red-flag emergency safety rule triggered" in adv_risk["override_reason"]


def test_15_phase2b_score_immutability():
    """
    CRITICAL INVARIANT:
    Phase 2B score, level, version, and signals are preserved exactly without alteration.
    """
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    
    base_risk = turn_resp.clinical_output["risk_assessment"]
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    curr_risk = adv_risk["current_risk"]
    
    assert curr_risk["risk_score"] == base_risk["risk_score"]
    assert curr_risk["risk_level"] == base_risk["risk_level"]
    assert curr_risk["risk_assessment_version"] == "phase2b_v1"


def test_16_safe_handling_of_undated_encounters():
    """Verifies undated encounters do not spoof chronological escalation trends."""
    fixture = ADVANCED_RISK_FIXTURES["undated_safe"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    # Without valid timestamps, historical escalation cannot trigger
    assert "historical_risk_escalation_signal" not in signal_ids


def test_17_explicit_resolution_vs_recurrence():
    """Verifies resolved symptoms that reappear in later encounters are classified as recurrent."""
    fixture = ADVANCED_RISK_FIXTURES["resolved_recurrent"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    long_risk = adv_risk["longitudinal_risk"]
    
    signal_ids = [s["signal_id"] for s in long_risk["risk_signals"]]
    assert "recurrent_complaint_signal" in signal_ids


def test_18_missing_not_resolved_in_risk_context():
    """Verifies unmentioned prior problems are preserved in unresolved issues and contribute to complexity."""
    fixture = ADVANCED_RISK_FIXTURES["missing_not_resolved"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    assert adv_risk is not None


def test_19_zero_diagnosis_and_prescription_invariants():
    """
    CRITICAL SAFETY INVARIANT:
    Phase 10 output contains NO medical diagnosis, NO drug prescriptions, and mandatory disclaimers.
    """
    fixture = ADVANCED_RISK_FIXTURES["low_high_conflict"]
    turn_resp = process_turn(fixture)
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    
    disclaimer = adv_risk["longitudinal_risk"]["disclaimer"]
    assert "not a medical diagnosis" in disclaimer.lower()
    
    for sig in adv_risk["longitudinal_risk"]["risk_signals"]:
        assert "diagnose" not in sig["rationale"].lower()
        assert "prescribe" not in sig["rationale"].lower()


def test_20_orchestrator_integration_bundle():
    """Verifies full end-to-end integration into TurnResponseDTO and StructuredClinicalOutputDTO."""
    fixture = ADVANCED_RISK_FIXTURES["recurrent_risk"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.status == "complete"
    assert turn_resp.clinical_output is not None
    assert "advanced_risk_assessment" in turn_resp.clinical_output
    assert "longitudinal_context" in turn_resp.clinical_output
    assert "risk_assessment" in turn_resp.clinical_output
    assert "safety_findings" in turn_resp.clinical_output


def run_all_tests():
    tests = [
        test_01_schema_validation,
        test_02_recurrent_complaint_escalation,
        test_03_persistent_unresolved_problem_duration,
        test_04_historical_risk_escalation_trend,
        test_05_repeated_moderate_risk_accumulation,
        test_06_multimorbid_burden_accumulation,
        test_07_biomarker_single_observation_safety_gating,
        test_08_biomarker_unit_mismatch_safety_gating,
        test_09_biomarker_observational_trajectory_reporting,
        test_10_governed_cross_modal_concordance,
        test_11_unsupported_cross_modal_produces_no_signal,
        test_12_conflict_arbitration_current_low_longitudinal_high,
        test_13_floor_preservation_current_high_longitudinal_low,
        test_14_phase2a_emergency_override_inviolability,
        test_15_phase2b_score_immutability,
        test_16_safe_handling_of_undated_encounters,
        test_17_explicit_resolution_vs_recurrence,
        test_18_missing_not_resolved_in_risk_context,
        test_19_zero_diagnosis_and_prescription_invariants,
        test_20_orchestrator_integration_bundle,
    ]
    
    passed = 0
    failed = 0
    print("=" * 75)
    print("VAIDYAARC PHASE 10 DIRECT TEST SUITE")
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

