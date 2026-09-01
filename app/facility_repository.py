"""
Phase 4: Facility Repository Interface and Mock Implementation.

Provides an extensible repository abstraction for healthcare facility discovery.
Designed to be backed by ABDM Health Facility Registry (HFR), state health registries,
or synthetic test datasets.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.care_navigation_schema import HealthcareFacility


class FacilityRepository(ABC):
    """Abstract interface for healthcare facility discovery."""

    @abstractmethod
    def get_facilities(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
    ) -> list[HealthcareFacility]:
        """Query facilities based on geographic criteria."""
        pass

    @abstractmethod
    def get_facility_by_id(self, facility_id: str) -> Optional[HealthcareFacility]:
        """Fetch a specific facility by its unique identifier."""
        pass


class MockFacilityRepository(FacilityRepository):
    """
    In-memory mock repository containing clearly-marked synthetic facilities.
    Used for local testing and deterministic validation.
    """

    def __init__(self):
        self._facilities: list[HealthcareFacility] = [
            # -------------------------------------------------------------
            # HYDERABAD REGION SYNTHETIC DATA
            # -------------------------------------------------------------
            HealthcareFacility(
                facility_id="SYN_HYD_HOSP_001",
                facility_name="Apex Emergency & Multispecialty Hospital",
                facility_type="tertiary_hospital",
                address="Plot 12, Health City, Jubilee Hills",
                city="Hyderabad",
                state="Telangana",
                latitude=17.4325,
                longitude=78.4072,
                emergency_services=True,
                capabilities=[
                    "emergency_care",
                    "trauma_care",
                    "icu",
                    "cardiology",
                    "general_medicine",
                    "radiology",
                    "inpatient",
                ],
                operating_hours="24/7",
                operating_hours_reliable=True,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-15T10:00:00Z",
                contact_number="+91-40-5550101",
                tier="tertiary",
            ),
            HealthcareFacility(
                facility_id="SYN_HYD_HOSP_002",
                facility_name="City Central General Hospital",
                facility_type="hospital",
                address="45 Station Road, Secunderabad",
                city="Hyderabad",
                state="Telangana",
                latitude=17.4411,
                longitude=78.4983,
                emergency_services=True,
                capabilities=[
                    "emergency_care",
                    "general_medicine",
                    "surgery",
                    "icu",
                    "pediatrics",
                    "inpatient",
                ],
                operating_hours="24/7",
                operating_hours_reliable=True,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-10T11:30:00Z",
                contact_number="+91-40-5550102",
                tier="secondary",
            ),
            HealthcareFacility(
                facility_id="SYN_HYD_CHC_003",
                facility_name="Banjara Community Health Centre",
                facility_type="community_health_centre",
                address="Road No 10, Banjara Hills",
                city="Hyderabad",
                state="Telangana",
                latitude=17.4156,
                longitude=78.4350,
                emergency_services=False,
                capabilities=[
                    "general_medicine",
                    "outpatient",
                    "maternal_health",
                    "minor_procedures",
                    "diagnostic_lab",
                ],
                operating_hours="08:00-20:00",
                operating_hours_reliable=False,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-07-20T09:00:00Z",
                contact_number="+91-40-5550103",
                tier="secondary",
            ),
            HealthcareFacility(
                facility_id="SYN_HYD_PHC_004",
                facility_name="Madhapur Primary Health Clinic",
                facility_type="primary_health_centre",
                address="Hitech City Main Road, Madhapur",
                city="Hyderabad",
                state="Telangana",
                latitude=17.4483,
                longitude=78.3915,
                emergency_services=False,
                capabilities=[
                    "general_medicine",
                    "outpatient",
                    "routine_consultation",
                    "immunization",
                ],
                operating_hours="09:00-17:00",
                operating_hours_reliable=False,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-01T14:00:00Z",
                contact_number="+91-40-5550104",
                tier="primary",
            ),
            HealthcareFacility(
                facility_id="SYN_HYD_CLIN_005",
                facility_name="Greenwood Family Medical Clinic",
                facility_type="clinic",
                address="Lane 3, Gachibowli",
                city="Hyderabad",
                state="Telangana",
                latitude=17.4401,
                longitude=78.3489,
                emergency_services=False,
                capabilities=[
                    "outpatient",
                    "general_medicine",
                    "preventive_care",
                ],
                operating_hours="09:00-18:00",
                operating_hours_reliable=False,
                source="synthetic_test_data",
                verification_status="unverified",
                last_verified=None,
                contact_number="+91-40-5550105",
                tier="primary",
            ),
            # -------------------------------------------------------------
            # BENGALURU REGION SYNTHETIC DATA
            # -------------------------------------------------------------
            HealthcareFacility(
                facility_id="SYN_BLR_HOSP_001",
                facility_name="Bengaluru Trauma & Emergency Institute",
                facility_type="tertiary_hospital",
                address="100 Feet Road, Indiranagar",
                city="Bengaluru",
                state="Karnataka",
                latitude=12.9719,
                longitude=77.6412,
                emergency_services=True,
                capabilities=[
                    "emergency_care",
                    "trauma_care",
                    "icu",
                    "cardiology",
                    "general_medicine",
                    "inpatient",
                ],
                operating_hours="24/7",
                operating_hours_reliable=True,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-20T10:00:00Z",
                contact_number="+91-80-5550201",
                tier="tertiary",
            ),
            HealthcareFacility(
                facility_id="SYN_BLR_PHC_002",
                facility_name="Koramangala Community Clinic",
                facility_type="clinic",
                address="5th Block, Koramangala",
                city="Bengaluru",
                state="Karnataka",
                latitude=12.9352,
                longitude=77.6245,
                emergency_services=False,
                capabilities=[
                    "outpatient",
                    "general_medicine",
                    "routine_consultation",
                ],
                operating_hours="09:00-17:00",
                operating_hours_reliable=False,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-12T09:00:00Z",
                contact_number="+91-80-5550202",
                tier="primary",
            ),
            # -------------------------------------------------------------
            # DELHI REGION SYNTHETIC DATA
            # -------------------------------------------------------------
            HealthcareFacility(
                facility_id="SYN_DEL_HOSP_001",
                facility_name="National Capital Emergency Centre",
                facility_type="hospital",
                address="Ring Road, Lajpat Nagar",
                city="Delhi",
                state="Delhi",
                latitude=28.5677,
                longitude=77.2433,
                emergency_services=True,
                capabilities=[
                    "emergency_care",
                    "icu",
                    "general_medicine",
                    "inpatient",
                ],
                operating_hours="24/7",
                operating_hours_reliable=True,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-08-18T16:00:00Z",
                contact_number="+91-11-5550301",
                tier="tertiary",
            ),
            HealthcareFacility(
                facility_id="SYN_DEL_CLIN_002",
                facility_name="South Delhi Family Care Clinic",
                facility_type="clinic",
                address="C-Block, Greater Kailash 1",
                city="Delhi",
                state="Delhi",
                latitude=28.5529,
                longitude=77.2372,
                emergency_services=False,
                capabilities=[
                    "outpatient",
                    "general_medicine",
                    "routine_consultation",
                ],
                operating_hours="09:00-19:00",
                operating_hours_reliable=False,
                source="synthetic_test_data",
                verification_status="verified",
                last_verified="2026-07-25T11:00:00Z",
                contact_number="+91-11-5550302",
                tier="primary",
            ),
        ]

    def get_facilities(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
    ) -> list[HealthcareFacility]:
        """Filter facilities by city/state or return all."""
        results = self._facilities

        if city:
            city_clean = city.strip().lower()
            results = [f for f in results if f.city.strip().lower() == city_clean]

        if state and not results:
            state_clean = state.strip().lower()
            results = [f for f in self._facilities if f.state.strip().lower() == state_clean]

        return results

    def get_facility_by_id(self, facility_id: str) -> Optional[HealthcareFacility]:
        """Find facility by ID."""
        for f in self._facilities:
            if f.facility_id == facility_id:
                return f
        return None

