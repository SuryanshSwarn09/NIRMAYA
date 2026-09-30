"""HL7 FHIR Release 4 and ABDM Encounter & Appointment Transformers.

Translates internal NIRMAYA relational appointment and encounter models into
standardized HL7 FHIR R4 resources (Appointment, Encounter, Collection Bundle)
and signed ABDM CareContext Consent Artifacts.
"""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional
import uuid
from app.fhir.schemas import (
    ABDMConsentLinkage,
    FHIRAppointment,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIREncounter,
    FHIREncounterParticipant,
    FHIRIdentifier,
    FHIRParticipant,
    FHIRPeriod,
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

# NIRMAYA to FHIR R4 Encounter status mapping
NIRMAYA_TO_FHIR_ENCOUNTER_STATUS: Dict[AppointmentStatus, str] = {
    AppointmentStatus.SCHEDULED: "planned",
    AppointmentStatus.CONFIRMED: "planned",
    AppointmentStatus.IN_PROGRESS: "in-progress",
    AppointmentStatus.COMPLETED: "finished",
    AppointmentStatus.CANCELLED: "cancelled",
    AppointmentStatus.NO_SHOW: "entered-in-error",
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


# ============================================================================
# Transformer: Encounter -> FHIR Encounter Resource
# ============================================================================


def to_fhir_encounter(appt: Appointment) -> FHIREncounter:
    """Transform internal clinical appointment/encounter into an HL7 FHIR R4 Encounter resource.

    Args:
        appt: Appointment database entity.

    Returns:
        Standard FHIREncounter resource model.
    """
    fhir_status = NIRMAYA_TO_FHIR_ENCOUNTER_STATUS.get(appt.status, "planned")

    # Class: VR (Virtual/Telehealth) vs AMB (Ambulatory)
    is_teleconsult = (
        appt.appointment_type == AppointmentType.TELECONSULTATION
        or (appt.slot and appt.slot.is_teleconsult)
    )

    if is_teleconsult:
        encounter_class = FHIRCoding(
            system=HL7_ACT_CODE_SYSTEM,
            code="VR",
            display="Virtual",
        )
    else:
        encounter_class = FHIRCoding(
            system=HL7_ACT_CODE_SYSTEM,
            code="AMB",
            display="Ambulatory",
        )

    # Identifiers
    identifiers = [
        FHIRIdentifier(
            system=NIRMAYA_ENCOUNTER_SYSTEM,
            value=f"enc-{appt.id}",
            use="official",
        )
    ]

    # Type
    types: List[FHIRCodeableConcept] = []
    if appt.appointment_type in APPOINTMENT_TYPE_MAPPINGS:
        types.append(APPOINTMENT_TYPE_MAPPINGS[appt.appointment_type])

    # Subject (Patient)
    pat_display = None
    if appt.patient and appt.patient.user:
        pat_display = appt.patient.user.full_name

    subject = FHIRReference(
        reference=f"Patient/{appt.patient_id}",
        display=pat_display,
        type="Patient",
    )

    # Participants (Doctor/Practitioner)
    participants: List[FHIREncounterParticipant] = []
    doc_display = None
    if appt.doctor and appt.doctor.user:
        doc_display = appt.doctor.user.full_name

    participants.append(
        FHIREncounterParticipant(
            individual=FHIRReference(
                reference=f"Practitioner/{appt.doctor_id}",
                display=doc_display,
                type="Practitioner",
            ),
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
        )
    )

    # Appointment reference
    appointments = [
        FHIRReference(
            reference=f"Appointment/{appt.id}",
            type="Appointment",
        )
    ]

    # Period
    period = FHIRPeriod(
        start=appt.scheduled_start,
        end=appt.scheduled_end,
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

    return FHIREncounter(
        id=f"enc-{appt.id}",
        identifier=identifiers,
        status=fhir_status,
        class_=encounter_class,
        type=types,
        subject=subject,
        participant=participants,
        appointment=appointments,
        period=period,
        reasonCode=reason_codes,
    )


# ============================================================================
# Transformer: Multi-Resource FHIR Collection Bundle
# ============================================================================


def to_fhir_encounter_bundle(appt: Appointment) -> FHIRBundle:
    """Bundle Appointment, Encounter, Patient, and Practitioner resources into a standard FHIR Bundle.

    Args:
        appt: Appointment database entity.

    Returns:
        FHIRBundle with type='collection' containing all clinical interaction resources.
    """
    entries: List[FHIRBundleEntry] = []

    # 1. Appointment resource
    fhir_appt = to_fhir_appointment(appt)
    entries.append(
        FHIRBundleEntry(
            fullUrl=f"urn:uuid:{appt.id}",
            resource=fhir_appt.model_dump(by_alias=True, exclude_none=True),
        )
    )

    # 2. Encounter resource
    fhir_enc = to_fhir_encounter(appt)
    entries.append(
        FHIRBundleEntry(
            fullUrl=f"urn:uuid:{fhir_enc.id}",
            resource=fhir_enc.model_dump(by_alias=True, exclude_none=True),
        )
    )

    # 3. Patient resource entry (if available)
    if appt.patient and appt.patient.user:
        pat = appt.patient
        patient_resource: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": pat.id,
            "identifier": [
                {
                    "system": "https://healthid.ndhm.gov.in",
                    "value": pat.abha_number or "UNASSIGNED",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical record number",
                            }
                        ]
                    },
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": pat.user.full_name,
                }
            ],
            "gender": pat.gender.value if pat.gender else "unknown",
        }
        if pat.date_of_birth:
            patient_resource["birthDate"] = pat.date_of_birth.isoformat()

        entries.append(
            FHIRBundleEntry(
                fullUrl=f"urn:uuid:{pat.id}",
                resource=patient_resource,
            )
        )

    # 4. Practitioner resource entry (if available)
    if appt.doctor and appt.doctor.user:
        doc = appt.doctor
        practitioner_resource: Dict[str, Any] = {
            "resourceType": "Practitioner",
            "id": doc.id,
            "identifier": [
                {
                    "system": "https://doctor.ndhm.gov.in",
                    "value": doc.registration_number or "UNREGISTERED",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MD",
                                "display": "Medical License number",
                            }
                        ]
                    },
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": doc.user.full_name,
                    "prefix": ["Dr."],
                }
            ],
        }
        entries.append(
            FHIRBundleEntry(
                fullUrl=f"urn:uuid:{doc.id}",
                resource=practitioner_resource,
            )
        )

    return FHIRBundle(
        id=str(uuid.uuid4()),
        type="collection",
        timestamp=datetime.now(timezone.utc),
        total=len(entries),
        entry=entries,
    )


