"""
VAIDYAARC PHASE 9 STANDALONE VALIDATION RUNNER

Validates:
1. Pydantic v2 schemas and serialization.
2. Chronological timeline synthesis and date normalization.
3. Biomarker mathematical trajectories without diagnostic bias.
4. Active, resolved, recurrent, and unresolved problem classification.
5. Invariant 'Missing != Resolved'.
6. Full orchestrator integration and multi-phase coexistence.

ZERO-LLM. 100% DETERMINISTIC.
"""

import sys
import os

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.longitudinal_schema import (
    BiomarkerRecord,
    BiomarkerTrajectory,
    ProblemRecord,
    LongitudinalPatientContextDTO,
)
from app.biomarker_engine import (
    extract_biomarker_records,
    calculate_biomarker_trajectories,
    normalize_test_name,
)
from app.problem_registry import (
    normalize_problem_label,
    build_problem_registry,
)
from app.longitudinal_timeline import (
    parse_and_normalize_date,
    build_longitudinal_timeline,
    synthesize_longitudinal_context,
)
from app.orchestrator import process_turn
from tests.fixtures.longitudinal_fixtures import LONGITUDINAL_FIXTURES


def test_01_schema_instantiation_and_validation():
    """Validates instantiation and serialization of all Phase 9 models."""
    dto = LongitudinalPatientContextDTO(
        patient_id="PAT_001",
        total_encounters=3,
    )
    dumped = dto.model_dump()
    assert dumped["patient_id"] == "PAT_001"
    assert dumped["total_encounters"] == 3
    assert isinstance(dumped["timeline"], list)
    assert isinstance(dumped["biomarker_trajectories"], list)


def test_02_timeline_chronological_ordering():
    """Validates chronological ordering of dated encounters."""
    encs = [
        {"encounter_id": "ENC_03", "timestamp": "2025-09-01", "chief_complaint": "cough"},
        {"encounter_id": "ENC_01", "timestamp": "2025-01-15", "chief_complaint": "fever"},
        {"encounter_id": "ENC_02", "timestamp": "2025-05-10", "chief_complaint": "headache"},
    ]
    timeline, _ = build_longitudinal_timeline(
        patient_id="PAT_001",
        previous_encounters=encs,
        documents=[],
        investigations=[],
        previous_conversations=[],
    )
    assert len(timeline) == 3
    assert timeline[0].source_id == "ENC_01"
    assert timeline[1].source_id == "ENC_02"
    assert timeline[2].source_id == "ENC_03"


