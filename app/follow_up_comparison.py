"""
Phase 5: Deterministic Follow-up Comparison & Trajectory Classification Engine.

Compares patient encounters over time to detect:
- Severity changes (improved, worsened, unchanged)
- Risk changes (Phase 2B score and level comparison)
- New symptom emergence
- Explicit symptom resolution (Missing != Resolved)
- Phase 2A Red-Flag escalation enforcement
- Patient trajectory classification

100% DETERMINISTIC. ZERO-LLM. NO DIAGNOSES. NO PRESCRIPTIONS.
"""

import re
from typing import Any, Optional
from datetime import datetime

from app.follow_up_schema import (
    FieldComparison,
    RiskComparison,
    SymptomChangeSummary,
    PatientTrajectory,
    FollowUpMonitoringOutput,
    ChangeType,
    RiskTrend,
    TrajectoryType,
)


SEVERITY_SCALE = {
    "none": 0,
    "resolved": 0,
    "gone": 0,
    "absent": 0,
    "0": 0,
    "mild": 1,
    "slight": 1,
    "minimal": 1,
    "low": 1,
    "1": 1,
    "2": 1,
    "3": 1,
    "moderate": 2,
    "medium": 2,
    "average": 2,
    "4": 2,
    "5": 2,
    "6": 2,
    "severe": 3,
    "very severe": 3,
    "high": 3,
    "bad": 3,
    "intense": 3,
    "7": 3,
    "8": 3,
    "critical": 4,
    "unbearable": 4,
    "extreme": 4,
    "extremely severe": 4,
    "worst": 4,
    "emergency": 4,
    "9": 4,
    "10": 4,
}

RISK_LEVEL_SCALE = {
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "URGENT": 4,
}

RESOLUTION_PATTERNS = [
    r"\b(?:resolved|stopped|subsided|gone|cured|no longer|no more|not having)\s+([a-zA-Z\s]+)",
    r"\b([a-zA-Z\s]+)\s+(?:has\s+|is\s+|have\s+)?(?:resolved|stopped|subsided|gone away|cleared up|improved completely)\b",
    r"\bno\s+more\s+([a-zA-Z\s]+)",
    r"\bnot\s+experiencing\s+([a-zA-Z\s]+)",
]


def _normalize_symptom(s: str) -> str:
    """Normalize symptom string for deterministic comparison."""
    if not s:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", str(s).lower()).strip()
    return " ".join(cleaned.split())


def _parse_severity_rank(sev: Optional[str]) -> Optional[int]:
    """Parse severity string to numeric scale rank."""
    if sev is None:
        return None
    normalized = str(sev).lower().strip()
    if normalized in SEVERITY_SCALE:
        return SEVERITY_SCALE[normalized]
    for key, rank in SEVERITY_SCALE.items():
        if key in normalized:
            return rank
    return None


def compare_severity(prev_sev: Optional[str], curr_sev: Optional[str]) -> tuple[ChangeType, str]:
    """
    Deterministically compare severity strings.
    Returns (ChangeType, evidence_string).
    """
    if prev_sev is None and curr_sev is None:
        return "UNCHANGED", "Severity was not recorded in either encounter."
    if prev_sev is None or curr_sev is None:
        return "INSUFFICIENT_DATA", f"Incomplete severity data (previous: '{prev_sev}', current: '{curr_sev}')."

    prev_rank = _parse_severity_rank(prev_sev)
    curr_rank = _parse_severity_rank(curr_sev)

    if prev_rank is None or curr_rank is None:
        if str(prev_sev).lower().strip() == str(curr_sev).lower().strip():
            return "UNCHANGED", f"Severity remained unchanged ('{curr_sev}')."
        return "INSUFFICIENT_DATA", f"Unquantifiable severity values (previous: '{prev_sev}', current: '{curr_sev}')."

    if curr_rank < prev_rank:
        return "IMPROVED", f"Symptom severity decreased from '{prev_sev}' (rank {prev_rank}) to '{curr_sev}' (rank {curr_rank})."
    elif curr_rank > prev_rank:
        return "WORSENED", f"Symptom severity increased from '{prev_sev}' (rank {prev_rank}) to '{curr_sev}' (rank {curr_rank})."
    else:
        return "UNCHANGED", f"Symptom severity remained constant at '{curr_sev}'."


