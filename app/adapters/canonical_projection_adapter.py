"""
VaidyaArc Brain - Canonical Projection Adapter.

Deterministically projects EvolvingClinicalHistory into legacy VaidyaArcState
dict structure expected by downstream Phase 2B-12.5 engines.
Strictly adheres to zero synthetic placeholder strings (None/empty lists only).
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from app.domain.clinical_history_schema import (
    EvolvingClinicalHistory,
    EpistemicStatus,
    InterviewStatus,
)


def project_history_to_canonical_state(
    history: EvolvingClinicalHistory,
    existing_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Translates an EvolvingClinicalHistory into the canonical flat/structured
    dictionary format expected by downstream clinical nodes (safety, risk, summary, dashavidha).
    Zero synthetic strings are introduced: unelicited fields project as None or [].
    """
    state = dict(existing_state) if existing_state else {}

    # 1. Chief Complaint & Versioned Descriptors
    if history.chief_complaint and history.chief_complaint.epistemic_status == EpistemicStatus.REPORTED:
        state["chief_complaint"] = history.chief_complaint.canonical_name

        # Duration
        dur_attr = getattr(history.chief_complaint, "duration", None)
        if dur_attr and not getattr(dur_attr, "is_superseded", False) and dur_attr.current_value:
            state["duration"] = str(dur_attr.current_value)
        elif "duration" not in state or state["duration"] is None:
            state["duration"] = None

        # Severity
        sev_attr = getattr(history.chief_complaint, "severity", None)
        if sev_attr and not getattr(sev_attr, "is_superseded", False) and sev_attr.current_value:
            val_str = str(sev_attr.current_value).strip()
            from app.nodes import _extract_severity
            state["severity"] = _extract_severity(val_str) or val_str.lower()
        elif "severity" not in state or state["severity"] is None:
            state["severity"] = None

        # Location
        loc_attr = getattr(history.chief_complaint, "anatomical_site", None)
        if loc_attr and not getattr(loc_attr, "is_superseded", False) and loc_attr.current_value:
            state["location"] = str(loc_attr.current_value)
        elif "location" not in state or state["location"] is None:
            state["location"] = None

        # Nature of pain / character
        char_attr = getattr(history.chief_complaint, "character", None)
        if char_attr and not getattr(char_attr, "is_superseded", False) and char_attr.current_value:
            state["nature_of_pain"] = str(char_attr.current_value)
        elif "nature_of_pain" not in state or state["nature_of_pain"] is None:
            state["nature_of_pain"] = None
    else:
        if "chief_complaint" not in state:
            state["chief_complaint"] = None

    # 2. Associated Symptoms (Reported findings)
    reported_assoc = [
        f.canonical_name
        for f in history.associated_findings
        if f.epistemic_status == EpistemicStatus.REPORTED
    ]
    existing_assoc = list(state.get("associated_symptoms") or [])
    for sym in reported_assoc:
        if sym not in existing_assoc:
            existing_assoc.append(sym)
    state["associated_symptoms"] = existing_assoc

    # 3. Pertinent Negatives (Explicitly denied findings)
    denied_assoc = [
        f.canonical_name
        for f in history.associated_findings
        if f.epistemic_status == EpistemicStatus.DENIED
    ]
    existing_denied = list(state.get("pertinent_negatives") or [])
    for sym in denied_assoc:
        if sym not in existing_denied:
            existing_denied.append(sym)
    state["pertinent_negatives"] = existing_denied

    # 4. Past Medical History Notes
    pmh_findings = [
        f"{f.canonical_name}: {f.epistemic_status.value}"
        for f in history.past_medical_history
    ]
    if pmh_findings:
        state["past_history_notes"] = "; ".join(pmh_findings)

    # 5. Epistemic Ledger and Turn Tracking
    state["evolving_clinical_history"] = history.model_dump()
    state["turn_count"] = history.turn_count

    # 6. Status and Completion
    if history.interview_status in (InterviewStatus.COMPLETE, InterviewStatus.BOUNDED_PARTIAL):
        state["is_complete"] = True
        state["information_complete"] = True
        state["missing_information"] = []
    elif history.interview_status == InterviewStatus.SAFETY_ESCALATED:
        state["is_complete"] = True
        state["immediate_attention_required"] = True
    else:
        state["is_complete"] = False
        state["information_complete"] = False

    return state
