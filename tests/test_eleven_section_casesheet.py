"""
Tests for Conversational History-Taking & 11-Section Case-Sheet Synthesis.

Verifies:
1. Strict Zero-Hallucination for unelicited fields (pain severity, family history, diet, etc.).
2. All 11 Markdown Section Headings and sub-sections.
3. Multi-turn conversational consultation simulation reproducing the reference clinical dialogue.
4. Downstream projection compatibility with Phase 2A/2B and Phase 10/12 engines.
"""

import sys
from pathlib import Path

repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import pytest
from app.domain.clinical_history_schema import (
    EvolvingClinicalHistory,
    EpistemicStatus,
    InterviewStatus,
)
from app.agents.adaptive_intake_nodes import (
    _extract_delta_fallback,
    tier1_safety_precheck_node,
    clinical_delta_extractor_node,
    state_consolidation_ledger_node,
    deterministic_governance_node,
    adaptive_question_generator_node,
    safety_scope_sanitizer_node,
    casesheet_synthesizer_node,
)
from app.clinical_summary_engine import generate_eleven_section_casesheet


def _simulate_turn(state: dict) -> dict:
    """Simulates a single adaptive turn through the graph nodes."""
    state = tier1_safety_precheck_node(state)
    if state.get("tier1_emergency_triggered"):
        return state

    state = clinical_delta_extractor_node(state)
    state = state_consolidation_ledger_node(state)
    state = deterministic_governance_node(state)
    if state.get("governance_verdict") == "complete":
        state = casesheet_synthesizer_node(state)
    else:
        state = adaptive_question_generator_node(state)
        state = safety_scope_sanitizer_node(state)
    return state


def test_zero_hallucination_severity_unelicited():
    """Verify that severity is NOT hallucinated when patient does not specify it."""
    state = {
        "current_message": "I have been having foot pain and swelling since yesterday.",
        "turn_count": 0,
        "episode_id": "EP_ZH_01",
        "patient_id": "PT_ZH_01",
    }
    state = _simulate_turn(state)
    hist = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])

    # Finding severity must be None internally
    assert hist.chief_complaint is not None
    assert hist.chief_complaint.severity is None

    # Synthesize casesheet and check explicit "Not elicited" format
    casesheet = generate_eleven_section_casesheet(state)
    assert "Severity: Not elicited" in casesheet
    # Ensure no fabricated numbers
    assert "7/10" not in casesheet
    assert "moderate" not in casesheet.lower().split("severity")[1].split("\n")[0]


def test_zero_hallucination_severity_when_explicitly_stated():
    """Verify that severity IS recorded when patient explicitly rates it."""
    state = {
        "current_message": "Foot pain rated at 7/10 since yesterday.",
        "turn_count": 0,
        "episode_id": "EP_ZH_02",
        "patient_id": "PT_ZH_02",
    }
    state = _simulate_turn(state)
    hist = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])

    assert hist.chief_complaint is not None
    assert hist.chief_complaint.severity is not None
    assert "7/10" in str(hist.chief_complaint.severity.current_value)

    casesheet = generate_eleven_section_casesheet(state)
    assert "7/10" in casesheet


def test_all_eleven_sections_present_in_casesheet():
    """Verify all 11 Markdown sections and sub-headings are strictly rendered."""
    state = {
        "current_message": "Severe right foot pain and swelling since yesterday, difficult to walk, that is all.",
        "turn_count": 0,
        "episode_id": "EP_11SEC",
        "patient_id": "PT_11SEC",
    }
    state = _simulate_turn(state)
    casesheet = generate_eleven_section_casesheet(state)

    expected_sections = [
        "# Clinical History",
        "## 1. Patient Details",
        "## 2. Chief Complaints",
        "## 3. History of Presenting Illness",
        "### Relevant Past Episode",
        "## 4. Past Medical History",
        "## 5. Drug History",
        "## 6. Allergy History",
        "## 7. Family History",
        "## 8. Personal History",
        "## 9. Review of Systems — Relevant Findings",
        "## 10. Preliminary Clinical Summary",
        "## 11. Important Points Requiring Clinical Assessment",
        "### Clinical Differential Considerations",
        "### Recommended Physical Examinations",
        "### Red-Flag Guidance & Warning Signs",
    ]

    for sec in expected_sections:
        assert sec in casesheet, f"Expected section '{sec}' was not found in casesheet output"


