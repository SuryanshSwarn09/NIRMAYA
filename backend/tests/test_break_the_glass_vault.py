"""Comprehensive Automated Test Suite for Break-The-Glass (BTG) Emergency Vault & Forensic Audit.

Tests:
1. Argon2id 256-bit key derivation determinism and salt uniqueness.
2. Zero-Knowledge AES-256-GCM encryption/decryption roundtrip.
3. Cryptographic tamper protection via Additional Authenticated Data (AAD) binding.
4. Authentication tag failure on wrong decryption passphrase.
5. Vault provisioning and status inquiry endpoints.
6. Successful Break-The-Glass clinical override execution with decrypted profile delivery.
7. Validation rejection (HTTP 422) for insufficient justification (< 15 characters).
8. HTTP 404 rejection for nonexistent emergency vault ABHA.
9. Tamper-evident forensic audit log verification with SHA-256 digital seals.
10. Emergency department compliance statistics and category distribution.
11. Real-time WebSocket push dissemination of EMERGENCY_BTG_ACCESS event.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.core.security import create_access_token
from app.main import app
from app.schemas.emergency_vault import (
    EmergencyAllergyItem,
    EmergencyBloodGroup,
    EmergencyConditionItem,
    EmergencyContactItem,
    EmergencyJustificationCategory,
    EmergencyMedicationItem,
    EmergencyProfileData,
)
from app.schemas.websocket_events import WebSocketChannel, WebSocketEventType
from app.services.emergency_vault import (
    decrypt_emergency_profile,
    derive_vault_key,
    encrypt_emergency_profile,
)

client = TestClient(app)


def _generate_test_token(sub: str = "doc-er-tester", role: str = "DOCTOR") -> str:
    """Helper generating signed JWT for authenticated WebSocket tests."""
    return create_access_token(
        data={"sub": sub, "role": role, "user_metadata": {"role": role}},
    )


class TestArgon2idVaultCryptography:
    """Unit tests verifying Argon2id KDF and AES-256-GCM AEAD encryption properties."""

    def test_argon2id_key_derivation_properties(self):
        """Asserts Argon2id produces 32-byte deterministic keys with unique salts."""
        salt1 = b"0123456789abcdef"
        salt2 = b"fedcba9876543210"

        key1_a = derive_vault_key("secure_passphrase_2026", salt1)
        key1_b = derive_vault_key("secure_passphrase_2026", salt1)
        key2 = derive_vault_key("secure_passphrase_2026", salt2)

        assert len(key1_a) == 32
        assert key1_a == key1_b  # Deterministic with same salt
        assert key1_a != key2    # Unique with different salt

    def test_encrypt_and_decrypt_profile_roundtrip(self):
        """Asserts complete encryption and decryption roundtrip preserves all emergency clinical fields."""
        profile = EmergencyProfileData(
            patientAbha="91-1122-3344-5566",
            patientName="Priya Nair",
            dateOfBirth="1984-11-20",
            gender="Female",
            bloodGroup=EmergencyBloodGroup.B_POS,
            allergies=[
                EmergencyAllergyItem(
                    substance="Sulfa Drugs",
                    criticality="high",
                    manifestation="Stevens-Johnson Syndrome",
                ),
            ],
            medications=[
                EmergencyMedicationItem(
                    medicationName="Warfarin",
                    dosage="5mg daily",
                    category="Anticoagulant",
                    highRiskWarning="High bleeding risk; reverse with Vitamin K / PCC if acute bleed",
                ),
            ],
            conditions=[
                EmergencyConditionItem(
                    conditionName="Atrial Fibrillation",
                    icd10Code="I48.0",
                ),
            ],
            emergencyContacts=[
                EmergencyContactItem(
                    name="Karan Nair",
                    relationship="Spouse",
                    phone="+91 98111 22233",
                    isPrimary=True,
                ),
            ],
            organDonorStatus=True,
            advanceDirectives="FULL_CODE",
        )

        passphrase = "priya-vault-passphrase-alpha"
        envelope = encrypt_emergency_profile(profile, passphrase)

        assert envelope.patientAbha == "91-1122-3344-5566"
        assert envelope.kdfAlgorithm == "Argon2id"
        assert envelope.cipherAlgorithm == "AES-256-GCM"
        assert envelope.ciphertextSha256 is not None

        # Decrypt
        decrypted = decrypt_emergency_profile(envelope, passphrase)
        assert decrypted.patientName == "Priya Nair"
        assert decrypted.bloodGroup == EmergencyBloodGroup.B_POS
        assert len(decrypted.allergies) == 1
        assert decrypted.allergies[0].substance == "Sulfa Drugs"
        assert decrypted.medications[0].medicationName == "Warfarin"

    def test_decrypt_with_tampered_aad_rejected(self):
        """Asserts ciphertext cannot be decrypted if ABHA number (AAD) is modified."""
        profile = EmergencyProfileData(
            patientAbha="91-0000-1111-2222",
            patientName="Test Subject",
            dateOfBirth="1995-01-01",
            gender="Other",
            bloodGroup=EmergencyBloodGroup.O_NEG,
        )
        passphrase = "test-passphrase"
        envelope = encrypt_emergency_profile(profile, passphrase)

        # Tamper with AAD by modifying patientAbha in the envelope
        envelope.patientAbha = "91-9999-8888-7777"

        with pytest.raises(ValidationException) as excinfo:
            decrypt_emergency_profile(envelope, passphrase)
        assert "Decryption failed" in str(excinfo.value)

    def test_decrypt_with_wrong_passphrase_rejected(self):
        """Asserts decryption fails when an incorrect passphrase is supplied."""
        profile = EmergencyProfileData(
            patientAbha="91-3333-4444-5555",
            patientName="Test Subject 2",
            dateOfBirth="1988-08-08",
            gender="Male",
            bloodGroup=EmergencyBloodGroup.A_POS,
        )
        envelope = encrypt_emergency_profile(profile, "correct-passphrase")

        with pytest.raises(ValidationException) as excinfo:
            decrypt_emergency_profile(envelope, "wrong-passphrase")
        assert "Decryption failed" in str(excinfo.value)


class TestBreakTheGlassEndpointsAndAudit:
    """Integration tests verifying REST API endpoints, BTG override, and forensic audit trail."""

    def test_get_vault_status_seeded_patient(self):
        """Asserts status check for seeded demo patient Arun Patel."""
        response = client.get("/api/v1/emergency/btg/vault/91-8472-1092-4821/status")
        assert response.status_code == 200
        data = response.json()

        assert data["patientAbha"] == "91-8472-1092-4821"
        assert data["isProvisioned"] is True
        assert data["vaultId"] is not None

    def test_get_vault_status_unprovisioned_patient(self):
        """Asserts status check for unprovisioned ABHA identity."""
        response = client.get("/api/v1/emergency/btg/vault/91-0000-0000-0000/status")
        assert response.status_code == 200
        data = response.json()

        assert data["isProvisioned"] is False
        assert data["vaultId"] is None

    def test_execute_emergency_override_success(self):
        """Asserts executing Break-The-Glass override decrypts emergency profile and returns audit seal."""
        payload = {
            "patientAbha": "91-8472-1092-4821",
            "doctorId": "doc-trauma-99",
            "doctorHpr": "vivek.murthy@hpr.abdm",
            "doctorName": "Dr. Vivek Murthy",
            "facilityId": "fac-aiims-trauma",
            "justificationCategory": "UNCONSCIOUS_TRAUMA",
            "clinicalJustification": "Patient arrived comatose with GCS 5 following high-speed vehicular collision. Stat airway and blood transfusion required.",
            "department": "Emergency Trauma Bay 1",
        }

        response = client.post("/api/v1/emergency/btg/override", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["overrideGranted"] is True
        assert data["eventId"] is not None
        assert data["patientAbha"] == "91-8472-1092-4821"
        assert data["auditFingerprint"] is not None
        assert len(data["auditFingerprint"]) == 64  # SHA-256 hex digest

        # Verify decrypted emergency profile contents
        profile = data["emergencyProfile"]
        assert profile["patientName"] == "Arun Patel"
        assert profile["bloodGroup"] == "O+"
        assert len(profile["allergies"]) >= 1
        assert profile["allergies"][0]["substance"] == "Penicillin V"
        assert len(profile["emergencyContacts"]) >= 1
        assert profile["emergencyContacts"][0]["name"] == "Pooja Patel"

    def test_execute_emergency_override_short_justification_rejected(self):
        """Asserts clinical justification under 15 characters is rejected with HTTP 422."""
        payload = {
            "patientAbha": "91-8472-1092-4821",
            "doctorId": "doc-trauma-99",
            "doctorHpr": "vivek.murthy@hpr.abdm",
            "doctorName": "Dr. Vivek Murthy",
            "facilityId": "fac-aiims-trauma",
            "justificationCategory": "UNCONSCIOUS_TRAUMA",
            "clinicalJustification": "emergency need",  # 14 chars -> < 15
        }

        response = client.post("/api/v1/emergency/btg/override", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data.get("error_code") == "VALIDATION_ERROR" or "detail" in data or "details" in data

    def test_execute_emergency_override_nonexistent_patient_404(self):
        """Asserts non-existent patient vault returns HTTP 404."""
        payload = {
            "patientAbha": "91-9999-9999-9999",
            "doctorId": "doc-trauma-99",
            "doctorHpr": "vivek.murthy@hpr.abdm",
            "doctorName": "Dr. Vivek Murthy",
            "facilityId": "fac-aiims-trauma",
            "justificationCategory": "UNCONSCIOUS_TRAUMA",
            "clinicalJustification": "Critical resuscitation required for unidentified trauma victim.",
        }

        response = client.post("/api/v1/emergency/btg/override", json=payload)
        assert response.status_code == 404

    def test_forensic_audit_trail_retrieval(self):
        """Asserts forensic audit trail captures emergency overrides with tamper-evident SHA-256 fingerprint."""
        response = client.get("/api/v1/emergency/btg/audit?patient_abha=91-8472-1092-4821")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        entry = data[0]
        assert entry["patientAbha"] == "91-8472-1092-4821"
        assert entry["doctorHpr"] == "vivek.murthy@hpr.abdm"
        assert entry["justificationCategory"] == "UNCONSCIOUS_TRAUMA"
        assert len(entry["auditFingerprint"]) == 64

    def test_emergency_btg_stats(self):
        """Asserts hospital emergency department compliance statistics."""
        response = client.get("/api/v1/emergency/btg/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["totalBTGOverrides"] >= 1
        assert data["distinctPatientsAccessed"] >= 1
        assert data["distinctCliniciansExecuting"] >= 1
        assert "UNCONSCIOUS_TRAUMA" in data["justificationDistribution"]


class TestBreakTheGlassWebSocketSynchronization:
    """Integration test verifying real-time WebSocket broadcast of BTG emergency overrides."""

    def test_emergency_btg_websocket_broadcast_delivery(self):
        """Asserts executing BTG override dispatches real-time critical alert to facility and doctor."""
        facility_id = "fac-er-ws-test"
        doctor_id = "doc-er-ws-01"
        token = _generate_test_token(sub=doctor_id, role="DOCTOR")

        with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={token}") as websocket:
            ack = websocket.receive_json()
            assert ack["eventType"] == WebSocketEventType.CONNECTION_ACK.value

            # Execute BTG override
            override_res = client.post(
                "/api/v1/emergency/btg/override",
                json={
                    "patientAbha": "91-8472-1092-4821",
                    "doctorId": doctor_id,
                    "doctorHpr": "er.specialist@hpr.abdm",
                    "doctorName": "Dr. Sunita Sen",
                    "facilityId": facility_id,
                    "justificationCategory": "MASSIVE_HEMORRHAGE",
                    "clinicalJustification": "Exsanguinating pelvic fracture and hemorrhagic shock. Immediate massive transfusion protocol initiated.",
                    "department": "Trauma Resuscitation Unit",
                },
            )
            assert override_res.status_code == 200

            # Inbound real-time WebSocket frame must arrive on facility queue
            event = websocket.receive_json()
            assert event["eventType"] == WebSocketEventType.CRITICAL_ALERT.value
            assert event["channel"] == f"facility:{facility_id}:queue"
            assert event["payload"]["category"] == "EMERGENCY_BTG_ACCESS"
            assert event["payload"]["severity"] == "PANIC"
            assert "EMERGENCY BREAK-THE-GLASS OVERRIDE EXECUTED" in event["payload"]["title"]
            assert "Blood: O+" in event["payload"]["observedValue"]
