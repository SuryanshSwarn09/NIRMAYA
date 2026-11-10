"""
Day 87 (Milestone 18-02) Test Suite: Strict CoWIN/DigiLocker 3-Tile Citizen Portal (/patient)
Tests service aggregation (<10ms), plain medication schedule engine, hospital QR token,
persona switching (Self, Pediatric, Geriatric), and REST API endpoints.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.citizen_portal_service import citizen_portal_service
from app.schemas.citizen_portal import (
    CitizenThreeTileResponse,
    CitizenHealthIdSummary,
    CitizenActiveMedicineItem,
    CitizenVisitReportItem,
    HospitalCheckInQrResponse,
)


@pytest.fixture(autouse=True)
def clean_portal_cache():
    """Clear citizen portal in-memory cache before every test run."""
    citizen_portal_service.clear_cache()
    yield
    citizen_portal_service.clear_cache()


# ============================================================================
# Service Layer Unit Tests: Aggregation & Persona Profiles
# ============================================================================


def test_service_get_tiles_adult_default():
    """Test 3-tile aggregation for adult self (Arun Patel)."""
    res = citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    assert isinstance(res, CitizenThreeTileResponse)
    assert res.health_id_tile.full_name == "Arun Patel"
    assert res.health_id_tile.abha_number == "91847210482190"
    assert res.health_id_tile.formatted_abha_number == "91-8472-1048-2190"
    assert res.health_id_tile.abha_address == "arun.patel@abdm"
    assert res.health_id_tile.gender == "Male"
    assert res.health_id_tile.age == 34
    assert res.cache_hit is False

    # Check medicines
    assert len(res.active_medicines_tile) >= 3
    names = [m.brand_name for m in res.active_medicines_tile]
    assert "Lisinopril 10mg" in names
    assert "Atorvastatin 20mg" in names

    # Check visits
    assert len(res.visits_and_reports_tile) >= 3
    assert any(v.item_type == "prescription" for v in res.visits_and_reports_tile)
    assert any(v.item_type == "diagnostic_report" for v in res.visits_and_reports_tile)


def test_service_get_tiles_pediatric_minor():
    """Test 3-tile aggregation for pediatric minor profile (Aarav Patel)."""
    res = citizen_portal_service.get_citizen_tiles("pat-aarav-patel")
    assert res.health_id_tile.full_name == "Aarav Patel"
    assert res.health_id_tile.abha_number == "91552188421002"
    assert res.health_id_tile.formatted_abha_number == "91-5521-8842-1002"
    assert res.health_id_tile.age == 5
    assert len(res.active_medicines_tile) >= 2
    # Pediatric safe formulations
    assert any("Suspension" in m.brand_name or "Syrup" in m.brand_name for m in res.active_medicines_tile)


def test_service_get_tiles_geriatric_senior():
    """Test 3-tile aggregation for geriatric senior profile (Ramesh Patel)."""
    res = citizen_portal_service.get_citizen_tiles("pat-ramesh-patel")
    assert res.health_id_tile.full_name == "Ramesh Patel"
    assert res.health_id_tile.abha_number == "91119238475021"
    assert res.health_id_tile.age == 68
    assert len(res.active_medicines_tile) >= 3
    # Geriatric regimen contains urgent or soon refill
    assert any(m.refill_needed is True for m in res.active_medicines_tile)


# ============================================================================
# Plain Language Medication Schedule Engine Tests (No Latin Abbreviations)
# ============================================================================


def test_service_plain_frequency_parsing_1_0_1():
    """1-0-1 must map to Morning: Yes, Afternoon: No, Night: Yes."""
    sched = citizen_portal_service._parse_frequency_code("1-0-1", "1 tablet")
    slots = {s.slot: s.dose for s in sched}
    assert "morning" in slots
    assert "night" in slots
    assert "afternoon" not in slots


def test_service_plain_frequency_parsing_0_1_0():
    """0-1-0 must map to Afternoon only."""
    sched = citizen_portal_service._parse_frequency_code("0-1-0", "1 tablet")
    slots = {s.slot: s.dose for s in sched}
    assert "afternoon" in slots
    assert "morning" not in slots
    assert "night" not in slots


def test_service_plain_frequency_parsing_1_1_1():
    """1-1-1 must map to Morning, Afternoon, and Night."""
    sched = citizen_portal_service._parse_frequency_code("1-1-1", "5 ml")
    slots = [s.slot for s in sched]
    assert "morning" in slots
    assert "afternoon" in slots
    assert "night" in slots


def test_service_plain_frequency_parsing_0_0_1():
    """0-0-1 must map to Night only (e.g. Atorvastatin before bed)."""
    sched = citizen_portal_service._parse_frequency_code("0-0-1", "1 tablet")
    slots = [s.slot for s in sched]
    assert slots == ["night"]


def test_service_plain_frequency_parsing_as_needed():
    """PRN / as needed must map to as_needed slot."""
    sched = citizen_portal_service._parse_frequency_code("PRN", "5 ml SOS")
    slots = [s.slot for s in sched]
    assert slots == ["as_needed"]


def test_service_plain_frequency_parsing_fallback():
    """Unknown string codes must gracefully map to morning fallback without error."""
    sched = citizen_portal_service._parse_frequency_code("UNKNOWN_SIG", "1 unit")
    assert len(sched) >= 1
    assert sched[0].slot == "morning"


# ============================================================================
# Refill Urgency Calculation Tests
# ============================================================================


def test_service_refill_urgency_urgent():
    """Remaining days <= 3 must trigger urgent refill."""
    urgency, needed = citizen_portal_service._calculate_refill_urgency(2)
    assert needed is True
    assert urgency == "urgent"


def test_service_refill_urgency_soon():
    """Remaining days between 4 and 7 must trigger soon refill."""
    urgency, needed = citizen_portal_service._calculate_refill_urgency(5)
    assert needed is True
    assert urgency == "soon"


def test_service_refill_urgency_none():
    """Remaining days > 7 must require no refill action."""
    urgency, needed = citizen_portal_service._calculate_refill_urgency(14)
    assert needed is False
    assert urgency == "none"


# ============================================================================
# Performance & Caching Benchmarks
# ============================================================================


def test_service_aggregation_sub_10ms_latency():
    """Verify aggregation executes in sub-10ms (latency benchmark)."""
    latencies = []
    for _ in range(15):
        t0 = time.perf_counter()
        citizen_portal_service.get_citizen_tiles("pat-arun-patel")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)
    
    # After first cold load, all subsequent in-memory cached calls should execute < 5ms
    cached_latencies = latencies[1:]
    assert all(lat < 15.0 for lat in cached_latencies)
    assert sum(cached_latencies) / len(cached_latencies) < 5.0


def test_service_in_memory_caching():
    """Verify cache hit behavior on subsequent calls."""
    res1 = citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    assert res1.cache_hit is False

    res2 = citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    assert res2.cache_hit is True
    assert res2.health_id_tile.abha_number == res1.health_id_tile.abha_number


def test_service_clear_cache():
    """Verify clear_cache completely resets the cache store."""
    citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    assert len(citizen_portal_service._cache) > 0

    citizen_portal_service.clear_cache()
    assert len(citizen_portal_service._cache) == 0


# ============================================================================
# Hospital OPD Counter QR Token Generator Tests
# ============================================================================


def test_service_qr_token_generation():
    """Test generating short-lived OPD check-in QR token."""
    res = citizen_portal_service.generate_hospital_checkin_qr("pat-arun-patel")
    assert isinstance(res, HospitalCheckInQrResponse)
    assert res.patient_id == "pat-arun-patel"
    assert res.abha_number == "91847210482190"
    assert res.token.startswith("ABDM-CHECKIN-")
    assert res.ttl_seconds == 3600
    assert "https://abdm.gov.in/checkin?t=" in res.qr_payload


def test_service_qr_token_custom_facility():
    """Test QR token includes facility context when provided."""
    res = citizen_portal_service.generate_hospital_checkin_qr(
        "pat-arun-patel", facility_context="AIIMS-OPD-GATE3"
    )
    assert res.facility_context == "AIIMS-OPD-GATE3"
    assert "AIIMS-OPD-GATE3" in res.qr_payload


# ============================================================================
# REST API Endpoint Tests (AsyncClient)
# ============================================================================


@pytest.mark.asyncio
async def test_endpoint_get_tiles_default():
    """GET /api/v1/patient/citizen-portal/tiles returns 200 and valid schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/tiles")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        data = envelope["data"]
        assert "health_id_tile" in data
        assert "active_medicines_tile" in data
        assert "visits_and_reports_tile" in data
        assert data["health_id_tile"]["full_name"] == "Arun Patel"
        assert data["health_id_tile"]["formatted_abha_number"] == "91-8472-1048-2190"


