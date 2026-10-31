"""Emergency Contact SMS Notification & Carrier Dispatcher for NIRMAYA.

Simulates carrier-grade SMS gateway notification to designated emergency next-of-kin
whenever a Break-The-Glass (BTG) emergency record override is executed.
Automatically seals every dispatch event into the immutable cryptographic audit ledger.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import List, Optional
import uuid

from app.schemas.audit_hash_chain import (
    AuditAppendRequest,
    AuditEventType,
    EmergencyDispatchMessage,
    EmergencyDispatchTestRequest,
)
from app.services.audit_hash_chain import audit_ledger_service

logger = logging.getLogger("nirmaya.emergency_dispatch")


def format_btg_sms_message(
    patient_name: str,
    patient_abha: str,
    hospital_name: str,
    doctor_name: str,
    department_phone: str,
) -> str:
    """Standardized emergency SMS notification compliant with hospital regulatory guidelines."""
    return (
        f"EMERGENCY NOTIFICATION: Break-The-Glass electronic health record override "
        f"was executed for patient {patient_name} (ABHA: {patient_abha}) at {hospital_name} "
        f"by attending physician {doctor_name}. If you have inquiries or wish to verify this "
        f"emergency clinical access, contact Emergency Triage immediately at {department_phone}."
    )


class EmergencyDispatchService:
    """Thread-safe carrier gateway simulation and emergency dispatch history manager."""

    def __init__(self) -> None:
        self._history: List[EmergencyDispatchMessage] = []
        self._lock = threading.Lock()
        self._seed_initial_history()

    def _seed_initial_history(self) -> None:
        """Seeds initial realistic dispatch logs for demonstration and audit verification."""
        seed_record = EmergencyDispatchMessage(
            dispatchId="disp-seed-982101",
            patientAbha="91-8472-1092-4821",
            patientName="Arun Patel",
            contactName="Pooja Patel",
            contactPhone="+91 98765 09991",
            relationship="Spouse",
            hospitalName="AIIMS New Delhi - Apex Trauma Center",
            doctorName="Dr. Ananya Sharma",
            departmentPhone="+91 11 2659 8700",
            messageText=(
                "EMERGENCY NOTIFICATION: Break-The-Glass electronic health record override "
                "was executed for patient Arun Patel (ABHA: 91-8472-1092-4821) at "
                "AIIMS New Delhi - Apex Trauma Center by attending physician Dr. Ananya Sharma. "
                "If you have inquiries or wish to verify this emergency clinical access, "
                "contact Emergency Triage immediately at +91 11 2659 8700."
            ),
            deliveryStatus="DELIVERED",
            gatewayReferenceId="gw-airtel-77A91B",
            dispatchTimestamp="2026-10-31T09:00:15.000000+00:00",
        )
        self._history.append(seed_record)

    def dispatch_emergency_sms(self, request: EmergencyDispatchTestRequest) -> EmergencyDispatchMessage:
        """Dispatches an emergency SMS alert via simulated carrier gateway and seals into audit ledger."""
        message_body = format_btg_sms_message(
            patient_name=request.patientName,
            patient_abha=request.patientAbha,
            hospital_name=request.hospitalName,
            doctor_name=request.doctorName,
            department_phone=request.departmentPhone,
        )

        gateway_ref = f"gw-carrier-{uuid.uuid4().hex[:8].upper()}"
        now_ts = datetime.now(timezone.utc).isoformat()

        record = EmergencyDispatchMessage(
            dispatchId=f"disp-{uuid.uuid4().hex[:12]}",
            patientAbha=request.patientAbha,
            patientName=request.patientName,
            contactName=request.contactName,
            contactPhone=request.contactPhone,
            relationship=request.relationship,
            hospitalName=request.hospitalName,
            doctorName=request.doctorName,
            departmentPhone=request.departmentPhone,
            messageText=message_body,
            deliveryStatus="DELIVERED",
            gatewayReferenceId=gateway_ref,
            dispatchTimestamp=now_ts,
        )

        with self._lock:
            self._history.append(record)

        # Cryptographically append event to the immutable hash-chain ledger
        try:
            audit_ledger_service.append_event(
                AuditAppendRequest(
                    eventType=AuditEventType.CRITICAL_ALERT_DISPATCH,
                    actorId=request.doctorName,
                    patientAbha=request.patientAbha,
                    facilityId=request.hospitalName,
                    payload={
                        "dispatchId": record.dispatchId,
                        "recipientPhone": record.contactPhone,
                        "recipientName": record.contactName,
                        "relationship": record.relationship,
                        "gatewayReferenceId": record.gatewayReferenceId,
                        "deliveryStatus": record.deliveryStatus,
                        "hospital": record.hospitalName,
                    },
                )
            )
        except Exception as exc:
            logger.error("Failed to append dispatch event to audit hash-chain: %s", exc)

        return record

    def dispatch_for_patient_vault(
        self,
        patient_abha: str,
        patient_name: str,
        contacts: List[dict],
        hospital_name: str,
        doctor_name: str,
        department_phone: str,
    ) -> List[EmergencyDispatchMessage]:
        """Dispatches notifications to all registered emergency contacts from a decrypted profile."""
        dispatched: List[EmergencyDispatchMessage] = []
        for contact in contacts:
            req = EmergencyDispatchTestRequest(
                patientAbha=patient_abha,
                patientName=patient_name,
                contactName=contact.get("name", "Emergency Next of Kin"),
                contactPhone=contact.get("phone", "+91 99999 99999"),
                relationship=contact.get("relationship", "Family"),
                hospitalName=hospital_name,
                doctorName=doctor_name,
                departmentPhone=department_phone,
            )
            msg = self.dispatch_emergency_sms(req)
            dispatched.append(msg)
        return dispatched

    def get_history(
        self,
        limit: int = 50,
        patient_abha: Optional[str] = None,
    ) -> List[EmergencyDispatchMessage]:
        """Returns chronological list of dispatched emergency messages (newest first)."""
        with self._lock:
            records = list(self._history)

        if patient_abha:
            records = [r for r in records if r.patientAbha == patient_abha]

        records.sort(key=lambda r: r.dispatchTimestamp, reverse=True)
        return records[:limit]


# Global singleton emergency dispatch service instance
emergency_dispatch_service = EmergencyDispatchService()
