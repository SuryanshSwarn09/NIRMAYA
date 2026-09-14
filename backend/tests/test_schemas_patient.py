"""Unit tests for User and PatientProfile Pydantic v2 schemas."""

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError
from app.models.enums import BloodGroup, Gender, UserRole
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.patient import (
    PatientProfileCreate,
    PatientProfileResponse,
    PatientProfileUpdate,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate


def test_user_create_validation_success() -> None:
    """Verify valid UserCreate payload serialization."""
    payload = UserCreate(
        email="doctor.sen@hospital.org",
        full_name="Dr. Sourav Sen",
        phone_number="+919876543210",
        role=UserRole.DOCTOR,
    )
    assert payload.email == "doctor.sen@hospital.org"
    assert payload.role == UserRole.DOCTOR


def test_user_create_invalid_email_failure() -> None:
    """Verify UserCreate rejects invalid email strings."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email-address",
            full_name="Invalid User",
        )


def test_patient_profile_abha_validation_success() -> None:
    """Verify PatientProfileCreate succeeds with valid ABHA format."""
    payload = PatientProfileCreate(
        date_of_birth=date(1988, 12, 1),
        gender=Gender.FEMALE,
        blood_group=BloodGroup.A_POSITIVE,
        pincode="560034",
        abha_number="14-9876-5432-1098",
        abha_address="ananya.sharma@abdm",
    )
    assert payload.abha_number == "14-9876-5432-1098"
    assert payload.abha_address == "ananya.sharma@abdm"
    assert payload.gender == Gender.FEMALE
    assert payload.blood_group == BloodGroup.A_POSITIVE


def test_patient_profile_invalid_abha_number() -> None:
    """Verify PatientProfileCreate rejects non-standard ABHA number formats."""
    # Too few digits
    with pytest.raises(ValidationError):
        PatientProfileCreate(abha_number="12-345-678-90")

    # Missing hyphens
    with pytest.raises(ValidationError):
        PatientProfileCreate(abha_number="14987654321098")


def test_patient_profile_invalid_abha_address() -> None:
    """Verify PatientProfileCreate rejects ABHA address without @abdm namespace."""
    with pytest.raises(ValidationError):
        PatientProfileCreate(abha_address="invalid.handle@gmail.com")

    with pytest.raises(ValidationError):
        PatientProfileCreate(abha_address="just_a_handle")


def test_patient_profile_invalid_pincode() -> None:
    """Verify pincode must be a 6-digit Indian PIN code not starting with 0."""
    # 5 digits
    with pytest.raises(ValidationError):
        PatientProfileCreate(pincode="56001")

    # Starting with 0
    with pytest.raises(ValidationError):
        PatientProfileCreate(pincode="060001")


def test_patient_profile_response_from_orm() -> None:
    """Verify PatientProfileResponse serializes from SQLAlchemy ORM entities with nested User."""
    mock_user = User(
        id="user-uuid-1234-5678",
        email="patient@example.com",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_profile = PatientProfile(
        id="profile-uuid-1234-5678",
        user_id=mock_user.id,
        user=mock_user,
        gender=Gender.OTHER,
        blood_group=BloodGroup.AB_POSITIVE,
        abha_number="12-1234-1234-1234",
        abha_address="test@abdm",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response_schema = PatientProfileResponse.model_validate(mock_profile)
    assert response_schema.id == "profile-uuid-1234-5678"
    assert response_schema.user_id == "user-uuid-1234-5678"
    assert response_schema.user is not None
    assert response_schema.user.email == "patient@example.com"
    assert response_schema.user.full_name == "Test Patient"
    assert response_schema.abha_number == "12-1234-1234-1234"
    assert response_schema.gender == Gender.OTHER
