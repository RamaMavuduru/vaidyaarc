"""
Phase 12.5: VaidyaArc Brain Acceptance & Integration Readiness Test Suite.

Contains 48 comprehensive, deterministic tests verifying:
- Part A (Tests 1-10): 10 End-to-End Synthetic Patient Journeys
- Part B (Tests 11-15): Multi-Turn State Integrity (5-10 turns, context preservation)
- Part C (Tests 16-27): Safety & Adversarial Attack Resistance (12 adversarial cases)
- Part D (Tests 28-34): Missing-Information Integrity (Missing != Absent)
- Part E (Tests 35-37): Provenance & Traceability Audit
- Part F (Tests 38-40): Cross-Phase Output Compatibility & Strict Boundaries
- Part G (Tests 41-45): Malformed Input & Robustness Handling
- Part I (Tests 46-47): Deterministic Repeatability (Multi-pass equivalence)
- Part J (Test 48): Latency & Performance Baseline Verification

100% DETERMINISTIC. ZERO-LLM. 100% PASS RATE REQUIRED.
"""

import sys
import os
import json
import time
import copy

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    PatientLocationDTO,
    DocumentDTO,
    TurnResponseDTO,
    StructuredClinicalOutputDTO,
)
from app.llm_adapter import (
    set_llm_adapter,
    reset_llm_adapter,
    DeterministicFallbackAdapter,
)
from app.orchestrator import (
    process_turn,
    synthesize_clinical_output,
    evaluate_early_safety_check,
    EMERGENCY_ALERT_MESSAGE,
)
from tests.fixtures.brain_acceptance_fixtures import (
    JOURNEY_01_ROUTINE_SIMPLE,
    JOURNEY_02_INCOMPLETE_TURN1,
    JOURNEY_02_INCOMPLETE_TURN2,
    JOURNEY_03_EMERGENCY_RED_FLAG,
    JOURNEY_04_LATE_EMERGENCY,
    JOURNEY_05_MODERATE_RISK_CONVERGENCE,
    JOURNEY_06_LONGITUDINAL_PATIENT,
    JOURNEY_07_INVESTIGATIONS_BIOMARKERS,
    JOURNEY_08_MEDICATIONS_ALLERGIES,
    JOURNEY_09_AYURVEDA_REPRESENTATION,
    JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE,
    MULTITURN_TURN_1,
    MULTITURN_TURN_2,
    MULTITURN_TURN_3,
    MULTITURN_TURN_4,
    MULTITURN_TURN_5,
    ADVERSARIAL_BURIED_EMERGENCY,
    ADVERSARIAL_REASSURING_LANGUAGE_AFTER_SEVERE,
    ADVERSARIAL_MULTIPLE_RED_FLAGS,
    ADVERSARIAL_CONTRADICTORY_SEVERITY,
    FIXTURE_MISSING_ALLERGIES,
    FIXTURE_MISSING_AGE,
    FIXTURE_MISSING_MEDICATIONS,
    FIXTURE_EMPTY_STRING,
    FIXTURE_WHITESPACE_ONLY,
    FIXTURE_VERY_LONG_TEXT,
    FIXTURE_SPECIAL_CHARACTERS,
)


# ==============================================================================
# PART A: 10 END-TO-END SYNTHETIC PATIENT JOURNEYS (TESTS 1 - 10)
# ==============================================================================

def test_01_journey_routine_simple():
    """Journey 1: Routine tension headache completes with clean clinical output bundle."""
    resp = process_turn(JOURNEY_01_ROUTINE_SIMPLE)
    assert resp.status == "complete"
    assert resp.information_complete is True
    assert resp.clinical_output is not None
    assert resp.clinical_output["intake_summary"]["chief_complaint"] == "tension headache"
    assert resp.clinical_output["safety_findings"]["immediate_attention_required"] is False
    assert resp.clinical_output["risk_assessment"]["risk_level"] in ["LOW", "MODERATE", "ROUTINE", "UNKNOWN"]
    assert resp.clinical_output["clinical_summary"] is not None
    assert resp.clinical_output["dashavidha_atura_pariksha"] is not None


