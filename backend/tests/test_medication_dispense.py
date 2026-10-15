"""Comprehensive unit and integration test suite for Pharmacy Medication Dispense & Fulfillment.

Tests:
1. Dispensing an active digitally signed prescription with lot number, expiry, and quantity tracking.
2. Rejection of dispensing an unsigned/draft prescription (HTTP 400).
3. Enforcement of authorized repeat refill quotas (transitioning to completed, rejection when exhausted).
4. Generic substitution governance (authorized substitution succeeds; forbidden substitution rejected).
5. Listing dispensations with patient, prescription, and lot number filters.
6. Exporting dispensation as canonical HL7 FHIR Release 4 MedicationDispense JSON.
7. Role-based access control (Doctor/Pharmacist can dispense, Patient cannot).
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
    MedicationDispenseStatus,
    MedicationForm,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
    MedicationStatus,
    UserRole,
)
from app.models.medication import Medication
from app.models.medication_dispense import MedicationDispense
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.models.user import User


@pytest_asyncio.fixture
async def dispense_test_env():
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


async def seed_dispense_actors(session_factory) -> dict:
    """Seed doctor, pharmacist, patient, and catalog medications."""
    async with session_factory() as session:
        # 1. Doctor
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
            specialty=MedicalSpecialty.GENERAL_MEDICINE,
            qualifications="MBBS, MD",
            experience_years=10,
            consultation_fee=1000.0,
        )
        session.add(doc_profile)

        # 2. Pharmacist / Clinical Staff
        u_pharm = User(
            id="user-pharm-khan",
            email="rashid.khan@nirmaya.health",
            full_name="Rashid Khan",
            role=UserRole.DOCTOR,  # clinical practitioner with dispensing authority
            is_active=True,
            is_verified=True,
        )
        session.add(u_pharm)

        # 3. Patient
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
            date_of_birth=date(1985, 4, 12),
            blood_group="O+",
            abha_number="91-1122-3344-5566",
            abha_address="arun.patel@abdm",
        )
        session.add(pat_profile)

        # 4. Another patient (unauthorized)
        u_unauth = User(
            id="user-pat-unauth",
            email="unauth@nirmaya.health",
            full_name="Sunil Verma",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(u_unauth)
        await session.flush()

        # 5. Catalog Medications: Brand & Generic
        med_brand = Medication(
            id="med-lipitor-20",
            name="Lipitor 20mg Oral Tablet",
            generic_name="Atorvastatin Calcium",
            brand_name="Lipitor",
            rxnorm_code="859088",
            rxnorm_display="Atorvastatin 20 MG Oral Tablet",
            atc_code="C10AA05",
            snomed_code="387584000",
            form=MedicationForm.TABLET,
            strength="20 mg",
            active_ingredient="Atorvastatin Calcium",
            formulary_tier=FormularyTier.TIER_2_PREFERRED_BRAND,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_brand)

        med_generic = Medication(
            id="med-atorva-generic-20",
            name="Atorvastatin Calcium 20mg Tablet",
            generic_name="Atorvastatin Calcium",
            brand_name="Atorva",
            rxnorm_code="859088",
            rxnorm_display="Atorvastatin 20 MG Oral Tablet",
            atc_code="C10AA05",
            snomed_code="387584000",
            form=MedicationForm.TABLET,
            strength="20 mg",
            active_ingredient="Atorvastatin Calcium",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_generic)

        # 6. Active signed prescription (allows generic substitution, 1 refill allowed)
        rx_signed = MedicationRequest(
            id="rx-signed-001",
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            medication_id=med_brand.id,
            status=MedicationRequestStatus.ACTIVE,
            intent=MedicationRequestIntent.ORDER,
            priority=MedicationRequestPriority.ROUTINE,
            dosage_text="Take 1 tablet orally once daily at bedtime",
            dose_quantity=20.0,
            dose_unit="mg",
            route=AdministrationRoute.ORAL,
            frequency=1,
            dispense_quantity=30.0,
            dispense_unit="tablets",
            expected_supply_duration_days=30,
            number_of_repeats_allowed=1,
            allow_generic_substitution=True,
            is_signed=True,
            signed_at=datetime.now(timezone.utc),
            signature_hash="sha256-signed-digest-001",
        )
        session.add(rx_signed)

        # 7. Unsigned draft prescription
        rx_unsigned = MedicationRequest(
            id="rx-unsigned-002",
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            medication_id=med_brand.id,
            status=MedicationRequestStatus.DRAFT,
            intent=MedicationRequestIntent.ORDER,
            priority=MedicationRequestPriority.ROUTINE,
            dosage_text="Take 1 tablet daily",
            is_signed=False,
            number_of_repeats_allowed=0,
            allow_generic_substitution=True,
        )
        session.add(rx_unsigned)

        # 8. Prescription forbidding substitution
        rx_no_sub = MedicationRequest(
            id="rx-no-sub-003",
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            medication_id=med_brand.id,
            status=MedicationRequestStatus.ACTIVE,
            intent=MedicationRequestIntent.ORDER,
            priority=MedicationRequestPriority.ROUTINE,
            dosage_text="Take 1 tablet daily - dispense as written",
            dispense_quantity=30.0,
            dispense_unit="tablets",
            number_of_repeats_allowed=0,
            allow_generic_substitution=False,
            is_signed=True,
            signed_at=datetime.now(timezone.utc),
            signature_hash="sha256-signed-digest-no-sub",
        )
        session.add(rx_no_sub)

        await session.commit()

        return {
            "doctor_user": u_doc,
            "pharmacist_user": u_pharm,
            "patient_user": u_pat,
            "unauth_user": u_unauth,
            "patient_profile": pat_profile,
            "med_brand": med_brand,
            "med_generic": med_generic,
            "rx_signed": rx_signed,
            "rx_unsigned": rx_unsigned,
            "rx_no_sub": rx_no_sub,
        }


@pytest.mark.asyncio
async def test_dispense_active_prescription_success(dispense_test_env):
    """Test dispensing an active signed prescription with lot number and expiry."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    dispense_payload = {
        "prescription_id": actors["rx_signed"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "days_supply": 30,
        "lot_number": "LOT-2026-X42",
        "expiration_date": "2027-11-30",
        "pharmacist_notes": "First fill. Patient counseled on lipid medication.",
    }

    resp = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=dispense_payload,
        headers=auth_header_for(actors["pharmacist_user"]),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]

    assert data["prescription_id"] == actors["rx_signed"].id
    assert data["patient_id"] == actors["patient_profile"].id
    assert data["medication_id"] == actors["med_brand"].id
    assert data["status"] == "completed"
    assert data["quantity_dispensed"] == 30.0
    assert data["dispense_unit"] == "tablets"
    assert data["days_supply"] == 30
    assert data["lot_number"] == "LOT-2026-X42"
    assert data["expiration_date"] == "2027-11-30"
    assert data["was_substituted"] is False
    assert data["dispense_number"].startswith("DISP-")
    assert data["dispenser_name"] == "Rashid Khan"
    assert data["medication_name"] == "Lipitor 20mg Oral Tablet"


