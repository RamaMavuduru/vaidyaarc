# VAIDYAARC PROJECT SPECIFICATION

## 1. PROJECT NAME

VaidyaArc

AI-Powered Health Intake, Risk Assessment, Patient Monitoring, Healthcare Navigation, and Physician Decision-Support System.

---

# 2. PROJECT PURPOSE

VaidyaArc is an AI-powered healthcare decision-support and patient-navigation system.

The system is NOT an autonomous doctor.

The system must NOT independently provide a definitive medical diagnosis or replace a qualified healthcare professional.

The primary purpose of VaidyaArc is to:

* Understand the patient's current health concern.
* Retrieve and use relevant existing patient information.
* Conduct adaptive history-taking.
* Convert patient responses into structured clinical information.
* Perform relevant Ayurvedic assessment using an approved knowledge base.
* Create a unified representation using both modern clinical and Ayurvedic perspectives.
* Detect configured red flags.
* Assess risk using deterministic or validated rules.
* Perform risk convergence analysis.
* Classify the patient as LOW, MODERATE, HIGH, or URGENT.
* Provide appropriate care navigation.
* Provide low-risk supportive Ayurvedic guidance only when eligible and supported by the approved knowledge base.
* Recommend clinical consultation when required.
* Recommend suitable healthcare facilities.
* Identify potentially relevant government healthcare schemes.
* Support follow-up monitoring.
* Maintain a longitudinal patient timeline.
* Generate a unified physician-ready report.

The system must prioritize:

1. Patient safety
2. Data integrity
3. Explainability
4. Privacy
5. Clinician verification
6. Longitudinal monitoring
7. Modular architecture

---

# 3. CURRENT TECHNOLOGY STACK

The current development environment is:

* Python 3.11
* LangGraph
* LangChain
* Ollama
* llama3:latest
* Pydantic

The current project is being developed locally.

Future components may include:

* FastAPI
* PostgreSQL
* SQLite for initial development
* pgvector or Chroma for knowledge retrieval
* OCR / Document AI
* Speech-to-Text
* Text-to-Speech
* Frontend application

Do not introduce unnecessary dependencies.

Prefer simple, modular, maintainable Python code.

---

# 4. CURRENT PROJECT STRUCTURE

Current structure:

Vaidyaarc/

```
main.py

app/
    __init__.py
    state.py
    schemas.py
    nodes.py
    workflow.py
```

The project already contains an initial multi-turn patient intake workflow.

Do not rebuild the project from scratch unless absolutely necessary.

Analyze and improve the existing architecture incrementally.

---

# 5. CENTRAL ARCHITECTURE

The intended high-level architecture is:

PATIENT PROFILE
↓
CURRENT PATIENT MESSAGE
↓
CENTRAL VAIDYAARC ORCHESTRATOR
↓
ADAPTIVE INTAKE
↓
STRUCTURED PATIENT STATE
↓
RED FLAG DETECTION
↓
RISK / SEVERITY ENGINE
↓
RISK CONVERGENCE
↓
LOW / MODERATE / HIGH / URGENT
↓
APPROPRIATE CARE PATHWAY
↓
FOLLOW-UP
↓
REASSESSMENT
↓
LONGITUDINAL PATIENT TIMELINE

---

# 6. CENTRAL ORCHESTRATOR

VaidyaArc acts as the central orchestrator.

The central workflow may eventually communicate with specialized components:

1. Adaptive Intake Engine
2. Structured Clinical Information Engine
3. Ayurvedic Assessment Engine
4. Red Flag Detection Engine
5. Risk and Severity Engine
6. Risk Convergence Engine
7. Ayurvedic Knowledge Base
8. Document Intelligence / OCR
9. Government Scheme Engine
10. Hospital Recommendation Engine
11. Follow-up Engine
12. Patient Timeline Engine
13. Unified Physician Report Generator

The central LLM is responsible for:

* Understanding patient language.
* Extracting structured information.
* Asking adaptive questions.
* Organizing information.
* Explaining system decisions.

The LLM must NOT be the only component responsible for clinical risk classification.

Safety-critical classification should use deterministic rules or validated tools where available.

---

# 7. PATIENT PROFILE

A patient profile may contain:

