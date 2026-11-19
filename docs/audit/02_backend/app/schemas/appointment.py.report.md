# Audit Report: backend/app/schemas/appointment.py

**Path:** `backend/app/schemas/appointment.py` | **Layer:** Backend (Pydantic Schemas) | **Language:** Python 3.12 (Pydantic v2) | **LOC:** 240 | **Last Modified:** 2026-11-19 | **Audit Date:** 2026-11-19

---

## Layer A — TL;DR

- **Purpose:** Pydantic v2 validation models for clinician availability schedules (`DoctorSlot`), bulk slot generation, checkout slot holds, and clinical appointment booking aligned with HL7 FHIR R4.
- **Risk Level:** **S2 (Medium)**
- **Verdict:** **READY-WITH-FIXES**
- **Single Most Important Finding:** In `AppointmentStatusUpdate`, `cancellation_reason` is documented as required when status is `CANCELLED`, but there is no model validator enforcing this rule, permitting silent cancellations without clinical audit justification.

---

## Layer B — Explain It (For Someone Who Did Not Write It)

### What problem this file solves
In modern digital hospital systems, patient encounters require reliable schedule coordination: doctors define working hours and breaks, the system generates conflict-free bookable slots, patients temporarily hold slots during checkout to prevent double-booking, and confirmed consultations are recorded as HL7 FHIR R4-aligned appointments. This file defines the request and response schemas for every stage of this lifecycle.

### How it works, step by step
1. `DoctorSlotBase`, `DoctorSlotCreate`, and `DoctorSlotResponse` represent discrete consultation intervals (e.g., 30-minute blocks), validating that `end_time > start_time`.
2. `SlotHoldRequest`, `SlotHoldResponse`, and `SlotReleaseResponse` manage temporary locks on slots (1–30 minutes) while a patient completes booking or teleconsultation payment.
3. `SlotGenerateRequest` defines rules for bulk schedule creation: start/end dates, daily working hours, slot durations (10–120 minutes), and lunch breaks, with extensive cross-field validations in `validate_dates_and_hours`.
4. `SlotGenerateResult` reports how many slots were created and how many conflicted/skipped.
5. `AppointmentBase`, `AppointmentCreate`, `AppointmentStatusUpdate`, and `AppointmentResponse` govern the clinical encounter itself, validating that either a pre-reserved `slot_id` or explicit `scheduled_start`/`scheduled_end` timestamps are supplied.

### Concepts and patterns used
- *HL7 FHIR R4 Resource Alignment:* Mapped to FHIR `Appointment`, `Schedule`, and `Slot`.
- *Cross-Field Model Validation:* Using `@model_validator(mode="after")` to verify complex business constraints (e.g., `end_date >= start_date`, `day_end > day_start`, `break_end > break_start`).
- *Optimistic Slot Holding:* Two-phase booking pattern with temporary lock expiration.

### Key lines to read first
- `appointment.py:35-39`: `validate_time_window` ensuring positive slot durations.
- `appointment.py:100-145`: `SlotGenerateRequest` and extensive schedule constraint validation.
- `appointment.py:201-207`: `validate_scheduling_specification` in `AppointmentCreate`.
- `appointment.py:210-220`: `AppointmentStatusUpdate` lifecycle transition model.

### How to change it safely
When modifying appointment schemas, ensure any added statuses exist in `app.models.enums.AppointmentStatus` and `SlotStatus`. Always maintain the conditional requirement: an appointment booking must supply either `slot_id` or both `scheduled_start` and `scheduled_end`.

---

## Layer C — Technical Detail

### 1. Role in architecture
- **Imports:** `datetime`, `date`, `typing` (List, Optional), `pydantic` (BaseModel, ConfigDict, Field, model_validator), `app.models.enums` (AppointmentStatus, AppointmentType, SlotStatus).
- **Imported By:** `backend/app/schemas/__init__.py`, `backend/app/services/appointment_service.py`, `backend/app/api/v1/endpoints/appointments.py`.
- **Public Surface:** 12 Pydantic models including `DoctorSlotBase`, `DoctorSlotCreate`, `DoctorSlotResponse`, `SlotHoldRequest`, `SlotHoldResponse`, `SlotReleaseResponse`, `SlotGenerateRequest`, `SlotGenerateResult`, `AppointmentBase`, `AppointmentCreate`, `AppointmentStatusUpdate`, `AppointmentResponse`.

