"""Unit tests for DoctorProfile and DiagnosticLabFacility Pydantic v2 schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.models.doctor import DoctorProfile
from app.models.enums import LabAccreditation, MedicalSpecialty, UserRole
from app.models.lab import DiagnosticLabFacility
from app.models.user import User
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)
from app.schemas.lab import (
    DiagnosticLabFacilityCreate,
    DiagnosticLabFacilityResponse,
    DiagnosticLabFacilityUpdate,
)


# ============================================================================
# DoctorProfile Schema Tests
# ============================================================================


def test_doctor_profile_create_validation_success() -> None:
    """Verify valid DoctorProfileCreate serialization with HPR registry identifier."""
    payload = DoctorProfileCreate(
        registration_number="KMC-45912",
        medical_council="Karnataka Medical Council",
        specialty=MedicalSpecialty.CARDIOLOGY,
        qualifications="MBBS, MD, DM (Cardiology)",
        experience_years=12,
        consultation_fee=1200,
        hospital_affiliation="Fortis Hospital Bangalore",
        bio="Consultant interventional cardiologist.",
        is_available_for_teleconsult=True,
        hpr_id="dr.vikram.sharma@hpr.abdm",
    )
    assert payload.registration_number == "KMC-45912"
    assert payload.specialty == MedicalSpecialty.CARDIOLOGY
    assert payload.experience_years == 12
    assert payload.consultation_fee == 1200
    assert payload.hpr_id == "dr.vikram.sharma@hpr.abdm"


def test_doctor_profile_invalid_hpr_id() -> None:
    """Verify DoctorProfileCreate rejects HPR IDs not adhering to @hpr.abdm standard."""
    # Missing @hpr.abdm suffix
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            hpr_id="dr.vikram@gmail.com",
        )

    # Just a handle without domain
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            hpr_id="dr_vikram",
        )

    # Invalid special characters
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            hpr_id="dr!vikram#@hpr.abdm",
        )


def test_doctor_profile_invalid_experience_and_fee() -> None:
    """Verify constraints on experience years and consultation fee."""
    # Negative experience
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            experience_years=-1,
        )

    # Unrealistic experience (>75)
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            experience_years=80,
        )

    # Negative fee
    with pytest.raises(ValidationError):
        DoctorProfileCreate(
            registration_number="KMC-45912",
            medical_council="Karnataka Medical Council",
            qualifications="MBBS",
            consultation_fee=-500,
        )


def test_doctor_profile_response_from_orm() -> None:
    """Verify DoctorProfileResponse serializes from SQLAlchemy ORM entities with nested User."""
    mock_user = User(
        id="user-doc-uuid-1",
        email="dr.kavita@hospital.org",
        full_name="Dr. Kavita Rao",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_doctor = DoctorProfile(
        id="doctor-profile-uuid-1",
        user_id=mock_user.id,
        user=mock_user,
        registration_number="DMC-98124",
        medical_council="Delhi Medical Council",
        specialty=MedicalSpecialty.NEUROLOGY,
        qualifications="MBBS, MD, DM",
        experience_years=10,
        consultation_fee=1500,
        hospital_affiliation="Max Super Speciality Hospital",
        bio="Consultant neurologist specializing in stroke recovery.",
        is_available_for_teleconsult=True,
        hpr_id="dr.kavita.rao@hpr.abdm",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = DoctorProfileResponse.model_validate(mock_doctor)
    assert response.id == "doctor-profile-uuid-1"
    assert response.user_id == "user-doc-uuid-1"
    assert response.user is not None
    assert response.user.full_name == "Dr. Kavita Rao"
    assert response.registration_number == "DMC-98124"
    assert response.specialty == MedicalSpecialty.NEUROLOGY
    assert response.hpr_id == "dr.kavita.rao@hpr.abdm"


# ============================================================================
# DiagnosticLabFacility Schema Tests
# ============================================================================


def test_lab_facility_create_validation_success() -> None:
    """Verify valid DiagnosticLabFacilityCreate serialization with HFR ID."""
    payload = DiagnosticLabFacilityCreate(
        facility_name="Metropolis Diagnostic Healthcare",
        license_number="MH-LAB-2023-1122",
        accreditation=LabAccreditation.NABL,
        accreditation_number="NABL-MC-9081",
        is_nabl_certified=True,
        contact_person="Dr. Ramesh Kulkarni",
        contact_phone="+919822334455",
        contact_email="reports@metropolis-health.com",
        address_line="Tower 3, MIDC Industrial Area",
        city="Pune",
        state="Maharashtra",
        pincode="411014",
        supported_tests="CBC, HbA1c, Lipid Profile, Renal Function",
        hfr_id="IN-MH-HFR-004512",
    )
    assert payload.facility_name == "Metropolis Diagnostic Healthcare"
    assert payload.accreditation == LabAccreditation.NABL
    assert payload.pincode == "411014"
    assert payload.hfr_id == "IN-MH-HFR-004512"


def test_lab_facility_invalid_hfr_id() -> None:
    """Verify DiagnosticLabFacilityCreate rejects invalid ABDM HFR ID format."""
    # Does not follow IN-STATE-HFR-XXXXXX pattern
    with pytest.raises(ValidationError):
        DiagnosticLabFacilityCreate(
            facility_name="Test Lab",
            license_number="LIC-123",
            contact_person="Tester",
            contact_phone="+919876543210",
            contact_email="test@lab.com",
            address_line="Main Road",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
            hfr_id="IN-MAHA-HFR-123",  # State code not 2 chars
        )

    # Missing HFR prefix
    with pytest.raises(ValidationError):
        DiagnosticLabFacilityCreate(
            facility_name="Test Lab",
            license_number="LIC-123",
            contact_person="Tester",
            contact_phone="+919876543210",
            contact_email="test@lab.com",
            address_line="Main Road",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
            hfr_id="IN-MH-004512",
        )


def test_lab_facility_invalid_pincode_and_email() -> None:
    """Verify pincode must be valid 6-digit Indian PIN and contact email must be valid."""
    # Invalid pincode starting with 0
    with pytest.raises(ValidationError):
        DiagnosticLabFacilityCreate(
            facility_name="Test Lab",
            license_number="LIC-123",
            contact_person="Tester",
            contact_phone="+919876543210",
            contact_email="test@lab.com",
            address_line="Main Road",
            city="Pune",
            state="Maharashtra",
            pincode="011001",
        )

    # Invalid email
    with pytest.raises(ValidationError):
        DiagnosticLabFacilityCreate(
            facility_name="Test Lab",
            license_number="LIC-123",
            contact_person="Tester",
            contact_phone="+919876543210",
            contact_email="not-an-email",
            address_line="Main Road",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
        )


def test_lab_facility_response_from_orm() -> None:
    """Verify DiagnosticLabFacilityResponse serializes from SQLAlchemy ORM entities."""
    mock_user = User(
        id="user-lab-uuid-1",
        email="lab.admin@thyrocare.com",
        full_name="Thyrocare Central",
        role=UserRole.LAB,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_lab = DiagnosticLabFacility(
        id="lab-facility-uuid-1",
        user_id=mock_user.id,
        user=mock_user,
        facility_name="Thyrocare Technologies Ltd",
        license_number="THYRO-MH-2022",
        accreditation=LabAccreditation.CAP,
        accreditation_number="CAP-8877",
        is_nabl_certified=True,
        contact_person="Dr. A. Velumani",
        contact_phone="+912244556677",
        contact_email="dispatch@thyrocare.com",
        address_line="D-37/1, TTC Industrial Area, Turbhe",
        city="Navi Mumbai",
        state="Maharashtra",
        pincode="400703",
        supported_tests="Thyroid, Vitamin D, Complete Metabolic Profile",
        hfr_id="IN-MH-HFR-008912",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = DiagnosticLabFacilityResponse.model_validate(mock_lab)
    assert response.id == "lab-facility-uuid-1"
    assert response.user_id == "user-lab-uuid-1"
    assert response.user is not None
    assert response.facility_name == "Thyrocare Technologies Ltd"
    assert response.accreditation == LabAccreditation.CAP
    assert response.is_nabl_certified is True
    assert response.hfr_id == "IN-MH-HFR-008912"