* Patient ID
* Basic demographic information
* Age
* Sex or gender where relevant
* Location
* Preferred language
* Existing medical conditions
* Current medications
* Known allergies
* Relevant medical history
* Relevant Ayurvedic profile
* ABHA information where available
* Previous consultations
* Previous medical documents
* Previous symptoms or episodes
* Previous risk assessments
* Previous recommendations
* Follow-up history
* Consent information

Do not repeatedly ask for information that already exists and is reliable.

Use relevant previous information when processing a new patient concern.

Never invent patient information.

---

# 8. CURRENT PATIENT SESSION

When a patient reports a new health concern:

Do NOT immediately recommend treatment.

First understand the patient's main complaint.

Collect additional information adaptively.

Do not ask every possible medical question.

Ask only questions relevant to understanding the current case.

Possible information may include:

* Main complaint
* Duration
* Location
* Nature
* Severity
* Frequency
* Progression
* Aggravating factors
* Relieving factors
* Associated symptoms
* Previous episodes
* Current medications
* Allergies
* Existing medical conditions
* Previous investigations
* Relevant lifestyle factors
* Relevant warning signs

The system should ask only one or a small number of questions at a time.

Questions must be understandable to ordinary patients.

---

# 9. CURRENT IMPLEMENTATION REQUIREMENT

The current implementation begins with adaptive intake.

The system must:

1. Receive a patient message.
2. Extract only new information explicitly provided in that message.
3. Preserve previously collected information.
4. Prevent None or empty values from overwriting valid previous information.
5. Identify which information is still missing.
6. Ask the most relevant next question.
7. Continue until sufficient information has been collected.
8. Then proceed to safety and risk assessment.

Example:

Patient:
I have stomach pain.

System:
Can you describe what the pain feels like?

Patient:
It feels like burning.

System:
Where exactly are you feeling the pain?

Patient:
In my upper abdomen.

System:
When did this problem start?

The previous information must remain preserved throughout the conversation.

The system must not forget:

Chief complaint:
stomach pain

Nature of pain:
burning

Location:
upper abdomen

when later messages provide new information.

---

# 10. STRUCTURED MODERN CLINICAL INFORMATION

Where relevant, the system should capture:

* Chief complaint
* History of present illness
* Duration
* Severity
* Location
* Nature
* Associated symptoms
* Progression
* Aggravating factors
* Relieving factors
* Relevant past medical history
* Past surgical history
* Medication history
* Allergy history
* Family history
* Personal or social history
* Relevant review of systems
* Relevant investigations
* Relevant previous diagnoses
* Relevant consultation history

Do not invent missing information.

If information is unknown, keep it as unknown or None.

The exact fields required should eventually depend on the patient's complaint.

Do not require pain-specific fields for every possible health complaint.

The intake system should become complaint-adaptive.

---

# 11. ADAPTIVE QUESTIONING

The system should not use a fixed questionnaire for every patient.

The workflow should adapt based on:

* Chief complaint
* Previous answers
* Existing patient history
* Current risk factors
* Possible red flags
* Information still required

Example:

For pain-related complaints:

* Location
* Nature
* Duration
* Severity
* Progression
* Associated symptoms

For respiratory complaints:

* Breathing difficulty
* Cough
* Duration
* Fever
* Chest discomfort
* Relevant associated symptoms

The architecture should support different complaint-specific intake pathways.

Do not implement all complaint pathways immediately.

Start with a simple generic architecture and expand incrementally.

---

# 12. AYURVEDIC REPRESENTATION

When appropriate, VaidyaArc may collect relevant Ayurvedic information.

Potential information includes:

* Prakriti
* Vikriti
* Agni
* Koshtha
* Ahara
* Vihara
* Nidana
* Relevant Dashavidha Pariksha parameters

Do not force Ayurvedic questions into every interaction.

Only collect Ayurvedic information when relevant to the current assessment.

All Ayurvedic guidance must come from an approved Ayurvedic knowledge base.

The system must NOT invent Ayurvedic remedies, dosages, or medical claims.

---

# 13. MODERN MEDICINE AND AYURVEDA BRIDGE

The system should create one unified patient representation.

The system should distinguish:

1. Modern clinical information
2. Ayurvedic observations
3. Overlapping observations
4. Framework-specific observations

Do not claim that Ayurvedic concepts are equivalent to modern medical diagnoses unless explicitly supported by the approved knowledge base.

Ayurvedic interpretation must never override medically significant warning signs.

---

# 14. RED FLAG DETECTION

