"""
Phase 8B: Ayurveda Safety and Eligibility Gate.

Evaluates upstream clinical safety findings (Phase 2A), risk assessment (Phase 2B),
and patient clinical profile to determine whether Ayurveda home remedies or
pharmacopoeial formulations are safe and eligible for presentation.

SAFETY INVARIANTS:
1. Phase 2A emergency/red-flags strictly BLOCK Ayurveda recommendations (0 overrides).
2. Phase 2B critical/urgent risk strictly BLOCKS Ayurveda recommendations.
3. Severe/extreme symptom presentations are BLOCKED from home remedy recommendation.
4. Unknown patient context (allergies, pregnancy) is PRESERVED as unknown.
5. Ingredients matching documented patient allergies are strictly BLOCKED.
"""

from typing import Any, Optional

from app.ayurveda_knowledge_schema import (
    AyurvedaKnowledgeRecord,
    AyurvedaEligibilityStatus,
    SafetyScreeningDecision,
)


def evaluate_safety_and_eligibility(
    state: dict[str, Any],
    candidate_record: Optional[AyurvedaKnowledgeRecord] = None,
) -> SafetyScreeningDecision:
    """
    Executes multi-factor safety screening against patient state and candidate remedy.
    """
    reasons: list[str] = []
    missing_safety_fields: list[str] = []
    is_emergency_blocked = False
    is_risk_blocked = False
    is_contraindication_blocked = False

    # Extract upstream signals
    immediate_attention = bool(state.get("immediate_attention_required", False))
    red_flag_status = state.get("red_flag_status", "no_obvious_red_flags")
    red_flags = list(state.get("red_flags") or [])

    risk_level = str(state.get("risk_level") or "LOW").upper()
    severity = str(state.get("severity") or "").lower()
    
    profile = state.get("patient_profile") or {}
    patient_allergies = [a.lower() for a in (profile.get("allergies") or [])]
    patient_conditions = [c.lower() for c in (profile.get("medical_conditions") or [])]
    pregnancy_status = profile.get("pregnancy_status")

    # Track unknown safety context
    if not profile.get("allergies"):
        missing_safety_fields.append("allergies_unspecified")
    if pregnancy_status is None:
        missing_safety_fields.append("pregnancy_status_unspecified")

    # -------------------------------------------------------------
    # RULE 1: Phase 2A Emergency Safety Block (Highest Precedence)
    # -------------------------------------------------------------
    if immediate_attention or red_flag_status == "red_flags_detected":
        is_emergency_blocked = True
        flag_str = ", ".join(red_flags) if red_flags else "Emergency red flag detected"
        reasons.append(f"Phase 2A medical emergency active ({flag_str}). Ayurveda remedy recommendations are strictly blocked.")
        return SafetyScreeningDecision(
            status=AyurvedaEligibilityStatus.BLOCKED,
            reasons=reasons,
            is_emergency_blocked=True,
            is_risk_blocked=False,
            is_contraindication_blocked=False,
            missing_safety_fields=missing_safety_fields,
        )

    # -------------------------------------------------------------
    # RULE 2: Phase 2B Risk Convergence Block
    # -------------------------------------------------------------
    if risk_level in ["URGENT", "CRITICAL", "HIGH"]:
        is_risk_blocked = True
        reasons.append(f"High clinical risk level ('{risk_level}') requires formal medical evaluation. Home remedy recommendation is blocked.")
        return SafetyScreeningDecision(
            status=AyurvedaEligibilityStatus.BLOCKED,
            reasons=reasons,
            is_emergency_blocked=False,
            is_risk_blocked=True,
            is_contraindication_blocked=False,
            missing_safety_fields=missing_safety_fields,
        )

    # -------------------------------------------------------------
    # RULE 3: Severe Symptom Presentation Block
    # -------------------------------------------------------------
    is_severe = False
    if any(term in severity for term in ["severe", "very severe", "extreme", "worst", "unbearable", "high"]):
        is_severe = True
    else:
        for num in ["8", "9", "10"]:
            if num in severity:
                is_severe = True
                break

    if is_severe:
        reasons.append(f"Severe acute symptom presentation ('{severity}') is unsuitable for self-administered home remedies. Formal medical evaluation required.")
        return SafetyScreeningDecision(
            status=AyurvedaEligibilityStatus.BLOCKED,
            reasons=reasons,
            is_emergency_blocked=False,
            is_risk_blocked=True,
            is_contraindication_blocked=False,
            missing_safety_fields=missing_safety_fields,
        )

    # -------------------------------------------------------------
    # RULE 4: Candidate Remedy-Specific Contraindication Checks
    # -------------------------------------------------------------
    if candidate_record:
        # Check ingredient, name, and alias allergy match
        remedy_substances = [i.lower() for i in candidate_record.ingredients] + [candidate_record.name.lower()] + [a.lower() for a in candidate_record.aliases]
        for allergy in patient_allergies:
            for substance in remedy_substances:
                if allergy in substance or substance in allergy:
                    is_contraindication_blocked = True
                    reasons.append(f"Remedy '{candidate_record.name}' matches documented patient allergy '{allergy}' (substance: '{substance}').")
                    break

        # Check explicit record contraindications against patient conditions
        for contra in candidate_record.contraindications:
            contra_lower = contra.lower()
            for cond in patient_conditions:
                if cond in contra_lower:
                    is_contraindication_blocked = True
                    reasons.append(f"Remedy contraindicated for patient condition '{cond}': {contra}")

        # Check procedural/surgical devices (e.g. Ksharasutra)
        if candidate_record.record_id.startswith("API2_FORM_051"):
            reasons.append("Ksharasutra is a surgical procedure requiring specialized operative assessment by a qualified surgeon.")
            return SafetyScreeningDecision(
                status=AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW,
                reasons=reasons,
                is_emergency_blocked=False,
                is_risk_blocked=False,
                is_contraindication_blocked=False,
                missing_safety_fields=missing_safety_fields,
            )

        if is_contraindication_blocked:
            return SafetyScreeningDecision(
                status=AyurvedaEligibilityStatus.BLOCKED,
                reasons=reasons,
                is_emergency_blocked=False,
                is_risk_blocked=False,
                is_contraindication_blocked=True,
                missing_safety_fields=missing_safety_fields,
            )

    # -------------------------------------------------------------
    # RULE 5: Demographic & Unknown Clinical Context Screening
    # -------------------------------------------------------------
    age = profile.get("age")
    sex = str(profile.get("sex") or "").lower()

    # Female childbearing age with unknown pregnancy status
    if sex == "female" and (age is None or (isinstance(age, (int, float)) and 15 <= age <= 50)):
        if pregnancy_status is None or str(pregnancy_status).lower() in ["unknown", "unspecified"]:
            reasons.append("Patient is a female of childbearing age with unknown pregnancy status. Remedies require qualified clinician review.")
            return SafetyScreeningDecision(
                status=AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW,
                reasons=reasons,
                is_emergency_blocked=False,
                is_risk_blocked=False,
                is_contraindication_blocked=False,
                missing_safety_fields=missing_safety_fields,
            )

    # Pediatric age < 12
    if isinstance(age, (int, float)) and age < 12:
        reasons.append(f"Pediatric patient (age {age} < 12). Remedies require pediatric clinical supervision.")
        return SafetyScreeningDecision(
            status=AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW,
            reasons=reasons,
            is_emergency_blocked=False,
            is_risk_blocked=False,
            is_contraindication_blocked=False,
            missing_safety_fields=missing_safety_fields,
        )

    # Default: Eligible
    reasons.append("Mild/moderate presentation with no detected contraindications or safety overrides.")
    return SafetyScreeningDecision(
        status=AyurvedaEligibilityStatus.ELIGIBLE,
        reasons=reasons,
        is_emergency_blocked=False,
        is_risk_blocked=False,
        is_contraindication_blocked=False,
        missing_safety_fields=missing_safety_fields,
    )
