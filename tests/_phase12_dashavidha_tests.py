"""
Phase 12: Dashavidha Atura Pariksha Unit Test Suite.

Contains 25+ comprehensive, deterministic test cases covering:
- 10 classical parameters (Charaka Samhita, Vimana Sthana 8/94)
- 3-tier status model (explicitly_reported, structurally_extracted, not_assessed)
- Non-inference invariants (Prakriti, Vikriti, Sara, Samhanana, Pramana, Satmya, Sattva, Ahara Shakti, Vyayama Shakti)
- Low Hb + fatigue non-grading
- Penicillin allergy != Asatmya
- Anxiety != Avara Sattva
- Burning sensation != Pitta Vikriti
- Phase 2A/2B/10 safety immutability
- Zero diagnosis, zero prescription, zero herbal recommendation
- Deterministic repeatability and provenance preservation
"""

import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.dashavidha_schema import (
    EpistemicStatus,
    DashavidhaParameterRecord,
    DashavidhaAturaParikshaProfileDTO,
    Phase12DashavidhaOutputDTO,
)
from app.dashavidha_engine import evaluate_dashavidha_atura_pariksha
from app.orchestrator import process_turn
from tests.fixtures.dashavidha_fixtures import DASHAVIDHA_FIXTURES


FORBIDDEN_CONCEPT_SUBSTRINGS = [
    "pitta vikriti",
    "vata vikriti",
    "kapha vikriti",
    "pitta-vata vikriti",
    "amlapitta",
    "sandhigata vata",
    "avara sara",
    "poor sara",
    "avara sattva",
    "avara satmya",
    "avara vyayama",
    "manda agni",
    "tikshna agni",
    "vishama agni",
]


def test_01_schema_structure_and_all_ten_parameters_exist():
    """Validates all 10 classical parameters exist with correct IDs and Charaka references."""
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]

    expected_params = [
        "prakriti", "vikriti", "sara", "samhanana", "pramana",
        "satmya", "sattva", "ahara_shakti", "vyayama_shakti", "vaya"
    ]
    for p in expected_params:
        assert p in dv, f"Missing parameter {p} in Dashavidha profile"
        rec = dv[p]
        assert rec["framework_reference"] == "Charaka Samhita, Vimana Sthana 8/94"
        assert rec["status"] in ["explicitly_reported", "structurally_extracted", "not_assessed"]


def test_02_vaya_balyavastha_mapping():
    """Validates chronological age <= 16 maps deterministically to Balyavastha."""
    fixture = DASHAVIDHA_FIXTURES["vaya_balya"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]

    assert vaya["status"] == "structurally_extracted"
    assert "Balyavastha" in vaya["structured_findings"]["classical_life_stage"]
    assert vaya["structured_findings"]["chronological_age"] == 8
    assert "patient_profile.age" in vaya["provenance_sources"]


def test_03_vaya_madhyamavastha_mapping():
    """Validates chronological age 17-60 maps deterministically to Madhyamavastha."""
    fixture = DASHAVIDHA_FIXTURES["vaya_madhyama"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]

    assert vaya["status"] == "structurally_extracted"
    assert "Madhyamavastha" in vaya["structured_findings"]["classical_life_stage"]
    assert vaya["structured_findings"]["chronological_age"] == 42


def test_04_vaya_vriddhavastha_mapping():
    """Validates chronological age > 60 maps deterministically to Vriddhavastha."""
    fixture = DASHAVIDHA_FIXTURES["vaya_vriddha"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]

    assert vaya["status"] == "structurally_extracted"
    assert "Vriddhavastha" in vaya["structured_findings"]["classical_life_stage"]
    assert vaya["structured_findings"]["chronological_age"] == 72


def test_05_vaya_missing_remains_not_assessed():
    """Validates missing age strictly results in status = not_assessed."""
    fixture = DASHAVIDHA_FIXTURES["vaya_missing"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]

    assert vaya["status"] == "not_assessed"
    assert vaya["structured_findings"] is None


def test_06_sara_strict_not_assessed_invariant():
    """Validates Sara is strictly not_assessed even when lab tests or symptoms are provided."""
    fixture = DASHAVIDHA_FIXTURES["low_hb_fatigue"]
    turn_resp = process_turn(fixture)
    sara = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sara"]

    assert sara["status"] == "not_assessed"
    assert sara["prior_formal_assessment"] is None
    assert any("hemoglobin" in lim.lower() for lim in sara["clinical_limitations"])


