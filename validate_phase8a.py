"""
================================================================================
PHASE 8A VALIDATION TEST SUITE
ARCHITECTURE CORRECTIONS & FOUNDATION IMPLEMENTATION
================================================================================

Comprehensive verification of:
1. Normalized input/output contracts (DTOs)
2. Decoupled LLM Adapter Layer
3. Central Orchestrator & Early Phase 2A Emergency Safety Evaluation
4. Preservation of Phases 1B, 2A, 2B, 3, 4, 5, 7 logic and invariants
5. Synthetic fixtures and external service independence
6. Zero-diagnosis and zero-treatment invariants

Runs 100% deterministically and offline without external service dependencies.
"""

import sys
import copy
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
    get_llm_adapter,
    set_llm_adapter,
    reset_llm_adapter,
    DeterministicFallbackAdapter,
    OllamaAdapter,
)
from app.orchestrator import (
    process_turn,
    synthesize_clinical_output,
    evaluate_early_safety_check,
    _build_initial_state_from_input,
    EMERGENCY_ALERT_MESSAGE,
)
from app.red_flag_rules import evaluate_red_flags as evaluate_red_flag_rules
from tests.fixtures.synthetic_inputs import (
    FIXTURE_ENGLISH_BASIC,
    FIXTURE_TELUGU_TRANSLATED,
    FIXTURE_OCR_NORMAL,
    FIXTURE_OCR_ABNORMAL,
    FIXTURE_PREVIOUS_ENCOUNTER_STABLE,
    FIXTURE_PREVIOUS_ENCOUNTER_WORSENING,
    FIXTURE_PREVIOUS_CONVERSATION_CONTEXT,
    FIXTURE_KNOWN_ALLERGIES_CONDITIONS,
    FIXTURE_RED_FLAG_EMERGENCY,
    FIXTURE_VAGUE_UNSPECIFIED,
    FIXTURE_UNMAPPED_AYURVEDIC,
)


def run_test(name: str, fn):
    try:
        fn()
        print(f"TEST {name}: PASS")
        return True
    except Exception as e:
        print(f"TEST {name}: FAIL -> {e}")
        import traceback
        traceback.print_exc()
        return False


def test_1_input_validation():
    """Test 1: Input Validation & Schema Ingestion (NormalizedClinicalInputDTO)."""
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    assert dto.patient_id == "PAT_ENG_001"
    assert dto.episode_id == "EP_ENG_001"
    assert dto.channel == "mobile_app"
    assert dto.message.original_text == "moderate"
    assert dto.message.original_language == "en"
    assert dto.patient_profile.age == 34
    assert dto.patient_profile.sex == "female"
    assert dto.patient_location.city == "Hyderabad"
    assert dto.patient_location.pincode == "500001"


def test_2_missing_optional_context():
    """Test 2: Missing Optional Context Safety (defaults handle empty/None)."""
    minimal_dto = NormalizedClinicalInputDTO(
        message=NormalizedMessageDTO(original_text="I have headache")
    )
    assert minimal_dto.patient_id == "ANONYMOUS"
    assert minimal_dto.episode_id == "EP_DEFAULT"
    assert minimal_dto.patient_profile is not None
    assert minimal_dto.patient_profile.medical_conditions == []
    assert minimal_dto.documents == []
    assert minimal_dto.previous_encounters == []
    assert minimal_dto.patient_location is None

    state = _build_initial_state_from_input(minimal_dto)
    assert state["patient_id"] == "ANONYMOUS"
    assert state["current_message"] == "I have headache"
    assert state["ocr_documents"] == []


def test_3_translation_provenance_preservation():
    """Test 3: Original Transcript & Translation Provenance Preservation."""
    dto = copy.deepcopy(FIXTURE_TELUGU_TRANSLATED)
    state = _build_initial_state_from_input(dto)
    assert state["original_transcript"] == "తీవ్రమైన"
    assert state["original_language"] == "te-IN"
    assert state["normalized_english"] == "severe"
    assert state["current_message"] == "severe"
    assert state["translation_provenance"] == "synthetic_stt_nmt"


def test_4_external_service_independence():
    """Test 4: External Service Independence (100% Offline with Fallback Adapter)."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert isinstance(response, TurnResponseDTO)
    assert response.status in ["in_progress", "complete", "emergency"]
    reset_llm_adapter()


def test_5_phase1b_intake_preservation():
    """Test 5: Phase 1B Adaptive Intake Behavior Preservation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.information_complete is True
    assert response.updated_state.get("chief_complaint") == "stomach pain"
    assert response.updated_state.get("nature_of_pain") == "burning"
    assert response.updated_state.get("location") == "upper abdomen"
    assert response.updated_state.get("duration") == "2 days"
    assert response.updated_state.get("severity") == "moderate"
    reset_llm_adapter()


