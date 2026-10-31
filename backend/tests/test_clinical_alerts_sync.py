"""Comprehensive Automated Test Suite for Clinical Alerts, Lab Panic-Values, and WebSocket Synchronization.

Tests:
1. Laboratory panic-value rule listing and boundary verification.
2. Rule-based panic evaluation for critically high values (e.g. Potassium > 6.0 mEq/L).
3. Rule-based panic evaluation for critically low values (e.g. Glucose < 45 mg/dL).
4. Safe non-panic laboratory evaluation (normal reference ranges).
5. Fallback analyte alias resolution (e.g. "Serum Potassium" -> LOINC 2823-3).
6. Manual clinical alert publication and classification.
7. Clinician alert feed retrieval with status and severity filters.
8. Single alert lookup and 404 handling.
9. Structured clinician alert acknowledgment and audit documentation.
10. Rapid unread count query and comprehensive summary statistics.
11. End-to-end WebSocket real-time broadcast delivery to doctor workspace channel.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.schemas.clinical_alerts import AlertCategory, AlertSeverity, AlertStatus
from app.schemas.websocket_events import WebSocketChannel, WebSocketEventType

client = TestClient(app)


def _generate_test_token(sub: str, role: str) -> str:
    """Helper generating signed JWT for authenticated WebSocket tests."""
    return create_access_token(
        data={"sub": sub, "role": role, "user_metadata": {"role": role}},
    )


class TestClinicalAlertsAndPanicEvaluation:
    """Suite verifying laboratory panic rules, observation evaluation, and CRUD endpoints."""

    def test_list_panic_rules(self):
        """Asserts retrieving registered laboratory panic-value threshold rules."""
        response = client.get("/api/v1/alerts/rules/panic")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 7
        loinc_codes = [r["loincCode"] for r in data]
        assert "2823-3" in loinc_codes  # Potassium
        assert "42757-5" in loinc_codes  # Troponin I
        assert "2345-7" in loinc_codes  # Glucose
        assert "777-3" in loinc_codes  # Platelets

    def test_evaluate_lab_observation_panic_high(self):
        """Asserts critically elevated potassium (6.8 mEq/L > 6.0) triggers PANIC alert."""
        payload = {
            "patientId": "pat-eval-01",
            "patientName": "Devendra Joshi",
            "doctorId": "doc-eval-01",
            "facilityId": "fac-aiims-delhi",
            "loincCode": "2823-3",
            "testName": "Serum Potassium",
            "numericValue": 6.8,
            "unit": "mEq/L",
            "referenceRange": "3.5 - 5.1 mEq/L",
        }

        response = client.post("/api/v1/alerts/evaluate-lab", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["isPanic"] is True
        assert data["severity"] == AlertSeverity.PANIC.value
        assert data["alertGenerated"] is True
        assert data["alertId"] is not None
        assert "critically HIGH" in data["message"]

    def test_evaluate_lab_observation_panic_low(self):
        """Asserts critically low blood glucose (38 mg/dL < 45) triggers PANIC alert."""
        payload = {
            "patientId": "pat-eval-02",
            "patientName": "Meera Nambiar",
            "doctorId": "doc-eval-01",
            "facilityId": "fac-aiims-delhi",
            "loincCode": "2345-7",
            "testName": "Serum Glucose",
            "numericValue": 38.0,
            "unit": "mg/dL",
            "referenceRange": "70 - 99 mg/dL",
        }

        response = client.post("/api/v1/alerts/evaluate-lab", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["isPanic"] is True
        assert data["severity"] == AlertSeverity.PANIC.value
        assert data["alertGenerated"] is True
        assert "critically LOW" in data["message"]

    def test_evaluate_lab_observation_normal_no_panic(self):
        """Asserts safe non-panic observation (Potassium 4.2 mEq/L) does not generate panic alert."""
        payload = {
            "patientId": "pat-eval-03",
            "patientName": "Kavita Sen",
            "doctorId": "doc-eval-01",
            "loincCode": "2823-3",
            "testName": "Serum Potassium",
            "numericValue": 4.2,
            "unit": "mEq/L",
            "referenceRange": "3.5 - 5.1 mEq/L",
        }

        response = client.post("/api/v1/alerts/evaluate-lab", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["isPanic"] is False
        assert data["alertGenerated"] is False
        assert data["alertId"] is None
        assert "safe non-panic limits" in data["message"]

    def test_evaluate_lab_observation_alias_matching(self):
        """Asserts analyte name 'serum potassium' without standard LOINC resolves alias and triggers panic."""
        payload = {
            "patientId": "pat-eval-04",
            "patientName": "Rajesh Gupta",
            "doctorId": "doc-eval-02",
            "loincCode": "UNKNOWN-CODE",
            "testName": "Serum Potassium",
            "numericValue": 2.4,  # < 2.8 panic low
            "unit": "mEq/L",
        }

        response = client.post("/api/v1/alerts/evaluate-lab", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["isPanic"] is True
        assert data["ruleMatched"] == "2823-3"
        assert "critically LOW" in data["message"]

    def test_publish_clinical_alert_manual(self):
        """Asserts manual clinical alert publication creates an UNREAD record."""
        payload = {
            "patientId": "pat-eval-05",
            "patientName": "Sunita Rao",
            "doctorId": "doc-eval-02",
            "category": "CRITICAL_VITALS",
            "severity": "CRITICAL",
            "title": "Severe Hypoxemia: SpO2 84%",
            "message": "Patient SpO2 dropped acutely to 84% on room air. Immediate oxygen supplementation advised.",
            "actionRequired": True,
        }

        response = client.post("/api/v1/alerts/publish", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert data["alertId"] is not None
        assert data["category"] == "CRITICAL_VITALS"
        assert data["severity"] == "CRITICAL"
        assert data["status"] == "UNREAD"
        assert data["title"] == "Severe Hypoxemia: SpO2 84%"

    def test_get_doctor_alerts_and_filters(self):
        """Asserts querying clinician alert feed with status and severity filters."""
        # Query for doc-ananya-sharma (has pre-seeded alerts)
        response = client.get("/api/v1/alerts/doctor/doc-ananya-sharma")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        # Test filter by severity=PANIC
        res_panic = client.get("/api/v1/alerts/doctor/doc-ananya-sharma?severity=PANIC")
        assert res_panic.status_code == 200
        for alert in res_panic.json():
            assert alert["severity"] == "PANIC"

    def test_get_single_alert_and_not_found(self):
        """Asserts fetching single alert details and returning 404 for unknown identifier."""
        # 1. Existing seed alert
        res_ok = client.get("/api/v1/alerts/alt-seed-001")
        assert res_ok.status_code == 200
        assert res_ok.json()["alertId"] == "alt-seed-001"
        assert res_ok.json()["patientName"] == "Arun Patel"

        # 2. Non-existent alert
        res_404 = client.get("/api/v1/alerts/nonexistent-alert-id")
        assert res_404.status_code == 404

    def test_acknowledge_alert_workflow(self):
        """Asserts clinician acknowledgement transitions status to ACKNOWLEDGED and captures clinical notes."""
        # First publish an alert to acknowledge
        create_res = client.post(
            "/api/v1/alerts/publish",
            json={
                "patientId": "pat-ack-01",
                "patientName": "Vikram Seth",
                "doctorId": "doc-ack-test",
                "category": "LAB_PANIC_VALUE",
                "severity": "PANIC",
                "title": "Platelets 14,000/uL",
                "message": "Critical thrombocytopenia",
            },
        )
        assert create_res.status_code == 201
        alert_id = create_res.json()["alertId"]

        # Acknowledge
        ack_payload = {
            "doctorId": "doc-ack-test",
            "clinicalAction": "Discontinued aspirin; ordered 1 unit irradiated apheresis platelets",
            "notes": "Patient admitted to Hematology Stepdown Unit",
        }
        ack_res = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", json=ack_payload)
        assert ack_res.status_code == 200
        ack_data = ack_res.json()

        assert ack_data["status"] == "ACKNOWLEDGED"
        assert ack_data["acknowledgedByDoctorId"] == "doc-ack-test"
        assert ack_data["acknowledgedAt"] is not None
        assert "Discontinued aspirin" in ack_data["clinicalActionTaken"]

    def test_doctor_alert_stats_and_unread_count(self):
        """Asserts fast unread count endpoint and full statistical breakdown."""
        # 1. Unread count
        res_count = client.get("/api/v1/alerts/doctor/doc-ananya-sharma/unread-count")
        assert res_count.status_code == 200
        assert "unreadCount" in res_count.json()
        assert res_count.json()["doctorId"] == "doc-ananya-sharma"

        # 2. Detailed stats
        res_stats = client.get("/api/v1/alerts/doctor/doc-ananya-sharma/stats")
        assert res_stats.status_code == 200
        data = res_stats.json()
        assert "totalAlerts" in data
        assert "panicCount" in data
        assert "acknowledgedCount" in data


class TestClinicalAlertsWebSocketSynchronization:
    """Suite verifying real-time WebSocket push delivery for critical alerts."""

    def test_critical_alert_websocket_broadcast_delivery(self):
        """Asserts that evaluating a panic-value observation immediately pushes a WebSocket frame to clinician."""
        doctor_id = "doc-ws-test-88"
        token = _generate_test_token(sub=doctor_id, role="DOCTOR")

        with client.websocket_connect(f"/ws/doctors/{doctor_id}/workspace?token={token}") as websocket:
            ack_frame = websocket.receive_json()
            assert ack_frame["eventType"] == WebSocketEventType.CONNECTION_ACK.value

            # Trigger panic-value evaluation via REST
            panic_payload = {
                "patientId": "pat-ws-panic-99",
                "patientName": "Aarav Sharma",
                "doctorId": doctor_id,
                "loincCode": "42757-5",
                "testName": "High-Sensitivity Cardiac Troponin I",
                "numericValue": 0.85,  # > 0.04 panic high
                "unit": "ng/mL",
                "referenceRange": "< 0.04 ng/mL",
            }
            eval_res = client.post("/api/v1/alerts/evaluate-lab", json=panic_payload)
            assert eval_res.status_code == 200
            assert eval_res.json()["isPanic"] is True

            # Inbound real-time WebSocket frame must arrive on clinician workspace
            alert_event = websocket.receive_json()
            assert alert_event["eventType"] == WebSocketEventType.CRITICAL_ALERT.value
            assert alert_event["channel"] == f"doctor:{doctor_id}:workspace"
            assert alert_event["payload"]["patientName"] == "Aarav Sharma"
            assert alert_event["payload"]["severity"] == AlertSeverity.PANIC.value
            assert alert_event["payload"]["observedValue"] == "0.85 ng/mL"
            assert alert_event["payload"]["actionRequired"] is True
