"""
Phase 4: Deterministic Facility Matching & Ranking Engine.

Evaluates healthcare facilities against patient care pathway, risk level,
emergency status, and geographic proximity using transparent, non-diagnostic criteria.
NO LLM CALLS. PURELY DETERMINISTIC.
"""

import math
from typing import Optional

from app.care_navigation_schema import (
    HealthcareFacility,
    FacilityMatchResult,
    Location,
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers.
    """
    # Earth radius in kilometers
    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(r * c, 2)


def match_and_rank_facilities(
    facilities: list[HealthcareFacility],
    care_pathway: str,
    risk_level: str,
    immediate_attention_required: bool,
    patient_location: Optional[Location] = None,
    required_capabilities: Optional[list[str]] = None,
) -> list[FacilityMatchResult]:
    """
    Deterministically match and rank healthcare facilities.
    
    Safety rules:
    - If immediate_attention_required == True: care pathway is strictly emergency.
    - Emergency pathway strictly requires emergency-capable facilities (non-emergency excluded or marked incompatible).
    - Transparent reasons generated for every evaluated facility.
    - No diagnostic or medical superiority claims.
    """
    # Safety assertion: Immediate attention strictly enforces emergency pathway
    effective_pathway = "emergency" if immediate_attention_required else care_pathway.lower()

    match_results: list[FacilityMatchResult] = []

    for facility in facilities:
        reasons: list[str] = []
        base_score = 0.0
        distance_score = 0.0
        verification_score = 0.0

        capability_match = False
        emergency_match = False
        is_incompatible = False

        # -------------------------------------------------------------
        # 1. CARE PATHWAY & CAPABILITY EVALUATION
        # -------------------------------------------------------------
        if effective_pathway == "emergency":
            if facility.emergency_services:
                capability_match = True
                emergency_match = True
                base_score += 45.0
                reasons.append("Facility provides dedicated, active emergency department services")
                if "trauma_care" in facility.capabilities or "icu" in facility.capabilities:
                    base_score += 10.0
                    reasons.append("Advanced trauma / critical care capabilities available")
            else:
                capability_match = False
                emergency_match = False
                is_incompatible = True
                reasons.append("Non-emergency facility: unsuitable for emergency care pathway")

        elif effective_pathway == "urgent":
            if facility.facility_type in ["tertiary_hospital", "hospital", "community_health_centre"]:
                capability_match = True
                base_score += 40.0
                reasons.append(f"Facility type ({facility.facility_type}) suitable for urgent clinical evaluation")
            elif facility.facility_type in ["clinic", "primary_health_centre"]:
                capability_match = True
                base_score += 25.0
                reasons.append(f"Outpatient facility ({facility.facility_type}) with general clinical capabilities")
            else:
                capability_match = True
                base_score += 20.0
                reasons.append("General healthcare facility available for consultation")

            if facility.emergency_services:
                emergency_match = True
                base_score += 10.0
                reasons.append("Emergency-capable facility providing higher escalation capacity if needed")

        elif effective_pathway in ["routine", "follow_up"]:
            capability_match = True
            if facility.facility_type in ["clinic", "primary_health_centre", "community_health_centre"]:
                base_score += 45.0
                reasons.append(f"Primary / outpatient facility ({facility.facility_type}) well-suited for routine care")
            elif facility.facility_type in ["hospital", "tertiary_hospital"]:
                base_score += 35.0
                reasons.append("Hospital outpatient department capable of routine consultation")
            else:
                base_score += 25.0
                reasons.append("Healthcare facility available for general consultation")

        else:
            # Incomplete or unspecified care pathway
            capability_match = True
            base_score += 20.0
            reasons.append("General facility capabilities evaluated for preliminary review")

        # -------------------------------------------------------------
        # 2. GEOGRAPHIC PROXIMITY & DISTANCE EVALUATION
        # -------------------------------------------------------------
        dist_km: Optional[float] = None
        if (
            patient_location
            and patient_location.latitude is not None
            and patient_location.longitude is not None
            and facility.latitude is not None
            and facility.longitude is not None
        ):
            dist_km = haversine_distance(
                patient_location.latitude,
                patient_location.longitude,
                facility.latitude,
                facility.longitude,
            )
            reasons.append(f"Estimated distance: {dist_km:.1f} km from patient location")

            if dist_km < 5.0:
                distance_score = 30.0
                reasons.append("Proximity: Very close to patient (< 5 km)")
            elif dist_km < 10.0:
                distance_score = 20.0
                reasons.append("Proximity: Nearby facility (5-10 km)")
            elif dist_km < 25.0:
                distance_score = 10.0
                reasons.append("Proximity: Moderate distance (10-25 km)")
            else:
                distance_score = 5.0
                reasons.append("Proximity: Extended distance (> 25 km)")
        else:
            # Distance coordinates not available
            distance_score = 15.0
            reasons.append("Precise distance unavailable (coordinates not provided)")

        # -------------------------------------------------------------
        # 3. VERIFICATION STATUS EVALUATION
        # -------------------------------------------------------------
        if facility.verification_status == "verified":
            verification_score = 15.0
            reasons.append(f"Facility verification: Verified (source: {facility.source})")
        elif facility.verification_status == "pending":
            verification_score = 5.0
            reasons.append(f"Facility verification: Pending verification (source: {facility.source})")
        else:
            verification_score = 0.0
            reasons.append(f"Facility verification: Unverified entry (source: {facility.source})")

        # -------------------------------------------------------------
        # 4. OPERATING HOURS (OPTIONAL METADATA ONLY)
        # -------------------------------------------------------------
        if facility.operating_hours_reliable and facility.operating_hours:
            reasons.append(f"Operating hours verified: {facility.operating_hours}")
            if facility.operating_hours == "24/7":
                base_score += 5.0
        elif facility.operating_hours:
            reasons.append(f"Reported operating hours (unverified metadata): {facility.operating_hours}")

        # -------------------------------------------------------------
        # 5. AGGREGATE MATCH SCORE & TIER DETERMINATION
        # -------------------------------------------------------------
        if is_incompatible:
            total_score = 0.0
            match_tier = "INCOMPATIBLE"
            match_summary = (
                f"{facility.facility_name} is not suitable for {effective_pathway} care "
                f"because it lacks required emergency services."
            )
        else:
            total_score = min(100.0, round(base_score + distance_score + verification_score, 1))
            if total_score >= 70.0:
                match_tier = "HIGH"
                match_summary = (
                    f"Strong match for {effective_pathway} care pathway based on available facility capabilities "
                    f"and geographic proximity."
                )
            elif total_score >= 45.0:
                match_tier = "MODERATE"
                match_summary = (
                    f"Suitable match for {effective_pathway} care pathway based on available facility data."
                )
            else:
                match_tier = "LOW"
                match_summary = (
                    f"Low match for {effective_pathway} care pathway based on available facility data."
                )

        match_results.append(
            FacilityMatchResult(
                facility=facility,
                distance_km=dist_km,
                match_score=total_score,
                match_tier=match_tier,
                capability_match=capability_match,
                emergency_match=emergency_match,
                distance_score=distance_score,
                verification_score=verification_score,
                matching_reasons=reasons,
                match_summary=match_summary,
            )
        )

    # -----------------------------------------------------------------
    # 6. DETERMINISTIC SORTING / RANKING
    # Primary: match_score DESC
    # Secondary: distance_km ASC (None treated as infinity)
    # Tertiary: facility_id ASC (for pure determinism)
    # -----------------------------------------------------------------
    def sort_key(res: FacilityMatchResult):
        dist = res.distance_km if res.distance_km is not None else 999999.0
        return (-res.match_score, dist, res.facility.facility_id)

    ranked_results = sorted(match_results, key=sort_key)
    return ranked_results

