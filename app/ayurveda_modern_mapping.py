"""
Phase 7: Deterministic Ayurveda <-> Modern Medicine Representation Engine.

Translates structured patient intake data into dual-perspective representations:
1. Modern Clinical Perspective (Purely descriptive, zero diagnosis).
2. Ayurvedic Descriptive Perspective (Explicit symptom descriptors, zero diagnosis, no Dosha/Prakriti classification).
3. Explicit Correspondence Layer (Traceable mapping, confidence, uncertainty, non-equivalence warnings).

ZERO-LLM. 100% DETERMINISTIC.
"""

from typing import Any, Optional

from app.ayurveda_modern_schema import (
    RelationshipType,
    MappingConfidence,
    RepresentationStatus,
    ModernSymptomFeature,
    ModernRepresentation,
    AyurvedicConceptMapping,
    AyurvedicAssessmentPlaceholder,
    AyurvedicRepresentation,
    CorrespondenceItem,
    CorrespondenceLayer,
    Phase7SafetyConstraints,
    AyurvedaModernOutput,
)
from app.ayurveda_knowledge_base import (
    AYURVEDA_KB_VERSION,
    AYURVEDA_KB_ENTRIES,
    AyurvedicKBEntry,
    lookup_ayurvedic_concepts,
)


VAGUE_INPUT_KEYWORDS = {
    "not feeling good",
    "not feeling well",
    "unwell",
    "sick",
    "bad",
    "don't feel good",
    "dont feel good",
    "not good",
    "something wrong",
    "feel bad",
    "not okay",
    "i feel fine",
    "fine",
    "okay",
}


def is_vague_observation(text: Optional[str]) -> bool:
    """Checks if a text string is too vague to form a specific clinical observation."""
    if not text:
        return True
    cleaned = text.strip().lower()
    if not cleaned:
        return True
    if len(cleaned) < 3:
        return True
    for kw in VAGUE_INPUT_KEYWORDS:
        if kw in cleaned or cleaned in kw:
            return True
    return False


def build_modern_representation(state: dict[str, Any]) -> ModernRepresentation:
    """
    Constructs the modern clinical representation strictly from structured state fields.
    Does NOT infer or generate modern disease diagnoses.
    """
    chief_complaint = state.get("chief_complaint")
    nature_of_pain = state.get("nature_of_pain")
    location = state.get("location")
    duration = state.get("duration")
    severity = state.get("severity")
    associated_symptoms = state.get("associated_symptoms") or []

    features: list[ModernSymptomFeature] = []

    # 1. Primary complaint feature
    if chief_complaint and not is_vague_observation(chief_complaint):
        features.append(
            ModernSymptomFeature(
                symptom_name=chief_complaint,
                character=nature_of_pain,
                location=location,
                duration=duration,
                severity=severity,
                source_field="chief_complaint",
                raw_evidence=chief_complaint,
            )
        )

    # 2. Associated symptom features
    for sym in associated_symptoms:
        if sym and not is_vague_observation(sym):
            features.append(
                ModernSymptomFeature(
                    symptom_name=sym,
                    character=None,
                    location=None,
                    duration=duration,
                    severity=None,
                    source_field="associated_symptoms",
                    raw_evidence=sym,
                )
            )

    # Safety and risk metadata preservation
    red_flag_status = state.get("red_flag_status") or "no_obvious_red_flags"
    immediate_attention = bool(state.get("immediate_attention_required", False))
    risk_level = state.get("risk_level")
    risk_score = state.get("risk_score")

    traceability = {
        "chief_complaint_source": "state.chief_complaint",
        "nature_of_pain_source": "state.nature_of_pain",
        "location_source": "state.location",
        "duration_source": "state.duration",
        "severity_source": "state.severity",
        "associated_symptoms_source": "state.associated_symptoms",
        "red_flag_source": "Phase 2A evaluate_red_flags",
        "risk_source": "Phase 2B risk_convergence",
    }

    return ModernRepresentation(
        chief_complaint=chief_complaint,
        symptom_features=features,
        duration=duration,
        severity=severity,
        location=location,
        nature_of_pain=nature_of_pain,
        associated_symptoms=associated_symptoms,
        red_flag_status=red_flag_status,
        immediate_attention_required=immediate_attention,
        risk_level=risk_level,
        risk_score=risk_score,
        source_traceability=traceability,
    )


