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
    FHIRAnnotation,
    FHIRAppointment,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRComposition,
    FHIRCompositionSection,
    FHIRCondition,
    FHIREncounter,
    FHIREncounterParticipant,
    FHIRIdentifier,
    FHIRNarrative,
    FHIRObservation,
    FHIRObservationComponent,
    FHIRObservationReferenceRange,
    FHIRParticipant,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
)
from app.models.appointment import Appointment
from app.models.condition import ClinicalCondition
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    ClinicalNoteStatus,
    ClinicalNoteType,
    ClinicalStatus,
    ConditionCategory,
    ConditionSeverity,
    ObservationCategory,
    ObservationInterpretation,
    ObservationStatus,
    VerificationStatus,
)
from app.models.observation import ClinicalObservation
from app.models.soap_note import SoapNote


# ============================================================================
# FHIR Terminology Coding Systems
# ============================================================================

HL7_APPOINTMENT_TYPE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0276"
HL7_ACT_CODE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
HL7_PARTICIPATION_TYPE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
HL7_CONDITION_CLINICAL_SYSTEM = "http://terminology.hl7.org/CodeSystem/condition-clinical"
HL7_CONDITION_VER_STATUS_SYSTEM = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
HL7_CONDITION_CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/condition-category"
HL7_OBSERVATION_CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/observation-category"
HL7_OBSERVATION_STATUS_SYSTEM = "http://hl7.org/fhir/observation-status"
HL7_OBSERVATION_INTERPRETATION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
SNOMED_CT_SYSTEM = "http://snomed.info/sct"
LOINC_SYSTEM = "http://loinc.org"
UCUM_SYSTEM = "http://unitsofmeasure.org"
NIRMAYA_APPOINTMENT_SYSTEM = "https://nirmaya.health/fhir/appointment"
NIRMAYA_ENCOUNTER_SYSTEM = "https://nirmaya.health/fhir/encounter"
NIRMAYA_CONDITION_SYSTEM = "https://nirmaya.health/fhir/condition"
NIRMAYA_OBSERVATION_SYSTEM = "https://nirmaya.health/fhir/observation"
NIRMAYA_COMPOSITION_SYSTEM = "https://nirmaya.health/fhir/composition"
NIRMAYA_CARE_CONTEXT_SYSTEM = "https://nirmaya.health/abdm/care-context"

# Observation interpretation mappings to HL7 v3 ObservationInterpretation concepts
OBSERVATION_INTERPRETATION_MAPPINGS: Dict[ObservationInterpretation, FHIRCoding] = {
    ObservationInterpretation.NORMAL: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="N",
        display="Normal",
    ),
    ObservationInterpretation.HIGH: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="H",
        display="High",
    ),
    ObservationInterpretation.LOW: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="L",
        display="Low",
    ),
    ObservationInterpretation.CRITICALLY_HIGH: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="HH",
        display="Critical high",
    ),
    ObservationInterpretation.CRITICALLY_LOW: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="LL",
        display="Critical low",
    ),
    ObservationInterpretation.ABNORMAL: FHIRCoding(
        system=HL7_OBSERVATION_INTERPRETATION_SYSTEM,
        code="A",
        display="Abnormal",
    ),
}

# Condition severity mappings to SNOMED-CT concepts
CONDITION_SEVERITY_MAPPINGS: Dict[ConditionSeverity, FHIRCoding] = {
    ConditionSeverity.MILD: FHIRCoding(
        system=SNOMED_CT_SYSTEM,
        code="255604002",
        display="Mild",
    ),
    ConditionSeverity.MODERATE: FHIRCoding(
        system=SNOMED_CT_SYSTEM,
        code="6736007",
        display="Moderate",
    ),
    ConditionSeverity.SEVERE: FHIRCoding(
        system=SNOMED_CT_SYSTEM,
        code="24484000",
        display="Severe",
    ),
}

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


# ============================================================================
# Transformer: FHIR R4 Condition Resource Serializer
# ============================================================================