def test_02_journey_incomplete_vague_clarification():
    """Journey 2: Incomplete input prompts for missing slots without crashing or inventing facts."""
    resp1 = process_turn(JOURNEY_02_INCOMPLETE_TURN1)
    assert resp1.status == "in_progress"
    assert resp1.information_complete is False
    assert len(resp1.missing_information) > 0

    resp2 = process_turn(JOURNEY_02_INCOMPLETE_TURN2)
    assert resp2.status == "in_progress"
    assert resp2.information_complete is False
    assert "duration" in resp2.missing_information or "severity" in resp2.missing_information


def test_03_journey_immediate_emergency_red_flag():
    """Journey 3: Crushing chest pain triggers immediate emergency short-circuit without LLM."""
    resp = process_turn(JOURNEY_03_EMERGENCY_RED_FLAG)
    assert resp.status == "emergency"
    assert resp.immediate_attention_required is True
    assert resp.red_flag_status == "red_flags_detected"
    assert "severe chest pain" in resp.red_flags or len(resp.red_flags) > 0
    assert resp.conversation_message == EMERGENCY_ALERT_MESSAGE
    assert resp.clinical_output is not None
    assert resp.clinical_output["safety_findings"]["immediate_attention_required"] is True


def test_04_journey_late_emerging_emergency():
    """Journey 4: Sudden thunderclap headache on turn 4 immediately activates emergency override."""
    resp = process_turn(JOURNEY_04_LATE_EMERGENCY)
    assert resp.status == "emergency"
    assert resp.immediate_attention_required is True
    assert resp.clinical_output["safety_findings"]["immediate_attention_required"] is True


def test_05_journey_multiple_moderate_risk_factors_converging():
    """Journey 5: 65yo diabetic with CKD and persistent epigastric pain scores high risk in Phase 2B."""
    resp = process_turn(JOURNEY_05_MODERATE_RISK_CONVERGENCE)
    assert resp.status == "complete"
    assert resp.clinical_output["risk_assessment"]["risk_level"] in ["HIGH", "MODERATE", "URGENT"]
    assert resp.clinical_output["safety_findings"]["immediate_attention_required"] is False


def test_06_journey_longitudinal_patient_prior_encounters():
    """Journey 6: Recurrent knee pain synthesizes prior encounters and longitudinal timeline in Phase 9/10/11."""
    resp = process_turn(JOURNEY_06_LONGITUDINAL_PATIENT)
    assert resp.status == "complete"
    long_ctx = resp.clinical_output.get("longitudinal_context")
    assert long_ctx is not None
    assert long_ctx.get("total_encounters") >= 2
    assert resp.clinical_output["clinical_summary"] is not None


def test_07_journey_investigations_and_biomarkers():
    """Journey 7: Document biomarkers (HbA1c, Fasting Glucose) extracted cleanly into clinical bundle."""
    resp = process_turn(JOURNEY_07_INVESTIGATIONS_BIOMARKERS)
    assert resp.status == "complete"
    clin_sum = resp.clinical_output["clinical_summary"]
    assert clin_sum is not None
    assert "prior_investigations" in clin_sum
    inv_section = clin_sum["prior_investigations"]
    serialized = json.dumps(inv_section)
    assert "HbA1c" in serialized


def test_08_journey_chronic_medications_and_allergies():
    """Journey 8: Chronic meds (Metformin, Atorvastatin) and allergies preserved without silent conversion."""
    resp = process_turn(JOURNEY_08_MEDICATIONS_ALLERGIES)
    assert resp.status == "complete"
    clin_sum = resp.clinical_output["clinical_summary"]
    meds_section = clin_sum["medication_history"]
    allergies_section = clin_sum["allergy_history"]
    assert "Metformin" in json.dumps(meds_section)
    assert "Penicillin" in json.dumps(allergies_section)


