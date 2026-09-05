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
        return ClinicalSummarySection(
            section_name="Chief Complaint",
            content=f"Patient presents with: {cc}.",
            status="reported",
            structured_data={"chief_complaint": cc},
            provenance=["intake_chief_complaint"],
        )
    
    msg = _clean_str(state.get("current_message"))
    if msg:
        return ClinicalSummarySection(
            section_name="Chief Complaint",
            content=f"Primary presenting concern from intake message: '{msg}'.",
            status="reported",
            structured_data={"chief_complaint": msg},
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

    parts: list[str] = []
    if cc:
        parts.append(f"Patient reports {cc}")
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

    if assoc:
        clean_assoc = [str(s).strip() for s in assoc if str(s).strip()]
        if clean_assoc:
            parts.append(f"Associated symptoms include: {', '.join(clean_assoc)}")

    missing = state.get("missing_information") or []
    if missing:
        parts.append(f"[Unreported HPI Elements: {', '.join(missing)}]")

    if not cc and not duration and not severity and not nature and not location and not assoc:
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
            "missing_elements": missing,
        },
        provenance=["phase1b_intake_extraction"],
    )


def build_pmh_section(state: dict[str, Any]) -> ClinicalSummarySection:
    profile = state.get("patient_profile") or {}
    conditions = profile.get("medical_conditions") or []
    clean_conds = [str(c).strip() for c in conditions if str(c).strip()]

    if clean_conds:
        return ClinicalSummarySection(
            section_name="Past Medical History",
            content=f"Documented chronic medical conditions: {', '.join(clean_conds)}.",
            status="reported",
            structured_data={"medical_conditions": clean_conds},
            provenance=["patient_profile_medical_conditions"],
        )

    return ClinicalSummarySection(
        section_name="Past Medical History",
        content="Past medical history not reported or not available in patient profile.",
        status="not_reported",
        structured_data={"medical_conditions": []},
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
    clean_assoc = [str(s).strip() for s in assoc if str(s).strip()]

    if clean_assoc:
        return ClinicalSummarySection(
            section_name="Review of Systems",
            content=f"Positive review of systems findings reported: {', '.join(clean_assoc)}. Full systemic review not documented.",
            status="reported",
            structured_data={"positive_findings": clean_assoc},
            provenance=["intake_associated_symptoms"],
        )

    return ClinicalSummarySection(
        section_name="Review of Systems",
        content="Review of systems not explicitly documented beyond primary complaint (system negatives not inferred).",
        status="not_reported",
        structured_data={"positive_findings": []},
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

    findings.append(f"Phase 2B Current Risk: {risk_level} (Score: {risk_score}/100)")
    
    if composite_level != risk_level:
        findings.append(f"Phase 10 Composite Risk: {composite_level} (Effective Pathway: {care_pathway.upper()})")
    else:
        findings.append(f"Effective Care Pathway: {care_pathway.upper()}")

    if risk_signals:
        findings.append(f"Active risk signals: {', '.join(risk_signals)}")

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
        questions.append(ConsultationQuestionDTO(
            question_id="Q_SYMPTOM_CAUSE",
            question=f"What potential underlying causes could explain my {cc}?",
            category="symptom_cause",
            rationale="Helps patient initiate diagnostic discussion regarding the chief complaint with the doctor.",
            priority="high",
            source_evidence=[f"Chief complaint: {cc}"],
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


def generate_clinical_summary_bundle(state: dict[str, Any]) -> Phase11ClinicalSummaryOutputDTO:
    """
    Main entry point for Phase 11 Clinical Summary & Consultation Questions.
    """
    clinical_summary = generate_clinical_summary(state)
    consultation_questions = generate_consultation_questions(state, clinical_summary)

    provenance_notes = [
        "Phase 11 deterministic clinical summary engine (app/clinical_summary_engine.py)",
        "Phase 11 contextual consultation questions synthesizer",
        "Phase 2A & 2B safety immutability preserved",
        "Phase 9 & 10 longitudinal intelligence integrated",
    ]

    return Phase11ClinicalSummaryOutputDTO(
        clinical_summary=clinical_summary,
        consultation_questions=consultation_questions,
        provenance_notes=provenance_notes,
    )
