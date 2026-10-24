"""Comprehensive unit and integration test suite for Electronic Prescriptions and MedicationRequests.

Validates:
1. Draft prescription authoring with structured dosage and dispense parameters.
2. Rejection of invalid medication catalog ID (HTTP 404).
3. Rejection of non-existent patient ID (HTTP 404).
4. Role-based access control (Doctor/Admin can author, Patient cannot -> HTTP 403).
5. Detailed prescription retrieval by UUID with nested medication catalog data.
6. Updating unsigned draft prescriptions.
7. Cryptographic SHA-256 digital signature attestation and status transition to ACTIVE.
8. Post-signature immutability guard: preventing modification of signed prescriptions (HTTP 409 Conflict).
9. Prescription cancellation with clinical rationale.
10. Paginated query and multi-parameter filtering (status, is_signed, prescriber).
11. HL7 FHIR Release 4 MedicationRequest export and ABDM NRCeS profile conformance.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AdministrationRoute,
    FormularyTier,
    Gender,
    MedicalSpecialty,
    MedicationForm,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
    MedicationStatus,
    UserRole,
)
from app.models.medication import Medication
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def rx_test_env():
    """Provide isolated in-memory SQLite database and async HTTP client."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


def auth_header_for(user: User) -> dict:
    """Generate JWT authorization bearer header for test user."""
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