def detect_explicit_resolutions(current_text: Optional[str], previous_symptoms: list[str]) -> list[str]:
    """
    Detects explicitly reported symptom resolutions from text.
    MANDATORY RULE: Missing != Resolved.
    Only explicit resolution statements can mark a symptom as resolved.
    """
    if not current_text or not previous_symptoms:
        return []

    text_lower = current_text.lower()
    resolved = []

    for prev_sym in previous_symptoms:
        norm_sym = _normalize_symptom(prev_sym)
        if not norm_sym:
            continue

        # Check explicit negation / resolution patterns
        explicit_phrases = [
            f"{norm_sym} stopped",
            f"{norm_sym} has stopped",
            f"{norm_sym} is gone",
            f"{norm_sym} resolved",
            f"{norm_sym} has resolved",
            f"no longer {norm_sym}",
            f"no longer have {norm_sym}",
            f"no longer having {norm_sym}",
            f"not having {norm_sym}",
            f"no more {norm_sym}",
            f"free of {norm_sym}",
            f"{norm_sym} completely gone",
            f"{norm_sym} went away",
        ]

        if any(phrase in text_lower for phrase in explicit_phrases):
            resolved.append(prev_sym)

    return resolved


def compare_symptoms(
    previous_symptoms: list[str],
    current_symptoms: list[str],
    explicitly_resolved: Optional[list[str]] = None,
) -> SymptomChangeSummary:
    """
    Compute structured set delta of symptoms.
    Adheres strictly to the rule: Missing != Resolved.
    """
    norm_prev_map = {_normalize_symptom(s): s for s in previous_symptoms if s}
    norm_curr_map = {_normalize_symptom(s): s for s in current_symptoms if s}

    prev_set = set(norm_prev_map.keys())
    curr_set = set(norm_curr_map.keys())

    explicit_set = {_normalize_symptom(s) for s in (explicitly_resolved or []) if s}

    # Persisting = present in both
    persisting_keys = prev_set.intersection(curr_set)
    persisting = [norm_curr_map[k] for k in persisting_keys]

    # New = in current but not in previous
    new_keys = curr_set - prev_set
    new_symptoms = [norm_curr_map[k] for k in new_keys]

    # Resolved = in previous AND explicitly confirmed resolved
    resolved_keys = prev_set.intersection(explicit_set)
    resolved_symptoms = [norm_prev_map[k] for k in resolved_keys]

    # Unmentioned = in previous, NOT in current, and NOT explicitly resolved
    unmentioned_keys = prev_set - curr_set - resolved_keys
    unmentioned_symptoms = [norm_prev_map[k] for k in unmentioned_keys]

    return SymptomChangeSummary(
        new_symptoms=new_symptoms,
        resolved_symptoms=resolved_symptoms,
        persisting_symptoms=persisting,
        unmentioned_symptoms=unmentioned_symptoms,
    )


def compare_risk(
    previous_risk: Optional[dict[str, Any]],
    current_risk: Optional[dict[str, Any]],
) -> RiskComparison:
    """
    Compare Phase 2B risk assessment outputs across encounters.
    Does NOT recalculate or modify Phase 2B scoring logic.
    """
    if not previous_risk and not current_risk:
        return RiskComparison(
            previous_risk_level=None,
            current_risk_level=None,
            previous_risk_score=None,
            current_risk_score=None,
            risk_trend="unknown",
            contributing_changes=["No risk assessment data available."],
        )

    prev_lvl = previous_risk.get("risk_level") if previous_risk else None
    prev_score = previous_risk.get("risk_score") if previous_risk else None
    curr_lvl = current_risk.get("risk_level") if current_risk else None
    curr_score = current_risk.get("risk_score") if current_risk else None

    if prev_score is None or curr_score is None:
        return RiskComparison(
            previous_risk_level=prev_lvl,
            current_risk_level=curr_lvl,
            previous_risk_score=prev_score,
            current_risk_score=curr_score,
            risk_trend="unknown",
            contributing_changes=["Risk score unavailable in one or both encounters."],
        )

    prev_rank = RISK_LEVEL_SCALE.get(str(prev_lvl).upper(), 0)
    curr_rank = RISK_LEVEL_SCALE.get(str(curr_lvl).upper(), 0)

    changes: list[str] = []

    if curr_score > prev_score or curr_rank > prev_rank:
        trend: RiskTrend = "increased"
        changes.append(f"Risk score increased from {prev_score} to {curr_score}.")
        if curr_lvl != prev_lvl:
            changes.append(f"Risk level shifted upward from {prev_lvl} to {curr_lvl}.")
    elif curr_score < prev_score and curr_rank <= prev_rank:
        trend = "decreased"
        changes.append(f"Risk score decreased from {prev_score} to {curr_score}.")
        if curr_lvl != prev_lvl:
            changes.append(f"Risk level shifted downward from {prev_lvl} to {curr_lvl}.")
    elif curr_score == prev_score and curr_rank == prev_rank:
        trend = "unchanged"
        changes.append(f"Risk level ({curr_lvl}) and risk score ({curr_score}) remained unchanged.")
    else:
        trend = "unknown"
        changes.append(f"Score shifted from {prev_score} to {curr_score}, level from {prev_lvl} to {curr_lvl}.")

    return RiskComparison(
        previous_risk_level=prev_lvl,
        current_risk_level=curr_lvl,
        previous_risk_score=prev_score,
        current_risk_score=curr_score,
        risk_trend=trend,
        contributing_changes=changes,
    )


