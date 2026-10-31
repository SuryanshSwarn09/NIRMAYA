"""Automated Test Suite for Distributed WebSockets & Redis Pub/Sub Gateway.

Validates:
- WebSocket handshake & Supabase JWT query authentication
- Immediate connection rejection for missing/invalid tokens (code 1008)
- ConnectionAck payload dispatch and server time synchronization
- Heartbeat ping/pong frame exchange
- Dynamic client channel subscription & unsubscription commands
- Facility OPD live patient queue updates
- Clinician workspace critical laboratory panic-value alerts
- Multi-client simultaneous channel broadcast delivery
- Diagnostic metrics & administrative broadcast REST APIs
"""

import json
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.main import app
from app.schemas.websocket_events import (
    AlertSeverity,
    CriticalAlertPayload,
    HoldStatus,
    QueueUpdatePayload,
    TriageLevel,
    WebSocketChannel,
    WebSocketEventType,
)
from app.services.websocket_manager import ws_manager

client = TestClient(app)


def _generate_test_token(sub: str = "doc-test-001", role: str = "DOCTOR") -> str:
    """Helper to mint valid test JWT tokens with role claims."""
    return create_access_token(
        data={"sub": sub, "role": role, "user_metadata": {"role": role}},
    )


class TestWebSocketAuthenticationAndLifecycle:
    """Tests for WebSocket handshake, authentication, and connection lifecycle."""

    def test_ws_rejects_missing_token(self):
        """Asserts that connecting without a JWT token immediately closes with code 1008."""
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/events"):
                pass
        assert exc_info.value.code == 1008

    def test_ws_rejects_invalid_token(self):
        """Asserts that connecting with a forged/malformed token closes with code 1008."""
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/events?token=forged.invalid.token"):
                pass
        assert exc_info.value.code == 1008

    def test_ws_connection_success_and_ack(self):
        """Asserts that a valid JWT connects and receives an immediate ConnectionAck event."""
        token = _generate_test_token(sub="doc-101", role="DOCTOR")
        with client.websocket_connect(f"/ws/events?token={token}") as websocket:
            data = websocket.receive_json()
            assert data["eventType"] == WebSocketEventType.CONNECTION_ACK.value
            assert data["channel"] == "direct"
            payload = data["payload"]
            assert payload["userId"] == "doc-101"
            assert payload["role"] == "DOCTOR"
            assert WebSocketChannel.GLOBAL_EVENTS in payload["subscribedChannels"]
            assert WebSocketChannel.doctor_workspace("doc-101") in payload["subscribedChannels"]

    def test_ws_heartbeat_ping_pong(self):
        """Asserts client sending a ping receives an immediate pong frame from server."""
        token = _generate_test_token(sub="patient-501", role="PATIENT")
        with client.websocket_connect(f"/ws/events?token={token}") as websocket:
            # Drain initial ConnectionAck
            _ = websocket.receive_json()

            # Dispatch ping command
            websocket.send_text(json.dumps({"action": "ping"}))
            response = websocket.receive_json()

            assert response["eventType"] == WebSocketEventType.HEARTBEAT_PONG.value
            assert response["channel"] == "direct"
            assert "serverTime" in response["payload"]

    def test_ws_channel_subscribe_and_unsubscribe_commands(self):
        """Asserts client can subscribe and unsubscribe to custom topics dynamically."""
        token = _generate_test_token(sub="staff-201", role="CLINICAL_STAFF")
        target_channel = "facility:HOSP-BLR-01:ot_status"

        with client.websocket_connect(f"/ws/events?token={token}") as websocket:
            _ = websocket.receive_json()  # Ack

            # Subscribe
            websocket.send_text(json.dumps({"action": "subscribe", "channel": target_channel}))
            # Verify metric shows channel subscribed
            metrics = ws_manager.get_metrics()
            assert target_channel in metrics.channelSubscribers

            # Unsubscribe
            websocket.send_text(json.dumps({"action": "unsubscribe", "channel": target_channel}))
            metrics = ws_manager.get_metrics()
            assert target_channel not in metrics.channelSubscribers


