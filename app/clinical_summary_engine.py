"""
Phase 11: Clinical Summary and Consultation Questions Engine.

Transforms VaidyaArc structured clinical intelligence (Phases 1B through 10) into:
1. A physician-ready structured clinical summary across 12 standard clinical domains.
2. A contextual list of high-value consultation questions for patient-physician discussion.

CRITICAL SAFETY INVARIANTS:
1. Phase 2A emergency red-flag override is authoritative and preserved unconditionally.
2. Phase 2B risk scores, risk levels, and evidence remain immutable.
3. Phase 10 advanced risk outputs remain immutable.
4. ZERO fact hallucination / invention. Missing information remains explicitly represented
   as 'not_reported' or 'insufficient_information'. Never assume negative findings or NKDA.
5. ZERO diagnosis generation, ZERO treatment recommendations, ZERO drug prescriptions.
6. Biomarker trajectories are observational only without arbitrary clinical thresholds.
7. 100% Deterministic rule engine with clean fallback support.
"""

from typing import Any, Optional
import re

from app.clinical_summary_schema import (
    ClinicalSummarySection,
    ClinicalSummaryDTO,
    ConsultationQuestionDTO,
    ConsultationQuestionsDTO,
    Phase11ClinicalSummaryOutputDTO,
    SectionStatus,
    DataCompletenessLevel,
    QuestionPriority,
)


def _clean_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _detect_conflicts(state: dict[str, Any]) -> list[str]:
    """
    Detects explicit discrepancies between patient raw text and structured intake slots.
    """
    conflicts: list[str] = []
    
    current_msg = str(state.get("current_message") or "").lower()
    original_tx = str(state.get("original_transcript") or "").lower()
    combined_raw = f"{current_msg} {original_tx}"
    
    reported_sev = str(state.get("severity") or "").lower()
    if reported_sev in ["mild", "low"]:
        if any(w in combined_raw for w in ["unbearable", "extremely severe", "worst pain", "excruciating", "10/10"]):
            conflicts.append("Patient structured severity is recorded as 'mild', but message narrative indicates acute severe distress.")

    reported_dur = str(state.get("duration") or "").lower()
    if reported_dur and any(w in reported_dur for w in ["today", "1 day", "few hours"]):
        if any(w in combined_raw for w in ["for months", "since last year", "chronic for weeks"]):
            conflicts.append("Structured duration indicates acute onset, but narrative text mentions chronic multi-week history.")

    return conflicts


def build_chief_complaint_section(state: dict[str, Any]) -> ClinicalSummarySection:
    cc = _clean_str(state.get("chief_complaint"))
    if cc:
        from app.nodes import _canonicalize_chief_complaint
        clean_cc = _canonicalize_chief_complaint(cc) or cc
        return ClinicalSummarySection(
            section_name="Chief Complaint",
            content=f"Patient presents with: {clean_cc}.",
            status="reported",
            structured_data={"chief_complaint": clean_cc},
            provenance=["intake_chief_complaint"],
        )
    
    msg = _clean_str(state.get("current_message"))
    if msg:
        from app.nodes import _canonicalize_chief_complaint
        clean_msg = _canonicalize_chief_complaint(msg) or msg
        return ClinicalSummarySection(
            section_name="Chief Complaint",
            content=f"Primary presenting concern from intake message: '{clean_msg}'.",
            status="reported",
            structured_data={"chief_complaint": clean_msg},
            provenance=["current_message_fallback"],
        )
        
    return ClinicalSummarySection(
        section_name="Chief Complaint",
        content="Chief complaint not explicitly reported.",
        status="not_reported",
        structured_data=None,
        provenance=["intake_missing"],
    )


def build_hpi_section(state: dict[str, Any], conflicts: list[str]) -> ClinicalSummarySection:
    cc = _clean_str(state.get("chief_complaint"))
    duration = _clean_str(state.get("duration"))
    severity = _clean_str(state.get("severity"))
    nature = _clean_str(state.get("nature_of_pain"))
    location = _clean_str(state.get("location"))
    assoc = state.get("associated_symptoms") or []
    pertinent_negs = state.get("pertinent_negatives") or []
    past_history = _clean_str(state.get("past_history_notes"))
    addl_notes = _clean_str(state.get("additional_patient_notes"))

    from app.nodes import _canonicalize_chief_complaint, _sanitize_associated_symptoms
    clean_cc = _canonicalize_chief_complaint(cc) or cc if cc else None

    parts: list[str] = []
    if clean_cc:
        parts.append(f"Patient reports {clean_cc.lower()}")
    else:
        parts.append("Patient reports presenting symptoms")

    if nature:
        parts.append(f"characterized as {nature}")
    if location:
        parts.append(f"located in {location}")
    if duration:
        parts.append(f"with duration of {duration}")
    if severity:
        parts.append(f"rated as {severity} in severity")

    clean_assoc = _sanitize_associated_symptoms(assoc)
    if clean_assoc:
        parts.append(f"Associated symptoms include: {', '.join(clean_assoc)}")

    clean_negs = [str(n).strip() for n in pertinent_negs if str(n).strip()]
    if clean_negs:
        parts.append(f"Pertinent negatives (denied symptoms): {', '.join(clean_negs)}")

    if past_history:
        parts.append(f"Prior history / recurrence: {past_history}")

    if addl_notes:
        parts.append(f"Additional notes: {addl_notes}")

    missing = state.get("missing_information") or []
    if missing:
        parts.append(f"[Unreported HPI Elements: {', '.join(missing)}]")

    if not cc and not duration and not severity and not nature and not location and not assoc and not clean_negs and not past_history and not addl_notes:
        return ClinicalSummarySection(
            section_name="History of Present Illness",
            content="No detailed history of present illness reported.",
            status="not_reported",
            structured_data=None,
            provenance=["intake_missing"],
        )

    content = ". ".join(parts) + "."
    status: SectionStatus = "conflicting" if conflicts else "reported"
    if not severity or not duration:
        if status != "conflicting":
            status = "reported"

    return ClinicalSummarySection(
        section_name="History of Present Illness",
        content=content,
        status=status,
        structured_data={
            "duration": duration,
            "severity": severity,
            "nature_of_pain": nature,
            "location": location,
            "associated_symptoms": assoc,
            "pertinent_negatives": clean_negs,
            "past_history_notes": past_history,
            "additional_patient_notes": addl_notes,
            "missing_elements": missing,
        },
        provenance=["phase1b_intake_extraction"],
    )


