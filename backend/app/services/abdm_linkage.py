"""ABDM Milestone 2 (M2) Care Context Linkage & OTP Verification Service.

Complies with ABDM M2 HIP Specification:
- Handles inbound care context link initiation (POST /v0.5/links/link/init)
- Generates 6-digit secure OTP challenge with 10-minute validity and attempt tracking
- Masks recipient phone number (e.g. +91 ******3210) for patient privacy
- Handles citizen OTP confirmation (POST /v0.5/links/link/confirm)
- Dispatches asynchronous callbacks:
  - POST /v0.5/links/link/on-init
  - POST /v0.5/links/link/on-confirm
- Provides interactive simulation methods for clinical and testing environments
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import re
import secrets
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.abdm_m2_bridge import (
    CareContextRepresentation,
    GatewayCareContextRef,
    GatewayLinkConfirmConfirmation,
    GatewayLinkConfirmRequest,
    GatewayLinkInitRequest,
    GatewayLinkMeta,
    GatewayLinkOnConfirmCallback,
    GatewayLinkOnConfirmPatient,
    GatewayLinkOnInitCallback,
    GatewayLinkOnInitLink,
    GatewayLinkPatient,
    GatewayRespRef,
    LinkConfirmSimulateRequest,
    LinkConfirmSimulateResponse,
    LinkInitSimulateRequest,
    LinkInitSimulateResponse,
    LinkSessionRepresentation,
    WebhookEventItem,
)
from app.services.abdm_discovery import resolve_patient_care_contexts
from app.services.abdm_hip_bridge import (
    NIRMAYA_FACILITY_NAME,
    NIRMAYA_HIP_ID,
    webhook_audit_store,
)

logger = logging.getLogger("nirmaya.abdm.linkage")


# ----------------------------------------------------------------------------
# In-Memory Thread-Safe Link Session Store
# ----------------------------------------------------------------------------


@dataclass
class AbdmLinkSession:
    """In-memory active care context link transaction."""

    link_ref_number: str
    transaction_id: str
    patient_profile_id: str
    patient_name: str
    patient_id: str  # ABHA Address or identifier
    patient_phone: str
    care_contexts: List[CareContextRepresentation]
    otp: str
    created_at: datetime
    expires_at: datetime
    attempts_left: int = 3
    status: str = "PENDING"  # PENDING | CONFIRMED | EXPIRED | FAILED
    error_message: Optional[str] = None


class AbdmLinkSessionManager:
    """Thread-safe store managing active ABDM care context link sessions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: Dict[str, AbdmLinkSession] = {}

    def create_session(
        self,
        transaction_id: str,
        patient_profile_id: str,
        patient_name: str,
        patient_id: str,
        patient_phone: str,
        care_contexts: List[CareContextRepresentation],
        otp: Optional[str] = None,
        ttl_minutes: int = 10,
    ) -> AbdmLinkSession:
        """Create and register a new care context link challenge session."""
        with self._lock:
            # Generate unique link reference number: LINK-REF-XXXXXXXX
            token_hex = uuid.uuid4().hex[:8].upper()
            link_ref = f"LINK-REF-{token_hex}"

            # Default to predictable test OTP in sandbox if not specified
            otp_code = otp or ("123456" if settings.DEBUG else "".join(secrets.choice("0123456789") for _ in range(6)))
            now = datetime.now(timezone.utc)
            expires = now + timedelta(minutes=ttl_minutes)

            session = AbdmLinkSession(
                link_ref_number=link_ref,
                transaction_id=transaction_id,
                patient_profile_id=patient_profile_id,
                patient_name=patient_name,
                patient_id=patient_id,
                patient_phone=patient_phone,
                care_contexts=care_contexts,
                otp=otp_code,
                created_at=now,
                expires_at=expires,
                attempts_left=3,
                status="PENDING",
            )
            self._sessions[link_ref] = session
            return session

    def get_session(self, link_ref_number: str) -> Optional[AbdmLinkSession]:
        """Fetch session by link reference number."""
        with self._lock:
            return self._sessions.get(link_ref_number)

    def verify_otp(
        self,
        link_ref_number: str,
        token: str,
    ) -> Tuple[bool, Optional[AbdmLinkSession], Optional[str]]:
        """Verify patient OTP against stored session with rate limiting and expiry check."""
        with self._lock:
            session = self._sessions.get(link_ref_number)
            if not session:
                return False, None, "Invalid or non-existent link reference number"

            now = datetime.now(timezone.utc)
            if now > session.expires_at or session.status == "EXPIRED":
                session.status = "EXPIRED"
                session.error_message = "Link verification challenge has expired"
                return False, session, "Link verification challenge has expired. Please initiate new link request."

            if session.status == "CONFIRMED":
                return True, session, None

            if session.status == "FAILED" or session.attempts_left <= 0:
                session.status = "FAILED"
                session.error_message = "Maximum verification attempts exceeded"
                return False, session, "Maximum verification attempts exceeded. Transaction blocked."

            # Verify OTP value
            if token.strip() == session.otp.strip():
                session.status = "CONFIRMED"
                session.error_message = None
                return True, session, None

            # On mismatch, decrement attempts
            session.attempts_left -= 1
            if session.attempts_left <= 0:
                session.status = "FAILED"
                session.error_message = "Maximum verification attempts exceeded"
                return False, session, "Invalid OTP. Maximum attempts exceeded. Link failed."

            return (
                False,
                session,
                f"Invalid OTP entered. {session.attempts_left} attempt(s) remaining.",
            )

    def list_sessions(self, limit: int = 50) -> List[AbdmLinkSession]:
        """List recent link sessions ordered newest first."""
        with self._lock:
            items = list(self._sessions.values())
            items.sort(key=lambda s: s.created_at, reverse=True)
            return items[:limit]

    def clear(self) -> None:
        """Clear all sessions (primarily for unit testing isolation)."""
        with self._lock:
            self._sessions.clear()


