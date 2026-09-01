import re
from urllib.request import urlopen

from langchain_ollama import ChatOllama

from app.red_flag_rules import evaluate_red_flags as evaluate_red_flag_rules
from app.state import VaidyaArcState
from app.schemas import IntakeResult

# Complaint-specific information requirements
# Maps chief_complaint keywords to required fields for adaptive intake
COMPLAINT_REQUIREMENTS = {
    "pain": {
        "required_fields": ["chief_complaint", "nature_of_pain", "location", "duration", "severity"],
        "optional_fields": ["associated_symptoms"],
        "category": "pain-like"
    },
    "chest pain": {
        "required_fields": ["chief_complaint", "nature_of_pain", "duration", "severity"],
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
    "chest pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain?",
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

model = ChatOllama(
    model="llama3:latest",
    temperature=0,
    format="json"
)

structured_model = model.with_structured_output(
    IntakeResult,
    method="json_schema"
)


def _ollama_available() -> bool:
    try:
        with urlopen("http://localhost:11434/api/tags", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def _extract_duration(value: str):
    text = (value or "").strip()
    if not text:
        return None

    lowered = text.lower()
    direct_patterns = [
        "ago", "today", "yesterday", "morning", "afternoon", "evening", "night",
        "since", "for", "days", "day", "hours", "hour", "weeks", "week",
        "months", "month", "minutes", "minute", "started", "begin"
    ]

    if any(keyword in lowered for keyword in direct_patterns):
        if re.match(r"^(?:since|for|from)\b", lowered):
            return text

        complaint_prefix_pattern = re.compile(
            r"^(?:i\s+have|i\s+am\s+having|i\s+had|i\s+was\s+having|i\s+have\s+a)\s+"
            r"(?:severe|moderate|mild\s+)?(?:fever|cough|headache|stomach pain|abdominal pain|chest pain|nausea|vomiting)\s*"
            r"(?:since|for|from)?\s*(.*)$",
            re.IGNORECASE,
        )
        complaint_match = complaint_prefix_pattern.match(text)
        if complaint_match:
            candidate = complaint_match.group(1).strip()
            if candidate:
                return candidate

        if re.match(r"^(?:i\s+have|i\s+am\s+having|i\s+had|i\s+was\s+having|i\s+have\s+a)\b", text, re.IGNORECASE):
            candidate = re.sub(
                r"^(?:i\s+have|i\s+am\s+having|i\s+had|i\s+was\s+having|i\s+have\s+a)\s+",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()
            if candidate and candidate.lower() != lowered:
                return candidate

        return text

    return None


def _extract_severity(value: str):
    text = (value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    severity_map = {
        "mild": "mild",
        "moderate": "moderate",
        "severe": "severe",
        "very severe": "very severe",
        "extreme": "extreme",
        "high": "high",
        "low": "low",
        "intense": "intense",
    }
    for keyword, normalized in severity_map.items():
        if keyword in lowered:
            return normalized
    return None


def _extract_pain_nature(value: str):
    text = (value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    for keyword in ["burning", "sharp", "dull", "cramping", "aching", "throbbing", "stabbing", "pressure"]:
        if keyword in lowered:
            return keyword
    return None


def _extract_location(value: str):
    text = (value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if "upper abdomen" in lowered or "upper stomach" in lowered:
        return "upper abdomen"
    if "lower abdomen" in lowered or "lower stomach" in lowered:
        return "lower abdomen"
    if "abdomen" in lowered:
        return "abdomen"
    if "chest" in lowered:
        return "chest"
    if "head" in lowered or "headache" in lowered:
        return "head"
    if "in my " in lowered:
        return re.sub(r"^.*?in my ", "", lowered).strip()
    return None


def _fallback_extract_information(patient_message: str, previous_question: str):
    message = (patient_message or "").strip()
    lower = message.lower()
    extracted = {
        "chief_complaint": None,
        "duration": None,
        "severity": None,
        "nature_of_pain": None,
        "location": None,
        "associated_symptoms": [],
    }

    complaint_map = [
        "stomach pain",
        "abdominal pain",
        "headache",
        "fever",
        "cough",
        "nausea",
        "vomiting",
        "chest pain",
    ]

    severe_complaint_match = re.search(r"\b(severe|moderate|mild)\s+(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain)\b", lower)
    if severe_complaint_match:
        extracted["chief_complaint"] = severe_complaint_match.group(0).strip()
    elif re.search(r"\bi have\b.*\b(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain)\b", lower):
        complaint = re.search(r"\b(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain)\b", lower).group(1)
        extracted["chief_complaint"] = complaint
    elif any(keyword in lower for keyword in complaint_map):
        for keyword in complaint_map:
            if keyword in lower:
                extracted["chief_complaint"] = keyword
                break

    if previous_question:
        q_lower = previous_question.lower()
        if any(phrase in q_lower for phrase in ["describe what the pain feels like", "pain feels like", "feels like"]):
            extracted["nature_of_pain"] = _extract_pain_nature(message)
        if "where" in q_lower or "location" in q_lower:
            extracted["location"] = _extract_location(message)
        if "when did" in q_lower or "how long" in q_lower or "start" in q_lower or "duration" in q_lower:
            extracted["duration"] = _extract_duration(message)
        if "how severe" in q_lower or "severity" in q_lower:
            extracted["severity"] = _extract_severity(message)

    if extracted["severity"] is None and not extracted["chief_complaint"]:
        severity = _extract_severity(message)
        if severity:
            extracted["severity"] = severity

    if extracted["severity"] is None:
        complaint_severity = _extract_severity(extracted.get("chief_complaint") or "")
        if complaint_severity:
            extracted["severity"] = complaint_severity

    if extracted["chief_complaint"] in {"fever", "severe fever", "moderate fever", "mild fever"} and extracted["severity"] is None:
        explicit_severity = _extract_severity(extracted["chief_complaint"])
        if explicit_severity and previous_question and any(q in previous_question.lower() for q in ["how severe", "severity", "severe"]):
            extracted["severity"] = explicit_severity

    if extracted["duration"] is None:
        duration = _extract_duration(message)
        if duration:
            extracted["duration"] = duration
        else:
            duration_match = re.search(r"\b(?:for|from|since)\s+([A-Za-z0-9 ]*(?:day|days|hour|hours|week|weeks|month|months|minute|minutes|morning|afternoon|evening|night))\b", lower)
            if duration_match:
                extracted["duration"] = duration_match.group(1).strip()

    if extracted["nature_of_pain"] is None:
        pain_nature = _extract_pain_nature(message)
        if pain_nature:
            extracted["nature_of_pain"] = pain_nature

    if extracted["location"] is None:
        location = _extract_location(message)
        if location:
            extracted["location"] = location

    if extracted["chief_complaint"] == "severe chest pain" and "severe" in lower:
        extracted["severity"] = "severe"

    if extracted["chief_complaint"] and re.fullmatch(r"(it|this|that|they)\s+(feels like|is|started|began).*", lower):
        extracted["chief_complaint"] = None

    return extracted


def intake_brain(state: VaidyaArcState):
    patient_message = state.get("current_message", "")
    previous_question = state.get("conversation_message", "")

    # Fresh-case protection: intake_brain never reads previously structured state values
    # to build extracted_information. It only reads the current message and the immediately
    # previous patient-facing question for short-answer interpretation.
    prompt = f"""
You are the Intake Information Extraction component of VaidyaArc.

Extract ONLY new information explicitly stated by the patient in the CURRENT PATIENT MESSAGE.

You are NOT diagnosing.
You are NOT recommending treatment.
You must NOT invent information.

PREVIOUS QUESTION:
{previous_question}

CURRENT PATIENT MESSAGE:
{patient_message}

IMPORTANT RULES:

1. Extract information only from the CURRENT PATIENT MESSAGE.
2. The PREVIOUS QUESTION may only be used to understand what pronouns such as "it", "they", "this", or "that" refer to.
3. Never copy values from previous conversation.
4. If a field is not mentioned in the current message, return None.
5. A patient may provide multiple pieces of information in one message. Extract ALL explicitly mentioned information.
6. Do not write any permanent patient state here. Return data into the temporary extracted_information field only.
7. Use the PREVIOUS QUESTION as the primary context for interpretation.
8. Do not automatically convert a short answer into a new chief complaint.
9. If the patient gives a short answer to a specific question, fill only the field being asked about unless they explicitly state a new main complaint.
10. Never inherit old structured values such as burning, upper abdomen, or previous complaint text into a fresh extraction.

FIELD PRIORITY BY PREVIOUS QUESTION:

- If the previous question is about location, prioritize location extraction.
- If the previous question is about severity, prioritize severity extraction.
- If the previous question is about duration, prioritize duration extraction.
- If the previous question is about nature of pain, prioritize nature_of_pain extraction.

DURATION EXTRACTION - CRITICAL EXAMPLES:

**ONLY extract duration when the PREVIOUS QUESTION is about timing/onset (e.g., "When did...", "When did...start", "How long...") OR when there is a clear temporal expression in the message.**

**If PREVIOUS QUESTION is empty/blank/None, do NOT extract duration unless the patient explicitly uses phrases like "I started", "I began", "since", "for", etc. Do not extract introductory phrases like "I have" as duration.**

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"today morning"

Expected:
duration = "today morning"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"this morning"

Expected:
duration = "this morning"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"1 day ago"

Expected:
duration = "1 day ago"
chief_complaint = None

PREVIOUS QUESTION:
"When did the fever start?"
CURRENT MESSAGE:
"since this morning"

Expected:
duration = "since this morning"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"since yesterday"

Expected:
duration = "since yesterday"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"for two days"

Expected:
duration = "for two days"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"yesterday"

Expected:
duration = "yesterday"
chief_complaint = None

PREVIOUS QUESTION:
(empty/blank - patient stating chief complaint)
CURRENT MESSAGE:
"I have fever"

Expected:
duration = None
chief_complaint = "fever"

PREVIOUS QUESTION:
(empty/blank - patient stating chief complaint)
CURRENT MESSAGE:
"I have a cough"

Expected:
duration = None
chief_complaint = "cough"

OTHER EXAMPLES:

PREVIOUS QUESTION:
"Where exactly are you feeling the pain?"
CURRENT MESSAGE:
"In my upper abdomen"

Expected:
location = "upper abdomen"
chief_complaint = None

PREVIOUS QUESTION:
"How severe is the pain?"
CURRENT MESSAGE:
"Moderate"

Expected:
severity = "moderate"
chief_complaint = None

PREVIOUS QUESTION:
"When did this problem start?"
CURRENT MESSAGE:
"It started 2 days ago"

Expected:
duration = "2 days"
chief_complaint = None

PREVIOUS QUESTION:
"Can you describe what the pain feels like?"
CURRENT MESSAGE:
"It feels like burning"

Expected:
nature_of_pain = "burning"
chief_complaint = None

CURRENT MESSAGE:
"I have stomach pain"

Expected:
chief_complaint = "stomach pain"
nature_of_pain = None
location = None
duration = None
severity = None
associated_symptoms = []

CURRENT MESSAGE:
"I have severe chest pain"

Expected:
chief_complaint = "severe chest pain"
nature_of_pain = None
location = None
duration = None
severity = None
associated_symptoms = []

IMPORTANT:

Do NOT put descriptive words such as:

* burning
* sharp
* dull
* cramping

into chief_complaint if they describe an existing pain.

If the message is only a symptom description such as "burning sensation in my upper abdomen" without a clear complaint statement, then:
- chief_complaint = None
- nature_of_pain = "burning"
- location = "upper abdomen"

Do NOT treat a symptom description as a patient complaint unless the patient explicitly says they have a condition or problem.

Do NOT put the main complaint inside associated_symptoms.

associated_symptoms must contain only additional symptoms explicitly mentioned by the patient.

Return only the structured schema.
"""

    if not _ollama_available():
        extracted = _fallback_extract_information(patient_message, previous_question)
    else:
        try:
            result = structured_model.invoke(prompt)
            extracted = result.model_dump()
        except Exception:
            extracted = _fallback_extract_information(patient_message, previous_question)

    previous_question = state.get("conversation_message", "")
    extracted = _contextualize_extraction(extracted, previous_question, patient_message)

    print("\nDEBUG - NEW INFORMATION EXTRACTED:")
    print(extracted)

    return {
        "extracted_information": extracted
    }


def _find_complaint_template(complaint_text: str) -> dict | None:
    """
    Match a chief_complaint string to a complaint template.
    Searches for keywords in the complaint and returns the matching template.
    More specific complaint names must win over generic ones like "pain".
    """
    if not complaint_text:
        return None

    complaint_lower = complaint_text.lower().strip()

    # Exact match first
    if complaint_lower in COMPLAINT_REQUIREMENTS:
        return COMPLAINT_REQUIREMENTS[complaint_lower]

    # Prefer longer, more specific complaint names before generic ones
    candidates = sorted(
        COMPLAINT_REQUIREMENTS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for template_key, template in candidates:
        if template_key in complaint_lower or complaint_lower in template_key:
            return template

    return None


def _normalize_blank(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() in {"none", "null", "nan", ""}:
            return None
        return cleaned if cleaned else None
    return value


def _field_has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned not in {"", "None", "null", "nan"}
    if isinstance(value, list):
        return len(value) > 0
    return True


def _contextualize_extraction(extracted, previous_question, patient_message):
    """Post-processing to resolve ambiguities based on context from previous question."""
    safe = dict(extracted or {})
    question = (previous_question or "").lower()
    message = (patient_message or "").lower().strip()

    complaint_match = re.search(
        r"\b(?:i have|i am having|i have been having|i have had)\s+((?:severe|moderate|mild)\s+)?(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain)\b",
        message,
    )
    if complaint_match:
        safe["chief_complaint"] = complaint_match.group(0).strip()
        if safe["chief_complaint"].lower().startswith("i have "):
            safe["chief_complaint"] = safe["chief_complaint"][7:].strip()

    if safe.get("severity") is None:
        complaint_severity = _extract_severity(safe.get("chief_complaint") or "")
        if complaint_severity:
            safe["severity"] = complaint_severity

    if not question:
        # No previous question context - be conservative about what we accept as duration
        # Only accept if it looks like a genuine temporal expression
        if safe.get("duration"):
            duration_str = str(safe.get("duration")).lower()
            valid_duration_keywords = {
                "ago", "today", "yesterday", "morning", "evening", "night",
                "hours", "hour", "days", "day", "weeks", "week", "months", "month",
                "minutes", "minute", "seconds", "second",
                "since", "for", "during", "from", "when", "started"
            }
            has_duration_keyword = any(kw in duration_str for kw in valid_duration_keywords)
            if not has_duration_keyword:
                safe["duration"] = None
        if safe.get("duration") is None:
            duration_match = re.search(r"\b(?:for|from|since)\s+([A-Za-z0-9 ]*(?:day|days|hour|hours|week|weeks|month|months|minute|minutes|morning|afternoon|evening|night))\b", message)
            if duration_match:
                safe["duration"] = duration_match.group(1).strip()
        return safe

    # Field correction: Check if values are in wrong fields
    # This happens when LLM confuses fields regardless of previous question
    
    # If severity is missing but duration looks like it's severity, move it
    if safe.get("severity") is None and safe.get("duration"):
        duration_val = str(safe.get("duration")).lower()
        severity_keywords = {"mild", "moderate", "severe", "very severe", "extreme", "low", "high", "intense", "bad", "good", "worse", "worsening"}
        if duration_val in severity_keywords or any(kw in duration_val for kw in severity_keywords):
            safe["severity"] = safe["duration"]
            safe["duration"] = None
    
    # With previous question context, apply contextual resolution
    
    # Handle severity questions: secondary check for severity extraction
    if "severity" in question or "how severe" in question or "severe" in question:
        if safe.get("severity") is not None:
            safe["chief_complaint"] = None
    
    # Handle location questions
    if "where" in question or "location" in question:
        if safe.get("chief_complaint") and safe.get("location"):
            safe["chief_complaint"] = None
        if safe.get("location") is None and "upper abdomen" in message:
            safe["location"] = "upper abdomen"
        if safe.get("chief_complaint") and message.startswith("in my "):
            safe["chief_complaint"] = None

    # Handle duration questions
    if "when did" in question or "start" in question or ("duration" in question and "when" in question):
        if safe.get("duration") is not None:
            safe["chief_complaint"] = None

    # Handle nature of pain questions
    if "describe what the pain feels like" in question or "nature of pain" in question or "pain feels like" in question:
        if safe.get("nature_of_pain") is not None:
            safe["chief_complaint"] = None
            # Don't accept location when answering about pain description
            if safe.get("location") and safe.get("location") not in ["chest", "upper abdomen", "lower abdomen", "back", "side"]:
                # If location looks like a pain descriptor, move it to nature_of_pain
                location_val = safe.get("location").lower()
                pain_descriptors = {"sharp", "dull", "burning", "aching", "pressure", "tingling", "throbbing", "stabbing"}
                if location_val in pain_descriptors:
                    if safe.get("nature_of_pain"):
                        safe["nature_of_pain"] = safe["nature_of_pain"] + ", " + safe["location"]
                    else:
                        safe["nature_of_pain"] = safe["location"]
                    safe["location"] = None

    return safe


def _normalize_symptom_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    text = value.strip()
    if not text:
        return None

    lowered = text.lower()
    replacements = {
        "nauseous": "nausea",
        "nauseated": "nausea",
        "painful": "pain",
        "stomachache": "stomach pain",
    }

    normalized = replacements.get(lowered, lowered)
    return normalized.strip()


def _merge_unique_list(existing, incoming):
    current = existing or []
    new_items = incoming or []

    if not isinstance(current, list):
        current = [current]
    if not isinstance(new_items, list):
        new_items = [new_items]

    merged = []
    seen = set()

    for item in current + new_items:
        if item is None:
            continue
        text = _normalize_symptom_text(item)
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            merged.append(text)

    return merged


def _looks_like_symptom_description(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text:
        return False
    symptom_prefixes = (
        "burning sensation",
        "sharp pain",
        "dull pain",
        "cramping",
        "feels like",
        "pain in my",
        "sensation in my",
        "pain in the",
        "sensation in the",
        "i also feel",
    )
    return any(text.startswith(prefix) for prefix in symptom_prefixes)


def _looks_like_duration_expression(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text:
        return False

    duration_keywords = {
        "ago", "today", "yesterday", "morning", "evening", "night",
        "hour", "hours", "day", "days", "week", "weeks", "month", "months",
        "minute", "minutes", "second", "seconds", "since", "for", "started",
        "begin", "onset", "duration"
    }
    return any(keyword in text for keyword in duration_keywords)


def _looks_like_severity_expression(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text:
        return False

    severity_keywords = {
        "mild", "moderate", "severe", "very severe", "extreme",
        "intense", "high", "low", "worse", "worsening", "bad"
    }
    return any(keyword in text for keyword in severity_keywords)


def _matches_previous_question_context(previous_question, field, value):
    if value is None:
        return False

    text = str(value).strip().lower()
    if not text:
        return False

    question = (previous_question or "").lower()

    if field == "location":
        if "where" in question or "location" in question:
            return True
        if "in my" in text or "in the" in text or "upper abdomen" in text or "chest" in text or "abdomen" in text:
            return True
        return False

    if field == "severity":
        if "severity" in question or "how severe" in question or "severe" in question:
            return True
        if _looks_like_severity_expression(value):
            return True
        return False

    if field == "duration":
        if "when did" in question or "duration" in question or "start" in question:
            return True
        if _looks_like_duration_expression(value):
            return True
        return False

    if field == "nature_of_pain":
        if "describe what the pain feels like" in question or "nature of pain" in question or "pain feels like" in question:
            return True
        if any(descriptor in text for descriptor in ["sharp", "dull", "burning", "cramping", "aching", "pressure", "throbbing", "stabbing"]):
            return True
        return False

    return True


def _is_likely_symptom_only(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text:
        return False

    symptom_words = {
        "nausea",
        "nauseous",
        "vomiting",
        "vomit",
        "burning",
        "sharp",
        "dull",
        "cramping",
    }

    return text in symptom_words or _looks_like_symptom_description(text)


def merge_intake_information(state: VaidyaArcState):
    extracted = state.get("extracted_information") or {}
    merged_state = {}

    existing_chief_complaint = state.get("chief_complaint")
    previous_question = state.get("conversation_message")

    for field in [
        "chief_complaint",
        "duration",
        "severity",
        "nature_of_pain",
        "location",
        "associated_symptoms",
    ]:
        existing_value = state.get(field)
        new_value = extracted.get(field)
        normalized_new_value = _normalize_blank(new_value)

        if field == "associated_symptoms":
            filtered_new_items = []
            if isinstance(normalized_new_value, list):
                filtered_new_items = [
                    item for item in normalized_new_value
                    if item and item.lower() not in {
                        "none",
                        "null",
                        str(existing_chief_complaint).lower() if existing_chief_complaint else "",
                        "stomach pain",
                        "pain",
                    }
                ]
            elif normalized_new_value is not None:
                filtered_new_items = [normalized_new_value]
                if filtered_new_items[0].lower() in {"none", "null", str(existing_chief_complaint).lower() if existing_chief_complaint else "", "stomach pain", "pain"}:
                    filtered_new_items = []
            merged_state[field] = _merge_unique_list(existing_value, filtered_new_items)
            continue

        if field == "chief_complaint":
            if normalized_new_value is None:
                merged_state[field] = existing_value
                continue
            if _looks_like_symptom_description(normalized_new_value) or _is_likely_symptom_only(normalized_new_value):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "location", normalized_new_value):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "severity", normalized_new_value):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "duration", normalized_new_value):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "nature_of_pain", normalized_new_value):
                merged_state[field] = existing_value
                continue
            merged_state[field] = normalized_new_value
            continue

        if normalized_new_value is None:
            merged_state[field] = existing_value
            continue

        if previous_question and field in {"location", "severity", "duration", "nature_of_pain"}:
            if not _matches_previous_question_context(previous_question, field, normalized_new_value):
                merged_state[field] = existing_value
                continue

        merged_state[field] = normalized_new_value

    merged_state["extracted_information"] = {}
    return merged_state


def validate_patient_state(state: VaidyaArcState):
    validated = dict(state)

    if "patient_profile" not in validated or validated["patient_profile"] is None:
        validated["patient_profile"] = {}

    if "previous_history" not in validated or validated["previous_history"] is None:
        validated["previous_history"] = []

    if "conversation_history" not in validated or validated["conversation_history"] is None:
        validated["conversation_history"] = []

    if "associated_symptoms" not in validated or validated["associated_symptoms"] is None:
        validated["associated_symptoms"] = []
    else:
        validated["associated_symptoms"] = _merge_unique_list(validated["associated_symptoms"], [])

    for field in [
        "chief_complaint",
        "duration",
        "severity",
        "nature_of_pain",
        "location",
    ]:
        if field not in validated:
            validated[field] = None
        value = validated[field]
        validated[field] = _normalize_blank(value)

    if "missing_information" not in validated or validated["missing_information"] is None:
        validated["missing_information"] = []

    if "information_complete" not in validated or validated["information_complete"] is None:
        validated["information_complete"] = False

    if "questions_asked" not in validated or validated["questions_asked"] is None:
        validated["questions_asked"] = []

    validated["extracted_information"] = {}
    return validated


def _field_has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() not in {"", "None", "null"}
    if isinstance(value, list):
        return len(value) > 0
    return True


def determine_missing_information(state: VaidyaArcState):
    missing = []

    complaint = state.get("chief_complaint")

    if not complaint:
        return {
            "missing_information": ["chief_complaint"],
            "information_complete": False
        }

    template = _find_complaint_template(complaint)
    required_fields = template["required_fields"] if template else FALLBACK_REQUIRED_FIELDS

    for field in required_fields:
        if not _field_has_value(state.get(field)):
            missing.append(field)

    information_complete = len(missing) == 0

    return {
        "missing_information": missing,
        "information_complete": information_complete
    }


def select_next_question(state: VaidyaArcState):
    complaint = state.get("chief_complaint")
    missing = []

    if complaint:
        template = _find_complaint_template(complaint)
        required_fields = template["required_fields"] if template else FALLBACK_REQUIRED_FIELDS
        missing = [field for field in required_fields if not _field_has_value(state.get(field))]
    else:
        missing = ["chief_complaint"]

    if state.get("information_complete") or not missing:
        return {
            "next_question": None,
            "questions_asked": list(state.get("questions_asked", []))
        }

    questions_asked = list(state.get("questions_asked", []) or [])

    next_field = None
    for field in missing:
        if field not in questions_asked:
            next_field = field
            break

    if next_field is None:
        return {
            "next_question": None,
            "questions_asked": questions_asked
        }

    if complaint:
        complaint_lower = complaint.lower()
        questions_for_complaint = None

        if complaint_lower in COMPLAINT_QUESTIONS:
            questions_for_complaint = COMPLAINT_QUESTIONS[complaint_lower]
        else:
            for template_key, template_qs in COMPLAINT_QUESTIONS.items():
                if template_key in complaint_lower or complaint_lower in template_key:
                    questions_for_complaint = template_qs
                    break

        if questions_for_complaint and next_field in questions_for_complaint:
            next_question = questions_for_complaint[next_field]
        else:
            next_question = DEFAULT_QUESTIONS.get(next_field, "Can you provide more information about this?")
    else:
        next_question = DEFAULT_QUESTIONS.get(next_field, "Can you provide more information?")

    updated_questions_asked = list(questions_asked) + [next_field]

    return {
        "next_question": next_question,
        "questions_asked": updated_questions_asked
    }


def ask_next_question(state: VaidyaArcState):
    if state.get("information_complete") and not (state.get("missing_information") or []):
        return {
            "conversation_message": "Thank you. I have collected the initial information about your concern.",
            "next_question": None,
            "conversation_history": state.get("conversation_history", [])
        }

    question = state.get("next_question")
    if question:
        return {
            "conversation_message": question,
            "next_question": question
        }

    return {
        "conversation_message": None,
        "next_question": None
    }


def _risk_rule_hit(rule_id, category, weight, evidence, explanation, matched=True, additive=True):
    return {
        "rule_id": rule_id,
        "category": category,
        "weight": weight,
        "evidence": evidence,
        "explanation": explanation,
        "matched": matched,
        "additive": additive,
    }


def _dedupe(items):
    seen = set()
    out = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            out.append(text)
    return out


def risk_convergence(state: VaidyaArcState):
    missing = list(state.get("missing_information") or [])
    if not state.get("information_complete") or missing:
        return {
            "risk_level": "INCOMPLETE",
            "risk_score": 0,
            "risk_signal_summary": ["information_incomplete"],
            "risk_contributing_factors": ["missing_required_fields"],
            "risk_evidence": [f"missing_information: {', '.join(missing) if missing else 'not available'}"],
            "risk_reasoning": "Risk convergence was deferred because required patient information is incomplete.",
            "risk_override_reason": None,
            "recommended_next_action": "Collect the missing clinical information before final risk classification.",
            "risk_rule_hits": [],
            "convergence_status": "incomplete",
            "risk_context_flags": ["information_incomplete"],
            "risk_assessment_version": "phase2b_v1",
        }

    red_flag_status = state.get("red_flag_status")
    immediate_attention = bool(state.get("immediate_attention_required"))
    if red_flag_status == "red_flags_detected" or immediate_attention:
        evidence = list(state.get("red_flag_evidence") or [])
        red_flags = list(state.get("red_flags") or [])
        override_reason = "Phase 2A red-flag rules identified an immediate safety concern; Phase 2B does not downgrade this risk."
        return {
            "risk_level": "URGENT",
            "risk_score": 100,
            "risk_signal_summary": ["red_flag_override", "phase2a_red_flag"],
            "risk_contributing_factors": ["Phase 2A emergency safety rule triggered"] + red_flags,
            "risk_evidence": _dedupe(evidence or red_flags or ["Phase 2A red-flag status"]),
            "risk_reasoning": override_reason,
            "risk_override_reason": override_reason,
            "recommended_next_action": "Immediate appropriate medical attention or urgent clinical evaluation.",
            "risk_rule_hits": [
                _risk_rule_hit(
                    "red_flag_override",
                    "safety_override",
                    100,
                    _dedupe(evidence or red_flags or ["Phase 2A red-flag status"]),
                    override_reason,
                    matched=True,
                    additive=False,
                )
            ],
            "convergence_status": "overridden_by_red_flag",
            "risk_context_flags": ["phase2a_red_flag_override"],
            "risk_assessment_version": "phase2b_v1",
        }

    combined_text = " ".join(
        part for part in [
            state.get("chief_complaint"),
            state.get("nature_of_pain"),
            state.get("location"),
            state.get("duration"),
            state.get("severity"),
            *list(state.get("associated_symptoms") or []),
            state.get("current_message"),
        ]
        if part is not None
    ).lower()

    rule_hits = []
    risk_context_flags = []
    risk_evidence = []
    factors = []

    severity_text = str(state.get("severity") or "").lower()
    if "severe" in severity_text or "very severe" in severity_text:
        rule_hits.append(_risk_rule_hit(
            "severe_symptom_present",
            "symptom_intensity",
            20,
            [str(state.get("severity"))],
            "High severity increases overall risk accumulation.",
            matched=True,
            additive=True,
        ))
        factors.append("high severity")
        risk_evidence.extend([str(state.get("severity"))])
        risk_context_flags.append("high_severity")

    worsening_terms = [
        "worsening",
        "rapidly worsening",
        "worse quickly",
        "getting worse quickly",
        "suddenly worse",
        "very rapidly worsening",
    ]
    if any(term in combined_text for term in worsening_terms):
        rule_hits.append(_risk_rule_hit(
            "worsening_progression",
            "progression",
            15,
            ["worsening progression reported"],
            "Worsening over time adds risk beyond a single isolated complaint.",
            matched=True,
            additive=True,
        ))
        factors.append("worsening progression")
        risk_evidence.append("worsening progression reported")
        risk_context_flags.append("worsening")

    symptoms = list(state.get("associated_symptoms") or [])
    if len(symptoms) >= 2:
        rule_hits.append(_risk_rule_hit(
            "multiple_symptom_cluster",
            "symptom_cluster",
            10,
            symptoms,
            "Multiple symptoms together indicate a broader pattern of concern.",
            matched=True,
            additive=True,
        ))
        factors.append("multiple symptoms")
        risk_evidence.extend(symptoms)
        risk_context_flags.append("multiple_symptoms")

    duration_text = str(state.get("duration") or "").lower()
    if any(term in duration_text for term in ["day", "days", "week", "weeks", "month", "months", "since", "for"]):
        if re.search(r"\b(?:[2-9]|[1-9][0-9]+)\s*(day|days|week|weeks|month|months)\b", duration_text) or "since" in duration_text or "for" in duration_text:
            rule_hits.append(_risk_rule_hit(
                "prolonged_duration",
                "temporal_risk",
                8,
                [str(state.get("duration"))],
                "Persistent or prolonged symptoms can increase overall risk.",
                matched=True,
                additive=True,
            ))
            factors.append("prolonged duration")
            risk_evidence.append(str(state.get("duration")))
            risk_context_flags.append("persistent_symptoms")

    patient_profile = state.get("patient_profile") or {}
    chronic_conditions = list(patient_profile.get("medical_conditions") or [])
    if chronic_conditions:
        rule_hits.append(_risk_rule_hit(
            "chronic_condition_context",
            "history_context",
            6,
            chronic_conditions,
            "Relevant chronic conditions increase background risk context.",
            matched=True,
            additive=True,
        ))
        factors.append("relevant chronic condition")
        risk_evidence.extend(chronic_conditions)
        risk_context_flags.append("chronic_condition")

    age_value = patient_profile.get("age")
    if isinstance(age_value, (int, float)) and (age_value >= 65 or age_value < 5):
        rule_hits.append(_risk_rule_hit(
            "age_or_vulnerability_context",
            "patient_context",
            6,
            [str(age_value)],
            "Age-related vulnerability adds background concern.",
            matched=True,
            additive=True,
        ))
        factors.append("age-related vulnerability")
        risk_evidence.append(str(age_value))
        risk_context_flags.append("age_vulnerability")

    complaint_text = str(state.get("chief_complaint") or "").lower()
    if "chest pain" in complaint_text and ("severe" in severity_text or "very severe" in severity_text):
        rule_hits.append(_risk_rule_hit(
            "chest_pain_severity",
            "anatomical_risk",
            25,
            [str(state.get("chief_complaint")), str(state.get("severity"))],
            "Chest pain with high severity is a clinically significant escalation signal.",
            matched=True,
            additive=True,
        ))
        factors.append("severe chest pain")
        risk_evidence.extend([str(state.get("chief_complaint")), str(state.get("severity"))])
        risk_context_flags.append("chest_pain")

    if any(term in combined_text for term in ["difficulty breathing", "shortness of breath", "trouble breathing", "cannot breathe", "can't breathe"]):
        rule_hits.append(_risk_rule_hit(
            "breathing_compromise",
            "anatomical_risk",
            25,
            ["breathing compromise reported"],
            "Breathing compromise raises risk substantially.",
            matched=True,
            additive=True,
        ))
        factors.append("breathing compromise")
        risk_evidence.append("breathing compromise reported")
        risk_context_flags.append("breathing_problem")

    neurological_terms = [
        "sudden weakness",
        "slurred speech",
        "facial droop",
        "seizure",
        "sudden confusion",
        "sudden numbness",
        "fainting",
        "passed out",
    ]
    if any(term in combined_text for term in neurological_terms):
        rule_hits.append(_risk_rule_hit(
            "neurological_change",
            "anatomical_risk",
            25,
            ["neurological change reported"],
            "Acute neurological symptoms add high-risk context.",
            matched=True,
            additive=True,
        ))
        factors.append("neurological concern")
        risk_evidence.append("neurological change reported")
        risk_context_flags.append("neurological_concern")

    bleeding_terms = [
        "vomiting blood",
        "black stool",
        "bloody stool",
        "major bleeding",
        "heavy bleeding",
        "bleeding heavily",
        "blood in vomit",
        "blood in stool",
    ]
    if any(term in combined_text for term in bleeding_terms):
        rule_hits.append(_risk_rule_hit(
            "bleeding_signal",
            "anatomical_risk",
            25,
            ["bleeding-related symptom reported"],
            "Bleeding or blood in stool/vomit indicates a high-risk pattern.",
            matched=True,
            additive=True,
        ))
        factors.append("bleeding concern")
        risk_evidence.append("bleeding-related symptom reported")
        risk_context_flags.append("bleeding_concern")

    abdominal_pattern = (
        ("abdominal pain" in combined_text or "stomach pain" in combined_text or "abdomen" in combined_text)
        and ("severe" in severity_text or "very severe" in severity_text)
        and any(term in combined_text for term in ["vomiting", "fainting", "difficulty breathing", "black stool", "bloody stool"])
    )
    if abdominal_pattern:
        rule_hits.append(_risk_rule_hit(
            "abdominal_urgency",
            "anatomical_risk",
            22,
            ["severe abdominal pain with concerning associated symptoms"],
            "Severe abdominal pain combined with concerning associated symptoms increases escalation risk.",
            matched=True,
            additive=True,
        ))
        factors.append("severe abdominal pain with concerning symptoms")
        risk_evidence.append("severe abdominal pain with concerning associated symptoms")
        risk_context_flags.append("abdominal_urgency")

    previous_history = state.get("previous_history") or []
    if previous_history:
        rule_hits.append(_risk_rule_hit(
            "recurrent_or_multiple_episodes",
            "history_context",
            8,
            ["prior clinical history available"],
            "Prior history adds context that the current episode may be part of a broader pattern.",
            matched=True,
            additive=True,
        ))
        factors.append("prior history available")
        risk_evidence.append("prior clinical history available")
        risk_context_flags.append("prior_history")

    risk_score = sum(rule["weight"] for rule in rule_hits)

    if risk_score >= 40:
        risk_level = "URGENT"
        recommended_next_action = "Immediate appropriate medical attention or urgent clinical evaluation."
    elif risk_score >= 25:
        risk_level = "HIGH"
        recommended_next_action = "Prompt clinical evaluation and reassessment; consider higher-priority review."
    elif risk_score >= 10:
        risk_level = "MODERATE"
        recommended_next_action = "Clinical review and close follow-up; reassess if symptoms worsen."
    else:
        risk_level = "LOW"
        recommended_next_action = "Routine follow-up and monitoring as appropriate; no urgent escalation indicated."

    risk_signal_summary = [rule["rule_id"] for rule in rule_hits]
    if not risk_signal_summary:
        risk_signal_summary = ["no_significant_risk_signals"]

    if not factors:
        factors = ["no material escalation signals identified"]

    risk_contributing_factors = _dedupe(factors)
    risk_evidence = _dedupe(risk_evidence)
    risk_context_flags = _dedupe(risk_context_flags)

    risk_reasoning = (
        f"Phase 2B aggregated {len(rule_hits)} deterministic risk signals. "
        + " ".join(
            rule["explanation"] for rule in rule_hits
        )
        if rule_hits else
        "No significant risk signals were identified from the available structured information."
    )

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_signal_summary": risk_signal_summary,
        "risk_contributing_factors": risk_contributing_factors,
        "risk_evidence": risk_evidence,
        "risk_reasoning": risk_reasoning,
        "risk_override_reason": None,
        "recommended_next_action": recommended_next_action,
        "risk_rule_hits": rule_hits,
        "convergence_status": "evaluated",
        "risk_context_flags": risk_context_flags,
        "risk_assessment_version": "phase2b_v1",
    }


def evaluate_red_flags(state: VaidyaArcState):
    missing = state.get("missing_information") or []
    if not state.get("information_complete") or missing:
        return {
            "red_flag_status": "insufficient_information",
            "red_flags": [],
            "red_flag_evidence": [],
            "immediate_attention_required": False,
            "red_flag_rule_hits": [],
            "next_question": state.get("next_question"),
            "conversation_message": None,
        }

    result = evaluate_red_flag_rules(state)

    completion_state = {
        "next_question": None,
        "conversation_message": "Thank you. I have collected the initial information about your concern.",
    }

    return {
        **completion_state,
        "red_flag_status": result["red_flag_status"],
        "red_flags": result["red_flags"],
        "red_flag_evidence": result["red_flag_evidence"],
        "immediate_attention_required": result["immediate_attention_required"],
        "red_flag_rule_hits": result["red_flag_rule_hits"],
    }

    return {
        **completion_state,
        "red_flag_status": result["red_flag_status"],
        "red_flags": result["red_flags"],
        "red_flag_evidence": result["red_flag_evidence"],
        "immediate_attention_required": result["immediate_attention_required"],
        "red_flag_rule_hits": result["red_flag_rule_hits"],
    }
