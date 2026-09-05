"""
Phase 10: Advanced Risk Convergence Engine.

Deterministically synthesizes longitudinal clinical context (Phase 9) with
current-encounter risk convergence (Phase 2B) and authoritative red-flag safety (Phase 2A).

CRITICAL SAFETY INVARIANTS:
1. Phase 2A Red-Flag Safety retains absolute emergency override authority.
2. Phase 2B Current Risk output is preserved immutably under `current_risk`.
3. Composite risk may escalate above Phase 2B risk level, but NEVER downgrades below it.
4. ZERO invented clinical thresholds for biomarkers; records observational trajectory signals only.
5. ZERO LLM dependencies. 100% Deterministic rule engine.
6. ZERO diagnosis, ZERO treatment, ZERO prescriptions.
"""

from typing import Any, Optional
from datetime import datetime

from app.advanced_risk_schema import (
    LongitudinalRiskSignal,
    LongitudinalRiskAssessmentDTO,
    CompositeRiskOutputDTO,
    LongitudinalRiskLevel,
    CompositeRiskLevel,
    EffectiveCarePathway,
    RiskEscalationStatus,
    TemporalPersistenceIndex,
    DataCompletenessStatus,
)
from app.longitudinal_schema import (
    LongitudinalPatientContextDTO,
    ProblemRecord,
    BiomarkerTrajectory,
)
from app.longitudinal_timeline import synthesize_longitudinal_context
from app.problem_registry import normalize_problem_label


# Explicitly governed cross-modal concordance relationships
# Only triggered when both the symptom and biomarker trajectory match exactly
GOVERNED_CROSS_MODAL_CONCORDANCE: list[dict[str, Any]] = [
    {
        "symptom_key": "fatigue",
        "biomarker_key": "hemoglobin",
        "direction": "downward",
        "rationale": "Active reported fatigue coincides with an observed downward hemoglobin trajectory.",
    },
    {
        "symptom_key": "headache",
        "biomarker_key": "blood_pressure_systolic",
        "direction": "upward",
        "rationale": "Active reported headache coincides with an observed upward systolic blood pressure trajectory.",
    },
    {
        "symptom_key": "joint_pain",
        "biomarker_key": "uric_acid",
        "direction": "upward",
        "rationale": "Active reported joint pain coincides with an observed upward uric acid trajectory.",
    },
]

RISK_LEVEL_ORDER: dict[str, int] = {
    "INCOMPLETE": 0,
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "URGENT": 4,
}


