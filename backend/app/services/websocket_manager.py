"""Distributed WebSocket Connection Manager & Redis Pub/Sub Bus Service for NIRMAYA.

Provides high-concurrency real-time WebSocket communication across multiple uvicorn
workers using a dual-mode Redis Pub/Sub message adapter (with zero-dependency
in-memory fallback for testing and solo edge nodes).
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.schemas.websocket_events import (
    ClientCommand,
    ConnectionAckPayload,
    WebSocketBaseEvent,
    WebSocketEventType,
    WebSocketMetricsResponse,
)

logger = logging.getLogger("nirmaya.websockets")


# -----------------------------------------------------------------------------
# Pub/Sub Adapter Implementations
# -----------------------------------------------------------------------------

class BasePubSubAdapter:
    """Abstract interface for inter-worker Pub/Sub message brokers."""

    async def start(self) -> None:
        """Start the adapter background workers."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Stop adapter and release connections."""
        raise NotImplementedError

    async def publish(self, channel: str, message: str) -> None:
        """Publish raw serialized message to channel."""
        raise NotImplementedError

    async def subscribe(self, channel: str, callback: Callable[[str, str], Coroutine[Any, Any, None]]) -> None:
        """Subscribe local callback to receive messages on channel."""
        raise NotImplementedError

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from channel."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Check if message bus is active."""
        raise NotImplementedError

    def get_mode(self) -> str:
        """Get descriptive mode identifier ('REDIS' or 'IN_MEMORY')."""
        raise NotImplementedError


class InMemoryPubSubAdapter(BasePubSubAdapter):
    """Zero-dependency in-memory Pub/Sub adapter for development, tests, and solo edge nodes."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[Callable[[str, str], Coroutine[Any, Any, None]]]] = {}
        self._lock = asyncio.Lock()
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("[WebSocketBus] In-Memory Pub/Sub adapter initialized")

    async def stop(self) -> None:
        self._running = False
        async with self._lock:
            self._subscribers.clear()
        logger.info("[WebSocketBus] In-Memory Pub/Sub adapter stopped")

    async def publish(self, channel: str, message: str) -> None:
        if not self._running:
            return
        async with self._lock:
            callbacks = list(self._subscribers.get(channel, set()))
            # Also check if wildcards or global listeners exist
            global_cbs = list(self._subscribers.get("*", set()))

        all_callbacks = callbacks + global_cbs
        for cb in all_callbacks:
            try:
                asyncio.create_task(cb(channel, message))
            except Exception as e:
                logger.error(f"[WebSocketBus] Error dispatching in-memory message on channel '{channel}': {e}")

    async def subscribe(self, channel: str, callback: Callable[[str, str], Coroutine[Any, Any, None]]) -> None:
        async with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = set()
            self._subscribers[channel].add(callback)

    async def unsubscribe(self, channel: str) -> None:
        async with self._lock:
            self._subscribers.pop(channel, None)

    def is_connected(self) -> bool:
        return self._running

    def get_mode(self) -> str:
        return "IN_MEMORY"


class RedisPubSubAdapter(BasePubSubAdapter):
    """Production Redis Pub/Sub adapter supporting horizontal multi-worker scaling."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._subscribers: Dict[str, Set[Callable[[str, str], Coroutine[Any, Any, None]]]] = {}
        self._lock = asyncio.Lock()
        self._connected = False

    async def start(self) -> None:
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._pubsub = self._redis.pubsub()
            self._connected = True
            self._reader_task = asyncio.create_task(self._reader_loop())
            logger.info(f"[WebSocketBus] Connected to Redis Pub/Sub at {self.redis_url}")
        except Exception as e:
            logger.warning(f"[WebSocketBus] Failed to connect to Redis at {self.redis_url}: {e}. Falling back to in-memory bus.")
            self._connected = False

    async def _reader_loop(self) -> None:
        """Background task reading messages from Redis subscription stream."""
        try:
            while self._connected and self._pubsub:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    async with self._lock:
                        callbacks = list(self._subscribers.get(channel, set()))
                    for cb in callbacks:
                        try:
                            asyncio.create_task(cb(channel, data))
                        except Exception as cb_err:
                            logger.error(f"[WebSocketBus] Callback error: {cb_err}")
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[WebSocketBus] Redis reader loop error: {e}")

    async def stop(self) -> None:
        self._connected = False
        if self._reader_task:
            self._reader_task.cancel()
        if self._pubsub:
            try:
                await self._pubsub.close()
            except Exception:
                pass
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
        logger.info("[WebSocketBus] Redis Pub/Sub adapter stopped")

    async def publish(self, channel: str, message: str) -> None:
        if self._connected and self._redis:
            await self._redis.publish(channel, message)
        else:
            logger.warning(f"[WebSocketBus] Redis not connected; cannot publish to channel '{channel}'")

    async def subscribe(self, channel: str, callback: Callable[[str, str], Coroutine[Any, Any, None]]) -> None:
        async with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = set()
                if self._connected and self._pubsub:
                    await self._pubsub.subscribe(channel)
            self._subscribers[channel].add(callback)

    async def unsubscribe(self, channel: str) -> None:
        async with self._lock:
            self._subscribers.pop(channel, None)
            if self._connected and self._pubsub:
                await self._pubsub.unsubscribe(channel)

    def is_connected(self) -> bool:
        return self._connected

    def get_mode(self) -> str:
        return "REDIS" if self._connected else "REDIS_FALLBACK"


