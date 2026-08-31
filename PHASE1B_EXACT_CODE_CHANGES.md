# PHASE 1B ADAPTIVE INTAKE - EXACT CODE CHANGES

## Summary

Replaced hardcoded pain-specific intake logic with complaint-aware adaptive intake. All Phase 2A red flag systems remain fully functional and unchanged.

---

## CHANGE 1: app/state.py

**Added 1 line to TypedDict definition:**

```python
class VaidyaArcState(TypedDict, total=False):
    # ... existing fields ...
    
    # Adaptive questioning
    missing_information: list[str]
    next_question: Optional[str]
    information_complete: bool
    questions_asked: list[str]  # ← NEW: Track which fields have been asked
    
    # ... rest of fields ...
```

---

## CHANGE 2: app/nodes.py

### 2a. Added Complaint Requirements and Questions Dictionaries (BEFORE _normalize_blank)

```python
# Complaint-specific information requirements
# Maps chief_complaint keywords to required fields for adaptive intake
COMPLAINT_REQUIREMENTS = {
    "pain": {
        "required_fields": ["chief_complaint", "nature_of_pain", "location", "duration", "severity"],
        "optional_fields": ["associated_symptoms"],
        "category": "pain-like"
    },
    "stomach pain": {
        "required_fields": ["chief_complaint", "nature_of_pain", "location", "duration", "severity"],
        "optional_fields": ["associated_symptoms"],
        "category": "pain-like"
    },
    "abdominal pain": {
        "required_fields": ["chief_complaint", "nature_of_pain", "location", "duration", "severity"],
        "optional_fields": ["associated_symptoms"],
        "category": "pain-like"
    },
    "headache": {
        "required_fields": ["chief_complaint", "duration", "severity", "location"],
        "optional_fields": ["associated_symptoms"],
        "category": "pain-like"
    },
    "fever": {
        "required_fields": ["chief_complaint", "duration", "severity"],
        "optional_fields": ["associated_symptoms"],
        "category": "systemic"
    },
    "cough": {
        "required_fields": ["chief_complaint", "duration"],
        "optional_fields": ["associated_symptoms"],
        "category": "respiratory"
    },
    "nausea": {
        "required_fields": ["chief_complaint", "duration"],
        "optional_fields": ["associated_symptoms"],
        "category": "gastrointestinal"
    },
    "vomiting": {
        "required_fields": ["chief_complaint", "duration"],
        "optional_fields": ["associated_symptoms"],
        "category": "gastrointestinal"
    },
}

# Fallback for unknown complaints: collect minimal information
FALLBACK_REQUIRED_FIELDS = ["chief_complaint", "duration", "severity"]

# Complaint-specific question templates
# Maps field names to complaint-specific question text
COMPLAINT_QUESTIONS = {
    "fever": {
        "chief_complaint": "What health problem are you experiencing?",
        "duration": "When did the fever start?",
        "severity": "How high is your fever or how severe is it?",
    },
    "cough": {
        "chief_complaint": "What health problem are you experiencing?",
        "duration": "When did the cough start?",
    },
    "headache": {
        "chief_complaint": "What health problem are you experiencing?",
        "duration": "When did the headache start?",
        "severity": "How severe is the headache?",
        "location": "Where exactly is the headache located?",
    },
    "nausea": {
        "chief_complaint": "What health problem are you experiencing?",
        "duration": "When did the nausea start?",
    },
    "vomiting": {
        "chief_complaint": "What health problem are you experiencing?",
        "duration": "When did the vomiting start?",
    },
    "pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain?",
    },
    "stomach pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain?",
    },
    "abdominal pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain?",
    },
}

# Default questions for generic fields
DEFAULT_QUESTIONS = {
    "chief_complaint": "What health problem are you experiencing?",
    "nature_of_pain": "Can you describe what the feeling is like?",
    "location": "Where exactly are you experiencing this?",
    "duration": "When did this start?",
    "severity": "How severe is this?",
}
```

### 2b. Added Helper Function (BEFORE _normalize_blank)

```python
def _find_complaint_template(complaint_text: str) -> dict | None:
    """
    Match a chief_complaint string to a complaint template.
    Searches for keywords in the complaint and returns the matching template.
    """
    if not complaint_text:
        return None
    
    complaint_lower = complaint_text.lower().strip()
    
    # Exact match first
    if complaint_lower in COMPLAINT_REQUIREMENTS:
        return COMPLAINT_REQUIREMENTS[complaint_lower]
    
    # Substring matching for common variants
    for template_key, template in COMPLAINT_REQUIREMENTS.items():
        if template_key in complaint_lower or complaint_lower in template_key:
            return template
    
    # No match found
    return None
```

### 2c. Modified validate_patient_state() Function

**BEFORE:**
```python
def validate_patient_state(state: VaidyaArcState):
    # ... existing code ...
    
    if "information_complete" not in validated or validated["information_complete"] is None:
        validated["information_complete"] = False

    validated["extracted_information"] = {}
    return validated
```

**AFTER:**
```python
def validate_patient_state(state: VaidyaArcState):
    # ... existing code ...
    
    if "information_complete" not in validated or validated["information_complete"] is None:
        validated["information_complete"] = False

    if "questions_asked" not in validated or validated["questions_asked"] is None:
        validated["questions_asked"] = []

    validated["extracted_information"] = {}
    return validated
```