def _dedupe_strings(items: list[Optional[str]]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item is None:
            continue
        cleaned = str(item).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def evaluate_longitudinal_risk(
    state_or_input: dict[str, Any],
    current_risk_assessment: dict[str, Any],
    longitudinal_context: Optional[LongitudinalPatientContextDTO] = None,
) -> LongitudinalRiskAssessmentDTO:
    """
    Evaluates multi-encounter longitudinal risk signals across problem registries,
    historical encounters, and biomarker observations without altering Phase 2B.
    """
    # 1. Obtain or synthesize LongitudinalPatientContextDTO
    long_ctx = longitudinal_context
    if long_ctx is None:
        long_ctx = synthesize_longitudinal_context(state_or_input)

    signals: list[LongitudinalRiskSignal] = []
    contributing_factors: list[str] = []
    evidence_list: list[str] = []

    active_cc = state_or_input.get("chief_complaint")
    active_norm_cc, _ = normalize_problem_label(str(active_cc)) if active_cc else ("", "")
    
    total_encounters = long_ctx.total_encounters
    has_history = total_encounters > 1 or len(long_ctx.timeline) > 1

    if not has_history:
        # Zero longitudinal history baseline
        return LongitudinalRiskAssessmentDTO(
            longitudinal_risk_score=0.0,
            longitudinal_risk_level="LOW",
            risk_escalation_status="insufficient_longitudinal_data",
            temporal_persistence_index="acute_isolated",
            risk_signals=[],
            contributing_longitudinal_factors=["single_isolated_encounter_no_history"],
            longitudinal_evidence=["No prior encounter or biomarker history documented."],
            reasoning="Single encounter baseline; insufficient longitudinal history for longitudinal risk accumulation.",
            data_completeness="minimal",
        )

    # -------------------------------------------------------------
    # RULE 1: Recurrent Complaint Escalation Signal
    # -------------------------------------------------------------
    matched_recurrent: Optional[ProblemRecord] = None
    for p in long_ctx.recurrent_complaints:
        if p.normalized_label == active_norm_cc:
            matched_recurrent = p
            break

    if matched_recurrent:
        weight = 15.0
        sev = "high" if matched_recurrent.episode_count >= 3 else "moderate"
        ev = [
            f"Recurrent complaint '{matched_recurrent.label}' documented across {matched_recurrent.episode_count} episodes in encounters: {', '.join(matched_recurrent.encounter_ids)}"
        ]
        rat = f"Recurrent presentation of '{matched_recurrent.label}' across multiple non-consecutive encounters indicates episodic re-emergence requiring heightened monitoring."
        signals.append(LongitudinalRiskSignal(
            signal_id="recurrent_complaint_signal",
            category="recurrence",
            severity=sev,
            weight=weight,
            evidence=ev,
            rationale=rat,
            provenance_sources=matched_recurrent.encounter_ids,
        ))
        contributing_factors.append(f"recurrent_{matched_recurrent.normalized_label}")
        evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 2: Temporal Persistence Signal
    # -------------------------------------------------------------
    duration_text = str(state_or_input.get("duration") or "").lower()
    is_persistent_duration = any(
        kw in duration_text for kw in ["week", "weeks", "month", "months", "year", "years"]
    )
    if is_persistent_duration and active_cc:
        weight = 12.0
        ev = [f"Active complaint '{active_cc}' has persistent documented duration: '{state_or_input.get('duration')}'"]
        rat = f"Prolonged persistence of '{active_cc}' over extended duration adds chronic background concern."
        signals.append(LongitudinalRiskSignal(
            signal_id="persistent_unresolved_problem_signal",
            category="persistence",
            severity="moderate",
            weight=weight,
            evidence=ev,
            rationale=rat,
            provenance_sources=["current_encounter_duration"],
        ))
        contributing_factors.append("persistent_symptom_duration")
        evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 3: Multi-Encounter Historical Risk Escalation Signal
    # -------------------------------------------------------------
    prev_encs = state_or_input.get("previous_encounters") or state_or_input.get("previous_history") or []
    dated_encs = []
    for e in prev_encs:
        if isinstance(e, dict):
            d = e.get("timestamp") or e.get("date")
            lvl = e.get("risk_level")
            if d and lvl:
                dated_encs.append((str(d), str(lvl).upper(), e.get("encounter_id", "ENC_HIST")))

    if len(dated_encs) >= 2:
        sorted_dated = sorted(dated_encs, key=lambda x: x[0])
        levels = [x[1] for x in sorted_dated]
        is_strictly_escalating = all(
            RISK_LEVEL_ORDER.get(levels[i], 0) <= RISK_LEVEL_ORDER.get(levels[i + 1], 0)
            for i in range(len(levels) - 1)
        ) and (RISK_LEVEL_ORDER.get(levels[-1], 0) > RISK_LEVEL_ORDER.get(levels[0], 0))

        if is_strictly_escalating:
            weight = 15.0
            ev_summary = " -> ".join(f"{x[2]}({x[1]})" for x in sorted_dated)
            ev = [f"Historical encounter risk strictly escalated over time: {ev_summary}"]
            rat = "Upward trajectory in historical encounter risk levels indicates systemic clinical escalation across encounters."
            signals.append(LongitudinalRiskSignal(
                signal_id="historical_risk_escalation_signal",
                category="historical_escalation",
                severity="high",
                weight=weight,
                evidence=ev,
                rationale=rat,
                provenance_sources=[x[2] for x in sorted_dated],
            ))
            contributing_factors.append("historical_risk_escalation")
            evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 4: Repeated Moderate Encounters Accumulation
    # -------------------------------------------------------------
    mod_enc_ids = [
        e.get("encounter_id", f"ENC_{i}")
        for i, e in enumerate(prev_encs, start=1)
        if isinstance(e, dict) and str(e.get("risk_level", "")).upper() == "MODERATE"
    ]
    if len(mod_enc_ids) >= 3:
        weight = 10.0
        ev = [f"Patient has {len(mod_enc_ids)} prior moderate-risk encounters: {', '.join(mod_enc_ids)}"]
        rat = "Recurrent moderate-risk episodes indicate persistent vulnerability and repeated clinical encounters."
        signals.append(LongitudinalRiskSignal(
            signal_id="repeated_moderate_episodes_signal",
            category="repeated_moderate",
            severity="moderate",
            weight=weight,
            evidence=ev,
            rationale=rat,
            provenance_sources=mod_enc_ids,
        ))
        contributing_factors.append("repeated_moderate_episodes")
        evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 5: Multimorbid Baseline Burden Signal
    # -------------------------------------------------------------
    chronic_conds = long_ctx.chronic_baseline_conditions
    unres_issues = long_ctx.unresolved_issues
    if len(chronic_conds) >= 2 and len(unres_issues) >= 2:
        weight = 10.0
        ev = [
            f"Chronic conditions ({len(chronic_conds)}): {', '.join(chronic_conds)}; Unresolved historical issues ({len(unres_issues)}): {', '.join(p.label for p in unres_issues)}"
        ]
        rat = "Multiple coexisting chronic medical conditions combined with unresolved past complaints increase longitudinal clinical complexity."
        signals.append(LongitudinalRiskSignal(
            signal_id="unresolved_multimorbid_burden_signal",
            category="multimorbid_burden",
            severity="moderate",
            weight=weight,
            evidence=ev,
            rationale=rat,
            provenance_sources=["patient_profile", "problem_registry"],
        ))
        contributing_factors.append("multimorbid_unresolved_burden")
        evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 6: Observational Biomarker Trajectory Signal
    # (Strictly observational without arbitrary clinical thresholds)
    # -------------------------------------------------------------
    for traj in long_ctx.biomarker_trajectories:
        if traj.observation_count >= 2 and not traj.unit_mismatch and traj.trajectory in {"increasing", "decreasing", "fluctuating"}:
            weight = 5.0
            ev = [
                f"Observed mathematical {traj.trajectory} trajectory for '{traj.test_name}' ({traj.earliest_observation.value} to {traj.latest_observation.value} {traj.unit or ''}, delta={traj.absolute_delta}) across {traj.observation_count} observations."
            ]
            rat = f"A mathematical trajectory change in '{traj.test_name}' was observed. Clinical significance is not established and requires physician review."
            signals.append(LongitudinalRiskSignal(
                signal_id="biomarker_trajectory_change_observed",
                category="biomarker_observation",
                severity="informational",
                weight=weight,
                evidence=ev,
                rationale=rat,
                provenance_sources=traj.provenance_sources,
            ))
            contributing_factors.append(f"biomarker_trajectory_{traj.normalized_name}")
            evidence_list.extend(ev)

    # -------------------------------------------------------------
    # RULE 7: Governed Cross-Modal Concordance Signal
    # (Conservative; triggers ONLY if explicitly defined in GOVERNED_CROSS_MODAL_CONCORDANCE)
    # -------------------------------------------------------------
    for entry in GOVERNED_CROSS_MODAL_CONCORDANCE:
        req_symp = entry["symptom_key"]
        req_bm = entry["biomarker_key"]
        req_dir = entry["direction"]

        # Check if symptom is active
        symp_match = (
            active_norm_cc == req_symp or
            any(normalize_problem_label(str(s))[0] == req_symp for s in (state_or_input.get("associated_symptoms") or []))
        )
        if not symp_match:
            continue

        # Check if matching biomarker has concordant trajectory
        for traj in long_ctx.biomarker_trajectories:
            if traj.normalized_name == req_bm and not traj.unit_mismatch and traj.direction == req_dir:
                weight = 12.0
                ev = [
                    f"Concordance observed: active symptom '{req_symp}' aligns with governed '{traj.test_name}' {req_dir} trajectory."
                ]
                rat = entry["rationale"]
                signals.append(LongitudinalRiskSignal(
                    signal_id="governed_cross_modal_concordance_signal",
                    category="cross_modal_concordance",
                    severity="moderate",
                    weight=weight,
                    evidence=ev,
                    rationale=rat,
                    provenance_sources=traj.provenance_sources + [f"symptom_{req_symp}"],
                ))
                contributing_factors.append(f"concordance_{req_symp}_{req_bm}")
                evidence_list.extend(ev)

    # -------------------------------------------------------------
    # STAGE 4: Calculate Longitudinal Risk Score & Level
    # -------------------------------------------------------------
    long_score = round(sum(s.weight for s in signals), 2)

    if long_score >= 35.0:
        long_lvl: LongitudinalRiskLevel = "URGENT"
    elif long_score >= 20.0:
        long_lvl = "HIGH"
    elif long_score >= 10.0:
        long_lvl = "MODERATE"
    else:
        long_lvl = "LOW"

    # -------------------------------------------------------------
    # STAGE 5: Determine Temporal Persistence Index
    # -------------------------------------------------------------
    if matched_recurrent:
        persist_idx: TemporalPersistenceIndex = "recurrent"
    elif is_persistent_duration:
        persist_idx = "persistent"
    elif any(normalize_problem_label(c)[0] == active_norm_cc for c in chronic_conds):
        persist_idx = "chronic_baseline"
    elif total_encounters == 1:
        persist_idx = "acute_isolated"
    else:
        persist_idx = "acute_isolated"

    # -------------------------------------------------------------
    # STAGE 6: Determine Escalation Status
    # -------------------------------------------------------------
    has_esc_signal = any(s.signal_id == "historical_risk_escalation_signal" for s in signals)
    curr_lvl_str = str(current_risk_assessment.get("risk_level", "LOW")).upper()
    
    if has_esc_signal or (RISK_LEVEL_ORDER.get(long_lvl, 0) > RISK_LEVEL_ORDER.get(curr_lvl_str, 0) and long_score >= 20.0):
        esc_status: RiskEscalationStatus = "escalated"
    elif total_encounters >= 2:
        esc_status = "stable"
    else:
        esc_status = "insufficient_longitudinal_data"

    data_comp: DataCompletenessStatus = "complete" if len(long_ctx.timeline) >= 2 else "partial"

    reasoning_parts = [
        f"Phase 10 evaluated {len(signals)} longitudinal risk signal(s) totaling score {long_score} ({long_lvl})."
    ]
    for s in signals:
        reasoning_parts.append(f"[{s.category.upper()}] {s.rationale}")

    return LongitudinalRiskAssessmentDTO(
        longitudinal_risk_score=long_score,
        longitudinal_risk_level=long_lvl,
        risk_escalation_status=esc_status,
        temporal_persistence_index=persist_idx,
        risk_signals=signals,
        contributing_longitudinal_factors=_dedupe_strings(contributing_factors),
        longitudinal_evidence=_dedupe_strings(evidence_list),
        reasoning=" ".join(reasoning_parts),
        data_completeness=data_comp,
    )


def synthesize_composite_risk(
    current_risk: dict[str, Any],
    longitudinal_risk: LongitudinalRiskAssessmentDTO,
    safety_findings: dict[str, Any],
) -> CompositeRiskOutputDTO:
    """
    Arbitrates composite risk level and effective care pathway following strict safety hierarchy:
    Phase 2A Emergency Override > Phase 2B Current Risk Floor > Phase 10 Longitudinal Escalation.
    """
    curr_lvl = str(current_risk.get("risk_level") or "LOW").upper()
    long_lvl = longitudinal_risk.longitudinal_risk_level

    # 1. Phase 2A Red Flag Emergency Override
    immediate_attention = bool(safety_findings.get("immediate_attention_required"))
    red_flag_detected = safety_findings.get("red_flag_status") == "red_flags_detected"

    if immediate_attention or red_flag_detected:
        override_reason = "Phase 2A red-flag emergency safety rule triggered; immediate emergency attention required."
        return CompositeRiskOutputDTO(
            current_risk=current_risk,
            longitudinal_risk=longitudinal_risk,
            composite_risk_level="URGENT",
            effective_care_pathway="emergency",
            composite_reasoning=f"Critical emergency override applied. {override_reason}",
            safety_override_applied=True,
            override_reason=override_reason,
            provenance_notes=[
                "Phase 2A red_flag_rules.py (Authoritative Emergency Override)",
                "Phase 2B risk_convergence (Preserved Immutably)",
                "Phase 10 advanced_risk_engine.py",
            ],
        )

    # 2. Arbitrate Floor vs Longitudinal Escalation
    curr_rank = RISK_LEVEL_ORDER.get(curr_lvl, 1)
    long_rank = RISK_LEVEL_ORDER.get(long_lvl, 1)

    if long_rank > curr_rank:
        composite_lvl: CompositeRiskLevel = long_lvl  # Escalated by longitudinal history
        composite_reason = (
            f"Current acute presentation risk is {curr_lvl}, but longitudinal context elevates composite risk to {long_lvl} "
            f"due to {len(longitudinal_risk.risk_signals)} historical/longitudinal risk signal(s) totaling score {longitudinal_risk.longitudinal_risk_score}."
        )
    else:
        # Phase 2B current risk floor preserved
        effective_curr = curr_lvl if curr_lvl in {"LOW", "MODERATE", "HIGH", "URGENT"} else "LOW"
        composite_lvl = effective_curr  # type: ignore[assignment]
        composite_reason = (
            f"Composite risk maintained at current encounter floor ({effective_curr}). "
            f"Phase 2B score is {current_risk.get('risk_score', 0)} ({effective_curr})."
        )

    # 3. Determine Effective Care Pathway
    if composite_lvl == "URGENT":
        pathway: EffectiveCarePathway = "emergency"
    elif composite_lvl == "HIGH":
        pathway = "urgent"
    elif curr_lvl == "INCOMPLETE":
        pathway = "incomplete"
    else:
        pathway = "routine"

    return CompositeRiskOutputDTO(
        current_risk=current_risk,
        longitudinal_risk=longitudinal_risk,
        composite_risk_level=composite_lvl,
        effective_care_pathway=pathway,
        composite_reasoning=composite_reason,
        safety_override_applied=False,
        override_reason=None,
        provenance_notes=[
            "Phase 2A red-flag rules (Evaluated, No Red Flags)",
            "Phase 2B deterministic risk scoring (phase2b_v1, Preserved)",
            "Phase 10 deterministic longitudinal risk convergence",
        ],
    )


def evaluate_advanced_risk(state: dict[str, Any]) -> CompositeRiskOutputDTO:
    """
    Main entry point for Phase 10: Advanced Risk Convergence.
    
    Accepts full VaidyaArcState, pulls/synthesizes Phase 9 longitudinal context,
    evaluates longitudinal risk signals, and arbitrates composite risk without
    altering Phase 2B.
    """
    # Current risk bundle from Phase 2B state
    current_risk = {
        "risk_level": state.get("risk_level", "LOW"),
        "risk_score": state.get("risk_score", 0),
        "risk_signal_summary": state.get("risk_signal_summary") or [],
        "risk_contributing_factors": state.get("risk_contributing_factors") or [],
        "risk_evidence": state.get("risk_evidence") or [],
        "risk_reasoning": state.get("risk_reasoning") or "",
        "recommended_next_action": state.get("recommended_next_action") or "",
        "convergence_status": state.get("convergence_status") or "evaluated",
        "risk_context_flags": state.get("risk_context_flags") or [],
        "risk_assessment_version": state.get("risk_assessment_version") or "phase2b_v1",
    }

    safety_findings = {
        "red_flag_status": state.get("red_flag_status"),
        "red_flags": state.get("red_flags") or [],
        "red_flag_evidence": state.get("red_flag_evidence") or [],
        "immediate_attention_required": state.get("immediate_attention_required", False),
        "red_flag_rule_hits": state.get("red_flag_rule_hits") or [],
    }

    # Evaluate Phase 10 longitudinal risk
    longitudinal_dto = evaluate_longitudinal_risk(
        state_or_input=state,
        current_risk_assessment=current_risk,
        longitudinal_context=None,
    )

    # Arbitrate composite risk
    composite_dto = synthesize_composite_risk(
        current_risk=current_risk,
        longitudinal_risk=longitudinal_dto,
        safety_findings=safety_findings,
    )

    return composite_dto
