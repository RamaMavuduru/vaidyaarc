"""
Phase 3: Clinical Case Representation Node.

Transforms VaidyaArcState into a structured, physician-ready clinical case.
Fully deterministic; no LLM involvement.
"""

from datetime import datetime
from typing import Any

from app.nodes import _find_complaint_template, FALLBACK_REQUIRED_FIELDS, _field_has_value
from app.state import VaidyaArcState
from app.clinical_case_schema import (
    ClinicalCase,
    ClinicalCaseOutput,
    PatientIdentifier,
    SymptomDescriptors,
    SafetyFindings,
    RiskAssessment,
    DataQuality,
)


def _generate_case_id(patient_id: str, session_id: str) -> str:
    """Generate deterministic case ID from patient and session."""
    return f"{patient_id}_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _build_complaint_narrative(state: VaidyaArcState) -> str:
    """Build structured narrative of chief complaint."""
    chief_complaint = state.get("chief_complaint")
    severity = state.get("severity")
    duration = state.get("duration")
    nature = state.get("nature_of_pain")
    location = state.get("location")
    
    if not chief_complaint:
        return "No chief complaint recorded."
    
    parts = [chief_complaint]
    
    if severity:
        parts.append(f"Severity: {severity}")
    
    if duration:
        parts.append(f"Duration: {duration}")
    
    if nature:
        parts.append(f"Character: {nature}")
    
    if location:
        parts.append(f"Location: {location}")
    
    return ". ".join(parts) + "."


def _calculate_completeness_score(state: VaidyaArcState) -> float:
    """Calculate data completeness as percentage based on complaint-specific requirements."""
    if state.get("information_complete") and not (state.get("missing_information") or []):
        return 100.0

    complaint = state.get("chief_complaint")
    if not complaint:
        return 0.0

    template = _find_complaint_template(complaint)
    required_fields = template["required_fields"] if template else FALLBACK_REQUIRED_FIELDS

    if not required_fields:
        return 100.0

    populated_count = 0
    for field in required_fields:
        if _field_has_value(state.get(field)):
            populated_count += 1

    percentage = (populated_count / len(required_fields)) * 100.0
    return round(percentage, 1)


def _determine_care_pathway_status(
    immediate_attention: bool,
    risk_level: str,
    information_complete: bool,
) -> str:
    """Deterministically route to care pathway."""
    if immediate_attention:
        return "emergency"
    
    if not information_complete:
        return "incomplete"
    
    if risk_level in ["HIGH", "URGENT"]:
        return "urgent"
    
    if risk_level in ["MODERATE", "LOW"]:
        return "routine"
    
    return "follow_up"


def _generate_case_summary(state: VaidyaArcState) -> str:
    """
    Generate deterministic physician-ready summary.
    
    Pure factual narrative from structured fields.
    NO DIAGNOSIS. NO TREATMENT RECOMMENDATIONS.
    """
    chief_complaint = state.get("chief_complaint")
    age = state.get("patient_profile", {}).get("age")
    severity = state.get("severity")
    duration = state.get("duration")
    associated_symptoms = state.get("associated_symptoms", [])
    risk_level = state.get("risk_level")
    immediate_attention = state.get("immediate_attention_required", False)
    
    if not chief_complaint:
        return "Insufficient information for clinical summary."
    
    # Build deterministic summary: facts only, no inference
    summary_parts = []
    
    # Age and complaint
    if age:
        summary_parts.append(f"{age}-year-old patient presenting with {chief_complaint}")
    else:
        summary_parts.append(f"Patient presenting with {chief_complaint}")
    
    # Duration
    if duration:
        summary_parts.append(f"Duration: {duration}")
    
    # Severity
    if severity:
        summary_parts.append(f"Severity: {severity}")
    
    # Associated symptoms
    if associated_symptoms:
        summary_parts.append(f"Associated symptoms: {', '.join(associated_symptoms)}")
    
    # Risk level
    if risk_level:
        summary_parts.append(f"Risk assessment: {risk_level}")
    
    # Emergency flag
    if immediate_attention:
        summary_parts.append("REQUIRES IMMEDIATE ATTENTION")
    
    summary = ". ".join(summary_parts) + "."
    
    # Limit to 2-3 sentences if too long
    if len(summary) > 300:
        summary = ". ".join(summary_parts[:3]) + "."
    
    return summary