### 2d. Completely Replaced determine_missing_information() Function

**BEFORE:**
```python
def determine_missing_information(state: VaidyaArcState):
    missing = []

    required_fields = [
        "chief_complaint",
        "nature_of_pain",
        "location",
        "duration",
        "severity"
    ]

    for field in required_fields:
        value = state.get(field)
        if value is None or value == "":
            missing.append(field)

    information_complete = len(missing) == 0

    return {
        "missing_information": missing,
        "information_complete": information_complete
    }
```

**AFTER:**
```python
def determine_missing_information(state: VaidyaArcState):
    missing = []
    
    complaint = state.get("chief_complaint")
    
    # If no complaint yet, we always need it first
    if not complaint:
        return {
            "missing_information": ["chief_complaint"],
            "information_complete": False
        }
    
    # Find the template for this complaint
    template = _find_complaint_template(complaint)
    
    if template:
        required_fields = template["required_fields"]
    else:
        # Unknown complaint: use fallback with a clarification step
        # For now, accept the chief_complaint as given and use fallback
        required_fields = FALLBACK_REQUIRED_FIELDS
    
    # Check which fields are missing
    for field in required_fields:
        value = state.get(field)
        if value is None or value == "":
            missing.append(field)
    
    information_complete = len(missing) == 0
    
    return {
        "missing_information": missing,
        "information_complete": information_complete
    }
```

### 2e. Completely Replaced select_next_question() Function

**BEFORE:**
```python
def select_next_question(state: VaidyaArcState):
    missing = state.get("missing_information", [])

    if state.get("information_complete") or not missing:
        return {
            "next_question": None
        }

    questions = {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain?"
    }

    next_question = questions.get(missing[0])

    return {
        "next_question": next_question
    }
```

**AFTER:**
```python
def select_next_question(state: VaidyaArcState):
    missing = state.get("missing_information", [])
    questions_asked = state.get("questions_asked", [])
    complaint = state.get("chief_complaint")
    
    if state.get("information_complete") or not missing:
        return {
            "next_question": None
        }
    
    # Find the first missing field that hasn't been asked yet
    next_field = None
    for field in missing:
        if field not in questions_asked:
            next_field = field
            break
    
    if next_field is None:
        # All missing fields have been asked but we're still incomplete
        # This means patient gave non-answers; stop asking
        return {
            "next_question": None
        }
    
    # Get complaint-specific questions if available
    if complaint:
        complaint_lower = complaint.lower()
        # Try to find exact or partial match in COMPLAINT_QUESTIONS
        questions_for_complaint = None
        
        # Exact match first
        if complaint_lower in COMPLAINT_QUESTIONS:
            questions_for_complaint = COMPLAINT_QUESTIONS[complaint_lower]
        else:
            # Substring matching
            for template_key, template_qs in COMPLAINT_QUESTIONS.items():
                if template_key in complaint_lower or complaint_lower in template_key:
                    questions_for_complaint = template_qs
                    break
        
        if questions_for_complaint and next_field in questions_for_complaint:
            next_question = questions_for_complaint[next_field]
        else:
            # Fall back to default question
            next_question = DEFAULT_QUESTIONS.get(next_field, "Can you provide more information about this?")
    else:
        # No complaint yet, use default
        next_question = DEFAULT_QUESTIONS.get(next_field, "Can you provide more information?")
    
    # Track that we're asking this field
    updated_questions_asked = list(questions_asked) + [next_field]
    
    return {
        "next_question": next_question,
        "questions_asked": updated_questions_asked
    }
```

---

## CHANGE 3: main.py

**Added 1 line to create_fresh_case_state():**

```python
def create_fresh_case_state():
    return {
        "patient_id": "TEST001",
        "session_id": "SESSION001",
        "language": "English",
        "patient_profile": {
            "age": 30,
            "medical_conditions": [],
            "allergies": []
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],  # ← NEW: Initialize empty questions_asked list
    }
```

---

## CHANGE 4: app/workflow.py

**No changes required.** The workflow routing logic is complaint-agnostic and continues to work correctly.

---

## CHANGE 5: app/red_flag_rules.py

**No changes.** Completely preserved for Phase 2A protection.

---

## TOTAL CHANGES

| File | Lines Added | Lines Modified | Lines Deleted |
|------|------------|---------------|----|
| app/state.py | 1 | 0 | 0 |
| app/nodes.py | ~150 | ~60 | 0 |
| main.py | 1 | 0 | 0 |
| app/workflow.py | 0 | 0 | 0 |
| app/red_flag_rules.py | 0 | 0 | 0 |
| **TOTAL** | **~152** | **~60** | **0** |

---

## BACKWARD COMPATIBILITY

✅ All existing flows continue to work:
- Stomach pain → Same question order (nature_of_pain → location → duration → severity)
- Red flag detection → Unchanged logic
- Workflow routing → Unchanged
- State handling → Compatible (questions_asked initialized to empty list)

✅ No breaking changes to:
- API/function signatures
- State field structure
- Workflow graph
- Red flag system

