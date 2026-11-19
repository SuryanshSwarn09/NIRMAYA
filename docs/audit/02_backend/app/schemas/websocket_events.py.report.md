# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/schemas/websocket_events.py`
# Component: Real-Time Pub/Sub & WebSocket Messaging Subsystem
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/schemas/websocket_events.py` specifies the typed event envelopes, channel naming conventions, clinical telemetry payloads, client commands, and administrative diagnostics models governing NIRMAYA's real-time WebSocket communications. It manages Redis Pub/Sub message distribution for outpatient department (OPD) queue progressions, critical panic-value lab alerts, appointment slot holds, system-wide notifications, and client connection handshakes.

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |   Clinical Alert / OPD Queue / Appointment   |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |    QueueUpdatePayload / CriticalAlertPayload   |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |   WebSocketBaseEvent (channel, eventType)     |
           +-----------------------------------------------+
                                  |
                   (Redis Pub/Sub / In-Memory Bus)
                                  v
           +-----------------------------------------------+
           |     FastAPI WebSocket Connection Handler      |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |      Client Browser / Doctor Clinical UI      |
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `datetime, timezone` from `datetime`: UTC timestamp generation.
  - `Enum` from `enum`: Event classifications and clinical severity tiers.
  - `Any, Dict, List, Optional` from `typing`: Type annotations.
  - `uuid`: Automatic unique event and alert identifier generation.
  - `BaseModel, ConfigDict, Field` from `pydantic`: Schema validation primitives.
- **Exports**:
  - `WebSocketEventType`: Event classification enum (`QUEUE_UPDATE`, `CRITICAL_ALERT`, etc.).
  - `TriageLevel`: OPD urgency grading (`EMERGENT`, `URGENT`, `STANDARD`, `NON_URGENT`).
  - `AlertSeverity`: Clinical alert tier (`PANIC`, `CRITICAL`, `WARNING`, `INFO`).
  - `HoldStatus`: Appointment reservation state (`HELD`, `RELEASED`, `BOOKED`).
  - `WebSocketChannel`: Canonical channel string generation utility (`facility_queue`, `doctor_workspace`, `patient_vault`).
  - `QueueUpdatePayload`, `CriticalAlertPayload`, `AppointmentHoldPayload`, `SystemNotificationPayload`, `ConnectionAckPayload`: Specialized domain event bodies.
  - `WebSocketBaseEvent`: Universal outer envelope for all distributed pub/sub events.
  - `ClientCommand`: Inbound client stream control messages (`subscribe`, `unsubscribe`, `ping`).
  - `WebSocketMetricsResponse`, `AdminBroadcastRequest`: Diagnostics and operations models.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Event Types & Severity Tiers**: Categorizes real-time traffic into distinct event types (`WebSocketEventType`), triage levels (`TriageLevel`), alert severities (`AlertSeverity`), and appointment slot hold statuses (`HoldStatus`).
2. **Channel Naming Conventions (`WebSocketChannel`)**: Formats consistent Redis pub/sub channel identifiers for facility queues (`facility:{facility_id}:queue`), doctor workspaces (`doctor:{doctor_id}:workspace`), and patient health vaults (`patient:{patient_id}:vault`).
3. **Queue Updates (`QueueUpdatePayload`)**: Delivers OPD token calls, wait-time estimates, triage classifications, and status transitions to clinic display boards and patient portal applications.
4. **Panic Alerts (`CriticalAlertPayload`)**: Transmits immediate, high-priority notifications when abnormal diagnostic findings (such as dangerous serum potassium or severe vitals degradation) require urgent physician intervention.
5. **Enveloping & Handshakes (`WebSocketBaseEvent`, `ConnectionAckPayload`)**: Packages payloads into a standardized envelope with unique `eventId`, publishing channel, event type, and UTC timestamp, returned alongside session authorization data during initial connection.
6. **Telemetry & Admin Broadcasting (`WebSocketMetricsResponse`, `AdminBroadcastRequest`)**: Provides real-time metrics on connected sessions, Redis adapter operational state, and active message counts.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Protected Health Information (PHI) Logging Leakage (CWE-532 / CWE-312)
`QueueUpdatePayload` and `CriticalAlertPayload` contain direct patient identifiers (`patientName`, `patientId`) alongside sensitive clinical observations (`observedValue`, `message`, `loincCode`). When events are passed through standard ASGI or logging middleware, default string serialization emits unmasked clinical panic-values and patient identities into standard output and container logs. Sensitive fields must be marked with `repr=False`.

### Invariant 2: Pub/Sub Channel Authorization & Wildcard Injection
`ClientCommand` allows WebSocket clients to submit `action="subscribe"` with an arbitrary `channel: Optional[str]`. If the WebSocket connection handler processes this command without verifying whether the authenticated user owns or has permission to read the requested channel (e.g., verifying that `channel == WebSocketChannel.patient_vault(current_user.patient_id)`), any client can subscribe to arbitrary patient health vaults or physician workspaces. Furthermore, the `channel` string field lacks regex constraints, permitting Redis wildcard characters (`*`, `?`) that could trigger broad pattern subscriptions.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-WS-F01` | S2 | `[SEC]` | `websocket_events.py:91, 113, 120` | Patient identity and panic lab values unmasked in `repr`, leaking PHI into logs |
| `BE-SCH-WS-F02` | S2 | `[SEC]` | `websocket_events.py:214, 244` | `ClientCommand.channel` lacks authorization parameter and `AdminBroadcastRequest.payload` accepts unbounded `Dict` |
| `BE-SCH-WS-F03` | S3 | `[QUAL]` | `websocket_events.py:97-100, 123-126` | Timestamps defined as unvalidated string fields with lambda defaults rather than native `datetime` |
| `BE-SCH-WS-F04` | S3 | `[QUAL]` | `websocket_events.py:200, 242` | `channel` string fields lack regex validation pattern preventing Redis glob character injection |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/schemas/websocket_events.py
+++ b/backend/app/schemas/websocket_events.py
@@ -88,7 +88,7 @@
     facilityId: str = Field(description="Facility or clinic identifier")
     queueEntryId: str = Field(description="Unique queue record ID")
     patientId: str = Field(description="Patient profile UUID")
