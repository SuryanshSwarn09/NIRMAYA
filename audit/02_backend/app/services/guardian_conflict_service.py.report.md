# Codebase Technical Audit Report: `backend/app/services/guardian_conflict_service.py`

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`guardian_conflict_service.py` governs multi-guardian arbitration, custody state machine transitions, pessimistic revocation precedence, and two-phase dual-signing consent workflows under the Digital Personal Data Protection (DPDP) Act 2023 Section 9 and the Guardians and Wards Act 1890. It arbitrates competing decisions among verified parents and legal guardians of pediatric minors and geriatric dependents, enforcing a pessimistic revocation invariant whereby any single guardian can unilaterally terminate data sharing or proxy access regardless of conflicting approvals.

### System Topology & Concurrency Model
```
   [ Guardian A (Mother) ]       [ Guardian B (Father) ]
              \                             /
               \                           /
      [ Consent Revoke / Grant / Dispute Action ]
                          |
                          v
         +----------------------------------+
         |     GuardianConflictService      |
         +----------------------------------+
         | - Pessimistic Revocation Check   |
         | - Custodial Freeze Engine        |
         | - Dual-Signing Co-Signature FSM  |
         | - SHA-256 Composite Ledger       |
         +----------------------------------+
               /                      \
              v                        v
    [ Delegated Consent ]    [ Forensic Audit Ledger ]
    (Unilateral Invalidate)  (Volatile Memory Dict)
```

### Module Metadata & Imports/Exports
- **Module Path:** `backend/app/services/guardian_conflict_service.py`
- **Component Classification:** Core Business & Governance Service / Legal Custody Arbiter
- **Lines of Code:** 552 LOC
- **Imports:** `hashlib`, `uuid`, `datetime`, `typing`, `app.schemas.guardian_conflict.*`
- **Primary Export:** `guardian_conflict_service` (Global Singleton Instance)

---

## Layer B: Plain-Language Developer Walkthrough

The service models family units where multiple guardians share legal authority over a dependent patient. Upon instantiation, `_init_seed_data()` bootstraps representative family structures: a pediatric minor (Aarav Sharma) with dual authorized guardians (Dr. Priya Sharma as Mother and Vikram Sharma as Father) operating under `JOINT_CONCURRENT` custody, and a senior citizen (Kavita Sharma) with an adult daughter guardian.

When an action is submitted via `arbitrate_action()`, the engine first verifies the mandatory presence of `guardian_signature_attestation`. It then evaluates the action type:
1. `RESOLVE_DISPUTE`: Clears active or court-ordered custody dispute flags, transitions the custody state back to `JOINT_CONCURRENT`, and logs an arbitration ticket.
2. `REVOKE_CONSENT`: Executes the foundational privacy rule—Pessimistic Revocation Prevailed. Any guardian can unilaterally revoke consent even if the other guardian approved it or custody is contested. It attempts to notify `guardian_delegation_service` and marks the revocation as immediately effective.
3. `DISPUTED_CUSTODY_FREEZE`: If an active dispute exists (or is raised via `RAISE_LEGAL_DISPUTE`), all non-emergency proxy read/write operations on `/api/v1/patients/{dep_id}/proxy/*` and `/records` are frozen under court sub-judice governance.
4. `GRANT_CONSENT`: If custody mode is `DUAL_SIGNATURE_REQUIRED`, unilateral approval is blocked and routed to the two-phase dual-signing workflow (`create_dual_sign_request` and `counter_sign_dual_artifact`), which requires both guardians to compute cryptographic signature hashes before full authorization is granted.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Pessimistic Revocation Precedence
Under the DPDP Act 2023 Section 9, parental consent for a minor's personal data processing can be withdrawn at any time. When multiple guardians exist, NIRMAYA mandates that withdrawal always takes precedence over continuance. The service enforces this invariant at line 223 by immediately terminating authorizations and bypassing dual-signature requirements.

### Invariant 2: Custodial Legal Freeze State Machine
When a family court order or legal contestation is submitted under the Guardians and Wards Act 1890, the dependent's profile transitions to `CustodyModeEnum.DISPUTED_LOCKED`. The state machine guarantees that no clinical proxy records can be accessed or modified by either party until formal dispute resolution or judicial clearance is recorded.