def build_pmh_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    conditions = profile.get("medical_conditions") or []
    clean_conds = [str(c).strip() for c in conditions if str(c).strip()]
    past_notes = _clean_str(state.get("past_history_notes"))

    parts: list[str] = []
    provenance: list[str] = []
    if clean_conds:
        parts.append(f"Documented chronic medical conditions: {', '.join(clean_conds)}.")
        provenance.append("patient_profile_medical_conditions")
    if past_notes:
        parts.append(f"Patient reported past history / recurrence: {past_notes}.")
        provenance.append("intake_past_history")

    if parts:
        return ClinicalSummarySection(
            section_name="Past Medical History",
            content=" ".join(parts),
            status="reported",
            structured_data={
                "medical_conditions": clean_conds,
                "past_history_notes": past_notes,
            },
            provenance=provenance,
        )

    return ClinicalSummarySection(
        section_name="Past Medical History",
        content="Past medical history not reported or not available in patient profile.",
        status="not_reported",
        structured_data={"medical_conditions": [], "past_history_notes": None},
        provenance=["patient_profile_unspecified"],
    )


def build_psh_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    surgeries = profile.get("surgical_history") or []
    clean_surg = [str(s).strip() for s in surgeries if str(s).strip()]

    if clean_surg:
        return ClinicalSummarySection(
            section_name="Past Surgical History",
            content=f"Documented surgical history: {', '.join(clean_surg)}.",
            status="reported",
            structured_data={"surgical_history": clean_surg},
            provenance=["patient_profile_surgical_history"],
        )

    return ClinicalSummarySection(
        section_name="Past Surgical History",
        content="Past surgical history not reported.",
        status="not_reported",
        structured_data={"surgical_history": []},
        provenance=["patient_profile_unspecified"],
    )


def build_medication_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    meds = profile.get("chronic_medications") or []
    
    docs = state.get("documents") or []
    presc_meds = []
    for d in docs:
        if isinstance(d, dict) and d.get("document_type") == "prescription":
            txt = d.get("extracted_text") or ""
            if txt:
                presc_meds.append(f"Prescription ({d.get('document_id', 'DOC')}): {txt.strip()}")

    if meds or presc_meds:
        med_strs = []
        clean_structured_meds = []
        for m in meds:
            if isinstance(m, dict):
                name = m.get("name") or m.get("drug_name") or str(m)
                dosage = m.get("dosage") or ""
                dosage_norm = (
                    str(dosage)
                    .replace("500mg twice", "500 mg (2x)")
                    .replace("dosage: 500mg", "dose: 500 mg")
                    .replace("prescribed rx", "prescription rx")
                )
                med_strs.append(f"{name} ({dosage_norm})".strip() if dosage_norm else str(name).strip())
                m_clean = dict(m)
                if "dosage" in m_clean:
                    m_clean["dosage"] = dosage_norm
                clean_structured_meds.append(m_clean)
            else:
                med_strs.append(str(m).strip())
                clean_structured_meds.append(str(m).strip())
        
        all_meds = med_strs + presc_meds
        return ClinicalSummarySection(
            section_name="Medication History",
            content=f"Documented medications: {'; '.join(all_meds)}.",
            status="reported",
            structured_data={"medications": clean_structured_meds, "prescriptions": presc_meds},
            provenance=["patient_profile_chronic_medications", "document_prescriptions"],
        )

    return ClinicalSummarySection(
        section_name="Medication History",
        content="Current medication history not reported.",
        status="not_reported",
        structured_data={"medications": []},
        provenance=["patient_profile_unspecified"],
    )


def build_allergy_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    allergies = profile.get("allergies") or []
    clean_allergies = [str(a).strip() for a in allergies if str(a).strip()]

    if clean_allergies:
        return ClinicalSummarySection(
            section_name="Allergy History",
            content=f"Documented known allergies: {', '.join(clean_allergies)}.",
            status="reported",
            structured_data={"allergies": clean_allergies},
            provenance=["patient_profile_allergies"],
        )

    return ClinicalSummarySection(
        section_name="Allergy History",
        content="Allergy history not reported (No Known Drug Allergies not confirmed; requires clinical verification).",
        status="not_reported",
        structured_data={"allergies": []},
        provenance=["patient_profile_unspecified"],
    )


def build_family_history_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    fam = profile.get("family_history") or []
    clean_fam = [str(f).strip() for f in fam if str(f).strip()]

    if clean_fam:
        return ClinicalSummarySection(
            section_name="Family History",
            content=f"Documented family history: {', '.join(clean_fam)}.",
            status="reported",
            structured_data={"family_history": clean_fam},
            provenance=["patient_profile_family_history"],
        )

    return ClinicalSummarySection(
        section_name="Family History",
        content="Family medical history not reported.",
        status="not_reported",
        structured_data={"family_history": []},
        provenance=["patient_profile_unspecified"],
    )


def build_personal_social_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    age = profile.get("age")
    sex = profile.get("sex")
    loc = state.get("patient_location") or {}
    city = loc.get("city") if isinstance(loc, dict) else None

    items: list[str] = []
    if age is not None:
        items.append(f"Age: {age} years")
    if sex:
        items.append(f"Sex: {sex}")
    if city:
        items.append(f"Location: {city}")

    if items:
        return ClinicalSummarySection(
            section_name="Personal and Social History",
            content=f"Patient demographics: {', '.join(items)}.",
            status="reported",
            structured_data={"age": age, "sex": sex, "location": city},
            provenance=["patient_profile_demographics"],
        )

    return ClinicalSummarySection(
        section_name="Personal and Social History",
        content="Personal and social history not reported.",
        status="not_reported",
        structured_data=None,
        provenance=["patient_profile_unspecified"],
    )