-    patientName: str = Field(description="Patient display name")
+    patientName: str = Field(description="Patient display name", repr=False)
     tokenNumber: int = Field(description="Daily OPD sequence token number")
     status: str = Field(description="Queue status (e.g. WAITING, IN_TRIAGE, IN_CONSULTATION, COMPLETED)")
     triageLevel: TriageLevel = Field(default=TriageLevel.STANDARD, description="Clinical triage level")
@@ -110,14 +110,14 @@
         description="Unique alert identifier",
     )
     patientId: str = Field(description="Patient profile UUID")
-    patientName: str = Field(description="Patient display name")
+    patientName: str = Field(description="Patient display name", repr=False)
     doctorId: str = Field(description="Target clinician profile UUID")
     severity: AlertSeverity = Field(description="Clinical alert severity")
     category: str = Field(description="Alert category: LAB_PANIC_VALUE, CRITICAL_VITALS, CONTRAINDICATION")
     title: str = Field(description="Short human-readable alert title")
     message: str = Field(description="Clinical narrative and recommended action")
     loincCode: Optional[str] = Field(default=None, description="LOINC code if lab or vital alert")
-    observedValue: Optional[str] = Field(default=None, description="Measured clinical value with units")
+    observedValue: Optional[str] = Field(default=None, description="Measured clinical value with units", repr=False)
     referenceRange: Optional[str] = Field(default=None, description="Normal biological reference range")
     actionRequired: bool = Field(default=True, description="Whether immediate action/acknowledgement is needed")
     createdAt: str = Field(
```
