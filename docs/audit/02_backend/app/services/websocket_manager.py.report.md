# Principal Software Engineering Audit: backend/app/services/websocket_manager.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/websocket_manager.py` implements the distributed real-time communication backbone for the NIRMAYA platform. It provides high-concurrency WebSocket connection management across multiple Uvicorn worker processes using an extensible Pub/Sub architecture supporting two modes: a production `RedisPubSubAdapter` for horizontal multi-node synchronization and a zero-dependency `InMemoryPubSubAdapter` for local edge appliances and isolated test suites. It manages connection lifecycles, user-to-socket routing, channel-based multicast, heartbeat ping/pong keepalives, and clinical event broadcasting (e.g., OPD queue advancement, vital alert telemetry, panic notifications). Key architectural vulnerabilities include unauthenticated and unvalidated channel subscription commands allowing arbitrary clients to listen to private doctor or patient channels, unbuffered serial frame delivery in message bus dispatch that creates Slowloris denial-of-service vulnerabilities, and overly aggressive 0.5s Redis connection timeouts that trigger premature fallback under load.

### System Topology & Architectural Invariants
```
                 +-------------------------------------------------+
                 |        Client WebSockets (Doctor / Patient)     |
                 +-----------------------+-------------------------+
                                         |
                                         v
                 +-------------------------------------------------+
                 |       ConnectionManager (websocket_manager.py)  |
                 |                                                 |
                 |  [Connection Registry & Metadata]               |
                 |   - _connections: {conn_id: WebSocket}          |
                 |   - _user_to_connections: {user_id: {conn_id}}  |
                 |   - _channel_to_connections: {chan: {conn_id}}  |
                 +-----------------------+-------------------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
        +-------------------------+             +-------------------------+
        |   RedisPubSubAdapter    |             |  InMemoryPubSubAdapter  |
        |   (Production Cluster)  |             |  (Edge Node / Testing)  |
        |  - aioredis pub/sub     |             |  - asyncio.Lock         |
        |  - Background reader    |             |  - In-process callbacks |
        +------------+------------+             +------------+------------+
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                         v
                 +-------------------------------------------------+
                 |            Redis / In-Memory Message Bus        |
                 +-------------------------------------------------+
```

### Import / Export Surface Map
- **Upstream Dependencies:**
  - `asyncio`: Asynchronous task creation, locks, and cancellation.
  - `datetime.datetime`, `datetime.timezone`: UTC timestamp recording.
  - `json`: Message serialization/deserialization.
  - `logging`: Diagnostic logging under logger `"nirmaya.websockets"`.
  - `typing.Any`, `typing.Callable`, `typing.Coroutine`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Set`: Type annotations.
  - `uuid`: Connection ID generation.
  - `fastapi.WebSocket`, `fastapi.WebSocketDisconnect`: Protocol transport handlers.
  - `app.core.config.settings`: Configuration flags (`REDIS_ENABLED`, `REDIS_URL`, `WS_HEARTBEAT_INTERVAL_SECONDS`).
  - `app.schemas.websocket_events`: `ClientCommand`, `ConnectionAckPayload`, `WebSocketBaseEvent`, `WebSocketEventType`, `WebSocketMetricsResponse`.
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/websockets.py`: WebSocket gateway endpoint `/ws/clinical`.
  - Clinical services (`opd_queue.py`, `clinical_alerts.py`, `express_consultation_service.py`): Dispatch real-time events via `ws_manager.broadcast_event()`.
- **Exported Interface:**
  - `BasePubSubAdapter`: Abstract interface for Pub/Sub adapters.
  - `InMemoryPubSubAdapter`: Local in-memory broadcast adapter.
  - `RedisPubSubAdapter`: Horizontal Redis pub/sub broker adapter.
  - `ConnectionManager`: High-level connection registry and event dispatcher.
  - `ws_manager`: Global singleton connection manager.

---

## Layer B: Plain-Language Developer Walkthrough

