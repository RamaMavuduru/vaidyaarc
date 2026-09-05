"""
Phase 10: Synthetic Advanced Risk Convergence Test Fixtures.

Provides 16 standardized multi-encounter and multi-document synthetic test fixtures
conforming to NormalizedClinicalInputDTO for comprehensive offline validation of
Phase 10 Advanced Risk Convergence.

ALL DATA IS SYNTHETIC / DEMO DATA FOR VALIDATION PURPOSES ONLY.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    DocumentDTO,
)


# 1. Recurrent Complaint Escalation (Headache across 3 non-consecutive episodes)
FIXTURE_RECURRENT_RISK_ESCALATION = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_001_RECURRENT",
    episode_id="EP_ADV_001_E4",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "headache",
        "duration": "2 days",
        "severity": "moderate",
        "location": "head",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_001_A",
            "timestamp": "2025-01-10T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "moderate",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_001_B",
            "timestamp": "2025-03-15T10:00:00Z",
            "chief_complaint": "skin rash",
            "severity": "mild",
            "risk_level": "LOW",
            "risk_score": 5.0,
        },
        {
            "encounter_id": "ENC_HIST_001_C",
            "timestamp": "2025-06-20T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "moderate",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
    ]
)


# 2. Persistent Unresolved Problem (Cough for 3 weeks)
FIXTURE_PERSISTENT_SYMPTOM_RISK = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_002_PERSISTENT",
    episode_id="EP_ADV_002",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "cough",
        "duration": "3 weeks",
        "severity": "moderate",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_002_A",
            "timestamp": "2025-05-01T10:00:00Z",
            "chief_complaint": "cough",
            "severity": "mild",
            "risk_level": "LOW",
        }
    ]
)


# 3. Multi-Encounter Historical Risk Escalation (LOW -> MODERATE -> HIGH)
FIXTURE_HISTORICAL_ESCALATION = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_003_ESCALATION",
    episode_id="EP_ADV_003_E4",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "duration": "3 days",
        "severity": "moderate",
        "location": "upper abdomen",
        "nature_of_pain": "cramping",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_003_A",
            "timestamp": "2025-01-01T10:00:00Z",
            "chief_complaint": "stomach ache",
            "risk_level": "LOW",
            "risk_score": 8.0,
        },
        {
            "encounter_id": "ENC_HIST_003_B",
            "timestamp": "2025-04-01T10:00:00Z",
            "chief_complaint": "stomach pain",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_003_C",
            "timestamp": "2025-08-01T10:00:00Z",
            "chief_complaint": "severe abdominal pain",
            "risk_level": "HIGH",
            "risk_score": 28.0,
        },
    ]
)


# 4. Repeated Moderate Risk Encounters (3 prior MODERATE encounters)
FIXTURE_REPEATED_MODERATE_RISK = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_004_MODERATE",
    episode_id="EP_ADV_004_E4",
    channel="kiosk",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "joint pain",
        "duration": "1 week",
        "severity": "moderate",
        "location": "both knees",
        "nature_of_pain": "aching",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_004_A",
            "timestamp": "2025-01-15T10:00:00Z",
            "chief_complaint": "joint pain",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_004_B",
            "timestamp": "2025-04-15T10:00:00Z",
            "chief_complaint": "back pain",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_004_C",
            "timestamp": "2025-07-15T10:00:00Z",
            "chief_complaint": "knee pain",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
    ]
)


# 5. Multimorbid Baseline Burden (2 chronic baseline conditions + 2 unresolved issues)
FIXTURE_MULTIMORBID_BURDEN = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_005_MULTIMORBID",
    episode_id="EP_ADV_005",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    patient_profile=PatientProfileDTO(
        age=68,
        sex="female",
        medical_conditions=["Hypertension", "Type 2 Diabetes Mellitus"],
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "dizziness",
        "duration": "2 days",
        "severity": "moderate",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_005_A",
            "timestamp": "2025-02-01T10:00:00Z",
            "chief_complaint": "headache",
            "severity": "moderate",
            "associated_symptoms": ["insomnia"],
        }
    ]
)


# 6. Observational Biomarker Trajectory Change (HbA1c increasing)
FIXTURE_BIOMARKER_OBSERVATION = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_006_BIOMARKER",
    episode_id="EP_ADV_006",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_BM_001",
            document_type="lab_report",
            document_date="2025-01-10",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 6.2, "unit": "%"}],
        ),
        DocumentDTO(
            document_id="DOC_BM_002",
            document_type="lab_report",
            document_date="2025-06-10",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 8.5, "unit": "%"}],
        ),
    ]
)


# 7. Biomarker Unit Mismatch Safe Gating
FIXTURE_BIOMARKER_UNIT_MISMATCH_SAFE = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_007_MISMATCH",
    episode_id="EP_ADV_007",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_MIS_1",
            document_type="lab_report",
            document_date="2025-01-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.0, "unit": "g/dL"}],
        ),
        DocumentDTO(
            document_id="DOC_MIS_2",
            document_type="lab_report",
            document_date="2025-03-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 85.0, "unit": "%"}],
        ),
    ]
)


# 8. Biomarker Single Observation Safe Gating
FIXTURE_BIOMARKER_SINGLE_OBSERVATION_SAFE = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_008_SINGLE",
    episode_id="EP_ADV_008",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_SIN_1",
            document_type="lab_report",
            document_date="2025-05-01",
            structured_biomarkers=[{"biomarker": "Platelets", "value": 250000.0, "unit": "/mcL"}],
        )
    ]
)


# 9. Governed Cross-Modal Concordance (Fatigue + decreasing Hemoglobin)
FIXTURE_GOVERNED_CROSS_MODAL = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_009_CROSSMODAL",
    episode_id="EP_ADV_009",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "fatigue",
        "duration": "2 weeks",
        "severity": "moderate",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_HB_1",
            document_type="lab_report",
            document_date="2025-01-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.0, "unit": "g/dL"}],
        ),
        DocumentDTO(
            document_id="DOC_HB_2",
            document_type="lab_report",
            document_date="2025-04-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 9.5, "unit": "g/dL"}],
        ),
    ]
)


# 10. Unsupported Cross-Modal Relationship (Skin Rash + Hemoglobin -> No cross-modal signal)
FIXTURE_UNSUPPORTED_CROSS_MODAL = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_010_UNSUPPORTED",
    episode_id="EP_ADV_010",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "skin rash",
        "duration": "3 days",
        "severity": "mild",
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_HB_A",
            document_type="lab_report",
            document_date="2025-01-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 14.0, "unit": "g/dL"}],
        ),
        DocumentDTO(
            document_id="DOC_HB_B",
            document_type="lab_report",
            document_date="2025-04-01",
            structured_biomarkers=[{"biomarker": "Hemoglobin", "value": 10.5, "unit": "g/dL"}],
        ),
    ]
)


# 11. Current LOW Risk + Longitudinal HIGH Risk
# Current: Routine checkup (LOW score ~5). History: Recurrent headache (3 episodes) + persistent duration + escalating risk.
FIXTURE_CURRENT_LOW_LONGITUDINAL_HIGH = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_011_LOW_HIGH",
    episode_id="EP_ADV_011_E5",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "headache",
        "duration": "1 day",
        "severity": "mild",
        "location": "head",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_011_A",
            "timestamp": "2025-01-10T10:00:00Z",
            "chief_complaint": "headache",
            "risk_level": "LOW",
            "risk_score": 8.0,
        },
        {
            "encounter_id": "ENC_HIST_011_B",
            "timestamp": "2025-03-10T10:00:00Z",
            "chief_complaint": "headache",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_011_C",
            "timestamp": "2025-06-10T10:00:00Z",
            "chief_complaint": "headache",
            "risk_level": "HIGH",
            "risk_score": 28.0,
        },
    ]
)


# 12. Current HIGH Risk + Clean History (Floor Preservation)
FIXTURE_CURRENT_HIGH_LONGITUDINAL_LOW = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_012_HIGH_CLEAN",
    episode_id="EP_ADV_012",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="severe", english_text="severe"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "duration": "2 days",
        "severity": "severe",
        "location": "upper abdomen",
        "nature_of_pain": "sharp",
        "associated_symptoms": ["nausea", "fever"],
        "information_complete": True,
    },
    previous_encounters=[]
)


# 13. Undated Encounters Safe Handling
FIXTURE_UNDATED_ENCOUNTERS_SAFE = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_013_UNDATED",
    episode_id="EP_ADV_013",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "headache",
        "duration": "1 day",
        "severity": "mild",
        "location": "head",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_UNDATED_A",
            "timestamp": None,
            "chief_complaint": "fever",
            "risk_level": "LOW",
        },
        {
            "encounter_id": "ENC_UNDATED_B",
            "timestamp": "",
            "chief_complaint": "cough",
            "risk_level": "MODERATE",
        },
    ]
)


# 14. Explicit Resolution Followed By Recurrence
FIXTURE_RESOLVED_THEN_RECURRENT = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_014_RES_REC",
    episode_id="EP_ADV_014_E3",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "fever",
        "duration": "2 days",
        "severity": "moderate",
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_014_A",
            "timestamp": "2025-01-01T10:00:00Z",
            "chief_complaint": "fever",
            "severity": "moderate",
            "risk_level": "MODERATE",
        },
        {
            "encounter_id": "ENC_HIST_014_B",
            "timestamp": "2025-03-01T10:00:00Z",
            "chief_complaint": "routine checkup",
            "resolved_symptoms": ["fever"],
            "risk_level": "LOW",
        },
    ]
)


# 15. Missing != Resolved (Insidious unmentioned prior problem)
FIXTURE_MISSING_NOT_RESOLVED_RISK = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_015_MISSING",
    episode_id="EP_ADV_015_E2",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "skin rash",
        "duration": "2 days",
        "severity": "mild",
        "resolved_signals": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_015_A",
            "timestamp": "2025-02-01T10:00:00Z",
            "chief_complaint": "fever",
            "associated_symptoms": ["cough"],
            "severity": "moderate",
            "risk_level": "MODERATE",
        }
    ]
)


# 16. Clean Baseline Zero History
FIXTURE_CLEAN_BASELINE_ZERO_HISTORY = NormalizedClinicalInputDTO(
    patient_id="PAT_ADV_016_CLEAN",
    episode_id="EP_ADV_016",
    channel="kiosk",
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


ADVANCED_RISK_FIXTURES: dict[str, NormalizedClinicalInputDTO] = {
    "recurrent_risk": FIXTURE_RECURRENT_RISK_ESCALATION,
    "persistent_symptom": FIXTURE_PERSISTENT_SYMPTOM_RISK,
    "historical_escalation": FIXTURE_HISTORICAL_ESCALATION,
    "repeated_moderate": FIXTURE_REPEATED_MODERATE_RISK,
    "multimorbid_burden": FIXTURE_MULTIMORBID_BURDEN,
    "biomarker_observation": FIXTURE_BIOMARKER_OBSERVATION,
    "unit_mismatch_safe": FIXTURE_BIOMARKER_UNIT_MISMATCH_SAFE,
    "single_observation_safe": FIXTURE_BIOMARKER_SINGLE_OBSERVATION_SAFE,
    "governed_cross_modal": FIXTURE_GOVERNED_CROSS_MODAL,
    "unsupported_cross_modal": FIXTURE_UNSUPPORTED_CROSS_MODAL,
    "low_high_conflict": FIXTURE_CURRENT_LOW_LONGITUDINAL_HIGH,
    "high_clean_floor": FIXTURE_CURRENT_HIGH_LONGITUDINAL_LOW,
    "undated_safe": FIXTURE_UNDATED_ENCOUNTERS_SAFE,
    "resolved_recurrent": FIXTURE_RESOLVED_THEN_RECURRENT,
    "missing_not_resolved": FIXTURE_MISSING_NOT_RESOLVED_RISK,
    "clean_baseline": FIXTURE_CLEAN_BASELINE_ZERO_HISTORY,
}
