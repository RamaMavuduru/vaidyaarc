"""
================================================================================
PHASE 8A: ORCHESTRATOR INTEGRATION & MULTI-TURN WORKFLOW TESTS
================================================================================

Tests the end-to-end multi-turn conversation execution through the central
orchestrator, validating state evolution, safety early-exit, translation
provenance, and complete clinical output generation.

Runs 100% deterministically and offline without external service dependencies.
"""

import sys
import os
import copy

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
    EMERGENCY_ALERT_MESSAGE,
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


def test_full_multiturn_consultation_loop():
    """
    Simulate a complete 5-turn patient intake from chief complaint to completion.
    Verifies that state progresses accurately across turns and completes cleanly.
    """
    set_llm_adapter(DeterministicFallbackAdapter())
    
    session_id = "EP_SIM_001"
    patient_id = "PAT_SIM_001"
    current_state_snapshot = None

    # Turn 1: Chief complaint
    input_t1 = NormalizedClinicalInputDTO(
        patient_id=patient_id,
        episode_id=session_id,
        message=NormalizedMessageDTO(original_text="I have stomach pain"),
        state_snapshot=current_state_snapshot
    )
    res_t1 = process_turn(input_t1)
    assert res_t1.status == "in_progress"
    assert res_t1.information_complete is False
    assert res_t1.updated_state["chief_complaint"] == "stomach pain"
    current_state_snapshot = res_t1.updated_state

    # Turn 2: Nature of pain
    input_t2 = NormalizedClinicalInputDTO(
        patient_id=patient_id,
        episode_id=session_id,
        message=NormalizedMessageDTO(original_text="burning"),
        state_snapshot=current_state_snapshot
    )
    res_t2 = process_turn(input_t2)
    assert res_t2.status == "in_progress"
    assert res_t2.information_complete is False
    assert res_t2.updated_state["nature_of_pain"] == "burning"
    current_state_snapshot = res_t2.updated_state

    # Turn 3: Location
    input_t3 = NormalizedClinicalInputDTO(
        patient_id=patient_id,
        episode_id=session_id,
        message=NormalizedMessageDTO(original_text="upper abdomen"),
        state_snapshot=current_state_snapshot
    )
    res_t3 = process_turn(input_t3)
    assert res_t3.status == "in_progress"
    assert res_t3.information_complete is False
    assert res_t3.updated_state["location"] == "upper abdomen"
    current_state_snapshot = res_t3.updated_state

    # Turn 4: Duration
    input_t4 = NormalizedClinicalInputDTO(
        patient_id=patient_id,
        episode_id=session_id,
        message=NormalizedMessageDTO(original_text="2 days ago"),
        state_snapshot=current_state_snapshot
    )
    res_t4 = process_turn(input_t4)
    assert res_t4.status == "in_progress"
    assert res_t4.information_complete is False
    assert res_t4.updated_state["duration"] == "2 days ago"
    current_state_snapshot = res_t4.updated_state

    # Turn 5: Severity (final required field)
    input_t5 = NormalizedClinicalInputDTO(
        patient_id=patient_id,
        episode_id=session_id,
        message=NormalizedMessageDTO(original_text="moderate"),
        patient_location=PatientLocationDTO(city="Hyderabad", pincode="500001"),
        state_snapshot=current_state_snapshot
    )
    res_t5 = process_turn(input_t5)
    assert res_t5.status == "complete"
    assert res_t5.information_complete is True
    assert res_t5.clinical_output is not None
    
    # Verify complete synthesized bundle
    output = res_t5.clinical_output
    assert output["intake_summary"]["chief_complaint"] == "stomach pain"
    assert output["intake_summary"]["nature_of_pain"] == "burning"
    assert output["intake_summary"]["location"] == "upper abdomen"
    assert output["intake_summary"]["duration"] == "2 days ago"
    assert output["intake_summary"]["severity"] == "moderate"
    assert output["risk_assessment"]["risk_level"] in ["LOW", "MODERATE", "HIGH", "URGENT"]
    assert output["care_navigation"] is not None
    assert output["clinical_case"] is not None
    assert output["ayurveda_modern_representation"] is not None

    reset_llm_adapter()


