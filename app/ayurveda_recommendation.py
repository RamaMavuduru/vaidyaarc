"""
Phase 8B: Ayurveda Recommendation and Policy Engine.

Translates verified candidate knowledge records and safety screening decisions
into structured, non-prescriptive clinical recommendation outputs.

PIPELINE:
    Clinical Context -> Safety/Risk Gate -> Retrieval -> Eligibility Filtering -> Recommendation Policy
"""

from typing import Any, Optional

from app.ayurveda_knowledge_schema import (
    AyurvedaKnowledgeRecord,
    AyurvedaEligibilityStatus,
    AyurvedaRecommendationItem,
    AyurvedaRecommendationOutput,
    AuthorityLevel,
    RecordType,
)
from app.ayurveda_retriever import get_ayurveda_retriever
from app.ayurveda_safety_gate import evaluate_safety_and_eligibility


def evaluate_ayurveda_recommendations(state: dict[str, Any]) -> AyurvedaRecommendationOutput:
    """
    Main evaluation pipeline for Phase 8B Ayurveda recommendations.
    """
    # 1. Baseline Safety Gate Evaluation
    baseline_decision = evaluate_safety_and_eligibility(state)

    if baseline_decision.status == AyurvedaEligibilityStatus.BLOCKED:
        return AyurvedaRecommendationOutput(
            decision=AyurvedaEligibilityStatus.BLOCKED,
            summary="Ayurveda remedy recommendations are blocked due to clinical safety or risk considerations.",
            recommendations=[],
            blocked_reasons=baseline_decision.reasons,
            safety_findings_summary={
                "red_flag_status": state.get("red_flag_status"),
                "immediate_attention_required": state.get("immediate_attention_required", False),
                "risk_level": state.get("risk_level"),
                "severity": state.get("severity"),
            },
            provenance_sources=[],
        )

    # 2. Candidate Retrieval
    retriever = get_ayurveda_retriever()
    chief_complaint = state.get("chief_complaint")
    associated_symptoms = state.get("associated_symptoms") or []

    candidates = retriever.retrieve_candidates(
        chief_complaint=chief_complaint,
        symptoms=associated_symptoms,
        limit=5
    )

    if not candidates:
        return AyurvedaRecommendationOutput(
            decision=AyurvedaEligibilityStatus.INSUFFICIENT_INFORMATION,
            summary="No verified Ayurveda home remedies or formulations match the reported symptoms in approved sources.",
            recommendations=[],
            blocked_reasons=["No matching indication in approved reference documents."],
            safety_findings_summary={
                "red_flag_status": state.get("red_flag_status"),
                "risk_level": state.get("risk_level"),
            },
            provenance_sources=[],
        )

    # 3. Candidate-Specific Safety & Eligibility Screening
    eligible_items: list[AyurvedaRecommendationItem] = []
    blocked_reasons: list[str] = []
    sources_used: set[str] = set()

    for cand in candidates:
        record: AyurvedaKnowledgeRecord = cand.record
        cand_decision = evaluate_safety_and_eligibility(state, candidate_record=record)

        if cand_decision.status == AyurvedaEligibilityStatus.BLOCKED:
            blocked_reasons.extend(cand_decision.reasons)
            continue

        sources_used.add(record.provenance.source_id)

        # Map remedy type
        if record.record_type == RecordType.HOME_REMEDY:
            remedy_type = "practical_home_remedy"
        elif record.record_type == RecordType.PHARMACOPOEIAL_FORMULATION:
            remedy_type = "pharmacopoeial_reference"
        else:
            remedy_type = "secondary_evidence"

        # Determine preparation summary and dosage reference
        prep = record.preparation_method
        dosage_ref = record.source_dosage_info

        if record.indication_details:
            for detail in record.indication_details:
                if cand.matched_symptom in detail.get("indication", "").lower():
                    if not prep:
                        prep = detail.get("preparation")
                    if not dosage_ref:
                        dosage_ref = detail.get("source_dosage")
                    break

        if not dosage_ref:
            dosage_ref = "As referenced in traditional source monograph / consult physician."

        item = AyurvedaRecommendationItem(
            name=record.name,
            remedy_type=remedy_type,
            matching_symptom=cand.matched_symptom,
            authority_level=record.authority_level.value,
            preparation_summary=prep,
            source_dosage_reference=dosage_ref,
            anupana_reference=record.anupana,
            safety_notes=record.safety_notes + cand_decision.reasons,
            limitations=record.limitations,
            provenance=record.provenance,
        )
        eligible_items.append(item)

    if not eligible_items:
        return AyurvedaRecommendationOutput(
            decision=AyurvedaEligibilityStatus.BLOCKED,
            summary="All retrieved candidate remedies were blocked by safety or allergy constraints.",
            recommendations=[],
            blocked_reasons=blocked_reasons,
            safety_findings_summary={
                "red_flag_status": state.get("red_flag_status"),
                "risk_level": state.get("risk_level"),
            },
            provenance_sources=list(sources_used),
        )

    overall_decision = (
        AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW
        if baseline_decision.status == AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW
        else AyurvedaEligibilityStatus.ELIGIBLE
    )

    summary_msg = (
        f"Identified {len(eligible_items)} source-grounded Ayurveda recommendation(s) for physician review."
        if overall_decision == AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW
        else f"Identified {len(eligible_items)} eligible home remedy/formulation recommendation(s) grounded in approved official sources."
    )

    return AyurvedaRecommendationOutput(
        decision=overall_decision,
        summary=summary_msg,
        recommendations=eligible_items,
        blocked_reasons=blocked_reasons,
        safety_findings_summary={
            "red_flag_status": state.get("red_flag_status"),
            "risk_level": state.get("risk_level"),
            "severity": state.get("severity"),
        },
        provenance_sources=list(sources_used),
    )
