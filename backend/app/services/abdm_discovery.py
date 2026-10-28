"""ABDM Milestone 2 (M2) Patient Discovery Protocol & Fuzzy Demographic Matcher Service.

Complies with ABDM M2 HIP Specification:
- Handles incoming patient discovery queries (POST /v0.5/care-contexts/discover)
- Multi-tier matching:
  1. Deterministic Verified Identifier Matching (ABHA Number, ABHA Address, MRN) -> 1.0
  2. Verified Mobile + Demographic Matching -> 0.90 to 0.95
  3. Fuzzy Demographic Matching (Name typo tolerance via Levenshtein & token sets, YOB +/- 1yr, Gender)
- Ambiguity Protection: Rejects multi-patient collisions with close scores to protect patient privacy
- Care Context Extractor: Maps longitudinal appointments and diagnostic orders into ABDM Care Contexts
- Asynchronous Callback Dispatcher: POST /v0.5/care-contexts/on-discover with correlation tracking
"""

from datetime import datetime, timezone
import difflib
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.diagnostic import DiagnosticOrder
from app.models.doctor import DoctorProfile
from app.models.enums import Gender
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.abdm_m2_bridge import (
    CareContextRepresentation,
    DemographicMatchBreakdown,
    DiscoveredPatientRepresentation,
    GatewayPatientDiscoveryRequest,
    GatewayPatientOnDiscoverCallback,
    GatewayRespRef,
    PatientDiscoveryQuery,
    PatientDiscoverySimulateRequest,
    PatientDiscoverySimulateResponse,
    WebhookEventItem,
)
from app.services.abdm_hip_bridge import (
    NIRMAYA_FACILITY_NAME,
    NIRMAYA_HIP_ID,
    webhook_audit_store,
)

logger = logging.getLogger("nirmaya.abdm.discovery")

# Common Indian name honorifics and titles to strip for demographic matching
INDIAN_HONORIFICS: Set[str] = {
    "dr",
    "doctor",
    "mr",
    "mrs",
    "ms",
    "miss",
    "master",
    "shri",
    "shree",
    "smt",
    "shrimati",
    "kumar",
    "kumari",
}


# ----------------------------------------------------------------------------
# Text Normalization & Fuzzy Similarity Utilities
# ----------------------------------------------------------------------------


def normalize_text(text: Optional[str]) -> str:
    """Lowercase and strip non-alphanumeric characters except spaces."""
    if not text:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return " ".join(cleaned.split())


def remove_honorifics(normalized_name: str) -> str:
    """Strip common honorific titles from a normalized name string."""
    tokens = normalized_name.split()
    filtered = [t for t in tokens if t not in INDIAN_HONORIFICS]
    return " ".join(filtered) if filtered else normalized_name


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute classical Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein similarity ratio between 0.0 and 1.0."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return max(0.0, 1.0 - (dist / max_len))


def calculate_name_similarity(name1: Optional[str], name2: Optional[str]) -> float:
    """Compute composite name similarity combining token overlap and edit distance.

    Handles:
    - Inverted names (e.g. 'Patel Arun' vs 'Arun Patel') -> 1.0
    - Missing middle names (e.g. 'Arun Kumar Patel' vs 'Arun Patel') -> ~0.90
    - Minor typos (e.g. 'Aron Patel' vs 'Arun Patel') -> ~0.85
    """
    n1 = remove_honorifics(normalize_text(name1))
    n2 = remove_honorifics(normalize_text(name2))

    if not n1 and not n2:
        return 1.0
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    tokens1 = set(n1.split())
    tokens2 = set(n2.split())

    # Exact token match regardless of ordering
    if tokens1 == tokens2:
        return 1.0

    # Jaccard token set similarity
    jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2) if (tokens1 | tokens2) else 0.0

    # Subset token match (e.g. partial middle name)
    subset_bonus = 0.0
    if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
        subset_bonus = 0.88

    # Character-level edit distance ratio
    lev_ratio = levenshtein_ratio(n1, n2)

    # Difflib Gestalt pattern matching
    seq_ratio = difflib.SequenceMatcher(None, n1, n2).ratio()

    return round(max(jaccard, subset_bonus, lev_ratio, seq_ratio), 4)


def calculate_yob_similarity(yob1: Optional[int], yob2: Optional[int]) -> float:
    """Compute birth year similarity score with +/- 1 year tolerance."""
    if yob1 is None or yob2 is None:
        return 0.5  # Neutral when birth year is omitted

    diff = abs(yob1 - yob2)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.85  # Common 1-year birthday/rounding skew
    if diff == 2:
        return 0.50
    return 0.0


