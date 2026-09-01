"""
Phase 1B Debugging Tests - Comprehensive Validation
Tests for:
1. Natural language duration extraction
2. Completion logic correctness
3. Red flag routing integration
4. Regression testing
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


def run_single_turn(state, message):
    """Run one turn and return updated state."""
    graph = build_vaidyaarc_graph()
    state["current_message"] = message
    result = graph.invoke(state)
    state.update(result)
    return state


def run_conversation(state, messages):
    """Run a full conversation."""
    graph = build_vaidyaarc_graph()
    
    for message in messages:
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


print("\n" + "="*80)
print("PHASE 1B DEBUGGING TEST SUITE")
print("="*80)


# ============================================================================
# TEST GROUP 1: NATURAL LANGUAGE DURATION EXTRACTION
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 1: NATURAL LANGUAGE DURATION EXTRACTION")
print("="*80)

duration_test_cases = [
    ("today morning", "today morning"),
    ("this morning", "this morning"),
    ("1 day ago", "1 day ago"),
    ("yesterday", "yesterday"),
    ("since yesterday", "since yesterday"),
    ("for two days", "for two days"),
    ("since this morning", "since this morning"),
]

duration_tests_passed = 0
duration_tests_failed = []

for patient_response, expected_duration in duration_test_cases:
    test_name = f"Duration: '{patient_response}'"
    try:
        state = create_fresh_state()
        
        # Set up: patient has fever, we're asking about duration
        state["chief_complaint"] = "fever"
        state["conversation_message"] = "When did the fever start?"
        state["missing_information"] = ["duration", "severity"]
        state["questions_asked"] = []
        
        # Patient answers duration question
        state = run_single_turn(state, patient_response)
        
        # Extract duration from state
        actual_duration = state.get("duration")
        
        # Check result
        if actual_duration is not None and actual_duration.lower() == expected_duration.lower():
            print(f"[PASS] {test_name}")
            print(f"  Extracted: '{actual_duration}'")
            duration_tests_passed += 1
        else:
            print(f"[FAIL] {test_name}")
            print(f"  Expected: '{expected_duration}'")
            print(f"  Got: '{actual_duration}'")
            duration_tests_failed.append(test_name)
    
    except Exception as e:
        print(f"[ERROR] {test_name}: {e}")
        duration_tests_failed.append(test_name)

print(f"\nDuration Extraction Summary: {duration_tests_passed}/{len(duration_test_cases)} passed")
if duration_tests_failed:
    print("Failed tests:")
    for test in duration_tests_failed:
        print(f"  - {test}")


# ============================================================================
# TEST GROUP 2: COMPLETION LOGIC
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 2: COMPLETION LOGIC VALIDATION")
print("="*80)

# Test 2A: Incomplete information should never produce completion message
print("\n--- Test 2A: Incomplete Data Should NOT Produce Completion Message ---")
state = create_fresh_state()
messages = [
    "I have severe chest pain",
    "sharp",
    "in my chest",
    "very severe"
    # Missing duration - should NOT complete
]

for msg in messages:
    print(f"\nPatient: {msg}")
    state["current_message"] = msg
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    state.update(result)
    
    print(f"  Information Complete: {state.get('information_complete')}")
    print(f"  Missing Information: {state.get('missing_information')}")
    print(f"  Response: {state.get('conversation_message', '(no message)')}")
    
    # Check invariant: if missing_information is not empty, we should NEVER see completion message
    if state.get("missing_information") and state.get("missing_information"):
        # Some fields still missing
        response = state.get("conversation_message", "")
        if "Thank you. I have collected" in response and not state.get("information_complete"):
            print("  [FAIL] Completion message sent while information incomplete!")
        else:
            print("  [OK] No premature completion message")

# Test 2B: Complete information should produce completion message
print("\n--- Test 2B: Complete Data SHOULD Produce Completion/Red-Flag Evaluation ---")
state = create_fresh_state()
messages = [
    "I have fever",
    "3 days ago",
    "high"
]

for msg in messages:
    state["current_message"] = msg
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    state.update(result)

print(f"Final State:")
print(f"  Chief Complaint: {state.get('chief_complaint')}")
print(f"  Duration: {state.get('duration')}")
print(f"  Severity: {state.get('severity')}")
print(f"  Information Complete: {state.get('information_complete')}")
print(f"  Missing Information: {state.get('missing_information')}")
print(f"  Response: {state.get('conversation_message', '(no message)')}")

if state.get('information_complete'):
    print("  [PASS] Information marked complete when all required fields present")
else:
    print("  [FAIL] Information should be complete!")


# ============================================================================
# TEST GROUP 3: RED FLAG INTEGRATION
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 3: RED FLAG INTEGRATION")
print("="*80)

# Test 3A: Severe chest pain with complete data should trigger red flags
print("\n--- Test 3A: Severe Chest Pain (Emergency) ---")
state = create_fresh_state()
messages = [
    "I have severe chest pain",
    "sharp",
    "center of my chest",
    "today",
    "very severe"
]

for msg in messages:
    state["current_message"] = msg
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    state.update(result)

print(f"\nFinal Red Flag Status:")
print(f"  Red Flag Status: {state.get('red_flag_status')}")
print(f"  Immediate Attention Required: {state.get('immediate_attention_required')}")
print(f"  Red Flags: {state.get('red_flags')}")

if state.get('red_flag_status') == 'red_flags_detected':
    print("  [PASS] Red flags correctly detected for severe chest pain")
else:
    print("  [FAIL] Red flags should be detected for severe chest pain!")

# Test 3B: Mild fever should NOT trigger red flags
print("\n--- Test 3B: Mild Fever (No Emergency) ---")
state = create_fresh_state()
messages = [
    "I have fever",
    "2 days ago",
    "mild"
]

for msg in messages:
    state["current_message"] = msg
    graph = build_vaidyaarc_graph()
    result = graph.invoke(state)
    state.update(result)

print(f"\nFinal Red Flag Status:")
print(f"  Red Flag Status: {state.get('red_flag_status')}")
print(f"  Immediate Attention Required: {state.get('immediate_attention_required')}")
print(f"  Red Flags: {state.get('red_flags')}")

if state.get('red_flag_status') == 'no_obvious_red_flags':
    print("  [PASS] No red flags for mild fever")
else:
    print("  [FAIL] Mild fever should not trigger red flags!")


# ============================================================================
# TEST GROUP 4: REGRESSION TESTS
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 4: REGRESSION TESTS")
print("="*80)

# Test 4A: Stomach pain original flow
print("\n--- Test 4A: Stomach Pain (Phase 1 Original Flow) ---")
state = create_fresh_state()
messages = [
    "I have stomach pain",
    "It feels like burning",
    "In my upper abdomen",
    "It started 2 days ago",
    "Moderate"
]

final_state = run_conversation(state, messages)

print(f"\nFinal State Check:")
print(f"  Chief Complaint: {final_state.get('chief_complaint')}")
print(f"  Nature of Pain: {final_state.get('nature_of_pain')}")
print(f"  Location: {final_state.get('location')}")
print(f"  Duration: {final_state.get('duration')}")
print(f"  Severity: {final_state.get('severity')}")
print(f"  Information Complete: {final_state.get('information_complete')}")
print(f"  Red Flag Status: {final_state.get('red_flag_status')}")

checks = [
    (final_state.get('chief_complaint') == "stomach pain", "Chief complaint"),
    (final_state.get('nature_of_pain') == "burning", "Nature of pain"),
    (final_state.get('location') == "upper abdomen", "Location"),
    (final_state.get('duration') == "2 days", "Duration"),
    ((final_state.get('severity') or "").lower() == "moderate", "Severity"),
    (final_state.get('information_complete') == True, "Information complete"),
    (final_state.get('red_flag_status') == 'no_obvious_red_flags', "No red flags"),
]

for passed, label in checks:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} {label}")

# Test 4B: Duplicate question prevention
print("\n--- Test 4B: Duplicate Question Prevention ---")
state = create_fresh_state()
graph = build_vaidyaarc_graph()

# Turn 1
state["current_message"] = "I have a fever"
result = graph.invoke(state)
state.update(result)
q1 = state.get("next_question")
qa1 = list(state.get("questions_asked", []))
print(f"Turn 1: Asked about '{qa1[-1] if qa1 else 'none'}': {q1}")

# Turn 2
state["current_message"] = "3 days ago"
result = graph.invoke(state)
state.update(result)
q2 = state.get("next_question")
qa2 = list(state.get("questions_asked", []))
print(f"Turn 2: Asked about '{qa2[-1] if len(qa2) > 1 else 'same'}': {q2}")

# Check no duplicates
all_asked = state.get("questions_asked", [])
if len(all_asked) == len(set(all_asked)):
    print(f"  [PASS] No duplicate questions (asked: {all_asked})")
else:
    print(f"  [FAIL] Duplicate questions detected (asked: {all_asked})")


print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Duration Extraction: {duration_tests_passed}/{len(duration_test_cases)} passed")
if duration_tests_failed:
    print(f"  Failed: {', '.join(duration_tests_failed)}")
print("\nManual Inspection Required For:")
print("  - Completion logic (check no premature messages)")
print("  - Red flag integration")
print("  - Regression tests")
