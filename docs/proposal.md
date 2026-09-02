# Disaster Mission Control System — Software Build Proposal
**Prepared for:** Soaring Aerotech Pvt. Ltd. (Minor Project Software Component)
**Prepared by:** Sarvesh, B.Tech CSE, PIEMR Indore
**Purpose of this document:** A build-ready specification to hand to Claude Code so it can scaffold and implement the software system end-to-end.

---

## 1. Project Overview

Soaring Aerotech wants a **Disaster Mission Control System** modeled on Air Force mission-control protocols, operated from a mobile **control vehicle**. The system coordinates:

- **Surveillance** — fixed-wing drone with a high-res camera + Nvidia Jetson Nano running edge AI for automated scene identification
- **Announcement** — broadcast/PA control from the control vehicle
- **Logistics dropping** — food, medicine, life-saving gadgets delivered by drone
- **Rescue operations** — coordinating ground teams based on what surveillance finds

This proposal covers the **software part only** — the dashboard, backend services, AI inference pipeline, and data layer that tie these functions together. Hardware (drone airframe, Jetson Nano deployment, PA hardware, actual drop mechanism) is out of scope but the software is built to interface with it.

---

## 2. Scope for the Minor Project

A full Air Force–grade mission control system is a multi-year, multi-team effort. For a single-semester Minor Project, the realistic and defensible scope is:

