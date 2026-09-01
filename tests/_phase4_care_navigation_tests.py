"""
Integration Test Suite for Phase 4: Care Navigation & Facility Matching.

Tests full LangGraph workflow execution with Phase 4 Care Navigation node,
validating end-to-end traversal from intake completion to facility recommendations.
"""

from app.workflow import build_vaidyaarc_graph
from app.care_navigation_node import care_navigation
from app.facility_matching import match_and_rank_facilities
from app.facility_repository import MockFacilityRepository
from app.care_navigation_schema import Location


def fresh_state():
    """Create a fresh patient state for testing."""
    return {
        "patient_id": "TEST_P_NAV",
        "session_id": "TEST_S_NAV",
        "language": "English",
        "patient_profile": {
            "age": 45,
            "medical_conditions": [],
            "allergies": [],
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],
        "red_flag_status": None,
        "red_flags": [],
        "red_flag_evidence": [],
        "immediate_attention_required": False,
        "red_flag_rule_hits": [],
        "risk_level": None,
        "risk_score": None,
        "risk_signal_summary": [],
        "risk_contributing_factors": [],
        "risk_evidence": [],
        "risk_reasoning": None,
        "risk_override_reason": None,
        "recommended_next_action": None,
        "risk_rule_hits": [],
        "convergence_status": None,
        "risk_context_flags": [],
        "risk_assessment_version": None,
        "patient_location": None,
    }


def test_full_graph_emergency_flow():
    """
    Test 1: Full graph execution with complete severe chest pain + location -> emergency facility matched.
    """
    print("\n" + "=" * 80)
    print("TEST 1: FULL GRAPH EMERGENCY FLOW")
    print("=" * 80)

    graph = build_vaidyaarc_graph()

    state = fresh_state()
    state.update({
        "chief_complaint": "severe chest pain",
        "nature_of_pain": "crushing pressure",
        "location": "center of chest",
        "duration": "since today morning",
        "severity": "very severe",
        "associated_symptoms": ["shortness of breath"],
        "information_complete": True,
        "missing_information": [],
        "patient_location": {"city": "Hyderabad", "latitude": 17.4300, "longitude": 78.4000},
    })

    result = graph.invoke(state)

    print("Information Complete:", result.get("information_complete"))
    print("Red Flag Status:", result.get("red_flag_status"))
    print("Immediate Attention Required:", result.get("immediate_attention_required"))
    print("Risk Level:", result.get("risk_level"))
    print("Case Generation Status:", result.get("case_generation_status"))
    print("Care Navigation Status:", result.get("care_navigation_status"))
    print("Navigation Explanation:", result.get("navigation_explanation"))

    assert result.get("care_navigation_status") == "matched"
    assert result.get("immediate_attention_required") is True
    matched = result.get("matched_facilities") or []
    assert len(matched) > 0
    # Every recommended facility must have emergency services
    for m in matched:
        assert m["facility"]["emergency_services"] is True
    print("[PASS] TEST 1: Full Graph Emergency Flow Passed")


def test_full_graph_routine_flow():
    """
    Test 2: Full graph execution with mild fever + location -> outpatient clinic matched.
    """
    print("\n" + "=" * 80)
    print("TEST 2: FULL GRAPH ROUTINE FLOW")
    print("=" * 80)

    graph = build_vaidyaarc_graph()

    state = fresh_state()
    state.update({
        "chief_complaint": "fever",
        "duration": "today morning",
        "severity": "mild",
        "information_complete": True,
        "missing_information": [],
        "patient_location": {"city": "Bengaluru", "latitude": 12.9350, "longitude": 77.6250},
    })

    result = graph.invoke(state)

    print("Information Complete:", result.get("information_complete"))
    print("Care Pathway Status:", (result.get("clinical_case") or {}).get("care_pathway_status"))
    print("Care Navigation Status:", result.get("care_navigation_status"))
    top_fac_name = (result.get("matched_facilities") or [{}])[0].get("facility", {}).get("facility_name")
    print("Top Matched Facility:", top_fac_name)

    assert result.get("care_navigation_status") == "matched"
    assert len(result.get("matched_facilities") or []) > 0
    print("[PASS] TEST 2: Full Graph Routine Flow Passed")


