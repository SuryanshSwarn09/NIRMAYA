# Principal Software Audit & Technical Documentation
## File: `backend/app/schemas/opd_queue.py`
**Audited Path:** `backend/app/schemas/opd_queue.py`  
**Module:** `backend` | **Subsystem:** Outpatient Department (OPD) Queue Management & Room Calling  
**Severity Classification:** HIGH RISK (`[SEC]` / `[QUAL]`)  
**Audit Date:** 2026-11-19  

---

### Layer A: Executive & Team-Lead Summary

#### 1. Purpose & Functional Role
`backend/app/schemas/opd_queue.py` defines the Pydantic v2 schemas for hospital Outpatient Department (OPD) queue tracking, clinical triage management, patient check-in workflows, and doctor consultation room summoning in NIRMAYA. Designed to handle high-velocity patient flows in public hospitals and large multi-specialty clinics, this module structures:
- Queue lifecycle states (`WAITING`, `CALLED`, `IN_CONSULTATION`, `COMPLETED`, `ABSENT`, `CANCELLED`).
- Granular patient queue tokens and clinical check-in records (`OPDQueueEntry`).
- Reception check-in requests (`QueueCheckInRequest`) and nurse triage updates (`QueueTriageUpdateRequest`).
- Physician room calling requests (`QueueCallPatientRequest`) and consultation state transitions (`QueueStatusUpdateRequest`).
- Real-time facility-wide queue summaries and monitoring dashboards (`OPDQueueResponse`, `QueueStatsResponse`).

#### 2. Key Components & Class Roster
- `QueueStatus`: Enumeration of outpatient consultation progress states.
- `OPDQueueEntry`: Complete queue entry record tracking queue UUID, facility ID, daily sequential token number, patient UUID, name, ABHA number, phone number, doctor UUID, doctor name, status, triage level (`STANDARD`, `URGENT`, `EMERGENT`), chief complaint, room number, estimated wait minutes, and ISO timestamps (`checkInTime`, `calledTime`, `consultationStartTime`, `completedTime`).
- `QueueCheckInRequest`: Receptionist intake payload registering an arriving patient into the OPD queue.
- `QueueTriageUpdateRequest`: Nursing/triage officer payload for updating clinical urgency levels and wait time estimates.
- `QueueCallPatientRequest`: Clinician summoning payload assigning a consultation room and triggering real-time patient notification.
- `QueueStatusUpdateRequest`: Transition payload advancing patient state to in-consultation, completed, or absent.
- `OPDQueueResponse`: Facility-wide listing of queue tokens with waiting, in-consultation, and completion counters.
- `QueueStatsResponse`: Administrative monitoring report detailing urgent counts, emergent counts, average wait times, and total tokens.

---

### Layer B: Plain-Language Developer Walkthrough

Anyone who has visited a government hospital or major clinic in India knows how chaotic outpatient waiting areas can be. Hundreds of patients wait in corridors, tokens are called over crackling loudspeakers, and urgent or elderly patients often get lost in the crowd.

`opd_queue.py` provides the digital nervous system for managing this waiting line smoothly and safely:
1. When a patient arrives at the hospital reception, they check in via `QueueCheckInRequest`. The system gives them a sequential daily token number and records their arrival time.
2. A triage nurse can review the patient and submit a `QueueTriageUpdateRequest` if the patient has chest pain or high fever, elevating their triage level from `STANDARD` to `URGENT` so they are moved forward in the queue.
3. When the doctor is ready, they click "Call Next" in their console, submitting a `QueueCallPatientRequest` with their room number (e.g. "Room 3"). This triggers display boards and mobile alerts notifying the patient to enter the consultation room.
4. Throughout the day, hospital administrators use `QueueStatsResponse` to monitor average wait times and identify if any department is overwhelmed.

---

### Layer C: Technical Deep Dive & Code Review

#### 1. Architectural Rigor & Invariants
- **Triage Integration:** Reuses the standardized `TriageLevel` enum imported from `app.schemas.websocket_events`.
- **Dynamic Token IDs:** Defaults `queueId` via `default_factory=lambda: str(uuid.uuid4())`.
- **ORM Configuration:** Enforces `model_config = ConfigDict(from_attributes=True)` consistently across all queue records and response envelopes.

#### 2. Identified Vulnerabilities & Technical Deficiencies

##### Vulnerability 1: Patient Personally Identifiable Information Exposed in Repr (`BE-SCH-OPD-F01`)
- **Severity:** S2 (`[SEC]`)
- **File & Lines:** `backend/app/schemas/opd_queue.py:42-44, 73-75`
- **Description:** In both `OPDQueueEntry` and `QueueCheckInRequest`, fields `patientName`, `patientAbha`, and `patientPhone` are declared as plain strings without `repr=False`. When queue listings, check-in requests, or triage updates are printed in application logs or WebSocket connection traces, patient full names, 14-digit ABHA numbers, and personal mobile numbers are written in cleartext to log files.
- **Impact:** Compromises patient privacy and leaks sensitive PII in log aggregators (CWE-532).
- **Remediation:** Annotate `patientName`, `patientAbha`, and `patientPhone` with `repr=False`.

