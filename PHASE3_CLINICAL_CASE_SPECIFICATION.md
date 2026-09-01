# PHASE 3: CLINICAL CASE REPRESENTATION SPECIFICATION

**Status**: Design Phase (PRE-IMPLEMENTATION)  
**Date**: 2026-09-01  
**Previous Phases**: Phase 1B (Adaptive Intake), Phase 2A (Red Flags), Phase 2B (Risk Convergence)

---

## 1. EXECUTIVE SUMMARY

Phase 3 transforms the internal VaidyaArc state (output from Phase 2B) into a **structured, physician-ready clinical case representation**. 

This representation is deterministic, non-inferential, and serves as the bridge between AI-driven assessment and clinician decision-making.

---

## 2. PHASE 3 GOALS

### Primary Goals
1. **Organize** Phase 1B/2A/2B outputs into clinically logical narrative structure
2. **Annotate** data quality and completeness metadata
3. **Preserve** all safety signals (red flags, risk scores) without modification or downgrade
4. **Prepare** information for physician review and clinical action
5. **Maintain** complete traceability to underlying rules and evidence

### What Phase 3 Does NOT Do
- ❌ Diagnose diseases
- ❌ Prescribe medications or treatments
- ❌ Infer new clinical facts
- ❌ Override Phase 2A red flags
- ❌ Downgrade Phase 2B risk scores
- ❌ Modify red-flag rules
- ❌ Provide clinical recommendations based on diagnosis
- ❌ Invent missing patient information

---

## 3. DATA FLOW

```
Phase 2B Output (risk_convergence)
    ↓
Phase 3 Node (clinical_case_representation)
    ↓
Clinical Case Structure (deterministic assembly)
    ↓
Physician Report Output
    ↓
End of Workflow (or downstream consumption)
```

---

## 4. INPUT CONTRACT (From Phase 2B)

Phase 3 receives complete VaidyaArcState with:

### Phase 1B Fields (Structured Intake)
- `chief_complaint` (str | None)
- `duration` (str | None)
- `severity` (str | None)
- `nature_of_pain` (str | None)
- `location` (str | None)
- `associated_symptoms` (list[str])
- `patient_profile` (dict: age, medical_conditions, allergies)
- `previous_history` (list[dict])
- `missing_information` (list[str])
- `information_complete` (bool)

### Phase 2A Fields (Red Flags)
- `red_flag_status` (str)
- `red_flags` (list[str])
- `red_flag_evidence` (list[str])
- `immediate_attention_required` (bool)
- `red_flag_rule_hits` (list[dict])

### Phase 2B Fields (Risk Convergence)
- `risk_level` (str: LOW, MODERATE, HIGH, URGENT)
- `risk_score` (int)
- `risk_signal_summary` (list[str])
- `risk_contributing_factors` (list[str])
- `risk_evidence` (list[str])
- `risk_reasoning` (str)
- `risk_override_reason` (str | None)
- `recommended_next_action` (str)
- `risk_rule_hits` (list[dict])
- `convergence_status` (str)
- `risk_context_flags` (list[str])

### Patient Identification
- `patient_id` (str)
- `session_id` (str)
- `language` (str)

---

## 5. OUTPUT CONTRACT (Phase 3 Clinical Case)

### New Schema: `ClinicalCase`