def compare_all_fields(
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    symptom_summary: SymptomChangeSummary,
) -> list[FieldComparison]:
    """
    Compare structured clinical fields between encounters.
    """
    comparisons: list[FieldComparison] = []

    # 1. Chief Complaint
    prev_cc = previous_state.get("chief_complaint")
    curr_cc = current_state.get("chief_complaint")
    if prev_cc and curr_cc:
        if _normalize_symptom(prev_cc) == _normalize_symptom(curr_cc):
            comparisons.append(FieldComparison(
                field_name="chief_complaint",
                previous_value=prev_cc,
                current_value=curr_cc,
                change_type="UNCHANGED",
                evidence=f"Chief complaint remained constant: '{curr_cc}'."
            ))
        else:
            comparisons.append(FieldComparison(
                field_name="chief_complaint",
                previous_value=prev_cc,
                current_value=curr_cc,
                change_type="NEW",
                evidence=f"Chief complaint shifted from '{prev_cc}' to '{curr_cc}'."
            ))
    elif curr_cc:
        comparisons.append(FieldComparison(
            field_name="chief_complaint",
            previous_value=prev_cc,
            current_value=curr_cc,
            change_type="NEW",
            evidence=f"Chief complaint recorded as '{curr_cc}'."
        ))

    # 2. Severity
    prev_sev = previous_state.get("severity")
    curr_sev = current_state.get("severity")
    sev_change, sev_ev = compare_severity(prev_sev, curr_sev)
    comparisons.append(FieldComparison(
        field_name="severity",
        previous_value=prev_sev,
        current_value=curr_sev,
        change_type=sev_change,
        evidence=sev_ev
    ))

    # 3. Duration
    prev_dur = previous_state.get("duration")
    curr_dur = current_state.get("duration")
    if prev_dur and curr_dur:
        if str(prev_dur).lower().strip() == str(curr_dur).lower().strip():
            comparisons.append(FieldComparison(
                field_name="duration",
                previous_value=prev_dur,
                current_value=curr_dur,
                change_type="UNCHANGED",
                evidence=f"Reported duration remained '{curr_dur}'."
            ))
        else:
            comparisons.append(FieldComparison(
                field_name="duration",
                previous_value=prev_dur,
                current_value=curr_dur,
                change_type="NEW",
                evidence=f"Duration changed from '{prev_dur}' to '{curr_dur}'."
            ))

    # 4. Care Pathway
    prev_case = previous_state.get("clinical_case") or {}
    curr_case = current_state.get("clinical_case") or {}
    prev_pw = prev_case.get("care_pathway_status")
    curr_pw = curr_case.get("care_pathway_status")
    if prev_pw and curr_pw:
        if prev_pw == curr_pw:
            comparisons.append(FieldComparison(
                field_name="care_pathway",
                previous_value=prev_pw,
                current_value=curr_pw,
                change_type="UNCHANGED",
                evidence=f"Care pathway remains '{curr_pw}'."
            ))
        else:
            c_type: ChangeType = "WORSENED" if curr_pw in ["emergency", "urgent"] and prev_pw in ["routine", "follow_up"] else "IMPROVED" if curr_pw == "routine" and prev_pw in ["emergency", "urgent"] else "NEW"
            comparisons.append(FieldComparison(
                field_name="care_pathway",
                previous_value=prev_pw,
                current_value=curr_pw,
                change_type=c_type,
                evidence=f"Care pathway shifted from '{prev_pw}' to '{curr_pw}'."
            ))

    # 5. Symptoms summary field
    if symptom_summary.new_symptoms:
        comparisons.append(FieldComparison(
            field_name="associated_symptoms",
            previous_value=previous_state.get("associated_symptoms"),
            current_value=current_state.get("associated_symptoms"),
            change_type="NEW",
            evidence=f"New symptom(s) detected: {', '.join(symptom_summary.new_symptoms)}."
        ))
    elif symptom_summary.resolved_symptoms:
        comparisons.append(FieldComparison(
            field_name="associated_symptoms",
            previous_value=previous_state.get("associated_symptoms"),
            current_value=current_state.get("associated_symptoms"),
            change_type="RESOLVED",
            evidence=f"Explicitly resolved symptom(s): {', '.join(symptom_summary.resolved_symptoms)}."
        ))
    else:
        comparisons.append(FieldComparison(
            field_name="associated_symptoms",
            previous_value=previous_state.get("associated_symptoms"),
            current_value=current_state.get("associated_symptoms"),
            change_type="UNCHANGED",
            evidence="No new or resolved associated symptoms."
        ))

    return comparisons