def _build_next_steps(
    immediate_attention: bool,
    risk_level: str,
    information_complete: bool,
    missing_information: list[str],
) -> list[str]:
    """Generate deterministic next steps."""
    steps = []
    
    if immediate_attention:
        steps.append("Requires immediate clinical evaluation")
        steps.append("Consider emergency department referral")
    elif risk_level in ["HIGH", "URGENT"]:
        steps.append("Prompt clinical consultation recommended")
        steps.append("Reassess if symptoms worsen")
    elif risk_level == "MODERATE":
        steps.append("Clinical review and close follow-up")
        steps.append("Reassess if symptoms persist or worsen")
    else:
        steps.append("Routine follow-up and monitoring")
    
    if not information_complete and missing_information:
        steps.append(f"Collect additional information: {', '.join(missing_information)}")
    else:
        steps.append("Case ready for physician review")
    
    return steps


def clinical_case_representation(state: VaidyaArcState) -> dict[str, Any]:
    """
    Phase 3: Clinical Case Representation.
    
    Transforms VaidyaArcState into structured clinical case without diagnosis.
    
    Input: Complete VaidyaArcState from Phase 2B
    Output: Updated state with clinical_case, clinical_case_output, etc.
    """
    
    errors = []
    warnings = []
    
    try:
        # ===== VALIDATION =====
        if not state.get("patient_id"):
            errors.append("Missing patient_id")
        if not state.get("session_id"):
            errors.append("Missing session_id")
        if state.get("red_flag_status") is None:
            errors.append("Missing red_flag_status from Phase 2A")
        if state.get("risk_level") is None:
            errors.append("Missing risk_level from Phase 2B")
        if state.get("risk_score") is None:
            errors.append("Missing risk_score from Phase 2B")
        
        # ===== EXTRACT PATIENT CONTEXT =====
        patient_id = state.get("patient_id", "UNKNOWN")
        session_id = state.get("session_id", "UNKNOWN")
        patient_profile = state.get("patient_profile", {})
        
        patient_identifier = PatientIdentifier(
            patient_id=patient_id,
            session_id=session_id,
            age=patient_profile.get("age"),
            known_conditions=patient_profile.get("medical_conditions", []),
            known_allergies=patient_profile.get("allergies", []),
        )
        
        # ===== BUILD COMPLAINT NARRATIVE =====
        complaint_narrative = _build_complaint_narrative(state)
        
        # ===== EXTRACT SYMPTOM DESCRIPTORS =====
        symptom_descriptors = SymptomDescriptors(
            severity=state.get("severity"),
            character=state.get("nature_of_pain"),
            location=state.get("location"),
            associated_symptoms=state.get("associated_symptoms", []),
        )
        
        # ===== SUMMARIZE MEDICAL HISTORY =====
        medical_history_summary = []
        medical_conditions = patient_profile.get("medical_conditions", [])
        if medical_conditions:
            medical_history_summary = [f"Known condition: {cond}" for cond in medical_conditions]
        
        relevant_history_notes = []
        previous_history = state.get("previous_history", [])
        if previous_history:
            relevant_history_notes = [
                f"Prior history: {item.get('description', str(item))}"
                for item in previous_history
            ]
        
        # ===== COPY PHASE 2A FINDINGS (UNMODIFIED) =====
        safety_findings = SafetyFindings(
            red_flag_status=state.get("red_flag_status", "no_obvious_red_flags"),
            red_flags_detected=state.get("red_flags", []),
            red_flag_evidence=state.get("red_flag_evidence", []),
            immediate_attention_required=state.get("immediate_attention_required", False),
            red_flag_rule_summary=state.get("red_flag_rule_hits", []),
        )
        
        # ===== COPY PHASE 2B FINDINGS (UNMODIFIED) =====
        risk_assessment = RiskAssessment(
            risk_level=state.get("risk_level", "LOW"),
            risk_score=state.get("risk_score", 0),
            risk_signals=state.get("risk_signal_summary", []),
            risk_factors=state.get("risk_contributing_factors", []),
            risk_evidence=state.get("risk_evidence", []),
            risk_reasoning=state.get("risk_reasoning", "No risk reasoning available"),
            risk_override_reason=state.get("risk_override_reason"),
            recommended_action=state.get("recommended_next_action", "Follow-up assessment"),
        )
        
        # ===== CALCULATE DATA QUALITY =====
        completeness_pct = _calculate_completeness_score(state)
        missing_fields = state.get("missing_information", [])
        
        data_quality = DataQuality(
            information_complete=state.get("information_complete", False),
            completeness_percentage=completeness_pct,
            missing_fields=missing_fields,
            uncertain_fields=[],
            data_gaps=missing_fields if missing_fields else [],
        )
        
        # ===== DETERMINE CARE PATHWAY STATUS =====
        care_pathway_status = _determine_care_pathway_status(
            immediate_attention=safety_findings.immediate_attention_required,
            risk_level=risk_assessment.risk_level,
            information_complete=data_quality.information_complete,
        )
        
        # ===== GENERATE CASE SUMMARY =====
        case_summary = _generate_case_summary(state)
        
        # ===== BUILD NEXT STEPS =====
        next_steps = _build_next_steps(
            immediate_attention=safety_findings.immediate_attention_required,
            risk_level=risk_assessment.risk_level,
            information_complete=data_quality.information_complete,
            missing_information=missing_fields,
        )
        
        # ===== DETERMINE FOLLOW-UP REQUIRED =====
        follow_up_required = care_pathway_status in ["emergency", "urgent", "routine"]
        
        # ===== BUILD TRACEABILITY =====
        source_phase_evidence = {
            "phase_1b": [
                f"chief_complaint: {state.get('chief_complaint')}",
                f"duration: {state.get('duration')}",
                f"severity: {state.get('severity')}",
            ],
            "phase_2a": [f"red_flag_status: {state.get('red_flag_status')}"],
            "phase_2b": [f"risk_level: {state.get('risk_level')}", f"risk_score: {state.get('risk_score')}"],
        }
        
        # ===== CREATE CLINICAL CASE =====
        case_id = _generate_case_id(patient_id, session_id)
        
        clinical_case = ClinicalCase(
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            case_status="complete" if data_quality.information_complete else "incomplete",
            patient_identifier=patient_identifier,
            chief_complaint=state.get("chief_complaint"),
            complaint_narrative=complaint_narrative,
            onset_description=state.get("duration"),
            symptom_descriptors=symptom_descriptors,
            medical_history_summary=medical_history_summary,
            relevant_history_notes=relevant_history_notes,
            safety_findings=safety_findings,
            risk_assessment=risk_assessment,
            data_quality=data_quality,
            care_pathway_status=care_pathway_status,
            case_summary=case_summary,
            next_steps=next_steps,
            follow_up_required=follow_up_required,
            source_phase_evidence=source_phase_evidence,
        )
        
        # ===== VALIDATION CHECKS =====
        # Consistency: High risk without red flags should trigger warning
        if (risk_assessment.risk_level in ["HIGH", "URGENT"] and
            not safety_findings.immediate_attention_required):
            warnings.append(
                "High/URGENT risk without immediate attention flag - ensure this is intentional"
            )
        
        # Consistency: Emergency pathway requires immediate attention
        if care_pathway_status == "emergency" and not safety_findings.immediate_attention_required:
            warnings.append("Emergency pathway but immediate_attention_required is False")
        
        # ===== CREATE OUTPUT =====
        case_ready_for_review = (
            data_quality.information_complete and len(errors) == 0
        )
        
        clinical_case_output = ClinicalCaseOutput(
            case_representation=clinical_case,
            validation_errors=errors,
            validation_warnings=warnings,
            case_ready_for_review=case_ready_for_review,
            formatting_version="phase3_v1",
        )
        
        # ===== RETURN UPDATED STATE =====
        return {
            "clinical_case": clinical_case.model_dump(),
            "clinical_case_output": clinical_case_output.model_dump(),
            "case_generation_status": "generated",
            "case_validation_errors": errors,
        }
    
    except Exception as e:
        # If case generation fails, return error state
        error_msg = str(e)
        return {
            "clinical_case": None,
            "clinical_case_output": None,
            "case_generation_status": "failed",
            "case_validation_errors": [f"Case generation failed: {error_msg}"],
        }
