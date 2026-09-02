"""
Optional MQTT ingestion path (Section 5 of the proposal: MQTT is the
industry-standard transport for drone -> backend telemetry/IoT data).

Disabled by default (MQTT_ENABLED=false). The REST endpoints in
app/api/telemetry.py and app/api/detections.py are the primary, always-on
ingestion path -- that's what edge-inference/simulate_drone.py and
edge-inference/detect.py use out of the box, and nothing about them changes
if this is also enabled. Turn MQTT_ENABLED on if/when a real drone or ground
station publishes over MQTT instead of calling the REST API directly; both
paths write through app.services.ingestion, so alerts/dedup/WebSocket
broadcast behave identically either way.

Topics (drone_id is a single path segment, e.g. "drone-01"):
    drone/{drone_id}/telemetry   -> same JSON shape as POST /api/telemetry/{id}
    drone/{drone_id}/detections  -> same JSON shape as POST /api/detections/{id}

paho-mqtt's client runs its network loop on its own thread; incoming
messages are handed back to the FastAPI event loop with
asyncio.run_coroutine_threadsafe so DB writes stay on the loop that owns the
async engine.
"""
import asyncio
import json
import logging

import paho.mqtt.client as mqtt

from app.config import settings
from app.database import SessionLocal
from app.schemas import DetectionIn, TelemetryIn
from app.services.ingestion import ingest_detection, ingest_telemetry

logger = logging.getLogger("mqtt_client")

_loop: asyncio.AbstractEventLoop | None = None
_client: mqtt.Client | None = None


def _drone_id_from_topic(topic: str) -> str | None:
    parts = topic.split("/")
    return parts[1] if len(parts) == 3 and parts[0] == "drone" else None


async def _handle_telemetry(drone_id: str, payload: dict) -> None:
    async with SessionLocal() as db:
        await ingest_telemetry(db, drone_id, TelemetryIn(**payload))


async def _handle_detection(drone_id: str, payload: dict) -> None:
    async with SessionLocal() as db:
        await ingest_detection(db, drone_id, DetectionIn(**payload))


def _on_message(_client: mqtt.Client, _userdata, msg: mqtt.MQTTMessage) -> None:
    if _loop is None:
        return

    drone_id = _drone_id_from_topic(msg.topic)
    if drone_id is None:
        return

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("dropped malformed MQTT payload on %s", msg.topic)
        return

    if msg.topic.endswith("/telemetry"):
        coro = _handle_telemetry(drone_id, payload)
    elif msg.topic.endswith("/detections"):
        coro = _handle_detection(drone_id, payload)
    else:
        return

    asyncio.run_coroutine_threadsafe(coro, _loop)


def start() -> None:
    """Call from the FastAPI lifespan. No-op unless MQTT_ENABLED=true."""
    global _loop, _client
    if not settings.mqtt_enabled:
        return

    _loop = asyncio.get_event_loop()
    _client = mqtt.Client()
    _client.on_message = _on_message
    _client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=30)
    _client.subscribe([("drone/+/telemetry", 0), ("drone/+/detections", 0)])
    _client.loop_start()
    logger.info("MQTT ingestion listening on %s:%s", settings.mqtt_broker_host, settings.mqtt_broker_port)


def stop() -> None:
    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