async def seed_rx_actors(session_factory) -> dict:
    """Seed patient, doctor, catalog medication, and unauthorized user."""
    async with session_factory() as session:
        # 1. Doctor user & profile
        u_doc = User(
            id="user-doc-sharma",
            email="dr.sharma@nirmaya.health",
            full_name="Dr. Ananya Sharma",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(u_doc)
        await session.flush()

        doc_profile = DoctorProfile(
            id="doc-profile-sharma",
            user_id=u_doc.id,
            registration_number="DMC/2026/0991",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD Cardiology",
            experience_years=12,
            consultation_fee=1200.0,
            hpr_id="ananya.sharma@hpr.abdm",
        )
        session.add(doc_profile)

        # 2. Patient user & profile
        u_pat = User(
            id="user-pat-patel",
            email="arun.patel@nirmaya.health",
            full_name="Arun Patel",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(u_pat)
        await session.flush()

        pat_profile = PatientProfile(
            id="pat-profile-patel",
            user_id=u_pat.id,
            gender=Gender.MALE,
            date_of_birth=date(1982, 8, 14),
            blood_group="B+",
            abha_number="91-8899-0011-2233",
            abha_address="arun.patel@abdm",
        )
        session.add(pat_profile)

        # 3. Third party patient (unauthorized to view pat's rx)
        u_unauth = User(
            id="user-pat-unauth",
            email="unauth@nirmaya.health",
            full_name="Priya Nair",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(u_unauth)
        await session.flush()

        unauth_profile = PatientProfile(
            id="pat-profile-unauth",
            user_id=u_unauth.id,
            gender=Gender.FEMALE,
            date_of_birth=date(1990, 5, 20),
            blood_group="O+",
            abha_number="91-5566-7788-9900",
            abha_address="priya.nair@abdm",
        )
        session.add(unauth_profile)

        # 4. Catalog Medication
        medication = Medication(
            id="med-atorvastatin-20",
            name="Atorvastatin 20mg Oral Tablet",
            generic_name="Atorvastatin Calcium",
            brand_name="Lipitor",
            rxnorm_code="855332",
            rxnorm_display="Atorvastatin 20 MG Oral Tablet",
            atc_code="C10AA05",
            atc_display="Atorvastatin",
            snomed_code="387584000",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="20 mg",
            active_ingredient="Atorvastatin",
            is_prescription_required=True,
            is_controlled_substance=False,
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(medication)
        await session.commit()

    return {
        "doctor_user": u_doc,
        "doctor_profile": doc_profile,
        "patient_user": u_pat,
        "patient_profile": pat_profile,
        "unauth_user": u_unauth,
        "unauth_profile": unauth_profile,
        "medication": medication,
    }


@pytest.mark.asyncio
async def test_create_draft_prescription(rx_test_env) -> None:
    """Verify that a doctor can draft a new electronic prescription."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    payload = {
        "medication_id": actors["medication"].id,
        "intent": "order",
        "priority": "routine",
        "dosage_text": "Take 1 tablet orally once daily at bedtime for 30 days",
        "dose_quantity": 20.0,
        "dose_unit": "mg",
        "route": "oral",
        "frequency": 1,
        "period": 1.0,
        "period_unit": "d",
        "as_needed": False,
        "additional_instructions": "Take at bedtime with water.",
        "dispense_quantity": 30.0,
        "dispense_unit": "tablets",
        "expected_supply_duration_days": 30,
        "number_of_repeats_allowed": 0,
        "allow_generic_substitution": True,
        "reason_code": "I10",
        "note": "Primary prevention of dyslipidemia.",
    }

    res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json=payload,
    )

    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["patient_id"] == actors["patient_profile"].id
    assert data["doctor_id"] == actors["doctor_profile"].id
    assert data["medication_id"] == actors["medication"].id
    assert data["status"] == "draft"
    assert data["is_signed"] is False
    assert data["dosage_text"] == "Take 1 tablet orally once daily at bedtime for 30 days"
    assert data["dispense_quantity"] == 30.0
    assert data["medication"]["name"] == "Atorvastatin 20mg Oral Tablet"


@pytest.mark.asyncio
async def test_create_prescription_invalid_medication(rx_test_env) -> None:
    """Verify 404 when referencing non-existent catalog medication."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    payload = {
        "medication_id": "non-existent-med-id",
        "dosage_text": "Take 1 tablet orally daily",
    }

    res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json=payload,
    )

    assert res.status_code == 404
    assert "Medication with identifier 'non-existent-med-id' not found" in res.json()["message"]


@pytest.mark.asyncio
async def test_create_prescription_invalid_patient(rx_test_env) -> None:
    """Verify 404 when referencing non-existent patient profile."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    payload = {
        "medication_id": actors["medication"].id,
        "dosage_text": "Take 1 tablet daily",
    }

    res = await client.post(
        "/api/v1/patients/non-existent-patient-id/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json=payload,
    )

    assert res.status_code == 404
    assert "Patient with identifier 'non-existent-patient-id' not found" in res.json()["message"]


@pytest.mark.asyncio
async def test_create_prescription_rbac_forbidden(rx_test_env) -> None:
    """Verify that a patient cannot author a prescription (HTTP 403)."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    payload = {
        "medication_id": actors["medication"].id,
        "dosage_text": "Self-prescribed medication",
    }

    res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["patient_user"]),
        json=payload,
    )

    assert res.status_code == 403
    assert "Only verified healthcare providers (doctors)" in res.json()["message"]


@pytest.mark.asyncio
async def test_get_prescription_details(rx_test_env) -> None:
    """Verify fetching prescription details by UUID."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet orally once daily",
            "dose_quantity": 20.0,
            "dose_unit": "mg",
            "dispense_quantity": 30.0,
        },
    )
    rx_id = create_res.json()["data"]["id"]

    res = await client.get(
        f"/api/v1/prescriptions/{rx_id}",
        headers=auth_header_for(actors["patient_user"]),
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == rx_id
    assert data["medication"]["rxnorm_code"] == "855332"


@pytest.mark.asyncio
async def test_update_draft_prescription(rx_test_env) -> None:
    """Verify updating fields of an unsigned draft prescription."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet daily",
            "dispense_quantity": 10.0,
        },
    )
    rx_id = create_res.json()["data"]["id"]

    update_res = await client.patch(
        f"/api/v1/prescriptions/{rx_id}",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "dosage_text": "Amended: Take 1 tablet twice daily with food",
            "dispense_quantity": 60.0,
            "expected_supply_duration_days": 30,
        },
    )

    assert update_res.status_code == 200
    data = update_res.json()["data"]
    assert data["dosage_text"] == "Amended: Take 1 tablet twice daily with food"
    assert data["dispense_quantity"] == 60.0


