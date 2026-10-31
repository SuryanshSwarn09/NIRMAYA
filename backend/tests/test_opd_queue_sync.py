"""Automated Test Suite for Live OPD Consultation Queue Synchronization.

Validates:
- Patient reception check-in and sequential daily token minting
- Clinical triage classification updates and wait time estimations
- Attending doctor patient call into specific consulting rooms
- Lifecycle status transitions (WAITING -> CALLED -> IN_CONSULTATION -> COMPLETED)
- Real-time automated WebSocket event broadcasts on facility queue streams
- Operational statistics and throughput metrics calculations
- Robust 404 handling on nonexistent queue entries
"""

import json
import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.schemas.opd_queue import (
    OPDQueueEntry,
    QueueCallPatientRequest,
    QueueCheckInRequest,
    QueueStatus,
    QueueStatusUpdateRequest,
    QueueTriageUpdateRequest,
)
from app.schemas.websocket_events import TriageLevel, WebSocketChannel, WebSocketEventType
from app.services.opd_queue import opd_queue_service

client = TestClient(app)


def _generate_test_token(sub: str = "doc-queue-tester", role: str = "DOCTOR") -> str:
    """Helper to mint valid test JWT tokens with role claims."""
    return create_access_token(
        data={"sub": sub, "role": role, "user_metadata": {"role": role}},
    )


