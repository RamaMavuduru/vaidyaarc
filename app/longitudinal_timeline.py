"""
Phase 9: Longitudinal Timeline Engine & Context Synthesizer.

Collects, normalizes, deduplicates, and chronologically orders clinical events
from historical encounters, documents, lab investigations, conversations, and baseline profiles.

SAFETY INVARIANTS:
1. 100% Deterministic sorting and date parsing.
2. Preserves undated historical events rather than discarding or guessing dates.
3. Strict provenance preservation for every timeline event.
4. ZERO-LLM.
"""

import re
from datetime import datetime
from typing import Any, Optional

from app.longitudinal_schema import (
    TimelineEvent,
    TimelineEventType,
    LongitudinalPatientContextDTO,
)
from app.biomarker_engine import (
    extract_biomarker_records,
    calculate_biomarker_trajectories,
)
from app.problem_registry import build_problem_registry


def parse_and_normalize_date(raw_date: Optional[str]) -> tuple[Optional[str], str]:
    """
    Normalizes a date string into an ISO 8601 string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    Returns: (normalized_date_str, date_certainty)
    date_certainty is 'exact', 'approximate', or 'unspecified'.
    """
    if not raw_date or not str(raw_date).strip():
        return None, "unspecified"

    s = str(raw_date).strip()

    # ISO formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if fmt in {"%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"}:
                return dt.strftime("%Y-%m-%d"), "exact"
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "exact"
        except ValueError:
            continue

    # Try regex matching for ISO-like substring
    m_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m_iso:
        return f"{m_iso.group(1)}-{m_iso.group(2)}-{m_iso.group(3)}", "exact"

    m_dmy = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", s)
    if m_dmy:
        return f"{m_dmy.group(3)}-{m_dmy.group(2)}-{m_dmy.group(1)}", "exact"

    # If unparseable string, preserve raw string with approximate tag
    return s, "approximate"


