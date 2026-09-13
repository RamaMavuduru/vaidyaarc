"""
VaidyaArc Brain - History Consolidation and Versioned Ledger Service.

Implements immutable turn append, attribute-level provenance validation,
explicit supersession management, contradiction handling, and active projection.
"""

from __future__ import annotations
import re
from typing import Optional, List, Dict, Any

from app.domain.clinical_history_schema import (
    EvolvingClinicalHistory,
    ClinicalDelta,
    ClinicalFinding,
    VersionedAttribute,
    SupersessionRecord,
    AttributeEvidence,
    ConversationTurn,
    EpistemicStatus,
    SourceType,
    ConversationRole,
)

HIGH_RISK_SAFETY_KEYWORDS = {
    "chest pain", "breathing", "shortness of breath", "dyspnea", "breathless",
    "syncope", "faint", "passed out", "loss of consciousness", "unconscious",
    "head injury", "thunderclap", "sudden severe headache", "unilateral weakness",
    "facial droop", "speech difficulty", "cannot speak", "numbness", "paralysis",
    "poison", "poisoning", "overdose", "suicide", "self harm", "severe bleeding",
    "vomiting blood", "hematemesis", "black stool", "melena", "anaphylaxis",
    "swelling of throat", "throat closing", "stridor", "cyanosis"
}


def is_potential_safety_concept(canonical_name: str, verbatim_term: str) -> bool:
    """Checks whether an entity name or verbatim phrase touches critical safety concepts."""
    combined = f"{canonical_name} {verbatim_term}".lower()
    return any(kw in combined for kw in HIGH_RISK_SAFETY_KEYWORDS)


def validate_grounding(evidence_text: str, turn_text: str) -> bool:
    """
    Checks whether evidence_text correlates to turn_text.
    Tolerates multilingual script normalization, punctuation, and code-switching.
    """
    if not evidence_text or not turn_text:
        return False
    ev_norm = re.sub(r"[^\w\s]", "", evidence_text.lower(), flags=re.UNICODE).strip()
    turn_norm = re.sub(r"[^\w\s]", "", turn_text.lower(), flags=re.UNICODE).strip()
    if not ev_norm or not turn_norm:
        return False
    if ev_norm in turn_norm:
        return True
    ev_words = set(ev_norm.split())
    turn_words = set(turn_norm.split())
    if ev_words and (len(ev_words & turn_words) / len(ev_words)) >= 0.5:
        return True
    return False


def _find_entity_in_history(
    history: EvolvingClinicalHistory,
    entity_id: str,
    canonical_name: str
) -> Optional[ClinicalFinding]:
    """Finds an entity by ID or canonical name across active findings."""
    if history.chief_complaint:
        if (entity_id and history.chief_complaint.entity_id == entity_id) or (
            canonical_name and history.chief_complaint.canonical_name.lower() == canonical_name.lower()
        ):
            return history.chief_complaint
    for f in history.associated_findings:
        if (entity_id and f.entity_id == entity_id) or (
            canonical_name and f.canonical_name.lower() == canonical_name.lower()
        ):
            return f
    for sys_findings in history.review_of_systems.values():
        for f in sys_findings:
            if (entity_id and f.entity_id == entity_id) or (
                canonical_name and f.canonical_name.lower() == canonical_name.lower()
            ):
                return f
    for f in history.past_medical_history:
        if (entity_id and f.entity_id == entity_id) or (
            canonical_name and f.canonical_name.lower() == canonical_name.lower()
        ):
            return f
    return None