**In scope (build this):**
1. Mission Control Web Dashboard (live map + video + alerts + task board)
2. Drone telemetry ingestion service (position, altitude, battery, heading)
3. Video feed ingestion + AI scene identification module (can run on a laptop/Jetson Nano; simulated drone feed for demo if real hardware isn't available during dev)
4. Automated alert generation → control center (event detected → logged → shown on dashboard, with severity)
5. Logistics/rescue task board (assign a drop or rescue task to a team, track status: pending → dispatched → completed)
6. Basic GIS map layer (disaster zone boundary, drone position, resource/team markers)
7. Announcement log (record what announcements were made, when, from where — full PA hardware integration is stretch goal)

**Out of scope for the minor project (future work / stretch goals — mention but don't build):**
- Actual drone flight control / autopilot integration
- Real PA hardware/audio broadcast integration
- Real drop-mechanism actuation
- Multi-drone swarm coordination

This keeps the project **feasible in one semester** while still being the actual software backbone Soaring Aerotech could plug real hardware into later.

---

## 3. System Architecture

```
┌─────────────────────────┐
│   Fixed-Wing Drone       │
│  (Camera + Jetson Nano)  │
│  - captures video        │
│  - runs edge inference   │
│  - sends telemetry       │
└────────────┬─────────────┘
             │ (WebSocket / MQTT)
             ▼
┌─────────────────────────────────────┐
│         Backend (FastAPI)             │
│  ┌───────────────┐ ┌───────────────┐ │
│  │ Telemetry Svc  │ │ Detection Svc │ │
│  └───────────────┘ └───────────────┘ │
│  ┌───────────────┐ ┌───────────────┐ │
│  │ Alerts Engine  │ │ Task/Logistics│ │
│  └───────────────┘ └───────────────┘ │
│              PostgreSQL + PostGIS     │
└────────────┬──────────────────────────┘
             │ REST + WebSocket
             ▼
┌─────────────────────────────────────┐
│   Mission Control Dashboard (React)   │
│  - Live map (drone pos, zones, teams) │
│  - Live video feed panel              │
│  - Alerts feed (severity-tagged)      │
│  - Task board (drag/assign/status)    │
│  - Announcement log                   │
└─────────────────────────────────────┘
```

**Edge side (Jetson Nano):** runs a lightweight object/scene detection model (YOLOv8n or similar) on the drone video stream, detects classes relevant to disaster response (person, vehicle, fire/smoke, flood water, damaged structure), and pushes detection events + telemetry to the backend over MQTT or WebSocket.

**Cloud/control side:** FastAPI backend stores telemetry, detections, tasks; React dashboard visualizes everything in near real time.

---

## 4. Core Modules

### 4.1 Drone Telemetry & Video Ingestion Service
- Ingests position (lat/lon), altitude, heading, battery %, and a low-latency video feed reference (RTSP/WebRTC stream URL, or uploaded frame snapshots if bandwidth-limited)
- Simulated telemetry generator for development/demo (script that publishes fake but realistic flight paths + battery drain)

### 4.2 AI Scene Identification Module (Edge)
- Runs on Jetson Nano (or dev laptop for simulation)
- Model: YOLOv8n (nano) fine-tuned or off-the-shelf, targeting classes: `person`, `fire`, `smoke`, `flood_water`, `vehicle`, `collapsed_structure`
- On detection above confidence threshold → emits an event: `{type, confidence, bbox, lat, lon, timestamp, frame_snapshot}`
- Publishes event to backend via MQTT topic `drone/{id}/detections` or REST POST fallback

### 4.3 Alerts Engine
- Consumes detection events, applies severity rules (e.g., `fire` = critical, `person` in disaster zone = high, `vehicle` = medium)
- Deduplicates repeated detections of the same object within a time/distance window
- Pushes alerts to dashboard via WebSocket; stores alert history in DB

### 4.4 Logistics & Rescue Task Board
- CRUD for tasks: `{id, type (drop/rescue), target_location, assigned_team, status, priority, linked_alert_id, created_at, updated_at}`
- Status lifecycle: `pending → dispatched → in_progress → completed / failed`
- Can be created manually by an operator or auto-suggested from a critical alert

### 4.5 GIS / Mapping Layer
- Leaflet or Mapbox GL map showing: disaster zone polygon, live drone position + flight path trail, alert pins (color-coded by severity), team/resource markers
- Click a pin → see linked alert detail + snapshot + action buttons (create task, dismiss)

### 4.6 Announcement Log
- Simple log/module: operator records an announcement made (text + timestamp + zone); stretch goal wires this to actual TTS + PA hardware later
- v1: manual log entry form + list view

### 4.7 Mission Control Dashboard (Frontend)
- Single-page app, 3-panel layout: map (left/center), live alerts + video (right), task board (bottom or tab)
- Real-time updates via WebSocket (no manual refresh)
- Role-agnostic for v1 (single operator view); multi-role auth is a stretch goal

---

## 5. Recommended Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend API | Python + FastAPI | Async, fast to build, great for WebSocket + ML integration |
| Real-time transport | WebSocket (native) or MQTT (paho-mqtt) for drone→backend | MQTT is the industry-standard for IoT/telemetry; WebSocket for backend→dashboard |
| Database | PostgreSQL + PostGIS extension | Native geospatial queries for zones/positions |
| AI inference | YOLOv8n (Ultralytics), ONNX/TensorRT export for Jetson Nano | Lightweight, edge-friendly, well documented |
| Frontend | React + TypeScript, Leaflet (or Mapbox GL JS) for maps | Fast real-time UI, huge map-library ecosystem |
| Video | RTSP stream (simulate with OpenCV + a sample disaster-footage clip during dev) | Matches real drone camera output pattern |
| Deployment (dev) | Docker Compose (backend + db + frontend) | One-command local spin-up for demos |

---

## 6. Suggested Repository Structure

```
disaster-mission-control/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # REST routes: telemetry, alerts, tasks
│   │   ├── ws/              # WebSocket handlers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # alert rules, task lifecycle logic
│   │   └── mqtt_client.py
│   ├── requirements.txt
│   └── Dockerfile
├── edge-inference/
│   ├── detect.py            # runs YOLO on video feed, publishes events
│   ├── simulate_drone.py    # fake telemetry + detection generator for demo
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/ (MapView, AlertFeed, TaskBoard, VideoPanel)
│   │   ├── hooks/ (useWebSocket, useTelemetry)
│   │   └── App.tsx
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 7. Development Phases (Semester Timeline)

| Phase | Weeks | Deliverable |
|---|---|---|
| 1. Setup & data model | 1–2 | Repo scaffolded, DB schema, FastAPI skeleton, Docker Compose running |
| 2. Simulated telemetry + map | 3–4 | Drone simulator publishing fake flight path; dashboard map showing live position |
| 3. AI detection pipeline | 5–7 | YOLO running on sample disaster video, publishing detection events, visible as alerts |
| 4. Alerts engine + task board | 8–9 | Severity rules, alert feed UI, task CRUD + status lifecycle |
| 5. Integration + polish | 10–11 | Full loop working end-to-end: detection → alert → task → status update, all live on dashboard |
| 6. Documentation + demo prep | 12 | README, architecture diagram, demo script, presentation deck |

---

## 8. Sample API Endpoints

```
POST   /api/telemetry/{drone_id}        # ingest position/battery/heading
POST   /api/detections/{drone_id}       # ingest an AI detection event
GET    /api/alerts?severity=critical    # list alerts, filterable
POST   /api/tasks                       # create a logistics/rescue task
PATCH  /api/tasks/{task_id}             # update task status
GET    /api/zones                       # get disaster zone polygons
WS     /ws/dashboard                    # live push: telemetry, alerts, task updates
```

---

## 9. Sample Data Models

```python
class DroneTelemetry(BaseModel):
    drone_id: str
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    battery_pct: float
    timestamp: datetime

class DetectionEvent(BaseModel):
    drone_id: str
    object_type: str        # person | fire | smoke | flood_water | vehicle | collapsed_structure
    confidence: float
    lat: float
    lon: float
    snapshot_url: str | None
    timestamp: datetime

class Alert(BaseModel):
    id: UUID
    detection_id: UUID
    severity: str            # critical | high | medium | low
    status: str               # open | acknowledged | resolved
    created_at: datetime

class Task(BaseModel):
    id: UUID
    type: str                 # drop | rescue
    target_lat: float
    target_lon: float
    assigned_team: str | None
    priority: str
    status: str                # pending | dispatched | in_progress | completed | failed
    linked_alert_id: UUID | None
    created_at: datetime
    updated_at: datetime
```

---

## 10. Deliverables for Minor Project Submission

1. Working end-to-end demo (simulated drone → detection → alert → task → dashboard, all live)
2. GitHub repo with clean README + architecture diagram
3. Short demo video (2–3 min) showing the full loop
4. Project report covering: problem statement, architecture, tech choices, results, future scope
5. Presentation deck for evaluation

---

## 11. Future Scope (mention in proposal, don't build now)

- Real drone/autopilot integration (MAVLink)
- Real PA/audio hardware integration with text-to-speech
- Actual payload-drop mechanism trigger from the dashboard
- Multi-drone swarm support with conflict-free zone assignment
- Offline-first control vehicle mode (poor connectivity in disaster zones)
- Role-based access (operator, field team, command)

---

## 12. Instructions for Claude Code

When implementing this project, build it in the phase order in Section 7. Start with Phase 1 (repo scaffold + Docker Compose + DB schema) and get a trivial end-to-end "hello world" flowing through telemetry → DB → dashboard before adding AI detection. Use the simulated drone generator (`edge-inference/simulate_drone.py`) so the whole system is demoable without real hardware. Keep the AI model swappable (a config flag) so it can later be pointed at a real Jetson Nano inference feed without changing the backend/dashboard code.
