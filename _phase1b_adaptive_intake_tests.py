"""
Phase 1B Adaptive Intake Tests
Tests the adaptive questioning for different chief complaints.
"""

from app.workflow import build_vaidyaarc_graph


def create_fresh_state():
    """Create a fresh patient state for each test."""
    return {
        "patient_id": "TEST001",
        "session_id": "SESSION001",
        "language": "English",
        "patient_profile": {
            "age": 30,
            "medical_conditions": [],
            "allergies": []
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
    }


def run_conversation(state, messages):
    """Run a conversation sequence and return final state."""
    graph = build_vaidyaarc_graph()
    
    for i, message in enumerate(messages):
        print(f"\nPatient: {message}")
        state["current_message"] = message
        result = graph.invoke(state)
        state.update(result)
        
        if state.get("conversation_message"):
            print(f"VaidyaArc: {state['conversation_message']}")
        
        state["conversation_history"].append({
            "role": "patient",
            "message": message
        })
        state["conversation_history"].append({
            "role": "assistant",
            "message": state.get("conversation_message", "")
        })
    
    return state


def test_stomach_pain():
    """Test A: Stomach pain (existing Phase 1 flow)."""
    print("\n" + "="*70)
    print("TEST A: STOMACH PAIN (Phase 1 Regression)")
    print("="*70)
    
    state = create_fresh_state()
    messages = [
        "I have stomach pain",
        "It feels like burning",
        "In my upper abdomen",
        "It started 2 days ago",
        "Moderate"
    ]
    
    final_state = run_conversation(state, messages)
    
    print("\n" + "-"*70)
    print("FINAL STATE CHECK:")
    print("-"*70)
    print(f"Chief Complaint: {final_state.get('chief_complaint')}")
    print(f"Location: {final_state.get('location')}")
    print(f"Nature of Pain: {final_state.get('nature_of_pain')}")
    print(f"Duration: {final_state.get('duration')}")
    print(f"Severity: {final_state.get('severity')}")
    print(f"Information Complete: {final_state.get('information_complete')}")
    print(f"Red Flag Status: {final_state.get('red_flag_status')}")
    print(f"Immediate Attention Required: {final_state.get('immediate_attention_required')}")
    
    # Validation
    assert final_state.get('chief_complaint') == "stomach pain", "Chief complaint should be 'stomach pain'"
    assert final_state.get('location') == "upper abdomen", "Location should be 'upper abdomen'"
    assert final_state.get('nature_of_pain') == "burning", "Nature of pain should be 'burning'"
    assert final_state.get('duration') == "2 days", "Duration should be '2 days'"
    assert (final_state.get('severity') or "").lower() == "moderate", "Severity should be 'moderate'"
    assert final_state.get('information_complete') == True, "Information should be complete"
    assert final_state.get('red_flag_status') == "no_obvious_red_flags", "Should have no red flags"
    
    print("\n[PASS] STOMACH PAIN TEST PASSED")
    return True


def test_fever():
    """Test B: Fever (should NOT ask about pain)."""
    print("\n" + "="*70)
    print("TEST B: FEVER (Adaptive Questions)")
    print("="*70)
    
    state = create_fresh_state()
    messages = [
        "I have fever",
    ]
    
    final_state = run_conversation(state, messages)
    
    print("\n" + "-"*70)
    print("VERIFICATION:")
    print("-"*70)
    print(f"Chief Complaint: {final_state.get('chief_complaint')}")
    print(f"Next Question: {final_state.get('next_question')}")
    print(f"Missing Information: {final_state.get('missing_information')}")
    print(f"Questions Asked: {final_state.get('questions_asked')}")
    
    # Validation
    assert final_state.get('chief_complaint') == "fever", "Chief complaint should be 'fever'"
    assert "pain" not in (final_state.get('next_question') or "").lower(), "Should NOT ask about pain for fever"
    assert "fever" in (final_state.get('next_question') or "").lower(), "Should ask fever-specific question"
    assert "nature_of_pain" not in final_state.get('missing_information', []), "Fever should NOT require nature_of_pain"
    assert "location" not in final_state.get('missing_information', []), "Fever should NOT require location"
    assert "duration" in final_state.get('missing_information', []), "Fever should require duration"
    assert "severity" in final_state.get('missing_information', []), "Fever should require severity"
    
    print("\n[PASS] FEVER TEST PASSED")
    return True


def test_cough():
    """Test C: Cough (should only ask about duration)."""
    print("\n" + "="*70)
    print("TEST C: COUGH (Minimal Questions)")
    print("="*70)
    
    state = create_fresh_state()
    messages = [
        "I have a cough",
    ]
    
    final_state = run_conversation(state, messages)
    
    print("\n" + "-"*70)
    print("VERIFICATION:")
    print("-"*70)
    print(f"Chief Complaint: {final_state.get('chief_complaint')}")
    print(f"Next Question: {final_state.get('next_question')}")
    print(f"Missing Information: {final_state.get('missing_information')}")
    
    # Validation
    assert final_state.get('chief_complaint') and "cough" in final_state.get('chief_complaint').lower(), "Chief complaint should contain 'cough'"
    assert "pain" not in (final_state.get('next_question') or "").lower(), "Should NOT ask about pain for cough"
    assert "duration" in final_state.get('missing_information', []), "Cough should require duration"
    assert "severity" not in final_state.get('missing_information', []), "Cough should NOT require severity (only duration)"
    assert "nature_of_pain" not in final_state.get('missing_information', []), "Cough should NOT require nature_of_pain"
    assert "location" not in final_state.get('missing_information', []), "Cough should NOT require location"
    
    print("\n[PASS] COUGH TEST PASSED")
    return True


def test_headache():
    """Test D: Headache (should ask about location, severity, duration)."""
    print("\n" + "="*70)
    print("TEST D: HEADACHE (Headache-Specific Questions)")
    print("="*70)
    
    state = create_fresh_state()
    messages = [
        "I have a headache",
    ]
    
    final_state = run_conversation(state, messages)
    
    print("\n" + "-"*70)
    print("VERIFICATION:")
    print("-"*70)
    print(f"Chief Complaint: {final_state.get('chief_complaint')}")
    print(f"Next Question: {final_state.get('next_question')}")
    print(f"Missing Information: {final_state.get('missing_information')}")
    
    # Validation
    assert final_state.get('chief_complaint') and "headache" in final_state.get('chief_complaint').lower(), "Chief complaint should contain 'headache'"
    assert "nature_of_pain" not in final_state.get('missing_information', []), "Headache should NOT require nature_of_pain"
    assert "location" in final_state.get('missing_information', []), "Headache should require location"
    assert "severity" in final_state.get('missing_information', []), "Headache should require severity"
    assert "duration" in final_state.get('missing_information', []), "Headache should require duration"
    
    print("\n[PASS] HEADACHE TEST PASSED")
    return True


def test_duplicate_prevention():
    """Test E: Duplicate question prevention."""
    print("\n" + "="*70)
    print("TEST E: DUPLICATE PREVENTION")
    print("="*70)
    
    state = create_fresh_state()
    graph = build_vaidyaarc_graph()
    
    # First message
    print("\nPatient: I have a fever")
    state["current_message"] = "I have a fever"
    result = graph.invoke(state)
    state.update(result)
    first_question = state.get("next_question")
    first_questions_asked = list(state.get("questions_asked", []))
    print(f"VaidyaArc: {first_question}")
    
    # Second message
    print("\nPatient: 3 days")
    state["current_message"] = "3 days"
    state["conversation_history"].append({"role": "patient", "message": "I have a fever"})
    state["conversation_history"].append({"role": "assistant", "message": first_question})
    result = graph.invoke(state)
    state.update(result)
    second_question = state.get("next_question")
    second_questions_asked = list(state.get("questions_asked", []))
    print(f"VaidyaArc: {second_question}")
    
    print("\n" + "-"*70)
    print("VERIFICATION:")
    print("-"*70)
    print(f"First Questions Asked: {first_questions_asked}")
    print(f"Second Questions Asked: {second_questions_asked}")
    print(f"First Question: {first_question}")
    print(f"Second Question: {second_question}")
    
    # Validation
    assert len(first_questions_asked) > 0, "Should track asked questions"
    assert len(second_questions_asked) > len(first_questions_asked), "Questions asked should accumulate"
    assert first_question != second_question, "Should not ask the same question twice"
    # Make sure questions don't overlap
    for q in first_questions_asked:
        assert q not in second_questions_asked[len(first_questions_asked):], f"Question '{q}' should not be asked again"
    
    print("\n[PASS] DUPLICATE PREVENTION TEST PASSED")
    return True


def test_red_flags_regression():
    """Test F: Phase 2A red flag regression - ensure severe chest pain still triggers red flags."""
    print("\n" + "="*70)
    print("TEST F: PHASE 2A RED FLAG REGRESSION")
    print("="*70)
    
    state = create_fresh_state()
    messages = [
        "I have severe chest pain",
        "sharp and pressure",
        "since this morning",
        "very severe and worsening"
    ]
    
    final_state = run_conversation(state, messages)
    
    print("\n" + "-"*70)
    print("VERIFICATION:")
    print("-"*70)
    print(f"Red Flag Status: {final_state.get('red_flag_status')}")
    print(f"Immediate Attention Required: {final_state.get('immediate_attention_required')}")
    print(f"Red Flags Detected: {final_state.get('red_flags')}")
    
    # Validation
    assert final_state.get('red_flag_status') == "red_flags_detected", "Severe chest pain should trigger red flags"
    assert final_state.get('immediate_attention_required') == True, "Severe chest pain should require immediate attention"
    assert len(final_state.get('red_flags', [])) > 0, "Should have red flags detected"
    
    print("\n[PASS] RED FLAG REGRESSION TEST PASSED")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 1B ADAPTIVE INTAKE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Test A: Stomach Pain", test_stomach_pain),
        ("Test B: Fever", test_fever),
        ("Test C: Cough", test_cough),
        ("Test D: Headache", test_headache),
        ("Test E: Duplicate Prevention", test_duplicate_prevention),
        ("Test F: Red Flag Regression", test_red_flags_regression),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "PASSED"))
        except AssertionError as e:
            print(f"\n[FAIL] {test_name} FAILED: {e}")
            results.append((test_name, f"FAILED: {e}"))
        except Exception as e:
            print(f"\n[FAIL] {test_name} ERROR: {e}")
            results.append((test_name, f"ERROR: {e}"))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, result in results:
        status = "[PASS]" if "PASSED" in result else "[FAIL]"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for _, r in results if r == "PASSED")
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED")


if __name__ == "__main__":
    main()
