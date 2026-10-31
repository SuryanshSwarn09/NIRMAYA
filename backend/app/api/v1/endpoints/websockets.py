"""WebSocket Gateway & Real-Time Event REST API Endpoints for NIRMAYA.

Provides authenticated WebSocket endpoints for:
- `/ws/events`: Multi-channel clinical and system event stream
- `/ws/facilities/{facility_id}/queue`: Dedicated real-time OPD patient queue
- `/ws/doctors/{doctor_id}/workspace`: Dedicated clinician consultation stream
Along with diagnostic metrics and administrative event broadcast APIs.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.security import decode_access_token
from app.schemas.websocket_events import (
    AdminBroadcastRequest,
    WebSocketBaseEvent,
    WebSocketChannel,
    WebSocketEventType,
    WebSocketMetricsResponse,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("nirmaya.websockets.api")

router = APIRouter()


# -----------------------------------------------------------------------------
# WebSocket Authentication Helper
# -----------------------------------------------------------------------------

async def authenticate_websocket(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """Validate JWT token passed in query parameter or subprotocol headers.

    If validation fails, the connection is rejected with close code 1008 (Policy Violation).
    """
    token = websocket.query_params.get(settings.WS_TOKEN_PARAM)

    # Check for token in Sec-WebSocket-Protocol headers if not in query
    if not token and "sec-websocket-protocol" in websocket.headers:
        protocols = [p.strip() for p in websocket.headers["sec-websocket-protocol"].split(",")]
        # Conventional 'bearer, <jwt>' subprotocol scheme
        if len(protocols) >= 2 and protocols[0].lower() == "bearer":
            token = protocols[1]
        elif len(protocols) == 1:
            token = protocols[0]

    if not token:
        logger.warning("[WebSocketAuth] Missing JWT credentials on connection handshake")
        await websocket.close(code=1008, reason="Missing authentication token")
        return None

    try:
        # Decode and verify JWT claims
        payload = decode_access_token(token, verify_aud=False)
        return payload
    except AuthenticationException as ae:
        logger.warning(f"[WebSocketAuth] Authentication rejected: {ae.message}")
        await websocket.close(code=1008, reason="Invalid or expired JWT token")
        return None
    except Exception as e:
        logger.warning(f"[WebSocketAuth] Unexpected error during token verification: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return None


# -----------------------------------------------------------------------------
# WebSocket Stream Endpoints
# -----------------------------------------------------------------------------

@router.websocket("/events")
async def websocket_events_gateway(websocket: WebSocket):
    """General authenticated real-time clinical and system event stream.

    Supports dynamic channel subscriptions, heartbeats (ping/pong), and personal notifications.
    """
    claims = await authenticate_websocket(websocket)
    if not claims:
        return

    user_id = str(claims.get("sub", "anon-user"))
    user_metadata = claims.get("user_metadata", {})
    role = str(user_metadata.get("role", claims.get("role", "PATIENT"))).upper()

    auto_channels = [WebSocketChannel.GLOBAL_EVENTS]
    if role == "DOCTOR":
        auto_channels.append(WebSocketChannel.doctor_workspace(user_id))
    elif role == "PATIENT":
        auto_channels.append(WebSocketChannel.patient_vault(user_id))

    connection_id = await ws_manager.connect(
        websocket=websocket,
        user_id=user_id,
        role=role,
        auto_channels=auto_channels,
    )

    try:
        while True:
            text_data = await websocket.receive_text()
            await ws_manager.handle_client_message(connection_id, text_data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"[WebSocket] Error on stream {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


@router.websocket("/facilities/{facility_id}/queue")
async def facility_opd_queue_websocket(websocket: WebSocket, facility_id: str):
    """Dedicated live stream for outpatient department (OPD) queue updates.

    Auto-subscribes clients to the facility queue channel.
    """
    claims = await authenticate_websocket(websocket)
    if not claims:
        return

    user_id = str(claims.get("sub", "staff-user"))
    user_metadata = claims.get("user_metadata", {})
    role = str(user_metadata.get("role", claims.get("role", "CLINICAL_STAFF"))).upper()

    facility_channel = WebSocketChannel.facility_queue(facility_id)
    connection_id = await ws_manager.connect(
        websocket=websocket,
        user_id=user_id,
        role=role,
        auto_channels=[facility_channel, WebSocketChannel.GLOBAL_EVENTS],
    )

    try:
        while True:
            text_data = await websocket.receive_text()
            await ws_manager.handle_client_message(connection_id, text_data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"[WebSocket] Error on queue stream {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


@router.websocket("/doctors/{doctor_id}/workspace")
async def doctor_workspace_websocket(websocket: WebSocket, doctor_id: str):
    """Dedicated live stream for clinician workspace, alerts, and patient triage calls."""
    claims = await authenticate_websocket(websocket)
    if not claims:
        return

    user_id = str(claims.get("sub", doctor_id))
    user_metadata = claims.get("user_metadata", {})
    role = str(user_metadata.get("role", claims.get("role", "DOCTOR"))).upper()

    doc_channel = WebSocketChannel.doctor_workspace(doctor_id)
    connection_id = await ws_manager.connect(
        websocket=websocket,
        user_id=user_id,
        role=role,
        auto_channels=[doc_channel, WebSocketChannel.GLOBAL_EVENTS],
    )

    try:
        while True:
            text_data = await websocket.receive_text()
            await ws_manager.handle_client_message(connection_id, text_data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"[WebSocket] Error on doctor workspace stream {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


# -----------------------------------------------------------------------------
# REST Management & Diagnostics Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/metrics",
    response_model=WebSocketMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve WebSocket gateway telemetry and Pub/Sub metrics",
)
async def get_websocket_metrics() -> WebSocketMetricsResponse:
    """Returns active sockets count, distinct users, channel subscribers, and message counters."""
    return ws_manager.get_metrics()


@router.post(
    "/broadcast",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Publish clinical or administrative event to WebSocket channel",
)
async def broadcast_event(request: AdminBroadcastRequest):
    """Administrative or internal service trigger to broadcast an event onto a channel."""
    event = await ws_manager.broadcast_event(
        channel=request.channel,
        event_type=request.eventType,
        payload=request.payload,
    )
    return {
        "status": "BROADCAST_QUEUED",
        "channel": request.channel,
        "eventId": event.eventId,
        "eventType": event.eventType,
        "timestamp": event.timestamp,
    }