class TestClinicalStreamsAndBroadcasts:
    """Tests for specialized clinical event streams (OPD queue & doctor alerts)."""

    def test_facility_queue_stream_broadcast(self):
        """Asserts facility OPD stream receives live patient queue status changes."""
        facility_id = "FAC-DL-001"
        token = _generate_test_token(sub="nurse-01", role="CLINICAL_STAFF")

        with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={token}") as websocket:
            _ = websocket.receive_json()  # Ack

            # Publish queue update event
            queue_payload = QueueUpdatePayload(
                facilityId=facility_id,
                queueEntryId="QE-992",
                patientId="PAT-8812",
                patientName="Aarav Sharma",
                tokenNumber=42,
                status="WAITING",
                triageLevel=TriageLevel.URGENT,
                estimatedWaitMinutes=12,
            )

            # Broadcast via REST endpoint
            post_res = client.post(
                "/api/v1/websockets/broadcast",
                json={
                    "channel": WebSocketChannel.facility_queue(facility_id),
                    "eventType": WebSocketEventType.QUEUE_UPDATE.value,
                    "payload": queue_payload.model_dump(),
                },
            )
            assert post_res.status_code == 202

            # Client receives event
            event = websocket.receive_json()
            assert event["eventType"] == WebSocketEventType.QUEUE_UPDATE.value
            assert event["channel"] == f"facility:{facility_id}:queue"
            assert event["payload"]["patientName"] == "Aarav Sharma"
            assert event["payload"]["tokenNumber"] == 42
            assert event["payload"]["triageLevel"] == "URGENT"

    def test_doctor_workspace_critical_alert(self):
        """Asserts clinician stream receives high-priority panic-value clinical alerts."""
        doctor_id = "DOC-CAR-09"
        token = _generate_test_token(sub=doctor_id, role="DOCTOR")

        with client.websocket_connect(f"/ws/doctors/{doctor_id}/workspace?token={token}") as websocket:
            _ = websocket.receive_json()  # Ack

            alert_payload = CriticalAlertPayload(
                patientId="PAT-4040",
                patientName="Ramesh Verma",
                doctorId=doctor_id,
                severity=AlertSeverity.PANIC,
                category="LAB_PANIC_VALUE",
                title="Critical Hyperkalemia Alert",
                message="Serum Potassium 6.9 mEq/L (Normal: 3.5-5.0 mEq/L). Immediate ECG indicated.",
                loincCode="2823-3",
                observedValue="6.9 mEq/L",
                referenceRange="3.5 - 5.0 mEq/L",
                actionRequired=True,
            )

            post_res = client.post(
                "/api/v1/websockets/broadcast",
                json={
                    "channel": WebSocketChannel.doctor_workspace(doctor_id),
                    "eventType": WebSocketEventType.CRITICAL_ALERT.value,
                    "payload": alert_payload.model_dump(),
                },
            )
            assert post_res.status_code == 202

            received = websocket.receive_json()
            assert received["eventType"] == WebSocketEventType.CRITICAL_ALERT.value
            assert received["channel"] == f"doctor:{doctor_id}:workspace"
            assert received["payload"]["severity"] == "PANIC"
            assert received["payload"]["loincCode"] == "2823-3"
            assert received["payload"]["actionRequired"] is True

    def test_multi_client_channel_broadcast(self):
        """Asserts multiple clients subscribed to the same channel receive identical messages."""
        facility_id = "FAC-MUM-99"
        tok1 = _generate_test_token(sub="staff-1", role="CLINICAL_STAFF")
        tok2 = _generate_test_token(sub="staff-2", role="CLINICAL_STAFF")

        with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={tok1}") as ws1:
            _ = ws1.receive_json()  # Ack 1
            with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={tok2}") as ws2:
                _ = ws2.receive_json()  # Ack 2

                # Broadcast to facility via REST
                post_res = client.post(
                    "/api/v1/websockets/broadcast",
                    json={
                        "channel": WebSocketChannel.facility_queue(facility_id),
                        "eventType": WebSocketEventType.QUEUE_CALLED.value,
                        "payload": {"tokenNumber": 105, "room": "OPD-Room-3"},
                    },
                )
                assert post_res.status_code == 202

                ev1 = ws1.receive_json()
                ev2 = ws2.receive_json()

                assert ev1["eventId"] == ev2["eventId"]
                assert ev1["payload"]["tokenNumber"] == 105
                assert ev2["payload"]["tokenNumber"] == 105


class TestWebSocketManagementAndDiagnosticsAPI:
    """Tests for REST metrics and administrative broadcast endpoints."""

    def test_websocket_metrics_endpoint(self):
        """Asserts GET /api/v1/websockets/metrics returns gateway telemetry."""
        response = client.get("/api/v1/websockets/metrics")
        assert response.status_code == 200
        data = response.json()

        assert "activeConnections" in data
        assert "activeUsers" in data
        assert "totalSubscribedChannels" in data
        assert "channelSubscribers" in data
        assert "adapterMode" in data
        assert data["adapterMode"] in ["IN_MEMORY", "REDIS"]
        assert "messagesPublishedTotal" in data
        assert "messagesDeliveredTotal" in data

    def test_websocket_admin_broadcast_endpoint(self):
        """Asserts POST /api/v1/websockets/broadcast successfully dispatches events onto bus."""
        payload = {
            "channel": "global:events",
            "eventType": "system.notification",
            "payload": {
                "title": "Hospital Emergency Mock Drill",
                "message": "Routine emergency drill commencing at 14:00 IST.",
                "level": "INFO",
            },
        }

        response = client.post("/api/v1/websockets/broadcast", json=payload)
        assert response.status_code == 202
        data = response.json()

        assert data["status"] == "BROADCAST_QUEUED"
        assert data["channel"] == "global:events"
        assert data["eventType"] == "system.notification"
        assert "eventId" in data
