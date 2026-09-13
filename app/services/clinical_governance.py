"""
VaidyaArc Brain - Clinical Governance Service.

Provides Tier 1 deterministic emergency precheck, presentation-dependent
sufficiency governance, advisory entropy calculation, question scope sanitization,
and deterministic emergency escalation.
"""

from __future__ import annotations
import re
from typing import Optional, Tuple, List, Dict, Any

from app.domain.clinical_history_schema import (
    EvolvingClinicalHistory,
    ClinicalDelta,
    ClinicalFinding,
    InterviewStatus,
    EpistemicStatus,
)

EMERGENCY_ALERT_MESSAGE: str = (
    "EMERGENCY WARNING: Your reported symptoms indicate a potential medical emergency "
    "requiring immediate clinical attention. Please proceed immediately to the nearest "
    "emergency department or contact emergency medical services."
)

TIER1_EMERGENCY_RULES: List[Tuple[str, re.Pattern]] = [
    (
        "Severe/Radiating Chest Pain",
        re.compile(
            r"\b(crushing\s+chest\s+pain|chest\s+pain.*(radiat|sweat|arm|jaw|back|neck)|"
            r"chest\s+pressure.*(radiat|sweat|arm|jaw|back|neck)|heavy\s+chest\s+pain)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Acute Respiratory Distress",
        re.compile(
            r"\b(cannot\s+breathe|can\'t\s+breathe|struggling\s+to\s+breathe|"
            r"severe\s+shortness\s+of\s+breath|throat\s+(is\s+)?clos(ing|ed)|"
            r"stridor|choking|gasping\s+for\s+air|blue\s+lips|cyanosis)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Acute Neurological Deficit / Stroke",
        re.compile(
            r"\b(facial\s+droop|slurred\s+speech|cannot\s+speak|can\'t\s+speak|"
            r"arm\s+weakness|one\s+side.*(numb|weak|paralyz)|sudden\s+paralysis|"
            r"sudden\s+loss\s+of\s+vision|stroke)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Thunderclap Headache / Meningism",
        re.compile(
            r"\b(thunderclap\s+headache|worst\s+headache\s+of\s+my\s+life|"
            r"sudden\s+severe\s+headache.*worst|stiff\s+neck.*(fever|confus))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Syncope / Loss of Consciousness",
        re.compile(
            r"\b(passed\s+out|lost\s+consciousness|unconscious|fainted\s+and\s+hit\s+head|"
            r"unresponsive)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Severe Hemorrhage",
        re.compile(
            r"\b(vomiting\s+blood|coughing\s+up\s+blood|massive\s+bleeding|"
            r"profuse\s+bleeding|hematemesis|black\s+tarry\s+stool.*dizz)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Anaphylaxis / Airway Compromise",
        re.compile(
            r"\b(anaphylaxis|swelling\s+of\s+(the\s+)?(lips|tongue|throat)|"
            r"throat\s+is\s+swelling)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Psychiatric Crisis / Acute Self-Harm",
        re.compile(
            r"\b(suicid|kill\s+myself|want\s+to\s+die|end\s+my\s+life|overdose[d]?)\b",
            re.IGNORECASE,
        ),
    ),
]

FORBIDDEN_QUESTION_TERMS: List[str] = [
    "tablet", "capsule", "mg", "syrup", "injection", "antibiotic",
    "paracetamol", "ibuprofen", "aspirin", "steroid", "take this", "take some",
    "prescribe", "prescription", "you have ", "diagnos"
]


def tier1_emergency_precheck(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Tier 1 fast regex/keyword emergency precheck.
    Returns emergency metadata if a life-threatening red flag is detected, else None.
    """
    if not raw_text:
        return None
    for label, pattern in TIER1_EMERGENCY_RULES:
        match = pattern.search(raw_text)
        if match:
            return {
                "is_emergency": True,
                "red_flag": label,
                "trigger_phrase": match.group(0),
                "emergency_number": "112",
                "alert_message": EMERGENCY_ALERT_MESSAGE,
            }
    return None


def governance_context_is_sufficient(
    history: EvolvingClinicalHistory,
    delta: ClinicalDelta
) -> Tuple[bool, str]:
    """
    Deterministic governance gate.
    Evaluates whether the clinical history is sufficient to conclude the interview
    based on presentation-dependent safety discriminators and state integrity.
    Universal checklists are strictly avoided.
    """
    # Check 1: Safety escalation or unresolved safety flags block normal completion
    if history.interview_status == InterviewStatus.SAFETY_ESCALATED:
        return False, "Interview interrupted due to safety escalation."
    if history.unresolved_safety_questions:
        return False, f"Unresolved safety questions exist: {', '.join(history.unresolved_safety_questions)}"

    # Check 2: Core presentation must be established
    if not history.chief_complaint or history.chief_complaint.epistemic_status != EpistemicStatus.REPORTED:
        return False, "Chief complaint is not yet established."

    # Check 3: Technical safety ceiling guard
    if history.turn_count >= history.max_turn_ceiling:
        history.interview_status = InterviewStatus.BOUNDED_PARTIAL
        return True, "Technical turn ceiling reached (bounded partial completion)."

    # Check 4: Presentation-dependent safety discriminators
    complaint_name = history.chief_complaint.canonical_name.lower()

    if "chest pain" in complaint_name:
        # Chest pain requires ruling out radiation or high-risk features
        radiation_addressed = (
            history.chief_complaint.radiation is not None
            or any("radiation" in f.canonical_name.lower() or "arm" in f.canonical_name.lower()
                   for f in history.associated_findings)
        )
        if not radiation_addressed and history.turn_count < 3:
            return False, "Chest pain presentation requires rule-out of radiation or associated symptoms."

    elif "headache" in complaint_name:
        # Headache requires acuity/onset assessment to distinguish acute vs chronic
        onset_addressed = history.chief_complaint.onset is not None or history.chief_complaint.duration is not None
        if not onset_addressed and history.turn_count < 2:
            return False, "Headache presentation requires onset/duration clarification."

    elif "abdominal pain" in complaint_name or "stomach pain" in complaint_name:
        # Abdominal pain requires severity or quadrant check
        severity_addressed = history.chief_complaint.severity is not None or history.chief_complaint.anatomical_site is not None
        if not severity_addressed and history.turn_count < 2:
            return False, "Abdominal pain requires severity or site clarification."

    # Check 5: Deterministic validation of LLM sufficiency recommendation
    if delta.llm_sufficiency_recommendation:
        history.interview_status = InterviewStatus.COMPLETE
        history.governance_conclusion_rationale = delta.sufficiency_rationale
        return True, f"Deterministic governance approved completion: {delta.sufficiency_rationale}"

    # Default: Inquiry continues
    return False, "Ongoing clinical inquiry indicated."


def calculate_advisory_entropy(history: EvolvingClinicalHistory) -> float:
    """
    Calculates residual diagnostic uncertainty score (0.0 to 1.0).
    Advisory metric for clinician visibility.
    """
    if not history.chief_complaint:
        return 1.0

    score = 0.85

    # More characterized finding reduces residual uncertainty
    char_attributes = [
        "anatomical_site", "onset", "duration", "severity",
        "character", "timing", "radiation"
    ]
    for attr in char_attributes:
        val = getattr(history.chief_complaint, attr, None)
        if val is not None and getattr(val, "current_value", None) is not None:
            score -= 0.08

    # Associated findings reduce uncertainty
    score -= min(0.20, len(history.associated_findings) * 0.05)

    # Uncertain items increase uncertainty
    for f in history.associated_findings:
        if f.epistemic_status == EpistemicStatus.UNCERTAIN:
            score += 0.10

    # Clamp between 0.05 and 0.95
    return round(max(0.05, min(0.95, score)), 2)


def sanitize_patient_question(
    candidate_question: str,
    history: EvolvingClinicalHistory
) -> Tuple[str, bool]:
    """
    Four-layer question scope sanitizer:
    1. Anti-duplication check against prior intents
    2. Single semantic focus enforcement
    3. Epistemic boundary verification
    4. Forbidden terminology filtering (no prescriptions, no diagnosis)
    """
    if not candidate_question or not candidate_question.strip():
        fallback = _generate_contextual_fallback_question(history)
        return fallback, True

    cleaned = candidate_question.strip()

    # Layer 4: Forbidden terms filter
    lower_q = cleaned.lower()
    for term in FORBIDDEN_QUESTION_TERMS:
        if term in lower_q:
            fallback = _generate_contextual_fallback_question(history)
            return fallback, False

    # Layer 2: Single semantic focus check (if multiple sentences, pick the first question)
    if "?" in cleaned:
        parts = cleaned.split("?")
        first_q = parts[0].strip() + "?"
        if len(first_q) >= 15:
            cleaned = first_q

    # Layer 1: Anti-duplication check
    norm_q = re.sub(r"[^\w\s]", "", cleaned.lower())
    q_words = set(norm_q.split())
    for prior in history.prior_question_intents:
        prior_words = set(re.sub(r"[^\w\s]", "", prior.lower()).split())
        if q_words and prior_words:
            overlap = len(q_words & prior_words) / len(q_words)
            if overlap >= 0.8:
                fallback = _generate_contextual_fallback_question(history)
                return fallback, False

    # Record intent for anti-duplication
    history.prior_question_intents.append(cleaned)
    return cleaned, True


def _generate_contextual_fallback_question(history: EvolvingClinicalHistory) -> str:
    """Generates a safe, non-redundant contextual question."""
    if history.chief_complaint:
        raw_term = (history.chief_complaint.verbatim_patient_term or history.chief_complaint.canonical_name or "").strip().lower()
        if (
            any(term in raw_term for term in FORBIDDEN_QUESTION_TERMS)
            or len(raw_term) > 30
            or any(kw in raw_term for kw in ["ignore", "instruction", "prompt", "system", "tablets", "capsule"])
        ):
            complaint = "symptoms"
        else:
            complaint = raw_term

        prior_texts = " ".join(history.prior_question_intents).lower()
        duration_already_asked = any(k in prior_texts for k in ["how long", "when did", "start", "duration"])
        severity_already_asked = any(k in prior_texts for k in ["mild", "moderate", "severe", "scale"])
        recurrence_already_asked = any(k in prior_texts for k in ["before", "first time", "previously", "past"])

        if history.chief_complaint.duration is None and not duration_already_asked:
            return f"Approximately how long have you been experiencing this {complaint}?"
        if history.chief_complaint.severity is None and not severity_already_asked:
            return f"On a scale from mild to severe, how would you rate the {complaint}?"
        if not recurrence_already_asked:
            return f"Have you experienced this kind of {complaint} previously, or is this the first time?"
        return "Thank you. Is there anything else you would like to describe or share with me about how you are feeling?"
    return "Could you share more details about the main health concern or symptoms you are experiencing today?"



def build_emergency_response(
    history: EvolvingClinicalHistory,
    emergency_trigger: str,
    locale: str = "IN"
) -> Dict[str, Any]:
    """
    Builds the deterministic emergency payload.
    Short-circuits immediately without downstream processing.
    """
    history.interview_status = InterviewStatus.SAFETY_ESCALATED
    emergency_number = "112" if locale.upper() in ["IN", "INDIA"] else "911"
    return {
        "status": "emergency",
        "immediate_attention_required": True,
        "red_flag_status": "red_flags_detected",
        "red_flags": [emergency_trigger],
        "emergency_locale_number": emergency_number,
        "conversation_message": EMERGENCY_ALERT_MESSAGE,
        "clinical_output": {
            "safety_findings": {
                "immediate_attention_required": True,
                "red_flags": [emergency_trigger],
                "emergency_locale_number": emergency_number,
            },
            "intake_summary": {
                "chief_complaint": history.chief_complaint.canonical_name if history.chief_complaint else emergency_trigger,
                "duration": None,
                "severity": "severe",
            }
        }
    }