@pytest.mark.asyncio
async def test_dispense_unsigned_prescription_rejected(dispense_test_env):
    """Test that dispensing an unsigned draft prescription is rejected with HTTP 400."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    dispense_payload = {
        "prescription_id": actors["rx_unsigned"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
    }

    resp = await client.post(
        f"/api/v1/prescriptions/{actors['rx_unsigned'].id}/dispense",
        json=dispense_payload,
        headers=auth_header_for(actors["pharmacist_user"]),
    )
    assert resp.status_code == 400
    assert "not been digitally signed" in resp.json()["message"]


@pytest.mark.asyncio
async def test_dispense_repeats_limit_enforced(dispense_test_env):
    """Test authorized refills limit enforcement: original + 1 refill, then reject 3rd fill."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    headers = auth_header_for(actors["pharmacist_user"])
    payload = {
        "prescription_id": actors["rx_signed"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "days_supply": 30,
        "lot_number": "LOT-2026-R1",
    }

    # Fill 1: Original fill (1/2 fills)
    resp1 = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=payload,
        headers=headers,
    )
    assert resp1.status_code == 201

    # Check prescription is still ACTIVE because 1 refill remains
    async with session_factory() as session:
        rx = await session.get(MedicationRequest, actors["rx_signed"].id)
        assert rx.status == MedicationRequestStatus.ACTIVE

    # Fill 2: Authorized Refill (2/2 fills) -> should exhaust repeats and transition prescription to COMPLETED
    payload["lot_number"] = "LOT-2026-R2"
    resp2 = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=payload,
        headers=headers,
    )
    assert resp2.status_code == 201

    async with session_factory() as session:
        rx = await session.get(MedicationRequest, actors["rx_signed"].id)
        assert rx.status == MedicationRequestStatus.COMPLETED

    # Fill 3: Unauthorized excess fill (3/2 fills) -> HTTP 400 REFILLS_EXHAUSTED
    payload["lot_number"] = "LOT-2026-R3"
    resp3 = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=payload,
        headers=headers,
    )
    assert resp3.status_code == 400
    assert "Maximum authorized prescription fills reached" in resp3.json()["message"]


