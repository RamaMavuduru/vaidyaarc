"""
Phase 12: Dashavidha Atura Pariksha Test Fixtures.

Contains synthetic, deterministic clinical inputs designed to test all 10
parameters, negative safety invariants, epistemic boundaries, and integration points.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
)


FIXTURE_EMPTY_PROFILE = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_EMPTY",
    episode_id="EP_DV_EMPTY",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(),
    state_snapshot={
        "chief_complaint": "general evaluation",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_VAYA_BALYA = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_BALYA",
    episode_id="EP_DV_BALYA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(age=8),
    state_snapshot={
        "chief_complaint": "common cold",
        "duration": "2 days",
        "severity": "mild",
        "patient_profile": {"age": 8},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_VAYA_MADHYAMA = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_MADHYAMA",
    episode_id="EP_DV_MADHYAMA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(age=42),
    state_snapshot={
        "chief_complaint": "headache",
        "duration": "1 day",
        "severity": "moderate",
        "location": "forehead",
        "patient_profile": {"age": 42},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_VAYA_VRIDDHA = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_VRIDDHA",
    episode_id="EP_DV_VRIDDHA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(age=72),
    state_snapshot={
        "chief_complaint": "knee pain",
        "duration": "1 month",
        "severity": "moderate",
        "location": "knees",
        "nature_of_pain": "aching",
        "patient_profile": {"age": 72},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_VAYA_MISSING = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_MISSING_AGE",
    episode_id="EP_DV_MISSING_AGE",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(age=None),
    state_snapshot={
        "chief_complaint": "cough",
        "duration": "3 days",
        "severity": "mild",
        "patient_profile": {},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_PRAKRITI_REPORTED = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_PRAKRITI_REP",
    episode_id="EP_DV_PRAKRITI_REP",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(
        age=30,
        reported_prakriti="Pitta-Kapha",
    ),
    state_snapshot={
        "chief_complaint": "skin rash",
        "duration": "5 days",
        "severity": "mild",
        "reported_prakriti": "Pitta-Kapha",
        "patient_profile": {"age": 30, "reported_prakriti": "Pitta-Kapha"},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_PRAKRITI_UNASSESSED = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_PRAKRITI_UNASSESSED",
    episode_id="EP_DV_PRAKRITI_UNASSESSED",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(age=28),
    state_snapshot={
        "chief_complaint": "fever",
        "duration": "2 days",
        "severity": "moderate",
        "patient_profile": {"age": 28},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_BURNING_SENSATION = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_BURNING",
    episode_id="EP_DV_BURNING",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(age=35),
    state_snapshot={
        "chief_complaint": "burning sensation in stomach",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "1 week",
        "severity": "moderate",
        "associated_symptoms": ["acid reflux", "stomach pain"],
        "patient_profile": {"age": 35},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_PENICILLIN_ALLERGY = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_ALLERGY",
    episode_id="EP_DV_ALLERGY",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(
        age=45,
        allergies=["Penicillin", "Sulfa drugs"],
    ),
    state_snapshot={
        "chief_complaint": "skin itchiness",
        "duration": "2 days",
        "severity": "mild",
        "allergies": ["Penicillin", "Sulfa drugs"],
        "patient_profile": {"age": 45, "allergies": ["Penicillin", "Sulfa drugs"]},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_ANXIETY_DISTRESS = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_ANXIETY",
    episode_id="EP_DV_ANXIETY",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(
        age=29,
        social_history="High workplace stress, emotional distress",
    ),
    state_snapshot={
        "chief_complaint": "insomnia",
        "duration": "3 weeks",
        "severity": "moderate",
        "associated_symptoms": ["severe anxiety", "panic", "restlessness"],
        "social_history": "High workplace stress, emotional distress",
        "patient_profile": {"age": 29, "social_history": "High workplace stress, emotional distress"},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_AHARA_SHAKTI_APPETITE = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_AHARA",
    episode_id="EP_DV_AHARA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(age=38),
    state_snapshot={
        "chief_complaint": "poor appetite",
        "duration": "10 days",
        "severity": "mild",
        "associated_symptoms": ["post-meal bloating", "indigestion", "loss of appetite"],
        "patient_profile": {"age": 38},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_VYAYAMA_SHAKTI_FATIGUE = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_VYAYAMA",
    episode_id="EP_DV_VYAYAMA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(
        age=52,
        functional_status="Fatigue upon walking 100 meters",
    ),
    state_snapshot={
        "chief_complaint": "exertional fatigue",
        "duration": "2 weeks",
        "severity": "moderate",
        "associated_symptoms": ["exhaustion", "breathless on walking", "tiredness"],
        "functional_status": "Fatigue upon walking 100 meters",
        "patient_profile": {"age": 52, "functional_status": "Fatigue upon walking 100 meters"},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_LOW_HB_FATIGUE = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_LOW_HB",
    episode_id="EP_DV_LOW_HB",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(age=40),
    investigations=[{"test_name": "Hemoglobin", "result_value": 8.2, "unit": "g/dL"}],
    state_snapshot={
        "chief_complaint": "general weakness",
        "duration": "1 month",
        "severity": "moderate",
        "associated_symptoms": ["fatigue", "tiredness"],
        "investigations": [{"test_name": "Hemoglobin", "result_value": 8.2, "unit": "g/dL"}],
        "patient_profile": {"age": 40},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_MODERN_VITALS_PRAMANA = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_VITALS",
    episode_id="EP_DV_VITALS",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(
        age=34,
        vitals={"height": 178, "weight": 74, "bmi": 23.4},
    ),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "vitals": {"height": 178, "weight": 74, "bmi": 23.4},
        "patient_profile": {"age": 34, "vitals": {"height": 178, "weight": 74, "bmi": 23.4}},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_SATMYA_DIET = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_SATMYA",
    episode_id="EP_DV_SATMYA",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        english_text="mild",
    ),
    patient_profile=PatientProfileDTO(
        age=36,
        dietary_habits="Vegetarian diet, rice, lentils, seasonal vegetables",
    ),
    state_snapshot={
        "chief_complaint": "mild indigestion",
        "duration": "3 days",
        "severity": "mild",
        "dietary_habits": "Vegetarian diet, rice, lentils, seasonal vegetables",
        "patient_profile": {"age": 36, "dietary_habits": "Vegetarian diet, rice, lentils, seasonal vegetables"},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_EMERGENCY_RED_FLAG = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_EMERGENCY",
    episode_id="EP_DV_EMERGENCY",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="crushing chest pain radiating to left arm",
        english_text="crushing chest pain radiating to left arm",
    ),
    patient_profile=PatientProfileDTO(age=58),
    state_snapshot={
        "chief_complaint": "crushing chest pain",
        "location": "chest",
        "nature_of_pain": "crushing pressure radiating to left arm",
        "severity": "severe",
        "associated_symptoms": ["cold sweats", "shortness of breath"],
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["suspected_acute_coronary_syndrome"],
        "patient_profile": {"age": 58},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_COMPLETE_ROUTINE = NormalizedClinicalInputDTO(
    patient_id="PAT_DV_001",
    episode_id="EP_DV_001",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        english_text="moderate",
    ),
    patient_profile=PatientProfileDTO(
        age=48,
        vitals={"height": 165, "weight": 68, "bmi": 25.0},
        dietary_habits="Standard Mediterranean diet",
        allergies=["Shellfish"],
    ),
    state_snapshot={
        "chief_complaint": "knee pain",
        "nature_of_pain": "dull ache",
        "location": "right knee",
        "duration": "2 weeks",
        "severity": "moderate",
        "associated_symptoms": ["mild stiffness"],
        "vitals": {"height": 165, "weight": 68, "bmi": 25.0},
        "dietary_habits": "Standard Mediterranean diet",
        "allergies": ["Shellfish"],
        "patient_profile": {
            "age": 48,
            "vitals": {"height": 165, "weight": 68, "bmi": 25.0},
            "dietary_habits": "Standard Mediterranean diet",
            "allergies": ["Shellfish"],
        },
        "missing_information": [],
        "information_complete": True,
    },
)

DASHAVIDHA_FIXTURES: dict[str, NormalizedClinicalInputDTO] = {
    "empty_profile": FIXTURE_EMPTY_PROFILE,
    "vaya_balya": FIXTURE_VAYA_BALYA,
    "vaya_madhyama": FIXTURE_VAYA_MADHYAMA,
    "vaya_vriddha": FIXTURE_VAYA_VRIDDHA,
    "vaya_missing": FIXTURE_VAYA_MISSING,
    "prakriti_reported": FIXTURE_PRAKRITI_REPORTED,
    "prakriti_unassessed": FIXTURE_PRAKRITI_UNASSESSED,
    "burning_sensation": FIXTURE_BURNING_SENSATION,
    "penicillin_allergy": FIXTURE_PENICILLIN_ALLERGY,
    "anxiety_distress": FIXTURE_ANXIETY_DISTRESS,
    "ahara_shakti_appetite": FIXTURE_AHARA_SHAKTI_APPETITE,
    "vyayama_shakti_fatigue": FIXTURE_VYAYAMA_SHAKTI_FATIGUE,
    "low_hb_fatigue": FIXTURE_LOW_HB_FATIGUE,
    "modern_vitals_pramana": FIXTURE_MODERN_VITALS_PRAMANA,
    "satmya_diet": FIXTURE_SATMYA_DIET,
    "emergency_red_flag": FIXTURE_EMERGENCY_RED_FLAG,
    "complete_routine": FIXTURE_COMPLETE_ROUTINE,
}

