"""ABDM Milestone 3 (M3) Health Information User (HIU) Data Consumer Service.

Implements NHA ABDM v0.5 Data Flow & Fidelius specifications for requesting, decrypting,
and parsing longitudinal medical records from peer Health Information Providers (HIPs):
- HIU Request Initiation & Ephemeral Curve25519 Key Generation
- Thread-safe HIURequestStore for correlation session management
- Nonce XOR + ECDH Key Agreement + HKDF-SHA256 Derivation on inbound push
- AES-256-GCM authenticated payload decryption and SHA-256 checksum verification
- Clinical HL7 FHIR R4 Document Bundle parser (Encounter, DiagnosticReport, MedicationRequest, Observation)
- Thread-safe HIURecordStore for clinician longitudinal review
"""

import base64
from datetime import datetime, timezone, timedelta
import hashlib
import json
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.schemas.abdm_m3_hiu import (
    DecryptedClinicalBundle,
    HIUDataRequestInitiate,
    HIUPatientRecordsResponse,
    HIURequestSession,
    ParsedDiagnosticReport,
    ParsedEncounter,
    ParsedObservation,
    ParsedPrescription,
)
from app.schemas.abdm_m3_transfer import (
    DataTransferPushPayload,
    EncryptedDataEntry,
    TransferAuditRecord,
)
from app.schemas.abdm_m2_bridge import WebhookEventItem
from app.services.abdm_crypto import AbdmCryptoService
from app.services.abdm_transfer import AbdmTransferService, transfer_audit_store
from app.services.abdm_hip_bridge import NIRMAYA_HIP_ID, webhook_audit_store

logger = logging.getLogger("nirmaya.abdm.m3_hiu")

DEFAULT_HIU_SESSION_TTL_SECONDS = 3600  # 1 hour lifetime


class HIURequestStore:
    """Thread-safe in-memory cache for active HIU data request sessions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: Dict[str, HIURequestSession] = {}  # tx_id -> session
        self._consent_index: Dict[str, str] = {}  # consent_id -> tx_id
        self._total_requests: int = 0

    @property
    def total_requests(self) -> int:
        with self._lock:
            return self._total_requests

    def store_session(self, session: HIURequestSession) -> None:
        with self._lock:
            self._total_requests += 1
            self._sessions[session.transactionId] = session
            self._consent_index[session.consentId] = session.transactionId
            logger.info(
                f"[HIURequestStore] Stored session tx={session.transactionId}, "
                f"consent={session.consentId}, patient={session.patientId}"
            )

    def get_session(self, transaction_id: str) -> Optional[HIURequestSession]:
        with self._lock:
            session = self._sessions.get(transaction_id)
            if not session:
                return None
            if datetime.now(timezone.utc) > session.expiresAt:
                logger.warning(f"[HIURequestStore] Session tx={transaction_id} expired")
                self.delete_session(transaction_id)
                return None
            return session

    def get_session_by_consent(self, consent_id: str) -> Optional[HIURequestSession]:
        with self._lock:
            tx_id = self._consent_index.get(consent_id)
            if not tx_id:
                return None
            return self.get_session(tx_id)

    def update_status(self, transaction_id: str, new_status: str) -> Optional[HIURequestSession]:
        with self._lock:
            session = self._sessions.get(transaction_id)
            if not session:
                return None
            updated = session.model_copy(update={"status": new_status})
            self._sessions[transaction_id] = updated
            return updated

    def delete_session(self, transaction_id: str) -> bool:
        with self._lock:
            session = self._sessions.pop(transaction_id, None)
            if session:
                self._consent_index.pop(session.consentId, None)
                return True
            return False

    def list_sessions(self) -> List[HIURequestSession]:
        with self._lock:
            now = datetime.now(timezone.utc)
            active = []
            for tx_id, s in list(self._sessions.items()):
                if now <= s.expiresAt:
                    active.append(s)
                else:
                    self.delete_session(tx_id)
            return active

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()
            self._consent_index.clear()
            self._total_requests = 0


class HIURecordStore:
    """Thread-safe store for imported, decrypted, and parsed longitudinal patient records."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._patient_bundles: Dict[str, List[DecryptedClinicalBundle]] = {}  # patient_id -> bundles
        self._tx_bundles: Dict[str, List[DecryptedClinicalBundle]] = {}  # tx_id -> bundles
        self._tamper_rejections: int = 0

    def record_tamper_rejection(self) -> None:
        with self._lock:
            self._tamper_rejections += 1

    @property
    def tamper_rejections(self) -> int:
        with self._lock:
            return self._tamper_rejections

    def save_records(
        self,
        patient_id: str,
        transaction_id: str,
        bundles: List[DecryptedClinicalBundle],
    ) -> None:
        with self._lock:
            p_id = patient_id.lower()
            if p_id not in self._patient_bundles:
                self._patient_bundles[p_id] = []
            self._patient_bundles[p_id].extend(bundles)
            self._tx_bundles[transaction_id] = bundles
            logger.info(
                f"[HIURecordStore] Persisted {len(bundles)} clinical bundles for "
                f"patient={p_id}, tx={transaction_id}"
            )

    def get_patient_records(self, patient_id: str) -> List[DecryptedClinicalBundle]:
        with self._lock:
            return list(self._patient_bundles.get(patient_id.lower(), []))

    def get_transaction_records(self, transaction_id: str) -> List[DecryptedClinicalBundle]:
        with self._lock:
            return list(self._tx_bundles.get(transaction_id, []))

    def get_all_bundles(self) -> List[DecryptedClinicalBundle]:
        with self._lock:
            all_bundles: List[DecryptedClinicalBundle] = []
            for b_list in self._tx_bundles.values():
                all_bundles.extend(b_list)
            return all_bundles

    def clear(self) -> None:
        with self._lock:
            self._patient_bundles.clear()
            self._tx_bundles.clear()
            self._tamper_rejections = 0