def to_fhir_condition(cond: ClinicalCondition) -> FHIRCondition:
    """Translate a NIRMAYA ClinicalCondition model to an HL7 FHIR Release 4 Condition resource.

    Args:
        cond: Internal relational ClinicalCondition entity.

    Returns:
        FHIRCondition instance fully compliant with FHIR R4 standard.
    """
    # 1. Clinical Status
    clinical_status_coding = FHIRCoding(
        system=HL7_CONDITION_CLINICAL_SYSTEM,
        code=cond.clinical_status.value,
        display=cond.clinical_status.value.capitalize(),
    )
    clinical_status_cc = FHIRCodeableConcept(
        coding=[clinical_status_coding],
        text=cond.clinical_status.value,
    )

    # 2. Verification Status
    verification_status_cc = None
    if cond.verification_status:
        verification_status_coding = FHIRCoding(
            system=HL7_CONDITION_VER_STATUS_SYSTEM,
            code=cond.verification_status.value,
            display=cond.verification_status.value.replace("-", " ").capitalize(),
        )
        verification_status_cc = FHIRCodeableConcept(
            coding=[verification_status_coding],
            text=cond.verification_status.value,
        )

    # 3. Category
    category_coding = FHIRCoding(
        system=HL7_CONDITION_CATEGORY_SYSTEM,
        code=cond.category.value,
        display=cond.category.value.replace("-", " ").title(),
    )
    category_list = [
        FHIRCodeableConcept(
            coding=[category_coding],
            text=cond.category.value,
        )
    ]

    # 4. Severity (optional)
    severity_cc = None
    if cond.severity and cond.severity in CONDITION_SEVERITY_MAPPINGS:
        severity_coding = CONDITION_SEVERITY_MAPPINGS[cond.severity]
        severity_cc = FHIRCodeableConcept(
            coding=[severity_coding],
            text=cond.severity.value.capitalize(),
        )

    # 5. Code (SNOMED-CT / ICD-10)
    code_cc = FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=cond.code_coding_system,
                code=cond.code_value,
                display=cond.code_display,
            )
        ],
        text=cond.code_display,
    )

    # 6. Body site
    body_site_list: List[FHIRCodeableConcept] = []
    if cond.body_site:
        body_site_list.append(
            FHIRCodeableConcept(
                coding=[],
                text=cond.body_site,
            )
        )

    # 7. Identifiers
    identifiers = [
        FHIRIdentifier(
            system=NIRMAYA_CONDITION_SYSTEM,
            value=cond.id,
            use="official",
        )
    ]

    # 8. Subject (Patient reference)
    patient_display = None
    if getattr(cond, "patient", None) and getattr(cond.patient, "user", None):
        patient_display = cond.patient.user.full_name
    subject_ref = FHIRReference(
        reference=f"Patient/{cond.patient_id}",
        display=patient_display,
        type="Patient",
    )

    # 9. Encounter (if linked)
    encounter_ref = None
    if cond.encounter_id:
        encounter_ref = FHIRReference(
            reference=f"Encounter/{cond.encounter_id}",
            type="Encounter",
        )

    # 10. Recorder (if doctor linked)
    recorder_ref = None
    if cond.recorded_by_doctor_id:
        doctor_display = None
        if getattr(cond, "recorded_by_doctor", None) and getattr(cond.recorded_by_doctor, "user", None):
            doctor_display = cond.recorded_by_doctor.user.full_name
        recorder_ref = FHIRReference(
            reference=f"Practitioner/{cond.recorded_by_doctor_id}",
            display=doctor_display,
            type="Practitioner",
        )

    # 11. Notes
    notes: List[FHIRAnnotation] = []
    if cond.note:
        notes.append(
            FHIRAnnotation(
                text=cond.note,
                time=cond.recorded_date,
            )
        )

    return FHIRCondition(
        id=cond.id,
        identifier=identifiers,
        clinicalStatus=clinical_status_cc,
        verificationStatus=verification_status_cc,
        category=category_list,
        severity=severity_cc,
        code=code_cc,
        bodySite=body_site_list,
        subject=subject_ref,
        encounter=encounter_ref,
        onsetDateTime=cond.onset_date_time,
        abatementDateTime=cond.abatement_date_time,
        recordedDate=cond.recorded_date,
        recorder=recorder_ref,
        note=notes,
    )


