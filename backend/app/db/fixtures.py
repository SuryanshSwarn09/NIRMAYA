"""Synthetic clinical data fixtures for NIRMAYA database seeding and integration testing.

Conforms to HL7 FHIR R4 clinical coding and Ayushman Bharat Digital Mission (ABDM)
standards including 14-digit ABHA IDs, @abdm handles, @hpr.abdm doctor IDs, and IN-STATE-HFR-XXXXXX lab IDs.
"""

from datetime import date
from typing import Any, Dict, List
from app.models.enums import BloodGroup, Gender, LabAccreditation, MedicalSpecialty, UserRole

# ----------------------------------------------------------------------------
# 1. System Administrator Fixture
# ----------------------------------------------------------------------------
ADMIN_FIXTURE: Dict[str, Any] = {
    "email": "admin@nirmaya.health",
    "full_name": "NIRMAYA Root Administrator",
    "phone_number": "+919800000001",
    "role": UserRole.ADMIN,
    "supabase_uid": "sb-auth-admin-root-001",
    "is_active": True,
    "is_verified": True,
}

# ----------------------------------------------------------------------------
# 2. Synthetic Patient Fixtures (Demographics + ABHA Registry)
# ----------------------------------------------------------------------------
PATIENT_FIXTURES: List[Dict[str, Any]] = [
    {
        "user": {
            "email": "arun.patel@example.com",
            "full_name": "Arun Patel",
            "phone_number": "+919876543210",
            "role": UserRole.PATIENT,
            "supabase_uid": "sb-auth-patient-001",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "date_of_birth": date(1985, 4, 12),
            "gender": Gender.MALE,
            "blood_group": BloodGroup.B_POSITIVE,
            "address_line": "B-402, Shivalik Residency, Satellite",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "pincode": "380015",
            "emergency_contact_name": "Kavita Patel",
            "emergency_contact_phone": "+919876543211",
            "emergency_contact_relation": "Spouse",
            "abha_number": "91-1029-3847-5610",
            "abha_address": "arun.patel@abdm",
        },
    },
    {
        "user": {
            "email": "meera.nair@example.com",
            "full_name": "Meera Nair",
            "phone_number": "+919812345678",
            "role": UserRole.PATIENT,
            "supabase_uid": "sb-auth-patient-002",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "date_of_birth": date(1992, 8, 25),
            "gender": Gender.FEMALE,
            "blood_group": BloodGroup.O_POSITIVE,
            "address_line": "Flat 7C, Marine View Apartments, Panampilly Nagar",
            "city": "Kochi",
            "state": "Kerala",
            "pincode": "682036",
            "emergency_contact_name": "Ramesh Nair",
            "emergency_contact_phone": "+919812345679",
            "emergency_contact_relation": "Father",
            "abha_number": "91-2233-4455-6677",
            "abha_address": "meera.nair@abdm",
        },
    },
    {
        "user": {
            "email": "priya.sharma@example.com",
            "full_name": "Priya Sharma",
            "phone_number": "+919799887766",
            "role": UserRole.PATIENT,
            "supabase_uid": "sb-auth-patient-003",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "date_of_birth": date(1998, 11, 3),
            "gender": Gender.FEMALE,
            "blood_group": BloodGroup.A_POSITIVE,
            "address_line": "Villa 12, Palm Meadows, Whitefield",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560066",
            "emergency_contact_name": "Sunil Sharma",
            "emergency_contact_phone": "+919799887765",
            "emergency_contact_relation": "Brother",
            "abha_number": "91-9988-7766-5544",
            "abha_address": "priya.sharma@abdm",
        },
    },
]

# ----------------------------------------------------------------------------
# 3. Synthetic Doctor Fixtures (Medical Council Licensing + ABDM HPR)
# ----------------------------------------------------------------------------
DOCTOR_FIXTURES: List[Dict[str, Any]] = [
    {
        "user": {
            "email": "dr.rajesh@nirmaya.health",
            "full_name": "Dr. Rajesh Sharma",
            "phone_number": "+919820011223",
            "role": UserRole.DOCTOR,
            "supabase_uid": "sb-auth-doctor-001",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "registration_number": "MCI-2008-14259",
            "medical_council": "Delhi Medical Council",
            "specialty": MedicalSpecialty.CARDIOLOGY,
            "qualifications": "MBBS, MD (General Medicine), DM (Cardiology)",
            "experience_years": 16,
            "consultation_fee": 1500,
            "hospital_affiliation": "Apollo Indraprastha Hospital, New Delhi",
            "bio": "Senior Consultant Interventional Cardiologist specializing in preventive coronary interventions and cardiac rehabilitation.",
            "is_available_for_teleconsult": True,
            "hpr_id": "dr.rajesh@hpr.abdm",
        },
    },
    {
        "user": {
            "email": "dr.anita@nirmaya.health",
            "full_name": "Dr. Anita Desai",
            "phone_number": "+919822334455",
            "role": UserRole.DOCTOR,
            "supabase_uid": "sb-auth-doctor-002",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "registration_number": "MMC-2012-08912",
            "medical_council": "Maharashtra Medical Council",
            "specialty": MedicalSpecialty.PEDIATRICS,
            "qualifications": "MBBS, DCH, MD (Pediatrics)",
            "experience_years": 12,
            "consultation_fee": 1000,
            "hospital_affiliation": "Manipal Hospital, Whitefield, Bengaluru",
            "bio": "Pediatrician and neonatal care specialist focused on early childhood developmental screening and comprehensive immunization.",
            "is_available_for_teleconsult": True,
            "hpr_id": "dr.anita@hpr.abdm",
        },
    },
    {
        "user": {
            "email": "dr.vikram@nirmaya.health",
            "full_name": "Dr. Vikram Sen",
            "phone_number": "+919833445566",
            "role": UserRole.DOCTOR,
            "supabase_uid": "sb-auth-doctor-003",
            "is_active": True,
            "is_verified": True,
        },
        "profile": {
            "registration_number": "KMC-2015-45210",
            "medical_council": "Karnataka Medical Council",
            "specialty": MedicalSpecialty.NEUROLOGY,
            "qualifications": "MBBS, MD (Medicine), DM (Neurology)",
            "experience_years": 9,
            "consultation_fee": 1200,
            "hospital_affiliation": "Fortis Hospital, Bannerghatta Road, Bengaluru",
            "bio": "Consultant Neurologist specializing in neuro-rehabilitation, stroke management, and chronic migraine therapies.",
            "is_available_for_teleconsult": True,
            "hpr_id": "dr.vikram@hpr.abdm",
        },
    },
]