def test_03_timeline_preservation_of_undated_events():
    """Validates that undated historical events are not discarded."""
    encs = [
        {"encounter_id": "ENC_DATED", "timestamp": "2025-05-01", "chief_complaint": "fever"},
        {"encounter_id": "ENC_UNDATED_1", "timestamp": None, "chief_complaint": "cough"},
        {"encounter_id": "ENC_UNDATED_2", "timestamp": "", "chief_complaint": "rash"},
    ]
    timeline, _ = build_longitudinal_timeline(
        patient_id="PAT_001",
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
    """Validates conservative deduplication of exact duplicate events."""
    fixture = LONGITUDINAL_FIXTURES["duplicate_encounters"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    enc_events = [e for e in dto.timeline if e.event_type == "encounter"]
    assert len(enc_events) == 2  # 1 historical deduped + 1 current turn


def test_05_biomarker_increasing_trajectory():
    """Validates that strictly increasing values output 'increasing' without medical claims."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "hba1c"
    assert traj.trajectory == "increasing"
    assert traj.direction == "upward"
    assert traj.absolute_delta == 2.6
    assert traj.percentage_change == 40.0
    assert "licensed medical evaluation" in traj.interpretation_note


def test_06_biomarker_decreasing_trajectory():
    """Validates that strictly decreasing values output 'decreasing'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_decreasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.normalized_name == "fasting_blood_glucose"
    assert traj.trajectory == "decreasing"
    assert traj.direction == "downward"
    assert traj.absolute_delta == -130.0


def test_07_biomarker_stable_trajectory():
    """Validates that unchanging values output 'stable'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_stable"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.trajectory == "stable"
    assert traj.direction == "unchanged"
    assert traj.absolute_delta == 0.0


def test_08_biomarker_fluctuating_trajectory():
    """Validates that oscillating values output 'fluctuating'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_fluctuating"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.trajectory == "fluctuating"
    assert traj.direction == "fluctuating"


def test_09_biomarker_single_observation_insufficient_data():
    """Validates that single observation yields 'insufficient_data'."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_single"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.observation_count == 1
    assert traj.trajectory == "insufficient_data"
    assert traj.absolute_delta is None


def test_10_biomarker_unit_mismatch():
    """Validates that incompatible units trigger unit_mismatch flag."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_unit_mismatch"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.biomarker_trajectories) == 1
    traj = dto.biomarker_trajectories[0]
    assert traj.unit_mismatch is True
    assert traj.trajectory == "insufficient_data"


def test_11_recurrent_symptom_detection():
    """Validates that recurring non-consecutive episodes are flagged recurrent."""
    fixture = LONGITUDINAL_FIXTURES["recurrent_symptom"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert any(p.normalized_label == "headache" for p in dto.recurrent_complaints)
    headache = next(p for p in dto.recurrent_complaints if p.normalized_label == "headache")
    assert headache.is_recurrent is True
    assert headache.episode_count >= 3


def test_12_explicit_resolution():
    """Validates that explicit confirmation moves problem to resolved_problems."""
    fixture = LONGITUDINAL_FIXTURES["explicit_resolution"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert any(p.normalized_label == "fever" for p in dto.resolved_problems)
    fever = next(p for p in dto.resolved_problems if p.normalized_label == "fever")
    assert fever.status == "resolved"


def test_13_missing_not_resolved_invariant():
    """Validates that unmentioned prior symptoms remain unresolved/unspecified."""
    fixture = LONGITUDINAL_FIXTURES["missing_not_resolved"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert not any(p.normalized_label == "fever" for p in dto.resolved_problems)
    assert not any(p.normalized_label == "cough" for p in dto.resolved_problems)
    assert any(p.normalized_label in {"fever", "cough"} for p in dto.unresolved_issues)


def test_14_chronic_baseline_preservation():
    """Validates chronic baseline conditions are preserved."""
    fixture = LONGITUDINAL_FIXTURES["comorbidities"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert "Hypertension" in dto.chronic_baseline_conditions
    assert "Type 2 Diabetes Mellitus" in dto.chronic_baseline_conditions
    assert "Osteoarthritis" in dto.chronic_baseline_conditions


def test_15_empty_history_baseline():
    """Validates graceful execution on empty historical profile."""
    fixture = LONGITUDINAL_FIXTURES["no_history_baseline"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert dto.patient_id == "PAT_LONG_014_CLEAN"
    assert len(dto.biomarker_trajectories) == 0


def test_16_provenance_summary():
    """Validates provenance audit summary generation."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    dto = synthesize_longitudinal_context(fixture.model_dump())
    assert len(dto.provenance_summary) > 0


def test_17_orchestrator_turn_integration():
    """Validates full orchestrator integration producing longitudinal context."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    turn_resp = process_turn(fixture)
    assert turn_resp.status == "complete"
    assert turn_resp.clinical_output is not None
    assert "longitudinal_context" in turn_resp.clinical_output
    assert len(turn_resp.clinical_output["longitudinal_context"]["biomarker_trajectories"]) == 1


def test_18_phase2a_emergency_preservation():
    """Validates that emergency red flags short-circuit safely and output longitudinal context."""
    from tests.fixtures.synthetic_inputs import FIXTURE_RED_FLAG_EMERGENCY
    turn_resp = process_turn(FIXTURE_RED_FLAG_EMERGENCY)
    assert turn_resp.status == "emergency"
    assert turn_resp.immediate_attention_required is True
    assert "longitudinal_context" in turn_resp.clinical_output



def test_19_phase2b_immutability():
    """Validates Phase 2B risk assessment immutability."""
    fixture = LONGITUDINAL_FIXTURES["recurrent_symptom"]
    turn_resp = process_turn(fixture)
    risk_out = turn_resp.clinical_output["risk_assessment"]
    assert risk_out["risk_score"] is not None
    assert risk_out["risk_level"] in ["LOW", "MODERATE", "HIGH", "URGENT"]


def test_20_multi_phase_coexistence():
    """Validates coexistence of Phase 7, Phase 8B, and Phase 9 outputs."""
    fixture = LONGITUDINAL_FIXTURES["biomarker_increasing"]
    turn_resp = process_turn(fixture)
    out = turn_resp.clinical_output
    assert "ayurveda_modern_representation" in out
    assert "ayurveda_recommendation" in out
    assert "longitudinal_context" in out


def run_all_tests():
    tests = [
        test_01_schema_instantiation_and_validation,
        test_02_timeline_chronological_ordering,
        test_03_timeline_preservation_of_undated_events,
        test_04_timeline_deduplication,
        test_05_biomarker_increasing_trajectory,
        test_06_biomarker_decreasing_trajectory,
        test_07_biomarker_stable_trajectory,
        test_08_biomarker_fluctuating_trajectory,
        test_09_biomarker_single_observation_insufficient_data,
        test_10_biomarker_unit_mismatch,
        test_11_recurrent_symptom_detection,
        test_12_explicit_resolution,
        test_13_missing_not_resolved_invariant,
        test_14_chronic_baseline_preservation,
        test_15_empty_history_baseline,
        test_16_provenance_summary,
        test_17_orchestrator_turn_integration,
        test_18_phase2a_emergency_preservation,
        test_19_phase2b_immutability,
        test_20_multi_phase_coexistence,
    ]
    
    passed = 0
    failed = 0
    print("=" * 70)
    print("VAIDYAARC PHASE 9 VALIDATION SUITE")
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