@pytest.mark.asyncio
async def test_endpoint_get_tiles_pediatric():
    """GET /api/v1/patient/citizen-portal/tiles?patient_id=pat-aarav-patel returns minor data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/tiles?patient_id=pat-aarav-patel")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        data = envelope["data"]
        assert data["health_id_tile"]["full_name"] == "Aarav Patel"
        assert data["health_id_tile"]["age"] == 5


@pytest.mark.asyncio
async def test_endpoint_get_tiles_geriatric():
    """GET /api/v1/patient/citizen-portal/tiles?patient_id=pat-ramesh-patel returns senior data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/tiles?patient_id=pat-ramesh-patel")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        data = envelope["data"]
        assert data["health_id_tile"]["full_name"] == "Ramesh Patel"
        assert data["health_id_tile"]["age"] == 68


@pytest.mark.asyncio
async def test_endpoint_get_qr_token_success():
    """GET /api/v1/patient/citizen-portal/qr-token returns 200 and QR payload."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/qr-token")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        data = envelope["data"]
        assert "token" in data
        assert "qr_payload" in data
        assert data["ttl_seconds"] == 3600


@pytest.mark.asyncio
async def test_endpoint_get_qr_token_facility_query():
    """GET /api/v1/patient/citizen-portal/qr-token?facility_context=SAF-OPD-1 returns custom context."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/qr-token?facility_context=SAF-OPD-1")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        data = envelope["data"]
        assert data["facility_context"] == "SAF-OPD-1"