```
ClinicalCase:
  # 1. Case Metadata
  case_id: str                          # Auto-generated from patient_id + session_id
  created_at: str                       # ISO 8601 timestamp
  case_status: str                      # "complete", "incomplete", "pending_review"
  data_completeness_score: float        # 0.0-1.0 (percentage of expected fields populated)
  
  # 2. Patient Context
  patient_identifier:
    patient_id: str
    session_id: str
    age: int | None
    known_conditions: list[str]
    known_allergies: list[str]
    
  # 3. Chief Complaint & Present Concern
  chief_complaint: str | None           # Verbatim from intake
  complaint_narrative: str               # Structured narrative of complaint
  
  # 4. Temporal Information
  onset_description: str | None          # "Duration" field from Phase 1B
  
  # 5. Symptom Characteristics
  symptom_descriptors:
    severity: str | None                # From Phase 1B
    character: str | None               # nature_of_pain from Phase 1B
    location: str | None                # From Phase 1B
    associated_symptoms: list[str]      # From Phase 1B
    
  # 6. Patient History Context
  medical_history_summary: list[str]    # From patient_profile.medical_conditions
  relevant_history_notes: list[str]     # From previous_history
  
  # 7. Safety Signal Integration (FROM PHASE 2A - UNMODIFIED)
  safety_findings:
    red_flag_status: str                # Direct from Phase 2A
    red_flags_detected: list[str]       # Direct from Phase 2A
    red_flag_evidence: list[str]        # Direct from Phase 2A
    immediate_attention_required: bool  # Direct from Phase 2A
    red_flag_rule_summary: list[dict]   # Direct from Phase 2A
    
  # 8. Risk Assessment (FROM PHASE 2B - UNMODIFIED)
  risk_assessment:
    risk_level: str                     # LOW, MODERATE, HIGH, URGENT
    risk_score: int                     # 0-100 scale
    risk_signals: list[str]             # rule IDs
    risk_factors: list[str]             # Contributing factors
    risk_evidence: list[str]            # Evidence items
    risk_reasoning: str                 # Phase 2B explanation
    risk_override_reason: str | None    # If Phase 2A took precedence
    recommended_action: str             # From Phase 2B
    
  # 9. Data Quality & Completeness
  data_quality:
    information_complete: bool          # From Phase 1B
    missing_fields: list[str]           # From Phase 1B
    uncertain_fields: list[str]         # Fields with low confidence
    data_gaps: list[str]                # Gaps in the narrative
    
  # 10. Care Pathway Indication
  care_pathway_status: str              # "emergency", "urgent", "routine", "follow_up", "incomplete"
  
  # 11. Physician Notes
  case_summary: str                     # 1-2 sentence clinical summary
  next_steps: list[str]                 # Suggested actions (non-prescriptive)
  follow_up_required: bool              # Whether follow-up needed
  
  # 12. Traceability
  source_phase_evidence: dict[str, list[str]]  # Map: "phase_1b" → [...], "phase_2a" → [...], "phase_2b" → [...]
  audit_trail: list[dict]               # When each field was populated, from which phase
```

### New Schema: `ClinicalCaseOutput`

```
ClinicalCaseOutput:
  case_representation: ClinicalCase
  validation_errors: list[str]          # Any validation issues (non-blocking)
  validation_warnings: list[str]        # Warnings about data quality
  case_ready_for_review: bool           # Physician can review this case
  formatting_version: str               # "phase3_v1"
```

---

## 6. STATE MODIFICATIONS

### New Fields to Add to VaidyaArcState

```python
# Phase 3: Clinical Case Representation
clinical_case: Optional[dict[str, Any]]      # Full ClinicalCase structure
clinical_case_output: Optional[dict[str, Any]]  # Full ClinicalCaseOutput
case_generation_status: Optional[str]        # "generated", "pending", "failed"
case_validation_errors: list[str]            # Validation messages
```

---

## 7. NEW NODE: `clinical_case_representation`

### Responsibilities
1. **Extract** all relevant fields from VaidyaArcState
2. **Organize** into ClinicalCase structure
3. **Annotate** data quality and completeness
4. **Validate** required fields and consistency
5. **Generate** physician-ready summary
6. **Return** updated state with clinical_case fields

### Input
- VaidyaArcState (complete, from Phase 2B)

### Output
- Updated VaidyaArcState with:
  - `clinical_case` (ClinicalCase dict)
  - `clinical_case_output` (ClinicalCaseOutput dict)
  - `case_generation_status` (str)
  - `case_validation_errors` (list[str])

### Algorithm

