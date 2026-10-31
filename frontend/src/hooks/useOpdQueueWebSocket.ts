"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export type WebSocketConnectionStatus = "CONNECTED" | "CONNECTING" | "DISCONNECTED";

export interface UseOpdQueueWebSocketOptions {
  facilityId?: string;
  token?: string | null;
  onQueueUpdate?: (eventPayload: any) => void;
  onQueueCalled?: (eventPayload: any) => void;
  enabled?: boolean;
}

export interface UseOpdQueueWebSocketResult {
  isConnected: boolean;
  connectionStatus: WebSocketConnectionStatus;
  lastEvent: any | null;
  error: string | null;
  reconnect: () => void;
}

/**
 * High-reliability React hook connecting Next.js clients to the NIRMAYA
 * real-time OPD Queue WebSocket stream (/ws/facilities/{facility_id}/queue).
 * 
 * Features:
 * - Exponential backoff auto-reconnect on socket drop
 * - Automatic heartbeat ping frame keep-alives (every 25 seconds)
 * - Cal.com-compliant connection status telemetry
 */
export function useOpdQueueWebSocket({
  facilityId = "IN0410000123",
  token,
  onQueueUpdate,
  onQueueCalled,
  enabled = true,
}: UseOpdQueueWebSocketOptions): UseOpdQueueWebSocketResult {
  const [connectionStatus, setConnectionStatus] = useState<WebSocketConnectionStatus>("DISCONNECTED");
  const [lastEvent, setLastEvent] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const isMountedRef = useRef<boolean>(true);

  // Store callbacks in refs to avoid reconnection loops when functions change
  const onQueueUpdateRef = useRef(onQueueUpdate);
  onQueueUpdateRef.current = onQueueUpdate;

  const onQueueCalledRef = useRef(onQueueCalled);
  onQueueCalledRef.current = onQueueCalled;

  const connect = useCallback(() => {
    if (!enabled || typeof window === "undefined") {
      return;
    }

    // Terminate existing socket if any
    if (socketRef.current) {
      try {
        socketRef.current.close();
      } catch {
        // ignore close exceptions
      }
    }

    setConnectionStatus("CONNECTING");
    setError(null);

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL
        ? new URL(process.env.NEXT_PUBLIC_API_URL).host
        : "localhost:8000";
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const authToken = token || "demo-token";

      const url = `${wsProtocol}//${apiHost}/ws/facilities/${facilityId}/queue?token=${encodeURIComponent(authToken)}`;
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus("CONNECTED");
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Start heartbeat keep-alive pings
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: "ping" }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          setLastEvent(data);

          if (data.eventType === "queue.update" && onQueueUpdateRef.current) {
            onQueueUpdateRef.current(data.payload);
          } else if (data.eventType === "queue.called" && onQueueCalledRef.current) {
            onQueueCalledRef.current(data.payload);
          }
        } catch {
          // non-json or unparsed frame
        }
      };

      ws.onerror = () => {
        if (!isMountedRef.current) return;
        setError("WebSocket encountered connection error");
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus("DISCONNECTED");
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);

        // Schedule reconnect with exponential backoff (capped at 10s)
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current && enabled) {
            connect();
          }
        }, delay);
      };
    } catch (err: any) {
      if (isMountedRef.current) {
        setConnectionStatus("DISCONNECTED");
        setError(err?.message || "Failed to establish WebSocket connection");
      }
    }
  }, [enabled, facilityId, token]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      if (socketRef.current) {
        try {
          socketRef.current.close();
        } catch {
          // ignore
        }
      }
    };
  }, [connect]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  return {
    isConnected: connectionStatus === "CONNECTED",
    connectionStatus,
    lastEvent,
    error,
    reconnect,
  };
}