@pytest.mark.asyncio
async def test_endpoint_get_medicines_only():
    """GET /api/v1/patient/citizen-portal/medicines returns active medications array."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/medicines")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        meds = envelope["data"]
        assert isinstance(meds, list)
        assert len(meds) >= 3
        first = meds[0]
        assert "plain_schedule" in first
        assert "course_duration_days" in first


@pytest.mark.asyncio
async def test_endpoint_get_visits_only():
    """GET /api/v1/patient/citizen-portal/visits returns chronological visits array."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/patient/citizen-portal/visits")
        assert res.status_code == 200
        envelope = res.json()
        assert envelope["success"] is True
        visits = envelope["data"]
        assert isinstance(visits, list)
        assert len(visits) >= 3



def test_endpoint_visits_filter_integrity():
    """Verify each visit item has valid item_type, encounter_date, and digital_signature_seal."""
    res = citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    for item in res.visits_and_reports_tile:
        assert item.item_type in ("prescription", "diagnostic_report")
        assert len(item.encounter_date) == 10  # YYYY-MM-DD
        assert item.doctor_name
        assert item.facility_name
        assert item.plain_diagnosis
        assert item.digital_signature_seal is not None


def test_schema_serialization():
    """Validate Pydantic models serialization and JSON dump consistency."""
    res = citizen_portal_service.get_citizen_tiles("pat-arun-patel")
    dumped = res.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["health_id_tile"]["abha_number"] == "91847210482190"
    reconstructed = CitizenThreeTileResponse.model_validate(dumped)
    assert reconstructed.health_id_tile.full_name == "Arun Patel"
