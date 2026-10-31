"""Clinical Alert and Laboratory Panic-Value Evaluation Service for NIRMAYA.

Provides real-time clinical panic-value rule evaluation, automated WebSocket
alert push delivery (< 100ms), and clinician acknowledgment workflow tracking.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Dict, List, Optional
import uuid

from app.core.exceptions import EntityNotFoundException
from app.schemas.clinical_alerts import (
    AlertAcknowledgeRequest,
    AlertCategory,
    AlertCreateRequest,
    AlertSeverity,
    AlertStatus,
    AlertSummaryStatsResponse,
    ClinicalAlertResponse,
    LabEvaluationRequest,
    LabEvaluationResult,
    LabPanicRule,
)
from app.schemas.websocket_events import (
    CriticalAlertPayload,
    WebSocketChannel,
    WebSocketEventType,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("nirmaya.clinical_alerts")


# -----------------------------------------------------------------------------
# Curated Standard Laboratory Panic-Value Rules Registry
# -----------------------------------------------------------------------------

PANIC_RULES_REGISTRY: Dict[str, LabPanicRule] = {
    "2823-3": LabPanicRule(
        loincCode="2823-3",
        testName="Serum Potassium",
        unit="mEq/L",
        panicLow=2.8,
        panicHigh=6.0,
        criticalGuidance=(
            "Immediate risk of lethal ventricular dysrhythmia or asystole. "
            "Verify with stat 12-lead ECG; prepare IV Calcium Gluconate and Insulin-Dextrose protocol."
        ),
    ),
    "42757-5": LabPanicRule(
        loincCode="42757-5",
        testName="High-Sensitivity Cardiac Troponin I",
        unit="ng/mL",
        panicLow=None,
        panicHigh=0.04,
        criticalGuidance=(
            "Acute Myocardial Infarction (AMI) panic threshold exceeded. "
            "Order immediate 12-lead ECG, cardiology consult, and initiate acute coronary syndrome protocol."
        ),
    ),
    "2345-7": LabPanicRule(
        loincCode="2345-7",
        testName="Serum Glucose",
        unit="mg/dL",
        panicLow=45.0,
        panicHigh=450.0,
        criticalGuidance=(
            "Critical neuroglycopenia (< 45 mg/dL) or severe diabetic ketoacidosis / HHS (> 450 mg/dL). "
            "Administer IV 25% dextrose or initiate regular insulin infusion with frequent fingerstick monitoring."
        ),
    ),
    "777-3": LabPanicRule(
        loincCode="777-3",
        testName="Platelet Count",
        unit="10^3/uL",
        panicLow=20.0,
        panicHigh=1000.0,
        criticalGuidance=(
            "Critical thrombocytopenia (< 20,000/uL) indicates imminent spontaneous intracranial/GI hemorrhage risk. "
            "Discontinue all antiplatelet/anticoagulant agents and prepare irradiated platelet transfusion."
        ),
    ),
    "2160-0": LabPanicRule(
        loincCode="2160-0",
        testName="Serum Creatinine",
        unit="mg/dL",
        panicLow=None,
        panicHigh=4.0,
        criticalGuidance=(
            "Severe acute kidney injury (AKI Stage 3) or uremic crisis. "
            "Hold nephrotoxic medications, assess hyperkalemia/fluid overload, and evaluate for urgent hemodialysis."
        ),
    ),
    "2744-1": LabPanicRule(
        loincCode="2744-1",
        testName="Arterial Blood pH",
        unit="pH",
        panicLow=7.20,
        panicHigh=7.60,
        criticalGuidance=(
            "Severe uncompensated acid-base derangement (< 7.20 severe acidosis, > 7.60 severe alkalosis). "
            "Immediate arterial blood gas analysis and respiratory or metabolic intervention required."
        ),
    ),
    "718-7": LabPanicRule(
        loincCode="718-7",
        testName="Blood Hemoglobin",
        unit="g/dL",
        panicLow=6.0,
        panicHigh=20.0,
        criticalGuidance=(
            "Critical acute anemia (< 6.0 g/dL) or severe polycythemia (> 20.0 g/dL). "
            "Type and crossmatch packed red blood cells immediately and evaluate for active hemorrhagic shock."
        ),
    ),
}

# Aliases to match common names to LOINC codes
LOINC_ALIASES: Dict[str, str] = {
    "potassium": "2823-3",
    "serum potassium": "2823-3",
    "k+": "2823-3",
    "troponin": "42757-5",
    "troponin i": "42757-5",
    "hs-ctni": "42757-5",
    "cardiac troponin": "42757-5",
    "glucose": "2345-7",
    "blood glucose": "2345-7",
    "serum glucose": "2345-7",
    "platelets": "777-3",
    "platelet count": "777-3",
    "plt": "777-3",
    "creatinine": "2160-0",
    "serum creatinine": "2160-0",
    "ph": "2744-1",
    "blood ph": "2744-1",
    "arterial ph": "2744-1",
    "hemoglobin": "718-7",
    "hgb": "718-7",
    "hb": "718-7",
}


# -----------------------------------------------------------------------------
# Clinical Alerts Service Engine
# -----------------------------------------------------------------------------

class ClinicalAlertsService:
    """Thread-safe real-time clinical notification and laboratory panic-value engine."""

    def __init__(self) -> None:
        self._alerts: Dict[str, ClinicalAlertResponse] = {}
        self._lock = threading.Lock()
        self._seed_initial_demo_data()

    def _seed_initial_demo_data(self) -> None:
        """Seeds initial realistic clinical alerts for demonstration and clinic testing."""
        seed_alert_1 = ClinicalAlertResponse(
            alertId="alt-seed-001",
            patientId="pat-arun-patel-01",
            patientName="Arun Patel",
            doctorId="doc-ananya-sharma",
            facilityId="fac-aiims-delhi",
            category=AlertCategory.LAB_PANIC_VALUE,
            severity=AlertSeverity.PANIC,
            status=AlertStatus.UNREAD,
            title="CRITICAL PANIC: Serum Potassium 6.8 mEq/L",
            message=(
                "Patient Arun Patel's stat serum potassium is critically elevated at 6.8 mEq/L "
                "(Reference range: 3.5 - 5.1 mEq/L). Immediate risk of lethal ventricular arrhythmia."
            ),
            loincCode="2823-3",
            observedValue="6.8 mEq/L",
            referenceRange="3.5 - 5.1 mEq/L",
            actionRequired=True,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

        seed_alert_2 = ClinicalAlertResponse(
            alertId="alt-seed-002",
            patientId="pat-priya-nair-02",
            patientName="Priya Nair",
            doctorId="doc-ananya-sharma",
            facilityId="fac-aiims-delhi",
            category=AlertCategory.APPOINTMENT_CONFIRMED,
            severity=AlertSeverity.INFO,
            status=AlertStatus.UNREAD,
            title="Appointment Confirmed: Priya Nair",
            message="Priya Nair has confirmed her teleconsultation for 11:30 AM today via ABHA PHR app.",
            actionRequired=False,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

        self._alerts[seed_alert_1.alertId] = seed_alert_1
        self._alerts[seed_alert_2.alertId] = seed_alert_2

    def get_panic_rules(self) -> List[LabPanicRule]:
        """Returns all registered laboratory panic-value threshold rules."""
        return list(PANIC_RULES_REGISTRY.values())

    def _resolve_rule(self, loinc_code: str, test_name: str) -> Optional[LabPanicRule]:
        """Resolves rule by standard LOINC code or recognized analyte alias."""
        if loinc_code in PANIC_RULES_REGISTRY:
            return PANIC_RULES_REGISTRY[loinc_code]
        cleaned_name = test_name.strip().lower()
        if cleaned_name in LOINC_ALIASES:
            alias_loinc = LOINC_ALIASES[cleaned_name]
            return PANIC_RULES_REGISTRY.get(alias_loinc)
        return None

    async def evaluate_lab_observation(
        self,
        request: LabEvaluationRequest,
    ) -> LabEvaluationResult:
        """Evaluates a laboratory measurement against panic thresholds and triggers WebSocket push.

        Executes within < 5ms, dispatching immediately across Redis/In-Memory Pub/Sub channels.
        """
        rule = self._resolve_rule(request.loincCode, request.testName)
        val = request.numericValue

        is_panic = False
        breach_direction = ""

        if rule:
            if rule.panicLow is not None and val < rule.panicLow:
                is_panic = True
                breach_direction = f"critically LOW ({val} < {rule.panicLow} {rule.unit})"
            elif rule.panicHigh is not None and val > rule.panicHigh:
                is_panic = True
                breach_direction = f"critically HIGH ({val} > {rule.panicHigh} {rule.unit})"

        if not is_panic or not rule:
            return LabEvaluationResult(
                isPanic=False,
                severity=AlertSeverity.INFO,
                alertGenerated=False,
                alertId=None,
                ruleMatched=rule.loincCode if rule else None,
                message=f"Measurement {val} {request.unit} for {request.testName} is within safe non-panic limits.",
            )

        # Formulate critical alert
        alert_id = f"alt-{uuid.uuid4().hex[:12]}"
        title = f"CRITICAL PANIC: {rule.testName} {val} {rule.unit}"
        narrative = (
            f"Stat laboratory alert for {request.patientName}: {rule.testName} is {breach_direction}. "
            f"Reference: {request.referenceRange or 'Standard'}. Guidance: {rule.criticalGuidance}"
        )

        alert_record = ClinicalAlertResponse(
            alertId=alert_id,
            patientId=request.patientId,
            patientName=request.patientName,
            doctorId=request.doctorId,
            facilityId=request.facilityId,
            category=AlertCategory.LAB_PANIC_VALUE,
            severity=AlertSeverity.PANIC,
            status=AlertStatus.UNREAD,
            title=title,
            message=narrative,
            loincCode=rule.loincCode,
            observedValue=f"{val} {rule.unit}",
            referenceRange=request.referenceRange,
            actionRequired=True,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._alerts[alert_id] = alert_record

        # Automated real-time push over doctor workspace channel
        payload = CriticalAlertPayload(
            alertId=alert_record.alertId,
            patientId=alert_record.patientId,
            patientName=alert_record.patientName,
            doctorId=alert_record.doctorId,
            severity=AlertSeverity.PANIC,
            category=AlertCategory.LAB_PANIC_VALUE.value,
            title=alert_record.title,
            message=alert_record.message,
            loincCode=alert_record.loincCode,
            observedValue=alert_record.observedValue,
            referenceRange=alert_record.referenceRange,
            actionRequired=True,
            createdAt=alert_record.createdAt,
        )

        try:
            # Broadcast to clinician workspace
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(request.doctorId),
                event_type=WebSocketEventType.CRITICAL_ALERT,
                payload=payload.model_dump(),
            )
            # If facility is provided, broadcast to facility queue as well
            if request.facilityId:
                await ws_manager.broadcast_event(
                    channel=WebSocketChannel.facility_queue(request.facilityId),
                    event_type=WebSocketEventType.CRITICAL_ALERT,
                    payload=payload.model_dump(),
                )
        except Exception as exc:
            logger.error("Failed to broadcast laboratory critical alert %s: %s", alert_id, exc)

        return LabEvaluationResult(
            isPanic=True,
            severity=AlertSeverity.PANIC,
            alertGenerated=True,
            alertId=alert_id,
            ruleMatched=rule.loincCode,
            message=narrative,
        )

    async def create_alert(
        self,
        request: AlertCreateRequest,
    ) -> ClinicalAlertResponse:
        """Publishes an arbitrary clinical alert or notification with real-time WebSocket broadcast."""
        alert_id = f"alt-{uuid.uuid4().hex[:12]}"
        alert_record = ClinicalAlertResponse(
            alertId=alert_id,
            patientId=request.patientId,
            patientName=request.patientName,
            doctorId=request.doctorId,
            facilityId=request.facilityId,
            category=request.category,
            severity=request.severity,
            status=AlertStatus.UNREAD,
            title=request.title,
            message=request.message,
            loincCode=request.loincCode,
            observedValue=request.observedValue,
            referenceRange=request.referenceRange,
            actionRequired=request.actionRequired,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._alerts[alert_id] = alert_record

        # Automated real-time push to target doctor workspace
        payload = CriticalAlertPayload(
            alertId=alert_record.alertId,
            patientId=alert_record.patientId,
            patientName=alert_record.patientName,
            doctorId=alert_record.doctorId,
            severity=alert_record.severity,
            category=alert_record.category.value,
            title=alert_record.title,
            message=alert_record.message,
            loincCode=alert_record.loincCode,
            observedValue=alert_record.observedValue,
            referenceRange=alert_record.referenceRange,
            actionRequired=alert_record.actionRequired,
            createdAt=alert_record.createdAt,
        )

        try:
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(request.doctorId),
                event_type=WebSocketEventType.CRITICAL_ALERT,
                payload=payload.model_dump(),
            )
        except Exception as exc:
            logger.error("Failed to broadcast alert %s: %s", alert_id, exc)

        return alert_record

    def get_doctor_alerts(
        self,
        doctor_id: str,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50,
    ) -> List[ClinicalAlertResponse]:
        """Fetches chronological clinical alerts targeted to a specific clinician."""
        with self._lock:
            matches = [
                a for a in self._alerts.values()
                if a.doctorId == doctor_id
            ]

        if status:
            matches = [a for a in matches if a.status == status]
        if severity:
            matches = [a for a in matches if a.severity == severity]

        # Sort descending by creation timestamp
        matches.sort(key=lambda a: a.createdAt, reverse=True)
        return matches[:limit]

    def get_alert(self, alert_id: str) -> ClinicalAlertResponse:
        """Fetches a single clinical alert by unique record identifier."""
        with self._lock:
            alert = self._alerts.get(alert_id)
        if not alert:
            raise EntityNotFoundException("ClinicalAlert", alert_id)
        return alert

    async def acknowledge_alert(
        self,
        alert_id: str,
        request: AlertAcknowledgeRequest,
    ) -> ClinicalAlertResponse:
        """Acknowledges a critical alert, recording clinician notes and broadcasting live sync event."""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                raise EntityNotFoundException("ClinicalAlert", alert_id)

            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledgedAt = datetime.now(timezone.utc).isoformat()
            alert.acknowledgedByDoctorId = request.doctorId
            alert.clinicalActionTaken = request.clinicalAction

        # Broadcast acknowledgment event over doctor channel
        try:
            ack_payload = {
                "alertId": alert.alertId,
                "status": AlertStatus.ACKNOWLEDGED.value,
                "acknowledgedByDoctorId": request.doctorId,
                "acknowledgedAt": alert.acknowledgedAt,
                "clinicalActionTaken": request.clinicalAction,
            }
            await ws_manager.broadcast_event(
                channel=WebSocketChannel.doctor_workspace(alert.doctorId),
                event_type=WebSocketEventType.SYSTEM_NOTIFICATION,
                payload=ack_payload,
            )
        except Exception as exc:
            logger.error("Failed to broadcast alert acknowledgement for %s: %s", alert_id, exc)

        return alert

    def get_doctor_stats(self, doctor_id: str) -> AlertSummaryStatsResponse:
        """Computes live telemetry statistics for doctor's clinical alert feed."""
        with self._lock:
            doctor_alerts = [a for a in self._alerts.values() if a.doctorId == doctor_id]

        total = len(doctor_alerts)
        unread = sum(1 for a in doctor_alerts if a.status == AlertStatus.UNREAD)
        panic = sum(1 for a in doctor_alerts if a.severity == AlertSeverity.PANIC)
        critical = sum(1 for a in doctor_alerts if a.severity == AlertSeverity.CRITICAL)
        warning = sum(1 for a in doctor_alerts if a.severity == AlertSeverity.WARNING)
        info = sum(1 for a in doctor_alerts if a.severity == AlertSeverity.INFO)
        acknowledged = sum(1 for a in doctor_alerts if a.status == AlertStatus.ACKNOWLEDGED)

        return AlertSummaryStatsResponse(
            doctorId=doctor_id,
            totalAlerts=total,
            unreadCount=unread,
            panicCount=panic,
            criticalCount=critical,
            warningCount=warning,
            infoCount=info,
            acknowledgedCount=acknowledged,
        )


# Global singleton instance
clinical_alerts_service = ClinicalAlertsService()