def test_immediate_emergency_interception():
    """
    Verifies that emergency inputs immediately bypass conversational questions
    and return an emergency status with immediate attention flag and alert message.
    """
    set_llm_adapter(DeterministicFallbackAdapter())
    
    emergency_input = NormalizedClinicalInputDTO(
        patient_id="PAT_EMERG_DIRECT",
        episode_id="EP_EMERG_DIRECT",
        message=NormalizedMessageDTO(
            original_text="Severe chest pain and difficulty breathing since 10 minutes",
            english_text="Severe chest pain and difficulty breathing since 10 minutes"
        ),
        patient_location=PatientLocationDTO(city="Hyderabad", pincode="500001")
    )
    res = process_turn(emergency_input)
    assert res.status == "emergency"
    assert res.immediate_attention_required is True
    assert res.red_flag_status == "red_flags_detected"
    assert "difficulty breathing" in res.red_flags or "severe chest pain" in res.red_flags
    assert res.conversation_message == EMERGENCY_ALERT_MESSAGE
    assert res.clinical_output is not None
    assert res.clinical_output["risk_assessment"]["risk_score"] == 100
    assert res.clinical_output["risk_assessment"]["risk_level"] == "URGENT"

    reset_llm_adapter()


def test_document_and_investigation_attachment():
    """
    Verifies that uploaded documents and lab reports in NormalizedClinicalInputDTO
    are preserved in the state snapshot and clinical output.
    """
    set_llm_adapter(DeterministicFallbackAdapter())

    doc = DocumentDTO(
        document_id="DOC_CBC_001",
        document_type="lab_report",
        document_date="2026-03-01",
        extracted_text="Hemoglobin: 13.5 g/dL, Platelets: 250000",
        structured_biomarkers=[
            {"biomarker": "Hemoglobin", "value": 13.5, "unit": "g/dL", "status": "normal"}
        ]
    )

    input_dto = NormalizedClinicalInputDTO(
        patient_id="PAT_DOC_001",
        episode_id="EP_DOC_001",
        message=NormalizedMessageDTO(original_text="I have cough"),
        documents=[doc]
    )

    res = process_turn(input_dto)
    assert "ocr_documents" in res.updated_state
    assert len(res.updated_state["ocr_documents"]) == 1
    assert res.updated_state["ocr_documents"][0]["document_id"] == "DOC_CBC_001"

    reset_llm_adapter()


def test_provenance_and_translation_tracking():
    """
    Verifies that non-English messages retain original text, original language,
    normalized English text, and translation provenance across orchestrator execution.
    """
    set_llm_adapter(DeterministicFallbackAdapter())

    input_dto = NormalizedClinicalInputDTO(
        patient_id="PAT_TEL_003",
        episode_id="EP_TEL_003",
        message=NormalizedMessageDTO(
            original_text="నాకు జ్వరం ఉంది",
            original_language="te-IN",
            english_text="I have fever",
            source="patient",
            confidence=0.98,
            provenance="synthetic_bhashini_nmt"
        )
    )

    res = process_turn(input_dto)
    assert res.updated_state["original_transcript"] == "నాకు జ్వరం ఉంది"
    assert res.updated_state["original_language"] == "te-IN"
    assert res.updated_state["normalized_english"] == "I have fever"
    assert res.updated_state["translation_provenance"] == "synthetic_bhashini_nmt"
    assert res.updated_state["chief_complaint"] == "fever"

    reset_llm_adapter()


def main():
    print("=" * 80)
    print("RUNNING PHASE 8A ORCHESTRATOR INTEGRATION TESTS")
    print("=" * 80)

    tests = [
        ("1 (Full Multi-Turn Consultation Loop)", test_full_multiturn_consultation_loop),
        ("2 (Immediate Emergency Interception)", test_immediate_emergency_interception),
        ("3 (Document & Investigation Attachment)", test_document_and_investigation_attachment),
        ("4 (Provenance & Translation Tracking)", test_provenance_and_translation_tracking),
    ]

    passed = 0
    total = len(tests)

    for name, fn in tests:
        if run_test(name, fn):
            passed += 1

    print("=" * 80)
    if passed == total:
        print(f"ALL {total} PHASE 8A ORCHESTRATOR INTEGRATION TESTS PASSED!")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f"FAILED: {total - passed}/{total} integration tests failed.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

