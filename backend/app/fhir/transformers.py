"""HL7 FHIR Release 4 and ABDM Encounter & Appointment Transformers.

Translates internal NIRMAYA relational appointment and encounter models into
standardized HL7 FHIR R4 resources (Appointment, Encounter, Collection Bundle)
and signed ABDM CareContext Consent Artifacts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from app.fhir.schemas import (
    FHIRAppointment,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRIdentifier,
    FHIRParticipant,
    FHIRReference,
)
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, AppointmentType


# ============================================================================
# FHIR Terminology Coding Systems
# ============================================================================

HL7_APPOINTMENT_TYPE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0276"
HL7_ACT_CODE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
HL7_PARTICIPATION_TYPE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
NIRMAYA_APPOINTMENT_SYSTEM = "https://nirmaya.health/fhir/appointment"
NIRMAYA_ENCOUNTER_SYSTEM = "https://nirmaya.health/fhir/encounter"
NIRMAYA_CARE_CONTEXT_SYSTEM = "https://nirmaya.health/abdm/care-context"

# NIRMAYA to FHIR R4 Appointment status mapping
NIRMAYA_TO_FHIR_APPOINTMENT_STATUS: Dict[AppointmentStatus, str] = {
    AppointmentStatus.SCHEDULED: "booked",
    AppointmentStatus.CONFIRMED: "booked",
    AppointmentStatus.IN_PROGRESS: "arrived",
    AppointmentStatus.COMPLETED: "fulfilled",
    AppointmentStatus.CANCELLED: "cancelled",
    AppointmentStatus.NO_SHOW: "noshow",
}

# NIRMAYA AppointmentType to HL7 FHIR CodeableConcept mapping
APPOINTMENT_TYPE_MAPPINGS: Dict[AppointmentType, FHIRCodeableConcept] = {
    AppointmentType.ROUTINE_CHECKUP: FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=HL7_APPOINTMENT_TYPE_SYSTEM,
                code="ROUTINE",
                display="Routine appointment",
            )
        ],
        text="Routine clinical checkup and physical examination",
    ),
    AppointmentType.FOLLOW_UP: FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=HL7_APPOINTMENT_TYPE_SYSTEM,
                code="FOLLOWUP",
                display="Follow-up appointment",
            )
        ],
        text="Clinical follow-up consultation",
    ),
    AppointmentType.TELECONSULTATION: FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=HL7_APPOINTMENT_TYPE_SYSTEM,
                code="TELEHEALTH",
                display="Telehealth consultation",
            )
        ],
        text="Virtual video teleconsultation encounter",
    ),
    AppointmentType.EMERGENCY: FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=HL7_APPOINTMENT_TYPE_SYSTEM,
                code="EMERGENCY",
                display="Emergency appointment",
            )
        ],
        text="Urgent unscheduled clinical encounter",
    ),
}


# ============================================================================
# Transformer: Appointment -> FHIR Appointment Resource
# ============================================================================


def to_fhir_appointment(appt: Appointment) -> FHIRAppointment:
    """Transform internal NIRMAYA Appointment ORM model into an HL7 FHIR R4 Appointment resource.

    Args:
        appt: Appointment database entity (optionally with doctor and patient preloaded).

    Returns:
        Standard FHIRAppointment resource model.
    """
    fhir_status = NIRMAYA_TO_FHIR_APPOINTMENT_STATUS.get(appt.status, "booked")

    # Identifiers
    identifiers = [
        FHIRIdentifier(
            system=NIRMAYA_APPOINTMENT_SYSTEM,
            value=appt.id,
            use="official",
        )
    ]

    # Coded Type
    appt_type_concept = APPOINTMENT_TYPE_MAPPINGS.get(
        appt.appointment_type,
        FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system=HL7_APPOINTMENT_TYPE_SYSTEM,
                    code="ROUTINE",
                    display="Routine appointment",
                )
            ],
            text=appt.appointment_type.value,
        ),
    )

    # Reason code
    reason_codes: List[FHIRCodeableConcept] = []
    if appt.reason:
        reason_codes.append(
            FHIRCodeableConcept(
                coding=[],
                text=appt.reason,
            )
        )

    # Participants: Patient and Practitioner
    participants: List[FHIRParticipant] = []

    # 1. Patient participant
    pat_display = None
    if appt.patient and appt.patient.user:
        pat_display = appt.patient.user.full_name
    participants.append(
        FHIRParticipant(
            type=[
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system=HL7_PARTICIPATION_TYPE_SYSTEM,
                            code="SBJ",
                            display="Subject",
                        )
                    ]
                )
            ],
            actor=FHIRReference(
                reference=f"Patient/{appt.patient_id}",
                display=pat_display,
                type="Patient",
            ),
            status="accepted" if appt.status != AppointmentStatus.CANCELLED else "declined",
        )
    )

    # 2. Practitioner participant
    doc_display = None
    if appt.doctor and appt.doctor.user:
        doc_display = appt.doctor.user.full_name
    participants.append(
        FHIRParticipant(
            type=[
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system=HL7_PARTICIPATION_TYPE_SYSTEM,
                            code="PPRF",
                            display="Primary performer",
                        )
                    ]
                )
            ],
            actor=FHIRReference(
                reference=f"Practitioner/{appt.doctor_id}",
                display=doc_display,
                type="Practitioner",
            ),
            status="accepted" if appt.status != AppointmentStatus.CANCELLED else "declined",
        )
    )

    # Slot reference
    slots: Optional[List[FHIRReference]] = None
    if appt.slot_id:
        slots = [
            FHIRReference(
                reference=f"Slot/{appt.slot_id}",
                type="Slot",
            )
        ]

    return FHIRAppointment(
        id=appt.id,
        identifier=identifiers,
        status=fhir_status,
        appointmentType=appt_type_concept,
        reasonCode=reason_codes,
        description=f"Consultation with {doc_display or 'Practitioner'}",
        start=appt.scheduled_start,
        end=appt.scheduled_end,
        created=appt.created_at,
        comment=appt.clinical_notes,
        slot=slots,
        participant=participants,
    )
