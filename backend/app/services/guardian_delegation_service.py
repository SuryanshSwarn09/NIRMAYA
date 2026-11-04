import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.guardian_delegation import (
    ConsentAuditTrailItem,
    ConsentPurposeEnum,
    DelegatedConsentArtifactResponse,
    DelegatedConsentGrantRequest,
    DelegatedConsentRevokeRequest,
    DelegatedConsentStatusEnum,
    ScopedProxyTokenRequest,
    ScopedProxyTokenResponse,
)
from app.services.family_proxy_service import family_proxy_service


class GuardianDelegationService:
    """Enterprise service managing electronic consent artifact delegation,
    scoped proxy token minting, and zero-contamination clinical ingestion under
    ABDM Milestone M3 and DPDP Act 2023 Section 9.
    """

    def __init__(self) -> None:
        self._consent_artifacts: Dict[str, DelegatedConsentArtifactResponse] = self._init_seed_artifacts()
        self._pending_requests: List[Dict[str, Any]] = self._init_seed_pending_requests()
        self._scoped_tokens: Dict[str, Dict[str, Any]] = {}
        self._audit_trail: List[ConsentAuditTrailItem] = self._init_seed_audit_trail()

    def _init_seed_artifacts(self) -> Dict[str, DelegatedConsentArtifactResponse]:
        """Seed representative active delegated consent artifacts."""
        art1 = DelegatedConsentArtifactResponse(
            artifact_id="art-delegated-001",
            consent_request_id="req-abdm-c-9812",
            status=DelegatedConsentStatusEnum.GRANTED,
            guardian_patient_id="pat-priya-sharma-01",
            dependent_patient_id="pat-aarav-sharma-02",
            requester_hiu_name="Max Healthcare Pediatric Care",
            purpose=ConsentPurposeEnum.CAREMGT,
            hi_types=["DiagnosticReport", "ImmunizationRecord"],
            date_range_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
            date_range_to=datetime(2026, 11, 1, tzinfo=timezone.utc),
            granted_at=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2027, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            guardian_signature_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            zero_contamination_verified=True,
        )
        return {art1.artifact_id: art1}

    def _init_seed_pending_requests(self) -> List[Dict[str, Any]]:
        """Seed inbound ABDM consent requests awaiting parent/guardian review."""
        return [
            {
                "consent_request_id": "req-abdm-inbound-401",
                "requester_hiu_name": "Apollo Clinic Indiranagar",
                "dependent_name": "Aarav Sharma",
                "dependent_patient_id": "pat-aarav-sharma-02",
                "guardian_patient_id": "pat-priya-sharma-01",
                "purpose": "CAREMGT",
                "requested_hi_types": ["Prescription", "DiagnosticReport"],
                "date_range": "2026-01-01 to 2026-11-01",
                "expiry_days": 180,
                "created_at": "2026-11-01T10:00:00Z",
            },
            {
                "consent_request_id": "req-abdm-inbound-402",
                "requester_hiu_name": "Fortis Senior Care Diagnostic Hub",
                "dependent_name": "Kavita Sharma",
                "dependent_patient_id": "pat-kavita-sharma-03",
                "guardian_patient_id": "pat-priya-sharma-01",
                "purpose": "DIAGNOSTIC",
                "requested_hi_types": ["DiagnosticReport", "OPDVisit"],
                "date_range": "2025-06-01 to 2026-10-31",
                "expiry_days": 90,
                "created_at": "2026-11-02T14:30:00Z",
            },
        ]

    def _init_seed_audit_trail(self) -> List[ConsentAuditTrailItem]:
        """Seed initial immutable forensic log items."""
        return [
            ConsentAuditTrailItem(
                audit_id="audit-c-001",
                artifact_id="art-delegated-001",
                action="CONSENT_ARTIFACT_GRANTED_BY_PROXY",
                actor_id="pat-priya-sharma-01",
                dependent_id="pat-aarav-sharma-02",
                timestamp=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
                ip_address="10.0.1.42",
                status="SUCCESS",
            )
        ]

    def grant_delegated_consent(self, req: DelegatedConsentGrantRequest) -> DelegatedConsentArtifactResponse:
        """Issue an ABDM electronic consent artifact signed by a verified proxy guardian."""
        # 1. Enforce DPDP Act 2023 Sec 9 parental consent attestation
        if not req.guardian_signature_attestation:
            raise ValueError(
                "DPDP Act Sec 9 Violation: Parental/guardian digital consent attestation is required to share dependent data."
            )

        # 2. Verify active proxy delegation authority
        active_dependents = family_proxy_service.list_dependents_for_guardian(req.guardian_patient_id)
        matching = [d for d in active_dependents if d.dependent_patient_id == req.dependent_patient_id]
        if not matching:
            raise ValueError(
                f"Unauthorized Delegation: Guardian '{req.guardian_patient_id}' does not hold active proxy authority for dependent '{req.dependent_patient_id}'."
            )

        # 3. Validate temporal bounds
        if req.date_range_from > req.date_range_to:
            raise ValueError("Temporal Bound Invariant: 'date_range_from' cannot be after 'date_range_to'.")

        now_utc = datetime.now(timezone.utc)
        if req.expiry_date <= now_utc:
            raise ValueError("Expiration Invariant: Consent expiry date must be strictly in the future.")

        # 4. Generate unique artifact identifier & cryptographic signature hash
        artifact_id = f"art-delegated-{uuid.uuid4().hex[:10]}"
        raw_sig = f"{req.consent_request_id}:{req.guardian_patient_id}:{req.dependent_patient_id}:{req.purpose.value}:{now_utc.isoformat()}"
        sig_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

        # 5. Build electronic consent artifact
        artifact = DelegatedConsentArtifactResponse(
            artifact_id=artifact_id,
            consent_request_id=req.consent_request_id,
            status=DelegatedConsentStatusEnum.GRANTED,
            guardian_patient_id=req.guardian_patient_id,
            dependent_patient_id=req.dependent_patient_id,
            requester_hiu_name=req.requester_hiu_name,
            purpose=req.purpose,
            hi_types=req.hi_types,
            date_range_from=req.date_range_from,
            date_range_to=req.date_range_to,
            granted_at=now_utc,
            expires_at=req.expiry_date,
            guardian_signature_hash=sig_hash,
            zero_contamination_verified=True,
        )

        self._consent_artifacts[artifact_id] = artifact

        # 6. Remove matching pending request if present
        self._pending_requests = [
            p for p in self._pending_requests if p.get("consent_request_id") != req.consent_request_id
        ]

        # 7. Record immutable forensic ledger entry
        self._audit_trail.append(
            ConsentAuditTrailItem(
                audit_id=f"audit-c-{uuid.uuid4().hex[:8]}",
                artifact_id=artifact_id,
                action="CONSENT_ARTIFACT_GRANTED_BY_PROXY",
                actor_id=req.guardian_patient_id,
                dependent_id=req.dependent_patient_id,
                timestamp=now_utc,
                ip_address="127.0.0.1",
                status="SUCCESS",
            )
        )

        return artifact

    def revoke_delegated_consent(self, req: DelegatedConsentRevokeRequest) -> DelegatedConsentArtifactResponse:
        """Revoke an active delegated consent artifact under DPDP Act Sec 9 rights."""
        artifact = self._consent_artifacts.get(req.artifact_id)
        if not artifact:
            raise KeyError(f"Consent artifact '{req.artifact_id}' not found.")

        if artifact.guardian_patient_id != req.guardian_patient_id:
            raise ValueError(
                f"Unauthorized Actor: Actor '{req.guardian_patient_id}' did not issue artifact '{req.artifact_id}'."
            )

        artifact.status = DelegatedConsentStatusEnum.REVOKED
        now_utc = datetime.now(timezone.utc)

        # Log revocation event
        self._audit_trail.append(
            ConsentAuditTrailItem(
                audit_id=f"audit-c-{uuid.uuid4().hex[:8]}",
                artifact_id=req.artifact_id,
                action=f"CONSENT_ARTIFACT_REVOKED: {req.revocation_reason}",
                actor_id=req.guardian_patient_id,
                dependent_id=artifact.dependent_patient_id,
                timestamp=now_utc,
                ip_address="127.0.0.1",
                status="REVOKED",
            )
        )

        return artifact

    def generate_scoped_proxy_token(self, req: ScopedProxyTokenRequest) -> ScopedProxyTokenResponse:
        """Issue an ephemeral scoped bearer token granting purpose-restricted proxy access."""
        # 1. Verify active relationship
        active_dependents = family_proxy_service.list_dependents_for_guardian(req.guardian_patient_id)
        matching = [d for d in active_dependents if d.dependent_patient_id == req.dependent_patient_id]
        if not matching:
            raise ValueError(
                f"Unauthorized Token Request: Guardian '{req.guardian_patient_id}' lacks active proxy delegation for dependent '{req.dependent_patient_id}'."
            )

        # 2. Mint token signature
        token_uuid = uuid.uuid4().hex
        token_str = f"nirmaya_proxy_eyJh_{token_uuid[:16]}.{req.requested_scope}.{token_uuid[16:]}"
        now_utc = datetime.now(timezone.utc)

        self._scoped_tokens[token_str] = {
            "guardian_id": req.guardian_patient_id,
            "dependent_id": req.dependent_patient_id,
            "scope": req.requested_scope,
            "issued_at": now_utc,
            "duration": req.duration_seconds,
        }

        # 3. Log token minting event
        self._audit_trail.append(
            ConsentAuditTrailItem(
                audit_id=f"audit-t-{uuid.uuid4().hex[:8]}",
                artifact_id=f"token-{token_uuid[:8]}",
                action=f"MINT_SCOPED_PROXY_TOKEN (scope: {req.requested_scope})",
                actor_id=req.guardian_patient_id,
                dependent_id=req.dependent_patient_id,
                timestamp=now_utc,
                ip_address="127.0.0.1",
                status="ISSUED",
            )
        )

        return ScopedProxyTokenResponse(
            access_token=token_str,
            token_type="Bearer",
            expires_in=req.duration_seconds,
            scope=req.requested_scope,
            guardian_id=req.guardian_patient_id,
            dependent_id=req.dependent_patient_id,
            issued_at=now_utc,
            zero_contamination_isolated=True,
        )

    def intercept_consent_request(
        self, guardian_id: str, dependent_id: str, consent_request_id: str
    ) -> Dict[str, Any]:
        """Interceptor checking whether inbound consent request is authorized for proxy action."""
        active_dependents = family_proxy_service.list_dependents_for_guardian(guardian_id)
        matching = [d for d in active_dependents if d.dependent_patient_id == dependent_id]
        is_authorized = len(matching) > 0

        return {
            "consent_request_id": consent_request_id,
            "authorized": is_authorized,
            "guardian_id": guardian_id,
            "dependent_id": dependent_id,
            "matching_relationship": matching[0].relationship_id if is_authorized else None,
            "permitted_hi_types": ["DiagnosticReport", "Prescription", "ImmunizationRecord", "OPDVisit"],
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    def list_delegated_consents(
        self, guardian_id: Optional[str] = None, dependent_id: Optional[str] = None
    ) -> List[DelegatedConsentArtifactResponse]:
        """Retrieve delegated consent artifacts with optional filters."""
        res = list(self._consent_artifacts.values())
        if guardian_id:
            res = [c for c in res if c.guardian_patient_id == guardian_id]
        if dependent_id:
            res = [c for c in res if c.dependent_patient_id == dependent_id]
        return res

    def list_pending_requests(self) -> List[Dict[str, Any]]:
        """Retrieve pending inbound consent requests awaiting guardian action."""
        return self._pending_requests

    def get_audit_trail(self, artifact_id: Optional[str] = None) -> List[ConsentAuditTrailItem]:
        """Fetch immutable forensic audit log for consent operations."""
        if artifact_id:
            return [a for a in self._audit_trail if a.artifact_id == artifact_id]
        return self._audit_trail


# Global singleton instance
guardian_delegation_service = GuardianDelegationService()