```
1. VALIDATE input state completeness
   - Check Phase 1B data exists
   - Check Phase 2A data exists
   - Check Phase 2B data exists
   
2. EXTRACT patient context
   - Patient ID, session ID, age
   - Known conditions, allergies
   
3. BUILD chief complaint narrative
   - Use chief_complaint, duration, severity, nature, location
   - Format as structured symptom description
   
4. EXTRACT symptom descriptors
   - Severity, character, location
   - Associated symptoms list
   - Validate against Phase 1B fields
   
5. SUMMARIZE medical history
   - Convert patient_profile to narrative
   - Extract relevant prior history
   
6. COPY Phase 2A findings (UNMODIFIED)
   - red_flag_status → safety_findings.red_flag_status
   - red_flags → safety_findings.red_flags_detected
   - red_flag_evidence → safety_findings.red_flag_evidence
   - immediate_attention_required → safety_findings.immediate_attention_required
   
7. COPY Phase 2B findings (UNMODIFIED)
   - risk_level → risk_assessment.risk_level
   - risk_score → risk_assessment.risk_score
   - risk_signals, risk_factors, risk_evidence, risk_reasoning
   - risk_override_reason (if present)
   
8. CALCULATE data quality score
   - Completeness: (populated_fields / expected_fields) * 100
   - Identify missing_information, uncertain_fields
   
9. DETERMINE care_pathway_status
   - IF immediate_attention_required: "emergency"
   - ELSE IF risk_level == "URGENT": "urgent"
   - ELSE IF risk_level == "HIGH": "urgent"
   - ELSE IF risk_level == "MODERATE": "routine"
   - ELSE IF risk_level == "LOW": "routine"
   - ELSE IF NOT information_complete: "incomplete"
   - ELSE: "follow_up"
   
10. GENERATE case_summary (deterministic)
    - 1-2 sentence clinical summary from structured fields
    - Format: "{Age} yo {gender if known} presenting with {chief_complaint}. {Severity descriptor}. {Associated findings if relevant}."
    - NO DIAGNOSIS, NO TREATMENT RECOMMENDATIONS
    
11. BUILD next_steps (deterministic list)
    - IF immediate_attention_required: "Requires immediate clinical evaluation"
    - IF risk_level in [HIGH, URGENT]: "Prompt clinical consultation recommended"
    - IF information_complete: "Case ready for physician review"
    - IF NOT information_complete: "Additional patient information needed"
    - IF follow_up_required: "Recommend follow-up assessment"
    
12. VALIDATE entire structure
    - Check required fields present
    - Check for contradictions (e.g., high risk but no red flags)
    - Log any validation warnings
    
13. MARK case_ready_for_review
    - TRUE if: information_complete AND valid_structure
    - FALSE if: missing required fields OR validation errors
    
14. RETURN updated state
    - Set clinical_case = ClinicalCase dict
    - Set clinical_case_output = ClinicalCaseOutput dict
    - Set case_generation_status = "generated" or "failed"
```

---

## 8. WORKFLOW POSITION

### New Workflow Edge

```
evaluate_red_flags
    ↓
risk_convergence
    ↓
clinical_case_representation  [NEW]
    ↓
END
```

### No Conditional Routing
- clinical_case_representation is ALWAYS invoked after risk_convergence
- It does not conditionally route; it generates a case representation regardless
- If data is incomplete, case_ready_for_review will be FALSE, but the structure is still generated

---

## 9. DETERMINISTIC vs LLM RESPONSIBILITIES

### Phase 3 Core (DETERMINISTIC)
- ✅ Extracting and reorganizing existing fields
- ✅ Calculating data completeness score
- ✅ Applying deterministic routing logic (care_pathway_status)
- ✅ Formatting structured summaries
- ✅ Validating consistency

### Optional LLM Component (IF USED ONLY FOR SUMMARIZATION)
**CONSTRAINT**: LLM can ONLY summarize already-structured, verified information.

**NOT ALLOWED**:
- ❌ Inferring diagnoses
- ❌ Proposing treatment
- ❌ Adding clinical interpretation
- ❌ Modifying Phase 2A/2B outputs
- ❌ Guessing missing information