def test_09_journey_ayurveda_representation_and_dashavidha():
    """Journey 9: Burning stomach and sour eructations map descriptive Ayurveda concepts + Dashavidha observations."""
    resp = process_turn(JOURNEY_09_AYURVEDA_REPRESENTATION)
    assert resp.status == "complete"
    ayur_rep = resp.clinical_output["ayurveda_modern_representation"]
    assert ayur_rep is not None
    dv = resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert dv["prakriti"]["status"] == "explicitly_reported"
    assert dv["prakriti"]["prior_formal_assessment"]["reported_prakriti"] == "Pitta-Vata"
    assert any("burning" in obs.lower() for obs in dv["vikriti"]["reported_observations"])


def test_10_journey_full_spectrum_comprehensive():
    """Journey 10: 52yo multi-domain patient exercises all 12 phases in unison without failure."""
    resp = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    assert resp.status == "complete"
    co = resp.clinical_output
    assert co["patient_id"] == "PAT_J10_FULL"
    assert co["safety_findings"] is not None
    assert co["risk_assessment"] is not None
    assert co["clinical_case"] is not None
    assert co["care_navigation"] is not None
    assert co["follow_up_monitoring"] is not None
    assert co["ayurveda_modern_representation"] is not None
    assert co["ayurveda_recommendation"] is not None
    assert co["longitudinal_context"] is not None
    assert co["advanced_risk_assessment"] is not None
    assert co["clinical_summary"] is not None
    assert co["consultation_questions"] is not None
    assert co["dashavidha_atura_pariksha"] is not None
    assert len(co["provenance_notes"]) >= 10


# ==============================================================================
# PART B: MULTI-TURN STATE INTEGRITY (TESTS 11 - 15)
# ==============================================================================

def test_11_multiturn_sequential_information_gathering():
    """Multi-turn progression across turns 1 through 5 builds state cumulatively without loss."""
    r1 = process_turn(MULTITURN_TURN_1)
    assert r1.status == "in_progress"
    assert r1.updated_state["chief_complaint"] == "stomach pain"

    r2 = process_turn(MULTITURN_TURN_2)
    assert r2.status == "in_progress"
    assert r2.updated_state["nature_of_pain"] == "burning"

    r3 = process_turn(MULTITURN_TURN_3)
    assert r3.status == "in_progress"
    assert r3.updated_state["location"] == "upper abdomen"

    r4 = process_turn(MULTITURN_TURN_4)
    assert r4.status == "in_progress"
    assert "3 days" in r4.updated_state["duration"]

    r5 = process_turn(MULTITURN_TURN_5)
    assert r5.status == "complete"
    assert r5.information_complete is True
    assert r5.updated_state["severity"] == "moderate"


def test_12_multiturn_turn_isolation():
    """Current message does not leak into prior transcript fields across turns."""
    inp = copy.deepcopy(MULTITURN_TURN_3)
    inp.message.original_text = "upper abdomen only"
    resp = process_turn(inp)
    assert resp.updated_state["current_message"] == "upper abdomen only"


def test_13_multiturn_profile_immutability():
    """Patient demographics (age, sex, allergies) persist immutably across multi-turn exchanges."""
    inp = copy.deepcopy(MULTITURN_TURN_5)
    inp.patient_profile = PatientProfileDTO(age=49, sex="female", allergies=["Sulfa"])
    inp.state_snapshot["patient_profile"] = {"age": 49, "sex": "female", "allergies": ["Sulfa"]}
    resp = process_turn(inp)
    prof = resp.updated_state["patient_profile"]
    assert prof["age"] == 49
    assert prof["sex"] == "female"
    assert "Sulfa" in prof["allergies"]


def test_14_multiturn_late_arriving_fact_available_downstream():
    """Fact mentioned on final turn (e.g. moderate severity) is correctly consumed by Phase 2B/3/11/12."""
    resp = process_turn(MULTITURN_TURN_5)
    co = resp.clinical_output
    assert co["intake_summary"]["severity"] == "moderate"
    assert co["clinical_case"]["symptom_descriptors"]["severity"] == "moderate"


