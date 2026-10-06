from app.services.appointment import (
    book_appointment,
    get_appointment_by_id,
    list_appointments,
    update_appointment_status,
)
from app.services.condition import (
    delete_condition,
    get_condition_by_id,
    list_patient_conditions,
    record_condition,
    update_condition,
)
from app.services.doctor import (
    create_doctor_profile,
    delete_doctor_profile,
    get_doctor_by_hpr_id,
    get_doctor_by_id,
    get_doctor_by_registration_number,
    get_doctor_by_user_id,
    list_doctors,
    update_doctor_profile,
)
from app.services.patient import (
    create_patient_profile,
    delete_patient_profile,
    get_patient_by_abha,
    get_patient_by_id,
    get_patient_by_user_id,
    list_patients,
    update_patient_profile,
)
from app.services.slot_engine import (
    generate_slots_for_doctor,
    get_doctor_slots,
    get_slot_by_id,
    hold_slot,
    release_slot_hold,
    sweep_expired_holds,
)
from app.services.observation import (
    record_observation,
    get_observation_by_id,
    list_patient_observations,
    get_latest_vitals_summary,
    update_observation,
)
from app.services.soap_note import (
    create_soap_note,
    get_soap_note_by_id,
    list_patient_soap_notes,
    update_soap_note,
    sign_soap_note,
    delete_soap_note,
    SoapNoteService,
)

__all__ = [
    # Patient service
    "get_patient_by_id",
    "get_patient_by_user_id",
    "get_patient_by_abha",
    "list_patients",
    "create_patient_profile",
    "update_patient_profile",
    "delete_patient_profile",
    # Doctor service
    "get_doctor_by_id",
    "get_doctor_by_user_id",
    "get_doctor_by_registration_number",
    "get_doctor_by_hpr_id",
    "list_doctors",
    "create_doctor_profile",
    "update_doctor_profile",
    "delete_doctor_profile",
    # Slot engine
    "generate_slots_for_doctor",
    "get_doctor_slots",
    "get_slot_by_id",
    "sweep_expired_holds",
    "hold_slot",
    "release_slot_hold",
    # Appointment service
    "book_appointment",
    "get_appointment_by_id",
    "list_appointments",
    "update_appointment_status",
    # Condition service
    "record_condition",
    "get_condition_by_id",
    "list_patient_conditions",
    "update_condition",
    "delete_condition",
    # Observation service
    "record_observation",
    "get_observation_by_id",
    "list_patient_observations",
    "get_latest_vitals_summary",
    "update_observation",
    # SOAP note service
    "create_soap_note",
    "get_soap_note_by_id",
    "list_patient_soap_notes",
    "update_soap_note",
    "sign_soap_note",
    "delete_soap_note",
    "SoapNoteService",
]