**IF CONSIDERED**:
- Use only for natural-language summarization of structured data
- Call AFTER all deterministic work
- Output a "human-readable summary" that echoes the structured case
- All clinical facts remain in structured form; summary is read-only

**Recommendation for Phase 3**: **START PURE DETERMINISTIC**. No LLM. All logic is rule-based.

---

## 10. VALIDATION RULES

### Pre-Validation (Input Checks)
- Phase 1B fields must exist and not be None (except missing_information)
- Phase 2A fields must exist (can be empty if no red flags)
- Phase 2B fields must exist (risk_level and risk_score must not be None)

### Consistency Checks
- If `immediate_attention_required` is TRUE, `risk_level` must be URGENT or HIGH
- If `risk_level` is URGENT, `red_flag_override_reason` OR `risk_override_reason` should explain why
- If `information_complete` is FALSE, `case_ready_for_review` must be FALSE
- If `red_flags_detected` is non-empty, `red_flag_status` must be "red_flags_detected"

### Data Quality Checks
- Completeness score reflects what was collected in Phase 1B
- Missing fields must align with `missing_information` list
- Uncertain fields should be flagged with warnings (low severity)

### Post-Validation (Output Checks)
- ClinicalCase structure must be valid Pydantic model
- All required fields populated
- Traceability links back to source phases

---

## 11. SAFETY CONSTRAINTS

### Immutability Constraints
1. **RED FLAGS ARE SACRED**: Never modify, downgrade, or reinterpret Phase 2A red flags
2. **RISK SCORES LOCKED**: Phase 2B risk scores and levels are read-only
3. **NO NEW FACTS**: Phase 3 does not invent or infer clinical information
4. **NO OVERRIDE**: Phase 3 does not provide alternate recommendations to Phase 2A/2B

### Clinical Safety
1. **Emergency Status is Sticky**: If `immediate_attention_required` is TRUE, `care_pathway_status` must be "emergency"
2. **Incomplete Data Transparency**: If data is incomplete, this must be clearly annotated
3. **Evidence Traceability**: Every clinical signal must link back to Phase 1B/2A/2B evidence
4. **No Diagnosis in Case Summary**: Case summary must be purely descriptive, no diagnostic labels

### Audit Trail
- Every field in ClinicalCase must have source attribution (phase_1b, phase_2a, or phase_2b)
- Timestamps mark when case was generated
- Validation errors/warnings are logged for review

---

## 12. TEST CASES

### Test Case 1: Complete High-Risk Case with Red Flags
**Scenario**: Severe chest pain, acute onset, shortness of breath
- **Input**: Information complete, red_flags_detected, risk_level=URGENT
- **Expected Output**:
  - case_ready_for_review = TRUE
  - care_pathway_status = "emergency"
  - safety_findings.immediate_attention_required = TRUE
  - risk_assessment.risk_override_reason is populated (explaining why URGENT)
  - case_summary includes severity descriptor
  - next_steps includes "Requires immediate clinical evaluation"

### Test Case 2: Incomplete Case with Missing Severity
**Scenario**: Patient reports stomach pain, duration not collected, severity not asked
- **Input**: information_complete = FALSE, missing_information = ['severity', 'duration']
- **Expected Output**:
  - case_ready_for_review = FALSE
  - case_generation_status = "generated" (still created, just marked incomplete)
  - data_completeness_score < 1.0
  - missing_fields includes 'severity' and 'duration'
  - care_pathway_status = "incomplete"
  - validation_warnings flagged

### Test Case 3: Low-Risk Routine Case
**Scenario**: Mild fever × 2 days, otherwise healthy
- **Input**: Information complete, no red flags, risk_level=LOW
- **Expected Output**:
  - case_ready_for_review = TRUE
  - care_pathway_status = "routine"
  - safety_findings.red_flag_status = "no_obvious_red_flags"
  - risk_assessment.risk_level = "LOW"
  - case_summary is brief and factual
  - next_steps includes "Follow-up assessment"

