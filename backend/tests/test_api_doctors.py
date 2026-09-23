"""Integration test suite for Doctor EMR API endpoints, clinical queries, and RBAC guards."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import MedicalSpecialty, UserRole
from app.models.user import User


@pytest_asyncio.fixture
async def doctor_api_client():
    """Provide an isolated in-memory test database and client for doctor API tests."""
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
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac, session_factory

    app.dependency_overrides.pop(get_db, None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def auth_header_for(user: User) -> dict:
    """Generate authorization bearer headers for a given user model."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_unauthenticated_requests_fail(doctor_api_client) -> None:
    """Verify unauthenticated requests to doctor endpoints yield 401."""
    client, _ = doctor_api_client

    for ep in ["/api/v1/doctors/", "/api/v1/doctors/some-id", "/api/v1/doctors/by-hpr/test@hpr.abdm"]:
        res = await client.get(ep)
        assert res.status_code == 401
        assert res.json()["error_code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_patient_cannot_onboard_as_doctor(doctor_api_client) -> None:
    """Verify a user with PATIENT role is rejected from registering as a healthcare practitioner."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        patient = User(
            email="patient.actor@example.com",
            full_name="Patient Actor",
            role=UserRole.PATIENT,
            is_active=True,
        )
        session.add(patient)
        await session.commit()
        patient_id = patient.id

    payload = {
        "user_id": patient_id,
        "registration_number": "MED-FAKE-001",
        "medical_council": "KMC",
        "qualifications": "None",
    }
    res = await client.post("/api/v1/doctors/", json=payload, headers=auth_header_for(patient))
    assert res.status_code == 403
    assert res.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_doctor_create_profile_success(doctor_api_client) -> None:
    """Verify DOCTOR persona can onboard clinical credentials and link ABDM HPR identifier."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        doctor_user = User(
            email="dr.kavita@nirmaya.health",
            full_name="Dr. Kavita Rao",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        session.add(doctor_user)
        await session.commit()
        doc_user_id = doctor_user.id

    headers = auth_header_for(doctor_user)
    payload = {
        "user_id": doc_user_id,
        "registration_number": "KMC-2018-77621",
        "medical_council": "Karnataka Medical Council",
        "specialty": MedicalSpecialty.PEDIATRICS.value,
        "qualifications": "MBBS, MD (Pediatrics)",
        "experience_years": 7,
        "consultation_fee": 750,
        "hospital_affiliation": "Cloudnine Hospital, Jayanagar",
        "bio": "Specialized in neonatology and general pediatrics.",
        "is_available_for_teleconsult": True,
        "hpr_id": "dr.kavita.rao@hpr.abdm",
    }

    res = await client.post("/api/v1/doctors/", json=payload, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["registration_number"] == "KMC-2018-77621"
    assert body["data"]["specialty"] == MedicalSpecialty.PEDIATRICS.value
    assert body["data"]["consultation_fee"] == 750
    assert body["data"]["hpr_id"] == "dr.kavita.rao@hpr.abdm"
    assert body["data"]["user"]["email"] == "dr.kavita@nirmaya.health"


@pytest.mark.asyncio
async def test_duplicate_profile_and_unique_constraints(doctor_api_client) -> None:
    """Verify 409 Conflict for duplicate doctor profile, duplicate registration number, and duplicate HPR ID."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        d1_user = User(email="d1@h.org", full_name="D1", role=UserRole.DOCTOR, is_active=True)
        d2_user = User(email="d2@h.org", full_name="D2", role=UserRole.DOCTOR, is_active=True)
        session.add_all([d1_user, d2_user])
        await session.commit()

    h1 = auth_header_for(d1_user)
    h2 = auth_header_for(d2_user)

    # First doctor creates profile
    p1 = {
        "user_id": d1_user.id,
        "registration_number": "MCI-UNIQUE-101",
        "medical_council": "DMC",
        "qualifications": "MBBS",
        "hpr_id": "dr.unique@hpr.abdm",
    }
    res1 = await client.post("/api/v1/doctors/", json=p1, headers=h1)
    assert res1.status_code == 201

    # 1. Same user tries creating second doctor profile
    res_dup_user = await client.post("/api/v1/doctors/", json=p1, headers=h1)
    assert res_dup_user.status_code == 409
    assert res_dup_user.json()["error_code"] == "PROFILE_ALREADY_EXISTS"

    # 2. Second doctor tries duplicate registration number
    p2_bad_reg = {
        "user_id": d2_user.id,
        "registration_number": "MCI-UNIQUE-101",
        "medical_council": "DMC",
        "qualifications": "MS",
    }
    res_dup_reg = await client.post("/api/v1/doctors/", json=p2_bad_reg, headers=h2)
    assert res_dup_reg.status_code == 409
    assert res_dup_reg.json()["error_code"] == "DUPLICATE_REGISTRATION_NUMBER"

    # 3. Second doctor tries duplicate HPR ID
    p2_bad_hpr = {
        "user_id": d2_user.id,
        "registration_number": "MCI-OTHER-202",
        "medical_council": "DMC",
        "qualifications": "MS",
        "hpr_id": "dr.unique@hpr.abdm",
    }
    res_dup_hpr = await client.post("/api/v1/doctors/", json=p2_bad_hpr, headers=h2)
    assert res_dup_hpr.status_code == 409
    assert res_dup_hpr.json()["error_code"] == "DUPLICATE_HPR_ID"


@pytest.mark.asyncio
async def test_get_doctor_by_id_and_not_found(doctor_api_client) -> None:
    """Verify GET /api/v1/doctors/{id} retrieval and 404 handling."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        doc_user = User(email="get.doc@h.org", full_name="Get Doc", role=UserRole.DOCTOR, is_active=True)
        session.add(doc_user)
        await session.commit()

    headers = auth_header_for(doc_user)
    create_res = await client.post(
        "/api/v1/doctors/",
        json={"user_id": doc_user.id, "registration_number": "REG-GET-1", "medical_council": "KMC", "qualifications": "MD"},
        headers=headers,
    )
    doctor_id = create_res.json()["data"]["id"]

    # Successful fetch
    get_res = await client.get(f"/api/v1/doctors/{doctor_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == doctor_id
    assert get_res.json()["data"]["registration_number"] == "REG-GET-1"

    # Missing UUID
    missing_res = await client.get("/api/v1/doctors/00000000-0000-0000-0000-000000000000", headers=headers)
    assert missing_res.status_code == 404
    assert missing_res.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_doctor_by_hpr_and_reg(doctor_api_client) -> None:
    """Verify resolving doctor via ABDM HPR handle and Medical Council license."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        doc_user = User(email="resolve.doc@h.org", full_name="Resolve Doc", role=UserRole.DOCTOR, is_active=True)
        session.add(doc_user)
        await session.commit()

    headers = auth_header_for(doc_user)
    await client.post(
        "/api/v1/doctors/",
        json={
            "user_id": doc_user.id,
            "registration_number": "REG-RES-99",
            "medical_council": "MMC",
            "qualifications": "MBBS",
            "hpr_id": "dr.resolve@hpr.abdm",
        },
        headers=headers,
    )

    # 1. By HPR ID
    res_hpr = await client.get("/api/v1/doctors/by-hpr/dr.resolve@hpr.abdm", headers=headers)
    assert res_hpr.status_code == 200
    assert res_hpr.json()["data"]["registration_number"] == "REG-RES-99"

    # 404 for unknown HPR ID
    res_hpr_404 = await client.get("/api/v1/doctors/by-hpr/unknown@hpr.abdm", headers=headers)
    assert res_hpr_404.status_code == 404

    # 2. By Registration Number
    res_reg = await client.get("/api/v1/doctors/by-reg/REG-RES-99", headers=headers)
    assert res_reg.status_code == 200
    assert res_reg.json()["data"]["hpr_id"] == "dr.resolve@hpr.abdm"

    # 404 for unknown Registration Number
    res_reg_404 = await client.get("/api/v1/doctors/by-reg/UNKNOWN-REG", headers=headers)
    assert res_reg_404.status_code == 404


@pytest.mark.asyncio
async def test_list_doctors_pagination_and_filters(doctor_api_client) -> None:
    """Verify GET /api/v1/doctors/ pagination, search query, and clinical filters."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        u1 = User(email="d_card@h.org", full_name="Dr. Priya Patel", role=UserRole.DOCTOR, is_active=True)
        u2 = User(email="d_ortho@h.org", full_name="Dr. Vikram Roy", role=UserRole.DOCTOR, is_active=True)
        u3 = User(email="d_neuro@h.org", full_name="Dr. Anita Rao", role=UserRole.DOCTOR, is_active=True)
        patient_caller = User(email="patient.search@h.org", full_name="Patient Searcher", role=UserRole.PATIENT, is_active=True)
        session.add_all([u1, u2, u3, patient_caller])
        await session.commit()

    # Patient can search directory
    caller_headers = auth_header_for(patient_caller)

    await client.post(
        "/api/v1/doctors/",
        json={
            "user_id": u1.id,
            "registration_number": "R-100",
            "medical_council": "KMC",
            "specialty": MedicalSpecialty.CARDIOLOGY.value,
            "qualifications": "MD",
            "consultation_fee": 1200,
            "hospital_affiliation": "Manipal Whitefield",
            "is_available_for_teleconsult": True,
        },
        headers=auth_header_for(u1),
    )
    await client.post(
        "/api/v1/doctors/",
        json={
            "user_id": u2.id,
            "registration_number": "R-200",
            "medical_council": "KMC",
            "specialty": MedicalSpecialty.ORTHOPEDICS.value,
            "qualifications": "MS",
            "consultation_fee": 800,
            "hospital_affiliation": "Aster CMI",
            "is_available_for_teleconsult": False,
        },
        headers=auth_header_for(u2),
    )
    await client.post(
        "/api/v1/doctors/",
        json={
            "user_id": u3.id,
            "registration_number": "R-300",
            "medical_council": "KMC",
            "specialty": MedicalSpecialty.NEUROLOGY.value,
            "qualifications": "DM",
            "consultation_fee": 600,
            "hospital_affiliation": "NIMHANS",
            "is_available_for_teleconsult": True,
        },
        headers=auth_header_for(u3),
    )

    # 1. Pagination: limit 2
    res_p1 = await client.get("/api/v1/doctors/?page=1&limit=2", headers=caller_headers)
    assert res_p1.status_code == 200
    b1 = res_p1.json()
    assert len(b1["data"]) == 2
    assert b1["pagination"]["total_count"] == 3
    assert b1["pagination"]["total_pages"] == 2
    assert b1["pagination"]["has_next"] is True

    # 2. Filter by specialty
    res_spec = await client.get(f"/api/v1/doctors/?specialty={MedicalSpecialty.CARDIOLOGY.value}", headers=caller_headers)
    assert res_spec.status_code == 200
    assert res_spec.json()["pagination"]["total_count"] == 1
    assert res_spec.json()["data"][0]["specialty"] == MedicalSpecialty.CARDIOLOGY.value

    # 3. Filter by teleconsult
    res_tele = await client.get("/api/v1/doctors/?teleconsult_only=true", headers=caller_headers)
    assert res_tele.status_code == 200
    assert res_tele.json()["pagination"]["total_count"] == 2

    # 4. Filter by max_fee
    res_fee = await client.get("/api/v1/doctors/?max_fee=800", headers=caller_headers)
    assert res_fee.status_code == 200
    assert res_fee.json()["pagination"]["total_count"] == 2

    # 5. Search query
    res_q = await client.get("/api/v1/doctors/?query=NIMHANS", headers=caller_headers)
    assert res_q.status_code == 200
    assert res_q.json()["pagination"]["total_count"] == 1
    assert res_q.json()["data"][0]["hospital_affiliation"] == "NIMHANS"


@pytest.mark.asyncio
async def test_update_doctor_profile_ownership_guard(doctor_api_client) -> None:
    """Verify doctor profile update is permitted only for owner or administrator."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        d_owner = User(email="owner.doc@h.org", full_name="Owner Doc", role=UserRole.DOCTOR, is_active=True)
        d_other = User(email="other.doc@h.org", full_name="Other Doc", role=UserRole.DOCTOR, is_active=True)
        admin = User(email="admin.doc@h.org", full_name="Admin Doc", role=UserRole.ADMIN, is_active=True)
        session.add_all([d_owner, d_other, admin])
        await session.commit()

    create_res = await client.post(
        "/api/v1/doctors/",
        json={"user_id": d_owner.id, "registration_number": "REG-OWNER", "medical_council": "KMC", "qualifications": "MBBS", "consultation_fee": 500},
        headers=auth_header_for(d_owner),
    )
    doctor_id = create_res.json()["data"]["id"]

    # 1. Other doctor tries to update -> 403 Forbidden
    unauth_res = await client.put(
        f"/api/v1/doctors/{doctor_id}",
        json={"consultation_fee": 2000},
        headers=auth_header_for(d_other),
    )
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error_code"] == "FORBIDDEN"

    # 2. Owner updates -> 200 OK
    owner_res = await client.put(
        f"/api/v1/doctors/{doctor_id}",
        json={"consultation_fee": 900, "bio": "Consultant pediatrician"},
        headers=auth_header_for(d_owner),
    )
    assert owner_res.status_code == 200
    assert owner_res.json()["data"]["consultation_fee"] == 900
    assert owner_res.json()["data"]["bio"] == "Consultant pediatrician"

    # 3. Admin updates -> 200 OK (admin override)
    admin_res = await client.put(
        f"/api/v1/doctors/{doctor_id}",
        json={"hospital_affiliation": "Manipal Central"},
        headers=auth_header_for(admin),
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["data"]["hospital_affiliation"] == "Manipal Central"


@pytest.mark.asyncio
async def test_delete_doctor_profile_ownership_guard(doctor_api_client) -> None:
    """Verify doctor profile deletion is permitted only for owner or administrator."""
    client, session_factory = doctor_api_client

    async with session_factory() as session:
        d_owner = User(email="del.owner@h.org", full_name="Del Owner", role=UserRole.DOCTOR, is_active=True)
        d_other = User(email="del.other@h.org", full_name="Del Other", role=UserRole.DOCTOR, is_active=True)
        session.add_all([d_owner, d_other])
        await session.commit()

    create_res = await client.post(
        "/api/v1/doctors/",
        json={"user_id": d_owner.id, "registration_number": "REG-DEL-01", "medical_council": "KMC", "qualifications": "MBBS"},
        headers=auth_header_for(d_owner),
    )
    doctor_id = create_res.json()["data"]["id"]

    # 1. Other doctor tries delete -> 403 Forbidden
    unauth_del = await client.delete(f"/api/v1/doctors/{doctor_id}", headers=auth_header_for(d_other))
    assert unauth_del.status_code == 403

    # 2. Owner deletes -> 200 OK
    owner_del = await client.delete(f"/api/v1/doctors/{doctor_id}", headers=auth_header_for(d_owner))
    assert owner_del.status_code == 200
    assert owner_del.json()["data"]["deleted"] is True

    # Subsequent fetch is 404
    fetch_del = await client.get(f"/api/v1/doctors/{doctor_id}", headers=auth_header_for(d_owner))
    assert fetch_del.status_code == 404