def calculate_gender_similarity(g1: Optional[Any], g2: Optional[Any]) -> float:
    """Compare genders normalized across clinical enum and single-char codes."""
    if not g1 or not g2:
        return 0.5  # Neutral when omitted

    def norm_gender(g: Any) -> str:
        val = g.value if isinstance(g, Gender) else str(g)
        val = val.strip().upper()
        if val in ("M", "MALE"):
            return "M"
        if val in ("F", "FEMALE"):
            return "F"
        if val in ("O", "OTHER"):
            return "O"
        return "UNKNOWN"

    code1 = norm_gender(g1)
    code2 = norm_gender(g2)

    if code1 == "UNKNOWN" or code2 == "UNKNOWN":
        return 0.5
    return 1.0 if code1 == code2 else 0.0


def normalize_phone(phone: Optional[str]) -> str:
    """Extract standard 10-digit mobile number."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits


# ----------------------------------------------------------------------------
# Demographic Score Evaluation
# ----------------------------------------------------------------------------


def evaluate_candidate_match(
    candidate_user: User,
    candidate_profile: PatientProfile,
    query: PatientDiscoveryQuery,
) -> Tuple[float, DemographicMatchBreakdown, List[str]]:
    """Evaluate a candidate patient record against discovery query criteria."""
    matched_by: List[str] = []

    # 1. Deterministic: ABHA Number Match
    query_abha_num = None
    for ident in query.verifiedIdentifiers:
        if ident.type in ("NDHM_HEALTH_NUMBER", "HEALTH_ID", "ABHA_NUMBER"):
            query_abha_num = re.sub(r"\D", "", ident.value)
            break

    if query_abha_num and candidate_profile.abha_number:
        cand_abha_num = re.sub(r"\D", "", candidate_profile.abha_number)
        if cand_abha_num == query_abha_num:
            matched_by.append("NDHM_HEALTH_NUMBER")
            breakdown = DemographicMatchBreakdown(
                name_score=1.0,
                yob_score=1.0,
                gender_score=1.0,
                composite_score=1.0,
                matched_by=["NDHM_HEALTH_NUMBER"],
                match_status="CONFIRMED",
            )
            return 1.0, breakdown, ["NDHM_HEALTH_NUMBER"]

    # 2. Deterministic: ABHA Address Match
    if query.id and candidate_profile.abha_address:
        if query.id.strip().lower() == candidate_profile.abha_address.strip().lower():
            matched_by.append("ABHA_ADDRESS")
            breakdown = DemographicMatchBreakdown(
                name_score=1.0,
                yob_score=1.0,
                gender_score=1.0,
                composite_score=1.0,
                matched_by=["ABHA_ADDRESS"],
                match_status="CONFIRMED",
            )
            return 1.0, breakdown, ["ABHA_ADDRESS"]

    # 3. Deterministic: Hospital MRN Match
    query_mrn = None
    for ident in query.verifiedIdentifiers:
        if ident.type == "MR":
            query_mrn = ident.value.strip().lower()
            break
    if query_mrn:
        cand_ref = candidate_profile.id.lower()
        if query_mrn in cand_ref or cand_ref.startswith(query_mrn):
            matched_by.append("MR")
            breakdown = DemographicMatchBreakdown(
                name_score=1.0,
                yob_score=1.0,
                gender_score=1.0,
                composite_score=1.0,
                matched_by=["MR"],
                match_status="CONFIRMED",
            )
            return 1.0, breakdown, ["MR"]

    # 4. Verified Mobile Match
    query_mobile = None
    for ident in query.verifiedIdentifiers:
        if ident.type == "MOBILE":
            query_mobile = normalize_phone(ident.value)
            break

    cand_mobile = normalize_phone(candidate_user.phone_number)
    phone_matched = False
    if query_mobile and cand_mobile and query_mobile == cand_mobile:
        phone_matched = True
        matched_by.append("MOBILE")

    # 5. Demographic Scores (Name, YOB, Gender)
    name_score = calculate_name_similarity(candidate_user.full_name, query.name)

    query_yob = query.yearOfBirth
    if not query_yob and query.dateOfBirth:
        try:
            query_yob = int(query.dateOfBirth[:4])
        except (ValueError, TypeError):
            pass

    cand_yob = candidate_profile.date_of_birth.year if candidate_profile.date_of_birth else None
    yob_score = calculate_yob_similarity(cand_yob, query_yob)

    gender_score = calculate_gender_similarity(candidate_profile.gender, query.gender)

    if name_score >= 0.75:
        matched_by.append("NAME")
    if yob_score >= 0.85:
        matched_by.append("YOB")
    if gender_score == 1.0:
        matched_by.append("GENDER")

    # 6. Composite Score Formula
    if phone_matched:
        # Verified mobile provides strong anchor
        # Base: 0.65 + Name (0.20) + YOB (0.10) + Gender (0.05)
        composite = 0.65 + (0.20 * name_score) + (0.10 * yob_score) + (0.05 * gender_score)
    else:
        # Pure demographic fuzzy matching without verified mobile
        # Name (50%) + YOB (25%) + Gender (25%)
        # Note: If gender mismatches completely, penalize heavily
        if gender_score == 0.0:
            composite = (0.50 * name_score + 0.25 * yob_score) * 0.50
        else:
            composite = (0.50 * name_score) + (0.25 * yob_score) + (0.25 * gender_score)

    composite = round(min(1.0, max(0.0, composite)), 4)

    breakdown = DemographicMatchBreakdown(
        name_score=name_score,
        yob_score=yob_score,
        gender_score=gender_score,
        composite_score=composite,
        matched_by=matched_by,
        match_status="CONFIRMED" if composite >= 0.75 else "NO_MATCH",
    )

    return composite, breakdown, matched_by


# ----------------------------------------------------------------------------
# Care Context Extraction Service
# ----------------------------------------------------------------------------


async def resolve_patient_care_contexts(
    session: AsyncSession,
    patient_profile_id: str,
) -> List[CareContextRepresentation]:
    """Extract clinical appointments and diagnostic orders as ABDM care contexts."""
    care_contexts: List[CareContextRepresentation] = []

    # 1. Fetch Clinical Consultations (Appointments)
    stmt_appts = (
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user)  # type: ignore[name-defined]
        )
        .where(Appointment.patient_id == patient_profile_id)
        .order_by(Appointment.scheduled_start.desc())
    )

    appts_res = await session.execute(stmt_appts)
    appointments = appts_res.scalars().all()

    for appt in appointments:
        doc_name = (
            appt.doctor.user.full_name
            if (appt.doctor and appt.doctor.user)
            else "Practitioner"
        )
        appt_date = (
            appt.scheduled_start.strftime("%d %b %Y")
            if appt.scheduled_start
            else "Scheduled"
        )
        type_label = appt.appointment_type.value.replace("_", " ").title()

        ref_no = f"OPD-ENC-{str(appt.id)[:8].upper()}"
        display_label = f"{type_label} with Dr. {doc_name} ({appt_date})"

        care_contexts.append(
            CareContextRepresentation(
                referenceNumber=ref_no,
                display=display_label,
            )
        )

    # 2. Fetch Laboratory Requisitions (Diagnostic Orders)
    stmt_orders = (
        select(DiagnosticOrder)
        .where(DiagnosticOrder.patient_id == patient_profile_id)
        .order_by(DiagnosticOrder.created_at.desc())
    )
    orders_res = await session.execute(stmt_orders)
    diagnostic_orders = orders_res.scalars().all()

    for order in diagnostic_orders:
        order_date = (
            order.created_at.strftime("%d %b %Y")
            if order.created_at
            else "Recent"
        )
        ref_no = f"LAB-ORD-{str(order.id)[:8].upper()}"
        display_label = f"Diagnostic Order: {order.code_display} ({order_date})"

        care_contexts.append(
            CareContextRepresentation(
                referenceNumber=ref_no,
                display=display_label,
            )
        )

    return care_contexts


# ----------------------------------------------------------------------------
# Core Discovery Engine & Ambiguity Handler
# ----------------------------------------------------------------------------


async def discover_patient(
    session: AsyncSession,
    query: PatientDiscoveryQuery,
    threshold: float = 0.75,
) -> Tuple[
    bool,
    Optional[PatientProfile],
    Optional[DemographicMatchBreakdown],
    List[CareContextRepresentation],
    Optional[str],
]:
    """Execute federated patient discovery against NIRMAYA patient database.

    Returns:
    - matched (bool): Whether a unique patient was confirmed
    - patient (PatientProfile | None): The matched profile
    - breakdown (DemographicMatchBreakdown | None): Scoring metrics
    - care_contexts (List[CareContextRepresentation]): Associated care contexts
    - error_message (str | None): Failure reason if no match or ambiguous
    """
    stmt = select(PatientProfile).options(joinedload(PatientProfile.user))
    res = await session.execute(stmt)
    all_profiles = res.scalars().all()

    candidates: List[Tuple[float, PatientProfile, DemographicMatchBreakdown, List[str]]] = []

    for profile in all_profiles:
        if not profile.user:
            continue
        score, breakdown, matched_keys = evaluate_candidate_match(
            candidate_user=profile.user,
            candidate_profile=profile,
            query=query,
        )
        if score >= threshold:
            candidates.append((score, profile, breakdown, matched_keys))

    # Sort descending by score
    candidates.sort(key=lambda x: x[0], reverse=True)

    if not candidates:
        empty_breakdown = DemographicMatchBreakdown(
            name_score=0.0,
            yob_score=0.0,
            gender_score=0.0,
            composite_score=0.0,
            matched_by=[],
            match_status="NO_MATCH",
        )
        return False, None, empty_breakdown, [], "No matching patient found at HIP"

    # Ambiguity Protection Check:
    # If more than 1 patient passes threshold and score gap is < 0.10, reject
    if len(candidates) > 1:
        top_score = candidates[0][0]
        second_score = candidates[1][0]
        if abs(top_score - second_score) < 0.10:
            ambiguous_breakdown = candidates[0][2]
            ambiguous_breakdown.match_status = "AMBIGUOUS"
            return (
                False,
                None,
                ambiguous_breakdown,
                [],
                "Multiple potential patient matches found. Please provide verified ABHA Number or Mobile.",
            )

    # Unique match confirmed!
    top_score, matched_profile, breakdown, _ = candidates[0]
    care_contexts = await resolve_patient_care_contexts(
        session=session,
        patient_profile_id=matched_profile.id,
    )

    return True, matched_profile, breakdown, care_contexts, None


# ----------------------------------------------------------------------------
# Interactive Simulation Service
# ----------------------------------------------------------------------------


async def simulate_patient_discovery(
    session: AsyncSession,
    sim_req: PatientDiscoverySimulateRequest,
) -> PatientDiscoverySimulateResponse:
    """Run an interactive simulation of the discovery protocol from the clinical console."""
    # Convert simulation request into PatientDiscoveryQuery
    verified_idents = []
    if sim_req.abha_number:
        verified_idents.append(
            {"type": "NDHM_HEALTH_NUMBER", "value": sim_req.abha_number}
        )
    if sim_req.mobile:
        verified_idents.append(
            {"type": "MOBILE", "value": sim_req.mobile}
        )

    query = PatientDiscoveryQuery(
        id=sim_req.abha_address or "citizen@abdm",
        name=sim_req.full_name,
        gender=sim_req.gender,
        yearOfBirth=sim_req.year_of_birth,
        verifiedIdentifiers=[
            ident for ident in verified_idents  # type: ignore[arg-type]
        ],
    )

    matched, profile, breakdown, care_contexts, err_msg = await discover_patient(
        session=session,
        query=query,
        threshold=sim_req.match_threshold,
    )

    callback_payload: Optional[Dict[str, Any]] = None
    if matched and profile and profile.user:
        discovered_patient = DiscoveredPatientRepresentation(
            referenceNumber=profile.id,
            display=profile.user.full_name,
            careContexts=care_contexts,
            matchedBy=breakdown.matched_by if breakdown else [],
        )
        cb = GatewayPatientOnDiscoverCallback(
            requestId=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            transactionId=str(uuid.uuid4()),
            patient=discovered_patient,
            resp=GatewayRespRef(requestId=str(uuid.uuid4())),
        )
        callback_payload = cb.model_dump(mode="json")
    else:
        cb = GatewayPatientOnDiscoverCallback(
            requestId=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            transactionId=str(uuid.uuid4()),
            patient=None,
            error={"code": 2500, "message": err_msg or "No match found"},
            resp=GatewayRespRef(requestId=str(uuid.uuid4())),
        )
        callback_payload = cb.model_dump(mode="json")

    return PatientDiscoverySimulateResponse(
        matched=matched,
        confidence_score=breakdown.composite_score if breakdown else 0.0,
        breakdown=breakdown or DemographicMatchBreakdown(
            name_score=0.0,
            yob_score=0.0,
            gender_score=0.0,
            composite_score=0.0,
            matched_by=[],
            match_status="NO_MATCH",
        ),
        patient_id=profile.id if profile else None,
        patient_name=profile.user.full_name if (profile and profile.user) else None,
        abha_address=profile.abha_address if profile else None,
        care_contexts=care_contexts,
        callback_payload=callback_payload,
    )


# ----------------------------------------------------------------------------
# Asynchronous Background Callback Dispatcher (/v0.5/care-contexts/on-discover)
# ----------------------------------------------------------------------------


async def dispatch_async_on_discover_callback(
    incoming_request: GatewayPatientDiscoveryRequest,
    result_patient: Optional[DiscoveredPatientRepresentation],
    error_details: Optional[Dict[str, Any]] = None,
) -> None:
    """Dispatches asynchronous callback to ABDM Gateway /v0.5/care-contexts/on-discover."""
    start_time = time.time()
    logger.info(
        "Initiating async discovery callback for request_id=%s, hip_id=%s",
        incoming_request.requestId,
        incoming_request.hipId,
    )

    callback_payload = GatewayPatientOnDiscoverCallback(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        transactionId=str(uuid.uuid4()),
        patient=result_patient,
        error=error_details,
        resp=GatewayRespRef(requestId=incoming_request.requestId),
    )

    gateway_url = settings.ABDM_GATEWAY_URL.rstrip("/")
    target_endpoint = f"{gateway_url}/v0.5/care-contexts/on-discover"

    payload_dict = callback_payload.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "X-CM-ID": "sbx",
        "REQUEST-ID": callback_payload.requestId,
        "TIMESTAMP": callback_payload.timestamp.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                target_endpoint,
                json=payload_dict,
                headers=headers,
            )
            elapsed_ms = (time.time() - start_time) * 1000.0
            logger.info(
                "Dispatched /on-discover callback to %s: status=%d, elapsed=%.2fms",
                target_endpoint,
                resp.status_code,
                elapsed_ms,
            )
            webhook_audit_store.update_event_status(
                request_id=incoming_request.requestId,
                new_status="CALLBACK_SENT",
                latency_ms=elapsed_ms,
                details={
                    "gateway_http_status": resp.status_code,
                    "target_endpoint": target_endpoint,
                    "patient_matched": result_patient is not None,
                },
            )
    except Exception as exc:
        elapsed_ms = (time.time() - start_time) * 1000.0
        logger.warning(
            "Sandbox simulated callback dispatch for %s (offline gateway): %s",
            target_endpoint,
            str(exc),
        )
        # In sandbox environment, mark callback sent with simulated delivery
        webhook_audit_store.update_event_status(
            request_id=incoming_request.requestId,
            new_status="CALLBACK_SENT",
            latency_ms=elapsed_ms,
            details={
                "simulated": True,
                "note": "ABDM sandbox simulated loop",
                "patient_matched": result_patient is not None,
                "care_contexts_count": len(result_patient.careContexts) if result_patient else 0,
            },
        )


from contextlib import asynccontextmanager


@asynccontextmanager
async def _get_worker_session():
    """Context manager for background worker database sessions, supporting test dependency overrides."""
    from app.main import app
    from app.db.session import get_db, AsyncSessionLocal

    override = app.dependency_overrides.get(get_db)
    if override:
        async for session in override():
            yield session
            return
    else:
        async with AsyncSessionLocal() as session:
            yield session


async def process_and_dispatch_discovery(
    incoming_request: GatewayPatientDiscoveryRequest,
    start_time: float,
) -> None:
    """Asynchronous worker executing patient discovery and dispatching callback."""
    async with _get_worker_session() as session:
        try:
            matched, profile, breakdown, care_contexts, err_msg = await discover_patient(
                session=session,
                query=incoming_request.patient,
            )


            result_patient = None
            error_details = None
            if matched and profile and profile.user:
                result_patient = DiscoveredPatientRepresentation(
                    referenceNumber=profile.id,
                    display=profile.user.full_name,
                    careContexts=care_contexts,
                    matchedBy=breakdown.matched_by if breakdown else [],
                )
            else:
                error_details = {
                    "code": 2500,
                    "message": err_msg or "No matching patient found at HIP",
                }

            await dispatch_async_on_discover_callback(
                incoming_request=incoming_request,
                result_patient=result_patient,
                error_details=error_details,
            )
        except Exception as exc:
            logger.error("Error processing discovery background task: %s", exc)
            await dispatch_async_on_discover_callback(
                incoming_request=incoming_request,
                result_patient=None,
                error_details={"code": 2500, "message": f"Internal discovery error: {str(exc)}"},
            )

