from langchain_ollama import ChatOllama

from app.red_flag_rules import evaluate_red_flags as evaluate_red_flag_rules
from app.state import VaidyaArcState
from app.schemas import IntakeResult

model = ChatOllama(
    model="llama3:latest",
    temperature=0,
    format="json"
)

structured_model = model.with_structured_output(
    IntakeResult,
    method="json_schema"
)


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

EXAMPLES:

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

    result = structured_model.invoke(prompt)
    extracted = result.model_dump()

    previous_question = state.get("conversation_message", "")
    extracted = _contextualize_extraction(extracted, previous_question, patient_message)

    print("\nDEBUG - NEW INFORMATION EXTRACTED:")
    print(extracted)

    return {
        "extracted_information": extracted
    }


def _normalize_blank(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() in {"none", "null", "nan", ""}:
            return None
        return cleaned if cleaned else None
    return value


def _contextualize_extraction(extracted, previous_question, patient_message):
    safe = dict(extracted or {})
    question = (previous_question or "").lower()
    message = (patient_message or "").lower().strip()

    if not question:
        return safe

    if "where" in question or "location" in question:
        if safe.get("chief_complaint") and safe.get("location"):
            safe["chief_complaint"] = None
        if safe.get("location") is None and "upper abdomen" in message:
            safe["location"] = "upper abdomen"
        if safe.get("chief_complaint") and message.startswith("in my "):
            safe["chief_complaint"] = None

    if "severity" in question or "how severe" in question or "severe" in question:
        if safe.get("severity") is not None:
            safe["chief_complaint"] = None
        if safe.get("chief_complaint") and str(safe.get("chief_complaint")).lower() in {"moderate", "mild", "severe"}:
            safe["chief_complaint"] = None

    if "when did" in question or "start" in question or "duration" in question:
        if safe.get("duration") is not None:
            safe["chief_complaint"] = None

    if "describe what the pain feels like" in question or "nature of pain" in question or "pain feels like" in question:
        if safe.get("nature_of_pain") is not None:
            safe["chief_complaint"] = None

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


def _matches_previous_question_context(previous_question, field, value):
    if value is None:
        return False

    text = str(value).strip().lower()
    if not text:
        return False

    question = (previous_question or "").lower()

    if field == "location":
        return "where" in question or "location" in question

    if field == "severity":
        return "severity" in question or "how severe" in question or "severe" in question

    if field == "duration":
        return "when did" in question or "duration" in question or "start" in question

    if field == "nature_of_pain":
        return "describe what the pain feels like" in question or "nature of pain" in question or "pain feels like" in question

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
                        str(existing_chief_complaint).lower() if existing_chief_complaint else "",
                        "stomach pain",
                        "pain",
                    }
                ]
            elif normalized_new_value is not None:
                filtered_new_items = [normalized_new_value]
                if filtered_new_items[0].lower() in {str(existing_chief_complaint).lower() if existing_chief_complaint else "", "stomach pain", "pain"}:
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

    validated["extracted_information"] = {}
    return validated


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


def ask_next_question(state: VaidyaArcState):
    if state.get("information_complete") or not state.get("missing_information"):
        return {
            "conversation_message": "Thank you. I have collected the initial information about your concern.",
            "next_question": None
        }

    question = state.get("next_question")
    if not question:
        question = "Thank you. I have collected the initial information about your concern."

    return {
        "conversation_message": question,
        "next_question": question
    }


def evaluate_red_flags(state: VaidyaArcState):
    if not state.get("information_complete"):
        return {
            "red_flag_status": "insufficient_information",
            "red_flags": [],
            "red_flag_evidence": [],
            "immediate_attention_required": False,
            "red_flag_rule_hits": [],
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
