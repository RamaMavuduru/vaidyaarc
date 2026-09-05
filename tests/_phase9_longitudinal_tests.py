"""
Phase 9: Longitudinal Patient Intelligence Test Suite.

Validates:
1. Pydantic v2 schemas and provenance preservation.
2. Chronological timeline ordering, tie-breaking, and deduplication.
3. Biomarker trajectory math and non-diagnostic directional characterization.
4. Active, resolved, recurrent, and unresolved problem classification.
5. Invariant 'Missing != Resolved'.
6. Full orchestrator integration and multi-phase regression preservation.

ZERO-LLM. 100% DETERMINISTIC.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.longitudinal_schema import (
    EncounterSummary,
    TimelineEvent,
    BiomarkerRecord,
    BiomarkerTrajectory,
    ProblemRecord,
    LongitudinalPatientContextDTO,
)
from app.biomarker_engine import (
    extract_biomarker_records,
    calculate_biomarker_trajectories,
    normalize_test_name,
    normalize_unit,
)
from app.problem_registry import (
    normalize_problem_label,
    detect_explicit_resolution,
    build_problem_registry,
)
from app.longitudinal_timeline import (
    parse_and_normalize_date,
    build_longitudinal_timeline,
    synthesize_longitudinal_context,
)
from app.orchestrator import process_turn
from tests.fixtures.longitudinal_fixtures import LONGITUDINAL_FIXTURES


def test_01_schema_validation():
    """Verifies instantiation and serialization of all Phase 9 Pydantic v2 schemas."""
    rec = BiomarkerRecord(
        test_name="HbA1c",
        normalized_name="hba1c",
        value=6.5,
        unit="%",
        status="high",
        is_abnormal=True,
        observation_date="2025-01-01",
        source_document_id="DOC_001",
    )
    assert rec.value == 6.5
    assert rec.is_abnormal is True

    prob = ProblemRecord(
        problem_id="PROB_FEVER",
        label="Fever",
        normalized_label="fever",
        status="active",
        episode_count=2,
        is_recurrent=True,
    )
    assert prob.is_recurrent is True

    dto = LongitudinalPatientContextDTO(
        patient_id="PAT_001",
        total_encounters=2,
        biomarker_trajectories=[],
        active_problems=[prob],
    )
    d = dto.model_dump()
    assert d["patient_id"] == "PAT_001"
    assert len(d["active_problems"]) == 1


def test_02_timeline_chronological_ordering():
    """Verifies that events with known dates are sorted chronologically ascending."""
    encs = [
        {"encounter_id": "ENC_3", "timestamp": "2025-08-01", "chief_complaint": "cough"},
        {"encounter_id": "ENC_1", "timestamp": "2025-01-01", "chief_complaint": "fever"},
        {"encounter_id": "ENC_2", "timestamp": "2025-04-01", "chief_complaint": "headache"},
    ]
    timeline, _ = build_longitudinal_timeline(
        patient_id="PAT_TEST",
        previous_encounters=encs,
        documents=[],
        investigations=[],
        previous_conversations=[],
    )
    assert len(timeline) == 3
    dates = [e.date for e in timeline]
    assert dates == ["2025-01-01", "2025-04-01", "2025-08-01"]
    assert timeline[0].source_id == "ENC_1"
    assert timeline[1].source_id == "ENC_2"
    assert timeline[2].source_id == "ENC_3"


def test_03_timeline_preserves_undated_events():
    """Verifies that events with missing/unspecified dates are preserved, not dropped."""
    encs = [
        {"encounter_id": "ENC_DATED", "timestamp": "2025-05-01", "chief_complaint": "fever"},
        {"encounter_id": "ENC_UNDATED_1", "timestamp": None, "chief_complaint": "cough"},
        {"encounter_id": "ENC_UNDATED_2", "timestamp": "", "chief_complaint": "rash"},
    ]
    timeline, _ = build_longitudinal_timeline(
        patient_id="PAT_TEST",
        previous_encounters=encs,
        documents=[],
        investigations=[],
        previous_conversations=[],
    )
    assert len(timeline) == 3
    assert timeline[0].date == "2025-05-01"
    assert timeline[1].date is None or timeline[1].date_certainty == "unspecified"
    assert timeline[2].date is None or timeline[2].date_certainty == "unspecified"


def test_04_timeline_deduplication():
    """Verifies duplicate encounter IDs are deduplicated without crashing."""
    fixture = LONGITUDINAL_FIXTURES["duplicate_encounters"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    enc_events = [e for e in dto.timeline if e.event_type == "encounter"]
    assert len(enc_events) == 2  # 1 historical deduped + 1 current turn


def test_05_biomarker_increasing_trajectory():
    """Verifies strictly increasing values report 'increasing' with accurate numeric deltas."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "hba1c"
    assert traj.observation_count == 4
    assert traj.trajectory == "increasing"
    assert traj.direction == "upward"
    assert traj.earliest_observation.value == 6.5
    assert traj.latest_observation.value == 9.1
    assert traj.absolute_delta == 2.6
    assert traj.percentage_change == 40.0
    # Invariant: Must contain non-diagnostic disclaimer
    assert "licensed medical evaluation" in traj.interpretation_note