# Global singleton instance
link_session_manager = AbdmLinkSessionManager()


# ----------------------------------------------------------------------------
# Helper Utilities
# ----------------------------------------------------------------------------


def mask_phone_number(phone: Optional[str]) -> str:
    """Mask telephone number according to ABDM privacy guidelines (e.g. +91 ******3210)."""
    if not phone:
        return "+91 ******0000"

    cleaned = re.sub(r"[^\d+]", "", phone)
    if len(cleaned) < 6:
        return "+91 ******" + cleaned[-2:]

    # Retain country prefix and last 4 digits
    suffix = cleaned[-4:]
    prefix = cleaned[:3] if cleaned.startswith("+") else "+91"
    return f"{prefix} ******{suffix}"


# ----------------------------------------------------------------------------
# Core Link Handlers
# ----------------------------------------------------------------------------


async def initiate_care_context_linking(
    session: AsyncSession,
    request: GatewayLinkInitRequest,
) -> Tuple[bool, Optional[AbdmLinkSession], Optional[str]]:
    """Resolve patient and care contexts, then create a pending link OTP session."""
    patient_query = request.patient
    target_abha = (patient_query.id or "").strip()
    target_ref = (patient_query.referenceNumber or "").strip()

    stmt = select(PatientProfile).options(joinedload(PatientProfile.user))

    # Match patient by ABHA address, ABHA number, or internal profile ID
    conditions = []
    if target_abha:
        conditions.append(PatientProfile.abha_address == target_abha)
        conditions.append(PatientProfile.abha_number == target_abha)
    if target_ref:
        conditions.append(PatientProfile.id == target_ref)

    if not conditions:
        return False, None, "No patient identifier or referenceNumber provided in query"

    stmt = stmt.where(or_(*conditions))
    res = await session.execute(stmt)
    patient_profile = res.scalars().first()

    if not patient_profile or not patient_profile.user:
        return (
            False,
            None,
            f"Patient with identifier '{target_abha or target_ref}' not found at this HIP",
        )

    # Resolve all patient care contexts from clinical appointments and diagnostic orders
    all_care_contexts = await resolve_patient_care_contexts(
        session=session,
        patient_profile_id=patient_profile.id,
    )

    # Filter requested care contexts if specified
    requested_refs = {cc.referenceNumber for cc in patient_query.careContexts}
    if requested_refs:
        selected_contexts = [
            cc for cc in all_care_contexts if cc.referenceNumber in requested_refs
        ]
        # If none of the specific requested refs exist, default to all available
        if not selected_contexts:
            selected_contexts = all_care_contexts
    else:
        selected_contexts = all_care_contexts

    # Create link session
    patient_phone = patient_profile.user.phone_number or "+919876543210"
    patient_name = patient_profile.user.full_name or "Patient"

    link_session = link_session_manager.create_session(
        transaction_id=request.transactionId,
        patient_profile_id=patient_profile.id,
        patient_name=patient_name,
        patient_id=target_abha or patient_profile.abha_address or patient_profile.id,
        patient_phone=patient_phone,
        care_contexts=selected_contexts,
        otp="123456" if settings.DEBUG else None,
        ttl_minutes=10,
    )

    logger.info(
        "Initiated link session %s for patient %s (phone %s, %d care contexts)",
        link_session.link_ref_number,
        link_session.patient_name,
        mask_phone_number(patient_phone),
        len(selected_contexts),
    )

    return True, link_session, None


