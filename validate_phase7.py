"""
Phase 7 Direct Validation Suite (Zero-LLM / Fast / Deterministic).

Validates all 15 core requirements and safety constraints for Phase 7:
Ayurveda <-> Modern Medicine Representation.
"""

import sys
import os

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ayurveda_modern_schema import (
    RelationshipType,
    MappingConfidence,
    RepresentationStatus,
    AyurvedaModernOutput,
)
from app.ayurveda_modern_mapping import generate_ayurveda_modern_representation
from app.ayurveda_knowledge_base import AYURVEDA_KB_VERSION, AYURVEDA_KB_ENTRIES


def test_1_basic_modern_representation():
    """Test 1: Modern clinical representation is accurately and descriptively structured."""
    state = {
        "patient_id": "P001",
        "session_id": "S001",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "5 days",
        "severity": "mild",
        "associated_symptoms": ["nausea"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 8,
    }
    output: AyurvedaModernOutput = generate_ayurveda_modern_representation(state)
    mod = output.modern_representation

    assert mod.chief_complaint == "stomach pain", "Chief complaint mismatch"
    assert mod.nature_of_pain == "burning", "Nature of pain mismatch"
    assert mod.location == "upper abdomen", "Location mismatch"
    assert mod.duration == "5 days", "Duration mismatch"
    assert mod.severity == "mild", "Severity mismatch"
    assert "nausea" in mod.associated_symptoms, "Associated symptom missing"
    assert mod.red_flag_status == "no_obvious_red_flags"
    assert mod.risk_level == "LOW"
    assert mod.risk_score == 8
    print("TEST 1 (Basic Modern Representation): PASS")


def test_2_basic_ayurvedic_descriptive_mapping():
    """Test 2: Patient observations map to supported descriptive concepts without diagnosis."""
    state = {
        "patient_id": "P002",
        "session_id": "S002",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "3 days",
        "severity": "moderate",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 10,
    }
    output = generate_ayurveda_modern_representation(state)
    ayur = output.ayurvedic_representation

    concept_ids = [c.concept_id for c in ayur.mapped_concepts]
    assert "vidaha" in concept_ids, "Expected 'vidaha' (burning descriptor) mapping"
    assert "shoola_udara" in concept_ids, "Expected 'shoola_udara' (abdominal pain descriptor) mapping"

    for concept in ayur.mapped_concepts:
        assert concept.sanskrit_name in ["Vidaha", "Udara Shoola"]
        assert len(concept.limitations) > 0, "Limitations must be explicit"
        assert concept.is_reference_verified is True, "Source citation must be verified"
    print("TEST 2 (Basic Ayurvedic Descriptive Mapping): PASS")


def test_3_supported_correspondence():
    """Test 3: Correspondence layer establishes descriptive correspondence with explicit evidence."""
    state = {
        "patient_id": "P003",
        "session_id": "S003",
        "chief_complaint": "headache",
        "duration": "1 day",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)
    corr = output.correspondence

    assert len(corr.correspondences) > 0, "Expected at least 1 correspondence"
    first_corr = corr.correspondences[0]
    assert first_corr.relationship_type == RelationshipType.DESCRIPTIVE_CORRESPONDENCE
    assert "Shiroruk" in first_corr.ayurvedic_concept
    assert len(first_corr.evidence) > 0, "Evidence must be present"
    assert "uncertainty" in first_corr.model_dump(), "Uncertainty must be explicitly captured"
    print("TEST 3 (Supported Correspondence): PASS")


def test_4_unsupported_unmapped_symptom():
    """Test 4: Symptoms without KB support result in no_supported_mapping without hallucination."""
    state = {
        "patient_id": "P004",
        "session_id": "S004",
        "chief_complaint": "blurred vision",
        "duration": "2 weeks",
        "severity": "mild",
        "associated_symptoms": ["tinnitus"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)
    corr = output.correspondence

    assert len(corr.unmapped_modern_symptoms) > 0, "Expected unmapped symptoms"
    for c in corr.correspondences:
        assert c.relationship_type == RelationshipType.NO_SUPPORTED_MAPPING
        assert c.ayurvedic_concept == "none"
        assert c.confidence == MappingConfidence.INSUFFICIENT_EVIDENCE
    assert corr.overall_correspondence_status == "no_supported_correspondence"
    print("TEST 4 (Unsupported / Unmapped Symptom): PASS")


def test_5_vague_missing_information():
    """Test 5: Vague or non-specific statements yield insufficient_evidence."""
    state = {
        "patient_id": "P005",
        "session_id": "S005",
        "chief_complaint": "I don't feel good",
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "information_complete": False,
        "red_flag_status": "insufficient_information",
        "immediate_attention_required": False,
        "risk_level": None,
        "risk_score": None,
    }
    output = generate_ayurveda_modern_representation(state)

    assert output.representation_status == RepresentationStatus.INSUFFICIENT_INFORMATION
    assert output.correspondence.overall_correspondence_status == "insufficient_evidence"
    assert len(output.ayurvedic_representation.mapped_concepts) == 0
    print("TEST 5 (Vague / Missing Information): PASS")


def test_6_mapping_confidence_distinction():
    """Test 6: Mapping confidence measures descriptive alignment, NOT clinical disease risk."""
    state = {
        "patient_id": "P006",
        "session_id": "S006",
        "chief_complaint": "cough",
        "duration": "3 days",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)

    # High mapping confidence in the descriptive concept 'Kasa'
    concept = output.ayurvedic_representation.mapped_concepts[0]
    assert concept.concept_id == "kasa_vega"
    assert concept.mapping_confidence in [MappingConfidence.HIGH, MappingConfidence.MODERATE]
    # But clinical risk remains LOW (score 5)
    assert output.modern_representation.risk_level == "LOW"
    assert output.modern_representation.risk_score == 5
    print("TEST 6 (Mapping Confidence Distinction): PASS")


def test_7_source_traceability():
    """Test 7: All representations provide structured provenance metadata."""
    state = {
        "patient_id": "P007",
        "session_id": "S007",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "duration": "2 days",
        "severity": "moderate",
        "associated_symptoms": ["nausea"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 8,
    }
    output = generate_ayurveda_modern_representation(state)

    assert "chief_complaint_source" in output.modern_representation.source_traceability
    assert "kb_version" in output.ayurvedic_representation.source_traceability
    assert output.ayurvedic_representation.source_traceability["kb_version"] == AYURVEDA_KB_VERSION
    for concept in output.ayurvedic_representation.mapped_concepts:
        assert len(concept.evidence_notes) > 0
    print("TEST 7 (Source Traceability): PASS")


def test_8_strict_dosha_non_inference():
    """Test 8: Dosha assessment is strictly locked to 'not_assessed'."""
    state = {
        "patient_id": "P008",
        "session_id": "S008",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "duration": "5 days",
        "severity": "moderate",
        "associated_symptoms": ["fever"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 12,
    }
    output = generate_ayurveda_modern_representation(state)
    dosha = output.ayurvedic_representation.dosha_assessment

    assert dosha.status == "not_assessed", "Dosha must always be 'not_assessed'"
    assert "intentionally omitted" in dosha.reason or "requires comprehensive clinical examination" in dosha.reason
    print("TEST 8 (Strict Dosha Non-Inference): PASS")


def test_9_strict_prakriti_non_inference():
    """Test 9: Prakriti assessment is strictly locked to 'not_assessed'."""
    state = {
        "patient_id": "P009",
        "session_id": "S009",
        "chief_complaint": "joint pain",
        "duration": "1 week",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 8,
    }
    output = generate_ayurveda_modern_representation(state)
    prakriti = output.ayurvedic_representation.prakriti_assessment

    assert prakriti.status == "not_assessed", "Prakriti must always be 'not_assessed'"
    assert "individualized constitution" in prakriti.reason or "intentionally omitted" in prakriti.reason
    print("TEST 9 (Strict Prakriti Non-Inference): PASS")


def test_10_phase_2a_red_flag_emergency_override():
    """Test 10: Phase 2A red flags trigger emergency safety override."""
    state = {
        "patient_id": "P010",
        "session_id": "S010",
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "crushing",
        "duration": "30 minutes",
        "severity": "severe",
        "associated_symptoms": ["difficulty breathing"],
        "information_complete": True,
        "red_flag_status": "red_flags_detected",
        "immediate_attention_required": True,
        "risk_level": "URGENT",
        "risk_score": 90,
    }
    output = generate_ayurveda_modern_representation(state)

    assert output.safety_constraints.red_flag_alert_preserved is True
    assert output.safety_constraints.emergency_warning is not None
    assert "CRITICAL EMERGENCY SAFETY OVERRIDE" in output.safety_constraints.emergency_warning
    assert "absolute precedence" in output.safety_constraints.emergency_warning
    assert output.modern_representation.immediate_attention_required is True
    print("TEST 10 (Phase 2A Red-Flag Emergency Override): PASS")


def test_11_phase_2b_risk_score_preservation():
    """Test 11: Phase 2B risk score and level remain completely untouched."""
    state = {
        "patient_id": "P011",
        "session_id": "S011",
        "chief_complaint": "diarrhea",
        "duration": "2 days",
        "severity": "high",
        "associated_symptoms": ["fever"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "HIGH",
        "risk_score": 45,
    }
    output = generate_ayurveda_modern_representation(state)

    assert output.modern_representation.risk_level == "HIGH"
    assert output.modern_representation.risk_score == 45
    assert output.safety_constraints.risk_assessment_preserved is True
    print("TEST 11 (Phase 2B Risk Score & Level Preservation): PASS")


def test_12_zero_diagnosis_generation():
    """Test 12: Output contains zero modern disease diagnoses and zero Ayurvedic Nidana diagnoses."""
    state = {
        "patient_id": "P012",
        "session_id": "S012",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "location": "upper abdomen",
        "duration": "5 days",
        "severity": "moderate",
        "associated_symptoms": ["nausea"],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 10,
    }
    output = generate_ayurveda_modern_representation(state)
    output_str = str(output.model_dump()).lower()

    # Forbidden diagnostic assertions
    forbidden_terms = [
        "patient has gastritis",
        "diagnosed with gastritis",
        "patient has gerd",
        "pitta vyadhi",
        "amapitta diagnosis",
        "disease diagnosis",
        "diagnosed with ulcer",
    ]
    for term in forbidden_terms:
        assert term not in output_str, f"Forbidden diagnostic term '{term}' found in output!"

    assert "does not generate medical or ayurvedic diagnoses" in output.safety_constraints.no_diagnosis_disclaimer.lower()
    print("TEST 12 (Zero Diagnosis Generation): PASS")


def test_13_zero_treatment_recommendation():
    """Test 13: Output contains zero treatment, herb, medication, or dosage recommendations."""
    state = {
        "patient_id": "P013",
        "session_id": "S013",
        "chief_complaint": "cough",
        "duration": "3 days",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)
    # Check payload (excluding safety disclaimer strings) for affirmative treatments
    payload_str = (
        str(output.modern_representation.model_dump())
        + str(output.ayurvedic_representation.model_dump())
        + str(output.correspondence.model_dump())
    ).lower()

    forbidden_treatments = [
        "prescribe",
        "prescription",
        "take triphala",
        "take paracetamol",
        "dosage",
        "mg twice daily",
        "take churnam",
        "take kashayam",
        "take antibiotic",
        "recommended treatment",
    ]
    for term in forbidden_treatments:
        assert term not in payload_str, f"Forbidden treatment term '{term}' found in payload!"

    assert "does not prescribe medications" in output.safety_constraints.no_treatment_disclaimer.lower()
    print("TEST 13 (Zero Treatment / Medication / Dosage Recommendation): PASS")


def test_14_non_equivalence_disclaimer_enforcement():
    """Test 14: Non-equivalence disclaimer is explicitly enforced on every correspondence."""
    state = {
        "patient_id": "P014",
        "session_id": "S014",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)

    for item in output.correspondence.correspondences:
        assert "not imply clinical or medical equivalence" in item.equivalence_disclaimer.lower()
    assert "not medically equivalent" in output.safety_constraints.non_equivalence_disclaimer.lower()
    print("TEST 14 (Non-Equivalence Disclaimer Enforcement): PASS")


def test_15_missing_not_absent_invariant():
    """Test 15: Missing symptoms are treated as unassessed, not absent."""
    state = {
        "patient_id": "P015",
        "session_id": "S015",
        "chief_complaint": "stomach pain",
        "nature_of_pain": "burning",
        "duration": "2 days",
        "severity": "mild",
        "associated_symptoms": [],  # Fever, vomiting, nausea unmentioned
        "information_complete": True,
        "red_flag_status": "no_obvious_red_flags",
        "immediate_attention_required": False,
        "risk_level": "LOW",
        "risk_score": 5,
    }
    output = generate_ayurveda_modern_representation(state)

    assert "treated as unassessed, not confirmed absent" in output.safety_constraints.missing_not_absent_disclaimer.lower()
    # Ensure unmentioned symptoms like fever are not in mapped concepts
    concept_ids = [c.concept_id for c in output.ayurvedic_representation.mapped_concepts]
    assert "jwara_lakshana" not in concept_ids, "Unmentioned fever must not be inferred as present or absent"
    print("TEST 15 (Missing != Absent Invariant): PASS")


def main():
    print("=" * 80)
    print("RUNNING PHASE 7 DIRECT VALIDATION SUITE (FAST / ZERO-LLM)")
    print("=" * 80)

    test_1_basic_modern_representation()
    test_2_basic_ayurvedic_descriptive_mapping()
    test_3_supported_correspondence()
    test_4_unsupported_unmapped_symptom()
    test_5_vague_missing_information()
    test_6_mapping_confidence_distinction()
    test_7_source_traceability()
    test_8_strict_dosha_non_inference()
    test_9_strict_prakriti_non_inference()
    test_10_phase_2a_red_flag_emergency_override()
    test_11_phase_2b_risk_score_preservation()
    test_12_zero_diagnosis_generation()
    test_13_zero_treatment_recommendation()
    test_14_non_equivalence_disclaimer_enforcement()
    test_15_missing_not_absent_invariant()

    print("=" * 80)
    print("ALL 15 PHASE 7 DIRECT VALIDATION TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
