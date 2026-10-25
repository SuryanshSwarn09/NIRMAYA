from fastapi import APIRouter
from app.api.v1.endpoints import (
    appointments,
    auth,
    conditions,
    diagnostics,
    doctors,
    health,
    medications,
    medication_requests,
    medication_dispenses,
    meta,
    observations,
    patients,
    soap_notes,
    abdm,
    digilocker,
    abdm_m1,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health & Telemetry"])
api_router.include_router(meta.router, prefix="", tags=["Interoperability & Metadata"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(digilocker.router, prefix="", tags=["DigiLocker Identity & e-Aadhaar"])
api_router.include_router(abdm_m1.router, prefix="", tags=["ABDM M1 - Aadhaar Demographic OTP Verification"])
api_router.include_router(abdm.router, prefix="", tags=["ABDM Gateway & National Interoperability"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Vault"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctor EMR"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Clinical Appointments"])
api_router.include_router(conditions.router, prefix="", tags=["Clinical Conditions & Problem List"])
api_router.include_router(observations.router, prefix="", tags=["Clinical Observations & Vital Signs"])
api_router.include_router(soap_notes.router, prefix="", tags=["Clinical SOAP Notes & Encounter Documentation"])
api_router.include_router(diagnostics.router, prefix="", tags=["Diagnostic Orders & Laboratory Reports"])
api_router.include_router(medications.router, prefix="", tags=["Medications"])
api_router.include_router(medication_requests.router, prefix="", tags=["Electronic Prescriptions & Medication Requests"])
api_router.include_router(medication_dispenses.router, prefix="", tags=["Pharmacy Dispense & Fulfillment"])