def to_fhir_observation(obs: ClinicalObservation) -> FHIRObservation:
    """Transform internal NIRMAYA ClinicalObservation model into standard HL7 FHIR R4 Observation.

    Translates quantitative readings, multi-component panels (Blood Pressure), reference
    ranges, and clinical interpretation flags into certified FHIR R4 schemas.
    """
    # 1. Identifiers
    identifiers = [
        FHIRIdentifier(
            system=NIRMAYA_OBSERVATION_SYSTEM,
            value=obs.id,
            use="official",
        )
    ]

    # 2. Category
    category_list = [
        FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system=HL7_OBSERVATION_CATEGORY_SYSTEM,
                    code=obs.category.value,
                    display=obs.category.value.replace("-", " ").title(),
                )
            ],
            text=obs.category.value,
        )
    ]

    # 3. Code (LOINC)
    code_cc = FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=obs.code_coding_system,
                code=obs.code_value,
                display=obs.code_display,
            )
        ],
        text=obs.code_display,
    )

    # 4. Subject (Patient)
    patient_display = None
    if getattr(obs, "patient", None) and getattr(obs.patient, "user", None):
        patient_display = obs.patient.user.full_name
    subject_ref = FHIRReference(
        reference=f"Patient/{obs.patient_id}",
        display=patient_display,
        type="Patient",
    )

    # 5. Encounter
    encounter_ref = None
    if obs.encounter_id:
        encounter_ref = FHIRReference(
            reference=f"Encounter/{obs.encounter_id}",
            type="Encounter",
        )

    # 6. Performer (Doctor)
    performers: List[FHIRReference] = []
    if obs.performer_doctor_id:
        doctor_display = None
        if getattr(obs, "performer_doctor", None) and getattr(obs.performer_doctor, "user", None):
            doctor_display = obs.performer_doctor.user.full_name
        performers.append(
            FHIRReference(
                reference=f"Practitioner/{obs.performer_doctor_id}",
                display=doctor_display,
                type="Practitioner",
            )
        )

    # 7. ValueQuantity (for single quantitative observation)
    value_quantity = None
    if obs.value_quantity is not None:
        value_quantity = FHIRQuantity(
            value=obs.value_quantity,
            unit=obs.value_unit,
            system=obs.value_system or UCUM_SYSTEM,
            code=obs.value_code,
        )

    # 8. Reference Range
    ref_ranges: List[FHIRObservationReferenceRange] = []
    if (
        obs.reference_range_low is not None
        or obs.reference_range_high is not None
        or obs.reference_range_text is not None
    ):
        low_qty = None
        if obs.reference_range_low is not None:
            low_qty = FHIRQuantity(
                value=obs.reference_range_low,
                unit=obs.value_unit,
                system=obs.value_system or UCUM_SYSTEM,
                code=obs.value_code,
            )
        high_qty = None
        if obs.reference_range_high is not None:
            high_qty = FHIRQuantity(
                value=obs.reference_range_high,
                unit=obs.value_unit,
                system=obs.value_system or UCUM_SYSTEM,
                code=obs.value_code,
            )
        ref_ranges.append(
            FHIRObservationReferenceRange(
                low=low_qty,
                high=high_qty,
                text=obs.reference_range_text,
            )
        )

    # 9. Interpretation
    interpretations: List[FHIRCodeableConcept] = []
    if obs.interpretation and obs.interpretation in OBSERVATION_INTERPRETATION_MAPPINGS:
        interp_coding = OBSERVATION_INTERPRETATION_MAPPINGS[obs.interpretation]
        interpretations.append(
            FHIRCodeableConcept(
                coding=[interp_coding],
                text=obs.interpretation.value.capitalize(),
            )
        )

    # 10. Multi-components (e.g. Systolic & Diastolic BP)
    components: List[FHIRObservationComponent] = []
    if obs.components:
        for c in obs.components:
            comp_code = FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=c.get("code_system", LOINC_SYSTEM),
                        code=c.get("code_value", ""),
                        display=c.get("code_display", ""),
                    )
                ],
                text=c.get("code_display", ""),
            )
            comp_qty = None
            if c.get("value_quantity") is not None:
                comp_qty = FHIRQuantity(
                    value=float(c["value_quantity"]),
                    unit=c.get("value_unit", "mmHg"),
                    system=UCUM_SYSTEM,
                    code=c.get("value_code", "mm[Hg]"),
                )
            comp_interps: List[FHIRCodeableConcept] = []
            c_interp = c.get("interpretation")
            if c_interp:
                interp_enum = None
                for enum_val in ObservationInterpretation:
                    if enum_val.value == c_interp:
                        interp_enum = enum_val
                        break
                if interp_enum and interp_enum in OBSERVATION_INTERPRETATION_MAPPINGS:
                    comp_interps.append(
                        FHIRCodeableConcept(
                            coding=[OBSERVATION_INTERPRETATION_MAPPINGS[interp_enum]],
                            text=interp_enum.value.capitalize(),
                        )
                    )
            comp_ref_ranges: List[FHIRObservationReferenceRange] = []
            if c.get("reference_range_low") is not None or c.get("reference_range_high") is not None:
                c_low = (
                    FHIRQuantity(value=float(c["reference_range_low"]), unit=c.get("value_unit"))
                    if c.get("reference_range_low") is not None
                    else None
                )
                c_high = (
                    FHIRQuantity(value=float(c["reference_range_high"]), unit=c.get("value_unit"))
                    if c.get("reference_range_high") is not None
                    else None
                )
                comp_ref_ranges.append(
                    FHIRObservationReferenceRange(
                        low=c_low,
                        high=c_high,
                        text=c.get("reference_range_text"),
                    )
                )

            components.append(
                FHIRObservationComponent(
                    code=comp_code,
                    valueQuantity=comp_qty,
                    valueString=c.get("value_string"),
                    interpretation=comp_interps,
                    referenceRange=comp_ref_ranges,
                )
            )

    # 11. Body site & Method
    body_site = None
    if obs.body_site:
        body_site = FHIRCodeableConcept(text=obs.body_site)
    method = None
    if obs.method:
        method = FHIRCodeableConcept(text=obs.method)

    # 12. Notes
    notes: List[FHIRAnnotation] = []
    if obs.note:
        notes.append(
            FHIRAnnotation(
                text=obs.note,
                time=obs.issued_date_time,
            )
        )

    return FHIRObservation(
        id=obs.id,
        identifier=identifiers,
        status=obs.status.value,
        category=category_list,
        code=code_cc,
        subject=subject_ref,
        encounter=encounter_ref,
        effectiveDateTime=obs.effective_date_time,
        issued=obs.issued_date_time,
        performer=performers,
        valueQuantity=value_quantity,
        valueString=obs.value_string,
        interpretation=interpretations,
        note=notes,
        bodySite=body_site,
        method=method,
        referenceRange=ref_ranges,
        component=components,
    )