### Invariant 3: Composite Hash Attestation
In dual-signature custody modes, authorization requires a composite hash:
$$\text{CompositeHash} = \text{SHA-256}(\text{PrimarySignatureHash} \parallel \text{CoSignatureHash})$$
This ensures mathematical non-repudiation and guarantees neither party can alter the consent terms after the initial signature has been affixed.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
|---|---|---|---|---|
| `BE-SVC-GCF-F01` | **S1** | `[SEC]` | `backend/app/services/guardian_conflict_service.py:27-33` | Volatile In-Memory Storage for Legal Custody Disputes, Dual-Sign Artifacts, and Immutable Audit Ledgers. Critical legal freezes, court sub-judice statuses, and forensic audit records are lost on process restart or across worker processes, creating major legal non-compliance under Guardians and Wards Act 1890 and DPDP Act 2023. |
| `BE-SVC-GCF-F02` | **S1** | `[SEC]` | `backend/app/services/guardian_conflict_service.py:175-179, 396-410` | Signature Attestation is a Pure Boolean Flag (`request.guardian_signature_attestation: bool`) without Cryptographic Verification (No PKI, DSC, or Aadhaar eSign). Any caller passing `True` bypasses DPDP Act 2023 Sec 9 digital signature requirements. |
| `BE-SVC-GCF-F03` | **S2** | `[QUAL]` | `backend/app/services/guardian_conflict_service.py:223-247` | Pessimistic Revocation silently suppresses exceptions when communicating with `guardian_delegation_service` via a blind `try...except Exception: pass`. If delegation service revocation fails, the caller receives success while delegation remains unrevoked! |
| `BE-SVC-GCF-F04` | **S2** | `[QUAL]` | `backend/app/services/guardian_conflict_service.py:151-170` | Dynamic Fallback for Arbitrary Dependent IDs auto-grants "Dr. Priya Sharma" as default primary guardian with AADHAAR_DEMOGRAPHIC_EKYC for any unknown dependent ID, bypassing authentication. |
| `BE-SVC-GCF-F05` | **S3** | `[PERF]` | `backend/app/services/guardian_conflict_service.py:488-518` | Linear Scan over Unindexed In-Memory Dictionaries and Audit Ledger for Dependent Filtering. |
| `BE-SVC-GCF-F06` | **S4** | `[DOC]` | `backend/app/services/guardian_conflict_service.py:18-24` | Missing Architectural Documentation on Legal Escalation Protocols for High Court / Family Court Sub-Judice Orders and Statutory Timelines. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch 1: Robust Revocation Propagation & Exception Logging (`BE-SVC-GCF-F03`)
```diff
--- a/backend/app/services/guardian_conflict_service.py
+++ b/backend/app/services/guardian_conflict_service.py
@@ -232,8 +232,13 @@ class GuardianConflictService:
                         guardian_patient_id=request.initiating_guardian_id,
                         revocation_reason=request.justification,
                         signature_attestation=True,
                     )
                 )
-            except Exception:
-                pass
+            except KeyError:
+                # Artifact not tracked in delegation store
+                pass
+            except Exception as exc:
+                import logging
+                logging.getLogger("nirmaya.guardian_conflict").error(
+                    f"Failed to cascade revocation to delegation service: {exc}"
+                )
+                raise RuntimeError(f"Pessimistic revocation cascade failure: {exc}")
```

### Patch 2: Disallow Insecure Dynamic Fallback for Unknown Dependents (`BE-SVC-GCF-F04`)
```diff
--- a/backend/app/services/guardian_conflict_service.py
+++ b/backend/app/services/guardian_conflict_service.py
@@ -150,21 +150,4 @@ class GuardianConflictService:
                 active_dispute_ticket_id=dispute_ticket_id,
             )

-        # Dynamic fallback for arbitrary dependent IDs
-        return MultiGuardianRelationshipSummary(
-            dependent_patient_id=dependent_patient_id,
-            dependent_name="Dependent Patient",
-            active_guardians=[
-                GuardianEntry(
-                    guardian_id="pat-priya-sharma-01",
-                    name="Dr. Priya Sharma",
-                    relationship_type="PRIMARY_GUARDIAN",
-                    verification_tier="AADHAAR_DEMOGRAPHIC_EKYC",
-                    priority_tier=1,
-                    authorized_at=datetime.now(timezone.utc).isoformat(),
-                )
-            ],
-            custody_mode=self._custody_modes.get(dependent_patient_id, CustodyModeEnum.JOINT_CONCURRENT),
-            dispute_flag_active=False,
-            active_dispute_ticket_id=None,
-        )
+        raise ValueError(f"No registered guardians or custody records found for dependent patient '{dependent_patient_id}'.")
```