# ----------------------------------------------------------------------------
# 4. Synthetic Diagnostic Lab Facilities (NABL/CAP Accreditation + ABDM HFR)
# ----------------------------------------------------------------------------
LAB_FIXTURES: List[Dict[str, Any]] = [
    {
        "user": {
            "email": "admin.apollo@diagnostics.example.com",
            "full_name": "Apollo Diagnostics Hub",
            "phone_number": "+919844556677",
            "role": UserRole.LAB,
            "supabase_uid": "sb-auth-lab-001",
            "is_active": True,
            "is_verified": True,
        },
        "facility": {
            "facility_name": "Apollo Diagnostics Center",
            "license_number": "DL-LAB-2021-0089",
            "accreditation": LabAccreditation.NABL,
            "accreditation_number": "NABL-MC-5421",
            "is_nabl_certified": True,
            "contact_person": "Dr. S. K. Gupta",
            "contact_phone": "+911145678901",
            "contact_email": "reports.delhi@apollodiagnostics.example.com",
            "address_line": "Plot 14, Institutional Area, Sector 32",
            "city": "Gurugram",
            "state": "Haryana",
            "pincode": "122001",
            "supported_tests": "Complete Blood Count (CBC), Lipid Profile, HbA1c, Thyroid Stimulating Hormone (TSH), Liver Function Test (LFT), Renal Function Test (KFT), RT-PCR",
            "hfr_id": "IN-HR-HFR-001234",
        },
    },
    {
        "user": {
            "email": "admin.metropolis@diagnostics.example.com",
            "full_name": "Metropolis Healthcare Hub",
            "phone_number": "+919855667788",
            "role": UserRole.LAB,
            "supabase_uid": "sb-auth-lab-002",
            "is_active": True,
            "is_verified": True,
        },
        "facility": {
            "facility_name": "Metropolis Diagnostic Research Center",
            "license_number": "MH-LAB-2019-4512",
            "accreditation": LabAccreditation.CAP,
            "accreditation_number": "CAP-89214",
            "is_nabl_certified": True,
            "contact_person": "Dr. Meenakshi Sundaram",
            "contact_phone": "+912266778899",
            "contact_email": "dispatch.mumbai@metropolis.example.com",
            "address_line": "Central Avenue, MIDC Andheri East",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400093",
            "supported_tests": "Vitamin D3 & B12, Cardiac Risk Markers, Cancer Tumor Markers (CA-125, PSA), Allergy Profiling, Autoimmune Screen (ANA)",
            "hfr_id": "IN-MH-HFR-005678",
        },
    },
    {
        "user": {
            "email": "admin.thyrocare@diagnostics.example.com",
            "full_name": "Thyrocare Diagnostics Node",
            "phone_number": "+919866778899",
            "role": UserRole.LAB,
            "supabase_uid": "sb-auth-lab-003",
            "is_active": True,
            "is_verified": True,
        },
        "facility": {
            "facility_name": "Thyrocare Diagnostic Laboratory",
            "license_number": "KA-LAB-2022-7821",
            "accreditation": LabAccreditation.ISO_15189,
            "accreditation_number": "ISO-15189-9821",
            "is_nabl_certified": True,
            "contact_person": "Anand Varma",
            "contact_phone": "+918023456789",
            "contact_email": "care.blr@thyrocare.example.com",
            "address_line": "100 Feet Ring Road, 4th Block, Koramangala",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560034",
            "supported_tests": "Master Health Checkup Panel, Thyroid Profile Ultra, Diabetic Monitoring Panel, Electrolytes Panel",
            "hfr_id": "IN-KA-HFR-009012",
        },
    },
]


def get_all_fixtures() -> Dict[str, Any]:
    """Retrieve structured dictionary containing all synthetic fixtures."""
    return {
        "admin": ADMIN_FIXTURE,
        "patients": PATIENT_FIXTURES,
        "doctors": DOCTOR_FIXTURES,
        "labs": LAB_FIXTURES,
    }
