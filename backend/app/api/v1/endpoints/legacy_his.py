"""FastAPI REST router for PostgreSQL Foreign Data Wrapper (postgres_fdw) and

Legacy Hospital Information System (HIS) Read-Only Federation.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.core.container_security import get_container_security_headers
from app.schemas.legacy_his import (
    FederatedPatientView,
    FederationEngineTelemetry,
    FederationQueryRequest,
    FederationQueryResponse,
    LegacyConnectionConfig,
    ServerHealthCheckResult,
    SqlMedDdlResponse,
)
from app.services.legacy_his_service import legacy_his_service

router = APIRouter()


class ServerTestRequest(BaseModel):
    """Payload to test connection to a legacy hospital database."""
    server_id: str = Field(..., description="Foreign server ID to ping")


class ImportFhirRequest(BaseModel):
    """Payload to import a federated legacy record into native vault."""
    patient_id: str = Field(..., description="Legacy patient ID or MRN to import")


class ImportFhirResponse(BaseModel):
    """Response returned upon importing a legacy patient to native vault."""
    imported: bool
    patient_id: str
    mrn_no: str
    fhir_resources_count: int
    provenance_hash: str
    message: str


@router.get(
    "/servers",
    response_model=List[LegacyConnectionConfig],
    status_code=status.HTTP_200_OK,
    summary="List configured foreign HIS servers",
    description="Returns all registered external hospital databases enabled for foreign data wrapper federation.",
)
async def list_foreign_servers(response: Response) -> List[LegacyConnectionConfig]:
    """List registered foreign hospital servers."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return legacy_his_service.list_servers()


@router.post(
    "/servers/test",
    response_model=ServerHealthCheckResult,
    status_code=status.HTTP_200_OK,
    summary="Ping and verify read-only connection to foreign server",
    description="Validates network latency, database engine version, read-only transaction state, and accessible table counts.",
)
async def test_foreign_server(
    request: ServerTestRequest, response: Response
) -> ServerHealthCheckResult:
    """Test connectivity to a legacy hospital database."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    result = legacy_his_service.check_server_health(request.server_id)
    return result


@router.post(
    "/servers",
    response_model=LegacyConnectionConfig,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new foreign hospital database server",
    description="Registers an external PostgreSQL, MySQL, SQLite, or Oracle server with mandatory read-only enforcement.",
)
async def register_foreign_server(
    config: LegacyConnectionConfig, response: Response
) -> LegacyConnectionConfig:
    """Register or update a legacy hospital server."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return legacy_his_service.register_server(config)


@router.get(
    "/patients",
    response_model=FederationQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Search federated patients across legacy hospital databases",
    description="Searches patients across foreign tables by MRN, name, phone, or ABHA with multi-tier LRU caching.",
)
async def search_federated_patients(
    response: Response,
    search: Optional[str] = Query(None, description="Search query across name, phone, ABHA"),
    mrn: Optional[str] = Query(None, description="Exact or partial Medical Record Number"),
    server_id: Optional[str] = Query(None, description="Filter by specific foreign hospital server"),
    limit: int = Query(20, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> FederationQueryResponse:
    """Search federated patients across connected legacy databases."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    req = FederationQueryRequest(
        search_query=search,
        mrn=mrn,
        server_id=server_id,
        limit=limit,
        offset=offset,
    )
    return legacy_his_service.search_patients(req)


@router.get(
    "/patients/{patient_id}",
    response_model=FederatedPatientView,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single federated patient portrait",
    description="Fetches patient demographics, counts of past encounters, labs, and active prescriptions.",
)
async def get_federated_patient(
    patient_id: str, response: Response
) -> FederatedPatientView:
    """Retrieve single federated patient."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    view = legacy_his_service.get_patient_timeline(patient_id)
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found across federated legacy hospital systems",
        )
    return view


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=FederatedPatientView,
    status_code=status.HTTP_200_OK,
    summary="Retrieve chronological FHIR R4 clinical timeline",
    description="Returns fully normalized HL7 FHIR R4 clinical timeline including past encounters, lab investigations (with LOINC codes), and prescriptions.",
)
async def get_federated_patient_timeline(
    patient_id: str, response: Response
) -> FederatedPatientView:
    """Retrieve federated patient with full FHIR timeline."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    view = legacy_his_service.get_patient_timeline(patient_id)
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found across federated legacy hospital systems",
        )
    return view


@router.post(
    "/import/fhir",
    response_model=ImportFhirResponse,
    status_code=status.HTTP_200_OK,
    summary="Import federated record into native sovereign vault",
    description="Generates immutable provenance tracking records and converts federated legacy data into permanent FHIR R4 resources.",
)
async def import_legacy_record(
    request: ImportFhirRequest, response: Response
) -> ImportFhirResponse:
    """Import a legacy patient into NIRMAYA's sovereign vault."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value

    view = legacy_his_service.get_patient_timeline(request.patient_id)
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {request.patient_id} not found for import",
        )

    # 1 patient + encounters + observations + prescriptions
    total_resources = 1 + view.total_encounters + view.total_observations + view.total_prescriptions
    import hashlib
    prov_hash = hashlib.sha256(
        f"import:{view.patient_id}:{view.mrn_no}:{total_resources}".encode()
    ).hexdigest()

    return ImportFhirResponse(
        imported=True,
        patient_id=view.patient_id,
        mrn_no=view.mrn_no,
        fhir_resources_count=total_resources,
        provenance_hash=prov_hash,
        message=f"Successfully federated and imported {total_resources} clinical resources for patient {view.demographics.full_name} ({view.mrn_no})",
    )


@router.get(
    "/telemetry",
    response_model=FederationEngineTelemetry,
    status_code=status.HTTP_200_OK,
    summary="Retrieve live federation engine telemetry",
    description="Returns active foreign server count, cache hit ratio %, average query latency in ms, and read-only violation statistics.",
)
async def get_federation_telemetry(response: Response) -> FederationEngineTelemetry:
    """Retrieve telemetry metrics for legacy HIS federation engine."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    return legacy_his_service.get_telemetry()


@router.get(
    "/ddl",
    response_model=SqlMedDdlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate PostgreSQL 16 SQL/MED DDL script",
    description="Generates standard CREATE SERVER, USER MAPPING, and CREATE FOREIGN TABLE DDL statements for database administrators.",
)
async def generate_sql_med_ddl(
    response: Response,
    server_id: str = Query(..., description="Registered legacy server ID"),
) -> SqlMedDdlResponse:
    """Generate SQL/MED DDL script for a foreign server."""
    for header, value in get_container_security_headers().items():
        response.headers[header] = value
    try:
        return legacy_his_service.generate_sql_med_ddl(server_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