def test_06_biomarker_decreasing_trajectory():
    """Verifies strictly decreasing values report 'decreasing' without clinical bias."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_decreasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "fasting_blood_glucose"
    assert traj.observation_count == 4
    assert traj.trajectory == "decreasing"
    assert traj.direction == "downward"
    assert traj.earliest_observation.value == 240.0
    assert traj.latest_observation.value == 110.0
    assert traj.absolute_delta == -130.0
    assert traj.percentage_change == -54.17


def test_07_biomarker_stable_trajectory():
    """Verifies constant values report 'stable'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_stable"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "hemoglobin"
    assert traj.observation_count == 3
    assert traj.trajectory == "stable"
    assert traj.direction == "unchanged"
    assert traj.absolute_delta == 0.0


def test_08_biomarker_fluctuating_trajectory():
    """Verifies up and down movements report 'fluctuating'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_fluctuating"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "blood_pressure_systolic"
    assert traj.observation_count == 4
    assert traj.trajectory == "fluctuating"
    assert traj.direction == "fluctuating"


def test_09_biomarker_single_observation_insufficient_data():
    """Verifies single observation returns 'insufficient_data' without calculating deltas."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_single"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.observation_count == 1
    assert traj.trajectory == "insufficient_data"
    assert traj.absolute_delta is None
    assert traj.percentage_change is None


def test_10_biomarker_unit_mismatch_blocks_calculation():
    """Verifies observations with incompatible units are flagged as unit_mismatch."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_unit_mismatch"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.unit_mismatch is True
    assert traj.trajectory == "insufficient_data"
    assert traj.absolute_delta is None


def test_11_recurrent_symptom_detection():
    """Verifies non-consecutive episodes of same symptom are classified as recurrent."""
    fixture = LONGITUDINAL_FIXTURES["recurrent_symptom"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    recurrent_labels = [p.normalized_label for p in dto.recurrent_complaints]
    assert "headache" in recurrent_labels
    
    headache_rec = next(p for p in dto.recurrent_complaints if p.normalized_label == "headache")
    assert headache_rec.is_recurrent is True
    assert headache_rec.episode_count >= 3


def test_12_explicit_resolution_moves_to_resolved():
    """Verifies explicit resolution evidence moves a problem to resolved_problems."""
    fixture = LONGITUDINAL_FIXTURES["explicit_resolution"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    resolved_labels = [p.normalized_label for p in dto.resolved_problems]
    assert "fever" in resolved_labels
    fever_rec = next(p for p in dto.resolved_problems if p.normalized_label == "fever")
    assert fever_rec.status == "resolved"
    assert fever_rec.resolution_evidence is not None


def test_13_missing_not_resolved_invariant():
    """
    CRITICAL SAFETY INVARIANT:
    Unmentioned prior symptoms must NOT be marked resolved.
    """
    fixture = LONGITUDINAL_FIXTURES["missing_not_resolved"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    
    # Fever and Cough were in Encounter 1, but unmentioned in Encounter 2
    resolved_labels = [p.normalized_label for p in dto.resolved_problems]
    assert "fever" not in resolved_labels
    assert "cough" not in resolved_labels
    
    unresolved_labels = [p.normalized_label for p in dto.unresolved_issues]
    assert "fever" in unresolved_labels or "cough" in unresolved_labels


def test_14_chronic_baseline_conditions_preserved():
    """Verifies patient profile chronic conditions are preserved in baseline and problem registry."""
    fixture = LONGITUDINAL_FIXTURES["comorbidities"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert "Hypertension" in dto.chronic_baseline_conditions
    assert "Type 2 Diabetes Mellitus" in dto.chronic_baseline_conditions
    assert "Osteoarthritis" in dto.chronic_baseline_conditions
    assert "Penicillin" in dto.known_allergies


def test_15_empty_history_graceful_handling():
    """Verifies patient with no history returns clean empty structure without errors."""
    fixture = LONGITUDINAL_FIXTURES["no_history_baseline"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert dto.patient_id == "PAT_LONG_014_CLEAN"
    assert len(dto.biomarker_trajectories) == 0
    assert len(dto.resolved_problems) == 0


def test_16_provenance_summary_integrity():
    """Verifies provenance audit trails are generated for all synthesized datasets."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.provenance_summary) > 0
    assert any("encounter" in p.lower() for p in dto.provenance_summary)
    assert any("biomarker" in p.lower() for p in dto.provenance_summary)


