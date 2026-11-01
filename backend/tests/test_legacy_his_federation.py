"""Unit and integration test suite for PostgreSQL Foreign Data Wrapper (postgres_fdw)

and Legacy Hospital Information System (HIS) Read-Only Federation Engine.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.legacy_his import (
    ConnectionStatusEnum,
    FederationQueryRequest,
    FhirResourceTypeEnum,
    LegacyConnectionConfig,
    LegacyPatientRecord,
    LegacySystemType,
)
from app.services.legacy_his_service import (
    LegacyHisFederationService,
    LegacyHisSecurityException,
    legacy_his_service,
)


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def fresh_service() -> LegacyHisFederationService:
    """Fixture providing an isolated federation service instance."""
    return LegacyHisFederationService()


def test_legacy_system_types_and_schemas():
    """Verify enum types and configuration schemas."""
    assert LegacySystemType.POSTGRES_FDW == "POSTGRES_FDW"
    assert LegacySystemType.MYSQL_LEGACY == "MYSQL_LEGACY"
    assert LegacySystemType.SQLITE_LEGACY == "SQLITE_LEGACY"

    config = LegacyConnectionConfig(
        server_id="test-pg-server",
        display_name="Test PG Server",
        system_type=LegacySystemType.POSTGRES_FDW,
        host="localhost",
        port=5432,
        database_name="test_his",
        username="readonly_user",
    )
    assert config.read_only_enforced is True
    assert config.schema_prefix == "foreign_his"
    assert config.pool_size == 5


def test_server_registration_and_health_check(fresh_service: LegacyHisFederationService):
    """Verify listing servers, registering a new server, and inspecting health."""
    servers = fresh_service.list_servers()
    assert len(servers) >= 4

    new_server = LegacyConnectionConfig(
        server_id="his-kolkata-sskm-05",
        display_name="SSKM Hospital Kolkata",
        system_type=LegacySystemType.POSTGRES_FDW,
        host="10.0.7.12",
        port=5432,
        database_name="sskm_legacy_db",
        username="ro_sync",
    )
    registered = fresh_service.register_server(new_server)
    assert registered.server_id == "his-kolkata-sskm-05"

    health = fresh_service.check_server_health("his-kolkata-sskm-05")
    assert health.status == ConnectionStatusEnum.READ_ONLY_VERIFIED
    assert health.read_only_verified is True
    assert health.latency_ms > 0.0
    assert health.table_count == 4


def test_read_only_enforcement_blocks_mutations(fresh_service: LegacyHisFederationService):
    """Verify that all mutating SQL operations are strictly blocked by AST inspection."""
    mutating_queries = [
        "INSERT INTO foreign_his.legacy_patients (pt_id) VALUES ('123')",
        "UPDATE foreign_his.legacy_patients SET full_name = 'Hacked' WHERE pt_id = '1'",
        "DELETE FROM foreign_his.legacy_encounters WHERE enc_no = 'ENC-001'",
        "DROP TABLE foreign_his.legacy_observations",
        "ALTER TABLE foreign_his.legacy_patients ADD COLUMN malicious TEXT",
        "TRUNCATE TABLE foreign_his.legacy_prescriptions",
        "EXEC xp_cmdshell('whoami')",
        "GRANT ALL PRIVILEGES ON DATABASE test TO public",
    ]

    for q in mutating_queries:
        with pytest.raises(LegacyHisSecurityException) as exc_info:
            fresh_service.validate_read_only_query(q)
        assert "Security Violation" in str(exc_info.value)

    # Verify benign SELECT query passes without exception
    fresh_service.validate_read_only_query(
        "SELECT pt_id, mrn_no, full_name FROM foreign_his.legacy_patients WHERE mrn_no = 'MRN-DEL-2023-8821'"
    )


def test_sql_med_ddl_generation(fresh_service: LegacyHisFederationService):
    """Verify standard ISO/IEC 9075-9 SQL/MED DDL generation for PostgreSQL 16."""
    ddl_resp = fresh_service.generate_sql_med_ddl("his-delhi-civil-01")
    assert ddl_resp.server_id == "his-delhi-civil-01"
    assert "CREATE EXTENSION IF NOT EXISTS postgres_fdw;" in ddl_resp.ddl_script
    assert "CREATE SERVER IF NOT EXISTS" in ddl_resp.ddl_script
    assert "FOREIGN DATA WRAPPER postgres_fdw" in ddl_resp.ddl_script
    assert "CREATE USER MAPPING IF NOT EXISTS" in ddl_resp.ddl_script
    assert "CREATE FOREIGN TABLE IF NOT EXISTS" in ddl_resp.ddl_script
    assert len(ddl_resp.foreign_tables) == 4
    assert any("legacy_patients" in t for t in ddl_resp.foreign_tables)


def test_federated_patient_search_by_mrn(fresh_service: LegacyHisFederationService):
    """Verify finding patient by exact and partial MRN."""
    req = FederationQueryRequest(mrn="MRN-DEL-2023-8821")
    resp = fresh_service.search_patients(req)
    assert resp.total_matches == 1
    assert resp.patients[0].mrn_no == "MRN-DEL-2023-8821"
    assert resp.patients[0].demographics.full_name == "Ramesh Sharma"


def test_federated_patient_search_by_name_and_city(fresh_service: LegacyHisFederationService):
    """Verify searching patient by name substring or city."""
    req_name = FederationQueryRequest(search_query="Sunita")
    resp_name = fresh_service.search_patients(req_name)
    assert resp_name.total_matches == 1
    assert resp_name.patients[0].demographics.full_name == "Sunita Patel"

    req_city = FederationQueryRequest(search_query="Bengaluru")
    resp_city = fresh_service.search_patients(req_city)
    assert resp_city.total_matches == 1
    assert resp_city.patients[0].demographics.full_name == "Arun Krishnan"


def test_federated_patient_timeline_retrieval(fresh_service: LegacyHisFederationService):
    """Verify retrieving complete clinical timeline across encounters, labs, and medications."""
    view = fresh_service.get_patient_timeline("LEGACY-PT-1001")
    assert view is not None
    assert view.patient_id == "LEGACY-PT-1001"
    assert view.total_encounters == 2
    assert view.total_observations == 4
    assert view.total_prescriptions == 3
    assert len(view.timeline) == 9

    # Verify chronological order (newest first)
    dates = [item.date for item in view.timeline]
    assert dates == sorted(dates, reverse=True)


def test_legacy_to_fhir_patient_normalization(fresh_service: LegacyHisFederationService):
    """Verify bijective mapping of legacy patient record into HL7 FHIR R4 Patient."""
    pt = fresh_service._patients_db["LEGACY-PT-1001"]
    fhir_pt = fresh_service.normalize_patient_to_fhir(pt)

    assert fhir_pt["resourceType"] == "Patient"
    assert fhir_pt["id"] == "fed-his-delhi-civil-01-legacy-pt-1001"
    assert fhir_pt["name"][0]["text"] == "Ramesh Sharma"
    assert fhir_pt["gender"] == "male"
    assert fhir_pt["birthDate"] == "1968-04-12"
    assert any(i["value"] == "MRN-DEL-2023-8821" for i in fhir_pt["identifier"])
    assert any(i["value"] == "91-1234-5678-9012" for i in fhir_pt["identifier"])


def test_legacy_to_fhir_observation_loinc_mapping(fresh_service: LegacyHisFederationService):
    """Verify mapping of legacy lab tests to standardized LOINC codes."""
    pt_fhir_id = "fed-his-delhi-civil-01-legacy-pt-1001"

    # Fasting glucose -> LOINC 1558-6
    obs_glucose = next(o for o in fresh_service._observations_db if o.test_code == "GLUCOSE")
    fhir_glucose = fresh_service.normalize_observation_to_fhir(obs_glucose, pt_fhir_id)
    assert fhir_glucose["resourceType"] == "Observation"
    assert fhir_glucose["code"]["coding"][0]["code"] == "1558-6"
    assert fhir_glucose["valueQuantity"]["value"] == 184.0

    # HbA1c -> LOINC 4548-4
    obs_hba1c = next(o for o in fresh_service._observations_db if o.test_code == "HBA1C")
    fhir_hba1c = fresh_service.normalize_observation_to_fhir(obs_hba1c, pt_fhir_id)
    assert fhir_hba1c["code"]["coding"][0]["code"] == "4548-4"
    assert fhir_hba1c["valueQuantity"]["value"] == 8.4


def test_legacy_to_fhir_encounter_normalization(fresh_service: LegacyHisFederationService):
    """Verify encounter conversion to HL7 FHIR R4 Encounter."""
    pt_fhir_id = "fed-his-delhi-civil-01-legacy-pt-1001"
    enc = fresh_service._encounters_db[0]
    fhir_enc = fresh_service.normalize_encounter_to_fhir(enc, pt_fhir_id)

    assert fhir_enc["resourceType"] == "Encounter"
    assert fhir_enc["status"] == "finished"
    assert fhir_enc["class"]["code"] == "AMB"
    assert fhir_enc["serviceProvider"]["display"] == "Endocrinology OPD"
    assert "E11.9" in fhir_enc["diagnosis"][0]["condition"]["display"]


def test_legacy_to_fhir_prescription_normalization(fresh_service: LegacyHisFederationService):
    """Verify medication orders normalized to HL7 FHIR R4 MedicationRequest."""
    pt_fhir_id = "fed-his-delhi-civil-01-legacy-pt-1001"
    rx = fresh_service._prescriptions_db[0]
    fhir_rx = fresh_service.normalize_prescription_to_fhir(rx, pt_fhir_id)

    assert fhir_rx["resourceType"] == "MedicationRequest"
    assert fhir_rx["status"] == "active"
    assert fhir_rx["medicationCodeableConcept"]["text"] == "Metformin Hydrochloride"
    assert "500 mg" in fhir_rx["dosageInstruction"][0]["text"]


def test_provenance_hash_integrity(fresh_service: LegacyHisFederationService):
    """Verify deterministic SHA-256 provenance hash on federated clinical items."""
    view = fresh_service.get_patient_timeline("LEGACY-PT-1001")
    assert view is not None
    for entry in view.timeline:
        assert len(entry.provenance_hash) == 64
        # Verify hex string
        int(entry.provenance_hash, 16)


def test_multi_tier_query_cache_hit(fresh_service: LegacyHisFederationService):
    """Verify that secondary queries hit cache with zero database traversal."""
    req = FederationQueryRequest(search_query="Sharma")

    # Initial query: cache miss
    resp1 = fresh_service.search_patients(req)
    assert resp1.cached is False

    # Secondary identical query: cache hit
    resp2 = fresh_service.search_patients(req)
    assert resp2.cached is True
    assert fresh_service._cache_hits >= 1


def test_federation_telemetry_metrics(fresh_service: LegacyHisFederationService):
    """Verify calculation of telemetry counters and health matrix."""
    # Execute some searches
    fresh_service.search_patients(FederationQueryRequest(search_query="Patel"))
    fresh_service.search_patients(FederationQueryRequest(search_query="Patel"))

    telemetry = fresh_service.get_telemetry()
    assert telemetry.configured_servers >= 4
    assert telemetry.active_servers >= 4
    assert telemetry.total_queries_executed >= 2
    assert telemetry.cache_hits >= 1
    assert telemetry.cache_hit_ratio_pct > 0.0
    assert len(telemetry.servers_health) >= 4


def test_api_endpoints_servers_and_test(client: TestClient):
    """Verify GET /api/v1/his/servers and POST /api/v1/his/servers/test."""
    # List servers
    resp = client.get("/api/v1/his/servers")
    assert resp.status_code == 200
    servers = resp.json()
    assert len(servers) >= 4

    # Test server
    test_resp = client.post("/api/v1/his/servers/test", json={"server_id": "his-delhi-civil-01"})
    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["server_id"] == "his-delhi-civil-01"
    assert data["status"] == "READ_ONLY_VERIFIED"
    assert data["read_only_verified"] is True


def test_api_endpoints_patients_timeline_ddl_and_import(client: TestClient):
    """Verify patient search, timeline retrieval, DDL generation, and import API."""
    # 1. Search patients
    search_resp = client.get("/api/v1/his/patients?search=Ramesh")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_matches"] >= 1
    pt_id = search_data["patients"][0]["patient_id"]

    # 2. Get timeline
    timeline_resp = client.get(f"/api/v1/his/patients/{pt_id}/timeline")
    assert timeline_resp.status_code == 200
    t_data = timeline_resp.json()
    assert len(t_data["timeline"]) == 9

    # 3. Generate DDL
    ddl_resp = client.get("/api/v1/his/ddl?server_id=his-delhi-civil-01")
    assert ddl_resp.status_code == 200
    assert "CREATE EXTENSION IF NOT EXISTS postgres_fdw" in ddl_resp.json()["ddl_script"]

    # 4. Import to native vault
    import_resp = client.post("/api/v1/his/import/fhir", json={"patient_id": pt_id})
    assert import_resp.status_code == 200
    imp_data = import_resp.json()
    assert imp_data["imported"] is True
    assert imp_data["fhir_resources_count"] == 10
    assert len(imp_data["provenance_hash"]) == 64