def test_6_phase2a_emergency_non_llm_bypass():
    """Test 6: Phase 2A Red-Flag Emergency Non-LLM Bypass."""
    dto = copy.deepcopy(FIXTURE_RED_FLAG_EMERGENCY)
    response = process_turn(dto)
    assert response.status == "emergency"
    assert response.immediate_attention_required is True
    assert response.red_flag_status == "red_flags_detected"
    assert response.conversation_message == EMERGENCY_ALERT_MESSAGE
    assert response.clinical_output is not None
    assert response.clinical_output["risk_assessment"]["risk_level"] in ["URGENT", "HIGH", "CRITICAL", "urgent", "high", "critical"]
    assert response.clinical_output["risk_assessment"]["risk_score"] == 100
    assert response.clinical_output["safety_findings"]["immediate_attention_required"] is True


def test_7_red_flag_single_source_of_truth():
    """Test 7: Red-Flag Single Source of Truth Enforcement."""
    dto = copy.deepcopy(FIXTURE_RED_FLAG_EMERGENCY)
    state = _build_initial_state_from_input(dto)
    early_result = evaluate_early_safety_check(state)
    
    # Direct evaluation using app.red_flag_rules
    eval_state = dict(state)
    eval_state["information_complete"] = True
    direct_result = evaluate_red_flag_rules(eval_state)

    assert early_result["red_flag_status"] == direct_result["red_flag_status"]
    assert early_result["immediate_attention_required"] == direct_result["immediate_attention_required"]
    assert early_result["red_flags"] == direct_result["red_flags"]


def test_8_phase2b_risk_convergence_preservation():
    """Test 8: Phase 2B Risk Convergence Preservation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.clinical_output is not None
    risk = response.clinical_output["risk_assessment"]
    assert "risk_score" in risk
    assert "risk_level" in risk
    assert "risk_signals" in risk
    assert isinstance(risk["risk_score"], (int, float))
    reset_llm_adapter()


def test_9_phase3_clinical_case_preservation():
    """Test 9: Phase 3 Clinical Case Representation Preservation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.clinical_output is not None
    case = response.clinical_output["clinical_case"]
    assert "case_id" in case
    assert "symptom_descriptors" in case
    assert "risk_assessment" in case
    assert "safety_findings" in case
    reset_llm_adapter()


def test_10_phase4_care_navigation_preservation():
    """Test 10: Phase 4 Care Navigation Facility Matching Preservation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.clinical_output is not None
    nav = response.clinical_output["care_navigation"]
    assert nav is not None
    assert "care_pathway" in nav
    assert "matched_facilities" in nav
    assert "navigation_status" in nav
    reset_llm_adapter()


def test_11_phase5_longitudinal_stable():
    """Test 11: Phase 5 Longitudinal Comparison Preservation (Stable Trajectory)."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_PREVIOUS_ENCOUNTER_STABLE)
    response = process_turn(dto)
    assert response.clinical_output is not None
    follow_up = response.clinical_output["follow_up_monitoring"]
    assert follow_up is not None
    trajectory = follow_up["trajectory"]["trajectory"]
    assert trajectory in ["stable", "unchanged", "improving"]
    reset_llm_adapter()


def test_12_phase5_longitudinal_worsening():
    """Test 12: Phase 5 Longitudinal Comparison Preservation (Worsening Trajectory)."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_PREVIOUS_ENCOUNTER_WORSENING)
    response = process_turn(dto)
    assert response.clinical_output is not None
    follow_up = response.clinical_output["follow_up_monitoring"]
    assert follow_up is not None
    trajectory = follow_up["trajectory"]["trajectory"]
    assert trajectory in ["worsening", "escalation_required", "new_risk_signal"]
    reset_llm_adapter()


def test_13_phase7_dual_perspective_preservation():
    """Test 13: Phase 7 Dual-Perspective Ayurveda <-> Modern Representation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.clinical_output is not None
    ayur = response.clinical_output["ayurveda_modern_representation"]
    assert ayur is not None
    assert "modern_representation" in ayur
    assert "ayurvedic_representation" in ayur
    assert "safety_constraints" in ayur
    reset_llm_adapter()


def test_14_phase7_unmapped_symptom():
    """Test 14: Phase 7 Unsupported / Unmapped Symptom Handling."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_UNMAPPED_AYURVEDIC)
    state = _build_initial_state_from_input(dto)
    state["chief_complaint"] = "tingling in left pinky toe"
    state["duration"] = "1 day"
    state["severity"] = "mild"
    state["information_complete"] = True
    
    from app.ayurveda_modern_node import ayurveda_modern_representation
    res = ayurveda_modern_representation(state)
    ayur_out = res["ayurveda_modern_output"]
    ayur_rep = ayur_out["ayurvedic_representation"]
    assert len(ayur_rep["mapped_concepts"]) == 0
    assert any("tingling" in obs.lower() for obs in ayur_rep["unmapped_observations"])
    reset_llm_adapter()


def test_15_llm_adapter_abstraction():
    """Test 15: LLM Adapter Abstraction & Swappability."""
    fallback_adapter = DeterministicFallbackAdapter()
    set_llm_adapter(fallback_adapter)
    active = get_llm_adapter()
    assert active is fallback_adapter
    assert active.is_available() is True
    
    result = active.extract_intake("I have fever for 3 days")
    assert result.chief_complaint == "fever"
    assert result.duration == "3 days"
    
    reset_llm_adapter()
    default_active = get_llm_adapter()
    assert isinstance(default_active, OllamaAdapter)


def test_16_multiturn_conversation_continuity():
    """Test 16: Multi-Turn Conversation Continuity via State Snapshot."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_PREVIOUS_CONVERSATION_CONTEXT)
    response = process_turn(dto)
    assert response.updated_state.get("duration") == "since yesterday"
    assert response.updated_state.get("chief_complaint") == "fever"
    reset_llm_adapter()


