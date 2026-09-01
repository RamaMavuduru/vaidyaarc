"""
Phase 4: Care Navigation Node.

LangGraph node for healthcare facility discovery, matching, and ranking.
Consumes upstream Phase 2A, Phase 2B, and Phase 3 signals deterministically.
NO LLM CALLS. ZERO DIAGNOSTIC INFERENCE.
"""

from typing import Any, Optional

from app.state import VaidyaArcState
from app.care_navigation_schema import (
    Location,
    CareNavigationOutput,
)
from app.facility_repository import MockFacilityRepository
from app.facility_matching import match_and_rank_facilities


def _extract_patient_location(state: VaidyaArcState) -> Optional[Location]:
    """
    Extract structured patient location from state or patient profile.
    Returns None if no location information is available.
    """
    raw_loc = state.get("patient_location")
    if raw_loc:
        if isinstance(raw_loc, Location):
            return raw_loc
        if isinstance(raw_loc, dict):
            return Location(**raw_loc)

    # Fallback to patient_profile location if present
    profile = state.get("patient_profile", {})
    profile_loc = profile.get("location")
    if profile_loc:
        if isinstance(profile_loc, Location):
            return profile_loc
        if isinstance(profile_loc, dict):
            return Location(**profile_loc)
        if isinstance(profile_loc, str) and profile_loc.strip():
            return Location(city=profile_loc.strip())

    return None


