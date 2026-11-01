from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LegacySystemType(str, Enum):
    """Supported external database engine types for foreign federation."""
    POSTGRES_FDW = "POSTGRES_FDW"
    MYSQL_LEGACY = "MYSQL_LEGACY"
    MSSQL_LEGACY = "MSSQL_LEGACY"
    ORACLE_LEGACY = "ORACLE_LEGACY"
    SQLITE_LEGACY = "SQLITE_LEGACY"
    SIMULATED_HIS = "SIMULATED_HIS"


class ConnectionStatusEnum(str, Enum):
    """Health status of external foreign server connection."""
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNAUTHORIZED = "UNAUTHORIZED"
    READ_ONLY_VERIFIED = "READ_ONLY_VERIFIED"


class FhirResourceTypeEnum(str, Enum):
    """HL7 FHIR R4 resource types produced by normalization pipeline."""
    Patient = "Patient"
    Encounter = "Encounter"
    Observation = "Observation"
    MedicationRequest = "MedicationRequest"
    Condition = "Condition"
    DocumentReference = "DocumentReference"


class LegacyConnectionConfig(BaseModel):
    """Connection parameters for a remote hospital database."""
    server_id: str = Field(..., description="Unique slug identifier for foreign server")
    display_name: str = Field(..., description="Human-readable hospital facility name")
    system_type: LegacySystemType = Field(default=LegacySystemType.POSTGRES_FDW)
    host: str = Field(default="localhost", description="Remote host IP or DNS name")
    port: int = Field(default=5432, description="Database port number")
    database_name: str = Field(..., description="Remote database name")
    username: str = Field(..., description="Read-only sync database user")
    password: Optional[str] = Field(None, description="Password or secret credential token")
    schema_prefix: str = Field(default="foreign_his", description="Isolated target schema")
    read_only_enforced: bool = Field(default=True, description="Enforce read-only transactions")
    connection_timeout_ms: int = Field(default=3000, description="Network timeout budget in ms")
    pool_size: int = Field(default=5, description="Max read-only connection pool size")
    is_active: bool = Field(default=True, description="Whether server is enabled for federation")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ServerHealthCheckResult(BaseModel):
    """Health inspection payload for a foreign database server."""
    server_id: str
    display_name: str
    system_type: LegacySystemType
    status: ConnectionStatusEnum
    latency_ms: float
    read_only_verified: bool
    server_version: Optional[str] = None
    table_count: int = 0
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class LegacyPatientRecord(BaseModel):
    """Raw patient row structure as stored in legacy hospital tables."""
    pt_id: str
    mrn_no: str
    full_name: str
    dob_str: str
    gender_char: str = Field(..., description="'M', 'F', or 'O'")
    cell_phone: Optional[str] = None
    legacy_abha: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    source_server_id: str
    created_at: Optional[datetime] = None


class LegacyEncounterRecord(BaseModel):
    """Raw encounter or visit row in legacy HIS database."""
    enc_no: str
    pt_id: str
    visit_datetime: datetime
    dept_name: str
    attending_dr: str
    chief_complaint: Optional[str] = None
    diagnosis_icd10: Optional[str] = None
    encounter_type: str = "outpatient"
    source_server_id: str


class LegacyObservationRecord(BaseModel):
    """Raw laboratory investigation or diagnostic observation."""
    lab_id: str
    pt_id: str
    enc_no: Optional[str] = None
    test_code: str
    test_name: str
    result_val: str
    unit_str: Optional[str] = None
    ref_range: Optional[str] = None
    interpretation: Optional[str] = None  # normal, high, low, critical
    recorded_at: datetime
    source_server_id: str


class LegacyPrescriptionRecord(BaseModel):
    """Raw medication or pharmacy order from legacy HIS."""
    rx_id: str
    pt_id: str
    enc_no: Optional[str] = None
    drug_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None
    prescribed_at: datetime
    prescribed_by: str
    source_server_id: str


class NormalizedFhirTimelineEntry(BaseModel):
    """Chronological clinical event normalized into HL7 FHIR R4."""
    entry_id: str
    resource_type: FhirResourceTypeEnum
    date: datetime
    title: str
    summary: str
    fhir_resource: Dict[str, Any]
    source_server_id: str
    source_system_type: LegacySystemType
    provenance_hash: str
    is_critical: bool = False


class FederatedPatientView(BaseModel):
    """Aggregated clinical portrait federated from remote hospital databases."""
    patient_id: str
    mrn_no: str
    demographics: LegacyPatientRecord
    fhir_patient: Dict[str, Any]
    total_encounters: int = 0
    total_observations: int = 0
    total_prescriptions: int = 0
    last_encounter_date: Optional[datetime] = None
    source_server_id: str
    timeline: List[NormalizedFhirTimelineEntry] = []
    query_latency_ms: float = 0.0
    cached: bool = False


class FederationQueryRequest(BaseModel):
    """Query parameters for federated patient search."""
    search_query: Optional[str] = None
    mrn: Optional[str] = None
    server_id: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class FederationQueryResponse(BaseModel):
    """Paginated search response across federated legacy hospital systems."""
    total_matches: int
    page: int
    page_size: int
    server_id: Optional[str] = None
    patients: List[FederatedPatientView]
    query_latency_ms: float
    cached: bool = False


class FederationEngineTelemetry(BaseModel):
    """Aggregated performance and security metrics for federation engine."""
    configured_servers: int
    active_servers: int
    total_queries_executed: int
    cache_hits: int
    cache_misses: int
    cache_hit_ratio_pct: float
    avg_query_latency_ms: float
    read_only_violations_prevented: int
    servers_health: List[ServerHealthCheckResult]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SqlMedDdlResponse(BaseModel):
    """Generated ISO/IEC 9075-9 SQL/MED DDL statements for PostgreSQL 16."""
    server_id: str
    ddl_script: str
    schema_name: str
    instructions: str
    foreign_tables: List[str]
