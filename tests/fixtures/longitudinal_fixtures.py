"""
Phase 9: Synthetic Longitudinal Clinical Test Fixtures.

Provides 14 standardized multi-encounter and multi-document synthetic test fixtures
conforming to NormalizedClinicalInputDTO for comprehensive offline validation of
Phase 9 Longitudinal Patient Intelligence.

ALL DATA IS SYNTHETIC / DEMO DATA FOR VALIDATION PURPOSES ONLY.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    PatientLocationDTO,
    DocumentDTO,
)


# 1. Chronic Biomarker Progression (Increasing numerical trajectory)
# HbA1c: 6.5% -> 7.2% -> 8.4% -> 9.1%
# INVARIANT: Engine reports 'increasing', ZERO unsupported 'diabetes worsening' claim.
FIXTURE_CHRONIC_BIOMARKER_INCREASING = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_001_INCREASING",
    episode_id="EP_LONG_001_D4",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="moderate",
        original_language="en",
        english_text="moderate",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=58,
        sex="male",
        medical_conditions=["Type 2 Diabetes Mellitus"],
        allergies=[],
        chronic_medications=[{"medication": "Metformin", "dosage": "500mg daily"}]
    ),
    state_snapshot={
        "chief_complaint": "fatigue",
        "duration": "2 weeks",
        "severity": "moderate",
        "associated_symptoms": ["increased thirst"],
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_001_A",
            "timestamp": "2025-01-15T09:00:00Z",
            "chief_complaint": "routine checkup",
            "severity": "mild",
            "duration": "1 day",
            "risk_score": 10.0,
            "risk_level": "LOW",
        },
        {
            "encounter_id": "ENC_HIST_001_B",
            "timestamp": "2025-04-15T09:00:00Z",
            "chief_complaint": "fatigue",
            "severity": "mild",
            "duration": "3 days",
            "risk_score": 15.0,
            "risk_level": "LOW",
        },
    ],
    documents=[
        DocumentDTO(
            document_id="DOC_HBA1C_T1",
            document_type="lab_report",
            document_date="2025-01-15",
            extracted_text="HbA1c: 6.5 % (Normal: 4.0-5.6)",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 6.5, "unit": "%", "status": "high"}],
            provenance="synthetic_ocr",
        ),
        DocumentDTO(
            document_id="DOC_HBA1C_T2",
            document_type="lab_report",
            document_date="2025-04-15",
            extracted_text="HbA1c: 7.2 % (High)",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 7.2, "unit": "%", "status": "high"}],
            provenance="synthetic_ocr",
        ),
        DocumentDTO(
            document_id="DOC_HBA1C_T3",
            document_type="lab_report",
            document_date="2025-08-10",
            extracted_text="HbA1c: 8.4 % (High)",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 8.4, "unit": "%", "status": "high"}],
            provenance="synthetic_ocr",
        ),
        DocumentDTO(
            document_id="DOC_HBA1C_T4",
            document_type="lab_report",
            document_date="2025-12-01",
            extracted_text="HbA1c: 9.1 % (Critical High)",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 9.1, "unit": "%", "status": "critical_high"}],
            provenance="synthetic_ocr",
        ),
    ]
)


# 2. Chronic Biomarker Progression (Decreasing numerical trajectory)
# Fasting Blood Glucose: 240 mg/dL -> 195 mg/dL -> 150 mg/dL -> 110 mg/dL
FIXTURE_CHRONIC_BIOMARKER_DECREASING = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_002_DECREASING",
    episode_id="EP_LONG_002_D4",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="mild",
        original_language="en",
        english_text="mild",
        source="patient",
    ),
    patient_profile=PatientProfileDTO(
        age=52,
        sex="female",
        medical_conditions=["Type 2 Diabetes Mellitus"],
    ),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_FBG_T1",
            document_type="lab_report",
            document_date="2025-02-01",
            extracted_text="Fasting Blood Glucose: 240 mg/dL (High)",
            structured_biomarkers=[{"biomarker": "Fasting Blood Glucose", "value": 240.0, "unit": "mg/dL", "status": "high"}],
        ),
        DocumentDTO(
            document_id="DOC_FBG_T2",
            document_type="lab_report",
            document_date="2025-05-01",
            extracted_text="Fasting Blood Glucose: 195 mg/dL (High)",
            structured_biomarkers=[{"biomarker": "Fasting Blood Glucose", "value": 195.0, "unit": "mg/dL", "status": "high"}],
        ),
        DocumentDTO(
            document_id="DOC_FBG_T3",
            document_type="lab_report",
            document_date="2025-08-01",
            extracted_text="Fasting Blood Glucose: 150 mg/dL (High)",
            structured_biomarkers=[{"biomarker": "Fasting Blood Glucose", "value": 150.0, "unit": "mg/dL", "status": "high"}],
        ),
        DocumentDTO(
            document_id="DOC_FBG_T4",
            document_type="lab_report",
            document_date="2025-11-01",
            extracted_text="Fasting Blood Glucose: 110 mg/dL (Normal)",
            structured_biomarkers=[{"biomarker": "Fasting Blood Glucose", "value": 110.0, "unit": "mg/dL", "status": "normal"}],
        ),
    ]
)


# 3. Stable Biomarker Numerical Trajectory
# Hemoglobin: 14.2 g/dL -> 14.2 g/dL -> 14.2 g/dL
FIXTURE_CHRONIC_BIOMARKER_STABLE = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_003_STABLE",
    episode_id="EP_LONG_003",
    channel="kiosk",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "annual physical",
        "duration": "today",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_HB_T1",
            document_type="lab_report",
            document_date="2025-01-10",
            extracted_text="Hemoglobin: 14.2 g/dL",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.2, "unit": "g/dL", "status": "normal"}],
        ),
        DocumentDTO(
            document_id="DOC_HB_T2",
            document_type="lab_report",
            document_date="2025-06-10",
            extracted_text="Hemoglobin: 14.2 g/dL",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.2, "unit": "g/dL", "status": "normal"}],
        ),
        DocumentDTO(
            document_id="DOC_HB_T3",
            document_type="lab_report",
            document_date="2025-12-10",
            extracted_text="Hemoglobin: 14.2 g/dL",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.2, "unit": "g/dL", "status": "normal"}],
        ),
    ]
)


# 4. Fluctuating Biomarker Trajectory
# Systolic BP: 130 -> 165 -> 125 -> 155 mmHg
FIXTURE_CHRONIC_BIOMARKER_FLUCTUATING = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_004_FLUCTUATING",
    episode_id="EP_LONG_004",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "blood pressure monitoring",
        "duration": "1 month",
        "severity": "moderate",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_BP_1",
            document_type="vitals_log",
            document_date="2025-01-01",
            structured_biomarkers=[{"biomarker": "Blood Pressure Systolic", "value": 130.0, "unit": "mmHg"}],
        ),
        DocumentDTO(
            document_id="DOC_BP_2",
            document_type="vitals_log",
            document_date="2025-02-01",
            structured_biomarkers=[{"biomarker": "Blood Pressure Systolic", "value": 165.0, "unit": "mmHg"}],
        ),
        DocumentDTO(
            document_id="DOC_BP_3",
            document_type="vitals_log",
            document_date="2025-03-01",
            structured_biomarkers=[{"biomarker": "Blood Pressure Systolic", "value": 125.0, "unit": "mmHg"}],
        ),
        DocumentDTO(
            document_id="DOC_BP_4",
            document_type="vitals_log",
            document_date="2025-04-01",
            structured_biomarkers=[{"biomarker": "Blood Pressure Systolic", "value": 155.0, "unit": "mmHg"}],
        ),
    ]
)


# 5. Single Observation Biomarker (Insufficient Data for Trajectory)
FIXTURE_BIOMARKER_SINGLE_OBSERVATION = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_005_SINGLE",
    episode_id="EP_LONG_005",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "rash",
        "duration": "2 days",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_SINGLE_CBC",
            document_type="lab_report",
            document_date="2025-06-01",
            structured_biomarkers=[{"biomarker": "Platelets", "value": 250000.0, "unit": "/mcL", "status": "normal"}],
        )
    ]
)


# 6. Biomarker Unit Mismatch (Incompatible Units)
FIXTURE_BIOMARKER_UNIT_MISMATCH = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_006_MISMATCH",
    episode_id="EP_LONG_006",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "checkup",
        "duration": "1 day",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_MISMATCH_1",
            document_type="lab_report",
            document_date="2025-01-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.0, "unit": "g/dL"}],
        ),
        DocumentDTO(
            document_id="DOC_MISMATCH_2",
            document_type="lab_report",
            document_date="2025-03-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 85.0, "unit": "%"}],
        ),
    ]
)


# 7. Recurrent Symptom / Complaint
# Enc 1: Headache | Enc 2: Rash | Enc 3: Headache | Enc 4: Cough | Enc 5: Headache
FIXTURE_RECURRENT_SYMPTOM = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_007_RECURRENT",
    episode_id="EP_LONG_007_E5",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="severe", english_text="severe"),
    state_snapshot={
        "chief_complaint": "headache",
        "location": "head",
        "duration": "1 day",
        "severity": "severe",
        "associated_symptoms": ["nausea"],
        "missing_information": [],
        "information_complete": True,
    },

    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_007_E1",
            "timestamp": "2025-01-10T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "moderate",
            "duration": "2 days",
        },
        {
            "encounter_id": "ENC_HIST_007_E2",
            "timestamp": "2025-03-15T10:00:00Z",
            "chief_complaint": "skin rash",
            "severity": "mild",
            "duration": "4 days",
        },
        {
            "encounter_id": "ENC_HIST_007_E3",
            "timestamp": "2025-06-20T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "severe",
            "duration": "1 day",
        },
        {
            "encounter_id": "ENC_HIST_007_E4",
            "timestamp": "2025-09-01T10:00:00Z",
            "chief_complaint": "cough",
            "severity": "mild",
            "duration": "3 days",
        },
    ]
)


# 8. Explicit Symptom Resolution
# Enc 1: Fever | Enc 2: Message explicitly states "fever has completely resolved"
FIXTURE_EXPLICIT_RESOLUTION = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_008_RESOLVED",
    episode_id="EP_LONG_008_E2",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="My fever has completely resolved and I have no more fever, just here for routine followup.",
        english_text="My fever has completely resolved and I have no more fever, just here for routine followup."
    ),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "today",
        "severity": "mild",
        "resolved_signals": ["fever"],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_008_E1",
            "timestamp": "2025-02-01T10:00:00Z",
            "chief_complaint": "fever",
            "severity": "moderate",
            "duration": "3 days",
        }
    ]
)


# 9. Missing != Resolved (Insidious Unmentioned Symptom)
# Enc 1: Fever & Cough | Enc 2: Patient reports Skin Rash, says nothing about fever/cough
# INVARIANT: Fever & Cough remain 'unresolved' (NOT marked resolved).
FIXTURE_MISSING_NOT_RESOLVED = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_009_MISSING",
    episode_id="EP_LONG_009_E2",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="I have a red rash on my arm",
        english_text="I have a red rash on my arm"
    ),
    state_snapshot={
        "chief_complaint": "skin rash",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": ["itching"],
        "resolved_signals": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_009_E1",
            "timestamp": "2025-01-15T10:00:00Z",
            "chief_complaint": "fever",
            "severity": "moderate",
            "duration": "4 days",
            "associated_symptoms": ["cough"],
        }
    ]
)


# 10. Multiple Chronic Comorbidities
FIXTURE_MULTIPLE_CHRONIC_COMORBIDITIES = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_010_COMORBID",
    episode_id="EP_LONG_010",
    channel="kiosk",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    patient_profile=PatientProfileDTO(
        age=67,
        sex="male",
        medical_conditions=["Hypertension", "Type 2 Diabetes Mellitus", "Osteoarthritis"],
        allergies=["Penicillin", "Sulfa drugs"],
        chronic_medications=[
            {"medication": "Amlodipine", "dosage": "5mg daily"},
            {"medication": "Metformin", "dosage": "1000mg daily"}
        ],
        surgical_history=["Right Knee Arthroscopy (2018)"]
    ),
    state_snapshot={
        "chief_complaint": "joint pain",
        "duration": "3 weeks",
        "severity": "moderate",
        "location": "both knees",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_010_A",
            "timestamp": "2025-01-10T10:00:00Z",
            "chief_complaint": "high blood pressure review",
            "severity": "moderate",
            "risk_level": "MODERATE",
            "risk_score": 35.0,
        },
        {
            "encounter_id": "ENC_HIST_010_B",
            "timestamp": "2025-04-12T10:00:00Z",
            "chief_complaint": "knee pain",
            "severity": "moderate",
            "risk_level": "LOW",
            "risk_score": 15.0,
        }
    ],
    documents=[
        DocumentDTO(
            document_id="DOC_COMORBID_CREAT",
            document_type="lab_report",
            document_date="2025-04-12",
            structured_biomarkers=[{"biomarker": "Serum Creatinine", "value": 1.1, "unit": "mg/dL", "status": "normal"}],
        )
    ]
)


# 11. Incomplete Historical Data (Missing timestamps & partial fields)
FIXTURE_INCOMPLETE_HISTORICAL_DATA = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_011_PARTIAL",
    episode_id="EP_LONG_011",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "headache",
        "severity": "mild",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_UNDATED_01",
            "timestamp": None,
            "chief_complaint": "fever",
            "severity": None,
        },
        {
            "encounter_id": "ENC_UNDATED_02",
            "timestamp": "",
            "chief_complaint": "cough",
        }
    ],
    documents=[
        DocumentDTO(
            document_id="DOC_UNDATED_01",
            document_type="lab_report",
            document_date=None,
            structured_biomarkers=[{"biomarker": "WBC", "value": 7500.0, "unit": "/mcL"}],
        )
    ]
)


# 12. Duplicate Encounter IDs
FIXTURE_DUPLICATE_ENCOUNTERS = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_012_DUP",
    episode_id="EP_LONG_012",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "stomach ache",
        "severity": "mild",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_DUP_001",
            "timestamp": "2025-03-01T10:00:00Z",
            "chief_complaint": "acidity",
        },
        {
            "encounter_id": "ENC_DUP_001",  # Exact duplicate ID
            "timestamp": "2025-03-01T10:00:00Z",
            "chief_complaint": "acidity",
        }
    ]
)


# 13. Conflicting Historical Records
FIXTURE_CONFLICTING_HISTORICAL_INFO = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_013_CONFLICT",
    episode_id="EP_LONG_013",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "back pain",
        "severity": "moderate",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_CONFLICT_A",
            "timestamp": "2025-02-01T10:00:00Z",
            "chief_complaint": "back pain",
            "severity": "mild",
        },
        {
            "encounter_id": "ENC_CONFLICT_B",
            "timestamp": "2025-02-01T10:00:00Z",
            "chief_complaint": "chest pain",
            "severity": "severe",
            "red_flags": ["severe chest pain"],
        }
    ]
)


# 14. Clean Baseline (Zero History)
FIXTURE_NO_HISTORY_BASELINE = NormalizedClinicalInputDTO(
    patient_id="PAT_LONG_014_CLEAN",
    episode_id="EP_LONG_014",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "mild cough",
        "duration": "1 day",
        "severity": "mild",
        "information_complete": True,
    },
    previous_encounters=[],
    documents=[],
    investigations=[],
)


LONGITUDINAL_FIXTURES: dict[str, NormalizedClinicalInputDTO] = {
    "biomarker_increasing": FIXTURE_CHRONIC_BIOMARKER_INCREASING,
    "biomarker_decreasing": FIXTURE_CHRONIC_BIOMARKER_DECREASING,
    "biomarker_stable": FIXTURE_CHRONIC_BIOMARKER_STABLE,
    "biomarker_fluctuating": FIXTURE_CHRONIC_BIOMARKER_FLUCTUATING,
    "biomarker_single": FIXTURE_BIOMARKER_SINGLE_OBSERVATION,
    "biomarker_unit_mismatch": FIXTURE_BIOMARKER_UNIT_MISMATCH,
    "recurrent_symptom": FIXTURE_RECURRENT_SYMPTOM,
    "explicit_resolution": FIXTURE_EXPLICIT_RESOLUTION,
    "missing_not_resolved": FIXTURE_MISSING_NOT_RESOLVED,
    "comorbidities": FIXTURE_MULTIPLE_CHRONIC_COMORBIDITIES,
    "incomplete_history": FIXTURE_INCOMPLETE_HISTORICAL_DATA,
    "duplicate_encounters": FIXTURE_DUPLICATE_ENCOUNTERS,
    "conflicting_history": FIXTURE_CONFLICTING_HISTORICAL_INFO,
    "no_history_baseline": FIXTURE_NO_HISTORY_BASELINE,
}
