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
    abdm_issuance,
    patient_auth,
    abdm_m2_bridge,
    abdm_m3_consent,
    abdm_m3_crypto,
    abdm_m3_transfer,
    abdm_m3_hiu,
    abdm_m3_audit,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health & Telemetry"])
api_router.include_router(meta.router, prefix="", tags=["Interoperability & Metadata"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patient_auth.router, prefix="", tags=["Passwordless Patient Authentication"])
api_router.include_router(digilocker.router, prefix="", tags=["DigiLocker Identity & e-Aadhaar"])
api_router.include_router(abdm_m1.router, prefix="", tags=["ABDM M1 - Aadhaar Demographic OTP Verification"])
api_router.include_router(abdm_issuance.router, prefix="", tags=["ABDM M1 - ABHA Issuance & HPR Onboarding"])
api_router.include_router(abdm_m2_bridge.router, prefix="/abdm/m2/bridge", tags=["ABDM M2 - HIP Bridge & Webhooks"])
api_router.include_router(abdm_m3_consent.router, prefix="/abdm/m3/consent", tags=["ABDM M3 - Consent Management"])
api_router.include_router(abdm_m3_crypto.router, prefix="/abdm/m3/crypto", tags=["ABDM M3 - Key Exchange & Cryptography"])
api_router.include_router(abdm_m3_transfer.router, prefix="/abdm/m3/transfer", tags=["ABDM M3 - Data Transfer & Encryption"])
api_router.include_router(abdm_m3_hiu.router, prefix="/abdm/m3/hiu", tags=["ABDM M3 - HIU Data Consumer & Decryption"])
api_router.include_router(abdm_m3_audit.router, prefix="/abdm/m3/audit", tags=["ABDM M3 - Integration Audit & Compliance"])
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



