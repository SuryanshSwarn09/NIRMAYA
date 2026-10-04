"""Schemas package exporting common envelopes, domain models, and health schemas."""

from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    PaginationMeta,
    PaginatedResponse,
)
from app.schemas.doctor import (
    DoctorProfileBase,
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)
from app.schemas.health import (
    DatabaseHealth,
    StandardsCompliance,
    SystemHealthResponse,
)
from app.schemas.lab import (
    DiagnosticLabFacilityBase,
    DiagnosticLabFacilityCreate,
    DiagnosticLabFacilityResponse,
    DiagnosticLabFacilityUpdate,
)
from app.schemas.patient import (
    PatientProfileBase,
    PatientProfileCreate,
    PatientProfileResponse,
    PatientProfileUpdate,
)
from app.schemas.auth import (
    AuthContext,
    TokenPayload,
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.appointment import (
    AppointmentBase,
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    DoctorSlotBase,
    DoctorSlotCreate,
    DoctorSlotResponse,
    SlotGenerateRequest,
    SlotGenerateResult,
    SlotHoldRequest,
    SlotHoldResponse,
    SlotReleaseResponse,
)
from app.schemas.condition import (
    ConditionBase,
    ConditionCreate,
    ConditionFilter,
    ConditionResponse,
    ConditionUpdate,
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
    "DoctorProfileBase",
    "DoctorProfileCreate",
    "DoctorProfileUpdate",
    "DoctorProfileResponse",
    "DiagnosticLabFacilityBase",
    "DiagnosticLabFacilityCreate",
    "DiagnosticLabFacilityUpdate",
    "DiagnosticLabFacilityResponse",
    "AuthContext",
    "TokenPayload",
    "TokenResponse",
    "TokenVerifyRequest",
    "TokenVerifyResponse",
    "DoctorSlotBase",
    "DoctorSlotCreate",
    "DoctorSlotResponse",
    "SlotGenerateRequest",
    "SlotGenerateResult",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentResponse",
    "AppointmentStatusUpdate",
    "SlotHoldRequest",
    "SlotHoldResponse",
    "SlotReleaseResponse",
    "ConditionBase",
    "ConditionCreate",
    "ConditionUpdate",
    "ConditionResponse",
    "ConditionFilter",
]


