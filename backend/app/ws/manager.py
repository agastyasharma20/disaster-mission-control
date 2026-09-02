import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Fan-out broadcaster for /ws/dashboard.

    Every REST write that other operators/panels should see live (new
    telemetry, a new detection/alert, a task status change) calls
    `broadcast()` with a small `{type, payload}` envelope after committing
    to the DB.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, message_type: str, payload: Any) -> None:
        if not self._connections:
            return
        data = json.dumps({"type": message_type, "payload": payload}, default=str)
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
