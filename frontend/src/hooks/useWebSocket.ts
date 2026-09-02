import { useEffect, useRef } from "react";
import { WS_URL } from "../api";
import type { WsMessage } from "../types";

/**
 * Opens one socket to /ws/dashboard and re-dispatches every {type, payload}
 * envelope to the caller. Auto-reconnects with a fixed backoff -- a control
 * vehicle's link may drop mid-mission, and the dashboard should recover on
 * its own rather than leave an operator staring at a stale screen.
 */
export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      socket = new WebSocket(WS_URL);
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WsMessage;
          handlerRef.current(msg);
        } catch {
          // ignore malformed frames
        }
      };
      socket.onclose = () => {
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };
      socket.onerror = () => socket?.close();
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);
}