### 2. Security [SEC]
- **Clinical Triage Confidentiality:** `AppointmentBase.clinical_notes` (line 173-176) carries confidential triage notes and clinician observations. Access to `AppointmentResponse` must be strictly gated by patient-doctor access controls in service/endpoint layers.
- **Preventing Denial-of-Service in Slot Generation (`BE-SCH-APP-F03`):** `SlotGenerateRequest` (line 100-145) lacks an upper-bound check on `(end_date - start_date).days`. A malicious or mistaken user could request slot generation for a 20-year span, resulting in millions of slot records being computed and overwhelming server memory and database connections.

### 3. Code quality [QUAL]
- **Missing Conditional Validation on Cancellation (`BE-SCH-APP-F01`):** In `AppointmentStatusUpdate` (line 215-219), `cancellation_reason` description states "Reason required when status is CANCELLED", but no validator checks this. If a client sends `status="cancelled"` with an empty `cancellation_reason`, validation passes silently.
- **Timezone Awareness Enforcement (`BE-SCH-APP-F02`):** In `DoctorSlotResponse` and `AppointmentResponse`, datetime fields do not explicitly reject naive datetimes. If naive datetimes enter the pipeline, timezone comparison against UTC timestamps will crash with `TypeError: can't compare offset-naive and offset-aware datetimes`.
- Excellent use of Pydantic v2 `@model_validator(mode="after")` in `DoctorSlotBase` and `SlotGenerateRequest`.

### 4. AI-generated-code smells [QUAL]
- None; the schema structures demonstrate careful domain modeling aligned with clinical workflows.

### 5. Performance [PERF]
- Bulk slot generation returns `SlotGenerateResult` containing `slots: List[DoctorSlotResponse]`. If generating hundreds of slots, serializing full response objects can produce large payloads; returning summary counts with slot IDs is preferable for high-volume batches.

### 6. Error handling & edge cases
- `AppointmentCreate.validate_scheduling_specification` cleanly handles both slot-based booking and emergency ad-hoc scheduling.

### 7. Doc accuracy [DOC]
- Perfectly reflects HL7 FHIR Appointment and Slot resource specifications.

### 8. Tests
- Covered by `backend/tests/test_appointments.py`.

---

## Findings Table

| ID | Sev | Tag | Line(s) | Issue | Evidence | Fix Summary |
|---|---|---|---|---|---|---|
| BE-SCH-APP-F01 | S2 | [QUAL] | 215-219 | `cancellation_reason` not enforced when status is `CANCELLED` | Field documented as required, but no validator exists | Add `@model_validator(mode="after")` verifying reason on cancellation |
| BE-SCH-APP-F02 | S2 | [QUAL] | 61, 230-231 | Missing UTC timezone enforcement on scheduling datetimes | `datetime` fields accept naive timestamps | Enforce timezone-aware UTC datetimes in validators |
| BE-SCH-APP-F03 | S3 | [PERF] | 104-105 | Unbounded date range in bulk slot generator request | No maximum date span limit (e.g. 90 days) | Add validator ensuring `(end_date - start_date).days <= 90` |

---

## Suggested Patches (NOT Applied)

### Patch BE-SCH-APP-F01 · Risk: Low · [UNTESTED]
Enforce cancellation reason requirement in `AppointmentStatusUpdate`:

```diff
--- a/backend/app/schemas/appointment.py
+++ b/backend/app/schemas/appointment.py
@@ -219,3 +219,9 @@ class AppointmentStatusUpdate(BaseModel):
         description="Reason required when status is CANCELLED",
     )
+
+    @model_validator(mode="after")
+    def validate_cancellation_reason(self) -> "AppointmentStatusUpdate":
+        if self.status == AppointmentStatus.CANCELLED and not self.cancellation_reason:
+            raise ValueError("cancellation_reason is required when cancelling an appointment")
+        return self
