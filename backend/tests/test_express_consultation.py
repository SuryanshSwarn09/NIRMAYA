"""Day 88 (Milestone 18-03) Test Suite: Express 45-Second Doctor Consultation Mode (/doctor).

Validates:
- Curated 1-click chief complaint chips (ICD-10, SNOMED CT)
- Pre-configured prescription bundles with plain time-of-day intake schedules
- High-visibility allergy safety shield (Penicillin & Sulfa contraindication blocks)
- Sub-50ms atomic encounter completion, cryptographic HPR seal, and live queue advance
- REST API endpoints via AsyncClient
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.express_consultation_service import express_consultation_service
from app.schemas.express_consultation import (
    ExpressEncounterSubmitRequest,
    ExpressEncounterSubmitResponse,
    QuickPrescriptionItem,
    PatientAllergyProfile,
)


@pytest.fixture(autouse=True)
def clean_express_state():
    """Reset express consultation service state between tests."""
    express_consultation_service.reset_state()
    yield
    express_consultation_service.reset_state()


# ============================================================================
# Service Layer Unit Tests: Catalog & Templates
# ============================================================================


def test_service_get_chief_complaints_count():
    """Verify all 7 curated clinical chief complaint templates are present."""
    complaints = express_consultation_service.get_chief_complaints()
    assert len(complaints) >= 7
    codes = [c.code for c in complaints]
    assert "FEVER" in codes
    assert "GASTRITIS" in codes
    assert "HTN_REV" in codes
    assert "DM_REV" in codes
    assert "ALLERGY_RHIN" in codes
    assert "BACK_PAIN" in codes
    assert "PED_FEVER" in codes


def test_service_get_chief_complaints_by_category():
    """Verify category filtering for complaint chips."""
    cardio = express_consultation_service.get_chief_complaints(category="cardio")
    assert len(cardio) >= 1
    assert all(c.category == "cardio" for c in cardio)

    pediatrics = express_consultation_service.get_chief_complaints(category="pediatrics")
    assert len(pediatrics) >= 1
    assert pediatrics[0].code == "PED_FEVER"


def test_service_get_prescription_bundles_count():
    """Verify standard Ayushman Bharat prescription bundles are seeded."""
    bundles = express_consultation_service.get_prescription_bundles()
    assert len(bundles) >= 7
    ids = [b.bundle_id for b in bundles]
    assert "BUNDLE-VIRAL-URTI" in ids
    assert "BUNDLE-GASTRITIS" in ids
    assert "BUNDLE-HTN" in ids
    assert "BUNDLE-DM" in ids
    assert "BUNDLE-PED-FEVER" in ids


def test_service_get_prescription_bundles_by_category():
    """Verify filtering bundles by medical specialty."""
    gastrology = express_consultation_service.get_prescription_bundles(category="gastrology")
    assert len(gastrology) >= 1
    assert gastrology[0].bundle_id == "BUNDLE-GASTRITIS"


def test_service_get_bundle_by_id_found():
    """Verify lookup of existing bundle returns correct medications."""
    bundle = express_consultation_service.get_bundle_by_id("BUNDLE-VIRAL-URTI")
    assert bundle is not None
    assert len(bundle.medications) >= 2
    med_names = [m.name for m in bundle.medications]
    assert any("Paracetamol" in n for n in med_names)
    assert any("Cetirizine" in n for n in med_names)


def test_service_get_bundle_by_id_not_found():
    """Verify lookup of non-existent bundle returns None."""
    bundle = express_consultation_service.get_bundle_by_id("BUNDLE-NON-EXISTENT")
    assert bundle is None


# ============================================================================
# Service Layer Unit Tests: Allergy & Safety Shield
# ============================================================================


def test_service_allergy_profile_arun_patel_penicillin():
    """Verify Arun Patel has certified severe Penicillin & beta-lactam allergy."""
    profile = express_consultation_service.get_patient_safety_profile("pat-arun-patel")
    assert isinstance(profile, PatientAllergyProfile)
    assert profile.has_known_allergies is True
    assert any("penicillin" in a.substance.lower() for a in profile.allergies)
    assert "CRITICAL ALLERGY ALERT" in profile.safety_alert_banner


def test_service_allergy_profile_ramesh_patel_sulfa():
    """Verify Ramesh Patel has certified Sulfonamide allergy."""
    profile = express_consultation_service.get_patient_safety_profile("pat-ramesh-patel")
    assert profile.has_known_allergies is True
    assert any("sulfa" in a.substance.lower() for a in profile.allergies)


def test_service_allergy_profile_aarav_patel_nkda():
    """Verify Aarav Patel has No Known Drug Allergies (NKDA)."""
    profile = express_consultation_service.get_patient_safety_profile("pat-aarav-patel")
    assert profile.has_known_allergies is False
    assert "NKDA" in profile.safety_alert_banner


def test_service_safety_check_penicillin_blocking():
    """Verify prescribing Amoxicillin to Penicillin-allergic patient triggers immediate block."""
    dangerous_meds = [
        QuickPrescriptionItem(
            medicine_id="med-amox-500",
            name="Amoxicillin 500mg",
            generic_name="Amoxicillin",
            dosage_form="Capsule",
            strength="500mg",
            morning=True,
            afternoon=False,
            night=True,
            frequency_badge="1-0-1",
            duration_days=5,
            instruction="Take 1 capsule after food",
            allergy_substance_tag="penicillin",
        )
    ]
    is_safe, conflicts = express_consultation_service.check_medication_safety(
        "pat-arun-patel", dangerous_meds
    )
    assert is_safe is False
    assert len(conflicts) >= 1
    assert "Penicillin" in conflicts[0]


def test_service_safety_check_sulfa_blocking():
    """Verify prescribing Sulfa drug to Sulfa-allergic patient triggers block."""
    sulfa_meds = [
        QuickPrescriptionItem(
            medicine_id="med-cotrimox",
            name="Bactrim DS",
            generic_name="Sulfamethoxazole + Trimethoprim",
            dosage_form="Tablet",
            strength="800mg / 160mg",
            morning=True,
            afternoon=False,
            night=True,
            frequency_badge="1-0-1",
            duration_days=5,
            instruction="Take with food",
            allergy_substance_tag="sulfa",
        )
    ]
    is_safe, conflicts = express_consultation_service.check_medication_safety(
        "pat-ramesh-patel", sulfa_meds
    )
    assert is_safe is False
    assert len(conflicts) >= 1
    assert "Sulfa" in conflicts[0]


def test_service_safety_check_clean_prescription():
    """Verify non-conflicting medication passes safety check."""
    clean_meds = [
        QuickPrescriptionItem(
            medicine_id="med-pcm-650",
            name="Paracetamol 650mg",
            generic_name="Paracetamol",
            dosage_form="Tablet",
            strength="650mg",
            morning=True,
            afternoon=False,
            night=True,
            frequency_badge="1-0-1",
            duration_days=3,
            instruction="Take 1 tablet after food",
            allergy_substance_tag="paracetamol",
        )
    ]
    is_safe, conflicts = express_consultation_service.check_medication_safety(
        "pat-arun-patel", clean_meds
    )
    assert is_safe is True
    assert len(conflicts) == 0


# ============================================================================
# Atomic Encounter Submission & Queue Advancement Benchmark Tests
# ============================================================================


def test_service_atomic_encounter_submission_sub_50ms():
    """Verify express consultation completes and signs within sub-50ms SLA."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        doctor_hpr="ananya.sharma@hpr.abdm",
        facility_id="aiims-delhi-01",
        token_number="OPD-041",
        chief_complaints=["Viral Fever"],
        clinical_diagnosis="Acute upper respiratory infection [J06.9]",
        icd10_code="J06.9",
        prescribed_medications=[
            QuickPrescriptionItem(
                medicine_id="med-pcm-650",
                name="Paracetamol 650mg",
                generic_name="Paracetamol",
                dosage_form="Tablet",
                strength="650mg",
                morning=True,
                afternoon=False,
                night=True,
                frequency_badge="1-0-1",
                duration_days=3,
                instruction="Take 1 tablet after food",
            )
        ],
        clinical_advice=["Adequate hydration", "Warm saline gargles"],
        follow_up_days=3,
    )

    # Allow 1 warm call then assert sub-50ms SLA
    res = express_consultation_service.submit_express_encounter(req)
    t0 = time.perf_counter()
    res = express_consultation_service.submit_express_encounter(req)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert isinstance(res, ExpressEncounterSubmitResponse)
    assert res.status == "COMPLETED"
    assert res.encounter_id.startswith("enc_exp_")
    assert len(res.digital_signature_hash) == 64  # SHA-256
    assert "ABDM-HPR-SEAL" in res.hpr_sign_seal
    assert res.prescribed_count == 1
    assert res.latency_ms < 50.0  # Internal sub-50ms SLA requirement



