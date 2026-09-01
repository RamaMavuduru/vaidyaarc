"""
Fast Deterministic Validation Suite for Phase 4: Care Navigation & Facility Matching.

Zero-LLM latency (<1s execution).
Validates all 10 required tests, safety invariants, distance calculations, and schema integrity.
"""

from app.care_navigation_node import care_navigation
from app.care_navigation_schema import (
    Location,
    HealthcareFacility,
    FacilityMatchResult,
    CareNavigationOutput,
)
from app.facility_matching import haversine_distance, match_and_rank_facilities
from app.facility_repository import MockFacilityRepository


def run_phase4_validation():
    print("=" * 80)
    print("RUNNING PHASE 4 DIRECT VALIDATION SUITE (FAST / ZERO-LLM)")
    print("=" * 80)

    repo = MockFacilityRepository()

    # -------------------------------------------------------------
    # TEST 1: Emergency patient + location + emergency-capable facilities
    # -------------------------------------------------------------
    state_emergency = {
        "patient_id": "P001",
        "session_id": "S001",
        "information_complete": True,
        "immediate_attention_required": True,
        "red_flag_status": "red_flags_detected",
        "risk_level": "URGENT",
        "risk_score": 55,
        "patient_location": {"city": "Hyderabad", "latitude": 17.4300, "longitude": 78.4000},
        "clinical_case": {"care_pathway_status": "emergency"},
    }
    res1 = care_navigation(state_emergency)
    assert res1["care_navigation_status"] == "matched", f"Expected 'matched', got {res1['care_navigation_status']}"
    assert len(res1["matched_facilities"]) > 0, "Expected at least 1 matched facility"
    for match in res1["matched_facilities"]:
        fac = match["facility"]
        assert fac["emergency_services"] is True, f"Non-emergency facility included in emergency pathway: {fac['facility_name']}"
        assert match["emergency_match"] is True
    print("TEST 1 (Emergency Patient Matching & Non-Emergency Exclusion): PASS")

    # -------------------------------------------------------------
    # TEST 2: Urgent patient -> appropriate hospital/clinic facilities returned
    # -------------------------------------------------------------
    state_urgent = {
        "patient_id": "P002",
        "session_id": "S002",
        "information_complete": True,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
        "risk_level": "HIGH",
        "risk_score": 35,
        "patient_location": {"city": "Hyderabad", "latitude": 17.4300, "longitude": 78.4000},
        "clinical_case": {"care_pathway_status": "urgent"},
    }
    res2 = care_navigation(state_urgent)
    assert res2["care_navigation_status"] == "matched"
    assert len(res2["matched_facilities"]) > 0
    top_fac = res2["matched_facilities"][0]["facility"]
    assert top_fac["facility_type"] in ["tertiary_hospital", "hospital", "community_health_centre"]
    print("TEST 2 (Urgent Patient Hospital/Clinical Matching): PASS")

    # -------------------------------------------------------------
    # TEST 3: Routine patient -> routine outpatient facilities returned
    # -------------------------------------------------------------
    state_routine = {
        "patient_id": "P003",
        "session_id": "S003",
        "information_complete": True,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
        "risk_level": "LOW",
        "risk_score": 10,
        "patient_location": {"city": "Hyderabad", "latitude": 17.4450, "longitude": 78.3900},
        "clinical_case": {"care_pathway_status": "routine"},
    }
    res3 = care_navigation(state_routine)
    assert res3["care_navigation_status"] == "matched"
    assert len(res3["matched_facilities"]) > 0
    # Top match should be a nearby outpatient/primary health centre
    top_match = res3["matched_facilities"][0]
    assert top_match["capability_match"] is True
    print("TEST 3 (Routine Patient Outpatient Matching): PASS")

    # -------------------------------------------------------------
    # TEST 4: No patient location -> location_required
    # -------------------------------------------------------------
    state_no_loc = {
        "patient_id": "P004",
        "session_id": "S004",
        "information_complete": True,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
        "risk_level": "LOW",
        "risk_score": 10,
        "patient_location": None,
        "patient_profile": {},
        "clinical_case": {"care_pathway_status": "routine"},
    }
    res4 = care_navigation(state_no_loc)
    assert res4["care_navigation_status"] == "location_required"
    assert len(res4["matched_facilities"]) == 0
    assert "location is required" in res4["navigation_explanation"].lower()
    print("TEST 4 (Missing Location Produces 'location_required' Without Fabrication): PASS")

    # -------------------------------------------------------------
    # TEST 5: No matching facility in unknown location -> no_facility_found
    # -------------------------------------------------------------
    state_unknown_city = {
        "patient_id": "P005",
        "session_id": "S005",
        "information_complete": True,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
        "risk_level": "LOW",
        "risk_score": 10,
        "patient_location": {"city": "Varanasi", "state": "Uttar Pradesh"},
        "clinical_case": {"care_pathway_status": "routine"},
    }
    res5 = care_navigation(state_unknown_city)
    assert res5["care_navigation_status"] == "no_facility_found"
    assert len(res5["matched_facilities"]) == 0
    assert "no healthcare facilities found" in res5["navigation_explanation"].lower()
    print("TEST 5 (Unknown Location Produces 'no_facility_found' Without False Recommendations): PASS")

    # -------------------------------------------------------------
    # TEST 6: Distance ranking -> closer suitable facility ranks above farther
    # -------------------------------------------------------------
    # Hyderabad patient right next to Jubilee Hills (17.4325, 78.4072)
    # Apex Hospital is at (17.4325, 78.4072) -> ~0 km
    # City Central Hospital is at (17.4411, 78.4983) -> ~9.7 km
    test_loc = Location(city="Hyderabad", latitude=17.4325, longitude=78.4072)
    hyd_facilities = repo.get_facilities(city="Hyderabad")
    ranked = match_and_rank_facilities(
        facilities=hyd_facilities,
        care_pathway="emergency",
        risk_level="URGENT",
        immediate_attention_required=True,
        patient_location=test_loc,
    )
    # Apex Hospital must rank higher than City Central Hospital
    assert ranked[0].facility.facility_id == "SYN_HYD_HOSP_001", f"Expected Apex Hosp first, got {ranked[0].facility.facility_name}"
    assert ranked[0].distance_km < ranked[1].distance_km
    assert ranked[0].match_score >= ranked[1].match_score
    print("TEST 6 (Proximity Ranking - Closer Facility Ranks Higher): PASS")

    # -------------------------------------------------------------
    # TEST 7: Unverified facility -> verification status remains visible
    # -------------------------------------------------------------
    unverified_fac = [f for f in hyd_facilities if f.verification_status == "unverified"][0]
    assert unverified_fac.verification_status == "unverified"
    ranked_routine = match_and_rank_facilities(
        facilities=[unverified_fac],
        care_pathway="routine",
        risk_level="LOW",
        immediate_attention_required=False,
        patient_location=test_loc,
    )
    assert ranked_routine[0].verification_score == 0.0
    assert any("unverified" in r.lower() for r in ranked_routine[0].matching_reasons)
    print("TEST 7 (Unverified Facility Transparency): PASS")

    # -------------------------------------------------------------
    # TEST 8: Phase 2A emergency override -> Phase 4 cannot downgrade
    # -------------------------------------------------------------
    state_override = {
        "patient_id": "P008",
        "session_id": "S008",
        "information_complete": True,
        "immediate_attention_required": True,  # Phase 2A Red Flag
        "red_flag_status": "red_flags_detected",
        "risk_level": "LOW",  # Mismatched/low upstream risk
        "risk_score": 10,
        "patient_location": {"city": "Hyderabad", "latitude": 17.4300, "longitude": 78.4000},
        "clinical_case": {"care_pathway_status": "routine"},  # Erroneous/routine pathway
    }
    res8 = care_navigation(state_override)
    # Must enforce emergency pathway because immediate_attention_required is True!
    assert res8["care_navigation_output"]["care_pathway"] == "emergency"
    for match in res8["matched_facilities"]:
        assert match["facility"]["emergency_services"] is True
    print("TEST 8 (Phase 2A Emergency Override Immutable in Phase 4): PASS")

    # -------------------------------------------------------------
    # TEST 9: Phase 2B risk score & level preservation
    # -------------------------------------------------------------
    state_preservation = {
        "patient_id": "P009",
        "session_id": "S009",
        "information_complete": True,
        "immediate_attention_required": False,
        "red_flag_status": "no_obvious_red_flags",
        "risk_level": "MODERATE",
        "risk_score": 25,
        "patient_location": {"city": "Hyderabad"},
        "clinical_case": {"care_pathway_status": "routine"},
    }
    res9 = care_navigation(state_preservation)
    # Verify Phase 4 does not return or mutate risk_level/risk_score
    assert "risk_level" not in res9, "Phase 4 must not overwrite risk_level"
    assert "risk_score" not in res9, "Phase 4 must not overwrite risk_score"
    print("TEST 9 (Phase 2B Risk Level and Score Preservation): PASS")

    # -------------------------------------------------------------
    # TEST 10: Haversine distance accuracy & Pydantic Schema Validation
    # -------------------------------------------------------------
    # Distance between Mumbai (19.0760, 72.8777) and Delhi (28.6139, 77.2090) is ~ 1148 km
    calc_dist = haversine_distance(19.0760, 72.8777, 28.6139, 77.2090)
    assert 1140.0 < calc_dist < 1160.0, f"Unexpected distance: {calc_dist}"

    # Pydantic schema validation on full output
    output_obj = CareNavigationOutput(**res1["care_navigation_output"])
    assert output_obj.navigation_status == "matched"
    assert output_obj.top_facility_id == "SYN_HYD_HOSP_001"
    print("TEST 10 (Haversine Accuracy & Pydantic Schema Validation): PASS")

    print("=" * 80)
    print("ALL 10 PHASE 4 DIRECT VALIDATION TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_validation()
