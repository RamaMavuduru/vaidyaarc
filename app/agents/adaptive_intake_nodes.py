"""
VaidyaArc Brain - Adaptive Intake Nodes.

Implements cognitive extraction, versioned ledger consolidation,
presentation-dependent governance, adaptive inquiry, and safety sanitization.
"""

from __future__ import annotations
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.domain.clinical_history_schema import (
    EvolvingClinicalHistory,
    ClinicalDelta,
    ClinicalFinding,
    ConversationTurn,
    ConversationRole,
    EpistemicStatus,
    InterviewStatus,
    VersionedAttribute,
    AttributeEvidence,
    SourceType,
)
from app.services.history_consolidation import consolidate_delta_into_history
from app.services.clinical_governance import (
    tier1_emergency_precheck,
    governance_context_is_sufficient,
    calculate_advisory_entropy,
    sanitize_patient_question,
    EMERGENCY_ALERT_MESSAGE,
)
from app.adapters.canonical_projection_adapter import project_history_to_canonical_state
from app.llm_adapter import get_llm_adapter


def _extract_delta_fallback(
    message: str,
    turn_id: int,
    history: Optional[EvolvingClinicalHistory] = None,
    previous_question: Optional[str] = None,
) -> ClinicalDelta:
    """
    Robust deterministic extraction fallback for clinical deltas.
    Extracts findings, identifies negations (DENIED), affirmations (REPORTED),
    and builds attribute-level evidence without synthetic data.
    """
    from app.nodes import _fallback_extract_information

    raw_dict = _fallback_extract_information(message, previous_question or "")
    findings = []

    msg_lower = message.lower()
    
    # 1. Chief Complaint
    complaint_name = raw_dict.get("chief_complaint")
    if complaint_name:
        if any(kw in complaint_name.lower() for kw in ["ignore", "instruction", "prescribe", "prompt", "system", "tablet"]) or len(complaint_name) > 40:
            complaint_name = None

    if not complaint_name:
        complaint_patterns = [
            ("sneezing", r"\b(sneezing|runny nose|nasal congestion)\b"),
            ("lower back pain", r"\b(back\s+(stiffness|pain|ache)|lower\s+back)\b"),
            ("heartburn", r"\b(burning\s+sensation.*chest|acid\s+taste|heartburn|gerd)\b"),
            ("ankle sprain", r"\b(twisted.*ankle|ankle\s+(sprain|pain|swelling))\b"),
            ("sore throat", r"\b(sore\s+throat|throat\s+pain|pain\s+in\s+throat)\b"),
            ("headache", r"\b(headache|head\s+pain|throbbing.*head|migraine|pain\s+on\s+one\s+side\s+of\s+my\s+head)\b"),
            ("abdominal pain", r"\b(stomach\s+pain|abdominal\s+pain|belly\s+pain|stomach\s+cramp)\b"),
            ("knee pain", r"\b(knee\s+pain|hurting.*knee|knee.*hurt)\b"),
            ("cough", r"\b(cough|coughing)\b"),
            ("fever", r"\b(fever|feverish|high\s+temperature)\b"),
        ]
        for c_label, c_pat in complaint_patterns:
            if re.search(c_pat, msg_lower):
                complaint_name = c_label
                break

    # Prioritize primary bodily pain complaints over secondary symptoms (e.g. headache over nausea)
    if "pain" in msg_lower or "hurts" in msg_lower:
        if "head" in msg_lower and complaint_name != "headache":
            if complaint_name and complaint_name != "headache":
                raw_dict.setdefault("associated_symptoms", []).append(complaint_name)
            complaint_name = "headache"
        elif ("stomach" in msg_lower or "abdomen" in msg_lower or "belly" in msg_lower) and complaint_name != "abdominal pain":
            if complaint_name and complaint_name != "abdominal pain":
                raw_dict.setdefault("associated_symptoms", []).append(complaint_name)
            complaint_name = "abdominal pain"
        elif "back" in msg_lower and complaint_name != "lower back pain":
            if complaint_name and complaint_name != "lower back pain":
                raw_dict.setdefault("associated_symptoms", []).append(complaint_name)
            complaint_name = "lower back pain"
        elif "knee" in msg_lower and complaint_name != "knee pain":
            if complaint_name and complaint_name != "knee pain":
                raw_dict.setdefault("associated_symptoms", []).append(complaint_name)
            complaint_name = "knee pain"

    # Contextual resolution: If patient is answering follow-up, bind to existing chief complaint in history
    existing_entity_id = None
    if not complaint_name and history and history.chief_complaint:
        complaint_name = history.chief_complaint.canonical_name
        existing_entity_id = history.chief_complaint.entity_id

    if complaint_name:
        c_match = re.search(re.escape(complaint_name.lower()), msg_lower)
        c_start = c_match.start() if c_match else None
        c_end = c_match.end() if c_match else None
        evidence = AttributeEvidence(
            source_turn_id=turn_id,
            evidence_text=message,
            char_start=c_start,
            char_end=c_end,
            extraction_confidence=0.9
        )
        finding = ClinicalFinding(
            entity_id=existing_entity_id or f"ent_complaint_{turn_id}",
            canonical_name=complaint_name.lower(),
            epistemic_status=EpistemicStatus.REPORTED,
            verbatim_patient_term=complaint_name,
            status_evidence=evidence,
        )

        # Duration
        dur = raw_dict.get("duration")
        if dur:
            finding.duration = VersionedAttribute(
                attribute_name="duration",
                current_value=dur,
                evidence=evidence
            )

        # Severity
        sev = raw_dict.get("severity")
        if sev:
            finding.severity = VersionedAttribute(
                attribute_name="severity",
                current_value=sev,
                evidence=evidence
            )

        # Location
        loc = raw_dict.get("location")
        if loc:
            finding.anatomical_site = VersionedAttribute(
                attribute_name="anatomical_site",
                current_value=loc,
                evidence=evidence
            )

        # Nature of pain
        nature = raw_dict.get("nature_of_pain")
        if nature:
            finding.character = VersionedAttribute(
                attribute_name="character",
                current_value=nature,
                evidence=evidence
            )

        findings.append(finding)

    # 2. Associated Symptoms & Pertinent Negatives
    # Detect explicit negations: "no nausea", "no vomiting", "denies fever"
    neg_patterns = [
        r"\b(?:no|not\s+having|without|denies)\s+([a-zA-Z\s]{3,20})\b",
    ]
    for pat in neg_patterns:
        for match in re.finditer(pat, msg_lower):
            denied_term = match.group(1).strip()
            # Stop if punctuation
            denied_term = re.split(r"[,.;]", denied_term)[0].strip()
            if len(denied_term) >= 3 and denied_term not in ["further", "other", "problem", "issues"]:
                ev = AttributeEvidence(
                    source_turn_id=turn_id,
                    evidence_text=match.group(0),
                    char_start=match.start(),
                    char_end=match.end(),
                    extraction_confidence=0.95
                )
                findings.append(ClinicalFinding(
                    entity_id=f"ent_neg_{turn_id}_{match.start()}",
                    canonical_name=denied_term,
                    epistemic_status=EpistemicStatus.DENIED,
                    verbatim_patient_term=match.group(0),
                    status_evidence=ev
                ))

    # 3. Reported associated symptoms
    for sym in raw_dict.get("associated_symptoms") or []:
        sym_clean = sym.strip()
        if sym_clean and not any(f.canonical_name.lower() == sym_clean.lower() for f in findings):
            ev = AttributeEvidence(
                source_turn_id=turn_id,
                evidence_text=sym_clean,
                char_start=None,
                char_end=None,
                extraction_confidence=0.85
            )
            findings.append(ClinicalFinding(
                entity_id=f"ent_assoc_{turn_id}_{len(findings)}",
                canonical_name=sym_clean.lower(),
                epistemic_status=EpistemicStatus.REPORTED,
                verbatim_patient_term=sym_clean,
                status_evidence=ev
            ))

    # Additional common symptom keyword scan
    common_symptom_kws = ["nausea", "vomiting", "fever", "chills", "cough", "dizziness", "headache", "shortness of breath"]
    for sym_kw in common_symptom_kws:
        if re.search(r"\b" + sym_kw + r"\b", msg_lower):
            if not any(f.canonical_name.lower() == sym_kw for f in findings):
                s_match = re.search(r"\b" + sym_kw + r"\b", msg_lower)
                ev = AttributeEvidence(
                    source_turn_id=turn_id,
                    evidence_text=sym_kw,
                    char_start=s_match.start() if s_match else None,
                    char_end=s_match.end() if s_match else None,
                    extraction_confidence=0.9
                )
                findings.append(ClinicalFinding(
                    entity_id=f"ent_sym_{turn_id}_{len(findings)}",
                    canonical_name=sym_kw,
                    epistemic_status=EpistemicStatus.REPORTED,
                    verbatim_patient_term=sym_kw,
                    status_evidence=ev
                ))

    # 4. Past history detection
    prev_q_lower = (previous_question or "").lower()
    past_indicators = [
        "first time", "never had", "had this before", "had a similar", "in the past",
        "months ago", "weeks ago", "years ago", "recurrent", "history of", "happened before"
    ]
    is_past_hist_prompt = any(q_kw in prev_q_lower for q_kw in ["before", "first time", "experienced this", "similar episode", "past"])
    if any(ind in msg_lower for ind in past_indicators) or is_past_hist_prompt:
        ev = AttributeEvidence(
            source_turn_id=turn_id,
            evidence_text=message,
            extraction_confidence=0.9
        )
        findings.append(ClinicalFinding(
            entity_id=f"ent_pmh_{turn_id}",
            canonical_name="past occurrence",
            epistemic_status=EpistemicStatus.DENIED if any(w in msg_lower for w in ["first time", "never", "no"]) else EpistemicStatus.REPORTED,
            verbatim_patient_term=message,
            status_evidence=ev
        ))

    # Sufficiency recommendation heuristic
    is_sufficient = bool(complaint_name and (raw_dict.get("duration") or raw_dict.get("severity")))
    rationale = "Key symptom dimensions gathered" if is_sufficient else "Awaiting further symptom clarification"

    return ClinicalDelta(
        turn_id=turn_id,
        extracted_findings=findings,
        supersessions=[],
        unresolved_clarifications=[],
        llm_sufficiency_recommendation=is_sufficient,
        sufficiency_rationale=rationale,
    )


