"""
Phase 11: Synthetic Clinical Summary & Consultation Questions Test Fixtures.

Provides 25+ comprehensive standardized synthetic test fixtures for offline validation
of Phase 11 Clinical Summary and Consultation Questions engine.

ALL DATA IS SYNTHETIC / DEMO DATA FOR VALIDATION PURPOSES ONLY.
"""

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
    DocumentDTO,
)


# 1. Complete Routine Case
FIXTURE_COMPLETE_ROUTINE = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_001",
    episode_id="EP_SUM_001",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    patient_profile=PatientProfileDTO(
        age=35,
        sex="female",
        medical_conditions=["Mild Asthma"],
        allergies=["Penicillin"],
        chronic_medications=[{"name": "Albuterol inhaler", "dosage": "as needed"}],
        surgical_history=["Appendectomy (2018)"],
        family_history=["Mother had Type 2 Diabetes"],
    ),
    state_snapshot={
        "chief_complaint": "headache",
        "duration": "2 days",
        "severity": "moderate",
        "nature_of_pain": "throbbing",
        "location": "forehead",
        "associated_symptoms": ["nausea"],
        "missing_information": [],
        "information_complete": True,
    }
)


# 2. Incomplete Intake (Missing severity and duration)
FIXTURE_INCOMPLETE_INTAKE = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_002",
    episode_id="EP_SUM_002",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="stomach pain", english_text="stomach pain"),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "duration": None,
        "severity": None,
        "location": "upper abdomen",
        "missing_information": ["duration", "severity"],
        "information_complete": False,
    }
)


# 3. Missing Past Medical and Surgical History
FIXTURE_MISSING_HISTORY = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_003",
    episode_id="EP_SUM_003",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    patient_profile=PatientProfileDTO(
        age=28,
        sex="male",
        medical_conditions=[],
        surgical_history=[],
    ),
    state_snapshot={
        "chief_complaint": "knee pain",
        "duration": "3 days",
        "severity": "moderate",
        "nature_of_pain": "aching",
        "location": "right knee",
        "missing_information": [],
        "information_complete": True,
    }
)


# 4. Missing Medication History
FIXTURE_MISSING_MEDICATIONS = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_004",
    episode_id="EP_SUM_004",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(
        age=45,
        sex="female",
        chronic_medications=[],
    ),
    state_snapshot={
        "chief_complaint": "mild skin rash",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    }
)


# 5. Missing Allergy History
FIXTURE_MISSING_ALLERGIES = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_005",
    episode_id="EP_SUM_005",
    channel="kiosk",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(
        age=50,
        sex="male",
        allergies=[],
    ),
    state_snapshot={
        "chief_complaint": "cough",
        "duration": "2 days",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    }
)


# 6. Missing Family History
FIXTURE_MISSING_FAMILY_HISTORY = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_006",
    episode_id="EP_SUM_006",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    patient_profile=PatientProfileDTO(
        age=32,
        sex="female",
        family_history=[],
    ),
    state_snapshot={
        "chief_complaint": "back ache",
        "duration": "4 days",
        "severity": "moderate",
        "nature_of_pain": "dull ache",
        "location": "lower back",
        "missing_information": [],
        "information_complete": True,
    }
)


# 7. Missing Review of Systems (Zero associated symptoms)
FIXTURE_MISSING_ROS = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_007",
    episode_id="EP_SUM_007",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "finger pain",
        "duration": "1 day",
        "severity": "mild",
        "nature_of_pain": "sharp",
        "location": "index finger",
        "associated_symptoms": [],
        "missing_information": [],
        "information_complete": True,
    }
)


# 8. Prior Investigations Present (Lab report with biomarkers)
FIXTURE_PRIOR_INVESTIGATIONS = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_008",
    episode_id="EP_SUM_008",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "fatigue",
        "duration": "2 weeks",
        "severity": "moderate",
        "missing_information": [],
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_LAB_001",
            document_type="lab_report",
            document_date="2025-06-01",
            structured_biomarkers=[
                {"biomarker": "Hemoglobin", "value": 10.2, "unit": "g/dL"},
                {"biomarker": "Serum Ferritin", "value": 15.0, "unit": "ng/mL"},
            ],
        )
    ]
)