# Global singletons
hiu_request_store = HIURequestStore()
hiu_record_store = HIURecordStore()


class AbdmHIUService:
    """HIU Data Consumer orchestration engine."""

    @classmethod
    def initiate_hi_request(
        cls,
        req: HIUDataRequestInitiate,
    ) -> Tuple[HIURequestSession, Dict[str, Any]]:
        """Initiates an outbound Health Information Request under an approved Consent Artefact.
        
        1. Generates ephemeral Curve25519 (X25519) key pair and 32-byte CSPRNG nonce.
        2. Establishes HIURequestSession with 1-hour expiration.
        3. Formulates NHA ABDM Gateway request payload for /v0.5/health-information/cm/request.
        
        Returns:
            Tuple of (HIURequestSession, gateway_request_payload_dict)
        """
        _, b64_pub, b64_priv = AbdmCryptoService.generate_key_pair()
        _, b64_nonce = AbdmCryptoService.generate_nonce()

        tx_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=DEFAULT_HIU_SESSION_TTL_SECONDS)

        session = HIURequestSession(
            transactionId=tx_id,
            consentId=req.consentId,
            patientId=req.patientId,
            hiuPrivateKey=b64_priv,
            hiuPublicKey=b64_pub,
            hiuNonce=b64_nonce,
            status="REQUESTED",
            dateRangeFrom=req.dateRangeFrom,
            dateRangeTo=req.dateRangeTo,
            createdAt=now,
            expiresAt=expires_at,
        )
        hiu_request_store.store_session(session)

        # Formulate NHA Gateway payload
        server_base = getattr(settings, "SERVER_HOST", "https://nirmaya.health")
        data_push_url = req.dataPushUrl or f"{server_base.rstrip('/')}{settings.API_V1_STR}/abdm/m3/hiu/transfer"
        gateway_payload = {
            "requestId": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "hiRequest": {
                "consent": {"id": req.consentId},
                "dateRange": {
                    "from": req.dateRangeFrom.isoformat(),
                    "to": req.dateRangeTo.isoformat(),
                },
                "dataPushUrl": data_push_url,
                "keyMaterial": {
                    "cryptoAlg": "ECDH",
                    "curve": "Curve25519",
                    "userInfo": {
                        "publicKey": b64_pub,
                        "nonce": b64_nonce,
                    },
                },
            },
        }

        logger.info(
            f"[initiate_hi_request] Initiated HIU request tx={tx_id}, consent={req.consentId}, "
            f"patient={req.patientId}, dataPushUrl={data_push_url}"
        )
        return session, gateway_payload

    @classmethod
    def process_inbound_transfer(
        cls,
        payload: DataTransferPushPayload,
    ) -> Tuple[bool, Optional[str], List[DecryptedClinicalBundle]]:
        """Processes an incoming encrypted data transfer push from a peer HIP.
        
        1. Validates matching transactionId in HIURequestStore.
        2. Computes Nonce XOR (HIU Nonce ⊕ HIP Nonce) to derive 20-byte Salt and 12-byte IV.
        3. Performs ECDH scalar multiplication: SharedSecret = ECDH(HIU_Private, HIP_Public).
        4. Derives 32-byte symmetric AES key via HKDF-SHA256(SharedSecret, Salt).
        5. Decrypts each EncryptedDataEntry via AES-256-GCM.
        6. Verifies SHA-256 checksum of decrypted plaintext bundle.
        7. Parses FHIR R4 Document Bundle into structured clinical representations.
        8. Persists parsed bundles in HIURecordStore for longitudinal review.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str], List[DecryptedClinicalBundle])
        """
        tx_id = str(payload.transactionId)
        session = hiu_request_store.get_session(tx_id)

        if not session:
            msg = f"HIU request session '{tx_id}' not found or has expired"
            logger.warning(f"[process_inbound_transfer] {msg}")
            return False, msg, []

        # Parse key material
        hip_pub_b64 = payload.keyMaterial.userInfo.publicKey
        hip_nonce_b64 = payload.keyMaterial.userInfo.nonce

        try:
            hiu_priv = AbdmCryptoService.parse_private_key(session.hiuPrivateKey)
            hiu_nonce = AbdmCryptoService.parse_nonce(session.hiuNonce)
            hip_pub = AbdmCryptoService.parse_public_key(hip_pub_b64)
            hip_nonce = AbdmCryptoService.parse_nonce(hip_nonce_b64)
        except ValidationException as ve:
            msg = f"Key parsing failed: {ve.message}"
            logger.error(f"[process_inbound_transfer] {msg}")
            return False, msg, []

        # Derive Salt, IV, Shared Secret, and Symmetric Key
        _, salt, iv = AbdmCryptoService.compute_xor_entropy(hiu_nonce, hip_nonce)
        shared_secret = AbdmCryptoService.derive_shared_secret(hiu_priv, hip_pub)
        derived_key = AbdmCryptoService.derive_symmetric_key(shared_secret, salt)

        decrypted_bundles: List[DecryptedClinicalBundle] = []

        for idx, entry in enumerate(payload.entries):
            # Decrypt payload
            try:
                plaintext_json = AbdmTransferService.decrypt_payload(
                    b64_ciphertext=entry.content,
                    derived_key=derived_key,
                    iv=iv,
                )
            except ValidationException as ve:
                hiu_record_store.record_tamper_rejection()
                msg = f"Entry {idx} decryption failed: {ve.message}"
                logger.error(f"[process_inbound_transfer] {msg}")
                return False, msg, []

            # Check SHA-256 checksum integrity
            computed_checksum = hashlib.sha256(plaintext_json.encode("utf-8")).hexdigest()
            if computed_checksum.lower() != entry.checksum.lower():
                hiu_record_store.record_tamper_rejection()
                msg = (
                    f"Entry {idx} checksum mismatch! Computed: {computed_checksum}, "
                    f"Expected: {entry.checksum}. Payload altered in transit."
                )
                logger.error(f"[process_inbound_transfer] {msg}")
                return False, msg, []

            # Parse FHIR R4 Bundle into structured clinical views
            bundle_obj = cls.parse_fhir_bundle(
                fhir_json=plaintext_json,
                care_context_ref=entry.careContextReference,
            )
            decrypted_bundles.append(bundle_obj)

        # Persist parsed bundles into record store
        hiu_record_store.save_records(
            patient_id=session.patientId,
            transaction_id=tx_id,
            bundles=decrypted_bundles,
        )

        # Update session status
        hiu_request_store.update_status(tx_id, "PROCESSED")

        # Record in transfer audit store
        audit_rec = TransferAuditRecord(
            id=str(uuid.uuid4()),
            transactionId=tx_id,
            consentId=session.consentId,
            direction="INBOUND_RECEIVE",
            entriesCount=len(decrypted_bundles),
            dataPushUrl="LOCAL_HIU_RECEIVER",
            status="SUCCESS",
            timestamp=datetime.now(timezone.utc),
        )
        transfer_audit_store.add_record(audit_rec)

        logger.info(
            f"[process_inbound_transfer] Successfully processed & imported {len(decrypted_bundles)} "
            f"bundles for patient={session.patientId}, tx={tx_id}"
        )
        return True, None, decrypted_bundles

    @classmethod
    def parse_fhir_bundle(
        cls,
        fhir_json: str,
        care_context_ref: str,
    ) -> DecryptedClinicalBundle:
        """Parses a decrypted HL7 FHIR R4 Document Bundle JSON into structured clinical entities."""
        try:
            bundle_dict = json.loads(fhir_json)
        except Exception:
            bundle_dict = {}

        bundle_id = bundle_dict.get("id", str(uuid.uuid4()))
        composition_title = None
        author_name = None

        encounters: List[ParsedEncounter] = []
        diagnostic_reports: List[ParsedDiagnosticReport] = []
        prescriptions: List[ParsedPrescription] = []
        observations: List[ParsedObservation] = []

        entries = bundle_dict.get("entry", [])

        for entry in entries:
            res = entry.get("resource", {})
            res_type = res.get("resourceType")

            if res_type == "Composition":
                composition_title = res.get("title")
                author_list = res.get("author", [])
                if author_list and isinstance(author_list, list):
                    author_name = author_list[0].get("display")

            elif res_type == "Encounter":
                enc_id = res.get("id", str(uuid.uuid4()))
                status = res.get("status", "finished")
                enc_class = res.get("class", {}).get("code", "AMB")
                period = res.get("period", {})
                start_dt = cls._parse_iso_datetime(period.get("start"))
                end_dt = cls._parse_iso_datetime(period.get("end"))
                provider = res.get("serviceProvider", {}).get("display")

                encounters.append(
                    ParsedEncounter(
                        encounterId=enc_id,
                        status=status,
                        encounterClass=enc_class,
                        careContextReference=care_context_ref,
                        periodStart=start_dt,
                        periodEnd=end_dt,
                        serviceProvider=provider,
                    )
                )

            elif res_type == "DiagnosticReport":
                rep_id = res.get("id", str(uuid.uuid4()))
                codings = res.get("code", {}).get("coding", [{}])
                code = codings[0].get("code", "DIAGNOSTIC") if codings else "DIAGNOSTIC"
                display = codings[0].get("display", "Diagnostic Lab Report") if codings else "Diagnostic Lab Report"
                conclusion = res.get("conclusion")
                issued_dt = cls._parse_iso_datetime(res.get("issued") or res.get("effectiveDateTime"))
                status = res.get("status", "final")
                performers = res.get("performer", [{}])
                perf_name = performers[0].get("display") if performers else None

                diagnostic_reports.append(
                    ParsedDiagnosticReport(
                        reportId=rep_id,
                        code=code,
                        display=display,
                        conclusion=conclusion,
                        issuedDate=issued_dt,
                        status=status,
                        performer=perf_name,
                    )
                )

            elif res_type == "MedicationRequest":
                med_id = res.get("id", str(uuid.uuid4()))
                codings = res.get("medicationCodeableConcept", {}).get("coding", [{}])
                med_code = codings[0].get("code") if codings else None
                med_name = codings[0].get("display", "Prescribed Medication") if codings else "Prescribed Medication"
                dosage_inst = None
                dosage_list = res.get("dosageInstruction", [])
                if dosage_list and isinstance(dosage_list, list):
                    dosage_inst = dosage_list[0].get("text")
                status = res.get("status", "active")
                authored_on = cls._parse_iso_datetime(res.get("authoredOn"))

                prescriptions.append(
                    ParsedPrescription(
                        prescriptionId=med_id,
                        medicationCode=med_code,
                        medicationName=med_name,
                        dosageInstruction=dosage_inst,
                        status=status,
                        authoredOn=authored_on,
                    )
                )

            elif res_type == "Observation":
                obs_id = res.get("id", str(uuid.uuid4()))
                codings = res.get("code", {}).get("coding", [{}])
                code = codings[0].get("code", "OBS") if codings else "OBS"
                display = codings[0].get("display", "Clinical Observation") if codings else "Clinical Observation"
                val_quantity = res.get("valueQuantity", {})
                val_str = None
                unit_str = None
                if val_quantity:
                    val_str = str(val_quantity.get("value", ""))
                    unit_str = val_quantity.get("unit")
                elif "valueString" in res:
                    val_str = res.get("valueString")
                eff_dt = cls._parse_iso_datetime(res.get("effectiveDateTime"))

                observations.append(
                    ParsedObservation(
                        observationId=obs_id,
                        code=code,
                        display=display,
                        value=val_str,
                        unit=unit_str,
                        effectiveDateTime=eff_dt,
                    )
                )

        return DecryptedClinicalBundle(
            bundleId=bundle_id,
            careContextReference=care_context_ref,
            compositionTitle=composition_title,
            author=author_name,
            encounters=encounters,
            diagnosticReports=diagnostic_reports,
            prescriptions=prescriptions,
            observations=observations,
            rawFhirJson=fhir_json,
        )

    @classmethod
    def aggregate_patient_records(
        cls,
        patient_id: str,
        transaction_id: Optional[str] = None,
        consent_id: Optional[str] = None,
    ) -> HIUPatientRecordsResponse:
        """Aggregates all parsed clinical records imported for a patient into a unified response."""
        if transaction_id:
            bundles = hiu_record_store.get_transaction_records(transaction_id)
        else:
            bundles = hiu_record_store.get_patient_records(patient_id)

        encounters: List[ParsedEncounter] = []
        diagnostics: List[ParsedDiagnosticReport] = []
        prescriptions: List[ParsedPrescription] = []
        observations: List[ParsedObservation] = []

        for b in bundles:
            encounters.extend(b.encounters)
            diagnostics.extend(b.diagnosticReports)
            prescriptions.extend(b.prescriptions)
            observations.extend(b.observations)

        return HIUPatientRecordsResponse(
            patientId=patient_id,
            transactionId=transaction_id,
            consentId=consent_id,
            totalBundles=len(bundles),
            encounters=encounters,
            diagnosticReports=diagnostics,
            prescriptions=prescriptions,
            observations=observations,
            importedAt=datetime.now(timezone.utc),
        )

    @staticmethod
    def _parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Safely parses ISO datetime string into datetime object."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None