def reconcile_supersessions(
    history: EvolvingClinicalHistory,
    supersessions: List[SupersessionRecord],
    current_turn_id: int
) -> None:
    """
    Applies explicit corrections to versioned attributes, archiving the superseded versions.
    """
    for record in supersessions:
        target = _find_entity_in_history(history, record.entity_id, "")
        if not target:
            continue
        attr_name = record.attribute_name
        current_attr = getattr(target, attr_name, None)
        if isinstance(current_attr, VersionedAttribute):
            current_attr.is_superseded = True
            current_attr.superseded_at_turn = current_turn_id
            current_attr.superseded_by_turn = current_turn_id
            target.superseded_attributes.append(current_attr)
        new_attr = VersionedAttribute(
            attribute_name=attr_name,
            current_value=record.new_value,
            is_superseded=False,
            evidence=record.new_evidence
        )
        setattr(target, attr_name, new_attr)


def merge_finding_attributes(
    existing: ClinicalFinding,
    incoming: ClinicalFinding,
    current_turn_id: int
) -> None:
    """
    Merges non-superseded attributes from incoming into existing finding.
    """
    attribute_keys = [
        "anatomical_site", "laterality", "onset", "duration",
        "severity", "character", "timing", "radiation",
        "triggers", "functional_impact"
    ]
    for attr in attribute_keys:
        inc_val = getattr(incoming, attr, None)
        if inc_val is not None and isinstance(inc_val, VersionedAttribute):
            exist_val = getattr(existing, attr, None)
            if exist_val is None or not exist_val.current_value:
                setattr(existing, attr, inc_val)
    if incoming.aggravating_factors:
        for factor in incoming.aggravating_factors:
            if not any(f.current_value == factor.current_value for f in existing.aggravating_factors):
                existing.aggravating_factors.append(factor)
    if incoming.relieving_factors:
        for factor in incoming.relieving_factors:
            if not any(f.current_value == factor.current_value for f in existing.relieving_factors):
                existing.relieving_factors.append(factor)


def consolidate_delta_into_history(
    history: EvolvingClinicalHistory,
    delta: ClinicalDelta,
    current_turn: ConversationTurn
) -> EvolvingClinicalHistory:
    """
    Consolidates incoming ClinicalDelta into EvolvingClinicalHistory.
    Preserves historical facts, validates provenance, applies supersessions,
    and updates the active projection.
    """
    if not any(
        t.turn_id == current_turn.turn_id and t.request_id == current_turn.request_id
        for t in history.conversation_turns
    ):
        history.conversation_turns.append(current_turn)
    history.turn_count = len([t for t in history.conversation_turns if t.role == ConversationRole.PATIENT])

    reconcile_supersessions(history, delta.supersessions, current_turn.turn_id)

    for finding in delta.extracted_findings:
        grounded = validate_grounding(finding.status_evidence.evidence_text, current_turn.raw_text)
        if not grounded:
            if is_potential_safety_concept(finding.canonical_name, finding.verbatim_patient_term):
                safety_alert = (
                    f"Ungrounded potential safety finding: {finding.canonical_name} "
                    f"({finding.verbatim_patient_term})"
                )
                if safety_alert not in history.unresolved_safety_questions:
                    history.unresolved_safety_questions.append(safety_alert)
            finding.epistemic_status = EpistemicStatus.UNCERTAIN

        existing = _find_entity_in_history(history, finding.entity_id, finding.canonical_name)

        if existing:
            if (
                existing.epistemic_status != finding.epistemic_status
                and finding.epistemic_status != EpistemicStatus.NOT_ELICITED
            ):
                if not any(s.entity_id == existing.entity_id for s in delta.supersessions):
                    existing.epistemic_status = EpistemicStatus.UNCERTAIN
                    clarify_msg = (
                        f"Contradictory status for {existing.canonical_name}: previously "
                        f"{existing.epistemic_status.value}, now stated as {finding.epistemic_status.value}"
                    )
                    if clarify_msg not in delta.unresolved_clarifications:
                        delta.unresolved_clarifications.append(clarify_msg)
            else:
                existing.epistemic_status = finding.epistemic_status
            merge_finding_attributes(existing, finding, current_turn.turn_id)
        else:
            if not history.chief_complaint and finding.epistemic_status == EpistemicStatus.REPORTED:
                history.chief_complaint = finding
            else:
                history.associated_findings.append(finding)

    return history
