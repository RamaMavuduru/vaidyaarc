"""
Phase 8A: Synthetic Clinical Input Fixtures.

Contains 11 standardized, integration-independent test scenarios
conforming to NormalizedClinicalInputDTO for robust offline testing of the
VaidyaArc Brain and Orchestrator.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    PatientLocationDTO,
    DocumentDTO,
)


# 1. Basic English completed intake
FIXTURE_ENGLISH_BASIC = NormalizedClinicalInputDTO(
    patient_id="PAT_ENG_001",
    episode_id="EP_ENG_001",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
        provenance="patient_typed"
    ),
    patient_profile=PatientProfileDTO(
        age=34,
        sex="female",
        medical_conditions=[],
        allergies=[]
    ),
    patient_location=PatientLocationDTO(
        city="Hyderabad",
        pincode="500001"
    ),
    conversation_context={
        "turn_count": 5,
        "previous_question": "How severe is the pain?"
    },
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "2 days",
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["severity"],
        "information_complete": False,
        "conversation_message": "How severe is the pain?",
        "conversation_history": [
            {"role": "patient", "content": "I have stomach pain"},
            {"role": "assistant", "content": "Can you describe what the pain feels like?"},
            {"role": "patient", "content": "burning"},
            {"role": "assistant", "content": "Where exactly are you feeling the pain?"},
            {"role": "patient", "content": "upper abdomen"},
            {"role": "assistant", "content": "When did this problem start?"},
            {"role": "patient", "content": "2 days ago"},
            {"role": "assistant", "content": "How severe is the pain?"}
        ]
    }
)

# 2. Translated Telugu voice input with NMT provenance
FIXTURE_TELUGU_TRANSLATED = NormalizedClinicalInputDTO(
    patient_id="PAT_TEL_002",
    episode_id="EP_TEL_002",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="తీవ్రమైన",
        original_language="te-IN",
        english_text="severe",
        source="patient",
        confidence=0.96,
        provenance="synthetic_stt_nmt"
    ),
    patient_profile=PatientProfileDTO(
        age=45,
        sex="male"
    ),
    conversation_context={
        "turn_count": 4,
        "previous_question": "How severe is the headache?"
    },
    state_snapshot={
        "chief_complaint": "headache",
        "location": "head",
        "duration": "2 days",
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["severity"],
        "information_complete": False,
        "conversation_message": "How severe is the headache?",
    }
)

# 3. Patient input with normal OCR lab report document
FIXTURE_OCR_NORMAL = NormalizedClinicalInputDTO(
    patient_id="PAT_OCR_003",
    episode_id="EP_OCR_003",
    channel="kiosk",
    message=NormalizedMessageDTO(
        original_text="3 days",
        original_language="en",
        english_text="3 days"
    ),
    conversation_context={
        "turn_count": 2,
        "previous_question": "When did the cough start?"
    },
    state_snapshot={
        "chief_complaint": "cough",
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["duration"],
        "information_complete": False,
        "conversation_message": "When did the cough start?",
    },
    documents=[
        DocumentDTO(
            document_id="DOC_CBC_NORM",
            document_type="lab_report",
            document_date="2026-03-01",
            extracted_text="Complete Blood Count: Hemoglobin 14.2 g/dL (Normal: 13.0-17.0), WBC 6500 /mcL (Normal: 4000-11000), Platelets 220000 /mcL",
            structured_biomarkers=[
                {"biomarker": "Hemoglobin", "value": 14.2, "unit": "g/dL", "status": "normal"},
                {"biomarker": "WBC", "value": 6500, "unit": "/mcL", "status": "normal"},
                {"biomarker": "Platelets", "value": 220000, "unit": "/mcL", "status": "normal"}
            ],
            provenance="synthetic_ocr"
        )
    ]
)

# 4. Patient input with abnormal OCR lab report document
FIXTURE_OCR_ABNORMAL = NormalizedClinicalInputDTO(
    patient_id="PAT_OCR_004",
    episode_id="EP_OCR_004",
    channel="kiosk",
    message=NormalizedMessageDTO(
        original_text="severe",
        original_language="en",
        english_text="severe"
    ),
    conversation_context={
        "turn_count": 3,
        "previous_question": "How high is your fever or how severe is it?"
    },
    state_snapshot={
        "chief_complaint": "fever",
        "duration": "1 week",
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["severity"],
        "information_complete": False,
        "conversation_message": "How high is your fever or how severe is it?",
    },
    documents=[
        DocumentDTO(
            document_id="DOC_LAB_ABN",
            document_type="lab_report",
            document_date="2026-03-02",
            extracted_text="Investigation Report: Hemoglobin 7.1 g/dL (CRITICAL LOW), Fasting Blood Glucose 240 mg/dL (HIGH)",
            structured_biomarkers=[
                {"biomarker": "Hemoglobin", "value": 7.1, "unit": "g/dL", "status": "critical_low"},
                {"biomarker": "Fasting Blood Glucose", "value": 240, "unit": "mg/dL", "status": "high"}
            ],
            provenance="synthetic_ocr"
        )
    ]
)

# 5. Longitudinal patient with previous encounter showing stable trajectory
FIXTURE_PREVIOUS_ENCOUNTER_STABLE = NormalizedClinicalInputDTO(
    patient_id="PAT_ENC_005",
    episode_id="EP_ENC_005",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate"
    ),
    conversation_context={
        "turn_count": 4,
        "previous_question": "How severe is the headache?"
    },
    state_snapshot={
        "chief_complaint": "headache",
        "location": "head",
        "duration": "2 days",
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["severity"],
        "information_complete": False,
        "conversation_message": "How severe is the headache?",
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_001",
            "timestamp": "2026-02-25T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "moderate",
            "duration": "1 day",
            "risk_score": 30.0,
            "risk_level": "moderate"
        }
    ]
)

# 6. Longitudinal patient with previous encounter showing worsening trajectory
FIXTURE_PREVIOUS_ENCOUNTER_WORSENING = NormalizedClinicalInputDTO(
    patient_id="PAT_ENC_006",
    episode_id="EP_ENC_006",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="severe",
        original_language="en",
        english_text="severe"
    ),
    conversation_context={
        "turn_count": 3,
        "previous_question": "How high is your fever or how severe is it?"
    },
    state_snapshot={
        "chief_complaint": "fever",
        "duration": "3 days",
        "severity": None,
        "associated_symptoms": ["vomiting"],
        "missing_information": ["severity"],
        "information_complete": False,
        "conversation_message": "How high is your fever or how severe is it?",
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_002",
            "timestamp": "2026-02-20T10:00:00Z",
            "chief_complaint": "fever",
            "severity": "mild",
            "duration": "1 day",
            "risk_score": 15.0,
            "risk_level": "low"
        }
    ]
)

# 7. Multi-turn conversation context
FIXTURE_PREVIOUS_CONVERSATION_CONTEXT = NormalizedClinicalInputDTO(
    patient_id="PAT_CONV_007",
    episode_id="EP_CONV_007",
    channel="web",
    message=NormalizedMessageDTO(
        original_text="since yesterday",
        original_language="en",
        english_text="since yesterday"
    ),
    conversation_context={
        "turn_count": 2,
        "previous_question": "When did the fever start?"
    },
    previous_conversations=[
        {"role": "patient", "text": "I have fever"},
        {"role": "assistant", "text": "When did the fever start?"}
    ],
    state_snapshot={
        "chief_complaint": "fever",
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["duration", "severity"],
        "conversation_message": "When did the fever start?",
        "conversation_history": [
            {"role": "patient", "content": "I have fever"},
            {"role": "assistant", "content": "When did the fever start?"}
        ]
    }
)

# 8. Patient profile with documented chronic conditions and allergies
FIXTURE_KNOWN_ALLERGIES_CONDITIONS = NormalizedClinicalInputDTO(
    patient_id="PAT_ALLERGY_008",
    episode_id="EP_ALLERGY_008",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="4 days",
        original_language="en",
        english_text="4 days"
    ),
    conversation_context={
        "turn_count": 2,
        "previous_question": "When did the cough start?"
    },
    state_snapshot={
        "chief_complaint": "cough",
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "missing_information": ["duration"],
        "information_complete": False,
        "conversation_message": "When did the cough start?",
    },
    patient_profile=PatientProfileDTO(
        age=58,
        sex="female",
        medical_conditions=["Hypertension", "Type 2 Diabetes"],
        allergies=["Penicillin", "Sulfa drugs"],
        chronic_medications=[
            {"name": "Amlodipine", "dosage": "5mg daily"},
            {"name": "Metformin", "dosage": "500mg twice daily"}
        ],
        surgical_history=["Appendectomy (2015)"],
        family_history=["Maternal history of myocardial infarction"]
    )
)

# 9. Emergency red flag input requiring immediate non-LLM triage
FIXTURE_RED_FLAG_EMERGENCY = NormalizedClinicalInputDTO(
    patient_id="PAT_EMERG_009",
    episode_id="EP_EMERG_009",
    channel="kiosk",
    message=NormalizedMessageDTO(
        original_text="I have severe crushing chest pain radiating to my left arm with cold sweating and shortness of breath",
        original_language="en",
        english_text="I have severe crushing chest pain radiating to my left arm with cold sweating and shortness of breath"
    ),
    patient_profile=PatientProfileDTO(
        age=62,
        sex="male"
    ),
    patient_location=PatientLocationDTO(
        city="Hyderabad",
        pincode="500003"
    )
)

# 10. Vague / unspecified input requiring adaptive clarification
FIXTURE_VAGUE_UNSPECIFIED = NormalizedClinicalInputDTO(
    patient_id="PAT_VAGUE_010",
    episode_id="EP_VAGUE_010",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="I don't feel well today",
        original_language="en",
        english_text="I don't feel well today"
    )
)

# 11. Unmapped Ayurvedic input (symptoms without classical Ayurvedic concept match)
FIXTURE_UNMAPPED_AYURVEDIC = NormalizedClinicalInputDTO(
    patient_id="PAT_UNMAPPED_011",
    episode_id="EP_UNMAPPED_011",
    channel="web",
    message=NormalizedMessageDTO(
        original_text="1 day",
        original_language="en",
        english_text="1 day"
    ),
    conversation_context={
        "turn_count": 2,
        "previous_question": "When did this problem start?"
    },
    state_snapshot={
        "chief_complaint": "tingling in left pinky toe",
        "duration": None,
        "severity": "mild",
        "associated_symptoms": [],
        "missing_information": ["duration"],
        "information_complete": False,
        "conversation_message": "When did this problem start?",
    }
)

ALL_FIXTURES = {
    "english_basic": FIXTURE_ENGLISH_BASIC,
    "telugu_translated": FIXTURE_TELUGU_TRANSLATED,
    "ocr_normal": FIXTURE_OCR_NORMAL,
    "ocr_abnormal": FIXTURE_OCR_ABNORMAL,
    "previous_encounter_stable": FIXTURE_PREVIOUS_ENCOUNTER_STABLE,
    "previous_encounter_worsening": FIXTURE_PREVIOUS_ENCOUNTER_WORSENING,
    "previous_conversation_context": FIXTURE_PREVIOUS_CONVERSATION_CONTEXT,
    "known_allergies_conditions": FIXTURE_KNOWN_ALLERGIES_CONDITIONS,
    "red_flag_emergency": FIXTURE_RED_FLAG_EMERGENCY,
    "vague_unspecified": FIXTURE_VAGUE_UNSPECIFIED,
    "unmapped_ayurvedic": FIXTURE_UNMAPPED_AYURVEDIC,
}

