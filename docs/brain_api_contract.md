# VaidyaArc Brain Service & API Contract Specification

**Version:** 1.0 (Phase 12.5 Integration-Ready)
**Status:** Frozen & Approved for Application Integration
**Underlying Architecture:** Decoupled Zero-LLM/Deterministic Python Intelligence Core

---

## 1. Executive Summary

The **VaidyaArc Brain** encapsulates clinical intelligence from Phases 1B through 12 into a single, stateless, turn-based REST contract. It processes normalized patient messages, maintains conversational and longitudinal context via state snapshots, enforces deterministic emergency safety overrides, and synthesizes multi-domain clinical outputs upon consultation completion.

---

## 2. Endpoint Specification

### `POST /v1/clinical/turn`

Processes a single conversational or data-intake turn for a patient encounter.

#### HTTP Headers
```http
Content-Type: application/json
Accept: application/json
X-Client-Version: 1.0.0
X-Request-ID: <uuid>
```

---

## 3. Request Contract (`NormalizedClinicalInputDTO`)

The request payload accepts normalized patient input, whether originating from mobile chat, speech-to-text (STT), multilingual neural machine translation (NMT), or optical character recognition (OCR) documents.

```json
{
  "patient_id": "PAT_12345",
  "episode_id": "EP_67890",
  "channel": "mobile_app",
  "message": {
    "original_text": "I have severe burning stomach pain since yesterday",
    "original_language": "en",
    "english_text": "I have severe burning stomach pain since yesterday",
    "source": "patient",
    "confidence": 1.0,
    "provenance": "patient_typed"
  },
  "patient_profile": {
    "age": 45,
    "sex": "male",
    "medical_conditions": ["Hypertension"],
    "allergies": ["Penicillin"],
    "chronic_medications": [
      { "drug_name": "Amlodipine", "dosage": "5mg", "frequency": "once daily" }
    ],
    "surgical_history": ["Appendectomy in 2010"],
    "family_history": ["Paternal Type 2 Diabetes"],
    "reported_prakriti": "Pitta-Kapha",
    "dietary_habits": "Vegetarian diet, spicy food intake",
    "functional_status": "Independent in all ADLs",
    "vitals": { "height": 175, "weight": 76, "bmi": 24.8 }
  },
  "patient_location": {
    "city": "Hyderabad",
    "pincode": "500001",
    "latitude": 17.3850,
    "longitude": 78.4867
  },
  "conversation_context": {
    "turn_count": 3,
    "previous_question": "Where exactly is the pain located?"
  },
  "previous_encounters": [
    {
      "encounter_id": "ENC_001",
      "date": "2026-02-15",
      "chief_complaint": "acid reflux",
      "severity": "mild",
      "duration": "2 days"
    }
  ],
  "documents": [
    {
      "document_id": "DOC_LAB_99",
      "document_type": "lab_report",
      "document_date": "2026-07-20",
      "extracted_text": "HbA1c: 6.2%, Hemoglobin: 14.1 g/dL",
      "structured_biomarkers": [
        { "test_name": "HbA1c", "result_value": 6.2, "unit": "%" },
        { "test_name": "Hemoglobin", "result_value": 14.1, "unit": "g/dL" }
      ],
      "provenance": "ocr_extracted"
    }
  ],
  "investigations": [
    { "test_name": "HbA1c", "result_value": 6.2, "unit": "%" }
  ],
  "state_snapshot": {
    "chief_complaint": "stomach pain",
    "nature_of_pain": "burning",
    "missing_information": ["location", "duration", "severity"],
    "information_complete": false
  }
}
```

### Field Definitions & Requirements

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | `string` | Optional (default: `"ANONYMOUS"`) | Unique patient identifier |
| `episode_id` | `string` | Optional (default: `"EP_DEFAULT"`) | Current clinical encounter identifier |
| `channel` | `string` | Optional (default: `"text"`) | Client channel: `"mobile_app"`, `"kiosk"`, `"web"` |
| `message` | `NormalizedMessageDTO` | **Required** | Current incoming user utterance |
| `message.original_text` | `string` | **Required** | Raw user transcript/text |
| `message.original_language` | `string` | Optional (default: `"en"`) | BCP-47 / ISO language code |
| `message.english_text` | `string` | Optional | English translation if NMT used |
| `patient_profile` | `PatientProfileDTO` | Optional | Demographics, chronic meds, allergies, vitals |
| `patient_location` | `PatientLocationDTO` | Optional | Geolocation for facility matching |
| `conversation_context`| `object` | Optional | Turn tracking and dialogue context |
| `previous_encounters` | `list[object]` | Optional | Structured history of prior consultations |
| `documents` | `list[DocumentDTO]`| Optional | Lab reports, prescriptions with OCR data |
| `investigations` | `list[object]` | Optional | Structured prior biomarker observations |
| `state_snapshot` | `object` | Optional | Serialized state from previous turn |

