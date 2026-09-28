# Week 4: Clinical Encounters, Scheduling & Month 1 Close (Release v0.1.0)

**Milestone Target:** Implement clinical appointment scheduling data models, conflict-free slot generation engine, ACID row-level booking concurrency, HL7 FHIR Encounter/Appointment mappings, and Cal.com slot picker integration to complete Month 1 and release `v0.1.0`.

---

## Daily Schedule & Commit Breakdown

| Day | Focus Area | Key Deliverables | Status |
|---|---|---|---|
| **Day 16 (Mon)** | Appointment Models & Slot Engine | `DoctorSlot`, `Appointment` models, migration 0002, conflict-free slot generator, booking API | **Completed** |
| **Day 17 (Tue)** | Booking Concurrency & ACID Locking | `SELECT ... FOR UPDATE` row locks, held slot timeouts, double-booking prevention, concurrency tests | *Next* |
| **Day 18 (Wed)** | HL7 FHIR Encounter Transformers | HL7 FHIR R4 `Appointment` & `Encounter` resource bundles, ABDM consent linkage | *Scheduled* |
| **Day 19 (Thu)** | Cal.com Slot Picker UI Integration | Interactive calendar availability matrix on `/doctor` and `/patient`, booking modal | *Scheduled* |
| **Day 20 (Fri)** | Month 1 Retrospective & Release v0.1.0 | End-to-end clinical encounter verification, accessibility audit, Month 1 close & tag `v0.1.0` | *Scheduled* |

---

## Week 4 Architecture Highlights

- **Conflict-Free Availability Engine:** Mathematical subdivision of daily clinical practice hours into discrete consultation windows with break interval exclusions and idempotency.
- **Relational Integrity & ACID Safety:** Bidirectional cascade integrity across `DoctorProfile`, `PatientProfile`, `DoctorSlot`, and `Appointment` with strict unique constraints (`uq_doctor_slot_start`, `uq_appointment_slot_id`).
- **Resource Lifecycle Management:** Synchronized state machine where appointment cancellations automatically replenish reserved doctor slots back to `AVAILABLE`.
- **Standards-Based Design:** Core models directly mirror HL7 FHIR R4 `Appointment`, `Schedule`, and `Slot` specifications.