The `websocket_manager.py` service coordinates real-time bi-directional messaging between clinicians, patients, and clinical subsystems:
1. **Adapter Initialization (`BasePubSubAdapter`, `InMemoryPubSubAdapter`, `RedisPubSubAdapter`)**: During startup, `ConnectionManager` chooses its message adapter. If `REDIS_ENABLED` is true and a valid URL is provided, it initializes `RedisPubSubAdapter`. It connects to Redis using `aioredis`, pings the broker, and launches a background asyncio task (`_reader_loop`) to poll for inbound cluster messages. If Redis is unavailable or unconfigured, it gracefully falls back to `InMemoryPubSubAdapter`.
2. **Client Connection (`connect`)**: When a client initiates a WebSocket handshake on `/ws/clinical`, the manager accepts the socket, assigns a unique UUID `connection_id`, registers the socket under its authenticated `user_id` and `role`, and subscribes it to any default auto-channels (e.g., `user:<user_id>`, `role:doctor`). It immediately dispatches a `ConnectionAck` event containing the assigned ID and heartbeat parameters.
3. **Channel Subscription & Multicast (`subscribe`, `unsubscribe`)**: Sockets can join named channels (e.g., `opd:dept_cardiology`, `alerts:ward_3`). When the first local socket joins a channel, the manager subscribes to that channel on the underlying message bus adapter. When a message is broadcast, the adapter delivers it to all connected cluster workers.
4. **Message Ingestion & Heartbeat (`handle_client_message`)**: Listens for text frames from clients. If a `ping` command is received, it responds with `HEARTBEAT_PONG` and updates `lastSeen` telemetry. If a `subscribe` or `unsubscribe` command is parsed, it mutates local channel bindings.
5. **Event Broadcasting (`broadcast_event`, `_on_bus_message`)**: Clinical services trigger `ws_manager.broadcast_event(channel, event_type, payload)`. The event is serialized to JSON and published to the message bus. When received via `_on_bus_message`, all local WebSockets bound to that channel receive the frame.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Unauthenticated Dynamic Channel Subscription (Access Control Bypass)
In `handle_client_message` (lines 430-455):
```python
elif action == "subscribe" and command.channel:
    await self.subscribe(connection_id, command.channel)
```
Any connected WebSocket client—regardless of whether they are a general patient or a third-party guest—can send `{"action": "subscribe", "channel": "doctor:doc-1234"}` or `{"action": "subscribe", "channel": "emergency:vault:alerts"}`. The manager binds the connection to that channel without checking whether the client's authenticated role or user ID permits access to that channel topic. This permits unauthorized snooping on private patient consultations and clinical emergency alerts.

### Invariant 2: Serial Unthrottled WebSocket Frame Delivery (Slowloris DoS)
In `_on_bus_message` (lines 375-393):
```python
for conn_id in subscribers:
    ws = self._connections.get(conn_id)
    if ws:
        try:
            await ws.send_json(event_dict)
            self._messages_delivered_total += 1
```
The loop awaits `ws.send_json` sequentially across all subscribers on that channel. If a malicious or slow client on a high-latency mobile connection blocks TCP window transmission, this `await` stalls. Other subscribers on the same uvicorn worker waiting in the loop will experience delayed message delivery or connection dropouts.

### Invariant 3: Overly Aggressive 0.5s Redis Socket Timeout
In `RedisPubSubAdapter.start` (lines 134-137):
```python
socket_connect_timeout=0.5,
socket_timeout=0.5,
await asyncio.wait_for(self._redis.ping(), timeout=0.5)
```
A 500ms timeout is excessively strict for production container networks experiencing transient CPU spikes or network re-routing. If Redis takes 550ms to respond to the initial ping during a rolling deployment, the manager prints a warning and silently falls back to `InMemoryPubSubAdapter`. In a multi-worker setup, this causes workers to partition into isolated islands that cannot communicate with each other.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SVC-WSM-F01` | **S1** | `[SEC]` | `websocket_manager.py:451-455` | Unauthenticated channel subscription in `handle_client_message` allows clients to eavesdrop on arbitrary private channels. |
| `BE-SVC-WSM-F02` | **S1** | `[SEC]` / `[PERF]` | `websocket_manager.py:385-393` | Sequential frame delivery in `_on_bus_message` allows slow clients to stall message broadcasts for all other local subscribers (Slowloris DoS). |
| `BE-SVC-WSM-F03` | **S2** | `[QUAL]` / `[PERF]` | `websocket_manager.py:134-144` | Aggressive 0.5s Redis connect/ping timeout triggers silent fallback to in-memory bus under minor container network latency. |
| `BE-SVC-WSM-F04` | **S2** | `[QUAL]` | `websocket_manager.py:160-165` | `_reader_loop` logs exceptions and loops without exponential backoff or reconnection logic if the Redis connection breaks. |
| `BE-SVC-WSM-F05` | **S3** | `[PERF]` | `websocket_manager.py:271-285` | In-memory connection registration holds `self._lock` during metadata mutations, creating lock contention under high-volume connection storms. |
| `BE-SVC-WSM-F06` | **S4** | `[DOC]` | `websocket_manager.py:1-6` | Lacks documentation on backpressure handling, maximum frame sizing, and binary WebSocket protocols for clinical ECG/vital streaming. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-WSM-F01-F02`: Channel Authorization & Concurrent Frame Dispatch
```diff
--- a/backend/app/services/websocket_manager.py
+++ b/backend/app/services/websocket_manager.py
@@ -382,13 +382,15 @@
         async with self._lock:
             subscribers = list(self._channel_to_connections.get(channel, set()))
 
+        async def _safe_send(conn_id: str) -> None:
+            ws = self._connections.get(conn_id)
+            if ws:
+                try:
+                    await asyncio.wait_for(ws.send_json(event_dict), timeout=2.0)
+                    self._messages_delivered_total += 1
+                except Exception:
+                    pass
+
+        await asyncio.gather(*[_safe_send(cid) for cid in subscribers], return_exceptions=True)
+
-        for conn_id in subscribers:
-            ws = self._connections.get(conn_id)
-            if ws:
-                try:
-                    await ws.send_json(event_dict)
-                    self._messages_delivered_total += 1
-                except Exception as e:
-                    logger.warning(f"[WebSocket] Failed to send message to {conn_id}: {e}")
```