---

## 4. Response Contract (`TurnResponseDTO`)

Every invocation returns a deterministic `TurnResponseDTO`.

```json
{
  "session_id": "EP_67890",
  "patient_id": "PAT_12345",
  "status": "complete",
  "conversation_message": "Thank you. Your clinical intake is complete.",
  "information_complete": true,
  "missing_information": [],
  "immediate_attention_required": false,
  "red_flag_status": "no_obvious_red_flags",
  "red_flags": [],
  "updated_state": {
    "chief_complaint": "stomach pain",
    "nature_of_pain": "burning",
    "location": "upper abdomen",
    "duration": "1 day",
    "severity": "severe",
    "associated_symptoms": [],
    "information_complete": true
  },
  "clinical_output": { ... }
}
```

### Response Status Lifecycle

1. **`status: "in_progress"`**: Intake slots remain incomplete. The client should prompt the patient with `conversation_message` and return `updated_state` as `state_snapshot` on the next turn.
2. **`status: "emergency"`**: Phase 2A Red Flag rule triggered. `immediate_attention_required: true`. `conversation_message` contains mandatory emergency alert. Pipeline short-circuits deterministically without LLM generation. Full emergency clinical output bundle is provided immediately.
3. **`status: "complete"`**: All required intake information has been extracted. `clinical_output` contains the complete multi-phase clinical bundle.

---

## 5. Structured Clinical Output Bundle (`StructuredClinicalOutputDTO`)

Emitted when `status == "complete"` or `status == "emergency"`. Contains unified results across all phases:

| Component | Responsible Phase | Schema / Contents |
|---|---|---|
| `case_id` | Core | Unique encounter case reference string |
| `patient_id` | Core | Patient identifier |
| `intake_summary` | Phase 1B | `chief_complaint`, `nature_of_pain`, `location`, `duration`, `severity`, `associated_symptoms` |
| `safety_findings` | Phase 2A | `red_flag_status`, `red_flags`, `red_flag_evidence`, `immediate_attention_required`, `red_flag_rule_hits` |
| `risk_assessment` | Phase 2B | `risk_level` (`LOW`/`MODERATE`/`HIGH`/`URGENT`), `risk_score` (0â€“100), `risk_signals`, `contributing_factors` |
| `clinical_case` | Phase 3 | Physician-ready clinical case object |
| `care_navigation` | Phase 4 | Matched facilities, specialized care pathways, transport/distance estimates |
| `follow_up_monitoring`| Phase 5 | Problem trajectory tracking (`improving`/`stable`/`worsening`/`new_risk_signal`) |
| `ayurveda_modern_representation` | Phase 7 | Descriptive dual-perspective concept mappings |
| `ayurveda_recommendation` | Phase 8B | Controlled lifestyle/dietary guidance with safety gating |
| `longitudinal_context`| Phase 9 | Patient problem timeline, recurrent complaints, biomarker trends |
| `advanced_risk_assessment` | Phase 10 | Longitudinal trajectory risk convergence bundle |
| `clinical_summary` | Phase 11 | Physician-ready clinical narrative across 12 clinical domains |
| `consultation_questions` | Phase 11 | Tailored patient consultation clarification questions |
| `dashavidha_atura_pariksha` | Phase 12 | Classical 10-parameter Ayurvedic examination profile (*Charaka Vimana 8/94*) |
| `provenance_notes` | Audit | Complete traceable provenance list across all 12 phases |

---

## 6. Safety & Non-Diagnostic Invariants

1. **Zero Diagnosis / Non-Prescriptive**: Output never generates definitive medical disease diagnoses or drug prescriptions.
2. **Missing != Absent**: Missing patient information (e.g. allergies, family history, ROS) is explicitly recorded as unassessed/not documentedâ€”never assumed normal or negative.
3. **Emergency Override Inviolability**: If an emergency red flag is triggered, `immediate_attention_required` remains `True` throughout all downstream structures and cannot be muted or downgraded by any downstream engine or LLM adapter.
4. **Deterministic Repeatability**: Identical inputs yield identical outputs across all execution passes.
