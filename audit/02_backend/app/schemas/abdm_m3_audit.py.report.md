# Audit Report: backend/app/schemas/abdm_m3_audit.py

**Path:** `backend/app/schemas/abdm_m3_audit.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 108 | **Last Modified:** 2026-11-18 | **Audit Date:** 2026-11-18

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 schemas for ABDM Milestone 3 (M3) compliance telemetry, tracking consent notification ingestion, NHA Fidelius cryptographic operations, data transfer pushes, and HIU consumer metrics.
- **Risk Level:** **S3 (Low)**
- **Verdict:** **READY**
- **Single Most Important Finding:** Stale default version string (`0.3.0-alpha.w11`) hardcoded in `AbdmM3AuditReport`, lagging behind the repository's current master release (`v1.1.0`).

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In ABDM Milestone 3, health information is exchanged across providers via encrypted data transfer gated by patient consent artefacts. To monitor and prove compliance with the NHA Fidelius cryptographic specifications, the system needs real-time telemetry: how many consents were ingested, how many Diffie-Hellman key exchanges succeeded, data transfer batch volumes, and health information consumer (HIU) decryption metrics. This file defines the reporting schemas.

### How it works, step by step
1. `ConsentAuditMetrics` captures consent counts: `totalIngested`, `activeGranted`, `revoked`, `expired`, and `denied`.
2. `CryptoAuditMetrics` records cryptographic parameters: `Curve25519 (X25519)`, `HKDF-SHA256`, `AES-256-GCM`, and NHA Fidelius parity scores.
3. `TransferAuditMetrics` tracks outbound clinical bundle dispatches, batches, records, and transmission failure rates.
4. `HIUConsumerAuditMetrics` tracks inbound encrypted bundles, extracted clinical resources (encounters, prescriptions, reports, vitals), and tamper rejection counts.
5. `AbdmM3AuditReport` synthesizes these four domains into a master compliance audit payload.

### Concepts and patterns used
- *NHA Fidelius Cryptographic Telemetry:* Documenting compliance with national cryptographic primitives.
- *Dual-Role Telemetry (HIP & HIU):* Auditing both outbound record provisioning (HIP) and inbound consumer ingestion (HIU).
- *Tamper-Detection Metrics:* Quantifying checksum rejections and cryptographic integrity scores.

### Key lines to read first
- `abdm_m3_audit.py:23-44`: `CryptoAuditMetrics` and Fidelius algorithm standards.
- `abdm_m3_audit.py:59-74`: `HIUConsumerAuditMetrics` and tamper rejection counters.
- `abdm_m3_audit.py:76-108`: `AbdmM3AuditReport` consolidated compliance schema.

### How to change it safely
When updating cryptographic standards, ensure values remain compatible with NHA specifications. Do not alter metric field names without updating the corresponding database aggregation service.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `typing`, `pydantic` (BaseModel, Field).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/abdm_m3_audit_service.py`, `backend/app/api/v1/endpoints/abdm_m3.py`.
- **Public Surface:** Classes `ConsentAuditMetrics`, `CryptoAuditMetrics`, `TransferAuditMetrics`, `HIUConsumerAuditMetrics`, `AbdmM3AuditReport`.

### 2. Security [SEC]
- **Cryptographic Audit Transparency:** The schemas explicitly expose the curve standard (`Curve25519`), key derivation function (`HKDF-SHA256`), and authenticated encryption mode (`AES-256-GCM`), providing auditable proof of zero-knowledge health data transfer compliance.
- No sensitive keys, private parameters, or patient identifiable information are exposed in these telemetry metrics.

### 3. Code quality [QUAL]
- **Missing `ConfigDict(from_attributes=True)` (Lines 13-108):** Unlike other schema files across the codebase, models in this file omit `model_config = ConfigDict(from_attributes=True)`, preventing automated serialization from ORM model instances (`BE-M3A-F01`).
- Clean separation of concern across the four telemetry domains.

### 4. AI-generated-code smells [QUAL]
- None; the metric categories comprehensively address real-world health information exchange failure modes.

### 5. Performance [PERF]
- Lightweight scalar metrics; minimal JSON payload size.

### 6. Error handling & edge cases
- All metric fields have default values or explicit descriptions, ensuring audit endpoints produce valid reports even on clean database installations with zero transactions.

### 7. Doc accuracy [DOC]
- **Stale Version String (Line 106):** `version: str = Field(default="0.3.0-alpha.w11", description="Software release version")` reflects Week 11 Milestone 3 development, lagging behind the project's `v1.1.0` master release (`BE-M3A-F02`).

### 8. Tests
- Covered by `backend/tests/test_abdm_m3.py` and `backend/tests/test_abdm_m3_audit.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-M3A-F01 | S3 | [QUAL] | 13-108 | Missing `from_attributes=True` configuration | Models lack `model_config = ConfigDict(...)` | Add `ConfigDict(from_attributes=True)` |
| BE-M3A-F02 | S3 | [DOC] | 106 | Stale version string in default field | `default="0.3.0-alpha.w11"` | Update default to dynamic version or `v1.1.0` |

---

## Suggested Patches (NOT Applied)

### S3 One-Line Fix
- **BE-M3A-F01:** In each model class, add `model_config = ConfigDict(from_attributes=True)`.
- **BE-M3A-F02:** In `AbdmM3AuditReport`, update default version to `default="1.1.0"`.

---

## Verdict

**READY** — Pristine telemetry and audit schema providing comprehensive compliance reporting for ABDM Milestone 3 and NHA Fidelius data exchange.