After sufficient relevant information has been collected, the system should run red flag detection.

Red flag detection must be implemented as a separate component.

The red flag engine should preferably use deterministic, configurable rules.

The LLM may help extract symptoms and contextual information, but the final configured red flag logic should not depend entirely on LLM intuition.

The red flag engine should return structured information such as:

* Detected red flags
* Rule or condition that triggered the flag
* Relevant patient information
* Escalation recommendation

The exact clinical rules should be configurable and reviewable.

Do not invent clinical guidelines or rules.

For development, use clearly identified placeholder or demonstration rules only when explicitly configured.

---

# 15. RISK AND SEVERITY ENGINE

The patient risk categories are:

* LOW
* MODERATE
* HIGH
* URGENT

Risk assessment should consider relevant factors such as:

* Current symptoms
* Severity
* Duration
* Progression
* Associated symptoms
* Red flags
* Existing conditions
* Medication history
* Relevant previous history
* Relevant medical documents
* Patient-specific risk factors
* Previous risk state
* Changes since previous assessment

The LLM should interpret and organize information.

The final risk classification should use deterministic or validated rules where possible.

Do not fabricate numerical severity scores.

---

# 16. RISK CONVERGENCE

The system must not evaluate every symptom independently.

Multiple individually mild factors may converge into a more significant risk pattern.

Example:

Multiple low-level symptoms
+
Relevant medical history
+
Worsening progression
↓
Higher combined risk

Risk convergence should be implemented as a separate modular component.

The system must preserve explainability by recording which factors contributed to escalation.

An urgent red flag must always override lower-risk interpretations.

---

# 17. LOW-RISK PATHWAY

If the patient is classified as LOW risk and no relevant red flags are present:

1. Determine whether supportive Ayurvedic guidance is eligible.
2. Retrieve information from the approved Ayurvedic knowledge base.
3. Provide only approved low-risk supportive guidance.
4. Prefer:

   * Diet guidance
   * Lifestyle guidance
   * Low-risk supportive practices
5. Clearly explain limitations.
6. Provide monitoring instructions.
7. Recommend follow-up where appropriate.

Do NOT:

* Invent remedies
* Invent dosages
* Recommend unsupported treatment
* Claim a cure
* Tell patients to delay urgent medical care

If sufficient knowledge is unavailable, state that the information is unavailable.

---

# 18. MODERATE-RISK PATHWAY

For MODERATE risk:

* Collect additional information when necessary.
* Monitor the patient.
* Provide only guidance permitted by configured safety rules.
* Recommend clinical evaluation when required.
* Schedule reassessment where appropriate.
* Escalate if the patient's condition worsens.

Do not automatically assume self-care is sufficient.

---

# 19. HIGH-RISK PATHWAY

For HIGH risk:

1. Recommend consultation with an appropriate qualified healthcare professional.
2. Do not present the interaction as a replacement for medical evaluation.
3. Generate a unified physician-ready report.
4. Retrieve relevant patient history.
5. Retrieve relevant documents and investigations.
6. Run hospital recommendation logic.
7. Run government scheme recommendation logic where relevant.
8. Generate patient-specific questions for the healthcare professional.

---

# 20. URGENT PATHWAY

If an urgent configured red flag or emergency condition is detected:

* Classify the case as URGENT.
* Do not recommend waiting for routine follow-up.
* Do not recommend routine self-care as a substitute for urgent evaluation.
* Trigger the configured emergency or priority escalation mechanism.
* Clearly advise immediate appropriate medical attention.
* Where supported, identify suitable emergency-capable facilities.
* Generate a concise urgent clinical summary.

Urgent safety rules must always override lower-risk pathways.

---

# 21. FOLLOW-UP AND LONGITUDINAL MONITORING

VaidyaArc is intended to be a longitudinal system.

During follow-up:

Retrieve:

* Previous complaint
* Previous answers
* Previous risk category
* Previous recommendations
* Relevant patient history
* New symptoms
* Changes in severity
* New documents
* New consultations

Determine whether the patient is:

* Improving
* Stable
* Worsening

Detect:

* New symptoms
* New red flags
* Risk category changes

Maintain a symptom and risk trajectory.

Example:

Day 0:
LOW

Day 2:
LOW

Day 4:
MODERATE

The system should detect worsening and apply configured escalation logic.

---

# 22. MEDICAL DOCUMENT INTELLIGENCE

