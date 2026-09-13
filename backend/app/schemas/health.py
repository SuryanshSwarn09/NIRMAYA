"""Health check and system telemetry schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class StandardsCompliance(BaseModel):
    """Healthcare data standards compliance indicators."""

    fhir_version: str = Field(default="R4", description="HL7 FHIR specification release")
    abdm_sandbox: bool = Field(default=True, description="Ayushman Bharat Digital Mission connectivity")
    loinc_mapped: bool = Field(default=True, description="Logical Observation Identifiers Names and Codes")
    snomed_ct_ready: bool = Field(default=True, description="SNOMED Clinical Terms clinical ontology readiness")


class DatabaseHealth(BaseModel):
    """Relational database connection and probe telemetry."""

    status: Literal["healthy", "unreachable", "degraded", "not_configured"] = Field(
        default="healthy", description="Database connection probe status"
    )
    driver: str = Field(default="postgresql+asyncpg", description="Underlying DB driver")
    database_type: Optional[str] = Field(default=None, description="Database dialect (e.g. postgresql, sqlite)")
    latency_ms: Optional[float] = Field(default=None, description="Roundtrip query latency in milliseconds")
    error: Optional[str] = Field(default=None, description="Error diagnostics if probe failed")
    pool_size: Optional[int] = Field(default=None, description="Configured connection pool size")


class SystemHealthResponse(BaseModel):
    """Enterprise health verification payload."""

    status: str = Field(default="healthy", description="Overall cluster health state")
    project: str = Field(default="NIRMAYA")
    full_name: str
    version: str
    environment: str
    uptime_seconds: float = Field(ge=0.0)
    timestamp: datetime
    standards: StandardsCompliance
    database: DatabaseHealth
