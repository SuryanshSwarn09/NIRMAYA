"""Comprehensive unit and integration test suite for the Medication Catalog and Formulary Engine.

Validates:
1. Seeding and idempotency of standard clinical formulary (30 essential drugs).
2. Multi-parameter search (name, generic, brand, RxCUI, active ingredient).
3. Clinical filtering by WHO-ATC therapeutic category prefix, dosage form, and formulary tier.
4. Legal classification filtering (prescription required, controlled substance).
5. Retrieval by UUID and by RxNorm CUI code.
6. HL7 FHIR Release 4 Medication resource serialization and NRCeS profile conformance.
7. WHO-ATC therapeutic classification summaries and aggregate counts.
8. RBAC security enforcement (Doctor/Admin write, Patient read-only).
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import (
    AdministrationRoute,
    FormularyTier,
    MedicationForm,
    MedicationStatus,
    UserRole,
)
from app.models.medication import Medication
from app.models.user import User
from app.services.medication import seed_medications_if_empty


@pytest_asyncio.fixture
async def medication_test_env():
    """Provide isolated in-memory SQLite database and HTTP client for medication tests."""
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
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


def auth_header_for(user: User) -> dict:
    """Generate JWT authorization bearer header for user."""
    token = create_access_token({"sub": user.id, "role": user.role.value, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


async def seed_test_users(session_factory) -> dict:
    """Create doctor, patient, and admin test users."""
    async with session_factory() as session:
        doctor_user = User(
            id="user-doc-sharma",
            email="sharma@nirmaya.health",
            full_name="Dr. Ananya Sharma",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        patient_user = User(
            id="user-pat-patel",
            email="patel@nirmaya.health",
            full_name="Arun Patel",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        admin_user = User(
            id="user-admin-root",
            email="admin@nirmaya.health",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add_all([doctor_user, patient_user, admin_user])
        await session.commit()

        # Seed initial medications
        seeded_count = await seed_medications_if_empty(session)

    return {
        "doctor_user": doctor_user,
        "patient_user": patient_user,
        "admin_user": admin_user,
        "seeded_count": seeded_count,
    }


@pytest.mark.asyncio
async def test_seed_clinical_formulary(medication_test_env) -> None:
    """Verify that clinical formulary seeds accurately and is idempotent."""
    _, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)

    assert fixture["seeded_count"] == 30

    async with session_factory() as session:
        # Idempotency check: calling again should seed 0
        second_run = await seed_medications_if_empty(session)
        assert second_run == 0


@pytest.mark.asyncio
async def test_list_medications_pagination_and_text_search(medication_test_env) -> None:
    """Verify text search across name, generic, brand, and ingredient."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    # 1. Search by name 'metformin'
    res = await client.get("/api/v1/medications?q=metformin", headers=auth_header_for(doctor))
    assert res.status_code == 200
    body = res.json()
    assert body["pagination"]["total_count"] >= 2
    for item in body["data"]:
        assert "metformin" in item["name"].lower() or "metformin" in item["generic_name"].lower()

    # 2. Search by commercial brand 'Glucophage'
    res_brand = await client.get("/api/v1/medications?q=glucophage", headers=auth_header_for(doctor))
    assert res_brand.status_code == 200
    brand_items = res_brand.json()["data"]
    assert len(brand_items) >= 2
    assert any("Glucophage" in item["brand_name"] for item in brand_items)

    # 3. Search by RxNorm CUI '617314' (Atorvastatin 20mg)
    res_cui = await client.get("/api/v1/medications?q=617314", headers=auth_header_for(doctor))
    assert res_cui.status_code == 200
    cui_items = res_cui.json()["data"]
    assert len(cui_items) == 1
    assert cui_items[0]["rxnorm_code"] == "617314"
    assert "Atorvastatin" in cui_items[0]["generic_name"]


@pytest.mark.asyncio
async def test_filter_medications_by_atc_prefix(medication_test_env) -> None:
    """Verify filtering by WHO-ATC therapeutic category prefix."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    patient = fixture["patient_user"]

    # Filter by A10 (Antidiabetics)
    res = await client.get("/api/v1/medications?atc_prefix=A10", headers=auth_header_for(patient))
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 5
    for item in items:
        assert item["atc_code"].startswith("A10")

    # Filter by J01 (Antimicrobials / Antibiotics)
    res_abx = await client.get("/api/v1/medications?atc_prefix=J01", headers=auth_header_for(patient))
    assert res_abx.status_code == 200
    abx_items = res_abx.json()["data"]
    assert len(abx_items) == 5
    for item in abx_items:
        assert item["atc_code"].startswith("J01")


@pytest.mark.asyncio
async def test_filter_medications_by_form_and_tier(medication_test_env) -> None:
    """Verify filtering by dosage form, formulary tier, and OTC legal classification."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    # 1. Filter by form = inhaler
    res_inhaler = await client.get("/api/v1/medications?form=inhaler", headers=auth_header_for(doctor))
    assert res_inhaler.status_code == 200
    inhalers = res_inhaler.json()["data"]
    assert len(inhalers) == 1
    assert inhalers[0]["name"] == "Albuterol 90 mcg/actuation Inhalation Aerosol"
    assert inhalers[0]["route"] == "inhalation"

    # 2. Filter by tier = tier_5_otc (Over-The-Counter)
    res_otc = await client.get("/api/v1/medications?tier=tier_5_otc", headers=auth_header_for(doctor))
    assert res_otc.status_code == 200
    otc_items = res_otc.json()["data"]
    assert len(otc_items) == 3  # Paracetamol, Ibuprofen, Omeprazole
    for item in otc_items:
        assert item["formulary_tier"] == "tier_5_otc"
        assert item["is_prescription_required"] is False

    # 3. Filter controlled substances
    res_controlled = await client.get("/api/v1/medications?is_controlled_substance=true", headers=auth_header_for(doctor))
    assert res_controlled.status_code == 200
    controlled = res_controlled.json()["data"]
    assert len(controlled) == 2  # Tramadol and Alprazolam
    for item in controlled:
        assert item["is_controlled_substance"] is True