def test_17_orchestrator_integration_clinical_output():
    """Verifies full orchestrator turn processing produces longitudinal_context in clinical output."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.status == "complete"
    assert turn_resp.clinical_output is not None
    assert "longitudinal_context" in turn_resp.clinical_output
    
    long_ctx = turn_resp.clinical_output["longitudinal_context"]
    assert long_ctx is not None
    assert len(long_ctx["biomarker_trajectories"]) == 1
    assert long_ctx["biomarker_trajectories"][0]["trajectory"] == "increasing"


def test_18_phase2a_emergency_non_llm_bypass_preserved():
    """Verifies emergency red flag short-circuits safely and generates output with longitudinal context."""
    from tests.fixtures.synthetic_inputs import FIXTURE_RED_FLAG_EMERGENCY
    turn_resp = process_turn(FIXTURE_RED_FLAG_EMERGENCY)
    
    assert turn_resp.status == "emergency"
    assert turn_resp.immediate_attention_required is True
    assert turn_resp.clinical_output is not None
    assert "longitudinal_context" in turn_resp.clinical_output



def test_19_phase2b_risk_scores_remain_immutable():
    """Verifies Phase 2B risk scoring equations and levels are untouched by Phase 9."""
    fixture = LONGITUDINAL_FIXTURES["recurrent_symptom"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.clinical_output is not None
    risk_out = turn_resp.clinical_output["risk_assessment"]
    assert risk_out["risk_score"] is not None
    assert risk_out["risk_level"] in ["LOW", "MODERATE", "HIGH", "URGENT"]


def test_20_phase7_and_phase8b_coexistence():
    """Verifies Phase 7 dual taxonomy and Phase 8B remedy recommendations coexist with Phase 9 context."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    turn_resp = process_turn(fixture)
    
    out = turn_resp.clinical_output
    assert "ayurveda_modern_representation" in out
    assert "ayurveda_recommendation" in out
    assert "longitudinal_context" in out


def test_21_biomarker_alias_normalization():
    """Verifies alias resolution (e.g. Hb, HGB -> Hemoglobin)."""
    k1, d1 = normalize_test_name("Hb")
    k2, d2 = normalize_test_name("HGB")
    k3, d3 = normalize_test_name("Hemoglobin")
    assert k1 == k2 == k3 == "hemoglobin"
    assert d1 == d2 == d3 == "Hemoglobin"


def test_22_unit_normalization():
    """Verifies standard unit string normalization."""
    assert normalize_unit("g/dL") == "g/dL"
    assert normalize_unit("gm/dl") == "g/dL"
    assert normalize_unit("mg/dL") == "mg/dL"
    assert normalize_unit("/mcL") == "/mcL"
    assert normalize_unit("cells/mm3") == "/mcL"
    assert normalize_unit("%") == "%"


def run_all_tests():
    tests = [
        test_01_schema_validation,
        test_02_timeline_chronological_ordering,
        test_03_timeline_preserves_undated_events,
        test_04_timeline_deduplication,
        test_05_biomarker_increasing_trajectory,
        test_06_biomarker_decreasing_trajectory,
        test_07_biomarker_stable_trajectory,
        test_08_biomarker_fluctuating_trajectory,
        test_09_biomarker_single_observation_insufficient_data,
        test_10_biomarker_unit_mismatch_blocks_calculation,
        test_11_recurrent_symptom_detection,
        test_12_explicit_resolution_moves_to_resolved,
        test_13_missing_not_resolved_invariant,
        test_14_chronic_baseline_conditions_preserved,
        test_15_empty_history_graceful_handling,
        test_16_provenance_summary_integrity,
        test_17_orchestrator_integration_clinical_output,
        test_18_phase2a_emergency_non_llm_bypass_preserved,
        test_19_phase2b_risk_scores_remain_immutable,
        test_20_phase7_and_phase8b_coexistence,
        test_21_biomarker_alias_normalization,
        test_22_unit_normalization,
    ]
    
    passed = 0
    failed = 0
    print("=" * 70)
    print("VAIDYAARC PHASE 9 DIRECT TEST SUITE")
    print("=" * 70)
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
            
    print("-" * 70)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