def test_07_samhanana_strict_not_assessed_invariant():
    """Validates Samhanana is strictly not_assessed even when modern BMI/weight is present."""
    fixture = DASHAVIDHA_FIXTURES["modern_vitals_pramana"]
    turn_resp = process_turn(fixture)
    samhanana = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["samhanana"]

    assert samhanana["status"] == "not_assessed"
    assert any("BMI" in lim for lim in samhanana["clinical_limitations"])


def test_08_pramana_modern_measurements_separated_from_classical():
    """Validates modern vitals are extracted as modern facts while classical Pramana remains not_assessed."""
    fixture = DASHAVIDHA_FIXTURES["modern_vitals_pramana"]
    turn_resp = process_turn(fixture)
    pramana = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["pramana"]

    assert pramana["status"] == "structurally_extracted"
    assert pramana["structured_findings"]["modern_measurements"]["height"] == 178
    assert pramana["structured_findings"]["modern_measurements"]["weight"] == 74
    assert pramana["structured_findings"]["classical_pramana_assessment"] == "not_assessed"
    assert any("not converted into classical pramana grades" in lim.lower() for lim in pramana["clinical_limitations"])


def test_09_prakriti_default_not_assessed():
    """Validates Prakriti defaults to not_assessed in absence of explicit prior patient report."""
    fixture = DASHAVIDHA_FIXTURES["prakriti_unassessed"]
    turn_resp = process_turn(fixture)
    prakriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["prakriti"]

    assert prakriti["status"] == "not_assessed"
    assert prakriti["prior_formal_assessment"] is None
    assert any("not predicted from acute symptoms" in lim.lower() for lim in prakriti["clinical_limitations"])


def test_10_prakriti_explicitly_reported_prior_assessment():
    """Validates explicit patient report of prior formal Prakriti assessment is preserved."""
    fixture = DASHAVIDHA_FIXTURES["prakriti_reported"]
    turn_resp = process_turn(fixture)
    prakriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["prakriti"]

    assert prakriti["status"] == "explicitly_reported"
    assert prakriti["prior_formal_assessment"]["reported_prakriti"] == "Pitta-Kapha"
    assert "patient_profile.reported_prakriti" in prakriti["provenance_sources"]


def test_11_burning_sensation_does_not_become_pitta_vikriti():
    """MANDATORY NEGATIVE TEST: Burning sensation captured as observation and NEVER generates Pitta Vikriti or Amlapitta."""
    fixture = DASHAVIDHA_FIXTURES["burning_sensation"]
    turn_resp = process_turn(fixture)
    vikriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vikriti"]

    assert vikriti["status"] == "not_assessed"
    assert any("burning" in obs.lower() for obs in vikriti["reported_observations"])
    
    # Assert forbidden concepts are not generated anywhere in the serialized profile
    serialized = json.dumps(turn_resp.clinical_output["dashavidha_atura_pariksha"]).lower()
    for forbidden in FORBIDDEN_CONCEPT_SUBSTRINGS:
        assert forbidden not in serialized, f"Forbidden concept '{forbidden}' found in Dashavidha output!"


def test_12_satmya_dietary_habits_preserved():
    """Validates patient-reported habitual diet is documented descriptively."""
    fixture = DASHAVIDHA_FIXTURES["satmya_diet"]
    turn_resp = process_turn(fixture)
    satmya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["satmya"]

    assert satmya["status"] == "explicitly_reported"
    assert any("Vegetarian" in obs for obs in satmya["reported_observations"])
    assert satmya["structured_findings"]["formal_satmya_assessment"] == "not_assessed"


def test_13_penicillin_allergy_does_not_become_asatmya():
    """MANDATORY NEGATIVE TEST: Penicillin allergy noted without asserting Asatmya or Avara Satmya."""
    fixture = DASHAVIDHA_FIXTURES["penicillin_allergy"]
    turn_resp = process_turn(fixture)
    satmya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["satmya"]

    assert satmya["status"] == "explicitly_reported"
    assert any("Penicillin" in obs for obs in satmya["reported_observations"])

    serialized = json.dumps(satmya).lower()
    assert "asatmya" not in serialized or "not equated to classical asatmya" in serialized
    assert "avara satmya" not in serialized


