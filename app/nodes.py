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
        "location": "Where exactly in your body are you feeling the pain?",
        "duration": "When did this pain start or how long has it lasted?",
        "severity": "How severe is the pain — would you describe it as mild, moderate, or severe?",
    },
    "burning pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the burning sensation feels like?",
        "location": "Where exactly are you feeling the burning pain?",
        "duration": "When did this burning sensation start or how long has it lasted?",
        "severity": "How severe is this discomfort — is it mild, moderate, or severe?",
    },
    "stomach pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain — is it mild, moderate, or severe?",
    },
    "abdominal pain": {
        "chief_complaint": "What health problem are you experiencing?",
        "nature_of_pain": "Can you describe what the pain feels like?",
        "location": "Where exactly are you feeling the pain?",
        "duration": "When did this problem start?",
        "severity": "How severe is the pain — is it mild, moderate, or severe?",
    },
}

# Default questions for generic fields
DEFAULT_QUESTIONS = {
    "chief_complaint": "What health problem are you experiencing?",
    "nature_of_pain": "Can you describe what the feeling is like?",
    "location": "Where exactly are you experiencing this?",
    "duration": "When did this start or how long have you had it?",
    "severity": "How severe is this on a mild, moderate, or severe scale?",
}

model = ChatOllama(
    base_url="http://127.0.0.1:11434",
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
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


WORD_NUMS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12"
}
NUM_PATTERN = r"[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|several|couple of"
TIME_UNITS = r"days?|hours?|weeks?|months?|minutes?|years?"


def _extract_duration(value: str):
    text = (value or "").strip()
    if not text:
        return None

    raw = text.strip()

    # 1. 'since/from' + date/time marker (e.g. 'since yesterday', 'since this morning', 'from yesterday morning')
    m_since = re.search(r"\b(since|from)\s+(yesterday(?:\s+morning|\s+evening|\s+night)?|today|this\s+morning|last\s+night|morning|evening|night)\b", raw, re.IGNORECASE)
    if m_since:
        return f"{m_since.group(1).lower()} {m_since.group(2).lower()}".strip()

    # 2. 'for/since/from/over the last/in the last' + number + unit (e.g. 'for 3 days', 'for three days', 'since 2 weeks')
    m_prep = re.search(rf"\b(?:for|since|from|over the past|over the last|in the past|in the last)\s+({NUM_PATTERN})\s+({TIME_UNITS})\b", raw, re.IGNORECASE)
    if m_prep:
        num = m_prep.group(1).lower()
        unit = m_prep.group(2).lower()
        num_norm = WORD_NUMS.get(num, num)
        return f"{num_norm} {unit}"

    # 3. Standalone number + unit (e.g. '3 days', 'three days', '2 weeks', '1 month', 'a few days')
    m_unit = re.search(rf"\b({NUM_PATTERN})\s+({TIME_UNITS})\b", raw, re.IGNORECASE)
    if m_unit:
        num = m_unit.group(1).lower()
        unit = m_unit.group(2).lower()
        num_norm = WORD_NUMS.get(num, num)
        return f"{num_norm} {unit}"

    # 4. Standalone temporal markers (e.g. 'yesterday', 'this morning', 'last night')
    m_marker = re.search(r"\b(yesterday(?:\s+morning|\s+evening|\s+night)?|this\s+morning|last\s+night)\b", raw, re.IGNORECASE)
    if m_marker:
        return m_marker.group(1).lower()

    # 5. Clean multi-word phrase starting with since/for (e.g. 'since 2 days ago')
    if re.match(r"^(?:since|for|from)\b", raw.lower()) and len(raw.split()) <= 4:
        if not any(kw in raw.lower() for kw in [",", ";", " and ", " but ", " with ", "fever", "pain", "severe", "moderate", "mild"]):
            return raw

    return None