@pytest.mark.asyncio
async def test_generic_substitution_governance(dispense_test_env):
    """Test generic substitution rules: permitted when prescriber allows, forbidden when prescriber forbids."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    headers = auth_header_for(actors["pharmacist_user"])

    # 1. Permitted substitution: rx_signed allows generic substitution
    sub_payload = {
        "prescription_id": actors["rx_signed"].id,
        "medication_id": actors["med_generic"].id,  # substitute with generic
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "was_substituted": True,
        "substitution_type": "G",
        "substitution_reason": "Formulary tier-1 generic equivalent supplied",
        "lot_number": "LOT-GEN-99",
    }
    resp1 = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=sub_payload,
        headers=headers,
    )
    assert resp1.status_code == 201, resp1.text
    data1 = resp1.json()["data"]
    assert data1["was_substituted"] is True
    assert data1["medication_id"] == actors["med_generic"].id
    assert data1["substitution_type"] == "G"
    assert data1["substitution_reason"] == "Formulary tier-1 generic equivalent supplied"

    # 2. Forbidden substitution: rx_no_sub strictly disallows substitution
    forbidden_payload = {
        "prescription_id": actors["rx_no_sub"].id,
        "medication_id": actors["med_generic"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "was_substituted": True,
        "lot_number": "LOT-GEN-FAIL",
    }
    resp2 = await client.post(
        f"/api/v1/prescriptions/{actors['rx_no_sub'].id}/dispense",
        json=forbidden_payload,
        headers=headers,
    )
    assert resp2.status_code == 400
    assert "substitution is strictly prohibited" in resp2.json()["message"]


@pytest.mark.asyncio
async def test_export_medication_dispense_fhir_endpoint(dispense_test_env):
    """Test retrieval and validation of HL7 FHIR Release 4 MedicationDispense JSON."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    headers = auth_header_for(actors["pharmacist_user"])
    dispense_payload = {
        "prescription_id": actors["rx_signed"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "days_supply": 30,
        "lot_number": "LOT-FHIR-01",
        "expiration_date": "2027-08-31",
        "dosage_instruction": "Take 1 tablet daily at bedtime",
    }

    create_resp = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=dispense_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    dispense_id = create_resp.json()["data"]["id"]

    # Export as FHIR R4
    fhir_resp = await client.get(
        f"/api/v1/dispensations/{dispense_id}/fhir",
        headers=headers,
    )
    assert fhir_resp.status_code == 200, fhir_resp.text
    fhir_data = fhir_resp.json()

    assert fhir_data["resourceType"] == "MedicationDispense"
    assert fhir_data["id"] == dispense_id
    assert fhir_data["status"] == "completed"
    assert "https://nrces.in/ndhm/fhir/r4/StructureDefinition/MedicationDispense" in fhir_data["meta"]["profile"]
    assert fhir_data["authorizingPrescription"][0]["reference"] == f"MedicationRequest/{actors['rx_signed'].id}"
    assert fhir_data["subject"]["reference"] == f"Patient/{actors['patient_profile'].id}"
    assert fhir_data["quantity"]["value"] == 30.0
    assert fhir_data["lotNumber"] == "LOT-FHIR-01"
    assert fhir_data["expirationDate"] == "2027-08-31"


@pytest.mark.asyncio
async def test_list_dispensations_and_filters(dispense_test_env):
    """Test listing dispensations with patient, prescription, and lot number query filters."""
    client, session_factory = dispense_test_env
    actors = await seed_dispense_actors(session_factory)

    headers = auth_header_for(actors["pharmacist_user"])
    p1 = {
        "prescription_id": actors["rx_signed"].id,
        "quantity_dispensed": 30.0,
        "dispense_unit": "tablets",
        "lot_number": "BATCH-ALPHA-01",
    }
    await client.post(f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense", json=p1, headers=headers)

    # 1. Query by prescription
    list_rx = await client.get(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispensations",
        headers=headers,
    )
    assert list_rx.status_code == 200
    assert list_rx.json()["pagination"]["total_count"] == 1

    # 2. Query by lot_number substring
    list_lot = await client.get(
        "/api/v1/dispensations?lot_number=ALPHA",
        headers=headers,
    )
    assert list_lot.status_code == 200
    assert list_lot.json()["pagination"]["total_count"] == 1
    assert list_lot.json()["data"][0]["lot_number"] == "BATCH-ALPHA-01"

    # 3. Patient role access control
    pat_headers = auth_header_for(actors["patient_user"])
    pat_list = await client.get(
        "/api/v1/dispensations",
        headers=pat_headers,
    )
    assert pat_list.status_code == 200
    assert len(pat_list.json()["data"]) == 1

    # Patient cannot dispense (HTTP 403)
    patient_attempt = await client.post(
        f"/api/v1/prescriptions/{actors['rx_signed'].id}/dispense",
        json=p1,
        headers=pat_headers,
    )
    assert patient_attempt.status_code == 403
