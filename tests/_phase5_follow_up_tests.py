import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflow import build_vaidyaarc_graph


def create_base_state():
    return {
        "patient_id": "TEST_P5_001",
        "session_id": "SESSION_001",
        "language": "English",
        "patient_profile": {
            "age": 35,
            "medical_conditions": ["hypertension"],
            "allergies": [],
            "location": {"city": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867},
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],
        "patient_location": {"city": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867},
    }


def test_initial_encounter_flow():
    """Test 1: First-time encounter through full graph produces 'initial_encounter' monitoring status."""
    print("\n--- Phase 5 Integration Test 1: Initial Encounter Flow ---")
    graph = build_vaidyaarc_graph()
    state = create_base_state()
    state.update({
        "chief_complaint": "fever",
        "nature_of_pain": "none",
        "location": "none",
        "severity": "mild",
        "duration": "2 days",
        "associated_symptoms": [],
        "information_complete": True,
        "missing_information": [],
    })

    result = graph.invoke(state)

    assert result.get("care_navigation_status") == "matched"
    assert result.get("monitoring_status") == "initial_encounter"
    assert result.get("patient_trajectory") == "initial_encounter"
    assert result.get("risk_trend") == "unknown"
    print("[PASS] Initial encounter passed with 'initial_encounter' status.")


def test_improving_follow_up_flow():
    """Test 2: Follow-up encounter with symptom and risk reduction."""
    print("\n--- Phase 5 Integration Test 2: Improving Follow-up Flow ---")
    graph = build_vaidyaarc_graph()
    state = create_base_state()
    
    # Prior encounter: severe fever, HIGH risk (28)
    previous_case_state = {
        "session_id": "SESSION_000",
        "chief_complaint": "fever",
        "nature_of_pain": "none",
        "location": "none",
        "severity": "severe",
        "duration": "4 days",
        "associated_symptoms": ["body ache"],
        "risk_level": "HIGH",
        "risk_score": 28,
        "immediate_attention_required": False,
    }

    # Current encounter: mild fever, LOW risk (8)
    state.update({
        "session_id": "SESSION_001",
        "previous_case_state": previous_case_state,
        "chief_complaint": "fever",
        "nature_of_pain": "none",
        "location": "none",
        "severity": "mild",
        "duration": "5 days",
        "associated_symptoms": ["body ache"],
        "information_complete": True,
        "missing_information": [],
    })

    result = graph.invoke(state)

    assert result.get("patient_trajectory") == "improving"
    assert result.get("risk_trend") == "decreased"
    assert result.get("monitoring_status") == "improving"
    print("[PASS] Improving follow-up trajectory correctly classified.")


def test_red_flag_escalation_follow_up_flow():
    """Test 3: Follow-up encounter where emergency red flag appears."""
    print("\n--- Phase 5 Integration Test 3: Red Flag Escalation Follow-up ---")
    graph = build_vaidyaarc_graph()
    state = create_base_state()

    # Prior encounter: mild stomach pain, LOW risk
    previous_case_state = {
        "session_id": "SESSION_000",
        "chief_complaint": "stomach pain",
        "severity": "mild",
        "duration": "2 days",
        "associated_symptoms": [],
        "risk_level": "LOW",
        "risk_score": 8,
        "immediate_attention_required": False,
    }

    # Current encounter: severe chest pain, emergency red flag
    state.update({
        "session_id": "SESSION_001",
        "previous_case_state": previous_case_state,
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "crushing pressure",
        "location": "center of chest",
        "severity": "very severe",
        "duration": "1 hour",
        "associated_symptoms": ["shortness of breath"],
        "red_flag_status": "red_flags_detected",
        "red_flags": ["severe chest pain", "difficulty breathing"],
        "immediate_attention_required": True,
        "information_complete": True,
        "missing_information": [],
    })

    result = graph.invoke(state)

    assert result.get("immediate_attention_required") is True
    assert result.get("patient_trajectory") == "escalation_required"
    assert result.get("monitoring_status") == "escalation_required"
    assert "emergency" in result.get("next_monitoring_action", "").lower()
    print("[PASS] Emergency red-flag override strictly enforced in monitoring.")


def test_explicit_resolution_flow():
    """Test 4: Follow-up encounter where symptom is explicitly confirmed resolved."""
    print("\n--- Phase 5 Integration Test 4: Explicit Resolution Flow ---")
    graph = build_vaidyaarc_graph()
    state = create_base_state()

    # Prior encounter: vomiting + fever
    previous_case_state = {
        "session_id": "SESSION_000",
        "chief_complaint": "fever",
        "nature_of_pain": "none",
        "location": "none",
        "severity": "moderate",
        "duration": "2 days",
        "associated_symptoms": ["vomiting"],
        "risk_level": "MODERATE",
        "risk_score": 18,
    }

    # Current encounter: vomiting stopped, only mild fever left
    state.update({
        "session_id": "SESSION_001",
        "previous_case_state": previous_case_state,
        "resolved_signals": ["vomiting"],
        "chief_complaint": "fever",
        "nature_of_pain": "none",
        "location": "none",
        "severity": "mild",
        "duration": "4 days",
        "associated_symptoms": [],
        "information_complete": True,
        "missing_information": [],
    })

    result = graph.invoke(state)

    resolved = result.get("resolved_signals") or []
    assert "vomiting" in resolved, f"Expected 'vomiting' in resolved_signals, got: {resolved}"
    assert result.get("patient_trajectory") == "improving"
    print("[PASS] Explicit symptom resolution confirmed.")


def run_all():
    print("=" * 80)
    print("RUNNING PHASE 5 INTEGRATION SUITE")
    print("=" * 80)
    test_initial_encounter_flow()
    test_improving_follow_up_flow()
    test_red_flag_escalation_follow_up_flow()
    test_explicit_resolution_flow()
    print("=" * 80)
    print("ALL PHASE 5 INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all()