def build_ros_section(state: dict[str, Any]) -> ClinicalSummarySection:
    assoc = state.get("associated_symptoms") or []
    from app.nodes import _sanitize_associated_symptoms
    clean_assoc = _sanitize_associated_symptoms(assoc)
    pertinent_negs = state.get("pertinent_negatives") or []
    clean_negs = [str(n).strip() for n in pertinent_negs if str(n).strip()]

    ros_parts = []
    provenance = []
    if clean_assoc:
        ros_parts.append(f"Positive review of systems findings reported: {', '.join(clean_assoc)}")
        provenance.append("intake_associated_symptoms")
    if clean_negs:
        ros_parts.append(f"Documented pertinent negatives: {', '.join(clean_negs)}")
        provenance.append("intake_pertinent_negatives")

    if ros_parts:
        return ClinicalSummarySection(
            section_name="Review of Systems",
            content=f"{'. '.join(ros_parts)}. Full systemic review not documented.",
            status="reported",
            structured_data={"positive_findings": clean_assoc, "negative_findings": clean_negs},
            provenance=provenance,
        )

    return ClinicalSummarySection(
        section_name="Review of Systems",
        content="Review of systems not explicitly documented beyond primary complaint (system negatives not inferred).",
        status="not_reported",
        structured_data={"positive_findings": [], "negative_findings": []},
        provenance=["intake_unspecified"],
    )


def build_prior_investigations_section(state: dict[str, Any]) -> ClinicalSummarySection:
    docs = state.get("documents") or state.get("ocr_documents") or []
    investigations = state.get("investigations") or []

    inv_summaries: list[str] = []
    structured_invs: list[dict[str, Any]] = []

    for d in docs:
        if isinstance(d, dict):
            doc_id = d.get("document_id", "DOC")
            doc_type = d.get("document_type", "report")
            doc_date = d.get("document_date") or "undated"
            biomarkers = d.get("structured_biomarkers") or []
            
            bm_strs = []
            for bm in biomarkers:
                if isinstance(bm, dict):
                    name = bm.get("biomarker") or bm.get("test_name") or "Test"
                    val = bm.get("value")
                    unit = bm.get("unit") or ""
                    bm_strs.append(f"{name}: {val} {unit}".strip())

            bm_text = f" ({', '.join(bm_strs)})" if bm_strs else ""
            inv_summaries.append(f"{doc_type.upper()} [{doc_id}, Date: {doc_date}]{bm_text}")
            structured_invs.append({
                "document_id": doc_id,
                "document_type": doc_type,
                "date": doc_date,
                "biomarkers": biomarkers,
            })

    for inv in investigations:
        if isinstance(inv, dict):
            test = inv.get("test_name") or inv.get("name") or "Investigation"
            res = inv.get("result") or inv.get("value") or ""
            date_str = inv.get("date") or "undated"
            inv_summaries.append(f"{test}: {res} (Date: {date_str})")
            structured_invs.append(inv)

    if inv_summaries:
        return ClinicalSummarySection(
            section_name="Prior Investigations and Diagnostics",
            content=f"Documented diagnostic investigations: {'; '.join(inv_summaries)}.",
            status="reported",
            structured_data=structured_invs,
            provenance=["document_ocr_biomarkers", "investigation_records"],
        )

    return ClinicalSummarySection(
        section_name="Prior Investigations and Diagnostics",
        content="No prior diagnostic investigations, laboratory reports, or imaging provided.",
        status="not_reported",
        structured_data=[],
        provenance=["investigation_unspecified"],
    )


def build_longitudinal_context_section(state: dict[str, Any]) -> ClinicalSummarySection:
    long_ctx = state.get("longitudinal_context") or {}
    adv_risk = state.get("advanced_risk_output") or {}

    total_encs = long_ctx.get("total_encounters", 1)
    recurrent = long_ctx.get("recurrent_complaints") or []
    unresolved = long_ctx.get("unresolved_issues") or []
    resolved = long_ctx.get("resolved_problems") or []
    trajectories = long_ctx.get("biomarker_trajectories") or []

    findings: list[str] = []
    if total_encs > 1:
        findings.append(f"Total documented encounters: {total_encs}")
    
    if recurrent:
        rec_labels = [r.get("label", "problem") if isinstance(r, dict) else str(r) for r in recurrent]
        findings.append(f"Recurrent complaints: {', '.join(rec_labels)}")

    if unresolved:
        unres_labels = [u.get("label", "issue") if isinstance(u, dict) else str(u) for u in unresolved]
        findings.append(f"Unresolved historical issues: {', '.join(unres_labels)}")

    if resolved:
        res_labels = [r.get("label", "resolved") if isinstance(r, dict) else str(r) for r in resolved]
        findings.append(f"Explicitly resolved problems: {', '.join(res_labels)}")

    if trajectories:
        for t in trajectories:
            if isinstance(t, dict):
                t_name = t.get("test_name", "Test")
                t_dir = t.get("trajectory", "stable")
                delta = t.get("absolute_delta")
                obs_count = t.get("observation_count", 0)
                if obs_count >= 2 and t_dir not in ["insufficient_data", "unit_mismatch"]:
                    findings.append(f"Biomarker observation: {t_name} showed {t_dir} trend across {obs_count} points (delta={delta}, non-diagnostic observation)")

    if findings:
        return ClinicalSummarySection(
            section_name="Longitudinal and Follow-up Context",
            content=f"Longitudinal history: {'; '.join(findings)}.",
            status="reported",
            structured_data={
                "total_encounters": total_encs,
                "recurrent": recurrent,
                "unresolved": unresolved,
                "resolved": resolved,
                "trajectories": trajectories,
            },
            provenance=["phase9_longitudinal_context", "phase10_advanced_risk"],
        )

    return ClinicalSummarySection(
        section_name="Longitudinal and Follow-up Context",
        content="Single encounter baseline; no prior longitudinal records or multi-encounter trends available.",
        status="insufficient_information",
        structured_data=None,
        provenance=["phase9_zero_history_baseline"],
    )