class TestOpdQueueLifecycleAndManagement:
    """Tests for REST API OPD queue registration, triage, calling, and stats."""

    def test_check_in_patient(self):
        """Asserts reception check-in mintage of sequential token number and WAITING state."""
        payload = {
            "facilityId": "IN0410000123",
            "patientId": "pat-test-uuid-001",
            "patientName": "Sunita Rao",
            "patientAbha": "91-1122-3344-5566",
            "patientPhone": "+91 99001 22334",
            "doctorId": "doc-test-001",
            "doctorName": "Dr. Ananya Sharma",
            "triageLevel": "URGENT",
            "chiefComplaint": "Persistent fever and productive cough for 5 days",
            "notes": "Walk-in registration",
        }

        response = client.post("/api/v1/queue/check-in", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert data["patientName"] == "Sunita Rao"
        assert data["tokenNumber"] >= 1
        assert data["status"] == "WAITING"
        assert data["triageLevel"] == "URGENT"
        assert "queueId" in data
        assert "checkInTime" in data

    def test_get_facility_queue(self):
        """Asserts retrieval of facility OPD queue with count statistics."""
        response = client.get("/api/v1/queue/facility/IN0410000123")
        assert response.status_code == 200
        data = response.json()

        assert data["facilityId"] == "IN0410000123"
        assert data["totalEntries"] >= 1
        assert "waitingCount" in data
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_get_single_queue_entry(self):
        """Asserts fetching details of an existing queue entry."""
        # Query default seeded entry
        response = client.get("/api/v1/queue/entry/queue-seed-01")
        assert response.status_code == 200
        data = response.json()

        assert data["queueId"] == "queue-seed-01"
        assert data["patientName"] == "Arun Patel"
        assert data["tokenNumber"] == 1

    def test_get_single_queue_entry_not_found(self):
        """Asserts HTTP 404 for nonexistent queue entry."""
        response = client.get("/api/v1/queue/entry/nonexistent-queue-uuid")
        assert response.status_code == 404

    def test_update_patient_triage(self):
        """Asserts updating patient triage classification modifies urgency and wait time."""
        payload = {
            "triageLevel": "EMERGENT",
            "estimatedWaitMinutes": 3,
            "notes": "Patient showing signs of respiratory distress",
        }

        response = client.put("/api/v1/queue/queue-seed-01/triage", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["triageLevel"] == "EMERGENT"
        assert data["estimatedWaitMinutes"] == 3
        assert "Triage Note:" in (data["notes"] or "")

    def test_call_patient_to_room(self):
        """Asserts clinician patient summon transitions status to CALLED and records room."""
        payload = {
            "doctorId": "doc-test-001",
            "doctorName": "Dr. Ananya Sharma",
            "roomNumber": "Consultation Room 3",
        }

        response = client.post("/api/v1/queue/queue-seed-02/call", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "CALLED"
        assert data["roomNumber"] == "Consultation Room 3"
        assert data["calledTime"] is not None

    def test_advance_queue_status_in_consultation_and_completed(self):
        """Asserts lifecycle transitions through IN_CONSULTATION and COMPLETED."""
        # 1. Start consultation
        start_payload = {
            "status": "IN_CONSULTATION",
            "roomNumber": "Room 3",
            "notes": "Consultation begun",
        }
        res1 = client.put("/api/v1/queue/queue-seed-02/status", json=start_payload)
        assert res1.status_code == 200
        assert res1.json()["status"] == "IN_CONSULTATION"
        assert res1.json()["consultationStartTime"] is not None

        # 2. Complete consultation
        complete_payload = {
            "status": "COMPLETED",
            "notes": "Rx provided and follow-up scheduled",
        }
        res2 = client.put("/api/v1/queue/queue-seed-02/status", json=complete_payload)
        assert res2.status_code == 200
        assert res2.json()["status"] == "COMPLETED"
        assert res2.json()["completedTime"] is not None

    def test_facility_queue_stats(self):
        """Asserts live throughput statistics calculations for facility."""
        response = client.get("/api/v1/queue/facility/IN0410000123/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["facilityId"] == "IN0410000123"
        assert "activeTokens" in data
        assert "waitingCount" in data
        assert "urgentCount" in data
        assert "emergentCount" in data
        assert "averageWaitMinutes" in data
        assert "completedToday" in data


class TestOpdQueueWebSocketSynchronization:
    """Tests asserting real-time WebSocket broadcast propagation on queue transitions."""

    def test_check_in_broadcasts_websocket_update(self):
        """Asserts reception check-in automatically broadcasts a queue.update frame over WebSocket."""
        facility_id = "FAC-RT-TEST-01"
        token = _generate_test_token(sub="nurse-ws-01", role="CLINICAL_STAFF")

        with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={token}") as websocket:
            _ = websocket.receive_json()  # Drain ConnectionAck

            # Check-in patient via REST
            check_in_payload = {
                "facilityId": facility_id,
                "patientId": "pat-ws-sync-01",
                "patientName": "Devendra Joshi",
                "patientAbha": "91-4455-6677-8899",
                "triageLevel": "URGENT",
                "chiefComplaint": "Acute migrainous headache",
            }
            res = client.post("/api/v1/queue/check-in", json=check_in_payload)
            assert res.status_code == 201

            # Inbound WebSocket frame must arrive
            event = websocket.receive_json()
            assert event["eventType"] == WebSocketEventType.QUEUE_UPDATE.value
            assert event["channel"] == f"facility:{facility_id}:queue"
            assert event["payload"]["patientName"] == "Devendra Joshi"
            assert event["payload"]["triageLevel"] == "URGENT"
            assert event["payload"]["status"] == "WAITING"

    def test_call_patient_broadcasts_websocket_queue_called(self):
        """Asserts clinician summoning patient broadcasts a queue.called frame with room number."""
        facility_id = "FAC-RT-TEST-02"
        token = _generate_test_token(sub="nurse-ws-02", role="CLINICAL_STAFF")

        with client.websocket_connect(f"/ws/facilities/{facility_id}/queue?token={token}") as websocket:
            _ = websocket.receive_json()  # Drain Ack

            # 1. Check in
            check_in_res = client.post(
                "/api/v1/queue/check-in",
                json={
                    "facilityId": facility_id,
                    "patientId": "pat-ws-sync-02",
                    "patientName": "Meera Nambiar",
                    "triageLevel": "STANDARD",
                },
            )
            assert check_in_res.status_code == 201
            queue_id = check_in_res.json()["queueId"]

            # Drain queue.update frame
            _ = websocket.receive_json()

            # 2. Call patient to room
            call_res = client.post(
                f"/api/v1/queue/{queue_id}/call",
                json={
                    "doctorId": "doc-cardio-01",
                    "doctorName": "Dr. Vivek Murthy",
                    "roomNumber": "Consultation Suite A",
                },
            )
            assert call_res.status_code == 200

            # Inbound WebSocket frame must arrive
            called_event = websocket.receive_json()
            assert called_event["eventType"] == WebSocketEventType.QUEUE_CALLED.value
            assert called_event["channel"] == f"facility:{facility_id}:queue"
            assert called_event["payload"]["patientName"] == "Meera Nambiar"
            assert called_event["payload"]["status"] == "CALLED"
            assert called_event["payload"]["roomNumber"] == "Consultation Suite A"

