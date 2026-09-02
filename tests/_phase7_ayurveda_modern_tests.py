"""
Integration Test Suite for Phase 7: Ayurveda <-> Modern Medicine Representation.

Tests full LangGraph workflow execution with Phase 7 node integrated,
validating end-to-end traversal from intake completion to dual-perspective representation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflow import build_vaidyaarc_graph
from app.ayurveda_modern_node import ayurveda_modern_representation


def test_phase7_integration_complete_case():
    """Test full workflow execution with complete intake and supported descriptive mapping."""
    graph = build_vaidyaarc_graph()

    state = {
        "patient_id": "TEST_P7_001",
        "session_id": "SESS_P7_001",
        "language": "English",
        "patient_profile": {
            "age": 35,
            "medical_conditions": [],
            "allergies": []
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "4 days",
        "severity": "moderate",
        "associated_symptoms": [],
        "current_message": "My stomach is burning in the upper abdomen for 4 days",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": True,
        "questions_asked": [],
        "patient_location": {"city": "Hyderabad", "pincode": "500001"},
    }

    result = graph.invoke(state)

    # 1. Verify Phase 7 status
    assert result.get("representation_status") in ["complete", "partial"], "Phase 7 representation status missing"
    assert result.get("ayurveda_modern_output") is not None, "Phase 7 output missing"

    # 2. Verify Modern Representation
    mod = result.get("modern_representation")
    assert mod is not None, "Modern representation missing"
    assert "stomach" in mod["chief_complaint"].lower()

    # 3. Verify Ayurvedic Representation
    ayur = result.get("ayurvedic_representation")
    assert ayur is not None, "Ayurvedic representation missing"
    concept_ids = [c["concept_id"] for c in ayur["mapped_concepts"]]
    assert "vidaha" in concept_ids, "Expected 'vidaha' mapping"

    # 4. Verify Correspondence Layer
    corr = result.get("correspondence_summary")
    assert corr is not None, "Correspondence summary missing"
    assert len(corr["correspondences"]) > 0, "Expected correspondences"

    # 5. Verify Dosha and Prakriti are 'not_assessed'
    assert ayur["dosha_assessment"]["status"] == "not_assessed"
    assert ayur["prakriti_assessment"]["status"] == "not_assessed"

    # 6. Verify Upstream nodes completed
    assert result.get("clinical_case") is not None, "Phase 3 clinical case missing"
    assert result.get("care_navigation_status") is not None, "Phase 4 care navigation missing"
    assert result.get("monitoring_status") == "initial_encounter", "Phase 5 monitoring missing"

    print("[PASS] Complete case integration test passed.")


def test_phase7_integration_red_flag_escalation():
    """Test full workflow execution with red-flag symptoms preserving emergency precedence."""
    graph = build_vaidyaarc_graph()

    state = {
        "patient_id": "TEST_P7_002",
        "session_id": "SESS_P7_002",
        "language": "English",
        "patient_profile": {
            "age": 60,
            "medical_conditions": ["hypertension"],
            "allergies": []
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "crushing",
        "location": "chest",
        "duration": "1 hour",
        "severity": "severe",
        "associated_symptoms": ["difficulty breathing"],
        "current_message": "I have severe crushing chest pain and difficulty breathing",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": True,
        "questions_asked": [],
        "patient_location": {"city": "Hyderabad", "pincode": "500001"},
    }

    result = graph.invoke(state)

    # 1. Verify Phase 2A Red Flag
    assert result.get("red_flag_status") == "red_flags_detected"
    assert result.get("immediate_attention_required") is True

    # 2. Verify Phase 7 preserves Red Flag and emergency warning
    out = result.get("ayurveda_modern_output")
    assert out is not None
    assert out["safety_constraints"]["red_flag_alert_preserved"] is True
    assert out["safety_constraints"]["emergency_warning"] is not None
    assert "CRITICAL EMERGENCY SAFETY OVERRIDE" in out["safety_constraints"]["emergency_warning"]

    # 3. Verify safety notes contain the warning
    safety_notes = result.get("ayurveda_safety_notes") or []
    assert any("CRITICAL EMERGENCY SAFETY OVERRIDE" in note for note in safety_notes)

    print("[PASS] Red flag emergency escalation integration test passed.")


def test_phase7_integration_unmapped_symptom():
    """Test workflow execution with an unmapped modern symptom."""
    graph = build_vaidyaarc_graph()

    state = {
        "patient_id": "TEST_P7_003",
        "session_id": "SESS_P7_003",
        "language": "English",
        "patient_profile": {
            "age": 28,
            "medical_conditions": [],
            "allergies": []
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": "blurred vision",
        "nature_of_pain": None,
        "location": "eyes",
        "duration": "2 weeks",
        "severity": "mild",
        "associated_symptoms": [],
        "current_message": "I have blurred vision in my eyes for 2 weeks",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": True,
        "questions_asked": [],
        "patient_location": {"city": "Hyderabad", "pincode": "500001"},
    }

    result = graph.invoke(state)

    corr = result.get("correspondence_summary")
    assert corr is not None
    assert corr["overall_correspondence_status"] == "no_supported_correspondence"
    assert len(corr["unmapped_modern_symptoms"]) > 0

    print("[PASS] Unmapped symptom integration test passed.")


def main():
    print("=" * 80)
    print("RUNNING PHASE 7 INTEGRATION SUITE")
    print("=" * 80)

    print("\n--- Phase 7 Integration Test 1: Complete Case Flow ---")
    test_phase7_integration_complete_case()

    print("\n--- Phase 7 Integration Test 2: Red Flag Emergency Flow ---")
    test_phase7_integration_red_flag_escalation()

    print("\n--- Phase 7 Integration Test 3: Unmapped Symptom Flow ---")
    test_phase7_integration_unmapped_symptom()

    print("=" * 80)
    print("ALL PHASE 7 INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