def _extract_severity(value: str):
    text = (value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    severity_mappings = [
        ("very severe", "severe"),
        ("extremely severe", "severe"),
        ("excruciating", "severe"),
        ("unbearable", "severe"),
        ("agonizing", "severe"),
        ("agony", "severe"),
        ("10 out of 10", "severe"),
        ("10/10", "severe"),
        ("9/10", "severe"),
        ("8/10", "severe"),
        ("terrible", "severe"),
        ("very bad", "severe"),
        ("extreme", "severe"),
        ("intense", "severe"),
        ("severe", "severe"),
        ("somewhat severe", "moderate"),
        ("fairly bad", "moderate"),
        ("tolerable", "moderate"),
        ("manageable", "moderate"),
        ("moderate", "moderate"),
        ("medium", "moderate"),
        ("average", "moderate"),
        ("very mild", "mild"),
        ("little bit", "mild"),
        ("a little", "mild"),
        ("not severe", "mild"),
        ("not very bad", "mild"),
        ("bearable", "mild"),
        ("minimal", "mild"),
        ("minimum", "mild"),
        ("slight", "mild"),
        ("slightly", "mild"),
        ("minor", "mild"),
        ("mild", "mild"),
        ("low", "low"),
        ("high", "high"),
    ]
    for keyword, normalized in severity_mappings:
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
    if "upper part" in lowered or "upper stomach" in lowered or "upper abdomen" in lowered:
        return "upper abdomen"
    if "lower part" in lowered or "lower stomach" in lowered or "lower abdomen" in lowered:
        return "lower abdomen"
    if "in my " in lowered:
        return re.sub(r"^.*?in my ", "", lowered).strip()
    return None


SEVERITY_KEYWORDS_SET = {
    "mild", "moderate", "severe", "very severe", "extreme", "intense", "high", "low",
    "bad", "worse", "worsening", "good", "better", "minimal", "minimum", "slight",
    "slightly", "bearable", "tolerable", "manageable", "minor", "excruciating", "unbearable"
}

TRAUMA_KEYWORDS = {
    "hit", "bump", "bumped", "fell", "fall", "fallen", "blow", "accident",
    "trauma", "injury", "injured", "struck", "collision", "knocked", "impact",
    "cut", "bruise", "bruised", "bleeding"
}


def _has_trauma_context(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(re.search(rf"\b{kw}\b", lowered) for kw in TRAUMA_KEYWORDS)


def _canonicalize_chief_complaint(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = str(text).strip()
    if not cleaned:
        return None

    # Strip conversational filler prefixes
    filler_prefixes = [
        r"^(?:patient\s+reports|patient\s+presents\s+with(?::)?|presenting\s+complaint(?::)?)\s*",
        r"^(?:i\s+have|i\s+am\s+having|i\s+had|i\s+was\s+having|i\s+have\s+been\s+having|i\s+have\s+a)\s*",
        r"^(?:it\s+is\s+a|it\s+is|it's\s+a|it's|this\s+is\s+a|this\s+is|there\s+is\s+a|there\s+is)\s*",
    ]
    candidate = cleaned
    for pattern in filler_prefixes:
        candidate = re.sub(pattern, "", candidate, flags=re.IGNORECASE).strip()

    # Strip conversational trailing clauses like ", it is and it is moderate", " and it is moderate"
    trailing_clauses = [
        r"[,;]?\s*(?:and\s+)?it\s+is\s+(?:and\s+it\s+is\s+)?(?:mild|moderate|severe|very\s+severe|extreme|intense|bad|low|high).*$",
        r"[,;]?\s*(?:and\s+)?it's\s+(?:mild|moderate|severe|very\s+severe|extreme|intense|bad|low|high).*$",
        r"[,;]?\s*(?:rated\s+as|severity\s+is|scale\s+is)\s+(?:mild|moderate|severe|very\s+severe|extreme|intense|bad|low|high).*$",
        r"[,;]?\s*(?:since|for)\s+\d+\s*(?:days?|hours?|weeks?|months?).*$",
    ]
    for pattern in trailing_clauses:
        candidate = re.sub(pattern, "", candidate, flags=re.IGNORECASE).strip()

    candidate = candidate.strip(".,;: -_")
    lower_cand = candidate.lower()
    cleaned_lower = cleaned.lower()

    # Clinical check: differentiate trauma from spontaneous head complaint
    if "head" in cleaned_lower:
        if _has_trauma_context(cleaned_lower):
            return "head injury"
        if any(kw in cleaned_lower for kw in ["headache", "head pain", "pain in head", "pain in my head", "ache in head"]):
            return "headache"
        if lower_cand in {"head", "pain in head", "head pain", "pain in my head"}:
            return "headache"

    if not candidate or lower_cand in {"it", "this", "pain", "something", "problem", "issue", "moderate", "severe", "mild"}:
        if "shiver" in cleaned_lower or "chills" in cleaned_lower:
            return "shivering and chills"
        if "burning" in cleaned_lower and "pain" in cleaned_lower:
            return "burning pain"
        if "sharp" in cleaned_lower and "pain" in cleaned_lower:
            return "sharp pain"
        if "cramping" in cleaned_lower and "pain" in cleaned_lower:
            return "cramping pain"
        if "throbbing" in cleaned_lower and "pain" in cleaned_lower:
            return "throbbing pain"
        if "chest" in cleaned_lower:
            return "chest injury" if _has_trauma_context(cleaned_lower) else "chest pain"
        if "stomach" in cleaned_lower or "abdomen" in cleaned_lower:
            return "abdominal trauma" if _has_trauma_context(cleaned_lower) else "abdominal pain"
        if "headache" in cleaned_lower:
            return "headache"
        if "fever" in cleaned_lower:
            return "fever"
        if "cough" in cleaned_lower:
            return "cough"
        if lower_cand == "pain":
            return "pain"
        return None

    if "shiver" in cleaned_lower or "chills" in cleaned_lower:
        return "shivering and chills"

    if "head" in lower_cand:
        if _has_trauma_context(lower_cand):
            return "head injury"
        if any(kw in lower_cand for kw in ["headache", "pain", "ache"]):
            return "headache"

    return candidate.lower()


def _sanitize_associated_symptoms(symptoms) -> list[str]:
    if not symptoms:
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    raw_list = symptoms if isinstance(symptoms, list) else [symptoms]
    for s in raw_list:
        if s is None:
            continue
        text = str(s).strip()
        if not text:
            continue
        low = text.lower()
        if low in {"none", "null", "nan", "nothing", "no", "no symptoms"}:
            continue
        if low in SEVERITY_KEYWORDS_SET or any(sk in low for sk in SEVERITY_KEYWORDS_SET):
            continue
        if any(dw in low for dw in ["day", "days", "hour", "hours", "week", "weeks", "month", "months", "since", "for"]):
            continue
        if low in {"pain", "stomach pain", "it", "this", "that", "upper part", "lower part"}:
            continue
        if low not in seen:
            seen.add(low)
            cleaned.append(text)
    return cleaned


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
        "cold and shivering",
        "shivering",
        "chills",
        "stomach pain",
        "abdominal pain",
        "headache",
        "fever",
        "cough",
        "nausea",
        "vomiting",
        "chest pain",
        "burning pain",
        "sharp pain",
        "pain",
        "dizziness",
        "fatigue",
        "body pain",
        "body ache",
        "sore throat",
        "rash",
    ]

    severe_complaint_match = re.search(r"\b(severe|moderate|mild)\s+(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain|burning pain|pain|shivering|chills)\b", lower)
    if severe_complaint_match:
        extracted["chief_complaint"] = _canonicalize_chief_complaint(severe_complaint_match.group(0).strip())
    elif re.search(r"\bi have\b.*\b(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain|burning pain|pain|shivering|chills)\b", lower):
        complaint = re.search(r"\b(stomach pain|abdominal pain|headache|fever|cough|nausea|vomiting|chest pain|burning pain|pain|shivering|chills)\b", lower).group(1)
        extracted["chief_complaint"] = _canonicalize_chief_complaint(complaint)
    elif "burning" in lower and "pain" in lower:
        extracted["chief_complaint"] = "Burning pain"
        extracted["nature_of_pain"] = "burning"
    elif "shiver" in lower or "chills" in lower:
        extracted["chief_complaint"] = "Shivering and chills"
    elif "head" in lower and _has_trauma_context(lower):
        extracted["chief_complaint"] = "head injury"
    elif "head" in lower and any(kw in lower for kw in ["headache", "head pain", "pain in head", "pain in my head", "ache", "hurts"]):
        extracted["chief_complaint"] = "headache"
    elif any(keyword in lower for keyword in complaint_map):
        for keyword in complaint_map:
            if keyword in lower:
                extracted["chief_complaint"] = _canonicalize_chief_complaint(keyword)
                break

    if not extracted["chief_complaint"] and not previous_question:
        candidate_cc = _canonicalize_chief_complaint(message)
        if candidate_cc:
            extracted["chief_complaint"] = candidate_cc

    detected_assoc = []
    common_symptom_words = [
        "fever", "cough", "headache", "nausea", "vomiting", "shivering", "chills",
        "cold", "dizziness", "fatigue", "weakness", "body pain", "body ache",
        "sore throat", "rash", "diarrhea"
    ]
    for sym in common_symptom_words:
        if sym in lower:
            if not extracted["chief_complaint"] or sym not in extracted["chief_complaint"].lower():
                detected_assoc.append(sym)
    extracted["associated_symptoms"] = _sanitize_associated_symptoms(detected_assoc)

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

    if extracted["severity"] is None:
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

    from app.llm_adapter import get_llm_adapter
    adapter = get_llm_adapter()
    try:
        adaptive_result = adapter.conduct_adaptive_turn(
            current_message=patient_message,
            conversation_history=state.get("conversation_history") or [],
            current_state=state,
        )
        extracted = adaptive_result.model_dump()
    except Exception:
        extracted = _fallback_extract_information(patient_message, previous_question)
        extracted["is_complete"] = False
        extracted["adaptive_question"] = None

    previous_question = state.get("conversation_message", "")
    extracted = _contextualize_extraction(extracted, previous_question, patient_message)
    if "adaptive_result" in locals() and hasattr(adaptive_result, "is_complete"):
        extracted["is_complete"] = adaptive_result.is_complete
        extracted["adaptive_question"] = adaptive_result.adaptive_question

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

    if safe.get("duration"):
        safe["duration"] = _extract_duration(safe["duration"])
    if safe.get("duration") is None:
        safe["duration"] = _extract_duration(message)

    if not question:
        return safe

    # Field correction: Check if values are in wrong fields
    # This happens when LLM confuses fields regardless of previous question
    
    # If severity is missing but duration looks like it's severity, move it
    if safe.get("severity") is None and safe.get("duration"):
        duration_val = str(safe.get("duration")).lower()
        if duration_val in SEVERITY_KEYWORDS_SET or any(kw in duration_val for kw in SEVERITY_KEYWORDS_SET):
            safe["severity"] = safe["duration"]
            safe["duration"] = None

    # If location looks like severity, move it
    if safe.get("location"):
        loc_val = str(safe.get("location")).lower()
        if loc_val in SEVERITY_KEYWORDS_SET or any(kw in loc_val for kw in SEVERITY_KEYWORDS_SET):
            if safe.get("severity") is None:
                safe["severity"] = safe["location"]
            safe["location"] = None

    # Clean and filter associated_symptoms
    if safe.get("associated_symptoms"):
        raw_assoc = safe["associated_symptoms"] if isinstance(safe["associated_symptoms"], list) else [safe["associated_symptoms"]]
        for item in raw_assoc:
            item_str = str(item).strip().lower()
            if item_str in SEVERITY_KEYWORDS_SET or any(kw in item_str for kw in SEVERITY_KEYWORDS_SET):
                if safe.get("severity") is None:
                    safe["severity"] = item_str
        safe["associated_symptoms"] = _sanitize_associated_symptoms(raw_assoc)

    # Ensure chief_complaint is canonicalized
    if safe.get("chief_complaint"):
        safe["chief_complaint"] = _canonicalize_chief_complaint(safe["chief_complaint"])

    # Fallback severity extraction from message text if still missing
    if safe.get("severity") is None:
        direct_sev = _extract_severity(message)
        if direct_sev:
            safe["severity"] = direct_sev
    
    # With previous question context, apply contextual resolution
    
    # Handle severity questions: secondary check for severity extraction
    if "severity" in question or "how severe" in question or "severe" in question:
        if safe.get("severity") is not None:
            safe["chief_complaint"] = None
    
    # Handle location questions
    if "where" in question or "location" in question:
        if safe.get("chief_complaint") and safe.get("location"):
            safe["chief_complaint"] = None
        if safe.get("location") is None and ("upper abdomen" in message or "upper part" in message or "upper stomach" in message):
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
        "intense", "high", "low", "worse", "worsening", "bad",
        "minimal", "minimum", "slight", "slightly", "bearable",
        "tolerable", "manageable", "minor"
    }
    return _extract_severity(value) is not None or any(keyword in text for keyword in severity_keywords)


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

        # If intake was already marked complete in the state snapshot, preserve existing structured slots
        if state.get("information_complete") and existing_value is not None and field != "associated_symptoms":
            merged_state[field] = existing_value
            continue

        if field == "associated_symptoms":
            filtered_new_items = _sanitize_associated_symptoms(normalized_new_value)
            if existing_chief_complaint:
                filtered_new_items = [
                    item for item in filtered_new_items
                    if str(item).lower() != str(existing_chief_complaint).lower()
                ]
            merged_state[field] = _merge_unique_list(existing_value, filtered_new_items)
            continue

        if field == "chief_complaint":
            if normalized_new_value is None:
                merged_state[field] = existing_value
                continue
            canonical_new = _canonicalize_chief_complaint(normalized_new_value)
            if not canonical_new:
                merged_state[field] = existing_value
                continue
            if existing_chief_complaint and (_looks_like_symptom_description(canonical_new) or _is_likely_symptom_only(canonical_new)):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "location", canonical_new):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "severity", canonical_new):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "duration", canonical_new):
                merged_state[field] = existing_value
                continue
            if previous_question and _matches_previous_question_context(previous_question, "nature_of_pain", canonical_new):
                merged_state[field] = existing_value
                continue
            # If already have a valid chief complaint, preserve it and record any new symptom into associated_symptoms
            if existing_chief_complaint:
                if canonical_new.lower() != existing_chief_complaint.lower() and canonical_new.lower() not in {"pain", "problem", "discomfort"}:
                    merged_state["associated_symptoms"] = _merge_unique_list(
                        merged_state.get("associated_symptoms", []),
                        [canonical_new]
                    )
                merged_state[field] = existing_chief_complaint
                continue
            merged_state[field] = canonical_new
            continue

        if normalized_new_value is None:
            merged_state[field] = existing_value
            continue

        if field == "duration" and normalized_new_value:
            clean_dur = _extract_duration(normalized_new_value)
            if clean_dur:
                merged_state[field] = clean_dur
                continue

        if field == "severity" and normalized_new_value:
            clean_sev = _extract_severity(normalized_new_value)
            raw_msg = f"{state.get('current_message', '')} {state.get('original_transcript', '')}".lower()
            sev_kws = ["mild", "slight", "minimal", "little", "bearable", "manageable", "moderate", "tolerable", "medium", "average", "fair", "severe", "unbearable", "excruciating", "intense", "extreme", "terrible", "worst", "bad"]
            if clean_sev and any(kw in raw_msg for kw in sev_kws):
                merged_state[field] = clean_sev
                continue
            elif clean_sev and existing_value:
                merged_state[field] = existing_value
                continue
            else:
                merged_state[field] = existing_value
                continue

        if previous_question and field in {"location", "severity", "duration", "nature_of_pain"}:
            if not _matches_previous_question_context(previous_question, field, normalized_new_value):
                merged_state[field] = existing_value
                continue

        merged_state[field] = normalized_new_value

    # Smart clinical synthesis: if chief complaint is generic ("pain" or None) but location is known
    cc = merged_state.get("chief_complaint")
    loc = merged_state.get("location")
    raw_utterances = f"{state.get('current_message', '')} {state.get('original_transcript', '')}"

    if (not cc or cc.lower() in {"pain", "discomfort", "problem", "issue"}) and loc:
        loc_lower = loc.lower()
        has_trauma = _has_trauma_context(raw_utterances) or _has_trauma_context(loc_lower)
        if "head" in loc_lower:
            merged_state["chief_complaint"] = "head injury" if has_trauma else "headache"
        elif "chest" in loc_lower:
            merged_state["chief_complaint"] = "chest injury" if has_trauma else "chest pain"
        elif any(ab in loc_lower for ab in ["abdomen", "stomach"]):
            merged_state["chief_complaint"] = "abdominal trauma" if has_trauma else "abdominal pain"
        elif "knee" in loc_lower:
            merged_state["chief_complaint"] = f"{loc_lower} injury" if has_trauma else f"{loc_lower} pain"
        else:
            merged_state["chief_complaint"] = f"{loc_lower} injury" if has_trauma else f"{loc_lower} pain"

    if not merged_state.get("chief_complaint") and merged_state.get("associated_symptoms"):
        # Promote primary symptom to chief complaint if no CC was extracted
        first_sym = merged_state["associated_symptoms"][0]
        merged_state["chief_complaint"] = _canonicalize_chief_complaint(first_sym)

    if "is_complete" in extracted:
        merged_state["is_complete"] = extracted["is_complete"]
    if "adaptive_question" in extracted and extracted["adaptive_question"]:
        merged_state["adaptive_question"] = extracted["adaptive_question"]

    if "pertinent_negatives" in extracted and extracted["pertinent_negatives"]:
        existing_negs = merged_state.get("pertinent_negatives") or state.get("pertinent_negatives") or []
        new_negs = [n for n in extracted["pertinent_negatives"] if n not in existing_negs]
        merged_state["pertinent_negatives"] = existing_negs + new_negs
    elif "pertinent_negatives" in state:
        merged_state["pertinent_negatives"] = state["pertinent_negatives"]

    if "past_history" in extracted and extracted["past_history"]:
        merged_state["past_history_notes"] = extracted["past_history"]
    elif "past_history_notes" in state:
        merged_state["past_history_notes"] = state["past_history_notes"]

    if "additional_notes" in extracted and extracted["additional_notes"]:
        merged_state["additional_patient_notes"] = extracted["additional_notes"]
    elif "additional_patient_notes" in state:
        merged_state["additional_patient_notes"] = state["additional_patient_notes"]

    if "intake_stage" in extracted and extracted["intake_stage"]:
        merged_state["intake_stage"] = extracted["intake_stage"]
    elif "intake_stage" in state:
        merged_state["intake_stage"] = state["intake_stage"]

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

    if "pertinent_negatives" not in validated or validated["pertinent_negatives"] is None:
        validated["pertinent_negatives"] = []

    if "past_history_notes" not in validated:
        validated["past_history_notes"] = None

    if "additional_patient_notes" not in validated:
        validated["additional_patient_notes"] = None

    if "intake_stage" not in validated:
        validated["intake_stage"] = "symptom_exploration"

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
    elif validated["information_complete"]:
        validated["information_complete_snapshot"] = True

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
    questions_asked = list(state.get("questions_asked") or [])

    # If chief complaint is still missing, attempt resolution from current message
    if not complaint:
        msg = (state.get("current_message") or "").strip()
        if msg:
            candidate = _canonicalize_chief_complaint(msg)
            if candidate:
                state["chief_complaint"] = candidate
                complaint = candidate

    if not complaint:
        # If chief complaint was already asked, DO NOT LOOP!
        if "chief_complaint" in questions_asked or len(questions_asked) >= 2:
            msg = (state.get("current_message") or "").strip()
            state["chief_complaint"] = msg.capitalize() if msg else "Reported discomfort"
            complaint = state["chief_complaint"]
        else:
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

    # If adaptive intake is actively ongoing and has an adaptive follow-up question
    # (e.g. asking about past history or open floor), do not prematurely mark complete!
    adaptive_q = state.get("adaptive_question")
    if adaptive_q and "Thank you. Your clinical intake and assessment are complete" not in adaptive_q:
        if not state.get("is_complete") and not state.get("information_complete_snapshot"):
            information_complete = False

    # Anti-deadlock progression guard:
    # If all currently missing required fields have already been asked once,
    # or if we have reached the inquiry budget:
    known_descriptors = sum(1 for k in ["nature_of_pain", "location", "duration", "severity"] if _field_has_value(state.get(k)))
    assoc_count = len(state.get("associated_symptoms") or [])

    if len(missing) > 0:
        all_asked = all(f in questions_asked for f in missing)
        if all_asked or (len(questions_asked) >= 3 and (known_descriptors >= 1 or assoc_count >= 1)) or len(questions_asked) >= 4:
            missing = []
            information_complete = True

    return {
        "missing_information": missing,
        "information_complete": information_complete
    }