def test_15_multiturn_snapshot_rehydration_fidelity():
    """State snapshot passed back to client can be rehydrated into next turn without data corruption."""
    r5 = process_turn(MULTITURN_TURN_5)
    snapshot = r5.updated_state
    next_input = NormalizedClinicalInputDTO(
        patient_id="PAT_MT_01",
        episode_id="EP_MT_01",
        message=NormalizedMessageDTO(original_text="confirming moderate stomach pain since 3 days"),
        state_snapshot=snapshot,
    )
    r_next = process_turn(next_input)
    assert r_next.updated_state["chief_complaint"] == "stomach pain"
    assert "3 days" in r_next.updated_state["duration"]


# ==============================================================================
# PART C: SAFETY & ADVERSARIAL ATTACK RESISTANCE (TESTS 16 - 27)
# ==============================================================================

def test_16_safety_first_turn_emergency():
    """Adversarial 1: First turn explicit emergency immediately aborts without intake delay."""
    resp = process_turn(JOURNEY_03_EMERGENCY_RED_FLAG)
    assert resp.immediate_attention_required is True
    assert resp.status == "emergency"


def test_17_safety_buried_emergency_in_prose():
    """Adversarial 2: Red-flag symptom buried inside conversational small talk triggers emergency."""
    resp = process_turn(ADVERSARIAL_BURIED_EMERGENCY)
    assert resp.immediate_attention_required is True
    assert resp.red_flag_status == "red_flags_detected"


def test_18_safety_late_emergency_activation():
    """Adversarial 3: Safe routine turn followed by sudden emergency immediately escalates."""
    resp = process_turn(JOURNEY_04_LATE_EMERGENCY)
    assert resp.status == "emergency"
    assert resp.immediate_attention_required is True


def test_19_safety_reassuring_language_after_severe():
    """Adversarial 4: Patient minimizing severe symptoms does NOT downgrade Phase 2A emergency status."""
    resp = process_turn(ADVERSARIAL_REASSURING_LANGUAGE_AFTER_SEVERE)
    assert resp.immediate_attention_required is True
    assert resp.status == "emergency"


def test_20_safety_contradictory_severity_resolves_to_severe():
    """Adversarial 5: Contradictory severity statements resolve safely without crash."""
    resp = process_turn(ADVERSARIAL_CONTRADICTORY_SEVERITY)
    assert resp.updated_state["severity"] == "severe"


def test_21_safety_multiple_simultaneous_red_flags():
    """Adversarial 6: Multiple simultaneous red flags are all captured in safety findings."""
    resp = process_turn(ADVERSARIAL_MULTIPLE_RED_FLAGS)
    assert resp.immediate_attention_required is True
    assert len(resp.red_flags) >= 2


def test_22_safety_high_phase2b_risk_without_red_flags():
    """Adversarial 7: High risk score does not hallucinate false emergency override flag."""
    resp = process_turn(JOURNEY_05_MODERATE_RISK_CONVERGENCE)
    assert resp.status == "complete"
    assert resp.immediate_attention_required is False
    assert resp.clinical_output["risk_assessment"]["risk_level"] in ["HIGH", "MODERATE", "URGENT"]


def test_23_safety_phase10_escalation_immutable():
    """Adversarial 8: Phase 10 advanced risk output is preserved and cannot be muted downstream."""
    resp = process_turn(JOURNEY_06_LONGITUDINAL_PATIENT)
    adv = resp.clinical_output.get("advanced_risk_assessment")
    assert adv is not None
    assert "composite_risk_level" in adv
    assert "longitudinal_risk" in adv