def classify_patient_trajectory(
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    risk_comparison: RiskComparison,
    symptom_summary: SymptomChangeSummary,
    severity_change: ChangeType,
) -> PatientTrajectory:
    """
    Deterministic trajectory classification hierarchy:
    1. Phase 2A Red Flag Escalation Override (Authoritative)
    2. Significant Risk Increase (Phase 2B)
    3. New High-Risk / Red Flag Symptoms
    4. New Symptoms Emergence (new_risk_signal)
    5. Clinical Worsening (severity worse, risk increased)
    6. Clinical Improvement (severity better, risk decreased, symptoms resolved)
    7. Stable / Unchanged
    8. Insufficient Information
    """
    evidence: list[str] = []

    # -------------------------------------------------------------
    # 1. PHASE 2A AUTHORITATIVE RED-FLAG OVERRIDE
    # -------------------------------------------------------------
    curr_immediate = current_state.get("immediate_attention_required", False)
    curr_red_flags = current_state.get("red_flags", [])
    curr_rf_status = current_state.get("red_flag_status")

    if curr_immediate or curr_rf_status == "red_flags_detected" or curr_red_flags:
        rf_list_str = ", ".join(curr_red_flags) if curr_red_flags else "unspecified emergency indicator"
        evidence.append(f"Phase 2A safety layer active: immediate attention required (Red flags: {rf_list_str}).")
        if risk_comparison.contributing_changes:
            evidence.extend(risk_comparison.contributing_changes)
        return PatientTrajectory(
            trajectory="escalation_required",
            confidence="high",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 2. DATA COMPLETENESS / VAGUE STATEMENT CHECK
    # -------------------------------------------------------------
    # Check if current state has insufficient structured data to compare
    curr_cc = current_state.get("chief_complaint")
    curr_sev = current_state.get("severity")
    curr_dur = current_state.get("duration")
    has_structured_fields = bool(curr_cc or curr_sev or curr_dur or current_state.get("associated_symptoms"))

    if not has_structured_fields or (curr_sev is None and not symptom_summary.resolved_symptoms and not symptom_summary.new_symptoms and risk_comparison.risk_trend == "unknown"):
        evidence.append("Insufficient structured follow-up data available to establish clinical trajectory.")
        return PatientTrajectory(
            trajectory="insufficient_information",
            confidence="low",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 3. NEW SYMPTOM / RISK SIGNAL CHECK
    # -------------------------------------------------------------
    if symptom_summary.new_symptoms:
        evidence.append(f"New symptom(s) identified: {', '.join(symptom_summary.new_symptoms)}.")
        if severity_change == "WORSENED" or risk_comparison.risk_trend == "increased":
            evidence.extend(risk_comparison.contributing_changes)
            return PatientTrajectory(
                trajectory="worsening",
                confidence="high",
                evidence=evidence,
            )
        return PatientTrajectory(
            trajectory="new_risk_signal",
            confidence="high",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 4. WORSENING CHECK
    # -------------------------------------------------------------
    if severity_change == "WORSENED" or risk_comparison.risk_trend == "increased":
        if severity_change == "WORSENED":
            prev_s = previous_state.get("severity")
            curr_s = current_state.get("severity")
            evidence.append(f"Symptom severity worsened from '{prev_s}' to '{curr_s}'.")
        if risk_comparison.contributing_changes:
            evidence.extend(risk_comparison.contributing_changes)
        return PatientTrajectory(
            trajectory="worsening",
            confidence="high",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 5. IMPROVING CHECK
    # -------------------------------------------------------------
    is_improving = False
    if severity_change == "IMPROVED":
        prev_s = previous_state.get("severity")
        curr_s = current_state.get("severity")
        evidence.append(f"Symptom severity improved from '{prev_s}' to '{curr_s}'.")
        is_improving = True

    if symptom_summary.resolved_symptoms:
        evidence.append(f"Explicitly confirmed resolution of: {', '.join(symptom_summary.resolved_symptoms)}.")
        is_improving = True

    if risk_comparison.risk_trend == "decreased":
        evidence.extend(risk_comparison.contributing_changes)
        is_improving = True

    if is_improving and risk_comparison.risk_trend != "increased" and not symptom_summary.new_symptoms:
        return PatientTrajectory(
            trajectory="improving",
            confidence="high",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 6. STABLE / UNCHANGED CHECK
    # -------------------------------------------------------------
    if severity_change == "UNCHANGED" and risk_comparison.risk_trend in ["unchanged", "unknown"] and not symptom_summary.new_symptoms:
        evidence.append("Symptom severity, risk level, and clinical presentation remained stable across encounters.")
        return PatientTrajectory(
            trajectory="stable",
            confidence="high",
            evidence=evidence,
        )

    # -------------------------------------------------------------
    # 7. DEFAULT / INSUFFICIENT DATA
    # -------------------------------------------------------------
    evidence.append("Clinical data is inconclusive for definitive trajectory classification.")
    return PatientTrajectory(
        trajectory="insufficient_information",
        confidence="low",
        evidence=evidence,
    )


def determine_monitoring_action(trajectory: TrajectoryType, care_pathway: str, immediate_attention: bool) -> str:
    """
    Deterministically map trajectory and safety status to operational next action.
    Non-diagnostic and non-prescriptive.
    """
    if immediate_attention or trajectory == "escalation_required":
        return "Immediate emergency clinical evaluation and escalation required."
    elif trajectory == "worsening":
        return "Clinical reassessment indicated due to symptom progression or increased risk."
    elif trajectory == "new_risk_signal":
        return "Physician evaluation advised to assess newly emerged symptoms."
    elif trajectory == "improving":
        return "Continue routine recovery monitoring; seek re-evaluation if symptoms recur or worsen."
    elif trajectory == "stable":
        return "Continue routine monitoring and follow care plan as advised by healthcare provider."
    elif trajectory == "initial_encounter":
        return "Initial encounter recorded. Baseline established for future longitudinal monitoring."
    else:
        return "Clinical assessment recommended to gather structured follow-up information."


def generate_monitoring_explanation(
    trajectory: PatientTrajectory,
    risk_comparison: RiskComparison,
    symptom_summary: SymptomChangeSummary,
    severity_change: ChangeType,
) -> str:
    """
    Generate a clear, explainable, factual narrative summary of the monitoring evaluation.
    """
    traj = trajectory.trajectory
    if traj == "initial_encounter":
        return "Initial clinical baseline encounter recorded. No prior encounter records available for comparison."

    parts = [f"Patient trajectory classified as '{traj}'."]

    if trajectory.evidence:
        parts.append("Key findings: " + "; ".join(trajectory.evidence))

    return " ".join(parts)


def compare_clinical_states(
    previous_state: Optional[dict[str, Any]],
    current_state: dict[str, Any],
    current_message: Optional[str] = None,
) -> FollowUpMonitoringOutput:
    """
    Main entry point for Phase 5 comparison engine.
    Compares previous encounter against current encounter deterministically.
    """
    patient_id = current_state.get("patient_id", "UNKNOWN")
    session_id = current_state.get("session_id", "UNKNOWN")
    now_iso = datetime.now().isoformat()
    warnings: list[str] = []

    # -------------------------------------------------------------
    # 1. INITIAL ENCOUNTER (NO PREVIOUS STATE)
    # -------------------------------------------------------------
    if not previous_state:
        trajectory = PatientTrajectory(
            trajectory="initial_encounter",
            confidence="high",
            evidence=["First recorded clinical encounter. Baseline established."],
        )
        risk_comp = RiskComparison(
            previous_risk_level=None,
            current_risk_level=current_state.get("risk_level"),
            previous_risk_score=None,
            current_risk_score=current_state.get("risk_score"),
            risk_trend="unknown",
            contributing_changes=["Initial encounter baseline."],
        )
        symptom_summary = SymptomChangeSummary(
            new_symptoms=current_state.get("associated_symptoms", []),
            resolved_symptoms=[],
            persisting_symptoms=[],
            unmentioned_symptoms=[],
        )
        return FollowUpMonitoringOutput(
            monitoring_status="initial_encounter",
            patient_id=patient_id,
            session_id=session_id,
            previous_session_id=None,
            evaluated_at=now_iso,
            trajectory=trajectory,
            risk_comparison=risk_comp,
            symptom_changes=symptom_summary,
            field_comparisons=[],
            next_monitoring_action=determine_monitoring_action("initial_encounter", "routine", False),
            monitoring_explanation="Initial clinical baseline encounter recorded. No prior encounter records available for comparison.",
            validation_warnings=["No previous encounter history."],
        )

    # -------------------------------------------------------------
    # 2. EXTRACT PREVIOUS AND CURRENT SIGNALS
    # -------------------------------------------------------------
    prev_session_id = previous_state.get("session_id")
    prev_symptoms = previous_state.get("associated_symptoms") or []
    if previous_state.get("chief_complaint") and previous_state.get("chief_complaint") not in prev_symptoms:
        prev_symptoms = [previous_state.get("chief_complaint")] + prev_symptoms

    curr_symptoms = current_state.get("associated_symptoms") or []
    if current_state.get("chief_complaint") and current_state.get("chief_complaint") not in curr_symptoms:
        curr_symptoms = [current_state.get("chief_complaint")] + curr_symptoms

    # Check explicit resolution from current text / state
    explicit_text = current_message or current_state.get("current_message", "")
    explicit_resolutions = detect_explicit_resolutions(explicit_text, prev_symptoms)

    # If state has explicitly tracked resolved signals, merge them
    if current_state.get("resolved_signals"):
        explicit_resolutions = list(set(explicit_resolutions + current_state.get("resolved_signals", [])))

    # Compute symptom delta
    symptom_summary = compare_symptoms(prev_symptoms, curr_symptoms, explicit_resolutions)

    # Compute severity comparison
    prev_sev = previous_state.get("severity")
    curr_sev = current_state.get("severity")
    sev_change, sev_evidence = compare_severity(prev_sev, curr_sev)

    # Compute risk comparison
    prev_risk_dict = {
        "risk_level": previous_state.get("risk_level"),
        "risk_score": previous_state.get("risk_score"),
    }
    curr_risk_dict = {
        "risk_level": current_state.get("risk_level"),
        "risk_score": current_state.get("risk_score"),
    }
    risk_comp = compare_risk(prev_risk_dict, curr_risk_dict)

    # Field by field comparison
    field_comps = compare_all_fields(previous_state, current_state, symptom_summary)

    # Classify trajectory
    trajectory = classify_patient_trajectory(
        previous_state=previous_state,
        current_state=current_state,
        risk_comparison=risk_comp,
        symptom_summary=symptom_summary,
        severity_change=sev_change,
    )

    # Determine next monitoring action
    curr_case = current_state.get("clinical_case") or {}
    care_pathway = curr_case.get("care_pathway_status", "routine")
    immediate_attention = current_state.get("immediate_attention_required", False)
    next_action = determine_monitoring_action(trajectory.trajectory, care_pathway, immediate_attention)

    # Generate explainable narrative
    explanation = generate_monitoring_explanation(trajectory, risk_comp, symptom_summary, sev_change)

    return FollowUpMonitoringOutput(
        monitoring_status=trajectory.trajectory,
        patient_id=patient_id,
        session_id=session_id,
        previous_session_id=prev_session_id,
        evaluated_at=now_iso,
        trajectory=trajectory,
        risk_comparison=risk_comp,
        symptom_changes=symptom_summary,
        field_comparisons=field_comps,
        next_monitoring_action=next_action,
        monitoring_explanation=explanation,
        validation_warnings=warnings,
    )
