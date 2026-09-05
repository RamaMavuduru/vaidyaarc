"""
Phase 8B: Synthetic Ayurveda Remedy and Safety Screening Fixtures.

Contains 12 standardized test scenarios for testing the Phase 8B Controlled
Ayurveda Knowledge System, retriever, safety gate, recommendation engine,
and orchestrator integration.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    PatientLocationDTO,
)


# 1. Mild dry cough - eligible for CCRAS home remedy
FIXTURE_AYUR_01_MILD_COUGH = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_001",
    episode_id="EP_AYUR_001",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        original_language="en",
        english_text="mild",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=28,
        sex="male",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "dry cough",
        "nature_of_pain": "throat irritation",
        "location": "throat",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": ["mild throat irritation"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 10,
    },
)

# 2. Mild indigestion / loss of appetite - eligible for CCRAS / API remedies
FIXTURE_AYUR_02_INDIGESTION = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_002",
    episode_id="EP_AYUR_002",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild bloating after meals",
        original_language="en",
        english_text="mild bloating after meals",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=42,
        sex="female",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "indigestion",
        "nature_of_pain": "mild fullness",
        "location": "abdomen",
        "duration": "3 days",
        "severity": "mild",
        "associated_symptoms": ["loss of appetite"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 8,
    },
)

# 3. Emergency Red Flag - Crushing chest pain -> BLOCKED
FIXTURE_AYUR_03_EMERGENCY_BLOCKED = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_003",
    episode_id="EP_AYUR_003",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="crushing chest pain radiating to left arm and sweating",
        original_language="en",
        english_text="crushing chest pain radiating to left arm and sweating",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=58,
        sex="male",
        medical_conditions=["Hypertension"],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "crushing chest pain",
        "nature_of_pain": "crushing",
        "location": "chest",
        "duration": "30 minutes",
        "severity": "severe",
        "associated_symptoms": ["sweating", "left arm pain"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "emergency_red_flag",
        "immediate_attention_required": True,
        "risk_level": "URGENT",
        "risk_score": 85,
    },
)

# 4. High Risk Case - High fever with altered sensorium -> BLOCKED
FIXTURE_AYUR_04_HIGH_RISK_BLOCKED = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_004",
    episode_id="EP_AYUR_004",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="high fever and persistent vomiting",
        original_language="en",
        english_text="high fever and persistent vomiting",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=65,
        sex="female",
        medical_conditions=["Diabetes"],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "high fever",
        "nature_of_pain": "generalized aches",
        "location": "whole body",
        "duration": "5 days",
        "severity": "high",
        "associated_symptoms": ["vomiting", "confusion"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "potential_risk_flag",
        "immediate_attention_required": False,
        "risk_level": "HIGH",
        "risk_score": 52,
    },
)

# 5. Severe symptom score (9/10) -> BLOCKED
FIXTURE_AYUR_05_SEVERE_PAIN_BLOCKED = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_005",
    episode_id="EP_AYUR_005",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="worst headache of my life 9 out of 10",
        original_language="en",
        english_text="worst headache of my life 9 out of 10",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=31,
        sex="male",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "severe headache",
        "nature_of_pain": "throbbing unbearable",
        "location": "head",
        "duration": "1 hour",
        "severity": "9/10",
        "associated_symptoms": ["nausea"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "potential_risk_flag",
        "immediate_attention_required": False,
        "risk_level": "HIGH",
        "risk_score": 45,
    },
)

# 6. Allergy constraint - Patient allergic to Ginger/Shunti
FIXTURE_AYUR_06_ALLERGY_CONSTRAINT = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_006",
    episode_id="EP_AYUR_006",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild cough",
        original_language="en",
        english_text="mild cough",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=25,
        sex="female",
        medical_conditions=[],
        allergies=["ginger", "shunti", "ardraka"],
    ),
    state_snapshot={
        "chief_complaint": "cough",
        "nature_of_pain": "tickling in throat",
        "location": "throat",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    },
)

# 7. Secondary Literature Only - eCAM 2013 Diabetes formulation
FIXTURE_AYUR_07_SECONDARY_EVIDENCE = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_007",
    episode_id="EP_AYUR_007",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild high blood sugar support",
        original_language="en",
        english_text="mild high blood sugar support",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=50,
        sex="male",
        medical_conditions=["Type 2 Diabetes"],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "diabetes support",
        "nature_of_pain": "none",
        "location": "metabolic",
        "duration": "1 year",
        "severity": "mild",
        "associated_symptoms": ["polyuria", "prameha"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 10,
    },
)

# 8. Unmapped rare symptom -> Insufficient Information
FIXTURE_AYUR_08_UNMAPPED_SYMPTOM = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_008",
    episode_id="EP_AYUR_008",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="floating purple dots and flashes in left eye",
        original_language="en",
        english_text="floating purple dots and flashes in left eye",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=39,
        sex="female",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "floating purple dots in vision",
        "nature_of_pain": "visual floaters",
        "location": "left eye",
        "duration": "1 day",
        "severity": "mild",
        "associated_symptoms": ["flashes of light"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    },
)

# 9. Female of childbearing age with unknown pregnancy status -> Requires Clinician Review
FIXTURE_AYUR_09_UNKNOWN_PREGNANCY = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_009",
    episode_id="EP_AYUR_009",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild constipation for 2 days",
        original_language="en",
        english_text="mild constipation for 2 days",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=27,
        sex="female",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "constipation",
        "nature_of_pain": "mild discomfort",
        "location": "lower abdomen",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    },
)

# 10. Authority Ranking Test - Multiple matches (CCRAS primary vs eCAM secondary)
FIXTURE_AYUR_10_AUTHORITY_RANKING = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_010",
    episode_id="EP_AYUR_010",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild fever and cough",
        original_language="en",
        english_text="mild fever and cough",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=30,
        sex="male",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "cough",
        "nature_of_pain": "throat irritation",
        "location": "throat",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": ["mild fever", "jwara"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 12,
    },
)

# 11. Preserved Source Dosage & Non-Prescription Disclaimer
FIXTURE_AYUR_11_DOSAGE_PRESERVATION = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_011",
    episode_id="EP_AYUR_011",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild dry cough and throat irritation",
        original_language="en",
        english_text="mild dry cough and throat irritation",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=35,
        sex="male",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "dry cough",
        "nature_of_pain": "scratchy throat",
        "location": "throat",
        "duration": "1 day",
        "severity": "mild",
        "associated_symptoms": ["hoarseness"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 6,
    },
)

# 12. Complete Phase 7 & Phase 8B Dual Representation & Remedy Coexistence
FIXTURE_AYUR_12_COEXISTENCE = NormalizedClinicalInputDTO(
    patient_id="PAT_AYUR_012",
    episode_id="EP_AYUR_012",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild acidity and burning in stomach",
        original_language="en",
        english_text="mild acidity and burning in stomach",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=40,
        sex="female",
        medical_conditions=[],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "acidity",
        "nature_of_pain": "burning sensation",
        "location": "epigastrium",
        "duration": "3 days",
        "severity": "mild",
        "associated_symptoms": ["sour belching", "amlapitta"],
        "missing_information": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 10,
    },
)

AYURVEDA_FIXTURES = {
    "mild_cough": FIXTURE_AYUR_01_MILD_COUGH,
    "indigestion": FIXTURE_AYUR_02_INDIGESTION,
    "emergency_blocked": FIXTURE_AYUR_03_EMERGENCY_BLOCKED,
    "high_risk_blocked": FIXTURE_AYUR_04_HIGH_RISK_BLOCKED,
    "severe_pain_blocked": FIXTURE_AYUR_05_SEVERE_PAIN_BLOCKED,
    "allergy_constraint": FIXTURE_AYUR_06_ALLERGY_CONSTRAINT,
    "secondary_evidence": FIXTURE_AYUR_07_SECONDARY_EVIDENCE,
    "unmapped_symptom": FIXTURE_AYUR_08_UNMAPPED_SYMPTOM,
    "unknown_pregnancy": FIXTURE_AYUR_09_UNKNOWN_PREGNANCY,
    "authority_ranking": FIXTURE_AYUR_10_AUTHORITY_RANKING,
    "dosage_preservation": FIXTURE_AYUR_11_DOSAGE_PRESERVATION,
    "coexistence": FIXTURE_AYUR_12_COEXISTENCE,
}

