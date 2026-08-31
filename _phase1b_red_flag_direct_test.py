"""
Direct red flag regression test - bypasses extraction to test red flag logic directly.
"""

from app.red_flag_rules import evaluate_red_flags
from app.state import VaidyaArcState


def test_red_flags_direct():
    """Test that Phase 2A red flags still work correctly with adaptive intake."""
    
    print("\n" + "="*70)
    print("PHASE 2A RED FLAG DIRECT TEST")
    print("="*70)
    
    # Test 1: Severe chest pain should trigger red flags
    print("\n--- Test 1: Severe Chest Pain ---")
    state = {
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "sharp",
        "location": "chest",
        "duration": "started today",
        "severity": "very severe",
        "associated_symptoms": [],
        "current_message": "I have severe chest pain, sharp, in my chest, started today, very severe",
        "information_complete": True,
    }
    
    result = evaluate_red_flags(state)
    print(f"Red Flag Status: {result['red_flag_status']}")
    print(f"Immediate Attention Required: {result['immediate_attention_required']}")
    print(f"Red Flags Detected: {result['red_flags']}")
    
    assert result['red_flag_status'] == "red_flags_detected", "Severe chest pain should trigger red flags"
    assert result['immediate_attention_required'] == True, "Severe chest pain should require immediate attention"
    print("[PASS] Severe chest pain red flag test passed")
    
    # Test 2: Difficulty breathing should trigger red flags
    print("\n--- Test 2: Difficulty Breathing ---")
    state = {
        "chief_complaint": "difficulty breathing",
        "duration": "1 hour",
        "severity": "severe",
        "associated_symptoms": [],
        "current_message": "I have difficulty breathing",
        "information_complete": True,
    }
    
    result = evaluate_red_flags(state)
    print(f"Red Flag Status: {result['red_flag_status']}")
    print(f"Immediate Attention Required: {result['immediate_attention_required']}")
    print(f"Red Flags Detected: {result['red_flags']}")
    
    assert result['red_flag_status'] == "red_flags_detected", "Difficulty breathing should trigger red flags"
    assert result['immediate_attention_required'] == True, "Difficulty breathing should require immediate attention"
    print("[PASS] Difficulty breathing red flag test passed")
    
    # Test 3: Vomiting blood should trigger red flags
    print("\n--- Test 3: Vomiting Blood ---")
    state = {
        "chief_complaint": "vomiting blood",
        "duration": "30 minutes",
        "severity": "severe",
        "associated_symptoms": [],
        "current_message": "I am vomiting blood",
        "information_complete": True,
    }
    
    result = evaluate_red_flags(state)
    print(f"Red Flag Status: {result['red_flag_status']}")
    print(f"Immediate Attention Required: {result['immediate_attention_required']}")
    print(f"Red Flags Detected: {result['red_flags']}")
    
    assert result['red_flag_status'] == "red_flags_detected", "Vomiting blood should trigger red flags"
    assert result['immediate_attention_required'] == True, "Vomiting blood should require immediate attention"
    print("[PASS] Vomiting blood red flag test passed")
    
    # Test 4: Fainting should trigger red flags
    print("\n--- Test 4: Fainting ---")
    state = {
        "chief_complaint": "fainting",
        "duration": "5 minutes ago",
        "severity": "severe",
        "associated_symptoms": [],
        "current_message": "I fainted",
        "information_complete": True,
    }
    
    result = evaluate_red_flags(state)
    print(f"Red Flag Status: {result['red_flag_status']}")
    print(f"Immediate Attention Required: {result['immediate_attention_required']}")
    print(f"Red Flags Detected: {result['red_flags']}")
    
    assert result['red_flag_status'] == "red_flags_detected", "Fainting should trigger red flags"
    assert result['immediate_attention_required'] == True, "Fainting should require immediate attention"
    print("[PASS] Fainting red flag test passed")
    
    # Test 5: No red flags for mild fever
    print("\n--- Test 5: No Red Flags for Mild Fever ---")
    state = {
        "chief_complaint": "fever",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],
        "current_message": "I have a mild fever",
        "information_complete": True,
    }
    
    result = evaluate_red_flags(state)
    print(f"Red Flag Status: {result['red_flag_status']}")
    print(f"Immediate Attention Required: {result['immediate_attention_required']}")
    print(f"Red Flags Detected: {result['red_flags']}")
    
    assert result['red_flag_status'] == "no_obvious_red_flags", "Mild fever should not trigger red flags"
    assert result['immediate_attention_required'] == False, "Mild fever should not require immediate attention"
    print("[PASS] No red flags for mild fever test passed")
    
    print("\n" + "="*70)
    print("ALL DIRECT RED FLAG TESTS PASSED!")
    print("Phase 2A red flag system is working correctly with adaptive intake.")
    print("="*70)


if __name__ == "__main__":
    test_red_flags_direct()