def build_ayurvedic_representation(
    state: dict[str, Any],
    modern_rep: ModernRepresentation
) -> tuple[AyurvedicRepresentation, list[str]]:
    """
    Constructs the Ayurvedic descriptive representation by matching patient-reported
    observations against the curated, versioned knowledge base (AYURVEDA_KB_V1).

    Returns (AyurvedicRepresentation, list_of_raw_tokens).
    """
    raw_tokens: list[str] = []

    if state.get("chief_complaint"):
        raw_tokens.append(state["chief_complaint"])
    if state.get("nature_of_pain"):
        raw_tokens.append(state["nature_of_pain"])
    if state.get("location"):
        raw_tokens.append(state["location"])
    for sym in (state.get("associated_symptoms") or []):
        if sym:
            raw_tokens.append(sym)

    # Filter out empty/vague
    valid_tokens = [t for t in raw_tokens if not is_vague_observation(t)]

    # Deterministic lookup in KB
    matched_entries = lookup_ayurvedic_concepts(valid_tokens)

    mapped_concepts: list[AyurvedicConceptMapping] = []
    matched_token_set: set[str] = set()

    for entry in matched_entries:
        # Determine which tokens triggered this entry
        triggering_tokens: list[str] = []
        for token in valid_tokens:
            clean = token.strip().lower()
            for kw in entry.trigger_keywords:
                if kw in clean or clean in kw:
                    triggering_tokens.append(token)
                    matched_token_set.add(token)
                    break

        # Calculate descriptive mapping confidence (NOT disease confidence)
        if len(triggering_tokens) >= 2 or any(token.strip().lower() in entry.trigger_keywords for token in triggering_tokens):
            confidence = MappingConfidence.HIGH
        elif len(triggering_tokens) == 1:
            confidence = MappingConfidence.MODERATE
        else:
            confidence = MappingConfidence.LIMITED

        limitations_list = list(entry.limitations)
        limitations_list.append(f"Mapped strictly under {AYURVEDA_KB_VERSION} descriptive taxonomy.")
        limitations_list.append("This is a symptom descriptor, NOT an Ayurvedic diagnosis or Dosha determination.")

        mapped_concepts.append(
            AyurvedicConceptMapping(
                concept_id=entry.concept_id,
                sanskrit_name=entry.sanskrit_name,
                english_descriptor=entry.english_descriptor,
                category=entry.category,
                matched_observations=triggering_tokens,
                required_evidence=list(entry.required_evidence_criteria),
                mapping_confidence=confidence,
                limitations=limitations_list,
                source_reference=entry.source_reference,
                is_reference_verified=entry.is_reference_verified,
                evidence_notes=[f"Matched patient observation: '{t}'" for t in triggering_tokens],
            )
        )

    # Identify unmapped observations
    unmapped_observations = [t for t in valid_tokens if t not in matched_token_set]

    # Boundaries and constraints
    limitations = [
        "Phase 7 Ayurvedic representation is strictly descriptive (Rupa/Lakshana).",
        "Dosha imbalances (Vata/Pitta/Kapha) are intentionally marked 'not_assessed' to prevent speculative single-symptom inference.",
        "Prakriti (individual constitution) is intentionally marked 'not_assessed' as it requires comprehensive longitudinal examination.",
        "Missing information is treated as unassessed, NOT absent.",
        "No Ayurvedic or modern therapeutic interventions are generated or implied.",
    ]

    traceability = {
        "kb_version": AYURVEDA_KB_VERSION,
        "input_tokens_analyzed": valid_tokens,
        "matched_concepts_count": len(mapped_concepts),
        "unmapped_tokens_count": len(unmapped_observations),
    }

    ayurvedic_rep = AyurvedicRepresentation(
        observed_descriptors=valid_tokens,
        mapped_concepts=mapped_concepts,
        unmapped_observations=unmapped_observations,
        dosha_assessment=AyurvedicAssessmentPlaceholder(
            status="not_assessed",
            reason="Dosha assessment requires comprehensive clinical examination and is intentionally omitted to prevent speculative inference."
        ),
        prakriti_assessment=AyurvedicAssessmentPlaceholder(
            status="not_assessed",
            reason="Prakriti determination requires individualized constitution evaluation and is intentionally omitted."
        ),
        representation_limitations=limitations,
        source_traceability=traceability,
    )

    return ayurvedic_rep, valid_tokens


