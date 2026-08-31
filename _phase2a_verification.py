from app.workflow import build_vaidyaarc_graph
from app.red_flag_rules import evaluate_red_flags
import json


def base_state():
    return {
        'patient_id': 'TEST001',
        'session_id': 'SESSION001',
        'language': 'English',
        'patient_profile': {'age': 30, 'medical_conditions': [], 'allergies': []},
        'previous_history': [],
        'conversation_history': [],
        'extracted_information': {},
        'chief_complaint': None,
        'nature_of_pain': None,
        'location': None,
        'duration': None,
        'severity': None,
        'associated_symptoms': [],
        'current_message': '',
        'conversation_message': None,
        'next_question': None,
        'missing_information': [],
        'information_complete': False,
        'red_flag_status': None,
        'red_flags': [],
        'red_flag_evidence': [],
        'immediate_attention_required': False,
        'red_flag_rule_hits': [],
    }


graph = build_vaidyaarc_graph()

cases = [
    (
        'A. Severe chest pain',
        {
            **base_state(),
            'chief_complaint': 'chest pain',
            'nature_of_pain': 'pressure',
            'location': 'chest',
            'duration': 'sudden',
            'severity': 'severe',
            'associated_symptoms': ['shortness of breath'],
            'current_message': 'I have severe chest pain and shortness of breath',
            'information_complete': True,
            'missing_information': [],
        },
    ),
    (
        'B. Difficulty breathing',
        {
            **base_state(),
            'chief_complaint': 'breathing problem',
            'location': 'chest',
            'duration': 'today',
            'severity': 'moderate',
            'associated_symptoms': ['difficulty breathing'],
            'current_message': 'I have difficulty breathing',
            'information_complete': True,
            'missing_information': [],
        },
    ),
    (
        'C. Vomiting blood',
        {
            **base_state(),
            'chief_complaint': 'vomiting',
            'location': 'stomach',
            'duration': '2 hours',
            'severity': 'severe',
            'associated_symptoms': ['vomiting blood'],
            'current_message': 'I am vomiting blood',
            'information_complete': True,
            'missing_information': [],
        },
    ),
    (
        'D. Black stool',
        {
            **base_state(),
            'chief_complaint': 'black stool',
            'location': 'stool',
            'duration': '1 day',
            'severity': 'moderate',
            'associated_symptoms': ['black stool'],
            'current_message': 'I have black stool',
            'information_complete': True,
            'missing_information': [],
        },
    ),
    (
        'E. Fainting',
        {
            **base_state(),
            'chief_complaint': 'fainting',
            'location': 'general',
            'duration': 'this morning',
            'severity': 'severe',
            'associated_symptoms': ['passed out'],
            'current_message': 'I fainted and passed out',
            'information_complete': True,
            'missing_information': [],
        },
    ),
    (
        'F. Non-urgent stomach pain',
        {
            **base_state(),
            'chief_complaint': 'stomach pain',
            'nature_of_pain': 'burning',
            'location': 'upper abdomen',
            'duration': '2 days',
            'severity': 'moderate',
            'associated_symptoms': [],
            'current_message': 'I have burning stomach pain in my upper abdomen for 2 days. Moderate.',
            'information_complete': True,
            'missing_information': [],
        },
    ),
]

for label, state in cases:
    result = evaluate_red_flags(state)
    print(label)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print('---')

incomplete = base_state()
incomplete['current_message'] = 'I have stomach pain'
incomplete['conversation_message'] = 'What health problem are you experiencing?'
partial = graph.invoke(incomplete)
print('G. Incomplete intake')
print(json.dumps({
    'information_complete': partial.get('information_complete'),
    'next_question': partial.get('next_question'),
    'conversation_message': partial.get('conversation_message'),
    'red_flag_status': partial.get('red_flag_status'),
}, indent=2, ensure_ascii=False))
print('---')

phase1 = base_state(); phase1['current_message'] = 'I have stomach pain'; phase1 = graph.invoke(phase1)
phase2 = phase1.copy(); phase2['current_message'] = 'It feels like burning'; phase2 = graph.invoke(phase2)
phase3 = phase2.copy(); phase3['current_message'] = 'In my upper abdomen'; phase3 = graph.invoke(phase3)
phase4 = phase3.copy(); phase4['current_message'] = 'It started 2 days ago'; phase4 = graph.invoke(phase4)
phase5 = phase4.copy(); phase5['current_message'] = 'Moderate'; phase5 = graph.invoke(phase5)
print('H. Existing Phase 1 stomach-pain conversation')
print(json.dumps({
    'chief_complaint': phase5.get('chief_complaint'),
    'nature_of_pain': phase5.get('nature_of_pain'),
    'location': phase5.get('location'),
    'duration': phase5.get('duration'),
    'severity': phase5.get('severity'),
    'information_complete': phase5.get('information_complete'),
    'missing_information': phase5.get('missing_information'),
    'next_question': phase5.get('next_question'),
    'conversation_message': phase5.get('conversation_message'),
    'red_flag_status': phase5.get('red_flag_status'),
}, indent=2, ensure_ascii=False))