def test_service_atomic_encounter_queue_advancement():
    """Verify OPD queue advances automatically to next patient."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        doctor_hpr="ananya.sharma@hpr.abdm",
        facility_id="aiims-delhi-01",
        token_number="OPD-041",
        chief_complaints=["Viral Fever"],
        clinical_diagnosis="Viral Fever",
        prescribed_medications=[],
        clinical_advice=[],
        follow_up_days=3,
    )
    res = express_consultation_service.submit_express_encounter(req)
    assert res.next_token_called == "OPD-042"
    assert res.next_patient_name == "Aarav Patel"


def test_service_atomic_encounter_hpr_seal_format():
    """Verify cryptographic HPR signature format."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        doctor_hpr="ananya.sharma@hpr.abdm",
        facility_id="aiims-delhi-01",
        chief_complaints=["Viral Fever"],
        clinical_diagnosis="Acute Viral Rhinitis",
        prescribed_medications=[],
        clinical_advice=[],
        follow_up_days=3,
    )
    res = express_consultation_service.submit_express_encounter(req)
    assert "ananya.sharma@hpr.abdm" in res.hpr_sign_seal
    assert "SIG=" in res.hpr_sign_seal


def test_service_atomic_encounter_fhir_bundle_minting():
    """Verify FHIR bundle and encounter URIs conform to ABDM standards."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        doctor_hpr="ananya.sharma@hpr.abdm",
        facility_id="aiims-delhi-01",
        chief_complaints=["Hypertension"],
        clinical_diagnosis="Essential hypertension [I10]",
        prescribed_medications=[],
        clinical_advice=[],
        follow_up_days=30,
    )
    res = express_consultation_service.submit_express_encounter(req)
    assert res.fhir_bundle_id.startswith("bundle_fhir_")
    assert res.fhir_encounter_uri.startswith("urn:uuid:enc_exp_")


def test_service_safety_violation_in_submission():
    """Verify safety warnings are prepended to clinical advice when contraindications exist."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        doctor_hpr="ananya.sharma@hpr.abdm",
        facility_id="aiims-delhi-01",
        chief_complaints=["Bacterial Tonsillitis"],
        clinical_diagnosis="Acute follicular tonsillitis",
        prescribed_medications=[
            QuickPrescriptionItem(
                medicine_id="med-amox-500",
                name="Amoxicillin 500mg",
                generic_name="Amoxicillin",
                dosage_form="Capsule",
                strength="500mg",
                morning=True,
                afternoon=False,
                night=True,
                frequency_badge="1-0-1",
                duration_days=5,
                instruction="Take 1 capsule",
                allergy_substance_tag="penicillin",
            )
        ],
        clinical_advice=["Rest well"],
        follow_up_days=5,
    )
    res = express_consultation_service.submit_express_encounter(req)
    # Stored record should have safety warning prepended
    stored = express_consultation_service._completed_encounters[res.encounter_id]
    advice = stored["clinical_advice"]
    assert any("SAFETY WARNING" in a for a in advice)