FORBIDDEN_QUESTION_TERMS = [
    "tablet", "capsule", "mg", "syrup", "injection", "antibiotic",
    "paracetamol", "ibuprofen", "aspirin", "steroid", "take this", "take some",
    "prescribe", "prescription", "you might have", "sounds like you have",
    "i think you have", "i believe you have", "diagnos"
]


def _validate_clinical_question(question: str | None, target_field: str, known_info: dict) -> bool:
    """
    Deterministic Python clinical validation for AI-generated questions.
    Ensures:
    1. Output is a non-empty string between 8 and 300 characters.
    2. Ends with '?' for questions, or '.'/'?' for open-floor/closing invitations.
    3. Contains no line breaks or run-on conversational filler.
    4. Does not prescribe, give medical advice, or speculate diagnoses.
    5. Does not re-ask information already confirmed in known_info.
    """
    if not isinstance(question, str):
        return False
    q = question.strip()
    if len(q) < 8 or len(q) > 300:
        return False
    if "\n" in q:
        return False

    is_open_floor = any(phrase in q.lower() for phrase in ["describe to me", "go on with that", "anything else", "other things", "want to describe"])
    if is_open_floor or target_field in {"open_floor", "closing", "follow_up"}:
        if not (q.endswith("?") or q.endswith(".")):
            return False
    else:
        if not q.endswith("?"):
            return False

    q_lower = q.lower()
    for kw in FORBIDDEN_QUESTION_TERMS:
        if kw in q_lower:
            return False

    # Prevent asking for information already confirmed in known state
    if known_info.get("duration") and target_field != "duration":
        if any(w in q_lower for w in ["how long", "when did", "since when", "how many days", "how many hours"]):
            return False
    if known_info.get("severity") and target_field != "severity":
        if any(w in q_lower for w in ["scale of", "how severe", "intensity", "how bad"]):
            return False
    if known_info.get("location") and target_field != "location":
        if any(w in q_lower for w in ["where exactly", "where is", "which part of your"]):
            return False
    if known_info.get("nature_of_pain") and target_field != "nature_of_pain":
        if any(w in q_lower for w in ["what kind of pain", "describe the pain", "feel like"]):
            return False

    return True


