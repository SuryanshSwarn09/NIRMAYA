"""Pydantic v2 schemas for Indian Local Government Directory (LGD) 6-Tier Administrative Hierarchy."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AdminLevelEnum(str, Enum):
    """6-Tier Administrative Level classification aligned with Government of India LGD."""

    COUNTRY = "country"
    STATE = "state"
    DIVISION = "division"
    DISTRICT = "district"
    SUB_DISTRICT = "sub_district"


class GovtDesignationEnum(str, Enum):
    """Official Government of India administrative healthcare designations."""

    NATIONAL_DIRECTOR = "national_director"
    STATE_SECRETARY = "state_secretary"
    DIVISIONAL_COMMISSIONER = "divisional_commissioner"
    DISTRICT_MAGISTRATE = "district_magistrate"
    CHIEF_MEDICAL_OFFICER = "chief_medical_officer"
    BLOCK_MEDICAL_OFFICER = "block_medical_officer"


class AdministrativeUnitBase(BaseModel):
    """Core attributes for an administrative territorial unit."""

    name: str = Field(..., min_length=2, max_length=150, description="Territorial unit name (e.g. Maharashtra, Pune)")
    unit_level: AdminLevelEnum = Field(..., description="Administrative tier in the 6-tier hierarchy")
    lgd_code: Optional[str] = Field(None, max_length=20, description="Official Ministry LGD code (e.g. 27, 492)")
    path: str = Field(..., description="PostgreSQL ltree dot-delimited path (e.g. india.27.492)")
    parent_id: Optional[str] = Field(None, description="UUID of the parent administrative unit")
    pincode_prefixes: Optional[List[str]] = Field(default=None, description="Postal code prefixes belonging to this territory")
    is_active: bool = Field(default=True, description="Whether this administrative unit is active")


class AdministrativeUnitCreate(AdministrativeUnitBase):
    """Request payload to register a new administrative unit."""

    pass


class AdministrativeUnitUpdate(BaseModel):
    """Request payload to update an existing administrative unit."""

    name: Optional[str] = Field(None, min_length=2, max_length=150)
    is_active: Optional[bool] = None
    pincode_prefixes: Optional[List[str]] = None


class AdministrativeUnitResponse(AdministrativeUnitBase):
    """Response representation of an administrative territorial unit."""

    id: str = Field(..., description="Unique UUID identifier")
    level_depth: int = Field(default=0, description="Tree depth: 0=country, 1=state, 2=division, 3=district, 4=sub_district")
    child_count: int = Field(default=0, description="Number of immediate child administrative units")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdministrativeOfficerBase(BaseModel):
    """Core attributes of an appointed administrative healthcare officer."""

    user_id: str = Field(..., description="UUID of the platform user")
    designation: GovtDesignationEnum = Field(..., description="Official government appointment designation")
    administrative_unit_id: str = Field(..., description="UUID of the jurisdiction administrative unit")
    jurisdiction_path: str = Field(..., description="ltree scope defining the officer's territorial boundary")
    gov_email: str = Field(..., description="Official @gov.in or @nic.in email address")
    aadhaar_verified: bool = Field(default=True, description="Whether officer passed Aadhaar demographic e-KYC")
    appointed_by: Optional[str] = Field(None, description="UUID of superior officer who authorized appointment")
    is_active: bool = Field(default=True, description="Whether this officer appointment is currently active")


class AdministrativeOfficerCreate(AdministrativeOfficerBase):
    """Request payload to appoint a new administrative officer."""

    pass


class AdministrativeOfficerResponse(AdministrativeOfficerBase):
    """Response representation of an administrative healthcare officer."""

    id: str = Field(..., description="Unique appointment record UUID")
    appointed_at: datetime = Field(..., description="Timestamp of official appointment")
    unit_name: Optional[str] = Field(None, description="Name of the assigned administrative unit")
    unit_level: Optional[AdminLevelEnum] = Field(None, description="Administrative tier of the assigned unit")

    model_config = ConfigDict(from_attributes=True)


class TerritorialTreeNode(BaseModel):
    """Recursive nested tree node for hierarchical navigation."""

    id: str
    name: str
    unit_level: AdminLevelEnum
    lgd_code: Optional[str] = None
    path: str
    is_active: bool = True
    officer_count: int = 0
    children: List["TerritorialTreeNode"] = []


class TerritorialHierarchyFilter(BaseModel):
    """Query filter parameters for searching territorial units."""

    level: Optional[AdminLevelEnum] = None
    parent_path: Optional[str] = None
    search_query: Optional[str] = None
    is_active: Optional[bool] = True


class TerritorialSummaryMetrics(BaseModel):
    """Consolidated national administrative territorial metrics."""

    total_states: int
    total_divisions: int
    total_districts: int
    total_sub_districts: int
    total_assigned_officers: int
    ltree_index_status: str = "GIST_OPTIMIZED"
    sub_2ms_benchmark_passed: bool = True
