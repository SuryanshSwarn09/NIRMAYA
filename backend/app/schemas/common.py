"""Standardized API response and error envelopes for NIRMAYA platform."""

from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard success response wrapper."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[DataT] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None


class ErrorDetail(BaseModel):
    """Specific field-level or entity-level error description."""

    location: Optional[str] = Field(default=None, description="Path or parameter of error")
    message: str = Field(description="Description of the validation or clinical issue")
    error_type: Optional[str] = Field(default=None, description="Machine-readable error classification")


class ErrorResponse(BaseModel):
    """Unified error response model for HTTP and business logic failures."""

    success: bool = False
    error_code: str = Field(description="Standardized error code (e.g., VALIDATION_ERROR, NOT_FOUND)")
    message: str = Field(description="Human-readable summary of the error")
    details: List[ErrorDetail] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None


class PaginationMeta(BaseModel):
    """Pagination metadata for clinical listings and record archives."""

    total_count: int = Field(ge=0, description="Total matching records")
    page: int = Field(ge=1, default=1, description="Current 1-indexed page")
    limit: int = Field(ge=1, le=100, default=20, description="Page record ceiling")
    total_pages: int = Field(ge=0, description="Calculated total pages")
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standardized wrapper for paginated collections."""

    success: bool = True
    data: List[DataT] = Field(default_factory=list)
    pagination: PaginationMeta
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