def test_service_reset_state():
    """Verify reset_state clears completed encounters and resets queue."""
    req = ExpressEncounterSubmitRequest(
        patient_id="pat-arun-patel",
        doctor_id="doc-ananya-sharma",
        facility_id="aiims-delhi-01",
        chief_complaints=["Fever"],
        clinical_diagnosis="Fever",
        prescribed_medications=[],
        clinical_advice=[],
        follow_up_days=3,
    )
    express_consultation_service.submit_express_encounter(req)
    assert len(express_consultation_service._completed_encounters) > 0

    express_consultation_service.reset_state()
    assert len(express_consultation_service._completed_encounters) == 0


# ============================================================================
# REST API Endpoint Integration Tests (AsyncClient)
# ============================================================================


@pytest.mark.asyncio
async def test_endpoint_get_templates():
    """GET /api/v1/doctor/express-consultation/templates returns 200 and templates payload."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/doctor/express-consultation/templates")
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        data = env["data"]
        assert "chief_complaints" in data
        assert "prescription_bundles" in data
        assert len(data["chief_complaints"]) >= 7
        assert len(data["prescription_bundles"]) >= 7


@pytest.mark.asyncio
async def test_endpoint_get_templates_category_filter():
    """GET /api/v1/doctor/express-consultation/templates?category=cardio filters items."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/doctor/express-consultation/templates?category=cardio")
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        data = env["data"]
        assert all(c["category"] == "cardio" for c in data["chief_complaints"])


@pytest.mark.asyncio
async def test_endpoint_get_patient_safety_arun():
    """GET /api/v1/doctor/express-consultation/patient-safety/pat-arun-patel returns Penicillin allergy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/doctor/express-consultation/patient-safety/pat-arun-patel")
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        profile = env["data"]
        assert profile["has_known_allergies"] is True
        assert "CRITICAL ALLERGY ALERT" in profile["safety_alert_banner"]


@pytest.mark.asyncio
async def test_endpoint_get_patient_safety_nkda():
    """GET /api/v1/doctor/express-consultation/patient-safety/pat-aarav-patel returns NKDA profile."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/doctor/express-consultation/patient-safety/pat-aarav-patel")
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        profile = env["data"]
        assert profile["has_known_allergies"] is False
        assert "NKDA" in profile["safety_alert_banner"]