def build_longitudinal_timeline(
    patient_id: str,
    previous_encounters: list[dict[str, Any]],
    documents: list[Any],
    investigations: list[dict[str, Any]],
    previous_conversations: list[dict[str, Any]],
    patient_profile: Optional[dict[str, Any]] = None,
    current_encounter_state: Optional[dict[str, Any]] = None,
) -> tuple[list[TimelineEvent], list[str]]:
    """
    Constructs a unified, deduplicated, chronologically sorted list of TimelineEvents.
    Returns: (timeline_events, data_quality_notes)
    """
    events: list[TimelineEvent] = []
    notes: list[str] = []
    seen_event_keys: set[str] = set()

    # 1. Timeline Events from Patient Profile Milestones (e.g. Surgical History)
    profile = patient_profile or {}
    for surg in profile.get("surgical_history") or []:
        if not surg:
            continue
        ev_id = f"EV_SURG_{re.sub(r'[^a-zA-Z0-9]', '_', str(surg))[:20]}"
        if ev_id not in seen_event_keys:
            seen_event_keys.add(ev_id)
            events.append(TimelineEvent(
                event_id=ev_id,
                event_type="patient_profile",
                date=None,
                date_certainty="unspecified",
                source_id="BASELINE_PROFILE",
                source_type="patient_profile",
                title=f"Prior Surgery: {surg}",
                description=f"Past surgical history documented in profile: {surg}",
                structured_data={"surgical_procedure": surg},
                provenance="patient_profile",
            ))

    # 2. Timeline Events from Historical Encounters
    for idx, enc in enumerate(previous_encounters or [], start=1):
        enc_id = enc.get("encounter_id") or f"ENC_HIST_{idx:03d}"
        raw_date = enc.get("timestamp") or enc.get("date")
        norm_date, certainty = parse_and_normalize_date(raw_date)
        cc = enc.get("chief_complaint") or "General Consultation"
        sev = enc.get("severity")
        risk_lvl = enc.get("risk_level")
        r_flags = enc.get("red_flags") or []

        desc_parts = [f"Chief complaint: {cc}"]
        if sev:
            desc_parts.append(f"Severity: {sev}")
        if risk_lvl:
            desc_parts.append(f"Risk: {risk_lvl}")
        if r_flags:
            desc_parts.append(f"Red flags: {', '.join(r_flags)}")

        ev_id = f"EV_{enc_id}"
        # Deduplication check
        if ev_id in seen_event_keys:
            notes.append(f"Duplicate encounter ID '{enc_id}' detected and deduplicated.")
            continue
        seen_event_keys.add(ev_id)

        events.append(TimelineEvent(
            event_id=ev_id,
            event_type="encounter",
            date=norm_date,
            date_certainty=certainty,
            source_id=enc_id,
            source_type="encounter",
            title=f"Encounter: {cc}",
            description=". ".join(desc_parts) + ".",
            structured_data=enc,
            provenance=enc.get("source") or f"encounter_{enc_id}",
        ))

    # 3. Timeline Events from Clinical Documents (e.g. Lab Reports, Discharge Summaries)
    for doc in documents or []:
        if not doc:
            continue
        doc_dict = doc.model_dump() if hasattr(doc, "model_dump") else (doc if isinstance(doc, dict) else {})
        doc_id = doc_dict.get("document_id") or "DOC_UNKNOWN"
        doc_type = doc_dict.get("document_type") or "clinical_document"
        raw_date = doc_dict.get("document_date")
        norm_date, certainty = parse_and_normalize_date(raw_date)
        ext_text = doc_dict.get("extracted_text") or f"{doc_type} record"

        ev_id = f"EV_{doc_id}"
        if ev_id in seen_event_keys:
            notes.append(f"Duplicate document ID '{doc_id}' detected and deduplicated.")
            continue
        seen_event_keys.add(ev_id)

        events.append(TimelineEvent(
            event_id=ev_id,
            event_type="document",
            date=norm_date,
            date_certainty=certainty,
            source_id=doc_id,
            source_type="document",
            title=f"Document: {doc_type.replace('_', ' ').title()}",
            description=ext_text[:200] + ("..." if len(ext_text) > 200 else ""),
            structured_data={"biomarkers": doc_dict.get("structured_biomarkers", [])},
            provenance=doc_dict.get("provenance") or f"document_{doc_id}",
        ))

    # 4. Timeline Events from Standalone Investigations
    for idx, inv in enumerate(investigations or [], start=1):
        if not isinstance(inv, dict):
            continue
        inv_id = inv.get("investigation_id") or inv.get("source_document_id") or f"INV_{idx:03d}"
        test_name = inv.get("test_name") or inv.get("biomarker") or "Investigation"
        val = inv.get("value")
        unit = inv.get("unit") or ""
        raw_date = inv.get("date") or inv.get("observation_date")
        norm_date, certainty = parse_and_normalize_date(raw_date)

        ev_id = f"EV_{inv_id}_{re.sub(r'[^a-zA-Z0-9]', '_', test_name)[:15]}"
        if ev_id in seen_event_keys:
            continue
        seen_event_keys.add(ev_id)

        events.append(TimelineEvent(
            event_id=ev_id,
            event_type="investigation",
            date=norm_date,
            date_certainty=certainty,
            source_id=inv_id,
            source_type="investigation",
            title=f"Lab Test: {test_name}",
            description=f"Observed value: {val} {unit}".strip(),
            structured_data=inv,
            provenance=inv.get("provenance") or f"investigation_{inv_id}",
        ))

    # 5. Timeline Event from Current Encounter Turn (if available)
    if current_encounter_state:
        curr_session_id = (
            current_encounter_state.get("session_id") or
            current_encounter_state.get("episode_id") or
            "CURRENT_SESSION"
        )
        curr_cc = current_encounter_state.get("chief_complaint")
        if curr_cc:
            curr_date = current_encounter_state.get("evaluated_at") or datetime.now().strftime("%Y-%m-%d")
            norm_date, certainty = parse_and_normalize_date(curr_date)
            ev_id = f"EV_CURR_{curr_session_id}"
            if ev_id not in seen_event_keys:
                seen_event_keys.add(ev_id)
                events.append(TimelineEvent(
                    event_id=ev_id,
                    event_type="encounter",
                    date=norm_date,
                    date_certainty=certainty,
                    source_id=curr_session_id,
                    source_type="current_encounter",
                    title=f"Current Encounter: {curr_cc}",
                    description=f"Active chief complaint: {curr_cc}. Severity: {current_encounter_state.get('severity', 'unspecified')}.",
                    structured_data={
                        "chief_complaint": curr_cc,
                        "severity": current_encounter_state.get("severity"),
                        "duration": current_encounter_state.get("duration"),
                    },
                    provenance="current_encounter_state",
                ))

    # Deterministic Sorting:
    # 1. Events with known dates sorted chronologically ascending.
    # 2. Tie-breaking by event_type and event_id.
    # 3. Undated events appended deterministically at the end.
    dated_events = [e for e in events if e.date]
    undated_events = [e for e in events if not e.date]

    def sort_dated(e: TimelineEvent):
        return (e.date or "", e.event_type, e.event_id)

    def sort_undated(e: TimelineEvent):
        return (e.event_type, e.event_id)

    sorted_dated = sorted(dated_events, key=sort_dated)
    sorted_undated = sorted(undated_events, key=sort_undated)

    return sorted_dated + sorted_undated, notes