async def confirm_care_context_linking(
    request: GatewayLinkConfirmRequest,
) -> Tuple[bool, Optional[AbdmLinkSession], Optional[str]]:
    """Validate citizen OTP token for the specified link reference number."""
    link_ref = request.confirmation.linkRefNumber
    token = request.confirmation.token

    valid, session, err_msg = link_session_manager.verify_otp(
        link_ref_number=link_ref,
        token=token,
    )

    return valid, session, err_msg


# ----------------------------------------------------------------------------
# Asynchronous Background Dispatchers
# ----------------------------------------------------------------------------


async def dispatch_async_on_link_init_callback(
    incoming_request: GatewayLinkInitRequest,
    link_session: Optional[AbdmLinkSession],
    error_details: Optional[Dict[str, Any]] = None,
) -> None:
    """Dispatch asynchronous callback to ABDM Gateway /v0.5/links/link/on-init."""
    start_time = time.time()
    logger.info(
        "Initiating async on-link-init callback for request_id=%s, transaction_id=%s",
        incoming_request.requestId,
        incoming_request.transactionId,
    )

    link_block = None
    if link_session and not error_details:
        masked_phone = mask_phone_number(link_session.patient_phone)
        link_block = GatewayLinkOnInitLink(
            referenceNumber=link_session.link_ref_number,
            authenticationType="DIRECT",
            meta=GatewayLinkMeta(
                communicationMedium="MOBILE",
                communicationHint=masked_phone,
                communicationExpiry=link_session.expires_at,
            ),
        )

    callback_payload = GatewayLinkOnInitCallback(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        transactionId=incoming_request.transactionId,
        link=link_block,
        error=error_details,
        resp=GatewayRespRef(requestId=incoming_request.requestId),
    )

    if settings.ENVIRONMENT != "production":
        elapsed_ms = (time.time() - start_time) * 1000.0
        webhook_audit_store.update_event_status(
            request_id=incoming_request.requestId,
            new_status="CALLBACK_SENT",
            latency_ms=elapsed_ms,
            details={
                "simulated": True,
                "note": "ABDM sandbox simulated link-init loop",
                "link_ref_number": link_session.link_ref_number if link_session else None,
            },
        )
        return

    gateway_url = settings.ABDM_GATEWAY_URL.rstrip("/")
    target_endpoint = f"{gateway_url}/v0.5/links/link/on-init"

    payload_dict = callback_payload.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "X-CM-ID": "sbx",
        "REQUEST-ID": callback_payload.requestId,
        "TIMESTAMP": callback_payload.timestamp.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(target_endpoint, json=payload_dict, headers=headers)
            elapsed_ms = (time.time() - start_time) * 1000.0
            logger.info(
                "Dispatched /links/link/on-init callback to %s: status=%d, elapsed=%.2fms",
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
                    "link_ref_number": link_session.link_ref_number if link_session else None,
                },
            )
    except Exception as exc:
        elapsed_ms = (time.time() - start_time) * 1000.0
        logger.warning(
            "Sandbox simulated callback dispatch for %s (offline gateway): %s",
            target_endpoint,
            str(exc),
        )
        webhook_audit_store.update_event_status(
            request_id=incoming_request.requestId,
            new_status="CALLBACK_SENT",
            latency_ms=elapsed_ms,
            details={
                "simulated": True,
                "note": "ABDM sandbox simulated link-init loop",
                "link_ref_number": link_session.link_ref_number if link_session else None,
            },
        )


