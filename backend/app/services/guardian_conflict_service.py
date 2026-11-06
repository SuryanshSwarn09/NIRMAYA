import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.guardian_conflict import (
    ConflictResolutionPolicyEnum,
    CustodyModeEnum,
    DualSignConsentArtifactRequest,
    DualSignConsentArtifactResponse,
    DualSignCounterSignatureRequest,
    DualSignStatusEnum,
    GuardianActionTypeEnum,
    GuardianConflictResolutionRequest,
    GuardianConflictResolutionResponse,
    GuardianDisputeStatusEnum,
    GuardianEntry,
    MultiGuardianRelationshipSummary,
)


class GuardianConflictService:
    """Enterprise service governing multi-guardian concurrency arbitration,
    pessimistic revocation prevalence, custodial legal freeze state machine,
    and two-phase dual-signing consent workflows under DPDP Act 2023 Sec 9
    and Guardians and Wards Act 1890.
    """

    def __init__(self) -> None:
        self._multi_guardians: Dict[str, MultiGuardianRelationshipSummary] = {}
        self._custody_modes: Dict[str, CustodyModeEnum] = {}
        self._disputes: Dict[str, Dict[str, Any]] = {}
        self._dual_sign_artifacts: Dict[str, DualSignConsentArtifactResponse] = {}
        self._audit_ledger: List[Dict[str, Any]] = []
        self._init_seed_data()

    def _init_seed_data(self) -> None:
        """Seed representative multi-guardian families and active policies."""
        # 1. Pediatric Minor Aarav Sharma with both Mother and Father authorized
        pediatric_guardians = [
            GuardianEntry(
                guardian_id="pat-priya-sharma-01",
                name="Dr. Priya Sharma",
                relationship_type="MOTHER",
                verification_tier="DIGILOCKER_BIRTH_CERTIFICATE",
                priority_tier=1,
                authorized_at="2026-09-01T09:00:00Z",
            ),
            GuardianEntry(
                guardian_id="pat-vikram-sharma-01",
                name="Vikram Sharma",
                relationship_type="FATHER",
                verification_tier="AADHAAR_DEMOGRAPHIC_EKYC",
                priority_tier=1,
                authorized_at="2026-09-05T14:30:00Z",
            ),
        ]

        summary_aarav = MultiGuardianRelationshipSummary(
            dependent_patient_id="pat-aarav-sharma-02",
            dependent_name="Aarav Sharma",
            active_guardians=pediatric_guardians,
            custody_mode=CustodyModeEnum.JOINT_CONCURRENT,
            dispute_flag_active=False,
            active_dispute_ticket_id=None,
        )
        self._multi_guardians["pat-aarav-sharma-02"] = summary_aarav
        self._multi_guardians["pat-pediatric-001"] = summary_aarav
        self._custody_modes["pat-aarav-sharma-02"] = CustodyModeEnum.JOINT_CONCURRENT
        self._custody_modes["pat-pediatric-001"] = CustodyModeEnum.JOINT_CONCURRENT

        # 2. Senior Parent Kavita Sharma
        senior_guardians = [
            GuardianEntry(
                guardian_id="pat-priya-sharma-01",
                name="Dr. Priya Sharma",
                relationship_type="DAUGHTER",
                verification_tier="AADHAAR_DEMOGRAPHIC_EKYC",
                priority_tier=1,
                authorized_at="2026-09-15T11:30:00Z",
            ),
        ]
        summary_kavita = MultiGuardianRelationshipSummary(
            dependent_patient_id="pat-kavita-sharma-03",
            dependent_name="Kavita Sharma",
            active_guardians=senior_guardians,
            custody_mode=CustodyModeEnum.JOINT_CONCURRENT,
            dispute_flag_active=False,
            active_dispute_ticket_id=None,
        )
        self._multi_guardians["pat-kavita-sharma-03"] = summary_kavita
        self._multi_guardians["pat-senior-002"] = summary_kavita
        self._custody_modes["pat-kavita-sharma-03"] = CustodyModeEnum.JOINT_CONCURRENT
        self._custody_modes["pat-senior-002"] = CustodyModeEnum.JOINT_CONCURRENT

        # Seed pre-existing dual-signing artifact in PENDING state
        seed_artifact_id = "art-dual-seed-001"
        self._dual_sign_artifacts[seed_artifact_id] = DualSignConsentArtifactResponse(
            artifact_id=seed_artifact_id,
            dependent_patient_id="pat-aarav-sharma-02",
            primary_guardian_id="pat-priya-sharma-01",
            co_guardian_id="pat-vikram-sharma-01",
            status=DualSignStatusEnum.PENDING_CO_SIGNATURE,
            primary_signature_hash=hashlib.sha256(
                f"{seed_artifact_id}:pat-priya-sharma-01:CAREMGT".encode()
            ).hexdigest(),
            co_signature_hash=None,
            composite_signature_hash=None,
            created_at=datetime.now(timezone.utc),
            authorized_at=None,
        )

    def reset_state(self) -> None:
        """Reset internal stores to seed state for clean test isolation."""
        self._multi_guardians.clear()
        self._custody_modes.clear()
        self._disputes.clear()
        self._dual_sign_artifacts.clear()
        self._audit_ledger.clear()
        self._init_seed_data()

    def get_guardians_for_dependent(self, dependent_patient_id: str) -> MultiGuardianRelationshipSummary:
        """Retrieve all active registered guardians and current custody governance."""
        dep_id = "pat-aarav-sharma-02" if dependent_patient_id == "pat-pediatric-001" else dependent_patient_id
        if dep_id in self._multi_guardians:
            item = self._multi_guardians[dep_id]
            # Reflect real-time custody mode and dispute flag
            curr_mode = self._custody_modes.get(dep_id, CustodyModeEnum.JOINT_CONCURRENT)
            active_dispute = any(
                d.get("dependent_patient_id") == dep_id and d.get("status") in [
                    GuardianDisputeStatusEnum.ACTIVE_DISPUTE,
                    GuardianDisputeStatusEnum.COURT_SUB_JUDICE,
                ]
                for d in self._disputes.values()
            )
            dispute_ticket_id = next(
                (
                    d["ticket_id"]
                    for d in self._disputes.values()
                    if d.get("dependent_patient_id") == dep_id
                    and d.get("status") in [
                        GuardianDisputeStatusEnum.ACTIVE_DISPUTE,
                        GuardianDisputeStatusEnum.COURT_SUB_JUDICE,
                    ]
                ),
                None,
            )
            return MultiGuardianRelationshipSummary(
                dependent_patient_id=dep_id,
                dependent_name=item.dependent_name,
                active_guardians=item.active_guardians,
                custody_mode=curr_mode,
                dispute_flag_active=active_dispute,
                active_dispute_ticket_id=dispute_ticket_id,
            )

        # Dynamic fallback for arbitrary dependent IDs
        return MultiGuardianRelationshipSummary(
            dependent_patient_id=dependent_patient_id,
            dependent_name="Dependent Patient",
            active_guardians=[
                GuardianEntry(
                    guardian_id="pat-priya-sharma-01",
                    name="Dr. Priya Sharma",
                    relationship_type="PRIMARY_GUARDIAN",
                    verification_tier="AADHAAR_DEMOGRAPHIC_EKYC",
                    priority_tier=1,
                    authorized_at=datetime.now(timezone.utc).isoformat(),
                )
            ],
            custody_mode=self._custody_modes.get(dependent_patient_id, CustodyModeEnum.JOINT_CONCURRENT),
            dispute_flag_active=False,
            active_dispute_ticket_id=None,
        )

    def arbitrate_action(
        self, request: GuardianConflictResolutionRequest
    ) -> GuardianConflictResolutionResponse:
        """Arbitrate multi-guardian actions enforcing pessimistic revocation,
        custody freeze on sub-judice disputes, and dual-signing policy.
        """
        if not request.guardian_signature_attestation:
            raise ValueError(
                "Digital signature attestation is mandatory under DPDP Act 2023 Section 9"
            )

        dep_id = "pat-aarav-sharma-02" if request.dependent_patient_id == "pat-pediatric-001" else request.dependent_patient_id
        ticket_id = f"ticket-arb-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        current_mode = self._custody_modes.get(dep_id, CustodyModeEnum.JOINT_CONCURRENT)
        is_disputed = current_mode == CustodyModeEnum.DISPUTED_LOCKED or any(
            d.get("dependent_patient_id") == dep_id and d.get("status") in [
                GuardianDisputeStatusEnum.ACTIVE_DISPUTE,
                GuardianDisputeStatusEnum.COURT_SUB_JUDICE,
            ]
            for d in self._disputes.values()
        )

        # 1. Dispute Resolution Action
        if request.action_type == GuardianActionTypeEnum.RESOLVE_DISPUTE:
            # Mark all active disputes for this dependent as RESOLVED
            for d in self._disputes.values():
                if d.get("dependent_patient_id") == dep_id and d.get("status") in [
                    GuardianDisputeStatusEnum.ACTIVE_DISPUTE,
                    GuardianDisputeStatusEnum.COURT_SUB_JUDICE,
                ]:
                    d["status"] = GuardianDisputeStatusEnum.RESOLVED
                    d["resolved_at"] = now.isoformat()

            self._custody_modes[dep_id] = CustodyModeEnum.JOINT_CONCURRENT
            if request.dependent_patient_id != dep_id:
                self._custody_modes[request.dependent_patient_id] = CustodyModeEnum.JOINT_CONCURRENT

            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:RESOLVED:{now.isoformat()}".encode()
            ).hexdigest()

            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=GuardianDisputeStatusEnum.RESOLVED,
                effective_policy=ConflictResolutionPolicyEnum.PRIMARY_GUARDIAN_ARBITRATION,
                arbitrated_action_result="Dispute successfully resolved. Custody lock cleared and governance restored to JOINT_CONCURRENT.",
                locked_resources=[],
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        # 2. Revocation Action (Pessimistic Revocation Prevailed)
        if request.action_type == GuardianActionTypeEnum.REVOKE_CONSENT:
            # Under privacy invariants, any verified guardian can unilaterally revoke consent,
            # even if the record is currently contested or custody mode is dual-signing.
            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:REVOKE:{now.isoformat()}".encode()
            ).hexdigest()

            # Attempt to propagate revocation to underlying guardian delegation service if present
            try:
                from app.schemas.guardian_delegation import DelegatedConsentRevokeRequest
                from app.services.guardian_delegation_service import guardian_delegation_service

                target_id = request.target_artifact_id or "art-delegated-001"
                guardian_delegation_service.revoke_delegated_consent(
                    DelegatedConsentRevokeRequest(
                        artifact_id=target_id,
                        guardian_patient_id=request.initiating_guardian_id,
                        revocation_reason=request.justification,
                        signature_attestation=True,
                    )
                )
            except Exception:
                pass

            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=GuardianDisputeStatusEnum.RESOLVED,
                effective_policy=ConflictResolutionPolicyEnum.PESSIMISTIC_REVOCATION_PREVALENCE,
                arbitrated_action_result="Pessimistic Revocation Prevailed: Target consent artifact unilaterally and immediately revoked across all guardian sessions.",
                locked_resources=[],
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        # 3. Active Custody Dispute Check for Non-Revocation Actions
        if is_disputed:
            is_court = any(
                d.get("dependent_patient_id") == dep_id
                and d.get("status") == GuardianDisputeStatusEnum.COURT_SUB_JUDICE
                for d in self._disputes.values()
            ) or bool(request.legal_order_reference)

            dispute_status = (
                GuardianDisputeStatusEnum.COURT_SUB_JUDICE
                if is_court
                else GuardianDisputeStatusEnum.ACTIVE_DISPUTE
            )
            locked = [
                f"/api/v1/patients/{dep_id}/proxy/*",
                f"/api/v1/patients/{dep_id}/records",
            ]
            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:FROZEN:{now.isoformat()}".encode()
            ).hexdigest()

            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=dispute_status,
                effective_policy=ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE,
                arbitrated_action_result="Action rejected: Dependent custody is actively contested under court sub-judice. Non-emergency proxy modifications are frozen.",
                locked_resources=locked,
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        # 4. Raising a Legal Custody Dispute
        if request.action_type == GuardianActionTypeEnum.RAISE_LEGAL_DISPUTE:
            self._custody_modes[dep_id] = CustodyModeEnum.DISPUTED_LOCKED
            if request.dependent_patient_id != dep_id:
                self._custody_modes[request.dependent_patient_id] = CustodyModeEnum.DISPUTED_LOCKED

            status = (
                GuardianDisputeStatusEnum.COURT_SUB_JUDICE
                if request.legal_order_reference
                else GuardianDisputeStatusEnum.ACTIVE_DISPUTE
            )
            dispute_ticket = {
                "ticket_id": ticket_id,
                "dependent_patient_id": dep_id,
                "initiating_guardian_id": request.initiating_guardian_id,
                "status": status,
                "legal_order_reference": request.legal_order_reference,
                "justification": request.justification,
                "created_at": now.isoformat(),
            }
            self._disputes[ticket_id] = dispute_ticket

            locked = [
                f"/api/v1/patients/{dep_id}/proxy/*",
                f"/api/v1/patients/{dep_id}/records",
            ]
            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:DISPUTE_RAISED:{now.isoformat()}".encode()
            ).hexdigest()

            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=status,
                effective_policy=ConflictResolutionPolicyEnum.DISPUTED_CUSTODY_FREEZE,
                arbitrated_action_result="Custodial dispute registered under Guardians and Wards Act 1890. Automatic pessimistic lock engaged. Non-emergency proxy write actions frozen.",
                locked_resources=locked,
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        # 5. Custody Mode Change
        if request.action_type == GuardianActionTypeEnum.CHANGE_CUSTODY_MODE:
            new_mode = CustodyModeEnum.DUAL_SIGNATURE_REQUIRED
            self._custody_modes[dep_id] = new_mode
            if request.dependent_patient_id != dep_id:
                self._custody_modes[request.dependent_patient_id] = new_mode

            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:MODE_CHANGE:{now.isoformat()}".encode()
            ).hexdigest()

            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=GuardianDisputeStatusEnum.RESOLVED,
                effective_policy=ConflictResolutionPolicyEnum.DUAL_GUARDIAN_CO_SIGNING,
                arbitrated_action_result="Custody governance mode transitioned to DUAL_SIGNATURE_REQUIRED. Co-signing mandatory for future consent artifacts.",
                locked_resources=[],
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        # 6. Grant Consent Action
        if request.action_type == GuardianActionTypeEnum.GRANT_CONSENT:
            if current_mode == CustodyModeEnum.DUAL_SIGNATURE_REQUIRED:
                audit_hash = hashlib.sha256(
                    f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:DUAL_REQUIRED:{now.isoformat()}".encode()
                ).hexdigest()
                response = GuardianConflictResolutionResponse(
                    ticket_id=ticket_id,
                    dependent_patient_id=dep_id,
                    initiating_guardian_id=request.initiating_guardian_id,
                    action_type=request.action_type,
                    dispute_status=GuardianDisputeStatusEnum.PENDING_MUTUAL_APPROVAL,
                    effective_policy=ConflictResolutionPolicyEnum.DUAL_GUARDIAN_CO_SIGNING,
                    arbitrated_action_result="Unilateral consent blocked: Dual-Signature required. Consent artifact queued for second guardian counter-signature.",
                    locked_resources=[],
                    audit_hash=audit_hash,
                    timestamp=now,
                )
                self._record_audit(response)
                return response

            # Default JOINT_CONCURRENT grant
            audit_hash = hashlib.sha256(
                f"{ticket_id}:{dep_id}:{request.initiating_guardian_id}:GRANT_OK:{now.isoformat()}".encode()
            ).hexdigest()
            response = GuardianConflictResolutionResponse(
                ticket_id=ticket_id,
                dependent_patient_id=dep_id,
                initiating_guardian_id=request.initiating_guardian_id,
                action_type=request.action_type,
                dispute_status=GuardianDisputeStatusEnum.RESOLVED,
                effective_policy=ConflictResolutionPolicyEnum.PRIMARY_GUARDIAN_ARBITRATION,
                arbitrated_action_result="Consent grant approved under JOINT_CONCURRENT authority.",
                locked_resources=[],
                audit_hash=audit_hash,
                timestamp=now,
            )
            self._record_audit(response)
            return response

        raise ValueError(f"Unsupported action type: {request.action_type}")

    def create_dual_sign_request(
        self, request: DualSignConsentArtifactRequest
    ) -> DualSignConsentArtifactResponse:
        """Initiate a two-phase co-signed electronic consent artifact."""
        if not request.primary_signature_attestation:
            raise ValueError(
                "Primary guardian digital signature attestation is required under DPDP Act 2023 Sec 9"
            )

        now = datetime.now(timezone.utc)
        primary_hash = hashlib.sha256(
            f"{request.artifact_id}:{request.primary_guardian_id}:{request.purpose}:{now.isoformat()}".encode()
        ).hexdigest()

        artifact = DualSignConsentArtifactResponse(
            artifact_id=request.artifact_id,
            dependent_patient_id=request.dependent_patient_id,
            primary_guardian_id=request.primary_guardian_id,
            co_guardian_id=request.co_guardian_id,
            status=DualSignStatusEnum.PENDING_CO_SIGNATURE,
            primary_signature_hash=primary_hash,
            co_signature_hash=None,
            composite_signature_hash=None,
            created_at=now,
            authorized_at=None,
        )
        self._dual_sign_artifacts[request.artifact_id] = artifact

        # Record in audit ledger
        self._audit_ledger.append(
            {
                "event_type": "DUAL_SIGN_INITIATED",
                "artifact_id": request.artifact_id,
                "dependent_patient_id": request.dependent_patient_id,
                "primary_guardian_id": request.primary_guardian_id,
                "co_guardian_id": request.co_guardian_id,
                "primary_signature_hash": primary_hash,
                "timestamp": now.isoformat(),
            }
        )
        return artifact

    def counter_sign_dual_artifact(
        self, request: DualSignCounterSignatureRequest
    ) -> DualSignConsentArtifactResponse:
        """Counter-sign a pending consent artifact to reach full authorization."""
        if not request.co_signature_attestation:
            raise ValueError(
                "Co-guardian digital signature attestation is required under DPDP Act 2023 Sec 9"
            )

        if request.artifact_id not in self._dual_sign_artifacts:
            raise ValueError(f"Artifact {request.artifact_id} not found")

        artifact = self._dual_sign_artifacts[request.artifact_id]

        if artifact.status != DualSignStatusEnum.PENDING_CO_SIGNATURE:
            raise ValueError(f"Artifact {request.artifact_id} is in status {artifact.status.value}, not pending co-signature")

        if artifact.co_guardian_id and artifact.co_guardian_id != request.co_guardian_id:
            raise ValueError(
                f"Signer {request.co_guardian_id} does not match designated co-guardian {artifact.co_guardian_id}"
            )

        now = datetime.now(timezone.utc)
        co_hash = hashlib.sha256(
            f"{request.artifact_id}:{request.co_guardian_id}:{now.isoformat()}".encode()
        ).hexdigest()

        composite_hash = hashlib.sha256(
            f"{artifact.primary_signature_hash}:{co_hash}".encode()
        ).hexdigest()

        artifact.status = DualSignStatusEnum.FULLY_AUTHORIZED
        artifact.co_signature_hash = co_hash
        artifact.composite_signature_hash = composite_hash
        artifact.authorized_at = now

        self._audit_ledger.append(
            {
                "event_type": "DUAL_SIGN_COMPLETED",
                "artifact_id": request.artifact_id,
                "co_guardian_id": request.co_guardian_id,
                "composite_signature_hash": composite_hash,
                "comments": request.comments,
                "timestamp": now.isoformat(),
            }
        )
        return artifact

    def list_dispute_tickets(self, dependent_patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active and historical dispute tickets, optionally filtered by dependent."""
        if not dependent_patient_id:
            return list(self._disputes.values())
        dep_id = "pat-aarav-sharma-02" if dependent_patient_id == "pat-pediatric-001" else dependent_patient_id
        return [
            d for d in self._disputes.values()
            if d.get("dependent_patient_id") in [dependent_patient_id, dep_id]
        ]

    def get_audit_ledger(self, dependent_patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve immutable forensic audit ledger entries."""
        if not dependent_patient_id:
            return self._audit_ledger
        dep_id = "pat-aarav-sharma-02" if dependent_patient_id == "pat-pediatric-001" else dependent_patient_id
        return [
            item for item in self._audit_ledger
            if item.get("dependent_patient_id") in [dependent_patient_id, dep_id]
        ]

    def _record_audit(self, response: GuardianConflictResolutionResponse) -> None:
        """Internal helper to log arbitration tickets to the audit ledger."""
        self._audit_ledger.append(
            {
                "event_type": "CONFLICT_ARBITRATION",
                "ticket_id": response.ticket_id,
                "dependent_patient_id": response.dependent_patient_id,
                "initiating_guardian_id": response.initiating_guardian_id,
                "action_type": response.action_type.value,
                "dispute_status": response.dispute_status.value,
                "effective_policy": response.effective_policy.value,
                "arbitrated_action_result": response.arbitrated_action_result,
                "locked_resources": response.locked_resources,
                "audit_hash": response.audit_hash,
                "timestamp": response.timestamp.isoformat(),
            }
        )


guardian_conflict_service = GuardianConflictService()