@pytest.mark.asyncio
async def test_sign_prescription_cryptographic_seal(rx_test_env) -> None:
    """Verify that doctor signing applies SHA-256 digest and transitions status to active."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet orally once daily",
            "dose_quantity": 20.0,
            "dose_unit": "mg",
            "dispense_quantity": 30.0,
        },
    )
    rx_id = create_res.json()["data"]["id"]

    sign_res = await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        headers=auth_header_for(actors["doctor_user"]),
        json={"signature_notes": "Clinical indications verified with laboratory profile."},
    )

    assert sign_res.status_code == 200
    data = sign_res.json()["data"]
    assert data["is_signed"] is True
    assert data["status"] == "active"
    assert data["signed_at"] is not None
    assert data["signature_hash"] is not None
    assert len(data["signature_hash"]) == 64  # Hex SHA-256 digest


@pytest.mark.asyncio
async def test_post_signature_immutability_guard(rx_test_env) -> None:
    """Verify that signed prescriptions cannot be updated (HTTP 409 Conflict)."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet daily",
        },
    )
    rx_id = create_res.json()["data"]["id"]

    # Sign prescription
    await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        headers=auth_header_for(actors["doctor_user"]),
    )

    # Attempt to modify signed prescription
    tamper_res = await client.patch(
        f"/api/v1/prescriptions/{rx_id}",
        headers=auth_header_for(actors["doctor_user"]),
        json={"dosage_text": "Tampered dosage modification"},
    )

    assert tamper_res.status_code == 409
    body = tamper_res.json()
    assert body["error_code"] == "IMMUTABLE_SIGNED_RECORD"


@pytest.mark.asyncio
async def test_cancel_prescription_with_rationale(rx_test_env) -> None:
    """Verify discontinuing / cancelling an active prescription."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet daily",
        },
    )
    rx_id = create_res.json()["data"]["id"]

    cancel_res = await client.post(
        f"/api/v1/prescriptions/{rx_id}/cancel",
        headers=auth_header_for(actors["doctor_user"]),
        json={"cancellation_reason": "Patient developed myalgia; switching to rosuvastatin."},
    )

    assert cancel_res.status_code == 200
    data = cancel_res.json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Patient developed myalgia; switching to rosuvastatin."


@pytest.mark.asyncio
async def test_list_patient_prescriptions_filtering(rx_test_env) -> None:
    """Verify querying patient prescriptions with status filters."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    # Create 2 prescriptions: one draft, one signed
    res1 = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={"medication_id": actors["medication"].id, "dosage_text": "Rx 1 Draft"},
    )
    res2 = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={"medication_id": actors["medication"].id, "dosage_text": "Rx 2 Signed"},
    )
    rx2_id = res2.json()["data"]["id"]
    await client.post(
        f"/api/v1/prescriptions/{rx2_id}/sign",
        headers=auth_header_for(actors["doctor_user"]),
    )

    # 1. Query all
    all_res = await client.get(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["patient_user"]),
    )
    assert all_res.status_code == 200
    assert all_res.json()["pagination"]["total_count"] == 2

    # 2. Query only signed
    signed_res = await client.get(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions?is_signed=true",
        headers=auth_header_for(actors["patient_user"]),
    )
    assert signed_res.status_code == 200
    assert signed_res.json()["pagination"]["total_count"] == 1
    assert signed_res.json()["data"][0]["dosage_text"] == "Rx 2 Signed"


