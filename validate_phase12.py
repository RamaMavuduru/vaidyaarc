"""
Validation Script for Phase 12: Dashavidha Atura Pariksha.

Runs standalone validation tests verifying all 10 classical parameters,
3-tier status model, negative safety invariants, non-inference rules,
and orchestrator integration.
"""

import json
import sys

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


def test_01_schema_structure():
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    for p in ["prakriti", "vikriti", "sara", "samhanana", "pramana", "satmya", "sattva", "ahara_shakti", "vyayama_shakti", "vaya"]:
        assert p in dv, f"Missing parameter {p}"
        assert dv[p]["framework_reference"] == "Charaka Samhita, Vimana Sthana 8/94"


def test_02_vaya_balyavastha():
    fixture = DASHAVIDHA_FIXTURES["vaya_balya"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]
    assert vaya["status"] == "structurally_extracted"
    assert "Balyavastha" in vaya["structured_findings"]["classical_life_stage"]


def test_03_vaya_madhyamavastha():
    fixture = DASHAVIDHA_FIXTURES["vaya_madhyama"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]
    assert vaya["status"] == "structurally_extracted"
    assert "Madhyamavastha" in vaya["structured_findings"]["classical_life_stage"]


def test_04_vaya_vriddhavastha():
    fixture = DASHAVIDHA_FIXTURES["vaya_vriddha"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]
    assert vaya["status"] == "structurally_extracted"
    assert "Vriddhavastha" in vaya["structured_findings"]["classical_life_stage"]


def test_05_vaya_missing():
    fixture = DASHAVIDHA_FIXTURES["vaya_missing"]
    turn_resp = process_turn(fixture)
    vaya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vaya"]
    assert vaya["status"] == "not_assessed"


def test_06_sara_strict_not_assessed():
    fixture = DASHAVIDHA_FIXTURES["low_hb_fatigue"]
    turn_resp = process_turn(fixture)
    sara = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sara"]
    assert sara["status"] == "not_assessed"


def test_07_samhanana_strict_not_assessed():
    fixture = DASHAVIDHA_FIXTURES["modern_vitals_pramana"]
    turn_resp = process_turn(fixture)
    samhanana = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["samhanana"]
    assert samhanana["status"] == "not_assessed"


def test_08_pramana_modern_measurements():
    fixture = DASHAVIDHA_FIXTURES["modern_vitals_pramana"]
    turn_resp = process_turn(fixture)
    pramana = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["pramana"]
    assert pramana["status"] == "structurally_extracted"
    assert pramana["structured_findings"]["modern_measurements"]["height"] == 178
    assert pramana["structured_findings"]["classical_pramana_assessment"] == "not_assessed"


def test_09_prakriti_default_not_assessed():
    fixture = DASHAVIDHA_FIXTURES["prakriti_unassessed"]
    turn_resp = process_turn(fixture)
    prakriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["prakriti"]
    assert prakriti["status"] == "not_assessed"


def test_10_prakriti_explicitly_reported():
    fixture = DASHAVIDHA_FIXTURES["prakriti_reported"]
    turn_resp = process_turn(fixture)
    prakriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["prakriti"]
    assert prakriti["status"] == "explicitly_reported"
    assert prakriti["prior_formal_assessment"]["reported_prakriti"] == "Pitta-Kapha"


def test_11_burning_sensation_not_pitta_vikriti():
    fixture = DASHAVIDHA_FIXTURES["burning_sensation"]
    turn_resp = process_turn(fixture)
    vikriti = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vikriti"]
    assert vikriti["status"] == "not_assessed"
    assert any("burning" in obs.lower() for obs in vikriti["reported_observations"])
    serialized = json.dumps(turn_resp.clinical_output["dashavidha_atura_pariksha"]).lower()
    for forbidden in FORBIDDEN_CONCEPT_SUBSTRINGS:
        assert forbidden not in serialized, f"Forbidden concept '{forbidden}' found!"


def test_12_satmya_dietary_habits():
    fixture = DASHAVIDHA_FIXTURES["satmya_diet"]
    turn_resp = process_turn(fixture)
    satmya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["satmya"]
    assert satmya["status"] == "explicitly_reported"
    assert any("Vegetarian" in obs for obs in satmya["reported_observations"])


def test_13_penicillin_allergy_not_asatmya():
    fixture = DASHAVIDHA_FIXTURES["penicillin_allergy"]
    turn_resp = process_turn(fixture)
    satmya = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["satmya"]
    assert satmya["status"] == "explicitly_reported"
    serialized = json.dumps(satmya).lower()
    assert "avara satmya" not in serialized


def test_14_anxiety_not_avara_sattva():
    fixture = DASHAVIDHA_FIXTURES["anxiety_distress"]
    turn_resp = process_turn(fixture)
    sattva = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sattva"]
    assert sattva["status"] == "explicitly_reported"
    serialized = json.dumps(sattva).lower()
    assert "avara sattva" not in serialized