##### Vulnerability 2: Datetimes Stored as Raw ISO Strings Instead of Native Types (`BE-SCH-OPD-F02`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/opd_queue.py:52-58`
- **Description:** Timestamps (`checkInTime`, `calledTime`, `consultationStartTime`, `completedTime`) are typed as `str` using `lambda: datetime.now(timezone.utc).isoformat()` rather than native `datetime`. Storing timestamps as raw strings bypasses Pydantic's automated ISO datetime parsing, timezone conversions, and OpenAPI schema typing (`type: string, format: date-time`).
- **Impact:** Loss of type safety, timezone normalization, and date-arithmetic capabilities.
- **Remediation:** Convert timestamp fields to `Optional[datetime]` typed natively.

##### Vulnerability 3: Missing Non-Negative Integer Constraints on Token and Count Fields (`BE-SCH-OPD-F03`)
- **Severity:** S3 (`[QUAL]`)
- **File & Lines:** `backend/app/schemas/opd_queue.py:40, 51, 123-126, 136-141`
- **Description:** Fields `tokenNumber`, `estimatedWaitMinutes`, `totalEntries`, `waitingCount`, `inConsultationCount`, and `completedCount` lack `ge=0` bounds, allowing negative token numbers or negative counts to pass validation.
- **Impact:** Schema boundary defect violating response invariants.
- **Remediation:** Add `ge=0` (and `ge=1` on `tokenNumber`) to integer fields.

---

### Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-OPD-F01` | S2 | `[SEC]` | `opd_queue.py:42-44, 73-75` | Patient name, ABHA number, and phone number unmasked in string `repr` |
| `BE-SCH-OPD-F02` | S3 | `[QUAL]` | `opd_queue.py:52-58` | Timestamps declared as ISO strings instead of native `datetime` |
| `BE-SCH-OPD-F03` | S3 | `[QUAL]` | `opd_queue.py:40, 123-126` | Token numbers and queue counters lack non-negative integer bounds |

---

### Layer E: Unified Diff Patches

```diff
--- a/backend/app/schemas/opd_queue.py
+++ b/backend/app/schemas/opd_queue.py
@@ -39,7 +39,7 @@ class OPDQueueEntry(BaseModel):
     facilityId: str = Field(description="Healthcare facility identifier")
-    tokenNumber: int = Field(description="Sequential daily OPD token number")
+    tokenNumber: int = Field(ge=1, description="Sequential daily OPD token number")
     patientId: str = Field(description="Patient profile UUID")
-    patientName: str = Field(description="Patient display name")
-    patientAbha: Optional[str] = Field(default=None, description="14-digit ABHA number if linked")
-    patientPhone: Optional[str] = Field(default=None, description="Contact phone number")
+    patientName: str = Field(repr=False, description="Patient display name")
+    patientAbha: Optional[str] = Field(default=None, repr=False, description="14-digit ABHA number if linked")
+    patientPhone: Optional[str] = Field(default=None, repr=False, description="Contact phone number")
     doctorId: Optional[str] = Field(default=None, description="Assigned clinician profile UUID")
@@ -51,8 +51,8 @@ class OPDQueueEntry(BaseModel):
     roomNumber: Optional[str] = Field(default=None, description="Consultation room / cubicle number")
-    estimatedWaitMinutes: Optional[int] = Field(default=None, description="Estimated wait time in minutes")
-    checkInTime: str = Field(
-        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
-        description="ISO 8601 UTC timestamp of patient arrival/check-in",
+    estimatedWaitMinutes: Optional[int] = Field(default=None, ge=0, description="Estimated wait time in minutes")
+    checkInTime: datetime = Field(
+        default_factory=lambda: datetime.now(timezone.utc),
+        description="UTC timestamp of patient arrival/check-in",
     )
-    calledTime: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp when patient was called")
-    consultationStartTime: Optional[str] = Field(default=None, description="ISO 8601 UTC consultation start time")
-    completedTime: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp when consultation ended")
+    calledTime: Optional[datetime] = Field(default=None, description="UTC timestamp when patient was called")
+    consultationStartTime: Optional[datetime] = Field(default=None, description="UTC consultation start time")
+    completedTime: Optional[datetime] = Field(default=None, description="UTC timestamp when consultation ended")
     notes: Optional[str] = Field(default=None, description="Administrative or nursing notes")
@@ -72,4 +72,4 @@ class QueueCheckInRequest(BaseModel):
     patientId: str = Field(description="Patient profile UUID")
-    patientName: str = Field(description="Patient display name")
-    patientAbha: Optional[str] = Field(default=None, description="14-digit ABHA number")
-    patientPhone: Optional[str] = Field(default=None, description="Contact phone number")
+    patientName: str = Field(repr=False, description="Patient display name")
+    patientAbha: Optional[str] = Field(default=None, repr=False, description="14-digit ABHA number")
+    patientPhone: Optional[str] = Field(default=None, repr=False, description="Contact phone number")
@@ -122,5 +122,5 @@ class OPDQueueResponse(BaseModel):
     facilityId: str = Field(description="Facility identifier")
-    totalEntries: int = Field(description="Total patient entries registered today")
-    waitingCount: int = Field(description="Patients currently waiting")
-    inConsultationCount: int = Field(description="Patients actively in consultation")
-    completedCount: int = Field(description="Consultations completed today")
+    totalEntries: int = Field(ge=0, description="Total patient entries registered today")
+    waitingCount: int = Field(ge=0, description="Patients currently waiting")
+    inConsultationCount: int = Field(ge=0, description="Patients actively in consultation")
+    completedCount: int = Field(ge=0, description="Consultations completed today")
```