When medical documents are uploaded:

Use OCR or Document AI.

Potential extraction fields include:

* Document type
* Date
* Healthcare provider
* Diagnosis
* Medications
* Dosages
* Investigation names
* Investigation values
* Units
* Reference ranges
* Procedures
* Surgeries
* Relevant clinical findings

OCR results may be incorrect.

Uncertain information must be marked for verification.

Documents should be organized chronologically.

Do not overwrite historical information.

---

# 23. PATIENT TIMELINE

Maintain a chronological patient record.

The timeline may contain:

* Registration events
* Medical documents
* Consultations
* Symptoms
* Episodes
* Investigations
* Medications
* Risk assessments
* Follow-ups
* Recommendations
* Hospital referrals
* Government scheme recommendations

Never overwrite previous medical events.

Historical records should remain preserved.

---

# 24. GOVERNMENT HEALTHCARE SCHEME ENGINE

The system may recommend potentially relevant government healthcare schemes.

Possible scheme categories include:

* Ayushman Bharat
* PM-JAY
* Major national healthcare schemes
* Relevant state-specific schemes

Eligibility must be based on structured and authoritative information.

The system may return:

* Scheme name
* Why it may be relevant
* Eligibility criteria that appear to match
* Missing eligibility information
* Required documents
* Application or access pathway

Never state that a patient is definitely eligible unless verified through an authoritative eligibility mechanism.

Use wording such as:

Potentially relevant

Potentially eligible pending verification

---

# 25. HOSPITAL AND HEALTHCARE FACILITY RECOMMENDATION

The goal is not simply to recommend the nearest hospital.

The Hospital Recommendation Engine should consider:

* Patient location
* Required specialty
* Risk category
* Emergency capability
* Available departments
* Specialist availability
* Facility capabilities
* Service availability
* Government or private status
* Scheme compatibility
* Ayurveda and modern medicine capabilities where relevant

Facilities should be ranked using defined criteria.

Use wording such as:

Most suitable facility based on available criteria.

Do not claim that a facility is objectively the best unless supported by a defined ranking methodology.

---

# 26. PRE-CONSULTATION QUESTIONS

When clinical consultation is recommended, generate useful discussion questions based on:

* Current symptoms
* Previous history
* Current medications
* Recent reports
* Unresolved symptoms
* Risk factors
* Previous consultations

Examples:

* What could be causing these symptoms?
* Do I need further investigations?
* Could any existing medication be relevant?
* What warning signs should I monitor?
* What should I do if the symptoms worsen?
* When should I follow up?

These must be discussion points, not AI-generated medical conclusions.

---

# 27. UNIFIED PHYSICIAN REPORT

When consultation is recommended, generate one unified report.

The report may include:

1. Patient profile
2. Current complaint
3. History of present illness
4. Relevant previous history
5. Medication history
6. Allergy history
7. Relevant family or personal history
8. Relevant investigations
9. OCR-extracted information
10. Chronological medical context
11. Modern clinical information
12. Ayurvedic assessment
13. Unified interpretation
14. Risk category
15. Risk convergence factors
16. Symptom and risk trajectory
17. Previous recommendations
18. Reason for consultation
19. Suggested discussion questions

The report is a DRAFT for clinician review.

A clinician must be able to:

* Review
* Edit
* Correct
* Accept
* Reject

The report must never be presented as a final diagnosis.

---

# 28. PATIENT RESPONSE STYLE

When communicating with patients:

* Use simple language.
* Support the preferred language when implemented.
* Ask one or a small number of questions at a time.
* Avoid unnecessary medical jargon.
* Clearly distinguish information from diagnosis.
* Be concise.
* Do not expose unnecessary internal reasoning.
* Clearly explain when professional evaluation is recommended.

---

# 29. DATA INTEGRITY RULES

Never fabricate:

* Patient information
* Medical history
* Symptoms
* Test results
* Diagnoses
* Medication history
* Allergies
* Ayurvedic facts
* Government scheme eligibility
* Hospital capabilities
* Hospital availability
* Locations
* Clinical outcomes

If information is unavailable, explicitly mark it as unavailable.

If information is uncertain, mark it as uncertain.

---

# 30. CLINICAL SAFETY RULES

VaidyaArc is a decision-support and patient-navigation system.

It must NOT:

