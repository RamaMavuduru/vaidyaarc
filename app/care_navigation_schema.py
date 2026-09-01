"""
Phase 4: Care Navigation & Facility Matching Schema.

Pydantic models for structured facility representation, location,
matching results, and care navigation outputs.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class Location(BaseModel):
    """Structured location information for patient or facility."""
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State / Province name")
    country: str = Field(default="India", description="Country name")
    latitude: Optional[float] = Field(None, description="Geographic latitude coordinate")
    longitude: Optional[float] = Field(None, description="Geographic longitude coordinate")
    postal_code: Optional[str] = Field(None, description="Postal / PIN code")


class HealthcareFacility(BaseModel):
    """
    Healthcare facility profile.
    
    Can represent data from ABDM Health Facility Registry, government
    healthcare registries, or synthetic test data.
    """
    facility_id: str = Field(..., description="Unique facility identifier")
    facility_name: str = Field(..., description="Facility name")
    facility_type: str = Field(
        ...,
        description="Type of facility (e.g. hospital, clinic, primary_health_centre, community_health_centre, tertiary_hospital)"
    )
    address: str = Field(..., description="Physical address of the facility")
    city: str = Field(..., description="City where facility is located")
    state: str = Field(..., description="State where facility is located")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    emergency_services: bool = Field(
        default=False,
        description="Whether facility has dedicated, active emergency department services"
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of verified capabilities/services (e.g. emergency_care, icu, general_medicine, pediatrics, outpatient)"
    )
    operating_hours: Optional[str] = Field(
        None,
        description="Reported operating hours metadata (e.g. '24/7', '08:00-20:00')"
    )
    operating_hours_reliable: bool = Field(
        default=False,
        description="Whether operating hours are verified and actively monitored"
    )
    source: str = Field(
        default="synthetic_test_data",
        description="Data source (e.g. 'synthetic_test_data', 'abdm_hfr', 'government_registry')"
    )
    verification_status: str = Field(
        default="unverified",
        description="Verification status: 'verified', 'unverified', or 'pending'"
    )
    last_verified: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of last verification"
    )
    contact_number: Optional[str] = Field(
        None,
        description="Facility contact telephone number if available"
    )
    tier: Optional[str] = Field(
        None,
        description="Care tier (e.g. 'primary', 'secondary', 'tertiary')"
    )


class FacilityMatchResult(BaseModel):
    """
    Deterministic evaluation and ranking result for a single facility.
    """
    facility: HealthcareFacility = Field(..., description="Matched healthcare facility")
    distance_km: Optional[float] = Field(None, description="Calculated Haversine distance in kilometers")
    match_score: float = Field(
        ...,
        ge=0.0, le=100.0,
        description="Deterministic compatibility match score (0.0 to 100.0)"
    )
    match_tier: str = Field(
        ...,
        description="Categorical match level: 'HIGH', 'MODERATE', 'LOW', or 'INCOMPATIBLE'"
    )
    capability_match: bool = Field(
        ...,
        description="Whether facility capabilities satisfy the care pathway requirement"
    )
    emergency_match: bool = Field(
        ...,
        description="Whether facility satisfies emergency care requirement if applicable"
    )
    distance_score: float = Field(
        default=0.0,
        description="Component score derived from geographic proximity"
    )
    verification_score: float = Field(
        default=0.0,
        description="Component score derived from facility verification status"
    )
    matching_reasons: list[str] = Field(
        default_factory=list,
        description="Traceable, non-diagnostic reasons for why this facility was matched"
    )
    match_summary: str = Field(
        ...,
        description="Brief summary of facility suitability based on available data"
    )


class CareNavigationOutput(BaseModel):
    """
    Complete output container for Phase 4: Care Navigation & Facility Matching.
    """
    navigation_status: str = Field(
        ...,
        description="One of: 'matched', 'location_required', 'no_facility_found', 'incomplete_case', 'failed'"
    )
    care_pathway: str = Field(
        ...,
        description="The care pathway evaluated ('emergency', 'urgent', 'routine', 'follow_up', 'incomplete')"
    )
    patient_location: Optional[Location] = Field(
        None,
        description="Patient location used for matching"
    )
    matched_facilities: list[FacilityMatchResult] = Field(
        default_factory=list,
        description="Ranked list of suitable healthcare facilities"
    )
    navigation_explanation: str = Field(
        ...,
        description="Factual, explainable overview of the navigation recommendation"
    )
    navigation_source: str = Field(
        default="mock_repository",
        description="Repository source used for facility discovery"
    )
    total_facilities_evaluated: int = Field(
        default=0,
        description="Total number of candidate facilities evaluated"
    )
    top_facility_id: Optional[str] = Field(
        None,
        description="Facility ID of the strongest match if found"
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking warnings (e.g. unverified facilities, unverified hours)"
    )

