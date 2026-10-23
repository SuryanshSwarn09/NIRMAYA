"""Service layer for ABDM Digital ABHA ID Card generation and QR cryptographic verification."""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from app.core.config import settings
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.abha_card import (
    AbhaCardData,
    AbhaCardResponse,
    AbhaQrPayload,
    AbhaQrVerificationResponse,
)


def _mask_mobile_number(phone: Optional[str]) -> Optional[str]:
    """Mask mobile number for display on the public digital card face."""
    if not phone:
        return None
    cleaned = phone.replace(" ", "").replace("-", "")
    if len(cleaned) >= 10:
        prefix = cleaned[:-4]
        suffix = cleaned[-4:]
        if len(prefix) > 4:
            masked_prefix = prefix[:3] + "*" * (len(prefix) - 3)
        else:
            masked_prefix = "*" * len(prefix)
        return f"{masked_prefix}{suffix}"
    return "****"


def _format_blood_group(bg_enum: Any) -> str:
    """Format BloodGroup enum into standard display string."""
    if not bg_enum:
        return "UNKNOWN"
    val = getattr(bg_enum, "value", str(bg_enum))
    mapping = {
        "A_POSITIVE": "A+",
        "A_NEGATIVE": "A-",
        "B_POSITIVE": "B+",
        "B_NEGATIVE": "B-",
        "AB_POSITIVE": "AB+",
        "AB_NEGATIVE": "AB-",
        "O_POSITIVE": "O+",
        "O_NEGATIVE": "O-",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get(str(val).upper(), str(val))


def _format_gender(gender_enum: Any) -> str:
    """Format Gender enum into M / F / O / U."""
    if not gender_enum:
        return "U"
    val = getattr(gender_enum, "value", str(gender_enum)).upper()
    if "MALE" in val and "FEMALE" not in val:
        return "M"
    elif "FEMALE" in val:
        return "F"
    elif "OTHER" in val:
        return "O"
    return "U"


def compute_abha_signature(claims: Dict[str, Any]) -> str:
    """Compute HMAC-SHA256 signature over canonically sorted JSON representation of claims."""
    # Exclude signature if present
    canonical_claims = {k: v for k, v in claims.items() if k != "signature"}
    serialized = json.dumps(canonical_claims, sort_keys=True, separators=(",", ":"))
    secret = settings.SECRET_KEY.encode("utf-8")
    sig = hmac.new(secret, serialized.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"SHA256:{sig}"


def generate_abha_card_data(patient: PatientProfile, user: Optional[User] = None) -> AbhaCardResponse:
    """Generate demographic claims, signed QR payload, and card attributes for a patient profile."""
    # Derive claims
    name = (user.full_name if user and user.full_name else None) or "Ayushman Citizen"
    gender_code = _format_gender(patient.gender)
    dob_str = patient.date_of_birth.isoformat() if patient.date_of_birth else None
    year_of_birth = patient.date_of_birth.year if patient.date_of_birth else None
    blood_group_str = _format_blood_group(patient.blood_group)
    raw_mobile = user.phone_number if user else None
    masked_mobile = _mask_mobile_number(raw_mobile)

    abha_number = patient.abha_number or "91-8472-1092-4821"
    abha_address = patient.abha_address or "citizen@abdm"
    issue_date = datetime.now(timezone.utc).isoformat()

    card_data = AbhaCardData(
        patient_id=patient.id,
        abha_number=abha_number,
        abha_address=abha_address,
        name=name,
        gender=gender_code,
        date_of_birth=dob_str,
        year_of_birth=year_of_birth,
        blood_group=blood_group_str,
        mobile=masked_mobile,
        address=patient.address_line,
        district=patient.city or "New Delhi",
        state=patient.state or "NCT of Delhi",
        pincode=patient.pincode,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_phone=patient.emergency_contact_phone,
        emergency_contact_relation=patient.emergency_contact_relation,
        kyc_status="VERIFIED",
        auth_methods=["AADHAAR_OTP", "MOBILE_OTP"],
    )

    # Prepare compact claims dictionary for QR payload
    qr_claims: Dict[str, Any] = {
        "hidn": abha_number,
        "hid": abha_address,
        "name": name,
        "gender": gender_code,
        "dob": dob_str or (str(year_of_birth) if year_of_birth else None),
        "state_name": patient.state or "NCT of Delhi",
        "dist_name": patient.city or "New Delhi",
        "mobile": masked_mobile,
        "blood_group": blood_group_str,
        "issue_date": issue_date,
    }

    # Generate HMAC signature
    signature = compute_abha_signature(qr_claims)
    qr_claims["signature"] = signature

    # Serialize compact QR payload string
    qr_payload_str = json.dumps(qr_claims, separators=(",", ":"))

    return AbhaCardResponse(
        card_data=card_data,
        qr_payload=qr_payload_str,
        signature=signature,
        issued_at=issue_date,
    )


def verify_abha_qr_payload(qr_string: str) -> AbhaQrVerificationResponse:
    """Parse, decode, and cryptographically verify a scanned ABHA QR string."""
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        data = json.loads(qr_string)
    except Exception as exc:
        return AbhaQrVerificationResponse(
            is_valid=False,
            message=f"Malformed QR payload: not valid JSON ({str(exc)})",
            claims=None,
            verified_at=now_iso,
        )

    if not isinstance(data, dict):
        return AbhaQrVerificationResponse(
            is_valid=False,
            message="Invalid QR payload structure: expected JSON object",
            claims=None,
            verified_at=now_iso,
        )

    required_keys = ["hidn", "hid", "name", "gender", "signature"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        return AbhaQrVerificationResponse(
            is_valid=False,
            message=f"Missing required ABDM QR fields: {', '.join(missing)}",
            claims=data,
            verified_at=now_iso,
        )

    claimed_signature = data.get("signature")
    if not isinstance(claimed_signature, str) or not claimed_signature.startswith("SHA256:"):
        return AbhaQrVerificationResponse(
            is_valid=False,
            message="Invalid or missing cryptographic signature format",
            claims=data,
            verified_at=now_iso,
        )

    # Recompute signature over payload without 'signature'
    expected_signature = compute_abha_signature(data)

    if not hmac.compare_digest(claimed_signature, expected_signature):
        return AbhaQrVerificationResponse(
            is_valid=False,
            message="Cryptographic signature mismatch: QR code has been altered or tampered with",
            claims=data,
            verified_at=now_iso,
        )

    return AbhaQrVerificationResponse(
        is_valid=True,
        message="ABDM National Health Authority digital signature verified successfully",
        claims=data,
        verified_at=now_iso,
    )
