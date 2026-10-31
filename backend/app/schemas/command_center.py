"""Pydantic v2 schemas for District & State Public Health Command Center and Disease Surveillance."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.administrative_hierarchy import AdminLevelEnum, GovtDesignationEnum


class OutbreakSeverityEnum(str, Enum):
    """Epidemiological alert classification based on 7-day incident growth rate and R_t."""

    NORMAL = "normal"
    WATCH = "watch"
    ALERT = "alert"
    OUTBREAK = "outbreak"


class DiseaseCategoryEnum(str, Enum):
    """Statutory Integrated Disease Surveillance Programme (IDSP) reportable pathogen categories."""

    DENGUE = "dengue"
    MALARIA = "malaria"
    COVID_19 = "covid_19"
    CHOLERA = "cholera"
    ACUTE_DIARRHEAL_DISEASE = "acute_diarrheal_disease"
    INFLUENZA_H1N1 = "influenza_h1n1"
    MEASLES = "measles"


class FacilityTierEnum(str, Enum):
    """Public healthcare institution classification across Indian health system."""

    PRIMARY_HEALTH_CENTER = "primary_health_center"
    COMMUNITY_HEALTH_CENTER = "community_health_center"
    SUB_DISTRICT_HOSPITAL = "sub_district_hospital"
    DISTRICT_HOSPITAL = "district_hospital"
    TERTIARY_MEDICAL_COLLEGE = "tertiary_medical_college"


class DirectiveCategoryEnum(str, Enum):
    """Sovereign administrative public health directive categories."""

    CONTAINMENT_ZONE = "containment_zone"
    MASKING_ADVISORY = "masking_advisory"
    HOSPITAL_DIVERSION = "hospital_diversion"
    VECTOR_CONTROL = "vector_control"
    PUBLIC_ADVISORY = "public_advisory"


class DiseaseClusterReport(BaseModel):
    """Syndromic and laboratory-confirmed disease cluster surveillance report."""

    id: str = Field(..., description="Unique cluster identifier")
    disease_name: str = Field(..., description="Common disease title (e.g. 'Dengue Serotype 2')")
    disease_category: DiseaseCategoryEnum = Field(..., description="Standardized IDSP disease category")
    jurisdiction_path: str = Field(..., description="PostgreSQL ltree territorial jurisdiction path (e.g. 'india.27.492')")
    territory_name: str = Field(..., description="Human-readable territory name (e.g. 'Pune District')")
    incident_count: int = Field(..., ge=0, description="Active laboratory-confirmed cases")
    seven_day_growth_rate_pct: float = Field(..., description="7-day case trajectory percentage change")
    effective_reproduction_rate_rt: float = Field(..., description="Estimated effective reproduction number (R_t)")
    severity: OutbreakSeverityEnum = Field(..., description="Epidemiological severity tier")
    cluster_centroid_lat: float = Field(..., description="Geographical latitude of cluster centroid")
    cluster_centroid_lng: float = Field(..., description="Geographical longitude of cluster centroid")
    radius_meters: int = Field(..., ge=100, description="Estimated containment perimeter radius in meters")
    first_case_reported_at: datetime = Field(..., description="Timestamp of index cluster case")
    last_case_reported_at: datetime = Field(..., description="Timestamp of latest confirmed case")
    is_contained: bool = Field(default=False, description="Whether containment measures have quelled transmission")

    model_config = ConfigDict(from_attributes=True)


class FacilityResourceTelemetry(BaseModel):
    """Operational critical care bed capacity and ventilator census per public health facility."""

    facility_id: str = Field(..., description="Unique facility identifier or HFR ID")
    facility_name: str = Field(..., description="Official facility title")
    facility_tier: FacilityTierEnum = Field(..., description="Classification tier of the institution")
    jurisdiction_path: str = Field(..., description="LGD territorial path of facility location")
    total_icu_beds: int = Field(..., ge=0, description="Total licensed Intensive Care Unit beds")
    occupied_icu_beds: int = Field(..., ge=0, description="Currently admitted ICU patients")
    available_icu_beds: int = Field(..., ge=0, description="Immediately available staffed ICU beds")
    icu_occupancy_pct: float = Field(..., ge=0.0, le=100.0, description="ICU utilization rate percentage")
    total_ventilator_beds: int = Field(..., ge=0, description="Total mechanical ventilators on site")
    available_ventilators: int = Field(..., ge=0, description="Unoccupied operational mechanical ventilators")
    oxygen_supported_beds: int = Field(..., ge=0, description="Total medical oxygen supported manifold beds")
    available_oxygen_beds: int = Field(..., ge=0, description="Vacant oxygen manifold beds")
    pediatric_icu_beds: int = Field(..., ge=0, description="Dedicated Pediatric Intensive Care Unit (PICU) beds")
    available_picu_beds: int = Field(..., ge=0, description="Vacant PICU beds")
    is_diverting_admissions: bool = Field(default=False, description="Emergency diversion status when occupancy exceeds 85%")
    last_updated_at: datetime = Field(..., description="UTC timestamp of last telemetry sync")

    model_config = ConfigDict(from_attributes=True)


class WorkforceDutyRoster(BaseModel):
    """Active clinical specialist deployment and medical officer duty telemetry."""

    jurisdiction_path: str = Field(..., description="Territorial scope path")
    territory_name: str = Field(..., description="Territory title")
    total_active_physicians: int = Field(..., ge=0, description="Total doctors currently on roster")
    intensivists_on_duty: int = Field(..., ge=0, description="Critical care specialist intensivists active")
    pediatricians_on_duty: int = Field(..., ge=0, description="Pediatric specialists active")
    emergency_physicians_on_duty: int = Field(..., ge=0, description="Casualty/ER physicians on active shift")
    active_nursing_staff: int = Field(..., ge=0, description="Staff nurses on duty")
    doctor_to_patient_ratio: str = Field(..., description="Current doctor-to-admitted patient ratio (e.g. '1:14')")
    coverage_status: str = Field(..., description="'ADEQUATE', 'STRAINED', or 'CRITICAL'")

    model_config = ConfigDict(from_attributes=True)


class PublicHealthDirectiveCreate(BaseModel):
    """Request payload to issue a sovereign public health containment or advisory directive."""

    issuing_officer_id: str = Field(..., description="UUID of the issuing health officer")
    issuing_officer_designation: str = Field(..., description="Designation of authority (e.g. 'CHIEF_MEDICAL_OFFICER')")
    jurisdiction_path: str = Field(..., description="PostgreSQL ltree territorial jurisdiction path for directive")
    directive_category: DirectiveCategoryEnum = Field(..., description="Category of directive")
    headline: str = Field(..., min_length=5, max_length=150, description="Executive headline of public health order")
    details: str = Field(..., min_length=10, max_length=2000, description="Full operational instructions and statutory mandate")
    affected_population_estimate: int = Field(..., ge=0, description="Estimated citizen population under jurisdiction")
    valid_until: datetime = Field(..., description="Expiration timestamp of the directive")


class PublicHealthDirectiveResponse(BaseModel):
    """Response model representing a recorded public health directive."""

    id: str = Field(..., description="Unique directive identifier")
    issuing_officer_id: str = Field(..., description="UUID of issuing authority")
    issuing_officer_designation: str = Field(..., description="Designation of issuing officer")
    jurisdiction_path: str = Field(..., description="Territorial path governed by order")
    territory_name: str = Field(..., description="Jurisdiction title")
    directive_category: DirectiveCategoryEnum = Field(..., description="Category of order")
    headline: str = Field(..., description="Order headline")
    details: str = Field(..., description="Full operational directives")
    affected_population_estimate: int = Field(..., description="Citizen population impact estimate")
    is_active: bool = Field(..., description="Whether directive is currently in effect")
    issued_at: datetime = Field(..., description="UTC issuance timestamp")
    valid_until: datetime = Field(..., description="Expiration timestamp")

    model_config = ConfigDict(from_attributes=True)


class CommandCenterOverviewResponse(BaseModel):
    """Executive consolidated public health telemetry overview for a sovereign territory."""

    jurisdiction_path: str = Field(..., description="Queried territorial jurisdiction path")
    territory_name: str = Field(..., description="Queried territory name")
    unit_level: AdminLevelEnum = Field(..., description="LGD tier depth level")
    total_active_cases: int = Field(..., ge=0, description="Cumulative active confirmed cases within territory")
    total_monitored_facilities: int = Field(..., ge=0, description="Number of healthcare institutions reporting")
    total_icu_capacity: int = Field(..., ge=0, description="Aggregate ICU beds across territory")
    occupied_icu_beds: int = Field(..., ge=0, description="Currently occupied ICU beds")
    available_icu_beds: int = Field(..., ge=0, description="Available staffed ICU beds")
    regional_icu_occupancy_pct: float = Field(..., ge=0.0, le=100.0, description="Weighted average ICU occupancy rate")
    available_ventilators: int = Field(..., ge=0, description="Total free mechanical ventilators")
    active_outbreak_clusters: int = Field(..., ge=0, description="Active disease clusters in territory")
    critical_alert_count: int = Field(..., ge=0, description="Facilities or clusters in CRITICAL/OUTBREAK status")
    active_directives_count: int = Field(..., ge=0, description="Active public health directives currently in effect")
    surveillance_sla_passed: bool = Field(default=True, description="Whether sub-2ms query SLA was achieved")
    telemetry_timestamp: datetime = Field(..., description="UTC timestamp of telemetry consolidation")

    model_config = ConfigDict(from_attributes=True)