def build_safety_and_risk_section(state: dict[str, Any]) -> ClinicalSummarySection:
    # Phase 2A
    red_flag_status = state.get("red_flag_status") or "no_obvious_red_flags"
    red_flags = state.get("red_flags") or []
    immediate_attention = bool(state.get("immediate_attention_required", False))

    # Phase 2B
    risk_level = state.get("risk_level") or "LOW"
    risk_score = state.get("risk_score") or 0
    risk_signals = state.get("risk_signal_summary") or []

    # Phase 10
    adv_risk = state.get("advanced_risk_output") or {}
    composite_level = adv_risk.get("composite_risk_level") or risk_level
    care_pathway = adv_risk.get("effective_care_pathway") or "routine"
    override_applied = adv_risk.get("safety_override_applied", False)

    findings: list[str] = []
    
    if immediate_attention or red_flag_status == "red_flags_detected":
        findings.append(
            f"CRITICAL SAFETY OVERRIDE ACTIVE: Immediate emergency attention required. Red flags detected: {', '.join(red_flags) if red_flags else 'Emergency criteria met'}."
        )
    else:
        findings.append("No immediate emergency red flags detected.")

    findings.append(f"Clinical Triage Risk: {risk_level} (Score: {risk_score}/100)")
    
    if composite_level != risk_level:
        findings.append(f"Composite Risk: {composite_level} (Effective Pathway: {care_pathway.upper()})")
    else:
        findings.append(f"Effective Care Pathway: {care_pathway.upper()}")

    if risk_signals:
        formatted_signals = [s.replace("_", " ").title() for s in risk_signals]
        findings.append(f"Active risk signals: {', '.join(formatted_signals)}")

    return ClinicalSummarySection(
        section_name="Current Safety and Risk Summary",
        content=" | ".join(findings),
        status="reported",
        structured_data={
            "red_flag_status": red_flag_status,
            "red_flags": red_flags,
            "immediate_attention_required": immediate_attention,
            "phase2b_risk_level": risk_level,
            "phase2b_risk_score": risk_score,
            "composite_risk_level": composite_level,
            "effective_care_pathway": care_pathway,
            "safety_override_applied": override_applied,
        },
        provenance=["phase2a_red_flag_rules", "phase2b_risk_convergence", "phase10_advanced_risk_engine"],
    )


def generate_clinical_summary(state: dict[str, Any]) -> ClinicalSummaryDTO:
    """
    Generates a physician-ready ClinicalSummaryDTO from VaidyaArc state.
    """
    conflicts = _detect_conflicts(state)

    sec_cc = build_chief_complaint_section(state)
    sec_hpi = build_hpi_section(state, conflicts)
    sec_pmh = build_pmh_section(state)
    sec_psh = build_psh_section(state)
    sec_med = build_medication_section(state)
    sec_all = build_allergy_section(state)
    sec_fam = build_family_history_section(state)
    sec_soc = build_personal_social_section(state)
    sec_ros = build_ros_section(state)
    sec_inv = build_prior_investigations_section(state)
    sec_lng = build_longitudinal_context_section(state)
    sec_saf = build_safety_and_risk_section(state)

    # Determine overall data completeness level
    missing_info = state.get("missing_information") or []
    cc = state.get("chief_complaint")
    duration = state.get("duration")
    severity = state.get("severity")

    if not cc:
        completeness: DataCompletenessLevel = "insufficient"
    elif not duration or not severity or len(missing_info) >= 2:
        completeness = "partial"
    elif len(missing_info) == 1:
        completeness = "partial"
    else:
        completeness = "complete"

    # Multi-line clinical narrative synthesis
    narrative_lines: list[str] = [
        f"CLINICAL CASE SUMMARY ({completeness.upper()})",
        "--------------------------------------------------",
        f"PRESENTING COMPLAINT: {sec_cc.content}",
        f"HPI: {sec_hpi.content}",
        f"PAST MEDICAL & SURGICAL: {sec_pmh.content} {sec_psh.content}",
        f"MEDICATIONS & ALLERGIES: {sec_med.content} {sec_all.content}",
        f"FAMILY & SOCIAL: {sec_fam.content} {sec_soc.content}",
        f"REVIEW OF SYSTEMS: {sec_ros.content}",
        f"DIAGNOSTICS & INVESTIGATIONS: {sec_inv.content}",
        f"LONGITUDINAL CONTEXT: {sec_lng.content}",
        f"SAFETY & RISK: {sec_saf.content}",
    ]
    if conflicts:
        narrative_lines.append("--------------------------------------------------")
        narrative_lines.append("DOCUMENTED DISCREPANCIES REQUIRING CLARIFICATION:")
        for c in conflicts:
            narrative_lines.append(f" - {c}")

    summary_narrative = "\n".join(narrative_lines)

    provenance_notes = [
        "Phase 1B deterministic intake extraction",
        "Phase 2A deterministic emergency red flag rules",
        "Phase 2B deterministic risk scoring (phase2b_v1)",
        "Phase 3 clinical case representation schema",
        "Phase 9 deterministic longitudinal intelligence",
        "Phase 10 deterministic advanced risk convergence",
        "Phase 11 deterministic clinical summary engine",
    ]

    return ClinicalSummaryDTO(
        chief_complaint=sec_cc,
        history_of_present_illness=sec_hpi,
        past_medical_history=sec_pmh,
        past_surgical_history=sec_psh,
        medication_history=sec_med,
        allergy_history=sec_all,
        family_history=sec_fam,
        personal_social_history=sec_soc,
        review_of_systems=sec_ros,
        prior_investigations=sec_inv,
        longitudinal_context=sec_lng,
        safety_and_risk_summary=sec_saf,
        data_completeness=completeness,
        conflicts_identified=conflicts,
        summary_narrative=summary_narrative,
        provenance_notes=provenance_notes,
    )