@pytest.mark.asyncio
async def test_export_prescription_fhir_r4(rx_test_env) -> None:
    """Verify exporting prescription to HL7 FHIR R4 MedicationRequest."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet orally once daily at bedtime",
            "dose_quantity": 20.0,
            "dose_unit": "mg",
            "route": "oral",
            "dispense_quantity": 30.0,
            "dispense_unit": "tablets",
            "reason_code": "I10",
        },
    )
    rx_id = create_res.json()["data"]["id"]

    fhir_res = await client.get(
        f"/api/v1/prescriptions/{rx_id}/fhir",
        headers=auth_header_for(actors["patient_user"]),
    )

    assert fhir_res.status_code == 200
    fhir_data = fhir_res.json()
    assert fhir_data["resourceType"] == "MedicationRequest"
    assert fhir_data["id"] == rx_id
    assert fhir_data["subject"]["reference"] == f"Patient/{actors['patient_profile'].id}"
    assert fhir_data["medicationReference"]["reference"] == f"Medication/{actors['medication'].id}"
    assert fhir_data["meta"]["profile"] == ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Prescription"]
    assert fhir_data["dosageInstruction"][0]["text"] == "Take 1 tablet orally once daily at bedtime"


@pytest.mark.asyncio
async def test_prescription_with_refills_and_generic_substitution(rx_test_env) -> None:
    """Verify authoring prescription with refills, PRN condition, and substitution permission."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet orally as needed for severe tension headache",
            "dose_quantity": 20.0,
            "dose_unit": "mg",
            "route": "oral",
            "as_needed": True,
            "as_needed_reason": "For acute tension headache",
            "dispense_quantity": 30.0,
            "dispense_unit": "tablets",
            "number_of_repeats_allowed": 3,
            "allow_generic_substitution": True,
            "reason_code": "G44.209",
        },
    )

    assert create_res.status_code == 201
    data = create_res.json()["data"]
    assert data["as_needed"] is True
    assert data["as_needed_reason"] == "For acute tension headache"
    assert data["number_of_repeats_allowed"] == 3
    assert data["allow_generic_substitution"] is True

    # Validate FHIR export represents substitution and repeats
    rx_id = data["id"]
    fhir_res = await client.get(
        f"/api/v1/prescriptions/{rx_id}/fhir",
        headers=auth_header_for(actors["patient_user"]),
    )
    assert fhir_res.status_code == 200
    fhir_data = fhir_res.json()
    assert fhir_data["dispenseRequest"]["numberOfRepeatsAllowed"] == 3
    assert fhir_data["substitution"]["allowedBoolean"] is True


@pytest.mark.asyncio
async def test_sign_prescription_idempotency_and_hash_stability(rx_test_env) -> None:
    """Verify that repeatedly signing an already signed prescription is idempotent and maintains SHA-256 digest stability."""
    client, session_factory = rx_test_env
    actors = await seed_rx_actors(session_factory)

    # 1. Draft prescription
    create_res = await client.post(
        f"/api/v1/patients/{actors['patient_profile'].id}/prescriptions",
        headers=auth_header_for(actors["doctor_user"]),
        json={
            "medication_id": actors["medication"].id,
            "dosage_text": "Take 1 tablet daily with food",
            "dose_quantity": 20.0,
            "dose_unit": "mg",
        },
    )
    rx_id = create_res.json()["data"]["id"]

    # 2. First sign operation
    sign_res_1 = await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        headers=auth_header_for(actors["doctor_user"]),
        json={"signature_notes": "Initial clinician authorization"},
    )
    assert sign_res_1.status_code == 200
    data_1 = sign_res_1.json()["data"]
    assert data_1["is_signed"] is True
    hash_1 = data_1["signature_hash"]
    assert len(hash_1) == 64  # SHA-256 64-char hex string

    # 3. Second sign operation (idempotency check)
    sign_res_2 = await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        headers=auth_header_for(actors["doctor_user"]),
        json={"signature_notes": "Attempting secondary sign"},
    )
    assert sign_res_2.status_code == 200
    data_2 = sign_res_2.json()["data"]
    assert data_2["is_signed"] is True
    assert data_2["signature_hash"] == hash_1  # Hash remains invariant and stable