def test_14_anxiety_does_not_become_avara_sattva():
    """MANDATORY NEGATIVE TEST: Reported anxiety/distress is noted without assigning Avara Sattva."""
    fixture = DASHAVIDHA_FIXTURES["anxiety_distress"]
    turn_resp = process_turn(fixture)
    sattva = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sattva"]

    assert sattva["status"] == "explicitly_reported"
    assert any("anxiety" in obs.lower() for obs in sattva["reported_observations"])
    assert sattva["structured_findings"]["formal_sattva_assessment"] == "not_assessed"

    serialized = json.dumps(sattva).lower()
    assert "avara sattva" not in serialized


def test_15_sattva_unreported_remains_not_assessed():
    """Validates unmentioned mental health strictly defaults to not_assessed."""
    fixture = DASHAVIDHA_FIXTURES["vaya_madhyama"]
    turn_resp = process_turn(fixture)
    sattva = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sattva"]

    assert sattva["status"] == "not_assessed"
    assert len(sattva["reported_observations"]) == 0


def test_16_ahara_shakti_reported_appetite_no_grading():
    """Validates appetite observations are captured without Pravara/Avara grading or Agni diagnosis."""
    fixture = DASHAVIDHA_FIXTURES["ahara_shakti_appetite"]
    turn_resp = process_turn(fixture)
    ahara = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["ahara_shakti"]

    assert ahara["status"] == "explicitly_reported"
    assert any("poor appetite" in obs.lower() for obs in ahara["reported_observations"])
    assert ahara["structured_findings"]["formal_ahara_shakti_assessment"] == "not_assessed"

    serialized = json.dumps(ahara).lower()
    assert "manda agni" not in serialized
    assert "avara ahara" not in serialized


def test_17_vyayama_shakti_reported_limits_no_grading():
    """Validates reported exercise limitations are captured without formal Vyayama Shakti grading."""
    fixture = DASHAVIDHA_FIXTURES["vyayama_shakti_fatigue"]
    turn_resp = process_turn(fixture)
    vyayama = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vyayama_shakti"]

    assert vyayama["status"] == "explicitly_reported"
    assert any("fatigue" in obs.lower() or "walking" in obs.lower() for obs in vyayama["reported_observations"])
    assert vyayama["structured_findings"]["formal_vyayama_shakti_assessment"] == "not_assessed"

    serialized = json.dumps(vyayama).lower()
    assert "avara vyayama" not in serialized


def test_18_low_hb_fatigue_no_sara_vyayama_bala_grading():
    """MANDATORY NEGATIVE TEST: Low Hb + fatigue does NOT become Sara = poor, Vyayama = Avara, or Bala = low."""
    fixture = DASHAVIDHA_FIXTURES["low_hb_fatigue"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]

    assert dv["sara"]["status"] == "not_assessed"
    assert "bala" not in dv, "Bala must NOT exist as a Dashavidha parameter"

    serialized = json.dumps(turn_resp.clinical_output["dashavidha_atura_pariksha"]).lower()
    assert "poor sara" not in serialized
    assert "avara sara" not in serialized
    assert "avara vyayama" not in serialized


def test_19_phase2a_emergency_safety_preservation():
    """Validates red flags preserve emergency warning in safety_context without converting to diagnosis."""
    fixture = DASHAVIDHA_FIXTURES["emergency_red_flag"]
    turn_resp = process_turn(fixture)
    safety_ctx = turn_resp.clinical_output["dashavidha_atura_pariksha"]["safety_context"]

    assert safety_ctx["immediate_attention_required"] is True
    assert safety_ctx["red_flag_status"] == "red_flags_detected"


def test_20_phase2b_and_phase10_immutability():
    """Validates Phase 2B and Phase 10 risk scores/levels remain completely unmodified."""
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    risk = turn_resp.clinical_output["risk_assessment"]
    adv_risk = turn_resp.clinical_output["advanced_risk_assessment"]
    dv_safety = turn_resp.clinical_output["dashavidha_atura_pariksha"]["safety_context"]

    assert dv_safety["risk_level"] == risk["risk_level"]
    assert dv_safety["risk_score"] == risk["risk_score"]
    assert adv_risk is not None