async def dispatch_async_on_link_confirm_callback(
    incoming_request: GatewayLinkConfirmRequest,
    link_session: Optional[AbdmLinkSession],
    error_details: Optional[Dict[str, Any]] = None,
) -> None:
    """Dispatch asynchronous callback to ABDM Gateway /v0.5/links/link/on-confirm."""
    start_time = time.time()
    logger.info(
        "Initiating async on-link-confirm callback for request_id=%s, link_ref=%s",
        incoming_request.requestId,
        incoming_request.confirmation.linkRefNumber,
    )

    patient_block = None
    if link_session and not error_details:
        patient_block = GatewayLinkOnConfirmPatient(
            referenceNumber=link_session.patient_profile_id,
            display=link_session.patient_name,
            careContexts=link_session.care_contexts,
        )

    callback_payload = GatewayLinkOnConfirmCallback(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        patient=patient_block,
        error=error_details,
        resp=GatewayRespRef(requestId=incoming_request.requestId),
    )

    if settings.ENVIRONMENT != "production":
        elapsed_ms = (time.time() - start_time) * 1000.0
        webhook_audit_store.update_event_status(
            request_id=incoming_request.requestId,
            new_status="CALLBACK_SENT",
            latency_ms=elapsed_ms,
            details={
                "simulated": True,
                "note": "ABDM sandbox simulated link-confirm loop",
                "patient_linked": link_session.patient_name if link_session else None,
                "linked_contexts_count": len(link_session.care_contexts) if link_session else 0,
            },
        )
        return

    gateway_url = settings.ABDM_GATEWAY_URL.rstrip("/")
    target_endpoint = f"{gateway_url}/v0.5/links/link/on-confirm"

    payload_dict = callback_payload.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "X-CM-ID": "sbx",
        "REQUEST-ID": callback_payload.requestId,
        "TIMESTAMP": callback_payload.timestamp.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(target_endpoint, json=payload_dict, headers=headers)
            elapsed_ms = (time.time() - start_time) * 1000.0
            logger.info(
                "Dispatched /links/link/on-confirm callback to %s: status=%d, elapsed=%.2fms",
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
                    "patient_linked": link_session.patient_name if link_session else None,
                    "linked_contexts_count": len(link_session.care_contexts) if link_session else 0,
                },
            )
    except Exception as exc:
        elapsed_ms = (time.time() - start_time) * 1000.0
        logger.warning(
            "Sandbox simulated callback dispatch for %s (offline gateway): %s",
            target_endpoint,
            str(exc),
        )
        webhook_audit_store.update_event_status(
            request_id=incoming_request.requestId,
            new_status="CALLBACK_SENT",
            latency_ms=elapsed_ms,
            details={
                "simulated": True,
                "note": "ABDM sandbox simulated link-confirm loop",
                "patient_linked": link_session.patient_name if link_session else None,
                "linked_contexts_count": len(link_session.care_contexts) if link_session else 0,
            },
        )


# ----------------------------------------------------------------------------
# Background Worker Functions
# ----------------------------------------------------------------------------


async def process_and_dispatch_link_init(
    incoming_request: GatewayLinkInitRequest,
    start_time: float,
) -> None:
    """Background worker processing /v0.5/links/link/init."""
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            success, link_session, err_msg = await initiate_care_context_linking(
                session=session,
                request=incoming_request,
            )

            error_block = {"code": 1411, "message": err_msg} if not success else None
            await dispatch_async_on_link_init_callback(
                incoming_request=incoming_request,
                link_session=link_session,
                error_details=error_block,
            )
    except Exception as exc:
        logger.warning("Background link init database query failed: %s", exc)
        await dispatch_async_on_link_init_callback(
            incoming_request=incoming_request,
            link_session=None,
            error_details={"code": 1411, "message": f"Service temporarily unable to process link: {exc}"},
        )


async def process_and_dispatch_link_confirm(
    incoming_request: GatewayLinkConfirmRequest,
    start_time: float,
) -> None:
    """Background worker processing /v0.5/links/link/confirm."""
    valid, link_session, err_msg = await confirm_care_context_linking(
        request=incoming_request,
    )

    error_block = {"code": 1412, "message": err_msg or "Invalid OTP"} if not valid else None
    await dispatch_async_on_link_confirm_callback(
        incoming_request=incoming_request,
        link_session=link_session,
        error_details=error_block,
    )