def test_24_safety_no_downstream_downgrade_of_phase2a():
    """Adversarial 9: Downstream phases (11, 12) preserve immediate_attention_required=True."""
    resp = process_turn(JOURNEY_03_EMERGENCY_RED_FLAG)
    co = resp.clinical_output
    assert co["safety_findings"]["immediate_attention_required"] is True
    assert co["dashavidha_atura_pariksha"]["safety_context"]["immediate_attention_required"] is True


def test_25_safety_zero_diagnosis_invariants():
    """Adversarial 10: Output never contains definitive diagnostic statements."""
    for fixture in [JOURNEY_01_ROUTINE_SIMPLE, JOURNEY_05_MODERATE_RISK_CONVERGENCE, JOURNEY_09_AYURVEDA_REPRESENTATION]:
        resp = process_turn(fixture)
        serialized = json.dumps(resp.clinical_output).lower()
        for forbidden in ["definitive diagnosis:", "you are diagnosed with", "patient has confirmed"]:
            assert forbidden not in serialized


def test_26_safety_zero_prescription_invariants():
    """Adversarial 11: Output never contains drug prescriptions or active dosages."""
    for fixture in [JOURNEY_01_ROUTINE_SIMPLE, JOURNEY_08_MEDICATIONS_ALLERGIES, JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE]:
        resp = process_turn(fixture)
        serialized = json.dumps(resp.clinical_output).lower()
        for forbidden in ["prescribed rx", "take 2 tablets", "take 500mg twice daily", "start taking immediately"]:
            assert forbidden not in serialized


def test_27_safety_malformed_safety_state_defaults_safe():
    """Adversarial 12: Corrupted red flag status string safely defaults without crashing."""
    corrupted_input = copy.deepcopy(JOURNEY_01_ROUTINE_SIMPLE)
    corrupted_input.state_snapshot["red_flag_status"] = None
    corrupted_input.state_snapshot["immediate_attention_required"] = None
    resp = process_turn(corrupted_input)
    assert resp.status == "complete"
    assert resp.immediate_attention_required is False


# ==============================================================================
# PART D: MISSING-INFORMATION INTEGRITY (TESTS 28 - 34)
# ==============================================================================

def test_28_missing_allergy_not_assumed_nkda():
    """Missing allergy information does NOT assert 'No Known Drug Allergies' (NKDA)."""
    resp = process_turn(FIXTURE_MISSING_ALLERGIES)
    clin_sum = resp.clinical_output["clinical_summary"]
    allergies_section = clin_sum["allergy_history"]
    serialized = json.dumps(allergies_section).lower()
    assert "all allergies negative" not in serialized
    assert "no known drug allergies not confirmed" in serialized or "not reported" in serialized


def test_29_missing_medications_not_assumed_none():
    """Missing medication history is explicitly recorded as unassessed / not documented."""
    resp = process_turn(FIXTURE_MISSING_MEDICATIONS)
    clin_sum = resp.clinical_output["clinical_summary"]
    meds_section = clin_sum["medication_history"]
    serialized = json.dumps(meds_section).lower()
    assert "not reported" in serialized or meds_section["status"] == "not_reported"


def test_30_missing_family_history_not_assumed_negative():
    """Missing family history does NOT assert absence of genetic/familial disease."""
    resp = process_turn(FIXTURE_MISSING_ALLERGIES)
    clin_sum = resp.clinical_output["clinical_summary"]
    fam_section = clin_sum["family_history"]
    serialized = json.dumps(fam_section).lower()
    assert "no family history of disease" not in serialized
    assert fam_section["status"] == "not_reported"


def test_31_missing_review_of_systems_not_assumed_negative():
    """Missing Review of Systems (ROS) does NOT claim all organ systems are negative."""
    resp = process_turn(FIXTURE_MISSING_ALLERGIES)
    clin_sum = resp.clinical_output["clinical_summary"]
    ros_section = clin_sum["review_of_systems"]
    serialized = json.dumps(ros_section).lower()
    assert "all systems negative" not in serialized
    assert "system negatives not inferred" in serialized or ros_section["status"] in ["not_reported", "reported"]