def build_correspondence_layer(
    modern_rep: ModernRepresentation,
    ayurvedic_rep: AyurvedicRepresentation,
    state: dict[str, Any]
) -> CorrespondenceLayer:
    """
    Constructs the explicit correspondence layer between Modern and Ayurvedic perspectives.
    Evaluates relationship types, confidence, evidence, uncertainty, and limitations.
    """
    correspondences: list[CorrespondenceItem] = []
    unmapped_modern_symptoms: list[str] = []

    # Map each modern symptom feature
    if not modern_rep.symptom_features:
        # Check if vague input
        raw_cc = state.get("chief_complaint") or state.get("current_message", "")
        if raw_cc and is_vague_observation(raw_cc):
            correspondences.append(
                CorrespondenceItem(
                    modern_concept=raw_cc,
                    ayurvedic_concept="none",
                    relationship_type=RelationshipType.INSUFFICIENT_EVIDENCE,
                    confidence=MappingConfidence.INSUFFICIENT_EVIDENCE,
                    evidence=[f"Vague input received: '{raw_cc}'"],
                    uncertainty="Patient narrative lacks specific clinical or descriptive characteristics required for correspondence.",
                    limitations=["Cannot establish correspondence from non-specific vague statements."],
                )
            )
            return CorrespondenceLayer(
                correspondences=correspondences,
                overall_correspondence_status="insufficient_evidence",
                unmapped_modern_symptoms=[raw_cc],
                summary_explanation="Insufficient clinical detail to establish supported correspondence."
            )

    for feature in modern_rep.symptom_features:
        feature_name = feature.symptom_name
        feature_character = feature.character or ""
        combined_text = f"{feature_name} ({feature_character})".strip() if feature_character else feature_name

        # Find any matching concepts in ayurvedic_rep
        matched_mappings: list[AyurvedicConceptMapping] = []
        for concept in ayurvedic_rep.mapped_concepts:
            for obs in concept.matched_observations:
                clean_obs = obs.strip().lower()
                if clean_obs in feature_name.lower() or feature_name.lower() in clean_obs or (feature_character and clean_obs in feature_character.lower()):
                    matched_mappings.append(concept)
                    break

        if matched_mappings:
            for concept in matched_mappings:
                # Descriptive correspondence
                evidence_items = [
                    f"Modern feature '{feature_name}' (quality: '{feature_character or 'unspecified'}') aligns descriptively with Ayurvedic descriptor '{concept.sanskrit_name}' ({concept.english_descriptor}).",
                ]
                if feature.duration:
                    evidence_items.append(f"Reported duration: {feature.duration}")
                if feature.location:
                    evidence_items.append(f"Reported anatomical location: {feature.location}")

                uncertainty_statement = (
                    f"Observation aligns with descriptive taxonomy '{concept.sanskrit_name}'. "
                    "However, clinical etiology and systemic context remain unconfirmed."
                )

                correspondences.append(
                    CorrespondenceItem(
                        modern_concept=combined_text,
                        ayurvedic_concept=f"{concept.sanskrit_name} ({concept.english_descriptor})",
                        relationship_type=RelationshipType.DESCRIPTIVE_CORRESPONDENCE,
                        confidence=concept.mapping_confidence,
                        evidence=evidence_items,
                        uncertainty=uncertainty_statement,
                        limitations=concept.limitations,
                    )
                )
        else:
            # Modern feature has no supported mapping
            unmapped_modern_symptoms.append(combined_text)
            correspondences.append(
                CorrespondenceItem(
                    modern_concept=combined_text,
                    ayurvedic_concept="none",
                    relationship_type=RelationshipType.NO_SUPPORTED_MAPPING,
                    confidence=MappingConfidence.INSUFFICIENT_EVIDENCE,
                    evidence=[f"Modern symptom '{combined_text}' was reported."],
                    uncertainty="No verified Ayurvedic descriptive equivalent exists in the current versioned knowledge base (AYURVEDA_KB_V1).",
                    limitations=[
                        "Absence in knowledge base does NOT imply clinical unimportance.",
                        "Knowledge base is intentionally constrained to verified descriptive symptom entries.",
                    ],
                )
            )

    # Determine overall status
    if not correspondences:
        overall_status = "insufficient_evidence"
        summary = "No clinical features available to evaluate correspondence."
    elif all(c.relationship_type == RelationshipType.DESCRIPTIVE_CORRESPONDENCE for c in correspondences):
        overall_status = "established_descriptive_correspondence"
        summary = "All reported clinical features have supported descriptive correspondences in AYURVEDA_KB_V1."
    elif any(c.relationship_type == RelationshipType.DESCRIPTIVE_CORRESPONDENCE for c in correspondences):
        overall_status = "partial_descriptive_correspondence"
        summary = "Some reported clinical features correspond to supported Ayurvedic descriptors; others lack verified mappings."
    elif any(c.relationship_type == RelationshipType.INSUFFICIENT_EVIDENCE for c in correspondences):
        overall_status = "insufficient_evidence"
        summary = "Available clinical information is insufficient or too vague to establish correspondence."
    else:
        overall_status = "no_supported_correspondence"
        summary = "Reported features currently have no supported descriptive entries in AYURVEDA_KB_V1."

    return CorrespondenceLayer(
        correspondences=correspondences,
        overall_correspondence_status=overall_status,
        unmapped_modern_symptoms=unmapped_modern_symptoms,
        summary_explanation=summary,
    )


