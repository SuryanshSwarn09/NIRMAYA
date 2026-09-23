"""NIRMAYA services package exposing modular domain business logic."""

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
]
