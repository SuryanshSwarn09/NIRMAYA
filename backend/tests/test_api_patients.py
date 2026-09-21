"""Integration tests for Patient Vault API endpoints with RBAC and session security."""

from datetime import date
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import BloodGroup, Gender, UserRole
from app.models.user import User


@pytest_asyncio.fixture
async def patient_api_client():
    """Provide an isolated in-memory test database and client for patient API tests."""
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
    """Generate authorization headers for a given user model."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_patient_profile_success(patient_api_client) -> None:
    """Verify POST /api/v1/patients/ creates a patient profile with full demographics and ABHA."""
    client, session_factory = patient_api_client

    # Seed a target patient user
    async with session_factory() as session:
        user = User(
            email="arun.test@example.com",
            full_name="Arun Test",
            role=UserRole.PATIENT,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)

    payload = {
        "user_id": user_id,
        "date_of_birth": "1990-05-15",
        "gender": "male",
        "blood_group": "B+",
        "address_line": "123 MG Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
        "emergency_contact_name": "Kavita Test",
        "emergency_contact_phone": "+919876543210",
        "emergency_contact_relation": "Spouse",
        "abha_number": "91-1234-5678-9012",
        "abha_address": "arun.test@abdm",
    }

    # Unauthenticated attempt fails with 401
    unauth_res = await client.post("/api/v1/patients/", json=payload)
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error_code"] == "AUTHENTICATION_REQUIRED"

    # Authenticated creation succeeds
    res = await client.post("/api/v1/patients/", json=payload, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == user_id
    assert body["data"]["abha_number"] == "91-1234-5678-9012"
    assert body["data"]["abha_address"] == "arun.test@abdm"
    assert body["data"]["user"]["email"] == "arun.test@example.com"


@pytest.mark.asyncio
async def test_create_patient_duplicate_profile_rejection(patient_api_client) -> None:
    """Verify creating a second profile for the same user is rejected with 409 Conflict."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        user = User(
            email="dup.user@example.com",
            full_name="Dup User",
            role=UserRole.PATIENT,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)

    payload = {
        "user_id": user_id,
        "gender": "female",
        "abha_address": "dup1@abdm",
    }
    res1 = await client.post("/api/v1/patients/", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second attempt
    payload2 = {
        "user_id": user_id,
        "gender": "female",
        "abha_address": "dup2@abdm",
    }
    res2 = await client.post("/api/v1/patients/", json=payload2, headers=headers)
    assert res2.status_code == 409
    body2 = res2.json()
    assert body2["success"] is False
    assert body2["error_code"] == "PROFILE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_patient_duplicate_abha_rejection(patient_api_client) -> None:
    """Verify reusing an existing ABHA number is rejected with 409 Conflict."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        u1 = User(email="user1@example.com", full_name="User One", role=UserRole.PATIENT, is_active=True)
        u2 = User(email="user2@example.com", full_name="User Two", role=UserRole.PATIENT, is_active=True)
        session.add_all([u1, u2])
        await session.commit()
        u1_id, u2_id = u1.id, u2.id

    res1 = await client.post(
        "/api/v1/patients/",
        json={"user_id": u1_id, "abha_number": "11-2222-3333-4444"},
        headers=auth_header_for(u1),
    )
    assert res1.status_code == 201

    res2 = await client.post(
        "/api/v1/patients/",
        json={"user_id": u2_id, "abha_number": "11-2222-3333-4444"},
        headers=auth_header_for(u2),
    )
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "DUPLICATE_ABHA_NUMBER"


@pytest.mark.asyncio
async def test_get_patient_by_id_and_not_found(patient_api_client) -> None:
    """Verify GET /api/v1/patients/{id} retrieval, ownership guard, and 404 handling."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        user = User(email="lookup@example.com", full_name="Lookup User", role=UserRole.PATIENT, is_active=True)
        other_user = User(email="other@example.com", full_name="Other User", role=UserRole.PATIENT, is_active=True)
        session.add_all([user, other_user])
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)
    other_headers = auth_header_for(other_user)

    create_res = await client.post(
        "/api/v1/patients/",
        json={"user_id": user_id, "city": "Kochi", "abha_address": "lookup@abdm"},
        headers=headers,
    )
    patient_id = create_res.json()["data"]["id"]

    # Successful fetch by owner
    get_res = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == patient_id
    assert get_res.json()["data"]["city"] == "Kochi"

    # Unauthorized fetch by unrelated patient returns 403
    forbidden_res = await client.get(f"/api/v1/patients/{patient_id}", headers=other_headers)
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error_code"] == "FORBIDDEN"

    # Non-existent ID fetch returns 404
    missing_res = await client.get(
        "/api/v1/patients/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert missing_res.status_code == 404
    assert missing_res.json()["success"] is False
    assert missing_res.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_patient_by_abha_identifier(patient_api_client) -> None:
    """Verify GET /api/v1/patients/by-abha/{identifier} resolves via ABHA ID or @abdm handle."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        user = User(email="abha.patient@example.com", full_name="ABHA Patient", role=UserRole.PATIENT, is_active=True)
        doc = User(email="dr.abha@example.com", full_name="Dr. ABHA", role=UserRole.DOCTOR, is_active=True)
        session.add_all([user, doc])
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)
    doc_headers = auth_header_for(doc)

    await client.post(
        "/api/v1/patients/",
        json={
            "user_id": user_id,
            "abha_number": "91-9999-8888-7777",
            "abha_address": "abha.user@abdm",
        },
        headers=headers,
    )

    # Lookup by 14-digit number by doctor
    res_num = await client.get("/api/v1/patients/by-abha/91-9999-8888-7777", headers=doc_headers)
    assert res_num.status_code == 200
    assert res_num.json()["data"]["abha_address"] == "abha.user@abdm"

    # Lookup by @abdm handle by patient owner
    res_handle = await client.get("/api/v1/patients/by-abha/abha.user@abdm", headers=headers)
    assert res_handle.status_code == 200
    assert res_handle.json()["data"]["abha_number"] == "91-9999-8888-7777"

    # Lookup non-existent returns 404
    res_none = await client.get("/api/v1/patients/by-abha/nonexistent@abdm", headers=doc_headers)
    assert res_none.status_code == 404


@pytest.mark.asyncio
async def test_list_patients_pagination_and_filtering(patient_api_client) -> None:
    """Verify GET /api/v1/patients/ handles clinical staff authorization, pagination, and filters."""
    client, session_factory = patient_api_client

    # Seed 3 distinct patients and 1 doctor
    async with session_factory() as session:
        u1 = User(email="p1@example.com", full_name="Ananya Roy", role=UserRole.PATIENT, is_active=True)
        u2 = User(email="p2@example.com", full_name="Rahul Varma", role=UserRole.PATIENT, is_active=True)
        u3 = User(email="p3@example.com", full_name="Sunita Deshmukh", role=UserRole.PATIENT, is_active=True)
        doc = User(email="doc.dir@example.com", full_name="Dr. Director", role=UserRole.DOCTOR, is_active=True)
        session.add_all([u1, u2, u3, doc])
        await session.commit()
        u1_id, u2_id, u3_id = u1.id, u2.id, u3.id

    await client.post(
        "/api/v1/patients/",
        json={"user_id": u1_id, "city": "Kolkata", "blood_group": "A+", "abha_address": "ananya@abdm"},
        headers=auth_header_for(u1),
    )
    await client.post(
        "/api/v1/patients/",
        json={"user_id": u2_id, "city": "Pune", "blood_group": "B+", "abha_address": "rahul@abdm"},
        headers=auth_header_for(u2),
    )
    await client.post(
        "/api/v1/patients/",
        json={"user_id": u3_id, "city": "Pune", "blood_group": "O+", "abha_address": "sunita@abdm"},
        headers=auth_header_for(u3),
    )

    # 1. Non-clinical patient attempting directory listing receives 403 Forbidden
    patient_res = await client.get("/api/v1/patients/", headers=auth_header_for(u1))
    assert patient_res.status_code == 403
    assert patient_res.json()["error_code"] == "FORBIDDEN"

    doc_headers = auth_header_for(doc)

    # 2. Doctor pagination: Page 1 with limit 2
    res_p1 = await client.get("/api/v1/patients/?page=1&limit=2", headers=doc_headers)
    assert res_p1.status_code == 200
    body_p1 = res_p1.json()
    assert len(body_p1["data"]) == 2
    assert body_p1["pagination"]["total_count"] == 3
    assert body_p1["pagination"]["page"] == 1
    assert body_p1["pagination"]["total_pages"] == 2
    assert body_p1["pagination"]["has_next"] is True
    assert body_p1["pagination"]["has_prev"] is False

    # 3. Pagination: Page 2
    res_p2 = await client.get("/api/v1/patients/?page=2&limit=2", headers=doc_headers)
    assert res_p2.status_code == 200
    body_p2 = res_p2.json()
    assert len(body_p2["data"]) == 1
    assert body_p2["pagination"]["has_next"] is False
    assert body_p2["pagination"]["has_prev"] is True

    # 4. Filter by City
    res_city = await client.get("/api/v1/patients/?city=Pune", headers=doc_headers)
    assert res_city.status_code == 200
    assert res_city.json()["pagination"]["total_count"] == 2

    # 5. Filter by Blood Group
    res_bg = await client.get("/api/v1/patients/", params={"blood_group": "A+"}, headers=doc_headers)
    assert res_bg.status_code == 200
    assert res_bg.json()["pagination"]["total_count"] == 1

    # 6. Search Query
    res_q = await client.get("/api/v1/patients/?query=Ananya", headers=doc_headers)
    assert res_q.status_code == 200
    assert res_q.json()["pagination"]["total_count"] == 1
    assert res_q.json()["data"][0]["user"]["full_name"] == "Ananya Roy"


@pytest.mark.asyncio
async def test_update_patient_profile(patient_api_client) -> None:
    """Verify PUT /api/v1/patients/{id} updates fields and guards non-owner modifications."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        user = User(email="update.me@example.com", full_name="Update User", role=UserRole.PATIENT, is_active=True)
        other_user = User(email="other.upd@example.com", full_name="Other Upd", role=UserRole.PATIENT, is_active=True)
        session.add_all([user, other_user])
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)

    create_res = await client.post(
        "/api/v1/patients/",
        json={"user_id": user_id, "city": "Bengaluru", "pincode": "560001", "abha_address": "orig@abdm"},
        headers=headers,
    )
    patient_id = create_res.json()["data"]["id"]

    update_payload = {
        "city": "Mysuru",
        "pincode": "570001",
        "emergency_contact_name": "Ravi Update",
        "emergency_contact_phone": "+919900112233",
    }

    # Unauthorized patient update attempt returns 403
    unauth_upd = await client.put(
        f"/api/v1/patients/{patient_id}",
        json=update_payload,
        headers=auth_header_for(other_user),
    )
    assert unauth_upd.status_code == 403
    assert unauth_upd.json()["error_code"] == "FORBIDDEN"

    # Owner update succeeds
    update_res = await client.put(
        f"/api/v1/patients/{patient_id}",
        json=update_payload,
        headers=headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()["data"]
    assert data["city"] == "Mysuru"
    assert data["pincode"] == "570001"
    assert data["emergency_contact_name"] == "Ravi Update"
    assert data["abha_address"] == "orig@abdm"


@pytest.mark.asyncio
async def test_delete_patient_profile(patient_api_client) -> None:
    """Verify DELETE /api/v1/patients/{id} removes profile enforcing owner or admin privileges."""
    client, session_factory = patient_api_client

    async with session_factory() as session:
        user = User(email="del.patient@example.com", full_name="Delete Patient", role=UserRole.PATIENT, is_active=True)
        other_user = User(email="other.del@example.com", full_name="Other Del", role=UserRole.PATIENT, is_active=True)
        session.add_all([user, other_user])
        await session.commit()
        user_id = user.id

    headers = auth_header_for(user)

    create_res = await client.post(
        "/api/v1/patients/",
        json={"user_id": user_id, "abha_address": "del.me@abdm"},
        headers=headers,
    )
    patient_id = create_res.json()["data"]["id"]

    # Unauthorized delete attempt returns 403
    unauth_del = await client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=auth_header_for(other_user),
    )
    assert unauth_del.status_code == 403
    assert unauth_del.json()["error_code"] == "FORBIDDEN"

    # Owner delete succeeds
    del_res = await client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
    assert del_res.json()["data"]["deleted"] is True

    # Subsequent GET returns 404
    fetch_res = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert fetch_res.status_code == 404