# 9. Longitudinal Recurrence Context
FIXTURE_LONGITUDINAL_RECURRENCE = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_009",
    episode_id="EP_SUM_009_E4",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "migraine headache",
        "duration": "2 days",
        "severity": "moderate",
        "nature_of_pain": "throbbing",
        "location": "temporal",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_009_A",
            "timestamp": "2025-01-10T10:00:00Z",
            "chief_complaint": "migraine headache",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
        {
            "encounter_id": "ENC_HIST_009_B",
            "timestamp": "2025-04-10T10:00:00Z",
            "chief_complaint": "migraine headache",
            "risk_level": "MODERATE",
            "risk_score": 18.0,
        },
    ]
)


# 10. Longitudinal Persistent Problem (Duration 4 weeks)
FIXTURE_LONGITUDINAL_PERSISTENT = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_010",
    episode_id="EP_SUM_010",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="moderate", english_text="moderate"),
    state_snapshot={
        "chief_complaint": "chronic cough",
        "duration": "4 weeks",
        "severity": "moderate",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_010_A",
            "timestamp": "2025-05-01T10:00:00Z",
            "chief_complaint": "cough",
            "risk_level": "LOW",
        }
    ]
)


# 11. Explicitly Resolved Problem Followed by Routine Checkup
FIXTURE_EXPLICITLY_RESOLVED = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_011",
    episode_id="EP_SUM_011",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "routine checkup",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    },
    previous_encounters=[
        {
            "encounter_id": "ENC_HIST_011_A",
            "timestamp": "2025-01-01T10:00:00Z",
            "chief_complaint": "fever",
            "severity": "moderate",
            "risk_level": "MODERATE",
        },
        {
            "encounter_id": "ENC_HIST_011_B",
            "timestamp": "2025-03-01T10:00:00Z",
            "chief_complaint": "follow up",
            "resolved_symptoms": ["fever"],
            "risk_level": "LOW",
        },
    ]
)


# 12. Biomarker Trajectory Present (HbA1c increasing across 2 documents)
FIXTURE_BIOMARKER_TRAJECTORY = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_012",
    episode_id="EP_SUM_012",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "routine diabetes review",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_LAB_012_A",
            document_type="lab_report",
            document_date="2025-01-15",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 6.5, "unit": "%"}],
        ),
        DocumentDTO(
            document_id="DOC_LAB_012_B",
            document_type="lab_report",
            document_date="2025-07-15",
            structured_biomarkers=[{"biomarker": "HbA1c", "value": 8.2, "unit": "%"}],
        ),
    ]
)


# 13. Biomarker Insufficient Data (Single observation)
FIXTURE_BIOMARKER_INSUFFICIENT = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_013",
    episode_id="EP_SUM_013",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    state_snapshot={
        "chief_complaint": "health check",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    },
    documents=[
        DocumentDTO(
            document_id="DOC_LAB_013_SINGLE",
            document_type="lab_report",
            document_date="2025-05-01",
            structured_biomarkers=[{"biomarker": "TSH", "value": 2.5, "unit": "mIU/L"}],
        )
    ]
)


# 14. Conflicting Patient Information (Mild slot vs severe raw text)
FIXTURE_CONFLICTING_INFORMATION = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_014",
    episode_id="EP_SUM_014",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="I have unbearable excruciating worst pain in my stomach",
        english_text="I have unbearable excruciating worst pain in my stomach",
    ),
    state_snapshot={
        "chief_complaint": "stomach pain",
        "duration": "2 days",
        "severity": "mild",
        "nature_of_pain": "cramping",
        "location": "abdomen",
        "missing_information": [],
        "information_complete": True,
    }
)