@pytest.mark.asyncio
async def test_get_medication_by_id_and_rxnorm(medication_test_env) -> None:
    """Verify retrieving specific medication by UUID and by RxNorm CUI."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    # 1. Lookup by RxNorm code
    res_rx = await client.get("/api/v1/medications/860975", headers=auth_header_for(doctor))
    assert res_rx.status_code == 200
    med_data = res_rx.json()["data"]
    assert med_data["rxnorm_code"] == "860975"
    assert med_data["generic_name"] == "Metformin Hydrochloride"

    # 2. Lookup by internal UUID
    med_id = med_data["id"]
    res_id = await client.get(f"/api/v1/medications/{med_id}", headers=auth_header_for(doctor))
    assert res_id.status_code == 200
    assert res_id.json()["data"]["id"] == med_id


@pytest.mark.asyncio
async def test_get_medication_fhir_export(medication_test_env) -> None:
    """Verify GET /api/v1/medications/{id}/fhir exports valid FHIR R4 Medication resource."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    res = await client.get("/api/v1/medications/860975/fhir", headers=auth_header_for(doctor))
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True

    fhir = body["data"]
    assert fhir["resourceType"] == "Medication"
    assert fhir["status"] == "active"
    assert len(fhir["identifier"]) >= 2
    assert fhir["code"]["text"] == "Metformin 500mg Oral Tablet"

    systems = {coding["system"] for coding in fhir["code"]["coding"]}
    assert "http://www.nlm.nih.gov/research/umls/rxnorm" in systems
    assert "http://www.whocc.no/atc" in systems
    assert "http://snomed.info/sct" in systems

    assert fhir["form"]["text"] == "Tablet"
    assert len(fhir["ingredient"]) == 1
    assert fhir["ingredient"][0]["itemCodeableConcept"]["text"] == "Metformin"
    assert fhir["ingredient"][0]["strength"]["text"] == "500 mg"


@pytest.mark.asyncio
async def test_get_therapeutic_classes(medication_test_env) -> None:
    """Verify aggregate breakdown of catalog by WHO-ATC therapeutic classification."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    res = await client.get("/api/v1/medications/classes", headers=auth_header_for(doctor))
    assert res.status_code == 200
    classes = res.json()["data"]
    assert len(classes) >= 5

    prefixes = {c["atc_prefix"]: c for c in classes}
    assert "A" in prefixes  # Alimentary
    assert "C" in prefixes  # Cardiovascular
    assert "J" in prefixes  # Antiinfectives
    assert "N" in prefixes  # Nervous
    assert "R" in prefixes  # Respiratory
    assert prefixes["A"]["medication_count"] >= 5


@pytest.mark.asyncio
async def test_create_and_update_medication_authorized(medication_test_env) -> None:
    """Verify Doctor or Admin can register and update medications."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    create_payload = {
        "name": "Dapagliflozin 10mg Oral Tablet",
        "generic_name": "Dapagliflozin Propanediol",
        "brand_name": "Farxiga",
        "rxnorm_code": "1488564",
        "rxnorm_display": "Dapagliflozin 10 MG Oral Tablet",
        "atc_code": "A10BK01",
        "atc_display": "Sodium-glucose co-transporter 2 (SGLT2) inhibitors",
        "snomed_code": "703774005",
        "snomed_display": "Dapagliflozin",
        "form": "tablet",
        "route": "oral",
        "strength": "10 mg",
        "active_ingredient": "Dapagliflozin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": "tier_2_preferred_brand",
        "status": "active",
        "description": "SGLT2 inhibitor for type 2 diabetes and heart failure.",
    }

    # 1. Create drug
    res_create = await client.post(
        "/api/v1/medications",
        json=create_payload,
        headers=auth_header_for(doctor),
    )
    assert res_create.status_code == 201
    new_med = res_create.json()["data"]
    assert new_med["name"] == "Dapagliflozin 10mg Oral Tablet"
    assert new_med["rxnorm_code"] == "1488564"

    # 2. Update drug properties
    med_id = new_med["id"]
    res_update = await client.patch(
        f"/api/v1/medications/{med_id}",
        json={"formulary_tier": "tier_1_generic", "description": "Updated formulary tier to generic."},
        headers=auth_header_for(doctor),
    )
    assert res_update.status_code == 200
    updated = res_update.json()["data"]
    assert updated["formulary_tier"] == "tier_1_generic"
    assert updated["description"] == "Updated formulary tier to generic."


@pytest.mark.asyncio
async def test_create_medication_rbac_forbidden(medication_test_env) -> None:
    """Verify Patient role receives 403 Forbidden when attempting to register a drug."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    patient = fixture["patient_user"]

    payload = {
        "name": "Unauthorized Drug",
        "generic_name": "Unauthorized",
        "rxnorm_code": "999999",
        "strength": "100 mg",
        "active_ingredient": "Unauthorized",
    }
    res = await client.post("/api/v1/medications", json=payload, headers=auth_header_for(patient))
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_nonexistent_medication_404(medication_test_env) -> None:
    """Verify requesting a non-existent medication returns 404 EntityNotFound."""
    client, session_factory = medication_test_env
    fixture = await seed_test_users(session_factory)
    doctor = fixture["doctor_user"]

    res = await client.get("/api/v1/medications/non-existent-uuid", headers=auth_header_for(doctor))
    assert res.status_code == 404
