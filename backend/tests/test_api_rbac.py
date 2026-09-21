"""Integration test suite for RBAC endpoints, role boundary enforcement, and 403 Forbidden responses."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User


@pytest_asyncio.fixture
async def rbac_test_env():
    """Set up isolated in-memory test database, test users across all 4 roles, and test client."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    users = {
        UserRole.PATIENT: User(
            id="usr-pat-rbac",
            email="patient.rbac@nirmaya.health",
            full_name="Patient Persona",
            role=UserRole.PATIENT,
            supabase_uid="sb-pat-rbac",
            is_active=True,
            is_verified=True,
        ),
        UserRole.DOCTOR: User(
            id="usr-doc-rbac",
            email="doctor.rbac@nirmaya.health",
            full_name="Doctor Persona",
            role=UserRole.DOCTOR,
            supabase_uid="sb-doc-rbac",
            is_active=True,
            is_verified=True,
        ),
        UserRole.LAB: User(
            id="usr-lab-rbac",
            email="lab.rbac@nirmaya.health",
            full_name="Lab Persona",
            role=UserRole.LAB,
            supabase_uid="sb-lab-rbac",
            is_active=True,
            is_verified=True,
        ),
        UserRole.ADMIN: User(
            id="usr-adm-rbac",
            email="admin.rbac@nirmaya.health",
            full_name="Admin Persona",
            role=UserRole.ADMIN,
            supabase_uid="sb-adm-rbac",
            is_active=True,
            is_verified=True,
        ),
    }

    async with session_factory() as session:
        for u in users.values():
            session.add(u)
        await session.commit()

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
        yield ac, users

    app.dependency_overrides.pop(get_db, None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def make_headers(user: User) -> dict:
    """Generate authorization headers for a given user."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_unauthenticated_requests_fail(rbac_test_env) -> None:
    """Verify accessing role-guarded endpoints without token yields 401."""
    client, _ = rbac_test_env
    endpoints = [
        "/api/v1/auth/roles/patient-only",
        "/api/v1/auth/roles/doctor-only",
        "/api/v1/auth/roles/lab-only",
        "/api/v1/auth/roles/admin-only",
        "/api/v1/auth/roles/clinical-staff-only",
    ]
    for ep in endpoints:
        res = await client.get(ep)
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error_code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_patient_role_permissions(rbac_test_env) -> None:
    """Verify Patient can access patient endpoint, but is blocked from doctor, lab, admin, clinical staff."""
    client, users = rbac_test_env
    headers = make_headers(users[UserRole.PATIENT])

    # Patient endpoint: 200 OK
    res_patient = await client.get("/api/v1/auth/roles/patient-only", headers=headers)
    assert res_patient.status_code == 200
    assert res_patient.json()["data"]["role"] == "patient"

    # Blocked endpoints: 403 FORBIDDEN
    for ep in [
        "/api/v1/auth/roles/doctor-only",
        "/api/v1/auth/roles/lab-only",
        "/api/v1/auth/roles/admin-only",
        "/api/v1/auth/roles/clinical-staff-only",
    ]:
        res = await client.get(ep, headers=headers)
        assert res.status_code == 403
        assert res.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_doctor_role_permissions(rbac_test_env) -> None:
    """Verify Doctor can access doctor and clinical staff endpoints, but not patient, lab, or admin."""
    client, users = rbac_test_env
    headers = make_headers(users[UserRole.DOCTOR])

    # Permitted endpoints: 200 OK
    res_doc = await client.get("/api/v1/auth/roles/doctor-only", headers=headers)
    assert res_doc.status_code == 200
    assert res_doc.json()["data"]["role"] == "doctor"

    res_staff = await client.get("/api/v1/auth/roles/clinical-staff-only", headers=headers)
    assert res_staff.status_code == 200

    # Blocked endpoints: 403 FORBIDDEN
    for ep in [
        "/api/v1/auth/roles/patient-only",
        "/api/v1/auth/roles/lab-only",
        "/api/v1/auth/roles/admin-only",
    ]:
        res = await client.get(ep, headers=headers)
        assert res.status_code == 403
        assert res.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_lab_role_permissions(rbac_test_env) -> None:
    """Verify Lab can access lab and clinical staff endpoints, but not patient, doctor, or admin."""
    client, users = rbac_test_env
    headers = make_headers(users[UserRole.LAB])

    # Permitted endpoints: 200 OK
    res_lab = await client.get("/api/v1/auth/roles/lab-only", headers=headers)
    assert res_lab.status_code == 200
    assert res_lab.json()["data"]["role"] == "lab"

    res_staff = await client.get("/api/v1/auth/roles/clinical-staff-only", headers=headers)
    assert res_staff.status_code == 200

    # Blocked endpoints: 403 FORBIDDEN
    for ep in [
        "/api/v1/auth/roles/patient-only",
        "/api/v1/auth/roles/doctor-only",
        "/api/v1/auth/roles/admin-only",
    ]:
        res = await client.get(ep, headers=headers)
        assert res.status_code == 403
        assert res.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_superuser_override_across_all_endpoints(rbac_test_env) -> None:
    """Verify Administrator role possesses superuser bypass for every single protected endpoint."""
    client, users = rbac_test_env
    headers = make_headers(users[UserRole.ADMIN])

    endpoints = [
        "/api/v1/auth/roles/patient-only",
        "/api/v1/auth/roles/doctor-only",
        "/api/v1/auth/roles/lab-only",
        "/api/v1/auth/roles/admin-only",
        "/api/v1/auth/roles/clinical-staff-only",
    ]
    for ep in endpoints:
        res = await client.get(ep, headers=headers)
        assert res.status_code == 200
        assert res.json()["data"]["role"] == "admin"
