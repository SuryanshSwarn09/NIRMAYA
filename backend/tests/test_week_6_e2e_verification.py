"""Week 6 End-to-End Closed-Loop Clinical Verification & Interoperability Test Suite.

Validates the full pharmacy and clinical medication lifecycle engineered across Week 6:
1. Multi-Role User Provisioning (Prescribing Doctor, Patient with ABHA, Dispensing Pharmacist, Unauthorized Tenant).
2. Longitudinal Condition & Allergy Profiling (Chronic Kidney Disease Stage 3, Severe Penicillin Anaphylaxis).
3. Pre-Prescription Clinical Decision Support (CDS) Safety Surveillance:
   - Contraindication detection: NSAID (Ketorolac) contraindicated in Chronic Kidney Disease (CRITICAL).
   - Hypersensitivity cross-reactivity detection: Penicillin allergy cross-reactive with Amoxicillin (CRITICAL).
   - Safe validation: Calcium channel blocker (Amlodipine) passes without critical contraindications.
4. Electronic Prescription (MedicationRequest) Authoring:
   - Formulating structured dosage, duration, repeat quotas, and generic substitution permissions.
   - Status transitions from draft to active upon cryptographic SHA-256 digital signature seal.
   - Post-signature immutability guard (HTTP 409 Conflict upon tamper attempts).
5. Pharmacy Dispense & Fulfillment Lifecycle (MedicationDispense):
   - Rejection of dispensing unsigned draft prescriptions (HTTP 400 Bad Request).
   - Execution of original fill (Fill 1/2) with batch lot, expiration tracking, and days supply.
   - Execution of authorized refill (Fill 2/2) with generic substitution governance.
   - Automatic prescription status transition to 'completed' upon repeat exhaustion.
   - Rejection of unauthorized excess fills beyond quota (HTTP 400 REFILLS_EXHAUSTED).
6. Longitudinal Patient Vault Inspection:
   - Patient accessing certified prescription timeline and dispensation records.
7. HL7 FHIR Release 4 Cross-Resource Export:
   - Canonical FHIR R4 MedicationRequest validation (dosageInstruction, dispenseRequest, signature).
   - Canonical FHIR R4 MedicationDispense validation (authorizingPrescription, substitution, lotNumber).
8. Strict Multi-Tenant Isolation & Role-Based Access Control (RBAC):
   - Cross-patient data isolation enforcement.
   - Role restriction on prescription authoring and pharmacy fulfillment.
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
from app.models.condition import ClinicalCondition
from app.models.doctor import DoctorProfile
from app.models.enums import (
    AdministrationRoute,
    CDSAlertType,
    CDSSeverity,
    ClinicalStatus,
    ConditionCategory,
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
    VerificationStatus,
)
from app.models.medication import Medication
from app.models.medication_dispense import MedicationDispense
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.models.user import User


# ==============================================================================
# FIXTURES & HELPERS
# ==============================================================================

@pytest_asyncio.fixture
async def week6_e2e_env():
    """Isolated in-memory test database and HTTP async client fixture for Week 6."""
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
    """Generate JWT Bearer authorization header for given user."""
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    })
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# COMPREHENSIVE E2E CLOSED-LOOP LIFECYCLE TEST
# ==============================================================================

@pytest.mark.asyncio
async def test_e2e_week_6_closed_loop_prescription_safety_dispense_lifecycle(week6_e2e_env) -> None:
    """Execute complete Week 6 closed-loop clinical and pharmacy lifecycle:
    Actors -> Conditions -> CDS Safety -> e-Prescription -> SHA-256 Sign -> Dispense Fill 1 ->
    Generic Refill Fill 2 -> Refill Exhaustion -> Patient Vault Query -> FHIR R4 Interop -> RBAC.
    """
    client, session_factory = week6_e2e_env

    # -------------------------------------------------------------------------
    # 1. Provision Multi-Role Actors
    # -------------------------------------------------------------------------
    async with session_factory() as session:
        # Prescribing Doctor (Cardiologist)
        doc_user = User(
            id="usr-doc-saxena",
            email="dr.saxena@nirmaya.health",
            full_name="Dr. Arvind Saxena",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(doc_user)
        await session.flush()

        doc_profile = DoctorProfile(
            id="doc-prof-saxena",
            user_id=doc_user.id,
            registration_number="DMC/2026/8841",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.CARDIOLOGY,
            qualifications="MBBS, MD (Cardiology), DM",
            experience_years=15,
            consultation_fee=1500.0,
            hpr_id="arvind.saxena@hpr.abdm",
        )
        session.add(doc_profile)

        # Primary Patient
        pat_user = User(
            id="usr-pat-singhania",
            email="vikram.singhania@nirmaya.health",
            full_name="Vikram Singhania",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(pat_user)
        await session.flush()

        pat_profile = PatientProfile(
            id="pat-prof-singhania",
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1974, 6, 21),
            blood_group="O+",
            abha_number="91-4455-6677-8899",
            abha_address="vikram.singhania@abdm",
        )
        session.add(pat_profile)

        # Dispensing Pharmacist / Clinical Practitioner
        pharm_user = User(
            id="usr-pharm-nair",
            email="meera.nair@nirmaya.health",
            full_name="Meera Nair",
            role=UserRole.DOCTOR,  # clinical practitioner with dispensing authority
            is_active=True,
            is_verified=True,
        )
        session.add(pharm_user)

        # Unauthorized Tenant Patient
        unauth_user = User(
            id="usr-pat-unauth",
            email="priya.sharma@nirmaya.health",
            full_name="Priya Sharma",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(unauth_user)
        await session.flush()

        unauth_profile = PatientProfile(
            id="pat-prof-unauth",
            user_id=unauth_user.id,
            gender=Gender.FEMALE,
            date_of_birth=date(1992, 11, 4),
            blood_group="A+",
            abha_number="91-1122-3344-9988",
            abha_address="priya.sharma@abdm",
        )
        session.add(unauth_profile)

        # -------------------------------------------------------------------------
        # 2. Seed Formulary Medications
        # -------------------------------------------------------------------------
        # Brand Amlodipine
        med_amlodipine_brand = Medication(
            id="med-norvasc-5",
            name="Norvasc 5mg Oral Tablet",
            generic_name="Amlodipine Besylate",
            brand_name="Norvasc",
            rxnorm_code="197361",
            rxnorm_display="Amlodipine 5 MG Oral Tablet",
            atc_code="C08CA01",
            atc_display="Amlodipine",
            snomed_code="386864001",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="5 mg",
            active_ingredient="Amlodipine Besylate",
            is_prescription_required=True,
            is_controlled_substance=False,
            formulary_tier=FormularyTier.TIER_2_PREFERRED_BRAND,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_amlodipine_brand)

        # Generic Amlodipine Equivalent
        med_amlodipine_generic = Medication(
            id="med-amlodac-5",
            name="Amlodipine 5mg Tablet",
            generic_name="Amlodipine Besylate",
            brand_name="Amlodac",
            rxnorm_code="197361",
            rxnorm_display="Amlodipine 5 MG Oral Tablet",
            atc_code="C08CA01",
            atc_display="Amlodipine",
            snomed_code="386864001",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="5 mg",
            active_ingredient="Amlodipine Besylate",
            is_prescription_required=True,
            is_controlled_substance=False,
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_amlodipine_generic)

        # Nephrotoxic NSAID: Ketorolac
        med_ketorolac = Medication(
            id="med-ketorolac-10",
            name="Ketorolac Tromethamine 10mg Tablet",
            generic_name="Ketorolac Tromethamine",
            brand_name="Toradol",
            rxnorm_code="311207",
            rxnorm_display="Ketorolac Tromethamine 10 MG Oral Tablet",
            atc_code="M01AB15",
            atc_display="Ketorolac",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="10 mg",
            active_ingredient="Ketorolac",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_ketorolac)

        # Penicillin Antibiotic: Amoxicillin
        med_amoxicillin = Medication(
            id="med-amox-500",
            name="Amoxicillin 500mg Oral Capsule",
            generic_name="Amoxicillin Trihydrate",
            brand_name="Mox 500",
            rxnorm_code="723",
            atc_code="J01CA04",
            form=MedicationForm.CAPSULE,
            route=AdministrationRoute.ORAL,
            strength="500 mg",
            active_ingredient="Amoxicillin Trihydrate",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_amoxicillin)

        # -------------------------------------------------------------------------
        # 3. Patient Clinical Problem List: Chronic Kidney Disease Stage 3
        # -------------------------------------------------------------------------
        ckd_condition = ClinicalCondition(
            id="cond-ckd-stage-3",
            patient_id=pat_profile.id,
            recorded_by_doctor_id=doc_profile.id,
            code_coding_system="http://hl7.org/fhir/sid/icd-10",
            code_value="N18.3",
            code_display="Chronic Kidney Disease, Stage 3",
            category=ConditionCategory.CHRONIC_CONDITION,
            clinical_status=ClinicalStatus.ACTIVE,
            verification_status=VerificationStatus.CONFIRMED,
            onset_date_time=datetime.now(timezone.utc) - timedelta(days=365),
            recorded_date=datetime.now(timezone.utc) - timedelta(days=30),
        )
        session.add(ckd_condition)
        await session.commit()

    # -------------------------------------------------------------------------
    # 4. Pre-Prescription CDS Safety Surveillance Checks
    # -------------------------------------------------------------------------
    # Candidate Drug 1: Ketorolac (NSAID in CKD Patient) -> Must trigger CRITICAL Contraindication
    check_nsaid_resp = await client.post(
        f"/api/v1/patients/{pat_profile.id}/prescriptions/safety-check",
        json={"medication_id": med_ketorolac.id, "dosage_text": "10mg as needed for severe pain"},
        headers=auth_header_for(doc_user),
    )
    assert check_nsaid_resp.status_code == 200
    nsaid_report = check_nsaid_resp.json()["data"]
    assert nsaid_report["passed"] is False
    assert nsaid_report["has_critical_alerts"] is True
    assert nsaid_report["requires_override"] is True
    assert any(
        alert["alert_type"] == "drug-condition" and "Kidney Disease" in alert["title"]
        for alert in nsaid_report["alerts"]
    )

    # Candidate Drug 2: Amoxicillin with Penicillin Hypersensitivity -> Must trigger CRITICAL Allergy Alert
    check_amox_resp = await client.post(
        f"/api/v1/patients/{pat_profile.id}/prescriptions/safety-check",
        json={
            "medication_id": med_amoxicillin.id,
            "dosage_text": "500mg three times daily",
            "supplemental_allergies": ["Severe penicillin anaphylaxis"],
        },
        headers=auth_header_for(doc_user),
    )
    assert check_amox_resp.status_code == 200
    amox_report = check_amox_resp.json()["data"]
    assert amox_report["passed"] is False
    assert amox_report["has_critical_alerts"] is True
    assert any(
        alert["alert_type"] == "drug-allergy" and "Penicillin" in alert["title"]
        for alert in amox_report["alerts"]
    )

    # Candidate Drug 3: Amlodipine Besylate (Safe Antihypertensive) -> Must Pass
    check_safe_resp = await client.post(
        f"/api/v1/patients/{pat_profile.id}/prescriptions/safety-check",
        json={
            "medication_id": med_amlodipine_brand.id,
            "dosage_text": "Take 1 tablet (5mg) orally once daily in the morning",
        },
        headers=auth_header_for(doc_user),
    )
    assert check_safe_resp.status_code == 200
    safe_report = check_safe_resp.json()["data"]
    assert safe_report["passed"] is True
    assert safe_report["has_critical_alerts"] is False
    assert safe_report["requires_override"] is False

    # -------------------------------------------------------------------------
    # 5. Electronic Prescription (MedicationRequest) Authoring
    # -------------------------------------------------------------------------
    rx_payload = {
        "medication_id": med_amlodipine_brand.id,
        "intent": "order",
        "priority": "routine",
        "dosage_text": "Take 1 tablet (5mg) orally once daily in the morning with water",
        "dose_quantity": 5.0,
        "dose_unit": "mg",
        "route": "oral",
        "frequency": 1,
        "period": 1.0,
        "period_unit": "d",
        "as_needed": False,
        "additional_instructions": "Maintain daily blood pressure diary.",
        "dispense_quantity": 30.0,
        "dispense_unit": "tablets",
        "expected_supply_duration_days": 30,
        "number_of_repeats_allowed": 1,  # Total fills = 2 (1 original + 1 refill)
        "allow_generic_substitution": True,
        "reason_code": "I10",
        "note": "Hypertension management concurrent with renal monitoring.",
    }

    create_rx_resp = await client.post(
        f"/api/v1/patients/{pat_profile.id}/prescriptions",
        json=rx_payload,
        headers=auth_header_for(doc_user),
    )
    assert create_rx_resp.status_code == 201
    rx_data = create_rx_resp.json()["data"]
    rx_id = rx_data["id"]
    assert rx_data["status"] == "draft"
    assert rx_data["is_signed"] is False
    assert rx_data["number_of_repeats_allowed"] == 1
    assert rx_data["allow_generic_substitution"] is True

    # -------------------------------------------------------------------------
    # 6. Unsigned Prescription Dispense Rejection Guard
    # -------------------------------------------------------------------------
    dispense_unverified_resp = await client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={
            "prescription_id": rx_id,
            "quantity_dispensed": 30.0,
            "dispense_unit": "tablets",
            "days_supply": 30,
            "lot_number": "LOT-PRE-FAIL",
        },
        headers=auth_header_for(pharm_user),
    )
    assert dispense_unverified_resp.status_code == 400
    assert "not been digitally signed" in dispense_unverified_resp.json()["message"]

    # -------------------------------------------------------------------------
    # 7. Prescriber Digital Signature & Cryptographic Seal
    # -------------------------------------------------------------------------
    sign_resp = await client.post(
        f"/api/v1/prescriptions/{rx_id}/sign",
        json={"signature_notes": "Cryptographically certified for outpatient dispensing."},
        headers=auth_header_for(doc_user),
    )
    assert sign_resp.status_code == 200
    signed_data = sign_resp.json()["data"]
    assert signed_data["is_signed"] is True
    assert signed_data["status"] == "active"
    assert signed_data["signed_at"] is not None
    assert len(signed_data["signature_hash"]) == 64  # SHA-256 hex digest

    # -------------------------------------------------------------------------
    # 8. Post-Signature Immutability Guard
    # -------------------------------------------------------------------------
    tamper_resp = await client.patch(
        f"/api/v1/prescriptions/{rx_id}",
        json={"dosage_text": "Tampered dosage instructions"},
        headers=auth_header_for(doc_user),
    )
    assert tamper_resp.status_code == 409
    assert "immutable" in tamper_resp.json()["message"]

    # -------------------------------------------------------------------------
    # 9. Pharmacy Dispense Lifecycle - Fill 1 (Original Fill)
    # -------------------------------------------------------------------------
    fill1_resp = await client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={
            "prescription_id": rx_id,
            "quantity_dispensed": 30.0,
            "dispense_unit": "tablets",
            "days_supply": 30,
            "lot_number": "LOT-2026-NORV-01",
            "expiration_date": "2028-06-30",
            "pharmacist_notes": "Original fill dispensed. Patient counseled on morning administration.",
        },
        headers=auth_header_for(pharm_user),
    )
    assert fill1_resp.status_code == 201
    fill1_data = fill1_resp.json()["data"]
    fill1_id = fill1_data["id"]
    assert fill1_data["status"] == "completed"
    assert fill1_data["quantity_dispensed"] == 30.0
    assert fill1_data["lot_number"] == "LOT-2026-NORV-01"
    assert fill1_data["was_substituted"] is False
    assert fill1_data["dispenser_name"] == "Meera Nair"

    # Verify prescription remains ACTIVE because 1 refill is still remaining
    async with session_factory() as session:
        rx_record = await session.get(MedicationRequest, rx_id)
        assert rx_record.status == MedicationRequestStatus.ACTIVE

    # -------------------------------------------------------------------------
    # 10. Pharmacy Dispense Lifecycle - Fill 2 (Refill with Generic Substitution)
    # -------------------------------------------------------------------------
    fill2_resp = await client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={
            "prescription_id": rx_id,
            "medication_id": med_amlodipine_generic.id,  # Generic substitution
            "quantity_dispensed": 30.0,
            "dispense_unit": "tablets",
            "days_supply": 30,
            "was_substituted": True,
            "substitution_type": "G",
            "substitution_reason": "Formulary tier-1 generic equivalent supplied",
            "lot_number": "LOT-2026-AMLO-GEN",
            "expiration_date": "2028-09-30",
            "pharmacist_notes": "Refill 1 dispensed with generic substitution as authorized by prescriber.",
        },
        headers=auth_header_for(pharm_user),
    )
    assert fill2_resp.status_code == 201
    fill2_data = fill2_resp.json()["data"]
    fill2_id = fill2_data["id"]
    assert fill2_data["was_substituted"] is True
    assert fill2_data["medication_id"] == med_amlodipine_generic.id
    assert fill2_data["substitution_type"] == "G"

    # Verify prescription automatically transitioned to COMPLETED upon repeat exhaustion
    async with session_factory() as session:
        rx_completed = await session.get(MedicationRequest, rx_id)
        assert rx_completed.status == MedicationRequestStatus.COMPLETED

    # -------------------------------------------------------------------------
    # 11. Refill Quota Exhaustion Guard (Fill 3 Attempt)
    # -------------------------------------------------------------------------
    excess_fill_resp = await client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={
            "prescription_id": rx_id,
            "quantity_dispensed": 30.0,
            "dispense_unit": "tablets",
            "days_supply": 30,
            "lot_number": "LOT-2026-EXCESS",
        },
        headers=auth_header_for(pharm_user),
    )
    assert excess_fill_resp.status_code == 400
    assert "Maximum authorized prescription fills reached" in excess_fill_resp.json()["message"]

    # -------------------------------------------------------------------------
    # 12. Longitudinal Patient Vault Inspection
    # -------------------------------------------------------------------------
    # Patient queries prescriptions list
    pat_rx_resp = await client.get(
        f"/api/v1/patients/{pat_profile.id}/prescriptions",
        headers=auth_header_for(pat_user),
    )
    assert pat_rx_resp.status_code == 200
    pat_rx_list = pat_rx_resp.json()["data"]
    assert len(pat_rx_list) == 1
    assert pat_rx_list[0]["id"] == rx_id
    assert pat_rx_list[0]["status"] == "completed"

    # Patient queries dispensations list
    pat_disp_resp = await client.get(
        f"/api/v1/dispensations?patient_id={pat_profile.id}",
        headers=auth_header_for(pat_user),
    )
    assert pat_disp_resp.status_code == 200
    pat_disp_list = pat_disp_resp.json()["data"]
    assert len(pat_disp_list) == 2
    lot_numbers = {d["lot_number"] for d in pat_disp_list}
    assert "LOT-2026-NORV-01" in lot_numbers
    assert "LOT-2026-AMLO-GEN" in lot_numbers

    # -------------------------------------------------------------------------
    # 13. HL7 FHIR Release 4 Cross-Resource Export Compliance
    # -------------------------------------------------------------------------
    # Export MedicationRequest FHIR
    fhir_rx_resp = await client.get(
        f"/api/v1/prescriptions/{rx_id}/fhir",
        headers=auth_header_for(doc_user),
    )
    assert fhir_rx_resp.status_code == 200
    fhir_rx = fhir_rx_resp.json()
    assert fhir_rx["resourceType"] == "MedicationRequest"
    assert fhir_rx["status"] == "completed"
    assert fhir_rx["intent"] == "order"
    assert fhir_rx["subject"]["reference"] == f"Patient/{pat_profile.id}"
    assert fhir_rx["requester"]["reference"] == f"Practitioner/{doc_profile.id}"
    assert len(fhir_rx["dosageInstruction"]) > 0
    assert fhir_rx["dispenseRequest"]["numberOfRepeatsAllowed"] == 1
    assert fhir_rx["substitution"]["allowedBoolean"] is True

    # Export MedicationDispense FHIR (Fill 1)
    fhir_disp1_resp = await client.get(
        f"/api/v1/dispensations/{fill1_id}/fhir",
        headers=auth_header_for(pharm_user),
    )
    assert fhir_disp1_resp.status_code == 200
    fhir_disp1 = fhir_disp1_resp.json()
    assert fhir_disp1["resourceType"] == "MedicationDispense"
    assert fhir_disp1["status"] == "completed"
    assert fhir_disp1["authorizingPrescription"][0]["reference"] == f"MedicationRequest/{rx_id}"
    assert fhir_disp1["subject"]["reference"] == f"Patient/{pat_profile.id}"
    assert fhir_disp1["quantity"]["value"] == 30.0
    assert fhir_disp1["daysSupply"]["value"] == 30
    assert fhir_disp1["substitution"]["wasSubstituted"] is False

    # Export MedicationDispense FHIR (Fill 2 with Generic Substitution)
    fhir_disp2_resp = await client.get(
        f"/api/v1/dispensations/{fill2_id}/fhir",
        headers=auth_header_for(pharm_user),
    )
    assert fhir_disp2_resp.status_code == 200
    fhir_disp2 = fhir_disp2_resp.json()
    assert fhir_disp2["substitution"]["wasSubstituted"] is True
    assert fhir_disp2["substitution"]["type"]["coding"][0]["code"] == "G"

    # -------------------------------------------------------------------------
    # 14. RBAC & Multi-Tenant Security Isolation
    # -------------------------------------------------------------------------
    # Unauthorized tenant patient cannot view primary patient's prescriptions
    unauth_rx_resp = await client.get(
        f"/api/v1/patients/{pat_profile.id}/prescriptions",
        headers=auth_header_for(unauth_user),
    )
    assert unauth_rx_resp.status_code == 403

    # Unauthorized tenant patient listing dispensations is scoped to own account (0 records)
    unauth_disp_resp = await client.get(
        f"/api/v1/dispensations?patient_id={pat_profile.id}",
        headers=auth_header_for(unauth_user),
    )
    assert unauth_disp_resp.status_code == 200
    assert len(unauth_disp_resp.json()["data"]) == 0

    # Unauthorized tenant patient attempting direct access to primary patient's dispensation is blocked
    unauth_direct_disp = await client.get(
        f"/api/v1/dispensations/{fill1_id}",
        headers=auth_header_for(unauth_user),
    )
    assert unauth_direct_disp.status_code == 403

    # Primary patient cannot dispense prescription (enforced role guard)
    patient_disp_attempt = await client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"prescription_id": rx_id, "quantity_dispensed": 30.0},
        headers=auth_header_for(pat_user),
    )
    assert patient_disp_attempt.status_code == 403


# ==============================================================================
# FOCUSED TEST: CRITICAL DRUG-DRUG INTERACTION SURVEILLANCE & OVERRIDE
# ==============================================================================

@pytest.mark.asyncio
async def test_e2e_cds_critical_ddi_blocking_and_override(week6_e2e_env) -> None:
    """Verify CDS safety engine catches severe Drug-Drug Interactions between an active
    anticoagulant prescription (Warfarin) and a candidate antiplatelet (Aspirin).
    """
    client, session_factory = week6_e2e_env

    async with session_factory() as session:
        # Doctor
        doc_user = User(
            id="usr-doc-ddi",
            email="dr.ddi@nirmaya.health",
            full_name="Dr. DDI Safety",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(doc_user)
        await session.flush()

        doc_profile = DoctorProfile(
            id="doc-prof-ddi",
            user_id=doc_user.id,
            registration_number="DMC/2026/1102",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.GENERAL_MEDICINE,
            qualifications="MBBS, MD",
            experience_years=8,
            consultation_fee=800.0,
        )
        session.add(doc_profile)

        # Patient
        pat_user = User(
            id="usr-pat-ddi",
            email="pat.ddi@nirmaya.health",
            full_name="Rajesh Verma",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(pat_user)
        await session.flush()

        pat_profile = PatientProfile(
            id="pat-prof-ddi",
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1968, 3, 15),
            blood_group="B+",
            abha_number="91-7788-9900-1122",
            abha_address="rajesh.verma@abdm",
        )
        session.add(pat_profile)

        # Active Medication 1: Warfarin 5mg
        med_warfarin = Medication(
            id="med-warfarin-5",
            name="Warfarin Sodium 5mg Tablet",
            generic_name="Warfarin Sodium",
            brand_name="Coumadin",
            rxnorm_code="855333",
            atc_code="B01AA03",
            form=MedicationForm.TABLET,
            strength="5 mg",
            active_ingredient="Warfarin Sodium",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_warfarin)

        # Candidate Medication 2: Aspirin 75mg
        med_aspirin = Medication(
            id="med-aspirin-75",
            name="Aspirin 75mg Gastro-Resistant Tablet",
            generic_name="Aspirin",
            brand_name="Ecosprin 75",
            rxnorm_code="1191",
            atc_code="B01AC06",
            form=MedicationForm.TABLET,
            strength="75 mg",
            active_ingredient="Aspirin",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_aspirin)

        # Active, digitally signed prescription for Warfarin
        rx_warfarin = MedicationRequest(
            id="rx-warfarin-active",
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            medication_id=med_warfarin.id,
            status=MedicationRequestStatus.ACTIVE,
            intent=MedicationRequestIntent.ORDER,
            priority=MedicationRequestPriority.ROUTINE,
            dosage_text="Take 1 tablet daily in the evening as per INR",
            is_signed=True,
            signed_at=datetime.now(timezone.utc),
            signature_hash="sha256-verified-warfarin-seal",
        )
        session.add(rx_warfarin)
        await session.commit()

    # Pre-prescription safety check for candidate Aspirin against active Warfarin
    check_resp = await client.post(
        f"/api/v1/patients/{pat_profile.id}/prescriptions/safety-check",
        json={"medication_id": med_aspirin.id, "dosage_text": "75mg once daily"},
        headers=auth_header_for(doc_user),
    )
    assert check_resp.status_code == 200
    report = check_resp.json()["data"]
    assert report["passed"] is False
    assert report["has_critical_alerts"] is True
    assert report["requires_override"] is True
    assert any(
        alert["alert_type"] == "drug-drug"
        and "Warfarin" in alert["title"]
        and alert["severity"] == "critical"
        for alert in report["alerts"]
    )


# ==============================================================================
# FOCUSED TEST: DISPENSE FORBIDDEN SUBSTITUTION GUARD
# ==============================================================================

@pytest.mark.asyncio
async def test_e2e_dispense_forbidden_substitution_guard(week6_e2e_env) -> None:
    """Verify that when a prescriber explicitly forbids generic substitution
    (Dispense As Written), any attempt by pharmacy to substitute is strictly rejected.
    """
    client, session_factory = week6_e2e_env

    async with session_factory() as session:
        doc_user = User(
            id="usr-doc-daw",
            email="dr.daw@nirmaya.health",
            full_name="Dr. Prescriber",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(doc_user)
        await session.flush()

        doc_profile = DoctorProfile(
            id="doc-prof-daw",
            user_id=doc_user.id,
            registration_number="DMC/2026/9090",
            medical_council="Delhi Medical Council",
            specialty=MedicalSpecialty.GENERAL_MEDICINE,
            qualifications="MBBS",
            experience_years=5,
        )
        session.add(doc_profile)

        pat_user = User(
            id="usr-pat-daw",
            email="pat.daw@nirmaya.health",
            full_name="Karan Oberoi",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(pat_user)
        await session.flush()

        pat_profile = PatientProfile(
            id="pat-prof-daw",
            user_id=pat_user.id,
            gender=Gender.MALE,
            date_of_birth=date(1988, 1, 1),
            blood_group="B+",
            abha_number="91-2233-4455-6677",
            abha_address="karan.oberoi@abdm",
        )
        session.add(pat_profile)

        pharm_user = User(
            id="usr-pharm-daw",
            email="pharm.daw@nirmaya.health",
            full_name="Pharmacy Staff",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True,
        )
        session.add(pharm_user)

        med_brand = Medication(
            id="med-brand-daw",
            name="Brand Specific Med 10mg",
            generic_name="Generic Molecule",
            brand_name="Brand Specific",
            rxnorm_code="990001",
            form=MedicationForm.TABLET,
            strength="10 mg",
            active_ingredient="Generic Molecule",
            formulary_tier=FormularyTier.TIER_2_PREFERRED_BRAND,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_brand)

        med_generic = Medication(
            id="med-generic-daw",
            name="Generic Molecule 10mg",
            generic_name="Generic Molecule",
            brand_name="Generic",
            rxnorm_code="990001",
            form=MedicationForm.TABLET,
            strength="10 mg",
            active_ingredient="Generic Molecule",
            formulary_tier=FormularyTier.TIER_1_GENERIC,
            status=MedicationStatus.ACTIVE,
        )
        session.add(med_generic)

        # Prescription with allow_generic_substitution = False (Dispense As Written)
        rx_daw = MedicationRequest(
            id="rx-daw-strict",
            patient_id=pat_profile.id,
            doctor_id=doc_profile.id,
            medication_id=med_brand.id,
            status=MedicationRequestStatus.ACTIVE,
            intent=MedicationRequestIntent.ORDER,
            priority=MedicationRequestPriority.ROUTINE,
            dosage_text="1 tablet daily - Dispense as Written strictly",
            dispense_quantity=30.0,
            dispense_unit="tablets",
            number_of_repeats_allowed=1,
            allow_generic_substitution=False,  # STRICT FORBIDDEN
            is_signed=True,
            signed_at=datetime.now(timezone.utc),
            signature_hash="sha256-daw-strict-seal",
        )
        session.add(rx_daw)
        await session.commit()

    # Attempt substitution
    sub_resp = await client.post(
        f"/api/v1/prescriptions/{rx_daw.id}/dispense",
        json={
            "prescription_id": rx_daw.id,
            "medication_id": med_generic.id,
            "quantity_dispensed": 30.0,
            "dispense_unit": "tablets",
            "was_substituted": True,
            "lot_number": "LOT-DAW-FAIL",
        },
        headers=auth_header_for(pharm_user),
    )
    assert sub_resp.status_code == 400
    assert "prohibited by the prescriber" in sub_resp.json()["message"]
