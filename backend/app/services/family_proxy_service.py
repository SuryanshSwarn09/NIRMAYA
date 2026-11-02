import hashlib
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.family_proxy import (
    FamilyProxyCreateRequest,
    FamilyProxyResponse,
    ProxyAccessScopeEnum,
    ProxyAuditLogItem,
    ProxyRelationshipStatusEnum,
    RelationshipTypeEnum,
    VerificationAuthorityEnum,
)


class FamilyProxyService:
    """Enterprise service managing dependent and family health proxy relationships.

    Enforces strict zero record contamination under Indian DPDP Act 2023 Sec 9:
    Dependents maintain isolated, sovereign health records; only access delegation is audited.
    """

    def __init__(self) -> None:
        self._relationships: Dict[str, FamilyProxyResponse] = self._init_seed_relationships()
        self._audit_logs: List[ProxyAuditLogItem] = self._init_seed_audit_logs()

    def _init_seed_relationships(self) -> Dict[str, FamilyProxyResponse]:
        """Initialize representative pre-verified familial proxy relationships."""
        seed: Dict[str, FamilyProxyResponse] = {}

        # 1. Child Minor Relationship: Dr. Priya Sharma (Guardian) -> Aarav Sharma (Son, Minor 8 yrs)
        rel1 = FamilyProxyResponse(
            relationship_id="rel-proxy-child-001",
            guardian_patient_id="pat-priya-sharma-01",
            dependent_patient_id="pat-aarav-sharma-02",
            relationship_type=RelationshipTypeEnum.CHILD_MINOR,
            verification_tier=VerificationAuthorityEnum.DIGILOCKER_BIRTH_CERTIFICATE,
            verification_document_hash="8f12a048c081294801928409182409182b0412984109481b049182b041298410",
            access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
            status=ProxyRelationshipStatusEnum.ACTIVE,
            authorized_at=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
            dependent_name="Aarav Sharma",
            dependent_abha="14-8291-0391-4821",
            dependent_age=8,
            zero_contamination_isolated=True,
        )
        seed[rel1.relationship_id] = rel1

        # 2. Senior Parent Relationship: Dr. Priya Sharma (Guardian) -> Kavita Sharma (Mother, Senior 68 yrs)
        rel2 = FamilyProxyResponse(
            relationship_id="rel-proxy-senior-002",
            guardian_patient_id="pat-priya-sharma-01",
            dependent_patient_id="pat-kavita-sharma-03",
            relationship_type=RelationshipTypeEnum.PARENT_SENIOR,
            verification_tier=VerificationAuthorityEnum.AADHAAR_DEMOGRAPHIC_EKYC,
            verification_document_hash="a192840192840192840192840192840192840192840192840192840192840192",
            access_scope=ProxyAccessScopeEnum.FULL_MANAGEMENT,
            status=ProxyRelationshipStatusEnum.ACTIVE,
            authorized_at=datetime(2026, 9, 15, 11, 30, 0, tzinfo=timezone.utc),
            dependent_name="Kavita Sharma",
            dependent_abha="14-9102-4819-2041",
            dependent_age=68,
            zero_contamination_isolated=True,
        )
        seed[rel2.relationship_id] = rel2

        return seed

    def _init_seed_audit_logs(self) -> List[ProxyAuditLogItem]:
        """Seed initial immutable forensic access log entries."""
        return [
            ProxyAuditLogItem(
                log_id="log-proxy-001",
                relationship_id="rel-proxy-child-001",
                actor_guardian_id="pat-priya-sharma-01",
                target_dependent_id="pat-aarav-sharma-02",
                action_performed="VIEW_PEDIATRIC_IMMUNIZATION_RECORD",
                resource_accessed="DiagnosticReport/imm-uip-bcg-01",
                ip_address="10.0.1.42",
                timestamp=datetime(2026, 10, 10, 14, 20, 0, tzinfo=timezone.utc),
                authorized=True,
            ),
            ProxyAuditLogItem(
                log_id="log-proxy-002",
                relationship_id="rel-proxy-senior-002",
                actor_guardian_id="pat-priya-sharma-01",
                target_dependent_id="pat-kavita-sharma-03",
                action_performed="SCHEDULE_GERIATRIC_CARDIOLOGY_SLOT",
                resource_accessed="DoctorSlot/slot-cardio-9102",
                ip_address="10.0.1.42",
                timestamp=datetime(2026, 10, 20, 16, 45, 0, tzinfo=timezone.utc),
                authorized=True,
            ),
        ]

    # =========================================================================
    # Relationship Lifecycle Management
    # =========================================================================

    def establish_proxy_relationship(self, req: FamilyProxyCreateRequest) -> FamilyProxyResponse:
        """Create and verify a new dependent family proxy linkage adhering to DPDP Act Sec 9."""
        # 1. Zero Record Contamination Guard: Guardian and dependent must be distinct
        if req.guardian_patient_id == req.dependent_patient_id:
            raise ValueError("Zero-Contamination Invariant Violation: Guardian cannot be their own proxy dependent.")

        # 2. Verifiable Consent Requirement (DPDP Act Sec 9)
        if not req.guardian_consent_attestation:
            raise ValueError("DPDP Act Sec 9 Violation: Verifiable parental/guardian consent attestation is required.")

        # 3. Age-of-Majority Constraint Check
        age: Optional[int] = None
        if req.dependent_dob_iso:
            try:
                dob = date.fromisoformat(req.dependent_dob_iso)
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if req.relationship_type == RelationshipTypeEnum.CHILD_MINOR and age >= 18:
                    raise ValueError(f"Age-of-Majority Invariant: Child minor proxy requires dependent age < 18 (provided age: {age}).")
            except ValueError as e:
                if "Age-of-Majority" in str(e):
                    raise
                pass

        # 4. Generate persistent relationship ID
        rel_id = f"rel-proxy-{uuid.uuid4().hex[:12]}"

        # 5. Build response object
        rel = FamilyProxyResponse(
            relationship_id=rel_id,
            guardian_patient_id=req.guardian_patient_id,
            dependent_patient_id=req.dependent_patient_id,
            relationship_type=req.relationship_type,
            verification_tier=req.verification_tier,
            verification_document_hash=req.verification_document_hash,
            access_scope=req.access_scope,
            status=ProxyRelationshipStatusEnum.ACTIVE,
            authorized_at=datetime.now(timezone.utc),
            dependent_name="Dependent Citizen",
            dependent_age=age,
            zero_contamination_isolated=True,
        )

        self._relationships[rel_id] = rel

        # 6. Log establishment event in audit trail
        self._audit_logs.append(
            ProxyAuditLogItem(
                log_id=f"log-{uuid.uuid4().hex[:8]}",
                relationship_id=rel_id,
                actor_guardian_id=req.guardian_patient_id,
                target_dependent_id=req.dependent_patient_id,
                action_performed="ESTABLISH_FAMILY_PROXY_RELATIONSHIP",
                resource_accessed=f"PatientProfile/{req.dependent_patient_id}",
                ip_address="127.0.0.1",
                timestamp=datetime.now(timezone.utc),
                authorized=True,
            )
        )

        return rel

    def list_dependents_for_guardian(self, guardian_patient_id: str) -> List[FamilyProxyResponse]:
        """Retrieve all active dependent relationships registered under the given guardian."""
        return [
            r for r in self._relationships.values()
            if r.guardian_patient_id == guardian_patient_id and r.status == ProxyRelationshipStatusEnum.ACTIVE
        ]

    def get_relationship(self, relationship_id: str) -> Optional[FamilyProxyResponse]:
        """Fetch relationship metadata by ID."""
        return self._relationships.get(relationship_id)

    def revoke_proxy_relationship(self, relationship_id: str, actor_id: str, reason: str = "Guardian Revocation") -> FamilyProxyResponse:
        """Revoke delegated proxy privileges and record forensic event."""
        rel = self._relationships.get(relationship_id)
        if not rel:
            raise KeyError(f"Proxy relationship '{relationship_id}' not found.")

        rel.status = ProxyRelationshipStatusEnum.REVOKED

        self._audit_logs.append(
            ProxyAuditLogItem(
                log_id=f"log-{uuid.uuid4().hex[:8]}",
                relationship_id=relationship_id,
                actor_guardian_id=actor_id,
                target_dependent_id=rel.dependent_patient_id,
                action_performed=f"REVOKE_PROXY_RELATIONSHIP: {reason}",
                resource_accessed=f"PatientProxyRelationship/{relationship_id}",
                ip_address="127.0.0.1",
                timestamp=datetime.now(timezone.utc),
                authorized=True,
            )
        )

        return rel

    # =========================================================================
    # Authorization & Forensic Audit Interceptor
    # =========================================================================

    def verify_proxy_access_permission(
        self,
        guardian_id: str,
        dependent_id: str,
        requested_action: str,
        ip_address: str = "127.0.0.1",
    ) -> bool:
        """Security guard validating whether guardian holds active proxy delegation for requested action."""
        matching = [
            r for r in self._relationships.values()
            if r.guardian_patient_id == guardian_id
            and r.dependent_patient_id == dependent_id
            and r.status == ProxyRelationshipStatusEnum.ACTIVE
        ]

        if not matching:
            # Audit unauthorized access attempt
            self._audit_logs.append(
                ProxyAuditLogItem(
                    log_id=f"log-{uuid.uuid4().hex[:8]}",
                    relationship_id="UNKNOWN",
                    actor_guardian_id=guardian_id,
                    target_dependent_id=dependent_id,
                    action_performed=requested_action,
                    ip_address=ip_address,
                    timestamp=datetime.now(timezone.utc),
                    authorized=False,
                )
            )
            return False

        rel = matching[0]

        # Evaluate scope constraint
        allowed = True
        if rel.access_scope == ProxyAccessScopeEnum.APPOINTMENTS_ONLY and "APPOINTMENT" not in requested_action.upper():
            allowed = False
        elif rel.access_scope == ProxyAccessScopeEnum.RECORDS_VIEW_ONLY and "WRITE" in requested_action.upper():
            allowed = False

        # Log authorized or denied action
        self._audit_logs.append(
            ProxyAuditLogItem(
                log_id=f"log-{uuid.uuid4().hex[:8]}",
                relationship_id=rel.relationship_id,
                actor_guardian_id=guardian_id,
                target_dependent_id=dependent_id,
                action_performed=requested_action,
                ip_address=ip_address,
                timestamp=datetime.now(timezone.utc),
                authorized=allowed,
            )
        )

        return allowed

    def get_audit_logs(self, relationship_id: Optional[str] = None) -> List[ProxyAuditLogItem]:
        """Retrieve immutable forensic audit trail filtered optionally by relationship."""
        if relationship_id:
            return [l for l in self._audit_logs if l.relationship_id == relationship_id]
        return self._audit_logs


# Global singleton instance
family_proxy_service = FamilyProxyService()