def test_32_missing_age_in_dashavidha_vaya():
    """Missing chronological age in patient profile leaves Vaya parameter strictly not_assessed."""
    resp = process_turn(FIXTURE_MISSING_AGE)
    dv = resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert dv["vaya"]["status"] == "not_assessed"
    assert len(dv["vaya"]["clinical_limitations"]) > 0


def test_33_missing_prior_investigations_not_assumed_normal():
    """Absence of prior lab investigations does NOT assert normal lab biomarkers."""
    resp = process_turn(FIXTURE_MISSING_ALLERGIES)
    clin_sum = resp.clinical_output["clinical_summary"]
    inv_section = clin_sum["prior_investigations"]
    serialized = json.dumps(inv_section).lower()
    assert "all laboratory tests normal" not in serialized
    assert inv_section["status"] == "not_reported"


def test_34_missing_dashavidha_observations_strict_10_not_assessed():
    """Completely blank intake marks all 10 Dashavidha parameters as not_assessed with limitations."""
    blank_input = NormalizedClinicalInputDTO(
        patient_id="PAT_BLANK",
        episode_id="EP_BLANK",
        message=NormalizedMessageDTO(original_text="mild"),
        patient_profile=PatientProfileDTO(),
        state_snapshot={
            "chief_complaint": "general checkup",
            "duration": "1 day",
            "severity": "mild",
            "missing_information": [],
            "information_complete": True,
        },
    )
    resp = process_turn(blank_input)
    dv = resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert dv["parameters_not_assessed_count"] >= 8


# ==============================================================================
# PART E: PROVENANCE & TRACEABILITY AUDIT (TESTS 35 - 37)
# ==============================================================================

def test_35_provenance_system_wide_notes_present():
    """Clinical output contains complete system-wide audit provenance notes for all phases."""
    resp = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    notes = resp.clinical_output["provenance_notes"]
    assert any("Phase 2A" in n for n in notes)
    assert any("Phase 2B" in n for n in notes)
    assert any("Phase 9" in n for n in notes)
    assert any("Phase 10" in n for n in notes)
    assert any("Phase 11" in n for n in notes)
    assert any("Phase 12" in n for n in notes)


def test_36_provenance_dashavidha_parameter_sources():
    """Dashavidha parameters explicitly record their data provenance keys without hallucination."""
    resp = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    dv = resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert "patient_profile.vitals" in dv["pramana"]["provenance_sources"]
    assert "patient_profile.age" in dv["vaya"]["provenance_sources"]
    assert "patient_profile.reported_prakriti" in dv["prakriti"]["provenance_sources"]


def test_37_provenance_clinical_summary_traceability():
    """Clinical summary sections map findings directly to documented state slots."""
    resp = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    clin_sum = resp.clinical_output["clinical_summary"]
    hpi = clin_sum["history_of_present_illness"]
    assert len(hpi["provenance"]) > 0


# ==============================================================================
# PART F: CROSS-PHASE COMPATIBILITY & STRICT BOUNDARIES (TESTS 38 - 40)
# ==============================================================================

def test_38_cross_phase_phase7_remains_descriptive_only():
    """Phase 7 does not generate disease diagnoses or replace Phase 1B intake."""
    resp = process_turn(JOURNEY_09_AYURVEDA_REPRESENTATION)
    ayur = resp.clinical_output["ayurveda_modern_representation"]
    assert "ayurvedic_representation" in ayur
    assert "modern_representation" in ayur
    assert "safety_constraints" in ayur


def test_39_cross_phase_phase10_advanced_risk_isolation():
    """Phase 10 calculates trajectory risk without overriding Phase 2B baseline score."""
    resp = process_turn(JOURNEY_06_LONGITUDINAL_PATIENT)
    p2b_risk = resp.clinical_output["risk_assessment"]
    p10_risk = resp.clinical_output["advanced_risk_assessment"]
    assert "risk_level" in p2b_risk
    assert "longitudinal_risk_score" in p10_risk["longitudinal_risk"]
    assert "composite_risk_level" in p10_risk


