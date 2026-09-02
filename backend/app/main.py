from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, announcements, detections, tasks, telemetry, zones
from app.config import settings
from app.database import init_db
from app.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Disaster Mission Control API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(detections.router)
app.include_router(alerts.router)
app.include_router(tasks.router)
app.include_router(zones.router)
app.include_router(announcements.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "ai_source": settings.ai_source}


@app.websocket("/ws/dashboard")
async def dashboard_ws(ws: WebSocket):
    """Single fan-out channel the dashboard opens once; every telemetry
    update, detection, alert and task change is pushed here as
    {type, payload} (Section 3 / Section 4.7)."""
    await manager.connect(ws)
    try:
        while True:
            # Dashboard doesn't need to send anything -- just keep the socket
            # open and drain any client pings/keepalives.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