### Test Case 4: Elderly Patient with Chronic Conditions
**Scenario**: Severe fever × 5 days, history of diabetes and hypertension
- **Input**: Information complete, risk_level=HIGH, medical_conditions populated
- **Expected Output**:
  - medical_history_summary includes diabetes and hypertension
  - risk_assessment.risk_factors mentions age/chronic conditions
  - care_pathway_status = "urgent"
  - case_summary acknowledges chronic condition context

### Test Case 5: Phase 2A Override (Red Flag Takes Precedence)
**Scenario**: Difficulty breathing detected as red flag, even if base risk would be lower
- **Input**: immediate_attention_required = TRUE, risk_level = URGENT
- **Expected Output**:
  - care_pathway_status = "emergency"
  - risk_override_reason populated
  - safety_findings.immediate_attention_required = TRUE
  - next_steps emphasizes emergency pathway

---

## 13. FILE IMPACT

### New Files to Create
1. **app/clinical_case_schema.py**
   - Pydantic models: ClinicalCase, ClinicalCaseOutput
   - Validation logic for clinical case structure

2. **app/clinical_case_node.py**
   - Function: `clinical_case_representation(state: VaidyaArcState) → dict`
   - All deterministic transformation logic
   - Data quality scoring
   - Care pathway routing
   - Validation and error handling

3. **tests/_phase3_clinical_case_tests.py** (after implementation)
   - Unit tests for all 5 test cases above
   - Validation tests
   - Edge case tests

### Modified Files
1. **app/state.py**
   - Add clinical_case, clinical_case_output, case_generation_status, case_validation_errors fields

2. **app/workflow.py**
   - Import clinical_case_representation from clinical_case_node
   - Add node to builder: `builder.add_node("clinical_case_representation", clinical_case_representation)`
   - Add edge: `builder.add_edge("risk_convergence", "clinical_case_representation")`
   - Update final edge: `builder.add_edge("clinical_case_representation", END)`

### Unchanged Files
- ❌ **app/red_flag_rules.py** (FROZEN - Phase 2A)
- ❌ **app/nodes.py** (FROZEN for Phase 1B/2A/2B nodes; only add new code)
- ❌ **app/schemas.py** (No changes to existing schemas; only add new clinical_case schemas)

---

## 14. IMPLEMENTATION SEQUENCE (FOR APPROVAL)

1. ✅ **THIS SPECIFICATION** (Approval Gate 1)
2. **Create app/clinical_case_schema.py** with Pydantic models (Approval Gate 2)
3. **Create app/clinical_case_node.py** with clinical_case_representation logic (Approval Gate 2)
4. **Modify app/state.py** to add Phase 3 fields (Approval Gate 3)
5. **Modify app/workflow.py** to insert Phase 3 node (Approval Gate 3)
6. **Create tests/_phase3_clinical_case_tests.py** with all test cases (Approval Gate 4)
7. **Run full regression suite** (Phase 1B, 2A, 2B, 3) (Approval Gate 5)
8. **Final validation** with git diff showing only new/modified Phase 3 files (Approval Gate 6)

---

## 15. SUCCESS CRITERIA

✅ **Phase 3 is successful if**:
1. Clinical case representation is generated for every complete workflow execution
2. All Phase 1B/2A/2B data is preserved without modification
3. Case structure is valid and passes Pydantic validation
4. Data quality is accurately assessed
5. Care pathway status is correctly determined
6. All safety signals are preserved
7. Physician can review the structured case for clinical decision-making
8. Red flags are never downgraded or reinterpreted
9. No new clinical facts are inferred
10. All changes are deterministic and auditable
11. All 5 test cases pass
12. Full regression suite (Phase 1B/2A/2B) still passes
13. No changes to frozen phases

---

## APPROVAL CHECKPOINTS

- [ ] **CHECKPOINT 1**: Specification approved
- [ ] **CHECKPOINT 2**: Schemas and node code approved
- [ ] **CHECKPOINT 3**: State and workflow modifications approved
- [ ] **CHECKPOINT 4**: Tests pass
- [ ] **CHECKPOINT 5**: Regression suite passes
- [ ] **CHECKPOINT 6**: Ready to commit to GitHub
