"""Tests for Clinical Decision Support (CDS) Safety Engine.

Verifies:
1. Rule-based Drug-Drug Interaction (DDI) detection and severity grading.
2. Allergy and hypersensitivity cross-reactivity checks.
3. Clinical condition and disease contraindication detection.
4. Asynchronous service integration and REST endpoint execution.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.condition import ClinicalCondition
from app.models.enums import (
    AdministrationRoute,
    CDSAlertType,
    CDSSeverity,
    ClinicalStatus,
    ConditionCategory,
    FormularyTier,
    MedicationForm,
    MedicationRequestStatus,
    MedicationStatus,
    UserRole,
    VerificationStatus,
)
from app.models.medication import Medication
from app.models.medication_request import MedicationRequest
from app.models.patient import PatientProfile
from app.models.user import User
from app.services.cds_rules import (
    evaluate_allergy_cross_sensitivity,
    evaluate_condition_contraindications,
    evaluate_drug_drug_interactions,
)
from app.services.cds_safety import evaluate_prescription_safety


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest_asyncio.fixture
async def cds_test_env():
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


# ==============================================================================
# 1. UNIT TESTS: RULE ENGINE
# ==============================================================================

def test_ddi_rules_all_curated_pairs():
    """Verify all 10 curated clinical DDI interaction pairs are accurately matched."""
    # 1. Warfarin + Aspirin
    alerts = evaluate_drug_drug_interactions("Aspirin 75mg Oral Tablet", ["Warfarin Sodium 5mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value
    assert alerts[0]["rule_id"] == "DDI-001"

    # 2. Ramipril + Spironolactone
    alerts = evaluate_drug_drug_interactions("Spironolactone 25mg Tablet", ["Ramipril 5mg Oral Capsule"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-002"

    # 3. Metformin + Iodinated Contrast
    alerts = evaluate_drug_drug_interactions("Metformin 500mg Tablet", ["Iodixanol Radiocontrast Injection"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value
    assert alerts[0]["rule_id"] == "DDI-003"

    # 4. Clopidogrel + Omeprazole
    alerts = evaluate_drug_drug_interactions("Omeprazole 20mg Delayed-Release Capsule", ["Clopidogrel 75mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-004"

    # 5. Fluoxetine + Tramadol
    alerts = evaluate_drug_drug_interactions("Tramadol 50mg Tablet", ["Fluoxetine Hydrochloride 20mg Capsule"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-005"

    # 6. Atorvastatin + Clarithromycin
    alerts = evaluate_drug_drug_interactions("Clarithromycin 500mg Tablet", ["Atorvastatin Calcium 40mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-006"

    # 7. Methotrexate + Amoxicillin
    alerts = evaluate_drug_drug_interactions("Amoxicillin 500mg Capsule", ["Methotrexate 2.5mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value
    assert alerts[0]["rule_id"] == "DDI-007"

    # 8. Levothyroxine + Calcium Carbonate
    alerts = evaluate_drug_drug_interactions("Calcium Carbonate 500mg Tablet", ["Levothyroxine Sodium 100mcg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MODERATE.value
    assert alerts[0]["rule_id"] == "DDI-008"

    # 9. Digoxin + Amiodarone
    alerts = evaluate_drug_drug_interactions("Amiodarone 200mg Tablet", ["Digoxin 0.25mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-009"

    # 10. Ciprofloxacin + Theophylline
    alerts = evaluate_drug_drug_interactions("Theophylline 300mg Extended Release", ["Ciprofloxacin 500mg Tablet"])
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value
    assert alerts[0]["rule_id"] == "DDI-010"


def test_allergy_cross_sensitivity_rules():
    """Verify allergy matching triggers expected critical and major alerts."""
    # Penicillin allergy with Amoxicillin
    alerts = evaluate_allergy_cross_sensitivity("Amoxicillin 500mg Oral Capsule", ["Penicillin allergy"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value
    assert alerts[0]["alert_type"] == CDSAlertType.DRUG_ALLERGY.value

    # Sulfa allergy with Co-trimoxazole
    alerts = evaluate_allergy_cross_sensitivity("Trimethoprim-Sulfamethoxazole 800mg/160mg", ["Severe sulfa rash"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value

    # Aspirin allergy with Diclofenac
    alerts = evaluate_allergy_cross_sensitivity("Diclofenac Sodium 50mg Tablet", ["Aspirin-induced asthma"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.MAJOR.value

    # Non-allergic drug
    alerts = evaluate_allergy_cross_sensitivity("Acetaminophen 500mg Tablet", ["Penicillin allergy"])
    assert len(alerts) == 0


def test_condition_contraindications_rules():
    """Verify condition contraindications correctly flag severe drug-disease conflicts."""
    # Chronic Kidney Disease + Ibuprofen
    alerts = evaluate_condition_contraindications("Ibuprofen 400mg Oral Tablet", ["Chronic Kidney Disease Stage 4"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value

    # Peptic Ulcer Disease + Ketorolac
    alerts = evaluate_condition_contraindications("Ketorolac Tromethamine 10mg", ["Active peptic ulcer with bleeding"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value

    # Severe Asthma + Propranolol
    alerts = evaluate_condition_contraindications("Propranolol Hydrochloride 40mg", ["Severe bronchial asthma"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == CDSSeverity.CRITICAL.value

    # Safe condition match
    alerts = evaluate_condition_contraindications("Amoxicillin 500mg Capsule", ["Essential Hypertension"])
    assert len(alerts) == 0


# ==============================================================================
# 2. INTEGRATION TESTS: SERVICE & ENDPOINTS
# ==============================================================================

@pytest.mark.asyncio
async def test_cds_safety_service_evaluation(cds_test_env):
    """Test full asynchronous CDSSafetyService evaluation against database entities."""
    client, session_factory = cds_test_env

    async with session_factory() as session:
        # 1. Create Patient User & Profile
        user = User(
            id="test-cds-patient-user",
            email="cds.patient@nirmaya.org",
            full_name="CDS Test Patient",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.flush()

        patient = PatientProfile(
            user_id=user.id,
            abha_number="91-1234-5678-9999",
            abha_address="cds.patient@abdm",
        )
        session.add(patient)
        await session.flush()

        # 2. Create Active Condition: Chronic Kidney Disease
        condition = ClinicalCondition(
            patient_id=patient.id,
            clinical_status=ClinicalStatus.ACTIVE,
            verification_status=VerificationStatus.CONFIRMED,
            category=ConditionCategory.CHRONIC_CONDITION,
            code_coding_system="http://snomed.info/sct",
            code_value="709044004",
            code_display="Chronic kidney disease stage 3 (disorder)",
        )
        session.add(condition)

        # 3. Create Existing Active Prescription: Warfarin
        warfarin_med = Medication(
            name="Warfarin Sodium 5mg Oral Tablet",
            generic_name="Warfarin Sodium",
            brand_name="Coumadin",
            active_ingredient="Warfarin Sodium",
            rxnorm_code="855332",
            atc_code="B01AA03",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="5 mg",
            status=MedicationStatus.ACTIVE,
            formulary_tier=FormularyTier.TIER_1_GENERIC,
        )
        session.add(warfarin_med)
        await session.flush()

        active_rx = MedicationRequest(
            patient_id=patient.id,
            medication_id=warfarin_med.id,
            status=MedicationRequestStatus.ACTIVE,
            is_signed=True,
            dosage_text="Take 5mg once daily in the evening",
        )
        session.add(active_rx)

        # 4. Candidate Drug: Aspirin (Triggers DDI with Warfarin + Condition warning with CKD)
        aspirin_med = Medication(
            name="Aspirin 75mg Gastro-resistant Tablet",
            generic_name="Aspirin",
            brand_name="Ecosprin",
            active_ingredient="Aspirin",
            rxnorm_code="243670",
            atc_code="B01AC06",
            form=MedicationForm.TABLET,
            route=AdministrationRoute.ORAL,
            strength="75 mg",
            status=MedicationStatus.ACTIVE,
            formulary_tier=FormularyTier.TIER_1_GENERIC,
        )
        session.add(aspirin_med)
        await session.commit()

        # 5. Evaluate Safety
        report = await evaluate_prescription_safety(
            db=session,
            patient_id=patient.id,
            medication_id=aspirin_med.id,
            supplemental_allergies=["Aspirin hypersensitivity"],
        )

        assert report.passed is False
        assert report.has_critical_alerts is True
        assert report.requires_override is True
        assert report.total_alerts >= 2  # DDI + Allergy

        # Ensure alerts are sorted with Critical alerts first
        severities = [a.severity.value for a in report.alerts]
        assert severities[0] == CDSSeverity.CRITICAL.value


@pytest.mark.asyncio
async def test_cds_safety_endpoint_via_api(cds_test_env):
    """Test POST /api/v1/patients/{patient_id}/prescriptions/safety-check REST endpoint."""
    client, session_factory = cds_test_env

    async with session_factory() as session:
        # 1. Create Patient User & Profile
        patient_user = User(
            id="test-api-cds-patient-user",
            email="api.cds.patient@nirmaya.org",
            full_name="API CDS Patient",
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=True,
        )
        session.add(patient_user)
        await session.flush()

        patient = PatientProfile(
            user_id=patient_user.id,
            abha_number="91-0000-1111-2222",
            abha_address="api.cds@abdm",
        )
        session.add(patient)

        # 2. Create Candidate Drug: Amoxicillin
        amoxicillin = Medication(
            name="Amoxicillin 500mg Oral Capsule",
            generic_name="Amoxicillin Trihydrate",
            brand_name="Mox 500",
            active_ingredient="Amoxicillin Trihydrate",
            rxnorm_code="723",
            atc_code="J01CA04",
            form=MedicationForm.CAPSULE,
            route=AdministrationRoute.ORAL,
            strength="500 mg",
            status=MedicationStatus.ACTIVE,
            formulary_tier=FormularyTier.TIER_1_GENERIC,
        )
        session.add(amoxicillin)
        await session.commit()

        patient_id = patient.id
        med_id = amoxicillin.id

    # 3. Call safety-check with documented penicillin allergy
    payload = {
        "medication_id": med_id,
        "dosage_text": "1 capsule three times daily for 7 days",
        "supplemental_allergies": ["Severe penicillin anaphylaxis"],
    }

    # Simulate authenticated patient viewing own safety check
    response = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions/safety-check",
        json=payload,
        headers=auth_header_for(patient_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    report = data["data"]
    assert report["passed"] is False
    assert report["has_critical_alerts"] is True
    assert report["requires_override"] is True
    assert any("Penicillin" in a["title"] for a in report["alerts"])