def test_missing_location_flow():
    """
    Test 3: Complete intake with missing location -> location_required status without fabrication.
    """
    print("\n" + "=" * 80)
    print("TEST 3: MISSING LOCATION FLOW")
    print("=" * 80)

    state = fresh_state()
    state.update({
        "chief_complaint": "fever",
        "duration": "today morning",
        "severity": "mild",
        "information_complete": True,
        "missing_information": [],
        "patient_location": None,
        "patient_profile": {},
        "clinical_case": {"care_pathway_status": "routine"},
    })

    result = care_navigation(state)

    assert result["care_navigation_status"] == "location_required"
    assert len(result["matched_facilities"]) == 0
    assert "location is required" in result["navigation_explanation"].lower()
    print("[PASS] TEST 3: Missing Location Flow Passed")


def test_safety_override_preservation():
    """
    Test 4: Immediate attention override locks care pathway to emergency and preserves risk scores.
    """
    print("\n" + "=" * 80)
    print("TEST 4: SAFETY OVERRIDE PRESERVATION")
    print("=" * 80)

    state = fresh_state()
    state.update({
        "chief_complaint": "chest pain",
        "duration": "1 hour",
        "severity": "mild",
        "information_complete": True,
        "missing_information": [],
        "immediate_attention_required": True,
        "red_flag_status": "red_flags_detected",
        "risk_level": "LOW",
        "risk_score": 12,
        "patient_location": {"city": "Delhi", "latitude": 28.5600, "longitude": 77.2400},
        "clinical_case": {"care_pathway_status": "routine"},
    })

    result = care_navigation(state)

    # Output care pathway must be emergency
    assert result["care_navigation_output"]["care_pathway"] == "emergency"
    # Matched facilities must only be emergency capable
    for match in result["matched_facilities"]:
        assert match["facility"]["emergency_services"] is True
    # Risk fields are not mutated
    assert "risk_level" not in result
    assert "risk_score" not in result
    print("[PASS] TEST 4: Safety Override Preservation Passed")


def test_distance_ranking_hyderabad():
    """
    Test 5: Geographic distance ranking places closer emergency hospital above farther one.
    """
    print("\n" + "=" * 80)
    print("TEST 5: DISTANCE RANKING HYDERABAD")
    print("=" * 80)

    repo = MockFacilityRepository()
    hyd_facilities = repo.get_facilities(city="Hyderabad")
    loc = Location(city="Hyderabad", latitude=17.4325, longitude=78.4072)

    ranked = match_and_rank_facilities(
        facilities=hyd_facilities,
        care_pathway="emergency",
        risk_level="URGENT",
        immediate_attention_required=True,
        patient_location=loc,
    )

    assert ranked[0].facility.facility_id == "SYN_HYD_HOSP_001"
    assert ranked[0].distance_km < ranked[1].distance_km
    assert ranked[0].match_score >= ranked[1].match_score
    print("[PASS] TEST 5: Distance Ranking Hyderabad Passed")


def test_unverified_facility_transparency():
    """
    Test 6: Unverified facility has verification_score = 0 and visible verification status.
    """
    print("\n" + "=" * 80)
    print("TEST 6: UNVERIFIED FACILITY TRANSPARENCY")
    print("=" * 80)

    repo = MockFacilityRepository()
    hyd_facilities = repo.get_facilities(city="Hyderabad")
    unverified = [f for f in hyd_facilities if f.verification_status == "unverified"][0]

    loc = Location(city="Hyderabad", latitude=17.4400, longitude=78.3500)
    ranked = match_and_rank_facilities(
        facilities=[unverified],
        care_pathway="routine",
        risk_level="LOW",
        immediate_attention_required=False,
        patient_location=loc,
    )

    assert ranked[0].verification_score == 0.0
    assert any("unverified" in r.lower() for r in ranked[0].matching_reasons)
    print("[PASS] TEST 6: Unverified Facility Transparency Passed")


def run_all_tests():
    print("=" * 80)
    print("RUNNING ALL PHASE 4 CARE NAVIGATION INTEGRATION TESTS")
    print("=" * 80)

    test_full_graph_emergency_flow()
    test_full_graph_routine_flow()
    test_missing_location_flow()
    test_safety_override_preservation()
    test_distance_ranking_hyderabad()
    test_unverified_facility_transparency()

    print("\n" + "=" * 80)
    print("ALL PHASE 4 INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