def care_navigation(state: VaidyaArcState) -> dict[str, Any]:
    """
    Phase 4 Care Navigation Node.
    
    Transforms clinical case context, safety findings, and patient location
    into a ranked list of matched healthcare facilities.
    """
    warnings: list[str] = []

    try:
        # -------------------------------------------------------------
        # 1. UPSTREAM SIGNALS & SAFETY HIERARCHY ENFORCEMENT
        # -------------------------------------------------------------
        immediate_attention = state.get("immediate_attention_required", False)
        risk_level = state.get("risk_level", "LOW")
        clinical_case = state.get("clinical_case") or {}
        raw_care_pathway = clinical_case.get("care_pathway_status", "routine")

        # STRICT SAFETY HIERARCHY:
        # If immediate_attention_required == True, pathway is strictly locked to emergency.
        if immediate_attention:
            effective_pathway = "emergency"
        else:
            effective_pathway = raw_care_pathway

        # Check for incomplete clinical intake
        if not state.get("information_complete") and effective_pathway == "incomplete":
            nav_output = CareNavigationOutput(
                navigation_status="incomplete_case",
                care_pathway="incomplete",
                patient_location=None,
                matched_facilities=[],
                navigation_explanation="Intake is incomplete. Complete intake is required before care navigation.",
                navigation_source="mock_repository",
                total_facilities_evaluated=0,
                top_facility_id=None,
                validation_warnings=["Incomplete clinical case representation"],
            )
            return {
                "care_navigation_status": "incomplete_case",
                "matched_facilities": [],
                "navigation_explanation": nav_output.navigation_explanation,
                "navigation_source": nav_output.navigation_source,
                "care_navigation_output": nav_output.model_dump(),
            }

        # -------------------------------------------------------------
        # 2. PATIENT LOCATION RESOLUTION
        # -------------------------------------------------------------
        patient_location = _extract_patient_location(state)

        if not patient_location or (not patient_location.city and patient_location.latitude is None):
            # Location is missing: DO NOT FABRICATE FACILITIES
            nav_output = CareNavigationOutput(
                navigation_status="location_required",
                care_pathway=effective_pathway,
                patient_location=None,
                matched_facilities=[],
                navigation_explanation=(
                    "Patient location is required to identify nearby healthcare facilities. "
                    "No facilities have been recommended without location context."
                ),
                navigation_source="mock_repository",
                total_facilities_evaluated=0,
                top_facility_id=None,
                validation_warnings=["Missing patient location"],
            )
            return {
                "patient_location": None,
                "care_navigation_status": "location_required",
                "matched_facilities": [],
                "navigation_explanation": nav_output.navigation_explanation,
                "navigation_source": nav_output.navigation_source,
                "care_navigation_output": nav_output.model_dump(),
            }

        # -------------------------------------------------------------
        # 3. FACILITY DISCOVERY VIA REPOSITORY
        # -------------------------------------------------------------
        repo = MockFacilityRepository()
        candidate_facilities = repo.get_facilities(
            city=patient_location.city,
            state=patient_location.state,
            lat=patient_location.latitude,
            lon=patient_location.longitude,
        )

        if not candidate_facilities:
            nav_output = CareNavigationOutput(
                navigation_status="no_facility_found",
                care_pathway=effective_pathway,
                patient_location=patient_location,
                matched_facilities=[],
                navigation_explanation=(
                    f"No healthcare facilities found in the facility registry for "
                    f"{patient_location.city or 'the provided location'}."
                ),
                navigation_source="mock_repository",
                total_facilities_evaluated=0,
                top_facility_id=None,
                validation_warnings=[f"No registered facilities in {patient_location.city}"],
            )
            return {
                "patient_location": patient_location.model_dump(),
                "care_navigation_status": "no_facility_found",
                "matched_facilities": [],
                "navigation_explanation": nav_output.navigation_explanation,
                "navigation_source": nav_output.navigation_source,
                "care_navigation_output": nav_output.model_dump(),
            }

        # -------------------------------------------------------------
        # 4. DETERMINISTIC MATCHING & RANKING
        # -------------------------------------------------------------
        ranked_matches = match_and_rank_facilities(
            facilities=candidate_facilities,
            care_pathway=effective_pathway,
            risk_level=risk_level,
            immediate_attention_required=immediate_attention,
            patient_location=patient_location,
        )

        # For emergency pathway, filter out incompatible (non-emergency) facilities from recommendations
        if effective_pathway == "emergency":
            suitable_matches = [m for m in ranked_matches if m.emergency_match and m.match_tier != "INCOMPATIBLE"]
        else:
            suitable_matches = [m for m in ranked_matches if m.match_tier != "INCOMPATIBLE"]

        if not suitable_matches:
            nav_output = CareNavigationOutput(
                navigation_status="no_facility_found",
                care_pathway=effective_pathway,
                patient_location=patient_location,
                matched_facilities=[],
                navigation_explanation=(
                    f"No facilities with suitable capabilities for {effective_pathway} care "
                    f"were found in {patient_location.city}."
                ),
                navigation_source="mock_repository",
                total_facilities_evaluated=len(candidate_facilities),
                top_facility_id=None,
                validation_warnings=["No capability-compatible facilities found"],
            )
            return {
                "patient_location": patient_location.model_dump(),
                "care_navigation_status": "no_facility_found",
                "matched_facilities": [],
                "navigation_explanation": nav_output.navigation_explanation,
                "navigation_source": nav_output.navigation_source,
                "care_navigation_output": nav_output.model_dump(),
            }

        top_match = suitable_matches[0]
        top_facility_id = top_match.facility.facility_id

        # Generate factual explanation
        if effective_pathway == "emergency":
            explanation = (
                f"Emergency pathway active. Identified {len(suitable_matches)} emergency-capable facility(ies) "
                f"in {patient_location.city}. Top match: {top_match.facility.facility_name}."
            )
        elif effective_pathway == "urgent":
            explanation = (
                f"Urgent care pathway. Identified {len(suitable_matches)} suitable hospital/clinical facility(ies) "
                f"in {patient_location.city}. Top match: {top_match.facility.facility_name}."
            )
        else:
            explanation = (
                f"Routine care pathway. Identified {len(suitable_matches)} outpatient/primary care facility(ies) "
                f"in {patient_location.city}. Top match: {top_match.facility.facility_name}."
            )

        # Record warnings for unverified facilities
        for m in suitable_matches:
            if m.facility.verification_status != "verified":
                warnings.append(f"Facility {m.facility.facility_name} is unverified ({m.facility.source})")

        nav_output = CareNavigationOutput(
            navigation_status="matched",
            care_pathway=effective_pathway,
            patient_location=patient_location,
            matched_facilities=suitable_matches,
            navigation_explanation=explanation,
            navigation_source="mock_repository",
            total_facilities_evaluated=len(candidate_facilities),
            top_facility_id=top_facility_id,
            validation_warnings=warnings,
        )

        return {
            "patient_location": patient_location.model_dump(),
            "care_navigation_status": "matched",
            "matched_facilities": [m.model_dump() for m in suitable_matches],
            "navigation_explanation": explanation,
            "navigation_source": "synthetic_test_data",
            "care_navigation_output": nav_output.model_dump(),
        }

    except Exception as e:
        error_msg = f"Care navigation failed: {str(e)}"
        return {
            "care_navigation_status": "failed",
            "matched_facilities": [],
            "navigation_explanation": error_msg,
            "navigation_source": "mock_repository",
            "care_navigation_output": None,
        }