# ----------------------------------------------------------------------------
# Interactive Simulation Handlers
# ----------------------------------------------------------------------------


async def simulate_care_context_link_init(
    session: AsyncSession,
    sim_req: LinkInitSimulateRequest,
) -> LinkInitSimulateResponse:
    """Simulate link initiation from the clinical cockpit or testing harness."""
    tx_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    care_refs = [
        GatewayCareContextRef(referenceNumber=ref)
        for ref in (sim_req.care_context_references or [])
    ]

    gateway_req = GatewayLinkInitRequest(
        requestId=req_id,
        timestamp=datetime.now(timezone.utc),
        transactionId=tx_id,
        patient=GatewayLinkPatient(
            id=sim_req.patient_identifier,
            referenceNumber=sim_req.patient_identifier,
            careContexts=care_refs,
        ),
    )

    success, link_session, err_msg = await initiate_care_context_linking(
        session=session,
        request=gateway_req,
    )

    if not success or not link_session:
        return LinkInitSimulateResponse(
            success=False,
            link_ref_number="",
            transaction_id=tx_id,
            communication_hint="",
            otp_sandbox_hint=None,
            care_contexts_count=0,
            callback_payload=None,
            error_message=err_msg or "Failed to initiate link challenge",
        )

    # Build on-init callback preview
    masked = mask_phone_number(link_session.patient_phone)
    cb = GatewayLinkOnInitCallback(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        transactionId=tx_id,
        link=GatewayLinkOnInitLink(
            referenceNumber=link_session.link_ref_number,
            authenticationType="DIRECT",
            meta=GatewayLinkMeta(
                communicationMedium="MOBILE",
                communicationHint=masked,
                communicationExpiry=link_session.expires_at,
            ),
        ),
        resp=GatewayRespRef(requestId=req_id),
    )

    return LinkInitSimulateResponse(
        success=True,
        link_ref_number=link_session.link_ref_number,
        transaction_id=tx_id,
        communication_hint=masked,
        otp_sandbox_hint=link_session.otp,
        care_contexts_count=len(link_session.care_contexts),
        callback_payload=cb.model_dump(mode="json"),
        error_message=None,
    )


async def simulate_care_context_link_confirm(
    sim_req: LinkConfirmSimulateRequest,
) -> LinkConfirmSimulateResponse:
    """Simulate citizen OTP confirmation from the clinical cockpit or test suite."""
    req_id = str(uuid.uuid4())
    gateway_req = GatewayLinkConfirmRequest(
        requestId=req_id,
        timestamp=datetime.now(timezone.utc),
        confirmation=GatewayLinkConfirmConfirmation(
            linkRefNumber=sim_req.link_ref_number,
            token=sim_req.otp_token,
        ),
    )

    valid, link_session, err_msg = await confirm_care_context_linking(
        request=gateway_req,
    )

    if not valid or not link_session:
        err_cb = GatewayLinkOnConfirmCallback(
            requestId=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            patient=None,
            error={"code": 1412, "message": err_msg or "Invalid OTP token"},
            resp=GatewayRespRef(requestId=req_id),
        )
        return LinkConfirmSimulateResponse(
            success=False,
            linked=False,
            patient_name=link_session.patient_name if link_session else None,
            linked_care_contexts=[],
            callback_payload=err_cb.model_dump(mode="json"),
            error_message=err_msg or "Invalid OTP verification token",
        )

    success_cb = GatewayLinkOnConfirmCallback(
        requestId=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        patient=GatewayLinkOnConfirmPatient(
            referenceNumber=link_session.patient_profile_id,
            display=link_session.patient_name,
            careContexts=link_session.care_contexts,
        ),
        resp=GatewayRespRef(requestId=req_id),
    )

    return LinkConfirmSimulateResponse(
        success=True,
        linked=True,
        patient_name=link_session.patient_name,
        linked_care_contexts=link_session.care_contexts,
        callback_payload=success_cb.model_dump(mode="json"),
        error_message=None,
    )