# -----------------------------------------------------------------------------
# Connection Manager
# -----------------------------------------------------------------------------

class ConnectionManager:
    """Enterprise-grade registry and dispatcher for active WebSocket connections."""

    def __init__(self, adapter: Optional[BasePubSubAdapter] = None) -> None:
        # If no adapter provided or REDIS_ENABLED is False, default to in-memory adapter
        if adapter is not None:
            self.adapter: BasePubSubAdapter = adapter
        elif settings.REDIS_ENABLED and settings.REDIS_URL:
            self.adapter = RedisPubSubAdapter(settings.REDIS_URL)
        else:
            self.adapter = InMemoryPubSubAdapter()

        self._connections: Dict[str, WebSocket] = {}
        self._user_to_connections: Dict[str, Set[str]] = {}
        self._channel_to_connections: Dict[str, Set[str]] = {}
        self._connection_to_channels: Dict[str, Set[str]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

        self._messages_published_total: int = 0
        self._messages_delivered_total: int = 0
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Start message bus adapter."""
        if not self._initialized:
            await self.adapter.start()
            self._initialized = True

    async def shutdown(self) -> None:
        """Close all connections and terminate adapter."""
        async with self._lock:
            for conn_id, ws in list(self._connections.items()):
                try:
                    await ws.close(code=1001, reason="Server shutting down")
                except Exception:
                    pass
            self._connections.clear()
            self._user_to_connections.clear()
            self._channel_to_connections.clear()
            self._connection_to_channels.clear()
            self._metadata.clear()

        await self.adapter.stop()
        self._initialized = False

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        role: str,
        auto_channels: Optional[List[str]] = None,
    ) -> str:
        """Accept WebSocket connection, assign connection ID, and auto-subscribe to default channels."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())

        async with self._lock:
            self._connections[connection_id] = websocket

            if user_id not in self._user_to_connections:
                self._user_to_connections[user_id] = set()
            self._user_to_connections[user_id].add(connection_id)

            self._connection_to_channels[connection_id] = set()
            self._metadata[connection_id] = {
                "userId": user_id,
                "role": role,
                "connectedAt": datetime.now(timezone.utc).isoformat(),
                "lastSeen": datetime.now(timezone.utc).isoformat(),
            }

        channels_to_bind = auto_channels or []
        for ch in channels_to_bind:
            await self.subscribe(connection_id, ch)

        # Dispatch immediate ConnectionAck
        ack = ConnectionAckPayload(
            connectionId=connection_id,
            userId=user_id,
            role=role,
            subscribedChannels=channels_to_bind,
            heartbeatIntervalSeconds=settings.WS_HEARTBEAT_INTERVAL_SECONDS,
        )
        ack_event = WebSocketBaseEvent(
            eventType=WebSocketEventType.CONNECTION_ACK,
            channel="direct",
            payload=ack.model_dump(),
        )
        await self.send_personal_event(connection_id, ack_event)

        logger.info(f"[WebSocket] Connected client {connection_id} (user={user_id}, role={role}, channels={channels_to_bind})")
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """Remove connection and cleanup all subscribed channels."""
        async with self._lock:
            ws = self._connections.pop(connection_id, None)
            meta = self._metadata.pop(connection_id, {})
            user_id = meta.get("userId")

            if user_id and user_id in self._user_to_connections:
                self._user_to_connections[user_id].discard(connection_id)
                if not self._user_to_connections[user_id]:
                    self._user_to_connections.pop(user_id, None)

            # Unsubscribe from channels
            sub_channels = self._connection_to_channels.pop(connection_id, set())
            for ch in sub_channels:
                if ch in self._channel_to_connections:
                    self._channel_to_connections[ch].discard(connection_id)
                    if not self._channel_to_connections[ch]:
                        self._channel_to_connections.pop(ch, None)
                        # Unsubscribe adapter if no local clients remain
                        asyncio.create_task(self.adapter.unsubscribe(ch))

        if ws:
            try:
                await ws.close()
            except Exception:
                pass

        logger.info(f"[WebSocket] Disconnected client {connection_id} (cleaned up {len(sub_channels)} channels)")

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe an active connection to a specific channel."""
        async with self._lock:
            if connection_id not in self._connections:
                return False

            first_subscriber_for_channel = channel not in self._channel_to_connections
            if first_subscriber_for_channel:
                self._channel_to_connections[channel] = set()

            self._channel_to_connections[channel].add(connection_id)
            self._connection_to_channels[connection_id].add(channel)

        if first_subscriber_for_channel:
            await self.adapter.subscribe(channel, self._on_bus_message)

        logger.debug(f"[WebSocket] Client {connection_id} subscribed to '{channel}'")
        return True

    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe connection from a channel."""
        async with self._lock:
            if connection_id not in self._connections:
                return False

            if channel in self._channel_to_connections:
                self._channel_to_connections[channel].discard(connection_id)
                if not self._channel_to_connections[channel]:
                    self._channel_to_connections.pop(channel, None)
                    await self.adapter.unsubscribe(channel)

            if connection_id in self._connection_to_channels:
                self._connection_to_channels[connection_id].discard(channel)

        logger.debug(f"[WebSocket] Client {connection_id} unsubscribed from '{channel}'")
        return True

    async def _on_bus_message(self, channel: str, raw_message: str) -> None:
        """Invoked when message arrives on message bus from local or remote workers."""
        try:
            event_dict = json.loads(raw_message)
        except Exception:
            event_dict = {"raw": raw_message}

        async with self._lock:
            subscribers = list(self._channel_to_connections.get(channel, set()))

        for conn_id in subscribers:
            ws = self._connections.get(conn_id)
            if ws:
                try:
                    await ws.send_json(event_dict)
                    self._messages_delivered_total += 1
                except Exception as e:
                    logger.warning(f"[WebSocket] Failed to send message to {conn_id}: {e}")

    async def send_personal_event(self, connection_id: str, event: WebSocketBaseEvent) -> bool:
        """Send a direct message to a specific connection."""
        ws = self._connections.get(connection_id)
        if not ws:
            return False
        try:
            await ws.send_json(event.model_dump())
            self._messages_delivered_total += 1
            return True
        except Exception as e:
            logger.warning(f"[WebSocket] Failed personal event to {connection_id}: {e}")
            return False

    async def broadcast_event(
        self,
        channel: str,
        event_type: WebSocketEventType,
        payload: Dict[str, Any],
    ) -> WebSocketBaseEvent:
        """Publish structured clinical event onto a channel across all cluster nodes."""
        if not self._initialized:
            await self.initialize()

        event = WebSocketBaseEvent(
            eventType=event_type,
            channel=channel,
            payload=payload,
        )
        json_data = json.dumps(event.model_dump())
        self._messages_published_total += 1

        # Publish to the message bus (Redis or InMemory)
        await self.adapter.publish(channel, json_data)
        logger.info(f"[WebSocket] Broadcast {event_type} on '{channel}' (id={event.eventId})")
        return event

    async def handle_client_message(self, connection_id: str, raw_text: str) -> None:
        """Process inbound text frame from client (commands or heartbeat)."""
        async with self._lock:
            if connection_id in self._metadata:
                self._metadata[connection_id]["lastSeen"] = datetime.now(timezone.utc).isoformat()

        try:
            data = json.loads(raw_text)
            command = ClientCommand.model_validate(data)
        except Exception:
            # If not valid JSON command, treat as echo or ignore
            return

        action = command.action.lower()
        if action == "ping":
            pong_event = WebSocketBaseEvent(
                eventType=WebSocketEventType.HEARTBEAT_PONG,
                channel="direct",
                payload={"serverTime": datetime.now(timezone.utc).isoformat()},
            )
            await self.send_personal_event(connection_id, pong_event)
        elif action == "subscribe" and command.channel:
            await self.subscribe(connection_id, command.channel)
        elif action == "unsubscribe" and command.channel:
            await self.unsubscribe(connection_id, command.channel)

    def get_metrics(self) -> WebSocketMetricsResponse:
        """Retrieve diagnostic metrics for WebSocket gateway."""
        channel_counts = {ch: len(conns) for ch, conns in self._channel_to_connections.items()}
        return WebSocketMetricsResponse(
            activeConnections=len(self._connections),
            activeUsers=len(self._user_to_connections),
            totalSubscribedChannels=len(self._channel_to_connections),
            channelSubscribers=channel_counts,
            redisConnected=self.adapter.is_connected(),
            adapterMode=self.adapter.get_mode(),
            messagesPublishedTotal=self._messages_published_total,
            messagesDeliveredTotal=self._messages_delivered_total,
        )


# Global singleton manager instance
ws_manager = ConnectionManager()
