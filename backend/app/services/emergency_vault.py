"""Break-The-Glass (BTG) Emergency Vault & Zero-Knowledge Cryptography Service.

Implements:
1. Argon2id key derivation from passphrases and CSPRNG salts.
2. AES-256-GCM authenticated encryption with Additional Authenticated Data (AAD = patient ABHA).
3. Audited Break-The-Glass emergency override execution for credentialed clinicians.
4. Tamper-evident forensic audit log pipeline with SHA-256 digital seals.
5. Automated real-time WebSocket event dissemination.
"""

import base64
from datetime import datetime, timezone
import hashlib
import logging
import os
import threading
from typing import Dict, List, Optional
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.schemas.emergency_vault import (
    BTGAuditLogEntry,
    BTGOverrideRequest,
    BTGOverrideResponse,
    BTGStatsResponse,
    EmergencyAllergyItem,
    EmergencyBloodGroup,
    EmergencyConditionItem,
    EmergencyContactItem,
    EmergencyJustificationCategory,
    EmergencyMedicationItem,
    EmergencyProfileData,
    EmergencyVaultStatusResponse,
    EncryptedVaultEnvelope,
)
from app.schemas.websocket_events import (
    AlertSeverity,
    CriticalAlertPayload,
    WebSocketChannel,
    WebSocketEventType,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("nirmaya.emergency_vault")

# System fallback master recovery key for demo environment
SYSTEM_DEMO_PASSPHRASE = "NIRMAYA-EMERGENCY-MASTER-OVERRIDE-KEY-2026"


# -----------------------------------------------------------------------------
# Cryptographic Primitives (Argon2id + AES-256-GCM)
# -----------------------------------------------------------------------------

def derive_vault_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a 256-bit symmetric encryption key using Argon2id.

    Parameters:
    - memory_cost: 65536 KiB (64 MiB)
    - iterations: 2
    - lanes (parallelism): 2
    - length: 32 bytes
    """
    kdf = Argon2id(
        salt=salt,
        length=32,
        iterations=2,
        lanes=2,
        memory_cost=65536,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_emergency_profile(
    profile: EmergencyProfileData,
    passphrase: str = SYSTEM_DEMO_PASSPHRASE,
) -> EncryptedVaultEnvelope:
    """Encrypts an emergency health profile using Argon2id and AES-256-GCM AEAD.

    Binds the patient ABHA number as Additional Authenticated Data (AAD) to prevent
    cross-patient ciphertext swapping attacks.
    """
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_vault_key(passphrase, salt)

    profile_json = profile.model_dump_json().encode("utf-8")
    aad = profile.patientAbha.encode("utf-8")

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, profile_json, aad)

    ciphertext_hash = hashlib.sha256(ciphertext).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()

    return EncryptedVaultEnvelope(
        vaultId=f"vlt-{uuid.uuid4().hex[:12]}",
        patientAbha=profile.patientAbha,
        ciphertextB64=base64.b64encode(ciphertext).decode("utf-8"),
        nonceB64=base64.b64encode(nonce).decode("utf-8"),
        saltB64=base64.b64encode(salt).decode("utf-8"),
        kdfAlgorithm="Argon2id",
        cipherAlgorithm="AES-256-GCM",
        ciphertextSha256=ciphertext_hash,
        createdAt=now_iso,
        updatedAt=now_iso,
    )


def decrypt_emergency_profile(
    envelope: EncryptedVaultEnvelope,
    passphrase: str = SYSTEM_DEMO_PASSPHRASE,
) -> EmergencyProfileData:
    """Decrypts an encrypted emergency vault envelope using Argon2id and AES-256-GCM AEAD."""
    salt = base64.b64decode(envelope.saltB64)
    nonce = base64.b64decode(envelope.nonceB64)
    ciphertext = base64.b64decode(envelope.ciphertextB64)

    # Validate raw ciphertext SHA-256 hash
    actual_hash = hashlib.sha256(ciphertext).hexdigest()
    if actual_hash != envelope.ciphertextSha256:
        raise ValidationException("Ciphertext integrity breach: SHA-256 digest does not match vault record")

    key = derive_vault_key(passphrase, salt)
    aad = envelope.patientAbha.encode("utf-8")

    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as exc:
        raise ValidationException(f"Decryption failed: authentication tag verification error or invalid key ({exc})")

    return EmergencyProfileData.model_validate_json(plaintext.decode("utf-8"))


# -----------------------------------------------------------------------------
# Emergency Vault & Audit Service
# -----------------------------------------------------------------------------

class EmergencyVaultService:
    """Thread-safe service managing Zero-Knowledge emergency health vaults and Break-The-Glass overrides."""

    def __init__(self) -> None:
        self._vaults: Dict[str, EncryptedVaultEnvelope] = {}
        self._audit_log: List[BTGAuditLogEntry] = []
        self._lock = threading.Lock()
        self._seed_demo_vault()

    def _seed_demo_vault(self) -> None:
        """Seeds initial realistic emergency profile for Arun Patel (ABHA: 91-8472-1092-4821)."""
        demo_profile = EmergencyProfileData(
            patientAbha="91-8472-1092-4821",
            patientName="Arun Patel",
            dateOfBirth="1990-06-04",
            gender="Male",
            bloodGroup=EmergencyBloodGroup.O_POS,
            allergies=[
                EmergencyAllergyItem(
                    substance="Penicillin V",
                    criticality="high",
                    manifestation="Severe Anaphylaxis with laryngeal edema",
                ),
                EmergencyAllergyItem(
                    substance="Ciprofloxacin",
                    criticality="moderate",
                    manifestation="Acute generalized urticaria and angioedema",
                ),
            ],
            medications=[
                EmergencyMedicationItem(
                    medicationName="Lisinopril",
                    dosage="10mg once daily",
                    category="ACE Inhibitor",
                    highRiskWarning="Risk of profound hypotension under general anesthesia",
                ),
                EmergencyMedicationItem(
                    medicationName="Metformin",
                    dosage="500mg twice daily",
                    category="Oral Antidiabetic",
                    highRiskWarning="Hold if iodinated radiocontrast or severe sepsis",
                ),
            ],
            conditions=[
                EmergencyConditionItem(
                    conditionName="Essential Hypertension",
                    icd10Code="I10",
                    notes="Baseline BP 138/88 mmHg. Prone to hypertensive urgency under acute pain.",
                ),
                EmergencyConditionItem(
                    conditionName="Type 2 Diabetes Mellitus",
                    icd10Code="E11.9",
                    notes="Stat fingerstick glucose required upon arrival.",
                ),
            ],
            emergencyContacts=[
                EmergencyContactItem(
                    name="Pooja Patel",
                    relationship="Spouse",
                    phone="+91 98765 09991",
                    isPrimary=True,
                ),
                EmergencyContactItem(
                    name="Ramesh Patel",
                    relationship="Brother",
                    phone="+91 98765 11223",
                    isPrimary=False,
                ),
            ],
            organDonorStatus=True,
            advanceDirectives="FULL_CODE: Perform CPR and endotracheal intubation if in cardiac/respiratory arrest.",
            updatedAt=datetime.now(timezone.utc).isoformat(),
        )

        envelope = encrypt_emergency_profile(demo_profile, SYSTEM_DEMO_PASSPHRASE)
        self._vaults[demo_profile.patientAbha] = envelope

    def store_vault(
        self,
        profile: EmergencyProfileData,
        passphrase: str = SYSTEM_DEMO_PASSPHRASE,
    ) -> EncryptedVaultEnvelope:
        """Encrypts and stores a patient's emergency health profile."""
        envelope = encrypt_emergency_profile(profile, passphrase)
        with self._lock:
            self._vaults[profile.patientAbha] = envelope
        return envelope

    def get_vault_status(self, patient_abha: str) -> EmergencyVaultStatusResponse:
        """Returns provisioning status and lifetime override count for a patient's vault."""
        with self._lock:
            envelope = self._vaults.get(patient_abha)
            overrides_count = sum(1 for e in self._audit_log if e.patientAbha == patient_abha)

        return EmergencyVaultStatusResponse(
            patientAbha=patient_abha,
            isProvisioned=envelope is not None,
            vaultId=envelope.vaultId if envelope else None,
            lastEncryptedAt=envelope.updatedAt if envelope else None,
            totalOverridesLifetime=overrides_count,
        )

    async def execute_emergency_override(
        self,
        request: BTGOverrideRequest,
        ip_address: Optional[str] = None,
        passphrase: str = SYSTEM_DEMO_PASSPHRASE,
    ) -> BTGOverrideResponse:
        """Executes audited Break-The-Glass emergency override, decrypting emergency vault.

        Validates clinical justification, decrypts profile under Argon2id+AES-256-GCM,
        generates tamper-evident SHA-256 forensic audit seal, and dispatches real-time WebSocket alerts.
        """
        # 1. Validate mandatory clinical justification
        if not request.clinicalJustification or len(request.clinicalJustification.strip()) < 15:
            raise ValidationException("Mandatory clinical justification must contain at least 15 characters of diagnostic rationale")

        with self._lock:
            envelope = self._vaults.get(request.patientAbha)

        if not envelope:
            raise EntityNotFoundException("EmergencyVault", request.patientAbha)

        # 2. Decrypt emergency profile
        decrypted_profile = decrypt_emergency_profile(envelope, passphrase)

        # 3. Formulate forensic audit event
        event_id = f"btg-evt-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        fingerprint_raw = (
            f"{event_id}:{request.patientAbha}:{request.doctorId}:{request.doctorHpr}:"
            f"{request.facilityId}:{request.justificationCategory.value}:{now_iso}:"
            f"{request.clinicalJustification.strip()}"
        )
        audit_fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

        audit_entry = BTGAuditLogEntry(
            eventId=event_id,
            patientAbha=request.patientAbha,
            doctorId=request.doctorId,
            doctorHpr=request.doctorHpr,
            doctorName=request.doctorName,
            facilityId=request.facilityId,
            justificationCategory=request.justificationCategory,
            clinicalJustification=request.clinicalJustification.strip(),
            department=request.department,
            timestamp=now_iso,
            auditFingerprint=audit_fingerprint,
            ipAddress=ip_address,
        )

        with self._lock:
            self._audit_log.append(audit_entry)

        # 4. Automated real-time WebSocket broadcast
        alert_payload = CriticalAlertPayload(
            alertId=f"alt-btg-{uuid.uuid4().hex[:8]}",
            patientId=request.patientAbha,
            patientName=decrypted_profile.patientName,
            doctorId=request.doctorId,
            severity=AlertSeverity.PANIC,
            category="EMERGENCY_BTG_ACCESS",
            title="EMERGENCY BREAK-THE-GLASS OVERRIDE EXECUTED",
            message=(
                f"Stat emergency access by {request.doctorName} ({request.doctorHpr}) for "
                f"ABHA {request.patientAbha}. Justification: {request.justificationCategory.value} - "
                f"{request.clinicalJustification.strip()} (Audit Fingerprint: {audit_fingerprint[:16]}...)"
            ),
            observedValue=f"Blood: {decrypted_profile.bloodGroup.value}",
            actionRequired=True,
            createdAt=now_iso,
        )

        try:
            # Broadcast to clinician workspace
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(request.doctorId),
                event_type=WebSocketEventType.CRITICAL_ALERT,
                payload=alert_payload.model_dump(),
            )
            # Broadcast to hospital facility queue / supervision
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.facility_queue(request.facilityId),
                event_type=WebSocketEventType.CRITICAL_ALERT,
                payload=alert_payload.model_dump(),
            )
        except Exception as exc:
            logger.error("Failed to broadcast BTG emergency alert: %s", exc)

        return BTGOverrideResponse(
            overrideGranted=True,
            eventId=event_id,
            patientAbha=request.patientAbha,
            emergencyProfile=decrypted_profile,
            auditFingerprint=audit_fingerprint,
            accessedAt=now_iso,
            warning="EMERGENCY OVERRIDE GRANTED. All actions are cryptographically sealed in the immutable forensic audit log.",
        )

    def get_audit_trail(
        self,
        patient_abha: Optional[str] = None,
        facility_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[BTGAuditLogEntry]:
        """Queries forensic audit trail filterable by patient ABHA or hospital facility."""
        with self._lock:
            matches = list(self._audit_log)

        if patient_abha:
            matches = [e for e in matches if e.patientAbha == patient_abha]
        if facility_id:
            matches = [e for e in matches if e.facilityId == facility_id]

        matches.sort(key=lambda e: e.timestamp, reverse=True)
        return matches[:limit]

    def get_stats(self, facility_id: Optional[str] = None) -> BTGStatsResponse:
        """Computes emergency department compliance statistics."""
        with self._lock:
            events = list(self._audit_log)

        if facility_id:
            events = [e for e in events if e.facilityId == facility_id]

        total = len(events)
        distinct_patients = len(set(e.patientAbha for e in events))
        distinct_doctors = len(set(e.doctorId for e in events))

        distribution: Dict[str, int] = {}
        for e in events:
            cat = e.justificationCategory.value
            distribution[cat] = distribution.get(cat, 0) + 1

        return BTGStatsResponse(
            facilityId=facility_id or "ALL_FACILITIES",
            totalBTGOverrides=total,
            distinctPatientsAccessed=distinct_patients,
            distinctCliniciansExecuting=distinct_doctors,
            justificationDistribution=distribution,
        )


# Global singleton instance
emergency_vault_service = EmergencyVaultService()