# 15. Phase 2B HIGH Risk Case
FIXTURE_PHASE2B_HIGH_RISK = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_015",
    episode_id="EP_SUM_015",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="severe", english_text="severe"),
    patient_profile=PatientProfileDTO(
        age=72,
        sex="male",
        medical_conditions=["Coronary Artery Disease", "Type 2 Diabetes"],
    ),
    state_snapshot={
        "chief_complaint": "high fever",
        "duration": "3 days",
        "severity": "severe",
        "location": "general",
        "associated_symptoms": ["extreme chills", "confusion"],
        "missing_information": [],
        "information_complete": True,
    }
)


# 16. Phase 2B URGENT Risk Case (Worsening severe presentation)
FIXTURE_PHASE2B_URGENT_RISK = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_016",
    episode_id="EP_SUM_016",
    channel="mobile_app",
    message=NormalizedMessageDTO(original_text="severe", english_text="severe"),
    state_snapshot={
        "chief_complaint": "severe abdominal pain",
        "duration": "1 day",
        "severity": "severe",
        "nature_of_pain": "rigid tearing",
        "location": "lower abdomen",
        "associated_symptoms": ["inability to keep fluids down", "high fever"],
        "missing_information": [],
        "information_complete": True,
    }
)


# 17. Phase 2A Emergency Red Flag Case
FIXTURE_PHASE2A_EMERGENCY = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_017_EMERGENCY",
    episode_id="EP_SUM_017",
    channel="mobile_app",
    message=NormalizedMessageDTO(
        original_text="crushing chest pain and difficulty breathing",
        english_text="crushing chest pain and difficulty breathing",
    ),
    state_snapshot={
        "chief_complaint": "severe chest pain",
        "duration": "1 hour",
        "severity": "severe",
        "location": "chest",
        "associated_symptoms": ["difficulty breathing"],
        "missing_information": [],
        "information_complete": True,
    }
)


# 18. Empty / Minimal Patient Profile Baseline
FIXTURE_EMPTY_PROFILE_BASELINE = NormalizedClinicalInputDTO(
    patient_id="PAT_SUM_018",
    episode_id="EP_SUM_018",
    channel="kiosk",
    message=NormalizedMessageDTO(original_text="mild", english_text="mild"),
    patient_profile=PatientProfileDTO(),
    state_snapshot={
        "chief_complaint": "mild sore throat",
        "duration": "1 day",
        "severity": "mild",
        "missing_information": [],
        "information_complete": True,
    }
)


CLINICAL_SUMMARY_FIXTURES: dict[str, NormalizedClinicalInputDTO] = {
    "complete_routine": FIXTURE_COMPLETE_ROUTINE,
    "incomplete_intake": FIXTURE_INCOMPLETE_INTAKE,
    "missing_history": FIXTURE_MISSING_HISTORY,
    "missing_medications": FIXTURE_MISSING_MEDICATIONS,
    "missing_allergies": FIXTURE_MISSING_ALLERGIES,
    "missing_family_history": FIXTURE_MISSING_FAMILY_HISTORY,
    "missing_ros": FIXTURE_MISSING_ROS,
    "prior_investigations": FIXTURE_PRIOR_INVESTIGATIONS,
    "longitudinal_recurrence": FIXTURE_LONGITUDINAL_RECURRENCE,
    "longitudinal_persistent": FIXTURE_LONGITUDINAL_PERSISTENT,
    "explicitly_resolved": FIXTURE_EXPLICITLY_RESOLVED,
    "biomarker_trajectory": FIXTURE_BIOMARKER_TRAJECTORY,
    "biomarker_insufficient": FIXTURE_BIOMARKER_INSUFFICIENT,
    "conflicting_information": FIXTURE_CONFLICTING_INFORMATION,
    "high_risk": FIXTURE_PHASE2B_HIGH_RISK,
    "urgent_risk": FIXTURE_PHASE2B_URGENT_RISK,
    "emergency_red_flag": FIXTURE_PHASE2A_EMERGENCY,
    "empty_profile": FIXTURE_EMPTY_PROFILE_BASELINE,
}