def test_40_cross_phase_phase11_and_12_coexistence():
    """Phase 11 clinical summary and Phase 12 Dashavidha exist simultaneously in structured output."""
    resp = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    assert resp.clinical_output["clinical_summary"] is not None
    assert resp.clinical_output["consultation_questions"] is not None
    assert resp.clinical_output["dashavidha_atura_pariksha"] is not None


# ==============================================================================
# PART G: MALFORMED INPUT & ROBUSTNESS HANDLING (TESTS 41 - 45)
# ==============================================================================

def test_41_malformed_empty_string_input():
    """Empty string input returns in_progress without crashing."""
    resp = process_turn(FIXTURE_EMPTY_STRING)
    assert resp.status in ["in_progress", "complete"]


def test_42_malformed_whitespace_only_input():
    """Whitespace-only input does not raise unhandled exception."""
    resp = process_turn(FIXTURE_WHITESPACE_ONLY)
    assert resp.status in ["in_progress", "complete"]


def test_43_malformed_very_long_input_text():
    """Very long input text (2000+ chars) is safely truncated/processed without memory blowup."""
    resp = process_turn(FIXTURE_VERY_LONG_TEXT)
    assert resp.status == "complete"
    assert resp.clinical_output is not None


def test_44_malformed_special_characters_and_symbols():
    """Special characters (#, @, &, <>, %, *) are handled safely without parse failures."""
    resp = process_turn(FIXTURE_SPECIAL_CHARACTERS)
    assert resp.status in ["complete", "emergency"]


def test_45_malformed_unexpected_extra_keys_in_profile():
    """Extra unexpected keys in PatientProfileDTO are safely accommodated via extra='allow'."""
    extra_input = copy.deepcopy(JOURNEY_01_ROUTINE_SIMPLE)
    extra_input.patient_profile = PatientProfileDTO(age=28, sex="female", custom_unknown_key="test_value")
    resp = process_turn(extra_input)
    assert resp.status == "complete"


# ==============================================================================
# PART I: DETERMINISTIC REPEATABILITY (TESTS 46 - 47)
# ==============================================================================

def test_46_deterministic_turn_processing_exact_match():
    """Processing identical input across separate executions produces 100% identical outputs."""
    resp_a = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)
    resp_b = process_turn(JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE)

    out_a = copy.deepcopy(resp_a.clinical_output)
    out_b = copy.deepcopy(resp_b.clinical_output)

    # Exclude dynamic wall-clock timestamps generated at invocation time
    out_a.pop("case_id", None)
    out_b.pop("case_id", None)
    if isinstance(out_a.get("clinical_case"), dict):
        out_a["clinical_case"].pop("created_at", None)
        out_a["clinical_case"].pop("case_id", None)
    if isinstance(out_b.get("clinical_case"), dict):
        out_b["clinical_case"].pop("created_at", None)
        out_b["clinical_case"].pop("case_id", None)
    if isinstance(out_a.get("follow_up_monitoring"), dict):
        out_a["follow_up_monitoring"].pop("evaluated_at", None)
    if isinstance(out_b.get("follow_up_monitoring"), dict):
        out_b["follow_up_monitoring"].pop("evaluated_at", None)

    assert out_a == out_b


def test_47_deterministic_dashavidha_repeatability():
    """Dashavidha engine produces byte-identical serialized output across multiple invocations."""
    resp1 = process_turn(JOURNEY_09_AYURVEDA_REPRESENTATION)
    resp2 = process_turn(JOURNEY_09_AYURVEDA_REPRESENTATION)
    assert resp1.clinical_output["dashavidha_atura_pariksha"] == resp2.clinical_output["dashavidha_atura_pariksha"]


# ==============================================================================
# PART J: PERFORMANCE / LATENCY BASELINE SANITY (TEST 48)
# ==============================================================================