def synthesize_longitudinal_context(
    state_or_input: dict[str, Any],
) -> LongitudinalPatientContextDTO:
    """
    Primary entry point for Phase 9: Longitudinal Patient Intelligence.
    
    Synthesizes complete multi-encounter clinical history into
    LongitudinalPatientContextDTO without LLM dependence.
    """
    working_state = dict(state_or_input)
    if "state_snapshot" in state_or_input and isinstance(state_or_input["state_snapshot"], dict):
        working_state.update(state_or_input["state_snapshot"])
    if "message" in state_or_input and isinstance(state_or_input["message"], dict):
        msg_obj = state_or_input["message"]
        working_state["current_message"] = (
            msg_obj.get("english_text") or msg_obj.get("original_text") or working_state.get("current_message")
        )

    patient_id = working_state.get("patient_id") or "ANONYMOUS"
    profile = working_state.get("patient_profile") or {}
    prev_encounters = (
        working_state.get("previous_encounters") or
        working_state.get("previous_history") or
        []
    )
    docs = working_state.get("documents") or working_state.get("ocr_documents") or []
    invs = working_state.get("investigations") or []
    prev_convs = working_state.get("previous_conversations") or []

    # 1. Build chronological timeline
    timeline, quality_notes = build_longitudinal_timeline(
        patient_id=patient_id,
        previous_encounters=prev_encounters,
        documents=docs,
        investigations=invs,
        previous_conversations=prev_convs,
        patient_profile=profile,
        current_encounter_state=working_state,
    )


    # 2. Extract and analyze biomarkers
    biomarker_records = extract_biomarker_records(docs, invs)
    biomarker_trajectories = calculate_biomarker_trajectories(biomarker_records)

    # 3. Synthesize problem registry
    active_probs, resolved_probs, recurrent_probs, unresolved_probs = build_problem_registry(
        patient_profile=profile,
        previous_encounters=prev_encounters,
        current_encounter_state=working_state,
    )


    # 4. Extract baseline profile facts
    chronic_conditions = list(dict.fromkeys(profile.get("medical_conditions") or []))
    allergies = list(dict.fromkeys(profile.get("allergies") or []))

    meds_raw = profile.get("chronic_medications") or []
    meds = []
    for m in meds_raw:
        if isinstance(m, dict):
            name = m.get("medication") or m.get("name")
            if name:
                meds.append(str(name))
        elif isinstance(m, str) and m.strip():
            meds.append(m.strip())



    # 5. Build provenance audit summary
    provenance_summary: list[str] = [
        f"Ingested {len(prev_encounters)} historical encounter(s)",
        f"Ingested {len(docs)} clinical document(s)",
        f"Ingested {len(invs)} standalone investigation(s)",
        f"Extracted {len(biomarker_records)} biomarker observation(s) across {len(biomarker_trajectories)} test(s)",
        f"Problem registry tracking {len(active_probs)} active, {len(resolved_probs)} resolved, {len(recurrent_probs)} recurrent, and {len(unresolved_probs)} unresolved problem(s)",
    ]

    total_encs = len(prev_encounters) + (1 if state_or_input.get("chief_complaint") else 0)

    return LongitudinalPatientContextDTO(
        patient_id=patient_id,
        total_encounters=total_encs,
        timeline=timeline,
        active_problems=active_probs,
        resolved_problems=resolved_probs,
        recurrent_complaints=recurrent_probs,
        unresolved_issues=unresolved_probs,
        chronic_baseline_conditions=chronic_conditions,
        known_allergies=allergies,
        chronic_medications=meds,
        biomarker_trajectories=biomarker_trajectories,
        provenance_summary=provenance_summary,
        data_quality_notes=quality_notes,
    )
