"""
Phase 8B Validation Script: Controlled Ayurveda Knowledge System.

Validates:
1. Metadata structure and 3 approved sources (excluding 4th source).
2. Pydantic v2 schema compliance of all ingested records.
3. Knowledge repository indexing, caching, and querying.
4. Source provenance integrity (page numbers, excerpts, titles).
5. Deterministic keyword and traditional indication retrieval.
6. Source hierarchy ranking (Primary Official >> Secondary Literature).
7. Safety gate emergency red flag blocking (Phase 2A invariant).
8. Safety gate high/urgent risk blocking (Phase 2B invariant).
9. Safety gate severe symptom blocking (severity >= 8).
10. Allergy and ingredient-level contraindication screening.
11. Secondary evidence labeling and restricted recommendation.
12. Non-prescription dosage reference preservation and disclaimers.
13. Preservation of unknown clinical context (pregnancy, pediatric).
14. Insufficient information behavior on unmapped symptoms (zero hallucination).
15. Full orchestrator integration in TurnResponseDTO.
16. Strict separation of Phase 7 taxonomy and Phase 8B recommendations.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ayurveda_knowledge_schema import (
    AuthorityLevel,
    RecordType,
    AyurvedaEligibilityStatus,
    AyurvedaKnowledgeRecord,
)
from app.ayurveda_knowledge_repository import get_ayurveda_repository
from app.ayurveda_retriever import get_ayurveda_retriever
from app.ayurveda_safety_gate import evaluate_safety_and_eligibility
from app.ayurveda_recommendation import evaluate_ayurveda_recommendations
from app.orchestrator import process_turn
from tests.fixtures.ayurveda_remedy_fixtures import AYURVEDA_FIXTURES


def test_01_metadata_structure_and_sources():
    """Test metadata.json structure and verifies the 3 approved sources."""
    metadata_path = PROJECT_ROOT / "knowledge" / "ayurveda" / "metadata.json"
    assert metadata_path.exists(), "metadata.json must exist"
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    assert "approved_sources" in meta
    sources = meta["approved_sources"]
    assert len(sources) == 3, f"Expected exactly 3 approved sources, found {len(sources)}"
    
    source_ids = {s["source_id"] for s in sources}
    expected_ids = {"SRC_CCRAS_HOME_REMEDIES_2005", "SRC_API_PART2_VOL2_2008", "SRC_ECAM_REVIEW_2013"}
    assert source_ids == expected_ids, f"Mismatch in approved source IDs: {source_ids}"
    
    # Assert excluded fourth source
    assert "excluded_sources" in meta
    assert meta["excluded_sources"][0]["source_id"] == "SRC_EXCLUDED_FOURTH"
    assert "excluded" in meta["excluded_sources"][0]["reason"].lower()


def test_02_ingested_records_schema_validation():
    """Validates every record in ingested_records.json parses into AyurvedaKnowledgeRecord."""
    records_path = PROJECT_ROOT / "knowledge" / "ayurveda" / "ingested_records.json"
    assert records_path.exists(), "ingested_records.json must exist"
    
    with open(records_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    source_records = data.get("source_records", {})
    assert len(source_records) == 3, "ingested_records.json must contain 3 source groups"
    
    total_records = 0
    for src_id, record_list in source_records.items():
        assert len(record_list) > 0, f"Source group {src_id} must have records"
        for item in record_list:
            record = AyurvedaKnowledgeRecord.model_validate(item)
            assert record.record_id, "Record must have record_id"
            assert record.name, "Record must have name"
            assert record.provenance.source_id in {"SRC_CCRAS_HOME_REMEDIES_2005", "SRC_API_PART2_VOL2_2008", "SRC_ECAM_REVIEW_2013"}
            total_records += 1
    assert total_records >= 20, f"Expected at least 20 ingested records, found {total_records}"


def test_03_repository_loading_and_indexing():
    """Tests repository singleton, caching, and querying capabilities."""
    repo = get_ayurveda_repository()
    all_records = repo.get_all_records()
    assert len(all_records) > 0, "Repository should load records"
    
    ccras_records = repo.get_records_by_source("SRC_CCRAS_HOME_REMEDIES_2005")
    assert len(ccras_records) > 0, "Should have CCRAS records"
    
    api_records = repo.get_records_by_source("SRC_API_PART2_VOL2_2008")
    assert len(api_records) > 0, "Should have API records"
    
    ecam_records = repo.get_records_by_source("SRC_ECAM_REVIEW_2013")
    assert len(ecam_records) > 0, "Should have eCAM records"
    
    primary_records = repo.get_records_by_authority(AuthorityLevel.PRIMARY_OFFICIAL)
    assert len(primary_records) == len(ccras_records) + len(api_records)


def test_04_provenance_integrity_and_excerpts():
    """Verifies that every record has complete, verifiable provenance."""
    repo = get_ayurveda_repository()
    for record in repo.get_all_records():
        prov = record.provenance
        assert prov.source_id in {"SRC_CCRAS_HOME_REMEDIES_2005", "SRC_API_PART2_VOL2_2008", "SRC_ECAM_REVIEW_2013"}, f"Invalid source_id in {record.record_id}"
        assert prov.document_title, f"Missing document_title in {record.record_id}"
        assert prov.page is not None, f"Missing page in {record.record_id}"
        assert prov.excerpt and len(prov.excerpt.strip()) > 10, f"Missing or empty excerpt in {record.record_id}"


def test_05_retriever_keyword_and_symptom_matching():
    """Tests deterministic retrieval for common symptoms."""
    retriever = get_ayurveda_retriever()
    
    # Test cough
    candidates = retriever.retrieve_candidates(chief_complaint="dry cough", limit=5)
    assert len(candidates) > 0, "Should retrieve candidates for cough"
    match_names = [c.record.name.lower() for c in candidates]
    assert any("adrak" in n or "ginger" in n or "tulasi" in n or "sitopaladi" in n or "vasa" in n for n in match_names)
    
    # Test indigestion
    candidates_digestion = retriever.retrieve_candidates(chief_complaint="indigestion", symptoms=["loss of appetite"], limit=5)
    assert len(candidates_digestion) > 0, "Should retrieve candidates for indigestion"


def test_06_source_hierarchy_ranking():
    """Tests that Primary Official sources are ranked above Secondary Literature."""
    retriever = get_ayurveda_retriever()
    
    # Search for fever/jwara which has both primary and secondary matches
    candidates = retriever.retrieve_candidates(chief_complaint="fever", symptoms=["jwara"], limit=10)
    assert len(candidates) > 0
    
    # If both primary and secondary are returned, primary must appear first
    primary_found = False
    secondary_found = False
    for c in candidates:
        if c.record.authority_level == AuthorityLevel.PRIMARY_OFFICIAL:
            assert not secondary_found, "Primary official source must appear before secondary literature"
            primary_found = True
        elif c.record.authority_level == AuthorityLevel.SECONDARY:
            secondary_found = True


def test_07_safety_gate_blocks_phase2a_emergency():
    """Verifies that Phase 2A emergency immediately BLOCKS recommendations."""
    fixture = AYURVEDA_FIXTURES["emergency_blocked"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision == AyurvedaEligibilityStatus.BLOCKED
    assert len(rec_output.recommendations) == 0
    assert any("emergency" in r.lower() or "immediate" in r.lower() for r in rec_output.blocked_reasons)


def test_08_safety_gate_blocks_phase2b_high_risk():
    """Verifies that Phase 2B High Risk (score >= 40) BLOCKS recommendations."""
    fixture = AYURVEDA_FIXTURES["high_risk_blocked"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision == AyurvedaEligibilityStatus.BLOCKED
    assert len(rec_output.recommendations) == 0
    assert any("risk" in r.lower() for r in rec_output.blocked_reasons)


def test_09_safety_gate_blocks_severe_symptom_scores():
    """Verifies that severe symptom severity (>=8/10 or 'severe') BLOCKS recommendations."""
    fixture = AYURVEDA_FIXTURES["severe_pain_blocked"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision == AyurvedaEligibilityStatus.BLOCKED
    assert len(rec_output.recommendations) == 0
    assert any("severe" in r.lower() or "risk" in r.lower() for r in rec_output.blocked_reasons)


def test_10_safety_gate_blocks_allergy_contraindication():
    """Verifies candidate remedies containing allergens are screened out."""
    fixture = AYURVEDA_FIXTURES["allergy_constraint"]
    state = dict(fixture.state_snapshot)
    state["patient_profile"] = fixture.patient_profile.model_dump()
    
    rec_output = evaluate_ayurveda_recommendations(state)
    # The output should NOT recommend any remedy with ginger/ardraka/shunti
    for item in rec_output.recommendations:
        item_text = (item.name + " " + (item.preparation_summary or "")).lower()
        assert "ardraka" not in item_text and "ginger" not in item_text


def test_11_secondary_evidence_labeling():
    """Verifies that secondary literature remedies are labeled secondary_evidence."""
    fixture = AYURVEDA_FIXTURES["secondary_evidence"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision in {AyurvedaEligibilityStatus.ELIGIBLE, AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW}
    
    ecam_items = [r for r in rec_output.recommendations if r.provenance.source_id == "SRC_ECAM_REVIEW_2013"]
    if ecam_items:
        for item in ecam_items:
            assert item.remedy_type == "secondary_evidence"


def test_12_non_prescription_framing_and_dosage_preservation():
    """Verifies dosage is framed as reference and non-prescription disclaimer is present."""
    fixture = AYURVEDA_FIXTURES["mild_cough"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision == AyurvedaEligibilityStatus.ELIGIBLE
    assert len(rec_output.recommendations) > 0
    
    assert rec_output.non_prescription_disclaimer is not None
    assert "not constitute a medical prescription" in rec_output.non_prescription_disclaimer.lower()
    
    for rec in rec_output.recommendations:
        assert rec.source_dosage_reference is not None, "Must preserve source dosage reference"


def test_13_preservation_of_unknown_clinical_context():
    """Verifies missing pregnancy status triggers cautious physician review."""
    fixture = AYURVEDA_FIXTURES["unknown_pregnancy"]
    state = dict(fixture.state_snapshot)
    state["patient_profile"] = fixture.patient_profile.model_dump()
    
    decision = evaluate_safety_and_eligibility(state)
    assert decision.status == AyurvedaEligibilityStatus.REQUIRES_CLINICIAN_REVIEW
    assert any("pregnancy" in r.lower() for r in decision.reasons)


def test_14_unmapped_symptom_insufficient_info():
    """Verifies unmapped symptoms return INSUFFICIENT_INFORMATION without hallucinations."""
    fixture = AYURVEDA_FIXTURES["unmapped_symptom"]
    state = dict(fixture.state_snapshot)
    
    rec_output = evaluate_ayurveda_recommendations(state)
    assert rec_output.decision == AyurvedaEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(rec_output.recommendations) == 0


def test_15_orchestrator_integration_turn_response():
    """Verifies full turn processing via process_turn includes ayurveda_recommendation."""
    fixture = AYURVEDA_FIXTURES["mild_cough"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.status == "complete"
    assert turn_resp.clinical_output is not None
    assert "ayurveda_recommendation" in turn_resp.clinical_output
    
    ayur_rec = turn_resp.clinical_output["ayurveda_recommendation"]
    assert ayur_rec["decision"] == "eligible"
    assert len(ayur_rec["recommendations"]) > 0


def test_16_phase7_and_phase8b_separation():
    """Verifies Phase 7 dual taxonomy and Phase 8B remedy recommendations coexist separately."""
    fixture = AYURVEDA_FIXTURES["coexistence"]
    turn_resp = process_turn(fixture)
    
    assert turn_resp.clinical_output is not None
    # Phase 7 node output
    assert "ayurveda_modern_representation" in turn_resp.clinical_output
    # Phase 8B node output
    assert "ayurveda_recommendation" in turn_resp.clinical_output
    
    phase7_out = turn_resp.clinical_output["ayurveda_modern_representation"]
    phase8b_out = turn_resp.clinical_output["ayurveda_recommendation"]
    
    assert phase7_out is not None
    assert phase8b_out is not None
    assert "recommendations" in phase8b_out


def run_all_tests():
    tests = [
        test_01_metadata_structure_and_sources,
        test_02_ingested_records_schema_validation,
        test_03_repository_loading_and_indexing,
        test_04_provenance_integrity_and_excerpts,
        test_05_retriever_keyword_and_symptom_matching,
        test_06_source_hierarchy_ranking,
        test_07_safety_gate_blocks_phase2a_emergency,
        test_08_safety_gate_blocks_phase2b_high_risk,
        test_09_safety_gate_blocks_severe_symptom_scores,
        test_10_safety_gate_blocks_allergy_contraindication,
        test_11_secondary_evidence_labeling,
        test_12_non_prescription_framing_and_dosage_preservation,
        test_13_preservation_of_unknown_clinical_context,
        test_14_unmapped_symptom_insufficient_info,
        test_15_orchestrator_integration_turn_response,
        test_16_phase7_and_phase8b_separation,
    ]
    
    passed = 0
    failed = 0
    print("=" * 70)
    print("VAIDYAARC PHASE 8B VALIDATION SUITE")
    print("=" * 70)
    
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
            
    print("-" * 70)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