def test_15_sattva_unreported():
    fixture = DASHAVIDHA_FIXTURES["vaya_madhyama"]
    turn_resp = process_turn(fixture)
    sattva = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["sattva"]
    assert sattva["status"] == "not_assessed"


def test_16_ahara_shakti_reported_appetite():
    fixture = DASHAVIDHA_FIXTURES["ahara_shakti_appetite"]
    turn_resp = process_turn(fixture)
    ahara = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["ahara_shakti"]
    assert ahara["status"] == "explicitly_reported"
    serialized = json.dumps(ahara).lower()
    assert "manda agni" not in serialized


def test_17_vyayama_shakti_reported_limits():
    fixture = DASHAVIDHA_FIXTURES["vyayama_shakti_fatigue"]
    turn_resp = process_turn(fixture)
    vyayama = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]["vyayama_shakti"]
    assert vyayama["status"] == "explicitly_reported"
    serialized = json.dumps(vyayama).lower()
    assert "avara vyayama" not in serialized


def test_18_low_hb_fatigue_no_sara_vyayama_bala():
    fixture = DASHAVIDHA_FIXTURES["low_hb_fatigue"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert dv["sara"]["status"] == "not_assessed"
    assert "bala" not in dv, "Bala must not be a Dashavidha parameter"


def test_19_phase2a_emergency_preservation():
    fixture = DASHAVIDHA_FIXTURES["emergency_red_flag"]
    turn_resp = process_turn(fixture)
    safety_ctx = turn_resp.clinical_output["dashavidha_atura_pariksha"]["safety_context"]
    assert safety_ctx["immediate_attention_required"] is True
    assert safety_ctx["red_flag_status"] == "red_flags_detected"


def test_20_phase2b_and_phase10_immutability():
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    risk = turn_resp.clinical_output["risk_assessment"]
    dv_safety = turn_resp.clinical_output["dashavidha_atura_pariksha"]["safety_context"]
    assert dv_safety["risk_level"] == risk["risk_level"]
    assert dv_safety["risk_score"] == risk["risk_score"]


def test_21_zero_diagnosis_prescription():
    fixture = DASHAVIDHA_FIXTURES["burning_sensation"]
    turn_resp = process_turn(fixture)
    serialized = json.dumps(turn_resp.clinical_output["dashavidha_atura_pariksha"]).lower()
    for forbidden in ["prescription", "herb", "dosage"]:
        assert forbidden not in serialized, f"Forbidden prescriptive token '{forbidden}' found!"


def test_22_deterministic_execution():
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    resp1 = process_turn(fixture)
    resp2 = process_turn(fixture)
    assert resp1.clinical_output["dashavidha_atura_pariksha"] == resp2.clinical_output["dashavidha_atura_pariksha"]


def test_23_provenance_traceability():
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert "patient_profile.vitals" in dv["pramana"]["provenance_sources"]
    assert "patient_profile.age" in dv["vaya"]["provenance_sources"]


def test_24_orchestrator_integration():
    fixture = DASHAVIDHA_FIXTURES["complete_routine"]
    turn_resp = process_turn(fixture)
    assert turn_resp.status == "complete"
    assert "dashavidha_atura_pariksha" in turn_resp.clinical_output


def test_25_missing_not_absent_empty():
    fixture = DASHAVIDHA_FIXTURES["empty_profile"]
    turn_resp = process_turn(fixture)
    dv = turn_resp.clinical_output["dashavidha_atura_pariksha"]["dashavidha_atura_pariksha"]
    assert dv["parameters_not_assessed_count"] == 10
    for p in ["prakriti", "vikriti", "sara", "samhanana", "pramana", "satmya", "sattva", "ahara_shakti", "vyayama_shakti", "vaya"]:
        assert dv[p]["status"] == "not_assessed"


def run_all_tests():
    tests = [
        test_01_schema_structure,
        test_02_vaya_balyavastha,
        test_03_vaya_madhyamavastha,
        test_04_vaya_vriddhavastha,
        test_05_vaya_missing,
        test_06_sara_strict_not_assessed,
        test_07_samhanana_strict_not_assessed,
        test_08_pramana_modern_measurements,
        test_09_prakriti_default_not_assessed,
        test_10_prakriti_explicitly_reported,
        test_11_burning_sensation_not_pitta_vikriti,
        test_12_satmya_dietary_habits,
        test_13_penicillin_allergy_not_asatmya,
        test_14_anxiety_not_avara_sattva,
        test_15_sattva_unreported,
        test_16_ahara_shakti_reported_appetite,
        test_17_vyayama_shakti_reported_limits,
        test_18_low_hb_fatigue_no_sara_vyayama_bala,
        test_19_phase2a_emergency_preservation,
        test_20_phase2b_and_phase10_immutability,
        test_21_zero_diagnosis_prescription,
        test_22_deterministic_execution,
        test_23_provenance_traceability,
        test_24_orchestrator_integration,
        test_25_missing_not_absent_empty,
    ]

    passed = 0
    failed = 0
    print("=" * 75)
    print("VAIDYAARC PHASE 12 VALIDATION SUITE")
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