def select_next_question(state: VaidyaArcState):
    complaint = state.get("chief_complaint")
    missing = list(state.get("missing_information") or [])
    questions_asked = list(state.get("questions_asked", []) or [])

    if state.get("information_complete"):
        return {
            "next_question": None,
            "questions_asked": questions_asked
        }

    known_info = {}
    for key in ["chief_complaint", "location", "nature_of_pain", "duration", "severity"]:
        val = state.get(key)
        if _field_has_value(val):
            known_info[key] = val

    next_field = None
    for field in missing:
        if field not in questions_asked:
            next_field = field
            break

    # 1. Primary choice: Use the AI's adaptive question if present and valid
    adaptive_q = state.get("adaptive_question")
    if adaptive_q and _validate_clinical_question(adaptive_q, next_field or "follow_up", known_info):
        updated_questions = list(questions_asked) + ([next_field] if next_field else ["adaptive_question"])
        return {
            "next_question": adaptive_q,
            "questions_asked": updated_questions
        }

    if not missing:
        return {
            "next_question": None,
            "questions_asked": questions_asked
        }

    # 2. If next_field is None (all missing were asked), avoid deadlocking:
    if next_field is None:
        next_field = missing[0] if missing else "general"

    # 3. Deterministic fallback question from static templates
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
            fallback_question = questions_for_complaint[next_field]
        else:
            fallback_question = DEFAULT_QUESTIONS.get(next_field, "Could you share a bit more about how your symptoms started?")
    else:
        fallback_question = "Could you tell me what health concern or symptoms you are experiencing today?"

    # 4. Try LLM adapter generate_next_question
    candidate_question = None
    try:
        from app.llm_adapter import get_llm_adapter
        adapter = get_llm_adapter()
        candidate_question = adapter.generate_next_question(
            current_message=state.get("current_message") or "",
            known_info=known_info,
            missing_info=missing,
            target_field=next_field,
            previous_question=state.get("conversation_message"),
        )
    except Exception:
        candidate_question = None

    if candidate_question and _validate_clinical_question(candidate_question, next_field, known_info):
        next_question = candidate_question
    else:
        next_question = fallback_question

    updated_questions_asked = list(questions_asked) + [next_field]

    return {
        "next_question": next_question,
        "questions_asked": updated_questions_asked
    }