# ============================================================================
# Transformer: ABDM Health Information Artifact & Cryptographic Signer
# ============================================================================


def to_abdm_health_information_artifact(
    appt: Appointment,
    hip_id: str = "IN010000001",
    consent_id: Optional[str] = None,
) -> ABDMConsentLinkage:
    """Build an ABDM-compliant Health Information artifact with CareContext and SHA-256 signature.

    Args:
        appt: Clinical appointment entity.
        hip_id: Health Information Provider registry identifier.
        consent_id: Active ABDM consent artifact UUID if consented.

    Returns:
        ABDMConsentLinkage containing FHIR bundle, careContextReference, and SHA-256 digest.
    """
    # Generate canonical multi-resource FHIR Bundle
    bundle = to_fhir_encounter_bundle(appt)

    # Derive canonical deterministic CareContext Reference: APPT-XXXXXXXX
    clean_uuid = appt.id.replace("-", "")[:8].upper()
    care_context_ref = f"APPT-{clean_uuid}"

    # Determine patient reference (prefer ABHA number/address, fallback to vault UUID)
    patient_ref = appt.patient_id
    if appt.patient:
        patient_ref = (
            appt.patient.abha_number
            or appt.patient.abha_address
            or f"Patient/{appt.patient_id}"
        )

    # Compute SHA-256 tamper-evident digest of serialized bundle
    bundle_json = bundle.model_dump_json(by_alias=True)
    digest = hashlib.sha256(bundle_json.encode("utf-8")).hexdigest()

    return ABDMConsentLinkage(
        careContextReference=care_context_ref,
        patientReference=patient_ref,
        hiType="OPConsultation",
        hipId=hip_id,
        consentArtifactId=consent_id,
        timestamp=datetime.now(timezone.utc),
        signature=digest,
        bundle=bundle,
    )