def test_21_zero_diagnosis_and_prescription_invariants():
    """Validates zero diagnostic assertions and zero herbal/drug prescriptions across output."""
    fixture = DASHAVIDHA_FIXTURES["burning_sensation"]
    turn_resp = process_turn(fixture)
    dv_output = turn_resp.clinical_output["dashavidha_atura_pariksha"]

    serialized = json.dumps(dv_output).lower()
    for forbidden in ["prescription", "herb", "dosage", "treatment plan"]:
        if forbidden == "treatment plan":
            # Allowed only in disclaimer
            assert serialized.count("treatment plan") == 1
        else:
            assert forbidden not in serialized, f"Forbidden prescriptive token '{forbidden}' found!"


def test_22_deterministic_execution():
    """Validates that identical inputs yield identical Dashavidha outputs across multiple execution passes."""
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    resp1 = process_turn(fixture)
    resp2 = process_turn(fixture)

    dv1 = resp1.clinical_output["dashavidha_atura_pariksha"]
    dv2 = resp2.clinical_output["dashavidha_atura_pariksha"]
    assert dv1 == dv2


def test_23_provenance_traceability():
    """Validates all populated parameters link to valid state provenance keys."""
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]

    assert "patient_profile.vitals" in dv["pramana"]["provenance_sources"]
    assert "patient_profile.age" in dv["vaya"]["provenance_sources"]
    assert "intake.chief_complaint" in dv["vikriti"]["provenance_sources"]


def test_24_orchestrator_integration_bundle():
    """Validates full orchestrator turn processing produces dashavidha_atura_pariksha in clinical output."""
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)

    assert turn_resp.status == "complete"
    assert "dashavidha_atura_pariksha" in turn_resp.clinical_output
    assert turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["version"] == "phase12_v1"


def test_25_missing_not_absent_empty_baseline():
    """Validates empty input produces all 10 parameters in not_assessed with clinical limitation notes."""
    fixture = DASHAVIDHA_FIXTURES["empty_profile"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]

    assert dv["parameters_not_assessed_count"] == 10
    for param_name in ["prakriti", "vikriti", "sara", "samhanana", "pramana", "satmya", "sattva", "ahara_shakti", "vyayama_shakti", "vaya"]:
        assert dv[param_name]["status"] == "not_assessed"
        assert len(dv[param_name]["clinical_limitations"]) > 0


def run_all_tests():
    tests = [
        test_01_schema_structure_and_all_ten_parameters_exist,
        test_02_vaya_balyavastha_mapping,
        test_03_vaya_madhyamavastha_mapping,
        test_04_vaya_vriddhavastha_mapping,
        test_05_vaya_missing_remains_not_assessed,
        test_06_sara_strict_not_assessed_invariant,
        test_07_samhanana_strict_not_assessed_invariant,
        test_08_pramana_modern_measurements_separated_from_classical,
        test_09_prakriti_default_not_assessed,
        test_10_prakriti_explicitly_reported_prior_assessment,
        test_11_burning_sensation_does_not_become_pitta_vikriti,
        test_12_satmya_dietary_habits_preserved,
        test_13_penicillin_allergy_does_not_become_asatmya,
        test_14_anxiety_does_not_become_avara_sattva,
        test_15_sattva_unreported_remains_not_assessed,
        test_16_ahara_shakti_reported_appetite_no_grading,
        test_17_vyayama_shakti_reported_limits_no_grading,
        test_18_low_hb_fatigue_no_sara_vyayama_bala_grading,
        test_19_phase2a_emergency_safety_preservation,
        test_20_phase2b_and_phase10_immutability,
        test_21_zero_diagnosis_and_prescription_invariants,
        test_22_deterministic_execution,
        test_23_provenance_traceability,
        test_24_orchestrator_integration_bundle,
        test_25_missing_not_absent_empty_baseline,
    ]

    passed = 0
    failed = 0
    print("=" * 75)
    print("VAIDYAARC PHASE 12 UNIT TEST SUITE")
    print("=" * 75)
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} -> {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("-" * 75)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print("=" * 75)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