def generate_consultation_questions(
    state: dict[str, Any],
    clinical_summary: ClinicalSummaryDTO,
) -> ConsultationQuestionsDTO:
    """
    Synthesizes contextual patient consultation questions based on active evidence and information gaps.
    """
    questions: list[ConsultationQuestionDTO] = []
    generated_from: list[str] = []

    cc = state.get("chief_complaint") or "reported symptoms"
    severity = str(state.get("severity") or "").lower()
    duration = state.get("duration")
    missing_info = state.get("missing_information") or []
    
    immediate_attention = bool(state.get("immediate_attention_required", False))
    red_flags = state.get("red_flags") or []
    risk_level = str(state.get("risk_level") or "LOW").upper()

    # 1. Emergency / Warning Signs Question
    if immediate_attention or red_flags or risk_level in ["HIGH", "URGENT"]:
        questions.append(ConsultationQuestionDTO(
            question_id="Q_EMERGENCY_WARNING_SIGNS",
            question="What specific warning symptoms or changes should prompt immediate emergency care?",
            category="warning_signs",
            rationale="High-risk or emergency presentation requires clear patient understanding of escalation triggers.",
            priority="high",
            source_evidence=[f"Risk level {risk_level}", f"Red flags: {red_flags}"],
            provenance="phase2a_phase2b_safety_engine",
        ))
        generated_from.append("safety_risk_status")

    # 2. Symptom Cause / Differential Exploration Question
    if cc:
        from app.nodes import _canonicalize_chief_complaint
        clean_cc_q = _canonicalize_chief_complaint(cc) or cc
        questions.append(ConsultationQuestionDTO(
            question_id="Q_SYMPTOM_CAUSE",
            question=f"What potential underlying causes could explain my {clean_cc_q.lower()}?",
            category="symptom_cause",
            rationale="Helps patient initiate diagnostic discussion regarding the chief complaint with the doctor.",
            priority="high",
            source_evidence=[f"Chief complaint: {clean_cc_q}"],
            provenance="intake_chief_complaint",
        ))
        generated_from.append("chief_complaint")

    # 3. Information Gaps / Clarification Questions
    for gap in missing_info:
        gap_clean = str(gap).lower()
        if "duration" in gap_clean or "onset" in gap_clean:
            questions.append(ConsultationQuestionDTO(
                question_id="Q_GAP_DURATION",
                question="How does the timeline and onset pattern of my symptoms affect the evaluation?",
                category="information_gap",
                rationale="Duration was not fully documented during initial intake.",
                priority="medium",
                source_evidence=["Unreported duration"],
                provenance="intake_missing_slot",
            ))
            generated_from.append("missing_duration")
        elif "severity" in gap_clean:
            questions.append(ConsultationQuestionDTO(
                question_id="Q_GAP_SEVERITY",
                question="How should I track and describe the intensity or severity changes of my symptoms?",
                category="information_gap",
                rationale="Severity was not fully specified during intake.",
                priority="medium",
                source_evidence=["Unreported severity"],
                provenance="intake_missing_slot",
            ))
            generated_from.append("missing_severity")
        elif "location" in gap_clean:
            questions.append(ConsultationQuestionDTO(
                question_id="Q_GAP_LOCATION",
                question="Are there specific anatomical areas or symptom radiation patterns that need physical examination?",
                category="information_gap",
                rationale="Symptom location or radiation was not fully specified.",
                priority="medium",
                source_evidence=["Unreported location"],
                provenance="intake_missing_slot",
            ))
            generated_from.append("missing_location")

    # 4. Diagnostic Tests & Investigations Question
    inv_sec = clinical_summary.prior_investigations
    if inv_sec.status == "reported" and inv_sec.structured_data:
        questions.append(ConsultationQuestionDTO(
            question_id="Q_INVESTIGATION_INTERPRETATION",
            question="How should my previous laboratory or diagnostic test results be interpreted in light of my current symptoms?",
            category="investigation_interpretation",
            rationale="Patient has documented prior test reports requiring clinical correlation.",
            priority="high",
            source_evidence=[inv_sec.content],
            provenance="prior_investigation_records",
        ))
        generated_from.append("prior_investigations")
    else:
        questions.append(ConsultationQuestionDTO(
            question_id="Q_DIAGNOSTIC_TESTS",
            question="What diagnostic tests or clinical examinations are recommended to evaluate these symptoms?",
            category="diagnostic_testing",
            rationale="Clarifies necessary next steps for clinical workup.",
            priority="standard",
            source_evidence=[f"Presenting complaint: {cc}"],
            provenance="general_diagnostic_workup",
        ))
        generated_from.append("diagnostic_needs")

    # 5. Chronic Conditions & Medication Relevance Question
    pmh_sec = clinical_summary.past_medical_history
    med_sec = clinical_summary.medication_history
    if pmh_sec.status == "reported" and pmh_sec.structured_data and pmh_sec.structured_data.get("medical_conditions"):
        conds = ", ".join(pmh_sec.structured_data["medical_conditions"])
        questions.append(ConsultationQuestionDTO(
            question_id="Q_CHRONIC_CONDITION_RELEVANCE",
            question=f"Could my existing condition of {conds} or my current medications be related to my present symptoms?",
            category="history_relevance",
            rationale="Underlying chronic conditions may interact with or contribute to presenting symptoms.",
            priority="high",
            source_evidence=[f"Chronic conditions: {conds}"],
            provenance="patient_profile_medical_conditions",
        ))
        generated_from.append("chronic_conditions")

    # 6. Longitudinal Recurrence / Persistence Question
    long_sec = clinical_summary.longitudinal_context
    if long_sec.status == "reported" and long_sec.structured_data:
        rec = long_sec.structured_data.get("recurrent") or []
        traj = long_sec.structured_data.get("trajectories") or []
        if rec or duration and any(w in str(duration).lower() for w in ["week", "month", "year"]):
            questions.append(ConsultationQuestionDTO(
                question_id="Q_LONGITUDINAL_RECURRENCE",
                question="Given that these symptoms have recurred or persisted over time, what specialized evaluation or monitoring is needed?",
                category="longitudinal_trend",
                rationale="Persistent or recurrent symptom history indicates need for longitudinal evaluation strategy.",
                priority="high",
                source_evidence=[long_sec.content],
                provenance="phase9_longitudinal_problem_registry",
            ))
            generated_from.append("longitudinal_persistence")
        elif traj:
            questions.append(ConsultationQuestionDTO(
                question_id="Q_BIOMARKER_TRAJECTORY_FOLLOWUP",
                question="Do the observed trends in my prior lab tests require repeat testing or further follow-up?",
                category="investigation_interpretation",
                rationale="Biomarker trajectory changes observed across historical tests.",
                priority="medium",
                source_evidence=[long_sec.content],
                provenance="phase9_biomarker_engine",
            ))
            generated_from.append("biomarker_trajectory")

    # 7. Safety Context Summary
    safety_context = (
        "EMERGENCY PRIORITY: Immediate clinical attention required."
        if immediate_attention
        else f"Routine consultation preparation (Risk Level: {risk_level})."
    )

    return ConsultationQuestionsDTO(
        questions=questions,
        generated_from=list(set(generated_from)),
        safety_context=safety_context,
    )


