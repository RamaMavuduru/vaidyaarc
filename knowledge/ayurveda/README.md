# VaidyaArc Phase 8B: Controlled Ayurveda Knowledge System

## 1. Overview & Purpose
The VaidyaArc Phase 8B Controlled Ayurveda Knowledge System provides an evidence-bounded, source-grounded repository and recommendation pipeline for traditional Ayurvedic remedies and pharmacopoeial formulations.

The primary mission is to offer culturally relevant, verified Ayurvedic home care and reference knowledge without compromising patient safety, without fabricating or hallucinating medical advice, and strictly adhering to the clinical safety invariants established in Phases 1–7.

---

## 2. Approved Sources & Governance Boundary

Phase 8B ingests knowledge **ONLY** from 3 approved, reviewed clinical documents:

1. **CCRAS Ayurvedic Home Remedies (English)**
   - **Document**: `Ayurvedic-Home-Remedies-English.pdf`
   - **Authority Level**: `primary_official`
   - **Publisher**: Central Council for Research in Ayurvedic Sciences (CCRAS), Department of AYUSH, Ministry of Health and Family Welfare, Govt. of India (2005)
   - **Role**: Primary practical guide for simple, accessible single-herb and home preparations suitable for self-care in mild, non-urgent indications.

2. **Ayurvedic Pharmacopoeia of India (API) Part II, Volume II**
   - **Document**: `API-II-Vol-2.pdf`
   - **Authority Level**: `primary_official`
   - **Publisher**: Ministry of AYUSH / Pharmacopoeia Commission for Indian Medicine & Homoeopathy, Govt. of India (2008)
   - **Role**: Statutory, standard pharmacopoeial formulations defining classical composition, classical therapeutic indications (*Rogadhikara*), and classical dosage/adjuvant (*Anupana*) references for clinician review.

3. **eCAM 2013 Review of Ayurvedic Formulations in Type 2 Diabetes**
   - **Document**: `ECAM2013-376327.pdf` (Evidence-Based Complementary and Alternative Medicine, 2013)
   - **Authority Level**: `secondary_literature`
   - **Role**: Secondary academic/scientific literature providing background observational and biochemical context.
   - **Governance Policy**: Categorized strictly as `secondary_evidence`. Cannot independently generate unrestricted direct patient recommendations without clinical consultation.

### Explicitly Excluded Sources
- **The Fourth Source (`CRIS-05-2024.pdf`)**: Excluded from Phase 8B ingestion due to pending review of scope, provenance, and clinical verification boundaries.
- **Unbounded Web / LLM Knowledge**: Strictly prohibited. No generative invention of indications, contraindications, dosages, ingredients, or citations is permitted.

---

## 3. Source Hierarchy & Precedence Rules

1. **Primary Official Sources Precedence**:
   - `primary_official` records (CCRAS Home Remedies, API Part II Vol II) receive highest ranking priority (`authority_score` bonus `+100.0`).
2. **Secondary Literature Precedence**:
   - `secondary_literature` records (eCAM 2013) receive standard ranking (`authority_score` bonus `+10.0`) and are tagged with `remedy_type = "secondary_evidence"`.
3. **Safety Gate Dominance**:
   - Clinical safety decisions (Phase 2A red flags, Phase 2B risk severity) unconditionally override all knowledge matches.

---

## 4. Ingestion Process & Schema Architecture

All ingested records in `knowledge/ayurveda/ingested_records.json` are validated against Pydantic v2 models defined in [`app/ayurveda_knowledge_schema.py`](../../app/ayurveda_knowledge_schema.py):

- **Record Schema (`AyurvedaKnowledgeRecord`)**:
  - `record_id`: Unique identifier (e.g., `CCRAS_HR_001`, `API2_V2_001`, `ECAM_T2D_001`).
  - `name`: Common/classical name.
  - `sanskrit_name`: Classical Sanskrit name (where applicable).
  - `record_type`: `home_remedy`, `pharmacopoeial_formulation`, or `literature_evidence`.
  - `authority_level`: `primary_official` vs `secondary_literature`.
  - `indications`: Normalized symptom strings and classical indications.
  - `ingredients`: Detailed list of ingredients with parts used and ratios.
  - `contraindications`: Stated medical and physiological exclusions.
  - `source_dosage_info`: Classical reference dosage text as stated in the source.
  - `preparation_method`: Classical or home preparation steps.
  - `anupana`: Stated vehicle/adjuvant (e.g., warm water, honey, milk).
  - `safety_notes`: Precautionary guidance.
  - `limitations`: Contextual and research limitations.
  - `provenance`: Full citation including `source_id`, `document_title`, `publisher`, `publication_year`, `page_number`, and `source_excerpt`.

---

## 5. Candidate Retrieval Engine

Implemented in [`app/ayurveda_retriever.py`](../../app/ayurveda_retriever.py):
- Deterministic token and synonym matching between patient symptoms/chief complaints and record indications.
- Scoring mechanism:
  $$\text{Score} = \text{Exact Matches} \times 10.0 + \text{Partial Matches} \times 3.0 + \text{Authority Bonus}$$
- Results sorted by score descending, returning top verified candidate matches with exact matched symptoms.

---

## 6. Safety Screening & Policy Gate

Implemented in [`app/ayurveda_safety_gate.py`](../../app/ayurveda_safety_gate.py):

### Hard Blocking Criteria
1. **Phase 2A Emergency / Immediate Attention**:
   - Any red flag or `immediate_attention_required == True` immediately sets status to `BLOCKED`.
2. **Phase 2B High Risk / Urgent Care**:
   - `risk_level in ["HIGH", "URGENT"]` immediately sets status to `BLOCKED`.
3. **Severe Symptoms**:
   - Severity >= 8/10 or described as "severe", "crushing", "worst", "unbearable" sets status to `BLOCKED`.
4. **Allergies & Contraindications**:
   - Known patient allergies matching remedy ingredients immediately block that specific candidate.

### Preservation of Unknowns
- Unknown pregnancy status, pediatric status, or unstated allergies remain explicit `unknowns` and trigger cautious physician review (`requires_clinician_review`) rather than being assumed safe.

---

## 7. Recommendation Lifecycle & Non-Prescription Framing

Implemented in [`app/ayurveda_recommendation.py`](../../app/ayurveda_recommendation.py):

```
Knowledge Match != Eligible Candidate != Recommendation != Prescription
```

- **Knowledge Match**: Raw retrieval match from ingested documents.
- **Eligible Candidate**: Knowledge match passed through Phase 2A/2B safety screening.
- **Recommendation**: Filtered, prioritized home care item or physician reference formulation.
- **Prescription**: **NEVER generated**. Dosages are strictly labeled `source_dosage_reference` and accompanied by mandatory disclaimers:
  > *"This information is provided for educational and supportive home care reference only. It does not constitute a medical prescription or diagnostic claim. Consult a qualified Ayurvedic physician or medical practitioner for treatment."*

---

## 8. Provenance & Auditability

Every recommendation output contains complete provenance metadata (`SourceProvenance`):
- `source_id`
- `document_title`
- `publisher`
- `publication_year`
- `page_number`
- `source_excerpt`

This guarantees end-to-end traceability from the final output back to the specific line and page in the approved government or pharmacopoeial PDF.