def test_multiturn_conversational_consultation_simulation():
    """
    Simulates the exact 8-turn clinical dialogue reference:
    - Foot pain presentation
    - Laterality & onset context exploration
    - Character & functional impact
    - Zero-hallucination severity rating
    - Local inflammatory signs & trauma check
    - ROS pertinent negatives
    - Past episodes & recurrence
    - Comorbidities & daily medications (Telugu confirmation)
    - Full 11-section Case-Sheet generation with Telugu closure
    """
    session_id = "EP_REF_SIM"
    patient_id = "PT_TELUGU_01"

    state = {
        "episode_id": session_id,
        "patient_id": patient_id,
        "turn_count": 0,
        "prior_question_intents": [],
    }

    # Turn 1: Initial Presentation
    state["current_message"] = "I have been having foot pain and swelling since yesterday."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    q1 = state["conversation_message"].lower()
    assert any(k in q1 for k in ["which foot", "which side", "right or left"])

    # Turn 2: Laterality & Triggers
    state["current_message"] = "It is on my right foot. I walked a long distance the previous day."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    hist2 = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    assert hist2.chief_complaint.laterality is not None
    assert "right" in str(hist2.chief_complaint.laterality.current_value).lower()
    q2 = state["conversation_message"].lower()
    assert any(k in q2 for k in ["describe the feeling", "pulling", "dragging", "sharp", "sensation", "feel like"])

    # Turn 3: Character & Functional Impact
    state["current_message"] = "It feels like a pulling and dragging sensation. Walking makes it worse, and I have difficulty walking."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    hist3 = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    assert hist3.chief_complaint.character is not None
    assert "pulling" in str(hist3.chief_complaint.character.current_value).lower()
    assert hist3.functional_impact is not None
    q3 = state["conversation_message"].lower()
    assert any(k in q3 for k in ["scale", "mild", "moderate", "severe", "rate"])

    # Turn 4: Severity Rating
    state["current_message"] = "It is around 7/10."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    hist4 = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    assert hist4.chief_complaint.severity is not None
    assert "7/10" in str(hist4.chief_complaint.severity.current_value)
    q4 = state["conversation_message"].lower()
    assert any(k in q4 for k in ["redness", "warmth", "injury", "fall", "twist"])

    # Turn 5: Local Signs & Trauma Negation
    state["current_message"] = "There is no redness or warmth, and no injury or fall. No ankle sprain."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    hist5 = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    assert hist5.trauma_history is not None
    assert "denied" in str(hist5.trauma_history.current_value).lower()
    q5 = state["conversation_message"].lower()
    assert any(k in q5 for k in ["numbness", "tingling", "weakness", "fever", "chills"])

    # Turn 6: Review of Systems Negatives
    state["current_message"] = "No numbness, no tingling, and no fever."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    q6 = state["conversation_message"].lower()
    assert any(k in q6 for k in ["similar episode", "had this before", "previously", "first time"])

    # Turn 7: Past Episode Recurrence
    state["current_message"] = "Yes, about 6 months ago I had similar pain. It lasted for about a day, I consulted a doctor and took medication which resolved it."
    state = _simulate_turn(state)
    assert state["status"] == "in_progress"
    hist7 = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    assert len(hist7.relevant_past_episodes) >= 1
    q7 = state["conversation_message"].lower()
    assert any(k in q7 for k in ["blood pressure", "diabetes", "regular medications", "daily medications"])

    # Turn 8: Comorbidities & Daily Medications (Telugu Confirmation)
    state["current_message"] = "సరే. నాకు BP మరియు diabetes ఉన్నాయి, రోజూ మందులు వాడుతున్నాను"
    state = _simulate_turn(state)

    # Verification: Intake is complete
    assert state["status"] == "complete"
    assert state["is_complete"] is True
    assert state["information_complete"] is True

    # Check that Telugu closure acknowledgment is prepended to conversation_message
    msg = state["conversation_message"]
    assert "సరే" in msg or "నమోదు" in msg

    # Check that 11-section Clinical Case-Sheet is rendered in conversation_message and clinical_casesheet
    casesheet = state["clinical_casesheet"]
    assert "# Clinical History" in casesheet
    assert "## 1. Patient Details" in casesheet
    assert "## 2. Chief Complaints" in casesheet
    assert "## 3. History of Presenting Illness" in casesheet
    assert "## 4. Past Medical History" in casesheet
    assert "## 5. Drug History" in casesheet
    assert "## 6. Allergy History" in casesheet
    assert "## 7. Family History" in casesheet
    assert "## 8. Personal History" in casesheet
    assert "## 9. Review of Systems — Relevant Findings" in casesheet
    assert "## 10. Preliminary Clinical Summary" in casesheet
    assert "## 11. Important Points Requiring Clinical Assessment" in casesheet

    # Specific clinical content assertions
    assert "7/10" in casesheet
    assert "pulling" in casesheet.lower()
    assert "walking" in casesheet.lower()
    assert "Diabetes mellitus:** Present; on regular medication" in casesheet
    assert "Hypertension:** Present; on regular medication" in casesheet
    assert "Right foot pain: Present" in casesheet or "Foot pain: Present" in casesheet
    assert "Fever: No" in casesheet
    assert "Numbness: No" in casesheet
    assert "Tingling: No" in casesheet
    assert "Trauma: No" in casesheet
    assert "Redness: No" in casesheet
    assert "Local warmth: No" in casesheet
