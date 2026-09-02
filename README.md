# Disaster Mission Control System

Minor project software backbone for Soaring Aerotech's disaster-response control vehicle: surveillance drone telemetry + AI scene detection → alerts → logistics/rescue task board → live mission-control dashboard.

Full requirements/design are in [`docs/proposal.md`](docs/proposal.md). This README covers running what's built.

## Architecture

```
Drone/Jetson (or edge-inference/simulate_drone.py in dev)
        │  REST: POST /api/telemetry/{id}, POST /api/detections/{id}
        ▼
FastAPI backend (backend/) ── PostgreSQL + PostGIS
        │  WebSocket: /ws/dashboard  (telemetry, detection, alert, task, announcement)
        ▼
React dashboard (frontend/) — map, alerts feed, task board, video panel, announcement log
```

## What's implemented

- **Backend** (`backend/`): FastAPI app with full REST API (telemetry, detections, alerts, tasks, zones, announcements), a WebSocket fan-out at `/ws/dashboard`, and an alerts engine that classifies severity by object type and dedups repeat detections of the same object (Section 4.3 of the proposal). Tables are created automatically on startup (no Alembic yet — fine for a demo, see Future Work).
- **Edge inference** (`edge-inference/`):
  - `simulate_drone.py` — flies a fake circular patrol, posts telemetry + occasional random detections. This is what makes the whole system demoable with zero hardware.
  - `detect.py` — real YOLOv8n pipeline over a webcam/video/RTSP source, publishing to the same endpoints. Stock COCO classes are mapped to the proposal's disaster classes as a placeholder until a fine-tuned model exists (see comments in the file).
  - Which one is "live" is just a config flag (`AI_SOURCE=simulated|jetson` in `backend/app/config.py`) — the backend and dashboard don't change either way.
- **Frontend** (`frontend/`): React + TypeScript + Leaflet dashboard — live map (drone position, flight trail, alert pins by severity), alerts feed with acknowledge action, task board (create from an alert, advance through pending → dispatched → in_progress → completed), announcement log, and a video panel placeholder (shows the latest detection until a real stream is wired up).

## Not implemented (stretch goals, see proposal §11)

Real drone flight control/MAVLink, real PA hardware + TTS, real payload-drop actuation, multi-drone swarm coordination, auth/roles, offline-first mode, Alembic migrations, real PostGIS geometry columns for zones (currently stored as JSON boundary arrays).

## Running it

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173
- Postgres/PostGIS: localhost:5432 (`mission`/`mission`/`mission_control`)

Then, in a separate terminal, start the simulated drone so there's something to see:

```bash
cd edge-inference
pip install -r requirements.txt
python simulate_drone.py
```

Open http://localhost:5173 — you should see the drone patrolling the map, alerts appearing as it "spots" things, and you can turn an alert into a task from the task board.

### Option B — run everything locally (no Docker)

```bash
# 1. Postgres with PostGIS must be reachable at the URL in backend/.env (copy from .env.example)
cd backend
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2. In another terminal
cd frontend
npm install
npm run dev

# 3. In another terminal
cd edge-inference
pip install -r requirements.txt
python simulate_drone.py
```

### Pointing at a real Jetson Nano feed later

Set `AI_SOURCE=jetson` in the backend env (informational — it doesn't gate any code path, it's just how the system records which source is authoritative), and run `edge-inference/detect.py --source rtsp://<drone-ip>/stream --model <fine-tuned-weights>.pt` on the Jetson instead of `simulate_drone.py`. It POSTs to the exact same `/api/detections/{drone_id}` endpoint, so nothing in the backend or dashboard needs to change.

## API surface

See `backend/app/api/` for the full routers, or `/docs` once the backend is running. Summary:

```
POST   /api/telemetry/{drone_id}
GET    /api/telemetry/{drone_id}/latest
POST   /api/detections/{drone_id}
GET    /api/alerts?severity=&status=
PATCH  /api/alerts/{id}
POST   /api/tasks
GET    /api/tasks?status=
PATCH  /api/tasks/{id}
GET    /api/zones
POST   /api/zones
GET    /api/announcements
POST   /api/announcements
WS     /ws/dashboard
```

## Repository layout

```
disaster-mission-control/
├── backend/            FastAPI app, SQLAlchemy models, alerts engine, WS manager
├── edge-inference/      simulate_drone.py (dev) + detect.py (real YOLO pipeline)
├── frontend/            React + TS + Leaflet dashboard
├── docs/proposal.md     Full project proposal (this is the source spec)
└── docker-compose.yml
```
