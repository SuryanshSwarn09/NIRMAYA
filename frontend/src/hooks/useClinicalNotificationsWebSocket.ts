import { useEffect, useRef, useState, useCallback } from "react";

export interface ClinicalAlertItem {
  alertId: string;
  patientId: string;
  patientName: string;
  doctorId: string;
  facilityId?: string;
  category: string;
  severity: "PANIC" | "CRITICAL" | "WARNING" | "INFO";
  status: "UNREAD" | "ACKNOWLEDGED" | "ESCALATED" | "DISMISSED";
  title: string;
  message: string;
  loincCode?: string;
  observedValue?: string;
  referenceRange?: string;
  actionRequired: boolean;
  createdAt: string;
  acknowledgedAt?: string;
  acknowledgedByDoctorId?: string;
  clinicalActionTaken?: string;
}

export interface UseClinicalNotificationsWebSocketOptions {
  doctorId: string;
  authToken?: string;
  apiBaseUrl?: string;
  wsBaseUrl?: string;
  autoConnect?: boolean;
}

export function useClinicalNotificationsWebSocket({
  doctorId,
  authToken = "mock-doctor-token",
  apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
  autoConnect = true,
}: UseClinicalNotificationsWebSocketOptions) {
  const [alerts, setAlerts] = useState<ClinicalAlertItem[]>([]);
  const [latestPanicAlert, setLatestPanicAlert] = useState<ClinicalAlertItem | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef<number>(0);

  // Fetch initial alerts list via REST
  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/alerts/doctor/${doctorId}?limit=50`);
      if (res.ok) {
        const data: ClinicalAlertItem[] = await res.json();
        setAlerts(data);
      }
    } catch {
      // In offline / mock mode, initialize with sample data if empty
      setAlerts((prev) => {
        if (prev.length > 0) return prev;
        return [
          {
            alertId: "alt-seed-001",
            patientId: "pat-arun-patel-01",
            patientName: "Arun Patel",
            doctorId: doctorId,
            facilityId: "fac-aiims-delhi",
            category: "LAB_PANIC_VALUE",
            severity: "PANIC",
            status: "UNREAD",
            title: "CRITICAL PANIC: Serum Potassium 6.8 mEq/L",
            message:
              "Patient Arun Patel's stat serum potassium is critically elevated at 6.8 mEq/L (Reference: 3.5 - 5.1 mEq/L). Risk of lethal ventricular arrhythmia.",
            loincCode: "2823-3",
            observedValue: "6.8 mEq/L",
            referenceRange: "3.5 - 5.1 mEq/L",
            actionRequired: true,
            createdAt: new Date().toISOString(),
          },
        ];
      });
    }
  }, [apiBaseUrl, doctorId]);

  // Connect WebSocket
  const connect = useCallback(() => {
    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setIsConnecting(true);
    setConnectionError(null);

    const wsUrl = `${wsBaseUrl}/ws/doctors/${doctorId}/workspace?token=${encodeURIComponent(authToken)}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionError(null);
        retryCountRef.current = 0;

        // Subscribe explicitly to doctor workspace channel
        ws.send(
          JSON.stringify({
            action: "subscribe",
            channel: `doctor:${doctorId}:workspace`,
          })
        );

        // Setup 25s heartbeat ping
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: "ping" }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const envelope = JSON.parse(event.data);

          // Handle Critical Alert frame
          if (envelope.eventType === "clinical.critical_alert" && envelope.payload) {
            const p = envelope.payload;
            const newAlert: ClinicalAlertItem = {
              alertId: p.alertId || `alt-${Date.now()}`,
              patientId: p.patientId || "",
              patientName: p.patientName || "Unknown Patient",
              doctorId: p.doctorId || doctorId,
              facilityId: p.facilityId,
              category: p.category || "LAB_PANIC_VALUE",
              severity: p.severity || "CRITICAL",
              status: "UNREAD",
              title: p.title || "Critical Clinical Notification",
              message: p.message || "",
              loincCode: p.loincCode,
              observedValue: p.observedValue,
              referenceRange: p.referenceRange,
              actionRequired: p.actionRequired ?? true,
              createdAt: p.createdAt || new Date().toISOString(),
            };

            setAlerts((prev) => [newAlert, ...prev.filter((a) => a.alertId !== newAlert.alertId)]);

            if (newAlert.severity === "PANIC" || newAlert.severity === "CRITICAL") {
              setLatestPanicAlert(newAlert);
            }
          }

          // Handle Alert Acknowledged frame
          if (envelope.eventType === "system.notification" && envelope.payload?.status === "ACKNOWLEDGED") {
            const p = envelope.payload;
            setAlerts((prev) =>
              prev.map((a) =>
                a.alertId === p.alertId
                  ? {
                      ...a,
                      status: "ACKNOWLEDGED",
                      acknowledgedAt: p.acknowledgedAt,
                      acknowledgedByDoctorId: p.acknowledgedByDoctorId,
                      clinicalActionTaken: p.clinicalActionTaken,
                    }
                  : a
              )
            );
            setLatestPanicAlert((current) => (current?.alertId === p.alertId ? null : current));
          }
        } catch {
          // ignore non-json frames
        }
      };

      ws.onerror = () => {
        setConnectionError("WebSocket connection encountered an error");
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);

        // Exponential backoff reconnect: 1s, 2s, 4s, 8s (max 10s)
        const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 10000);
        retryCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err: unknown) {
      setIsConnecting(false);
      setConnectionError(err instanceof Error ? err.message : "Failed to open WebSocket");
    }
  }, [authToken, doctorId, wsBaseUrl]);

  // Acknowledge Alert via REST
  const acknowledgeAlert = useCallback(
    async (alertId: string, clinicalAction: string, notes?: string): Promise<boolean> => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/alerts/${alertId}/acknowledge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            doctorId,
            clinicalAction,
            notes,
          }),
        });

        if (res.ok) {
          const updated: ClinicalAlertItem = await res.json();
          setAlerts((prev) => prev.map((a) => (a.alertId === alertId ? updated : a)));
          if (latestPanicAlert?.alertId === alertId) {
            setLatestPanicAlert(null);
          }
          return true;
        }
        return false;
      } catch {
        // Fallback local update in offline mode
        setAlerts((prev) =>
          prev.map((a) =>
            a.alertId === alertId
              ? {
                  ...a,
                  status: "ACKNOWLEDGED",
                  acknowledgedAt: new Date().toISOString(),
                  acknowledgedByDoctorId: doctorId,
                  clinicalActionTaken: clinicalAction,
                }
              : a
          )
        );
        if (latestPanicAlert?.alertId === alertId) {
          setLatestPanicAlert(null);
        }
        return true;
      }
    },
    [apiBaseUrl, doctorId, latestPanicAlert]
  );

  const dismissPanicAlert = useCallback(() => {
    setLatestPanicAlert(null);
  }, []);

  useEffect(() => {
    fetchAlerts();
    if (autoConnect) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [autoConnect, connect, fetchAlerts]);

  const unreadCount = alerts.filter((a) => a.status === "UNREAD").length;

  return {
    alerts,
    unreadCount,
    latestPanicAlert,
    isConnected,
    isConnecting,
    connectionError,
    acknowledgeAlert,
    dismissPanicAlert,
    refetchAlerts: fetchAlerts,
  };
}