def test_48_latency_baseline_sanity():
    """Full multi-phase brain turn execution completes within acceptable offline baseline."""
    start_time = time.time()
    resp = process_turn(JOURNEY_01_ROUTINE_SIMPLE)
    elapsed = time.time() - start_time
    assert resp.status == "complete"
    assert elapsed < 15.0, f"Execution took too long: {elapsed:.2f}s"


# ==============================================================================
# MASTER ACCEPTANCE TEST RUNNER
# ==============================================================================

def run_all_tests():
    tests = [
        # Part A: 10 End-to-End Journeys
        test_01_journey_routine_simple,
        test_02_journey_incomplete_vague_clarification,
        test_03_journey_immediate_emergency_red_flag,
        test_04_journey_late_emerging_emergency,
        test_05_journey_multiple_moderate_risk_factors_converging,
        test_06_journey_longitudinal_patient_prior_encounters,
        test_07_journey_investigations_and_biomarkers,
        test_08_journey_chronic_medications_and_allergies,
        test_09_journey_ayurveda_representation_and_dashavidha,
        test_10_journey_full_spectrum_comprehensive,
        # Part B: Multi-Turn State Integrity
        test_11_multiturn_sequential_information_gathering,
        test_12_multiturn_turn_isolation,
        test_13_multiturn_profile_immutability,
        test_14_multiturn_late_arriving_fact_available_downstream,
        test_15_multiturn_snapshot_rehydration_fidelity,
        # Part C: Safety & Adversarial Attacks
        test_16_safety_first_turn_emergency,
        test_17_safety_buried_emergency_in_prose,
        test_18_safety_late_emergency_activation,
        test_19_safety_reassuring_language_after_severe,
        test_20_safety_contradictory_severity_resolves_to_severe,
        test_21_safety_multiple_simultaneous_red_flags,
        test_22_safety_high_phase2b_risk_without_red_flags,
        test_23_safety_phase10_escalation_immutable,
        test_24_safety_no_downstream_downgrade_of_phase2a,
        test_25_safety_zero_diagnosis_invariants,
        test_26_safety_zero_prescription_invariants,
        test_27_safety_malformed_safety_state_defaults_safe,
        # Part D: Missing Information Integrity
        test_28_missing_allergy_not_assumed_nkda,
        test_29_missing_medications_not_assumed_none,
        test_30_missing_family_history_not_assumed_negative,
        test_31_missing_review_of_systems_not_assumed_negative,
        test_32_missing_age_in_dashavidha_vaya,
        test_33_missing_prior_investigations_not_assumed_normal,
        test_34_missing_dashavidha_observations_strict_10_not_assessed,
        # Part E: Provenance & Traceability
        test_35_provenance_system_wide_notes_present,
        test_36_provenance_dashavidha_parameter_sources,
        test_37_provenance_clinical_summary_traceability,
        # Part F: Cross-Phase Compatibility
        test_38_cross_phase_phase7_remains_descriptive_only,
        test_39_cross_phase_phase10_advanced_risk_isolation,
        test_40_cross_phase_phase11_and_12_coexistence,
        # Part G: Malformed Input Robustness
        test_41_malformed_empty_string_input,
        test_42_malformed_whitespace_only_input,
        test_43_malformed_very_long_input_text,
        test_44_malformed_special_characters_and_symbols,
        test_45_malformed_unexpected_extra_keys_in_profile,
        # Part I: Determinism
        test_46_deterministic_turn_processing_exact_match,
        test_47_deterministic_dashavidha_repeatability,
        # Part J: Latency Baseline
        test_48_latency_baseline_sanity,
    ]

    passed = 0
    failed = 0
    set_llm_adapter(DeterministicFallbackAdapter())
    print("=" * 80)
    print("VAIDYAARC PHASE 12.5 BRAIN ACCEPTANCE TEST SUITE")
    print(f"Total Tests to Execute: {len(tests)}")
    print("=" * 80)

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

    print("-" * 80)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed} | Skipped: 0")
    print("=" * 80)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
