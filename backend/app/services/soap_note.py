"""Structured SOAP Clinical Notes service layer for NIRMAYA platform.

Provides business logic for documenting clinical encounters in Subjective, Objective,
Assessment, Plan format, validating clinical actors, managing note lifecycles, and
applying tamper-evident SHA-256 digital signature attestation.
"""

from datetime import datetime, timezone
import hashlib
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EntityNotFoundException
from app.models.appointment import Appointment
from app.models.doctor import DoctorProfile
from app.models.enums import ClinicalNoteStatus, ClinicalNoteType
from app.models.patient import PatientProfile
from app.models.soap_note import SoapNote
from app.schemas.soap_note import (
    SoapNoteCreate,
    SoapNoteFilter,
    SoapNoteSignRequest,
    SoapNoteUpdate,
)


async def create_soap_note(
    db: AsyncSession,
    patient_id: str,
    payload: SoapNoteCreate,
    author_doctor_id: Optional[str] = None,
) -> SoapNote:
    """Create a new preliminary structured SOAP clinical note for a patient encounter."""
    # 1. Verify patient exists
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    # 2. Resolve and verify doctor author
    effective_doctor_id = payload.doctor_id or author_doctor_id
    if effective_doctor_id:
        doctor = await db.scalar(select(DoctorProfile).where(DoctorProfile.id == effective_doctor_id))
        if not doctor:
            raise EntityNotFoundException("Doctor", effective_doctor_id)

    # 3. Verify encounter if provided
    if payload.encounter_id:
        appt = await db.scalar(select(Appointment).where(Appointment.id == payload.encounter_id))
        if not appt:
            raise EntityNotFoundException("Appointment", payload.encounter_id)

    # 4. Instantiate entity
    note = SoapNote(
        patient_id=patient_id,
        doctor_id=effective_doctor_id,
        encounter_id=payload.encounter_id,
        note_type=payload.note_type,
        status=payload.status or ClinicalNoteStatus.PRELIMINARY,
        title=payload.title,
        chief_complaint=payload.chief_complaint,
        subjective=payload.subjective,
        objective=payload.objective,
        assessment=payload.assessment,
        plan=payload.plan,
        primary_diagnosis_code=payload.primary_diagnosis_code,
        primary_diagnosis_display=payload.primary_diagnosis_display,
        follow_up_instructions=payload.follow_up_instructions,
        is_signed=False,
        signed_at=None,
        signature_hash=None,
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)
    return await get_soap_note_by_id(db, note.id)


async def get_soap_note_by_id(db: AsyncSession, note_id: str) -> SoapNote:
    """Retrieve a specific clinical note with eager-loaded patient, doctor, and encounter."""
    stmt = (
        select(SoapNote)
        .options(
            selectinload(SoapNote.patient),
            selectinload(SoapNote.doctor),
            selectinload(SoapNote.encounter),
        )
        .where(SoapNote.id == note_id)
    )
    res = await db.execute(stmt)
    note = res.scalar_one_or_none()
    if not note:
        raise EntityNotFoundException("SoapNote", note_id)
    return note