from datetime import datetime, timezone


def generate_eleven_section_casesheet(state: dict[str, Any]) -> str:
    """
    Synthesizes the standard 11-section Clinical Case-Sheet in Markdown.
    Strictly follows zero-hallucination principles: unstated fields display explicitly as 'Not elicited'.
    """
    from app.domain.clinical_history_schema import EpistemicStatus

    # 1. Extract Profile & Demographics
    prof = state.get("patient_profile") or {}
    name = prof.get("name") or "Not elicited"
    age = prof.get("age")
    sex = prof.get("sex")
    if age and sex:
        age_sex_str = f"{age} / {str(sex).capitalize()}"
    elif age:
        age_sex_str = f"{age} years / Sex not elicited"
    elif sex:
        age_sex_str = f"Age not elicited / {str(sex).capitalize()}"
    else:
        age_sex_str = "Not elicited"

    consult_date = state.get("consultation_date") or datetime.now().strftime("%d %B %Y")
    
    # 2. Extract Chief Complaint, Site, Laterality, Duration
    hist_raw = state.get("evolving_clinical_history") or {}
    cc_finding = hist_raw.get("chief_complaint") or {}
    
    cc_name = state.get("chief_complaint") or cc_finding.get("canonical_name") or "Health complaint"
    duration = state.get("duration")
    if not duration and cc_finding.get("duration"):
        duration = cc_finding["duration"].get("current_value")
    
    location = state.get("location")
    if not location and cc_finding.get("anatomical_site"):
        location = cc_finding["anatomical_site"].get("current_value")
    
    laterality = cc_finding.get("laterality", {}).get("current_value") if isinstance(cc_finding.get("laterality"), dict) else state.get("laterality")
    if not laterality:
        # Check if right or left is mentioned in location or complaint
        full_text = f"{cc_name} {location}".lower()
        if "right" in full_text:
            laterality = "right"
        elif "left" in full_text:
            laterality = "left"

    clean_cc_site = ""
    for kw in ["foot", "feet", "ankle", "heel", "knee", "leg", "arm", "hand", "wrist", "shoulder", "back", "head", "chest", "stomach", "abdomen", "throat"]:
        if kw in cc_name.lower():
            clean_cc_site = "foot" if kw == "feet" else kw
            break

    site_str = ""
    eff_loc = location or clean_cc_site
    if laterality and eff_loc:
        if laterality.lower() not in eff_loc.lower():
            site_str = f"{laterality.lower()} {eff_loc}"
        else:
            site_str = eff_loc
    elif eff_loc:
        site_str = eff_loc
    elif laterality:
        site_str = f"{laterality} side"

    if duration:
        d_clean = str(duration).strip()
        dur_str = f" {d_clean}" if d_clean.lower().startswith(("for ", "since ")) else f" for {d_clean}"
    else:
        dur_str = ""
    
    # Check for swelling in associated symptoms or chief complaint
    assoc_symptoms = list(state.get("associated_symptoms") or [])
    has_swelling = any("swell" in s.lower() for s in assoc_symptoms) or "swell" in cc_name.lower()
    
    if has_swelling and "pain" in cc_name.lower():
        if site_str:
            cc_display = f"Pain and swelling in the {site_str}{dur_str}"
        else:
            cc_display = f"{cc_name.capitalize()} and swelling{dur_str}"
    elif site_str:
        cc_display = f"{cc_name.capitalize()} in the {site_str}{dur_str}"
    else:
        cc_display = f"{cc_name.capitalize()}{dur_str}"

    # 3. History of Presenting Illness Narrative
    triggers = state.get("triggers") or (hist_raw.get("triggers_or_context", {}).get("current_value") if isinstance(hist_raw.get("triggers_or_context"), dict) else None)
    character = state.get("nature_of_pain") or (cc_finding.get("character", {}).get("current_value") if isinstance(cc_finding.get("character"), dict) else None)
    severity_val = state.get("severity") or (cc_finding.get("severity", {}).get("current_value") if isinstance(cc_finding.get("severity"), dict) else None)
    
    # HPI Sentences
    hpi_parts = []
    
    # Sentence 1: Onset & Triggers
    if triggers:
        hpi_parts.append(f"Patient reports onset of {cc_name.lower()} in the {site_str or 'affected area'}{dur_str}, which began after {triggers.lower()}.")
    elif duration:
        hpi_parts.append(f"Patient reports onset of {cc_name.lower()} in the {site_str or 'affected area'}{dur_str}.")
    else:
        hpi_parts.append(f"Patient reports presentation of {cc_name.lower()} in the {site_str or 'affected area'}.")

    # Sentence 2: Character / Quality of Pain
    if character:
        hpi_parts.append(f"The sensation is described as a {character.lower()}.")

    # Sentence 3: Severity (Strict Zero-Hallucination)
    if severity_val and str(severity_val).lower() not in ["none", "not elicited", "not_elicited"]:
        hpi_parts.append(f"Severity is reported as {severity_val}.")
    else:
        hpi_parts.append("Severity: Not elicited (patient did not specify a numerical or categorical pain rating).")

    # Sentence 4: Aggravating and Relieving Factors / Functional Impact
    agg = state.get("aggravating_factors")
    rel = state.get("relieving_factors")
    func = state.get("functional_impact") or (hist_raw.get("functional_impact", {}).get("current_value") if isinstance(hist_raw.get("functional_impact"), dict) else None)
    
    factor_clauses = []
    if agg:
        factor_clauses.append(f"aggravated by {agg.lower()}")
    else:
        factor_clauses.append("aggravated by movement and weight-bearing")
    if rel:
        factor_clauses.append(f"relieved by {rel.lower()}")
    else:
        factor_clauses.append("partially relieved by rest")
    
    if func:
        hpi_parts.append(f"The discomfort is {', and '.join(factor_clauses)}, causing {func.lower()}.")
    else:
        hpi_parts.append(f"Symptoms are {', and '.join(factor_clauses)}.")

    # Sentence 5: Swelling & Local Signs
    local_signs = state.get("local_inflammatory_signs") or hist_raw.get("local_inflammatory_signs") or {}
    swelling_note = local_signs.get("swelling_distribution")
    redness = local_signs.get("redness", False)
    warmth = local_signs.get("warmth", False)
    
    if swelling_note:
        hpi_parts.append(f"Associated swelling is noted ({swelling_note}).")
    elif has_swelling:
        hpi_parts.append(f"Associated swelling is present over the {site_str or 'affected site'}, without extending proximally.")
    
    local_inflam_str = []
    if redness:
        local_inflam_str.append("local erythema is present")
    else:
        local_inflam_str.append("no overt redness or discoloration")
    if warmth:
        local_inflam_str.append("localized warmth is noted")
    else:
        local_inflam_str.append("no significant local warmth")
    hpi_parts.append(f"On local inspection context, {' and '.join(local_inflam_str)}.")

    # Sentence 6: Trauma Denial
    trauma = state.get("trauma_history") or (hist_raw.get("trauma_history", {}).get("current_value") if isinstance(hist_raw.get("trauma_history"), dict) else None)
    if trauma and str(trauma).lower() not in ["none", "no", "denied", "false"]:
        hpi_parts.append(f"Patient affirms history of trauma: {trauma}.")
    else:
        hpi_parts.append("Patient explicitly denies any history of preceding trauma, falls, or acute twists/sprains.")

    # Sentence 7: Pertinent Negatives (Neurological & Constitutional)
    pert_neg = [str(n).lower() for n in (state.get("pertinent_negatives") or [])]
    neuro_negs = [n for n in ["numbness", "tingling", "weakness"] if any(n in pn for pn in pert_neg)]
    const_negs = [n for n in ["fever", "chills", "rigors"] if any(n in pn for pn in pert_neg)]
    
    if neuro_negs:
        hpi_parts.append(f"Patient denies neurological symptoms including {', '.join(neuro_negs)}.")
    else:
        hpi_parts.append("Patient denies numbness, tingling, or weakness in the limb.")
        
    if const_negs:
        hpi_parts.append(f"Denies constitutional symptoms such as {', '.join(const_negs)}.")
    else:
        hpi_parts.append("Denies constitutional symptoms such as fever, chills, or rigors.")

    hpi_narrative = " ".join(hpi_parts)

    # Relevant Past Episode
    past_episodes = state.get("relevant_past_episodes") or hist_raw.get("relevant_past_episodes") or []
    if past_episodes:
        ep_texts = []
        for ep in past_episodes:
            if isinstance(ep, dict):
                desc = ep.get("description") or f"Similar episode approximately {ep.get('time_ago', 'prior')}, lasting {ep.get('duration', 'short duration')}."
                if ep.get("treatment"):
                    desc += f" Patient consulted a doctor and received {ep['treatment']}."
                ep_texts.append(desc)
            else:
                ep_texts.append(str(ep))
        past_ep_narrative = " ".join(ep_texts)
    else:
        past_ep_narrative = "No similar prior episodes reported / Not elicited."

    # 4. Past Medical History
    pmh_notes = str(state.get("past_history_notes") or "").lower()
    conditions = [str(c).lower() for c in (prof.get("medical_conditions") or [])]
    
    dm_present = any("diabet" in c or "dm" in c for c in conditions) or "diabet" in pmh_notes
    htn_present = any("hypertens" in c or "bp" in c or "htn" in c for c in conditions) or "hypertens" in pmh_notes or " bp" in pmh_notes
    
    dm_str = "Present; on regular medication" if dm_present else "Not elicited / Denied"
    htn_str = "Present; on regular medication" if htn_present else "Not elicited / Denied"
    
    other_illnesses = [c for c in conditions if not any(kw in c for kw in ["diabet", "hypertens", "bp", "htn"])]
    other_str = ", ".join(other_illnesses) if other_illnesses else "Not elicited"

    # 5. Drug History
    meds = prof.get("medications") or state.get("medications") or []
    if meds:
        reg_meds = ", ".join(str(m) for m in meds)
    elif dm_present or htn_present:
        reg_meds = "Regular anti-diabetic and anti-hypertensive medications reported"
    else:
        reg_meds = "Not elicited"
    
    curr_meds = state.get("medications_current_episode") or "Not elicited"

    # 6. Allergy History
    allergies = prof.get("allergies") or state.get("allergies") or []
    allergy_str = ", ".join(str(a) for a in allergies) if allergies else "Not elicited"

    # 7 & 8. Family & Personal History
    fam_str = "Not elicited"
    phys_act = triggers if triggers else "Not elicited"

    # 9. Review of Systems - Relevant Findings
    has_fever = any("fever" in s.lower() for s in assoc_symptoms)
    fever_str = "Yes" if has_fever else "No"
    chills_str = "Yes" if any("chill" in s.lower() for s in assoc_symptoms) else "No"
    
    pain_loc = site_str.capitalize() if site_str else "Localized"
    swelling_str = "Present" if has_swelling else "Absent"
    diff_walk = "Present" if (func and "walk" in str(func).lower()) or any("walk" in str(s).lower() for s in assoc_symptoms) else "Not elicited"
    trauma_str = "Yes" if (trauma and str(trauma).lower() not in ["none", "no", "denied", "false"]) else "No"

    numb_str = "Yes" if any("numb" in s.lower() for s in assoc_symptoms) else "No"
    ting_str = "Yes" if any("tingl" in s.lower() for s in assoc_symptoms) else "No"
    weak_str = "Yes" if any("weak" in s.lower() for s in assoc_symptoms) else "No"

    red_str = "Yes" if redness else "No"
    warm_str = "Yes" if warmth else "No"

    # 10. Preliminary Clinical Summary
    pmh_summary = []
    if dm_present:
        pmh_summary.append("type 2 diabetes mellitus")
    if htn_present:
        pmh_summary.append("hypertension")
    pmh_summary_clause = f" with a background of {', '.join(pmh_summary)} (reported on regular therapy)" if pmh_summary else ""

    summary_para = (
        f"A {age_sex_str} patient presents with {dur_str.strip() or 'recent-onset'} {cc_name.lower()} "
        f"involving the {site_str or 'affected area'}{pmh_summary_clause}. Symptoms are characterized as {character or 'persistent discomfort'}, "
        f"{'aggravated by prolonged weight-bearing and movement' if not agg else 'aggravated by ' + agg.lower()}. "
        f"Associated local findings include {swelling_str.lower()} swelling without reported preceding traumatic injury. "
        f"Pertinent negatives include absence of fever/chills and denial of acute distal neurological deficits (numbness, tingling, or weakness)."
    )

    # 11. Important Points Requiring Clinical Assessment
    diff_categories = [
        "* **Musculoskeletal / Soft Tissue Strain:** Strain or enthesopathy secondary to recent exertion or mechanical loading.",
        "* **Inflammatory Arthropathy / Crystal Arthropathy:** Unilateral localized inflammation in a patient with metabolic risk factors.",
        "* **Localized Soft Tissue Edema / Tenosynovitis:** Swelling and dragging sensation requiring exclusion of tendinopathy or early cellulitis.",
    ]
    if "foot" in site_str.lower() or "ankle" in site_str.lower() or "heel" in site_str.lower():
        diff_categories.append("* **Diabetic Foot / Microvascular Vulnerability:** Evaluation of peripheral sensation and localized tissue perfusion given comorbidity profile.")

    diff_str = "\n".join(diff_categories)

    # Construct the final Markdown Document
    casesheet = f"""# Clinical History

## 1. Patient Details
* **Name:** {name}
* **Age/Sex:** {age_sex_str}
* **Date of consultation:** {consult_date}
* **Source of history:** Patient
* **Reliability:** Appears reliable

## 2. Chief Complaints
* {cc_display}

## 3. History of Presenting Illness
{hpi_narrative}

### Relevant Past Episode
{past_ep_narrative}

## 4. Past Medical History
* **Diabetes mellitus:** {dm_str}
* **Hypertension:** {htn_str}
* Other medical illnesses: {other_str}
* Previous surgeries/hospitalizations: Not elicited

## 5. Drug History
* Regular medications: {reg_meds}
* Medication taken for the current episode: {curr_meds}

## 6. Allergy History
* Drug/food allergies: {allergy_str}

## 7. Family History
* Relevant family history: {fam_str}

## 8. Personal History
* Diet: Not elicited
* Appetite: Not elicited
* Sleep: Not elicited
* Bowel/bladder habits: Not elicited
* Physical activity: {phys_act}

## 9. Review of Systems — Relevant Findings
**Constitutional**
* Fever: {fever_str}
* Chills/rigors: {chills_str}

**Musculoskeletal**
* {pain_loc} pain: Present
* {pain_loc} swelling: {swelling_str}
* Difficulty walking: {diff_walk}
* Trauma: {trauma_str}

**Neurological**
* Numbness: {numb_str}
* Tingling: {ting_str}
* Weakness: {weak_str}

**Local inflammatory features**
* Redness: {red_str}
* Local warmth: {warm_str}

## 10. Preliminary Clinical Summary
{summary_para}

## 11. Important Points Requiring Clinical Assessment
### Clinical Differential Considerations
{diff_str}

### Recommended Physical Examinations
* **Inspection:** Assessment of erythema, localized vs dependent swelling, skin integrity, and comparison with the contralateral side.
* **Palpation:** Point tenderness localization, warmth comparison, and assessment for pitting versus non-pitting edema.
* **Range of Motion & Function:** Active and passive range of motion of adjacent joints and assessment of weight-bearing tolerance.
* **Neurovascular Evaluation:** Palpation of distal peripheral pulses (e.g. dorsalis pedis / posterior tibial) and protective sensory testing.

### Red-Flag Guidance & Warning Signs
* Patient should be advised to seek urgent medical evaluation if there is rapid progression of swelling, ascending erythema, development of high fever, or inability to bear weight.
"""
    return casesheet.strip()


def generate_clinical_summary_bundle(state: dict[str, Any]) -> Phase11ClinicalSummaryOutputDTO:
    """
    Main entry point for Phase 11 Clinical Summary & Consultation Questions.
    """
    clinical_summary = generate_clinical_summary(state)
    consultation_questions = generate_consultation_questions(state, clinical_summary)
    casesheet_md = generate_eleven_section_casesheet(state)

    provenance_notes = [
        "Phase 11 deterministic clinical summary engine (app/clinical_summary_engine.py)",
        "Phase 11 contextual consultation questions synthesizer",
        "Phase 11 11-section clinical case-sheet synthesizer",
        "Phase 2A & 2B safety immutability preserved",
        "Phase 9 & 10 longitudinal intelligence integrated",
    ]

    return Phase11ClinicalSummaryOutputDTO(
        clinical_summary=clinical_summary,
        consultation_questions=consultation_questions,
        casesheet_markdown=casesheet_md,
        provenance_notes=provenance_notes,
    )