def generate_ayurveda_modern_representation(state: dict[str, Any]) -> AyurvedaModernOutput:
    """
    Main entry point for Phase 7 execution.

    Generates:
    - Modern Clinical Representation
    - Ayurvedic Descriptive Representation
    - Correspondence Layer
    - Safety Constraints & Emergency Precedence
    - Physician Synthesis Summary
    """
    case_id = state.get("session_id") or state.get("patient_id") or "CASE_UNKNOWN"

    # 1. Modern representation
    modern_rep = build_modern_representation(state)

    # 2. Ayurvedic representation
    ayurvedic_rep, valid_tokens = build_ayurvedic_representation(state, modern_rep)

    # 3. Correspondence layer
    correspondence_layer = build_correspondence_layer(modern_rep, ayurvedic_rep, state)

    # 4. Representation status determination
    is_complete_intake = bool(state.get("information_complete", False))
    if not valid_tokens or (len(valid_tokens) == 1 and is_vague_observation(valid_tokens[0])):
        status = RepresentationStatus.INSUFFICIENT_INFORMATION
    elif not is_complete_intake or len(correspondence_layer.unmapped_modern_symptoms) > 0:
        status = RepresentationStatus.PARTIAL
    else:
        status = RepresentationStatus.COMPLETE

    # 5. Safety constraints enforcement
    red_flag_alert = (modern_rep.red_flag_status == "red_flags_detected") or modern_rep.immediate_attention_required
    emergency_warning: Optional[str] = None

    if red_flag_alert:
        emergency_warning = (
            "CRITICAL EMERGENCY SAFETY OVERRIDE: Red flag symptoms detected. "
            "Modern emergency medical evaluation takes absolute precedence. "
            "No integrative, Ayurvedic, or descriptive correspondence should delay acute emergency care."
        )

    safety_constraints = Phase7SafetyConstraints(
        red_flag_alert_preserved=red_flag_alert,
        emergency_warning=emergency_warning,
        risk_assessment_preserved=True,
    )

    # 6. Non-diagnostic physician summary
    summary_parts: list[str] = []
    if emergency_warning:
        summary_parts.append(emergency_warning)

    summary_parts.append(
        f"Case represented from dual observational perspectives under {AYURVEDA_KB_VERSION}."
    )
    if modern_rep.chief_complaint:
        summary_parts.append(f"Modern descriptive features: {len(modern_rep.symptom_features)} structured feature(s).")
    if ayurvedic_rep.mapped_concepts:
        concept_names = [f"{c.sanskrit_name} ({c.english_descriptor})" for c in ayurvedic_rep.mapped_concepts]
        summary_parts.append(f"Ayurvedic descriptive concepts: {', '.join(concept_names)}.")
    else:
        summary_parts.append("Ayurvedic descriptive concepts: None mapped.")

    summary_parts.append(f"Correspondence status: {correspondence_layer.overall_correspondence_status}.")
    summary_parts.append("Dosha and Prakriti classifications remain intentionally unassessed. Physician review required.")

    physician_summary = " ".join(summary_parts)

    return AyurvedaModernOutput(
        representation_status=status,
        case_id=case_id,
        modern_representation=modern_rep,
        ayurvedic_representation=ayurvedic_rep,
        correspondence=correspondence_layer,
        safety_constraints=safety_constraints,
        physician_summary=physician_summary,
        formatting_version="phase7_v1",
    )