def ask_next_question(state: VaidyaArcState):
    closing_message = (
        "Thank you. Your clinical intake and assessment are complete. "
        "I have organized your details into a clinical summary for the doctor. "
        "If there are any other things you want to describe to me as you wait, please feel free to go on with that."
    )

    conv_history = list(state.get("conversation_history") or [])
    current_msg = state.get("current_message")
    if current_msg and not any(entry.get("content") == current_msg and entry.get("role") == "patient" for entry in conv_history[-2:]):
        conv_history.append({"role": "patient", "content": current_msg})

    if state.get("information_complete") and not (state.get("missing_information") or []):
        return {
            "conversation_message": closing_message,
            "next_question": None,
            "conversation_history": conv_history
        }

    question = state.get("next_question")
    if question:
        conv_history.append({"role": "assistant", "content": question})
        return {
            "conversation_message": question,
            "next_question": question,
            "conversation_history": conv_history
        }

    return {
        "conversation_message": closing_message,
        "next_question": None,
        "conversation_history": conv_history
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

    closing_message = (
        "Thank you. Your clinical intake and assessment are complete. "
        "I have organized your details into a clinical summary for the doctor. "
        "If there are any other things you want to describe to me as you wait, please feel free to go on with that."
    )

    completion_state = {
        "next_question": None,
        "conversation_message": closing_message,
    }

    return {
        **completion_state,
        "red_flag_status": result["red_flag_status"],
        "red_flags": result["red_flags"],
        "red_flag_evidence": result["red_flag_evidence"],
        "immediate_attention_required": result["immediate_attention_required"],
        "red_flag_rule_hits": result["red_flag_rule_hits"],
    }
