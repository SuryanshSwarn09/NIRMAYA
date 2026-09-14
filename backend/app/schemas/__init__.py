"""Schemas package exporting common envelopes, domain models, and health schemas."""

from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    PaginationMeta,
    PaginatedResponse,
)
from app.schemas.health import (
    DatabaseHealth,
    StandardsCompliance,
    SystemHealthResponse,
)
from app.schemas.patient import (
    PatientProfileBase,
    PatientProfileCreate,
    PatientProfileResponse,
    PatientProfileUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "APIResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "StandardsCompliance",
    "DatabaseHealth",
    "SystemHealthResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PatientProfileBase",
    "PatientProfileCreate",
    "PatientProfileUpdate",
    "PatientProfileResponse",
]