# ============================================================================
# HL7 FHIR Release 4 Composition Transformer (Clinical SOAP Notes)
# ============================================================================


def to_fhir_composition(note: SoapNote) -> FHIRComposition:
    """Transforms a relational SoapNote clinical document into an HL7 FHIR R4 Composition resource.

    Formats standard LOINC narrative sections:
    - Chief Complaint (LOINC 10154-3)
    - Subjective narrative (LOINC 61150-9)
    - Objective examination & observations (LOINC 61149-1)
    - Assessment & clinical evaluation (LOINC 51848-0)
    - Plan of care & therapeutics (LOINC 18776-5)
    """
    # 1. Subject reference (Patient)
    patient_display = (
        getattr(getattr(note, "patient", None), "abha_address", None)
        or f"Patient {note.patient_id}"
    )
    subject_ref = FHIRReference(
        reference=f"Patient/{note.patient_id}",
        display=patient_display,
    )

    # 2. Encounter reference (Encounter)
    encounter_ref = None
    if note.encounter_id:
        encounter_ref = FHIRReference(
            reference=f"Encounter/{note.encounter_id}",
            display=f"Encounter {note.encounter_id}",
        )

    # 3. Practitioner Author reference
    authors = []
    if note.doctor_id:
        doc_display = (
            getattr(getattr(note, "doctor", None), "registration_number", None)
            or f"Practitioner {note.doctor_id}"
        )
        authors.append(
            FHIRReference(
                reference=f"Practitioner/{note.doctor_id}",
                display=doc_display,
            )
        )

    # 4. Note classification LOINC coding
    type_code = "11506-3"
    type_display = "Provider-unspecified Progress note"
    if note.note_type == ClinicalNoteType.CONSULTATION:
        type_code = "11488-4"
        type_display = "Consultation note"
    elif note.note_type == ClinicalNoteType.DISCHARGE_SUMMARY:
        type_code = "18842-5"
        type_display = "Discharge summary"

    doc_type = FHIRCodeableConcept(
        coding=[
            FHIRCoding(
                system=LOINC_SYSTEM,
                code=type_code,
                display=type_display,
            )
        ],
        text=note.title,
    )

    doc_category = [
        FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system=LOINC_SYSTEM,
                    code="LP173421-1",
                    display="Report",
                )
            ],
            text="Clinical Encounter Documentation",
        )
    ]

    # 5. Build structured LOINC sections
    sections: List[FHIRCompositionSection] = [
        FHIRCompositionSection(
            title="Chief Complaint",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=LOINC_SYSTEM,
                        code="10154-3",
                        display="Chief complaint narrative",
                    )
                ],
                text="Chief Complaint",
            ),
            text=FHIRNarrative(
                status="generated",
                div=f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{note.chief_complaint}</p></div>",
            ),
        ),
        FHIRCompositionSection(
            title="Subjective",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=LOINC_SYSTEM,
                        code="61150-9",
                        display="Subjective narrative",
                    )
                ],
                text="Subjective",
            ),
            text=FHIRNarrative(
                status="generated",
                div=f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{note.subjective}</p></div>",
            ),
        ),
        FHIRCompositionSection(
            title="Objective",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=LOINC_SYSTEM,
                        code="61149-1",
                        display="Objective narrative",
                    )
                ],
                text="Objective",
            ),
            text=FHIRNarrative(
                status="generated",
                div=f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{note.objective}</p></div>",
            ),
        ),
        FHIRCompositionSection(
            title="Assessment",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=LOINC_SYSTEM,
                        code="51848-0",
                        display="Evaluation note",
                    )
                ],
                text="Assessment",
            ),
            text=FHIRNarrative(
                status="generated",
                div=f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{note.assessment}</p></div>",
            ),
        ),
        FHIRCompositionSection(
            title="Plan",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system=LOINC_SYSTEM,
                        code="18776-5",
                        display="Plan of care note",
                    )
                ],
                text="Plan",
            ),
            text=FHIRNarrative(
                status="generated",
                div=f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{note.plan}</p></div>",
            ),
        ),
    ]

    effective_date = note.signed_at or note.updated_at or note.created_at

    return FHIRComposition(
        id=note.id,
        identifier=FHIRIdentifier(
            system=NIRMAYA_COMPOSITION_SYSTEM,
            value=note.id,
        ),
        status=note.status.value,
        type=doc_type,
        category=doc_category,
        subject=subject_ref,
        encounter=encounter_ref,
        date=effective_date,
        author=authors,
        title=note.title,
        section=sections,
    )