* Claim definitive diagnosis.
* Replace a qualified healthcare professional.
* Ignore red flags.
* Tell urgent or high-risk patients to wait unnecessarily.
* Generate unsupported treatment.
* Invent Ayurvedic remedies.
* Invent medication dosages.
* Override deterministic safety rules.
* Hide uncertainty.

Configured safety rules always take priority over conversational convenience.

---

# 31. SOFTWARE DEVELOPMENT REQUIREMENTS

The system should be built incrementally.

Each component should:

* Have a clear responsibility.
* Be independently testable.
* Avoid unnecessary dependencies.
* Use structured inputs and outputs where possible.
* Avoid tightly coupling all logic into one file.
* Preserve backward compatibility where reasonable.

Do not rewrite the entire project every time a new feature is added.

Prefer adding modules such as:

app/
state.py
schemas.py
nodes.py
workflow.py
red_flag_engine.py
risk_engine.py
risk_convergence.py
care_pathways.py
ayurveda_engine.py
follow_up.py
timeline.py
report_generator.py

Additional files should only be created when necessary.

---

# 32. DEVELOPMENT ROADMAP

The implementation should proceed in this order.

PHASE 1:
Fix and stabilize multi-turn adaptive intake.

PHASE 2:
Make intake complaint-adaptive instead of requiring the same fields for every complaint.

PHASE 3:
Implement configurable red flag detection.

PHASE 4:
Implement deterministic risk classification.

PHASE 5:
Implement risk convergence.

PHASE 6:
Implement LOW, MODERATE, HIGH, and URGENT routing.

PHASE 7:
Implement patient follow-up and reassessment.

PHASE 8:
Implement longitudinal patient timeline.

PHASE 9:
Implement unified physician report generation.

PHASE 10:
Implement approved Ayurvedic knowledge retrieval and supportive guidance.

PHASE 11:
Implement document upload and OCR integration.

PHASE 12:
Implement government scheme recommendation.

PHASE 13:
Implement hospital recommendation.

PHASE 14:
Implement API and frontend interface.

Do not skip directly to later phases while the central safety and intake workflow is unstable.

---

# 33. CURRENT DEVELOPMENT PRIORITY

The current priority is:

1. Stabilize the existing LangGraph multi-turn intake system.
2. Ensure patient information persists correctly between turns.
3. Make the intake logic adaptive.
4. Add deterministic red flag detection.
5. Add deterministic risk classification.
6. Add risk convergence.
7. Build the care pathway router.

Do not implement all future components immediately.

Build, test, and validate one module at a time.

---

# 34. COPILOT IMPLEMENTATION RULES

When modifying this project:

1. First inspect the existing files.
2. Understand the current architecture before modifying code.
3. Explain the proposed changes before making them.
4. Do not unnecessarily rewrite working files.
5. Preserve working functionality.
6. Keep code beginner-friendly and readable.
7. Use clear function and variable names.
8. Add comments only where useful.
9. Ensure imports are correct.
10. Check that functions referenced in workflow files actually exist.
11. Avoid generating placeholder functions that appear complete but contain no real logic.
12. Do not silently invent clinical rules or medical facts.
13. Keep safety-critical logic deterministic and configurable.
14. Make each new module testable.
15. Prefer incremental implementation and testing.

---

# 35. FINAL OBJECTIVE

The final VaidyaArc system should follow this overall flow:

PATIENT PROFILE
↓
CURRENT HEALTH CONCERN
↓
ADAPTIVE HISTORY-TAKING
↓
STRUCTURED PATIENT INFORMATION
↓
MODERN CLINICAL REPRESENTATION
+
RELEVANT AYURVEDIC REPRESENTATION
↓
UNIFIED PATIENT STATE
↓
RED FLAG DETECTION
↓
RISK ASSESSMENT
↓
RISK CONVERGENCE
↓
LOW / MODERATE / HIGH / URGENT
↓
APPROPRIATE CARE PATHWAY
↓
SUPPORTIVE GUIDANCE
OR
CLINICAL CONSULTATION
OR
URGENT ESCALATION
↓
HOSPITAL RECOMMENDATION
↓
GOVERNMENT SCHEME NAVIGATION
↓
FOLLOW-UP
↓
REASSESSMENT
↓
LONGITUDINAL PATIENT TIMELINE
↓
UNIFIED PHYSICIAN-READY REPORT

The system must remain a patient-support, clinician-assist, and healthcare-navigation system with human clinical oversight.