async def list_patient_soap_notes(
    db: AsyncSession,
    patient_id: str,
    filters: Optional[SoapNoteFilter] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[SoapNote], int]:
    """Query longitudinal clinical encounter notes for a patient with optional filters."""
    patient = await db.scalar(select(PatientProfile).where(PatientProfile.id == patient_id))
    if not patient:
        raise EntityNotFoundException("Patient", patient_id)

    base_query = select(SoapNote).where(SoapNote.patient_id == patient_id)

    if filters:
        if filters.status:
            base_query = base_query.where(SoapNote.status == filters.status)
        if filters.note_type:
            base_query = base_query.where(SoapNote.note_type == filters.note_type)
        if filters.encounter_id:
            base_query = base_query.where(SoapNote.encounter_id == filters.encounter_id)
        if filters.is_signed is not None:
            base_query = base_query.where(SoapNote.is_signed == filters.is_signed)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    data_stmt = (
        base_query.options(
            selectinload(SoapNote.patient),
            selectinload(SoapNote.doctor),
            selectinload(SoapNote.encounter),
        )
        .order_by(SoapNote.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    data_res = await db.execute(data_stmt)
    notes = list(data_res.scalars().all())

    return notes, total


async def update_soap_note(
    db: AsyncSession,
    note_id: str,
    payload: SoapNoteUpdate,
) -> SoapNote:
    """Update an existing clinical note prior to final cryptographic signature."""
    note = await get_soap_note_by_id(db, note_id)

    if note.is_signed:
        raise ValueError(
            "Cannot modify a finalized and digitally signed clinical note. "
            "Signed clinical documents are immutable under FHIR & ABDM standards."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return note


async def sign_soap_note(
    db: AsyncSession,
    note_id: str,
    payload: Optional[SoapNoteSignRequest] = None,
    signing_doctor_id: Optional[str] = None,
) -> SoapNote:
    """Electronically sign and finalize a clinical note with SHA-256 tamper-evident digest."""
    note = await get_soap_note_by_id(db, note_id)

    if note.is_signed:
        raise ValueError("Clinical note is already finalized and signed.")

    if signing_doctor_id and not note.doctor_id:
        note.doctor_id = signing_doctor_id

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    signature_payload = (
        f"id:{note.id}|patient:{note.patient_id}|doctor:{note.doctor_id}|"
        f"encounter:{note.encounter_id}|cc:{note.chief_complaint}|"
        f"s:{note.subjective}|o:{note.objective}|a:{note.assessment}|p:{note.plan}|"
        f"dx:{note.primary_diagnosis_code}|signed_at:{now_iso}"
    )
    signature_hash = hashlib.sha256(signature_payload.encode("utf-8")).hexdigest()

    note.is_signed = True
    note.signed_at = now
    note.status = ClinicalNoteStatus.FINAL
    note.signature_hash = signature_hash

    if payload and payload.comments:
        if note.follow_up_instructions:
            note.follow_up_instructions += f" [Attestation: {payload.comments}]"
        else:
            note.follow_up_instructions = f"[Attestation: {payload.comments}]"

    await db.commit()
    await db.refresh(note)
    return note


async def delete_soap_note(db: AsyncSession, note_id: str) -> None:
    """Mark note as entered-in-error if signed, or permanently purge if draft."""
    note = await get_soap_note_by_id(db, note_id)

    if note.is_signed:
        note.status = ClinicalNoteStatus.ENTERED_IN_ERROR
        await db.commit()
    else:
        await db.delete(note)
        await db.commit()


class SoapNoteService:
    """Class wrapper providing object-oriented access to SOAP note service functions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_soap_note(
        self, patient_id: str, payload: SoapNoteCreate, author_doctor_id: Optional[str] = None
    ) -> SoapNote:
        return await create_soap_note(self.db, patient_id, payload, author_doctor_id)

    async def get_soap_note_by_id(self, note_id: str) -> SoapNote:
        return await get_soap_note_by_id(self.db, note_id)

    async def list_patient_soap_notes(
        self, patient_id: str, filters: Optional[SoapNoteFilter] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[SoapNote], int]:
        return await list_patient_soap_notes(self.db, patient_id, filters, limit, offset)

    async def update_soap_note(self, note_id: str, payload: SoapNoteUpdate) -> SoapNote:
        return await update_soap_note(self.db, note_id, payload)

    async def sign_soap_note(
        self, note_id: str, payload: Optional[SoapNoteSignRequest] = None, signing_doctor_id: Optional[str] = None
    ) -> SoapNote:
        return await sign_soap_note(self.db, note_id, payload, signing_doctor_id)

    async def delete_soap_note(self, note_id: str) -> None:
        return await delete_soap_note(self.db, note_id)