def test_17_zero_diagnosis_zero_treatment():
    """Test 17: Zero Diagnosis / Zero Treatment Prescription Invariant."""
    set_llm_adapter(DeterministicFallbackAdapter())
    
    forbidden_prescriptive_phrases = [
        "prescribed rx", "take 2 tablets", "take 1 tablet", "500mg twice", "dosage: 500mg",
        "definitive diagnosis:", "you are diagnosed with", "start taking"
    ]
    
    for key, fixture in [
        ("basic", FIXTURE_ENGLISH_BASIC),
        ("allergy", FIXTURE_KNOWN_ALLERGIES_CONDITIONS),
        ("emergency", FIXTURE_RED_FLAG_EMERGENCY),
        ("worsening", FIXTURE_PREVIOUS_ENCOUNTER_WORSENING)
    ]:
        dto = copy.deepcopy(fixture)
        response = process_turn(dto)
        if response.clinical_output:
            out_str = str(response.clinical_output).lower()
            for phrase in forbidden_prescriptive_phrases:
                assert phrase not in out_str, f"Forbidden phrase '{phrase}' found in clinical output for {key}"
    reset_llm_adapter()


def test_18_clinical_output_bundle_completeness():
    """Test 18: Complete Structured Clinical Output Bundle Validation."""
    set_llm_adapter(DeterministicFallbackAdapter())
    dto = copy.deepcopy(FIXTURE_ENGLISH_BASIC)
    response = process_turn(dto)
    assert response.clinical_output is not None
    
    # Validate against StructuredClinicalOutputDTO
    bundle = StructuredClinicalOutputDTO(**response.clinical_output)
    assert bundle.case_id is not None
    assert bundle.patient_id == "PAT_ENG_001"
    assert bundle.intake_summary["chief_complaint"] == "stomach pain"
    assert bundle.safety_findings is not None
    assert bundle.risk_assessment is not None
    assert bundle.clinical_case is not None
    assert bundle.care_navigation is not None
    assert bundle.follow_up_monitoring is not None
    assert bundle.ayurveda_modern_representation is not None
    assert len(bundle.provenance_notes) >= 5
    reset_llm_adapter()


def main():
    print("=" * 80)
    print("RUNNING PHASE 8A DIRECT VALIDATION SUITE (FAST / ZERO-LLM)")
    print("=" * 80)

    tests = [
        ("1 (Input Validation & Schema Ingestion)", test_1_input_validation),
        ("2 (Missing Optional Context Safety)", test_2_missing_optional_context),
        ("3 (Original Transcript & Provenance Preservation)", test_3_translation_provenance_preservation),
        ("4 (External Service Independence)", test_4_external_service_independence),
        ("5 (Phase 1B Intake Behavior Preservation)", test_5_phase1b_intake_preservation),
        ("6 (Phase 2A Emergency Non-LLM Bypass)", test_6_phase2a_emergency_non_llm_bypass),
        ("7 (Red-Flag Single Source of Truth)", test_7_red_flag_single_source_of_truth),
        ("8 (Phase 2B Risk Convergence Preservation)", test_8_phase2b_risk_convergence_preservation),
        ("9 (Phase 3 Clinical Case Preservation)", test_9_phase3_clinical_case_preservation),
        ("10 (Phase 4 Care Navigation Preservation)", test_10_phase4_care_navigation_preservation),
        ("11 (Phase 5 Longitudinal Stable)", test_11_phase5_longitudinal_stable),
        ("12 (Phase 5 Longitudinal Worsening)", test_12_phase5_longitudinal_worsening),
        ("13 (Phase 7 Dual-Perspective Representation)", test_13_phase7_dual_perspective_preservation),
        ("14 (Phase 7 Unmapped Symptom Handling)", test_14_phase7_unmapped_symptom),
        ("15 (LLM Adapter Abstraction)", test_15_llm_adapter_abstraction),
        ("16 (Multi-Turn Continuity via State Snapshot)", test_16_multiturn_conversation_continuity),
        ("17 (Zero Diagnosis / Zero Treatment Invariant)", test_17_zero_diagnosis_zero_treatment),
        ("18 (Complete Structured Clinical Output Bundle)", test_18_clinical_output_bundle_completeness),
    ]

    passed = 0
    total = len(tests)

    for name, fn in tests:
        if run_test(name, fn):
            passed += 1

    print("=" * 80)
    if passed == total:
        print(f"ALL {total} PHASE 8A DIRECT VALIDATION TESTS PASSED CLEANLY!")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f"FAILED: {total - passed}/{total} tests failed.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

