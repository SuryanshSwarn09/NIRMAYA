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
    abdm_certification,
    abdm_security_audit,
    fhir_validator,
    terminology_validator,
    websockets,
    opd_queue,
    clinical_alerts,
    emergency_vault,
    audit_ledger,
    security_scan,
    asvs_audit,
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
api_router.include_router(abdm_certification.router, prefix="/abdm/certification", tags=["ABDM Sandbox E2E Certification & Regression"])
api_router.include_router(abdm_security_audit.router, prefix="/abdm/security", tags=["ABDM Security Penetration & Consent Hardening"])
api_router.include_router(fhir_validator.router, prefix="/fhir", tags=["FHIR R4 Bundle Validation & NRCES Profiles"])
api_router.include_router(terminology_validator.router, prefix="/fhir/ontology", tags=["FHIR R4 Medical Ontology & Terminology Binding"])
api_router.include_router(websockets.router, prefix="/websockets", tags=["WebSockets & Real-Time Event Bus"])
api_router.include_router(opd_queue.router, prefix="/queue", tags=["OPD Consultation Queue & Live Sync"])
api_router.include_router(clinical_alerts.router, prefix="/alerts", tags=["Clinical Alerts & Lab Panic Values"])
api_router.include_router(emergency_vault.router, prefix="/emergency/btg", tags=["Break-The-Glass Emergency Access"])
api_router.include_router(audit_ledger.router, prefix="/audit/ledger", tags=["Audit Ledger & Emergency Dispatch"])
api_router.include_router(security_scan.router, prefix="/security", tags=["Security & Vulnerability Auditing"])
api_router.include_router(asvs_audit.router, prefix="/security", tags=["OWASP ASVS & DoS Shield"])
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



