#!/usr/bin/env python3
"""Direct validation of Phase 2B risk convergence without LLM processing."""

from app.nodes import risk_convergence

# Test HIGH RISK case
high_risk_state = {
    'chief_complaint': 'abdominal pain',
    'nature_of_pain': 'sharp',
    'location': 'upper abdomen',
    'duration': '5 days',
    'severity': 'severe',
    'information_complete': True,
    'missing_information': [],
    'associated_symptoms': ['nausea', 'fatigue'],
    'red_flag_status': 'no_obvious_red_flags',
    'red_flags': [],
    'red_flag_evidence': [],
    'immediate_attention_required': False,
    'patient_profile': {'age': 30, 'medical_conditions': []},
    'previous_history': [],
    'current_message': 'I have severe abdominal pain for 5 days and it is worsening'
}

result = risk_convergence(high_risk_state)
level = result.get('risk_level')
score = result.get('risk_score', 0)
assert level == 'URGENT', 'Expected URGENT (worsening + severe + multiple), got ' + str(level)
assert score >= 40, 'Expected score >= 40, got ' + str(score)
print('HIGH SEVERITY + WORSENING CASE: PASS (level=' + level + ', score=' + str(score) + ')')

# Test all cases
test_cases = [
    ({'chief_complaint': 'fever', 'duration': '2 days', 'severity': 'mild', 'information_complete': True, 'missing_information': [], 'associated_symptoms': [], 'red_flag_status': 'no_obvious_red_flags', 'immediate_attention_required': False, 'patient_profile': {'age': 30, 'medical_conditions': []}}, 'LOW', 0, 9),
    ({'chief_complaint': 'stomach pain', 'duration': '3 days', 'severity': 'moderate', 'nature_of_pain': 'burning', 'location': 'upper abdomen', 'information_complete': True, 'missing_information': [], 'associated_symptoms': ['nausea', 'fatigue'], 'red_flag_status': 'no_obvious_red_flags', 'immediate_attention_required': False, 'patient_profile': {'age': 30, 'medical_conditions': []}}, 'MODERATE', 10, 24),
    ({'chief_complaint': 'fever', 'duration': None, 'severity': None, 'information_complete': False, 'missing_information': ['duration', 'severity'], 'associated_symptoms': [], 'red_flag_status': 'no_obvious_red_flags', 'immediate_attention_required': False, 'patient_profile': {'age': 30, 'medical_conditions': []}}, 'INCOMPLETE', 0, 0),
    # Test true HIGH (25-39): severe fever + 3 days = 20 + 8 = 28
    ({'chief_complaint': 'fever', 'duration': '3 days', 'severity': 'severe', 'information_complete': True, 'missing_information': [], 'associated_symptoms': [], 'red_flag_status': 'no_obvious_red_flags', 'immediate_attention_required': False, 'patient_profile': {'age': 45, 'medical_conditions': []}, 'current_message': 'severe fever for 3 days'}, 'HIGH', 25, 39),
]

for state, expected_level, min_score, max_score in test_cases:
    result = risk_convergence(state)
    level = result.get('risk_level')
    score = result.get('risk_score', 0)
    assert level == expected_level, 'Expected ' + expected_level + ', got ' + level
    assert min_score <= score <= max_score, 'Expected score ' + str(min_score) + '-' + str(max_score) + ', got ' + str(score)
    print(expected_level + ' CASE: PASS (score=' + str(score) + ')')

print('\nPHASE_2B_DIRECT_VALIDATION_COMPLETE')
