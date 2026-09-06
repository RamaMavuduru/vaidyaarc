"""
Phase 12.5: Brain Acceptance & Integration Readiness Test Fixtures.

Contains comprehensive, standardized synthetic clinical inputs designed to test:
- 10 Complete End-to-End Patient Journeys
- Multi-turn State Integrity (up to 8 turns)
- Adversarial Safety Scenarios
- Missing Information Integrity (Missing != Absent)
- Provenance & Traceability
- Malformed & Edge-case Inputs

100% SYNTHETIC DATA. ZERO REAL PATIENT DATA. ZERO EXTERNAL DEPENDENCIES.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    PatientLocationDTO,
    DocumentDTO,
)


# ==============================================================================
# SECTION 1: 10 END-TO-END SYNTHETIC PATIENT JOURNEYS
# ==============================================================================

# Journey 1: Routine Simple Complaint (Mild Tension Headache)
JOURNEY_01_ROUTINE_SIMPLE = NormalizedClinicalInputDTO(
    patient_id="PAT_J01_SIMPLE",
    episode_id="EP_J01_SIMPLE",
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
        sex="female",
        medical_conditions=[],
        allergies=[],
    ),
    patient_location=PatientLocationDTO(city="Hyderabad", pincode="500001"),
    state_snapshot={
        "chief_complaint": "tension headache",
        "nature_of_pain": "dull ache",
        "location": "forehead and temples",
        "duration": "1 day",
        "severity": "mild",
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": True,
        "patient_profile": {"age": 28, "sex": "female"},
    },
)

# Journey 2: Incomplete/Vague Complaint (Turn 1: "I feel sick", Turn 2: "knee pain")
JOURNEY_02_INCOMPLETE_TURN1 = NormalizedClinicalInputDTO(
    patient_id="PAT_J02_VAGUE",
    episode_id="EP_J02_VAGUE",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="I just don't feel well today",
        original_language="en",
        english_text="I just don't feel well today",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(age=45),
    state_snapshot={
        "chief_complaint": None,
        "duration": None,
        "severity": None,
        "missing_information": ["chief_complaint", "duration", "severity"],
        "information_complete": False,
    },
)

JOURNEY_02_INCOMPLETE_TURN2 = NormalizedClinicalInputDTO(
    patient_id="PAT_J02_VAGUE",
    episode_id="EP_J02_VAGUE",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="My left knee hurts when walking",
        original_language="en",
        english_text="My left knee hurts when walking",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(age=45),
    state_snapshot={
        "chief_complaint": "left knee pain",
        "location": "left knee",
        "duration": None,
        "severity": None,
        "missing_information": ["duration", "severity"],
        "information_complete": False,
    },
)

# Journey 3: Immediate Emergency Red Flag (Crushing chest pain radiating to left arm)
JOURNEY_03_EMERGENCY_RED_FLAG = NormalizedClinicalInputDTO(
    patient_id="PAT_J03_EMERGENCY",
    episode_id="EP_J03_EMERGENCY",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="I have crushing chest pain radiating to my left arm with cold sweats",
        original_language="en",
        english_text="I have crushing chest pain radiating to my left arm with cold sweats",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(age=58, sex="male", medical_conditions=["Hypertension"]),
    patient_location=PatientLocationDTO(city="Bengaluru", pincode="560001"),
    state_snapshot={
        "chief_complaint": "crushing chest pain",
        "location": "chest",
        "nature_of_pain": "crushing pressure radiating to left arm",
        "severity": "severe",
        "associated_symptoms": ["cold sweats", "shortness of breath"],
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["suspected_acute_coronary_syndrome"],
        "missing_information": [],
        "information_complete": True,
        "patient_profile": {"age": 58, "sex": "male", "medical_conditions": ["Hypertension"]},
    },
)

# Journey 4: Late Red Flag Appearing After Several Turns (Turn 4 Sudden Thunderclap Headache)
JOURNEY_04_LATE_EMERGENCY = NormalizedClinicalInputDTO(
    patient_id="PAT_J04_LATE_EMERGENCY",
    episode_id="EP_J04_LATE_EMERGENCY",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="Suddenly it became a sudden severe headache with neck stiffness and vomiting",
        original_language="en",
        english_text="Suddenly it became a sudden severe headache with neck stiffness and vomiting",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(age=42, sex="female"),
    conversation_context={"turn_count": 4},
    state_snapshot={
        "chief_complaint": "sudden severe headache",
        "location": "entire head",
        "nature_of_pain": "sudden thunderclap",
        "duration": "1 hour",
        "severity": "severe",
        "associated_symptoms": ["neck stiffness", "projectile vomiting", "worst headache of life"],
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["sudden severe neurological symptoms"],
        "missing_information": [],
        "information_complete": True,
        "patient_profile": {"age": 42, "sex": "female"},
    },
)

# Journey 5: Multiple Moderate Risk Factors Converging (Phase 2B High Risk, No Red Flag)
JOURNEY_05_MODERATE_RISK_CONVERGENCE = NormalizedClinicalInputDTO(
    patient_id="PAT_J05_MOD_RISK",
    episode_id="EP_J05_MOD_RISK",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=65,
        sex="male",
        medical_conditions=["Type 2 Diabetes", "Chronic Kidney Disease Stage 3", "Hypertension"],
    ),
    state_snapshot={
        "chief_complaint": "persistent abdominal discomfort",
        "location": "epigastrium",
        "duration": "3 weeks",
        "severity": "moderate",
        "associated_symptoms": ["unexplained weight loss", "loss of appetite", "post-prandial fullness"],
        "patient_profile": {
            "age": 65,
            "sex": "male",
            "medical_conditions": ["Type 2 Diabetes", "Chronic Kidney Disease Stage 3", "Hypertension"],
        },
        "missing_information": [],
        "information_complete": True,
    },
)

# Journey 6: Longitudinal Patient with Prior Encounters
JOURNEY_06_LONGITUDINAL_PATIENT = NormalizedClinicalInputDTO(
    patient_id="PAT_J06_LONGITUDINAL",
    episode_id="EP_J06_ENC_3",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=56,
        sex="female",
        medical_conditions=["Osteoarthritis"],
    ),
    previous_encounters=[
        {
            "encounter_id": "ENC_J06_01",
            "date": "2026-01-10",
            "chief_complaint": "right knee pain",
            "severity": "mild",
            "duration": "1 week",
            "problem_id": "knee_oa",
        },
        {
            "encounter_id": "ENC_J06_02",
            "date": "2026-04-15",
            "chief_complaint": "right knee pain",
            "severity": "moderate",
            "duration": "2 weeks",
            "problem_id": "knee_oa",
        },
    ],
    state_snapshot={
        "chief_complaint": "right knee pain",
        "location": "right knee",
        "nature_of_pain": "aching stiffness",
        "duration": "3 weeks",
        "severity": "moderate",
        "associated_symptoms": ["morning stiffness for 20 minutes"],
        "patient_profile": {"age": 56, "sex": "female", "medical_conditions": ["Osteoarthritis"]},
        "previous_history": [
            {"chief_complaint": "right knee pain", "severity": "mild", "duration": "1 week"},
            {"chief_complaint": "right knee pain", "severity": "moderate", "duration": "2 weeks"},
        ],
        "missing_information": [],
        "information_complete": True,
    },
)

# Journey 7: Patient with Prior Investigations & Biomarkers
JOURNEY_07_INVESTIGATIONS_BIOMARKERS = NormalizedClinicalInputDTO(
    patient_id="PAT_J07_BIOMARKER",
    episode_id="EP_J07_BIOMARKER",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        original_language="en",
        english_text="mild",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(age=50, sex="male"),
    documents=[
        DocumentDTO(
            document_id="DOC_LAB_01",
            document_type="lab_report",
            document_date="2026-08-01",
            extracted_text="HbA1c: 8.4%, Fasting Glucose: 165 mg/dL, Hemoglobin: 13.5 g/dL",
            structured_biomarkers=[
                {"test_name": "HbA1c", "result_value": 8.4, "unit": "%"},
                {"test_name": "Fasting Blood Glucose", "result_value": 165, "unit": "mg/dL"},
                {"test_name": "Hemoglobin", "result_value": 13.5, "unit": "g/dL"},
            ],
        )
    ],
    investigations=[
        {"test_name": "HbA1c", "result_value": 8.4, "unit": "%"},
        {"test_name": "Fasting Blood Glucose", "result_value": 165, "unit": "mg/dL"},
    ],
    state_snapshot={
        "chief_complaint": "routine diabetes checkup",
        "duration": "6 months",
        "severity": "mild",
        "associated_symptoms": ["increased thirst", "mild fatigue"],
        "investigations": [
            {"test_name": "HbA1c", "result_value": 8.4, "unit": "%"},
            {"test_name": "Fasting Blood Glucose", "result_value": 165, "unit": "mg/dL"},
        ],
        "documents": [
            {
                "document_id": "DOC_LAB_01",
                "structured_biomarkers": [
                    {"test_name": "HbA1c", "result_value": 8.4, "unit": "%"},
                    {"test_name": "Fasting Blood Glucose", "result_value": 165, "unit": "mg/dL"},
                ],
            }
        ],
        "patient_profile": {"age": 50, "sex": "male"},
        "missing_information": [],
        "information_complete": True,
    },
)

# Journey 8: Patient with Chronic Medications & Drug Allergies
JOURNEY_08_MEDICATIONS_ALLERGIES = NormalizedClinicalInputDTO(
    patient_id="PAT_J08_MEDS",
    episode_id="EP_J08_MEDS",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        original_language="en",
        english_text="mild",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=62,
        sex="female",
        chronic_medications=[
            {"drug_name": "Metformin", "dosage": "500mg", "frequency": "twice daily"},
            {"drug_name": "Atorvastatin", "dosage": "20mg", "frequency": "once daily at night"},
        ],
        allergies=["Penicillin", "Sulfa drugs"],
        surgical_history=["Cholecystectomy in 2018"],
        family_history=["Maternal history of Coronary Artery Disease"],
    ),
    state_snapshot={
        "chief_complaint": "mild intermittent dizziness",
        "duration": "4 days",
        "severity": "mild",
        "allergies": ["Penicillin", "Sulfa drugs"],
        "patient_profile": {
            "age": 62,
            "sex": "female",
            "chronic_medications": [
                {"drug_name": "Metformin", "dosage": "500mg"},
                {"drug_name": "Atorvastatin", "dosage": "20mg"},
            ],
            "allergies": ["Penicillin", "Sulfa drugs"],
            "surgical_history": ["Cholecystectomy in 2018"],
            "family_history": ["Maternal history of Coronary Artery Disease"],
        },
        "missing_information": [],
        "information_complete": True,
    },
)

# Journey 9: Patient with Ayurveda Descriptive Representation & Prior Assessment
JOURNEY_09_AYURVEDA_REPRESENTATION = NormalizedClinicalInputDTO(
    patient_id="PAT_J09_AYUR",
    episode_id="EP_J09_AYUR",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=37,
        sex="male",
        reported_prakriti="Pitta-Vata",
        dietary_habits="Spicy diet, irregular meal times, tea 4 times daily",
    ),
    state_snapshot={
        "chief_complaint": "burning sensation in stomach with sour belching",
        "location": "epigastrium",
        "nature_of_pain": "burning",
        "duration": "1 week",
        "severity": "moderate",
        "associated_symptoms": ["sour eructations", "post-meal burning", "acid reflux"],
        "reported_prakriti": "Pitta-Vata",
        "dietary_habits": "Spicy diet, irregular meal times, tea 4 times daily",
        "patient_profile": {
            "age": 37,
            "sex": "male",
            "reported_prakriti": "Pitta-Vata",
            "dietary_habits": "Spicy diet, irregular meal times, tea 4 times daily",
        },
        "missing_information": [],
        "information_complete": True,
    },
)

# Journey 10: Full-Spectrum Comprehensive Journey
JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE = NormalizedClinicalInputDTO(
    patient_id="PAT_J10_FULL",
    episode_id="EP_J10_FULL",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
        provenance="patient_typed",
    ),
    patient_profile=PatientProfileDTO(
        age=52,
        sex="male",
        medical_conditions=["Hypertension", "Dyslipidemia"],
        allergies=["Shellfish"],
        chronic_medications=[{"drug_name": "Amlodipine", "dosage": "5mg once daily"}],
        surgical_history=["Appendectomy (2005)"],
        family_history=["Father had Type 2 Diabetes"],
        reported_prakriti="Kapha-Pitta",
        dietary_habits="Vegetarian diet with moderate dairy",
        functional_status="Able to walk 2 km daily without chest discomfort",
        vitals={"height": 172, "weight": 78, "bmi": 26.4},
    ),
    patient_location=PatientLocationDTO(city="Hyderabad", pincode="500034"),
    previous_encounters=[
        {
            "encounter_id": "ENC_J10_PREV_1",
            "date": "2026-03-01",
            "chief_complaint": "joint stiffness",
            "severity": "mild",
            "duration": "1 week",
        }
    ],
    documents=[
        DocumentDTO(
            document_id="DOC_J10_LAB",
            document_type="lab_report",
            document_date="2026-07-15",
            extracted_text="Total Cholesterol: 210 mg/dL, Triglycerides: 160 mg/dL, Fasting Glucose: 98 mg/dL",
            structured_biomarkers=[
                {"test_name": "Total Cholesterol", "result_value": 210, "unit": "mg/dL"},
                {"test_name": "Triglycerides", "result_value": 160, "unit": "mg/dL"},
                {"test_name": "Fasting Blood Glucose", "result_value": 98, "unit": "mg/dL"},
            ],
        )
    ],
    investigations=[
        {"test_name": "Total Cholesterol", "result_value": 210, "unit": "mg/dL"},
        {"test_name": "Triglycerides", "result_value": 160, "unit": "mg/dL"},
    ],
    state_snapshot={
        "chief_complaint": "knee stiffness and aching",
        "location": "bilateral knees",
        "nature_of_pain": "dull aching with morning stiffness",
        "duration": "2 weeks",
        "severity": "moderate",
        "associated_symptoms": ["morning stiffness for 15 minutes", "mild clicking sound"],
        "reported_prakriti": "Kapha-Pitta",
        "dietary_habits": "Vegetarian diet with moderate dairy",
        "functional_status": "Able to walk 2 km daily without chest discomfort",
        "vitals": {"height": 172, "weight": 78, "bmi": 26.4},
        "allergies": ["Shellfish"],
        "investigations": [
            {"test_name": "Total Cholesterol", "result_value": 210, "unit": "mg/dL"},
            {"test_name": "Triglycerides", "result_value": 160, "unit": "mg/dL"},
        ],
        "previous_history": [
            {"chief_complaint": "joint stiffness", "severity": "mild", "duration": "1 week"}
        ],
        "patient_profile": {
            "age": 52,
            "sex": "male",
            "medical_conditions": ["Hypertension", "Dyslipidemia"],
            "allergies": ["Shellfish"],
            "chronic_medications": [{"drug_name": "Amlodipine", "dosage": "5mg once daily"}],
            "surgical_history": ["Appendectomy (2005)"],
            "family_history": ["Father had Type 2 Diabetes"],
            "reported_prakriti": "Kapha-Pitta",
            "dietary_habits": "Vegetarian diet with moderate dairy",
            "functional_status": "Able to walk 2 km daily without chest discomfort",
            "vitals": {"height": 172, "weight": 78, "bmi": 26.4},
        },
        "missing_information": [],
        "information_complete": True,
    },
)


# ==============================================================================
# SECTION 2: MULTI-TURN SEQUENCE FIXTURES (TURNS 1 THROUGH 8)
# ==============================================================================

MULTITURN_TURN_1 = NormalizedClinicalInputDTO(
    patient_id="PAT_MT_01",
    episode_id="EP_MT_01",
    message=NormalizedMessageDTO(original_text="I have stomach pain"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "missing_information": ["nature_of_pain", "location", "duration", "severity"],
        "information_complete": False,
    },
)

MULTITURN_TURN_2 = NormalizedClinicalInputDTO(
    patient_id="PAT_MT_01",
    episode_id="EP_MT_01",
    message=NormalizedMessageDTO(original_text="burning"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "missing_information": ["location", "duration", "severity"],
        "information_complete": False,
    },
)

MULTITURN_TURN_3 = NormalizedClinicalInputDTO(
    patient_id="PAT_MT_01",
    episode_id="EP_MT_01",
    message=NormalizedMessageDTO(original_text="upper abdomen"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "missing_information": ["duration", "severity"],
        "information_complete": False,
    },
)

MULTITURN_TURN_4 = NormalizedClinicalInputDTO(
    patient_id="PAT_MT_01",
    episode_id="EP_MT_01",
    message=NormalizedMessageDTO(original_text="since 3 days"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "3 days",
        "missing_information": ["severity"],
        "information_complete": False,
    },
)

MULTITURN_TURN_5 = NormalizedClinicalInputDTO(
    patient_id="PAT_MT_01",
    episode_id="EP_MT_01",
    message=NormalizedMessageDTO(original_text="moderate"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "3 days",
        "severity": "moderate",
        "missing_information": [],
        "information_complete": True,
    },
)


# ==============================================================================
# SECTION 3: ADVERSARIAL SAFETY FIXTURES
# ==============================================================================

ADVERSARIAL_BURIED_EMERGENCY = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_BURIED",
    episode_id="EP_ADV_BURIED",
    message=NormalizedMessageDTO(
        original_text="I was eating lunch with friends and had mild indigestion, but then suddenly I felt crushing chest pain radiating to left arm and cold sweats, though I think I might just be tired from work.",
    ),
    state_snapshot={
        "chief_complaint": "crushing chest pain radiating to left arm",
        "associated_symptoms": ["cold sweats"],
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["suspected_acute_coronary_syndrome"],
        "missing_information": [],
        "information_complete": True,
    },
)

ADVERSARIAL_REASSURING_LANGUAGE_AFTER_SEVERE = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_REASSURE",
    episode_id="EP_ADV_REASSURE",
    message=NormalizedMessageDTO(
        original_text="I had severe chest pain and breathlessness but I took a glass of water and now I feel somewhat better so please just give me home remedies.",
    ),
    state_snapshot={
        "chief_complaint": "severe chest pain",
        "associated_symptoms": ["breathlessness"],
        "severity": "severe",
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["suspected_cardiac_or_pulmonary_emergency"],
        "missing_information": [],
        "information_complete": True,
    },
)

ADVERSARIAL_MULTIPLE_RED_FLAGS = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_MULTI_RF",
    episode_id="EP_ADV_MULTI_RF",
    message=NormalizedMessageDTO(
        original_text="I have severe chest pain and I am struggling with difficulty breathing and vomiting blood",
    ),
    state_snapshot={
        "chief_complaint": "severe chest pain",
        "location": "chest",
        "nature_of_pain": "crushing pressure",
        "duration": "1 hour",
        "severity": "severe",
        "associated_symptoms": ["difficulty breathing", "vomiting blood"],
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "red_flags": ["severe chest pain", "difficulty breathing", "vomiting blood"],
        "missing_information": [],
        "information_complete": True,
    },
)

ADVERSARIAL_CONTRADICTORY_SEVERITY = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_CONTRADICT",
    episode_id="EP_ADV_CONTRADICT",
    message=NormalizedMessageDTO(
        original_text="It is very mild but also completely unbearable 10 out of 10 agony",
    ),
    state_snapshot={
        "chief_complaint": "severe abdominal pain",
        "severity": "severe",
        "missing_information": [],
        "information_complete": True,
    },
)


# ==============================================================================
# SECTION 4: MISSING INFORMATION FIXTURES
# ==============================================================================

FIXTURE_MISSING_ALLERGIES = NormalizedClinicalInputDTO(
    patient_id="PAT_MISS_ALLERGY",
    episode_id="EP_MISS_ALLERGY",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(age=30, allergies=[]),
    state_snapshot={
        "chief_complaint": "headache",
        "location": "forehead",
        "duration": "1 day",
        "severity": "mild",
        "allergies": [],
        "patient_profile": {"age": 30, "allergies": []},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_MISSING_AGE = NormalizedClinicalInputDTO(
    patient_id="PAT_MISS_AGE",
    episode_id="EP_MISS_AGE",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(age=None),
    state_snapshot={
        "chief_complaint": "skin rash",
        "duration": "3 days",
        "severity": "mild",
        "patient_profile": {"age": None},
        "missing_information": [],
        "information_complete": True,
    },
)

FIXTURE_MISSING_MEDICATIONS = NormalizedClinicalInputDTO(
    patient_id="PAT_MISS_MEDS",
    episode_id="EP_MISS_MEDS",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(age=40, chronic_medications=[]),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "nature_of_pain": "dull ache",
        "location": "upper abdomen",
        "duration": "2 weeks",
        "severity": "mild",
        "patient_profile": {"age": 40, "chronic_medications": []},
        "missing_information": [],
        "information_complete": True,
    },
)


# ==============================================================================
# SECTION 5: MALFORMED & ROBUSTNESS FIXTURES
# ==============================================================================

FIXTURE_EMPTY_STRING = NormalizedClinicalInputDTO(
    patient_id="PAT_EMPTY_STR",
    episode_id="EP_EMPTY_STR",
    message=NormalizedMessageDTO(original_text=""),
    state_snapshot={"information_complete": False, "missing_information": ["chief_complaint"]},
)

FIXTURE_WHITESPACE_ONLY = NormalizedClinicalInputDTO(
    patient_id="PAT_WS_ONLY",
    episode_id="EP_WS_ONLY",
    message=NormalizedMessageDTO(original_text="   \t\n   "),
    state_snapshot={"information_complete": False, "missing_information": ["chief_complaint"]},
)

FIXTURE_VERY_LONG_TEXT = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_TXT",
    episode_id="EP_LONG_TXT",
    message=NormalizedMessageDTO(original_text="I have had a mild headache for 2 days. " * 50),
    state_snapshot={
        "chief_complaint": "mild headache",
        "location": "forehead",
        "duration": "2 days",
        "severity": "mild",
        "information_complete": True,
        "missing_information": [],
    },
)

FIXTURE_SPECIAL_CHARACTERS = NormalizedClinicalInputDTO(
    patient_id="PAT_SPECIAL_CHARS",
    episode_id="EP_SPECIAL_CHARS",
    message=NormalizedMessageDTO(original_text="Pain level #10! @upper_abdomen & <burning> ??? 100% ***"),
    state_snapshot={
        "chief_complaint": "abdominal pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "1 day",
        "severity": "severe",
        "information_complete": True,
        "missing_information": [],
    },
)


ALL_ACCEPTANCE_JOURNEYS = {
    "journey_01_routine_simple": JOURNEY_01_ROUTINE_SIMPLE,
    "journey_02_incomplete_turn1": JOURNEY_02_INCOMPLETE_TURN1,
    "journey_02_incomplete_turn2": JOURNEY_02_INCOMPLETE_TURN2,
    "journey_03_emergency_red_flag": JOURNEY_03_EMERGENCY_RED_FLAG,
    "journey_04_late_emergency": JOURNEY_04_LATE_EMERGENCY,
    "journey_05_moderate_risk_convergence": JOURNEY_05_MODERATE_RISK_CONVERGENCE,
    "journey_06_longitudinal_patient": JOURNEY_06_LONGITUDINAL_PATIENT,
    "journey_07_investigations_biomarkers": JOURNEY_07_INVESTIGATIONS_BIOMARKERS,
    "journey_08_medications_allergies": JOURNEY_08_MEDICATIONS_ALLERGIES,
    "journey_09_ayurveda_representation": JOURNEY_09_AYURVEDA_REPRESENTATION,
    "journey_10_full_spectrum_comprehensive": JOURNEY_10_FULL_SPECTRUM_COMPREHENSIVE,
}
