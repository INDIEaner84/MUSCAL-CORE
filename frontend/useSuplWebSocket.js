import { useEffect, useRef, useState, useCallback } from "react";

const WS_BASE = "ws://localhost:8000";

export default function useSuplWebSocket(lastSeq) {
  const wsRef = useRef(null);
  const [connectionState, setConnectionState] = useState("DISCONNECTED");
  const [events, setEvents] = useState([]);
  const [currentSeq, setCurrentSeq] = useState(lastSeq || 0);
  const [resyncRequired, setResyncRequired] = useState(false);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const params = currentSeq > 0 ? `?last_seq=${currentSeq}` : "";
    const ws = new WebSocket(`${WS_BASE}/api/supl/stream${params}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("CONNECTED");
      if (resyncRequired) setResyncRequired(false);
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);

        if (data.type === "heartbeat") {
          if (data.last_seq !== undefined) {
            setCurrentSeq(data.last_seq);
          }
          return;
        }

        if (data.type === "gap_detected") {
          setResyncRequired(true);
          return;
        }

        if (data.resync_required) {
          setResyncRequired(true);
          return;
        }

        setEvents((prev) => [...prev, data]);
        if (data.seq > 0) {
          setCurrentSeq(data.seq);
        }
      } catch (e) {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnectionState("DISCONNECTED");
      wsRef.current = null;
      reconnectTimeoutRef.current = setTimeout(() => {
        setConnectionState("RECONNECTING");
        connect();
      }, 3000);
    };

    ws.onerror = () => {
      setConnectionState("DISCONNECTED");
      ws.close();
    };
  }, [currentSeq, resyncRequired]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const resync = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setResyncRequired(false);
    setEvents([]);
    connect();
  }, [connect]);

  return {
    connectionState,
    events,
    currentSeq,
    resyncRequired,
    resync,
  };
}