def tier1_safety_precheck_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 1 fast safety precheck executed before any cognitive processing.
    Short-circuits immediately if life-threatening emergency keywords are found.
    """
    msg = state.get("current_message") or ""
    emergency = tier1_emergency_precheck(msg)
    if emergency:
        state["tier1_emergency_triggered"] = True
        state["immediate_attention_required"] = True
        state["status"] = "emergency"
        state["red_flags"] = [emergency["red_flag"]]
        state["red_flag_status"] = "red_flags_detected"
        state["conversation_message"] = emergency["alert_message"]
        state["is_complete"] = True
        state["information_complete"] = True
    return state


def clinical_delta_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cognitive extraction node.
    Extracts clinical entities, epistemic status, and attribute evidence.
    Wraps untrusted patient messages safely.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    msg = (state.get("current_message") or "").strip()
    turn_count = state.get("turn_count", 0) + 1
    prev_question = state.get("conversation_message") or state.get("adaptive_question") or state.get("next_question")

    # Retrieve history object if present
    hist_data = state.get("evolving_clinical_history")
    if hist_data:
        history = EvolvingClinicalHistory.model_validate(hist_data)
    else:
        history = EvolvingClinicalHistory(
            session_id=state.get("episode_id", str(uuid.uuid4())),
            patient_id=state.get("patient_id")
        )

    # Rehydrate chief complaint from state snapshot if missing in history
    if not history.chief_complaint and state.get("chief_complaint"):
        cc_text = state.get("chief_complaint")
        ev = AttributeEvidence(source_turn_id=0, evidence_text=cc_text, extraction_confidence=1.0)
        history.chief_complaint = ClinicalFinding(
            entity_id="ent_complaint_rehydrated",
            canonical_name=cc_text.lower(),
            epistemic_status=EpistemicStatus.REPORTED,
            verbatim_patient_term=cc_text,
            status_evidence=ev
        )
        if state.get("duration"):
            history.chief_complaint.duration = VersionedAttribute(attribute_name="duration", current_value=state.get("duration"), evidence=ev)
        if state.get("severity"):
            history.chief_complaint.severity = VersionedAttribute(attribute_name="severity", current_value=state.get("severity"), evidence=ev)
        if state.get("location"):
            history.chief_complaint.anatomical_site = VersionedAttribute(attribute_name="anatomical_site", current_value=state.get("location"), evidence=ev)
        if state.get("nature_of_pain"):
            history.chief_complaint.character = VersionedAttribute(attribute_name="character", current_value=state.get("nature_of_pain"), evidence=ev)

    # Use LLM adapter or deterministic fallback
    adapter = get_llm_adapter()
    delta: Optional[ClinicalDelta] = None

    if hasattr(adapter, "extract_clinical_delta") and adapter.is_available():
        try:
            delta = adapter.extract_clinical_delta(msg, history.model_dump(), turn_count, prev_question)
        except Exception:
            delta = None

    if delta is None:
        delta = _extract_delta_fallback(msg, turn_count, history, prev_question)

    state["clinical_delta"] = delta.model_dump()
    return state


def state_consolidation_ledger_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    State consolidation node.
    Updates the append-only ledger, resolves supersessions, validates provenance,
    and recalculates the active clinical projection.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    hist_data = state.get("evolving_clinical_history")
    if hist_data:
        history = EvolvingClinicalHistory.model_validate(hist_data)
    else:
        history = EvolvingClinicalHistory(
            session_id=state.get("episode_id", str(uuid.uuid4())),
            patient_id=state.get("patient_id")
        )

    delta_data = state.get("clinical_delta")
    if delta_data:
        delta = ClinicalDelta.model_validate(delta_data)
    else:
        delta = _extract_delta_fallback(state.get("current_message", ""), history.turn_count + 1, history)

    turn = ConversationTurn(
        turn_id=history.turn_count + 1,
        request_id=state.get("request_id", str(uuid.uuid4())),
        role=ConversationRole.PATIENT,
        raw_text=state.get("current_message", ""),
        source_type=SourceType.PATIENT
    )

    history = consolidate_delta_into_history(history, delta, turn)
    history.advisory_entropy_score = calculate_advisory_entropy(history)

    state["evolving_clinical_history"] = history.model_dump()
    state["turn_count"] = history.turn_count
    return state


def deterministic_governance_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic governance node.
    Enforces presentation-dependent safety discriminators to decide whether
    to conclude the interview or formulate another question.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    if state.get("information_complete"):
        state["governance_sufficient"] = True
        state["governance_rationale"] = "Intake information already complete from previous turn snapshot"
        state["governance_verdict"] = "complete"
        return state

    hist_data = state.get("evolving_clinical_history")
    if hist_data:
        history = EvolvingClinicalHistory.model_validate(hist_data)
    else:
        history = EvolvingClinicalHistory(
            session_id=state.get("episode_id", str(uuid.uuid4())),
            patient_id=state.get("patient_id")
        )

    delta_data = state.get("clinical_delta")
    if delta_data:
        delta = ClinicalDelta.model_validate(delta_data)
    else:
        delta = _extract_delta_fallback(state.get("current_message", ""), history.turn_count, history)

    is_sufficient, rationale = governance_context_is_sufficient(history, delta)

    state["governance_sufficient"] = is_sufficient
    state["governance_rationale"] = rationale
    state["evolving_clinical_history"] = history.model_dump()

    if is_sufficient:
        state["governance_verdict"] = "complete"
    else:
        state["governance_verdict"] = "continue"

    return state


def adaptive_question_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formulates a context-aware clinical follow-up question.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    history = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])

    # Check chief complaint
    if history.chief_complaint:
        raw_c = history.chief_complaint.verbatim_patient_term or history.chief_complaint.canonical_name or ""
        if (
            any(kw in raw_c.lower() for kw in ["ignore", "instruction", "prescribe", "prompt", "system", "tablet"])
            or len(raw_c) > 30
        ):
            complaint = "symptoms"
        else:
            complaint = raw_c

        prior_texts = " ".join(history.prior_question_intents).lower()
        duration_already_asked = any(k in prior_texts for k in ["how long", "when did", "start", "duration"])
        severity_already_asked = any(k in prior_texts for k in ["mild", "moderate", "severe", "scale"])
        recurrence_already_asked = any(k in prior_texts for k in ["before", "first time", "previously", "past"])

        if history.chief_complaint.duration is None and not duration_already_asked:
            candidate = f"Approximately how long have you been experiencing this {complaint}?"
        elif history.chief_complaint.severity is None and not severity_already_asked:
            candidate = f"On a scale of mild, moderate, or severe, how would you describe the {complaint}?"
        elif not recurrence_already_asked and not history.past_medical_history and not state.get("past_history_notes"):
            candidate = f"Have you ever experienced this kind of {complaint} before, or is this the first time?"
        else:
            candidate = "Thank you. Is there anything else you would like to describe or share with me about how you are feeling?"
    else:
        candidate = "Could you tell me more about the main health symptoms or discomfort you are experiencing today?"

    state["candidate_question"] = candidate
    return state


def safety_scope_sanitizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes question against duplications, multiple semantic foci, and forbidden clinical jargon.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    history = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    candidate = state.get("candidate_question", "")

    sanitized, _ = sanitize_patient_question(candidate, history)

    state["conversation_message"] = sanitized
    state["adaptive_question"] = sanitized
    state["next_question"] = sanitized
    state["status"] = "in_progress"
    state["is_complete"] = False
    state["information_complete"] = False

    # Also update canonical projection
    proj = project_history_to_canonical_state(history, state)
    state.update(proj)
    return state


def casesheet_synthesizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intake completion closing node.
    Delivers graceful doctor-ready closing and projects final state for downstream engines.
    """
    if state.get("tier1_emergency_triggered"):
        return state

    history = EvolvingClinicalHistory.model_validate(state["evolving_clinical_history"])
    history.interview_status = InterviewStatus.COMPLETE
    closing_msg = (
        "Thank you. Your clinical intake and assessment are complete. "
        "I have organized your details into a clinical summary for the doctor. "
        "If there are any other things you want to describe to me as you wait, "
        "please feel free to go on with that."
    )
    state["evolving_clinical_history"] = history.model_dump(mode="json")
    state["conversation_message"] = closing_msg
    state["status"] = "complete"
    state["is_complete"] = True
    state["information_complete"] = True

    # Deterministically project to canonical state
    proj = project_history_to_canonical_state(history, state)
    state.update(proj)
    state["status"] = "complete"
    state["is_complete"] = True
    state["information_complete"] = True
    return state