@pytest.mark.asyncio
async def test_endpoint_check_safety_clean():
    """POST /api/v1/doctor/express-consultation/check-safety with safe meds returns is_safe=True."""
    transport = ASGITransport(app=app)
    payload = {
        "patient_id": "pat-arun-patel",
        "medications": [
            {
                "medicine_id": "med-pcm-650",
                "name": "Paracetamol 650mg",
                "generic_name": "Paracetamol",
                "dosage_form": "Tablet",
                "strength": "650mg",
                "morning": True,
                "afternoon": False,
                "night": True,
                "frequency_badge": "1-0-1",
                "duration_days": 3,
                "instruction": "Take 1 tablet after food",
                "allergy_substance_tag": "paracetamol",
            }
        ],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/doctor/express-consultation/check-safety", json=payload)
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        assert env["data"]["is_safe"] is True
        assert len(env["data"]["conflicts"]) == 0


@pytest.mark.asyncio
async def test_endpoint_check_safety_violation():
    """POST /api/v1/doctor/express-consultation/check-safety with Amoxicillin triggers violation."""
    transport = ASGITransport(app=app)
    payload = {
        "patient_id": "pat-arun-patel",
        "medications": [
            {
                "medicine_id": "med-amox-500",
                "name": "Amoxicillin 500mg",
                "generic_name": "Amoxicillin",
                "dosage_form": "Capsule",
                "strength": "500mg",
                "morning": True,
                "afternoon": False,
                "night": True,
                "frequency_badge": "1-0-1",
                "duration_days": 5,
                "instruction": "Take 1 capsule",
                "allergy_substance_tag": "penicillin",
            }
        ],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/doctor/express-consultation/check-safety", json=payload)
        assert res.status_code == 200
        env = res.json()
        assert env["success"] is True
        assert env["data"]["is_safe"] is False
        assert len(env["data"]["conflicts"]) >= 1


@pytest.mark.asyncio
async def test_endpoint_submit_express_encounter():
    """POST /api/v1/doctor/express-consultation/submit signs encounter and advances queue."""
    transport = ASGITransport(app=app)
    payload = {
        "patient_id": "pat-arun-patel",
        "doctor_id": "doc-ananya-sharma",
        "doctor_hpr": "ananya.sharma@hpr.abdm",
        "facility_id": "aiims-delhi-01",
        "token_number": "OPD-041",
        "chief_complaints": ["Viral Fever"],
        "clinical_diagnosis": "Acute Febrile Illness [J06.9]",
        "icd10_code": "J06.9",
        "prescribed_medications": [
            {
                "medicine_id": "med-pcm-650",
                "name": "Paracetamol 650mg",
                "generic_name": "Paracetamol",
                "dosage_form": "Tablet",
                "strength": "650mg",
                "morning": True,
                "afternoon": False,
                "night": True,
                "frequency_badge": "1-0-1",
                "duration_days": 3,
                "instruction": "Take 1 tablet after food",
            }
        ],
        "clinical_advice": ["Rest well", "Warm fluids"],
        "follow_up_days": 3,
        "emergency_escalation": False,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/doctor/express-consultation/submit", json=payload)
        assert res.status_code == 201
        env = res.json()
        assert env["success"] is True
        data = env["data"]
        assert data["status"] == "COMPLETED"
        assert data["encounter_id"].startswith("enc_exp_")
        assert data["next_token_called"] == "OPD-042"
        assert data["latency_ms"] < 50.0


@pytest.mark.asyncio
async def test_endpoint_submit_latency_sla():
    """Verify end-to-end API latency for sequential encounter submissions adheres to sub-50ms SLA."""
    transport = ASGITransport(app=app)
    latencies = []
    payload = {
        "patient_id": "pat-arun-patel",
        "doctor_id": "doc-ananya-sharma",
        "doctor_hpr": "ananya.sharma@hpr.abdm",
        "facility_id": "aiims-delhi-01",
        "chief_complaints": ["Follow-up"],
        "clinical_diagnosis": "Routine follow-up",
        "prescribed_medications": [],
        "clinical_advice": ["Maintain diet"],
        "follow_up_days": 14,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for _ in range(5):
            t0 = time.perf_counter()
            res = await ac.post("/api/v1/doctor/express-consultation/submit", json=payload)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert res.status_code == 201
            latencies.append(elapsed_ms)

    # All should be well under 50ms in this environment
    assert all(lat < 50.0 for lat in latencies)
